#!/usr/bin/env python3
"""results/DEMO_C/tools/democ_v8_overlay.py — montaż v8: AKT 8 „Bez GPS, bez znaczników" (PROMPT_DEMOC_V8 §3–§6). NOWY plik;
akty 1–7 i ich narzędzia NIETKNIĘTE (importowane READ-ONLY: democ_overlay_v2.put/nearest, democ_overlay_v5_71.draw_brain/top_edges/
srt_time, democ_overlay_v7_71.karta/wrap/COL7, democ_en_71.PLANSZA_EN, teach_analyze — kanon błędów i tabela lotu).
Teksty na ekranie wprost po angielsku (teksty zamrożone §5, asercja zgodności i słów zakazanych przed renderem).

Część A (ujęcie, katalog take'u w results/DEMO_C/s8_mapa): układ aktu 7 v7.1 — kamera pokładowa (ramki celu wyłącznie z percep_feed),
panel z góry 640×640 (prawda GT, pierścień pozycji poprawionej p_corr w fazie utraty, kropkowany estymator bez poprawek p_ekf, intruz
gt_intruder, strefa R_E = 32 m; zamiast znaczników obrysy klatek kluczowych mapy od chwili zapisu), HUD (błędy kanonem analizatora
TEACH z asercją wobec wyniki_teach.json), wkładka kamery w dół (klatka po stemplu sim; w fazie mapy numer klatki mapy i klatki kluczowej
z wiersza producenta „wlaczony”; po cięciu numer klatki kluczowej i liczba punktów zgodnych z wiersza „lok”; współrzędnych punktów
zapis nie niesie — nie są rysowane), mini-mózg warunkowo (kotwica replayu, niżej).
Oś czasu A: faza mapy [t_mapa0, t_inj − 4] ściśnięta do 8 s (tempo policzone i podpisane), [t_inj − 4, t_inj + 8] ×1, ×8 do zejścia
planowego, zejście 2 s wideo ×4.
Obrys klatki kluczowej: środek = cam_ekf (E, N) z rekordu georeferencji producenta (asercja: ≤ 1.0 m od ekf_pos wiersza nf producenta w chwili zapisu),
rozmiar = rzut pola widzenia kamery w dół (horizontal_fov 1.74 rad, 640×480 z model.sdf x500_teach_flow, sha w asercji) z wysokości
„a” zapisanej w klatce kluczowej, obrót = kurs EKF z wiersza nf w chwili zapisu (szerokość obrazu wzdłuż osi poprzecznej drona).
Mini-mózg: replay sieci NCP-20 (net/frozen/ncp.npz) na wierszach demo.jsonl z own_pos_ned := p_corr z rama.jsonl (pozycja EKF +
przesunięcie poprawki z ramy wykonania), stan ukryty zmienia się tylko w ticku fazy approach albo orbit z ważnym trackiem (wiek
≤ 1.0 s); kotwica = |replay − cmd_v_ned| na tych tickach; wchodzi, gdy p95 ≤ 5e-3 m/s.
Część B (lot TEACH-II z logów, results/TEACH2/s1/L1_S_c10, 0 bootów): panel z góry 760×760 z obrysami 15 klatek kluczowych, wykres
pod panelem (błąd każdej poprawki z mapy z poprawki_teach2.jsonl i odległość estymatora bez poprawek od prawdy, wspólna oś czasu),
miniatury kadry/ w chwilach zapisu; ×30 od początku epizodu do zejścia planowego; asercje §4 wobec sedzia_teach2.json i przeliczeń.

Tryby:
  aktA <takedir> <out.mp4>   aktB <out.mp4>   karty <out_dir>   cut <v71.mp4> <out_dir>
"""
import bisect
import datetime
import hashlib
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
for p in (ROOT, HERE, os.path.join(ROOT, "results", "TEACH", "tools"), os.path.join(ROOT, "results", "NAD3", "tools")):
    if p not in sys.path:
        sys.path.insert(0, p)
from democ_overlay_v2 import nearest, put  # noqa: E402
import democ_overlay_v5_71 as V5  # noqa: E402
import democ_overlay_v7_71 as V7  # noqa: E402
import teach_analyze as TA  # noqa: E402

F_T, F_BIG, F_B36, F_B28, F_MED, F_SML, F_S18, F_S15, F_M38 = V7.F_T, V7.F_BIG, V7.F_B36, V7.F_B28, V7.F_MED, V7.F_SML, V7.F_S18, \
    V7.F_S15, V7.F_M38
R_E = 32.0
UTRATA = ("KONT", "KONT_REFUSE")
LONG = os.path.join(ROOT, "results", "TEACH2", "s1", "L1_S_c10")
MODEL_SDF = os.path.join(ROOT, "PX4-Autopilot/Tools/simulation/gz/models/x500_teach_flow/model.sdf")
MODEL_SHA = "656ccc9b2040fd96c863f3bb44fa740ca7b7a40ac745773aa06d663f30b4a447"
HFOV, IMG_W, IMG_H = 1.74, 640, 480

# ------------------------------------------------------------------ teksty zamrożone (PROMPT_DEMOC_V8 §5)
CARD_IN = "ACT 8 — NO GPS, NO MARKERS. Act 7 needed markers on the ground. Here the drone maps the ground itself while GPS still works."
CAPS_A = ["GPS working — the drone maps the ground beneath it",
          "GPS CUT (deliberately, a test)",
          "position now comes from its own map — no markers, no beacons",
          "the same network: 20 neurons, 1903 parameters — keeps flying the mission",
          "a shield with a proof guards the zone",
          "planned descent after 110 s"]
