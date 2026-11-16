#!/usr/bin/env python3
"""results/TEACH/tools/teach_rejestrator.py — pasywny rejestrator kadrów kamery w dół (PROMPT_TEACH_S2 §3): co 1 s czasu sim zapisuje
jeden kadr (PNG bez strat, nazwa = czas sim) z tematu gz kamery w dół, poza ścieżką lotu i bez zmiany harness/nadir_obs.py. Czeka na
temat do --czekaj s, kończy na SIGTERM. Kadry zostają na stanowisku (katalog poza repo).
Użycie: teach_rejestrator.py --world W --model M --out KATALOG [--okres 1.0]
"""
import argparse
import os
import signal
import time

import numpy as np

os.environ.setdefault("GZ_IP", "127.0.0.1")
ap = argparse.ArgumentParser()
ap.add_argument("--world", required=True)
ap.add_argument("--model", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--okres", type=float, default=1.0)
ap.add_argument("--czekaj", type=float, default=900.0)
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
TOPIC = f"/world/{a.world}/model/{a.model}/link/nadir_link/sensor/nadir/image"
stop = [False]
signal.signal(signal.SIGTERM, lambda *_: stop.__setitem__(0, True))
signal.signal(signal.SIGINT, lambda *_: stop.__setitem__(0, True))


def main():
    import cv2
    from gz.transport13 import Node
    from gz.msgs10.image_pb2 import Image
    st = {"ost": -1e9, "n": 0}

    def cb(m):
        t = m.header.stamp.sec + m.header.stamp.nsec / 1e9
        if t - st["ost"] < a.okres - 1e-6:
            return
        st["ost"] = t
        ch = len(m.data) // (m.width * m.height)
        img = np.frombuffer(m.data, np.uint8).reshape(m.height, m.width, ch)
        cv2.imwrite(os.path.join(a.out, f"{t:09.3f}.png"), cv2.cvtColor(img, cv2.COLOR_RGB2BGR) if ch == 3 else img)
        st["n"] += 1
    n = Node()
    t0 = time.time()
    while not stop[0] and not n.subscribe(Image, TOPIC, cb):
        if time.time() - t0 > a.czekaj:
            return
        time.sleep(2)
    while not stop[0]:
        time.sleep(0.5)
    print(f"[rejestrator] kadrów {st['n']}", flush=True)


if __name__ == "__main__":
    main()
