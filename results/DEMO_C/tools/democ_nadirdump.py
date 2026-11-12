#!/usr/bin/env python3
"""results/DEMO_C/tools/democ_nadirdump.py — pasywny zrzutnik klatek kamery nadir (PROMPT_DEMOC_V7 §1.2).

Subskrypcja gz-transport jak harness/nadir_obs.py (gz.transport13 Node.subscribe(Image, TOPIC), stempel sim z header.stamp,
RGB → szarość jak w nadir_obs; nadir_obs NIETKNIĘTY, ten proces jest osobnym subskrybentem obok niego). Wszystkie klatki
(kamera 5 Hz), zapis JPG q=90 w wątku roboczym (kolejka, callback gz nie czeka na dysk), jak democ_framedump.py.
Wyjście: <out>/frames/n_<sim:012.3f>.jpg + <out>/frames_index.jsonl (sim, mono, shape) + <out>/summary.json.

Użycie: democ_nadirdump.py <world> <model> <outdir> [max_s=1800]. Stop: SIGTERM/SIGINT albo max_s.
"""
import json
import os
import queue
import signal
import sys
import threading
import time

import cv2
import numpy as np


def main():
    world, model, outdir = sys.argv[1:4]
    max_s = float(sys.argv[4]) if len(sys.argv) > 4 else 1800.0
    topic = f"/world/{world}/model/{model}/link/nadir_link/sensor/nadir/image"
    fdir = os.path.join(outdir, "frames")
    os.makedirs(fdir, exist_ok=True)
    idx = open(os.path.join(outdir, "frames_index.jsonl"), "w")
    q = queue.Queue(maxsize=64)
    st = {"n_img": 0, "n_zapis": 0, "n_drop": 0}
    stop = [False]

    def on_img(m):
        st["n_img"] += 1
        sim = m.header.stamp.sec + m.header.stamp.nsec / 1e9
        try:
            q.put_nowait((sim, time.monotonic(), m.width, m.height, bytes(m.data)))
        except queue.Full:
            st["n_drop"] += 1

    def worker():
        while not (stop[0] and q.empty()):
            try:
                sim, mono, w, h, data = q.get(timeout=0.2)
            except queue.Empty:
                continue
            ch = len(data) // (w * h)
            img = np.frombuffer(data, np.uint8).reshape(h, w, ch)
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY) if ch == 3 else img[:, :, 0]
            fn = f"n_{sim:012.3f}.jpg"
            cv2.imwrite(os.path.join(fdir, fn), gray, [cv2.IMWRITE_JPEG_QUALITY, 90])
            idx.write(json.dumps({"f": fn, "sim": round(sim, 4), "mono": round(mono, 3), "shape": [h, w]}) + "\n")
            st["n_zapis"] += 1
            if st["n_zapis"] % 100 == 0:
                idx.flush()

    from gz.transport13 import Node as GzNode
    from gz.msgs10.image_pb2 import Image
    th = threading.Thread(target=worker, daemon=True)
    th.start()
    gn = GzNode()
    gn.subscribe(Image, topic, on_img)
    signal.signal(signal.SIGTERM, lambda *_: stop.__setitem__(0, True))
    signal.signal(signal.SIGINT, lambda *_: stop.__setitem__(0, True))
    t0 = time.monotonic()
    while not stop[0] and time.monotonic() - t0 < max_s:
        time.sleep(0.2)
    stop[0] = True
    th.join(timeout=10)
    idx.flush()
    idx.close()
    json.dump({"topic": topic, **st}, open(os.path.join(outdir, "summary.json"), "w"))
    print(f"[nadirdump] {json.dumps(st)} → {fdir}", flush=True)
    os._exit(0)                                     # wątki gz-transport nie trzymają procesu


if __name__ == "__main__":
    main()
