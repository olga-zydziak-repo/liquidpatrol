#!/usr/bin/env python3
"""results/WABIK/tools/wabik_motion.py — pusher WABIKA (PRE_WABIK §1/§2.1; PROMPT_WABIK_S1 §1.1).

KOPIA WZORU harness/intruder_motion.py pod nową nazwą (oryginał NIETKNIĘTY),
zredukowana do roli wabika: set_pose 20 Hz dla encji `name="wabik"` wg WŁASNEGO
pliku trajektorii (semantyka segmentów 1:1 z manifestem: t0,t1,x0,y0,heading_deg,v;
interpolacja liniowa jak bench/scenarios.position_at), log `wabik_motion.jsonl`
(t_sim / cmd_ned / applied_ned) = GT wabika — POZA sędzią (sędzia liczy wyłącznie
gt_intruder). Ramki i klient gz = te same FROZEN klocki co intruder_motion
(GzPoseClient z r02/intruder_driver — parametr name; common.frames).

Start epizodu: --t0-from-trace czeka na event episode_start w OUTDIR/trace.jsonl
(scenariusz intruza; wabik żyje w tym samym zegarze epizodu).

Użycie: wabik_motion.py --world W --traj results/WABIK/wabik_manifest.json
        --traj-id W-LOITER --outdir OUTDIR [--t0-from-trace]
"""
import argparse
import json
import math
import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from common.frames import ned2drv, drv2gz, enu2drv, drv2ned   # READ-ONLY (1:1 z intruder_motion)

SETPOSE_HZ = 20.0


def position_at(traj, t_rel):
    """1:1 semantyka bench/scenarios.position_at (interpolacja liniowa po odcinku)."""
    z = traj["z"]
    segs = traj["segments"]
    if t_rel <= 0:
        return (segs[0]["x0"], segs[0]["y0"], z)
    for s in segs:
        if s["t0"] <= t_rel < s["t1"]:
            dt = t_rel - s["t0"]
            hx = math.cos(math.radians(s["heading_deg"]))
            hy = math.sin(math.radians(s["heading_deg"]))
            return (s["x0"] + s["v"] * hx * dt, s["y0"] + s["v"] * hy * dt, z)
    last = segs[-1]
    dt = last["t1"] - last["t0"]
    hx = math.cos(math.radians(last["heading_deg"]))
    hy = math.sin(math.radians(last["heading_deg"]))
    return (last["x0"] + last["v"] * hx * dt, last["y0"] + last["v"] * hy * dt, z)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", default="world_demo_A3")
    ap.add_argument("--traj", required=True, help="plik manifestu WABIK")
    ap.add_argument("--traj-id", required=True, help="klucz w wabik_trajektorie")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--t0-from-trace", action="store_true")
    ap.add_argument("--max-s", type=float, default=1800.0)
    a = ap.parse_args()
    man = json.load(open(os.path.join(ROOT, a.traj)))
    traj = man["wabik_trajektorie"][a.traj_id]

    from r02.intruder_driver import GzPoseClient          # READ-ONLY, param name
    from gz.transport13 import Node as GzNode
    from gz.msgs10.pose_v_pb2 import Pose_V

    cli = GzPoseClient(a.world, name="wabik", apply_hz=SETPOSE_HZ)
    applied = {"gz": None}

    def pose_cb(msg):
        for p in msg.pose:
            if p.name == "wabik":
                applied["gz"] = [p.position.x, p.position.y, p.position.z]
                return
    gn = GzNode()
    gn.subscribe(Pose_V, f"/world/{a.world}/pose/info", pose_cb)

    # t0: event episode_start z trace (wabik żyje w zegarze epizodu intruza)
    t0 = None
    trace = os.path.join(a.outdir, "trace.jsonl")
    t_wait0 = time.monotonic()
    while a.t0_from_trace and t0 is None and time.monotonic() - t_wait0 < 900:
        if os.path.exists(trace):
            for ln in open(trace):
                if '"ev": "episode_start"' in ln:
                    try:
                        t0 = json.loads(ln)["t0_sim"]
                    except (ValueError, KeyError):
                        pass
                    break
        if t0 is None:
            time.sleep(0.5)
    if t0 is None:
        t0 = cli.sim_t() or 0.0
    print(f"[wabik_motion] t0={t0:.2f} traj={a.traj_id}", flush=True)

    lg = open(os.path.join(a.outdir, "wabik_motion.jsonl"), "a")
    lg.write(json.dumps({"t": "meta", "traj_id": a.traj_id, "t0_sim": round(t0, 3),
                         "traj": traj}) + "\n")
    dur = traj.get("dur_s", 110.0)
    t_start_wall = time.monotonic()
    while time.monotonic() - t_start_wall < a.max_s:
        sim = cli.sim_t()
        if sim is None:
            time.sleep(0.05)
            continue
        trel = sim - t0
        if trel > dur + 2.0:
            break
        x, y, z = position_at(traj, max(0.0, trel))
        cmd_ned = [x, y, -z]
        gx, gy, gz_ = drv2gz(ned2drv(cmd_ned))
        cli.set_pose(gx, gy, gz_)
        ap_ned = None
        if applied["gz"] is not None:
            ap_ned = drv2ned(enu2drv(applied["gz"]))
        lg.write(json.dumps({"t_sim": round(sim, 3), "cmd_ned": [round(v, 4) for v in cmd_ned],
                             "ned": ([round(v, 4) for v in ap_ned] if ap_ned else None)}) + "\n")
        time.sleep(1.0 / SETPOSE_HZ)
    lg.close()
    print("[wabik_motion] DONE", flush=True)


if __name__ == "__main__":
    main()
