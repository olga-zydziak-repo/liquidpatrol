#!/usr/bin/env python3
"""results/TEACH2_RECON/tools/t2r_r2.py — PROMPT_TEACH2_S0 §4 R2: geometria z manifestu (0 bootów).

Intruz: manifest NAD3 v2 (results/NAD3/s1/scenario_manifest_nad3_v2.json), epizody c05_s01 / c10_s01, wahadło jak NAD2 S4
(results/NAD2/tools/nad2_s4_manifest.wahadlo, import, plik nietknięty; długość w tym procesie 1000 s), pozycja z
bench.scenarios.position_at co 0.1 s przez pełny okres wahadła [0, 400] s (i dla kontroli do 830 s): największy promień od (0, 0).
Dron: 12 cięć bramki S3 — GT drona z rama.jsonl (pole gt, ENU) i GT intruza z gt_intruder.jsonl (pole ned → E = ned[1],
N = ned[0]), najbliższa w czasie próbka intruza (≤ 0.05 s); okno misji jak sędzia (sedzia_s3.json okno_misji). Sprawdzian ramy:
udział odległości dron–intruz w paśmie 6–10 m wobec pasma sędziego.
Przewidywany promień drona = największy promień intruza + największa odległość dron–intruz z 12 cięć (per komórka i łącznie);
zapas do bariery 24.84 m.
Wyjście: results/TEACH2_RECON/r2.json.
"""
import json
import math
import os
import sys

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/NAD2/tools"), os.path.join(ROOT, "results/NAD3_RECON/tools")]
from bench import scenarios as S                         # noqa: E402
import nad2_s4_manifest as W                             # noqa: E402
import nad3_dane as N3                                   # noqa: E402

MAN = os.path.join(ROOT, "results/NAD3/s1/scenario_manifest_nad3_v2.json")
S3 = os.path.join(ROOT, "results/TEACH/s3")
BARIERA = 24.84
CIECIA = {"c05": ["p01_S_c05_a", "p03_S_c05_b", "p06_M_c05_a", "p08_M_c05_b", "p11_J_c05_a", "p13_J_c05_b"],
          "c10": ["p02_S_c10_a", "p04_S_c10_b", "p07_M_c10_a", "p09_M_c10_b", "p12_J_c10_a", "p14_J_c10_b"]}


def intruz(ep):
    W.EP_DUR_S_L = 1000.0
    e = W.wahadlo(ep)
    t = np.arange(0.0, 830.0 + 1e-9, 0.1)
    p = np.array([S.position_at(e, x)[:2] for x in t])
    r = np.hypot(p[:, 0], p[:, 1])
    okr = t <= 400.0 + 1e-9
    i = int(np.argmax(np.where(okr, r, -1)))
    skok = float(np.max(np.hypot(*np.diff(p, axis=0).T)))
    return {"r_max_400s": round(float(r[okr].max()), 3), "t_r_max": round(float(t[i]), 1),
            "r_max_200s": round(float(r[t <= 200.0 + 1e-9].max()), 3), "r_max_830s": round(float(r.max()), 3),
            "najwiekszy_krok_0p1s_m": round(skok, 4), "v_max": max(sg["v"] for sg in ep["segments"]),
            "n_odcinkow_wahadla": len(e["segments"])}


def lot(nazwa):
    d = os.path.join(S3, nazwa)
    s = json.load(open(os.path.join(d, "sedzia_s3.json")))
    t0, t1 = s["epizody"][0]["okno_misji"]
    ii = [json.loads(l) for l in open(os.path.join(d, "gt_intruder.jsonl"))]
    ti = np.array([r["t_sim"] for r in ii])
    pi = np.array([[r["ned"][1], r["ned"][0]] for r in ii])
    od, rd, dt_max = [], [], 0.0
    for r in N3.jl(d, "rama.jsonl"):
        if not (t0 <= r["sim"] <= t1) or r.get("gt") is None:
            continue
        j = int(np.clip(np.searchsorted(ti, r["sim"]), 1, len(ti) - 1))
        j = j if abs(ti[j] - r["sim"]) < abs(ti[j - 1] - r["sim"]) else j - 1
        if abs(ti[j] - r["sim"]) > 0.05:
            continue
        dt_max = max(dt_max, abs(ti[j] - r["sim"]))
        g = np.array(r["gt"][:2])
        od.append(float(np.linalg.norm(g - pi[j])))
        rd.append(float(np.hypot(*g)))
    od = np.array(od)
    return {"lot": nazwa, "n": len(od), "max_dron_intruz": round(float(od.max()), 3), "p99_dron_intruz": round(float(np.quantile(od, .99)), 3),
            "udzial_pasmo_6_10": round(float(((od >= 6) & (od <= 10)).mean()), 4), "pasmo_sedzia": s["epizody"][0]["pasmo"],
            "r_max_dron": round(max(rd), 3), "dt_max_s": round(dt_max, 4)}


def main():
    m = json.load(open(MAN))
    out = {"bariera": BARIERA, "komorki": {}}
    for kom in ("c05", "c10"):
        ep = next(e for e in m["episodes"] if e["scenario_id"] == f"{kom}_s01")
        it = intruz(ep)
        loty = [lot(n) for n in CIECIA[kom]]
        dmax = max(l["max_dron_intruz"] for l in loty)
        prz = round(it["r_max_400s"] + dmax, 3)
        out["komorki"][kom] = {"intruz": it, "max_dron_intruz_6_lotow": dmax, "promien_przewidywany": prz,
                               "zapas_do_bariery": round(BARIERA - prz, 3), "r_max_dron_zmierzony": max(l["r_max_dron"] for l in loty),
                               "loty": loty}
        print(kom, json.dumps({k: v for k, v in out["komorki"][kom].items() if k != "loty"}, ensure_ascii=False), flush=True)
    dm = max(v["max_dron_intruz_6_lotow"] for v in out["komorki"].values())
    for kom, v in out["komorki"].items():
        v["promien_przewidywany_z_12_ciec"] = round(v["intruz"]["r_max_400s"] + dm, 3)
        v["zapas_z_12_ciec"] = round(BARIERA - v["promien_przewidywany_z_12_ciec"], 3)
    out["max_dron_intruz_12_ciec"] = dm
    json.dump(out, open(os.path.join(ROOT, "results/TEACH2_RECON/r2.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: (v["promien_przewidywany_z_12_ciec"], v["zapas_z_12_ciec"]) for k, v in out["komorki"].items()}), dm)


if __name__ == "__main__":
    main()
