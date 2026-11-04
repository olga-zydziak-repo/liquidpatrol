#!/usr/bin/env python3
"""results/KONT_RECON/tools/kont_r3_eps.py — R3 PROMPT_KONT_S0: krzywe eps(t) od chwili utraty GNSS.

Instrument = gt_judge.py IMPORTEM (FROZEN 447efaa2): compute_drift daje T_home i skew, _paired_series
parę EKF/GT; tu tylko próbkowanie krzywej po siatce czasu. Krzyżowo: max(krzywa) == max_drift sędziego
(rozjazd > 0.01 m ⇒ assert). Obok krzywej znaczniki fazy lotu, bo długie okno B1-bis NIE jest lotem:
  t_xy_invalid  pierwsza próbka xy_valid=False po utracie,
  t_ground      pierwsza chwila, od której GT stoi (|Δxy|<2 cm/s i z<0.5 m) do końca okna DR,
  eps_at        eps przy kolejnych sekundach.
Bieg K2: dead_reckoning nie jest w wierszach ławki — okno DR wyznacza zdarzenie denial i REALNE przyziemienie
z GT (z<0.2 m); zdarzenie "touchdown" uprzęży to koniec profilu komend (GT z≈2 m, 9.83 s). Flaga wstrzyknięta
do kopii wierszy w pamięci.
Wyjście: results/KONT_RECON/r3_eps.json
"""
import glob
import hashlib
import json
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
B = os.path.join(ROOT, "results", "R03", "recon", "B1bis")
sys.path.insert(0, os.path.join(B, "instrument"))
import gt_judge as J

GT_SHA8 = "447efaa2"
GRID = 0.25
RUNS = [("hover", "flights/f1_hover"), ("hover", "flights/f2_hover"),
        ("straight_long", "flights/f3_straight"), ("straight_long", "flights/f4_straight120"),
        ("corner_long", "flights/f5_corner"),
        ("ep_straight", "episode/g1_straight"), ("ep_straight", "episode/p_s1_straight"),
        ("ep_straight", "episode/p_s2_straight"),
        ("ep_corner", "episode/c1_corner"), ("ep_corner", "episode/c2_corner"),
        ("ep_corner", "episode/p_c1_corner"), ("ep_corner", "episode/p_c2_corner"),
        ("ep_corner", "episode/p_c3_corner")]


def curve(ekf, gt):
    m = J.compute_drift(ekf, gt)
    thx, thy = m["T_home"]
    ts = m["skew_hat_s"] if m["skew_applied"] else 0.0
    dr = [r for r in ekf if r.get("dead_reckoning")]
    t0, t1 = dr[0]["mono"], dr[-1]["mono"]
    s = [(t - t0, math.hypot(ex - thx, ey - thy))
         for (t, ex, ey) in J._paired_series(ekf, gt, True, ts) if t0 <= t <= t1]
    assert abs(max(d for _, d in s) - m["max_drift"]) < 0.01, (max(d for _, d in s), m["max_drift"])
    return m, t0, t1, s


def sample(s, tmax):
    out, i, n = [], 0, int(tmax / GRID) + 1
    for k in range(n):
        tk = k * GRID
        while i + 1 < len(s) and s[i + 1][0] <= tk:
            i += 1
        if s[i][0] <= tk + GRID:
            out.append([round(tk, 2), round(s[i][1], 3)])
    return out


def t_ground(gt, t0, t1):
    g = [r for r in gt if t0 <= r["mono"] <= t1]
    tg = None
    for a, b in zip(reversed(g[:-1]), reversed(g[1:])):
        dt = b["mono"] - a["mono"]
        if dt <= 0:
            continue
        v = math.hypot(b["x"] - a["x"], b["y"] - a["y"]) / dt
        if b["z"] < 0.5 and v < 0.25:
            tg = a["mono"] - t0
        else:
            break
    return round(tg, 2) if tg is not None else None


