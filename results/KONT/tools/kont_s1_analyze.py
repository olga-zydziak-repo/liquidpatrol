#!/usr/bin/env python3
"""results/KONT/tools/kont_s1_analyze.py — wyniki (ii)–(v) Bootu B (PROMPT_KONT_S1 §3) z ulogu, trace, percep_feed; GT przez kont_eps (gt_judge).
Czas ulogu = czas gz (arming 91.456 vs 91.46, porównanie w wyniku); stempel `ts` DDS w trace jest w innej bazie (synchronizacja agenta), nieużywany.
Odcięcie: sim z t_rel sprzed wywołania set_param (episode_start.t0_sim + cut.t_rel). Wyjście: results/KONT/s1/s1_wyniki.json + ulog_wyciag_bootB.jsonl"""
import json
import math
import os
import sys

import numpy as np
from pyulog import ULog

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
import kont_eps
import kont_ulog_extract as X

B = os.path.join(ROOT, "results/KONT/s1/bootB")
SLOW = 0.10


def trans(t, v):
    return [(round(int(t[i]) / 1e6, 3), int(v[i])) for i in np.flatnonzero(np.r_[True, v[1:] != v[:-1]])]


def gaps(t, thr=0.5):
    d = np.diff(t) / 1e6
    return [[round(float(t[i]) / 1e6, 2), round(float(d[i]), 3)] for i in np.flatnonzero(d > thr)]


def cadence(rows, a, b):
    ts = [t for t in rows if a <= t <= b]
    d = np.diff(ts); d = d[(d > 0) & (d <= 2.0)]
    p50 = float(np.median(d))
    return {"okno_sim": [round(a, 2), round(b, 2)], "n_delt": int(d.size), "dt_p50": round(p50, 4), "hz_p50": round(1 / p50, 2),
            "frac_gt_0p10": round(float((d > SLOW).mean()), 4), "max_dt": round(float(d.max()), 3),
            "werdykt_frozen": "PASS" if p50 <= 0.070 and (d > SLOW).mean() <= 0.05 else "FAIL", "podloga_10hz": bool(1 / p50 >= 10)}


