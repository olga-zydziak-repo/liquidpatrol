#!/usr/bin/env python3
"""acts/hud_render.py — PROMPT_D_U1R: HUD post-produkcyjny na klatkach osądzonych prób v1.0.

Wyłącznie post-produkcja (§1): żadnych nowych biegów/pomiarów. Nakłada na ISTNIEJĄCE klatki filmowe
(A1 proba_1, A3 proba_1) HUD wyprowadzony WYŁĄCZNIE z trace v2:
  §2a marker intruza: NED z trace → piksel kamery filmowej (rzut pinhole, poza+intrinsics ze świata v1.0),
      diament + range [m] + etykieta "GT-fed track (admitted)";
  §2b pasek MODE (PATROL/REFUSE/OBSERVE/LAND) ze stanu bramy w trace;
  §2c status tokenu (ISSUED/CONSUMED) przy zdarzeniach trace;
  §2d plansze §1c + napisy EN bez zmian (współdzielone z montażem).

Rzut (do raportu §5): P_cam = R(yaw,pitch)^T · (P_enu − C);  u = cx − fx·Y/X,  v = cy − fy·Z/X;
  fx = (W/2)/tan(hfov/2), fy = fx;  ENU = [E,N,U] = [ned_E, ned_N, −ned_D].
Frame→time: kalibracja przez detekcję drona (najciemniejszy piksel w paśmie nieba) ↔ rzut drona z trace
  (least-squares t=t0+dt·i). „nie na oko" — walidacja geometryczna (reprojekcja drona), §3.

Uruchom: python3 -m acts.hud_render --out results/demo/DEMO_B_A1_A3_HUD.mp4
"""
from __future__ import annotations
import argparse, glob, hashlib, json, math, os, sys
import numpy as np
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from common import frames as _frames

W, H = 1280, 720

# --- kamera filmowa (world_demo_A1/A3.sdf v1.0; film_cam FREEZE ANEKS_D2) ---
CAMS = {
    "A1": dict(C=[11.0, -13.0, 11.5], pitch=-0.0209, yaw=2.0032),   # U2R-2 §3: kamera v3.1 (podniesiona)
    "A3": dict(C=[14.0, -18.0, 7.0], pitch=-0.1649, yaw=1.6263),   # world_demo_A3.sdf film_cam (aim (13,0,4))
}
HFOV = 1.20
FX = (W / 2) / math.tan(HFOV / 2); FY = FX; CXp, CYp = W / 2, H / 2


def _R(yaw, pitch):
    cz, sz, cy, sy = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch)
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    return Rz @ Ry


def _enu(ned):
    # DRON: mav.pos = NED [N,E,D] → ENU. PROMPT_K1 §A: przez common.frames (bez lokalnego swapu).
    return np.array(_frames.ned2enu(ned), float)


def _enu_intr(ned):
    # INTRUZ: trace intr_ned = DRV [E,N,-U] → ENU (bez zamiany E/N). PROMPT_K1 §A: przez common.frames.
    return np.array(_frames.drv2enu(ned), float)


def make_proj(act):
    cam = CAMS[act]; C = np.array(cam["C"]); Rwc = _R(cam["yaw"], cam["pitch"])

    def proj(P_enu):
        Pc = Rwc.T @ (np.array(P_enu) - C); X, Y, Z = Pc
        if X <= 0.05:
            return None
        return np.array([CXp - FX * (Y / X), CYp - FY * (Z / X)])
    return proj


def _load(f):
    import cv2
    a = np.load(f)
    return cv2.cvtColor(a, cv2.COLOR_RGB2BGR) if a.ndim == 3 else cv2.cvtColor(a, cv2.COLOR_GRAY2BGR)


def _ticks(path):
    out = []
    for ln in open(path):
        ln = ln.strip()
        if not ln:
            continue
        try:
            d = json.loads(ln)
        except Exception:
            continue
        if isinstance(d, dict):
            out.append(d)
    return out


def _tsec(r):
    return float(r["t"]) if isinstance(r.get("t"), (int, float)) else float(r.get("tick", 0)) * 0.05


def calibrate_time(fs, ticks, proj):
    """A1: frame→time przez detekcję drona (ciemny piksel w niebie) ↔ rzut drona z trace (grid t0,dt)."""
    import cv2
    rec = [r for r in ticks if "pos" in r and (isinstance(r.get("t"), (int, float)) or isinstance(r.get("tick"), (int, float)))]
    T = np.array([_tsec(r) for r in rec])

    def dproj(t):
        r = rec[int(np.argmin(np.abs(T - t)))]; return proj(_enu(r["pos"]))
    det = []
    for i, f in enumerate(fs):
        g = cv2.cvtColor(_load(f), cv2.COLOR_BGR2GRAY); band = g[40:195, :]
        if band.min() > 190:
            continue
        p = np.unravel_index(band.argmin(), band.shape); det.append((i, np.array([p[1], p[0] + 40])))
    best = None
    for t0 in np.arange(0, 20, 0.5):
        for dt in np.arange(0.8, 1.9, 0.05):
            c = 0.0
            for i, px in det:
                q = dproj(t0 + dt * i)
                c += 1e6 if q is None else float(np.hypot(*(q - px)))
            if best is None or c < best[0]:
                best = (c, t0, dt)
    return best[1], best[2], (best[0] / max(len(det), 1)), len(det)


