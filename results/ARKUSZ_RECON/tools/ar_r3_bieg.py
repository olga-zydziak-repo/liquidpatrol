#!/usr/bin/env python3
"""results/ARKUSZ_RECON/tools/ar_r3_bieg.py — przebieg R3 k = 1 na wszystkich parach (PROMPT_ARKUSZ_S0 §5; 0 bootów).

Procesy: 4 × wątki 2 (budżet ≤ 8). Kolejno: dziedzina (ar_r3.Dziedzina + baza T_c), zbiory startowe (obwiednia danych +10% + 1e-3),
testy poprawności D1/D2/D3 (10⁴ par × 100 punktów, rng 2024), punkty stałe D1/D2/D3 (≤ 6 iteracji), sufit empiryczny dla postaci
D1/D2/D3 (4 punkty losowe na parę i iterację, rng 99, ≤ 6 iteracji). Zapis cząstkowy r3.json po każdym punkcie,
wektory r3_<poziom>.npz (dowiedzione, zamrożone, półszerokości per komórka, czas pobytu = liczba stanów).
"""
import json
import os
import sys
import time
from multiprocessing import Pool

os.environ.setdefault("OMP_NUM_THREADS", "2")
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ar_r3 as R                                        # noqa: E402

OUT = R.OUT
FN = os.path.join(OUT, "r3.json")
NPROC = int(os.environ.get("NPROC", "4"))
DZ = None
STAN = {}


def hull(ci, v, nc):
    L = np.full((nc, 20), np.inf); H = np.full((nc, 20), -np.inf)
    np.minimum.at(L, ci, v); np.maximum.at(H, ci, v)
    w = H - L
    return L - 0.1 * w - 1e-3, H + 0.1 * w + 1e-3


def _praca(arg):
    poziom, emp, st, en, it = arg
    El, Eh = STAN["El"], STAN["Eh"]
    T = DZ.T if poziom == "D3" else None
    Ti = DZ.Ti if poziom == "D3" else None
    rng = np.random.default_rng(99 + 1000 * it + st)
    L = np.full((DZ.nc, 20), np.inf); H = np.full((DZ.nc, 20), -np.inf)
    for a in range(st, en, 10000):
        idx = np.arange(a, min(a + 10000, en))
        if emp:
            G = R.probki(DZ, idx, El, Eh, rng, 4, T, Ti, poziom)
            lo, hi = G.min(1), G.max(1)
        elif poziom == "D1":
            lo, hi = R.obraz_D1(DZ, idx, El, Eh)
        else:
            lo, hi, _ = R.obraz_D23(DZ, idx, El, Eh, T, Ti)
        np.minimum.at(L, DZ.pd[idx], lo); np.maximum.at(H, DZ.pd[idx], hi)
    return L, H


def punkt_staly(poziom, El0, Eh0, emp, iters=6):
    global STAN
    scale = np.abs(DZ.T).sum(2) if poziom == "D3" else np.ones((DZ.nc, 20))
    El, Eh = El0.copy(), Eh0.copy()
    zamr = np.zeros(DZ.nc, bool)
    w = DZ.ile.astype(float)
    hist = []
    t0 = time.time()
    nP = len(DZ.pc)
    gr = np.linspace(0, nP, 4 * NPROC + 1).astype(int)
    for it in range(iters):
        STAN = {"El": El, "Eh": Eh}
        with Pool(NPROC) as pool:
            res = pool.map(_praca, [(poziom, emp, gr[i], gr[i + 1], it) for i in range(len(gr) - 1)])
        L = np.min([r[0] for r in res], 0); H = np.max([r[1] for r in res], 0)
        wej = np.isfinite(L[:, 0])
        ok = ~wej | ((L >= El).all(1) & (H <= Eh).all(1))
        nEl = np.where(wej[:, None], np.minimum(El, L), El); nEh = np.where(wej[:, None], np.maximum(Eh, H), Eh)
        pw = (nEh - nEl) / 2 if poziom == "D1" else scale * np.maximum(np.abs(nEl), np.abs(nEh))
        zamr |= (pw > R.CAP).any(1)
        dow = ok & ~zamr
        upd = ~zamr
        El = np.where(upd[:, None], nEl, El); Eh = np.where(upd[:, None], nEh, Eh)
        # półszerokość obrazu (do raportu) w jednostkach stanu
        pwo = (H - L) / 2 if poziom == "D1" else scale * np.maximum(np.abs(L), np.abs(H))
        rec = {"iter": it, "dowiedzione_komorki": float(dow.mean()), "dowiedzione_czas": float(w[dow].sum() / w.sum()),
               "zamrozone": int(zamr.sum()), "zamrozone_czas": float(w[zamr].sum() / w.sum()),
               "polszer_obrazu_stan_p50": float(np.median(pwo[wej].max(1))), "polszer_obrazu_stan_max": float(pwo[wej].max()),
               "czas_s": time.time() - t0}
        hist.append(rec)
        print(poziom, "emp" if emp else "dow", rec, flush=True)
        if (ok | zamr).all():
            break
    pz = (Eh - El) / 2 if poziom == "D1" else scale * np.maximum(np.abs(El), np.abs(Eh))
    return {"historia": hist, "operacje_par": int(nP * len(hist)), "czas_s": time.time() - t0,
            "polszer_Z_koncowa_stan": {"p50": float(np.median(pz.max(1))), "p99": float(np.percentile(pz.max(1), 99)), "max": float(pz.max())}}, \
        {"dowiedzione": dow, "zamrozone": zamr, "El": El, "Eh": Eh}


