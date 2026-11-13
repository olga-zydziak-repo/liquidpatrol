#!/usr/bin/env python3
"""results/NAD3_RECON/tools/nad3_r1.py — PROMPT_NAD3_S0 R1: rachunek wymagań F_max(r, f, K) (0 bootów).

Stałe z results/NAD2_RECON/r5_tabela.json (R_E, d_stop, Δ_D5, krawędzie τ do 22 s, G_poziomo) i results/NAD2/s1/freeze_U.json
(zapas 1.5, F znacznika per koszyk × tryb, τ* 1.05, krawędzie ≤ 1.05 zgodne z r5). Reguła osłony (r03/nadir_shield.py:74-89):
u′ = U + Δ_D5, ALLOW ⇔ r_est ≤ R_E − d_stop − u′; komórka/zadanie o promieniu r wykonalne ⇔ u′(τ_max) ≤ m(r) = R_E − d_stop − r.
  τ_max(f, K) = (K + 1)/f + 0.05 s (rachunek CC); przedział wybierany jak w osłonie z τ + 0.012 s (TAU_EPS_NAD2) — obie wersje.
  (a) F = F_znacznika + E, zapas na całość:  U = 1.5·(F + G)            ⇒ F_max = (m − Δ_D5)/1.5 − G
  (b) zapas tylko na część mierzoną:          U = 1.5·(F_zn + G) + E     ⇒ E_max = m − Δ_D5 − 1.5·(F_zn + G), F_max = F_zn + E_max
  E_max(a) = F_max − F_zn. F_zn: najgorsze pole tabeli (jeden, koszyk 3–4: 0.4527) i najgorsze pole pary (0.2577).
Pochodzenie G dla przedziałów τ > 1.05 s: przeliczenie G_kum własnym kodem na tych samych 12 cięciach NADIR S4 (loader
results/NAD2_RECON/tools/nad2_dane.py, tylko import), z lotem/τ′ argmax i liczbą okien rozłącznych n = Σ ⌊T_lotu/τ⌋;
oraz świeże G z 13 lotów NAD2 (12 cięć S3 + lot długi; EKF bez poprawek — rama B+ nie karmi estymatora).
Wyjście: results/NAD3_RECON/r1_wymagania.json.
"""
import json
import os
import sys

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/NAD2_RECON/tools"), os.path.dirname(os.path.abspath(__file__))]
import nad3_dane as N

T5 = json.load(open(os.path.join(ROOT, "results/NAD2_RECON/r5_tabela.json")))["stale"]
FU = json.load(open(os.path.join(ROOT, "results/NAD2/s1/freeze_U.json")))["tabela"]
R_E, D_STOP, DELTA = T5["R_E"], T5["d_stop"], T5["delta_D5"]
KRAW, G = list(T5["krawedzie_tau"]), list(T5["G_poziomo"])
ZAPAS = FU["zapas"]
F_ZN = {"jeden_max": max(FU["F"]["jeden"]), "para_max": max(FU["F"]["para"])}
TAU_EPS = 0.012
R_SIATKA = list(range(14, 28))
FS, KS = [4, 2, 1, 0.5], [0, 1, 2, 3]
DT = 0.01
CC_PUNKTY = [  # (r, f, K, liczba z §1 promptu albo None = „niewykonalne”, opis)
    (20, 1, 0, 3.0, "1 Hz bez zgubień"), (20, 1, 1, 2.1, "1 Hz jedno zgubienie"), (20, 4, 0, 4.0, "4 Hz bez zgubień"),
    (22, 1, 0, 1.7, "1 Hz bez zgubień"), (22, 4, 0, 2.7, "4 Hz"), (24, 4, 0, 1.35, "4 Hz bez zgubień"),
    (24, 1, 1, None, "1 Hz jedno zgubienie — niewykonalne"), (26, 4, 0, 0.0, "4 Hz — ok. 0 m")]


def przedzial(tau):
    for i, k in enumerate(KRAW):
        if tau <= k + 1e-12:
            return i
    return None


def punkt(r, f, K, eps):
    tau = (K + 1) / f + 0.05
    i = przedzial(tau + eps)
    m = R_E - D_STOP - r
    if i is None:
        return {"tau": round(tau, 3), "przedzial": None, "F_max_a": None}
    g = G[i]
    fa = (m - DELTA) / ZAPAS - g
    o = {"tau": round(tau, 3), "przedzial": i, "kraw": KRAW[i], "G": g, "m": round(m, 3), "F_max_a": round(fa, 4)}
    for nz, fz in F_ZN.items():
        o[f"E_max_a_{nz}"] = round(fa - fz, 4)
        eb = m - DELTA - ZAPAS * (fz + g)
        o[f"E_max_b_{nz}"] = round(eb, 4)
        o[f"F_max_b_{nz}"] = round(fz + eb, 4)
    return o


def powierzchnia():
    out = {}
    for eps, lab in ((0.0, "cc"), (TAU_EPS, "oslona")):
        out[lab] = {f"r{r}_f{f}_K{K}": punkt(r, f, K, eps) for r in R_SIATKA for f in FS for K in KS}
    return out


