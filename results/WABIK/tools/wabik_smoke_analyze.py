#!/usr/bin/env python3
"""results/WABIK/tools/wabik_smoke_analyze.py — analiza SMOKE S1 (PROMPT_WABIK_S1 §1.6).

(b) KOTWICA CZYSTOŚCI: werdykt sędziego epizodu INTRUZA pełną literą (import
    analyze_boot z perc2_s2_analyze — sędzia FROZEN 8ec0fcfb, GT manifest,
    świadek OBOK) vs przebieg historyczny (c08_s01: S2-PERC2 d_min 6.854).
(c) TRACKER PRZY WABIKU W FOV (pierwszy taki pomiar w programie): per klatka
    percep_feed — stożek ±43.45° wokół yaw (own_q); azymuty do INTRUZA (GT
    manifest) i WABIKA (GT z wabik_motion.jsonl, ZOH): klatki wabik-w-stożku
    (w tym sam-w-stożku, bez intruza), boxy/mti/fresh w tych klatkach,
    PRZESKOKI tracka: ticki demo z track_valid, gdzie trk bliżej WABIKA niż
    intruza i ≤3 m od wabika (semantyka F1 na wabiku) — łącznie i w fazach
    werdyktowych (od t_entry sędziego).
Wyjście: results/WABIK/s1/<boot>/wabik_smoke.json + stdout.
Użycie: wabik_smoke_analyze.py <bootdir> <sid>
"""
import json
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
for p in (ROOT, os.path.join(ROOT, "results", "PERC2", "tools")):
    if p not in sys.path:
        sys.path.insert(0, p)
from perc2_s2_analyze import analyze_boot, iter_jsonl, interp as interp3
from bench import scenarios as S

HALF_CONE = 43.45
MAN = json.load(open(os.path.join(ROOT, "results", "BENCH", "scenario_manifest.json")))
SCEN = {e["scenario_id"]: e for e in MAN["episodes"]}


def yaw_of(q):
    w, x, y, z = q
    return math.degrees(math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z)))


def wrap(a):
    return (a + 180.0) % 360.0 - 180.0


def main():
    d, sid = sys.argv[1], sys.argv[2]
    rows_j = analyze_boot(d)
    kot = next(r for r in rows_j if r["sid"] == sid)
    # GT wabika (applied) z wabik_motion.jsonl
    wgt = [(r["t_sim"], r["ned"]) for r in iter_jsonl(os.path.join(d, "wabik_motion.jsonl"))
           if r.get("ned") and r.get("t_sim")]
    wgt.sort()
    t0 = None
    for r in iter_jsonl(os.path.join(d, "trace.jsonl")):
        if r.get("t") == "event" and r.get("ev") == "episode_start" and r.get("scenario_id") == sid:
            t0 = r["t0_sim"]
            break
    ep = SCEN[sid]
    # klatki percep: stożki
    n_cone_w = n_cone_w_alone = n_box_alone = n_mti_alone = n_fresh_alone = 0
    n_frames = 0
    for r in iter_jsonl(os.path.join(d, "percep_feed.jsonl")):
        t = r.get("t_frame")
        if t is None or not r.get("own_q") or t0 is None or not (t0 <= t <= t0 + 112):
            continue
        n_frames += 1
        yw = yaw_of(r["own_q"])
        op = r["own_pos_ned"]
        g = S.position_at(ep, max(0.0, t - t0))
        az_i = math.degrees(math.atan2(g[1] - op[1], g[0] - op[0]))
        in_i = abs(wrap(az_i - yw)) <= HALF_CONE
        pw = None
        if wgt:
            pw = interp3(wgt, t)
        in_w = False
        if pw is not None:
            az_w = math.degrees(math.atan2(pw[1] - op[1], pw[0] - op[0]))
            in_w = abs(wrap(az_w - yw)) <= HALF_CONE
        if in_w:
            n_cone_w += 1
            if not in_i:
                n_cone_w_alone += 1
                if r.get("box"):
                    n_box_alone += 1
                if r.get("mti_ok"):
                    n_mti_alone += 1
                if r.get("fresh"):
                    n_fresh_alone += 1
    # przeskoki tracka (demo)
    t_entry = kot["sedzia_D6_opisowo"]["t_entry_s"]
    n_valid = n_jump = n_jump_werd = 0
    for r in iter_jsonl(os.path.join(d, "demo.jsonl")):
        if r.get("scenario_id") != sid or not r.get("track_valid") or not r.get("trk_pos_ned"):
            continue
        t = r["t_sim"]
        trk = r["trk_pos_ned"]
        gi = S.position_at(ep, max(0.0, t - t0))
        d_i = math.hypot(trk[0] - gi[0], trk[1] - gi[1])
        pw = interp3(wgt, t) if wgt else None
        if pw is None:
            continue
        d_w = math.hypot(trk[0] - pw[0], trk[1] - pw[1])
        n_valid += 1
        if d_w < d_i and d_w <= 3.0:
            n_jump += 1
            if t_entry is not None and t - t0 >= t_entry:
                n_jump_werd += 1
    out = {"sid": sid,
           "kotwica_sedzia": kot["sedzia_D6_opisowo"] | {"swiadek": kot["swiadek_erratum"],
                                                         "t_acq_s": kot["t_acq_s"],
                                                         "kadencja_lotu": kot["kadencja_lotu"]},
           "historyczne_c08_s01": {"S2_PERC2_d_min": 6.854, "DEMOC_era_d_min": 6.877},
           "tracker_przy_wabiku": {"n_frames_epizod": n_frames,
                                   "n_wabik_w_stozku": n_cone_w,
                                   "n_wabik_SAM_w_stozku": n_cone_w_alone,
                                   "n_box_gdy_wabik_sam": n_box_alone,
                                   "n_mti_gdy_wabik_sam": n_mti_alone,
                                   "n_fresh_gdy_wabik_sam": n_fresh_alone},
           "przeskoki_tracka": {"n_tickow_valid": n_valid,
                                "n_trk_blizej_wabika_le3m": n_jump,
                                "w_fazach_werdyktowych_od_t_entry": n_jump_werd},
           "n_probek_gt_wabika": len(wgt)}
    json.dump(out, open(os.path.join(d, "wabik_smoke.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
