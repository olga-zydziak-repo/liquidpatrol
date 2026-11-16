#!/usr/bin/env python3
"""results/TEACH_RECON/tools/teach_r5.py — PROMPT_TEACH_S0 R5 (wyniki) i R6 (rachunek kontraktu), 0 bootów.

Wejście: results/TEACH_RECON/r4_czesci/*.json.gz (teach_r34.py). Na łatę × wariant mapy × rodzaj cech × lot:
  udział przyjętych; błąd przyjętych p50 / p95 / max; liczba przyjętych ponad 1.0 / 1.37 / 2.28 m; przerwy między przyjętymi
  (z [cięcie, pierwsza] i [ostatnia, koniec misji]): max, liczba > 1.15 s i > 2.15 s. Razem po 13 lotach (max po lotach).
  Błąd przyjętych w funkcji odległości od środka klatki kluczowej (0–3, 3–6, 6–10, > 10 m) i pokrycia prawdziwego (≥ 50 %, 30–50 %, < 30 %).
R6: jak recon ORTO R6 (orto_r5.g_siatka: G z results/NAD3/tools/nad3_freeze.py, te same 25 lotów, krawędzie na siatce klatki 0.2 s):
  E = największy błąd przyjętej poprawki po 13 lotach; τ* = największa przerwa zaokrąglona w górę do siatki; U′ = 1.5·(E + G(τ)),
  u′ = U′ + Δ_D5, R = R_E − d_stop − u′. Zdanie na łatę i wariant (najlepszy rodzaj cech: najmniejsze E, potem τ*):
  „mieści się” — R(τ*) ≥ r_zad; „mieści się z odmowami” — R ≥ r_zad do krawędzi τ_ok < τ*, odmowa przy przerwie > τ_ok (podana
  liczba takich przerw); „nie mieści się” — R < r_zad już na pierwszej krawędzi.
Wyjście: results/TEACH_RECON/r5_wyniki.json, r6_kontrakt.json.
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

OUT = os.path.join(ROOT, "results/TEACH_RECON")
R_E, D_STOP, DELTA_D5, ZAPAS, R_ZAD, SIATKA = O5.R_E, O5.D_STOP, O5.DELTA_D5, O5.ZAPAS, O5.R_ZAD, O5.SIATKA
ODL = ((0, 3), (3, 6), (6, 10), (10, 1e9))
POKR = ((0.5, 1.01), (0.3, 0.5), (0.0, 0.3))


def statlot(kl, t_cut, t_end):
    acc = [r for r in kl if r[3]]
    e = np.array([r[2] for r in acc])
    ts = [t_cut] + [r[0] for r in acc] + [t_end]
    g = np.diff(ts)
    return {"n": len(kl), "n_przyj": len(acc), "udz_przyj": round(len(acc) / len(kl), 4) if kl else None,
            "n_wynik": sum(r[2] is not None for r in kl),
            "blad_p50": round(float(np.median(e)), 4) if e.size else None, "blad_p95": round(float(np.quantile(e, .95)), 4) if e.size else None,
            "blad_max": round(float(e.max()), 4) if e.size else None,
            "gt_100": int((e > 1.0).sum()), "gt_137": int((e > 1.37).sum()), "gt_228": int((e > 2.28).sum()),
            "przerwa_max": round(float(g.max()), 3), "przerwy_gt_115": int((g > 1.15).sum()), "przerwy_gt_215": int((g > 2.15).sum()),
            "_gaps": g.tolist()}


def main():
    W = [json.load(gzip.open(f, "rt")) for f in sorted(glob.glob(os.path.join(OUT, "r4_czesci", "*.json.gz")))]
    klucze = sorted({kk for w in W for kk in w["klatki"]})
    laty = sorted({w["lata"] for w in W}, key="SMJ".index)
    wyn = {"loty": sorted({w["lot"] for w in W}), "n_zadan": len(W), "laty": {}}
    for lata in laty:
        ws = sorted([w for w in W if w["lata"] == lata], key=lambda w: w["lot"])
        wyn["laty"][lata] = {"kalibracja": {w["lot"]: w["kal"] for w in ws}, "n_kf": {w["lot"]: w["n_kf"] for w in ws}}
        for kk in klucze:
            per = {w["lot"]: statlot(w["klatki"][kk], w["t_ciecia"], w["t_konca"]) for w in ws}
            acc = [r for w in ws for r in w["klatki"][kk] if r[3]]
            e = np.array([r[2] for r in acc])
            razem = {"n": sum(p["n"] for p in per.values()), "n_przyj": sum(p["n_przyj"] for p in per.values()),
                     "blad_p50": round(float(np.median(e)), 4) if e.size else None,
                     "blad_p95": round(float(np.quantile(e, .95)), 4) if e.size else None,
                     "blad_max": round(float(e.max()), 4) if e.size else None,
                     "gt_100": int((e > 1.0).sum()), "gt_137": int((e > 1.37).sum()), "gt_228": int((e > 2.28).sum()),
                     "przerwa_max": max(p["przerwa_max"] for p in per.values()),
                     "przerwy_gt_115": sum(p["przerwy_gt_115"] for p in per.values()),
                     "przerwy_gt_215": sum(p["przerwy_gt_215"] for p in per.values())}
            razem["udz_przyj"] = round(razem["n_przyj"] / razem["n"], 4)
            odl = {f"{a}-{b if b < 1e8 else 'inf'}m": (lambda x: {"n": len(x), "p50": round(float(np.median(x)), 4) if x else None,
                                                                  "max": round(float(max(x)), 4) if x else None})(
                [r[2] for r in acc if a <= r[5] < b]) for a, b in ODL}
            pok = {f"{a:.0%}-{min(b, 1):.0%}": (lambda x: {"n": len(x), "p50": round(float(np.median(x)), 4) if x else None,
                                                          "max": round(float(max(x)), 4) if x else None})(
                [r[2] for r in acc if a <= r[6] < b]) for a, b in POKR}
            wyn["laty"][lata][kk] = {"razem": razem, "per_lot": {l: {k: v for k, v in p.items() if k != "_gaps"} for l, p in per.items()},
                                     "blad_wg_odleglosci_od_kf": odl, "blad_wg_pokrycia": pok,
                                     "_gaps": [g for p in per.values() for g in p["_gaps"]]}
            print(lata, kk, razem, flush=True)
    # R6
    tau_max = min(max(max(v["razem"]["przerwa_max"] for kk, v in L.items() if "/" in kk) for L in wyn["laty"].values()), O5.TAU_CAP)
    kr, G = O5.g_siatka(max(tau_max, 1.15))
    r6 = {"siatka_s": SIATKA, "krawedzie": kr, "G": G, "regula": "U′ = 1.5·(E + G(τ)); u′ = U′ + Δ_D5; R = R_E − d_stop − u′; r_zad 20 m",
          "laty": {}}
    for lata, L in wyn["laty"].items():
        for war in ("M0", "M1", "M2"):
            kand = [(kk.split("/")[1], v) for kk, v in L.items() if kk.startswith(war + "/") and v["razem"]["n_przyj"]]
            if not kand:
                r6["laty"][f"{lata}/{war}"] = {"zdanie": f"Łata {lata}, mapa {war}: nie mieści się — żadna poprawka nie przyjęta."}
                continue
            rd, v = min(kand, key=lambda kv: (kv[1]["razem"]["blad_max"], kv[1]["razem"]["przerwa_max"]))
            E, gap = v["razem"]["blad_max"], v["razem"]["przerwa_max"]
            ts = round(math.ceil(gap / SIATKA - 1e-9) * SIATKA, 2)
            n = len(kr) if ts > kr[-1] else kr.index(ts) + 1
            U = [round(ZAPAS * (E + g), 4) for g in G[:n]]
            R = [round(R_E - D_STOP - (u + DELTA_D5), 4) for u in U]
            ok = [kr[i] for i in range(n) if R[i] >= R_ZAD]
            tau_ok = ok[-1] if ok else None                                # G rośnie z τ ⇒ R maleje: krawędzie ≥ r_zad to przedrostek
            if R[-1] >= R_ZAD and ts <= kr[-1]:
                ocena, zd = "mieści się", ""
            elif tau_ok is not None:
                n_odm = sum(1 for g in v["_gaps"] if g > tau_ok)
                ocena, zd = "mieści się z odmowami", f" (odmowa przy przerwie > {tau_ok:.1f} s: {n_odm} przerw)"
            else:
                ocena, zd = "nie mieści się", ""
            r6["laty"][f"{lata}/{war}"] = {"rodzaj": rd, "E": E, "przerwa_max_s": gap, "tau_star_s": ts, "krawedzie": kr[:n], "U_prim": U,
                                          "R": R, "R_tau_star": R[-1], "tau_ok_s": tau_ok, "ocena": ocena,
                                          "zdanie": f"Łata {lata}, mapa {war}: {rd}, E = {E:.2f} m, τ* = {ts:.1f} s, "
                                                    f"R(τ*) = {R[-1]:.2f} m — {ocena}{zd}."}
            print(r6["laty"][f"{lata}/{war}"]["zdanie"], flush=True)
    for L in wyn["laty"].values():
        for kk in list(L):
            if "/" in kk:
                L[kk].pop("_gaps", None)
    json.dump(wyn, open(os.path.join(OUT, "r5_wyniki.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(r6, open(os.path.join(OUT, "r6_kontrakt.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