def test(poziom, El, Eh, rng, n_par=10000, n_pkt=100):
    T = DZ.T if poziom == "D3" else None
    Ti = DZ.Ti if poziom == "D3" else None
    idx = np.sort(rng.choice(len(DZ.pc), n_par, replace=False))
    wyj = 0; marg = []
    for a in range(0, n_par, 1000):
        ii = idx[a:a + 1000]
        if poziom == "D1":
            lo, hi = R.obraz_D1(DZ, ii, El, Eh)
        else:
            lo, hi, _ = R.obraz_D23(DZ, ii, El, Eh, T, Ti)
        G = R.probki(DZ, ii, El, Eh, rng, n_pkt, T, Ti, poziom)
        wyj += int(((G < lo[:, None]) | (G > hi[:, None])).sum())
        marg.append(np.minimum(G - lo[:, None], hi[:, None] - G).min((1, 2)))
    marg = np.concatenate(marg)
    return {"punkty": n_par * n_pkt, "pary": n_par, "wyjatki_wspolrzednych": wyj, "zdany": wyj == 0,
            "najmniejszy_zapas": float(marg.min())}


def zapisz(wyn):
    json.dump(wyn, open(FN, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    wyn = json.load(open(FN)) if os.path.exists(FN) else {}
    a = time.time()
    DZ = R.Dziedzina(); DZ.baza()
    ci = DZ.cel_stanu
    st = {"D1": hull(ci, DZ.h, DZ.nc), "D2": hull(ci, DZ.e_dane, DZ.nc),
          "D3": hull(ci, np.einsum("phj,pj->ph", DZ.Ti[ci], DZ.e_dane), DZ.nc)}
    wyn["dziedzina"] = {"komorki": int(DZ.nc), "pary": int(len(DZ.pc)), "delta_x1_2": DZ.delta.tolist(),
                        "rel_z": list(map(float, DZ.rz)), "vd": list(map(float, DZ.vd)), "komorki_ge8": int((DZ.ile >= 8).sum()),
                        "rho_srodek": {"p50": float(np.median(DZ.rho)), "p99": float(np.percentile(DZ.rho, 99)), "max": float(DZ.rho.max()),
                                       "udzial_ge1": float((DZ.rho >= 1).mean())},
                        "cond_T": {"p50": float(np.median(np.linalg.cond(DZ.T))), "max": float(np.linalg.cond(DZ.T).max())},
                        "czas_s": time.time() - a}
    del DZ.s, DZ.h, DZ.e_dane
    zapisz(wyn)
    rng = np.random.default_rng(2024)
    poz = sys.argv[1:] or ["D1", "D2", "D3"]
    for p in poz:
        wyn.setdefault("testy", {})[p + "_start"] = test(p, *st[p], rng)
        print("test", p, wyn["testy"][p + "_start"], flush=True); zapisz(wyn)
        o, wk = punkt_staly(p, *st[p], emp=False)
        wyn.setdefault("k1", {})[p] = o
        wyn["testy"][p + "_koniec"] = test(p, wk["El"], wk["Eh"], rng)
        np.savez(os.path.join(OUT, f"r3_{p}.npz"), ile=DZ.ile, klucze=DZ.k, **wk)
        zapisz(wyn)
        o, wk = punkt_staly(p, *st[p], emp=True)
        wyn.setdefault("sufit_empiryczny_k1", {})[p] = o
        np.savez(os.path.join(OUT, f"r3_{p}_emp.npz"), ile=DZ.ile, **wk)
        zapisz(wyn)
