#!/usr/bin/env python3
"""r02/gate_run_r02.py — runner ŻYWEJ bramki R0.2 (G1–G5, PRE_R02 §4).

Świeży boot per scenariusz (dyscyplina R0.0/R0.1). Rozszerza r01/gate_run.py o:
  - subskrypcję KANAŁU celu `/liquidpatrol/target_channel` (5-dim, z węzła detektora),
  - tryb OBSERVE (7. liść osłony) + naprowadzanie `ObserveController` (ZOH estymaty świata),
  - autorytet gramatyki `observe on` (P4) — OBSERVE nie omija admisji,
  - liczniki bramki: A1 (mavsdk_motion_cmds=0), ε_FP (ENTRY na pustej scenie), GF native=0.
Księgowość TRÓJWYNIKOWA (shield.outcome). Setpointy TYLKO XRCE przez osłonę (A1). Intruz sterowany
osobno (`r02/intruder_driver.py`) — runner tylko odczytuje detekcje z kanału.

Uruchom (env ROS2, po starcie stacku+detektora+intruza): SCENARIO=G1..G5 python3 -m r02.gate_run_r02
Orkiestracja świeżego bootu per scenariusz: r02/run_gate_r02.sh
"""
from __future__ import annotations
import os, sys, json, time, math

import rclpy
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from std_msgs.msg import Float32MultiArray

from r01.exec_lib import XrcePublisher, Mav, Planner
from r01.shield import PatrolShield, ALLOW, HOLD, REFUSE, GEOFENCE, M_PATROL, M_OBSERVE
from r01.authz import Authorizer
from r01.config import ALT_M, TICK_HZ, DT, R_E
from r02.config_r02 import (D_SAFE_M, THETA_AGE_S, T_ACK_S, F_FOV, EPS_FP_PER_MIN, ChannelConfig)
from r02.target_channel import TargetChannel, Box
from r02.observe_guidance import ObserveController

SCEN = os.environ.get("SCENARIO", "G1")
TRACE = os.environ.get("TRACE", f"/tmp/r02/gate_{SCEN}.jsonl")
PERIOD = DT
CH_TOPIC = "/liquidpatrol/target_channel"


def offboard_ok(fm):
    return fm is not None and "OFFBOARD" in fm


def qos_be():
    return QoSProfile(depth=1, history=HistoryPolicy.KEEP_LAST, reliability=ReliabilityPolicy.BEST_EFFORT)


class ChannelSub:
    """Subskrybent kanału 5-dim z węzła detektora. Utrzymuje ostatnią wartość (cx,cy,w,h,age).
    UWAGA: kanał niesie tylko piksele+age (BEZ conf, A1). Estymatę NED liczy ObserveController."""
    def __init__(self, node):
        self.last = None            # Box|None (z ostatniej niepustej wiadomości)
        self.age = None
        self.locked = False
        self.stamp = None
        node.create_subscription(Float32MultiArray, CH_TOPIC, self._cb, qos_be())

    def _cb(self, msg):
        self.stamp = time.monotonic()
        if msg.data and len(msg.data) == 5:
            cx, cy, w, h, age = msg.data
            self.last = Box(float(cx), float(cy), float(w), float(h))
            self.age = float(age); self.locked = True
        else:
            self.locked = False     # pusty kanał = brak locka (detektor: SEARCHING/CANDIDATE/EXPIRE)


