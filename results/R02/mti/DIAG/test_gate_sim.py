#!/usr/bin/env python3
"""results/R02/mti/DIAG/test_gate_sim.py — UNIT-TEST symulatora projekcji (SR-D3).

Bez tego PASS D2/D3 NIE ISTNIEJĄ. Syntetyczne ślady o ZNANYM wyniku bramy → sprawdzamy,
że replay_gate() odtwarza łańcuch okno→streak→ENTRY→ZOH-hold poprawnie. Zero danych realnych.
"""
from gate_sim import replay_gate, TICK_S, THETA_AGE_TICKS

FAILS = []


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    if not cond:
        FAILS.append(name)
    print(f"[{status}] {name}  {detail}")


# T1: ciąg samych True — admisja na K-tym ticku (consecutive), pełne pokrycie po admisji.
r = replay_gate([1] * 10, mode="consecutive", K=3)
check("T1_all_true_entry_at_K", r.entry_tick == 2 and r.n_entry == 1,
      f"entry_tick={r.entry_tick} n_entry={r.n_entry}")
check("T1_all_true_gate_cov_1", r.gate_coverage == 1.0, f"gate_cov={r.gate_coverage}")
check("T1_all_true_locked_post_1", r.locked_coverage_post_entry == 1.0,
      f"lock_post={r.locked_coverage_post_entry}")

# T2: naprzemienny T/F — streak nigdy nie sięga 3 pod rząd → BRAK admisji (consecutive).
r = replay_gate([1, 0] * 8, mode="consecutive", K=3)
check("T2_alt_consecutive_no_entry", r.n_entry == 0 and r.entry_tick is None,
      f"n_entry={r.n_entry}")
check("T2_alt_gate_cov_half", r.gate_coverage == 0.5, f"gate_cov={r.gate_coverage}")

# T3: ten sam naprzemienny ślad, ale okno 3-of-6 — po zebraniu 3 True w oknie → admisja.
# ślad [1,0,1,0,1,...]: na t=4 mamy True i w oknie [t-5..t] są indeksy 0,2,4 = 3 True → admisja @t=4.
r = replay_gate([1, 0] * 8, mode="window", K=3, M=6)
check("T3_alt_window_admits", r.n_entry == 1 and r.entry_tick == 4,
      f"n_entry={r.n_entry} entry_tick={r.entry_tick}")

# T4: pusty ślad — zero pokrycia, zero admisji (kryterium (−) w miniaturze).
r = replay_gate([0] * 20, mode="window", K=3, M=4)
check("T4_empty_no_entry", r.n_entry == 0 and r.gate_coverage == 0.0 and r.locked_coverage == 0.0,
      f"n_entry={r.n_entry} gate_cov={r.gate_coverage}")

# T5: izolowane pojedyncze True rozrzucone rzadziej niż okno — 3-of-4 NIE domyka (FP-like persist).
r = replay_gate([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1], mode="window", K=3, M=4)
check("T5_isolated_spikes_no_entry", r.n_entry == 0,
      f"n_entry={r.n_entry}  (rozrzut > okno ⇒ persist zjada, brak ENTRY)")

# T6: ZOH-age hold — po admisji luka < theta_age (6 ticków) trzyma lock; luka > theta_age wygasza.
# admisja @t=2; potem 5 ticków False (5 < 6-0.2) → wciąż locked; ślad kończy się locked.
seq = [1, 1, 1] + [0] * 5
r = replay_gate(seq, mode="consecutive", K=3)
check("T6_zoh_holds_within_theta_age", r.locked_coverage_post_entry == 1.0,
      f"lock_post={r.locked_coverage_post_entry} (luka 5t<{THETA_AGE_TICKS}t ⇒ trzyma)")

# T7: ZOH-age EXPIRE — po admisji luka > theta_age → lock puszcza (post-entry pokrycie <1).
seq = [1, 1, 1] + [0] * 10
r = replay_gate(seq, mode="consecutive", K=3)
check("T7_zoh_expires_beyond_theta_age", r.locked_coverage_post_entry is not None
      and r.locked_coverage_post_entry < 1.0,
      f"lock_post={r.locked_coverage_post_entry} (luka 10t>{THETA_AGE_TICKS}t ⇒ EXPIRE)")

# T8: sanity jednostki czasu — tick = 0.5 s, time_to_entry zgodny.
r = replay_gate([1, 1, 1], mode="consecutive", K=3)
check("T8_time_to_entry_units", abs(r.time_to_entry_s - 2 * TICK_S) < 1e-9,
      f"t_entry={r.time_to_entry_s}s (=2 ticki×{TICK_S}s)")

print()
if FAILS:
    print(f"UNIT-TEST FAIL ({len(FAILS)}): {FAILS}  — SR-D3 NIE spełnione, D2/D3 wstrzymane.")
    raise SystemExit(1)
print("UNIT-TEST PASS (8/8) — SR-D3 spełnione: symulator projekcji zwalidowany na syntetyce.")
