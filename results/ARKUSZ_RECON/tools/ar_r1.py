#!/usr/bin/env python3
"""results/ARKUSZ_RECON/tools/ar_r1.py — R1 arkusz (PROMPT_ARKUSZ_S0 §3; 0 bootów).

R1.1 loty: mapa uczona na 10 lotach, test p03/p07/p09/p12/p13; wariancja niewyjaśniona per neuron (Σ reszta² / Σ (h − h̄_test)²),
reszta |h − Φ| per wpis i w normie max per tick, błąd komendy poziomej |c_xy(Φ) − c_xy|; odniesienie: jedna mapa afiniczna
globalna (bez siatki) i stała (średnia). Historia: regresory sytuacji sprzed 10 i 20 ticków (ten sam lot, ticki ciągłe) — na tym
samym podzbiorze z i bez historii.
R1.2 model W / R1.4 model „siec”: mapa na biegach parzystych, test na nieparzystych; statystyki komórek (wszystkie stany):
liczba zajętych, z ≥ 8 stanami i ich udział stanów, półszerokość pudełka = max po neuronach (max − min)/2 w komórce.
R1.3 PCA lokalne: komórki z ≥ 30 stanami, liczba składowych niosących 99% wariancji stanu (surowego i reszty mapy).
R1.5 z wag: stan z ostatnich 160 kroków wejścia od zera / od losowego U(−1, 1)^20 (rng 777) i punkt stały przy zamrożonym wejściu
(500 iteracji od stanu faktycznego) — różnica w normie max wobec stanu faktycznego.
"""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ar_wspolne as AW                                  # noqa: E402

OUT = AW.OUT
W8 = 160


def q(a, ps=(50, 99, 99.9)):
    a = np.asarray(a, float)
    d = {f"p{p:g}": float(np.percentile(a, p)) for p in ps}
    d["max"] = float(a.max()); d["n"] = int(a.size)
    return d


def var_unexpl(h, hp):
    return ((h - hp) ** 2).sum(0) / ((h - h.mean(0)) ** 2).sum(0)


def global_affine(s_tr, h_tr, s_te):
    sr = np.array([5.0, 0.0, 0.0, 0.0])
    R = AW.regresory(s_tr, sr); R[:, 2] = 0
    Rt = AW.regresory(s_te, sr); Rt[:, 2] = 0
    R = np.c_[R, np.cos(s_tr[:, 1]), np.sin(s_tr[:, 1])]; Rt = np.c_[Rt, np.cos(s_te[:, 1]), np.sin(s_te[:, 1])]
    return Rt @ AW._fit(R, h_tr)


def ocena(siatka, s_tr, h_tr, s_te, h_te, c_te=None, x_te=None, kol=()):
    mp = AW.Mapa(siatka, s_tr, h_tr, kol)
    hp, rr = mp.przewiduj(s_te)
    ok = ~np.isnan(hp[:, 0])
    vu = var_unexpl(h_te[ok], hp[ok])
    res = np.abs(h_te[ok] - hp[ok])
    o = {"pokrycie": float(ok.mean()), "promien_sasiedztwa": {str(r): int((rr[ok] == r).sum()) for r in (1, 2, 3)},
         "war_niewyj_mediana": float(np.median(vu)), "war_niewyj_max": float(vu.max()), "war_niewyj_per_neuron": vu.tolist(),
         "reszta_wpis": q(res), "reszta_max_tick": q(res.max(1)), "rozrzut_neuronu_std_mediana": float(np.median(h_te.std(0))),
         "n_komorek_mapy": int(len(mp.uk))}
    wek = {"reszta": (h_te - hp).astype(np.float32)}
    if c_te is not None:
        cp = AW.komenda(hp[ok])
        e = np.hypot(*(cp[:, :2] - c_te[ok][:, :2]).T)
        o["blad_komendy_poziom"] = q(e)
        ef = np.full(len(ok), np.nan); ef[ok] = e
        wek["blad_komendy"] = ef
    return o, wek, mp


