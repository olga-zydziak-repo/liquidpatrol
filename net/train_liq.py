#!/usr/bin/env python3
"""net/train_liq.py — wrapper toru treningu/bramki dla kontroli LIQ (PRE_LIQ §2, PROMPT_LIQ_S1 §1-3).

IMPORTY z net/train.py / net/dataset.py / net/rollout_eval.py — ZERO edycji plików istniejących.
Identyczność toru = lista inwariantów PRE_LIQ §2: dane 114 D6, split z kodu, cechy bench.features,
standaryzacja TRAIN, MSE, Adam+clip, hiperparametry VERBATIM z gałęzi ncp configu (echo w raporcie),
cap 1000, selekcja WYŁĄCZNIE VAL, seed CLI (kampania=1; dyspersja 2,3).

Mapowanie configu (PROMPT §1(a), literalne):
  GRU    : komplet gałęzi ncp poza polami architektury (hidden 20→21; bb nie istnieje w GRU).
  MLP-k20: to samo (lr/epochs/clip/beta/milestones/seed z gałęzi ncp); parametry FORMATU toru
           okiennego — batch — z gałęzi mlp (512); architektura k=20, h=11.

Użycie:
  python -m net.train_liq train gru|mlp20 [seed] [outdir]   (domyślnie seed=1, results/LIQ/train/<arm>)
  python -m net.train_liq gate <model.npz>                   (bramka G13' = analog-D6 >=20/24 rolloutów)
  python -m net.train_liq gate-ncp                           (bramka dla kanonicznego ncp.npz 0337d5ea)
"""
import json
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from net import dataset as D
from net.train import Adam, CFG, _std, _prep_windows
from net.models_liq import GRU21, MLPk20
from net.models import NCP20
from net import rollout_eval as RE
from bench import scenarios as S


def _cfg_liq(arm):
    """Mapowanie PROMPT §1(a): baza = gałąź ncp; format okienny (batch) z gałęzi mlp."""
    base = dict(CFG["ncp"])
    if arm == "gru":
        return {"hidden": 21, "lr": base["lr"], "epochs": base["epochs"], "seed": 1,
                "grad_clip": base["grad_clip"], "beta1": base["beta1"], "beta2": base["beta2"],
                "lr_schedule": base["lr_schedule"]}
    if arm == "mlp20":
        return {"hidden": 11, "k": 20, "lr": base["lr"], "epochs": base["epochs"], "seed": 1,
                "grad_clip": base["grad_clip"], "beta1": base["beta1"], "beta2": base["beta2"],
                "lr_schedule": base["lr_schedule"], "batch": CFG["mlp"]["batch"]}
    raise SystemExit("arm: gru|mlp20")


def train_gru(seed):
    c = _cfg_liq("gru"); c["seed"] = seed; vmax = CFG["vmax"]
    mean, sd = D.feature_stats()
    tr = D.episodes("TRAIN"); va = D.episodes("VAL")
    Xtr, Ytr, Mtr = D.batched(tr); Xtr = _std(D.clip_age(Xtr), mean, sd)
    Xva, Yva, Mva = D.batched(va); Xva = _std(D.clip_age(Xva), mean, sd)
    m = GRU21(vmax, hidden=c["hidden"], seed=c["seed"])
    m.input_mean = mean; m.input_std = sd
    opt = Adam(m.params(), c["lr"], c["beta1"], c["beta2"])
    curves = {"train": [], "val": []}
    best = {"val": 1e18, "params": None, "epoch": -1}
    ntr = Mtr.sum() * 3; nva = Mva.sum() * 3
    sched = c.get("lr_schedule")
    for ep in range(c["epochs"]):
        if sched and ep in sched["milestones"]:
            opt.lr *= sched["gamma"]
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
    return m, curves, best, c


