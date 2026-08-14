#!/usr/bin/env python3
"""b1_flight.py — B1: attitude nosiciela POD RUCHEM OBSERVE (nie zawis). Multirotor przyspiesza pochylając
kadłub: a=2 m/s² → ustalony pitch ~atan(a/g)≈11.5°, rząd wielkości nad jitterem zawisu (~0.6°).
Mierzy BIAS (składowa stała pitchu w krążeniu) vs JITTER (rozrzut) → reguła (już zamrożona PRE_R02C):
bias→0a (offset montażu), jitter→0b (gimbal), ani-ani→sztywna kamera. Etykieta: mav (MAVSDK attitude 20 Hz).
Env: OUTDIR, HOVER_ALT (9).
"""
import os, time, json, math, asyncio, subprocess
from mavsdk import System
from mavsdk.offboard import VelocityNedYaw, OffboardError

OUTDIR = os.environ.get("OUTDIR", "results/R02/livefed/B1/run")
HOVER_ALT = float(os.environ.get("HOVER_ALT", "9.0"))
os.makedirs(OUTDIR, exist_ok=True)


async def _health(d):
    async for h in d.telemetry.health():
        if h.is_global_position_ok and h.is_home_position_ok:
            return True
    return False


async def sample_attitude(d, dur, tag, store):
    """Próbkuj pitch/roll (mav) przez dur s, dopisz do store z etykietą fazy."""
    t0 = time.monotonic()
    while time.monotonic() - t0 < dur:
        async for a in d.telemetry.attitude_euler():
            store.append({"t": round(time.monotonic() - t0, 3), "phase": tag,
                          "pitch": a.pitch_deg, "roll": a.roll_deg, "yaw": a.yaw_deg})
            break
        await asyncio.sleep(0.05)


async def main():
    d = System(); await d.connect(system_address="udpin://0.0.0.0:14540")
    async for s in d.core.connection_state():
        if s.is_connected: break
    try:
        healthy = await asyncio.wait_for(_health(d), timeout=60)
    except asyncio.TimeoutError:
        healthy = False
    if not healthy: print("[b1] HEALTH TIMEOUT", flush=True); os._exit(3)
    for i in range(20):
        try: await d.action.arm(); break
        except Exception:
            if i % 4 == 0: print(f"[b1] arm retry #{i}", flush=True)
            await asyncio.sleep(3)
    else: print("[b1] ARM FAILED", flush=True); os._exit(2)
    await d.action.set_takeoff_altitude(HOVER_ALT); await d.action.takeoff()
    for _ in range(40):
        async for pv in d.telemetry.position_velocity_ned():
            alt = -pv.position.down_m; break
        if alt >= HOVER_ALT - 1.5: break
        await asyncio.sleep(0.5)
    await asyncio.sleep(4)
    samples = []
    # faza 0: ZAWIS (baseline, powtórzenie R0.2 ~0.6°)
    await d.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
    try:
        await d.offboard.start()
    except OffboardError as e:
        print("[b1] offboard err", e, flush=True); os._exit(4)
    await sample_attitude(d, 5, "hover", samples)
    # OBSERVE-motion: profil krążenia/ścigania — przyspieszenia w N/E (pitch), zmiany kierunku (roll).
    V = 2.5   # m/s cel; ramp przez PX4 → pitch przejściowy + ustalony
    legs = [(V, 0), (V, 0), (0, V), (0, V), (-V, 0), (-V, 0), (0, -V), (0, -V)]  # kwadrat/ósemka ~ OBSERVE
    for (vn, ve) in legs:
        await d.offboard.set_velocity_ned(VelocityNedYaw(vn, ve, 0, 0))
        await sample_attitude(d, 2.5, "motion", samples)
    await d.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
    await sample_attitude(d, 3, "settle", samples)

    import statistics as st
    def stats(vals):
        if not vals: return None
        return {"n": len(vals), "mean": round(st.mean(vals), 2), "std": round(st.pstdev(vals), 2),
                "abs_max": round(max(abs(v) for v in vals), 2),
                "min": round(min(vals), 2), "max": round(max(vals), 2)}
    hov = [s for s in samples if s["phase"] == "hover"]
    mot = [s for s in samples if s["phase"] == "motion"]
    res = {
        "HEADLESS": os.environ.get("HEADLESS"), "instrument": "mav (MAVSDK attitude_euler ~20Hz)",
        "GZ_VER": subprocess.run(["gz","sim","--version"], capture_output=True, text=True).stdout.strip()[:40],
        "v_cmd_mps": V, "expected_steady_pitch_deg": round(math.degrees(math.atan(V*0.6/9.8)), 1),
        "hover_pitch": stats([s["pitch"] for s in hov]), "hover_roll": stats([s["roll"] for s in hov]),
        "motion_pitch": stats([s["pitch"] for s in mot]), "motion_roll": stats([s["roll"] for s in mot]),
        "note": "bias=mean(motion) skladowa stala; jitter=std(motion) rozrzut; reguła PRE_R02C: bias→0a, jitter→0b, ani-ani→sztywna",
    }
    # rekomendacja (stosuję zamrożoną regułę, NIE buduję)
    mp = res["motion_pitch"]; mr = res["motion_roll"]
    bias = max(abs(mp["mean"]), abs(mr["mean"])) if mp and mr else 0
    jit = max(mp["std"], mr["std"]) if mp and mr else 0
    if bias >= 5.0 and bias >= 2*jit:
        rec = "0a (statyczny offset montażu) — dominuje BIAS"
    elif jit >= 3.0 and jit >= bias:
        rec = "0b (gimbal) — dominuje JITTER"
    elif bias < 3.0 and jit < 3.0:
        rec = "ŻADNA (sztywna kamera zostaje) — ani bias, ani jitter istotny"
    else:
        rec = f"NIEJEDNOZNACZNE (bias={bias}° jitter={jit}°) — do ratyfikacji"
    res["bias_deg"] = round(bias, 2); res["jitter_deg"] = round(jit, 2); res["lever_recommendation"] = rec
    json.dump(res, open(os.path.join(OUTDIR, "result.json"), "w"), indent=2, ensure_ascii=False)
    json.dump(samples, open(os.path.join(OUTDIR, "attitude_samples.json"), "w"))
    print(f"[b1] hover_pitch={res['hover_pitch']} motion_pitch={res['motion_pitch']} motion_roll={res['motion_roll']}", flush=True)
    print(f"[b1] bias={bias:.2f}° jitter={jit:.2f}° → {rec}", flush=True)
    try:
        await d.offboard.stop(); await d.action.land(); await asyncio.sleep(3)
    except Exception: pass
    os._exit(0)


asyncio.run(main())