def main():
    ev, gt, ctl, ekf = {}, [], [], []
    for l in open(os.path.join(B, "trace.jsonl")):
        r = json.loads(l)
        if r["t"] == "event":
            ev.setdefault(r["ev"], r)
        elif r["t"] == "gt":
            gt.append(r)
        elif r["t"] == "ctl":
            ctl.append(r)
        elif r["t"] == "ekf":
            ekf.append(r)
    t_cut = ev["episode_start"]["t0_sim"] + ev["cut"]["t_rel"]
    t_desc = ev["descent_start"]["sim"]
    t_land = ev["gt_przyziemienie"]["sim"]
    rows = X.extract(os.path.join(B, "boot.ulg"), t_cut)
    with open(os.path.join(ROOT, "results/KONT/s1/ulog_wyciag_bootB.jsonl"), "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    _, d = X.load(os.path.join(B, "boot.ulg"))
    vs, lp, fl, ff = d["vehicle_status"], d["vehicle_local_position"], d["estimator_status_flags"], d["failsafe_flags"]
    arm_u = float(vs["timestamp"][int(np.argmax(vs["arming_state"] == 2))]) / 1e6
    mw = lp["timestamp"] / 1e6 >= t_cut
    mo = (lp["timestamp"] / 1e6 >= t_cut) & (lp["timestamp"] / 1e6 <= t_desc)
    nav = trans(vs["timestamp"], vs["nav_state"])
    ii = {"okno_orbity_sim_s": round(t_desc - t_cut, 2), "xy_valid_min_w_oknie": int(lp["xy_valid"][mo].min()),
          "v_xy_valid_min_w_oknie": int(lp["v_xy_valid"][mo].min()), "dead_reckoning_max_w_oknie": int(lp["dead_reckoning"][mo].max()),
          "xy_valid_min_do_przyziemienia": int(lp["xy_valid"][(lp["timestamp"] / 1e6 >= t_cut) & (lp["timestamp"] / 1e6 <= t_land)].min()),
          "nav_przejscia": nav, "nav_12_po_odcieciu": any(n == 12 and t >= t_cut for t, n in nav),
          "failsafe_przejscia": trans(vs["timestamp"], vs["failsafe"]),
          "offboard_lost_przejscia": trans(ff["timestamp"], ff["offboard_control_signal_lost"]),
          "cs_opt_flow_przejscia": trans(fl["timestamp"], fl["cs_opt_flow"])}
    a = d["estimator_aid_src_optical_flow"]
    at = a["timestamp"] / 1e6
    win = (at >= t_cut) & (at <= t_desc)
    nom = (at >= ev["offboard"]["sim"]) & (at < t_cut)
    fused = a["fused"].astype(bool)
    tf = a["timestamp"][win & fused]
    of = d["vehicle_optical_flow"]; oq = of["quality"]; ot = of["timestamp"] / 1e6
    rej = (fl["reject_optflow_x"] | fl["reject_optflow_y"])
    ftt = fl["timestamp"] / 1e6
    tr = a["test_ratio"] if "test_ratio" in a else None
    ii["aiding_flow"] = {"n_probek_okno": int(win.sum()), "frac_fused_okno": round(float(fused[win].mean()), 4), "frac_fused_nominal": round(float(fused[nom].mean()), 4),
                         "frac_rejected_okno": round(float(a["innovation_rejected"][win].mean()), 4), "frac_rejected_nominal": round(float(a["innovation_rejected"][nom].mean()), 4),
                         "luki_fuzji_gt_0p5s_okno": gaps(tf), "luki_fuzji_gt_0p2s_n": len(gaps(tf, 0.2)), "najdluzsza_luka_s": round(float(np.diff(tf).max()) / 1e6, 3),
                         "hz_fuzji_okno": round(float(len(tf) / (t_desc - t_cut)), 1)}
    ii["jakosc_flow"] = {"quality_okno_p50": float(np.median(oq[(ot >= t_cut) & (ot <= t_desc)])), "quality_okno_min": int(oq[(ot >= t_cut) & (ot <= t_desc)].min()),
                         "quality_okno_frac_0": round(float((oq[(ot >= t_cut) & (ot <= t_desc)] == 0).mean()), 4), "EKF2_OF_QMIN": 1}
    dd = d["distance_sensor"]; dt_ = dd["timestamp"] / 1e6; dw = (dt_ >= t_cut) & (dt_ <= t_desc)
    ii["dalmierz"] = {"current_distance_p50": round(float(np.median(dd["current_distance"][dw])), 2), "min": round(float(dd["current_distance"][dw].min()), 2),
                      "max": round(float(dd["current_distance"][dw].max()), 2), "signal_quality_min": int(dd["signal_quality"][dw].min()) if "signal_quality" in dd else None,
                      "cs_rng_hgt_przejscia": trans(fl["timestamp"], fl["cs_rng_hgt"])}
    cg = trans(fl["timestamp"], fl["cs_gnss_pos"])
    off = next(t for t, v in cg if v == 0 and t >= t_cut - 1)
    nom_flips = [x for x in cg if arm_u - 60 <= x[0] < t_cut - 1e-3 and x[0] > cg[1][0]]
    iii = {"przejscia": cg, "t_odciecie_sim": round(t_cut, 3), "t_flaga_off": off, "opoznienie_s": round(off - t_cut, 3),
           "okno_nominalu_s": round(t_cut - cg[1][0], 1), "okno_nominalu_w_powietrzu_s": round(t_cut - next(t for t, v in trans(fl["timestamp"], fl["cs_in_air"]) if v == 1), 1),
           "przeskoki_w_nominale": len(nom_flips), "changed_param_ts": [(round(t / 1e6, 3), n, v) for t, n, v in ULogParams(os.path.join(B, "boot.ulg"))],
           "odniesienie": "t_rel sprzed set_param; stemple flag ms; ulog≈gz: arming ulog %.3f vs event %.3f" % (arm_u, ev["armed"]["sim"])}
    pf = [json.loads(l).get("t_frame") for l in open(os.path.join(B, "percep_feed.jsonl"))]
    pf = [t for t in pf if t is not None]
    iv = {"preflight": json.load(open(os.path.join(B, "sonda_preflight.json"))), "lot_arm_do_przyziemienia": cadence(pf, ev["armed"]["sim"], t_land),
          "okno_po_odcieciu": cadence(pf, t_cut, t_desc)}
    e = kont_eps.eps_curve(B)
    k2_h = []
    for n in range(1, 13):
        try:
            k2_h.append(kont_eps.eps_curve(os.path.join(ROOT, f"results/K2/k2c_b{n}"), z_ground=0.2)["healthy_p95"])
        except Exception as ex:
            k2_h.append(str(ex))
    rg = [c["r_gt"] for c in ctl]
    rc = [abs(c["r_gt"] - c["r_est"]) for c in ctl if c["sim"] >= t_cut]
    gw = [(g["mono"], g["sim"]) for g in gt if ev["armed"]["mono"] <= g["mono"] <= ev["descent_end"]["mono"]]
    v2 = (gw[-1][1] - gw[0][1]) / (gw[-1][0] - gw[0][0])
    res = {"t_cut_sim": round(t_cut, 3), "t_descent_sim": t_desc, "t_land_gt_sim": t_land, "scenariusz": ev["episode_start"]["scenario_id"], "t_entry": ev["entry"]["t_entry"],
           "ii": ii, "iii": iii, "iv": iv,
           "v": {"eps": e, "k2_healthy_p95_bez_flow": k2_h, "boot_b_healthy_p95_z_flow": e["healthy_p95"], "healthy_valid_gt_judge": e["healthy_valid"]},
           "r_gt_max": max(rg), "r_gt_przy_odcieciu": ev["cut"]["r_gt"], "max_abs_rgt_minus_rest_po_odcieciu": round(max(rc), 2), "breach": any(r > 32 for r in rg), "fuse_odpalil": ev["descent_start"]["reason"] == "fuse_r_gt",
           "powod_zejscia": ev["descent_start"]["reason"], "v2p_dsim_dwall": round(v2, 4), "gt_koncowe_z": ev["gt_przyziemienie"]["z"], "r_gt_przyziemienie": ev["gt_przyziemienie"]["r_gt"],
           "fazy_po_odcieciu": {p: sum(1 for c in ctl if c["sim"] >= t_cut and c["phase"] == p) for p in {c["phase"] for c in ctl}}}
    json.dump(res, open(os.path.join(ROOT, "results/KONT/s1/s1_wyniki.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: res[k] for k in res if k not in ("v",)}, ensure_ascii=False, indent=0)[:6000])
    print(json.dumps({k: v for k, v in e.items() if not k.startswith("krzywa")}, ensure_ascii=False))
    print("sim:", e["krzywa_1s_sim"][::5]); print("k2_h", k2_h)


def ULogParams(p):
    return ULog(p, []).changed_parameters


main()
