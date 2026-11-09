#!/usr/bin/env python3
"""results/NADIR/tools/nadir_s1v2_r4trk.py — R4 po położeniu tracku (PROMPT_NADIR_S1 §R4), uzupełnienie nadir_s1v2_analyze.r4.

Powód: test „środek boxa top-1 w rzucie płyty znacznika” (r4) daje fałszywe trafienia — (i) duży box bliskiego intruza
(track na intruzie, 0.4 m) zahacza o rzut znacznika; (ii) wiersze feedu z etykietą REFRESH niosą śmieciowy box top-1
(conf ~0.001). Miara rozstrzygająca to stan TRACKU: trk_pos_ned z percep_feed vs pozycja intruza (gt_intruder, |Δt| ≤ 0.1 s)
i vs znaczniki manifestu v2 (NED, z = −0.03).
  przejęcie tracku ⇔ trk ≤ 3 m od znacznika ∧ > 5 m od intruza (próbki z intruzem w epizodzie);
  fałszywa admisja na znaczniku ⇔ zdarzenie ENTRY z trk ≤ 3 m od znacznika (w epizodzie lub poza nim).
Dla każdego ENTRY: czas, czy w epizodzie, odległość trk od intruza i od najbliższego znacznika, wysokość trk.
Kontrola: ten sam rachunek na boocie KONT bez znaczników (znaczniki „na niby”).
Użycie: nadir_s1v2_r4trk.py <out.json> <boot_dir> ... [--kontrola <dir>]
"""
import bisect
import json
import math
import os
import sys

ROOT = "/home/olga/projects/liquidpatrol"
MAN = json.load(open(os.path.join(ROOT, "results/NADIR/s1/n1/manifest_znaczniki_v2.json")))["znaczniki"]
M = [(z["N"], z["E"], -z["z"]) for z in MAN]


def load(p, typ=None):
    out = []
    for l in open(p):
        if typ and f'"t": "{typ}"' not in l:
            continue
        try:
            out.append(json.loads(l))
        except ValueError:
            pass
    return out


def boot(d):
    f = [r for r in load(os.path.join(d, "percep_feed.jsonl")) if "t_frame" in r]
    intr = sorted(load(os.path.join(d, "gt_intruder.jsonl")), key=lambda r: r["t_sim"])
    it = [r["t_sim"] for r in intr]
    ev = load(os.path.join(d, "trace.jsonl"), "event")
    st = [e["sim"] for e in ev if e["ev"] == "episode_start"]
    en = [e["sim"] for e in ev if e["ev"] == "episode_end"]
    epi = list(zip(st, en))
    w_ep = lambda t: any(a <= t <= b for a, b in epi)
    out = {"probki_trk_z_intruzem": 0, "przejecie_trk": 0, "entry": [], "trk_intr_p95": None}
    di_all = []
    for r in f:
        trk = r.get("trk_pos_ned")
        if trk is None:
            continue
        dm = min(math.dist(trk, m) for m in M)
        j = min(bisect.bisect_left(it, r["t_frame"]), len(intr) - 1) if intr else None
        di = math.dist(trk, intr[j]["ned"]) if intr and abs(intr[j]["t_sim"] - r["t_frame"]) <= 0.1 else None
        if di is not None:
            out["probki_trk_z_intruzem"] += 1
            di_all.append(di)
            if dm <= 3 and di > 5:
                out["przejecie_trk"] += 1
        if r["ev"] == "ENTRY":
            out["entry"].append({"t": round(r["t_frame"], 3), "w_epizodzie": w_ep(r["t_frame"]), "d_intruz": None if di is None else round(di, 2),
                                 "d_znacznik": round(dm, 2), "trk_wys_m": round(-trk[2], 2), "conf": round(r["conf"], 3),
                                 "na_znaczniku": dm <= 3})
    di_all.sort()
    out["trk_intr_p95"] = round(di_all[int(0.95 * len(di_all))], 3) if di_all else None
    out["falszywa_admisja_na_znaczniku"] = sum(e["na_znaczniku"] for e in out["entry"])
    return out


def main():
    a = sys.argv[1:]
    outp = a.pop(0)
    kon = None
    if "--kontrola" in a:
        i = a.index("--kontrola"); kon = a[i + 1]; a = a[:i] + a[i + 2:]
    res = {os.path.basename(d.rstrip("/")): boot(d) for d in a}
    if kon:
        res["KONTROLA_" + os.path.basename(kon.rstrip("/"))] = boot(kon)
    json.dump(res, open(outp, "w"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
