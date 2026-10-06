#!/usr/bin/env python3
"""results/2A/tools/probeC_analyze.py — rozbiór bootu C-sondy (ANEKS_2A-2 §3) z artefaktów
bootu (trace.jsonl + demo.jsonl + feed_v.jsonl + gt_intruder.jsonl). Zero GT w torze lotu —
GT tylko do opisu trajektorii względem fantomów (S-MISJA, bez progów).

S-BEZP (kryterialne): breach R_E (wymagane 0), REFUSE per gałąź, REFUSE(POS) ⇒ STOP.
S-MISJA (opisowe): frakcja track_valid, frakcja hover-hold (|cmd|<0.1), orbit-entry/t_entry,
z_max, maks. zbliżenie do R_E, fantomy (|trk_pos| od home, odległość tracku od intruza GT).

Użycie: probeC_analyze.py <OUTDIR> → <OUTDIR>/probeC_summary.json + print
"""
import json
import math
import os
import sys

R_E = 32.0


def _rows(path):
    if not os.path.exists(path):
        return []
    out = []
    with open(path) as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                try:
                    out.append(json.loads(ln))
                except json.JSONDecodeError:
                    pass
    return out


def _pct(xs, q):
    if not xs:
        return None
    s = sorted(xs)
    i = min(len(s) - 1, max(0, int(round(q * (len(s) - 1)))))
    return s[i]


def main(outdir):
    trace = _rows(os.path.join(outdir, "trace.jsonl"))
    demo = _rows(os.path.join(outdir, "demo.jsonl"))
    feed = _rows(os.path.join(outdir, "feed_v.jsonl"))
    gti = _rows(os.path.join(outdir, "gt_intruder.jsonl"))

    evs = [r for r in trace if "ev" in r]
    def ev_all(name):
        return [r for r in evs if r["ev"] == name]

    ep_end = ev_all("episode_end")
    refuse = ev_all("refuse")
    breach = ev_all("breach")

    # --- S-BEZP ---
    s_bezp = {
        "breach_count": len(breach),
        "breach_events": [{k: r.get(k) for k in ("episode_id", "r_est")} for r in breach],
        "refuse_count": len(refuse),
        "refuse_branches": {},
        "refuse_events": [{k: r.get(k) for k in ("episode_id", "reason", "r_est", "t_rel")} for r in refuse],
    }
    for r in refuse:
        key = str(r.get("reason"))
        s_bezp["refuse_branches"][key] = s_bezp["refuse_branches"].get(key, 0) + 1

    # --- S-MISJA z demo.jsonl (ticki epizodu) ---
    n = len(demo)
    tv = [r for r in demo if r["track_valid"]]
    hover = [r for r in demo if math.hypot(*r["cmd_v_ned"][:2]) < 0.1 and abs(r["cmd_v_ned"][2]) < 0.1]
    r_ests = [math.hypot(r["own_pos_ned"][0], r["own_pos_ned"][1]) for r in demo]
    zs = [r["own_pos_ned"][2] for r in demo]
    phases = {}
    for r in demo:
        phases[str(r["phase"])] = phases.get(str(r["phase"]), 0) + 1
    # fantomy: |trk_pos| od home na tickach z trackiem
    trk_r = [math.hypot(r["trk_pos_ned"][0], r["trk_pos_ned"][1]) for r in tv]
    # odległość tracku od intruza GT (najbliższa próbka GT w sim-time)
    gts = sorted([(g.get("t_sim", g.get("t", 0.0)), g) for g in gti]) if gti else []
    def _gt_at(t):
        if not gts:
            return None
        lo, hi = 0, len(gts) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if gts[mid][0] < t:
                lo = mid + 1
            else:
                hi = mid
        cand = [gts[max(0, lo - 1)], gts[lo]]
        return min(cand, key=lambda p: abs(p[0] - t))[1]
    trk_vs_gt = []
    for r in tv:
        g = _gt_at(r["t_sim"])
        if g is None:
            continue
        p = g.get("ned")
        if p:
            trk_vs_gt.append(math.dist(r["trk_pos_ned"], p))

    t_entry = ep_end[0].get("t_entry") if ep_end else None
    s_misja = {
        "n_ticks": n,
        "frac_track_valid": round(len(tv) / n, 4) if n else None,
        "frac_hover_hold_cmd": round(len(hover) / n, 4) if n else None,
        "phase_hist": phases,
        "orbit_entry": t_entry is not None,
        "t_entry": t_entry,
        "z_min_ned_m": round(min(zs), 2) if zs else None,     # najwyżej (NED: ujemne=góra)
        "z_max_ned_m": round(max(zs), 2) if zs else None,
        "r_est_max_m": round(max(r_ests), 2) if r_ests else None,
        "margin_to_RE_min_m": round(R_E - max(r_ests), 2) if r_ests else None,
        "track_r_from_home": {"p50": _pct(trk_r, 0.5), "p95": _pct(trk_r, 0.95),
                              "max": max(trk_r) if trk_r else None,
                              "n_beyond_RE": sum(1 for x in trk_r if x > R_E)},
        "track_err_vs_gt_m": {"p50": _pct(trk_vs_gt, 0.5), "p95": _pct(trk_vs_gt, 0.95),
                              "max": max(trk_vs_gt) if trk_vs_gt else None, "n": len(trk_vs_gt)},
    }

    # --- feed_v.jsonl: stan toru percepcji w locie ---
    f_boxes = [r for r in feed if r.get("box")]
    f_fresh = [r for r in feed if r.get("fresh")]
    f_evs = {}
    for r in feed:
        if r.get("ev"):
            f_evs[r["ev"]] = f_evs.get(r["ev"], 0) + 1
    gates = {}
    for r in f_fresh:
        gates[str(r.get("gate"))] = gates.get(str(r.get("gate")), 0) + 1
    feed_stats = {
        "n_frames": len(feed), "n_boxes": len(f_boxes), "n_fresh": len(f_fresh),
        "events": f_evs, "fresh_gates": gates,
        "feed_hz": None,
    }
    if len(feed) >= 2:
        dt = feed[-1]["t_frame"] - feed[0]["t_frame"]
        if dt > 0:
            feed_stats["feed_hz"] = round(len(feed) / dt, 2)

    out = {"outdir": outdir, "s_bezp": s_bezp, "s_misja": s_misja, "feed_v": feed_stats}
    # kind/valid z manifestu, jeśli jest
    mp = os.path.join(outdir, "manifest.json")
    if os.path.exists(mp):
        m = json.load(open(mp))
        out["manifest"] = {k: m.get(k) for k in ("kind", "rc", "net_arm", "weights_sha",
                                                 "feed_sha", "n_valid_V2p", "episodes")}
    with open(os.path.join(outdir, "probeC_summary.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
