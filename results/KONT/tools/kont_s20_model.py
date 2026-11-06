#!/usr/bin/env python3
"""results/KONT/tools/kont_s20_model.py — model błędu po odcięciu (S2.0, ANEKS_KONT-1 R-3): e(t) = p_EKF−p_GT−e(cięcie), wektorowo w NED.
Regresje: (A) e = (s−1)·d, d = p_GT(t)−p_GT(cięcie) [jednorodna skala]; (B) e = c·τ [stały bias prędkości w NED]; (C) A+B; (D) C + obrót θ·J·d.
Plus błąd prędkości EKF−GT i przepływu w ciele, przedziałami. Składowe surowego przepływu liczone średnimi (orbita ma v_body_y≈stałe, więc regresja
s,b po składowej ciała jest osobliwa; odczytywać stosunek średnich). Wyjście: results/KONT/s2/s20_model.json"""
import json
import os

import numpy as np
from pyulog import ULog

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
B = os.path.join(ROOT, "results/KONT/s1/bootB/boot.ulg")
W = json.load(open(os.path.join(ROOT, "results/KONT/s1/s1_wyniki.json")))
T_CUT, T_DESC = W["t_cut_sim"], W["t_descent_sim"]
T_NOM0 = 102.508
J = np.array([[0.0, -1.0], [1.0, 0.0]])


def lsq(names, cols, y):
    X = np.column_stack(cols)
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    r = y - X @ b
    return {"wsp": {n: round(float(v), 4) for n, v in zip(names, b)}, "rms_m": round(float(np.sqrt((r ** 2).mean() * 2)), 3)}


def main():
    u = ULog(B, ["vehicle_local_position", "vehicle_local_position_groundtruth", "vehicle_attitude_groundtruth", "estimator_optical_flow_vel", "estimator_status_flags"])
    d = {x.name: x.data for x in u.data_list if x.multi_id == 0}
    lp, gl, ga, fv = d["vehicle_local_position"], d["vehicle_local_position_groundtruth"], d["vehicle_attitude_groundtruth"], d["estimator_optical_flow_vel"]
    gt_t = gl["timestamp"] / 1e6
    tg = np.arange(T_NOM0, T_DESC, 0.1)
    lt = lp["timestamp"] / 1e6
    P = np.c_[np.interp(tg, lt, lp["x"]), np.interp(tg, lt, lp["y"])]
    G = np.c_[np.interp(tg, gt_t, gl["x"]), np.interp(tg, gt_t, gl["y"])]
    V = np.c_[np.interp(tg, lt, lp["vx"]), np.interp(tg, lt, lp["vy"])]
    Vg = np.c_[np.interp(tg, gt_t, gl["vx"]), np.interp(tg, gt_t, gl["vy"])]
    m = tg >= T_CUT
    i0 = int(np.argmax(m))
    e = (P - G) - (P[i0] - G[i0])
    res = {"eps_koniec_okna_m": round(float(np.hypot(*e[-1])), 3)}
    dd = G[m] - G[i0]; tau = tg[m] - T_CUT; em = e[m]
    y = em.ravel()
    dv = dd.ravel()
    tx = np.c_[tau, np.zeros_like(tau)].ravel(); ty = np.c_[np.zeros_like(tau), tau].ravel()
    Jd = (dd @ J.T).ravel()
    res["modele"] = {"0_brak": {"rms_m": round(float(np.sqrt((y ** 2).mean() * 2)), 3)},
                     "A_skala": lsq(["s-1"], [dv], y), "B_bias_v": lsq(["cn", "ce"], [tx, ty], y), "C_skala_bias": lsq(["s-1", "cn", "ce"], [dv, tx, ty], y),
                     "D_skala_bias_obrot": lsq(["s-1", "cn", "ce", "theta"], [dv, tx, ty, Jd], y)}
    # błąd prędkości w przedziałach 10 s: NED i ciało, EKF−GT
    q = np.c_[[np.interp(tg, ga["timestamp"] / 1e6, ga[f"q[{i}]"]) for i in range(4)]].T
    q /= np.linalg.norm(q, axis=1, keepdims=True)
    yaw = np.arctan2(2 * (q[:, 0] * q[:, 3] + q[:, 1] * q[:, 2]), 1 - 2 * (q[:, 2] ** 2 + q[:, 3] ** 2))
    cy, sy = np.cos(yaw), np.sin(yaw)
    bf = lambda v: np.c_[cy * v[:, 0] + sy * v[:, 1], -sy * v[:, 0] + cy * v[:, 1]]    # NED → rama kursu (x nos, y prawo)
    Ev = V - Vg
    Evb, Vgb = bf(Ev), bf(Vg)
    ft = fv["timestamp_sample"] / 1e6
    Fb = np.c_[np.interp(tg, ft, fv["vel_body_filtered[0]"]), np.interp(tg, ft, fv["vel_body_filtered[1]"])]
    Fn = np.c_[np.interp(tg, ft, fv["vel_ne_filtered[0]"]), np.interp(tg, ft, fv["vel_ne_filtered[1]"])]
    rows = []
    for a in list(np.arange(T_NOM0 + 5, T_CUT - 4.99, 10.0)) + list(np.arange(T_CUT, T_DESC - 9.99, 10.0)):
        k = (tg >= a) & (tg < a + 10)
        rows.append({"od_ciecia": round(float(a - T_CUT), 1), "Ev_ned": [round(float(x), 3) for x in Ev[k].mean(0)], "Ev_cialo": [round(float(x), 3) for x in Evb[k].mean(0)],
                     "Vg_cialo": [round(float(x), 2) for x in Vgb[k].mean(0)], "V_gt": round(float(np.hypot(*Vg[k].T).mean()), 2), "V_ekf": round(float(np.hypot(*V[k].T).mean()), 2),
                     "F_ne_minus_gt": [round(float(x), 3) for x in (Fn[k] - Vg[k]).mean(0)], "F_cialo": [round(float(x), 2) for x in Fb[k].mean(0)], "yaw_deg": round(float(np.degrees(np.arctan2(sy[k].mean(), cy[k].mean()))), 0)})
    res["przedzialy_10s"] = rows
    for nm, k in {"nominal": (tg >= T_NOM0 + 5) & (tg < T_CUT), "po_odcieciu": m}.items():
        res[nm] = {"Ev_ned_srednia": [round(float(x), 4) for x in Ev[k].mean(0)], "Ev_cialo_srednia": [round(float(x), 4) for x in Evb[k].mean(0)], "F_ne_minus_gt": [round(float(x), 4) for x in (Fn[k] - Vg[k]).mean(0)],
                   "stosunek_sredniej_predkosci_ekf_gt": round(float(np.hypot(*V[k].T).mean() / np.hypot(*Vg[k].T).mean()), 4), "stosunek_flow_filtr_gt": round(float(np.hypot(*Fn[k].T).mean() / np.hypot(*Vg[k].T).mean()), 4),
                   "rzut_v_ekf_na_v_gt": round(float((V[k] * Vg[k]).sum() / (Vg[k] ** 2).sum()), 4), "rzut_flow_na_v_gt": round(float((Fn[k] * Vg[k]).sum() / (Vg[k] ** 2).sum()), 4)}
    json.dump(res, open(os.path.join(ROOT, "results/KONT/s2/s20_model.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(res["modele"], ensure_ascii=False)); print(res["eps_koniec_okna_m"]); print("nom", res["nominal"]); print("po", res["po_odcieciu"])
    for r in rows: print(r)


main()
