#!/usr/bin/env python3
"""bench/tests_campaign_analyze.py — test D9=V3 (override sędziego), Wilson, blok1 order, judge_boot na re-shakeout."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from bench import scenarios as S
from bench.campaign_analyze import wilson, blok1_episode_ids, judge_boot, aggregate_p_exec, D9_V3_PARAMS
from bench.bench_judge import judge_episode
import math


def test_blok1_ids_48():
    m = S.gen_manifest()
    ids = blok1_episode_ids(m)
    assert len(ids) == 48
    assert all(m["episodes"][i]["block"] == 1 for i in ids)


def test_wilson():
    p, lo, hi = wilson(48, 48)
    assert p == 1.0 and lo < 1.0 and hi == 1.0            # 48/48 → dolny < 1
    p, lo, hi = wilson(0, 10)
    assert p == 0.0 and lo == 0.0
    p, lo, hi = wilson(8, 10)
    assert 0.0 < lo < 0.8 < hi <= 1.0


def _circle(intr, r, omega, z=-12.0, T=100.0, dt=0.05):
    out = []; t = 0.0
    while t <= T:
        ip = _pos(intr, t)
        out.append((round(t, 3), [ip[0] + r * math.cos(omega * t), ip[1] + r * math.sin(omega * t), z]))
        t = round(t + dt, 6)
    return out


def _pos(v_intr, t):
    return [15.0 + v_intr * t, 0.0, -10.0]


def test_d9v3_longest_stall_rule():
    """D9=V3: nieważny wyłącznie gdy najdłuższy stall > 3 s wall. Stall 2.5 s → ważny; 3.5 s → nieważny."""
    intr = [(round(t, 3), _pos(1.0, t)) for t in [i * 0.05 for i in range(2001)]]
    drone = _circle(1.0, 8.0, 1.8 / 8.0)
    drone = [(t, p) for t, p in [(round(i * 0.05, 3), None) for i in range(0)]] or drone

    def rtf_stall(longest):
        out = []; sim = 0.0; wall = 0.0
        while sim < 40.0:
            out.append({"sim": round(sim, 3), "wall": round(wall, 3), "rtf": 1.0}); wall += 0.1; sim = round(sim + 0.1, 3)
        for j in range(3):                                # run deep, span = longest
            out.append({"sim": round(sim, 3), "wall": round(wall, 3), "rtf": 0.2}); wall += longest / 2.0; sim = round(sim + 0.1, 3)
        while sim < 100.0:
            out.append({"sim": round(sim, 3), "wall": round(wall, 3), "rtf": 1.0}); wall += 0.1; sim = round(sim + 0.1, 3)
        return out
    v25 = judge_episode(drone, intr, rtf=rtf_stall(2.5), timejump=0, params=dict(D9_V3_PARAMS))
    v35 = judge_episode(drone, intr, rtf=rtf_stall(3.5), timejump=0, params=dict(D9_V3_PARAMS))
    assert v25["valid_V3"] is True, ("stall 2.5s < 3s → ważny", v25["stalls"])
    assert v35["valid_V3"] is False, ("stall 3.5s > 3s → nieważny", v35["stalls"])


def test_judge_boot_on_reshakeout_b2():
    """judge_boot na realnym boocie re-shakeout b2 (v1.2): 4 epizody, D6 4/4, wszystkie ważne D9=V3."""
    od = os.path.join(ROOT, "results/BENCH/reshakeout/boot2")
    if not os.path.exists(os.path.join(od, "trace.jsonl")):
        return                                           # brak danych (środowisko) — pomiń
    vs = judge_boot(od)
    assert len(vs) == 4
    agg = aggregate_p_exec(vs)
    assert agg["n_valid"] == 4 and agg["n_success"] == 4 and agg["p_exec"] == 1.0


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_") and callable(f):
            f(); print(f"OK {n}")
    print("tests_campaign_analyze: ALL PASS")
