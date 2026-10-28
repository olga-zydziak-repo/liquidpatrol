#!/usr/bin/env python3
"""results/DEMO_C/tools/democ_overlay_v5.py — montaż v5 „sieć przez całe demo"
(seans Olgi po STOP-DEMOC-4: pas sieci w aktach + lepszy widok neuronów).
NOWY plik; v1–v4 NIETYKALNE. Zero bootów; te same ujęcia i logi; aktywacje
WYŁĄCZNIE replayem (xai_replay ac9551ab IMPORTEM, wagi 0337d5ea kopią);
zasada cytowania FREEZE_XAI: na ekranie tylko T1/T2, role „opisowe".

Nowości v5:
  • WIDOK „ŻYWA SIEĆ": graf NCP-20 — 8 wejść → 20 neuronów (4×5, puls:
    promień ∝|h_i|, kolor = znak) → 3 wyjścia vn/ve/vd (wartości na żywo);
    krawędzie = top-3 |Wo| per wyjście (struktura stała z wag).
  • MINI-MÓZG W ROGU AKTÓW 1/2/4a/4b: nakładka na GOTOWE klipy (zero
    re-renderu aktów): mapping klatka→t_sim odtworzony z segmentów TEMPO
    danego klipu (litera raportów v2/v3/v3.1; asercja liczby klatek).
    AKT 3 BEZ nakładki: po REFUSE(POS) steruje OSŁONA (zejście D5), pas
    sieci sugerowałby sterowanie siecią — powód nazwany w dopisku.
  • AKT 5 (nowy widok): pierścień PCA (zoom na medianę projekcji ujęcia)
    + kompas „kierunek na cel" (krążą razem) + ŻYWA SIEĆ (pełny graf)
    + nakładka krzywych n0 vs sin(bearing) z lotu (|r| liczona z TEGO
    ujęcia i wypalona) + sekwencja 4 kroków (wzór admisji v3.1).

Tryby:
  brain-clip <in.mp4> <out.mp4> <bootdir> <sid> <segmenty a:b:sp,...>
  akt5 <bootdir> <sid> <akt2_v2.mp4> <pca_base.json> <out.mp4> <segmenty>
  cut <a1> <a2> <a3> <a4a> <a4b> <a5> <out_dir>
"""
import json
import math
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
for p in (ROOT, os.path.join(ROOT, "results", "XAI_RECON", "tools")):
    if p not in sys.path:
        sys.path.insert(0, p)
from xai_replay import load_eps, replay_episode, anchor_stats, model_of  # FROZEN

F_T = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 54)
F_BIG = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
F_B28 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
F_B22 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
F_MED = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
F_M38 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 38)
F_SML = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
F_S18 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
F_S15 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)

FAZA_COL = {"hold": (150, 150, 160), "approach": (255, 160, 90), "orbit": (60, 165, 255)}
FAZA_PL = {"hold": "scan", "approach": "approach", "orbit": "orbita"}
XN8 = ["rel_x", "rel_y", "rel_z", "v_n", "v_e", "v_d", "age", "trk"]

CAPTIONS5 = [(0.0, 7.0, "AKT 5 — W GŁOWIE SIECI: ta sama misja co akt 2; stan 20 neuronów odtworzony replayem"),
             (7.0, 16.0, "Skan: stan STOI. Akwizycja: stan SKACZE. Orbita: stan krąży po PIERŚCIENIU"),
             (16.0, 26.0, "Pierścień stanu i strzałka «kierunek na cel» krążą RAZEM — tak sieć pamięta, gdzie jest cel"),
             (26.0, 99.0, "Wykres: neuron n0 nakłada się na sin(kierunku na cel) — czytamy, CO sieć koduje (opisowe)")]

PLANSZA = ["LiquidPatrol — PX4/Gazebo SITL.",
           "Zero naruszeń strefy i zero błędnych odmów w ~140 bootach.",
           "Sterownik: płynna sieć 20 neuronów — 48/48 vs GRU 29/48",
           "na tej samej siatce.",
           "Wabiki: rozpoznawane po zachowaniu — zero fałszywych alarmów w pomiarach.",
           "Sterownik: 20 neuronów — dowiedzione twierdzenia o ograniczoności (T1/T2),",
           "aktywacje audytowalne replayem.",
           "Domowy sprzęt, wieczory i weekendy."]


