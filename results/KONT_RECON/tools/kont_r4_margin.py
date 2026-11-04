#!/usr/bin/env python3
"""results/KONT_RECON/tools/kont_r4_margin.py — R4 PROMPT_KONT_S0: r w fazie orbity, margines m i budżet T_cont.

r = |GT_xy| z trace.jsonl (środek strefy = home ≈ świat, T_home≈0 w B1-bis; rozjazd r_GT−r_EKF liczony obok).
Faza orbity: od t0_sim+t_entry do episode_end. Epizod bez t_entry nie ma orbity: liczony osobno, poza tabelą.
m = R_E − d_stop − r_max(scenariusz), R_E i D_STOP importem z r03/config (FROZEN 4c440e42).
T_cont(scenariusz, krzywa) = pierwsze t z eps(t) > m, krzywe z r3_eps.json WYŁĄCZNIE w locie (t ≤ t_ground);
brak przekroczenia ⇒ cenzura „>t_end" (bierzemy koniec okna lotu, to dolne oszacowanie, nie pomiar).
Wyjście: results/KONT_RECON/r4_margin.json
"""
import glob
import json
import math
import os
import statistics as st
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, ROOT)
from r03.config import R_E, D_STOP

WALL_S = 4.0     # zmierzone: native_wall.json (nav 14→12 12/12 K2, xy_valid=False 4.0 s)


def boots():
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, "results", "FANTOM", "camp", "r*_V2*", "trace.jsonl"))):
        out.append(("FANTOM_S2", p))
    for sub, tag in (("PERC2/s2", "PERC2_S2"), ("SKAN2/s1", "SKAN2_S1")):
        for p in sorted(glob.glob(os.path.join(ROOT, "results", sub, "b*", "trace.jsonl"))):
            out.append((tag, p))
    return out


def episodes(tag, path):
    ev, gt, ekf = [], [], []
    for l in open(path):
        try:
            r = json.loads(l)
        except Exception:
            continue
        k = r.get("t")
        if k == "event":
            ev.append(r)
        elif k == "gt":
            gt.append((r["sim"], r["x"], r["y"]))
        elif k == "ekf":
            ekf.append((r["mono"], r["x"], r["y"]))
    res = []
    start = None
    for e in ev:
        if e["ev"] == "episode_start":
            start = e
        elif e["ev"] == "episode_end" and start is not None:
            te = e.get("t_entry")
            row = {"zrodlo": tag, "boot": os.path.basename(os.path.dirname(path)), "scenario_id": start["scenario_id"],
                   "t_entry": te, "refuse": e.get("refuse"), "breach": e.get("breach")}
            if te is None:
                row["orbita"] = False
            else:
                a, b = start["t0_sim"] + te, e["sim"]
                rs = sorted(math.hypot(x, y) for s, x, y in gt if a <= s <= b)
                row.update({"orbita": True, "n": len(rs), "r_p50": round(st.median(rs), 2),
                            "r_p95": round(rs[int(0.95 * (len(rs) - 1))], 2), "r_max": round(rs[-1], 2)})
            res.append(row)
            start = None
    return res


def cross(path):
    """Mediana |r_GT−r_EKF| po sparowaniu po mono — rozjazd środka strefy GT vs osłona."""
    gt, ekf = [], []
    for l in open(path):
        try:
            r = json.loads(l)
        except Exception:
            continue
        if r.get("t") == "gt":
            gt.append((r["mono"], r["x"], r["y"]))
        elif r.get("t") == "ekf":
            ekf.append((r["mono"], r["x"], r["y"]))
    i, d = 0, []
    for t, n, e in ekf[::40]:
        while i + 1 < len(gt) and gt[i + 1][0] <= t:
            i += 1
        d.append(abs(math.hypot(n, e) - math.hypot(gt[i][1], gt[i][2])))
    return round(st.median(d), 3)


def t_cont(curve, tg, m):
    """Pierwsze t z eps>m; None gdy brak (cenzura, koniec okna lotu zwracany obok)."""
    fl = [(t, d) for t, d in curve if tg is None or t <= tg]
    for t, d in fl:
        if d > m:
            return t, False
    return fl[-1][0], True


