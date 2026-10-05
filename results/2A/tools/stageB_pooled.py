#!/usr/bin/env python3
"""results/2A/tools/stageB_pooled.py — etap B ŁĄCZNIE (PROMPT_2A_S2 §2: „per boot i łącznie").
Próbki budowane per boot DOKŁADNIE przepisem percep_judge.judge_shadow (import frozen 363c37b7 —
osie czasu bootów NIE są mieszane przy interpolacji GT), po czym zlane i zagregowane tym samym
_accumulate. Latencja: pula (t_update_sim − t_frame) ze wszystkich bootów."""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from percep_judge import load_jsonl, gt_flat, interp, _accumulate, _stats


def boot_samples(bootdir):
    rows = load_jsonl(os.path.join(bootdir, "shadow_feed.jsonl"))
    ts, ps = gt_flat(load_jsonl(os.path.join(bootdir, "gt_intruder.jsonl")))
    samples, lat = [], []
    last_trk = None
    for r in rows:
        if r.get("trk_pos_ned"):
            last_trk = r["trk_pos_ned"]
        if not r.get("locked") or last_trk is None:
            continue
        g = interp(ts, ps, r["t_frame"])
        if g is None:
            continue
        samples.append((r["t_frame"], r.get("own_pos_ned"), last_trk, g, bool(r.get("fresh"))))
        if r.get("fresh") and r.get("t_update_sim") is not None:
            lat.append(r["t_update_sim"] - r["t_frame"])
    return samples, lat


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bootdirs", nargs="+")
    ap.add_argument("--out")
    a = ap.parse_args()
    samples, lat = [], []
    for bd in a.bootdirs:
        s, l = boot_samples(bd)
        samples.extend(s)
        lat.extend(l)
    out = {"mode": "shadow-pooled", "src": a.bootdirs, "latency_s": _stats(lat) if lat else None}
    # UWAGA: kadencja z _accumulate liczona na posortowanych odstępach świeżych W OBRĘBIE puli;
    # osie sim bootów się nakładają — odstępy międzybootowe odfiltrowane sortowaniem per boot:
    # tu sortujemy świeże czasy per boot już w samples (kolejność bootdirs), gap<5 s tnie resztę.
    _accumulate(samples, out)
    print(json.dumps(out, indent=1))
    if a.out:
        with open(a.out, "w") as f:
            json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
