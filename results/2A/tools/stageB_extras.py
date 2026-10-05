#!/usr/bin/env python3
"""results/2A/tools/stageB_extras.py — uzupełnienie etapu B (PROMPT_2A_S2 §2) ponad percep_judge:
FP-admisje: ŚWIEŻE próbki tracku (fresh=true, trk_pos_ned≠None) odległe od GT intruza o > 5 m
= podejrzane wejścia tła — licznik + wypis (t_frame, err, box, conf, mti_ok, ev).
Interpolacja GT i oś czasu 1:1 z percep_judge (gt_flat/interp — import z frozen sędziego).
GT żyje wyłącznie offline (reguła nadrzędna)."""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from percep_judge import load_jsonl, gt_flat, interp   # frozen 363c37b7 — reuse, nie kopia


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shadow", required=True)
    ap.add_argument("--gt", required=True)
    ap.add_argument("--thr", type=float, default=5.0)
    ap.add_argument("--out")
    a = ap.parse_args()
    ts, ps = gt_flat(load_jsonl(a.gt))
    rows = load_jsonl(a.shadow)
    n_fresh = 0
    fps = []
    for r in rows:
        if not r.get("fresh") or not r.get("trk_pos_ned"):
            continue
        g = interp(ts, ps, r["t_frame"])
        if g is None:
            continue
        n_fresh += 1
        e = math.dist(r["trk_pos_ned"], g)
        if e > a.thr:
            fps.append({"t_frame": r["t_frame"], "err_m": round(e, 2), "box": r.get("box"),
                        "conf": r.get("conf"), "mti_ok": r.get("mti_ok"), "ev": r.get("ev")})
    out = {"shadow": a.shadow, "thr_m": a.thr, "n_fresh_in_gt_window": n_fresh,
           "n_fp_admissions": len(fps), "fp_list": fps[:50],
           "fp_truncated": max(0, len(fps) - 50)}
    print(json.dumps(out, indent=1))
    if a.out:
        with open(a.out, "w") as f:
            json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
