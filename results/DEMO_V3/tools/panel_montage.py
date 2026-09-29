#!/usr/bin/env python3
"""results/DEMO_V3/tools/panel_montage.py — panel opisowy OBOK obrazu + montaż real-time (PROMPT_DEMO_V3 §1/§5).

Canvas 1920x1080: klatka lotu 1280x720 skalowana do lewej strefy (1320x742, letterbox), panel 600 px
po prawej. Dane panelu WYŁĄCZNIE z artefaktów bootu (trace.jsonl / demo.jsonl / frames_index.jsonl /
boot.ulg przez tools.w_tilt.tilt_series / manifest.json) — zero odczytów „z oka". Czas materiału =
czas symulacji 1:1 (bez przyspieszeń); cięcia tylko na granicach aktów (składane w `concat`).

Podkomendy:
  act <run_dir> <act_json> <out.mp4>   — segment aktu (act_json: label/wind/t0/t1/postroll itd.)
  title <captions.txt> <KEY> <secs> <out.mp4>  — plansza (tekst [KEY] z CAPTIONS_VERBATIM.txt)
  concat <out.mp4> <in1.mp4> [in2...]  — sklejka segmentów (re-mux klatek, ten sam format)
  sanity <run_dir> <act_json> <sim_t1,sim_t2,sim_t3> <outdir>  — 3 klatki kontrolne (wzór U1R):
         PNG + verbatim wartości źródłowe (mode/z/wiatr/tilt) do sanity.json

Captions: CAPTIONS_VERBATIM.txt, linie `[KEY @ t0-t1] tekst` (t w sim_t aktu) oraz plansze
`[KEY] tekst` (\\n = nowa linia). Wyłącznie zdania opisowe + zdania kanonów (D3-2).
MODE (deterministycznie): przed episode_start=PATROL · phase=orbit→OBSERVE · inna faza→PATROL ·
od eventu refuse→REFUSE · po episode_end (lot trwa)→DESCENT.
"""
import json, math, os, sys, glob, bisect

import numpy as np
import cv2

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, ROOT)

W, H = 1920, 1080
PANEL_W = 600
FLIGHT_W, FLIGHT_H = W - PANEL_W, H          # 1320x1080 strefa, obraz letterbox
FPS = 10
V_E = 20.0
R_E = 32.0

BG = (24, 22, 20)          # BGR
PANEL_BG = (34, 30, 28)
FG = (225, 225, 220)
DIM = (150, 148, 143)
RED = (60, 60, 230)
GRN = (110, 200, 120)
AMB = (60, 170, 240)
BLU = (235, 180, 90)
MODE_COLORS = {"PATROL": BLU, "OBSERVE": GRN, "REFUSE": RED, "DESCENT": AMB}
F = cv2.FONT_HERSHEY_SIMPLEX


# ---------------- dane bootu ----------------
class RunData:
    def __init__(self, run_dir):
        self.dir = run_dir
        self.manifest = json.load(open(os.path.join(run_dir, "manifest.json")))
        self.frames = []           # (sim, idx)
        for ln in open(os.path.join(run_dir, "frames_index.jsonl")):
            r = json.loads(ln); self.frames.append((r["sim"], r["idx"]))
        self.frames.sort()
        self.f_sims = [s for s, _ in self.frames]
        self.demo = []             # rows z demo.jsonl (t_sim rosnąco)
        for ln in open(os.path.join(run_dir, "demo.jsonl")):
            self.demo.append(json.loads(ln))
        self.d_sims = [r["t_sim"] for r in self.demo]
        self.events = []
        gt_mono, gt_sim = [], []
        self.gt = []               # (sim, x,y,z ENU)
        for ln in open(os.path.join(run_dir, "trace.jsonl")):
            r = json.loads(ln)
            if r.get("t") == "event":
                self.events.append(r)
            elif r.get("t") == "gt":
                gt_mono.append(r["mono"]); gt_sim.append(r["sim"])
                self.gt.append((r["sim"], r["x"], r["y"], r["z"]))
        self.gt.sort(); self.g_sims = [g[0] for g in self.gt]
        self.t_ep0 = next((e["sim"] for e in self.events if e["ev"] == "episode_start"), None)
        self.t_refuse = next((e["sim"] for e in self.events if e["ev"] == "refuse"), None)
        self.refuse_reason = next((e.get("reason") for e in self.events if e["ev"] == "refuse"), None)
        self.t_ep_end = next((e["sim"] for e in self.events if e["ev"] == "episode_end"), None)
        # tilt: ulog t_us ~= sim*1e6 (lockstep SITL — most jak w tools/w_tilt.py)
        from tools.w_tilt import tilt_series
        ul = os.path.join(run_dir, "boot.ulg")
        self.tilt = [(t / 1e6, d) for t, d in tilt_series(ul)] if os.path.exists(ul) else []
        self.tl_sims = [t for t, _ in self.tilt]

    def frame_at(self, sim):
        i = bisect.bisect_right(self.f_sims, sim) - 1
        i = max(0, i)
        idx = self.frames[i][1]
        return np.load(os.path.join(self.dir, "frames", f"f_{idx:06d}.npy"))

    def demo_at(self, sim):
        i = bisect.bisect_right(self.d_sims, sim) - 1
        return self.demo[max(0, i)] if self.demo else None

    def gt_at(self, sim):
        i = bisect.bisect_right(self.g_sims, sim) - 1
        return self.gt[max(0, i)] if self.gt else None

    def tilt_at(self, sim):
        if not self.tilt:
            return None
        i = bisect.bisect_right(self.tl_sims, sim) - 1
        return self.tilt[max(0, i)][1]

    def mode_at(self, sim):
        if self.t_refuse is not None and sim >= self.t_refuse:
            return "REFUSE" if sim < (self.t_refuse + 3.0) else "DESCENT"
        if self.t_ep_end is not None and sim >= self.t_ep_end:
            return "DESCENT"
        d = self.demo_at(sim)
        if self.t_ep0 is not None and sim >= self.t_ep0 and d and d.get("phase") == "orbit":
            return "OBSERVE"
        return "PATROL"


