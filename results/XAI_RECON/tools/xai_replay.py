#!/usr/bin/env python3
"""results/XAI_RECON/tools/xai_replay.py — replayer deterministyczny sieci (PROMPT_XAI_S0 §R1).

Replay OFFLINE polityki z zalogowanych wejść demo.jsonl — przyrządy WYŁĄCZNIE
importem (zero edycji FROZEN): modele net/models.py (NCP20 0337d5ea) i
net/models_liq.py (GRU21 5ec02755…), cechy bench/features.py 9adc1505,
clip_age net/dataset.py:104, clip_v r03/controllers/common.py:11.

Replikowana LITERA toru lotu (dowody plik:linia):
  • wejście sieci = features(own_pos_ned, own_vel_ned, trk_pos_ned,
    track_age_s, track_valid) → clip_age → (x−mean)/std; mean/std z npz wag
    (net_controller.py:84-88 == liq_controller.py:82-86);
  • utrata tracka (fd None / !valid / age>TRACK_LOSS_S=1.0) ⇒ cmd [0,0,0],
    SIEĆ NIE STEPUJE (stan ukryty zamrożony) — net_controller.py:106-111;
  • wyjście = clip_v(step_np(xs,h), V_MAX=3.0) — net_controller.py:89-97,
    V_MAX r01/config.py:24, vmax=V_MAX bench_flight.py:310;
  • reset stanu per epizod: świeży kontroler per ep (bench_flight.py:310-312);
  • wiersz demo loguje DOKŁADNIE skonsumowane obiekty (bench_flight.py:360-361
    vs :406: te same own/vel/fs + cmd["v_ned"]), zaokrąglone do 3 miejsc
    (demo_logger.py:_r3) — zaokrąglenie zapisu = źródło szumu kotwicy;
  • wrapper net_fantom (FANTOM/PERC2/DEMO_C): kwarantanna K1 — delegat widzi
    blank_fd (invalid) do wyjścia A/B/C (fantom_scan.py:93-140; progi FROZEN
    T_q=3.0, D_JUMP=5.0); AkwScan zmienia wyłącznie yaw w hold
    (akw_scan.py:91-109) — cmd_v nietknięte, dla repleyu v_ned bez znaczenia.

Zużycie: anchor <wyjście.json> <bootdir:arm[:fantom]> ...   (kotwica R1)
         (biblioteka: load_eps / replay_episode dla atlasu R2/R3)
"""
import json
import math
import os
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from bench.features import features                    # 9adc1505 — importem
from net.dataset import clip_age                       # AGE_CAP=1.0 (dataset.py:101)
from net.models import NCP20                           # CfC — step_np models.py:127
from net.models_liq import GRU21                       # GRU — step_np models_liq.py:51
from r03.controllers.common import clip_v              # saturacja |v|<=vmax

V_MAX = 3.0            # r01/config.py:24 (bench_flight.py:310 vmax=V_MAX)
TRACK_LOSS_S = 1.0     # net_controller.py:35
FANTOM_TQ_S = 3.0      # fantom_scan.py:43 (FROZEN)
FANTOM_DJUMP_M = 5.0   # fantom_scan.py:44 (FROZEN)

_MODELS = {}


def model_of(arm):
    """Ładuje zamrożone wagi KOPIĄ w pamięci (plik tylko czytany)."""
    if arm not in _MODELS:
        path = os.path.join(ROOT, "net", "frozen", f"{arm}.npz")
        _MODELS[arm] = (NCP20 if arm == "ncp" else GRU21).load(path)
    return _MODELS[arm]


def iter_jsonl(p):
    with open(p) as f:
        for ln in f:
            try:
                yield json.loads(ln)
            except ValueError:
                continue


def load_eps(bootdir):
    """demo.jsonl → {(episode_id, attempt): [wiersze w kolejności]}."""
    eps = {}
    for r in iter_jsonl(os.path.join(bootdir, "demo.jsonl")):
        eps.setdefault((r["episode_id"], r["attempt"]), []).append(r)
    return eps