def train_mlp20(seed):
    c = _cfg_liq("mlp20"); c["seed"] = seed; vmax = CFG["vmax"]
    mean, sd = D.feature_stats()
    Xtr, Ytr = D.windows("TRAIN", k=c["k"]); Xtr = _prep_windows(Xtr, c["k"], mean, sd)
    Xva, Yva = D.windows("VAL", k=c["k"]); Xva = _prep_windows(Xva, c["k"], mean, sd)
    m = MLPk20(vmax, hidden=c["hidden"], seed=c["seed"])
    m.input_mean = mean; m.input_std = sd
    opt = Adam(m.params(), c["lr"], c["beta1"], c["beta2"])
    rng = np.random.RandomState(c["seed"])
    N = Xtr.shape[0]; bs = c["batch"]
    curves = {"train": [], "val": []}
    best = {"val": 1e18, "params": None, "epoch": -1}
    sched = c.get("lr_schedule")
    for ep in range(c["epochs"]):
        if sched and ep in sched["milestones"]:
            opt.lr *= sched["gamma"]
        idx = rng.permutation(N)
        tl = 0.0; nb = 0
        for s0 in range(0, N, bs):
            b = idx[s0:s0 + bs]
            Xb, Yb = Xtr[b], Ytr[b]
            y, cache = m.forward(Xb, cache=True)
            dd = y - Yb
            tl += np.mean(dd * dd); nb += 1
            dY = (2.0 / (Xb.shape[0] * 3)) * dd
            opt.step(m.params(), m.grads(cache, dY), clip=c["grad_clip"])
        yv = m.forward(Xva); vl = float(np.mean((yv - Yva) ** 2))
        curves["train"].append(tl / nb); curves["val"].append(vl)
        if vl < best["val"]:
            best = {"val": vl, "params": {k: v.copy() for k, v in m.params().items()}, "epoch": ep}
    m.set_params(best["params"])
    return m, curves, best, c


# ---------------- bramka offline G13' (ANEKS_NET-1 §2: analog-D6 >= 20/24 rolloutów) ----------------
class _LiqRolloutCtrl:
    """Adapter rolloutu dla GRU (stan) i MLPk20 (okno k=20) — preprocess identyczny z RE.NetController."""
    def __init__(self, model, ep):
        self.m = model
        self.mean = model.input_mean; self.std = model.input_std
        self.stateful = hasattr(model, "step_np")
        if self.stateful:
            self.h = np.zeros((1, model.H))
        else:
            self.k = model.K
            self.win = [np.zeros(8) for _ in range(self.k)]

    def cmd(self, tick, own, ov, t, sample):
        row = {"own_pos_ned": own, "own_vel_ned": [ov[0], ov[1], ov[2]],
               "trk_pos_ned": sample["trk_pos_ned"], "track_age_s": sample["track_age_s"],
               "track_valid": sample["track_valid"]}
        x = np.array(RE.features(row), dtype=np.float64)
        xs = (D.clip_age(x) - self.mean) / self.std
        if self.stateful:
            y, self.h, _ = self.m.step_np(xs[None, :], self.h)
        else:
            self.win.pop(0); self.win.append(xs)
            y = self.m.forward(np.concatenate(self.win)[None, :])
        v = RE.clip_v([float(y[0, 0]), float(y[0, 1]), float(y[0, 2])], RE.VMAX)
        return [v[0], v[1], v[2]]


def gate_g13p(model, adapter_cls=_LiqRolloutCtrl):
    """G13' (ANEKS_NET-1 §2): analog-D6 w >=20/24 rolloutów. Struktura LUSTRZANA z RE.gate_on_seeds
    (S.CELLS x ziarna TEST [4,8], find_episode, _rollout(..., "B", seed=sd)) — jedyna różnica: adapter
    kontrolera dla GRU/MLPk20. Widoki per-cell (oba/którekolwiek) raportowane OPISOWO (jak G13')."""
    man = S.gen_manifest()
    test_seeds = [sd for sd in S.SEEDS if sd % 4 == 0]            # 4, 8
    table = []
    for cell in S.CELLS:
        per_seed = []
        for sd in test_seeds:
            ep = S.find_episode(man, cell["v_intr"], cell["bearing_deg"], seed=sd)
            ctrl = adapter_cls(model, ep)
            te, fr, dm = RE._rollout(ep, ctrl, "B", seed=sd)
            per_seed.append({"seed": sd, "t_entry": round(te, 2) if te is not None else None,
                             "frac": round(fr, 4), "d_min": round(dm, 3) if dm is not None else None,
                             "ok": RE.analog_d6(te, fr, dm)})
        table.append({"cell": f"c{cell['cell_index']:02d}", "per_seed": per_seed,
                      "cell_both": all(p["ok"] for p in per_seed),
                      "cell_any": any(p["ok"] for p in per_seed)})
    n_ok = sum(1 for r in table for p in r["per_seed"] if p["ok"])
    n = sum(len(r["per_seed"]) for r in table)
    return {"n_ok": n_ok, "n": n, "pass": n_ok >= 20,
            "per_cell_both": sum(1 for r in table if r["cell_both"]),
            "per_cell_any": sum(1 for r in table if r["cell_any"]), "rows": table}


