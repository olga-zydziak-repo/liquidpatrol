#!/usr/bin/env python3
"""tools/test_act_common.py — testy deterministycznego rdzenia runnerów per-akt (B4 §1, bez SITL)."""
from __future__ import annotations
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from acts import act_common as AC   # noqa: E402

DRONE_NED = [0.0, 0.0, -10.0]


def _rng(intr):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(DRONE_NED, intr))) if intr else None


def test_A1_intruder_in_ring_during_hold():
    spec = AC.load_spec("A1"); fn = AC.intruder_ned_fn(spec)
    hold = spec["timeline_s"]["intruder_ring_hold"]
    for t in (hold[0] + 1, (hold[0] + hold[1]) / 2, hold[1] - 1):
        d = _rng(fn(t))
        assert 7.0 <= d <= 9.0, (t, d)


def test_A1_intruder_parked_outside_before_approach():
    spec = AC.load_spec("A1"); fn = AC.intruder_ned_fn(spec)
    d = _rng(fn(5.0))                       # przed approach → parking (nisko, poza kopertą)
    assert d is None or d > 9.0 or fn(5.0)[2] > -5.0    # parking z=-3 (nisko)


def test_A2_leave_far_then_return_ring():
    spec = AC.load_spec("A2"); fn = AC.intruder_ned_fn(spec)
    gap = spec["timeline_s"]["expire_gap"]
    far_h = math.hypot(fn((gap[0] + gap[1]) / 2)[0], fn((gap[0] + gap[1]) / 2)[1])
    assert far_h > 9.0                      # poza kopertą podczas EXPIRE
    ep1 = spec["timeline_s"]["ep1_ring_hold"]
    assert 7.0 <= _rng(fn((ep1[0] + ep1[1]) / 2)) <= 9.0   # w pierścieniu po powrocie


def test_A3_intruder_absent():
    spec = AC.load_spec("A3"); fn = AC.intruder_ned_fn(spec)
    assert fn(0.0) is None and fn(50.0) is None


def test_grant_delay_from_spec():
    assert AC.grant_delay_s(AC.load_spec("A1")) == 3.0
    assert AC.grant_delay_s(AC.load_spec("A2")) == 3.0


def test_assert_token_gated_raises_on_false():
    class R:
        token_gated = False
    try:
        AC.assert_token_gated(R()); assert False
    except RuntimeError as e:
        assert "A4" in str(e)
    class R2:
        token_gated = True
    AC.assert_token_gated(R2())             # nie rzuca


def test_manifest_reads_hashes_from_files():
    world = os.path.join(ROOT, "worlds", "world_demo_A1.sdf")
    m = AC.build_manifest("A1", world, "HEADSHA", token_gated=True, contention="test")
    assert m["world_hash"] == AC.sha256_file(world)
    assert m["spec_hash"] == AC.sha256_file(os.path.join(ROOT, "acts", "A1_spec.yaml"))
    assert set(m["certs"]) == {"P1", "P4", "P5"} and all(len(h) == 16 for h in m["certs"].values())
    assert m["token_gated"] is True


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn(); print(f"  PASS  {fn.__name__}")
    print(f"WERDYKT test_act_common: PASS ({len(fns)}/{len(fns)})")


if __name__ == "__main__":
    _run_all()
