#!/usr/bin/env python3
"""results/BLIZNIAK_RECON/tools/bz_r3.py — R3 lemat U i R4 profil S z testem poprawności (PROMPT_BLIZNIAK_S0 §5–§6; 0 bootów).

Użycie: bz_r3.py <ramię> <A|B> [k]
1. U_k(c) (szczebel E1, rozwinięcie przez X_{k−1} … X_0) na wszystkich komórkach 𝒟: półszerokość max po neuronach (p50, p99, max).
   k = najmniejsze z B(W)^k ≤ 0.005 dla B(W) < 1 (B(W) z zapisanych wag, nie γ); dla Z i K k z argumentu (jak B30).
2. Komenda: komórki z d ≥ 6.0 m; h_{t−1} ∈ U^(1) = rozwinięcie przez X_k … X_1; dolna granica ku po clip_v szczeblami E1, E2,
   E3 (E3 tylko dla komórek z d ≥ 9.0 m, w których E2 < 1.2 m/s: podział X_0 na 2 części w (d, θ, v_r, v_t) i X_1 na 3).
3. Profil: dla v ∈ {0.3, 0.6, 1.0, 1.2} najmniejsze d₁ (siatka 0.25 m), od którego wszystkie komórki z d_lo ≥ d₁ mają
   ograniczenie ≥ v; pokrycie dla d₁ ∈ {9.5, 9.75, 10.0, 10.5, 11.0}; wyjątki.
4. Test poprawności (10⁶ historii z 𝒞, rng 31 + …): komórka końcowa losowa (d ≥ 6), s_t ~ U(c), wstecz s_{t−j} = s_{t−j+1} − δ,
   δ ~ U(±Δ) (wyjście z 𝒟 ⇒ δ = 0 w tej współrzędnej), (rel_z, vd, wiek) losowo w przedziałach co tick, stan początkowy
   h_{t−k−1} ~ U(−1, 1)²⁰. Sprawdza: h_t ∈ U_k(c), h_{t−1} ∈ U^(1)(c), ku_t ≥ ograniczenie E1/E2/E3 komórki.
5. Próbki: 10⁷ historii tym samym generatorem (rng 4321), min ku per komórka (d ≥ 9).
Zapis: r3_<ramię>_<A|B>.json, r3_<ramię>_<A|B>.npz (wektory per komórka).
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

OUT = "/home/olga/projects/liquidpatrol/results/BLIZNIAK_RECON"
BATCH = 40000


def delta(wersja):
    if wersja == "A":
        return BD.DELTA_A.copy()
    return np.array(json.load(open(os.path.join(OUT, "r4_przeslanki.json")))["delta_B"])


def U_wszystkie(S, lo, hi, k, D, j0=0):
    Ul = np.zeros((len(lo), 20)); Uh = np.zeros((len(lo), 20))
    for a in range(0, len(lo), BATCH):
        sl = slice(a, a + BATCH)
        Ul[sl], Uh[sl] = BD.U(S, lo[sl], hi[sl], k, D, j0)
    return Ul, Uh


def ku_szczeble(S, lo, hi, U1l, U1h, D):
    P = len(lo)
    e1 = np.zeros(P); e2 = np.zeros(P)
    for a in range(0, P, BATCH):
        sl = slice(a, a + BATCH)
        Sl, Sh = BD.pelne(lo[sl], hi[sl])
        l1, yb = BD.ku_E1(S, Sl, Sh, U1l[sl], U1h[sl])
        e1[sl] = BD.ku_dolne(l1, yb)
        l2, yb2 = BD.ku_E2(S, Sl, Sh, U1l[sl], U1h[sl])
        e2[sl] = BD.ku_dolne(l2, yb2)
    return e1, np.maximum(e1, e2)


def ku_E3(S, lo4, hi4, k, D, U1l, U1h, pelny):
    """Podział X_0 na 2 części w (d, θ, v_r, v_t) (16 pod-pudełek), ku E2 na każdym z h_{t−1} ∈ U^(1); gdy pelny: dodatkowo X_1 na
    3 części (81) z h_{t−1} = F̂(X_1^p, U^(2)) ∩ U^(1), U^(2) = rozwinięcie przez X_k … X_2. Wynik: minimum po pod-pudełkach."""
    P = len(lo4)
    w0 = (hi4 - lo4) / 2
    H = [(U1l, U1h)]
    if pelny:
        U2l, U2h = BD.U(S, lo4, hi4, k - 1, D, j0=2)
        X1l, X1h = BD.Xj(lo4, hi4, 1, D)
        w1 = (X1h[:, :4] - X1l[:, :4]) / 3
        H = []
        for i1 in np.ndindex(3, 3, 3, 3):
            sl1 = X1l.copy(); sh1 = X1h.copy()
            sl1[:, :4] = X1l[:, :4] + np.array(i1) * w1; sh1[:, :4] = sl1[:, :4] + w1
            xl, xh, _, _ = S.x_box(sl1, sh1)
            Hl, Hh = S.F_box(xl, xh, U2l, U2h)
            H.append((np.maximum(Hl, U1l), np.minimum(Hh, U1h)))
    best = np.full(P, np.inf)
    for Hl, Hh in H:
        for i0 in np.ndindex(2, 2, 2, 2):
            l4 = lo4 + np.array(i0) * w0
            Sl, Sh = BD.pelne(l4, l4 + w0)
            l2, yb = BD.ku_E2(S, Sl, Sh, Hl, Hh)
            best = np.minimum(best, BD.ku_dolne(l2, yb))
    return best


def profil(dlo, lb):
    out = {}
    d1s = np.round(np.arange(6.0, 15.0 + 1e-9, 0.25), 2)
    for v in (0.3, 0.6, 1.0, 1.2):
        best = None
        for d1 in d1s[::-1]:
            m = dlo >= d1 - 1e-9
            if m.any() and (lb[m] >= v).all():
                best = float(d1)
            elif m.any():
                break
        out[f"v{v}"] = best
    pok = {}
    for d1 in (9.5, 9.75, 10.0, 10.5, 11.0):
        m = dlo >= d1 - 1e-9
        pok[str(d1)] = {"komorki": int(m.sum()), "udzial_ge_0_3": float((lb[m] >= 0.3).mean()),
                        "udzial_ge_1_0": float((lb[m] >= 1.0).mean())}
    return out, pok


def historie(S, rng, N, k, D, lo, hi, idx_c):
    """N historii kończących się w komórkach idx_c (losowo z podanych): zwraca h_t, h_{t−1}, ku_t, komórka."""
    c = idx_c[rng.integers(0, len(idx_c), N)]
    s = lo[c] + (hi[c] - lo[c]) * rng.uniform(0, 1, (N, 4))
    seq = [s]
    for j in range(k + 1):
        dl = rng.uniform(-1, 1, (N, 4)) * D
        sn = seq[-1] - dl
        bad = (sn[:, 0] < BD.DOM["d"][0]) | (sn[:, 0] > BD.DOM["d"][1])
        sn[bad, 0] = seq[-1][bad, 0]
        badv = np.hypot(sn[:, 2], sn[:, 3]) > BD.DOM["v"]
        sn[badv, 2:] = seq[-1][badv, 2:]
        seq.append(sn)
    seq = seq[::-1]                                          # najstarszy pierwszy; seq[-1] = s_t
    h = rng.uniform(-1, 1, (N, 20))
    hs = []
    for s4 in seq[1:]:                                       # k + 1 kroków: h_{t−k−1} → h_t
        rz = rng.uniform(*BD.DOM["rz"], N); vd = rng.uniform(*BD.DOM["vd"], N); wk = rng.uniform(*BD.DOM["wiek"], N)
        x = np.stack([s4[:, 0] * np.cos(s4[:, 1]), s4[:, 0] * np.sin(s4[:, 1]), rz,
                      s4[:, 2] * np.cos(s4[:, 1]) - s4[:, 3] * np.sin(s4[:, 1]), s4[:, 2] * np.sin(s4[:, 1]) + s4[:, 3] * np.cos(s4[:, 1]),
                      vd, wk, np.ones(N)], 1)
        xn = (x - S.mean) / S.std
        hprev = h
        h = S.F(xn, h)
        hs.append(h)
    ku = S.ku(xn, hprev, seq[-1][:, 1])
    return h, hprev, ku, c


def main(ramie, wersja, k_arg=None):
    t0 = time.time()
    m = BP.model(ramie)
    S = BD.Siec(m)
    k = BD.k_dla(S) if S.B < 1 else int(k_arg)
    D = delta(wersja)
    lo, hi = BD.komorki()
    wyn = {"ramie": ramie, "delta": wersja, "Delta": D.tolist(), "B_z_wag": S.B, "k": k, "B_do_k": S.B ** k if S.B < 1 else None,
           "komorki": int(len(lo))}
    a = time.time()
    Ul, Uh = U_wszystkie(S, lo, hi, k, D)
    pw = ((Uh - Ul) / 2).max(1)
    wyn["U_k_E1"] = {"polszer_p50": float(np.median(pw)), "polszer_p99": float(np.percentile(pw, 99)), "polszer_max": float(pw.max()),
                     "polszer_min": float(pw.min()), "czas_s": time.time() - a}
    print(ramie, wersja, "U", wyn["U_k_E1"], flush=True)
    sel = np.where(lo[:, 0] >= 6.0 - 1e-9)[0]
    a = time.time()
    U1l, U1h = U_wszystkie(S, lo[sel], hi[sel], k, D, j0=1)
    e1, e2 = ku_szczeble(S, lo[sel], hi[sel], U1l, U1h, D)
    wyn["czas_E1E2_s"] = time.time() - a
    e3 = e2.copy()
    a = time.time()
    if ramie not in ("Z", "K"):
        kand = np.where((lo[sel, 0] >= 9.0 - 1e-9) & (e2 < 1.2))[0]
        for b in range(0, len(kand), 4000):
            ii = kand[b:b + 4000]
            e3[ii] = np.maximum(e2[ii], ku_E3(S, lo[sel][ii], hi[sel][ii], k, D, U1l[ii], U1h[ii], False))
        kand2 = np.where((lo[sel, 0] >= 9.5 - 1e-9) & (e3 < 0.3))[0]
        for b in range(0, len(kand2), 200):
            ii = kand2[b:b + 200]
            e3[ii] = np.maximum(e3[ii], ku_E3(S, lo[sel][ii], hi[sel][ii], k, D, U1l[ii], U1h[ii], True))
        wyn["E3_komorki_podzial_X0"] = int(len(kand)); wyn["E3_komorki_podzial_X0_X1"] = int(len(kand2))
    wyn["czas_E3_s"] = time.time() - a
    dlo = lo[sel, 0]
    for nm, lb in (("E1", e1), ("E2", e2), ("E3", e3)):
        pr, pk = profil(dlo, lb)
        wyj = np.where((dlo >= 10.0 - 1e-9) & (lb < 0.3))[0]
        wyn[nm] = {"profil_d1": pr, "pokrycie": pk,
                   "wyjatki_d_ge_10_v0_3": {"n": int(len(wyj)),
                                            "d_lo": np.unique(dlo[wyj]).tolist()[:20],
                                            "vr_lo": np.unique(lo[sel][wyj, 2]).tolist()[:30],
                                            "vt_lo": np.unique(lo[sel][wyj, 3]).tolist()[:30]}}
        print(ramie, wersja, nm, pr, flush=True)
    json.dump(wyn, open(os.path.join(OUT, f"r3_{ramie}_{wersja}.json"), "w"), ensure_ascii=False, indent=1)
    # test poprawności: 10⁶ historii
    a = time.time()
    rng = np.random.default_rng(31 + (0 if wersja == "A" else 1))
    wyjU = wyjU1 = wyj1 = wyj2 = wyj3 = 0
    full_idx = np.arange(len(lo)); pos_sel = np.full(len(lo), -1); pos_sel[sel] = np.arange(len(sel))
    for _ in range(10):
        h, hp, ku, c = historie(S, rng, 100000, k, D, lo, hi, sel)
        ps = pos_sel[c]
        wyjU += int(((h < Ul[c] - 1e-12) | (h > Uh[c] + 1e-12)).sum())
        wyjU1 += int(((hp < U1l[ps] - 1e-12) | (hp > U1h[ps] + 1e-12)).sum())
        wyj1 += int((ku < e1[ps] - 1e-12).sum()); wyj2 += int((ku < e2[ps] - 1e-12).sum()); wyj3 += int((ku < e3[ps] - 1e-12).sum())
    wyn["test_poprawnosci"] = {"historie": 1000000, "wyjatki_U_k": wyjU, "wyjatki_U1": wyjU1, "wyjatki_ku_E1": wyj1,
                               "wyjatki_ku_E2": wyj2, "wyjatki_ku_E3": wyj3,
                               "zdany": wyjU == wyjU1 == wyj1 == wyj2 == wyj3 == 0, "czas_s": time.time() - a}
    print(ramie, wersja, "test", wyn["test_poprawnosci"], flush=True)
    # próbki 10⁷ (d ≥ 9)
    a = time.time()
    rng = np.random.default_rng(4321)
    sel9 = sel[lo[sel, 0] >= 9.0 - 1e-9]
    kmin = np.full(len(lo), np.inf)
    for _ in range(100):
        h, hp, ku, c = historie(S, rng, 100000, k, D, lo, hi, sel9)
        np.minimum.at(kmin, c, ku)
    pr_s = {}
    for d1 in (9.0, 9.5, 9.75, 10.0, 10.5, 11.0, 12.0):
        mm = (lo[:, 0] >= d1 - 1e-9) & np.isfinite(kmin)
        pr_s[str(d1)] = float(kmin[mm].min())
    wyn["probki_1e7"] = {"min_ku_od_d1": pr_s, "komorki_trafione": int(np.isfinite(kmin[sel9]).sum()), "z": int(len(sel9)),
                         "czas_s": time.time() - a}
    print(ramie, wersja, "probki", pr_s, flush=True)
    wyn["czas_s"] = time.time() - t0
    json.dump(wyn, open(os.path.join(OUT, f"r3_{ramie}_{wersja}.json"), "w"), ensure_ascii=False, indent=1)
    np.savez_compressed(os.path.join(OUT, f"r3_{ramie}_{wersja}.npz"), lo=lo[sel].astype(np.float32), e1=e1, e2=e2, e3=e3,
                        U_polszer=pw.astype(np.float32), kmin=kmin[sel].astype(np.float32))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
