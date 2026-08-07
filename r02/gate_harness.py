"""r02/gate_harness.py — DETERMINISTYCZNY harness pętli zamkniętej bramki (G1–G4, logika).

Waliduje LOGIKĘ bramki na PRAWDZIWYM kodzie R0.2: osłona `PatrolShield` (7 liści), kanał
`TargetChannel` (ZOH-age), naprowadzanie `observe_guidance` — sprzężone z:
  - INTRUZ: deterministyczna trajektoria `intruder_driver.scripted_pose(sim_t)` (znana, powtarzalna),
  - DRON: kinematyczny model punktowy (pos += clamp(setpoint−pos, v_max·dt)); yaw śledzi estymatę,
  - DETEKTOR: IDEALNY model projekcji kamery (intruz→piksel; w FOV ⇔ box). Harness testuje
    KANAŁ+STEROWANIE, NIE jakość detekcji (to G1/G2 na żywym symie). Rozłączność jawnie zaznaczona.

Zakres: G1 (ε_FP=0, brak intruza), G2 (ENTRY≤T_ack, d≥D_safe, f_fov), G3 (prowadzenie→R-G REFUSE,
≤R_E), G4 (utrata→age+sufit→wyjście OBSERVE). **G5 (natywny failsafe warstwy-0) = TYLKO żywy sim**
(PX4 COM_OF_LOSS_T) — poza harnessem, w `r02/gate_run_r02.py`.

Kryteria = ZAMROŻONE progi z `config_r02` (A4, prowizoryczne+związane z bramką). Uruchom:
  python3 -m r02.gate_harness            (exit 0 = wszystkie logiczne PASS)
"""
from __future__ import annotations
import math, sys, json

from r01.shield import PatrolShield, ALLOW, HOLD, REFUSE, GEOFENCE, M_PATROL, M_OBSERVE
from r01.config import R_E, V_MAX, ALT_M, DT, corner_waypoints
from r02.config_r02 import (D_SAFE_M, THETA_AGE_S, T_ACK_S, F_FOV, EPS_FP_PER_MIN,
                            INTRUDER_ALT_M, DET_DT, ChannelConfig)
from r02.target_channel import TargetChannel, Box
from r02.observe_guidance import HFOV, VFOV, ObserveController
from r02.intruder_driver import scripted_pose

TICK = DT                      # 0.05 s (20 Hz osłona)


# ------------------------- model projekcji kamery (idealny detektor) --------
def project_to_pixel(pos, yaw, intr):
    """Prawdziwy intruz NED → (cx,cy,w,h)|None. None gdy poza FOV / za dronem.
    Odwrotność observe_guidance.bearing_from_pixel (spójna geometria)."""
    wx, wy, wz = intr[0] - pos[0], intr[1] - pos[1], intr[2] - pos[2]
    # świat → body (obrót o −yaw wokół z)
    bx = math.cos(yaw) * wx + math.sin(yaw) * wy
    by = -math.sin(yaw) * wx + math.cos(yaw) * wy
    bz = wz
    if bx <= 0.1:
        return None                                    # za dronem / zbyt blisko płaszczyzny nosa
    az = math.atan2(by, bx)
    el = math.atan2(-bz, math.hypot(bx, by))
    if abs(az) > HFOV / 2.0 or abs(el) > VFOV / 2.0:
        return None                                    # poza FOV
    cx = 0.5 + math.tan(az) / (2.0 * math.tan(HFOV / 2.0))
    cy = 0.5 - math.tan(el) / (2.0 * math.tan(VFOV / 2.0))
    dist = math.sqrt(wx * wx + wy * wy + wz * wz)
    ang = 1.0 / max(dist, 1.0)                          # pozorny rozmiar ~1/odl (intruz ~1 m)
    w = min(0.4, ang); h = min(0.4, ang)
    return Box(cx, cy, w, h, conf=0.5)                 # conf tylko log (A1) — nie wchodzi do kanału


