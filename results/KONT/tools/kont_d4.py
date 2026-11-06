#!/usr/bin/env python3
"""results/KONT/tools/kont_d4.py — diagnoza D4 przy biurku (ANEKS_KONT-1e §3), 0 bootów, ulogi i trace 5 lotów z dysku. D4a: bias żyroskopu na starcie, przy odcięciu, przy zejściu; pierwsze próbki IMU. D4b: okno ±3 s od początku zejścia: resety pozycji, spójność pozycji z prędkością, przepływ, profil, wychylenie, prędkość styczna GT, zgodność trace z ulogiem. Czas ulogu = czas gz, jak w kont_s2_analyze.py.
Stan filtra nie jest mierzony: states[7..8] nie zmieniają się w oknie, więc w tej wersji PX4 nie są pozycją. Wyjście: results/KONT/s2/d4/d4.json. Bez werdyktu: werdykt stawia raport."""
import json
import math
import os

import numpy as np
from pyulog import ULog

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
S2 = os.path.join(ROOT, "results/KONT/s2")
LOTY = ["c08_s02a_r2", "c11_s02_r3", "c11_s03_r4", "c08_s04_r3", "c00_s02_r3"]
OKNO = 3.0


def wart(t, v, t0):
    return float(v[min(np.searchsorted(t, t0), len(v) - 1)])


def trans(t, v, a, b):
    m = (t >= a) & (t <= b)
    if not m.any():
        return []
    tt, vv = t[m], v[m]
    i = np.flatnonzero(np.r_[False, vv[1:] != vv[:-1]])
    return [(round(float(tt[j]), 3), int(vv[j])) for j in i]


def euler(q):
    w, x, y, z = q
    return math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y)), math.asin(max(-1, min(1, 2 * (w * y - z * x)))), math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))


def d4a(D, tc, td, t_air):
    b = D["estimator_sensor_bias"]
    t = b["timestamp"] / 1e6
    g = np.c_[b["gyro_bias[0]"], b["gyro_bias[1]"], b["gyro_bias[2]"]]
    a = np.abs(g).max(axis=1)
    sc = D["sensor_combined"]
    ts = sc["timestamp"] / 1e6
    w = np.c_[sc["gyro_rad[0]"], sc["gyro_rad[1]"], sc["gyro_rad[2]"]]
    m5 = ts < ts[0] + 5
    vi = D["vehicle_imu"]
    gt = D["vehicle_angular_velocity_groundtruth"]
    tg = gt["timestamp"] / 1e6
    wg = np.c_[gt["xyz[0]"], gt["xyz[1]"], gt["xyz[2]"]]
    at, q = D["vehicle_attitude"], D["vehicle_attitude_groundtruth"]
    tq, tqg = at["timestamp"] / 1e6, q["timestamp"] / 1e6

    def yaw_err(t0):
        i, j = min(np.searchsorted(tq, t0), len(tq) - 1), min(np.searchsorted(tqg, t0), len(tqg) - 1)
        y = euler([at[f"q[{k}]"][i] for k in range(4)])[2] - euler([q[f"q[{k}]"][j] for k in range(4)])[2]
        return round(math.degrees((y + math.pi) % (2 * math.pi) - math.pi), 2)

    return {"bias_pierwsza": {"t": round(float(t[0]), 2), "xyz": [round(float(x), 5) for x in g[0]]}, "bias_max_ziemia": round(float(a[t < t_air].max()), 5), "bias_ziemia_koniec": round(float(a[t < t_air][-1]), 5),
            "bias_start": round(wart(t, a, t_air), 5), "bias_ciecie": round(wart(t, a, tc), 5), "bias_ciecie_xyz": [round(wart(t, g[:, i], tc), 5) for i in range(3)], "bias_zejscie": round(wart(t, a, td), 5), "bias_max_powietrze": round(float(a[(t >= t_air) & (t <= td)].max()), 5),
            "sensor_combined_t0": round(float(ts[0]), 3), "gyro_abs_max_pierwsze_5s": round(float(np.abs(w[m5]).max()), 4), "gyro_srednia_5s_xyz": [round(float(x), 5) for x in w[m5].mean(axis=0)],
            "gyro_gt_abs_max_pierwsze_5s": round(float(np.abs(wg[tg < ts[0] + 5]).max()), 4), "pierwsze_gyro": [[round(float(x), 4) for x in r] for r in w[:3]], "vehicle_imu_sample_0": int((vi["timestamp_sample"] == 0).sum()), "sensor_combined_ts_0": int((sc["timestamp"] == 0).sum()),
            "yaw_blad_deg": {"t0+10": yaw_err(ts[0] + 10), "start": yaw_err(t_air), "ciecie": yaw_err(tc), "zejscie": yaw_err(td)}}


