#!/usr/bin/env python3
"""results/KONT/tools/kont_s4_analyze.py — kryteria S4 per boot (PROMPT_KONT_S4 §2), z GT i ulogu, nie z listy zdarzeń.
Prerejestracja definicji (commit przed pierwszym bootem S4):

Wspólne: ε przez gt_judge importem (sha 447efaa2, test syntetyczny --selftest = warunek ważności, R-1a), metoda par i ramka
T_home 1:1 jak kont_s2_analyze.py; czas = sim (ulog PX4 w lockstep = sim); wiek flagi = sim − t_flag, t_flag = pierwsze
cs_gnss_pos 1→0 w ulogu po t_cut − 0.5 s; koszyk = ⌊wiek flagi⌋ (ANEKS_KONT-3b §1.3); ε_b, Δ_D5 z s2_freeze_bf.json (sha
ae19f66c, asercja). r_GT = |GT_xy − GT_home_xy| (home = poza GT przy uzbrojeniu).
Ważność epizodu: selftest GT PASS ∧ V2′ kanoniczne per epizod (ANEKS_KONT-4d §1.1: bench/campaign_analyze.judge_boot,
D9 = Δsim/Δwall ≥ 0.90 z rtf_stream.jsonl ∧ najdłuższy deep-stall ≤ 1.5 s ∧ timejump 0) ∧ zegar (skan2_zegar --check:
≤ 3 skoki, |skok| ≤ 1.2 s) ∧ xy_valid (ulog) od t_flag do REFUSE.
(a) max r_GT ≤ R_E = 32 przez cały epizod do przyziemienia (wiersze gt + tk).
(b) ∀ par ε w [t_flag, t_REFUSE): ε ≤ ε_b(⌊wiek⌋) ∧ Δ = max ε od REFUSE do przyziemienia GT − ε w chwili REFUSE ≤ 1.524.
(c) okno [t_flag, t_REFUSE]: frac(ticków z ważnym trackiem) ≥ 0.85 ∧ frac(ticków z d_GT ∈ [6, 10] m) ≥ 0.85, gdzie d_GT =
    pozioma odległość GT dron–intruz; pasmo [6.0, 10.0] i próg 0.85 = kanon ławki (bench/bench_judge.py:22, :123;
    RAPORT_BENCH §3 „frac (b) … min 0.95 ≥ 0.85"). Raport: czas kontynuacji i przyczyna końca (T* / bariera / inne).
(d) opóźnienie w pętli: sim(REFUSE) − sim(pierwszego ticka z t_KONT ≥ 22 − 2·dt albo r_est > R(k)) ≤ 0.15 s; dla przyczyny
    T* dodatkowo sim(REFUSE) − (t_flag + 21.9) ≤ 0.15 s (wiek z ulogu).
(e) ulog: nav_state = 14 w [t_flag, t_REFUSE] ∧ nav_state = 14 i failsafe = 0 w [t_flag, przyziemienie GT].
(f) ramię (−): epizod nominalny i faza przed cięciem — 0 ticków REFUSE(POS) i 0 ticków z fazą ≠ NOMINAL; R-G-NOM osobno.
Użycie: kont_s4_analyze.py <katalog bootu>. Wyjście: wyniki_s4.json, ulog_wyciag.jsonl (boot z cięciem)."""
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
sys.path[:0] = [HERE, GJ, ROOT]
import gt_judge as J
import kont_ulog_extract as X
from harness.intruder_motion import gz_to_ned
from bench.campaign_analyze import judge_boot                       # ANEKS_KONT-4d §1.1: V2′ jak sędzia

GT_SHA8 = "447efaa2"
FREEZE = os.path.join(ROOT, "results/KONT/s2/s2_freeze_bf.json")
FREEZE_SHA = "ae19f66c6807de6c824bf0fd723965258b15b77963eb866afb78d3dd3740ae4a"
R_E, Z_GROUND, V2P_MIN = 32.0, 0.15, 0.90
BAND, FRAC_MIN = (6.0, 10.0), 0.85
T_THR, LAT_MAX = 21.9, 0.15


