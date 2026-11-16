#!/usr/bin/env python3
"""results/ORTO_RECON/tools/orto_r7_czas.py — PROMPT_ORTO_S0 R7: czas dopasowania jednego kadru na stanowisku (0 bootów).

Jeden proces, cv2 jednowątkowo i (osobno) z wątkami domyślnymi, bez innych obciążeń; łata A, wariant „para”, pierwsze N klatek lotu
oceny p02 (c10). Etapy: prostowanie kadru (orto_r3.Prost), cechy kadru + knn do mapy (Cechy.klatka), dopasowanie w oknie
(Cechy.dopasuj / NCC); pozycja przewidywana = GT (czas nie zależy od trafności). Rozgrzewka 5 klatek poza pomiarem.
Wyjście: results/ORTO_RECON/r7_czas.json (ms p50/p95 na etap i łącznie; częstość = 1000 / p95 łącznie).
Użycie: orto_r7_czas.py [N]
"""
import json
import os
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orto_r2 as R2
import orto_r3 as R3
import orto_r4 as R4


def pomiar(n, watki):
    cv2.setNumThreads(watki)
    kam = R2.Kam(R2.kamera())
    pr = R3.Prost(kam)
    mapa = cv2.imread(os.path.join(R4.DANE, "A_mapa_2025-08-12.png"))
    swiat = cv2.imread(os.path.join(R4.DANE, "A_swiat_2012-04-28.png"))
    det = {"K1_SIFT": R3.Cechy("K1_SIFT", mapa), "K2_AKAZE": R3.Cechy("K2_AKAZE", mapa), "K3_NCC": R3.NCC(mapa)}
    K = [k for k in R4.klatki_lotu("p02_p1_c10_zew")][:n + 5]
    t = {"prost": []} | {kd: {"klatka": [], "dopasuj": []} for kd in det}
    for i, k in enumerate(K):
        p_gt = np.array(k["gt_p"])
        C, Rk = kam.poza(p_gt, R2.rotm(k["gt_q"]))
        fr, _ = kam.renderuj(swiat, R3.RHO, C, Rk)
        t0 = time.perf_counter()
        rect, mask, off = pr(fr, k["ekf_q"], k["ekf_pos"])
        dt = (time.perf_counter() - t0) * 1e3
        if i >= 5:
            t["prost"].append(dt)
        for kd, D in det.items():
            t0 = time.perf_counter()
            fk = D.klatka(rect, mask)
            t1 = time.perf_counter()
            D.dopasuj(fk, p_gt[:2] + off, R3.r_szuk(1.0))
            t2 = time.perf_counter()
            if i >= 5:
                t[kd]["klatka"].append((t1 - t0) * 1e3)
                t[kd]["dopasuj"].append((t2 - t1) * 1e3)
    q = lambda v, p: round(float(np.quantile(v, p)), 2)
    out = {"prost_ms": {"p50": q(t["prost"], .5), "p95": q(t["prost"], .95)}}
    for kd in det:
        laczny = np.array(t["prost"]) + np.array(t[kd]["klatka"]) + np.array(t[kd]["dopasuj"])
        out[kd] = {"klatka_ms_p50": q(t[kd]["klatka"], .5), "dopasuj_ms_p50": q(t[kd]["dopasuj"], .5),
                   "lacznie_ms_p50": q(laczny, .5), "lacznie_ms_p95": q(laczny, .95),
                   "czestosc_hz_przy_p95": round(1000 / float(np.quantile(laczny, .95)), 2)}
    return out


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    wyn = {"n_klatek": n, "lot": "p02_p1_c10_zew", "lata": "A", "wariant": "para", "cpu": os.cpu_count(),
           "uwaga": "knn cech kadru do całej mapy łaty (100 × 100 m) jak w orto_r4; w locie mapa byłaby przycinana do okna szukania",
           "jeden_watek": pomiar(n, 1), "watki_domyslne": pomiar(n, -1)}
    json.dump(wyn, open(os.path.join(R4.OUT, "r7_czas.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(wyn, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
