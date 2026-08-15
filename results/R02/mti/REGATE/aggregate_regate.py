#!/usr/bin/env python3
"""results/R02/mti/REGATE/aggregate_regate.py — agregat bramki REGATE ×3 booty (ENTRY-once).

Kryterium (ANEKS_MTI_2 AM2.2): (+) ENTRY ∧ coverage_entry_once ≥0.8 (mediana per boot) na {7,9} m;
5 m informacyjnie (R-5). (−) 0 fałszywych ENTRY na obu scenach ×3, z dekompozycją koniunktów.
Wejście: results/R02/mti/REGATE/<boot>/result.json. Wyjście: REGATE/B_regate_aggregate.json.
"""
import json
import os
import statistics as st

REGATE = os.path.join("/home/olga/projects/liquidpatrol/results/R02/mti/REGATE")
BOOTS = sorted(b for b in os.listdir(REGATE)
               if os.path.isdir(os.path.join(REGATE, b))
               and os.path.exists(os.path.join(REGATE, b, "result.json")))
RANGES = ["5m", "7m", "9m"]
CRIT = ["7m", "9m"]   # kryterium (+); 5m informacyjnie

data = {b: json.load(open(os.path.join(REGATE, b, "result.json"))) for b in BOOTS}


def aneks_h(b):
    r = data[b]
    hp = open(os.path.join(REGATE, b, "headless_proof.txt")).read()
    tj_pre = open(os.path.join(REGATE, b, "timejump_pre.txt")).read().strip()
    tj_post = open(os.path.join(REGATE, b, "timejump_post.txt")).read().strip()
    ekf = open(os.path.join(REGATE, b, "ekf_health_hits.txt")).read().strip()
    whash = open(os.path.join(REGATE, b, "world_hash.txt")).read().split()[0][:16]
    def rtf_val(s): return float(s.split(":")[-1])
    valid = ("GUI_PROCS=[brak]" in hp and tj_pre == "0" and tj_post == "0"
             and whash == "a76a38c83cc774d3" and r["trace"]["complete"])
    return {"headless": "GUI_PROCS=[brak]" in hp, "timejump_pre": tj_pre, "timejump_post": tj_post,
            "ekf_health_hits": ekf, "world_hash16": whash,
            "rtf_start": round(rtf_val(r["rtf_start"]), 5), "rtf_end": round(rtf_val(r["rtf_end"]), 5),
            "trace_complete": r["trace"]["complete"], "valid": bool(valid)}


aneks = {b: aneks_h(b) for b in BOOTS}
valid_boots = [b for b in BOOTS if aneks[b]["valid"]]

# (+) ENTRY-once
plus = {}
for rng in RANGES:
    ceo, ce, te, cg, cs = [], [], [], [], []
    for b in valid_boots:
        p = data[b]["phases"].get(f"sweep_{rng}")
        if not p:
            continue
        ceo.append(p["coverage_entry_once"])
        ce.append(p["n_entry"])
        te.append(p["time_to_entry_s"])
        cg.append(p["coverage_gate"])
        cs.append(p["coverage_seen"])
    ceo_valid = [x for x in ceo if x is not None]
    plus[rng] = {
        "coverage_entry_once_raw": ceo,
        "coverage_entry_once_median": round(st.median(ceo_valid), 3) if ceo_valid else None,
        "n_entry_raw": ce, "n_admitted": sum(1 for x in ce if x and x >= 1),
        "time_to_entry_s_raw": te,
        "coverage_gate_raw": cg, "coverage_seen_raw": cs,
    }

# werdykt (+): mediana coverage_entry_once ≥0.8 na 7 i 9 m, admisja na wszystkich ważnych bootach
def crit_pass(rng):
    m = plus[rng]["coverage_entry_once_median"]
    adm = plus[rng]["n_admitted"] == len(valid_boots)
    return (m is not None and m >= 0.8 and adm), m, adm

plus_verdict = {}
for rng in CRIT:
    ok, m, adm = crit_pass(rng)
    plus_verdict[rng] = {"pass": ok, "median_cov_entry_once": m, "admitted_all_boots": adm}
plus_overall = all(plus_verdict[r]["pass"] for r in CRIT)

# (−) ε_FP + dekompozycja koniunktów
minus = {}
for b in valid_boots:
    fe = data[b]["phases"]["fp_empty"]
    fb = data[b]["phases"]["fp_bg"]
    minus[b] = {
        "fp_empty_false_entry": fe["false_entry"], "fp_empty_conj": fe.get("false_gate_conj"),
        "fp_bg_false_entry": fb["false_entry"], "fp_bg_false_gate_frames": fb.get("false_gate_frames"),
        "fp_bg_conj": fb.get("false_gate_conj"),
    }
minus_overall = all(m["fp_empty_false_entry"] == 0 and m["fp_bg_false_entry"] == 0 for m in minus.values())

out = {
    "step": "REGATE — bramka ENTRY-once ×3 booty (POMIAR live, world_demo_v1.1)",
    "criterion": "ANEKS_MTI_2 AM2.2: (+) coverage_entry_once≥0.8 mediana/boot na {7,9}m; (−) 0 false ENTRY oba sceny",
    "boots": BOOTS, "valid_boots": valid_boots, "aneks_h": aneks,
    "plus_by_range": plus, "plus_verdict": plus_verdict, "plus_overall_PASS": plus_overall,
    "minus_by_boot": minus, "minus_overall_PASS": minus_overall,
    "verdict": f"(+) {'PASS' if plus_overall else 'FAIL'} · (−) {'PASS' if minus_overall else 'FAIL'}",
    "note_5m": {"info_only": True, "coverage_entry_once_median": plus["5m"]["coverage_entry_once_median"],
                "n_admitted": plus["5m"]["n_admitted"]},
}
outp = os.path.join(REGATE, "B_regate_aggregate.json")
json.dump(out, open(outp, "w"), indent=2, ensure_ascii=False)
print(json.dumps(out, indent=2, ensure_ascii=False))
print(f"\n[aggregate] zapisano {outp}  ·  valid_boots={valid_boots}")
