"""p2/metrics.py — metryki (§4 PRE_P2): filtracja RMSE (chwile obserwacji) + predykcja ADE/FDE (dziury)."""
from __future__ import annotations
import numpy as np
from p2.arms import HORIZONS


def filtration_rmse(res, ep):
    """RMSE pozycji (cx,cy) w chwilach OBSERWACJI (gdzie est i gt istnieją)."""
    est, gt, obs = res["est"], ep["gt"], ep["observed"]
    mask = obs & ~np.isnan(gt[:, 0]) & ~np.isnan(est[:, 0])
    if mask.sum() == 0:
        return np.nan
    d = est[mask, :2] - gt[mask, :2]
    return float(np.sqrt((d ** 2).sum(axis=1).mean()))


def prediction_ade_fde(res, ep):
    """Predykcja W GŁĄB DZIUR: dla punktów startu t predykcja na horyzont H celuje w gt[t+H],
    liczone TYLKO gdy t+H jest nieobserwowane (w dziurze) i gt[t+H] istnieje."""
    pred, gt, obs, vf = res["pred"], ep["gt"], ep["observed"], ep["valid_from"]
    T = gt.shape[0]
    per_h = {H: [] for H in HORIZONS}
    for t in range(vf, T):
        for j, H in enumerate(HORIZONS):
            tt = t + H
            if tt >= T or obs[tt] or np.isnan(gt[tt, 0]) or np.isnan(pred[t, j, 0]):
                continue
            per_h[H].append(float(np.linalg.norm(pred[t, j, :2] - gt[tt, :2])))
    fde = {H: (float(np.mean(v)) if v else np.nan) for H, v in per_h.items()}
    allv = [e for v in per_h.values() for e in v]
    ade = float(np.mean(allv)) if allv else np.nan
    return {"FDE": fde, "ADE": ade, "n": {H: len(v) for H, v in per_h.items()}}


def evaluate(arm, ep):
    res = arm.run(ep)
    return {"filt_rmse": filtration_rmse(res, ep), **prediction_ade_fde(res, ep)}


if __name__ == "__main__":
    # test analitycznych ramion + metryk na syntetyku CV (bez etykiet)
    from p2.protocol import make_episode
    from p2.arms import ZOHAge, KalmanCV, IMM
    T = 400; t = np.arange(T)
    boxes = np.stack([0.3 + 0.0008 * t, 0.5 + 0.0004 * t, np.full(T, 0.05), np.full(T, 0.04)], 1)
    exist = np.ones(T, bool); exist[150:170] = False
    seq = {"name": "synth_cv", "boxes": boxes, "exist": exist}
    ep = make_episode(seq, sigma=0.05, p=0.5, L=25, seed=0)
    for Arm in (ZOHAge, KalmanCV, IMM):
        a = Arm(0.05) if Arm is not ZOHAge else Arm()
        m = evaluate(a, ep)
        fde = {k: round(v, 4) for k, v in m["FDE"].items()}
        print(f"{a.name:10s} filt_RMSE={m['filt_rmse']:.4f}  ADE={m['ADE']:.4f}  FDE={fde}  n={m['n']}")
    print("[metrics] oczek.: Kalman/IMM filt_RMSE < ZOH; predykcja Kalman/IMM lepsza w dziury")