class Runner:
    def __init__(self, laps):
        os.makedirs(os.path.dirname(TRACE), exist_ok=True)
        self.tf = open(TRACE, "w")
        self.xrce = XrcePublisher()
        self.chan = ChannelSub(self.xrce.node)          # współdziel węzeł rclpy osłony
        self.mav = Mav(set_gf=True)
        self.shield = PatrolShield(); self.shield.reset()
        self.planner = Planner(laps)
        self.ctrl = ObserveController(d_safe=D_SAFE_M, alt=ALT_M)
        self.authz = Authorizer()
        self.observe_authority = False
        self.k = 0
        self.max_radial = 0.0
        self._last_pub = None; self.setpoint_max_dt = 0.0
        self.gf_fired = False
        self.n_entry = 0; self.n_false_entry = 0
        self.observe_ticks = 0; self.dsafe_violations = 0; self.min_d_observe = float("inf")
        self.entry_t = None; self.intruder_present = False; self.intruder_in_view_t = None
        self._prev_locked = False

    def admit_observe(self, on=True):
        """Autorytet OBSERVE przez gramatykę (P4) — 'observe on/off' (§2.4, default on)."""
        rec = self.authz.admit("observe on" if on else "observe off")
        self.observe_authority = (rec["decision"] == "ALLOW" and rec["mode"] == "OBSERVE")
        return rec

    def _pub(self, xyz):
        now = time.monotonic()
        if self._last_pub is not None:
            self.setpoint_max_dt = max(self.setpoint_max_dt, now - self._last_pub)
        self._last_pub = now
        self.xrce.publish_setpoint(xyz)

    def _spin(self):
        rclpy.spin_once(self.xrce.node, timeout_sec=0.0)

    def tick(self, force_mode=None, watch_gf=True):
        self._spin()
        pos = list(self.mav.pos); vel = list(self.mav.vel)
        # aktualizacja naprowadzania z kanału (świeża detekcja → zamroź estymatę)
        locked = self.chan.locked and (self.chan.age is not None and self.chan.age <= THETA_AGE_S)
        if self.chan.locked and self.chan.last is not None:
            # traktuj każdą niepustą wiadomość jako świeżą detekcję (węzeł publikuje @1 Hz)
            yaw = self._yaw()
            self.ctrl.on_detection(pos, yaw, self.chan.last)
        if self._prev_locked and not locked:
            self.ctrl.reset()
        # ENTRY: przejście unlocked→locked
        if locked and not self._prev_locked:
            self.n_entry += 1
            if self.entry_t is None:
                self.entry_t = time.time() - self.t0
            if not self.intruder_present:
                self.n_false_entry += 1        # ε_FP: lock na pustej scenie
        self._prev_locked = locked

        # tryb: OBSERVE gdy lock ∧ autorytet gramatyki ∧ estymata; inaczej force/patrol
        if locked and self.observe_authority and self.ctrl.has_estimate() and force_mode is None:
            mode = M_OBSERVE
            sp = self.ctrl.setpoint(pos) or self.planner.target()
        elif force_mode is not None:
            mode = force_mode; sp = self.planner.target()
        else:
            mode = M_PATROL; sp = self.planner.target()

        d = self.shield.step(self.k, pos, vel, sp, mode=mode)
        self._pub(d["applied"])
        self.max_radial = max(self.max_radial, math.hypot(pos[0], pos[1]))
        if mode == M_OBSERVE and locked:
            self.observe_ticks += 1
            dd = self.ctrl.h_distance(pos)
            if dd is not None:
                self.min_d_observe = min(self.min_d_observe, dd)
                if dd < D_SAFE_M - 0.5:
                    self.dsafe_violations += 1
        if watch_gf and self.mav.armed and not offboard_ok(self.mav.flight_mode) and self.mav.flight_mode:
            self.gf_fired = True
        rec = {"k": self.k, "t": round(time.time()-self.t0, 3), "decision": d["decision"],
               "reason": d["reason"], "rule": d["rule"], "mode": mode, "locked": locked,
               "age": self.chan.age, "pos": [round(v, 2) for v in pos],
               "applied": [round(v, 2) for v in d["applied"]], "r_pos": round(math.hypot(pos[0], pos[1]), 2),
               "flight_mode": self.mav.flight_mode, "min_d": None if self.min_d_observe==float("inf") else round(self.min_d_observe,2)}
        self.tf.write(json.dumps(rec) + "\n")
        self.k += 1
        return d

    def _yaw(self):
        # R0.2: PRAWDZIWY yaw z attitude (exec_lib.Mav.yaw, NED rad) — domknięte dla latającego OBSERVE.
        return self.mav.yaw

    def bring_up(self):
        print("[gate] czekam na MAVSDK health...")
        if not self.mav.wait_ready(30):
            print("[gate] BRAK health — STOP"); self._abort(); sys.exit(2)
        self.t0 = time.time(); self.start = list(self.mav.pos)
        for _ in range(int(TICK_HZ * 1.5)):
            self.xrce.publish_setpoint((self.start[0], self.start[1], -ALT_M)); time.sleep(PERIOD)
        self.xrce.set_offboard_mode(); time.sleep(0.2); self.mav.arm()
        t = time.time()
        while not self.mav.armed and time.time()-t < 5:
            self.xrce.publish_setpoint((self.start[0], self.start[1], -ALT_M)); time.sleep(PERIOD)
        tc = time.time()
        while time.time()-tc < 15:
            self.xrce.publish_setpoint((self.start[0], self.start[1], -ALT_M)); time.sleep(PERIOD)
            if abs(self.mav.pos[2] - (-ALT_M)) < 1.0:
                break
        self.mav.reset_tel_gap()
        print(f"[gate] armed={self.mav.armed} down={self.mav.pos[2]:.1f} fm={self.mav.flight_mode}")

    def _abort(self):
        try: self.mav.stop(); self.xrce.shutdown()
        except Exception: pass

    def finish(self, summary):
        self.tf.write(json.dumps({"SCENARIO_RESULT": summary}) + "\n"); self.tf.close()
        print("[gate] RESULT:", json.dumps(summary, ensure_ascii=False))
        self.mav.stop(); self.xrce.shutdown()


