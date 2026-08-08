#!/usr/bin/env python3
"""r02/irr_seed_spread.py — SPREAD nieregularności GT-fed na 5 seedach (bez SITL/GPU).

Domyka zastrzeżenie Olgi: „wariant nieregularności na 3–5 seedach (nie 1) — raportuj rozrzut".
Odtwarza WIERNIE logikę _channel_step (GT-fed) z r02/gate_run_r02.py: stała poza (dron hover,
intruz statyczny w FOV), REALNY TargetChannel(ChannelConfig()), identyczny dropout (Bernoulli+burst)
+ szum obserwacyjny + kadencja detektora 1 Hz + egzekucja sufitu age między klatkami (tick_time).
Mierzy per-seed: n_dropout, n_entry, n_reentry, n_expire, max_age (sufit THETA_AGE_S), locked_ticks.
Teza: kanał zachowuje się SOUNDNIE na KAŻDYM seedzie (ENTRY, EXPIRE na suficie, re-ENTRY), nie na 1.
"""
import random, statistics
from r02.gate_harness import project_to_pixel
from r02.target_channel import TargetChannel, Box
from r02.config_r02 import ChannelConfig, DET_DT, THETA_AGE_S
from r01.config import ALT_M

PERIOD = 0.05
POS = [0.0, 0.0, -ALT_M]; YAW = 0.0; INTR = (7.0, 0.0, -11.5)   # jak G2/G5 (intruz w FOV)
DUR_S = 60.0
DROPOUT_P, BURST_P, BURST_LEN, NOISE = 0.25, 0.3, 5, 0.01        # jak G2-IRR
SEEDS = [1, 7, 13, 42, 101]

def run_seed(seed):
    rng = random.Random(seed)
    ch = TargetChannel(ChannelConfig())
    burst_left = 0; n_dropout = 0; gt_next = 0.0
    max_age = 0.0; locked_ticks = 0; n_steps = 0
    t = 0.0
    while t < DUR_S:
        if t >= gt_next - 1e-9:
            b = project_to_pixel(POS, YAW, INTR)
            box = None
            if b is not None:
                cx = min(max(b.cx + rng.gauss(0, NOISE), 0.0), 1.0)
                cy = min(max(b.cy + rng.gauss(0, NOISE), 0.0), 1.0)
                box = Box(cx, cy, b.w, b.h, conf=1.0)
            if box is not None:
                if burst_left > 0:
                    box = None; burst_left -= 1; n_dropout += 1
                elif rng.random() < DROPOUT_P:
                    box = None; n_dropout += 1
                    if rng.random() < BURST_P:
                        burst_left = BURST_LEN
            ch.on_frame(box, t, gt_present=(box is not None))
            gt_next += DET_DT
        else:
            ch.tick_time(t)
        val = ch.sample(t)
        locked = ch.locked and not ch.is_expired(t)
        if val is not None and val.age_s is not None:
            max_age = max(max_age, val.age_s)
        if locked: locked_ticks += 1
        n_steps += 1
        t += PERIOD
    return {"seed": seed, "n_dropout": n_dropout, "n_entry": ch.n_entry,
            "n_reentry": max(ch.n_entry - 1, 0), "n_expire": ch.n_expire,
            "max_age": round(max_age, 3), "locked_ticks": locked_ticks,
            "age_ceiling_ok": max_age <= THETA_AGE_S + PERIOD + 1e-6,
            "final_locked": bool(ch.locked)}

def main():
    print(f"=== SPREAD nieregularności GT-fed — {len(SEEDS)} seedów (dropout={DROPOUT_P} "
          f"burst={BURST_P}/{BURST_LEN} noise={NOISE} dur={DUR_S}s @1Hz det) ===")
    rows = [run_seed(s) for s in SEEDS]
    hdr = f"{'seed':>5} {'drop':>5} {'entry':>6} {'reent':>6} {'expire':>7} {'max_age':>8} {'lock_tk':>8} {'ceil_ok':>8}"
    print(hdr); print("-"*len(hdr))
    for r in rows:
        print(f"{r['seed']:>5} {r['n_dropout']:>5} {r['n_entry']:>6} {r['n_reentry']:>6} "
              f"{r['n_expire']:>7} {r['max_age']:>8} {r['locked_ticks']:>8} {str(r['age_ceiling_ok']):>8}")
    def spread(key):
        vs = [r[key] for r in rows]
        return f"min={min(vs)} max={max(vs)} mean={statistics.mean(vs):.1f} sd={statistics.pstdev(vs):.2f}"
    print("\n--- ROZRZUT (5 seedów) ---")
    for k in ("n_dropout", "n_entry", "n_expire", "max_age", "locked_ticks"):
        print(f"  {k:12s}: {spread(k)}")
    all_entry = all(r["n_entry"] >= 1 for r in rows)
    all_ceiling = all(r["age_ceiling_ok"] for r in rows)
    # re-ENTRY występuje tam, gdzie był EXPIRE — spójność
    coherent = all((r["n_reentry"] >= 1) == (r["n_expire"] >= 1) for r in rows)
    ok = all_entry and all_ceiling and coherent
    print(f"\nTEZA (każdy seed): ENTRY≥1 na wszystkich={all_entry}  sufit_age_ok={all_ceiling}  "
          f"re-ENTRY↔EXPIRE spójne={coherent}")
    print(f"SPREAD PASS: {ok} (nieregularność obsłużona SOUNDNIE na {len(SEEDS)} seedach, nie na 1)")
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
