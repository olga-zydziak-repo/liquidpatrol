#!/usr/bin/env python3
"""acts/anim_montage.py — DEMO-B B6: montaż DANE-DRIVEN z prób OSĄDZONYCH (VALID).

Zamiast statycznego ujęcia film_cam (fixed wide, ANEKS_D2 — dron sub-pikselowy), renderuje ANIMACJĘ
TOP-DOWN z RZECZYWISTEGO trace.jsonl próby: pozycja drona + intruza w czasie, tryb (PATROL/OBSERVE),
zdarzenia maszyny stanów (ENTRY, REFUSE(NO_AUTH), token→OBSERVE; A3: POS_DEGRADED→descent→touchdown).
Ruch prawdziwy (dane próby), zero zmiany frozen świata, zero re-runu. Plansze §1c zachowane (krótsze).

Bramka: verdict.json ∧ habitat.json = VALID (jak montage_b6). Wyjście mp4v → (opcj.) re-enc H.264.
Uruchom: python3 -m acts.anim_montage --out results/demo/DEMO_B_anim.mp4 \
         A1:results/demo/A1/proba_1 A3:results/demo/rehearsal/A3/proba_1
"""
from __future__ import annotations
import argparse, json, math, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

W, H = 1280, 720
BG = "#111111"; FG = "#e8e8e8"; ACCENT = "#ffcf87"; DRONE = "#5b9bd5"; INTR = "#e06666"; OK = "#7ac07a"


def _load_ticks(path):
    out = []
    for ln in open(path):
        ln = ln.strip()
        if not ln:
            continue
        try:
            d = json.loads(ln)
        except Exception:
            continue
        # A1 (gate_run_r02): t=sekundy. A3 (gate_run_r03): t="tick" (string), licznik w polu tick.
        if isinstance(d, dict) and "pos" in d and (isinstance(d.get("t"), (int, float)) or isinstance(d.get("tick"), (int, float))):
            out.append(d)
    return out


def _tsec(t):
    """Czas [s]: A1 ma t=sekundy; A3 ma tick (×0.05 s @20 Hz)."""
    if isinstance(t.get("t"), (int, float)):
        return float(t["t"])
    return float(t.get("tick", 0)) * 0.05


def _fig():
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0.06, 0.06, 0.62, 0.88]); ax.set_facecolor(BG)
    for s in ax.spines.values():
        s.set_color("#333333")
    ax.tick_params(colors="#777777", labelsize=8)
    return fig, ax


def _rgb(fig):
    fig.canvas.draw()
    buf = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8)
    img = buf.reshape(fig.canvas.get_width_height()[::-1] + (4,))[:, :, :3]
    import cv2
    return cv2.resize(cv2.cvtColor(img, cv2.COLOR_RGB2BGR), (W, H))


def _panel(fig, lines, y0=0.92):
    for i, (txt, col, sz) in enumerate(lines):
        fig.text(0.70, y0 - i * 0.052, txt, color=col, fontsize=sz, family="monospace", va="top")


