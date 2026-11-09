#!/usr/bin/env python3
"""harness/nadir_obs.py — PASYWNY rejestrator kamery nadir (PROMPT_NADIR_S1 §1.4, PRE_NADIR §2.2). Nowy plik.

TYLKO LOGUJE: niczego nie publikuje (ani do sterowania, ani do osłony, ani do percepcji misji).
Wejścia: obraz nadir przez gz-transport (bez mostu ROS — topic gz /world/<W>/model/<M>/link/nadir_link/sensor/nadir/image;
stempel header = czas symulacji), EKF pokładowy przez ROS2: /fmu/out/vehicle_attitude (q FRD→NED) i
/fmu/out/vehicle_local_position (x, y, z NED, heading) — QoS BEST_EFFORT jak harness/feed_vision.py.
Detekcja cv2.aruco (OpenCV 4.6.0 systemowe, DICT_4X4_50, parametry domyślne DetectorParameters_create()). Gdy obraz nie
daje żadnego ID, a env NADIR_FLIP=auto (dom.), próba na obrazie odbitym poziomo (tekstura płaszczyzny gz może być lustrzana;
wynik i tryb w logu, narożniki przeliczone do obrazu oryginalnego). NADIR_FLIP=0/1 wymusza tryb.
Wiersz per klatka (JSONL): mono, sim, n_det, tryb lustra, per znacznik id/narożniki/środek (przecięcie przekątnych)/bok px
(najkrótsza krawędź), EKF q/pos/heading z wiekiem; czas detekcji. Pozycje (tryb 1 / para) liczy analiza offline
(results/NADIR/tools/nadir_s1_analyze.py) — z EKF i z GT, żeby rozdzielić wkład postawy.
Detekcja w wątku roboczym z kolejką 1 (zawsze najnowsza klatka); klatki pominięte liczone (n_drop) i raportowane.
PROMPT_NADIR_S2 §1.1 — gałąź NADIR_MODE=1 (przy 0 zachowanie pasywne jak wyżej, wiersze bez zmian): producent ramy B+ —
po detekcji harness/nadir_fix.Rama.obserwacja(sim, det, migawka EKF) i datagram stanu ramy do gniazd z env NADIR_FIX_SOCKS
(lista ścieżek UDS rozdzielona „:”); rekord w wierszu klatki pod kluczem "fx" (przyjęte/odrzucone obserwacje z powodem).
PROMPT_NADIR_S2 §1.6 (wada S1: brak summary — proces nie doszedł do ścieżki zamknięcia w 4 s przed SIGKILL): summary
zapisywany atomowo co 15 s z wątku roboczego (przeżywa SIGKILL), końcowy w handlerze SIGTERM; faulthandler zrzuca stosy
wątków na stderr przy SIGTERM (diagnoza zawieszenia).
Użycie: nadir_obs.py --world W --model M --out plik.jsonl
"""
import argparse
import faulthandler
import json
import os
import queue
import signal
import sys
import threading
import time

import cv2
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--world", required=True)
ap.add_argument("--model", required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()
TOPIC = f"/world/{a.world}/model/{a.model}/link/nadir_link/sensor/nadir/image"
FLIP = os.environ.get("NADIR_FLIP", "auto")
if hasattr(cv2.aruco, "ArucoDetector"):                    # OpenCV ≥ 4.7 (nowe API)
    _DET = cv2.aruco.ArucoDetector(cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50), cv2.aruco.DetectorParameters())
    _detm = lambda g: _DET.detectMarkers(g)
else:                                                         # OpenCV 4.6 (systemowe; boot uruchamia bez .b0deps)
    _D, _P = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50), cv2.aruco.DetectorParameters_create()
    _detm = lambda g: cv2.aruco.detectMarkers(g, _D, parameters=_P)

