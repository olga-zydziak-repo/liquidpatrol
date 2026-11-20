#!/usr/bin/env python3
"""results/ARKUSZ_RECON/tools/ar_r2.py — R2 stany czułe (PROMPT_ARKUSZ_S0 §4; 0 bootów).

R2.1/R2.2 (pętla otwarta): próba = (bieg b, tick t) z biegi_W.npz (t ≤ 1200 − 161), zaburzenie δ ~ U(−a, a)^20 (a = 0.05, 0.15)
stanu po ticku t, potem te same wejścia x[t+1..t+160] co w biegu; odniesienie = zapisany stan biegu. Wzmocnienie po k krokach
= ‖Δh_k‖∞ / ‖δ‖∞, k ∈ {1, 2, 5, 10, 20, 40, 80, 160}. Losowanie rng(4242 + 1000·a). Dla prób z wzmocnieniem20 > 1: sytuacja
(d, vt, znak obiegu = sign vt), neuron niosący różnicę (argmax |Δh_20|), pierwszy krok z wzmocnieniem < 0.2.
R2.3 (pętla zamknięta): wsady jak ar_biegi (te same ziarna, wariant W, B = 150), przebieg do t0 ∈ {30, 40, 50, 60, 70} s,
potem 1 + K kopii (K = 50): kopia 0 bez zaburzenia, kopie 1..K ze stanem sieci zaburzonym U(−a, a)^20 (rng 9000 + ziarno + t0);
intruz porusza się względem kopii 0 i ten sam tor dostają wszystkie kopie; szum ten sam (te same innowacje). 10 s. Miary: max
|Δc_xy|, max |Δd| (dystans prawdziwy), zmiana kierunku obiegu (znak średniego momentu (p − q) × v_drona w ostatnich 5 s, gdy
|średnia| > 0.1 w kopii 0).
R2.4: udział ticków (t ≥ 30 s) czułych: tick czuły, gdy któraś z K_t = 8 prób (a = 0.05) ma wzmocnienie20 > 1 — na modelu W
(podpróbka ticków) i na lotach (ticki misji z 20 kolejnymi krokami sieci).
"""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ar_wspolne as AW                                  # noqa: E402
import ar_biegi as AB                                    # noqa: E402
import pl_naped as PN                                    # noqa: E402
import pl_intruz as PI                                   # noqa: E402

OUT = AW.OUT
KS = (1, 2, 5, 10, 20, 40, 80, 160)


def q(a, ps=(50, 99)):
    a = np.asarray(a, float)
    d = {f"p{p:g}": float(np.percentile(a, p)) for p in ps}
    d["max"] = float(a.max()); d["n"] = int(a.size)
    return d


ROZKLAD = "jednostajny"


def otwarta(xn_seq, h_ref_seq, h_start, a, rng, kmax=160):
    """xn_seq (N,kmax,8) wejścia, h_ref_seq (N,kmax,H) stan odniesienia po kolejnych krokach, h_start (N,H).
    Zaburzenie: ROZKLAD „jednostajny” U(−a, a)^20 albo „znak” a·(±1)^20 (narożniki pudełka)."""
    N = len(h_start)
    d0 = rng.uniform(-a, a, (N, AW.H)) if ROZKLAD == "jednostajny" else a * rng.choice([-1.0, 1.0], (N, AW.H))
    n0 = np.abs(d0).max(1)
    h = h_start + d0
    g = {}
    t02 = np.full(N, -1)
    arg20 = None
    for k in range(1, kmax + 1):
        h = AW.F(xn_seq[:, k - 1], h)
        dd = h - h_ref_seq[:, k - 1]
        gk = np.abs(dd).max(1) / n0
        t02[(t02 < 0) & (gk < 0.2)] = k
        if k in KS:
            g[k] = gk
        if k == 20:
            arg20 = np.abs(dd).argmax(1)
    return g, t02, arg20


