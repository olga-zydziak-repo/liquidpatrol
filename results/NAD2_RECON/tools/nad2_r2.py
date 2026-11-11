#!/usr/bin/env python3
"""results/NAD2_RECON/tools/nad2_r2.py — PROMPT_NAD2_S0 R2: przyrost błędu własnego EKF na horyzoncie τ (składnik G; 0 bootów).

e(t) = p_EKF(t) − GT(t) na osi timestamp_sample vehicle_local_position (wyciąg ULG; R1: próbka EKF ticku = próbka VLP), GT z trace
interpolowane na ten sam czas sim; okno [flaga cs_gnss_pos → 0, zejście planowe], 12 cięć S4. Siatka 0.01 s (interpolacja liniowa).
Przyrost |e(t+τ) − e(t)| po wszystkich t (okno przesuwne), poziomo (NE) i 3D, dla τ ∈ TAU; rozkład per boot i łącznie
(p50 / p95 / p99 / p99.9 / max), krzywa przekroczeń (liczba okien > 0.8·max i > 0.9·max), zależność od przyspieszenia
poziomego GT (max |a| w oknie: < 1, 1–2, ≥ 2 m/s²).
Do R5: G_kum(τ_kraw) = max po t i po τ' ≤ τ_kraw przyrostu (maksimum bieżące) dla krawędzi przedziałów R5.
Wyjście: results/NAD2_RECON/r2_przyrost.json.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nad2_dane as D

DT = 0.01
TAU = [0.25, 0.45, 0.65, 0.85, 1.05, 2, 3, 5, 10, 22]
KRAW = [0.25, 0.45, 0.65, 0.85, 1.05] + [float(k) for k in range(2, 23)]


def szereg(b):
    t1 = b.zp[b.denial["episode_id"]]
    g = np.arange(b.t_flag, t1, DT)
    e = b.ekf_w(g) - b.gt(g)
    a = np.gradient(np.gradient(b.gt(g)[:, :2], DT, axis=0), DT, axis=0)
    a_h = np.linalg.norm(a, axis=1)
    # wygładzenie |a| (GT 33 Hz, druga pochodna szumi): średnia krocząca 0.05 s
    k = 5
    a_h = np.convolve(a_h, np.ones(k) / k, mode="same")
    return g, e, a_h


def kw(x):
    x = np.asarray(x)
    return {"n": int(x.size), "p50": round(float(np.quantile(x, .5)), 4), "p95": round(float(np.quantile(x, .95)), 4),
            "p99": round(float(np.quantile(x, .99)), 4), "p99.9": round(float(np.quantile(x, .999)), 4), "max": round(float(x.max()), 4)}


def main():
    out = {"dt_siatki_s": DT, "tau": TAU, "boot": {}, "lacznie": {}}
    acc = {t: {"h": [], "3d": [], "a": []} for t in TAU}
    gk_h = {k: 0.0 for k in KRAW}
    gk_3 = {k: 0.0 for k in KRAW}
    gk_boot = {}
    for n in D.CIECIA_S4:
        b = D.Boot(n)
        g, e, a_h = szereg(b)
        ob = {"okno": [round(g[0], 3), round(g[-1], 3)], "n": int(g.size), "tau": {}}
        lag_max = int(round(max(KRAW) / DT))
        run_h = np.zeros(g.size); run_3 = np.zeros(g.size)
        gb = {}
        kr = sorted(KRAW)
        ki = 0
        for L in range(1, lag_max + 1):
            d = e[L:] - e[:-L]
            dh = np.hypot(d[:, 0], d[:, 1]); d3 = np.linalg.norm(d, axis=1)
            m = dh.size
            run_h[:m] = np.maximum(run_h[:m], dh); run_3[:m] = np.maximum(run_3[:m], d3)
            tau = L * DT
            while ki < len(kr) and tau >= kr[ki] - 1e-9:
                gb[kr[ki]] = (round(float(run_h[:m].max()), 4), round(float(run_3[:m].max()), 4))
                ki += 1
            for t in TAU:
                if L == int(round(t / DT)):
                    amax = np.array([a_h[i:i + L + 1].max() for i in range(m)]) if t <= 1.05 else None
                    ob["tau"][str(t)] = {"poziomo": kw(dh), "3d": kw(d3),
                                         "n_gt_0.8max_h": int((dh > 0.8 * dh.max()).sum()), "n_gt_0.9max_h": int((dh > 0.9 * dh.max()).sum())}
                    if amax is not None:
                        ob["tau"][str(t)]["max_h_wg_a"] = {lab: (round(float(dh[sel].max()), 4) if sel.any() else None)
                                                          for lab, sel in (("a<1", amax < 1), ("1<=a<2", (amax >= 1) & (amax < 2)), ("a>=2", amax >= 2))}
                    acc[t]["h"].append(dh); acc[t]["3d"].append(d3)
                    if amax is not None:
                        acc[t]["a"].append(amax)
        gk_boot[n] = {str(k): v for k, v in gb.items()}
        for k, (h, d3) in gb.items():
            gk_h[k] = max(gk_h[k], h); gk_3[k] = max(gk_3[k], d3)
        out["boot"][n] = ob
        print(n, {t: ob["tau"][str(t)]["poziomo"]["max"] for t in (0.25, 1.05, 22)}, flush=True)
    for t in TAU:
        h = np.concatenate(acc[t]["h"]); d3 = np.concatenate(acc[t]["3d"])
        o = {"poziomo": kw(h), "3d": kw(d3), "n_gt_0.8max_h": int((h > 0.8 * h.max()).sum()), "n_gt_0.9max_h": int((h > 0.9 * h.max()).sum())}
        if acc[t]["a"]:
            a = np.concatenate(acc[t]["a"])
            o["wg_a"] = {lab: ({"n": int(sel.sum()), "max_h": round(float(h[sel].max()), 4), "p99_h": round(float(np.quantile(h[sel], .99)), 4)}
                               if sel.any() else None) for lab, sel in (("a<1", a < 1), ("1<=a<2", (a >= 1) & (a < 2)), ("a>=2", a >= 2))}
        out["lacznie"][str(t)] = o
    out["G_kum"] = {"poziomo": {str(k): gk_h[k] for k in KRAW}, "3d": {str(k): gk_3[k] for k in KRAW}, "per_boot": gk_boot,
                    "opis": "max po t i τ' ≤ krawędź przedziału (maksimum bieżące), okno [flaga, zejście] 12 cięć S4"}
    json.dump(out, open(os.path.join(D.OUT, "r2_przyrost.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({t: (out["lacznie"][str(t)]["poziomo"], out["lacznie"][str(t)].get("wg_a")) for t in TAU}, ensure_ascii=False)[:3500])
    print("G_kum h", out["G_kum"]["poziomo"])


if __name__ == "__main__":
    main()
