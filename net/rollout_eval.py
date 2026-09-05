#!/usr/bin/env python3
"""net/rollout_eval.py — bramka N3(i): rollout zamknięty w modelu punktowym z FEED-B (PRE_NET N3).

Model punktowy = kinematyka z buildu ławki (`bench/tests_orbit_executor._sim_cell`): śledzenie cmd_v
z accel≤A_MAX i |v|≤V_MAX, dt=0.05. RÓŻNICA: feed = FEED-B (harness.track_feed.FeedB, szum/latencja/
dropout, RNG z ziarna epizodu) zamiast idealnego; sterowanie = SIEĆ (NCP/MLP) zamiast wyroczni.
analog-D6: wejście w pasmo ≤25 s ∧ frac[6,10]≥0.85 ∧ d_min≥4. Bramka: ≥10/12 komórek na ziarnach TEST.

Sanity przyrządu (I1): egzekutor-wyrocznia w TYM modelu (idealny feed, seed=1) = 12/12 — reprodukcja
buildu ławki. Deterministyczne: RNG feedu = ziarno epizodu.

Zero SITL. features/executor/scenarios/track_feed importowane (frozen), nigdy kopiowane.
"""
import json
import math
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from bench import scenarios as S
from bench.features import features
from harness.track_feed import FeedB
from r03.controllers.orbit_executor import OrbitExecutor
from r03.controllers.common import clip_v
from net import dataset as D

PARAMS = json.load(open(os.path.join(ROOT, "bench", "executor_params.json")))
VMAX = 3.0
A_MAX = 2.0
DT = 0.05
DUR_S = 95.0
BAND = (PARAMS["band_lo_m"], PARAMS["band_hi_m"])


# --------------------------- adaptery sterujące (jednolity interfejs cmd_v = f(feed_sample, own)) ---------
class OracleController:
    """Egzekutor-wyrocznia jako sterownik rolloutu (sanity przyrządu)."""
    def __init__(self, ep):
        self.ex = OrbitExecutor(PARAMS, orbit_dir=ep["orbit_dir"], vmax=VMAX,
                                home_ned=(0.0, 0.0, -PARAMS["home_hover_alt_m"]))
        self.ex.reset()

    def cmd(self, tick, own, ov, t, sample):
        self.ex.set_feed(sample)
        return self.ex.step(tick, own, ov, t, False)["v_ned"]


class NetController:
    """Sieć (NCP/MLP) jako sterownik: buduje 8-cechowy wektor z sample+own (bench.features), preprocess, forward."""
    def __init__(self, model, ep):
        self.m = model
        self.arm = model.ARM
        self.mean = model.input_mean; self.std = model.input_std
        if self.arm == "ncp":
            self.h = np.zeros((1, model.H))
        else:
            self.k = model.K
            self.win = [np.zeros(8) for _ in range(self.k)]

    def cmd(self, tick, own, ov, t, sample):
        row = {"own_pos_ned": own, "own_vel_ned": [ov[0], ov[1], ov[2]],
               "trk_pos_ned": sample["trk_pos_ned"], "track_age_s": sample["track_age_s"],
               "track_valid": sample["track_valid"]}
        x = np.array(features(row), dtype=np.float64)               # 8 cech (ta sama funkcja co w treningu)
        xc = D.clip_age(x)
        xs = (xc - self.mean) / self.std
        if self.arm == "ncp":
            y, self.h, _ = self.m.step_np(xs[None, :], self.h)
            raw = [float(y[0, 0]), float(y[0, 1]), float(y[0, 2])]
        else:
            self.win.pop(0); self.win.append(xs)                    # okno standaryzowanych cech
            X = np.concatenate(self.win)[None, :]
            y = self.m.forward(X)
            raw = [float(y[0, 0]), float(y[0, 1]), float(y[0, 2])]
        v = clip_v(raw, VMAX)                                        # belt kontrolera (N1 „clip_v w kontrolerze")
        return [v[0], v[1], v[2]]


