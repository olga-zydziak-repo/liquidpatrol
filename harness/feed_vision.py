#!/usr/bin/env python3
"""harness/feed_vision.py — FEED-V: producent feedu percepcyjnego (noga 2A, PRE_2A §2 D1/D2/D4).

REGUŁA NADRZĘDNA (PROMPT_2A_S1): FEED-V konsumuje WYŁĄCZNIE klatki kamery pokładowej + stan
własny z POKŁADU (EKF: /fmu/out/vehicle_local_position; attitude: /fmu/out/vehicle_attitude).
GT nie występuje w tym pliku w żadnej postaci — GT żyje wyłącznie u sędziego offline
(results/2A/tools/percep_judge.py).

Tor: klatka (sim-time ze stempla) → YOLO-World top-1 (D4, wagi frozen 9b2c17ab, guard SR-2)
→ MTI (derotacja z attitude, r02/mti.py READ-ONLY import) → admisja STRUKTURA∧MTI przez
TargetChannel (ENTRY k=3, sufit θ_age; r02/target_channel.py READ-ONLY import) → pinhole
box→NED (D1: Z = f_px·W_real/w_px, kierunek z (cx,cy) + quat pokładowy) → REFRESH bramkowany
(ANEKS_2A-1 N2: koniunkcja admisyjna NA KLATCE albo okno REFRESH_GATE_M wokół predykcji;
inaczej ZOH — top-1 tła nigdy nie odświeża tracku) → kontrakt R1:
{trk_pos_ned, trk_vel_ned (linreg 1 s sim), track_age_s, track_valid, feed_sha}.

Tryby: LIVE (FeedVisionLive: subskrypcje ROS2, własny spin-thread — zero edycji pętli
bench_flight poza rejestrem) · REPLAY/SYNTETYCZNY (push_frame/ingest_box wołane z zewnątrz
— smoke S1, sędzia etapu B). Semantyka utraty: producent trzyma hold-last z rosnącym age
(jak FeedB); hover-hold robi KONSUMENT (kontrakt R1), nie producent.

Stałe geometrii (FREEZE_2A):
  f_px = 270.0 — kanon przyrządu MTI (r02/mti.py:17, PRE_MTI R1 z mono_cam/model.sdf);
         dokładnie: (640/2)/tan(1.74/2) = 269.976 px — rozjazd 0.009% wobec kanonu.
  W_real = 2.5 m — rozpiętość ramion intruza, r02/intruder_model.sdf:15/18
         (<size>0.16 2.5 0.14</size> ×2 ramiona krzyżowe); jawny prior klasy celu (D1).
  Offset kamery w FRD: (0.12, −0.03, −0.242) m — x500_mono_cam/model.sdf pose
         `.12 .03 .242` (gz body: x przód, y lewo, z góra → FRD: y,z ze zmianą znaku).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import time

from r02.mti import (FX, CX, CY, IMG_W, IMG_H, quat_to_R,
                     MTITracker, MTIParams, box_matches_component)
from r02.target_channel import TargetChannel, Box
from r02.config_r02 import ChannelConfig, MTI_CENTER_THR
from harness.track_feed import _slope

# --- stałe zamrożone (echo w FREEZE_2A) --------------------------------------
F_PX = FX                                   # 270.0 (r02/mti.py:17 — jedna ogniskowa w całym programie)
W_REAL_M = 2.5                              # r02/intruder_model.sdf:15/18 (ramiona 2.5 m)
CAM_OFF_FRD = (0.12, -0.03, -0.242)         # x500_mono_cam/model.sdf (gz → FRD)
WEIGHTS_SHA = "9b2c17ab6124a913e9b3a5c170617920d91b0f01111a8479da69f00e2cf27792"  # RAPORT_B0:24
WEIGHTS_DEFAULT = ".b0deps/weights/yolov8s-worldv2.pt"
VEL_WINDOW_S = 1.0                          # D4: trk_vel jak FeedB (linreg 1 s sim)
FRAME_HZ_NOMINAL = 15.0                     # kamera stock (D3)
# ANEKS_2A-1 N2: promień okna bramkowania REFRESH wokół predykcji tracku [m] (decyzja
# wykonawcza, echo w FREEZE_2A). Kalibracja klas z danych S2: błąd całkowity FeedB p95
# 1.26 m (kalibracja S1) + ruch celu ≤1 m/s w oknie ZOH + jitter zasięgu pinhole ~1 m
# przy widocznym celu — a FP tła leżały ≥5 m (768/810 powyżej progu 5 m, RAPORT_2A_S2 §4).
REFRESH_GATE_M = 3.0


def box_to_ned(box: Box, own_pos_ned, q_frd2ned):
    """Pinhole (D1): box znormalizowany [0,1] + poza własna (EKF) → pozycja celu NED [m].
    Z = f_px·W_real/w_px (głębia wzdłuż osi optycznej); ramka optyczna per r02/mti.py:
    z_opt=przód(+X_frd), x_opt=prawo(+Y_frd), y_opt=dół(+Z_frd). Zwraca None dla boxa
    zdegenerowanego (w_px ≤ 1 px)."""
    w_px = float(box.w) * IMG_W
    if w_px <= 1.0:
        return None
    Z = F_PX * W_REAL_M / w_px
    u = float(box.cx) * IMG_W
    v = float(box.cy) * IMG_H
    x_opt = (u - CX) / F_PX * Z
    y_opt = (v - CY) / F_PX * Z
    # FRD = C_FRD2OPT^T @ opt:  x_frd=z_opt, y_frd=x_opt, z_frd=y_opt
    p_frd = (Z + CAM_OFF_FRD[0], x_opt + CAM_OFF_FRD[1], y_opt + CAM_OFF_FRD[2])
    R = quat_to_R(q_frd2ned)                # [w,x,y,z] FRD→NED (konwencja r02/mti.py:9)
    return [own_pos_ned[0] + R[0, 0] * p_frd[0] + R[0, 1] * p_frd[1] + R[0, 2] * p_frd[2],
            own_pos_ned[1] + R[1, 0] * p_frd[0] + R[1, 1] * p_frd[1] + R[1, 2] * p_frd[2],
            own_pos_ned[2] + R[2, 0] * p_frd[0] + R[2, 1] * p_frd[1] + R[2, 2] * p_frd[2]]


class YoloDetector:
    """Detektor D4 1:1 z toru C (RAPORT_B0): YOLO-World, classes=["drone"], imgsz 640,
    conf=0.001 (telemetrycznie). Guard SR-2: sha wag ≠ FREEZE ⇒ RuntimeError ODMOWA."""

    def __init__(self, weights=None, device=None):
        self.weights = weights or os.environ.get("YOLO_WEIGHTS", WEIGHTS_DEFAULT)
        h = hashlib.sha256()
        with open(self.weights, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 16), b""):
                h.update(chunk)
        got = h.hexdigest()
        if got != WEIGHTS_SHA:
            raise RuntimeError(f"[feed_vision] weights_sha rozjazd z FREEZE_2A "
                               f"({got[:16]}≠{WEIGHTS_SHA[:16]}) — ODMOWA (SR-2)")
        self.weights_sha = got
        import torch
        from ultralytics import YOLOWorld
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = YOLOWorld(self.weights)
        self.model.set_classes(["drone"])

    def top1(self, frame_rgb_or_mono):
        """Top-1 box (max conf) BEZ bramkowania conf (A1) → Box znormalizowany | None."""
        import numpy as np
        fr = frame_rgb_or_mono
        if fr.ndim == 2:
            fr = np.stack([fr] * 3, axis=-1)
        r = self.model.predict(fr, imgsz=640, conf=0.001, verbose=False, device=self.device)[0]
        if r.boxes is None or len(r.boxes) == 0:
            return None
        i = int(r.boxes.conf.argmax())
        x, y, w, h = [float(t) for t in r.boxes.xywh[i]]
        H, W = fr.shape[:2]
        return Box(cx=x / W, cy=y / H, w=w / W, h=h / H, conf=float(r.boxes.conf[i]))


class FeedVision:
    """Rdzeń FEED-V (bez ROS2 — testowalny). Zewnętrze woła:
    push_own(sim_t, pos_ned, q) — stan własny POKŁADOWY (EKF + attitude);
    push_frame(sim_t, frame_mono_u8) — pełny tor (YOLO+MTI) [REPLAY/LIVE];
    ingest_box(sim_t, box|None, mti_ok) — tor od admisji w dół [SYNTETYCZNY smoke];
    sample(sim_now) — kontrakt R1 (ten sam dict co FeedB._out)."""

    def __init__(self, detector: YoloDetector | None = None, log_path=None,
                 mti_params: MTIParams | None = None, cfg: ChannelConfig | None = None):
        self.cfg = cfg or ChannelConfig(entry_require_mti=True)      # D2: struktura∧MTI
        assert self.cfg.entry_require_mti, "FEED-V wymaga bramy struktura∧MTI (PRE_2A D2)"
        self.channel = TargetChannel(self.cfg)
        self.mti = MTITracker(mti_params or MTIParams())
        self.detector = detector
        self.params = {"profile": "V", "detector": "yolov8s-worldv2", "weights_sha": WEIGHTS_SHA,
                       "imgsz": 640, "classes": ["drone"], "f_px": F_PX, "w_real_m": W_REAL_M,
                       "img_wh": [IMG_W, IMG_H], "cam_hfov_rad": 1.74, "cam_off_frd": list(CAM_OFF_FRD),
                       "entry_k": self.cfg.entry_k, "entry_require_mti": True,
                       "mti_center_thr": MTI_CENTER_THR, "theta_age_s": self.cfg.theta_age_s,
                       "vel_window_s": VEL_WINDOW_S, "frame_hz_nominal": FRAME_HZ_NOMINAL,
                       "pos": "pinhole_raw", "trk_vel": "linreg_1s_sim",
                       "refresh_gate": "admisja(central∧mti) OR okno predykcji (ANEKS_2A-1 N2)",
                       "refresh_gate_m": REFRESH_GATE_M}
        self.feed_sha = hashlib.sha256(json.dumps(self.params, sort_keys=True).encode()).hexdigest()
        self._own = None                 # (sim_t, pos_ned[3], q[4] wxyz) — ostatni stan pokładowy
        self._last_pos = None
        self._last_fresh_sim = None
        self._issued = []                # [(sim_t, pos)] świeże pozycje tracku (do linreg)
        self.n_frames = 0
        self.n_boxes = 0
        self.n_fresh = 0                 # admitowane aktualizacje tracku
        self.n_feed_expire = 0           # N2: wygaśnięcia tracku feedu (sufit θ_age po stronie feedu)
        self._log = open(log_path, "w") if log_path else None

    # --- wejścia ------------------------------------------------------------
    def push_own(self, sim_t, pos_ned, q_wxyz):
        self._own = (float(sim_t), [float(x) for x in pos_ned], [float(x) for x in q_wxyz])

    def push_frame(self, sim_t, frame_mono_u8):
        """Pełny tor na klatce: YOLO top-1 + MTI(frame, q) → _ingest. Wymaga push_own wcześniej."""
        if self._own is None:
            return None                   # bez stanu własnego klatka jest bezużyteczna (nie ma projekcji)
        q = self._own[2]
        box = self.detector.top1(frame_mono_u8) if self.detector else None
        comps, _dbg = self.mti.push(frame_mono_u8, q)
        mti_ok = box_matches_component(box, comps, self.cfg.mti_center_thr) if box else False
        self.n_frames += 1
        return self._ingest(float(sim_t), box, bool(mti_ok))

    def ingest_box(self, sim_t, box: Box | None, mti_ok: bool):
        """Tor syntetyczny (smoke S1 (c)): od admisji w dół, bez YOLO/MTI na klatce."""
        return self._ingest(float(sim_t), box, bool(mti_ok))

    # --- rdzeń --------------------------------------------------------------
    def _ingest(self, t, box, mti_ok):
        if box is not None:
            self.n_boxes += 1
        expired_now = False
        if (self.channel.locked and self._last_fresh_sim is not None
                and t - self._last_fresh_sim > self.cfg.theta_age_s):
            # ANEKS_2A-1 N2: sufit wieku TRACKU FEEDU (ten sam θ_age co kanał). Kanał frozen
            # odświeża swój wiek KAŻDYM boxem przy locku (target_channel.py:123 „Refresh locka
            # NIE stosuje ani edge-margin, ani conf/MTI"), więc tło podtrzymywałoby lock w
            # nieskończoność — wygaśnięcie orzeka FEED i wymusza PEŁNĄ re-admisję
            # (ENTRY k=3 struktura∧MTI) przez reset kanału (API, nie edycja frozen).
            self.channel.reset()
            self._last_pos = None
            self._issued = []
            self.n_feed_expire += 1
            expired_now = True
        ev = self.channel.on_frame(box, t, mti_ok=mti_ok)
        if ev is None and expired_now:
            ev = "FEED_EXPIRE"
        fresh = False
        gate = None
        pos = None
        if self.channel.locked and box is not None and self._own is not None:
            cand = box_to_ned(box, self._own[1], self._own[2])
            if cand is not None:
                # ANEKS_2A-1 N2: REFRESH bramkowany — track odświeża WYŁĄCZNIE box, który
                # (a) spełnia koniunkcję admisyjną struktura∧MTI NA TEJ KLATCE (central z
                #     last_conj kanału — ta sama geometria co brama ENTRY — ∧ mti_ok), ALBO
                # (b) mieści się w oknie REFRESH_GATE_M wokół predykcji tracku
                #     (last_pos + trk_vel·Δt od ostatniej świeżej).
                # Brak zgodnego boxa ⇒ ZOH z rosnącym age (lustro semantyki dropu FeedB),
                # NIGDY refresh z top-1 tła (lekcja S2: 768/810 FP-admisji po ENTRY).
                if self.channel.last_conj["central"] and bool(mti_ok):
                    gate = "mti"
                elif self._last_pos is not None:
                    dt = t - self._last_fresh_sim if self._last_fresh_sim is not None else 0.0
                    vel = self._trk_vel(t)
                    pred = [self._last_pos[k] + vel[k] * dt for k in range(3)]
                    if math.dist(cand, pred) <= REFRESH_GATE_M:
                        gate = "window"
                if gate is not None:
                    pos = cand
                    fresh = True
                    self._last_pos = pos
                    self._last_fresh_sim = t
                    self._issued.append((t, pos))
                    self.n_fresh += 1
                    lo = t - VEL_WINDOW_S - 0.5
                    if len(self._issued) > 4 and self._issued[0][0] < lo:
                        self._issued = [s for s in self._issued if s[0] >= lo]
        if self._log:
            self._log.write(json.dumps({
                "t_frame": round(t, 4), "wall": round(time.monotonic(), 4),
                "box": ([round(box.cx, 4), round(box.cy, 4), round(box.w, 4), round(box.h, 4)]
                        if box else None),
                "conf": (round(box.conf, 4) if box and box.conf is not None else None),
                "mti_ok": mti_ok, "ev": ev, "locked": self.channel.locked, "fresh": fresh,
                "gate": gate,
                "own_pos_ned": ([round(x, 4) for x in self._own[1]] if self._own else None),
                "own_q": ([round(x, 6) for x in self._own[2]] if self._own else None),
                "trk_pos_ned": ([round(x, 4) for x in pos] if pos else None)}) + "\n")
            self._log.flush()
        return ev

    def _trk_vel(self, sim_now):
        lo = sim_now - VEL_WINDOW_S
        win = [(t, p) for (t, p) in self._issued if t >= lo]
        if len(win) < 2:
            return [0.0, 0.0, 0.0]
        ts = [t for t, _ in win]
        return [_slope(ts, [p[k] for _, p in win]) for k in range(3)]

    # --- kontrakt R1 ----------------------------------------------------------
    def sample(self, sim_now):
        """Ten sam kształt co FeedB._out (track_feed.py:74-78). valid = lock kanału ∧ istnieje
        pozycja; hold-last z rosnącym age (konsument tnie na age>1.0 s — nie naśladujemy go tu)."""
        pos = self._last_pos
        valid = bool(self.channel.locked and pos is not None)
        age = (sim_now - self._last_fresh_sim) if self._last_fresh_sim is not None else 1e9
        return {"trk_pos_ned": [round(pos[0], 4), round(pos[1], 4), round(pos[2], 4)] if pos else [0.0, 0.0, 0.0],
                "trk_vel_ned": [round(v, 4) for v in self._trk_vel(sim_now)],
                "track_age_s": round(age, 4), "track_valid": valid,
                "feed_sha": self.feed_sha}

    def close(self):
        if self._log:
            self._log.close()
            self._log = None


class FeedVisionLive(FeedVision):
    """Tryb LIVE: własny węzeł ROS2 + spin-thread (daemon) — zero dotykania pętli bench_flight.
    Subskrypcje (WYŁĄCZNIE pokład): Image (zbridżowany topic kamery mono, BEST_EFFORT — lekcja
    R0.1), /fmu/out/vehicle_local_position (EKF), /fmu/out/vehicle_attitude (quat FRD→NED).
    sim-time klatki ze stempla header.stamp (most gz stempluje czasem symulacji)."""

    def __init__(self, image_topic=None, detector=None, log_path=None, node_name="feed_v"):
        super().__init__(detector=detector or YoloDetector(), log_path=log_path)
        self.image_topic = image_topic or os.environ.get("FEED_V_TOPIC") \
            or os.environ.get("LIVE_DETECTOR_TOPIC")
        if not self.image_topic:
            raise RuntimeError("[feed_vision] brak topicu kamery (FEED_V_TOPIC/LIVE_DETECTOR_TOPIC)")
        import threading
        import rclpy
        from rclpy.node import Node as RosNode
        from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
        from sensor_msgs.msg import Image
        from px4_msgs.msg import VehicleLocalPosition, VehicleAttitude
        from r02.detector_node import imgmsg_to_mono, qos_be        # READ-ONLY import (PRE §6)
        self._imgmsg_to_mono = imgmsg_to_mono
        if not rclpy.ok():
            rclpy.init()
        self._node = RosNode(node_name)
        qos = QoSProfile(depth=1, history=HistoryPolicy.KEEP_LAST,
                         reliability=ReliabilityPolicy.BEST_EFFORT)
        self._pos = None                 # ostatni VehicleLocalPosition (EKF pokładowy)
        self._q = None                   # ostatni quat [w,x,y,z]
        self._node.create_subscription(VehicleLocalPosition, "/fmu/out/vehicle_local_position",
                                       self._on_pos, qos)
        self._node.create_subscription(VehicleAttitude, "/fmu/out/vehicle_attitude",
                                       self._on_att, qos)
        self._node.create_subscription(Image, self.image_topic, self._on_image, qos_be())
        # ANEKS_2A-3 N3-C: DEDYKOWANY egzekutor dla węzła feedu. rclpy.spin_once(node)
        # używa egzekutora GLOBALNEGO, który w bench_flight już spinuje wątek EKF
        # (bench_flight.py:248-251) ⇒ 'Executor is already spinning' i śmierć wątku _spin
        # pierwszym wywołaniem (boot C1 sondy, RAPORT_2A_S3 §2b; repro probeC_repro_executor).
        from rclpy.executors import SingleThreadedExecutor
        self._ex = SingleThreadedExecutor()
        self._ex.add_node(self._node)
        self._running = True
        self._th = threading.Thread(target=self._spin, daemon=True)
        self._th.start()

    def _spin(self):
        import rclpy
        while self._running and rclpy.ok():
            self._ex.spin_once(timeout_sec=0.05)

    def _on_pos(self, m):
        self._pos = [float(m.x), float(m.y), float(m.z)]
        self._sync_own(m.timestamp / 1e6)

    def _on_att(self, m):
        self._q = [float(m.q[0]), float(m.q[1]), float(m.q[2]), float(m.q[3])]
        self._sync_own(m.timestamp / 1e6)

    def _sync_own(self, t):
        if self._pos is not None and self._q is not None:
            self.push_own(t, self._pos, self._q)

    def _on_image(self, msg):
        sim = msg.header.stamp.sec + msg.header.stamp.nanosec / 1e9
        self.push_frame(sim, self._imgmsg_to_mono(msg))

    def close(self):
        self._running = False
        super().close()
