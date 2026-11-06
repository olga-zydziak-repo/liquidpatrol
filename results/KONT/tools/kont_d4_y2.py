#!/usr/bin/env python3
"""results/KONT/tools/kont_d4_y2.py — kopia kont_d4_y.py (oryginał nietknięty, wyprodukował reguły dwóch lotów), jedna zmiana: t_air = ostatnie przejście cs_in_air 0→1 przed odcięciem, bo c02_s01_r4 ma cs_in_air = 1 od pierwszej próbki filtra i d4a padał na pustym oknie; d4c od t_air nie zależy. Oryginał: nakładka na kont_d4.py z listą lotów argumentem (ANEKS_KONT-2b §3.2). Metryka bajtowo ta sama: d4a, d4b, d4c, seria_bias z kont_d4.py bez zmian. Dodatek: obrót heading i yaw rate (jak kont_d4_yaw.py) oraz reguła Y: wektor_skoku_3s ≤ kontrola_orbita.wektor_max.
Użycie: kont_d4_y2.py <wyjście.json> <lot> [<lot> ...]; wyjście pod results/KONT/s2/d4/."""
import json
import math
import os
import sys

import numpy as np
from pyulog import ULog

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kont_d4 as K


def ocen(n):
    d = os.path.join(K.S2, n)
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
    D = {x.name: x.data for x in ULog(os.path.join(d, "boot.ulg")).data_list if x.multi_id == 0}
    f = D["estimator_status_flags"]
    tf, ca = f["timestamp"] / 1e6, f["cs_in_air"]
    wej = np.flatnonzero(np.r_[False, (ca[1:] == 1) & (ca[:-1] == 0)] & (tf < w["t_cut"]))
    t_air = float(tf[wej[-1]])
    c = K.d4c(D, w)
    p, r = D["vehicle_local_position"], D["vehicle_angular_velocity"]
    t, tr = p["timestamp"] / 1e6, r["timestamp"] / 1e6
    td = w["t_descent"]
    h0, h3 = float(p["heading"][np.searchsorted(t, td)]), float(p["heading"][np.searchsorted(t, td + 3)])
    m, mo = (tr >= td - 1) & (tr <= td + 4), (tr >= w["t_cut"] + 1) & (tr < td - 3)
    z = np.abs(r["xyz[2]"])
    yaw = {"obrot_3s_deg": round(abs(math.degrees((h3 - h0 + math.pi) % (2 * math.pi) - math.pi)), 1), "yaw_rate_max": round(float(z[m].max()), 2), "yaw_rate_orbita_p99": round(float(np.percentile(z[mo], 99)), 2)}
    return {"t_air": round(t_air, 2), "t_cut": w["t_cut"], "d4a": K.d4a(D, w["t_cut"], td, t_air), "d4b": K.d4b(D, w, ev), "d4c": c, "bias_seria": K.seria_bias(D), "yaw": yaw,
            "regula_y": {"wektor": c["wektor_skoku_3s"], "kontrola": c["kontrola_orbita"]["wektor_max"], "ponizej_kontroli": c["wektor_skoku_3s"] <= c["kontrola_orbita"]["wektor_max"]}}


def main():
    out = {n: ocen(n) for n in sys.argv[2:]}
    json.dump(out, open(os.path.join(K.S2, "d4", sys.argv[1]), "w"), ensure_ascii=False, indent=1)
    for n, v in out.items():
        print(n, v["regula_y"], v["yaw"])


if __name__ == "__main__":
    main()
