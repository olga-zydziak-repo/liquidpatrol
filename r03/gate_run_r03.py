#!/usr/bin/env python3
"""
r03/gate_run_r03.py — BRAMKA R0.3a (GPS-DENIED), OSŁONA W PĘTLI. Jeden scenariusz per uruchomienie.

Osłona (r01.shield.PatrolShield) decyduje co tick; pos_flag = dead_reckoning (R1). Na
REFUSE(POS_DEGRADED) egzekutor stosuje AKCJĘ BEZPIECZNĄ = zejście STEROWANE PRĘDKOŚCIĄ dwufazowe
(1.5→0.7 m/s, v_xy=0; D5 zrew. §3quater; AUTO.LAND WYKLUCZONY). GT (gz) WYŁĄCZNIE sędzią (nigdy w
decyzji). Setpointy przez offboard velocity. Świeży boot per bieg (woła caller). Params restore (SR-B5).

Scenariusze (env SCEN): S1 nominal (bez denialu, N min) | S2 denial w patrolu | S3 denial+recovery |
S4 cięcie narożnik v_max + denial. Kryteria D13 liczone w judge (osobno, po biegu, z GT).

Env: SCEN, GATE_OUT (jsonl), S1_MIN (dla S1), boot już wstał (świeży, ≥90 s konwergencji EKF).
"""
import os, json, time, math, threading
import asyncio
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from px4_msgs.msg import VehicleLocalPosition
from gz.transport13 import Node as GzNode
from gz.msgs10.pose_v_pb2 import Pose_V
from mavsdk import System
from mavsdk.offboard import VelocityNedYaw, OffboardError
from mavsdk.action import ActionError

from r01.shield import PatrolShield, REFUSE, POS_DEGRADED, M_PATROL
from r03 import config as C

SCEN = os.environ.get("SCEN", "S2")
OUT = os.environ.get("GATE_OUT", f"/tmp/r03gate/{SCEN}.jsonl")
S1_MIN = float(os.environ.get("S1_MIN", "5"))
WORLD = os.environ.get("PX4_GZ_WORLD", "default")
MODEL = os.environ.get("B1_MODEL", "x500_mono_cam_0")
GT_TOPIC = f"/world/{WORLD}/dynamic_pose/info"
from r01.config import V_MAX as VMAX
ALT = 8.0
QOS = QoSProfile(depth=1, history=HistoryPolicy.KEEP_LAST, reliability=ReliabilityPolicy.BEST_EFFORT)

_lock = threading.Lock(); _f = None; _running = False
_gt_last = [0.0]


def _w(row):
    with _lock:
        if _f is not None and _running:
            _f.write(json.dumps(row) + "\n")


def gt_cb(msg):
    now = time.monotonic()
    if now - _gt_last[0] < 1.0 / 50:
        return
    for p in msg.pose:
        if p.name == MODEL:
            sim = msg.header.stamp.sec + msg.header.stamp.nsec / 1e9
            _w({"t": "gt", "mono": round(now, 4), "sim": round(sim, 4),
                "x": round(p.position.x, 5), "y": round(p.position.y, 5), "z": round(p.position.z, 5)})
            _gt_last[0] = now
            return


class EkfSub(Node):
    def __init__(self):
        super().__init__("gate_ekf")
        self.m = None
        self.create_subscription(VehicleLocalPosition, "/fmu/out/vehicle_local_position", self._cb, QOS)

    def _cb(self, m):
        self.m = m
        _w({"t": "ekf", "mono": round(time.monotonic(), 4), "ts": round(m.timestamp / 1e6, 4),
            "x": round(float(m.x), 4), "y": round(float(m.y), 4), "z": round(float(m.z), 4),
            "vx": round(float(m.vx), 4), "vy": round(float(m.vy), 4),
            "eph": round(float(m.eph), 4), "dead_reckoning": bool(m.dead_reckoning),
            "xy_reset_counter": int(m.xy_reset_counter)})


async def arm_retry(d):
    for i in range(40):
        try:
            await d.action.arm(); return True
        except (ActionError, Exception):    # ActionError (preflight) LUB gRPC (serwer wstaje)
            if i % 5 == 0:
                print(f"[gate] arm niegotowe retry #{i}", flush=True)
            await asyncio.sleep(3)
    return False


