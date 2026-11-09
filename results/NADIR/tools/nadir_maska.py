#!/usr/bin/env python3
"""results/NADIR/tools/nadir_maska.py — maska własnego kadłuba w kadrze nadir (R6, PROMPT_NADIR_S1) z klatek bootu b1.

Metoda: dwie pozy b1 o IDENTYCZNEJ postawie (p6 i p8: roll = pitch = yaw = 0) i różnym położeniu/wysokości (12 m vs 3 m).
Słońce jest kierunkowe, więc kadłub sztywny w ramie kamery ma w obu klatkach te same wartości pikseli, a grunt różne.
Maska = |Δ| ≤ 1 → domknięcie 9×9 → składowe ≥ 800 px (przypadkowe równości pól szachownicy dekalu mają ≤ ~480 px) →
suma z odbiciem w poziomie (kadłub symetryczny względem osi x_body = kolumny u = 320) → dylatacja 2 px.
(Pierwsza próba — piksele stałe we wszystkich 10 pozach — dała 0.3%: cieniowanie nóg zmienia się z postawą; odrzucona.)
Wynik: b1/maska_kadluba.png + udziały kadru i stożka centralnego (edge ≥ 0.10)."""
import json
import os

import cv2
import numpy as np

B1 = "/home/olga/projects/liquidpatrol/results/NADIR/s1/b1"
a = cv2.imread(os.path.join(B1, "frames/nadirR1_p6_z12_pochowany_m24.png"), 0).astype(int)
b = cv2.imread(os.path.join(B1, "frames/nadirR1_p8_z3.png"), 0).astype(int)
e = (np.abs(a - b) <= 1).astype(np.uint8)
c = cv2.morphologyEx(e, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
n, lab, st, _ = cv2.connectedComponentsWithStats(c)
m = np.zeros_like(c)
for i in range(1, n):
    if st[i, 4] >= 800:
        m[lab == i] = 1
m = np.maximum(m, cv2.flip(m, 1))
m = cv2.dilate(m, np.ones((5, 5), np.uint8)) > 0
cv2.imwrite(os.path.join(B1, "maska_kadluba.png"), m.astype(np.uint8) * 255)
H, W = m.shape
cc = m[int(0.1 * H):int(0.9 * H), int(0.1 * W):int(0.9 * W)]
res = {"metoda": "p6 vs p8 (ta sama postawa), |Δ|≤1, close 9, składowe ≥800 px, ∪ odbicie, dylatacja 2",
       "frac_kadr": round(float(m.mean()), 4), "frac_stozek_centralny": round(float(cc.mean()), 4)}
json.dump(res, open(os.path.join(B1, "maska_kadluba.json"), "w"), ensure_ascii=False, indent=1)
print(res)