HONESTY = "camera footage of a judged flight · simulation"
B_SUB_T = "flight log of {data} — replayed from logs, not camera footage · SPEED ×30"
B_MAP = "200 s with GPS: the drone builds a map from its downward camera"
B_FINAL = ("600 s without GPS and without markers: intruder tracked 100% of the time · 0 shield refusals · position error never "
           "above 0.45 m, no trend · the raw estimator drifted up to 17.4 m")
CARD_SCOPE = ("Scope: simulation; the ground is a flat aerial image; the map is minutes old, same light. The drone flies without GPS "
              "only over ground it has flown over with GPS. Gate: 12/12 flights of 110 s over three terrains. Long flight: one flight, one site.")
LINE_V8 = "No GPS, no markers: 10 minutes on a map the drone built itself in 200 s."
DATA_PROMPT = "18.11.2026"
# słowa zakazane: lista v7 (PL) z odpowiednikami EN + §5
ZAKAZANE = ("bez nawigacji", "rekord", "najdłuższy", "odporny na zagłuszanie", "without navigation", "record", "longest",
            "jamming", "slam", "unknown terrain", "anywhere", "real world")
NAPISY = []                                                          # wszystkie napisy wypalone (do asercji i raportu)


def sprawdz_tekst(s):
    lo = s.lower()
    assert not any(z in lo for z in ZAKAZANE), f"słowo zakazane: {s!r}"
    assert not ("proved" in lo and any(w in lo for w in ("map", "fix", "position", "source"))), f"„proved” przy mapie: {s!r}"


def P(d, xy, s, f, col=(255, 255, 255)):
    sprawdz_tekst(s)
    NAPISY.append(s)
    put(d, xy, s, f, col)


def jl(p, typ=None):
    return V7.jl(p, typ)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


# ------------------------------------------------------------------ dane lotu TEACH
class Lot8:
    def __init__(self, d):
        self.d = d
        tr = os.path.join(d, "trace.jsonl")
        ev = jl(tr, "event")
        e1 = lambda n: next((e for e in ev if e.get("ev") == n), None)
        self.armed, self.st, self.cut, self.zp = e1("armed"), e1("episode_start"), e1("denial"), e1("zejscie_planowe")
        assert self.st and self.cut and self.zp, "STOP: brak zdarzeń epizodu"
        self.ep = self.st["episode_id"]
        self.t0, self.t_inj, self.t_zp = self.st["t0_sim"], self.cut["t_inj_sim"], self.zp["sim"]
        TA.T3 = TA.tabela_lotu(d)
        assert TA.T3 is not None and TA.T3["sha"].startswith("7a56ba1b"), "STOP: tabela lotu"
        gt = sorted(jl(tr, "gt"), key=lambda r: r["sim"])
        self.gt_t = np.array([g["sim"] for g in gt])
        self.gt_ne = np.array([[g["y"], g["x"]] for g in gt])                     # kanon analizatora: NED = [y, x, −z]
        u = TA.ulg(d)
        v = u["vehicle_local_position"]
        self.vt, self.vts = v["timestamp"] / 1e6, v["timestamp_sample"] / 1e6
        self.vp = np.stack([v["x"], v["y"], v["z"]], 1)
        rama = sorted((r for r in jl(os.path.join(d, "rama.jsonl")) if r.get("ep") == self.ep), key=lambda r: r["tick"])
        self.tk = []
        for r in rama:
            n2, ph, nad = r.get("nad2"), r.get("ph"), r.get("nadir") or {}
            row = {"sim": r["sim"], "tick": r["tick"], "ph": ph, "p_ekf": r["p_ekf"][:2], "p_corr": (r.get("p_corr") or r["p_ekf"])[:2],
                   "tau": nad.get("tau"), "e": None, "eU": None, "e_ekf": None}
            ts = self._t_probki(r["p_ekf"], r["sim"])
            if ts is not None:
                g = self.GT(ts)
                row["e_ekf"] = float(math.hypot(r["p_ekf"][0] - g[0], r["p_ekf"][1] - g[1]))
                if ph in UTRATA and n2 is not None:
                    i, tr_, j = n2.get("przedzial"), n2.get("tryb"), nad.get("j")
                    if i is not None and j is not None:
                        pc = r["p_corr"]
                        row["e"] = float(math.hypot(pc[0] - g[0], pc[1] - g[1]))
                        row["eU"] = row["e"] / TA.U_of(i, j, tr_)
            self.tk.append(row)
        self.tk_t = [r["sim"] for r in self.tk]
        self.ref_t = [b["sim"] for a, b in zip(self.tk, self.tk[1:]) if b["ph"] == "KONT_REFUSE" and a["ph"] != "KONT_REFUSE"
                      and b["sim"] < self.t_zp]
        self.intr = []
        for r in jl(os.path.join(d, "gt_intruder.jsonl")):
            if r.get("ned") and r.get("episode_id") == self.ep and not (r.get("cmd_ned") and math.dist(r["ned"][:2], r["cmd_ned"][:2]) > 1.0):
                self.intr.append((r["t_sim"], r["ned"][:2]))
        self.intr.sort()
        self.in_t = [x[0] for x in self.intr]
        # producent mapy: wiersze nf
        self.nf = {}
        self.t_mapa0, self.georef, self.t_georef = None, None, None
        for r in jl(os.path.join(d, "nadir_obs.jsonl"), "nf"):
            self.nf[round(r["sim"], 3)] = r
            te = r.get("teach") or {}
            if self.t_mapa0 is None and te.get("faza") == "mapa" and "bufor" in te:
                self.t_mapa0 = r["sim"]
            if te.get("georef") and self.georef is None:
                self.georef, self.t_georef = te["georef"], r["sim"]
        self.nf_t = sorted(self.nf)
        assert self.t_mapa0 is not None and self.georef is not None, "STOP: brak fazy mapy albo georeferencji w zapisie"
        # klatki kluczowe: środek (N, E) = (cam_ekf[1], cam_ekf[0]); asercja wobec p_ekf ramy
        assert sha(MODEL_SDF) == MODEL_SHA, "STOP: model kamery w dół"
        self.kf = []
        for k in self.georef["kf"]:
            c = (k["cam_ekf"][1], k["cam_ekf"][0])
            tn = nearest(self.nf_t, k["sim"], 0.01)
            nf = self.nf[tn] if tn is not None else {}
            ep = nf.get("ekf_pos")
            assert ep is not None and math.dist(c, ep[:2]) <= 1.0, ("STOP: klatka kluczowa ≠ ekf_pos wiersza nf", k["k"], c, ep)
            hdg = nf.get("ekf_hdg")
            assert hdg is not None, ("STOP: brak kursu EKF w chwili klatki kluczowej", k["k"])
            self.kf.append({"k": k["k"], "sim": k["sim"], "c": c, "a": k["a"], "hdg": hdg})

    def _t_probki(self, p, t_ref, okno=(-0.4, 0.1)):                 # = teach_analyze.analyze.t_probki (1:1, funkcja wewnętrzna)
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

    def series(self, t, span):
        return self.tk[bisect.bisect_left(self.tk_t, t - span):bisect.bisect_right(self.tk_t, t)]

    def intr_at(self, t):
        i = bisect.bisect_right(self.in_t, t) - 1
        return self.intr[i][1] if i >= 0 and t - self.in_t[i] < 0.5 else None

    def nf_at(self, t, tol=0.25):
        tn = nearest(self.nf_t, t, tol)
        return self.nf.get(tn) if tn is not None else None

    def ocenione(self):
        return [r for r in self.tk if r["e"] is not None]


