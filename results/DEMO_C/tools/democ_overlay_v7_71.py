#!/usr/bin/env python3
"""results/DEMO_C/tools/democ_overlay_v7_71.py — KOPIA democ_overlay_v7.py (nietknięty) dla v7.1 (PROMPT_DEMOC_V71). Hunki:
  (§4) adapter replayu rep_nad2: wiersze demo.jsonl z own_pos_ned podmienionym na p_corr z rama.jsonl we WSZYSTKICH tickach
       (dopasowanie po epizodzie i numerze ticku; brak wiersza ramy ⇒ STOP), replay_episode(..., "ncp", fantom=True);
       kryterium p95 ≤ 5e-3 m/s bez zmian; wynik porównany z odniesieniem CC (p95 1.16e-3);
  (§2.4) tytuł mini-mózgu w pasku nad panelem, podpis pod panelem, na podkładce; (§2.4/§2.5 wspólne) importy z democ_overlay_v5_71;
  (§2.1) wkładka nadir: ID znacznika rysowane tylko, gdy napis mieści się w obrazie; etykieta trybu dosunięta do prawej
         krawędzi wkładki.
--- nagłówek kopii ---
results/DEMO_C/tools/democ_overlay_v7.py — montaż v7: AKT 7 „Bez GPS" (PROMPT_DEMOC_V7 §2–§6). NOWY plik; v1–v6 i narzędzia
NAD2 NIETYKALNE (importowane wyłącznie READ-ONLY: helpery democ_overlay_v2/v5/v6, nad2_analyze, xai_replay).

Część A (ujęcie z kamerami, katalog take'u): układ aktów 1–2 — kamera pokładowa ×2 nearest z ramkami celu WYŁĄCZNIE
z percep_feed, panel taktyczny 640×640, HUD, mini-mózg (tylko gdy kotwica replayu p95 ≤ 5e-3 m/s) + wkładka kamery nadir
(klatka po stemplu sim; obrysy/ID znaczników WYŁĄCZNIE z nadir_obs.jsonl, kolor = przyjęty / odrzucony literą z fx zapisu,
podpis trybu). Panel: prawda (GT, pełny), pozycja poprawiona (pierścień, p_corr z rama.jsonl w fazie utraty), surowy estymator
(kropkowany, p_ekf), intruz (gt_intruder, filtr brzegu startu jak democ_topdown), strefa R_E = 32 m, 37 znaczników z
results/NADIR/s1/n1/manifest_znaczniki_v2.json.
Błędy w HUD: e_corr = |p_corr − GT(ts)| i |p_ekf − GT(ts)|, ts = timestamp_sample próbki EKF ticku dopasowanej po wartości
w oknie [sim − 0.4, sim + 0.1] — ten sam kanon i to samo okno co nad2_analyze.analyze (funkcja wewnętrzna t_probki nie jest
eksportowana; wzór przepisany 1:1, a zgodność sprawdzona asercją: max e_corr/U i liczba ocenionych ticków = wyniki_nad2.json).
Oś czasu: [t_inj − 5, t_inj + 10] ×1, potem ×8 do zejscie_planowe, zejście 2 s wideo ×4.
Część B („10 minut", 0 bootów): logi lotu results/NAD2/s4/L_c10_s01 z repo — trace, rama, gt_intruder, nadir_obs (gzip) oraz
wyciąg ULG ulg.jsonl.gz (vehicle_local_position w pełnej kadencji, z timestamp_sample — źródło kanonu czasu B1) — pełnoekranowy
panel, TEMPO ×30, liczniki bieżące; asercje §3 przed renderem.

Tryby:
  aktA <takedir> <out.mp4>            część A z ujęcia
  aktB <out.mp4>                      część B z zapisu lotu długiego
  karty <out_dir>                     karta wejścia (4 s), karta zakresu (6 s), plansza v7 (9 s) → mp4 + png
  cut <v6.mp4> <out_dir>              v7 = v6 bez planszy + akt 7 + plansza v7; klip GPS = akt 7 + plansza v7; srt EN
"""
import bisect
import gzip
import json
import math
import os
import re
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
for p in (ROOT, HERE, os.path.join(ROOT, "results", "NAD2", "tools"), os.path.join(ROOT, "results", "XAI_RECON", "tools")):
    if p not in sys.path:
        sys.path.insert(0, p)
from r03 import nadir_shield as NS  # noqa: E402
import nad2_analyze as A  # noqa: E402
from democ_overlay_v2 import nearest, put  # noqa: E402
from democ_overlay_v5_71 import top_edges, draw_brain, srt_time  # noqa: E402  (§2.4)
from xai_replay import replay_episode  # noqa: E402  (§4)
from democ_overlay_v6 import PLANSZA6, COL6  # noqa: E402
from xai_replay import anchor_stats, model_of  # noqa: E402

FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
F_T = ImageFont.truetype(FONT_B, 54)
F_BIG = ImageFont.truetype(FONT_B, 44)
F_B36 = ImageFont.truetype(FONT_B, 36)
F_B28 = ImageFont.truetype(FONT_B, 28)
F_B22 = ImageFont.truetype(FONT_B, 22)
F_MED = ImageFont.truetype(FONT_R, 30)
F_M38 = ImageFont.truetype(FONT_R, 38)
F_M44 = ImageFont.truetype(FONT_R, 44)
F_SML = ImageFont.truetype(FONT_R, 22)
F_S18 = ImageFont.truetype(FONT_R, 18)
F_S15 = ImageFont.truetype(FONT_R, 15)

