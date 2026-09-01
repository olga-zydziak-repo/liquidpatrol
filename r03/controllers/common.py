#!/usr/bin/env python3
"""r03/controllers/common.py — pomocnicze kontrolerów (niepinowane). Bez gz, bez GT, bez losowości."""
import math


def clip_scalar(x, lo, hi):
    return lo if x < lo else (hi if x > hi else x)


def clip_v(v, vmax):
    """Saturacja wektora prędkości do |v| ≤ vmax (skalowanie, zachowuje kierunek). v = [vn, ve, vd]."""
    n = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    if n <= vmax or n < 1e-12:
        return [float(v[0]), float(v[1]), float(v[2])]
    s = vmax / n
    return [v[0] * s, v[1] * s, v[2] * s]


def unit2(x, y):
    n = math.hypot(x, y)
    if n < 1e-9:
        return (0.0, 0.0)
    return (x / n, y / n)
