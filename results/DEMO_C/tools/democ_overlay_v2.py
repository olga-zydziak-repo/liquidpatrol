#!/usr/bin/env python3
"""results/DEMO_C/tools/democ_overlay_v2.py — montaż v2 (PROMPT_DEMO_C_V2): KOPIA
democ_overlay.py (v1 NIETYKALNY) z panelem taktycznym z góry (democ_topdown.Panel).

Zmiany vs v1 (decyzja montażowa, nazwana w dopisku raportu):
  • lewa kolumna = PANEL TAKTYCZNY 640×640 (zamiast wkładki świata — miniatura
    świata była mało czytelna i dublowała kontekst; kamera pokładowa pozostaje
    widokiem głównym) + HUD kompaktowy 640×324 pod panelem;
  • akt 3: na panelu DWA punkty drona — GT pełny, ESTYMATA nawigacji kropkowana
    (odpływa po denialu; zmierzone 0.17→3.1 m do touchdown) + legenda w HUD;
  • reszta 1:1 z v1: zegar ciągły, segmenty tempa z JAWNYM podpisem „TEMPO ×N",
    ramki detektora wyłącznie z percep_feed (akty 1–2), napisy PL i plansza bez
    zmian, kamera ×2 nearest-neighbor.

Użycie: democ_overlay_v2.py <bootdir> <sid> <AKT:1|2|3> <t_od> <t_do> <out_mp4> [segmenty]
"""
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
from democ_topdown import Panel

MAN = json.load(open(os.path.join(ROOT, "results", "BENCH", "scenario_manifest.json")))
SCEN = {e["scenario_id"]: e for e in MAN["episodes"]}
F_BIG = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
F_B36 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
F_MED = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
F_SML = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)

CAPTIONS = {  # 1:1 z v1 (napisy PL bez zmian — §2)
    1: [(0.0, 6.0, "AKT 1 — DRON WIDZI: cel nadlatuje czołowo; detektor det_v2 na żywej kamerze"),
        (6.0, 14.0, "Zielona ramka = detekcja; TRACK = admisja toru percepcji (14,7 kl/s)"),
        (14.0, 99.0, "Sieć płynna (20 neuronów) prowadzi podejście i orbitę 6–10 m")],
    2: [(0.0, 7.0, "AKT 2 — DRON SZUKA: cel startuje ZA plecami (azymut 180°) — kamera pusta"),
        (7.0, 14.0, "Skan skokowy całym kadłubem: krok 40°, przegląd perymetru"),
        (14.0, 99.0, "Znalezienie → pościg → orbita; wszystko z jednej kamery mono 640×480")],
    3: [(0.0, 6.0, "AKT 3 — DRON PRZEŻYWA: orbita nominalna (widok z kamery pokładowej)"),
        (6.0, 12.0, "Wstrzykujemy awarię GPS (EKF2_GPS_CTRL=0) — pozycja zaczyna dryfować"),
        (12.0, 99.0, "Osłona: REFUSE(POS) w ~0,1 s → bezpieczne zejście D5 do przyziemienia")],
}


def iter_jsonl(p):
    if not os.path.exists(p):
        return
    with open(p) as f:
        for ln in f:
            try:
                yield json.loads(ln)
            except ValueError:
                continue


def nearest(sorted_keys, t, tol):
    import bisect
    i = bisect.bisect_left(sorted_keys, t)
    best = None
    for j in (i - 1, i):
        if 0 <= j < len(sorted_keys) and abs(sorted_keys[j] - t) <= tol:
            if best is None or abs(sorted_keys[j] - t) < abs(best - t):
                best = sorted_keys[j]
    return best


def zoh(sorted_keys, t, max_stale):
    import bisect
    i = bisect.bisect_right(sorted_keys, t) - 1
    if i >= 0 and t - sorted_keys[i] <= max_stale:
        return sorted_keys[i]
    return None


def put(draw, xy, txt, font, fill=(255, 255, 255)):
    draw.text((xy[0] + 2, xy[1] + 2), txt, font=font, fill=(0, 0, 0))
    draw.text(xy, txt, font=font, fill=fill)


