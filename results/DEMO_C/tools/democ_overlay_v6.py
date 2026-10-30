#!/usr/bin/env python3
"""results/DEMO_C/tools/democ_overlay_v6.py — montaż v6: AKT 6 „Wiatr" + errata planszy
(PROMPT_DEMOC_V6 §2–§4). NOWY plik; v1–v5 NIETYKALNE (importowane wyłącznie READ-ONLY:
democ_topdown.Panel, helpery democ_overlay_v2, mini-mózg democ_overlay_v5 → xai_replay
ac9551ab FROZEN).

Układ aktu 6 = akty 1–2 (panel taktyczny z góry 640×640 + HUD kompaktowy + kamera
pokładowa ×2 nearest-neighbor z ramkami det_v2 z percep_feed) + mini-mózg „ta sieć
PROWADZI lot" (replay; kotwica ujęcia asercją p95 ≤ 1e-2) oraz trzy elementy §2:
  1. STRZAŁKA WIATRU na panelu — z LITERY świata world_wk3_p2 (RECON_WK3 §R1, wzór
     1:1 z wk3_gust.py 12ea2f2f): |w| = W0(1 + A sin(2π t/Pm)), θ = Ad sin(2π t/Pd) [deg],
     ENU w kierunku +x ⇒ w_NED = (|w| sin θ, |w| cos θ); t = t_sim (zegar świata od 0,
     ten sam co trace/ulog — most czasu RECON_WK §R3). P2: W0 2, A 0.8, Pm 4, Ad 30, Pd 11.
  2. WSKAŹNIK PRZECHYŁU z zapisu lotu: vehicle_attitude ulogu (wczytanie wk2_k.load
     09e4b440 importem), przechył = acos(R[2,2]); bieżący + maks. w epizodzie DOTĄD
     (statystyka wyłącznie w oknie epizodu — lekcja ANEKS_WK3-1 §3).
  3. PASEK PORYWU: |w|(t) z litery, ostatnie 20 s, znacznik „teraz".

Tryby:
  akt6 <bootdir> <sid> <out.mp4> <segmenty a:b:sp,...>
  cut <v5.mp4> <akt6.mp4> <out_dir>          (v5 bez planszy + akt 6 + plansza v6 + srt EN)
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
for p in (ROOT, HERE, os.path.join(ROOT, "results", "WK2_RECON", "tools")):
    if p not in sys.path:
        sys.path.insert(0, p)
from bench import scenarios as S  # noqa: E402
from democ_topdown import Panel  # noqa: E402
from democ_overlay_v2 import iter_jsonl, nearest, put  # noqa: E402
from democ_overlay_v5 import rep_of, top_edges, draw_brain, srt_time  # noqa: E402
from xai_replay import anchor_stats, model_of  # noqa: E402
from r02.mti import quat_to_R  # noqa: E402
from wk2_k import load as ulog_load  # noqa: E402

MAN = json.load(open(os.path.join(ROOT, "results", "BENCH", "scenario_manifest.json")))
SCEN = {e["scenario_id"]: e for e in MAN["episodes"]}
F_T = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 54)
F_BIG = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
F_B36 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
F_B28 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
F_MED = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
F_M38 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 38)
F_SML = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
F_S18 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
F_S15 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)

# litera świata world_wk3_p2 (RECON_WK3 R2, profil ostry; e47ef380)
W0, A_M, P_M, A_D, P_D = 2.0, 0.8, 4.0, 30.0, 11.0
STRIP_S = 20.0

HONESTY = ("świat z oporem aerodynamicznym skalibrowanym do fizyki (k ≈ 0.49 /s); "
           "wiatr zmienny o znanym profilu, nie turbulencja")
WIND_LABEL = "wiatr: profil z litery świata — 0.4–3.6 m/s, kierunek ±30°"
FINAL_CAP = "pod wiatrem: łagodne 8/8, ostre 7/8 — jedyna porażka to spóźnione rozpoznanie celu"


def captions6(dur):
    return [(0.0, 8.0, "AKT 6 — WIATR: ta sama sieć, uczona bez wiatru i bez oporu"),
            (8.0, 17.0, "porywy do 3.6 m/s, kierunek wędruje o ±30°"),
            (17.0, dur - 9.0, "orbita trzyma: dystans 6–10 m przez całe okno"),
            (dur - 9.0, 999.0, FINAL_CAP)]


def wind(t):
    """Litera świata: (|w| m/s, θ deg, w_N, w_E)."""
    m = W0 * (1.0 + A_M * math.sin(2 * math.pi * t / P_M))
    th = A_D * math.sin(2 * math.pi * t / P_D)
    r = math.radians(th)
    return m, th, m * math.sin(r), m * math.cos(r)


def plan_of(t0, segments):
    plan = []
    for (a, b, sp) in segments:
        t = t0 + a
        while t <= t0 + b + 1e-9:
            plan.append((t, sp))
            t += 0.1 * sp
    return plan


def episode_bounds(bootdir, sid):
    t0 = t1 = None
    for r in iter_jsonl(os.path.join(bootdir, "trace.jsonl")):
        if r.get("t") != "event":
            continue
        if r.get("ev") == "episode_start" and r.get("scenario_id") == sid:
            t0 = r["t0_sim"]
        elif r.get("ev") == "episode_end" and t0 is not None and t1 is None and r["sim"] > t0:
            t1 = r["sim"]
    assert t0 is not None and t1 is not None, f"brak granic epizodu {sid}"
    return t0, t1


def tilt_series(bootdir, t0, t1):
    att, _lp = ulog_load(os.path.join(bootdir, "boot.ulg"))
    ts = np.asarray(att[0], dtype=float) * 1e-6
    m = (ts >= t0) & (ts <= t1)
    tilt = np.array([math.degrees(math.acos(max(-1.0, min(1.0, float(quat_to_R(q)[2, 2])))))
                     for q in np.asarray(att[1])[m]])
    return ts[m], tilt


def draw_wind_arrow(panel_img, t):
    """Strzałka wiatru w prawym dolnym rogu panelu, poza okręgiem R_E (N↑, E→; długość ∝ |w|,
    3.6 m/s = 56 px). Kolor BGR (255, 230, 90) = cyjan, jak napisy wiatru."""
    mag, th, wn, we = wind(t)
    cx, cy = 560, 556
    cv2.circle(panel_img, (cx, cy), 60, (60, 60, 70), 1, cv2.LINE_AA)
    s = 56.0 / 3.6
    tip = (int(cx + we * s), int(cy - wn * s))
    cv2.arrowedLine(panel_img, (cx, cy), tip, (255, 230, 90), 3, cv2.LINE_AA, tipLength=0.28)
    # stopka panelu nadpisywana w PIL (cv2.putText nie renderuje „·" — w democ_topdown wychodzi „??")
    cv2.rectangle(panel_img, (2, 612), (420, 636), (26, 26, 26), -1)
    return mag, th


def draw_strip(canvas, region, t):
    """|w|(t) z litery, ostatnie 20 s; „teraz" na prawej krawędzi."""
    x0, y0, w, h = region
    cv2.rectangle(canvas, (x0, y0), (x0 + w, y0 + h), (40, 40, 48), -1)
    def ypx(v):
        return int(y0 + h - v / 4.0 * h)
    for v in (0.4, 2.0, 3.6):
        cv2.line(canvas, (x0, ypx(v)), (x0 + w, ypx(v)), (70, 70, 82), 1)
    pts = []
    for k in range(w + 1):
        tt = t - STRIP_S + STRIP_S * k / w
        pts.append((x0 + k, ypx(wind(tt)[0])))
    cv2.polylines(canvas, [np.array(pts, np.int32)], False, (255, 230, 90), 2, cv2.LINE_AA)
    cv2.line(canvas, (x0 + w, y0), (x0 + w, y0 + h), (255, 255, 255), 2)
    cv2.circle(canvas, pts[-1], 6, (255, 255, 255), -1, cv2.LINE_AA)


