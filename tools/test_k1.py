"""Regresja instrumentu K1 (PRE_K1 §3.2/§3.3) w suicie pytest — opakowuje --selftest sędziego i agregatu."""
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "k1"))


def test_k1_judge_selftest():
    import k1_judge
    assert k1_judge.selftest() is True


def test_k1_aggregate_selftest():
    import k1_aggregate
    assert k1_aggregate.selftest() is True
