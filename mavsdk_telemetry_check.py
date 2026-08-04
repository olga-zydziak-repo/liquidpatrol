#!/usr/bin/env python3
"""mavsdk_telemetry_check.py — minimalny probe: polacz z PX4 SITL (udp:14540),
poczekaj na polaczenie + zdrowie, wydrukuj kilka probek pozycji. NIE lata.
Dowod plaszczyzny sterowania (czesc A4). Uzycie: python3 mavsdk_telemetry_check.py"""
import asyncio, sys
from mavsdk import System

async def main():
    drone = System()
    await drone.connect(system_address="udp://:14540")
    print("[tc] laczenie…")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("[tc] POLACZONO z autopilotem")
            break

    # zdrowie
    async for h in drone.telemetry.health():
        print(f"[tc] health: gpos_ok={h.is_global_position_ok} home_ok={h.is_home_position_ok} "
              f"gyro_ok={h.is_gyrometer_calibration_ok} armable={h.is_armable}")
        if h.is_global_position_ok and h.is_home_position_ok:
            break

    # 5 probek pozycji
    n = 0
    async for p in drone.telemetry.position():
        print(f"[tc] pos: lat={p.latitude_deg:.6f} lon={p.longitude_deg:.6f} "
              f"rel_alt={p.relative_altitude_m:.2f}m abs_alt={p.absolute_altitude_m:.1f}m")
        n += 1
        if n >= 5:
            break
    print("[tc] OK — telemetria dociera")

if __name__ == "__main__":
    try:
        asyncio.run(asyncio.wait_for(main(), timeout=90))
    except asyncio.TimeoutError:
        print("[tc] TIMEOUT — brak telemetrii w 90s"); sys.exit(1)
