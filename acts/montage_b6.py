#!/usr/bin/env python3
"""acts/montage_b6.py — DEMO-B blok B6: montaż z prób OSĄDZONYCH (verdict VALID ∧ habitat VALID).

Wejście = kolejne run_dir aktów (kolejność dema, np. A1 A3 A2). Każdy MUSI mieć proba_N.mp4 (build_clip)
oraz verdict.json/habitat.json = VALID — inaczej ODMOWA (B6: materiał tylko z prób osądzonych, plansze §1c).
Wyjście: montage.mp4 = karta tytułowa + DWA dyskleimery §1c (globalnie, raz, SR-M2) → dla każdego aktu:
karta CUT „separate boot" + klatki klipu aktu. Renderowane cv2 (brak ffmpeg).

Uruchom: python3 -m acts.montage_b6 --out results/demo/montage.mp4 A1:results/demo/A1/proba_1 \
         A3:results/demo/rehearsal/A3/proba_1 A2:results/demo/A2/proba_2 [--fps 8]
"""
from __future__ import annotations
import argparse, json, os, sys
import numpy as np

W, H = 1280, 720


def main():
    import cv2
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+", help="ACT:run_dir w kolejności dema")
    ap.add_argument("--out", required=True)
    ap.add_argument("--fps", type=float, default=8.0)
    ap.add_argument("--allow-partial", action="store_true", help="pomiń akty nie-VALID zamiast twardej ODMOWY")
    args = ap.parse_args()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, root)
    from acts.build_clip import _text_card, _wrap
    from tools.gen_subtitles import STRINGS
    S = STRINGS["en"]

    # bramka: każdy bieg osądzony VALID
    items = []
    for spec in args.runs:
        act, rd = spec.split(":", 1)
        v = json.load(open(os.path.join(rd, "verdict.json"))) if os.path.exists(os.path.join(rd, "verdict.json")) else {}
        h = json.load(open(os.path.join(rd, "habitat.json"))) if os.path.exists(os.path.join(rd, "habitat.json")) else {}
        mp4 = os.path.join(rd, f"{os.path.basename(rd)}.mp4")
        ok = v.get("verdict") == "VALID" and h.get("verdict") == "VALID" and os.path.exists(mp4)
        if not ok:
            msg = f"[b6] {act} {rd}: NIE osądzony (judge={v.get('verdict')} habitat={h.get('verdict')} mp4={os.path.exists(mp4)})"
            if args.allow_partial:
                print(msg + " — POMIJAM", file=sys.stderr); continue
            print(msg + " — ODMOWA (B6: tylko próby osądzone)", file=sys.stderr); sys.exit(2)
        items.append((act, rd, mp4))
    if not items:
        print("[b6] brak osądzonych aktów", file=sys.stderr); sys.exit(2)

    vw = cv2.VideoWriter(args.out, cv2.VideoWriter_fourcc(*"mp4v"), args.fps, (W, H))

    def hold(img, secs):
        for _ in range(int(secs * args.fps)):
            vw.write(img)

    # karta tytułowa + DWA dyskleimery §1c (globalnie, raz)
    acts_lbl = " · ".join(a for a, _, _ in items)
    hold(_text_card(cv2, ["LiquidPatrol DEMO-B", f"acts: {acts_lbl}", "certified safety layer — behavior given detection"],
                    sub="SITL / TRL 2–3 — not an operational system"), 4.0)
    hold(_text_card(cv2, _wrap(cv2, S["pl.detection_channel"], 0.9, W - 160),
                    sub="mandatory disclaimer (ANEKS_D6 §1c)"), 4.0)
    hold(_text_card(cv2, _wrap(cv2, S["pl.live_perception"], 0.75, W - 160),
                    sub="mandatory disclaimer (ANEKS_D6 §1c)"), 4.5)

    total = 0
    for act, rd, mp4 in items:
        hold(_text_card(cv2, [S["pl.cut"], f"ACT {act}"], sub=os.path.basename(rd)), 2.5)
        cap = cv2.VideoCapture(mp4)
        while True:
            ret, fr = cap.read()
            if not ret:
                break
            if (fr.shape[1], fr.shape[0]) != (W, H):
                fr = cv2.resize(fr, (W, H))
            vw.write(fr); total += 1
        cap.release()
    hold(_text_card(cv2, ["END — DEMO-B", "detection: GT-fed (idealized); live perception characterized separately"],
                    sub="LiquidPatrol"), 3.0)
    vw.release()
    dur = None
    try:
        dur = round(os.path.getsize(args.out) / 1e6, 2)
    except Exception:
        pass
    print(f"[b6] montage.mp4 → {args.out} ({dur} MB) | akty={acts_lbl} | klatek_ciała={total}")


if __name__ == "__main__":
    main()
