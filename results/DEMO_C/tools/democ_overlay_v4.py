#!/usr/bin/env python3
"""results/DEMO_C/tools/democ_overlay_v4.py — AKT 5 „W głowie sieci" + montaż v4
(PROMPT_DEMOC_V4). NOWY plik; v1–v3.1 NIETYKALNE. Zero bootów: źródło = ujęcie
AKTU 2 (boot d2_akty12, epizod c10_s02 — te same klatki i demo.jsonl),
aktywacje odtworzone replayem (xai_replay ac9551ab IMPORTEM, wagi 0337d5ea).

Tryby:
  pca-base <out.json>  — baza PCA KORPUSU ATLASU (48 ep. LIQ NCP po erratum,
      indeks erratum_sweep.json — ten sam korpus co xai_atlas; loadings nie są
      zapisane w JSON-ach atlasu literą, więc przeliczenie DETERMINISTYCZNE:
      pula h na tickach inferencji → centrowanie → SVD; znak składowej
      ustalony: element o max |ładunku| dodatni). KOTWICA BAZY: frakcje
      wariancji top5 muszą równać się xai_atlas_ncp.json b_pca.var_top5
      co do 4 miejsc (asercja) — inaczej STOP.
  akt5 <bootdir> <sid> <akt2_v2.mp4> <pca_base.json> <out.mp4> <segmenty>
      — render AKTU 5: lewa połowa = klatki gotowego klipu akt2_v2 (×0.5,
      indeks = round(trel·10), sekwencyjnie; w segmencie TEMPO ×0.5 klatka
      duplikowana — podpisane plakietką); prawa połowa: (1) przestrzeń stanu
      h(t)→PCA (kolor per faza z demo: scan=hold/approach/orbit; ogon 8 s),
      (2) pasek 20 neuronów z rolami ATLASU (n0 sin_brg 0.953 / n5 cos_brg
      0.892 / n11 rel_x 0.913 — „role z korelacji (opisowe)"),
      (3) linia twierdzeń WYŁĄCZNIE T1/T2 (zasada cytowania FREEZE_XAI).
      Napis uczciwości cały akt + KOTWICA TEGO ujęcia (p95 |Δv| liczona
      w locie przez anchor_stats; p95>1e-2 ⇒ RuntimeError STOP).
  cut <v31.mp4> <akt5.mp4> <out_dir> — DEMO_C_v4.mp4 = v3.1 bez planszy
      (1570 klatek) + AKT 5 + plansza v4 (tekst v3.1 + linia T1/T2) +
      DEMO_C_v4_en.srt (NOWY plik — edycja DEMO_C_en.srt zakazana literą
      „zero edycji istniejących"; odchylenie nazwane w dopisku).
"""
import json
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
from xai_replay import load_eps, replay_episode, anchor_stats   # FROZEN ac9551ab

F_BIG = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
F_T = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 54)
F_B28 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
F_MED = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
F_M38 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 38)
F_SML = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
F_S18 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)

ROLE_EKRAN = [(0, "kierunek na cel (sin)", 0.953),
              (5, "kierunek na cel (cos)", 0.892),
              (11, "cel względny N (rel_x)", 0.913)]   # xai_atlas_ncp.json c_role
# BGR (cv2); PIL dostaje reversed() → RGB. Konwencja ATLASU: approach=niebieski, orbita=pomarańcz.
FAZA_COL = {"hold": (150, 150, 160), "approach": (255, 160, 90), "orbit": (60, 165, 255)}
FAZA_PL = {"hold": "scan", "approach": "approach", "orbit": "orbita"}

CAPTIONS5 = [(0.0, 7.0, "AKT 5 — W GŁOWIE SIECI: te same klatki co akt 2; stan 20 neuronów odtworzony replayem"),
             (7.0, 16.0, "Prawo: trajektoria stanu sieci w 2 osiach PCA — skan stoi, akwizycja rusza trajektorię"),
             (16.0, 26.0, "Wejście w orbitę: trajektoria stanu ZWIJA SIĘ W PIERŚCIEŃ — stabilny cykl = decyzja «krążę»"),
             (26.0, 99.0, "Pasek: aktywacje 20 neuronów (role z korelacji, opisowe); T1/T2 — jedyne twierdzenia na ekranie")]

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


def atlas_index():
    d = json.load(open(os.path.join(ROOT, "results", "POSCIG_RECON", "erratum_sweep.json")))
    out = []
    for c in d["cases"]:
        if ":ncp:" in c["label"]:
            out.append({"dir": os.path.join(ROOT, c["dir"]), "eid": c["episode_id"],
                        "sid": c["scenario_id"]})
    out.sort(key=lambda e: e["sid"])
    return out