def r21(wyn, N_PROB=1_000_000, BATCH=10_000):
    z = np.load(os.path.join(OUT, "biegi_W.npz"))
    X, Hh = z["x"], z["h"]
    nb, nt = X.shape[:2]
    s_all = None
    out = {}
    wek = {}
    for a in (0.05, 0.15):
        rng = np.random.default_rng(4242 + int(1000 * a))
        G = {k: [] for k in KS}; T02, A20, BI, TI = [], [], [], []
        t_ = time.time()
        for st in range(0, N_PROB, BATCH):
            bi = rng.integers(0, nb, BATCH); ti = rng.integers(0, nt - 161, BATCH)
            idx = ti[:, None] + np.arange(1, 161)[None]
            xs = AW.norm(X[bi[:, None], idx]); hr = Hh[bi[:, None], idx]
            g, t02, a20 = otwarta(xs, hr, Hh[bi, ti], a, rng)
            for k in KS:
                G[k].append(g[k].astype(np.float32))
            T02.append(t02); A20.append(a20); BI.append(bi); TI.append(ti)
        G = {k: np.concatenate(v) for k, v in G.items()}
        T02, A20, BI, TI = map(np.concatenate, (T02, A20, BI, TI))
        o = {"n_prob": int(N_PROB), "czas_s": time.time() - t_}
        for k in KS:
            o[f"k{k}"] = {"mediana": float(np.median(G[k])), "p99": float(np.percentile(G[k], 99)), "max": float(G[k].max()),
                          "udzial_gt1": float((G[k] > 1).mean()), "n_gt1": int((G[k] > 1).sum())}
        cz = G[20] > 1
        s = AW.sytuacja(X[BI, TI])
        if cz.any():
            o["czule_k20"] = {"n": int(cz.sum()),
                              "d": {"czule": q(s[cz, 0], (5, 50, 95)), "wszystkie": q(s[:, 0], (5, 50, 95))},
                              "vt": {"czule": q(s[cz, 3], (5, 50, 95)), "wszystkie": q(s[:, 3], (5, 50, 95))},
                              "vr": {"czule": q(s[cz, 2], (5, 50, 95)), "wszystkie": q(s[:, 2], (5, 50, 95))},
                              "znak_obiegu_vt_dodatni": {"czule": float((s[cz, 3] > 0).mean()), "wszystkie": float((s[:, 3] > 0).mean())},
                              "neuron_roznicy": {str(i): int((A20[cz] == i).sum()) for i in np.unique(A20[cz])},
                              "krok_do_ponizej_0_2": {"mediana": float(np.median(np.where(T02[cz] < 0, 999, T02[cz]))),
                                                      "max": int(np.where(T02[cz] < 0, 999, T02[cz]).max()),
                                                      "nie_spadlo_w_160": int((T02[cz] < 0).sum())},
                              "rodzina": {PI.RODZINY[r]: int((z["meta"][BI[cz], 0] == r).sum()) for r in range(7)},
                              "rodzina_wszystkie": {PI.RODZINY[r]: int((z["meta"][BI, 0] == r).sum()) for r in range(7)}}
        out[f"a{a}"] = o
        wek[f"a{a}_G"] = np.stack([G[k] for k in KS], 1); wek[f"a{a}_bi"] = BI; wek[f"a{a}_ti"] = TI; wek[f"a{a}_t02"] = T02; wek[f"a{a}_arg20"] = A20
        print("R2.1", a, json.dumps({k: v for k, v in o.items() if k.startswith("k")})[:900], flush=True)
    wyn["R2_1" + ("" if ROZKLAD == "jednostajny" else "_znak")] = out
    np.savez(os.path.join(OUT, "r2_otwarta_wektory" + ("" if ROZKLAD == "jednostajny" else "_znak") + ".npz"), **wek)


