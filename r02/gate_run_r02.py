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
from sensor_msgs.msg import Image            # C-A1 (tor C): capture surowej klatki dla overlay projekcji
from px4_msgs.msg import VehicleStatus       # G5: precyzyjny pomiar nav_state (failsafe) — szybszy niż MAVSDK flight_mode

from r01.exec_lib import XrcePublisher, Mav, Planner
from r01.shield import PatrolShield, ALLOW, HOLD, REFUSE, GEOFENCE, NO_AUTH, M_PATROL, M_OBSERVE
from r01.authz import Authorizer
from r01.config import ALT_M, TICK_HZ, DT, R_E
from r02.config_r02 import (D_SAFE_M, THETA_AGE_S, T_ACK_S, F_FOV, EPS_FP_PER_MIN, ChannelConfig,
                            THETA_CONF, ENTRY_EDGE_MARGIN, DET_DT, DEADMAN_TICKS)

# TOR B — GT-FED (teza architektury niezależna od percepcji, decyzja Olgi). Kanał 5-dim zasilany POZĄ
# celu z symulatora (projekcja GT do kamery, perfekcyjna detekcja w FOV, conf=1.0) zamiast detektora.
# JAWNIE ETYKIETOWANE w trace/result/raporcie (precedens 3b: sufit GT-fed vs live-fed osobno).
GT_FED = os.environ.get("GT_FED") == "1"

# ANEKS_D5 §4a (ratyf. 2026-08-17): kadencja DECYZYJNA toru aktów LIVE = 2.0 Hz == REGATE DECISION_HZ
# (mti_flight.py L41). Restauracja charakteryzacji (klasa §1.1): DET_HZ w config_r02 NIETKNIĘTY (1 Hz =
# default R0.2); tu jedno źródło dla --det-hz detektora ORAZ echa manifestu (bez driftu). Bieg z
# det_hz≠2.0 = INVALID z definicji (SR §4). k=3 @2 Hz → okno ENTRY 1.5 s (jak REGATE), nie 3 s.
DEMO_DECISION_HZ = 2.0
# ANEKS_D5 §5a (ratyf. 2026-08-18): kadencja RUCHU intruza (teleport) toru aktów == REGATE replacer
# (mti_flight.py: `time.sleep(0.06)` ≈ 16.7 Hz). Restauracja charakteryzacji (klasa §4a/§1.1): teleport
# @2 Hz dawał cel STATYCZNY ~7/7.5 klatek (kamera 15 Hz) → filtr trwałości MTI (persist_m/window) odrzucał
# izolowany ruch skokowy → n_comps=0 in-window → brak ENTRY (RAPORT_D_B5 §FINAL). Oscylacja
# 1.5·sin(2π·0.3·t) BEZ ZMIAN — zmienia się WYŁĄCZNIE gęstość jej próbkowania. Echo teleport_hz w
# manifeście; bieg z teleport_hz≠16.7 = INVALID z definicji.
DEMO_TELEPORT_DT = 0.06
DEMO_TELEPORT_HZ = round(1.0 / DEMO_TELEPORT_DT, 1)   # 16.7 Hz (== REGATE mti_flight.replacer)
from r02.target_channel import TargetChannel, Box
from r02.observe_guidance import ObserveController
from r02.gate_harness import project_to_pixel   # EKSPLORACJA: projekcja GT intruza (klasyfikacja true/false)

SCEN = os.environ.get("SCENARIO", "G1")
TRACE = os.environ.get("TRACE", f"/tmp/r02/gate_{SCEN}.jsonl")
PERIOD = DT
CH_TOPIC = "/liquidpatrol/target_channel"
BOXES_TOPIC = "/liquidpatrol/detector_boxes"

# --- TRACE SCHEMA (DEMO-B B3, PROMPT_D_BUILD_3 §1) ---------------------------
# Wersjonowany schemat trace gate_live. Zmiana pól ⇒ bump + wpis w changelogu.
#   v1 (pre-B3): tick rec {k,t,decision,reason,rule,mode,locked,age,gt_fed,pos,yaw,applied,r_pos,
#                flight_mode,min_d}; +B1: {auth_ok,admission_seq}; event rows {event: token_issued|
#                token_consumed|refuse_no_auth}.
#   v2 (B3, patche PRE_D §4): +tick (a) state(str automatu), (b) conj{box,central,mti_ok}(bool|null),
#                (f) intr_ned([x,y,z] m NED | null). (c) age i (d) min_d już były. Pola nowe OPCJONALNE
#                (zgodność wsteczna: parser czyta v1 bez wywrotki — .get z domyślną).
TRACE_SCHEMA_V = 2
TRACE_TICK_FIELDS = ["k", "t", "decision", "reason", "rule", "mode", "state", "locked", "age",
                     "conj", "intr_ned", "gt_fed", "pos", "yaw", "applied", "r_pos", "flight_mode",
                     "min_d", "auth_ok", "admission_seq"]
TRACE_EVENT_TYPES = ["token_issued", "token_consumed", "refuse_no_auth"]


def offboard_ok(fm):
    return fm is not None and "OFFBOARD" in fm


def project_full_attitude(pos, yaw, pitch, roll, intr):
    """C-A1 (tor C): projekcja intruza NED → (in_fov, cx, cy, az_deg, el_deg) z PEŁNYM attitude kamery
    (yaw+pitch+roll), w przeciwieństwie do project_to_pixel (level, tylko yaw). Rozdziela „poza FOV"
    (klip pitchem) od „w FOV" (renderer/detektor). Kamera forward = body +X (montaż x500_mono_cam)."""
    import math as _m
    HFOV = 1.74; VFOV = 1.453           # mono_cam: h_fov 1.74 rad, V-FOV pochodne (640×480 pinhole)
    wx, wy, wz = intr[0]-pos[0], intr[1]-pos[1], intr[2]-pos[2]
    cy_, sy = _m.cos(yaw), _m.sin(yaw); cp, sp = _m.cos(pitch), _m.sin(pitch); cr, sr = _m.cos(roll), _m.sin(roll)
    # NED→body: Rx(roll)·Ry(pitch)·Rz(yaw)
    x1 =  cy_*wx + sy*wy;  y1 = -sy*wx + cy_*wy;  z1 = wz            # Rz(yaw)
    x2 =  cp*x1 - sp*z1;   y2 = y1;               z2 = sp*x1 + cp*z1 # Ry(pitch)
    bx = x2;               by = cr*y2 + sr*z2;    bz = -sr*y2 + cr*z2# Rx(roll)
    if bx <= 0.1:
        return {"in_fov": False, "reason": "za_kamera", "cx": None, "cy": None, "az_deg": None, "el_deg": None}
    az = _m.atan2(by, bx); el = _m.atan2(-bz, _m.hypot(bx, by))
    in_fov = (abs(az) <= HFOV/2.0 and abs(el) <= VFOV/2.0)
    cx = 0.5 + _m.tan(az)/(2.0*_m.tan(HFOV/2.0))
    cyp = 0.5 - _m.tan(el)/(2.0*_m.tan(VFOV/2.0))
    return {"in_fov": in_fov, "cx": round(cx,3), "cy": round(cyp,3),
            "az_deg": round(_m.degrees(az),2), "el_deg": round(_m.degrees(el),2)}


