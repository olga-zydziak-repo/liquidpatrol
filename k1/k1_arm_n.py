#!/usr/bin/env python3
"""
k1_arm_n.py — RAMIĘ N (natywny failsafe PX4) dla K1 (PRE_K1 §2, ridery R3).

Lot OFFBOARD velocity na trasie zredukowanej (corner_waypoints_r03, VMAX=3, ALT=8), IDENTYCZNY do
punktu wstrzyknięcia co ramię S. W punkcie (seg_i==1, ułamek nogi K1_POINT):
  R3(i)   d.param.set_param_int("EKF2_GPS_CTRL", 0)   — stempel = ack paramu (mono; sim z nearest gt)
  R3(ii)  NATYCHMIAST d.action.land()                 — stempel komendy + stempel acku (mono, result)
  R3(iii) strumień setpointów offboard MILKNIE DOPIERO PO acku land (nie wcześniej — inaczej
          COM_OF_LOSS_T odpala offboard-loss failsafe = INNA ścieżka niż PRE §1).
Ack ≠ ACCEPTED przy δ=0 to WYNIK, nie błąd (log z cytatem). Od acku land PX4 robi swoje (AUTO_LAND→…).
GT (gz) i EKF (px4) logowane przez cały epizod; touchdown wykrywany z GT z≤0.5 (sędzia też).
Params NIE dotykane poza EKF2_GPS_CTRL (SR-K6); restore po touchdown.

Env: GATE_OUT (jsonl trace), K1_POINT, PX4_GZ_WORLD, B1_MODEL. Boot już wstał (≥90 s konwergencji).
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

from r03 import config as C
from r01.config import V_MAX as VMAX

OUT = os.environ.get("GATE_OUT", "/tmp/k1n/trace.jsonl")
K1_POINT = float(os.environ.get("K1_POINT", "0.5"))
WORLD = os.environ.get("PX4_GZ_WORLD", "default")
MODEL = os.environ.get("B1_MODEL", "x500_mono_cam_0")
GT_TOPIC = f"/world/{WORLD}/dynamic_pose/info"
ALT = 8.0
HEALTH_WAIT_TIMEOUT_S = 45
QOS = QoSProfile(depth=1, history=HistoryPolicy.KEEP_LAST, reliability=ReliabilityPolicy.BEST_EFFORT)

_lock = threading.Lock(); _f = None; _running = False
_gt_last = [0.0]
_last_gt = {"sim": None, "x": None, "y": None, "z": None}   # do detekcji touchdown + sim-stamp


def _w(row):
    with _lock:
        if _f is not None and _running:
            _f.write(json.dumps(row) + "\n")


def ev(s, **extra):
    row = {"t": "event", "mono": round(time.monotonic(), 4), "ev": s}
    row.update(extra)
    _w(row)
    print(f"[k1N] EVENT {s} mono={row['mono']} {extra}", flush=True)


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
        super().__init__("k1n_ekf")
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
                print(f"[k1N] arm niegotowe (preflight) retry #{i}", flush=True)
            await asyncio.sleep(3)
    return False


async def main():
    global _f, _running
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    _f = open(OUT, "w"); _running = True

    # GT (gz) w tle
    gz = GzNode(); gz.subscribe(Pose_V, GT_TOPIC, gt_cb)
    # EKF (rclpy) w tle
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

    # preflight assert (R-D1 jak r03) — poison EKF2_GPS_CTRL≠7 ⇒ INVALID
    poison = False
    for p, want in C.HARNESS_PARAM_PREFLIGHT.items():
        try:
            got = await d.param.get_param_int(p)
        except Exception:
            got = None
        if p in C.HARNESS_PARAM_POISON_CRITICAL and got != want:
            poison = True
        try:
            await d.param.set_param_int(p, want)
        except Exception as e:
            print(f"[k1N] preflight set {p} err {e}", flush=True)
    _w({"t": "meta", "arm": "N", "scen": "K1", "k1_point": K1_POINT, "alt": ALT,
        "vmax": VMAX, "world": WORLD, "model": MODEL, "harness_poison": poison,
        "harness_valid": (not poison)})
    if poison:
        ev("harness_invalid", reason="EKF2_GPS_CTRL poison on entry")
        _running = False; _f.close(); os._exit(4)

    try:
        await asyncio.wait_for(_wait_health(d), HEALTH_WAIT_TIMEOUT_S)
    except (asyncio.TimeoutError, TimeoutError):
        print("[k1N] health timeout", flush=True); os._exit(3)

    await d.action.set_takeoff_altitude(ALT)
    if not await arm_retry(d):
        print("[k1N] ARM FAILED", flush=True); os._exit(2)
    ev("armed")
    await d.action.takeoff(); ev("takeoff")
    await asyncio.sleep(10)
    await d.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
    try:
        await d.offboard.start(); ev("offboard")
    except OffboardError as e:
        print(f"[k1N] offboard err {e}", flush=True); os._exit(5)

    wps = C.corner_waypoints_r03()
    seg_i = 0
    t_start = time.monotonic()
    injected = False
    landed_ack = None

    # --- lot do punktu wstrzyknięcia (OFFBOARD velocity), potem R3 ---
    while True:
        now = time.monotonic() - t_start
        m = ekf.m
        if m is None:
            await asyncio.sleep(0.05); continue
        pos = (float(m.x), float(m.y), float(m.z))
        wp = wps[seg_i % len(wps)]
        dx, dy = wp[0] - pos[0], wp[1] - pos[1]
        dist = math.hypot(dx, dy)
        if dist < 1.0:
            seg_i += 1
        # trigger K1: pierwsza noga po pierwszym narożniku (seg_i==1), ułamek nogi
        _leg = math.hypot(wps[1][0] - wps[0][0], wps[1][1] - wps[0][1])
        _fa = (_leg - dist) / _leg if (seg_i == 1 and _leg > 1e-6) else -1.0
        if (not injected) and seg_i == 1 and _fa >= K1_POINT:
            # R3(i): param set EKF2_GPS_CTRL=0, stempel = ack paramu
            await d.param.set_param_int("EKF2_GPS_CTRL", 0)
            ev("denial_on", k1_point=K1_POINT, k1_f_along=round(_fa, 3),
               r_est_at_cut=round(math.hypot(pos[0], pos[1]), 3),
               pos=[round(v, 3) for v in pos])
            # R3(ii): NATYCHMIAST action.land(), stempel komendy + acku
            ev("land_cmd_sent")
            try:
                await d.action.land()
                ev("land_ack", result="ACCEPTED")
                landed_ack = "ACCEPTED"
            except ActionError as e:
                # ack ≠ ACCEPTED = WYNIK, nie błąd (R3)
                ev("land_ack", result=f"REJECTED:{e}")
                landed_ack = f"REJECTED:{e}"
            injected = True
            # R3(iii): setpointy MILKNĄ DOPIERO TERAZ (po acku) — wychodzimy z pętli setpointów
            break
        # setpoint offboard (przed wstrzyknięciem)
        vn, ve = (VMAX * dx / dist, VMAX * dy / dist) if dist > 1e-3 else (0.0, 0.0)
        await d.offboard.set_velocity_ned(VelocityNedYaw(vn, ve, 0, 0))
        if now > 300:
            ev("timeout_preinject"); os._exit(6)
        await asyncio.sleep(C.DT)

    # --- po acku land: PX4 robi swoje; NIE wysyłamy setpointów. Czekamy na touchdown z GT ---
    t_inj = time.monotonic()
    airborne_seen = False
    while True:
        el = time.monotonic() - t_inj
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

    _w({"t": "outcome", "arm": "N", "land_ack": landed_ack, "k1_point": K1_POINT})
    ev("done")
    await asyncio.sleep(2)
    # restore EKF2_GPS_CTRL (SR-B5); reszta paramów nie tknięta
    try:
        await d.param.set_param_int("EKF2_GPS_CTRL", C.HARNESS_PARAM_PREFLIGHT["EKF2_GPS_CTRL"])
    except Exception as e:
        print(f"[k1N] restore err {e}", flush=True)
    try:
        await d.action.disarm()
    except Exception:
        pass
    stop.set()
    _running = False
    _f.close()
    print("[k1N] KONIEC", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
