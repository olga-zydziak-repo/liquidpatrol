#!/usr/bin/env python3
"""results/2A/tools/coverage_real.py — bramki A(i) i A(iii) OFFLINE (PROMPT_2A_S2 §1, PRE_2A §3).

A(i) pokrycie kadru RZECZYWISTE: GT drona z trace.jsonl (wiersze t=gt: poza gz-ENU + kwaternion
POZY GZ — edycja D5, FREEZE_2A „Konwencje ramek") + GT intruza z gt_intruder.jsonl (NED APPLIED)
→ projekcja pinhole stałymi FREEZE_2A (f_px=270, 640×480, offset kamery FRD (0.12,−0.03,−0.242))
→ frakcja ticków GT z celem w kadrze, per faza approach/orbit (fazy z demo.jsonl po t_sim),
w oknach epizodów (eventy episode_start/episode_end z trace). Próg: ≥0.90 w orbicie i ≥0.90
w approach, per boot. GT żyje wyłącznie offline (reguła nadrzędna) — to narzędzie sędziowskie.

A(iii) quat w trace obecny i sensowny: norma ~1, ciągłość (max krok kątowy między kolejnymi
wierszami gt), oraz ZGODNOŚĆ NIEZALEŻNA: R_ned←frd zrekonstruowane z kwaternionu GZ
(ENU→NED przez common/frames; body_gz→FRD = diag(1,−1,−1)) vs attitude PX4 (own_q FRD→NED
z shadow_feed.jsonl, konwencja r02/mti.py) — kąt rozbieżności p50/p95 [deg].

Konwersje ramek wyłącznie przez common/frames (enu2ned) — zero lokalnych swapów (lekcja Z2).
"""
from __future__ import annotations

import argparse
import bisect
import json
import math
import os
import sys

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from common.frames import enu2ned                      # [E,N,U]→[N,E,D] (kanon programu)
from r02.mti import quat_to_R, FX, CX, CY, IMG_W, IMG_H   # intrinsics kanon (PRE_MTI R1)

CAM_OFF_FRD = (0.12, -0.03, -0.242)                     # FREEZE_2A (x500_mono_cam/model.sdf)
# ENU→NED jako macierz = enu2ned na wektorach bazowych (spójność z kanonem, nie ręczny swap)
M_NED_ENU = np.array([enu2ned([1, 0, 0]), enu2ned([0, 1, 0]), enu2ned([0, 0, 1])]).T
# body_gz (x przód, y lewo, z góra) → FRD (x przód, y prawo, z dół)
M_BODYGZ_FRD = np.diag([1.0, -1.0, -1.0])


def quat_to_R_enu(q):
    """Kwaternion POZY GZ [w,x,y,z] (body_gz→świat gz-ENU, Hamilton) → macierz 3×3.
    Ta sama algebra co r02/mti.quat_to_R (reuse), inna interpretacja ramek (gz, nie FRD/NED)."""
    return quat_to_R(q)


def R_ned_frd_from_gz(q_gz):
    """R_ned←frd = M(ned←enu) · R(enu←body_gz) · M(body_gz←frd)."""
    return M_NED_ENU @ quat_to_R_enu(q_gz) @ M_BODYGZ_FRD


def load_jsonl(path):
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


def interp(ts, ps, t):
    if not ts or t < ts[0] or t > ts[-1]:
        return None
    i = bisect.bisect_right(ts, t)
    if i >= len(ts):
        return ps[-1]
    t0, t1 = ts[i - 1], ts[i]
    a = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
    return [ps[i - 1][k] + a * (ps[i][k] - ps[i - 1][k]) for k in range(3)]


