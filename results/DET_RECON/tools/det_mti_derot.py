#!/usr/bin/env python3
"""R3b: rezyduum derotacji MTI na KOLEJNYCH zapisanych klatkach (ograniczenie: zapis
zdecymowany ~2 Hz => dt ~0.5 s, 7x dluzszy niz lotne 1/15 s — pomiar to GORNE oszacowanie
mechanizmu, nie replay). Porownanie mean|diff| tla: bez derotacji vs z derotacja
(mti.homography z Δquat attitude shadow_feed) na parach A2b (orbita ~20 deg/s)."""
import json, sys, glob, os
import numpy as np
sys.path.insert(0, "/home/olga/projects/liquidpatrol")
from r02.mti import rel_rotation_opt, homography, warp_prev
import cv2

d = "results/2A/stageA/A2b_c11_s01"
sf = {round(r["t_frame"],3): r for r in
      (json.loads(l) for l in open(d+"/shadow_feed.jsonl")) if r.get("t_frame")}
fr = sorted(glob.glob(d+"/frames/*.jpg"))
pairs = []
for i in range(len(fr)-1):
    t0 = float(os.path.basename(fr[i])[2:-4]); t1 = float(os.path.basename(fr[i+1])[2:-4])
    r0, r1 = sf.get(round(t0,3)), sf.get(round(t1,3))
    if r0 and r1 and r0.get("own_q") and r1.get("own_q") and 0.3 < t1-t0 < 0.8:
        pairs.append((fr[i], fr[i+1], r0["own_q"], r1["own_q"], t1-t0))
res = []
for (f0, f1, q0, q1, dt) in pairs[:40]:
    a = cv2.imread(f0, cv2.IMREAD_GRAYSCALE).astype(np.float32)
    b = cv2.imread(f1, cv2.IMREAD_GRAYSCALE).astype(np.float32)
    raw = float(np.abs(b - a)[40:-40, 40:-40].mean())
    H = homography(rel_rotation_opt(q0, q1))
    aw, valid = warp_prev(a.astype(np.uint8), H)
    aw = aw.astype(np.float32)
    m = valid[40:-40, 40:-40] > 0
    der = float(np.abs(b - aw)[40:-40, 40:-40][m].mean())
    res.append((dt, raw, der))
rs = sorted(r[1] for r in res); ds = sorted(r[2] for r in res)
print(json.dumps({"n_pairs": len(res), "dt_p50": round(sorted(r[0] for r in res)[len(res)//2],3),
  "mean_absdiff_raw_p50": round(rs[len(rs)//2],2), "mean_absdiff_derot_p50": round(ds[len(ds)//2],2),
  "redukcja_pct_p50": round(100*(1 - ds[len(ds)//2]/rs[len(rs)//2]),1)}))