def render_akt6(bootdir, sid, out_mp4, segments):
    t0, t1 = episode_bounds(bootdir, sid)
    rep, _rows = rep_of(bootdir, sid)
    st = anchor_stats(rep)
    assert st["p95"] <= 1e-2, f"STOP: kotwica ujęcia p95={st['p95']}>1e-2"
    print(f"[akt6] kotwica replayu {sid}: p50={st['p50']:.2e} p95={st['p95']:.2e} max={st['max']:.2e}")
    tt_rep = rep["t"]
    edges = top_edges(model_of("ncp"))
    tl_t, tl_v = tilt_series(bootdir, t0, t1)
    print(f"[akt6] przechył w oknie epizodu: n={len(tl_v)} p50={np.median(tl_v):.1f} "
          f"max={tl_v.max():.1f} deg")
    demo = [r for r in iter_jsonl(os.path.join(bootdir, "demo.jsonl")) if r.get("scenario_id") == sid]
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
    panel = Panel(bootdir, sid, 1)
    ep = SCEN[sid]
    plan = plan_of(t0, segments)
    dur = len(plan) / 10.0
    caps = captions6(dur)
    vw = cv2.VideoWriter(out_mp4, cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (1920, 1080))
    n = 0
    n_cam = 0
    for (t_abs, speed) in plan:
        canvas = np.zeros((1080, 1920, 3), dtype=np.uint8)
        trel = t_abs - t0
        td = nearest(dts, t_abs, 0.2)
        drow = dmap.get(td) if td is not None else None
        dh = None
        if drow is not None and trel >= 0:
            g = S.position_at(ep, max(0.0, trel))
            op = drow["own_pos_ned"]
            dh = math.hypot(g[0] - op[0], g[1] - op[1])
        # kamera pokładowa — tor v2 1:1
        canvas[60:1020, 640:1920] = 128
        tcf = nearest(ck, t_abs, 0.08)
        if tcf is not None:
            n_cam += 1
            cam = cv2.imread(os.path.join(bootdir, "cam", "frames", cmap[tcf]))
            if cam.ndim == 2:
                cam = cv2.cvtColor(cam, cv2.COLOR_GRAY2BGR)
            tpf = nearest(pfk, tcf, 0.01)
            if tpf is not None and pf[tpf].get("box"):
                b = pf[tpf]["box"]
                mti = bool(pf[tpf].get("mti_ok"))
                cx, cy, w, h = b[0] * 640, b[1] * 480, b[2] * 640, b[3] * 480
                cv2.rectangle(cam, (int(cx - w / 2), int(cy - h / 2)), (int(cx + w / 2), int(cy + h / 2)),
                              (80, 255, 80) if mti else (60, 220, 255), 2)
            canvas[60:1020, 640:1920] = cv2.resize(cam, (1280, 960), interpolation=cv2.INTER_NEAREST)
        # panel taktyczny + strzałka wiatru (litera świata)
        pimg = panel.draw(t_abs, 640, 640)
        mag, th = draw_wind_arrow(pimg, t_abs)
        canvas[56:696, 0:640] = pimg
        # mini-mózg (replay) — region jak v5
        i = min(max(int(np.searchsorted(tt_rep, t_abs, side="right")) - 1, 0), len(tt_rep) - 1)
        reg = (1596, 736, 312, 236)
        draw_brain(canvas, reg, rep["h"][i], rep["y"][i], None, edges, mini=True)
        # pasek porywu (HUD; tło HUD w cv2, żeby nie przykryło paska)
        canvas[696:1020, 0:640] = (20, 10, 10)
        strip = (24, 930, 592, 70)
        draw_strip(canvas, strip, t_abs)
        # przechył z zapisu lotu
        j = int(np.searchsorted(tl_t, t_abs, side="right")) - 1
        tilt_now = float(tl_v[j]) if j >= 0 else None
        tilt_max = float(tl_v[:j + 1].max()) if j >= 0 else None
        # HUD + napisy (PIL)
        img = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle([0, 0, 1920, 56], fill=(0, 0, 0, 200))
        put(d, (16, 6), "AKT 6", F_BIG, (255, 220, 90))
        put(d, (190, 14), f"epizod {sid} · świat world_wk3_p2 · zegar {trel:6.1f} s", F_MED)
        d.rectangle([640, 60, 1920, 92], fill=(0, 0, 0, 170))
        put(d, (656, 64), HONESTY, F_S18, (255, 200, 120))
        put(d, (10, 62), WIND_LABEL, F_S15, (150, 200, 220))
        put(d, (452, 56 + 462), f"wiatr {mag:.1f} m/s", F_S18, (90, 230, 255))
        put(d, (452, 56 + 484), f"kierunek {th:+.0f}°", F_S15, (90, 230, 255))
        put(d, (452, 56 + 620), "strzałka = dokąd wieje", F_S15, (150, 200, 220))
        put(d, (10, 56 + 614), "panel taktyczny (GT) · siatka 5 m", F_S15, (150, 150, 160))
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
        put(d, (24, 704), "FAZA", F_SML, (150, 150, 160))
        put(d, (24, 728), faza, F_B28, (120, 220, 255))
        put(d, (380, 704), "DYSTANS (GT)", F_SML, (150, 150, 160))
        put(d, (380, 728), f"{dh:5.1f} m" if dh is not None else "—", F_B28)
        put(d, (24, 782), "PRZECHYŁ", F_SML, (150, 150, 160))
        if tilt_now is not None:
            put(d, (24, 806), f"{tilt_now:4.1f}°", F_B36, (255, 255, 255))
            put(d, (190, 818), f"maks. w epizodzie dotąd {tilt_max:4.1f}°", F_SML, (200, 200, 210))
        put(d, (24, 856), "przechył z zapisu lotu", F_S15, (130, 130, 140))
        put(d, (24, 896), f"PORYW |w| — ostatnie {STRIP_S:.0f} s (litera świata)", F_SML, (150, 150, 160))
        put(d, (556, 900), "teraz", F_S15, (255, 255, 255))
        put(d, (24 + 4, strip[1] + 2), "3.6", F_S15, (110, 110, 125))
        put(d, (24 + 4, strip[1] + strip[3] - 18), "0.4", F_S15, (110, 110, 125))
        put(d, (reg[0] + 8, reg[1] + 4), "W GŁOWIE SIECI — ta sieć PROWADZI lot", F_S15, (255, 220, 120))
        put(d, (reg[0] + 8, reg[1] + reg[3] - 22), "panel = replay zapisu (nie steruje)",
            F_S15, (200, 180, 140))
        if speed != 1.0:
            d.rectangle([1600, 4, 1904, 52], fill=(0, 0, 0, 220))
            put(d, (1620, 8), f"TEMPO ×{speed:g}", F_BIG, (255, 160, 60))
        tk = n / 10.0
        cap = next((c[2] for c in caps if c[0] <= tk < c[1]), None)
        if cap:
            d.rectangle([0, 1020, 1920, 1080], fill=(0, 0, 0, 220))
            put(d, (24, 1032), cap, F_MED)
        vw.write(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))
        n += 1
    vw.release()
    print(f"[akt6] {sid}: {n} klatek ({dur:.1f} s), klatki kamery {n_cam}/{n} → {out_mp4}")
    return {"klatek": n, "dur_s": dur, "kotwica": st, "tilt_max_ep": float(tl_v.max()),
            "tilt_p50_ep": float(np.median(tl_v))}


