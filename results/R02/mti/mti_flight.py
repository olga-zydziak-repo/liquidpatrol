#!/usr/bin/env python3
"""mti_flight.py — B4/B5 charakteryzacja+bramka MTI w world_demo_v1 (headless, ANEKS-H).

Jeden proces: YOLO (struktura) + MTI (r02.mti, derotacja z XRCE vehicle_attitude) + brama struktura∧MTI
(target_channel entry_require_mti=True; conf PASYWNE). Dron OBSERVE-motion (profil B1, ego-motion dla
derotacji); intruz re-placer dead-ahead na zasięgu R z OSCYLACJĄ boczną (ruch względny dla MTI, R stały).

Fazy (env PHASES): sweep zasięgów {5,7,9} (coverage +); fp_empty (zawis, brak intruza); fp_bg (OBSERVE-motion,
brak intruza, teksturowany grunt → paralaksa = dominujące FP). Metryki: coverage struktura∧MTI, czas-do-ENTRY,
komponenty MTI/klatkę (mediana+IQR R-M2), fałszywe ENTRY. Parowanie klatka↔attitude: recv-monotonic (100 Hz
XRCE) + offset O(sim↔epoch) raportowany dla stabilności (SR-M1). Etykiety: mav/monotonic; sim_t z header klatki.
Env: OUTDIR, IMG_TOPIC, HOVER_ALT(9), RANGES, DWELL_S, FP_EMPTY_S, FP_BG_S, PHASES, PX4_GZ_WORLD.
"""
import os, sys, time, json, math, asyncio, subprocess, threading, statistics
import numpy as np
import cv2
from mavsdk import System
from mavsdk.offboard import VelocityNedYaw, OffboardError
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image
from px4_msgs.msg import VehicleAttitude

sys.path.insert(0, "/home/olga/projects/liquidpatrol")
from r02.mti import MTITracker, MTIParams, box_matches_component
from r02.target_channel import TargetChannel, Box, EV_ENTRY
from r02.config_r02 import ChannelConfig
from dataclasses import replace

OUTDIR = os.environ.get("OUTDIR", "results/R02/mti/B4/run")
HOVER_ALT = float(os.environ.get("HOVER_ALT", "9.0"))
WORLD = os.environ.get("PX4_GZ_WORLD", "world_demo_v1")
IMG_TOPIC = os.environ.get("IMG_TOPIC", "")
RANGES = [float(x) for x in os.environ.get("RANGES", "5,7,9").split(",")] if os.environ.get("RANGES") else [5.0, 7.0, 9.0]
DWELL_S = float(os.environ.get("DWELL_S", "30"))
FP_EMPTY_S = float(os.environ.get("FP_EMPTY_S", "300"))
FP_BG_S = float(os.environ.get("FP_BG_S", "300"))
PHASES = os.environ.get("PHASES", "sweep,fp_empty,fp_bg").split(",")
DALT = 1.5
DECISION_HZ = 2.0
os.makedirs(OUTDIR, exist_ok=True)
WEIGHTS = os.environ.get("YOLO_WEIGHTS", "/home/olga/projects/liquidpatrol/.b0deps/weights/yolov8s-worldv2.pt")


def qos_be(depth=10):
    return QoSProfile(depth=depth, history=HistoryPolicy.KEEP_LAST, reliability=ReliabilityPolicy.BEST_EFFORT)


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


