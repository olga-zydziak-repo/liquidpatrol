"""p2/train.py — harness treningu ramion uczonych (§6 PRE_P2). URUCHOMIĆ DOPIERO PO freeze+push (A2).

Identyczny trening: te same seedy/optymalizator/epoki. JAWNY selektor epoki (F-3b-3): best-val wg
zapisanego kryterium (min val FDE@25). PRECONDITION: uczone musi bić ZOH-age na filtracji RMSE,
inaczej FAIL_EARLY. Buduje epizody z zamrożonego protokołu (split + maski + σ).
"""
from __future__ import annotations
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".p2deps"))
import torch, torch.nn as nn
import numpy as np
from p2.protocol import make_episode
from p2.learned import build, HORIZONS, OUT
from p2.arms import ZOHAge
from p2.metrics import evaluate, filtration_rmse

EPOCH_SELECTOR = "min val FDE@25"     # F-3b-3: jawny, zero ukrytego early-stop
EPOCHS = 100


def targets(ep):
    """Cele per klatka: [gt(4) | gt@H1(4) | gt@H2(4) | gt@H3(4)]; maska gdzie GT istnieje."""
    gt = ep["gt"]; T = gt.shape[0]
    Y = np.full((T, OUT), np.nan)
    Y[:, :4] = gt
    for j, H in enumerate(HORIZONS):
        Y[:T - H, 4 + 4 * j:8 + 4 * j] = gt[H:H + (T - H)] if False else gt[H:]  # gt[t+H]
    return Y


def to_tensors(eps):
    X = [torch.tensor(np.nan_to_num(e["X"], nan=0.0), dtype=torch.float32) for e in eps]
    Y = [torch.tensor(targets(e), dtype=torch.float32) for e in eps]
    return X, Y


def masked_loss(pred, y):
    m = ~torch.isnan(y)
    if m.sum() == 0:
        return pred.sum() * 0.0
    return nn.functional.smooth_l1_loss(pred[m], y[m])


def val_fde25(arm, val_eps):
    j = HORIZONS.index(25)
    errs = []
    for e in val_eps:
        r = arm.run(e); fde = r  # arm.run zwraca est/pred
        m = evaluate(arm, e)
        if not np.isnan(m["FDE"].get(25, np.nan)):
            errs.append(m["FDE"][25])
    return float(np.mean(errs)) if errs else np.inf


def train_arm(name, train_eps, val_eps, seed, epochs=EPOCHS):
    torch.manual_seed(seed); np.random.seed(seed)
    arm = build(name); opt = torch.optim.AdamW(arm.parameters(), lr=1e-3)
    Xtr, Ytr = to_tensors(train_eps)
    best = {"fde": np.inf, "epoch": -1, "state": None}
    for ep in range(epochs):
        arm.train(); perm = np.random.permutation(len(Xtr))
        for i in perm:
            opt.zero_grad(); out = arm(Xtr[i][None])[0]
            loss = masked_loss(out, Ytr[i]); loss.backward(); opt.step()
        arm.eval(); fde = val_fde25(arm, val_eps)          # JAWNY selektor
        if fde < best["fde"]:
            best = {"fde": fde, "epoch": ep, "state": {k: v.clone() for k, v in arm.state_dict().items()}}
    arm.load_state_dict(best["state"])                      # best-val
    return arm, best


def precondition_beats_zoh(arm, val_eps):
    """FAIL_EARLY: uczone musi bić ZOH-age na filtracji RMSE (val)."""
    zoh = ZOHAge()
    a_rmse = np.nanmean([filtration_rmse(arm.run(e), e) for e in val_eps])
    z_rmse = np.nanmean([filtration_rmse(zoh.run(e), e) for e in val_eps])
    return a_rmse < z_rmse, float(a_rmse), float(z_rmse)


if __name__ == "__main__":
    # SMOKE-TEST na syntetyku (2 epoki) — walidacja pętli. NIE trening bramkowy.
    def synth(i):
        T = 300; t = np.arange(T)
        b = np.stack([0.3 + (0.0006 + 0.0002 * i) * t, 0.5 + 0.0004 * t,
                      np.full(T, 0.05), np.full(T, 0.04)], 1)
        ex = np.ones(T, bool); ex[120:140] = False
        return make_episode({"name": f"s{i}", "boxes": b, "exist": ex}, 0.05, 0.5, 25, seed=i)
    tr = [synth(i) for i in range(4)]; vl = [synth(i + 100) for i in range(2)]
    arm, best = train_arm("GRU+dt", tr, vl, seed=0, epochs=2)
    ok, ar, zr = precondition_beats_zoh(arm, vl)
    print(f"[train] SMOKE GRU+dt: best_epoch={best['epoch']} val_FDE@25={best['fde']:.4f} "
          f"(selektor='{EPOCH_SELECTOR}')")
    print(f"[train] precondition beats-ZOH(filtracja): {ok}  arm_rmse={ar:.4f} zoh_rmse={zr:.4f}")
    print("[train] OK — petla dziala. Trening bramkowy DOPIERO po freeze+push (A2).")
