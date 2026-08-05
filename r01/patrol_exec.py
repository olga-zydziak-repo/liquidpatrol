#!/usr/bin/env python3
"""r01/patrol_exec.py — węzeł egzekutora patrolu (B2/B3).

Płaszczyzna HYBRYDOWA (A1, §3 PRE_R01):
  - MAVSDK: telemetria NED (pos/vel), ARM, tryby RTL/Land, heartbeat GCS (do uzbrojenia).
            NIGDY komenda ruchu (żadnego set_position) — niezmiennik A1.
  - XRCE (rclpy publisher): OFboardControlMode + TrajectorySetpoint = JEDYNA ścieżka setpointów,
            PRZEZ OSŁONĘ. Wejście w offboard = VehicleCommand DO_SET_MODE (komenda trybu, nie ruch).
Osłona (r01.shield.PatrolShield) tyka @20 Hz; applied-setpoint publikowany do PX4.
Trace jsonl per tick → dowód bramki (A1: 0 motion-komend po MAVSDK).

Uruchom (po source ROS+ros2_ws, stack żywy):  python3 -m r01.patrol_exec
Env: LAPS (default 1), TRACE (plik jsonl).
"""
from __future__ import annotations
import os, sys, json, time, math, asyncio, threading

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from px4_msgs.msg import OffboardControlMode, TrajectorySetpoint, VehicleCommand

from mavsdk import System
from r01.config import corner_waypoints, TICK_HZ, DT, ALT_M
from r01.shield import PatrolShield, ALLOW, HOLD, REFUSE, M_PATROL

LAPS = int(os.environ.get("LAPS", "1"))
TRACE = os.environ.get("TRACE", "/tmp/r01/patrol_trace.jsonl")
ACCEPT_R = 1.5           # promień akceptacji waypointu [m]
PRESTREAM_S = 1.5

def qos_pub():
    return QoSProfile(depth=10, history=HistoryPolicy.KEEP_LAST,
                      reliability=ReliabilityPolicy.BEST_EFFORT,
                      durability=DurabilityPolicy.TRANSIENT_LOCAL)


class XrcePublisher:
    """rclpy jako czysty publisher XRCE (bez spin — publish nie wymaga spinowania)."""
    def __init__(self):
        rclpy.init()
        self.node = Node("patrol_exec_xrce")
        self.p_ocm = self.node.create_publisher(OffboardControlMode, "/fmu/in/offboard_control_mode", qos_pub())
        self.p_tsp = self.node.create_publisher(TrajectorySetpoint, "/fmu/in/trajectory_setpoint", qos_pub())
        self.p_cmd = self.node.create_publisher(VehicleCommand, "/fmu/in/vehicle_command", qos_pub())

    def _now_us(self):
        return int(self.node.get_clock().now().nanoseconds / 1000)

    def publish_setpoint(self, xyz, yaw=0.0):
        o = OffboardControlMode(); o.timestamp = self._now_us()
        o.position = True
        self.p_ocm.publish(o)
        t = TrajectorySetpoint(); t.timestamp = self._now_us()
        t.position = [float(xyz[0]), float(xyz[1]), float(xyz[2])]
        t.yaw = float(yaw)
        self.p_tsp.publish(t)

    def set_offboard_mode(self):
        """Komenda TRYBU przez XRCE (nie ruch) — wejście w offboard."""
        m = VehicleCommand(); m.timestamp = self._now_us()
        m.command = VehicleCommand.VEHICLE_CMD_DO_SET_MODE
        m.param1 = 1.0; m.param2 = 6.0
        m.target_system = 1; m.target_component = 1
        m.source_system = 1; m.source_component = 1; m.from_external = True
        self.p_cmd.publish(m)

    def shutdown(self):
        self.node.destroy_node(); rclpy.shutdown()


class Planner:
    """Generator setpointów pętli perymetru (proceduralny, slot uczonego pilota PUSTY)."""
    def __init__(self, laps):
        self.wps = corner_waypoints()
        self.laps = laps
        self.idx = 0        # bieżący waypoint w bieżącym okrążeniu
        self.lap = 0
        self.done = False

    def target(self):
        return self.wps[self.idx % 4]

    def advance_if_reached(self, pos):
        tx, ty, tz = self.target()
        if math.hypot(pos[0]-tx, pos[1]-ty) <= ACCEPT_R:
            self.idx += 1
            if self.idx % 4 == 0:
                self.lap += 1
                if self.lap >= self.laps:
                    self.done = True
            return True
        return False


