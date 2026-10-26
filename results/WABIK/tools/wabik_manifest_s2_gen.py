#!/usr/bin/env python3
"""results/WABIK/tools/wabik_manifest_s2_gen.py — manifest S2 nogi WABIK
(ANEKS_WABIK-1 §4.3-4.6). NOWY plik results/WABIK/wabik_manifest_s2.json
(wabik_manifest.json v1 z FREEZE NIETKNIĘTY — sha 046fa12b; istniejący
scenario_manifest.json NIETYKALNY — kopie 1:1 dowodzone diffem).

JEDEN OBIEKT NARAZ (litera PRE §3 / ANEKS §4.2): epizody T-W-TP = trajektorie
wabika GRANE TOREM INTRUZA (intruder_motion z BENCH_MANIFEST; wabik_motion
w S2 nieobecny — ANEKS §4.6). Warianty parametrów w przedziałach z PRE §2.1:
  [0] w_loiter_a  — W-LOITER r=10 m (1:1 trajektoria z FREEZE)      [1] w_loiter_b  — r=12 m
  [2] w_styczny_a — W-STYCZNY b=8 m (1:1)                           [3] w_styczny_b — b=12 m
  [4] w_zbliz_a   — W-ZBLIŻ-ODSKOK do 7 m (1:1)                     [5] w_zbliz_b   — do 8.5 m
  [6] c08_s03 — KOPIA 1:1 z scenario_manifest (diff pól w raporcie) [7] c10_s02 — KOPIA 1:1
  [8] m00_s01 M-ŁUK (1:1 z manifestu WABIK v1)
  [9] m01_s01 M-POD-ORBITĄ (1:1)  [10] m01_s02 — drugi przebieg (segmenty identyczne, odrębny sid)
Po końcu trajektorii krótszej niż 110 s: segment hold v=0 (cel zamiera).
"""
import json
import math
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(HERE, "wabik_manifest_s2.json")
V1 = json.load(open(os.path.join(HERE, "wabik_manifest.json")))
ORIG = json.load(open(os.path.join(ROOT, "results", "BENCH", "scenario_manifest.json")))
Z = 10.0


def seg(t0, x0, y0, hd, dur, v):
    return {"t0": round(t0, 4), "t1": round(t0 + dur, 4), "x0": round(x0, 4),
            "y0": round(y0, 4), "heading_deg": round(hd, 4), "v": v}


def end_of(s):
    dt = s["t1"] - s["t0"]
    return (s["x0"] + s["v"] * math.cos(math.radians(s["heading_deg"])) * dt,
            s["y0"] + s["v"] * math.sin(math.radians(s["heading_deg"])) * dt)


def pad_hold(segs, dur=110.0):
    segs = [dict(s) for s in segs if s["t0"] < dur]
    if segs and segs[-1]["t1"] > dur:
        segs[-1]["t1"] = dur
    t_end = segs[-1]["t1"]
    if t_end < dur:
        ex, ey = end_of(segs[-1])
        segs.append(seg(t_end, ex, ey, 0.0, dur - t_end, 0.0))
    return segs


def polyline(pts, v=1.0):
    segs, t = [], 0.0
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        d = math.hypot(x1 - x0, y1 - y0)
        if d < 1e-6:
            continue
        segs.append(seg(t, x0, y0, math.degrees(math.atan2(y1 - y0, x1 - x0)), d / v, v))
        t += d / v
    return segs


def arc_pts(r, a0, a1, step=10.0):
    n = max(2, int(abs(a1 - a0) / step) + 1)
    return [(r * math.cos(math.radians(a0 + (a1 - a0) * k / (n - 1))),
             r * math.sin(math.radians(a0 + (a1 - a0) * k / (n - 1))))
            for k in range(n)]


def ep(eid, sid, segs, opis, bearing=180):
    segs = pad_hold(segs)
    return {"scenario_id": sid, "cell": {"v_intr": 1.0, "bearing_deg": bearing},
            "cell_index": eid, "seed": 1, "block": 1, "is_test": False,
            "orbit_dir": "CW", "start_pos": [segs[0]["x0"], segs[0]["y0"], Z],
            "z": Z, "ep_dur_s": 110.0, "segments": segs, "episode_id": eid,
            "opis": opis}


def loiter_segs(r):
    pts = []
    for cyc in range(8):
        a, b = (140.0, 220.0) if cyc % 2 == 0 else (220.0, 140.0)
        p = arc_pts(r, a, b)
        pts.extend(p if not pts else p[1:])
    return polyline(pts)