def footprint(kf):
    hw = kf["a"] * math.tan(HFOV / 2)
    hh = hw * IMG_H / IMG_W
    f = np.array([math.cos(kf["hdg"]), math.sin(kf["hdg"])])
    r = np.array([-math.sin(kf["hdg"]), math.cos(kf["hdg"])])
    c = np.array(kf["c"])
    return [c + hh * f + hw * r, c + hh * f - hw * r, c - hh * f - hw * r, c - hh * f + hw * r]


class Panel8:
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
        for kf in L.kf:                                                          # obrysy klatek kluczowych od chwili zapisu
            if kf["sim"] <= t:
                pts = np.array([self.px(p) for p in footprint(kf)], np.int32)
                cv2.polylines(img, [pts], True, (150, 150, 150) if t - kf["sim"] > 2.0 else (90, 230, 255), 1, cv2.LINE_AA)
        c = self.px([0, 0])
        r_px = self.px([0, R_E])[0] - c[0]
        cv2.circle(img, c, r_px, (90, 70, 170), 2, cv2.LINE_AA)
        cv2.drawMarker(img, c, (140, 140, 150), cv2.MARKER_CROSS, 12, 1)
        utrata = L.t_inj <= t
        for k, r in enumerate(L.series(t, self.trail)):
            a = max(0.12, 1.0 - (t - r["sim"]) / self.trail)
            if k % 4 == 0:
                cv2.circle(img, self.px(L.GT(r["sim"])), 2, tuple(int(ch * a + 26 * (1 - a)) for ch in (120, 255, 120)), -1, cv2.LINE_AA)
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
            cv2.circle(img, self.px(r["p_ekf"]), 7, (80, 190, 255), 2, cv2.LINE_AA)
            if utrata and r["ph"] in UTRATA:
                cv2.circle(img, self.px(r["p_corr"]), 11, (255, 230, 90), 2, cv2.LINE_AA)
        cv2.circle(img, self.px(L.GT(t)), 6, (120, 255, 120), -1, cv2.LINE_AA)
        cv2.rectangle(img, (0, 0), (W - 1, H - 1), (70, 70, 80), 1)
        cv2.arrowedLine(img, (W - 24, 54), (W - 24, 32), (200, 200, 210), 1, tipLength=0.4)
        return img


def legend(d, x, y, f=F_S15):
    P(d, (x, y), "● truth (simulator)", f, (120, 255, 120))
    P(d, (x + 160, y), "◯ corrected position", f, (90, 230, 255))
    P(d, (x + 360, y), "∘ raw estimator", f, (255, 190, 80))
    P(d, (x, y + 20), "● intruder", f, (255, 60, 60))
    P(d, (x + 160, y + 20), "▭ map keyframes", f, (170, 170, 170))
    P(d, (x + 360, y + 20), f"○ zone {R_E:.0f} m", f, (200, 100, 120))


def mmss(s):
    s = max(0.0, s)
    return f"{int(s // 60):02d}:{int(s % 60):02d}"