def scene_sanity_intruder(frame, pos, yaw, pitch, roll, intr_ned, dark_thr=160, min_px=8, box_frac=0.10):
    """SCENE-SANITY GUARD (tor C/C-A1, wzorzec certs_selfcheck): asercja że intruz obecny w STANIE sceny
    jest też WIDOCZNY w OBRAZIE. Projektuje pozę intruza (pełne attitude); jeśli w FOV — sprawdza czy w
    przewidzianym regionie są ciemne piksele obiektu (mesh ciemny < dark_thr na tle nieba/gruntu). Zwraca
    verdict. Regresja renderu (intruz w stanie, brak w obrazie) = GUARD_FAIL, NIE wynik detekcji.
    Egzekwowane kodem: mechanizm §3f (iteracja 6) był awarią renderu udającą porażkę detekcji."""
    pf = project_full_attitude(pos, yaw, pitch, roll, intr_ned)
    if not pf.get("in_fov"):
        return {"guard": "SKIP_out_of_fov", "in_fov": False, **pf}   # poza kadrem — guard nie orzeka
    if frame is None:
        return {"guard": "NO_FRAME", "in_fov": True, **pf}
    import numpy as _np
    g = (frame[..., 0] if frame.ndim == 3 else frame).astype(int)
    h, w = g.shape
    cxpx, cypx = int(pf["cx"]*w), int(pf["cy"]*h)
    r = max(6, int(box_frac*min(h, w)/2))               # okno ~box_frac ramki wokół projekcji
    reg = g[max(0,cypx-r):cypx+r, max(0,cxpx-r):cxpx+r]
    dark = int((reg < dark_thr).sum()) if reg.size else 0
    visible = dark >= min_px
    return {"guard": ("PASS_visible" if visible else "FAIL_in_state_not_in_image"),
            "in_fov": True, "cx": pf["cx"], "cy": pf["cy"], "dark_px": dark, "min_px": min_px,
            "region_px": int(reg.size), "el_deg": pf["el_deg"]}


