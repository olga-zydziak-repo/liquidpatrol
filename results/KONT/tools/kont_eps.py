#!/usr/bin/env python3
"""results/KONT/tools/kont_eps.py — ε(t) od odcięcia przez gt_judge.py IMPORTEM (FROZEN 447efaa2; PROMPT_KONT_S1 §1.5).
T_home z okna zdrowego GNSS ≥ 20 s (compute_drift). Okno pomiaru = odcięcie (zdarzenie cut/denial) → przyziemienie GT z<0.15 m
(PRE §2.7). Flaga okna wstrzykiwana do kopii wierszy w pamięci, jak K2 w kont_r3_eps.py. Δ zejścia = max ε od początku zejścia do
przyziemienia minus ε na początku zejścia. Użycie: kont_eps.py <katalog bootu> [--out plik.json]"""
import hashlib
import json
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
B = os.path.join(ROOT, "results", "R03", "recon", "B1bis", "instrument")
sys.path.insert(0, B)
import gt_judge as J

GT_SHA8 = "447efaa2"
Z_GROUND = 0.15


def eps_curve(d, z_ground=Z_GROUND, fallback_land=None):
    ekf, gt, ev = [], [], {}
    for l in open(os.path.join(d, "trace.jsonl")):
        try:
            r = json.loads(l)
        except ValueError:
            continue
        if r.get("t") == "ekf":
            ekf.append(r)
        elif r.get("t") == "gt":
            gt.append(r)
        elif r.get("t") == "event":
            ev.setdefault(r["ev"], r)
    cut = (ev.get("cut") or ev["denial"])["mono"]
    desc = ev.get("descent_start", {}).get("mono") or ev.get("refuse", {}).get("mono")
    ekf.sort(key=lambda r: r["mono"]); gt.sort(key=lambda r: r["mono"])
    land = next((r["mono"] for r in gt if r["mono"] > cut and r["z"] < z_ground), None)
    land_win = land if land is not None else gt[-1]["mono"]
    for r in ekf:
        r["dead_reckoning"] = cut <= r["mono"] <= land_win
    m = J.compute_drift(ekf, gt)
    thx, thy = m["T_home"]
    ts = m["skew_hat_s"] if m["skew_applied"] else 0.0
    s = [(t - cut, math.hypot(ex - thx, ey - thy)) for (t, ex, ey) in J._paired_series(ekf, gt, True, ts) if cut <= t <= land_win]
    assert abs(max(x for _, x in s) - m["max_drift"]) < 0.01, (max(x for _, x in s), m["max_drift"])
    at = {str(k): next((round(x, 3) for t, x in s if t >= k), None) for k in (1, 2, 4, 5, 10, 15, 20, 30, 40, 50, 60, 70)}
    res = {"max_drift": m["max_drift"], "T_home": m["T_home"], "healthy_valid": m["healthy_valid"], "healthy_p95": m["healthy_p95_eps"],
           "skew_applied": m["skew_applied"], "skew_hat_s": m["skew_hat_s"], "t_land_gt_s": round(land - cut, 2) if land else None,
           "eps_at": at, "krzywa_1s": [[k, next(round(x, 3) for t, x in s if t >= k)] for k in range(int(s[-1][0]) + 1)]}
    if desc is not None:
        e0 = next((x for t, x in s if t >= desc - cut), None)
        res["t_descent_s"] = round(desc - cut, 2)
        if e0 is not None:
            res.update(eps_descent_start=round(e0, 3), delta_zejscia=round(max(x for t, x in s if t >= desc - cut) - e0, 3),
                       eps_max_przed_zejsciem=round(max(x for t, x in s if t < desc - cut), 3))
    return res


def main():
    assert hashlib.sha256(open(os.path.join(B, "gt_judge.py"), "rb").read()).hexdigest()[:8] == GT_SHA8
    res = eps_curve(sys.argv[1])
    if "--out" in sys.argv:
        json.dump(res, open(sys.argv[sys.argv.index("--out") + 1], "w"), ensure_ascii=False, indent=0)
    print(json.dumps({k: v for k, v in res.items() if k != "krzywa_1s"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
