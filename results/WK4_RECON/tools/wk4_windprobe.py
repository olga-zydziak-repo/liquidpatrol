#!/usr/bin/env python3
"""results/WK4_RECON/tools/wk4_windprobe.py — R1/R3: wejście wiatru W CZASIE RZECZYWISTYM przez topik
/world/<W>/wind (gz.msgs.Wind; litera: `gz topic -i` na gołym serwerze — subskrybent WindEffects), 0 bootów.

Wzór: results/WK3_RECON/tools/wk3_windprobe.py (abc4a665, nietknięty) — goły `gz sim -s -r`, izolowany
GZ_PARTITION, ciało-sonda 1 kg bez grawitacji z enable_wind i PosePublisher 100 Hz. NOWE: publikator
sterowany CZASEM SYMULACJI (topik /world/<W>/clock), nie zegarem ściennym — wartość dla bieżącego t_sim
publikowana w chwilach k/rate (rate Hz) czasu symulacji. Rekonstrukcja 3D: w = v + a/f (f = 0.397 przy
s = 0.63 — RECON_WK3, wk3_wind_rekon 6ae9027a, prawo F = m·f·(w − v)).

Programy:
  --step "t0:vx,vy,vz[:en];t1:...;tSTOP:stop"  — odcinki stałe (en=0 ⇒ enable_wind=false w wiadomości)
  --series <D*.json> [--t-off S]               — przebieg z pliku (wartość próbki floor((t−t_off)/dt))
Wyjście JSON: poses [(t, x, y, z)], publikacje [(t_sim, wx, wy, wz, en)], parametry.

Użycie: wk4_windprobe.py <świat.sdf> <nazwa_świata> <t_sim_koniec> <out.json> (--step ... | --series ...)
        [--rate 20]
"""
import argparse
import json
import os
import subprocess
import time

import numpy as np
from gz.msgs10.clock_pb2 import Clock
from gz.msgs10.pose_pb2 import Pose
from gz.msgs10.wind_pb2 import Wind
from gz.transport13 import Node

F_S063 = 0.397


def parse_step(s):
    prog = []
    for seg in s.split(";"):
        parts = seg.split(":")
        t = float(parts[0])
        if parts[1] == "stop":
            prog.append((t, None, True))
            continue
        v = [float(x) for x in parts[1].split(",")]
        en = (parts[2] != "0") if len(parts) > 2 else True
        prog.append((t, v, en))
    return sorted(prog, key=lambda x: x[0])


def value_step(prog, t):
    cur = None
    for (t0, v, en) in prog:
        if t >= t0:
            cur = (v, en)
    return cur          # None = przed pierwszym odcinkiem (nie publikuj); (None, …) = stop


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sdf"); ap.add_argument("world"); ap.add_argument("t_end", type=float); ap.add_argument("out")
    ap.add_argument("--step"); ap.add_argument("--series"); ap.add_argument("--t-off", type=float, default=0.0)
    ap.add_argument("--rate", type=float, default=20.0)
    a = ap.parse_args()
    ser = None
    if a.series:
        d = json.load(open(a.series))
        ser = (d["dt"], np.array(d["wx"]), np.array(d["wy"]), np.array(d["wz"]))
    prog = parse_step(a.step) if a.step else None
    part = f"wk4probe_{os.getpid()}"
    env = dict(os.environ, GZ_PARTITION=part, GZ_IP="127.0.0.1")
    os.environ.update(GZ_PARTITION=part, GZ_IP="127.0.0.1")
    cmd = ["gz", "sim", "-s", "-r", "--verbose=1", a.sdf]
    proc = subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            start_new_session=True)
    node = Node()
    tsim = {"t": None}
    node.subscribe(Clock, f"/world/{a.world}/clock",
                   lambda m: tsim.__setitem__("t", m.sim.sec + m.sim.nsec * 1e-9))
    poses = []
    node.subscribe(Pose, "/model/probe/pose",
                   lambda m: poses.append((round(m.header.stamp.sec + m.header.stamp.nsec * 1e-9, 4),
                                           m.position.x, m.position.y, m.position.z)))
    pub = node.advertise(f"/world/{a.world}/wind", Wind)
    pubs = []
    k_next = 0
    t_wait = time.time() + 30
    try:
        while True:
            t = tsim["t"]
            if t is None:
                if time.time() > t_wait:
                    raise SystemExit("clock nie wstał w 30 s")
                time.sleep(0.005)
                continue
            if t >= a.t_end:
                break
            if t >= k_next / a.rate:
                k_next = int(t * a.rate) + 1
                val = None
                if ser is not None:
                    i = int((t - a.t_off) / ser[0])
                    if 0 <= i < len(ser[1]):
                        val = ([float(ser[1][i]), float(ser[2][i]), float(ser[3][i])], True)
                elif prog is not None:
                    cur = value_step(prog, t)
                    if cur is not None and cur[0] is not None:
                        val = cur
                if val is not None:
                    m = Wind()
                    m.linear_velocity.x, m.linear_velocity.y, m.linear_velocity.z = val[0]
                    m.enable_wind = bool(val[1])
                    pub.publish(m)
                    pubs.append((round(t, 4), *[round(x, 5) for x in val[0]], int(val[1])))
            time.sleep(0.001)
    finally:
        os.killpg(proc.pid, 9)
        proc.wait()
    json.dump({"sdf": a.sdf, "world": a.world, "cmd": " ".join(cmd), "rate": a.rate, "step": a.step,
               "series": a.series, "t_off": a.t_off, "publikacje": pubs, "poses": poses},
              open(a.out, "w"))
    print(f"[zapis] {a.out}: publikacji {len(pubs)}, póz {len(poses)}")


def rekon3(poses, f=F_S063, k=9):
    """w = v + a/f, 3D; v, a z różnic centralnych + średnia ruchoma k próbek (wzór wk3_wind_rekon)."""
    P = np.array(poses, float)
    P = P[np.argsort(P[:, 0])]
    _, idx = np.unique(P[:, 0], return_index=True)
    P = P[idx]
    t = P[:, 0]
    ker = np.ones(k) / k
    out = []
    for c in (1, 2, 3):
        v = np.convolve(np.gradient(P[:, c], t), ker, mode="same")
        acc = np.convolve(np.gradient(v, t), ker, mode="same")
        out.append(v + acc / f)
    sl = slice(2 * k, len(t) - 2 * k)
    return t[sl], out[0][sl], out[1][sl], out[2][sl]


if __name__ == "__main__":
    main()
