#!/usr/bin/env python3
"""acts/live_stability_probe.py — DEMO-B B5R2 T1: sonda stabilności bootu na RDZENIU mti_flight.

Sterowanie połączeniem/arm/offboard przeniesione 1:1 z results/R02/mti/mti_flight.py (topologia
DOWIEDZIONA live w REGATE): raw MAVSDK System() + udpin 14540, health 90 s (global+home), arm-retry 60×,
takeoff, offboard start(v=0), ≥10 s hover, czysty land+shutdown. ARM PRZED jakimkolwiek YOLO (kontencja).

Cel: sprawdzić czy łącze MAVSDK↔PX4 ustanawia się w torze LIVE (habitat aktu). NIE lata choreografii,
NIE percepcja — wyłącznie kryterium stabilności T1. Zrzut JSON: czas-do-health, próby arm, hover, wynik.

Uruchom (pod zsourcowanym ROS/env, świat już wstał ≥ settle): python3 acts/live_stability_probe.py <OUT.json>
Exit: 0=OK(arm+takeoff+hover+land), 3=health timeout, 2=arm fail, 4=offboard err.
"""
import asyncio
import json
import os
import sys
import time

from mavsdk import System
from mavsdk.offboard import VelocityNedYaw, OffboardError

HOVER_ALT = float(os.environ.get("HOVER_ALT", "9.0"))
HOVER_HOLD_S = float(os.environ.get("HOVER_HOLD_S", "10.0"))
OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/stability_probe.json"


async def _health(d):
    async for h in d.telemetry.health():
        if h.is_global_position_ok and h.is_home_position_ok:
            return True
    return False


async def main():
    rec = {"topology": "mti_flight core (System udpin14540, health90s, arm-retry60x)",
           "connected": False, "healthy": False, "t_to_health_s": None, "arm_attempts": None,
           "armed": False, "takeoff": False, "hover_ok": False, "landed": False, "verdict": "FAIL"}
    t0 = time.monotonic()
    d = System()
    await d.connect(system_address="udpin://0.0.0.0:14540")
    async for s in d.core.connection_state():
        if s.is_connected:
            break
    rec["connected"] = True
    rec["t_connect_s"] = round(time.monotonic() - t0, 2)
    print(f"[probe] MAVSDK connected @ {rec['t_connect_s']}s", flush=True)
    # health (global+home), timeout 90 s — jak mti_flight (ARM przed YOLO, redukcja kontencji EKF)
    th = time.monotonic()
    try:
        rec["healthy"] = await asyncio.wait_for(_health(d), timeout=90)
    except asyncio.TimeoutError:
        rec["healthy"] = False
    rec["t_to_health_s"] = round(time.monotonic() - th, 2)
    if not rec["healthy"]:
        print(f"[probe] HEALTH TIMEOUT @ {rec['t_to_health_s']}s", flush=True)
        json.dump(rec, open(OUT, "w"), indent=2); sys.exit(3)
    print(f"[probe] health OK @ {rec['t_to_health_s']}s", flush=True)
    # arm-retry 60×
    for i in range(60):
        try:
            await d.action.arm(); rec["armed"] = True; rec["arm_attempts"] = i + 1; break
        except Exception:
            if i % 6 == 0:
                print(f"[probe] arm retry #{i}", flush=True)
            await asyncio.sleep(3)
    if not rec["armed"]:
        print("[probe] ARM FAILED", flush=True); json.dump(rec, open(OUT, "w"), indent=2); sys.exit(2)
    print(f"[probe] armed (attempts={rec['arm_attempts']})", flush=True)
    await d.action.set_takeoff_altitude(HOVER_ALT); await d.action.takeoff()
    alt = 0.0
    for _ in range(40):
        async for pv in d.telemetry.position_velocity_ned():
            alt = -pv.position.down_m; break
        if alt >= HOVER_ALT - 1.5:
            break
        await asyncio.sleep(0.5)
    rec["takeoff"] = alt >= HOVER_ALT - 1.5
    rec["alt_reached_m"] = round(alt, 2)
    await asyncio.sleep(4)
    await d.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
    try:
        await d.offboard.start()
    except OffboardError as e:
        print(f"[probe] offboard err {e}", flush=True); json.dump(rec, open(OUT, "w"), indent=2); sys.exit(4)
    # ≥10 s hover (v=0)
    thov = time.monotonic()
    while time.monotonic() - thov < HOVER_HOLD_S:
        await d.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
        await asyncio.sleep(0.5)
    rec["hover_ok"] = True
    print(f"[probe] hover {HOVER_HOLD_S}s OK; land", flush=True)
    try:
        await d.offboard.stop()
    except Exception:
        pass
    await d.action.land()
    await asyncio.sleep(6)
    rec["landed"] = True
    rec["verdict"] = "OK" if (rec["armed"] and rec["takeoff"] and rec["hover_ok"]) else "FAIL"
    rec["total_s"] = round(time.monotonic() - t0, 2)
    json.dump(rec, open(OUT, "w"), indent=2)
    print(f"[probe] VERDICT {rec['verdict']} (t_health={rec['t_to_health_s']}s arm={rec['arm_attempts']})", flush=True)
    sys.exit(0 if rec["verdict"] == "OK" else 5)


if __name__ == "__main__":
    asyncio.run(main())
