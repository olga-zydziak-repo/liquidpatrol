#!/usr/bin/env python3
"""results/DET3_RECON/tools/det3_r2_kontrast.py — R2: kontrast celu wobec tła na klatkach korpusu DET.

Per klatka OK (meta.jsonl, det_labels 8f7430cd): w boxie etykiety p10 jasności (ciemne piksele
sylwetki), mediana pierścienia 6 px wokół boxa (tło); kontrast = mediana_tła − p10_boxa [DN].
Porównanie z diff_thr 22 (r02/mti.py:30). Próbka co 10. klatka OK, wszystkie boot-y NEW.
"""
import glob, json, os, sys
import cv2, numpy as np
ROOT = "/home/olga/projects/liquidpatrol"
rows = []
for md in sorted(glob.glob(f"{ROOT}/results/DET/labels/*/meta.jsonl")):
    b = md.split("/")[-2]
    ok = [json.loads(l) for l in open(md)]
    ok = [r for r in ok if r["flag"] == "OK"]
    for r in ok[::10]:
        im = cv2.imread(f"{ROOT}/results/DET/collect/{b}/frames/{r['frame']}", cv2.IMREAD_GRAYSCALE)
        cx, cy, w, h = r["box"]
        x0, x1, y0, y1 = int(cx - w / 2), int(cx + w / 2), int(cy - h / 2), int(cy + h / 2)
        H, W = im.shape
        inner = im[max(0, y0):min(H, y1), max(0, x0):min(W, x1)]
        X0, X1, Y0, Y1 = max(0, x0 - 6), min(W, x1 + 6), max(0, y0 - 6), min(H, y1 + 6)
        outer = im[Y0:Y1, X0:X1].astype(float)
        mask = np.ones_like(outer, bool); mask[(max(0, y0) - Y0):(min(H, y1) - Y0), (max(0, x0) - X0):(min(W, x1) - X0)] = False
        if inner.size == 0 or mask.sum() == 0:
            continue
        rows.append({"boot": b, "Z": r["uvZ"][2], "v": r["uvZ"][1], "bg": float(np.median(outer[mask])),
                     "p10": float(np.percentile(inner, 10)), "kontrast": float(np.median(outer[mask]) - np.percentile(inner, 10))})
out = {}
for lo, hi in [(6, 8), (8, 10), (10, 12), (12, 15)]:
    s = [r["kontrast"] for r in rows if lo <= r["Z"] < hi]
    bg = [r["bg"] for r in rows if lo <= r["Z"] < hi]
    if s:
        out[f"{lo}-{hi}"] = {"n": len(s), "kontrast_p10": round(float(np.percentile(s, 10)), 1),
                             "kontrast_p50": round(float(np.median(s)), 1), "tlo_p50": round(float(np.median(bg)), 1),
                             "frac_kontrast_ge_22": round(float(np.mean(np.array(s) >= 22)), 3)}
print(json.dumps(out, indent=1))
json.dump(out, open(sys.argv[1], "w"), indent=1)
