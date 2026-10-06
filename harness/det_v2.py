#!/usr/bin/env python3
"""harness/det_v2.py — detektor-v2 nogi DET (ANEKS_DET-2 §4.3, PRE_DET §4/§6).

Wrapper wag `net/frozen/det_v2.pt` (fine-tune yolov8n nc=1, FREEZE_DET sha 775ead15…)
z kontraktem D4 identycznym jak YoloDetector (feed_vision.py): .top1(frame) → Box
znormalizowany (top-1 po max conf, conf=0.001 telemetrycznie — ZERO progu bramkującego;
θ* z S2 do runtime NIE wchodzi, ANEKS_DET-2 §2). Guard klasy SR-2: sha wag ≠ FREEZE ⇒
RuntimeError ODMOWA. imgsz 640 (tryb runtime, PRE §4).

Dodatkowo `feed_sha_v2()` — JEDEN punkt prawdy kontraktowego feed_sha FEED=V2:
sha256(params rdzenia FeedVision ∪ {detector: det_v2, weights_sha: DET_V2_SHA});
używany i przez proces percepcji, i przez klienta (identyczność z konstrukcji).
"""
from __future__ import annotations

import hashlib
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEIGHTS_DET_V2 = os.path.join(ROOT, "net/frozen/det_v2.pt")
DET_V2_SHA = "775ead150b9937453168538cb97c55f69166e27ddc2d93f71b3710e0e49832ce"  # FREEZE_DET


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for ch in iter(lambda: f.read(1 << 16), b""):
            h.update(ch)
    return h.hexdigest()


class DetV2:
    """Detektor jednoklasowy („intruder") — kontrakt D4 jak YoloDetector.top1."""

    def __init__(self, weights=None, device=None):
        self.weights = weights or WEIGHTS_DET_V2
        got = _sha256(self.weights)
        if got != DET_V2_SHA:
            raise RuntimeError(f"[det_v2] weights_sha rozjazd z FREEZE_DET "
                               f"({got[:16]}≠{DET_V2_SHA[:16]}) — ODMOWA (klasa SR-2)")
        self.weights_sha = got
        import torch
        from ultralytics import YOLO
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = YOLO(self.weights)

    def top1(self, frame_mono_u8):
        import numpy as np
        from r02.target_channel import Box
        fr = frame_mono_u8
        if fr.ndim == 2:
            fr = np.stack([fr] * 3, axis=-1)
        r = self.model.predict(fr, imgsz=640, conf=0.001, verbose=False, device=self.device)[0]
        if r.boxes is None or len(r.boxes) == 0:
            return None
        i = int(r.boxes.conf.argmax())
        x, y, w, h = [float(t) for t in r.boxes.xywh[i]]
        H, W = fr.shape[:2]
        return Box(cx=x / W, cy=y / H, w=w / W, h=h / H, conf=float(r.boxes.conf[i]))


def feed_sha_v2():
    """Kontraktowy feed_sha FEED=V2 (FREEZE_DET): params rdzenia FeedVision z podmianą
    pól detektora. Rdzeń NIE jest edytowany — hash liczony na kopii słownika."""
    from harness.feed_vision import FeedVision
    core = FeedVision(detector=None)
    params = dict(core.params)
    params["detector"] = "det_v2(yolov8n-ft)"
    params["weights_sha"] = DET_V2_SHA
    return hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()
