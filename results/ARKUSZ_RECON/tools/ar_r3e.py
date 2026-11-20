#!/usr/bin/env python3
"""results/ARKUSZ_RECON/tools/ar_r3e.py — R3 sufit empiryczny punktu stałego k = 1, wejścia sprzężone (PROMPT_ARKUSZ_S0 §5; 0 bootów).

W odróżnieniu od sufitu w ar_r3_bieg (pary rozprzężone: s ∈ c i s′ ∈ c′ ∩ (c ⊕ Δ) niezależnie — nadzbiór wejść dopuszczalnych)
tu próbki są dokładnie z lematu: s ∈ c, δ ~ U(−Δ, Δ), s′ = s + δ; c′ = komórka s′ (zajęta, rel_z i vd w pudełku), inaczej odrzut.
Postać D2: e ∈ E_c — połowa próbek jednostajnie, połowa w losowych narożnikach pudełka; obraz G = F(x(s′), Φ_c(s) + e) − Φ_c′(s′).
Postać D1: h ∈ Z_c (pudełko stanu), połowa jednostajnie, połowa narożniki; obraz F(x(s′), h).
Iteracja: E_c′ ← obwiednia(E_c′, obrazy); komórka z półszerokością (D1: (hi − lo)/2, D2: max |E|) > CAP zamrożona.
n próbek na komórkę na iterację = 64 (rng 6060 + iteracja), ≤ 15 iteracji.
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


def kom(Dz, s):
    kod = Dz.g.kod(Dz.g.klucze(np.c_[s, np.full(len(s), R.WIEK)]))
    pos = np.minimum(np.searchsorted(Dz.uk, kod), Dz.nc - 1)
    ok = (Dz.uk[pos] == kod) & (s[:, 4] >= Dz.rz[0]) & (s[:, 4] <= Dz.rz[1]) & (s[:, 5] >= Dz.vd[0]) & (s[:, 5] <= Dz.vd[1])
    return pos, ok


def bieg(Dz, poziom, El, Eh, n=64, iters=15):
    w = Dz.ile.astype(float)
    zamr = np.zeros(Dz.nc, bool)
    hist = []
    for it in range(iters):
        rng = np.random.default_rng(6060 + it)
        L = np.full((Dz.nc, 20), np.inf); H = np.full((Dz.nc, 20), -np.inf)
        for st in range(0, Dz.nc, 4000):
            cs = np.repeat(np.arange(st, min(st + 4000, Dz.nc)), n)
            P = len(cs)
            s = Dz.sc[cs] + Dz.w[cs] * rng.uniform(-1, 1, (P, 6))
            sp = s + Dz.delta * rng.uniform(-1, 1, (P, 6)); sp[:, 1] = AW.wrap(sp[:, 1])
            pos, ok = kom(Dz, sp)
            u = rng.uniform(0, 1, (P, 20))
            u = np.where((np.arange(P) % 2 == 1)[:, None], (u > 0.5).astype(float), u)
            e = El[cs] + (Eh[cs] - El[cs]) * u
            xn = AW.norm(AW.cechy(np.c_[sp, np.full(P, R.WIEK)]))
            if poziom == "D1":
                G = AW.F(xn, e)
            else:
                G = AW.F(xn, Dz.Phi(cs, s) + e)
                G[ok] -= Dz.Phi(pos[ok], sp[ok])
            np.minimum.at(L, pos[ok], G[ok]); np.maximum.at(H, pos[ok], G[ok])
        wej = np.isfinite(L[:, 0])
        okc = ~wej | ((L >= El).all(1) & (H <= Eh).all(1))
        nEl = np.where(wej[:, None], np.minimum(El, L), El); nEh = np.where(wej[:, None], np.maximum(Eh, H), Eh)
        pw = (nEh - nEl) / 2 if poziom == "D1" else np.maximum(np.abs(nEl), np.abs(nEh))
        zamr |= (pw > R.CAP).any(1)
        El = np.where(~zamr[:, None], nEl, El); Eh = np.where(~zamr[:, None], nEh, Eh)
        pz = (Eh - El) / 2 if poziom == "D1" else np.maximum(np.abs(El), np.abs(Eh))
        rec = {"iter": it, "stabilne_komorki": float((okc & ~zamr).mean()), "stabilne_czas": float(w[okc & ~zamr].sum() / w.sum()),
               "zamrozone": int(zamr.sum()), "zamrozone_czas": float(w[zamr].sum() / w.sum()),
               "polszer_Z_p50": float(np.median(pz.max(1))), "polszer_Z_p99": float(np.percentile(pz.max(1), 99))}
        hist.append(rec)
        print(poziom, rec, flush=True)
        if (okc | zamr).all():
            break
    return hist, zamr, El, Eh


if __name__ == "__main__":
    import pickle
    Dz = pickle.load(open(sys.argv[1], "rb"))
    ci = Dz.cel_stanu
    def hull(v):
        L = np.full((Dz.nc, 20), np.inf); H = np.full((Dz.nc, 20), -np.inf)
        np.minimum.at(L, ci, v); np.maximum.at(H, ci, v)
        ww = H - L
        return L - 0.1 * ww - 1e-3, H + 0.1 * ww + 1e-3
    wyn = {}
    for p, st in (("D2", hull(Dz.e_dane)), ("D1", hull(Dz.h))):
        a = time.time()
        hist, zamr, El, Eh = bieg(Dz, p, *st)
        wyn[p] = {"historia": hist, "czas_s": time.time() - a}
        np.savez(os.path.join(OUT, f"r3e_{p}.npz"), zamrozone=zamr, El=El, Eh=Eh, ile=Dz.ile)
        json.dump(wyn, open(os.path.join(OUT, "r3e.json"), "w"), ensure_ascii=False, indent=1)
