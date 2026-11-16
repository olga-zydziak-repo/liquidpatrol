#!/usr/bin/env python3
"""results/TEACH/tools/teach_w5.py — W5 replay osłony na 13 lotach reconu z poprawkami mapy i tabelą TEACH (PROMPT_TEACH_S1 §4 W5;
0 bootów). Wzór results/NAD3/tools/nad3_w2.py (nietknięty).

Strumień: results/TEACH/tools/teach_strumien.py (poprawki W2 w wariancie z results/TEACH/s1/tor.json, dostarczenie w miejscu seq
datagramu lotu). Osłona r03/nadir_shield.NadirShield(nad3, tabela results/TEACH/s1/freeze_U_TEACH.json) przez ścieżkę drivera
results/NAD3/tools/nad3_krok.krok (nietknięta; driver TEACH woła ją bez zmian). Pętla otwarta: tor drona, EKF i GT z zapisu.
Miary na łatę × lot (ticki utraty epizodu cięcia z przedziałem): e′ = |p_corr − GT(t próbki EKF)| poziomo, liczba e′ > U′
(U′ przedziału użytego przez osłonę), max e′/U′; pierwsza odmowa (tick, misja, przyczyna, czas od flagi); τ max w misji
i w całej utracie. Wynik do porównania z lotami, nie do zmiany tabeli ani toru.
Wyjście: results/TEACH/s1/w5_replay.json.
"""
import json
import math
import os
import sys

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/TEACH/tools"), os.path.join(ROOT, "results/NAD3/tools"),
                os.path.join(ROOT, "results/NAD3_RECON/tools")]
import nad3_krok                                                     # noqa: E402
import teach_strumien as TS                                          # noqa: E402
from r03 import nadir_shield as NS                                   # noqa: E402
from r03 import config as C                                          # noqa: E402

OUT = os.path.join(ROOT, "results/TEACH/s1")
TAB = os.path.join(OUT, "freeze_U_TEACH.json")


class _Rama:
    def __init__(self):
        self.t_fix = self.kosz = self.tryb = None


def przebieg(L, inp_list, sha):
    sh = NS.NadirShield(nadir_mode=True, kont_mode=True, nad3=True, tabela=TAB, tabela_sha=sha)
    sh.reset()
    sh.pos_debounce_ticks = C.DEBOUNCE_TICKS
    sh.pos_hyst_ticks = int(round(C.HYST_M_S / C.DT))
    T = sh.nad3_T
    rama = _Rama()
    n_ut = n_ocen = n_viol = 0
    eU, eU_arg = 0.0, None
    taus_m, taus = [], []
    refuse = None
    r_by_tick = {r["tick"]: r for r in L.rama}
    for inp in inp_list:
        r = r_by_tick[inp["_tick"]]
        if inp.get("t_fix") is not None:
            rama.t_fix, rama.kosz, rama.tryb = inp["t_fix"], inp["kosz"], inp["tryb"]
        d, _ = nad3_krok.krok(sh, inp["_tick"], inp["pos"], inp["pos_corr"], inp["vel"], inp["target"], inp["target_corr"], "PATROL",
                              inp["pos_flag"], inp["cs_gnss_pos"], inp["now"], None, rama)
        ph = sh.kont_phase()
        misja = L.misja(r)
        if ph == "KONT_REFUSE" and refuse is None:
            refuse = {"tick": inp["_tick"], "misja": bool(misja), "przyczyna": sh.kont_cause,
                      "t_od_flagi": round(inp["_sim"] - L.t_flag, 2) if L.t_flag else None, "tau": round(sh._tau, 4)}
        if ph == "NOMINAL" or inp["_ep"] != L.ep_cut:
            continue
        n_ut += 1
        if sh._tau is not None:
            taus.append(sh._tau)
            if misja:
                taus_m.append(sh._tau)
        i, j, tr = sh._przedzial, sh._j_eff, sh._tryb_eff
        if i is None or j is None:
            continue
        ts = L.t_probki(inp["pos"], inp["_sim"])
        if ts is None:
            continue
        g = L.gt(ts)[0]
        pc = inp["pos_corr"]
        e = math.hypot(pc[0] - g[0], pc[1] - g[1])
        U = NS.u_nad3(T, i, j, tr) - NS.DELTA_D5
        n_ocen += 1
        n_viol += int(e > U)
        if e / U > eU:
            eU, eU_arg = e / U, {"sim": inp["_sim"], "e": round(e, 4), "U": round(U, 4), "przedzial": i, "misja": bool(misja)}
    return {"ticki_utraty": n_ut, "ticki_ocenione": n_ocen, "e_gt_U": n_viol, "max_e_do_U": round(eU, 4), "argmax": eU_arg,
            "refuse": refuse, "refuse_misja": bool(refuse and refuse["misja"]),
            "tau_misja_max": round(max(taus_m), 4) if taus_m else None, "tau_utrata_max": round(max(taus), 4) if taus else None}


def main():
    tor = json.load(open(os.path.join(OUT, "tor.json")))
    wariant = tor["tor"]["wariant_K"]
    sha = json.load(open(TAB))["sha256_tabeli"]
    out = {"tabela": os.path.relpath(TAB, ROOT), "sha256_tabeli": sha, "wariant_K": wariant, "loty": {}, "zbiorczo": {}}
    for n, d in TS.loty():
        L = TS.wczytaj_lot(n, d)
        o = {}
        for lata in TS.LATY:
            st = TS.strumien(L, TS.czesc(n, lata, wariant))
            ticks, _ = TS.ticki(L, st)
            o[lata] = przebieg(L, ticks, sha)
        out["loty"][n] = o
        print(n, {l: (v["e_gt_U"], v["max_e_do_U"], v["refuse"] and (v["refuse"]["misja"], v["refuse"]["przyczyna"], v["refuse"]["t_od_flagi"]),
                      v["tau_misja_max"]) for l, v in o.items()}, flush=True)
    for lata in TS.LATY:
        v = [out["loty"][n][lata] for n in out["loty"]]
        ci = [out["loty"][n][lata] for n in out["loty"] if not n.startswith("L_")]
        out["zbiorczo"][lata] = {"e_gt_U": sum(x["e_gt_U"] for x in v), "max_e_do_U": max(x["max_e_do_U"] for x in v),
                                 "refuse_misja_12ciec": sum(x["refuse_misja"] for x in ci),
                                 "refuse_misja_lot_dlugi": out["loty"]["L_c10_s01"][lata]["refuse_misja"],
                                 "przyczyny_w_misji": sorted({x["refuse"]["przyczyna"] for x in v if x["refuse_misja"]}),
                                 "przyczyny_poza_misja": sorted({x["refuse"]["przyczyna"] for x in v if x["refuse"] and not x["refuse_misja"]}),
                                 "tau_misja_max_12ciec": max(x["tau_misja_max"] or 0 for x in ci),
                                 "tau_misja_max_lot_dlugi": out["loty"]["L_c10_s01"][lata]["tau_misja_max"]}
        print(lata, out["zbiorczo"][lata], flush=True)
    out["e_gt_U_razem"] = sum(z["e_gt_U"] for z in out["zbiorczo"].values())
    out["max_e_do_U_razem"] = max(z["max_e_do_U"] for z in out["zbiorczo"].values())
    json.dump(out, open(os.path.join(OUT, "w5_replay.json"), "w"), ensure_ascii=False, indent=1)
    print("e′ > U′ razem", out["e_gt_U_razem"], "max e′/U′", out["max_e_do_U_razem"])


if __name__ == "__main__":
    main()
