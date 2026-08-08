"""r01/exec_lib.py — transport egzekutora (kanoniczny, rozszerzony instrumentacją bramki).

Płaszczyzna HYBRYDOWA (A1): MAVSDK = telemetria NED + flight_mode + arm + RTL/Land + param + heartbeat;
XRCE (rclpy publisher) = OffboardControlMode + TrajectorySetpoint (setpointy) + DO_SET_MODE (tryb).
Instrumentacja: luka telemetrii (max), flight_mode (detekcja odpaleń GF/warstwy-0), config GF natywnego.
NIGDY set_position po MAVSDK (A1). Używane przez r01/gate_run.py (S1–S4).
"""
from __future__ import annotations
import time, math, asyncio, threading

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from px4_msgs.msg import OffboardControlMode, TrajectorySetpoint, VehicleCommand

from mavsdk import System
from r01.config import corner_waypoints, ALT_M, GF_MAX_HOR_DIST, GF_MAX_VER_DIST, GF_ACTION

ACCEPT_R = 1.5


def qos_pub():
    return QoSProfile(depth=10, history=HistoryPolicy.KEEP_LAST,
                      reliability=ReliabilityPolicy.BEST_EFFORT,
                      durability=DurabilityPolicy.TRANSIENT_LOCAL)


class XrcePublisher:
    def __init__(self):
        rclpy.init()
        self.node = Node("gate_xrce")
        self.p_ocm = self.node.create_publisher(OffboardControlMode, "/fmu/in/offboard_control_mode", qos_pub())
        self.p_tsp = self.node.create_publisher(TrajectorySetpoint, "/fmu/in/trajectory_setpoint", qos_pub())
        self.p_cmd = self.node.create_publisher(VehicleCommand, "/fmu/in/vehicle_command", qos_pub())

    def _now_us(self):
        return int(self.node.get_clock().now().nanoseconds / 1000)

    def publish_setpoint(self, xyz, yaw=0.0):
        o = OffboardControlMode(); o.timestamp = self._now_us(); o.position = True
        self.p_ocm.publish(o)
        t = TrajectorySetpoint(); t.timestamp = self._now_us()
        t.position = [float(xyz[0]), float(xyz[1]), float(xyz[2])]; t.yaw = float(yaw)
        self.p_tsp.publish(t)

    def set_offboard_mode(self):
        m = VehicleCommand(); m.timestamp = self._now_us()
        m.command = VehicleCommand.VEHICLE_CMD_DO_SET_MODE
        m.param1 = 1.0; m.param2 = 6.0
        m.target_system = 1; m.target_component = 1
        m.source_system = 1; m.source_component = 1; m.from_external = True
        self.p_cmd.publish(m)

    def shutdown(self):
        self.node.destroy_node(); rclpy.shutdown()


class Planner:
    def __init__(self, laps):
        self.wps = corner_waypoints(); self.laps = laps
        self.idx = 0; self.lap = 0; self.done = False
        self._override = None            # wymuszony target (S3)

    def override(self, xyz):
        self._override = xyz

    def clear_override(self):
        self._override = None

    def target(self):
        return self._override if self._override else self.wps[self.idx % 4]

    def advance_if_reached(self, pos):
        if self._override:               # override nie awansuje pętli
            return False
        tx, ty, _ = self.target()
        if math.hypot(pos[0]-tx, pos[1]-ty) <= ACCEPT_R:
            self.idx += 1
            if self.idx % 4 == 0:
                self.lap += 1
                if self.lap >= self.laps:
                    self.done = True
            return True
        return False


