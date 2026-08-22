#!/usr/bin/env python3
"""
r03/gate_run_r03.py — BRAMKA R0.3a (GPS-DENIED), OSŁONA W PĘTLI. Jeden scenariusz per uruchomienie.

Osłona (r01.shield.PatrolShield) decyduje co tick; pos_flag = dead_reckoning (R1). Na
REFUSE(POS_DEGRADED) egzekutor stosuje AKCJĘ BEZPIECZNĄ = zejście STEROWANE PRĘDKOŚCIĄ dwufazowe
(1.5→0.7 m/s, v_xy=0; D5 zrew. §3quater; AUTO.LAND WYKLUCZONY). GT (gz) WYŁĄCZNIE sędzią (nigdy w
decyzji). Setpointy przez offboard velocity. Świeży boot per bieg (woła caller). Params restore (SR-B5).

Scenariusze (env SCEN): S1 nominal (bez denialu, N min) | S2 denial w patrolu | S3 denial+recovery |
S4 cięcie narożnik v_max + denial. Kryteria D13 liczone w judge (osobno, po biegu, z GT).

Env: SCEN, GATE_OUT (jsonl), S1_MIN (dla S1), boot już wstał (świeży, ≥90 s konwergencji EKF).
"""
import os, json, time, math, threading
import asyncio
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from px4_msgs.msg import VehicleLocalPosition
from gz.transport13 import Node as GzNode
from gz.msgs10.pose_v_pb2 import Pose_V
from mavsdk import System
from mavsdk.offboard import VelocityNedYaw, OffboardError
from mavsdk.action import ActionError

from r01.shield import PatrolShield, REFUSE, POS_DEGRADED, M_PATROL
from r03 import config as C

SCEN = os.environ.get("SCEN", "S2")
OUT = os.environ.get("GATE_OUT", f"/tmp/r03gate/{SCEN}.jsonl")
S1_MIN = float(os.environ.get("S1_MIN", "5"))
# K1 (PRE_K1 §2, ramię S): wstrzyknięcie na PIERWSZEJ nodze po PIERWSZYM narożniku, przy UŁAMKU nogi
# K1_POINT ∈ {0.2,0.35,0.5,0.65,0.8}. Osłona/zejście/config NIETKNIĘTE — tylko punkt wstrzyknięcia.
K1_POINT = float(os.environ.get("K1_POINT", "0.5"))
WORLD = os.environ.get("PX4_GZ_WORLD", "default")
MODEL = os.environ.get("B1_MODEL", "x500_mono_cam_0")
GT_TOPIC = f"/world/{WORLD}/dynamic_pose/info"
from r01.config import V_MAX as VMAX
# ALT: wysokość startowa (parametr UPRZĘŻY, nie kryterium). S3 wyżej, bo testuje re-ALLOW-po-histerezie:
# zejście z 8 m trwa ~8.4 s, a re-ALLOW wymaga recovery + rekonwergencja-EKF + M(5 s) ≈ 9 s → touchdown
# wyprzedzał re-ALLOW (nie dawało się zaobserwować kryterium D13). Z 15 m zejście ~13 s → jest margines.
# ALT jest pionowe; r_est (zawieranie) jest poziome → wyższy start NIE zmienia geometrii zawierania.
ALT = 15.0 if SCEN == "S3" else 8.0

# --- TRACE SCHEMA (DEMO-B B3, PROMPT_D_BUILD_3 §1, patch (e) PRE_D §4) --------
#   v1 (pre-B3): rows {t: meta|event|outcome}; event denial_on niosło r_est_at_cut (RAZ), brak per-tick.
#   v2 (B3): +row {t: "tick"} per-tick z r_est [m] i margin_R_E = R_E − r_est [m] (ε-budżet GPS-denied),
#            + decision/reason/pos/dr/descending. Pola stare nietknięte (zgodność wsteczna).
TRACE_SCHEMA_V = 2

# --- STAŁE UPRZĘŻY (nie kryteria bramki; parametry instrumentu) ---
# Stan preflight paramów = biała lista R-D1 w JEDNYM źródle prawdy (r03/config.HARNESS_PARAM_PREFLIGHT).
# ZASADA R-D1: assert-on-entry (preflight wymusza wymagany stan na CAŁEJ klasie JEDNYM setem), NIE
# restore-on-exit — restore zawodzi przy pkill -9 / os._exit / crashu, więc naprawa jednego paramu nie
# zamyka KLASY. SITL persystuje parametry w rootfs/parameters.bson przez reboot → zatruty param skaża każdy
# boot DETERMINISTYCZNIE. Invalidity (R-D3) tylko dla POISON_CRITICAL (GPS_CTRL).
GPS_CTRL_NOMINAL = C.HARNESS_PARAM_PREFLIGHT["EKF2_GPS_CTRL"]   # 7 (params_gnss.yaml default:7)
# HEALTH_WAIT_TIMEOUT_S: ograniczony (stary bezterminowy `async for` WIESZAŁ się na zatrutym boocie).
# Zmierzony bring-up przy zdrowym GPS (po 90 s settle, HGT_REF=0): t_health=2.3 s
# (results/R03/recon/DIAG/confirm.log). 45 s = ~19× margines (pokrywa też reset HGT_REF 1→0). Zostaje 45.
HEALTH_WAIT_TIMEOUT_S = 45
QOS = QoSProfile(depth=1, history=HistoryPolicy.KEEP_LAST, reliability=ReliabilityPolicy.BEST_EFFORT)

