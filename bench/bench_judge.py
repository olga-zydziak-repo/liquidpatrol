#!/usr/bin/env python3
"""bench/bench_judge.py — sędzia orbity (PROMPT_BENCH_BUILD H, PRE §5/§6). ZAMROŻONY SHA przed lotem krytycznym.

Wejście: GT drona (NED, z trace) + GT intruza (NED, z gt_intruder.jsonl) + rtf_stream + zdarzenia osłony.
Wyjście `episode_judge.json` per epizod: t_entry, frac[6,10] w T_orb, frac[7,9], omiatanie[°], d_min, REFUSE,
breach, sukces D6, stalle (n, najdłuższy, Δsim/Δwall), ważność V1/V2/V3 OSOBNO. Wszystko w CZASIE SIM z GT
(stall lockstep NIE zniekształca metryk geometrycznych — D9).

Rdzeń `judge_episode(...)` testowalny bez SITL (NED in). `main()` czyta pliki (ramki: drona gz-ENU→NED
`enu2ned`, intruz gt_intruder już NED przez `drv2ned` w intruder_motion).
"""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

DEFAULTS = {
    "r_orb": 8.0, "band": [6.0, 10.0], "tight": [7.0, 9.0],
    "T_orb": 70.0, "entry_max_s": 25.0, "d_min_req": 4.0, "sweep_req_deg": 630.0,
    # V1/V2/V3 (D9 aneks: V2). Shakeout liczy wszystkie trzy.
    # V1 = strict K1 (H2): ŻADNEGO deep-stalla (max_deep_stall=0) ∧ Δsim/Δwall≥0.95 ∧ timejump=0.
    # V2 = D9 aneks: ≤3 deep-stalle ∧ najdłuższy ≤1.5 s wall ∧ Δsim/Δwall≥0.90 ∧ timejump=0.
    # V3 = najluźniejsza: Δsim/Δwall≥0.80 ∧ timejump=0.
    "V1": {"dsw_min": 0.95, "max_deep_stall": 0, "longest_stall_s": 0.0, "timejump": 0},
    "V2": {"dsw_min": 0.90, "max_deep_stall": 3, "longest_stall_s": 1.5, "timejump": 0},
    "V3": {"dsw_min": 0.80, "timejump": 0},
}


def _interp_ned(series, t):
    """series = [(t_sim, [N,E,D])] posortowane. Interpolacja liniowa pozy w chwili t."""
    if not series:
        return None
    if t <= series[0][0]:
        return list(series[0][1])
    if t >= series[-1][0]:
        return list(series[-1][1])
    for i in range(1, len(series)):
        t0, p0 = series[i - 1]; t1, p1 = series[i]
        if t0 <= t <= t1:
            a = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
            return [p0[k] + a * (p1[k] - p0[k]) for k in range(3)]
    return list(series[-1][1])


def _stalls(rtf, sim_lo, sim_hi):
    """rtf = [{'sim','wall','rtf'}]. Zwraca (n_runs, longest_wall_s, dsim_dwall) na oknie [sim_lo,sim_hi].
    n_runs = liczba CIĄGŁYCH epizodów deep (rtf<0.5), nie próbek (ANEKS „≤3 deep-stalle" = zdarzenia)."""
    seg = [r for r in rtf if sim_lo <= r.get("sim", -1) <= sim_hi and r.get("rtf") is not None]
    if len(seg) < 2:
        return 0, 0.0, 1.0
    n_runs = 0
    longest = 0.0
    run_start_wall = None
    prev_deep = False
    for r in seg:
        deep = r["rtf"] < 0.5
        w = r.get("wall", r["sim"])
        if deep and not prev_deep:                # wejście w run
            n_runs += 1
            run_start_wall = w
        if deep:
            longest = max(longest, w - run_start_wall)
        prev_deep = deep
    walls = [r.get("wall") for r in seg if r.get("wall") is not None]
    dsim = seg[-1]["sim"] - seg[0]["sim"]
    dwall = (max(walls) - min(walls)) if len(walls) >= 2 else dsim
    dsw = dsim / dwall if dwall > 1e-6 else 1.0
    return n_runs, round(longest, 3), round(dsw, 4)


