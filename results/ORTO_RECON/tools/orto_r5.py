#!/usr/bin/env python3
"""results/ORTO_RECON/tools/orto_r5.py — PROMPT_ORTO_S0 R4/R5/R6: wybór reguły odrzucania (c05), zestawienia, rachunek kontraktu (0 bootów).

`wybor`: z results/ORTO_RECON/r4_strojenie.json.gz (6 cięć c05, wszystkie reguły) dla każdej (łata, wariant, kandydat) reguła wybrana
leksykograficznie (kryterium wykonawcy, nie zamrożenie):
  (1) zbiór dopuszczalny: łącznie na 6 lotach największy błąd przyjętej poprawki ≤ 1.0 m (zmierzony błąd kontraktu NAD3) i ≥ 1 przyjęta;
  (2) w dopuszczalnym: najmniejsza największa przerwa (max po lotach), potem najwięcej przyjętych, potem identyfikator;
  (3) dopuszczalny pusty: najmniejszy największy błąd przyjętej (≥ 1 przyjęta), potem najmniejsza największa przerwa;
  żadna reguła nic nie przyjmuje: brak reguły (wpis null).
  Wyjście results/ORTO_RECON/r5_reguly.json.
`zestaw`: z results/ORTO_RECON/r4_ocena.json.gz (13 lotów) —
  R4 (reguła „wszystko”): per łata/wariant/kandydat/lot p50/p95/p99/max błędu wyniku, udział > 1.37 i > 2.28 m, udział bez wyniku;
  R5 (reguła wybrana) na lotach oceny (6 cięć c10 + lot długi) i osobno strojenia: max błąd przyjętej, przerwy (max, liczba > 1.15 s
  i > 2.15 s), liczba przyjętych z błędem > 1.37 m;
  R6: tabela U′ per łata (najlepszy kandydat pary na lotach oceny: najmniejszy E, potem τ*) — reguła NAD3 U′ = 1.5·(E + G(τ)),
  E = zmierzony max błąd przyjętej (oceny), krawędzie τ na siatce klatek 0.2 s do τ* = największa przerwa (zaokrąglona w górę
  do siatki), G(τ) jak results/NAD3/tools/nad3_freeze.py (te same 25 lotów, funkcje serie/g_kum, tylko odczyt; krawędzie podmienione);
  u′ = U′ + Δ_D5, R = R_E − d_stop − u′, warunek R(τ*) ≥ r_zad = 20 m. Zdanie per łata.
  Wyjście results/ORTO_RECON/r4_r5_zestaw.json, r6_kontrakt.json.
Użycie: orto_r5.py wybor | zestaw
"""
import gzip
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orto_r4 as R4

OUT = R4.OUT
ROOT = "/home/olga/projects/liquidpatrol"
PROG_WYB = 1.0
R_E, D_STOP, DELTA_D5, ZAPAS, R_ZAD = 32.0, 2.85, 1.524, 1.5, 20.0
SIATKA = 0.2
TAU_CAP = 30.0            # G liczone najdalej do 30 s; τ* dalej ⇒ wniosek tylko, jeśli bariera pada już na krawędzi 30 s


def wczytaj(tryb):
    return json.load(gzip.open(os.path.join(OUT, f"r4_{tryb}.json.gz"), "rt"))


def agreguj(wpisy):
    """Łącznie po lotach dla jednej reguły: max błąd przyjętej, max przerwa, przyjęte, przerwy > progi."""
    acc = [w for w in wpisy if w["n_przyj"]]
    return {"err_acc_max": max((w["err_acc_max"] for w in acc), default=None), "n_przyj": sum(w["n_przyj"] for w in wpisy),
            "przerwa_max": max(w["przerwa_max"] for w in wpisy), "przerwy_gt_115": sum(w["przerwy_gt_115"] for w in wpisy),
            "przerwy_gt_215": sum(w["przerwy_gt_215"] for w in wpisy), "acc_gt_137": sum(w["acc_gt_137"] for w in wpisy),
            "acc_gt_228": sum(w["acc_gt_228"] for w in wpisy), "n": sum(w["n"] for w in wpisy), "loty": len(wpisy)}


