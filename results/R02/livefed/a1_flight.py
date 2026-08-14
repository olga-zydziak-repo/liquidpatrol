#!/usr/bin/env python3
"""a1_flight.py — A1 (dyskryminator 0b): POWTÓRZENIE B0 (detektor w pętli) POD OBSERVE-motion (reżim B1).

Cel dead-ahead w geometrii OPERACYJNEJ (config_r02): R_h=6.84 m poziomo + Δalt=1.5 m nad dronem → 3D=7.0 m,
el_nom~12.4°. Cel jest CIĄGLE PRZE-STAWIANY dead-ahead z żywej pozy gz (~8 Hz), więc NOMINALNA projekcja
zostaje wyśrodkowana (az≈0) — jedyne co może wyrzucić cel z kadru to JITTER attitude (pitch/roll), czyli
dokładnie mechanizm, który 0b (gimbal) miałby naprawić. Placement-lag @2.5 m/s / 8 Hz ≈ 0.31 m → ~2.6° az,
≪ ROI. Dodatkowo w locie: MOTION-BLUR na ~30 px celu (czego tor geometryczny NIE widzi).

Pary klatka↔attitude: `monotonic` (ten sam zegar procesu dla odbioru boxów i attitude) — do ATRYBUCJI
coverage; NIE do derotacji (to osobny problem, PRE_MTI). Habitat H.1: RTF/time-jump/HEADLESS/EKF zewn.
Metryki: coverage_seen (box detektora ≤R od PRZEWIDZIANEJ projekcji), rozkład (cx,cy) i edge, frames_out_of_fov
(z pary attitude, geometrycznie), true-conf (log/telemetria, θ NIETYKALNY). Reguła A1: coverage_seen≥0.95 ⇒ 0b ODRZUCONE.
Env: OUTDIR, IMG_TOPIC, HOVER_ALT(9).
"""
import os, time, json, math, asyncio, subprocess, threading
import numpy as np
from mavsdk import System
from mavsdk.offboard import VelocityNedYaw, OffboardError
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from std_msgs.msg import Float32MultiArray
from sensor_msgs.msg import Image

OUTDIR = os.environ.get("OUTDIR", "results/R02/livefed/A1/run")
HOVER_ALT = float(os.environ.get("HOVER_ALT", "9.0"))
WORLD = os.environ.get("PX4_GZ_WORLD", "default")
IMG_TOPIC = os.environ.get("IMG_TOPIC", "")
DALT = 1.5                              # Δalt operacyjny (INTRUDER_ALT-ALT = 11.5-10)
R_H = math.sqrt(7.0**2 - DALT**2)       # 6.84 m poziomo (3D=7.0)
HFOV, VFOV = 1.74, 1.453                # mono_cam (SDF) — h_fov 1.74 rad, V-FOV pochodne
TGT = (0.5, 0.376); RAD = 0.20          # ROI: nominalna projekcja el~12.4° → cy 0.376; R hojne
os.makedirs(OUTDIR, exist_ok=True)


def qos_be():
    return QoSProfile(depth=5, history=HistoryPolicy.KEEP_LAST, reliability=ReliabilityPolicy.BEST_EFFORT)


def gz_set_intruder(x, y, z):
    subprocess.run(["gz", "service", "-s", f"/world/{WORLD}/set_pose", "--reqtype", "gz.msgs.Pose",
                    "--reptype", "gz.msgs.Boolean", "--timeout", "2000",
                    "--req", f'name: "intruder", position: {{x: {x:.3f}, y: {y:.3f}, z: {z:.3f}}}, orientation: {{w: 1.0}}'],
                   capture_output=True, text=True, timeout=6)


def gz_drone_pose():
    import re
    out = subprocess.run(["gz", "model", "-m", "x500_mono_cam_0", "-p"], capture_output=True, text=True, timeout=6).stdout
    nums = re.findall(r"\[\s*(-?[0-9.eE+-]+\s+-?[0-9.eE+-]+\s+-?[0-9.eE+-]+)\s*\]", out)
    xyz = [float(v) for v in nums[0].split()] if nums else None
    rpy = [float(v) for v in nums[1].split()] if len(nums) > 1 else None
    return xyz, (rpy[2] if rpy else None)


