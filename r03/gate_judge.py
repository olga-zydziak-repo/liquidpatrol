#!/usr/bin/env python3
"""r03/gate_judge.py — sędzia bramki R0.3a (kryteria D13) z pliku biegu (ekf/gt/event/outcome).

GT WYŁĄCZNIE sędzią (nigdy w decyzji). ε_pos przez gt_judge (mono+skew+T_home, ramka home).
D13(+): (a) REFUSE ≤ debounce+1 tick (0.15 s) od zwalidowanej flagi; (b) touchdown wewnątrz R_E (GT);
(c) ε_pos ≤ ε_cap przez epizod; (d) 0 naruszeń R_E (GT); (e) nota natywna. D13(−): 0 fałszywych REFUSE(POS) w S1.

Uruchom: PYTHONPATH=. python3 -m r03.gate_judge results/R03/gate/S2_run.jsonl
"""
import sys, json, math
sys.path.insert(0, "results/R03/recon/B1bis/instrument")
import gt_judge as J
from r03 import config as C
from r01.config import R_E

BOUND_S = C.POS_REFUSE_BOUND_S    # 0.15 s (debounce 2 ticki + 1 tick)


def judge(path):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    meta = next((r for r in rows if r.get("t") == "meta"), {})
    scen = meta.get("scen", "?")
    events = {r["ev"]: r["mono"] for r in rows if r.get("t") == "event"}
    outcome = next((r for r in rows if r.get("t") == "outcome"), {})
    ekf = [r for r in rows if r.get("t") == "ekf"]
    gt = [r for r in rows if r.get("t") == "gt"]

    # GT max |pos| (naruszenie R_E) — GT to gz ENU; |xy| promień od origin (home≈world, T_home≈0)
    gt_r = [math.hypot(g["x"], g["y"]) for g in gt]
    gt_rmax = max(gt_r) if gt_r else None
    # touchdown: GT |pos| w chwili touchdown (ostatnie gt przed/na evencie)
    td = events.get("touchdown")
    gt_at_td = None
    if td and gt:
        g = min(gt, key=lambda r: abs(r["mono"] - td))
        gt_at_td = math.hypot(g["x"], g["y"])

    res = {"scen": scen, "eps_cap": meta.get("eps_cap"), "R_E": R_E,
           "n_pos_enter": outcome.get("n_pos_enter"), "terminal": outcome.get("terminal"),
           "events": sorted(events.keys())}

    if scen == "S1":
        # (−): 0 fałszywych REFUSE(POS)
        false_refuse = outcome.get("n_pos_enter", 0) > 0 or "refuse_pos_land" in events
        res["crit_minus_no_false_refuse"] = (not false_refuse)
        res["PASS"] = (not false_refuse)
        return res

    # (a) REFUSE ≤ bound od zwalidowanej flagi (first dead_reckoning=True)
    fdr = next((r["mono"] for r in ekf if r.get("dead_reckoning")), None)
    t_refuse = events.get("refuse_pos_land")
    a_ok = None
    if fdr and t_refuse:
        dt = t_refuse - fdr
        res["refuse_from_flag_s"] = round(dt, 3)
        a_ok = dt <= BOUND_S + 1e-6
    res["crit_a_refuse_timing"] = a_ok
    # (b) touchdown wewnątrz R_E
    b_ok = (gt_at_td is not None and gt_at_td <= R_E)
    res["touchdown_gt_r"] = round(gt_at_td, 3) if gt_at_td is not None else None
    res["crit_b_touchdown_in_RE"] = b_ok
    # (c) ε_pos ≤ ε_cap (epizod = denial→touchdown)
    try:
        m = J.compute_drift(ekf, gt, swap=True)
        eps = m["max_drift"]
        res["eps_pos"] = eps
        res["healthy_p95"] = m.get("healthy_p95_eps")
        c_ok = eps <= C.EPS_CAP
    except Exception as e:
        eps = None; c_ok = None; res["eps_err"] = str(e)
    res["crit_c_eps_le_cap"] = c_ok
    # (d) 0 naruszeń R_E (GT)
    d_ok = (gt_rmax is not None and gt_rmax <= R_E)
    res["gt_rmax"] = round(gt_rmax, 3) if gt_rmax is not None else None
    res["crit_d_no_RE_violation"] = d_ok
    # (e) nota natywna (bez nav_state w tym executorze — nota)
    res["crit_e_native_note"] = "nav_state niemierzony w tym executorze — nota pustości (§2/A2)"

    crits = [a_ok, b_ok, c_ok, d_ok]
    res["PASS"] = all(x is True for x in crits)
    return res


def main():
    for path in sys.argv[1:]:
        r = judge(path)
        print(f"\n== {path} ({r['scen']}) ==")
        for k, v in r.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
