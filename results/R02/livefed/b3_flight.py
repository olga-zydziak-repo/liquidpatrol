#!/usr/bin/env python3
"""b3_flight.py — B3 re-derywacja N dead-mana POD RUCHEM OBSERVE. Mierzy rozkład stalli pętli DECYZYJNEJ
(20 Hz: shield.step + odczyt telemetrii) pod ruchem — inter-tick dt (etykieta: monotonic_local). Detektor =
osobny proces (R3: pętla nie stalluje na inferencji), tu opcjonalny. Reguła PRE_R02C: N·tick > max stalla,
margines ≥3×. NIE zmieniam DEADMAN_TICKS — wynik = REKOMENDACJA.
Env: OUTDIR, HOVER_ALT (9).
"""
import os, time, json, math, asyncio, subprocess
from mavsdk import System
from mavsdk.offboard import VelocityNedYaw, OffboardError
from r01.shield import PatrolShield, M_PATROL

OUTDIR = os.environ.get("OUTDIR", "results/R02/livefed/B3/run")
HOVER_ALT = float(os.environ.get("HOVER_ALT", "9.0"))
TICK = 1.0 / 20.0
os.makedirs(OUTDIR, exist_ok=True)


async def _health(d):
    async for h in d.telemetry.health():
        if h.is_global_position_ok and h.is_home_position_ok:
            return True
    return False


async def main():
    d = System(); await d.connect(system_address="udpin://0.0.0.0:14540")
    async for s in d.core.connection_state():
        if s.is_connected: break
    try:
        healthy = await asyncio.wait_for(_health(d), timeout=60)
    except asyncio.TimeoutError:
        healthy = False
    if not healthy: print("[b3] HEALTH TIMEOUT", flush=True); os._exit(3)
    for i in range(20):
        try: await d.action.arm(); break
        except Exception:
            if i % 4 == 0: print(f"[b3] arm retry #{i}", flush=True)
            await asyncio.sleep(3)
    else: print("[b3] ARM FAILED", flush=True); os._exit(2)
    await d.action.set_takeoff_altitude(HOVER_ALT); await d.action.takeoff()
    for _ in range(40):
        async for pv in d.telemetry.position_velocity_ned():
            alt = -pv.position.down_m; break
        if alt >= HOVER_ALT - 1.5: break
        await asyncio.sleep(0.5)
    await asyncio.sleep(4)
    await d.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
    try:
        await d.offboard.start()
    except OffboardError as e:
        print("[b3] offboard err", e, flush=True); os._exit(4)

    # najświeższa telemetria w tle (żeby odczyt w pętli nie blokował)
    state = {"pos": (0, 0, -HOVER_ALT), "vel": (0, 0, 0)}
    async def tel():
        async for pv in d.telemetry.position_velocity_ned():
            state["pos"] = (pv.position.north_m, pv.position.east_m, pv.position.down_m)
            state["vel"] = (pv.velocity.north_m_s, pv.velocity.east_m_s, pv.velocity.down_m_s)
    tel_task = asyncio.ensure_future(tel())

    shield = PatrolShield(); shield.reset()
    dts = []; V = 2.5
    legs = [(V, 0), (0, V), (-V, 0), (0, -V), (V, 0), (0, -V)]   # OBSERVE-motion
    k = 0; last = time.monotonic()
    for (vn, ve) in legs:
        await d.offboard.set_velocity_ned(VelocityNedYaw(vn, ve, 0, 0))
        t_leg = time.monotonic()
        while time.monotonic() - t_leg < 3.0:
            pos = list(state["pos"]); vel = list(state["vel"])
            tgt = (pos[0] + vn, pos[1] + ve, -HOVER_ALT)
            _ = shield.step(k, pos, vel, tgt, mode=M_PATROL)   # praca pętli decyzyjnej
            now = time.monotonic(); dts.append(now - last); last = now
            k += 1
            await asyncio.sleep(TICK)
    dts = dts[2:]   # odrzuć rozruch
    ds = sorted(dts)
    def pct(p): return round(ds[min(len(ds)-1, int(p*len(ds)))], 4)
    mx = round(ds[-1], 4)
    res = {
        "HEADLESS": os.environ.get("HEADLESS"), "instrument": "monotonic_local (pętla decyzyjna 20Hz, ruch OBSERVE)",
        "n": len(ds), "tick_s": TICK, "p50": pct(0.50), "p95": pct(0.95), "p99": pct(0.99), "max_s": mx,
        "max_ticks": round(mx / TICK, 2), "p99_ticks": round(pct(0.99) / TICK, 2),
        "over_4ticks": sum(1 for x in ds if x > 4 * TICK), "over_6ticks": sum(1 for x in ds if x > 6 * TICK),
        "baseline_R3_static": {"max_ticks": 1.06, "n": 3088, "note": "R0.2 R3, inny reżim/habitat"},
        "DEADMAN_TICKS_current": 6,
    }
    # rekomendacja N: N·tick > max stalla, margines ≥3× nad zmierzonym max
    need_ticks = res["max_ticks"] * 3.0
    res["N_min_3x_margin_ticks"] = round(need_ticks, 2)
    res["N_recommendation"] = (f"N=6 (0.30s) WYSTARCZA: max {res['max_ticks']}t, 3× margines = {need_ticks:.1f}t < 6"
                               if need_ticks <= 6 else
                               f"N=6 ZA MAŁE: 3× margines = {need_ticks:.1f}t > 6 → rekomenduj N≥{math.ceil(need_ticks)}")
    json.dump(res, open(os.path.join(OUTDIR, "result.json"), "w"), indent=2, ensure_ascii=False)
    print(f"[b3] stall: n={res['n']} max={mx}s ={res['max_ticks']}t p99={res['p99_ticks']}t over4t={res['over_4ticks']} "
          f"→ {res['N_recommendation']}", flush=True)
    tel_task.cancel()
    try:
        await d.offboard.stop(); await d.action.land(); await asyncio.sleep(3)
    except Exception: pass
    os._exit(0)


asyncio.run(main())
