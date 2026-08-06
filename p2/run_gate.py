"""p2/run_gate.py — pełny bieg bramki P2 (§6/§7). URUCHAMIAĆ PO freeze+push (A2).

1. Strojenie A3: Kalman/IMM Q na TRAIN (grid), R=σ².
2. Trening 5 ramion uczonych × N seedów; JAWNY selektor epoki (min val FDE@25, F-3b-3).
3. PRECONDITION: uczone bije ZOH na filtracji (val) → inaczej FAIL_EARLY.
4. Ewaluacja test × seedy masek (operating point); metryki ADE/FDE w dziury.
5. TEZA §7 (dwustronna): best uczone vs Kalman/IMM o > pooled_std (seq × mask-seed × train-seed).
Wyniki → p2/frozen/gate_results.json. SMOKE=1 dla szybkiej walidacji.
"""
from __future__ import annotations
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".p2deps"))
import numpy as np, torch
from p2.io_labels import load_split
from p2.protocol import make_episode
from p2.arms import ZOHAge, KalmanCV, IMM, tune_kalman_q, Q_VEL_GRID
from p2.learned import LEARNED, build
from p2.metrics import evaluate, filtration_rmse
import p2.train as T

M = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "frozen", "manifest.json")))
OP = M["operating_point"]; SIGMA, P, L = OP["sigma"], OP["p"], OP["L"]
MASK_SEEDS = M["mask_seeds"]; TRAIN_SEEDS = M["train_seeds"]; TMIN = M["T_min_s"] * 25
SMOKE = os.environ.get("SMOKE") == "1"
EPOCHS = 5 if SMOKE else int(os.environ.get("EPOCHS", "80"))
if SMOKE:
    MASK_SEEDS = MASK_SEEDS[:2]; TRAIN_SEEDS = TRAIN_SEEDS[:1]


def qualify(seqs):
    return [s for s in seqs if s["n_frames"] >= TMIN]


def episodes(seqs, seed):
    return [make_episode(s, SIGMA, P, L, seed) for s in seqs]


def ade_units(arm, seqs, seeds):
    """Zbiera per-(seq × mask-seed) ADE predykcji w dziury."""
    u = []
    for ms in seeds:
        for s in seqs:
            ep = make_episode(s, SIGMA, P, L, ms)
            m = evaluate(arm, ep)
            if not np.isnan(m["ADE"]):
                u.append(m["ADE"])
    return np.array(u)