class Sensors(Node):
    """Kamera (15 Hz, sim-stamp) + XRCE vehicle_attitude (100 Hz). Bufory z recv-monotonic do parowania."""
    def __init__(self):
        super().__init__("mti_sensors")
        self.att = []          # (recv, ts_s_epoch, q[w,x,y,z])
        self.frames = []       # (recv, sim_s, frame)
        self.O = None          # ZAMROŻONY offset epoch↔sim (PRE_MTI R1); parowanie po TREŚCI, nie recv
        self.pair_resid = []   # rezyduum parowania po treści [s] (stabilność SR-M1)
        self.create_subscription(VehicleAttitude, "/fmu/out/vehicle_attitude", self._att, qos_be(50))
        if IMG_TOPIC:
            self.create_subscription(Image, IMG_TOPIC, self._img, qos_be(10))

    def _att(self, m):
        q = [float(m.q[0]), float(m.q[1]), float(m.q[2]), float(m.q[3])]
        self.att.append((time.monotonic(), m.timestamp * 1e-6, q))
        if len(self.att) > 600:
            self.att = self.att[-600:]

    def _img(self, msg):
        h, w = msg.height, msg.width
        buf = np.frombuffer(bytes(msg.data), dtype=np.uint8)
        enc = msg.encoding.lower()
        if enc in ("rgb8", "bgr8"):
            frame = buf.reshape(h, w, 3).mean(axis=2).astype(np.uint8)
        else:
            frame = buf[:h * w].reshape(h, w)
        sim_s = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        self.frames.append((time.monotonic(), sim_s, frame))
        if len(self.frames) > 60:
            self.frames = self.frames[-60:]

    def freeze_offset(self, samples):
        """PRE_MTI R1: zamróź O = median(att_ts_epoch - frame_sim_elapsed) z recv-bliskich par w OKNIE
        SPOKOJNYM (przed YOLO, mała kontencja → recv-parowanie wiarygodne). Potem parowanie PO TREŚCI."""
        Os = []
        for (recv, sim_s, _f) in self.frames[-samples:]:
            a = self._pair_att_recv(recv)
            if a: Os.append(a[1] - sim_s)
        if Os:
            Os.sort(); self.O = Os[len(Os) // 2]
        return self.O, (round(Os[-1] - Os[0], 4) if len(Os) > 2 else None)

    def _pair_att_recv(self, recv):
        best = None; bdt = 1e9
        for a in self.att[-300:]:
            dt = abs(a[0] - recv)
            if dt < bdt: bdt = dt; best = a
        return (best[2], best[1], bdt) if best else None

    def pair_by_content(self, sim_s):
        """Attitude sparowane PO TREŚCI: min|att_ts - O - sim_s| (odporne na jitter callbacków). O zamrożony."""
        if self.O is None:
            a = self._pair_att_recv(time.monotonic()); return (a[0], 0.0) if a else None
        best = None; bd = 1e9
        for a in self.att[-400:]:
            d = abs((a[1] - self.O) - sim_s)
            if d < bd: bd = d; best = a
        if best is None: return None
        self.pair_resid.append(bd)
        if len(self.pair_resid) > 400: self.pair_resid = self.pair_resid[-400:]
        return (best[2], bd)


def pctl(a, p):
    if not a: return None
    a = sorted(a); return a[min(len(a) - 1, int(p / 100 * len(a)))]


def summ(a):
    """mediana + IQR (R-M2); max informacyjnie."""
    if not a: return None
    a = sorted(a)
    return {"n": len(a), "median": round(a[len(a) // 2], 4), "q1": round(pctl(a, 25), 4),
            "q3": round(pctl(a, 75), 4), "max": round(a[-1], 4)}


async def _health(d):
    async for h in d.telemetry.health():
        if h.is_global_position_ok and h.is_home_position_ok:
            return True
    return False


# stan współdzielony re-placera
RP = {"run": True, "mode": "off", "R": 7.0, "t0": 0.0}


def replacer():
    """Intruz dead-ahead na R z oscylacją boczną (ruch względny dla MTI). mode: off/track/far."""
    while RP["run"]:
        if RP["mode"] == "off":
            time.sleep(0.1); continue
        xyz, yaw = gz_drone_pose()
        if xyz is None or yaw is None:
            time.sleep(0.1); continue
        if RP["mode"] == "far":
            gz_set_intruder(xyz[0] - 60.0, xyz[1], 3.0); time.sleep(0.2); continue
        R = RP["R"]; R_h = math.sqrt(max(R * R - DALT * DALT, 1.0))
        t = time.monotonic() - RP["t0"]
        osc = 1.5 * math.sin(2 * math.pi * 0.3 * t)          # ±1.5 m boczna oscylacja @0.3 Hz
        vosc = 0.6 * math.sin(2 * math.pi * 0.23 * t)        # niewielka pionowa
        fwd = (math.cos(yaw), math.sin(yaw)); right = (-math.sin(yaw), math.cos(yaw))
        ix = xyz[0] + R_h * fwd[0] + osc * right[0]
        iy = xyz[1] + R_h * fwd[1] + osc * right[1]
        iz = xyz[2] + DALT + vosc
        gz_set_intruder(ix, iy, iz)
        time.sleep(0.06)


async def main():
    rclpy.init(); sen = Sensors()
    threading.Thread(target=lambda: rclpy.spin(sen), daemon=True).start()
    tracker = MTITracker(MTIParams(), delta=3)   # baseline 200ms (dynamika celu ~3 m/s)
    cfg = replace(ChannelConfig(), entry_require_mti=True)
    threading.Thread(target=replacer, daemon=True).start()

    d = System(); await d.connect(system_address="udpin://0.0.0.0:14540")
    async for s in d.core.connection_state():
        if s.is_connected: break
    print("[mti] MAVSDK connected", flush=True)
    # ARM: YOLO NIE załadowany jeszcze (redukcja kontencji CPU w oknie EKF — E2/ANEKS-H).
    try:
        healthy = await asyncio.wait_for(_health(d), timeout=90)
    except asyncio.TimeoutError:
        healthy = False
    if not healthy: print("[mti] HEALTH TIMEOUT", flush=True); os._exit(3)
    armed = False
    for i in range(60):
        try: await d.action.arm(); armed = True; break
        except Exception:
            if i % 6 == 0: print(f"[mti] arm retry #{i}", flush=True)
            await asyncio.sleep(3)
    if not armed: print("[mti] ARM FAILED", flush=True); os._exit(2)
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
        print("[mti] offboard err", e, flush=True); os._exit(4)
    # ZAMROŻENIE OFFSETU O w OKNIE SPOKOJNYM (przed YOLO — mała kontencja, recv-parowanie wiarygodne).
    # PRE_MTI R1 / SR-M1: potem parowanie klatka↔attitude PO TREŚCI (odporne na jitter callbacków).
    await asyncio.sleep(4.0)
    O, O_spread0 = sen.freeze_offset(45)
    print(f"[mti] O_frozen={O} (init spread={O_spread0}s, n_frames_buf={len(sen.frames)})", flush=True)
    # YOLO ładowany DOPIERO PO uzbrojeniu+starcie+O (poza oknem EKF)
    print(f"[mti] YOLO load {WEIGHTS}", flush=True)
    from ultralytics import YOLO
    model = YOLO(WEIGHTS); model.set_classes(["drone"])

    # MTI worker: konsumuje klatki 15 Hz, paruje attitude, push do trackera; utrzymuje ostatnie komponenty
    STATE = {"comps": [], "last_sim": None, "last_frame": None, "run": True, "comp_counts": []}

    def mti_worker():
        seen = 0
        while STATE["run"]:
            fr = sen.frames[-1] if sen.frames else None
            if fr is None or fr[0] == STATE.get("last_recv"):
                time.sleep(0.02); continue
            STATE["last_recv"] = fr[0]
            recv, sim_s, frame = fr
            qa = sen.pair_by_content(sim_s)      # parowanie PO TREŚCI (frozen O), nie recv
            if qa is None:
                time.sleep(0.02); continue
            comps, dbg = tracker.push(frame, qa[0])
            STATE["comps"] = comps; STATE["last_sim"] = sim_s; STATE["last_frame"] = frame
            if not dbg.get("warmup"):
                STATE["comp_counts"].append(len(comps))
            time.sleep(0.005)
    threading.Thread(target=mti_worker, daemon=True).start()

    async def observe_motion(dur, legs_v=2.5):
        """Profil OBSERVE (kwadrat) przez dur s; nieblokujący re-placera."""
        legs = [(legs_v, 0), (0, legs_v), (-legs_v, 0), (0, -legs_v)]
        t0 = time.monotonic(); i = 0
        while time.monotonic() - t0 < dur:
            vn, ve = legs[i % len(legs)]
            await d.offboard.set_velocity_ned(VelocityNedYaw(vn, ve, 0, 0))
            await asyncio.sleep(2.0); i += 1
        await d.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))

    def decide_once(ch, gt_present):
        """Jeden tik decyzyjny @DECISION_HZ: YOLO struktura + MTI koincydencja + kanał. Zwraca rekord."""
        frame = STATE["last_frame"]; sim_t = STATE["last_sim"]; comps = list(STATE["comps"])
        if frame is None or sim_t is None:
            return None
        img3 = np.stack([frame] * 3, -1)
        res = model.predict(img3, imgsz=640, conf=0.001, verbose=False)[0]
        box = None; conf = None
        if res.boxes is not None and len(res.boxes) > 0:
            xywhn = res.boxes.xywhn.cpu().numpy(); confs = res.boxes.conf.cpu().numpy()
            j = int(np.argmax(confs))
            box = Box(float(xywhn[j][0]), float(xywhn[j][1]), float(xywhn[j][2]), float(xywhn[j][3]), conf=float(confs[j]))
            conf = float(confs[j])
        mti_ok = box_matches_component(box, comps, cfg.mti_center_thr) if box is not None else False
        central = box is not None and box.edge_dist() >= cfg.entry_edge_margin
        ev = ch.on_frame(box, sim_t, gt_present=gt_present, mti_ok=mti_ok)
        gate = bool(box is not None and central and mti_ok)   # struktura∧MTI (admisja tej klatki)
        return {"sim_t": round(sim_t, 3), "has_box": box is not None, "conf": conf,
                "central": central, "n_comps": len(comps), "mti_ok": bool(mti_ok),
                "gate": gate, "entry": ev == EV_ENTRY, "locked": ch.locked}

    results = {"world": WORLD, "world_hash": None, "HEADLESS": os.environ.get("HEADLESS"),
               "instrument": "mav/monotonic; sim_t z header klatki; XRCE vehicle_attitude 100Hz",
               "params": {"decision_hz": DECISION_HZ, "dwell_s": DWELL_S, "dalt": DALT,
                          "mti": MTIParams().__dict__, "require_mti": True, "theta_conf_defined": cfg.entry_theta_conf},
               "rtf_start": rtf(), "phases": {}}

    async def run_dwell(label, R, dur, gt_present):
        ch = TargetChannel(cfg)
        RP["R"] = R; RP["t0"] = time.monotonic()
        RP["mode"] = "track" if gt_present else "far"
        await asyncio.sleep(2.0)   # niech re-placer ustawi cel + MTI się rozgrzeje
        recs = []; t_start = time.monotonic(); t_entry = None
        # ruch OBSERVE równolegle z decyzjami
        motion_task = asyncio.ensure_future(observe_motion(dur))
        period = 1.0 / DECISION_HZ
        while time.monotonic() - t_start < dur:
            r = decide_once(ch, gt_present)
            if r:
                recs.append(r)
                if r["entry"] and t_entry is None:
                    t_entry = round(time.monotonic() - t_start, 2)
            await asyncio.sleep(period)
        await motion_task
        n = len(recs)
        seen = sum(1 for r in recs if r["has_box"])
        gate = sum(1 for r in recs if r["gate"])
        locked = sum(1 for r in recs if r["locked"])
        # coverage_locked PO akwizycji (operacyjne: kanał trzyma lock ZOH-age między detekcjami)
        recs_post = recs[recs.index(next((r for r in recs if r["entry"]), recs[-1])):] if any(r["entry"] for r in recs) else []
        locked_post = sum(1 for r in recs_post if r["locked"])
        n_entry = sum(1 for r in recs if r["entry"])
        false_entry = sum(1 for r in recs if r["entry"] and gt_present is False)
        confs = [r["conf"] for r in recs if r["conf"] is not None]
        comps_dist = [r["n_comps"] for r in recs]
        return {
            "label": label, "R": R, "dur_s": round(time.monotonic() - t_start, 1), "gt_present": gt_present,
            "n_ticks": n, "coverage_seen": round(seen / n, 3) if n else None,
            "coverage_gate": round(gate / n, 3) if n else None,
            "coverage_locked": round(locked / n, 3) if n else None,
            "coverage_locked_post_entry": round(locked_post / len(recs_post), 3) if recs_post else None,
            "n_entry": n_entry, "false_entry": false_entry,
            "time_to_entry_s": t_entry,
            "conf_passive": summ(confs), "mti_comps_per_tick": summ(comps_dist),
            "mti_comps_stream": summ(STATE["comp_counts"][-int(dur * 12):]),
        }

    # --- SWEEP (coverage +) ---
    if "sweep" in PHASES:
        for R in RANGES:
            res = await run_dwell(f"sweep_{R:g}m", R, DWELL_S, gt_present=True)
            results["phases"][f"sweep_{R:g}m"] = res
            print(f"[mti] sweep {R:g}m cov_seen={res['coverage_seen']} cov_gate={res['coverage_gate']} "
                  f"n_entry={res['n_entry']} t_entry={res['time_to_entry_s']} comps={res['mti_comps_per_tick']}", flush=True)
    # --- FP empty (zawis, brak intruza) ---
    if "fp_empty" in PHASES:
        RP["mode"] = "far"; await asyncio.sleep(2.0)
        ch = TargetChannel(cfg); t0 = time.monotonic(); recs = []
        while time.monotonic() - t0 < FP_EMPTY_S:
            r = decide_once(ch, gt_present=False)
            if r: recs.append(r)
            await asyncio.sleep(1.0 / DECISION_HZ)
        fe = sum(1 for r in recs if r["entry"]); mins = (time.monotonic() - t0) / 60.0
        results["phases"]["fp_empty"] = {"label": "fp_empty_hover", "dur_s": round(time.monotonic()-t0,1),
            "n_ticks": len(recs), "false_entry": fe, "eps_fp_per_min": round(fe / mins, 3) if mins else None,
            "mti_comps_per_tick": summ([r["n_comps"] for r in recs])}
        print(f"[mti] FP_EMPTY false_entry={fe} eps_fp/min={results['phases']['fp_empty']['eps_fp_per_min']}", flush=True)
    # --- FP bg-motion (OBSERVE-motion, brak intruza, teksturowany grunt) ---
    if "fp_bg" in PHASES:
        RP["mode"] = "far"; await asyncio.sleep(1.0)
        ch = TargetChannel(cfg); t0 = time.monotonic(); recs = []
        motion_task = asyncio.ensure_future(observe_motion(FP_BG_S))
        while time.monotonic() - t0 < FP_BG_S:
            r = decide_once(ch, gt_present=False)
            if r: recs.append(r)
            await asyncio.sleep(1.0 / DECISION_HZ)
        await motion_task
        fe = sum(1 for r in recs if r["entry"]); mins = (time.monotonic() - t0) / 60.0
        gatef = sum(1 for r in recs if r["gate"])
        results["phases"]["fp_bg"] = {"label": "fp_bg_observe_motion", "dur_s": round(time.monotonic()-t0,1),
            "n_ticks": len(recs), "false_entry": fe, "eps_fp_per_min": round(fe / mins, 3) if mins else None,
            "false_gate_frames": gatef, "mti_comps_per_tick": summ([r["n_comps"] for r in recs])}
        print(f"[mti] FP_BG false_entry={fe} eps_fp/min={results['phases']['fp_bg']['eps_fp_per_min']} "
              f"false_gate_frames={gatef}", flush=True)

    STATE["run"] = False; RP["run"] = False
    results["rtf_end"] = rtf()
    results["pairing"] = {"O_frozen_s": round(sen.O, 3) if sen.O else None,
                          "content_resid_median_ms": round(1000 * statistics.median(sen.pair_resid), 2) if sen.pair_resid else None,
                          "content_resid_p95_ms": round(1000 * pctl(sen.pair_resid, 95), 2) if len(sen.pair_resid) > 10 else None,
                          "n_pairs": len(sen.pair_resid)}
    json.dump(results, open(os.path.join(OUTDIR, "result.json"), "w"), indent=2, ensure_ascii=False)
    print(f"[mti] DONE rtf {results['rtf_start']}->{results['rtf_end']} pairing={results['pairing']}", flush=True)
    try:
        await d.offboard.stop(); await d.action.land(); await asyncio.sleep(3)
    except Exception: pass
    os._exit(0)


asyncio.run(main())