# plansza v4 (democ_overlay_v5.PLANSZA) z erratą §3 (linia wabików FROZEN, łamana na 2 wiersze
# bez zmiany słowa) + linia wiatru przed wierszem zamykającym
PLANSZA6 = ["LiquidPatrol — PX4/Gazebo SITL.",
            "Zero naruszeń strefy i zero błędnych odmów w ~140 bootach.",
            "Sterownik: płynna sieć 20 neuronów — 48/48 vs GRU 29/48",
            "na tej samej siatce.",
            "Wabiki: rozpoznawane po zachowaniu — zero fałszywych alarmów na celach atakujących;",
            "wolny cel, który tylko krąży, pozostaje nierozróżnialny.",
            "Sterownik: 20 neuronów — dowiedzione twierdzenia o ograniczoności (T1/T2),",
            "aktywacje audytowalne replayem.",
            "Wiatr zmienny do 3.6 m/s na kamerze: 15/16 misji.",
            "Domowy sprzęt, wieczory i weekendy."]
COL6 = {4: (255, 190, 120), 5: (255, 190, 120), 6: (120, 255, 160), 7: (120, 255, 160),
        8: (90, 230, 255)}


def cut(v5_mp4, akt6_mp4, outd):
    out = os.path.join(outd, "DEMO_C_v6.mp4")
    vw = cv2.VideoWriter(out, cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (1920, 1080))
    c = cv2.VideoCapture(v5_mp4)
    n5 = int(c.get(cv2.CAP_PROP_FRAME_COUNT))
    keep = n5 - 90  # v5 = akty 1–5 + plansza v4 9 s (90 klatek) — plansza odcięta
    k5 = 0
    while k5 < keep:
        ok, fr = c.read()
        if not ok:
            break
        vw.write(fr); k5 += 1
    c.release()
    assert k5 == keep, f"v5: przeczytano {k5} z {keep}"
    c = cv2.VideoCapture(akt6_mp4); k6 = 0
    while True:
        ok, fr = c.read()
        if not ok:
            break
        vw.write(fr); k6 += 1
    c.release()
    img = Image.new("RGB", (1920, 1080), (8, 10, 16))
    d = ImageDraw.Draw(img)
    y = 200
    for i, ln in enumerate(PLANSZA6):
        f = F_T if i == 0 else F_M38
        w = d.textlength(ln, font=f)
        assert w <= 1880, f"linia planszy za szeroka: {ln}"
        d.text(((1920 - w) / 2, y), ln, font=f,
               fill=(255, 220, 90) if i == 0 else COL6.get(i, (235, 235, 235)))
        y += 92 if i == 0 else 62
    pl = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    for _ in range(90):
        vw.write(pl)
    vw.release()
    cv2.imwrite(os.path.join(outd, "clips", "plansza_v6.png"), pl)
    # SRT: bloki v5 bez planszy + akt 6 + plansza v6
    src = open(os.path.join(outd, "DEMO_C_v5_en.srt")).read().strip().split("\n\n")
    blocks = src[:-1]
    t6 = k5 / 10.0
    dur6 = k6 / 10.0
    ak6 = [(0, 8, "ACT 6 — WIND: the same network, trained with no wind and no drag"),
           (8, 17, "Gusts up to 3.6 m/s, the direction swings by ±30°"),
           (17, dur6 - 9, "The orbit holds: 6–10 m distance through the whole window"),
           (dur6 - 9, dur6, "Under wind: mild profile 8/8, sharp 7/8 — the only failure was late target recognition")]
    idx = len(blocks) + 1
    for (a, b, txt) in ak6:
        blocks.append(f"{idx}\n{srt_time(t6 + a)} --> {srt_time(t6 + b)}\n{txt}")
        idx += 1
    t_pl = (k5 + k6) / 10.0
    blocks.append(f"{idx}\n{srt_time(t_pl)} --> {srt_time(t_pl + 9.0)}\n"
                  "LiquidPatrol — PX4/Gazebo SITL. Zero zone breaches and zero false refusals "
                  "across ~140 boots. Controller: a 20-neuron liquid network — 48/48 vs GRU 29/48 "
                  "on the same grid. Decoys: recognised by behaviour — zero false alarms on attacking "
                  "targets; a slow target that only circles remains indistinguishable. Controller: "
                  "20 neurons with PROVED boundedness theorems (T1/T2), activations auditable by replay. "
                  "Time-varying wind up to 3.6 m/s on camera: 15/16 missions. "
                  "Home hardware, evenings and weekends.")
    open(os.path.join(outd, "DEMO_C_v6_en.srt"), "w").write("\n\n".join(blocks) + "\n")
    tot = (k5 + k6) / 10.0 + 9.0
    print(f"[cut_v6] v5 bez planszy {k5 / 10:.1f} s + akt 6 {dur6:.1f} s + plansza 9 s = {tot:.1f} s → {out}")
    assert tot <= 250.0, f"całość {tot:.1f} s > 250 s"


def main():
    mode = sys.argv[1]
    if mode == "akt6":
        segs = [(float(a), float(b), float(c)) for a, b, c in
                (s.split(":") for s in sys.argv[5].split(","))]
        r = render_akt6(sys.argv[2], sys.argv[3], sys.argv[4], segs)
        print(json.dumps(r, default=float))
    elif mode == "cut":
        cut(sys.argv[2], sys.argv[3], sys.argv[4])


if __name__ == "__main__":
    main()