def anim_A1(ticks, stride=4):
    """Top-down E(x)–N(y): dron ściga intruza; ENTRY→REFUSE(NO_AUTH)→OBSERVE. Zwraca listę klatek BGR."""
    D = [t for i, t in enumerate(ticks) if i % stride == 0]
    N = [t["pos"][0] for t in ticks]; E = [t["pos"][1] for t in ticks]
    iN = [t["intr_ned"][0] for t in ticks if t.get("intr_ned")]
    iE = [t["intr_ned"][1] for t in ticks if t.get("intr_ned")]
    xlo, xhi = min(E + iE) - 2, max(E + iE) + 2
    ylo, yhi = min(N + iN) - 2, max(N + iN) + 2
    frames = []
    import cv2  # noqa
    for k, t in enumerate(D):
        fig, ax = _fig()
        ax.set_xlim(xlo, xhi); ax.set_ylim(ylo, yhi); ax.set_aspect("equal")
        ax.set_xlabel("East (m)", color="#777"); ax.set_ylabel("North (m)", color="#777")
        # trail (do bieżącego tick w oryg. indeksie)
        gi = ticks.index(t)
        tr0 = max(0, gi - 120)
        ax.plot(E[tr0:gi + 1], N[tr0:gi + 1], color=DRONE, lw=1.2, alpha=0.5)
        dp = t["pos"]; ax.plot(dp[1], dp[0], "o", color=DRONE, ms=11, mec="white", mew=0.6)
        locked = bool(t.get("locked")); mode = t.get("mode"); reason = t.get("reason")
        auth = t.get("auth_ok")
        ip = t.get("intr_ned")
        if ip:
            itr = [x[1] for x in (q.get("intr_ned") for q in ticks[tr0:gi + 1]) if x]
            itn = [x[0] for x in (q.get("intr_ned") for q in ticks[tr0:gi + 1]) if x]
            ax.plot(itr, itn, color=INTR, lw=1.0, alpha=0.4)
            ax.plot(ip[1], ip[0], "^", color=INTR, ms=12, mec="white", mew=0.6)
            rng = math.dist(dp[:2], ip[:2])
            if locked:
                ax.plot([dp[1], ip[1]], [dp[0], ip[0]], "--", color=(OK if mode == "OBSERVE" else ACCENT), lw=1.0)
                ax.add_patch(Circle((ip[1], ip[0]), 2.0, fill=False, ec="#555", ls=":", lw=0.8))
        # panel stanu
        st_mode = mode or "—"
        col_mode = OK if mode == "OBSERVE" else (ACCENT if locked else FG)
        lines = [("DEMO-B  —  ACT A1", ACCENT, 15),
                 (f"t = {_tsec(t):6.1f} s", "#aaaaaa", 12),
                 (f"mode   : {st_mode}", col_mode, 13),
                 (f"target : {'LOCKED' if locked else 'searching'}", (ACCENT if locked else '#888'), 12)]
        if ip:
            lines.append((f"range  : {math.dist(dp[:2], ip[:2]):4.1f} m", FG, 12))
        if locked and reason == "NO_AUTH":
            lines.append(("REFUSE : NO_AUTH", INTR, 14))
            lines.append(("(default-deny; awaiting token)", "#888", 10))
        elif mode == "OBSERVE":
            lines.append(("AUTH   : token OK -> OBSERVE", OK, 13))
            lines.append(("(per-admission authority, B1)", "#888", 10))
        _panel(fig, lines)
        fig.text(0.70, 0.10, "detection: GT-fed (idealized)\nlive perception char. separately\ntop-down from trace.jsonl (real)",
                 color="#666", fontsize=9, family="monospace", va="bottom")
        frames.append(_rgb(fig)); plt.close(fig)
    return frames


def anim_A3(ticks, stride=3):
    """A3 GPS-denied: dron dryfuje, r_est rośnie, POS_DEGRADED→descent→touchdown w R_E."""
    D = [t for i, t in enumerate(ticks) if i % stride == 0]
    N = [t["pos"][0] for t in ticks]; E = [t["pos"][1] for t in ticks]
    R_E = None
    for t in ticks:
        if t.get("margin_R_E") is not None and t.get("r_est") is not None:
            R_E = t["r_est"] + t["margin_R_E"]; break
    R_E = R_E or 32.0
    rad = max(R_E, max(abs(v) for v in N + E) + 3) + 2
    frames = []
    for t in D:
        fig, ax = _fig()
        ax.set_xlim(-rad, rad); ax.set_ylim(-rad, rad); ax.set_aspect("equal")
        ax.set_xlabel("East (m)", color="#777"); ax.set_ylabel("North (m)", color="#777")
        ax.add_patch(Circle((0, 0), R_E, fill=False, ec=OK, ls="--", lw=1.2))
        ax.text(0, R_E, "  containment R_E", color=OK, fontsize=9, va="bottom")
        gi = ticks.index(t)
        ax.plot(E[:gi + 1], N[:gi + 1], color=DRONE, lw=1.2, alpha=0.6)
        dp = t["pos"]; ax.plot(dp[1], dp[0], "o", color=DRONE, ms=11, mec="white", mew=0.6)
        re = t.get("r_est")
        if re:
            ax.add_patch(Circle((dp[1], dp[0]), re, fill=False, ec=ACCENT, ls=":", lw=0.9, alpha=0.8))
        alt = -dp[2]
        desc = bool(t.get("descending")); reason = t.get("reason")
        lines = [("DEMO-B  —  ACT A3", ACCENT, 15),
                 ("GPS-denied containment", "#aaaaaa", 11),
                 (f"t   : {_tsec(t):6.1f} s", "#aaaaaa", 12),
                 (f"alt : {alt:5.1f} m", FG, 12),
                 (f"pos_est unc: {re:4.1f} m" if re else "", ACCENT, 12)]
        if reason == "POS_DEGRADED":
            lines.append(("REFUSE : POS_DEGRADED", INTR, 14))
        if desc:
            lines.append(("ACTION : controlled descent", ACCENT, 13))
            lines.append(("(guarantee containment, R0.3a)", "#888", 10))
        _panel(fig, [l for l in lines if l[0]])
        fig.text(0.70, 0.10, "detection: GT-fed (idealized)\nlive perception char. separately\ntop-down from trace.jsonl (real)",
                 color="#666", fontsize=9, family="monospace", va="bottom")
        frames.append(_rgb(fig)); plt.close(fig)
    return frames