def replay_episode(rows, arm, fantom=False):
    """Replay 1:1 litery kontrolera na zalogowanych wierszach epizodu.

    Zwraca dict: y (T,3) replay, y_log (T,3), infer (T,) bool, h (T,H) stan PO ticku,
    gate (T,H) bramka czasu (CfC: gate; GRU: z) na tickach inferencji (NaN poza),
    x (T,8) cechy znormalizowane (NaN poza), t (T,), phase (T,) str."""
    m = model_of(arm)
    H = m.H
    h = np.zeros((1, H))
    T = len(rows)
    out = {"t": np.zeros(T), "y": np.zeros((T, 3)), "y_log": np.zeros((T, 3)),
           "infer": np.zeros(T, bool), "h": np.zeros((T, H)),
           "gate": np.full((T, H), np.nan), "x": np.full((T, 8), np.nan),
           "phase": [], "d": np.full(T, np.nan)}
    # stan kwarantanny K1 (fantom_scan.py:70-135) — t_ref = t_sim 1. wiersza
    q_active = bool(fantom)
    t_ref = None
    snap = None
    prev_valid = None
    for i, r in enumerate(rows):
        t = r["t_sim"]
        valid_raw = bool(r["track_valid"])
        age = r["track_age_s"]
        if q_active:
            # kolejność 1:1 z fantom_scan.step: init t_ref (ustawia prev_valid na
            # BIEŻĄCĄ ważność — A niemożliwe na 1. ticku), potem predykaty, potem
            # aktualizacja prev_valid (fantom_scan.py:98-115)
            if t_ref is None:
                t_ref = t
                snap = list(r["trk_pos_ned"]) if valid_raw else None
                prev_valid = valid_raw
            reason = None
            if valid_raw and prev_valid is False:
                reason = "A"
            elif (valid_raw and snap is not None
                    and math.dist(r["trk_pos_ned"][:2], snap[:2]) > FANTOM_DJUMP_M):
                reason = "B"
            elif t - t_ref >= FANTOM_TQ_S:
                reason = "C"
            prev_valid = valid_raw
            if reason is not None:
                q_active = False
        consume = (not q_active) and valid_raw and age <= TRACK_LOSS_S
        if consume:
            row = {"own_pos_ned": r["own_pos_ned"], "own_vel_ned": r["own_vel_ned"],
                   "trk_pos_ned": r["trk_pos_ned"], "track_age_s": age,
                   "track_valid": True}
            x = np.array(features(row), dtype=np.float64)
            xs = (clip_age(x) - m.input_mean) / m.input_std
            y, h, cache = m.step_np(xs[None, :], h)
            v = clip_v([float(y[0, 0]), float(y[0, 1]), float(y[0, 2])], V_MAX)
            out["x"][i] = xs
            out["gate"][i] = cache[4][0] if arm == "ncp" else cache[2][0]  # CfC gate / GRU z
            out["d"][i] = math.hypot(r["trk_pos_ned"][0] - r["own_pos_ned"][0],
                                     r["trk_pos_ned"][1] - r["own_pos_ned"][1])
            out["infer"][i] = True
        else:
            v = [0.0, 0.0, 0.0]
        out["t"][i] = t
        out["y"][i] = v
        out["y_log"][i] = r["cmd_v_ned"]
        out["h"][i] = h[0]
        out["phase"].append(r["phase"])
    out["phase"] = np.array(out["phase"])
    return out


def anchor_stats(rep):
    """|Δ| per tick (max po 3 składowych) na WSZYSTKICH tickach epizodu."""
    d = np.abs(rep["y"] - rep["y_log"]).max(axis=1)
    return {"n_tick": int(len(d)), "n_infer": int(rep["infer"].sum()),
            "p50": float(np.percentile(d, 50)), "p95": float(np.percentile(d, 95)),
            "max": float(d.max()),
            "p95_infer": float(np.percentile(d[rep["infer"]], 95)) if rep["infer"].any() else 0.0,
            "max_hold": float(d[~rep["infer"]].max()) if (~rep["infer"]).any() else 0.0}


def main():
    assert sys.argv[1] == "anchor"
    out_json = sys.argv[2]
    res = {"vmax": V_MAX, "track_loss_s": TRACK_LOSS_S, "cases": []}
    for spec in sys.argv[3:]:
        parts = spec.split(":")
        bootdir, arm = parts[0], parts[1]
        fantom = len(parts) > 2 and parts[2] == "fantom"
        for (eid, att), rows in sorted(load_eps(bootdir).items()):
            rep = replay_episode(rows, arm, fantom=fantom)
            st = anchor_stats(rep)
            st.update({"boot": os.path.basename(os.path.normpath(bootdir)), "arm": arm,
                       "fantom": fantom, "episode_id": eid, "attempt": att,
                       "scenario_id": rows[0]["scenario_id"]})
            res["cases"].append(st)
            print(f"[{st['boot']}:{arm}{'(f)' if fantom else ''}] {st['scenario_id']} "
                  f"n={st['n_tick']}/{st['n_infer']} p50={st['p50']:.4g} "
                  f"p95={st['p95']:.4g} max={st['max']:.4g} max_hold={st['max_hold']:.4g}")
    allp95 = [c["p95"] for c in res["cases"]]
    allmax = [c["max"] for c in res["cases"]]
    res["agg"] = {"n_ep": len(res["cases"]), "p95_med": float(np.median(allp95)),
                  "p95_max": float(max(allp95)), "max_max": float(max(allmax))}
    json.dump(res, open(out_json, "w"), indent=1)
    print("AGG:", json.dumps(res["agg"]))


if __name__ == "__main__":
    main()