def main():
    t0 = time.time()
    tr = qualify(load_split("train")); vl = qualify(load_split("val")); te = qualify(load_split("test"))
    if SMOKE:
        tr, vl, te = tr[:20], vl[:8], te[:10]
    print(f"[gate] SMOKE={SMOKE} epochs={EPOCHS} | train={len(tr)} val={len(vl)} test={len(te)} "
          f"mask_seeds={MASK_SEEDS} train_seeds={TRAIN_SEEDS}")
    res = {"config": {"op": OP, "epochs": EPOCHS, "mask_seeds": MASK_SEEDS, "train_seeds": TRAIN_SEEDS,
                      "n_test": len(te), "smoke": SMOKE}, "arms": {}}

    # --- A3: strojenie Kalman/IMM Q na train ---
    tr_eps = episodes(tr, seed=TRAIN_SEEDS[0])
    tune = tune_kalman_q(tr_eps, SIGMA, q_grid=Q_VEL_GRID if not SMOKE else [1e-3, 1e-6, 1e-9])
    qbest = tune["best_q_vel"]
    print(f"[gate] A3 Kalman Q strojone na train: best_q_vel={qbest:.0e}")
    kal = KalmanCV(SIGMA, q_vel=qbest); imm = IMM(SIGMA)
    imm.cv = KalmanCV(SIGMA, q_vel=qbest); imm.st = KalmanCV(SIGMA, q_vel=min(qbest * 100, 1e-3))

    # --- ramiona analityczne na test ---
    for name, arm in [("ZOH-age", ZOHAge()), ("Kalman-CV", kal), ("IMM", imm)]:
        u = ade_units(arm, te, MASK_SEEDS)
        res["arms"][name] = {"type": "analityczne", "ADE_mean": float(u.mean()), "ADE_std": float(u.std()),
                             "n_units": len(u)}
        print(f"[gate] {name:10s} test ADE={u.mean():.4f}±{u.std():.4f} (n={len(u)})")

    # --- ramiona uczone: trening × seedy + precondition + eval ---
    for name in LEARNED:
        per_seed_ade = []; units_all = []; failed = []
        for ts in TRAIN_SEEDS:
            trE = episodes(tr, seed=ts); vlE = episodes(vl, seed=ts)
            arm, best = T.train_arm(name, trE, vlE, seed=ts, epochs=EPOCHS)
            ok, ar, zr = T.precondition_beats_zoh(arm, vlE)
            if not ok:
                failed.append({"train_seed": ts, "arm_rmse": ar, "zoh_rmse": zr}); continue
            u = ade_units(arm, te, MASK_SEEDS)
            units_all.append(u); per_seed_ade.append(float(u.mean()))
            print(f"[gate] {name:12s} seed={ts} ep*={best['epoch']} val_FDE@25={best['fde']:.4f} "
                  f"test_ADE={u.mean():.4f} precond={'OK' if ok else 'FAIL'}")
        if units_all:
            allu = np.concatenate(units_all)
            res["arms"][name] = {"type": "uczone", "params": T.build(name).__class__ and None,
                                 "ADE_mean": float(allu.mean()), "ADE_std": float(allu.std()),
                                 "per_seed_ADE": per_seed_ade, "n_fail_early": len(failed),
                                 "fail_early": failed, "n_units": len(allu)}
        else:
            res["arms"][name] = {"type": "uczone", "FAIL_EARLY_ALL": True, "fail_early": failed}
        print(f"[gate] {name}: FAIL_EARLY {len(failed)}/{len(TRAIN_SEEDS)} seedow")

    # --- TEZA §7 (dwustronna) ---
    learned_ok = {k: v for k, v in res["arms"].items()
                  if v.get("type") == "uczone" and "ADE_mean" in v}
    baseline = min((res["arms"][b]["ADE_mean"] for b in ("Kalman-CV", "IMM")))
    baseline_name = min(("Kalman-CV", "IMM"), key=lambda b: res["arms"][b]["ADE_mean"])
    if learned_ok:
        best_learned = min(learned_ok, key=lambda k: learned_ok[k]["ADE_mean"])
        bl = learned_ok[best_learned]["ADE_mean"]
        # pooled_std: sqrt(średnia wariancji po porównywanych ramionach) [seq×mask×train]
        pooled_var = np.mean([learned_ok[best_learned]["ADE_std"] ** 2,
                              res["arms"][baseline_name]["ADE_std"] ** 2])
        pooled_std = float(np.sqrt(pooled_var))
        margin = baseline - bl                          # >0: uczone lepsze
        if margin > pooled_std:
            verdict = "POZYTYWNY (uczone bije baseline o >pooled_std)"
        elif margin < -pooled_std:
            verdict = "NEGATYWNY (baseline bije uczone o >pooled_std)"
        else:
            verdict = "NULL (różnica ≤ pooled_std)"
        res["teza"] = {"best_learned": best_learned, "best_learned_ADE": bl,
                       "baseline": baseline_name, "baseline_ADE": baseline,
                       "margin": float(margin), "pooled_std": pooled_std, "verdict": verdict}
        print(f"\n[gate] TEZA §7: best uczone={best_learned} ADE={bl:.4f} vs {baseline_name} ADE={baseline:.4f} "
              f"| margin={margin:.4f} pooled_std={pooled_std:.4f}\n[gate] WERDYKT: {verdict}")
    else:
        res["teza"] = {"verdict": "wszystkie uczone FAIL_EARLY — brak porównania"}
        print("[gate] wszystkie uczone FAIL_EARLY")

    res["wall_time_s"] = round(time.time() - t0, 1)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frozen",
                       "gate_results_smoke.json" if SMOKE else "gate_results.json")
    json.dump(res, open(out, "w"), indent=2, ensure_ascii=False)
    print(f"[gate] zapisano {out}  (wall {res['wall_time_s']}s)")


if __name__ == "__main__":
    main()
