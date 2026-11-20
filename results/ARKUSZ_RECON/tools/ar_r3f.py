#!/usr/bin/env python3
"""results/ARKUSZ_RECON/tools/ar_r3f.py — R3 sufit: kontrprzykłady lematu arkusza (PROMPT_ARKUSZ_S0 §5; 0 bootów).

Start: stan prawdziwy h_t z biegi_W.npz (więc h_t ∈ Z_c dla każdej postaci Z zawierającej dane), sytuacja s_t (komórka c).
Ciąg k wejść dopuszczalnych (dokładnie wg lematu): s_j = s_{j−1} + δ_j, |δ_j| ≤ Δ per współrzędna (Δ = 1.2 × max zmiana na tick,
ar_r3.Dziedzina), każde s_j w komórce zajętej (d, θ, vr, vt) i rel_z, vd w pudełku globalnym; ciąg niespełniający — odrzucony.
Strategie δ (rng 8080 + k):
  dane     — rzeczywiste kolejne wejścia biegu (odniesienie);
  losowe   — δ_j ~ U(−Δ, Δ) niezależnie co krok;
  pchniecie — δ_j = m ⊙ σ ⊙ Δ stałe w ciągu, σ losowe ±1, m losowa maska (każda współrzędna z p = 0.5);
  pchniecie_pol — jak pchniecie, ale 0.5·Δ.
Miary po k krokach (c′ = komórka s_k): reszta wobec arkusza r = h_k − Φ_c′(s_k) (postać D2/D3: kontrprzykład dla każdego Z_c′
o odległości od arkusza ≤ CAP, gdy max|r| > CAP); postać D1: brak pudełka o półszerokości ≤ CAP zawierającego stany danych c′ i h_k
(h_k poza [max_dane − 2·CAP, min_dane + 2·CAP] w którymś neuronie). Udziały: po startach (czas) i po komórkach c′ (komórka z ≥ 1
kontrprzykładem ma lemat fałszywy; udział czasu pobytu w takich komórkach = górne ograniczenie każdego szczebla).
"""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ar_wspolne as AW                                  # noqa: E402
import ar_r3 as R                                        # noqa: E402

OUT = AW.OUT
CAP = R.CAP


def main(Dz, N=200_000, ks=(1, 10, 20)):
    z = np.load(os.path.join(OUT, "biegi_W.npz"))
    X, Hh = z["x"], z["h"]
    nb, nt = X.shape[:2]
    ci_all = Dz.cel_stanu
    hlo = np.full((Dz.nc, 20), np.inf); hhi = np.full((Dz.nc, 20), -np.inf)
    np.minimum.at(hlo, ci_all, Dz.h); np.maximum.at(hhi, ci_all, Dz.h)
    D = Dz.delta
    lo_g = np.array([Dz.rz[0], Dz.vd[0]]); hi_g = np.array([Dz.rz[1], Dz.vd[1]])
    wyn, wek = {"N_startow": N, "delta": D.tolist(), "CAP": CAP}, {}
    w_cel = Dz.ile.astype(float)

    def kom(s):
        kod = Dz.g.kod(Dz.g.klucze(np.c_[s, np.full(len(s), R.WIEK)]))
        pos = np.minimum(np.searchsorted(Dz.uk, kod), Dz.nc - 1)
        ok = (Dz.uk[pos] == kod) & (s[:, 4] >= lo_g[0]) & (s[:, 4] <= hi_g[0]) & (s[:, 5] >= lo_g[1]) & (s[:, 5] <= hi_g[1])
        return pos, ok

    for k in ks:
        rng = np.random.default_rng(8080 + k)
        bi = rng.integers(0, nb, N); ti = rng.integers(0, nt - k - 1, N)
        s0 = AW.sytuacja(X[bi, ti])[:, :6]
        wek[f"k{k}_bi"], wek[f"k{k}_ti"] = bi, ti
        for strat in ("dane", "losowe", "pchniecie", "pchniecie_pol"):
            a = time.time()
            h = Hh[bi, ti].copy(); s = s0.copy()
            ok = np.ones(N, bool)
            if strat.startswith("pchniecie"):
                f = 0.5 if strat.endswith("pol") else 1.0
                dstale = f * D * rng.choice([-1.0, 1.0], (N, 6)) * (rng.uniform(0, 1, (N, 6)) < 0.5)
            for j in range(1, k + 1):
                if strat == "dane":
                    s = AW.sytuacja(X[bi, ti + j])[:, :6]
                else:
                    dl = rng.uniform(-1, 1, (N, 6)) * D if strat == "losowe" else dstale
                    s = s + dl; s[:, 1] = AW.wrap(s[:, 1])
                pos, okj = kom(s)
                ok &= okj
                h = AW.F(AW.norm(AW.cechy(np.c_[s, np.full(N, R.WIEK)])), h)
            pos, okk = kom(s)
            ok &= okk
            r = np.full(N, np.nan); kD1 = np.zeros(N, bool)
            r[ok] = np.abs(h[ok] - Dz.Phi(pos[ok], s[ok])).max(1)
            kD1[ok] = ((h[ok] > hlo[pos[ok]] + 2 * CAP) | (h[ok] < hhi[pos[ok]] - 2 * CAP)).any(1)
            kD2 = ok & (np.nan_to_num(r) > CAP)
            o = {"dopuszczalne": int(ok.sum()), "udzial_dopuszczalnych": float(ok.mean()),
                 "reszta_od_arkusza": {"p50": float(np.nanmedian(r)), "p99": float(np.nanpercentile(r, 99)), "max": float(np.nanmax(r))},
                 "kontrprzyklady_D2D3": int(kD2.sum()), "udzial_kontr_D2D3_wsrod_dopuszczalnych": float(kD2.sum() / max(ok.sum(), 1)),
                 "kontrprzyklady_D1": int(kD1.sum()), "udzial_kontr_D1_wsrod_dopuszczalnych": float(kD1.sum() / max(ok.sum(), 1))}
            for nm, kk in (("D2D3", kD2), ("D1", kD1)):
                fals = np.zeros(Dz.nc, bool); fals[pos[kk]] = True
                o[f"komorki_falsyfikowane_{nm}"] = int(fals.sum())
                o[f"czas_pobytu_w_falsyfikowanych_{nm}"] = float(w_cel[fals].sum() / w_cel.sum())
                wek[f"k{k}_{strat}_fals_{nm}"] = fals
            o["czas_s"] = time.time() - a
            wyn[f"k{k}_{strat}"] = o
            wek[f"k{k}_{strat}_reszta"] = r.astype(np.float32); wek[f"k{k}_{strat}_cel"] = np.where(ok, pos, -1)
            print(k, strat, o, flush=True)
            json.dump(wyn, open(os.path.join(OUT, "r3f.json"), "w"), ensure_ascii=False, indent=1)
    
    np.savez(os.path.join(OUT, "r3f_wektory.npz"), **wek)


if __name__ == "__main__":
    Dz = R.Dziedzina()
    main(Dz)