def wybor():
    S = wczytaj("strojenie")
    wyb, tab = {}, {}
    for lata in R4.LATY:
        for war in R4.WARIANTY:
            for kd in ("K1_SIFT", "K2_AKAZE", "K3_NCC"):
                ws = [w for w in S if w["lata"] == lata and w["wariant"] == war]
                ids = list(ws[0]["kand"][kd].keys())
                ag = {i: agreguj([w["kand"][kd][i] for w in ws]) for i in ids if i != "wszystko"}
                dop = [i for i, a in ag.items() if a["n_przyj"] and a["err_acc_max"] <= PROG_WYB]
                if dop:
                    best = min(dop, key=lambda i: (ag[i]["przerwa_max"], -ag[i]["n_przyj"], i))
                    tryb = "dopuszczalny"
                else:
                    cand = [i for i, a in ag.items() if a["n_przyj"]]
                    best = min(cand, key=lambda i: (ag[i]["err_acc_max"], ag[i]["przerwa_max"], i)) if cand else None
                    tryb = "najmniejszy_blad" if cand else "nic_nie_przyjmuje"
                k = f"{lata}/{war}/{kd}"
                wyb[k] = ws[0]["kand"][kd][best]["regula"] if best else None
                tab[k] = {"tryb_wyboru": tryb, "regula": best, "n_dopuszczalnych": len(dop), "n_regul": len(ag),
                          "strojenie": ag.get(best), "wszystko": agreguj([w["kand"][kd]["wszystko"] for w in ws])}
                print(k, tryb, best, ag.get(best), flush=True)
    json.dump({"kryterium": "(1) max błąd przyjętej ≤ 1.0 m na 6 cięciach c05 i ≥ 1 przyjęta; (2) min max przerwa, max przyjętych;"
                            " (3) pusty dopuszczalny: min max błąd przyjętej, potem min max przerwa",
               "wybrane": wyb, "tabela": tab}, open(os.path.join(OUT, "r5_reguly.json"), "w"), ensure_ascii=False, indent=1)


def rozklad(e):
    e = np.asarray(e, float)
    if not e.size:
        return None
    return {"n": int(e.size), "p50": round(float(np.quantile(e, .5)), 4), "p95": round(float(np.quantile(e, .95)), 4),
            "p99": round(float(np.quantile(e, .99)), 4), "max": round(float(e.max()), 4)}


def g_siatka(tau_max):
    sys.path[:0] = [ROOT, os.path.join(ROOT, "results/NAD2_RECON/tools"), os.path.join(ROOT, "results/NAD3_RECON/tools"),
                    os.path.join(ROOT, "results/NAD3/tools")]
    import nad3_freeze as FZ
    kr = [round(SIATKA * i, 2) for i in range(1, int(math.ceil(tau_max / SIATKA - 1e-9)) + 1)]
    FZ.KRAW = kr
    s = FZ.serie()
    best = FZ.g_kum(s)
    return kr, [round(best[k][0], 4) for k in kr]


