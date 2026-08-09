#!/usr/bin/env python3
"""
B1-bis GT-JUDGE (R-2) — sędzia dryfu pozycji z jawną korelacją osi ENU/NED.

Kanały (etykiety przyrządów):
  EKF = vehicle_local_position  (NED: x=Północ, y=Wschód)   etykieta 'nav-local'
  GT  = gz model -p             (ENU: x=Wschód,  y=Północ)   etykieta 'gt_judge'
  Δt  = monotonic_local

KORELACJA OSI (obowiązkowa, R-2): GT ENU → NED horyzontalnie:
  north_gt = gt.y ;  east_gt = gt.x
Błąd poziomy:  e(t) = ( ekf.x - north_gt , ekf.y - east_gt )
Dryf względem bazy (usuwa stały offset origin EKF-home vs gz-world):
  drift(t) = || e(t) - e0 ||,  e0 = średnia e po zdrowym oknie tuż przed dead_reckoning.

max_drift  = max drift(t) w oknie DR
plateau    = średnia drift(t) po transiencie (ostatnie PLATEAU_TAIL_S s okna DR)
t_do_plateau = pierwszy czas, gdy drift(t) ≥ PLATEAU_FRAC * plateau (i już nie spada poniżej)
resets     = (max xy_reset_counter, max z_reset_counter) w oknie DR jeśli w danych (R-1)

Instrument WYŁĄCZNIE liczy — GT jest sędzią, nie wchodzi w decyzję runtime.
Unit-test (--selftest): syntetyka, znany błąd → znany wynik, OBA układy osi. PASS wymagany
ZANIM policzy cokolwiek na danych lotu.
"""
import sys, json, math, argparse

GT_MATCH_TOL_S = 0.5      # GT ~5 Hz: dopuszczalne dopasowanie czasowe do próbki EKF
T_HOME_WINDOW_S = 20.0    # §3bis: okno zdrowego GPS do estymaty T_home (≥20 s, stały na epizod)
HEALTHY_P95_GATE_M = 0.10 # §3bis/W5: bramka instrumentu p95(ε_pos) w oknie zdrowym
PLATEAU_TAIL_S = 15.0     # ogon okna DR do średniej plateau
PLATEAU_FRAC   = 0.90     # próg t_do_plateau
SKEW_GRID_S    = [i / 100.0 for i in range(-50, 51, 2)]  # -0.5..0.5 s, krok 0.02 (detekcja skew)
V_GATE_MS      = 1.0      # bramka W5 liczona na próbkach |v|<V_GATE (izoluje fidelity kanału od v·Δt)
EPISODE_MARKS_S = [2, 5, 10, 20]  # profil dryfu wczesnego epizodu (operacyjny vs długie okno)


def enu_to_ned_horiz(gt_x_enu, gt_y_enu):
    """GT ENU (x=Wschód, y=Północ) -> (north, east) w konwencji NED."""
    north = gt_y_enu
    east  = gt_x_enu
    return north, east


GT_INTERP_MAX_GAP_S = 2.0   # max luka między próbkami GT do interpolacji liniowej


def _nearest_gt(gt_rows, t):
    """Najbliższa próbka GT do czasu t (mono), w granicy GT_MATCH_TOL_S; else None."""
    best = None
    bestdt = GT_MATCH_TOL_S
    for g in gt_rows:
        dt = abs(g["mono"] - t)
        if dt <= bestdt:
            bestdt = dt
            best = g
    return best


