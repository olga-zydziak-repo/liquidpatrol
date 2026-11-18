#!/usr/bin/env python3
"""results/PETLA_RECON/tools/pl_siec.py — krok sieci NCP-20 (zamrożone wagi, import) i replay lotów (PROMPT_PETLA_S0 §4).

Litera toru (READ-ONLY, numery wierszy): cechy bench/features.py:23-32 (rel = trk − own, own_v, age, valid); clip_age
net/dataset.py:104-112 (age ≤ AGE_CAP 1.0); normalizacja (x − mean)/std net_controller.py:87-88; krok NCP20.step_np
net/models.py:127-138 (CfC: h' = gate·g + (1−gate)·hh, y = tanh(·)·vmax); clip_v r03/controllers/common.py:10-16 (|v| ≤ 3.0,
skalowanie); utrata tracka (fd None ∨ ¬valid ∨ age > 1.0) ⇒ v = 0, krok sieci NIE wykonany, stan zamrożony
net_controller.py:106-111; kwarantanna K1 (FantomScan, fantom_scan.py: A invalid→valid, B skok > 5 m wobec migawki,
C 3.0 s) — delegat widzi „brak tracku”, stan sieci bez kroku; SkanScan / AkwScan zmieniają wyłącznie yaw w hold.
Sieć dostaje pozycję p_corr (teach_flight.py:671-677: own_net = rama.p_corr(own)), prędkość EKF (vel).
Wersja wsadowa `krok(xs, h)` dla symulacji (B równoległych biegów).
"""
import math
import os
import sys

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, ROOT)
from net.models import NCP20                             # noqa: E402
from bench.features import features                      # noqa: E402
from net.dataset import clip_age, AGE_CAP                # noqa: E402

V_MAX, TRACK_LOSS_S, TQ, DJUMP = 3.0, 1.0, 3.0, 5.0
M = NCP20.load(os.path.join(ROOT, "net/frozen/ncp.npz"))
MEAN, STD, H = M.input_mean, M.input_std, M.H


def norm(x):
    """x (..., 8) surowe cechy → znormalizowane (clip_age jak dataset.py:104)."""
    x = np.array(x, dtype=np.float64, copy=True)
    x[..., 6] = np.minimum(x[..., 6], AGE_CAP)
    return (x - MEAN) / STD


def krok(xs, h):
    """Wsad: xs (B,8) znormalizowane, h (B,H) → (v (B,3) po clip_v, h')."""
    y, h2, _ = M.step_np(xs, h)
    n = np.linalg.norm(y, axis=1, keepdims=True)
    s = np.where(n > V_MAX, V_MAX / np.maximum(n, 1e-12), 1.0)
    return y * s, h2


def replay(L):
    """Replay lotu L (pl_dane.wczytaj). Zwraca dict: v (T,3), infer (T,), h (T,H) po ticku, xs (T,8), x (T,8) surowe."""
    T = len(L["t"])
    h = np.zeros((1, H))
    v = np.zeros((T, 3)); infer = np.zeros(T, bool); hs = np.zeros((T, H)); xs_all = np.full((T, 8), np.nan); x_all = np.full((T, 8), np.nan)
    q, t_ref, snap, prev = True, None, None, None
    for i in range(T):
        valid, age = bool(L["valid"][i]), float(L["age"][i])
        if q:
            if t_ref is None:
                t_ref, snap, prev = L["t"][i], (L["trk"][i].copy() if valid else None), valid
            reason = None
            if valid and prev is False:
                reason = "A"
            elif valid and snap is not None and math.dist(L["trk"][i][:2], snap[:2]) > DJUMP:
                reason = "B"
            elif L["t"][i] - t_ref >= TQ:
                reason = "C"
            prev = valid
            if reason:
                q = False
        if (not q) and valid and age <= TRACK_LOSS_S:
            x = np.array(features({"own_pos_ned": L["net"][i], "own_vel_ned": L["vel"][i], "trk_pos_ned": L["trk"][i],
                                   "track_age_s": age, "track_valid": True}))
            xs = norm(x)
            vv, h = krok(xs[None], h)
            v[i], infer[i], xs_all[i], x_all[i] = vv[0], True, xs, x
        hs[i] = h[0]
    return {"v": v, "infer": infer, "h": hs, "xs": xs_all, "x": x_all}
