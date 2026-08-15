#!/usr/bin/env python3
"""results/R02/mti/REGATE/posthoc.py — ANALIZA POST-HOC z trace REGATE (NIE bramka).

Etykieta: **ANALIZA POST-HOC** — nie zmienia kryterium, karmi D1/D2/D4 z per-frame trace.
Wejście: results/R02/mti/REGATE/<boot>/{trace.jsonl,result.json}. Wyjście: REGATE/posthoc.json.

D1 — atrybucja koniunktów per dystans (który człon zawodził) + hipoteza pościgu:
     korelacja mti_ok z pozornym ruchem celu |Δ(cx,cy)|/klatkę i manewrem platformy (|v| z lpos).
D2 — tabela K przez gate_sim na REALNYCH śladach bramy per-tick (informacyjnie).
D4 — MTI-P: rezydualna separacja (bearing z cx,cy + baseline z lpos) cel vs tło (informacyjnie).
"""
import json
import math
import os
import statistics as st
import sys

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, os.path.join(ROOT, "results/R02/mti/DIAG"))
from gate_sim import replay_gate  # noqa: E402

REGATE = os.path.join(ROOT, "results/R02/mti/REGATE")
# intrinsics mono_cam (PRE_MTI R1): fx=fy=270, cx=320, cy=240, 640x480
FX = FY = 270.0
CX0, CY0 = 320.0, 240.0
W, H = 640.0, 480.0


def load_boot(boot):
    d = os.path.join(REGATE, boot)
    tr = os.path.join(d, "trace.jsonl")
    rj = os.path.join(d, "result.json")
    if not (os.path.exists(tr) and os.path.exists(rj)):
        return None
    recs = [json.loads(l) for l in open(tr) if l.strip()]
    res = json.load(open(rj))
    return {"boot": boot, "recs": recs, "result": res}


def bearing(cx, cy):
    """(az, el) rad z znormalizowanego środka boxa (proste intrinsics)."""
    px, py = cx * W, cy * H
    return math.atan2((px - CX0), FX), math.atan2((py - CY0), FY)


def d1_attribution(recs):
    """Per faza sweep: dekompozycja porażki bramy + korelacja mti_ok↔ruch pozorny/manewr."""
    out = {}
    phases = sorted({r["phase"] for r in recs if r["phase"] and r["phase"].startswith("sweep")})
    for ph in phases:
        rr = [r for r in recs if r["phase"] == ph]
        n = len(rr)
        if n == 0:
            continue
        n_box = sum(1 for r in rr if r["has_box"])
        # per-tick: który człon blokował gate (wśród klatek z boxem, gate=False)
        fail_central = sum(1 for r in rr if r["has_box"] and not r["central"])
        fail_mti = sum(1 for r in rr if r["has_box"] and r["central"] and not r["mti_ok"])
        gate_on = sum(1 for r in rr if r["gate"])
        # ruch pozorny celu |Δ(cx,cy)| między kolejnymi klatkami z boxem
        motion = []
        prev = None
        for r in rr:
            if r["has_box"] and r["cx"] is not None:
                if prev is not None:
                    motion.append(math.hypot(r["cx"] - prev[0], r["cy"] - prev[1]))
                prev = (r["cx"], r["cy"])
        # manewr platformy |v| z lpos
        vlat = []
        for r in rr:
            lp = r.get("lpos")
            if lp and lp.get("xy_valid"):
                vlat.append(math.hypot(lp["vx"], lp["vy"]))
        # korelacja mti_ok (0/1) vs ruch pozorny na klatce (proxy: |Δcx,cy| dla par kolejnych)
        pairs = []
        prev = None
        for r in rr:
            if r["has_box"] and r["cx"] is not None:
                if prev is not None:
                    dm = math.hypot(r["cx"] - prev[1], r["cy"] - prev[2])
                    pairs.append((1 if r["mti_ok"] else 0, dm))
                prev = (r["mti_ok"], r["cx"], r["cy"])
        mti_hit_motion = [dm for (m, dm) in pairs if m == 1]
        mti_miss_motion = [dm for (m, dm) in pairs if m == 0]
        out[ph] = {
            "n_ticks": n, "n_box": n_box, "gate_on": gate_on,
            "fail_central_frames": fail_central, "fail_mti_frames": fail_mti,
            "limiting_conjunct": ("mti" if fail_mti >= fail_central else "central") if (n_box - gate_on) > 0 else "none",
            "apparent_motion_median": round(st.median(motion), 5) if motion else None,
            "apparent_motion_q90": round(sorted(motion)[int(0.9 * len(motion))], 5) if len(motion) > 5 else None,
            "platform_vlat_median": round(st.median(vlat), 4) if vlat else None,
            "mti_hit_apparent_motion_median": round(st.median(mti_hit_motion), 5) if mti_hit_motion else None,
            "mti_miss_apparent_motion_median": round(st.median(mti_miss_motion), 5) if mti_miss_motion else None,
            "n_hit_pairs": len(mti_hit_motion), "n_miss_pairs": len(mti_miss_motion),
        }
    return out


