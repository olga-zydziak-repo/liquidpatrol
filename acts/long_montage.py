#!/usr/bin/env python3
"""acts/long_montage.py — PROMPT_D_U2R §7: montaż DŁUGI z prób OSĄDZONYCH.

≥90 s łącznie, każda faza ≥3 s czasu ekranowego, sim_t w rogu, kompresje czasu JAWNE (etykieta ×N),
wyłącznie klatki biegów osądzonych (verdict VALID ∧ habitat VALID). Pełne łuki obu aktów.
HUD: box-on-silhouette „GT-fed track (admitted)" (U2R §6, rozjazd ≤0.5 m przez slaving) + pasek MODE
+ token; plansze §1c. Marker z trace intr_ned (== pozycja modelu, slaving).

Uruchom: python3 -m acts.long_montage --out results/demo/DEMO_B_A1_A3_v3.mp4 \
         A1:results/demo/A1_v3/proba_1 A3:results/demo/rehearsal/A3/v3_1
"""
from __future__ import annotations
import argparse, glob, hashlib, json, math, os, sys
import numpy as np

W, H = 1280, 720


def _load(f):
    import cv2
    a = np.load(f)
    return cv2.cvtColor(a, cv2.COLOR_RGB2BGR) if a.ndim == 3 else cv2.cvtColor(a, cv2.COLOR_GRAY2BGR)


def phases_A1(rec, tsec):
    ts = [tsec(r) for r in rec]
    lock = next((tsec(r) for r in rec if r.get("mode") == "OBSERVE"), None)
    if lock is None:
        return [("patrol", ts[0], ts[-1])]
    after = [tsec(r) for r in rec if tsec(r) > lock and r.get("mode") != "OBSERVE"]
    unlock = after[0] if after else ts[-1]
    appr = max(ts[0], lock - 3.0)
    return [("takeoff / patrol", ts[0], appr), ("intruder approach", appr, lock),
            ("ENTRY / REFUSE / OBSERVE", lock, unlock), ("RTL / land", unlock, ts[-1])]