def _interp_gt(gt_rows, t):
    """
    Liniowa interpolacja GT (x,y) do czasu t — usuwa szum time-matching przy ruchu
    (GT rzadkie ~2 Hz, dron ~1.5 m/s → nearest-neighbor wstrzykuje do v·Δt błędu).
    Wymaga pary otaczającej w granicy GT_INTERP_MAX_GAP_S; poza zakresem -> nearest fallback.
    gt_rows posortowane po mono.
    """
    n = len(gt_rows)
    if n == 0:
        return None
    # binary search: pierwszy indeks o mono >= t
    lo, hi = 0, n
    while lo < hi:
        mid = (lo + hi) // 2
        if gt_rows[mid]["mono"] < t:
            lo = mid + 1
        else:
            hi = mid
    i = lo
    if i == 0:
        g = gt_rows[0]
        return (g["x"], g["y"]) if abs(g["mono"] - t) <= GT_MATCH_TOL_S else None
    if i >= n:
        g = gt_rows[-1]
        return (g["x"], g["y"]) if abs(g["mono"] - t) <= GT_MATCH_TOL_S else None
    a, b = gt_rows[i - 1], gt_rows[i]
    gap = b["mono"] - a["mono"]
    if gap > GT_INTERP_MAX_GAP_S:
        g = _nearest_gt(gt_rows, t)
        return (g["x"], g["y"]) if g else None
    if gap <= 0:
        return (a["x"], a["y"])
    w = (t - a["mono"]) / gap
    return (a["x"] + w * (b["x"] - a["x"]), a["y"] + w * (b["y"] - a["y"]))


def load(path, time_key="mono"):
    """Wczytuje jsonl. time_key wybiera oś czasu parowania: 'mono' (stary B1) lub 'sim'
    (B1-bis streaming: px4/sim time == gz sim-time w lockstep). Kopiuje do 'mono' downstream."""
    ekf, gt = [], []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if time_key != "mono" and time_key in r:
                r["mono"] = r[time_key]
            if r.get("t") == "ekf":
                ekf.append(r)
            elif r.get("t") == "gt":
                gt.append(r)
    ekf.sort(key=lambda r: r["mono"])
    gt.sort(key=lambda r: r["mono"])
    return ekf, gt


def _median(xs):
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return None
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def align_by_sim(ekf, gt):
    """
    B1-bis (§3bis): parowanie po SIM-time ze stempli u źródła.
      ekf.ts = px4 sek (epoch-offset, lockstep); gt.sim = gz sim sek.
    Gross offset (stały, lockstep) = median(ekf.ts − gt.sim) po parach dopasowanych po mono odbioru.
    Ustawia 'mono' := zaligowany sim (ekf: ts−gross; gt: sim). Residualny skew < 1 s → estymator skew.
    Zwraca gross_offset (lub None gdy brak native stempli).
    """
    if not ekf or not gt or "ts" not in ekf[0] or "sim" not in gt[0]:
        return None
    gt_by_mono = sorted(gt, key=lambda r: r["mono"])
    offs = []
    for e in ekf:
        # najbliższy gt po mono odbioru
        g = _nearest_gt([{"mono": r["mono"]} for r in gt_by_mono], e["mono"])
        if g is None:
            continue
        # znajdź realny wiersz gt o tym mono
        # (mapowanie: bisekcja)
        lo, hi = 0, len(gt_by_mono)
        while lo < hi:
            mid = (lo + hi) // 2
            if gt_by_mono[mid]["mono"] < g["mono"]:
                lo = mid + 1
            else:
                hi = mid
        if lo < len(gt_by_mono) and abs(gt_by_mono[lo]["mono"] - e["mono"]) <= 0.1:
            offs.append(e["ts"] - gt_by_mono[lo]["sim"])
    gross = _median(offs)
    if gross is None:
        return None
    for e in ekf:
        e["mono"] = round(e["ts"] - gross, 4)
    for g in gt:
        g["mono"] = round(g["sim"], 4)
    ekf.sort(key=lambda r: r["mono"])
    gt.sort(key=lambda r: r["mono"])
    return gross


def _paired_series(ekf, gt, swap, tshift=0.0):
    """Seria (t, ex, ey): ekf sparowany z GT interpolowanym w czasie (t+tshift). tshift do
    de-skew. swap=True -> poprawna korelacja ENU/NED (R-2)."""
    series = []
    for r in ekf:
        g = _interp_gt(gt, r["mono"] + tshift)
        if g is None:
            continue
        gx, gy = g
        if swap:
            north_gt, east_gt = gy, gx      # ENU.y=Północ, ENU.x=Wschód
        else:
            north_gt, east_gt = gx, gy      # BŁĄD: brak swapa
        series.append((r["mono"], r["x"] - north_gt, r["y"] - east_gt))
    return series


