#!/usr/bin/env python3
"""results/DEMO_V3/tools/film_recorder.py — ciągły rejestrator klatek kamery filmowej (DEMO_V3 §3/§5).

Subskrybuje zbridżowany topic sensor_msgs/Image (BEST_EFFORT, lekcja R0.1), zapisuje klatki
zdecymowane do docelowego fps WEDŁUG STEMPLA SIM-TIME (header.stamp — gz bridge stempluje czasem
symulacji; weryfikacja stempli = 3 klatki kontrolne w raporcie). Wyjście:
  <out>/frames/f_%06d.npy  (RGB uint8)
  <out>/frames_index.jsonl (idx, sim, wall, shape) — most klatka→sim_t dla montażu real-time.
Zamiast pętli subprocess-per-klatka (capture_frame w run_act*.sh): JEDEN proces — zero churnu
(lekcja D §5c: subprocess churn łamie RTF).

Użycie: python3 film_recorder.py <topic> <outdir> [fps=8] [max_s=900]
Stop: SIGTERM/SIGINT (driver) albo max_s.
"""
import json, os, signal, sys, time

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image


class Recorder(Node):
    def __init__(self, topic, outdir, fps):
        super().__init__("demo_v3_film_recorder")
        self.dir = os.path.join(outdir, "frames"); os.makedirs(self.dir, exist_ok=True)
        self.idx_f = open(os.path.join(outdir, "frames_index.jsonl"), "w")
        self.min_dt = 1.0 / fps
        self.last_sim = -1e9
        self.n = 0
        qos = QoSProfile(depth=5, history=HistoryPolicy.KEEP_LAST,
                         reliability=ReliabilityPolicy.BEST_EFFORT)
        self.create_subscription(Image, topic, self.cb, qos)

    def cb(self, msg):
        sim = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        if sim - self.last_sim < self.min_dt:
            return
        h, w = msg.height, msg.width
        buf = np.frombuffer(bytes(msg.data), dtype=np.uint8)
        ch = len(buf) // (h * w) if h * w else 1
        fr = buf.reshape(h, w, ch) if ch > 1 else buf.reshape(h, w)
        np.save(os.path.join(self.dir, f"f_{self.n:06d}.npy"), fr)
        self.idx_f.write(json.dumps({"idx": self.n, "sim": round(sim, 4),
                                     "wall": round(time.time(), 3), "shape": list(fr.shape),
                                     "encoding": msg.encoding}) + "\n")
        self.idx_f.flush()
        self.last_sim = sim; self.n += 1


def main():
    topic, outdir = sys.argv[1], sys.argv[2]
    fps = float(sys.argv[3]) if len(sys.argv) > 3 else 8.0
    max_s = float(sys.argv[4]) if len(sys.argv) > 4 else 900.0
    rclpy.init()
    node = Recorder(topic, outdir, fps)
    stop = {"f": False}
    for s in (signal.SIGTERM, signal.SIGINT):
        signal.signal(s, lambda *_: stop.update(f=True))
    t0 = time.time()
    while not stop["f"] and time.time() - t0 < max_s:
        rclpy.spin_once(node, timeout_sec=0.2)
    node.idx_f.close()
    print(f"[film_recorder] saved n={node.n} → {node.dir}", flush=True)


if __name__ == "__main__":
    main()
