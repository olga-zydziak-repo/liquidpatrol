#!/usr/bin/env python3
"""results/WABIK3_RECON/tools/wabik3_recon.py — recon WABIK-III „tor i geometria zbliżenia"
(PROMPT_WABIK3_S0; 0 bootów). NOWY plik; zamrożone WYŁĄCZNIE importem READ-ONLY:
  results/WABIK2/tools/wabik_sig2.py a8397cb4 — load_s2/load_null/feed_rows/episodes_of/evaluate,
    progi FREEZE_WABIK (V_MOVE 0.30 / V_RAD_MAX 0.30 / DH_MIN_FLOOR 5.0 / R_ZONE 18 / T_FLAG 12 / WIN 1.0);
  bench.scenarios.position_at — GT celu z manifestu (R5);
  r02/mti.py FX — rachunek pikselowy (R4).
Bench = 126 lotów: 11 S2 (6 TP / 3 FP / 2 ORB) + 115 NULL (litera wabik_sig2.load_null).
Kryterium WABIK-II (s1_tabela, verbatim): TP ≥ 5/6 w ≤ 15 s ∧ FP 0/3 ∧ ORB odwołane 2/2 ∧ NULL_final ≤ 13/115.

Tryby: anchor | r2 | r3 | r4 | r5 | all  → JSON-y w results/WABIK3_RECON/.
"""
import bisect
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(ROOT, "results", "WABIK3_RECON")
for p in (ROOT, os.path.join(ROOT, "results", "WABIK2", "tools")):
    if p not in sys.path:
        sys.path.insert(0, p)
import wabik_sig2 as W2  # noqa: E402  (a8397cb4, READ-ONLY)
from bench import scenarios as S  # noqa: E402

V_MOVE, V_RAD_MAX, FLOOR, R_ZONE, T_FLAG, WIN = (W2.V_MOVE, W2.V_RAD_MAX, W2.DH_MIN_FLOOR,
                                                  W2.R_ZONE, W2.T_FLAG, W2.WIN)
BENCH_MAN = {e["scenario_id"]: e for e in
             json.load(open(os.path.join(ROOT, "results", "BENCH", "scenario_manifest.json")))["episodes"]}
S2_MAN = {e["scenario_id"]: e for e in
          json.load(open(os.path.join(ROOT, "results", "WABIK", "wabik_manifest_s2.json")))["episodes"]}


# ------------------------------------------------------------------ ładowanie benchu
def load_bench():
    """Lista epizodów: dict(id, rodz TP/FP/ORB/NULL, klasa, dir, sid, t0, t1, feed rows, demo rows, v)."""
    eps = []
    for boot, sid, rodz in W2.S2_EPS:
        d = os.path.join(ROOT, "results", "WABIK", "s2", boot)
        e = next(x for x in W2.episodes_of(d) if x["sid"] == sid)
        eps.append(dict(id=f"S2:{boot}:{sid}", rodz=rodz, dir=d, sid=sid, t0=e["t0"], t1=e["t1"],
                        man=S2_MAN[sid]))
    camps = [("DET_S4", "results/DET/camp"), ("AKW_S3", "results/AKW/camp"),
             ("FANTOM_S2", "results/FANTOM/camp")]
    for camp, base in camps:                      # pętla 1:1 z wabik_sig2.load_null
        for i in range(1, 13):
            d = os.path.join(ROOT, base, f"r{i}_V2")
            pf = os.path.join(d, "percep_feed.jsonl")
            if not os.path.isdir(d) or not os.path.exists(pf):
                continue
            for e in W2.episodes_of(d):
                rows = W2.feed_rows(pf, e["t0"], e["t1"])
                if len(rows) >= 50:
                    eps.append(dict(id=f"{camp}:r{i}:{e['sid']}", rodz="NULL", dir=d, sid=e["sid"],
                                    t0=e["t0"], t1=e["t1"], man=BENCH_MAN[e["sid"]], _rows=rows))
    feeds = {}
    for e in eps:
        if "_rows" in e:
            e["rows"] = e.pop("_rows")
        else:
            e["rows"] = W2.feed_rows(os.path.join(e["dir"], "percep_feed.jsonl"), e["t0"], e["t1"])
        e["v"] = e["man"]["cell"]["v_intr"]
        e["t_first"] = e["rows"][0][0] if e["rows"] else e["t0"]   # zegar kryterium = 1. klatka trk (v1)
        e["klasa"] = e["rodz"] if e["rodz"] != "NULL" else f"NULL_v{e['v']:g}"
        feeds.setdefault(e["dir"], None)
    # demo.jsonl per boot (trk_vel_ned = LITERA klienta feedu, nie refit)
    demo_by_dir = {}
    for d in feeds:
        rows = []
        for r in W2.iter_jsonl(os.path.join(d, "demo.jsonl")):
            if r.get("track_valid") and r.get("trk_pos_ned") and r.get("trk_vel_ned"):
                rows.append((r["t_sim"], r["trk_pos_ned"][:2], r["trk_vel_ned"][:2],
                             r["own_pos_ned"][:2], r["own_vel_ned"][:2], r.get("scenario_id")))
        rows.sort(key=lambda x: x[0])
        demo_by_dir[d] = rows
    for e in eps:
        dr = demo_by_dir[e["dir"]]
        lo = bisect.bisect_left([x[0] for x in dr], e["t0"])
        e["demo"] = [x for x in dr[lo:] if x[0] <= e["t1"] and x[5] == e["sid"]]
    assert sum(1 for e in eps if e["rodz"] == "NULL") == 115, "NULL ≠ 115"
    return eps