def main():
    cmd = sys.argv[1]
    if cmd == "train":
        arm = sys.argv[2]
        seed = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        outdir = sys.argv[4] if len(sys.argv) > 4 else os.path.join(ROOT, "results", "LIQ", "train", arm)
        os.makedirs(outdir, exist_ok=True)
        t0 = time.time()
        m, curves, best, c = (train_gru if arm == "gru" else train_mlp20)(seed)
        wall = time.time() - t0
        m.save(os.path.join(outdir, "model.npz"))
        json.dump(curves, open(os.path.join(outdir, "curves.json"), "w"))
        meta = {"arm": arm, "seed": seed, "cfg": c, "params": m.param_count(),
                "best_val_epoch": best["epoch"], "best_val_mse": best["val"],
                "final_train_mse": curves["train"][-1], "wall_time_s": round(wall, 1),
                "numpy": np.__version__}
        json.dump(meta, open(os.path.join(outdir, "train_meta.json"), "w"), indent=1)
        print(json.dumps(meta))
    elif cmd == "gate":
        path = sys.argv[2]
        d = np.load(path, allow_pickle=True)
        arm = str(d["arm"])
        model = {"gru": GRU21, "mlp20": MLPk20}[arm].load(path)
        res = gate_g13p(model)
        print(json.dumps({k: res[k] for k in ("n_ok", "n", "pass", "per_cell_both", "per_cell_any")}))
        json.dump(res, open(os.path.splitext(path)[0] + "_gate.json", "w"), indent=1)
    elif cmd == "gate-ncp":
        model = NCP20.load(os.path.join(ROOT, "net", "frozen", "ncp.npz"))
        res = gate_g13p(model, adapter_cls=lambda m, ep: RE.NetController(m, ep))
        print(json.dumps({k: res[k] for k in ("n_ok", "n", "pass", "per_cell_both", "per_cell_any")}))
        json.dump(res, open(os.path.join(ROOT, "results", "LIQ", "train", "ncp_gate.json"), "w"), indent=1)
    elif cmd == "disp":
        # §3 dyspersja OPISOWA: seedy {2,3} x {ncp, gru, mlp20} -> results/LIQ/offline_dispersion/
        # NCP: train_ncp z net/train.py z in-process podmianą seeda w CFG (zero edycji plików toru,
        # zero zapisu do results/NET); selekcja VAL bez zmian; wagi NIGDY do net/frozen.
        import net.train as T
        base = os.path.join(ROOT, "results", "LIQ", "offline_dispersion")
        summary = []
        for seed in (2, 3):
            for arm in ("ncp", "gru", "mlp20"):
                out = os.path.join(base, f"{arm}_s{seed}"); os.makedirs(out, exist_ok=True)
                t0 = time.time()
                if arm == "ncp":
                    keep = T.CFG["ncp"]["seed"]
                    T.CFG["ncp"]["seed"] = seed
                    try:
                        m, curves, best = T.train_ncp()
                    finally:
                        T.CFG["ncp"]["seed"] = keep
                    adapter = lambda mm, ep: RE.NetController(mm, ep)
                elif arm == "gru":
                    m, curves, best, _ = train_gru(seed); adapter = _LiqRolloutCtrl
                else:
                    m, curves, best, _ = train_mlp20(seed); adapter = _LiqRolloutCtrl
                wall = time.time() - t0
                m.save(os.path.join(out, "model.npz"))
                json.dump(curves, open(os.path.join(out, "curves.json"), "w"))
                res = gate_g13p(m, adapter_cls=adapter)
                row = {"arm": arm, "seed": seed, "best_val": best["val"], "best_epoch": best["epoch"],
                       "wall_s": round(wall, 1), "gate_n_ok": res["n_ok"], "gate_pass": res["pass"]}
                json.dump(res, open(os.path.join(out, "gate.json"), "w"), indent=1)
                summary.append(row)
                print(json.dumps(row), flush=True)
        json.dump(summary, open(os.path.join(base, "summary.json"), "w"), indent=1)
    else:
        raise SystemExit("train|gate|gate-ncp|disp")


if __name__ == "__main__":
    main()
