#!/usr/bin/env python3
"""results/BLIZNIAK_RECON/tools/bz_jakobian.py — R1: norma max i promień spektralny ∂h′/∂h na stanach z R2 (PROMPT_BLIZNIAK_S0 §3).

Stany: model pętli jak bz_petla (wariant W, te same ziarna), 7 rodzin × 2 v_max × 20 biegów × 90 s, co 20. tick (wejście
znormalizowane i stan przed krokiem). Jakobian analityczny: ∂h′/∂u (bz: σg′Wg + (1−σ)q′Wh + (g−q)σ′Wt, razy tanh′(u)) · Wh^T,
kontrola różnicami skończonymi (1e-6) na 200 stanach. Dla każdego ramienia: norma max (max suma wiersza |J|) i promień spektralny,
p50 / p99 / max.
"""
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bz_petla as BP                                    # noqa: E402
import pl_naped as PN                                    # noqa: E402
import pl_intruz as PI                                   # noqa: E402
from net.dataset import AGE_CAP                          # noqa: E402

OUT = BP.OUT


def stany(m, B=20, T=90.0):
    X, Hs = [], []
    for r, rod in enumerate(PI.RODZINY):
        for j, vm in enumerate((1.0, 0.5)):
            zr = 70000 + 100 * r + j
            rng = np.random.default_rng(zr)
            I = PI.Intruz(rod, B, vm, rng)
            sz = PN.Szum(B, np.random.default_rng(zr + 7919), wl=True)
            S = BP.Ster(m, B)
            p = np.tile([0.0, 0.0, -8.0], (B, 1)); v = np.zeros((B, 3))
            N = BP.NAPED
            bh = [np.zeros((B, 2)) for _ in range(N["kh"] + 1)]; bv = [np.zeros(B) for _ in range(N["kv"] + 1)]
            ah, av = 1 - math.exp(-PN.DT / N["th"]), 1 - math.exp(-PN.DT / N["tv"])
            q = I.pos3()
            for k in range(int(T / PN.DT)):
                rel = q - p + sz.krok()
                x = np.concatenate([rel, v, np.full((B, 1), BP.WIEK), np.ones((B, 1))], 1)
                if k % 20 == 0:
                    xx = x.copy(); xx[:, 6] = np.minimum(xx[:, 6], AGE_CAP)
                    X.append((xx - m.input_mean) / m.input_std); Hs.append(S.h.copy())
                c = S.krok(x)
                c[:, 2] = np.clip(0.5 * (rel[:, 2] - 2.0), -1.0, 1.0)
                bh.append(c[:, :2]); ch = bh.pop(0); bv.append(c[:, 2]); cv = bv.pop(0)
                v[:, :2] += ah * (ch - v[:, :2]); v[:, 2] += av * (cv - v[:, 2])
                p = p + v * PN.DT
                q = I.krok(p)
    return np.concatenate(X), np.concatenate(Hs)


def jac(m, x, h):
    u = np.concatenate([x, h], 1) @ m.Wb + m.bb0
    b = np.tanh(u)
    g = np.tanh(b @ m.Wg + m.bg); q = np.tanh(b @ m.Wh + m.bh); s = 1 / (1 + np.exp(-(b @ m.Wt + m.bt)))
    a1 = s * (1 - g * g); a2 = (1 - s) * (1 - q * q); a3 = (g - q) * s * (1 - s)
    Jb = a1[:, :, None] * m.Wg.T[None] + a2[:, :, None] * m.Wh.T[None] + a3[:, :, None] * m.Wt.T[None]
    return (Jb * (1 - b * b)[:, None, :]) @ m.Wb[8:].T


if __name__ == "__main__":
    wyn = {}
    for n in ("Z", "K", "B90", "B50", "B30", "C3", "C12"):
        m = BP.model(n)
        X, Hs = stany(m)
        J = jac(m, X, Hs)
        e = 1e-6
        i = np.arange(200); kol = np.random.default_rng(5).integers(0, 20, 200)
        dh = np.zeros((200, 20)); dh[i, kol] = e
        f = lambda hh: m.step_np(X[:200], hh)[1]
        fd = (f(Hs[:200] + dh) - f(Hs[:200] - dh)) / (2 * e)
        blad = float(np.abs(fd - J[i, :, kol]).max())
        nmax = np.abs(J).sum(2).max(1); rho = np.abs(np.linalg.eigvals(J)).max(1)
        q_ = lambda a: {"p50": float(np.median(a)), "p99": float(np.percentile(a, 99)), "max": float(a.max())}
        wyn[n] = {"stany": int(len(X)), "norma_max": q_(nmax), "promien_spektralny": q_(rho), "kontrola_roznic_max_blad": blad}
        print(n, wyn[n], flush=True)
    json.dump(wyn, open(os.path.join(OUT, "r1_jakobian.json"), "w"), ensure_ascii=False, indent=1)