def d4b(D, w, ev):
    td, tc = w["t_descent"], w["t_cut"]
    a, b = td - OKNO, td + OKNO
    p, g = D["vehicle_local_position"], D["vehicle_local_position_groundtruth"]
    t, tg = p["timestamp"] / 1e6, g["timestamp"] / 1e6
    m = (t >= a) & (t <= b)
    # błąd wobec GT z offsetem z 20 s przed odcięciem, jak CC w 1b §1 (metoda opisowa, kanon ε = gt_judge)
    gx, gy = np.interp(t, tg, g["x"]), np.interp(t, tg, g["y"])
    mo = (t >= tc - 20) & (t < tc)
    ox, oy = float((p["x"][mo] - gx[mo]).mean()), float((p["y"][mo] - gy[mo]).mean())
    e = np.hypot(p["x"] - gx - ox, p["y"] - gy - oy)
    e_d = wart(t, e, td)
    mz = (t >= td) & (t <= td + 15)
    # spójność: przyrost pozycji minus całka prędkości własnej EKF
    tw, xw, yw, vxw, vyw = t[m], p["x"][m], p["y"][m], p["vx"][m], p["vy"][m]
    dt = np.diff(tw)
    rx = np.r_[0, np.cumsum(np.diff(xw) - 0.5 * (vxw[1:] + vxw[:-1]) * dt)]
    ry = np.r_[0, np.cumsum(np.diff(yw) - 0.5 * (vyw[1:] + vyw[:-1]) * dt)]
    rr = np.hypot(rx, ry)
    skok = np.hypot(np.diff(xw) - 0.5 * (vxw[1:] + vxw[:-1]) * dt, np.diff(yw) - 0.5 * (vyw[1:] + vyw[:-1]) * dt)
    i = int(skok.argmax())
    res = {k: trans(t, p[k], tc, td + 15) for k in ("xy_reset_counter", "vxy_reset_counter", "z_reset_counter", "heading_reset_counter", "dist_bottom_reset_counter") if k in p}
    st = D["estimator_status"]
    ts = st["timestamp"] / 1e6
    rs = {k: trans(ts, st[k], tc, td + 15) for k in ("reset_count_pos_ne", "reset_count_vel_ne", "reset_count_quat")}
    vg = np.hypot(np.gradient(g["x"], tg), np.gradient(g["y"], tg))
    vgn = np.hypot(g["vx"], g["vy"]) if "vx" in g else vg
    fl = D["estimator_aid_src_optical_flow"]
    tf = fl["timestamp"] / 1e6
    mf = (tf >= td - OKNO) & (tf <= td + OKNO)
    mf0 = (tf >= tc) & (tf < td - OKNO)
    q = D["vehicle_optical_flow"]
    tq = q["timestamp"] / 1e6
    mq = (tq >= a) & (tq <= b)
    f = D["estimator_status_flags"]
    tfl = f["timestamp"] / 1e6
    flagi = {k: trans(tfl, f[k], a, b) for k in ("cs_opt_flow", "cs_rng_hgt", "cs_baro_hgt", "cs_rng_terrain", "cs_terrain", "cs_opt_flow_terrain", "reject_optflow_x", "reject_optflow_y", "reject_hagl", "reject_hor_vel") if k in f}
    at = D["vehicle_attitude"]
    tat = at["timestamp"] / 1e6
    ma = (tat >= a) & (tat <= b)
    e_rp = np.array([euler([at[f"q[{k}]"][j] for k in range(4)])[:2] for j in np.flatnonzero(ma)[::10]])
    rps = D["vehicle_angular_velocity"]
    trps = rps["timestamp"] / 1e6
    mr = (trps >= a) & (trps <= b)
    sp = D["trajectory_setpoint"]
    tsp = sp["timestamp"] / 1e6
    # trace kontra ulog: pozycja EKF w oknie
    tr = [r for r in ev["_ekf"] if a <= r["sim"] <= b]
    tr_t = np.array([r["sim"] for r in tr])
    dtr = np.hypot(np.array([r["x"] for r in tr]) - np.interp(tr_t, t, p["x"]), np.array([r["y"] for r in tr]) - np.interp(tr_t, t, p["y"])) if tr else np.array([np.nan])
    profil = [{"t": round(float(tx - td), 1), "e": round(wart(t, e, tx), 2), "x": round(wart(t, p["x"], tx), 2), "y": round(wart(t, p["y"], tx), 2), "vx": round(wart(t, p["vx"], tx), 2), "vy": round(wart(t, p["vy"], tx), 2), "vz": round(wart(t, p["vz"], tx), 2), "v_gt": round(wart(tg, vgn, tx), 2), "z_gt": round(-wart(tg, g["z"], tx), 2), "dist_bottom": round(wart(t, p["dist_bottom"], tx), 2), "q": int(wart(tq, q["quality"], tx))} for tx in np.arange(td - OKNO, td + OKNO + 0.01, 0.5)]
    return {"delta_max_kanon": w["delta_max"], "eps_start_kanon": w["eps_start_zejscia"], "t_descent": td, "e_opis_start": round(e_d, 3), "e_opis_max_15s": round(float(e[mz].max()), 3), "t_e_max": round(float(t[mz][e[mz].argmax()] - td), 2),
            "v_styczna_gt_w_zejsciu": round(wart(tg, vgn, td), 3), "v_styczna_ekf_w_zejsciu": round(float(np.hypot(wart(t, p["vx"], td), wart(t, p["vy"], td))), 3),
            "rezyduum_poz_minus_calka_v_max": round(float(rr.max()), 3), "najwiekszy_skok_1_probka": {"m": round(float(skok[i]), 3), "t_od_zejscia": round(float(tw[i + 1] - td), 3)},
            "resety_lp": res, "resety_status": rs, "flow_okno": {"fused_frac": round(float(fl["fused"][mf].mean()), 3), "rejected_frac": round(float(fl["innovation_rejected"][mf].mean()), 3), "test_ratio_max": round(float(np.nanmax(np.c_[fl["test_ratio[0]"][mf], fl["test_ratio[1]"][mf]])), 2), "innow_max": round(float(np.nanmax(np.abs(np.c_[fl["innovation[0]"][mf], fl["innovation[1]"][mf]]))), 3), "n": int(mf.sum())},
            "flow_orbita": {"fused_frac": round(float(fl["fused"][mf0].mean()), 3), "rejected_frac": round(float(fl["innovation_rejected"][mf0].mean()), 3), "test_ratio_p95": round(float(np.nanpercentile(np.c_[fl["test_ratio[0]"][mf0], fl["test_ratio[1]"][mf0]], 95)), 2)},
            "jakosc_min_okno": int(q["quality"][mq].min()), "flagi": flagi, "roll_pitch_max_deg": round(float(np.degrees(np.abs(e_rp).max())), 1), "rate_max_rad_s": round(float(np.abs(np.c_[rps["xyz[0]"][mr], rps["xyz[1]"][mr], rps["xyz[2]"][mr]]).max()), 2), "vz_max": round(float(np.abs(p["vz"][m]).max()), 2),
            "trace_vs_ulog_xy_max_m": round(float(np.nanmax(dtr)), 3), "trace_n": len(tr), "setpoint_n": int(((tsp >= a) & (tsp <= b)).sum()), "profil": profil}


