#!/usr/bin/env python3
"""r02/detector_node.py — WĘZEŁ DETEKTORA ROS2 (R3, PRE_R02 §2.3).

Subskrybuje obraz kamery (sensor_msgs/Image, mono 320×240, BEST_EFFORT — lekcja R0.1: reliable
dławi), uruchamia detektor uczony (YOLO-World `yolov8s-worldv2`, fingerprint z RAPORT_B0), bierze
**top-1 box BEZ bramkowania conf** (R02-A1/D1 — conf tylko do logu/telemetrii), zasila kanał
`TargetChannel` (ZOH-age, ENTRY k=3, sufit θ_age) i **publikuje kanał 5-dim** `(cx,cy,w,h,age)`
jako `std_msgs/Float32MultiArray` @1 Hz do osłony/planera. Setpointy dalej TYLKO XRCE przez osłonę
(niezmiennik A1 — węzeł detektora NIC nie publikuje do /fmu/in/*).

Topiki:
  sub  <image_topic>                      sensor_msgs/Image (BEST_EFFORT)
  pub  /liquidpatrol/target_channel        Float32MultiArray [cx,cy,w,h,age]  (locked) | [] (brak locka)
  pub  /liquidpatrol/detector_debug        Float32MultiArray [n_box, conf_top1, entry(0/1), locked]

Uruchom (env złożony ROS2+torch): patrz r02/run_detector.sh
"""
from __future__ import annotations
import argparse, os, sys, time

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image
from std_msgs.msg import Float32MultiArray

from dataclasses import replace
from r02.config_r02 import IMG_W, IMG_H, DET_HZ, ChannelConfig, MTI_CENTER_THR
from r02.target_channel import TargetChannel, Box, EV_ENTRY

# DEMO-B B5P (ANEKS_D5 ratyfikowane): brama LIVE = struktura∧MTI (jak REGATE), gdy DEMO_MTI=1.
# Bez flagi: zachowanie domyślne (conf-floor) dla charakteryzacji. Zero zmiany PROGÓW (MTI_CENTER_THR,
# θ_conf, k) — to charakteryzacja frozen; zmienia się WYŁĄCZNIE aktywna brama.
DEMO_MTI = os.environ.get("DEMO_MTI") == "1"

WEIGHTS = os.environ.get("YOLO_WEIGHTS", ".b0deps/weights/yolov8s-worldv2.pt")
CH_TOPIC = "/liquidpatrol/target_channel"
DBG_TOPIC = "/liquidpatrol/detector_debug"
BOXES_TOPIC = "/liquidpatrol/detector_boxes"     # EKSPLORACJA: wszystkie boxy (poza torem osłony)


def qos_be():
    return QoSProfile(depth=1, history=HistoryPolicy.KEEP_LAST, reliability=ReliabilityPolicy.BEST_EFFORT)


def imgmsg_to_mono(msg) -> np.ndarray:
    """sensor_msgs/Image → HxW mono uint8 (obsługa mono8/rgb8/bgr8). Bez cv_bridge (lżej)."""
    h, w = msg.height, msg.width
    buf = np.frombuffer(bytes(msg.data), dtype=np.uint8)
    enc = msg.encoding.lower()
    if enc in ("mono8", "8uc1"):
        return buf.reshape(h, w)
    if enc in ("rgb8", "bgr8"):
        return buf.reshape(h, w, 3).mean(axis=2).astype(np.uint8)
    # fallback: przytnij do h*w
    return buf[:h * w].reshape(h, w)


