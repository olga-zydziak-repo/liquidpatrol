#!/usr/bin/env python3
"""results/TEACH_RECON/tools/teach_r2.py — PROMPT_TEACH_S0 R2: dwie serie klatek 5 Hz na lot (0 bootów).

Loty jak recon ORTO R2 (orto_r2.loty_klatek: 12 ważnych cięć S3 NAD3 + lot długi NAD2 L_c10_s01). Wiersze nf z nadir_obs.jsonl
(chwila klatki kamery w dół) z migawką EKF (ekf_q FRD→NED, ekf_pos NED) — wejście drona; poza GT z trace.jsonl (orto_r2.GT) — render
i ocena. Serie:
  „przed” — od początku zapisu do chwili cięcia (t_inj_sim zdarzenia „denial”), tylko klatki z wysokością EKF −z ≥ 6 m
            (selekcja po tym, co dron ma; wymóg promptu „wysokość ≥ 6 m”);
  „po”    — od cięcia do końca misji jak sędzia NAD3 — identycznie z orto_r2.klatki (te same 8609 klatek).
Wyjście: results/TEACH_RECON/r2_klatki.json.gz (lista wpisów; pole „seria”), r2_loty.json (liczności, chwile).
"""
import gzip
import json
import os
import sys

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, os.path.join(ROOT, "results/ORTO_RECON/tools"))
import orto_r2 as R2

N3 = R2.N3
OUT = os.path.join(ROOT, "results/TEACH_RECON")
H_MIN = 6.0


def main():
    po = {}
    for k in R2.klatki():                                           # seria „po” = recon ORTO R2 bez zmian
        po.setdefault(k["lot"], []).append(k)
    out, loty = [], {}
    for nazwa, d in R2.loty_klatek():
        g = R2.GT(d)
        den = next(e for e in N3.jl(d, "trace.jsonl", "event") if e.get("ev") == "denial")
        n = 0
        for r in N3.jl(d, "nadir_obs.jsonl", "nf"):
            if r["sim"] >= den["t_inj_sim"] or not r.get("ekf_pos") or not r.get("ekf_q") or -r["ekf_pos"][2] < H_MIN:
                continue
            p, q, dtg = g(r["sim"])
            out.append({"lot": nazwa, "seria": "przed", "sim": r["sim"], "od_ciecia": round(r["sim"] - den["t_inj_sim"], 3),
                        "gt_p": [round(x, 4) for x in p], "gt_q": [round(x, 6) for x in q], "gt_dt": round(dtg, 4),
                        "ekf_q": r["ekf_q"], "ekf_pos": r["ekf_pos"], "ekf_pos_age": r.get("ekf_pos_age")})
            n += 1
        for k in po[nazwa]:
            out.append(dict(k, seria="po"))
        loty[nazwa] = {"t_ciecia": den["t_inj_sim"], "przed": n, "po": len(po[nazwa]), "koniec_misji": po[nazwa][0]["koniec_misji"]}
        print(nazwa, loty[nazwa], flush=True)
    with gzip.open(os.path.join(OUT, "r2_klatki.json.gz"), "wt") as f:
        json.dump(out, f)
    json.dump(loty, open(os.path.join(OUT, "r2_loty.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
