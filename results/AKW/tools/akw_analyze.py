#!/usr/bin/env python3
"""results/AKW/tools/akw_analyze.py — rozbiór JEDNEGO bootu nogi AKW (PRE_AKW §4/§5).

KOPIA results/DET/tools/detS4_analyze.py (FROZEN, nietknięty) z dodatkami AKW:
  * klucze manifestu akw_arm/akw_round (driver akw_boot.sh), summary → akw_summary.json;
  * per epizod blok "akw":
      - sędzia pełny (bench.campaign_analyze.judge_boot — sędzia FROZEN 8ec0fcfb,
        override V2′ jak kampanie): t_entry_s, fail_reasons;
      - skan z demo.jsonl: t_first_track_rel (pierwszy tick track_valid od startu
        epizodu = akwizycja), frac_hold, n_hold_runs (odcinki hold), reaquisitions
        (przejścia hold→track), osc_track_to_hold_w_5s_po_akwizycji (oscylacja
        skan↔ENTRY, PRE §4 opisowo);
      - fałszywe ENTRY: eventy ENTRY z percep_feed klasyfikowane jak R3:
        F1_cel (świeża próbka ±0.5 s z err<3 m vs GT) / F2_poza_oknem_GT (gt_at None —
        artefakt locku-przed-epizodem) / F3_kandydat_tla (reszta; przegląd ręczny);
      - stopnie skanu do pierwszego boxu świeżego i do ENTRY (PROMPT_AKW_S1 §3
        opisowo): ω·max(0, t_rel − dwell) dla pierwszej świeżej próbki / pierwszego
        ENTRY, liczone od startu pierwszego hold epizodu (przybliżenie: start epizodu);
  * boot-level sanity profilu w locie (PROMPT_AKW_S1 §3 opisowo): yaw pojazdu
    z boot.ulg (pyulog, vehicle_attitude) — rozkład |dψ/dt| w segmentach rotacji
    (5–100 °/s), p50 oczekiwane ~30 °/s, frakcja czasu rotacji w paśmie 25–35 °/s,
    suma omiecionych stopni; bez progu, bez wyrównywania zegarów;
  * boot-level bramka B (verbatim DET S3): kadencja przetwarzania z dt kolejnych
    t_frame percep_feed (CAŁY boot) p50 ≥8 Hz; E2E p95 ≤0.25 s z client_e2e_full.jsonl
    (pełny przechwyt drivera; klient frozen nadpisuje per epizod);
  * blok "smoke_gates" (tylko gdy zestaw epizodów = c00_s01…c03_s01): bramka A
    (ENTRY wg sędziego t_entry_s ≤20 s w 3/3 ślepych c01/c02/c03), B, C (breach=0;
    REFUSE per gałąź wpis; REFUSE(POS) ⇒ stop_now).

Użycie: akw_analyze.py <OUTDIR> → <OUTDIR>/akw_summary.json + print JSON.
"""
import bisect
import json
import math
import os
import sys

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, ROOT)


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
    arm = (man or {}).get("akw_arm") or ("V2" if os.path.exists(os.path.join(outdir, "percep_feed.jsonl")) else "B")
    trace = rows(os.path.join(outdir, "trace.jsonl"))
    demo = rows(os.path.join(outdir, "demo.jsonl"))
    feed = rows(os.path.join(outdir, "percep_feed.jsonl"))
    gti = rows(os.path.join(outdir, "gt_intruder.jsonl"))
    evs = [r for r in trace if r.get("ev")]

    # sędzia pełny (FROZEN przez judge_boot) — t_entry_s per epizod
    try:
        from bench.campaign_analyze import judge_boot
        judged = {j["episode_id"]: j for j in judge_boot(outdir)}
    except Exception as e:
        judged = {}
        print(f"[akw_analyze] judge_boot niedostępny: {e}", file=sys.stderr)

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

    # own pos — interpolacja z demo
    owns = sorted((d["t_sim"], d["own_pos_ned"]) for d in demo)
    own_t = [o[0] for o in owns]

    def own_at(t):
        if not own_t or t < own_t[0] or t > own_t[-1]:
            return None
        i = bisect.bisect_right(own_t, t)
        i = max(1, min(i, len(owns) - 1))
        a = (t - own_t[i - 1]) / (own_t[i] - own_t[i - 1]) if own_t[i] > own_t[i - 1] else 0
        return [owns[i - 1][1][k] + a * (owns[i][1][k] - owns[i - 1][1][k]) for k in range(3)]

    # świeże próbki feedu (do klasyfikacji ENTRY F1)
    fresh_rows = [(r["t_frame"], r) for r in feed
                  if r.get("fresh") and r.get("trk_pos_ned") and "t_frame" in r]
    fresh_t = [t for t, _ in fresh_rows]

    def entry_class(t):
        g = gt_at(t)
        if g is None:
            return "F2_poza_oknem_GT"
        i = bisect.bisect_left(fresh_t, t - 0.5)
        while i < len(fresh_t) and fresh_t[i] <= t + 0.5:
            if math.dist(fresh_rows[i][1]["trk_pos_ned"], gt_at(fresh_t[i]) or g) < 3.0:
                return "F1_cel"
            i += 1
        return "F3_kandydat_tla"

    out_eps = []
    stop_now = False
    man_eps = {e["episode_id"]: e for e in (man or {}).get("episodes", [])}
    for eid, w in sorted(wins.items()):
        me = man_eps.get(eid, {})
        dd = dep.get(eid, [])
        errs_cons = []
        for d in dd:
            g = gt_at(d["t_sim"])
            if g is not None and d.get("track_valid") and d.get("trk_pos_ned"):
                errs_cons.append(math.dist(d["trk_pos_ned"], g))
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
        entry_events = []
        if arm == "V2":
            fw = [r for r in feed if "t_frame" in r and w["lo"] <= r["t_frame"] <= w["hi"]]
            f30 = [r for r in fw if r["t_frame"] <= w["lo"] + 30.0]
            nf30 = sum(1 for r in f30 if r.get("fresh"))
            for r in fw:
                if r.get("ev") == "ENTRY":
                    entry_events.append({"t_frame": r["t_frame"],
                                         "t_rel": round(r["t_frame"] - w["lo"], 3),
                                         "klasa": entry_class(r["t_frame"])})
            v2 = {"n_frames": len(fw), "n_fresh": sum(1 for r in fw if r.get("fresh")),
                  "n_feed_expire": sum(1 for r in fw if r.get("ev") == "FEED_EXPIRE"),
                  "n_entry": len(entry_events),
                  "alive_30s": {"n_frames_30s": len(f30), "n_fresh_30s": nf30,
                                "alive": bool(nf30 >= 1 or len(f30) >= 10)}}
        alive = (v2["alive_30s"]["alive"] if v2 else True)
        valid_v2p = bool(me.get("valid_V2p"))

        # --- AKW: skan z demo (phase hold/track) ---
        t_first_track = None
        n_hold = 0
        hold_runs = 0
        reacq = 0
        osc5 = 0
        prev_hold = None
        for d in dd:
            is_hold = (d.get("phase") == "hold")
            if is_hold:
                n_hold += 1
                if prev_hold is False and t_first_track is not None \
                        and d["t_sim"] - t_first_track <= 5.0:
                    osc5 += 1
            if is_hold and prev_hold in (None, False):
                hold_runs += 1
            if prev_hold is True and not is_hold:
                reacq += 1
            if not is_hold and t_first_track is None and d.get("track_valid"):
                t_first_track = d["t_sim"]
            prev_hold = is_hold
        jd = judged.get(eid, {})
        OMEGA, DWELL = 30.0, 2.0
        t_first_fresh_rel = None
        if arm == "V2":
            for tfr, _r in fresh_rows:
                if w["lo"] <= tfr <= w["hi"]:
                    t_first_fresh_rel = round(tfr - w["lo"], 3)
                    break
        def _deg(t_rel):
            return round(OMEGA * max(0.0, t_rel - DWELL), 1) if t_rel is not None else None
        akw = {"t_entry_s": jd.get("t_entry_s"),
               "fail_reasons": jd.get("fail_reasons"),
               "t_first_track_rel": (round(t_first_track - w["lo"], 3)
                                     if t_first_track is not None else None),
               "t_first_fresh_rel": t_first_fresh_rel,
               "deg_skanu_do_pierwszego_boxu": _deg(t_first_fresh_rel),
               "deg_skanu_do_entry": _deg(entry_events[0]["t_rel"] if entry_events else None),
               "frac_hold": round(n_hold / len(dd), 4) if dd else None,
               "n_hold_runs": hold_runs, "n_reacquisitions": reacq,
               "osc_track_to_hold_w_5s_po_akwizycji": osc5,
               "entry_events": entry_events}

        ep = {
            "episode_id": eid, "scenario_id": w["sid"],
            "valid_V2p": valid_v2p, "alive_feed": alive,
            "valid_final": bool(valid_v2p and alive),
            "success_D6": bool(me.get("success_D6")),
            "d_min_m": me.get("d_min_m"),
            "refuse_count": me.get("refuse_count", 0), "breach": bool(me.get("breach")),
            "n_deep_stall": me.get("n_deep_stall"), "longest_stall_s": me.get("longest_stall_s"),
            "dsim_dwall": me.get("dsim_dwall"),
            "akw": akw,
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

    # bramka B boot-level (verbatim DET S3): kadencja z t_frame; E2E z client_e2e_full
    tf = sorted(r["t_frame"] for r in feed if "t_frame" in r)
    dts = [b - a for a, b in zip(tf, tf[1:]) if b > a]
    hz_p50 = round(1.0 / pct(dts, 0.5), 2) if dts else None
    e2e = rows(os.path.join(outdir, "client_e2e_full.jsonl")) or rows(os.path.join(outdir, "client_e2e.jsonl"))
    lat = [r["e2e_s"] for r in e2e if r.get("e2e_s") is not None and r["e2e_s"] >= 0]
    e2e_p95 = round(pct(lat, 0.95), 4) if lat else None
    gate_b = {"kadencja_przetwarzania_hz_p50": hz_p50,
              "PASS_kadencja": bool(hz_p50 is not None and hz_p50 >= 8.0),
              "e2e_p95_s": e2e_p95,
              "PASS_e2e": bool(e2e_p95 is not None and e2e_p95 <= 0.25),
              "n_frames": len(feed), "n_e2e": len(lat)} if arm == "V2" else None

    # REFUSE z trace per gałąź
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

    # sanity profilu w locie: yaw pojazdu z boot.ulg (opisowe, bez progu)
    yaw_sanity = None
    ulg_path = os.path.join(outdir, "boot.ulg")
    if os.path.exists(ulg_path):
        try:
            from pyulog import ULog
            u = ULog(ulg_path, ["vehicle_attitude"])
            d = u.get_dataset("vehicle_attitude")
            ts = d.data["timestamp"] / 1e6
            q0, q1, q2, q3 = (d.data["q[0]"], d.data["q[1]"], d.data["q[2]"], d.data["q[3]"])
            yaws = [math.atan2(2.0 * (w_ * z_ + x_ * y_), 1.0 - 2.0 * (y_ * y_ + z_ * z_))
                    for w_, x_, y_, z_ in zip(q0, q1, q2, q3)]
            # unwrap + rate
            uw = [yaws[0]]
            for y in yaws[1:]:
                dy = math.atan2(math.sin(y - uw[-1]), math.cos(y - uw[-1]))
                uw.append(uw[-1] + dy)
            rates = []
            for i in range(1, len(uw)):
                dt = ts[i] - ts[i - 1]
                if dt > 1e-4:
                    rates.append((math.degrees(uw[i] - uw[i - 1]) / dt, dt))
            rot = [(abs(r), dt) for r, dt in rates if 5.0 <= abs(r) <= 100.0]
            t_rot = sum(dt for _, dt in rot)
            t_band = sum(dt for r, dt in rot if 25.0 <= r <= 35.0)
            swept = sum(r * dt for r, dt in rot)
            rvals = sorted(r for r, _ in rot)
            yaw_sanity = {"n_att": len(uw),
                          "p50_abs_rate_rot_dps": (round(rvals[len(rvals) // 2], 1) if rvals else None),
                          "frac_czasu_rotacji_w_25_35": (round(t_band / t_rot, 3) if t_rot > 0 else None),
                          "t_rotacji_s": round(t_rot, 1),
                          "suma_omiecionych_deg": round(swept, 0)}
        except Exception as e:
            yaw_sanity = {"error": str(e)}

    # smoke_gates (PRE_AKW §4) — tylko dla zestawu c00_s01…c03_s01
    smoke = None
    sids = sorted(e["scenario_id"] for e in out_eps)
    if sids == ["c00_s01", "c01_s01", "c02_s01", "c03_s01"]:
        blind = [e for e in out_eps if e["scenario_id"] in ("c01_s01", "c02_s01", "c03_s01")]
        a_detail = [{"scenario_id": e["scenario_id"],
                     "t_entry_s": e["akw"]["t_entry_s"],
                     "entry_le_20": bool(e["akw"]["t_entry_s"] is not None
                                         and e["akw"]["t_entry_s"] <= 20.0)} for e in blind]
        ctrl = next((e for e in out_eps if e["scenario_id"] == "c00_s01"), None)
        smoke = {"A_entry_3z3_le20s": {"detail": a_detail,
                                       "n_pass": sum(1 for x in a_detail if x["entry_le_20"]),
                                       "PASS": all(x["entry_le_20"] for x in a_detail) and len(a_detail) == 3},
                 "B_runtime": gate_b,
                 "C_sbezp": {"breach_events": len(breach_evs),
                             "refuse_branches": branches,
                             "PASS": len(breach_evs) == 0 and not any("POS" in k.upper() for k in branches)},
                 "kontrolny_c00": {"success_D6": ctrl["success_D6"] if ctrl else None,
                                   "t_entry_s": ctrl["akw"]["t_entry_s"] if ctrl else None}}

    out = {"outdir": outdir, "akw_arm": arm,
           "akw_round": (man or {}).get("akw_round"),
           "controller": (man or {}).get("controller"),
           "controller_sha": ((man or {}).get("controller_sha") or "")[:16],
           "rc": (man or {}).get("rc"), "feed_sha": (man or {}).get("feed_sha"),
           "weights_sha": ((man or {}).get("weights_sha") or "")[:16],
           "n_episodes": len(out_eps),
           "n_valid_final": sum(1 for e in out_eps if e["valid_final"]),
           "episodes": out_eps,
           "gate_b_runtime": gate_b,
           "yaw_sanity_ulog": yaw_sanity,
           "s_bezp": {"breach_events": len(breach_evs), "refuse_events": len(refuse_evs),
                      "refuse_branches": branches,
                      "refuse_detail": [{k: r.get(k) for k in ("reason", "r_est", "t_rel")}
                                        for r in refuse_evs]},
           "smoke_gates": smoke,
           "stop_now": stop_now,
           "missing_manifest": man is None}
    json.dump(out, open(os.path.join(outdir, "akw_summary.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
