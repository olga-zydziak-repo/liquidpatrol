#!/usr/bin/env python3
"""results/KOTW_RECON/r2/tools/kotw2_r4_szersze.py — R4′ opisowo poza pasmem promptu: odsetek próbek orbity, w których
dowolna kotwica w stożku centralnym leży ≤ 5° od GT intruza, w pasmach zasięgu kotwicy [5,18] (litera R4′), (18,30], (30,45].
Te same źródła i funkcje co kotw2_obwod.py (import READ-ONLY). Użycie: kotw2_r4_szersze.py <out.json> <kampania=glob> ...
"""
import bisect, glob, json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kotw2_obwod as O

PASMA = ((5.0, 18.0), (18.0, 30.0), (30.0, 45.0))
acc = {}
for arg in sys.argv[2:]:
    kamp, pat = arg.split("=", 1)
    for d in sorted(glob.glob(pat)):
        tr, dm, gi = (os.path.join(d, x) for x in ("trace.jsonl", "demo.jsonl", "gt_intruder.jsonl"))
        if not all(os.path.exists(p) for p in (tr, dm, gi)):
            continue
        gt = sorted([g for g in O.K1.load(tr, "gt") if "qw" in g and "sim" in g], key=lambda g: g["sim"])
        rows = sorted(O.K1.load(dm), key=lambda r: r["t_sim"]); rt = [r["t_sim"] for r in rows]
        it = sorted(O.K1.load(gi), key=lambda r: r["t_sim"]); its = np.array([r["t_sim"] for r in it])
        gs = np.array([g["sim"] for g in gt])
        m = (gs >= rt[0]) & (gs <= rt[-1])
        gt = [g for g, k in zip(gt, m) if k]; gs = gs[m]
        orb = np.array([rows[min(bisect.bisect_left(rt, s), len(rows) - 1)]["phase"] == "orbit" for s in gs])
        j = np.clip(np.searchsorted(its, gs), 0, len(it) - 1); ok = np.abs(its[j] - gs) <= 0.1
        pos = np.array([[g["x"], g["y"], g["z"]] for g in gt]); q = np.array([[g["qw"], g["qx"], g["qy"], g["qz"]] for g in gt])
        R = O.rotmats(q); cam = pos + np.einsum("nij,j->ni", R, np.array(O.K1.CAM))
        ip = np.array([[it[k]["ned"][1], it[k]["ned"][0], -it[k]["ned"][2]] for k in j])
        ib = np.einsum("nji,nj->ni", R, ip - cam); iu = ib / np.linalg.norm(ib, axis=1, keepdims=True)
        sel = orb & ok
        for Ra in O.RA:
            for n in O.NS:
                for ph in O.PHI:
                    p0 = 0.0 if ph == "0" else math.pi / n
                    for h in O.HS:
                        A = np.array([[Ra * math.cos(p0 + 2 * math.pi * k / n), Ra * math.sin(p0 + 2 * math.pi * k / n), h] for k in range(n)])
                        c, r, a, u = O.projekcja(R, cam, A)
                        ang = np.degrees(np.arccos(np.clip(np.einsum("nai,ni->na", u, iu), -1, 1)))
                        cfg = f"R{int(Ra)}_n{n}_{ph}_h{int(h)}"
                        s = acc.setdefault(cfg, {"n_orbit": 0, **{f"{lo:g}-{hi:g}": 0 for lo, hi in PASMA}})
                        s["n_orbit"] += int(sel.sum())
                        for lo, hi in PASMA:
                            hit = (c & (r > lo if lo > 5 else r >= lo) & (r <= hi) & (ang <= O.R4_DEG)).any(axis=1)
                            s[f"{lo:g}-{hi:g}"] += int((hit & sel).sum())
for v in acc.values():
    for k in list(v):
        if k != "n_orbit":
            v["frac_" + k] = round(v[k] / v["n_orbit"], 4)
json.dump(acc, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
for k, v in acc.items():
    print(k, {x: v[x] for x in v if x.startswith("frac")})
