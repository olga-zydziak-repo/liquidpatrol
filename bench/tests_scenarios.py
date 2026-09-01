#!/usr/bin/env python3
"""bench/tests_scenarios.py — test A (PROMPT_BENCH_BUILD): determinizm manifestu + dysk 18 m."""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from bench import scenarios as S


def test_manifest_deterministic_bitidentical():
    a = json.dumps(S.gen_manifest(), sort_keys=True)
    b = json.dumps(S.gen_manifest(), sort_keys=True)
    assert a == b, "manifest NIE bit-identyczny przy dwóch generacjach z tych samych ziaren"


def test_counts_and_blocks():
    m = S.gen_manifest()
    assert m["n_episodes"] == 120
    assert len(m["cells"]) == 12
    b1 = [e for e in m["episodes"] if e["block"] == 1]
    b2 = [e for e in m["episodes"] if e["block"] == 2]
    assert len(b1) == 48 and len(b2) == 72
    # blok 1 = ziarna 1-4, blok 2 = 5-10
    assert set(e["seed"] for e in b1) == {1, 2, 3, 4}
    assert set(e["seed"] for e in b2) == {5, 6, 7, 8, 9, 10}
    # TEST = seed%4==0 → dokładnie jedno ziarno testowe na komórkę w bloku 1 (seed 4)
    test_b1 = [e for e in b1 if e["is_test"]]
    assert len(test_b1) == 12 and all(e["seed"] == 4 for e in test_b1)


def test_no_point_outside_disk():
    m = S.gen_manifest()
    worst = 0.0
    for e in m["episodes"]:
        # próbkuj gęsto po całej trajektorii
        t = 0.0
        while t <= e["ep_dur_s"]:
            x, y, z = S.position_at(e, t)
            r = math.hypot(x, y)
            worst = max(worst, r)
            assert r <= S.DISK_R + 1e-6, f"{e['scenario_id']} t={t}: r={r:.3f} > {S.DISK_R}"
            t += 0.25
    assert worst <= S.DISK_R + 1e-6


def test_static_cell_no_motion():
    m = S.gen_manifest()
    for e in m["episodes"]:
        if e["cell"]["v_intr"] == 0.0:
            p0 = S.position_at(e, 0.0); p1 = S.position_at(e, 50.0)
            assert p0 == p1, f"{e['scenario_id']} v=0 ale poza się zmienia"


def test_find_episode_shakeout_cells():
    m = S.gen_manifest()
    for v, b in [(0.0, 0), (0.5, 90), (1.0, 180), (1.0, 270)]:
        e = S.find_episode(m, v, b, 1)
        assert e is not None and e["seed"] == 1 and e["block"] == 1


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_") and callable(f):
            f(); print(f"OK {n}")
    print("tests_scenarios: ALL PASS")
