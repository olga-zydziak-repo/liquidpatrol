#!/usr/bin/env python3
"""results/DET3_RECON/tools/det3_r2_imgsz.py — R2: koszt inferencji det_v2 775ead15 vs imgsz.

200 klatek z D10_c09_s08 (TEST), mono→3 kanały jak SingleClassDetector.top1 (det_replay.py:55-67),
predict(conf=0.001) na GPU; rozgrzewka 20 klatek; per imgsz: ms/klatkę p50/p95 (perf_counter wokół
predict+argmax, synchronizacja CUDA) + top-1 na celu wg etykiety (ten sam boot, meta.jsonl).
Wagi trenowane przy 640 — inferencja 960/1280 to ZERO-SHOT skali (koszt czasu jest miarą główną).
Pomiar offline na pustym GPU = DOLNA granica czasu w locie (gz renderuje na tym samym GPU).
"""
import glob
import json
import os
import sys
import time

import cv2
import numpy as np
import torch
from ultralytics import YOLO

ROOT = "/home/olga/projects/liquidpatrol"
BOOT = os.path.join(ROOT, "results/DET/collect/D10_c09_s08")
META = os.path.join(ROOT, "results/DET/labels/D10_c09_s08/meta.jsonl")


def main():
    out = sys.argv[1]
    meta = {}
    for ln in open(META):
        r = json.loads(ln)
        meta[r["frame"]] = r
    frames = sorted(glob.glob(os.path.join(BOOT, "frames", "*.jpg")))
    frames = [f for f in frames if meta.get(os.path.basename(f), {}).get("flag") == "OK"][:220]
    imgs = [np.stack([cv2.imread(f, cv2.IMREAD_GRAYSCALE)] * 3, axis=-1) for f in frames]
    model = YOLO(os.path.join(ROOT, "net/frozen/det_v2.pt"))
    res = {"gpu": torch.cuda.get_device_name(0), "n_frames": len(imgs) - 20, "torch": torch.__version__}
    for sz in (640, 960, 1280):
        ts, on = [], 0
        for i, (f, im) in enumerate(zip(frames, imgs)):
            torch.cuda.synchronize()
            t0 = time.perf_counter()
            r = model.predict(im, imgsz=sz, conf=0.001, verbose=False, device="cuda")[0]
            box = None
            if r.boxes is not None and len(r.boxes):
                j = int(r.boxes.conf.argmax())
                box = [float(t) for t in r.boxes.xywh[j]]
            torch.cuda.synchronize()
            dt = (time.perf_counter() - t0) * 1000
            if i < 20:
                continue
            ts.append(dt)
            lb = meta[os.path.basename(f)]["box"]
            if box and abs(box[0] - lb[0]) <= lb[2] / 2 and abs(box[1] - lb[1]) <= lb[3] / 2:
                on += 1
        ts.sort()
        res[str(sz)] = {"ms_p50": round(ts[len(ts) // 2], 2), "ms_p95": round(ts[int(len(ts) * 0.95)], 2),
                        "ms_max": round(ts[-1], 2), "top1_on": f"{on}/{len(ts)}"}
        print(sz, res[str(sz)])
    json.dump(res, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
