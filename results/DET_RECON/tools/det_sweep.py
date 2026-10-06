#!/usr/bin/env python3
"""results/DET_RECON/tools/det_sweep.py — R3 PROMPT_DET_S0: baseline-C, ratunek YOLO tanio.

Na klatkach z etykietą OK (det_labels.py, 4 booty 2A): sweep YOLO-World
(wagi FROZEN 9b2c17ab, guard SR-2 przez YoloDetector NIE — tu ładujemy wprost z sha-checkiem,
bo potrzebujemy set_classes wariantowego i pełnej listy boxów, nie top-1):
  - prompty klas (≥4 warianty), imgsz ∈ {640, 960, 1280} dla kanonu i najlepszego promptu,
  - metryki per wariant × tło (sky/terrain per KLATKA z pikseli — pierścień wokół etykiety):
      top1_on_target [%] (top-1 = argmax conf; środek w boxie etykiety),
      any_on_target  [%] (≥1 box na celu wśród wszystkich conf≥0.001),
      conf_sep: p50 conf boxów na celu vs p50 conf top-1 poza celem.
  - tabela progu conf dla najlepszego wariantu: TP-frames vs FP-frames per θ.

Wyjście: results/DET_RECON/sweep_results.json (+ raw per-frame jsonl do reuse).
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import sys
import time

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, ROOT)
from r02.mti import IMG_W, IMG_H

WEIGHTS = os.path.join(ROOT, ".b0deps/weights/yolov8s-worldv2.pt")
WEIGHTS_SHA = "9b2c17ab6124a913e9b3a5c170617920d91b0f01111a8479da69f00e2cf27792"
BOOTS = ["A1_c08_s03_r4", "A1b_c08_s03", "A2_c11_s01", "A2b_c11_s01"]
PROMPTS = {
    "P1_kanon": ["drone"],
    "P2_quad": ["quadcopter"],
    "P3_multi": ["drone", "quadcopter", "uav"],
    "P4_opis": ["small dark quadcopter drone flying"],
    "P5_aircraft": ["aircraft"],
}
IMGSZ_EXTRA = [960, 1280]      # dla P1 i zwycięzcy @640


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for ch in iter(lambda: f.read(1 << 16), b""):
            h.update(ch)
    return h.hexdigest()


def load_frames():
    """[(img_path, label_box_px(cx,cy,w,h), boot, Z)]"""
    out = []
    for b in BOOTS:
        meta = [json.loads(l) for l in open(f"{ROOT}/results/DET_RECON/labels/{b}/meta.jsonl")]
        for r in meta:
            if r["flag"] == "OK":
                out.append((f"{ROOT}/results/2A/stageA/{b}/frames/{r['frame']}",
                            tuple(r["box"]), b, r["uvZ"][2]))
    return out


def bg_class(img, box):
    """Tło per klatka: pierścień wokół boxa etykiety (±1.6×) — sky=jasne i gładkie."""
    cx, cy, w, h = box
    x0, x1 = int(max(0, cx - w * 1.6)), int(min(IMG_W, cx + w * 1.6))
    y0, y1 = int(max(0, cy - h * 2.5)), int(min(IMG_H, cy + h * 2.5))
    reg = img[y0:y1, x0:x1].astype(np.float32)
    ix0, ix1 = int(max(0, cx - w / 2)) - x0, int(min(IMG_W, cx + w / 2)) - x0
    iy0, iy1 = int(max(0, cy - h / 2)) - y0, int(min(IMG_H, cy + h / 2)) - y0
    mask = np.ones(reg.shape[:2], bool)
    mask[max(0, iy0):max(0, iy1), max(0, ix0):max(0, ix1)] = False
    ring = reg[mask] if reg.ndim == 2 else reg.mean(axis=2)[mask]
    return ("sky" if (ring.mean() > 190 and ring.std() < 14) else "terrain",
            round(float(ring.mean()), 1), round(float(ring.std()), 1))


def on_target(bx_px, lab):
    return abs(bx_px[0] - lab[0]) <= lab[2] / 2 and abs(bx_px[1] - lab[1]) <= lab[3] / 2


def main():
    assert sha256(WEIGHTS) == WEIGHTS_SHA, "wagi != FREEZE (SR-2)"
    import cv2
    from ultralytics import YOLOWorld

    frames = load_frames()
    print(f"[sweep] {len(frames)} klatek z etykietą OK")
    imgs, bgs = {}, {}
    for (fp, lab, b, Z) in frames:
        im = cv2.imread(fp)
        imgs[fp] = im
        bgs[fp] = bg_class(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), lab)

    results = {}
    raw_f = open(f"{ROOT}/results/DET_RECON/sweep_raw.jsonl", "w")

    def run(tag, classes, imgsz):
        # świeży model per wariant: set_classes PRZED 1. predictem (feler device-mismatch
        # CLIP przy set_classes po inferencji CUDA w ultralytics 8.4.115)
        model = YOLOWorld(WEIGHTS)
        model.set_classes(classes)
        per_bg = {}
        t0 = time.monotonic()
        for (fp, lab, b, Z) in frames:
            r = model.predict(imgs[fp], imgsz=imgsz, conf=0.001, verbose=False)[0]
            boxes = []
            if r.boxes is not None and len(r.boxes):
                for i in range(len(r.boxes)):
                    x, y, w, h = [float(t) for t in r.boxes.xywh[i]]
                    sx, sy = IMG_W / r.orig_shape[1], IMG_H / r.orig_shape[0]
                    boxes.append((x, y, w, h, float(r.boxes.conf[i])))
            bg = bgs[fp][0]
            d = per_bg.setdefault(bg, {"n": 0, "top1_on": 0, "any_on": 0,
                                       "conf_on": [], "conf_top1_off": []})
            d["n"] += 1
            if boxes:
                top1 = max(boxes, key=lambda z: z[4])
                t_on = on_target(top1, lab)
                d["top1_on"] += int(t_on)
                ons = [bb for bb in boxes if on_target(bb, lab)]
                d["any_on"] += int(bool(ons))
                d["conf_on"] += [bb[4] for bb in ons]
                if not t_on:
                    d["conf_top1_off"].append(top1[4])
            raw_f.write(json.dumps({"tag": tag, "frame": fp.split("/")[-1], "boot": b,
                                    "bg": bg, "Z": round(Z, 1), "lab": [round(x, 1) for x in lab],
                                    "boxes": [[round(v, 4) for v in bb] for bb in boxes[:12]]}) + "\n")
        dt = time.monotonic() - t0
        summ = {}
        for bg, d in per_bg.items():
            co = sorted(d["conf_on"]); cf = sorted(d["conf_top1_off"])
            summ[bg] = {"n": d["n"],
                        "top1_on_pct": round(100 * d["top1_on"] / d["n"], 1),
                        "any_on_pct": round(100 * d["any_on"] / d["n"], 1),
                        "conf_on_p50": round(co[len(co) // 2], 4) if co else None,
                        "conf_top1_off_p50": round(cf[len(cf) // 2], 4) if cf else None}
        summ["ms_per_frame"] = round(1000 * dt / len(frames), 1)
        results[tag] = summ
        print(tag, json.dumps(summ))

    for name, classes in PROMPTS.items():
        run(f"{name}@640", classes, 640)
    best = max([k for k in results if k.endswith("@640")],
               key=lambda k: sum(results[k][bg]["top1_on_pct"] * results[k][bg]["n"]
                                 for bg in results[k] if bg in ("sky", "terrain")))
    for sz in IMGSZ_EXTRA:
        run(f"P1_kanon@{sz}", PROMPTS["P1_kanon"], sz)
        if not best.startswith("P1_kanon"):
            bname = best.split("@")[0]
            run(f"{bname}@{sz}", PROMPTS[bname], sz)

    # tabela progu conf dla najlepszego wariantu ogółem (z raw)
    raw_f.close()
    best_all = max(results, key=lambda k: sum(results[k][bg]["top1_on_pct"] * results[k][bg]["n"]
                                              for bg in results[k] if bg in ("sky", "terrain")))
    rows = [json.loads(l) for l in open(f"{ROOT}/results/DET_RECON/sweep_raw.jsonl")
            if json.loads(l)["tag"] == best_all]
    thr_tab = {}
    for th in (0.005, 0.01, 0.02, 0.05, 0.1):
        tp = fp_ = 0
        for r in rows:
            lab = r["lab"]
            bs = [b for b in r["boxes"] if b[4] >= th]
            if any(on_target(b, lab) for b in bs):
                tp += 1
            if any(not on_target(b, lab) for b in bs):
                fp_ += 1
        thr_tab[th] = {"frames_TP_pct": round(100 * tp / len(rows), 1),
                       "frames_FPbox_pct": round(100 * fp_ / len(rows), 1)}
    bgc = {}
    for fp2, (bg, m, s) in bgs.items():
        bgc[bg] = bgc.get(bg, 0) + 1
    out = {"n_frames": len(frames), "bg_counts": bgc, "variants": results,
           "best_variant": best_all, "conf_threshold_table": thr_tab}
    json.dump(out, open(f"{ROOT}/results/DET_RECON/sweep_results.json", "w"), indent=1)
    print(json.dumps({"bg_counts": bgc, "best": best_all, "thr": thr_tab}, indent=1))


if __name__ == "__main__":
    main()
