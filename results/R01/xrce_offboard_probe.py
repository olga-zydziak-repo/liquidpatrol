#!/usr/bin/env python3
"""xrce_offboard_probe.py — R1 pomiar sciezki XRCE /fmu/in/trajectory_setpoint.
NIEINWAZYJNY POMIAR (recon): arm+offboard, hover, mierzy:
  - jitter petli publikacji setpointow (dt: mean/std/p95/max) @ target Hz
  - latencja aktywacji offboard (cmd -> VehicleControlMode.flag_control_offboard_enabled)
  - czas reakcji PX4 na UTRATE strumienia (stop publikacji -> zmiana nav_state/failsafe)
Po pomiarze: bezpieczne disarm.
Wynik: JSON na stdout + /tmp/r1/xrce_probe.json
"""
import sys, time, json, statistics, os
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from px4_msgs.msg import (OffboardControlMode, TrajectorySetpoint, VehicleCommand,
                          VehicleControlMode, VehicleStatus, VehicleLocalPosition,
                          FailsafeFlags)

HZ = float(os.environ.get("HZ", "50"))
HOVER_S = float(os.environ.get("HOVER_S", "8"))
CUT_WAIT_S = float(os.environ.get("CUT_WAIT_S", "4"))  # ile obserwowac po odcieciu strumienia

def qos_pub():
    return QoSProfile(depth=10, history=HistoryPolicy.KEEP_LAST,
                      reliability=ReliabilityPolicy.BEST_EFFORT, durability=DurabilityPolicy.TRANSIENT_LOCAL)
def qos_sub():
    return QoSProfile(depth=10, history=HistoryPolicy.KEEP_LAST,
                      reliability=ReliabilityPolicy.BEST_EFFORT, durability=DurabilityPolicy.VOLATILE)

class Probe(Node):
    def __init__(self):
        super().__init__("xrce_offboard_probe")
        self.ocm = self.create_publisher(OffboardControlMode, "/fmu/in/offboard_control_mode", qos_pub())
        self.tsp = self.create_publisher(TrajectorySetpoint, "/fmu/in/trajectory_setpoint", qos_pub())
        self.cmd = self.create_publisher(VehicleCommand, "/fmu/in/vehicle_command", qos_pub())
        self.create_subscription(VehicleControlMode, "/fmu/out/vehicle_control_mode", self.cb_vcm, qos_sub())
        self.create_subscription(VehicleStatus, "/fmu/out/vehicle_status_v1", self.cb_vs, qos_sub())
        self.create_subscription(VehicleLocalPosition, "/fmu/out/vehicle_local_position", self.cb_lp, qos_sub())
        self.create_subscription(FailsafeFlags, "/fmu/out/failsafe_flags", self.cb_ff, qos_sub())
        self.offboard_enabled = False
        self.t_offboard_enabled = None
        self.nav_state = None
        self.failsafe = False
        self.ob_signal_lost = False
        self.z = 0.0
        self.have_lp = False
        self.arming_state = None
        self.min_z = 0.0

    def cb_ff(self, m):
        self.ob_signal_lost = bool(m.offboard_control_signal_lost)

    def cb_vcm(self, m):
        if m.flag_control_offboard_enabled and not self.offboard_enabled:
            self.offboard_enabled = True
            self.t_offboard_enabled = time.monotonic()
        elif not m.flag_control_offboard_enabled:
            self.offboard_enabled = False
    def cb_vs(self, m):
        self.nav_state = m.nav_state
        self.failsafe = bool(getattr(m, "failsafe", False))
        self.arming_state = getattr(m, "arming_state", None)
    def cb_lp(self, m):
        self.z = m.z; self.have_lp = True
        if m.z < self.min_z: self.min_z = m.z

    def now_us(self):
        return int(self.get_clock().now().nanoseconds / 1000)

    def send_cmd(self, command, p1=0.0, p2=0.0):
        m = VehicleCommand()
        m.timestamp = self.now_us()
        m.command = command; m.param1 = p1; m.param2 = p2
        m.target_system = 1; m.target_component = 1
        m.source_system = 1; m.source_component = 1; m.from_external = True
        self.cmd.publish(m)

    def pub_setpoint(self, z=-5.0):
        o = OffboardControlMode(); o.timestamp = self.now_us()
        o.position = True; o.velocity = False; o.acceleration = False
        o.attitude = False; o.body_rate = False
        self.ocm.publish(o)
        t = TrajectorySetpoint(); t.timestamp = self.now_us()
        t.position = [0.0, 0.0, float(z)]
        t.yaw = 0.0
        self.tsp.publish(t)

