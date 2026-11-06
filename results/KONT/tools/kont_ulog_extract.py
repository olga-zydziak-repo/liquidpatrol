#!/usr/bin/env python3
"""results/KONT/tools/kont_ulog_extract.py — wyciąg per boot z ulogu (PRE_KONT §2.7, PROMPT_KONT_S1 §1.5).
Każdy wniosek o stanie pojazdu z tego pliku, nie z listy zdarzeń trace. Czas = stempel PX4 [s]; w SITL lockstep to czas sim.
Wyjście: jsonl, wiersz na zmianę stanu + wiersze "seria" (1 Hz: jakość flow, dalmierz) + wiersz "podsumowanie".
Użycie: kont_ulog_extract.py <boot.ulg> <wyjście.jsonl> [--t-cut <s PX4>]; bez --t-cut odniesieniem jest zbocze dead_reckoning
w offboard (definicja kont_native_wall.py, K2)."""
import json
import sys

import numpy as np
from pyulog import ULog

TOPICS = ["vehicle_status", "vehicle_local_position", "failsafe_flags", "estimator_status_flags", "vehicle_optical_flow",
          "estimator_aid_src_optical_flow", "distance_sensor", "vehicle_land_detected", "estimator_status"]
TRACK = [("vehicle_status", "nav_state"), ("vehicle_status", "failsafe"), ("vehicle_status", "arming_state"),
         ("vehicle_local_position", "xy_valid"), ("vehicle_local_position", "v_xy_valid"),
         ("vehicle_local_position", "dead_reckoning"), ("vehicle_local_position", "dist_bottom_valid"),
         ("failsafe_flags", "offboard_control_signal_lost"), ("failsafe_flags", "local_position_invalid"),
         ("estimator_status_flags", "cs_gnss_pos"), ("estimator_status_flags", "cs_gnss_vel"),
         ("estimator_status_flags", "cs_opt_flow"), ("estimator_status_flags", "cs_inertial_dead_reckoning"),
         ("estimator_status_flags", "cs_rng_hgt"), ("estimator_status_flags", "cs_baro_hgt"),
         ("estimator_status_flags", "reject_optflow_x"), ("estimator_status_flags", "reject_optflow_y"),
         ("vehicle_land_detected", "landed")]


def load(path):
    u = ULog(path, TOPICS)
    d = {}
    for x in u.data_list:
        if x.multi_id == 0:
            d[x.name] = x.data
    return u, d


def transitions(t, v):
    idx = np.flatnonzero(v[1:] != v[:-1]) + 1
    return [(int(t[0]), int(v[0]))] + [(int(t[i]), int(v[i])) for i in idx]


def dr_edge(d):
    """Zbocze dead_reckoning po pierwszym nav=14 (kont_native_wall.py). None, gdy nie ma."""
    vs, lp = d["vehicle_status"], d["vehicle_local_position"]
    if not (vs["nav_state"] == 14).any():
        return None
    t14 = vs["timestamp"][int(np.argmax(vs["nav_state"] == 14))]
    m = lp["timestamp"] > t14
    if not (lp["dead_reckoning"][m] > 0).any():
        return None
    return int(lp["timestamp"][m][int(np.argmax(lp["dead_reckoning"][m] > 0))])


def first_after(d, topic, field, t0, pred):
    tt, vv = d[topic]["timestamp"], d[topic][field]
    m = tt > t0
    if not pred(vv[m]).any():
        return None
    return round((int(tt[m][int(np.argmax(pred(vv[m])))]) - t0) / 1e6, 3)


def extract(path, t_cut_s=None):
    u, d = load(path)
    edge = dr_edge(d)
    t0 = int(t_cut_s * 1e6) if t_cut_s is not None else edge
    rows = []
    for topic, f in TRACK:
        if topic in d and f in d[topic]:
            for t, v in transitions(d[topic]["timestamp"], d[topic][f]):
                rows.append({"t": "zmiana", "topic": topic, "pole": f, "ts": round(t / 1e6, 3), "wartosc": v,
                             "od_ref_s": round((t - t0) / 1e6, 3) if t0 else None})
    rows.sort(key=lambda r: r["ts"])
    for t, name, val in u.changed_parameters:
        rows.append({"t": "param", "ts": round(t / 1e6, 3), "nazwa": name, "wartosc": val,
                     "od_ref_s": round((t - t0) / 1e6, 3) if t0 else None})
    for topic, f in (("vehicle_optical_flow", "quality"), ("distance_sensor", "current_distance"),
                     ("estimator_aid_src_optical_flow", "fused"), ("estimator_aid_src_optical_flow", "innovation_rejected")):
        if topic in d and f in d[topic]:
            tt, vv = d[topic]["timestamp"], d[topic][f]
            for s in np.unique(tt // 1000000):
                m = tt // 1000000 == s
                rows.append({"t": "seria", "topic": topic, "pole": f, "ts": int(s), "srednia": round(float(vv[m].mean()), 3),
                             "min": round(float(vv[m].min()), 3), "n": int(m.sum())})
    podsum = {"t": "podsumowanie", "t_ref_s": round(t0 / 1e6, 3) if t0 else None, "ref": "cut" if t_cut_s is not None else "dr_edge",
              "t_dr_edge_s": round(edge / 1e6, 3) if edge else None, "ostatni_ts": round(float(d["vehicle_status"]["timestamp"][-1]) / 1e6, 3),
              "params": {k: u.initial_parameters.get(k) for k in ("EKF2_OF_CTRL", "EKF2_RNG_CTRL", "EKF2_HGT_REF", "EKF2_GPS_CTRL",
                                                                  "EKF2_NOAID_TOUT", "EKF2_OF_QMIN", "SDLOG_MODE")}}
    if t0:
        podsum.update(t_xy_invalid_s=first_after(d, "vehicle_local_position", "xy_valid", t0, lambda v: v == 0),
                      t_vxy_invalid_s=first_after(d, "vehicle_local_position", "v_xy_valid", t0, lambda v: v == 0),
                      t_dr_po_ref_s=first_after(d, "vehicle_local_position", "dead_reckoning", t0, lambda v: v > 0),
                      t_offboard_lost_s=first_after(d, "failsafe_flags", "offboard_control_signal_lost", t0, lambda v: v == 1),
                      t_nav_change_s=first_after(d, "vehicle_status", "nav_state", t0, lambda v: v != 14),
                      t_cs_gnss_pos_off_s=first_after(d, "estimator_status_flags", "cs_gnss_pos", t0, lambda v: v == 0))
    rows.append(podsum)
    return rows


def main():
    a = sys.argv[1:]
    tc = float(a[a.index("--t-cut") + 1]) if "--t-cut" in a else None
    rows = extract(a[0], tc)
    with open(a[1], "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps(rows[-1], ensure_ascii=False))


if __name__ == "__main__":
    main()