def trans(t, v):
    return [(round(int(t[i]) / 1e6, 3), int(v[i])) for i in np.flatnonzero(np.r_[True, v[1:] != v[:-1]])]


def zegar_ok(p):
    if not os.path.exists(p):
        return None, None
    r = subprocess.run([sys.executable, os.path.join(ROOT, "results/SKAN2/tools/skan2_zegar.py"), "--check", p], capture_output=True, text=True)
    z = json.loads(r.stdout)
    return (z["skoki"] <= 3 and all(abs(j["skok_s"]) <= 1.2 for j in z["lista"])), z["skoki"]


def load(d):
    rows = {"event": [], "ekf": [], "gt": [], "tk": [], "flag": [], "meta": []}
    for l in open(os.path.join(d, "trace.jsonl")):
        try:
            r = json.loads(l)
        except ValueError:
            continue
        if r.get("t") in rows:
            rows[r["t"]].append(r)
    for k in ("ekf", "gt", "tk"):
        rows[k].sort(key=lambda r: r["mono"])
    return rows


def ev1(evs, name, ep=None):
    return next((e for e in evs if e["ev"] == name and (ep is None or e.get("episode_id") == ep)), None)


def analyze(d):
    raw = open(FREEZE, "rb").read()
    assert hashlib.sha256(raw).hexdigest() == FREEZE_SHA
    F = json.loads(raw)
    eps_b, delta_d5 = F["eps_b_obwiednia"], F["delta_D5"]
    assert hashlib.sha256(open(os.path.join(GJ, "gt_judge.py"), "rb").read()).hexdigest()[:8] == GT_SHA8
    st = subprocess.run([sys.executable, os.path.join(GJ, "gt_judge.py"), "--selftest"], capture_output=True, text=True)
    R = load(d)
    evs, gt, tk = R["event"], R["gt"], R["tk"]
    res = {"boot": os.path.basename(d), "przyrzad_selftest": st.returncode == 0}
    res["zegar_ok"], res["zegar_skoki"] = zegar_ok(os.path.join(d, "zegar2.jsonl"))
    armed = ev1(evs, "armed")
    if armed is None or not tk:
        res.update(wazny=False, powod_niewazny="brak uzbrojenia albo pętli")
        json.dump(res, open(os.path.join(d, "wyniki_s4.json"), "w"), ensure_ascii=False, indent=1)
        return res
    gx0, gy0 = armed["gt_home"]
    rgt = lambda g: math.hypot(g["x"] - gx0, g["y"] - gy0)
    end_m = (ev1(evs, "gt_przyziemienie") or ev1(evs, "denial_boot_end") or evs[-1])["mono"]
    v2 = {v["episode_id"]: v for v in judge_boot(d)}                    # ANEKS_KONT-4d §1.1
    res["v2p_epizody"] = {str(k): {"valid": bool(v["valid_campaign_V2p"]), **v["stalls"]} for k, v in v2.items()}
    gm, gs = np.array([g["mono"] for g in gt]), np.array([g["sim"] for g in gt])
    cut = ev1(evs, "denial")
    res["ciecie"] = cut is not None
    eps_out = []
    for st_ev in [e for e in evs if e["ev"] == "episode_start"]:
        ep = st_ev["episode_id"]
        en = ev1(evs, "episode_end", ep)
        t0m, t1m = st_ev["mono"], (en["mono"] if en else end_m)
        rows = [r for r in tk if r["ep"] == ep]
        cut_sim = cut["sim"] if (cut and cut.get("episode_id") == ep) else None
        pre = [r for r in rows if cut_sim is None or r["sim"] < cut_sim]
        gts = [g for g in gt if t0m <= g["mono"] <= max(t1m, end_m if cut_sim is not None else t1m)]
        o = {"episode_id": ep, "scenario_id": st_ev["scenario_id"], "ciecie": cut_sim is not None,
             "t_entry": en.get("t_entry") if en else None, "n_tk": len(rows),
             "minus_refuse_pos": sum(1 for r in pre if r["dec"] == "REFUSE" and r["reason"] == "POS_DEGRADED"),
             "minus_kont_ticki": sum(1 for r in pre if r["ph"] != "NOMINAL"),
             "r_g_nom_minus": sum(1 for r in pre if r["rule"] == "R-G-NOM"),
             "r_g_nom_wszystkie": sum(1 for r in rows if r["rule"] == "R-G-NOM"),
             "refuse_rg": sum(1 for r in rows if r["rule"] == "R-G"),
             "r_gt_max": round(max([rgt(g) for g in gts] + [r["r_gt"] for r in rows]), 3)}
        o["v2p"] = res["v2p_epizody"].get(str(ep))
        o["v2p_ok"] = bool(o["v2p"] and o["v2p"]["valid"])
        o["a_ok"] = o["r_gt_max"] <= R_E
        o["f_ok"] = o["minus_refuse_pos"] == 0 and o["minus_kont_ticki"] == 0
        if cut_sim is not None:
            o.update(cut_episode(d, R, ep, cut, rows, gm, gs, eps_b, delta_d5))
        eps_out.append(o)
    res["epizody"] = eps_out
    pw = []
    if not res["przyrzad_selftest"]:
        pw.append("selftest GT")
    for o in eps_out:
        if not o["v2p_ok"]:
            pw.append(f"V2p {o['scenario_id']} {(o['v2p'] or {}).get('dsim_dwall')}")
    if res["zegar_ok"] is False:
        pw.append("zegar")
    for o in eps_out:
        if o["ciecie"] and not o.get("xy_valid_do_refuse"):
            pw.append(f"xy_valid {o['scenario_id']}")
    res["wazny"] = not pw
    res["powod_niewazny"] = "; ".join(pw) or None
    json.dump(res, open(os.path.join(d, "wyniki_s4.json"), "w"), ensure_ascii=False, indent=1)
    return res


