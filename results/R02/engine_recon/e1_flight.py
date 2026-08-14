#!/usr/bin/env python3
"""e1_flight.py — E1 KONFIRMATOR: dron W LOCIE (zawis) + HEADLESS, przechwyt renderu intruza.

Jednozmienny względem §6: lot zachowany, tylko GUI off. Intruz dead-ahead na wysokości drona (gz z=9,
poziomo centralnie — projekcja C1 potwierdziła cx~0.47) → pomiar renderu ODPORNY na drobne kołysanie
zawisu (w przeciwieństwie do (7,0,11.5) na krawędzi FOV, który klipował attitude). Reużywa grab.py
(dark_px w centrum, enumeracja sceny). MAVSDK: arm+takeoff+hover; gz transport capture; land.

Env: INTR_GZ="x,y,z" (gz world, domyślnie 7,0,9), OUTDIR, HOVER_ALT (m, domyślnie 9).
"""
import os, sys, time, json, math, asyncio, subprocess
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from mavsdk import System
from mavsdk.offboard import VelocityNedYaw, OffboardError
import grab  # capture + dark_px + enumeracja (ten sam instrument co D0.5)

INTR_GZ = tuple(float(x) for x in os.environ.get("INTR_GZ", "7,0,9").split(","))
OUTDIR = os.environ.get("OUTDIR", "results/R02/engine_recon/E1_confirm/flight_headless_clean")
HOVER_ALT = float(os.environ.get("HOVER_ALT", "9.0"))
WORLD = os.environ.get("PX4_GZ_WORLD", "default")
os.makedirs(OUTDIR, exist_ok=True)


def gz_set_intruder(x, y, z):
    subprocess.run(["gz", "service", "-s", f"/world/{WORLD}/set_pose", "--reqtype", "gz.msgs.Pose",
                    "--reptype", "gz.msgs.Boolean", "--timeout", "3000",
                    "--req", f'name: "intruder", position: {{x: {x:.3f}, y: {y:.3f}, z: {z:.3f}}}, orientation: {{w: 1.0}}'],
                   capture_output=True, text=True, timeout=8)


def gz_drone_pose():
    """Poza drona w gz world (XYZ + yaw) z `gz model -p`. Do centrowania intruza dead-ahead niezależnie
    od (niekontrolowanego) yaw zawisu — usuwa konfundację yaw z pomiaru renderu."""
    out = subprocess.run(["gz", "model", "-m", "x500_mono_cam_0", "-p"], capture_output=True, text=True, timeout=8).stdout
    import re
    # tylko nawiasy z DOKŁADNIE 3 liczbami (pomija `Model: [55]`); nums[0]=XYZ, nums[1]=RPY
    nums = re.findall(r"\[\s*(-?[0-9.eE+-]+\s+-?[0-9.eE+-]+\s+-?[0-9.eE+-]+)\s*\]", out)
    xyz = [float(v) for v in nums[0].split()] if nums else None
    rpy = [float(v) for v in nums[1].split()] if len(nums) > 1 else None
    return xyz, (rpy[2] if rpy else None)


