#!/usr/bin/env python3
"""results/DET/tools/detS4_analyze.py — rozbiór JEDNEGO bootu kampanii C (ANEKS_DET-3 §3.4/§3.5/§3.6).

Per epizod:
  * werdykt sędziego i ważność V2′ — z manifest.json (bench_finalize, sędzia frozen 8ec0fcfb
    przez override V2′ jak LIQ/kampanie; TU NIC NIE LICZYMY NA NOWO);
  * ramię V2: ŻYWOŚĆ feedu VERBATIM ANEKS_2A-3 §4 — w pierwszych 30 s epizodu ≥1 świeża
    próbka tracku ALBO ≥10 klatek przetworzonych (percep_feed.jsonl, okna z trace);
    martwy feed ⇒ epizod NIEWAŻNY instrumentowo (valid_final=False);
  * telemetria (ANEKS_DET-3 §3.6, OPISOWA): err feedu vs GT p50/p95/max w KONWENCJI NOGI
    (próbki ŚWIEŻE: V2 → wiersze fresh percep_feed.jsonl @t_frame, jak smoke/T2;
    B → ticki track_valid demo.jsonl, świeże z konstrukcji FeedB ≤0.1 s) vs interpolowany
    gt_intruder.jsonl; DODATKOWO err_consumed (demo, oba ramiona) = co widział kontroler,
    z artefaktem granicy epizodu (track V2 trzyma pozę sprzed teleportu startowego przez
    ≤1 s wieku + ~2 s re-ENTRY — udokumentowane, nie wchodzi do err_fresh);
    frakcja fresh (demo frac_track_valid + dla V2 fresh/frames z percep_feed w oknie),
    FEED_EXPIRE w oknie, z_max (NED→alt), r_max, d_min (sędzia), err w paśmie d<6 m
    OSOBNO (d = |own−GT|, own interpolowany z demo);
  * REFUSE per gałąź (trace, okno epizodu) — wynik epizodu, nie unieważnienie.
Sygnały STOP bootu (ANEKS_DET-3 §3.5): breach LUB REFUSE(POS*) ⇒ stop_now=True.

Użycie: detS4_analyze.py <OUTDIR> → <OUTDIR>/detS4_summary.json + print JSON.
"""
import bisect
import json
import math
import os
import sys


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


def estat(xs):
    return {"n": len(xs), "p50": round(pct(xs, 0.5), 3) if xs else None,
            "p95": round(pct(xs, 0.95), 3) if xs else None,
            "max": round(max(xs), 3) if xs else None}