SID = "c10_s01"
EPID = 10
R_E = 32.0
UTRATA = ("KONT", "KONT_REFUSE")
LONG = os.path.join(ROOT, "results", "NAD2", "s4", "L_c10_s01")
MARK = json.load(open(os.path.join(ROOT, "results", "NADIR", "s1", "n1", "manifest_znaczniki_v2.json")))["znaczniki"]
assert len(MARK) == 37

# teksty FROZEN (PROMPT_DEMOC_V7 §2–§4)
CAPS_A = ["GPS działa — sieć krąży wokół intruza",
          "GPS ODCIĘTY (celowo, test)",
          "pozycję daje kamera w dół: znaczniki naziemne co 10 m",
          "ta sama sieć: 20 neuronów, 1903 parametry — prowadzi lot dalej",
          "osłona z dowodem pilnuje strefy"]
HONESTY = "symulacja PX4/Gazebo · pozycja bez GNSS: przepływ optyczny + kamera w dół nad znacznikami"
DESC_LABEL = "planowe zejście po 110 s"
B_SUB = "zapis lotu z 12.11.2026 — odtworzenie z logów, nie obraz z kamery · TEMPO ×30"
B_FINAL = ("600 s bez GPS: intruz śledzony 100% czasu · 0 odmów osłony · błąd pozycji bez trendu (p95 0.2 m) · "
           "surowy estymator odjechał do 20.6 m")
CARD_IN = "Akt 3: po utracie GPS osłona kończy lot. Nad terenem ze znacznikami naziemnymi misja trwa."
CARD_SCOPE = ("Zakres: symulacja, jedna sceneria, znaczniki dobrze widoczne. Bez znaczników: 22 s pod dowodem. Bramka: "
              "12/12 lotów po 110 s — założenie dowodu sprawdzone w każdym kroku, zero przekroczeń.")
LINE_V7 = "Bez GPS nad polem znaczników: 12/12 lotów po 110 s pod dowodem; 10 minut w jednym locie."
ZAKAZANE = ("bez nawigacji", "rekord", "najdłuższy", "odporny na zagłuszanie")
for _t in CAPS_A + [HONESTY, DESC_LABEL, B_SUB, B_FINAL, CARD_IN, CARD_SCOPE, LINE_V7]:
    assert not any(z in _t.lower() for z in ZAKAZANE), _t
# EN (srt)
CAPS_A_EN = ["GPS working — the network orbits the intruder",
             "GPS CUT (deliberately, a test)",
             "position now comes from a downward camera: ground markers every 10 m",
             "the same network: 20 neurons, 1903 parameters — keeps flying the mission",
             "a shield with a proof guards the zone"]
CARD_IN_EN = "Act 3: after GPS loss the shield ends the flight. Over terrain with ground markers the mission goes on."
CARD_SCOPE_EN = ("Scope: simulation, one scene, markers clearly visible. Without markers: 22 s under proof. Gate: 12/12 flights "
                 "of 110 s — the proof's assumption checked at every step, zero violations.")
B_SUB_EN = "flight log of 12.11.2026 — replayed from logs, not camera footage · SPEED ×30"
B_FINAL_EN = ("600 s without GPS: intruder tracked 100% of the time · 0 shield refusals · position error with no trend "
              "(p95 0.2 m) · the raw estimator drifted up to 20.6 m")
LINE_V7_EN = "Without GPS over a marker field: 12/12 flights of 110 s under proof; 10 minutes in a single flight."


# ------------------------------------------------------------------ (§4) adapter replayu NAD2
KOTWICA_CC = {"p50": 5.7e-4, "p95": 1.16e-3, "max": 2.3e-3}


def rep_nad2(take):
    """W trybie NAD2 wejściem sieci jest p_corr z rama.jsonl (nad2_flight.py:619–625: own_net = rama.p_corr(own)), nie
    own_pos_ned z demo.jsonl. Wiersze demo z own_pos_ned := p_corr (każdy tick), replay z kwarantanną wrappera (fantom=True)."""
    import copy
    rama = {(r["ep"], r["tick"]): r for r in jl(os.path.join(take, "rama.jsonl"))}
    rows = []
    for x in jl(os.path.join(take, "demo.jsonl")):
        if x.get("scenario_id") != SID:
            continue
        k = (x["episode_id"], x["tick"])
        assert k in rama, f"STOP: brak wiersza ramy dla {k}"
        y = copy.deepcopy(x)
        y["own_pos_ned"] = rama[k]["p_corr"]
        rows.append(y)
    return replay_episode(rows, "ncp", fantom=True), rows


# ------------------------------------------------------------------ dane
def jl(p, typ=None):
    if not os.path.exists(p) and os.path.exists(p + ".gz"):
        p = p + ".gz"
    if not os.path.exists(p):
        return []
    op = gzip.open if p.endswith(".gz") else open
    out = []
    with op(p, "rt") as f:
        for l in f:
            if typ is not None and f'"{typ}"' not in l:
                continue
            try:
                r = json.loads(l)
            except ValueError:
                continue
            if typ is None or r.get("t") == typ:
                out.append(r)
    return out