def zestaw():
    O = wczytaj("ocena")
    wyb = json.load(open(os.path.join(OUT, "r5_reguly.json")))["wybrane"]
    r4, r5 = {}, {}
    for lata in R4.LATY:
        for war in R4.WARIANTY:
            for kd in ("K1_SIFT", "K2_AKAZE", "K3_NCC"):
                k = f"{lata}/{war}/{kd}"
                ws = sorted([w for w in O if w["lata"] == lata and w["wariant"] == war], key=lambda w: w["lot"])
                per = {}
                eall_ocena, eall_str = [], []
                for w in ws:
                    o = w["kand"][kd]["wszystko"]
                    e = [x[1] for x in o["klatki"] if x[1] is not None]
                    (eall_str if "_c05_" in w["lot"] else eall_ocena).extend(e)
                    per[w["lot"]] = {"rozklad": rozklad(e), "udz_gt_137": round(np.mean(np.array(e) > 1.37), 4) if e else None,
                                     "udz_gt_228": round(np.mean(np.array(e) > 2.28), 4) if e else None,
                                     "udz_bez_wyniku": round(o["brak"] / o["n"], 4), "n": o["n"]}
                def podsum(e, n):
                    e = np.array(e)
                    return {"rozklad": rozklad(e), "udz_gt_137": round(float(np.mean(e > 1.37)), 4) if e.size else None,
                            "udz_gt_228": round(float(np.mean(e > 2.28)), 4) if e.size else None, "udz_bez_wyniku": round(1 - e.size / n, 4)}
                n_oc = sum(w["n_klatek"] for w in ws if "_c05_" not in w["lot"])
                n_st = sum(w["n_klatek"] for w in ws if "_c05_" in w["lot"])
                r4[k] = {"per_lot": per, "ocena_razem": podsum(eall_ocena, n_oc), "strojenie_razem": podsum(eall_str, n_st)}
                reg = wyb.get(k)
                if reg is None:
                    r5[k] = None
                    continue
                oc = [w["kand"][kd][reg["id"]] for w in ws if "_c05_" not in w["lot"]]
                st = [w["kand"][kd][reg["id"]] for w in ws if "_c05_" in w["lot"]]
                r5[k] = {"regula": reg, "ocena": agreguj(oc), "strojenie_powtorzone": agreguj(st),
                         "per_lot_ocena": {w["lot"]: {kk: w["kand"][kd][reg["id"]][kk] for kk in
                                                      ("n_przyj", "err_acc_max", "przerwa_max", "przerwy_gt_115", "przerwy_gt_215",
                                                       "acc_gt_137")} for w in ws if "_c05_" not in w["lot"]}}
                print("R5", k, reg["id"], r5[k]["ocena"], flush=True)
    czasy = {}
    for kd in ("K1_SIFT", "K2_AKAZE", "K3_NCC"):
        v = [w["czas_ms_p50"][kd] for w in O]
        czasy[kd] = {"p50_z_p50_zadan": round(float(np.median(v)), 2), "max_p95": round(max(w["czas_ms_p95"][kd] for w in O), 2)}
    czasy["prostowanie"] = round(float(np.median([w["czas_prost_ms_p50"] for w in O])), 2)
    json.dump({"R4": r4, "R5": r5, "czasy_ms": czasy}, open(os.path.join(OUT, "r4_r5_zestaw.json"), "w"), ensure_ascii=False, indent=1)
    # R6
    m = R_E - D_STOP - R_ZAD
    naj = {}
    for lata in R4.LATY:
        for war in R4.WARIANTY:                                 # „kontrola” = odniesienie (sufit przyrządu), nie wynik pary
            kandy = [(kd, r5[f"{lata}/{war}/{kd}"]) for kd in ("K1_SIFT", "K2_AKAZE", "K3_NCC") if r5.get(f"{lata}/{war}/{kd}")
                     and r5[f"{lata}/{war}/{kd}"]["ocena"]["n_przyj"]]
            nm = lata if war == "para" else f"{lata}_kontrola"
            if not kandy:
                naj[nm] = None
                continue
            kd, v = min(kandy, key=lambda kv: (kv[1]["ocena"]["err_acc_max"], kv[1]["ocena"]["przerwa_max"]))
            naj[nm] = (kd, v["ocena"]["err_acc_max"], v["ocena"]["przerwa_max"])
    tau_max = min(max([v[2] for v in naj.values() if v] + [1.15]), TAU_CAP)
    kr, G = g_siatka(tau_max)
    r6 = {"m_r_zad": m, "siatka_s": SIATKA, "krawedzie": kr, "G": G, "regula": "U′ = 1.5·(E + G(τ)); u′ = U′ + Δ_D5; R = R_E − d_stop − u′",
          "laty": {}}
    for lata, v in naj.items():
        if v is None:
            r6["laty"][lata] = {"zdanie": f"Łata {lata}: żaden kandydat nie przyjął poprawki na lotach oceny — kontraktu nie ma z czego liczyć."}
            continue
        kd, E, gap = v
        ts = round(math.ceil(gap / SIATKA - 1e-9) * SIATKA, 2)
        ucięte = ts > kr[-1]
        U = [round(ZAPAS * (E + g), 4) for g in (G if ucięte else G[:kr.index(ts) + 1])]
        up = [round(u + DELTA_D5, 4) for u in U]
        R = [round(R_E - D_STOP - u, 4) for u in up]
        ok = R[-1] >= R_ZAD
        if ucięte and ok:
            ok = None                                           # bariera trzyma do 30 s, τ* dalej — nierozstrzygnięte
        r6["laty"][lata] = {"G_uciete_na_s": kr[-1] if ucięte else None, "kandydat": kd, "E_max_przyjetej": round(E, 4), "przerwa_max_s": round(gap, 3), "tau_star_s": ts,
                            "krawedzie": kr[:len(U)], "U_prim": U, "u_prim": up, "R": R, "R_tau_star": R[-1], "bariera_nad_r_zad": ok,
                            "zdanie": (f"Łata {lata}: {kd}, E = {E:.2f} m, τ* = {ts:.1f} s ⇒ R({min(ts, kr[-1]):.1f} s) = {R[-1]:.2f} m "
                                       + ("≥" if R[-1] >= R_ZAD else "<") + " r_zad 20 m — bariera "
                                       + {True: "zostaje", False: "NIE zostaje", None: "nierozstrzygnięta (G ucięte na 30 s)"}[ok]
                                       + " nad zadaniem.")}
        print(r6["laty"][lata]["zdanie"], flush=True)
    json.dump(r6, open(os.path.join(OUT, "r6_kontrakt.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    {"wybor": wybor, "zestaw": zestaw}[sys.argv[1]]()