# ------------------------- kinematyczny dron --------------------------------
class KinDrone:
    """Punktowy model: pos→setpoint z clampem prędkości v_max; yaw śledzi zadany kurs (rate-limit)."""
    def __init__(self, pos, yaw=0.0):
        self.pos = list(pos); self.prev = list(pos); self.yaw = yaw
        self.vmax = V_MAX; self.dt = TICK; self.yaw_rate = math.radians(90)  # 90°/s
    def vel(self):
        return [(self.pos[i] - self.prev[i]) / self.dt for i in range(3)]
    def step(self, setpoint, yaw_cmd=None):
        self.prev = list(self.pos)
        for i in range(3):
            d = setpoint[i] - self.pos[i]
            step = max(-self.vmax * self.dt, min(self.vmax * self.dt, d))
            self.pos[i] += step
        if yaw_cmd is not None:
            dyaw = math.atan2(math.sin(yaw_cmd - self.yaw), math.cos(yaw_cmd - self.yaw))
            m = self.yaw_rate * self.dt
            self.yaw += max(-m, min(m, dyaw))


def yaw_to(pos, target):
    return math.atan2(target[1] - pos[1], target[0] - pos[0])


# ------------------------- pętla scenariusza --------------------------------
def run_loop(*, intruder_fn, duration_s, mode_seq, start=(0.0, 0.0, -ALT_M),
             observe_authority=True, planner_wp=None):
    """Jedna pętla zamknięta. intruder_fn(sim_t)->(N,E,D)|None (None=brak intruza w świecie).
    mode_seq(t, locked)->mode osłony. Zwraca dict metryk. Detektor @DET_DT, osłona @TICK."""
    ch = TargetChannel(ChannelConfig())
    sh = PatrolShield(); sh.reset()
    ctrl = ObserveController(d_safe=D_SAFE_M, alt=ALT_M)    # ZOH estymaty świata (nie piksela)
    drone = KinDrone(start, yaw=0.0)
    wps = planner_wp or corner_waypoints()
    wp_idx = 0
    t = 0.0
    next_det = 0.0
    n_ticks = int(duration_s / TICK)
    max_r = 0.0
    entry_t = None
    intruder_in_fov_first = None
    observe_ticks = 0
    fov_hit_ticks = 0
    dsafe_violations = 0
    min_d_observe = float("inf")
    native_gf = 0                      # w harnessie natywnego GF nie ma (to live) — zawsze 0
    refuse_reason = None
    trace = []
    for k in range(n_ticks):
        t = k * TICK
        intr = intruder_fn(t)
        # DETEKTOR @1 Hz: projekcja prawdziwego intruza (idealny) → kanał
        if t >= next_det - 1e-9:
            box = project_to_pixel(drone.pos, drone.yaw, intr) if intr is not None else None
            ev = ch.on_frame(box, t, gt_present=(intr is not None and box is not None))
            if box is not None:
                ctrl.on_detection(drone.pos, drone.yaw, box)   # ZAMROŹ estymatę świata (poza z tej klatki)
            if ev == "EXPIRE":
                ctrl.reset()
            if ev == "ENTRY" and entry_t is None:
                entry_t = t
            # kiedy intruz PIERWSZY raz realnie w FOV (do T_ack)
            if intruder_in_fov_first is None and box is not None and intr is not None:
                intruder_in_fov_first = t
            next_det += DET_DT
        else:
            if ch.tick_time(t) == "EXPIRE":
                ctrl.reset()               # egzekwuj sufit między klatkami + resetuj kontroler
        val = ch.sample(t)
        locked = ch.locked and not ch.is_expired(t)
        mode = mode_seq(t, locked)
        # setpoint wg trybu
        yaw_cmd = None
        if mode == M_OBSERVE and ctrl.has_estimate():
            sp = ctrl.setpoint(drone.pos)              # pierścień D_safe wokół ZAMROŻONEJ estymaty
            if sp is None:
                sp = list(drone.pos)
            yaw_cmd = ctrl.yaw_cmd(drone.pos)          # kurs na zamrożoną estymatę (stabilny)
        else:
            wp = wps[wp_idx % len(wps)]
            sp = [wp[0], wp[1], wp[2]]
            if math.hypot(drone.pos[0]-wp[0], drone.pos[1]-wp[1]) <= 1.5:
                wp_idx += 1
        # OSŁONA decyduje (7 liści; R-G nadrzędny)
        d = sh.step(k, drone.pos, drone.vel(), sp, mode=mode)
        applied = d["applied"]
        if d["decision"] == REFUSE:
            refuse_reason = d["reason"]
        # metryki OBSERVE
        if mode == M_OBSERVE and locked:
            observe_ticks += 1
            dd = ctrl.h_distance(drone.pos)
            if dd is not None:
                min_d_observe = min(min_d_observe, dd)
                if dd < D_SAFE_M - 0.5:                # 0.5 m tolerancja modelu
                    dsafe_violations += 1
            # czy prawdziwy intruz w FOV w tym ticku?
            if intr is not None and project_to_pixel(drone.pos, drone.yaw, intr) is not None:
                fov_hit_ticks += 1
        # ruch drona wg APPLIED (osłona) — HOLD/REFUSE => hold-setpoint
        drone.step(applied, yaw_cmd=yaw_cmd)
        max_r = max(max_r, math.hypot(drone.pos[0], drone.pos[1]))
        trace.append({"k": k, "t": round(t, 2), "mode": mode, "dec": d["decision"],
                      "reason": d["reason"], "rule": d["rule"], "locked": locked,
                      "pos": [round(v, 2) for v in drone.pos], "r": round(math.hypot(*drone.pos[:2]), 2)})
        if d["decision"] == REFUSE and refuse_reason == GEOFENCE:
            break                                     # latch terminal (G3)
    return {
        "entry_t": entry_t, "intruder_in_fov_first": intruder_in_fov_first,
        "t_ack": (entry_t - intruder_in_fov_first)
                 if (entry_t is not None and intruder_in_fov_first is not None) else None,
        "observe_ticks": observe_ticks, "fov_hit_ticks": fov_hit_ticks,
        "f_fov": (fov_hit_ticks / observe_ticks) if observe_ticks else None,
        "dsafe_violations": dsafe_violations,
        "min_d_observe": None if min_d_observe == float("inf") else round(min_d_observe, 2),
        "max_r": round(max_r, 2), "refuse_reason": refuse_reason, "native_gf": native_gf,
        "n_entry": ch.n_entry, "n_false_entry": ch.n_false_entry, "n_expire": ch.n_expire,
        "final_state": sh.state, "final_locked": ch.locked, "trace_tail": trace[-3:],
    }