def estimate_skew(ekf, gt, t_end, swap=True, grid=SKEW_GRID_S):
    """
    Estymuje skew stempla GT vs EKF na oknie ZDROWYM (t < t_end), gdzie prawdziwe ε≈0,
    więc każdy błąd = skew × prędkość. Dla każdego tshift liczy RMS(ε − mean) (mean = T_home
    dla danego tshift) i zwraca tshift minimalizujący residuum.
    Zwraca (skew_hat_s, resid_rms_at_skew, resid_rms_at_zero).
    """
    def resid_rms(tshift):
        s = [(ex, ey) for (t, ex, ey) in _paired_series(ekf, gt, swap, tshift) if t < t_end]
        if len(s) < 2:
            return None
        mx = sum(a for a, _ in s) / len(s)
        my = sum(b for _, b in s) / len(s)
        return (sum((a - mx) ** 2 + (b - my) ** 2 for a, b in s) / len(s)) ** 0.5

    best_tau, best = 0.0, None
    for tau in grid:
        r = resid_rms(tau)
        if r is None:
            continue
        if best is None or r < best:
            best, best_tau = r, tau
    r0 = resid_rms(0.0)
    return best_tau, (round(best, 4) if best is not None else None), (round(r0, 4) if r0 is not None else None)


def _gt_speed_lookup(gt):
    """Prędkość drona z kolejnych próbek GT (ENU, własny mono). Zwraca posortowaną listę (t, |v|)."""
    gs = sorted(gt, key=lambda r: r["mono"])
    pts = []
    for i in range(1, len(gs)):
        dt = gs[i]["mono"] - gs[i - 1]["mono"]
        if dt > 1e-3:
            v = math.hypot(gs[i]["x"] - gs[i - 1]["x"], gs[i]["y"] - gs[i - 1]["y"]) / dt
            pts.append((0.5 * (gs[i]["mono"] + gs[i - 1]["mono"]), v))
    return pts


def _speed_at(pts, t):
    if not pts:
        return 0.0
    lo, hi = 0, len(pts)
    while lo < hi:
        mid = (lo + hi) // 2
        if pts[mid][0] < t:
            lo = mid + 1
        else:
            hi = mid
    cands = []
    if lo < len(pts):
        cands.append(pts[lo])
    if lo > 0:
        cands.append(pts[lo - 1])
    return min(cands, key=lambda p: abs(p[0] - t))[1] if cands else 0.0


def _p95(xs):
    s = sorted(xs)
    return s[int(0.95 * (len(s) - 1))] if s else None


