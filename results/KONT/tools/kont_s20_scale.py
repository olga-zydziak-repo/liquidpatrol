#!/usr/bin/env python3
"""results/KONT/tools/kont_s20_scale.py — diagnoza skali przepływu (PROMPT_KONT_S2 §S2.0, ANEKS_KONT-1 R-3), 0 bootów, ulog bootB.
Wszystko z ulogu, jedna baza czasu: estimator_optical_flow_vel (prędkość z samego przepływu) vs vehicle_local_position_groundtruth,
ramka ciała przez vehicle_attitude_groundtruth. Regresja v_flow = s·v_GT + b po składowych, nominał / po odcięciu, próg opóźnienia.
Wyjście: results/KONT/s2/s20_scale.json"""
import json
import os

import numpy as np
from pyulog import ULog

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
B = os.path.join(ROOT, "results/KONT/s1/bootB/boot.ulg")
W = json.load(open(os.path.join(ROOT, "results/KONT/s1/s1_wyniki.json")))
T_CUT, T_DESC = W["t_cut_sim"], W["t_descent_sim"]
T_OFFB = 102.508
TOPICS = ["estimator_optical_flow_vel", "vehicle_local_position_groundtruth", "vehicle_attitude_groundtruth", "vehicle_local_position",
          "distance_sensor", "vehicle_optical_flow", "vehicle_attitude", "vehicle_angular_velocity"]


def fit(x, y):
    A = np.c_[x, np.ones_like(x)]
    (s, b), *_ = np.linalg.lstsq(A, y, rcond=None)
    r = y - (s * x + b)
    return {"s": round(float(s), 4), "b": round(float(b), 4), "rms": round(float(r.std()), 4), "n": int(x.size), "r2": round(1 - float(r.var() / y.var()), 4)}


def quat_rot(q, v):
    w, x, y, z = q.T
    R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)], [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                  [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]]).transpose(2, 0, 1)
    return np.einsum("nij,nj->ni", R, v), R


def yaw(q):
    w, x, y, z = q.T
    return np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))


