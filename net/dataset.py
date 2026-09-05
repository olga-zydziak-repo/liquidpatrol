#!/usr/bin/env python3
"""net/dataset.py — zbiór treningowy nogi sieci (PRE_NET N2).

WYŁĄCZNIE 114 udanych demonstracji D6 (pierwsza ważna V2′ per scenariusz). Wejścia = `bench.features`
(IMPORT, nigdy kopia — SR-2, zero rozjazdu train/flight). Cel = `cmd_v_ned` (3D). Wykluczenia: ticki
stall=1 i faza reset (w praktyce 0 — D0 §4). Podział ZASZYTY (nie CLI): TEST=seed%4==0 (4,8), VAL=seed 2,
TRAIN=reszta. Ziarna, nie flagi — żeby nie dało się „przypadkiem" zmienić (N2).

Formaty:
- sekwencje (NCP): `episodes(split)` → lista (sid, X[Ti,8], Y[Ti,3]); `batched(eps)` → (X[T,B,8], Y, mask).
- okna (MLP): `windows(split, k=5)` → (X[N,40], Y[N,3]) z zero-paddingiem startu PER epizod.
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from bench.features import features            # SR-2: import, nie kopia
from net.d0_dataset import resolve_first_valid, split_of, CAMP


def _episode_rows(boot, sid, attempt):
    """Wiersze demo epizodu (sid,attempt) z bootu, w kolejności tick, po wykluczeniu stall=1 i reset."""
    path = os.path.join(CAMP, boot, "demo.jsonl")
    rows = []
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        if r.get("scenario_id") != sid or r.get("attempt") != attempt:
            continue
        if int(r.get("stall", 0)) == 1 or r.get("phase") == "reset":
            continue
        rows.append(r)
    rows.sort(key=lambda r: r["tick"])
    return rows


def _load_all():
    """Zwraca {split: [(sid, X[Ti,8], Y[Ti,3])]} dla 114 sukcesów."""
    first = resolve_first_valid()
    succ = {sid: v for sid, v in first.items() if v["success_D6"]}
    out = {"TRAIN": [], "VAL": [], "TEST": []}
    for sid in sorted(succ):
        v = succ[sid]
        rows = _episode_rows(v["boot"], sid, v["attempt"])
        if not rows:
            continue
        X = np.array([features(r) for r in rows], dtype=np.float64)     # (Ti,8)
        Y = np.array([r["cmd_v_ned"] for r in rows], dtype=np.float64)  # (Ti,3)
        out[split_of(v["seed"])].append((sid, X, Y))
    return out


_CACHE = None


def load():
    global _CACHE
    if _CACHE is None:
        _CACHE = _load_all()
    return _CACHE


def episodes(split):
    return load()[split]


def batched(eps):
    """Lista (sid,X,Y) → (X[T,B,8], Y[T,B,3], mask[T,B]) z paddingiem do T_max."""
    B = len(eps)
    T = max(x.shape[0] for _, x, _ in eps)
    X = np.zeros((T, B, 8)); Y = np.zeros((T, B, 3)); M = np.zeros((T, B))
    for j, (_, x, y) in enumerate(eps):
        Ti = x.shape[0]
        X[:Ti, j, :] = x; Y[:Ti, j, :] = y; M[:Ti, j] = 1.0
    return X, Y, M


def windows(split, k=5):
    """Okna k ticków z zero-paddingiem startu PER epizod. Zwraca (X[N,40], Y[N,3])."""
    Xs, Ys = [], []
    for _, x, y in episodes(split):
        Ti = x.shape[0]
        for i in range(Ti):
            win = np.zeros((k, 8))
            for j in range(k):
                idx = i - (k - 1) + j
                if idx >= 0:
                    win[j] = x[idx]
            Xs.append(win.reshape(-1))
            Ys.append(y[i])
    return np.array(Xs), np.array(Ys)


AGE_CAP = 1.0          # track_age_s: sentinel 1e9 (track_valid=0) → CAP; valid age max ~0.46s (D0)


def clip_age(X):
    """Kanoniczny preprocessing cechy track_age_s: min(age, AGE_CAP). Stosowany IDENTYCZNIE train/rollout/flight
    (deterministyczny adapter wejścia sieci — features.py NIETKNIĘTE, SR-2). Zwraca kopię."""
    Xc = np.array(X, dtype=np.float64, copy=True)
    if Xc.ndim == 1:
        Xc[6] = min(Xc[6], AGE_CAP)
    else:
        Xc[..., 6] = np.minimum(Xc[..., 6], AGE_CAP)
    return Xc


def standardize(X, mean, std):
    return (clip_age(X) - mean) / std


def feature_stats():
    """Statystyki cech na TRAIN PO clip_age (do standaryzacji wejść). Zwraca (mean[8], std[8])."""
    allX = clip_age(np.concatenate([x for _, x, _ in episodes("TRAIN")], axis=0))
    mean = allX.mean(0)
    std = allX.std(0)
    std[std < 1e-6] = 1.0
    return mean, std


if __name__ == "__main__":
    d = load()
    for s in ("TRAIN", "VAL", "TEST"):
        eps = d[s]
        nrows = sum(x.shape[0] for _, x, _ in eps)
        print(f"{s}: epizody={len(eps)} wiersze={nrows}")
    m, sd = feature_stats()
    print("feat mean", np.round(m, 3))
    print("feat std ", np.round(sd, 3))
