#!/usr/bin/env python3
"""results/DEMO_C/tools/democ_overlay_v31.py — montaż v3.1 (PROMPT_DEMOC_V31).
NOWY plik; democ_overlay.py v1/_v2/_v3 NIETYKALNE (odtwarzalność wstecz).
Zero bootów: te same ujęcia, nowy overlay WYŁĄCZNIE z istniejących logów.

Dwa tryby:
  • akt1 (§2): tor aktu 1 v2 (Panel z democ_topdown importem, napisy PL 1:1)
    + zwolnienie ×0.5 z plakietką „TEMPO ×0.5" (badge także dla speed<1)
    + sekwencja admisji krok-po-kroku zsynchronizowana z klatkami feedu:
    kroki WYLICZANE z percep_feed/demo/democ_werdykty (nie z ręki):
      s1 = pierwsza klatka epizodu z boxem conf≥0.5 (conf z tej klatki),
      s2/s3 = pierwszy run ≥3 kolejnych klatek fresh (brama admisji k=3:
              centralność+ruch — litera r02/target_channel), ADMISJA→TRACK
              (t_acq sędziego z democ_werdykty.json),
      s4 = przejścia fazy APPROACH/ORBIT z demo.jsonl (sieć płynna prowadzi).
  • 4a|4b (§1): tor aktu 4 v3 (wbudowana kopia Panel4) z polem ETYKIETY
    rozbudowanym do żywego panelu reguły „JAK ROZPOZNAJE": trzy warunki
    (w ruchu / nie zbliża się / nie był <5 m) ✓/✗ per klatka + licznik X.X/12 s
    — dane per klatka z akt4*_sig.jsonl (litera FREEZE_WABIK 475c972e — te
    same rachunki, które policzyły etykietę; czwarty człon koniunkcji dh<18 m
    w obu ujęciach zawsze prawdziwy: dh_max 10.96/15.55 — nie wiąże, więc nie
    jest wyświetlany); flagi/odwołania z akt4*_sig.json (kotwica: rekonstrukcja
    licznika z jsonl odtwarza t_flag/t_revoke — asercja w kodzie, tol. 10 ms
    zaokrągleń jsonl). Napis uczciwości bez zmian.

Użycie:
  democ_overlay_v31.py akt1 <bootdir> <sid> <out_mp4> <segmenty>
  democ_overlay_v31.py 4a|4b <bootdir> <sid> <out_mp4> <segmenty> <sig.json> <sig.jsonl>
"""
import bisect
import json
import math
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bench import scenarios as S

F_BIG = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
F_B36 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
F_MED = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
F_SML = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
F_S24B = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)

CAPTIONS = {  # akt1: 1:1 z v1/v2; 4a/4b: 1:1 z v3
    "akt1": [(0.0, 6.0, "AKT 1 — DRON WIDZI: cel nadlatuje czołowo; detektor det_v2 na żywej kamerze"),
             (6.0, 14.0, "Zielona ramka = detekcja; TRACK = admisja toru percepcji (14,7 kl/s)"),
             (14.0, 99.0, "Sieć płynna (20 neuronów) prowadzi podejście i orbitę 6–10 m")],
    "4a": [(0.0, 7.0, "AKT 4 — DRON ROZPOZNAJE PRZYNĘTĘ: obiekt krąży, nigdy nie atakuje"),
           (7.0, 15.0, "Sygnatura ruchu: szybki, nie zbliża się, nie schodzi pod 5 m"),
           (15.0, 99.0, "Etykieta WABIK po spełnieniu reguły — czas liczony jawnie")],
    "4b": [(0.0, 7.0, "AKT 4b — FLAGA SIĘ COFA: cel zaczyna jak wabik (kręci, nie zbliża się)"),
           (7.0, 16.0, "Klasyfikator daje flagę wstępną… ale cel ZMIENIA zachowanie"),
           (16.0, 99.0, "Zejście <5 m ⇒ system COFA etykietę i ściga — orbita domyka")],
}
R_E = 32.0
TRAIL_S = 12.0
HALF_M = 36.0
T_FLAG = 12.0
GREEN = (120, 255, 120)
RED = (255, 110, 100)
GREY = (150, 150, 160)


def iter_jsonl(p):
    if not os.path.exists(p):
        return
    with open(p) as f:
        for ln in f:
            try:
                yield json.loads(ln)
            except ValueError:
                continue


