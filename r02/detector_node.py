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

from r02.config_r02 import IMG_W, IMG_H, DET_HZ, ChannelConfig
from r02.target_channel import TargetChannel, Box, EV_ENTRY

WEIGHTS = os.environ.get("YOLO_WEIGHTS", ".b0deps/weights/yolov8s-worldv2.pt")
CH_TOPIC = "/liquidpatrol/target_channel"
DBG_TOPIC = "/liquidpatrol/detector_debug"


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
        self.channel = TargetChannel(ChannelConfig())
        self.conf_floor = conf_floor
        self.imgsz = imgsz
        self.last_frame = None
        self.frame_stamp = None
        self.t0 = None
        # detektor (fingerprint B0)
        from ultralytics import YOLO
        self.model = YOLO(WEIGHTS)
        self.model.set_classes(["drone"])
        self.get_logger().info(f"detektor: {WEIGHTS} set_classes(['drone']) imgsz={imgsz} conf_floor={conf_floor}")
        self.sub = self.create_subscription(Image, image_topic, self._on_image, qos_be())
        self.pub_ch = self.create_publisher(Float32MultiArray, CH_TOPIC, 10)
        self.pub_dbg = self.create_publisher(Float32MultiArray, DBG_TOPIC, 10)
        self.timer = self.create_timer(1.0 / det_hz, self._on_tick)   # kadencja detektora 1 Hz
        self.get_logger().info(f"sub={image_topic} pub={CH_TOPIC} @ {det_hz} Hz")

    def _on_image(self, msg):
        self.last_frame = imgmsg_to_mono(msg)
        self.frame_stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9

    def _sim_t(self):
        # sim-time z nagłówka klatki (spójne z zegarem symu / determinizmem aktora)
        return self.frame_stamp if self.frame_stamp is not None else time.monotonic()

    def _detect_top1(self, frame):
        """Zwraca (Box|None). Top-1 box po AREA? NIE — po conf top-1 (najpewniejszy),
        ALE conf NIE bramkuje publikacji ani nie wchodzi do kanału (A1/D1): conf_floor bardzo niski,
        wybieramy 1 box o najwyższym conf, conf ląduje wyłącznie w debug/log."""
        img3 = np.stack([frame] * 3, axis=-1)   # mono→3ch (jak B0)
        res = self.model.predict(img3, imgsz=self.imgsz, conf=self.conf_floor, verbose=False)[0]
        if res.boxes is None or len(res.boxes) == 0:
            return None, 0, None
        xywhn = res.boxes.xywhn.cpu().numpy()    # [cx,cy,w,h] znormalizowane
        confs = res.boxes.conf.cpu().numpy()
        i = int(np.argmax(confs))                # top-1 = najwyższy conf (conf tylko do wyboru+log)
        cx, cy, w, h = [float(v) for v in xywhn[i]]
        return Box(cx, cy, w, h, conf=float(confs[i])), len(confs), float(confs[i])

    def _on_tick(self):
        if self.last_frame is None:
            return
        if self.t0 is None:
            self.t0 = self._sim_t()
        t = self._sim_t()
        box, nbox, conf_top1 = self._detect_top1(self.last_frame)
        ev = self.channel.on_frame(box, t)       # zasila ZOH-age (ENTRY k=3, sufit θ_age)
        val = self.channel.sample(t)
        # publikacja kanału 5-dim (BEZ conf) — pusty gdy brak locka
        m = Float32MultiArray()
        m.data = list(val.as_tuple()) if val is not None else []
        self.pub_ch.publish(m)
        # debug/telemetria (conf ŻYJE TYLKO TU — nigdy w kanale)
        dbg = Float32MultiArray()
        dbg.data = [float(nbox), float(conf_top1 or 0.0), 1.0 if ev == EV_ENTRY else 0.0,
                    1.0 if self.channel.locked else 0.0]
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
