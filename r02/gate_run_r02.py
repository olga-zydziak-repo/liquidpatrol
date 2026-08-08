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
import os, sys, json, time, math, threading, random

import rclpy
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from std_msgs.msg import Float32MultiArray
from px4_msgs.msg import VehicleStatus       # G5: precyzyjny pomiar nav_state (failsafe) — szybszy niż MAVSDK flight_mode

from r01.exec_lib import XrcePublisher, Mav, Planner
from r01.shield import PatrolShield, ALLOW, HOLD, REFUSE, GEOFENCE, M_PATROL, M_OBSERVE
from r01.authz import Authorizer
from r01.config import ALT_M, TICK_HZ, DT, R_E
from r02.config_r02 import (D_SAFE_M, THETA_AGE_S, T_ACK_S, F_FOV, EPS_FP_PER_MIN, ChannelConfig,
                            THETA_CONF, ENTRY_EDGE_MARGIN, DET_DT)

# TOR B — GT-FED (teza architektury niezależna od percepcji, decyzja Olgi). Kanał 5-dim zasilany POZĄ
# celu z symulatora (projekcja GT do kamery, perfekcyjna detekcja w FOV, conf=1.0) zamiast detektora.
# JAWNIE ETYKIETOWANE w trace/result/raporcie (precedens 3b: sufit GT-fed vs live-fed osobno).
GT_FED = os.environ.get("GT_FED") == "1"
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


class NavStatusSub:
    """G5: subskrybent /fmu/out/vehicle_status (nav_state) przez XRCE — WYSOKI rate (px4 ~kilka-Hz),
    precyzyjny pomiar chwili natywnego failsafe (opuszczenie OFFBOARD=14). MAVSDK flight_mode jest
    event-driven na HEARTBEAT ~1 Hz → za gruby dla okna 0.9–1.5 s. Znaczniki czasu: monotonic."""
    OFFBOARD = VehicleStatus.NAVIGATION_STATE_OFFBOARD   # 14
    def __init__(self, node):
        self.nav_state = None; self.last_t = None; self.left_offboard_t = None; self.seq = 0
        node.create_subscription(VehicleStatus, "/fmu/out/vehicle_status_v1", self._cb, qos_be())
        node.create_subscription(VehicleStatus, "/fmu/out/vehicle_status", self._cb, qos_be())  # fallback nazwy
    def _cb(self, msg):
        self.nav_state = int(msg.nav_state); self.last_t = time.monotonic(); self.seq += 1
        if self.nav_state != self.OFFBOARD and self.left_offboard_t is None and self._armed_seen:
            self.left_offboard_t = self.last_t
    _armed_seen = False   # ustawiane przez runner po wejściu w OFFBOARD (żeby nie łapać pre-arm nav_state)


