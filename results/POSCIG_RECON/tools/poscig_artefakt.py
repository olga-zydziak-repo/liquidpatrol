#!/usr/bin/env python3
"""results/POSCIG_RECON/tools/poscig_artefakt.py — kwantyfikacja artefaktu teleportu w d_min sędziego.

Mechanizm (dowód w RECON_POSCIG §R2a): gt_intruder.jsonl loguje `cmd_ned` (komenda trajektorii,
poprawna od t0) i `ned` (poza ZASTOSOWANA z pose/info). W pierwszych ~0.1–0.2 s epizodu `ned`
bywa STALE sprzed teleportu bramki startu (klasa znana: harness/intruder_motion.py:27-29,
"max 21 m = tranzient teleportu granicznego"), mimo że bramka startu zweryfikowała intruza
≤TOL_START=0.20 m od pozy startowej PRZED t0 (bench_flight.py:276, intruder_motion.py:30).
Zamrożony sędzia (bench_judge.py:88-96) liczy d_min na tych próbkach i na interpolacji
liniowej przez skok (bench_judge.py:34-47) ⇒ fikcyjne zbliżenie.

Pomiar per epizod: (1) reprodukcja werdyktu sędziego na LOGOWANYM GT w oknie epizodu
(sanity vs akw_summary / raporty ławki); (2) werdykt po odfiltrowaniu próbek artefaktu
(|ned−cmd_ned|_xy > 1.0 m — intruz nie śledzi komendy); (3) statystyki artefaktu.
Zero edycji istniejących plików. Wynik: artefakt_dmin.json.
"""
import json
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from bench.bench_judge import judge_episode
from common.frames import enu2ned

OUTDIR = os.path.join(ROOT, "results", "POSCIG_RECON")
DEV_GATE = 1.0   # [m] próg niezgodności poza-zastosowana vs komenda = marker artefaktu


def iter_jsonl(p):
    with open(p) as f:
        for line in f:
            try:
                yield json.loads(line)
            except Exception:
                continue


def episode_bounds(trace_path, sid):
    t0 = t1 = None
    eid = None
    for r in iter_jsonl(trace_path):
        if r.get("t") != "event":
            continue
        if r.get("ev") == "episode_start" and r.get("scenario_id") == sid:
            t0 = r["t0_sim"]; eid = r.get("episode_id")
        elif r.get("ev") == "episode_end" and t0 is not None and t1 is None and r.get("episode_id") == eid:
            t1 = r["sim"]
    return t0, t1, eid


def analyze(d, sid, label):
    trace = os.path.join(ROOT, d, "trace.jsonl")
    t0, t1, eid = episode_bounds(trace, sid)
    assert t0 is not None and t1 is not None, f"brak granic epizodu {sid} w {d}"
    drone = [(r["sim"], enu2ned([r["x"], r["y"], r["z"]]))
             for r in iter_jsonl(trace) if r.get("t") == "gt" and t0 <= r["sim"] <= t1]
    drone.sort()
    rows = [r for r in iter_jsonl(os.path.join(ROOT, d, "gt_intruder.jsonl"))
            if r.get("ned") and t0 <= r["t_sim"] <= t1 and r.get("scenario_id") == sid]
    full = [(r["t_sim"], r["ned"]) for r in rows]
    bad = [r for r in rows
           if math.hypot(r["ned"][0] - r["cmd_ned"][0], r["ned"][1] - r["cmd_ned"][1]) > DEV_GATE]
    filt = [(r["t_sim"], r["ned"]) for r in rows
            if math.hypot(r["ned"][0] - r["cmd_ned"][0], r["ned"][1] - r["cmd_ned"][1]) <= DEV_GATE]
    v_full = judge_episode(drone, full)
    v_filt = judge_episode(drone, filt)
    res = {
        "label": label, "dir": d, "scenario_id": sid,
        "judge_full": {k: v_full[k] for k in ("success_D6", "fail_reasons", "d_min_m", "t_entry_s",
                                              "frac_band_6_10", "sweep_deg")},
        "judge_filtered": {k: v_filt[k] for k in ("success_D6", "fail_reasons", "d_min_m", "t_entry_s",
                                                  "frac_band_6_10", "sweep_deg")},
        "artefakt": {
            "n_rows_bad": len(bad),
            "t_rel_bad": [round(r["t_sim"] - t0, 3) for r in bad[:6]],
            "max_dev_m": (round(max(math.hypot(r["ned"][0] - r["cmd_ned"][0],
                                               r["ned"][1] - r["cmd_ned"][1]) for r in bad), 2)
                          if bad else 0.0),
        },
        "flip_dmin": (v_full["d_min_m"] is not None and v_filt["d_min_m"] is not None
                      and v_full["d_min_m"] < 4.0 <= v_filt["d_min_m"]),
        "flip_D6": (not v_full["success_D6"]) and v_filt["success_D6"],
    }
    print(f"[ART] {label:24s} {sid}: pełny d_min={v_full['d_min_m']} {v_full['fail_reasons']} | "
          f"filtr d_min={v_filt['d_min_m']} {v_filt['fail_reasons']} | "
          f"bad n={len(bad)} t_rel={res['artefakt']['t_rel_bad']} max_dev={res['artefakt']['max_dev_m']} | "
          f"flip_dmin={res['flip_dmin']} flip_D6={res['flip_D6']}")
    return res


