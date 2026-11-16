#!/usr/bin/env python3
"""results/TEACH_RECON2/tools/teach2_r5.py — PROMPT_TEACH_S0B R1 (sprawdzian), R3 (podsumowanie georeferencji), R5, R6 (0 bootów).

Wejście results/TEACH_RECON2/czesci/*.json.gz (teach2.py).
R1: M1 nowym torem wobec results/TEACH_RECON/r5_wyniki.json — na łatę i rodzaj cech liczba przyjętych i największy błąd (tol. 0.001 m).
R5: na łatę × wariant × rodzaj: osobno „12 cięć” i „lot długi” (oraz per lot) — udział przyjętych, błąd p50/p95/max, liczba > 1.0 / 1.37
    / 2.28 m, przerwy (z [cięcie, pierwsza] i [ostatnia, koniec misji]) max, > 1.15 s, > 2.15 s; każda przerwa > 1.15 s z największym
    pokryciem prawdziwym wśród jej kadrów (kadry nieprzyjęte w przedziale przerwy) — „w mapie”, gdy ≥ 0.50, inaczej „poza mapą”;
    max przerwa w mapie / poza mapą; błąd wg odległości od środka klatki kluczowej i wg pokrycia z k (jak S0).
R3: per łata × wariant × rodzaj: |θ_k − e_k| i |t_k − cam_gt(k)| po klatkach kluczowych (p50 / max), liczba wiązań.
R6: jak S0 (orto_r5.g_siatka; U′ = 1.5·(E + G(τ)), R = R_E − d_stop − (U′ + Δ_D5)), dla M3 i M4, osobno 12 cięć / lot długi / razem;
    plus τ_dost = największa krawędź z R − E ≥ 20 m (dostępność; osłona liczy błąd źródła dwa razy, ANEKS_NAD3-4).
Wyjście: results/TEACH_RECON2/r1_sprawdzian.json, r5_wyniki.json, r3_georeferencja.json, r6_kontrakt.json.
"""
import glob
import gzip
import json
import math
import os
import sys

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, os.path.join(ROOT, "results/ORTO_RECON/tools"))
import orto_r5 as O5

OUT = os.path.join(ROOT, "results/TEACH_RECON2")
LOT_DL = "L_c10_s01"
ODL = ((0, 3), (3, 6), (6, 10), (10, 1e9))
POKR = ((0.5, 1.01), (0.3, 0.5), (0.0, 0.3))
I_SIM, I_TAU, I_K, I_RE, I_RN, I_ZG, I_PE, I_PN, I_ERR, I_OK, I_INN, I_PK, I_PMAX = range(13)


def przerwy(kl, t_cut, t_end):
    acc = [r[I_SIM] for r in kl if r[I_OK]]
    ts = [t_cut] + acc + [t_end]
    out = []
    for a, b in zip(ts[:-1], ts[1:]):
        g = b - a
        if g > 1.15:
            kad = [r for r in kl if a < r[I_SIM] < b or (b == t_end and r[I_SIM] == t_end and not r[I_OK])]
            pm = max((r[I_PMAX] for r in kad), default=0.0)
            out.append({"od": round(a - t_cut, 2), "s": round(g, 3), "pokrycie_max": pm, "w_mapie": pm >= 0.5})
    return [round(g, 3) for g in np.diff(ts)], out


def stat(kls):
    """kls: lista (kl, t_cut, t_end) — łącznie."""
    acc = [r for kl, _, _ in kls for r in kl if r[I_OK]]
    n = sum(len(kl) for kl, _, _ in kls)
    e = np.array([r[I_ERR] for r in acc])
    gaps, dl = [], []
    for kl, a, b in kls:
        g, d = przerwy(kl, a, b)
        gaps += g; dl += d
    gaps = np.array(gaps)
    wm = [d["s"] for d in dl if d["w_mapie"]]; pm = [d["s"] for d in dl if not d["w_mapie"]]
    q = lambda p: round(float(np.quantile(e, p)), 4) if e.size else None
    return {"n": n, "n_przyj": len(acc), "udz_przyj": round(len(acc) / n, 4) if n else None, "blad_p50": q(.5), "blad_p95": q(.95),
            "blad_max": round(float(e.max()), 4) if e.size else None,
            "gt_100": int((e > 1.0).sum()), "gt_137": int((e > 1.37).sum()), "gt_228": int((e > 2.28).sum()),
            "przerwa_max": round(float(gaps.max()), 3), "przerwy_gt_115": int((gaps > 1.15).sum()), "przerwy_gt_215": int((gaps > 2.15).sum()),
            "przerwa_max_w_mapie": max(wm, default=0.0), "przerwa_max_poza_mapa": max(pm, default=0.0),
            "przerwy_gt_215_w_mapie": sum(g > 2.15 for g in wm), "przerwy_gt_215_poza_mapa": sum(g > 2.15 for g in pm),
            "przerwy_gt_115_lista": dl, "_gaps": gaps.tolist()}