def gate_state(r):
    """MODE + token z rekordu trace."""
    mode = r.get("mode"); reason = r.get("reason")
    if r.get("descending") or (r.get("decision") == "ALLOW" and r.get("reason") == "POS_DEGRADED"):
        pass
    if reason == "POS_DEGRADED":
        return "REFUSE", "POS_DEGRADED"
    if reason == "NO_AUTH":
        return "REFUSE", "NO_AUTH"
    if mode == "OBSERVE":
        return "OBSERVE", None
    if mode == "PATROL" or mode is None:
        return "PATROL", None
    return str(mode), None


def draw_hud(img, act, r, ip, rng, token_txt):
    import cv2
    MODE, sub = gate_state(r)
    col = {"PATROL": (200, 200, 200), "OBSERVE": (120, 200, 120),
           "REFUSE": (70, 90, 235), "LAND": (60, 180, 235)}.get(MODE, (200, 200, 200))
    if act == "A3" and (r.get("descending")):
        MODE, col = "LAND", (60, 180, 235)
    # datum toru GT (ANEKS_U1R §2b): NIE box detekcji — diament + leader line + "GT track · range".
    # Styl instrumentowy, kolor odrębny od plansz (cyan-teal). Scenografia (model) może się rozjeżdżać.
    if ip is not None:
        u, v = int(ip[0]), int(ip[1])
        DATUM = (225, 205, 70)   # BGR cyan-teal (odrębny od plansz amber/niebieski)
        lx, ly = u + 52, v - 46  # koniec leader line / kotwica etykiety
        cv2.drawMarker(img, (u, v), DATUM, cv2.MARKER_DIAMOND, 24, 2, cv2.LINE_AA)
        cv2.line(img, (u + 12, v - 12), (lx - 4, ly + 4), DATUM, 1, cv2.LINE_AA)
        cv2.putText(img, f"GT track · {rng:.1f} m", (lx, ly), cv2.FONT_HERSHEY_SIMPLEX, 0.5, DATUM, 1, cv2.LINE_AA)
    # pasek MODE (§2b) — górny lewy
    cv2.rectangle(img, (18, 16), (250, 52), (0, 0, 0), -1)
    cv2.rectangle(img, (18, 16), (30, 52), col, -1)
    label = MODE + (f" · {sub}" if sub else "")
    cv2.putText(img, label, (40, 41), cv2.FONT_HERSHEY_SIMPLEX, 0.62, col, 2, cv2.LINE_AA)
    # status tokenu (§2c)
    if token_txt:
        cv2.putText(img, token_txt, (40, 76), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (120, 200, 120), 2, cv2.LINE_AA)
    # stopka prowieniencji
    cv2.putText(img, f"ACT {act} · film_cam (v1.0) · HUD from trace.jsonl", (20, H - 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, (150, 150, 160), 1, cv2.LINE_AA)
    return img


def legend_banner(img):
    """ANEKS_U1R §2b: raz na akt (intro) — legenda datum toru. Kolor datum = cyan-teal."""
    import cv2
    o = img.copy()
    cv2.rectangle(o, (0, H - 96), (W, H - 40), (0, 0, 0), -1)
    cv2.addWeighted(o, 0.5, img, 0.5, 0, img)
    DATUM = (225, 205, 70)
    cv2.drawMarker(img, (44, H - 68), DATUM, cv2.MARKER_DIAMOND, 20, 2, cv2.LINE_AA)
    cv2.putText(img, "certified GT track - the shield's input;  airframe model is decorative",
                (66, H - 62), cv2.FONT_HERSHEY_SIMPLEX, 0.56, (225, 205, 70), 1, cv2.LINE_AA)
    return img


def render_act(act, run_dir, control_out=None):
    import cv2
    proj = make_proj(act)
    fs = sorted(glob.glob(os.path.join(run_dir, "frames", "f_*.npy")))
    ticks = _ticks(os.path.join(run_dir, "trace.jsonl"))
    rec = [r for r in ticks if "pos" in r and (isinstance(r.get("t"), (int, float)) or isinstance(r.get("tick"), (int, float)))]
    T = np.array([_tsec(r) for r in rec])
    events = [r for r in ticks if r.get("event") in ("token_issued", "token_consumed")]
    # time map
    if act == "A1":
        t0, dt, err, ndet = calibrate_time(fs, ticks, proj)
        cal = f"drone-fit t0={t0:.1f} dt={dt:.2f} err={err:.0f}px n={ndet}"
    else:
        # A3: brak intruza; mapowanie liniowe na pełen trace
        t0, dt = float(T.min()), (float(T.max()) - float(T.min())) / max(len(fs) - 1, 1)
        cal = f"linear t0={t0:.1f} dt={dt:.2f} (A3: no intruder marker)"

    def rec_at(t):
        return rec[int(np.argmin(np.abs(T - t)))]
    frames = []
    controls = {}
    for i, f in enumerate(fs):
        t = t0 + dt * i
        r = rec_at(t)
        ip, rng = None, 0.0
        if act == "A1" and r.get("intr_ned"):
            ip = proj(_enu_intr(r["intr_ned"]))
            rng = math.sqrt(sum((r["intr_ned"][k] - r["pos"][k]) ** 2 for k in range(3)))
        tok = None
        for e in events:
            if abs(_tsec(e) - t) < 1.2:
                tok = "TOKEN ISSUED" if e["event"] == "token_issued" else "TOKEN CONSUMED"
        img = draw_hud(_load(f).copy(), act, r, ip, rng, tok)
        frames.append(img)
        # klatki kontrolne §3
        MODE, _ = gate_state(r)
        if act == "A1" and "preentry" not in controls and MODE == "PATROL" and r.get("intr_ned") and r["intr_ned"][2] > -6:
            controls["preentry"] = (i, img.copy())
        if act == "A1" and MODE == "OBSERVE":
            controls["observe"] = (i, img.copy())
        if act == "A3" and (r.get("descending") or (-r["pos"][2]) < 1.0):
            controls["touchdown"] = (i, img.copy())
    if control_out:
        for k, (i, im) in controls.items():
            cv2.imwrite(os.path.join(control_out, f"control_{act}_{k}.png"), im)
    return frames, cal, [os.path.basename(x) for x in fs]


def main():
    import cv2
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results/demo/DEMO_B_A1_A3_HUD.mp4")
    ap.add_argument("--fps", type=float, default=8.0)
    ap.add_argument("--control-dir", default="results/demo/hud_control")
    args = ap.parse_args()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, root)
    from acts.build_clip import _text_card, _wrap
    from tools.gen_subtitles import STRINGS
    S = STRINGS["en"]
    os.makedirs(args.control_dir, exist_ok=True)

    ACTS = [("A1", "results/demo/A1/proba_1"), ("A3", "results/demo/rehearsal/A3/proba_1")]
    vw = cv2.VideoWriter(args.out, cv2.VideoWriter_fourcc(*"mp4v"), args.fps, (W, H))

    def hold(img, secs):
        for _ in range(int(secs * args.fps)):
            vw.write(img)

    prov = {"script_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest(),
            "camera": CAMS, "hfov": HFOV, "acts": {}}
    # §2d plansze §1c (bez zmian)
    hold(_text_card(cv2, ["LiquidPatrol DEMO-B", "acts: A1 · A3", "HUD overlay — from trace.jsonl"],
                    sub="SITL / TRL 2-3 — not an operational system"), 3.0)
    hold(_text_card(cv2, _wrap(cv2, S["pl.detection_channel"], 0.8, W - 160), sub="mandatory disclaimer (ANEKS_D6 §1c)"), 3.5)
    hold(_text_card(cv2, _wrap(cv2, S["pl.live_perception"], 0.7, W - 160), sub="mandatory disclaimer (ANEKS_D6 §1c)"), 3.5)
    for act, rd in ACTS:
        frames, cal, fnames = render_act(act, rd, args.control_dir)
        hold(_text_card(cv2, ["— separate boot —", f"ACT {act}"], sub=os.path.basename(rd)), 2.0)
        _lg = int(2.2 * args.fps) if act == "A1" else 0   # §2b: legenda datum tylko gdzie jest marker (A1)
        for k, fr in enumerate(frames):
            vw.write(legend_banner(fr) if k < _lg else fr)
        if frames:
            for _ in range(int(1.0 * args.fps)):
                vw.write(frames[-1])
        sha = hashlib.sha256("".join(fnames).encode()).hexdigest()[:16]
        prov["acts"][act] = {"run_dir": rd, "n_frames": len(fnames), "frames_sha16": sha, "time_calibration": cal}
    hold(_text_card(cv2, ["END — DEMO-B", "detection: GT-fed; HUD markers are the GT track projected"], sub="LiquidPatrol"), 2.5)
    vw.release()
    json.dump(prov, open(os.path.splitext(args.out)[0] + "_manifest.json", "w"), indent=2, ensure_ascii=False)
    print(f"[hud] {args.out}  ({round(os.path.getsize(args.out)/1e6,2)} MB)")
    for a, d in prov["acts"].items():
        print(f"  {a}: {d['n_frames']} frames · {d['time_calibration']}")
    print(f"  control frames → {args.control_dir}/")


if __name__ == "__main__":
    main()