def put(d, xy, txt, font, fill=(255, 255, 255)):
    d.text((xy[0] + 2, xy[1] + 2), txt, font=font, fill=(0, 0, 0))
    d.text(xy, txt, font=font, fill=fill)


def plan_of(t0, segments):
    plan = []
    for (a, b, sp) in segments:
        t = t0 + a
        while t <= t0 + b:
            plan.append((t, sp))
            t += 0.1 * sp
    return plan


def rep_of(bootdir, sid):
    eps = load_eps(os.path.join(ROOT, bootdir) if not os.path.isabs(bootdir) else bootdir)
    k = [kk for kk in eps if eps[kk][0]["scenario_id"] == sid][0]
    rows = eps[k]
    rep = replay_episode(rows, "ncp", fantom=(rows[0]["controller"] == "net_fantom"))
    return rep, rows


def top_edges(m, k=3):
    """Top-k |Wo[i,out]| per wyjście — struktura stała z wag (kopia npz)."""
    return [list(np.argsort(-np.abs(m.Wo[:, o]))[:k]) for o in range(3)]


def node_col(v):
    """BGR: dodatnie czerwonawe / ujemne niebieskie (jak pasek v4)."""
    return (90, 90, 255) if v > 0 else (255, 170, 90)


def draw_brain(canvas, region, hvec, yvec, xvec, edges, mini=False):
    """Żywa sieć: wejścia→neurony(4×5)→wyjścia. hvec (20,), yvec (3,) m/s,
    xvec (8,) znorm. lub None (brak tracka)."""
    x0, y0, w, h = region
    ov = canvas[y0:y0 + h, x0:x0 + w].astype(np.int32)
    ov = (ov * 0.15 + np.array([30, 26, 24]) * 0.85).astype(np.uint8)
    canvas[y0:y0 + h, x0:x0 + w] = ov
    cv2.rectangle(canvas, (x0, y0), (x0 + w - 1, y0 + h - 1), (90, 90, 100), 1)
    gx0 = x0 + (int(w * 0.30) if not mini else 14)
    gx1 = x0 + w - (74 if not mini else 46)
    gy0, gy1 = y0 + (34 if not mini else 26), y0 + h - (16 if not mini else 10)
    pos = {}
    for i in range(20):
        r, c = divmod(i, 5)
        pos[i] = (int(gx0 + c * (gx1 - gx0) / 4.6), int(gy0 + r * (gy1 - gy0) / 3))
    out_xy = [(x0 + w - (40 if not mini else 22), int(y0 + h * f)) for f in (0.28, 0.52, 0.76)]
    for o, idxs in enumerate(edges):
        for i in idxs:
            cv2.line(canvas, pos[i], out_xy[o], (70, 70, 80), 1, cv2.LINE_AA)
    base_r = 3 if mini else 4
    amp = 9 if mini else 13
    for i in range(20):
        v = float(hvec[i])
        rr = base_r + int(abs(v) * amp)
        cv2.circle(canvas, pos[i], rr, node_col(v), -1, cv2.LINE_AA)
        cv2.circle(canvas, pos[i], rr, (25, 25, 28), 1, cv2.LINE_AA)
    for o, (ox, oy) in enumerate(out_xy):
        v = float(yvec[o])
        rr = base_r + int(min(abs(v) / 3.0, 1.0) * amp)
        cv2.circle(canvas, (ox, oy), rr, node_col(v), -1, cv2.LINE_AA)
        cv2.circle(canvas, (ox, oy), rr, (25, 25, 28), 1, cv2.LINE_AA)
    if not mini and xvec is not None:
        ixx = x0 + 30
        for j in range(8):
            iy = int(y0 + 40 + j * (h - 60) / 7)
            v = float(xvec[j])
            cv2.circle(canvas, (ixx + 150, iy), 3 + int(min(abs(v), 2.5) * 3),
                       node_col(v), -1, cv2.LINE_AA)
            cv2.line(canvas, (ixx + 158, iy), (gx0 - 8, iy), (55, 55, 62), 1)
    return out_xy


