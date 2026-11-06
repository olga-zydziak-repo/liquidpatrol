#!/usr/bin/env python3
"""results/KONT/tools/kont_s2_analyze.py — wyniki lotu S2 (PROMPT_KONT_S2 §S2.1). ε przez gt_judge importem (sha 447efaa2), test syntetyczny przyrządu PASS warunkiem ważności (R-1a),
p95 nominału jako ε(0⁺) (R-1b), koszyki 1 s od flagi cs_gnss_pos (czas sim), Δ = przyrost ε od początku zejścia do przyziemienia GT (maks. i końcowy), stany z ulogu, wyciąg jsonl.
Użycie: kont_s2_analyze.py <katalog bootu>. Wyjście: <katalog>/wyniki.json, <katalog>/ulog_wyciag.jsonl"""
import hashlib
import json
import math
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
GJ = os.path.join(ROOT, "results/R03/recon/B1bis/instrument")
sys.path[:0] = [HERE, GJ]
import gt_judge as J
import kont_ulog_extract as X

GT_SHA8 = "447efaa2"
Z_GROUND = 0.15
V2P_MIN = 0.90
E_TRK_MAX = 3.0            # [m] track przed odcięciem na realnym celu (próg wykonawcy, nazwany w raporcie)


def trans(t, v):
    return [(round(int(t[i]) / 1e6, 3), int(v[i])) for i in np.flatnonzero(np.r_[True, v[1:] != v[:-1]])]


def zegar_ok(p):
    if not os.path.exists(p):
        return None, None
    r = subprocess.run([sys.executable, os.path.join(ROOT, "results/SKAN2/tools/skan2_zegar.py"), "--check", p], capture_output=True, text=True)
    z = json.loads(r.stdout)
    return (z["skoki"] <= 3 and all(abs(j["skok_s"]) <= 1.2 for j in z["lista"])), z["skoki"]