class Mav:
    """MAVSDK (wątek asyncio): telemetria + flight_mode + arm/RTL/Land + GF config. A1: brak ruchu."""
    def __init__(self, set_gf=True):
        self.pos = [0.0, 0.0, 0.0]; self.vel = [0.0, 0.0, 0.0]
        self.yaw = 0.0                   # R0.2: yaw [rad] NED (0=Północ) — OBSERVE potrzebuje attitude
        self.have_tel = False; self.armed = False
        self.flight_mode = None
        self.tel_max_gap = 0.0; self._last_tel = None
        self.calls = []                  # (name, is_motion) — A1: is_motion zawsze False
        self.set_gf = set_gf
        self._arm = threading.Event(); self._rtl = threading.Event(); self._land = threading.Event()
        self._stop = threading.Event(); self._ready = threading.Event()
        self.t = threading.Thread(target=self._run, daemon=True); self.t.start()

    def _run(self):
        asyncio.run(self._main())

    async def _main(self):
        drone = System()
        await drone.connect(system_address="udpin://0.0.0.0:14540")
        async for s in drone.core.connection_state():
            if s.is_connected:
                break
        # clamp prędkości (v_max=3, spójne z barierą A2)
        for pname in ("MPC_XY_VEL_MAX", "MPC_XY_CRUISE", "MPC_XY_VEL_ALL"):
            try:
                await drone.param.set_param_float(pname, 3.0); self.calls.append((f"param:{pname}=3", False))
            except Exception:
                pass
        # §3: akcja natywna po utracie offboard = Hold (COM_OBL_RC_ACT=5); COM_OF_LOSS_T=1.0 (default)
        try:
            await drone.param.set_param_int("COM_OBL_RC_ACT", 5)
            self.calls.append(("param:COM_OBL_RC_ACT=5(Hold)", False))
        except Exception:
            pass
        # A3: natywny geofence NA ZEWNĄTRZ obwiedni osłony (defense-in-depth)
        if self.set_gf:
            try:
                await drone.param.set_param_float("GF_MAX_HOR_DIST", float(GF_MAX_HOR_DIST))
                await drone.param.set_param_float("GF_MAX_VER_DIST", float(GF_MAX_VER_DIST))
                await drone.param.set_param_int("GF_ACTION", int(GF_ACTION))
                self.calls.append((f"param:GF(hor={GF_MAX_HOR_DIST},ver={GF_MAX_VER_DIST},act={GF_ACTION})", False))
            except Exception as e:
                self.calls.append((f"gf_fail:{e}", False))

        try:
            await drone.telemetry.set_rate_position_velocity_ned(30.0)
        except Exception:
            pass
        try:
            await drone.telemetry.set_rate_attitude_euler(20.0)
        except Exception:
            pass
        async def tel():
            async for pv in drone.telemetry.position_velocity_ned():
                now = time.monotonic()
                if self._last_tel is not None:
                    self.tel_max_gap = max(self.tel_max_gap, now - self._last_tel)
                self._last_tel = now
                p = pv.position; v = pv.velocity
                self.pos = [p.north_m, p.east_m, p.down_m]
                self.vel = [v.north_m_s, v.east_m_s, v.down_m_s]
                self.have_tel = True
        asyncio.ensure_future(tel())

        async def fm():
            async for m in drone.telemetry.flight_mode():
                self.flight_mode = str(m)
        asyncio.ensure_future(fm())

        async def att():                 # R0.2: yaw z attitude (NED, deg→rad) dla naprowadzania OBSERVE
            async for a in drone.telemetry.attitude_euler():
                self.yaw = math.radians(a.yaw_deg)
        asyncio.ensure_future(att())

        async for h in drone.telemetry.health():
            if h.is_global_position_ok and h.is_home_position_ok:
                break
        self._ready.set()
        while not self._stop.is_set():
            if self._arm.is_set():
                self._arm.clear()
                try:
                    await drone.action.arm(); self.calls.append(("arm", False)); self.armed = True
                except Exception as e:
                    self.calls.append((f"arm_fail:{e}", False))
            if self._rtl.is_set():
                self._rtl.clear()
                try:
                    await drone.action.return_to_launch(); self.calls.append(("return_to_launch", False))
                except Exception as e:
                    self.calls.append((f"rtl_fail:{e}", False))
            if self._land.is_set():
                self._land.clear()
                try:
                    await drone.action.land(); self.calls.append(("land", False))
                except Exception as e:
                    self.calls.append((f"land_fail:{e}", False))
            await asyncio.sleep(0.05)

    def reset_tel_gap(self):
        """Zeruj pomiar luki telemetrii na starcie fazy patrolu (§7: 'przez cały lot')."""
        self.tel_max_gap = 0.0; self._last_tel = None

    def wait_ready(self, timeout): return self._ready.wait(timeout)
    def arm(self): self._arm.set()
    def rtl(self): self._rtl.set()
    def land(self): self._land.set()
    def stop(self): self._stop.set()
    def motion_cmds(self): return [c for c, mo in self.calls if mo]
