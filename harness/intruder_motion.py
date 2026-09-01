#!/usr/bin/env python3
"""harness/intruder_motion.py — ruch intruza obok stacku (PROMPT_BENCH_BUILD B, PRE D2/D5).

Czyta manifest scenariuszy; dla bieżącego epizodu pcha `set_pose` 20 Hz wg `position_at(ep, t_rel)`
(czas SIM z zegara świata, nie wall). Loguje KOMENDĘ i POZĘ ZASTOSOWANĄ (z `/world/W/pose/info`) do
`gt_intruder.jsonl` (czas sim, ~50 Hz). Reaguje na sygnały epizodu (start/reset) z pliku sterującego w OUTDIR.

Ramki (common/frames): scenario (N,E,alt) → cmd_ned [N,E,−alt]; komenda gz = drv2gz(ned2drv(cmd_ned));
applied z pose/info (gz-ENU) → NED = drv2ned(enu2drv(gz)). GT sędziego = APPLIED (nie komenda) — chybienia set_pose w danych.

`IntruderMotion` — rdzeń z wstrzykiwanymi zależnościami (testowalny bez gz). `main()` — spina z gz.
"""
import json
import math
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from bench import scenarios as S
from common.frames import ned2drv, drv2gz, enu2drv, drv2ned

SETPOSE_HZ = 20.0

# TOL_START (FAKT): p95 błędu set_pose (|poza_zastosowana − komenda|) w danych shakeoutu = 0.10 m
# (boot1/boot2 gt_intruder.jsonl, mean 0.05 / p50 0.04 / p95 0.10; max 21 m = tranzient teleportu granicznego).
# TOL_START = 0.20 m = 2× p95 → komfortowo powyżej szumu set_pose, poniżej istotnego błędu pozycji.
TOL_START = 0.20


def intruder_start_gate(set_pose_fn, get_applied_ned_fn, clock_fn, start_ned,
                        tol=TOL_START, timeout_sim=5.0, step_fn=None):
    """Bramka startu intruza (PROMPT_BENCH_RESHAKEOUT §2). Komenderuje set_pose do `start_ned` i czeka aż
    poza ZASTOSOWANA (GT z pose/info) będzie ≤ tol. Timeout `timeout_sim` sim → jeden pełny retry →
    drugi timeout ⇒ INVALID_START. Czysta logika (deps wstrzykiwane) → testowalna bez gz.
    Zwraca {status: OK|INVALID_START, n_setpose, wait_sim, pose, attempts}."""
    n_set = 0
    total_wait = 0.0
    for attempt in range(2):                       # próba 0 + jeden pełny retry
        t0 = clock_fn()
        while clock_fn() - t0 < timeout_sim:
            set_pose_fn()
            n_set += 1
            ap = get_applied_ned_fn()
            if ap is not None:
                d = math.sqrt(sum((ap[k] - start_ned[k]) ** 2 for k in range(3)))
                if d <= tol:
                    total_wait += clock_fn() - t0
                    return {"status": "OK", "n_setpose": n_set, "wait_sim": round(total_wait, 3),
                            "pose": [round(v, 4) for v in ap], "attempts": attempt + 1}
            if step_fn:
                step_fn()
        total_wait += clock_fn() - t0
    ap = get_applied_ned_fn()
    return {"status": "INVALID_START", "n_setpose": n_set, "wait_sim": round(total_wait, 3),
            "pose": [round(v, 4) for v in ap] if ap else None, "attempts": 2}


def scenario_to_gz(px, py, pz):
    """scenario (N=px, E=py, alt=pz) → gz set_pose [x=E, y=N, z=U]."""
    cmd_ned = [px, py, -pz]
    return drv2gz(ned2drv(cmd_ned)), cmd_ned


def gz_to_ned(gz):
    """gz-ENU [E,N,U] → NED [N,E,D]."""
    return drv2ned(enu2drv(list(gz)))