def rtf():
    return subprocess.run("gz topic -et /world/%s/stats -n 1 2>/dev/null | grep -m1 real_time_factor" % WORLD,
                          shell=True, capture_output=True, text=True, timeout=8).stdout.strip()


def project_full_attitude(pos, yaw, pitch, roll, intr):
    """KOPIA VERBATIM z r02/gate_run_r02.py:50-69 (pure)."""
    wx, wy, wz = intr[0]-pos[0], intr[1]-pos[1], intr[2]-pos[2]
    cy_, sy = math.cos(yaw), math.sin(yaw); cp, sp = math.cos(pitch), math.sin(pitch); cr, sr = math.cos(roll), math.sin(roll)
    x1 = cy_*wx + sy*wy;  y1 = -sy*wx + cy_*wy;  z1 = wz
    x2 = cp*x1 - sp*z1;   y2 = y1;               z2 = sp*x1 + cp*z1
    bx = x2;              by = cr*y2 + sr*z2;    bz = -sr*y2 + cr*z2
    if bx <= 0.1:
        return {"in_fov": False, "cx": None, "cy": None, "el_deg": None}
    az = math.atan2(by, bx); el = math.atan2(-bz, math.hypot(bx, by))
    in_fov = (abs(az) <= HFOV/2.0 and abs(el) <= VFOV/2.0)
    cx = 0.5 + math.tan(az)/(2.0*math.tan(HFOV/2.0)); cyp = 0.5 - math.tan(el)/(2.0*math.tan(VFOV/2.0))
    return {"in_fov": in_fov, "cx": round(cx, 4), "cy": round(cyp, 4),
            "az_deg": round(math.degrees(az), 2), "el_deg": round(math.degrees(el), 2)}


class DetSub(Node):
    def __init__(self):
        super().__init__("a1_detsub")
        self.samples = []; self.frame = None
        self.create_subscription(Float32MultiArray, "/liquidpatrol/detector_boxes", self._boxes, qos_be())
        if IMG_TOPIC:
            self.create_subscription(Image, IMG_TOPIC, self._img, qos_be())

    def _boxes(self, msg):
        d = list(msg.data)
        if not d:
            self.samples.append({"t": time.monotonic(), "nbox": 0, "boxes": []}); return
        flat = d[:-1]
        boxes = [tuple(round(float(x), 5) for x in flat[i:i+5]) for i in range(0, len(flat) - 4, 5)]
        self.samples.append({"t": time.monotonic(), "sim_t": d[-1], "nbox": len(boxes), "boxes": boxes})

    def _img(self, msg):
        h, w = msg.height, msg.width
        buf = np.frombuffer(bytes(msg.data), dtype=np.uint8)
        ch = len(buf) // (h * w) if h * w else 1
        self.frame = buf.reshape(h, w, ch) if ch > 1 else buf.reshape(h, w)


# stan współdzielony: najświeższe attitude (mav) z etykietą monotonic + pozy dla re-placement
STATE = {"att": [], "run": True}


async def att_logger(d):
    """Loguj attitude (mav) @~20 Hz z etykietą monotonic — do parowania z klatkami."""
    while STATE["run"]:
        async for a in d.telemetry.attitude_euler():
            STATE["att"].append({"t": time.monotonic(), "pitch": a.pitch_deg, "roll": a.roll_deg, "yaw": a.yaw_deg})
            break
        await asyncio.sleep(0.05)


def replacer():
    """Wątek: przestaw intruza dead-ahead z żywej pozy gz (~8 Hz). Utrzymuje az_nominal≈0."""
    while STATE["run"]:
        xyz, yaw = gz_drone_pose()
        if xyz is not None and yaw is not None:
            ix = xyz[0] + R_H * math.cos(yaw); iy = xyz[1] + R_H * math.sin(yaw); iz = xyz[2] + DALT
            gz_set_intruder(ix, iy, iz)
        time.sleep(0.05)


async def _health(d):
    async for h in d.telemetry.health():
        if h.is_global_position_ok and h.is_home_position_ok:
            return True
    return False


