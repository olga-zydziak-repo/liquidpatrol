#!/usr/bin/env python3
"""results/BLIZNIAK_RECON/tools/bz_r3m.py — scalenie R3/R4, test poprawności, próbki (PROMPT_BLIZNIAK_S0 §5–§6; 0 bootów).

Użycie: bz_r3m.py <ramię> <A|B> <liczba_kawałków> [bez_testu]
1. Scala r3e_<ramię>_<w>_*.npz: profil S(v, d₁) dla v ∈ {0.3, 0.6, 1.0, 1.2} (najmniejsze d₁ z siatki 0.25 m, od którego
   wszystkie komórki z d_lo ≥ d₁ mają ograniczenie ≥ v; 15.0 = brak d₁ — ostatnie komórki mają d_lo 14.75), pokrycie d₁ ∈ {9.5, 9.75, 10.0, 10.5, 11.0}, wyjątki — per szczebel.
   Półszerokość U_k (E1, E3) na komórkach d ≥ 8.
2. Test ku (10⁶ historii z 𝒞, rng 101): komórki końcowe losowo spośród wszystkich scalonych, historia k + 1 kroków od stanu
   U(−1, 1)²⁰ (bz_r3.historie); ku ≥ e1, e2, e3 komórki.
3. Test U (10⁴ komórek × 100 historii, rng 202): pudełka U_k przeliczone tą samą procedurą (E1 i E3, przecięcie z zerem + B^k),
   h_t w pudełku.
4. Próbki 10⁷ historii (rng 4321) z komórek d ≥ 9: min ku od d₁.
Zapis: r3_<ramię>_<w>.json, r3_<ramię>_<w>.npz.
"""
import glob
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bz_dowod as BD                                    # noqa: E402
import bz_afin as AF                                     # noqa: E402
import bz_petla as BP                                    # noqa: E402
import bz_r3 as R                                        # noqa: E402
import bz_r3e as RE                                      # noqa: E402

OUT = "/home/olga/projects/liquidpatrol/results/BLIZNIAK_RECON"


def wczytaj(ramie, w, n):
    cz = [np.load(os.path.join(OUT, f"r3e_{ramie}_{w}_{i}.npz")) for i in range(n)]
    out = {k: np.concatenate([c[k] for c in cz]) for k in ("idx", "lo", "hi", "e1", "e2", "e3", "etap", "uE1", "uE3")}
    o = np.argsort(out["idx"])
    out = {k: v[o] for k, v in out.items()}
    out["k"] = int(cz[0]["k"]); out["B"] = float(cz[0]["B"])
    cz_t = {}
    for c in cz:
        for kk, v in json.loads(str(c["czasy"])).items():
            cz_t[kk] = cz_t.get(kk, 0) + v
    out["czasy"] = cz_t
    return out


def profil(dlo, lb):
    out = {}
    d1s = np.round(np.arange(8.0, 15.0 + 1e-9, 0.25), 2)
    for v in (0.3, 0.6, 1.0, 1.2):
        best = None
        for d1 in d1s[::-1]:
            m = dlo >= d1 - 1e-9
            if (lb[m] >= v).all():
                best = float(d1)
            else:
                break
        out[str(v)] = best
    return out


