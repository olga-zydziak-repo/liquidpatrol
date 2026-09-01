#!/usr/bin/env python3
"""bench/tests_demo_features.py — testy E+F: features 8-wym dwie ścieżki bit-identyczne; demo row bez null."""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from bench.features import features, FEATURE_NAMES
from bench.demo_logger import make_row, feature_state_from_row, DemoLogger, REQUIRED


def test_features_len8_and_names():
    assert len(FEATURE_NAMES) == 8
    st = {"own_pos_ned": [1, 2, 3], "own_vel_ned": [0.1, 0.2, 0.3],
          "trk_pos_ned": [5, 7, 9], "track_age_s": 0.4, "track_valid": True}
    v = features(st)
    assert len(v) == 8
    assert v[:3] == [4.0, 5.0, 6.0]              # rel = trk - own
    assert v[6] == 0.4 and v[7] == 1.0


def test_features_two_paths_identical():
    st = {"own_pos_ned": [1.5, -2.0, -10.0], "own_vel_ned": [0.5, -0.5, 0.1],
          "trk_pos_ned": [8.0, 3.0, -10.0], "track_age_s": 0.2, "track_valid": False}

    class Obj:
        pass
    o = Obj()
    for k, val in st.items():
        setattr(o, k, val)
    assert features(st) == features(o), "features rozjazd dict vs obiekt"


def test_demo_row_from_feature_state_matches_flight():
    fd = {"trk_pos_ned": [8.0, 3.0, -10.0], "trk_vel_ned": [1.0, 0.0, 0.0],
          "track_age_s": 0.0, "track_valid": True, "feed_sha": "abc"}
    ep = {"episode_id": 5, "scenario_id": "c05_s01", "seed": 1, "attempt": 0}
    row = make_row(12.34, 246, ep, [1.5, -2.0, -10.0], [0.5, -0.5, 0.1], fd,
                   [0.3, 1.7, -0.2], "orbit", 0, "orbit", "sha_ctrl", "sha_params")
    # brak null w REQUIRED
    for k in REQUIRED:
        assert row.get(k) is not None
    # features z wiersza == features ze stanu lotu (ta sama funkcja)
    flight_state = {"own_pos_ned": [1.5, -2.0, -10.0], "own_vel_ned": [0.5, -0.5, 0.1],
                    "trk_pos_ned": [8.0, 3.0, -10.0], "track_age_s": 0.0, "track_valid": True}
    assert features(feature_state_from_row(row)) == features(flight_state)
    # trk_vel_ned logowane, ale NIE w cechach
    assert "trk_vel_ned" in row and len(features(flight_state)) == 8


def test_logger_one_row_per_tick():
    fd = {"trk_pos_ned": [8, 3, -10], "trk_vel_ned": [1, 0, 0], "track_age_s": 0.0,
          "track_valid": True, "feed_sha": "abc"}
    ep = {"episode_id": 0, "scenario_id": "c00_s01", "seed": 1, "attempt": 0}
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "demo.jsonl")
        lg = DemoLogger(p)
        for t in range(10):
            lg.log(make_row(t * 0.05, t, ep, [0, 0, -10], [0, 0, 0], fd, [0, 0, 0],
                            "approach", 0, "orbit", "s1", "s2"))
        lg.close()
        assert sum(1 for _ in open(p)) == 10


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_") and callable(f):
            f(); print(f"OK {n}")
    print("tests_demo_features: ALL PASS")