# ------------------------------------------------------------------ mini-mózg: replay
def replay(take):
    from bench.features import features
    from net.dataset import clip_age
    from net.models import NCP20
    m = NCP20.load(os.path.join(ROOT, "net", "frozen", "ncp.npz"))
    rama = {(r["ep"], r["tick"]): r for r in jl(os.path.join(take, "rama.jsonl"))}
    h = np.zeros((1, m.H))
    out = {"t": [], "h": [], "y": [], "d": []}
    for x in sorted(jl(os.path.join(take, "demo.jsonl")), key=lambda r: r["tick"]):
        k = (x.get("episode_id"), x["tick"])
        if k not in rama:
            continue
        own = rama[k].get("p_corr") or rama[k]["p_ekf"]
        krok = x.get("phase") in ("approach", "orbit") and bool(x.get("track_valid")) and x.get("track_age_s", 9) <= 1.0
        y = np.zeros(3)
        if krok:
            f = np.array(features({"own_pos_ned": own, "own_vel_ned": x["own_vel_ned"], "trk_pos_ned": x["trk_pos_ned"],
                                   "track_age_s": x["track_age_s"], "track_valid": True}))
            xs = (clip_age(f) - m.input_mean) / m.input_std
            yy, h, _ = m.step_np(xs[None], h)
            y = yy[0]
            n = np.linalg.norm(y)
            if n > 3.0:
                y = y * 3.0 / n
            out["d"].append(float(np.max(np.abs(y - np.asarray(x["cmd_v_ned"], float)))))
        out["t"].append(rama[k]["sim"]); out["h"].append(h[0].copy()); out["y"].append(y.copy())
    d = np.array(out["d"]) if out["d"] else np.array([np.inf])
    st = {"n": int(len(out["d"])), "p50": float(np.median(d)), "p95": float(np.quantile(d, 0.95)), "max": float(d.max())}
    return out, st


# ------------------------------------------------------------------ część A
def plan_A(L):
    plan = []
    t_b = L.t_inj - 4.0
    dur = t_b - L.t_mapa0
    assert dur > 8.0, "STOP: faza mapy krótsza niż 8 s"
    sp = dur / 8.0
    for k in range(80):
        plan.append((L.t_mapa0 + k * dur / 80.0, sp))
    t = t_b
    while t < L.t_inj + 8.0 - 1e-9:
        plan.append((t, 1.0)); t += 0.1
    while t < L.t_zp - 1e-9:
        plan.append((t, 8.0)); t += 0.8
    t = L.t_zp
    for _ in range(20):
        plan.append((t, 4.0)); t += 0.4
    return plan, sp


def caps_A(plan):
    n = len(plan)
    k_cut = 80 + 40                                                    # 8 s mapy + 4 s przed cięciem
    k_desc = n - 20
    return [(0, k_cut, CAPS_A[0]), (k_cut, k_cut + 30, CAPS_A[1]), (k_cut + 30, k_cut + 80, CAPS_A[2]),
            (k_cut + 80, k_cut + 140, CAPS_A[3]), (k_cut + 140, k_desc, CAPS_A[4]), (k_desc, n, CAPS_A[5])]


def draw_nadir(canvas, L, dd, t, reg):
    x0, y0, w, h = reg
    cv2.rectangle(canvas, (x0 - 2, y0 - 26), (x0 + w + 2, y0 + h + 2), (20, 20, 20), -1)
    tn = nearest(dd["t"], t, 0.25)
    if tn is not None:
        im = cv2.imread(os.path.join(L.d, "nadir", "frames", dd["idx"][tn]))
        dd["n"] += 1
        canvas[y0:y0 + h, x0:x0 + w] = cv2.resize(im, (w, h), interpolation=cv2.INTER_AREA)
    else:
        canvas[y0:y0 + h, x0:x0 + w] = 40
    nf = L.nf_at(tn if tn is not None else t, 0.01 if tn is not None else 0.25)
    te = (nf or {}).get("teach") or {}
    info = None
    if te.get("faza") == "mapa" and te.get("wlaczony"):
        dd["ost_map"] = (te["wlaczony"]["n"], te["wlaczony"]["kf"])
    if te.get("faza") == "mapa" and dd.get("ost_map"):
        info = ("map", f"map frame {dd['ost_map'][0]} · keyframe {dd['ost_map'][1]}")
    elif te.get("faza") == "lok" and te.get("k") is not None and te.get("zgodne") is not None:
        info = ("lok", f"keyframe {te['k']} · {te['zgodne']} matching points")
    elif te.get("faza") == "lok" and te.get("georef"):
        info = ("lok", f"map closed: {te['georef']['n_kf']} keyframes")
    return info