def kryterium(res, zegar_ok=15.0):
    """res: {id: wynik} z polami ever/final/t_flag. Liczy kryterium WABIK-II."""
    tp = sum(1 for k, r in res.items() if r["rodz"] == "TP" and r["ever"] and r["t_flag"] is not None
             and r["t_flag"] <= zegar_ok)
    fp = sum(1 for r in res.values() if r["rodz"] == "FP" and r["ever"])
    orb = sum(1 for r in res.values() if r["rodz"] == "ORB" and not r["final"])
    ne = sum(1 for r in res.values() if r["rodz"] == "NULL" and r["ever"])
    nf = sum(1 for r in res.values() if r["rodz"] == "NULL" and r["final"])
    nf05 = sum(1 for r in res.values() if r["rodz"] == "NULL" and r["final"] and r["v"] == 0.5)
    nf10 = sum(1 for r in res.values() if r["rodz"] == "NULL" and r["final"] and r["v"] == 1.0)
    tpf = sum(1 for r in res.values() if r["rodz"] == "TP" and r["final"])   # informacyjnie (kryterium
    return {"TP_le15": tp, "TP_final": tpf,                                  # WABIK-II go nie liczy)
            "FP_flags": fp, "ORB_odwolane": orb, "NULL_ever": ne, "NULL_final": nf,
            "NULL_final_v05": nf05, "NULL_final_v10": nf10,
            "dopuszczony": tp >= 5 and fp == 0 and orb == 2 and nf <= 13}


# ------------------------------------------------------------------ silnik reguły (streak + odwołanie)
def streak_rule(ts, W, dh_min, T, revoke_extra=None, t0=None):
    """Streak ciągły ≥T (zero tolerancji, jak baza(i)); odwołanie: dh_min<FLOOR po fladze
    (litera FREEZE) LUB revoke_extra[i] (opcjonalnie). Zegar od pierwszej próbki."""
    t_flag = t_rev = None
    s0 = None
    for i in range(len(ts)):
        if t_flag is None:
            if W[i]:
                if s0 is None:
                    s0 = ts[i]
                if ts[i] - s0 >= T:
                    t_flag = ts[i]
            else:
                s0 = None
        if t_flag is not None and t_rev is None and (dh_min[i] < FLOOR or
                                                     (revoke_extra is not None and revoke_extra[i])):
            t_rev = ts[i]
    t0 = t0 if t0 is not None else (ts[0] if len(ts) else None)
    return {"ever": t_flag is not None, "final": t_flag is not None and t_rev is None,
            "t_flag": round(t_flag - t0, 2) if t_flag is not None else None,
            "t_rev": round(t_rev - t0, 2) if t_rev is not None else None}