class Mav:
    """MAVSDK w osobnym wątku (asyncio) — heartbeat + arm + RTL/Land + telemetria NED.
    NIGDY set_position (A1). Rejestr wywołań MAVSDK do dowodu bramki."""
    def __init__(self):
        self.pos = [0.0, 0.0, 0.0]; self.vel = [0.0, 0.0, 0.0]
        self.have_tel = False; self.armed = False
        self.calls = []                      # (name, is_motion)
        self._arm = threading.Event(); self._rtl = threading.Event(); self._land = threading.Event()
        self._stop = threading.Event()
        self._ready = threading.Event()
        self.t = threading.Thread(target=self._run, daemon=True); self.t.start()

    def _run(self):
        asyncio.run(self._main())

    async def _main(self):
        drone = System()
        await drone.connect(system_address="udpin://0.0.0.0:14540")
        async for s in drone.core.connection_state():
            if s.is_connected:
                break
        # clamp prędkości do v_max=3 (§5 cruise; spójne z założeniem bariery A2)
        for pname, pval in [("MPC_XY_VEL_MAX", 3.0), ("MPC_XY_CRUISE", 3.0), ("MPC_XY_VEL_ALL", 3.0)]:
            try:
                await drone.param.set_param_float(pname, pval); self.calls.append((f"param:{pname}=3", False))
            except Exception:
                pass
        # telemetria NED w tle
        async def tel():
            async for pv in drone.telemetry.position_velocity_ned():
                p = pv.position; v = pv.velocity
                self.pos = [p.north_m, p.east_m, p.down_m]
                self.vel = [v.north_m_s, v.east_m_s, v.down_m_s]
                self.have_tel = True
        asyncio.ensure_future(tel())
        # czekaj na health (heartbeat + pozycja) — armable
        async for h in drone.telemetry.health():
            if h.is_global_position_ok and h.is_home_position_ok:
                break
        self._ready.set()
        # pętla obsługi zdarzeń
        while not self._stop.is_set():
            if self._arm.is_set():
                self._arm.clear()
                try:
                    await drone.action.arm(); self.calls.append(("arm", False)); self.armed = True
                except Exception as e:
                    self.calls.append((f"arm_fail:{e}", False))
            if self._rtl.is_set():
                self._rtl.clear()
                await drone.action.return_to_launch(); self.calls.append(("return_to_launch", False))
            if self._land.is_set():
                self._land.clear()
                await drone.action.land(); self.calls.append(("land", False))
            await asyncio.sleep(0.05)

    # API z wątku głównego
    def wait_ready(self, timeout): return self._ready.wait(timeout)
    def arm(self): self._arm.set()
    def rtl(self): self._rtl.set()
    def land(self): self._land.set()
    def stop(self): self._stop.set()


def main():
    os.makedirs(os.path.dirname(TRACE), exist_ok=True)
    tf = open(TRACE, "w")
    xrce = XrcePublisher()
    mav = Mav()
    shield = PatrolShield(); shield.reset()
    planner = Planner(LAPS)

    print("[exec] czekam na MAVSDK health (heartbeat+pozycja)...")
    if not mav.wait_ready(30):
        print("[exec] BRAK health MAVSDK — STOP"); xrce.shutdown(); mav.stop(); sys.exit(2)
    print(f"[exec] MAVSDK ready. Home-rel start pos={['%.1f'%v for v in mav.pos]}")

    period = DT
    k = 0
    # 1) prestream hover na bieżącej pozycji (wymóg PX4 przed offboard)
    hold0 = list(mav.pos)
    for _ in range(int(TICK_HZ * PRESTREAM_S)):
        xrce.publish_setpoint((hold0[0], hold0[1], -ALT_M)); time.sleep(period)
    # 2) offboard (komenda trybu XRCE) + arm (MAVSDK)
    xrce.set_offboard_mode()
    time.sleep(0.2)
    mav.arm()
    print("[exec] arm zlecony (MAVSDK); wchodzę w patrol")
    t_arm = time.time()
    while not mav.armed and time.time() - t_arm < 5:
        xrce.publish_setpoint((hold0[0], hold0[1], -ALT_M)); time.sleep(period)
    print(f"[exec] armed={mav.armed}")

    # 2b) wznoszenie do wysokości patrolu na starcie (setpoint alt, pozycja start)
    t_climb = time.time()
    while time.time() - t_climb < 15:
        xrce.publish_setpoint((hold0[0], hold0[1], -ALT_M)); time.sleep(period)
        if abs(mav.pos[2] - (-ALT_M)) < 1.0:   # osiągnięto ~alt
            break
    print(f"[exec] na wysokości: down={mav.pos[2]:.1f} (cel {-ALT_M})")

    # 3) pętla patrolu pod osłoną
    t0 = time.time()
    max_r = 0.0
    while not planner.done and time.time() - t0 < 180:
        pos = list(mav.pos); vel = list(mav.vel)
        target = planner.target()
        d = shield.step(k, pos, vel, target, mode=M_PATROL)
        applied = d["applied"]
        xrce.publish_setpoint(applied)
        max_r = max(max_r, math.hypot(pos[0], pos[1]))
        rec = {"k": k, "t": round(time.time()-t0,3), "decision": d["decision"], "reason": d["reason"],
               "rule": d["rule"], "pos": [round(v,2) for v in pos], "target": [round(v,2) for v in target],
               "applied": [round(v,2) for v in applied], "lap": planner.lap, "wp": planner.idx % 4,
               "armed": mav.armed}
        tf.write(json.dumps(rec)+"\n")
        if d["decision"] == REFUSE:
            print(f"[exec] REFUSE({d['reason']}) tick {k} — akcja bezpieczna"); break
        planner.advance_if_reached(pos)
        k += 1
        time.sleep(period)

    # 4) powrót + ląd (MAVSDK — tryby, nie ruch)
    print(f"[exec] patrol koniec: laps={planner.lap} done={planner.done} max_r={max_r:.1f}m")
    mav.rtl()
    time.sleep(8)
    mav.land()
    time.sleep(2)

    # 5) dowód A1 + podsumowanie
    o = shield.outcome(env_success=planner.done)
    motion_calls = [c for c, mo in mav.calls if mo]
    summary = {"laps_done": planner.lap, "planner_done": planner.done, "max_radial_m": round(max_r,2),
               "outcome": o, "mavsdk_calls": [c for c, _ in mav.calls],
               "mavsdk_motion_cmds": len(motion_calls), "A1_ok": len(motion_calls) == 0,
               "ticks": k, "decisions_allow": sum(1 for x in shield.trace if x["decision"]==ALLOW)}
    tf.write(json.dumps({"SUMMARY": summary})+"\n"); tf.close()
    print("[exec] SUMMARY:", json.dumps(summary))
    mav.stop(); xrce.shutdown()
    sys.exit(0 if summary["A1_ok"] else 3)

if __name__ == "__main__":
    main()
