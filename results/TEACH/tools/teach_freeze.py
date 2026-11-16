#!/usr/bin/env python3
"""results/TEACH/tools/teach_freeze.py — FREEZE TEACH (PRE_TEACH §4, PROMPT_TEACH_S1 §2; 0 bootów).

Kopia results/NAD3/tools/nad3_freeze.py (nietknięty) ze zmianami oznaczonymi „TEACH:”.
G unii 38 lotów: 25 lotów jak w NAD3 (12 cięć NADIR S4, 12 cięć NAD2 S3, lot długi L_c10_s01) oraz 12 cięć NAD3 S3 (boot ważny
w results/NAD3/s3/kampania_ksiega.jsonl) i cięcie B4 z NAD3 S2 (results/NAD3/s2/b4_c05_p1_na_zewnatrz; loader nad3_dane.Lot
na katalogu bootu). Okno i siatka jak w NAD3: e(t) = p_EKF(t) − GT(t) poziomo na osi timestamp_sample, [flaga cs_gnss_pos → 0,
zejście planowe], siatka 0.01 s, maksimum bieżące po τ′ ≤ krawędź. Krawędzie: dziesięć do 2.15 s.
Asercja wobec liczb CC (PRE_TEACH §4): |G − G_CC| ≤ 0.01 m w każdym polu, inaczej STOP-TEACH-1-FREEZE (kod 3, bez tabeli).
Tabela punktu „TEACH” w formacie NAD3: F = 0 we wszystkich polach obu trybów (5 koszyków — kształt sprawdzany przez osłonę),
E = 1.00 m, U′[tryb][i][k] = 1.5·(F + E + G(i)); τ* = 2.15 s = ostatnia krawędź, próg zatrzasku 41 ticków; dodatek 0.012 s.
Sprawdzian PRE §4: bariery po krawędziach, największe u′ 8.02 m, wykonalne, granice E_d / E_s na krawędzi τ* (1.05 / 1.75 m)
i przy τ ≤ 0.35 s (2.54 / 4.23 m), |Δ| ≤ 0.01 m.
Wyjście: results/TEACH/s1/freeze_G_TEACH.json, results/TEACH/s1/freeze_U_TEACH.json.
"""
import hashlib
import json
import os
import sys

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/NAD2_RECON/tools"), os.path.join(ROOT, "results/NAD3_RECON/tools")]
OUT = os.path.join(ROOT, "results/TEACH/s1")
DT = 0.01
KRAW = [0.35, 0.55, 0.75, 0.95, 1.15, 1.35, 1.55, 1.75, 1.95, 2.15]                      # TEACH: dziesięć krawędzi
G_CC = [0.8573, 1.2703, 1.6614, 2.0590, 2.3471, 2.5715, 2.7572, 2.8929, 3.1498, 3.3315]  # TEACH: PRE_TEACH §4
TOL = 0.01
E_TEACH = 1.00                                                                           # TEACH: jeden punkt
R_ZAD = 20.0
R_E, D_STOP, DELTA_D5, ZAPAS = 32.0, 2.85, 1.524, 1.5
TAU_STAR, TAU_EPS, DT_PETLI, T_MARGIN = 2.15, 0.012, 0.05, 2                            # TEACH: τ* 2.15 s
PROG = 41
KOSZE, TRYBY = 5, ("para", "jeden")
SPR = {"bariery": [24.84, 24.22, 23.63, 23.04, 22.61, 22.27, 21.99, 21.79, 21.40, 21.13], "u_max": 8.02,
       "E_d_tau_star": 1.05, "E_s_tau_star": 1.75, "E_d_0": 2.54, "E_s_0": 4.23}                # TEACH: PRE_TEACH §4
PRE = os.path.join(ROOT, "PRE_TEACH.md")
PRE_SHA = "ee1a4bb70129dde42cf7b2fba0bfa6807bae9aeac676e2e031e0d22eb8ab0e54"
NAD3_S3 = os.path.join(ROOT, "results/NAD3/s3")
NAD3_B4 = os.path.join(ROOT, "results/NAD3/s2/b4_c05_p1_na_zewnatrz")


