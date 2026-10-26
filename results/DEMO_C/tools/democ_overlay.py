#!/usr/bin/env python3
"""results/DEMO_C/tools/democ_overlay.py — render klipu aktu (PROMPT_DEMO_C §3.2), offline po locie.

Zasady (FROZEN §1.2): zero inscenizacji — klip = JEDNO CIĄGŁE okno czasu epizodu
(zero cięć wewnątrz, zero przyspieszeń ⇒ zero podpisów ×N); zegar epizodu ciągły
na overlayu; ramki detektora wyłącznie z percep_feed (dopasowanie po t_frame);
kamera pokładowa upscale ×2 nearest-neighbor (pixel-look, bez wygładzania).

Kompozycja 1920×1080 @10 fps (kadencja = klatki świata, stemple sim):
  AKT12: kamera 640×480→×2 NN (1280×960) po prawej; świat 640×360 lewy-góra;
         panel telemetrii lewy-dół (zegar, faza, dystans, conf); pasek napisu PL.
  AKT3:  świat pełnoekranowo (1920×1080, upscale ×1.5); panel + wskaźnik
         GPS OK → GPS DENIED → SHIELD (D5) → TOUCHDOWN z trace; napis o percepcji
         emulowanej WYPALONY przez cały akt.
Werdykt klipu NIE powstaje tu — mapping take→werdykt liczy democ_judge/raport.

Użycie: democ_overlay.py <bootdir> <sid> <AKT:1|2|3> <t_od_rel> <t_do_rel> <out_mp4>
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
from bench import scenarios as S

MAN = json.load(open(os.path.join(ROOT, "results", "BENCH", "scenario_manifest.json")))
SCEN = {e["scenario_id"]: e for e in MAN["episodes"]}
F_BIG = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
F_MED = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
F_SML = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)

CAPTIONS = {  # napisy PL per akt: (t_od_rel_klipu, t_do_rel_klipu, tekst)
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
    """ostatnia klatka ≤ t (ZOH renderera; klatki trzymane, nigdy fabrykowane)."""
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
    # t0 epizodu + eventy
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

    def widx(sub):
        rows = [r for r in iter_jsonl(os.path.join(bootdir, sub, "frames_index.jsonl"))]
        return {round(r["sim"], 3): r["f"] for r in rows}

    wmap = widx("world")
    wk = sorted(wmap)
    cmap = widx("cam")
    ck = sorted(cmap)

    ep = SCEN[sid]
    vw = cv2.VideoWriter(out_mp4, cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (1920, 1080))
    n = 0
    t_abs = t0 + t_od
    while t_abs <= t0 + t_do:
        twf = zoh(wk, t_abs, 0.5)
        if twf is None:
            t_abs += 0.1
            continue
        world = cv2.imread(os.path.join(bootdir, "world", "frames", wmap[twf]))
        canvas = np.zeros((1080, 1920, 3), dtype=np.uint8)
        trel = t_abs - t0
        # demo tick (faza, pozycje)
        td = nearest(dts, t_abs, 0.2)
        drow = dmap.get(td) if td is not None else None
        # dystans z manifestu
        dh = None
        if drow is not None and 0 <= trel <= 112:
            g = S.position_at(ep, max(0.0, trel))
            op = drow["own_pos_ned"]
            dh = math.hypot(g[0] - op[0], g[1] - op[1])
        canvas[60:1020, 640:1920] = 128
        tcf = nearest(ck, t_abs, 0.08)
        box = None
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
                    box = (int(cx - w / 2), int(cy - h / 2), int(cx + w / 2), int(cy + h / 2), mti)
                if box:
                    cv2.rectangle(cam, (box[0], box[1]), (box[2], box[3]),
                                  (80, 255, 80) if box[4] else (60, 220, 255), 2)
            cam2 = cv2.resize(cam, (1280, 960), interpolation=cv2.INTER_NEAREST)
            canvas[60:1020, 640:1920] = cam2
        wsm = cv2.resize(world, (640, 360), interpolation=cv2.INTER_AREA)
        canvas[60:420, 0:640] = wsm
        # panel (PIL)
        img = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle([0, 0, 1920, 56], fill=(0, 0, 0, 200))
        put(d, (16, 6), f"AKT {akt}", F_BIG, (255, 220, 90))
        put(d, (190, 14), f"epizod {sid} · zegar {trel:6.1f} s", F_MED)
        if akt in (1, 2):
            d.rectangle([0, 430, 640, 1020], fill=(10, 10, 20, 230))
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
            put(d, (24, 460), "FAZA", F_SML, (150, 150, 160))
            put(d, (24, 490), faza, F_BIG, (120, 220, 255))
            put(d, (24, 570), "DYSTANS DO CELU (GT)", F_SML, (150, 150, 160))
            put(d, (24, 600), f"{dh:5.1f} m" if dh is not None else "—", F_BIG)
            put(d, (24, 680), "DETEKTOR det_v2 (kamera mono 640×480 ×2)", F_SML, (150, 150, 160))
            put(d, (24, 710), (f"conf {conf:.2f}" if conf is not None else "brak detekcji"),
                F_MED, (120, 255, 120) if conf is not None else (255, 160, 120))
            put(d, (24, 770), "świat ↑ · kamera pokładowa →", F_SML, (120, 120, 130))
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
            d.rectangle([0, 430, 640, 1020], fill=(10, 10, 20, 230))
            put(d, (24, 460), "STAN", F_SML, (150, 150, 160))
            put(d, (24, 490), gps, ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36), col)
            put(d, (24, 570), "WYSOKOŚĆ (GT)", F_SML, (150, 150, 160))
            put(d, (24, 600), f"{alt:5.1f} m" if alt is not None else "—", F_BIG)
            put(d, (24, 680), "DYSTANS DO INTRUZA (GT)", F_SML, (150, 150, 160))
            put(d, (24, 710), f"{dh:5.1f} m" if dh is not None else "—", F_MED)
            put(d, (24, 790), "percepcja EMULOWANA w tym akcie", F_SML, (255, 200, 120))
            put(d, (24, 820), "(obraz pokładowy = podgląd, nie karmi sterowania)", F_SML, (255, 200, 120))
            put(d, (24, 880), "świat ↑ · kamera pokładowa →", F_SML, (120, 120, 130))
        # napis PL (pasek dolny)
        tk = trel - t_od
        cap = next((c[2] for c in CAPTIONS[akt] if c[0] <= tk < c[1]), None)
        if cap:
            d.rectangle([0, 1020, 1920, 1080], fill=(0, 0, 0, 220))
            put(d, (24, 1032), cap, F_MED)
        canvas = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        vw.write(canvas)
        n += 1
        t_abs += 0.1
    vw.release()
    print(f"[overlay] akt {akt} {sid}: {n} klatek → {out_mp4}")


if __name__ == "__main__":
    main()
