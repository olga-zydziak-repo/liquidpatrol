"""p2/freeze.py — commit ZAMRAŻAJĄCY kroku 0 (A2). Uruchom po wrzuceniu etykiet + statystykach.

Zamraża PRZED pierwszym treningiem (nietykalne po commicie): split (ID sekwencji + sha256),
siatkę masek (p,L,σ) + seedy, wybrane T_min, wariant baseline, statystyki, prowieniencję.
Zapisuje p2/frozen/manifest.json + p2/frozen/provenance.json. Ten commit → push przed treningiem.
"""
from __future__ import annotations
import os, json, sys
from p2.io_labels import load_split, discover, sha256
from p2 import stats_k0

FROZEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frozen")
SOURCE_URL = os.environ.get("SOURCE_URL",
    "https://drive.google.com/file/d/1NPYaop35ocVTYWHOYQQHn8YHsM9jmLGr/view")  # paczka Anti-UAV300
LICENSE_REPO = "https://github.com/ZhaoJ9014/Anti-UAV (MIT)"  # A1: licencja projektu

# --- siatki i seedy (z PRE_P2 §2, [PROPOZYCJA]) — ZAMROŻONE ---
SIGMA_GRID = [0.02, 0.05, 0.10]
P_GRID = [0.3, 0.5, 0.7]
L_GRID = [13, 25, 50]
OP_POINT = {"sigma": 0.05, "p": 0.5, "L": 25}
MASK_SEEDS = [0, 1, 2, 3, 4]
TRAIN_SEEDS = [0, 1, 2, 3, 4]
SPLIT_SEED = 1234
HORIZONS = [13, 25, 50]              # {0.5,1,2}s @25fps
PARAM_BUDGET = 30000
PARAM_TOL = 0.02
# A3 (mocny baseline): R=σ² (prawdziwe σ) ORAZ Q strojone na TRAIN (grid q_vel, wybór po ADE) —
# empirycznie potwierdzone (synthetic CV): sam default Q => Kalman słomiany (przegrywa ZOH);
# strojony Q => Kalman bije ZOH ~12x na predykcji. Test nietykany.
BASELINE_VARIANT = "R=sigma^2 (prawdziwe sigma) + Q strojone na train (arms.tune_kalman_q, A3)"


def provenance():
    prov = {"source_url": SOURCE_URL, "license_repo": LICENSE_REPO, "modality": "IR",
            "package": "Anti-UAV300 (zip, sha256 w deleted_videos.json)", "files": []}
    for split in ("train", "val", "test"):
        for f in discover(split):
            prov["files"].append({"split": split, "path": os.path.relpath(f),
                                   "name": os.path.basename(f), "sha256": sha256(f)})
    return prov


def build_manifest():
    st = stats_k0.compute()
    ladder = st.get("ladder", {})
    def _seqname(f):
        b = os.path.splitext(os.path.basename(f))[0]
        return os.path.basename(os.path.dirname(f)) if b.lower() in ("infrared", "ir_label") else b
    split = {sp: sorted(_seqname(f) for f in discover(sp)) for sp in ("train", "val", "test")}
    if not any(split.values()):
        return None, st
    manifest = {
        "phase": "P2 krok 0 — ZAMROŻENIE przed treningiem (A2)",
        "dataset": "Anti-UAV wariant B (oryginał, MIT), modalność IR (A1)",
        "split_by": "SEKWENCJE", "split_seed": SPLIT_SEED, "split_counts":
            {k: len(v) for k, v in split.items()}, "split_seq_ids": split,
        "T_min_s": ladder.get("T_min_s"), "ladder": ladder,
        "horizons_frames": HORIZONS, "horizons_s": [h / 25 for h in HORIZONS],
        "noise_sigma_grid": SIGMA_GRID, "mask_p_grid": P_GRID, "mask_L_grid": L_GRID,
        "operating_point": OP_POINT, "mask_seeds": MASK_SEEDS, "train_seeds": TRAIN_SEEDS,
        "param_budget": PARAM_BUDGET, "param_parity_tol": PARAM_TOL,
        "baseline_variant_A3": BASELINE_VARIANT,
        "verdict_criteria_locked": {
            "precondition": "kazde uczone bije ZOH-age na filtracji RMSE, inaczej FAIL_EARLY (§6)",
            "teza": "najlepsze uczone bije Kalman/IMM na predykcji w dziury o > pooled_std (§7); NULL/NEG=WYNIK",
            "pooled_std_over": "sekwencje x seedy masek x seedy treningu",
            "epoch_selector": "JAWNY best-val (np. min val FDE@25), zero ukrytego early-stop (F-3b-3)",
            "test_frozen": True},
        "stats": st,
    }
    return manifest, st


def main():
    os.makedirs(FROZEN, exist_ok=True)
    manifest, st = build_manifest()
    if manifest is None:
        print("[freeze] BRAK DANYCH — wrzuć etykiety (p2/data/README.md). Nic nie zamrożono.")
        print(json.dumps(st, indent=2, ensure_ascii=False))
        sys.exit(2)
    prov = provenance()
    json.dump(manifest, open(os.path.join(FROZEN, "manifest.json"), "w"), indent=2, ensure_ascii=False)
    json.dump(prov, open(os.path.join(FROZEN, "provenance.json"), "w"), indent=2, ensure_ascii=False)
    print(f"[freeze] ZAMROŻONO: split {manifest['split_counts']}, T_min={manifest['T_min_s']}s, "
          f"{len(prov['files'])} plikow (sha256). Manifest + provenance w p2/frozen/.")
    print("[freeze] -> commit ZAMRAŻAJĄCY -> push przed treningiem (znacznik zewnętrzny, A2).")


if __name__ == "__main__":
    main()
