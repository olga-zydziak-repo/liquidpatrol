#!/usr/bin/env python3
"""results/KONT/s4/d5diag/kont_d5diag.py — D5-diag (ANEKS_KONT-4c §2): inicjalizacja estymatora przy biurku, 0 bootów.

Per boot, wyłącznie z ulogu (czas = stempel PX4 = sim w lockstep):
  1. yaw(t): błąd = yaw(vehicle_attitude) − yaw(vehicle_attitude_groundtruth), oba kwaterniony FRD→NED z PX4, zawinięty
     do ±180°; próbki od startu, w punktach 5/10/20/30/60/90/120 s, przed uzbrojeniem (ostatnia próbka przed
     arming_state=2 albo koniec logu), max |błąd| w oknie [t0+5 s, uzbrojenie); „płasko" = rozrzut yaw EKF < 1° w oknie
     ostatnich 30 s przed uzbrojeniem. Reinity watchdoga (ekf_watchdog.json, czas sim) z błędem yaw 3 s przed i 15 s po.
  2. Magnetometr: przejścia cs_yaw_align, cs_mag_hdg, cs_mag_3d, cs_mag_fault, cs_mag_field_disturbed,
     cs_mag_heading_consistent, cs_tilt_align (estimator_status_flags); test_ratio heading/mag z estimator_aid_src_mag
     (pola wypisane z ulogu); parametry EKF2_MAG_TYPE/EKF2_MAG_CHECK/EKF2_MAG_CHK_STR/EKF2_MAG_CHK_INC/EKF2_DECL_TYPE/
     SYS_HAS_MAG z initial_parameters.
  3. Bias: estimator_sensor_bias gyro_bias — pierwsza próbka, |max| w 30 s, wartość przed uzbrojeniem; pierwsza próbka
     sensor_combined/vehicle_imu (timestamp, timestamp_sample jeśli jest); faza dołączenia z manifestu/px4_join.
  4. Tor S4 vs S2 przed kontrolą: czasy (sim) uzbrojenia i kontroli yaw z trace vs okno inicjalizacji EKF (cs_yaw_align).
Użycie: kont_d5diag.py <wyjście.json>. Zbiór bootów stały w BOOTS (S4, S2-Y, S2 z reinitem, kontrola starego launchera)."""
import json
import math
import os
import sys

import numpy as np
from pyulog import ULog

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
BOOTS = [("S4", "results/KONT/s4/nom_b1"), ("S4", "results/KONT/s4/nom_b1_r2"), ("S4", "results/KONT/s4/nom_b2"),
         ("S2-Y", "results/KONT/s2/c11_s04_r3"), ("S2-Y", "results/KONT/s2/c08_s02b_r2"), ("S2-Y", "results/KONT/s2/c02_s01_r4"),
         ("S2-reinit", "results/KONT/s2/c00_s02_r3"),
         ("kontrola-stary-launcher", "results/SKAN2/s1/bA_c08"), ("kontrola-stary-launcher", "results/SKAN2/s1/bB_c1011"),
         ("kontrola-stary-launcher", "results/PERC2/s2/bA_c08"), ("kontrola-stary-launcher", "results/PERC2/s2/bB_c1011")]
FLAGS = ["cs_tilt_align", "cs_yaw_align", "cs_mag_hdg", "cs_mag_3d", "cs_mag_fault", "cs_mag_field_disturbed",
         "cs_mag_heading_consistent", "cs_mag"]
PARAMS = ["EKF2_MAG_TYPE", "EKF2_MAG_CHECK", "EKF2_MAG_CHK_STR", "EKF2_MAG_CHK_INC", "EKF2_DECL_TYPE", "SYS_HAS_MAG",
          "EKF2_GPS_CTRL", "EKF2_OF_CTRL", "EKF2_HGT_REF"]


def yaw_q(q0, q1, q2, q3):
    return np.arctan2(2 * (q0 * q3 + q1 * q2), 1 - 2 * (q2 * q2 + q3 * q3))


