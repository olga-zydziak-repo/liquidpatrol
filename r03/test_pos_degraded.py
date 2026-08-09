"""r03/test_pos_degraded.py — testy deterministyczne B2 (bez SITL) dla POS_DEGRADED (R0.3a).

Weryfikuje: (1) debounce (1-tick NIE tripuje, 2-tick tak, dokładnie na progu); (2) histereza
(migotanie < M bez re-ALLOW ani oscylacji; M ciągłego zdrowia → re-ALLOW); (3) brak sprzężenia
z dead-manem (REFUSE(POS) aktywny ⇒ osłona produkuje applied co tick ⇒ streamer żyje);
(4) kompatybilność wstecz (pos_flag=None ⇒ zachowanie r01/r02 bez zmian); (5) priorytet R-POS
poniżej latch, na/ponad R-G.

Uruchom: PYTHONPATH=. python3 -m r03.test_pos_degraded
"""
from __future__ import annotations
from r01.shield import (PatrolShield, ALLOW, HOLD, REFUSE, POS_DEGRADED, GEOFENCE, ABORT,
                        M_PATROL, M_ABORT)

SAFE_POS = (0.0, 0.0, -10.0)      # w kopercie
SAFE_TGT = (1.0, 0.0, -10.0)
SAFE_VEL = (0.0, 0.0, 0.0)
FAR_TGT = (100.0, 0.0, -10.0)     # poza R_E (geofence violation)


def _mk(hyst=5):
    s = PatrolShield()
    s.reset()
    s.pos_debounce_ticks = 2
    s.pos_hyst_ticks = hyst
    return s


def test_debounce_1tick_no_trip():
    s = _mk()
    d = s.step(0, SAFE_POS, SAFE_VEL, SAFE_TGT, pos_flag=True)   # 1 bad tick
    assert d["decision"] == ALLOW, f"1-tick nie powinien tripować, got {d}"
    d = s.step(1, SAFE_POS, SAFE_VEL, SAFE_TGT, pos_flag=False)  # healthy
    assert d["decision"] == ALLOW and not s._pos_refuse
    return "debounce 1-tick: no trip"


def test_debounce_2tick_trips_exact():
    s = _mk()
    d0 = s.step(0, SAFE_POS, SAFE_VEL, SAFE_TGT, pos_flag=True)  # bad #1
    assert d0["decision"] == ALLOW, "po 1 bad ticku jeszcze ALLOW"
    d1 = s.step(1, SAFE_POS, SAFE_VEL, SAFE_TGT, pos_flag=True)  # bad #2 → trip
    assert d1["decision"] == REFUSE and d1["reason"] == POS_DEGRADED, f"2-tick musi tripować, got {d1}"
    assert d1["rule"] == "R-POS" and d1["action"] == "VELOCITY_DESCENT"
    return "debounce 2-tick: trips exactly at threshold (R-POS, velocity-descent)"


def test_hysteresis_flicker_no_reallow():
    s = _mk(hyst=5)
    s.step(0, SAFE_POS, SAFE_VEL, SAFE_TGT, pos_flag=True)
    s.step(1, SAFE_POS, SAFE_VEL, SAFE_TGT, pos_flag=True)       # tripped
    assert s._pos_refuse
    # migotanie: 3 zdrowe (< M=5), potem znowu bad → NIE re-ALLOW, brak oscylacji
    for k in range(2, 5):
        d = s.step(k, SAFE_POS, SAFE_VEL, SAFE_TGT, pos_flag=False)
        assert d["decision"] == REFUSE and d["reason"] == POS_DEGRADED, f"flicker<M nie re-ALLOW, tick {k}"
    d = s.step(5, SAFE_POS, SAFE_VEL, SAFE_TGT, pos_flag=True)   # bad znów
    assert d["decision"] == REFUSE and s._pos_refuse, "po migotaniu wciąż REFUSE (bez oscylacji)"
    return "histereza: flicker < M NIE re-ALLOW, brak oscylacji"