# ------------------------- scenariusze G1–G4 --------------------------------
def g1_nominal():
    """G1: patrol bez intruza — detektor żywy, 0 ENTRY (ε_FP), patrol jak R0.1."""
    m = run_loop(intruder_fn=lambda t: None, duration_s=60.0,
                 mode_seq=lambda t, locked: M_PATROL)
    fp_per_min = m["n_false_entry"] / (60.0 / 60.0)
    crit = {"n_entry": m["n_entry"], "n_false_entry": m["n_false_entry"],
            "eps_fp_per_min": fp_per_min, "eps_fp_ok": fp_per_min <= EPS_FP_PER_MIN,
            "max_r": m["max_r"], "inside_R_E": m["max_r"] <= R_E}
    crit["PASS"] = crit["eps_fp_ok"] and crit["inside_R_E"] and m["n_entry"] == 0
    return "G1", crit, m


def _intr_lateral(t):
    """G2 intruz: wchodzi w FOV z przodu (x≈12), ŁAGODNY oscylacyjny ruch boczny (śledzalny —
    test „utrzymania w FOV", nie adwersarialnej geometrii). Wysokość 6 m (paralaksa bearing-only)."""
    y = 5.0 * math.sin(0.35 * t)          # ±5 m boczny, powolny
    return (12.0, y, -INTRUDER_ALT_M)


def g2_detect_observe():
    """G2: intruz wchodzi w FOV → ENTRY≤T_ack → OBSERVE, d≥D_safe, cel w FOV ≥ f_fov."""
    # OBSERVE autorytet on; tryb = OBSERVE gdy lock, inaczej patrol (mini, dron blisko Home patrzy N)
    m = run_loop(intruder_fn=_intr_lateral, duration_s=25.0,
                 mode_seq=lambda t, locked: M_OBSERVE if locked else M_PATROL,
                 start=(0.0, 0.0, -ALT_M), planner_wp=[(2.0, 0.0, -ALT_M)])
    crit = {"entry": m["entry_t"] is not None, "t_ack": m["t_ack"],
            "t_ack_ok": (m["t_ack"] is not None and m["t_ack"] <= T_ACK_S),
            "min_d_observe": m["min_d_observe"], "dsafe_violations": m["dsafe_violations"],
            "dsafe_ok": m["dsafe_violations"] == 0,
            "f_fov": m["f_fov"], "f_fov_ok": (m["f_fov"] is not None and m["f_fov"] >= F_FOV),
            "observe_ticks": m["observe_ticks"]}
    crit["PASS"] = (crit["entry"] and crit["t_ack_ok"] and crit["dsafe_ok"]
                    and crit["f_fov_ok"] and m["observe_ticks"] > 0)
    return "G2", crit, m


