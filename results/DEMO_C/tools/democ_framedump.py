#!/usr/bin/env python3
"""results/DEMO_C/tools/democ_framedump.py — zrzutnik klatek do jpg (PROMPT_DEMO_C §3.1/§3.3).

Mechanizm 1:1 z results/DEMO_V3/tools/film_recorder.py (subskrybent zbridżowanego
sensor_msgs/Image BEST_EFFORT, decymacja WEDŁUG STEMPLA SIM — header.stamp; jeden
proces, zero churnu subprocess), zmiany WYŁĄCZNIE: zapis JPG (q=90) zamiast .npy
(dyski; percepcja NIETKNIĘTA — to osobny subskrybent obok percep, objęty profilem
FastDDS przez env FASTRTPS_DEFAULT_PROFILES_FILE od wołającego) + obsługa mono8.
Wyjście: <out>/frames/f_<sim:012.3f>.jpg + <out>/frames_index.jsonl (sim, wall, shape).

Użycie: democ_framedump.py <topic> <outdir> [fps=0=wszystkie] [max_s=1800]
Stop: SIGTERM/SIGINT albo max_s.
"""
import json
import os
import signal
import sys
import time

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image


class Dumper(Node):
    def __init__(self, topic, outdir, fps):
        super().__init__("democ_framedump")
        self.dir = os.path.join(outdir, "frames")
        os.makedirs(self.dir, exist_ok=True)
        self.idx = open(os.path.join(outdir, "frames_index.jsonl"), "w")
        self.min_dt = (1.0 / fps) if fps > 0 else 0.0
        self.last = -1e9
        self.n = 0
        qos = QoSProfile(depth=5, history=HistoryPolicy.KEEP_LAST,
                         reliability=ReliabilityPolicy.BEST_EFFORT)
        self.create_subscription(Image, topic, self.cb, qos)

    def cb(self, msg):
        sim = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        if sim - self.last < self.min_dt:
            return
        self.last = sim
        h, w = msg.height, msg.width
        buf = np.frombuffer(bytes(msg.data), dtype=np.uint8)
        enc = msg.encoding.lower()
        if enc.startswith("mono") or enc == "8uc1":
            img = buf.reshape(h, w)
        elif enc in ("rgb8",):
            img = cv2.cvtColor(buf.reshape(h, w, 3), cv2.COLOR_RGB2BGR)
        elif enc in ("bgr8",):
            img = buf.reshape(h, w, 3)
        else:
            return
        fn = f"f_{sim:012.3f}.jpg"
        cv2.imwrite(os.path.join(self.dir, fn), img, [cv2.IMWRITE_JPEG_QUALITY, 90])
        self.idx.write(json.dumps({"f": fn, "sim": round(sim, 4),
                                   "wall": round(time.monotonic(), 3),
                                   "shape": [h, w]}) + "\n")
        self.n += 1
        if self.n % 300 == 0:
            self.idx.flush()


def main():
    topic = sys.argv[1]
    outdir = sys.argv[2]
    fps = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
    max_s = float(sys.argv[4]) if len(sys.argv) > 4 else 1800.0
    stop = [False]
    signal.signal(signal.SIGTERM, lambda *_: stop.__setitem__(0, True))
    signal.signal(signal.SIGINT, lambda *_: stop.__setitem__(0, True))
    rclpy.init()
    node = Dumper(topic, outdir, fps)
    t0 = time.monotonic()
    while not stop[0] and rclpy.ok() and time.monotonic() - t0 < max_s:
        rclpy.spin_once(node, timeout_sec=0.1)
    node.idx.flush()
    node.idx.close()
    print(f"[framedump] zapisano {node.n} klatek → {node.dir}", flush=True)


if __name__ == "__main__":
    main()