def gz_scene_models(expected_name):
    """A4 (tor C ogon): enumeracja modeli sceny gz (`gz model --list`) — pierwsza, PRZED query po nazwie.
    Zwraca {names, expected, present}. Rozdziela „nazwa nieobecna w scenie" od „obecna, nierenderowana".
    Guard tylko RAPORTUJE (nie orzeka o kryteriach)."""
    try:
        import subprocess, re as _re
        out = subprocess.run(["gz", "model", "--list"], capture_output=True, text=True, timeout=6).stdout
        names = _re.findall(r"^\s*-\s*(\S+)\s*$", out, _re.M) or _re.findall(r"\b(\w+)\b", out)
        names = [n for n in names if n not in ("Available", "models", "Requesting", "world")]
        return {"names": names, "expected": expected_name, "present": expected_name in names}
    except Exception as e:
        return {"names": None, "expected": expected_name, "present": None, "err": str(e)}


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
        # B3: nagłówek schematu (self-describing) — overlay/parser rozpoznaje wersję; brak = v1 (stare trace'y).
        self.tf.write(json.dumps({"t": "schema", "v": TRACE_SCHEMA_V, "tick_fields": TRACE_TICK_FIELDS,
                                  "event_types": TRACE_EVENT_TYPES}) + "\n")
        self.xrce = XrcePublisher()
        self.chan = ChannelSub(self.xrce.node)          # współdziel węzeł rclpy osłony
        self.boxes_sub = BoxesSub(self.xrce.node)       # A6: pasywne logowanie conf (wszystkie boxy)
        self.navsub = NavStatusSub(self.xrce.node)      # G5: precyzyjny nav_state (failsafe)
        # SCENE-SANITY GUARD (tor C/C-A1): capture klatki do asercji widoczności intruza (regresja renderu
        # nigdy więcej nie udaje wyniku detekcji). Subskrypcja tylko gdy IMG_TOPIC podany przez orkiestrację.
        self._frame = None; _img_topic = os.environ.get("IMG_TOPIC")
        if _img_topic:
            self.xrce.node.create_subscription(Image, _img_topic, self._on_frame, qos_be())
        self.conf_samples = []; self.n_admitted = 0; self._boxes_seq = -1
        self.mav = Mav(set_gf=True)
        self.shield = PatrolShield(); self.shield.reset()
        self.planner = Planner(laps)
        self.ctrl = ObserveController(d_safe=D_SAFE_M, alt=ALT_M)
        self.authz = Authorizer()
        self.observe_authority = False
        # DEMO-B (§2 PROMPT_D_BUILD_1) — ścieżka tokenowa, DOMYŚLNIE WYŁĄCZONA (token_gated=False ⇒
        # zachowanie R0.2/R0.3a bez zmian: legacy observe_authority, auth_ok=True). Per-akt runner DEMO-B
        # ustawia token_gated=True. admission_seq = epizod admisji (inkrement na ENTRY; -1 = brak epizodu).
        self.token_gated = False
        self.admission_seq = -1
        self._nonce_ctr = 0
        self.n_token_issued = 0; self.n_token_consumed = 0; self.n_refuse_no_auth = 0
        # B3 patche PRE_D §4: (b) koniunkty ostatniej klatki (ZOH do tiku); (f) pozycja intruza NED
        # (GT-fed: z gt_intruder_fn; live/B4: runner ustawia self._intr_ned per-tick). None gdy nieznane.
        self._last_conj = None
        self._intr_ned = None
        self.k = 0
        self.max_radial = 0.0
        self._last_pub = None; self.setpoint_max_dt = 0.0; self.setpoint_dts = []
        # fix #2: setpoint w OSOBNYM WĄTKU o stałym takcie (odsprzężony od pętli decyzji/kanału),
        # by kontencja CPU detektora nie głodziła strumienia → brak natywnego HOLD z utraty offboard.
        self._sp_lock = threading.Lock(); self._latest_sp = None
        self._sp_yaw = 0.0    # ANEKS_D8 §3c: yaw setpointu (default 0=fwd/N; probe ego-motion trzyma na celu)
        self._stream_stop = threading.Event(); self._stream_thread = None
        self._stream_last = None; self.stream_max_dt = 0.0; self.stream_pub_count = 0
        # DEAD-MAN (fix G5, decyzja Olgi): brak odświeżenia setpointu przez N ticków ⇒ osłona MARTWA ⇒
        # streamer MILKNIE ⇒ natywny failsafe (COM_OF_LOSS_T). Egzekwuje własność „martwa osłona ⇒
        # bezpieczne przejęcie warstwy-0" (regresja wprowadzona przez fix#2 zombie-stream). REGUŁA N:
        # N=DEADMAN_TICKS (config_r02, [PROWIZORYCZNE/A4]): > max legalnego stalla pętli, < COM_OF_LOSS_T.
        # GT-fed N=6 (0.3 s) OK; live-fed re-derywacja z rozkładu stalli → tor C. NIE strojone pod okno.
        self.DEADMAN_TICKS = DEADMAN_TICKS; self.deadman_s = self.DEADMAN_TICKS * PERIOD   # 0.3 s
        self._last_refresh = time.monotonic(); self._deadman_armed = False; self._deadman_tripped = False
        self.gf_fired = False; self.offboard_lost_ticks = 0
        self.n_entry = 0; self.n_false_entry = 0
        self.observe_ticks = 0; self.dsafe_violations = 0; self.min_d_observe = float("inf")
        self.entry_t = None; self.intruder_present = False; self.intruder_in_view_t = None
        self._prev_locked = False; self.locked = False   # locked ustawiane w tick(); init dla odczytu pre-tick
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

    def issue_operator_token(self, operator_id="operator", nonce=None):
        """DEMO-B: operator wydaje token OBSERVE_GRANT dla BIEŻĄCEGO epizodu admisji (default-deny,
        per-admisja). Pre-autoryzacja zakazana: gdy ¬locked albo brak epizodu ⇒ REFUSE(PREAUTH), logowane.
        Zwraca rekord PCDL (podpisany). Punkt-dławik: eskalacja i tak przez token_auth_ok w tick()."""
        if nonce is None:
            self._nonce_ctr += 1
            nonce = f"{operator_id}:{self.admission_seq}:{self._nonce_ctr}"
        rec = self.authz.issue_token(operator_id, nonce, self.admission_seq,
                                     locked=bool(getattr(self, "locked", False)),
                                     current_seq=self.admission_seq)
        if rec["decision"] == "ALLOW":
            self.n_token_issued += 1
        self.tf.write(json.dumps({"k": self.k, "t": round(time.time()-self.t0, 3),
                                  "event": "token_issued", "op": operator_id,
                                  "admission_seq": self.admission_seq, "decision": rec["decision"],
                                  "reason": rec["reason"]}) + "\n")
        return rec

    def _pub(self, xyz):
        # pętla decyzji NIE publikuje bezpośrednio — tylko aktualizuje setpoint; publikuje streamer.
        now = time.monotonic()
        if self._last_pub is not None:
            dt = now - self._last_pub
            self.setpoint_max_dt = max(self.setpoint_max_dt, dt)  # takt decyzji (info)
            self.setpoint_dts.append(dt)      # R3 tor C: rozkład stalli pętli decyzyjnej (re-derywacja N dead-mana)
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
                sp_yaw = self._sp_yaw
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
                try: self.xrce.publish_setpoint(sp, sp_yaw)
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

    def _on_frame(self, msg):
        try:
            import numpy as _np
            buf = _np.frombuffer(bytes(msg.data), dtype=_np.uint8)
            ch = max(1, len(msg.data)//(msg.height*msg.width))
            self._frame = buf.reshape(msg.height, msg.width, ch) if ch > 1 else buf.reshape(msg.height, msg.width)
        except Exception: pass

    def preflight_scene_sanity(self, intr_ned, enforce=None):
        """GUARD widoczności intruza na starcie scenariusza LIVE (nie GT-fed). Zbiera klatkę i orzeka.
        enforce: gdy True i FAIL → sys.exit (twarda bariera). Default: enforce w trybie LIVE (nie GT-fed),
        wyłączony gdy SCENE_SANITY=off (np. dopóki render niesprawny — świadoma zgoda)."""
        if enforce is None:
            enforce = (not self.gt_mode) and os.environ.get("SCENE_SANITY", "on") != "off"
        for _ in range(30):                              # do ~1.5 s na złapanie klatki
            self._spin()
            if self._frame is not None: break
            time.sleep(0.05)
        res = scene_sanity_intruder(self._frame, list(self.mav.pos), self._yaw(),
                                    self.mav.pitch, self.mav.roll, intr_ned)
        # A4: enumeracja sceny NAJPIERW → rozdziela „nazwa nieobecna" od „obecna, nierenderowana"
        res["model_in_state"] = gz_scene_models(os.environ.get("INTRUDER_NAME", "intruder"))
        self.tf.write(json.dumps({"EVENT": "scene_sanity", **res})+"\n")
        print(f"[gate] SCENE-SANITY intruz: {res.get('guard')} "
              f"(in_fov={res.get('in_fov')} dark_px={res.get('dark_px')} el={res.get('el_deg')} "
              f"model_in_state={res['model_in_state'].get('present')} names={res['model_in_state'].get('names')})")
        if enforce and res.get("guard") == "FAIL_in_state_not_in_image":
            print("[gate] !! GUARD FAIL: intruz w STANIE sceny, ale NIEOBECNY w OBRAZIE (regresja renderu, "
                  "tor C C-A1). Bramka live NIE jest wiarygodna. STOP (SCENE_SANITY=off by pominąć świadomie).")
            self.finish({"scenario": "SCENE_SANITY_FAIL", "scene_sanity": res})
            sys.exit(4)
        return res

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
                self._intr_ned = [round(float(v), 3) for v in intr] if intr is not None else None  # B3 (f)
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
            self._last_conj = dict(self.gt_channel.last_conj)         # B3 (b): koniunkty ZOH
            return locked, (self.gt_channel.last_box if locked else None), (val.age_s if val else None)
        self._last_conj = getattr(self.chan, "last_conj", None)       # B3 (b): live (None gdy sub bez pola)
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
            # EXPIRE (DEMO-B): konsumpcja tokenów bieżącego epizodu — re-admisja wymaga nowego tokenu.
            if self.token_gated and self.admission_seq >= 0:
                nc = self.authz.consume_tokens(self.admission_seq)
                if nc:
                    self.n_token_consumed += nc
                    self.tf.write(json.dumps({"k": self.k, "t": round(time.time()-self.t0, 3),
                                              "event": "token_consumed",
                                              "admission_seq": self.admission_seq, "n": nc}) + "\n")
        # ENTRY: przejście unlocked→locked
        if locked and not self._prev_locked:
            self.n_entry += 1
            self.admission_seq += 1            # DEMO-B: nowy epizod admisji (per-cel operacyjnie = per-admisja)
            if self.entry_t is None:
                self.entry_t = time.time() - self.t0
            if not self.intruder_present:
                self.n_false_entry += 1        # ε_FP: lock na pustej scenie
        self._prev_locked = locked; self.locked = locked   # dostępne dla scenariuszy (GT-fed lub live)

        # tryb: OBSERVE gdy lock ∧ autorytet ∧ estymata; inaczej force/patrol.
        # DEMO-B: gdy token_gated, eskalacja żądana na lock∧estymata, a OSŁONA bramkuje przez auth_ok
        #  (token ważny dla epizodu). ¬auth_ok ⇒ shield zwraca REFUSE(NO_AUTH) ODWRACALNY (patrol/confirm trwa).
        auth_ok = True
        if self.token_gated and locked and self.ctrl.has_estimate() and force_mode is None:
            mode = M_OBSERVE
            sp = self.ctrl.setpoint(pos) or self.planner.target()
            auth_ok = self.authz.token_auth_ok(self.admission_seq)
        elif locked and self.observe_authority and self.ctrl.has_estimate() and force_mode is None:
            mode = M_OBSERVE
            sp = self.ctrl.setpoint(pos) or self.planner.target()
        elif force_mode is not None:
            mode = force_mode; sp = self.planner.target()
        elif self.idle_sp is not None:
            mode = M_PATROL; sp = list(self.idle_sp)   # hover na intruzie (dwell do ENTRY), nie patrol
        else:
            mode = M_PATROL; sp = self.planner.target()

        d = self.shield.step(self.k, pos, vel, sp, mode=mode, auth_ok=auth_ok)
        d["mode"] = mode                       # udostępnij tryb scenariuszom (fix: shield.step nie zwraca 'mode')
        if d["reason"] == NO_AUTH:
            self.n_refuse_no_auth += 1
            self.tf.write(json.dumps({"k": self.k, "t": round(time.time()-self.t0, 3),
                                      "event": "refuse_no_auth",
                                      "admission_seq": self.admission_seq}) + "\n")
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
               "reason": d["reason"], "rule": d["rule"], "mode": mode, "state": d.get("state"),   # B3 (a)
               "locked": locked,
               "age": chage, "conj": self._last_conj, "intr_ned": self._intr_ned,   # B3 (b), (f)
               "gt_fed": self.gt_mode, "pos": [round(v, 2) for v in pos], "yaw": round(self.mav.yaw, 3),
               "applied": [round(v, 2) for v in d["applied"]], "r_pos": round(math.hypot(pos[0], pos[1]), 2),
               "flight_mode": self.mav.flight_mode, "min_d": None if self.min_d_observe==float("inf") else round(self.min_d_observe,2),
               "auth_ok": bool(auth_ok), "admission_seq": self.admission_seq}   # DEMO-B: pola tokenu (overlay B3)
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

    def _stall_report(self):
        """R3 tor C: rozkład stalli pętli decyzyjnej (inter-_set_sp) — wejście do re-derywacji N dead-mana.
        KANAŁ POMIARU: time.monotonic() lokalny (nie MAVSDK). N musi być > p_max stalla, by dead-man nie
        tripował na legalnym stallu (reintrodukcja problemu fix#2)."""
        d = sorted(self.setpoint_dts)
        if not d: return None
        def pct(p): return round(d[min(len(d)-1, int(p*len(d)))], 4)
        tick = 1.0/20.0
        return {"channel": "monotonic_local", "n": len(d), "p50": pct(0.50), "p95": pct(0.95),
                "p99": pct(0.99), "max": round(d[-1], 4),
                "max_ticks_@20Hz": round(d[-1]/tick, 2), "p99_ticks_@20Hz": round(pct(0.99)/tick, 2),
                "over_6ticks(0.30s)": sum(1 for x in d if x > 6*tick),
                "over_4ticks(0.20s)": sum(1 for x in d if x > 4*tick)}

    def finish(self, summary):
        self.stop_streamer()
        summary = {**summary, "conf_passive_A6": self.conf_report()}   # A6: pasywny log conf w każdym locie
        summary["stall_dist_R3"] = self._stall_report()                # R3 tor C: rozkład stalli pętli (re-derywacja N)
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
    r.preflight_scene_sanity((7.0, 0.0, -11.5))   # GUARD (tor C): live wymaga widocznego intruza; GT-fed pomija
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