def frac_rule(ts, A, M, dh_min, T, phi, mv_min=0.8, t0=None):
    """Flaga, gdy w PEŁNYM oknie T: frac(atak) ≤ phi ∧ frac(ruch∧strefa∧podłoga) ≥ mv_min."""
    t_flag = t_rev = None
    j = 0
    ca = cm = 0
    for i in range(len(ts)):
        ca += A[i]; cm += M[i]
        while ts[i] - ts[j] > T:
            ca -= A[j]; cm -= M[j]; j += 1
        n = i - j + 1
        if t_flag is None and ts[i] - ts[j] >= T - 0.15 and n >= 10:
            if ca / n <= phi and cm / n >= mv_min:
                t_flag = ts[i]
        if t_flag is not None and t_rev is None and dh_min[i] < FLOOR:
            t_rev = ts[i]
    t0 = t0 if t0 is not None else (ts[0] if len(ts) else None)
    return {"ever": t_flag is not None, "final": t_flag is not None and t_rev is None,
            "t_flag": round(t_flag - t0, 2) if t_flag is not None else None,
            "t_rev": round(t_rev - t0, 2) if t_rev is not None else None}


# ------------------------------------------------------------------ R2: DCPA/TCPA
def dcpa_tcpa(p, v):
    vv = v[:, 0] ** 2 + v[:, 1] ** 2
    with np.errstate(divide="ignore", invalid="ignore"):
        tc = np.where(vv > 1e-4, -(p[:, 0] * v[:, 0] + p[:, 1] * v[:, 1]) / vv, np.inf)
    tcp = np.clip(np.where(np.isfinite(tc), tc, 0.0), 0.0, None)
    d = np.hypot(p[:, 0] + v[:, 0] * tcp, p[:, 1] + v[:, 1] * tcp)
    return d, tc


def trailing_mean(ts, x, w):
    out = np.empty_like(x)
    j = 0
    c = 0.0
    for i in range(len(ts)):
        c += x[i]
        while ts[i] - ts[j] > w:
            c -= x[j]; j += 1
        out[i] = c / (i - j + 1)
    return out


def r2_arrays(e):
    D = e["demo"]
    if len(D) < 10:
        return None
    ts = np.array([x[0] for x in D])
    p = np.array([x[1] for x in D]); v = np.array([x[2] for x in D])
    o = np.array([x[3] for x in D]); ov = np.array([x[4] for x in D])
    dh = np.hypot(p[:, 0], p[:, 1])
    dh_min = np.minimum.accumulate(dh)
    spd = np.hypot(v[:, 0], v[:, 1])
    dH, tH = dcpa_tcpa(p, v)
    dD, tD = dcpa_tcpa(p - o, v - ov)
    return dict(ts=ts, dh=dh, dh_min=dh_min, spd=spd,
                dH=trailing_mean(ts, dH, 1.0), tH=tH, dD=trailing_mean(ts, dD, 1.0), tD=tD,
                dH_raw=dH)


