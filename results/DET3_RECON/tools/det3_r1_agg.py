#!/usr/bin/env python3
"""results/DET3_RECON/tools/det3_r1_agg.py — agregacja R1 per przedział Z (z r1/*.frames.jsonl).

Zbiory: NEW = korpus DET S1 (D01..D12, 6 154 pozytywy — liczba z PROMPT_DET3_S0), ALL = + stary
korpus 2A (A1*, A2*); osobno split PRE_DET §3 (TEST c06+c09, VAL c02+c04 — VAL dotknięty
early-stoppingiem, TRAIN = in-sample) i faza approach.
Wyjście: r1/r1_tabela.json + wydruk.
"""
import glob
import json
import os

ROOT = "/home/olga/projects/liquidpatrol"
R1 = os.path.join(ROOT, "results/DET3_RECON/r1")
BINS = [(0, 6), (6, 8), (8, 10), (10, 12), (12, 14), (14, 15), (12, 15)]
SPLIT = {"c06": "test", "c09": "test", "c02": "val", "c04": "val"}


def pct(xs, q):
    xs = sorted(xs)
    return round(xs[min(len(xs) - 1, int(len(xs) * q))], 3) if xs else None


def frac(rs, k):
    v = [r for r in rs if k in r]
    return (round(sum(1 for r in v if r[k]) / len(v), 3), len(v)) if v else (None, 0)


def table(rs):
    out = {}
    for lo, hi in BINS:
        b = [r for r in rs if lo <= r["Z"] < hi]
        if not b:
            out[f"{lo}-{hi}"] = {"n": 0}
            continue
        rep = [r for r in b if r.get("replayed")]
        errs = [r["err"] for r in b if "err" in r]
        confs = [r["conf"] for r in rep if r.get("conf") is not None]
        mti = [r for r in b if not r.get("mti_warm", True)]
        areas = [r["blob_area_diag"] for r in mti]
        out[f"{lo}-{hi}"] = {
            "n": len(b), "n_boots": len({r["boot"] for r in b}),
            "yolo_on": frac(rep, "yolo_on"),
            "conf_p50": pct(confs, 0.5),
            "err_n": len(errs), "err_p50": pct(errs, 0.5), "err_p95": pct(errs, 0.95),
            "fresh": frac(rep, "fresh"),
            "mti_raw_on": frac(mti, "mti_raw_on"),
            "mti_cons_on": frac(mti, "mti_cons_on"),
            "mti_ok_flight": frac(rep, "mti_ok_flight"),
            "blob_area_p50": pct(areas, 0.5), "blob_area_p10": pct(areas, 0.10),
            "blob_lt8": round(sum(1 for a in areas if a < 8) / len(areas), 3) if areas else None,
            "lab_w_p50": pct([r["lab_w"] for r in b], 0.5), "lab_h_p50": pct([r["lab_h"] for r in b], 0.5),
        }
    return out


def main():
    rows = []
    for p in sorted(glob.glob(os.path.join(R1, "*.frames.jsonl"))):
        rows += [json.loads(ln) for ln in open(p)]
    for r in rows:
        r["split"] = "old2A" if r["boot"].startswith("A") else SPLIT.get(r["boot"].split("_")[1], "train")
    new = [r for r in rows if r["boot"].startswith("D")]
    sets = {"NEW": new, "ALL": rows,
            "NEW_test": [r for r in new if r["split"] == "test"],
            "NEW_val": [r for r in new if r["split"] == "val"],
            "NEW_train": [r for r in new if r["split"] == "train"],
            "NEW_approach": [r for r in new if r["phase"] == "approach"],
            "ALL_approach": [r for r in rows if r["phase"] == "approach"]}
    res = {k: {"n": len(v), "bins": table(v)} for k, v in sets.items()}
    far = sorted([r for r in rows if r["Z"] >= 12], key=lambda r: -r["Z"])
    res["far_ge12_frames"] = [{k: r.get(k) for k in ("boot", "t", "Z", "phase", "split", "yolo_on", "conf",
                                                    "err", "mti_raw_on", "mti_cons_on", "blob_area_diag")}
                              for r in far]
    res["phase_counts_NEW"] = {}
    for r in new:
        res["phase_counts_NEW"][str(r["phase"])] = res["phase_counts_NEW"].get(str(r["phase"]), 0) + 1
    json.dump(res, open(os.path.join(R1, "r1_tabela.json"), "w"), indent=1)
    for k in sets:
        print(f"== {k} n={res[k]['n']}")
        for b, t in res[k]["bins"].items():
            if t["n"]:
                print(f"  {b:6s} n={t['n']:4d} boots={t['n_boots']:2d} yolo={t['yolo_on']} conf50={t['conf_p50']} "
                      f"err50/95={t['err_p50']}/{t['err_p95']} (n{t['err_n']}) fresh={t['fresh'][0]} "
                      f"mti_raw={t['mti_raw_on'][0]} mti_cons={t['mti_cons_on'][0]} mti_ok_fl={t['mti_ok_flight'][0]} "
                      f"blob50/10={t['blob_area_p50']}/{t['blob_area_p10']} <8:{t['blob_lt8']} lab={t['lab_w_p50']}x{t['lab_h_p50']}")
    print("phase NEW", res["phase_counts_NEW"])


if __name__ == "__main__":
    main()