def compute_drift(ekf, gt, swap=True):
    """Zwraca dict metryk. swap=True -> poprawna korelacja ENU/NED (R-2).
    Parowanie: MONO (jeden zegar; native px4/gz DRYFUJĄ ~0.77% — sim-align odrzucony) + korekta
    skew (stała latencja odbioru). Bramka W5 na próbkach |v|<V_GATE (v·Δt-odporna)."""
    dr = [r for r in ekf if r.get("dead_reckoning")]
    if not dr:
        raise ValueError("brak próbek dead_reckoning=True (okno DR puste)")
    t_dr0 = dr[0]["mono"]
    t_dr1 = dr[-1]["mono"]

    # skew stempla (na oknie zdrowym) — zastosuj TYLKO gdy obserwowalny i pomaga (v≈0 → ill-posed)
    skew_hat, skew_resid, resid_at_zero = estimate_skew(ekf, gt, t_dr0, swap)
    apply_skew = (resid_at_zero is not None and skew_resid is not None
                  and (resid_at_zero - skew_resid) > 0.02 and skew_resid < 0.8 * resid_at_zero)
    tshift = skew_hat if apply_skew else 0.0

    series = _paired_series(ekf, gt, swap, tshift)
    if not series:
        raise ValueError("brak sparowanych próbek EKF/GT")
    spts = _gt_speed_lookup(gt)

    # T_home (§3bis): STAŁY offset ramki home↔gz-world z okna zdrowego ≥ T_HOME_WINDOW_S przed DR.
    # Przy zdrowym GPS EKF śledzi truth do cm ⇒ T_home = -home_ned = offset ramki, NIE błąd EKF.
    # Trzymany stały na cały epizod (skoki EKF po resecie w oknie DR liczą się w pełni jako ε).
    base = [(ex, ey) for (t, ex, ey) in series if t_dr0 - T_HOME_WINDOW_S <= t < t_dr0]
    if len(base) < 2:
        base = [(ex, ey) for (t, ex, ey) in series if t < t_dr0] or \
               [(series[0][1], series[0][2])]
    thx = sum(b[0] for b in base) / len(base)   # T_home w osi Północ
    thy = sum(b[1] for b in base) / len(base)   # T_home w osi Wschód
    t_home_window_s = round((t_dr0 - min(t for (t, _, _) in series if t < t_dr0)), 1) \
        if any(t < t_dr0 for (t, _, _) in series) else 0.0

    # ε_pos w oknie zdrowym po odjęciu T_home. Bramka W5 na próbkach |v|<V_GATE (fidelity kanału,
    # v·Δt-odporna); pełna p95 raportowana informacyjnie (przy v_max zdominowana jitterem stempla).
    healthy = [(t, math.hypot(ex - thx, ey - thy)) for (t, ex, ey) in series if t < t_dr0]
    healthy_all = [d for (_, d) in healthy]
    healthy_lowv = [d for (t, d) in healthy if _speed_at(spts, t) < V_GATE_MS]
    healthy_p95_full = _p95(healthy_all)
    healthy_p95 = _p95(healthy_lowv) if healthy_lowv else healthy_p95_full  # metryka bramki
    healthy_max = max(healthy_all) if healthy_all else None

    # ε_pos(t) w oknie DR = ||e(t) - T_home||  (T_home stały)
    dr_series = [(t, math.hypot(ex - thx, ey - thy))
                 for (t, ex, ey) in series if t_dr0 <= t <= t_dr1]
    if not dr_series:
        raise ValueError("brak próbek w oknie DR po sparowaniu")

    max_drift = max(d for (_, d) in dr_series)
    tail = [d for (t, d) in dr_series if t >= t_dr1 - PLATEAU_TAIL_S]
    plateau = sum(tail) / len(tail) if tail else max_drift

    # profil dryfu wczesnego epizodu (operacyjny REFUSE→Land ≈ sekundy) vs długie okno
    episode = {}
    for sec in EPISODE_MARKS_S:
        near = [(abs((t - t_dr0) - sec), d) for (t, d) in dr_series if (t - t_dr0) <= sec + 1.0]
        episode[f"drift_at_{sec}s"] = round(min(near)[1], 4) if near else None

    # ABSOLUTNY |e(t)| bez odjęcia bazy (styl ANEKS-2) — do rekoncyliacji, NIE do capa
    abs_dr = [math.hypot(ex, ey) for (t, ex, ey) in series if t_dr0 <= t <= t_dr1]
    max_abs_err = max(abs_dr) if abs_dr else None

    # t_do_plateau: pierwszy czas, gdy drift ≥ PLATEAU_FRAC*plateau i pozostaje
    thr = PLATEAU_FRAC * plateau
    t_plat = None
    for i, (t, d) in enumerate(dr_series):
        if d >= thr and all(dd >= thr * 0.8 for (_, dd) in dr_series[i:]):
            t_plat = t - t_dr0
            break

    # monotoniczność (SR-B6): czy rośnie przez całe okno bez plateau?
    n = len(dr_series)
    last_third = dr_series[int(2 * n / 3):]
    first_third = dr_series[:max(1, int(n / 3))]
    mono_growth = (sum(d for _, d in last_third) / len(last_third)
                   > 1.10 * (sum(d for _, d in first_third) / len(first_third))) if last_third and first_third else False

    # resets (R-1) jeśli w danych
    xy_rc = [r["xy_reset_counter"] for r in dr if "xy_reset_counter" in r]
    z_rc = [r["z_reset_counter"] for r in dr if "z_reset_counter" in r]
    resets = {
        "xy_reset_span": (max(xy_rc) - min(xy_rc)) if xy_rc else None,
        "z_reset_span": (max(z_rc) - min(z_rc)) if z_rc else None,
    }

    healthy_valid = (healthy_p95 is not None and healthy_p95 <= HEALTHY_P95_GATE_M)

    out = {
        "swap": swap,
        "n_ekf": len(ekf), "n_gt": len(gt), "n_paired": len(series),
        "dr_window_s": round(t_dr1 - t_dr0, 3),
        "max_drift": round(max_drift, 4),          # ε_pos = ||e - T_home|| (§3bis) — DO CAPA (D10)
        "plateau": round(plateau, 4),
        "t_do_plateau_s": round(t_plat, 3) if t_plat is not None else None,
        "max_abs_err": round(max_abs_err, 4) if max_abs_err is not None else None,  # |e| bez T_home
        # bramka instrumentu (§3bis / W5) — na |v|<V_GATE (fidelity kanału):
        "healthy_p95_eps": round(healthy_p95, 4) if healthy_p95 is not None else None,
        "healthy_p95_full": round(healthy_p95_full, 4) if healthy_p95_full is not None else None,
        "healthy_max_eps": round(healthy_max, 4) if healthy_max is not None else None,
        "healthy_valid": healthy_valid,            # p95(|v|<V_GATE) ≤ 0.10 m ?
        "v_gate_ms": V_GATE_MS,
        "t_home_window_s": t_home_window_s,
        "T_home": (round(thx, 3), round(thy, 3)),  # offset ramki (Północ, Wschód)
        "skew_hat_s": skew_hat, "skew_applied": apply_skew,
        "skew_resid_rms": skew_resid,               # residuum po de-skew
        "resid_rms_at_zero": resid_at_zero,         # residuum bez de-skew (motion×skew)
        "mono_growth_tail_vs_head": mono_growth,    # SR-B6: rośnie przez całe okno?
        "resets": resets,
    }
    out.update(episode)   # profil dryfu wczesnego epizodu (drift_at_{2,5,10,20}s)
    return out