NADIR_MODE = os.environ.get("NADIR_MODE") == "1"
if NADIR_MODE:                                                # PROMPT_NADIR_S2 §1.1: producent ramy B+
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from harness.nadir_fix import Rama, nadawca
    _rama = Rama()
    _send = nadawca([x for x in os.environ.get("NADIR_FIX_SOCKS", "").split(":") if x])
_stop = [False]
_ekf = {"q": None, "q_mono": None, "pos": None, "hdg": None, "pos_mono": None}
_q = queue.Queue(maxsize=1)
st = {"n_img": 0, "n_drop": 0, "n_proc": 0, "n_det_klatki": 0, "flip_hits": 0, "det_ms": []}
if NADIR_MODE:
    st["n_fix"] = 0
fout = open(a.out, "w", buffering=1)
_hb = [time.monotonic()]


def zapisz_summary(zamkniecie):
    """PROMPT_NADIR_S2 §1.6: summary atomowo (tmp + rename) — z wątku roboczego co 15 s i z handlera SIGTERM."""
    ms = sorted(st["det_ms"])
    summ = {k: v for k, v in st.items() if k != "det_ms"}
    summ["det_ms"] = {"p50": ms[len(ms) // 2], "p95": ms[int(len(ms) * 0.95)], "max": ms[-1]} if ms else None
    summ["zamkniecie"] = zamkniecie
    summ["mono"] = round(time.monotonic(), 3)
    tmp = a.out + ".summary.json.tmp"
    with open(tmp, "w") as f:
        json.dump(summ, f, indent=1)
    os.replace(tmp, a.out + ".summary.json")
    return summ


def on_term(*_):
    _stop[0] = True
    try:
        zapisz_summary("SIGTERM")
    except Exception:                                         # noqa: BLE001 — zamknięcie nie może rzucić
        pass


def srodek(c):
    p1, p2, p3, p4 = c
    d1, d2 = p3 - p1, p4 - p2
    try:
        t = np.linalg.solve(np.array([d1, -d2]).T, p2 - p1)
        return p1 + t[0] * d1
    except np.linalg.LinAlgError:
        return c.mean(axis=0)


def detect(gray):
    tryb = 0
    if FLIP == "1":
        corners, ids, _ = _detm(cv2.flip(gray, 1))
        tryb = 1
    else:
        corners, ids, _ = _detm(gray)
        if ids is None and FLIP == "auto":
            cf, idf, _ = _detm(cv2.flip(gray, 1))
            if idf is not None:
                corners, ids, tryb = cf, idf, 1
    out = []
    if ids is not None:
        w = gray.shape[1]
        for c, i in zip(corners, ids.ravel()):
            c = c.reshape(4, 2).astype(float)
            if tryb:
                c[:, 0] = w - 1 - c[:, 0]
            s = srodek(c)
            bok = min(float(np.linalg.norm(c[k] - c[(k + 1) % 4])) for k in range(4))
            out.append({"id": int(i), "c": np.round(c, 2).tolist(), "uv": [round(float(s[0]), 2), round(float(s[1]), 2)],
                        "bok": round(bok, 2)})
    return out, tryb


def worker():
    while not _stop[0]:
        try:
            mono, sim, gray, ekf = _q.get(timeout=0.2)
        except queue.Empty:
            continue
        t0 = time.monotonic()
        det, tryb = detect(gray)
        ms = (time.monotonic() - t0) * 1000
        st["n_proc"] += 1
        st["det_ms"].append(ms)
        if det:
            st["n_det_klatki"] += 1
        if tryb:
            st["flip_hits"] += 1
        row = {"t": "nf", "mono": round(mono, 4), "sim": round(sim, 4), "n": len(det), "lustro": tryb,
               "det": det, "ms": round(ms, 2), **ekf}
        if NADIR_MODE:                                         # PROMPT_NADIR_S2 §1.1
            fx = _rama.obserwacja(sim, det, ekf["ekf_q"], ekf["ekf_pos"])
            _send(fx)
            st["n_fix"] += int(fx["ok"])
            row["fx"] = fx
        fout.write(json.dumps(row) + "\n")
        if time.monotonic() - _hb[0] >= 15.0:                  # PROMPT_NADIR_S2 §1.6: summary okresowo (przeżywa SIGKILL)
            _hb[0] = time.monotonic()
            zapisz_summary("heartbeat")


def on_img(m):
    mono = time.monotonic()
    st["n_img"] += 1
    sim = m.header.stamp.sec + m.header.stamp.nsec / 1e9
    ch = len(m.data) // (m.width * m.height)
    img = np.frombuffer(m.data, np.uint8).reshape(m.height, m.width, ch)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY) if ch == 3 else img[:, :, 0].copy()
    ekf = {"ekf_q": _ekf["q"], "ekf_q_age": None if _ekf["q_mono"] is None else round(mono - _ekf["q_mono"], 4),
           "ekf_pos": _ekf["pos"], "ekf_hdg": _ekf["hdg"], "ekf_pos_age": None if _ekf["pos_mono"] is None else round(mono - _ekf["pos_mono"], 4)}
    try:
        _q.put_nowait((mono, sim, gray, ekf))
    except queue.Full:
        st["n_drop"] += 1
        try:
            _q.get_nowait()
        except queue.Empty:
            pass
        _q.put_nowait((mono, sim, gray, ekf))


def main():
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
    from rclpy.executors import SingleThreadedExecutor
    from px4_msgs.msg import VehicleLocalPosition, VehicleAttitude
    from gz.transport13 import Node as GzNode
    from gz.msgs10.image_pb2 import Image

    def on_att(m):
        _ekf["q"] = [round(float(x), 6) for x in m.q]
        _ekf["q_mono"] = time.monotonic()

    def on_pos(m):
        _ekf["pos"] = [round(float(m.x), 4), round(float(m.y), 4), round(float(m.z), 4)]
        _ekf["hdg"] = round(float(m.heading), 5)
        _ekf["pos_mono"] = time.monotonic()

    fout.write(json.dumps({"t": "meta", "topic": TOPIC, "opencv": cv2.__version__, "slownik": "DICT_4X4_50", "flip": FLIP,
                           "mono": round(time.monotonic(), 4)}) + "\n")
    th = threading.Thread(target=worker, daemon=True)
    th.start()
    gn = GzNode()
    gn.subscribe(Image, TOPIC, on_img)
    rclpy.init()
    node = Node("nadir_obs")
    qos = QoSProfile(depth=1, history=HistoryPolicy.KEEP_LAST, reliability=ReliabilityPolicy.BEST_EFFORT)
    node.create_subscription(VehicleLocalPosition, "/fmu/out/vehicle_local_position", on_pos, qos)
    node.create_subscription(VehicleAttitude, "/fmu/out/vehicle_attitude", on_att, qos)
    ex = SingleThreadedExecutor()
    ex.add_node(node)
    signal.signal(signal.SIGTERM, on_term)
    faulthandler.register(signal.SIGTERM, file=sys.stderr, all_threads=True, chain=True)   # §1.6: diagnoza, potem on_term
    signal.signal(signal.SIGINT, lambda *_: _stop.__setitem__(0, True))
    t_hb = time.monotonic()
    while not _stop[0] and rclpy.ok():
        ex.spin_once(timeout_sec=0.05)
        if time.monotonic() - t_hb >= 15.0:
            t_hb = time.monotonic()
            print(f"[nadir_obs] img={st['n_img']} proc={st['n_proc']} det={st['n_det_klatki']} drop={st['n_drop']} "
                  f"flip={st['flip_hits']}", flush=True)
    _stop[0] = True
    th.join(timeout=2)
    summ = zapisz_summary("koniec_petli")
    fout.write(json.dumps({"t": "summary", **summ}) + "\n")
    fout.close()
    print(f"[nadir_obs] DONE {json.dumps(summ)}", flush=True)


if __name__ == "__main__":
    main()