def styczny_segs(b):
    half = math.sqrt(18.0 ** 2 - b ** 2)
    return polyline([(-half, -b), (half, -b)])


def zbliz_segs(r_in):
    az = 200.0
    ux, uy = math.cos(math.radians(az)), math.sin(math.radians(az))
    pts = []
    for _ in range(3):
        pts.extend([(15 * ux, 15 * uy), (r_in * ux, r_in * uy)])
    pts.append((15 * ux, 15 * uy))
    return polyline(pts)


def copy_episode(sid, eid):
    src = next(e for e in ORIG["episodes"] if e["scenario_id"] == sid)
    e = json.loads(json.dumps(src))          # kopia 1:1
    e["episode_id"] = eid                     # JEDYNA zmiana (dowód diffem w raporcie)
    return e, src


def main():
    v1w = V1["wabik_trajektorie"]
    eps = []
    eps.append(ep(0, "w00a_s01", v1w["W-LOITER"]["segments"], "W-LOITER r=10 (1:1 FREEZE)"))
    eps.append(ep(1, "w00b_s01", loiter_segs(12.0), "W-LOITER wariant b: r=12 (przedzial 8-12 PRE)"))
    eps.append(ep(2, "w01a_s01", v1w["W-STYCZNY"]["segments"], "W-STYCZNY b=8 (1:1 FREEZE)"))
    eps.append(ep(3, "w01b_s01", styczny_segs(12.0), "W-STYCZNY wariant b: b=12 (b>=5 PRE)"))
    eps.append(ep(4, "w02a_s01", v1w["W-ZBLIZ-ODSKOK"]["segments"], "W-ZBLIZ do 7 m (1:1 FREEZE)"))
    eps.append(ep(5, "w02b_s01", zbliz_segs(8.5), "W-ZBLIZ wariant b: do 8.5 m (~7 PRE)"))
    c08, src08 = copy_episode("c08_s03", 6)
    c10, src10 = copy_episode("c10_s02", 7)
    eps.extend([c08, c10])
    m00 = json.loads(json.dumps(V1["episodes"][0])); m00["episode_id"] = 8
    m01a = json.loads(json.dumps(V1["episodes"][1])); m01a["episode_id"] = 9
    m01b = json.loads(json.dumps(V1["episodes"][1])); m01b["episode_id"] = 10
    m01b["scenario_id"] = "m01_s02"
    m01b["opis"] = m01b.get("opis", "") + " [drugi przebieg, segmenty identyczne]"
    eps.extend([m00, m01a, m01b])
    # dowód równoważności kopii: diff pól vs oryginał
    for cp, src, sid in ((c08, src08, "c08_s03"), (c10, src10, "c10_s02")):
        diff = [k for k in set(cp) | set(src) if cp.get(k) != src.get(k)]
        print(f"diff {sid} vs oryginał: {diff} (c: episode_id {src['episode_id']}→{cp['episode_id']})")
        assert diff == ["episode_id"], f"kopia {sid} NIE 1:1: {diff}"
    man = {"nota": "manifest S2 nogi WABIK (ANEKS_WABIK-1 par.4) — BENCH_MANIFEST; "
                   "JEDEN obiekt naraz: TP = trajektorie wabika grane torem intruza; "
                   "kopie c08_s03/c10_s02 1:1 (diff=episode_id); v<=1.0",
           "z_intr_m": Z, "ep_dur_s": 110.0, "episodes": eps}
    json.dump(man, open(OUT, "w"), indent=1)
    import math as _m
    for e in eps:
        rmin, rmax, t = 1e9, 0, 0.0
        while t <= 110:
            x, y = None, None
            for s in e["segments"]:
                if s["t0"] <= t < s["t1"]:
                    dt = t - s["t0"]
                    x = s["x0"] + s["v"] * _m.cos(_m.radians(s["heading_deg"])) * dt
                    y = s["y0"] + s["v"] * _m.sin(_m.radians(s["heading_deg"])) * dt
                    break
            if x is not None:
                r = _m.hypot(x, y)
                rmin, rmax = min(rmin, r), max(rmax, r)
            t += 0.5
        print(f"[{e['episode_id']:2d}] {e['scenario_id']:10s} r_min={rmin:5.2f} r_max={rmax:5.2f} n_seg={len(e['segments'])}")
    print(f"zapisano {OUT}")


if __name__ == "__main__":
    main()