# ----------------------------- UNIT-TEST (R-2) -----------------------------

def _synth(drift_n, drift_e, truth_move_n, truth_move_e, woff=(7.0, -3.0), home=(1.5, 2.5)):
    """
    Syntetyka: faza zdrowa (drift=0) + faza DR (drift stały drift_n/drift_e; truth przesuwa
    się o truth_move_n/truth_move_e liniowo). Zwraca listę rekordów jsonl-like (ekf+gt).
    Prawda w NED: north_true(t), east_true(t).  GT ENU: x=east, y=north (+woff world origin).
    EKF NED local: x=north-home_n+drift_n, y=east-home_e+drift_e.
    """
    WOFF_N, WOFF_E = woff
    HOME_N, HOME_E = home
    rows = []
    dt = 0.05  # 20 Hz EKF
    N_HEALTHY = 80   # 4 s zdrowe
    N_DR = 200       # 10 s DR
    # GT co-timed z EKF (dt=0 w parowaniu) — unit-test izoluje LOGIKĘ SWAPA, nie 5 Hz GT.
    # (realizm 5 Hz GT obsługuje GT_MATCH_TOL_S na danych lotu.)
    def emit(t, nt, et, dr):
        rows.append({"t": "ekf", "mono": round(t, 4),
                     "x": nt - HOME_N + (drift_n if dr else 0.0),
                     "y": et - HOME_E + (drift_e if dr else 0.0),
                     "dead_reckoning": dr})
        rows.append({"t": "gt", "mono": round(t, 4),
                     "x": et + WOFF_E, "y": nt + WOFF_N, "z": 5.0})
    # faza zdrowa: truth statyczny w (0,0), drift 0
    for i in range(N_HEALTHY):
        emit(i * dt, 0.0, 0.0, False)
    # faza DR: truth przesuwa się liniowo, drift stały (plateau) od razu
    t0 = N_HEALTHY * dt
    for i in range(N_DR):
        frac = i / (N_DR - 1)
        emit(t0 + i * dt, truth_move_n * frac, truth_move_e * frac, True)
    return rows