async def main():
    d = System(); await d.connect(system_address="udpin://0.0.0.0:14540")
    async for s in d.core.connection_state():
        if s.is_connected:
            break
    print("[e1] MAVSDK connected; czekam health", flush=True)
    try:
        healthy = await asyncio.wait_for(_health(d), timeout=60)
    except asyncio.TimeoutError:
        healthy = False
    if not healthy:
        print("[e1] HEALTH TIMEOUT", flush=True); os._exit(3)
    armed = False
    for i in range(20):
        try:
            await d.action.arm(); armed = True; break
        except Exception as e:
            if i % 4 == 0:
                print(f"[e1] arm retry #{i} ({e})", flush=True)
            await asyncio.sleep(3)
    if not armed:
        print("[e1] ARM FAILED po retry", flush=True); os._exit(2)
    await d.action.set_takeoff_altitude(HOVER_ALT)
    await d.action.takeoff()
    print(f"[e1] takeoff → {HOVER_ALT} m", flush=True)
    # czekaj aż na wysokości + stabilnie
    for _ in range(40):
        async for pv in d.telemetry.position_velocity_ned():
            alt = -pv.position.down_m; break
        if alt >= HOVER_ALT - 1.0:
            break
        await asyncio.sleep(0.5)
    await asyncio.sleep(4)   # ustabilizuj zawis
    # odczyt pozy drona (gz) + yaw NED
    async for att in d.telemetry.attitude_euler():
        yaw_deg = att.yaw_deg; pitch_deg = att.pitch_deg; roll_deg = att.roll_deg; break
    async for pv in d.telemetry.position_velocity_ned():
        ned = (pv.position.north_m, pv.position.east_m, -pv.position.down_m); break
    print(f"[e1] hover ned={[round(v,2) for v in ned]} yaw={yaw_deg:.1f} pitch={pitch_deg:.1f} roll={roll_deg:.1f}", flush=True)
    # intruz DEAD-AHEAD z realnej pozy gz drona (usuwa konfundację yaw): 7 m wzdłuż forward kamery
    dxyz, dyaw = gz_drone_pose()
    if dxyz is not None and dyaw is not None:
        ix = dxyz[0] + 7.0 * math.cos(dyaw); iy = dxyz[1] + 7.0 * math.sin(dyaw); iz = dxyz[2]
        print(f"[e1] drone gz={[round(v,2) for v in dxyz]} yaw_gz={math.degrees(dyaw):.1f} → intruz dead-ahead=({ix:.2f},{iy:.2f},{iz:.2f})", flush=True)
    else:
        ix, iy, iz = INTR_GZ; print(f"[e1] gz pose parse FAIL → fallback INTR_GZ={INTR_GZ}", flush=True)
    gz_set_intruder(ix, iy, iz)   # wstępne (pre-stres); ostateczne po stresie z BIEŻĄCEJ pozy
    # E2: kontencja CPU DOPIERO w zawisie (health/arm już przeszły bez stresu) → izoluje render-pod-kontencją.
    # yes SPAWNOWANY WPROST (nie przez bash) → p.kill() ubija właściwy proces (bez sierot). Mierz RTF gz.
    stress_procs = []
    STRESS_N = int(os.environ.get("STRESS_N", "0"))
    def _rtf():
        try:
            return subprocess.run("gz topic -et /world/default/stats -n 1 2>/dev/null | grep -m1 real_time_factor",
                                  shell=True, capture_output=True, text=True, timeout=8).stdout.strip()
        except Exception as e:
            return f"err:{e}"
    meta_extra = {"rtf_baseline": _rtf()}
    if STRESS_N > 0:
        for _ in range(STRESS_N):
            stress_procs.append(subprocess.Popen(["yes"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        print(f"[e1] E2: STRESS {STRESS_N}× yes — czekam 12 s (RTF/time-jump/hover)", flush=True)
        await asyncio.sleep(12)
        meta_extra["rtf_under_stress"] = _rtf(); meta_extra["stress_n"] = STRESS_N
        print(f"[e1] RTF baseline={meta_extra['rtf_baseline']} under_stress={meta_extra['rtf_under_stress']}", flush=True)
    # OSTATECZNE centrowanie z BIEŻĄCEJ pozy — ale GUARD: jeśli dron spadł/odczyt zły (z<3 m, a leciał ~9 m)
    # NIE przerzucaj intruza pod ziemię; zostaw placement pre-stres i ODNOTUJ utratę wysokości (finding lotu).
    dxyz2, dyaw2 = gz_drone_pose()
    if dxyz2 is not None and dyaw2 is not None and dxyz2[2] >= 3.0:
        ix = dxyz2[0] + 7.0 * math.cos(dyaw2); iy = dxyz2[1] + 7.0 * math.sin(dyaw2); iz = dxyz2[2]
        meta_extra["drone_z_post_stress"] = round(dxyz2[2], 2)
    elif dxyz2 is not None:
        meta_extra["drone_z_post_stress"] = round(dxyz2[2], 2)
        meta_extra["altitude_loss_flag"] = True   # dron stracił wysokość pod kontencją (EKF głodzony) — placement pre-stres
        print(f"[e1] GUARD: dron gz z={dxyz2[2]:.2f} <3 m (utrata wysokości pod stresem?) → placement pre-stres", flush=True)
    intr_placed = (round(ix, 3), round(iy, 3), round(iz, 3))
    gz_set_intruder(ix, iy, iz); await asyncio.sleep(1.5); gz_set_intruder(ix, iy, iz); await asyncio.sleep(1.0)
    print(f"[e1] intruz dead-ahead (po stresie): {intr_placed}", flush=True)
    # capture przez gz transport (ten sam topik co bramka)
    img = subprocess.run("gz topic -l | grep -E 'imager/image$' | head -1", shell=True,
                         capture_output=True, text=True).stdout.strip()
    print(f"[e1] topik: {img}", flush=True)
    os.environ["HEADLESS"] = "1"; os.environ["RENDER_BACKEND"] = os.environ.get("RENDER_BACKEND", "mesa-d3d12")
    os.environ["GZ_VER"] = subprocess.run(["gz", "sim", "--version"], capture_output=True, text=True).stdout.strip()[:40]
    os.environ["CAM_KIND"] = "drone_FLIGHT_hover"; os.environ["CAM_Z"] = str(round(ned[2], 2))
    os.environ["INTR_KIND"] = "mesh"; os.environ["INTR_RANGE"] = "7"; os.environ["DISC"] = "E1"; os.environ["RUN"] = os.path.basename(OUTDIR)
    box, status = grab.grab_frame(img, wait_s=12)
    meta = {k: os.environ.get(k) for k in ("HEADLESS", "RENDER_BACKEND", "GZ_VER", "CAM_KIND", "CAM_Z")}
    meta["img_topic"] = img; meta["capture_status"] = status
    meta["hover_ned"] = [round(v, 3) for v in ned]; meta["att_deg"] = {"yaw": round(yaw_deg, 2), "pitch": round(pitch_deg, 2), "roll": round(roll_deg, 2)}
    meta["intruder_gz"] = list(intr_placed); meta["models"] = grab.enumerate_models()
    if box and box["frame"] is not None:
        frame = box["frame"]
        np.save(os.path.join(OUTDIR, "frame.npy"), frame)
        try:
            from PIL import Image as PImage
            arr = frame if frame.ndim == 3 else np.stack([frame] * 3, -1)
            PImage.fromarray(arr[..., :3].astype(np.uint8)).save(os.path.join(OUTDIR, "frame.png"))
        except Exception as e:
            meta["png_err"] = str(e)
        m = grab.measure_dark(frame); meta.update(m)
        meta["frame_mean"] = round(float(frame.mean()), 1); meta["frame_min"] = int(frame.min())
        present = meta["models"].get("intruder_present")
        meta["verdict"] = ("RENDER_PASS_visible" if m["visible"] else
                           ("RENDER_FAIL_in_state_not_in_image" if present else "AMBIG_not_in_state"))
    else:
        meta["verdict"] = "NO_FRAME"
    meta.update(meta_extra)
    for p in stress_procs:
        try: p.kill()
        except Exception: pass
    json.dump(meta, open(os.path.join(OUTDIR, "result.json"), "w"), indent=2, ensure_ascii=False)
    print(f"[e1] {meta['verdict']} dark_px={meta.get('dark_px')} center_min={meta.get('center_min')} "
          f"frame_mean={meta.get('frame_mean')} intruder_in_state={meta['models'].get('intruder_present')}", flush=True)
    try:
        await d.action.land(); await asyncio.sleep(3)
    except Exception:
        pass
    os._exit(0)


async def _health(d):
    async for h in d.telemetry.health():
        if h.is_global_position_ok and h.is_home_position_ok:
            return True
    return False


asyncio.run(main())