def vlp_ulg(d):
    """(timestamp s, timestamp_sample s, xyz) z boot.ulg (nad2_analyze.ulg) albo z wyciągu ulg.jsonl.gz."""
    if os.path.exists(os.path.join(d, "boot.ulg")) and d != LONG:
        v = A.ulg(d)["vehicle_local_position"]
        return v["timestamp"] / 1e6, v["timestamp_sample"] / 1e6, np.stack([v["x"], v["y"], v["z"]], 1), "boot.ulg"
    for l in gzip.open(os.path.join(d, "ulg.jsonl.gz"), "rt"):
        r = json.loads(l)
        if r.get("temat") == "vehicle_local_position":
            dd = r["dane"]
            return (np.asarray(dd["timestamp"], float), np.asarray(dd["timestamp_sample"], float),   # wyciąg: już w s
                    np.stack([dd["x"], dd["y"], dd["z"]], 1).astype(float), "ulg.jsonl.gz")
    raise RuntimeError("brak vehicle_local_position")


class Lot:
    """Wspólne dane epizodu cięcia: zdarzenia, GT, rama, błędy per tick (kanon analizatora), intruz, nadir_obs."""

    def __init__(self, d):
        self.d = d
        ev = jl(os.path.join(d, "trace.jsonl"), "event")
        e1 = lambda n: next((e for e in ev if e.get("ev") == n), None)
        self.st, self.cut, self.zp, self.land = e1("episode_start"), e1("denial"), e1("zejscie_planowe"), e1("gt_przyziemienie")
        assert self.st["scenario_id"] == SID and self.cut and self.zp
        self.t0 = self.st["t0_sim"]
        self.t_inj = self.cut["t_inj_sim"]
        self.t_zp = self.zp["sim"]
        gt = sorted(jl(os.path.join(d, "trace.jsonl"), "gt"), key=lambda r: r["sim"])
        self.gt_t = np.array([g["sim"] for g in gt])
        self.gt_ne = np.array([[g["y"], g["x"]] for g in gt])
        self.vt, self.vts, self.vp, self.ulg_src = vlp_ulg(d)
        rama = sorted((r for r in jl(os.path.join(d, "rama.jsonl")) if r.get("ep") == EPID), key=lambda r: r["tick"])
        self.tk = []
        for r in rama:
            n2, ph = r.get("nad2") or {}, r.get("ph")
            nad = r.get("nadir") or {}
            row = {"sim": r["sim"], "ph": ph, "p_ekf": r["p_ekf"][:2], "p_corr": (r.get("p_corr") or r["p_ekf"])[:2],
                   "tau": nad.get("tau"), "tryb": n2.get("tryb"), "e": None, "eU": None, "e_ekf": None}
            ts = self._t_probki(r["p_ekf"], r["sim"])
            if ts is not None:
                g = self.GT(ts)
                row["e_ekf"] = float(math.hypot(r["p_ekf"][0] - g[0], r["p_ekf"][1] - g[1]))
                if ph in UTRATA and n2:
                    i, tr, j = n2.get("przedzial"), n2.get("tryb"), nad.get("j")
                    if i is not None and j is not None:
                        pc = r["p_corr"]
                        row["e"] = float(math.hypot(pc[0] - g[0], pc[1] - g[1]))
                        row["eU"] = row["e"] / A.U_of(i, j, tr)
            self.tk.append(row)
        self.tk_t = [r["sim"] for r in self.tk]
        # odmowy osłony w misji: wejścia w KONT_REFUSE przed zejscie_planowe
        self.ref_t = [b["sim"] for a, b in zip(self.tk, self.tk[1:]) if b["ph"] == "KONT_REFUSE" and a["ph"] != "KONT_REFUSE"
                      and b["sim"] < self.t_zp]
        self.intr = []
        for r in jl(os.path.join(d, "gt_intruder.jsonl")):
            if r.get("ned") and r.get("episode_id") == EPID and not (r.get("cmd_ned") and math.dist(r["ned"][:2], r["cmd_ned"][:2]) > 1.0):
                self.intr.append((r["t_sim"], r["ned"][:2]))
        self.intr.sort()
        self.in_t = [x[0] for x in self.intr]
        self.nf = {round(r["sim"], 3): r for r in jl(os.path.join(d, "nadir_obs.jsonl"), "nf")}
        self.nf_t = sorted(self.nf)

    def _t_probki(self, p, t_ref, okno=(-0.4, 0.1)):          # = nad2_analyze.analyze.t_probki (1:1)
        i0, i1 = bisect.bisect_left(self.vt, t_ref + okno[0]), bisect.bisect_right(self.vt, t_ref + okno[1])
        if i1 <= i0:
            return None
        dd = np.linalg.norm(self.vp[i0:i1] - np.asarray(p, float), axis=1)
        return float(self.vts[i0 + int(np.argmin(dd))])

    def GT(self, t):
        return np.array([np.interp(t, self.gt_t, self.gt_ne[:, k]) for k in range(2)])

    def tick(self, t):
        i = bisect.bisect_right(self.tk_t, t) - 1
        return self.tk[i] if i >= 0 else None

    def series(self, key, t, span):
        i1 = bisect.bisect_right(self.tk_t, t)
        i0 = bisect.bisect_left(self.tk_t, t - span)
        return self.tk[i0:i1]

    def intr_at(self, t):
        i = bisect.bisect_right(self.in_t, t) - 1
        return self.intr[i][1] if i >= 0 and t - self.in_t[i] < 0.5 else None

    def ocenione(self):
        return [r for r in self.tk if r["e"] is not None]


