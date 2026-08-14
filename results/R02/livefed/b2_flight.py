#!/usr/bin/env python3
"""b2_flight.py — B2 re-charakteryzacja θ_conf w LOCIE: sweep dystansu (5/7/9/11 m) + faza SZUMU, jeden zawis.
θ_conf NIETYKALNY — mierzę gdzie leżą chmury sygnału i szumu względem istniejącego progu 0.1635.
Sygnał: intruz dead-ahead na danym range; szum: intruz odsunięty (-60 m) → pusta scena → ε_FP.
Coverage = frakcja klatek detektora z boxem-celem (center w R od projekcji) i conf≥θ_conf (kryterium +).
Env: OUTDIR, IMG_TOPIC, HOVER_ALT (9), RANGES ("5,7,9,11"), DWELL_S (8), NOISE_S (12).
"""
import os, sys, time, json, math, asyncio, subprocess, threading
import numpy as np
from mavsdk import System
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from std_msgs.msg import Float32MultiArray

OUTDIR = os.environ.get("OUTDIR", "results/R02/livefed/B2/run")
HOVER_ALT = float(os.environ.get("HOVER_ALT", "9.0"))
WORLD = os.environ.get("PX4_GZ_WORLD", "default")
RANGES = [float(x) for x in os.environ.get("RANGES", "5,7,9,11").split(",")]
DWELL_S = float(os.environ.get("DWELL_S", "8"))
NOISE_S = float(os.environ.get("NOISE_S", "12"))
THETA = 0.1635
TGT = (0.5, 0.5); RAD = 0.18
os.makedirs(OUTDIR, exist_ok=True)


def qos_be():
    return QoSProfile(depth=5, history=HistoryPolicy.KEEP_LAST, reliability=ReliabilityPolicy.BEST_EFFORT)


def gz_set_intruder(x, y, z):
    subprocess.run(["gz", "service", "-s", f"/world/{WORLD}/set_pose", "--reqtype", "gz.msgs.Pose",
                    "--reptype", "gz.msgs.Boolean", "--timeout", "3000",
                    "--req", f'name: "intruder", position: {{x: {x:.3f}, y: {y:.3f}, z: {z:.3f}}}, orientation: {{w: 1.0}}'],
                   capture_output=True, text=True, timeout=8)


def gz_drone_pose():
    import re
    out = subprocess.run(["gz", "model", "-m", "x500_mono_cam_0", "-p"], capture_output=True, text=True, timeout=8).stdout
    nums = re.findall(r"\[\s*(-?[0-9.eE+-]+\s+-?[0-9.eE+-]+\s+-?[0-9.eE+-]+)\s*\]", out)
    xyz = [float(v) for v in nums[0].split()] if nums else None
    rpy = [float(v) for v in nums[1].split()] if len(nums) > 1 else None
    return xyz, (rpy[2] if rpy else None)


def rtf():
    return subprocess.run("gz topic -et /world/%s/stats -n 1 2>/dev/null | grep -m1 real_time_factor" % WORLD,
                          shell=True, capture_output=True, text=True, timeout=8).stdout.strip()


class DetSub(Node):
    def __init__(self):
        super().__init__("b2_detsub")
        self.samples = []
        self.create_subscription(Float32MultiArray, "/liquidpatrol/detector_boxes", self._boxes, qos_be())

    def _boxes(self, msg):
        d = list(msg.data)
        if not d:
            self.samples.append({"t": time.monotonic(), "nbox": 0, "boxes": []}); return
        flat = d[:-1]
        boxes = [tuple(round(float(x), 5) for x in flat[i:i+5]) for i in range(0, len(flat) - 4, 5)]
        self.samples.append({"t": time.monotonic(), "nbox": len(boxes), "boxes": boxes})