def brain_clip(in_mp4, out_mp4, bootdir, sid, segments):
    rep, rows = rep_of(bootdir, sid)
    tt = rep["t"]
    t0 = tt[0]
    plan = plan_of(t0, segments)
    cap = cv2.VideoCapture(in_mp4)
    n_in = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    assert len(plan) == n_in, f"mapping segmentów ≠ klip: plan {len(plan)} vs {n_in} klatek"
    m = model_of("ncp")
    edges = top_edges(m)
    vw = cv2.VideoWriter(out_mp4, cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (1920, 1080))
    reg = (1596, 736, 312, 236)
    for (t_abs, _sp) in plan:
        ok, fr = cap.read()
        if not ok:
            break
        i = min(max(int(np.searchsorted(tt, t_abs, side="right")) - 1, 0), len(tt) - 1)
        draw_brain(fr, reg, rep["h"][i], rep["y"][i], None, edges, mini=True)
        img = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
        d = ImageDraw.Draw(img, "RGBA")
        put(d, (reg[0] + 8, reg[1] + 4), "W GŁOWIE SIECI — ta sieć PROWADZI lot", F_S15, (255, 220, 120))
        put(d, (reg[0] + 8, reg[1] + reg[3] - 22), "panel = replay zapisu (nie steruje)",
            F_S15, (200, 180, 140))
        vw.write(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))
    vw.release()
    cap.release()
    print(f"[brain-clip] {sid}: {n_in} klatek → {out_mp4}")


