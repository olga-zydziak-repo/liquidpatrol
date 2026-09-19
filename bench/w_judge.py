#!/usr/bin/env python3
"""bench/w_judge.py — sędzia nogi W (wiatr). GLUE nad bench_judge (NIETKNIĘTY) + GT; DOKŁADA pola.

PRE_W §5/§6. Rdzeń = klasyfikacja REFUSE(POS_DEGRADED) w epizodzie BEZ denialu:
  FAŁSZYWY  ⇔ mediana |pos_EKF − pos_GT| z ostatnich 20 ticków (1 s) przed tripem  <  ε_false=2.0 m
  PRAWDZIWY ⇔ ≥ 2.0 m  (brzeg: dokładnie 2.0 = PRAWDZIWY, reguła `>=`)
GT wyłącznie sędzią (reguła 8). EKF w NED (VehicleLocalPosition), GT w ENU (dynamic_pose) →
GT konwertowane enu2ned (jak bench_judge). Flagi (nie bramki): ground-speed GT vs V_ENV=6.0,
r_max vs R_E=32, zużycie EPS_CAP=9.25. Rozkład per-kierunek względny (tailwind/headwind/crosswind)
z faz orbity. bench_judge.judge_episode wywoływany dla werdyktu bazowego; w_judge tylko dopisuje w_*.

Freeze hashem = FREEZE_W (ANEKS_W-1), przed pierwszym bootem kryterialnym.
"""
import os, sys, json, math

EPS_FALSE = 2.0          # PRE §5 (ZAMROŻONE ANEKS_W-0)
V_ENV = 6.0              # k1_finalize.py:113 (FLAGA, Q10)
R_E = 32.0              # r01/config.py:30
EPS_CAP = 9.25          # r03/config.py:20
WIN_S = 1.0             # okno przed tripem (1 s)
N_TICKS = 20            # maks. ticków w oknie


# ---------- czyste helpery (testowane) ----------
def _median(xs):
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return None
    m = n // 2
    return s[m] if n % 2 else 0.5 * (s[m - 1] + s[m])


def _enu2ned(x, y, z):
    # zgodne z common.frames.enu2ned: (E,N,U) -> (N,E,D)
    return [y, x, -z]


def _nearest(rows, mono, key_x=("x", "y")):
    """Najbliższy wiersz po 'mono'."""
    best = None; bd = None
    for r in rows:
        d = abs(r["mono"] - mono)
        if bd is None or d < bd:
            bd = d; best = r
    return best


def median_err_before_trip(ekf_rows, gt_rows, trip_mono, window_s=WIN_S, n_max=N_TICKS):
    """Mediana poziomego |EKF−GT| (NED) z do n_max ticków EKF w [trip_mono-window_s, trip_mono]."""
    win = [r for r in ekf_rows if trip_mono - window_s <= r["mono"] <= trip_mono]
    win.sort(key=lambda r: r["mono"])
    win = win[-n_max:]
    errs = []
    for e in win:
        g = _nearest(gt_rows, e["mono"])
        if g is None:
            continue
        gned = _enu2ned(g["x"], g["y"], g["z"])
        # EKF już w NED: x=N, y=E
        errs.append(math.hypot(e["x"] - gned[0], e["y"] - gned[1]))
    return _median(errs), len(errs)


def classify(median_err, eps_false=EPS_FALSE):
    """PRE §5: >= eps_false ⇒ PRAWDZIWY; < ⇒ FALSZYWY. None ⇒ NIEROZSTRZYGNIETE."""
    if median_err is None:
        return "NIEROZSTRZYGNIETE"
    return "PRAWDZIWY" if median_err >= eps_false else "FALSZYWY"


def rel_direction(vel_xy, wind_xy):
    """Kierunek WZGLĘDNY wiatru do wektora prędkości: tailwind/headwind/crosswind.
    Kąt między vel a wind: <45° tailwind (wiatr w plecy, zgodny z ruchem), >135° headwind, else crosswind.
    Zdegenerowane (|vel|~0 lub |wind|~0) ⇒ 'none'."""
    vn = math.hypot(vel_xy[0], vel_xy[1]); wn = math.hypot(wind_xy[0], wind_xy[1])
    if vn < 1e-6 or wn < 1e-6:
        return "none"
    cos = (vel_xy[0] * wind_xy[0] + vel_xy[1] * wind_xy[1]) / (vn * wn)
    cos = max(-1.0, min(1.0, cos))
    ang = math.degrees(math.acos(cos))
    if ang < 45.0:
        return "tailwind"
    if ang > 135.0:
        return "headwind"
    return "crosswind"