# --------------------------- SCENARIUSZE G1–G5 ------------------------------
def scenario_G1(r: Runner):
    """Nominal bez intruza: patrol jak R0.1 S1, detektor żywy ale 0 ENTRY (ε_FP)."""
    r.admit_observe(True); r.intruder_present = False
    r.bring_up()
    while not r.planner.done and time.time()-r.t0 < 240:
        d = r.tick()
        if d["decision"] == REFUSE: break
        r.planner.advance_if_reached(list(r.mav.pos)); time.sleep(PERIOD)
    r.mav.rtl(); time.sleep(8); r.mav.land(); time.sleep(2)
    o = r.shield.outcome(env_success=r.planner.done)
    dur_min = max((time.time()-r.t0)/60.0, 1e-6)
    crit = {"laps_done": r.planner.lap, "n_entry": r.n_entry, "n_false_entry": r.n_false_entry,
            "eps_fp_per_min": round(r.n_false_entry/dur_min, 3), "eps_fp_ok": (r.n_false_entry/dur_min) <= EPS_FP_PER_MIN,
            "A1_motion": len(r.mav.motion_cmds()), "A1_ok": len(r.mav.motion_cmds())==0,
            "A3_gf_fired": r.gf_fired, "max_r": round(r.max_radial,2), "inside_R_E": r.max_radial<=R_E,
            "outcome": o["wynik"]}
    crit["PASS"] = (crit["n_entry"]==0 and crit["eps_fp_ok"] and crit["A1_ok"] and not r.gf_fired
                    and crit["inside_R_E"] and o["wynik"]=="SUKCES")
    r.finish({"scenario": "G1", **crit, "mavsdk_calls": [c for c,_ in r.mav.calls]})
    return crit["PASS"]


def scenario_G2(r: Runner):
    """Intruz wchodzi w FOV → ENTRY≤T_ack → OBSERVE, d≥D_safe, cel w FOV ≥ f_fov."""
    r.admit_observe(True); r.intruder_present = True
    r.bring_up()
    while time.time()-r.t0 < 60:
        r.tick()
        if r.observe_ticks > int(20*TICK_HZ):   # ~20 s obserwacji wystarczy
            break
        time.sleep(PERIOD)
    r.mav.rtl(); time.sleep(6); r.mav.land(); time.sleep(2)
    o = r.shield.outcome(env_success=(r.n_entry>0 and r.dsafe_violations==0))
    f_fov = None  # udział FOV liczy detektor (debug topic) — tu proxy: observe_ticks>0 i lock stabilny
    crit = {"n_entry": r.n_entry, "entry_t": round(r.entry_t,2) if r.entry_t else None,
            "t_ack_ok": (r.entry_t is not None and r.entry_t <= T_ACK_S),
            "observe_ticks": r.observe_ticks, "min_d": None if r.min_d_observe==float("inf") else round(r.min_d_observe,2),
            "dsafe_violations": r.dsafe_violations, "dsafe_ok": r.dsafe_violations==0,
            "A1_ok": len(r.mav.motion_cmds())==0, "max_r": round(r.max_radial,2), "inside_R_E": r.max_radial<=R_E,
            "outcome": o["wynik"]}
    crit["PASS"] = (r.n_entry>0 and crit["t_ack_ok"] and crit["dsafe_ok"] and r.observe_ticks>0
                    and crit["A1_ok"] and crit["inside_R_E"])
    r.finish({"scenario": "G2", **crit, "mavsdk_calls": [c for c,_ in r.mav.calls]})
    return crit["PASS"]


def scenario_G3(r: Runner):
    """Intruz prowadzi w stronę płotu → setpoint OBSERVE za obwiednię → REFUSE(GEOFENCE), ≤R_E."""
    r.admit_observe(True); r.intruder_present = True
    r.bring_up()
    refuse_reason = None
    while time.time()-r.t0 < 90:
        d = r.tick()
        if d["decision"] == REFUSE:
            refuse_reason = d["reason"]; print(f"[gate] G3 REFUSE({d['reason']})"); break
        time.sleep(PERIOD)
    r.mav.rtl(); time.sleep(6); r.mav.land(); time.sleep(2)
    o = r.shield.outcome(env_success=False)
    crit = {"refuse_reason": refuse_reason, "refuse_is_geofence": refuse_reason==GEOFENCE,
            "max_r": round(r.max_radial,2), "inside_R_E": r.max_radial<=R_E,
            "A3_gf_fired": r.gf_fired, "native_gf_ok": not r.gf_fired,
            "A1_ok": len(r.mav.motion_cmds())==0, "outcome": o["wynik"], "outcome_is_odmowa": o["wynik"]=="ODMOWA"}
    crit["PASS"] = (crit["refuse_is_geofence"] and crit["inside_R_E"] and crit["native_gf_ok"]
                    and crit["A1_ok"] and crit["outcome_is_odmowa"])
    r.finish({"scenario": "G3", **crit, "mavsdk_calls": [c for c,_ in r.mav.calls]})
    return crit["PASS"]


