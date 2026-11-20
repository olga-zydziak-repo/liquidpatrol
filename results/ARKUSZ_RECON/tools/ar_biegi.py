#!/usr/bin/env python3
"""results/ARKUSZ_RECON/tools/ar_biegi.py — biegi modelu pętli w dziedzinie ARKUSZA (PROMPT_ARKUSZ_S0 §2, §3.2; 0 bootów).

Silnik PĘTLI bez zmian (pl_naped.Petla, napęd N z r3_naped.json: poziom 7 ticków / 0.3 s, pion 1 tick / 0.1 s), szum AR(1)
z szum_rel.json, wiek tracka = mediana z lotów (r2b.json). Start z lotu: dron w home na 8 m (p = (0, 0, −8)), v = 0, stan sieci
zerowy; intruz 6–11 m od home na 10 m (pl_intruz). Rodziny: wszystkie 7 z pl_intruz.RODZINY, v_max 1.0 i 0.5.
Wariant „W” (dziedzina): komenda pionowa = clip(0.5·(rel_z − 2), ±1). Wariant „siec” (R1.4): pion z sieci.
Ziarno wsadu (rodzina r, v_max j, wariant w) = 50000 + 1000·w + 100·r + j; intruz default_rng(ziarno), szum default_rng(ziarno + 7919)
— jak pl_bieg. Zapis t ≥ 30 s: cechy x (8), stan przed krokiem h0, stan po kroku h, komenda c, indeks biegu, t, dystans prawdziwy.
Biegi o parzystym indeksie w wsadzie = uczące, nieparzystym = testowe.
"""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ar_wspolne as AW                                  # noqa: E402
import pl_naped as PN                                    # noqa: E402
import pl_intruz as PI                                   # noqa: E402

PET = os.path.join(AW.ROOT, "results/PETLA_RECON")
NAPED = json.load(open(os.path.join(PET, "r3_naped.json")))["napedy"]["N"]
WIEK = float(json.load(open(os.path.join(PET, "r2b.json")))["wiek_tracka"]["mediana"])
T_OC = 30.0


def ziarno(r, j, w):
    return 50000 + 1000 * w + 100 * r + j


def wsad(rodzina, vmax, wariant, B, T, zr):
    rng = np.random.default_rng(zr)
    I = PI.Intruz(rodzina, B, vmax, rng)
    sz = PN.Szum(B, np.random.default_rng(zr + 7919), wl=True)
    P = PN.Petla(B, NAPED, np.tile([0.0, 0.0, -8.0], (B, 1)), np.zeros((B, 3)), WIEK, sz, wariant)
    q = I.pos3()
    rec = {k: [] for k in ("x", "h0", "h", "c", "t", "d", "relz", "p")}
    n = int(round(T / PN.DT))
    for k in range(n):
        t = k * PN.DT
        c = P.krok(q)
        if t >= T_OC - 1e-9:
            rec["x"].append(P.x.copy()); rec["h0"].append(P.h_przed.copy()); rec["h"].append(P.h.copy()); rec["c"].append(c.copy())
            rec["t"].append(np.full(B, t)); rec["d"].append(np.hypot(*(q[:, :2] - P.p[:, :2]).T)); rec["relz"].append(q[:, 2] - P.p[:, 2])
            rec["p"].append(P.p.copy())
        q = I.krok(P.p)
    # (T', B, ...) → bieg-major
    return {k: np.swapaxes(np.array(v), 0, 1) for k, v in rec.items()}


def zbierz(wariant, B, T, nazwa):
    a = time.time()
    czesci = {}
    meta = []
    for r, rod in enumerate(PI.RODZINY):
        for j, vm in enumerate((1.0, 0.5)):
            zr = ziarno(r, j, 0 if wariant == "W" else 1)
            o = wsad(rod, vm, wariant, B, T, zr)
            for k, v in o.items():
                czesci.setdefault(k, []).append(v)
            meta += [(r, j, i, zr) for i in range(B)]
            print(wariant, rod, vm, f"{time.time() - a:.0f}s", flush=True)
    out = {k: np.concatenate(v, 0) for k, v in czesci.items()}     # (biegi, T', ...)
    out["meta"] = np.array(meta)                                       # (rodzina, vmax_idx, indeks w wsadzie, ziarno)
    np.savez(os.path.join(AW.OUT, nazwa), **out)
    return out


if __name__ == "__main__":
    os.makedirs(AW.OUT, exist_ok=True)
    if "W" in sys.argv[1:]:
        zbierz("W", 150, 90.0, "biegi_W.npz")
    if "siec" in sys.argv[1:]:
        zbierz("siec", 50, 90.0, "biegi_siec.npz")
