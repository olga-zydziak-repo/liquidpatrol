#!/usr/bin/env python3
"""results/NAD3/tools/nad3_w2.py — W2 replay degradacji na 13 lotach NAD2 (PROMPT_NAD3_S1 §4 W2; 0 bootów).

Punkty P1 / P2 / P3 (tabele results/NAD3/s1/freeze_U_P{1,2,3}.json, E = 1.00 / 1.75 / 2.75 m) × bias radialny w obu kierunkach
(harness/nad3_degrad: {model bias_rad, kierunek, E_max = E tabeli, f 1, K 0, ziarno 1}) na strumieniu producenta odtworzonym
jak W1 (Rama NAD2 na zapisanych klatkach). Osłona: r03/nadir_shield.NadirShield(nad3, tabela punktu) przez nad3_krok.krok;
wejścia ticku z zapisu (p_EKF, sp_EKF, cs, pf, prędkość), own_net = p_EKF + Δ′, cel w ramie poprawionej = sp_EKF + Δ′.
Miary (ticki utraty z przedziałem): e′ = |p_corr′ − GT(t próbki EKF)| poziomo, liczba e′ > U′ (U′ przedziału użytego przez
osłonę), max e′/U′; REFUSE w misji (zatrzask w ticku misji: faza approach/hold/orbit przed zejściem planowym) z przyczyną
i czasem od flagi; τ zrealizowane w misji. Pętla otwarta: tor drona, EKF i GT z zapisu (wynik do porównania z lotami, nie
do zmiany tabel). Wyjście: results/NAD3/s1/w2_replay.json.
"""
import json
import math
import os
import sys

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/NAD3/tools"), os.path.join(ROOT, "results/NAD3_RECON/tools")]
import nad3_dane as N
import nad3_krok
import nad3_w1 as W1
from r03 import nadir_shield as NS
from r03 import config as C

OUT = os.path.join(ROOT, "results/NAD3/s1")
PUNKTY = ("P1", "P2", "P3")
KIERUNKI = ("na_zewnatrz", "do_srodka")


def przebieg(L, strumien, tab, sha, cfg):
    from harness import nad3_degrad as DG
    dg = DG.Degradacja(cfg)
    st = {s: dg.przetworz(strumien[s]) for s in sorted(strumien)}
    tk = {r["tick"]: r for r in N.jl(L.d, "trace.jsonl", "tk")}
    demo = {r["tick"]: r for r in N.jl(L.d, "demo.jsonl")}
    sh = NS.NadirShield(nadir_mode=True, kont_mode=True, nad3=True, tabela=tab, tabela_sha=sha)
    sh.reset()
    sh.pos_debounce_ticks = C.DEBOUNCE_TICKS
    sh.pos_hyst_ticks = int(round(C.HYST_M_S / C.DT))
    T = sh.nad3_T
    seqs = sorted(st)
    kl = W1.Klient()
    ip = 0
    n_ut = n_ocen = n_viol = 0
    eU = 0.0
    taus, refuse = [], None
    for r in L.rama:
        while ip < len(seqs) and seqs[ip] <= r["seq"]:
            m = st[seqs[ip]]
            kl.d_ne, kl.t_fix = list(m["d_ne"]), m["t_fix"]
            if m.get("ok"):
                kl.kosz, kl.tryb = m.get("kosz"), m.get("tryb")
            ip += 1
        t, dm = tk[r["tick"]], demo[r["tick"]]
        pe, se = r["p_ekf"], r["sp_ekf"]
        own_net = [pe[0] + kl.d_ne[0], pe[1] + kl.d_ne[1], pe[2]]
        tgt_net = [se[0] + kl.d_ne[0], se[1] + kl.d_ne[1], se[2]]
        d, _ = nad3_krok.krok(sh, r["tick"], pe, own_net, dm["own_vel_ned"], se, tgt_net, "PATROL", t["pf"], t["cs"], r["sim"],
                              t.get("dr"), kl)
        ph = sh.kont_phase()
        misja = L.misja(r)
        if ph == "KONT_REFUSE" and refuse is None:
            refuse = {"tick": r["tick"], "misja": bool(misja), "przyczyna": sh.kont_cause,
                      "t_od_flagi": round(r["sim"] - L.t_flag, 2) if L.t_flag else None}
        if ph == "NOMINAL" or r["ep"] != L.ep_cut:
            continue
        n_ut += 1
        if misja and sh._tau is not None:
            taus.append(sh._tau)
        i, j, tr = sh._przedzial, sh._j_eff, sh._tryb_eff
        if i is None or j is None:
            continue
        ts = L.t_probki(pe, r["sim"])
        if ts is None:
            continue
        g = L.gt(ts)[0]
        e = math.hypot(own_net[0] - g[0], own_net[1] - g[1])
        U = NS.u_nad3(T, i, j, tr) - NS.DELTA_D5
        n_ocen += 1
        n_viol += int(e > U)
        eU = max(eU, e / U)
    return {"ticki_utraty": n_ut, "ticki_ocenione": n_ocen, "e_gt_U": n_viol, "max_e_do_U": round(eU, 4),
            "refuse": refuse, "refuse_misja": bool(refuse and refuse["misja"]),
            "tau_misja_max": round(max(taus), 4) if taus else None}


def main():
    tabs = {p: os.path.join(OUT, f"freeze_U_{p}.json") for p in PUNKTY}
    shas = {p: json.load(open(tabs[p]))["sha256_tabeli"] for p in PUNKTY}
    out = {"tabele": {p: {"plik": os.path.relpath(tabs[p], ROOT), "sha256_tabeli": shas[p]} for p in PUNKTY}, "loty": {}, "zbiorczo": {}}
    for n, d, k in N.loty():
        L = N.wczytaj(n, d, k)
        strumien, pw = W1.producent(L, None)
        assert pw["niezgodne"] == 0
        o = {}
        for p in PUNKTY:
            E = json.load(open(tabs[p]))["tabela"]["E"]
            for kier in KIERUNKI:
                cfg = {"model": "bias_rad", "kierunek": kier, "E_max": E, "f": 1, "K": 0, "ziarno": 1}
                o[f"{p}/{kier}"] = przebieg(L, strumien, tabs[p], shas[p], cfg)
        out["loty"][n] = o
        print(n, {kk: (v["e_gt_U"], v["max_e_do_U"], v["refuse"] and (v["refuse"]["misja"], v["refuse"]["przyczyna"])) for kk, v in o.items()},
              flush=True)
    for p in PUNKTY:
        for kier in KIERUNKI:
            kk = f"{p}/{kier}"
            v = [out["loty"][n][kk] for n in out["loty"]]
            ci = [out["loty"][n][kk] for n in out["loty"] if not n.startswith("L_")]
            out["zbiorczo"][kk] = {"e_gt_U": sum(x["e_gt_U"] for x in v), "max_e_do_U": max(x["max_e_do_U"] for x in v),
                                   "refuse_misja_13": sum(x["refuse_misja"] for x in v), "refuse_misja_12ciec": sum(x["refuse_misja"] for x in ci),
                                   "przyczyny": sorted({x["refuse"]["przyczyna"] for x in v if x["refuse_misja"]}),
                                   "lot_dlugi": out["loty"]["L_c10_s01"][kk], "tau_misja_max": max(x["tau_misja_max"] or 0 for x in v)}
            print(kk, out["zbiorczo"][kk])
    json.dump(out, open(os.path.join(OUT, "w2_replay.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
