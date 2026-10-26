#!/usr/bin/env python3
"""results/WABIK/tools/wabik_manifest_gen.py — generator manifestu WABIK
(PRE_WABIK §2.1; PROMPT_WABIK_S1 §1.3). NOWY plik results/WABIK/wabik_manifest.json;
istniejący results/BENCH/scenario_manifest.json NIETYKALNY (podpinanie przez env
BENCH_MANIFEST dopiero w scenariuszach M-*; smoke S1 leci na manifeście
DOMYŚLNYM — kotwica czystości 1:1).

Semantyka segmentów 1:1 z bench/scenarios.py (t0,t1,x0,y0,heading_deg,v; liniowa);
wszystkie prędkości ≤1.0 (liga R4). Parametry liczbowe JAWNIE niżej.

TRAJEKTORIE WABIKA (konsumuje wabik_motion.py):
  W-LOITER       — łuk ping-pong na promieniu R=10.0 m wokół home, sektor
                   azymutalny 140°→220° (przeciwny do intruza bearing 0°),
                   v=1.0, z=10; dh stałe 10 (nigdy <5).
  W-STYCZNY      — cięciwa o parametrze b=8.0 m: prosta przez (N=−16.12…+16.12,
                   E=−8.0), v=1.0; d_min=8 (nigdy <5); rezydencja 32.2 s (R4).
  W-ZBLIZ-ODSKOK — 3× (podejście radialne z r=15 do r=7 @az 200° + odskok do
                   r=15), v=1.0; dh_min=7 (nigdy <5).

SCENARIUSZE INTRUZA (episodes — czyta bench/intruder_motion przez BENCH_MANIFEST):
  M-LUK (episode_id 0, scenario_id m00_s01)      — łuk do home: polilinia 8×15°
                   po okręgu o R_c=10 m stycznie schodząca z r=15 do r≈4,
                   potem 2 krótkie segmenty w centrum; v=1.0.
  M-POD-ORBITA (episode_id 1, scenario_id m01_s01) — radialny z (15,0) 9 s
                   (r 15→6; ENTRY @k=1 zajdzie w pierwszych sekundach — zmiana
                   kursu PO ENTRY), potem kurs +90° (styczny) 14 s, powrót ku
                   home 10 s, odejście 10 s; v=1.0.
"""
import json
import math
import os

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "wabik_manifest.json")
Z = 10.0
V = 1.0


def seg(t0, x0, y0, heading_deg, dur, v=V):
    return {"t0": round(t0, 4), "t1": round(t0 + dur, 4), "x0": round(x0, 4),
            "y0": round(y0, 4), "heading_deg": round(heading_deg, 4), "v": v}


def polyline_from_points(pts, v=V, t0=0.0):
    segs = []
    t = t0
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        d = math.hypot(x1 - x0, y1 - y0)
        if d < 1e-6:
            continue
        hd = math.degrees(math.atan2(y1 - y0, x1 - x0))
        segs.append(seg(t, x0, y0, hd, d / v, v))
        t += d / v
    return segs, t


def arc_points(r, az0, az1, step_deg):
    n = max(2, int(abs(az1 - az0) / step_deg) + 1)
    return [(r * math.cos(math.radians(az0 + (az1 - az0) * k / (n - 1))),
             r * math.sin(math.radians(az0 + (az1 - az0) * k / (n - 1))))
            for k in range(n)]


# ---------------- trajektorie WABIKA ----------------
def w_loiter():
    pts = []
    for cyc in range(8):                      # ping-pong 140->220->140... — pelny epizod
        a, b = (140.0, 220.0) if cyc % 2 == 0 else (220.0, 140.0)
        p = arc_points(10.0, a, b, 10.0)
        pts.extend(p if not pts else p[1:])
    segs, t_end = polyline_from_points(pts)
    return {"opis": "łuk ping-pong R=10.0 m, sektor az 140-220 st, v=1.0; dh=10 stałe",
            "z": Z, "dur_s": round(t_end, 1), "segments": segs}


def w_styczny():
    b = 8.0
    half = math.sqrt(18.0 ** 2 - b ** 2)
    pts = [(-half, -b), (half, -b)]
    segs, t_end = polyline_from_points(pts)
    return {"opis": f"cięciwa b={b} m (N -{half:.2f}->+{half:.2f}, E=-{b}); d_min={b}",
            "z": Z, "dur_s": round(t_end, 1), "segments": segs}


def w_zbliz_odskok():
    az = 200.0
    ux, uy = math.cos(math.radians(az)), math.sin(math.radians(az))
    pts = []
    for _ in range(3):
        pts.extend([(15 * ux, 15 * uy), (7 * ux, 7 * uy)])
    pts.append((15 * ux, 15 * uy))
    segs, t_end = polyline_from_points(pts)
    return {"opis": "3x (radialne 15->7 m @az 200 st + odskok 7->15); dh_min=7",
            "z": Z, "dur_s": round(t_end, 1), "segments": segs}


