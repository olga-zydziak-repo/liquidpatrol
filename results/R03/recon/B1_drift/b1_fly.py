#!/usr/bin/env python3
"""B1 lot: arm+takeoff+offboard VELOCITY patrol (back-forth) POD RUCHEM; inject EKF2_GPS_CTRL=0 mid-lot;
denial ≥ DENIAL_S pod ruchem; restore 0→7; land. Zdarzenia: monotonic_local. Params przywrócone (SR-B5)."""
import asyncio, time, os
from mavsdk import System
from mavsdk.offboard import VelocityNedYaw, OffboardError
DENIAL_S=float(os.environ.get("DENIAL_S","65")); VP=float(os.environ.get("VP","1.5"))
def ev(s): print(f"[b1] EVENT {s} mono={time.monotonic():.4f}",flush=True)
async def patrol(d,stop_t):
    # back-forth N/S przy stałej prędkości — ruch bez zależności od pozycji absolutnej
    leg=4.0  # s na nogę
    while time.monotonic()<stop_t:
        for vn in (VP,-VP):
            t=time.monotonic()
            while time.monotonic()-t<leg and time.monotonic()<stop_t:
                await d.offboard.set_velocity_ned(VelocityNedYaw(vn,0.0,0.0,0.0)); await asyncio.sleep(0.1)
async def main():
    d=System(); await d.connect(system_address="udpin://0.0.0.0:14540")
    async for s in d.core.connection_state():
        if s.is_connected: break
    old=await d.param.get_param_int("EKF2_GPS_CTRL"); print(f"[b1] EKF2_GPS_CTRL old={old}",flush=True)
    async for h in d.telemetry.health():
        if h.is_global_position_ok and h.is_home_position_ok: break
    await d.action.set_takeoff_altitude(8.0); await d.action.arm(); ev("armed")
    await d.action.takeoff(); ev("takeoff"); await asyncio.sleep(10)
    await d.offboard.set_velocity_ned(VelocityNedYaw(0,0,0,0))
    try: await d.offboard.start(); ev("offboard")
    except OffboardError as e: print("[b1] offboard err",e)
    # ruch 8 s przed denialem (rozpędź EKF), potem denial, potem ruch pod denialem
    pre=asyncio.create_task(patrol(d, time.monotonic()+8)); await pre
    ev("denial_on"); await d.param.set_param_int("EKF2_GPS_CTRL",0)
    await patrol(d, time.monotonic()+DENIAL_S)   # ruch pod dead-reckoningiem
    ev("denial_off"); await d.param.set_param_int("EKF2_GPS_CTRL",int(old)); print(f"[b1] restored EKF2_GPS_CTRL={old}",flush=True)
    await asyncio.sleep(3)
    try: await d.offboard.stop()
    except Exception: pass
    ev("land")
    try: await d.action.land()
    except Exception as e: print("[b1] land err",e)
    await asyncio.sleep(10)
    try: await d.action.disarm()
    except Exception: pass
    ev("done")
asyncio.run(main())
