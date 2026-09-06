#!/usr/bin/env python3
"""net/demo_v2_clip.py — montaż DEMO_V2.mp4 (PROMPT_DEMO_V2 D3). DEMO≠POMIAR.

Styl DEMO-B (cv2, bez ffmpeg; helpery z acts.build_clip). Plansze WYŁĄCZNIE ze zdaniami kanonu
ANEKS_NET-4 §2 (zdanie o osłonie DOKŁADNIE jak w D3). Łańcuch prowieniencji per epizod z manifestów.
Zakazy trwałe: bez „failsafe zawodzi", bez języka istotności, bez „native ucieka".

Uruchom: python3 -m net.demo_v2_clip <run_dir1> [<run_dir2> ...] --out results/DEMO_V2/DEMO_V2.mp4
"""
from __future__ import annotations
import argparse, glob, json, os, subprocess, sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from acts.build_clip import _text_card, _wrap, _load_frame, W, H


def _overlay(cv2, frame, banner, footer):
    """Lower-third jak DEMO-B, ale footer auto-skalowany by ZMIEŚCIĆ się w kadrze (zdanie kanonu §2/E2
    jest mandatowane verbatim — nie wolno go obciąć)."""
    img = frame.copy(); ov = img.copy()
    cv2.rectangle(ov, (0, H - 130), (W, H), (0, 0, 0), -1)
    cv2.addWeighted(ov, 0.55, img, 0.45, 0, img)
    y = H - 95
    for ln in _wrap(cv2, banner, 0.7, W - 60)[:2]:
        cv2.putText(img, ln, (30, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
        y += 34
    fs = 0.5
    while fs > 0.28 and cv2.getTextSize(footer, cv2.FONT_HERSHEY_SIMPLEX, fs, 1)[0][0] > W - 44:
        fs -= 0.02
    cv2.putText(img, footer, (22, H - 16), cv2.FONT_HERSHEY_SIMPLEX, fs, (150, 200, 255), 1, cv2.LINE_AA)
    return img

FOOTER = "the network flies under the same frozen shield and through the same controller socket as every controller in the program; the shield did not need to intervene"

# Kanon roszczeń ANEKS_NET-4 §2 (EN, tylko WOLNO — plansze)
CANON_OPEN = [
    "DEMONSTRATION - NOT A MEASUREMENT",
    "No number here enters any ledger. Seeds chosen openly for the film.",
    "Verdicts live in RAPORT_NET (ANEKS_NET-4).",
]
CANON_CLAIMS = [
    "A 20-neuron CfC network (~1.9k params),",
    "trained by pure imitation on 114 demonstrations,",
    "matches the teacher's SITL flight success (45/48 vs 44/48;",
    "47/48 concordant pairs) and passes the pre-registered 0.9*p_exec gate,",
    "under an emulated track-feed (10 Hz, 0.2 s, sigma 0.5 m).",
]
CANON_CLOSE = [
    "Controller swap (script -> network) under UNCHANGED certs and pins,",
    "weights identity verified at every start (weights_sha).",
    "Intruder trajectory is deterministic; the network's flight is",
    "similar, not identical (the feed samples noise from the seed).",
]


def _prov(run_dir):
    m = json.load(open(os.path.join(run_dir, "manifest.json")))
    eps = ", ".join(e["scenario_id"] for e in m.get("episodes", []))
    wh = (m.get("world_hash") or "").split()[0][:12]
    return {
        "eps": eps,
        "world_hash": wh,
        "weights_sha": (m.get("weights_sha") or "")[:16],
        "controller_sha": (m.get("controller_sha") or "")[:12],
        "n_ep": m.get("n_episodes"),
        "d6": m.get("n_success_D6"),
    }


def main():
    import cv2
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dirs", nargs="+")
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "DEMO_V2", "DEMO_V2.mp4"))
    ap.add_argument("--fps", type=float, default=8.0)
    ap.add_argument("--stride", type=int, default=2, help="co która klatka (grabber ~1 Hz)")
    a = ap.parse_args()
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()

    vw = cv2.VideoWriter(a.out, cv2.VideoWriter_fourcc(*"mp4v"), a.fps, (W, H))

    def hold(img, secs):
        for _ in range(int(secs * a.fps)):
            vw.write(img)

    # karty otwierające: dyskleimer + roszczenie kanonu
    hold(_text_card(cv2, CANON_OPEN, sub="LiquidPatrol | position 5 | NCP-20 (CfC)"), 4.0)
    hold(_text_card(cv2, CANON_CLAIMS, sub=f"canon ANEKS_NET-4 sec2 | commit {commit}"), 5.0)

    for rd in a.run_dirs:
        p = _prov(rd)
        # karta prowieniencji epizodu
        prov_lines = [f"scenarios: {p['eps']}",
                      f"controller=net (NCP-20)  weights_sha={p['weights_sha']}",
                      f"controller_sha={p['controller_sha']}  world_hash={p['world_hash']}",
                      f"feed: FEED-B 10 Hz, 0.2 s, sigma 0.5 m  |  D6 {p['d6']}/{p['n_ep']}",
                      "seed-deterministic intruder; flight similar, not identical"]
        hold(_text_card(cv2, prov_lines, sub=f"provenance | {os.path.basename(rd)}"), 4.0)
        frames = sorted(glob.glob(os.path.join(rd, "frames", "f_*.npy")))[::a.stride]
        banner = f"NCP-20 CfC orbiting intruder under PatrolShield  |  {p['eps']}"
        for f in frames:
            try:
                fr = _load_frame(cv2, f)
            except Exception:
                continue
            vw.write(_overlay(cv2, fr, banner, FOOTER))

    # karty zamykające: kanon + nota trajektorii
    hold(_text_card(cv2, CANON_CLOSE, sub="canon ANEKS_NET-4 sec2"), 5.0)
    vw.release()
    print(f"[demo_v2] zapisano {a.out}")


if __name__ == "__main__":
    main()
