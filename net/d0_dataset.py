#!/usr/bin/env python3
"""net/d0_dataset.py — D0 (PROMPT_NET_S1 I0.5): inwentarz zbioru demonstracji ławki.

Zbiór = WYŁĄCZNIE udane epizody D6 (PRE_NET N2), pierwsza WAŻNA (V2′) próba per scenariusz.
Wiersze demo z tych epizodów, z wykluczeniem ticków stall=1 i fazy reset. Podział N2:
TEST = seed%4==0 (ziarna 4,8), VAL = seed 2, TRAIN = reszta. Determinizm z manifestów + demo.jsonl.

Zero SITL, zero zmian frozen. Odczyt results/BENCH/** tylko.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# kolejność LOTÓW (chronologiczna) — dla „pierwszej ważnej próby"
BLOCK1 = ["boot1", "boot2", "boot3", "boot4", "boot5", "boot6", "boot7", "boot8",
          "boot9r", "boot10r", "boot11", "boot12", "boot13"]
BLOCK2 = ["b2b1", "b2b2", "b2b3", "b2b4", "b2b5", "b2b6r2", "b2b7", "b2b8", "b2b9",
          "b2b10", "b2b11", "b2b12", "b2b13", "b2b14", "b2b15", "b2b16", "b2b17", "b2b18"]
CAMP = os.path.join(ROOT, "results", "BENCH", "campaign")


def split_of(seed):
    if seed % 4 == 0:
        return "TEST"
    if seed == 2:
        return "VAL"
    return "TRAIN"


def resolve_first_valid():
    """Zwraca {scenario_id: {boot, attempt, seed, cell, success_D6}} — pierwsza ważna (V2′) próba w kolejności lotów."""
    first = {}
    for boot in BLOCK1 + BLOCK2:
        mpath = os.path.join(CAMP, boot, "manifest.json")
        if not os.path.exists(mpath):
            continue
        m = json.load(open(mpath))
        for ep in m.get("episodes", []):
            sid = ep.get("scenario_id")
            if ep.get("valid_V2p") and sid not in first:
                seed = int(sid.split("_s")[1])
                cell = sid.split("_s")[0]
                first[sid] = {"boot": boot, "attempt": ep.get("attempt"), "seed": seed,
                              "cell": cell, "success_D6": bool(ep.get("success_D6"))}
    return first


def demo_rows_for(boot, sid, attempt):
    """Wiersze demo epizodu (sid,attempt) z danego bootu: (n_total, n_stall, n_reset, n_kept)."""
    path = os.path.join(CAMP, boot, "demo.jsonl")
    n_total = n_stall = n_reset = n_kept = 0
    if not os.path.exists(path):
        return (0, 0, 0, 0)
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        if r.get("scenario_id") != sid or r.get("attempt") != attempt:
            continue
        n_total += 1
        is_stall = int(r.get("stall", 0)) == 1
        is_reset = r.get("phase") == "reset"
        if is_stall:
            n_stall += 1
        if is_reset:
            n_reset += 1
        if not is_stall and not is_reset:
            n_kept += 1
    return (n_total, n_stall, n_reset, n_kept)


def build():
    first = resolve_first_valid()
    succ = {sid: v for sid, v in first.items() if v["success_D6"]}
    rows = []
    for sid in sorted(succ):
        v = succ[sid]
        n_total, n_stall, n_reset, n_kept = demo_rows_for(v["boot"], sid, v["attempt"])
        rows.append({"scenario_id": sid, "cell": v["cell"], "seed": v["seed"],
                     "split": split_of(v["seed"]), "boot": v["boot"], "attempt": v["attempt"],
                     "n_total": n_total, "n_stall": n_stall, "n_reset": n_reset, "n_kept": n_kept})
    return first, succ, rows


if __name__ == "__main__":
    first, succ, rows = build()
    print(f"scenariusze rozwiązane (pierwsza ważna V2'): {len(first)}")
    print(f"udane D6 (zbiór demonstracji): {len(succ)}")
    tot = {"n_total": 0, "n_stall": 0, "n_reset": 0, "n_kept": 0}
    per_split = {"TRAIN": {"eps": 0, "kept": 0}, "VAL": {"eps": 0, "kept": 0}, "TEST": {"eps": 0, "kept": 0}}
    for r in rows:
        for k in tot:
            tot[k] += r[k]
        per_split[r["split"]]["eps"] += 1
        per_split[r["split"]]["kept"] += r["n_kept"]
    print(f"wiersze total={tot['n_total']} stall={tot['n_stall']} reset={tot['n_reset']} kept={tot['n_kept']}")
    for s in ("TRAIN", "VAL", "TEST"):
        print(f"  {s}: epizody={per_split[s]['eps']} kept_rows={per_split[s]['kept']}")
    json.dump({"n_resolved": len(first), "n_success": len(succ), "totals": tot,
               "per_split": per_split, "rows": rows},
              open(os.path.join(ROOT, "results", "NET", "d0_dataset.json"), "w"), indent=2)
