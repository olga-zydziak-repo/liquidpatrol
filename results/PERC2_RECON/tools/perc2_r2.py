#!/usr/bin/env python3
"""results/PERC2_RECON/tools/perc2_r2.py — R2 PROMPT_PERC2_S0: krzywe P(detekcja|Z)
i P(admisja|Z, mod) na ISTNIEJĄCYCH klatkach (metadane percep_feed; zero lotów).

Dane: percep_feed.jsonl wszystkich bootów V2 trzech kampanii (DET S4 / AKW S3 /
FANTOM S2); epizody z trace.jsonl (episode_start — wzór erratum_sweep.py:48-58);
GT celu DO ODLEGŁOŚCI z manifestu analitycznie (reguła erratum: wolny od tranzientu;
świadek |ned−cmd|_xy>1 m zliczony OBOK na surowym gt_intruder); etykieta on-target
FROZEN det_labels.BootGeo (8f7430cd — kryterium identyczne z det_replay).

Per klatka (cel W KADRZE wg etykiety, flag OK): dh [m] poziome own↔cel (manifest),
Z_opt [m] (etykieta), box YOLO (obecność / środek w boxie etykiety = on-target /
conf / centralność edge≥0.10 / w,h px), mti_ok, fresh. Kosze dh 0–30 co 2 m × mod
kadencji bootu (z r1_kadencja.json) + kosze drobne 1 m na zboczu bliskim 2–8 m
+ kosze Z co 2 m dla px-vs-Z. Wyjście: r2_krzywe.json + tabele stdout.
"""
import json
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
for p in (ROOT, os.path.join(ROOT, "results", "POSCIG_RECON", "tools"),
          os.path.join(ROOT, "results", "DET_RECON", "tools")):
    if p not in sys.path:
        sys.path.insert(0, p)

from bench import scenarios as S
from poscig_recon import iter_jsonl, _SCEN
from det_labels import BootGeo                    # FROZEN 8f7430cd

OUTD = os.path.join(ROOT, "results", "PERC2_RECON")
CAMPS = [("DET_S4", "results/DET/camp"), ("AKW_S3", "results/AKW/camp"),
         ("FANTOM_S2", "results/FANTOM/camp")]
R1 = json.load(open(os.path.join(OUTD, "r1_kadencja.json")))
MODE_BY_DIR = {r["dir"]: r["mode"] for r in R1["kadencja"]}


def pct(xs, q):
    if not xs:
        return None
    xs = sorted(xs)
    return xs[min(len(xs) - 1, max(0, int(round(q * (len(xs) - 1)))))]


def episodes_of(d):
    eps = []
    for r in iter_jsonl(os.path.join(d, "trace.jsonl")):
        if r.get("t") == "event" and r.get("ev") == "episode_start" and r.get("scenario_id"):
            eps.append({"sid": r["scenario_id"], "t0": r["t0_sim"]})
    for i, e in enumerate(eps):
        e["t1"] = eps[i + 1]["t0"] - 1.0 if i + 1 < len(eps) else e["t0"] + 112.0
    return eps


def witness_count(d, eps):
    n = tot = 0
    for r in iter_jsonl(os.path.join(d, "gt_intruder.jsonl")):
        if not (r.get("ned") and r.get("cmd_ned")):
            continue
        t = r["t_sim"]
        if any(e["t0"] <= t <= e["t1"] for e in eps):
            tot += 1
            if math.dist(r["ned"][:2], r["cmd_ned"][:2]) > 1.0:
                n += 1
    return n, tot


def frames_of_boot(camp, d):
    eps = [e for e in episodes_of(d) if e["sid"] in _SCEN]
    if not eps:
        return [], (0, 0)
    geo = BootGeo(d, 1.0, 200.0)       # z_max 200: pełna krzywa (F4 wyłączone świadomie)
    mode = MODE_BY_DIR.get(os.path.relpath(d, ROOT), "?")
    out = []
    pf = [r for r in iter_jsonl(os.path.join(d, "percep_feed.jsonl"))
          if r.get("t_frame") is not None and r.get("own_pos_ned")]
    pf.sort(key=lambda r: r.get("t_frame", 0))
    ei = 0
    for r in pf:
        t = r["t_frame"]
        e = None
        for k in range(ei, len(eps)):
            if eps[k]["t0"] <= t <= eps[k]["t1"]:
                e = eps[k]; ei = k
                break
            if eps[k]["t0"] > t:
                break
        if e is None or (t - e["t0"]) > 110.0:
            continue
        lab = geo.label(t)
        if lab.get("flag") != "OK":
            continue                     # cel poza kadrem/za plecami/brak GT — poza krzywą
        g = S.position_at(_SCEN[e["sid"]], t - e["t0"])
        gt = [g[0], g[1], -g[2]]
        op = r["own_pos_ned"]
        dh = math.hypot(gt[0] - op[0], gt[1] - op[1])
        Z = lab["uvZ"][2]
        b = r.get("box")
        on_tgt = False
        central = False
        if b:
            bx, by = b[0] * 640, b[1] * 480
            lb = lab["box"]
            on_tgt = abs(bx - lb[0]) <= lb[2] / 2 and abs(by - lb[1]) <= lb[3] / 2
            central = min(b[0], 1.0 - b[0], b[1], 1.0 - b[1]) >= 0.10
        out.append({"camp": camp, "mode": mode, "dh": dh, "Z": Z,
                    "box": b is not None, "on_tgt": on_tgt,
                    "conf": r.get("conf") if on_tgt else None,
                    "central": central, "mti": bool(r.get("mti_ok")),
                    "fresh": bool(r.get("fresh")),
                    "conj": central and bool(r.get("mti_ok")),
                    "wpx": (b[2] * 640 if (b and on_tgt) else None),
                    "hpx": (b[3] * 480 if (b and on_tgt) else None),
                    "lab_wpx": lab["box"][2]})
    wit = witness_count(d, eps)
    return out, wit


