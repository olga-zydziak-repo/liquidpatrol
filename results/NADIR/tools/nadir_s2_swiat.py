#!/usr/bin/env python3
"""results/NADIR/tools/nadir_s2_swiat.py — PROMPT_NADIR_S2 §0.2: identyczność świata v2 (0 bootów, gz bez PX4, metoda b1).

Metoda = results/NADIR/tools/nadir_frames.py (import READ-ONLY: env, svc, teardown, Grab, quat, rotm, diff, POSES, F, CAM,
N_SKIP/N_KEEP/POSE_TMO) — ten sam serwer gz per przebieg, statyczny rig na stałej pozie, te same 10 póz. Zmiany wobec b1:
rig = model lotny x500_nadir2_flow (results/NADIR/s2/zrodla/rig_nadir2.sdf), świat testowy world_nadir2_A3, maska z manifestu
v2 (pozycje rzeczywiste po przesunięciu 7 węzłów), wyjście results/NADIR/s2/swiat/.
Przebiegi: K1, K2 = world_kont_A3 (kanoniczny; K1 vs K2 = szum renderu), T = world_nadir2_A3.
Werdykt ⇔ dla każdej pozy liczba pikseli imagera (kamera misji) z |T − K1| > K_max poza maską rzutów płyt = 0.
Dodatkowo flow_camera (maska widoczności ~bit2 — znaczników nie widzi): |T − K1| > szum = 0 w całym kadrze.
"""
import json
import os
import subprocess
import sys
import time

import cv2
import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, os.path.join(ROOT, "results/NADIR/tools"))
import nadir_frames as NF                                    # READ-ONLY

OUT = os.path.join(ROOT, "results/NADIR/s2/swiat")
FR = os.path.join(OUT, "frames")
RIG = os.path.join(ROOT, "results/NADIR/s2/zrodla/rig_nadir2.sdf")
MAN = json.load(open(os.path.join(ROOT, "results/NADIR/s1/n1/manifest_znaczniki_v2.json")))
KW, NW = "world_kont_A3", "world_nadir2_A3"
RUNS = [("K1", KW), ("T", NW), ("K2", KW)]


def run_one(tag, world, e, log):
    from gz.transport13 import Node
    rc = subprocess.run(["bash", "harness/world_hash.sh", world, OUT], cwd=ROOT, capture_output=True, text=True)
    assert rc.returncode == 0, rc.stdout
    srv = subprocess.Popen(["gz", "sim", "--verbose=1", "-r", "-s", f"{e['PX4_GZ_WORLDS']}/{world}.sdf"], env=e, stdout=log, stderr=log)
    t0 = time.monotonic()
    while "Service providers" not in NF.svc(e, "-i", "--service", f"/world/{world}/scene/info").stdout:
        if time.monotonic() - t0 > 90:
            raise RuntimeError(f"{tag}: świat nie wstał")
        time.sleep(1)
    res = {}
    for i, (pn, (x, y, z, ro, pi, ya)) in enumerate(NF.POSES.items()):
        name = f"probe_{i}"
        node = Node()
        base = f"/world/{world}/model/{name}/link"
        g = NF.Grab(node, f"{base}/camera_link/sensor/imager/image")
        gf = NF.Grab(node, f"{base}/flow_link/sensor/flow_camera/image")
        q = NF.quat(ro, pi, ya)
        req = (f'sdf_filename: "{RIG}", name: "{name}", allow_renaming: false, pose: {{position: {{x: {x}, y: {y}, z: {z}}}, '
               f'orientation: {{w: {q[0]}, x: {q[1]}, y: {q[2]}, z: {q[3]}}}}}')
        r = NF.svc(e, "-s", f"/world/{world}/create", "--reqtype", "gz.msgs.EntityFactory", "--reptype", "gz.msgs.Boolean",
                   "--timeout", "10000", "--req", req)
        assert "true" in r.stdout, (tag, pn, r.stdout, r.stderr)
        t1 = time.monotonic()
        while not (g.done() and gf.done()):
            if time.monotonic() - t1 > NF.POSE_TMO:
                raise RuntimeError(f"{tag} {pn}: brak klatek n={g.n} flow={gf.n}")
            time.sleep(0.2)
        res[pn] = {"n_kl": g.n, "wewn_max": int(max(np.abs(a.astype(int) - g.frames[0].astype(int)).max() for a in g.frames))}
        cv2.imwrite(os.path.join(FR, f"{tag}_{pn}.png"), g.frames[-1][:, :, ::-1] if g.frames[-1].shape[2] == 3 else g.frames[-1])
        cv2.imwrite(os.path.join(FR, f"flow{tag}_{pn}.png"), gf.frames[-1])
        NF.svc(e, "-s", f"/world/{world}/remove", "--reqtype", "gz.msgs.Entity", "--reptype", "gz.msgs.Boolean",
               "--timeout", "5000", "--req", f'name: "{name}" type: MODEL')
        del node
        time.sleep(1)
        print(tag, pn, res[pn], flush=True)
    srv.kill()
    NF.teardown()
    return res


