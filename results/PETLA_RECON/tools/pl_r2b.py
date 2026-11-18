#!/usr/bin/env python3
"""results/PETLA_RECON/tools/pl_r2b.py — R2 cd. (PROMPT_PETLA_S0 §4): obwiednie cech i stanów (misja), PCA stanu, wiek tracka
i odpowiedź na wiek podmieniony, błąd wektora względnego i e_trk (pierwsze 30 s / reszta), czas korelacji błędu (szum do W2).
Wejście: r2_wektory.npz + dane lotów. Wyjście: results/PETLA_RECON/r2b.json, szum_rel.json (parametry AR(1) per oś)."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pl_dane as PD                                     # noqa: E402
import pl_siec as PS                                     # noqa: E402

OUT = os.path.join(PD.ROOT, "results/PETLA_RECON")
q = lambda x: {"p50": float(np.percentile(x, 50)), "p99": float(np.percentile(x, 99)), "max": float(np.max(x)), "n": int(len(x))}


def h_prev(W):
    """Stan przed tickiem: stan po poprzednim ticku inferencji tego samego lotu (poza inferencją stan zamrożony)."""
    hp = np.zeros_like(W["h"])
    hp[1:] = W["h"][:-1]
    nowy = np.r_[True, W["lot"][1:] != W["lot"][:-1]]
    hp[nowy] = 0.0
    return hp


def acf_czas(series_list, dt=0.05, max_lag=400):
    """Czas korelacji: lag, przy którym średnia ACF (po segmentach) spada poniżej 1/e."""
    acc, n = np.zeros(max_lag), np.zeros(max_lag)
    for s in series_list:
        s = s - s.mean()
        v = (s * s).mean()
        if len(s) < max_lag * 2 or v <= 0:
            continue
        for k in range(max_lag):
            acc[k] += (s[: len(s) - k] * s[k:]).mean() / v
            n[k] += 1
    a = acc / np.maximum(n, 1)
    k = int(np.argmax(a < 1 / np.e)) if (a < 1 / np.e).any() else max_lag
    return k * dt, a


def main():
    W = dict(np.load(os.path.join(OUT, "r2_wektory.npz"), allow_pickle=True))
    m = W["misja"].astype(bool)
    out = {}
    X, Hh = W["x"][m], W["h"][m]
    out["obwiednie_cech"] = {n: [float(X[:, i].min()), float(X[:, i].max())] for i, n in enumerate(PS.features.__globals__["FEATURE_NAMES"])}
    out["obwiednie_stanu"] = [[float(Hh[:, i].min()), float(Hh[:, i].max())] for i in range(PS.H)]
    ev = np.linalg.eigvalsh(np.cov(Hh.T))[::-1]
    out["pca_stanu_udzial_8"] = float(ev[:8].sum() / ev.sum())
    out["pca_stanu_udzialy"] = [float(x) for x in ev / ev.sum()]
    age = X[:, 6]
    out["wiek_tracka"] = dict(q(age), n_gt_0p15=int((age > 0.15).sum()), n_gt_0p5=int((age > 0.5).sum()),
                              mediana=float(np.median(age)), p95=float(np.percentile(age, 95)))
    # odpowiedź na wiek podmieniony (stan przed tickiem z lotu)
    hp = h_prev(W)[m]
    v0, _ = PS.krok(PS.norm(X), hp)
    rel = X[:, :2]
    d = np.hypot(rel[:, 0], rel[:, 1])
    u = rel / np.maximum(d[:, None], 1e-9)
    odp = {}
    for a_ in (0.2, 0.5, 1.0):
        Xa = X.copy(); Xa[:, 6] = a_
        va, _ = PS.krok(PS.norm(Xa), hp)
        ku = (va[:, :2] * u).sum(1)
        s9 = d >= 9.0
        odp[str(a_)] = {"min_ku_d_ge_9": float(ku[s9].min()), "p1_ku_d_ge_9": float(np.percentile(ku[s9], 1)),
                        "dvd_p50": float(np.median(np.abs(va[:, 2] - v0[:, 2]))), "dvd_p99": float(np.percentile(np.abs(va[:, 2] - v0[:, 2]), 99)),
                        "dvd_max": float(np.abs(va[:, 2] - v0[:, 2]).max()), "n_d_ge_9": int(s9.sum())}
    out["odpowiedz_wiek"] = odp
    out["regresja_v0_vs_log"] = float(np.abs(v0 - W["v"][m]).max())
    # błąd wektora względnego i e_trk (ze wszystkich lotów, misja, tick inferencji)
    t30 = W["t_od_inf"][m] < 30.0
    out["rel_err_h"] = {"pierwsze_30s": q(W["rel_err"][m][t30]), "reszta": q(W["rel_err"][m][~t30])}
    out["etrk_h"] = {"pierwsze_30s": q(W["etrk"][m][t30]), "reszta": q(W["etrk"][m][~t30])}
    # szum per oś (po 30 s) i czas korelacji — z pełnych szeregów lotów (ciągłe odcinki misji z inferencją)
    serie = {0: [], 1: [], 2: []}
    wart = {0: [], 1: [], 2: []}
    for d_ in PD.loty():
        L = PD.wczytaj(d_)
        R = PS.replay(L)
        s = L["misja"].astype(bool) & R["infer"]
        t0 = L["t"][R["infer"]][0]
        s &= (L["t"] - t0) >= 30.0
        e = (L["trk"] - L["net"]) - (L["intr"] - L["gt"])
        idx = np.where(s)[0]
        if len(idx) == 0:
            continue
        cuts = np.where(np.diff(idx) > 1)[0]
        for seg in np.split(idx, cuts + 1):
            for ax in range(3):
                serie[ax].append(e[seg, ax]); wart[ax].append(e[seg, ax])
    sz = {}
    for ax, nm in ((0, "N"), (1, "E"), (2, "D")):
        allv = np.concatenate(wart[ax])
        tc, a = acf_czas(serie[ax])
        sz[nm] = {"srednia": float(allv.mean()), "std": float(allv.std()), "p99_abs": float(np.percentile(np.abs(allv), 99)),
                  "max_abs": float(np.abs(allv).max()), "czas_korelacji_s": tc, "acf_0_2_5s": [float(a[0]), float(a[40]), float(a[100])]}
    out["szum_rel_po_30s"] = sz
    json.dump(sz, open(os.path.join(OUT, "szum_rel.json"), "w"), indent=1)
    json.dump(out, open(os.path.join(OUT, "r2b.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: out[k] for k in ("pca_stanu_udzial_8", "wiek_tracka", "odpowiedz_wiek", "regresja_v0_vs_log", "rel_err_h", "etrk_h", "szum_rel_po_30s")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
