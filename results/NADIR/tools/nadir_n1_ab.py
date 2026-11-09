#!/usr/bin/env python3
"""results/NADIR/tools/nadir_n1_ab.py — ANEKS_NADIR-1 §CO (1)+(2): A/B kadencji nadir {5, 3, 2} Hz i maska kadłuba montażu v2.
Goły gz bez PX4 (wzór B0 / nadir_ab.py), 0 bootów lotnych. Funkcje pomocnicze importowane READ-ONLY z nadir_ab.py
(Licz, regresja) i nadir_frames.py (env, svc, teardown, quat).

Rigi (generowane do results/NADIR/s1/zrodla/n1/, statyczne, nie instalowane do PX4):
  B      = results/KONT/s1/zrodla/rig_flow.sdf (x500_mono_cam_flow: imager + przepływ);
  A_<r>  = x500_mono_cam_flow + nadir_link montaż v2 (0, 0, −0.215 m względem base_link: między płozami x500 na ich
           wysokości — płozy y = ±0.132, z_środka −0.2195, spód −0.227 wg x500_base/model.sdf collision_3/4; prześwit
           na ziemi 0.025 m) + czujnik nadir jak v1 (640×480, hfov 1.74, oś −z_body) z update_rate = r.
Kolejność: B, A5, A3, A2, B, A2, A3, A5, B (każdy wariant ×2, B ×3, przeplot). Konsumenci jak w boocie (nadir z detekcją).
Przeniesione tempo = 0.97 · (tempo_A / średnie tempo B sesji) — baza ANEKS §2.2; wybór: najwyższa r z przeniesionym ≥ 0.94.
Maska v2: rig A_5 w dwóch pozach o tej samej postawie (p6: (9, −8, 12), p8: (1, 1, 3), roll = pitch = yaw = 0), metoda
nadir_maska.py (|Δ| ≤ 1 → close 9 → składowe ≥ 800 px → ∪ odbicie → dylatacja 2); wymóg ≤ 2% stożka centralnego.
Wynik: results/NADIR/s1/n1/ab_kadencja.json, maska_v2.png/json, klatki maski.
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
import nadir_frames as NF
import nadir_ab as AB

N1 = os.path.join(ROOT, "results/NADIR/s1/n1")
ZRN = os.path.join(ROOT, "results/NADIR/s1/zrodla/n1")
W = "world_nadir_A3"
MOUNT_Z = -0.215
RATES = (5, 3, 2)
ORDER = ["B", "A5", "A3", "A2", "B", "A2", "A3", "A5", "B"]
BAZA, PROG = 0.97, 0.94


def rig(r):
    p = os.path.join(ZRN, f"rig_ab_{r}hz.sdf")
    open(p, "w").write(f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- ANEKS_NADIR-1 A/B: statyczny rig x500_mono_cam_flow + nadir montaż v2 ({MOUNT_Z} m), {r} Hz. Tylko gz bez PX4. -->
<sdf version='1.9'>
  <model name='probe'>
    <static>true</static>
    <include merge='true'>
      <uri>x500_mono_cam_flow</uri>
    </include>
    <link name="nadir_link">
      <pose relative_to="base_link">0 0 {MOUNT_Z} 0 0 0</pose>
      <inertial><mass>0.001</mass><inertia><ixx>0.00001</ixx><iyy>0.00001</iyy><izz>0.00001</izz><ixy>0</ixy><ixz>0</ixz><iyz>0</iyz></inertia></inertial>
      <sensor name="nadir" type="camera">
        <pose>0 0 0 0 1.5707963 0</pose>
        <camera>
          <horizontal_fov>1.74</horizontal_fov>
          <image><width>640</width><height>480</height></image>
          <clip><near>0.1</near><far>100</far></clip>
        </camera>
        <always_on>1</always_on>
        <update_rate>{r}</update_rate>
        <visualize>false</visualize>
      </sensor>
    </link>
    <joint name="nadir_joint" type="fixed">
      <parent>base_link</parent>
      <child>nadir_link</child>
    </joint>
  </model>
</sdf>
""")
    return p