def render_A(take, out_mp4):
    L = Lot8(take)
    an = json.load(open(os.path.join(take, "wyniki_teach.json")))
    o = next(x for x in an["epizody"] if x["ciecie"])
    oc = L.ocenione()
    assert len(oc) == o["B1"]["ticki_ocenione"], (len(oc), o["B1"]["ticki_ocenione"])
    assert abs(max(r["eU"] for r in oc) - o["B1"]["max_e_do_U"]) <= 1e-4, "HUD ≠ analizator (e/U)"
    assert abs(max(r["e"] for r in oc) - o["e_corr"]["max"]) <= 1e-4, "HUD ≠ analizator (e_corr)"
    rep, st = replay(take)
    brain = st["p95"] <= 5e-3
    print(f"[aktA] kotwica replayu: n={st['n']} p50={st['p50']:.2e} p95={st['p95']:.2e} max={st['max']:.2e} → mini-mózg={brain}")
    edges = V5.top_edges(V7.model_of("ncp"))
    pf = {round(r["t_frame"], 3): r for r in jl(os.path.join(take, "percep_feed.jsonl")) if r.get("t_frame") is not None}
    pfk = sorted(pf)
    cmap = {round(r["sim"], 3): r["f"] for r in jl(os.path.join(take, "cam", "frames_index.jsonl"))}
    ck = sorted(cmap)
    nidx = {round(r["sim"], 3): r["f"] for r in jl(os.path.join(take, "nadir", "frames_index.jsonl"))}
    dd = {"idx": nidx, "t": sorted(nidx), "n": 0}
    panel = Panel8(L, 640, 640, 12.0)
    plan, sp_map = plan_A(L)
    caps = caps_A(plan)
    for c in caps:
        sprawdz_tekst(c[2])
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
        info = draw_nadir(canvas, L, dd, t, nreg)
        canvas[56:696, 0:640] = panel.draw(t)
        if brain:
            i = min(max(bisect.bisect_right(rep["t"], t) - 1, 0), len(rep["t"]) - 1)
            V5.draw_brain(canvas, (1596, 736, 312, 236), rep["h"][i], rep["y"][i], None, edges, mini=True)
        canvas[696:1020, 0:640] = (20, 10, 10)
        r = L.tick(t)
        img = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle([0, 0, 1920, 56], fill=(0, 0, 0, 200))
        P(d, (16, 6), "ACT 8", F_BIG, (255, 220, 90))
        P(d, (190, 14), f"mission clock {t - L.t0:6.1f} s", F_MED)
        d.rectangle([640, 60, 1920, 92], fill=(0, 0, 0, 170))
        P(d, (656, 64), HONESTY, F_S18, (255, 200, 120))
        legend(d, 10, 56 + 6)
        P(d, (nreg[0] + 4, nreg[1] - 24), "downward camera", F_S15, (220, 220, 220))
        d.rectangle([nreg[0] - 2, nreg[1] + nreg[3] + 2, nreg[0] + nreg[2] + 2, nreg[1] + nreg[3] + 24], fill=(0, 0, 0, 220))
        if info:
            P(d, (nreg[0] + 4, nreg[1] + nreg[3] + 4), info[1], F_S15, (90, 230, 255) if info[0] == "map" else (90, 255, 90))
        gps_ok = t < L.t_inj
        P(d, (24, 704), "GPS", F_SML, (150, 150, 160))
        P(d, (24, 728), "OK" if gps_ok else "CUT", F_B36, (120, 255, 120) if gps_ok else (255, 90, 90))
        P(d, (330, 704), "WITHOUT GPS", F_SML, (150, 150, 160))
        P(d, (330, 728), mmss(t - L.t_inj) if not gps_ok else "—", F_B36)
        P(d, (24, 790), "age of last fix", F_SML, (150, 150, 160))
        P(d, (24, 814), f"{r['tau']:.2f} s" if (r and r["tau"] is not None and not gps_ok) else "—", F_B28)
        P(d, (330, 790), "shield refusals (mission)", F_SML, (150, 150, 160))
        P(d, (330, 814), str(sum(1 for x in L.ref_t if x <= t)), F_B28)
        P(d, (24, 866), "corrected position error", F_SML, (150, 150, 160))
        P(d, (24, 890), f"{r['e']:.2f} m" if (r and r["e"] is not None) else "—", F_B28, (90, 230, 255))
        P(d, (330, 866), "raw estimator ↔ truth", F_SML, (150, 150, 160))
        P(d, (330, 890), f"{r['e_ekf']:.2f} m" if (r and r["e_ekf"] is not None) else "—", F_B28, (255, 190, 80))
        P(d, (24, 944), "errors vs simulator truth, analyser time canon", F_S15, (130, 130, 140))
        if brain:
            d.rectangle([1596, 736 - 24, 1596 + 312, 736 - 2], fill=(0, 0, 0, 170))
            P(d, (1596 + 8, 736 - 22), "INSIDE THE NETWORK (it flies)", F_S15, (255, 220, 120))
            d.rectangle([1596, 736 + 236 + 2, 1596 + 312, 736 + 236 + 24], fill=(0, 0, 0, 170))
            P(d, (1596 + 8, 736 + 236 + 4), "replay of the log (steers nothing)", F_S15, (200, 180, 140))
        if sp != 1.0:
            d.rectangle([1600, 4, 1904, 52], fill=(0, 0, 0, 220))
            P(d, (1620, 8), f"SPEED ×{sp:.1f}" if abs(sp - round(sp)) > 1e-6 else f"SPEED ×{sp:g}", F_BIG, (255, 160, 60))
        cap = next((c[2] for c in caps if c[0] <= n < c[1]), None)
        if cap:
            d.rectangle([0, 1020, 1920, 1080], fill=(0, 0, 0, 220))
            P(d, (24, 1032), cap, F_MED)
        vw.write(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))
        n += 1
    vw.release()
    res = {"klatek": n, "dur_s": n / 10.0, "klatki_cam": n_cam, "klatki_nadir": dd["n"], "kotwica": st, "mini_mozg": brain,
           "tempo_mapy": round(sp_map, 3), "t_mapa0": L.t_mapa0, "t_georef": L.t_georef, "t_inj": L.t_inj, "t_zp": L.t_zp,
           "kontynuacja": round(L.t_zp - L.t_inj, 3), "klatki_kluczowe": len(L.kf), "ticki_ocenione": len(oc),
           "max_e_do_U": round(max(x["eU"] for x in oc), 4), "max_e": round(max(x["e"] for x in oc), 4),
           "napisy": [[a / 10, b / 10, c] for a, b, c in caps]}
    print(f"[aktA] {n} klatek ({n / 10:.1f} s), kamera {n_cam}/{n}, nadir {dd['n']}/{n}, tempo mapy ×{sp_map:.2f} → {out_mp4}")
    return res


