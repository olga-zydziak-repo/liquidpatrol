#!/usr/bin/env python3
"""results/DEMO_C/tools/democ_overlay_v3.py — render AKTU 4 (PROMPT_DEMOC_V3 §2).
NOWY plik; democ_overlay.py v1 i _v2 NIETYKALNE (odtwarzalność wstecz).

Kopia toru v2 (kamera pokładowa główna ×2 NN + ramki detektora z percep_feed +
panel taktyczny + HUD + zegar ciągły + segmenty TEMPO z jawnym podpisem) ze
zmianami AKTU 4:
  • panel = WBUDOWANA kopia klasy Panel z democ_topdown (moduł FROZEN toru v2
    nietknięty) z parametrem wyglądu obiektu: 4a — POMARAŃCZOWY punkt+ogon,
    podpis „wabik"; 4b — czerwony, podpis „cel";
  • wskaźnik ETYKIETY klasyfikatora (litera wabik_sig v1 475c972e, POSTHOC):
    „—" → „WABIK (t+X.X s)" z sekundnikiem od flagi → (4b) „ODWOŁANA — cel
    atakuje"; czasy z pliku akt4_sig.json (absolutne t_flag/t_revoke);
  • napis uczciwości WYPALONY przez cały akt: „klasyfikator diagnostyczny —
    etykieta wyliczona z zapisu lotu, nie steruje dronem".
W bootach aktu 4 scenariusz wabika jest GRANY TOREM INTRUZA (jeden obiekt
w świecie — litera WABIK S2), więc GT obiektu = gt_intruder/manifest S2.

Użycie: democ_overlay_v3.py <bootdir> <sid> <4a|4b> <t_od> <t_do> <out_mp4>
        <akt4_sig.json> [segmenty]
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

MAN2 = json.load(open(os.path.join(ROOT, "results", "WABIK", "wabik_manifest_s2.json")))
SCEN = {e["scenario_id"]: e for e in MAN2["episodes"]}
F_BIG = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
F_B36 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
F_MED = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
F_SML = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)

CAPTIONS = {
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
    import bisect
    i = bisect.bisect_left(keys, t)
    best = None
    for j in (i - 1, i):
        if 0 <= j < len(keys) and abs(keys[j] - t) <= tol:
            if best is None or abs(keys[j] - t) < abs(best - t):
                best = keys[j]
    return best


def zoh(keys, t, max_stale):
    import bisect
    i = bisect.bisect_right(keys, t) - 1
    if i >= 0 and t - keys[i] <= max_stale:
        return keys[i]
    return None


def put(d, xy, txt, font, fill=(255, 255, 255)):
    d.text((xy[0] + 2, xy[1] + 2), txt, font=font, fill=(0, 0, 0))
    d.text(xy, txt, font=font, fill=fill)


def _interp2(series, t):
    import bisect
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
    """Kopia democ_topdown.Panel (moduł nietknięty) z parametrem wyglądu obiektu."""

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


def main():
    bootdir, sid, akt, t_od, t_do, out_mp4, sigjson = sys.argv[1], sys.argv[2], \
        sys.argv[3], float(sys.argv[4]), float(sys.argv[5]), sys.argv[6], sys.argv[7]
    segments = None
    if len(sys.argv) > 8:
        segments = [(float(a), float(b), float(c)) for a, b, c in
                    (seg.split(":") for seg in sys.argv[8].split(","))]
    sig = json.load(open(sigjson))
    t_flag_abs = sig.get("t_flag_abs")
    t_revoke_abs = sig.get("t_revoke_abs")
    t0 = None
    for r in iter_jsonl(os.path.join(bootdir, "trace.jsonl")):
        if r.get("t") == "event" and r.get("ev") == "episode_start" \
                and r.get("scenario_id") == sid:
            t0 = r["t0_sim"]
            break
    assert t0 is not None
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
    col = (0, 165, 255) if akt == "4a" else (60, 60, 255)
    lab = "wabik" if akt == "4a" else "cel"
    panel = Panel4(bootdir, sid, col, lab)
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
        canvas[60:1020, 640:1920] = 128
        tcf = nearest(ck, t_abs, 0.08)
        conf = None
        if tcf is not None:
            cam = cv2.imread(os.path.join(bootdir, "cam", "frames", cmap[tcf]))
            if cam.ndim == 2:
                cam = cv2.cvtColor(cam, cv2.COLOR_GRAY2BGR)
            tpf = nearest(pfk, tcf, 0.01)
            if tpf is not None and pf[tpf].get("box"):
                b = pf[tpf]["box"]
                conf = pf[tpf].get("conf")
                mti = bool(pf[tpf].get("mti_ok"))
                cx, cy, w, h = b[0] * 640, b[1] * 480, b[2] * 640, b[3] * 480
                cv2.rectangle(cam, (int(cx - w / 2), int(cy - h / 2)),
                              (int(cx + w / 2), int(cy + h / 2)),
                              (80, 255, 80) if mti else (60, 220, 255), 2)
            cam2 = cv2.resize(cam, (1280, 960), interpolation=cv2.INTER_NEAREST)
            canvas[60:1020, 640:1920] = cam2
        canvas[56:696, 0:640] = panel.draw(t_abs, 640, 640)
        img = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle([0, 0, 1920, 56], fill=(0, 0, 0, 200))
        put(d, (16, 6), "AKT 4", F_BIG, (255, 220, 90))
        put(d, (190, 14), f"epizod {sid} · zegar {trel:6.1f} s", F_MED)
        d.rectangle([0, 696, 640, 1020], fill=(10, 10, 20, 235))
        # ETYKIETA klasyfikatora
        et_txt, et_col = "—", (160, 160, 170)
        if t_flag_abs is not None and t_abs >= t_flag_abs:
            if t_revoke_abs is not None and t_abs >= t_revoke_abs:
                et_txt, et_col = "ODWOŁANA — cel atakuje", (255, 140, 90)
            else:
                et_txt, et_col = f"WABIK  (+{t_abs - t_flag_abs:4.1f} s)", (90, 200, 255)
        put(d, (24, 706), "ETYKIETA KLASYFIKATORA", F_SML, (150, 150, 160))
        put(d, (24, 732), et_txt, F_B36, et_col)
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
        put(d, (24, 796), "FAZA", F_SML, (150, 150, 160))
        put(d, (24, 820), faza, F_MED, (120, 220, 255))
        put(d, (330, 796), "DYSTANS (GT)", F_SML, (150, 150, 160))
        put(d, (330, 820), f"{dh:5.1f} m" if dh is not None else "—", F_MED)
        put(d, (24, 872), (f"detektor conf {conf:.2f}" if conf is not None else "brak detekcji"),
            F_SML, (120, 255, 120) if conf is not None else (255, 160, 120))
        put(d, (24, 920), "klasyfikator diagnostyczny — etykieta wyliczona", F_SML, (255, 200, 120))
        put(d, (24, 946), "z zapisu lotu, nie steruje dronem", F_SML, (255, 200, 120))
        put(d, (24, 986), "panel taktyczny ↑ · kamera pokładowa →", F_SML, (120, 120, 130))
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
    print(f"[overlay_v3] akt {akt} {sid}: {n} klatek → {out_mp4}")


if __name__ == "__main__":
    main()
