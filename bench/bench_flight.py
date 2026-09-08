#!/usr/bin/env python3
"""bench/bench_flight.py — orkiestracja epizodów ławki (PROMPT_BENCH_BUILD G). Wołany przez wrapper jako
FLIGHT=bench. NIE dotyka gate_run_r03.py (pinowany) — osobny moduł, ta sama osłona P2-ε w pętli.

Pętla 20 Hz: EKF(NED) → feed.sample(sim) → orbit_executor.step → shield.step(tgt) → ALLOW: set_velocity_ned(v_ned),
REFUSE: akcja bezpieczna (hover) + zapis zdarzenia. Epizody: bramka startu (home±1 m, |v|<0.3, pos_valid,
intruz w pozie startowej z pose/info), koniec = T_entry+T_orb(70) albo REFUSE/breach, reset ≤30 s do hoveru na home.
Loguje: trace (gt drona z dynamic_pose, ekf, zdarzenia), demo.jsonl (kontrakt §4), gt_intruder.jsonl (przez intruder_motion).

Env: BENCH_MANIFEST, BENCH_EPISODES (dom.4), BENCH_EPISODE_IDS (csv), FEED_PROFILE (B), CONTROLLER (orbit),
INTRUDER_MOTION (1), GATE_OUT (trace), PX4_GZ_WORLD, B1_MODEL.
"""
import asyncio
import hashlib
import json
import math
import os
import subprocess
import sys
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from px4_msgs.msg import VehicleLocalPosition
from gz.transport13 import Node as GzNode
from gz.msgs10.pose_v_pb2 import Pose_V
from gz.msgs10.clock_pb2 import Clock
from mavsdk import System
from mavsdk.offboard import VelocityNedYaw, OffboardError
from mavsdk.action import ActionError

from r01.shield import PatrolShield, REFUSE, POS_DEGRADED, M_PATROL
from r01.config import V_MAX
from r03 import config as C
from r03.controllers import make_controller, controller_sha
from r03.controllers.safe_descend import safe_descend_step, new_state   # K2 B3: D5 współdzielone z gate
from harness.track_feed import FeedB, TrackFeedGz
from harness.intruder_motion import scenario_to_gz, gz_to_ned, TOL_START, SETPOSE_HZ
from bench import scenarios as S
from bench.demo_logger import DemoLogger, make_row
from common.frames import enu2ned

WORLD = os.environ.get("PX4_GZ_WORLD", "world_demo_A3")
MODEL = os.environ.get("B1_MODEL", "x500_mono_cam_0")
OUT = os.environ.get("GATE_OUT", "/tmp/bench/trace.jsonl")
OUTDIR = os.path.dirname(OUT)
MANIFEST = os.environ.get("BENCH_MANIFEST", "results/BENCH/scenario_manifest.json")
N_EP = int(os.environ.get("BENCH_EPISODES", "4"))
EP_IDS = os.environ.get("BENCH_EPISODE_IDS", "")
CONTROLLER = os.environ.get("CONTROLLER", "orbit")
INTRUDER_MOTION = os.environ.get("INTRUDER_MOTION", "1") == "1"
ALT = C.ALT_M
DT = C.DT
TICK_HZ = C.TICK_HZ
T_ORB = 70.0
ENTRY_MAX = 25.0
# K2 B4: hook denialu. K2_INJECT_T = sekundy po t_entry do wstrzyknięcia EKF2_GPS_CTRL=0.
# BRAK zmiennej ⇒ zero denialu (loty nominalne IDENTYCZNE jak dotąd).
K2_INJECT_T = float(os.environ["K2_INJECT_T"]) if os.environ.get("K2_INJECT_T") else None
_SD_CFG = {"v_desc_fast": C.V_DESC_FAST, "v_desc_land": C.V_DESC_LAND,
           "desc_fast_dur": max(0.0, (C.ALT_M - C.H_SWITCH_AGL) / C.V_DESC_FAST),
           "desc_total": max(0.0, (C.ALT_M - C.H_SWITCH_AGL) / C.V_DESC_FAST) + C.H_SWITCH_AGL / C.V_DESC_LAND + 1.5}
RESET_MAX = 30.0
QOS = QoSProfile(depth=1, history=HistoryPolicy.KEEP_LAST, reliability=ReliabilityPolicy.BEST_EFFORT)

_lock = threading.Lock(); _f = None; _running = False
_sim_t = [0.0]
_drone_gt_last = [0.0]
_intr_start_pose = {"gz": None}


