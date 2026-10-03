#!/usr/bin/env python3
"""results/2A/tools/percep_judge.py — sędzia percepcji OFFLINE (noga 2A, PRE_2A §3 etap B).

JEDYNE miejsce toru 2A, które dotyka GT (reguła nadrzędna PROMPT_2A_S1): porównuje log feedu
z gt_intruder.jsonl PO locie. Metryki (PRE B + PROMPT §3):
  - błąd NED e(t)=|trk_pos_ned−GT| na tickach track_valid: mean/p50/p95/max, n;
  - DEKOMPOZYCJA kierunek-vs-zasięg (obowiązkowa przy cytowaniu C): błąd kątowy [deg]
    między LOS(own→trk) a LOS(own→gt) oraz błąd zasięgu |d_trk−d_gt| (+bias ze znakiem);
  - kadencja świeżych próbek [Hz] (p50 z odstępów między świeżymi);
  - latencja end-to-end capture→update (p50/p95), gdy log niesie stemple (t_frame, t_update_sim).

Tryby:
  --demo <bootdir>                 FeedB z demo.jsonl + gt_intruder.jsonl (sanity przyrządu:
                                   baseline RECON R4 na r1_ncp: mean 0.741 / p50 0.673 / p95 1.258)
  --shadow <log> --gt <gt.jsonl>   shadow-log FEED-V (harness/feed_vision._ingest) + GT
Wyjście: JSON na stdout (+ --out plik).
"""
import argparse
import bisect
import json
import math
import os
import sys


def load_jsonl(path):
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


def gt_index(gt_rows):
    """episode_id → (ts, ned[]); wiersze gt_intruder.jsonl (klucz 'ned' = APPLIED NED)."""
    gt = {}
    for r in gt_rows:
        e = gt.setdefault(r["episode_id"], ([], []))
        e[0].append(r["t_sim"])
        e[1].append(r["ned"])
    return gt


def gt_flat(gt_rows):
    """Jedna oś czasu (shadow-log nie zna episode_id): (ts, ned[]) posortowane po t_sim."""
    rows = sorted(gt_rows, key=lambda r: r["t_sim"])
    return [r["t_sim"] for r in rows], [r["ned"] for r in rows]


def interp(ts, ps, t):
    """Interpolacja liniowa; None poza [ts[0], ts[-1]] (identycznie jak sanity RECON R4)."""
    if not ts or t < ts[0] or t > ts[-1]:
        return None
    i = bisect.bisect_right(ts, t)
    if i >= len(ts):
        return ps[-1]
    t0, t1 = ts[i - 1], ts[i]
    a = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
    return [ps[i - 1][k] + a * (ps[i][k] - ps[i - 1][k]) for k in range(3)]


def _stats(xs):
    if not xs:
        return None
    s = sorted(xs)
    n = len(s)
    return {"n": n, "mean": round(sum(s) / n, 3), "p50": round(s[n // 2], 3),
            "p95": round(s[int(n * 0.95)], 3), "max": round(s[-1], 3)}


def _accumulate(samples, out):
    """samples: iterable (t, own[3]|None, trk[3], gt[3], fresh:bool). Buduje metryki."""
    errs, angs, rngs, rng_signed, fresh_ts = [], [], [], [], []
    for (t, own, trk, gt, fresh) in samples:
        e = math.dist(trk, gt)
        errs.append(e)
        if fresh:
            fresh_ts.append(t)
        if own is not None:
            v_t = [trk[k] - own[k] for k in range(3)]
            v_g = [gt[k] - own[k] for k in range(3)]
            d_t = math.sqrt(sum(x * x for x in v_t))
            d_g = math.sqrt(sum(x * x for x in v_g))
            if d_t > 1e-6 and d_g > 1e-6:
                c = sum(v_t[k] * v_g[k] for k in range(3)) / (d_t * d_g)
                angs.append(math.degrees(math.acos(max(-1.0, min(1.0, c)))))
                rngs.append(abs(d_t - d_g))
                rng_signed.append(d_t - d_g)
    out["err_ned_m"] = _stats(errs)
    out["decomp"] = {"angular_deg": _stats(angs), "range_abs_m": _stats(rngs),
                     "range_bias_m": (round(sum(rng_signed) / len(rng_signed), 3)
                                      if rng_signed else None)}
    gaps = [b - a for a, b in zip(fresh_ts, fresh_ts[1:]) if 0 < b - a < 5.0]
    out["fresh_cadence_hz_p50"] = (round(1.0 / sorted(gaps)[len(gaps) // 2], 2) if gaps else None)
    out["n_fresh"] = len(fresh_ts)
    return out


def judge_demo(bootdir):
    """FeedB: demo.jsonl (per tick, track_valid) vs gt_intruder per episode_id.
    Filtry 1:1 z sanity RECON R4 (ticki track_valid, t w zakresie GT epizodu)."""
    demo = load_jsonl(os.path.join(bootdir, "demo.jsonl"))
    gt = gt_index(load_jsonl(os.path.join(bootdir, "gt_intruder.jsonl")))
    samples = []
    for row in demo:
        if not row["track_valid"] or row["episode_id"] not in gt:
            continue
        ts, ps = gt[row["episode_id"]]
        g = interp(ts, ps, row["t_sim"])
        if g is None:
            continue
        fresh = (row["track_age_s"] == 0.0)
        samples.append((row["t_sim"], row["own_pos_ned"], row["trk_pos_ned"], g, fresh))
    out = {"mode": "demo", "src": bootdir, "latency_s": None}   # L=0.2 s z konstrukcji FeedB, nie mierzona
    return _accumulate(samples, out)


def judge_shadow(log_path, gt_path):
    """FEED-V shadow-log: błąd na rekordach z lockiem (ZOH ostatniej pozycji tracku),
    świeżość = pole fresh; latencja z (t_update_sim − t_frame), gdy runner ją niesie."""
    rows = load_jsonl(log_path)
    ts, ps = gt_flat(load_jsonl(gt_path))
    samples, lat = [], []
    last_trk = None
    for r in rows:
        if r.get("trk_pos_ned"):
            last_trk = r["trk_pos_ned"]
        if not r.get("locked") or last_trk is None:
            continue
        g = interp(ts, ps, r["t_frame"])
        if g is None:
            continue
        samples.append((r["t_frame"], r.get("own_pos_ned"), last_trk, g, bool(r.get("fresh"))))
        if r.get("fresh") and r.get("t_update_sim") is not None:
            lat.append(r["t_update_sim"] - r["t_frame"])
    out = {"mode": "shadow", "src": log_path, "latency_s": _stats(lat) if lat else None}
    return _accumulate(samples, out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", help="bootdir z demo.jsonl + gt_intruder.jsonl (FeedB)")
    ap.add_argument("--shadow", help="shadow-log FEED-V (jsonl)")
    ap.add_argument("--gt", help="gt_intruder.jsonl (wymagane z --shadow)")
    ap.add_argument("--out", help="plik wyjściowy JSON")
    a = ap.parse_args()
    if a.demo:
        res = judge_demo(a.demo)
    elif a.shadow and a.gt:
        res = judge_shadow(a.shadow, a.gt)
    else:
        ap.error("podaj --demo ALBO --shadow+--gt")
    print(json.dumps(res, indent=1))
    if a.out:
        with open(a.out, "w") as f:
            json.dump(res, f, indent=1)


if __name__ == "__main__":
    main()