def zamknieta_wsad(rodzina, vmax, zr, t0, a, K, B=150):
    rng = np.random.default_rng(zr)
    I = PI.Intruz(rodzina, B, vmax, rng)
    sz = PN.Szum(B, np.random.default_rng(zr + 7919), wl=True)
    P = PN.Petla(B, AB.NAPED, np.tile([0.0, 0.0, -8.0], (B, 1)), np.zeros((B, 3)), AB.WIEK, sz, "W")
    qq = I.pos3()
    for k in range(int(round(t0 / PN.DT))):
        P.krok(qq); qq = I.krok(P.p)
    # kopie: wiersz = kopia·B + b
    R = 1 + K
    rp = np.random.default_rng(9000 + zr + int(t0))
    p, v = np.tile(P.p, (R, 1)), np.tile(P.v, (R, 1))
    h = np.tile(P.h, (R, 1))
    d0 = rp.uniform(-a, a, ((R - 1) * B, AW.H)); h[B:] += d0
    bh = [np.tile(x, (R, 1)) for x in P.bh]; bv = [np.tile(x, R) for x in P.bv]
    nk = int(round(10.0 / PN.DT))
    dc = np.zeros(R * B); dd = np.zeros(R * B); mom = []
    for k in range(nk):
        rel = np.tile(qq - P.p + sz.krok(), (R, 1))     # szum ten sam dla kopii; P.p = kopia 0 (do szumu niepotrzebne)
        rel = rel - (p - np.tile(P.p, (R, 1)))          # rel = q − p_kopii + szum
        x = np.concatenate([rel, v, np.full((R * B, 1), AB.WIEK), np.ones((R * B, 1))], 1)
        y, h = None, AW.F(AW.norm(x), h)
        c = AW.komenda(h).copy()
        c[:, 2] = np.clip(0.5 * (rel[:, 2] - 2.0), -1.0, 1.0)
        bh.append(c[:, :2]); ch = bh.pop(0); bv.append(c[:, 2]); cv = bv.pop(0)
        v[:, :2] += P.ah * (ch - v[:, :2]); v[:, 2] += P.av * (cv - v[:, 2])
        p = p + v * PN.DT
        P.p = p[:B].copy()
        q3 = np.tile(qq, (R, 1))
        d = np.hypot(*(q3[:, :2] - p[:, :2]).T)
        dc = np.maximum(dc, np.hypot(*(c[:, :2] - np.tile(c[:B, :2], (R, 1))).T))
        dd = np.maximum(dd, np.abs(d - np.tile(d[:B], R)))
        if k >= nk - 100:
            r_ = p[:, :2] - q3[:, :2]
            mom.append(r_[:, 0] * v[:, 1] - r_[:, 1] * v[:, 0])
        qq = I.krok(P.p)
    mom = np.mean(mom, 0)
    m0 = np.tile(mom[:B], R)
    zmiana = (np.abs(m0) > 0.1) & (np.sign(mom) != np.sign(m0))
    return dc[B:], dd[B:], zmiana[B:], (np.abs(m0) > 0.1)[B:]


def r23(wyn, K=50):
    out, wek = {}, {}
    for a in (0.05, 0.15):
        DC, DD, ZM, OKM, META = [], [], [], [], []
        t_ = time.time()
        for r, rod in enumerate(PI.RODZINY):
            for j, vm in enumerate((1.0, 0.5)):
                zr = AB.ziarno(r, j, 0)
                for t0 in (30.0, 40.0, 50.0, 60.0, 70.0):
                    dc, dd, zm, okm = zamknieta_wsad(rod, vm, zr, t0, a, K)
                    DC.append(dc); DD.append(dd); ZM.append(zm); OKM.append(okm)
                    META.append(np.tile([r, j, t0], (len(dc), 1)))
            print("R2.3", a, rod, f"{time.time() - t_:.0f}s", flush=True)
        DC, DD, ZM, OKM, META = map(np.concatenate, (DC, DD, ZM, OKM, META))
        out[f"a{a}"] = {"n_prob": int(len(DC)), "max_roznica_komendy": q(DC, (50, 99, 99.9)), "max_roznica_dystansu_10s": q(DD, (50, 99, 99.9)),
                        "udzial_dd_gt_1m": float((DD > 1.0).mean()), "n_dd_gt_1m": int((DD > 1.0).sum()),
                        "zmiana_obiegu": int(ZM.sum()), "proby_z_okreslonym_obiegiem": int(OKM.sum()),
                        "dd_gt_1m_po_rodzinie": {PI.RODZINY[r]: int(((DD > 1.0) & (META[:, 0] == r)).sum()) for r in range(7)},
                        "czas_s": time.time() - t_}
        wek[f"a{a}"] = np.c_[DC, DD, ZM, OKM, META]
        print("R2.3", a, out[f"a{a}"], flush=True)
    wyn["R2_3"] = out
    np.savez(os.path.join(OUT, "r2_zamknieta_wektory.npz"), **wek)


