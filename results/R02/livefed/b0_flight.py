#!/usr/bin/env python3
"""b0_flight.py — B0 SONDA live-fed: dron w zawisie (headless), intruz dead-ahead ~7 m, detektor w pętli.
Mierzy: czy detektor WIDZI cel w locie i z jakim conf (+ nbox), klatka z NANIESIONĄ projekcją celu
(rider C-A1: rozdziela „poza FOV" od „w FOV nierozpoznany"). Habitat H.1: RTF, time-jump, HEADLESS, EKF-health.

Reużywa centrowania z e1_flight (poza gz drona → intruz dead-ahead). Detektor: r02.detector_node (osobny
proces, ROS). Tu subskrybuję /liquidpatrol/detector_boxes (conf) + Image (klatka+overlay).
Env: OUTDIR, INTR_RANGE (m, domyślnie 7), HOVER_ALT (9), IMG_TOPIC (ROS).
"""
import os, sys, time, json, math, asyncio, subprocess, threading
import numpy as np
from mavsdk import System
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from std_msgs.msg import Float32MultiArray
from sensor_msgs.msg import Image

OUTDIR = os.environ.get("OUTDIR", "results/R02/livefed/B0/run")
INTR_RANGE = float(os.environ.get("INTR_RANGE", "7"))
HOVER_ALT = float(os.environ.get("HOVER_ALT", "9.0"))
WORLD = os.environ.get("PX4_GZ_WORLD", "default")
IMG_TOPIC = os.environ.get("IMG_TOPIC", "")
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


def gz_rtf_timejump():
    rtf = subprocess.run("gz topic -et /world/%s/stats -n 1 2>/dev/null | grep -m1 real_time_factor" % WORLD,
                         shell=True, capture_output=True, text=True, timeout=8).stdout.strip()
    return rtf


class DetSub(Node):
    """Subskrybent detektora: /detector_boxes [cx,cy,w,h,conf]*n + Image (klatka)."""
    def __init__(self):
        super().__init__("b0_detsub")
        self.samples = []      # per klatka: {t, nbox, boxes:[(cx,cy,w,h,conf)]}
        self.frame = None; self.enc = None
        self.create_subscription(Float32MultiArray, "/liquidpatrol/detector_boxes", self._boxes, qos_be())
        if IMG_TOPIC:
            self.create_subscription(Image, IMG_TOPIC, self._img, qos_be())

    def _boxes(self, msg):
        d = list(msg.data)
        if not d:
            self.samples.append({"t": time.monotonic(), "nbox": 0, "boxes": []}); return
        sim_t = d[-1]; flat = d[:-1]
        boxes = [tuple(round(float(x), 5) for x in flat[i:i+5]) for i in range(0, len(flat) - 4, 5)]
        self.samples.append({"t": time.monotonic(), "sim_t": sim_t, "nbox": len(boxes), "boxes": boxes})

    def _img(self, msg):
        h, w = msg.height, msg.width
        buf = np.frombuffer(bytes(msg.data), dtype=np.uint8)
        ch = len(buf) // (h * w) if h * w else 1
        self.frame = buf.reshape(h, w, ch) if ch > 1 else buf.reshape(h, w)
        self.enc = msg.encoding


async def _health(d):
    async for h in d.telemetry.health():
        if h.is_global_position_ok and h.is_home_position_ok:
            return True
    return False