def pca_base(out_json):
    Hs = []
    for c in atlas_index():
        eps = load_eps(c["dir"])
        k = max(kk for kk in eps if kk[0] == c["eid"])
        r = replay_episode(eps[k], "ncp", fantom=False)
        Hs.append(r["h"][r["infer"]])
    H = np.concatenate(Hs)
    mean = H.mean(0)
    U, s, Vt = np.linalg.svd(H - mean, full_matrices=False)
    var = s ** 2 / (s ** 2).sum()
    atl = json.load(open(os.path.join(ROOT, "results", "XAI_RECON", "xai_atlas_ncp.json")))
    ref = atl["b_pca"]["var_top5"]
    got = [round(float(v), 4) for v in var[:5]]
    assert all(abs(a - b) <= 5e-5 for a, b in zip(got, ref)), \
        f"KOTWICA BAZY PCA: {got} vs atlas {ref}"
    comp = Vt[:2].copy()
    for i in range(2):                      # determinizm znaku
        j = int(np.argmax(np.abs(comp[i])))
        if comp[i, j] < 0:
            comp[i] *= -1
    out = {"zrodlo": "pula h tickow inferencji 48 ep. LIQ NCP (indeks erratum_sweep, "
                     "ten sam korpus co xai_atlas_ncp); SVD po centrowaniu; znak: max|ładunek| dodatni",
           "n_tick": int(len(H)), "mean": [round(float(v), 6) for v in mean],
           "comp": [[round(float(v), 6) for v in row] for row in comp],
           "var_frac_top5": got, "kotwica_atlas_var_top5": ref,
           "var_top2_pct": round(100 * float(var[0] + var[1]), 1)}
    json.dump(out, open(out_json, "w"), indent=1)
    print(f"[pca-base] n_tick={out['n_tick']} var_top2={out['var_top2_pct']}% "
          f"kotwica OK → {out_json}")


