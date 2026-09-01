#!/usr/bin/env python3
"""harness/tests_intruder_motion.py — test B: trajektoria deterministyczna na syntetycznym zegarze; set_pose liczone."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from harness.intruder_motion import IntruderMotion, scenario_to_gz, gz_to_ned, intruder_start_gate, TOL_START
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


def test_start_gate_ok_after_settle():
    """Poza ≤ TOL po kilku set_pose ⇒ OK; n_setpose liczone; wait_sim > 0."""
    start = [3.0, 7.0, -10.0]
    clk = SynthClock(0.0, 0.1)
    calls = {"n": 0}
    # intruz „dojeżdża" do startu po 3 wywołaniach set_pose
    def get_applied():
        if calls["n"] < 3:
            return [3.0 + 5.0, 7.0, -10.0]      # daleko (5 m)
        return [3.0 + 0.05, 7.0 + 0.03, -10.0]  # w tolerancji (~0.06 m)
    def set_pose():
        calls["n"] += 1
    r = intruder_start_gate(set_pose, get_applied, clk.now, start, tol=TOL_START,
                            timeout_sim=5.0, step_fn=clk.step)
    assert r["status"] == "OK", r
    assert r["n_setpose"] >= 3 and r["attempts"] == 1
    assert r["wait_sim"] >= 0.0


def test_start_gate_invalid_after_two_timeouts():
    """Poza NIGDY nie osiąga TOL ⇒ 2 timeouty (5 s każdy) ⇒ INVALID_START."""
    start = [0.0, 0.0, -10.0]
    clk = SynthClock(0.0, 0.5)
    r = intruder_start_gate(lambda: None, lambda: [10.0, 0.0, -10.0], clk.now, start,
                            tol=TOL_START, timeout_sim=5.0, step_fn=clk.step)
    assert r["status"] == "INVALID_START" and r["attempts"] == 2


def test_run_episode_interruptible(monkeypatch=None):
    """fix v1.2: should_stop() przerywa run_episode (mover nie kłóci się z bramką następnego epizodu)."""
    m = S.gen_manifest()
    ep = S.find_episode(m, 1.0, 180, seed=1)          # ep długi (110 s)
    clk = SynthClock(0.0, 0.02)
    calls = {"n": 0}
    gt = []
    im = IntruderMotion(set_pose_fn=lambda x, y, z: None, clock_fn=clk.now, get_applied_gz_fn=None)
    def should_stop():
        calls["n"] += 1
        return calls["n"] > 20                          # przerwij po 20 iteracjach
    im.run_episode(ep, 0.0, ep["ep_dur_s"], gt.append, step_fn=clk.step, should_stop=should_stop)
    assert im.n_gt <= 21, f"run_episode nie przerwał się: n_gt={im.n_gt}"   # << pełne 110s/0.02=5500
    # bez should_stop leci do dur
    clk2 = SynthClock(0.0, 0.02); im2 = IntruderMotion(lambda x, y, z: None, clk2.now)
    im2.run_episode(ep, 0.0, 2.0, [].append, step_fn=clk2.step)
    assert im2.n_gt > 90


def test_start_gate_deterministic():
    start = [1.0, 2.0, -10.0]
    def run():
        clk = SynthClock(0.0, 0.1); c = {"n": 0}
        def ga():
            c["n"] += 1
            return [1.0 + (2.0 if c["n"] < 5 else 0.05), 2.0, -10.0]
        return intruder_start_gate(lambda: None, ga, clk.now, start, step_fn=clk.step)
    assert run() == run()


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_") and callable(f):
            f(); print(f"OK {n}")
    print("tests_intruder_motion: ALL PASS")