def render_akt5(bootdir, sid, clip_v2, base_json, out_mp4, segments):
    base = json.load(open(base_json))
    mean = np.array(base["mean"]); comp = np.array(base["comp"])
    rep, rows = rep_of(bootdir, sid)
    st = anchor_stats(rep)
    assert st["p95"] <= 1e-2, f"STOP: kotwica ujęcia p95={st['p95']}>1e-2"
    print(f"[akt5] kotwica {sid}: p50={st['p50']:.2e} p95={st['p95']:.2e} max={st['max']:.2e}")
    tt = rep["t"]; t0 = tt[0]
    mm = rep["infer"]
    P = (rep["h"] - mean) @ comp.T
    ctr = np.median(P[mm], axis=0)
    lim = float(np.percentile(np.linalg.norm(P[mm] - ctr, axis=1), 99)) * 1.18
    brg = np.array([math.atan2(r["trk_pos_ned"][1] - r["own_pos_ned"][1],
                               r["trk_pos_ned"][0] - r["own_pos_ned"][0]) for r in rows])
    sb = np.sin(brg)
    n0 = rep["h"][:, 0]
    r_n0 = float(np.corrcoef(n0[mm], sb[mm])[0, 1])
    print(f"[akt5] corr(n0, sin_brg) tego ujęcia: {r_n0:+.3f}")
    t_acq = float(tt[np.argmax(mm)] - t0)
    i_orb = np.where(rep["phase"] == "orbit")[0]
    t_orb = float(tt[i_orb[0]] - t0) if len(i_orb) else 99.0
    steps = [(1.0, "1. skan: sieć nie widzi celu — punkt stanu STOI"),
             (t_acq + 0.2, f"2. akwizycja ({t_acq:.1f} s): stan SKACZE — sieć złapała cel"),
             (t_orb + 5.0, "3. orbita: stan krąży po PIERŚCIENIU — rytm = okrążenia celu"),
             (20.0, f"4. neuron n0 ≈ sin(kierunku na cel): |r|={abs(r_n0):.2f} na tym ujęciu")]
    m = model_of("ncp")
    edges = top_edges(m)
    cap = cv2.VideoCapture(clip_v2)
    n_clip = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cur = -1; frame_small = None
    plan = plan_of(t0, segments)
    vw = cv2.VideoWriter(out_mp4, cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (1920, 1080))
    W2, H2 = 960, 540
    x0, y0, wP, hP = 1000, 70, 880, 400

    def px(p):
        return (int(x0 + (p[0] - ctr[0] + lim) / (2 * lim) * wP),
                int(y0 + hP - (p[1] - ctr[1] + lim) / (2 * lim) * hP))

    shown_tk = [None] * len(steps)
    n = 0
    for (t_abs, speed) in plan:
        trel = t_abs - t0
        idx = min(max(int(round(trel * 10)), 0), n_clip - 1)
        while cur < idx:
            ok, fr = cap.read()
            if not ok:
                break
            cur += 1
            frame_small = cv2.resize(fr, (W2, H2), interpolation=cv2.INTER_AREA)
        canvas = np.full((1080, 1920, 3), 14, dtype=np.uint8)
        if frame_small is not None:
            canvas[262:262 + H2, 0:W2] = frame_small
            cv2.rectangle(canvas, (0, 262), (W2 - 1, 262 + H2 - 1), (70, 70, 80), 1)
        # panel PCA
        cv2.rectangle(canvas, (x0 - 10, y0 - 10), (x0 + wP + 10, y0 + hP + 10), (40, 40, 46), -1)
        cv2.rectangle(canvas, (x0 - 10, y0 - 10), (x0 + wP + 10, y0 + hP + 10), (80, 80, 90), 1)
        i_now = int(np.searchsorted(tt, t_abs, side="right")) - 1
        for i in range(1, max(i_now, 1)):
            col = FAZA_COL.get(rep["phase"][i], (120, 120, 120))
            c = tuple(int(ch * 0.45 + 40 * 0.55) for ch in col)
            q = px(P[i])
            if x0 <= q[0] <= x0 + wP and y0 <= q[1] <= y0 + hP:
                cv2.circle(canvas, q, 1, c, -1)
        i_lo = int(np.searchsorted(tt, t_abs - 8.0))
        for i in range(max(i_lo, 1), max(i_now, 1)):
            a = (tt[i] - (t_abs - 8.0)) / 8.0
            col = FAZA_COL.get(rep["phase"][i], (120, 120, 120))
            c = tuple(int(ch * (0.3 + 0.7 * a)) for ch in col)
            cv2.line(canvas, px(P[i - 1]), px(P[i]), c, 2, cv2.LINE_AA)
        if i_now >= 0:
            cv2.circle(canvas, px(P[i_now]), 8,
                       FAZA_COL.get(rep["phase"][i_now], (200, 200, 200)), -1, cv2.LINE_AA)
        # kompas bearingu (z lotu) — krąży razem z punktem na pierścieniu
        cxy = (x0 + wP - 70, y0 + 78)
        cv2.circle(canvas, cxy, 46, (55, 55, 62), -1, cv2.LINE_AA)
        cv2.circle(canvas, cxy, 46, (120, 120, 130), 1, cv2.LINE_AA)
        if i_now >= 0 and mm[i_now]:
            b = brg[i_now]
            tip = (int(cxy[0] + 38 * math.sin(b)), int(cxy[1] - 38 * math.cos(b)))
            cv2.arrowedLine(canvas, cxy, tip, (60, 165, 255), 3, cv2.LINE_AA, tipLength=0.3)
        # żywa sieć (pełny graf)
        hv = rep["h"][i_now] if i_now >= 0 else np.zeros(20)
        yv = rep["y"][i_now] if i_now >= 0 else np.zeros(3)
        xv = rep["x"][i_now] if (i_now >= 0 and mm[i_now]) else None
        out_xy = draw_brain(canvas, (1000, 660, 890, 230), hv, yv, xv, edges, mini=False)
        img = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle([0, 0, 1920, 56], fill=(0, 0, 0, 210))
        put(d, (16, 4), "AKT 5 — W GŁOWIE SIECI", F_BIG, (255, 220, 90))
        put(d, (700, 14), f"epizod {sid} (ujęcie aktu 2) · zegar {trel:5.1f} s", F_MED)
        if speed != 1.0:
            d.rectangle([1600, 4, 1904, 52], fill=(0, 0, 0, 220))
            put(d, (1620, 8), f"TEMPO ×{speed:g}", F_BIG, (255, 160, 60))
        # kroki (lewa góra)
        tk = n / 10.0
        for i, (anch, _) in enumerate(steps):
            if shown_tk[i] is None and trel >= anch \
                    and (i == 0 or (shown_tk[i - 1] is not None and tk >= shown_tk[i - 1] + 1.0)):
                shown_tk[i] = tk
        d.rectangle([8, 64, 952, 84 + 34 * max(sum(s is not None for s in shown_tk), 1)],
                    fill=(0, 0, 0, 185))
        put(d, (20, 68), "KROK PO KROKU (liczby z tego lotu):", F_S18, (255, 220, 90))
        yk = 92
        last = max((i for i, s in enumerate(shown_tk) if s is not None), default=-1)
        for i, (_, txt) in enumerate(steps):
            if shown_tk[i] is None:
                continue
            put(d, (20, yk), txt, F_SML, (255, 255, 255) if i == last else (185, 185, 195))
            yk += 32
        # podpisy PCA + faza + legenda
        put(d, (1000, 476), f"PRZESTRZEŃ STANU h(t)∈R²⁰ → PCA · 2 osie = {base['var_top2_pct']}% "
                            f"wariancji (pomiar atlasu)", F_S18, (190, 190, 200))
        ph_now = rep["phase"][i_now] if i_now >= 0 else "hold"
        put(d, (1016, 84), "faza:", F_SML, (150, 150, 160))
        put(d, (1082, 82), FAZA_PL.get(ph_now, ph_now), F_B28,
            tuple(reversed(FAZA_COL.get(ph_now, (200, 200, 200)))))
        lx = 1268
        for phk in ("hold", "approach", "orbit"):
            col = tuple(reversed(FAZA_COL[phk]))
            d.rectangle([lx, 92, lx + 14, 106], fill=col)
            put(d, (lx + 20, 86), FAZA_PL[phk], F_S18, col)
            lx += 128
        put(d, (1704, 134), "kierunek", F_S15, (190, 190, 200))
        put(d, (1704, 152), "na cel", F_S15, (190, 190, 200))
        if ph_now == "orbit" and 11.0 <= trel <= 24.0:
            put(d, (1060, 420), "stabilny cykl = decyzja «krążę»", F_B28, (255, 200, 90))
        # sparkline n0 vs sin_brg
        sx, sy, sw, sh = 1000, 522, 880, 118
        d.rectangle([sx - 10, sy - 8, sx + sw + 10, sy + sh + 8], fill=(40, 40, 46))
        tlo = t_abs - 14.0
        pts_s, pts_n = [], []
        for i in range(len(tt)):
            if tlo <= tt[i] <= t_abs:
                xq = sx + (tt[i] - tlo) / 14.0 * sw
                if mm[i]:
                    pts_s.append((xq, sy + sh / 2 - sb[i] * sh * 0.42))
                else:
                    if pts_s:
                        d.line(pts_s, fill=(255, 205, 90), width=2); pts_s = []
                pts_n.append((xq, sy + sh / 2 - np.clip(n0[i], -1, 1) * sh * 0.42))
        if len(pts_s) > 1:
            d.line(pts_s, fill=(255, 205, 90), width=2)
        if len(pts_n) > 1:
            d.line(pts_n, fill=(120, 255, 140), width=2)
        put(d, (sx + 4, sy - 4), "neuron n0", F_S18, (120, 255, 140))
        put(d, (sx + 140, sy - 4), "sin(kierunku na cel) z lotu", F_S18, (255, 205, 90))
        put(d, (sx + 480, sy - 4), f"|r| = {abs(r_n0):.2f} (to ujęcie; atlas 0.95) — opisowe",
            F_S18, (190, 190, 200))
        # podpisy żywej sieci
        put(d, (1000, 636), "ŻYWA SIEĆ: 8 wejść → 20 neuronów → komenda [vn ve vd] (replay)",
            F_S18, (190, 190, 200))
        for j, nm in enumerate(XN8):
            iy = int(660 + 40 + j * (230 - 60) / 7)
            put(d, (1006, iy - 9), nm, F_S15, (170, 170, 180))
        for o, nm in enumerate(("vn", "ve", "vd")):
            put(d, (out_xy[o][0] - 8, out_xy[o][1] - 34), nm, F_S15, (200, 200, 210))
            put(d, (out_xy[o][0] - 26, out_xy[o][1] + 14),
                f"{float(yv[o]):+.1f}", F_S15, (200, 200, 210))
        # linia twierdzeń + uczciwość + napisy
        d.rectangle([0, 912, 1920, 960], fill=(10, 10, 24, 235))
        put(d, (24, 920), "dowiedzione: |komenda| < 3 m/s (T1) · stan ograniczony |h|<1 (T2)"
                          " — status PROVED, różnicówka 0/74 708 ticków", F_B28, (120, 255, 160))
        d.rectangle([0, 962, 1920, 1016], fill=(0, 0, 0, 200))
        put(d, (24, 966), "sieć NCP-20 PROWADZIŁA ten lot; panel aktywacji odtworzony "
                          "deterministycznie z zapisu (replay) — sam niczym nie steruje",
            F_SML, (255, 200, 120))
        put(d, (24, 990), f"kotwica tego ujęcia: p95 |Δv_replay − Δv_log| = "
                          f"{st['p95'] * 1000:.1f}·10⁻³ m/s (max {st['max'] * 1000:.1f}·10⁻³)",
            F_SML, (255, 200, 120))
        c5 = next((c[2] for c in CAPTIONS5 if c[0] <= tk < c[1]), None)
        if c5:
            d.rectangle([0, 1020, 1920, 1080], fill=(0, 0, 0, 220))
            put(d, (24, 1032), c5, F_MED)
        vw.write(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))
        n += 1
    vw.release(); cap.release()
    print(f"[akt5-v5] {n} klatek → {out_mp4}")


