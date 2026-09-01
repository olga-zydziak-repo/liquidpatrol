#!/usr/bin/env python3
"""bench/tests_bench_judge.py — testy syntetyczne H (PRE §5): SUKCES + FAIL(a-e) + D9 (stall sim-robust)."""
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from bench.bench_judge import judge_episode

DT = 0.05
T = 100.0


def _intr(v_intr=1.0, start=(15.0, 0.0), T=T, dt=DT):
    """Intruz jedzie +N z v_intr od `start` (15 m od home jak siatka), z=-10 NED."""
    s = []
    t = 0.0
    while t <= T + 1e-9:
        s.append((round(t, 3), [start[0] + v_intr * t, start[1], -10.0]))
        t = round(t + dt, 6)
    return s


def _circle(intr, r, omega, z=-12.0, t_lo=0.0, t_hi=T, dt=DT):
    """Dron = intruz + r·(cos ωt, sin ωt) w płaszczyźnie N-E; z stałe."""
    out = []
    for t, ip in intr:
        if t < t_lo or t > t_hi:
            continue
        out.append((t, [ip[0] + r * math.cos(omega * t), ip[1] + r * math.sin(omega * t), z]))
    return out


def test_success_circle_r8():
    intr = _intr(1.0)
    omega = 1.8 / 8.0
    drone = _circle(intr, 8.0, omega)
    v = judge_episode(drone, intr, refuse_count=0, breach=False)
    assert v["success_D6"], v["fail_reasons"]
    assert v["t_entry_s"] == 0.0 and v["frac_band_6_10"] >= 0.99 and v["sweep_deg"] >= 630 and v["d_min_m"] >= 7.9


def test_fail_a_hover():
    intr = _intr(1.0)
    drone = [(t, [0.0, 0.0, -10.0]) for t, _ in intr]        # hover na home
    v = judge_episode(drone, intr)
    assert not v["success_D6"] and "a_entry" in v["fail_reasons"] and v["t_entry_s"] is None


def test_fail_b_radius_12():
    intr = _intr(1.0)
    omega = 1.8 / 8.0
    # wejście w pasmo na starcie (r=8 przez 3 s), potem orbita r=12 → frac_band niska
    d1 = _circle(intr, 8.0, omega, t_lo=0.0, t_hi=3.0)
    d2 = _circle(intr, 12.0, omega, t_lo=3.05, t_hi=T)
    drone = d1 + d2
    v = judge_episode(drone, intr)
    assert not v["success_D6"] and "b_frac" in v["fail_reasons"], v
    assert v["t_entry_s"] is not None and v["t_entry_s"] <= 25.0    # (a) spełnione


def test_fail_c_one_and_half_orbits():
    intr = _intr(1.0)
    omega = 1.5 * 2 * math.pi / 70.0                          # 1.5 okrążenia w oknie 70 s
    drone = _circle(intr, 8.0, omega)
    v = judge_episode(drone, intr)
    assert not v["success_D6"] and "c_sweep" in v["fail_reasons"], v
    assert v["frac_band_6_10"] >= 0.99 and 500 <= v["sweep_deg"] < 630


def test_fail_d_through_intruder():
    intr = _intr(0.0, start=(0.0, 0.0))                      # intruz statyczny w origin
    # dron przelatuje przez intruza: liniowo od (-15,0) do (15,0)
    drone = []
    t = 0.0
    while t <= 40.0:
        x = -15.0 + (30.0 / 40.0) * t
        drone.append((round(t, 3), [x, 0.0, -12.0]))
        t = round(t + DT, 6)
    v = judge_episode(drone, intr)
    assert not v["success_D6"] and "d_dmin" in v["fail_reasons"], v
    assert v["d_min_m"] < 4.0


def test_fail_e_refuse():
    intr = _intr(1.0)
    omega = 1.8 / 8.0
    drone = _circle(intr, 8.0, omega)
    v = judge_episode(drone, intr, refuse_count=1, breach=False)
    assert not v["success_D6"] and "e_refuse_breach" in v["fail_reasons"]
    v2 = judge_episode(drone, intr, refuse_count=0, breach=True)
    assert not v2["success_D6"] and "e_refuse_breach" in v2["fail_reasons"]


def _rtf_with_stall(stall_wall_s, t_mid=35.0, dt=0.1, T=100.0, n_deep=3):
    """rtf=1.0 wszędzie; JEDEN ciągły run deep (rtf<0.5) w połowie o wall-span dokładnie stall_wall_s."""
    out = []
    sim = 0.0; wall = 0.0
    while sim < t_mid:
        out.append({"sim": round(sim, 3), "wall": round(wall, 3), "rtf": 1.0}); wall += dt; sim = round(sim + dt, 6)
    step = stall_wall_s / (n_deep - 1) if n_deep > 1 else stall_wall_s
    for j in range(n_deep):                          # ciągły run: n_deep próbek, longest = (n_deep-1)*step = stall
        out.append({"sim": round(sim, 3), "wall": round(wall, 3), "rtf": 0.2}); wall += step; sim = round(sim + dt, 6)
    while sim <= T:
        out.append({"sim": round(sim, 3), "wall": round(wall, 3), "rtf": 1.0}); wall += dt; sim = round(sim + dt, 6)
    return out


def test_d9_stall_sim_metrics_robust_and_validity():
    intr = _intr(1.0)
    omega = 1.8 / 8.0
    drone = _circle(intr, 8.0, omega)
    base = judge_episode(drone, intr, rtf=[], timejump=0)
    # stall 1.4 s wall (≤1.5) → metryki sim BEZ ZMIAN; V1 FAIL (deep-stall), V2 PASS, V3 PASS
    r14 = _rtf_with_stall(1.4)
    v14 = judge_episode(drone, intr, rtf=r14, timejump=0)
    for k in ("t_entry_s", "frac_band_6_10", "frac_tight_7_9", "sweep_deg", "d_min_m"):
        assert v14[k] == base[k], f"metryka {k} zmieniona przez stall (nie-sim!)"
    assert v14["valid_V1"] is False, "V1 nie odrzucił stalla"
    assert v14["valid_V2"] is True, ("V2 powinien przejść przy 1.4s", v14["stalls"])
    assert v14["valid_V3"] is True
    # stall 2.0 s wall (>1.5, per ANEKS V2) → V2 FAIL, V3 PASS (dowód że cap V2 działa; PROMPT §5 "2s→V2 PASS"
    # SPRZECZNE z ANEKS D9 longest≤1.5 — aneks wygrywa, nota §6)
    r20 = _rtf_with_stall(2.0)
    v20 = judge_episode(drone, intr, rtf=r20, timejump=0)
    for k in ("t_entry_s", "frac_band_6_10", "sweep_deg", "d_min_m"):
        assert v20[k] == base[k]
    assert v20["valid_V2"] is False, ("V2 powinien odrzucić 2s stall", v20["stalls"])
    assert v20["valid_V3"] is True


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_") and callable(f):
            f(); print(f"OK {n}")
    print("tests_bench_judge: ALL PASS")
