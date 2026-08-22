"""W2(c) (PRE_K1 / ANEKS_K1-2): punkt wstrzyknięcia SCEN∈{S2,S3,S4} identyczny przed i po dodaniu
gałęzi SCEN=K1 do r03/gate_run_r03.py. Czysta replika logiki triggera (bez importu gate — ROS deps).
Także: W2(b) — sha256 modułów osłony zgodne z zapięciem."""
import os, sys, math

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "k1"))


# --- replika triggera SPRZED zmiany (baseline 6db3393) ---
def trigger_old(scen, denial_done, seg_i, dist, now, denial_at):
    if scen == "S4":
        return (not denial_done) and seg_i >= 1 and dist < 3.0 and now >= 8.0
    else:
        return (not denial_done) and now >= denial_at


# --- replika triggera PO zmianie (0ce4d8e, z gałęzią K1) ---
def trigger_new(scen, denial_done, seg_i, dist, now, denial_at, wps, k1_point):
    if scen == "S4":
        return (not denial_done) and seg_i >= 1 and dist < 3.0 and now >= 8.0
    elif scen == "K1":
        _leg = math.hypot(wps[1][0] - wps[0][0], wps[1][1] - wps[0][1])
        _fa = (_leg - dist) / _leg if (seg_i == 1 and _leg > 1e-6) else -1.0
        return (not denial_done) and seg_i == 1 and _fa >= k1_point
    else:
        return (not denial_done) and now >= denial_at


WPS = [(14.07, 14.07), (14.07, -14.07), (-14.07, -14.07), (-14.07, 14.07)]  # corner_waypoints_r03 (NED)


def test_injection_point_S2_S3_S4_unchanged():
    """Dla S2/S3/S4 trigger identyczny old vs new na siatce (denial_done, seg_i, dist, now)."""
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


def test_K1_is_new_branch_only():
    """K1 wyzwala się TYLKO na seg_i==1 przy ułamku nogi — i nie zmienia gałęzi S*."""
    leg = math.hypot(WPS[1][0] - WPS[0][0], WPS[1][1] - WPS[0][1])   # 2*14.07 ≈ 28.14
    # na seg_i==1: f_along = (leg-dist)/leg; próg 0.5 → dist ≤ leg*0.5
    fired = trigger_new("K1", False, 1, dist=leg * 0.4, now=0, denial_at=1e9, wps=WPS, k1_point=0.5)
    notyet = trigger_new("K1", False, 1, dist=leg * 0.6, now=0, denial_at=1e9, wps=WPS, k1_point=0.5)
    assert fired is True and notyet is False
    # nie odpala na seg_i != 1
    assert trigger_new("K1", False, 0, dist=0.1, now=0, denial_at=1e9, wps=WPS, k1_point=0.5) is False
    assert trigger_new("K1", False, 2, dist=0.1, now=0, denial_at=1e9, wps=WPS, k1_point=0.5) is False


def test_shield_pins_frozen():
    """W2(b): sha256 modułów osłony zgodne z zapięciem (shield.py/config.py/gate)."""
    import k1_shield_pins as SP
    frozen, detail = SP.check_shield_frozen()
    assert frozen, f"osłona niezamrożona: {[k for k,v in detail.items() if not v['ok']]}"