def scenario_C1(r: Runner):
    """C-A1 (tor C, krok 1 buildu = RE-ATRYBUCJA §3f): dron ZAWIS w Home, intruz statyczny (7,0,11.5).
    Mierzy rozkład pitch/roll (att() rozszerzone), projekcję celu LEVEL vs PEŁNO-ATTITUDE, oraz co widzi
    detektor (boxy/conf). Rozdziela: (i) POZA FOV (klip pitchem) vs (ii) W FOV nie-wykryty (render/detektor).
    GATE C-A1: mały pitch ∧ cel-w-kadrze ⇒ STOP+re-atrybucja przed 0a/0b. Wyłącznie w locie."""
    INTR_NED = tuple(float(x) for x in os.environ.get("C1_INTR", "7,0,-11.5").split(","))  # NED; diagnostyka pozycji
    r.admit_observe(False); r.intruder_present = True
    # capture surowej klatki (jeśli IMG_TOPIC podany przez orkiestrację)
    frame = {"buf": None}
    img_topic = os.environ.get("IMG_TOPIC")
    if img_topic:
        import numpy as _np
        def _on_img(msg):
            try:
                buf = _np.frombuffer(bytes(msg.data), dtype=_np.uint8)
                ch = max(1, len(msg.data)//(msg.height*msg.width))
                frame["buf"] = buf.reshape(msg.height, msg.width, ch) if ch>1 else buf.reshape(msg.height, msg.width)
            except Exception: pass
        r.xrce.node.create_subscription(Image, img_topic, _on_img, qos_be())
    r.bring_up()
    r.idle_sp = [r.start[0], r.start[1], -ALT_M]
    gsan = r.preflight_scene_sanity(INTR_NED, enforce=False)   # GUARD jako kryterium (rider 0), bez STOP w diagnostyce
    # A4: weryfikacja pozy = ENUMERACJA sceny NAJPIERW, potem query po nazwie z parametru (INTRUDER_NAME)
    intr_name = os.environ.get("INTRUDER_NAME", "intruder")
    scene_models = gz_scene_models(intr_name)
    intr_pose_q = None
    try:
        import subprocess
        intr_pose_q = subprocess.run(["gz", "model", "-m", intr_name, "-p"], capture_output=True,
                                     text=True, timeout=5).stdout.strip()[:200]
    except Exception as e: intr_pose_q = f"query_fail:{e}"
    pitches = []; rolls = []; yaws = []; boxes_seen = []; projs_full = []; proj_cx = []
    t_hover = time.time()
    while time.time()-t_hover < 18:                      # ~18 s zawisu — rozkład attitude + detekcja
        r._spin(); r._log_conf_passive()
        r._pub(r.idle_sp)                                # utrzymuj hover (dead-man żywy)
        yw = r._yaw()
        pitches.append(r.mav.pitch); rolls.append(r.mav.roll); yaws.append(yw)
        pf = project_full_attitude(list(r.mav.pos), yw, r.mav.pitch, r.mav.roll, INTR_NED)
        projs_full.append(pf)
        if pf.get("cx") is not None: proj_cx.append(pf["cx"])
        if r.boxes_sub.boxes:                            # co widzi detektor (max conf box)
            b = max(r.boxes_sub.boxes, key=lambda x: x[4])
            boxes_seen.append({"cx": round(b[0],3), "cy": round(b[1],3), "conf": round(b[4],4)})
        time.sleep(PERIOD)
    r.mav.land(); time.sleep(2)
    import statistics as _st, numpy as _np
    def deg(x): return round(math.degrees(x),2)
    pitch_deg = [math.degrees(p) for p in pitches]; roll_deg = [math.degrees(x) for x in rolls]
    # projekcje przy ŚREDNIM attitude
    mp = _st.mean(pitches) if pitches else 0.0; mr = _st.mean(rolls) if rolls else 0.0
    proj_level = project_to_pixel(list(r.mav.pos), r._yaw(), INTR_NED)     # level (tylko yaw)
    proj_full_mean = project_full_attitude(list(r.mav.pos), r._yaw(), mp, mr, INTR_NED)
    n_in_fov = sum(1 for p in projs_full if p.get("in_fov"))
    conf_max = max((b["conf"] for b in boxes_seen), default=0.0)
    # zapis klatki (jeśli złapana) + npy
    prefix = os.environ.get("C1_PREFIX", "/tmp/r02/C1/frame")
    os.makedirs(os.path.dirname(prefix), exist_ok=True)
    frame_saved = None
    if frame["buf"] is not None:
        _np.save(prefix+".npy", frame["buf"]); frame_saved = prefix+".npy"
    yaw_deg = [math.degrees(y) for y in yaws]
    verdict = {"scenario": "C1_reattrib",
        "intruder_pose_gz": intr_pose_q, "intruder_assumed_NED": INTR_NED,
        "scene_models_enum": scene_models,   # A4: enumeracja sceny (nazwa obecna? lista nazw)
        "pitch_deg": {"mean": deg(mp), "min": round(min(pitch_deg),2) if pitch_deg else None,
                      "max": round(max(pitch_deg),2) if pitch_deg else None,
                      "abs_max": round(max((abs(x) for x in pitch_deg), default=0),2),
                      "std": round(_st.pstdev(pitch_deg),2) if len(pitch_deg)>1 else 0.0},
        "roll_deg": {"mean": deg(mr), "abs_max": round(max((abs(x) for x in roll_deg), default=0),2)},
        "yaw_deg": {"mean": round(_st.mean(yaw_deg),2) if yaw_deg else None,
                    "abs_max": round(max((abs(x) for x in yaw_deg), default=0),2)},
        "proj_cx_hover": {"mean": round(_st.mean(proj_cx),3) if proj_cx else None,
                          "min": round(min(proj_cx),3) if proj_cx else None,
                          "max": round(max(proj_cx),3) if proj_cx else None},
        "proj_level": (None if proj_level is None else {"cx": round(proj_level.cx,3), "cy": round(proj_level.cy,3)}),
        "frames_in_fov_frac": round(n_in_fov/max(len(projs_full),1),3),
        "detector_conf_max": round(conf_max,4), "detector_boxes_n": len(boxes_seen),
        "theta_conf": THETA_CONF, "frame_saved": frame_saved, "channel_time": "monotonic_local(att via MAVSDK 20Hz)"}
    # KLASYFIKACJA re-atrybucji (per-frame, NIE post-land)
    in_fov = verdict["frames_in_fov_frac"] >= 0.9; small_pitch = verdict["pitch_deg"]["abs_max"] < 15.0
    detected = conf_max >= THETA_CONF
    if not in_fov:
        verdict["reattrib"] = "POZA_FOV (klip attitude) — dźwignia 0 (celowanie) UZASADNIONA"
        verdict["GATE_C1_stop"] = False
    elif in_fov and not detected:
        verdict["reattrib"] = "W_FOV_NIE_WYKRYTY (render/detektor) — NIE kadrowanie; gimbal moze byc NIEPOTRZEBNY"
        verdict["GATE_C1_stop"] = small_pitch     # mały pitch + w kadrze ⇒ STOP+re-atrybucja
    else:
        verdict["reattrib"] = "W_FOV_WYKRYTY — cel widoczny w zawisie (sprzeczne z §3f? sprawdz OBSERVE-motion)"
        verdict["GATE_C1_stop"] = small_pitch
    r.finish(verdict)
    return True


# ============================ DEMO-B akty (B4, PROMPT_D_BUILD_4 §1) ============================
# Runnery per-akt wyprowadzone z tego Runnera (A3-aneks: orkiestrator wieloaktowy OUT). Kanał GT-fed
# (deterministyczny ENTRY); intruz WIDOCZNY teleportowany tym samym f(sim_t) (set_pose, MODEL) dla kamery
# filmowej. Beat operatora = skryptowany sygnatariusz (A5) na ENTRY+opóźnienie. Assert A4 token_gated=True.

def _act_setup(r, act):
    """Wspólny wstęp aktu: spec, A4-assert, GT-fed fn ze spec, WĄTEK teleportu widocznego intruza (~2 Hz,
    poza pętlą decyzji — jak mti_flight.replacer; kamera filmowa widzi ruch, kanał ENTRY z projekcji GT)."""
    from acts import act_common as AC
    spec = AC.load_spec(act)
    r.token_gated = True
    AC.assert_token_gated(r)                       # A4: twardy błąd jeśli False
    r.intruder_present = True
    ned_fn = AC.intruder_ned_fn(spec)
    if r.gt_mode:
        r.gt_intruder_fn = lambda t: ned_fn(t)     # kanał (ENTRY) — projekcja GT
    r._teleport_stop = threading.Event()

    def _telethread():
        # ANEKS_D5 §6a: TRWAŁY klient set_pose in-process (zero spawnów subprocess w pętli) — usuwa churn
        # transportu gz który stalluje RTF (RAPORT §AKT-9). §6b: faza ruchu z sim_t (zegar symu), nie ściennego.
        from r02.intruder_driver import set_pose as _sp_fallback
        client = None
        try:
            from r02.intruder_driver import GzPoseClient
            # §7a nieblokujący worker; ANEKS_D6 §3: APPLY_HZ konfigurowalne (default 20). Przy GT-fed kadencja
            # APLIKACJI (widoczny intruz→film) NIE wpływa na detekcję (kanał GT-fed=projekcja ned_fn) ani na
            # geometrię sędziego (intr_ned z producenta @16.7 Hz) → obniżenie zbija koszt server-side set_pose.
            _apply_hz = float(os.environ.get("APPLY_HZ", "20.0"))
            # ANEKS_D7 §7d: POSE_ASYNC=0 → klient BLOKUJĄCY z §6d (0% głębokich dipów; koszt server-side
            # set_pose UJEDNOLICONY zamiast bursty stalli worker'a FF które wchodziły w segment roszczenia
            # A2 → spurious EXPIRE, RAPORT §AKT-13). §3: przy GT-fed kadencja set_pose nie wpływa na detekcję
            # (intr_ned z producenta @16.7 Hz nietknięte) → decymacja set_pose do APPLY_HZ obniża koszt
            # server-side (↑Δsim/Δwall) trzymając lockstep. Domyślnie async (A1/A3 PASS); blokujący dla A2 retry.
            _async = os.environ.get("POSE_ASYNC", "1") != "0"
            client = GzPoseClient(WORLD_NAME, async_apply=_async, apply_hz=_apply_hz)
        except Exception as e:
            print(f"[teleport] GzPoseClient init FAIL ({e}) — fallback subprocess set_pose")
            _async = True
        sim0 = None                               # §6b: kotwica fazy sim_t do zera choreografii (r.t0)
        n_set = 0; loop_t0 = time.time(); last_log = loop_t0
        _blk_dt = 1.0 / max(_apply_hz, 0.1)       # §7d: okres decymacji set_pose w trybie blokującym
        _last_apply = 0.0
        r._teleport_backend = "gz.transport13(persistent)" if client is not None else "subprocess(fallback)"
        r._pose_apply_mode = ("async_ff" if _async else "blocking_6d") if client is not None else "subprocess"
        print(f"[teleport] backend={r._teleport_backend} mode={r._pose_apply_mode} apply_hz={_apply_hz} target={DEMO_TELEPORT_HZ}Hz")
        while not r._teleport_stop.is_set():
            it0 = time.time()
            st = client.sim_t() if client is not None else None
            if st is not None:                    # §6b: faza z sim-time (kotwiczona do r.t0 przy 1. próbce)
                if sim0 is None:
                    sim0 = st - (time.time() - r.t0 if getattr(r, "t0", None) else 0.0)
                phase = st - sim0
            else:                                 # rozgrzewka: zegar symu jeszcze niegotowy → zegar ścienny
                phase = time.time() - r.t0 if getattr(r, "t0", None) else 0.0
            p = ned_fn(phase)
            # B5 LIVE: aktor STEROWANY (teleport) — poza NED = znana GT choreografii (NIE percepcja); tracowi.
            r._intr_ned = [round(p[0], 3), round(p[1], 3), round(p[2], 3)] if p is not None else None
            if p is not None:
                # §7d: w trybie blokującym decymuj set_pose do APPLY_HZ (koszt server-side ↓, lockstep);
                # tryb async wysyła co tick (set_pose nieblokujące → worker aplikuje @apply_hz).
                _do_apply = _async or (it0 - _last_apply >= _blk_dt)
                try:
                    if client is not None:
                        if _do_apply:
                            client.set_pose(round(p[0], 3), round(p[1], 3), round(-p[2], 3))
                            if not _async:
                                _last_apply = it0; n_set += 1
                            else:
                                n_set += 1
                    elif _do_apply:
                        _sp_fallback(WORLD_NAME, round(p[0], 3), round(p[1], 3), round(-p[2], 3))
                        _last_apply = it0; n_set += 1
                except Exception:
                    pass
            # §6a: producent @DEMO_TELEPORT_DT (16.7 Hz — świeżość intr_ned); §7a: set_pose NIEBLOKUJĄCE,
            # worker APLIKUJE pozy osobno → kadencja aplikowana = client.applied_hz() (wielkość bramkowana 7a).
            time.sleep(max(0.0, DEMO_TELEPORT_DT - (time.time() - it0)))
            now = time.time()
            if now - last_log >= 5.0:
                r._teleport_hz_producer = round(n_set / (now - loop_t0), 2)
                r._teleport_hz_eff = (client.applied_hz() if client is not None else r._teleport_hz_producer)
                r._teleport_req_lat_ms = getattr(client, "last_lat_ms", None) if client is not None else None
                r._teleport_ok_rate = client.ok_rate() if client is not None else None
                last_log = now
        r._teleport_hz_producer = round(n_set / max(time.time() - loop_t0, 1e-6), 2)
        r._teleport_hz_eff = (client.applied_hz() if client is not None else r._teleport_hz_producer)  # §7a: APLIKOWANA
        r._teleport_req_lat_ms = getattr(client, "last_lat_ms", None) if client is not None else None
        r._teleport_ok_rate = client.ok_rate() if client is not None else None
        print(f"[teleport] APLIKOWANA={r._teleport_hz_eff}Hz producent={r._teleport_hz_producer}Hz "
              f"req_lat={r._teleport_req_lat_ms}ms ok_rate={r._teleport_ok_rate} backend={r._teleport_backend}")

    def start_teleport():
        threading.Thread(target=_telethread, daemon=True).start()
    return spec, AC, start_teleport


WORLD_NAME = os.environ.get("PX4_GZ_WORLD", "world_demo_v1")


def _start_live_detector(r):
    """B5: bridge mono + detector_node uruchamiane PO bring_up (po arm). Diagnoza 5 env-fail: obciążenie
    LIVE (bridge+YOLO) PODCZAS arm blokuje połączenie MAVSDK/GCS ('No connection to GCS') → health timeout.
    REGATE (mti_flight) armuje ZANIM ładuje YOLO. Tu: MAVSDK łączy+arm CZYSTO, potem start toru LIVE."""
    topic = os.environ.get("LIVE_DETECTOR_TOPIC")
    if not topic or r.gt_mode:
        return
    import subprocess
    try:
        # NIE-blokujące (żaden sleep w wątku scenariusza — inaczej dead-man 0.3 s tripuje stream→failsafe).
        # Bridge+detektor ładują się w tle; pętla ticków odświeża setpoint; ENTRY pada gdy YOLO gotowy
        # (intruz w pierścieniu w oknie dwell z zapasem). Late-join ROS: detektor złapie obraz po bridge.
        subprocess.Popen(["ros2", "run", "ros_gz_bridge", "parameter_bridge",
                          f"{topic}@sensor_msgs/msg/Image[gz.msgs.Image"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        dlog = os.environ.get("DETECTOR_LOG", "/tmp/detector.log")
        subprocess.Popen([sys.executable, "-m", "r02.detector_node", "--image-topic", topic,
                          "--det-hz", str(DEMO_DECISION_HZ)],   # §4a: kadencja decyzji == REGATE 2.0 Hz
                         stdout=open(dlog, "w"), stderr=subprocess.STDOUT)
        print(f"[gate] LIVE bridge+detektor PO arm (topic={topic}, det_hz={DEMO_DECISION_HZ}, nie-blokująco)")
    except Exception as e:
        print(f"[gate] LIVE detektor start FAIL: {e}")


def _emit_act_manifest(r, act):
    """B5 §0/§2: manifest emitowany PO bring_up (po arm) a PRZED choreografią. Dzięki temu env-fail
    bootu/health (crash w bring_up, PRZED manifestem) = NIE-próba (§0), a crash w choreografii = próba.
    Ścieżka z env MANIFEST_OUT; jeśli brak — nie emituje (tryb nie-B5)."""
    out = os.environ.get("MANIFEST_OUT")
    if not out:
        return
    try:
        import hashlib
        from acts import act_common as AC
        world_sdf = os.environ.get("WORLD_SDF", os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "worlds", f"{WORLD_NAME}.sdf"))
        head = os.environ.get("HEAD_SHA", "unknown")
        jhash = hashlib.sha256(open(os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "act_judge.py"),
            "rb").read()).hexdigest()
        m = AC.build_manifest(act, world_sdf, head, token_gated=r.token_gated,
                              contention=os.environ.get("CONTENTION", "?"),
                              aneks_h={"headless": None, "note": "ANEKS-H domknięty po biegu"},
                              demo_mti=(os.environ.get("DEMO_MTI") == "1"))
        m["judge_sha256"] = jhash
        m["detector"] = "LIVE (r02.detector_node YOLO); GT_FED=0" if not r.gt_mode else "GT-fed"
        # ANEKS_D6 §1a: JAWNE etykietowanie kanału detekcji. Demo A1/A2 = GT-fed (idealizowany detektor,
        # konfig B4 gdzie sędzia orzekł VALID); live-MTI NIE jest przedmiotem roszczenia (RAPORT §AKT-12,
        # koperta 8a). Bieg aktu bez echa `detection_channel: gt_fed` = INVALID z definicji (SR-M3).
        m["detection_channel"] = "gt_fed" if r.gt_mode else "live"
        # §4a: echo kadencji decyzji przekazanej detektorowi LIVE (== REGATE 2.0). Bieg z det_hz≠2.0 =
        # INVALID z definicji. Dla GT-fed brak detektora LIVE → None (kadencja z pętli runnera).
        m["det_hz"] = DEMO_DECISION_HZ if (not r.gt_mode and os.environ.get("LIVE_DETECTOR_TOPIC")) else None
        # §5a: echo kadencji RUCHU intruza (teleport) == REGATE ~16.7 Hz. Bieg z teleport_hz≠16.7 = INVALID
        # z definicji (dotyczy OBU torów — wątek teleportu żyje w gt-fed i live). RAPORT_D_B5 §FINAL: 2 Hz
        # teleport zabijał MTI in-window (filtr trwałości odrzucał ruch skokowy).
        m["teleport_hz"] = DEMO_TELEPORT_HZ
        m["apply_hz"] = float(os.environ.get("APPLY_HZ", "20.0"))   # §3: kadencja APLIKACJI worker (GT-fed: nie wpływa na detekcję)
        # §6a: echo backendu set_pose (trwały klient gz.transport vs subprocess-fallback). Zmierzona
        # efektywna kadencja jest w SCENARIO_RESULT (teleport_hz_eff) — mierzona w trakcie biegu.
        try:
            import gz.transport13 as _gzt  # noqa: F401
            m["teleport_backend"] = "gz.transport13(persistent)"
        except Exception:
            m["teleport_backend"] = "subprocess(fallback)"
        # §7c higiena backendu: pose_backend echo; bieg AKTU z 'subprocess(fallback)' = INVALID z definicji
        # (cichy powrót churnu zakazany). Sędzia/harness czyta to pole.
        m["pose_backend"] = m["teleport_backend"]
        # ANEKS_D7 §7d: tryb aplikacji pozy (async_ff domyślny; blocking_6d = fallback przy dipie w oknie
        # roszczenia). Echo do artefaktów/raportu; subprocess(fallback) = INVALID (§7c).
        m["pose_apply_mode"] = getattr(r, "_pose_apply_mode", "async_ff" if os.environ.get("POSE_ASYNC", "1") != "0" else "blocking_6d")
        m["armed_before_manifest"] = bool(getattr(r.mav, "armed", False))   # dowód: manifest PO arm
        # ANEKS_D7 §7b: unix wall biegu-zegara osłony (self.t0 = time.time() przy arm). Trace tick `t` =
        # time.time()-t0 (wall-elapsed), więc bramka habitatu mapuje okna roszczeń (spec timeline_s, w t)
        # → unix [t0+start, t0+end] → próbki rtf_stream. Wyłącznie do SELEKCJI okna (choreografia), NIE z RTF.
        m["arm_wall_unix"] = round(getattr(r, "t0", 0.0), 3)
        # H0 (5P): echo EKF2_GPS_CTRL z persystowanego bson (stan który PX4 załadował) — cicha regresja
        # ensure_gps_enabled widoczna w prowieniencji PIERWSZEGO biegu, nie po polowaniu. (0=GPS off=przyczyna 5R3)
        try:
            _bson = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                 "PX4-Autopilot/build/px4_sitl_default/rootfs/parameters.bson")
            if os.path.exists(_bson):
                _d = open(_bson, "rb").read(); _n = b"EKF2_GPS_CTRL\x00"; _i = _d.find(_n)
                m["ekf2_gps_ctrl_bson"] = (int.from_bytes(_d[_i+len(_n):_i+len(_n)+4], "little")
                                           if _i >= 0 else "absent(default 7)")
        except Exception:
            m["ekf2_gps_ctrl_bson"] = "read_fail"
        json.dump(m, open(out, "w"), indent=2, ensure_ascii=False)
        print(f"[gate] manifest PO arm → {out} (judge={jhash[:16]}… armed={m['armed_before_manifest']})")
    except Exception as e:
        print(f"[gate] manifest emit FAIL: {e}")


