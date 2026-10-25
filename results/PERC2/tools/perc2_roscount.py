#!/usr/bin/env python3
"""results/PERC2/tools/perc2_roscount.py — licznik klatek po stronie ROS (za mostem),
ZERO pracy GPU/percepcji: subskrybuje topic obrazu z QoS jak percep (BEST_EFFORT,
KEEP_LAST, --depth) i liczy stemple. Rozstrzyga, czy stratę klatek robi most/DDS
(tu już rzadkie), czy odbiór+praca percep (tu gęste, w percep rzadkie).
Czysty ops (rclpy to infrastruktura transportu, nie tor percepcji).
"""
import argparse
import json
import time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", required=True)
    ap.add_argument("--window", type=float, default=35.0)
    ap.add_argument("--depth", type=int, default=1)
    ap.add_argument("--busy-ms", type=float, default=0.0,
                    help="sztuczne zajęcie callbacku [ms] (emulacja kosztu percep)")
    ap.add_argument("--out")
    ap.add_argument("--label", default="")
    a = ap.parse_args()

    import rclpy
    from rclpy.node import Node
    from rclpy.executors import SingleThreadedExecutor
    from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
    from sensor_msgs.msg import Image

    stamps = []

    def cb(msg):
        stamps.append(msg.header.stamp.sec + msg.header.stamp.nanosec / 1e9)
        if a.busy_ms > 0:
            t0 = time.monotonic()
            while (time.monotonic() - t0) * 1000.0 < a.busy_ms:
                pass

    rclpy.init()
    node = Node("perc2_roscount")
    qos = QoSProfile(depth=a.depth, history=HistoryPolicy.KEEP_LAST,
                     reliability=ReliabilityPolicy.BEST_EFFORT)
    node.create_subscription(Image, a.topic, cb, qos)
    ex = SingleThreadedExecutor()
    ex.add_node(node)
    t_end = time.monotonic() + a.window
    while time.monotonic() < t_end:
        ex.spin_once(timeout_sec=0.05)
    node.destroy_node()
    rclpy.shutdown()

    d = [stamps[i] - stamps[i - 1] for i in range(1, len(stamps))
         if 0 < stamps[i] - stamps[i - 1] <= 2.0]

    def p(xs, q):
        if not xs:
            return None
        s = sorted(xs)
        return round(s[min(len(s) - 1, int(q * (len(s) - 1)))], 4)

    res = {"label": a.label, "depth": a.depth, "busy_ms": a.busy_ms,
           "window_s": a.window, "n_frames": len(stamps),
           "dt_sim_p50": p(d, 0.5), "dt_sim_p90": p(d, 0.9),
           "frac_gt_0p10": (round(sum(1 for x in d if x > 0.10) / len(d), 4) if d else None),
           "hz_p50": (round(1.0 / p(d, 0.5), 2) if d else None)}
    print(json.dumps(res))
    if a.out:
        json.dump(res, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
