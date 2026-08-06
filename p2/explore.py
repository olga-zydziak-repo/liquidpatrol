"""p2/explore.py — ANEKS EKSPLORACYJNY (POZA pre-rejestracją; werdykt §7 NIETYKALNY).

Cel: czy filtracyjny precondition odciął ramię DOBRE na osi tezy (predykcja w dziury)?
Deterministyczna re-produkcja 4 miarodajnych ramion (latent-ODE WYKLUCZONY — bug integracji):
te same seedy/config co bieg pre-rejestrowany (40 epok) → identyczne wagi; liczymy ADE/FDE
predykcji na teście × seedach masek IGNORUJĄC precondition. Wynik → gate_explore.json.
"""
from __future__ import annotations
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".p2deps"))
import numpy as np
from p2.io_labels import load_split
from p2.protocol import make_episode
from p2.metrics import evaluate
from p2.arms import HORIZONS
import p2.train as T

M = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "frozen", "manifest.json")))
OP = M["operating_point"]; SIGMA, P, L = OP["sigma"], OP["p"], OP["L"]
MASK_SEEDS = M["mask_seeds"]; TRAIN_SEEDS = M["train_seeds"]; TMIN = M["T_min_s"] * 25
EPOCHS = int(os.environ.get("EPOCHS", "40"))
ARMS = ["GRU+dt", "CfC", "Mamba-notime", "Mamba+dt"]     # latent-ODE wykluczony (niemiarodajny)


def qualify(seqs): return [s for s in seqs if s["n_frames"] >= TMIN]
def episodes(seqs, seed): return [make_episode(s, SIGMA, P, L, seed) for s in seqs]


def pred_units(arm, seqs, seeds):
    """Zbiera per-(seq×mask) ADE oraz FDE@H."""
    ade = []; fde = {h: [] for h in HORIZONS}
    for ms in seeds:
        for s in seqs:
            m = evaluate(arm, make_episode(s, SIGMA, P, L, ms))
            if not np.isnan(m["ADE"]):
                ade.append(m["ADE"])
            for h in HORIZONS:
                if not np.isnan(m["FDE"].get(h, np.nan)):
                    fde[h].append(m["FDE"][h])
    return np.array(ade), {h: (float(np.mean(v)) if v else None) for h, v in fde.items()}


def main():
    t0 = time.time()
    tr = qualify(load_split("train")); vl = qualify(load_split("val")); te = qualify(load_split("test"))
    print(f"[explore] POZA pre-rejestracja | train={len(tr)} test={len(te)} arms={ARMS} epochs={EPOCHS}")
    res = {"note": "EKSPLORACJA — poza pre-rejestracja; werdykt §7 nietykalny; latent-ODE wykluczony (bug)",
           "baselines_prereg": {"ZOH-age": 0.1073, "Kalman-CV": 0.1356, "IMM": 0.1563}, "arms": {}}
    for name in ARMS:
        ade_all = []; fde_seed = {h: [] for h in HORIZONS}; per_seed = []
        for ts in TRAIN_SEEDS:
            arm, best = T.train_arm(name, episodes(tr, ts), episodes(vl, ts), seed=ts, epochs=EPOCHS)
            ade, fde = pred_units(arm, te, MASK_SEEDS)
            ade_all.append(ade); per_seed.append(float(ade.mean()))
            for h in HORIZONS:
                if fde[h] is not None: fde_seed[h].append(fde[h])
            print(f"[explore] {name:12s} seed={ts} ep*={best['epoch']} test_ADE={ade.mean():.4f}")
        allu = np.concatenate(ade_all)
        res["arms"][name] = {"ADE_mean": float(allu.mean()), "ADE_std": float(allu.std()),
                             "per_seed_ADE": per_seed,
                             "FDE_mean": {str(h): (float(np.mean(fde_seed[h])) if fde_seed[h] else None) for h in HORIZONS},
                             "n_units": len(allu)}
        print(f"[explore] {name}: ADE={allu.mean():.4f}±{allu.std():.4f}  (ZOH=0.1073)")
    # czy ktores bije ZOH / Kalman na predykcji?
    zoh = 0.1073; kal = 0.1356
    beats = {n: {"beats_ZOH": res["arms"][n]["ADE_mean"] < zoh,
                 "beats_Kalman": res["arms"][n]["ADE_mean"] < kal} for n in ARMS}
    res["summary"] = beats
    res["wall_time_s"] = round(time.time() - t0, 1)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frozen", "gate_explore.json")
    json.dump(res, open(out, "w"), indent=2, ensure_ascii=False)
    print("[explore] czy ktores bije ZOH(0.107)/Kalman(0.136):", json.dumps(beats))
    print(f"[explore] zapisano {out} (wall {res['wall_time_s']}s)")


if __name__ == "__main__":
    main()