# ------------------------------------------------------------------ część B
def asercje_B(L):
    s = json.load(open(os.path.join(LONG, "sedzia_teach2.json")))
    oc = [r for r in L.ocenione() if r["sim"] < L.t_zp + 60]
    kont = round(L.t_zp - L.t_inj, 2)
    pop = [r for r in jl(os.path.join(LONG, "poprawki_teach2.jsonl")) if s["misja"]["okno"][0] <= r["sim"] <= s["misja"]["okno"][1]]
    ekf = max(r["e_ekf"] for r in L.tk if r["e_ekf"] is not None and r["ph"] in UTRATA and r["sim"] < L.t_zp)
    a = {"kontynuacja_s": kont, "ticki_ocenione": len(L.ocenione()), "przekroczenia": sum(1 for r in L.ocenione() if r["eU"] > 1.0),
         "max_e_do_U": round(max(r["eU"] for r in L.ocenione()), 4), "blad_poprawki_max": round(max(r["blad"] for r in pop), 4),
         "poprawki_w_misji": len(pop), "track": s["misja"]["track"], "odmowy_misja": len(L.ref_t),
         "refuse_misja_sedzia": s["epizod"]["D_L"]["refuse_misja"], "blad_ekf_max_m": round(ekf, 3), "blad_ekf_sedzia": s["misja"]["blad_ekf"]["max"]}
    print("[aktB] asercje", a)
    assert abs(kont - 600.52) <= 0.01 and round(kont, 1) == 600.5, a
    assert a["ticki_ocenione"] == 12638 and a["przekroczenia"] == 0, a
    assert round(a["max_e_do_U"], 2) == 0.24, a
    assert a["blad_poprawki_max"] <= 0.45 and abs(a["blad_poprawki_max"] - s["misja"]["blad_poprawki"]["max"]) <= 1e-4, a
    assert a["track"] == 1.0 and a["odmowy_misja"] == 0 and a["refuse_misja_sedzia"] == 0, a
    assert round(a["blad_ekf_max_m"], 1) == 17.4 and abs(a["blad_ekf_max_m"] - a["blad_ekf_sedzia"]) <= 0.05, a
    return a, pop


def data_lotu():
    ts = next(r["ts"] for r in jl(os.path.join(LONG, "trace.jsonl")) if r.get("ts"))
    return datetime.datetime.fromtimestamp(ts).strftime("%d.%m.%Y")


