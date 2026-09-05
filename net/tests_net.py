#!/usr/bin/env python3
"""net/tests_net.py — testy N-B1 PRZED treningiem (PROMPT_NET_S1 I1). Zero SITL.

- liczności datasetu == D0 (114; 81/10/23)
- tożsamość cech: features(feature_state_from_row(row)) == features(row_state) bit-w-bit (jak E ławki)
- kontrakt 10⁴ na NIEtrenowanych sieciach: komponenty ≤ V_MAX (tanh×V_MAX) ∧ clip_v ⇒ |v|₂ ≤ V_MAX
- sanity rolloutu: wyrocznia w modelu punktowym = 12/12 (reprodukcja buildu ławki — test przyrządu)
- gradcheck numeryczny MLP i CfC (poprawność ręcznego backprop)
"""
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from bench.features import features
from bench.demo_logger import feature_state_from_row
from r03.controllers.common import clip_v
from net import dataset as D
from net.models import TinyMLP, NCP20
from net.rollout_eval import oracle_sanity_12, VMAX

D0 = json.load(open(os.path.join(ROOT, "results", "NET", "d0_dataset.json")))


def test_dataset_counts_match_d0():
    d = D.load()
    assert D0["n_success"] == 114, D0["n_success"]
    assert len(d["TRAIN"]) == D0["per_split"]["TRAIN"]["eps"] == 81
    assert len(d["VAL"]) == D0["per_split"]["VAL"]["eps"] == 10
    assert len(d["TEST"]) == D0["per_split"]["TEST"]["eps"] == 23
    for split in ("TRAIN", "VAL", "TEST"):
        rows = sum(x.shape[0] for _, x, _ in d[split])
        assert rows == D0["per_split"][split]["kept"], (split, rows)


def test_feature_identity_bit_exact():
    """Cechy z wiersza demo == cechy ze stanu (ta sama funkcja, dwie ścieżki) — bit-w-bit, jak E ławki."""
    # weź realny wiersz z demo pierwszego sukcesu
    import glob
    f = sorted(glob.glob(os.path.join(ROOT, "results", "BENCH", "campaign", "boot1", "demo.jsonl")))[0]
    row = json.loads(open(f).readline())
    st = feature_state_from_row(row)
    v1 = features(row)          # dict-path bezpośrednio z wiersza
    v2 = features(st)           # przez rekonstrukcję stanu
    assert v1 == v2, "features rozjazd wiersz vs stan"
    assert len(v1) == 8


def test_contract_10k_vmax_both_arms():
    for M in (TinyMLP(VMAX, seed=3), NCP20(VMAX, seed=3)):
        rng = np.random.RandomState(11)
        if M.ARM == "mlp":
            X = rng.randn(10000, M.K * 8) * 3.0
            Y = M.forward(X)
        else:
            h = np.zeros((10000, M.H))
            X = rng.randn(10000, 8) * 3.0
            Y, _, _ = M.step_np(X, h)
        # (a) saturacja architektoniczna: każdy komponent ≤ V_MAX
        assert np.all(np.abs(Y) <= VMAX + 1e-9), f"{M.ARM}: komponent > V_MAX"
        # (b) belt clip_v: |v|₂ ≤ V_MAX
        for i in range(0, 10000, 137):
            v = clip_v([float(Y[i, 0]), float(Y[i, 1]), float(Y[i, 2])], VMAX)
            n = (v[0] ** 2 + v[1] ** 2 + v[2] ** 2) ** 0.5
            assert n <= VMAX + 1e-6, f"{M.ARM}: |v|₂={n} > V_MAX"


def test_oracle_rollout_12_of_12():
    res = oracle_sanity_12()
    passed = sum(1 for _, ok in res if ok)
    assert passed == 12, f"model punktowy: wyrocznia {passed}/12 (≠ build ławki)"


def _mse_grad_mlp(m, X, Y):
    y, cache = m.forward(X, cache=True)
    N = X.shape[0]
    loss = np.mean((y - Y) ** 2)
    g = m.grads(cache, (2.0 / (N * 3)) * (y - Y))
    return loss, g


def test_gradcheck_mlp():
    m = TinyMLP(3.0, hidden=8, seed=1)
    rng = np.random.RandomState(0)
    X = rng.randn(6, 40); Y = rng.randn(6, 3) * 0.5
    _, g = _mse_grad_mlp(m, X, Y)
    eps = 1e-6; maxerr = 0.0
    for k in ("W1", "b1", "W2", "b2", "W3", "b3"):
        flat = m.params()[k].ravel(); gf = g[k].ravel()
        for i in rng.choice(flat.size, min(8, flat.size), replace=False):
            old = flat[i]; flat[i] = old + eps; lp, _ = _mse_grad_mlp(m, X, Y)
            flat[i] = old - eps; lm, _ = _mse_grad_mlp(m, X, Y); flat[i] = old
            maxerr = max(maxerr, abs((lp - lm) / (2 * eps) - gf[i]))
    assert maxerr < 1e-6, maxerr


def _mse_grad_ncp(m, X, Y, M):
    Yh, caches = m.forward_seq(X, M)
    n = M.sum() * 3
    d = (Yh - Y) * M[:, :, None]
    loss = np.sum(d * d) / n
    g = m.grads_seq(caches, (2.0 / n) * d, M)
    return loss, g


def test_gradcheck_ncp_bptt():
    m = NCP20(3.0, hidden=6, bb=6, seed=2)
    rng = np.random.RandomState(0)
    T, B = 7, 4
    X = rng.randn(T, B, 8); Y = rng.randn(T, B, 3) * 0.5
    M = np.ones((T, B)); M[5:, 0] = 0; M[6:, 1] = 0
    _, g = _mse_grad_ncp(m, X, Y, M)
    eps = 1e-6; maxerr = 0.0
    for k in m.params():
        flat = m.params()[k].ravel(); gf = g[k].ravel()
        for i in rng.choice(flat.size, min(6, flat.size), replace=False):
            old = flat[i]; flat[i] = old + eps; lp, _ = _mse_grad_ncp(m, X, Y, M)
            flat[i] = old - eps; lm, _ = _mse_grad_ncp(m, X, Y, M); flat[i] = old
            maxerr = max(maxerr, abs((lp - lm) / (2 * eps) - gf[i]))
    assert maxerr < 1e-6, maxerr


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_") and callable(f):
            f(); print(f"OK {n}")
    print("tests_net: ALL PASS")