def staty_komorek(siatka, s, h):
    k = siatka.klucze(s); kod = siatka.kod(k)
    o = np.argsort(kod, kind="stable"); kod, hs = kod[o], h[o]
    uk, st, ile = np.unique(kod, return_index=True, return_counts=True)
    mx = np.maximum.reduceat(hs, st, 0); mn = np.minimum.reduceat(hs, st, 0)
    pw = ((mx - mn) / 2).max(1)
    m8 = ile >= 8
    return {"zajete": int(len(uk)), "z_ge8": int(m8.sum()), "udzial_stanow_ge8": float(ile[m8].sum() / ile.sum()),
            "polszer_ge8": q(pw[m8]), "pofaldowane_gt025_ge8": int((pw[m8] > 0.25).sum()),
            "pofaldowane_gt025_wszystkie": int((pw > 0.25).sum()), "udzial_pofaldowanych_ge8": float((pw[m8] > 0.25).mean())}, pw, ile


def pca(siatka, s, h, mp=None):
    k = siatka.klucze(s); kod = siatka.kod(k)
    o = np.argsort(kod, kind="stable")
    uk, st, ile = np.unique(kod[o], return_index=True, return_counts=True)
    nk_raw, nk_res, wag = [], [], []
    for i in np.where(ile >= 30)[0]:
        idx = o[st[i]:st[i] + ile[i]]
        X = h[idx] - h[idx].mean(0)
        ev = np.sort(np.linalg.eigvalsh(X.T @ X))[::-1]
        nk_raw.append(int(np.searchsorted(np.cumsum(ev) / ev.sum(), 0.99) + 1))
        if mp is not None:
            hp, _ = mp.przewiduj(s[idx])
            Xr = h[idx] - hp; Xr -= Xr.mean(0)
            evr = np.sort(np.linalg.eigvalsh(Xr.T @ Xr))[::-1]
            nk_res.append(int(np.searchsorted(np.cumsum(evr) / evr.sum(), 0.99) + 1))
        wag.append(ile[i])
    nk_raw, wag = np.array(nk_raw), np.array(wag)
    o = {"komorek_ge30": int(len(nk_raw)), "kierunki_99_mediana": float(np.median(nk_raw)), "kierunki_99_max": int(nk_raw.max()),
         "kierunki_99_wazone_stanami_mediana": float(np.median(np.repeat(nk_raw, wag))),
         "rozklad": {str(v): int((nk_raw == v).sum()) for v in np.unique(nk_raw)}}
    if nk_res:
        nr = np.array(nk_res)
        o["reszta_kierunki_99_mediana"] = float(np.median(nr)); o["reszta_rozklad"] = {str(v): int((nr == v).sum()) for v in np.unique(nr)}
    return o, nk_raw


