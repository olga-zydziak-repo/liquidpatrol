#!/usr/bin/env python3
"""results/WK2_RECON/tools/wk2_k.py — pomiar efektywnego liniowego współczynnika oporu k [1/s] z bilansu sił
poziomych (PROMPT_WK2_S0 §R3; metoda jak ANEKS_WK-1 §1.3), 0 bootów — czyta istniejące logi.

Model (wiatr 0, NED): a = g·ẑ + (T/m)·t + D,  t = −R[:,2] (oś ciągu w NED z vehicle_attitude),
  T/m z równania pionowego: a_z = g + (T/m)·t_z  ⇒  T/m = (a_z − g)/t_z,
  opór poziomy D_h = a_h − (T/m)·t_h  ≈  −k·v_h (+ b, stały bias przyrządu).
Estymator: MNK k (bez wyrazu wolnego) oraz k z wyrazem wolnym (b_N, b_E); niepewność = bootstrap blokowy
po 2-sekundowych blokach (500 losowań, ziarno 0) → przedział 2.5–97.5%.
Dane: ulog vehicle_attitude (q), vehicle_local_position (vx, vy, ax, ay, az) — próbki LP jako oś czasu,
q najbliższe w czasie. Okno: wiersze demo.jsonl z phase == "orbit" (sterownik w orbicie) — granice
[t_sim_min, t_sim_max] ciągłych serii; most czasu t_sim·1e6 ≈ ulog us (lockstep; zweryfikowany w reconie WK
§R3: mediana |Δz| ≤ 0.0012 m). Próbki z |v_h| < 0.3 m/s odrzucone (brak informacji o k).
Dodatkowo: k w przedziałach |v_h| (test liniowości oporu w prędkości) i przechył w oknie orbity.
Zero miar misji.

Użycie: wk2_k.py <out.json> <katalog_boota>...
"""
import bisect
import json
import os
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, ROOT)
from r02.mti import quat_to_R  # noqa: E402

G = 9.80665
V_MIN = 0.3
BLOCK_S = 2.0


def load(ulog):
    from pyulog import ULog
    u = ULog(ulog, ["vehicle_attitude", "vehicle_local_position"])
    att = lp = None
    for d in u.data_list:
        if d.name == "vehicle_attitude" and att is None:
            att = (np.asarray(d.data["timestamp"], float), np.stack([d.data[f"q[{i}]"] for i in range(4)], 1))
        if d.name == "vehicle_local_position" and lp is None:
            lp = {k: np.asarray(d.data[k], float) for k in ("timestamp", "vx", "vy", "ax", "ay", "az")}
    return att, lp


def orbit_windows(demo):
    wins, cur = [], None
    for ln in open(demo):
        r = json.loads(ln)
        if r.get("phase") == "orbit":
            cur = [r["t_sim"], r["t_sim"]] if cur is None else [cur[0], r["t_sim"]]
        elif cur is not None:
            wins.append(cur); cur = None
    if cur is not None:
        wins.append(cur)
    return [w for w in wins if w[1] - w[0] > 5.0]


def fit(D, V, with_bias):
    if with_bias:
        # D_N = −k v_N + b_N ; D_E = −k v_E + b_E  (wspólne k)
        n = len(V)
        A = np.zeros((2 * n, 3)); y = np.concatenate([D[:, 0], D[:, 1]])
        A[:n, 0] = -V[:, 0]; A[n:, 0] = -V[:, 1]; A[:n, 1] = 1; A[n:, 2] = 1
        sol, *_ = np.linalg.lstsq(A, y, rcond=None)
        return float(sol[0]), [float(sol[1]), float(sol[2])]
    return float(-np.sum(D * V) / np.sum(V * V)), None


def measure(d):
    att, lp = load(os.path.join(d, "boot.ulg"))
    ats = att[0]
    wins = orbit_windows(os.path.join(d, "demo.jsonl"))
    Ds, Vs, Ts, TILT = [], [], [], []
    for lo, hi in wins:
        m = (lp["timestamp"] >= lo * 1e6) & (lp["timestamp"] <= hi * 1e6)
        for i in np.where(m)[0]:
            v = np.array([lp["vx"][i], lp["vy"][i]])
            if np.hypot(*v) < V_MIN:
                continue
            j = min(max(bisect.bisect_left(ats, lp["timestamp"][i]), 0), len(ats) - 1)
            R = quat_to_R(att[1][j])
            t = -R[:, 2]
            if t[2] > -0.5:
                continue
            Tm = (lp["az"][i] - G) / t[2]
            Ds.append(np.array([lp["ax"][i], lp["ay"][i]]) - Tm * t[:2])
            Vs.append(v); Ts.append(lp["timestamp"][i] / 1e6)
            TILT.append(float(np.degrees(np.arccos(np.clip(R[2, 2], -1.0, 1.0)))))
    if len(Vs) < 50:
        return {"boot": os.path.relpath(d, ROOT), "n": len(Vs), "blad": "za mało próbek"}
    D, V, T = np.array(Ds), np.array(Vs), np.array(Ts)
    k0, _ = fit(D, V, False)
    kb, b = fit(D, V, True)
    blocks = np.floor((T - T.min()) / BLOCK_S).astype(int)
    ub = np.unique(blocks)
    rng = np.random.RandomState(0)
    boot = []
    for _ in range(500):
        pick = rng.choice(ub, len(ub), replace=True)
        idx = np.concatenate([np.where(blocks == p)[0] for p in pick])
        boot.append(fit(D[idx], V[idx], True)[0])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    # liniowość w prędkości: k (z wyrazem wolnym) w przedziałach |v_h|
    sp = np.hypot(V[:, 0], V[:, 1])
    k_bins = {}
    for lo_v, hi_v in ((0.3, 1.0), (1.0, 1.5), (1.5, 2.0), (2.0, 3.5)):
        mm = (sp >= lo_v) & (sp < hi_v)
        if mm.sum() >= 200:
            k_bins[f"{lo_v}-{hi_v}"] = {"n": int(mm.sum()), "k": round(fit(D[mm], V[mm], True)[0], 4)}
    tl = np.sort(np.array(TILT))
    return {"boot": os.path.relpath(d, ROOT), "n": int(len(V)), "okna_orbity": len(wins),
            "k_w_przedzialach_v": k_bins,
            "przechyl_orbita_p50_p95": [round(float(np.median(tl)), 2), round(float(tl[int(0.95 * (len(tl) - 1))]), 2)],
            "v_h_p50": round(float(np.median(np.hypot(V[:, 0], V[:, 1]))), 3),
            "k_bez_wyrazu_wolnego": round(k0, 4), "k": round(kb, 4), "bias_NE_m_s2": [round(x, 4) for x in b],
            "k_ci95_bootstrap_blokowy": [round(float(lo), 4), round(float(hi), 4)]}


def main():
    out, dirs = sys.argv[1], sys.argv[2:]
    res = []
    for d in dirs:
        r = measure(os.path.abspath(d))
        res.append(r)
        print(json.dumps(r, ensure_ascii=False))
    json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