def _intr_toward_fence(t):
    """Intruz prowadzi dron w stronę płotu: leci na wschód (+y) coraz dalej, ciągnąc setpoint
    OBSERVE poza R_E. Zaczyna w FOV z przodu, potem odjeżdża na +x poza obwiednię."""
    # rusza z (12,0) i leci na Północ (+x) rosnąco — dron goni na pierścieniu D_safe → za płot
    x = 12.0 + 3.0 * t                    # +x rośnie: 12 → poza R_E=32 po ~7 s
    return (x, 0.0, -INTRUDER_ALT_M)


def g3_lead_to_fence():
    """G3: intruz prowadzi w stronę płotu → setpoint OBSERVE za obwiednię → R-G REFUSE(GEOFENCE),
    dron ≤R_E, native GF=0 (osłona uprzedza). ODMOWA (≠porażka)."""
    m = run_loop(intruder_fn=_intr_toward_fence, duration_s=30.0,
                 mode_seq=lambda t, locked: M_OBSERVE if locked else M_PATROL,
                 start=(0.0, 0.0, -ALT_M), planner_wp=[(2.0, 0.0, -ALT_M)])
    crit = {"refuse_reason": m["refuse_reason"],
            "refuse_is_geofence": m["refuse_reason"] == GEOFENCE,
            "max_r": m["max_r"], "inside_R_E": m["max_r"] <= R_E,
            "native_gf": m["native_gf"], "native_gf_ok": m["native_gf"] == 0}
    crit["outcome"] = "ODMOWA" if crit["refuse_is_geofence"] else "?"
    crit["PASS"] = crit["refuse_is_geofence"] and crit["inside_R_E"] and crit["native_gf_ok"]
    return "G3", crit, m


def _intr_vanish(t):
    """Intruz widoczny do t=6 s, potem znika (wychodzi z FOV/świata) — test utraty detekcji."""
    if t < 6.0:
        y = 5.0 * math.sin(0.35 * t)
        return (12.0, y, -INTRUDER_ALT_M)
    return None                           # zniknął — brak detekcji → ZOH → age rośnie → sufit


def g4_loss_age_ceiling():
    """G4: utrata detekcji → ZOH utrzymuje kanał, age rośnie, przy age>θ_age wyjście z OBSERVE
    do PATROL (nie ślepy finisz na starej detekcji), brak dryfu/padu."""
    m = run_loop(intruder_fn=_intr_vanish, duration_s=20.0,
                 mode_seq=lambda t, locked: M_OBSERVE if locked else M_PATROL,
                 start=(0.0, 0.0, -ALT_M), planner_wp=[(2.0, 0.0, -ALT_M)])
    crit = {"entered_observe": m["entry_t"] is not None, "n_expire": m["n_expire"],
            "expired": m["n_expire"] >= 1, "final_locked": m["final_locked"],
            "exited_to_patrol": (not m["final_locked"]) and m["final_state"] in ("PATROL",),
            "max_r": m["max_r"], "inside_R_E": m["max_r"] <= R_E}
    crit["PASS"] = (crit["entered_observe"] and crit["expired"]
                    and crit["exited_to_patrol"] and crit["inside_R_E"])
    return "G4", crit, m


def main():
    print("=== R0.2 harness bramki (G1–G4 LOGIKA, detektor-idealny) ===")
    print("    UWAGA: harness testuje KANAŁ+STEROWANIE+OSŁONĘ (7 liści), NIE jakość detekcji")
    print("    ani natywny failsafe (G5) — te tylko na żywym symie (r02/gate_run_r02.py).\n")
    results = []
    for fn in (g1_nominal, g2_detect_observe, g3_lead_to_fence, g4_loss_age_ceiling):
        gid, crit, m = fn()
        results.append((gid, crit))
        print(f"[{gid}] {'PASS' if crit['PASS'] else 'FAIL'}")
        print("   crit:", json.dumps({k: v for k, v in crit.items() if k != "trace_tail"},
                                      ensure_ascii=False))
    allpass = all(c["PASS"] for _, c in results)
    print(f"\nWERDYKT harness G1–G4 (logika): {'PASS' if allpass else 'FAIL'}")
    sys.exit(0 if allpass else 1)


if __name__ == "__main__":
    main()