def d4c(D, w):
    """Skok jako wektor, kontrola na orbicie, stan filtra, kolejność zdarzeń. Zejście: [td, td+3]; kontrola: okna 3 s co 1 s na orbicie po odcięciu, do td-3."""
    td, tc = w["t_descent"], w["t_cut"]
    p, g = D["vehicle_local_position"], D["vehicle_local_position_groundtruth"]
    t, tg = p["timestamp"] / 1e6, g["timestamp"] / 1e6
    gx, gy = np.interp(t, tg, g["x"]), np.interp(t, tg, g["y"])
    ex, ey = p["x"] - gx, p["y"] - gy
    i_v = np.r_[0, np.cumsum(0.5 * (p["vx"][1:] + p["vx"][:-1]) * np.diff(t))], np.r_[0, np.cumsum(0.5 * (p["vy"][1:] + p["vy"][:-1]) * np.diff(t))]

    def okno(a, b):
        m = (t >= a) & (t <= b)
        ev = np.hypot(ex[m] - ex[m][0], ey[m] - ey[m][0])
        rv = np.hypot(p["x"][m] - p["x"][m][0] - (i_v[0][m] - i_v[0][m][0]), p["y"][m] - p["y"][m][0] - (i_v[1][m] - i_v[1][m][0]))
        return float(ev.max()), float(rv.max())

    kon = [okno(a, a + 3) for a in np.arange(tc + 1, td - 3, 1.0)]
    zw = okno(td, td + 3)
    z2 = okno(td, td + 15)
    fl = D["estimator_aid_src_optical_flow"]
    tf = fl["timestamp"] / 1e6
    mf = (tf >= td - 1) & (tf <= td + 4)
    inn = np.hypot(fl["innovation[0]"][mf], fl["innovation[1]"][mf])
    r = D["vehicle_angular_velocity"]
    tr = r["timestamp"] / 1e6
    mr = (tr >= td - 1) & (tr <= td + 4)
    rr = np.hypot(r["xyz[0]"][mr], r["xyz[1]"][mr])
    m3 = (t >= td - 1) & (t <= td + 4)
    tt = t[m3]
    # prędkość pozycji niewyjaśniona prędkością, okno 0.25 s
    n = max(1, int(0.25 / float(np.median(np.diff(tt)))))
    rs = np.hypot(p["x"][m3][n:] - p["x"][m3][:-n] - (i_v[0][m3][n:] - i_v[0][m3][:-n]), p["y"][m3][n:] - p["y"][m3][:-n] - (i_v[1][m3][n:] - i_v[1][m3][:-n])) / 0.25
    return {"wektor_skoku_3s": round(zw[0], 3), "wektor_skoku_15s": round(z2[0], 3), "rezyduum_3s": round(zw[1], 3), "kontrola_orbita": {"n_okien": len(kon), "wektor_max": round(max(x[0] for x in kon), 3), "wektor_p50": round(float(np.median([x[0] for x in kon])), 3), "rezyduum_max": round(max(x[1] for x in kon), 3), "rezyduum_p50": round(float(np.median([x[1] for x in kon])), 3)},
            "t_szczyt_innowacji_flow": round(float(tf[mf][inn.argmax()] - td), 2), "innowacja_szczyt": round(float(inn.max()), 3), "t_szczyt_rate_rp": round(float(tr[mr][rr.argmax()] - td), 2), "rate_rp_szczyt": round(float(rr.max()), 2), "t_szczyt_slew": round(float(tt[rs.argmax()] - td), 2), "slew_szczyt_m_s": round(float(rs.max()), 2)}