def _card(cv2, lines, sub=None):
    img = np.full((H, W, 3), 17, np.uint8)
    y = H // 2 - 24 * (len(lines) - 1)
    for i, (txt, big) in enumerate(lines):
        sc = 1.3 if big else 0.85
        col = (135, 207, 255) if big and i == 0 else (232, 232, 232)
        (tw, th), _ = cv2.getTextSize(txt, cv2.FONT_HERSHEY_SIMPLEX, sc, 2)
        cv2.putText(img, txt, ((W - tw) // 2, y + i * 52), cv2.FONT_HERSHEY_SIMPLEX, sc, col, 2, cv2.LINE_AA)
    if sub:
        (tw, th), _ = cv2.getTextSize(sub, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
        cv2.putText(img, sub, ((W - tw) // 2, H - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 150), 1, cv2.LINE_AA)
    return img


def main():
    import cv2
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--fps", type=float, default=12.0)
    args = ap.parse_args()

    items = []
    for spec in args.runs:
        act, rd = spec.split(":", 1)
        v = json.load(open(os.path.join(rd, "verdict.json")))
        h = json.load(open(os.path.join(rd, "habitat.json")))
        if not (v.get("verdict") == "VALID" and h.get("verdict") == "VALID"):
            print(f"[anim] {act} {rd} NIE VALID — ODMOWA", file=sys.stderr); sys.exit(2)
        items.append((act, rd))

    vw = cv2.VideoWriter(args.out, cv2.VideoWriter_fourcc(*"mp4v"), args.fps, (W, H))

    def hold(img, secs):
        for _ in range(int(secs * args.fps)):
            vw.write(img)

    acts_lbl = " · ".join(a for a, _ in items)
    hold(_card(cv2, [("LiquidPatrol DEMO-B", True), (f"acts: {acts_lbl}", False),
                     ("certified safety layer - behavior given detection", False)],
               sub="SITL / TRL 2-3 - not an operational system"), 3.5)
    hold(_card(cv2, [("Detection channel: GT-fed (idealized)", False),
                     ("live perception characterized separately", False)],
               sub="mandatory disclaimer (ANEKS_D6 §1c)"), 3.5)
    hold(_card(cv2, [("Authority gating: local HMAC, per-admission", False),
                     ("demonstration, not secure C2 (B1 §1.7)", False)],
               sub="mandatory disclaimer (ANEKS_D6 §1c)"), 3.5)

    for act, rd in items:
        hold(_card(cv2, [("— separate boot —", False), (f"ACT {act}", True)], sub=os.path.basename(rd)), 2.0)
        ticks = _load_ticks(os.path.join(rd, "trace.jsonl"))
        frames = anim_A1(ticks) if act == "A1" else anim_A3(ticks)
        for fr in frames:
            vw.write(fr)
        if frames:
            for _ in range(int(1.2 * args.fps)):  # zamrożenie ostatniej klatki
                vw.write(frames[-1])
    hold(_card(cv2, [("END — DEMO-B", True),
                     ("detection: GT-fed; live perception characterized separately", False)], sub="LiquidPatrol"), 2.5)
    vw.release()
    print(f"[anim] {args.out} ({round(os.path.getsize(args.out)/1e6,2)} MB) akty={acts_lbl}")


if __name__ == "__main__":
    main()
