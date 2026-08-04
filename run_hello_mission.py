#!/usr/bin/env python3
"""run_hello_mission.py — hello-mission R0.0 (bramka §1/§3/A4).
Arm -> start misji (takeoff + kilka waypointow) -> RTL(land) -> disarm.
Rownolegle: strumien pozycji z detekcja przerw >1s (A4). Wynik trojwartosciowy:
  PASS  — misja domknieta, land+disarm, brak przerwy >1s
  FAIL  — nie domknieto / przerwa telemetrii >1s
  (pad procesu = odnotowac osobno, wg A5)
Uzycie: python3 run_hello_mission.py
"""
import asyncio, sys, time
from mavsdk import System
from mavsdk.mission import MissionItem, MissionPlan

TIMEOUT_S = 240

def wp(lat, lon, alt, speed=5.0):
    return MissionItem(lat, lon, alt, speed,
                       True, float('nan'), float('nan'),
                       MissionItem.CameraAction.NONE, float('nan'), float('nan'),
                       float('nan'), float('nan'), float('nan'),
                       MissionItem.VehicleAction.NONE)

async def position_monitor(drone, state):
    """Strumien pozycji; wykrywa przerwy >1s (A4)."""
    last = None
    async for p in drone.telemetry.position():
        now = time.monotonic()
        if last is not None:
            gap = now - last
            if gap > state["max_gap"]:
                state["max_gap"] = gap
            if gap > 1.0:
                state["gap_violation"] = True
                print(f"[hm] !! przerwa pozycji {gap:.2f}s (>1s) — A4 naruszone")
        last = now
        state["last_alt"] = p.relative_altitude_m
        if state["done"]:
            break

async def main():
    state = {"max_gap": 0.0, "gap_violation": False, "done": False, "last_alt": 0.0}
    drone = System()
    await drone.connect(system_address="udpin://0.0.0.0:14540")
    print("[hm] laczenie…")
    async for s in drone.core.connection_state():
        if s.is_connected:
            print("[hm] POLACZONO"); break

    print("[hm] czekam na pozycje globalna + home…")
    async for h in drone.telemetry.health():
        if h.is_global_position_ok and h.is_home_position_ok:
            break

    # dom
    async for p in drone.telemetry.position():
        lat0, lon0 = p.latitude_deg, p.longitude_deg; break
    print(f"[hm] home: {lat0:.6f},{lon0:.6f}")

    ALT = 5.0
    D = 0.00018  # ~20 m
    items = [
        wp(lat0 + D, lon0,      ALT),
        wp(lat0 + D, lon0 + D,  ALT),
        wp(lat0,     lon0 + D,  ALT),
        wp(lat0,     lon0,      ALT),
    ]
    print(f"[hm] upload misji: {len(items)} waypointow, alt {ALT} m")
    await drone.mission.set_return_to_launch_after_mission(True)
    await drone.mission.upload_mission(MissionPlan(items))

    mon = asyncio.ensure_future(position_monitor(drone, state))

    print("[hm] arm…"); await drone.action.arm()
    t_start = time.monotonic()
    print("[hm] start misji…"); await drone.mission.start_mission()

    # postep misji
    async for mp in drone.mission.mission_progress():
        print(f"[hm] misja {mp.current}/{mp.total}  (alt={state['last_alt']:.1f}m)")
        if mp.total > 0 and mp.current >= mp.total:
            print("[hm] wszystkie waypointy osiagniete -> RTL"); break

    # czekaj na ladowanie + disarm
    print("[hm] czekam na land+disarm…")
    async for armed in drone.telemetry.armed():
        if not armed:
            print("[hm] DISARMED (wyladowano)"); break

    dur = time.monotonic() - t_start
    state["done"] = True
    mon.cancel()

    ok = (not state["gap_violation"])
    print(f"[hm] czas lotu (wall): {dur:.1f}s ; max przerwa pozycji: {state['max_gap']:.2f}s")
    print(f"[hm] WYNIK: {'PASS' if ok else 'FAIL'}  (misja domknieta + disarm; A4 gap_ok={ok})")
    return 0 if ok else 2

if __name__ == "__main__":
    try:
        rc = asyncio.run(asyncio.wait_for(main(), timeout=TIMEOUT_S))
        sys.exit(rc)
    except asyncio.TimeoutError:
        print("[hm] TIMEOUT — misja nie domknieta w limicie"); sys.exit(2)