def r2(eps):
    A = {e["id"]: r2_arrays(e) for e in eps}
    configs = []
    for ref in ("home", "dron"):
        for H in (None, 10.0):
            for R in (3.0, 5.0, 7.0, 9.0):
                for T in (4.0, 6.0, 8.0, 10.0, 12.0):
                    for rev in ("floor", "floor+atak"):
                        configs.append(dict(rodz="streak", ref=ref, H=H, R=R, T=T, rev=rev))
    for R in (3.0, 5.0, 7.0, 9.0):
        for T in (4.0, 6.0, 8.0, 10.0):
            for phi in (0.0, 0.1, 0.2):
                configs.append(dict(rodz="frac", ref="home", H=None, R=R, T=T, phi=phi, rev="floor"))
    table = []
    for c in configs:
        res = {}
        for e in eps:
            a = A[e["id"]]
            if a is None:
                res[e["id"]] = dict(rodz=e["rodz"], v=e["v"], ever=False, final=False, t_flag=None, t_rev=None)
                continue
            d, tc = (a["dH"], a["tH"]) if c["ref"] == "home" else (a["dD"], a["tD"])
            hor = np.inf if c["H"] is None else c["H"]
            atak = (tc > 0) & (tc < hor) & (d < c["R"])
            mv = (a["spd"] > V_MOVE) & (a["dh"] < R_ZONE) & (a["dh_min"] >= FLOOR)
            if c["rodz"] == "streak":
                Wm = mv & ~atak
                rx = None
                if c["rev"] == "floor+atak":
                    # odwołanie atakiem: ≥1 s ciągłego „atak" po fladze
                    rx = np.zeros(len(atak), bool); s0 = None
                    for i in range(len(atak)):
                        if atak[i]:
                            s0 = a["ts"][i] if s0 is None else s0
                            rx[i] = a["ts"][i] - s0 >= 1.0
                        else:
                            s0 = None
                r = streak_rule(a["ts"], Wm, a["dh_min"], c["T"], rx, t0=e["t_first"])
            else:
                r = frac_rule(a["ts"], atak.astype(int), mv.astype(int), a["dh_min"], c["T"], c["phi"],
                              t0=e["t_first"])
            r.update(rodz=e["rodz"], v=e["v"])
            res[e["id"]] = r
        k = kryterium(res)
        k["cfg"] = c
        k["tp_czasy"] = {i.split(":")[-1]: res[i]["t_flag"] for i in res if res[i]["rodz"] == "TP"}
        k["fp_ever"] = [i.split(":")[-1] for i in res if res[i]["rodz"] == "FP" and res[i]["ever"]]
        k["orb"] = {i.split(":")[-1]: (res[i]["ever"], res[i]["final"]) for i in res if res[i]["rodz"] == "ORB"}
        table.append(k)
    # cechy per klasa (rozkłady): DCPA_home wygładzona (mediana epizodu), frakcja ataku, t do pierwszego
    # DCPA_min_w_oknie(4 s) > R
    feats = {}
    for e in eps:
        a = A[e["id"]]
        if a is None:
            continue
        atak5 = (a["tH"] > 0) & (a["dH"] < 5.0)
        tf = {}
        for R in (5.0, 7.0):
            tfirst = None
            for i in range(len(a["ts"])):
                j = bisect.bisect_left(a["ts"], a["ts"][i] - 4.0)
                if a["ts"][i] - a["ts"][j] >= 3.85 and a["dH"][j:i + 1].min() > R:
                    tfirst = round(float(a["ts"][i] - a["ts"][0]), 2)
                    break
            tf[f"R{R:g}"] = tfirst
        feats[e["id"]] = dict(klasa=e["klasa"], dcpa_home_med=round(float(np.median(a["dH"])), 2),
                              dcpa_dron_med=round(float(np.median(a["dD"])), 2),
                              frac_atak_R5=round(float(atak5.mean()), 3), t_do_dcpa_min4s_gt=tf)
    return table, feats


def pareto(table):
    ok = [r for r in table if r["FP_flags"] == 0 and r["ORB_odwolane"] == 2]
    front = []
    for r in ok:
        dom = any((q["TP_le15"] >= r["TP_le15"] and q["NULL_final"] <= r["NULL_final"]) and
                  (q["TP_le15"] > r["TP_le15"] or q["NULL_final"] < r["NULL_final"]) for q in ok)
        if not dom:
            front.append(r)
    pts = sorted({(r["TP_le15"], r["NULL_final"]) for r in front})
    return pts, front