def render_B(out_mp4):
    L = Lot8(LONG)
    a, pop = asercje_B(L)
    data = data_lotu()
    if data != DATA_PROMPT:
        print(f"[aktB] data z logu {data} ≠ {DATA_PROMPT} z promptu — idzie data z logu")
    b_sub = B_SUB_T.format(data=data)
    for s in (b_sub, B_MAP, B_FINAL):
        sprawdz_tekst(s)
    kadry = sorted(os.listdir(os.path.join(LONG, "kadry")))
    kt = [float(k[:-4]) for k in kadry]
    W = 1920
    panel = Panel8(L, 720, 720, 60.0)
    plan = []
    t = L.t0
    while t <= L.t_zp + 1e-9:
        plan.append(t); t += 3.0
    pt = np.array([r["sim"] for r in pop]); pb = np.array([r["blad"] for r in pop])
    et = np.array([r["sim"] for r in L.tk if r["e_ekf"] is not None]); eb = np.array([r["e_ekf"] for r in L.tk if r["e_ekf"] is not None])
    gx0, gx1, gy = 120, 1000, (812, 990)                                     # wykres: oś czasu wspólna, dwa pasy (812–872, 896–990)
    T0, T1 = L.t0, L.t_zp
    X = lambda tt: int(gx0 + (tt - T0) / (T1 - T0) * (gx1 - gx0))
    vw = cv2.VideoWriter(out_mp4, cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (W, 1080))
    eU_max = 0.0
    n_fin = 60
    for k, t in enumerate(plan):
        canvas = np.full((1080, W, 3), 12, np.uint8)
        canvas[60:780, 280:1000] = panel.draw(t)
        # wykres
        cv2.rectangle(canvas, (gx0, gy[0]), (gx1, gy[0] + 70), (24, 24, 28), -1)
        cv2.rectangle(canvas, (gx0, gy[0] + 84), (gx1, gy[1]), (24, 24, 28), -1)
        xc = X(L.t_inj)
        cv2.line(canvas, (xc, gy[0]), (xc, gy[1]), (90, 90, 255), 1, cv2.LINE_AA)
        m = et <= t
        if m.any():
            ys = (gy[0] + 70 - np.clip(eb[m] / 20.0, 0, 1) * 70).astype(int)
            xs = np.array([X(x) for x in et[m]])
            cv2.polylines(canvas, [np.stack([xs, ys], 1).astype(np.int32)], False, (80, 190, 255), 1, cv2.LINE_AA)
        m = pt <= t
        if m.any():
            for xx, yy in zip(pt[m][::3], pb[m][::3]):
                cv2.circle(canvas, (X(xx), int(gy[1] - min(yy, 1.0) * 90)), 1, (90, 230, 255), -1)          # BGR = żółty legendy
        y45 = int(gy[1] - 0.45 * 90)
        cv2.line(canvas, (gx0, y45), (gx1, y45), (90, 90, 110), 1)
        tcur = min(t, T1)
        cv2.line(canvas, (X(tcur), gy[0]), (X(tcur), gy[1]), (200, 200, 210), 1)
        for e in L.series(t, 3.0):
            if e["eU"] is not None:
                eU_max = max(eU_max, e["eU"])
        r = L.tick(t)
        img = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
        if t >= kt[0]:
            j = bisect.bisect_right(kt, t) - 1
            mini = Image.open(os.path.join(LONG, "kadry", kadry[j])).convert("RGB").resize((320, 240))
            img.paste(mini, (1520, 700))
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle([0, 0, W, 56], fill=(0, 0, 0, 200))
        P(d, (16, 6), "ACT 8 — 10 minutes without GPS, without markers", F_BIG, (255, 220, 90))
        d.rectangle([1600, 60, 1910, 104], fill=(0, 0, 0, 220))
        P(d, (1620, 60), "SPEED ×30", F_BIG, (255, 160, 60))
        d.rectangle([280, 60, 1000, 84], fill=(0, 0, 0, 170))
        P(d, (288, 62), b_sub, F_S15, (255, 200, 120))
        for k2, (txt, col) in enumerate((("● truth (simulator)", (120, 255, 120)), ("◯ corrected position", (90, 230, 255)),
                                         ("∘ raw estimator", (255, 190, 80)), ("● intruder", (255, 60, 60)),
                                         ("▭ map keyframes (15)", (170, 170, 170)), (f"○ zone {R_E:.0f} m", (200, 100, 120)))):
            P(d, (24, 120 + 30 * k2), txt, F_S18, col)
        P(d, (gx0, gy[0] - 26), "raw estimator vs truth (0–20 m)", F_S15, (255, 190, 80))
        P(d, (gx0, gy[0] + 72), "error of each map fix (0–1 m) · line = 0.45 m", F_S15, (255, 230, 90))
        P(d, (gx0 + 420, gy[0] - 26), "│ blue line = GPS cut", F_S15, (150, 150, 255))
        x = 1090
        P(d, (x, 120), "flight clock", F_SML, (150, 150, 160))
        P(d, (x, 146), mmss(min(t, T1) - L.t0), F_B36)
        P(d, (x + 300, 120), "WITHOUT GPS", F_SML, (150, 150, 160))
        P(d, (x + 300, 146), mmss(min(t, T1) - L.t_inj) if t >= L.t_inj else "—", F_B36)
        P(d, (x, 230), "corrected position error", F_SML, (150, 150, 160))
        P(d, (x, 256), f"{r['e']:.2f} m" if r and r["e"] is not None else "—", F_B36, (90, 230, 255))
        P(d, (x, 330), "raw estimator vs truth", F_SML, (150, 150, 160))
        P(d, (x, 356), f"{r['e_ekf']:.1f} m" if r and r["e_ekf"] is not None else "—", F_B36, (255, 190, 80))
        P(d, (x, 430), "share of the proof's error bound used", F_SML, (150, 150, 160))
        P(d, (x, 456), f"{100 * r['eU']:.0f}%" if r and r["eU"] is not None else "—", F_B36)
        P(d, (x + 200, 468), f"max so far {100 * eU_max:.0f}%", F_SML, (200, 200, 210))
        P(d, (x, 530), "shield refusals", F_SML, (150, 150, 160))
        P(d, (x, 556), str(sum(1 for z in L.ref_t if z <= t)), F_B36)
        P(d, (x, 640), "errors vs simulator truth", F_S18, (130, 130, 140))
        if t >= kt[0]:
            P(d, (1520, 946), f"downward camera, t = {kt[j] - L.t0:.0f} s", F_S15, (200, 200, 200))
        if k >= len(plan) - n_fin:
            d.rectangle([0, 1008, W, 1080], fill=(0, 0, 0, 230))
            lines = V7.wrap(d, B_FINAL, F_SML, 1870)
            assert " ".join(lines) == B_FINAL and len(lines) <= 2
            for i2, ln in enumerate(lines):
                P(d, (24, 1012 + 30 * i2), ln, F_SML, (255, 230, 150))
        elif t < L.t_inj:
            d.rectangle([0, 1020, W, 1080], fill=(0, 0, 0, 220))
            P(d, (24, 1032), B_MAP, F_MED)
        vw.write(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))
    vw.release()
    print(f"[aktB] {len(plan)} klatek ({len(plan) / 10:.1f} s) → {out_mp4}")
    return {"klatek": len(plan), "dur_s": len(plan) / 10.0, "asercje": a, "data_lotu": data, "napis_daty": b_sub, "klatki_kluczowe": len(L.kf),
            "kadry": kadry, "t_wideo_ciecia": next(i for i, x in enumerate(plan) if x >= L.t_inj) / 10.0}


# ------------------------------------------------------------------ karty, plansza, montaż
PLANSZA8 = None


def plansza8():
    import democ_en_71 as E
    pl = list(E.PLANSZA_EN)
    assert pl[-1].startswith("Home hardware")
    pl = pl[:-1] + [LINE_V8] + pl[-1:]
    img = Image.new("RGB", (1920, 1080), (8, 10, 16))
    d = ImageDraw.Draw(img)
    col = dict(V7.COL7); col[len(pl) - 2] = (150, 220, 255)
    y = 140
    for i, ln in enumerate(pl):
        sprawdz_tekst(ln)
        f = F_T if i == 0 else F_M38
        w = d.textlength(ln, font=f)
        assert w <= 1880, f"linia planszy za szeroka: {ln}"
        d.text(((1920 - w) / 2, y), ln, font=f, fill=(255, 220, 90) if i == 0 else col.get(i, (235, 235, 235)))
        y += 92 if i == 0 else 62
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR), pl


def karty(outd):
    os.makedirs(outd, exist_ok=True)
    res = {}
    sprawdz_tekst(CARD_IN); sprawdz_tekst(CARD_SCOPE)
    for nm, rys, sek in (("karta_wejscia_v8", lambda: V7.karta(CARD_IN)[0], 5), ("karta_zakresu_v8", lambda: V7.karta(CARD_SCOPE)[0], 6),
                         ("plansza_v8", lambda: plansza8()[0], 9)):
        img = rys()
        cv2.imwrite(os.path.join(outd, nm + ".png"), img)
        vw = cv2.VideoWriter(os.path.join(outd, nm + ".mp4"), cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (1920, 1080))
        for _ in range(sek * 10):
            vw.write(img)
        vw.release()
        res[nm] = sek
    print("[karty]", res)
    return res


