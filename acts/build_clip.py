#!/usr/bin/env python3
"""acts/build_clip.py — montaż klipu PRÓBY (ANEKS_D6 §4): frames_manifest.json + subtitles.vtt (--lang EN)
+ proba_N.mp4. TYLKO dla biegów OSĄDZONYCH (verdict VALID ∧ habitat VALID) — sprawdzane przed montażem.

Klip = karty otwierające (dyskleimery §1c OBOWIĄZKOWE + PROVED) → klatki filmowe z dolnym paskiem
(segment/zdarzenie z subtitles.vtt) i trwałą stopką „GT-fed" → karty zamykające (MEASURED + TRL).
Renderowane cv2 (brak ffmpeg/imageio). Klatki .npy (RGB) z r02/capture_frame.

Uruchom: python3 -m acts.build_clip <run_dir> <act> [--fps 8] [--out proba.mp4] [--force-unjudged]
"""
from __future__ import annotations
import argparse, glob, json, os, sys
import numpy as np

W, H = 1280, 720


def _cv2():
    import cv2
    return cv2


def _text_card(cv2, lines, sub=None, bg=(18, 18, 22), fg=(235, 235, 235), accent=(120, 200, 255)):
    img = np.zeros((H, W, 3), np.uint8); img[:] = bg
    y = H // 2 - 30 * (len(lines) - 1)
    for i, ln in enumerate(lines):
        scale = 1.1 if i == 0 else 0.8
        col = accent if i == 0 else fg
        th = 2 if i == 0 else 1
        (tw, _), _ = cv2.getTextSize(ln, cv2.FONT_HERSHEY_SIMPLEX, scale, th)
        cv2.putText(img, ln, ((W - tw) // 2, y), cv2.FONT_HERSHEY_SIMPLEX, scale, col, th, cv2.LINE_AA)
        y += 52
    if sub:
        (tw, _), _ = cv2.getTextSize(sub, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
        cv2.putText(img, sub, ((W - tw) // 2, H - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 160), 1, cv2.LINE_AA)
    return img


def _wrap(cv2, text, scale, max_w):
    words = text.split(); lines = []; cur = ""
    for w in words:
        t = (cur + " " + w).strip()
        (tw, _), _ = cv2.getTextSize(t, cv2.FONT_HERSHEY_SIMPLEX, scale, 1)
        if tw > max_w and cur:
            lines.append(cur); cur = w
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines


def _overlay_lower_third(cv2, frame, banner, footer):
    img = frame.copy()
    ov = img.copy()
    cv2.rectangle(ov, (0, H - 130), (W, H), (0, 0, 0), -1)
    cv2.addWeighted(ov, 0.55, img, 0.45, 0, img)
    y = H - 95
    for ln in _wrap(cv2, banner, 0.7, W - 60)[:2]:
        cv2.putText(img, ln, (30, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
        y += 34
    cv2.putText(img, footer, (30, H - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 200, 255), 1, cv2.LINE_AA)
    return img


def _load_frame(cv2, path):
    a = np.load(path)
    if a.ndim == 2:
        a = cv2.cvtColor(a, cv2.COLOR_GRAY2BGR)
    elif a.shape[2] == 3:
        a = cv2.cvtColor(a, cv2.COLOR_RGB2BGR)   # kamera gz publikuje RGB
    if (a.shape[1], a.shape[0]) != (W, H):
        a = cv2.resize(a, (W, H))
    return a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir"); ap.add_argument("act", choices=["A1", "A2", "A3"])
    ap.add_argument("--fps", type=float, default=8.0)
    ap.add_argument("--out", default=None)
    ap.add_argument("--force-unjudged", action="store_true", help="pomiń bramkę VALID (tylko debug)")
    args = ap.parse_args()
    cv2 = _cv2()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, root)

    # BRAMKA: montaż TYLKO z biegów osądzonych (B6 §1c). verdict.json ∧ habitat.json = VALID.
    vp = os.path.join(args.run_dir, "verdict.json"); hp = os.path.join(args.run_dir, "habitat.json")
    v = json.load(open(vp)) if os.path.exists(vp) else {}
    h = json.load(open(hp)) if os.path.exists(hp) else {}
    judged_ok = v.get("verdict") == "VALID" and h.get("verdict") == "VALID"
    if not judged_ok and not args.force_unjudged:
        print(f"[clip] ODMOWA: bieg NIE osądzony VALID (judge={v.get('verdict')} habitat={h.get('verdict')}) "
              f"— montaż tylko z prób osądzonych (B6)", file=sys.stderr)
        sys.exit(2)

    # subtitles.vtt + planszas.json (gen_subtitles, --lang en)
    from tools import gen_subtitles as G
    spec = os.path.join(root, "acts", f"{args.act}_spec.yaml")
    r = G.generate(os.path.join(args.run_dir, "trace.jsonl"), spec, args.run_dir, lang="en")
    planszas = r["planszas"]; segs = r["segments"]; found = r["found"]

    frames = sorted(glob.glob(os.path.join(args.run_dir, "frames", "f_*.npy")))
    # frames_manifest.json: klatki + przybliżony sim-time (1 fps grabber → indeks≈sekundy od 1. klatki
    # wyrównany do 1. segmentu roszczenia; sync przybliżony — rygor w planszach PROVED/MEASURED, nie w sync).
    claim_segs = [s for s in segs if s["kind"] == "claim"]
    t0 = claim_segs[0]["t_start"] if claim_segs else (segs[0]["t_start"] if segs else 0.0)
    fman = {"act": args.act, "n_frames": len(frames), "grabber_hz": 1.0,
            "note": "sim-time przybliżony (grabber ~1 fps); event/segment sync ilustracyjny",
            "frames": [{"file": os.path.basename(f), "idx": i, "sim_t_approx": round(t0 + i, 2)}
                       for i, f in enumerate(frames)]}
    json.dump(fman, open(os.path.join(args.run_dir, "frames_manifest.json"), "w"), indent=2, ensure_ascii=False)

    out = args.out or os.path.join(args.run_dir, f"{os.path.basename(args.run_dir)}.mp4")
    vw = cv2.VideoWriter(out, cv2.VideoWriter_fourcc(*"mp4v"), args.fps, (W, H))

    def hold(img, secs):
        for _ in range(int(secs * args.fps)):
            vw.write(img)

    footer = "GT-fed detector (idealized) — certified-layer behavior, not live perception"
    # karty otwierające: dyskleimery §1c NAJPIERW (SR-M2), potem PROVED + tytuł
    disc = [p for p in planszas if p["kind"] in ("DETECTION_CHANNEL", "LIVE_PERCEPTION")]
    for p in disc:
        hold(_text_card(cv2, _wrap(cv2, p["text"], 0.85, W - 160), sub="mandatory disclaimer (ANEKS_D6 §1c)"), 3.5)
    proved = next((p for p in planszas if p["kind"] == "PROVED"), None)
    if proved:
        hold(_text_card(cv2, proved["text"].split("\n"), sub=f"DEMO-B {args.act}"), 3.5)

    # ciało: klatki z dolnym paskiem (segment aktywny wg sim_t_approx)
    def banner_at(t):
        lab = ""
        for s in segs:
            a, b = s.get("t_start"), s.get("t_end")
            if a is not None and b is not None and a <= t <= b:
                lab = s["label"]
        return lab or f"DEMO-B {args.act}"
    if frames:
        for i, f in enumerate(frames):
            fr = _load_frame(cv2, f)
            vw.write(_overlay_lower_third(cv2, fr, banner_at(t0 + i), footer))
    else:
        hold(_text_card(cv2, [f"DEMO-B {args.act}", "(no film frames captured)"], sub=footer), 2.0)

    # karty zamykające: MEASURED + statyczne obowiązkowe (OPERATOR/TRL/CONTRAST)
    for kind in ("MEASURED", "OPERATOR", "PER_ADMISSION", "AUTHORITY_GATING", "CONTRAST", "TRL"):
        p = next((x for x in planszas if x["kind"] == kind), None)
        if p:
            hold(_text_card(cv2, _wrap(cv2, p["text"].replace("\n", " • "), 0.7, W - 160)), 3.0)
    vw.release()
    dur = None
    try:
        import os as _o; dur = round(_o.path.getsize(out) / 1e6, 2)
    except Exception:
        pass
    print(f"[clip] {args.act} {os.path.basename(args.run_dir)}: {len(frames)} klatek → {out} ({dur} MB) "
          f"| planszas={len(planszas)} (disc={len(disc)}) | judged={judged_ok}")


if __name__ == "__main__":
    main()