def loty_nad3():
    """TEACH: 12 cięć NAD3 S3 (ważne wg księgi kampanii, katalogi p*_c05_* / p*_c10_*) + B4 z NAD3 S2."""
    ks = [json.loads(l) for l in open(os.path.join(NAD3_S3, "kampania_ksiega.jsonl")) if l.strip()]
    wazne = {w["nazwa"] for w in ks if w.get("status") == "wazny"}
    out = sorted(n for n in os.listdir(NAD3_S3) if n in wazne and ("_c05_" in n or "_c10_" in n)
                 and os.path.isdir(os.path.join(NAD3_S3, n)))
    assert len(out) == 12, out
    return [(f"NAD3_S3/{n}", os.path.join(NAD3_S3, n)) for n in out] + [("NAD3_S2/b4_c05_p1_na_zewnatrz", NAD3_B4)]


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
    for n, d in loty_nad3():                                    # TEACH: 13 lotów NAD3 (bez pamięci podręcznej)
        L = N.Lot(n, d, None)
        g = np.arange(L.t_flag, L.t_zp, DT)
        out.append((n, (L.ekf_w(g) - L.gt(g))[:, :2]))
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
    assert hashlib.sha256(open(PRE, "rb").read()).hexdigest() == PRE_SHA, "sha PRE_TEACH"
    s = serie()
    assert len(s) == 38, len(s)
    best = g_kum(s)
    best25 = g_kum(s[:25])                                      # TEACH: czy 13 lotów NAD3 podnosi któreś pole
    G = [round(best[k][0], 4) for k in KRAW]
    G25 = [round(best25[k][0], 4) for k in KRAW]
    roz = [round(a - b, 4) for a, b in zip(G, G_CC)]
    gj = {"krawedzie_tau_s": KRAW, "G": G, "G_CC": G_CC, "roznica": roz, "tolerancja": TOL, "n_lotow": len(s),
          "G_25_lotow": G25, "nad3_podnosi_pole": [a > b for a, b in zip(G, G25)],
          "loty": [n for n, _ in s], "argmax": {str(k): {"lot": best[k][1], "tau_prim": best[k][2]} for k in KRAW},
          "okno": "[flaga cs_gnss_pos → 0, zejście planowe], siatka 0.01 s, poziomo, maksimum bieżące po τ′ ≤ krawędź"}
    os.makedirs(OUT, exist_ok=True)
    json.dump(gj, open(os.path.join(OUT, "freeze_G_TEACH.json"), "w"), ensure_ascii=False, indent=1)
    print("G", G, "CC", G_CC, "Δ", roz)
    print("G25", G25, "NAD3 podnosi", gj["nad3_podnosi_pole"])
    if any(abs(x) > TOL for x in roz):
        print("STOP-TEACH-1-FREEZE: |G − G_CC| > 0.01 m")
        sys.exit(3)
    m = R_E - D_STOP - R_ZAD
    F = {tr: [0.0] * KOSZE for tr in TRYBY}                     # TEACH: F = 0 — cały błąd źródła w E
    n = len(KRAW)
    U = {tr: [[round(ZAPAS * (F[tr][k] + E_TEACH + G[i]), 6) for k in range(KOSZE)] for i in range(n)] for tr in TRYBY}
    up = [U[tr][i][k] + DELTA_D5 for tr in U for i in range(n) for k in range(KOSZE)]
    bariery = [round(R_E - D_STOP - (U["jeden"][i][0] + DELTA_D5), 4) for i in range(n)]
    R_min = R_E - D_STOP - max(up)
    wyk = all(x <= m for x in up)
    assert round((TAU_STAR - T_MARGIN * DT_PETLI) / DT_PETLI, 9) == PROG
    t = {"punkt": "TEACH", "E": E_TEACH, "krawedzie_tau_s": KRAW, "G": G, "F": F, "zapas": ZAPAS, "delta_D5": DELTA_D5, "R_E": R_E,
         "d_stop": D_STOP, "tau_star_s": TAU_STAR, "tau_eps_s": TAU_EPS, "prog_zatrzasku_ticki": PROG, "dt_s": DT_PETLI,
         "pole_brak": ["jeden", 4], "U": U, "regula": "U′ = 1.5·(F_zn + E + G); u′ = U′ + Δ_D5; R = R_E − d_stop − u′"}
    doc = {"tabela": t, "sha256_tabeli": kan_sha(t), "pre_sha256": PRE_SHA, "r_zad": R_ZAD, "m_r_zad": round(m, 4),
           "wykonalne": wyk, "u_prim_max": round(max(up), 4), "bariera_min": round(R_min, 4), "bariery": bariery,
           "freeze_G": "results/TEACH/s1/freeze_G_TEACH.json", "F_zrodlo": "PRE_TEACH §4: F = 0 we wszystkich polach"}
    g_l, g_0 = G[-1], G[0]
    spr = {"bariery": bariery, "u_max": round(max(up), 4), "wykonalne": wyk,
           "E_d_tau_star": round((m - DELTA_D5 - ZAPAS * g_l) / (ZAPAS + 1.0), 4), "E_s_tau_star": round((m - DELTA_D5) / ZAPAS - g_l, 4),
           "E_d_0": round((m - DELTA_D5 - ZAPAS * g_0) / (ZAPAS + 1.0), 4), "E_s_0": round((m - DELTA_D5) / ZAPAS - g_0, 4)}
    ok = (wyk and all(abs(a - b) <= TOL for a, b in zip(bariery, SPR["bariery"])) and abs(spr["u_max"] - SPR["u_max"]) <= TOL
          and all(abs(spr[k] - SPR[k]) <= TOL for k in ("E_d_tau_star", "E_s_tau_star", "E_d_0", "E_s_0")))
    doc["sprawdzian_PRE_4"] = {**spr, "oczekiwane": SPR, "ok": ok}
    json.dump(doc, open(os.path.join(OUT, "freeze_U_TEACH.json"), "w"), ensure_ascii=False, indent=1)
    print("TEACH E", E_TEACH, "bariery", bariery, "u′max", spr["u_max"], "wykonalne", wyk, "sha", doc["sha256_tabeli"][:16])
    print("sprawdzian", spr, "OK" if ok else "STOP")
    gj["sprawdzian_PRE_4"] = {**spr, "ok": ok}
    json.dump(gj, open(os.path.join(OUT, "freeze_G_TEACH.json"), "w"), ensure_ascii=False, indent=1)
    if not ok:
        sys.exit(4)


if __name__ == "__main__":
    main()