# ------------------------------------------------------------------ panel
class PanelV7:
    def __init__(self, lot, W, H, trail_s, half_m=36.0):
        self.lot, self.W, self.H, self.trail, self.half = lot, W, H, trail_s, half_m

    def px(self, ne):
        s = (min(self.W, self.H) / 2 - 8) / self.half
        return int(self.W / 2 + ne[1] * s), int(self.H / 2 - ne[0] * s)

    def draw(self, t):
        L, W, H = self.lot, self.W, self.H
        img = np.full((H, W, 3), 26, np.uint8)
        m = -35
        while m <= 35:
            x, _ = self.px([0, m]); _, y = self.px([m, 0])
            cv2.line(img, (x, 0), (x, H), (40, 40, 44), 1)
            cv2.line(img, (0, y), (W, y), (40, 40, 44), 1)
            m += 5
        c = self.px([0, 0])
        r_px = self.px([0, R_E])[0] - c[0]
        cv2.circle(img, c, r_px, (90, 70, 170), 2, cv2.LINE_AA)
        q = max(4, int(r_px / R_E * 1.0 / 2))                          # znacznik 1 m
        for z in MARK:
            p = self.px([z["N"], z["E"]])
            cv2.rectangle(img, (p[0] - q, p[1] - q), (p[0] + q, p[1] + q), (150, 150, 150), 1)
        cv2.drawMarker(img, c, (140, 140, 150), cv2.MARKER_CROSS, 12, 1)
        utrata = L.t_inj <= t
        # ogony: intruz, prawda, poprawiona (w utracie), surowy estymator
        for k, r in enumerate(L.series(None, t, self.trail)):
            a = max(0.12, 1.0 - (t - r["sim"]) / self.trail)
            if k % 4 == 0:
                g = L.GT(r["sim"])
                cv2.circle(img, self.px(g), 2, tuple(int(ch * a + 26 * (1 - a)) for ch in (120, 255, 120)), -1, cv2.LINE_AA)
            if k % 8 == 0:
                cv2.circle(img, self.px(r["p_ekf"]), 2, tuple(int(ch * a + 26 * (1 - a)) for ch in (80, 190, 255)), -1, cv2.LINE_AA)
        i0 = bisect.bisect_left(L.in_t, t - self.trail); i1 = bisect.bisect_right(L.in_t, t)
        for k in range(i0, i1, 10):
            a = max(0.12, 1.0 - (t - L.in_t[k]) / self.trail)
            cv2.circle(img, self.px(L.intr[k][1]), 2, tuple(int(ch * a + 26 * (1 - a)) for ch in (70, 70, 230)), -1, cv2.LINE_AA)
        pi = L.intr_at(t)
        if pi is not None:
            cv2.circle(img, self.px(pi), 7, (60, 60, 255), -1, cv2.LINE_AA)
        r = L.tick(t)
        if r is not None:
            cv2.circle(img, self.px(r["p_ekf"]), 7, (80, 190, 255), 2, cv2.LINE_AA)            # surowy estymator (kropkowany ogon)
            if utrata and r["ph"] in UTRATA:
                cv2.circle(img, self.px(r["p_corr"]), 11, (255, 230, 90), 2, cv2.LINE_AA)       # pozycja poprawiona (pierścień)
        g = L.GT(t)
        cv2.circle(img, self.px(g), 6, (120, 255, 120), -1, cv2.LINE_AA)                     # prawda
        cv2.rectangle(img, (0, 0), (W - 1, H - 1), (70, 70, 80), 1)
        cv2.arrowedLine(img, (W - 24, 54), (W - 24, 32), (200, 200, 210), 1, tipLength=0.4)
        return img


def legend(d, x, y, f=F_S15):
    put(d, (x, y), "● prawda (GT)", f, (120, 255, 120))
    put(d, (x + 150, y), "◯ pozycja poprawiona", f, (90, 230, 255))
    put(d, (x + 360, y), "∘ surowy estymator", f, (255, 190, 80))
    put(d, (x, y + 20), "● intruz", f, (255, 60, 60))
    put(d, (x + 150, y + 20), "□ znaczniki (37, co 10 m)", f, (170, 170, 170))
    put(d, (x + 380, y + 20), f"○ strefa R_E = {R_E:.0f} m", f, (200, 100, 120))


def mmss(s):
    s = max(0.0, s)
    return f"{int(s // 60):02d}:{int(s % 60):02d}"


# ------------------------------------------------------------------ część A
def plan_A(L):
    plan = []
    t = L.t_inj - 5.0
    while t < L.t_inj + 10.0 - 1e-9:
        plan.append((t, 1.0)); t += 0.1
    while t < L.t_zp - 1e-9:
        plan.append((t, 8.0)); t += 0.8
    t = L.t_zp
    for _ in range(20):                                          # zejście: 2 s wideo ×4
        plan.append((t, 4.0)); t += 0.4
    return plan


def caps_A(plan, L):
    # granice napisów w czasie wideo: 0–5 przed cięciem, 5–9, 9–15, 15–21, 21–koniec
    return [(0.0, 5.0, CAPS_A[0]), (5.0, 9.0, CAPS_A[1]), (9.0, 15.0, CAPS_A[2]), (15.0, 21.0, CAPS_A[3]),
            (21.0, len(plan) / 10.0 + 1, CAPS_A[4])]


