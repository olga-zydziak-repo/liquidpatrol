#!/usr/bin/env python3
"""results/WK_RECON/tools/wk_r3_rate.py — R3 wrażliwość MTI/derotacji: tempo obrotu kadłuba (0 bootów).

Derotacja MTI kompensuje rotacyjny ego-motion homografią H = K·R(Δq)·K⁻¹ z attitude (r02/mti.py:3,57-66);
rezyduum rośnie z |Δq| między klatkami. Proxy: kąt obrotu między kolejnymi klatkami kamery (15 Hz,
mono_cam/model.sdf:64) = |ω|·(1/15 s), |ω| z kolejnych próbek ulog vehicle_attitude w oknie aktywnym
epizodów (cmd_v_ned ≠ 0, demo.jsonl; most czasu t_sim·1e6 jak wk_r3_view.py).

Użycie: wk_r3_rate.py <out.json> <katalog_boota>...
"""
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wk_r2_creep import classify  # noqa: E402
from wk_r3_view import load_ulog  # noqa: E402

FRAME_DT = 1.0 / 15.0


def main():
    out, dirs = sys.argv[1], sys.argv[2:]
    res = []
    for d in dirs:
        if not all(os.path.exists(os.path.join(d, f)) for f in ("manifest.json", "demo.jsonl", "boot.ulg")):
            continue
        cls = classify(json.load(open(os.path.join(d, "manifest.json"))), d)
        wins = []
        cur = None
        for ln in open(os.path.join(d, "demo.jsonl")):
            r = json.loads(ln)
            act = any(abs(c) > 0 for c in r["cmd_v_ned"])
            if act and cur is None:
                cur = [r["t_sim"], r["t_sim"]]
            elif act:
                cur[1] = r["t_sim"]
            elif cur is not None:
                wins.append(cur); cur = None
        if cur is not None:
            wins.append(cur)
        att, _ = load_ulog(os.path.join(d, "boot.ulg"))
        ts, q = att
        rates = []
        for lo, hi in wins:
            m = (ts >= lo * 1e6) & (ts <= hi * 1e6)
            tt, qq = ts[m], q[m]
            if len(tt) < 3:
                continue
            # kąt obrotu q_rel = conj(q_prev)·q_cur przez atan2(|wektor|, |w|) — stabilne numerycznie
            # (arccos iloczynu skalarnego kwantyzuje się przy float32 z ulogu)
            a_, b_ = qq[:-1], qq[1:]
            w = np.abs(np.sum(a_ * b_, axis=1))
            v1 = a_[:, 0:1] * b_[:, 1:] - b_[:, 0:1] * a_[:, 1:] - np.cross(a_[:, 1:], b_[:, 1:])
            ang = 2 * np.arctan2(np.linalg.norm(v1, axis=1), w)  # kąt obrotu między próbkami [rad]
            dt = np.diff(tt) / 1e6
            ok = dt > 0
            rates.extend(list(np.degrees(ang[ok] / dt[ok])))
        if not rates:
            continue
        r_ = np.sort(np.array(rates))
        row = {"boot": os.path.relpath(d), **cls, "n": len(r_),
               "omega_deg_s_p50": round(float(np.median(r_)), 2),
               "omega_deg_s_p95": round(float(r_[int(0.95 * (len(r_) - 1))]), 2),
               "omega_deg_s_p99": round(float(r_[int(0.99 * (len(r_) - 1))]), 2),
               "kat_na_klatke_deg_p95": round(float(r_[int(0.95 * (len(r_) - 1))]) * FRAME_DT, 3)}
        res.append(row)
        print(row["boot"], row["world"], row["controller"], row["omega_deg_s_p50"], row["omega_deg_s_p95"], row["omega_deg_s_p99"])
    json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
