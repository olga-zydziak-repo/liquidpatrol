#!/usr/bin/env python3
"""results/POSCIG_RECON/tools/erratum_sweep.py — sweep świadka artefaktu teleportu
(ERRATUM-DMIN, ANEKS_POSCIG-1 §5 pkt 2) po WSZYSTKICH zbiorach sędziowanych na gt_intruder:

  DET_S4  — results/DET/camp/r{1..12}_{B,V2}        (werdykty kanoniczne: detS4_summary.json)
  LIQ     — results/LIQ/camp/r{1..12}_{ncp,gru}     (booty W1′)
  K2C     — results/K2/k2c_b{1..12}                 (kanon K2 = REFUSE/touchdown, NIE D6 —
  K4B     — results/K2/k4b_b{1..3}                   D6 liczony informacyjnie; patrz nota w JSON)
  BENCH   — results/BENCH/campaign/boot*,b2b*       (ławka blok1+2, nauczyciel)
  AKW_S3 / FANTOM_S2 — re-sweep z index_episodes.json w OBU kierunKACH (uzupełnienie
                       sweep_artefakt.json, który liczył tylko FAIL→PASS)

Marker-świadek: |ned − cmd_ned|_xy > 1.0 m (intruz nie śledzi komendy = poza sprzed teleportu).
Werdykt pełny vs odfiltrowany liczony ZAMROŻONYM sędzią (bench.bench_judge, import bez zmian).
Flipy OBU kierunków: flip_f2p (FAIL→PASS, twarz 1: fałszywe d_min) i flip_p2f (PASS→FAIL,
twarz 2: fałszywe t_entry → okno frac/sweep otwarte za wcześnie, wzór c07_s01 AKW V2).
Krzyżowa reprodukcja: dla DET_S4 porównanie judge_full vs zapisane success_D6/d_min_m.
Zero edycji istniejących plików. Wynik: erratum_sweep.json."""
import glob
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
DEV_GATE = 1.0   # [m] marker-świadek, identyczny z poscig_artefakt.DEV_GATE


def iter_jsonl(p):
    with open(p) as f:
        for line in f:
            try:
                yield json.loads(line)
            except Exception:
                continue


def load_boot(d):
    """Jedno czytanie trace: granice wszystkich epizodów + GT drona; jedno czytanie gt_intruder."""
    trace = os.path.join(ROOT, d, "trace.jsonl")
    eps = {}      # episode_id -> {sid, t0, t1}
    drone = []    # [(t_sim, ned)]
    for r in iter_jsonl(trace):
        t = r.get("t")
        if t == "event":
            if r.get("ev") == "episode_start" and r.get("scenario_id"):
                eps[r.get("episode_id")] = {"sid": r["scenario_id"], "t0": r["t0_sim"], "t1": None}
            elif r.get("ev") == "episode_end" and r.get("episode_id") in eps:
                e = eps[r["episode_id"]]
                if e["t1"] is None:
                    e["t1"] = r["sim"]
        elif t == "gt":
            drone.append((r["sim"], enu2ned([r["x"], r["y"], r["z"]])))
    drone.sort()
    intr = [r for r in iter_jsonl(os.path.join(ROOT, d, "gt_intruder.jsonl")) if r.get("ned")]
    return eps, drone, intr


def judge_pair(drone, intr, sid, t0, t1):
    rows = [r for r in intr if r.get("scenario_id") == sid and t0 <= r["t_sim"] <= t1]
    dr = [(s, n) for s, n in drone if t0 <= s <= t1]
    full = [(r["t_sim"], r["ned"]) for r in rows]
    bad = [r for r in rows
           if math.hypot(r["ned"][0] - r["cmd_ned"][0], r["ned"][1] - r["cmd_ned"][1]) > DEV_GATE]
    filt = [(r["t_sim"], r["ned"]) for r in rows
            if math.hypot(r["ned"][0] - r["cmd_ned"][0], r["ned"][1] - r["cmd_ned"][1]) <= DEV_GATE]
    if not dr or not full:
        return None
    v_full = judge_episode(dr, full)
    v_filt = judge_episode(dr, filt) if filt else v_full
    keys = ("success_D6", "fail_reasons", "d_min_m", "t_entry_s", "frac_band_6_10", "sweep_deg")
    return {
        "judge_full": {k: v_full[k] for k in keys},
        "judge_filtered": {k: v_filt[k] for k in keys},
        "artefakt": {
            "n_rows_bad": len(bad),
            "t_rel_bad": [round(r["t_sim"] - t0, 3) for r in bad[:6]],
            "max_dev_m": (round(max(math.hypot(r["ned"][0] - r["cmd_ned"][0],
                                               r["ned"][1] - r["cmd_ned"][1]) for r in bad), 2)
                          if bad else 0.0),
        },
        "flip_f2p": (not v_full["success_D6"]) and v_filt["success_D6"],
        "flip_p2f": v_full["success_D6"] and (not v_filt["success_D6"]),
    }


def sweep_dir(set_name, d, canon=None):
    out = []
    if not (os.path.exists(os.path.join(ROOT, d, "trace.jsonl"))
            and os.path.exists(os.path.join(ROOT, d, "gt_intruder.jsonl"))):
        print(f"[POMINIĘTY] {set_name} {d}: brak trace/gt_intruder (boot padły/diagnostyczny)")
        return out
    eps, drone, intr = load_boot(d)
    for eid in sorted(eps):
        e = eps[eid]
        if e["t1"] is None:
            continue
        r = judge_pair(drone, intr, e["sid"], e["t0"], e["t1"])
        if r is None:
            continue
        r.update({"label": f"{set_name}:{os.path.basename(d)}:{e['sid']}",
                  "dir": d, "scenario_id": e["sid"], "episode_id": eid})
        if canon and e["sid"] in canon:
            c = canon[e["sid"]]
            r["canon"] = c
            r["repro_ok"] = (c.get("success_D6") == r["judge_full"]["success_D6"]
                             and (c.get("d_min_m") is None or r["judge_full"]["d_min_m"] is None
                                  or abs(c["d_min_m"] - r["judge_full"]["d_min_m"]) <= 0.01))
        out.append(r)
    return out


