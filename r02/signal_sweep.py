#!/usr/bin/env python3
"""r02/signal_sweep.py — STATYCZNY sweep sygnału (EKSPLORACJA, krok 1 — bez lotu).

Dron stoi na ziemi w Home (kamera pozioma, Północ — zwalidowane smoke R3: intruz na +X → cx≈0.5).
Przesuwa intruza `gz set_pose` przez zasięgi 5–25 m przy stałej niskiej elewacji (~11°, geometria
smoke gdzie detektor ODPALA: intruz na tle nieba, blisko poziomu), czyta detektor: WSZYSTKIE boxy
(/detector_boxes) + top-1 conf (/detector_debug). Wynik: gęsta krzywa conf(zasięg) SYGNAŁU
(top-1 box na intruzie), obok chmury szumu z CHAR. Bez PX4 arm/lotu — tani, kontrolowany pomiar.
Uruchom (po stack+bridge+detektor): python3 -m r02.signal_sweep <world> [out.jsonl]
"""
from __future__ import annotations
import json, math, subprocess, sys, time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from std_msgs.msg import Float32MultiArray

BOXES_TOPIC = "/liquidpatrol/detector_boxes"
CAM_H = 0.4                      # wys. kamery drona na ziemi (x500 ~0.18 + mount 0.242)
ELEV_DEG = 11.0                 # elewacja intruza (geometria smoke: (8,0,2) → ~11°, detektor odpala)
RANGES = [5, 7, 9, 11, 13, 15, 18, 21, 24]   # zasięgi poziome [m]
DWELL_S = 5.0                   # dwell per zasięg (≥4 klatki detektora @1 Hz)


def set_pose(world, x, y, z):
    req = f'name: "intruder", position: {{x: {x}, y: {y}, z: {z}}}, orientation: {{w: 1.0}}'
    subprocess.run(["gz", "service", "-s", f"/world/{world}/set_pose", "--reqtype", "gz.msgs.Pose",
                    "--reptype", "gz.msgs.Boolean", "--timeout", "3000", "--req", req],
                   capture_output=True, text=True, timeout=6)


class Sweeper(Node):
    def __init__(self):
        super().__init__("signal_sweep")
        self.boxes = []; self.seq = 0
        qos = QoSProfile(depth=1, history=HistoryPolicy.KEEP_LAST, reliability=ReliabilityPolicy.BEST_EFFORT)
        self.create_subscription(Float32MultiArray, BOXES_TOPIC, self._cb, qos)

    def _cb(self, msg):
        d = list(msg.data)
        if d and len(d) > 1:
            flat = d[:-1]
            self.boxes = [tuple(flat[i:i+5]) for i in range(0, len(flat)-4, 5)]
        else:
            self.boxes = []
        self.seq += 1

    def spin_for(self, secs):
        t = time.time()
        while time.time() - t < secs:
            rclpy.spin_once(self, timeout_sec=0.2)


def main():
    world = sys.argv[1] if len(sys.argv) > 1 else "default"
    out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/r02/SWEEP/sweep.jsonl"
    rclpy.init(); node = Sweeper()
    outf = open(out, "w")
    tan_e = math.tan(math.radians(ELEV_DEG))
    for R in RANGES:
        z = CAM_H + R * tan_e                        # elewacja stała → intruz na tle nieba
        set_pose(world, float(R), 0.0, float(z))
        # oczekiwany piksel: cx≈0.5 (na wprost), cy ≈ upper-center (elewacja w górę)
        t0 = time.time(); last = -1
        while time.time() - t0 < DWELL_S:
            node.spin_for(0.3)
            if node.seq != last:
                last = node.seq
                boxes = sorted(node.boxes, key=lambda b: -b[4])   # po conf malejąco
                # kandydat na intruza = box najbliżej cx=0.5 wśród 3 najpewniejszych (na wprost)
                cand = None
                for b in boxes[:3]:
                    if 0.3 <= b[0] <= 0.7:                        # centralny poziomo (dead-ahead)
                        cand = b; break
                top1 = boxes[0] if boxes else None
                rec = {"range": R, "z": round(z, 2), "nbox": len(boxes),
                       "top1_conf": round(top1[4], 5) if top1 else 0.0,
                       "top1_cx": round(top1[0], 4) if top1 else None,
                       "cand_conf": round(cand[4], 5) if cand else None,
                       "cand_cx": round(cand[0], 4) if cand else None,
                       "cand_cy": round(cand[1], 4) if cand else None,
                       "cand_edge": round(min(cand[0], 1-cand[0], cand[1], 1-cand[1]), 4) if cand else None}
                outf.write(json.dumps(rec) + "\n"); outf.flush()
                print(json.dumps(rec, ensure_ascii=False))
    outf.close(); node.destroy_node(); rclpy.shutdown()


if __name__ == "__main__":
    main()
