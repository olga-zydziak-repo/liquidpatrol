#!/usr/bin/env python3
"""bench/campaign_analyze.py — analiza kampanii blok1/48 (ANEKS_BENCH-1 §2/§3).

D9 = V3 (ERRATUM ANEKS §2): epizod NIEWAŻNY wyłącznie gdy najdłuższy pojedynczy stall > 3 s wall (+ timejump=0).
Realizowane WARSTWĄ ANALIZY przez override params sędziego `bench_judge` (frozen 8ec0fcfb… NIETKNIĘTY):
V3_campaign = {dsw_min:0, timejump:0, max_deep_stall:∞, longest_stall_s:3.0} → valid ⇔ timejump=0 ∧ longest≤3.0.

`judge_boot(outdir)` — per epizod z trace+gt_intruder+rtf (jak w shakeout). `wilson(k,n)` — przedział Wilsona.
`blok1_episode_ids(manifest)` — 48 id (bloki seed 1-4 × 12 komórek) w kolejności manifestu.
"""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from bench.bench_judge import judge_episode, _load_drone_ned, _load_intr_ned, _load_rtf, _interp_ned

# D9 = V3 (ANEKS §2): nieważny wyłącznie gdy najdłuższy stall > 3 s wall.
D9_V3_PARAMS = {"V3": {"dsw_min": 0.0, "timejump": 0, "max_deep_stall": 10 ** 9, "longest_stall_s": 3.0}}


def blok1_episode_ids(manifest):
    return [e["episode_id"] for e in manifest["episodes"] if e["block"] == 1]


def wilson(k, n, z=1.96):
    """Przedział ufności Wilsona dla proporcji k/n (dom. 95%). Zwraca (p, lo, hi)."""
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1.0 + z * z / n
    center = (p + z * z / (2 * n)) / d
    half = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d
    return (round(p, 4), round(max(0.0, center - half), 4), round(min(1.0, center + half), 4))


def judge_boot(outdir, params=None):
    """Zwraca listę werdyktów epizodów w boocie (trace+gt_intruder+rtf). D9=V3 (valid_V3) = ważność kampanii."""
    p = dict(D9_V3_PARAMS)
    if params:
        p.update(params)
    trace = os.path.join(outdir, "trace.jsonl")
    drone = _load_drone_ned(trace)
    intr = _load_intr_ned(os.path.join(outdir, "gt_intruder.jsonl"))
    rtf = _load_rtf(os.path.join(outdir, "rtf_stream.jsonl"))
    tj = 0
    for fn in ("timejump_pre.txt", "timejump_post.txt"):
        fp = os.path.join(outdir, fn)
        if os.path.exists(fp):
            tj += int(open(fp).read().strip() or 0)
    evs = [json.loads(l) for l in open(trace) if '"event"' in l]
    eps = []; cur = None
    for e in evs:
        if e.get("ev") == "episode_start":
            cur = {"id": e["episode_id"], "sid": e["scenario_id"], "lo": e["t0_sim"]}
        elif e.get("ev") == "invalid_start":
            cur = None
        elif e.get("ev") == "episode_end" and cur:
            cur["hi"] = e["sim"]; cur["refuse"] = e.get("refuse", 0); cur["breach"] = e.get("breach", False)
            eps.append(cur); cur = None
    out = []
    for ep in eps:
        dg = [(t, q) for t, q in drone if ep["lo"] <= t <= ep["hi"]]
        v = judge_episode(dg, intr, rtf=rtf, refuse_count=ep["refuse"], breach=ep["breach"],
                          timejump=tj, params=p)
        # d_min po 3 s (faza orbity) — diagnostyka
        dm3 = 1e9
        for t, q in dg:
            if t - ep["lo"] >= 3.0:
                ip = _interp_ned(intr, t)
                if ip:
                    dm3 = min(dm3, math.sqrt(sum((ip[k] - q[k]) ** 2 for k in range(3))))
        v["episode_id"] = ep["id"]; v["scenario_id"] = ep["sid"]
        v["d_min_orbit"] = round(dm3, 3) if dm3 < 1e9 else None
        v["valid_campaign_D9V3"] = v["valid_V3"]        # D9=V3
        out.append(v)
    return out


def aggregate_p_exec(episode_verdicts):
    """p_exec = udane D6 / WAŻNE (D9=V3). Zwraca dict z liczbami + Wilson."""
    valid = [v for v in episode_verdicts if v["valid_campaign_D9V3"]]
    succ = [v for v in valid if v["success_D6"]]
    p, lo, hi = wilson(len(succ), len(valid))
    return {"n_episodes": len(episode_verdicts), "n_valid": len(valid), "n_success": len(succ),
            "p_exec": p, "wilson95": [lo, hi],
            "n_invalid_D9V3": len(episode_verdicts) - len(valid),
            "v2_flag": sum(1 for v in episode_verdicts if not v["valid_V2"])}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("outdirs", nargs="+")
    a = ap.parse_args()
    allv = []
    for od in a.outdirs:
        vs = judge_boot(od)
        allv += vs
        for v in vs:
            print(f"{v['scenario_id']}: D6={v['success_D6']} valid(D9V3)={v['valid_campaign_D9V3']} "
                  f"frac[6,10]={v['frac_band_6_10']} d_min={v['d_min_m']} dorb={v['d_min_orbit']} "
                  f"REFUSE={v['refuse_count']} breach={v['breach']}")
    print(json.dumps(aggregate_p_exec(allv)))
