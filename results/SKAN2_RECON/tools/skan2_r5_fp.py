#!/usr/bin/env python3
"""results/SKAN2_RECON/tools/skan2_r5_fp.py — R5b: fałszywe admisje w fazie skanu.

Per epizod (te same boot-y/warstwy co R1/R2): zdarzenia ENTRY w percep_feed (ev == "ENTRY") od t0 do
pierwszej fresh na celu (skan2_r1: |trk−GT|_xy ≤ 3 m, GT z manifestu). ENTRY z |trk−GT|_xy > 3 m = admisja
FAŁSZYWA (tło/speckle). Dodatkowo: czy ENTRY padło w rampie (|yaw_rate| ≥ 30°/s) czy w stare.
Wyjście: r5_fp.json + wydruk.  Użycie: skan2_r5_fp.py <out.json> <bootdir>,<warstwa> ...
"""
import json, math, os, sys
sys.path.insert(0, "/home/olga/projects/liquidpatrol/results/SKAN2_RECON/tools")
import skan2_r1 as K


def analyze(d):
    eps = [(r["scenario_id"], r["t0_sim"]) for r in K.iter_jsonl(os.path.join(d, "trace.jsonl"))
           if r.get("t") == "event" and r.get("ev") == "episode_start" and r.get("scenario_id")]
    demo = list(K.iter_jsonl(os.path.join(d, "demo.jsonl")))
    pf = sorted((r for r in K.iter_jsonl(os.path.join(d, "percep_feed.jsonl"))
                 if r.get("t_frame") is not None and r.get("own_q")), key=lambda r: r["t_frame"])
    out = []
    for sid, t0 in eps:
        drows = [r for r in demo if r.get("scenario_id") == sid]
        if not drows:
            continue
        tend = drows[-1]["t_sim"]
        fr = [r for r in pf if t0 <= r["t_frame"] <= tend]
        def gt(t):
            x, y, z = K.S.position_at(K.MAN[sid], t - t0)
            return [x, y]
        t_acq = None
        ent = []
        prev = None
        for r in fr:
            rate = abs(K.wrap(K.yaw_of(r["own_q"]) - K.yaw_of(prev["own_q"]))) / (r["t_frame"] - prev["t_frame"]) \
                if prev is not None and r["t_frame"] > prev["t_frame"] else 0.0
            prev = r
            on = None
            if r.get("trk_pos_ned"):
                g = gt(r["t_frame"])
                on = math.hypot(r["trk_pos_ned"][0] - g[0], r["trk_pos_ned"][1] - g[1]) <= K.FRESH_GATE_M
            if r.get("ev") == "ENTRY":
                ent.append({"t_rel": round(r["t_frame"] - t0, 3), "na_celu": on, "rampa": rate >= 30.0,
                            "rate": round(rate, 1)})
            if r.get("fresh") and on:
                t_acq = r["t_frame"]
                break
        out.append({"sid": sid, "t_acq_rel": t_acq and round(t_acq - t0, 3), "ENTRY_przed_akw": ent})
    return out


res, summ = {}, {}
for a in sys.argv[2:]:
    d, lab = a.split(",")
    res.setdefault(lab, {})[d] = analyze(os.path.join(K.ROOT, d))
for lab, boots in res.items():
    ents = [e for eps in boots.values() for ep in eps for e in ep["ENTRY_przed_akw"]]
    summ[lab] = {"n_epizodow": sum(len(v) for v in boots.values()), "ENTRY": len(ents),
                 "ENTRY_falszywe": sum(1 for e in ents if e["na_celu"] is False),
                 "ENTRY_na_celu": sum(1 for e in ents if e["na_celu"]),
                 "ENTRY_na_celu_w_rampie": sum(1 for e in ents if e["na_celu"] and e["rampa"]),
                 "ENTRY_falszywe_w_rampie": sum(1 for e in ents if e["na_celu"] is False and e["rampa"])}
json.dump({"warstwy": summ, "per_boot": res}, open(sys.argv[1], "w"), indent=1)
print(json.dumps(summ, indent=1))