def main(outdir):
    mp = os.path.join(outdir, "manifest.json")
    man = json.load(open(mp)) if os.path.exists(mp) else None
    arm = (man or {}).get("det_arm") or ("V2" if os.path.exists(os.path.join(outdir, "percep_feed.jsonl")) else "B")
    trace = rows(os.path.join(outdir, "trace.jsonl"))
    demo = rows(os.path.join(outdir, "demo.jsonl"))
    feed = rows(os.path.join(outdir, "percep_feed.jsonl"))
    gti = rows(os.path.join(outdir, "gt_intruder.jsonl"))
    evs = [r for r in trace if r.get("ev")]

    # okna epizodów z trace
    wins = {}
    cur = None
    for e in evs:
        if e["ev"] == "episode_start":
            cur = {"id": e["episode_id"], "sid": e["scenario_id"], "lo": e["t0_sim"]}
        elif e["ev"] == "invalid_start":
            cur = None
        elif e["ev"] == "episode_end" and cur:
            cur["hi"] = e["sim"]
            wins[cur["id"]] = cur
            cur = None

    # GT intruza — interpolacja
    gts = sorted((g["t_sim"], g["ned"]) for g in gti)
    gt_t = [g[0] for g in gts]

    def gt_at(t):
        if not gt_t or t < gt_t[0] or t > gt_t[-1]:
            return None
        i = bisect.bisect_right(gt_t, t)
        i = max(1, min(i, len(gts) - 1))
        a = (t - gt_t[i - 1]) / (gt_t[i] - gt_t[i - 1]) if gt_t[i] > gt_t[i - 1] else 0
        return [gts[i - 1][1][k] + a * (gts[i][1][k] - gts[i - 1][1][k]) for k in range(3)]

    # demo per epizod
    dep = {}
    for d in demo:
        dep.setdefault(d["episode_id"], []).append(d)

    # own pos — interpolacja z demo (do pasma d<6 m dla próbek fresh V2 @t_frame)
    owns = sorted((d["t_sim"], d["own_pos_ned"]) for d in demo)
    own_t = [o[0] for o in owns]

    def own_at(t):
        if not own_t or t < own_t[0] or t > own_t[-1]:
            return None
        i = bisect.bisect_right(own_t, t)
        i = max(1, min(i, len(owns) - 1))
        a = (t - own_t[i - 1]) / (own_t[i] - own_t[i - 1]) if own_t[i] > own_t[i - 1] else 0
        return [owns[i - 1][1][k] + a * (owns[i][1][k] - owns[i - 1][1][k]) for k in range(3)]

    out_eps = []
    stop_now = False
    man_eps = {e["episode_id"]: e for e in (man or {}).get("episodes", [])}
    for eid, w in sorted(wins.items()):
        me = man_eps.get(eid, {})
        dd = dep.get(eid, [])
        # err_consumed: co widział kontroler (demo, oba ramiona; artefakt granicy epizodu w środku)
        errs_cons = []
        for d in dd:
            g = gt_at(d["t_sim"])
            if g is not None and d.get("track_valid") and d.get("trk_pos_ned"):
                errs_cons.append(math.dist(d["trk_pos_ned"], g))
        # err_fresh: konwencja nogi (T2/smoke) + pasmo d<6 m
        errs, errs_lt6, errs_ge6 = [], [], []
        if arm == "V2":
            for r in feed:
                t = r.get("t_frame")
                if t is None or not r.get("fresh") or not r.get("trk_pos_ned"):
                    continue
                if not (w["lo"] <= t <= w["hi"]):
                    continue
                g = gt_at(t)
                o = own_at(t)
                if g is None:
                    continue
                e = math.dist(r["trk_pos_ned"], g)
                errs.append(e)
                if o is not None:
                    (errs_lt6 if math.dist(o, g) < 6.0 else errs_ge6).append(e)
        else:
            for d in dd:
                g = gt_at(d["t_sim"])
                if g is None or not d.get("track_valid") or not d.get("trk_pos_ned"):
                    continue
                e = math.dist(d["trk_pos_ned"], g)
                errs.append(e)
                (errs_lt6 if math.dist(d["own_pos_ned"], g) < 6.0 else errs_ge6).append(e)
        rr = [math.hypot(d["own_pos_ned"][0], d["own_pos_ned"][1]) for d in dd]
        zz = [-d["own_pos_ned"][2] for d in dd]
        tv = sum(1 for d in dd if d.get("track_valid"))
        v2 = None
        if arm == "V2":
            fw = [r for r in feed if "t_frame" in r and w["lo"] <= r["t_frame"] <= w["hi"]]
            f30 = [r for r in fw if r["t_frame"] <= w["lo"] + 30.0]
            nf30 = sum(1 for r in f30 if r.get("fresh"))
            v2 = {"n_frames": len(fw), "n_fresh": sum(1 for r in fw if r.get("fresh")),
                  "n_feed_expire": sum(1 for r in fw if r.get("ev") == "FEED_EXPIRE"),
                  "n_entry": sum(1 for r in fw if r.get("ev") == "ENTRY"),
                  "alive_30s": {"n_frames_30s": len(f30), "n_fresh_30s": nf30,
                                "alive": bool(nf30 >= 1 or len(f30) >= 10)}}
        alive = (v2["alive_30s"]["alive"] if v2 else True)
        valid_v2p = bool(me.get("valid_V2p"))
        ep = {
            "episode_id": eid, "scenario_id": w["sid"],
            "valid_V2p": valid_v2p, "alive_feed": alive,
            "valid_final": bool(valid_v2p and alive),
            "success_D6": bool(me.get("success_D6")),
            "d_min_m": me.get("d_min_m"),
            "refuse_count": me.get("refuse_count", 0), "breach": bool(me.get("breach")),
            "n_deep_stall": me.get("n_deep_stall"), "longest_stall_s": me.get("longest_stall_s"),
            "dsim_dwall": me.get("dsim_dwall"),
            "telemetry": {
                "err_fresh": estat(errs),
                "err_consumed_demo": estat(errs_cons),
                "err_d_lt6": estat(errs_lt6), "err_d_ge6": estat(errs_ge6),
                "frac_track_valid": round(tv / len(dd), 4) if dd else None,
                "r_max": round(max(rr), 2) if rr else None,
                "z_max_alt": round(max(zz), 2) if zz else None,
                "feed_v2": v2},
        }
        out_eps.append(ep)
        if ep["breach"]:
            stop_now = True

    # REFUSE z trace per gałąź (boot-level; przypisanie epizodowe niesie manifest refuse_count)
    refuse_evs = [r for r in evs if r["ev"] == "refuse"]
    branches = {}
    for r in refuse_evs:
        k = str(r.get("reason"))
        branches[k] = branches.get(k, 0) + 1
        if "POS" in k.upper():
            stop_now = True
    breach_evs = [r for r in evs if r["ev"] == "breach"]
    if breach_evs:
        stop_now = True

    out = {"outdir": outdir, "det_arm": arm,
           "det_round": (man or {}).get("det_round"),
           "rc": (man or {}).get("rc"), "feed_sha": (man or {}).get("feed_sha"),
           "weights_sha": ((man or {}).get("weights_sha") or "")[:16],
           "n_episodes": len(out_eps),
           "n_valid_final": sum(1 for e in out_eps if e["valid_final"]),
           "episodes": out_eps,
           "s_bezp": {"breach_events": len(breach_evs), "refuse_events": len(refuse_evs),
                      "refuse_branches": branches,
                      "refuse_detail": [{k: r.get(k) for k in ("reason", "r_est", "t_rel")}
                                        for r in refuse_evs]},
           "stop_now": stop_now,
           "missing_manifest": man is None}
    json.dump(out, open(os.path.join(outdir, "detS4_summary.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
