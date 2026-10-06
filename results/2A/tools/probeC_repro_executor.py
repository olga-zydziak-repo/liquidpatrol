#!/usr/bin/env python3
"""results/2A/tools/probeC_repro_executor.py — repro offline (zero lotów) dwóch blokerów
bootu C1 sondy (RAPORT_2A_S3 §2) + dowód naprawy-kandydata. Uruchamiane per-część, bo
repro kolizji zostawia wątek-demona na globalnym egzekutorze (teardown bez rclpy.shutdown
⇒ abort przy wyjściu — artefakt repro, nie dowodu).

Część A (kolizja, mechanizm bootu C1 1:1):
  wątek 1 = pętla rclpy.spin_once(node_a) [wzór bench_flight.py:248-251, egzekutor GLOBALNY]
  wątek 2 = rclpy.spin_once(node_b)       [wzór feed_vision.py:299]
  → RuntimeError('Executor is already spinning') w wątku 2 przy PIERWSZYM wywołaniu;
  w bootcie C1 wątek _spin FeedVisionLive ginie ⇒ zero callbacków pos/att/obraz ⇒ feed martwy.

Część B (naprawa-kandydat N3-C): węzeł feedu na DEDYKOWANYM SingleThreadedExecutor
  (ex = SingleThreadedExecutor(); ex.add_node(node_b); pętla ex.spin_once(0.05))
  współistnieje ze spinem globalnym — subskrypcja odbiera wiadomości (5/5 w repro 06.10).

Repro ros2 CLI (bloker 2, błąd DRIVERA nie frozen):
  PYTHONPATH=.b0deps/... ros2 topic list → PackageNotFoundError: ros2cli
  (B0SP maskuje metadata dystrybucji; fix w probeC_boot.sh: B0SP tylko w env run_boot).

Użycie: probeC_repro_executor.py {collision|fix}
"""
import sys
import threading
import time

import rclpy
from rclpy.node import Node


def collision():
    rclpy.init()
    a = Node("bench_like")
    b = Node("feed_like")

    def spin_a():
        while True:
            rclpy.spin_once(a, timeout_sec=0.02)      # bench_flight.py:250 (globalny egzekutor)

    threading.Thread(target=spin_a, daemon=True).start()
    time.sleep(0.3)
    try:
        rclpy.spin_once(b, timeout_sec=0.05)          # feed_vision.py:299
        print("feed_like spin_once: OK (kolizji brak)")
    except RuntimeError as e:
        print("feed_like spin_once: RuntimeError:", e)


def fix():
    from rclpy.executors import SingleThreadedExecutor
    from std_msgs.msg import String
    rclpy.init()
    a = Node("bench_like")
    b = Node("feed_like")
    hits = []
    b.create_subscription(String, "/probe_t", lambda m: hits.append(m.data), 1)

    def spin_a():
        while True:
            rclpy.spin_once(a, timeout_sec=0.02)

    threading.Thread(target=spin_a, daemon=True).start()
    ex = SingleThreadedExecutor()
    ex.add_node(b)

    def spin_b():
        while True:
            ex.spin_once(timeout_sec=0.05)

    threading.Thread(target=spin_b, daemon=True).start()
    pub = a.create_publisher(String, "/probe_t", 1)
    time.sleep(0.5)
    for i in range(5):
        pub.publish(String(data=f"m{i}"))
        time.sleep(0.1)
    time.sleep(0.3)
    print("dedykowany executor: odebrane", hits,
          "— współistnienie z globalnym OK" if hits else "— FAIL")


if __name__ == "__main__":
    {"collision": collision, "fix": fix}[sys.argv[1]]()