def r1_loty(wyn):
    z = np.load(os.path.join(OUT, "loty.npz"), allow_pickle=True)
    nazwy = [str(n)[:3] for n in z["nazwy"]]
    te = np.isin(np.array(nazwy)[z["lot"]], ("p03", "p07", "p09", "p12", "p13"))
    s = AW.sytuacja(z["x"]); h = z["h"]; c = z["c"]
    out, wek = {}, {}
    for nm, g in (("siatka", AW.Siatka()), ("siatka_x2", AW.Siatka(0.125, 128, 0.125))):
        o, w, mp = ocena(g, s[~te], h[~te], s[te], h[te], c[te])
        out[nm] = o
        wek.update({f"{nm}_{k}": v for k, v in w.items()})
    hg = global_affine(s[~te], h[~te], s[te])
    out["odniesienie_globalna_afiniczna"] = {"war_niewyj_mediana": float(np.median(var_unexpl(h[te], hg))),
                                             "reszta_wpis": q(np.abs(h[te] - hg))}
    out["odniesienie_stala"] = {"war_niewyj_mediana": 1.0, "rozrzut_neuronu_std": q(h[te].std(0))}
    # historia: regresory sytuacji sprzed 10 i 20 ticków (ten sam lot, tick − 10/−20 obecny)
    klucz = z["lot"].astype(np.int64) * 10 ** 7 + z["tick"].astype(np.int64)
    pos = {int(k): i for i, k in enumerate(klucz)}
    i10 = np.array([pos.get(int(k) - 10, -1) for k in klucz]); i20 = np.array([pos.get(int(k) - 20, -1) for k in klucz])
    mh = (i10 >= 0) & (i20 >= 0)
    sH = np.c_[s, s[i10], s[i20]]
    g = AW.Siatka()
    # z historią: mapa na sytuacji bieżącej + reszta regresowana liniowo na [s(t−0.5), s(t−1)] − s(t) w komórce globalnie
    o0, _, mp0 = ocena(g, s[~te & mh], h[~te & mh], s[te & mh], h[te & mh])
    hp_tr, _ = mp0.przewiduj(s[~te & mh]); hp_te, _ = mp0.przewiduj(s[te & mh])
    def hist(sx, i1, i2):
        dd = np.c_[sx[i1] - sx, sx[i2] - sx]
        dd[:, [1, 8]] = AW.wrap(dd[:, [1, 8]])
        return np.c_[np.ones(len(dd)), dd]
    Htr, Hte = hist(s, i10, i20)[~te & mh], hist(s, i10, i20)[te & mh]
    okt = ~np.isnan(hp_tr[:, 0]); oke = ~np.isnan(hp_te[:, 0])
    Wh = AW._fit(Htr[okt], (h[~te & mh] - hp_tr)[okt])
    hph = hp_te[oke] + Hte[oke] @ Wh
    out["historia"] = {"podzbior_test": int(oke.sum()), "bez_historii_war_niewyj_mediana": float(np.median(var_unexpl(h[te & mh][oke], hp_te[oke]))),
                       "z_historia_war_niewyj_mediana": float(np.median(var_unexpl(h[te & mh][oke], hph))),
                       "bez_historii_reszta_p99": float(np.percentile(np.abs(h[te & mh][oke] - hp_te[oke]), 99)),
                       "z_historia_reszta_p99": float(np.percentile(np.abs(h[te & mh][oke] - hph), 99))}
    # 20 najgorszych ticków (norma max reszty, siatka podstawowa)
    r = np.abs(wek["siatka_reszta"]).max(1)
    r = np.where(np.isnan(r), -1, r)
    idx_te = np.where(te)[0]
    naj = []
    for j in np.argsort(-r)[:20]:
        i = idx_te[j]
        naj.append({"lot": str(z["nazwy"][z["lot"][i]]), "tick": int(z["tick"][i]), "t_od_i0": float(z["t"][i]), "reszta_max": float(r[j]),
                    "blad_komendy": float(wek["siatka_blad_komendy"][j]),
                    "faza": str(z["faza"][i]), "d_cech": float(s[i, 0]), "vr": float(s[i, 2]), "vt": float(s[i, 3]), "rel_z": float(s[i, 4]),
                    "vd": float(s[i, 5]), "wiek": float(s[i, 6]), "d_gt": float(z["d_gt"][i])})
    out["najgorsze_20"] = naj
    # zakres sytuacji na lotach
    out["zakres_sytuacji_test"] = {n: [float(s[te][:, i].min()), float(s[te][:, i].max())] for i, n in enumerate(AW.NAZWY_S)}
    out["n_ticki"] = {"razem": int(len(s)), "uczace": int((~te).sum()), "testowe": int(te.sum())}
    wyn["R1_1_loty"] = out
    np.savez(os.path.join(OUT, "r1_loty_wektory.npz"), test_idx=idx_te, **wek)


