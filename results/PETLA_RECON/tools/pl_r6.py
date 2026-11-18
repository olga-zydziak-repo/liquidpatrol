#!/usr/bin/env python3
"""results/PETLA_RECON/tools/pl_r6.py — R6 rachunek złożenia z barierą (PROMPT_PETLA_S0 §8; 0 bootów).

Łańcuch (w ramie osłony bez GNSS = ramie p_corr; poziomo):
  (1) |q| ≤ ρ                                — klasa intruza (definicja);
  (2) trk = q + e_trk, |trk| ≤ ρ + e_trk     — nierówność trójkąta; trk w ramie p_corr (harness/percep_proc.py:128-151);
  (3) rel_net = trk − p_corr                 — bench/features.py:28-29, own = p_corr (teach_flight.py:671-677);
  (4) r_est = |p_corr| ≤ |trk| + |rel_net| ≤ ρ + e_trk + D, D = |rel_net| (dystans z cech) — r_est w ramie wybranej
      (r03/nadir_shield.py:326-330 / 358-362);
  (5) e_trk = (p_corr − p) + (rel_net − rel) ⇒ e_trk ≤ e′ + ε_rel;
  (6) e′ ≤ U′(i) = zapas·(F + E + G(i))      — przesłanka istniejącego dowodu (tabela results/TEACH/s1/freeze_U_TEACH.json, F = 0;
      cert P9_teach); w lotach 0 przekroczeń (ANEKS_TEACH-5 / TEACH2-2);
  (7) ε_rel ≤ ε_rel,max                      — zmierzona (R2: misja po 30 s);
  (8) D ≤ D_max                              — zmierzona (loty, R2) albo model (R5: wariant W, rodziny i szukanie);
  (9) ALLOW w przedziale i wymaga r_est ≤ R(i) (r03/nadir_shield.py:311-313); R(i) z tabeli (bariery).
Wynik: ρ*_dowód(i) = R(i) − U′(i) − ε_rel,max − D;  ρ*_zmierz(i) = R(i) − e_trk,max − D (e_trk zmierzone wprost).
Wyjście: results/PETLA_RECON/r6.json.
"""
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pl_dane as PD                                     # noqa: E402

OUT = os.path.join(PD.ROOT, "results/PETLA_RECON")


def main():
    T = json.load(open(os.path.join(PD.ROOT, "results/TEACH/s1/freeze_U_TEACH.json")))
    tab = T["tabela"]
    R = T["bariery"]
    U = [tab["zapas"] * (max(tab["F"]["jeden"][0], tab["F"]["para"][0]) + tab["E"] + g) for g in tab["G"]]
    r2, r2b = json.load(open(os.path.join(OUT, "r2.json"))), json.load(open(os.path.join(OUT, "r2b.json")))
    eps_rel = r2b["rel_err_h"]["reszta"]["max"]
    e_trk = r2b["etrk_h"]["reszta"]["max"]
    D_loty = r2["d_cech_max_misja"]
    r45 = json.load(open(os.path.join(OUT, "r45.json")))
    D_r5 = max(v["d_cech_max"] for k, v in r45.items() if k.startswith("W_1.0_"))
    D_r5_szuk = None
    fn = os.path.join(OUT, "szukanie_r5.json")
    if os.path.exists(fn):
        D_r5_szuk = json.load(open(fn))["najlepszy"]["miary"]["d_cech_max"]
    D_r5_all = max(D_r5, D_r5_szuk or 0.0)
    przedz = []
    for i in range(len(R)):
        przedz.append({"i": i, "R": R[i], "U_prim": round(U[i], 4),
                       "rho_dowod_D_loty": round(R[i] - U[i] - eps_rel - D_loty, 3), "rho_zmierz_D_loty": round(R[i] - e_trk - D_loty, 3),
                       "rho_dowod_D_R5": round(R[i] - U[i] - eps_rel - D_r5_all, 3), "rho_zmierz_D_R5": round(R[i] - e_trk - D_r5_all, 3)})
    out = {"przeslanki": {"U_prim_0": U[0], "eps_rel_max_po_30s": eps_rel, "e_trk_max_po_30s": e_trk, "D_loty": D_loty,
                          "D_R5_rodziny_v1": D_r5, "D_R5_szukanie": D_r5_szuk, "D_R5": D_r5_all,
                          "eps_rel_pierwsze_30s_max": r2b["rel_err_h"]["pierwsze_30s"]["max"]},
           "statusy": {"(1) |q|<=rho": "definicja klasy", "(2)-(5) nierówności": "algebra (trójkąt)",
                       "(6) e'<=U'": "przesłanka istniejącego dowodu (P9_teach; w lotach 0 przekroczeń)",
                       "(7) eps_rel": "zmierzona (R2, 15 lotów, misja po 30 s); pierwsze 30 s do 11.96 m — poza przesłanką",
                       "(8) D": "zmierzona (loty) / model (R5)", "(9) bariera": "kod osłony (nadir_shield.py:311-313), tabela z sumą"},
           "przedzialy": przedz,
           "korekta_c": {"CC_rho_plus_D_dowod": 20.65, "tu_rho_plus_D_dowod": round(R[0] - U[0] - eps_rel, 3),
                         "CC_rho_plus_D_zmierz": 23.24, "tu_rho_plus_D_zmierz": round(R[0] - e_trk, 3)}}
    json.dump(out, open(os.path.join(OUT, "r6.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(out["przeslanki"], indent=1)); print(json.dumps(out["korekta_c"]))
    for p in przedz:
        print(p)


if __name__ == "__main__":
    main()
