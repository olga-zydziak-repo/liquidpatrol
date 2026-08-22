"""W2(c) (PRE_K1 / ANEKS_K1-2): punkt wstrzyknięcia SCEN∈{S2,S3,S4} identyczny przed i po dodaniu
gałęzi SCEN=K1 do r03/gate_run_r03.py. Czysta replika logiki triggera (bez importu gate — ROS deps).
Także: W2(b) — sha256 modułów osłony zgodne z zapięciem.
ANEKS_K1-6 F2: naprawa defektu stale-dist (K1_POINT ignorowany) — replika = kod naprawiony; test
trajektorii syntetycznej dla K1_POINT∈{0.2,0.35,0.5,0.65,0.8} + wariant narożnikowy (|f−K1_POINT|≤0.02);
tożsamość gałęzi K1 w OBU ramionach (k1_arm_n.py ≡ gate_run_r03.py)."""
import os, sys, math

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "k1"))

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WPS = [(14.07, 14.07), (14.07, -14.07), (-14.07, -14.07), (-14.07, 14.07)]  # corner_waypoints_r03 (NED)
K1_POINTS = [0.2, 0.35, 0.5, 0.65, 0.8]


# --- replika triggera SPRZED zmiany K1 (baseline 6db3393; brak gałęzi K1) ---
def trigger_old(scen, denial_done, seg_i, dist, now, denial_at):
    if scen == "S4":
        return (not denial_done) and seg_i >= 1 and dist < 3.0 and now >= 8.0
    else:
        return (not denial_done) and now >= denial_at


# --- replika triggera PO naprawie (ANEKS_K1-6 F2, z gałęzią K1 = f_along względem AKTUALNEGO celu) ---
def trigger_new(scen, denial_done, seg_i, dist, now, denial_at, wps=None, k1_point=0.5, pos=None):
    if scen == "S4":
        return (not denial_done) and seg_i >= 1 and dist < 3.0 and now >= 8.0
    elif scen == "K1":
        _leg = math.hypot(wps[1][0] - wps[0][0], wps[1][1] - wps[0][1])
        _cur = wps[seg_i % len(wps)]
        _cur_dist = math.hypot(_cur[0] - pos[0], _cur[1] - pos[1])
        _fa = (_leg - _cur_dist) / _leg if (seg_i == 1 and _leg > 1e-6) else -1.0
        return (not denial_done) and seg_i == 1 and _fa >= k1_point
    else:
        return (not denial_done) and now >= denial_at


def _f_along(seg_i, pos, wps):
    """f_along gałęzi K1 (kod naprawiony) — do sprawdzenia wartości wstrzyknięcia."""
    _leg = math.hypot(wps[1][0] - wps[0][0], wps[1][1] - wps[0][1])
    _cur = wps[seg_i % len(wps)]
    _cur_dist = math.hypot(_cur[0] - pos[0], _cur[1] - pos[1])
    return (_leg - _cur_dist) / _leg if (seg_i == 1 and _leg > 1e-6) else -1.0


def _sim_inject_fa(k1_point, wps=WPS, n_leg=400):
    """Symulacja pętli lotu (inkrementacja seg_i + naprawiony f_along) po trajektorii
    origin→wps[0]→wps[1]. Zwraca (f_along_przy_wstrzyknięciu, seg_i). Mirror pętli obu ramion."""
    def _seg_pts(a, b, n):
        return [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n + 1)]
    path = _seg_pts((0.0, 0.0), wps[0], n_leg) + _seg_pts(wps[0], wps[1], n_leg)[1:]
    seg_i = 0
    for pos in path:
        wp = wps[seg_i % len(wps)]
        dist = math.hypot(wp[0] - pos[0], wp[1] - pos[1])
        if dist < 1.0:
            seg_i += 1
        fa = _f_along(seg_i, pos, wps)
        if seg_i == 1 and fa >= k1_point:
            return fa, seg_i
    return None, seg_i


