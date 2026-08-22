"""tests_frames_k1.py — PROMPT_K1 §A3(iii): unit-test helpera ramek (common.frames).
Uruchom: PYTHONPATH=.b0deps/...:. python3 tests_frames_k1.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import frames as F


def test_examples():
    # dron NED [N,E,D] -> ENU [E,N,U]
    assert F.ned2enu([1.5, -0.1, -10]) == [-0.1, 1.5, 10]
    # intruz DRV [E,N,-U] -> ENU [E,N,U] (BEZ zamiany E/N — naprawa markera U2R-2)
    assert F.drv2enu([7.86, 0, -11.5]) == [7.86, 0, 11.5]
    assert F.drv2enu([7.86, -0.1, -11.5]) == [7.86, -0.1, 11.5]
    # DRV -> NED-standard (zamiana E/N do wspólnej ramki z dronem)
    assert F.drv2ned([7.86, 0, -11.5]) == [0, 7.86, -11.5]
    # gz set_pose mapping
    assert F.drv2gz([7.86, 0, -11.5]) == [7.86, 0, 11.5]


def test_roundtrips():
    for v in ([1.5, -0.1, -10], [0, 7, -12], [-3, 4, -9]):
        assert F.enu2ned(F.ned2enu(v)) == v
    for v in ([7.86, 0, -11.5], [1, -2, -11]):
        assert F.enu2drv(F.drv2enu(v)) == v
        assert F.ned2drv(F.drv2ned(v)) == v


def test_delegation_matches_hud():
    from acts.hud_render import _enu, _enu_intr
    v = [7.86, -0.1, -11.5]
    assert list(_enu_intr(v)) == F.drv2enu(v)         # HUD intruz == frames
    assert list(_enu([1.5, -0.1, -10])) == F.ned2enu([1.5, -0.1, -10])  # HUD dron == frames


if __name__ == "__main__":
    test_examples(); test_roundtrips(); test_delegation_matches_hud()
    print("tests_frames_k1: ALL PASS")