def _synth_skew(v_north, gt_skew, drift_n=0.5, woff=(7.0, -3.0), home=(1.5, 2.5)):
    """
    Syntetyka RUCHOMA z wstrzykniętym skewem stempla GT (Olga p.3).
    Faza zdrowa: truth porusza się w Północy trójkątnie (±v_north, noga 4 s) przez 30 s
    (≥20 s na T_home). GT stemplowany PÓŹNO o gt_skew (próbka niosąca truth(t) ma mono=t+gt_skew).
    Faza DR: 6 s, drift_n stały. Zwraca rekordy jsonl-like.
    Instrument POWINIEN: skew_hat ≈ gt_skew, resid_at_skew ≈ 0, resid_at_zero ≈ |v·gt_skew| ≫ 0.
    """
    WOFF_N, WOFF_E = woff
    HOME_N, HOME_E = home
    rows = []
    dt = 0.05
    leg = 4.0
    T_HEALTHY = 30.0
    T_DR = 6.0

    def north_of(t):
        # trójkąt: prędkość ±v_north, zmiana co `leg`
        cyc = int(t // leg)
        base = 0.0
        # zsumuj przebyte nogi
        for k in range(cyc):
            base += (v_north * leg) * (1 if k % 2 == 0 else -1)
        frac = t - cyc * leg
        sign = 1 if cyc % 2 == 0 else -1
        return base + sign * v_north * frac

    n_h = int(T_HEALTHY / dt)
    for i in range(n_h):
        t = i * dt
        nt = north_of(t)
        rows.append({"t": "ekf", "mono": round(t, 4), "x": nt - HOME_N, "y": -HOME_E,
                     "dead_reckoning": False})
        rows.append({"t": "gt", "mono": round(t + gt_skew, 4),
                     "x": 0.0 + WOFF_E, "y": nt + WOFF_N, "z": 5.0})
    t0 = T_HEALTHY
    n_d = int(T_DR / dt)
    for i in range(n_d):
        t = t0 + i * dt
        nt = north_of(t)
        rows.append({"t": "ekf", "mono": round(t, 4), "x": nt - HOME_N + drift_n, "y": -HOME_E,
                     "dead_reckoning": True})
        rows.append({"t": "gt", "mono": round(t + gt_skew, 4),
                     "x": 0.0 + WOFF_E, "y": nt + WOFF_N, "z": 5.0})
    return rows


def selftest():
    ok = True
    cases = []

    # CASE 1: dryf 2.0 m Północ, truth przesuwa 5.0 m Północ w oknie DR.
    #  swap  -> max_drift = 2.0
    #  noswap-> max przy Δ=5:  sqrt((Δ+drift)^2 + Δ^2) = sqrt(7^2+5^2)=sqrt(74)=8.6023
    rows = _synth(drift_n=2.0, drift_e=0.0, truth_move_n=5.0, truth_move_e=0.0)
    ekf = [r for r in rows if r["t"] == "ekf"]
    gt = [r for r in rows if r["t"] == "gt"]
    s = compute_drift(ekf, gt, swap=True)
    ns = compute_drift(ekf, gt, swap=False)
    exp_swap, exp_noswap = 2.0, math.sqrt(74)
    c1 = abs(s["max_drift"] - exp_swap) < 0.02 and abs(ns["max_drift"] - exp_noswap) < 0.03
    cases.append(("C1 dryf 2.0 N / truth 5.0 N", s["max_drift"], exp_swap,
                  ns["max_drift"], round(exp_noswap, 4), c1))
    ok = ok and c1

    # CASE 2: dryf 1.5 m Wschód, truth przesuwa 3.0 m Wschód.
    #  swap  -> 1.5
    #  noswap-> max przy ΔE=3: sqrt(ΔE^2 + (ΔE+drift)^2)=sqrt(9+20.25)=sqrt(29.25)=5.4083
    rows = _synth(drift_n=0.0, drift_e=1.5, truth_move_n=0.0, truth_move_e=3.0)
    ekf = [r for r in rows if r["t"] == "ekf"]
    gt = [r for r in rows if r["t"] == "gt"]
    s = compute_drift(ekf, gt, swap=True)
    ns = compute_drift(ekf, gt, swap=False)
    exp_swap, exp_noswap = 1.5, math.sqrt(29.25)
    c2 = abs(s["max_drift"] - exp_swap) < 0.02 and abs(ns["max_drift"] - exp_noswap) < 0.03
    cases.append(("C2 dryf 1.5 E / truth 3.0 E", s["max_drift"], exp_swap,
                  ns["max_drift"], round(exp_noswap, 4), c2))
    ok = ok and c2

    # CASE 3: zero dryfu, truth przesuwa 6.0 N -> swap MUSI dać ~0 (truth znosi się),
    #  noswap da spurious sqrt(6^2+6^2)=8.485 (dowód że brak swapa myli ruch z błędem).
    rows = _synth(drift_n=0.0, drift_e=0.0, truth_move_n=6.0, truth_move_e=0.0)
    ekf = [r for r in rows if r["t"] == "ekf"]
    gt = [r for r in rows if r["t"] == "gt"]
    s = compute_drift(ekf, gt, swap=True)
    ns = compute_drift(ekf, gt, swap=False)
    exp_swap, exp_noswap = 0.0, math.sqrt(72)
    c3 = abs(s["max_drift"] - exp_swap) < 0.02 and abs(ns["max_drift"] - exp_noswap) < 0.03
    cases.append(("C3 zero dryf / truth 6.0 N", s["max_drift"], exp_swap,
                  ns["max_drift"], round(exp_noswap, 4), c3))
    ok = ok and c3

    print("=== GT-JUDGE UNIT-TEST (R-2): znany błąd -> znany wynik, oba układy osi ===")
    print(f"{'case':32} {'swap_got':>9} {'swap_exp':>9} {'noswap_got':>11} {'noswap_exp':>11}  PASS")
    for name, sg, se, ng, ne, c in cases:
        print(f"{name:32} {sg:9.4f} {se:9.4f} {ng:11.4f} {ne:11.4f}  {'PASS' if c else 'FAIL'}")

    # CASE 4 (RUCHOMA + SKEW, Olga p.3): znane v=1.5 m/s, wstrzyknięty skew stempla GT = 0.16 s.
    #  Instrument MUSI: skew_hat ≈ 0.16, resid_at_skew ≈ 0, resid_at_zero ≫ 0 (≈ v·skew).
    print("\n=== CASE 4: syntetyka RUCHOMA — detekcja skew stempla GT ===")
    skew4 = []
    for inj in (0.16, -0.10):
        rows = _synth_skew(v_north=1.5, gt_skew=inj)
        ekf = [r for r in rows if r["t"] == "ekf"]
        gt = [r for r in rows if r["t"] == "gt"]
        res = compute_drift(ekf, gt, swap=True)
        detected = res["skew_hat_s"]
        resid = res["skew_resid_rms"]
        rz = res["resid_rms_at_zero"]
        c = (abs(detected - inj) <= 0.02 and resid < 0.02 and rz > 0.08)
        skew4.append(c)
        print(f"  inj_skew={inj:+.2f}s  skew_hat={detected:+.2f}s  resid@skew={resid:.4f}  "
              f"resid@0={rz:.4f}  {'PASS' if c else 'FAIL'}")
    c4 = all(skew4)
    ok = ok and c4

    print(f"\nWYNIK: {'PASS — instrument zwalidowany (swap+skew), wolno liczyć B1-bis' if ok else 'FAIL — NIE liczyć danych'}")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonl", nargs="?", help="plik lotu jsonl (ekf+gt)")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json", action="store_true", help="wynik jako JSON")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if not a.jsonl:
        ap.error("podaj plik jsonl albo --selftest")
    ekf, gt = load(a.jsonl)
    # UWAGA: NIE align_by_sim — native px4/gz DRYFUJĄ ~0.77% (offset +0.96 s / 125 s). Parowanie MONO
    # (jeden zegar) + korekta skew (stała latencja odbioru). Diagnostyka: patrz FINDING_clock.
    res = compute_drift(ekf, gt, swap=True)
    res_ns = compute_drift(ekf, gt, swap=False)
    res["max_drift_NOSWAP_sanity"] = res_ns["max_drift"]
    if a.json:
        print(json.dumps(res))
    else:
        print(f"== {a.jsonl} ==")
        for k, v in res.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
