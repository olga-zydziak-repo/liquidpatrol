#!/usr/bin/env python3
"""net/fresh_scenarios.py — świeże ziarna s11–s13 (PROMPT_NET_FLY N-F1a).

KONFLIKT/ODCHYLENIE (O-F1): prompt mówi „rozszerzenie bench/scenarios.py", ale scenarios.py jest
BAJT-PINOWANY w FREEZE_BENCH (fe4f2aeb…) — modyfikacja złamałaby SR-2. Bezpieczna droga: TEN SAM
generator `gen_episode(cell, seed)` UŻYWANY PRZEZ IMPORT (zero dotknięcia frozen pliku), ziarna 11–13.
Manifest bazowy e0527026 NIETKNIĘTY. Zgłoszone CC przy STOP-F0.

Świeży zbiór ZAMROŻONY commitem N-F1 (SR-6: nietykalny po commicie).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from bench.scenarios import gen_episode, CELLS, DISK_R, RANGE0, Z_INTR, EP_DUR_S   # import frozen generatora

FRESH_SEEDS = (11, 12, 13)


def gen_fresh_manifest():
    """36 epizodów: ziarna 11–13 × 12 komórek. Ten sam gen_episode co ławka (import)."""
    eps = []
    for seed in FRESH_SEEDS:
        for cell in CELLS:
            eps.append(gen_episode(cell, seed))
    for i, e in enumerate(eps):
        e["episode_id"] = i
    return {
        "n_episodes": len(eps), "n_cells": len(CELLS),
        "fresh_seeds": list(FRESH_SEEDS),
        "disk_r_m": DISK_R, "range0_m": RANGE0, "z_intr_m": Z_INTR, "ep_dur_s": EP_DUR_S,
        "note": "świeże ziarna s11-s13 (raport-only, luka uogólnienia PRE_NET N6); generator=bench.scenarios.gen_episode (import, scenarios.py fe4f2aeb NIETKNIĘTY)",
        "cells": CELLS, "episodes": eps,
    }


if __name__ == "__main__":
    m = gen_fresh_manifest()
    outp = os.path.join(ROOT, "results", "NET", "FLY", "scenario_manifest_fresh.json")
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    json.dump(m, open(outp, "w"), indent=2)
    print(f"fresh manifest: {m['n_episodes']} epizodów, ziarna {m['fresh_seeds']} × {m['n_cells']} komórek")
