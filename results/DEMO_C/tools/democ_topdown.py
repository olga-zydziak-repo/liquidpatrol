#!/usr/bin/env python3
"""results/DEMO_C/tools/democ_topdown.py — panel taktyczny z góry (PROMPT_DEMO_C_V2 §1).

Źródła WYŁĄCZNIE istniejące logi bootu: trace.jsonl (GT drona + eventy refuse/
touchdown), gt_intruder.jsonl (GT intruza; FILTR BRZEGU STARTU: próbki świadka
|ned−cmd|_xy>1 m NIE są rysowane — ta sama reguła co u sędziego), demo.jsonl
(estymata nawigacji own_pos_ned — akt 3: drugi punkt drona, kropkowany),
percep_feed.jsonl (marker ENTRY). Synchronizacja po t_sim — panel żyje w tym
samym czasie (i tempie ×n) co reszta kadru.

Rysunek: północ w górę (NED: N↑ = −oś pikseli y, E→ = oś x), skala stała per akt,
siatka co 5 m, granica strefy osłony R_E = 32 m (r01/config.py:30, podpisana),
home, dron = punkt z ogonem ~12 s (blaknący), intruz = punkt z ogonem; markery
zdarzeń w momencie zajścia (trwałe po zajściu). Etykieta „(GT)".
"""
import json
import math
import os

import cv2
import numpy as np

R_E = 32.0          # r01/config.py:30 (strefa osłony — podpisana na panelu)
TRAIL_S = 12.0
HALF_M = 36.0       # okno panelu: ±36 m (mieści R_E i start intruza r=15)


def _iter_jsonl(p):
    if not os.path.exists(p):
        return
    with open(p) as f:
        for ln in f:
            try:
                yield json.loads(ln)
            except ValueError:
                continue


def _interp(series, t):
    if not series:
        return None
    if t <= series[0][0]:
        return series[0][1]
    if t >= series[-1][0]:
        return series[-1][1]
    lo, hi = 0, len(series) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if series[mid][0] <= t:
            lo = mid
        else:
            hi = mid
    t0, p0 = series[lo]
    t1, p1 = series[hi]
    a = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
    return [p0[0] + a * (p1[0] - p0[0]), p0[1] + a * (p1[1] - p0[1])]