def analyze(d):
    assert hashlib.sha256(open(os.path.join(GJ, "gt_judge.py"), "rb").read()).hexdigest()[:8] == GT_SHA8
    st = subprocess.run([sys.executable, os.path.join(GJ, "gt_judge.py"), "--selftest"], capture_output=True, text=True)
    res = {"boot": os.path.basename(d), "przyrzad_selftest": st.returncode == 0}
    ev, ekf, gt, ctl = {}, [], [], []
    p = os.path.join(d, "trace.jsonl")
    if os.path.exists(p):
        for l in open(p):
            try:
                r = json.loads(l)
            except ValueError:
                continue
            if r["t"] == "event":
                ev.setdefault(r["ev"], r)
            elif r["t"] == "gt":
                gt.append(r)
            elif r["t"] == "ekf":
                ekf.append(r)
            elif r["t"] == "ctl":
                ctl.append(r)
    res["scenariusz"] = ev.get("episode_start", {}).get("scenario_id")
    res["z_off_m"] = json.load(open(os.path.join(d, "kont_offset.json")))["z_off_m"] if os.path.exists(os.path.join(d, "kont_offset.json")) else None
    res["t_entry"] = ev.get("entry", {}).get("t_entry")
    res["zegar_ok"], res["zegar_skoki"] = zegar_ok(os.path.join(d, "zegar2.jsonl"))
    ulg = os.path.join(d, "boot.ulg")
    if "cut" not in ev or not os.path.exists(ulg) or not ctl:
        res.update(wazny=False, powod_niewazny="brak odcięcia, ulogu albo pętli", breach=bool(ev.get("breach")), refuse_nominal=ev.get("descent_start", {}).get("reason") == "refuse_pos_nominal_STOP",
                   powod_zejscia=ev.get("descent_start", {}).get("reason"))
        json.dump(res, open(os.path.join(d, "wyniki.json"), "w"), ensure_ascii=False, indent=1)
        return res
    t_cut = ev["episode_start"]["t0_sim"] + ev["cut"]["t_rel"]
    rows = X.extract(ulg, t_cut)
    with open(os.path.join(d, "ulog_wyciag.jsonl"), "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    _, u = X.load(ulg)
    vs, lp, fl = u["vehicle_status"], u["vehicle_local_position"], u["estimator_status_flags"]
    cg = trans(fl["timestamp"], fl["cs_gnss_pos"])
    t_on = next(t for t, v in cg if v == 1)
    t_flag = next((t for t, v in cg if v == 0 and t >= t_cut - 0.5), None)
    flips = [x for x in cg if t_on < x[0] < t_cut - 0.5]
    t_air = next((t for t, v in trans(fl["timestamp"], fl["cs_in_air"]) if v == 1), None)
    t_desc = ev["descent_start"]["sim"]
    ref = t_flag if t_flag is not None else t_cut
    lt = lp["timestamp"] / 1e6
    mk = (lt >= ref) & (lt <= t_desc)
    bad_xy = lt[mk][lp["xy_valid"][mk] == 0]
    nav = trans(vs["timestamp"], vs["nav_state"])
    t_land = ev.get("gt_przyziemienie", {}).get("sim")
    nav_loss = next((t for t, n in nav if t >= ref and n != 14 and (t_land is None or t < t_land)), None)
    # ε przez gt_judge
    ekf.sort(key=lambda r: r["mono"]); gt.sort(key=lambda r: r["mono"])
    cut_m = ev["cut"]["mono"]
    land_m = next((r["mono"] for r in gt if r["mono"] > cut_m and r["z"] < Z_GROUND), gt[-1]["mono"])
    desc_m = ev["descent_start"]["mono"]
    for r in ekf:
        r["dead_reckoning"] = cut_m <= r["mono"] <= land_m
    m = J.compute_drift(ekf, gt)
    thx, thy = m["T_home"]
    ts = m["skew_hat_s"] if m["skew_applied"] else 0.0
    gm, gs = np.array([r["mono"] for r in gt]), np.array([r["sim"] for r in gt])
    ser = [(float(np.interp(t, gm, gs)), t, math.hypot(ex - thx, ey - thy)) for (t, ex, ey) in J._paired_series(ekf, gt, True, ts) if cut_m <= t <= land_m]
    assert abs(max(x[2] for x in ser) - m["max_drift"]) < 0.01
    orb = [(s - ref, e) for s, t, e in ser if t <= desc_m and s >= ref]
    kosz = {}
    for tk, e in orb:
        k = int(tk)
        kosz[k] = max(kosz.get(k, 0.0), e)
    e0 = next((e for s, t, e in ser if t >= desc_m), None)
    dz = [e for s, t, e in ser if t >= desc_m]
    d_max = (max(dz) - e0) if dz else None
    at = lambda k: round(kosz[k], 3) if k in kosz else None
    gw = [(g["mono"], g["sim"]) for g in gt if ev["armed"]["mono"] <= g["mono"] <= ev.get("descent_end", ev["descent_start"])["mono"]]
    v2 = (gw[-1][1] - gw[0][1]) / (gw[-1][0] - gw[0][0])
    prec = [c for c in ctl if ev["entry"]["sim"] <= c["sim"] < ev["cut"]["sim"]] if "entry" in ev else []
    fv = float(np.mean([c["trk_valid"] for c in prec])) if prec else 0.0
    err = [math.dist(c["trk"][:2], c["intr"][:2]) for c in prec if c["trk_valid"] and c.get("intr")]
    e_med = float(np.median(err)) if err else None
    fp = [c for c in ctl if c["sim"] >= ev["cut"]["sim"] and c["sim"] <= t_desc]
    fp_valid = float(np.mean([c["trk_valid"] for c in fp])) if fp else None
    track_ok = bool(ev["cut"].get("track_valid")) and e_med is not None and e_med <= E_TRK_MAX
    rg = [c["r_gt"] for c in ctl]
    breach = any(r > 32.0 for r in rg) or "breach" in ev
    okno = t_desc - ref
    res.update(t_flag=t_flag, t_cut=round(t_cut, 3), opoznienie_flagi_s=round(t_flag - t_cut, 3) if t_flag else None, t_descent=t_desc, t_land_gt=t_land, okno_s=round(okno, 2), powod_zejscia=ev["descent_start"]["reason"],
               nominal_powietrze_s=round(t_cut - t_air, 1) if t_air else None, nominal_cisza_s=round(t_cut - t_on, 1), przeskoki_cs_gnss=len(flips), przeskoki_lista=flips,
               xy_valid_cale_okno=bad_xy.size == 0, t_xy_utrata_s=round(float(bad_xy[0] - ref), 2) if bad_xy.size else None, nav_przejscia=nav, t_nav_utrata_s=round(nav_loss - ref, 2) if nav_loss else None,
               failsafe=trans(vs["timestamp"], vs["failsafe"]), dr_max_okno=int(lp["dead_reckoning"][mk].max()),
               eps0_p95_nominal=m["healthy_p95_eps"], healthy_valid_gt_judge=m["healthy_valid"], T_home=m["T_home"], skew=m["skew_hat_s"] if m["skew_applied"] else 0.0, max_drift=m["max_drift"],
               koszyki={str(k): round(v, 3) for k, v in sorted(kosz.items())}, eps_10=at(10), eps_20=at(20), eps_30=at(30), eps_60=at(60), eps_70=at(70),
               eps_start_zejscia=round(e0, 3) if e0 is not None else None, delta_max=round(d_max, 3) if d_max is not None else None, delta_koniec=round(dz[-1] - e0, 3) if dz else None,
               r_gt_max=max(rg), r_gt_ciecie=ev["cut"].get("r_gt"), r_gt_ziemia=ev.get("gt_przyziemienie", {}).get("r_gt"), breach=breach, refuse_nominal=ev["descent_start"]["reason"] == "refuse_pos_nominal_STOP",
               v2p=round(v2, 4), track_frac_przed=round(fv, 3), track_blad_med_m=round(e_med, 2) if e_med is not None else None, track_przy_ciecie=ev["cut"].get("track_valid"), track_frac_po=round(fp_valid, 3) if fp_valid is not None else None, track_ok=track_ok,
               gt_z_orbita=round(float(np.median([g["z"] for g in gt if ev["cut"]["mono"] <= g["mono"] <= desc_m])), 2))
    pw = []
    if not res["przyrzad_selftest"]:
        pw.append("selftest")
    if v2 < V2P_MIN:
        pw.append(f"V2p {v2:.3f}")
    if res["zegar_ok"] is False:
        pw.append("zegar")
    if not track_ok:
        pw.append("track przed odcięciem")
    res["wazny"] = not pw
    res["powod_niewazny"] = "; ".join(pw) or None
    pf = os.path.join(d, "percep_feed.jsonl")
    if os.path.exists(pf):
        tf = [json.loads(l).get("t_frame") for l in open(pf)]
        tf = np.array([t for t in tf if t is not None and ev["armed"]["sim"] <= t <= t_desc])
        dt = np.diff(tf); dt = dt[(dt > 0) & (dt <= 2)]
        res["kadencja_lot"] = {"hz_p50": round(1 / float(np.median(dt)), 2), "frac_gt_0p10": round(float((dt > 0.1).mean()), 4)} if dt.size else None
    json.dump(res, open(os.path.join(d, "wyniki.json"), "w"), ensure_ascii=False, indent=1)
    return res


if __name__ == "__main__":
    r = analyze(sys.argv[1])
    print(json.dumps({k: v for k, v in r.items() if k not in ("koszyki", "nav_przejscia", "failsafe", "przeskoki_lista", "T_home")}, ensure_ascii=False))
