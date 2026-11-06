#!/usr/bin/env python3
"""results/KONT/tools/kont_frames.py — test identyczności klatek mono_cam (PROMPT_KONT_S1 §2, PRE_KONT §2.3). Boot A: gz bez PX4.

Przebiegi (po jednym serwerze gz na przebieg, statyczny model na stałej pozie, bez fizyki lotu):
  R1, R2 = x500_mono_cam (pin, bez maski) na world_demo_A3 — kontrola szumu (K);
  T      = x500_mono_cam_flow (maska) na world_kont_A3 — test;
  N      = x500_mono_cam (bez maski) na world_kont_A3 — kontrola negatywna czułości: dekal MA być widoczny.
Metryka per poza: max|Δ| piksela i liczba pikseli ≠ 0. K = R1 vs R2, T = R1 vs T. Identyczność ⇔ T ≤ K w każdej pozie.
Klatki kamery przepływu z T do raportu. PNG bezstratne w results/KONT/s1/frames/ (przeliczalne przez CC bez bootu).
Tryby: bez argumentów = przebiegi + porównanie; --compare = samo porównanie z PNG.
"""
import json
import math
import os
import subprocess
import sys
import threading
import time

import cv2
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT = os.path.join(ROOT, "results", "KONT", "s1", "frames")
ZR = os.path.join(ROOT, "results", "KONT", "s1", "zrodla")
A3, KONT = "world_demo_A3", "world_kont_A3"
RUNS = [("R1", A3, "rig_ref.sdf"), ("T", KONT, "rig_flow.sdf"), ("R2", A3, "rig_ref.sdf"), ("N", KONT, "rig_ref.sdf")]
# (nazwa, x, y, z, pitch_deg, yaw_rad) w ENU gz; pitch>0 = nos w dół
def _ring(r, az_deg, z, out, pitch=0.0):
    a = math.radians(az_deg)
    return (r * math.cos(a), r * math.sin(a), z, pitch, a if out else a + math.pi)
POSES = {"p1_srodek_z10": (0.0, 0.0, 10.0, 0.0, 0.0),
         "p2_r20_out": _ring(20, 30, 12, True), "p3_r20_in": _ring(20, 30, 12, False),
         "p4_r30_out": _ring(30, 135, 12, True), "p5_r30_in": _ring(30, 135, 12, False),
         "p6_r10_pitch15": _ring(10, 250, 10, True, 15.0), "p7_z5": _ring(5, 80, 5, False),
         "p8_r30_out_pitch15": _ring(30, 300, 12, True, 15.0)}
N_SKIP, N_KEEP, POSE_TMO = 30, 5, 90.0


def env():
    e = dict(os.environ)
    src = ("source env_gpu.sh >/dev/null; cd PX4-Autopilot/build/px4_sitl_default/rootfs && . ./gz_env.sh; env -0")
    raw = subprocess.check_output(["bash", "-c", f"cd {ROOT}; {src}"])
    e.update(dict(kv.split("=", 1) for kv in raw.decode().split("\0") if "=" in kv))
    e.update(GZ_IP="127.0.0.1", HEADLESS="1", GALLIUM_DRIVER="d3d12", MESA_D3D12_DEFAULT_ADAPTER_NAME="NVIDIA")
    return e


def teardown():
    for p in ("gz sim", "ruby.*gz"):
        subprocess.run(["pkill", "-9", "-f", p], capture_output=True)
    time.sleep(3)


def svc(e, *a):
    return subprocess.run(["gz", "service", *a], env=e, capture_output=True, text=True, timeout=30)


class Grab:
    def __init__(self, node, topic):
        from gz.msgs10.image_pb2 import Image
        self.frames, self.n, self.lock = [], 0, threading.Lock()
        node.subscribe(Image, topic, self._cb)

    def _cb(self, m):
        with self.lock:
            self.n += 1
            if self.n > N_SKIP and len(self.frames) < N_KEEP:
                ch = len(m.data) // (m.width * m.height)
                self.frames.append(np.frombuffer(m.data, np.uint8).reshape(m.height, m.width, ch).copy())

    def done(self):
        with self.lock:
            return len(self.frames) >= N_KEEP


