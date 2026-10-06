#!/usr/bin/env python3
"""results/DET_RECON/tools/det_labels.py — R2 PROMPT_DET_S0: pipeline etykiet z GT.

Etykieta per klatka: GT intruza (gt_intruder.jsonl, NED APPLIED) + poza własna GT
(trace t:"gt": ENU + kwaternion POZY GZ, edycja D5) + projekcja FROZEN 1:1 z
results/2A/tools/coverage_real.py (R_ned←frd = M(ned←enu)·R(enu←body_gz)·M(body_gz←frd),
pinhole f_px=270, offset kamery FRD (0.12,−0.03,−0.242)) ⇒ box:
  w_px = FX · W_REAL / Z_opt   (W_REAL=2.5 m — kanon pinhole FREEZE_2A),
  h_px = FX · H_REAL / Z_opt   (H_REAL=0.5 m — pion wizualiów intruder_model.sdf:
                                korpus 0.32 + rotory do ~0.2; PRIOR do walidacji IoU).

Filtry (zliczane, nie ciche): (F1) brak wiersza gt ±0.06 s → DROP; (F2) t poza zakresem
gt_intruder → DROP (intruz w pozycji nieznanej tej chwili — klatka NIE jest bezpiecznym
negatywem); (F3) środek poza kadrem lub Z_opt<Z_MIN → NEGATYW (etykieta pusta — intruz
policzalnie poza FOV); (F4) Z_opt>Z_MAX → NEGATYW z flagą (sub-pikselowy cel).

Wyjścia (OUTDIR): labels/<frame>.txt (YOLO: cls cx cy w h znorm., puste=negatyw),
meta.jsonl (per klatka: t, uv, Z, box_px, flags), stats.json.
Walidacja (a): dla WSZYSTKICH wierszy shadow_feed z boxem (14.7 Hz — nie tylko zapisane
jpg): projekcja etykiety w t_frame → dystans środków [px] → „YOLO na celu" gdy środek
boxa YOLO wewnątrz boxa etykiety → IoU; statystyki per boot.
Walidacja (b): --sample N: PNG z narysowaną etykietą (zielony) + boxem YOLO (żółty).

Użycie: det_labels.py <bootdir> <outdir> [--sample N] [--z-min 1.0] [--z-max 60]
"""
from __future__ import annotations

import argparse
import bisect
import glob
import json
import os
import sys

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "results/2A/tools"))
from coverage_real import R_ned_frd_from_gz, interp, load_jsonl, CAM_OFF_FRD   # kanon 1:1
from common.frames import enu2ned
from r02.mti import FX, CX, CY, IMG_W, IMG_H

W_REAL = 2.5    # kanon FREEZE_2A (pinhole zasięgu)
H_REAL = 0.5    # prior pionu (intruder_model.sdf wizualia) — walidowany IoU


def project_box(own_ned, q_gz, tgt_ned, z_min):
    """→ (u, v, Z, w_px, h_px) albo None gdy za plecami/za blisko."""
    R = R_ned_frd_from_gz(q_gz)
    rel_frd = R.T @ (np.asarray(tgt_ned) - np.asarray(own_ned))
    cam = rel_frd - np.asarray(CAM_OFF_FRD)
    x_opt, y_opt, z_opt = cam[1], cam[2], cam[0]
    if z_opt <= z_min:
        return None
    u = CX + x_opt / z_opt * FX
    v = CY + y_opt / z_opt * FX
    return float(u), float(v), float(z_opt), FX * W_REAL / z_opt, FX * H_REAL / z_opt


