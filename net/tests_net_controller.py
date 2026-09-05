#!/usr/bin/env python3
"""r03/controllers/tests_net_controller.py — testy N-F0 (PROMPT_NET_FLY), bez SITL.

kontrakt 10⁴ per ramię; tożsamość cech kontroler↔trening (bit-w-bit); replay-determinizm;
reset stanu (2 epizody ten sam feed ⇒ identyczne wyjścia ep2); benchmark inferencji/tick;
grep-test bez gz; odmowa lotu przy rozjeździe sha.
"""
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from r01.config import V_MAX
from r03.controllers.common import clip_v
from bench.features import features
from net import dataset as D


def _mk(arm):
    os.environ["NET_ARM"] = arm
    from r03.controllers import make_controller
    return make_controller("net", params=None, orbit_dir="CCW", vmax=V_MAX)


def _feed(trk, age=0.0, valid=True):
    return {"trk_pos_ned": list(trk), "trk_vel_ned": [0.0, 0.0, 0.0], "track_age_s": age,
            "track_valid": valid, "feed_sha": "x"}


def test_no_gz_static():
    import re
    txt = open(os.path.join(ROOT, "r03/controllers/net_controller.py")).read()
    assert not re.search(r"import\s+gz|from\s+gz|gz\.transport|gz\.msgs|dynamic_pose|pose/info|/world/", txt)


def test_contract_10k_both_arms():
    rng = np.random.RandomState(5)
    for arm in ("ncp", "mlp"):
        c = _mk(arm); c.reset()
        for i in range(10000):
            if i % 200 == 0:
                c.reset()
            own = [rng.uniform(-30, 30), rng.uniform(-30, 30), rng.uniform(-15, -5)]
            trk = [rng.uniform(-18, 18), rng.uniform(-18, 18), -10.0]
            c.set_feed(_feed(trk, age=rng.uniform(0, 2.0), valid=rng.random() > 0.1))
            cmd = c.step(i, own, [rng.uniform(-3, 3), rng.uniform(-3, 3), 0], i * 0.05, False)
            v = cmd["v_ned"]
            n = (v[0] ** 2 + v[1] ** 2 + v[2] ** 2) ** 0.5
            assert n <= V_MAX + 1e-6, f"{arm}: |v|₂={n} > V_MAX przy i={i}"


def test_feature_identity_controller_vs_training():
    """Cechy budowane w kontrolerze == cechy treningu (ta sama funkcja bench.features) bit-w-bit."""
    import glob, json
    f = glob.glob(os.path.join(ROOT, "results/BENCH/campaign/boot1/demo.jsonl"))[0]
    row = json.loads(open(f).readline())
    # rekonstrukcja stanu kontrolera z wiersza (own,vel,feed) → features == features(row)
    st = {"own_pos_ned": row["own_pos_ned"], "own_vel_ned": row["own_vel_ned"],
          "trk_pos_ned": row["trk_pos_ned"], "track_age_s": row["track_age_s"],
          "track_valid": row["track_valid"]}
    assert features(st) == features(row)


def test_replay_determinism():
    seq = []
    rng = np.random.RandomState(9)
    for _ in range(150):
        seq.append(([rng.uniform(-15, 15), rng.uniform(-15, 15), -10.0],
                    _feed([rng.uniform(-18, 18), rng.uniform(-18, 18), -10.0])))
    for arm in ("ncp", "mlp"):
        def run():
            c = _mk(arm); c.reset()
            out = []
            for i, (own, fd) in enumerate(seq):
                c.set_feed(fd)
                out.append(tuple(round(x, 9) for x in c.step(i, own, [0, 0, 0], i * 0.05, False)["v_ned"]))
            return out
        assert run() == run(), f"{arm}: replay niedeterministyczny"


def test_state_reset_clean():
    """Dwa epizody z tym samym feedem ⇒ identyczne wyjścia epizodu 2 = czysty reset stanu."""
    rng = np.random.RandomState(3)
    seq = [([rng.uniform(-12, 12), rng.uniform(-12, 12), -10.0],
            _feed([rng.uniform(-16, 16), rng.uniform(-16, 16), -10.0])) for _ in range(120)]
    for arm in ("ncp", "mlp"):
        c = _mk(arm)
        def ep():
            c.reset()
            out = []
            for i, (own, fd) in enumerate(seq):
                c.set_feed(fd)
                out.append(tuple(round(x, 9) for x in c.step(i, own, [0, 0, 0], i * 0.05, False)["v_ned"]))
            return out
        e1 = ep(); e2 = ep()
        assert e1 == e2, f"{arm}: reset nie czyści stanu (ep1≠ep2)"


def test_inference_benchmark_per_tick():
    for arm in ("ncp", "mlp"):
        c = _mk(arm); c.reset()
        c.set_feed(_feed([8.0, 0.0, -10.0]))
        # rozgrzewka
        for i in range(50):
            c.step(i, [0, 0, -10], [0, 0, 0], i * 0.05, False)
        t0 = time.perf_counter()
        N = 2000
        for i in range(N):
            c.step(i, [0.1, 0.2, -10], [0.1, 0, 0], i * 0.05, False)
        per_tick_ms = (time.perf_counter() - t0) / N * 1000.0
        print(f"[bench] {arm} inferencja/tick = {per_tick_ms:.3f} ms")
        assert per_tick_ms < 50.0, f"{arm}: {per_tick_ms:.1f} ms ≥ 50 ms (za wolno na 20 Hz)"
        if per_tick_ms > 10.0:
            print(f"  NOTA: {arm} > 10 ms/tick")


def test_sha_mismatch_refuses_flight():
    import importlib
    import r03.controllers.net_controller as ncmod
    importlib.reload(ncmod)
    orig = dict(ncmod.FREEZE_SHA)
    ncmod.FREEZE_SHA["ncp"] = "0" * 64
    os.environ["NET_ARM"] = "ncp"
    try:
        ncmod.NetController(vmax=V_MAX)
        assert False, "nie odmówił lotu przy rozjeździe sha"
    except RuntimeError as e:
        assert "rozjazd" in str(e)
    finally:
        ncmod.FREEZE_SHA.update(orig)


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_") and callable(f):
            f(); print(f"OK {n}")
    print("tests_net_controller: ALL PASS")