def judge_episode(drone_ned, intr_ned, rtf=None, refuse_count=0, breach=False, timejump=0, params=None):
    """drone_ned/intr_ned = [(t_sim,[N,E,D])]. Zwraca dict werdyktu epizodu."""
    P = dict(DEFAULTS);
    if params:
        P.update(params)
    rtf = rtf or []
    assert drone_ned, "brak GT drona"
    t0 = drone_ned[0][0]
    band_lo, band_hi = P["band"]; tlo, thi = P["tight"]
    # d(t) na siatce czasów drona
    ts = [t for t, _ in drone_ned]
    d_h = []; d_3 = []; bearings = []
    for t, dp in drone_ned:
        ip = _interp_ned(intr_ned, t)
        if ip is None:
            continue
        relN, relE, relD = ip[0] - dp[0], ip[1] - dp[1], ip[2] - dp[2]
        dh = math.hypot(relN, relE)
        d_h.append((t, dh)); d_3.append(math.sqrt(relN * relN + relE * relE + relD * relD))
        bearings.append((t, math.atan2(relE, relN)))
    d_min = round(min(d_3), 3) if d_3 else None
    # t_entry: pierwszy t (rel) z d ∈ band
    t_entry = None
    for t, dh in d_h:
        if band_lo <= dh <= band_hi:
            t_entry = round(t - t0, 3); break
    # okno orbity [t_entry, t_entry+T_orb]
    frac_band = frac_tight = 0.0
    sweep_deg = 0.0
    if t_entry is not None:
        w_lo = t0 + t_entry; w_hi = w_lo + P["T_orb"]
        win = [(t, dh) for t, dh in d_h if w_lo <= t <= w_hi]
        if win:
            frac_band = sum(1 for _, dh in win if band_lo <= dh <= band_hi) / len(win)
            frac_tight = sum(1 for _, dh in win if tlo <= dh <= thi) / len(win)
        # omiatanie: suma |Δbearing| (unwrap) na oknie
        bw = [(t, b) for t, b in bearings if w_lo <= t <= w_hi]
        for i in range(1, len(bw)):
            db = bw[i][1] - bw[i - 1][1]
            while db > math.pi:
                db -= 2 * math.pi
            while db < -math.pi:
                db += 2 * math.pi
            sweep_deg += abs(math.degrees(db))
    sweep_deg = round(sweep_deg, 1)
    # kryteria D6
    a = t_entry is not None and t_entry <= P["entry_max_s"]
    b = frac_band >= 0.85
    c = sweep_deg >= P["sweep_req_deg"]
    dd = (d_min is not None and d_min >= P["d_min_req"])
    e = (refuse_count == 0 and not breach)
    success = bool(a and b and c and dd and e)
    fail_reasons = [n for n, ok in [("a_entry", a), ("b_frac", b), ("c_sweep", c),
                                    ("d_dmin", dd), ("e_refuse_breach", e)] if not ok]
    # ważność V1/V2/V3
    sim_lo = t0; sim_hi = ts[-1]
    n_deep, longest, dsw = _stalls(rtf, sim_lo, sim_hi)
    def _valid(v):
        ok = (timejump == v["timejump"]) and (dsw >= v["dsw_min"])
        if "max_deep_stall" in v:
            ok = ok and (n_deep <= v["max_deep_stall"]) and (longest <= v["longest_stall_s"])
        return ok
    return {
        "t_entry_s": t_entry, "frac_band_6_10": round(frac_band, 4), "frac_tight_7_9": round(frac_tight, 4),
        "sweep_deg": sweep_deg, "d_min_m": d_min, "refuse_count": refuse_count, "breach": bool(breach),
        "success_D6": success, "fail_reasons": fail_reasons,
        "stalls": {"n_deep": n_deep, "longest_s": longest, "dsim_dwall": dsw, "timejump": timejump},
        "valid_V1": _valid(P["V1"]), "valid_V2": _valid(P["V2"]), "valid_V3": _valid(P["V3"]),
    }


# ------------------------------- LIVE (pliki) -------------------------------
def _load_drone_ned(trace_path):
    from common.frames import enu2ned
    out = []
    with open(trace_path) as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("t") == "gt":
                out.append((r["sim"], enu2ned([r["x"], r["y"], r["z"]])))
    out.sort()
    return out


def _load_intr_ned(gt_path):
    out = []
    with open(gt_path) as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("ned"):
                out.append((r["t_sim"], r["ned"]))
    out.sort()
    return out


def _load_rtf(path):
    out = []
    if not os.path.exists(path):
        return out
    with open(path) as f:
        for line in f:
            try:
                r = json.loads(line)
                out.append({"sim": r.get("sim"), "wall": r.get("wall") or r.get("mono"), "rtf": r.get("rtf")})
            except Exception:
                continue
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", required=True)
    ap.add_argument("--gt-intruder", required=True)
    ap.add_argument("--rtf", default=None)
    ap.add_argument("--refuse", type=int, default=0)
    ap.add_argument("--breach", action="store_true")
    ap.add_argument("--timejump", type=int, default=0)
    ap.add_argument("--sim-lo", type=float, default=None)
    ap.add_argument("--sim-hi", type=float, default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    drone = _load_drone_ned(a.trace)
    intr = _load_intr_ned(a.gt_intruder)
    if a.sim_lo is not None:
        drone = [(t, p) for t, p in drone if a.sim_lo <= t <= (a.sim_hi or 1e18)]
    rtf = _load_rtf(a.rtf) if a.rtf else []
    v = judge_episode(drone, intr, rtf, refuse_count=a.refuse, breach=a.breach, timejump=a.timejump)
    json.dump(v, open(a.out, "w"), indent=2)
    print(json.dumps(v))