def render_akt5(bootdir, sid, clip_v2, base_json, out_mp4, segments):
    base = json.load(open(base_json))
    mean = np.array(base["mean"]); comp = np.array(base["comp"])
    eps = load_eps(bootdir)
    k = [kk for kk in eps if eps[kk][0]["scenario_id"] == sid][0]
    rep = replay_episode(eps[k], "ncp", fantom=True)     # net_fantom — wzór kotwicy
    st = anchor_stats(rep)
    assert st["p95"] <= 1e-2, f"STOP: kotwica ujęcia p95={st['p95']} > 1e-2"
    print(f"[akt5] kotwica ujęcia {sid}: p50={st['p50']:.2e} p95={st['p95']:.2e} "
          f"max={st['max']:.2e} hold_rozjazd={st['max_hold']}")
    t0 = rep["t"][0]
    P = (rep["h"] - mean) @ comp.T                        # (T,2) projekcja
    lim = float(np.abs(P).max()) * 1.12 + 1e-6
    tt = rep["t"]

    cap = cv2.VideoCapture(clip_v2)
    n_clip = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cur = -1
    frame_small = None

    plan = []
    for (a, b, sp) in segments:
        t = t0 + a
        while t <= t0 + b:
            plan.append((t, sp))
            t += 0.1 * sp
    vw = cv2.VideoWriter(out_mp4, cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (1920, 1080))
    W2, H2 = 960, 540

    def px(p, x0, y0, w, h):
        return (int(x0 + (p[0] + lim) / (2 * lim) * w),
                int(y0 + h - (p[1] + lim) / (2 * lim) * h))

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
            canvas[214:214 + H2, 0:W2] = frame_small
            cv2.rectangle(canvas, (0, 214), (W2 - 1, 214 + H2 - 1), (70, 70, 80), 1)
        # --- panel przestrzeni stanu (prawa góra) ---
        x0, y0, wP, hP = 1000, 70, 880, 520
        cv2.rectangle(canvas, (x0 - 10, y0 - 10), (x0 + wP + 10, y0 + hP + 10), (40, 40, 46), -1)
        cv2.rectangle(canvas, (x0 - 10, y0 - 10), (x0 + wP + 10, y0 + hP + 10), (80, 80, 90), 1)
        cv2.line(canvas, px((0, -lim), x0, y0, wP, hP), px((0, lim), x0, y0, wP, hP), (55, 55, 62), 1)
        cv2.line(canvas, px((-lim, 0), x0, y0, wP, hP), px((lim, 0), x0, y0, wP, hP), (55, 55, 62), 1)
        i_now = int(np.searchsorted(tt, t_abs, side="right")) - 1
        # ślad skumulowany (wygaszony) — pierścień buduje się na ekranie;
        # jasny ogon 8 s na wierzchu (dodatek montażowy nazwany w dopisku)
        for i in range(1, max(i_now, 1), 2):
            col = FAZA_COL.get(rep["phase"][i], (120, 120, 120))
            c = tuple(int(ch * 0.30 + 40 * 0.7) for ch in col)
            cv2.circle(canvas, px(P[i], x0, y0, wP, hP), 1, c, -1)
        i_lo = int(np.searchsorted(tt, t_abs - 8.0))
        for i in range(max(i_lo, 1), max(i_now, 1)):
            a = (tt[i] - (t_abs - 8.0)) / 8.0
            col = FAZA_COL.get(rep["phase"][i], (120, 120, 120))
            c = tuple(int(ch * (0.25 + 0.75 * a)) for ch in col)
            cv2.line(canvas, px(P[i - 1], x0, y0, wP, hP), px(P[i], x0, y0, wP, hP), c, 2, cv2.LINE_AA)
        if i_now >= 0:
            q = px(P[i_now], x0, y0, wP, hP)
            cv2.circle(canvas, q, 7, FAZA_COL.get(rep["phase"][i_now], (200, 200, 200)), -1, cv2.LINE_AA)
        # --- pasek neuronów (prawa, środek-dół) ---
        bx, by, bw, bh = 1000, 680, 880, 150
        cv2.rectangle(canvas, (bx - 10, by - 34), (bx + bw + 10, by + bh + 58), (40, 40, 46), -1)
        if i_now >= 0:
            hvec = rep["h"][i_now]
            slot = bw // 20
            for j in range(20):
                v = float(hvec[j])
                xj = bx + j * slot + 6
                mid = by + bh // 2
                hh = int(abs(v) * (bh // 2 - 2))
                col = (90, 90, 255) if v > 0 else (255, 150, 80)   # BGR: + czerwonawy / − niebieskawy
                y1 = mid - hh if v > 0 else mid
                cv2.rectangle(canvas, (xj, y1), (xj + slot - 12, y1 + hh), col, -1)
                cv2.line(canvas, (bx, mid), (bx + bw, mid), (90, 90, 100), 1)
        img = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
        d = ImageDraw.Draw(img, "RGBA")
        # top bar
        d.rectangle([0, 0, 1920, 56], fill=(0, 0, 0, 210))
        put(d, (16, 4), "AKT 5 — W GŁOWIE SIECI", F_BIG, (255, 220, 90))
        put(d, (700, 14), f"epizod {sid} (ujęcie aktu 2) · zegar {trel:5.1f} s", F_MED)
        if speed != 1.0:
            d.rectangle([1600, 4, 1904, 52], fill=(0, 0, 0, 220))
            put(d, (1620, 8), f"TEMPO ×{speed:g}", F_BIG, (255, 160, 60))
        # podpisy panelu stanu
        put(d, (1000, 598), f"PRZESTRZEŃ STANU h(t)∈R²⁰ → PCA · 2 osie = {base['var_top2_pct']}% wariancji (pomiar atlasu)",
            F_S18, (190, 190, 200))
        ph_now = rep["phase"][i_now] if i_now >= 0 else "hold"
        put(d, (1016, 86), "faza:", F_SML, (150, 150, 160))
        put(d, (1080, 84), FAZA_PL.get(ph_now, ph_now), F_B28,
            tuple(reversed(FAZA_COL.get(ph_now, (200, 200, 200)))))
        lx = 1420
        for phk in ("hold", "approach", "orbit"):
            col = tuple(reversed(FAZA_COL[phk]))
            d.rectangle([lx, 92, lx + 16, 108], fill=col)
            put(d, (lx + 22, 88), FAZA_PL[phk], F_S18, col)
            lx += 150
        if ph_now == "orbit" and 10.0 <= trel <= 24.0:
            put(d, (1090, 520), "stabilny cykl = decyzja «krążę»", F_B28, (255, 200, 90))
        # podpisy paska neuronów
        put(d, (1000, 652), "AKTYWACJE 20 NEURONÓW (h_i z replayu)", F_SML, (190, 190, 200))
        for (j, rola, r) in ROLE_EKRAN:
            xj = 1000 + j * (880 // 20) + 6
            d.line([xj + 7, 836, xj + 7, 848], fill=(220, 220, 230), width=1)
        put(d, (1000, 852), "n0: kierunek na cel (sin) |r|=0.95 · n5: (cos) |r|=0.89 · "
                            "n11: cel względny N |r|=0.91", F_S18, (190, 190, 200))
        put(d, (1000, 876), "role z korelacji (opisowe)", F_S18, (150, 150, 160))
        # linia twierdzeń (stała)
        d.rectangle([0, 912, 1920, 960], fill=(10, 10, 24, 235))
        put(d, (24, 920), "dowiedzione: |komenda| < 3 m/s (T1) · stan ograniczony |h|<1 (T2)"
                          " — status PROVED, różnicówka 0/74 708 ticków", F_B28, (120, 255, 160))
        # napis uczciwości + kotwica ujęcia
        d.rectangle([0, 962, 1920, 1016], fill=(0, 0, 0, 200))
        put(d, (24, 966), "aktywacje odtworzone deterministycznie z zapisu lotu (replay) — "
                          "nakładka nie steruje dronem", F_SML, (255, 200, 120))
        put(d, (24, 990), f"kotwica tego ujęcia: p95 |Δv_replay − Δv_log| = "
                          f"{st['p95'] * 1000:.1f}·10⁻³ m/s (max {st['max'] * 1000:.1f}·10⁻³)",
            F_SML, (255, 200, 120))
        tk = n / 10.0
        c5 = next((c[2] for c in CAPTIONS5 if c[0] <= tk < c[1]), None)
        if c5:
            d.rectangle([0, 1020, 1920, 1080], fill=(0, 0, 0, 220))
            put(d, (24, 1032), c5, F_MED)
        vw.write(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))
        n += 1
    vw.release()
    cap.release()
    print(f"[akt5] {n} klatek → {out_mp4}")
    return st


def srt_time(t):
    ms = int(round((t - int(t)) * 1000))
    s = int(t)
    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d},{ms:03d}"


def cut(v31, akt5, outd):
    out = os.path.join(outd, "DEMO_C_v4.mp4")
    vw = cv2.VideoWriter(out, cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (1920, 1080))
    c = cv2.VideoCapture(v31)
    n31 = 0
    while n31 < 1570:                      # v3.1 bez planszy (9 s = 90 klatek)
        ok, fr = c.read()
        if not ok:
            break
        vw.write(fr)
        n31 += 1
    c.release()
    c = cv2.VideoCapture(akt5)
    n5 = 0
    while True:
        ok, fr = c.read()
        if not ok:
            break
        vw.write(fr)
        n5 += 1
    c.release()
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
    total = (n31 + n5 + 90) / 10.0
    # SRT: bloki v3.1 verbatim (plik DEMO_C_v31_en.srt) z przesuniętą planszą + bloki aktu 5
    src = open(os.path.join(outd, "DEMO_C_v31_en.srt")).read().strip().split("\n\n")
    t5 = n31 / 10.0
    blocks = [b for b in src[:-1]]          # bez bloku planszy v3.1
    ak5 = [(0, 7, "ACT 5 — INSIDE THE NETWORK: same footage as act 2; the 20-neuron state replayed deterministically"),
           (7, 16, "Right: network state trajectory in 2 PCA axes (87.8% of variance, atlas measurement)"),
           (16, 26, "Orbit entry: the state trajectory CURLS INTO A RING — a stable cycle = the decision to circle"),
           (26, 99, "Bar: 20 neuron activations (roles from correlations, descriptive); only T1/T2 on screen — both PROVED")]
    idx = len(blocks) + 1
    dur5 = n5 / 10.0
    for (a, b, txt) in ak5:
        if a >= dur5:
            continue
        blocks.append(f"{idx}\n{srt_time(t5 + a)} --> {srt_time(t5 + min(b, dur5))}\n{txt}")
        idx += 1
    t_pl = (n31 + n5) / 10.0
    blocks.append(f"{idx}\n{srt_time(t_pl)} --> {srt_time(t_pl + 9.0)}\n"
                  "LiquidPatrol — PX4/Gazebo SITL. Zero zone breaches and zero false refusals "
                  "across ~140 boots. Controller: a 20-neuron liquid network — 48/48 vs GRU 29/48 "
                  "on the same grid. Decoys: recognised by behaviour — zero false alarms. "
                  "Controller: 20 neurons with PROVED boundedness theorems (T1/T2), activations "
                  "auditable by replay. Home hardware, evenings and weekends.")
    open(os.path.join(outd, "DEMO_C_v4_en.srt"), "w").write("\n\n".join(blocks) + "\n")
    print(f"[cut_v4] {n31 / 10:.1f} + {n5 / 10:.1f} + 9.0 = {total:.1f} s → {out}")


def main():
    mode = sys.argv[1]
    if mode == "pca-base":
        pca_base(sys.argv[2])
    elif mode == "akt5":
        segs = [(float(a), float(b), float(c)) for a, b, c in
                (s.split(":") for s in sys.argv[7].split(","))]
        render_akt5(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], segs)
    elif mode == "cut":
        cut(sys.argv[2], sys.argv[3], sys.argv[4])


if __name__ == "__main__":
    main()