def seria_bias(D):
    b, at, q = D["estimator_sensor_bias"], D["vehicle_attitude"], D["vehicle_attitude_groundtruth"]
    t, tq, tqg = b["timestamp"] / 1e6, at["timestamp"] / 1e6, q["timestamp"] / 1e6
    out = []
    for x in np.arange(t[0], min(t[0] + 60, t[-1]), 4.0):
        i, j = min(np.searchsorted(tq, x), len(tq) - 1), min(np.searchsorted(tqg, x), len(tqg) - 1)
        y = euler([at[f"q[{k}]"][i] for k in range(4)])[2] - euler([q[f"q[{k}]"][j] for k in range(4)])[2]
        out.append({"t": round(float(x), 1), "bz": round(wart(t, b["gyro_bias[2]"], x), 4), "limit": round(wart(t, b["gyro_bias_limit"], x), 3), "yaw_bl_deg": round(math.degrees((y + math.pi) % (2 * math.pi) - math.pi), 1)})
    return out


def main():
    out = {}
    for n in LOTY:
        d = os.path.join(S2, n)
        w = json.load(open(os.path.join(d, "wyniki.json")))
        ev = {"_ekf": []}
        gtm = []
        for l in open(os.path.join(d, "trace.jsonl")):
            try:
                r = json.loads(l)
            except ValueError:
                continue
            if r["t"] == "ekf":
                ev["_ekf"].append(r)
            elif r["t"] == "gt":
                gtm.append((r["mono"], r["sim"]))
        gtm.sort()
        for r in ev["_ekf"]:
            r["sim"] = float(np.interp(r["mono"], [x[0] for x in gtm], [x[1] for x in gtm]))
        u = ULog(os.path.join(d, "boot.ulg"))
        D = {}
        for x in u.data_list:
            if x.multi_id == 0:
                D[x.name] = x.data
        f = D["estimator_status_flags"]
        ti = f["timestamp"] / 1e6
        t_air = float(ti[np.flatnonzero(f["cs_in_air"] == 1)[0]])
        out[n] = {"t_air": round(t_air, 2), "t_cut": w["t_cut"], "d4a": d4a(D, w["t_cut"], w["t_descent"], t_air), "d4b": d4b(D, w, ev), "d4c": d4c(D, w), "bias_seria": seria_bias(D)}
    p = os.path.join(S2, "d4/d4.json")
    json.dump(out, open(p, "w"), ensure_ascii=False, indent=1)
    print(p)


if __name__ == "__main__":
    main()