class Panel:
    def __init__(self, bootdir, sid, akt):
        self.akt = akt
        self.t0 = None
        self.ev = {}
        self.drone = []      # (t, [N, E]) — GT z trace
        for r in _iter_jsonl(os.path.join(bootdir, "trace.jsonl")):
            if r.get("t") == "event":
                if r.get("ev") == "episode_start" and r.get("scenario_id") == sid:
                    self.t0 = r["t0_sim"]
                if r.get("ev") in ("refuse", "touchdown", "denial"):
                    self.ev.setdefault(r["ev"], r.get("sim"))
            elif r.get("t") == "gt":
                # ENU (x=E, y=N) → [N, E]
                self.drone.append((r["sim"], [r["y"], r["x"]]))
        self.drone.sort()
        # intruz: FILTR BRZEGU STARTU (świadek |ned−cmd|_xy>1 — nie rysujemy)
        self.intr = []
        for r in _iter_jsonl(os.path.join(bootdir, "gt_intruder.jsonl")):
            if not r.get("ned"):
                continue
            if r.get("cmd_ned") and math.dist(r["ned"][:2], r["cmd_ned"][:2]) > 1.0:
                continue
            self.intr.append((r["t_sim"], [r["ned"][0], r["ned"][1]]))
        self.intr.sort()
        # estymata nawigacji (demo own_pos_ned) — akt 3: drugi punkt drona
        self.est = []
        for r in _iter_jsonl(os.path.join(bootdir, "demo.jsonl")):
            if r.get("scenario_id") == sid and r.get("own_pos_ned"):
                self.est.append((r["t_sim"], [r["own_pos_ned"][0], r["own_pos_ned"][1]]))
        self.est.sort()
        # ENTRY (percep_feed ev) — pozycja drona w chwili zajścia
        self.t_entry_ev = None
        for r in _iter_jsonl(os.path.join(bootdir, "percep_feed.jsonl")):
            if r.get("ev") == "ENTRY" and r.get("t_frame") is not None \
                    and self.t0 is not None and r["t_frame"] >= self.t0:
                self.t_entry_ev = r["t_frame"]
                break

    def _px(self, ne, W, H):
        n, e = ne[0], ne[1]
        x = int(W / 2 + e / HALF_M * (W / 2 - 8))
        y = int(H / 2 - n / HALF_M * (H / 2 - 8))
        return x, y

    def _trail(self, img, series, t, col, W, H, dotted=False):
        tt = t - TRAIL_S
        k = 0
        while tt <= t:
            p = _interp(series, tt)
            if p is not None and (not dotted or k % 3 == 0):
                a = max(0.12, (tt - (t - TRAIL_S)) / TRAIL_S)
                c = tuple(int(ch * a + 26 * (1 - a)) for ch in col)
                cv2.circle(img, self._px(p, W, H), 2, c, -1, cv2.LINE_AA)
            tt += 0.2
            k += 1

    def draw(self, t_abs, W=640, H=640):
        img = np.full((H, W, 3), 26, dtype=np.uint8)
        # siatka co 5 m (delikatna)
        m = -35
        while m <= 35:
            x, _ = self._px([0, m], W, H)
            _, y = self._px([m, 0], W, H)
            cv2.line(img, (x, 0), (x, H), (40, 40, 44), 1)
            cv2.line(img, (0, y), (W, y), (40, 40, 44), 1)
            m += 5
        # strefa osłony R_E (podpisana)
        c = self._px([0, 0], W, H)
        r_px = int(R_E / HALF_M * (W / 2 - 8))
        cv2.circle(img, c, r_px, (90, 70, 170), 2, cv2.LINE_AA)
        cv2.putText(img, f"strefa oslony R_E = {R_E:.0f} m", (c[0] - r_px + 10, c[1] - r_px + 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 100, 200), 1, cv2.LINE_AA)
        # home
        cv2.drawMarker(img, c, (140, 140, 150), cv2.MARKER_CROSS, 12, 1)
        cv2.putText(img, "home", (c[0] + 8, c[1] + 16), cv2.FONT_HERSHEY_SIMPLEX,
                    0.4, (140, 140, 150), 1, cv2.LINE_AA)
        # ogony + punkty
        self._trail(img, self.intr, t_abs, (70, 70, 230), W, H)
        pi = _interp(self.intr, t_abs)
        if pi is not None and self.intr[0][0] - 0.5 <= t_abs <= self.intr[-1][0] + 0.5:
            cv2.circle(img, self._px(pi, W, H), 6, (60, 60, 255), -1, cv2.LINE_AA)
            cv2.putText(img, "intruz", (self._px(pi, W, H)[0] + 8, self._px(pi, W, H)[1] - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (60, 60, 255), 1, cv2.LINE_AA)
        if self.akt == 3 and self.est:
            self._trail(img, self.est, t_abs, (80, 190, 255), W, H, dotted=True)
            pe = _interp(self.est, t_abs)
            if pe is not None and t_abs <= self.est[-1][0] + 0.3:
                cv2.circle(img, self._px(pe, W, H), 6, (80, 190, 255), 2, cv2.LINE_AA)
        self._trail(img, self.drone, t_abs, (120, 255, 120), W, H)
        pd = _interp(self.drone, t_abs)
        if pd is not None:
            cv2.circle(img, self._px(pd, W, H), 6, (120, 255, 120), -1, cv2.LINE_AA)
            cv2.putText(img, "dron", (self._px(pd, W, H)[0] + 8, self._px(pd, W, H)[1] + 16),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 255, 120), 1, cv2.LINE_AA)
        # markery zdarzeń (trwałe po zajściu)
        marks = []
        if self.t_entry_ev and t_abs >= self.t_entry_ev:
            marks.append((self.t_entry_ev, "ENTRY", (90, 230, 255), cv2.MARKER_DIAMOND))
        if self.ev.get("refuse") and t_abs >= self.ev["refuse"]:
            marks.append((self.ev["refuse"], "REFUSE(POS)", (60, 160, 255), cv2.MARKER_TILTED_CROSS))
        if self.ev.get("touchdown") and t_abs >= self.ev["touchdown"]:
            marks.append((self.ev["touchdown"], "TOUCHDOWN", (120, 255, 120), cv2.MARKER_SQUARE))
        for (tm, lab, col, mk) in marks:
            p = _interp(self.drone, tm)
            if p is None:
                continue
            q = self._px(p, W, H)
            cv2.drawMarker(img, q, col, mk, 14, 2)
            cv2.putText(img, lab, (q[0] + 10, q[1] - 8), cv2.FONT_HERSHEY_SIMPLEX,
                        0.45, col, 1, cv2.LINE_AA)
        # ramka, północ, etykieta GT
        cv2.rectangle(img, (0, 0), (W - 1, H - 1), (70, 70, 80), 1)
        cv2.putText(img, "N", (W - 30, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (200, 200, 210), 1, cv2.LINE_AA)
        cv2.arrowedLine(img, (W - 24, 54), (W - 24, 32), (200, 200, 210), 1, tipLength=0.4)
        cv2.putText(img, "panel taktyczny (GT) · siatka 5 m", (10, H - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (150, 150, 160), 1, cv2.LINE_AA)
        return img
