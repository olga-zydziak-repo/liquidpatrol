#!/usr/bin/env python3
"""net/eval_arm.py — ewaluacja ramienia po zamknięciu selekcji (PROMPT_NET_S1 I2 kroki 3–4).

TEST dotykany RAZ (SR-3): (3) RMS(v̂ − v_nauczyciel) per epizod TEST — mediana+IQR (DIAGNOSTYKA, N3(ii));
(4) bramka N3(i): rollout FEED-B na 12 komórek × ziarna TEST → analog-D6 → werdykt ≥10/12.
Zapisuje results/NET/<arm>/eval.json. Zero SITL, frozen import-only.

Użycie: python -m net.eval_arm ncp|mlp
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
from net.rollout_eval import gate_arm


def _load(arm):
    p = os.path.join(ROOT, "results", "NET", arm, "model.npz")
    return (NCP20 if arm == "ncp" else TinyMLP).load(p)


def test_rms_per_episode(model):
    """RMS(v̂−v_nauczyciel) per epizod TEST (teacher-forced, open-loop na realnych cechach). Lista (sid, rms)."""
    mean, sd = model.input_mean, model.input_std
    out = []
    for sid, X, Y in D.episodes("TEST"):
        Xs = (D.clip_age(X) - mean) / sd
        if model.ARM == "ncp":
            Xb = Xs[:, None, :]                              # (T,1,8)
            Yh, _ = model.forward_seq(Xb, np.ones((Xb.shape[0], 1)))
            pred = Yh[:, 0, :]
        else:
            k = model.K
            wins = []
            for i in range(Xs.shape[0]):
                w = np.zeros((k, 8))
                for j in range(k):
                    idx = i - (k - 1) + j
                    if idx >= 0:
                        w[j] = Xs[idx]
                wins.append(w.reshape(-1))
            pred = model.forward(np.array(wins))
        rms = float(np.sqrt(np.mean((pred - Y) ** 2)))
        out.append((sid, rms))
    return out


def main(arm):
    model = _load(arm)
    rms = test_rms_per_episode(model)
    vals = sorted(r for _, r in rms)
    n = len(vals)
    median = vals[n // 2]
    q1 = vals[n // 4]; q3 = vals[(3 * n) // 4]
    table, n_pass = gate_arm(model)
    verdict = "PASS" if n_pass >= 10 else "FAIL"
    out = {"arm": arm, "param_count": int(model.param_count()),
           "test_rms": {"median": round(median, 4), "iqr": [round(q1, 4), round(q3, 4)],
                        "min": round(vals[0], 4), "max": round(vals[-1], 4),
                        "per_episode": [{"sid": s, "rms": round(r, 4)} for s, r in rms]},
           "gate_N3i": {"n_pass": n_pass, "n_cells": len(table), "verdict": verdict, "table": table}}
    outp = os.path.join(ROOT, "results", "NET", arm, "eval.json")
    json.dump(out, open(outp, "w"), indent=2)
    print(f"[{arm}] TEST RMS median={median:.4f} IQR[{q1:.4f},{q3:.4f}] | bramka N3(i) {n_pass}/12 = {verdict}")
    for r in table:
        seeds = " ".join(f"s{p['seed']}:{'OK' if p['ok'] else 'x'}(entry={p['t_entry']},frac={p['frac']},dmin={p['d_min']})"
                         for p in r["per_seed"])
        print(f"  {r['cell']} v={r['v_intr']} brg={r['bearing']:>3}: {'PASS' if r['cell_ok'] else 'FAIL'}  {seeds}")
    return out


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "ncp")
