#!/usr/bin/env python3
"""results/TEACH_RECON2/tools/teach2_r7_czas.py — PROMPT_TEACH_S0B R7: koszt wiązań na kadr sprzed cięcia i czas rozwiązania R3 (0 bootów).

Jeden proces, cv2.setNumThreads(1), bez innych obliczeń. Łata S; loty p02_p1_c10_zew, p13_p3_c05_srod, L_c10_s01 (krótki c10, krótki c05,
długi). Wiązanie na kadr = render pomocniczy (tylko przyrząd) + prostowanie + cechy obu rodzajów + do 3 dopasowań na rodzaj (teach2.wiazania,
czas mierzony łącznie dla obu rodzajów; render wydzielony osobnym pomiarem). Rozwiązanie = teach2.rozwiaz dla M3 i M4 na rodzaj, 5 powtórzeń.
Wyjście: results/TEACH_RECON2/r7_czas.json.
"""
import json
import os
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import teach2 as T2

LOTY = ("p02_p1_c10_zew", "p13_p3_c05_srod", "L_c10_s01")


def main():
    cv2.setNumThreads(1)
    q = lambda v, p: round(float(np.quantile(v, p)), 2)
    wyn = {"lata": "S", "procesy": 1, "watki_cv2": 1, "loty": {}}
    wsz_wz, wsz_r, wsz_rend = [], {"M3": [], "M4": []}, []
    for lot in LOTY:
        L = T2.Lot(lot, "S")
        kf = L.klatki_kluczowe()
        cz = []
        wz = T2.wiazania(L, cz)
        rend = []
        for k in L.przed:
            a = time.perf_counter()
            C, Rk = L.kam.poza(np.array(k["gt_p"]), T2.R2.rotm(k["gt_q"]))
            L.kam.renderuj(L.teren, T2.T.PIKSEL_T, C, Rk)
            rend.append((time.perf_counter() - a) * 1e3)
        rr = {}
        for war in ("M3", "M4"):
            t = []
            for rd in T2.RODZAJE:
                for _ in range(5):
                    a = time.perf_counter(); T2.rozwiaz(kf, wz[rd], war); t.append((time.perf_counter() - a) * 1e3)
            rr[war] = {"p50": q(t, .5), "p95": q(t, .95)}
            wsz_r[war] += t
        wyn["loty"][lot] = {"n_przed": len(L.przed), "n_kf": len(kf), "wiazanie_na_kadr_ms": {"p50": q(cz, .5), "p95": q(cz, .95)},
                            "render_pomocniczy_ms": {"p50": q(rend, .5), "p95": q(rend, .95)}, "rozwiazanie_ms": rr,
                            "n_wiazan": {rd: len(wz[rd]) for rd in T2.RODZAJE}}
        wsz_wz += cz; wsz_rend += rend
        print(lot, wyn["loty"][lot], flush=True)
    wyn["razem"] = {"wiazanie_na_kadr_ms": {"p50": q(wsz_wz, .5), "p95": q(wsz_wz, .95)},
                    "render_pomocniczy_ms": {"p50": q(wsz_rend, .5), "p95": q(wsz_rend, .95)},
                    "rozwiazanie_na_lot_i_rodzaj_ms": {w: {"p50": q(v, .5), "p95": q(v, .95)} for w, v in wsz_r.items()},
                    "uwaga": "wiązanie na kadr obejmuje oba rodzaje cech i render pomocniczy; dron płaci bez renderu"}
    json.dump(wyn, open(os.path.join(T2.OUT, "r7_czas.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(wyn["razem"], ensure_ascii=False))


if __name__ == "__main__":
    main()
