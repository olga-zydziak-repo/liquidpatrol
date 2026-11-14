#!/usr/bin/env python3
"""results/NAD3/tools/nad3_freeze.py — FREEZE NADIR-III (PRE_NAD3 §4, PROMPT_NAD3_S1 §2; 0 bootów).

G unii 25 lotów: 12 cięć NADIR S4 (wyciągi results/NAD2_RECON/ulg/, loader results/NAD2_RECON/tools/nad2_dane.py), 12 cięć NAD2 S3
i lot długi L_c10_s01 (loader results/NAD3_RECON/tools/nad3_dane.py; wyciąg ulg.jsonl.gz w katalogu bootu). e(t) = p_EKF(t) − GT(t)
poziomo na osi timestamp_sample, okno [flaga cs_gnss_pos → 0, zejście planowe], siatka 0.01 s, przyrost |e(t+τ′) − e(t)| po wszystkich
t, maksimum bieżące po τ′ ≤ krawędź (jak results/NAD2_RECON/tools/nad2_r2.py). Krawędzie 0.35 / 0.55 / 0.75 / 0.95 / 1.15 s.
Asercja wobec liczb CC (PRE §4): |G − G_CC| ≤ 0.01 m w każdym polu, inaczej STOP-NAD3-1-FREEZE (kod wyjścia 3, bez tabel).
Tabele punktów P1/P2/P3 (E = 1.00 / 1.75 / 2.75 m): U′[tryb][i][k] = 1.5·(F_zn(k, tryb) + E + G(i)), F_zn z results/NAD2/s1/freeze_U.json
bez zmian; u′ = U′ + Δ_D5; R = R_E − d_stop − u′; τ* = 1.15 s = ostatnia krawędź, próg zatrzasku 21 ticków (τ* − 2·dt); dodatek 0.012 s;
pole `wykonalne` = [u′ ≤ m(r_zad = 20 m) we wszystkich polach]. Sumy: sha256 kanonicznego JSON tabeli (sort_keys, separatory zwarte),
sha PRE_NAD3.md. Sprawdzian PRE §4: najniższa bariera 21.93 / 20.80 / 19.30 m, E_d 1.37, E_s 2.28 (|Δ| ≤ 0.01 m).
Wyjście: results/NAD3/s1/freeze_G.json, results/NAD3/s1/freeze_U_P{1,2,3}.json.
"""
import hashlib
import json
import os
import sys

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/NAD2_RECON/tools"), os.path.join(ROOT, "results/NAD3_RECON/tools")]
OUT = os.path.join(ROOT, "results/NAD3/s1")
DT = 0.01
KRAW = [0.35, 0.55, 0.75, 0.95, 1.15]
G_CC = [0.8573, 1.2703, 1.6614, 2.0590, 2.3471]
TOL = 0.01
PUNKTY = {"P1": 1.00, "P2": 1.75, "P3": 2.75}
R_ZAD = 20.0
R_E, D_STOP, DELTA_D5, ZAPAS = 32.0, 2.85, 1.524, 1.5
TAU_STAR, TAU_EPS, DT_PETLI, T_MARGIN = 1.15, 0.012, 0.05, 2
SPR = {"bariera_min": {"P1": 21.93, "P2": 20.80, "P3": 19.30}, "E_d": 1.37, "E_s": 2.28}
WYK_OCZ = {"P1": True, "P2": True, "P3": False}
PRE = os.path.join(ROOT, "PRE_NAD3.md")
PRE_SHA = "56a1ac4396630d41b5e87f1161e090097b8b5f39d2a4ade793664a13c06a37da"


def serie():
    import nad2_dane as D2
    import nad3_dane as N
    out = []
    for n in D2.CIECIA_S4:
        b = D2.Boot(n)
        g = np.arange(b.t_flag, b.zp[b.denial["episode_id"]], DT)
        out.append((f"NADIR_S4/{n}", (b.ekf_w(g) - b.gt(g))[:, :2]))
    for n, d, k in N.loty():
        L = N.wczytaj(n, d, k)
        g = np.arange(L.t_flag, L.t_zp, DT)
        out.append((f"NAD2/{n}", (L.ekf_w(g) - L.gt(g))[:, :2]))
    return out


def g_kum(seria):
    lag_max = int(round(max(KRAW) / DT))
    best = {k: (0.0, None, None) for k in KRAW}
    for n, e in seria:
        run, arg, ki = 0.0, None, 0
        for L in range(1, lag_max + 1):
            d = e[L:] - e[:-L]
            mx = float(np.hypot(d[:, 0], d[:, 1]).max())
            if mx > run:
                run, arg = mx, round(L * DT, 2)
            while ki < len(KRAW) and L * DT >= KRAW[ki] - 1e-9:
                if run > best[KRAW[ki]][0]:
                    best[KRAW[ki]] = (run, n, arg)
                ki += 1
    return best


