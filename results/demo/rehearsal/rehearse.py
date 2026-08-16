#!/usr/bin/env python3
"""results/demo/rehearsal/rehearse.py — DEMO-B B2 rehearsal (OFFLINE geometria+timing, ZERO SITL).

Waliduje CHOREOGRAFIĘ aktów (acts/<AKT>_spec.yaml), NIE dowodzi percepcji (PROMPT_D_BUILD_2 §3:
„rehearsal nie jest dowodem percepcji"; werdykty percepcyjne NIERAPORTOWALNE — tu tylko binarne
sanity geometrii/timingu). RE-DERYWUJE liczby z FROZEN źródeł (r01.config, r02.config_r02, REGATE
aggregate, RAPORT_R03A) i porównuje ze spec — łapie dryf prowieniencji. Kryterium wyjścia B2:
≥1 rehearsal per akt w tolerancjach.

Uruchom: python3 -m results.demo.rehearsal.rehearse            (wszystkie akty)
         python3 results/demo/rehearsal/rehearse.py A1|A2|A3
Artefakty: results/demo/rehearsal/<AKT>/rehearsal_1/verdict.json
"""
from __future__ import annotations
import json
import math
import os
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)            # by direct run (python3 …/rehearse.py) widział r01/r02

from r01.config import R_E, ALT_M, V_MAX, A_BRAKE
from r02.config_r02 import INTRUDER_ALT_M, D_SAFE_M, THETA_AGE_S
ACTS = os.path.join(ROOT, "acts")
OUT = os.path.dirname(os.path.abspath(__file__))
REGATE_AGG = os.path.join(ROOT, "results/R02/mti/REGATE/B_regate_aggregate.json")

# --- FROZEN re-derywacje (niezależne od spec — porównywane z nim) ------------
D_STOP = V_MAX ** 2 / (2.0 * A_BRAKE)          # 2.25 m (r01.config)
EPS_CAP = 9.25                                  # RAPORT_R03A (D10/D11)
R_ROUTE_PRIME = R_E - D_STOP - EPS_CAP          # 20.5 m


def regate_entry_p95_ring():
    """t_entry p95 (≈max, n=6) z valid boots REGATE, pierścień {7,9} m."""
    d = json.load(open(REGATE_AGG))
    pool = []
    for rng in ("7m", "9m"):
        pool += d["plus_by_range"][rng]["time_to_entry_s_raw"]
    return max(pool), pool


def approx(a, b, tol):
    return abs(float(a) - float(b)) <= tol


def rng3d(drone_enu, intr_enu):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(drone_enu, intr_enu)))


def check_A1(spec, checks):
    g = spec["geometry"]; t = spec["timeline_s"]
    drone_ned = g["drone_dwell_ned"]; drone_enu = [drone_ned[0], drone_ned[1], -drone_ned[2]]
    intr = g["intruder_ring_enu"]; osc = g["intruder_lateral_osc_m"]; band = g["ring_band_m"]
    tol = spec["tolerances"]
    # frozen cross-check: intruz 1.5 m nad patrolem
    checks.append(("intruder_alt_frozen", approx(intr[2] - (-drone_ned[2]), INTRUDER_ALT_M - ALT_M, 1e-6),
                   f"Δalt spec {intr[2]-(-drone_ned[2])} vs frozen {INTRUDER_ALT_M-ALT_M}"))
    # range 3D w paśmie dla całej osc
    rmin = rng3d(drone_enu, [intr[0], 0.0, intr[2]])
    rmax = rng3d(drone_enu, [intr[0], osc, intr[2]])
    checks.append(("range3d_in_band", band[0] - tol["range_tol_m"] <= rmin and rmax <= band[1] + tol["range_tol_m"],
                   f"range3d ∈ [{rmin:.3f},{rmax:.3f}] vs band {band} ±{tol['range_tol_m']}"))
    # t_entry p95 zgodny z REGATE
    p95, pool = regate_entry_p95_ring()
    ring_hold = t["intruder_ring_hold"]
    entry_by = t["entry_expected_by"]
    checks.append(("t_entry_p95_matches_regate", approx(entry_by - ring_hold[0], p95, 0.01),
                   f"spec entry_by-hold0 {entry_by-ring_hold[0]:.2f} vs REGATE p95 {p95:.2f} (pool {pool})"))
    checks.append(("entry_window_in_hold", ring_hold[0] <= entry_by <= ring_hold[1],
                   f"entry_by {entry_by} ∈ ring_hold {ring_hold}"))
    # worst-case ENTRY + grant(3) + OBSERVE(10) ≤ koniec ring_hold
    grant_delay = 3.0; observe_s = 10.0
    end_needed = entry_by + grant_delay + observe_s
    checks.append(("grant_observe_fit", end_needed <= ring_hold[1] + tol["time_tol_s"],
                   f"entry_by+grant+observe {end_needed} ≤ ring_hold_end {ring_hold[1]}"))
    return {"range3d_band": [rmin, rmax], "t_entry_p95": p95, "end_needed": end_needed}


