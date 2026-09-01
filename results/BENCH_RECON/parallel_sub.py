#!/usr/bin/env python3
"""results/BENCH_RECON/parallel_sub.py — RECON (read-only, poza drzewem kodu, SR-5).

Równoległa subskrypcja pozy intruza (gz.transport13) RÓWNOLEGLE do stacku — R2 fakt architektoniczny:
kontroler (niepinowany) może mieć WŁASNĄ subskrypcję gz + WŁASNY zapis jsonl bez wiedzy pętli gate.
Mierzy: częstotliwość [msg/s wall], opóźnienie pozy vs zegar sim [s], rozmiar logu [B/msg → B/s @20Hz].

Uruchom: python3 parallel_sub.py <world> <seconds> <out.jsonl>
Nie modyfikuje niczego w scenie (tylko subskrybuje).
"""
import json
import os
import re
import sys
import time

WORLD = sys.argv[1] if len(sys.argv) > 1 else "world_demo_A3"
SECS = float(sys.argv[2]) if len(sys.argv) > 2 else 20.0
OUT = sys.argv[3] if len(sys.argv) > 3 else "parallel_sub.jsonl"

from gz.transport13 import Node as GzNode
from gz.msgs10.pose_v_pb2 import Pose_V
from gz.msgs10.clock_pb2 import Clock

_clock_sim = [0.0]
_rows = []
_t0 = time.monotonic()


def clock_cb(msg):
    _clock_sim[0] = msg.sim.sec + msg.sim.nsec / 1e9


def pose_cb(msg):
    now = time.monotonic()
    if now - _t0 > SECS:
        return
    pose_sim = msg.header.stamp.sec + msg.header.stamp.nsec / 1e9
    for p in msg.pose:
        if p.name == "intruder":
            _rows.append({
                "recv_wall": round(now - _t0, 4),
                "pose_sim": round(pose_sim, 4),
                "clock_sim": round(_clock_sim[0], 4),
                "age_sim": round(_clock_sim[0] - pose_sim, 4),
                "x": round(p.position.x, 4), "y": round(p.position.y, 4), "z": round(p.position.z, 4),
            })
            return


def main():
    gn = GzNode()
    gn.subscribe(Clock, f"/world/{WORLD}/clock", clock_cb)
    gn.subscribe(Pose_V, f"/world/{WORLD}/dynamic_pose/info", pose_cb)
    while time.monotonic() - _t0 < SECS:
        time.sleep(0.05)
    with open(OUT, "w") as f:
        for r in _rows:
            f.write(json.dumps(r) + "\n")
    n = len(_rows)
    ages = [r["age_sim"] for r in _rows if r["clock_sim"] > 0]
    nbytes = os.path.getsize(OUT) if os.path.exists(OUT) else 0
    per_msg = nbytes / n if n else 0
    summary = {
        "world": WORLD, "seconds": SECS, "n_msgs": n,
        "rate_hz_wall": round(n / SECS, 2),
        "age_sim_mean": round(sum(ages) / len(ages), 4) if ages else None,
        "age_sim_max": round(max(ages), 4) if ages else None,
        "bytes_total": nbytes, "bytes_per_msg": round(per_msg, 1),
        "bytes_per_s_at_20hz": round(per_msg * 20.0, 1),
    }
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
