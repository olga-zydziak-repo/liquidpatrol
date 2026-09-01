#!/usr/bin/env python3
"""bench/tests_orbit_executor.py — testy D (PROMPT_BENCH_BUILD):
(i) grep statyczny: r03/controllers/* bez importów gz / łańcuchów topików GT;
(ii) replay: ten sam feed dwa razy ⇒ bit-identyczne cmd_v_ned;
(iii) kontrakt: 10⁴ losowych wejść ⇒ |v| ≤ V_MAX i klucze zgodne z base.py;
(iv) kinematyczny model punktowy (bez SITL): wejście w pasmo ≤25 s ∧ frakcja ≥0.85 dla 12 komórek, idealny feed.
"""
import glob
import json
import math
import os
import random
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from r03.controllers.orbit_executor import OrbitExecutor
from r03.controllers.base import SetpointSource
from bench import scenarios as S

VMAX = 3.0
PARAMS = json.load(open(os.path.join(ROOT, "bench/executor_params.json")))
RET_KEYS = {"tgt_ned", "v_ned", "yaw", "seg_i", "dist", "wps", "extra"}


def test_no_gz_in_controllers():
    bad = []
    for f in glob.glob(os.path.join(ROOT, "r03/controllers/*.py")):
        txt = open(f).read()
        if re.search(r"import\s+gz|from\s+gz|gz\.transport|gz\.msgs|dynamic_pose|pose/info|/world/", txt):
            bad.append(os.path.basename(f))
    assert not bad, f"gz/GT w kontrolerach: {bad}"


def _feed(trk, tvel, age=0.0, valid=True):
    return {"trk_pos_ned": list(trk), "trk_vel_ned": list(tvel), "track_age_s": age,
            "track_valid": valid, "feed_sha": "x"}


def test_replay_deterministic():
    seq = []
    rng = random.Random(42)
    for _ in range(200):
        seq.append(([rng.uniform(-15, 15), rng.uniform(-15, 15), rng.uniform(-12, -8)],
                    _feed([rng.uniform(-18, 18), rng.uniform(-18, 18), -10.0],
                          [rng.uniform(-1, 1), rng.uniform(-1, 1), 0.0])))

    def run():
        ex = OrbitExecutor(PARAMS, orbit_dir="CCW", vmax=VMAX); ex.reset()
        outs = []
        for i, (own, fd) in enumerate(seq):
            ex.set_feed(fd)
            outs.append(ex.step(i, own, [0, 0, 0], i * 0.05, False)["v_ned"])
        return outs
    a, b = run(), run()
    assert a == b, "egzekutor niedeterministyczny (replay ≠)"


def test_contract_vmax_and_keys():
    rng = random.Random(7)
    ex = OrbitExecutor(PARAMS, orbit_dir="CW", vmax=VMAX)
    for i in range(10000):
        if i % 137 == 0:
            ex.reset()
        if i % 500 == 0:
            ex.begin_reset()
        own = [rng.uniform(-30, 30), rng.uniform(-30, 30), rng.uniform(-15, -5)]
        valid = rng.random() > 0.1
        fd = _feed([rng.uniform(-18, 18), rng.uniform(-18, 18), -10.0],
                   [rng.uniform(-1.5, 1.5), rng.uniform(-1.5, 1.5), 0.0],
                   age=rng.uniform(0, 2.0), valid=valid)
        ex.set_feed(fd)
        cmd = ex.step(i, own, [rng.uniform(-3, 3), rng.uniform(-3, 3), 0], i * 0.05, False)
        assert set(cmd.keys()) == RET_KEYS, f"klucze {set(cmd.keys())} ≠ base.py"
        v = cmd["v_ned"]
        n = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)
        assert n <= VMAX + 1e-6, f"|v|={n:.4f} > V_MAX przy i={i}"


def _sim_cell(ep, dur_s=95.0, dt=0.05, a_max=2.0):
    """Model punktowy: dron śledzi cmd_v z limitem accel a_max i |v|≤VMAX; idealny feed = position_at(ep)."""
    ex = OrbitExecutor(PARAMS, orbit_dir=ep["orbit_dir"], vmax=VMAX,
                       home_ned=(0.0, 0.0, -PARAMS["home_hover_alt_m"]))
    ex.reset()
    own = [0.0, 0.0, -PARAMS["home_hover_alt_m"]]
    ov = [0.0, 0.0, 0.0]
    t = 0.0
    t_entry = None
    in_band_orbit = 0
    orbit_ticks = 0
    r_lo, r_hi = PARAMS["band_lo_m"], PARAMS["band_hi_m"]
    while t < dur_s:
        px, py, pz = S.position_at(ep, t)                  # scenario (N,E,alt)
        trk = [px, py, -pz]                                # NED
        # idealna prędkość intruza (różnica skończona)
        px2, py2, _ = S.position_at(ep, t + 0.1)
        tvel = [(px2 - px) / 0.1, (py2 - py) / 0.1, 0.0]
        ex.set_feed(_feed(trk, tvel, age=0.0, valid=True))
        cmd = ex.step(int(t / dt), own, ov, t, False)
        cv = cmd["v_ned"]
        # śledzenie z limitem accel
        for k in range(3):
            dv = cv[k] - ov[k]
            amax_dv = a_max * dt
            dv = max(-amax_dv, min(amax_dv, dv))
            ov[k] += dv
        # clip |v|
        nv = math.sqrt(sum(c * c for c in ov))
        if nv > VMAX:
            ov = [c * VMAX / nv for c in ov]
        for k in range(3):
            own[k] += ov[k] * dt
        d = math.hypot(trk[0] - own[0], trk[1] - own[1])
        if t_entry is None and r_lo <= d <= r_hi:
            t_entry = t
        if t_entry is not None and t >= t_entry:
            orbit_ticks += 1
            if r_lo <= d <= r_hi:
                in_band_orbit += 1
        t += dt
    frac = in_band_orbit / orbit_ticks if orbit_ticks else 0.0
    return t_entry, frac


def test_kinematic_point_model_12_cells():
    m = S.gen_manifest()
    fails = []
    for cell in S.CELLS:
        ep = S.find_episode(m, cell["v_intr"], cell["bearing_deg"], seed=1)
        t_entry, frac = _sim_cell(ep)
        ok = (t_entry is not None and t_entry <= 25.0 and frac >= 0.85)
        if not ok:
            fails.append((ep["scenario_id"], t_entry, round(frac, 3)))
    assert not fails, f"model punktowy FAIL komórek: {fails}"


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_") and callable(f):
            f(); print(f"OK {n}")
    print("tests_orbit_executor: ALL PASS")
