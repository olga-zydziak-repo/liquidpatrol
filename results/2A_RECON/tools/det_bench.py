#!/usr/bin/env python3
"""results/2A_RECON/tools/det_bench.py — R2 recon 2A: czas inferencji detektora OFFLINE (zero SITL).

Detektor 1:1 z toru C (RAPORT_B0): YOLO-World yolov8s-worldv2.pt, set_classes(["drone"]),
imgsz=640, conf=0.001. Wejście: ISTNIEJĄCE klatki kamery 640×480 z repo (r1_frames/gate_live).
Pomiar: warmup 10, potem 200 inferencji (rotacja klatek), wall per predict(); p50/p95/mean/max.
Uruchom: .b0deps/bin/python3 results/2A_RECON/tools/det_bench.py
"""
import hashlib
import json
import os
import statistics
import time

ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..")
WEIGHTS = os.path.join(ROOT, ".b0deps", "weights", "yolov8s-worldv2.pt")
FRAMES = [os.path.join(ROOT, p) for p in (
    "results/R02/r1_frames/base.png",
    "results/R02/r1_frames/intruder.png",
    "results/R02/gate_live/flight.png",
    "results/R02/gate_live/static.png",
)]
N_WARM, N_MEAS = 10, 200


def sha8(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()[:8]


def main():
    import torch
    from ultralytics import YOLOWorld
    from PIL import Image
    import numpy as np

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    model = YOLOWorld(WEIGHTS)
    model.set_classes(["drone"])
    imgs = [np.array(Image.open(p).convert("RGB")) for p in FRAMES]

    for i in range(N_WARM):
        model.predict(imgs[i % len(imgs)], imgsz=640, conf=0.001, verbose=False, device=dev)
    if dev == "cuda":
        torch.cuda.synchronize()
    ts = []
    for i in range(N_MEAS):
        t0 = time.perf_counter()
        model.predict(imgs[i % len(imgs)], imgsz=640, conf=0.001, verbose=False, device=dev)
        if dev == "cuda":
            torch.cuda.synchronize()
        ts.append((time.perf_counter() - t0) * 1000.0)
    ts_sorted = sorted(ts)
    out = {
        "weights": os.path.relpath(WEIGHTS, ROOT), "weights_sha8": sha8(WEIGHTS),
        "device": dev, "gpu": torch.cuda.get_device_name(0) if dev == "cuda" else None,
        "torch": torch.__version__, "imgsz": 640, "conf": 0.001, "classes": ["drone"],
        "frames": [os.path.relpath(p, ROOT) for p in FRAMES],
        "n_warmup": N_WARM, "n_meas": N_MEAS,
        "ms": {"mean": round(statistics.mean(ts), 2), "p50": round(ts_sorted[len(ts) // 2], 2),
               "p95": round(ts_sorted[int(len(ts) * 0.95)], 2), "max": round(max(ts), 2),
               "min": round(min(ts), 2)},
    }
    outp = os.path.join(os.path.dirname(__file__), "..", "det_bench.json")
    with open(outp, "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out["ms"]), "->", outp)


if __name__ == "__main__":
    main()