def wrap_deg(x):
    return (np.degrees(x) + 180.0) % 360.0 - 180.0


def topic(u, name):
    return next((d.data for d in u.data_list if d.name == name and d.multi_id == 0), None)


def trans(t, v):
    v = np.asarray(v)
    idx = np.r_[0, np.flatnonzero(v[1:] != v[:-1]) + 1]
    return [(round(float(t[i]) / 1e6, 3), int(v[i])) for i in idx]


def boot(grp, rel):
    d = os.path.join(ROOT, rel)
    p = os.path.join(d, "boot.ulg")
    out = {"grupa": grp, "boot": rel}
    if not os.path.exists(p):
        out["brak_ulogu"] = True
        return out
    u = ULog(p)
    out["parametry"] = {k: u.initial_parameters.get(k) for k in PARAMS}
    att, gt = topic(u, "vehicle_attitude"), topic(u, "vehicle_attitude_groundtruth")
    vs, fl = topic(u, "vehicle_status"), topic(u, "estimator_status_flags")
    sb, sc, vi = topic(u, "estimator_sensor_bias"), topic(u, "sensor_combined"), topic(u, "vehicle_imu")
    t_arm = None
    if vs is not None:
        a = np.flatnonzero(vs["arming_state"] == 2)
        t_arm = float(vs["timestamp"][a[0]]) / 1e6 if a.size else None
    out["t_uzbrojenia_s"] = t_arm
    if att is not None and gt is not None:
        ta, tg = att["timestamp"] / 1e6, gt["timestamp"] / 1e6
        ye = yaw_q(att["q[0]"], att["q[1]"], att["q[2]"], att["q[3]"])
        yg = np.interp(ta, tg, np.unwrap(yaw_q(gt["q[0]"], gt["q[1]"], gt["q[2]"], gt["q[3]"])))
        err = wrap_deg(ye - yg)
        t0 = float(ta[0])
        out["t0_attitude_s"] = round(t0, 3)
        pts = {}
        for k in (0, 5, 10, 20, 30, 60, 90, 120):
            i = int(np.searchsorted(ta, t0 + k))
            if i < len(ta) and (t_arm is None or ta[i] < t_arm):
                pts[str(k)] = {"yaw_ekf_deg": round(float(np.degrees(ye[i])), 2), "yaw_gt_deg": round(float(np.degrees(yg[i])), 2),
                               "blad_deg": round(float(err[i]), 2)}
        out["yaw_punkty"] = pts
        end = t_arm if t_arm is not None else float(ta[-1])
        m = (ta >= t0 + 5) & (ta < end)
        if m.any():
            out["blad_max_abs_przed_uzbr_deg"] = round(float(np.abs(err[m]).max()), 2)
            ib = np.flatnonzero(m)[-1]
            out["blad_przed_uzbr_deg"] = round(float(err[ib]), 2)
            w = m & (ta >= end - 30)
            out["yaw_ekf_rozrzut_30s_deg"] = round(float(np.ptp(np.degrees(np.unwrap(ye[w])))), 3) if w.any() else None
            out["plasko_30s"] = out["yaw_ekf_rozrzut_30s_deg"] is not None and out["yaw_ekf_rozrzut_30s_deg"] < 1.0
        wd = os.path.join(d, "ekf_watchdog.json")
        if os.path.exists(wd):
            W = json.load(open(wd))
            out["watchdog"] = {"n_reinits": W.get("n_reinits"), "bias_max": W.get("bias_max"), "first_fault_sim": W.get("first_fault_sim")}
            rr = []
            for r in W.get("reinits", []):
                ts = r.get("sim") or r.get("sim_before") or r.get("t_sim")
                if ts is None:
                    continue
                pre = np.flatnonzero((ta >= ts - 3) & (ta < ts))
                post = np.flatnonzero((ta >= ts + 10) & (ta < ts + 15))
                rr.append({"sim": ts, "powod": r.get("reason"), "bias_przed": r.get("bias_before") or r.get("bias_pre"),
                           "bias_po": r.get("bias_after") or r.get("bias_post"),
                           "blad_yaw_przed_deg": round(float(err[pre[-1]]), 2) if pre.size else None,
                           "blad_yaw_po_10_15s_deg": round(float(np.median(err[post])), 2) if post.size else None})
            out["reinity"] = rr
    if fl is not None:
        out["flagi"] = {f: trans(fl["timestamp"], fl[f]) for f in FLAGS if f in fl}
    if sb is not None:
        tb = sb["timestamp"] / 1e6
        gb = np.stack([sb["gyro_bias[0]"], sb["gyro_bias[1]"], sb["gyro_bias[2]"]], axis=1)
        out["bias_pierwsza"] = [round(float(x), 5) for x in gb[0]]
        out["bias_t_pierwsza_s"] = round(float(tb[0]), 3)
        w = tb <= tb[0] + 30
        out["bias_absmax_30s"] = round(float(np.abs(gb[w]).max()), 5)
        if t_arm is not None:
            i = max(0, int(np.searchsorted(tb, t_arm)) - 1)
            out["bias_przed_uzbr"] = [round(float(x), 5) for x in gb[i]]
    for nm, t in (("sensor_combined", sc), ("vehicle_imu", vi)):
        if t is not None:
            out[f"{nm}_pierwsza"] = {"timestamp_s": round(float(t["timestamp"][0]) / 1e6, 4),
                                    **({"timestamp_sample_s": round(float(t["timestamp_sample"][0]) / 1e6, 4)} if "timestamp_sample" in t else {})}
    ma = topic(u, "estimator_aid_src_mag")
    if ma is not None:
        keys = [k for k in ma if "test_ratio" in k or k.startswith("fused") or k.startswith("innovation_rejected")]
        out["aid_src_mag_pola"] = keys
        tm = ma["timestamp"] / 1e6
        end = t_arm if t_arm is not None else float(tm[-1])
        w = tm < end
        out["aid_src_mag"] = {k: {"pierwsza": round(float(ma[k][0]), 4), "przed_uzbr": round(float(ma[k][w][-1]), 4) if w.any() else None,
                                 "max": round(float(np.max(ma[k][w])), 4) if w.any() else None} for k in keys}
    jp = os.path.join(d, "px4_join.json")
    if os.path.exists(jp):
        out["px4_join"] = json.load(open(jp))
    try:
        log = open(os.path.join(d, "px4.log"), errors="replace").read()
        import re
        x = re.search(r"initial absolute time to (\d+)", log)
        out["initial_absolute_time_us"] = int(x.group(1)) if x else None
    except OSError:
        pass
    tr = os.path.join(d, "trace.jsonl")
    if os.path.exists(tr):
        ev = {}
        for l in open(tr):
            if '"t": "event"' in l:
                r = json.loads(l)
                ev.setdefault(r["ev"], r.get("sim"))
        out["trace_sim"] = {k: ev.get(k) for k in ("yaw_assert", "armed", "takeoff")}
    yj = os.path.join(d, "kont_yaw.json")
    if os.path.exists(yj):
        out["kont_yaw"] = json.load(open(yj))
    return out


def main():
    res = [boot(g, b) for g, b in BOOTS]
    json.dump(res, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
    for r in res:
        print(r["boot"], r["grupa"], "| t0", r.get("t0_attitude_s"), "init_us", r.get("initial_absolute_time_us"),
              "| błąd przed uzbr", r.get("blad_przed_uzbr_deg"), "max", r.get("blad_max_abs_przed_uzbr_deg"), "płasko", r.get("plasko_30s"),
              "| bias1", r.get("bias_pierwsza"), "max30", r.get("bias_absmax_30s"), "| reinity", r.get("reinity"),
              "| kont_yaw", (r.get("kont_yaw") or {}).get("yaw_blad_deg"))


if __name__ == "__main__":
    main()
