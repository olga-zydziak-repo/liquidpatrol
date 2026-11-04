#!/usr/bin/env python3
"""results/KONT_RECON/tools/kont_native_wall.py — ściana natywna pod denialem: chwila, w której PX4 odbiera
offboard (nav 14→12 DESCEND), liczona z ulogów biegów K2 (denial w locie, sieć w pętli). Czas od zbocza
dead_reckoning w locie. Wyjście: results/KONT_RECON/native_wall.json"""
import glob
import json
import os
import sys

import numpy as np
from pyulog import ULog

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def run(d):
    u = ULog(os.path.join(d, "boot.ulg"), ["vehicle_status", "vehicle_local_position", "failsafe_flags"])
    g = lambda n: [x for x in u.data_list if x.name == n and x.multi_id == 0][0].data
    vs, lp, ff = g("vehicle_status"), g("vehicle_local_position"), g("failsafe_flags")
    # lot: pierwsze wejście nav=14 (offboard); denial: pierwsze zbocze DR po nim
    i14 = int(np.argmax(vs["nav_state"] == 14))
    t14 = vs["timestamp"][i14]
    m = lp["timestamp"] > t14
    tt, dr = lp["timestamp"][m], lp["dead_reckoning"][m]
    k = int(np.argmax(dr > 0))
    t0 = tt[k]
    a = vs["timestamp"] > t0
    tv, nv, fs = vs["timestamp"][a], vs["nav_state"][a], vs["failsafe"][a]
    j = int(np.argmax(nv != 14))
    nav_after = int(nv[j])
    t_nav = (tv[j] - t0) / 1e6
    fv = lp["timestamp"] > t0
    tl, xv, vv, z, vz = lp["timestamp"][fv], lp["xy_valid"][fv], lp["v_xy_valid"][fv], lp["z"][fv], lp["vz"][fv]
    t_xy = (tl[int(np.argmax(xv == 0))] - t0) / 1e6
    t_vxy = (tl[int(np.argmax(vv == 0))] - t0) / 1e6
    ffm = ff["timestamp"] > t0
    t_ofl = (ff["timestamp"][ffm][int(np.argmax(ff["offboard_control_signal_lost"][ffm] == 1))] - t0) / 1e6
    prof = {}
    for s in (1, 2, 3, 4, 5, 6, 7, 8, 9):
        q = int(np.searchsorted(tl, t0 + s * 1e6))
        if q < len(z):
            prof[str(s)] = [round(float(z[q]), 2), round(float(vz[q]), 2)]
    return {"boot": os.path.basename(d), "t_xy_invalid_s": round(float(t_xy), 2), "t_vxy_invalid_s": round(float(t_vxy), 2),
            "t_offboard_lost_s": round(float(t_ofl), 2), "t_nav_change_s": round(float(t_nav), 2), "nav_po": nav_after,
            "failsafe_po": int(fs[j]), "z_vz_od_utraty": prof}


res = []
for d in sorted(glob.glob(os.path.join(ROOT, "results", "K2", "k2c_b*"))):
    if os.path.isfile(os.path.join(d, "boot.ulg")):
        res.append(run(d)); print(json.dumps(res[-1], ensure_ascii=False))
json.dump({"biegi": res}, open(os.path.join(ROOT, "results", "KONT_RECON", "native_wall.json"), "w"), ensure_ascii=False, indent=0)
