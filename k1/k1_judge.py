#!/usr/bin/env python3
"""
k1_judge.py — sędzia K1 (PRE_K1 §3.2). ZAMROŻONY commitem PRZED pierwszym bootem; hash w ANEKS_K1-1.

Liczy metryki kontrastu osłona (S) vs natywny failsafe PX4 (N) pod utratą GNSS, na parze
(bieg, punkt wstrzyknięcia). GT = pozycja drona z gz (ground truth, ENU sim-time). ulog = PX4.

WEJŚCIE (kontrakt, spełniany przez harness §2 — zamrożony tu):
  --gt <gt.jsonl>     : strumień GT z gz, sim-time. Rekord: {"sim":<s>, "x":E, "y":N, "z":U}
                        (ENU: x=Wschód, y=Północ, z=Góra — konwencja gz, jak gt_judge r03).
                        Opcjonalnie filtr rekordów t=="gt".
  --ulog <f.ulg>      : PX4 ulog tego bootu (vehicle_status, vehicle_local_position,
                        vehicle_command_ack, estimator_status_flags).
  --t-inj <sim_s>     : sim-time wstrzyknięcia EKF2_GPS_CTRL=0 (stempel harnessu, sim-time).
  --arm N|S           : ramię.
  --px4-inj-us <us>   : (opc.) hrt ulog w chwili wstrzyknięcia — pin ulog→sim. Gdy brak:
                        ramię N pinuje po acku NAV_LAND (δ=0); ramię S WYMAGA --px4-inj-us.
  --home E,N          : (opc.) home ENU. Gdy brak — estymowany z okna nieruchomego przed t-inj.
  --refuse-sim <s>    : (opc., ramię S) sim-time zdarzenia REFUSE (z logu agenta/harnessu).
  --ekf <ekf.jsonl>   : (opc., ramię S) strumień EKF (jak gt_judge) do ε_pos na touchdown.

METRYKI (per bieg): r_max, r_td, x_exc, t_td, breach(r_max>R_E), sekwencja nav_state z czasami,
  t_xy_valid_off (rel. wstrzyknięcia), ack NAV_LAND; dla S: t_refuse, ε_pos_touchdown.

Instrument WYŁĄCZNIE liczy. Unit-test (--selftest): syntetyczna trajektoria GT z podstawionym
home i skewem czasu → znane r_max/x_exc/r_td/t_td. PASS wymagany ZANIM policzy cokolwiek na danych.
"""
import sys, os, json, math, argparse

# R_E — jedyne źródło prawdy: r01/config.py (frozen, NIETYKANY). Import + asercja wartości.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from r01.config import R_E as _R_E
    R_E = float(_R_E)
except Exception:                    # środowisko bez r01 na ścieżce — fallback z jawnym źródłem
    R_E = 32.0                        # source: r01/config.py R_E (frozen)
assert abs(R_E - 32.0) < 1e-9, f"R_E z r01 != 32.0 (={R_E}) — koperta zmieniona, STOP"

GROUND_EPS_U   = 0.5      # [m Up] próg touchdownu (GT z ≤ próg po locie)
AIRBORNE_U     = 1.0      # [m Up] uznanie 'był w powietrzu' przed touchdownem
HOME_STILL_V   = 0.3      # [m/s] okno nieruchome do estymaty home
GT_MATCH_TOL_S = 0.5      # tolerancja dopasowania czasu GT
NAV_NAMES = {0:"MANUAL",1:"ALTCTL",2:"POSCTL",3:"AUTO_MISSION",4:"AUTO_LOITER",
             5:"AUTO_RTL",10:"ACRO",12:"DESCEND",14:"OFFBOARD",17:"AUTO_PRECLAND",18:"AUTO_LAND"}
VEHICLE_CMD_NAV_LAND = 21


# ----------------------------- GT (ground truth, sim-time) -----------------------------

def load_gt(path):
    """Wczytuje strumień GT jsonl (ENU: x=E, y=N, z=U), sim-time. Sortuje po 'sim'."""
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if "t" in r and r["t"] != "gt":
                continue
            if "sim" not in r or "x" not in r or "y" not in r:
                continue
            rows.append(r)
    rows.sort(key=lambda r: r["sim"])
    return rows