def main():
    rclpy.init()
    n = Probe()
    res = {"target_hz": HZ}
    # 0) poczekaj na telemetrie
    t0 = time.monotonic()
    while not n.have_lp and time.monotonic() - t0 < 10:
        rclpy.spin_once(n, timeout_sec=0.05)
    res["telemetry_ok"] = n.have_lp
    # 1) prestream >1s setpointow (wymog PX4 przed offboard)
    dt_period = 1.0 / HZ
    for _ in range(int(HZ * 1.5)):
        n.pub_setpoint(); rclpy.spin_once(n, timeout_sec=0.001); time.sleep(dt_period)
    # 2) offboard + arm (retry az arming_state==2), mierz latencje aktywacji
    t_cmd = time.monotonic()
    n.send_cmd(VehicleCommand.VEHICLE_CMD_DO_SET_MODE, 1.0, 6.0)   # offboard
    t_arm0 = time.monotonic()
    while n.arming_state != 2 and time.monotonic() - t_arm0 < 6.0:
        n.send_cmd(VehicleCommand.VEHICLE_CMD_DO_SET_MODE, 1.0, 6.0)
        n.send_cmd(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, 1.0)  # arm
        for _ in range(int(HZ*0.4)):
            n.pub_setpoint(); rclpy.spin_once(n, timeout_sec=0.001); time.sleep(dt_period)
    res["armed_after_retry"] = n.arming_state
    # 3) hover + pomiar jittera petli
    dts = []
    last = time.monotonic()
    t_end = time.monotonic() + HOVER_S
    while time.monotonic() < t_end:
        n.pub_setpoint()
        rclpy.spin_once(n, timeout_sec=0.001)
        now = time.monotonic()
        dts.append((now - last) * 1000.0)  # ms
        last = now
        sleep = dt_period - (time.monotonic() - now)
        if sleep > 0: time.sleep(sleep)
    res["offboard_activation_latency_s"] = (n.t_offboard_enabled - t_cmd) if n.t_offboard_enabled else None
    res["offboard_enabled_reached"] = n.offboard_enabled
    res["nav_state_hover"] = n.nav_state
    res["armed_state_hover"] = n.arming_state  # 2 = ARMED
    res["max_alt_m_hover"] = round(-n.min_z, 2)
    # jitter (odrzuc pierwsze 10 probek - rozruch)
    j = dts[10:] if len(dts) > 20 else dts
    if j:
        res["loop_dt_ms"] = {"mean": round(statistics.mean(j),3), "std": round(statistics.pstdev(j),3),
                             "p95": round(sorted(j)[int(len(j)*0.95)],3), "max": round(max(j),3),
                             "min": round(min(j),3), "n": len(j)}
    # 4) UTRATA strumienia: przestan publikowac, mierz czas do (a) offboard_control_signal_lost,
    #    (b) zmiany nav_state / spadku flag_control_offboard_enabled (akcja failsafe)
    nav_before = n.nav_state
    n.ob_signal_lost = False
    t_cut = time.monotonic()
    t_signal_lost = None; t_action = None
    tw = time.monotonic() + CUT_WAIT_S
    while time.monotonic() < tw:
        rclpy.spin_once(n, timeout_sec=0.02)
        if t_signal_lost is None and n.ob_signal_lost:
            t_signal_lost = time.monotonic() - t_cut
        if t_action is None and ((n.nav_state is not None and n.nav_state != nav_before)
                                 or not n.offboard_enabled or n.failsafe):
            t_action = time.monotonic() - t_cut
        # NIE przerywaj wczesnie — obserwuj cale okno, by zlapac pozna akcje
    res["stream_loss_nav_before"] = nav_before
    res["stream_loss_nav_after"] = n.nav_state
    res["stream_loss_failsafe"] = n.failsafe
    res["stream_loss_signal_lost_s"] = round(t_signal_lost,3) if t_signal_lost else None
    res["stream_loss_action_s"] = round(t_action,3) if t_action else None
    res["stream_loss_offboard_still_enabled"] = n.offboard_enabled
    res["COM_OF_LOSS_T_ref"] = 1.0
    # 5) bezpieczne disarm (land + disarm)
    n.send_cmd(VehicleCommand.VEHICLE_CMD_NAV_LAND)
    for _ in range(20):
        rclpy.spin_once(n, timeout_sec=0.05); time.sleep(0.05)
    n.send_cmd(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, 0.0)
    os.makedirs("/tmp/r1", exist_ok=True)
    json.dump(res, open("/tmp/r1/xrce_probe.json","w"), indent=2)
    print(json.dumps(res, indent=2))
    n.destroy_node(); rclpy.shutdown()

if __name__ == "__main__":
    main()
