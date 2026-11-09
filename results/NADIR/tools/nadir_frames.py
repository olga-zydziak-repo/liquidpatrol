#!/usr/bin/env python3
"""results/NADIR/tools/nadir_frames.py — boot b1 S1 NADIR (PROMPT_NADIR_S1 §2.1, R1 + R3 statycznie). Gz bez PX4, bez lotu.
Wzór: results/KONT/tools/kont_frames.py (oryginał nietknięty) — ten sam mechanizm (serwer gz per przebieg, statyczny rig na
stałej pozie, N_SKIP klatek rozgrzewki, N_KEEP klatek do porównania), inne przebiegi i pozy.

Przebiegi:
  R1, R2 = rig_nadir (x500_nadir_flow) na world_kont_A3 — kontrola szumu renderu (K);
  T      = rig_nadir na world_nadir_A3 — test: klatki imagera różne WYŁĄCZNIE w masce rzutu płyt znaczników;
  M      = rig_flow (x500_mono_cam_flow, KONT) na world_kont_A3 — model-wariant nie zmienia klatek misji ani przepływu.
Metryki per poza (imager i flow_camera): max|Δ| i liczba pikseli ≠ 0; dla T dodatkowo poza maską (rzut płyt 1.3333 m przez
pinhole imagera f = 269.5 px z pozy rigu i montażu mono_cam .12 .03 .242, dylatacja MASK_DIL px). Werdykt R1 ⇔ T_poza_maska = 0
we wszystkich pozach (piksele różne poza maską liczone dopiero ponad szum K: |Δ| > K_max danej pozy).
Nadir (T): detekcja cv2.aruco (DICT_4X4_50) na klatkach z rigu; pozycja z każdego znacznika w stożku centralnym (edge ≥ 0.10)
przy POZIE PRAWDZIWEJ (postawa i wysokość dokładne) — błąd czysto pikselowo-modelowy (R3 statycznie). Dla każdej pozy
też liczba znaczników przewidzianych geometrią w stożku i bok px — do R6.
PNG bezstratne w results/NADIR/s1/b1/frames/. Tryby: bez argumentów = przebiegi + porównanie; --compare = z PNG.
"""
import json
import math
import os
import shutil
import subprocess
import sys
import threading
import time

import cv2
import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
B1 = os.path.join(ROOT, "results/NADIR/s1/b1")
OUT = os.path.join(B1, "frames")
ZR = os.path.join(ROOT, "results/NADIR/s1/zrodla")
ZR_KONT = os.path.join(ROOT, "results/KONT/s1/zrodla")
MODELS = os.path.join(ROOT, "PX4-Autopilot/Tools/simulation/gz/models")
MAN = json.load(open(os.path.join(ROOT, "results/NADIR/s1/manifest_znaczniki.json")))
KW, NW = "world_kont_A3", "world_nadir_A3"
RUNS = [("R1", KW, os.path.join(ZR, "rig_nadir.sdf")), ("T", NW, os.path.join(ZR, "rig_nadir.sdf")),
        ("R2", KW, os.path.join(ZR, "rig_nadir.sdf")), ("M", KW, os.path.join(ZR_KONT, "rig_flow.sdf"))]
F = 320.0 / math.tan(0.87)
IW, IH = 640, 480
CAM = np.array([0.12, 0.03, 0.242])
PLATE = MAN["plyta_m"]
MASK_DIL = 4
EDGE = 0.10
# (x E, y N, z, roll°, pitch°, yaw°) ENU gz; pitch > 0 = nos w dół
POSES = {"p1_hold_z8.4": (0.3, -0.2, 8.4, 0, 0, 90), "p2_z12_5_5": (5, 5, 12, 0, 0, 30),
         "p3_z12_3_m4_tilt": (3, -4, 12, 6, 8, -60), "p4_orbit_r15_out": (12.99, 7.5, 12, 0, 8, 30),
         "p5_orbit_r25_in": (-21.65, -12.5, 12, -5, 6, 30 + 180 - 180), "p6_z12_pochowany_m24": (9, -8, 12, 0, 0, 0),
         "p7_z5_zejscie": (4, 6, 5, 0, 0, 120), "p8_z3": (1, 1, 3, 0, 0, 0), "p9_z12_tilt15": (-6, 14, 12, 15, 0, 200),
         "p10_r28_out_pitch12": (24.25, -14, 12, 0, 12, -30)}
N_SKIP, N_KEEP, POSE_TMO = 30, 5, 90.0


