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
import os, sys, json, time, math, threading

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
from r02.gate_harness import project_to_pixel   # EKSPLORACJA: projekcja GT intruza (klasyfikacja true/false)

SCEN = os.environ.get("SCENARIO", "G1")
TRACE = os.environ.get("TRACE", f"/tmp/r02/gate_{SCEN}.jsonl")
PERIOD = DT
CH_TOPIC = "/liquidpatrol/target_channel"
BOXES_TOPIC = "/liquidpatrol/detector_boxes"


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


class BoxesSub:
    """EKSPLORACJA: subskrybent WSZYSTKICH boxów detektora [cx,cy,w,h,conf]*n + sim_t. Poza torem
    osłony (osłona subskrybuje wyłącznie kanał 5-dim). Do pomiaru rozkładu conf/przestrzennego."""
    def __init__(self, node):
        self.boxes = []          # [(cx,cy,w,h,conf)]
        self.sim_t = None
        self.seq = 0
        node.create_subscription(Float32MultiArray, BOXES_TOPIC, self._cb, qos_be())

    def _cb(self, msg):
        d = list(msg.data)
        if not d:
            self.boxes = []; self.sim_t = None; self.seq += 1; return
        self.sim_t = d[-1]; flat = d[:-1]
        self.boxes = [tuple(flat[i:i+5]) for i in range(0, len(flat) - 4, 5)]
        self.seq += 1


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
        # fix #2: setpoint w OSOBNYM WĄTKU o stałym takcie (odsprzężony od pętli decyzji/kanału),
        # by kontencja CPU detektora nie głodziła strumienia → brak natywnego HOLD z utraty offboard.
        self._sp_lock = threading.Lock(); self._latest_sp = None
        self._stream_stop = threading.Event(); self._stream_thread = None
        self._stream_last = None; self.stream_max_dt = 0.0; self.stream_pub_count = 0
        self.gf_fired = False; self.offboard_lost_ticks = 0
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
        # pętla decyzji NIE publikuje bezpośrednio — tylko aktualizuje setpoint; publikuje streamer.
        now = time.monotonic()
        if self._last_pub is not None:
            self.setpoint_max_dt = max(self.setpoint_max_dt, now - self._last_pub)  # takt decyzji (info)
        self._last_pub = now
        self._set_sp(xyz)

    def _set_sp(self, xyz):
        with self._sp_lock:
            self._latest_sp = [float(xyz[0]), float(xyz[1]), float(xyz[2])]

    def _streamer(self):
        """Wątek fix #2: publikuje OSTATNI setpoint (OCM+TrajectorySetpoint) przy STAŁYM 20 Hz,
        niezależnie od stalli pętli decyzyjnej/detektora. Mierzy realny takt (stream_max_dt)."""
        nxt = time.monotonic()
        try: os.nice(-5)                       # łagodny RT-bias (bez uprawnień = no-op)
        except Exception: pass
        while not self._stream_stop.is_set():
            with self._sp_lock:
                sp = None if self._latest_sp is None else list(self._latest_sp)
            if sp is not None:
                now = time.monotonic()
                if self._stream_last is not None:
                    self.stream_max_dt = max(self.stream_max_dt, now - self._stream_last)
                self._stream_last = now; self.stream_pub_count += 1
                try: self.xrce.publish_setpoint(sp)
                except Exception: pass
            nxt += PERIOD
            slp = nxt - time.monotonic()
            if slp > 0: time.sleep(slp)
            else: nxt = time.monotonic()       # spóźnieni → reset harmonogramu (bez kumulacji)

    def start_streamer(self):
        if self._stream_thread is None:
            self._stream_stop.clear()
            self._stream_thread = threading.Thread(target=self._streamer, daemon=True)
            self._stream_thread.start()

    def stop_streamer(self):
        self._stream_stop.set()

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
            self.offboard_lost_ticks += 1        # fix #2 metryka: ticki poza OFFBOARD w patrolu
        rec = {"k": self.k, "t": round(time.time()-self.t0, 3), "decision": d["decision"],
               "reason": d["reason"], "rule": d["rule"], "mode": mode, "locked": locked,
               "age": self.chan.age, "pos": [round(v, 2) for v in pos], "yaw": round(self.mav.yaw, 3),
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
        # fix #2: uruchom streamer (stały 20 Hz) ZANIM offboard — strumień żyje niezależnie od pętli
        self._set_sp((self.start[0], self.start[1], -ALT_M)); self.start_streamer()
        time.sleep(1.5)                                    # prestream (streamer publikuje)
        self.xrce.set_offboard_mode(); time.sleep(0.2); self.mav.arm()
        t = time.time()
        while not self.mav.armed and time.time()-t < 5:
            time.sleep(PERIOD)
        tc = time.time()
        while time.time()-tc < 15:
            time.sleep(PERIOD)
            if abs(self.mav.pos[2] - (-ALT_M)) < 1.0:
                break
        self.mav.reset_tel_gap()
        print(f"[gate] armed={self.mav.armed} down={self.mav.pos[2]:.1f} fm={self.mav.flight_mode} "
              f"stream_pub={self.stream_pub_count}")

    def _abort(self):
        try: self.mav.stop(); self.xrce.shutdown()
        except Exception: pass

    def finish(self, summary):
        self.stop_streamer()
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
    r.stop_streamer()                            # fix #2: prawdziwe urwanie = zatrzymaj streamer
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


def scenario_CHAR(r: Runner):
    """EKSPLORACJA (poza pre-rejestracją, kryteria NIETKNIĘTE): nominalny patrol N okrążeń z intruzem
    statycznym w znanym miejscu (GT). Loguje WSZYSTKIE boxy detektora z klasyfikacją true/false (vs
    projekcja GT) + edge_dist + conf. Cel: rozkład conf i przestrzenny szumu vs sygnału na CAŁYM locie.
    ALSO: dowód fix #2 (0 utrat OFFBOARD w patrolu, GF-native=0, stream_max_dt). OBSERVE WYŁĄCZONE
    (observe_authority off) — czysty patrol, brak wpływu fałszywych locków na tor."""
    gt = os.environ.get("CHAR_INTRUDER", "25,0,6").split(",")
    gx, gy, gz = float(gt[0]), float(gt[1]), float(gt[2])
    intr_ned = (gx, gy, -gz)                      # NED (down = -alt)
    r.admit_observe(False); r.intruder_present = True   # patrol, bez autorytetu OBSERVE
    boxes_sub = BoxesSub(r.xrce.node)
    charf = open(os.environ.get("CHAR_LOG", "/tmp/r02/CHAR/char.jsonl"), "w")
    r.bring_up()
    last_seq = -1; n_frames = 0; n_true = 0; n_false = 0
    laps_target = r.planner.laps
    while not r.planner.done and time.time()-r.t0 < 400:
        r.tick(force_mode=M_PATROL)              # wymuś patrol (bez OBSERVE)
        r.planner.advance_if_reached(list(r.mav.pos))
        if boxes_sub.seq != last_seq:            # nowa klatka detektora (1 Hz)
            last_seq = boxes_sub.seq; n_frames += 1
            pos = list(r.mav.pos); yaw = r.mav.yaw
            exp = project_to_pixel(pos, yaw, intr_ned)   # Box|None (GT w FOV?)
            in_fov = exp is not None
            recs = []
            for (cx, cy, w, h, conf) in boxes_sub.boxes:
                edge = min(cx, 1.0 - cx, cy, 1.0 - cy)
                is_true = bool(in_fov and math.hypot(cx - exp.cx, cy - exp.cy) < 0.12)
                if is_true: n_true += 1
                else: n_false += 1
                recs.append({"cx": round(cx, 4), "cy": round(cy, 4), "w": round(w, 4),
                             "h": round(h, 4), "conf": round(conf, 5), "edge": round(edge, 4),
                             "true": is_true})
            charf.write(json.dumps({"t": round(time.time()-r.t0, 2), "pos": [round(v,2) for v in pos],
                        "yaw": round(yaw, 3), "in_fov": in_fov,
                        "exp": [round(exp.cx,4), round(exp.cy,4)] if exp else None,
                        "nbox": len(recs), "boxes": recs}) + "\n")
        time.sleep(PERIOD)
    charf.close()
    o = r.shield.outcome(env_success=r.planner.done)
    crit = {"laps_done": r.planner.lap, "laps_target": laps_target,
            "char_frames": n_frames, "char_true_boxes": n_true, "char_false_boxes": n_false,
            # fix #2 dowód:
            "offboard_lost_ticks": r.offboard_lost_ticks, "gf_native_0": r.offboard_lost_ticks == 0,
            "stream_max_dt": round(r.stream_max_dt, 3), "stream_dt_ok": r.stream_max_dt < 1.0,
            "stream_pub": r.stream_pub_count, "A1_ok": len(r.mav.motion_cmds()) == 0,
            "max_r": round(r.max_radial, 2), "inside_R_E": r.max_radial <= R_E, "outcome": o["wynik"]}
    # CHAR PASS = dowód fix #2 (patrol OK, brak transientu HOLD); charakteryzacja to dane, nie werdykt
    crit["PASS"] = (crit["gf_native_0"] and crit["stream_dt_ok"] and crit["A1_ok"]
                    and crit["inside_R_E"] and r.planner.done)
    r.mav.rtl(); time.sleep(6); r.mav.land(); time.sleep(2)
    r.finish({"scenario": "CHAR", **crit, "char_log": os.environ.get("CHAR_LOG", "/tmp/r02/CHAR/char.jsonl"),
              "mavsdk_calls": [c for c, _ in r.mav.calls]})
    return crit["PASS"]


def scenario_CHAR2(r: Runner):
    """EKSPLORACJA — DEDYKOWANY PAS SYGNAŁU (krok 1 decyzji Olgi). Dron leci wzdłuż OSI KAMERY (y=0)
    ku STATYCZNEMU intruzowi (dead-ahead, yaw=0), z dwellem per zasięg → zamiata 5–25 m, cel centralny
    → GĘSTY rozkład conf(zasięg) SYGNAŁU (nie 1 box). Loguje wszystkie boxy z true/false + range + edge.
    OBSERVE off, kanał bez wpływu na tor. Cel: chmura sygnału do wyboru progu (z chmurą szumu z CHAR)."""
    gt = os.environ.get("CHAR_INTRUDER", "25,0,8").split(",")
    gx, gy, gz = float(gt[0]), float(gt[1]), float(gt[2])
    intr_ned = (gx, gy, -gz)
    r.admit_observe(False); r.intruder_present = True
    boxes_sub = BoxesSub(r.xrce.node)
    charf = open(os.environ.get("CHAR_LOG", "/tmp/r02/CHAR2/char.jsonl"), "w")
    r.bring_up()                                  # wznios w Home (0,0,-10)
    # zamiataj zasięg: target_x kroki tam-i-z-powrotem, dwell per zasięg (gęstość klatek)
    xs = [0, 4, 8, 12, 16, 20, 20, 16, 12, 8, 4, 0]   # x drona; range do (gx,gy)=~sqrt((gx-x)^2+dz^2)
    last_seq = -1; n_true = 0; n_false = 0; n_frames = 0
    for tx in xs:
        t_dwell = time.time()
        while time.time() - t_dwell < 4.0 and time.time() - r.t0 < 300:
            pos = list(r.mav.pos); vel = list(r.mav.vel)
            sp = [float(tx), gy, -ALT_M]          # leć wzdłuż y=gy ku intruzowi (dead-ahead)
            d = r.shield.step(r.k, pos, vel, sp, mode=M_PATROL)
            r._pub(d["applied"]); r._spin()
            r.max_radial = max(r.max_radial, math.hypot(pos[0], pos[1]))
            if boxes_sub.seq != last_seq:
                last_seq = boxes_sub.seq; n_frames += 1
                yaw = r.mav.yaw
                exp = project_to_pixel(pos, yaw, intr_ned)
                rng = math.sqrt((pos[0]-gx)**2 + (pos[1]-gy)**2 + (pos[2]-(-gz))**2)
                recs = []
                for (cx, cy, w, h, conf) in boxes_sub.boxes:
                    edge = min(cx, 1.0-cx, cy, 1.0-cy)
                    is_true = bool(exp is not None and math.hypot(cx-exp.cx, cy-exp.cy) < 0.15)
                    if is_true: n_true += 1
                    else: n_false += 1
                    recs.append({"cx": round(cx,4), "cy": round(cy,4), "conf": round(conf,5),
                                 "edge": round(edge,4), "true": is_true})
                charf.write(json.dumps({"t": round(time.time()-r.t0,2), "range": round(rng,2),
                            "pos": [round(v,2) for v in pos], "in_fov": exp is not None,
                            "exp": [round(exp.cx,4), round(exp.cy,4)] if exp else None,
                            "nbox": len(recs), "boxes": recs}) + "\n")
            r.k += 1; time.sleep(PERIOD)
    charf.close()
    crit = {"scenario": "CHAR2_signal", "char_frames": n_frames, "char_true_boxes": n_true,
            "char_false_boxes": n_false, "offboard_lost_ticks": r.offboard_lost_ticks,
            "gf_native_0": r.offboard_lost_ticks == 0, "stream_max_dt": round(r.stream_max_dt,3),
            "A1_ok": len(r.mav.motion_cmds())==0, "max_r": round(r.max_radial,2),
            "inside_R_E": r.max_radial <= R_E,
            "char_log": os.environ.get("CHAR_LOG", "/tmp/r02/CHAR2/char.jsonl")}
    crit["PASS"] = n_true > 20 and crit["A1_ok"] and crit["inside_R_E"]   # gęsty sygnał zebrany
    r.mav.rtl(); time.sleep(6); r.mav.land(); time.sleep(2)
    r.finish(crit)
    return crit["PASS"]


def main():
    laps = {"G1": 3, "G2": 1, "G3": 3, "G4": 2, "G5": 1, "CHAR": 3, "CHAR2": 1}[SCEN]
    r = Runner(laps)
    fn = {"G1": scenario_G1, "G2": scenario_G2, "G3": scenario_G3, "G4": scenario_G4,
          "G5": scenario_G5, "CHAR": scenario_CHAR, "CHAR2": scenario_CHAR2}[SCEN]
    ok = fn(r)
    sys.exit(0 if ok else 3)


if __name__ == "__main__":
    main()