def scenario_A1(r: Runner):
    """AKT 1: patrol→intruz dwell 7–9→ENTRY→REFUSE(NO_AUTH)→token(A5)→OBSERVE. NIE próba (B5)."""
    spec, AC, start_teleport = _act_setup(r, "A1")
    r.bring_up()
    _emit_act_manifest(r, "A1")                    # B5 §0/§2: manifest PO arm (env-fail bootu = nie-próba)
    _start_live_detector(r)                       # B5: tor LIVE PO arm (nie blokuje MAVSDK/GCS przy arm)
    start_teleport()                              # wątek teleportu widocznego intruza (~2 Hz)
    r.idle_sp = [r.start[0], r.start[1], -ALT_M]
    # ANEKS_D8 §3c: probe ego-motion (T1) — orbita wokół punktu dwell (home), promień dobrany tak, by
    # zasięg do świat-stałego intruza pozostał w 7-9 m; yaw trzymany na celu (cel stabilny w kadrze, tło
    # płynie); v=2.5 m/s zachowane z REGATE (paralaksa/krok MTI = v·Δt), ρ steruje zasięgiem (v=ω·ρ).
    # Intruz przypięty do świata, spec/osc bez zmian. Ruch TYLKO pre-lock (po ENTRY OBSERVE przejmuje).
    _probe = os.environ.get("PROBE_EGOMOTION", "0") == "1"
    _orbit_r = float(os.environ.get("PROBE_ORBIT_R", "1.0"))   # ρ: 7.86±ρ (+DALT 1.5) → zasięg ~7.0-9.0 m
    _orbit_v = float(os.environ.get("PROBE_ORBIT_V", "2.5"))   # REGATE mti_flight legs_v
    _omega = _orbit_v / max(_orbit_r, 1e-3)
    _c0, _c1, _cz = r.start[0], r.start[1], -ALT_M
    _t_probe0 = None
    grant_delay = AC.grant_delay_s(spec)
    hold_end = spec["timeline_s"]["intruder_ring_hold"][1]
    granted = False; entry_local = None
    while time.time() - r.t0 < hold_end + 5:
        t = time.time() - r.t0
        if _probe and not r.locked:
            if _t_probe0 is None:
                _t_probe0 = t
            ang = _omega * (t - _t_probe0)
            r.idle_sp = [_c0 + _orbit_r * math.cos(ang), _c1 + _orbit_r * math.sin(ang), _cz]
            intr = r._intr_ned                                  # świat-stały cel (worker teleportu)
            if intr is not None:
                p = r.mav.pos
                r._sp_yaw = math.atan2(intr[1] - p[1], intr[0] - p[0])   # bearing NED → yaw na cel
        elif _probe and r.locked:
            r._sp_yaw = 0.0                                     # po locku OBSERVE przejmuje — domyślny yaw
        d = r.tick()
        if r.locked and entry_local is None:
            entry_local = t
        if entry_local is not None and not granted and t >= entry_local + grant_delay:
            r.issue_operator_token("operator"); granted = True   # A5 skryptowany sygnatariusz
        time.sleep(PERIOD)
    r.mav.rtl(); time.sleep(6); r.mav.land(); time.sleep(2)
    crit = {"scenario": "A1", "n_entry": r.n_entry, "n_refuse_no_auth": r.n_refuse_no_auth,
            "n_token_issued": r.n_token_issued, "observe_ticks": r.observe_ticks,
            "min_d": None if r.min_d_observe == float("inf") else round(r.min_d_observe, 2),
            "dsafe_violations": r.dsafe_violations, "granted": granted,
            "teleport_hz_eff": getattr(r, "_teleport_hz_eff", None),      # §7a: kadencja APLIKOWANA (worker)
            "teleport_ok_rate": getattr(r, "_teleport_ok_rate", None),   # §3: frakcja request ok=True
            "teleport_hz_producer": getattr(r, "_teleport_hz_producer", None),  # §6a: świeżość intr_ned (pętla)
            "teleport_req_lat_ms": getattr(r, "_teleport_req_lat_ms", None),    # §7a: latencja request (diag 108ms)
            "teleport_backend": getattr(r, "_teleport_backend", None),
            "note": "REHEARSAL/integracja (B4) — NIE próba (B5); percepcja NIERAPORTOWALNA"}
    r.finish(crit)
    return True


