#!/usr/bin/env python3
"""results/ARKUSZ_RECON/tools/ar_r4.py — R4 prawo na arkuszu (PROMPT_ARKUSZ_S0 §6; 0 bootów).

Komenda ku celowi na zbiorze Z_c = {Φ_c(s) + e : s ∈ c, e ∈ E_c}: y = 3·tanh(Wo^T(Φ_c(s) + e) + bo) — wnętrze afiniczne
w (s, e), więc jego zakres na pudełku jest dokładny (środek ± |Wo^T A_c|·w + |Wo^T|·r_e), tanh monotoniczny; clip_v: dolna
granica ku celowi > 0 mnożona przez min(1, 3/‖y‖_max); ku = y_x cos θ + y_y sin θ, θ w sektorze (iloczyn przedziałów).
Zbiory E_c: (a) dowiedzione na najlepszym szczeblu (r3_<poziom>.npz, maska „dowiedzione”) — R4 w sensie promptu;
(b) WARUNKOWO, bez dowodu lematu: obwiednia danych (+10% + 1e-3) — wszystkie komórki; (c) empirycznie: min ku po stanach danych.
S′(d₀): komórki o górnej krawędzi dystansu > d₀; udział z dolną granicą ku ≥ 0.3 m/s; najmniejsze d₀ (siatka 0.25 m) z ≥ 99%.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ar_wspolne as AW                                  # noqa: E402
import ar_r3 as R                                        # noqa: E402

OUT = AW.OUT


def ku_przedzial(Dz, El, Eh, cel=None):
    cel = np.arange(Dz.nc) if cel is None else cel
    e0, re = (El[cel] + Eh[cel]) / 2, (Eh[cel] - El[cel]) / 2
    Wo = AW.WO                                                  # (20, 3)
    c = (Dz.phi[cel] + e0) @ Wo + AW.BO
    WA = np.einsum("hk,phj->pkj", Wo, Dz.A[cel])                # (P, 3, 6)
    r = np.einsum("pkj,pj->pk", np.abs(WA), Dz.w[cel]) + re @ np.abs(Wo)
    yl, yh = 3 * np.tanh(c - r), 3 * np.tanh(c + r)
    th_l, th_h = Dz.sc[cel, 1] - Dz.w[cel, 1], Dz.sc[cel, 1] + Dz.w[cel, 1]
    cl, ch = R.icos(th_l, th_h); nl, nh = R.isin(th_l, th_h)
    a = R.imul(yl[:, 0], yh[:, 0], cl, ch); b = R.imul(yl[:, 1], yh[:, 1], nl, nh)
    kl, kh = a[0] + b[0], a[1] + b[1]
    nmax = np.sqrt((np.maximum(np.abs(yl), np.abs(yh)) ** 2).sum(1))
    sc = np.minimum(1.0, 3.0 / nmax)
    kl = np.where(kl > 0, kl * sc, kl)
    pw = ((yh - yl) / 2)[:, :2].max(1)
    return kl, kh, pw


def s_prim(Dz, kl, maska):
    gora = Dz.sc[:, 0] + Dz.w[:, 0]
    out = {}
    d0s = np.arange(6.0, 10.51, 0.25)
    for d0 in d0s:
        m = maska & (gora > d0)
        out[f"{d0:.2f}"] = {"komorki": int(m.sum()), "udzial_ku_ge_0_3": float((kl[m] >= 0.3).mean()) if m.any() else None}
    ok = [d0 for d0 in d0s if out[f"{d0:.2f}"]["udzial_ku_ge_0_3"] is not None and out[f"{d0:.2f}"]["udzial_ku_ge_0_3"] >= 0.99]
    # najmniejsze d₀, od którego wszystkie większe też spełniają
    best = None
    for d0 in d0s[::-1]:
        v = out[f"{d0:.2f}"]["udzial_ku_ge_0_3"]
        if v is None or v >= 0.99:
            best = float(d0)
        else:
            break
    return {"tabela": out, "najmniejsze_d0_99proc": best, "d0_9_5": out["9.50"]}


if __name__ == "__main__":
    import pickle
    Dz = pickle.load(open(sys.argv[1], "rb"))
    ci = Dz.cel_stanu
    L = np.full((Dz.nc, 20), np.inf); H = np.full((Dz.nc, 20), -np.inf)
    np.minimum.at(L, ci, Dz.e_dane); np.maximum.at(H, ci, Dz.e_dane)
    w = H - L
    El, Eh = L - 0.1 * w - 1e-3, H + 0.1 * w + 1e-3
    wyn = {}
    # (a) dowiedzione
    najl = json.load(open(os.path.join(OUT, "r3.json"))).get("najlepszy_szczebel")
    dow = None
    for p in ("D3", "D2", "D1"):
        fn = os.path.join(OUT, f"r3_{p}.npz")
        if os.path.exists(fn):
            z = np.load(fn)
            if z["dowiedzione"].any():
                dow = (p, z)
                break
    if dow is None:
        wyn["a_dowiedzione"] = {"komorki_z_dowiedzionym_lematem": 0, "uwaga": "brak komórek z dowiedzionym lematem na żadnym szczeblu — R4 w sensie promptu pusty"}
    else:
        p, z = dow
        kl, kh, pw = ku_przedzial(Dz, z["El"], z["Eh"]) if p != "D1" else (None, None, None)
        m = z["dowiedzione"]
        wyn["a_dowiedzione"] = {"szczebel": p, "komorki": int(m.sum()), "S_prim": s_prim(Dz, kl, m)}
    # (b) warunkowo: obwiednia danych; test poprawności 10⁶ punktów (10⁴ komórek × 100)
    kl, kh, pw = ku_przedzial(Dz, El, Eh)
    rng = np.random.default_rng(4040)
    cs = rng.choice(Dz.nc, 10000, replace=False)
    s = (Dz.sc[cs][:, None] + Dz.w[cs][:, None] * rng.uniform(-1, 1, (10000, 100, 6))).reshape(-1, 6)
    e = (El[cs][:, None] + (Eh[cs] - El[cs])[:, None] * rng.uniform(0, 1, (10000, 100, 20))).reshape(-1, 20)
    cc = np.repeat(cs, 100)
    hh = Dz.Phi(cc, s) + e
    kk = AW.ku_celowi(AW.komenda(hh), AW.cechy(np.c_[s, np.full(len(s), R.WIEK)]))
    wyj = int(((kk < kl[cc] - 1e-12) | (kk > kh[cc] + 1e-12)).sum())
    wyn["test_poprawnosci_ku"] = {"punkty": int(len(kk)), "wyjatki": wyj, "zdany": wyj == 0}
    wsz = np.ones(Dz.nc, bool)
    wyn["b_warunkowo_obwiednia_danych"] = {"polszer_komendy": {"p50": float(np.median(pw)), "p99": float(np.percentile(pw, 99)), "max": float(pw.max())},
                                           "S_prim": s_prim(Dz, kl, wsz),
                                           "S_prim_komorki_ge8": s_prim(Dz, kl, Dz.ile >= 8)}
    # (c) empirycznie: min ku po stanach
    xs = AW.cechy(np.c_[Dz.s, np.full(len(Dz.s), R.WIEK)])
    ku = AW.ku_celowi(AW.komenda(Dz.h), xs)
    kmin = np.full(Dz.nc, np.inf); np.minimum.at(kmin, ci, ku)
    wyn["c_empirycznie_min_po_stanach"] = {"S_prim": s_prim(Dz, kmin, wsz), "ku_min_d_ge_9_5": float(ku[Dz.s[:, 0] >= 9.5].min()),
                                           "ku_p01_d_ge_9_5": float(np.percentile(ku[Dz.s[:, 0] >= 9.5], 1)), "n_d_ge_9_5": int((Dz.s[:, 0] >= 9.5).sum())}
    json.dump(wyn, open(os.path.join(OUT, "r4.json"), "w"), ensure_ascii=False, indent=1)
    np.savez(os.path.join(OUT, "r4_wektory.npz"), ku_lo_obwiednia=kl, ku_hi_obwiednia=kh, polszer_komendy=pw, ku_min_dane=kmin, ile=Dz.ile)
    print(json.dumps(wyn, ensure_ascii=False)[:3000])