def nearest(keys, t, tol):
    i = bisect.bisect_left(keys, t)
    best = None
    for j in (i - 1, i):
        if 0 <= j < len(keys) and abs(keys[j] - t) <= tol:
            if best is None or abs(keys[j] - t) < abs(best - t):
                best = keys[j]
    return best


def zoh(keys, t, max_stale):
    i = bisect.bisect_right(keys, t) - 1
    if i >= 0 and t - keys[i] <= max_stale:
        return keys[i]
    return None


def put(d, xy, txt, font, fill=(255, 255, 255)):
    d.text((xy[0] + 2, xy[1] + 2), txt, font=font, fill=(0, 0, 0))
    d.text(xy, txt, font=font, fill=fill)


def _interp2(series, t):
    if not series:
        return None
    ts = [s[0] for s in series]
    i = bisect.bisect_left(ts, t)
    if i <= 0:
        return series[0][1]
    if i >= len(series):
        return series[-1][1]
    (t0, p0), (t1, p1) = series[i - 1], series[i]
    a = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
    return [p0[0] + a * (p1[0] - p0[0]), p0[1] + a * (p1[1] - p0[1])]


class Panel4:
    """Kopia democ_overlay_v3.Panel4 (plik v3 nietknięty)."""

    def __init__(self, bootdir, sid, obj_col, obj_label):
        self.col = obj_col
        self.lab = obj_label
        self.t0 = None
        self.drone = []
        for r in iter_jsonl(os.path.join(bootdir, "trace.jsonl")):
            if r.get("t") == "event" and r.get("ev") == "episode_start" \
                    and r.get("scenario_id") == sid:
                self.t0 = r["t0_sim"]
            elif r.get("t") == "gt":
                self.drone.append((r["sim"], [r["y"], r["x"]]))
        self.drone.sort()
        self.obj = []
        for r in iter_jsonl(os.path.join(bootdir, "gt_intruder.jsonl")):
            if not r.get("ned"):
                continue
            if r.get("cmd_ned") and math.dist(r["ned"][:2], r["cmd_ned"][:2]) > 1.0:
                continue                                   # filtr brzegu (świadek)
            self.obj.append((r["t_sim"], [r["ned"][0], r["ned"][1]]))
        self.obj.sort()

    def _px(self, ne, W, H):
        return (int(W / 2 + ne[1] / HALF_M * (W / 2 - 8)),
                int(H / 2 - ne[0] / HALF_M * (H / 2 - 8)))

    def _trail(self, img, series, t, col, W, H):
        tt = t - TRAIL_S
        while tt <= t:
            p = _interp2(series, tt)
            if p is not None:
                a = max(0.12, (tt - (t - TRAIL_S)) / TRAIL_S)
                c = tuple(int(ch * a + 26 * (1 - a)) for ch in col)
                cv2.circle(img, self._px(p, W, H), 2, c, -1, cv2.LINE_AA)
            tt += 0.2

    def draw(self, t_abs, W=640, H=640):
        img = np.full((H, W, 3), 26, dtype=np.uint8)
        m = -35
        while m <= 35:
            x, _ = self._px([0, m], W, H)
            _, y = self._px([m, 0], W, H)
            cv2.line(img, (x, 0), (x, H), (40, 40, 44), 1)
            cv2.line(img, (0, y), (W, y), (40, 40, 44), 1)
            m += 5
        c = self._px([0, 0], W, H)
        r_px = int(R_E / HALF_M * (W / 2 - 8))
        cv2.circle(img, c, r_px, (90, 70, 170), 2, cv2.LINE_AA)
        cv2.putText(img, f"strefa oslony R_E = {R_E:.0f} m", (c[0] - r_px + 10, c[1] - r_px + 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 100, 200), 1, cv2.LINE_AA)
        cv2.drawMarker(img, c, (140, 140, 150), cv2.MARKER_CROSS, 12, 1)
        cv2.putText(img, "home", (c[0] + 8, c[1] + 16), cv2.FONT_HERSHEY_SIMPLEX,
                    0.4, (140, 140, 150), 1, cv2.LINE_AA)
        self._trail(img, self.obj, t_abs, self.col, W, H)
        po = _interp2(self.obj, t_abs)
        if po is not None:
            q = self._px(po, W, H)
            cv2.circle(img, q, 6, self.col, -1, cv2.LINE_AA)
            cv2.putText(img, self.lab, (q[0] + 8, q[1] - 6), cv2.FONT_HERSHEY_SIMPLEX,
                        0.45, self.col, 1, cv2.LINE_AA)
        self._trail(img, self.drone, t_abs, (120, 255, 120), W, H)
        pd = _interp2(self.drone, t_abs)
        if pd is not None:
            q = self._px(pd, W, H)
            cv2.circle(img, q, 6, (120, 255, 120), -1, cv2.LINE_AA)
            cv2.putText(img, "dron", (q[0] + 8, q[1] + 16), cv2.FONT_HERSHEY_SIMPLEX,
                        0.45, (120, 255, 120), 1, cv2.LINE_AA)
        cv2.rectangle(img, (0, 0), (W - 1, H - 1), (70, 70, 80), 1)
        cv2.putText(img, "N", (W - 30, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (200, 200, 210), 1, cv2.LINE_AA)
        cv2.arrowedLine(img, (W - 24, 54), (W - 24, 32), (200, 200, 210), 1, tipLength=0.4)
        cv2.putText(img, "panel taktyczny (GT) / siatka 5 m", (10, H - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (150, 150, 160), 1, cv2.LINE_AA)
        return img


def load_common(bootdir, sid):
    t0 = None
    for r in iter_jsonl(os.path.join(bootdir, "trace.jsonl")):
        if r.get("t") == "event" and r.get("ev") == "episode_start" \
                and r.get("scenario_id") == sid:
            t0 = r["t0_sim"]
            break
    assert t0 is not None, f"brak episode_start {sid}"
    demo = [r for r in iter_jsonl(os.path.join(bootdir, "demo.jsonl"))
            if r.get("scenario_id") == sid]
    dts = sorted(r["t_sim"] for r in demo)
    dmap = {r["t_sim"]: r for r in demo}
    pf = {}
    for r in iter_jsonl(os.path.join(bootdir, "percep_feed.jsonl")):
        if r.get("t_frame") is not None:
            pf[round(r["t_frame"], 3)] = r
    pfk = sorted(pf)
    cmap = {}
    for r in iter_jsonl(os.path.join(bootdir, "cam", "frames_index.jsonl")):
        cmap[round(r["sim"], 3)] = r["f"]
    ck = sorted(cmap)
    return t0, demo, dts, dmap, pf, pfk, cmap, ck


def plan_of(t0, segments):
    plan = []
    for (a, b, sp) in segments:
        t = t0 + a
        while t <= t0 + b:
            plan.append((t, sp))
            t += 0.1 * sp
    return plan


def admission_steps(t0, pf, pfk, demo, tacq):
    """Kroki admisji WYLICZONE z logów ujęcia (sim-time kotwic + teksty z liczbami)."""
    s1 = next(((t, pf[t]["conf"]) for t in pfk
               if t >= t0 and pf[t].get("box") and (pf[t].get("conf") or 0) >= 0.5), None)
    assert s1 is not None, "brak klatki detekcji conf>=0.5 w epizodzie"
    run = []
    g3 = None
    for t in pfk:
        if t < t0:
            continue
        if pf[t].get("fresh"):
            run.append(t)
            if len(run) == 3:
                g3 = run[:]
                break
        else:
            run = []
    assert g3 is not None, "brak runu 3 kolejnych klatek fresh w epizodzie"
    t_appr = next((r["t_sim"] for r in demo if r.get("phase") == "approach"), None)
    t_orb = next((r["t_sim"] for r in demo if r.get("phase") == "orbit"), None)
    assert t_appr is not None and t_orb is not None
    return [(s1[0], f"ramka detektora na celu — conf {s1[1]:.2f}"),
            (g3[2], "3 zgodne klatki: centralność + ruch (brama admisji k=3)"),
            (g3[2], f"ADMISJA → TRACK  (t_acq sędziego {tacq:.2f} s)"),
            (max(g3[2], t_appr),
             f"sieć płynna prowadzi — APPROACH {t_appr - t0:.1f} s"
             f" → ORBITA {t_orb - t0:.1f} s")]


def sig_rows_load(sig_jsonl, sig_json):
    """Wiersze per klatka + licznik streaka zrekonstruowany literą classify;
    KOTWICA: flaga/odwołanie rekonstrukcji == sig.json (tol. 10 ms zaokrągleń)."""
    sig = json.load(open(sig_json))
    rows = [json.loads(ln) for ln in open(sig_jsonl)]
    streak = None
    t_flag = None
    t_rev = None
    licz = []
    for r in rows:
        if r["W"]:
            if streak is None:
                streak = r["t_sim"]
            c = r["t_sim"] - streak
            if t_flag is None and c >= T_FLAG:
                t_flag = r["t_sim"]
        else:
            streak = None
            c = 0.0
        if t_flag is not None and t_rev is None and r["dh_min"] < 5.0:
            t_rev = r["t_sim"]
        licz.append(c)
    fa, ra = sig.get("t_flag_abs"), sig.get("t_revoke_abs")
    assert (fa is None) == (t_flag is None) and (fa is None or abs(t_flag - fa) <= 0.01), \
        f"kotwica flagi: {t_flag} vs {fa}"
    assert (ra is None) == (t_rev is None) and (ra is None or abs(t_rev - ra) <= 0.01), \
        f"kotwica odwołania: {t_rev} vs {ra}"
    return sig, rows, licz


def draw_cam(canvas, bootdir, cmap, ck, pf, pfk, t_abs, boxes=True):
    canvas[60:1020, 640:1920] = 128
    conf = None
    tcf = nearest(ck, t_abs, 0.08)
    if tcf is not None:
        cam = cv2.imread(os.path.join(bootdir, "cam", "frames", cmap[tcf]))
        if cam.ndim == 2:
            cam = cv2.cvtColor(cam, cv2.COLOR_GRAY2BGR)
        if boxes:
            tpf = nearest(pfk, tcf, 0.01)
            if tpf is not None and pf[tpf].get("box"):
                b = pf[tpf]["box"]
                conf = pf[tpf].get("conf")
                mti = bool(pf[tpf].get("mti_ok"))
                cx, cy, w, h = b[0] * 640, b[1] * 480, b[2] * 640, b[3] * 480
                cv2.rectangle(cam, (int(cx - w / 2), int(cy - h / 2)),
                              (int(cx + w / 2), int(cy + h / 2)),
                              (80, 255, 80) if mti else (60, 220, 255), 2)
        canvas[60:1020, 640:1920] = cv2.resize(cam, (1280, 960),
                                               interpolation=cv2.INTER_NEAREST)
    return conf


def topbar(d, akt_label, sid, trel, speed):
    d.rectangle([0, 0, 1920, 56], fill=(0, 0, 0, 200))
    put(d, (16, 6), akt_label, F_BIG, (255, 220, 90))
    put(d, (300 if len(akt_label) > 5 else 190, 14),
        f"epizod {sid} · zegar {trel:6.1f} s", F_MED)
    if speed != 1.0:
        d.rectangle([1600, 4, 1904, 52], fill=(0, 0, 0, 220))
        put(d, (1620, 8), f"TEMPO ×{speed:g}", F_BIG, (255, 160, 60))


def caption(d, akt, tk):
    cap = next((c[2] for c in CAPTIONS[akt] if c[0] <= tk < c[1]), None)
    if cap:
        d.rectangle([0, 1020, 1920, 1080], fill=(0, 0, 0, 220))
        put(d, (24, 1032), cap, F_MED)


def render_akt1(bootdir, sid, out_mp4, segments):
    from democ_topdown import Panel                     # moduł v2 FROZEN — importem
    MAN = json.load(open(os.path.join(ROOT, "results", "BENCH", "scenario_manifest.json")))
    ep = {e["scenario_id"]: e for e in MAN["episodes"]}[sid]
    t0, demo, dts, dmap, pf, pfk, cmap, ck = load_common(bootdir, sid)
    wj = json.load(open(os.path.join(ROOT, "results", "DEMO_C", "democ_werdykty.json")))
    boot = os.path.basename(os.path.normpath(bootdir))
    tacq = next(r["t_acq_s"] for r in wj["akty12"][boot] if r["sid"] == sid)
    steps = admission_steps(t0, pf, pfk, demo, tacq)
    panel = Panel(bootdir, sid, 1)
    vw = cv2.VideoWriter(out_mp4, cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (1920, 1080))
    n = 0
    shown_tk = [None] * len(steps)                      # kiedy (tk wyjścia) krok się pokazał
    for (t_abs, speed) in plan_of(t0, segments):
        canvas = np.zeros((1080, 1920, 3), dtype=np.uint8)
        trel = t_abs - t0
        conf = draw_cam(canvas, bootdir, cmap, ck, pf, pfk, t_abs, boxes=True)
        canvas[56:696, 0:640] = panel.draw(t_abs, 640, 640)
        img = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
        d = ImageDraw.Draw(img, "RGBA")
        topbar(d, "AKT 1", sid, trel, speed)
        # HUD 1:1 z v2 (akt 1)
        d.rectangle([0, 696, 640, 1020], fill=(10, 10, 20, 235))
        td = nearest(dts, t_abs, 0.2)
        drow = dmap.get(td) if td is not None else None
        dh = None
        if drow is not None and 0 <= trel <= 112:
            g = S.position_at(ep, max(0.0, trel))
            op = drow["own_pos_ned"]
            dh = math.hypot(g[0] - op[0], g[1] - op[1])
        faza = "—"
        if drow:
            if not drow.get("track_valid"):
                faza = "SCAN (szukam)"
            elif drow.get("phase") == "approach":
                faza = "TRACK → APPROACH"
            elif drow.get("phase") == "orbit":
                faza = "ORBIT 6–10 m"
            else:
                faza = "TRACK"
        put(d, (24, 710), "FAZA", F_SML, GREY)
        put(d, (24, 736), faza, F_B36, (120, 220, 255))
        put(d, (24, 800), "DYSTANS DO CELU (GT)", F_SML, GREY)
        put(d, (24, 826), f"{dh:5.1f} m" if dh is not None else "—", F_B36)
        put(d, (24, 890), "DETEKTOR det_v2 (mono 640×480 ×2)", F_SML, GREY)
        put(d, (24, 916), (f"conf {conf:.2f}" if conf is not None else "brak detekcji"),
            F_MED, GREEN if conf is not None else (255, 160, 120))
        put(d, (24, 975), "panel taktyczny ↑ · kamera pokładowa →", F_SML, (120, 120, 130))
        # sekwencja admisji (kroki pojawiają się na kotwicach sim; dwell ≥1.1 s wyjścia)
        tk = n / 10.0
        for i, (anchor, _) in enumerate(steps):
            if shown_tk[i] is None and t_abs >= anchor \
                    and (i == 0 or (shown_tk[i - 1] is not None and tk >= shown_tk[i - 1] + 1.1)):
                shown_tk[i] = tk
        if tk < 16.0 and any(s is not None for s in shown_tk):
            d.rectangle([1150, 66, 1910, 108 + 34 * sum(s is not None for s in shown_tk)],
                        fill=(0, 0, 0, 185))
            put(d, (1166, 72), "ADMISJA INTRUZA — krok po kroku (liczby z feedu lotu)",
                F_SML, (255, 220, 90))
            y = 104
            last = max((i for i, s in enumerate(shown_tk) if s is not None), default=-1)
            for i, (_, txt) in enumerate(steps):
                if shown_tk[i] is None:
                    continue
                put(d, (1166, y), f"{i + 1}. {txt}", F_SML,
                    (255, 255, 255) if i == last else (185, 185, 195))
                y += 34
        caption(d, "akt1", tk)
        vw.write(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))
        n += 1
    vw.release()
    print(f"[overlay_v31] akt1 {sid}: {n} klatek → {out_mp4}; kroki (sim abs) "
          f"{[round(a, 3) for a, _ in steps]}")


def render_akt4(akt, bootdir, sid, out_mp4, segments, sig_json, sig_jsonl):
    MAN2 = json.load(open(os.path.join(ROOT, "results", "WABIK", "wabik_manifest_s2.json")))
    ep = {e["scenario_id"]: e for e in MAN2["episodes"]}[sid]
    t0, demo, dts, dmap, pf, pfk, cmap, ck = load_common(bootdir, sid)
    sig, srows, licz = sig_rows_load(sig_jsonl, sig_json)
    sk = [r["t_sim"] for r in srows]
    t_flag_abs = sig.get("t_flag_abs")
    t_revoke_abs = sig.get("t_revoke_abs")
    col = (0, 165, 255) if akt == "4a" else (60, 60, 255)
    lab = "wabik" if akt == "4a" else "cel"
    panel = Panel4(bootdir, sid, col, lab)
    vw = cv2.VideoWriter(out_mp4, cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (1920, 1080))
    n = 0
    for (t_abs, speed) in plan_of(t0, segments):
        canvas = np.zeros((1080, 1920, 3), dtype=np.uint8)
        trel = t_abs - t0
        conf = draw_cam(canvas, bootdir, cmap, ck, pf, pfk, t_abs, boxes=True)
        canvas[56:696, 0:640] = panel.draw(t_abs, 640, 640)
        img = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
        d = ImageDraw.Draw(img, "RGBA")
        topbar(d, "AKT 4", sid, trel, speed)
        d.rectangle([0, 696, 640, 1020], fill=(10, 10, 20, 235))
        # --- panel reguły „JAK ROZPOZNAJE" (dane per klatka z sig.jsonl) ---
        ti = zoh(sk, t_abs, 0.3)
        r = srows[sk.index(ti)] if ti is not None else None
        c = licz[sk.index(ti)] if ti is not None else 0.0
        put(d, (24, 702), "JAK ROZPOZNAJE (reguła):", F_SML, (255, 220, 90))
        put(d, (330, 702), "— warunki z zapisu lotu", F_SML, (110, 110, 120))
        conds = [("w ruchu", f"{r['speed']:5.2f} m/s" if r else "",
                  None if not r else r["speed"] > 0.30),
                 ("nie zbliża się", f"v_rad {r['v_rad']:+5.2f}" if r else "",
                  None if not r else r["v_rad"] < 0.30),
                 ("nie był <5 m", f"min {r['dh_min']:4.2f} m" if r else "",
                  None if not r else r["dh_min"] >= 5.0)]
        y = 728
        for name, val, ok in conds:
            put(d, (24, y), name, F_SML)
            put(d, (240, y), val, F_SML, (170, 170, 180))
            put(d, (460, y), "—" if ok is None else ("✓" if ok else "✗"),
                F_S24B, GREY if ok is None else (GREEN if ok else RED))
            y += 26
        flagged = t_flag_abs is not None and t_abs >= t_flag_abs
        revoked = t_revoke_abs is not None and t_abs >= t_revoke_abs
        cd = T_FLAG if flagged else min(c, T_FLAG)
        lcol = (110, 110, 120) if flagged else ((255, 255, 255) if cd > 0 else GREY)
        put(d, (24, y + 6), f"licznik: {cd:4.1f} / {T_FLAG:.0f} s  →", F_MED, lcol)
        et_txt, et_col = "—", (160, 160, 170)
        if flagged:
            if revoked:
                et_txt, et_col = "ODWOŁANA — cel atakuje", (255, 140, 90)
            else:
                et_txt, et_col = f"WABIK  (+{t_abs - t_flag_abs:4.1f} s)", (90, 200, 255)
        put(d, (24, y + 44), et_txt, F_B36, et_col)
        # --- reszta HUD: faza/dystans/detektor/napis uczciwości (teksty v3) ---
        td = nearest(dts, t_abs, 0.2)
        drow = dmap.get(td) if td is not None else None
        dh = None
        if drow is not None and 0 <= trel <= 112:
            g = S.position_at(ep, max(0.0, trel))
            op = drow["own_pos_ned"]
            dh = math.hypot(g[0] - op[0], g[1] - op[1])
        faza = "—"
        if drow:
            if not drow.get("track_valid"):
                faza = "SCAN"
            elif drow.get("phase") == "approach":
                faza = "TRACK → APPROACH"
            elif drow.get("phase") == "orbit":
                faza = "ORBIT 6–10 m"
            else:
                faza = "TRACK"
        put(d, (24, 886), "FAZA", F_SML, GREY)
        put(d, (110, 884), faza, F_MED, (120, 220, 255))
        put(d, (330, 886), "DYSTANS (GT)", F_SML, GREY)
        put(d, (490, 884), f"{dh:5.1f} m" if dh is not None else "—", F_MED)
        put(d, (24, 926), (f"detektor conf {conf:.2f}" if conf is not None else "brak detekcji"),
            F_SML, GREEN if conf is not None else (255, 160, 120))
        put(d, (24, 960), "klasyfikator diagnostyczny — etykieta wyliczona", F_SML, (255, 200, 120))
        put(d, (24, 986), "z zapisu lotu, nie steruje dronem", F_SML, (255, 200, 120))
        caption(d, akt, n / 10.0)
        vw.write(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))
        n += 1
    vw.release()
    print(f"[overlay_v31] akt {akt} {sid}: {n} klatek → {out_mp4}")


def main():
    mode = sys.argv[1]
    segments = [(float(a), float(b), float(c)) for a, b, c in
                (seg.split(":") for seg in sys.argv[5].split(","))]
    if mode == "akt1":
        render_akt1(sys.argv[2], sys.argv[3], sys.argv[4], segments)
    else:
        assert mode in ("4a", "4b")
        render_akt4(mode, sys.argv[2], sys.argv[3], sys.argv[4], segments,
                    sys.argv[6], sys.argv[7])


if __name__ == "__main__":
    main()
