#!/usr/bin/env python3
"""
tools/infra1_empty_flight.py — INFRA-1 I3: PUSTY lot walidacyjny (BEZ denialu, BEZ sędziego, BEZ K1).

Scenariusz: connect → health → arm → takeoff(ALT) → 10 s ustabilizowanie → OFFBOARD hover (vel 0,0,0)
przez HOVER_S s → land → touchdown(GT z≤0.5) → disarm. Cel: zmierzyć czy zahartowany boot (I2)
armuje i utrzymuje zdrowy lockstep na 60 s okna hoveru. NIE dotyka osłony/sędziego/kryteriów K1,
NIE zmienia parametrów PX4 (EKF2_GPS_CTRL zostaje 7 — higiena zrobiona w run_k1_boot.sh).

Trace (GATE_OUT jsonl): gt {sim,x,y,z}, ekf, event {armed,takeoff,offboard,hover_start(sim),
hover_end(sim),land_cmd,touchdown,done | arm_fail}. Habitat liczony offline z okna [hover_start,hover_end].
Env: GATE_OUT, PX4_GZ_WORLD, B1_MODEL, K1_HOVER_S (dom. 60).
"""
import os, sys, json, time, math, threading
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

OUT = os.environ.get("GATE_OUT", "/tmp/infra1e/trace.jsonl")
WORLD = os.environ.get("PX4_GZ_WORLD", "default")
MODEL = os.environ.get("B1_MODEL", "x500_mono_cam_0")
HOVER_S = float(os.environ.get("K1_HOVER_S", "60"))
GT_TOPIC = f"/world/{WORLD}/dynamic_pose/info"
ALT = 8.0
DT = 0.05
HEALTH_WAIT_TIMEOUT_S = 60
QOS = QoSProfile(depth=1, history=HistoryPolicy.KEEP_LAST, reliability=ReliabilityPolicy.BEST_EFFORT)

_lock = threading.Lock(); _f = None; _running = False
_gt_last = [0.0]
_last_gt = {"sim": None, "x": None, "y": None, "z": None}


def _w(row):
    with _lock:
        if _f is not None and _running:
            _f.write(json.dumps(row) + "\n")


def ev(s, **extra):
    row = {"t": "event", "mono": round(time.monotonic(), 4), "ev": s}
    row.update(extra)
    _w(row)
    print(f"[E] EVENT {s} mono={row['mono']} {extra}", flush=True)


def gt_cb(msg):
    now = time.monotonic()
    if now - _gt_last[0] < 1.0 / 50:
        return
    for p in msg.pose:
        if p.name == MODEL:
            sim = msg.header.stamp.sec + msg.header.stamp.nsec / 1e9
            _w({"t": "gt", "mono": round(now, 4), "sim": round(sim, 4),
                "x": round(p.position.x, 5), "y": round(p.position.y, 5), "z": round(p.position.z, 5)})
            _last_gt.update(sim=sim, x=p.position.x, y=p.position.y, z=p.position.z)
            _gt_last[0] = now
            return


class EkfSub(Node):
    def __init__(self):
        super().__init__("infra1e_ekf")
        self.m = None
        self.create_subscription(VehicleLocalPosition, "/fmu/out/vehicle_local_position", self._cb, QOS)

    def _cb(self, m):
        self.m = m
        _w({"t": "ekf", "mono": round(time.monotonic(), 4), "ts": round(m.timestamp / 1e6, 4),
            "x": round(float(m.x), 4), "y": round(float(m.y), 4), "z": round(float(m.z), 4),
            "vx": round(float(m.vx), 4), "vy": round(float(m.vy), 4),
            "eph": round(float(m.eph), 4), "dead_reckoning": bool(m.dead_reckoning),
            "xy_reset_counter": int(m.xy_reset_counter)})


async def _wait_health(d):
    async for h in d.telemetry.health():
        if h.is_global_position_ok and h.is_home_position_ok:
            return
    raise TimeoutError