# ------------------------------------------------------------------ R3: estymatory v_rad
def est_stream(rows, est):
    """Zwraca (ts, speed, v_rad, dh_min) dla klatek z policzalnym oknem; est = nazwa."""
    if est.startswith("jump"):
        J = float(est.split("_")[1])
        kept = []
        for r in rows:
            if kept and math.dist(r[1], kept[-1][1]) > J:
                continue
            kept.append(r)
        rows = kept
        est = "E0"
    ts = [r[0] for r in rows]
    P = np.array([r[1] for r in rows]) if rows else np.zeros((0, 2))
    dh_all = np.hypot(P[:, 0], P[:, 1]) if len(rows) else np.zeros(0)
    out_t, out_s, out_v, out_m = [], [], [], []
    dh_min = 1e9
    for i, (t, p) in enumerate(rows):
        dh = dh_all[i]
        dh_min = min(dh_min, dh)
        if est in ("E0", "med1", "med2", "ls1", "ls2", "ts2"):
            win = {"E0": 1.0, "med1": 1.0, "med2": 2.0, "ls1": 1.0, "ls2": 2.0, "ts2": 2.0}[est]
            j = bisect.bisect_left(ts, t - win)
            if j >= i or ts[i] - ts[j] < 0.5 * win:
                continue
            if est == "E0":
                q = rows[j][1]; dt = t - ts[j]
                spd = math.hypot((p[0] - q[0]) / dt, (p[1] - q[1]) / dt)
                vr = (math.hypot(q[0], q[1]) - dh) / dt
            elif est in ("med1", "med2"):
                tt = np.array(ts[j:i + 1]); PP = P[j:i + 1]; dd = dh_all[j:i + 1]
                dtt = np.diff(tt); dtt[dtt <= 0] = 1e-3
                vN = np.diff(PP[:, 0]) / dtt; vE = np.diff(PP[:, 1]) / dtt
                spd = math.hypot(float(np.median(vN)), float(np.median(vE)))
                vr = float(np.median(-np.diff(dd) / dtt))
            elif est.startswith("ls"):
                tt = np.array(ts[j:i + 1]) - t
                A_ = np.vstack([tt, np.ones_like(tt)]).T
                cN = np.linalg.lstsq(A_, P[j:i + 1, 0], rcond=None)[0][0]
                cE = np.linalg.lstsq(A_, P[j:i + 1, 1], rcond=None)[0][0]
                cd = np.linalg.lstsq(A_, dh_all[j:i + 1], rcond=None)[0][0]
                spd = math.hypot(cN, cE); vr = -cd
            else:  # Theil–Sen 2 s (mediana nachyleń par, podpróbka do 40 punktów)
                idx = np.arange(j, i + 1)
                if len(idx) > 40:
                    idx = idx[np.linspace(0, len(idx) - 1, 40).astype(int)]
                tt = np.array([ts[k] for k in idx])
                a_, b_ = np.triu_indices(len(idx), 1)
                dtt = tt[b_] - tt[a_]
                m = dtt > 1e-3
                sN = np.median((P[idx][b_, 0] - P[idx][a_, 0])[m] / dtt[m])
                sE = np.median((P[idx][b_, 1] - P[idx][a_, 1])[m] / dtt[m])
                sd = np.median((dh_all[idx][b_] - dh_all[idx][a_])[m] / dtt[m])
                spd = math.hypot(sN, sE); vr = -sd
        else:
            raise ValueError(est)
        out_t.append(t); out_s.append(spd); out_v.append(vr); out_m.append(dh_min)
    return np.array(out_t), np.array(out_s), np.array(out_v), np.array(out_m)


def r3_episode(rows, est):
    ts, spd, vr, dmin = est_stream(rows, est)
    if len(ts) == 0:
        return None
    # dh bieżące potrzebne do strefy: odtwarzamy z rows po czasie
    tmap = {r[0]: math.hypot(r[1][0], r[1][1]) for r in rows}
    dh = np.array([tmap[t] for t in ts])
    Wm = (spd > V_MOVE) & (dh < R_ZONE) & (vr < V_RAD_MAX) & (dmin >= FLOOR)
    r = streak_rule(ts, Wm, dmin, T_FLAG, t0=rows[0][0])   # zegar v1: od pierwszej klatki trk
    # przerwania licznika: streak ≥1 s zerwany przed 12 s (w strefie i w ruchu)
    br = 0; s0 = None
    for i in range(len(ts)):
        if Wm[i]:
            s0 = ts[i] if s0 is None else s0
        else:
            if s0 is not None and 1.0 <= ts[i] - s0 < T_FLAG:
                br += 1
            s0 = None
    r["przerwania"] = br
    sel = (spd > V_MOVE) & (dh < R_ZONE)
    r["vrad_p95"] = round(float(np.percentile(vr[sel], 95)), 3) if sel.any() else None
    r["vrad_p99"] = round(float(np.percentile(vr[sel], 99)), 3) if sel.any() else None
    r["frac_pik_vrad_ge_030"] = round(float((vr[sel] >= V_RAD_MAX).mean()), 4) if sel.any() else None
    return r