_lock = threading.Lock(); _f = None; _running = False
_gt_last = [0.0]


def _w(row):
    with _lock:
        if _f is not None and _running:
            _f.write(json.dumps(row) + "\n")


def gt_cb(msg):
    now = time.monotonic()
    if now - _gt_last[0] < 1.0 / 50:
        return
    for p in msg.pose:
        if p.name == MODEL:
            sim = msg.header.stamp.sec + msg.header.stamp.nsec / 1e9
            _w({"t": "gt", "mono": round(now, 4), "sim": round(sim, 4),
                "x": round(p.position.x, 5), "y": round(p.position.y, 5), "z": round(p.position.z, 5)})
            _gt_last[0] = now
            return


class EkfSub(Node):
    def __init__(self):
        super().__init__("gate_ekf")
        self.m = None
        self.create_subscription(VehicleLocalPosition, "/fmu/out/vehicle_local_position", self._cb, QOS)

    def _cb(self, m):
        self.m = m
        _w({"t": "ekf", "mono": round(time.monotonic(), 4), "ts": round(m.timestamp / 1e6, 4),
            "x": round(float(m.x), 4), "y": round(float(m.y), 4), "z": round(float(m.z), 4),
            "vx": round(float(m.vx), 4), "vy": round(float(m.vy), 4),
            "eph": round(float(m.eph), 4), "dead_reckoning": bool(m.dead_reckoning),
            "xy_reset_counter": int(m.xy_reset_counter)})


async def arm_retry(d):
    for i in range(40):
        try:
            await d.action.arm(); return True
        except (ActionError, Exception):    # ActionError (preflight) LUB gRPC (serwer wstaje)
            if i % 5 == 0:
                print(f"[gate] arm niegotowe retry #{i}", flush=True)
            await asyncio.sleep(3)
    return False


async def _wait_health(d):
    async for h in d.telemetry.health():
        if h.is_global_position_ok and h.is_home_position_ok:
            return True
    return False