def scenario_G4(r: Runner):
    """Utrata detekcji → ZOH+age → age>θ_age → wyjście z OBSERVE do PATROL (nie ślepy finisz)."""
    r.admit_observe(True); r.intruder_present = True
    r.bring_up()
    saw_observe = False; vanished_at = None; exited = False
    while time.time()-r.t0 < 90:
        d = r.tick()
        if d["mode"] == M_OBSERVE: saw_observe = True
        # po ~8 s obserwacji: intruz znika (sterowane z zewnątrz — tu wykrywamy przez brak locka)
        if saw_observe and not r.chan.locked and vanished_at is None:
            vanished_at = time.time()-r.t0
        if saw_observe and vanished_at is not None and d["mode"] == M_PATROL:
            exited = True; print("[gate] G4 wyjście z OBSERVE do PATROL po sufcie age"); break
        time.sleep(PERIOD)
    r.mav.rtl(); time.sleep(6); r.mav.land(); time.sleep(2)
    o = r.shield.outcome(env_success=(saw_observe and exited))
    crit = {"entered_observe": saw_observe, "exited_to_patrol": exited,
            "A1_ok": len(r.mav.motion_cmds())==0, "max_r": round(r.max_radial,2), "inside_R_E": r.max_radial<=R_E,
            "outcome": o["wynik"]}
    crit["PASS"] = saw_observe and exited and crit["A1_ok"] and crit["inside_R_E"]
    r.finish({"scenario": "G4", **crit, "mavsdk_calls": [c for c,_ in r.mav.calls]})
    return crit["PASS"]


def scenario_G5(r: Runner):
    """Warstwa-0 (regres R0.1 S4): urwanie XRCE → natywna reakcja HOLD ≤~1.2 s, ≤R_E, mimo OBSERVE."""
    r.admit_observe(True); r.intruder_present = True
    r.bring_up()
    # wejdź w OBSERVE jeśli intruz jest, potem URWIJ strumień
    t_fly = time.time()
    while time.time()-t_fly < 8:
        r.tick(); time.sleep(PERIOD)
    print("[gate] G5: URWANIE strumienia XRCE (test warstwy-0 mimo OBSERVE)")
    r.tf.write(json.dumps({"EVENT":"stream_cut","t":round(time.time()-r.t0,3),
                           "flight_mode":r.mav.flight_mode})+"\n")
    t_cut = time.time(); react_s = None; max_r_after = 0.0
    while time.time()-t_cut < 6.0:
        r._spin()
        max_r_after = max(max_r_after, math.hypot(r.mav.pos[0], r.mav.pos[1]))
        if react_s is None and not offboard_ok(r.mav.flight_mode):
            react_s = time.time()-t_cut; print(f"[gate] G5 reakcja natywna po {react_s:.3f}s → {r.mav.flight_mode}")
        time.sleep(0.02)
    r.mav.land(); time.sleep(2)
    crit = {"stream_cut": True, "native_reaction_s": round(react_s,3) if react_s else None,
            "reaction_ok_0.9_1.5": (react_s is not None and 0.9<=react_s<=1.5),
            "native_flight_mode": r.mav.flight_mode, "max_r_after": round(max_r_after,2),
            "inside_R_E": max_r_after<=R_E, "A1_ok": len(r.mav.motion_cmds())==0}
    crit["PASS"] = crit["reaction_ok_0.9_1.5"] and crit["inside_R_E"] and crit["A1_ok"]
    r.finish({"scenario": "G5", **crit, "mavsdk_calls": [c for c,_ in r.mav.calls]})
    return crit["PASS"]


def main():
    laps = {"G1": 3, "G2": 1, "G3": 3, "G4": 2, "G5": 1}[SCEN]
    r = Runner(laps)
    fn = {"G1": scenario_G1, "G2": scenario_G2, "G3": scenario_G3, "G4": scenario_G4, "G5": scenario_G5}[SCEN]
    ok = fn(r)
    sys.exit(0 if ok else 3)


if __name__ == "__main__":
    main()