def _w(row):
    with _lock:
        if _f is not None and _running:
            _f.write(json.dumps(row) + "\n")


class EkfSub(Node):
    def __init__(self):
        super().__init__("bench_ekf")
        self.m = None
        self.create_subscription(VehicleLocalPosition, "/fmu/out/vehicle_local_position", self._cb, QOS)

    def _cb(self, m):
        self.m = m
        _w({"t": "ekf", "mono": round(time.monotonic(), 4), "ts": round(m.timestamp / 1e6, 4),
            "x": round(float(m.x), 4), "y": round(float(m.y), 4), "z": round(float(m.z), 4),
            "vx": round(float(m.vx), 4), "vy": round(float(m.vy), 4), "vz": round(float(m.vz), 4),
            "eph": round(float(m.eph), 4)})


def _clock_cb(msg):
    _sim_t[0] = msg.sim.sec + msg.sim.nsec / 1e9


def _dronegt_cb(msg):
    now = time.monotonic()
    if now - _drone_gt_last[0] < 1.0 / 50:
        return
    for p in msg.pose:
        if p.name == MODEL:
            sim = msg.header.stamp.sec + msg.header.stamp.nsec / 1e9
            _w({"t": "gt", "mono": round(now, 4), "sim": round(sim, 4),
                "x": round(p.position.x, 5), "y": round(p.position.y, 5), "z": round(p.position.z, 5)})
            _drone_gt_last[0] = now
            return


def _intr_pose_cb(msg):
    for p in msg.pose:
        if p.name == "intruder":
            _intr_start_pose["gz"] = [p.position.x, p.position.y, p.position.z]
            return


async def arm_retry(d):
    for i in range(40):
        try:
            await d.action.arm(); return True
        except (ActionError, Exception):
            await asyncio.sleep(3)
    return False


async def _wait_health(d):
    async for h in d.telemetry.health():
        if h.is_global_position_ok and h.is_home_position_ok:
            return True
    return False


def _resolve_episodes(manifest):
    q = os.environ.get("BENCH_QUEUE", "")
    if q:                                          # kampania (C8): weź in_flight z kolejki (driver popnął), NIE listę
        from bench.campaign_queue import CampaignQueue
        batch = CampaignQueue(q).current_batch()
        eps = []
        for b in batch[:N_EP]:
            ep = dict(manifest["episodes"][b["episode_id"]])
            ep["attempt"] = b["attempt"]           # propagacja attempt → ep_meta → demo/judge/manifest
            eps.append(ep)
        return eps
    if EP_IDS.strip():
        ids = [int(x) for x in EP_IDS.split(",") if x.strip()]
        return [manifest["episodes"][i] for i in ids][:N_EP]
    return manifest["episodes"][:N_EP]


def _write_control(phase, episode_id=None, t0_sim=None):
    ctl = {"phase": phase, "episode_id": episode_id, "t0_sim": t0_sim}
    with open(os.path.join(OUTDIR, "episode_control.json"), "w") as f:
        json.dump(ctl, f)


