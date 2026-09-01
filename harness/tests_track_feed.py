#!/usr/bin/env python3
"""harness/tests_track_feed.py — test C (FEED-B): L, σ, p_drop w ±deklaracji; σ_v regresji; sim-time inwariant."""
import math
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from harness.track_feed import FeedB, _slope

V = 1.0          # intruz 1 m/s wzdłuż N (x)
GT_HZ = 50.0
CTRL_HZ = 20.0


def _run(seed, dur_s, wall_stall=False):
    """GT liniowe x=V·t streamowane 50 Hz PRZEPLATANE z próbkowaniem kontrolera 20 Hz (realistycznie:
    GT napływa w miarę sim, kontroler próbkuje bieżący sim_now). Zwraca [(sim_now, out, fresh)]."""
    feed = FeedB(seed)
    out = []
    STEP = 1.0 / GT_HZ                     # najdrobniejszy krok = tempo GT
    next_ctrl = 0.0
    t = -1.0
    while t < dur_s + 1e-9:
        feed.push_gt(t, [V * t, 0.0, -10.0])
        if t >= next_ctrl - 1e-9 and t >= 0.0:
            s = feed.sample(t)
            out.append((t, s, s["track_age_s"] == 0.0 and s["track_valid"]))
            if wall_stall and abs(t - round(dur_s / 2)) < 1e-6:
                time.sleep(0.05)          # STALL WALL — nie wolno wpłynąć na okno (sim-only)
            next_ctrl += 1.0 / CTRL_HZ
        t = round(t + STEP, 6)
    return out


def test_L_sigma_pdrop():
    feed = FeedB(seed=1)
    out = []
    STEP = 1.0 / GT_HZ; next_ctrl = 0.0; t = -1.0
    while t < 300.0 + 1e-9:
        feed.push_gt(t, [V * t, 0.0, -10.0])
        if t >= next_ctrl - 1e-9 and t >= 0.0:
            s = feed.sample(t)
            out.append((t, s, s["track_age_s"] == 0.0 and s["track_valid"]))
            next_ctrl += 1.0 / CTRL_HZ
        t = round(t + STEP, 6)
    fresh = [(t, s) for t, s, f in out if f]
    assert len(fresh) > 2000, f"fresh={len(fresh)}"
    offs = [s["trk_pos_ned"][0] - V * t for t, s in fresh]
    mean_off = sum(offs) / len(offs)
    L_meas = -mean_off / V
    assert abs(L_meas - 0.20) <= 0.02, f"L={L_meas:.4f} poza ±10% 0.20"
    sig = math.sqrt(sum((o - mean_off) ** 2 for o in offs) / len(offs))
    assert abs(sig - 0.5) <= 0.05, f"σ={sig:.4f} poza ±10% 0.5"
    p = feed.n_drops / feed.n_feed_ticks
    tol = max(0.005, 3.0 * math.sqrt(0.05 * 0.95 / feed.n_feed_ticks))
    assert abs(p - 0.05) <= tol, f"p_drop={p:.4f} (n_tick={feed.n_feed_ticks}) poza 0.05±{tol:.4f}"


def test_sigma_v_regression():
    out = _run(seed=3, dur_s=120.0)
    fresh = [(t, s) for t, s, f in out if f]
    vx = [s["trk_vel_ned"][0] for _, s in fresh if abs(s["trk_vel_ned"][0]) > 1e-9]
    assert len(vx) > 500
    mean_v = sum(vx) / len(vx)
    sd_v = math.sqrt(sum((v - mean_v) ** 2 for v in vx) / len(vx))
    assert abs(mean_v - V) < 0.15, f"mean trk_vel={mean_v:.3f} ≠ {V}"
    assert 0.55 * 0.7 <= sd_v <= 0.55 * 1.3, f"σ_v={sd_v:.3f} poza 0.55±30%"


def test_sim_time_invariant_under_wall_stall():
    a = _run(seed=7, dur_s=20.0, wall_stall=False)
    b = _run(seed=7, dur_s=20.0, wall_stall=True)
    assert len(a) == len(b)
    for (ta, sa, _), (tb, sb, _) in zip(a, b):
        assert sa["trk_pos_ned"] == sb["trk_pos_ned"], "stall wall zmienił pozycję feedu (nie-sim-time!)"
        assert sa["trk_vel_ned"] == sb["trk_vel_ned"], "stall wall zmienił okno regresji (nie-sim-time!)"
        assert sa["track_age_s"] == sb["track_age_s"]


def test_slope_helper():
    ts = [0, 1, 2, 3]; xs = [0, 2, 4, 6]
    assert abs(_slope(ts, xs) - 2.0) < 1e-9


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_") and callable(f):
            f(); print(f"OK {n}")
    print("tests_track_feed: ALL PASS")
