#!/usr/bin/env python3
"""results/2A/tools/test_aneks3.py — test naprawy ANEKS_2A-3 N3-C (dedykowany egzekutor
węzła feedu). Wzór repro probeC_repro_executor.py przeniesiony na PRAWDZIWĄ klasę
FeedVisionLive: wątek-lustro bench_flight (pętla rclpy.spin_once na egzekutorze GLOBALNYM,
bench_flight.py:248-251) + FeedVisionLive z dummy-detektorem; przed N3-C wątek _spin feedu
ginął pierwszym wywołaniem ('Executor is already spinning', boot C1 sondy, RAPORT_2A_S3
§2b) ⇒ zero callbacków. Po N3-C: wątek żyje, callbacki pos/att/obraz dochodzą.

Wymaga rclpy (ROS sourced) + B0SP w PYTHONPATH (cv2 dla r02.mti). Uruchamiany jawnie:
  PYTHONPATH=.b0deps/lib/python3.12/site-packages:. python3 -m pytest results/2A/tools/test_aneks3.py
(poza automatyczną regresją dirs — jak r01/brake_test i r02/test_deadman, klasa rclpy env)."""
import sys
import threading
import time

ROOT = "/home/olga/projects/liquidpatrol"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


class _DummyDet:
    """Zamiennik YoloDetector w teście (bez wag/GPU): zawsze brak boxa."""
    weights_sha = "dummy"

    def top1(self, frame):
        return None


def test_n3c_feed_spin_coexists_with_global_executor():
    import numpy as np
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import Image
    from px4_msgs.msg import VehicleLocalPosition, VehicleAttitude
    from harness.feed_vision import FeedVisionLive

    rclpy.init()
    bench = Node("bench_like_aneks3")
    running = [True]

    def spin_bench():                       # lustro bench_flight.py:248-251 (egzekutor GLOBALNY)
        while running[0]:
            rclpy.spin_once(bench, timeout_sec=0.02)

    th_bench = threading.Thread(target=spin_bench, daemon=True)
    th_bench.start()
    time.sleep(0.3)                         # globalny egzekutor już spinuje (warunek kolizji C1)

    feed = FeedVisionLive(image_topic="/aneks3_probe_img", detector=_DummyDet(),
                          node_name="feed_v_aneks3")
    try:
        time.sleep(0.5)
        # przed N3-C: RuntimeError w _spin ⇒ wątek martwy już tutaj
        assert feed._th.is_alive(), "wątek _spin feedu zginął (regresja kolizji egzekutora C1)"

        pub_pos = bench.create_publisher(VehicleLocalPosition, "/fmu/out/vehicle_local_position", 10)
        pub_att = bench.create_publisher(VehicleAttitude, "/fmu/out/vehicle_attitude", 10)
        pub_img = bench.create_publisher(Image, "/aneks3_probe_img", 10)
        time.sleep(0.5)                     # discovery pub↔sub

        pos = VehicleLocalPosition(); pos.x, pos.y, pos.z = 0.0, 0.0, -10.0; pos.timestamp = 1_000_000
        att = VehicleAttitude(); att.q = [1.0, 0.0, 0.0, 0.0]; att.timestamp = 1_000_000
        img = Image(); img.height, img.width, img.encoding = 480, 640, "mono8"
        img.data = bytes(np.zeros(480 * 640, dtype=np.uint8))
        img.header.stamp.sec = 1

        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline and feed.n_frames < 3:
            pub_pos.publish(pos); pub_att.publish(att); pub_img.publish(img)
            time.sleep(0.1)

        assert feed._own is not None, "callbacki pos/att nie doszły (sub na dedykowanym egzekutorze)"
        assert feed.n_frames >= 1, "callback obrazu nie doszedł / push_frame nie przetworzył klatki"
        assert feed._th.is_alive(), "wątek _spin padł w trakcie przetwarzania"
    finally:
        running[0] = False
        feed._running = False
        th_bench.join(timeout=2.0)
        feed._th.join(timeout=2.0)
        feed.close()
        bench.destroy_node()
        feed._node.destroy_node()
        rclpy.shutdown()
