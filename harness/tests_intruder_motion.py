#!/usr/bin/env python3
"""harness/tests_intruder_motion.py — test B: trajektoria deterministyczna na syntetycznym zegarze; set_pose liczone."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from harness.intruder_motion import IntruderMotion, scenario_to_gz, gz_to_ned
from bench import scenarios as S


class SynthClock:
    def __init__(self, t0, dt):
        self.t = t0; self.dt = dt

    def now(self):
        return self.t

    def step(self):
        self.t = round(self.t + self.dt, 6)


def _drive(ep, t0, dur, dt=0.02):
    clk = SynthClock(t0, dt)
    calls = []
    gt = []
    im = IntruderMotion(set_pose_fn=lambda x, y, z: calls.append((round(x, 4), round(y, 4), round(z, 4))),
                        clock_fn=clk.now,
                        get_applied_gz_fn=None)   # applied = komenda (idealne zastosowanie)
    im.run_episode(ep, t0, dur, gt_writer=gt.append, step_fn=clk.step)
    return calls, gt, im


def test_deterministic_trajectory():
    m = S.gen_manifest()
    ep = S.find_episode(m, 1.0, 90, seed=1)
    c1, g1, _ = _drive(ep, 100.0, 4.0)
    c2, g2, _ = _drive(ep, 100.0, 4.0)
    assert c1 == c2, "komendy set_pose niedeterministyczne"
    assert [r["cmd_ned"] for r in g1] == [r["cmd_ned"] for r in g2], "gt cmd niedeterministyczne"


def test_setpose_count_and_rate():
    m = S.gen_manifest()
    ep = S.find_episode(m, 0.5, 180, seed=1)
    dur = 5.0
    calls, gt, im = _drive(ep, 0.0, dur, dt=0.02)   # 50 Hz zegar (pętla=rate gt; set_pose podzbiór ~20 Hz)
    # set_pose liczone: przy 50 Hz zegarze i okresie 0.05 s efektywnie ~16.7 Hz (dyskretyzacja);
    # GzPoseClient aplikuje 20 Hz niezależnie (recon applied_hz 19.9). Band luźny [75,110].
    assert 75 <= im.n_setpose <= 110, f"n_setpose={im.n_setpose}"
    assert im.n_setpose == len(calls)
    # gt ~50 Hz przez 5 s ≈ 250
    assert 240 <= im.n_gt <= 260, f"n_gt={im.n_gt}"


def test_frame_roundtrip():
    # scenario (N=3, E=7, alt=10) → gz → NED wraca do (3,7,-10)
    gz, cmd_ned = scenario_to_gz(3.0, 7.0, 10.0)
    assert cmd_ned == [3.0, 7.0, -10.0]
    assert gz == [7.0, 3.0, 10.0]                 # [E,N,U]
    assert gz_to_ned(gz) == [3.0, 7.0, -10.0]     # applied → NED == cmd_ned


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_") and callable(f):
            f(); print(f"OK {n}")
    print("tests_intruder_motion: ALL PASS")
