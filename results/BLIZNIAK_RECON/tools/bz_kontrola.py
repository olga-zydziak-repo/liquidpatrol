#!/usr/bin/env python3
"""results/BLIZNIAK_RECON/tools/bz_kontrola.py — R3 kontrola Z i K tym samym kodem (PROMPT_BLIZNIAK_S0 §5; 0 bootów).

Próba 20 000 komórek 𝒟 z d ≥ 8 m (rng 303), k = 5 (jak B30), Δ_A. U_k szczeblem E1 (bz_dowod.U, od [−1, 1]²⁰) i E3 (bz_afin.U_af,
przecięte z E1); dla B(W) ≥ 1 brak rozwinięcia od zera + B^k. Ograniczenie ku E3 bez podziału. Obok B30 na tych samych komórkach.
Test: 10⁶ historii (rng 404) wobec pudełek U i ograniczenia ku.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bz_dowod as BD                                    # noqa: E402
import bz_afin as AF                                     # noqa: E402
import bz_petla as BP                                    # noqa: E402
import bz_r3 as R                                        # noqa: E402
import bz_r3e as RE                                      # noqa: E402

OUT = BP.OUT
lo, hi = BD.komorki(8.0, 15.0)
rng = np.random.default_rng(303)
cs = rng.choice(len(lo), 20000, replace=False)
l4, h4 = lo[cs], hi[cs]
D = BD.DELTA_A
wyn = {}
for n in ("Z", "K", "B30"):
    S = BD.Siec(BP.model(n)); k = 5
    U1 = BD.U(S, l4, h4, k, D); U1 = RE.U_zero(S, U1, l4, h4, k, D)
    Ua = AF.U_af(S, l4, h4, k, D); U3 = (np.maximum(Ua[0], U1[0]), np.minimum(Ua[1], U1[1]))
    kb, _ = AF.ku_af(S, l4, h4, D, k)
    r = np.random.default_rng(404)
    wU = wk = 0
    for _ in range(10):
        h, hp, ku, c = R.historie(S, r, 100000, k, D, l4, h4, np.arange(len(cs)))
        wU += int(((h < U3[0][c] - 1e-12) | (h > U3[1][c] + 1e-12)).sum()); wk += int((ku < kb[c] - 1e-12).sum())
    q = lambda a: {"p50": float(np.median(a)), "p99": float(np.percentile(a, 99)), "max": float(a.max()), "min": float(a.min())}
    wyn[n] = {"B_z_wag": S.B_nominal, "k": k, "U_E1_polszer": q(((U1[1] - U1[0]) / 2).max(1)), "U_E3_polszer": q(((U3[1] - U3[0]) / 2).max(1)),
              "ku_E3_bez_podzialu": {"p1": float(np.percentile(kb, 1)), "p50": float(np.median(kb)), "udzial_ge_0_3_d_ge_10": float((kb[l4[:, 0] >= 10] >= 0.3).mean())},
              "test": {"historie": 1000000, "wyjatki_U": wU, "wyjatki_ku": wk}}
    print(n, wyn[n], flush=True)
json.dump(wyn, open(os.path.join(OUT, "r3_kontrola_ZK.json"), "w"), ensure_ascii=False, indent=1)
