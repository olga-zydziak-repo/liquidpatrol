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
MODE     = os.environ.get("MODE", "straight")   # hover|straight|corner|episode
ESTATE   = os.environ.get("EPISODE_STATE", "straight")  # dla MODE=episode: straight|corner
T_PRE    = float(os.environ.get("T_PRE", "1.0"))        # segment pre-REFUSE @v_max (§3ter, zamrozony)
LEG      = float(os.environ.get("LEG", "4.0"))
ALT      = float(os.environ.get("ALT", "8.0"))


def ev(s):
    print(f"[b1bis] EVENT {s} mono={time.monotonic():.4f} mode={MODE}", flush=True)


async def set_v(d, vn, ve):
    await d.offboard.set_velocity_ned(VelocityNedYaw(vn, ve, 0.0, 0.0))


async def pattern(d, stop_t, pmode=None):
    """Wzorzec prędkości do stop_t (mono). pmode nadpisuje MODE (dla episode: straight|corner)."""
    m = pmode or MODE
    if m == "hover":
        while time.monotonic() < stop_t:
            await set_v(d, 0.0, 0.0)
            await asyncio.sleep(0.1)
        return
    if m == "straight":
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
    # Warunek habitatu (§3quater): height ref = Baro (default GPS degraduje pod denialiem).
    hgt_old = None
    if MODE == "episode":
        try:
            hgt_old = await d.param.get_param_int("EKF2_HGT_REF")
            await d.param.set_param_int("EKF2_HGT_REF", 0)  # 0=Baro
            print(f"[b1bis] EKF2_HGT_REF {hgt_old}->0 (Baro, habitat GPS-denied)", flush=True)
        except Exception as e:
            print("[b1bis] EKF2_HGT_REF set err", e, flush=True)
    async for h in d.telemetry.health():
        if h.is_global_position_ok and h.is_home_position_ok:
            break
    await d.action.set_takeoff_altitude(ALT)
    # arm adaptacyjnie: EKF preflight (gyro bias/heading) potrzebuje czasu na konwergencję;
    # retry aż preflight przejdzie (do ~120 s) zamiast sztywnego settle (arm COMMAND_DENIED = niegotowe)
    armed = False
    from mavsdk.action import ActionError as _AE
    for i in range(40):
        try:
            await d.action.arm(); armed = True; break
        except _AE:
            if i % 5 == 0:
                print(f"[b1bis] arm niegotowe (preflight), retry #{i}", flush=True)
            await asyncio.sleep(3)
    if not armed:
        print("[b1bis] ARM FAILED po retry — abort", flush=True)
        return
    ev("armed")
    await d.action.takeoff(); ev("takeoff")
    await asyncio.sleep(10)
    await set_v(d, 0.0, 0.0)
    try:
        await d.offboard.start(); ev("offboard")
    except OffboardError as e:
        print("[b1bis] offboard err", e, flush=True)
        return
    if MODE == "episode":
        # T_home baseline: HOVER ≥ 22 s (czysty offset ramki, bramka W5 na zawisie ~cm; T_home to
        # offset geometryczny home↔world — mierzony w zawisie, niezależny od dynamiki cięcia).
        await pattern(d, time.monotonic() + 22, pmode="hover")
        # run-up do v_max w kierunku cięcia (~3 s; próbki |v|>1 poza bramką W5 zawisu)
        ru = time.monotonic() + 3.0
        while time.monotonic() < ru:
            await set_v(d, VMAX, 0.0)
            await asyncio.sleep(0.05)
        ev("denial_on")                      # cięcie w stanie v_max (worst-case)
        await d.param.set_param_int("EKF2_GPS_CTRL", 0)
        # segment pre-REFUSE @ v_max w NAJGORSZYM stanie (§3ter, t_pre zamrożone)
        tp = time.monotonic() + T_PRE
        while time.monotonic() < tp:
            if ESTATE == "corner":
                await set_v(d, 0.0, VMAX)    # ostry zwrot 90° (+N→+E) — worst-case narożnika
            else:
                await set_v(d, VMAX, 0.0)    # prosta — pełne v_max jednokierunkowo
            await asyncio.sleep(0.05)
        # AKCJA BEZPIECZNA = ZEJŚCIE STEROWANE PRĘDKOŚCIĄ, v_xy=0 RÓWNOCZEŚNIE (D5 zrew. §3quater).
        # NIE d.action.land() (AUTO.LAND = position-hold → flyaway 42 m pod DR). Profil DWUFAZOWY:
        # ERRATUM_42M (PRE_K1 §0): "42 m" asserted 09.08, run not preserved — superseded by K1 measurement (PRE_K1); see results/K1/ERRATUM_42M.md
        # faza1 v_desc_fast=MPC_Z_VEL_MAX_DN=1.5 m/s do ~2 m AGL; faza2 MPC_LAND_SPEED=0.7 do touchdown.
        # Czas zejścia = DŹWIGNIA dryfu (krótszy epizod DR = mniejszy ε_pos).
        ev("refuse_land")
        V_FAST = float(os.environ.get("V_DESC_FAST", "1.5"))   # MPC_Z_VEL_MAX_DN (limit VRS PX4)
        V_LAND = float(os.environ.get("V_DESC_LAND", "0.7"))   # MPC_LAND_SPEED
        t1 = time.monotonic() + max(0.0, (ALT - 2.0) / V_FAST)  # faza1 do ~2 m AGL
        while time.monotonic() < t1:
            await d.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, V_FAST, 0.0))
            await asyncio.sleep(0.05)
        ev("h_switch")
        t2 = time.monotonic() + (2.0 / V_LAND + 2.0)            # faza2 do touchdown (2 m + zapas)
        while time.monotonic() < t2:
            await d.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, V_LAND, 0.0))
            await asyncio.sleep(0.05)
        ev("touchdown")
        try:
            await d.offboard.stop()
        except Exception:
            pass
        await d.param.set_param_int("EKF2_GPS_CTRL", int(old))  # restore PO touchdown (SR-B5)
        if hgt_old is not None:
            await d.param.set_param_int("EKF2_HGT_REF", int(hgt_old))  # restore (SR-B5)
        print(f"[b1bis] restored EKF2_GPS_CTRL={old} EKF2_HGT_REF={hgt_old}", flush=True)
    else:
        # profil długiego okna (sonda falsyfikująca A-plateau)
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