def main():
    bootdir, sid, akt, t_od, t_do, out_mp4 = sys.argv[1], sys.argv[2], int(sys.argv[3]), \
        float(sys.argv[4]), float(sys.argv[5]), sys.argv[6]
    segments = None
    if len(sys.argv) > 7:
        segments = [(float(a), float(b), float(c)) for a, b, c in
                    (seg.split(":") for seg in sys.argv[7].split(","))]
    t0 = None
    events = []
    gts = []
    for r in iter_jsonl(os.path.join(bootdir, "trace.jsonl")):
        if r.get("t") == "event":
            if r.get("ev") == "episode_start" and r.get("scenario_id") == sid:
                t0 = r["t0_sim"]
            events.append(r)
        elif r.get("t") == "gt":
            gts.append((r["sim"], r["z"]))
    gts.sort()
    gk = [g[0] for g in gts]
    galt = {g[0]: g[1] for g in gts}
    assert t0 is not None, f"brak episode_start {sid}"
    demo = [r for r in iter_jsonl(os.path.join(bootdir, "demo.jsonl")) if r.get("scenario_id") == sid]
    dts = sorted(r["t_sim"] for r in demo)
    dmap = {r["t_sim"]: r for r in demo}
    pf = {}
    for r in iter_jsonl(os.path.join(bootdir, "percep_feed.jsonl")):
        if r.get("t_frame") is not None:
            pf[round(r["t_frame"], 3)] = r
    pfk = sorted(pf)
    t_inj = next((e.get("sim") for e in events if e.get("ev") == "denial"), None)
    t_ref = next((e.get("sim") for e in events if e.get("ev") == "refuse"), None)
    t_td = next((e.get("sim") for e in events if e.get("ev") == "touchdown"), None)
    cmap = {}
    for r in iter_jsonl(os.path.join(bootdir, "cam", "frames_index.jsonl")):
        cmap[round(r["sim"], 3)] = r["f"]
    ck = sorted(cmap)
    panel = Panel(bootdir, sid, akt)
    ep = SCEN[sid]

    vw = cv2.VideoWriter(out_mp4, cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (1920, 1080))
    n = 0
    plan = []
    if segments:
        for (a, b, sp) in segments:
            t = t0 + a
            while t <= t0 + b:
                plan.append((t, sp))
                t += 0.1 * sp
    else:
        t = t0 + t_od
        while t <= t0 + t_do:
            plan.append((t, 1.0))
            t += 0.1
    for (t_abs, speed) in plan:
        canvas = np.zeros((1080, 1920, 3), dtype=np.uint8)
        trel = t_abs - t0
        td = nearest(dts, t_abs, 0.2)
        drow = dmap.get(td) if td is not None else None
        dh = None
        if drow is not None and 0 <= trel <= 112:
            g = S.position_at(ep, max(0.0, trel))
            op = drow["own_pos_ned"]
            dh = math.hypot(g[0] - op[0], g[1] - op[1])
        # kamera pokładowa (widok główny) — 1:1 z v1
        canvas[60:1020, 640:1920] = 128
        tcf = nearest(ck, t_abs, 0.08)
        conf = None
        if tcf is not None:
            cam = cv2.imread(os.path.join(bootdir, "cam", "frames", cmap[tcf]))
            if cam.ndim == 2:
                cam = cv2.cvtColor(cam, cv2.COLOR_GRAY2BGR)
            if akt in (1, 2):
                tpf = nearest(pfk, tcf, 0.01)
                if tpf is not None and pf[tpf].get("box"):
                    b = pf[tpf]["box"]
                    conf = pf[tpf].get("conf")
                    mti = bool(pf[tpf].get("mti_ok"))
                    cx, cy, w, h = b[0] * 640, b[1] * 480, b[2] * 640, b[3] * 480
                    box = (int(cx - w / 2), int(cy - h / 2), int(cx + w / 2), int(cy + h / 2))
                    cv2.rectangle(cam, (box[0], box[1]), (box[2], box[3]),
                                  (80, 255, 80) if mti else (60, 220, 255), 2)
            cam2 = cv2.resize(cam, (1280, 960), interpolation=cv2.INTER_NEAREST)
            canvas[60:1020, 640:1920] = cam2
        # PANEL TAKTYCZNY (lewa kolumna, zamiast wkładki świata)
        canvas[56:696, 0:640] = panel.draw(t_abs, 640, 640)
        # HUD kompaktowy + napisy (PIL)
        img = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle([0, 0, 1920, 56], fill=(0, 0, 0, 200))
        put(d, (16, 6), f"AKT {akt}", F_BIG, (255, 220, 90))
        put(d, (190, 14), f"epizod {sid} · zegar {trel:6.1f} s", F_MED)
        d.rectangle([0, 696, 640, 1020], fill=(10, 10, 20, 235))
        if akt in (1, 2):
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
            put(d, (24, 710), "FAZA", F_SML, (150, 150, 160))
            put(d, (24, 736), faza, F_B36, (120, 220, 255))
            put(d, (24, 800), "DYSTANS DO CELU (GT)", F_SML, (150, 150, 160))
            put(d, (24, 826), f"{dh:5.1f} m" if dh is not None else "—", F_B36)
            put(d, (24, 890), "DETEKTOR det_v2 (mono 640×480 ×2)", F_SML, (150, 150, 160))
            put(d, (24, 916), (f"conf {conf:.2f}" if conf is not None else "brak detekcji"),
                F_MED, (120, 255, 120) if conf is not None else (255, 160, 120))
            put(d, (24, 975), "panel taktyczny ↑ · kamera pokładowa →", F_SML, (120, 120, 130))
        else:
            gps = "GPS OK"
            col = (120, 255, 120)
            if t_inj and t_abs >= t_inj:
                gps, col = "GPS DENIED", (255, 120, 90)
            if t_ref and t_abs >= t_ref:
                gps, col = "SHIELD: REFUSE(POS) → D5", (255, 220, 90)
            if t_td and t_abs >= t_td:
                gps, col = "TOUCHDOWN — bez naruszeń", (120, 255, 120)
            alt = None
            tg = zoh(gk, t_abs, 0.5)
            if tg is not None:
                alt = max(0.0, galt[tg])
            put(d, (24, 706), "STAN", F_SML, (150, 150, 160))
            put(d, (24, 730), gps, F_B36, col)
            put(d, (24, 790), "WYSOKOŚĆ (GT)", F_SML, (150, 150, 160))
            put(d, (24, 816), f"{alt:5.1f} m" if alt is not None else "—", F_B36)
            if dh is not None:
                put(d, (330, 790), "DYSTANS (GT)", F_SML, (150, 150, 160))
                put(d, (330, 816), f"{dh:5.1f} m", F_B36)
            put(d, (24, 880), "panel: ● dron (GT) · ∘ estymata nawigacji —", F_SML, (80, 190, 255))
            put(d, (24, 906), "po denialu estymata ODPŁYWA od prawdy", F_SML, (80, 190, 255))
            put(d, (24, 946), "percepcja EMULOWANA w tym akcie", F_SML, (255, 200, 120))
            put(d, (24, 972), "(obraz pokładowy = podgląd, nie karmi sterowania)", F_SML, (255, 200, 120))
        if speed > 1.0:
            d.rectangle([1600, 4, 1904, 52], fill=(0, 0, 0, 220))
            put(d, (1620, 8), f"TEMPO ×{speed:g}", F_BIG, (255, 160, 60))
        tk = n / 10.0
        cap = next((c[2] for c in CAPTIONS[akt] if c[0] <= tk < c[1]), None)
        if cap:
            d.rectangle([0, 1020, 1920, 1080], fill=(0, 0, 0, 220))
            put(d, (24, 1032), cap, F_MED)
        canvas = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        vw.write(canvas)
        n += 1
    vw.release()
    print(f"[overlay_v2] akt {akt} {sid}: {n} klatek → {out_mp4}")


if __name__ == "__main__":
    main()
