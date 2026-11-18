#!/usr/bin/env python3
"""results/PETLA_RECON/tools/pl_szukanie.py — szukanie toru intruza (PROMPT_PETLA_S0 §6–§7; 0 bootów).

Metoda: entropia krzyżowa (CEM) na wektorze 62 parametrów toru (pl_intruz „tor”: kąt i r startu, 30 odcinków po 10 s:
kąt, logit ułamka v_max), rozkład normalny diagonalny, populacja 300, elita 30, 200 iteracji, wygładzanie 0.7, minimalne σ 0.05;
napęd N, szum wektora względnego jak W2 (wspólne liczby losowe w iteracji: ziarno szumu = baza + iteracja).
Cel: R4 (wariant siec) — największe |rel_z − 2| (t ≥ 20 s); R5 (wariant W) — największy dystans prawdziwy (t ≥ 20 s).
Zapis cząstkowy po każdej iteracji: results/PETLA_RECON/szukanie_<cel>.json (historia, najlepszy wektor, jego miary).
Użycie: pl_szukanie.py r4|r5 [--iter N]
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pl_bieg as PB                                     # noqa: E402

POP, ELITA, ITER, ALFA, SMIN = 300, 30, 200, 0.7, 0.05


def main():
    cel = sys.argv[1]
    it_n = int(sys.argv[sys.argv.index("--iter") + 1]) if "--iter" in sys.argv else ITER
    wariant, klucz, baza = ("siec", "max_dz", 500000) if cel == "r4" else ("W", "d_max", 600000)
    rng = np.random.default_rng(baza)
    mu = np.zeros(62); sd = np.ones(62)
    mu[2:32] = rng.uniform(-np.pi, np.pi, 30); sd[0] = np.pi; sd[2:32] = np.pi
    mu[32:62] = 2.0; sd[32:62] = 2.0
    fn = os.path.join(PB.OUT, f"szukanie_{cel}.json")
    hist, naj = [], None
    for it in range(it_n):
        P = mu + sd * rng.standard_normal((POP, 62))
        res = PB.bieg("tor", "N", True, 1.0, wariant=wariant, B=POP, ziarno=baza + it, param=P)
        f = res[klucz]
        o = np.argsort(-f)[:ELITA]
        mu = ALFA * P[o].mean(0) + (1 - ALFA) * mu
        sd = np.maximum(ALFA * P[o].std(0) + (1 - ALFA) * sd, SMIN)
        b = int(o[0])
        if naj is None or f[b] > naj["wartosc"]:
            naj = {"wartosc": float(f[b]), "iteracja": it, "ziarno": baza + it, "indeks": b, "param": P[b].tolist(),
                   "miary": {k: (float(v[b]) if np.ndim(v) else None) for k, v in res.items() if k != "logi"}}
        hist.append({"it": it, "max": float(f.max()), "p90": float(np.percentile(f, 90)), "med": float(np.median(f)),
                     "zdarzenia": int(np.isfinite(res["t_ev"]).sum())})
        json.dump({"cel": cel, "wariant": wariant, "klucz": klucz, "metoda": "CEM pop 300 elita 30 α 0.7", "historia": hist, "najlepszy": naj,
                   "mu": mu.tolist(), "sd": sd.tolist()}, open(fn + ".tmp", "w"))
        os.replace(fn + ".tmp", fn)
        print(it, hist[-1], round(naj["wartosc"], 3), flush=True)


if __name__ == "__main__":
    main()