async def main():
    global _f, _running
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    gn = GzNode()
    rclpy.init()
    ekf = EkfSub()
    d = System(); await d.connect(system_address="udpin://0.0.0.0:14540")
    async for s in d.core.connection_state():
        if s.is_connected:
            break
    # --- PREFLIGHT PARAM ASSERT (R-D1): assert-on-entry na CAŁEJ klasie JEDNYM setem (bez churn) ---
    poison = {}   # param POISON-CRITICAL != stan preflight (R-D3: wtedy bieg JAWNIE nieważny)
    for p, want in C.HARNESS_PARAM_PREFLIGHT.items():
        boot_v = await d.param.get_param_int(p)
        if p in C.HARNESS_PARAM_POISON_CRITICAL and boot_v != want:
            poison[p] = boot_v
        await d.param.set_param_int(p, want)    # WYMUŚ stan preflight niezależnie od rootfs/parameters.bson
    if poison:
        print(f"[gate] PREFLIGHT: zatrute paramy {poison} → wymuszono stan preflight (self-heal); "
              f"BIEG BĘDZIE OZNACZONY JAKO NIEWAŻNY (R-D3)", flush=True)
    try:
        healthy = await asyncio.wait_for(_wait_health(d), timeout=HEALTH_WAIT_TIMEOUT_S)
    except asyncio.TimeoutError:
        healthy = False
    if not healthy:
        print("[gate] HEALTH TIMEOUT — boot niezdatny (retry przez wrapper)", flush=True)
        try:
            for p, want in C.HARNESS_PARAM_PREFLIGHT.items():
                await d.param.set_param_int(p, want)   # zostaw zdrowy stan (best-effort)
        except Exception:
            pass
        os._exit(3)     # boot niezdatny → HARD exit (mavsdk/rclpy cleanup wisi) → wrapper retry

    shield = PatrolShield(); shield.reset()
    shield.pos_debounce_ticks = C.DEBOUNCE_TICKS
    shield.pos_hyst_ticks = int(round(C.HYST_M_S / C.DT))

    fh = open(OUT, "w"); _f = fh; _running = True
    _w({"t": "meta", "scen": SCEN, "schema_v": TRACE_SCHEMA_V, "eps_cap": C.EPS_CAP, "R_E": shield.cfg.r_e,
        "half_p": C.HALF_P, "vmax": VMAX, "debounce": C.DEBOUNCE_TICKS,
        "harness_valid": (not poison), "harness_poison": poison,
        "note": "osłona w pętli; GT=sędzia; velocity-descent dwufazowy na POS_DEGRADED"})
    gn.subscribe(Pose_V, GT_TOPIC, gt_cb)

    def ev(s):
        _w({"t": "event", "mono": round(time.monotonic(), 4), "ev": s})
        print(f"[gate {SCEN}] {s} mono={time.monotonic():.3f}", flush=True)

    # R-D3: twarda asercja w trace — boot startował z zatrutym paramem ⇒ bieg JAWNIE NIEWAŻNY (self-heal
    # naprawił stan, ale runu z brudnego wejścia NIE liczymy; wrapper go odrzuci i zrobi retry).
    if poison:
        _w({"t": "event", "mono": round(time.monotonic(), 4), "ev": "harness_invalid",
            "reason": f"boot param poison {poison} != preflight {C.HARNESS_PARAM_PREFLIGHT}"})
        print(f"[gate {SCEN}] HARNESS_INVALID: {poison} — bieg nieważny (R-D3)", flush=True)

    if not await arm_retry(d):
        print("[gate] ARM FAILED — boot niezdatny (retry przez wrapper)", flush=True)
        try:
            for p, want in C.HARNESS_PARAM_PREFLIGHT.items():
                await d.param.set_param_int(p, want)   # zostaw zdrowy stan (best-effort)
        except Exception:
            pass
        os._exit(2)     # arm nie przechodzi → HARD exit (cleanup wisi) → wrapper retry
    ev("armed")
    await d.action.set_takeoff_altitude(ALT); await d.action.takeoff(); ev("takeoff")
    await asyncio.sleep(10 + max(0.0, (ALT - 8.0) / 1.5))   # dojście na wysokość (S3=15 m potrzebuje więcej)
    await d.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))
    try:
        await d.offboard.start(); ev("offboard")
    except OffboardError as e:
        print("[gate] offboard err", e, flush=True); return

    # spin ekf w tle
    def spin():
        while _running and rclpy.ok():
            rclpy.spin_once(ekf, timeout_sec=0.02)
    th = threading.Thread(target=spin, daemon=True); th.start()

    # --- pętla OSŁONY (20 Hz), shield-driven przez CAŁY epizod (zejście też) ---
    wps = C.corner_waypoints_r03()          # trasa zredukowana (NED)
    tick = 0
    denial_done = False; recovery_done = False
    descending = False; desc_t0 = None; h_switched = False; td = False
    re_allowed = False; re_allow_t = None
    denial_t = None
    seg_i = 0
    dist = 1e9
    t_start = time.monotonic()
    denial_at = 12.0 if SCEN in ("S2", "S3") else 1e9    # S4: wyzwalane narożnikiem
    recovery_after = 1.5 if SCEN == "S3" else 1e9        # sekundy PO denialu (wcześnie → M zdąży przed touchdown)
    s1_dur = S1_MIN * 60.0 if SCEN == "S1" else 1e9
    desc_fast_dur = max(0.0, (ALT - C.H_SWITCH_AGL) / C.V_DESC_FAST)
    desc_total = desc_fast_dur + C.H_SWITCH_AGL / C.V_DESC_LAND + 1.5

    while True:
        now = time.monotonic() - t_start
        m = ekf.m
        if m is None:
            await asyncio.sleep(0.05); continue
        pos = (float(m.x), float(m.y), float(m.z))
        vel = (float(m.vx), float(m.vy), 0.0)
        dr = bool(m.dead_reckoning)
        r_est = math.hypot(pos[0], pos[1])
        # waypoint / dist (potrzebne PRZED triggerem S4)
        wp = wps[seg_i % len(wps)]
        dx, dy = wp[0] - pos[0], wp[1] - pos[1]
        dist = math.hypot(dx, dy)
        if dist < 1.0 and not descending:
            seg_i += 1
        tgt = (wp[0], wp[1], -ALT)
        # denial injection
        _k1_fa = None
        if SCEN == "S4":
            trigger = (not denial_done) and seg_i >= 1 and dist < 3.0 and now >= 8.0  # przy narożniku, v_max
        elif SCEN == "K1":
            _leg = math.hypot(wps[1][0] - wps[0][0], wps[1][1] - wps[0][1])   # długość 1. nogi po narożniku
            _k1_fa = (_leg - dist) / _leg if (seg_i == 1 and _leg > 1e-6) else -1.0
            trigger = (not denial_done) and seg_i == 1 and _k1_fa >= K1_POINT  # ułamek nogi
        else:
            trigger = (not denial_done) and now >= denial_at
        if trigger:
            await d.param.set_param_int("EKF2_GPS_CTRL", 0)
            _ev = {"t": "event", "mono": round(time.monotonic(), 4), "ev": "denial_on",
                   "r_est_at_cut": round(r_est, 3), "speed_at_cut": round(math.hypot(vel[0], vel[1]), 3)}
            if SCEN == "K1":
                _ev["k1_point"] = K1_POINT
                _ev["k1_f_along"] = round(_k1_fa, 3) if _k1_fa is not None else None
            _w(_ev)
            print(f"[gate {SCEN}] denial_on r_est={r_est:.2f} v={math.hypot(vel[0],vel[1]):.2f}", flush=True)
            denial_done = True; denial_t = now
        # recovery (S3): 0→7 w locie
        if SCEN == "S3" and denial_done and not recovery_done and denial_t is not None and (now - denial_t) >= recovery_after:
            await d.param.set_param_int("EKF2_GPS_CTRL", GPS_CTRL_NOMINAL); ev("denial_off"); recovery_done = True
        # decyzja osłony
        d_dec = shield.step(tick, pos, vel, tgt, mode=M_PATROL, pos_flag=(dr if denial_done else None))
        is_pos = (d_dec["decision"] == REFUSE and d_dec.get("reason") == POS_DEGRADED)
        # B3 (e) PRE_D §4: per-tick ε-budżet GPS-denied — r_est [m] i margin_R_E = R_E − r_est [m].
        _w({"t": "tick", "tick": tick, "mono": round(time.monotonic(), 4), "r_est": round(r_est, 3),
            "margin_R_E": round(shield.cfg.r_e - r_est, 3), "decision": d_dec["decision"],
            "reason": d_dec.get("reason"), "state": d_dec.get("state"),
            "pos": [round(v, 3) for v in pos], "dr": bool(dr), "descending": bool(descending)})

        if is_pos:
            if not descending:
                descending = True; desc_t0 = time.monotonic(); ev("refuse_pos_land")
            el = time.monotonic() - desc_t0
            if el < desc_fast_dur:
                vdesc = C.V_DESC_FAST
            else:
                if not h_switched:
                    ev("h_switch"); h_switched = True
                vdesc = C.V_DESC_LAND
            await d.offboard.set_velocity_ned(VelocityNedYaw(0, 0, vdesc, 0))
            if el >= desc_total and not td:
                ev("touchdown"); td = True
                break                                   # S2/S4 (i S3 bez re-ALLOW przed touchdown)
        else:
            # ALLOW (patrol LUB re-ALLOW po histerezie w S3)
            if descending and SCEN == "S3":
                if not re_allowed:
                    re_allowed = True; re_allow_t = now; ev("re_allow")
                await d.offboard.set_velocity_ned(VelocityNedYaw(0, 0, 0, 0))   # hold (bez oscylacji)
                if re_allow_t is not None and (now - re_allow_t) > 3.0:
                    ev("s3_reallow_confirmed"); break
            else:
                vn, ve = (VMAX * dx / dist, VMAX * dy / dist) if dist > 1e-3 else (0.0, 0.0)
                await d.offboard.set_velocity_ned(VelocityNedYaw(vn, ve, 0, 0))
        tick += 1
        if SCEN == "S1" and now >= s1_dur:
            ev("s1_done"); break
        _to_ref = (denial_t if denial_t is not None else denial_at)   # K1: denial_at=1e9 → użyj denial_t
        if now > (_to_ref + 90 if denial_done else max(s1_dur, 400) + 30):
            ev("timeout"); break
        await asyncio.sleep(C.DT)

    # księgowość osłony + telemetria
    _w({"t": "outcome", "n_pos_enter": shield.n_pos_enter,
        "terminal": (shield.terminal[0] if shield.terminal else None)})
    ev("done")
    await asyncio.sleep(2)
    # restore params (SR-B5) — do ZDROWYCH nominałów z białej listy (nie do odczytu z bootu). To tylko
    # sprzątanie; twardą gwarancją czystego wejścia jest preflight-asercja NASTĘPNEGO biegu (R-D1).
    for p, want in C.HARNESS_PARAM_PREFLIGHT.items():
        await d.param.set_param_int(p, want)
    print(f"[gate {SCEN}] restored do stanu preflight {C.HARNESS_PARAM_PREFLIGHT} (poison na wejściu: {poison})", flush=True)
    try:
        await d.offboard.stop()
    except Exception:
        pass
    try:
        await d.action.disarm()
    except Exception:
        pass
    with _lock:
        _running = False
    ekf.destroy_node(); rclpy.shutdown(); fh.close()
    print(f"[gate {SCEN}] done -> {OUT}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
