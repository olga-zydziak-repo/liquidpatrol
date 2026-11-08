#!/usr/bin/env python3
"""results/KOTW_RECON/tools/kotw_r1.py — R1 PROMPT_KOTW_S0: widoczność hipotetycznej kotwicy w (0,0) w istniejących lotach.

Źródła (odczyt): trace.jsonl rekordy "gt" (poza gz modelu drona: ENU, kwaternion body FLU→świat, ~50 Hz; ramka
ustalona empirycznie: N = gt.y, E = gt.x, yaw_NED = 90° − yaw_ENU, zgodność z EKF ~2° w nom_b1_r5) oraz demo.jsonl
(t_sim, episode_id, scenario_id, phase, track_valid) do podziału na epizody i fazy.
Kamera z pinu: PX4-Autopilot/Tools/simulation/gz/models/mono_cam/model.sdf (3354ae1e) — horizontal_fov 1.74 rad,
640×480, pose sensora 0 (oś optyczna = +x linku); montaż x500_mono_cam/model.sdf:9 (.12 .03 .242, rpy 0) — kamera
poziomo do przodu, sztywno z kadłubem. f = 320 / tan(0.87) = 269.5 px.
„Stożek centralny jak w admisji": edge_dist = min(cx, 1−cx, cy, 1−cy) ≥ 0.10 w znormalizowanych współrzędnych
(r02/config_r02.py:36 ENTRY_EDGE_MARGIN). Kotwica = punkt (E 0, N 0, U h). Brak okluzji (świat płaski, rachunek
geometryczny); punkt środka kotwicy, nie jej obrys.

Użycie: kotw_r1.py <out.json> <kampania=glob_katalogów_bootów> ...
"""
import bisect
import glob
import json
import math
import os
import sys

F = 320.0 / math.tan(1.74 / 2)
W, H = 640.0, 480.0
CAM = (0.12, 0.03, 0.242)
EDGE = 0.10
HS = (0.5, 2.0, 5.0)
GAP_MERGE_S = 0.25          # dziura krótsza niż 0.25 s (≈ 4 klatki @15 Hz) nie przerywa okna
MIN_PX = 10.0               # ZAŁOŻENIE (niezmierzone): kotwica użyteczna, gdy jej szerokość w obrazie f·W/D ≥ 10 px
WS = (None, 0.5, 1.0, 2.0)  # None = sama geometria (bez progu rozdzielczości)


def qrot_inv(q, v):
    """Obrót wektora świata do ramy ciała dla kwaternionu body→świat (w, x, y, z)."""
    w, x, y, z = q
    x, y, z = -x, -y, -z
    tx = 2 * (y * v[2] - z * v[1]); ty = 2 * (z * v[0] - x * v[2]); tz = 2 * (x * v[1] - y * v[0])
    return (v[0] + w * tx + (y * tz - z * ty), v[1] + w * ty + (z * tx - x * tz), v[2] + w * tz + (x * ty - y * tx))


def qrot(q, v):
    w, x, y, z = q
    tx = 2 * (y * v[2] - z * v[1]); ty = 2 * (z * v[0] - x * v[2]); tz = 2 * (x * v[1] - y * v[0])
    return (v[0] + w * tx + (y * tz - z * ty), v[1] + w * ty + (z * tx - x * tz), v[2] + w * tz + (x * ty - y * tx))


def widok(g, h):
    q = (g["qw"], g["qx"], g["qy"], g["qz"])
    c = qrot(q, CAM)
    cam = (g["x"] + c[0], g["y"] + c[1], g["z"] + c[2])
    d = (0.0 - cam[0], 0.0 - cam[1], h - cam[2])
    b = qrot_inv(q, d)                      # FLU kamery: x do przodu, y w lewo, z w górę
    rng = math.sqrt(d[0] ** 2 + d[1] ** 2 + d[2] ** 2)
    if b[0] <= 0.1:
        return False, False, rng, None
    u = W / 2 - F * b[1] / b[0]
    v = H / 2 - F * b[2] / b[0]
    cx, cy = u / W, v / H
    inside = 0 <= cx <= 1 and 0 <= cy <= 1
    central = inside and min(cx, 1 - cx, cy, 1 - cy) >= EDGE
    return inside, central, rng, (round(cx, 3), round(cy, 3))


def load(p, typ=None):
    out = []
    for ln in open(p):
        if typ and f'"t": "{typ}"' not in ln:
            continue
        try:
            out.append(json.loads(ln))
        except json.JSONDecodeError:
            pass
    return out


def okna(ts, flags):
    """Okna True z łączeniem dziur < GAP_MERGE_S; zwraca listę (t0, t1, idx)."""
    w, cur = [], None
    for i, (t, f) in enumerate(zip(ts, flags)):
        if f:
            if cur and t - cur[1] <= GAP_MERGE_S:
                cur[1] = t; cur[2].append(i)
            else:
                if cur:
                    w.append(cur)
                cur = [t, t, [i]]
    if cur:
        w.append(cur)
    return w