def run_one(tag, world, rig, e, log):
    from gz.transport13 import Node
    os.environ.update(GZ_IP="127.0.0.1")
    rc = subprocess.run(["bash", "harness/world_hash.sh", world, os.path.join(ROOT, "results/KONT/s1/bootA")], cwd=ROOT,
                        capture_output=True, text=True)
    assert rc.returncode == 0, rc.stdout
    srv = subprocess.Popen(["gz", "sim", "--verbose=1", "-r", "-s", f"{e['PX4_GZ_WORLDS']}/{world}.sdf"], env=e,
                           stdout=log, stderr=log)
    t0 = time.monotonic()
    while "Service providers" not in svc(e, "-i", "--service", f"/world/{world}/scene/info").stdout:
        if time.monotonic() - t0 > 90:
            raise RuntimeError(f"{tag}: świat nie wstał")
        time.sleep(1)
    res = {}
    for i, (pn, (x, y, z, pitch, yaw)) in enumerate(POSES.items()):
        name = f"probe_{i}"
        node = Node()
        base = f"/world/{world}/model/{name}/link"
        g = Grab(node, f"{base}/camera_link/sensor/imager/image")
        gf = Grab(node, f"{base}/flow_link/sensor/flow_camera/image") if tag == "T" else None
        cp, sp = math.cos(math.radians(pitch) / 2), math.sin(math.radians(pitch) / 2)
        cy, sy = math.cos(yaw / 2), math.sin(yaw / 2)
        q = {"w": cy * cp, "x": -sy * sp, "y": cy * sp, "z": sy * cp}     # q = Rz(yaw)·Ry(pitch)
        req = (f'sdf_filename: "{ZR}/{rig}", name: "{name}", allow_renaming: false, pose: {{position: {{x: {x}, y: {y}, z: {z}}}, '
               f'orientation: {{w: {q["w"]}, x: {q["x"]}, y: {q["y"]}, z: {q["z"]}}}}}')
        r = svc(e, "-s", f"/world/{world}/create", "--reqtype", "gz.msgs.EntityFactory", "--reptype", "gz.msgs.Boolean",
                "--timeout", "10000", "--req", req)
        assert "true" in r.stdout, (tag, pn, r.stdout, r.stderr)
        t1 = time.monotonic()
        while not (g.done() and (gf is None or gf.done())):
            if time.monotonic() - t1 > POSE_TMO:
                raise RuntimeError(f"{tag} {pn}: brak klatek n={g.n} flow={gf.n if gf else None}")
            time.sleep(0.2)
        res[pn] = {"n_kl": g.n, "wewn_max": int(max(np.abs(a.astype(int) - g.frames[0].astype(int)).max() for a in g.frames))}
        cv2.imwrite(os.path.join(OUT, f"{tag}_{pn}.png"), g.frames[-1][:, :, ::-1] if g.frames[-1].shape[2] == 3 else g.frames[-1])
        if gf:
            cv2.imwrite(os.path.join(OUT, f"flow_{pn}.png"), gf.frames[-1])
        r = svc(e, "-s", f"/world/{world}/remove", "--reqtype", "gz.msgs.Entity", "--reptype", "gz.msgs.Boolean",
                "--timeout", "5000", "--req", f'name: "{name}" type: MODEL')
        del node
        time.sleep(1)
        print(tag, pn, res[pn], flush=True)
    srv.kill()
    teardown()
    return res


def diff(a, b):
    d = np.abs(cv2.imread(a, -1).astype(int) - cv2.imread(b, -1).astype(int))
    return int(d.max()), int((d.reshape(d.shape[0], d.shape[1], -1).max(axis=2) > 0).sum())


def compare(meta):
    tab = {}
    for pn in POSES:
        f = lambda t: os.path.join(OUT, f"{t}_{pn}.png")
        kmax, kn = diff(f("R1"), f("R2"))
        tmax, tn = diff(f("R1"), f("T"))
        nmax, nn = diff(f("R1"), f("N"))
        fl = cv2.imread(os.path.join(OUT, f"flow_{pn}.png"), -1)
        tab[pn] = {"K_max": kmax, "K_n": kn, "T_max": tmax, "T_n": tn, "N_max": nmax, "N_n": nn,
                   "identyczne": tmax <= kmax and tn <= kn, "flow_std": round(float(fl.std()), 1),
                   "imager_std": round(float(cv2.imread(f("T"), -1).std()), 1)}
        print(pn, tab[pn])
    w = all(v["identyczne"] for v in tab.values())
    res = {"werdykt_identycznosc": "PASS" if w else "FAIL", "tabela": tab, "pozy": POSES, **meta}
    json.dump(res, open(os.path.join(ROOT, "results/KONT/s1/bootA/frames_identity.json"), "w"), ensure_ascii=False, indent=1)
    print("IDENTYCZNOSC", res["werdykt_identycznosc"])
    return w


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.join(ROOT, "results/KONT/s1/bootA"), exist_ok=True)
    if "--compare" in sys.argv:
        sys.exit(0 if compare({}) else 1)
    e = env()
    teardown()
    meta = {"przebiegi": {}}
    for tag, world, rig in RUNS:
        with open(os.path.join(ROOT, f"results/KONT/s1/bootA/gz_{tag}.log"), "w") as log:
            meta["przebiegi"][tag] = {"swiat": world, "rig": rig, "pozy": run_one(tag, world, rig, e, log)}
    sys.exit(0 if compare(meta) else 1)


if __name__ == "__main__":
    main()
