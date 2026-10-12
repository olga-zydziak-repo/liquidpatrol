#!/usr/bin/env python3
"""results/FANTOM_RECON/tools/fantom_recon.py — recon pozycji FANTOM-START
(PROMPT_FANTOM_S0 §R). ZERO lotów, zero edycji istniejących; czyta artefakty
kampanii AKW S3 (results/AKW/camp), DET S4 (results/DET/camp) i smoke S2.

Tryby:
  r1   : szczegół 6 fantomów — źródło tracku przy t0 (spawn-świata / koniec
         poprzedniego epizodu), czasy freshów wokół t0, czas expire.
  r2   : zasięg na WSZYSTKICH epizodach V2 AKW (48) + DET (48) + ramię B:
         lock na starcie (track_valid na 1. ticku), fantom (d(trk,GT_spawn)>5 m)
         vs real, wynik epizodu; klasy: fantom-FAIL / fantom-PASS (nieszkodliwy) /
         czysty-FAIL / czysty-PASS. + c00 smoke S2 (resmoke_r1_V2).
  r3   : replay czystego startu na 6 fantomach — harmonogram profilu II od ψ=0
         (reset) vs GT: kiedy cel w stożku ENTRY podczas stare; przewidywana
         akwizycja; empiryka sióstr (ta sama komórka, inne ziarna) i DET.
Wyjścia: results/FANTOM_RECON/{r1_phantom.json, r2_scope.json, r3_cleanstart.json}.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import glob
import sys

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, os.path.join(ROOT, "results/REAKW_RECON/tools"))
from reakw_recon import jload, episode_windows, GT, ang_diff_deg   # narzędzie recon (READ-ONLY)

CAMP_AKW = os.path.join(ROOT, "results/AKW/camp")
CAMP_DET = os.path.join(ROOT, "results/DET/camp")
OUTD = os.path.join(ROOT, "results/FANTOM_RECON")

SIX = {"c01_s01": "r1_V2", "c05_s02": "r5_V2", "c06_s04": "r11_V2",
       "c08_s02": "r6_V2", "c08_s03": "r9_V2", "c08_s04": "r12_V2"}
HALF_CONE = 86.9 / 2
STEP_T = 40.0 / 60.0
STARE_S = 1.2
DWELL_S = 2.0
CYCLE = STEP_T + STARE_S
D_PHANTOM = 5.0            # [m] próg: trk@t0 dalej niż to od GT spawn = fantom


def demo_ticks(d):
    return [r for r in jload(os.path.join(d, "demo.jsonl"))
            if "tick" in r and "own_pos_ned" in r]


def first_tick_state(ticks, sid):
    for r in ticks:
        if r["scenario_id"] == sid:
            return r
    return None


def scan_heading_deg(t_rel_from_hold):
    """ψ komendy profilu II [deg, CCW od 0] po t_rel od wejścia w hold (ψ_last=0)."""
    if t_rel_from_hold <= DWELL_S:
        return 0.0
    tc = t_rel_from_hold - DWELL_S
    n = int(tc // CYCLE)
    ph = tc - n * CYCLE
    return (n * 40.0 + min(ph, STEP_T) * 60.0)


def cmd_r1():
    out = []
    for sid, boot in SIX.items():
        d = os.path.join(CAMP_AKW, boot)
        wins = episode_windows(d)
        lo, hi = wins[sid]
        order = sorted(wins.items(), key=lambda kv: kv[1][0])
        idx = [k for k, _ in order].index(sid)
        prev_sid = order[idx - 1][0] if idx > 0 else None
        gt = GT(d)
        prev_end = gt.pos(wins[prev_sid][1] - 0.2) if prev_sid else None
        spawn = gt.pos(lo + 0.1)
        pf = [r for r in jload(os.path.join(d, "percep_feed.jsonl"))
              if r.get("t_frame") and lo - 60 <= r["t_frame"] <= lo + 6]
        fresh = [r for r in pf if r.get("fresh")]
        before = [r for r in fresh if r["t_frame"] < lo + 0.05]
        lb = before[-1] if before else None

        def d2(p, q):
            return round(math.dist(p[:2], q[:2]), 1) if (p and q) else None
        tp = lb["trk_pos_ned"] if lb else None
        out.append({
            "sid": sid, "boot": boot, "ep_index_w_boocie": idx, "prev_sid": prev_sid,
            "t0": round(lo, 2),
            "ostatni_fresh_przed_t0_rel": round(lb["t_frame"] - lo, 2) if lb else None,
            "gate": lb.get("gate") if lb else None,
            "trk_przy_t0": [round(x, 1) for x in tp] if tp else None,
            "d_trk_spawn": d2(tp, spawn), "d_trk_prev_end": d2(tp, prev_end),
            "d_trk_staging_swiata": d2(tp, [-1.0, 6.6, 0]),
            "n_fresh_t0m10_t0": len([r for r in before if r["t_frame"] >= lo - 10]),
            "n_fresh_po_t0_6s": len([r for r in fresh if r["t_frame"] >= lo + 0.05]),
            "klasa": ("spawn-świata (pierwszy epizod bootu)" if idx == 0
                      else "koniec poprzedniego epizodu"),
        })
    json.dump(out, open(os.path.join(OUTD, "r1_phantom.json"), "w"), indent=1)
    print(json.dumps(out, indent=1, ensure_ascii=False))


def scope_for(campdir, arm_glob, summary_name, name_re=None):
    import re
    rows = []
    for d in sorted(glob.glob(os.path.join(campdir, arm_glob))):
        if not os.path.isdir(d):
            continue
        if name_re and not re.match(name_re, os.path.basename(d)):
            continue
        sp = os.path.join(d, summary_name)
        if not os.path.exists(sp):
            continue
        s = json.load(open(sp))
        wins = episode_windows(d)
        gt = GT(d)
        ticks = demo_ticks(d)
        for e in s["episodes"]:
            sid = e["scenario_id"]
            if sid not in wins:
                continue
            lo, hi = wins[sid]
            ft = first_tick_state(ticks, sid)
            if ft is None:
                continue
            spawn = gt.pos(lo + 0.1)
            lock = bool(ft.get("track_valid"))
            dsp = (round(math.dist(ft["trk_pos_ned"][:2], spawn[:2]), 1)
                   if lock and spawn else None)
            fant = bool(lock and dsp is not None and dsp > D_PHANTOM)
            zywy = bool(fant and ft.get("track_age_s", 9) <= 1.0)   # konsument go śledzi
            # los fantomu ŻYWEGO: PRZECHWYT (trk doskakuje do GT <5 m bez utraty) czy EXPIRE;
            # pętla od lo+0.2 (GT.pos interpoluje przez lukę teleportu — brzeg wykluczony)
            fate = "martwy@t0 (age>1 — konsument w hold od ticku 0)" if (fant and not zywy) else None
            t_fate = None
            if zywy:
                ep_ticks = [r for r in ticks if r["scenario_id"] == sid
                            and r["t_sim"] >= lo + 0.2]
                for r in ep_ticks:
                    if not r.get("track_valid") or r.get("track_age_s", 9) > 1.0:
                        fate, t_fate = "expire/utrata", round(r["t_sim"] - lo, 2)
                        break
                    g = gt.pos(r["t_sim"])
                    if g and math.dist(r["trk_pos_ned"][:2], g[:2]) <= D_PHANTOM:
                        fate, t_fate = "przechwyt", round(r["t_sim"] - lo, 2)
                        break
            rows.append({"boot": os.path.basename(d), "sid": sid,
                         "lock_at_start": lock, "age_at_start": ft.get("track_age_s"),
                         "d_trk_spawn": dsp, "fantom": fant,
                         "los_fantomu": fate, "t_losu_s": t_fate,
                         "valid": e.get("valid_final"), "D6": e.get("success_D6")})
    return rows


def cmd_r2():
    res = {}
    akw = scope_for(CAMP_AKW, "r*_V2", "akw_summary.json", r"^r\d+_V2r?$")
    det = scope_for(CAMP_DET, "r*_V2", "detS4_summary.json", r"^r\d+_V2r?$")
    bb = scope_for(CAMP_AKW, "r*_B", "akw_summary.json", r"^r\d+_Br?$")
    smoke = scope_for(CAMP_AKW, "resmoke_r1_V2", "akw_summary.json")

    def agg(rows, label):
        lock = [r for r in rows if r["lock_at_start"]]
        fant = [r for r in rows if r["fantom"]]
        return {"label": label, "n": len(rows),
                "lock_at_start": len(lock), "fantom_at_start": len(fant),
                "fantom_FAIL": sorted(r["sid"] for r in fant if r["valid"] and not r["D6"]),
                "fantom_PASS": sorted(r["sid"] for r in fant if r["valid"] and r["D6"]),
                "lock_real_at_start": sorted(f'{r["sid"]}' for r in lock if not r["fantom"]),
                "czysty_FAIL": sorted(r["sid"] for r in rows
                                      if not r["fantom"] and r["valid"] and not r["D6"])}
    res["AKW_V2"] = agg(akw, "AKW S3 V2 (48 ep, pierwsza ważna próba w bootach)")
    res["DET_V2"] = agg(det, "DET S4 V2 (48 ep)")
    res["AKW_B"] = agg(bb, "AKW S3 B (48 ep)")
    res["smoke_S2_c00"] = [r for r in smoke if r["sid"] == "c00_s01"]
    res["rows_AKW_V2"] = akw
    res["rows_DET_V2"] = det
    json.dump(res, open(os.path.join(OUTD, "r2_scope.json"), "w"), indent=1)
    for k in ("AKW_V2", "DET_V2", "AKW_B"):
        print(k, json.dumps(res[k], ensure_ascii=False, indent=1))
    print("smoke_S2_c00:", json.dumps(res["smoke_S2_c00"], ensure_ascii=False))


def cmd_r3():
    pairs = json.load(open(os.path.join(CAMP_AKW, "akw_pairs.json")))
    by_sid = {p["scenario_id"]: p for p in pairs["pairs"]}
    out = []
    for sid, boot in SIX.items():
        d = os.path.join(CAMP_AKW, boot)
        wins = episode_windows(d)
        lo, hi = wins[sid]
        gt = GT(d)
        ticks = [r for r in demo_ticks(d) if r["scenario_id"] == sid]
        own0 = ticks[0]["own_pos_ned"]
        # kontrfaktycznie: hold od t0 (ψ_last=0 po reset) — kiedy cel w stożku ±43.45°
        # wokół ψ(t) profilu II i nos w STARE (ω·dt=0)?
        t_acq = None
        t = 0.2
        while t < min(30.0, hi - lo):
            g = gt.pos(lo + t)
            if g is None:
                t += 0.1
                continue
            psi_cmd = scan_heading_deg(t)
            # czy w stare (dwell tez jest stare)?
            in_stare = (t <= DWELL_S) or (((t - DWELL_S) % CYCLE) >= STEP_T)
            az = math.degrees(math.atan2(g[1] - own0[1], g[0] - own0[0])) % 360
            derr = abs((az - psi_cmd + 180) % 360 - 180)
            if in_stare and derr <= HALF_CONE:
                # wymagaj 1.0 s ciaglego okna (MTI warmup+k=3 w szybkim; wolny ~1.2 s pelne stare)
                ok = True
                tt = t
                while tt < t + 1.0:
                    gg = gt.pos(lo + tt)
                    ps = scan_heading_deg(tt)
                    ins = (tt <= DWELL_S) or (((tt - DWELL_S) % CYCLE) >= STEP_T)
                    azz = math.degrees(math.atan2(gg[1] - own0[1], gg[0] - own0[0])) % 360
                    de = abs((azz - ps + 180) % 360 - 180)
                    if not (ins and de <= HALF_CONE):
                        ok = False
                        break
                    tt += 0.1
                if ok:
                    t_acq = round(t + 1.0, 1)
                    break
            t += 0.1
        # siostry: ta sama komorka, inne ziarna — wynik z kampanii
        cell = sid.split("_")[0]
        sisters = {p["scenario_id"]: p["V2_D6"] for p in pairs["pairs"]
                   if p["cell"] == cell and p["scenario_id"] != sid and p["common_valid"]}
        det_pairs = json.load(open(os.path.join(CAMP_DET, "detS4_pairs.json")))
        det_same = {p["scenario_id"]: p["V2_D6"] for p in det_pairs["pairs"]
                    if p["scenario_id"] == sid}
        out.append({"sid": sid, "boot": boot,
                    "przewidywana_akwizycja_czysty_start_s": t_acq,
                    "margines_do_tA23_s": (round(23 - t_acq, 1) if t_acq else None),
                    "slepota_obserwowana_s": None,   # z dir_replay (REAKW) — w raporcie
                    "siostry_tej_komorki_V2_D6": sisters,
                    "ten_sid_w_DET_V2_D6": det_same})
    json.dump(out, open(os.path.join(OUTD, "r3_cleanstart.json"), "w"), indent=1)
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    os.makedirs(OUTD, exist_ok=True)
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["r1", "r2", "r3"])
    a = ap.parse_args()
    {"r1": cmd_r1, "r2": cmd_r2, "r3": cmd_r3}[a.mode]()