def draw_nadir(canvas, L, d, t, reg):
    """Wkładka kamery nadir: klatka po stemplu sim; obrysy z nadir_obs (det.c), kolor z fx (ids przyjęte / odrz)."""
    x0, y0, w, h = reg
    cv2.rectangle(canvas, (x0 - 2, y0 - 26), (x0 + w + 2, y0 + h + 2), (20, 20, 20), -1)
    idx = d["nadir_idx"]
    tn = nearest(d["nadir_t"], t, 0.25)
    info = None
    if tn is not None:
        im = cv2.imread(os.path.join(L.d, "nadir", "frames", idx[tn]))
        tf = nearest(L.nf_t, tn, 0.01)
        nf = L.nf.get(tf) if tf is not None else None
        if nf is not None:
            fx = nf.get("fx") or {}
            ok_ids = set(fx.get("ids") or []) | set(((fx.get("para") or {}).get("ids")) or [])
            odrz = {o["id"] for o in fx.get("odrz") or []}
            for dt in nf.get("det") or []:
                col = (90, 255, 90) if (fx.get("ok") and dt["id"] in ok_ids) else ((60, 60, 255) if dt["id"] in odrz else (200, 200, 200))
                pts = np.array(dt["c"], np.int32)
                cv2.polylines(im, [pts], True, col, 3, cv2.LINE_AA)
                org = (int(dt["uv"][0]) + 18, int(dt["uv"][1]) - 14)                               # (§2.1) ID tylko w obrazie
                (tw, th_), tb = cv2.getTextSize(str(dt["id"]), cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)
                if org[0] >= 2 and org[1] - th_ >= 2 and org[0] + tw <= im.shape[1] - 2 and org[1] + tb <= im.shape[0] - 2:
                    cv2.putText(im, str(dt["id"]), org, cv2.FONT_HERSHEY_SIMPLEX, 0.9, col, 2, cv2.LINE_AA)
            info = fx
        d["n_nadir"] += 1
        canvas[y0:y0 + h, x0:x0 + w] = cv2.resize(im, (w, h), interpolation=cv2.INTER_AREA)
    else:
        canvas[y0:y0 + h, x0:x0 + w] = 40
    return info


