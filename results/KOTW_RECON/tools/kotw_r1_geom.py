#!/usr/bin/env python3
"""results/KOTW_RECON/tools/kotw_r1_geom.py — R1: przyczyna niewidoczności kotwicy (h = 2 m) per faza, z tych samych źródeł
co kotw_r1.py. Klasy per próbka GT poza stożkiem centralnym: ZA (kotwica za płaszczyzną obrazu lub |azymut| > połowy FOV
poziomego minus margines), POD (azymut w kadrze, ale depresja większa niż dolna krawędź stożka centralnego), INNE (krawędzie).
Dodatkowo: kąt między kursem kamery a kierunkiem do środka (|Δψ|) i depresja do kotwicy, mediany per faza.
Użycie: kotw_r1_geom.py <out.json> <kampania=glob> ...
"""
import bisect, glob, json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kotw_r1 as K

H = 2.0
res = {}
for arg in sys.argv[2:]:
    kamp, pat = arg.split("=", 1)
    for d in sorted(glob.glob(pat)):
        tr, dm = os.path.join(d, "trace.jsonl"), os.path.join(d, "demo.jsonl")
        if not (os.path.exists(tr) and os.path.exists(dm)):
            continue
        gt = sorted([g for g in K.load(tr, "gt") if "qw" in g and "sim" in g], key=lambda g: g["sim"])
        gs = [g["sim"] for g in gt]
        rows = sorted(K.load(dm), key=lambda r: r["t_sim"]); rt = [r["t_sim"] for r in rows]
        if not rows:
            continue
        for g in gt[bisect.bisect_left(gs, rt[0]):bisect.bisect_right(gs, rt[-1])]:
            r = rows[min(bisect.bisect_left(rt, g["sim"]), len(rows) - 1)]
            f = r["phase"]
            q = (g["qw"], g["qx"], g["qy"], g["qz"])
            inside, central, rng, _ = K.widok(g, H)
            b = K.qrot_inv(q, (-g["x"], -g["y"], H - g["z"]))
            az = math.degrees(math.atan2(b[1], b[0]))
            dep = math.degrees(math.atan2(-b[2], math.hypot(b[0], b[1])))
            half_h = math.degrees(math.atan((0.5 - K.EDGE) * K.W / K.F))
            half_v = math.degrees(math.atan((0.5 - K.EDGE) * K.H / K.F))
            if central:
                k = "WIDOCZNA"
            elif abs(az) > half_h:
                k = "ZA"
            elif dep > half_v:
                k = "POD"
            else:
                k = "INNE"
            s = res.setdefault(f, {"n": 0, "klasy": {}, "az": [], "dep": [], "r": []})
            s["n"] += 1; s["klasy"][k] = s["klasy"].get(k, 0) + 1
            s["az"].append(abs(az)); s["dep"].append(dep); s["r"].append(math.hypot(g["x"], g["y"]))
out = {"h_m": H, "pol_fov_central_poziom_deg": round(math.degrees(math.atan((0.5 - K.EDGE) * K.W / K.F)), 1),
       "pol_fov_central_pion_deg": round(math.degrees(math.atan((0.5 - K.EDGE) * K.H / K.F)), 1), "fazy": {}}
for f, s in res.items():
    md = lambda v: round(sorted(v)[len(v) // 2], 1)
    out["fazy"][f] = {"n": s["n"], "frac": {k: round(v / s["n"], 3) for k, v in s["klasy"].items()},
                      "abs_azymut_do_srodka_p50_deg": md(s["az"]), "depresja_p50_deg": md(s["dep"]), "r_gt_p50_m": md(s["r"])}
json.dump(out, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
