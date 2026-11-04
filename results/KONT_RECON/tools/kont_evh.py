#!/usr/bin/env python3
"""results/KONT_RECON/tools/kont_evh.py — evh/eph(t) od utraty z ulogów K2 oraz chwila przekroczenia
COM_VEL_FS_EVH: druga ściana natywna (local_velocity_invalid liczy też evh, estimatorCheck.cpp:754).
Wyjście: results/KONT_RECON/evh.json"""
import glob
import json
import os

import numpy as np
from pyulog import ULog

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
out = []
for d in sorted(glob.glob(os.path.join(ROOT, "results", "K2", "k2c_b*"))):
    p = os.path.join(d, "boot.ulg")
    if not os.path.isfile(p):
        continue
    u = ULog(p, ["vehicle_status", "vehicle_local_position"])
    g = lambda n: [x for x in u.data_list if x.name == n and x.multi_id == 0][0].data
    vs, lp = g("vehicle_status"), g("vehicle_local_position")
    t14 = vs["timestamp"][int(np.argmax(vs["nav_state"] == 14))]
    m = lp["timestamp"] > t14
    tt, dr, evh, eph = lp["timestamp"][m], lp["dead_reckoning"][m], lp["evh"][m], lp["eph"][m]
    t0 = tt[int(np.argmax(dr > 0))]
    prof = {}
    for s in (1, 2, 3, 4, 5, 6, 8, 9):
        q = int(np.searchsorted(tt, t0 + s * 1e6))
        if q < len(evh):
            prof[str(s)] = [round(float(evh[q]), 3), round(float(eph[q]), 2)]
    a = tt >= t0
    over = np.nonzero(evh[a] > 1.0)[0]
    out.append({"boot": os.path.basename(d), "evh_eph": prof,
                "t_evh_gt_1": round(float((tt[a][over[0]] - t0) / 1e6), 2) if len(over) else None})
    print(out[-1])
json.dump(out, open(os.path.join(ROOT, "results", "KONT_RECON", "evh.json"), "w"), ensure_ascii=False, indent=0)