def boot(d, kampania):
    tr, dm = os.path.join(d, "trace.jsonl"), os.path.join(d, "demo.jsonl")
    if not (os.path.exists(tr) and os.path.exists(dm)):
        return []
    gt = [g for g in load(tr, "gt") if "qw" in g and "sim" in g]
    gt.sort(key=lambda g: g["sim"])
    gs = [g["sim"] for g in gt]
    rows = load(dm)
    eps = {}
    for r in rows:
        eps.setdefault(r["episode_id"], []).append(r)
    out = []
    for ep, rr in eps.items():
        rr.sort(key=lambda r: r["t_sim"])
        t0, t1 = rr[0]["t_sim"], rr[-1]["t_sim"]
        i0, i1 = bisect.bisect_left(gs, t0), bisect.bisect_right(gs, t1)
        seg = gt[i0:i1]
        if len(seg) < 10:
            continue
        rt = [r["t_sim"] for r in rr]
        faza = []
        for g in seg:
            j = min(max(bisect.bisect_left(rt, g["sim"]), 0), len(rr) - 1)
            r = rr[j]
            f = r["phase"]
            if f == "hold":
                f = "hold"
            elif f == "orbit" and not r.get("track_valid"):
                f = "orbit_bez_tracka"
            faza.append(f)
        ts = [g["sim"] - t0 for g in seg]
        rgt = [math.hypot(g["x"], g["y"]) for g in seg]
        alt = [g["z"] for g in seg]
        rec = {"kampania": kampania, "boot": os.path.basename(d.rstrip("/")), "ep": ep, "scenario": rr[0]["scenario_id"],
               "T_s": round(t1 - t0, 2), "n_gt": len(seg),
               "fazy_s": {}, "r_gt_p50": round(sorted(rgt)[len(rgt) // 2], 2), "alt_p50": round(sorted(alt)[len(alt) // 2], 2),
               "h": {}}
        for f in set(faza):
            idx = [i for i, x in enumerate(faza) if x == f]
            rec["fazy_s"][f] = round(len(idx) * (ts[-1] / max(len(ts) - 1, 1)), 1)
        for h in HS:
            vw = [widok(g, h) for g in seg]
            for klucz, k, wm in [("central", 1, None), ("kadr", 0, None)] + [(f"central_W{w}", 1, w) for w in WS if w]:
                dmax = F * wm / MIN_PX if wm else float("inf")
                fl = [v[k] and v[2] <= dmax for v in vw]
                w = okna(ts, fl)
                przerwy = []
                prev = 0.0
                for a, b, idx in w:
                    przerwy.append({"t0": round(prev, 2), "t1": round(a, 2), "dl": round(a - prev, 2), "cenz": prev == 0.0,
                                    "faza": max(set(faza[bisect.bisect_left(ts, prev):bisect.bisect_left(ts, a) + 1] or ["?"]),
                                                key=(faza[bisect.bisect_left(ts, prev):bisect.bisect_left(ts, a) + 1] or ["?"]).count)})
                    prev = b
                przerwy.append({"t0": round(prev, 2), "t1": round(ts[-1], 2), "dl": round(ts[-1] - prev, 2), "cenz": True,
                                "faza": max(set(faza[bisect.bisect_left(ts, prev):] or ["?"]), key=(faza[bisect.bisect_left(ts, prev):] or ["?"]).count)})
                okn = [{"t0": round(a, 2), "dl": round(b - a, 2),
                        "zasieg_min": round(min(vw[i][2] for i in idx), 2), "zasieg_max": round(max(vw[i][2] for i in idx), 2),
                        "faza": max(set(faza[i] for i in idx), key=[faza[i] for i in idx].count)} for a, b, idx in w]
                frac = {f: round(sum(1 for i, x in enumerate(faza) if x == f and fl[i]) / max(1, sum(1 for x in faza if x == f)), 4)
                        for f in set(faza)}
                rec["h"].setdefault(str(h), {})[klucz] = {"okna": okn, "przerwy": przerwy, "frac_widoczny_per_faza": frac,
                                                           "frac_widoczny": round(sum(fl) / len(fl), 4)}
        out.append(rec)
    return out


def main():
    outp = sys.argv[1]
    res = []
    for arg in sys.argv[2:]:
        kamp, pat = arg.split("=", 1)
        for d in sorted(glob.glob(pat)):
            if os.path.isdir(d):
                res += boot(d, kamp)
    json.dump({"opis": __doc__.split("\n\n")[0], "F_px": round(F, 2), "edge": EDGE, "h_m": HS, "gap_merge_s": GAP_MERGE_S, "min_px": MIN_PX, "W_m": [w for w in WS if w],
               "epizody": res}, open(outp, "w"), ensure_ascii=False)
    print(len(res), "epizodów")


if __name__ == "__main__":
    main()