class DetectorNode(Node):
    def __init__(self, image_topic, det_hz=DET_HZ, conf_floor=0.001, imgsz=640):
        super().__init__("liquidpatrol_detector")
        cfg = replace(ChannelConfig(), entry_require_mti=True) if DEMO_MTI else ChannelConfig()
        self.channel = TargetChannel(cfg)
        self.conf_floor = conf_floor
        self.imgsz = imgsz
        self.last_frame = None
        self.frame_stamp = None
        self.t0 = None
        # DEMO_MTI: tracker MTI (derotacja z vehicle_attitude) + koincydencja box↔komponent (mti_ok)
        self.demo_mti = DEMO_MTI
        self.tracker = None; self.q = None; self.last_comps = []
        if self.demo_mti:
            from r02.mti import MTITracker, MTIParams
            self._box_matches = __import__("r02.mti", fromlist=["box_matches_component"]).box_matches_component
            self.tracker = MTITracker(MTIParams(), delta=3)
            from px4_msgs.msg import VehicleAttitude
            self.create_subscription(VehicleAttitude, "/fmu/out/vehicle_attitude", self._att, qos_be())
            self.get_logger().info("DEMO_MTI=1: brama struktura∧MTI (entry_require_mti=True, conf pasywne)")
        # detektor (fingerprint B0)
        from ultralytics import YOLO
        self.model = YOLO(WEIGHTS)
        self.model.set_classes(["drone"])
        self.get_logger().info(f"detektor: {WEIGHTS} set_classes(['drone']) imgsz={imgsz} conf_floor={conf_floor}")
        self.sub = self.create_subscription(Image, image_topic, self._on_image, qos_be())
        self.pub_ch = self.create_publisher(Float32MultiArray, CH_TOPIC, 10)
        self.pub_dbg = self.create_publisher(Float32MultiArray, DBG_TOPIC, 10)
        # EKSPLORACJA (charakteryzacja): WSZYSTKIE boxy [cx,cy,w,h,conf]*n spłaszczone. Poza torem
        # decyzyjnym (osłona NIE subskrybuje) — tylko do pomiaru rozkładu conf/przestrzennego.
        self.pub_boxes = self.create_publisher(Float32MultiArray, BOXES_TOPIC, 10)
        self.timer = self.create_timer(1.0 / det_hz, self._on_tick)   # kadencja detektora 1 Hz
        self.get_logger().info(f"sub={image_topic} pub={CH_TOPIC} @ {det_hz} Hz")

    def _on_image(self, msg):
        self.last_frame = imgmsg_to_mono(msg)
        self.frame_stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        # MTI PRZY PEŁNEJ KADENCJI KLATEK (~15 Hz, jak REGATE mti_flight; delta=3 → baseline ~200 ms).
        # YOLO/kanał zostają 1 Hz (_on_tick), ale derotacja-residuum MUSI iść z częstotliwością klatek —
        # przy 1 Hz baseline ~3 s aliasuje z oscylacją 0.3 Hz (n_comps≈0). Push tu, box↔comp match w tiku.
        if self.demo_mti and self.q is not None:
            try:
                self.last_comps, _ = self.tracker.push(self.last_frame, self.q)
            except Exception:
                self.last_comps = []

    def _att(self, m):
        self.q = [float(m.q[0]), float(m.q[1]), float(m.q[2]), float(m.q[3])]   # [w,x,y,z]

    def _sim_t(self):
        # sim-time z nagłówka klatki (spójne z zegarem symu / determinizmem aktora)
        return self.frame_stamp if self.frame_stamp is not None else time.monotonic()

    def _detect(self, frame):
        """Zwraca (top1_box|None, all_boxes, nbox). all_boxes = lista (cx,cy,w,h,conf) posortowana
        malejąco po conf. Top-1 = najwyższy conf (conf tylko do wyboru+log, NIE do kanału — A1/D1)."""
        img3 = np.stack([frame] * 3, axis=-1)   # mono→3ch (jak B0)
        res = self.model.predict(img3, imgsz=self.imgsz, conf=self.conf_floor, verbose=False)[0]
        if res.boxes is None or len(res.boxes) == 0:
            return None, [], 0
        xywhn = res.boxes.xywhn.cpu().numpy()    # [cx,cy,w,h] znormalizowane
        confs = res.boxes.conf.cpu().numpy()
        order = np.argsort(-confs)               # malejąco po conf
        allb = [(float(xywhn[j][0]), float(xywhn[j][1]), float(xywhn[j][2]), float(xywhn[j][3]),
                 float(confs[j])) for j in order]
        top = allb[0]
        return Box(top[0], top[1], top[2], top[3], conf=top[4]), allb, len(allb)

    def _on_tick(self):
        if self.last_frame is None:
            return
        if self.t0 is None:
            self.t0 = self._sim_t()
        t = self._sim_t()
        box, allb, nbox = self._detect(self.last_frame)
        conf_top1 = box.conf if box is not None else None
        # DEMO_MTI: derotacja (MTITracker push frame+q) → komponenty ruchu → mti_ok = koincydencja box↔comp
        mti_ok = None; n_comps = 0
        if self.demo_mti:
            comps = self.last_comps                              # komponenty z toru 15 Hz (_on_image)
            n_comps = len(comps)
            mti_ok = self._box_matches(box, comps, MTI_CENTER_THR) if box is not None else False
            ev = self.channel.on_frame(box, t, mti_ok=mti_ok)   # brama struktura∧MTI (conf pasywne)
        else:
            ev = self.channel.on_frame(box, t)   # zasila ZOH-age (ENTRY k=3, sufit θ_age) — conf-floor
        val = self.channel.sample(t)
        # publikacja kanału 5-dim (BEZ conf) — pusty gdy brak locka
        m = Float32MultiArray()
        m.data = list(val.as_tuple()) if val is not None else []
        self.pub_ch.publish(m)
        # EKSPLORACJA: wszystkie boxy [cx,cy,w,h,conf]*n + sim_t na końcu (poza torem osłony)
        bm = Float32MultiArray()
        flat = [v for b in allb for v in b]
        bm.data = flat + [float(t)]
        self.pub_boxes.publish(bm)
        # debug/telemetria (conf ŻYJE TYLKO TU — nigdy w kanale)
        dbg = Float32MultiArray()
        dbg.data = [float(nbox), float(conf_top1 or 0.0), 1.0 if ev == EV_ENTRY else 0.0,
                    1.0 if self.channel.locked else 0.0,
                    (1.0 if mti_ok else 0.0) if mti_ok is not None else -1.0,  # -1 = MTI nieaktywne
                    float(n_comps)]
        self.pub_dbg.publish(dbg)
        if ev == EV_ENTRY:
            self.get_logger().info(f"ENTRY @ sim_t={t:.2f} box={m.data}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image-topic", required=True)
    ap.add_argument("--det-hz", type=float, default=DET_HZ)
    ap.add_argument("--imgsz", type=int, default=640)
    args, _ = ap.parse_known_args()
    rclpy.init()
    node = DetectorNode(args.image_topic, det_hz=args.det_hz, imgsz=args.imgsz)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