def _rollout(ep, controller, feed_mode, seed):
    """Model punktowy. feed_mode='ideal' (wyrocznia sanity) lub 'B' (FEED-B). Zwraca (t_entry, frac, d_min)."""
    own = [0.0, 0.0, -PARAMS["home_hover_alt_m"]]
    ov = [0.0, 0.0, 0.0]
    t = 0.0
    t_entry = None
    in_band = 0; orbit_ticks = 0
    d_min = 1e9
    r_lo, r_hi = BAND
    feed = FeedB(seed) if feed_mode == "B" else None
    while t < DUR_S:
        px, py, pz = S.position_at(ep, t)
        trk_true = [px, py, -pz]                                    # NED
        if feed_mode == "ideal":
            px2, py2, _ = S.position_at(ep, t + 0.1)
            tvel = [(px2 - px) / 0.1, (py2 - py) / 0.1, 0.0]
            sample = {"trk_pos_ned": trk_true, "trk_vel_ned": tvel, "track_age_s": 0.0,
                      "track_valid": True, "feed_sha": "ideal"}
        else:
            feed.push_gt(t, trk_true)
            sample = feed.sample(t)
        cv = controller.cmd(int(t / DT), own, ov, t, sample)
        for k in range(3):                                          # śledzenie z limitem accel
            dv = cv[k] - ov[k]
            amax_dv = A_MAX * DT
            ov[k] += max(-amax_dv, min(amax_dv, dv))
        nv = math.sqrt(sum(c * c for c in ov))
        if nv > VMAX:
            ov = [c * VMAX / nv for c in ov]
        for k in range(3):
            own[k] += ov[k] * DT
        # metryki liczone wobec PRAWDZIWEJ pozy intruza (jak sędzia z GT), nie wobec feedu
        d = math.hypot(trk_true[0] - own[0], trk_true[1] - own[1])
        d3 = math.sqrt((trk_true[0] - own[0]) ** 2 + (trk_true[1] - own[1]) ** 2 + (trk_true[2] - own[2]) ** 2)
        if t >= 3.0:                                                # faza po starcie (jak d_min_orbit sędziego)
            d_min = min(d_min, d3)
        if t_entry is None and r_lo <= d <= r_hi:
            t_entry = t
        if t_entry is not None and t >= t_entry:
            orbit_ticks += 1
            if r_lo <= d <= r_hi:
                in_band += 1
        t += DT
    frac = in_band / orbit_ticks if orbit_ticks else 0.0
    return t_entry, frac, (d_min if d_min < 1e9 else None)


def analog_d6(t_entry, frac, d_min):
    return (t_entry is not None and t_entry <= 25.0 and frac >= 0.85 and d_min is not None and d_min >= 4.0)


def oracle_sanity_12():
    """I1: wyrocznia w modelu punktowym (idealny feed, seed=1) → 12/12. Reprodukcja buildu ławki."""
    m = S.gen_manifest()
    res = []
    for cell in S.CELLS:
        ep = S.find_episode(m, cell["v_intr"], cell["bearing_deg"], seed=1)
        te, fr, dm = _rollout(ep, OracleController(ep), "ideal", seed=1)
        res.append((ep["scenario_id"], te is not None and te <= 25.0 and fr >= 0.85))
    return res


def gate_on_seeds(model, seeds):
    """Rollout FEED-B na 12 komórek × podane ziarna. Zwraca (tabela, n_rollout_pass, n_total)."""
    m = S.gen_manifest()
    table = []
    for cell in S.CELLS:
        ci = f"c{cell['cell_index']:02d}"
        per_seed = []
        for sd in seeds:
            ep = S.find_episode(m, cell["v_intr"], cell["bearing_deg"], seed=sd)
            te, fr, dm = _rollout(ep, NetController(model, ep), "B", seed=sd)
            per_seed.append({"seed": sd, "t_entry": te, "frac": round(fr, 4),
                             "d_min": round(dm, 3) if dm else None, "ok": analog_d6(te, fr, dm)})
        table.append({"cell": ci, "v_intr": cell["v_intr"], "bearing": cell["bearing_deg"],
                      "per_seed": per_seed, "cell_ok": all(p["ok"] for p in per_seed)})
    n_pass = sum(1 for r in table for p in r["per_seed"] if p["ok"])
    n_tot = sum(len(r["per_seed"]) for r in table)
    return table, n_pass, n_tot


def gate_arm(model):
    """Bramka N3(i) dla ramienia: rollout FEED-B na 12 komórek × ziarna TEST (4,8). Zwraca (tabela, n_pass)."""
    m = S.gen_manifest()
    test_seeds = [s for s in S.SEEDS if s % 4 == 0]                 # 4, 8
    table = []
    for cell in S.CELLS:
        ci = f"c{cell['cell_index']:02d}"
        per_seed = []
        for sd in test_seeds:
            ep = S.find_episode(m, cell["v_intr"], cell["bearing_deg"], seed=sd)
            te, fr, dm = _rollout(ep, NetController(model, ep), "B", seed=sd)
            per_seed.append({"seed": sd, "t_entry": te, "frac": round(fr, 4),
                             "d_min": round(dm, 3) if dm else None, "ok": analog_d6(te, fr, dm)})
        cell_ok = all(p["ok"] for p in per_seed)                   # komórka PASS ⇔ analog-D6 na OBU ziarnach TEST
        table.append({"cell": ci, "v_intr": cell["v_intr"], "bearing": cell["bearing_deg"],
                      "per_seed": per_seed, "cell_ok": cell_ok})
    n_pass = sum(1 for r in table if r["cell_ok"])
    return table, n_pass


if __name__ == "__main__":
    print("oracle sanity 12:", oracle_sanity_12())
