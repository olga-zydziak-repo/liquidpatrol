#!/usr/bin/env python3
"""results/SKAN2_RECON/tools/skan2_r1_agg.py — R1: rozkłady latencji admisji per populacja.

Wejścia: r1_zdarzenia_{stare,any}.json (skan2_r1.py; populacje a = PERC2 S2 @14.7 Hz,
a2 = net_fantom po PERC2 w reżimie OPS @14.7 Hz: WK/WK2/WK3 — ROZSZERZENIE NAZWANE, c = FANTOM S2
V2 @5 Hz) + populacja b = korpus DET S1 @15 Hz z results/DET3_RECON/r1 (frames.jsonl + replay.jsonl):
zdarzenie = pierwsza klatka bootu z celem w stożku centralnym (meta uvZ, edge ≥ 0.10), te same kamienie
milowe (box na celu, mti, koincydencja, run≥3, fresh na celu = fresh ∧ err ≤ 3 m).
Klasy: Z0 ≥ 5 m (pas admisji) / Z0 < 5 m (strefa martwa — inna klasa, poza L).
L = p90 latencji „start zdarzenia → fresh na celu" z UCIĘTYMI jako +∞ (konserwatywnie); obok p90
wśród przyjętych i liczba uciętych.
Warstwy (a2): bez wiatru = wk0_b1/b2, g0_b1/b2 (światy z <linear_velocity>0 0 0>), wiatr = reszta.
"""
import glob
import json
import os

ROOT = "/home/olga/projects/liquidpatrol"
OUT = os.path.join(ROOT, "results/SKAN2_RECON")
MS = ("box_on", "mti", "conj", "run3", "fresh_on")
INF = float("inf")


def pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return None
    v = xs[min(len(xs) - 1, int(-(-q * len(xs) // 1)) - 1)]   # nearest-rank
    return None if v == INF else round(v, 3)


def stats(evs):
    o = {"n": len(evs), "n_uciete": sum(1 for e in evs if e["uciete"])}
    for m in MS:
        xs = [(e[m] if (e[m] is not None and not (m == "fresh_on" and e["uciete"])) else INF) for e in evs]
        o[m] = {"p50": pct(xs, 0.5), "p90": pct(xs, 0.9), "p95": pct(xs, 0.95),
                "n_osiagniete": sum(1 for x in xs if x != INF)}
    adm = [e["fresh_on"] for e in evs if not e["uciete"] and e["fresh_on"] is not None]
    o["fresh_on_przyjete"] = {"n": len(adm), "p50": pct(adm, 0.5), "p90": pct(adm, 0.9), "max": max(adm) if adm else None}
    st = [e.get("frac_stare_do_fresh") for e in evs if e.get("frac_stare_do_fresh") is not None]
    o["frac_stare_do_fresh_p50"] = pct(st, 0.5)
    return o


def det_events():
    evs = []
    for fp in sorted(glob.glob(os.path.join(ROOT, "results/DET3_RECON/r1/D*.frames.jsonl"))):
        boot = os.path.basename(fp).split(".")[0]
        fr = [json.loads(l) for l in open(fp)]
        meta = {round(json.loads(l)["t"], 3): json.loads(l)
                for l in open(os.path.join(ROOT, f"results/DET/labels/{boot}/meta.jsonl"))}
        rep = {round(r["t_frame"], 3): r for r in
               (json.loads(l) for l in open(os.path.join(ROOT, f"results/DET3_RECON/r1/{boot}.replay.json.replay.jsonl")))}
        rows = []
        for r in sorted(fr, key=lambda x: x["t"]):
            m = meta[round(r["t"], 3)]
            u, v, _ = m["uvZ"]
            rr = rep.get(round(r["t"], 3), {})
            b = rr.get("box")
            cen = bool(b) and min(b[0], 1 - b[0], b[1], 1 - b[1]) >= 0.10
            rows.append({"t": r["t"], "Z": r["Z"], "inc": min(u / 640, 1 - u / 640, v / 480, 1 - v / 480) >= 0.10,
                         "on": bool(r.get("yolo_on")), "mti": bool(r.get("yolo_on")) and bool(rr.get("mti_ok")),
                         "conj": bool(r.get("yolo_on")) and cen and bool(rr.get("mti_ok")),
                         "fresh_on": bool(r.get("fresh")) and r.get("err") is not None and r["err"] <= 3.0})
        ev = next((x for x in rows if x["inc"]), None)
        if ev is None:
            continue
        s0 = ev["t"]
        post = [x for x in rows if x["t"] >= s0]
        def first(k):
            return next((round(x["t"] - s0, 3) for x in post if x[k]), None)
        run, t3 = 0, None
        for x in post:
            run = run + 1 if x["conj"] else 0
            if run >= 3:
                t3 = round(x["t"] - s0, 3); break
        evs.append({"boot": boot, "Z0": round(ev["Z"], 2), "uciete": first("fresh_on") is None,
                    "box_on": first("on"), "mti": first("mti"), "conj": first("conj"), "run3": t3,
                    "fresh_on": first("fresh_on"), "frac_stare_do_fresh": None})
    return evs


def main():
    res = {}
    for mode in ("stare", "any"):
        d = json.load(open(os.path.join(OUT, f"r1_zdarzenia_{mode}.json")))
        for pop, boots in d.items():
            evs = [dict(e, boot=b, sid=ep["sid"]) for b, eps in boots.items() for ep in eps for e in ep["zdarzenia"]]
            for cls, sel in (("Z0>=5", lambda e: e["Z0"] is not None and e["Z0"] >= 5.0),
                             ("Z0<5", lambda e: e["Z0"] is None or e["Z0"] < 5.0)):
                res[f"{mode}|{pop}|{cls}"] = stats([e for e in evs if sel(e)])
        bw = ("wk0_b1", "wk0_b2", "g0_b1", "g0_b2")          # wiatr 0 m/s (linear_velocity 0 0 0 w świecie)
        for nm, pick in (("a2_bez_wiatru", lambda b: os.path.basename(b) in bw),
                         ("a2_wiatr", lambda b: os.path.basename(b) not in bw)):
            res[f"{mode}|{nm}|Z0>=5"] = stats([e for b, eps in d["a2"].items() if pick(b) for ep in eps
                                                for e in ep["zdarzenia"] if e["Z0"] is not None and e["Z0"] >= 5.0])
        res[f"{mode}|a+a2bw+b|Z0>=5"] = None
        res[f"{mode}|a+a2|Z0>=5"] = stats([dict(e) for pop in ("a", "a2") for b, eps in d[pop].items()
                                           for ep in eps for e in ep["zdarzenia"] if e["Z0"] is not None and e["Z0"] >= 5.0])
    db = det_events()
    res["b|DET|Z0>=5"] = stats([e for e in db if e["Z0"] >= 5.0])
    for mode in ("stare", "any"):
        d = json.load(open(os.path.join(OUT, f"r1_zdarzenia_{mode}.json")))
        bw = ("wk0_b1", "wk0_b2", "g0_b1", "g0_b2")
        evs = [e for b, eps in d["a"].items() for ep in eps for e in ep["zdarzenia"] if e["Z0"] and e["Z0"] >= 5.0]
        evs += [e for b, eps in d["a2"].items() if os.path.basename(b) in bw for ep in eps for e in ep["zdarzenia"]
                if e["Z0"] and e["Z0"] >= 5.0]
        evs += [e for e in db if e["Z0"] >= 5.0]
        res[f"{mode}|a+a2bw+b|Z0>=5"] = stats(evs)
    res["b_zdarzenia"] = db
    json.dump(res, open(os.path.join(OUT, "r1_L.json"), "w"), indent=1)
    for k, v in res.items():
        if k == "b_zdarzenia" or v is None:
            continue
        print(f"{k:22s} n={v['n']:3d} uc={v['n_uciete']:2d} " + " ".join(
            f"{m}:{v[m]['p50']}/{v[m]['p90']}/{v[m]['p95']}" for m in MS) +
            f" | przyjete p90 {v['fresh_on_przyjete']['p90']} max {v['fresh_on_przyjete']['max']} stare50 {v['frac_stare_do_fresh_p50']}")


if __name__ == "__main__":
    main()
