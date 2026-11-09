#!/usr/bin/env python3
"""results/NADIR/tools/nadir_ab.py — diagnostyka tempa A/B po STOP-NADIR1-TEMPO (decyzja Olgi 9.11: „rób test A/B”).
Goły gz bez PX4 (wzór B0 z KONT), 0 bootów lotnych. Rozdziela hipotezy: (a) drugi render nadir vs (b) stanowisko.

Przebieg (×4, naprzemiennie A, B, A, B): serwer gz -r -s world_nadir_A3 (świat bootu b2), statyczny rig na pozie
patrolu (5, 5, 12) — A = rig_nadir (x500_nadir_flow: imager + przepływ + nadir), B = rig_flow KONT (x500_mono_cam_flow:
imager + przepływ). Konsumenci jak w boocie: subskrypcja imagera, kamery przepływu i (A) nadir w procesie gz-transport;
klatki nadir przechodzą przez detekcję cv2.aruco (jak harness/nadir_obs.py). acts/rtf_sampler.py (READ-ONLY) zapisuje
sim↔wall; po rozgrzewce WARM_S liczę dsim/dwall z regresji liniowej po oknie WIN_S (metryka bramki tempa KONT 4d)
oraz liczbę klatek per kamera. Wynik: results/NADIR/s1/ab/ab_tempo.json.
"""
import json
import os
import subprocess
import sys
import threading
import time

import cv2
import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, os.path.join(ROOT, "results/NADIR/tools"))
import nadir_frames as NF                                  # env(), svc(), teardown(), instaluj_model(), quat() — READ-ONLY

AB = os.path.join(ROOT, "results/NADIR/s1/ab")
W = "world_nadir_A3"
RIGS = {"A_nadir": os.path.join(ROOT, "results/NADIR/s1/zrodla/rig_nadir.sdf"),
        "B_flow": os.path.join(ROOT, "results/KONT/s1/zrodla/rig_flow.sdf")}
ORDER = ["A_nadir", "B_flow", "A_nadir", "B_flow"]
WARM_S, WIN_S = 20.0, 120.0
if hasattr(cv2.aruco, "ArucoDetector"):
    _DET = cv2.aruco.ArucoDetector(cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50), cv2.aruco.DetectorParameters())
    detm = lambda g: _DET.detectMarkers(g)
else:
    _D, _P = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50), cv2.aruco.DetectorParameters_create()
    detm = lambda g: cv2.aruco.detectMarkers(g, _D, parameters=_P)


class Licz:
    def __init__(self, node, topic, detekcja=False):
        from gz.msgs10.image_pb2 import Image
        self.n, self.ndet, self.det = 0, 0, detekcja
        node.subscribe(Image, topic, self._cb)

    def _cb(self, m):
        self.n += 1
        if self.det:
            ch = len(m.data) // (m.width * m.height)
            img = np.frombuffer(m.data, np.uint8).reshape(m.height, m.width, ch)
            g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY) if ch == 3 else img[:, :, 0]
            _, ids, _ = detm(g)
            self.ndet += ids is not None


def regresja(p):
    r = [json.loads(l) for l in open(p) if l.strip()]
    if len(r) < 10:
        return None, len(r)
    t0 = r[0]["wall"]
    seg = [x for x in r if WARM_S <= x["wall"] - t0 <= WARM_S + WIN_S]
    w = np.array([x["wall"] for x in seg]); s = np.array([x["sim"] for x in seg])
    return round(float(np.polyfit(w - w[0], s - s[0], 1)[0]), 4), len(seg)


def run(i, tag, e):
    from gz.transport13 import Node
    log = open(os.path.join(AB, f"gz_{i}_{tag}.log"), "w")
    srv = subprocess.Popen(["gz", "sim", "--verbose=1", "-r", "-s", f"{e['PX4_GZ_WORLDS']}/{W}.sdf"], env=e, stdout=log, stderr=log)
    t0 = time.monotonic()
    while "Service providers" not in NF.svc(e, "-i", "--service", f"/world/{W}/scene/info").stdout:
        assert time.monotonic() - t0 < 90, "świat nie wstał"
        time.sleep(1)
    q = NF.quat(0, 0, 30)
    req = (f'sdf_filename: "{RIGS[tag]}", name: "probe", allow_renaming: false, pose: {{position: {{x: 5, y: 5, z: 12}}, '
           f'orientation: {{w: {q[0]}, x: {q[1]}, y: {q[2]}, z: {q[3]}}}}}')
    r = NF.svc(e, "-s", f"/world/{W}/create", "--reqtype", "gz.msgs.EntityFactory", "--reptype", "gz.msgs.Boolean",
               "--timeout", "10000", "--req", req)
    assert "true" in r.stdout, r.stdout + r.stderr
    node = Node()
    base = f"/world/{W}/model/probe/link"
    L = {"imager": Licz(node, f"{base}/camera_link/sensor/imager/image"),
         "flow": Licz(node, f"{base}/flow_link/sensor/flow_camera/image")}
    if tag.startswith("A"):
        L["nadir"] = Licz(node, f"{base}/nadir_link/sensor/nadir/image", detekcja=True)
    rp = os.path.join(AB, f"rtf_{i}_{tag}.jsonl")
    rs = subprocess.Popen([sys.executable, "-m", "acts.rtf_sampler", "--world", W, "--out", rp], cwd=ROOT, env=e,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(WARM_S + WIN_S + 3)
    rs.terminate(); rs.wait(timeout=10)
    srv.kill()
    NF.teardown()
    tempo, n = regresja(rp)
    load = open("/proc/loadavg").read().split()[0]
    res = {"tag": tag, "dsim_dwall": tempo, "n_probek_okna": n, "loadavg1_po": float(load),
           "klatki": {k: v.n for k, v in L.items()}, "nadir_klatki_z_id": L["nadir"].ndet if "nadir" in L else None,
           "hz": {k: round(v.n / (WARM_S + WIN_S), 2) for k, v in L.items()}}
    del node
    print(i, res, flush=True)
    return res


def main():
    os.makedirs(AB, exist_ok=True)
    e = NF.env()
    meta = {"opis": __doc__.split("\n\n")[0], "instalacja_modelu": NF.instaluj_model(), "opencv": cv2.__version__,
            "timesyncd": subprocess.run(["systemctl", "is-active", "systemd-timesyncd"], capture_output=True, text=True).stdout.strip(),
            "warm_s": WARM_S, "win_s": WIN_S, "przebiegi": []}
    NF.teardown()
    for i, tag in enumerate(ORDER):
        meta["przebiegi"].append(run(i, tag, e))
    a = [x["dsim_dwall"] for x in meta["przebiegi"] if x["tag"].startswith("A")]
    b = [x["dsim_dwall"] for x in meta["przebiegi"] if x["tag"].startswith("B")]
    meta["srednia"] = {"A_nadir": round(sum(a) / len(a), 4), "B_flow": round(sum(b) / len(b), 4)}
    json.dump(meta, open(os.path.join(AB, "ab_tempo.json"), "w"), ensure_ascii=False, indent=1)
    print("ŚREDNIA", meta["srednia"])


if __name__ == "__main__":
    main()