def srt_time(t):
    ms = int(round((t - int(t)) * 1000))
    s = int(t)
    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d},{ms:03d}"


def cut(clips, outd):
    out = os.path.join(outd, "DEMO_C_v5.mp4")
    vw = cv2.VideoWriter(out, cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (1920, 1080))
    lens = []
    for p in clips:
        c = cv2.VideoCapture(p); k = 0
        while True:
            ok, fr = c.read()
            if not ok:
                break
            vw.write(fr); k += 1
        lens.append(k); c.release()
    img = Image.new("RGB", (1920, 1080), (8, 10, 16))
    d = ImageDraw.Draw(img)
    y = 270
    for i, ln in enumerate(PLANSZA):
        f = F_T if i == 0 else F_M38
        w = d.textlength(ln, font=f)
        d.text(((1920 - w) / 2, y), ln, font=f,
               fill=(255, 220, 90) if i == 0 else
                    ((255, 190, 120) if i == 4 else
                     ((120, 255, 160) if i in (5, 6) else (235, 235, 235))))
        y += 92 if i == 0 else 62
    pl = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    for _ in range(90):
        vw.write(pl)
    vw.release()
    # SRT: bloki v3.1 (te same długości aktów 1–4) + akt 5 + plansza v4
    src = open(os.path.join(outd, "DEMO_C_v31_en.srt")).read().strip().split("\n\n")
    blocks = src[:-1]
    t5 = sum(lens[:5]) / 10.0
    dur5 = lens[5] / 10.0
    ak5 = [(0, 7, "ACT 5 — INSIDE THE NETWORK: same mission as act 2; the 20-neuron state replayed deterministically"),
           (7, 16, "Scan: the state SITS STILL. Acquisition: it JUMPS. Orbit: it circles a RING (PCA, 87.8% of variance)"),
           (16, 26, "The state ring and the bearing-to-target arrow circle TOGETHER — the network remembers where the target is"),
           (26, 99, "Chart: neuron n0 overlaps sin(bearing) — |r|=0.96 on this take (descriptive); only T1/T2 (PROVED) on screen")]
    idx = len(blocks) + 1
    for (a, b, txt) in ak5:
        if a >= dur5:
            continue
        blocks.append(f"{idx}\n{srt_time(t5 + a)} --> {srt_time(t5 + min(b, dur5))}\n{txt}")
        idx += 1
    t_pl = sum(lens) / 10.0
    blocks.append(f"{idx}\n{srt_time(t_pl)} --> {srt_time(t_pl + 9.0)}\n"
                  "LiquidPatrol — PX4/Gazebo SITL. Zero zone breaches and zero false refusals "
                  "across ~140 boots. Controller: a 20-neuron liquid network — 48/48 vs GRU 29/48 "
                  "on the same grid. Decoys: recognised by behaviour — zero false alarms. "
                  "Controller: 20 neurons with PROVED boundedness theorems (T1/T2), activations "
                  "auditable by replay. Home hardware, evenings and weekends.")
    open(os.path.join(outd, "DEMO_C_v5_en.srt"), "w").write("\n\n".join(blocks) + "\n")
    print(f"[cut_v5] akty {[round(x/10,1) for x in lens]} + plansza 9 s = "
          f"{sum(lens)/10+9:.1f} s → {out}")


def main():
    mode = sys.argv[1]
    if mode == "brain-clip":
        segs = [(float(a), float(b), float(c)) for a, b, c in
                (s.split(":") for s in sys.argv[6].split(","))]
        brain_clip(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], segs)
    elif mode == "akt5":
        segs = [(float(a), float(b), float(c)) for a, b, c in
                (s.split(":") for s in sys.argv[7].split(","))]
        render_akt5(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], segs)
    elif mode == "cut":
        cut(sys.argv[2:8], sys.argv[8])


if __name__ == "__main__":
    main()
