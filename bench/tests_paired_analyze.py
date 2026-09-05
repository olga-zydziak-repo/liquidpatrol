#!/usr/bin/env python3
"""bench/tests_paired_analyze.py — testy N-F1b na danych syntetycznych (bez lotów)."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from bench.paired_analyze import pair, refuse_ledger, oracle_d6_block1


def test_pair_concord_discord():
    a = {"c00_s01": True, "c01_s01": True, "c02_s01": False, "c03_s01": True}
    b = {"c00_s01": True, "c01_s01": False, "c02_s01": False, "c04_s01": True}
    r = pair(a, b)
    assert r["n"] == 3                       # wspólne: c00,c01,c02
    assert r["concordant"] == 2              # c00(T,T), c02(F,F)
    assert r["discordant"] == 1              # c01(T,F)
    assert r["a_only_pass"] == 1 and r["b_only_pass"] == 0
    assert r["only_in_a"] == ["c03_s01"] and r["only_in_b"] == ["c04_s01"]


def test_pair_all_concord():
    a = {"x": True, "y": False}
    r = pair(a, a)
    assert r["concordant"] == 2 and r["discordant"] == 0


def test_refuse_ledger():
    recs = [{"scenario_id": "c05_s01", "refuse_events": [{"t": 12.3, "reason": "GEOFENCE"}]},
            {"scenario_id": "c09_s02", "refuse_events": [{"t": 5.0, "reason": "GEOFENCE"},
                                                          {"t": 9.0, "reason": "POS_DEGRADED"}]},
            {"scenario_id": "c00_s01", "refuse_events": []}]
    L = refuse_ledger(recs)
    assert L["n_refuse"] == 3
    assert L["by_reason"] == {"GEOFENCE": 2, "POS_DEGRADED": 1}
    assert len(L["events"]) == 3


def test_oracle_d6_block1_real():
    """Egzekutor D6 ziaren 1-4 z ławki: 48 scenariuszy minus 4 porażki proximity (c05_s01,c07_s02,c09_s02,c09_s03)."""
    orc = oracle_d6_block1()
    assert len(orc) == 48, len(orc)
    assert sum(orc.values()) == 44, sum(orc.values())    # 44 sukcesy D6 w bloku 1
    for fail in ("c05_s01", "c07_s02", "c09_s02", "c09_s03"):
        assert orc[fail] is False, fail


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_") and callable(f):
            f(); print(f"OK {n}")
    print("tests_paired_analyze: ALL PASS")
