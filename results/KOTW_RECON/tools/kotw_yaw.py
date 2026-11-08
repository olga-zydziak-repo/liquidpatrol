#!/usr/bin/env python3
"""results/KOTW_RECON/tools/kotw_yaw.py — błąd yaw estymatora (EKF heading vs GT) w cięciach KONT S4, do R2.

Źródło: trace.jsonl (rekordy "ekf": heading [rad, NED]; "gt": kwaternion ENU) i wyniki_s4.json (t_cut, t_land w sim).
yaw_GT_NED = 90° − yaw_ENU(kwaternion). Złączenie po mono (najbliższy rekord ekf, |Δmono| ≤ 0.05 s).
Okna: przed cięciem (ostatnie 20 s, GNSS zdrowy) i od cięcia do lądowania (pod przepływem). Wyjście JSON na stdout.
Użycie: kotw_yaw.py <katalog_bootu> ...
"""
import bisect, json, math, sys, os

def load(p, t):
    return [json.loads(l) for l in open(p) if f'"t": "{t}"' in l]

def wrap(a):
    return (a + 180) % 360 - 180

out = {}
for d in sys.argv[1:]:
    w = json.load(open(os.path.join(d, "wyniki_s4.json")))["epizody"][0]
    tc, tl = w["t_cut"], w["t_land"]
    tr = os.path.join(d, "trace.jsonl")
    ek = load(tr, "ekf"); gt = [g for g in load(tr, "gt") if "qw" in g]
    em = [e["mono"] for e in ek]
    pre, kont = [], []
    for g in gt:
        i = bisect.bisect_left(em, g["mono"])
        if i >= len(ek) or abs(ek[i]["mono"] - g["mono"]) > 0.05 or "heading" not in ek[i]:
            continue
        qw, qx, qy, qz = g["qw"], g["qx"], g["qy"], g["qz"]
        y_enu = math.degrees(math.atan2(2 * (qw * qz + qx * qy), 1 - 2 * (qy * qy + qz * qz)))
        err = wrap(math.degrees(ek[i]["heading"]) - (90 - y_enu))
        if tc - 20 <= g["sim"] < tc:
            pre.append(err)
        elif tc <= g["sim"] <= tl:
            kont.append((g["sim"] - tc, err))
    s = lambda v: {"n": len(v), "mean": round(sum(v) / len(v), 2), "min": round(min(v), 2), "max": round(max(v), 2)} if v else None
    ke = [e for _, e in kont]
    out[os.path.basename(d)] = {"przed_cieciem": s(pre), "kontynuacja": s(ke),
                                "dryf_w_kont": round(max(ke) - min(ke), 2) if ke else None}
print(json.dumps(out, ensure_ascii=False, indent=1))
