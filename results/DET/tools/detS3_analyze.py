#!/usr/bin/env python3
"""results/DET/tools/detS3_analyze.py — rozbiór bootu smoke S3 (ANEKS_DET-2 §4.4).

Bramki runtime: (a) kadencja PRZETWARZANIA klatek p50 ≥8 Hz (def. czasowa PRE §5 —
z dt kolejnych t_frame w percep_feed.jsonl); E2E p95 ≤0.25 s (stempel klatki → próbka
u klienta; client_e2e.jsonl, sim-time). Żywość (ANEKS_2A-3 §4 verbatim): ≥1 świeża LUB
≥10 klatek w 30 s epizodu. S-BEZP: breach/REFUSE z trace. Opisowe: kadencja świeżych
(def. b), err tracku vs GT (offline, percep_feed vs gt_intruder — pierwsze
zamknięto-pętlowe echo T2), rozkład admisji, r/z/hover z demo.jsonl.
Użycie: detS3_analyze.py <OUTDIR> → <OUTDIR>/smoke_summary.json + print
"""
import bisect
import json
import math
import os
import sys

R_E = 32.0


def rows(p):
    if not os.path.exists(p):
        return []
    out = []
    for ln in open(p):
        ln = ln.strip()
        if ln:
            try:
                out.append(json.loads(ln))
            except json.JSONDecodeError:
                pass
    return out


def pct(xs, q):
    if not xs:
        return None
    s = sorted(xs)
    return s[min(len(s) - 1, int(q * (len(s) - 1)))]


def main(outdir):
    trace = rows(os.path.join(outdir, "trace.jsonl"))
    demo = rows(os.path.join(outdir, "demo.jsonl"))
    feed = [r for r in rows(os.path.join(outdir, "percep_feed.jsonl")) if "t_frame" in r]
    e2e = rows(os.path.join(outdir, "client_e2e.jsonl"))
    gti = rows(os.path.join(outdir, "gt_intruder.jsonl"))
    evs = [r for r in trace if r.get("ev")]

    def ev_all(n):
        return [r for r in evs if r["ev"] == n]

    refuse = ev_all("refuse"); breach = ev_all("breach")
    s_bezp = {"breach_count": len(breach), "refuse_count": len(refuse),
              "refuse_branches": {}, "refuse_events":
              [{k: r.get(k) for k in ("reason", "r_est", "t_rel")} for r in refuse]}
    for r in refuse:
        k = str(r.get("reason")); s_bezp["refuse_branches"][k] = s_bezp["refuse_branches"].get(k, 0) + 1

    # bramka (a): kadencja przetwarzania
    ts = [r["t_frame"] for r in feed]
    dts = [b - a for a, b in zip(ts, ts[1:]) if 0 < b - a < 2.0]
    hz_p50 = round(1.0 / pct(dts, 0.5), 2) if dts else None
    # bramka E2E
    lat = [r["e2e_s"] for r in e2e if r.get("e2e_s") is not None and r["e2e_s"] >= 0]
    e2e_p95 = round(pct(lat, 0.95), 4) if lat else None
    # żywość
    ep0 = ev_all("episode_start")
    t0 = ep0[0]["t0_sim"] if ep0 else None
    alive = None
    if t0 is not None:
        w = [r for r in feed if t0 <= r["t_frame"] <= t0 + 30.0]
        nf = sum(1 for r in w if r.get("fresh"))
        alive = {"t0": t0, "n_frames_30s": len(w), "n_fresh_30s": nf,
                 "alive": bool(nf >= 1 or len(w) >= 10)}
    # opisowe: świeże, admisja, err vs GT (offline)
    fresh = [r for r in feed if r.get("fresh")]
    fts = [r["t_frame"] for r in fresh]
    fdts = [b - a for a, b in zip(fts, fts[1:]) if 0 < b - a < 5.0]
    adm = {}
    gates = {}
    for r in feed:
        if r.get("ev"):
            adm[r["ev"]] = adm.get(r["ev"], 0) + 1
        if r.get("fresh"):
            gates[str(r.get("gate"))] = gates.get(str(r.get("gate")), 0) + 1
    gts = sorted((g["t_sim"], g["ned"]) for g in gti)
    gt_t = [g[0] for g in gts]

    def gt_at(t):
        if not gt_t or t < gt_t[0] or t > gt_t[-1]:
            return None
        i = bisect.bisect_right(gt_t, t)
        i = max(1, min(i, len(gts) - 1))
        a = (t - gt_t[i - 1]) / (gt_t[i] - gt_t[i - 1]) if gt_t[i] > gt_t[i - 1] else 0
        return [gts[i - 1][1][k] + a * (gts[i][1][k] - gts[i - 1][1][k]) for k in range(3)]

    errs = []
    for r in fresh:
        if not r.get("trk_pos_ned"):
            continue
        g = gt_at(r["t_frame"])
        if g:
            errs.append(math.dist(r["trk_pos_ned"], g))
    # demo: r/z/hover
    rr = [math.hypot(d["own_pos_ned"][0], d["own_pos_ned"][1]) for d in demo]
    zz = [d["own_pos_ned"][2] for d in demo]
    tv = sum(1 for d in demo if d["track_valid"])
    hov = sum(1 for d in demo if math.hypot(*d["cmd_v_ned"][:2]) < 0.1 and abs(d["cmd_v_ned"][2]) < 0.1)
    ep_end = ev_all("episode_end")

    out = {
        "outdir": outdir,
        "bramki_runtime": {
            "kadencja_przetwarzania_hz_p50": hz_p50, "PASS_kadencja": (hz_p50 or 0) >= 8.0,
            "e2e_p95_s": e2e_p95, "PASS_e2e": (e2e_p95 is not None and e2e_p95 <= 0.25),
            "n_frames": len(feed), "n_e2e": len(lat)},
        "zywosc_aneks2a3": alive,
        "s_bezp": s_bezp,
        "opisowe": {
            "kadencja_swiezych_hz_p50": (round(1.0 / pct(fdts, 0.5), 2) if fdts else None),
            "n_fresh": len(fresh), "admisja_ev": adm, "fresh_gates": gates,
            "err_vs_gt_fresh": {"n": len(errs), "p50": round(pct(errs, 0.5), 3) if errs else None,
                                "p95": round(pct(errs, 0.95), 3) if errs else None,
                                "max": round(max(errs), 3) if errs else None},
            "t_entry": (ep_end[0].get("t_entry") if ep_end else None),
            "r_est_max": round(max(rr), 2) if rr else None,
            "z_min_ned": round(min(zz), 2) if zz else None,
            "frac_track_valid": round(tv / len(demo), 4) if demo else None,
            "frac_hover_cmd": round(hov / len(demo), 4) if demo else None},
    }
    mp = os.path.join(outdir, "manifest.json")
    if os.path.exists(mp):
        m = json.load(open(mp))
        out["manifest"] = {k: m.get(k) for k in ("kind", "rc", "net_arm", "feed_sha", "n_valid_V2p", "episodes", "feed_v2")}
    json.dump(out, open(os.path.join(outdir, "smoke_summary.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