def main():
    u = ULog(B, TOPICS)
    d = {x.name: x.data for x in u.data_list if x.multi_id == 0}
    fv, gl, ga, lp = d["estimator_optical_flow_vel"], d["vehicle_local_position_groundtruth"], d["vehicle_attitude_groundtruth"], d["vehicle_local_position"]
    t = fv["timestamp_sample"] / 1e6
    gt_t, ga_t = gl["timestamp"] / 1e6, ga["timestamp"] / 1e6
    q = np.c_[[np.interp(t, ga_t, ga[f"q[{i}]"]) for i in range(4)]].T
    q /= np.linalg.norm(q, axis=1, keepdims=True)
    vfn, vfe = fv["vel_ne[0]"], fv["vel_ne[1]"]
    vfb = np.c_[fv["vel_body[0]"], fv["vel_body[1]"]]
    res = {"t_cut": T_CUT, "t_desc": T_DESC, "opoznienie": {}}
    # opóźnienie przepływ–GT: maksimum korelacji na oknie
    win = (t >= T_OFFB) & (t <= T_DESC)
    best = None
    for lag in np.arange(-0.2, 0.3001, 0.01):
        g = np.interp(t[win] - lag, gt_t, gl["vx"])
        c = float(np.corrcoef(g, vfn[win])[0, 1])
        res["opoznienie"][f"{lag:.2f}"] = round(c, 4)
        if best is None or c > best[1]:
            best = (float(lag), c)
    lag = best[0]
    res["lag_s"] = round(lag, 3)
    vgn = np.interp(t - lag, gt_t, gl["vx"]); vge = np.interp(t - lag, gt_t, gl["vy"]); vgd = np.interp(t - lag, gt_t, gl["vz"])
    Rq = quat_rot(q, np.zeros((t.size, 3)))[1]
    vgb = np.einsum("nji,nj->ni", Rq, np.c_[vgn, vge, vgd])    # NED → ciało
    segs = {"nominal_offboard": (t >= T_OFFB) & (t < T_CUT), "po_odcieciu": (t >= T_CUT) & (t <= T_DESC)}
    res["regresje"] = {}
    for nm, m in segs.items():
        res["regresje"][nm] = {"ned_n": fit(vgn[m], vfn[m]), "ned_e": fit(vge[m], vfe[m]), "body_x": fit(vgb[m, 0], vfb[m, 0]), "body_y": fit(vgb[m, 1], vfb[m, 1]),
                               "predkosc_p50_flow": round(float(np.median(np.hypot(vfn[m], vfe[m]))), 3), "predkosc_p50_gt": round(float(np.median(np.hypot(vgn[m], vge[m]))), 3)}
    # odcinki 10 s po odcięciu: stabilność s
    rows = []
    for a in np.arange(T_CUT, T_DESC - 9.99, 10.0):
        m = (t >= a) & (t < a + 10)
        rows.append({"od_s": round(float(a - T_CUT), 1), "n": fit(vgn[m], vfn[m])["s"], "e": fit(vge[m], vfe[m])["s"], "body_x": fit(vgb[m, 0], vfb[m, 0])["s"], "body_y": fit(vgb[m, 1], vfb[m, 1])["s"],
                     "bx": fit(vgb[m, 0], vfb[m, 0])["b"], "by": fit(vgb[m, 1], vfb[m, 1])["b"]})
    res["okna_10s_po_odcieciu"] = rows
    # estymata EKF vs GT: prędkość, droga, kurs
    lt = lp["timestamp"] / 1e6
    gvx, gvy = np.interp(lt, gt_t, gl["vx"]), np.interp(lt, gt_t, gl["vy"])
    gx, gy = np.interp(lt, gt_t, gl["x"]), np.interp(lt, gt_t, gl["y"])
    res["ekf_vs_gt"] = {}
    for nm, (a, b) in {"nominal_offboard": (T_OFFB, T_CUT), "po_odcieciu": (T_CUT, T_DESC)}.items():
        m = (lt >= a) & (lt <= b)
        dt = np.diff(lt[m])
        out = {"fit_vx": fit(gvx[m], lp["vx"][m]), "fit_vy": fit(gvy[m], lp["vy"][m]),
               "droga_ekf_pozycje": round(float(np.hypot(np.diff(lp["x"][m]), np.diff(lp["y"][m])).sum()), 1), "droga_gt_pozycje": round(float(np.hypot(np.diff(gx[m]), np.diff(gy[m])).sum()), 1),
               "droga_ekf_calka_v": round(float((np.hypot(lp["vx"][m], lp["vy"][m])[:-1] * dt).sum()), 1), "droga_gt_calka_v": round(float((np.hypot(gvx[m], gvy[m])[:-1] * dt).sum()), 1)}
        # droga z pozycji próbkowanych co 1 s (bez wkładu szumu)
        idx = np.searchsorted(lt[m], np.arange(a, b, 1.0))
        idx = idx[idx < m.sum()]
        out["droga_ekf_1hz"] = round(float(np.hypot(np.diff(lp["x"][m][idx]), np.diff(lp["y"][m][idx])).sum()), 1)
        out["droga_gt_1hz"] = round(float(np.hypot(np.diff(gx[m][idx]), np.diff(gy[m][idx])).sum()), 1)
        out["blad_v_srednia_ned"] = [round(float((lp["vx"][m] - gvx[m]).mean()), 3), round(float((lp["vy"][m] - gvy[m]).mean()), 3)]
        res["ekf_vs_gt"][nm] = out
    # zasięg: użyty do przeliczenia (|vel_body|/|flow_rate_compensated|) vs dalmierz, dist_bottom, GT
    fr = np.hypot(fv["flow_rate_compensated[0]"], fv["flow_rate_compensated[1]"])
    sp = np.hypot(vfb[:, 0], vfb[:, 1])
    ds, dst = d["distance_sensor"]["current_distance"], d["distance_sensor"]["timestamp"] / 1e6
    res["zasieg"] = {}
    for nm, m in segs.items():
        ok = m & (fr > 0.03)
        impl = sp[ok] / fr[ok]
        gz = -np.interp(t[ok], gt_t, gl["z"])
        m2 = (lt >= t[m][0]) & (lt <= t[m][-1])
        res["zasieg"][nm] = {"uzyty_p50": round(float(np.median(impl)), 3), "dalmierz_p50": round(float(np.median(np.interp(t[ok], dst, ds))), 3), "dist_bottom_p50": round(float(np.median(lp["dist_bottom"][m2])), 3),
                             "gt_z_lokalne_p50": round(float(np.median(gz)), 3), "z_ekf_p50": round(float(np.median(-lp["z"][m2])), 3), "n": int(ok.sum())}
    # kurs EKF vs GT
    va = d["vehicle_attitude"]
    yg = np.unwrap(yaw(np.c_[[ga[f"q[{i}]"] for i in range(4)]].T))
    ye = np.unwrap(yaw(np.c_[[va[f"q[{i}]"] for i in range(4)]].T))
    ye_i = np.interp(ga_t, va["timestamp"] / 1e6, ye)
    dy = np.degrees(np.arctan2(np.sin(ye_i - yg), np.cos(ye_i - yg)))
    res["blad_kursu_deg"] = {nm: {"p50": round(float(np.median(dy[(ga_t >= a) & (ga_t <= b)])), 2), "min": round(float(dy[(ga_t >= a) & (ga_t <= b)].min()), 2), "max": round(float(dy[(ga_t >= a) & (ga_t <= b)].max()), 2)}
                              for nm, (a, b) in {"nominal_offboard": (T_OFFB, T_CUT), "po_odcieciu": (T_CUT, T_DESC)}.items()}
    json.dump(res, open(os.path.join(ROOT, "results/KONT/s2/s20_scale.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "opoznienie"}, ensure_ascii=False, indent=0))


main()
