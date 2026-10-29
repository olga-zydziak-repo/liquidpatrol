#!/usr/bin/env python3
"""results/WK3_RECON/tools/wk3_windprobe.py — R1: pomiar litery porywu WindEffects (gz-sim 8.14, binarny)
przez serwis /world/<W>/wind_info (litera symboli pluginu: AdvertiseService Empty→gz.msgs.Wind), 0 bootów.
POMIAR pokazał, że wind_info zwraca wektor BAZOWY (seed), nie chwilowy — dlatego dodatkowo rejestrowana
jest poza ciała-sondy (model "probe" w świecie testowym: link enable_wind, masa 1 kg, grawitacja wył.,
PosePublisher 100 Hz, topik /model/probe/pose). Wiatr chwilowy odtwarza wk3_wind_rekon.py: w = v + a/s.

Uruchamia SAM serwer gz (`gz sim -s -r [--seed N] <świat>`; bez PX4, bez drona — świat testowy z samą
fizyką + WindEffects + <wind>), izolowany GZ_PARTITION, próbkuje serwis wind_info i /clock przez
wiązania python gz.transport13 przez zadany czas ściany, zabija serwer. Zapis: [(t_sim, vx, vy, vz)].

Użycie: wk3_windprobe.py <świat.sdf> <nazwa_świata> <czas_s> <out.json> [--seed N]
"""
import argparse
import json
import os
import subprocess
import time

from gz.msgs10.clock_pb2 import Clock
from gz.msgs10.empty_pb2 import Empty
from gz.msgs10.pose_pb2 import Pose
from gz.msgs10.wind_pb2 import Wind
from gz.transport13 import Node


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sdf"); ap.add_argument("world"); ap.add_argument("secs", type=float); ap.add_argument("out")
    ap.add_argument("--seed", type=int, default=None)
    a = ap.parse_args()
    part = f"wk3probe_{os.getpid()}"
    env = dict(os.environ, GZ_PARTITION=part, GZ_IP="127.0.0.1")
    os.environ.update(GZ_PARTITION=part, GZ_IP="127.0.0.1")
    cmd = ["gz", "sim", "-s", "-r", "--verbose=1"] + (["--seed", str(a.seed)] if a.seed is not None else []) + [a.sdf]
    proc = subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    node = Node()
    tsim = {"t": None}

    def on_clock(msg):
        tsim["t"] = msg.sim.sec + msg.sim.nsec * 1e-9
    node.subscribe(Clock, f"/world/{a.world}/clock", on_clock)
    poses = []

    def on_pose(msg):
        t = msg.header.stamp.sec + msg.header.stamp.nsec * 1e-9
        poses.append((round(t, 4), msg.position.x, msg.position.y, msg.position.z))
    node.subscribe(Pose, "/model/probe/pose", on_pose)
    srv = f"/world/{a.world}/wind_info"
    samples, t_end, t_wait = [], None, time.time() + 30
    try:
        while True:
            now = time.time()
            ok, rep = node.request(srv, Empty(), Empty, Wind, 200)
            if ok and tsim["t"] is not None:
                if t_end is None:
                    t_end = now + a.secs
                v = rep.linear_velocity
                samples.append((round(tsim["t"], 4), v.x, v.y, v.z))
            elif t_end is None and now > t_wait:
                raise SystemExit("serwis wind_info / clock nie wstał w 30 s")
            if t_end is not None and now > t_end:
                break
            time.sleep(0.02)
    finally:
        os.killpg(proc.pid, 9)
        proc.wait()
    json.dump({"sdf": a.sdf, "world": a.world, "seed": a.seed, "cmd": " ".join(cmd), "n": len(samples),
               "probki_t_vx_vy_vz": samples, "sonda_ciala_t_x_y_z": poses}, open(a.out, "w"))
    print(f"[zapis] {a.out}: n={len(samples)} t_sim {samples[0][0]}..{samples[-1][0]}")


if __name__ == "__main__":
    main()
