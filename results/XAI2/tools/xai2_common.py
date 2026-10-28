#!/usr/bin/env python3
"""results/XAI2/tools/xai2_common.py — wspólne dla narzędzi nogi XAI-II (PRE_XAI2 §1).

Przyrządy WYŁĄCZNIE importem (zero edycji FROZEN): korpus i replay z
xai_thm_diff (b4454cb9) / xai_replay (ac9551ab), wagi ncp 0337d5ea kopią
przez model_of/fresh_model, clip_v r03/controllers/common.py:11, przedziałówka
ia_* z xai_proofs (e7a65b37).

WŁASNY krok wsadowy step_vec = niezależna implementacja litery models.py:127-138
(te same macierze z npz, własny kod) — kotwica KROK 0 (ii): replay z h₀=0 tym
krokiem musi odtworzyć xai_replay co do max |Δy| ≤ 1e-12.
"""
import json
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
for p in (ROOT, os.path.join(ROOT, "results", "XAI", "tools"),
          os.path.join(ROOT, "results", "XAI_RECON", "tools")):
    if p not in sys.path:
        sys.path.insert(0, p)

from xai_thm_diff import corpus_index, replay_all, fresh_model, make_mutant, install, jac_h  # noqa: E402
from xai_proofs import ia_affine, ia_mul, ia_mul_scalar  # noqa: E402
from r03.controllers.common import clip_v  # noqa: E402

V_MAX = 3.0                      # r01/config.py:24
OUTD = os.path.join(ROOT, "results", "XAI2")

FEATURE_MAP = [("rel_n (rel_x)", 0), ("rel_e (rel_y)", 1), ("rel_d (rel_z)", 2),
               ("own_vn", 3), ("own_ve", 4), ("own_vd", 5),
               ("track_age_s", 6), ("track_valid", 7)]


def assert_mapping(m):
    """KROK 0 (i) / PRE §1: indeks → nazwa → (mean, std) z npz; std[0]≈6.10,
    std[1]≈6.03 (rel_n, rel_e), std[2]≈0.503 (rel_d). Rozjazd ⇒ ŚMIERĆ S1."""
    rows = [{"i": i, "nazwa": nm, "mean": round(float(m.input_mean[i]), 5),
             "std": round(float(m.input_std[i]), 5)} for nm, i in FEATURE_MAP]
    ok = (abs(m.input_std[0] - 6.10) < 0.01 and abs(m.input_std[1] - 6.03) < 0.01
          and abs(m.input_std[2] - 0.503) < 0.001)
    return {"tabela": rows, "pass": bool(ok)}


def step_vec(m, X, H):
    """Własna implementacja kroku CfC (litera models.py:127-138), wsadowa.
    X:(B,8) znorm., H:(B,20) → (y_raw:(B,3) głowa PRZED clip_v, h2, bb, g, hh, gate)."""
    concat = np.concatenate([X, H], axis=1)
    bb = np.tanh(concat @ m.Wb + m.bb0)
    g = np.tanh(bb @ m.Wg + m.bg)
    hh = np.tanh(bb @ m.Wh + m.bh)
    gate = 1.0 / (1.0 + np.exp(-(bb @ m.Wt + m.bt)))
    h2 = gate * g + (1.0 - gate) * hh
    y_raw = np.tanh(h2 @ m.Wo + m.bo) * m.vmax
    return y_raw, h2, bb, g, hh, gate


def raw_pass(m, rep):
    """Sekwencyjny przebieg epizodu WŁASNYM krokiem na x z repleyu (h₀ = 0,
    hold = stan zamrożony — semantyka xai_replay). Zwraca per tick inferencji:
    y_raw, y_clip, h_prev, bb/g/hh/gate (do jakobianów), oraz max |Δy| vs rep["y"]."""
    T = len(rep["t"])
    h = np.zeros((1, 20))
    out = {"y_raw": np.full((T, 3), np.nan), "y_clip": np.zeros((T, 3)),
           "h_prev": np.full((T, 20), np.nan),
           "bb": np.full((T, 20), np.nan), "g": np.full((T, 20), np.nan),
           "hh": np.full((T, 20), np.nan), "gate": np.full((T, 20), np.nan)}
    dmax = 0.0
    for i in range(T):
        if rep["infer"][i]:
            out["h_prev"][i] = h[0]
            y_raw, h, bb, g, hh, gate = step_vec(m, rep["x"][i][None, :], h)
            v = clip_v([float(y_raw[0, 0]), float(y_raw[0, 1]), float(y_raw[0, 2])], V_MAX)
            out["y_raw"][i] = y_raw[0]
            out["y_clip"][i] = v
            out["bb"][i], out["g"][i], out["hh"][i], out["gate"][i] = bb[0], g[0], hh[0], gate[0]
            dmax = max(dmax, max(abs(v[k] - rep["y"][i][k]) for k in range(3)))
        else:
            dmax = max(dmax, float(np.abs(rep["y"][i]).max()))   # replay: hold ⇒ y=0
    return out, dmax


