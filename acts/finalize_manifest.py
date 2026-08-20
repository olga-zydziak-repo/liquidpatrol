#!/usr/bin/env python3
"""acts/finalize_manifest.py — domknięcie ANEKS-H w manifeście PO biegu (dla sędziego `79b1e936`).

Manifest jest emitowany PO-arm (przed danymi biegu) z `aneks_h` = placeholder (None). Sędzia
(`_aneks_h`) wymaga wypełnionych: headless ∧ rtf_start/rtf_end∈[0.97,1.03] ∧ timejump=0 ∧
ekf_health_hits=0 ∧ world_hash_matches. Ten finalizer wypełnia je z ARTEFAKTÓW biegu — krok, który
w B4 (rehearsal_online_1, A1 VALID 5/5) był wykonywany osobno.

METODA rtf = 0.05 / stall_dist.p50 (kadencja pętli osłony @20 Hz; TICK_NOMINAL=0.05 s) — IDENTYCZNA
jak B4 (`results/demo/rehearsal/A1/rehearsal_online_1/manifest.json`: p50 0.0504 → 0.992). Trzymamy tę
samą metodę, bo sędzia jest FROZEN i był kalibrowany tym wejściem. ANEKS_D7: rygor sim-RTF (segmenty,
Δsim/Δwall) żyje w `habitat_gate.py`; tu domykamy tylko coarse boot-sanity sędziego. DODATKOWO stampujemy
`rtf_gz_claim_*` z realnie próbkowanego gz-RTF (habitat.json) — prowieniencja (B4 miał „gz-RTF nie próbkowano").

Uruchom: python3 -m acts.finalize_manifest <RUNDIR> [--world-sdf worlds/world_demo_A1.sdf]
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, sys

TICK_NOMINAL = 0.05   # 20 Hz pętla decyzji osłony (r01/config TICK_HZ) — jak B4


def _read_int(path, default=1):
    try:
        return int(open(path).read().strip() or default)
    except Exception:
        return default


def _stall_p50(run_dir):
    """stall_dist.p50 z SCENARIO_RESULT (trace ostatnia linia) albo act.log RESULT."""
    tr = os.path.join(run_dir, "trace.jsonl")
    if os.path.exists(tr):
        last = None
        for ln in open(tr):
            if '"SCENARIO_RESULT"' in ln:
                last = ln
        if last:
            d = json.loads(last)["SCENARIO_RESULT"]
            sd = d.get("stall_dist_R3") or {}
            if sd.get("p50"):
                return float(sd["p50"])
    al = os.path.join(run_dir, "act.log")
    if os.path.exists(al):
        m = re.search(r'"stall_dist_R3":\s*\{[^}]*"p50":\s*([0-9.]+)', open(al).read())
        if m:
            return float(m.group(1))
    # A3 (r03): brak stall_dist_R3 → kadencja ticków z trace (mono delty rekordów "t":"tick")
    if os.path.exists(tr):
        ms = []
        for ln in open(tr):
            if '"t": "tick"' in ln:
                try:
                    ms.append(json.loads(ln)["mono"])
                except Exception:
                    pass
        d = sorted(b - a for a, b in zip(ms, ms[1:]) if 0 < b - a < 1.0)
        if len(d) >= 10:
            return d[len(d) // 2]   # p50 dt ticka
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--world-sdf", default=None, help="ścieżka frozen world SDF do porównania hash")
    args = ap.parse_args()
    mpath = os.path.join(args.run_dir, "manifest.json")
    if not os.path.exists(mpath):
        print(f"[finalize] BRAK manifest.json w {args.run_dir}", file=sys.stderr); sys.exit(2)
    m = json.load(open(mpath))
    a = dict(m.get("aneks_h") or {})

    # headless (headless_proof.txt: GUI_PROCS=[brak])
    hp = os.path.join(args.run_dir, "headless_proof.txt")
    headless = os.path.exists(hp) and ("brak" in open(hp).read().lower())
    a["headless"] = bool(headless)

    # timejump = pre + post ; ekf_health_hits
    tj = _read_int(os.path.join(args.run_dir, "timejump_pre.txt"), 0) + \
         _read_int(os.path.join(args.run_dir, "timejump_post.txt"), 0)
    a["timejump"] = tj
    a["ekf_health_hits"] = _read_int(os.path.join(args.run_dir, "ekf_health_hits.txt"), 1)

    # rtf z tick-period (metoda B4)
    p50 = _stall_p50(args.run_dir)
    if p50:
        rtf = round(TICK_NOMINAL / p50, 3)
        a["rtf_start"] = rtf; a["rtf_end"] = rtf
        a["rtf_method"] = f"TICK_NOMINAL(0.05)/stall_dist.p50({p50}) — jak B4"
    else:
        a["rtf_start"] = None; a["rtf_end"] = None
        a["rtf_method"] = "stall_dist.p50 niedostępne"

    # world_hash_matches: sha256(frozen world SDF) == manifest.world_hash
    wsdf = args.world_sdf or m.get("world_sdf")
    wh_match = False
    if wsdf and os.path.exists(wsdf) and m.get("world_hash"):
        h = hashlib.sha256(open(wsdf, "rb").read()).hexdigest()
        wh_match = (h == m["world_hash"])
        a["world_hash_actual"] = h
    a["world_hash_matches"] = bool(wh_match)

    # DODATKOWO (ANEKS_D7 prowieniencja): realnie próbkowany gz-RTF z habitat.json (segment roszczeń)
    hb = os.path.join(args.run_dir, "habitat.json")
    if os.path.exists(hb):
        H = json.load(open(hb))
        claim = [s for s in H.get("segments", []) if s.get("kind") == "claim"]
        if claim:
            a["rtf_gz_claim_median"] = [s["metrics"].get("median_rtf") for s in claim]
            a["rtf_gz_claim_dsim_dwall"] = [s["metrics"].get("dsim_dwall") for s in claim]
        a["habitat_verdict"] = H.get("verdict")

    m["aneks_h"] = a
    json.dump(m, open(mpath, "w"), indent=2, ensure_ascii=False)
    print(f"[finalize] {args.run_dir}: headless={a['headless']} rtf={a['rtf_start']} "
          f"timejump={a['timejump']} ekf_hits={a['ekf_health_hits']} world_hash_matches={a['world_hash_matches']}")
    # zwróć niezerowo jeśli ANEKS-H by nie przeszedł (diagnostyka)
    ok = (a["headless"] and a["rtf_start"] is not None and 0.97 <= a["rtf_start"] <= 1.03
          and a["timejump"] == 0 and a["ekf_health_hits"] == 0 and a["world_hash_matches"])
    sys.exit(0 if ok else 3)


if __name__ == "__main__":
    main()
