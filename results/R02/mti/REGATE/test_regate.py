#!/usr/bin/env python3
"""results/R02/mti/REGATE/test_regate.py — unit-testy REGATE (SR-R1, PASS przed lotem).

Trzy grupy:
  (1) automat ENTRY-once na `r02.target_channel.TargetChannel` (entry_require_mti=True), 4 wektory;
  (2) kompletność trace: liczba rekordów = liczba ticków (kontrakt asercji harnessu);
  (3) zgodność `gate_sim` (projekcja DIAG) ↔ żywa brama na TYM SAMYM syntetycznym śladzie —
      to zdanie spina projekcję z implementacją (identyczny entry_tick + pokrycie po admisji).
Zero SITL/GPU — deterministyczne.
"""
import os
import sys

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "results/R02/mti/DIAG"))

from dataclasses import replace
from r02.target_channel import TargetChannel, Box, EV_ENTRY, EV_EXPIRE, EV_REFRESH
from r02.config_r02 import ChannelConfig
from gate_sim import replay_gate, TICK_S

FAILS = []


def check(name, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")
    if not cond:
        FAILS.append(name)


CFG = replace(ChannelConfig(), entry_require_mti=True)   # tryb DEMO/MTI (jak mti_flight.py:184)
CENTRAL_BOX = Box(0.5, 0.5, 0.1, 0.1, conf=0.2)          # centralny (edge_dist 0.5 ≥ margin)


def feed(ch, i, has_box=True, central=True, mti_ok=True):
    """Jeden tick @0.5 s. central=False → box przy krawędzi (edge<margin)."""
    t = i * TICK_S
    box = None
    if has_box:
        box = CENTRAL_BOX if central else Box(0.02, 0.5, 0.1, 0.1, conf=0.2)
    return ch.on_frame(box, t, gt_present=True, mti_ok=mti_ok)


# ---------- GRUPA 1: automat ENTRY-once, 4 wektory ----------
# V1: pełna koniunkcja box∧central∧mti_ok → ENTRY po K=3.
ch = TargetChannel(CFG)
evs = [feed(ch, i) for i in range(3)]
check("V1_full_conjunction_ENTRY", ch.locked and ch.n_entry == 1 and evs[-1] == EV_ENTRY,
      f"locked={ch.locked} n_entry={ch.n_entry} ev3={evs[-1]}")

# V2: PO ENTRY brak mti_ok NIE wybija locka (post-admisja: kanał karmi struktura, mti_ok=telemetria).
ev_a = feed(ch, 3, has_box=True, central=True, mti_ok=False)   # box jest, MTI nie
ev_b = feed(ch, 4, has_box=True, central=False, mti_ok=False)  # box przy krawędzi, MTI nie
check("V2_post_entry_no_mti_holds_lock", ch.locked and ev_a == EV_REFRESH and ev_b == EV_REFRESH,
      f"locked={ch.locked} ev_a={ev_a} ev_b={ev_b} (ENTRY-once: po locku mti_ok obojętne)")

# V3: EXPIRE → ponowna admisja WYMAGA pełnej koniunkcji (anti-clutter na KAŻDYM wejściu).
ev_exp = ch.on_frame(None, 4 * TICK_S + 4.0, gt_present=True, mti_ok=False)  # luka > θ_age → EXPIRE
check("V3a_expire_after_gap", (not ch.locked) and ev_exp == EV_EXPIRE, f"locked={ch.locked} ev={ev_exp}")
# po EXPIRE: box centralny ale BEZ mti_ok ×5 → NIE re-admisja
base = 20
for i in range(base, base + 5):
    feed(ch, i, has_box=True, central=True, mti_ok=False)
check("V3b_reentry_needs_mti", (not ch.locked) and ch.n_entry == 1,
      f"locked={ch.locked} n_entry={ch.n_entry} (brak MTI ⇒ brak re-ENTRY)")
# teraz pełna koniunkcja ×3 → re-admisja
for i in range(base + 5, base + 8):
    feed(ch, i, has_box=True, central=True, mti_ok=True)
check("V3c_reentry_on_full_conjunction", ch.locked and ch.n_entry == 2,
      f"locked={ch.locked} n_entry={ch.n_entry}")

# V4: ślad sceny-FP (box jest, ale nigdy mti_ok) → NIGDY ENTRY.
ch2 = TargetChannel(CFG)
for i in range(40):
    feed(ch2, i, has_box=True, central=True, mti_ok=False)
check("V4_fp_scene_no_entry", ch2.n_entry == 0 and not ch2.locked,
      f"n_entry={ch2.n_entry} locked={ch2.locked}")


# ---------- GRUPA 2: kompletność trace (kontrakt asercji harnessu) ----------
def drive_trace(gate_seq):
    """Buduje trace jak harness: 1 rekord / tick, niezależnie od stanu. Zwraca (trace, n_entry, locked_list)."""
    ch = TargetChannel(CFG)
    trace = []
    locked_list = []
    entry_tick = None
    for i, g in enumerate(gate_seq):
        ev = feed(ch, i, has_box=bool(g), central=bool(g), mti_ok=bool(g))
        trace.append({"tick": i, "gate": bool(g), "locked": ch.locked, "entry": ev == EV_ENTRY})
        locked_list.append(ch.locked)
        if ev == EV_ENTRY and entry_tick is None:
            entry_tick = i
    return trace, entry_tick, locked_list


seqA = [1, 1, 1, 0, 0, 1, 1, 1, 0, 0]
trace, _, _ = drive_trace(seqA)
check("G2_trace_completeness", len(trace) == len(seqA), f"n_records={len(trace)} n_ticks={len(seqA)}")


# ---------- GRUPA 3: zgodność gate_sim ↔ żywa brama ----------
def live_metrics(gate_seq):
    """entry_tick + pokrycie LOCKED po admisji z ŻYWEJ bramy."""
    _, entry_tick, locked_list = drive_trace(gate_seq)
    if entry_tick is None:
        return None, None
    post = locked_list[entry_tick:]
    cov_post = round(sum(1 for x in post if x) / len(post), 4)
    return entry_tick, cov_post


CONSISTENCY_SEQS = {
    "all_true":      [1] * 10,
    "gap_hold":      [1, 1, 1, 0, 0, 0, 0, 0],          # luka 5 < θ_age(6t) → trzyma
    "gap_expire":    [1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],  # luka >θ_age → EXPIRE, re-admisja
    "alternating":   [1, 0] * 8,                        # nigdy 3 pod rząd → brak ENTRY
    "late_start":    [0, 0, 1, 1, 1, 0, 0],
}
for name, seq in CONSISTENCY_SEQS.items():
    live_et, live_cov = live_metrics(seq)
    sim = replay_gate(seq, mode="consecutive", K=3)
    sim_et = sim.entry_tick
    sim_cov = sim.locked_coverage_post_entry
    match = (live_et == sim_et) and (
        (live_cov is None and sim_cov is None) or
        (live_cov is not None and sim_cov is not None and abs(live_cov - sim_cov) < 1e-9))
    check(f"G3_consistency_{name}", match,
          f"live(entry={live_et},cov={live_cov}) sim(entry={sim_et},cov={sim_cov})")


print()
if FAILS:
    print(f"UNIT-TEST REGATE FAIL ({len(FAILS)}): {FAILS} — SR-R1 NIESPEŁNIONE, LOT WSTRZYMANY.")
    raise SystemExit(1)
print("UNIT-TEST REGATE PASS — SR-R1 spełnione (automat ENTRY-once + kompletność + gate_sim↔brama).")