def det_canon(d):
    p = os.path.join(ROOT, d, "detS4_summary.json")
    if not os.path.exists(p):
        return None
    s = json.load(open(p))
    return {e["scenario_id"]: {"success_D6": e["success_D6"], "d_min_m": e["d_min_m"],
                               "valid_final": e["valid_final"]} for e in s.get("episodes", [])}


def main():
    cases = []

    # DET S4 — oba ramiona, kanon z detS4_summary.json
    for n in range(1, 13):
        for arm in ("B", "V2"):
            d = f"results/DET/camp/r{n}_{arm}"
            if os.path.isdir(os.path.join(ROOT, d)):
                cases += sweep_dir(f"DET_S4:{arm}", d, det_canon(d))

    # LIQ (booty W1′) — oba ramiona
    for n in range(1, 13):
        for arm in ("ncp", "gru"):
            d = f"results/LIQ/camp/r{n}_{arm}"
            if os.path.isdir(os.path.join(ROOT, d)):
                cases += sweep_dir(f"LIQ:{arm}", d)

    # K2 (k2c) + K4b — kanon NIE-D6; D6 informacyjnie
    for n in range(1, 13):
        d = f"results/K2/k2c_b{n}"
        if os.path.isdir(os.path.join(ROOT, d)):
            cases += sweep_dir("K2C:k2c", d)
    for n in range(1, 4):
        d = f"results/K2/k4b_b{n}"
        if os.path.isdir(os.path.join(ROOT, d)):
            cases += sweep_dir("K4B:k4b", d)

    # Ławka blok1+2 (nauczyciel) — wszystkie booty łącznie z retry i boot0_diag
    for d in sorted(glob.glob(os.path.join(ROOT, "results/BENCH/campaign/boot*"))) + \
             sorted(glob.glob(os.path.join(ROOT, "results/BENCH/campaign/b2b*"))):
        if os.path.isdir(d):
            rel = os.path.relpath(d, ROOT)
            blk = "b2" if os.path.basename(d).startswith("b2b") else "b1"
            cases += sweep_dir(f"BENCH:{blk}", rel)

    # AKW S3 / FANTOM S2 — re-sweep w OBU kierunkach z index_episodes.json
    idx = json.load(open(os.path.join(OUTDIR, "index_episodes.json")))
    by_dir = {}
    for key, rec in sorted(idx.items()):
        by_dir.setdefault(rec["dir"], []).append((key, rec))
    for d, entries in sorted(by_dir.items()):
        eps, drone, intr = load_boot(d)
        bysid = {e["sid"]: e for e in eps.values() if e["t1"] is not None}
        for key, rec in entries:
            e = bysid.get(rec["scenario_id"])
            if e is None:
                continue
            r = judge_pair(drone, intr, e["sid"], e["t0"], e["t1"])
            if r is None:
                continue
            camp, arm, _ = key.split(":")
            r.update({"label": key, "dir": d, "scenario_id": e["sid"],
                      "valid_final": rec.get("valid_final")})
            cases.append(r)

    # agregaty per zbiór:ramię
    agg = {}
    for r in cases:
        set_arm = ":".join(r["label"].split(":")[:2])
        a = agg.setdefault(set_arm, {"n": 0, "n_bad_rows": 0, "flip_f2p": 0, "flip_p2f": 0,
                                     "repro_n": 0, "repro_ok": 0})
        a["n"] += 1
        a["n_bad_rows"] += (1 if r["artefakt"]["n_rows_bad"] > 0 else 0)
        a["flip_f2p"] += (1 if r["flip_f2p"] else 0)
        a["flip_p2f"] += (1 if r["flip_p2f"] else 0)
        if "repro_ok" in r:
            a["repro_n"] += 1
            a["repro_ok"] += (1 if r["repro_ok"] else 0)
    print(json.dumps(agg, indent=1))
    for r in cases:
        if r["flip_f2p"] or r["flip_p2f"]:
            kind = "FAIL->PASS" if r["flip_f2p"] else "PASS->FAIL"
            print(f"FLIP {kind}: {r['label']} d_min {r['judge_full']['d_min_m']} -> "
                  f"{r['judge_filtered']['d_min_m']} | t_entry {r['judge_full']['t_entry_s']} -> "
                  f"{r['judge_filtered']['t_entry_s']} | sweep {r['judge_full']['sweep_deg']} -> "
                  f"{r['judge_filtered']['sweep_deg']} | powody pełne {r['judge_full']['fail_reasons']} "
                  f"filtr {r['judge_filtered']['fail_reasons']}")
        if r.get("repro_ok") is False:
            print(f"REPRO-MISMATCH: {r['label']} canon={r['canon']} full={r['judge_full']}")
    nota = ("K2C/K4B: kanoniczny werdykt K2 = REFUSE/touchdown/breach (k2_campaign.json), "
            "NIE D6 — kolumny judge_* mają tam charakter informacyjny; werdykto-nośne jest "
            "wyłącznie d_min/artefakt (fałszywa bliskość nie wytworzyła breach).")
    json.dump({"dev_gate_m": DEV_GATE, "nota_k2": nota, "agg": agg, "cases": cases},
              open(os.path.join(OUTDIR, "erratum_sweep.json"), "w"), indent=1)
    print(f"zapisano erratum_sweep.json ({len(cases)} epizodów)")


if __name__ == "__main__":
    main()
