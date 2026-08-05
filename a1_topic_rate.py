#!/usr/bin/env python3
"""a1_topic_rate.py — pomiar czestotliwosci tematu ROS2 z jawnym QoS (A1).
Powod: `ros2 topic hz` w Jazzy nie ma opcji QoS -> subskrybuje RELIABLE i nie
odbiera BEST_EFFORT tematow PX4 /fmu/out. Ten miernik uzywa poprawnego QoS,
binuje per-sekunda i raportuje avg + MIN rate w oknie (dowod ">=10 Hz przez caly lot").

Uzycie: python3 a1_topic_rate.py <topic> <pkg/msg> <sekundy> [reliability=best_effort|reliable]
Przyklad: python3 a1_topic_rate.py /fmu/out/vehicle_odometry px4_msgs/msg/VehicleOdometry 45 best_effort
"""
import sys, time, importlib
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy

def load_msg(spec):
    pkg, _, name = spec.replace('/msg/', '/').partition('/') if '/msg/' not in spec else (spec.split('/')[0], 'msg', spec.split('/')[-1])
    parts = spec.split('/')
    module = importlib.import_module(f"{parts[0]}.msg")
    return getattr(module, parts[-1])

def main():
    topic = sys.argv[1]; msgspec = sys.argv[2]; dur = float(sys.argv[3])
    rel = sys.argv[4] if len(sys.argv) > 4 else "best_effort"
    MsgType = load_msg(msgspec)
    rclpy.init()
    node = Node("a1_rate_meter")
    qos = QoSProfile(depth=10, history=HistoryPolicy.KEEP_LAST,
                     reliability=ReliabilityPolicy.BEST_EFFORT if rel == "best_effort" else ReliabilityPolicy.RELIABLE,
                     durability=DurabilityPolicy.VOLATILE)
    state = {"count": 0, "bins": {}, "t0": time.monotonic()}
    def cb(_):
        state["count"] += 1
        sec = int(time.monotonic() - state["t0"])
        state["bins"][sec] = state["bins"].get(sec, 0) + 1
    node.create_subscription(MsgType, topic, cb, qos)
    end = time.monotonic() + dur
    while time.monotonic() < end and rclpy.ok():
        rclpy.spin_once(node, timeout_sec=0.1)
    elapsed = time.monotonic() - state["t0"]
    avg = state["count"] / elapsed if elapsed > 0 else 0
    # min rate po pelnych sekundach (ignoruj pierwsza/ostatnia czesciowa)
    full = [v for k, v in sorted(state["bins"].items()) if 0 < k < int(elapsed)]
    mn = min(full) if full else 0
    print(f"[a1] topic={topic} qos={rel}")
    print(f"[a1] wiadomosci={state['count']} czas={elapsed:.1f}s avg={avg:.1f} Hz min_per_sec={mn} Hz")
    ok = avg >= 10.0 and mn >= 10
    print(f"[a1] WERDYKT >=10Hz przez caly czas: {'PASS' if ok else 'FAIL'} (avg>=10 i min_per_sec>=10)")
    node.destroy_node(); rclpy.shutdown()
    return 0 if ok else 2

if __name__ == "__main__":
    sys.exit(main())
