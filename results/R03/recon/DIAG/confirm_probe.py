#!/usr/bin/env python3
"""DIAGNOSTYKA — potwierdzenie przyczyny: ustaw EKF2_GPS_CTRL=7 (zdrowy default) na żywej instancji
i zmierz t_health. Jeśli health staje się OK → przyczyną było persisted GPS_CTRL=0 (nie timeout/MAVSDK).
Daje też realny czas bring-upu (dla doboru nowego limitu health-wait)."""
import asyncio, time
from mavsdk import System

HEALTHY_GPS_CTRL = 7   # PX4 default (GPS+baro+...); r01 nominal


async def main():
    d = System()
    await d.connect(system_address="udpin://0.0.0.0:14540")
    async for s in d.core.connection_state():
        if s.is_connected:
            break
    g = await d.param.get_param_int("EKF2_GPS_CTRL")
    h = await d.param.get_param_int("EKF2_HGT_REF")
    print(f"[confirm] przed: EKF2_GPS_CTRL={g} EKF2_HGT_REF={h}", flush=True)
    t0 = time.monotonic()
    await d.param.set_param_int("EKF2_GPS_CTRL", HEALTHY_GPS_CTRL)
    print(f"[MONO 0.0s] set EKF2_GPS_CTRL={HEALTHY_GPS_CTRL} — start pomiaru", flush=True)
    gp = hp = None
    t_health = None
    async for hh in d.telemetry.health():
        el = time.monotonic() - t0
        if hh.is_global_position_ok != gp:
            print(f"[MONO {el:6.1f}s] is_global_position_ok -> {hh.is_global_position_ok}", flush=True); gp = hh.is_global_position_ok
        if hh.is_home_position_ok != hp:
            print(f"[MONO {el:6.1f}s] is_home_position_ok   -> {hh.is_home_position_ok}", flush=True); hp = hh.is_home_position_ok
        if hh.is_global_position_ok and hh.is_home_position_ok:
            print(f"[MONO {el:6.1f}s] *** HEALTH OK — t_health={el:.1f}s ***", flush=True); t_health = el; break
        if el > 150:
            print(f"[MONO {el:6.1f}s] nadal nie OK — inny bloker", flush=True); break
    print(f"[confirm] t_health={t_health}", flush=True)


asyncio.run(main())
