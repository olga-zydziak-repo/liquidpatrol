#!/usr/bin/env python3
"""results/2A/tools/smoke_detect.py — smoke S1 (b): YoloDetector (harness/feed_vision, guard
SR-2) na ISTNIEJĄCYCH klatkach repo (te same 4 co det_bench RECON R2). Boxy + czasy per
klatka → smoke_detect.json. Oczekiwanie: czasy zgodne z det_bench.json (p50 6.5/p95 13 ms),
boxy sensowne (na klatkach z intruzem box w rejonie celu).
Uruchom: PYTHONPATH=. .b0deps/bin/python3 results/2A/tools/smoke_detect.py
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from harness.feed_vision import YoloDetector

ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..")
FRAMES = ["results/R02/r1_frames/base.png", "results/R02/r1_frames/intruder.png",
          "results/R02/gate_live/flight.png", "results/R02/gate_live/static.png"]


def main():
    import numpy as np
    from PIL import Image
    det = YoloDetector()
    out = {"weights_sha": det.weights_sha, "device": det.device, "frames": {}}
    for rel in FRAMES:
        img = np.array(Image.open(os.path.join(ROOT, rel)).convert("RGB"))
        det.top1(img)                                   # warmup per rozmiar
        t0 = time.perf_counter()
        box = det.top1(img)
        ms = (time.perf_counter() - t0) * 1000.0
        out["frames"][rel] = {
            "ms": round(ms, 2),
            "box": ([round(box.cx, 4), round(box.cy, 4), round(box.w, 4), round(box.h, 4)]
                    if box else None),
            "conf": (round(box.conf, 4) if box else None)}
    p = os.path.join(os.path.dirname(__file__), "..", "smoke_detect.json")
    with open(p, "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