def jumps(rows, J):
    if len(rows) < 2:
        return None
    n = sum(1 for a, b in zip(rows, rows[1:]) if math.dist(a[1], b[1]) > J)
    return n / (len(rows) - 1)


R3_EST = ["E0", "med1", "med2", "ls1", "ls2", "ts2", "jump_0.5", "jump_1.0"]


def r3(eps):
    table = []
    per = {}
    for est in R3_EST:
        res = {}
        for e in eps:
            r = r3_episode(e["rows"], est)
            if r is None:
                r = dict(ever=False, final=False, t_flag=None, t_rev=None, przerwania=0,
                         vrad_p95=None, vrad_p99=None, frac_pik_vrad_ge_030=None)
            r.update(rodz=e["rodz"], v=e["v"], klasa=e["klasa"])
            res[e["id"]] = r
        k = kryterium(res)
        k["estymator"] = est
        k["tp_czasy"] = {i.split(":")[-1]: res[i]["t_flag"] for i in res if res[i]["rodz"] == "TP"}
        for kl in ("TP", "NULL_v0.5", "NULL_v1", "NULL_v0", "FP", "ORB"):
            xs = [r for r in res.values() if r["klasa"] == kl]
            if not xs:
                continue
            p95 = [r["vrad_p95"] for r in xs if r["vrad_p95"] is not None]
            fr = [r["frac_pik_vrad_ge_030"] for r in xs if r["frac_pik_vrad_ge_030"] is not None]
            k[f"{kl}:vrad_p95_med"] = round(float(np.median(p95)), 3) if p95 else None
            k[f"{kl}:frac_pik_med"] = round(float(np.median(fr)), 4) if fr else None
            k[f"{kl}:przerwania_sum"] = int(sum(r["przerwania"] for r in xs))
        if est == "E0":   # KOTWICA: E0 == baza(i) wabik_sig2 co do liczb
            ref = json.load(open(os.path.join(ROOT, "results", "WABIK2", "s1_tabela.json")))["tabela"][0]
            assert (k["TP_le15"], k["NULL_ever"], k["NULL_final"]) == \
                (ref["TP_le15"], ref["NULL_ever"], ref["NULL_final"]), f"KOTWICA E0 FAIL {k}"
            for sid, rr in ref["epizody"].items():
                mine = [res[i] for i in res if i.endswith(":" + sid)][0]
                assert mine["t_flag"] == rr["t_flag_od_pierwszej"], f"E0 {sid} {mine} vs {rr}"
        table.append(k)
        per[est] = {i: {kk: res[i][kk] for kk in ("ever", "final", "t_flag", "przerwania")} for i in res}
    jm = {}
    for J in (0.5, 1.0, 2.0):
        for kl in ("TP", "FP", "ORB", "NULL_v0", "NULL_v0.5", "NULL_v1"):
            xs = [jumps(e["rows"], J) for e in eps if e["klasa"] == kl]
            xs = [x for x in xs if x is not None]
            jm[f"J{J:g}:{kl}"] = round(float(np.mean(xs)), 4) if xs else None
    # kalibracja miary wobec 24.3% (ANEKS_WABIK-1:17 — atrybucja w smoke A z DWOMA obiektami)
    d = os.path.join(ROOT, "results", "WABIK", "s1", "s1_smoke")
    sm = {}
    if os.path.isdir(d):
        e = W2.episodes_of(d)[0]
        rows = W2.feed_rows(os.path.join(d, "percep_feed.jsonl"), e["t0"], e["t1"])
        for J in (0.5, 1.0, 2.0):
            sm[f"J{J:g}"] = round(jumps(rows, J), 4)
    return table, per, jm, sm


