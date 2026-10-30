#!/usr/bin/env python3
"""results/WK4_RECON/tools/wk4_view.py — R4: miary bootu NAUCZYCIELA w świecie world_wk4 (ramię odniesienia).

Importy / wywołania READ-ONLY: results/WK/tools/wk_judge.py c33c3ff8 (D6 sędzia bazowy 8ec0fcfb + świadek
ERRATUM-DMIN), results/WK3/tools/wk3_kadr.py 55875787 (cel w kadrze — definicja zamrożona WK-III),
results/WK2_RECON/tools/wk2_k.py 09e4b440 (wczytanie ulogu, bilans sił, okna orbity), r02/mti.quat_to_R.
NOWE: kontrola oporu z wiatrem ZNANYM Z PLIKU — w(t) = zero-order-hold LOGU PUBLIKACJI (wind_pub.jsonl:
dokładnie to, co dostał świat), D = a_h − (T/m)·t_h (wk3_gust), MNK D = −k(v − w_h) bez wyrazu wolnego,
okna fazy orbit; tolerancja ±20 % od 0.494. Przechył = acos(R[2,2]) wyłącznie w OKNACH EPIZODÓW
(episode_start.t0_sim … episode_end.sim; lekcja ANEKS_WK3-1 §3).

Użycie: wk4_view.py <boot_dir> <out.json>
"""
import bisect
import json
import math
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
for p in (ROOT, os.path.join(ROOT, "results", "WK2_RECON", "tools")):
    if p not in sys.path:
        sys.path.insert(0, p)
from r02.mti import quat_to_R  # noqa: E402
from wk2_k import G, load, orbit_windows  # noqa: E402

K_REF = 0.494


def iter_jsonl(p):
    with open(p) as f:
        for ln in f:
            try:
                yield json.loads(ln)
            except ValueError:
                continue


def episodes(boot):
    eps, cur = [], None
    for r in iter_jsonl(os.path.join(boot, "trace.jsonl")):
        if r.get("t") != "event":
            continue
        if r.get("ev") == "episode_start" and r.get("scenario_id"):
            cur = {"sid": r["scenario_id"], "t0": r["t0_sim"]}
        elif r.get("ev") == "episode_end" and cur is not None:
            cur["t1"] = r["sim"]; cur["refuse"] = r.get("refuse"); cur["breach"] = r.get("breach")
            eps.append(cur); cur = None
    return eps


def main():
    boot, outp = sys.argv[1], sys.argv[2]
    res = {"boot": os.path.relpath(boot, ROOT)}
    man = json.load(open(os.path.join(boot, "manifest.json")))
    res["wk4"] = man.get("wk4"); res["wk"] = man.get("wk")
    res["V2p"] = {e["scenario_id"]: {"valid": e.get("valid_V2p"), "dsim_dwall": e.get("dsim_dwall")}
                  for e in man.get("episodes", [])}
    # sędzia (wk_judge) i kadr (wk3_kadr) — wywołania CLI, wyniki obok
    jd = os.path.join(os.path.dirname(outp), f"judge_{os.path.basename(boot)}.json")
    subprocess.run([sys.executable, os.path.join(ROOT, "results/WK/tools/wk_judge.py"), jd, boot], check=True,
                   stdout=subprocess.DEVNULL)
    J = json.load(open(jd))
    res["D6"] = {e["scenario_id"]: {"pelny": e["judge_full"]["success_D6"], "swiadek": e["judge_swiadek"]["success_D6"],
                                    "powody": e["judge_swiadek"]["fail_reasons"],
                                    "d_min": e["judge_swiadek"]["d_min_m"], "t_entry": e["judge_swiadek"]["t_entry_s"],
                                    "frac": e["judge_swiadek"]["frac_band_6_10"],
                                    "sweep": e["judge_swiadek"]["sweep_deg"]} for e in J["epizody"]}
    res["breach_refuse"] = J["booty"]
    kd = os.path.join(os.path.dirname(outp), f"kadr_{os.path.basename(boot)}.json")
    subprocess.run([sys.executable, os.path.join(ROOT, "results/WK3/tools/wk3_kadr.py"), kd, boot], check=True,
                   stdout=subprocess.DEVNULL)
    res["kadr_plik"] = os.path.relpath(kd, ROOT)
    # ulog
    att, lp = load(os.path.join(boot, "boot.ulg"))
    ats = np.asarray(att[0], float)
    tilt_all = np.array([math.degrees(math.acos(max(-1.0, min(1.0, float(quat_to_R(q)[2, 2])))))
                         for q in att[1]])
    res["przechyl_epizody"] = {}
    for e in episodes(boot):
        m = (ats >= e["t0"] * 1e6) & (ats <= e["t1"] * 1e6)
        tl = tilt_all[m]
        res["przechyl_epizody"][e["sid"]] = [round(float(np.median(tl)), 2), round(float(np.percentile(tl, 95)), 2),
                                             round(float(tl.max()), 2)]
    # wiatr z logu publikacji (ZOH)
    pubs = [r for r in iter_jsonl(os.path.join(boot, "wind_pub.jsonl")) if isinstance(r, list)]
    pt = np.array([r[0] for r in pubs]); pw = np.array([[r[1], r[2], r[3]] for r in pubs])

    def w_at(t):
        i = np.clip(np.searchsorted(pt, t, side="right") - 1, 0, len(pt) - 1)
        return pw[i]
    T, V, D = [], [], []
    for lo, hi in orbit_windows(os.path.join(boot, "demo.jsonl")):
        msk = (lp["timestamp"] >= lo * 1e6) & (lp["timestamp"] <= hi * 1e6)
        for i in np.where(msk)[0]:
            j = min(max(bisect.bisect_left(ats, lp["timestamp"][i]), 0), len(ats) - 1)
            R = quat_to_R(att[1][j]); th = -R[:, 2]
            if th[2] > -0.5:
                continue
            Tm = (lp["az"][i] - G) / th[2]
            D.append(np.array([lp["ax"][i], lp["ay"][i]]) - Tm * th[:2])
            V.append(np.array([lp["vx"][i], lp["vy"][i]])); T.append(lp["timestamp"][i] / 1e6)
    T, V, D = np.array(T), np.array(V), np.array(D)
    W = w_at(T)
    Wned = np.stack([W[:, 1], W[:, 0]], 1)                       # ENU (x=E, y=N) → NED (N, E)
    rel = V - Wned
    k = float(-np.sum(D * rel) / np.sum(rel * rel))
    res["k_z_pliku"] = {"k": round(k, 4), "odch_od_0494": round(k / K_REF - 1, 4),
                        "w_tolerancji_20pct": bool(abs(k / K_REF - 1) <= 0.20), "n": int(len(T))}
    tN = np.hypot(*(V - Wned + D / K_REF).T)
    res["residuum_wiatru_odtw_vs_plik_p50_p95"] = [round(float(np.median(tN)), 3),
                                                   round(float(np.percentile(tN, 95)), 3)]
    json.dump(res, open(outp, "w"), indent=1, ensure_ascii=False)
    print(json.dumps({k_: v for k_, v in res.items() if k_ not in ("wk", "wk4")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
