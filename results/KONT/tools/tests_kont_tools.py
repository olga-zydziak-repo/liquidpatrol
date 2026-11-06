#!/usr/bin/env python3
"""Testy narzędzi KONT na danych K2 (PROMPT_KONT_S1 §1.5): k2c_b1 ma dać 4.00 s jak results/K2/ulog_wyciag_k2c.jsonl,
kont_eps ma odtworzyć krzywą K2 z kont_r3_eps."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
import kont_eps
import kont_ulog_extract as X

ref = {json.loads(l)["boot"]: json.loads(l) for l in open(os.path.join(ROOT, "results/K2/ulog_wyciag_k2c.jsonl"))}
for b in ("k2c_b1", "k2c_b6"):
    s = X.extract(os.path.join(ROOT, "results/K2", b, "boot.ulg"))[-1]
    for f in ("t_xy_invalid_s", "t_vxy_invalid_s", "t_offboard_lost_s", "t_nav_change_s"):
        assert round(s[f], 2) == ref[b][f], (b, f, s[f], ref[b][f])
    print("OK ulog", b, s["t_xy_invalid_s"], s["t_nav_change_s"])
r3 = {r["run"].split(":")[0]: r for r in json.load(open(os.path.join(ROOT, "results/KONT_RECON/r3_eps.json")))["runs"]}
e = kont_eps.eps_curve(os.path.join(ROOT, "results/K2/k2c_b1"), z_ground=0.2)
assert abs(e["max_drift"] - r3["k2c_b1"]["max_drift_sedzia"]) < 0.01, (e["max_drift"], r3["k2c_b1"]["max_drift_sedzia"])
assert e["eps_at"]["4"] == r3["k2c_b1"]["eps_at"]["4"], (e["eps_at"]["4"], r3["k2c_b1"]["eps_at"]["4"])
print("OK eps k2c_b1", e["max_drift"], e["eps_at"]["4"])
print("PASS")