async def main():
    global _f, _running
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    gn = GzNode()
    rclpy.init()
    ekf = EkfSub()
    d = System(); await d.connect(system_address="udpin://0.0.0.0:14540")
    async for s in d.core.connection_state():
        if s.is_connected:
            break
    gps_old = await d.param.get_param_int("EKF2_GPS_CTRL")
    hgt_old = await d.param.get_param_int("EKF2_HGT_REF")
    await d.param.set_param_int("EKF2_HGT_REF", 0)   # Baro (§3quater)
    async for h in d.telemetry.health():
        if h.is_global_position_ok and h.is_home_position_ok:
            break

    shield = PatrolShield(); shield.reset()
    shield.pos_debounce_ticks = C.DEBOUNCE_TICKS
    shield.pos_hyst_ticks = int(round(C.HYST_M_S / C.DT))

    fh = open(OUT, "w"); _f = fh; _running = True
    _w({"t": "meta", "scen": SCEN, "eps_cap": C.EPS_CAP, "R_E": shield.cfg.r_e,
        "half_p": C.HALF_P, "vmax": VMAX, "debounce": C.DEBOUNCE_TICKS,
        "note": "osłona w pętli; GT=sędzia; velocity-descent dwufazowy na POS_DEGRADED"})
    gn.subscribe(Pose_V, GT_TOPIC, gt_cb)

    def ev(s):
        _w({"t": "event", "mono": round(time.monotonic(), 4), "ev": s})
        print(f"[gate {SCEN}] {s} mono={time.monotonic():.3f}", flush=True)

    if not await arm_retry(d):
        print("[gate] ARM FAILED", flush=True); return
    ev("armed")
    await d.action.set_takeoff_altitude(ALT); await d.action.takeoff(); ev("takeoff")
    await asyncio.sleep(10)
    await d.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
    try:
        await d.offboard.start(); ev("offboard")
    except OffboardError as e:
        print("[gate] offboard err", e, flush=True); return

    # spin ekf w tle
    def spin():
        while _running and rclpy.ok():
            rclpy.spin_once(ekf, timeout_sec=0.02)
    th = threading.Thread(target=spin, daemon=True); th.start()

    # --- pętla OSŁONY (20 Hz) ---
    wps = C.corner_waypoints_r03()          # trasa zredukowana (NED)
    tick = 0
    denial_done = False
    recovery_done = False
    landed = False
    t_start = time.monotonic()
    # czas denialu: S2/S4 po ~1 nodze patrolu; S1 nigdy; S3 denial potem recovery
    denial_at = 12.0 if SCEN in ("S2", "S3", "S4") else 1e9
    recovery_at = denial_at + 8.0 if SCEN == "S3" else 1e9
    s1_dur = S1_MIN * 60.0 if SCEN == "S1" else 1e9
    leg = 4.0
    seg_i = 0
    # dla S4: cięcie w narożniku — denial gdy zmiana kierunku
    vmax_scale = 1.0
    while True:
        now = time.monotonic() - t_start
        m = ekf.m
        if m is None:
            await asyncio.sleep(0.05); continue
        pos = (float(m.x), float(m.y), float(m.z))
        vel = (float(m.vx), float(m.vy), 0.0)
        dr = bool(m.dead_reckoning)
        # denial injection. S4: cięcie PRZY NAROŻNIKU (po dojściu do 1. waypointa = zmiana kierunku
        # przy v_max) — worst-case stanu prędkości. S2/S3: w patrolu (mid-leg). S1: nigdy.
        if SCEN == "S4":
            trigger = (not denial_done) and seg_i >= 1 and dist < 3.0 and now >= 8.0
        else:
            trigger = (not denial_done) and now >= denial_at
        if trigger:
            await d.param.set_param_int("EKF2_GPS_CTRL", 0); ev("denial_on"); denial_done = True
        if SCEN == "S3" and denial_done and not recovery_done and now >= recovery_at:
            await d.param.set_param_int("EKF2_GPS_CTRL", int(gps_old)); ev("denial_off"); recovery_done = True
        # target: patrol po trasie (velocity ku waypointowi), v_max
        wp = wps[seg_i % len(wps)]
        dx, dy = wp[0] - pos[0], wp[1] - pos[1]
        dist = math.hypot(dx, dy)
        if dist < 1.0:
            seg_i += 1
        tgt = (wp[0], wp[1], -ALT)
        # shield decyzja
        d_dec = shield.step(tick, pos, vel, tgt, mode=M_PATROL, pos_flag=(dr if denial_done else None))
        # zastosuj decyzję
        if d_dec["decision"] == REFUSE and d_dec.get("reason") == POS_DEGRADED:
            if not landed:
                ev("refuse_pos_land")
                # AKCJA BEZPIECZNA: zejście dwufazowe velocity (v_xy=0)
                t1 = time.monotonic() + max(0.0, (ALT - C.H_SWITCH_AGL) / C.V_DESC_FAST)
                while time.monotonic() < t1:
                    await d.offboard.set_velocity_ned(VelocityNedYaw(0, 0, C.V_DESC_FAST, 0)); await asyncio.sleep(0.05)
                ev("h_switch")
                t2 = time.monotonic() + (C.H_SWITCH_AGL / C.V_DESC_LAND + 2.0)
                while time.monotonic() < t2:
                    await d.offboard.set_velocity_ned(VelocityNedYaw(0, 0, C.V_DESC_LAND, 0)); await asyncio.sleep(0.05)
                ev("touchdown"); landed = True
                break
        else:
            # patrol: velocity ku waypointowi, clamp v_max
            if dist > 1e-3:
                vn = VMAX * dx / dist; ve = VMAX * dy / dist
            else:
                vn = ve = 0.0
            await d.offboard.set_velocity_ned(VelocityNedYaw(vn, ve, 0, 0))
        tick += 1
        # S1: zakończ po s1_dur (bez denialu)
        if SCEN == "S1" and now >= s1_dur:
            ev("s1_done"); break
        # bezpiecznik czasu
        if now > (denial_at + 60 if denial_done else 400):
            ev("timeout"); break
        await asyncio.sleep(C.DT)

    # księgowość osłony + telemetria
    _w({"t": "outcome", "n_pos_enter": shield.n_pos_enter,
        "terminal": (shield.terminal[0] if shield.terminal else None)})
    ev("done")
    await asyncio.sleep(2)
    # restore params (SR-B5)
    await d.param.set_param_int("EKF2_GPS_CTRL", int(gps_old))
    await d.param.set_param_int("EKF2_HGT_REF", int(hgt_old))
    print(f"[gate {SCEN}] restored GPS_CTRL={gps_old} HGT_REF={hgt_old}", flush=True)
    try:
        await d.offboard.stop()
    except Exception:
        pass
    try:
        await d.action.disarm()
    except Exception:
        pass
    with _lock:
        _running = False
    ekf.destroy_node(); rclpy.shutdown(); fh.close()
    print(f"[gate {SCEN}] done -> {OUT}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