# ---------------- captions ----------------
def load_captions(path):
    timed, cards = {}, {}
    for ln in open(path, encoding="utf-8"):
        ln = ln.rstrip("\n")
        if not ln.startswith("["):
            continue
        head, _, text = ln.partition("] ")
        head = head[1:]
        if " @ " in head:
            key, rng = head.split(" @ ")
            t0, t1 = (float(x) for x in rng.split("-"))
            timed.setdefault(key, []).append((t0, t1, text))
        else:
            cards[head] = text.replace("\\n", "\n")
    return timed, cards


def caption_at(entries, t_rel):
    for t0, t1, text in entries:
        if t0 <= t_rel <= t1:
            return text
    return None


# ---------------- rysowanie panelu ----------------
def _txt(img, s, xy, scale=0.55, color=FG, th=1):
    cv2.putText(img, s, xy, F, scale, color, th, cv2.LINE_AA)


def _wrap(s, width=40):
    out, cur = [], ""
    for w in s.split():
        if len(cur) + len(w) + 1 > width:
            out.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        out.append(cur)
    return out


def draw_panel(panel, rd, cfg, sim, trail, t_cap=None):
    panel[:] = PANEL_BG
    x0 = 30
    _txt(panel, "LIQUIDPATROL - DEMO_V3", (x0, 42), 0.62, DIM, 1)
    _txt(panel, cfg["label"], (x0, 78), 0.7, FG, 2)
    t_rel = sim - cfg["t0"]
    _txt(panel, f"sim_t {sim:8.2f} s", (x0, 112), 0.6, FG, 1)
    # MODE
    mode = rd.mode_at(sim)
    c = MODE_COLORS[mode]
    cv2.rectangle(panel, (x0, 130), (PANEL_W - 30, 178), c, 2)
    _txt(panel, f"MODE  {mode}", (x0 + 14, 163), 0.85, c, 2)
    if mode == "REFUSE" and rd.refuse_reason:
        _txt(panel, f"reason: {rd.refuse_reason}", (x0, 200), 0.55, RED, 1)
    # wiatr + przechył
    wx, wy = cfg["wind"][0], cfg["wind"][1]
    wmag = math.hypot(wx, wy)
    _txt(panel, f"wind  {wmag:.1f} m/s", (x0, 238), 0.6, FG, 1)
    cxa, cya = PANEL_W - 90, 232
    cv2.circle(panel, (cxa, cya), 24, DIM, 1)
    _txt(panel, "N", (cxa - 6, cya - 30), 0.4, DIM, 1)
    if wmag > 0.05:
        ang = math.atan2(wx, wy)      # ENU: strzałka DOKĄD wieje, N w górę
        dx, dy = math.sin(ang), -math.cos(ang)
        cv2.arrowedLine(panel, (int(cxa - dx * 18), int(cya - dy * 18)),
                        (int(cxa + dx * 18), int(cya + dy * 18)), BLU, 2, tipLength=0.35)
    tl = rd.tilt_at(sim)
    _txt(panel, f"tilt  {tl:5.1f} deg" if tl is not None else "tilt   n/a", (x0, 272), 0.6, FG, 1)
    # wysokość: pasek pionowy z linią V_E
    bx, by0, by1 = x0 + 10, 320, 620
    zmax_bar = 24.0
    cv2.rectangle(panel, (bx, by0), (bx + 26, by1), DIM, 1)
    g = rd.gt_at(sim)
    z = g[3] if g else 0.0
    zy = int(by1 - (min(z, zmax_bar) / zmax_bar) * (by1 - by0))
    cv2.rectangle(panel, (bx + 1, zy), (bx + 25, by1 - 1), (90, 140, 90), -1)
    vey = int(by1 - (V_E / zmax_bar) * (by1 - by0))
    cv2.line(panel, (bx - 8, vey), (bx + 60, vey), RED, 2)
    _txt(panel, f"V_E {V_E:.0f} m", (bx + 66, vey + 5), 0.5, RED, 1)
    _txt(panel, f"alt {z:5.1f} m", (bx + 50, by0 + 16), 0.6, FG, 1)
    # dystanse
    d = rd.demo_at(sim)
    if d:
        own = d["own_pos_ned"]; trk = d["trk_pos_ned"]
        r_home = math.hypot(own[0], own[1])
        if d.get("track_valid"):
            di = math.hypot(trk[0] - own[0], trk[1] - own[1])
            _txt(panel, f"range to intruder {di:5.1f} m", (x0 + 120, 360), 0.55, FG, 1)
        _txt(panel, f"r from home {r_home:5.1f} m", (x0 + 120, 392), 0.55, FG, 1)
        _txt(panel, f"R_E {R_E:.0f} m  (margin {R_E - r_home:4.1f})", (x0 + 120, 424), 0.5, DIM, 1)
    # minimapa top-down (dodatek ponad liste §5 — flagowane w raporcie)
    mcx, mcy, mr = PANEL_W - 150, 520, 105
    cv2.circle(panel, (mcx, mcy), mr, DIM, 1)                       # R_E=32
    _txt(panel, "top-down / circle = R_E = 32 m", (mcx - 105, mcy + mr + 22), 0.42, DIM, 1)
    scale = mr / R_E
    cv2.circle(panel, (mcx, mcy), 3, FG, -1)                        # home
    for (px, py, col) in trail:
        cv2.circle(panel, (int(mcx + px * scale), int(mcy - py * scale)), 1, col, -1)
    if d:
        own = d["own_pos_ned"]
        cv2.circle(panel, (int(mcx + own[1] * scale), int(mcy - own[0] * scale)), 4, GRN, -1)
        if d.get("track_valid"):
            trk = d["trk_pos_ned"]
            cv2.circle(panel, (int(mcx + trk[1] * scale), int(mcy - trk[0] * scale)), 4, RED, -1)
    # caption
    cap = caption_at(cfg["_captions"], t_rel if t_cap is None else t_cap)
    if cap:
        lines = _wrap(cap, 46)
        y = H - 46 - 20 * 3 - 18 - 30 * len(lines)
        for line in lines:
            _txt(panel, line, (x0, y), 0.55, FG, 1)
            y += 30
    # footer E3 (staly przez film)
    y = H - 46
    for line in _wrap(cfg["_footer"], 60):
        _txt(panel, line, (x0, y), 0.4, DIM, 1)
        y += 20


