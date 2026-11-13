#!/usr/bin/env python3
"""results/NAD3_RECON/tools/nad3_r2.py — PROMPT_NAD3_S0 R2: promień zadania faktyczny (0 bootów).

Per lot (12 cięć bramki S3 + lot długi) i per faza: r_GT = |GT_xy − gt_home| (kanon B2 analizatora) w tickach epizodu cięcia,
fazy: approach / hold / orbit (misja, przed zejściem planowym), z podziałem przed flagą utraty GNSS / po fladze, oraz zejście
(desc albo po komendzie zejścia). Dodatkowo r_est osłony (nad2.r_est) w utracie i m = R_E − d_stop − r_max z tabeli
results/KONT_RECON/r4_margin.json (r_max tej komórki ze starszych kampanii, faza orbity). Lot długi dodatkowo per 100 s.
Rozkład intruza: |trk GT| z gt_intruder.jsonl (max, p50) — wejście do dróg R2.
Wyjście: results/NAD3_RECON/r2_promien.json.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nad3_dane as N

MARG = json.load(open(os.path.join(N.ROOT, "results/KONT_RECON/r4_margin.json")))["tabela_scenariuszy"]
R_E, D_STOP = 32.0, 2.85


def intruz(L):
    """|intruz| w ramie lokalnej NED (gt_intruder.jsonl: pole ned) w epizodzie cięcia."""
    xs = [float(np.hypot(r["ned"][0], r["ned"][1])) for r in N.jl(L.d, "gt_intruder.jsonl")
          if r.get("episode_id") == L.ep_cut and r.get("ned") is not None]
    return N.rozklad(xs) if xs else None


def main():
    out = {}
    for n, d, k in N.loty():
        L = N.wczytaj(n, d, k)
        rr = [r for r in L.rama if r["ep"] == L.ep_cut]
        sim = np.array([r["sim"] for r in rr])
        rg = L.r_gt(sim)
        po = sim >= L.t_flag
        ms = np.array([L.misja(r) for r in rr])
        ph = np.array([r.get("phase") or "-" for r in rr])
        o = {"komorka": k, "r4_margin": MARG.get(k), "fazy": {}}
        for f in ("approach", "hold", "orbit"):
            for lab, sel in (("przed_flaga", ~po), ("po_fladze", po)):
                s = ms & (ph == f) & sel
                if s.any():
                    o["fazy"][f"{f}/{lab}"] = {"n": int(s.sum()), "r_max": round(float(rg[s].max()), 3),
                                               "r_p50": round(float(np.median(rg[s])), 3)}
        zj = ~ms & (sim >= (L.t_zp or 1e18))
        if zj.any():
            o["fazy"]["zejscie"] = {"n": int(zj.sum()), "r_max": round(float(rg[zj].max()), 3)}
        mis = ms
        o["r_max_misja"] = round(float(rg[mis].max()), 3)
        o["r_max_misja_po_fladze"] = round(float(rg[mis & po].max()), 3)
        o["r_max_epizod"] = round(float(rg.max()), 3)
        o["m_faktyczne_misja_po_fladze"] = round(R_E - D_STOP - o["r_max_misja_po_fladze"], 3)
        tu = L.tu
        o["r_est_max_utrata_misja"] = round(float(tu["r_est"][tu["misja"]].max()), 3)
        o["intruz_r"] = intruz(L)
        if n.startswith("L_"):
            t0 = L.t_flag
            o["per_100s"] = {}
            for a in range(0, 600, 100):
                s = mis & (sim >= t0 + a) & (sim < t0 + a + 100)
                if s.any():
                    o["per_100s"][f"{a}-{a + 100}"] = round(float(rg[s].max()), 3)
        out[n] = o
        print(n, k, o["r_max_misja_po_fladze"], o["r_max_epizod"], (o["r4_margin"] or {}).get("r_max"),
              {kk: v["r_max"] for kk, v in o["fazy"].items()}, o["intruz_r"] and o["intruz_r"]["max"], flush=True)
    ci = [v for kk, v in out.items() if not kk.startswith("L_")]
    pods = {"n_komorek_rmax_gt_20": sum(v["r_max_misja_po_fladze"] > 20 for v in ci),
            "n_komorek_rmax_gt_22": sum(v["r_max_misja_po_fladze"] > 22 for v in ci),
            "n_komorek_rmax_gt_24": sum(v["r_max_misja_po_fladze"] > 24 for v in ci),
            "definicja": "r_max = max r_GT w tickach misji po fladze utraty GNSS (approach/hold/orbit, przed zejściem planowym)"}
    print(pods)
    json.dump({"loty": out, "podsumowanie": pods}, open(os.path.join(N.OUT, "r2_promien.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
