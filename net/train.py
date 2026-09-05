#!/usr/bin/env python3
"""net/train.py — trening ramienia (PRE_NET N2). Adam + MSE; selekcja checkpointu WYŁĄCZNIE na VAL (ziarno 2).

Hiperparametry z `net/train_config.json` (ZAMROŻONE w N-B1). Standaryzacja wejść ze statystyk TRAIN
(po clip_age) — zapisana w modelu (rollout/lot stosują identycznie). Krzywe train/VAL → curves.json.
Zero SITL, zero dotykania TEST (SR-3: TEST tylko w rollout_eval po zamknięciu selekcji).

Użycie: python -m net.train ncp|mlp
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from net import dataset as D
from net.models import TinyMLP, NCP20

CFG = json.load(open(os.path.join(ROOT, "net", "train_config.json")))


class Adam:
    def __init__(self, params, lr, b1=0.9, b2=0.999, eps=1e-8):
        self.lr = lr; self.b1 = b1; self.b2 = b2; self.eps = eps
        self.m = {k: np.zeros_like(v) for k, v in params.items()}
        self.v = {k: np.zeros_like(v) for k, v in params.items()}
        self.t = 0

    def step(self, params, grads, clip=None):
        self.t += 1
        if clip:
            tot = np.sqrt(sum(float(np.sum(g * g)) for g in grads.values()))
            scale = clip / (tot + 1e-12) if tot > clip else 1.0
        else:
            scale = 1.0
        for k in params:
            g = grads[k] * scale
            self.m[k] = self.b1 * self.m[k] + (1 - self.b1) * g
            self.v[k] = self.b2 * self.v[k] + (1 - self.b2) * (g * g)
            mh = self.m[k] / (1 - self.b1 ** self.t)
            vh = self.v[k] / (1 - self.b2 ** self.t)
            params[k] -= self.lr * mh / (np.sqrt(vh) + self.eps)


def _std(X, mean, sd):
    return (X - mean) / sd


# ------------------------------------------------------------------- MLP
def _prep_windows(X, k, mean, sd):
    """X:(N,k*8) → clip_age i standaryzacja PER blok 8, zwraca (N,k*8). Padding startowy (zera) też jest
    clip'owany/standaryzowany spójnie (jak realne wejście z zerowym wektorem cech)."""
    N = X.shape[0]
    Xb = X.reshape(N, k, 8)
    Xb = D.clip_age(Xb)                       # clip col 6 w każdym bloku
    Xb = (Xb - mean) / sd                     # broadcast (8,) po ostatniej osi
    return Xb.reshape(N, k * 8)


def train_mlp():
    c = CFG["mlp"]; vmax = CFG["vmax"]
    mean, sd = D.feature_stats()
    Xtr, Ytr = D.windows("TRAIN", k=c["k"]); Xtr = _prep_windows(Xtr, c["k"], mean, sd)
    Xva, Yva = D.windows("VAL", k=c["k"]); Xva = _prep_windows(Xva, c["k"], mean, sd)
    m = TinyMLP(vmax, hidden=c["hidden"], seed=c["seed"])
    m.input_mean = mean; m.input_std = sd
    opt = Adam(m.params(), c["lr"], c["beta1"], c["beta2"])
    rng = np.random.RandomState(c["seed"])
    N = Xtr.shape[0]; bs = c["batch"]
    curves = {"train": [], "val": []}
    best = {"val": 1e18, "params": None}
    for ep in range(c["epochs"]):
        idx = rng.permutation(N)
        tl = 0.0; nb = 0
        for s in range(0, N, bs):
            b = idx[s:s + bs]
            Xb, Yb = Xtr[b], Ytr[b]
            y, cache = m.forward(Xb, cache=True)
            d = y - Yb
            tl += np.mean(d * d); nb += 1
            dY = (2.0 / (Xb.shape[0] * 3)) * d
            opt.step(m.params(), m.grads(cache, dY), clip=c["grad_clip"])
        yv = m.forward(Xva); vl = float(np.mean((yv - Yva) ** 2))
        curves["train"].append(tl / nb); curves["val"].append(vl)
        if vl < best["val"]:
            best = {"val": vl, "params": {k: v.copy() for k, v in m.params().items()}, "epoch": ep}
    m.set_params(best["params"])
    return m, curves, best


# ------------------------------------------------------------------- NCP
def train_ncp():
    c = CFG["ncp"]; vmax = CFG["vmax"]
    mean, sd = D.feature_stats()
    tr = D.episodes("TRAIN"); va = D.episodes("VAL")
    Xtr, Ytr, Mtr = D.batched(tr); Xtr = _std(D.clip_age(Xtr), mean, sd)
    Xva, Yva, Mva = D.batched(va); Xva = _std(D.clip_age(Xva), mean, sd)
    m = NCP20(vmax, hidden=c["hidden"], bb=c["bb"], seed=c["seed"])
    m.input_mean = mean; m.input_std = sd
    opt = Adam(m.params(), c["lr"], c["beta1"], c["beta2"])
    curves = {"train": [], "val": []}
    best = {"val": 1e18, "params": None}
    ntr = Mtr.sum() * 3; nva = Mva.sum() * 3
    for ep in range(c["epochs"]):
        Yh, caches = m.forward_seq(Xtr, Mtr)
        d = (Yh - Ytr) * Mtr[:, :, None]
        tl = float(np.sum(d * d) / ntr)
        dY = (2.0 / ntr) * d
        opt.step(m.params(), m.grads_seq(caches, dY, Mtr), clip=c["grad_clip"])
        Yv, _ = m.forward_seq(Xva, Mva)
        dv = (Yv - Yva) * Mva[:, :, None]
        vl = float(np.sum(dv * dv) / nva)
        curves["train"].append(tl); curves["val"].append(vl)
        if vl < best["val"]:
            best = {"val": vl, "params": {k: v.copy() for k, v in m.params().items()}, "epoch": ep}
    m.set_params(best["params"])
    return m, curves, best


def main(arm):
    outdir = os.path.join(ROOT, "results", "NET", arm)
    os.makedirs(outdir, exist_ok=True)
    if arm == "mlp":
        m, curves, best = train_mlp()
    elif arm == "ncp":
        m, curves, best = train_ncp()
    else:
        raise SystemExit("arm: ncp|mlp")
    m.save(os.path.join(outdir, "model.npz"))
    json.dump(curves, open(os.path.join(outdir, "curves.json"), "w"))
    print(f"[{arm}] params={m.param_count()} best_val_epoch={best['epoch']} "
          f"best_val_mse={best['val']:.5f} final_train_mse={curves['train'][-1]:.5f}")
    return m, curves, best


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "ncp")
