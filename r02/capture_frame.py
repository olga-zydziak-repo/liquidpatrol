#!/usr/bin/env python3
"""r02/capture_frame.py — przechwyt N klatek z mostkowanej kamery (rclpy, R1 weryfikacja widoczności).

Subskrybuje sensor_msgs/Image (BEST_EFFORT — lekcja R0.1), zapisuje ostatnią klatkę jako .npy.
Uruchom pod zsourcowanym ROS: python3 -m r02.capture_frame <topic> <out.npy> [n_wait_s]
"""
import sys
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image


class Grab(Node):
    def __init__(self, topic, out):
        super().__init__("r02_capture")
        self.out = out
        self.frame = None
        qos = QoSProfile(depth=5, history=HistoryPolicy.KEEP_LAST,
                         reliability=ReliabilityPolicy.BEST_EFFORT)
        self.create_subscription(Image, topic, self.cb, qos)

    def cb(self, msg):
        h, w = msg.height, msg.width
        buf = np.frombuffer(bytes(msg.data), dtype=np.uint8)
        ch = len(buf) // (h * w) if h * w else 1
        self.frame = buf.reshape(h, w, ch) if ch > 1 else buf.reshape(h, w)
        self.enc = msg.encoding


def main():
    topic = sys.argv[1]
    out = sys.argv[2]
    wait_s = float(sys.argv[3]) if len(sys.argv) > 3 else 8.0
    rclpy.init()
    node = Grab(topic, out)
    t = 0.0
    while rclpy.ok() and node.frame is None and t < wait_s:
        rclpy.spin_once(node, timeout_sec=0.2)
        t += 0.2
    if node.frame is None:
        print(f"[capture] BRAK klatki z {topic} w {wait_s}s", file=sys.stderr)
        rclpy.shutdown()
        sys.exit(2)
    np.save(out, node.frame)
    print(f"[capture] zapisano {out} shape={node.frame.shape} enc={node.enc} "
          f"min={int(node.frame.min())} max={int(node.frame.max())} mean={float(node.frame.mean()):.1f}")
    rclpy.shutdown()


if __name__ == "__main__":
    main()