def render_A(take, out_mp4):
    L = Lot(take)
    an = json.load(open(os.path.join(take, "wyniki_nad2.json")))
    o = next(x for x in an["epizody"] if x["ciecie"])
    oc = L.ocenione()
    assert len(oc) == o["B1"]["ticki_ocenione"], (len(oc), o["B1"]["ticki_ocenione"])
    assert abs(max(r["eU"] for r in oc) - o["B1"]["max_e_do_U"]) <= 1e-4, "HUD ≠ analizator"
    rep, _rows = rep_nad2(take)                                                              # (§4)
    st = anchor_stats(rep)
    brain = st["p95"] <= 5e-3
    st["roznica_p95_vs_CC"] = abs(st["p95"] - KOTWICA_CC["p95"])  # (§4)
    print(f"[aktA] kotwica replayu: p50={st['p50']:.2e} p95={st['p95']:.2e} max={st['max']:.2e} → mini-mózg={brain}")
    edges = top_edges(model_of("ncp"))
    tt_rep = rep["t"]
    pf = {round(r["t_frame"], 3): r for r in jl(os.path.join(take, "percep_feed.jsonl")) if r.get("t_frame") is not None}
    pfk = sorted(pf)
    cmap = {round(r["sim"], 3): r["f"] for r in jl(os.path.join(take, "cam", "frames_index.jsonl"))}
    ck = sorted(cmap)
    nidx = {round(r["sim"], 3): r["f"] for r in jl(os.path.join(take, "nadir", "frames_index.jsonl"))}
    dd = {"nadir_idx": nidx, "nadir_t": sorted(nidx), "n_nadir": 0}
    panel = PanelV7(L, 640, 640, 12.0)
    plan = plan_A(L)
    caps = caps_A(plan, L)
    vw = cv2.VideoWriter(out_mp4, cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (1920, 1080))
    n = n_cam = 0
    for (t, sp) in plan:
        canvas = np.zeros((1080, 1920, 3), np.uint8)
        canvas[60:1020, 640:1920] = 128
        tcf = nearest(ck, t, 0.08)
        if tcf is not None:
            n_cam += 1
            cam = cv2.imread(os.path.join(take, "cam", "frames", cmap[tcf]))
            if cam.ndim == 2:
                cam = cv2.cvtColor(cam, cv2.COLOR_GRAY2BGR)
            tpf = nearest(pfk, tcf, 0.01)
            if tpf is not None and pf[tpf].get("box"):
                b = pf[tpf]["box"]
                cx, cy, w, h = b[0] * 640, b[1] * 480, b[2] * 640, b[3] * 480
                cv2.rectangle(cam, (int(cx - w / 2), int(cy - h / 2)), (int(cx + w / 2), int(cy + h / 2)),
                              (80, 255, 80) if pf[tpf].get("mti_ok") else (60, 220, 255), 2)
            canvas[60:1020, 640:1920] = cv2.resize(cam, (1280, 960), interpolation=cv2.INTER_NEAREST)
        nreg = (660, 690, 400, 300)
        fx = draw_nadir(canvas, L, dd, t, nreg)
        canvas[56:696, 0:640] = panel.draw(t)
        if brain:
            i = min(max(int(np.searchsorted(tt_rep, t, side="right")) - 1, 0), len(tt_rep) - 1)
            reg = (1596, 736, 312, 236)
            draw_brain(canvas, reg, rep["h"][i], rep["y"][i], None, edges, mini=True)
        canvas[696:1020, 0:640] = (20, 10, 10)
        r = L.tick(t)
        img = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle([0, 0, 1920, 56], fill=(0, 0, 0, 200))
        put(d, (16, 6), "AKT 7", F_BIG, (255, 220, 90))
        put(d, (190, 14), f"epizod {SID} · świat world_nadir2_A3 · zegar {t - L.t0:6.1f} s", F_MED)
        d.rectangle([640, 60, 1920, 92], fill=(0, 0, 0, 170))
        put(d, (656, 64), HONESTY, F_S18, (255, 200, 120))
        legend(d, 10, 56 + 6)
        put(d, (nreg[0] + 4, nreg[1] - 24), "kamera w dół (nadir) · obrysy z zapisu", F_S15, (220, 220, 220))
        if fx:
            tryb = {"para": "para", "jeden": "jeden znacznik"}.get(fx.get("tryb"), "—") if fx.get("ok") else "bez poprawki"
            put(d, (nreg[0] + nreg[2] - 4 - int(d.textlength(tryb, font=F_S15)), nreg[1] - 24), tryb, F_S15,   # (§2.1)
                (90, 255, 90) if fx.get("ok") else (255, 120, 120))
        d.rectangle([nreg[0] - 2, nreg[1] + nreg[3] + 2, nreg[0] + nreg[2] + 2, nreg[1] + nreg[3] + 24], fill=(0, 0, 0, 220))
        put(d, (nreg[0] + 4, nreg[1] + nreg[3] + 4), "zielony = przyjęty literą · czerwony = odrzucony", F_S15, (190, 190, 190))
        gps_ok = t < L.t_inj
        put(d, (24, 704), "GPS", F_SML, (150, 150, 160))
        put(d, (24, 728), "OK" if gps_ok else "ODCIĘTY", F_B36, (120, 255, 120) if gps_ok else (255, 90, 90))
        put(d, (330, 704), "BEZ GPS", F_SML, (150, 150, 160))
        put(d, (330, 728), mmss(t - L.t_inj) if not gps_ok else "—", F_B36)
        put(d, (24, 790), "wiek poprawki τ", F_SML, (150, 150, 160))
        put(d, (24, 814), f"{r['tau']:.2f} s" if (r and r["tau"] is not None and not gps_ok) else "—", F_B28)
        put(d, (330, 790), "odmowy osłony (misja)", F_SML, (150, 150, 160))
        put(d, (330, 814), str(sum(1 for x in L.ref_t if x <= t)), F_B28)
        put(d, (24, 866), "błąd pozycji poprawionej", F_SML, (150, 150, 160))
        put(d, (24, 890), f"{r['e']:.2f} m" if (r and r["e"] is not None) else "—", F_B28, (90, 230, 255))
        put(d, (330, 866), "surowy estymator ↔ prawda", F_SML, (150, 150, 160))
        put(d, (330, 890), f"{r['e_ekf']:.2f} m" if (r and r["e_ekf"] is not None) else "—", F_B28, (255, 190, 80))
        put(d, (24, 944), "błędy wobec prawdy symulatora (GT), kanon czasu analizatora", F_S15, (130, 130, 140))
        if brain:
            d.rectangle([1596, 736 - 24, 1596 + 312, 736 - 2], fill=(0, 0, 0, 170))                       # (§2.4) pasek tytułu nad panelem
            put(d, (1596 + 8, 736 - 22), "W GŁOWIE SIECI — ta sieć PROWADZI lot", F_S15, (255, 220, 120))
            d.rectangle([1596, 736 + 236 + 2, 1596 + 312, 736 + 236 + 24], fill=(0, 0, 0, 170))   # (§2.4)
            put(d, (1596 + 8, 736 + 236 + 4), "panel = replay zapisu (nie steruje)", F_S15, (200, 180, 140))
        if sp != 1.0:
            d.rectangle([1600, 4, 1904, 52], fill=(0, 0, 0, 220))
            put(d, (1620, 8), f"TEMPO ×{sp:g}", F_BIG, (255, 160, 60))
        if t >= L.t_zp:
            d.rectangle([1100, 100, 1900, 150], fill=(0, 0, 0, 200))
            put(d, (1120, 106), DESC_LABEL, F_B28, (255, 220, 120))
        tk = n / 10.0
        cap = next((c[2] for c in caps if c[0] <= tk < c[1]), None)
        if cap:
            d.rectangle([0, 1020, 1920, 1080], fill=(0, 0, 0, 220))
            put(d, (24, 1032), cap, F_MED)
        vw.write(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))
        n += 1
    vw.release()
    res = {"klatek": n, "dur_s": n / 10.0, "klatki_cam": n_cam, "klatki_nadir": dd["n_nadir"], "kotwica": st, "mini_mozg": brain,
           "t_inj": L.t_inj, "t_zp": L.t_zp, "kontynuacja": round(L.t_zp - L.t_inj, 3), "ulg": L.ulg_src, "napisy": caps}
    print(f"[aktA] {n} klatek ({n / 10:.1f} s), kamera {n_cam}/{n}, nadir {dd['n_nadir']}/{n} → {out_mp4}")
    return res


