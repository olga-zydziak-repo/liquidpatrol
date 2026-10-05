#!/usr/bin/env python3
"""results/2A/tools/sanity_yaw.py — sanity naprawy N1 (ANEKS_2A-1 §4; miara naprawy, nie bramka
percepcji): mediana |yaw_drona − az(do TRACKU)| w fazie orbit, po ustaleniu, ≤ 15°.

az liczony DO TRACKU (demo.jsonl trk_pos_ned, track_valid) — to jest cel komendy yaw
kontrolera (atan2 ku trackowi, net_controller.py:115), więc miara odpowiada dokładnie temu,
co N1 miał naprawić (nos realnie śledzi komendę). yaw drona z kwaternionu GZ w trace
(konwersja ramek jak coverage_real — dowiedziona w S2 vs attitude PX4 p50 <1°).
„Po ustaleniu" = ticki orbit od t ≥ pierwszy_tick_orbit + 5.0 s (slew nosa po wejściu w pas)."""
from __future__ import annotations

import argparse
import bisect
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from coverage_real import load_jsonl, R_ned_frd_from_gz

SETTLE_ORBIT_S = 5.0
THRESH_DEG = 15.0


def wrap(a):
    while a > 180.0:
        a -= 360.0
    while a < -180.0:
        a += 360.0
    return a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bootdir")
    ap.add_argument("--out")
    a = ap.parse_args()
    demo = load_jsonl(os.path.join(a.bootdir, "demo.jsonl"))
    gt = [r for r in load_jsonl(os.path.join(a.bootdir, "trace.jsonl"))
          if r.get("t") == "gt" and "qw" in r]
    gts = [r["sim"] for r in gt]
    t_orb0 = next((r["t_sim"] for r in demo if r["phase"] == "orbit"), None)
    diffs = []
    for r in demo:
        if r["phase"] != "orbit" or not r.get("track_valid"):
            continue
        if t_orb0 is None or r["t_sim"] < t_orb0 + SETTLE_ORBIT_S:
            continue
        i = bisect.bisect_left(gts, r["t_sim"])
        cand = [j for j in (i - 1, i) if 0 <= j < len(gt)]
        if not cand:
            continue
        j = min(cand, key=lambda k: abs(gts[k] - r["t_sim"]))
        if abs(gts[j] - r["t_sim"]) > 0.1:
            continue
        g = gt[j]
        R = R_ned_frd_from_gz([g["qw"], g["qx"], g["qy"], g["qz"]])
        yaw = math.degrees(math.atan2(R[1, 0], R[0, 0]))
        own, trk = r["own_pos_ned"], r["trk_pos_ned"]
        az = math.degrees(math.atan2(trk[1] - own[1], trk[0] - own[0]))
        diffs.append(abs(wrap(yaw - az)))
    s = sorted(diffs)
    med = s[len(s) // 2] if s else None
    out = {"bootdir": a.bootdir, "n_ticks": len(s), "settle_orbit_s": SETTLE_ORBIT_S,
           "median_abs_deg": (round(med, 2) if med is not None else None),
           "p95_abs_deg": (round(s[int(len(s) * 0.95)], 2) if s else None),
           "thresh_deg": THRESH_DEG,
           "sanity_N1": (med is not None and med <= THRESH_DEG)}
    print(json.dumps(out, indent=1))
    if a.out:
        with open(a.out, "w") as f:
            json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
