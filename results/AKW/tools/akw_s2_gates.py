#!/usr/bin/env python3
"""results/AKW/tools/akw_s2_gates.py — bramki re-smoke S2 (ANEKS_AKW-1 §6.4) liczone
NA WYJŚCIU frozen akw_analyze.py (akw_summary.json) — zero edycji FROZEN:
  A′ : ENTRY ze skanu w 3/3 ważnych ślepych (c01–c03), każdy t_entry_s ≤ t_A = 23 s
       (wzór §5 dla ścieżki II: min(23, ceil((16.8+3)·1.25)) = 23).
  C  : verbatim — breach 0 we wszystkich epizodach; REFUSE = wpis (nie bramka liczby);
       REFUSE(POS) ⇒ STOP (flaga stop_now analyzera).
  B  : opisowo (ANEKS §2 — w nodze AKW B nie bramkuje): kadencja p50, E2E p95, mod.
Użycie: akw_s2_gates.py <OUTDIR>
"""
import json
import math
import os
import sys

T_A = 23.0
BLIND = {"c01_s01", "c02_s01", "c03_s01"}


def main(outdir):
    s = json.load(open(os.path.join(outdir, "akw_summary.json")))
    eps = {e["scenario_id"]: e for e in s["episodes"]}
    rows = []
    a_ok = True
    n_valid_blind = 0
    for sid in sorted(BLIND):
        e = eps.get(sid)
        if e is None:
            rows.append({"sid": sid, "valid": False, "nota": "BRAK epizodu"})
            a_ok = False
            continue
        ak = e.get("akw", {})
        te = ak.get("t_entry_s")
        valid = bool(e.get("valid_final"))
        if valid:
            n_valid_blind += 1
        ok = valid and te is not None and te <= T_A
        a_ok = a_ok and ok
        rows.append({"sid": sid, "valid": valid, "t_entry_s": te,
                     "t_first_track_rel": ak.get("t_first_track_rel"),
                     "deg_skanu_do_entry": ak.get("deg_skanu_do_entry"),
                     "entry_events": ak.get("entry_events"),
                     "n_reacquisitions": ak.get("n_reacquisitions"),
                     "osc_5s": ak.get("osc_track_to_hold_w_5s_po_akwizycji"),
                     "A_prime_ok": ok})
    breaches = [e["scenario_id"] for e in s["episodes"] if e.get("breach")]
    refuse = {e["scenario_id"]: e.get("refuse_count", 0) for e in s["episodes"]
              if e.get("refuse_count")}
    c_ok = (not breaches) and not s.get("stop_now")
    gb = s.get("gate_b_runtime", {})
    out = {"t_A_s": T_A,
           "A_prime": {"pass": a_ok, "n_valid_blind": n_valid_blind, "episodes": rows},
           "C": {"pass": c_ok, "breaches": breaches, "refuse_wpis": refuse,
                 "stop_now": bool(s.get("stop_now"))},
           "B_opisowo": gb,
           "invalid_any": n_valid_blind < 3}
    p = os.path.join(outdir, "akw_s2_gates.json")
    json.dump(out, open(p, "w"), indent=1)
    print(json.dumps(out, indent=1, ensure_ascii=False))
    print(f"\nA' {'PASS' if a_ok else 'FAIL'} | C {'PASS' if c_ok else 'FAIL'} | "
          f"valid_blind {n_valid_blind}/3 -> {p}")


if __name__ == "__main__":
    main(sys.argv[1])