async def arm_retry(d):
    for i in range(40):
        try:
            await d.action.arm(); return True
        except ActionError:
            if i % 5 == 0:
                print(f"[E] arm niegotowe (preflight) retry #{i}", flush=True)
            await asyncio.sleep(3)
    return False


async def main():
    global _f, _running
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    _f = open(OUT, "w"); _running = True

    gz = GzNode(); gz.subscribe(Pose_V, GT_TOPIC, gt_cb)
    rclpy.init()
    ekf = EkfSub()
    stop = threading.Event()

    def _spin():
        while not stop.is_set():
            rclpy.spin_once(ekf, timeout_sec=0.1)
    threading.Thread(target=_spin, daemon=True).start()

    d = System()
    await d.connect(system_address="udpin://0.0.0.0:14540")
    async for s in d.core.connection_state():
        if s.is_connected:
            break

    _w({"t": "meta", "arm": "E", "scen": "INFRA1-empty", "alt": ALT, "hover_s": HOVER_S,
        "world": WORLD, "model": MODEL})

    try:
        await asyncio.wait_for(_wait_health(d), HEALTH_WAIT_TIMEOUT_S)
    except (asyncio.TimeoutError, TimeoutError):
        ev("health_timeout")
        print("[E] health timeout", flush=True)
        _running = False; _f.close(); os._exit(3)

    await d.action.set_takeoff_altitude(ALT)
    if not await arm_retry(d):
        ev("arm_fail")
        print("[E] ARM FAILED", flush=True)
        _running = False; _f.close(); os._exit(2)
    ev("armed", sim=(round(_last_gt["sim"], 4) if _last_gt["sim"] is not None else None))
    await d.action.takeoff(); ev("takeoff", sim=(round(_last_gt["sim"], 4) if _last_gt["sim"] is not None else None))
    await asyncio.sleep(10)

    await d.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
    try:
        await d.offboard.start(); ev("offboard", sim=(round(_last_gt["sim"], 4) if _last_gt["sim"] is not None else None))
    except OffboardError as e:
        ev("offboard_fail", err=str(e))
        print(f"[E] offboard err {e}", flush=True); os._exit(5)

    # --- 60 s hover OFFBOARD (setpoint 0,0,0) — okno roszczenia habitatu pustego lotu ---
    ev("hover_start", sim=(round(_last_gt["sim"], 4) if _last_gt["sim"] is not None else None),
       gt_z=(round(_last_gt["z"], 3) if _last_gt["z"] is not None else None))
    t_h = time.monotonic()
    while time.monotonic() - t_h < HOVER_S:
        await d.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
        await asyncio.sleep(DT)
    ev("hover_end", sim=(round(_last_gt["sim"], 4) if _last_gt["sim"] is not None else None),
       gt_z=(round(_last_gt["z"], 3) if _last_gt["z"] is not None else None))

    # --- land + touchdown z GT ---
    ev("land_cmd")
    try:
        await d.action.land()
    except ActionError as e:
        ev("land_err", err=str(e))
    t_l = time.monotonic()
    airborne_seen = False
    while True:
        el = time.monotonic() - t_l
        z = _last_gt["z"]
        if z is not None and z >= 1.0:
            airborne_seen = True
        if airborne_seen and z is not None and z <= 0.5:
            ev("touchdown", gt_z=round(z, 3))
            break
        if el > 90:
            ev("timeout_land", gt_z=(round(z, 3) if z is not None else None))
            break
        await asyncio.sleep(0.1)

    _w({"t": "outcome", "arm": "E", "hover_s": HOVER_S})
    ev("done")
    await asyncio.sleep(2)
    try:
        await d.action.disarm()
    except Exception:
        pass
    stop.set()
    _running = False
    _f.close()
    print("[E] KONIEC", flush=True)
    try:
        rclpy.shutdown()
    except Exception:
        pass
    sys.stdout.flush(); sys.stderr.flush()
    os._exit(0)


if __name__ == "__main__":
    asyncio.run(main())
