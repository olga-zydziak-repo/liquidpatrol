#!/usr/bin/env python3
"""results/PETLA_RECON/tools/pl_bieg.py — bieg wsadowy pętli sieć–napęd w klasie I (PROMPT_PETLA_S0 §6–§7; 0 bootów).

Start: dron w home na wysokości 12 m (p = (0, 0, −12), v = 0, rel_z = 2.0), stan sieci zerowy, wiek tracka = mediana z lotów
(r2b.json), track ważny. Ocena od 20. sekundy. Każdy bieg odtwarzalny z (rodzina, napęd, szum, v_max, wariant, ziarno, indeks):
ziarno wsadu = `ziarno`; generator numpy default_rng(ziarno) losuje kolejno: start/parametry intruza, potem szum (osobny strumień
default_rng(ziarno + 7919)).
Miary per bieg (t ≥ 20 s): max |rel_z − 2| (rel_z prawdziwe = z_intruza − z_drona, NED), zdarzenie „ucieczka wysokości”
|rel_z − 2| > 8 (pierwsza chwila, kierunek: + = dron wyżej), dystans po zdarzeniu (max, na końcu); max dystans prawdziwy
i z cech; max promień drona; najmniejsza składowa komendy sieci ku celowi (z cech) przy dystansie z cech ≥ 10.5 / 11 / 12 m.
`log_idx`: zapis per tick dla wskazanych indeksów (pozycja intruza, stan drona p v, cechy surowe, stan sieci, komenda).
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pl_naped as PN                                    # noqa: E402
import pl_intruz as PI                                   # noqa: E402

OUT = PN.OUT
T_OC, PROG = 20.0, 8.0


def wiek_med():
    return float(json.load(open(os.path.join(OUT, "r2b.json")))["wiek_tracka"]["mediana"])


def bieg(rodzina, naped, szum, vmax, wariant="siec", B=900, ziarno=0, T=300.0, param=None, log_idx=None, napedy=None, zbierz=0):
    napedy = napedy or json.load(open(os.path.join(OUT, "r3_naped.json")))["napedy"]
    rng = np.random.default_rng(ziarno)
    I = PI.Intruz(rodzina, B, vmax, rng, param)
    sz = PN.Szum(B, np.random.default_rng(ziarno + 7919), wl=szum)
    p0 = np.tile([0.0, 0.0, -12.0], (B, 1))
    P = PN.Petla(B, napedy[naped], p0, np.zeros((B, 3)), wiek_med(), sz, wariant)
    n = int(round(T / PN.DT))
    maxz = np.zeros(B); t_ev = np.full(B, np.nan); kier = np.zeros(B)
    dmax = np.zeros(B); dfmax = np.zeros(B); rmax = np.zeros(B)
    ku = {g: np.full(B, np.inf) for g in (10.5, 11.0, 12.0)}
    d_po_max = np.full(B, np.nan); d_kon = np.zeros(B)
    logi = {i: [] for i in (log_idx or [])}
    q = I.pos3()
    zb_x, zb_h = [], []
    for k in range(n):
        t = k * PN.DT
        c = P.krok(q)
        x = P.x
        relz = q[:, 2] - P.p[:, 2]
        d = np.hypot(*(q[:, :2] - P.p[:, :2]).T)
        df = np.hypot(x[:, 0], x[:, 1])
        if t >= T_OC:
            dz = np.abs(relz - 2.0)
            maxz = np.maximum(maxz, dz)
            nowe = np.isnan(t_ev) & (dz > PROG)
            t_ev[nowe] = t; kier[nowe] = np.sign(relz[nowe] - 2.0)
            po = ~np.isnan(t_ev)
            d_po_max[po] = np.fmax(d_po_max[po], d[po])
            dmax = np.maximum(dmax, d); dfmax = np.maximum(dfmax, df)
            rmax = np.maximum(rmax, np.hypot(P.p[:, 0], P.p[:, 1]))
            kk = (c[:, 0] * x[:, 0] + c[:, 1] * x[:, 1]) / np.maximum(df, 1e-9)
            for g in ku:
                s = df >= g
                ku[g][s] = np.minimum(ku[g][s], kk[s])
        if zbierz and t >= T_OC and k % zbierz == 0:          # stany do opisu Ω (R7): cechy surowe i stan PRZED krokiem
            zb_x.append(P.x.copy()); zb_h.append(P.h_przed.copy())
        for i in logi:
            logi[i].append(np.concatenate([[t], q[i], P.p[i], P.v[i], x[i], P.h[i], c[i]]))
        q = I.krok(P.p)
    d_kon[:] = d
    res = {"max_dz": maxz, "t_ev": t_ev, "kier": kier, "d_max": dmax, "d_cech_max": dfmax, "r_max": rmax,
           "ku_10_5": ku[10.5], "ku_11": ku[11.0], "ku_12": ku[12.0], "d_po_max": d_po_max, "d_kon": d_kon}
    if zbierz:
        res["stany_x"], res["stany_h"] = np.concatenate(zb_x), np.concatenate(zb_h)
    if log_idx:
        res["logi"] = {i: np.array(v) for i, v in logi.items()}
    return res


KOLUMNY_LOGU = (["t", "qN", "qE", "qD", "pN", "pE", "pD", "vN", "vE", "vD", "rel_x", "rel_y", "rel_z", "own_vn", "own_ve", "own_vd",
                 "age", "valid"] + [f"h{i}" for i in range(20)] + ["cN", "cE", "cD"])


if __name__ == "__main__":
    import time
    a = time.time()
    r = bieg("ucieczka", "N", True, 1.0, B=900, ziarno=1, T=60.0)
    print(time.time() - a, np.nanmax(r["max_dz"]), np.isfinite(r["t_ev"]).sum())
