#!/usr/bin/env python3
"""results/NAD3_RECON/tools/nad3_r5_trening.py — PROMPT_NAD3_S0 R5: co sieć widziała w treningu (0 bootów).

Sieć (net_skan2 → NetController, net/frozen/ncp.npz) widzi pozycję własną tylko przez rel = trk_pos_ned − own_pos (wejścia 0–2,
bench/features.py). Skok ramy ΔΔ przesuwa own_net od razu, a track percepcji dopiero przy następnej świeżej klatce, więc rel
skacze o −ΔΔ na co najmniej jeden tick. Miara treningowa: per tick |Δ rel_xy| między kolejnymi wierszami tego samego epizodu
z track_valid w obu (demo.jsonl kampanii BENCH, bloki BLOCK1 + BLOCK2 z net/d0_dataset.py, wszystkie epizody — nadzbiór zbioru
treningowego); osobno |Δ trk_xy| przy odświeżeniu tracku (≠ 0) — szum FeedB. Wyjście: results/NAD3_RECON/r5_trening.json.
"""
import json
import os
import sys

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.dirname(os.path.abspath(__file__))]
import nad3_dane as N
from net.d0_dataset import BLOCK1, BLOCK2, CAMP


def main():
    drel, dtrk = [], []
    n_wier = 0
    for b in BLOCK1 + BLOCK2:
        p = os.path.join(CAMP, b, "demo.jsonl")
        if not os.path.exists(p):
            continue
        prev = None
        for l in open(p):
            try:
                r = json.loads(l)
            except ValueError:
                continue
            n_wier += 1
            key = (r.get("scenario_id"), r.get("seed"), r.get("attempt"))
            ok = r.get("track_valid") and r.get("trk_pos_ned") is not None
            if prev is not None and prev[0] == key and ok and prev[1] is not None:
                rel = np.array(r["trk_pos_ned"][:2]) - np.array(r["own_pos_ned"][:2])
                drel.append(float(np.linalg.norm(rel - prev[1])))
                dt = float(np.linalg.norm(np.array(r["trk_pos_ned"][:2]) - prev[2]))
                if dt > 1e-6:
                    dtrk.append(dt)
            prev = (key, (np.array(r["trk_pos_ned"][:2]) - np.array(r["own_pos_ned"][:2])) if ok else None,
                    np.array(r["trk_pos_ned"][:2]) if ok else None)
    drel, dtrk = np.array(drel), np.array(dtrk)
    out = {"n_wierszy": n_wier, "d_rel_xy_per_tick": N.rozklad(drel), "d_trk_xy_przy_odswiezeniu": N.rozklad(dtrk),
           "p99.9_d_rel": round(float(np.quantile(drel, .999)), 4),
           "frakcja_d_rel_gt": {str(x): round(float((drel > x).mean()), 6) for x in (0.5, 1.0, 2.0, 3.0)}}
    print(json.dumps(out, ensure_ascii=False))
    json.dump(out, open(os.path.join(N.OUT, "r5_trening.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