def env():
    e = dict(os.environ)
    src = "source env_gpu.sh >/dev/null; cd PX4-Autopilot/build/px4_sitl_default/rootfs && . ./gz_env.sh; env -0"
    raw = subprocess.check_output(["bash", "-c", f"cd {ROOT}; {src}"])
    e.update(dict(kv.split("=", 1) for kv in raw.decode().split("\0") if "=" in kv))
    e.update(GZ_IP="127.0.0.1", HEADLESS="1", GALLIUM_DRIVER="d3d12", MESA_D3D12_DEFAULT_ADAPTER_NAME="NVIDIA")
    return e


def instaluj_model():
    """Kopia źródła modelu do PX4 models/ (nowy katalog). Istniejący katalog musi być identyczny — inaczej odmowa."""
    dst = os.path.join(MODELS, "x500_nadir_flow")
    src = os.path.join(ZR, "x500_nadir_flow")
    if os.path.isdir(dst):
        for f in os.listdir(src):
            assert open(os.path.join(src, f), "rb").read() == open(os.path.join(dst, f), "rb").read(), f"różny {f} w {dst}"
        return "istniał, identyczny"
    shutil.copytree(src, dst)
    return "skopiowany"


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


def quat(roll, pitch, yaw):
    """q = Rz(yaw)·Ry(pitch)·Rx(roll), stopnie → (w, x, y, z)."""
    r, p, y = (math.radians(a) / 2 for a in (roll, pitch, yaw))
    cr, sr, cp, sp, cy, sy = math.cos(r), math.sin(r), math.cos(p), math.sin(p), math.cos(y), math.sin(y)
    return (cy * cp * cr + sy * sp * sr, cy * cp * sr - sy * sp * cr, cy * sp * cr + sy * cp * sr, sy * cp * cr - cy * sp * sr)


def rotm(q):
    w, x, y, z = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                     [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                     [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])


def run_one(tag, world, rig, e, log):
    from gz.transport13 import Node
    os.environ.update(GZ_IP="127.0.0.1")
    rc = subprocess.run(["bash", "harness/world_hash.sh", world, B1], cwd=ROOT, capture_output=True, text=True)
    assert rc.returncode == 0, rc.stdout
    srv = subprocess.Popen(["gz", "sim", "--verbose=1", "-r", "-s", f"{e['PX4_GZ_WORLDS']}/{world}.sdf"], env=e, stdout=log, stderr=log)
    t0 = time.monotonic()
    while "Service providers" not in svc(e, "-i", "--service", f"/world/{world}/scene/info").stdout:
        if time.monotonic() - t0 > 90:
            raise RuntimeError(f"{tag}: świat nie wstał")
        time.sleep(1)
    res = {}
    nadir = "rig_nadir" in rig
    for i, (pn, (x, y, z, ro, pi, ya)) in enumerate(POSES.items()):
        name = f"probe_{i}"
        node = Node()
        base = f"/world/{world}/model/{name}/link"
        g = Grab(node, f"{base}/camera_link/sensor/imager/image")
        gf = Grab(node, f"{base}/flow_link/sensor/flow_camera/image")
        gn = Grab(node, f"{base}/nadir_link/sensor/nadir/image") if nadir else None
        q = quat(ro, pi, ya)
        req = (f'sdf_filename: "{rig}", name: "{name}", allow_renaming: false, pose: {{position: {{x: {x}, y: {y}, z: {z}}}, '
               f'orientation: {{w: {q[0]}, x: {q[1]}, y: {q[2]}, z: {q[3]}}}}}')
        r = svc(e, "-s", f"/world/{world}/create", "--reqtype", "gz.msgs.EntityFactory", "--reptype", "gz.msgs.Boolean",
                "--timeout", "10000", "--req", req)
        assert "true" in r.stdout, (tag, pn, r.stdout, r.stderr)
        t1 = time.monotonic()
        while not (g.done() and gf.done() and (gn is None or gn.done())):
            if time.monotonic() - t1 > POSE_TMO:
                raise RuntimeError(f"{tag} {pn}: brak klatek n={g.n} flow={gf.n} nadir={gn.n if gn else None}")
            time.sleep(0.2)
        res[pn] = {"n_kl": g.n, "wewn_max": int(max(np.abs(a.astype(int) - g.frames[0].astype(int)).max() for a in g.frames))}
        cv2.imwrite(os.path.join(OUT, f"{tag}_{pn}.png"), g.frames[-1][:, :, ::-1] if g.frames[-1].shape[2] == 3 else g.frames[-1])
        cv2.imwrite(os.path.join(OUT, f"flow{tag}_{pn}.png"), gf.frames[-1])
        if gn:
            cv2.imwrite(os.path.join(OUT, f"nadir{tag}_{pn}.png"), gn.frames[-1][:, :, ::-1] if gn.frames[-1].shape[2] == 3 else gn.frames[-1])
        svc(e, "-s", f"/world/{world}/remove", "--reqtype", "gz.msgs.Entity", "--reptype", "gz.msgs.Boolean",
            "--timeout", "5000", "--req", f'name: "{name}" type: MODEL')
        del node
        time.sleep(1)
        print(tag, pn, res[pn], flush=True)
    srv.kill()
    teardown()
    return res