def check_A2(spec, checks):
    g = spec["geometry"]; t = spec["timeline_s"]; tol = spec["tolerances"]
    # geometria pierścienia jak A1
    drone_ned = g["drone_dwell_ned"]; drone_enu = [drone_ned[0], drone_ned[1], -drone_ned[2]]
    intr = g["intruder_ring_enu"]; osc = g["intruder_lateral_osc_m"]; band = g["ring_band_m"]
    rmin = rng3d(drone_enu, [intr[0], 0.0, intr[2]]); rmax = rng3d(drone_enu, [intr[0], osc, intr[2]])
    checks.append(("range3d_in_band", band[0] - tol["range_tol_m"] <= rmin and rmax <= band[1] + tol["range_tol_m"],
                   f"range3d ∈ [{rmin:.3f},{rmax:.3f}] vs {band}"))
    # far poza zasięg
    far = g["intruder_far_enu"]; far_h = math.hypot(far[0] - drone_enu[0], far[1] - drone_enu[1])
    checks.append(("far_beyond_envelope", far_h > 9.0, f"far horizontal {far_h:.1f} > 9 m koperty"))
    # expire_gap ≥ k·θ_age (k=2.0)
    gap = t["expire_gap"]; gap_len = gap[1] - gap[0]
    checks.append(("expire_gap_ge_k_theta", gap_len >= 2.0 * THETA_AGE_S - 1e-6,
                   f"gap {gap_len} ≥ k·θ_age {2.0*THETA_AGE_S} (θ_age frozen {THETA_AGE_S})"))
    # dwa epizody, re-ENTRY okno w ep1_ring_hold
    p95, _ = regate_entry_p95_ring()
    ep1 = t["ep1_ring_hold"]; ent1 = t["entry_expected_by_ep1"]
    checks.append(("re_entry_window_in_ep1", ep1[0] <= ent1 <= ep1[1] and approx(ent1 - ep1[0], p95, 0.01),
                   f"re-ENTRY_by {ent1} ∈ ep1 {ep1}, offset {ent1-ep1[0]:.2f} vs p95 {p95:.2f}"))
    # dwa beaty operatora
    checks.append(("two_operator_beats", len(spec["operator_beats"]) == 2,
                   f"{len(spec['operator_beats'])} beaty (grant_1, grant_2)"))
    return {"range3d_band": [rmin, rmax], "expire_gap_len": gap_len, "k_theta": 2.0 * THETA_AGE_S}


def check_A3(spec, checks):
    g = spec["geometry"]; e = spec["expected_response"]
    r_inj = 18.0                                    # z timeline trigger drone_radial_reaches_outbound(18.0)
    # frozen cross-check R_route'
    checks.append(("R_route_prime_frozen", approx(g["R_route_prime_m"], R_ROUTE_PRIME, 1e-6),
                   f"spec R_route' {g['R_route_prime_m']} vs frozen {R_ROUTE_PRIME} (R_E {R_E} − d_stop {D_STOP} − ε_cap {EPS_CAP})"))
    checks.append(("inject_within_R_route_prime", r_inj <= R_ROUTE_PRIME,
                   f"r_inj {r_inj} ≤ R_route' {R_ROUTE_PRIME}"))
    # touchdown bound: r_inj + ε_cap + d_stop ≤ R_E (worst case)
    td_bound = r_inj + EPS_CAP + D_STOP
    checks.append(("touchdown_le_R_E", td_bound <= R_E,
                   f"touchdown_bound {td_bound} = r_inj {r_inj}+ε_cap {EPS_CAP}+d_stop {D_STOP} ≤ R_E {R_E}"))
    # REFUSE ≤ 0.15
    checks.append(("refuse_within_015", e["refuse_pos_degraded_within_s"] <= 0.15 + 1e-9,
                   f"REFUSE ≤ {e['refuse_pos_degraded_within_s']} s (S2 0.091 frozen)"))
    checks.append(("no_token_elements", spec.get("intruder") == "absent",
                   "brak elementów tokenowych; intruz absent"))
    return {"r_inj": r_inj, "touchdown_bound": td_bound, "R_route_prime": R_ROUTE_PRIME}


CHECKERS = {"A1": check_A1, "A2": check_A2, "A3": check_A3}


def rehearse(act):
    spec = yaml.safe_load(open(os.path.join(ACTS, f"{act}_spec.yaml")))
    checks = []
    derived = CHECKERS[act](spec, checks)
    passed = all(ok for _, ok, _ in checks)
    outdir = os.path.join(OUT, act, "rehearsal_1")
    os.makedirs(outdir, exist_ok=True)
    verdict = {
        "act": act, "kind": "OFFLINE geometry+timing (NIE dowód percepcji — PROMPT §3)",
        "world": spec["world"], "token_gated": spec.get("token_gated"),
        "verdict": "PASS" if passed else "FAIL",
        "checks": [{"name": n, "ok": bool(ok), "detail": d} for n, ok, d in checks],
        "frozen_rederived": {"d_stop_m": D_STOP, "eps_cap_m": EPS_CAP, "R_route_prime_m": R_ROUTE_PRIME,
                             "theta_age_s": THETA_AGE_S, "R_E_m": R_E, "intruder_alt_m": INTRUDER_ALT_M,
                             "D_safe_m": D_SAFE_M},
        "derived": derived,
        "note": "sanity binarne; percepcja (ENTRY faktyczny, kadr pikselowy) = B5 pierwsza próba, nie tu",
    }
    json.dump(verdict, open(os.path.join(outdir, "verdict.json"), "w"), indent=2, ensure_ascii=False)
    return verdict


def main():
    acts = [sys.argv[1]] if len(sys.argv) > 1 else ["A1", "A2", "A3"]
    allpass = True
    for act in acts:
        v = rehearse(act)
        allpass &= (v["verdict"] == "PASS")
        print(f"=== {act}: {v['verdict']} ===")
        for c in v["checks"]:
            print(f"  {'OK  ' if c['ok'] else 'FAIL'} {c['name']}: {c['detail']}")
    print(f"REHEARSAL B2: {'ALL PASS' if allpass else 'FAIL'}")
    if not allpass:
        sys.exit(1)


if __name__ == "__main__":
    main()
