#!/usr/bin/env python3
"""results/DET3_RECON/tools/det3_r1.py — R1 PROMPT_DET3_S0: czy zasięg jest wąskim gardłem dziś.

Per boot korpusu DET (etykiety det_labels 8f7430cd, meta.jsonl z Z per klatka):
  (1) det_replay.py de0feb37 BEZ ZMIAN (subprocess) z det_v2 775ead15 → per klatka box/conf/
      mti_ok/fresh/trk_pos_ned (rdzeń FeedVision acc81df7, ten sam tor co lot);
  (2) przebieg MTI-only na tych samych klatkach i tych samych pozach (own_q z shadow_feed,
      dobór ±0.1 s jak det_replay): MTITracker z MTIParams FROZEN (persystencja) +
      motion_components z MTIParams FROZEN (surowe, po filtrze rozmiaru) + DIAGNOSTYKA
      motion_components z min_area_px=1 (rozmiar bloba PRZED filtrem 8 px; parametr
      wywołania, r02/mti.py nietknięty).
Złączenie z meta (Z, box etykiety) i fazą z demo.jsonl (najbliższy wiersz t_sim ≤ 0.2 s).
Definicje: YOLO na celu = środek top-1 wewnątrz boxa etykiety (det_replay.py:149-157);
MTI na celu = centroid komponentu wewnątrz boxa etykiety poszerzonego o TOL_PX z każdej strony.

Użycie: det3_r1.py <labels_dir_boota> <frames_root_boota> <out_dir>
Wyjście: <out_dir>/<boot>.frames.jsonl (per klatka OK) + <boot>.replay.json (+ .replay.jsonl).
"""
from __future__ import annotations

import bisect
import glob
import json
import os
import subprocess
import sys

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "results/2A/tools"))
import cv2                                                        # noqa: E402
from r02.mti import MTITracker, MTIParams, motion_components, IMG_W, IMG_H   # noqa: E402
from coverage_real import interp                                  # noqa: E402

DET_V2 = os.path.join(ROOT, "net/frozen/det_v2.pt")
DET_REPLAY = os.path.join(ROOT, "results/DET/tools/det_replay.py")
PY = os.path.join(ROOT, ".b0deps/bin/python")
TOL_PX = 3.0


def load_jsonl(p):
    out = []
    for ln in open(p):
        ln = ln.strip()
        if ln:
            try:
                out.append(json.loads(ln))
            except json.JSONDecodeError:
                pass
    return out


def on_box(cx, cy, lb, tol=0.0):
    return abs(cx - lb[0]) <= lb[2] / 2 + tol and abs(cy - lb[1]) <= lb[3] / 2 + tol


def main():
    lab_dir, fr_dir, out_dir = sys.argv[1:4]
    boot = os.path.basename(lab_dir.rstrip("/"))
    os.makedirs(out_dir, exist_ok=True)
    rep_json = os.path.join(out_dir, f"{boot}.replay.json")
    if not os.path.exists(rep_json):
        subprocess.run([PY, DET_REPLAY, fr_dir, "--detector", DET_V2, "--out", rep_json],
                       check=True, stdout=subprocess.DEVNULL, cwd=ROOT)
    rep = {round(r["t_frame"], 3): r for r in load_jsonl(rep_json + ".replay.jsonl")}

    meta = {round(r["t"], 3): r for r in load_jsonl(os.path.join(lab_dir, "meta.jsonl"))}
    gtin = load_jsonl(os.path.join(fr_dir, "gt_intruder.jsonl"))
    its, ips = [r["t_sim"] for r in gtin], [r["ned"] for r in gtin]
    demo = [r for r in load_jsonl(os.path.join(fr_dir, "demo.jsonl")) if "phase" in r]
    dts = [r["t_sim"] for r in demo]

    def phase_at(t):
        i = bisect.bisect_left(dts, t)
        c = [j for j in (i - 1, i) if 0 <= j < len(dts)]
        if not c:
            return None
        k = min(c, key=lambda j: abs(dts[j] - t))
        return demo[k]["phase"] if abs(dts[k] - t) <= 0.2 else None

    own = {}
    for r in load_jsonl(os.path.join(fr_dir, "shadow_feed.jsonl")):
        if r.get("t_frame") is not None and r.get("own_pos_ned") and r.get("own_q"):
            own[round(r["t_frame"], 3)] = r["own_q"]
    ots = sorted(own)

    def q_at(t):
        i = bisect.bisect_left(ots, round(t, 3))
        c = [j for j in (i - 1, i) if 0 <= j < len(ots)]
        if not c:
            return None
        k = min(c, key=lambda j: abs(ots[j] - t))
        return own[ots[k]] if abs(ots[k] - t) <= 0.1 else None

    trk = MTITracker(MTIParams())          # FROZEN: delta=3, persist 3/4
    p_diag = MTIParams(min_area_px=1)      # diagnostyka rozmiaru (parametr wywołania)
    buf = []                               # (frame, q) — ta sama para co MTITracker (delta=3)
    out = []
    for fp in sorted(glob.glob(os.path.join(fr_dir, "frames", "*.jpg"))):
        base = os.path.basename(fp)
        t = float(base[2:-4])
        q = q_at(t)
        if q is None:
            continue
        fr = cv2.imread(fp, cv2.IMREAD_GRAYSCALE)
        cons, dbg = trk.push(fr, q)
        buf.append((fr, q))
        if len(buf) > 4:
            buf.pop(0)
        m = meta.get(round(t, 3))
        if not m or m.get("flag") != "OK":
            continue
        lb = m["box"]
        Z = m["uvZ"][2]
        rec = {"boot": boot, "t": t, "Z": round(Z, 3), "lab_w": round(lb[2], 2),
               "lab_h": round(lb[3], 2), "phase": phase_at(t)}
        rr = rep.get(round(t, 3))
        rec["replayed"] = rr is not None
        if rr:
            b = rr.get("box")
            rec["conf"] = rr.get("conf")
            rec["yolo_on"] = bool(b) and on_box(b[0] * IMG_W, b[1] * IMG_H, lb)
            rec["mti_ok_flight"] = rr.get("mti_ok")
            rec["fresh"] = rr.get("fresh")
            if rr.get("fresh") and rr.get("trk_pos_ned"):
                g = interp(its, ips, t)
                if g is not None:
                    rec["err"] = round(sum((rr["trk_pos_ned"][k] - g[k]) ** 2 for k in range(3)) ** 0.5, 4)
        warm = len(buf) < 4
        rec["mti_warm"] = warm
        if not warm:
            (pf, pq), (cf, cq) = buf[0], buf[-1]
            raw, _ = motion_components(pf, pq, cf, cq, MTIParams())
            dia, _ = motion_components(pf, pq, cf, cq, p_diag)
            rec["mti_raw_on"] = any(on_box(c["cx"] * IMG_W, c["cy"] * IMG_H, lb, TOL_PX) for c in raw)
            rec["mti_cons_on"] = any(on_box(c["cx"] * IMG_W, c["cy"] * IMG_H, lb, TOL_PX) for c in cons)
            hit = [c["area_px"] for c in dia if on_box(c["cx"] * IMG_W, c["cy"] * IMG_H, lb, TOL_PX)]
            rec["blob_area_diag"] = max(hit) if hit else 0
        out.append(rec)
    with open(os.path.join(out_dir, f"{boot}.frames.jsonl"), "w") as f:
        for r in out:
            f.write(json.dumps(r) + "\n")
    print(boot, len(out))


if __name__ == "__main__":
    main()