def maska(pose):
    """Rzut płyt manifestu v2 do imagera (pinhole, montaż mono_cam), dylatacja NF.MASK_DIL px (jak b1)."""
    x, y, z, ro, pi, ya = pose
    R = NF.rotm(NF.quat(ro, pi, ya))
    cam = np.array([x, y, z]) + R @ NF.CAM
    m = np.zeros((NF.IH, NF.IW), np.uint8)
    h = MAN["plyta_m"] / 2
    for zn in MAN["znaczniki"]:
        pts = []
        for dx, dy in ((-h, -h), (h, -h), (h, h), (-h, h)):
            b = R.T @ (np.array([zn["E"] + dx, zn["N"] + dy, zn["z"]]) - cam)
            if b[0] <= 0.1:
                pts = None
                break
            pts.append((NF.IW / 2 - NF.F * b[1] / b[0], NF.IH / 2 - NF.F * b[2] / b[0]))
        if pts:
            cv2.fillConvexPoly(m, np.round(np.array(pts)).astype(np.int32), 255)
    return cv2.dilate(m, np.ones((2 * NF.MASK_DIL + 1, 2 * NF.MASK_DIL + 1), np.uint8)) > 0


def compare(meta):
    tab = {}
    for pn, pose in NF.POSES.items():
        f = lambda t: os.path.join(FR, f"{t}_{pn}.png")
        K, T = NF.diff(f("K1"), f("K2")), NF.diff(f("K1"), f("T"))
        FK, FT = NF.diff(f("flowK1"), f("flowK2")), NF.diff(f("flowK1"), f("flowT"))
        mk = maska(pose)
        kmax = int(K.max())
        tab[pn] = {"K_max": kmax, "K_n": int((K > 0).sum()), "T_n": int((T > 0).sum()), "T_max": int(T.max()),
                   "maska_px": int(mk.sum()), "T_poza_maska_n": int(((T > kmax) & ~mk).sum()),
                   "T_poza_maska_max": int(np.where(mk, 0, T).max()),
                   "flow_K_max": int(FK.max()), "flow_T_max": int(FT.max()), "flow_T_n": int((FT > FK.max()).sum())}
        t = tab[pn]
        t["identyczne_poza_maska"] = t["T_poza_maska_n"] == 0
        t["flow_bez_znacznikow"] = t["flow_T_n"] == 0
        print(pn, t, flush=True)
    w = {k: all(v[k] for v in tab.values()) for k in ("identyczne_poza_maska", "flow_bez_znacznikow")}
    res = {"opis": __doc__.split("\n\n")[0], "werdykty": w, "werdykt": "PASS" if all(w.values()) else "FAIL", "tabela": tab,
           "pozy": NF.POSES, "maska_dylatacja_px": NF.MASK_DIL, "rig": os.path.relpath(RIG, ROOT),
           "manifest": "results/NADIR/s1/n1/manifest_znaczniki_v2.json", **meta}
    json.dump(res, open(os.path.join(OUT, "swiat_v2_identycznosc.json"), "w"), ensure_ascii=False, indent=1)
    print("WERDYKTY", w, flush=True)
    return all(w.values())


def main():
    os.makedirs(FR, exist_ok=True)
    if "--compare" in sys.argv:
        sys.exit(0 if compare({}) else 1)
    e = NF.env()
    meta = {"model_sha256": subprocess.check_output(["sha256sum", os.path.join(NF.MODELS, "x500_nadir2_flow/model.sdf")]).decode().split()[0],
            "przebiegi": {}}
    NF.teardown()
    for tag, world in RUNS:
        with open(os.path.join(OUT, f"gz_{tag}.log"), "w") as log:
            meta["przebiegi"][tag] = {"swiat": world, "pozy": run_one(tag, world, e, log)}
    sys.exit(0 if compare(meta) else 1)


if __name__ == "__main__":
    main()
