#!/usr/bin/env python3
"""r03/gate_judge.py — sędzia bramki R0.3a (kryteria D13) z pliku biegu (ekf/gt/event/outcome).

GT WYŁĄCZNIE sędzią (nigdy w decyzji). ε_pos przez gt_judge (mono+skew+T_home, ramka home).
S2/S4 (+): (a) REFUSE ≤ debounce+1 tick (0.15 s) od zwalidowanej flagi; (b) touchdown wewnątrz R_E (GT);
(c) ε_pos ≤ ε_cap przez epizod; (d) 0 naruszeń R_E (GT); (e) nota natywna. Raport: r_est przy cięciu,
min margines zawierania R_E−r_true_max.
S1 (−): 0 fałszywych REFUSE(POS) + histogram flipów flagi dead_reckoning (SR-B3).
S3: histereza (re-ALLOW dopiero po M=5 s, zero oscylacji) + skok resetu EKF (xy_reset_counter) i ε po recovery.

Uruchom: PYTHONPATH=. python3 -m r03.gate_judge results/R03/gate/S2/run.jsonl
"""
import sys, json, math
sys.path.insert(0, "results/R03/recon/B1bis/instrument")
import gt_judge as J
from r03 import config as C
from r01.config import R_E

BOUND_S = C.POS_REFUSE_BOUND_S    # 0.15 s (debounce 2 ticki + 1 tick)
M_S = C.HYST_M_S                  # 5.0 s histereza


def _load(path):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    meta = next((r for r in rows if r.get("t") == "meta"), {})
    events = [r for r in rows if r.get("t") == "event"]
    ev_t = {}
    for r in events:
        ev_t.setdefault(r["ev"], r["mono"])
    outcome = next((r for r in rows if r.get("t") == "outcome"), {})
    ekf = [r for r in rows if r.get("t") == "ekf"]
    gt = [r for r in rows if r.get("t") == "gt"]
    denial_ev = next((r for r in events if r["ev"] == "denial_on"), {})
    return meta, ev_t, events, outcome, ekf, gt, denial_ev


def _flag_flips(ekf):
    """Histogram flipów dead_reckoning: liczba, czasy trwania True, czy w transiencie po boocie."""
    flips = []
    prev = None; t_true0 = None
    for r in sorted(ekf, key=lambda r: r["mono"]):
        v = bool(r.get("dead_reckoning"))
        if prev is not None and v != prev:
            flips.append((r["mono"], v))
            if v:
                t_true0 = r["mono"]
        prev = v
    n_flip = len(flips)
    # czasy trwania epizodów True
    durs = []
    stack = None
    for (t, v) in flips:
        if v:
            stack = t
        elif stack is not None:
            durs.append(round(t - stack, 3)); stack = None
    return {"n_flips": n_flip, "true_episode_durs_s": durs}


