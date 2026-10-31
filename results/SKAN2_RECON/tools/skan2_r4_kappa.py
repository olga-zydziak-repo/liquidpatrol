#!/usr/bin/env python3
"""results/SKAN2_RECON/tools/skan2_r4_kappa.py — R4: per-klatkowa koincydencja na celu vs obrót [°/klatkę]
(odpowiednik κ₉₀ z ANEKS_AKW-1:57 — „największe °/kl z admisją ≥ 90% przy celu w FOV" — w reżimie 14.7 Hz).

Klatki fazy skanu (t0 → pierwsza fresh na celu), cel w stożku centralnym (skan2_r1: rzut GT z manifestu,
edge ≥ 0.10). Miara per klatka: koincydencja = box na celu ∧ box centralny ∧ mti_ok (target_channel.py:124-128).
Biny |Δyaw| [°/klatkę]: 0–1, 1–2, 2–3, 3–4, 4–5, 5–7, 7–12, >12. Wyjście r4_kappa.json + wydruk.
"""
import json, math, os, sys
sys.path.insert(0, "/home/olga/projects/liquidpatrol/results/SKAN2_RECON/tools")
import skan2_r1 as K

BINS = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 7), (7, 12), (12, 999)]


def frames(d):
    eps = [(r["scenario_id"], r["t0_sim"]) for r in K.iter_jsonl(os.path.join(d, "trace.jsonl"))
           if r.get("t") == "event" and r.get("ev") == "episode_start" and r.get("scenario_id")]
    demo = list(K.iter_jsonl(os.path.join(d, "demo.jsonl")))
    pf = sorted((r for r in K.iter_jsonl(os.path.join(d, "percep_feed.jsonl"))
                 if r.get("t_frame") is not None and r.get("own_q")), key=lambda r: r["t_frame"])
    geo = K.BootGeo(d, 1.0, 60.0)
    out = []
    for sid, t0 in eps:
        drows = [r for r in demo if r.get("scenario_id") == sid]
        if not drows:
            continue
        tend = drows[-1]["t_sim"]
        its, ips, t = [], [], 0.0
        while t <= tend - t0 + 1.0:
            x, y, z = K.S.position_at(K.MAN[sid], t)
            its.append(t0 + t); ips.append([x, y, -z]); t += 0.05
        geo.its, geo.ips = its, ips
        prev = None
        for r in (x for x in pf if t0 <= x["t_frame"] <= tend):
            i = max(0, min(len(ips) - 1, int(round((r["t_frame"] - t0) / 0.05))))
            g = ips[i]
            if r.get("fresh") and r.get("trk_pos_ned") and \
                    math.hypot(r["trk_pos_ned"][0] - g[0], r["trk_pos_ned"][1] - g[1]) <= K.FRESH_GATE_M:
                break
            dpf = abs(K.wrap(K.yaw_of(r["own_q"]) - K.yaw_of(prev["own_q"]))) if prev else None
            prev = r
            lab = geo.label(r["t_frame"])
            if dpf is None or lab.get("flag") != "OK":
                continue
            u, v, Z = lab["uvZ"]
            if K.edge_dist(u / 640, v / 480) < K.EDGE or Z < 5.0:
                continue
            b = r.get("box")
            on = bool(b) and abs(b[0] * 640 - lab["box"][0]) <= lab["box"][2] / 2 and abs(b[1] * 480 - lab["box"][1]) <= lab["box"][3] / 2
            conj = on and K.edge_dist(b[0], b[1]) >= K.EDGE and bool(r.get("mti_ok"))
            out.append((dpf, on, conj))
    return out


res = {}
for a in sys.argv[2:]:
    d, lab = a.split(",")
    res.setdefault(lab, []).extend(frames(os.path.join(K.ROOT, d)))
summ = {}
for lab, fr in res.items():
    summ[lab] = {}
    for lo, hi in BINS:
        s = [x for x in fr if lo <= x[0] < hi]
        if s:
            summ[lab][f"{lo}-{hi}"] = {"n": len(s), "box_na_celu": round(sum(x[1] for x in s) / len(s), 3),
                                       "koincydencja": round(sum(x[2] for x in s) / len(s), 3)}
json.dump(summ, open(sys.argv[1], "w"), indent=1)
print(json.dumps(summ, indent=1))
