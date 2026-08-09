#!/usr/bin/env python3
"""
B1-bis lot: arm+takeoff+offboard VELOCITY; pre-ruch (rozpędź EKF); inject EKF2_GPS_CTRL=0;
utrzymaj DR ≥ DENIAL_S; restore 0→7; land. Params przywrócone (SR-B5, weryfikacja po biegu).
MODE (regime prędkości w chwili/podczas cięcia):
  hover    — v=0 (najczystsza kotwica ε_pos)
  straight — tam-i-z-powrotem Północ na v_max (worst-case prostej)
  corner   — box N/E/S/W na v_max (zmiany kierunku = narożniki)
Etykiety zdarzeń: monotonic_local. DR-okno definiuje flaga dead_reckoning w rejestratorze.
"""
import asyncio, os, time
from mavsdk import System
from mavsdk.offboard import VelocityNedYaw, OffboardError

DENIAL_S = float(os.environ.get("DENIAL_S", "70"))
VMAX     = float(os.environ.get("VMAX", "3.0"))
MODE     = os.environ.get("MODE", "straight")
LEG      = float(os.environ.get("LEG", "4.0"))
ALT      = float(os.environ.get("ALT", "8.0"))


def ev(s):
    print(f"[b1bis] EVENT {s} mono={time.monotonic():.4f} mode={MODE}", flush=True)


async def set_v(d, vn, ve):
    await d.offboard.set_velocity_ned(VelocityNedYaw(vn, ve, 0.0, 0.0))


async def pattern(d, stop_t):
    """Wzorzec prędkości do stop_t (mono)."""
    if MODE == "hover":
        while time.monotonic() < stop_t:
            await set_v(d, 0.0, 0.0)
            await asyncio.sleep(0.1)
        return
    if MODE == "straight":
        segs = [(VMAX, 0.0), (-VMAX, 0.0)]
    else:  # corner / box
        segs = [(VMAX, 0.0), (0.0, VMAX), (-VMAX, 0.0), (0.0, -VMAX)]
    i = 0
    while time.monotonic() < stop_t:
        vn, ve = segs[i % len(segs)]
        t = time.monotonic()
        while time.monotonic() - t < LEG and time.monotonic() < stop_t:
            await set_v(d, vn, ve)
            await asyncio.sleep(0.1)
        i += 1


async def main():
    d = System()
    await d.connect(system_address="udpin://0.0.0.0:14540")
    async for s in d.core.connection_state():
        if s.is_connected:
            break
    old = await d.param.get_param_int("EKF2_GPS_CTRL")
    print(f"[b1bis] EKF2_GPS_CTRL old={old}", flush=True)
    async for h in d.telemetry.health():
        if h.is_global_position_ok and h.is_home_position_ok:
            break
    await d.action.set_takeoff_altitude(ALT)
    await d.action.arm(); ev("armed")
    await d.action.takeoff(); ev("takeoff")
    await asyncio.sleep(10)
    await set_v(d, 0.0, 0.0)
    try:
        await d.offboard.start(); ev("offboard")
    except OffboardError as e:
        print("[b1bis] offboard err", e, flush=True)
        return
    # pre-ruch 8 s (rozpędź/ustabilizuj EKF przed denialiem; T_home z ≥20 s zdrowego okna)
    await pattern(d, time.monotonic() + 8)
    ev("denial_on")
    await d.param.set_param_int("EKF2_GPS_CTRL", 0)
    await pattern(d, time.monotonic() + DENIAL_S)   # ruch pod dead-reckoningiem
    ev("denial_off")
    await d.param.set_param_int("EKF2_GPS_CTRL", int(old))
    print(f"[b1bis] restored EKF2_GPS_CTRL={old}", flush=True)
    await asyncio.sleep(3)
    try:
        await d.offboard.stop()
    except Exception:
        pass
    ev("land")
    try:
        await d.action.land()
    except Exception as e:
        print("[b1bis] land err", e, flush=True)
    await asyncio.sleep(12)
    # weryfikacja przywrócenia params (SR-B5 / W4)
    chk = await d.param.get_param_int("EKF2_GPS_CTRL")
    print(f"[b1bis] EKF2_GPS_CTRL post={chk}", flush=True)
    try:
        await d.action.disarm()
    except Exception:
        pass
    ev("done")


asyncio.run(main())