def judge(path):
    meta, ev_t, events, outcome, ekf, gt, denial_ev = _load(path)
    scen = meta.get("scen", "?")
    res = {"scen": scen, "eps_cap": meta.get("eps_cap"), "R_E": R_E,
           "n_pos_enter": outcome.get("n_pos_enter"), "terminal": outcome.get("terminal"),
           "events": [r["ev"] for r in events]}

    gt_r = [math.hypot(g["x"], g["y"]) for g in gt]
    gt_rmax = max(gt_r) if gt_r else None

    if scen == "S1":
        false_refuse = (outcome.get("n_pos_enter", 0) or 0) > 0 or "refuse_pos_land" in ev_t
        flips = _flag_flips(ekf)
        res["flag_flips"] = flips
        res["crit_minus_no_false_refuse"] = (not false_refuse)
        res["SR_B3_flag_flap"] = (flips["n_flips"] > 0)
        res["eph_passive_med"] = None
        ephs = sorted(r["eph"] for r in ekf if "eph" in r)
        if ephs:
            res["eph_passive_med"] = round(ephs[len(ephs) // 2], 3)
        res["PASS"] = (not false_refuse) and (flips["n_flips"] == 0)
        res["note"] = "SR-B3: flapowanie flagi → STOP przed S3 (bez strojenia def./debounce/histerezy)" \
            if flips["n_flips"] > 0 else "flaga stabilna w nominalu"
        return res

    # --- S2/S4/S3: epizod z denialem ---
    fdr = next((r["mono"] for r in sorted(ekf, key=lambda r: r["mono"]) if r.get("dead_reckoning")), None)
    t_refuse = ev_t.get("refuse_pos_land")
    if fdr and t_refuse:
        res["refuse_from_flag_s"] = round(t_refuse - fdr, 3)
        res["crit_a_refuse_timing"] = (t_refuse - fdr) <= BOUND_S + 1e-6
    res["r_est_at_cut"] = denial_ev.get("r_est_at_cut")
    res["speed_at_cut"] = denial_ev.get("speed_at_cut")

    # ε_pos (epizod)
    try:
        m = J.compute_drift(ekf, gt, swap=True)
        res["eps_pos"] = m["max_drift"]; res["healthy_p95"] = m.get("healthy_p95_eps")
        res["crit_c_eps_le_cap"] = m["max_drift"] <= C.EPS_CAP
    except Exception as e:
        res["eps_err"] = str(e); res["crit_c_eps_le_cap"] = None

    # touchdown + margines
    td = ev_t.get("touchdown")
    gt_at_td = None
    if td and gt:
        g = min(gt, key=lambda r: abs(r["mono"] - td)); gt_at_td = math.hypot(g["x"], g["y"])
    res["touchdown_gt_r"] = round(gt_at_td, 3) if gt_at_td is not None else None
    res["gt_rmax"] = round(gt_rmax, 3) if gt_rmax is not None else None
    res["margin_RE_minus_rmax"] = round(R_E - gt_rmax, 3) if gt_rmax is not None else None

    if scen in ("S2", "S4"):
        res["crit_b_touchdown_in_RE"] = (gt_at_td is not None and gt_at_td <= R_E)
        res["crit_d_no_RE_violation"] = (gt_rmax is not None and gt_rmax <= R_E)
        res["crit_e_native_note"] = "nav_state niemierzony w executorze — nota pustości (§2/A2)"
        crits = [res.get("crit_a_refuse_timing"), res.get("crit_b_touchdown_in_RE"),
                 res.get("crit_c_eps_le_cap"), res.get("crit_d_no_RE_violation")]
        res["PASS"] = all(x is True for x in crits)
        return res

    if scen == "S3":
        # kryterium: re-ALLOW dopiero po M od recovery; zero oscylacji REFUSE↔ALLOW
        t_off = ev_t.get("denial_off")      # recovery injection
        t_reallow = ev_t.get("re_allow")
        res["recovery_mono"] = t_off
        res["reallow_mono"] = t_reallow
        if t_off and t_reallow:
            res["reallow_after_recovery_s"] = round(t_reallow - t_off, 3)
            # re-ALLOW musi być ≥ M (od momentu, gdy zdrowie ciągłe; recovery+rekonwergencja)
            res["crit_reallow_after_M"] = (t_reallow - t_off) >= M_S - 1e-6
        # oscylacja: liczba przejść REFUSE↔ALLOW w eventach po recovery
        seq = [r["ev"] for r in events if r["ev"] in ("refuse_pos_land", "re_allow")]
        res["osc_events_seq"] = seq
        res["crit_no_oscillation"] = seq.count("re_allow") <= 1
        # skok resetu EKF + ε po recovery (rider S3)
        rc = [r.get("xy_reset_counter") for r in ekf if r.get("xy_reset_counter") is not None]
        res["xy_reset_span"] = (max(rc) - min(rc)) if rc else None
        # ε po recovery (informacyjnie — twierdzenie NIE obejmuje fazy recovery)
        res["eps_note"] = ("skok pozycji po re-konwergencji liczy się jako ε (ramka T_home stała); "
                           "jeśli ε>ε_cap po recovery — WYNIK (zakres poza twierdzeniem), nie FAIL S3")
        crits = [res.get("crit_reallow_after_M"), res.get("crit_no_oscillation")]
        res["PASS"] = all(x is True for x in crits)
        return res

    res["PASS"] = None
    return res


def main():
    for path in sys.argv[1:]:
        r = judge(path)
        print(f"\n== {path} ({r['scen']}) ==")
        for k, v in r.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