def kan_sha(t):
    return hashlib.sha256(json.dumps(t, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main():
    assert hashlib.sha256(open(PRE, "rb").read()).hexdigest() == PRE_SHA, "sha PRE_NAD3"
    s = serie()
    assert len(s) == 25, len(s)
    best = g_kum(s)
    G = [round(best[k][0], 4) for k in KRAW]
    roz = [round(a - b, 4) for a, b in zip(G, G_CC)]
    gj = {"krawedzie_tau_s": KRAW, "G": G, "G_CC": G_CC, "roznica": roz, "tolerancja": TOL, "n_lotow": len(s),
          "loty": [n for n, _ in s], "argmax": {str(k): {"lot": best[k][1], "tau_prim": best[k][2]} for k in KRAW},
          "okno": "[flaga cs_gnss_pos → 0, zejście planowe], siatka 0.01 s, poziomo, maksimum bieżące po τ′ ≤ krawędź"}
    os.makedirs(OUT, exist_ok=True)
    json.dump(gj, open(os.path.join(OUT, "freeze_G.json"), "w"), ensure_ascii=False, indent=1)
    print("G", G, "CC", G_CC, "Δ", roz)
    if any(abs(x) > TOL for x in roz):
        print("STOP-NAD3-1-FREEZE: |G − G_CC| > 0.01 m")
        sys.exit(3)
    FU = json.load(open(os.path.join(ROOT, "results/NAD2/s1/freeze_U.json")))
    F = FU["tabela"]["F"]
    m = R_E - D_STOP - R_ZAD
    Fw = max(max(F["para"]), max(F["jeden"]))
    g_last = G[-1]
    E_d = (m - DELTA_D5 - ZAPAS * (Fw + g_last)) / (ZAPAS + 1.0)
    E_s = (m - DELTA_D5) / ZAPAS - g_last - Fw
    spr = {"E_d": round(E_d, 4), "E_s": round(E_s, 4)}
    ok = abs(E_d - SPR["E_d"]) <= TOL and abs(E_s - SPR["E_s"]) <= TOL
    for p, E in PUNKTY.items():
        U = {tr: [[round(ZAPAS * (F[tr][k] + E + G[i]), 6) for k in range(5)] for i in range(5)] for tr in ("para", "jeden")}
        up = [U[tr][i][k] + DELTA_D5 for tr in U for i in range(5) for k in range(5)]
        R_min = R_E - D_STOP - max(up)
        wyk = all(x <= m for x in up)
        t = {"punkt": p, "E": E, "krawedzie_tau_s": KRAW, "G": G, "F": F, "zapas": ZAPAS, "delta_D5": DELTA_D5, "R_E": R_E,
             "d_stop": D_STOP, "tau_star_s": TAU_STAR, "tau_eps_s": TAU_EPS, "prog_zatrzasku_ticki": 21, "dt_s": DT_PETLI,
             "pole_brak": ["jeden", 4], "U": U, "regula": "U′ = 1.5·(F_zn + E + G); u′ = U′ + Δ_D5; R = R_E − d_stop − u′"}
        assert round((TAU_STAR - T_MARGIN * DT_PETLI) / DT_PETLI, 9) == 21
        doc = {"tabela": t, "sha256_tabeli": kan_sha(t), "pre_sha256": PRE_SHA, "r_zad": R_ZAD, "m_r_zad": round(m, 4),
               "wykonalne": wyk, "u_prim_max": round(max(up), 4), "bariera_min": round(R_min, 4),
               "freeze_G": "results/NAD3/s1/freeze_G.json", "F_zrodlo": "results/NAD2/s1/freeze_U.json (sha256_tabeli "
               + FU["sha256_tabeli"][:16] + "…)"}
        json.dump(doc, open(os.path.join(OUT, f"freeze_U_{p}.json"), "w"), ensure_ascii=False, indent=1)
        spr[f"bariera_min_{p}"] = round(R_min, 4)
        spr[f"wykonalne_{p}"] = wyk
        ok = ok and abs(R_min - SPR["bariera_min"][p]) <= TOL and wyk == WYK_OCZ[p]
        print(p, "E", E, "R_min", round(R_min, 4), "wykonalne", wyk, "sha", doc["sha256_tabeli"][:16])
    print("sprawdzian", spr, "OK" if ok else "STOP")
    gj["sprawdzian_PRE_4"] = {**spr, "ok": ok}
    json.dump(gj, open(os.path.join(OUT, "freeze_G.json"), "w"), ensure_ascii=False, indent=1)
    if not ok:
        sys.exit(4)


if __name__ == "__main__":
    main()
