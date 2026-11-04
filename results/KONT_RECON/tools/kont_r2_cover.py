#!/usr/bin/env python3
"""results/KONT_RECON/tools/kont_r2_cover.py — R2: czy w world_demo_A3 kamera w dół ma cokolwiek do śledzenia.

Grunt jest jednolity (SDF), więc przepływ widzi tylko bryły świata. Geometria offline: kwadrat obrazu
flow_camera (hfov 0.733 rad, optical_flow/model.sdf) z wysokości GT nad szczytem bryły, obrót po yaw GT,
tilt pominięty. Klatka ma cechę ⇔ krawędź którejś bryły leży w kwadracie (przecięcie ∧ bryła nie zakrywa
całego obrazu). Liczone po trajektoriach orbity z trace.jsonl kampanii (r4_margin.json) @10 Hz.
Metryki: ułamek klatek z cechą, luki bez cechy (p50/p95/max) wobec ściany 4 s. Wyjście: r2_cover.json
"""
import json
import math
import os
import statistics as st
import xml.etree.ElementTree as ET
import glob

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
HF = 0.733038
T = math.tan(HF / 2)
root = ET.parse(os.path.join(ROOT, "worlds", "world_demo_A3.sdf")).getroot()
boxes = []
for m in root.iter("model"):
    pose = m.find("pose")
    if pose is None or m.find("static") is None or m.find("static").text.strip() != "true":
        continue
    p = [float(x) for x in pose.text.split()]
    for v in m.iter("visual"):
        sz = v.find("geometry/box/size")
        if sz is None:
            continue
        sx, sy, sz_ = [float(x) for x in sz.text.split()]
        boxes.append({"n": m.get("name"), "x": p[0], "y": p[1], "yaw": p[5], "hx": sx / 2, "hy": sy / 2, "top": p[2] + sz_ / 2})
inside = [b for b in boxes if math.hypot(b["x"], b["y"]) <= 32.0 + 4]
area = sum(4 * b["hx"] * b["hy"] for b in inside)


def has_feature(x, y, h, yaw):
    """SAT dwóch prostokątów: obraz (bok 2·T·(h−top)) i bryła; pełne zakrycie obrazu nie liczy się jako cecha."""
    c, s = math.cos(yaw), math.sin(yaw)
    for b in inside:
        hh = h - b["top"]
        if hh <= 0.2:
            continue
        a = T * hh
        dx, dy = b["x"] - x, b["y"] - y
        if abs(dx) > a * 1.42 + max(b["hx"], b["hy"]) * 1.42 or abs(dy) > a * 1.42 + max(b["hx"], b["hy"]) * 1.42:
            continue
        cb, sb = math.cos(b["yaw"]), math.sin(b["yaw"])
        ok = True
        for ax, ay in ((c, s), (-s, c), (cb, sb), (-sb, cb)):
            ra = a * (abs(ax * c + ay * s) + abs(-ax * s + ay * c))
            rb = b["hx"] * abs(ax * cb + ay * sb) + b["hy"] * abs(-ax * sb + ay * cb)
            if abs(dx * ax + dy * ay) > ra + rb:
                ok = False
                break
        if ok:
            return True
    return False


def quat_yaw(r):
    return math.atan2(2 * (r["qw"] * r["qz"] + r["qx"] * r["qy"]), 1 - 2 * (r["qy"] ** 2 + r["qz"] ** 2))


fr, gaps, per = 0, [], []
tot = 0
for p in sorted(glob.glob(os.path.join(ROOT, "results", "FANTOM", "camp", "r*_V2*", "trace.jsonl"))) + \
        sorted(glob.glob(os.path.join(ROOT, "results", "PERC2", "s2", "b*", "trace.jsonl"))) + \
        sorted(glob.glob(os.path.join(ROOT, "results", "SKAN2", "s1", "b*", "trace.jsonl"))):
    ev, gt = [], []
    for l in open(p):
        try:
            r = json.loads(l)
        except Exception:
            continue
        if r.get("t") == "event":
            ev.append(r)
        elif r.get("t") == "gt" and "qw" in r:
            gt.append(r)
    st0 = None
    for e in ev:
        if e["ev"] == "episode_start":
            st0 = e
        elif e["ev"] == "episode_end" and st0 is not None:
            if e.get("t_entry") is not None:
                a, b = st0["t0_sim"] + e["t_entry"], e["sim"]
                seg = [r for r in gt if a <= r["sim"] <= b][::5]
                gap, nf, n = 0.0, 0, 0
                prev = None
                for r in seg:
                    n += 1
                    dt = 0.0 if prev is None else r["sim"] - prev
                    prev = r["sim"]
                    # ENU→NED: bryły w świecie gz (ENU), GT też — liczymy w ENU; yaw GT ENU wprost
                    if has_feature(r["x"], r["y"], r["z"], quat_yaw(r)):
                        nf += 1
                        if gap > 0:
                            gaps.append(gap)
                        gap = 0.0
                    else:
                        gap += dt
                if gap > 0:
                    gaps.append(gap)
                if n:
                    per.append(nf / n)
                fr += nf; tot += n
            st0 = None
q = sorted(gaps) or [0.0]
res = {"n_bryl_w_R36": len(inside), "pole_bryl_m2": round(area, 1), "ulamek_pola_kola_R36": round(area / (math.pi * 36 ** 2), 4),
       "footprint_bok_m_przy_10m": round(2 * T * 10, 2), "n_epizodow": len(per), "n_klatek": tot,
       "ulamek_klatek_z_cecha": round(fr / tot, 3), "ulamek_per_epizod_p10": round(sorted(per)[int(0.1 * (len(per) - 1))], 3),
       "ulamek_per_epizod_p50": round(st.median(per), 3),
       "luki_n": len(gaps), "luka_p50_s": round(q[len(q) // 2], 2), "luka_p95_s": round(q[int(0.95 * (len(q) - 1))], 2), "luka_max_s": round(q[-1], 2),
       "luk_ge_4s": sum(1 for g in q if g >= 4.0), "luk_ge_1s": sum(1 for g in q if g >= 1.0)}
json.dump(res, open(os.path.join(ROOT, "results", "KONT_RECON", "r2_cover.json"), "w"), ensure_ascii=False, indent=0)
print(res)
