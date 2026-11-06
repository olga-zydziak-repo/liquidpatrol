#!/usr/bin/env python3
"""results/KONT/tools/kont_s20_rate.py — S2.0, źródło błędu przepływu na poziomie kątowym: residuum flow_rate_uncompensated względem przewidywania z GT.
Konwencja EKF (optical_flow_control.cpp:123-124): v_b_x = −comp[1]·R, v_b_y = comp[0]·R, comp = unc − gyro. Stąd przewidywanie z GT: unc0 = v_b_y/R + ω_x, unc1 = −v_b_x/R + ω_y.
R = wys. GT nad gruntem / cos(pochylenie) (albo dalmierz, jako wariant). Regresja residuum na ω_z, v_b_x, v_b_y, stała; oraz błąd żyroskopu EKF względem ω GT. Wyjście: results/KONT/s2/s20_rate.json"""
import json
import os

import numpy as np
from pyulog import ULog

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
B = os.path.join(ROOT, "results/KONT/s1/bootB/boot.ulg")
W = json.load(open(os.path.join(ROOT, "results/KONT/s1/s1_wyniki.json")))
T_CUT, T_DESC = W["t_cut_sim"], W["t_descent_sim"]
T_NOM0 = 107.5


def main():
    u = ULog(B, ["estimator_optical_flow_vel", "vehicle_local_position_groundtruth", "vehicle_attitude_groundtruth", "vehicle_angular_velocity_groundtruth", "distance_sensor"])
    d = {x.name: x.data for x in u.data_list if x.multi_id == 0}
    fv, gl, ga, gw, ds = d["estimator_optical_flow_vel"], d["vehicle_local_position_groundtruth"], d["vehicle_attitude_groundtruth"], d["vehicle_angular_velocity_groundtruth"], d["distance_sensor"]
    t = fv["timestamp_sample"] / 1e6
    ip = lambda x, tt: np.interp(t, x["timestamp"] / 1e6, tt)
    q = np.c_[ip(ga, ga["q[0]"]), ip(ga, ga["q[1]"]), ip(ga, ga["q[2]"]), ip(ga, ga["q[3]"])]
    q /= np.linalg.norm(q, axis=1, keepdims=True)
    w, x, y, z = q.T
    R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)], [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                  [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]]).transpose(2, 0, 1)
    vned = np.c_[ip(gl, gl["vx"]), ip(gl, gl["vy"]), ip(gl, gl["vz"])]
    vb = np.einsum("nji,nj->ni", R, vned)
    wb = np.c_[ip(gw, gw["xyz[0]"]), ip(gw, gw["xyz[1]"]), ip(gw, gw["xyz[2]"])]
    hgt = -ip(gl, gl["z"]) / R[:, 2, 2]
    hrng = np.interp(t, ds["timestamp"] / 1e6, ds["current_distance"])
    unc = np.c_[fv["flow_rate_uncompensated[0]"], fv["flow_rate_uncompensated[1]"]]
    gyr = np.c_[fv["gyro_rate[0]"], fv["gyro_rate[1]"], fv["gyro_rate[2]"]]
    res = {"odniesienia": {}, "segmenty": {}}
    for nm, m in {"nominal": (t >= T_NOM0) & (t < T_CUT), "po_odcieciu": (t >= T_CUT) & (t <= T_DESC)}.items():
        out = {}
        for lab, rng in (("R_gt", hgt), ("R_dalmierz", hrng)):
            pred = np.c_[vb[:, 1] / rng + wb[:, 0], -vb[:, 0] / rng + wb[:, 1]]
            e = unc - pred
            X = np.column_stack([np.ones(m.sum()), wb[m, 2], vb[m, 0] / rng[m], vb[m, 1] / rng[m]])
            row = {"srednia_res_rad_s": [round(float(v), 5) for v in e[m].mean(0)], "sd_res_rad_s": [round(float(v), 4) for v in e[m].std(0)]}
            for i, axis in enumerate(("unc0→v_by", "unc1→v_bx")):
                b, *_ = np.linalg.lstsq(X, e[m, i], rcond=None)
                row[axis] = {"stala": round(float(b[0]), 5), "na_omega_z": round(float(b[1]), 4), "na_vbx/R": round(float(b[2]), 4), "na_vby/R": round(float(b[3]), 4),
                             "stala_w_m_s_przy_R": round(float(b[0] * np.median(rng[m])), 3), "omega_z_sr": round(float(wb[m, 2].mean()), 4), "udzial_omega_m_s": round(float(b[1] * wb[m, 2].mean() * np.median(rng[m])), 3)}
            out[lab] = row
        out["blad_zyro_ekf_minus_gt_rad_s"] = [round(float(v), 5) for v in (gyr[m] - wb[m]).mean(0)]
        out["gyro_bias_przeplywu"] = [round(float(fv[f"gyro_bias[{i}]"][m].mean()), 5) for i in range(3)]
        out["omega_gt_sr"] = [round(float(v), 4) for v in wb[m].mean(0)]
        out["v_b_sr"] = [round(float(v), 3) for v in vb[m].mean(0)]
        res["segmenty"][nm] = out
    # podział po znaku/rozmiarze omega_z w całym locie offboard (z GNSS i bez)
    m = (t >= T_NOM0) & (t <= T_DESC)
    wz = wb[:, 2]
    e_x = -(unc[:, 1] - gyr[:, 1]) * hrng - vb[:, 0]
    bins = [(-1, -0.3), (-0.3, -0.1), (-0.1, -0.02), (-0.02, 0.02), (0.02, 0.1), (0.1, 0.3), (0.3, 1)]
    res["blad_vbx_wg_omega_z"] = [{"przedzial": b, "n": int((m & (wz >= b[0]) & (wz < b[1])).sum()), "sr_m_s": round(float(e_x[m & (wz >= b[0]) & (wz < b[1])].mean()), 3) if (m & (wz >= b[0]) & (wz < b[1])).sum() > 50 else None} for b in bins]
    json.dump(res, open(os.path.join(ROOT, "results/KONT/s2/s20_rate.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=0).replace("\n", " "))


main()