def phases_A3(rec, tsec):
    ts = [tsec(r) for r in rec]
    degr = next((tsec(r) for r in rec if r.get("reason") == "POS_DEGRADED"), None)
    desc = next((tsec(r) for r in rec if r.get("descending")), None)
    tdn = next((tsec(r) for r in rec if (-r["pos"][2]) < 1.0), None)
    degr = degr or ts[len(ts) // 4]; desc = desc or degr; tdn = tdn or ts[-1]
    return [("GPS nominal", ts[0], degr), ("REFUSE · POS_DEGRADED", degr, desc),
            ("controlled descent", desc, tdn), ("touchdown (contained)", tdn, ts[-1])]


def main():
    import cv2
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from acts.hud_render import make_proj, _enu_intr, _ticks, _tsec, gate_state
    from acts.build_clip import _text_card, _wrap
    from tools.gen_subtitles import STRINGS
    S = STRINGS["en"]

    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--fps", type=float, default=12.0)
    ap.add_argument("--min-total", type=float, default=92.0)
    ap.add_argument("--min-phase", type=float, default=3.5)
    args = ap.parse_args()

    items = []
    for spec in args.runs:
        act, rd = spec.split(":", 1)
        v = json.load(open(os.path.join(rd, "verdict.json")))
        h = json.load(open(os.path.join(rd, "habitat.json")))
        if not (v.get("verdict") == "VALID" and h.get("verdict") == "VALID"):
            print(f"[long] {act} {rd} NIE VALID — ODMOWA (§7 tylko osądzone)", file=sys.stderr); sys.exit(2)
        items.append((act, rd))

    vw = cv2.VideoWriter(args.out, cv2.VideoWriter_fourcc(*"mp4v"), args.fps, (W, H))

    def hold(img, secs):
        for _ in range(max(1, int(secs * args.fps))):
            vw.write(img)

    DATUM = (70, 90, 235)  # box-on-silhouette (§6) — czerwony (odróżnia od plansz)

    def draw(img, act, r, ip, rng, tok, sim_t, phase, xn):
        MODE, sub = gate_state(r)
        if act == "A3" and r.get("descending"):
            MODE, sub = "LAND", None
        col = {"PATROL": (200, 200, 200), "OBSERVE": (120, 200, 120), "REFUSE": (70, 90, 235),
               "LAND": (60, 180, 235)}.get(MODE, (200, 200, 200))
        # U2R-2 §6: BOX-ON-SILHOUETTE (intruz ciemny/kontrastowy widoczny; rozjazd toru ≤0.5m slaving +
        # naprawa E/N). Box wokół sylwetki + etykieta „GT-fed track (admitted)". Kolor czerwony.
        if ip is not None:
            u, v = int(ip[0]), int(ip[1]); hw = 48
            cv2.rectangle(img, (u - hw, v - 30), (u + hw, v + 30), DATUM, 2, cv2.LINE_AA)
            cv2.putText(img, f"GT-fed track (admitted) · {rng:.1f} m", (u - hw, v - 38),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.46, DATUM, 1, cv2.LINE_AA)
        # MODE bar
        cv2.rectangle(img, (18, 16), (270, 52), (0, 0, 0), -1)
        cv2.rectangle(img, (18, 16), (30, 52), col, -1)
        cv2.putText(img, MODE + (f" · {sub}" if sub else ""), (40, 41), cv2.FONT_HERSHEY_SIMPLEX, 0.62, col, 2, cv2.LINE_AA)
        if tok:
            cv2.putText(img, tok, (40, 76), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (120, 200, 120), 2, cv2.LINE_AA)
        # phase label (lower-left)
        cv2.putText(img, phase, (24, H - 26), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (235, 235, 235), 2, cv2.LINE_AA)
        # sim_t corner (upper-right) + ×N
        cv2.putText(img, f"sim t = {sim_t:6.1f} s", (W - 250, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 210, 255), 2, cv2.LINE_AA)
        if xn >= 1.5:
            cv2.putText(img, f"time x{xn:.0f}", (W - 250, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (120, 200, 255), 2, cv2.LINE_AA)
        cv2.putText(img, f"ACT {act} · world v3.1 · from trace.jsonl (judged VALID)", (24, H - 54),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (150, 150, 160), 1, cv2.LINE_AA)
        return img

    # tytuł + §1c
    hold(_text_card(cv2, ["LiquidPatrol DEMO-B", "acts: A1 · A3 (world v3.1)", "certified safety layer — behavior given detection"],
                    sub="SITL / TRL 2-3 — not an operational system"), 3.5)
    hold(_text_card(cv2, _wrap(cv2, S["pl.detection_channel"], 0.8, W - 160), sub="mandatory disclaimer (ANEKS_D6 §1c)"), 3.5)
    hold(_text_card(cv2, _wrap(cv2, S["pl.live_perception"], 0.7, W - 160), sub="mandatory disclaimer (ANEKS_D6 §1c)"), 3.5)

    prov = {"script_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest(), "acts": {}, "cutlist": []}

    # pierwsze przejście: policz screen-durations by osiągnąć min-total
    plans = []
    for act, rd in items:
        proj = make_proj(act)
        fs = sorted(glob.glob(os.path.join(rd, "frames", "f_*.npy")))
        ticks = _ticks(os.path.join(rd, "trace.jsonl"))
        rec = [r for r in ticks if "pos" in r and (isinstance(r.get("t"), (int, float)) or isinstance(r.get("tick"), (int, float)))]
        T = np.array([_tsec(r) for r in rec])
        events = [r for r in ticks if r.get("event") in ("token_issued", "token_consumed")]
        # frame -> time (liniowo na pełny łuk trace — kalibracja drona zawodzi w v3, buildings w niebie)
        t_lo, t_hi = float(T.min()), float(T.max())
        ftime = [t_lo + (i / max(len(fs) - 1, 1)) * (t_hi - t_lo) for i in range(len(fs))]
        phs = (phases_A1 if act == "A1" else phases_A3)(rec, _tsec)
        plans.append((act, rd, proj, fs, rec, T, events, ftime, phs))

    # rozdziel czas: każda faza screen = clamp(min_phase, real*0.45, 14); potem skaluj do min-total
    all_phase_screens = []
    for (_, _, _, _, _, _, _, _, phs) in plans:
        for (name, a, b) in phs:
            all_phase_screens.append(max(args.min_phase, min(14.0, (b - a) * 0.45)))
    foot_total = sum(all_phase_screens)
    scale = max(1.0, args.min_total / max(foot_total, 1e-6))
    it = iter(all_phase_screens)

    def frame_at(fs, ftime, t):
        i = int(np.argmin([abs(x - t) for x in ftime]))
        return fs[i]

    for (act, rd, proj, fs, rec, T, events, ftime, phs) in plans:
        hold(_text_card(cv2, ["— separate boot —", f"ACT {act}"], sub=os.path.basename(rd)), 2.0)
        for (name, a, b) in phs:
            screen = next(it) * scale
            real = b - a
            xn = real / max(screen, 1e-6)
            nout = max(1, int(screen * args.fps))
            prov["cutlist"].append({"act": act, "phase": name, "sim_t": [round(a, 1), round(b, 1)],
                                    "screen_s": round(screen, 1), "x": round(xn, 1)})
            for k in range(nout):
                st = a + (b - a) * (k / max(nout - 1, 1))          # sim_t interpolowany
                f = frame_at(fs, ftime, st)
                r = rec[int(np.argmin(np.abs(T - st)))]
                ip, rng = None, 0.0
                if act == "A1" and r.get("intr_ned"):
                    ip = proj(_enu_intr(r["intr_ned"]))
                    rng = math.sqrt(sum((r["intr_ned"][j] - r["pos"][j]) ** 2 for j in range(3)))
                tok = None
                for e in events:
                    if abs(_tsec(e) - st) < max(real / nout, 0.6):
                        tok = "TOKEN ISSUED" if e["event"] == "token_issued" else "TOKEN CONSUMED"
                vw.write(draw(_load(f).copy(), act, r, ip, rng, tok, st, name, xn))
        sha = hashlib.sha256("".join(os.path.basename(x) for x in fs).encode()).hexdigest()[:16]
        prov["acts"][act] = {"run_dir": rd, "n_frames": len(fs), "frames_sha16": sha}

    hold(_text_card(cv2, ["END — DEMO-B (world v3.1)", "detection: GT-fed; markers = certified GT track"], sub="LiquidPatrol"), 3.0)
    vw.release()
    json.dump(prov, open(os.path.splitext(args.out)[0] + "_manifest.json", "w"), indent=2, ensure_ascii=False)
    dur = None
    try:
        import subprocess  # noqa
    except Exception:
        pass
    print(f"[long] {args.out} ({round(os.path.getsize(args.out)/1e6,2)} MB) scale={scale:.2f}")
    for c in prov["cutlist"]:
        print(f"  {c['act']} {c['phase']}: {c['screen_s']}s (x{c['x']})")


if __name__ == "__main__":
    main()