def rel_raw(m, x_norm):
    """Odnormalizowane rel_n, rel_e z cech znormalizowanych (std>0)."""
    rel_n = x_norm[..., 0] * m.input_std[0] + m.input_mean[0]
    rel_e = x_norm[..., 1] * m.input_std[1] + m.input_mean[1]
    return rel_n, rel_e


def v_rad_tan(y_raw, rel_n, rel_e):
    """PRE §1: r̂=(rel_n,rel_e)/d, t̂=(−r̂_e, r̂_n); v_rad=v_h·r̂ (>0 = zbliża się)."""
    d = np.hypot(rel_n, rel_e)
    v_rad = (y_raw[..., 0] * rel_n + y_raw[..., 1] * rel_e) / d
    v_tan = (-y_raw[..., 0] * rel_e + y_raw[..., 1] * rel_n) / d
    return d, v_rad, v_tan


# -------------------------------------------------- przedziałówka 1 kroku → y₀,y₁
def ia_step_y(m, xlo, xhi, hlo, hhi):
    """Przedziały (y₀, y₁) głowy PRZED clip_v na pudełku x×h (ia_* z xai_proofs)."""
    clo, chi = np.concatenate([xlo, hlo]), np.concatenate([xhi, hhi])
    zbl, zbh = ia_affine(clo, chi, m.Wb, m.bb0)
    bbl, bbh = np.tanh(zbl), np.tanh(zbh)
    zgl, zgh = ia_affine(bbl, bbh, m.Wg, m.bg)
    gl, gh = np.tanh(zgl), np.tanh(zgh)
    zhl, zhh = ia_affine(bbl, bbh, m.Wh, m.bh)
    hhl, hhh = np.tanh(zhl), np.tanh(zhh)
    ztl, zth = ia_affine(bbl, bbh, m.Wt, m.bt)
    gal = 1.0 / (1.0 + np.exp(-ztl))
    gah = 1.0 / (1.0 + np.exp(-zth))
    p1l, p1h = ia_mul(gal, gah, gl, gh)                      # γ·g
    p2l, p2h = ia_mul(1 - gah, 1 - gal, hhl, hhh)            # (1−γ)·hh
    h2l, h2h = p1l + p2l, p1h + p2h
    zol, zoh = ia_affine(h2l, h2h, m.Wo, m.bo)
    return (np.tanh(zol[:2]) * m.vmax, np.tanh(zoh[:2]) * m.vmax)


def ia_vrad_sign(m, xlo, xhi, hlo, hhi):
    """Przedział LICZNIKA v_rad·d = y₀·rel_n + y₁·rel_e (znak v_rad = znak licznika,
    bo d>0). rel z przedziału x₀,x₁ (denormalizacja monotoniczna, std>0).
    Zwraca (lo, hi, d_lo) — d_lo>0 wymagane do interpretacji."""
    ylo, yhi = ia_step_y(m, xlo, xhi, hlo, hhi)
    rnl = xlo[0] * m.input_std[0] + m.input_mean[0]
    rnh = xhi[0] * m.input_std[0] + m.input_mean[0]
    rel_ = xlo[1] * m.input_std[1] + m.input_mean[1]
    reh_ = xhi[1] * m.input_std[1] + m.input_mean[1]
    t1l, t1h = ia_mul(np.array([ylo[0]]), np.array([yhi[0]]),
                      np.array([rnl]), np.array([rnh]))
    t2l, t2h = ia_mul(np.array([ylo[1]]), np.array([yhi[1]]),
                      np.array([rel_]), np.array([reh_]))
    dn = 0.0 if rnl <= 0 <= rnh else min(abs(rnl), abs(rnh))
    de = 0.0 if rel_ <= 0 <= reh_ else min(abs(rel_), abs(reh_))
    return float(t1l[0] + t2l[0]), float(t1h[0] + t2h[0]), math.hypot(dn, de)


# ------------------------------------------------------------- mutanty XAI2
def make_m6(m=None):
    """M6_odwrócenie: Wo, bo → −Wo, −bo (PRE §2 czułość). Dynamika h BEZ zmian."""
    m = m or fresh_model()
    m.Wo = -m.Wo
    m.bo = -m.bo
    m._mut = "M6: Wo,bo → −Wo,−bo"
    return m


def make_m7(k):
    """M7_rekurencja: wiersze STANU w Wb (concat = [x(8), h(20)] ⇒ wiersze 8:28) × k."""
    m = fresh_model()
    m.Wb[m.IN:, :] *= k
    m._mut = f"M7: Wb[8:28,:] × {k}"
    return m


def sid_orbit_dir(sid):
    """orbit_dir scenariusza z litery bench/scenarios.py:70 (rng = Random(seed*100+ci),
    losowanie PO segmentach) — regeneracja deterministyczna gen_episode."""
    mm = re.match(r"c(\d+)_s(\d+)$", sid)
    if not mm:
        return None
    from bench.scenarios import CELLS, gen_episode
    ci, seed = int(mm.group(1)), int(mm.group(2))
    return gen_episode(CELLS[ci], seed)["orbit_dir"]


def jd(obj, path):
    json.dump(obj, open(path, "w"), indent=1, ensure_ascii=False)
    print("[zapis]", os.path.relpath(path, ROOT))