def r1_model(wyn, plik, klucz):
    z = np.load(os.path.join(OUT, plik))
    nb, nt = z["t"].shape
    tr_b = (z["meta"][:, 2] % 2 == 0)
    x = z["x"].reshape(-1, 8); h = z["h"].reshape(-1, AW.H); c = z["c"].reshape(-1, 3)
    s = AW.sytuacja(x)
    tr = np.repeat(tr_b, nt)
    out, wek = {"n_biegow": int(nb), "n_stanow": int(len(s)), "biegi_uczace": int(tr_b.sum()), "d_cech_max": float(s[:, 0].max()),
                "d_prawdziwy_max": float(z["d"].max())}, {}
    for nm, g in (("siatka", AW.Siatka()), ("siatka_x2", AW.Siatka(0.125, 128, 0.125))):
        a = time.time()
        o, w, mp = ocena(g, s[tr], h[tr], s[~tr], h[~tr], c[~tr], kol=(7,))
        o["czas_s"] = time.time() - a
        ks, pw, ile = staty_komorek(g, s, h)
        o["komorki"] = ks
        o["pca"], nk = pca(g, s[~tr], h[~tr], mp) if nm == "siatka" else pca(g, s, h)
        out[nm] = o
        wek[f"{nm}_reszta"] = w["reszta"]; wek[f"{nm}_blad_komendy"] = w["blad_komendy"]; wek[f"{nm}_polszer"] = pw; wek[f"{nm}_ile"] = ile
        print(klucz, nm, json.dumps({k: v for k, v in o.items() if k not in ("war_niewyj_per_neuron",)})[:600], flush=True)
    hg = global_affine(s[tr], h[tr], s[~tr])
    out["odniesienie_globalna_afiniczna"] = {"war_niewyj_mediana": float(np.median(var_unexpl(h[~tr], hg))), "reszta_wpis": q(np.abs(h[~tr] - hg))}
    out["zakres_sytuacji"] = {n: [float(s[:, i].min()), float(s[:, i].max())] for i, n in enumerate(AW.NAZWY_S)}
    wyn[klucz] = out
    np.savez(os.path.join(OUT, f"r1_{klucz}_wektory.npz"), **wek)


def r1_wagi(wyn):
    rng = np.random.default_rng(777)
    out = {}
    # loty: okna 160 kroków sieci (tylko ticki z krokiem), co 5. tick misji
    sys.path.insert(0, os.path.join(AW.ROOT, "results/PETLA_RECON/tools"))
    import pl_dane as PD
    import pl_siec as PS
    X, Hf = [], []
    for d in PD.loty():
        L = PD.wczytaj(d); R = PS.replay(L)
        inf = np.where(R["infer"])[0]
        i0 = inf[0]; tt = L["t"] - L["t"][i0]
        mis = set(np.where((L["misja"] > 0) & (tt >= 30))[0].tolist())
        for j in range(W8, len(inf), 5):
            if inf[j] in mis:
                X.append(R["xs"][inf[j - W8 + 1:j + 1]]); Hf.append(R["h"][inf[j]])
    X, Hf = np.array(X), np.array(Hf)
    zb = {}
    for nm, X_, H_ in (("loty", X, Hf), ("model_W", None, None)):
        if nm == "model_W":
            z = np.load(os.path.join(OUT, "biegi_W.npz"))
            bi = rng.choice(z["x"].shape[0], 400, replace=False)
            ti = rng.integers(W8, z["x"].shape[1], 400)
            X_ = np.array([AW.norm(z["x"][b, t - W8 + 1:t + 1]) for b, t in zip(bi, ti)]); H_ = z["h"][bi, ti]
        h0 = np.zeros((len(X_), AW.H)); hr = rng.uniform(-1, 1, (len(X_), AW.H))
        for k in range(W8):
            h0 = AW.F(X_[:, k], h0); hr = AW.F(X_[:, k], hr)
        hf = H_.copy()
        for _ in range(500):
            hf = AW.F(X_[:, -1], hf)
        e0 = np.abs(h0 - H_).max(1); er = np.abs(hr - H_).max(1); ef = np.abs(hf - H_).max(1)
        out[nm] = {"n": int(len(X_)), "od_zera": q(e0), "od_losowego": q(er), "punkt_staly": q(ef)}
        zb[nm] = np.c_[e0, er, ef]
    wyn["R1_5_wagi"] = out
    np.savez(os.path.join(OUT, "r1_wagi_wektory.npz"), **zb)


if __name__ == "__main__":
    fn = os.path.join(OUT, "r1.json")
    wyn = json.load(open(fn)) if os.path.exists(fn) else {}
    for a in sys.argv[1:]:
        t0 = time.time()
        if a == "loty":
            r1_loty(wyn)
        elif a == "W":
            r1_model(wyn, "biegi_W.npz", "R1_2_model_W")
        elif a == "siec":
            r1_model(wyn, "biegi_siec.npz", "R1_4_model_siec")
        elif a == "wagi":
            r1_wagi(wyn)
        wyn.setdefault("czasy_s", {})[a] = time.time() - t0
        json.dump(wyn, open(fn, "w"), ensure_ascii=False, indent=1)
        print(a, "zrobione", time.time() - t0, flush=True)
