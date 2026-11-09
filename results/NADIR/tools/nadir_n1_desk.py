#!/usr/bin/env python3
"""results/NADIR/tools/nadir_n1_desk.py — ANEKS_NADIR-1 §2.5 desk-bramka pokrycia (0 bootów).

Narzędzie reconu (results/NADIR_RECON/tools/nadir_r1.py — import READ-ONLY: rotmats, fazy_boot, nadir_uv_pts, stałe;
kotw_r1.load) na manifeście v2 (pozycje rzeczywiste) i montażu v2 (kamera w (0, 0, MOUNT_Z) ramy body), pełna postawa z GT,
te same 4 kampanie co recon. Znacznik widoczny w klatce ⇔ środek w stożku centralnym (edge ≥ 0.10) ∧ bok ≥ 18 px
(W = 1 m; obserwacja przyjęta PRE §2.3) ∧ nie w masce kadłuba v2 (b/maska_v2.png; znacznik w masce = niewidoczny) ∧ węzeł
bez kolizji z bryłą wg manifestu v2 (zasłonięty z góry = niewidoczny, konserwatywnie).
Klatki: próbkowanie GT na siatce kadencji r Hz (najbliższa próbka GT ≤ 1/(2r) s), r ∈ {5, 3, 2}. τ = czas od ostatniej
klatki z widocznym znacznikiem. Fazy misji: approach/hold/orbit. Wymóg: ≥ 1 znacznik w ≥ 99.9% klatek misji ∧ τ_max ≤ 2 s.
Użycie: nadir_n1_desk.py <out.json> <kampania=glob> ...
"""
import glob
import json
import math
import os
import sys

import cv2
import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, os.path.join(ROOT, "results/NADIR_RECON/tools"))
import nadir_r1 as R                                        # READ-ONLY
K1 = R.K1
MAN = json.load(open(os.path.join(ROOT, "results/NADIR/s1/n1/manifest_znaczniki_v2.json")))
MASKA_P = os.path.join(ROOT, "results/NADIR/s1/n1/maska_v2.png")
MOUNT_Z = -0.215
RATES = (5, 3, 2)
MISJA = ("approach", "hold", "orbit")
BOK_MIN, EDGE = 18.0, R.EDGE
F, IW, IH = R.F, R.IW, R.IH


def boot(d, kamp, maska, A, ukryte, out):
    tr, dm = os.path.join(d, "trace.jsonl"), os.path.join(d, "demo.jsonl")
    if not (os.path.exists(tr) and os.path.exists(dm)):
        return
    gt = sorted([g for g in K1.load(tr, "gt") if "qw" in g and "sim" in g], key=lambda g: g["sim"])
    rows = K1.load(dm)
    ev = K1.load(tr, "event")
    if not rows or len(gt) < 10:
        return
    gs = np.array([g["sim"] for g in gt])
    pos = np.array([[g["x"], g["y"], g["z"]] for g in gt])
    q = np.array([[g["qw"], g["qx"], g["qy"], g["qz"]] for g in gt])
    Rm = R.rotmats(q)
    fz, sc, epi = R.fazy_boot(gs, pos[:, 2], rows, ev)
    cam = pos + Rm @ np.array([0, 0, MOUNT_Z])
    u, v, depth = R.nadir_uv(Rm, cam, A)
    cx, cy = u / IW, v / IH
    vis = (depth > 0.1) & (np.minimum(np.minimum(cx, 1 - cx), np.minimum(cy, 1 - cy)) >= EDGE)
    vis[:, ukryte] = False
    if maska is not None:
        ui = np.clip(np.round(u), 0, IW - 1).astype(int); vi = np.clip(np.round(v), 0, IH - 1).astype(int)
        vis &= ~maska[vi, ui]
    # bok px: krótszy z rzutów ±0.5 m wzdłuż E i N
    bok = np.full(vis.shape, np.inf)
    for e in (np.array([0.5, 0, 0]), np.array([0, 0.5, 0])):
        ua, va, _ = R.nadir_uv(Rm, cam, A + e); ub, vb, _ = R.nadir_uv(Rm, cam, A - e)
        bok = np.minimum(bok, np.hypot(ua - ub, va - vb))
    vis &= bok >= BOK_MIN
    has = vis.any(axis=1)
    for ep in np.unique(epi[epi >= 0]):
        m = np.flatnonzero((epi == ep) & np.isin(fz, MISJA))
        if len(m) < 10:
            continue
        t = gs[m]
        for r in RATES:
            grid = np.arange(t[0], t[-1], 1.0 / r)
            j = np.clip(np.searchsorted(t, grid), 1, len(t) - 1)
            j = np.where(np.abs(t[j - 1] - grid) < np.abs(t[j] - grid), j - 1, j)
            ok = np.abs(t[j] - grid) <= 0.5 / r
            idx, tg = m[j[ok]], grid[ok]
            h = has[idx]
            last, tmax = None, 0.0
            for tt, hh in zip(tg, h):
                if hh:
                    if last is not None:
                        tmax = max(tmax, tt - last)
                    else:
                        tmax = max(tmax, tt - tg[0])
                    last = tt
            if last is None:
                tmax = tg[-1] - tg[0]
            else:
                tmax = max(tmax, tg[-1] - last)
            o = out.setdefault(f"{r}Hz", {"klatki": 0, "z_znacznikiem": 0, "tau_max": 0.0, "najgorszy": None, "epizody": 0,
                                         "per_faza": {}})
            o["klatki"] += int(len(h)); o["z_znacznikiem"] += int(h.sum()); o["epizody"] += 1
            for f in MISJA:
                mf = fz[idx] == f
                pf = o["per_faza"].setdefault(f, [0, 0])
                pf[0] += int(mf.sum()); pf[1] += int((h & mf).sum())
            if tmax > o["tau_max"]:
                o["tau_max"] = round(float(tmax), 3)
                o["najgorszy"] = {"kampania": kamp, "boot": os.path.basename(d.rstrip("/")), "ep": int(ep), "scenario": sc[m[0]]}


def main():
    outp = sys.argv[1]
    maska = cv2.imread(MASKA_P, 0) > 0 if os.path.exists(MASKA_P) else None
    A = np.array([[z["E"], z["N"], z["z"]] for z in MAN["znaczniki"]])
    ukryte = [i for i, z in enumerate(MAN["znaczniki"]) if z["kolizje_z_brylami"]]
    out = {}
    for arg in sys.argv[2:]:
        kamp, pat = arg.split("=", 1)
        for d in sorted(glob.glob(pat)):
            if os.path.isdir(d):
                boot(d, kamp, maska, A, ukryte, out)
    for r, o in out.items():
        o["frac_ge1"] = round(o["z_znacznikiem"] / o["klatki"], 5)
        o["per_faza"] = {f: round(v[1] / v[0], 5) for f, v in o["per_faza"].items() if v[0]}
        o["PASS"] = o["frac_ge1"] >= 0.999 and o["tau_max"] <= 2.0
    res = {"opis": __doc__.split("\n\n")[0], "montaz_z_m": MOUNT_Z, "maska": os.path.relpath(MASKA_P, ROOT) if maska is not None else None,
           "maska_frac": round(float(maska.mean()), 5) if maska is not None else None,
           "ukryte_id": [MAN["znaczniki"][i]["id"] for i in ukryte], "bok_min_px": BOK_MIN, "wyniki": out}
    json.dump(res, open(outp, "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: {kk: vv for kk, vv in v.items()} for k, v in out.items()}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