def compose(rd, cfg, sim, trail, t_cap=None, speed=1):
    canvas = np.zeros((H, W, 3), np.uint8); canvas[:] = BG
    fr = rd.frame_at(sim)
    if fr.ndim == 2:
        fr = cv2.cvtColor(fr, cv2.COLOR_GRAY2BGR)
    else:
        fr = fr[:, :, :3][:, :, ::-1]      # RGB→BGR
    fh = int(FLIGHT_W * fr.shape[0] / fr.shape[1])
    fr = cv2.resize(fr, (FLIGHT_W, fh))
    y0 = (H - fh) // 2
    canvas[y0:y0 + fh, 0:FLIGHT_W] = fr
    panel = canvas[:, FLIGHT_W:W]
    draw_panel(panel, rd, cfg, sim, trail, t_cap=t_cap)
    if speed and speed > 1:
        cv2.putText(canvas, f"x{speed:g}", (24, 60), F, 1.4, (60, 200, 245), 3, cv2.LINE_AA)
    return canvas


# ---------------- podkomendy ----------------
def cmd_act(run_dir, act_json, out_mp4):
    cfg = json.load(open(act_json))
    timed, cards = load_captions(cfg["captions"])
    cfg["_captions"] = timed.get(cfg["cap_key"], [])
    cfg["_footer"] = cards["FOOTER"]
    rd = RunData(run_dir)
    vw = cv2.VideoWriter(out_mp4, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
    trail = []
    n = int((cfg["t1"] - cfg["t0"]) * FPS)
    for k in range(n):
        sim = cfg["t0"] + k / FPS
        if k % (2 * FPS) == 0:
            d = rd.demo_at(sim)
            if d:
                own = d["own_pos_ned"]; trail.append((own[1], own[0], (90, 130, 90)))
        vw.write(compose(rd, cfg, sim, trail))
    vw.release()
    print(f"[act] {out_mp4}  {n} klatek @ {FPS} fps = {n / FPS:.1f} s (sim {cfg['t0']}..{cfg['t1']})")


def _card(text, secs, out_mp4):
    vw = cv2.VideoWriter(out_mp4, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
    img = np.zeros((H, W, 3), np.uint8); img[:] = BG
    lines = []
    for para in text.split("\n"):
        lines.extend(_wrap(para, 78) or [""])
    y = H // 2 - 18 * len(lines)
    for ln in lines:
        sz = cv2.getTextSize(ln, F, 0.8, 1)[0]
        cv2.putText(img, ln, ((W - sz[0]) // 2, y), F, 0.8, FG, 1, cv2.LINE_AA)
        y += 40
    for _ in range(int(secs * FPS)):
        vw.write(img)
    vw.release()
    print(f"[title] {out_mp4}  {secs}s")


def cmd_title(captions, key, secs, out_mp4):
    _, cards = load_captions(captions)
    _card(cards[key], float(secs), out_mp4)


def cmd_concat(out_mp4, parts):
    vw = cv2.VideoWriter(out_mp4, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
    tot = 0
    for p in parts:
        c = cv2.VideoCapture(p)
        while True:
            ok, fr = c.read()
            if not ok:
                break
            vw.write(fr); tot += 1
        c.release()
    vw.release()
    print(f"[concat] {out_mp4}  {tot} klatek = {tot / FPS:.1f} s z {len(parts)} segmentów")


def cmd_sanity(run_dir, act_json, sims, outdir):
    cfg = json.load(open(act_json))
    timed, cards = load_captions(cfg["captions"])
    cfg["_captions"] = timed.get(cfg["cap_key"], [])
    cfg["_footer"] = cards["FOOTER"]
    rd = RunData(run_dir)
    os.makedirs(outdir, exist_ok=True)
    rep = []
    for s in sims:
        img = compose(rd, cfg, s, [])
        cv2.imwrite(os.path.join(outdir, f"sanity_{s:.1f}.png"), img)
        g = rd.gt_at(s); d = rd.demo_at(s)
        rep.append({"sim_t": s, "mode": rd.mode_at(s), "z_gt": round(g[3], 3) if g else None,
                    "tilt_deg": round(rd.tilt_at(s), 2) if rd.tilt_at(s) is not None else None,
                    "wind_cfg": cfg["wind"],
                    "own_pos_ned": d["own_pos_ned"] if d else None,
                    "phase_demo": d.get("phase") if d else None})
    json.dump(rep, open(os.path.join(outdir, "sanity.json"), "w"), indent=1)
    print(json.dumps(rep, indent=1))


def cmd_cut(run_dir, cut_json, out_mp4):
    """ANEKS_DEMO3-3: cut dynamiczny — segmenty [t0,t1,speed] (speed=N => xN, N<=8, marker jawny);
    captions kluczowane czasem WYJSCIOWYM (reflow, zdania nietykalne); sim_t stale widoczny (panel)."""
    cfg = json.load(open(cut_json))
    timed, cards = load_captions(cfg["captions"])
    cfg["_captions"] = timed.get(cfg["cap_key"], [])
    cfg["_footer"] = cards["FOOTER"]
    rd = RunData(run_dir)
    vw = cv2.VideoWriter(out_mp4, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
    trail = []
    t_out = 0.0
    last_trail_sim = -1e9
    for seg in cfg["segments"]:
        sp = seg.get("speed", 1)
        assert sp <= 8, "N>8 zakazane (ANEKS_DEMO3-3)"
        n = int(round((seg["t1"] - seg["t0"]) / sp * FPS))
        for k in range(n):
            sim = seg["t0"] + k * sp / FPS
            if sim - last_trail_sim >= 2.0:
                d = rd.demo_at(sim)
                if d:
                    own = d["own_pos_ned"]; trail.append((own[1], own[0], (90, 130, 90)))
                last_trail_sim = sim
            vw.write(compose(rd, cfg, sim, trail, t_cap=t_out, speed=sp))
            t_out += 1.0 / FPS
    vw.release()
    print(f"[cut] {out_mp4}  {t_out:.1f} s wyjscia z {len(cfg['segments'])} segmentow")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "act":
        cmd_act(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "title":
        cmd_title(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    elif cmd == "cut":
        cmd_cut(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "concat":
        cmd_concat(sys.argv[2], sys.argv[3:])
    elif cmd == "sanity":
        cmd_sanity(sys.argv[2], sys.argv[3], [float(x) for x in sys.argv[4].split(",")], sys.argv[5])
    else:
        raise SystemExit("act|title|concat|sanity")
