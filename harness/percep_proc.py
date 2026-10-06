#!/usr/bin/env python3
"""harness/percep_proc.py — PROCES PERCEPCJI nogi DET (FEED=V2; PRE_DET §6, ANEKS_DET-2 §3/§4).

Osobny proces (wzór dowiedziony wykonaniem: shadow S2 E2E p95 0.044–0.052 s):
  subskrypcje POKŁADOWE (obraz zbridżowany + /fmu/out/vehicle_local_position +
  /fmu/out/vehicle_attitude) → rdzeń `harness.feed_vision.FeedVision` (acc81df7,
  READ-ONLY — TE SAME BAJTY co lot 2A i przyrząd bramki T det_replay; ZAKAZ
  reimplementacji MTI/admisji/pinhole/REFRESH/starzenia, ANEKS_DET-2 §3)
  z WSTRZYKNIĘTYM detektorem DetV2 → po każdej klatce datagram UDS (jsonl) do klienta
  FeedVisionProc w procesie ławki. Zero GT w tym procesie.

Lekcja N3-C wbudowana: świeży proces = własny kontekst rclpy; spin WYŁĄCZNIE przez
DEDYKOWANY SingleThreadedExecutor (nigdy rclpy.spin_once na egzekutorze globalnym
w obecności innych spinów).

Datagram per klatka: {"t": "s", "t_frame", "t_update_sim" (zegar sim gz w chwili
wysyłki — jak LogProxy S2), "s": feed.sample(t_frame) z feed_sha podmienionym na
feed_sha_v2, "n_frames", "n_fresh"}. Meta na starcie: {"t": "meta", ...}.
Klient liczy wiek w sim: age(sim_now) = (sim_now − t_frame) + s.track_age_s —
ta sama matematyka co FeedVision.sample (wiek od ostatniej świeżej, w sim-time);
trk_vel = ZOH z t_frame (okno linreg 1.0 s przesuwa się o ≤0.07 s między klatkami —
odchyłka pomijalna, odnotowana).

Wyjścia plikowe: --log (jsonl rdzenia FeedVision z doklejką t_update_sim — wzór
LogProxy S2) + <log>.summary.json przy SIGTERM.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

_sim = [0.0]
_stop = [False]


class LogProxy:
    """Jak results/2A/tools/shadow_feed_live.LogProxy: doklejka t_update_sim do wierszy
    loga rdzenia (kompozycja, zero edycji frozen feed_vision)."""

    def __init__(self, path):
        self._f = open(path, "w")

    def write(self, s):
        try:
            rec = json.loads(s)
            if _sim[0] > 0.0:
                rec["t_update_sim"] = round(_sim[0], 4)
            self._f.write(json.dumps(rec) + "\n")
        except (ValueError, TypeError):
            self._f.write(s)

    def write_raw(self, s):
        self._f.write(s); self._f.flush()

    def flush(self):
        self._f.flush()

    def close(self):
        self._f.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", required=True)
    ap.add_argument("--world", required=True)
    ap.add_argument("--sock", required=True, help="ścieżka UDS klienta (SOCK_DGRAM)")
    ap.add_argument("--log", required=True)
    a = ap.parse_args()

    # zegar sim gz (do t_update_sim; wzór shadow S2)
    from gz.transport13 import Node as GzNode
    from gz.msgs10.clock_pb2 import Clock
    gn = GzNode()
    gn.subscribe(Clock, f"/world/{a.world}/clock",
                 lambda m: _sim.__setitem__(0, m.sim.sec + m.sim.nsec / 1e9))

    import rclpy
    from rclpy.node import Node
    from rclpy.executors import SingleThreadedExecutor          # lekcja N3-C
    from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
    from sensor_msgs.msg import Image
    from px4_msgs.msg import VehicleLocalPosition, VehicleAttitude
    from r02.detector_node import imgmsg_to_mono, qos_be        # READ-ONLY
    from harness.feed_vision import FeedVision                  # acc81df7 READ-ONLY
    from harness.det_v2 import DetV2, feed_sha_v2

    det = DetV2()
    fsha = feed_sha_v2()
    proxy = LogProxy(a.log)
    feed = FeedVision(detector=det, log_path=None)
    feed._log = proxy                                           # kompozycja jak shadow

    sk = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    sk.setblocking(False)

    def send(obj):
        try:
            sk.sendto(json.dumps(obj).encode(), a.sock)
        except OSError:
            pass                                                # klient jeszcze/już nie słucha

    proxy.write_raw(json.dumps({"t": "meta", "role": "PERCEP V2 (karmi kontroler po UDS)",
                                "det_v2_sha": det.weights_sha, "feed_sha_v2": fsha,
                                "core_feed_sha": feed.feed_sha, "topic": a.topic,
                                "sock": a.sock, "device": det.device}) + "\n")
    send({"t": "meta", "feed_sha_v2": fsha, "det_v2_sha": det.weights_sha})
    print(f"[percep] det_v2={det.weights_sha[:16]} feed_sha_v2={fsha[:16]} "
          f"core={feed.feed_sha[:16]} device={det.device}", flush=True)

    st = {"pos": None, "q": None, "n_img": 0, "wall_ms": []}

    def on_pos(m):
        st["pos"] = [float(m.x), float(m.y), float(m.z)]
        if st["q"] is not None:
            feed.push_own(m.timestamp / 1e6, st["pos"], st["q"])

    def on_att(m):
        st["q"] = [float(m.q[0]), float(m.q[1]), float(m.q[2]), float(m.q[3])]
        if st["pos"] is not None:
            feed.push_own(m.timestamp / 1e6, st["pos"], st["q"])

    def on_img(msg):
        t = msg.header.stamp.sec + msg.header.stamp.nanosec / 1e9
        w0 = time.monotonic()
        feed.push_frame(t, imgmsg_to_mono(msg))
        st["wall_ms"].append(round((time.monotonic() - w0) * 1000.0, 2))
        st["n_img"] += 1
        s = feed.sample(t)
        s["feed_sha"] = fsha                                    # kontraktowy sha V2
        send({"t": "s", "t_frame": round(t, 4),
              "t_update_sim": round(_sim[0], 4), "s": s,
              "n_frames": feed.n_frames, "n_fresh": feed.n_fresh})

    rclpy.init()
    node = Node("percep_v2")
    qos = QoSProfile(depth=1, history=HistoryPolicy.KEEP_LAST,
                     reliability=ReliabilityPolicy.BEST_EFFORT)
    node.create_subscription(VehicleLocalPosition, "/fmu/out/vehicle_local_position", on_pos, qos)
    node.create_subscription(VehicleAttitude, "/fmu/out/vehicle_attitude", on_att, qos)
    node.create_subscription(Image, a.topic, on_img, qos_be())
    ex = SingleThreadedExecutor()
    ex.add_node(node)

    signal.signal(signal.SIGTERM, lambda *_: _stop.__setitem__(0, True))
    signal.signal(signal.SIGINT, lambda *_: _stop.__setitem__(0, True))
    t_hb = time.monotonic()
    while not _stop[0] and rclpy.ok():
        ex.spin_once(timeout_sec=0.05)
        if time.monotonic() - t_hb >= 15.0:
            t_hb = time.monotonic()
            print(f"[percep] sim={_sim[0]:.1f} frames={feed.n_frames} boxes={feed.n_boxes} "
                  f"fresh={feed.n_fresh}", flush=True)

    feed.close()
    pm = sorted(st["wall_ms"])
    summ = {"n_img_cb": st["n_img"], "n_frames": feed.n_frames, "n_boxes": feed.n_boxes,
            "n_fresh": feed.n_fresh, "n_feed_expire": feed.n_feed_expire,
            "push_frame_wall_ms": ({"n": len(pm), "p50": pm[len(pm) // 2],
                                    "p95": pm[int(len(pm) * 0.95)], "max": pm[-1]} if pm else None),
            "det_v2_sha": det.weights_sha, "feed_sha_v2": fsha, "sim_last": round(_sim[0], 3)}
    with open(a.log + ".summary.json", "w") as f:
        json.dump(summ, f, indent=1)
    print(f"[percep] DONE {json.dumps(summ)}", flush=True)


if __name__ == "__main__":
    main()
