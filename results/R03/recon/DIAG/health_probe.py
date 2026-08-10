#!/usr/bin/env python3
"""DIAGNOSTYKA (NIE bieg bramkowy) — cierpliwy pomiar bring-upu health.

Odtwarza sekwencję egzekutora gate_run_r03.py DOKŁADNIE, ale bez limitu 45 s:
  connect udpin:14540 -> czekaj connection -> get GPS_CTRL/HGT_REF -> set HGT_REF=0 (Baro)
  -> pętla health() z monotonic; loguj każdy flip is_global_position_ok / is_home_position_ok
  -> t_health = moment gdy OBA True (od chwili set HGT_REF=0, jak w egzekutorze).
Równolegle wypisuje, czy PX4 widzi GCS (heartbeat) — telemetry oraz raw.
Etykieta przyrządu: MONO (time.monotonic, sekundy od set_hgt).
"""
import asyncio, time
from mavsdk import System


async def watch_health(d, t0, done):
    g_prev = h_prev = None
    async for hh in d.telemetry.health():
        el = time.monotonic() - t0
        if hh.is_global_position_ok != g_prev:
            print(f"[MONO {el:6.1f}s] is_global_position_ok -> {hh.is_global_position_ok}", flush=True)
            g_prev = hh.is_global_position_ok
        if hh.is_home_position_ok != h_prev:
            print(f"[MONO {el:6.1f}s] is_home_position_ok   -> {hh.is_home_position_ok}", flush=True)
            h_prev = hh.is_home_position_ok
        if hh.is_global_position_ok and hh.is_home_position_ok and not done.done():
            print(f"[MONO {el:6.1f}s] *** HEALTH OK (oba True) — t_health={el:.1f}s ***", flush=True)
            done.set_result(el)


async def main():
    d = System()
    await d.connect(system_address="udpin://0.0.0.0:14540")
    print("[probe] czekam connection_state…", flush=True)
    async for s in d.core.connection_state():
        if s.is_connected:
            print("[probe] MAVSDK connected", flush=True)
            break
    gps_old = await d.param.get_param_int("EKF2_GPS_CTRL")
    hgt_old = await d.param.get_param_int("EKF2_HGT_REF")
    print(f"[probe] przed: EKF2_GPS_CTRL={gps_old} EKF2_HGT_REF={hgt_old}", flush=True)
    t0 = time.monotonic()
    await d.param.set_param_int("EKF2_HGT_REF", 0)   # Baro — jak egzekutor (§3quater)
    print(f"[MONO   0.0s] set EKF2_HGT_REF=0 (Baro) — start pomiaru", flush=True)
    done = asyncio.get_event_loop().create_future()
    hw = asyncio.ensure_future(watch_health(d, t0, done))
    try:
        t_health = await asyncio.wait_for(done, timeout=180)
    except asyncio.TimeoutError:
        print(f"[MONO 180.0s] *** health NIE OK po 180 s — realny bloker ***", flush=True)
        t_health = None
    hw.cancel()
    # przywróć param (higiena; to nie zmienia kryteriów)
    try:
        await d.param.set_param_int("EKF2_HGT_REF", int(hgt_old))
    except Exception:
        pass
    print(f"[probe] KONIEC t_health={t_health}", flush=True)


asyncio.run(main())
