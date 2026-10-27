#!/usr/bin/env python3
"""results/DEMO_C/tools/democ_cut_v31.py — sklejka DEMO_C_v31 (PROMPT_DEMOC_V31 §3).
NOWY plik; democ_cut.py i democ_cut_v3.py NIETYKALNE. Tor 1:1 z democ_cut_v3
(cv2 mp4v @10 fps — odchylenie jawne: ffmpeg nie istnieje na hoście), plansza
= tekst FROZEN v3 BEZ ZMIAN; zmiany vs v3: klip aktu 1 = akt1_v31 (sekwencja
admisji + TEMPO ×0.5), klipy 4a/4b = v31 (panel reguły), bloki SRT aktu 1
przepisane pod sekwencję admisji + po jednym bloku o panelu reguły w 4a/4b.

Użycie: democ_cut_v31.py <akt1> <akt2> <akt3> <akt4a> <akt4b> <out_dir>
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

F_T = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 54)
F_M = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 38)

PLANSZA = ["LiquidPatrol — PX4/Gazebo SITL.",
           "Zero naruszeń strefy i zero błędnych odmów w ~140 bootach.",
           "Sterownik: płynna sieć 20 neuronów — 48/48 vs GRU 29/48",
           "na tej samej siatce.",
           "Wabiki: rozpoznawane po zachowaniu — zero fałszywych alarmów w pomiarach.",
           "Domowy sprzęt, wieczory i weekendy."]

SRT_EN = {
    1: [(0, 5, "ACT 1 — THE DRONE SEES: head-on intruder; det_v2 on a live camera (slow-mo x0.5)"),
        (5, 10, "Step by step: detector box (conf 0.77) -> 3 consistent frames: centrality + motion"),
        (10, 15, "ADMISSION -> TRACK (judge t_acq 0.73 s); the 20-neuron liquid net takes over"),
        (15, 99, "Approach and the 6-10 m orbit — all from one 640x480 mono camera")],
    2: [(0, 7, "ACT 2 — THE DRONE SEARCHES: target starts BEHIND (azimuth 180°) — empty camera"),
        (7, 14, "Step-scan with the whole airframe: 40° steps, perimeter sweep"),
        (14, 99, "Find, pursue, orbit — all from one 640x480 mono camera")],
    3: [(0, 6, "ACT 3 — THE DRONE SURVIVES: nominal orbit; perception EMULATED in this act"),
        (6, 12, "We inject a GPS failure (EKF2_GPS_CTRL=0) — position starts drifting"),
        (12, 99, "The shield: REFUSE(POS) in ~0.1 s, then a safe D5 descent to touchdown")],
    4: [(0, 7, "ACT 4 — THE DRONE SPOTS A DECOY: the object circles, never attacks"),
        (7, 15, "Motion signature: fast, not closing, never below 5 m"),
        (15, 24, "Rule panel (left): moving / not closing / never below 5 m — the 12-s counter grows only when ALL hold"),
        (24, 99, "Label DECOY once the rule holds — the clock is shown openly")],
    5: [(0, 7, "ACT 4b — THE FLAG REVERSES: the target starts out like a decoy"),
        (7, 16, "The classifier raises a tentative flag... but the target CHANGES behaviour"),
        (16, 24, "Watch the panel: 'not closing' flips to X, then 'never below 5 m' — the label is REVOKED"),
        (24, 99, "Descent below 5 m => the label is REVOKED and the drone pursues")],
}


def srt_time(t):
    ms = int(round((t - int(t)) * 1000))
    s = int(t)
    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d},{ms:03d}"


def main():
    clips = sys.argv[1:6]
    outd = sys.argv[6]
    os.makedirs(outd, exist_ok=True)
    out = os.path.join(outd, "DEMO_C_v31.mp4")
    vw = cv2.VideoWriter(out, cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (1920, 1080))
    lens = []
    for p in clips:
        c = cv2.VideoCapture(p)
        n = 0
        while True:
            ok, fr = c.read()
            if not ok:
                break
            vw.write(fr)
            n += 1
        lens.append(n / 10.0)
        c.release()
    img = Image.new("RGB", (1920, 1080), (8, 10, 16))
    d = ImageDraw.Draw(img)
    y = 330
    for i, ln in enumerate(PLANSZA):
        f = F_T if i == 0 else F_M
        w = d.textlength(ln, font=f)
        d.text(((1920 - w) / 2, y), ln, font=f,
               fill=(255, 220, 90) if i == 0 else
                    ((255, 190, 120) if i == 4 else (235, 235, 235)))
        y += 92 if i == 0 else 62
    pl = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    for _ in range(90):
        vw.write(pl)
    vw.release()
    total = sum(lens) + 9.0
    srt = []
    idx = 1
    off = 0.0
    for akt, ln in zip((1, 2, 3, 4, 5), lens):
        for (t0, t1, txt) in SRT_EN[akt]:
            if t0 >= ln:
                continue
            srt.append(f"{idx}\n{srt_time(off + t0)} --> {srt_time(off + min(t1, ln))}\n{txt}\n")
            idx += 1
        off += ln
    srt.append(f"{idx}\n{srt_time(off)} --> {srt_time(off + 9.0)}\n"
               "LiquidPatrol — PX4/Gazebo SITL. Zero zone breaches and zero false refusals "
               "across ~140 boots. Controller: a 20-neuron liquid network — 48/48 vs GRU 29/48 "
               "on the same grid. Decoys: recognised by behaviour — zero false alarms in "
               "the measurements. Home hardware, evenings and weekends.\n")
    open(os.path.join(outd, "DEMO_C_v31_en.srt"), "w").write("\n".join(srt))
    print(f"[cut_v31] klipy {[round(x,1) for x in lens]} s + plansza 9 s = {total:.1f} s → {out}")


if __name__ == "__main__":
    main()
