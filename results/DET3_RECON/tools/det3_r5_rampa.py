#!/usr/bin/env python3
"""results/DET3_RECON/tools/det3_r5_rampa.py — R5 wariant A: czy detektor widzi cel W RAMPIE skanu
(poza admisją), tj. czy „detekcja jako wskazówka kierunku" ma sygnał na obecnej siatce.

Dane: FANTOM S2 ramię V2 (48 epizodów, indeks POSCIG_RECON — Episode READ-ONLY), percep_feed.jsonl
(per klatka: box top-1 det_v2, own_q, fresh). Etykieta: det_labels.BootGeo 8f7430cd (READ-ONLY),
on-target jak transit_r1.on_target (= det_replay.py:149-157). Okno: [t0, pierwsza klatka fresh)
— przed akwizycją. Rampa = |yaw_rate| > 15 °/s między kolejnymi klatkami (STARE_DPS transit_r1:42).
Miary: P(top-1 na celu | cel w kadrze) w rampie vs w stare, per Z; per epizod: pierwsza klatka
on-target w rampie vs t pierwszej fresh (zysk czasu wskazówki, brutto — bez obrotu i admisji).
Wyjście: r5_rampa.json + wydruk.
"""
import json
import math
import os
import sys

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "results/POSCIG_RECON/tools"))
sys.path.insert(0, os.path.join(ROOT, "results/DET_RECON/tools"))
import poscig_recon as P                           # noqa: E402  READ-ONLY
from det_labels import BootGeo                      # noqa: E402  READ-ONLY 8f7430cd

STARE_DPS = 15.0


def yaw_of(q):
    w, x, y, z = q
    return math.degrees(math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)))


def wrap(a):
    return (a + 180.0) % 360.0 - 180.0


def main():
    keys = sorted(k for k in P._INDEX if k.startswith("FANTOM_S2:V2:"))
    agg = {"ramp": {}, "stare": {}}
    eps = []
    geo_cache = {}
    for k in keys:
        rec = P._INDEX[k]
        sid = rec["scenario_id"]
        epi = P.Episode("FANTOM_S2", "V2", sid)
        d = os.path.join(ROOT, epi.dir)
        if d not in geo_cache:
            geo_cache[d] = BootGeo(d, 1.0, 60.0)
        geo = geo_cache[d]
        pf = [r for r in P.iter_jsonl(os.path.join(d, "percep_feed.jsonl"))
              if r.get("t_frame") is not None and r.get("own_q") and epi.t0 <= r["t_frame"] <= epi.t_end_demo]
        pf.sort(key=lambda r: r["t_frame"])
        t_fresh = next((r["t_frame"] for r in pf if r.get("fresh")), None)
        first_ramp_hit = first_stare_hit = None
        n = {"ramp_fov": 0, "ramp_on": 0, "stare_fov": 0, "stare_on": 0}
        for a, b in zip(pf, pf[1:]):
            if t_fresh is not None and b["t_frame"] >= t_fresh:
                break
            dt = b["t_frame"] - a["t_frame"]
            if dt <= 0:
                continue
            rate = abs(wrap(yaw_of(b["own_q"]) - yaw_of(a["own_q"]))) / dt
            lab = geo.label(b["t_frame"])
            if lab.get("flag") != "OK":
                continue
            Z = lab["uvZ"][2]
            bb = b.get("box")
            on = bool(bb) and abs(bb[0] * 640 - lab["box"][0]) <= lab["box"][2] / 2 \
                and abs(bb[1] * 480 - lab["box"][1]) <= lab["box"][3] / 2
            kind = "ramp" if rate > STARE_DPS else "stare"
            n[f"{kind}_fov"] += 1
            n[f"{kind}_on"] += int(on)
            zb = f"{int(Z // 3) * 3}-{int(Z // 3) * 3 + 3}"
            c = agg[kind].setdefault(zb, [0, 0])
            c[0] += 1
            c[1] += int(on)
            if on and kind == "ramp" and first_ramp_hit is None:
                first_ramp_hit = round(b["t_frame"] - epi.t0, 2)
            if on and kind == "stare" and first_stare_hit is None:
                first_stare_hit = round(b["t_frame"] - epi.t0, 2)
        eps.append({"sid": sid, "success_D6": rec["success_D6"],
                    "t_first_fresh_rel": round(t_fresh - epi.t0, 2) if t_fresh else None,
                    "first_ramp_hit_rel": first_ramp_hit, "first_stare_hit_rel": first_stare_hit, **n})
    tot = {k: [sum(e[f"{k}_fov"] for e in eps), sum(e[f"{k}_on"] for e in eps)] for k in ("ramp", "stare")}
    gain = [e["t_first_fresh_rel"] - e["first_ramp_hit_rel"] for e in eps
            if e["first_ramp_hit_rel"] is not None and e["t_first_fresh_rel"] is not None]
    t6 = {"c08_s03", "c08_s04", "c10_s02", "c11_s02", "c11_s03", "c11_s04"}
    out = {"n_episodes": len(eps), "przed_akwizycja": tot, "per_Z": agg,
           "ep_z_trafieniem_w_rampie_przed_fresh": sum(1 for e in eps if e["first_ramp_hit_rel"] is not None),
           "zysk_brutto_s_sorted": sorted(round(g, 2) for g in gain),
           "T6": [e for e in eps if e["sid"] in t6], "epizody": eps}
    json.dump(out, open(sys.argv[1], "w"), indent=1)
    print(json.dumps({k: out[k] for k in ("n_episodes", "przed_akwizycja", "per_Z",
                                          "ep_z_trafieniem_w_rampie_przed_fresh", "zysk_brutto_s_sorted")}, indent=1))
    for e in out["T6"]:
        print(e)


if __name__ == "__main__":
    main()