def serwer(e, tag):
    log = open(os.path.join(N1, f"gz_{tag}.log"), "w")
    srv = subprocess.Popen(["gz", "sim", "--verbose=1", "-r", "-s", f"{e['PX4_GZ_WORLDS']}/{W}.sdf"], env=e, stdout=log, stderr=log)
    t0 = time.monotonic()
    while "Service providers" not in NF.svc(e, "-i", "--service", f"/world/{W}/scene/info").stdout:
        assert time.monotonic() - t0 < 90, "świat nie wstał"
        time.sleep(1)
    return srv


def spawn(e, path, name, x, y, z, ro=0, pi=0, ya=0):
    q = NF.quat(ro, pi, ya)
    req = (f'sdf_filename: "{path}", name: "{name}", allow_renaming: false, pose: {{position: {{x: {x}, y: {y}, z: {z}}}, '
           f'orientation: {{w: {q[0]}, x: {q[1]}, y: {q[2]}, z: {q[3]}}}}}')
    r = NF.svc(e, "-s", f"/world/{W}/create", "--reqtype", "gz.msgs.EntityFactory", "--reptype", "gz.msgs.Boolean",
               "--timeout", "10000", "--req", req)
    assert "true" in r.stdout, r.stdout + r.stderr


def run(i, tag, e):
    from gz.transport13 import Node
    srv = serwer(e, f"{i}_{tag}")
    path = os.path.join(ROOT, "results/KONT/s1/zrodla/rig_flow.sdf") if tag == "B" else rig(int(tag[1:]))
    spawn(e, path, "probe", 5, 5, 12, 0, 0, 30)
    node = Node()
    base = f"/world/{W}/model/probe/link"
    L = {"imager": AB.Licz(node, f"{base}/camera_link/sensor/imager/image"),
         "flow": AB.Licz(node, f"{base}/flow_link/sensor/flow_camera/image")}
    if tag != "B":
        L["nadir"] = AB.Licz(node, f"{base}/nadir_link/sensor/nadir/image", detekcja=True)
    rp = os.path.join(N1, f"rtf_{i}_{tag}.jsonl")
    rs = subprocess.Popen([sys.executable, "-m", "acts.rtf_sampler", "--world", W, "--out", rp], cwd=ROOT, env=e,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(AB.WARM_S + AB.WIN_S + 3)
    rs.terminate(); rs.wait(timeout=10)
    srv.kill(); srv.wait(timeout=10)
    NF.teardown()
    tempo, n = AB.regresja(rp)
    r = [json.loads(l) for l in open(rp)]
    cof = sum(r[k]["sim"] < r[k - 1]["sim"] or r[k]["wall"] < r[k - 1]["wall"] for k in range(1, len(r)))
    res = {"tag": tag, "dsim_dwall": tempo, "n_probek_okna": n, "cofniecia": cof, "loadavg1_po": float(open("/proc/loadavg").read().split()[0]),
           "hz": {k: round(v.n / (AB.WARM_S + AB.WIN_S), 2) for k, v in L.items()},
           "nadir_klatki_z_id": L["nadir"].ndet if "nadir" in L else None}
    del node
    print(i, res, flush=True)
    return res


class Grab1:
    def __init__(self, node, topic, n_skip=10):
        from gz.msgs10.image_pb2 import Image
        self.f, self.n, self.skip, self.lock = None, 0, n_skip, threading.Lock()
        node.subscribe(Image, topic, self._cb)

    def _cb(self, m):
        with self.lock:
            self.n += 1
            if self.n > self.skip and self.f is None:
                ch = len(m.data) // (m.width * m.height)
                im = np.frombuffer(m.data, np.uint8).reshape(m.height, m.width, ch)
                self.f = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY) if ch == 3 else im[:, :, 0].copy()