# ---------- ładowanie trace ----------
def _load(trace_path):
    ekf, gt, ev = [], [], []
    with open(trace_path, errors="replace") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                r = json.loads(ln)
            except Exception:
                continue
            t = r.get("t")
            if t == "ekf":
                ekf.append(r)
            elif t == "gt":
                gt.append(r)
            elif t == "event":
                ev.append(r)
    return ekf, gt, ev


def judge_trace(trace_path, wind_vec_enu=(0.0, 0.0, 0.0), gt_intr_path=None, rtf_path=None):
    """Werdykt bazowy (bench_judge, jeśli dostępny) + pola w_*. wind_vec_enu = wektor świata (ENU)."""
    ekf, gt, ev = _load(trace_path)
    wind_ned = _enu2ned(*wind_vec_enu)  # do rel_direction (spójne z EKF/GT NED)

    # REFUSE(POS) — klasyfikacja §5
    refuses = []
    for e in ev:
        if e.get("ev") == "refuse" and e.get("reason") in ("POS_DEGRADED", "pos_degraded"):
            trip_mono = e.get("mono")
            med, n = median_err_before_trip(ekf, gt, trip_mono) if trip_mono is not None else (None, 0)
            refuses.append({"episode_id": e.get("episode_id"), "trip_mono": trip_mono,
                            "median_err_m": (round(med, 4) if med is not None else None),
                            "n_ticks": n, "verdict": classify(med)})

    # flagi z GT (ground-speed, r_max) — GT ENU; prędkość z różnicowania GT
    gt_sorted = sorted(gt, key=lambda r: r.get("sim", r["mono"]))
    gspeed_max = 0.0; r_max = 0.0
    for a, b in zip(gt_sorted, gt_sorted[1:]):
        dt = (b.get("sim", 0) - a.get("sim", 0)) or (b["mono"] - a["mono"])
        if dt and dt > 1e-3:
            v = math.hypot(b["x"] - a["x"], b["y"] - a["y"]) / dt
            gspeed_max = max(gspeed_max, v)
    for g in gt_sorted:
        r_max = max(r_max, math.hypot(g["x"], g["y"]))

    # rozkład per-kierunek (z GT: prędkość chwilowa vs wiatr)
    dir_counts = {"tailwind": 0, "headwind": 0, "crosswind": 0, "none": 0}
    for a, b in zip(gt_sorted, gt_sorted[1:]):
        dt = (b.get("sim", 0) - a.get("sim", 0))
        if dt and dt > 1e-3:
            vel_enu = [(b["x"] - a["x"]) / dt, (b["y"] - a["y"]) / dt]
            dir_counts[rel_direction(vel_enu, list(wind_vec_enu[:2]))] += 1

    w_block = {
        "eps_false_m": EPS_FALSE, "window_s": WIN_S, "n_ticks_max": N_TICKS,
        "wind_vec_enu": list(wind_vec_enu),
        "refuses": refuses,
        "n_refuse": len(refuses),
        "n_refuse_false": sum(1 for r in refuses if r["verdict"] == "FALSZYWY"),
        "n_refuse_true": sum(1 for r in refuses if r["verdict"] == "PRAWDZIWY"),
        "flag_gspeed_gt_max": round(gspeed_max, 3),
        "flag_gspeed_over_venv": bool(gspeed_max > V_ENV),
        "flag_r_max": round(r_max, 3),
        "flag_r_margin_to_re": round(R_E - r_max, 3),
        "flag_eps_cap_used": round(max(0.0, r_max - (R_E - EPS_CAP)), 3),
        "dir_dist": dir_counts,
        "V_ENV": V_ENV, "R_E": R_E, "EPS_CAP": EPS_CAP,
    }

    base = None
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        import bench.bench_judge as BJ
        drone_ned = BJ._load_drone_ned(trace_path)
        intr_ned = BJ._load_intr_ned(gt_intr_path) if gt_intr_path and os.path.exists(gt_intr_path) else []
        rtf = BJ._load_rtf(rtf_path) if rtf_path and os.path.exists(rtf_path) else None
        base = BJ.judge_episode(drone_ned, intr_ned, rtf=rtf,
                                refuse_count=len(refuses), breach=False, timejump=0)
    except Exception as e:
        base = {"_bench_judge_error": repr(e)}

    return {"base": base, "w": w_block}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", required=True)
    ap.add_argument("--wind", default="0,0,0", help="wektor ENU vx,vy,vz")
    ap.add_argument("--gt-intr", default=None)
    ap.add_argument("--rtf", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    wind = tuple(float(x) for x in a.wind.split(","))
    res = judge_trace(a.trace, wind_vec_enu=wind, gt_intr_path=a.gt_intr, rtf_path=a.rtf)
    s = json.dumps(res, indent=2)
    if a.out:
        open(a.out, "w").write(s)
    print(s)