# ------------------------------------------------------------------ R4: mikro-sygnatura
def r4(eps):
    sys.path.insert(0, ROOT)
    from r02.mti import FX  # noqa
    stat = []
    for e in eps:
        if e["klasa"] != "NULL_v0":
            continue
        P = np.array([r[1] for r in e["rows"]])
        own = []
        for r in W2.iter_jsonl(os.path.join(e["dir"], "percep_feed.jsonl")):
            t = r.get("t_frame")
            if t is not None and e["t0"] <= t <= e["t1"] and r.get("trk_pos_ned") and r.get("own_pos_ned"):
                own.append(math.dist(r["trk_pos_ned"], r["own_pos_ned"]))
        rng = float(np.median(own)) if own else None
        sd = np.std(P - np.median(P, axis=0), axis=0)
        sig = float(np.hypot(sd[0], sd[1]))
        mad = float(np.median(np.hypot(*(P - np.median(P, axis=0)).T))) * 1.4826
        stat.append(dict(id=e["id"], n=len(P), sigma_xy_m=round(sig, 3), mad_xy_m=round(mad, 3),
                         zasieg_med_m=round(rng, 2) if rng else None,
                         sigma_px=round(mad * FX / rng, 2) if rng else None))
    mets = {}
    for e in eps:
        ts = np.array([r[0] for r in e["rows"]]); P = np.array([r[1] for r in e["rows"]])
        M1, M2, M5 = [], [], []
        k = 0
        while k < len(ts):
            j = bisect.bisect_left(ts, ts[k] + 1.0)
            if j - k >= 8:
                seg = P[k:j]; tt = ts[k:j] - ts[k]
                d1 = np.diff(seg, axis=0)
                m1 = float(np.var(d1[:, 0]) + np.var(d1[:, 1]))
                vp = float(np.var(seg[:, 0]) + np.var(seg[:, 1]))
                res = 0.0
                for ax in (0, 1):
                    c = np.polyfit(tt, seg[:, ax], 2)
                    res += float(np.mean((np.polyval(c, tt) - seg[:, ax]) ** 2))
                M1.append(m1); M2.append(m1 / vp if vp > 1e-9 else np.nan); M5.append(math.sqrt(res))
            k = j if j > k else k + 1
        if M1:
            mets[e["id"]] = dict(klasa=e["klasa"], M1_med=float(np.median(M1)),
                                 M2_med=float(np.nanmedian(M2)), M5_med=float(np.median(M5)))
    agg = {}
    for kl in sorted({m["klasa"] for m in mets.values()}):
        xs = [m for m in mets.values() if m["klasa"] == kl]
        agg[kl] = {f: [round(float(np.percentile([x[f] for x in xs], q)), 5) for q in (10, 50, 90)]
                   for f in ("M1_med", "M2_med", "M5_med")}
        agg[kl]["n"] = len(xs)

    def auc(a, b):
        a = np.array(a); b = np.array(b)
        return float(((a[:, None] > b[None, :]).mean() + 0.5 * (a[:, None] == b[None, :]).mean()))
    sep = {}
    tp = [m for m in mets.values() if m["klasa"] == "TP"]
    nw = [m for m in mets.values() if m["klasa"] == "NULL_v0.5"]
    n1 = [m for m in mets.values() if m["klasa"] == "NULL_v1"]
    for f in ("M1_med", "M2_med", "M5_med"):
        sep[f] = {"AUC_TP_vs_NULLv05": round(auc([x[f] for x in tp], [x[f] for x in nw]), 3),
                  "AUC_TP_vs_NULLv1": round(auc([x[f] for x in tp], [x[f] for x in n1]), 3)}
    return dict(FX=FX, statyczne=stat, metryki_klasy_p10_p50_p90=agg, separacja=sep)