def maska(e):
    from gz.transport13 import Node
    srv = serwer(e, "maska")
    out = {}
    path = rig(5)
    for k, (x, y, z) in enumerate(((9, -8, 12), (1, 1, 3), (-4, 6, 8))):
        name = f"m{k}"
        node = Node()
        g = Grab1(node, f"/world/{W}/model/{name}/link/nadir_link/sensor/nadir/image")
        spawn(e, path, name, x, y, z)
        t0 = time.monotonic()
        while g.f is None:
            assert time.monotonic() - t0 < 120, "brak klatek nadir"
            time.sleep(0.2)
        cv2.imwrite(os.path.join(N1, f"nadir_v2_{k}_{x}_{y}_{z}.png"), g.f)
        out[k] = g.f.astype(int)
        NF.svc(e, "-s", f"/world/{W}/remove", "--reqtype", "gz.msgs.Entity", "--reptype", "gz.msgs.Boolean", "--timeout", "5000",
               "--req", f'name: "{name}" type: MODEL')
        del node
        time.sleep(1)
    srv.kill(); srv.wait(timeout=10)
    NF.teardown()
    e_ = (np.abs(out[0] - out[1]) <= 1).astype(np.uint8)
    c = cv2.morphologyEx(e_, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(c)
    m = np.zeros_like(c)
    for i in range(1, n):
        if st[i, 4] >= 800:
            m[lab == i] = 1
    m = np.maximum(m, cv2.flip(m, 1))
    m = cv2.dilate(m, np.ones((5, 5), np.uint8)) > 0
    cv2.imwrite(os.path.join(N1, "maska_v2.png"), m.astype(np.uint8) * 255)
    H, Wd = m.shape
    cc = m[int(0.1 * H):int(0.9 * H), int(0.1 * Wd):int(0.9 * Wd)]
    # kontrola trzecią pozą: maska z pary (0, 2) — to samo kryterium
    e2 = (np.abs(out[0] - out[2]) <= 1).astype(np.uint8)
    res = {"montaz_z_m": MOUNT_Z, "frac_kadr": round(float(m.mean()), 5), "frac_stozek_centralny": round(float(cc.mean()), 5),
           "wymog_le": 0.02, "pass": float(cc.mean()) <= 0.02, "rowne_px_kontrola_p0_p2": round(float(e2.mean()), 5)}
    json.dump(res, open(os.path.join(N1, "maska_v2.json"), "w"), ensure_ascii=False, indent=1)
    print("MASKA", res, flush=True)
    return res


def main():
    os.makedirs(N1, exist_ok=True)
    os.makedirs(ZRN, exist_ok=True)
    e = NF.env()
    NF.teardown()
    meta = {"opis": __doc__.split("\n\n")[0], "montaz_z_m": MOUNT_Z, "kolejnosc": ORDER, "baza": BAZA, "prog": PROG,
            "timesyncd": subprocess.run(["systemctl", "is-active", "systemd-timesyncd"], capture_output=True, text=True).stdout.strip(),
            "opencv": cv2.__version__, "przebiegi": []}
    if "--tylko-maska" not in sys.argv:
        for i, tag in enumerate(ORDER):
            meta["przebiegi"].append(run(i, tag, e))
        tb = [x["dsim_dwall"] for x in meta["przebiegi"] if x["tag"] == "B"]
        mb = sum(tb) / len(tb)
        wyn = {}
        for r in RATES:
            ta = [x["dsim_dwall"] for x in meta["przebiegi"] if x["tag"] == f"A{r}"]
            ma = sum(ta) / len(ta)
            wyn[f"{r}Hz"] = {"tempo_A": [round(x, 4) for x in ta], "stosunek": round(ma / mb, 4), "przeniesione": round(BAZA * ma / mb, 4),
                             "ok_094": BAZA * ma / mb >= PROG, "ok_093": BAZA * ma / mb >= 0.93}
        meta["B_srednia"] = round(mb, 4)
        meta["warianty"] = wyn
        ok = [r for r in RATES if wyn[f"{r}Hz"]["ok_094"]]
        meta["wybor_hz"] = max(ok) if ok else None
        meta["werdykt"] = "WYBÓR" if ok else ("STOP: żadna ≥ 0.94" + (" (≥ 0.93 jest)" if any(wyn[f"{r}Hz"]["ok_093"] for r in RATES) else " ani ≥ 0.93"))
        print("KADENCJA", wyn, meta["wybor_hz"], meta["werdykt"], flush=True)
    meta["maska_v2"] = maska(e)
    json.dump(meta, open(os.path.join(N1, "ab_kadencja.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
