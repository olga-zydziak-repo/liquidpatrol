#!/usr/bin/env python3
"""results/DET/tools/det_replay.py — T3 PROMPT_DET_S1: replay admisyjny (przyrząd bramki T,
PRE_DET §5; FROZEN po commicie S1).

Sekwencja klatek bootu → DETEKTOR → MTI → admisja D2 → pinhole → TargetChannel:
rdzeń = harness.feed_vision.FeedVision (sha acc81df7, TE SAME BAJTY co lot: brama REFRESH
N2, θ_age, kontrakt) z wstrzykniętym detektorem; poza/quat POKŁADOWE per klatka
z shadow_feed.jsonl bootu (own_pos_ned/own_q przy t_frame — to, co widział lot).
Zero GT w torze; GT wyłącznie w sędziowaniu po fakcie.

Miary (semantyka bramki B PRE_2A / percep_judge):
  err świeżych vs GT: e=|trk_pos_ned − GT(t)| na próbkach fresh (p50/p95/max/n),
  top-1-na-celu [%] klatek z celem w FOV (etykieta geometryczna: BootGeo z det_labels
  8f7430cd, import READ-ONLY),
  rozkład admisji: ENTRY/FEED_EXPIRE, gates {mti,window}, n_fresh/n_boxes/n_frames.

Detektor: --detector world  → YoloDetector (frozen 9b2c17ab, guard SR-2)  [walidacja T4]
          --detector <ścieżka .pt> → SingleClassDetector (fine-tune nc=1; top-1 max conf,
          ten sam kształt Box co YoloDetector.top1 — kontrakt detektora D4)   [S2]

Użycie: det_replay.py <bootdir> --detector world --out <json> [--labels-root <dir_z_meta>]
"""
from __future__ import annotations

import argparse
import bisect
import glob
import hashlib
import json
import os
import sys
import time

ROOT = "/home/olga/projects/liquidpatrol"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "results/DET_RECON/tools"))

from harness.feed_vision import FeedVision, YoloDetector   # frozen acc81df7
from det_labels import BootGeo                              # frozen 8f7430cd (READ-ONLY import)


class SingleClassDetector:
    """Detektor fine-tune nc=1 — kontrakt D4 jak YoloDetector.top1 (box znorm. + conf)."""

    def __init__(self, weights):
        import torch
        from ultralytics import YOLO
        h = hashlib.sha256()
        with open(weights, "rb") as f:
            for ch in iter(lambda: f.read(1 << 16), b""):
                h.update(ch)
        self.weights_sha = h.hexdigest()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = YOLO(weights)

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


def load_jsonl(path):
    out = []
    with open(path) as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                try:
                    out.append(json.loads(ln))
                except json.JSONDecodeError:
                    pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bootdir")
    ap.add_argument("--detector", required=True, help="'world' albo ścieżka .pt (nc=1)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    import cv2
    det = YoloDetector() if a.detector == "world" else SingleClassDetector(a.detector)

    # poza pokładowa per t_frame z shadow_feed (to co widział lot — zero GT w torze)
    own = {}
    for r in load_jsonl(os.path.join(a.bootdir, "shadow_feed.jsonl")):
        if r.get("t_frame") is not None and r.get("own_pos_ned") and r.get("own_q"):
            own[round(r["t_frame"], 3)] = (r["own_pos_ned"], r["own_q"])
    own_ts = sorted(own)

    def own_at(t):
        i = bisect.bisect_left(own_ts, round(t, 3))
        cand = [j for j in (i - 1, i) if 0 <= j < len(own_ts)]
        if not cand:
            return None
        k = min(cand, key=lambda j: abs(own_ts[j] - t))
        return own[own_ts[k]] if abs(own_ts[k] - t) <= 0.1 else None

    log_path = a.out + ".replay.jsonl"
    feed = FeedVision(detector=det, log_path=log_path)
    frames = sorted(glob.glob(os.path.join(a.bootdir, "frames", "*.jpg")))
    n_noown = 0
    t0w = time.monotonic()
    for fp in frames:
        t = float(os.path.basename(fp)[2:-4])
        st = own_at(t)
        if st is None:
            n_noown += 1
            continue
        feed.push_own(t, st[0], st[1])
        feed.push_frame(t, cv2.imread(fp, cv2.IMREAD_GRAYSCALE))
    feed.close()
    wall = time.monotonic() - t0w

    # --- sędziowanie po fakcie (GT dopiero tutaj) ---
    geo = BootGeo(a.bootdir, 1.0, 60.0)
    rows = load_jsonl(log_path)
    errs = []
    for r in rows:
        if not r.get("fresh") or not r.get("trk_pos_ned"):
            continue
        from coverage_real import interp         # ścieżkę 2A/tools dokłada import det_labels
        tgt = interp(geo.its, geo.ips, r["t_frame"])
        if tgt is None:
            continue
        e = sum((r["trk_pos_ned"][k] - tgt[k]) ** 2 for k in range(3)) ** 0.5
        errs.append(e)
    on = n_fov = 0
    for r in rows:
        lab = geo.label(r["t_frame"])
        if lab["flag"] != "OK":
            continue
        n_fov += 1
        b = r.get("box")
        if b:
            from r02.mti import IMG_W, IMG_H
            bx, by = b[0] * IMG_W, b[1] * IMG_H
            lb = lab["box"]
            if abs(bx - lb[0]) <= lb[2] / 2 and abs(by - lb[1]) <= lb[3] / 2:
                on += 1
    evs, gates = {}, {}
    for r in rows:
        if r.get("ev"):
            evs[r["ev"]] = evs.get(r["ev"], 0) + 1
        if r.get("fresh"):
            gates[str(r.get("gate"))] = gates.get(str(r.get("gate")), 0) + 1
    es = sorted(errs)
    out = {"bootdir": a.bootdir, "detector": a.detector,
           "detector_sha": det.weights_sha,
           "n_frames_replayed": len(rows), "n_frames_no_own": n_noown,
           "wall_s": round(wall, 1),
           "err_fresh_vs_gt": {"n": len(es),
                               "p50": round(es[len(es) // 2], 3) if es else None,
                               "p95": round(es[int(len(es) * 0.95)], 3) if es else None,
                               "max": round(es[-1], 3) if es else None},
           "top1_on_target": {"n_fov": n_fov, "n_on": on,
                              "pct": round(100 * on / n_fov, 1) if n_fov else None},
           "admisja": {"events": evs, "fresh_gates": gates,
                       "n_boxes": sum(1 for r in rows if r.get("box")),
                       "n_fresh": sum(1 for r in rows if r.get("fresh"))}}
    with open(a.out, "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