# ------------------------------------------------------------------ R5: wędrowcy
def r5(eps):
    out = []
    for e in eps:
        if e["rodz"] != "NULL":
            continue
        r = W2.evaluate(e["rows"])
        if not r["final"]:
            continue
        m = e["man"]
        dur = min(m.get("ep_dur_s", 110.0), e["t1"] - e["t0"])
        gt = [S.position_at(m, t) for t in np.arange(0.0, dur, 0.1)]
        gdh = [math.hypot(g[0], g[1]) for g in gt]
        P = np.array([x[1] for x in e["rows"]])
        dh = np.hypot(P[:, 0], P[:, 1])
        ts = np.array([x[0] for x in e["rows"]])
        dts = np.diff(ts)
        in_zone = float(np.sum(dts[dh[1:] < R_ZONE][dts[dh[1:] < R_ZONE] < 1.0]))
        out.append(dict(id=e["id"], sid=e["sid"], cell=m["cell"], v=e["v"],
                        t_pierwszy_trk_s=round(float(ts[0] - e["t0"]), 2),
                        dh_min_trk=round(float(dh.min()), 2), dh_min_GT=round(float(min(gdh)), 2),
                        dh_med_GT=round(float(np.median(gdh)), 2),
                        czas_w_strefie_trk_s=round(in_zone, 1), t_flagi_s=r["t_flag_od_pierwszej"],
                        klasa_R5=("GT nigdy <5 m — definicyjnie wabiko-podobny" if min(gdh) >= FLOOR
                                  else "GT <5 m, track ≥5 m — percepcja (track nie widział zbliżenia)")))
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    eps = load_bench()
    print(f"[bench] {len(eps)} epizodów: " + ", ".join(
        f"{k} {sum(1 for e in eps if e['klasa'] == k)}" for k in sorted({e['klasa'] for e in eps})))
    if mode in ("anchor", "all"):
        res = {}
        for e in eps:
            r = W2.evaluate(e["rows"])
            res[e["id"]] = dict(rodz=e["rodz"], v=e["v"], ever=r["ever"], final=r["final"],
                                t_flag=r["t_flag_od_pierwszej"], t_rev=r["t_revoke"])
        k = kryterium(res)
        print("[kotwica baza(i)]", k)
        ref = json.load(open(os.path.join(ROOT, "results", "WABIK2", "s1_tabela.json")))["tabela"][0]
        assert (k["TP_le15"], k["FP_flags"], k["ORB_odwolane"], k["NULL_ever"], k["NULL_final"]) == \
            (ref["TP_le15"], ref["FP_flags"], ref["ORB_final_niew"], ref["NULL_ever"], ref["NULL_final"]), "KOTWICA FAIL"
        print("[kotwica] PASS vs s1_tabela baza(i)")
    if mode in ("r2", "all"):
        table, feats = r2(eps)
        pts, front = pareto(table)
        adm = [r for r in table if r["dopuszczony"]]
        print(f"[R2] konfiguracji {len(table)}, dopuszczonych {len(adm)}; krawędź Pareto (TP≤15, NULL_final) "
              f"przy FP 0 ∧ ORB 2/2: {pts}")
        json.dump(dict(kryterium="TP>=5/6 w <=15 s ∧ FP 0/3 ∧ ORB odwolane 2/2 ∧ NULL_final <=13/115",
                       n_konfiguracji=len(table), n_dopuszczonych=len(adm), pareto=pts,
                       front=front, tabela=table, cechy=feats),
                  open(os.path.join(OUT, "r2_dcpa_tabela.json"), "w"), indent=1, default=str)
    if mode in ("r3", "all"):
        table, per, jm, sm = r3(eps)
        pts, front = pareto(table)
        for r in table:
            print(f"[R3] {r['estymator']:9s} TP≤15={r['TP_le15']}/6 FP={r['FP_flags']} ORB={r['ORB_odwolane']} "
                  f"NULL ever/final={r['NULL_ever']}/{r['NULL_final']} TP={r['tp_czasy']}")
        print(f"[R3] Pareto {pts}; skoki {jm}; smoke A {sm}")
        json.dump(dict(tabela=table, pareto=pts, per_epizod=per, skoki_frac=jm, smoke_A_skoki=sm),
                  open(os.path.join(OUT, "r3_estymatory.json"), "w"), indent=1, default=str)
    if mode in ("r4", "all"):
        r = r4(eps)
        print("[R4]", json.dumps(r["separacja"]), "statyczne:",
              [(s["id"].split(":")[-1], s["mad_xy_m"], s["zasieg_med_m"], s["sigma_px"]) for s in r["statyczne"]][:12])
        json.dump(r, open(os.path.join(OUT, "r4_mikro.json"), "w"), indent=1)
    if mode in ("r5", "all"):
        r = r5(eps)
        for x in r:
            print("[R5]", x)
        json.dump(r, open(os.path.join(OUT, "r5_wedrowcy.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
