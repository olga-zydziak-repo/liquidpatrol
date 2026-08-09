#!/usr/bin/env python3
"""
B1-bis rejestrator (kanał GT STREAMING, R-2 / §3bis).
  EKF: /fmu/out/vehicle_local_position (rclpy, px4_msgs) — NED, etykieta nav-local.
       loguje px4 timestamp (ts, sek), reset countery (R-1), eph, dead_reckoning.
  GT : /world/<world>/dynamic_pose/info (gz.transport13, gz.msgs10 Pose_V) — ENU, gt_judge.
       stempel SIM u źródła (header.stamp), pozycja modelu x500 w świecie.
Obie próbki + mono (odbiór) + native stamp. Parowanie po sim-time (gross offset + skew) w gt_judge.
Bez subprocessu gz model -p (usunięto skew latencji stempla).
"""
import os, json, time, threading
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from px4_msgs.msg import VehicleLocalPosition
from gz.transport13 import Node as GzNode
from gz.msgs10.pose_v_pb2 import Pose_V

QOS = QoSProfile(depth=1, history=HistoryPolicy.KEEP_LAST, reliability=ReliabilityPolicy.BEST_EFFORT)
OUT   = os.environ.get("B1_OUT", "/tmp/r03bbis/rec.jsonl")
DUR   = float(os.environ.get("B1_DUR", "150"))
WORLD = os.environ.get("PX4_GZ_WORLD", "default")
MODEL = os.environ.get("B1_MODEL", "x500_mono_cam_0")
GT_TOPIC = f"/world/{WORLD}/dynamic_pose/info"
GT_HZ = float(os.environ.get("B1_GT_HZ", "50"))   # throttle GT do ~50 Hz

_lock = threading.Lock()
_f = None
_running = False
_gt_last = [0.0]
_gt_min_dt = 1.0 / GT_HZ
_counts = {"ekf": 0, "gt": 0}


def _write(row):
    with _lock:
        if _f is None or not _running:
            return
        _f.write(json.dumps(row) + "\n")


def gt_cb(msg):
    # throttle po mono odbioru
    now = time.monotonic()
    if now - _gt_last[0] < _gt_min_dt:
        return
    for p in msg.pose:
        if p.name == MODEL:
            sim = msg.header.stamp.sec + msg.header.stamp.nsec / 1e9
            _write({"t": "gt", "mono": round(now, 4), "sim": round(sim, 4),
                    "x": round(p.position.x, 5), "y": round(p.position.y, 5),
                    "z": round(p.position.z, 5)})
            _gt_last[0] = now
            _counts["gt"] += 1
            return


class Rec(Node):
    def __init__(self):
        super().__init__("b1bis_rec")
        self._n = 0
        self.create_subscription(VehicleLocalPosition, "/fmu/out/vehicle_local_position", self.vlp, QOS)

    def vlp(self, m):
        self._n += 1
        if self._n % 5:   # ~100 Hz -> ~20 Hz
            return
        _write({"t": "ekf", "mono": round(time.monotonic(), 4), "ts": round(m.timestamp / 1e6, 4),
                "x": round(float(m.x), 4), "y": round(float(m.y), 4), "z": round(float(m.z), 4),
                "eph": round(float(m.eph), 4), "dead_reckoning": bool(m.dead_reckoning),
                "xy_valid": bool(m.xy_valid),
                "xy_reset_counter": int(m.xy_reset_counter), "z_reset_counter": int(m.z_reset_counter)})
        _counts["ekf"] += 1


def main():
    global _f, _running
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    gn = GzNode()
    rclpy.init()
    with open(OUT, "w") as f:
        _f = f
        _running = True
        _write({"t": "meta", "model": MODEL, "gt_topic": GT_TOPIC, "gt_hz": GT_HZ,
                "note": "ekf.ts=px4 sek; gt.sim=gz sim sek; parowanie po sim (gross offset+skew)"})
        if not gn.subscribe(Pose_V, GT_TOPIC, gt_cb):
            print(f"[b1bis_rec] BŁĄD subskrypcji GT {GT_TOPIC}", flush=True)
        n = Rec()
        t0 = time.monotonic()
        while rclpy.ok() and time.monotonic() - t0 < DUR:
            rclpy.spin_once(n, timeout_sec=0.02)
        with _lock:
            _running = False
        n.destroy_node()
    rclpy.shutdown()
    print(f"[b1bis_rec] done -> {OUT}  ekf={_counts['ekf']} gt={_counts['gt']}", flush=True)


if __name__ == "__main__":
    main()