def _interp_xy(rows, t):
    """Liniowa interpolacja (E,N,U) GT do sim-time t; None poza tolerancją. rows sort po sim."""
    n = len(rows)
    if n == 0:
        return None
    lo, hi = 0, n
    while lo < hi:
        mid = (lo + hi) // 2
        if rows[mid]["sim"] < t:
            lo = mid + 1
        else:
            hi = mid
    i = lo
    if i == 0:
        g = rows[0]
        return (g["x"], g["y"], g.get("z", 0.0)) if abs(g["sim"] - t) <= GT_MATCH_TOL_S else None
    if i >= n:
        g = rows[-1]
        return (g["x"], g["y"], g.get("z", 0.0)) if abs(g["sim"] - t) <= GT_MATCH_TOL_S else None
    a, b = rows[i - 1], rows[i]
    gap = b["sim"] - a["sim"]
    if gap <= 0:
        return (a["x"], a["y"], a.get("z", 0.0))
    w = (t - a["sim"]) / gap
    return (a["x"] + w * (b["x"] - a["x"]),
            a["y"] + w * (b["y"] - a["y"]),
            a.get("z", 0.0) + w * (b.get("z", 0.0) - a.get("z", 0.0)))


def _estimate_home(gt, t_inj):
    """Home ENU = mediana (x,y) GT w oknie nieruchomym (|v|<HOME_STILL_V) przed t_inj.
    Fallback: pierwsza próbka. (Dron startuje z home; przed ruchem xy≈home.)"""
    pre = [r for r in gt if r["sim"] < t_inj]
    if len(pre) < 2:
        g = gt[0]
        return (g["x"], g["y"])
    still = []
    for i in range(1, len(pre)):
        dt = pre[i]["sim"] - pre[i - 1]["sim"]
        if dt > 1e-3:
            v = math.hypot(pre[i]["x"] - pre[i - 1]["x"], pre[i]["y"] - pre[i - 1]["y"]) / dt
            if v < HOME_STILL_V:
                still.append((pre[i]["x"], pre[i]["y"]))
    src = still if len(still) >= 2 else [(r["x"], r["y"]) for r in pre]
    xs = sorted(p[0] for p in src)
    ys = sorted(p[1] for p in src)
    med = lambda s: s[len(s) // 2] if len(s) % 2 else 0.5 * (s[len(s) // 2 - 1] + s[len(s) // 2])
    return (med(xs), med(ys))


def _touchdown(gt, t_inj):
    """Pierwszy sim>t_inj z GT z≤GROUND_EPS_U po tym jak był ≥AIRBORNE_U. (sim, (E,N,U)) lub None."""
    airborne = False
    for r in gt:
        if r["sim"] < t_inj:
            if r.get("z", 0.0) >= AIRBORNE_U:
                airborne = True
            continue
        if r.get("z", 0.0) >= AIRBORNE_U:
            airborne = True
        if airborne and r.get("z", 0.0) <= GROUND_EPS_U:
            return (r["sim"], (r["x"], r["y"], r.get("z", 0.0)))
    return None


def gt_metrics(gt, t_inj, home=None):
    """r_max/r_td/x_exc/t_td/breach z GT (post-wstrzyknięcie). Promień od home; x_exc od punktu inj."""
    if not gt:
        raise ValueError("pusty strumień GT")
    if home is None:
        home = _estimate_home(gt, t_inj)
    hx, hy = home
    inj = _interp_xy(gt, t_inj)
    if inj is None:
        raise ValueError(f"brak próbki GT przy t_inj={t_inj} (±{GT_MATCH_TOL_S}s)")
    ix, iy, _ = inj

    epi = [r for r in gt if r["sim"] >= t_inj]      # epizod = odpowiedź failsafe po wstrzyknięciu
    if not epi:
        raise ValueError("brak próbek GT po t_inj")
    r_from_home = lambda r: math.hypot(r["x"] - hx, r["y"] - hy)
    d_from_inj  = lambda r: math.hypot(r["x"] - ix, r["y"] - iy)

    r_max = max(r_from_home(r) for r in epi)
    r_max_t = max(epi, key=r_from_home)["sim"] - t_inj
    x_exc = max(d_from_inj(r) for r in epi)

    td = _touchdown(gt, t_inj)
    if td is not None:
        t_touch, (tx, ty, _) = td
        r_td = math.hypot(tx - hx, ty - hy)
        t_td = t_touch - t_inj
    else:
        r_td = None
        t_td = None

    return {
        "home_enu": (round(hx, 3), round(hy, 3)),
        "inj_xy_enu": (round(ix, 3), round(iy, 3)),
        "r_max": round(r_max, 3),
        "r_max_rel_t_s": round(r_max_t, 3),
        "r_td": round(r_td, 3) if r_td is not None else None,
        "x_exc": round(x_exc, 3),
        "t_td_s": round(t_td, 3) if t_td is not None else None,
        "breach": bool(r_max > R_E),
        "R_E": R_E,
        "touchdown_found": td is not None,
        "n_gt": len(gt), "n_epi": len(epi),
    }


# ----------------------------- ulog (PX4) -----------------------------

def read_ulog(path):
    """Czyta z ulogu potrzebne topiki. Zwraca dict topic->{field:list}. Defensywnie (brak topiku→{})."""
    from pyulog import ULog
    want = {
        "vehicle_status": ["timestamp", "nav_state"],
        "vehicle_local_position": ["timestamp", "xy_valid", "v_xy_valid"],
        "vehicle_command_ack": ["timestamp", "command", "result"],
        "estimator_status_flags": ["timestamp", "cs_inertial_dead_reckoning"],
    }
    ul = ULog(path, list(want.keys()))
    out = {}
    for d in ul.data_list:
        if d.name not in want:
            continue
        cols = {}
        for fld in want[d.name]:
            if fld in d.data:
                cols[fld] = list(d.data[fld])
        out.setdefault(d.name, cols)
    # snapshot parametrów (część wyniku, PRE §2)
    params = {}
    try:
        params = {k: ul.initial_parameters.get(k) for k in
                  ("EKF2_GPS_CTRL", "COM_POS_LOW_ACT", "COM_POS_FS_EPH", "MPC_LAND_SPEED",
                   "EKF2_HGT_REF", "COM_OF_LOSS_T")}
    except Exception:
        pass
    return out, params


def _transitions(ts, vals):
    """Lista (t_us, val) w punktach zmiany val."""
    out = []
    prev = object()
    for t, v in zip(ts, vals):
        if v != prev:
            out.append((t, v))
            prev = v
    return out


def ulog_events(ud, offset_s, t_inj):
    """Wyprowadza zdarzenia ulogu w sim-time względem wstrzyknięcia. offset_s: sim = us/1e6+offset_s."""
    to_sim = lambda us: us / 1e6 + offset_s
    rel = lambda us: round(to_sim(us) - t_inj, 3)
    ev = {"offset_s": round(offset_s, 6)}

    vs = ud.get("vehicle_status", {})
    if "nav_state" in vs:
        seq = [(rel(t), int(v), NAV_NAMES.get(int(v), str(int(v))))
               for (t, v) in _transitions(vs["timestamp"], vs["nav_state"])]
        ev["nav_state_seq"] = seq

    lp = ud.get("vehicle_local_position", {})
    if "xy_valid" in lp:
        off = None
        for t, xv in zip(lp["timestamp"], lp["xy_valid"]):
            if to_sim(t) >= t_inj and not xv:
                off = rel(t)
                break
        ev["t_xy_valid_off_rel_s"] = off

    es = ud.get("estimator_status_flags", {})
    if "cs_inertial_dead_reckoning" in es:
        on = None
        for t, dr in zip(es["timestamp"], es["cs_inertial_dead_reckoning"]):
            if to_sim(t) >= t_inj and dr:
                on = rel(t)
                break
        ev["t_dead_reckoning_on_rel_s"] = on

    ack = ud.get("vehicle_command_ack", {})
    if "command" in ack:
        lands = [(rel(t), int(res)) for (t, c, res) in
                 zip(ack["timestamp"], ack["command"], ack["result"])
                 if int(c) == VEHICLE_CMD_NAV_LAND and to_sim(t) >= t_inj - 1.0]
        ev["nav_land_ack"] = lands[0] if lands else None
    return ev


def _land_ack_us(ud):
    """hrt (us) pierwszego acku NAV_LAND — do pinowania ulog→sim dla ramienia N (δ=0)."""
    ack = ud.get("vehicle_command_ack", {})
    if "command" not in ack:
        return None
    for t, c in zip(ack["timestamp"], ack["command"]):
        if int(c) == VEHICLE_CMD_NAV_LAND:
            return t
    return None


# ----------------------------- ε_pos touchdown (ramię S) -----------------------------

def eps_pos_touchdown(ekf_path, gt, t_touch):
    """ε_pos = ||e(touchdown) − e0|| (ramię S, D13). e(t)=EKF_ned − GT_ned; GT ENU→NED: north=y, east=x.
    Parowanie EKF↔GT po MONO (wspólny zegar odbioru — EKF ma mono+ts px4, NIE sim); e0 = baseline
    zdrowego okna (pierwsze BASE_WIN_S) usuwa stały offset ramki home↔gz-world. Zwraca ε_pos [m] lub None."""
    BASE_WIN_S = 5.0
    ekf = []
    with open(ekf_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("t") == "ekf" and "mono" in r and "x" in r and "y" in r:
                ekf.append(r)
    return _eps_core(ekf, gt, t_touch, BASE_WIN_S)


def _eps_core(ekf, gt, t_touch, BASE_WIN_S=5.0):
    gtm = [g for g in gt if "mono" in g]
    if not ekf or not gtm:
        return None
    ekf.sort(key=lambda r: r["mono"])
    gtm.sort(key=lambda r: r["mono"])

    def e_vec(er, gr):
        return (er["x"] - gr["y"], er["y"] - gr["x"])     # NED − (ENU→NED swap): north=gr.y, east=gr.x

    def nearest_gt(mono):
        return min(gtm, key=lambda r: abs(r["mono"] - mono))

    # baseline e0 z pierwszych BASE_WIN_S (zawis w home — stały offset ramki)
    t0 = ekf[0]["mono"]
    base = [e_vec(e, nearest_gt(e["mono"])) for e in ekf if e["mono"] <= t0 + BASE_WIN_S]
    if not base:
        base = [e_vec(ekf[0], nearest_gt(ekf[0]["mono"]))]
    e0 = (sum(b[0] for b in base) / len(base), sum(b[1] for b in base) / len(base))

    # touchdown mono z wiersza GT najbliższego t_touch (sim)
    gt_td = min(gt, key=lambda r: abs(r.get("sim", 1e18) - t_touch))
    tm = gt_td.get("mono")
    if tm is None:
        return None
    e = min(ekf, key=lambda r: abs(r["mono"] - tm))
    g = nearest_gt(tm)
    ev = e_vec(e, g)
    return round(math.hypot(ev[0] - e0[0], ev[1] - e0[1]), 3)


# ----------------------------- assemble -----------------------------

def judge(args):
    gt = load_gt(args.gt)
    home = None
    if args.home:
        hx, hy = [float(v) for v in args.home.split(",")]
        home = (hx, hy)
    m = gt_metrics(gt, args.t_inj, home=home)
    res = {"arm": args.arm, "t_inj_sim": args.t_inj, **m}
    if args.point is not None:
        res["point"] = args.point

    if args.ulog:
        ud, params = read_ulog(args.ulog)
        # pin ulog→sim
        if args.px4_inj_us is not None:
            offset = args.t_inj - args.px4_inj_us / 1e6
            pin = "px4_inj_us"
        elif args.arm == "N":
            la = _land_ack_us(ud)
            if la is None:
                raise ValueError("ramię N bez acku NAV_LAND w ulogu i bez --px4-inj-us — nie mogę pinować")
            offset = args.t_inj - la / 1e6     # δ=0: land ack ≈ t_inj
            pin = "nav_land_ack"
        else:
            raise ValueError("ramię S wymaga --px4-inj-us do pinowania ulog→sim")
        res["ulog"] = ulog_events(ud, offset, args.t_inj)
        res["ulog"]["pin"] = pin
        res["params"] = params

    if args.arm == "S":
        if args.refuse_sim is not None:
            res["t_refuse_rel_s"] = round(args.refuse_sim - args.t_inj, 3)
        if args.ekf and m["touchdown_found"]:
            td = _touchdown(gt, args.t_inj)
            res["eps_pos_touchdown_m"] = eps_pos_touchdown(args.ekf, gt, td[0])
    return res


# ----------------------------- UNIT-TEST -----------------------------

def _sample_waypoints(wps, dt, skew):
    """Próbkuje piecewise-liniowo listę waypointów [(sim,x,y,z)] co dt (gwarantuje próbkę w każdym
    wierzchołku). Oś sim przesunięta o skew. Zwraca rekordy GT."""
    rows = []
    for k in range(len(wps) - 1):
        t0, x0, y0, z0 = wps[k]
        t1, x1, y1, z1 = wps[k + 1]
        span = t1 - t0
        n = max(1, int(round(span / dt)))
        for i in range(n):                       # [t0, t1) — wierzchołek t1 wchodzi w następnym segmencie
            f = i / n
            rows.append({"t": "gt", "sim": round(skew + t0 + i * dt, 4),
                         "x": x0 + (x1 - x0) * f, "y": y0 + (y1 - y0) * f,
                         "z": z0 + (z1 - z0) * f})
    tN, xN, yN, zN = wps[-1]                      # ostatni wierzchołek
    rows.append({"t": "gt", "sim": round(skew + tN, 4), "x": xN, "y": yN, "z": zN})
    rows.sort(key=lambda r: r["sim"])
    return rows


def _synth_gt(home=(0.0, 0.0), inj=(2.0, 1.0), escape=(6.0, 8.0), skew=0.0, dt=0.1):
    """Syntetyczna trajektoria GT (ENU) z WAYPOINTÓW (próbka dokładnie w każdym wierzchołku):
      zawis w home 0..20 s → przelot do inj @25 s (t_inj) → ucieczka o `escape` @31 s (6 s) →
      zejście z ALT do 0 @39 s (8 s). home/inj podstawiane; `skew` przesuwa całą oś sim.
    Oczekiwania liczone TĄ SAMĄ regułą co sędzia (touchdown: z≤GROUND_EPS_U)."""
    ALT = 10.0
    hx, hy = home
    ix, iy = inj
    ex, ey = escape
    fx, fy = ix + ex, iy + ey
    t_inj = 25.0
    wps = [(0.0, hx, hy, ALT), (20.0, hx, hy, ALT), (25.0, ix, iy, ALT),
           (31.0, fx, fy, ALT), (39.0, fx, fy, 0.0)]
    rows = _sample_waypoints(wps, dt, skew)
    # touchdown: z(t)=ALT*(1-(t-31)/8) na zejściu; z≤GROUND_EPS_U przy (t-31)/8 ≥ 1-EPS/ALT
    f_td = 1.0 - GROUND_EPS_U / ALT
    t_touch = 31.0 + 8.0 * f_td
    # zaokrąglij do siatki próbek (pierwsza próbka ≥ t_touch)
    t_touch = 31.0 + dt * math.ceil((t_touch - 31.0) / dt)
    exp = {
        "home": home,
        "t_inj_sim": skew + t_inj,
        "inj_xy": (ix, iy),
        "x_exc": math.hypot(ex, ey),                # maks oddalenie od inj = |escape|
        "r_max": math.hypot(fx - hx, fy - hy),      # najdalszy = koniec ucieczki (kolumna zejścia)
        "r_td": math.hypot(fx - hx, fy - hy),
        "t_td": round(t_touch - t_inj, 3),
        "breach": math.hypot(fx - hx, fy - hy) > R_E,
    }
    return rows, exp


def selftest():
    print("=== K1-JUDGE UNIT-TEST: syntetyka GT z podstawionym home i skewem ===")
    ok = True
    cases = [("skew=0, home/inj podstawione", 0.0),
             ("skew=+37.5s (przesunięta oś sim)", 37.5),
             ("skew=-12.3s", -12.3)]
    for name, skew in cases:
        rows, exp = _synth_gt(skew=skew)
        m = gt_metrics(rows, exp["t_inj_sim"], home=exp["home"])
        checks = {
            "x_exc": abs(m["x_exc"] - exp["x_exc"]) < 0.02,
            "r_max": abs(m["r_max"] - exp["r_max"]) < 0.02,
            "r_td":  m["r_td"] is not None and abs(m["r_td"] - exp["r_td"]) < 0.02,
            "t_td":  m["t_td_s"] is not None and abs(m["t_td_s"] - exp["t_td"]) < 0.11,
            "inj_xy": abs(m["inj_xy_enu"][0] - exp["inj_xy"][0]) < 0.02
                      and abs(m["inj_xy_enu"][1] - exp["inj_xy"][1]) < 0.02,
            "breach": m["breach"] == exp["breach"],   # geometria domyślna: r_max≈10.05 < R_E
        }
        c = all(checks.values())
        ok = ok and c
        print(f"-- {name}")
        print(f"   x_exc got={m['x_exc']} exp≈{round(exp['x_exc'],3)} | r_max got={m['r_max']} "
              f"exp≈{round(exp['r_max'],3)} | r_td got={m['r_td']} | t_td got={m['t_td_s']} "
              f"exp≈{exp['t_td']} | {'PASS' if c else 'FAIL '+str(checks)}")

    # home-estymacja (bez podania home): musi odtworzyć home z okna nieruchomego
    rows, exp = _synth_gt(skew=0.0)
    m = gt_metrics(rows, exp["t_inj_sim"], home=None)
    che = abs(m["home_enu"][0] - exp["home"][0]) < 0.05 and abs(m["home_enu"][1] - exp["home"][1]) < 0.05
    ok = ok and che
    print(f"-- estymacja home (bez --home): got={m['home_enu']} exp={exp['home']} "
          f"{'PASS' if che else 'FAIL'}")

    # breach TRUE gdy ucieczka > R_E
    rows, exp = _synth_gt(inj=(0.0, 0.0), escape=(30.0, 20.0), home=(0.0, 0.0), skew=0.0)
    m = gt_metrics(rows, exp["t_inj_sim"], home=(0.0, 0.0))
    cb = m["breach"] is True and m["r_max"] > R_E
    ok = ok and cb
    print(f"-- breach TRUE gdy r_max>{R_E}: r_max={m['r_max']} breach={m['breach']} "
          f"{'PASS' if cb else 'FAIL'}")

    # ε_pos (ramię S): stały offset ramki off + dryf przy touchdown → ε = ||dryf||
    off_n, off_e = 0.4, -0.3          # offset home↔world (NED)
    dn, de = 1.5, 2.0                 # dryf EKF przy touchdown
    gtE, gtN = 2.0, 1.0               # GT stały ENU (E,N) → NED (north=1, east=2)
    ekf, gtl = [], []
    dt = 0.1
    for i in range(200):              # 0..20 s
        t = round(i * dt, 4)
        drift = (i >= 150)            # dryf od 15 s (touchdown ~19.9 s)
        ekf.append({"t": "ekf", "mono": t,
                    "x": gtN + off_n + (dn if drift else 0.0),      # NED north
                    "y": gtE + off_e + (de if drift else 0.0)})     # NED east
        gtl.append({"t": "gt", "mono": t, "sim": 1000.0 + t, "x": gtE, "y": gtN, "z": 5.0})
    eps = _eps_core(ekf, gtl, t_touch=1000.0 + 19.9)
    ce = eps is not None and abs(eps - math.hypot(dn, de)) < 0.02
    ok = ok and ce
    print(f"-- ε_pos (offset ramki usunięty, dryf {math.hypot(dn,de):.2f}): got={eps} "
          f"exp={round(math.hypot(dn,de),3)} {'PASS' if ce else 'FAIL'}")

    print(f"\nWYNIK: {'PASS — sędzia zwalidowany, wolno liczyć biegi K1' if ok else 'FAIL — NIE liczyć'}")
    return ok


def main():
    ap = argparse.ArgumentParser(description="k1_judge (PRE_K1 §3.2)")
    ap.add_argument("--gt")
    ap.add_argument("--ulog")
    ap.add_argument("--t-inj", type=float, dest="t_inj")
    ap.add_argument("--arm", choices=["N", "S"])
    ap.add_argument("--px4-inj-us", type=float, dest="px4_inj_us", default=None)
    ap.add_argument("--home", default=None)
    ap.add_argument("--point", type=float, default=None, help="ułamek nogi (0.2..0.8) — metadana parowania")
    ap.add_argument("--refuse-sim", type=float, dest="refuse_sim", default=None)
    ap.add_argument("--ekf", default=None)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if not (a.gt and a.t_inj is not None and a.arm):
        ap.error("wymagane: --gt --t-inj --arm (albo --selftest)")
    res = judge(a)
    if a.json:
        print(json.dumps(res))
    else:
        for k, v in res.items():
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()