def diff(a, b):
    d = np.abs(cv2.imread(a, -1).astype(int) - cv2.imread(b, -1).astype(int))
    d = d.reshape(d.shape[0], d.shape[1], -1).max(axis=2)
    return d


def maska(pose):
    """Rzut płyt znaczników do imagera (pinhole, montaż mono_cam), dylatacja MASK_DIL px."""
    x, y, z, ro, pi, ya = pose
    R = rotm(quat(ro, pi, ya))
    cam = np.array([x, y, z]) + R @ CAM
    m = np.zeros((IH, IW), np.uint8)
    h = PLATE / 2
    for zn in MAN["znaczniki"]:
        pts = []
        for dx, dy in ((-h, -h), (h, -h), (h, h), (-h, h)):
            b = R.T @ (np.array([zn["E"] + dx, zn["N"] + dy, zn["z"]]) - cam)
            if b[0] <= 0.1:
                pts = None
                break
            pts.append((IW / 2 - F * b[1] / b[0], IH / 2 - F * b[2] / b[0]))
        if pts:
            cv2.fillConvexPoly(m, np.round(np.array(pts)).astype(np.int32), 255)
    return cv2.dilate(m, np.ones((2 * MASK_DIL + 1, 2 * MASK_DIL + 1), np.uint8)) > 0


def nadir_pred(pose):
    """Znaczniki w stożku centralnym nadir z geometrii pozy: id → (u, v, bok_px)."""
    x, y, z, ro, pi, ya = pose
    R = rotm(quat(ro, pi, ya))
    p = np.array([x, y, z])
    out = {}
    for zn in MAN["znaczniki"]:
        def uv(P):
            b = R.T @ (P - p)
            d = -b[2]
            return (IW / 2 + F * (-b[1]) / d, IH / 2 + F * (-b[0]) / d) if d > 0.1 else None
        c = uv(np.array([zn["E"], zn["N"], zn["z"]]))
        if c is None:
            continue
        cx, cy = c[0] / IW, c[1] / IH
        if min(cx, 1 - cx, cy, 1 - cy) < EDGE:
            continue
        a, b_ = uv(np.array([zn["E"] - 0.5, zn["N"], zn["z"]])), uv(np.array([zn["E"] + 0.5, zn["N"], zn["z"]]))
        a2, b2 = uv(np.array([zn["E"], zn["N"] - 0.5, zn["z"]])), uv(np.array([zn["E"], zn["N"] + 0.5, zn["z"]]))
        bok = min(math.dist(a, b_), math.dist(a2, b2))
        out[zn["id"]] = (round(c[0], 1), round(c[1], 1), round(bok, 1))
    return out


def srodek(c):
    """Przecięcie przekątnych czworokąta narożników (4,2)."""
    p1, p2, p3, p4 = c
    d1, d2 = p3 - p1, p4 - p2
    A = np.array([d1, -d2]).T
    t = np.linalg.solve(A, p2 - p1)
    return p1 + t[0] * d1


def fix_z_pozy(pose, u, v, zn):
    """Pozycja drona (E, N) z jednego znacznika przy pozie prawdziwej (postawa + wysokość)."""
    x, y, z, ro, pi, ya = pose
    R = rotm(quat(ro, pi, ya))
    ys, zs = -(u - IW / 2) / F, -(v - IH / 2) / F
    ray_b = np.array([zs, ys, -1.0])
    ray = R @ ray_b
    t = (zn["z"] - z) / ray[2]
    return np.array([zn["E"], zn["N"]]) - t * ray[:2]


