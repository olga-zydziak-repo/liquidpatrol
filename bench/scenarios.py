#!/usr/bin/env python3
"""bench/scenarios.py — siatka scenariuszy ławki (PROMPT_BENCH_BUILD A, ANEKS P3).

12 komórek (v_intr ∈ {0, 0.5, 1.0} × namiar startowy {0, 90, 180, 270}° przy zasięgu 15 m od home)
× 10 ziaren = 120 epizodów. Kolejność: blok 1 = ziarna 1–4 (48, p_exec), blok 2 = ziarna 5–10 (72, zbiór).
TEST = (seed % 4 == 0). Trajektoria intruza: odcinki stałej prędkości, zmiana kursu co U(10, 20) s,
DYSK r ≤ 18 m wokół home (32 − 10 − 3.5 − 0.5), z = 10 m. Kierunek orbity CW/CCW z ziarna.

Determinizm: RNG = random.Random(seed*100 + cell_index). `position_at(ep, t_rel)` = f(sim_t) (interpolacja
liniowa po odcinkach). Frame = HOME-planar (x=Północ, y=Wschód, home=origin); intruder_motion mapuje do gz.
"""
import json
import math
import os
import random

HOME = (0.0, 0.0)
RANGE0 = 15.0           # zasięg startowy intruza [m]
DISK_R = 18.0           # twardy dysk trajektorii [m]
Z_INTR = 10.0           # stała wysokość intruza [m]
EP_DUR_S = 110.0        # dług. trajektorii na epizod (T_orb 70 + podejście + zapas)
V_INTR = (0.0, 0.5, 1.0)
BEARINGS = (0, 90, 180, 270)
SEEDS = tuple(range(1, 11))            # 1..10
BLOCK1_SEEDS = (1, 2, 3, 4)
BLOCK2_SEEDS = (5, 6, 7, 8, 9, 10)

CELLS = [{"cell_index": i, "v_intr": v, "bearing_deg": b}
         for i, (v, b) in enumerate((v, b) for v in V_INTR for b in BEARINGS)]


def _start_pos(bearing_deg):
    th = math.radians(bearing_deg)
    return (RANGE0 * math.cos(th), RANGE0 * math.sin(th))


def gen_episode(cell, seed):
    # Odcinki: KONIEC każdego ≤ DISK_R (dystans-od-origin wypukły wzdłuż prostej → max w końcach;
    # oba końce ≤18 ⇒ cała trasa ≤18). Blisko krawędzi/przy przekroczeniu — kurs ku środkowi.
    ci = cell["cell_index"]
    v_intr = cell["v_intr"]
    rng = random.Random(seed * 100 + ci)
    sx, sy = _start_pos(cell["bearing_deg"])
    segs = []
    t = 0.0
    x, y = sx, sy
    if v_intr <= 1e-9:
        segs.append({"t0": 0.0, "t1": EP_DUR_S, "x0": round(x, 4), "y0": round(y, 4),
                     "heading_deg": 0.0, "v": 0.0})
    else:
        while t < EP_DUR_S:
            r = math.hypot(x, y)
            if r > 14.0:
                heading = math.degrees(math.atan2(-y, -x))          # blisko krawędzi → ku środkowi
            else:
                heading = rng.uniform(0.0, 360.0)
            dur = rng.uniform(10.0, 20.0)
            hx, hy = math.cos(math.radians(heading)), math.sin(math.radians(heading))
            # cap dur na czas WYJŚCIA z dysku: |start + v·h·t| = DISK_R (kwadrat: v²t² + 2v(x·hx+y·hy)t + (r²−R²)=0)
            a = v_intr * v_intr
            b = 2.0 * v_intr * (x * hx + y * hy)
            c = r * r - DISK_R * DISK_R                              # ≤ 0 (start w dysku)
            disc = b * b - 4.0 * a * c
            t_exit = (-b + math.sqrt(disc)) / (2.0 * a) if a > 0 and disc >= 0 else dur
            dur_ok = min(dur, max(0.1, t_exit))                     # ≤ czas wyjścia → koniec ≤ DISK_R
            ex, ey = x + v_intr * hx * dur_ok, y + v_intr * hy * dur_ok
            segs.append({"t0": round(t, 4), "t1": round(t + dur_ok, 4), "x0": round(x, 4), "y0": round(y, 4),
                         "heading_deg": round(heading, 4), "v": v_intr})
            x, y, t = ex, ey, t + dur_ok
    orbit_dir = rng.choice(["CW", "CCW"])
    block = 1 if seed in BLOCK1_SEEDS else 2
    return {
        "scenario_id": f"c{ci:02d}_s{seed:02d}",
        "cell": {"v_intr": v_intr, "bearing_deg": cell["bearing_deg"]},
        "cell_index": ci,
        "seed": seed,
        "block": block,
        "is_test": (seed % 4 == 0),
        "orbit_dir": orbit_dir,
        "start_pos": [round(sx, 4), round(sy, 4), Z_INTR],
        "z": Z_INTR,
        "ep_dur_s": EP_DUR_S,
        "segments": segs,
    }


def position_at(ep, t_rel):
    """Poza intruza (x, y, z) w chwili t_rel [s sim] od startu epizodu. Interpolacja liniowa po odcinku."""
    z = ep["z"]
    segs = ep["segments"]
    if t_rel <= 0:
        return (segs[0]["x0"], segs[0]["y0"], z)
    for s in segs:
        if s["t0"] <= t_rel < s["t1"]:
            dt = t_rel - s["t0"]
            hx = math.cos(math.radians(s["heading_deg"])); hy = math.sin(math.radians(s["heading_deg"]))
            return (s["x0"] + s["v"] * hx * dt, s["y0"] + s["v"] * hy * dt, z)
    last = segs[-1]                                                  # po końcu: trzymaj koniec ostatniego
    dt = last["t1"] - last["t0"]
    hx = math.cos(math.radians(last["heading_deg"])); hy = math.sin(math.radians(last["heading_deg"]))
    return (last["x0"] + last["v"] * hx * dt, last["y0"] + last["v"] * hy * dt, z)


def gen_manifest():
    """120 epizodów: blok 1 (ziarna 1–4 × 12 komórek = 48), blok 2 (ziarna 5–10 × 12 = 72). Seed-major w bloku."""
    eps = []
    for seed in BLOCK1_SEEDS:
        for cell in CELLS:
            eps.append(gen_episode(cell, seed))
    for seed in BLOCK2_SEEDS:
        for cell in CELLS:
            eps.append(gen_episode(cell, seed))
    for i, e in enumerate(eps):
        e["episode_id"] = i
    return {
        "n_episodes": len(eps),
        "n_cells": len(CELLS),
        "seeds": list(SEEDS),
        "block1_seeds": list(BLOCK1_SEEDS),
        "block2_seeds": list(BLOCK2_SEEDS),
        "disk_r_m": DISK_R, "range0_m": RANGE0, "z_intr_m": Z_INTR, "ep_dur_s": EP_DUR_S,
        "test_rule": "seed % 4 == 0",
        "cells": CELLS,
        "episodes": eps,
    }


def find_episode(manifest, v_intr, bearing_deg, seed):
    for e in manifest["episodes"]:
        if (abs(e["cell"]["v_intr"] - v_intr) < 1e-9 and e["cell"]["bearing_deg"] == bearing_deg
                and e["seed"] == seed):
            return e
    return None


if __name__ == "__main__":
    m = gen_manifest()
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "results", "BENCH", "scenario_manifest.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(m, f, indent=1)
    print(f"scenario_manifest: {m['n_episodes']} epizodów → {out}")