# ------------------------------------------------------------------ część B
def render_B(out_mp4):
    L = Lot(LONG)
    oc = L.ocenione()
    kont = round(L.t_zp - L.t_inj, 3)
    n_mis = sum(1 for r in oc if r["sim"] < L.t_zp)
    eU = max(r["eU"] for r in oc)
    ekf = max(r["e_ekf"] for r in L.tk if r["e_ekf"] is not None and r["ph"] in UTRATA)
    asercje = {"kontynuacja_s": kont, "ticki_misji_z_tabela": n_mis, "max_e_do_U": round(eU, 4), "max_surowy_m": round(ekf, 3),
               "zrodlo_ulg": L.ulg_src}
    print("[aktB] asercje", asercje)
    assert abs(kont - 600.516) <= 5e-4, asercje
    assert n_mis == 12077, asercje
    assert abs(eU - 0.412) <= 0.001, asercje
    assert abs(ekf - 20.59) <= 0.02, asercje
    W = 1920
    panel = PanelV7(L, 1000, 1000, 60.0)
    plan = []
    t = L.t_inj
    while t <= L.t_zp + 1e-9:
        plan.append(t); t += 3.0
    vw = cv2.VideoWriter(out_mp4, cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (W, 1080))
    eU_max = 0.0
    for k, t in enumerate(plan):
        canvas = np.full((1080, W, 3), 12, np.uint8)
        canvas[60:1060, 40:1040] = panel.draw(t)
        win = [r for r in L.series(None, t, 3.0) if r["e"] is not None]
        for r in win:
            eU_max = max(eU_max, r["eU"])
        r = L.tick(t)
        img = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle([0, 0, W, 56], fill=(0, 0, 0, 200))
        put(d, (16, 6), "AKT 7 — 10 minut bez GPS", F_BIG, (255, 220, 90))
        put(d, (1600, 8), "TEMPO ×30", F_BIG, (255, 160, 60))
        for k2, (txt, col) in enumerate((("● prawda (GT)", (120, 255, 120)), ("◯ pozycja poprawiona", (90, 230, 255)),
                                         ("∘ surowy estymator", (255, 190, 80)), ("● intruz", (255, 60, 60)),
                                         ("□ znaczniki (37, co 10 m)", (170, 170, 170)), (f"○ strefa R_E = {R_E:.0f} m", (200, 100, 120)))):
            put(d, (1090, 760 + 30 * k2), txt, F_SML, col)
        x = 1090
        put(d, (x, 100), "BEZ GPS", F_SML, (150, 150, 160))
        put(d, (x, 126), mmss(min(t - L.t_inj, 600.0)), F_T)
        put(d, (x, 230), "błąd pozycji poprawionej", F_SML, (150, 150, 160))
        put(d, (x, 256), f"{r['e']:.2f} m" if r and r["e"] is not None else "—", F_B36, (90, 230, 255))
        put(d, (x, 330), "surowy estymator od prawdy", F_SML, (150, 150, 160))
        put(d, (x, 356), f"{r['e_ekf']:.1f} m" if r and r["e_ekf"] is not None else "—", F_B36, (255, 190, 80))
        put(d, (x, 430), "zużycie granicy dowodu (e/U)", F_SML, (150, 150, 160))
        put(d, (x, 456), f"{100 * r['eU']:.0f}%" if r and r["eU"] is not None else "—", F_B36)
        put(d, (x + 200, 468), f"maks. dotąd {100 * eU_max:.0f}%", F_SML, (200, 200, 210))
        put(d, (x, 530), "odmowy osłony", F_SML, (150, 150, 160))
        put(d, (x, 556), str(sum(1 for z in L.ref_t if z <= t)), F_B36)
        put(d, (x, 640), "błędy wobec prawdy symulatora (GT)", F_S18, (130, 130, 140))
        d.rectangle([0, 1020, W, 1080], fill=(0, 0, 0, 220))
        if k >= len(plan) - 50:
            put(d, (24, 1034), B_FINAL, F_SML, (255, 230, 150))
        else:
            put(d, (24, 1032), B_SUB, F_MED)
        vw.write(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))
    vw.release()
    print(f"[aktB] {len(plan)} klatek ({len(plan) / 10:.1f} s) → {out_mp4}")
    return {"klatek": len(plan), "dur_s": len(plan) / 10.0, "asercje": asercje}


# ------------------------------------------------------------------ karty, plansza, montaż
def wrap(d, text, f, maxw):
    out, cur = [], ""
    for w in text.split(" "):
        c = (cur + " " + w).strip()
        if d.textlength(c, font=f) <= maxw:
            cur = c
        else:
            out.append(cur); cur = w
    out.append(cur)
    return out


def karta(text, f=F_M44):
    img = Image.new("RGB", (1920, 1080), (8, 10, 16))
    d = ImageDraw.Draw(img)
    lines = []
    for zd in re.split(r"(?<=\.)\s+", text):                     # zdanie od nowej linii, długie zawijane
        lines += wrap(d, zd, f, 1700)
    assert " ".join(lines) == text
    y = 540 - len(lines) * 34
    for ln in lines:
        w = d.textlength(ln, font=f)
        d.text(((1920 - w) / 2, y), ln, font=f, fill=(235, 235, 235))
        y += 68
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR), lines


PLANSZA7 = PLANSZA6[:-1] + [LINE_V7] + PLANSZA6[-1:]
COL7 = dict(COL6); COL7[9] = (190, 170, 255)