def scenario_A2(r: Runner):
    """AKT 2: OBSERVE→utrata→EXPIRE(konsumpcja)→powrót→re-admisja→NO_AUTH→2. token→OBSERVE."""
    spec, AC, start_teleport = _act_setup(r, "A2")
    r.bring_up()
    _emit_act_manifest(r, "A2")                    # B5 §0/§2: manifest PO arm
    _start_live_detector(r)                       # B5: tor LIVE PO arm
    start_teleport()
    r.idle_sp = [r.start[0], r.start[1], -ALT_M]
    grant_delay = AC.grant_delay_s(spec)
    ep1_end = spec["timeline_s"]["ep1_ring_hold"][1]
    granted_seq = set(); prev_seq = -1; ep_entry_local = 0.0
    while time.time() - r.t0 < ep1_end + 5:
        t = time.time() - r.t0
        d = r.tick()
        # marker ENTRY lokalny per-epizod: gdy admission_seq rośnie, zapamiętaj czas nowego locka
        if r.admission_seq != prev_seq:
            prev_seq = r.admission_seq; ep_entry_local = t
        # na każdy epizod (admission_seq) po ENTRY+opóźnieniu wydaj token (2 beaty operatora, A5)
        if (r.locked and r.admission_seq >= 0 and r.admission_seq not in granted_seq
                and t >= ep_entry_local + grant_delay):
            r.issue_operator_token("operator"); granted_seq.add(r.admission_seq)
        time.sleep(PERIOD)
    r.mav.rtl(); time.sleep(6); r.mav.land(); time.sleep(2)
    crit = {"scenario": "A2", "n_entry": r.n_entry, "n_token_issued": r.n_token_issued,
            "n_token_consumed": r.n_token_consumed, "n_refuse_no_auth": r.n_refuse_no_auth,
            "teleport_hz_eff": getattr(r, "_teleport_hz_eff", None),
            "teleport_ok_rate": getattr(r, "_teleport_ok_rate", None),
            "teleport_hz_producer": getattr(r, "_teleport_hz_producer", None),
            "teleport_req_lat_ms": getattr(r, "_teleport_req_lat_ms", None),
            "teleport_backend": getattr(r, "_teleport_backend", None),
            "max_admission_seq": r.admission_seq, "granted_seqs": sorted(granted_seq),
            "note": "REHEARSAL/integracja (B4) — NIE próba (B5)"}
    r.finish(crit)
    return True


def main():
    laps = {"G1": 3, "G2": 1, "G3": 3, "G4": 2, "G5": 1, "CHAR": 3, "CHAR2": 1, "C1": 1,
            "A1": 1, "A2": 1}[SCEN]
    r = Runner(laps)
    fn = {"G1": scenario_G1, "G2": scenario_G2, "G3": scenario_G3, "G4": scenario_G4,
          "G5": scenario_G5, "CHAR": scenario_CHAR, "CHAR2": scenario_CHAR2, "C1": scenario_C1,
          "A1": scenario_A1, "A2": scenario_A2}[SCEN]
    ok = fn(r)
    sys.exit(0 if ok else 3)


if __name__ == "__main__":
    main()