def cut_episode(d, R, ep, cut, rows, gm, gs, eps_b, delta_d5):
    evs, ekf, gt = R["event"], R["ekf"], R["gt"]
    o = {}
    ulg = os.path.join(d, "boot.ulg")
    t_cut = cut["sim"]
    rows_x = X.extract(ulg, t_cut)
    with open(os.path.join(d, "ulog_wyciag.jsonl"), "w") as f:
        for r in rows_x:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    _, u = X.load(ulg)
    vs, lp, fl = u["vehicle_status"], u["vehicle_local_position"], u["estimator_status_flags"]
    cg = trans(fl["timestamp"], fl["cs_gnss_pos"])
    t_flag = next((t for t, v in cg if v == 0 and t >= t_cut - 0.5), None)
    ref = ev1(evs, "refuse", ep)
    land = ev1(evs, "gt_przyziemienie", ep)
    o.update(t_cut=t_cut, t_flag=t_flag, opoznienie_flagi_s=round(t_flag - t_cut, 3) if t_flag else None,
             refuse=({k: ref.get(k) for k in ("sim", "rule", "cause", "t_kont", "k", "R_k", "r_est", "r_gt", "heading_deg")} if ref else None),
             t_land=land["sim"] if land else None)
    if t_flag is None or ref is None or land is None:
        o.update(b_ok=False, c_ok=False, d_ok=False, e_ok=False, xy_valid_do_refuse=False,
                 uwaga="brak flagi, REFUSE albo przyziemienia")
        return o
    t_ref, t_land = ref["sim"], land["sim"]
    o["kontynuacja_s"] = round(t_ref - t_flag, 3)
    o["przyczyna_konca"] = {"T*": "T*", "bariera": "bariera"}.get(ref.get("cause"), f"inne ({ref.get('rule')})")
    # ε — metoda 1:1 kont_s2_analyze.py
    cut_m, ref_m, land_m = cut["mono"], ref["mono"], land["mono"]
    for r in ekf:
        r["dead_reckoning"] = cut_m <= r["mono"] <= land_m
    m = J.compute_drift(ekf, gt)
    thx, thy = m["T_home"]
    ts = m["skew_hat_s"] if m["skew_applied"] else 0.0
    ser = [(float(np.interp(t, gm, gs)), t, math.hypot(ex - thx, ey - thy))
           for (t, ex, ey) in J._paired_series(ekf, gt, True, ts) if cut_m <= t <= land_m]
    cont = [(s - t_flag, e) for s, t, e in ser if t_flag <= s < t_ref]
    viol = [(round(a, 3), round(e, 3), eps_b[int(a)]) for a, e in cont if int(a) < len(eps_b) and e > eps_b[int(a)]]
    e0 = next((e for s, t, e in ser if t >= ref_m), None)
    dz = [e for s, t, e in ser if t >= ref_m]
    delta = (max(dz) - e0) if dz and e0 is not None else None
    o.update(eps_max_kont=round(max(e for _, e in cont), 3) if cont else None,
             eps_max_ratio=round(max(e / eps_b[int(a)] for a, e in cont if int(a) < len(eps_b)), 3) if cont else None,
             eps_naruszenia=viol[:10], n_eps_naruszen=len(viol), eps_przy_refuse=round(e0, 3) if e0 is not None else None,
             delta_zejscia=round(delta, 3) if delta is not None else None, T_home=m["T_home"],
             healthy_p95=m["healthy_p95_eps"])
    o["b_ok"] = bool(cont) and not viol and delta is not None and delta <= delta_d5
    # (c) okno [t_flag, t_ref]
    win = [r for r in rows if t_flag <= r["sim"] <= t_ref]
    gmono = np.array([g["mono"] for g in gt])
    dgt = []
    for r in win:
        if r.get("intr") is None:
            continue
        g = gt[int(np.clip(np.searchsorted(gmono, r["mono"]), 0, len(gt) - 1))]
        own = gz_to_ned([g["x"], g["y"], g["z"]])
        dgt.append(math.hypot(own[0] - r["intr"][0], own[1] - r["intr"][1]))
    f_trk = float(np.mean([r["trk_valid"] for r in win])) if win else 0.0
    f_band = float(np.mean([BAND[0] <= x <= BAND[1] for x in dgt])) if dgt else 0.0
    o.update(c_frac_track=round(f_trk, 3), c_frac_pasmo=round(f_band, 3), c_n=len(win),
             c_d_gt_p50=round(float(np.median(dgt)), 2) if dgt else None)
    o["c_ok"] = f_trk >= FRAC_MIN and f_band >= FRAC_MIN
    # (d)
    thr = next((r for r in rows if r["sim"] >= t_flag and r["t_kont"] is not None and
                (r["t_kont"] >= T_THR or (r["R_k"] is not None and r["r_est"] > r["R_k"]))), None)
    lat_loop = round(t_ref - thr["sim"], 3) if thr else None
    lat_flag = round(t_ref - (t_flag + T_THR), 3) if ref.get("cause") == "T*" else None
    o.update(d_lat_petla_s=lat_loop, d_lat_wiek_flagi_s=lat_flag,
             wiek_flagi_przy_refuse_s=round(t_ref - t_flag, 3))
    o["d_ok"] = lat_loop is not None and lat_loop <= LAT_MAX and (lat_flag is None or lat_flag <= LAT_MAX)
    # (e) ulog
    vt = vs["timestamp"] / 1e6
    nav, fs = vs["nav_state"], vs["failsafe"]
    m1 = (vt >= t_flag) & (vt <= t_land)
    o.update(e_nav_poza_14=sorted(set(int(x) for x in nav[m1] if x != 14)), e_failsafe_max=int(fs[m1].max()) if m1.any() else None,
             nav_przejscia=[x for x in trans(vs["timestamp"], nav) if t_flag - 5 <= x[0] <= t_land + 2],
             failsafe_przejscia=trans(vs["timestamp"], fs))
    o["e_ok"] = bool(m1.any()) and not o["e_nav_poza_14"] and o["e_failsafe_max"] == 0
    lt = lp["timestamp"] / 1e6
    m2 = (lt >= t_flag) & (lt <= t_ref)
    o["xy_valid_do_refuse"] = bool(m2.any()) and bool((lp["xy_valid"][m2] == 1).all())
    o["dr_max_kont"] = int(lp["dead_reckoning"][m2].max()) if m2.any() else None
    return o


if __name__ == "__main__":
    r = analyze(sys.argv[1])
    print(json.dumps(r, ensure_ascii=False, default=str)[:3000])
