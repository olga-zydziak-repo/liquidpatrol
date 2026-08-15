#!/usr/bin/env python3
"""results/R02/mti/DIAG/gate_sim.py — SYMULATOR PROJEKCJI bramy ENTRY (D2/D3, offline).

PROJEKCJA OFFLINE ≠ POMIAR. Ten symulator NIE lata i NIE dotyka bramy produkcyjnej
(r02/target_channel.py). Odtwarza logikę ADMISJI ENTRY na SYNTETYCZNYM lub realnym śladzie
per-tick booleanów bramy g[t] = (box ∧ central ∧ mti_ok) — PEŁNY łańcuch okno→streak→ENTRY,
nie skrót (SR-D2: bez zmian w kodzie bramy; to osobny instrument analityczny).

Model (uzgodniony z r02/target_channel.py @ e4c76ba):
  - decision_hz = 2.0  → 1 tick = 0.5 s   (result.json params.decision_hz)
  - ENTRY_K = 3        → admisja: streak ≥ K spójnych klatek bramy (target_channel.entry_k)
  - THETA_AGE_S = 3.0, L_DELIVER_S = 0.10 → po admisji lock trzyma ZOH-age, wygasa gdy
    (Δt_od_ostatniej_True + l_deliver) > theta_age.
Założenie modelujące (JAWNE): gdy g[t]=True, środek boxa jest spójny lokalizacyjnie z poprzednim
tickiem serii (pościg OBSERVE ⇒ cel quasi-statyczny w kadrze), więc streak = długość ciągu True.
To założenie jest OPTYMISTYCZNE dla ADMISJI (realny gate dodatkowo wymaga move≤entry_move_thr);
projekcja przewiduje, pomiar rozstrzyga.

Dwa tryby admisji:
  mode="consecutive"  K spójnych True pod rząd (WIERNY obecnej bramie, entry_k=K).
  mode="window"       ≥m True w przesuwnym oknie długości M (PROPONOWANE złagodzenie D2, m-of-M).
"""
from dataclasses import dataclass

DECISION_HZ = 2.0
TICK_S = 1.0 / DECISION_HZ          # 0.5 s
ENTRY_K = 3
THETA_AGE_S = 3.0
L_DELIVER_S = 0.10
THETA_AGE_TICKS = THETA_AGE_S / TICK_S   # 6.0 ticków


@dataclass
class GateResult:
    n_ticks: int
    gate_coverage: float          # surowa frakcja True (niezależna od K)
    n_entry: int
    entry_tick: int | None        # indeks ticka, na którym zaszła 1. admisja (0-based)
    time_to_entry_s: float | None
    locked_coverage: float        # frakcja ticków w stanie LOCKED (po admisji, ZOH-age hold)
    locked_coverage_post_entry: float | None  # frakcja LOCKED liczona OD admisji


def replay_gate(gate_seq, mode="consecutive", K=ENTRY_K, M=None,
                theta_age_ticks=THETA_AGE_TICKS):
    """Odtwórz łańcuch admisji ENTRY na ciągu booleanów bramy `gate_seq`.

    mode="consecutive": streak ≥ K spójnych True → ENTRY (wierne entry_k).
    mode="window": ≥K True w oknie ostatnich M ticków → ENTRY (m-of-M; M wymagane).
    Po ENTRY: lock trzyma dopóki (ticki_od_ostatniej_True + l_deliver/tick) ≤ theta_age_ticks;
    świeża True odświeża; przekroczenie wieku → EXPIRE (i seria może startować od nowa).
    Zwraca GateResult. NIE modyfikuje żadnego stanu produkcyjnego.
    """
    if mode == "window" and M is None:
        raise ValueError("mode='window' wymaga M (długość okna)")
    n = len(gate_seq)
    streak = 0
    locked = False
    ticks_since_true = None
    entry_tick = None
    n_entry = 0
    locked_count = 0
    locked_post = 0
    l_deliver_ticks = L_DELIVER_S / TICK_S
    for t in range(n):
        g = bool(gate_seq[t])
        if not locked:
            # --- faza admisji ---
            admit = False
            if mode == "consecutive":
                streak = streak + 1 if g else 0
                admit = streak >= K
            else:  # window m-of-M
                lo = max(0, t - M + 1)
                cnt = sum(1 for x in gate_seq[lo:t + 1] if x)
                admit = g and cnt >= K   # bieżąca klatka musi być True (kandydat serii)
            if admit:
                locked = True
                ticks_since_true = 0
                if entry_tick is None:      # entry_tick = PIERWSZA admisja (zgodne z żywą bramą; re-ENTRY nie nadpisuje)
                    entry_tick = t
                n_entry += 1
        else:
            # --- faza LOCKED: ZOH-age hold ---
            if g:
                ticks_since_true = 0
            else:
                ticks_since_true += 1
                if ticks_since_true + l_deliver_ticks > theta_age_ticks:
                    locked = False
                    streak = 1 if g else 0   # po EXPIRE klatka może zacząć serię
        if locked:
            locked_count += 1
        if entry_tick is not None and t >= entry_tick:
            if locked:
                locked_post += 1
    gate_cov = sum(1 for x in gate_seq if x) / n if n else 0.0
    lock_cov = locked_count / n if n else 0.0
    post_n = (n - entry_tick) if entry_tick is not None else 0
    lock_cov_post = (locked_post / post_n) if post_n else None
    return GateResult(
        n_ticks=n,
        gate_coverage=round(gate_cov, 4),
        n_entry=n_entry,
        entry_tick=entry_tick,
        time_to_entry_s=round(entry_tick * TICK_S, 3) if entry_tick is not None else None,
        locked_coverage=round(lock_cov, 4),
        locked_coverage_post_entry=round(lock_cov_post, 4) if lock_cov_post is not None else None,
    )


if __name__ == "__main__":
    # smoke
    print(replay_gate([1, 1, 1, 0, 0, 1, 1], mode="consecutive", K=3))
    print(replay_gate([1, 0, 1, 0, 1, 0, 1, 0], mode="consecutive", K=3))
    print(replay_gate([1, 0, 1, 0, 1, 0, 1, 0], mode="window", K=3, M=6))