# ---------------- scenariusze INTRUZA (episodes) ----------------
def m_luk():
    # łuk R_c=10: okrąg o środku (5,10) — styczny do promienia w (15,0)? Konstrukcja jawna:
    # punkty: start (15,0); łuk po okręgu środek C=(5,8.66) R=10 (przechodzi przez (15,0)
    # bo |C-(15,0)|=sqrt(100+75)? — konstrukcja prostsza: łuk parametryczny od (15,0)
    # zakrzywiający ku home: azymut od home maleje z r; polilinia jawna punktami:
    pts = [(15.0, 0.0)]
    for k in range(1, 9):                     # 8 kroków: r maleje 15->4, az rośnie 0->60
        r = 15.0 - k * (11.0 / 8.0)
        az = k * (60.0 / 8.0)
        pts.append((r * math.cos(math.radians(az)), r * math.sin(math.radians(az))))
    pts.extend([(2.0, 4.5), (4.0, 1.0)])      # 2 segmenty w centrum
    segs, t_end = polyline_from_points(pts)
    while t_end < 110.0:                      # hold-kurs w dysku do konca epizodu
        segs.append(seg(t_end, pts[-1][0], pts[-1][1], 0.0, 110.0 - t_end, 0.0))
        t_end = 110.0
    return {"scenario_id": "m00_s01", "cell": {"v_intr": 1.0, "bearing_deg": 0},
            "cell_index": 0, "seed": 1, "block": 1, "is_test": False,
            "orbit_dir": "CW", "start_pos": [15.0, 0.0, Z], "z": Z,
            "ep_dur_s": 110.0, "segments": segs, "episode_id": 0,
            "opis": "M-LUK: polilinia 8 krokow (r 15->4, az 0->60) ~ luk R_c~10; v=1.0"}


def m_pod_orbita():
    segs = []
    t = 0.0
    segs.append(seg(t, 15.0, 0.0, -180.0, 9.0)); t += 9.0          # radial 15->6
    x, y = 6.0, 0.0
    segs.append(seg(t, x, y, -90.0, 14.0)); t += 14.0              # +90 st: styczny (ku -E)
    x, y = x, y - 14.0
    hd_home = math.degrees(math.atan2(-y, -x))
    segs.append(seg(t, x, y, hd_home, 10.0)); t += 10.0            # powrot ku home 10 s
    r = math.hypot(x, y)
    ux, uy = x / r, y / r
    x2, y2 = x - 10.0 * ux * 0 + 10.0 * math.cos(math.radians(hd_home)), \
             y + 10.0 * math.sin(math.radians(hd_home))
    segs.append(seg(t, x2, y2, hd_home + 180.0, 10.0)); t += 10.0  # odejscie 10 s
    x3 = x2 + 10.0 * math.cos(math.radians(hd_home + 180.0))
    y3 = y2 + 10.0 * math.sin(math.radians(hd_home + 180.0))
    segs.append(seg(t, x3, y3, 0.0, 110.0 - t, 0.0))               # hold do konca
    return {"scenario_id": "m01_s01", "cell": {"v_intr": 1.0, "bearing_deg": 0},
            "cell_index": 1, "seed": 1, "block": 1, "is_test": False,
            "orbit_dir": "CW", "start_pos": [15.0, 0.0, Z], "z": Z,
            "ep_dur_s": 110.0, "segments": segs, "episode_id": 1,
            "opis": "M-POD-ORBITA: radial 9 s (15->6; ENTRY wczesniej) -> kurs +90 st 14 s -> ku home 10 s -> odejscie; v=1.0"}


def main():
    man = {"nota": "manifest WABIK (PRE_WABIK par.2.1) — NOWY plik; istniejacy "
                   "scenario_manifest.json NIETYKALNY; semantyka segmentow 1:1 "
                   "bench/scenarios.position_at; v<=1.0 (liga R4)",
           "z_intr_m": Z, "ep_dur_s": 110.0,
           "wabik_trajektorie": {"W-LOITER": w_loiter(), "W-STYCZNY": w_styczny(),
                                 "W-ZBLIZ-ODSKOK": w_zbliz_odskok()},
           "episodes": [m_luk(), m_pod_orbita()]}
    json.dump(man, open(OUT, "w"), indent=1)
    for k, tr in man["wabik_trajektorie"].items():
        dmin = min(math.hypot(s["x0"], s["y0"]) for s in tr["segments"])
        print(f"{k}: dur={tr['dur_s']} s, n_seg={len(tr['segments'])}, min|p0|={dmin:.2f}")
    for e in man["episodes"]:
        print(f"{e['scenario_id']}: n_seg={len(e['segments'])} ({e['opis'][:60]})")
    print(f"zapisano {OUT}")


if __name__ == "__main__":
    main()