def main():
    eps = json.load(open(os.path.join(ROOT, "results", "KONT_RECON", "r3_eps.json")))["runs"]
    bs = boots()
    rows = []
    for tag, p in bs:
        rows += episodes(tag, p)
    orb = [r for r in rows if r["orbita"]]
    scen = {}
    for r in orb:
        scen.setdefault(r["scenario_id"], []).append(r)
    tab = {s: {"n_ep": len(v), "r_p50": round(st.median(x["r_p50"] for x in v), 2),
               "r_max": max(x["r_max"] for x in v),
               "m": round(R_E - D_STOP - max(x["r_max"] for x in v), 2)} for s, v in sorted(scen.items())}
    ms = [v["m"] for v in tab.values()]
    # krzywe: ruch poleceniem (proxy zadania); hover i epizody zejścia osobno
    wybor = {"f5_corner(naj.zastepnik)": ["flights/f5_corner"], "f3_straight": ["flights/f3_straight"],
             "f4_straight120(najgorszy)": ["flights/f4_straight120"], "hover_f2": ["flights/f2_hover"],
             "c1_corner(episode)": ["episode/c1_corner"]}
    byrun = {r["run"]: r for r in eps}
    # krzywa p50 po trzech lotach z ruchem poleceniem, w oknie wspólnym lotu
    moving = ["flights/f3_straight", "flights/f4_straight120", "flights/f5_corner"]
    tg_common = min(byrun[r]["t_ground_s"] for r in moving)
    n_c = int(tg_common / 0.25) + 1
    p50_curve = [[k * 0.25, st.median(byrun[r]["curve"][k][1] for r in moving)] for k in range(n_c)]
    byrun["p50_f3f4f5"] = {"curve": p50_curve, "t_ground_s": tg_common}
    wybor["p50_ruch(f3,f4,f5)"] = ["p50_f3f4f5"]
    wyn = {}
    for nazwa, rr in wybor.items():
        c = byrun[rr[0]]
        ts, cens = [], 0
        ts_m5 = []
        for s, v in tab.items():
            t, ce = t_cont(c["curve"], c["t_ground_s"], v["m"])
            ts.append(t); cens += int(ce)
            ts_m5.append(t_cont(c["curve"], c["t_ground_s"], v["m"] + 5.0)[0])
        q = sorted(ts)
        wyn[nazwa] = {"t_ground_s": c["t_ground_s"], "T_cont_p10": q[int(0.1 * (len(q) - 1))], "T_cont_p50": st.median(q),
                      "T_cont_min": q[0], "T_cont_max": q[-1], "n_scen": len(q), "n_cenzura": cens,
                      "T_cont_p50_m_plus5": st.median(ts_m5),
                      "T_cont_eff_p50_ze_sciana": min(st.median(q), WALL_S)}
    # ε(t) na fazie ważnej (t≤4 s, offboard żywy): koperta po ruchu poleceniem
    env = {str(k): {"p50": round(st.median(byrun[r]["eps_at"][str(k)] for r in moving), 2),
                    "max": round(max(byrun[r]["eps_at"][str(k)] for r in moving), 2)} for k in (1, 2, 3, 4)}
    k2 = [r for r in eps if r["profile"] == "k2_orbita_D5"]
    k2env = {str(k): {"p50": round(st.median(r["eps_at"][str(k)] for r in k2), 2),
                      "max": round(max(r["eps_at"][str(k)] for r in k2), 2)} for k in (1, 2, 3, 4, 5, 6, 8)}
    k2_d10 = sorted(r["max_eps_w_locie"] for r in k2)
    # ogon zejścia: przyrost eps od 4 s do przyziemienia (K2 realne, c1 najgorszy epizod B1-bis)
    ogon = {"K2_p50": round(st.median(r["max_eps_w_locie"] - r["eps_at"]["4"] for r in k2), 2),
            "K2_max": round(max(r["max_eps_w_locie"] - r["eps_at"]["4"] for r in k2), 2),
            "c1_corner": round(byrun["episode/c1_corner"]["max_eps_w_locie"] - byrun["episode/c1_corner"]["eps_at"]["4"], 2)}
    scen_ponad_route = sum(1 for v in tab.values() if v["r_max"] > 19.9)
    out = {"R_E": R_E, "D_STOP": D_STOP, "wall_s": WALL_S, "n_boot": len(bs), "n_ep": len(rows), "n_ep_orbita": len(orb),
           "n_ep_bez_orbity": len(rows) - len(orb), "rozjazd_rGT_rEKF_med": [cross(p) for _, p in bs[:3]],
           "r_max_po_scen": sorted(v["r_max"] for v in tab.values()),
           "m": {"p10": sorted(ms)[int(0.1 * (len(ms) - 1))], "p50": st.median(ms), "min": min(ms), "max": max(ms)},
           "tabela_scenariuszy": tab, "T_cont": wyn, "eps_poleceniem_t_le_4": env, "eps_K2_orbita_D5": k2env,
           "ogon_D5_od_4s": ogon, "n_scen_rmax_ponad_R_route_prim": scen_ponad_route,
           "eps_K2_max_w_oknie": {"p50": st.median(k2_d10), "max": k2_d10[-1]}, "epizody": rows}
    json.dump(out, open(os.path.join(ROOT, "results", "KONT_RECON", "r4_margin.json"), "w"), ensure_ascii=False, indent=0)
    print({k: out[k] for k in ("n_boot", "n_ep", "n_ep_orbita", "n_ep_bez_orbity", "rozjazd_rGT_rEKF_med", "m")})
    print("r_max po scen", out["r_max_po_scen"])
    for s, v in tab.items():
        print(s, v)
    print(json.dumps(wyn, ensure_ascii=False, indent=0))
    print(env); print(k2env); print(out["eps_K2_max_w_oknie"])


main()