def plansza7():
    img = Image.new("RGB", (1920, 1080), (8, 10, 16))
    d = ImageDraw.Draw(img)
    y = 170
    for i, ln in enumerate(PLANSZA7):
        f = F_T if i == 0 else F_M38
        w = d.textlength(ln, font=f)
        assert w <= 1880, f"linia planszy za szeroka: {ln}"
        d.text(((1920 - w) / 2, y), ln, font=f, fill=(255, 220, 90) if i == 0 else COL7.get(i, (235, 235, 235)))
        y += 92 if i == 0 else 62
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def karty(outd):
    os.makedirs(os.path.join(outd, "clips"), exist_ok=True)
    res = {}
    for nm, img, sek in (("karta_wejscia_v7", karta(CARD_IN)[0], 4), ("karta_zakresu_v7", karta(CARD_SCOPE)[0], 6),
                         ("plansza_v7", plansza7(), 9)):
        cv2.imwrite(os.path.join(outd, "clips", nm + ".png"), img)
        vw = cv2.VideoWriter(os.path.join(outd, "clips", nm + ".mp4"), cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (1920, 1080))
        for _ in range(sek * 10):
            vw.write(img)
        vw.release()
        res[nm] = sek
    print("[karty]", res)


def frames(p):
    c = cv2.VideoCapture(p)
    while True:
        ok, fr = c.read()
        if not ok:
            break
        yield fr
    c.release()


def nframes(p):
    c = cv2.VideoCapture(p); n = int(c.get(cv2.CAP_PROP_FRAME_COUNT)); c.release()
    return n


def cut(v6_mp4, outd):
    cl = os.path.join(outd, "clips")
    czesci = [os.path.join(cl, x) for x in ("karta_wejscia_v7.mp4", "akt7_A.mp4", "akt7_B.mp4", "karta_zakresu_v7.mp4")]
    pl = os.path.join(cl, "plansza_v7.mp4")
    n6 = nframes(v6_mp4); keep = n6 - 90
    dl = [nframes(p) for p in czesci]
    tot7 = (keep + sum(dl) + 90) / 10.0
    totg = (sum(dl) + 90) / 10.0
    assert tot7 <= 310.0, f"v7 {tot7:.1f} s > 310 s"
    assert totg <= 75.0, f"klip GPS {totg:.1f} s > 75 s"
    vw = cv2.VideoWriter(os.path.join(outd, "DEMO_C_v7.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (1920, 1080))
    k = 0
    for fr in frames(v6_mp4):
        if k >= keep:
            break
        vw.write(fr); k += 1
    assert k == keep
    for p in czesci + [pl]:
        for fr in frames(p):
            vw.write(fr)
    vw.release()
    vg = cv2.VideoWriter(os.path.join(outd, "DEMO_C_v7_GPS.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (1920, 1080))
    for p in czesci + [pl]:
        for fr in frames(p):
            vg.write(fr)
    vg.release()
    # SRT EN: v6 bez planszy + akt 7 + plansza v7
    blocks = open(os.path.join(outd, "DEMO_C_v6_en.srt")).read().strip().split("\n\n")[:-1]
    t = keep / 10.0
    dA, dB = dl[1] / 10.0, dl[2] / 10.0
    ev = [(t, t + 4, CARD_IN_EN)]
    tA = t + 4
    for (a, b, txt) in zip((0, 5, 9, 15, 21), (5, 9, 15, 21, dA), CAPS_A_EN):
        ev.append((tA + a, tA + b, txt))
    tB = tA + dA
    ev.append((tB, tB + dB - 5, B_SUB_EN))
    ev.append((tB + dB - 5, tB + dB, B_FINAL_EN))
    tS = tB + dB
    ev.append((tS, tS + 6, CARD_SCOPE_EN))
    tP = tS + 6
    v6_pl = open(os.path.join(outd, "DEMO_C_v6_en.srt")).read().strip().split("\n\n")[-1].split("\n", 2)[2]
    pl_en = v6_pl.replace(" Home hardware, evenings and weekends.", " " + LINE_V7_EN + " Home hardware, evenings and weekends.")
    assert pl_en != v6_pl
    ev.append((tP, tP + 9, pl_en))
    idx = len(blocks) + 1
    for (a, b, txt) in ev:
        blocks.append(f"{idx}\n{srt_time(a)} --> {srt_time(b)}\n{txt}"); idx += 1
    open(os.path.join(outd, "DEMO_C_v7_en.srt"), "w").write("\n\n".join(blocks) + "\n")
    print(f"[cut_v7] v6 bez planszy {keep / 10:.1f} s + akt 7 {sum(dl) / 10:.1f} s + plansza 9 s = {tot7:.1f} s; klip GPS {totg:.1f} s")
    return {"v7_s": tot7, "gps_s": totg, "czesci_s": [x / 10 for x in dl], "v6_bez_planszy_s": keep / 10}


def main():
    m = sys.argv[1]
    if m == "aktA":
        r = render_A(sys.argv[2], sys.argv[3])
    elif m == "aktB":
        r = render_B(sys.argv[2])
    elif m == "karty":
        r = karty(sys.argv[2])
    elif m == "cut":
        r = cut(sys.argv[2], sys.argv[3])
    print(json.dumps(r, default=float, ensure_ascii=False))


if __name__ == "__main__":
    main()