def test_hysteresis_reallow_after_M():
    s = _mk(hyst=5)
    s.step(0, SAFE_POS, SAFE_VEL, SAFE_TGT, pos_flag=True)
    s.step(1, SAFE_POS, SAFE_VEL, SAFE_TGT, pos_flag=True)       # tripped
    # M=5 ciągłych zdrowych → re-ALLOW dopiero na 5-tym
    for k in range(2, 6):
        d = s.step(k, SAFE_POS, SAFE_VEL, SAFE_TGT, pos_flag=False)
        assert d["decision"] == REFUSE, f"przed M wciąż REFUSE, tick {k} (healthy #{k-1})"
    d = s.step(6, SAFE_POS, SAFE_VEL, SAFE_TGT, pos_flag=False)  # 5-ty zdrowy → re-ALLOW
    assert d["decision"] == ALLOW and not s._pos_refuse, f"po M zdrowych re-ALLOW, got {d}"
    return "histereza: M ciągłego zdrowia → re-ALLOW (nie wcześniej)"


def test_no_deadman_coupling():
    s = _mk()
    s.step(0, SAFE_POS, SAFE_VEL, SAFE_TGT, pos_flag=True)
    # w POS_DEGRADED: KAŻDY tick zwraca 'applied' (świeży setpoint) → streamer karmiony, dead-man NIE tripuje
    for k in range(1, 20):
        d = s.step(k, SAFE_POS, SAFE_VEL, SAFE_TGT, pos_flag=True)
        assert d["decision"] == REFUSE and d["reason"] == POS_DEGRADED
        assert "applied" in d and len(d["applied"]) == 3, f"brak applied w ticku {k} (dead-man!)"
    return "brak sprzężenia z dead-manem: applied świeży co tick w POS_DEGRADED"


def test_backward_compat_no_posflag():
    s = _mk()
    # bez pos_flag (None): monitor nieaktywny → nigdy POS_DEGRADED (r01/r02 bez zmian)
    for k in range(10):
        d = s.step(k, SAFE_POS, SAFE_VEL, SAFE_TGT)   # pos_flag domyślnie None
        assert d["decision"] == ALLOW and not s._pos_refuse
    return "kompatybilność wstecz: pos_flag=None ⇒ brak POS_DEGRADED (r01/r02 nietknięte)"


def test_priority_pos_above_geo():
    # R-POS ponad R-G: gdy pos zdegradowana ORAZ cel poza R_E → REFUSE(POS_DEGRADED), nie GEOFENCE
    s = _mk()
    s.step(0, SAFE_POS, SAFE_VEL, SAFE_TGT, pos_flag=True)
    d = s.step(1, SAFE_POS, SAFE_VEL, FAR_TGT, pos_flag=True)   # trip + geofence violation
    assert d["decision"] == REFUSE and d["reason"] == POS_DEGRADED, \
        f"R-POS ponad R-G (bariera na niepewnym p niewiarygodna), got {d}"
    return "priorytet: R-POS na/ponad R-G (pos-degraded > geofence)"


def test_latch_above_pos():
    # latch (terminal, np. ABORT) ponad R-POS
    s = _mk()
    s.step(0, SAFE_POS, SAFE_VEL, SAFE_TGT, mode=M_ABORT)       # ABORT → terminal latch
    d = s.step(1, SAFE_POS, SAFE_VEL, SAFE_TGT, mode=M_PATROL, pos_flag=True)
    d = s.step(2, SAFE_POS, SAFE_VEL, SAFE_TGT, mode=M_PATROL, pos_flag=True)
    assert d["reason"] == ABORT, f"latch (ABORT) ponad R-POS, got {d}"
    return "priorytet: latch (terminal) ponad R-POS"


def main():
    tests = [test_debounce_1tick_no_trip, test_debounce_2tick_trips_exact,
             test_hysteresis_flicker_no_reallow, test_hysteresis_reallow_after_M,
             test_no_deadman_coupling, test_backward_compat_no_posflag,
             test_priority_pos_above_geo, test_latch_above_pos]
    print("=== B2 testy deterministyczne POS_DEGRADED (R0.3a) ===")
    ok = True
    for t in tests:
        try:
            msg = t()
            print(f"  PASS  {msg}")
        except AssertionError as e:
            ok = False
            print(f"  FAIL  {t.__name__}: {e}")
    print(f"\nWYNIK: {'PASS — B2 logika osłony zwalidowana' if ok else 'FAIL'}")
    import sys
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
