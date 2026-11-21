#!/usr/bin/env python3
"""results/BLIZNIAK_RECON/tools/bz_kontr.py — R4 kontrprzykłady do S(0.3, 10 m) (PROMPT_BLIZNIAK_S0 §6; 0 bootów).

Użycie: bz_kontr.py <ramię> <A|B>
Historia długości L ∈ {k, 2k, 60} w 𝒞 na 𝒟: s_0 losowe w 𝒟 (d 4–15, θ, (v_r, v_t) w kole 3.2), s_{j+1} = s_j + δ_j,
|δ_j| ≤ Δ per współrzędna (d, θ, v_r, v_t), (rel_z, vd, wiek) w przedziałach co tick; stan początkowy dowolny (U(−1, 1)²⁰
albo wybrany przez szukanie). Historia wychodząca z 𝒟 — odrzucona (karą w szukaniu kierowanym).
Kontrprzykład: d(końcowe, z cech) ≥ 10.0 m i składowa komendy ku celowi (po clip_v) < 0.3 m/s.
Strategie (rng 7000 + …): losowe δ ~ U(±Δ) (10⁶ historii na L); stałe pchnięcie δ = σ ⊙ Δ (σ ∈ {−1, 1}⁴ losowe, stałe w historii;
10⁶) i ±Δ/2 (10⁶); kierowane — 4000 łańcuchów × 400 iteracji wspinaczki: perturbacja gaussowska parametrów (s_0, δ, rel_z/vd/wiek,
h_0), akceptacja przy spadku celu ku_końcowe + 10·max(0, 10 − d_końcowe) + kara za wyjście z 𝒟.
"""
import json
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bz_dowod as BD                                    # noqa: E402
import bz_petla as BP                                    # noqa: E402
import bz_r3e as RE                                      # noqa: E402

OUT = "/home/olga/projects/liquidpatrol/results/BLIZNIAK_RECON"
DOM = BD.DOM


def symuluj(S, s0, dl, ext, h0):
    """s0 (N,4), dl (N,L,4) przyrosty, ext (N,L+1,3) w [0,1] → (rel_z, vd, wiek), h0 (N,20). Zwraca ku, d końcowe, poza𝒟."""
    N, L, _ = dl.shape
    s = s0.copy(); h = h0
    poza = np.zeros(N, bool)
    lo3 = np.array([DOM["rz"][0], DOM["vd"][0], DOM["wiek"][0]]); hi3 = np.array([DOM["rz"][1], DOM["vd"][1], DOM["wiek"][1]])
    for j in range(L + 1):
        if j > 0:
            s = s + dl[:, j - 1]
            s[:, 1] = (s[:, 1] + math.pi) % (2 * math.pi) - math.pi
        poza |= (s[:, 0] < DOM["d"][0]) | (s[:, 0] > DOM["d"][1]) | (np.hypot(s[:, 2], s[:, 3]) > DOM["v"])
        e = lo3 + (hi3 - lo3) * ext[:, j]
        x = np.stack([s[:, 0] * np.cos(s[:, 1]), s[:, 0] * np.sin(s[:, 1]), e[:, 0],
                      s[:, 2] * np.cos(s[:, 1]) - s[:, 3] * np.sin(s[:, 1]), s[:, 2] * np.sin(s[:, 1]) + s[:, 3] * np.cos(s[:, 1]),
                      e[:, 1], e[:, 2], np.ones(N)], 1)
        xn = (x - S.mean) / S.std
        hprev = h
        h = S.F(xn, h)
    ku = S.ku(xn, hprev, s[:, 1])
    return ku, s[:, 0], poza


def losuj_s0(rng, N):
    r = 3.2 * np.sqrt(rng.uniform(0, 1, N)); a = rng.uniform(-math.pi, math.pi, N)
    return np.stack([rng.uniform(4, 15, N), rng.uniform(-math.pi, math.pi, N), r * np.cos(a), r * np.sin(a)], 1)