def porownanie_cc(pw):
    rows = []
    for r, f, K, cc, opis in CC_PUNKTY:
        a, b = pw["cc"][f"r{r}_f{f}_K{K}"], pw["oslona"][f"r{r}_f{f}_K{K}"]
        fa = a["F_max_a"]
        if cc is None:
            zg = fa is not None and fa < 0
            roz = None
        else:
            roz = None if fa is None else round(fa - cc, 4)
            zg = roz is not None and abs(roz) <= 0.05
        rows.append({"r": r, "f": f, "K": K, "opis": opis, "cc": cc, "F_max_a": fa, "roznica": roz, "zgodne_0_05": zg,
                     "przedzial_cc": a.get("przedzial"), "przedzial_oslony": b.get("przedzial"), "F_max_a_oslona": b.get("F_max_a"),
                     "E_max_a_jeden": a.get("E_max_a_jeden_max"), "E_max_a_para": a.get("E_max_a_para_max"),
                     "E_max_b_jeden": a.get("E_max_b_jeden_max"), "E_max_b_para": a.get("E_max_b_para_max")})
    return rows


def g_kum(seria):
    """seria: lista (nazwa, e[n×2] na siatce DT). Zwraca per krawędź: G, argmax (lot, τ′), n okien rozłącznych, n lotów ≥ 0.9·G."""
    lag_max = int(round(max(KRAW) / DT))
    best = {k: (0.0, None, None) for k in KRAW}
    per_lot = {n: {} for n, _ in seria}
    for n, e in seria:
        run = 0.0
        ki = 0
        kr = sorted(KRAW)
        for L in range(1, min(lag_max, e.shape[0] - 1) + 1):
            d = e[L:] - e[:-L]
            dh = np.hypot(d[:, 0], d[:, 1])
            mx = float(dh.max())
            if mx > run:
                run = mx
                arg = (n, round(L * DT, 2))
            tau = L * DT
            while ki < len(kr) and tau >= kr[ki] - 1e-9:
                per_lot[n][kr[ki]] = (round(run, 4), arg[1])
                if run > best[kr[ki]][0]:
                    best[kr[ki]] = (round(run, 4), arg[0], arg[1])
                ki += 1
    dl = {n: e.shape[0] * DT for n, e in seria}
    out = {}
    for i, k in enumerate(KRAW):
        g, lot, tp = best[k]
        lo = KRAW[i - 1] if i else 0.0
        n_rozl = int(sum(np.floor(T / k) for T in dl.values()))
        n_rozl_lo = int(sum(np.floor(T / max(lo, DT)) for T in dl.values()))
        n_blisko = sum(1 for n in per_lot if per_lot[n].get(k, (0,))[0] >= 0.9 * g) if g > 0 else 0
        out[str(k)] = {"G": g, "lot_argmax": lot, "tau_argmax": tp, "n_okien_rozlacznych_przy_krawedzi": n_rozl,
                       "n_okien_rozlacznych_przy_dolnej": n_rozl_lo, "n_lotow_ge_0.9G": n_blisko,
                       "per_lot": {n: per_lot[n].get(k) for n in per_lot}}
    return out, {n: round(T, 2) for n, T in dl.items()}


def serie_s4():
    import nad2_dane as D2
    out = []
    for n in D2.CIECIA_S4:
        b = D2.Boot(n)
        t1 = b.zp[b.denial["episode_id"]]
        g = np.arange(b.t_flag, t1, DT)
        out.append((f"NADIR_S4/{n}", (b.ekf_w(g) - b.gt(g))[:, :2]))
    return out


def serie_nad2():
    out = []
    for n, d, k in N.loty():
        L = N.wczytaj(n, d, k)
        g = np.arange(L.t_flag, L.t_zp, DT)
        out.append((f"NAD2/{n}", (L.ekf_w(g) - L.gt(g))[:, :2]))
    return out


def main():
    pw = powierzchnia()
    cc = porownanie_cc(pw)
    for row in cc:
        print(row)
    s4 = serie_s4()
    gs4, dl4 = g_kum(s4)
    zg = {k: (gs4[k]["G"], G[i]) for i, k in enumerate(map(str, KRAW))}
    odtw = max(abs(a - b) for a, b in zg.values())
    print("odtworzenie G r5: max |Δ| =", odtw)
    nad2 = serie_nad2()
    gn, dln = g_kum(nad2)
    gl, _ = g_kum([x for x in nad2 if x[0].endswith("L_c10_s01")])
    gc, _ = g_kum([x for x in nad2 if not x[0].endswith("L_c10_s01")])
    por = {}
    for i, k in enumerate(map(str, KRAW)):
        por[k] = {"G_tabela": G[i], "G_NAD2_12ciec": gc[k]["G"], "G_NAD2_lot_dlugi": gl[k]["G"], "G_NAD2_13": gn[k]["G"],
                  "lot_argmax_NAD2": gn[k]["lot_argmax"], "przekracza_tabele": gn[k]["G"] > G[i]}
        print(k, por[k])
    out = {"stale": {"R_E": R_E, "d_stop": D_STOP, "delta_D5": DELTA, "zapas": ZAPAS, "krawedzie_tau": KRAW, "G": G,
                     "F_zn": F_ZN, "tau_eps_oslony": TAU_EPS, "tau_star_dzis": FU["tau_star_s"]},
           "reguly": {"a": "F_max = (m − Δ_D5)/1.5 − G(przedział τ_max); E_max = F_max − F_zn",
                      "b": "E_max = m − Δ_D5 − 1.5·(F_zn + G); F_max = F_zn + E_max",
                      "tau_max": "(K+1)/f + 0.05 s; wersja „oslona” wybiera przedział z τ + 0.012 s"},
           "powierzchnia": pw, "porownanie_cc": cc,
           "G_pochodzenie_NADIR_S4": {"odtworzenie_max_abs": round(odtw, 5), "dlugosci_okien_s": dl4, "krawedzie": gs4},
           "G_NAD2_swieze": {"dlugosci_okien_s": dln, "krawedzie": gn, "porownanie": por}}
    json.dump(out, open(os.path.join(N.OUT, "r1_wymagania.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