def main(ramie, w, n, test=True):
    t0 = time.time()
    z = wczytaj(ramie, w, n)
    S = BD.Siec(BP.model(ramie)); k = z["k"]; D = RE.delta(w)
    dlo = z["lo"][:, 0]
    wyn = {"ramie": ramie, "delta": w, "Delta": D.tolist(), "B_z_wag_z_zapasem": S.B, "B_nominalne": S.B_nominal, "k": k,
           "B_do_k": S.B ** k if S.B < 1 else None, "komorki_d_ge_8": int(len(dlo)), "czasy_s": z["czasy"]}
    for nm in ("E1", "E2", "E3"):
        lb = z[nm.lower()]
        pk = {}
        for d1 in (9.5, 9.75, 10.0, 10.5, 11.0):
            m = dlo >= d1 - 1e-9
            wyj = np.where(m & (lb < 0.3))[0]
            pk[str(d1)] = {"komorki": int(m.sum()), "udzial_ge_0_3": float((lb[m] >= 0.3).mean()), "udzial_ge_1_0": float((lb[m] >= 1.0).mean()),
                           "wyjatki_0_3": int(len(wyj)),
                           "wyjatki_przyklady": [[round(float(x), 3) for x in z["lo"][i]] + [round(float(lb[i]), 3)] for i in wyj[:15]]}
        wyn[nm] = {"profil_d1": profil(dlo, lb), "pokrycie": pk, "min_od_10m": float(lb[dlo >= 10 - 1e-9].min())}
    wyn["E3_etapy"] = {str(e): int((z["etap"] == e).sum()) for e in range(3)}
    for nm in ("uE1", "uE3"):
        v = z[nm]
        wyn["U_k_" + nm[1:]] = {"polszer_p50": float(np.median(v)), "polszer_p99": float(np.percentile(v, 99)), "polszer_max": float(v.max()),
                                "polszer_min": float(v.min())}
    print(json.dumps({k_: wyn[k_] for k_ in ("E3", "U_k_E3")}, ensure_ascii=False)[:1500], flush=True)
    if test:
        a = time.time()
        rng = np.random.default_rng(101)
        wyj = {"E1": 0, "E2": 0, "E3": 0}
        allc = np.arange(len(dlo))
        for _ in range(10):
            h, hp, ku, c = R.historie(S, rng, 100000, k, D, z["lo"], z["hi"], allc)
            for nm in wyj:
                wyj[nm] += int((ku < z[nm.lower()][c] - 1e-12).sum())
        wyn["test_ku"] = {"historie": 1000000, "wyjatki": wyj, "zdany": sum(wyj.values()) == 0, "czas_s": time.time() - a}
        a = time.time()
        rng = np.random.default_rng(202)
        cs = rng.choice(len(dlo), 10000, replace=False)
        l4, h4 = z["lo"][cs], z["hi"][cs]
        U1 = RE.U_zero(S, BD.U(S, l4, h4, k, D), l4, h4, k, D)
        Ua = AF.U_af(S, l4, h4, k, D); U3 = RE.U_zero(S, (np.maximum(Ua[0], U1[0]), np.minimum(Ua[1], U1[1])), l4, h4, k, D)
        wU1 = wU3 = 0
        for rep in range(100):
            h, hp, ku, c = R.historie(S, rng, 10000, k, D, l4, h4, np.arange(10000))
            wU1 += int(((h < U1[0][c] - 1e-12) | (h > U1[1][c] + 1e-12)).sum()); wU3 += int(((h < U3[0][c] - 1e-12) | (h > U3[1][c] + 1e-12)).sum())
        wyn["test_U"] = {"historie": 1000000, "komorki": 10000, "wyjatki_E1": wU1, "wyjatki_E3": wU3, "zdany": wU1 == wU3 == 0,
                         "polszer_E3_p50_tych_komorek": float(np.median(((U3[1] - U3[0]) / 2).max(1))), "czas_s": time.time() - a}
        print(ramie, w, "testy", wyn["test_ku"], wyn["test_U"], flush=True)
        a = time.time()
        rng = np.random.default_rng(4321)
        sel9 = np.where(dlo >= 9.0 - 1e-9)[0]
        kmin = np.full(len(dlo), np.inf)
        for _ in range(100):
            h, hp, ku, c = R.historie(S, rng, 100000, k, D, z["lo"], z["hi"], sel9)
            np.minimum.at(kmin, c, ku)
        wyn["probki_1e7"] = {str(d1): float(kmin[(dlo >= d1 - 1e-9) & np.isfinite(kmin)].min()) for d1 in (9.0, 9.5, 9.75, 10.0, 10.5, 11.0)}
        wyn["probki_1e7"]["komorki_trafione"] = int(np.isfinite(kmin).sum()); wyn["probki_1e7"]["czas_s"] = time.time() - a
        z["kmin"] = kmin
        print(ramie, w, "probki", wyn["probki_1e7"], flush=True)
    wyn["czas_scalania_s"] = time.time() - t0
    json.dump(wyn, open(os.path.join(OUT, f"r3_{ramie}_{w}.json"), "w"), ensure_ascii=False, indent=1)
    np.savez_compressed(os.path.join(OUT, f"r3_{ramie}_{w}.npz"), **{k_: v for k_, v in z.items() if isinstance(v, np.ndarray)})


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]), len(sys.argv) < 5)
