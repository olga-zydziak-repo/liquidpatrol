#!/usr/bin/env python3
"""results/TEACH/tools/teach_st.py — booty statyczne ST1 / ST2 / ST3 nogi TEACH (PROMPT_TEACH_S2 §3–§4, ANEKS_TEACH-2 §3.4).

Boot statyczny = serwer gz bez PX4 (ten sam serwer, świat i konfiguracja co stos: env_gpu.sh, gz_env.sh rootfs PX4, `gz sim -r -s`),
jeden dron wstawiony usługą /world/<W>/create jako model STATYCZNY (kopia model.sdf z <static>true</static>; include’y merge='true',
więc całe ciało statyczne) w pozie POZA — ta sama poza w każdym boocie; nad znacznikami 31 i 35 (kamera w dół widzi w starym świecie
co najmniej jeden znacznik — ANEKS_TEACH-2 §3.4). Po POCZEKAJ_S s sim zapis po N_KLATEK kolejnych klatek: kamera misji (imager), kamera
przepływu (flow_camera), kamera w dół (nadir) — PNG bez strat — i lidar (zakresy). Kamera w dół: detektor znaczników jak w boocie
(DICT_4X4_50, parametry domyślne, bez lustra) i zgodność z manifestem (teach_analyze.zgodnosc_detekcji, poza GT = POZA).
Warianty: ST1 = x500_nadir2_flow (przypięty) + world_nadir2_A3; ST2 = x500_teach_flow + world_teach_S; ST3 = x500_teach_flow +
world_nadir2_A3. Modele i światy instalowane do PX4 jak w launcherach (istniejący katalog musi być identyczny; świat przez
harness/world_hash.sh). Strażnik: żadnego gz / px4 przed startem; po boocie zabicie gz (kont_inw).
Użycie: teach_st.py ST1|ST2|ST3. Wyjście: results/TEACH/s2/<st>/ (klatki, st.json) ; porównanie: teach_st.py --porownaj.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

import numpy as np

os.environ["GZ_IP"] = "127.0.0.1"             # jak teach_boot.sh (serwer, usługi i klient gz-transport na jednym interfejsie)
ROOT = "/home/olga/projects/liquidpatrol"
S2 = os.path.join(ROOT, "results/TEACH/s2")
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/TEACH/tools")]
POZA = (25.0, 0.0, 11.0)                      # E, N, wysokość ramy modelu [m], kurs 0
POCZEKAJ_S, N_KLATEK = 4.0, 3
WARIANTY = {"ST1": ("x500_nadir2_flow", "results/NADIR/s1/zrodla/x500_nadir2_flow", "world_nadir2_A3"),
            "ST2": ("x500_teach_flow", "results/TEACH/s1/zrodla/x500_teach_flow", "world_teach_S"),
            "ST3": ("x500_teach_flow", "results/TEACH/s1/zrodla/x500_teach_flow", "world_nadir2_A3")}
PX4M = os.path.join(ROOT, "PX4-Autopilot/Tools/simulation/gz/models")
ROOTFS = os.path.join(ROOT, "PX4-Autopilot/build/px4_sitl_default/rootfs")


def sh(cmd, **kw):
    return subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, cwd=ROOT, **kw)


def zyje():
    r = sh(f"python3 {ROOT}/results/KONT/tools/kont_inw.py LIST gz px4 MicroXRCEAgent")
    return r.stdout.strip()


def boot(tag):
    model, src, world = WARIANTY[tag]
    out = os.path.join(S2, tag.lower())
    if os.path.exists(os.path.join(out, "st.json")):
        sys.exit(f"{tag}: {out}/st.json istnieje — REPO-2, ODMOWA")
    os.makedirs(out, exist_ok=True)
    z = zyje()
    if z:
        sys.exit(f"{tag}: żyją procesy {z} — ODMOWA")
    dst = os.path.join(PX4M, model)
    if os.path.isdir(dst):
        for f in ("model.sdf", "model.config"):
            if open(os.path.join(ROOT, src, f), "rb").read() != open(os.path.join(dst, f), "rb").read():
                sys.exit(f"{tag}: {model}/{f} różny w PX4 — ODMOWA")
    else:
        shutil.copytree(os.path.join(ROOT, src), dst)
    wh = sh(f"bash harness/world_hash.sh {world} {out}")
    sdf = open(os.path.join(ROOT, src, "model.sdf")).read()
    a = f"<model name='{model}'>"
    assert sdf.count(a) == 1
    sdf = sdf.replace(a, a + "\n    <static>true</static>")
    spawn = os.path.join(out, "spawn_static.sdf")
    open(spawn, "w").write(sdf)
    log = open(os.path.join(out, "gz_server.log"), "w")
    gz = subprocess.Popen(["bash", "-c", f"source {ROOT}/env_gpu.sh >/dev/null; export HEADLESS=1 RENDER_BACKEND=mesa-d3d12 GZ_IP=127.0.0.1; "
                                         f"cd {ROOTFS}; set +u; . ./gz_env.sh; exec gz sim --verbose=1 -r -s $PX4_GZ_WORLDS/{world}.sdf"],
                          stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    wyn = {"tag": tag, "model": model, "zrodlo_modelu": src, "swiat": world, "poza": POZA, "world_hash": wh.stdout.strip(),
           "sha_model_sdf": __import__("hashlib").sha256(open(os.path.join(ROOT, src, "model.sdf"), "rb").read()).hexdigest()}
    try:
        for _ in range(60):
            if f"/world/{world}/clock" in sh("gz topic -l").stdout:
                break
            time.sleep(1)
        else:
            raise RuntimeError("zegar świata nie wstał")
        name = f"{model}_0"
        req = (f'sdf_filename: "{spawn}", name: "{name}", allow_renaming: false, '
               f'pose: {{position: {{x: {POZA[0]}, y: {POZA[1]}, z: {POZA[2]}}}}}')
        r = sh(f"cd {ROOTFS}; set +u; . ./gz_env.sh; gz service -s /world/{world}/create --reqtype gz.msgs.EntityFactory "
               f"--reptype gz.msgs.Boolean --timeout 10000 --req '{req}'")
        wyn["spawn"] = r.stdout.strip() + r.stderr.strip()
        pre = f"/world/{world}/model/{name}/link/"
        tematy = {"imager": pre + "camera_link/sensor/imager/image", "flow": pre + "flow_link/sensor/flow_camera/image",
                  "nadir": pre + "nadir_link/sensor/nadir/image", "lidar": pre + "lidar_sensor_link/sensor/lidar/scan"}
        for _ in range(60):
            tl = sh("gz topic -l").stdout
            if all(t in tl for t in tematy.values()):
                break
            time.sleep(1)
        wyn["tematy"] = {k: (v in tl) for k, v in tematy.items()}
        open(os.path.join(out, "topics.txt"), "w").write(tl)
        wyn["dane"] = zbierz(out, world, tematy)
    finally:
        sh(f"python3 {ROOT}/results/KONT/tools/kont_inw.py KILL gz")
        time.sleep(2)
        gz.wait(timeout=30)
        log.close()
    wyn["swiadek"] = swiadek(out)
    json.dump(wyn, open(os.path.join(out, "st.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in wyn.items() if k != "dane"}, ensure_ascii=False, indent=1))


def zbierz(out, world, tematy):
    import cv2
    from gz.transport13 import Node
    from gz.msgs10.image_pb2 import Image
    from gz.msgs10.laserscan_pb2 import LaserScan
    from gz.msgs10.clock_pb2 import Clock
    st = {"t": None, "t0": None, "img": {k: [] for k in ("imager", "flow", "nadir")}, "lidar": []}
    n = Node()

    def zeg(m):
        st["t"] = m.sim.sec + m.sim.nsec / 1e9
        if st["t0"] is None:
            st["t0"] = st["t"]

    def obraz(k):
        def cb(m):
            if st["t"] is None or st["t"] - st["t0"] < POCZEKAJ_S or len(st["img"][k]) >= N_KLATEK:
                return
            ch = len(m.data) // (m.width * m.height)
            a = np.frombuffer(m.data, np.uint8).reshape(m.height, m.width, ch).copy()
            st["img"][k].append((m.header.stamp.sec + m.header.stamp.nsec / 1e9, a))
        return cb

    def lid(m):
        if st["t"] is None or st["t"] - st["t0"] < POCZEKAJ_S or len(st["lidar"]) >= N_KLATEK:
            return
        st["lidar"].append((m.header.stamp.sec + m.header.stamp.nsec / 1e9, list(m.ranges)))
    n.subscribe(Clock, f"/world/{world}/clock", zeg)
    for k in ("imager", "flow", "nadir"):
        n.subscribe(Image, tematy[k], obraz(k))
    n.subscribe(LaserScan, tematy["lidar"], lid)
    t0 = time.time()
    while time.time() - t0 < 120 and not (all(len(v) >= N_KLATEK for v in st["img"].values()) and len(st["lidar"]) >= N_KLATEK):
        time.sleep(0.2)
    d = {"t0_sim": st["t0"]}
    for k, v in st["img"].items():
        d[k] = []
        for i, (t, a) in enumerate(v):
            p = os.path.join(out, f"{k}_{i}.png")
            cv2.imwrite(p, cv2.cvtColor(a, cv2.COLOR_RGB2BGR) if a.shape[2] == 3 else a)
            d[k].append({"sim": round(t, 4), "plik": os.path.basename(p), "ksztalt": list(a.shape)})
    d["lidar"] = [{"sim": round(t, 4), "zakresy": [round(x, 5) for x in r]} for t, r in st["lidar"]]
    return d


def swiadek(out):
    import cv2
    import teach_analyze as A
    D, P = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50), cv2.aruco.DetectorParameters_create()
    wp = []
    for i in range(N_KLATEK):
        p = os.path.join(out, f"nadir_{i}.png")
        if not os.path.exists(p):
            continue
        g = cv2.cvtColor(cv2.imread(p), cv2.COLOR_BGR2GRAY)
        c, ids, _ = cv2.aruco.detectMarkers(g, D, parameters=P)
        det = []
        if ids is not None:
            for cc, k in zip(c, ids.ravel()):
                cc = cc.reshape(4, 2)
                det.append({"id": int(k), "uv": cc.mean(0).tolist(),
                            "bok": round(min(float(np.linalg.norm(cc[j] - cc[(j + 1) % 4])) for j in range(4)), 2)})
        wp.append((float(i), det))
        wp[-1] = (float(i), det)
    poza = ([POZA[0], POZA[1], POZA[2]], [1.0, 0.0, 0.0, 0.0])
    z = A.zgodnosc_detekcji(wp, lambda t: poza)
    sz = [float(cv2.imread(os.path.join(out, f"nadir_{i}.png"), cv2.IMREAD_GRAYSCALE).std()) for i in range(N_KLATEK)
          if os.path.exists(os.path.join(out, f"nadir_{i}.png"))]
    return {"detekcje": z, "nadir_std_jasnosci": [round(x, 2) for x in sz]}


def porownaj():
    import cv2
    w = {}
    pary = [("ST1", "ST2")] + ([("ST1", "ST3"), ("ST3", "ST2")] if os.path.exists(os.path.join(S2, "st3", "st.json")) else [])
    for a, b in pary:
        A_, B_ = os.path.join(S2, a.lower()), os.path.join(S2, b.lower())
        o = {}
        for k in ("imager", "flow"):
            r = []
            for i in range(N_KLATEK):
                x = cv2.imread(os.path.join(A_, f"{k}_{i}.png"), cv2.IMREAD_UNCHANGED).astype(int)
                y = cv2.imread(os.path.join(B_, f"{k}_{i}.png"), cv2.IMREAD_UNCHANGED).astype(int)
                d = np.abs(x - y)
                r.append({"pikseli_roznych": int((d.max(axis=-1) if d.ndim == 3 else d).astype(bool).sum()), "max_roznica": int(d.max())})
            o[k] = r
        la = json.load(open(os.path.join(A_, "st.json")))["dane"]["lidar"]
        lb = json.load(open(os.path.join(B_, "st.json")))["dane"]["lidar"]
        o["lidar"] = [{"a": x["zakresy"], "b": y["zakresy"], "roznica_m": round(max(abs(p - q) for p, q in zip(x["zakresy"], y["zakresy"])), 5)}
                      for x, y in zip(la, lb)]
        o["zero_obrazow"] = all(x["pikseli_roznych"] == 0 for k in ("imager", "flow") for x in o[k])
        o["lidar_ok"] = all(x["roznica_m"] <= 0.002 for x in o["lidar"])
        w[f"{a}-{b}"] = o
    s1 = json.load(open(os.path.join(S2, "st1", "st.json")))["swiadek"]
    s2 = json.load(open(os.path.join(S2, "st2", "st.json")))["swiadek"]
    w["swiadek"] = {"ST1_zgodne": s1["detekcje"]["zgodne"]["n"], "ST2_zgodne": s2["detekcje"]["zgodne"]["n"],
                    "ST2_surowe": s2["detekcje"]["surowe"]["n"], "ST2_nadir_std": s2["nadir_std_jasnosci"],
                    "ok": s1["detekcje"]["zgodne"]["n"] >= 1 and s2["detekcje"]["zgodne"]["n"] == 0}
    json.dump(w, open(os.path.join(S2, "st_porownanie.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: ({kk: vv for kk, vv in v.items() if kk != "lidar"} if isinstance(v, dict) else v) for k, v in w.items()},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    porownaj() if sys.argv[1] == "--porownaj" else boot(sys.argv[1])