def test_injection_point_S2_S3_S4_unchanged():
    """F2c: dla S2/S3/S4 trigger identyczny old vs new (naprawa dotknęła WYŁĄCZNIE gałęzi K1)."""
    mismatches = 0
    checked = 0
    for scen in ("S2", "S3", "S4"):
        denial_at = 12.0 if scen in ("S2", "S3") else 1e9
        for denial_done in (False, True):
            for seg_i in range(0, 5):
                for dist in (0.0, 0.5, 1.0, 2.9, 3.0, 5.0, 20.0):
                    for now in (0.0, 7.9, 8.0, 11.9, 12.0, 12.1, 50.0):
                        old = trigger_old(scen, denial_done, seg_i, dist, now, denial_at)
                        new = trigger_new(scen, denial_done, seg_i, dist, now, denial_at, WPS, 0.5)
                        checked += 1
                        if old != new:
                            mismatches += 1
    assert mismatches == 0, f"{mismatches}/{checked} rozbieżności S2/S3/S4 old vs new"
    assert checked > 0


def test_K1_point_honored_on_trajectory():
    """F2a: na trajektorii syntetycznej wstrzyknięcie zachodzi przy f_along ≈ K1_POINT (|Δ|≤0.02)
    dla wszystkich pięciu punktów — NIE przy narożniku (defekt stale-dist naprawiony)."""
    for kp in K1_POINTS:
        fa, seg_i = _sim_inject_fa(kp)
        assert fa is not None, f"K1_POINT={kp}: brak wstrzyknięcia"
        assert seg_i == 1, f"K1_POINT={kp}: wstrzyknięcie poza 1. nogą (seg_i={seg_i})"
        assert abs(fa - kp) <= 0.02, f"K1_POINT={kp}: f_along={fa:.4f} |Δ|={abs(fa-kp):.4f} > 0.02"


def test_K1_corner_variant_not_passthrough():
    """F2a (wariant narożnikowy): na 1. ticku seg_i==1 (przy narożniku-0) f_along ≈ 0, NIE ~0.97 —
    trigger nie odpala natychmiast dla K1_POINT≥0.2 (regresja defektu stale-dist)."""
    # pozycja tuż przed narożnikiem-0 na odcinku origin→wps[0] (dron dolatuje do narożnika)
    corner = WPS[0]
    pos_near_corner = (corner[0] - 0.7 / math.sqrt(2), corner[1] - 0.7 / math.sqrt(2))
    fa = _f_along(1, pos_near_corner, WPS)   # seg_i==1 świeżo po inkrementacji
    assert fa < 0.05, f"narożnik: f_along={fa:.4f} (powinno ≈0, nie ~0.97 defektu)"
    for kp in K1_POINTS:
        assert not (fa >= kp), f"K1_POINT={kp}: odpaliłby przy narożniku (f={fa:.4f})"
    # kontrola pozytywna: STARY (wadliwy) wzór dałby ~0.97 przy tej samej pozycji
    _leg = math.hypot(WPS[1][0] - WPS[0][0], WPS[1][1] - WPS[0][1])
    dist_stale = math.hypot(WPS[0][0] - pos_near_corner[0], WPS[0][1] - pos_near_corner[1])
    fa_bug = (_leg - dist_stale) / _leg
    assert fa_bug > 0.95, f"kontrola: stary wzór f={fa_bug:.4f} (spodziewane ~0.97)"


def _k1_branch_src(path):
    """Wyciąga rdzeń gałęzi K1 (linie z _cur_dist / f_along) z pliku źródłowego."""
    txt = open(os.path.join(_ROOT, path)).read()
    return txt


def test_K1_branch_identical_both_arms():
    """F2a/F2c: OBA ramiona liczą f_along tą samą arytmetyką (naprawiony rdzeń obecny w obu plikach)."""
    core_cur = "_cur = wps[seg_i % len(wps)]"
    core_dist = "_cur_dist = math.hypot(_cur[0] - pos[0], _cur[1] - pos[1])"
    core_fa = "(_leg - _cur_dist) / _leg if (seg_i == 1 and _leg > 1e-6) else -1.0"
    for path in ("k1/k1_arm_n.py", "r03/gate_run_r03.py"):
        src = _k1_branch_src(path)
        assert core_cur in src, f"{path}: brak '{core_cur}'"
        assert core_dist in src, f"{path}: brak '{core_dist}'"
        assert core_fa in src, f"{path}: brak wyrażenia f_along '{core_fa}'"


def test_shield_pins_frozen():
    """W2(b): sha256 modułów osłony zgodne z zapięciem (shield.py/config.py/gate)."""
    import k1_shield_pins as SP
    frozen, detail = SP.check_shield_frozen()
    assert frozen, f"osłona niezamrożona: {[k for k,v in detail.items() if not v['ok']]}"