def strategia(S, D, L, nazwa, rng, N=1_000_000, B=100_000):
    wyn = {"historie": 0, "dopuszczalne_d_ge_10": 0, "kontrprzyklady": 0, "min_ku_d_ge_10": np.inf, "min_ku_d_ge_9_5": np.inf}
    for _ in range(N // B):
        s0 = losuj_s0(rng, B)
        if nazwa == "losowe":
            dl = rng.uniform(-1, 1, (B, L, 4)) * D
        else:
            f = 1.0 if nazwa == "pchniecie" else 0.5
            dl = np.repeat((f * D * rng.choice([-1.0, 1.0], (B, 4)))[:, None], L, 1)
        ext = rng.uniform(0, 1, (B, L + 1, 3)); h0 = rng.uniform(-1, 1, (B, 20))
        ku, d, poza = symuluj(S, s0, dl, ext, h0)
        ok = ~poza
        wyn["historie"] += B
        m10 = ok & (d >= 10.0); m95 = ok & (d >= 9.5)
        wyn["dopuszczalne_d_ge_10"] += int(m10.sum())
        wyn["kontrprzyklady"] += int((m10 & (ku < 0.3)).sum())
        if m10.any():
            wyn["min_ku_d_ge_10"] = min(wyn["min_ku_d_ge_10"], float(ku[m10].min()))
        if m95.any():
            wyn["min_ku_d_ge_9_5"] = min(wyn["min_ku_d_ge_9_5"], float(ku[m95].min()))
    return wyn


def kierowane(S, D, L, rng, N=4000, iters=400):
    s0 = losuj_s0(rng, N); s0[:, 0] = rng.uniform(10, 15, N)
    dl = rng.uniform(-1, 1, (N, L, 4)) * D
    ext = rng.uniform(0, 1, (N, L + 1, 3)); h0 = rng.uniform(-1, 1, (N, 20))

    def cel(s0, dl, ext, h0):
        ku, d, poza = symuluj(S, s0, dl, ext, h0)
        return ku + 10 * np.maximum(0, 10.0 - d) + 100 * poza, ku, d, poza
    f, ku, d, poza = cel(s0, dl, ext, h0)
    for it in range(iters):
        sc = 0.3 * (1 - it / iters) + 0.02
        n0 = s0 + rng.normal(0, 1, s0.shape) * sc * np.array([0.5, 0.2, 0.5, 0.5])
        n1 = np.clip(dl + rng.normal(0, 1, dl.shape) * sc * D, -D, D)
        n2 = np.clip(ext + rng.normal(0, 1, ext.shape) * sc, 0, 1)
        n3 = np.clip(h0 + rng.normal(0, 1, h0.shape) * sc, -1, 1)
        fn, kn, dn, pn = cel(n0, n1, n2, n3)
        lep = fn < f
        s0[lep], dl[lep], ext[lep], h0[lep] = n0[lep], n1[lep], n2[lep], n3[lep]
        f[lep], ku[lep], d[lep], poza[lep] = fn[lep], kn[lep], dn[lep], pn[lep]
    m10 = ~poza & (d >= 10.0)
    i = int(np.argmin(np.where(m10, ku, np.inf))) if m10.any() else None
    return {"lancuchy": N, "iteracje": iters, "dopuszczalne_d_ge_10": int(m10.sum()), "kontrprzyklady": int((m10 & (ku < 0.3)).sum()),
            "min_ku_d_ge_10": float(ku[m10].min()) if m10.any() else None,
            "najgorszy": {"s0": s0[i].tolist(), "d_konc": float(d[i]), "ku": float(ku[i])} if i is not None else None}


def main(ramie, w):
    t0 = time.time()
    S = BD.Siec(BP.model(ramie))
    k = RE.k_ramienia(S)
    D = RE.delta(w)
    wyn = {"ramie": ramie, "delta": w, "k": k}
    for L in (k, 2 * k, 60):
        rng = np.random.default_rng(7000 + L)
        for nm in ("losowe", "pchniecie", "pchniecie_pol"):
            wyn[f"L{L}_{nm}"] = strategia(S, D, L, nm, rng)
            print(ramie, w, L, nm, wyn[f"L{L}_{nm}"], flush=True)
        wyn[f"L{L}_kierowane"] = kierowane(S, D, L, rng)
        print(ramie, w, L, "kierowane", wyn[f"L{L}_kierowane"], flush=True)
        json.dump(wyn, open(os.path.join(OUT, f"r4_kontr_{ramie}_{w}.json"), "w"), ensure_ascii=False, indent=1)
    wyn["kontrprzyklady_razem"] = sum(v["kontrprzyklady"] for kk, v in wyn.items() if isinstance(v, dict) and "kontrprzyklady" in v)
    wyn["czas_s"] = time.time() - t0
    json.dump(wyn, open(os.path.join(OUT, f"r4_kontr_{ramie}_{w}.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