def clip_box(u, v, w, h):
    """Przytnij do kadru; zwraca (cx,cy,w,h) px albo None gdy znika."""
    x0, x1 = max(0.0, u - w / 2), min(float(IMG_W), u + w / 2)
    y0, y1 = max(0.0, v - h / 2), min(float(IMG_H), v + h / 2)
    if x1 - x0 < 2.0 or y1 - y0 < 2.0:
        return None
    return ((x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0)


def iou(b1, b2):
    """boxy (cx,cy,w,h) px."""
    ax0, ax1 = b1[0] - b1[2] / 2, b1[0] + b1[2] / 2
    ay0, ay1 = b1[1] - b1[3] / 2, b1[1] + b1[3] / 2
    bx0, bx1 = b2[0] - b2[2] / 2, b2[0] + b2[2] / 2
    by0, by1 = b2[1] - b2[3] / 2, b2[1] + b2[3] / 2
    iw = max(0.0, min(ax1, bx1) - max(ax0, bx0))
    ih = max(0.0, min(ay1, by1) - max(ay0, by0))
    inter = iw * ih
    return inter / (b1[2] * b1[3] + b2[2] * b2[3] - inter) if inter > 0 else 0.0


class BootGeo:
    """GT drona + intruza bootu; label(t) → dict."""

    def __init__(self, bootdir, z_min, z_max):
        trace = load_jsonl(os.path.join(bootdir, "trace.jsonl"))
        self.gt = [r for r in trace if r.get("t") == "gt" and "qw" in r]
        self.gts = [r["sim"] for r in self.gt]
        gtin = load_jsonl(os.path.join(bootdir, "gt_intruder.jsonl"))
        self.its = [r["t_sim"] for r in gtin]
        self.ips = [r["ned"] for r in gtin]
        self.z_min, self.z_max = z_min, z_max

    def label(self, t):
        i = bisect.bisect_left(self.gts, t)
        cand = [j for j in (i - 1, i) if 0 <= j < len(self.gt)]
        if not cand:
            return {"flag": "F1_no_gt"}
        j = min(cand, key=lambda k: abs(self.gts[k] - t))
        if abs(self.gts[j] - t) > 0.06:
            return {"flag": "F1_no_gt"}
        tgt = interp(self.its, self.ips, t)
        if tgt is None:
            return {"flag": "F2_no_intruder_gt"}
        g = self.gt[j]
        own = enu2ned([g["x"], g["y"], g["z"]])
        p = project_box(own, [g["qw"], g["qx"], g["qy"], g["qz"]], tgt, self.z_min)
        if p is None:
            return {"flag": "F3_behind", "box": None}
        u, v, Z, w, h = p
        if not (0.0 <= u <= IMG_W and 0.0 <= v <= IMG_H):
            return {"flag": "F3_out_of_fov", "box": None, "uvZ": [u, v, Z]}
        if Z > self.z_max:
            return {"flag": "F4_too_far", "box": None, "uvZ": [u, v, Z]}
        cb = clip_box(u, v, w, h)
        if cb is None:
            return {"flag": "F3_clipped_away", "box": None, "uvZ": [u, v, Z]}
        return {"flag": "OK", "box": list(cb), "uvZ": [u, v, Z]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bootdir")
    ap.add_argument("outdir")
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--z-min", type=float, default=1.0)
    ap.add_argument("--z-max", type=float, default=60.0)
    a = ap.parse_args()
    os.makedirs(os.path.join(a.outdir, "labels"), exist_ok=True)

    geo = BootGeo(a.bootdir, a.z_min, a.z_max)
    frames = sorted(glob.glob(os.path.join(a.bootdir, "frames", "*.jpg")))
    stats = {"n_frames": len(frames), "flags": {}, "pos": 0, "neg": 0}
    meta = []
    for fp in frames:
        base = os.path.basename(fp)
        t = float(base[2:-4])
        lab = geo.label(t)
        stats["flags"][lab["flag"]] = stats["flags"].get(lab["flag"], 0) + 1
        rec = {"frame": base, "t": t, **lab}
        if lab["flag"] in ("F1_no_gt", "F2_no_intruder_gt"):
            meta.append(rec); continue              # DROP — bez pliku etykiety
        lp = os.path.join(a.outdir, "labels", base[:-4] + ".txt")
        if lab["flag"] == "OK":
            cx, cy, w, h = lab["box"]
            open(lp, "w").write(f"0 {cx/IMG_W:.6f} {cy/IMG_H:.6f} {w/IMG_W:.6f} {h/IMG_H:.6f}\n")
            stats["pos"] += 1
        else:
            open(lp, "w").write("")                  # negatyw
            stats["neg"] += 1
        meta.append(rec)
    with open(os.path.join(a.outdir, "meta.jsonl"), "w") as f:
        for r in meta:
            f.write(json.dumps(r) + "\n")

    # --- walidacja (a): IoU etykieta↔YOLO na wierszach shadow_feed (pełna kadencja) ---
    val = None
    sfp = os.path.join(a.bootdir, "shadow_feed.jsonl")
    if os.path.exists(sfp):
        n_box = n_lab = n_on = 0
        ious, dists = [], []
        for r in load_jsonl(sfp):
            if r.get("t_frame") is None or not r.get("box"):
                continue
            n_box += 1
            lab = geo.label(r["t_frame"])
            if lab["flag"] != "OK":
                continue
            n_lab += 1
            bx = r["box"]
            yb = (bx[0] * IMG_W, bx[1] * IMG_H, bx[2] * IMG_W, bx[3] * IMG_H)
            lb = tuple(lab["box"])
            d = ((yb[0] - lb[0]) ** 2 + (yb[1] - lb[1]) ** 2) ** 0.5
            dists.append(d)
            on = (abs(yb[0] - lb[0]) <= lb[2] / 2 and abs(yb[1] - lb[1]) <= lb[3] / 2)
            if on:
                n_on += 1
                ious.append(iou(yb, lb))
        srt = sorted(ious)
        val = {"n_yolo_box": n_box, "n_z_etykieta_OK": n_lab, "n_yolo_na_celu": n_on,
               "frac_na_celu": round(n_on / n_lab, 4) if n_lab else None,
               "iou_na_celu": {"n": len(srt),
                               "p50": round(srt[len(srt) // 2], 3) if srt else None,
                               "p90": round(srt[int(len(srt) * 0.9)], 3) if srt else None,
                               "min": round(srt[0], 3) if srt else None}}

    stats["val_vs_yolo"] = val
    with open(os.path.join(a.outdir, "stats.json"), "w") as f:
        json.dump(stats, f, indent=1)
    print(json.dumps(stats, indent=1))

    # --- walidacja (b): próbka wizualna ---
    if a.sample:
        import cv2
        sfrows = {round(r["t_frame"], 3): r for r in load_jsonl(sfp)
                  if r.get("t_frame") is not None} if os.path.exists(sfp) else {}
        ok_frames = [r for r in meta if r["flag"] == "OK"]
        step = max(1, len(ok_frames) // a.sample)
        os.makedirs(os.path.join(a.outdir, "sample"), exist_ok=True)
        for r in ok_frames[::step][:a.sample]:
            img = cv2.imread(os.path.join(a.bootdir, "frames", r["frame"]))
            cx, cy, w, h = r["box"]
            cv2.rectangle(img, (int(cx - w / 2), int(cy - h / 2)),
                          (int(cx + w / 2), int(cy + h / 2)), (0, 255, 0), 2)
            sr = sfrows.get(round(r["t"], 3))
            if sr and sr.get("box"):
                b = sr["box"]
                cv2.rectangle(img, (int((b[0] - b[2] / 2) * IMG_W), int((b[1] - b[3] / 2) * IMG_H)),
                              (int((b[0] + b[2] / 2) * IMG_W), int((b[1] + b[3] / 2) * IMG_H)),
                              (0, 255, 255), 1)
            cv2.putText(img, f"t={r['t']:.1f} Z={r['uvZ'][2]:.1f}m", (5, 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
            cv2.imwrite(os.path.join(a.outdir, "sample", r["frame"].replace(".jpg", "_lab.png")), img)
        print(f"[sample] zapisano do {a.outdir}/sample")


if __name__ == "__main__":
    main()