def biny(acc):
    f = lambda x: {"n": len(x), "p50": round(float(np.median(x)), 4) if x else None, "max": round(float(max(x)), 4) if x else None}
    return ({f"{a}-{b if b < 1e8 else 'inf'}m": f([r[I_ERR] for r in acc if a <= math.hypot(r[I_RE], r[I_RN]) < b]) for a, b in ODL},
            {f"{a:.0%}-{min(b, 1):.0%}": f([r[I_ERR] for r in acc if a <= r[I_PK] < b]) for a, b in POKR})


def main():
    W = [json.load(gzip.open(f, "rt")) for f in sorted(glob.glob(os.path.join(OUT, "czesci", "*.json.gz")))]
    klucze = sorted({kk for w in W for kk in w["klatki"]})
    laty = sorted({w["lata"] for w in W}, key="SMJ".index)
    # R1
    s0 = json.load(open(os.path.join(ROOT, "results/TEACH_RECON/r5_wyniki.json")))
    r1 = {}
    for lata in laty:
        for rd in ("K1_SIFT", "K2_AKAZE"):
            acc = [r for w in W if w["lata"] == lata for r in w["klatki"][f"M1/{rd}"] if r[I_OK]]
            a = s0["laty"][lata][f"M1/{rd}"]["razem"]
            mx = max(r[I_ERR] for r in acc)
            r1[f"{lata}/{rd}"] = {"S0_n_przyj": a["n_przyj"], "S0B_n_przyj": len(acc), "S0_max": a["blad_max"], "S0B_max": round(mx, 4),
                                  "zgodne": len(acc) == a["n_przyj"] and abs(mx - a["blad_max"]) <= 0.001}
    r1_ok = all(v["zgodne"] for v in r1.values())
    json.dump({"zgodne_wszystkie": r1_ok, "wiersze": r1}, open(os.path.join(OUT, "r1_sprawdzian.json"), "w"), ensure_ascii=False, indent=1)
    print("R1", r1_ok, flush=True)
    # R3
    r3 = {}
    for lata in laty:
        for kk in klucze:
            th = [abs(x["geo"][kk]["theta_minus_e_deg"]) for w in W if w["lata"] == lata for x in w["kf"]]
            tt = [x["geo"][kk]["t_minus_cam_gt_m"] for w in W if w["lata"] == lata for x in w["kf"]]
            nw = [x["n_wiazan"][kk.split("/")[1]] for w in W if w["lata"] == lata for x in w["kf"]]
            r3[f"{lata}/{kk}"] = {"n_kf": len(th), "abs_theta_minus_e_deg": {"p50": round(float(np.median(th)), 3), "p95": round(float(np.quantile(th, .95)), 3), "max": round(max(th), 3)},
                                 "t_minus_cam_gt_m": {"p50": round(float(np.median(tt)), 4), "p95": round(float(np.quantile(tt, .95)), 4), "max": round(max(tt), 4)},
                                 "wiazan_na_kf": {"min": min(nw), "p50": float(np.median(nw))}}
    json.dump(r3, open(os.path.join(OUT, "r3_georeferencja.json"), "w"), ensure_ascii=False, indent=1)
    # R5
    wyn = {"laty": {}}
    for lata in laty:
        ws = sorted([w for w in W if w["lata"] == lata], key=lambda w: w["lot"])
        wyn["laty"][lata] = {}
        for kk in klucze:
            grupy = {"12_ciec": [w for w in ws if w["lot"] != LOT_DL], "lot_dlugi": [w for w in ws if w["lot"] == LOT_DL]}
            o = {}
            for g, gw in grupy.items():
                o[g] = stat([(w["klatki"][kk], w["t_ciecia"], w["t_konca"]) for w in gw])
                acc = [r for w in gw for r in w["klatki"][kk] if r[I_OK]]
                o[g]["blad_wg_odleglosci_od_kf"], o[g]["blad_wg_pokrycia_z_k"] = biny(acc)
            o["per_lot"] = {w["lot"]: {k: v for k, v in stat([(w["klatki"][kk], w["t_ciecia"], w["t_konca"])]).items()
                                       if not k.startswith("_") and k != "przerwy_gt_115_lista"} for w in ws}
            wyn["laty"][lata][kk] = o
            print(lata, kk, {g: (o[g]["blad_max"], o[g]["blad_p95"], o[g]["przerwa_max"], o[g]["przerwa_max_w_mapie"]) for g in grupy}, flush=True)
    # R6
    tau_max = 1.15
    for L in wyn["laty"].values():
        for kk, o in L.items():
            for g in ("12_ciec", "lot_dlugi"):
                tau_max = max(tau_max, o[g]["przerwa_max"])
    kr, G = O5.g_siatka(min(tau_max, O5.TAU_CAP))
    r6 = {"krawedzie": kr, "G": G, "regula": "U′ = 1.5·(E + G(τ)); R = R_E − d_stop − (U′ + Δ_D5); r_zad 20; τ_dost: R − E ≥ 20", "wiersze": {}}
    for lata, L in wyn["laty"].items():
        for kk, o in L.items():
            if kk.startswith("M1/"):
                continue
            for g in ("12_ciec", "lot_dlugi", "razem"):
                if g == "razem":
                    E = max(o["12_ciec"]["blad_max"], o["lot_dlugi"]["blad_max"])
                    gap = max(o["12_ciec"]["przerwa_max"], o["lot_dlugi"]["przerwa_max"])
                    gs = o["12_ciec"]["_gaps"] + o["lot_dlugi"]["_gaps"]
                else:
                    E, gap, gs = o[g]["blad_max"], o[g]["przerwa_max"], o[g]["_gaps"]
                ts = round(math.ceil(gap / O5.SIATKA - 1e-9) * O5.SIATKA, 2)
                n = len(kr) if ts > kr[-1] else kr.index(ts) + 1
                R = [round(O5.R_E - O5.D_STOP - (O5.ZAPAS * (E + G[i]) + O5.DELTA_D5), 4) for i in range(len(kr))]
                ok = [kr[i] for i in range(len(kr)) if R[i] >= O5.R_ZAD]
                dost = [kr[i] for i in range(len(kr)) if R[i] - E >= O5.R_ZAD]
                tau_ok = ok[-1] if ok else None
                if R[n - 1] >= O5.R_ZAD and ts <= kr[-1]:
                    ocena = "mieści się"
                elif tau_ok is not None:
                    ocena = f"mieści się z odmowami (odmowa przy przerwie > {tau_ok:.1f} s: {sum(x > tau_ok for x in gs)} przerw)"
                else:
                    ocena = "nie mieści się"
                r6["wiersze"][f"{lata}/{kk}/{g}"] = {"E": E, "przerwa_max": gap, "tau_star": ts, "R_tau_star": R[n - 1], "tau_ok": tau_ok,
                                                     "tau_dost": dost[-1] if dost else None, "ocena": ocena,
                                                     "zdanie": f"Łata {lata}, {kk}, {g}: E = {E:.2f} m, τ* = {ts:.1f} s, R(τ*) = {R[n - 1]:.2f} m — {ocena}; "
                                                               f"dostępność (R − E ≥ 20) do {dost[-1] if dost else 0:.1f} s."}
    for L in wyn["laty"].values():
        for o in L.values():
            for g in ("12_ciec", "lot_dlugi"):
                o[g].pop("_gaps", None)
    json.dump(wyn, open(os.path.join(OUT, "r5_wyniki.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(r6, open(os.path.join(OUT, "r6_kontrakt.json"), "w"), ensure_ascii=False, indent=1)
    for k, v in r6["wiersze"].items():
        if "SIFT" in k:
            print(v["zdanie"])


if __name__ == "__main__":
    main()
