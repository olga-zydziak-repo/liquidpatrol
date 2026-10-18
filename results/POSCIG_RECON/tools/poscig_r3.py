#!/usr/bin/env python3
"""results/POSCIG_RECON/tools/poscig_r3.py — R3: charakterystyka korpusu demonstracji (ławka,
nauczyciel=orbit_executor) pod kątem pościgu. Skan results/BENCH/campaign/*/demo.jsonl:
per grupa v_intr (0 / 0.5 / 1.0): wiersze, fazy, pokrycie sytuacji pościgowej
(track_valid ∧ d_feed>10 m), profil |cmd_h| w tej sytuacji. Dedup per scenario_id:
pierwszy napotkany boot w porządku leksykalnym (duplikaty retry — skaza nazwana w raporcie).
Wynik: r3_corpus.json."""
import glob
import json
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUTDIR = os.path.join(ROOT, "results", "POSCIG_RECON")


def pct(xs, q):
    if not xs:
        return None
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(q * (len(xs) - 1))))]


def vgroup(sid):
    c = int(sid[1:3])
    return "0.0" if c < 4 else ("0.5" if c < 8 else "1.0")


def main():
    seen = set()
    G = {g: {"rows": 0, "episodes": 0, "phase": {}, "chase_rows": 0, "chase_spd": [],
             "band_rows": 0, "reentries": 0} for g in ("0.0", "0.5", "1.0")}
    for d in sorted(glob.glob(os.path.join(ROOT, "results", "BENCH", "campaign", "*", "demo.jsonl"))):
        cur_sid = None; skip = False; in_band_prev = False; was_out = False
        with open(d) as f:
            for line in f:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                sid = r["scenario_id"]
                if sid != cur_sid:
                    cur_sid = sid
                    skip = sid in seen
                    if not skip:
                        seen.add(sid)
                        G[vgroup(sid)]["episodes"] += 1
                    in_band_prev = False; was_out = False
                if skip:
                    continue
                g = G[vgroup(sid)]
                g["rows"] += 1
                ph = r["phase"]
                g["phase"][ph] = g["phase"].get(ph, 0) + 1
                own = r["own_pos_ned"]; trk = r["trk_pos_ned"]
                dh = math.hypot(trk[0] - own[0], trk[1] - own[1])
                valid = r["track_valid"]
                if valid and dh > 10.0:
                    g["chase_rows"] += 1
                    g["chase_spd"].append(math.hypot(r["cmd_v_ned"][0], r["cmd_v_ned"][1]))
                in_band = valid and 6.0 <= dh <= 10.0
                if in_band:
                    g["band_rows"] += 1
                    if was_out and in_band_prev is False:
                        g["reentries"] += 1
                if in_band_prev and not in_band:
                    was_out = True
                in_band_prev = in_band
    out = {}
    for gname, g in G.items():
        out[gname] = {
            "episodes": g["episodes"], "rows": g["rows"], "phase": g["phase"],
            "chase_rows": g["chase_rows"],
            "chase_frac": round(g["chase_rows"] / max(1, g["rows"]), 4),
            "chase_spd_p50": round(pct(g["chase_spd"], 0.5), 3) if g["chase_spd"] else None,
            "chase_spd_p90": round(pct(g["chase_spd"], 0.9), 3) if g["chase_spd"] else None,
            "band_rows": g["band_rows"], "reentries_do_pasma": g["reentries"],
        }
        print(gname, json.dumps(out[gname]))
    json.dump(out, open(os.path.join(OUTDIR, "r3_corpus.json"), "w"), indent=1)
    print("zapisano r3_corpus.json")


if __name__ == "__main__":
    main()