async def main():
    global _f, _running
    os.makedirs(OUTDIR, exist_ok=True)
    manifest = json.load(open(os.path.join(ROOT, MANIFEST)))
    episodes = _resolve_episodes(manifest)
    exec_params = json.load(open(os.path.join(ROOT, "bench/executor_params.json")))
    exec_params_sha = hashlib.sha256(json.dumps(exec_params, sort_keys=True).encode()).hexdigest()

    gn = GzNode()
    rclpy.init()
    ekf = EkfSub()
    d = System(); await d.connect(system_address="udpin://0.0.0.0:14540")
    async for s in d.core.connection_state():
        if s.is_connected:
            break
    for p, want in C.HARNESS_PARAM_PREFLIGHT.items():
        await d.param.set_param_int(p, want)
    try:
        healthy = await asyncio.wait_for(_wait_health(d), timeout=45)
    except asyncio.TimeoutError:
        healthy = False
    if not healthy:
        print("[bench] HEALTH TIMEOUT", flush=True); os._exit(3)

    shield = PatrolShield(); shield.reset()
    shield.pos_debounce_ticks = C.DEBOUNCE_TICKS
    shield.pos_hyst_ticks = int(round(C.HYST_M_S / C.DT))

    fh = open(OUT, "w"); _f = fh; _running = True
    ctrl_sha = controller_sha(make_controller(CONTROLLER, params=exec_params, orbit_dir="CCW", vmax=V_MAX))
    # K2 B5: certs_selfcheck dla FLIGHT=bench (dotąd biegł tylko dla gate_r03; wynik do trace+sidecar)
    try:
        _cs = subprocess.run([sys.executable, "-m", "r01.proofs.certs_selfcheck"],
                             cwd=ROOT, capture_output=True, text=True,
                             env={**os.environ, "PYTHONPATH": f".:.certdeps:{os.environ.get('PYTHONPATH','')}"})
        _cs_rc = _cs.returncode
        with open(os.path.join(OUTDIR, "certs_selfcheck.log"), "w") as _cf:
            _cf.write(_cs.stdout + _cs.stderr + f"\ncerts_selfcheck rc={_cs_rc}\n")
    except Exception as _e:
        _cs_rc = -1
    _w({"t": "meta", "flight": "bench", "world": WORLD, "controller": CONTROLLER,
        "controller_sha": ctrl_sha, "exec_params_sha": exec_params_sha, "R_E": shield.cfg.r_e,
        "n_episodes": len(episodes), "T_orb": T_ORB, "vmax": V_MAX,
        "certs_selfcheck_rc": _cs_rc, "k2_inject_t": K2_INJECT_T})
    gn.subscribe(Clock, f"/world/{WORLD}/clock", _clock_cb)
    gn.subscribe(Pose_V, f"/world/{WORLD}/dynamic_pose/info", _dronegt_cb)
    gn.subscribe(Pose_V, f"/world/{WORLD}/pose/info", _intr_pose_cb)

    def ev(s, **kw):
        _w({"t": "event", "mono": round(time.monotonic(), 4), "sim": round(_sim_t[0], 4), "ev": s, **kw})
        print(f"[bench] {s} sim={_sim_t[0]:.2f} {kw}", flush=True)

    # intruder_motion obok
    im_proc = None
    if INTRUDER_MOTION:
        im_proc = subprocess.Popen(
            [sys.executable, "-m", "harness.intruder_motion", "--world", WORLD,
             "--manifest", MANIFEST, "--outdir", OUTDIR],
            cwd=ROOT, env={**os.environ, "PYTHONPATH": f".:{os.environ.get('PYTHONPATH','')}"})
        _write_control("idle")

    if not await arm_retry(d):
        print("[bench] ARM FAILED", flush=True); os._exit(2)
    ev("armed")
    await d.action.set_takeoff_altitude(ALT); await d.action.takeoff(); ev("takeoff")
    await asyncio.sleep(12)
    await d.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
    try:
        await d.offboard.start(); ev("offboard")
    except OffboardError as e:
        print("[bench] offboard err", e, flush=True); os._exit(4)

    def _spin():
        while _running and rclpy.ok():
            rclpy.spin_once(ekf, timeout_sec=0.02)
    th = threading.Thread(target=_spin, daemon=True); th.start()

    demo = DemoLogger(os.path.join(OUTDIR, "demo.jsonl"))
    tick = 0
    home_ned = [0.0, 0.0, -C.ALT_M]

    from r02.intruder_driver import GzPoseClient

    async def _intruder_start_gate(ep):
        """§2 async twin: komenderuj set_pose do pozy startowej + hover, czekaj aż GT intruza ≤ TOL_START.
        5 s sim → retry → 5 s sim → INVALID_START. Zamyka własny GzPoseClient po prestart (nie kłóci się
        z intruder_motion w epizodzie)."""
        px, py, pz = S.position_at(ep, 0.0)
        gz_start, start_ned = scenario_to_gz(px, py, pz)
        cli = GzPoseClient(WORLD, apply_hz=SETPOSE_HZ)
        n_set = 0; total_wait = 0.0; status = "INVALID_START"; pose = None; attempts = 0
        try:
            for attempt in range(2):
                t0 = _sim_t[0]; attempts = attempt + 1
                while _sim_t[0] - t0 < 5.0:
                    cli.set_pose(*gz_start); n_set += 1
                    await d.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))   # hover — nie zrywaj offboardu
                    g = _intr_start_pose["gz"]
                    if g is not None:
                        ap = gz_to_ned(g)
                        if math.dist(ap, start_ned) <= TOL_START:
                            total_wait += _sim_t[0] - t0; status = "OK"; pose = ap
                            return {"status": status, "n_setpose": n_set, "wait_sim": round(total_wait, 3),
                                    "pose": [round(v, 4) for v in ap], "attempts": attempts,
                                    "start_ned": [round(v, 4) for v in start_ned]}
                    await asyncio.sleep(DT)
                total_wait += _sim_t[0] - t0
            g = _intr_start_pose["gz"]; pose = gz_to_ned(g) if g else None
            return {"status": status, "n_setpose": n_set, "wait_sim": round(total_wait, 3),
                    "pose": [round(v, 4) for v in pose] if pose else None, "attempts": attempts,
                    "start_ned": [round(v, 4) for v in start_ned]}
        finally:
            cli.close()

    async def _fly_to_home_hover(deadline_s):
        """Reset: leć do hoveru na home; zwraca True gdy w bramce (home±1, |v|<0.3)."""
        t0 = _sim_t[0]
        while _sim_t[0] - t0 < deadline_s:
            m = ekf.m
            if m is None:
                await asyncio.sleep(0.05); continue
            dx, dy = -float(m.x), -float(m.y)
            dh = math.hypot(dx, dy)
            vh = math.hypot(float(m.vx), float(m.vy))
            if dh < 1.0 and vh < 0.3:
                return True
            ux, uy = (dx / dh, dy / dh) if dh > 1e-6 else (0.0, 0.0)
            spd = min(V_MAX, 0.6 * dh)
            vz = 0.6 * ((-C.ALT_M) - float(m.z))
            await d.offboard.set_velocity_ned(VelocityNedYaw(spd * ux, spd * uy, vz, 0))
            await asyncio.sleep(DT)
        return False

    for ep in episodes:
        ctrl = make_controller(CONTROLLER, params=exec_params, orbit_dir=ep["orbit_dir"],
                               vmax=V_MAX, home_ned=(0.0, 0.0, -C.ALT_M))
        ctrl.reset()
        feed = FeedB(ep["seed"], f=10.0)
        tf = TrackFeedGz(WORLD, feed)          # subskrybuje pose/info → feed
        # bramka startu: dron na home, intruz w pozie startowej
        in_gate = await _fly_to_home_hover(RESET_MAX)
        m = ekf.m
        pos_ok = m is not None and bool(getattr(m, "xy_valid", True))
        intr_ok = _intr_start_pose["gz"] is not None
        if not (in_gate and pos_ok):
            ev("start_gate_fail", episode_id=ep["episode_id"], in_gate=in_gate, pos_ok=pos_ok, intr_ok=intr_ok)
            break                              # bramka niespełniona → lądowanie, epizody dotąd ważne
        # BRAMKA STARTU INTRUZA (§2): czekaj aż intruz w pozie startowej ≤ TOL_START (async twin logiki
        # `intruder_start_gate`, ta sama pętla TOL/retry/INVALID_START — wysyła hover setpoint by nie zerwać offboardu)
        sg = await _intruder_start_gate(ep)
        ev("intruder_start_gate", episode_id=ep["episode_id"], **sg)
        if sg["status"] != "OK":
            ev("invalid_start", episode_id=ep["episode_id"], reason="intruz nie w pozie startowej", **sg)
            continue                           # INVALID_START — epizod nie liczony, następny
        t0_sim = _sim_t[0]
        _write_control("start", episode_id=ep["episode_id"], t0_sim=t0_sim)
        ev("episode_start", episode_id=ep["episode_id"], scenario_id=ep["scenario_id"], t0_sim=round(t0_sim, 3))

        ep_meta = {"episode_id": ep["episode_id"], "scenario_id": ep["scenario_id"], "seed": ep["seed"],
                   "attempt": ep.get("attempt", 0)}
        t_entry = None
        refuse_count = 0
        breach = False
        denial_done = False; t_inj_sim = None; sd_state = new_state(); denied = False   # K2 B3/B4
        ep_wall0 = time.monotonic()
        while True:
            if time.monotonic() - ep_wall0 > 180.0:      # bezpiecznik wall (stack padł / hang) — D8 ≤10 min/boot
                ev("episode_wall_timeout", episode_id=ep["episode_id"]); break
            now_sim = _sim_t[0]
            t_rel = now_sim - t0_sim
            m = ekf.m
            if m is None:
                await asyncio.sleep(0.05); continue
            own = [float(m.x), float(m.y), float(m.z)]
            vel = [float(m.vx), float(m.vy), float(m.vz)]
            r_est = math.hypot(own[0], own[1])
            fs = feed.sample(now_sim)
            ctrl.set_feed(fs)
            cmd = ctrl.step(tick, own, vel, now_sim, False)
            tgt = cmd["tgt_ned"]
            phase = cmd["extra"].get("phase")
            dband = cmd["extra"].get("d")
            if t_entry is None and dband is not None and 6.0 <= dband <= 10.0:
                t_entry = t_rel
            dr = bool(getattr(m, "dead_reckoning", False))
            # K2 B4: hook denialu — EKF2_GPS_CTRL=0 w t_entry+K2_INJECT_T (deterministycznie, raz)
            if (K2_INJECT_T is not None and t_entry is not None and not denial_done
                    and t_rel >= t_entry + K2_INJECT_T):
                await d.param.set_param_int("EKF2_GPS_CTRL", 0)
                denial_done = True; t_inj_sim = now_sim
                ev("denial", episode_id=ep["episode_id"], t_inj_sim=round(now_sim, 3), inj_t_rel=round(t_rel, 3))
            pf = dr if denial_done else None                 # K2 B3: pos_flag z dead-reckoning (wzór gate:267)
            d_dec = shield.step(tick, own, vel, tgt, mode=M_PATROL, pos_flag=pf)
            is_pos = (d_dec["decision"] == REFUSE and d_dec.get("reason") == POS_DEGRADED)
            if is_pos:
                # K2 B3: REFUSE(POS) → zejście D5 (ta sama funkcja co gate) do touchdown → koniec bootu
                if refuse_count == 0:
                    refuse_count += 1
                    ev("refuse", episode_id=ep["episode_id"], reason=POS_DEGRADED,
                       r_est=round(r_est, 2), t_rel=round(t_rel, 3))
                vdesc, sd_evs, sd_td, sd_state = safe_descend_step(sd_state, time.monotonic(), _SD_CFG)
                for _e in sd_evs:
                    ev(_e, episode_id=ep["episode_id"])
                await d.offboard.set_velocity_ned(VelocityNedYaw(0, 0, vdesc, 0))
                if sd_td:
                    denied = True
            elif d_dec["decision"] == REFUSE:
                refuse_count += 1
                ev("refuse", episode_id=ep["episode_id"], reason=d_dec.get("reason"), r_est=round(r_est, 2))
                await d.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
            else:
                v = cmd["v_ned"]
                await d.offboard.set_velocity_ned(VelocityNedYaw(v[0], v[1], v[2], cmd.get("yaw", 0.0)))
            if r_est > shield.cfg.r_e:
                breach = True; ev("breach", episode_id=ep["episode_id"], r_est=round(r_est, 2))
            demo.log(make_row(now_sim, tick, ep_meta, own, vel, fs, cmd["v_ned"], phase, 0,
                              CONTROLLER, ctrl_sha or "na", exec_params_sha))
            tick += 1
            done = (t_entry is not None and t_rel >= t_entry + T_ORB) or denied or breach
            if d_dec["decision"] == REFUSE and not is_pos:
                done = True                    # GEOFENCE/inny REFUSE — hover + koniec epizodu (jak dotąd)
            if t_entry is None and t_rel > ENTRY_MAX + 5.0 and t_rel > 40.0:
                done = True                    # nie weszło — kończ epizod (do sędziego a-FAIL)
            if done:
                break
            await asyncio.sleep(DT)
        ev("episode_end", episode_id=ep["episode_id"], t_entry=(round(t_entry, 2) if t_entry else None),
           refuse=refuse_count, breach=breach,
           t_inj_sim=(round(t_inj_sim, 3) if t_inj_sim is not None else None), denied=denied)
        _write_control("idle")
        if breach:
            ev("breach_stop"); break           # SR-6 breach ⇒ STOP natychmiast
        if denied:
            ev("denial_boot_end", episode_id=ep["episode_id"]); break   # K2 B3: denial kończy boot (D5 wykonane)

    # zejście
    _running_reset = await _fly_to_home_hover(RESET_MAX)
    ev("reset_done", in_gate=_running_reset)
    demo.close()
    _write_control("stop")
    await asyncio.sleep(1)
    try:
        await d.offboard.stop()
    except Exception:
        pass
    try:
        await d.action.land()
    except Exception:
        pass
    await asyncio.sleep(5)
    with _lock:
        _running = False
    if im_proc:
        im_proc.terminate()
    ekf.destroy_node(); rclpy.shutdown(); fh.close()
    print(f"[bench] done -> {OUT} (demo n={demo.n})", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
