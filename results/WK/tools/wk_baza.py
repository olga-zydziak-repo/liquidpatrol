#!/usr/bin/env python3
"""results/WK/tools/wk_baza.py — opisowe porównanie WK0 z bazą kamerową stock na tych samych scenariuszach
(c00–c07 × s01): sędzia bazowy 8ec0fcfb (import) na FANTOM S2 V2 (results/FANTOM/camp/r*_V2), świadek
ERRATUM-DMIN jak w wk_judge.py. Pomiar OPISOWY (PRE_WK §3), nie bramka.

Użycie: wk_baza.py <judge_wk0.json> <out.json>
"""
import glob
import json
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
for p in (ROOT, os.path.join(ROOT, "results", "POSCIG_RECON", "tools")):
    sys.path.insert(0, p)
from bench.bench_judge import judge_episode  # noqa: E402
from erratum_sweep import DEV_GATE, load_boot  # noqa: E402

SIDS = [f"c0{i}_s01" for i in range(8)]


def main():
    wk = {e["scenario_id"]: e["judge_swiadek"] for e in json.load(open(sys.argv[1]))["epizody"]}
    base = {}
    for d in sorted(glob.glob(os.path.join(ROOT, "results", "FANTOM", "camp", "r*_V2"))):
        eps, drone, intr = load_boot(os.path.relpath(d, ROOT))
        for e in eps.values():
            if e["sid"] not in SIDS or e["t1"] is None or e["sid"] in base:
                continue
            rows = [r for r in intr if r.get("scenario_id") == e["sid"] and e["t0"] <= r["t_sim"] <= e["t1"]]
            filt = [(r["t_sim"], r["ned"]) for r in rows
                    if math.hypot(r["ned"][0] - r["cmd_ned"][0], r["ned"][1] - r["cmd_ned"][1]) <= DEV_GATE]
            dr = [(s, n) for s, n in drone if e["t0"] <= s <= e["t1"]]
            v = judge_episode(dr, filt)
            base[e["sid"]] = {"boot": os.path.relpath(d, ROOT), "success_D6": v["success_D6"],
                              "sweep_deg": v["sweep_deg"], "t_entry_s": v["t_entry_s"],
                              "frac_band_6_10": round(v["frac_band_6_10"], 4), "d_min_m": v["d_min_m"]}
    rows = []
    for sid in SIDS:
        b, w = base.get(sid), wk.get(sid)
        rows.append({"scenario_id": sid, "stock_FANTOM_S2": b,
                     "WK0": {k: w[k] for k in ("success_D6", "sweep_deg", "t_entry_s", "frac_band_6_10", "d_min_m")} if w else None,
                     "sweep_ratio_WK0_do_stock": round(w["sweep_deg"] / b["sweep_deg"], 3) if (b and w and b["sweep_deg"]) else None})
        print(rows[-1])
    json.dump(rows, open(sys.argv[2], "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
