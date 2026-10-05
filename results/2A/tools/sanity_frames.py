#!/usr/bin/env python3
"""results/2A/tools/sanity_frames.py — 6 klatek sanity do repo (PROMPT_2A_S2 §3, wzór U1R: 3/boot,
z boxem i wartościami shadow vs GT na podpisie). Wybór per boot: (a) najlepsza świeża (min err),
(b) najgorsza świeża (max err — ilustracja FP/kadrowania), (c) klatka ENTRY. Narzędzie sędziowskie
offline — GT dozwolone. Zapis PNG do <bootdir>/sanity/ (commitowane; jpg surowe zostają lokalnie)."""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from percep_judge import load_jsonl, gt_flat, interp


def pick(rows, ts, ps):
    rows_g = (rows,)
    fresh = []
    entry = None
    for r in rows:
        if r.get("ev") == "ENTRY" and entry is None:
            entry = r
        if not (r.get("fresh") and r.get("trk_pos_ned")):
            continue
        g = interp(ts, ps, r["t_frame"])
        if g is None:
            continue
        fresh.append((math.dist(r["trk_pos_ned"], g), r, g))
    fresh.sort(key=lambda x: x[0])
    out = []
    if fresh:
        out.append(("best_fresh", fresh[0]))
        out.append(("worst_fresh", fresh[-1]))
    if entry is not None:
        g = interp(ts, ps, entry["t_frame"])
        e = math.dist(entry["trk_pos_ned"], g) if (g and entry.get("trk_pos_ned")) else None
        out.append(("entry", (e, entry, g)))
    # fallback (boot bez świeżych w oknie GT): boxy NIE-admitowane — ilustracja bramy D2
    # (struktura∧MTI odrzuca top-1 tła) na najwyższym conf i na medianie okna GT
    if len(out) < 3:
        nadm = [r for r in rows_g[0] if r.get("box") and not r.get("locked")
                and interp(ts, ps, r["t_frame"]) is not None]
        nadm.sort(key=lambda r: -(r.get("conf") or 0))
        for tag, r in (("d2_odrzut_maxconf", nadm[0] if nadm else None),
                       ("d2_odrzut_mediana", nadm[len(nadm) // 2] if nadm else None)):
            if r is not None and len(out) < 3:
                out.append((tag, (None, r, interp(ts, ps, r["t_frame"]))))
    return out[:3]


def nearest_frame(frames, t):
    return min(frames, key=lambda f: abs(f[0] - t)) if frames else None


def annotate(img, rec, err, gt, tag):
    H, W = img.shape[:2]
    vis = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR) if img.ndim == 2 else img.copy()
    if rec.get("box"):
        cx, cy, w, h = rec["box"]
        x0, y0 = int((cx - w / 2) * W), int((cy - h / 2) * H)
        x1, y1 = int((cx + w / 2) * W), int((cy + h / 2) * H)
        cv2.rectangle(vis, (x0, y0), (x1, y1), (0, 0, 255), 2)
    pad = np.zeros((84, W, 3), dtype=np.uint8)
    lines = [
        f"[{tag}] t={rec['t_frame']:.2f} conf={rec.get('conf')} mti={rec.get('mti_ok')} ev={rec.get('ev')} fresh={rec.get('fresh')}",
        f"shadow trk_ned={rec.get('trk_pos_ned')}",
        f"GT ned={[round(x,2) for x in gt] if gt else None}  err={round(err,2) if err is not None else 'n/a'} m",
    ]
    for i, s in enumerate(lines):
        cv2.putText(pad, s, (6, 22 + 26 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
    return np.vstack([vis, pad])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bootdir")
    a = ap.parse_args()
    rows = [r for r in load_jsonl(os.path.join(a.bootdir, "shadow_feed.jsonl")) if r.get("t") != "meta"]
    ts, ps = gt_flat(load_jsonl(os.path.join(a.bootdir, "gt_intruder.jsonl")))
    frames = []
    for fp in sorted(glob.glob(os.path.join(a.bootdir, "frames", "*.jpg"))):
        try:
            frames.append((float(os.path.basename(fp)[2:-4]), fp))
        except ValueError:
            pass
    outdir = os.path.join(a.bootdir, "sanity")
    os.makedirs(outdir, exist_ok=True)
    for tag, (err, rec, g) in pick(rows, ts, ps):
        nf = nearest_frame(frames, rec["t_frame"])
        if nf is None:
            print(f"[sanity] {tag}: brak klatek"); continue
        dt = abs(nf[0] - rec["t_frame"])
        img = cv2.imread(nf[1], cv2.IMREAD_GRAYSCALE)
        vis = annotate(img, rec, err, g, f"{tag} dt_klatki={dt:.2f}s")
        out = os.path.join(outdir, f"{tag}_t{rec['t_frame']:.1f}.png")
        cv2.imwrite(out, vis)
        print(f"[sanity] {out} (err={err} m, dt_klatki={dt:.2f}s)")


if __name__ == "__main__":
    main()