def r24(wyn, KT=8):
    out, wek = {}, {}
    rng = np.random.default_rng(31337)
    # model: podpróbka 200 000 ticków
    z = np.load(os.path.join(OUT, "biegi_W.npz"))
    X, Hh = z["x"], z["h"]
    nb, nt = X.shape[:2]
    N = 200_000
    bi = rng.integers(0, nb, N); ti = rng.integers(0, nt - 21, N)
    czm = np.zeros(N, bool); gmax = np.zeros(N)
    for st in range(0, N, 25_000):
        sl = slice(st, st + 25_000)
        idx = ti[sl, None] + np.arange(1, 21)[None]
        xs = AW.norm(X[bi[sl, None], idx]); hr = Hh[bi[sl, None], idx]
        for _ in range(KT):
            g, _, _ = otwarta(xs, hr, Hh[bi[sl], ti[sl]], 0.05, rng, kmax=20)
            gmax[sl] = np.maximum(gmax[sl], g[20])
    czm = gmax > 1
    out["model_W"] = {"n_tickow": N, "K_na_tick": KT, "udzial_czulych": float(czm.mean()), "n_czulych": int(czm.sum()),
                      "wzmocnienie20_max_na_tick": q(gmax, (50, 99, 99.9))}
    wek["model_gmax"] = gmax; wek["model_bi"] = bi; wek["model_ti"] = ti
    # loty: ticki misji z 20 kolejnymi krokami sieci
    zl = np.load(os.path.join(OUT, "loty.npz"), allow_pickle=True)
    kl = zl["lot"].astype(np.int64) * 10 ** 7 + zl["tick"].astype(np.int64)
    pos = {int(k): i for i, k in enumerate(kl)}
    ok, nast = [], []
    for i, k in enumerate(kl):
        js = [pos.get(int(k) + j, -1) for j in range(1, 21)]
        if min(js) >= 0:
            ok.append(i); nast.append(js)
    ok, nast = np.array(ok), np.array(nast)
    xs = AW.norm(zl["x"][nast]); hr = zl["h"][nast]
    gl = np.zeros(len(ok))
    for _ in range(KT):
        g, _, _ = otwarta(xs, hr, zl["h"][ok], 0.05, rng, kmax=20)
        gl = np.maximum(gl, g[20])
    out["loty"] = {"n_tickow": int(len(ok)), "z_wszystkich_misji": int(len(kl)), "udzial_czulych": float((gl > 1).mean()),
                   "n_czulych": int((gl > 1).sum()), "wzmocnienie20_max_na_tick": q(gl, (50, 99, 99.9))}
    wek["loty_gmax"] = gl; wek["loty_idx"] = ok
    wyn["R2_4"] = out
    np.savez(os.path.join(OUT, "r2_czas_wektory.npz"), **wek)
    print("R2.4", out, flush=True)


if __name__ == "__main__":
    fn = os.path.join(OUT, "r2.json")
    wyn = json.load(open(fn)) if os.path.exists(fn) else {}
    for a in sys.argv[1:]:
        t0 = time.time()
        if a == "r21z":
            ROZKLAD = "znak"; a = "r21"
        {"r21": r21, "r23": r23, "r24": r24}[a](wyn)
        wyn.setdefault("czasy_s", {})[a + ("" if ROZKLAD == "jednostajny" else "_znak")] = time.time() - t0
        json.dump(wyn, open(fn, "w"), ensure_ascii=False, indent=1)