def analyze(samples, t0, t1):
    """W oknie [t0,t1]: chmura conf celu (box near center) i szumu (box far), coverage@θ, ε_FP@θ."""
    seg = [s for s in samples if t0 <= s["t"] <= t1]
    tgt_conf = []; noise_conf = []; frames_admit = 0; n = len(seg); frames_fp = 0
    for s in seg:
        best_t = None; any_admit_far = False
        for (cx, cy, w, h, conf) in s["boxes"]:
            if math.hypot(cx - TGT[0], cy - TGT[1]) <= RAD:
                best_t = conf if best_t is None else max(best_t, conf)
            else:
                noise_conf.append(conf)
                if conf >= THETA: any_admit_far = True
        if best_t is not None:
            tgt_conf.append(best_t)
            if best_t >= THETA: frames_admit += 1
        if any_admit_far: frames_fp += 1

    def st(a):
        if not a: return None
        a = sorted(a)
        return {"n": len(a), "max": round(a[-1], 4), "p95": round(a[min(len(a)-1, int(0.95*len(a)))], 4),
                "p50": round(a[len(a)//2], 4), "min": round(a[0], 4)}
    return {"n_frames": n, "target_conf": st(tgt_conf), "noise_conf": st(noise_conf),
            "coverage_admit@theta": round(frames_admit / n, 3) if n else None,
            "frames_target_seen": len(tgt_conf), "coverage_seen": round(len(tgt_conf)/n, 3) if n else None,
            "eps_fp_frames@theta": frames_fp}


async def _health(d):
    async for h in d.telemetry.health():
        if h.is_global_position_ok and h.is_home_position_ok:
            return True
    return False


async def main():
    rclpy.init(); det = DetSub()
    threading.Thread(target=lambda: rclpy.spin(det), daemon=True).start()
    d = System(); await d.connect(system_address="udpin://0.0.0.0:14540")
    async for s in d.core.connection_state():
        if s.is_connected: break
    try:
        healthy = await asyncio.wait_for(_health(d), timeout=60)
    except asyncio.TimeoutError:
        healthy = False
    if not healthy: print("[b2] HEALTH TIMEOUT", flush=True); os._exit(3)
    for i in range(20):
        try: await d.action.arm(); break
        except Exception as e:
            if i % 4 == 0: print(f"[b2] arm retry #{i}", flush=True)
            await asyncio.sleep(3)
    else: print("[b2] ARM FAILED", flush=True); os._exit(2)
    await d.action.set_takeoff_altitude(HOVER_ALT); await d.action.takeoff()
    for _ in range(40):
        async for pv in d.telemetry.position_velocity_ned():
            alt = -pv.position.down_m; break
        if alt >= HOVER_ALT - 1.5: break
        await asyncio.sleep(0.5)
    await asyncio.sleep(4)
    async for att in d.telemetry.attitude_euler():
        att0 = {"yaw": round(att.yaw_deg, 2), "pitch": round(att.pitch_deg, 2), "roll": round(att.roll_deg, 2)}; break
    dxyz, dyaw = gz_drone_pose()
    _yg = round(math.degrees(dyaw), 1) if dyaw is not None else None
    print(f"[b2] hover; drone gz={[round(v,2) for v in dxyz] if dxyz else None} yaw_gz={_yg}", flush=True)
    res = {"HEADLESS": os.environ.get("HEADLESS"), "RENDER_BACKEND": os.environ.get("RENDER_BACKEND"),
           "GZ_VER": subprocess.run(["gz","sim","--version"], capture_output=True, text=True).stdout.strip()[:40],
           "att_hover": att0, "theta_conf": THETA, "ranges": RANGES, "rtf_start": rtf(),
           "note": "sygnał=box w R0.18 od centrum (cel dead-ahead); szum=boxy poza; θ NIETYKALNY; conf-floor detektora 0.001",
           "sweep": {}}
    fwd = (math.cos(dyaw), math.sin(dyaw)) if dyaw is not None else (1.0, 0.0)
    cz = dxyz[2] if dxyz else HOVER_ALT; cxy = (dxyz[0], dxyz[1]) if dxyz else (0.0, 0.0)
    for rng in RANGES:
        ix = cxy[0] + rng * fwd[0]; iy = cxy[1] + rng * fwd[1]; iz = cz
        gz_set_intruder(ix, iy, iz); await asyncio.sleep(1.0); gz_set_intruder(ix, iy, iz)
        t0 = time.monotonic(); await asyncio.sleep(DWELL_S); t1 = time.monotonic()
        a = analyze(det.samples, t0 + 1.0, t1)   # +1s: pomiń przejście
        res["sweep"][f"{rng:g}m"] = a
        print(f"[b2] range {rng}m: target_conf={a['target_conf']} coverage_seen={a['coverage_seen']} "
              f"coverage_admit@θ={a['coverage_admit@theta']}", flush=True)
    # FAZA SZUMU: intruz odsunięty daleko (pusta scena) → ε_FP
    gz_set_intruder(cxy[0] - 60.0, cxy[1], 3.0); await asyncio.sleep(1.5)
    t0 = time.monotonic(); await asyncio.sleep(NOISE_S); t1 = time.monotonic()
    noise = analyze(det.samples, t0 + 1.0, t1)
    res["noise_phase"] = noise
    res["rtf_end"] = rtf()
    print(f"[b2] NOISE: noise_conf={noise['noise_conf']} eps_fp_frames@θ={noise['eps_fp_frames@theta']} "
          f"(any box near-center? coverage_seen={noise['coverage_seen']})", flush=True)
    json.dump(res, open(os.path.join(OUTDIR, "result.json"), "w"), indent=2, ensure_ascii=False)
    try:
        await d.action.land(); await asyncio.sleep(3)
    except Exception: pass
    os._exit(0)


asyncio.run(main())
