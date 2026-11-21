#!/usr/bin/env python3
"""results/BLIZNIAK_RECON/tools/bz_przeslanki.py — Δ_B i przesłanki P1–P3 na lotach TEACH (PROMPT_BLIZNIAK_S0 §5, §6; 0 bootów).

15 lotów pl_dane.loty() (cache PĘTLI, READ-ONLY), cechy z replayu pl_siec.replay (te same, które dostała sieć; ticki bez kroku
sieci — utrata / kwarantanna — nie mają cech). Tick misji: misja > 0 ∧ krok sieci ∧ t − t(i0) ≥ 1 s.
Sytuacja s = (d, θ, v_r, v_t) z cech; zmiana na tick między kolejnymi tickami (tick + 1) z krokiem sieci, θ zawinięte.
Δ_B: 99.9. percentyl |zmiany| d i v_t na 10 lotach uczących (wszystkie poza p03, p07, p09, p12, p13); reszta = Δ_A.
P1: zmiana na tick w Δ_A / Δ_B (wszystkie 4 współrzędne; tick bez poprzednika = poza). P2: d ∈ [4, 15], |v_xy| ≤ 3.2.
P3: wiek ∈ [0.024, 0.15], track ważny. Ocena na 5 lotach testowych; obok na wszystkich 15.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, "/home/olga/projects/liquidpatrol/results/PETLA_RECON/tools")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pl_dane as PD                                     # noqa: E402
import pl_siec as PS                                     # noqa: E402
import bz_dowod as BD                                    # noqa: E402

OUT = "/home/olga/projects/liquidpatrol/results/BLIZNIAK_RECON"
TEST = ("p03", "p07", "p09", "p12", "p13")


def syt(x):
    d = np.hypot(x[:, 0], x[:, 1]); th = np.arctan2(x[:, 1], x[:, 0])
    ux, uy = x[:, 0] / np.maximum(d, 1e-9), x[:, 1] / np.maximum(d, 1e-9)
    return np.stack([d, th, x[:, 3] * ux + x[:, 4] * uy, -x[:, 3] * uy + x[:, 4] * ux], 1)


def main():
    rows = []
    for d in PD.loty():
        L = PD.wczytaj(d); R = PS.replay(L)
        i0 = int(np.argmax(R["infer"])); tt = L["t"] - L["t"][i0]
        m = (L["misja"] > 0) & R["infer"] & (tt >= 1.0)
        idx = np.where(m)[0]
        x = R["x"][idx]; s = syt(x)
        prev = idx - 1
        okp = (prev >= 0) & R["infer"][np.maximum(prev, 0)] & (L["tick"][np.maximum(prev, 0)] == L["tick"][idx] - 1)
        sp = syt(np.nan_to_num(R["x"][np.maximum(prev, 0)]))
        ds = np.abs(s - sp); ds[:, 1] = np.abs((s[:, 1] - sp[:, 1] + np.pi) % (2 * np.pi) - np.pi)
        ds[~okp] = np.inf
        rows.append({"lot": str(L["nazwa"]), "ds": ds, "d": s[:, 0], "v": np.hypot(x[:, 3], x[:, 4]),
                     "wiek": L["age"][idx], "valid": L["valid"][idx] > 0})
    ucz = [r for r in rows if r["lot"][:3] not in TEST]; tst = [r for r in rows if r["lot"][:3] in TEST]
    dsu = np.concatenate([r["ds"] for r in ucz]); dsu = dsu[np.isfinite(dsu).all(1)]
    dB = BD.DELTA_A.copy()
    dB[0] = float(np.percentile(dsu[:, 0], 99.9)); dB[3] = float(np.percentile(dsu[:, 3], 99.9))
    out = {"delta_A": BD.DELTA_A.tolist(), "delta_B": dB.tolist(),
           "percentyle_uczace_p99_9": np.percentile(dsu, 99.9, axis=0).tolist(), "max_uczace": dsu.max(0).tolist(),
           "ticki_uczace": int(len(dsu))}
    for nm, grp in (("test", tst), ("wszystkie", rows)):
        ds = np.concatenate([r["ds"] for r in grp]); dd = np.concatenate([r["d"] for r in grp]); vv = np.concatenate([r["v"] for r in grp])
        wk = np.concatenate([r["wiek"] for r in grp]); va = np.concatenate([r["valid"] for r in grp])
        p1a = (ds <= BD.DELTA_A).all(1); p1b = (ds <= dB).all(1)
        p2 = (dd >= 4.0) & (dd <= 15.0) & (vv <= 3.2)
        p3 = (wk >= 0.024) & (wk <= 0.15) & va
        brak = ~np.isfinite(ds).all(1)
        out[nm] = {"ticki": int(len(ds)), "bez_poprzednika": int(brak.sum()),
                   "P1_A": float(p1a.mean()), "P1_B": float(p1b.mean()), "P2": float(p2.mean()), "P3": float(p3.mean()),
                   "P1A_P2_P3": float((p1a & p2 & p3).mean()), "P1B_P2_P3": float((p1b & p2 & p3).mean()),
                   "przekroczenia_A_per_wspolrzedna": [float((ds[:, i] > BD.DELTA_A[i]).mean()) for i in range(4)],
                   "zmiana_d_p99_9_max": [float(np.percentile(ds[np.isfinite(ds[:, 0]), 0], 99.9)), float(ds[np.isfinite(ds[:, 0]), 0].max())],
                   "wiek_gt_0_15": float((wk > 0.15).mean()), "d_zakres": [float(dd.min()), float(dd.max())], "v_max": float(vv.max())}
    json.dump(out, open(os.path.join(OUT, "r4_przeslanki.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
