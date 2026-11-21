#!/usr/bin/env python3
"""results/BLIZNIAK_RECON/tools/bz_r3e.py — R3/R4 przebieg na kawałku komórek (PROMPT_BLIZNIAK_S0 §5–§6; 0 bootów).

Użycie: bz_r3e.py <ramię> <A|B> <kawałek> <liczba_kawałków>
Komórki 𝒟 (bz_dowod.komorki) z d ≥ 8.0 m, dzielone na kawałki po indeksie (i % liczba == kawałek).
Szczeble ograniczenia komendy ku (po clip_v), h_{t−1} z rozwinięcia przez X_k … X_1, krok X_0, odczyt:
  E1 — przedziały naturalne (bz_dowod.U + ku_E1);
  E2 — forma o wartości średniej po całej historii (bz_dowod.ku_lancuch: jakobian przedziałowy po h_init i sytuacjach);
  E3 — formy afiniczne (bz_afin.ku_af) z podziałem adaptacyjnym: etap 0 bez podziału; etap 1 (komórki z ograniczeniem < 1.2)
       θ w X_1 na 3, θ w X_0 na 4; etap 2 (d ≥ 9.5 m i nadal < 0.3) θ w X_2 na 2, (d, θ, v_r, v_t) w X_1 na (1, 4, 2, 2), w X_0 na (2, 4, 1, 1).
       Wynik komórki = max po etapach (każdy etap jest osobnym poprawnym ograniczeniem).
U_k (lemat U, h_t przez X_{k−1} … X_0) — E1 i E3 (bez podziału) na tych samych komórkach; dla B(W) < 1 przecięte
z rozwinięciem od zera + B(W)^k (B z wag z zapasem).
Zapis: r3e_<ramię>_<A|B>_<kawałek>.npz.
"""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bz_dowod as BD                                    # noqa: E402
import bz_afin as AF                                     # noqa: E402
import bz_petla as BP                                    # noqa: E402

OUT = "/home/olga/projects/liquidpatrol/results/BLIZNIAK_RECON"
BATCH = 2000
ETAP1 = ({1: [1, 3, 1, 1, 1, 1, 1]}, [1, 4, 1, 1, 1, 1, 1])
ETAP2 = ({2: [1, 2, 1, 1, 1, 1, 1], 1: [1, 4, 2, 2, 1, 1, 1]}, [2, 4, 1, 1, 1, 1, 1])
PROG = 1.2


def delta(w):
    if w == "A":
        return BD.DELTA_A.copy()
    return np.array(json.load(open(os.path.join(OUT, "r4_przeslanki.json")))["delta_B"])


def k_ramienia(S):
    return BD.k_dla(S) if S.B < 1 else 5


def ku_podzial(S, lo4, hi4, D, k, spec):
    nad_cz, cz0 = spec
    X0 = BD.pelne(lo4, hi4)
    gen = {j: list(BD.podzial(*BD.Xj(lo4, hi4, j, D), c)) for j, c in nad_cz.items()}
    js = sorted(gen)
    best = np.full(len(lo4), np.inf)
    for combo in np.ndindex(*[len(gen[j]) for j in js]):
        nad = {j: gen[j][i] for j, i in zip(js, combo)}
        for s0 in BD.podzial(*X0, cz0):
            l, _ = AF.ku_af(S, lo4, hi4, D, k, X0=s0, nadpisz=nad)
            best = np.minimum(best, l)
    return best


def U_zero(S, U, lo4, hi4, k, D, j0=0):
    """Przecięcie z rozwinięciem od zera + B^k (tylko B < 1)."""
    if S.B >= 1:
        return U
    P = len(lo4)
    Hz = (np.zeros((P, 20)), np.zeros((P, 20)))
    for j in range(j0 + k - 1, j0 - 1, -1):
        Sl, Sh = BD.Xj(lo4, hi4, j, D)
        xl, xh, _, _ = S.x_box(Sl, Sh)
        Hz = S.F_box(xl, xh, *Hz)
    e = S.B ** k + BD.ZAPAS
    return np.maximum(U[0], Hz[0] - e), np.minimum(U[1], Hz[1] + e)