CASES = [
    # §Z V2-11
    ("V2_11", "results/FANTOM/camp/r5_V2", "c05_s02"),
    ("V2_11", "results/FANTOM/camp/r9_V2", "c08_s03"),
    ("V2_11", "results/FANTOM/camp/r12_V2", "c08_s04"),
    ("V2_11", "results/FANTOM/camp/r6_V2", "c09_s02"),
    ("V2_11", "results/FANTOM/camp/r6_V2", "c10_s02"),
    ("V2_11", "results/FANTOM/camp/r9_V2", "c10_s03"),
    ("V2_11", "results/FANTOM/camp/r6_V2", "c11_s02"),
    ("V2_11", "results/FANTOM/camp/r9_V2", "c11_s03"),
    ("V2_11", "results/FANTOM/camp/r12_V2", "c11_s04"),
    ("V2_11", "results/AKW/camp/r9_V2", "c09_s03"),
    ("V2_11", "results/AKW/camp/r3_V2", "c10_s01"),
    # B-2 (FANTOM) + analogiczne B-FAILe AKW
    ("B_2", "results/FANTOM/camp/r9_B", "c09_s03"),
    ("B_2", "results/FANTOM/camp/r6_B", "c11_s02"),
    ("B_AKW", "results/AKW/camp/r6_B", "c09_s02"),
    ("B_AKW", "results/AKW/camp/r6_B", "c11_s02"),
    # kontrola 5 (PASS — artefakt nie powinien flipować niczego w drugą stronę)
    ("CTRL_5", "results/FANTOM/camp/r6_V2", "c08_s02"),
    ("CTRL_5", "results/FANTOM/camp/r9_V2", "c09_s03"),
    ("CTRL_5", "results/FANTOM/camp/r12_V2", "c09_s04"),
    ("CTRL_5", "results/FANTOM/camp/r3_V2", "c10_s01"),
    ("CTRL_5", "results/FANTOM/camp/r12_V2", "c10_s04"),
    # NAUCZYCIEL — wszystkie 6 porażek D6 ławki (klasa "proximity wejścia", RAPORT_KAMPANIA_BLOK1)
    ("TEACHER", "results/BENCH/campaign/boot2", "c05_s01"),
    ("TEACHER", "results/BENCH/campaign/b2b9", "c05_s08"),
    ("TEACHER", "results/BENCH/campaign/boot5", "c07_s02"),
    ("TEACHER", "results/BENCH/campaign/boot6", "c09_s02"),
    ("TEACHER", "results/BENCH/campaign/boot11", "c09_s03"),
    ("TEACHER", "results/BENCH/campaign/b2b17", "c09_s06"),
]


def main():
    out = {"dev_gate_m": DEV_GATE, "cases": []}
    for label, d, sid in CASES:
        try:
            out["cases"].append(analyze(d, sid, label))
        except AssertionError as e:
            print(f"[ART] {label} {d} {sid}: POMINIĘTY ({e})")
            out["cases"].append({"label": label, "dir": d, "scenario_id": sid, "error": str(e)})
    json.dump(out, open(os.path.join(OUTDIR, "artefakt_dmin.json"), "w"), indent=1)
    print("zapisano artefakt_dmin.json")


if __name__ == "__main__":
    main()