def pair_attitude(t):
    """Najbliższa próbka attitude (monotonic) do czasu odbioru klatki t. Zwraca (att, dt)."""
    best = None; bdt = 1e9
    for a in STATE["att"]:
        dt = abs(a["t"] - t)
        if dt < bdt: bdt = dt; best = a
    return best, bdt


async def main():
    rclpy.init(); det = DetSub()
    threading.Thread(target=lambda: rclpy.spin(det), daemon=True).start()
    d = System(); await d.connect(system_address="udpin://0.0.0.0:14540")
    async for s in d.core.connection_state():
        if s.is_connected: break
    print("[a1] MAVSDK connected", flush=True)
    try:
        healthy = await asyncio.wait_for(_health(d), timeout=60)
    except asyncio.TimeoutError:
        healthy = False
    if not healthy: print("[a1] HEALTH TIMEOUT", flush=True); os._exit(3)
    for i in range(20):
        try: await d.action.arm(); break
        except Exception:
            if i % 4 == 0: print(f"[a1] arm retry #{i}", flush=True)
            await asyncio.sleep(3)
    else: print("[a1] ARM FAILED", flush=True); os._exit(2)
    await d.action.set_takeoff_altitude(HOVER_ALT); await d.action.takeoff()
    for _ in range(40):
        async for pv in d.telemetry.position_velocity_ned():
            alt = -pv.position.down_m; break
        if alt >= HOVER_ALT - 1.5: break
        await asyncio.sleep(0.5)
    await asyncio.sleep(4)
    asyncio.ensure_future(att_logger(d))
    threading.Thread(target=replacer, daemon=True).start()
    await asyncio.sleep(1.5)   # niech re-placer ustawi cel + attitude się napełni

    def window_analyze(t0, t1, phase):
        seg = [s for s in det.samples if t0 <= s["t"] <= t1]
        n = len(seg); seen = 0; cxs = []; cys = []; edges = []; out_fov = 0; tconf = []; paired = 0; maxdt = 0.0
        for s in seg:
            att, dt = pair_attitude(s["t"])
            if att is not None:
                paired += 1; maxdt = max(maxdt, dt)
            best_t = None; best_c = None
            for (cx, cy, w, h, conf) in s["boxes"]:
                if math.hypot(cx - TGT[0], cy - TGT[1]) <= RAD:
                    if best_t is None or conf > best_t: best_t = conf; best_c = (cx, cy)
            if best_t is not None:
                seen += 1; tconf.append(best_t); cxs.append(best_c[0]); cys.append(best_c[1])
                edges.append(min(best_c[0], 1 - best_c[0], best_c[1], 1 - best_c[1]))
            # geometryczny in_fov z paired attitude (cel dead-ahead operacyjny wg yaw próbki)
            if att is not None:
                yaw = math.radians(att["yaw"])
                intr = (R_H * math.cos(yaw), R_H * math.sin(yaw), -DALT)  # NED: down ujemny=w górę
                pf = project_full_attitude((0, 0, 0), yaw, math.radians(att["pitch"]), math.radians(att["roll"]), intr)
                if not pf["in_fov"]: out_fov += 1

        def st(a):
            if not a: return None
            a = sorted(a); return {"n": len(a), "min": round(a[0], 4), "p50": round(a[len(a)//2], 4),
                                   "max": round(a[-1], 4)}
        return {"phase": phase, "n_frames": n, "frames_seen": seen,
                "coverage_seen": round(seen / n, 3) if n else None,
                "frames_out_of_fov_geom": out_fov, "box_cx": st(cxs), "box_cy": st(cys), "box_edge": st(edges),
                "true_conf": st(tconf), "att_paired": paired, "pair_maxdt_s": round(maxdt, 3)}

    # FAZA HOVER baseline (5 s) — cel operacyjny, brak ruchu
    await d.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
    try:
        await d.offboard.start()
    except OffboardError as e:
        print("[a1] offboard err", e, flush=True); os._exit(4)
    rtf0 = rtf(); det.samples.clear(); STATE["att"].clear()
    th0 = time.monotonic(); await asyncio.sleep(8); th1 = time.monotonic()
    hover = window_analyze(th0 + 1.0, th1, "hover")

    # FAZA OBSERVE-MOTION (profil B1: kwadrat/ósemka, V=2.5, 2.5 s/leg)
    V = 2.5
    legs = [(V, 0), (V, 0), (0, V), (0, V), (-V, 0), (-V, 0), (0, -V), (0, -V)]
    tm0 = time.monotonic()
    for (vn, ve) in legs:
        await d.offboard.set_velocity_ned(VelocityNedYaw(vn, ve, 0, 0))
        await asyncio.sleep(2.5)
    tm1 = time.monotonic()
    await d.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
    motion = window_analyze(tm0 + 0.5, tm1, "motion")
    rtf1 = rtf()

    res = {
        "HEADLESS": os.environ.get("HEADLESS"), "RENDER_BACKEND": os.environ.get("RENDER_BACKEND"),
        "GZ_VER": subprocess.run(["gz", "sim", "--version"], capture_output=True, text=True).stdout.strip()[:40],
        "instrument": "mav (attitude ~20Hz), monotonic (parowanie klatka↔attitude)",
        "geometry": {"R_h_m": round(R_H, 3), "delta_alt_m": DALT, "range_3d_m": 7.0,
                     "el_nom_deg": round(math.degrees(math.atan2(DALT, R_H)), 2), "ROI": TGT, "ROI_R": RAD},
        "rtf_start": rtf0, "rtf_end": rtf1, "theta_conf": 0.1635,
        "HOVER": hover, "MOTION": motion,
        "routing_rule": "coverage_seen>=0.95 => 0b ODRZUCONE definitywnie (PRE_R02C/A1)",
        "note": "cel CIĄGLE dead-ahead (re-placer 8Hz) geometria operacyjna; coverage_seen=box≤R od projekcji; "
                "frames_out_of_fov_geom z paired attitude; motion-blur widoczne w coverage (nie w torze geom).",
    }
    if det.frame is not None:
        np.save(os.path.join(OUTDIR, "frame_motion.npy"), det.frame)
        g = (det.frame[..., 0] if det.frame.ndim == 3 else det.frame).astype(int)
        res["frame_min"] = int(g.min()); res["frame_mean"] = round(float(g.mean()), 1)
        try:
            from PIL import Image as PImage, ImageDraw
            arr = det.frame if det.frame.ndim == 3 else np.stack([det.frame] * 3, -1)
            im = PImage.fromarray(arr[..., :3].astype(np.uint8)).convert("RGB"); dr = ImageDraw.Draw(im); W, H = im.size
            tx, ty = int(TGT[0]*W), int(TGT[1]*H)
            dr.ellipse([tx-int(RAD*W), ty-int(RAD*H), tx+int(RAD*W), ty+int(RAD*H)], outline=(255, 0, 0), width=2)
            im.save(os.path.join(OUTDIR, "frame_motion_overlay.png")); res["overlay"] = "frame_motion_overlay.png"
        except Exception as e:
            res["overlay_err"] = str(e)
    verdict = "0b ODRZUCONE" if (motion["coverage_seen"] or 0) >= 0.95 else "0b WRACA do ratyfikacji"
    res["verdict"] = verdict
    json.dump(res, open(os.path.join(OUTDIR, "result.json"), "w"), indent=2, ensure_ascii=False)
    json.dump({"att": STATE["att"], "det": det.samples}, open(os.path.join(OUTDIR, "raw.json"), "w"))
    print(f"[a1] HOVER cov={hover['coverage_seen']} out_fov={hover['frames_out_of_fov_geom']} | "
          f"MOTION cov={motion['coverage_seen']} seen={motion['frames_seen']}/{motion['n_frames']} "
          f"out_fov={motion['frames_out_of_fov_geom']} conf={motion['true_conf']} pair_dt={motion['pair_maxdt_s']}", flush=True)
    print(f"[a1] rtf {rtf0}->{rtf1}  VERDICT={verdict}", flush=True)
    STATE["run"] = False
    try:
        await d.offboard.stop(); await d.action.land(); await asyncio.sleep(3)
    except Exception: pass
    os._exit(0)


asyncio.run(main())