def d2_ktable(recs):
    """Tabela K (gate_sim) na REALNYCH śladach bramy per-tick, per faza sweep."""
    out = {}
    phases = sorted({r["phase"] for r in recs if r["phase"] and r["phase"].startswith("sweep")})
    for ph in phases:
        gate_seq = [1 if r["gate"] else 0 for r in recs if r["phase"] == ph]
        row = {}
        for K in range(2, 8):
            # consecutive (obecna) vs window m-of-M (M=K+2) — informacyjnie
            cons = replay_gate(gate_seq, mode="consecutive", K=K)
            win = replay_gate(gate_seq, mode="window", K=K, M=K + 2)
            row[f"K{K}"] = {
                "consec_entry": cons.entry_tick is not None,
                "consec_cov_post": cons.locked_coverage_post_entry,
                "window_entry": win.entry_tick is not None,
                "window_cov_post": win.locked_coverage_post_entry,
            }
        row["gate_coverage_raw"] = round(sum(gate_seq) / len(gate_seq), 4) if gate_seq else None
        out[ph] = row
    return out


def d4_mtip(recs):
    """MTI-P (informacyjnie): baseline platformy per faza + rozrzut bearingu celu (separacja stat/ruch)."""
    out = {}
    phases = sorted({r["phase"] for r in recs if r["phase"] and r["phase"].startswith("sweep")})
    for ph in phases:
        rr = [r for r in recs if r["phase"] == ph and r["has_box"] and r["cx"] is not None]
        pos = [(r["lpos"]["x"], r["lpos"]["y"], r["lpos"]["z"]) for r in rr
               if r.get("lpos") and r["lpos"].get("xy_valid")]
        # baseline B_perp ~ rozpiętość pozycji platformy w płaszczyźnie
        b_perp = None
        if len(pos) >= 2:
            xs = [p[0] for p in pos]; ys = [p[1] for p in pos]
            b_perp = round(math.hypot(max(xs) - min(xs), max(ys) - min(ys)), 3)
        az = [bearing(r["cx"], r["cy"])[0] for r in rr]
        el = [bearing(r["cx"], r["cy"])[1] for r in rr]
        out[ph] = {
            "n_box_ticks": len(rr),
            "baseline_B_perp_m": b_perp,
            "bearing_az_spread_deg": round(math.degrees(max(az) - min(az)), 3) if len(az) > 1 else None,
            "bearing_el_spread_deg": round(math.degrees(max(el) - min(el)), 3) if len(el) > 1 else None,
            "note": "MTI-P pełny (rezydual triangulacji) wymaga sync bearing↔poza per klatka; "
                    "tu dostępność geometrii (baseline) + rozrzut bearingu jako wykonalność.",
            "feasible": bool(b_perp and b_perp > 0.5),
        }
    return out


def main():
    boots = [b for b in sorted(os.listdir(REGATE))
             if os.path.isdir(os.path.join(REGATE, b)) and load_boot(b)]
    report = {"step": "REGATE post-hoc (D1/D2/D4)", "label": "ANALIZA POST-HOC ≠ bramka",
              "boots": boots, "per_boot": {}}
    for b in boots:
        data = load_boot(b)
        recs = data["recs"]
        report["per_boot"][b] = {
            "n_records": len(recs),
            "trace_complete": data["result"].get("trace", {}).get("complete"),
            "D1_attribution": d1_attribution(recs),
            "D2_ktable": d2_ktable(recs),
            "D4_mtip": d4_mtip(recs),
        }
    outp = os.path.join(REGATE, "posthoc.json")
    json.dump(report, open(outp, "w"), indent=2, ensure_ascii=False)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\n[posthoc] zapisano {outp}")


if __name__ == "__main__":
    main()