def agg(frames, keyf, bins):
    table = {}
    for f in frames:
        k = keyf(f)
        if k is None:
            continue
        a = table.setdefault(k, {"n": 0, "box": 0, "on": 0, "cen": 0, "mti": 0,
                                 "fresh": 0, "conj": 0, "conf": [], "hpx": [],
                                 "lab_wpx": [], "Z": []})
        a["n"] += 1
        a["box"] += f["box"]
        a["on"] += f["on_tgt"]
        a["cen"] += (f["central"] and f["on_tgt"])
        a["mti"] += f["mti"]
        a["fresh"] += f["fresh"]
        a["conj"] += (f["conj"] and f["on_tgt"])
        if f["conf"] is not None:
            a["conf"].append(f["conf"])
        if f["hpx"] is not None:
            a["hpx"].append(f["hpx"])
        a["lab_wpx"].append(f["lab_wpx"])
        a["Z"].append(f["Z"])
    out = []
    for k in bins:
        a = table.get(k)
        if not a or a["n"] < 10:
            out.append({"bin": k, "n": (a["n"] if a else 0)})
            continue
        n = a["n"]
        out.append({"bin": k, "n": n,
                    "P_box": round(a["box"] / n, 3), "P_on_tgt": round(a["on"] / n, 3),
                    "P_central_on": round(a["cen"] / n, 3),
                    "P_mti": round(a["mti"] / n, 3), "P_fresh": round(a["fresh"] / n, 3),
                    "P_conj_on": round(a["conj"] / n, 3),
                    "conf_p50": round(pct(a["conf"], 0.5), 3) if a["conf"] else None,
                    "hpx_p50": round(pct(a["hpx"], 0.5), 1) if a["hpx"] else None,
                    "lab_wpx_p50": round(pct(a["lab_wpx"], 0.5), 1),
                    "Z_p50": round(pct(a["Z"], 0.5), 1)})
    return out


def main():
    all_fr = []
    wit_per_camp = {}
    for camp, base in CAMPS:
        for i in range(1, 13):
            d = os.path.join(ROOT, base, f"r{i}_V2")
            if not os.path.isdir(d):
                continue
            fr, wit = frames_of_boot(camp, d)
            all_fr.extend(fr)
            w = wit_per_camp.setdefault(camp, [0, 0])
            w[0] += wit[0]; w[1] += wit[1]
            print(f"[{camp} r{i}] klatek_in_FOV={len(fr)} świadek={wit[0]}/{wit[1]}")
    print(f"RAZEM klatek in-FOV: {len(all_fr)}; świadek per camp: {wit_per_camp}")

    def dh_bin(f):
        if f["dh"] >= 30:
            return None
        return int(f["dh"] // 2) * 2

    bins2 = list(range(0, 30, 2))
    out = {"n_frames_in_fov": len(all_fr), "swiadek_per_camp": wit_per_camp,
           "zrodla": "etykieta FROZEN det_labels 8f7430cd (z_max=200 jawnie); dh z manifestu "
                     "(erratum); epizody trace episode_start (wzór erratum_sweep); "
                     "mod bootu z r1_kadencja.json",
           "krzywa_dh_all": agg(all_fr, dh_bin, bins2)}
    for m in ("SZYBKI", "SREDNI", "WOLNY"):
        out[f"krzywa_dh_{m}"] = agg([f for f in all_fr if f["mode"] == m], dh_bin, bins2)
    out["zbocze_bliskie_1m"] = agg(all_fr, lambda f: int(f["dh"]) if 2 <= f["dh"] < 8 else None,
                                   list(range(2, 8)))
    out["px_vs_Z"] = agg(all_fr, lambda f: int(f["Z"] // 2) * 2 if f["Z"] < 40 else None,
                         list(range(0, 40, 2)))

    print("=== krzywa dh (all) ===")
    for r in out["krzywa_dh_all"]:
        print(r)
    print("=== px vs Z ===")
    for r in out["px_vs_Z"]:
        print(r)
    json.dump(out, open(os.path.join(OUTD, "r2_krzywe.json"), "w"), indent=1)
    print("zapisano r2_krzywe.json")


if __name__ == "__main__":
    main()
