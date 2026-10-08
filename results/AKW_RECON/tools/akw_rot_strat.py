#!/usr/bin/env python3
"""results/AKW_RECON/tools/akw_rot_strat.py — R3 PROMPT_AKW_S0: brama pod rotacją,
stratyfikacja po |yaw_rate| (ZERO lotów, zero edycji frozen).

Dwa źródła danych (oba istniejące):
  (a) REPLAY dolotu S1 (FEED=B, 15 Hz, D01–D12): frozen det_replay.py (de0feb37)
      uruchamiany subprocesem z --detector net/frozen/det_v2.pt; wynik .replay.jsonl
      per klatka (pola: t_frame, own_q, box, conf, mti_ok, fresh, gate, ev).
  (b) ŻYWE percep_feed.jsonl z 12 bootów V2 kampanii C (det_v2 w locie, pętla
      zamknięta) — te same pola, zero inferencji.

Stratyfikacja: yaw z own_q (wxyz, NED/FRD: psi=atan2(2(wz+xy),1-2(y^2+z^2))),
yaw_rate centralną różnicą na unwrapped psi (pary dt<=0.3 s — odcina granice
epizodów/teleporty), biny |yaw_rate|: 0-10 / 10-25 / 25+ °/s.
Etykieta celu per klatka: BootGeo z det_labels 8f7430cd (READ-ONLY import,
kryterium on-target IDENTYCZNE jak det_replay.py:147-151).

Użycie:
  akw_rot_strat.py replay            # 12 replayów dolotu -> replays/
  akw_rot_strat.py strat --out akw_R3_strat.json
"""
from __future__ import annotations

import argparse
import bisect
import glob
import json
import math
import os
import subprocess
import sys

ROOT = "/home/olga/projects/liquidpatrol"
HERE = os.path.dirname(os.path.abspath(__file__))
OUTD = os.path.dirname(HERE)                      # results/AKW_RECON
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "results/DET_RECON/tools"))

from det_labels import BootGeo                    # frozen 8f7430cd (READ-ONLY)
from r02.mti import IMG_W, IMG_H                  # frozen (stałe kadru)

DET_REPLAY = os.path.join(ROOT, "results/DET/tools/det_replay.py")   # frozen de0feb37
DET_V2 = os.path.join(ROOT, "net/frozen/det_v2.pt")                  # frozen 775ead15
COLLECT = os.path.join(ROOT, "results/DET/collect")
CAMP = os.path.join(ROOT, "results/DET/camp")
BINS = [(0.0, 10.0), (10.0, 25.0), (25.0, 1e9)]
BIN_LAB = ["0-10", "10-25", "25+"]
DT_MAX = 0.3          # [s] maks. odstęp pary do różnicy centralnej (odcina teleporty)


def load_jsonl(path):
    out = []
    with open(path) as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                try:
                    out.append(json.loads(ln))
                except json.JSONDecodeError:
                    pass
    return out


def yaw_of(q):
    w, x, y, z = q
    return math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))


def yaw_rates(rows):
    """rate [deg/s] per wiersz (None gdy brak sąsiada w dt<=DT_MAX po obu stronach)."""
    ts = [r["t_frame"] for r in rows]
    ps = [yaw_of(r["own_q"]) for r in rows]
    # unwrap
    un = [ps[0]]
    for p in ps[1:]:
        d = p - un[-1]
        while d > math.pi:
            d -= 2 * math.pi
        while d < -math.pi:
            d += 2 * math.pi
        un.append(un[-1] + d)
    rates = []
    for i in range(len(rows)):
        lo = i - 1 if i - 1 >= 0 and ts[i] - ts[i - 1] <= DT_MAX else i
        hi = i + 1 if i + 1 < len(rows) and ts[i + 1] - ts[i] <= DT_MAX else i
        if hi == lo:
            rates.append(None)
            continue
        rates.append(math.degrees((un[hi] - un[lo]) / (ts[hi] - ts[lo])))
    return rates


def on_target(row, lab):
    b = row.get("box")
    if not b:
        return False
    bx, by = b[0] * IMG_W, b[1] * IMG_H
    lb = lab["box"]
    return abs(bx - lb[0]) <= lb[2] / 2 and abs(by - lb[1]) <= lb[3] / 2


