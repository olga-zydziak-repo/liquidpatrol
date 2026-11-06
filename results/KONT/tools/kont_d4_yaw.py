#!/usr/bin/env python3
"""results/KONT/tools/kont_d4_yaw.py — dodatek do D4 (przed lotami drogi B, ANEKS_KONT-2), 0 bootów: obrót heading w zejściu przy komendzie yaw = 0 (kont_s2_probe.py, VelocityNedYaw(0, 0, v_z, 0)) wobec odjazdu pozycji. Wejście: ulogi 5 lotów, d4/d4.json. Wyjście: d4/d4_yaw.json."""
import json
import math
import os

import numpy as np
from pyulog import ULog

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
S2 = os.path.join(ROOT, "results/KONT/s2")


def main():
    d4 = json.load(open(os.path.join(S2, "d4/d4.json")))
    out = {}
    for n, v in d4.items():
        w = json.load(open(os.path.join(S2, n, "wyniki.json")))
        u = ULog(os.path.join(S2, n, "boot.ulg"), ["vehicle_local_position", "vehicle_angular_velocity"])
        D = {x.name: x.data for x in u.data_list if x.multi_id == 0}
        p, r = D["vehicle_local_position"], D["vehicle_angular_velocity"]
        t, tr = p["timestamp"] / 1e6, r["timestamp"] / 1e6
        td = w["t_descent"]
        h0, h3 = float(p["heading"][np.searchsorted(t, td)]), float(p["heading"][np.searchsorted(t, td + 3)])
        obrot = abs(math.degrees((h3 - h0 + math.pi) % (2 * math.pi) - math.pi))
        m, mo = (tr >= td - 1) & (tr <= td + 4), (tr >= w["t_cut"] + 1) & (tr < td - 3)
        z = np.abs(r["xyz[2]"])
        out[n] = {"heading_zejscie_deg": round(math.degrees(h0), 1), "heading_3s_deg": round(math.degrees(h3), 1), "obrot_3s_deg": round(obrot, 1), "yaw_rate_max": round(float(z[m].max()), 2), "t_yaw_rate_max": round(float(tr[m][z[m].argmax()] - td), 2), "yaw_rate_orbita_p99": round(float(np.percentile(z[mo], 99)), 2),
                  "wektor_skoku_3s": v["d4c"]["wektor_skoku_3s"], "rezyduum_3s": v["d4c"]["rezyduum_3s"], "t_szczyt_slew": v["d4c"]["t_szczyt_slew"], "delta_kanon": v["d4b"]["delta_max_kanon"], "v_styczna": v["d4b"]["v_styczna_gt_w_zejsciu"]}
    L = list(out)
    rk = lambda x: np.argsort(np.argsort(x))
    kor = {}
    for a in ("obrot_3s_deg", "yaw_rate_max", "v_styczna"):
        for b in ("wektor_skoku_3s", "rezyduum_3s", "delta_kanon"):
            x, y = np.array([out[n][a] for n in L]), np.array([out[n][b] for n in L])
            kor[f"{a}~{b}"] = {"pearson": round(float(np.corrcoef(x, y)[0, 1]), 2), "spearman": round(float(np.corrcoef(rk(x), rk(y))[0, 1]), 2)}
    json.dump({"loty": out, "korelacje_n5": kor}, open(os.path.join(S2, "d4/d4_yaw.json"), "w"), ensure_ascii=False, indent=1)
    for n in L:
        print(n, out[n])
    print(kor)


if __name__ == "__main__":
    main()
