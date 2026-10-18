#!/usr/bin/env python3
"""results/POSCIG_RECON/tools/poscig_sweep.py — pełny sweep artefaktu teleportu po kampaniach
FANTOM S2 i AKW S3 (oba ramiona, wszystkie epizody z index_episodes.json — wpis per para
po regule parowania). Liczy werdykt pełny vs odfiltrowany (poscig_artefakt.analyze) i skalę:
ile epizodów ma próbki artefaktu, ile flipów d_min/D6, wpływ na Δ kampanii.
Wynik: sweep_artefakt.json."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from poscig_artefakt import analyze, OUTDIR, ROOT


def main():
    idx = json.load(open(os.path.join(OUTDIR, "index_episodes.json")))
    out = []
    for key, rec in sorted(idx.items()):
        try:
            r = analyze(rec["dir"], rec["scenario_id"], key)
        except AssertionError as e:
            r = {"label": key, "error": str(e)}
        r["valid_final"] = rec.get("valid_final")
        out.append(r)
    # agregaty per kampania×ramię
    agg = {}
    for r in out:
        if "error" in r:
            continue
        camp, arm, _ = r["label"].split(":")
        a = agg.setdefault(f"{camp}:{arm}", {"n": 0, "n_bad_rows": 0, "flip_dmin": 0, "flip_D6": 0,
                                             "flip_D6_valid": 0})
        a["n"] += 1
        a["n_bad_rows"] += (1 if r["artefakt"]["n_rows_bad"] > 0 else 0)
        a["flip_dmin"] += (1 if r["flip_dmin"] else 0)
        a["flip_D6"] += (1 if r["flip_D6"] else 0)
        a["flip_D6_valid"] += (1 if (r["flip_D6"] and r.get("valid_final")) else 0)
    print(json.dumps(agg, indent=1))
    for r in out:
        if r.get("flip_D6"):
            print("FLIP:", r["label"], "valid=", r.get("valid_final"),
                  r["judge_full"]["d_min_m"], "->", r["judge_filtered"]["d_min_m"])
    json.dump({"agg": agg, "cases": out},
              open(os.path.join(OUTDIR, "sweep_artefakt.json"), "w"), indent=1)
    print("zapisano sweep_artefakt.json")


if __name__ == "__main__":
    main()