def nframes(p):
    c = cv2.VideoCapture(p); n = int(c.get(cv2.CAP_PROP_FRAME_COUNT)); c.release()
    return n


def cut(v71_mp4, outd):
    """v8 EN = v7.1 EN bez planszy (ostatnie 90 klatek) + karta 8 + A + B + karta zakresu + plansza v8; klip NOMARKERS; srt; kontaktówka."""
    dc = os.path.join(ROOT, "results", "DEMO_C")
    czesci = [os.path.join(outd, x + ".mp4") for x in ("karta_wejscia_v8", "akt8_A", "akt8_B", "karta_zakresu_v8")]
    pl = os.path.join(outd, "plansza_v8.mp4")
    n71 = nframes(v71_mp4); keep = n71 - 90
    dl = [nframes(p) for p in czesci]
    t8, tn = (keep + sum(dl) + 90) / 10.0, (sum(dl) + 90) / 10.0
    assert t8 <= 390.0, f"v8 {t8:.1f} s > 390 s"
    assert tn <= 90.0, f"klip NOMARKERS {tn:.1f} s > 90 s"

    def frames(p):
        c = cv2.VideoCapture(p)
        while True:
            ok, fr = c.read()
            if not ok:
                break
            assert fr.shape == (1080, 1920, 3)
            yield fr
        c.release()
    vw = cv2.VideoWriter(os.path.join(dc, "DEMO_C_v8_EN.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (1920, 1080))
    k = 0
    for fr in frames(v71_mp4):
        if k >= keep:
            break
        vw.write(fr); k += 1
    assert k == keep
    for p in czesci + [pl]:
        for fr in frames(p):
            vw.write(fr)
    vw.release()
    vg = cv2.VideoWriter(os.path.join(dc, "DEMO_C_v8_NOMARKERS_EN.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (1920, 1080))
    for p in czesci + [pl]:
        for fr in frames(p):
            vg.write(fr)
    vg.release()
    # SRT: bloki v7 EN (te same czasy co v7.1) bez planszy + akt 8 + plansza v8
    blocks = open(os.path.join(dc, "DEMO_C_v7_en.srt")).read().strip().split("\n\n")
    v7_pl = blocks[-1].split("\n", 2)[2]
    blocks = blocks[:-1]
    t = keep / 10.0
    rA = json.load(open(os.path.join(outd, "akt8_A.json"))); rB = json.load(open(os.path.join(outd, "akt8_B.json")))
    dA, dB = dl[1] / 10.0, dl[2] / 10.0
    ev = [(t, t + 5, CARD_IN)]
    tA = t + 5
    for a, b, txt in rA["napisy"]:
        ev.append((tA + a, tA + b, txt))
    tB = tA + dA
    t_cut_B = rB.get("t_wideo_ciecia", dB - 6.0)
    ev.append((tB, tB + dB, rB["napis_daty"]))
    ev.append((tB, tB + t_cut_B, B_MAP))
    ev.append((tB + dB - 6.0, tB + dB, B_FINAL))
    tS = tB + dB
    ev.append((tS, tS + 6, CARD_SCOPE))
    tP = tS + 6
    _, pl8 = plansza8()                                                       # linie planszy sprawdzone każda osobno w plansza8()
    ev.append((tP, tP + 9, " ".join(pl8)))
    idx = len(blocks) + 1
    for a, b, txt in ev:
        if a != tP:
            sprawdz_tekst(txt)
        blocks.append(f"{idx}\n{V5.srt_time(a)} --> {V5.srt_time(b)}\n{txt}"); idx += 1
    open(os.path.join(dc, "DEMO_C_v8_en.srt"), "w").write("\n\n".join(blocks) + "\n")
    print(f"[cut_v8] v7.1 bez planszy {keep / 10:.1f} s + akt 8 {sum(dl) / 10:.1f} s + plansza 9 s = {t8:.1f} s; NOMARKERS {tn:.1f} s")
    return {"v8_s": t8, "nomarkers_s": tn, "czesci_s": [x / 10 for x in dl], "v71_bez_planszy_s": keep / 10, "v7_plansza_srt": v7_pl}


def kontaktowka(outd, out_jpg):
    """Kontaktówka: po 6 klatek z części A i B (równomiernie) + karty, 4 kolumny."""
    sel = []
    for nm, k in (("akt8_A.mp4", 8), ("akt8_B.mp4", 6)):
        p = os.path.join(outd, nm); n = nframes(p)
        want = set(int(i) for i in np.linspace(0, n - 1, k))
        c = cv2.VideoCapture(p); i = 0
        while True:
            ok, fr = c.read()
            if not ok:
                break
            if i in want:
                sel.append(fr)
            i += 1
        c.release()
    for nm in ("karta_wejscia_v8.png", "karta_zakresu_v8.png"):
        sel.append(cv2.imread(os.path.join(outd, nm)))
    th = [cv2.resize(x, (480, 270)) for x in sel]
    while len(th) % 4:
        th.append(np.zeros_like(th[0]))
    rows = [np.hstack(th[i:i + 4]) for i in range(0, len(th), 4)]
    cv2.imwrite(out_jpg, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])


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
    elif m == "kontaktowka":
        kontaktowka(sys.argv[2], sys.argv[3]); r = {}
    r = r or {}
    r["napisy_unikalne"] = sorted(set(NAPISY))[:400]
    print(json.dumps(r, default=float, ensure_ascii=False)[:3000])
    if m in ("aktA", "aktB"):
        out = sys.argv[3] if m == "aktA" else sys.argv[2]
        json.dump(r, open(out[:-4] + ".json", "w"), default=float, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