def one(prof, name, ekf, gt):
    m, t0, t1, s = curve(ekf, gt)
    fv = [r["mono"] - t0 for r in ekf if t0 <= r["mono"] <= t1 and r.get("xy_valid") is False]
    tg = t_ground(gt, t0, t1)
    at = {str(k): next((round(d, 3) for t, d in s if t >= k), None)
          for k in (1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 30, 60)}
    flight = [(t, d) for t, d in s if tg is None or t <= tg]
    return {"profile": prof, "run": name, "max_drift_sedzia": m["max_drift"], "dr_window_s": m["dr_window_s"],
            "healthy_valid": m["healthy_valid"], "healthy_p95": m["healthy_p95_eps"], "T_home": m["T_home"],
            "skew_applied": m["skew_applied"], "skew_hat_s": m["skew_hat_s"], "resets": m["resets"],
            "t_xy_invalid_s": round(fv[0], 2) if fv else None, "t_ground_s": tg,
            "eps_at": at, "max_eps_w_locie": round(max(d for _, d in flight), 3),
            "curve": sample(s, min(t1 - t0, 60.0))}


def k2_runs():
    out = []
    for d in sorted(glob.glob(os.path.join(ROOT, "results", "K2", "k2c_b*"))):
        p = os.path.join(d, "trace.jsonl")
        if not os.path.isfile(p):
            continue
        ekf, gt = [], []
        denial = None; td = None; sc = None
        for l in open(p):
            try:
                r = json.loads(l)
            except Exception:
                continue
            if r.get("t") == "event" and r.get("ev") == "denial":
                denial = r["mono"]
            if r.get("t") == "event" and r.get("ev") == "touchdown":
                td = r["mono"]
            if r.get("t") == "event" and r.get("ev") == "episode_start":
                sc = r.get("scenario_id")
            if r.get("t") == "ekf":
                ekf.append(r)
            elif r.get("t") == "gt":
                gt.append(r)
        if denial is None or td is None:
            continue
        gt.sort(key=lambda r: r["mono"])
        land = next((r["mono"] for r in gt if r["mono"] > denial and r["z"] < 0.2), td + 0.5)
        for r in ekf:
            r["dead_reckoning"] = denial <= r["mono"] <= land
        ekf.sort(key=lambda r: r["mono"]); gt.sort(key=lambda r: r["mono"])
        rec = one("k2_orbita_D5", os.path.basename(d) + ":" + str(sc), ekf, gt)
        rec["t_koniec_profilu_s"] = round(td - denial, 2)
        rec["t_gt_przyziemienie_s"] = round(land - denial, 2)
        out.append(rec)
    return out


def main():
    got = hashlib.sha256(open(os.path.join(B, "instrument", "gt_judge.py"), "rb").read()).hexdigest()[:8]
    assert got == GT_SHA8, got
    res, skipped = [], []
    for prof, name in RUNS:
        ekf, gt = J.load(os.path.join(B, name + ".jsonl"))
        try:
            res.append(one(prof, name, ekf, gt))
        except ValueError as e:            # bieg bez okna DR: nie ma czego mierzyć, odnotowany, nie liczony
            skipped.append({"run": name, "powod": str(e)})
    res += k2_runs()
    json.dump({"gt_judge_sha8": got, "grid_s": GRID, "runs": res, "pominiete": skipped},
              open(os.path.join(ROOT, "results", "KONT_RECON", "r3_eps.json"), "w"), ensure_ascii=False, indent=0)
    print("pominiete:", skipped)
    print(f"{'bieg':34s} {'max':>6s} {'xyinv':>5s} {'tgnd':>6s} " + " ".join(f"{k:>5s}" for k in "1 2 3 4 5 6 8 10 12 15 20".split()))
    for r in res:
        print(f"{r['run'][:34]:34s} {r['max_drift_sedzia']:6.2f} {str(r['t_xy_invalid_s']):>5s} {str(r['t_ground_s']):>6s} " +
              " ".join(f"{(r['eps_at'][k] if r['eps_at'][k] is not None else float('nan')):5.2f}" for k in "1 2 3 4 5 6 8 10 12 15 20".split()))


main()