def in_frame(own_ned, q_gz, tgt_ned):
    """Projekcja środka celu do kadru. Zwraca (bool, u, v, Z_opt)."""
    R = R_ned_frd_from_gz(q_gz)
    rel_frd = R.T @ (np.asarray(tgt_ned) - np.asarray(own_ned))
    cam = rel_frd - np.asarray(CAM_OFF_FRD)
    x_opt, y_opt, z_opt = cam[1], cam[2], cam[0]       # ramka optyczna per r02/mti.py
    if z_opt <= 0.1:
        return False, None, None, float(z_opt)
    u = CX + x_opt / z_opt * FX
    v = CY + y_opt / z_opt * FX
    return (0.0 <= u <= IMG_W and 0.0 <= v <= IMG_H), round(float(u), 1), round(float(v), 1), float(z_opt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bootdir")
    ap.add_argument("--out")
    a = ap.parse_args()

    trace = load_jsonl(os.path.join(a.bootdir, "trace.jsonl"))
    gt_rows = [r for r in trace if r.get("t") == "gt"]
    events = [r for r in trace if r.get("t") == "event"]
    demo = load_jsonl(os.path.join(a.bootdir, "demo.jsonl"))
    gtin = load_jsonl(os.path.join(a.bootdir, "gt_intruder.jsonl"))

    # okna epizodów
    wins = []
    t0 = eid = None
    for e in events:
        if e["ev"] == "episode_start":
            t0, eid = e["sim"], e["episode_id"]
        elif e["ev"] == "episode_end" and t0 is not None:
            wins.append((t0, e["sim"], eid)); t0 = None
    # GT intruza per epizod
    gi = {}
    for r in gtin:
        e = gi.setdefault(r["episode_id"], ([], []))
        e[0].append(r["t_sim"]); e[1].append(r["ned"])
    # fazy z demo (t_sim rosnące)
    dts = [r["t_sim"] for r in demo]
    dph = [r["phase"] for r in demo]

    def phase_at(t):
        i = bisect.bisect_right(dts, t)
        if i == 0:
            return None
        return dph[i - 1] if t - dts[i - 1] <= 0.2 else None

    # --- A(iii): quat obecny/norma/ciągłość ---
    n_gt = len(gt_rows)
    n_q = sum(1 for r in gt_rows if "qw" in r)
    norms, steps = [], []
    prevq = None
    for r in gt_rows:
        if "qw" not in r:
            continue
        q = np.array([r["qw"], r["qx"], r["qy"], r["qz"]])
        norms.append(float(np.linalg.norm(q)))
        if prevq is not None:
            d = abs(float(np.dot(q, prevq)))
            steps.append(math.degrees(2 * math.acos(min(1.0, d))))
        prevq = q
    # zgodność z attitude PX4 (shadow own_q), jeśli shadow-log jest
    vs_px4 = None
    sf = os.path.join(a.bootdir, "shadow_feed.jsonl")
    if os.path.exists(sf) and gt_rows:
        gts = [r["sim"] for r in gt_rows]
        angs = []
        for r in load_jsonl(sf):
            if r.get("own_q") is None or r.get("t_frame") is None:
                continue
            i = bisect.bisect_left(gts, r["t_frame"])
            cand = [j for j in (i - 1, i) if 0 <= j < len(gt_rows)]
            if not cand:
                continue
            j = min(cand, key=lambda k: abs(gts[k] - r["t_frame"]))
            if abs(gts[j] - r["t_frame"]) > 0.05 or "qw" not in gt_rows[j]:
                continue
            g = gt_rows[j]
            R_gz = R_ned_frd_from_gz([g["qw"], g["qx"], g["qy"], g["qz"]])
            R_px4 = quat_to_R(r["own_q"])
            c = (np.trace(R_gz.T @ R_px4) - 1.0) / 2.0
            angs.append(math.degrees(math.acos(max(-1.0, min(1.0, c)))))
        if angs:
            s = sorted(angs)
            vs_px4 = {"n": len(s), "p50_deg": round(s[len(s) // 2], 3),
                      "p95_deg": round(s[int(len(s) * 0.95)], 3), "max_deg": round(s[-1], 3)}

    # --- A(i): pokrycie per faza, w oknach epizodów ---
    cov = {}
    per_ep = {}
    for r in gt_rows:
        if "qw" not in r:
            continue
        t = r["sim"]
        win = next(((w0, w1, we) for (w0, w1, we) in wins if w0 <= t <= w1), None)
        if win is None:
            continue
        ph = phase_at(t)
        if ph not in ("approach", "orbit"):
            continue
        g = gi.get(win[2])
        tgt = interp(g[0], g[1], t) if g else None
        if tgt is None:
            continue
        own_ned = enu2ned([r["x"], r["y"], r["z"]])
        ok, u, v, z = in_frame(own_ned, [r["qw"], r["qx"], r["qy"], r["qz"]], tgt)
        c = cov.setdefault(ph, [0, 0]); c[0] += 1; c[1] += int(ok)
        ce = per_ep.setdefault((win[2], ph), [0, 0]); ce[0] += 1; ce[1] += int(ok)

    out = {
        "bootdir": a.bootdir,
        "episodes": [{"episode_id": e, "t0": round(w0, 2), "t1": round(w1, 2)} for (w0, w1, e) in wins],
        "coverage": {ph: {"n_ticks": n, "in_frame": k, "frac": round(k / n, 4)}
                     for ph, (n, k) in sorted(cov.items())},
        "coverage_per_episode": {f"ep{e}_{ph}": {"n": n, "in": k, "frac": round(k / n, 4)}
                                 for (e, ph), (n, k) in sorted(per_ep.items())},
        "gate_A_i": {ph: (cov.get(ph, [0, 0])[1] / cov[ph][0] >= 0.90 if ph in cov and cov[ph][0] else None)
                     for ph in ("approach", "orbit")},
        "quat": {"n_gt_rows": n_gt, "n_with_quat": n_q,
                 "norm_min": round(min(norms), 6) if norms else None,
                 "norm_max": round(max(norms), 6) if norms else None,
                 "max_step_deg": round(max(steps), 3) if steps else None,
                 "vs_px4_attitude": vs_px4},
    }
    print(json.dumps(out, indent=1))
    if a.out:
        with open(a.out, "w") as f:
            json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
