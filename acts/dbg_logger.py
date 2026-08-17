#!/usr/bin/env python3
"""acts/dbg_logger.py — DEMO-B B5P P0/P1: loguje DBG detektora LIVE (co patch (b) daje w GT-fed, ale w
LIVE żyje w OSOBNYM procesie detector_node). Subskrybuje /liquidpatrol/detector_debug
`[n_box, conf_top1, entry, locked]` (+ opcj. /liquidpatrol/detector_boxes) i zapisuje jsonl z recv-time.

Rozstrzyga gałąź P0 dla LIVE: n_box=0 przez ring ⇒ YOLO nie widzi celu (P1); n_box>0 ale conf<θ_conf
(≈0.1635) ⇒ conf-floor odrzuca (P2/conf); entry pojawia się ⇒ lock powinien być (wtedy wiring do gate).
SONDA (SR-J2, probe_*): NIE próba, werdykt percepcji nieraportowalny jako wynik aktu.

Uruchom (pod ROS): python3 acts/dbg_logger.py <out.jsonl> [seconds]
"""
import json
import sys
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from std_msgs.msg import Float32MultiArray

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/dbg.jsonl"
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 80.0


def qos_be():
    return QoSProfile(depth=10, history=HistoryPolicy.KEEP_LAST, reliability=ReliabilityPolicy.BEST_EFFORT)


class DbgLog(Node):
    def __init__(self, f):
        super().__init__("dbg_logger")
        self.f = f
        self.create_subscription(Float32MultiArray, "/liquidpatrol/detector_debug", self._dbg, qos_be())
        self.create_subscription(Float32MultiArray, "/liquidpatrol/target_channel", self._ch, qos_be())
        self.t0 = time.monotonic()

    def _dbg(self, m):
        d = list(m.data)
        rec = {"t": round(time.monotonic() - self.t0, 3), "topic": "dbg",
               "n_box": d[0] if len(d) > 0 else None, "conf_top1": d[1] if len(d) > 1 else None,
               "entry": d[2] if len(d) > 2 else None, "locked": d[3] if len(d) > 3 else None,
               "mti_ok": d[4] if len(d) > 4 else None, "n_comps": d[5] if len(d) > 5 else None}
        self.f.write(json.dumps(rec) + "\n"); self.f.flush()

    def _ch(self, m):
        d = list(m.data)
        rec = {"t": round(time.monotonic() - self.t0, 3), "topic": "channel",
               "empty": (len(d) == 0), "val": d}
        self.f.write(json.dumps(rec) + "\n"); self.f.flush()


def main():
    rclpy.init()
    f = open(OUT, "w")
    node = DbgLog(f)
    t0 = time.monotonic()
    while time.monotonic() - t0 < DUR:
        rclpy.spin_once(node, timeout_sec=0.2)
    f.close(); node.destroy_node(); rclpy.shutdown()
    print(f"[dbg_logger] done → {OUT}")


if __name__ == "__main__":
    main()
