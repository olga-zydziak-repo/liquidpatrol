#!/usr/bin/env python3
"""results/PETLA_RECON/tools/pl_r45.py — R4 / R5 rodziny stałe (PROMPT_PETLA_S0 §6–§7; 0 bootów).

Zadania: wariant ∈ {siec (sieć jak leci), W (pion regulatorem zewnętrznym)} × v_max ∈ {1.0, 0.5} × 7 rodzin × 5 napędów × szum
∈ {tak, nie}; po 900 biegów × 300 s. Ziarno zadania = indeks zadania na tej liście (stała kolejność) · 1000 + 17.
Zapis cząstkowy po każdym zadaniu: results/PETLA_RECON/r45_czesci/<wariant>_<v>_<rodzina>_<napęd>_<szum>.npz (tablice per bieg)
+ podsumowanie r45.json. Procesy ≤ 6 (dwa pozostałe na szukanie), wątki BLAS 1.
"""
import itertools
import json
import os
import sys
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pl_bieg as PB                                     # noqa: E402
import pl_intruz as PI                                   # noqa: E402

CZ = os.path.join(PB.OUT, "r45_czesci")
NAPEDY = ("N", "P-", "P+", "H-", "H+")


def zadania():
    return list(itertools.product(("siec", "W"), (1.0, 0.5), PI.RODZINY, NAPEDY, (True, False)))


def nazwa(z):
    w, v, r, n, s = z
    return f"{w}_{v}_{r}_{n}_{'szum' if s else 'bez'}"


def jedno(arg):
    i, z = arg
    fn = os.path.join(CZ, nazwa(z) + ".npz")
    if os.path.exists(fn):
        return nazwa(z)
    w, v, r, n, s = z
    res = PB.bieg(r, n, s, v, wariant=w, B=900, ziarno=i * 1000 + 17)
    np.savez_compressed(fn + ".tmp.npz", ziarno=i * 1000 + 17, **res)
    os.replace(fn + ".tmp.npz", fn)
    return nazwa(z)


def podsumuj():
    out = {}
    for i, z in enumerate(zadania()):
        fn = os.path.join(CZ, nazwa(z) + ".npz")
        if not os.path.exists(fn):
            continue
        a = np.load(fn)
        ev = np.isfinite(a["t_ev"])
        bez = ~ev
        out[nazwa(z)] = {"ziarno": int(a["ziarno"]), "n": int(len(ev)), "zdarzenia": int(ev.sum()),
                         "w_gore": int((a["kier"][ev] > 0).sum()), "w_dol": int((a["kier"][ev] < 0).sum()),
                         "t_ev_min": float(np.nanmin(a["t_ev"])) if ev.any() else None,
                         "t_ev_med": float(np.nanmedian(a["t_ev"])) if ev.any() else None,
                         "d_po_max_med": float(np.nanmedian(a["d_po_max"][ev])) if ev.any() else None,
                         "d_kon_med_po_ev": float(np.median(a["d_kon"][ev])) if ev.any() else None,
                         "max_dz": float(a["max_dz"].max()),
                         "d_max": float(a["d_max"].max()), "d_cech_max": float(a["d_cech_max"].max()), "r_max": float(a["r_max"].max()),
                         "d_max_bez_ev": float(a["d_max"][bez].max()) if bez.any() else None,
                         "d_cech_max_bez_ev": float(a["d_cech_max"][bez].max()) if bez.any() else None,
                         "r_max_bez_ev": float(a["r_max"][bez].max()) if bez.any() else None,
                         **{f"min_ku_{g}": (float(a[f"ku_{g}"][bez][np.isfinite(a[f'ku_{g}'][bez])].min())
                                            if bez.any() and np.isfinite(a[f"ku_{g}"][bez]).any() else None) for g in ("10_5", "11", "12")}}
    json.dump(out, open(os.path.join(PB.OUT, "r45.json"), "w"), ensure_ascii=False, indent=1)
    return out


if __name__ == "__main__":
    os.makedirs(CZ, exist_ok=True)
    if "podsumuj" not in sys.argv[1:]:
        zz = list(enumerate(zadania()))
        with Pool(6) as p:
            for k, nm in enumerate(p.imap_unordered(jedno, zz)):
                print(k + 1, "/", len(zz), nm, flush=True)
    o = podsumuj()
    print("zadań", len(o))
