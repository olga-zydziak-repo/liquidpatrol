#!/usr/bin/env python3
"""results/TEACH_RECON/tools/teach_r7_czas.py — PROMPT_TEACH_S0 R7: czas jednej klatki w jednym procesie bez obciążenia (0 bootów).

Lot p02_p1_c10_zew, łata S, pierwsze 200 klatek serii „po” (+ 5 rozgrzewkowych poza pomiarem); klatki kluczowe = te same chwile, co
w r4_czesci/p02_p1_c10_zew_S.json.gz (prostowane przy EKF, jak M1/M2). Etapy na klatkę: render pomocniczy (kadr z terenu — w locie
robi to kamera, tu tylko przyrząd), prostowanie (orto_r3.Prost), cechy (SIFT / AKAZE po CLAHE), dopasowanie do trzech klatek
kluczowych najbliższych pozycji EKF kamery (knn 2 + iloraz + RANSAC podobieństwa). cv2.setNumThreads(1), jeden proces.
Częstość = 1000 / p95(prostowanie + cechy + dopasowanie) — render pomocniczy nie wchodzi do budżetu drona.
Wyjście: results/TEACH_RECON/r7_czas.json.
"""
import gzip
import json
import os
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import teach_r34 as T

R2, R3, NF = T.R2, T.R3, T.NF
LOT, LATA, N, ROZGRZEWKA = "p02_p1_c10_zew", "S", 200, 5


def main():
    cv2.setNumThreads(1)
    kam = R2.Kam(R2.kamera())
    pr = R3.Prost(kam)
    teren = cv2.imread(os.path.join(T.OUT, "dane", f"{LATA}_2024-04-27.png"))
    K = [k for k in json.load(gzip.open(os.path.join(T.OUT, "r2_klatki.json.gz"), "rt")) if k["lot"] == LOT]
    czesc = json.load(gzip.open(os.path.join(T.CZ, f"{LOT}_{LATA}.json.gz"), "rt"))
    kf_t = {x["sim"] for x in czesc["kf"]}
    przed = [k for k in K if k["seria"] == "przed" and round(k["sim"], 3) in kf_t]
    po = sorted([k for k in K if k["seria"] == "po"], key=lambda k: k["sim"])[:N + ROZGRZEWKA]
    D = {rd: T.Dop(rd) for rd in T.RODZAJE}

    def kadr(k):
        C, Rk = kam.poza(np.array(k["gt_p"]), R2.rotm(k["gt_q"]))
        return kam.renderuj(teren, T.PIKSEL_T, C, Rk)[0]

    kf = []
    for k in przed:
        rect, mask, off = pr(kadr(k), k["ekf_q"], k["ekf_pos"])
        kf.append({"cam": np.array([k["ekf_pos"][1], k["ekf_pos"][0]]) + off, **{rd: D[rd].cechy(rect, mask) for rd in T.RODZAJE}})
    t = {"render": [], "prost": []} | {rd: {"cechy": [], "dopasuj": []} for rd in T.RODZAJE}
    for i, k in enumerate(po):
        t0 = time.perf_counter(); fr = kadr(k); t1 = time.perf_counter()
        rect, mask, off = pr(fr, k["ekf_q"], k["ekf_pos"]); t2 = time.perf_counter()
        cam = np.array([k["ekf_pos"][1], k["ekf_pos"][0]]) + off
        bliskie = sorted(range(len(kf)), key=lambda j: np.linalg.norm(kf[j]["cam"] - cam))[:T.N_KAND]
        if i >= ROZGRZEWKA:
            t["render"].append((t1 - t0) * 1e3); t["prost"].append((t2 - t1) * 1e3)
        for rd in T.RODZAJE:
            a = time.perf_counter(); f = D[rd].cechy(rect, mask); b = time.perf_counter()
            for j in bliskie:
                D[rd].dopasuj(f, kf[j][rd])
            c = time.perf_counter()
            if i >= ROZGRZEWKA:
                t[rd]["cechy"].append((b - a) * 1e3); t[rd]["dopasuj"].append((c - b) * 1e3)
    q = lambda v, p: round(float(np.quantile(v, p)), 2)
    wyn = {"lot": LOT, "lata": LATA, "n_klatek": N, "n_kf": len(kf), "watki_cv2": 1, "procesy": 1,
           "render_pomocniczy_ms": {"p50": q(t["render"], .5), "p95": q(t["render"], .95)},
           "prostowanie_ms": {"p50": q(t["prost"], .5), "p95": q(t["prost"], .95)}}
    for rd in T.RODZAJE:
        l = np.array(t["prost"]) + np.array(t[rd]["cechy"]) + np.array(t[rd]["dopasuj"])
        wyn[rd] = {"cechy_ms": {"p50": q(t[rd]["cechy"], .5), "p95": q(t[rd]["cechy"], .95)},
                   "dopasuj_3kf_ms": {"p50": q(t[rd]["dopasuj"], .5), "p95": q(t[rd]["dopasuj"], .95)},
                   "lacznie_bez_renderu_ms": {"p50": q(l, .5), "p95": q(l, .95)}, "czestosc_hz_przy_p95": round(1000 / q(l, .95), 2)}
    json.dump(wyn, open(os.path.join(T.OUT, "r7_czas.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(wyn, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
