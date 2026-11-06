#!/usr/bin/env python3
"""results/KONT/tools/kont_s20_robust.py — S2.0, odpornie: residuum prędkości z przepływu (surowe, bez filtra) wobec GT w ramie ciała: mediana vs średnia, ogony, asymetria,
zależność od tempa kursu (z kwaternionu GT, nie z vehicle_angular_velocity_groundtruth) i prędkości; rozdział próbek odrzuconych/przyjętych przez EKF.
Wyjście: results/KONT/s2/s20_robust.json"""
import json
import os

import numpy as np
from pyulog import ULog

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
B = os.path.join(ROOT, "results/KONT/s1/bootB/boot.ulg")
W = json.load(open(os.path.join(ROOT, "results/KONT/s1/s1_wyniki.json")))
T_CUT, T_DESC = W["t_cut_sim"], W["t_descent_sim"]
T_NOM0 = 107.5


def stat(e):
    return {"n": int(e.size), "srednia": round(float(e.mean()), 3), "mediana": round(float(np.median(e)), 3), "p05": round(float(np.percentile(e, 5)), 3), "p95": round(float(np.percentile(e, 95)), 3),
            "frac_abs_gt_2ms": round(float((abs(e) > 2).mean()), 4), "srednia_abs_lt_2ms": round(float(e[abs(e) < 2].mean()), 3) if (abs(e) < 2).any() else None}


def main():
    u = ULog(B, ["estimator_optical_flow_vel", "vehicle_local_position_groundtruth", "vehicle_attitude_groundtruth", "estimator_aid_src_optical_flow"])
    d = {x.name: x.data for x in u.data_list if x.multi_id == 0}
    fv, gl, ga, a = d["estimator_optical_flow_vel"], d["vehicle_local_position_groundtruth"], d["vehicle_attitude_groundtruth"], d["estimator_aid_src_optical_flow"]
    t = fv["timestamp_sample"] / 1e6
    gq = np.c_[ga["q[0]"], ga["q[1]"], ga["q[2]"], ga["q[3]"]]
    yaw_g = np.unwrap(np.arctan2(2 * (gq[:, 0] * gq[:, 3] + gq[:, 1] * gq[:, 2]), 1 - 2 * (gq[:, 2] ** 2 + gq[:, 3] ** 2)))
    gt_a = ga["timestamp"] / 1e6
    yaw = np.interp(t, gt_a, yaw_g)
    tu = np.arange(t[0], t[-1], 0.5)
    rate = np.interp(t, tu[:-1] + 0.25, np.diff(np.interp(tu, gt_a, yaw_g)) / 0.5)
    cy, sy = np.cos(yaw), np.sin(yaw)
    vn, ve = np.interp(t, gl["timestamp"] / 1e6, gl["vx"]), np.interp(t, gl["timestamp"] / 1e6, gl["vy"])
    vbx, vby = cy * vn + sy * ve, -sy * vn + cy * ve            # rama kursu; tilt mały, opisowo
    ex, ey = fv["vel_body[0]"] - vbx, fv["vel_body[1]"] - vby
    fx, fy = fv["vel_body_filtered[0]"] - vbx, fv["vel_body_filtered[1]"] - vby
    fused = np.interp(t, a["timestamp_sample"] / 1e6, a["fused"].astype(float)) > 0.5
    res = {}
    for nm, m in {"nominal": (t >= T_NOM0) & (t < T_CUT), "po_odcieciu": (t >= T_CUT) & (t <= T_DESC)}.items():
        res[nm] = {"surowe_x": stat(ex[m]), "surowe_y": stat(ey[m]), "filtr_x": stat(fx[m]), "filtr_y": stat(fy[m]), "przyjete_x": stat(ex[m & fused]), "przyjete_y": stat(ey[m & fused]),
                   "odrzucone_x": stat(ex[m & ~fused]), "odrzucone_y": stat(ey[m & ~fused]), "tempo_kursu_sr_rad_s": round(float(rate[m].mean()), 3), "v_bx_sr": round(float(vbx[m].mean()), 3), "v_by_sr": round(float(vby[m].mean()), 3)}
    m = (t >= T_NOM0) & (t <= T_DESC)
    rows = []
    for lo, hi in [(-0.6, -0.15), (-0.15, -0.05), (-0.05, 0.05), (0.05, 0.15), (0.15, 0.3), (0.3, 0.8)]:
        k = m & (rate >= lo) & (rate < hi)
        if k.sum() > 100:
            rows.append({"tempo": [lo, hi], "n": int(k.sum()), "med_ex": round(float(np.median(ex[k])), 3), "med_ey": round(float(np.median(ey[k])), 3), "v_bx": round(float(vbx[k].mean()), 2), "v_by": round(float(vby[k].mean()), 2)})
    res["wg_tempa_kursu"] = rows
    k = m & (abs(ex) < 2)
    X = np.column_stack([np.ones(k.sum()), rate[k], vbx[k], vby[k]])
    res["regresja_ex_przyjete"] = {n: round(float(v), 4) for n, v in zip(["stala", "tempo", "v_bx", "v_by"], np.linalg.lstsq(X, ex[k], rcond=None)[0])}
    k = m & (abs(ey) < 2)
    X = np.column_stack([np.ones(k.sum()), rate[k], vbx[k], vby[k]])
    res["regresja_ey_przyjete"] = {n: round(float(v), 4) for n, v in zip(["stala", "tempo", "v_bx", "v_by"], np.linalg.lstsq(X, ey[k], rcond=None)[0])}
    json.dump(res, open(os.path.join(ROOT, "results/KONT/s2/s20_robust.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False).replace('}, "', '},\n"'))


main()
