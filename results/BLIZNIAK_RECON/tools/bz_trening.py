#!/usr/bin/env python3
"""results/BLIZNIAK_RECON/tools/bz_trening.py — R1 trening ramion (PROMPT_BLIZNIAK_S0 §3; 0 bootów).

Przepis (jeden dla wszystkich ramion): start z wag Z (net/frozen/ncp.npz); dane, maska, standaryzacja i strata jak
net/train.train_ncp (TRAIN do uczenia, VAL do wyboru); Adam z net/train.py, lr 0.003, β 0.9 / 0.999, przycięcie 5.0;
900 epok pełnym wsadem; lr × 0.5 na początku epok 540 i 765. Po każdym kroku: b = B(W); cel = γ dla e ≥ 300, wcześniej
B₀·(γ/B₀)^((e+1)/300), B₀ = B(W_Z); b > cel ⇒ Wb[8:] *= cel/b. Wybór: najniższy VAL (po rzucie) wśród e ≥ 300.
B(W) = max_k Σ_j s[j]·A[j,k], A[j,k] = max(|Wg[j,k]|, |Wh[j,k]|) + 0.5·|Wt[j,k]|, s[j] = Σ_i |Wb[8+i, j]|.
Zapis: wagi/<ramię>.npz (NCP20.save), wagi/<ramię>_krzywe.json.
Użycie: bz_trening.py <ramię> [nazwa_pliku]   ramię ∈ K, B90, B50, B30, C3, C12.
"""
import json
import os
import sys
import time

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, ROOT)
from net import dataset as D                             # noqa: E402
from net.models import NCP20                             # noqa: E402
from net.train import Adam, _std                         # noqa: E402

OUT = os.path.join(ROOT, "results/BLIZNIAK_RECON/wagi")
GAMMA = {"K": None, "B90": 0.9, "B50": 0.5, "B30": 0.3, "C3": 3.0, "C12": 12.0}
EPOKI, LR, CLIP, MIL = 900, 0.003, 5.0, (540, 765)


def B(m):
    A = np.maximum(np.abs(m.Wg), np.abs(m.Wh)) + 0.5 * np.abs(m.Wt)
    s = np.abs(m.Wb[8:]).sum(0)
    return float((s[:, None] * A).sum(0).max())


def trenuj(ramie, nazwa):
    g = GAMMA[ramie]
    mean, sd = D.feature_stats()
    Xtr, Ytr, Mtr = D.batched(D.episodes("TRAIN")); Xtr = _std(D.clip_age(Xtr), mean, sd)
    Xva, Yva, Mva = D.batched(D.episodes("VAL")); Xva = _std(D.clip_age(Xva), mean, sd)
    m = NCP20.load(os.path.join(ROOT, "net/frozen/ncp.npz"))
    B0 = B(m)
    opt = Adam(m.params(), LR, 0.9, 0.999)
    ntr, nva = Mtr.sum() * 3, Mva.sum() * 3
    best = {"val": 1e18}
    kr = {"train": [], "val": [], "B": []}
    t0 = time.time()
    for ep in range(EPOKI):
        if ep in MIL:
            opt.lr *= 0.5
        Yh, caches = m.forward_seq(Xtr, Mtr)
        d = (Yh - Ytr) * Mtr[:, :, None]
        kr["train"].append(float(np.sum(d * d) / ntr))
        opt.step(m.params(), m.grads_seq(caches, (2.0 / ntr) * d, Mtr), clip=CLIP)
        if g is not None:
            cel = g if ep >= 300 else B0 * (g / B0) ** ((ep + 1) / 300)
            b = B(m)
            if b > cel:
                m.Wb[8:] *= cel / b
        Yv, _ = m.forward_seq(Xva, Mva)
        dv = (Yv - Yva) * Mva[:, :, None]
        vl = float(np.sum(dv * dv) / nva)
        kr["val"].append(vl); kr["B"].append(B(m))
        if ep >= 300 and vl < best["val"]:
            best = {"val": vl, "epoka": ep, "params": {k: v.copy() for k, v in m.params().items()},
                    "val_os": [float(np.sum(dv[..., i] ** 2) / Mva.sum()) for i in range(3)]}
    m.set_params(best["params"])
    fn = os.path.join(OUT, nazwa + ".npz")
    m.save(fn)
    meta = {"ramie": ramie, "gamma": g, "B0": B0, "epoka": best["epoka"], "val": best["val"], "val_os": best["val_os"],
            "B_z_wag": B(NCP20.load(fn)), "czas_s": time.time() - t0}
    json.dump({"meta": meta, **kr}, open(os.path.join(OUT, nazwa + "_krzywe.json"), "w"))
    print(json.dumps(meta), flush=True)


if __name__ == "__main__":
    trenuj(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else sys.argv[1])