def detekcja(pn, pose):
    im = cv2.imread(os.path.join(OUT, f"nadirT_{pn}.png"), 0)
    d = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)
    par = cv2.aruco.DetectorParameters_create()
    out = {"lustro": False}
    corners, ids, _ = cv2.aruco.detectMarkers(im, d, parameters=par)
    if ids is None:
        cf, idf, _ = cv2.aruco.detectMarkers(cv2.flip(im, 1), d, parameters=par)
        if idf is not None:
            out["lustro"] = True
            corners, ids = [np.stack([IW - 1 - c[0][:, 0], c[0][:, 1]], axis=1)[None] for c in cf], idf
    pred = nadir_pred(pose)
    zn = {z["id"]: z for z in MAN["znaczniki"]}
    det = []
    for c, i in zip(corners if ids is not None else [], ids.ravel() if ids is not None else []):
        c = c.reshape(4, 2).astype(float)
        s = srodek(c)
        bok = min(np.linalg.norm(c[k] - c[(k + 1) % 4]) for k in range(4))
        cx, cy = s[0] / IW, s[1] / IH
        cen = min(cx, 1 - cx, cy, 1 - cy) >= EDGE
        rec = {"id": int(i), "u": round(float(s[0]), 2), "v": round(float(s[1]), 2), "bok_px": round(float(bok), 1), "centralny": bool(cen)}
        if int(i) in zn:
            f = fix_z_pozy(pose, s[0], s[1], zn[int(i)])
            rec["blad_fix_m"] = round(float(np.hypot(f[0] - pose[0], f[1] - pose[1])), 3)
            rec["r_h_m"] = round(math.hypot(zn[int(i)]["E"] - pose[0], zn[int(i)]["N"] - pose[1]), 2)
            if int(i) in pred:
                rec["pred_uv_bok"] = pred[int(i)]
        det.append(rec)
    out["wykryte"] = det
    out["przewidziane_w_stozku"] = {str(k): v for k, v in pred.items()}
    out["pominiete"] = sorted(set(pred) - {r["id"] for r in det})
    return out


def compare(meta):
    tab = {}
    for pn, pose in POSES.items():
        f = lambda t: os.path.join(OUT, f"{t}_{pn}.png")
        K = diff(f("R1"), f("R2"))
        T = diff(f("R1"), f("T"))
        M = diff(f("R1"), f("M"))
        FK = diff(f("flowR1"), f("flowR2"))
        FT = diff(f("flowR1"), f("flowT"))
        FM = diff(f("flowR1"), f("flowM"))
        NK = diff(f("nadirR1"), f("nadirR2"))
        mk = maska(pose)
        kmax = int(K.max())
        tab[pn] = {"K_max": kmax, "K_n": int((K > 0).sum()),
                   "T_n": int((T > 0).sum()), "T_max": int(T.max()), "maska_px": int(mk.sum()),
                   "T_poza_maska_n": int(((T > kmax) & ~mk).sum()), "T_poza_maska_max": int(np.where(mk, 0, T).max()),
                   "M_max": int(M.max()), "M_n": int((M > kmax).sum()),
                   "flow_K_max": int(FK.max()), "flow_T_max": int(FT.max()), "flow_T_n": int((FT > FK.max()).sum()),
                   "flow_M_max": int(FM.max()), "flow_M_n": int((FM > FK.max()).sum()),
                   "nadir_K_max": int(NK.max()),
                   "nadir": detekcja(pn, pose)}
        t = tab[pn]
        t["identyczne_poza_maska"] = t["T_poza_maska_n"] == 0
        t["model_wariant_identyczny"] = t["M_n"] == 0 and t["flow_M_n"] == 0
        t["flow_bez_znacznikow"] = t["flow_T_n"] == 0
        print(pn, {k: v for k, v in t.items() if k != "nadir"}, "nadir:",
              [(r["id"], r["bok_px"], r.get("blad_fix_m")) for r in t["nadir"]["wykryte"]], "pominięte", t["nadir"]["pominiete"], flush=True)
    w = {k: all(v[k] for v in tab.values()) for k in ("identyczne_poza_maska", "model_wariant_identyczny", "flow_bez_znacznikow")}
    res = {"werdykty": w, "werdykt_R1": "PASS" if w["identyczne_poza_maska"] else "FAIL", "tabela": tab, "pozy": POSES,
           "maska_dylatacja_px": MASK_DIL, "opencv": cv2.__version__, **meta}
    json.dump(res, open(os.path.join(B1, "r1_identycznosc.json"), "w"), ensure_ascii=False, indent=1)
    print("WERDYKTY", w)
    return w["identyczne_poza_maska"]


def main():
    os.makedirs(OUT, exist_ok=True)
    if "--compare" in sys.argv:
        sys.exit(0 if compare({}) else 1)
    if "--dry" in sys.argv:                                 # na sucho: bez gz — maski i predykcje z geometrii
        for pn, pose in POSES.items():
            print(pn, "maska_px", int(maska(pose).sum()), "nadir_pred", nadir_pred(pose))
        return
    e = env()
    meta = {"instalacja_modelu": instaluj_model(), "przebiegi": {}}
    teardown()
    for tag, world, rig in RUNS:
        with open(os.path.join(B1, f"gz_{tag}.log"), "w") as log:
            meta["przebiegi"][tag] = {"swiat": world, "rig": os.path.relpath(rig, ROOT), "pozy": run_one(tag, world, rig, e, log)}
    sys.exit(0 if compare(meta) else 1)


if __name__ == "__main__":
    main()
