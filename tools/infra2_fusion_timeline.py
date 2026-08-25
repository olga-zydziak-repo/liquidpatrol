#!/usr/bin/env python3
"""
tools/infra2_fusion_timeline.py — ANEKS_INFRA2-5rev V1: oś czasu źródeł wspomagających EKF.
OFFLINE, read-only. Booty: b4 (odzyskał), b7 (czysty), FAIL {1,3,5} (zatrzask).

(a) estimator_status_flags: sim-czas PIERWSZEGO wejścia każdego źródła do fuzji (cs_* → 1).
(b) estimator_status reset_count_* + vehicle_local_position *_reset_counter (końcowe + liczba inkrementów);
    estimator_event_flags reset_* (liczba zdarzeń reinicjalizacji).
(e) estimator_status.time_slip (max/koniec).
    fault flags (fs_bad_*, cs_*_fault, filter_fault_flags) — kiedy pierwszy raz true.
"""
import sys, json
import numpy as np
from pyulog import ULog

CS_WATCH = ["cs_tilt_align", "cs_yaw_align", "cs_vehicle_at_rest", "cs_baro_hgt",
            "cs_mag", "cs_mag_hdg", "cs_mag_3d", "cs_gnss_pos", "cs_gnss_vel",
            "cs_gps_hgt", "cs_in_air"]
FAULT_WATCH = ["cs_baro_fault", "cs_mag_fault", "cs_mag_field_disturbed",
               "fs_bad_hdg", "fs_bad_mag_x", "fs_bad_mag_y", "fs_bad_mag_z",
               "fs_bad_acc_vertical", "fs_bad_acc_clipping"]
RESET_CNT = ["reset_count_quat", "reset_count_pos_ne", "reset_count_vel_ne",
             "reset_count_vel_d", "reset_count_pod_d"]
EVENT_WATCH = ["reset_hgt_to_baro", "reset_hgt_to_gps", "reset_pos_to_gps",
               "reset_vel_to_gps", "reset_vel_to_zero", "reset_pos_to_last_known"]


def first_true(sim, arr):
    idx = np.where(arr != 0)[0]
    return round(float(sim[idx[0]]), 2) if len(idx) else None


def analyze(b):
    d = f"results/K1/E/p0_0/boot{b}"
    u = ULog(d + "/boot.ulg", ["estimator_status_flags", "estimator_status",
                               "vehicle_local_position", "estimator_event_flags",
                               "actuator_armed"])
    out = {"boot": b}

    # arm sim
    a = u.get_dataset("actuator_armed")
    ats = a.data["timestamp"].astype(float) / 1e6
    ai = np.where(a.data["armed"] == 1)[0]
    out["arm_sim"] = round(float(ats[ai[0]]), 2) if len(ai) else None

    # (a) cs_ flags first-true
    f = u.get_dataset("estimator_status_flags")
    fs = f.data["timestamp"].astype(float) / 1e6
    out["cs_first_true"] = {k: first_true(fs, f.data[k]) for k in CS_WATCH if k in f.data}
    out["fault_first_true"] = {k: first_true(fs, f.data[k]) for k in FAULT_WATCH if k in f.data}

    # (b/e) estimator_status: reset counts final + increments, time_slip
    es = u.get_dataset("estimator_status")
    ets = es.data["timestamp"].astype(float) / 1e6
    rc = {}
    for k in RESET_CNT:
        if k in es.data:
            v = es.data[k]
            incs = int(np.sum(np.diff(v) != 0))
            rc[k] = {"final": int(v[-1]), "incs": incs}
    out["reset_counts"] = rc
    if "time_slip" in es.data:
        ts_ = es.data["time_slip"]
        out["time_slip"] = {"max": round(float(np.max(np.abs(ts_))), 4),
                            "end": round(float(ts_[-1]), 4)}
    if "filter_fault_flags" in es.data:
        ff = es.data["filter_fault_flags"]
        out["filter_fault_flags_max"] = int(np.max(ff))

    # vehicle_local_position reset counters
    lp = u.get_dataset("vehicle_local_position")
    lpr = {}
    for k in ["xy_reset_counter", "z_reset_counter", "vxy_reset_counter",
              "vz_reset_counter", "heading_reset_counter"]:
        if k in lp.data:
            lpr[k] = int(lp.data[k][-1])
    out["lp_reset_final"] = lpr

    # (b) event flags counts
    try:
        ev = u.get_dataset("estimator_event_flags")
        evc = {}
        for k in EVENT_WATCH:
            if k in ev.data:
                evc[k] = int(np.sum(ev.data[k] != 0))
        out["event_counts"] = {k: v for k, v in evc.items() if v}
    except Exception:
        out["event_counts"] = {}

    return out


def main():
    boots = ["4", "7", "1", "3", "5"]
    cls = {"4": "PASS-recover", "7": "PASS-clean", "1": "FAIL", "3": "FAIL", "5": "FAIL"}
    res = {}
    for b in boots:
        try:
            res[b] = analyze(b)
            res[b]["class"] = cls[b]
        except Exception as e:
            res[b] = {"boot": b, "err": str(e)}
    with open("results/K1/INFRA1/V1_fusion_timeline.json", "w") as fjson:
        json.dump(res, fjson, indent=2)

    # tabela (a) cs first-true
    print("=== (a) cs_* PIERWSZE wejście do fuzji [sim s] + arm ===")
    hdr = ["boot", "cls", "arm"] + [k.replace("cs_", "") for k in CS_WATCH]
    print(" | ".join("%-11s" % h for h in hdr))
    for b in boots:
        r = res[b]
        if "err" in r:
            print(b, "ERR", r["err"]); continue
        row = [b, r["class"], str(r["arm_sim"])] + [str(r["cs_first_true"].get(k)) for k in CS_WATCH]
        print(" | ".join("%-11s" % c for c in row))

    print("\n=== (fault) fs/cs_fault PIERWSZE true [sim s] ===")
    for b in boots:
        r = res[b]
        if "err" in r: continue
        ft = {k: v for k, v in r["fault_first_true"].items() if v is not None}
        print(f"boot{b} {r['class']}: {ft if ft else 'ZADEN fault'}")

    print("\n=== (b/e) resety + time_slip + filter_fault ===")
    for b in boots:
        r = res[b]
        if "err" in r: continue
        rc = {k: v["final"] for k, v in r["reset_counts"].items()}
        print(f"boot{b} {r['class']}: reset_final={rc} lp_reset={r['lp_reset_final']} "
              f"events={r.get('event_counts')} time_slip={r.get('time_slip')} "
              f"filter_fault_max={r.get('filter_fault_flags_max')}")
    print("\nJSON → results/K1/INFRA1/V1_fusion_timeline.json")


if __name__ == "__main__":
    main()