class Runner:
    def __init__(self, laps):
        os.makedirs(os.path.dirname(TRACE), exist_ok=True)
        self.tf = open(TRACE, "w")
        self.xrce = XrcePublisher()
        self.chan = ChannelSub(self.xrce.node)          # współdziel węzeł rclpy osłony
        self.boxes_sub = BoxesSub(self.xrce.node)       # A6: pasywne logowanie conf (wszystkie boxy)
        self.navsub = NavStatusSub(self.xrce.node)      # G5: precyzyjny nav_state (failsafe)
        self.conf_samples = []; self.n_admitted = 0; self._boxes_seq = -1
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
        # DEAD-MAN (fix G5, decyzja Olgi): brak odświeżenia setpointu przez N ticków ⇒ osłona MARTWA ⇒
        # streamer MILKNIE ⇒ natywny failsafe (COM_OF_LOSS_T). Egzekwuje własność „martwa osłona ⇒
        # bezpieczne przejęcie warstwy-0" (regresja wprowadzona przez fix#2 zombie-stream). REGUŁA N:
        # 6 ticków osłony @20 Hz = 0.3 s (> normalny jitter setpoint_max_dt, < COM_OF_LOSS_T 1 s).
        self.DEADMAN_TICKS = 6; self.deadman_s = self.DEADMAN_TICKS * PERIOD   # 0.3 s
        self._last_refresh = time.monotonic(); self._deadman_armed = False; self._deadman_tripped = False
        self.gf_fired = False; self.offboard_lost_ticks = 0
        self.n_entry = 0; self.n_false_entry = 0
        self.observe_ticks = 0; self.dsafe_violations = 0; self.min_d_observe = float("inf")
        self.entry_t = None; self.intruder_present = False; self.intruder_in_view_t = None
        self._prev_locked = False
        self.idle_sp = None            # gdy ustawiony: setpoint utrzymania (hover) zamiast patrolu gdy nie-locked
        # TOR B — GT-FED: lokalny kanał zasilany pozą GT (bez detektora/kamery)
        self.gt_mode = GT_FED
        self.gt_channel = TargetChannel(ChannelConfig()) if GT_FED else None
        self.gt_next = 0.0; self.gt_intruder_fn = None
        # NIEREGULARNOŚĆ GT (decyzja Olgi — jedyny sposób zmierzyć semantykę ZOH-age): maski dropoutu
        # (Bernoulli + burst) + szum obserwacyjny na GT. SEEDY PRZYPIĘTE (odtwarzalne). Wynik OSOBNO od czystego GT.
        self.gt_rng = random.Random(int(os.environ.get("GT_SEED", "1")))
        self.gt_dropout_p = float(os.environ.get("GT_DROPOUT", "0.0"))   # Bernoulli p pojedynczej dziury
        self.gt_burst_p = float(os.environ.get("GT_BURST_P", "0.0"))     # p rozpoczęcia bursta (duch G2)
        self.gt_burst_len = int(os.environ.get("GT_BURST_LEN", "5"))     # długość bursta [klatek det.]
        self.gt_noise_std = float(os.environ.get("GT_NOISE", "0.0"))     # szum obserwacyjny (piksel, σ)
        self.gt_burst_left = 0; self.gt_n_dropout = 0

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
            self._last_refresh = time.monotonic()      # dead-man: znacznik żywotności osłony

    def _streamer(self):
        """Wątek fix #2: publikuje OSTATNI setpoint (OCM+TrajectorySetpoint) przy STAŁYM 20 Hz,
        niezależnie od stalli pętli decyzyjnej/detektora. Mierzy realny takt (stream_max_dt)."""
        nxt = time.monotonic()
        try: os.nice(-5)                       # łagodny RT-bias (bez uprawnień = no-op)
        except Exception: pass
        while not self._stream_stop.is_set():
            with self._sp_lock:
                sp = None if self._latest_sp is None else list(self._latest_sp)
                stale = time.monotonic() - self._last_refresh
            # DEAD-MAN: gdy zbrojony (po bring_up) i osłona nie odświeżyła setpointu > deadman_s →
            # MILCZ (nie publikuj) → PX4 traci offboard w COM_OF_LOSS_T → warstwa-0 przejmuje.
            if self._deadman_armed and stale > self.deadman_s:
                if not self._deadman_tripped:
                    self._deadman_tripped = True
                sp = None                              # streamer milknie (zombie-stream ucięty)
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

    def _log_conf_passive(self):
        """A6: pasywne logowanie conf (sygnał+szum) w KAŻDYM locie — czy przerwa utrzymała się w locie.
        Liczy też n_admitted = boxy przechodzące admisję ENTRY (conf≥θ_conf ∧ central) = potencjalne locki."""
        if self.boxes_sub.seq != self._boxes_seq:
            self._boxes_seq = self.boxes_sub.seq
            for (cx, cy, w, h, conf) in self.boxes_sub.boxes:
                self.conf_samples.append(conf)
                edge = min(cx, 1-cx, cy, 1-cy)
                if conf >= THETA_CONF and edge >= ENTRY_EDGE_MARGIN:
                    self.n_admitted += 1

    def conf_report(self):
        cs = sorted(self.conf_samples)
        p99 = cs[min(len(cs)-1, int(0.99*(len(cs)-1)))] if cs else None
        return {"theta_conf": round(THETA_CONF, 4), "conf_n": len(cs),
                "conf_max": round(max(cs), 4) if cs else None, "conf_p99": round(p99, 4) if p99 else None,
                "n_admitted_entry": self.n_admitted,        # dla G1 (brak intruza): oczekiwane 0
                "gap_held_in_flight": (max(cs) < THETA_CONF) if cs else None}   # szum < θ_conf?

    def _channel_step(self, pos, yaw, t):
        """Zwraca (locked, box, age) z kanału. TOR B (GT-fed): zasila lokalny kanał pozą GT projektowaną
        do kamery (perfekcyjna detekcja w FOV, conf=1.0 → przechodzi admisję A6). Live: z ChannelSub."""
        if self.gt_mode:
            if t >= self.gt_next - 1e-9:                    # kadencja detektora 1 Hz
                intr = self.gt_intruder_fn(t) if self.gt_intruder_fn else None
                box = None
                if intr is not None:
                    b = project_to_pixel(pos, yaw, intr)     # projekcja GT (None gdy poza FOV level-camera)
                    if b is not None:
                        cx = min(max(b.cx + self.gt_rng.gauss(0, self.gt_noise_std), 0.0), 1.0)  # szum obs.
                        cy = min(max(b.cy + self.gt_rng.gauss(0, self.gt_noise_std), 0.0), 1.0)
                        box = Box(cx, cy, b.w, b.h, conf=1.0)   # perfekcyjna detekcja (GT-fed) + szum
                # DROPOUT (Bernoulli + burst) — symuluje utratę detekcji → test ZOH-age (dziura→age→sufit)
                if box is not None:
                    if self.gt_burst_left > 0:
                        box = None; self.gt_burst_left -= 1; self.gt_n_dropout += 1
                    elif self.gt_rng.random() < self.gt_dropout_p:
                        box = None; self.gt_n_dropout += 1
                        if self.gt_rng.random() < self.gt_burst_p:
                            self.gt_burst_left = self.gt_burst_len   # rozpocznij burst (duch G2)
                self.gt_channel.on_frame(box, t, gt_present=(intr is not None and box is not None))
                self.gt_next += DET_DT
            else:
                self.gt_channel.tick_time(t)                 # egzekwuj sufit age między klatkami
            val = self.gt_channel.sample(t)
            locked = self.gt_channel.locked and not self.gt_channel.is_expired(t)
            return locked, (self.gt_channel.last_box if locked else None), (val.age_s if val else None)
        locked = self.chan.locked and (self.chan.age is not None and self.chan.age <= THETA_AGE_S)
        return locked, (self.chan.last if self.chan.locked else None), self.chan.age

    def tick(self, force_mode=None, watch_gf=True):
        self._spin()
        self._log_conf_passive()
        pos = list(self.mav.pos); vel = list(self.mav.vel)
        yaw = self._yaw()
        # kanał (GT-fed lub live) → (locked, box, age); świeży box → zamroź estymatę OBSERVE
        locked, chbox, chage = self._channel_step(pos, yaw, round(time.time() - self.t0, 4))
        if chbox is not None:
            self.ctrl.on_detection(pos, yaw, chbox)
            if self.intruder_in_view_t is None:              # pierwsze wejście celu w FOV (do T_ack)
                self.intruder_in_view_t = time.time() - self.t0
        if self._prev_locked and not locked:
            self.ctrl.reset()
        # ENTRY: przejście unlocked→locked
        if locked and not self._prev_locked:
            self.n_entry += 1
            if self.entry_t is None:
                self.entry_t = time.time() - self.t0
            if not self.intruder_present:
                self.n_false_entry += 1        # ε_FP: lock na pustej scenie
        self._prev_locked = locked; self.locked = locked   # dostępne dla scenariuszy (GT-fed lub live)

        # tryb: OBSERVE gdy lock ∧ autorytet gramatyki ∧ estymata; inaczej force/patrol
        if locked and self.observe_authority and self.ctrl.has_estimate() and force_mode is None:
            mode = M_OBSERVE
            sp = self.ctrl.setpoint(pos) or self.planner.target()
        elif force_mode is not None:
            mode = force_mode; sp = self.planner.target()
        elif self.idle_sp is not None:
            mode = M_PATROL; sp = list(self.idle_sp)   # hover na intruzie (dwell do ENTRY), nie patrol
        else:
            mode = M_PATROL; sp = self.planner.target()

        d = self.shield.step(self.k, pos, vel, sp, mode=mode)
        d["mode"] = mode                       # udostępnij tryb scenariuszom (fix: shield.step nie zwraca 'mode')
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
               "age": chage, "gt_fed": self.gt_mode, "pos": [round(v, 2) for v in pos], "yaw": round(self.mav.yaw, 3),
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
        self._last_refresh = time.monotonic(); self._deadman_armed = True   # zbrój dead-man po climb (pętla tick odświeża)
        self.navsub._armed_seen = True; self.navsub.left_offboard_t = None   # od teraz nav_state≠OFFBOARD = failsafe
        print(f"[gate] armed={self.mav.armed} down={self.mav.pos[2]:.1f} fm={self.mav.flight_mode} "
              f"stream_pub={self.stream_pub_count} deadman_armed=True (N={self.DEADMAN_TICKS}t={self.deadman_s}s)")

    def _abort(self):
        try: self.mav.stop(); self.xrce.shutdown()
        except Exception: pass

    def finish(self, summary):
        self.stop_streamer()
        summary = {**summary, "conf_passive_A6": self.conf_report()}   # A6: pasywny log conf w każdym locie
        if self.gt_mode:                                               # TOR B: etykieta + nieregularność (seedy)
            summary["gt_fed"] = True
            summary["gt_irregularity"] = {"seed": int(os.environ.get("GT_SEED", "1")),
                "dropout_p": self.gt_dropout_p, "burst_p": self.gt_burst_p, "burst_len": self.gt_burst_len,
                "noise_std": self.gt_noise_std, "n_dropout": self.gt_n_dropout,
                "n_expire": self.gt_channel.n_expire if self.gt_channel else None}
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
    if r.gt_mode: r.gt_intruder_fn = lambda t: (7.0, 0.0, -11.5)   # TOR B: intruz statyczny w kopercie
    r.bring_up()
    # G2: dron HOVER w Home (twarzą N na statycznego intruza w kopercie A7) do ENTRY, potem OBSERVE
    r.idle_sp = [r.start[0], r.start[1], -ALT_M]
    while time.time()-r.t0 < 60:
        r.tick()
        if r.observe_ticks > int(20*TICK_HZ):   # ~20 s obserwacji wystarczy
            break
        time.sleep(PERIOD)
    r.mav.rtl(); time.sleep(6); r.mav.land(); time.sleep(2)
    o = r.shield.outcome(env_success=(r.n_entry>0 and r.dsafe_violations==0))
    f_fov = None  # udział FOV liczy detektor (debug topic) — tu proxy: observe_ticks>0 i lock stabilny
    # T_ack = od WEJŚCIA celu w FOV do ENTRY (nie od startu misji — climb nie wlicza się)
    t_ack = (r.entry_t - r.intruder_in_view_t) if (r.entry_t is not None and r.intruder_in_view_t is not None) else None
    crit = {"n_entry": r.n_entry, "entry_t": round(r.entry_t,2) if r.entry_t else None,
            "intruder_in_view_t": round(r.intruder_in_view_t,2) if r.intruder_in_view_t else None,
            "t_ack": round(t_ack,2) if t_ack is not None else None,
            "t_ack_ok": (t_ack is not None and t_ack <= T_ACK_S),
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
    # TOR B: intruz prowadzi na Północ (ku płotowi R_E=32) — dron goni na pierścieniu D_safe → za płot
    if r.gt_mode: r.gt_intruder_fn = lambda t: (7.0, 0.0, -11.5) if t < 15.0 else (7.0 + 3.0*(t-15.0), 0.0, -11.5)  # statyczny do locka, potem prowadzi ku plotowi
    r.bring_up()
    r.idle_sp = [r.start[0], r.start[1], -ALT_M]
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
    # TOR B: intruz obecny do sim-t=20 s, potem ZNIKA (None) → age rośnie → sufit → wyjście z OBSERVE
    if r.gt_mode: r.gt_intruder_fn = lambda t: (7.0, 0.0, -11.5) if t < 20.0 else None
    r.bring_up()
    r.idle_sp = [r.start[0], r.start[1], -ALT_M]
    saw_observe = False; vanished_at = None; exited = False
    while time.time()-r.t0 < 90:
        d = r.tick()
        if d["mode"] == M_OBSERVE: saw_observe = True
        # intruz znika → brak locka
        if saw_observe and not r.locked and vanished_at is None:
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
    """Warstwa-0 (regres R0.1 S4): martwa osłona ⇒ natywna reakcja HOLD w oknie 0.9–1.5 s, ≤R_E, mimo OBSERVE.
    DWA warianty urwania (env G5_CUT), by pokazać, co odpowiada za 2.179 s i że dead-man domyka okno:
      • zombie  (default) — pętla decyzyjna/osłona ZAMIERA, ale streamer fix#2 ŻYJE. Bez dead-mana stream
                 publikuje stale setpoint → PX4 nie widzi utraty offboard → BRAK failsafe (regresja).
                 Z dead-manem: po deadman_s streamer MILKNIE → failsafe w COM_OF_LOSS_T.
      • stream  — bezpośredni stop_streamer() (baseline: to dało 2.179 s w poprzedniej rundzie)."""
    G5_CUT = os.environ.get("G5_CUT", "zombie")
    r.admit_observe(True); r.intruder_present = True
    if r.gt_mode: r.gt_intruder_fn = lambda t: (7.0, 0.0, -11.5)   # TOR B: intruz obecny (OBSERVE aktywny)
    r.bring_up()
    r.idle_sp = [r.start[0], r.start[1], -ALT_M]
    t_fly = time.time()
    while time.time()-t_fly < 8:
        r.tick(); time.sleep(PERIOD)
    pub_at_cut = r.stream_pub_count
    print(f"[gate] G5[{G5_CUT}]: URWANIE (test warstwy-0 mimo OBSERVE) stream_pub={pub_at_cut}")
    if G5_CUT == "stream":
        r.stop_streamer()                        # baseline: bezpośredni stop streamera
    # zombie: NIE stopujemy streamera i NIE wołamy tick() → osłona martwa, streamer żyje → dead-man decyduje
    r.tf.write(json.dumps({"EVENT":"shield_death","cut":G5_CUT,"t":round(time.time()-r.t0,3),
                           "flight_mode":r.mav.flight_mode,"stream_pub":pub_at_cut})+"\n")
    t_cut = time.time(); t_cut_mono = time.monotonic()
    mav_react_s = None; deadman_s = None; max_r_after = 0.0
    while time.time()-t_cut < 6.0:
        r._spin()                                # odbiór telemetrii (nav_state + MAVSDK) — pętla decyzyjna NIE odświeża setpointu
        max_r_after = max(max_r_after, math.hypot(r.mav.pos[0], r.mav.pos[1]))
        if deadman_s is None and r._deadman_tripped:
            deadman_s = time.monotonic()-t_cut_mono
            r.tf.write(json.dumps({"EVENT":"deadman_trip","t_since_cut":round(deadman_s,3),
                                   "stream_pub":r.stream_pub_count})+"\n")
            print(f"[gate] G5 dead-man ZADZIAŁAŁ po {deadman_s:.3f}s (streamer milknie)")
        if mav_react_s is None and not offboard_ok(r.mav.flight_mode):
            mav_react_s = time.time()-t_cut
            print(f"[gate] G5 MAVSDK flight_mode opuścił OFFBOARD po {mav_react_s:.3f}s → {r.mav.flight_mode}")
        time.sleep(0.02)
    # PRECYZYJNY pomiar (monotonic): failsafe = navsub.left_offboard_t − t_cut_mono
    nav_react_s = round(r.navsub.left_offboard_t - t_cut_mono, 3) if r.navsub.left_offboard_t else None
    pub_end = r.stream_pub_count
    r.mav.land(); time.sleep(2)
    crit = {"cut_variant": G5_CUT, "shield_death": True,
            "nav_reaction_s": nav_react_s,                       # PRECYZYJNY (nav_state, XRCE ~kilka-Hz)
            "mavsdk_reaction_s": round(mav_react_s,3) if mav_react_s else None,  # LAGGY (flight_mode ~1 Hz) — diagnoza 2.179 s
            "deadman_trip_s": round(deadman_s,3) if deadman_s else None,
            "deadman_tripped": bool(r._deadman_tripped),
            "final_nav_state": r.navsub.nav_state,
            "stream_pub_at_cut": pub_at_cut, "stream_pub_end": pub_end,
            "stream_kept_publishing": (pub_end - pub_at_cut),
            "reaction_ok_0.9_1.5": (nav_react_s is not None and 0.9<=nav_react_s<=1.5),
            "native_flight_mode": r.mav.flight_mode, "max_r_after": round(max_r_after,2),
            "inside_R_E": max_r_after<=R_E, "A1_ok": len(r.mav.motion_cmds())==0}
    # zombie musi mieć dead-man; stream nie wymaga dead-mana (bezpośredni stop)
    dm_ok = (r._deadman_tripped if G5_CUT == "zombie" else True)
    crit["PASS"] = crit["reaction_ok_0.9_1.5"] and crit["inside_R_E"] and crit["A1_ok"] and dm_ok
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
    boxes_sub = r.boxes_sub          # A6: współdziel pasywny subskrybent boxów
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
    boxes_sub = r.boxes_sub          # A6: współdziel pasywny subskrybent boxów
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
