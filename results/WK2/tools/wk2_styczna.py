#!/usr/bin/env python3
"""results/WK2/tools/wk2_styczna.py — opisowe (PRE_WK2 §3): składowa styczna komendy sieci i zrealizowana
w fazie orbity, per epizod (metoda ANEKS_WK-1 §1.3: mediana w oknie orbity).

Geometria z GT intruza (gt_intruder.jsonl, ned, najbliższy w czasie ≤ 0.1 s) i pozycji własnej z demo:
r̂ = (gt − own)_h / |·|, t̂ = (−r̂_E, r̂_N); |v_tan| komendy = |cmd_v_ned_h · t̂|, zrealizowana = |own_vel_ned_h · t̂|.
Okno: wiersze demo z phase == "orbit". Wyjście: mediany per epizod + stosunek zrealizowana/komenda.

Użycie: wk2_styczna.py <out.json> <katalog_boota>...
"""
import bisect
import json
import math
import os
import statistics as st
import sys


def main():
    out, dirs = sys.argv[1], sys.argv[2:]
    res = []
    for d in dirs:
        gt = [json.loads(l) for l in open(os.path.join(d, "gt_intruder.jsonl")) if l.strip()]
        gt = [g for g in gt if g.get("ned")]
        gts = [g["t_sim"] for g in gt]
        per = {}
        for ln in open(os.path.join(d, "demo.jsonl")):
            r = json.loads(ln)
            if r.get("phase") != "orbit":
                continue
            i = min(max(bisect.bisect_left(gts, r["t_sim"]), 0), len(gts) - 1)
            if abs(gts[i] - r["t_sim"]) > 0.1 or gt[i].get("scenario_id") != r["scenario_id"]:
                continue
            dn, de = gt[i]["ned"][0] - r["own_pos_ned"][0], gt[i]["ned"][1] - r["own_pos_ned"][1]
            dh = math.hypot(dn, de)
            if dh < 1e-3:
                continue
            tn, te = -de / dh, dn / dh
            c, v = r["cmd_v_ned"], r["own_vel_ned"]
            per.setdefault(r["scenario_id"], ([], []))
            per[r["scenario_id"]][0].append(abs(c[0] * tn + c[1] * te))
            per[r["scenario_id"]][1].append(abs(v[0] * tn + v[1] * te))
        for sid, (cv, rv) in per.items():
            mc, mr = st.median(cv), st.median(rv)
            res.append({"boot": os.path.relpath(d), "scenario_id": sid, "n": len(cv),
                        "v_tan_komenda_med": round(mc, 3), "v_tan_zrealizowana_med": round(mr, 3),
                        "realizacja": round(mr / mc, 3) if mc > 0 else None})
            print(res[-1])
    json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