async def main():
    rclpy.init()
    det = DetSub()
    spin = threading.Thread(target=lambda: rclpy.spin(det), daemon=True); spin.start()

    d = System(); await d.connect(system_address="udpin://0.0.0.0:14540")
    async for s in d.core.connection_state():
        if s.is_connected:
            break
    print("[b0] MAVSDK connected", flush=True)
    try:
        healthy = await asyncio.wait_for(_health(d), timeout=60)
    except asyncio.TimeoutError:
        healthy = False
    if not healthy:
        print("[b0] HEALTH TIMEOUT", flush=True); os._exit(3)
    for i in range(20):
        try:
            await d.action.arm(); break
        except Exception as e:
            if i % 4 == 0: print(f"[b0] arm retry #{i} ({e})", flush=True)
            await asyncio.sleep(3)
    else:
        print("[b0] ARM FAILED", flush=True); os._exit(2)
    await d.action.set_takeoff_altitude(HOVER_ALT); await d.action.takeoff()
    for _ in range(40):
        async for pv in d.telemetry.position_velocity_ned():
            alt = -pv.position.down_m; break
        if alt >= HOVER_ALT - 1.5: break
        await asyncio.sleep(0.5)
    await asyncio.sleep(4)
    async for att in d.telemetry.attitude_euler():
        yaw_deg, pitch_deg, roll_deg = att.yaw_deg, att.pitch_deg, att.roll_deg; break
    async for pv in d.telemetry.position_velocity_ned():
        ned = (pv.position.north_m, pv.position.east_m, -pv.position.down_m); break
    print(f"[b0] hover ned={[round(v,2) for v in ned]} yaw={yaw_deg:.1f} pitch={pitch_deg:.1f} roll={roll_deg:.1f}", flush=True)
    # intruz dead-ahead z pozy gz drona → projekcja ~ centrum
    dxyz, dyaw = gz_drone_pose()
    if dxyz is not None and dyaw is not None:
        ix = dxyz[0] + INTR_RANGE * math.cos(dyaw); iy = dxyz[1] + INTR_RANGE * math.sin(dyaw); iz = dxyz[2]
    else:
        ix, iy, iz = INTR_RANGE, 0.0, HOVER_ALT
    gz_set_intruder(ix, iy, iz); await asyncio.sleep(1.5); gz_set_intruder(ix, iy, iz)
    print(f"[b0] intruz dead-ahead gz=({ix:.2f},{iy:.2f},{iz:.2f}) range={INTR_RANGE}", flush=True)
    rtf0 = gz_rtf_timejump()
    # zbieraj detekcje ~15 s stabilnego zawisu
    det.samples.clear()
    await asyncio.sleep(15)
    rtf1 = gz_rtf_timejump()
    # analiza conf: cel dead-ahead → projekcja ~ (0.5, 0.5). box „prawdziwy" = center w promieniu 0.15 od (0.5,0.5)
    TGT = (0.5, 0.5); RAD = 0.18
    frames = list(det.samples)
    n_frames = len(frames)
    true_confs = []; any_confs = []; nbox_list = []; n_frame_with_true = 0
    for s in frames:
        nbox_list.append(s["nbox"])
        best_true = None
        for (cx, cy, w, h, conf) in s["boxes"]:
            any_confs.append(conf)
            if math.hypot(cx - TGT[0], cy - TGT[1]) <= RAD:
                if best_true is None or conf > best_true: best_true = conf
        if best_true is not None:
            true_confs.append(best_true); n_frame_with_true += 1

    def stats(a):
        if not a: return None
        a = sorted(a)
        return {"n": len(a), "max": round(max(a), 4), "p50": round(a[len(a)//2], 4), "min": round(min(a), 4)}
    res = {
        "HEADLESS": os.environ.get("HEADLESS"), "RENDER_BACKEND": os.environ.get("RENDER_BACKEND"),
        "GZ_VER": subprocess.run(["gz", "sim", "--version"], capture_output=True, text=True).stdout.strip()[:40],
        "hover_ned": [round(v, 3) for v in ned], "att_deg": {"yaw": round(yaw_deg, 2), "pitch": round(pitch_deg, 2), "roll": round(roll_deg, 2)},
        "intruder_gz": [round(ix, 3), round(iy, 3), round(iz, 3)], "intr_range": INTR_RANGE,
        "rtf_start": rtf0, "rtf_end": rtf1,
        "n_det_frames": n_frames, "nbox_mean": round(float(np.mean(nbox_list)), 2) if nbox_list else None,
        "true_target_conf": stats(true_confs), "any_box_conf": stats(any_confs),
        "frames_with_true_target": n_frame_with_true, "coverage_true": round(n_frame_with_true / n_frames, 3) if n_frames else None,
        "theta_conf": 0.1635, "note": "cel dead-ahead ~centrum; true=box w R0.18 od (0.5,0.5); conf-floor detektora 0.001",
    }
    # klatka + overlay projekcji
    if det.frame is not None:
        frame = det.frame
        np.save(os.path.join(OUTDIR, "frame.npy"), frame)
        try:
            from PIL import Image as PImage, ImageDraw
            arr = frame if frame.ndim == 3 else np.stack([frame] * 3, -1)
            im = PImage.fromarray(arr[..., :3].astype(np.uint8)).convert("RGB")
            dr = ImageDraw.Draw(im); W, H = im.size
            tx, ty = int(TGT[0] * W), int(TGT[1] * H)
            dr.ellipse([tx - int(RAD * W), ty - int(RAD * H), tx + int(RAD * W), ty + int(RAD * H)], outline=(255, 0, 0), width=2)
            dr.line([tx - 10, ty, tx + 10, ty], fill=(255, 0, 0), width=2); dr.line([tx, ty - 10, tx, ty + 10], fill=(255, 0, 0), width=2)
            # narysuj boxy detektora z ostatniej próbki
            if frames and frames[-1]["boxes"]:
                for (cx, cy, w, h, conf) in frames[-1]["boxes"]:
                    bx, by = int(cx * W), int(cy * H); bw, bh = int(w * W / 2), int(h * H / 2)
                    dr.rectangle([bx - bw, by - bh, bx + bw, by + bh], outline=(0, 200, 0), width=1)
            im.save(os.path.join(OUTDIR, "frame_overlay.png"))
            res["overlay"] = "frame_overlay.png"
            g = (frame[..., 0] if frame.ndim == 3 else frame).astype(int)
            res["frame_min"] = int(g.min()); res["frame_mean"] = round(float(g.mean()), 1)
        except Exception as e:
            res["overlay_err"] = str(e)
    else:
        res["frame"] = "NO_FRAME"
    json.dump(res, open(os.path.join(OUTDIR, "result.json"), "w"), indent=2, ensure_ascii=False)
    print(f"[b0] n_frames={n_frames} true_conf={res['true_target_conf']} any_conf={res['any_box_conf']} "
          f"coverage_true={res['coverage_true']} nbox_mean={res['nbox_mean']} rtf_end={rtf1}", flush=True)
    try:
        await d.action.land(); await asyncio.sleep(3)
    except Exception:
        pass
    os._exit(0)


asyncio.run(main())