class IntruderMotion:
    def __init__(self, set_pose_fn, clock_fn, get_applied_gz_fn=None, setpose_hz=SETPOSE_HZ):
        self.set_pose_fn = set_pose_fn          # (gz_x, gz_y, gz_z) -> None
        self.clock_fn = clock_fn                # () -> sim_t [s]
        self.get_applied_gz_fn = get_applied_gz_fn   # () -> [E,N,U] applied (pose/info) lub None
        self.setpose_period = 1.0 / setpose_hz
        self.n_setpose = 0
        self.n_gt = 0

    def run_episode(self, ep, t0_sim, dur_sim, gt_writer, step_fn=None):
        """Prowadzi intruza wg position_at(ep, sim_now−t0) aż t_rel ≥ dur_sim. gt_writer(row) na każdą iterację.
        step_fn() (test: advance synthetic clock / live: sleep) — po każdej iteracji."""
        last_sp = None
        while True:
            sim_now = self.clock_fn()
            if sim_now is None:
                break
            t_rel = sim_now - t0_sim
            if t_rel >= dur_sim:
                break
            px, py, pz = S.position_at(ep, t_rel)
            gz, cmd_ned = scenario_to_gz(px, py, pz)
            if last_sp is None or (sim_now - last_sp) >= self.setpose_period - 1e-9:
                self.set_pose_fn(*gz)
                self.n_setpose += 1
                last_sp = sim_now
            applied_gz = self.get_applied_gz_fn() if self.get_applied_gz_fn else gz
            applied_ned = gz_to_ned(applied_gz) if applied_gz is not None else None
            gt_writer({
                "t_sim": round(sim_now, 4),
                "episode_id": ep["episode_id"], "scenario_id": ep["scenario_id"],
                "cmd_ned": [round(v, 4) for v in cmd_ned],
                "ned": [round(v, 4) for v in applied_ned] if applied_ned else None,
            })
            self.n_gt += 1
            if step_fn:
                step_fn()
            else:
                time.sleep(0.02)


# ------------------------------- LIVE -------------------------------
def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", default="world_demo_A3")
    ap.add_argument("--manifest", default="results/BENCH/scenario_manifest.json")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--control", default=None, help="plik sterujący epizodami (JSON)")
    args = ap.parse_args()
    control = args.control or os.path.join(args.outdir, "episode_control.json")
    manifest = json.load(open(os.path.join(ROOT, args.manifest)))

    from r02.intruder_driver import GzPoseClient
    from gz.transport13 import Node as GzNode
    from gz.msgs10.pose_v_pb2 import Pose_V

    cli = GzPoseClient(args.world, apply_hz=SETPOSE_HZ)
    applied = {"gz": None}

    def pose_cb(msg):
        for p in msg.pose:
            if p.name == "intruder":
                applied["gz"] = [p.position.x, p.position.y, p.position.z]
                return
    gn = GzNode(); gn.subscribe(Pose_V, f"/world/{args.world}/pose/info", pose_cb)

    def set_pose_fn(x, y, z):
        cli.set_pose(x, y, z)

    def clock_fn():
        return cli.sim_t()

    im = IntruderMotion(set_pose_fn, clock_fn, get_applied_gz_fn=lambda: applied["gz"])
    gt_path = os.path.join(args.outdir, "gt_intruder.jsonl")
    gtf = open(gt_path, "a")

    def gt_writer(row):
        gtf.write(json.dumps(row) + "\n"); gtf.flush()

    print(f"[intruder_motion] gotowy; kontrola={control}", flush=True)
    seen = None
    while True:
        try:
            ctl = json.load(open(control)) if os.path.exists(control) else {}
        except Exception:
            ctl = {}
        phase = ctl.get("phase")
        if phase == "stop":
            break
        if phase == "start" and ctl.get("episode_id") != seen:
            seen = ctl.get("episode_id")
            ep = manifest["episodes"][ctl["episode_id"]]
            t0 = ctl.get("t0_sim") or (clock_fn() or 0.0)
            im.run_episode(ep, t0, ep["ep_dur_s"], gt_writer)
        time.sleep(0.1)
    gtf.close()


if __name__ == "__main__":
    main()