def main(ramie, wersja, kaw, nkaw):
    t0 = time.time()
    S = BD.Siec(BP.model(ramie))
    k = k_ramienia(S)
    D = delta(wersja)
    DMIN = float(os.environ.get("DMIN", "8.0"))          # Δ_B w budżecie: DMIN = 9.5, OKROJONY = 1 (etap 1 tylko < 0.3, bez etapu 2)
    OKR = os.environ.get("OKROJONY") == "1"
    lo, hi = BD.komorki(DMIN, 15.0)
    idx = np.arange(len(lo))[kaw::nkaw]
    lo, hi = lo[idx], hi[idx]
    P = len(lo)
    e1 = np.zeros(P); e2 = np.zeros(P); e3 = np.zeros(P); etap = np.zeros(P, np.int8)
    uE1 = np.zeros(P); uE3 = np.zeros(P)
    czasy = {"E1": 0.0, "E2": 0.0, "E3_0": 0.0, "E3_1": 0.0, "E3_2": 0.0, "U": 0.0}
    for a in range(0, P, BATCH):
        sl = slice(a, a + BATCH); l4, h4 = lo[sl], hi[sl]
        t = time.time()
        U1 = U_zero(S, BD.U(S, l4, h4, k, D, j0=1) if S.B < 1 else BD.U(S, l4, h4, k, D, j0=1), l4, h4, k, D, j0=1)
        Sl, Sh = BD.pelne(l4, h4)
        l1, yb = BD.ku_E1(S, Sl, Sh, *U1); e1[sl] = BD.ku_dolne(l1, yb)
        czasy["E1"] += time.time() - t; t = time.time()
        l2, _ = BD.ku_lancuch(S, l4, h4, D, k); e2[sl] = np.maximum(e1[sl], l2)
        czasy["E2"] += time.time() - t; t = time.time()
        l3, _ = AF.ku_af(S, l4, h4, D, k); e3[sl] = np.maximum(e2[sl], l3)
        czasy["E3_0"] += time.time() - t; t = time.time()
        Ue1 = U_zero(S, BD.U(S, l4, h4, k, D), l4, h4, k, D)
        Ua = AF.U_af(S, l4, h4, k, D); Ua = U_zero(S, (np.maximum(Ua[0], Ue1[0]), np.minimum(Ua[1], Ue1[1])), l4, h4, k, D)
        uE1[sl] = ((Ue1[1] - Ue1[0]) / 2).max(1); uE3[sl] = ((Ua[1] - Ua[0]) / 2).max(1)
        czasy["U"] += time.time() - t
    if ramie not in ("Z", "K"):
        for nr, spec in (((1, ETAP1),) if OKR else ((1, ETAP1), (2, ETAP2))):
            t = time.time()
            if OKR:
                kand = np.where(e3 < 0.3)[0]
            else:
                kand = np.where(e3 < PROG)[0] if nr == 1 else np.where((lo[:, 0] >= 9.5 - 1e-9) & (e3 < 0.3))[0]
            for a in range(0, len(kand), BATCH // 4):
                ii = kand[a:a + BATCH // 4]
                v = ku_podzial(S, lo[ii], hi[ii], D, k, spec)
                lepiej = v > e3[ii]
                e3[ii] = np.maximum(e3[ii], v); etap[ii[lepiej]] = nr
            czasy[f"E3_{nr}"] = time.time() - t
            print(ramie, wersja, kaw, "etap", nr, len(kand), f"{time.time() - t0:.0f}s", flush=True)
    np.savez_compressed(os.path.join(OUT, f"r3e_{ramie}_{wersja}_{kaw}.npz"), idx=idx, lo=lo, hi=hi, e1=e1, e2=e2, e3=e3, etap=etap,
                        uE1=uE1, uE3=uE3, k=k, B=S.B, czasy=json.dumps(czasy))
    print(ramie, wersja, kaw, "koniec", f"{time.time() - t0:.0f}s", json.dumps(czasy), flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
