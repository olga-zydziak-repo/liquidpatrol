#!/usr/bin/env python3
"""r02/attrib_probe.py — sonda ATRYBUCYJNA (tor A, decyzja Olgi): surowa klatka + metadane + conf.

Cel: rozstrzygnąć czy 4× spadek conf (statyczny sweep 0.169 → lot 0.045) to PERCEPCJA (treść obrazu:
attitude kamery, tło, oświetlenie, azymut, rozmiar/pozycja intruza) czy POTOK (topik, rozdzielczość,
skalowanie, most vs gz-transport). Oba tory dzielą TEN SAM węzeł detektora+most → potok identyczny;
sonda przechwytuje surową klatkę z pipeline'u przy IDENTYCZNEJ pozie WZGLĘDNEJ intruza i zapisuje:
  - <prefix>.png / .npy (wizualne porównanie + pixel-diff),
  - <prefix>_meta.json: topik, width, height, encoding, step (rozdzielczość/skalowanie potoku),
  - conf top-1 z /liquidpatrol/detector_debug (percepcja: siła detekcji na tej klatce).
Uruchom (po stack+bridge+detektor): python3 -m r02.attrib_probe <image_topic> <out_prefix> [n_wait_s]
"""
from __future__ import annotations
import json, sys, time

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image
from std_msgs.msg import Float32MultiArray


def qos_be():
    return QoSProfile(depth=5, history=HistoryPolicy.KEEP_LAST, reliability=ReliabilityPolicy.BEST_EFFORT)


class Probe(Node):
    def __init__(self, image_topic):
        super().__init__("attrib_probe")
        self.frame = None; self.meta = None; self.conf = None; self.nbox = None
        self.create_subscription(Image, image_topic, self._img, qos_be())
        self.create_subscription(Float32MultiArray, "/liquidpatrol/detector_debug", self._dbg, qos_be())
        self.topic = image_topic

    def _img(self, msg):
        h, w = msg.height, msg.width
        buf = np.frombuffer(bytes(msg.data), dtype=np.uint8)
        ch = len(buf) // (h * w) if h * w else 1
        self.frame = buf.reshape(h, w, ch) if ch > 1 else buf.reshape(h, w)
        self.meta = {"topic": self.topic, "width": w, "height": h, "encoding": msg.encoding,
                     "step": msg.step, "channels": ch}

    def _dbg(self, msg):
        if msg.data and len(msg.data) >= 2:
            self.nbox = float(msg.data[0]); self.conf = float(msg.data[1])


def main():
    topic = sys.argv[1]; prefix = sys.argv[2]
    wait_s = float(sys.argv[3]) if len(sys.argv) > 3 else 12.0
    rclpy.init(); node = Probe(topic)
    t = time.time()
    while rclpy.ok() and time.time() - t < wait_s and (node.frame is None or node.conf is None):
        rclpy.spin_once(node, timeout_sec=0.2)
    if node.frame is None:
        print(json.dumps({"error": "brak klatki", "topic": topic})); rclpy.shutdown(); sys.exit(2)
    np.save(prefix + ".npy", node.frame)
    try:
        import cv2
        img = node.frame if node.frame.ndim == 3 else np.stack([node.frame] * 3, -1)
        cv2.imwrite(prefix + ".png", img)
    except Exception as e:
        print("png fail:", e)
    meta = {**(node.meta or {}), "conf_top1": node.conf, "nbox": node.nbox}
    json.dump(meta, open(prefix + "_meta.json", "w"), indent=2)
    print(json.dumps(meta, ensure_ascii=False))
    node.destroy_node(); rclpy.shutdown()


if __name__ == "__main__":
    main()
