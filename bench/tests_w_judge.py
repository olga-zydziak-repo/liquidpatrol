#!/usr/bin/env python3
"""tests_w_judge.py — W B4: testy klasyfikatora §5 (obie strony ε_false=2.0, brzeg) + binning kierunków."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bench import w_judge as W


def _ekf(mono, x, y):      # NED: x=N, y=E
    return {"t": "ekf", "mono": mono, "x": x, "y": y, "z": 0.0}


def _gt(mono, x, y):       # ENU: x=E, y=N ; enu2ned -> [N=y, E=x]
    return {"t": "gt", "mono": mono, "sim": mono, "x": x, "y": y, "z": 0.0}


def test_classify_boundary():
    assert W.classify(1.9) == "FALSZYWY"
    assert W.classify(1.999) == "FALSZYWY"
    assert W.classify(2.0) == "PRAWDZIWY"       # brzeg: >= ⇒ PRAWDZIWY
    assert W.classify(2.5) == "PRAWDZIWY"
    assert W.classify(None) == "NIEROZSTRZYGNIETE"


def test_median_err_false_side():
    # EKF w (0,0); GT ENU (x=1.0,y=0) → err = hypot(0-0, 0-1.0)=1.0 < 2.0 ⇒ FALSZYWY
    ekf = [_ekf(99.0 + 0.05 * i, 0.0, 0.0) for i in range(20)]
    gt = [_gt(99.0 + 0.05 * i, 1.0, 0.0) for i in range(20)]
    med, n = W.median_err_before_trip(ekf, gt, trip_mono=100.0)
    assert abs(med - 1.0) < 1e-6, med
    assert W.classify(med) == "FALSZYWY"
    assert n == 20


def test_median_err_true_boundary():
    # GT ENU (x=2.0,y=0) → err = 2.0 dokładnie ⇒ PRAWDZIWY (brzeg)
    ekf = [_ekf(99.0 + 0.05 * i, 0.0, 0.0) for i in range(20)]
    gt = [_gt(99.0 + 0.05 * i, 2.0, 0.0) for i in range(20)]
    med, n = W.median_err_before_trip(ekf, gt, trip_mono=100.0)
    assert abs(med - 2.0) < 1e-6, med
    assert W.classify(med) == "PRAWDZIWY"


def test_median_err_true_side():
    ekf = [_ekf(99.0 + 0.05 * i, 0.0, 0.0) for i in range(20)]
    gt = [_gt(99.0 + 0.05 * i, 3.0, 0.0) for i in range(20)]
    med, _ = W.median_err_before_trip(ekf, gt, trip_mono=100.0)
    assert abs(med - 3.0) < 1e-6
    assert W.classify(med) == "PRAWDZIWY"


def test_window_excludes_old_ticks():
    # rzędy PRZED oknem (mono < 99.0) z ogromnym błędem NIE wchodzą; mediana z okna = 1.0
    old = [_ekf(50.0 + i, 100.0, 100.0) for i in range(30)]  # daleko poza oknem, wielki błąd
    ekf = old + [_ekf(99.0 + 0.05 * i, 0.0, 0.0) for i in range(20)]
    gt = [_gt(99.0 + 0.05 * i, 1.0, 0.0) for i in range(20)]
    med, n = W.median_err_before_trip(ekf, gt, trip_mono=100.0)
    assert abs(med - 1.0) < 1e-6, (med, n)
    assert n == 20


def test_nmax_caps_at_20():
    # 40 ticków w oknie [99,100] → tylko ostatnie 20 użyte (wszystkie err=1.0 tu, więc sprawdzamy n)
    ekf = [_ekf(99.0 + (1.0 / 40) * i, 0.0, 0.0) for i in range(40)]
    gt = [_gt(99.0 + (1.0 / 40) * i, 1.0, 0.0) for i in range(40)]
    med, n = W.median_err_before_trip(ekf, gt, trip_mono=100.0)
    assert n == 20, n
    assert abs(med - 1.0) < 1e-6


def test_rel_direction_bins():
    assert W.rel_direction([1.0, 0.0], [1.0, 0.0]) == "tailwind"     # zgodny z wiatrem
    assert W.rel_direction([-1.0, 0.0], [1.0, 0.0]) == "headwind"    # pod wiatr
    assert W.rel_direction([0.0, 1.0], [1.0, 0.0]) == "crosswind"    # prostopadle
    assert W.rel_direction([0.0, 0.0], [1.0, 0.0]) == "none"         # brak ruchu
    assert W.rel_direction([1.0, 0.0], [0.0, 0.0]) == "none"         # brak wiatru


if __name__ == "__main__":
    for name in sorted(n for n in dir() if n.startswith("test_")):
        globals()[name](); print(f"{name}: ok")
    print("tests_w_judge: all passed")