def stratify(name, rows, bootdir):
    rows = [r for r in rows if r.get("t_frame") is not None and r.get("own_q")]
    rows.sort(key=lambda r: r["t_frame"])
    rates = yaw_rates(rows)
    geo = BootGeo(bootdir, 1.0, 60.0)
    bins = [{"n": 0, "n_fov": 0, "on": 0, "box_fov": 0, "box_any": 0, "box_nofov": 0,
             "fp_fov": 0, "fresh": 0, "g_mti": 0, "g_window": 0, "entry": 0,
             "feed_expire": 0, "rates": []} for _ in BINS]
    n_norate = 0
    for r, rt in zip(rows, rates):
        if rt is None:
            n_norate += 1
            continue
        a = abs(rt)
        k = next(i for i, (lo, hi) in enumerate(BINS) if lo <= a < hi)
        B = bins[k]
        B["n"] += 1
        B["rates"].append(a)
        lab = geo.label(r["t_frame"])
        fov = lab.get("flag") == "OK"
        box = bool(r.get("box"))
        if fov:
            B["n_fov"] += 1
            if box:
                B["box_fov"] += 1
                if on_target(r, lab):
                    B["on"] += 1
                else:
                    B["fp_fov"] += 1
        elif box:
            B["box_nofov"] += 1
        if box:
            B["box_any"] += 1
        if r.get("fresh"):
            B["fresh"] += 1
            g = str(r.get("gate"))
            if g == "mti":
                B["g_mti"] += 1
            elif g == "window":
                B["g_window"] += 1
        ev = r.get("ev")
        if ev == "ENTRY":
            B["entry"] += 1
        elif ev == "FEED_EXPIRE":
            B["feed_expire"] += 1
    out = {"source": name, "bootdir": os.path.relpath(bootdir, ROOT),
           "n_rows": len(rows), "n_norate": n_norate, "bins": {}}
    for lab_, B in zip(BIN_LAB, bins):
        rs = sorted(B.pop("rates"))
        B["rate_med"] = round(rs[len(rs) // 2], 1) if rs else None
        B["on_pct"] = round(100 * B["on"] / B["n_fov"], 1) if B["n_fov"] else None
        B["fresh_pct"] = round(100 * B["fresh"] / B["n"], 1) if B["n"] else None
        out["bins"][lab_] = B
    return out


def cmd_replay():
    os.makedirs(os.path.join(OUTD, "replays"), exist_ok=True)
    boots = sorted(glob.glob(os.path.join(COLLECT, "D??_*")))
    boots = [b for b in boots if os.path.isdir(b)]
    for b in boots:
        bid = os.path.basename(b)
        out = os.path.join(OUTD, "replays", bid + ".json")
        if os.path.exists(out):
            print(f"[skip] {bid} (jest)")
            continue
        print(f"[replay] {bid} ...", flush=True)
        subprocess.run([sys.executable, DET_REPLAY, b, "--detector", DET_V2,
                        "--out", out], check=True,
                       stdout=open(out + ".log", "w"), stderr=subprocess.STDOUT)
    print("replay DONE")


def cmd_strat(outname):
    res = {"replay_dolot_B": [], "live_camp_V2": []}
    for j in sorted(glob.glob(os.path.join(OUTD, "replays", "D??_*.json"))):
        bid = os.path.basename(j)[:-5]
        rows = load_jsonl(j + ".replay.jsonl")
        res["replay_dolot_B"].append(stratify("replay:" + bid, rows,
                                              os.path.join(COLLECT, bid)))
    for d in sorted(glob.glob(os.path.join(CAMP, "r*_V2"))):
        pf = os.path.join(d, "percep_feed.jsonl")
        if not os.path.exists(pf):
            continue
        rows = load_jsonl(pf)
        res["live_camp_V2"].append(stratify("live:" + os.path.basename(d), rows, d))

    def agg(lst):
        keys = ["n", "n_fov", "on", "box_fov", "box_any", "box_nofov", "fp_fov",
                "fresh", "g_mti", "g_window", "entry", "feed_expire"]
        A = {lab_: {k: 0 for k in keys} for lab_ in BIN_LAB}
        for it in lst:
            for lab_ in BIN_LAB:
                for k in keys:
                    A[lab_][k] += it["bins"][lab_][k]
        for lab_ in BIN_LAB:
            B = A[lab_]
            B["on_pct"] = round(100 * B["on"] / B["n_fov"], 1) if B["n_fov"] else None
            B["fresh_pct"] = round(100 * B["fresh"] / B["n"], 1) if B["n"] else None
            B["fp_fov_pct"] = round(100 * B["fp_fov"] / B["n_fov"], 1) if B["n_fov"] else None
        return A
    res["AGG_replay_dolot_B"] = agg(res["replay_dolot_B"])
    res["AGG_live_camp_V2"] = agg(res["live_camp_V2"])
    with open(os.path.join(OUTD, outname), "w") as f:
        json.dump(res, f, indent=1)
    for src in ("AGG_replay_dolot_B", "AGG_live_camp_V2"):
        print(f"\n== {src} ==")
        print("bin | n | n_fov | on-target% | fp_fov | box_nofov | fresh% | g_mti | g_win | ENTRY | EXPIRE")
        for lab_ in BIN_LAB:
            B = res[src][lab_]
            print(f"{lab_:>5} | {B['n']:5} | {B['n_fov']:5} | {str(B['on_pct']):>6} | "
                  f"{B['fp_fov']:4} | {B['box_nofov']:4} | {str(B['fresh_pct']):>5} | "
                  f"{B['g_mti']:5} | {B['g_window']:4} | {B['entry']:3} | {B['feed_expire']:3}")
    print("\nOK ->", outname)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["replay", "strat"])
    ap.add_argument("--out", default="akw_R3_strat.json")
    a = ap.parse_args()
    if a.mode == "replay":
        cmd_replay()
    else:
        cmd_strat(a.out)
