#!/usr/bin/env python3
"""results/NAD3/tools/nad3_s2_geom.py — geometria nominałów smoke NAD3 (PROMPT_NAD3_S2 §3 „Geometria”; PRE_NAD3 §6 S2).

Per epizod bootu nominalnego (trace.jsonl: tk, gt, event; gt_intruder.jsonl; manifest NAD3; wyniki_nad3.json analizatora):
  - okno misji = ticki tk epizodu z fazą ∈ {approach, hold, orbit}, bez zejścia; czas okna [s];
  - r_max GT = max |GT_xy − gt_home| (kanon B2) w oknie misji; promień intruza max (gt_intruder, pole ned) w oknie misji;
    różnica dron − intruz;
  - promień intruza na torze ZADANYM (bench/scenarios.position_at z manifestu NAD3) w oknie nominału oraz w oknie cięcia
    [0, t_entry + 30 + 110.5] s od startu epizodu (t_entry z nominału — pierwszy tick w paśmie; uwaga promptu §3);
  - track = średnia trk_valid w oknie, pasmo = udział ticków z |GT − intruz| ∈ [6, 10] m (definicje D1 z nad2_analyze),
    B1–B5 z analizatora;
  - kryterium nominału: B1–B5 ok ∧ track ≥ 0.85 ∧ pasmo ≥ 0.85; bramka geometrii: r_max ≤ 19.5 m.
Wyjście: <boot>/geometria_nad3.json. Użycie: nad3_s2_geom.py <katalog_bootu> [...]
"""
import json
import math
import os
import sys

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, ROOT)
from bench import scenarios as S

MISJA = ("approach", "hold", "orbit")
BRAMKA_R = 19.5
FRAC_MIN, BAND = 0.85, (6.0, 10.0)
MAN = os.path.join(ROOT, "results/NAD3/s1/scenario_manifest_nad3.json")
T_INJ, T_CONT = 30.0, 110.5


def jl(p, typ=None):
    out = []
    if not os.path.exists(p):
        return out
    for l in open(p):
        if typ is not None and f'"{typ}"' not in l:
            continue
        try:
            r = json.loads(l)
        except ValueError:
            continue
        if typ is None or r.get("t") == typ:
            out.append(r)
    return out


def zadany_max(ep, t0, t1, dt=0.01):
    n = int(max(0.0, t1 - t0) / dt) + 1
    return max(math.hypot(*S.position_at(ep, t0 + k * dt)[:2]) for k in range(n))


def geometria(d):
    man = {e["scenario_id"]: e for e in json.load(open(MAN))["episodes"]}
    tr = os.path.join(d, "trace.jsonl")
    ev, tk, gt = jl(tr, "event"), jl(tr, "tk"), sorted(jl(tr, "gt"), key=lambda r: r["sim"])
    armed = next((e for e in ev if e.get("ev") == "armed"), None)
    gx0, gy0 = armed["gt_home"] if armed else (0.0, 0.0)
    gt_t = np.array([g["sim"] for g in gt]); gt_n = np.array([g["y"] for g in gt]); gt_e = np.array([g["x"] for g in gt])
    gi = jl(os.path.join(d, "gt_intruder.jsonl"))
    try:
        wyn = {o["episode_id"]: o for o in json.load(open(os.path.join(d, "wyniki_nad3.json")))["epizody"]}
    except (OSError, ValueError, KeyError):
        wyn = {}
    out = {"boot": os.path.basename(d.rstrip("/")), "epizody": []}
    for st in [e for e in ev if e.get("ev") == "episode_start"]:
        ep, scen = st["episode_id"], st["scenario_id"]
        ms = [r for r in tk if r.get("ep") == ep and r.get("phase") in MISJA and not r.get("desc")]
        o = {"episode_id": ep, "scenario_id": scen}
        if not ms:
            o["blad"] = "brak ticków misji"
            out["epizody"].append(o)
            continue
        t0, t1 = ms[0]["sim"], ms[-1]["sim"]
        rg = [math.hypot(g["x"] - gx0, g["y"] - gy0) for g in gt if t0 <= g["sim"] <= t1]
        ri = [math.hypot(r["ned"][0], r["ned"][1]) for r in gi if r.get("episode_id") == ep and t0 <= r["t_sim"] <= t1]
        ft = sum(bool(r.get("trk_valid")) for r in ms) / len(ms)
        dg = []
        for r in ms:                                                  # GT(t) NED interpolowane jak nad2_analyze (D1)
            if r.get("intr") is None:
                continue
            gn, ge = np.interp(r["sim"], gt_t, gt_n), np.interp(r["sim"], gt_t, gt_e)
            dg.append(math.hypot(gn - r["intr"][0], ge - r["intr"][1]))
        fp = sum(BAND[0] <= x <= BAND[1] for x in dg) / len(dg) if dg else 0.0
        t_ep0 = st["sim"]
        t_entry = next((r["sim"] for r in ms if r.get("d") is not None and BAND[0] <= r["d"] <= BAND[1]), None)
        e_m = man.get(scen)
        w = wyn.get(ep, {})
        o.update(okno_misji_s=round(t1 - t0, 2), okno_od_startu_s=[round(t0 - t_ep0, 2), round(t1 - t_ep0, 2)],
                 r_max_gt=round(max(rg), 3) if rg else None, r_max_intruz=round(max(ri), 3) if ri else None,
                 frac_track=round(ft, 3), frac_pasmo=round(fp, 3),
                 B={k: (w.get(k) or {}).get("ok") for k in ("B1", "B2", "B3", "B4", "B5")})
        o["roznica_dron_intruz"] = round(o["r_max_gt"] - o["r_max_intruz"], 3) if rg and ri else None
        if e_m is not None:
            o["intruz_zadany_max_okno_nominalu"] = round(zadany_max(e_m, max(0.0, t0 - t_ep0), t1 - t_ep0), 4)
            if t_entry is not None:
                o["okno_ciecia_od_startu_s"] = [0.0, round(t_entry - t_ep0 + T_INJ + T_CONT, 2)]
                o["intruz_zadany_max_okno_ciecia"] = round(zadany_max(e_m, 0.0, t_entry - t_ep0 + T_INJ + T_CONT), 4)
        o["kryterium_nominalu"] = all(v is True for v in o["B"].values()) and ft >= FRAC_MIN and fp >= FRAC_MIN
        o["bramka_r"] = o["r_max_gt"] is not None and o["r_max_gt"] <= BRAMKA_R
        out["epizody"].append(o)
    out["bramka_ok"] = bool(out["epizody"]) and all(e.get("bramka_r") for e in out["epizody"])
    out["nominaly_niespelnione"] = sum(not e.get("kryterium_nominalu") for e in out["epizody"])
    json.dump(out, open(os.path.join(d, "geometria_nad3.json"), "w"), ensure_ascii=False, indent=1)
    return out


if __name__ == "__main__":
    for d in sys.argv[1:]:
        g = geometria(d)
        print(json.dumps({"boot": g["boot"], "bramka_ok": g["bramka_ok"], "niespelnione": g["nominaly_niespelnione"],
                          "r_max": [(e["scenario_id"], e.get("r_max_gt")) for e in g["epizody"]]}, ensure_ascii=False))
