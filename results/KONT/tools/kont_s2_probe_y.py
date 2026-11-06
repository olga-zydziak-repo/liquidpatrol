#!/usr/bin/env python3
"""results/KONT/tools/kont_s2_probe_y.py — sonda Y (ANEKS_KONT-2b §2, §3.4) = kopia kont_s2_probe.py (oryginał nietknięty), dwie zmiany: yaw w zejściu = heading z chwili decyzji, trzymany do przyziemienia; asercja przed uzbrojeniem |błąd yaw vs GT| ≤ 10° (kont_yaw.json, naruszenie: kod 7, bez uzbrojenia). Oryginał: driver lotu S2 (PROMPT_KONT_S2 §S2.1) = kopia kont_probe.py; zmiany: FEED=V2 (R-4); kompensacja przesunięcia pionowego (R-2,
pomiar EKF z − GT z na ziemi ≥ 5 s, komenda wysokości przesunięta, wartość w kont_echo.json); nauczyciel z akwizycją kanonu: rejestr "net_skan2" z delegatem OrbitExecutor
zamiast NetController (podmiana nazwy w module akw_scan w tym procesie, zero edycji plików; skan SKAN2 i kwarantanna K1 bez zmian), bo orbit_executor sam nie skanuje, a c11/c02
bez skanu nie mają akwizycji; wiersze ctl z tym, co widzi feed; zapis t_flag = odcięcie. Oryginał:
Skrót bench/bench_flight.py (FROZEN, nietknięty) do jednego epizodu: nauczyciel orbit_executor + FeedB, odcięcie GNSS przy t_entry + 30 s
(jak K2), potem orbita ≥ KONT_WINDOW_S, potem safe_descend_step (ta sama akcja co D5, bez osłony) do przyziemienia GT z < 0.15 m.

Osłona BIERNA: decyzje PatrolShield tylko logowane, nic nie wykonują. REFUSE(POS) przed odcięciem = poza scenariuszem ⇒ STOP (zejście).
Bezpiecznik sondy (zapisany w manifeście, nie część projektu): r_GT ≥ R_E − 3 m ⇒ zejście; utrata GT > 2 s ⇒ zejście.
Odniesienie czasu odcięcia: stempel PX4 ostatniej próbki EKF przed wysłaniem parametru (t_cut_px4), więc opóźnienia z ulogu są liczone
od chwili przed wywołaniem, z latencją set_param po stronie zachowawczej.

Env: GATE_OUT, PX4_GZ_WORLD, B1_MODEL, KONT_EPISODE_ID (20 = c08_s02), KONT_WINDOW_S (72), KONT_INJECT_T (30), KONT_HOLD_S (15), BENCH_MANIFEST.
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

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
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
from r03 import kont_config as KC
from r03.controllers import make_controller, controller_sha
from r03.controllers import akw_scan as _akw_scan
from r03.controllers.orbit_executor import OrbitExecutor
_akw_scan.NetController = OrbitExecutor                  # nauczyciel zamiast sieci pod skanem kanonu (R-4), tylko ten proces
from r03.controllers.safe_descend import safe_descend_step, new_state
from harness.feed_registry import make_feed
from harness.intruder_motion import scenario_to_gz, gz_to_ned, TOL_START, SETPOSE_HZ
from bench import scenarios as S

WORLD = os.environ.get("PX4_GZ_WORLD", "world_kont_A3")
MODEL = os.environ.get("B1_MODEL", "x500_mono_cam_flow_0")
OUT = os.environ.get("GATE_OUT", "/tmp/kont/trace.jsonl")
OUTDIR = os.path.dirname(OUT)
OFFSET_WIN_S = 6.0
FEED_NAME = os.environ.get("FEED", "V2")
MANIFEST = os.environ.get("BENCH_MANIFEST", "results/BENCH/scenario_manifest.json")
EP_ID = int(os.environ.get("KONT_EPISODE_ID", "20"))
WINDOW_S = float(os.environ.get("KONT_WINDOW_S", "72"))
INJECT_T = float(os.environ.get("KONT_INJECT_T", "30"))
HOLD_S = float(os.environ.get("KONT_HOLD_S", "15"))
DT = C.DT
FUSE_M = C.R_E - 3.0
Z_GROUND = 0.15
GT_STALE_S = 2.0
YAW_ASSERT_DEG = 10.0
ENTRY_MAX = 40.0
RESET_MAX = 30.0
DESC_MAX_S = 60.0
_SD_CFG = {"v_desc_fast": C.V_DESC_FAST, "v_desc_land": C.V_DESC_LAND,
           "desc_fast_dur": max(0.0, (C.ALT_M - C.H_SWITCH_AGL) / C.V_DESC_FAST),
           "desc_total": max(0.0, (C.ALT_M - C.H_SWITCH_AGL) / C.V_DESC_FAST) + C.H_SWITCH_AGL / C.V_DESC_LAND + 1.5}
QOS = QoSProfile(depth=1, history=HistoryPolicy.KEEP_LAST, reliability=ReliabilityPolicy.BEST_EFFORT)

_lock = threading.Lock(); _f = None; _running = False
_sim_t = [0.0]
_gt = {"x": None, "y": None, "z": None, "mono": 0.0, "last_log": 0.0}
_intr_gz = [None]


def _w(row):
    with _lock:
        if _f is not None and _running:
            _f.write(json.dumps(row) + "\n")


class EkfSub(Node):
    def __init__(self):
        super().__init__("kont_ekf")
        self.m = None
        self.create_subscription(VehicleLocalPosition, "/fmu/out/vehicle_local_position", self._cb, QOS)

    def _cb(self, m):
        self.m = m
        _w({"t": "ekf", "mono": round(time.monotonic(), 4), "ts": round(m.timestamp / 1e6, 4),
            "x": round(float(m.x), 4), "y": round(float(m.y), 4), "z": round(float(m.z), 4),
            "vx": round(float(m.vx), 4), "vy": round(float(m.vy), 4), "vz": round(float(m.vz), 4),
            "eph": round(float(m.eph), 4), "xy_valid": bool(m.xy_valid), "v_xy_valid": bool(m.v_xy_valid),
            "dr": bool(m.dead_reckoning), "dist_bottom": round(float(m.dist_bottom), 3),
            "dist_bottom_valid": bool(m.dist_bottom_valid)})


def _yaw_blad_deg(heading, qw, qx, qy, qz):
    """heading NED EKF minus yaw GT z kwaternionu gz (ENU) w stopniach, zawinięty do ±180."""
    y = math.atan2(2 * (qw * qz + qx * qy), 1 - 2 * (qy * qy + qz * qz))
    return math.degrees((heading - (math.pi / 2 - y) + math.pi) % (2 * math.pi) - math.pi)


def _clock_cb(msg):
    _sim_t[0] = msg.sim.sec + msg.sim.nsec / 1e9


def _dronegt_cb(msg):
    now = time.monotonic()
    for p in msg.pose:
        if p.name == MODEL:
            _gt.update(x=p.position.x, y=p.position.y, z=p.position.z, mono=now, q=(p.orientation.w, p.orientation.x, p.orientation.y, p.orientation.z))
            if now - _gt["last_log"] >= 1.0 / 50:
                sim = msg.header.stamp.sec + msg.header.stamp.nsec / 1e9
                _w({"t": "gt", "mono": round(now, 4), "sim": round(sim, 4), "x": round(p.position.x, 5), "y": round(p.position.y, 5),
                    "z": round(p.position.z, 5), "qw": round(p.orientation.w, 6), "qx": round(p.orientation.x, 6),
                    "qy": round(p.orientation.y, 6), "qz": round(p.orientation.z, 6)})
                _gt["last_log"] = now
            return


def _intr_pose_cb(msg):
    for p in msg.pose:
        if p.name == "intruder":
            _intr_gz[0] = [p.position.x, p.position.y, p.position.z]
            return


async def _wait_health(d):
    async for h in d.telemetry.health():
        if h.is_global_position_ok and h.is_home_position_ok:
            return True
    return False


def _write_control(phase, episode_id=None, t0_sim=None):
    with open(os.path.join(OUTDIR, "episode_control.json"), "w") as f:
        json.dump({"phase": phase, "episode_id": episode_id, "t0_sim": t0_sim}, f)


async def main():
    global _f, _running
    os.makedirs(OUTDIR, exist_ok=True)
    manifest = json.load(open(os.path.join(ROOT, MANIFEST)))
    ep = manifest["episodes"][EP_ID]
    exec_params = json.load(open(os.path.join(ROOT, "bench/executor_params.json")))

    gn = GzNode()
    rclpy.init()
    ekf = EkfSub()
    d = System(); await d.connect(system_address="udpin://0.0.0.0:14540")
    async for s in d.core.connection_state():
        if s.is_connected:
            break
    echo = await KC.apply_and_assert(d.param)
    gn.subscribe(Pose_V, f"/world/{WORLD}/dynamic_pose/info", _dronegt_cb)
    gn.subscribe(Clock, f"/world/{WORLD}/clock", _clock_cb)
    def _spin():
        while _running_spin[0] and rclpy.ok():
            rclpy.spin_once(ekf, timeout_sec=0.02)
    _running_spin = [True]
    threading.Thread(target=_spin, daemon=True).start()
    # R-2: przesunięcie originu pionowego na ziemi przed uzbrojeniem
    _s = []
    _t0 = time.monotonic()
    while time.monotonic() - _t0 < 60.0:
        if ekf.m is not None and _gt["z"] is not None:
            _s.append((_sim_t[0], float(ekf.m.z) + _gt["z"]))
            if _s[-1][0] - _s[0][0] >= OFFSET_WIN_S:
                break
        await asyncio.sleep(0.05)
    if not _s or _s[-1][0] - _s[0][0] < 5.0:
        print("[kont] brak okna przesunięcia", flush=True); os._exit(6)
    Z_OFF = sum(x for _, x in _s) / len(_s)                # z_NED_EKF − (−z_GT); > 0: EKF sądzi, że jest poniżej originu
    _ep2 = dict(exec_params)
    _ep2["z_orb_alt_m"] = exec_params["z_orb_alt_m"] - Z_OFF
    json.dump({"z_off_m": round(Z_OFF, 4), "okno_sim_s": round(_s[-1][0] - _s[0][0], 2), "n": len(_s), "z_orb_alt_m_kanon": exec_params["z_orb_alt_m"], "z_orb_alt_m_kom": round(_ep2["z_orb_alt_m"], 4),
               "home_alt_kom": round(C.ALT_M - Z_OFF, 4), "feed": FEED_NAME}, open(os.path.join(OUTDIR, "kont_offset.json"), "w"), indent=1)
    exec_params = _ep2
    json.dump({"preflight": echo, "cut": KC.KONT_CUT, "fuse_r_gt_m": FUSE_M, "episode_id": EP_ID, "scenario_id": ep["scenario_id"],
               "window_s": WINDOW_S, "inject_t": INJECT_T, "hold_s": HOLD_S, "feed": FEED_NAME, "z_off_m": round(Z_OFF, 4),
               "nota_fuse": "bezpiecznik sondy, nie część projektu (PROMPT_KONT_S1 §3)"},
              open(os.path.join(OUTDIR, "kont_echo.json"), "w"), ensure_ascii=False, indent=1)
    try:
        healthy = await asyncio.wait_for(_wait_health(d), timeout=45)
    except asyncio.TimeoutError:
        healthy = False
    if not healthy:
        print("[kont] HEALTH TIMEOUT", flush=True); os._exit(3)

    shield = PatrolShield(); shield.reset()
    shield.pos_debounce_ticks = C.DEBOUNCE_TICKS
    shield.pos_hyst_ticks = int(round(C.HYST_M_S / C.DT))
    fh = open(OUT, "w"); _f = fh; _running = True
    HOME_Z = -C.ALT_M + Z_OFF
    ctrl = make_controller("net_skan2", params=exec_params, orbit_dir=ep["orbit_dir"], vmax=V_MAX, home_ned=(0.0, 0.0, HOME_Z))
    _w({"t": "meta", "flight": "kont_probe", "world": WORLD, "model": MODEL, "controller": "net_skan2+OrbitExecutor", "z_off_m": round(Z_OFF, 4), "controller_sha": controller_sha(ctrl),
        "scenario_id": ep["scenario_id"], "episode_id": EP_ID, "echo": echo, "fuse_m": FUSE_M, "window_s": WINDOW_S, "inject_t": INJECT_T})
    gn.subscribe(Pose_V, f"/world/{WORLD}/pose/info", _intr_pose_cb)

    def ev(s, **kw):
        _w({"t": "event", "mono": round(time.monotonic(), 4), "sim": round(_sim_t[0], 4), "ev": s, **kw})
        print(f"[kont] {s} sim={_sim_t[0]:.2f} {kw}", flush=True)

    # ANEKS_KONT-2b §2: asercja startowa yaw, próg 10°
    _yb = None
    for _ in range(50):
        if ekf.m is not None and _gt.get("q") is not None:
            _yb = _yaw_blad_deg(float(ekf.m.heading), *_gt["q"]); break
        await asyncio.sleep(0.1)
    _y_ok = _yb is not None and abs(_yb) <= YAW_ASSERT_DEG
    json.dump({"yaw_blad_deg": None if _yb is None else round(_yb, 2), "prog_deg": YAW_ASSERT_DEG, "ok": _y_ok}, open(os.path.join(OUTDIR, "kont_yaw.json"), "w"))
    ev("yaw_assert", yaw_blad_deg=None if _yb is None else round(_yb, 2), ok=_y_ok)
    if not _y_ok:
        fh.flush(); print("[kont] ASERCJA YAW", flush=True); os._exit(7)

    im_proc = subprocess.Popen([sys.executable, "-m", "harness.intruder_motion", "--world", WORLD, "--manifest", MANIFEST, "--outdir", OUTDIR],
                               cwd=ROOT, env={**os.environ, "PYTHONPATH": f".:{os.environ.get('PYTHONPATH', '')}"})
    _write_control("idle")
    armed = False
    for _ in range(40):
        try:
            await d.action.arm(); armed = True; break
        except (ActionError, Exception):
            await asyncio.sleep(3)
    if not armed:
        print("[kont] ARM FAILED", flush=True); os._exit(2)
    for _ in range(50):
        if _gt["x"] is not None:
            break
        await asyncio.sleep(0.1)
    if _gt["x"] is None:
        print("[kont] brak GT", flush=True); os._exit(5)
    gx0, gy0 = _gt["x"], _gt["y"]
    ev("armed", gt_home=[round(gx0, 3), round(gy0, 3)])
    await d.action.set_takeoff_altitude(C.ALT_M); await d.action.takeoff(); ev("takeoff")
    await asyncio.sleep(12)
    await d.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
    try:
        await d.offboard.start(); ev("offboard")
    except OffboardError as e:
        print("[kont] offboard err", e, flush=True); os._exit(4)

    def r_gt():
        return math.hypot(_gt["x"] - gx0, _gt["y"] - gy0)

    def gt_stale():
        return time.monotonic() - _gt["mono"] > GT_STALE_S

    t_hold = time.monotonic()
    while time.monotonic() - t_hold < HOLD_S:              # nominał w powietrzu przed epizodem (≥ 60 s przed odcięciem, §3 iii)
        await d.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0)); await asyncio.sleep(DT)
    from r02.intruder_driver import GzPoseClient
    # powrót nad home
    t0w = time.monotonic()
    while time.monotonic() - t0w < RESET_MAX:
        m = ekf.m
        if m is None:
            await asyncio.sleep(0.05); continue
        dx, dy = -float(m.x), -float(m.y); dh = math.hypot(dx, dy); vh = math.hypot(float(m.vx), float(m.vy))
        if dh < 1.0 and vh < 0.3:
            break
        ux, uy = (dx / dh, dy / dh) if dh > 1e-6 else (0.0, 0.0)
        await d.offboard.set_velocity_ned(VelocityNedYaw(min(V_MAX, 0.6 * dh) * ux, min(V_MAX, 0.6 * dh) * uy, 0.6 * (HOME_Z - float(m.z)), 0))
        await asyncio.sleep(DT)
    # bramka startu intruza (jak bench_flight)
    px, py, pz = S.position_at(ep, 0.0)
    gz_start, start_ned = scenario_to_gz(px, py, pz)
    cli = GzPoseClient(WORLD, apply_hz=SETPOSE_HZ)
    ok = False; t0 = _sim_t[0]
    while _sim_t[0] - t0 < 10.0:
        cli.set_pose(*gz_start)
        await d.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
        g = _intr_gz[0]
        if g is not None and math.dist(gz_to_ned(g), start_ned) <= TOL_START:
            ok = True; break
        await asyncio.sleep(DT)
    cli.close()
    ev("intruder_start_gate", ok=ok)
    feed, tf = make_feed(FEED_NAME, seed=ep["seed"], world=WORLD)
    ctrl.reset()
    t0_sim = _sim_t[0]
    _write_control("start", episode_id=EP_ID, t0_sim=t0_sim)
    ev("episode_start", episode_id=EP_ID, scenario_id=ep["scenario_id"], t0_sim=round(t0_sim, 3))

    t_entry = None; cut_done = False; t_cut_rel = None; reason = None; tick = 0; last_dec = None; t_w0 = time.monotonic()
    while ok:
        now_sim = _sim_t[0]; t_rel = now_sim - t0_sim
        m = ekf.m
        if m is None:
            await asyncio.sleep(0.05); continue
        own = [float(m.x), float(m.y), float(m.z)]; vel = [float(m.vx), float(m.vy), float(m.vz)]
        fs = feed.sample(now_sim)
        ctrl.set_feed(fs)
        cmd = ctrl.step(tick, own, vel, now_sim, False)
        dband = cmd["extra"].get("d")
        if t_entry is None and dband is not None and 6.0 <= dband <= 10.0:
            t_entry = t_rel; ev("entry", t_entry=round(t_entry, 3))
        if t_entry is not None and not cut_done and t_rel >= t_entry + INJECT_T:
            mono_before = time.monotonic()
            await d.param.set_param_int(*KC.KONT_CUT)
            cut_done = True; t_cut_rel = t_rel
            _g = _intr_gz[0]
            _e_trk = (math.dist(fs["trk_pos_ned"][:2], gz_to_ned(_g)[:2]) if (_g is not None and fs.get("track_valid")) else None)
            ev("cut", t_rel=round(t_rel, 3), param_rtt_s=round(time.monotonic() - mono_before, 4), r_gt=round(r_gt(), 2),
               xy_valid=bool(m.xy_valid), track_valid=bool(fs.get("track_valid")), blad_tracku_m=(round(_e_trk, 2) if _e_trk is not None else None))
        dec = shield.step(tick, own, vel, cmd["tgt_ned"], mode=M_PATROL, pos_flag=bool(m.dead_reckoning))
        key = (dec["decision"], dec.get("reason"))
        if key != last_dec:
            ev("shield_bierna", decision=str(dec["decision"]), reason=str(dec.get("reason")), cut=cut_done)
            last_dec = key
        v = cmd["v_ned"]
        await d.offboard.set_velocity_ned(VelocityNedYaw(v[0], v[1], v[2], math.degrees(cmd.get("yaw", 0.0))))
        _w({"t": "ctl", "mono": round(time.monotonic(), 4), "sim": round(now_sim, 4), "phase": cmd["extra"].get("phase"), "d": dband,
            "v": [round(x, 3) for x in v], "r_gt": round(r_gt(), 3), "r_est": round(math.hypot(own[0], own[1]), 3),
            "trk_valid": bool(fs.get("track_valid")), "trk_age": round(float(fs.get("track_age_s", 1e9)), 3), "trk": [round(x, 3) for x in fs["trk_pos_ned"]],
            "intr": ([round(x, 3) for x in gz_to_ned(_intr_gz[0])] if _intr_gz[0] is not None else None)})
        tick += 1
        if r_gt() >= FUSE_M:
            reason = "fuse_r_gt"
        elif gt_stale():
            reason = "gt_stale"
        elif _gt["z"] < Z_GROUND and cut_done:
            reason = "gt_ziemia_w_oknie"
        elif not cut_done and dec["decision"] == REFUSE and dec.get("reason") == POS_DEGRADED:
            reason = "refuse_pos_nominal_STOP"
        elif cut_done and t_rel >= t_cut_rel + WINDOW_S:
            reason = "koniec_okna"
        elif t_entry is None and t_rel > ENTRY_MAX:
            reason = "brak_wejscia"
        elif time.monotonic() - t_w0 > 300.0:
            reason = "wall_timeout"
        if reason:
            break
        await asyncio.sleep(DT)
    ev("descent_start", reason=reason or "brak_bramki_intruza", r_gt=round(r_gt(), 2), t_rel=round(_sim_t[0] - t0_sim, 3),
       okno_s=round(_sim_t[0] - t0_sim - t_cut_rel, 2) if t_cut_rel is not None else None)
    _write_control("idle")
    yaw_dec = math.degrees(float(ekf.m.heading)) if ekf.m is not None else 0.0   # ANEKS_KONT-2b §2: heading z chwili decyzji
    ev("yaw_hold", yaw_decyzji_deg=round(yaw_dec, 2))
    sd = new_state(); td = False; t_d = time.monotonic(); r_max_d = r_gt()
    while time.monotonic() - t_d < DESC_MAX_S:
        if not td:                                         # koniec profilu ≠ przyziemienie (ANEKS_KONT-0 E2): potem v_land do GT z<0.15
            v_z, evs, td, sd = safe_descend_step(sd, time.monotonic(), _SD_CFG)
            for e in evs:
                ev(e)
        else:
            v_z = C.V_DESC_LAND
        await d.offboard.set_velocity_ned(VelocityNedYaw(0, 0, v_z, yaw_dec))
        r_max_d = max(r_max_d, r_gt())
        if r_gt() > C.R_E:
            ev("breach", r_gt=round(r_gt(), 2))
        if _gt["z"] < Z_GROUND:
            ev("gt_przyziemienie", z=round(_gt["z"], 3), r_gt=round(r_gt(), 2)); break
        await asyncio.sleep(DT)
    ev("descent_end", r_max_zejscie=round(r_max_d, 2))
    try:
        await d.offboard.stop()
    except Exception:
        pass
    try:
        await d.action.land()
    except Exception:
        pass
    await asyncio.sleep(8)
    _write_control("stop")
    await asyncio.sleep(1)
    with _lock:
        _running = False
    _running_spin[0] = False
    im_proc.terminate()
    ekf.destroy_node(); rclpy.shutdown(); fh.close()
    print(f"[kont] done -> {OUT}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
