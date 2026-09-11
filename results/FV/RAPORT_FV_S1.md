# RAPORT_FV_S1 — sesja budowy: lustro + różnicówka + dowód O1 (STOP-FV1)

CC · 11.09.2026 · noga FV (poz.1b), sesja S1 wg PROMPT_FV_S1. Zero bootów/GPU/treningu/instalacji.
Narzędzia: z3 (`.certdeps`) + stdlib + numpy z repo.

## §1. Bramka wejścia
`git log origin/master..HEAD` na wejściu = DOKŁADNIE 24f884d + 8e6206c (stan przewidziany §0.1) →
prośba o push → Olga potwierdziła („pushnięte") → `origin/master..HEAD` puste po fetch → dalej.

## §2. C0 — dokumenty ARCH-1 (df58922)
Cztery pliki pobrane z `/mnt/c/Users/User/Downloads/` (pojedyncze trafienia globów, bez sufiksów),
nagłówki zgodne, brak CRLF, skopiowane do korzenia repo bez transformacji. sha256:
- PRE_FV.md       `9e3caf234c47f96c1c8cec26f10c877c88f49383308e576313cb3050b95516a1`
- ANEKS_K2-7.md   `92ed5bbb0c962952f2f6d8771f55cd17157492b835cd924001585efaba408097`
- ANEKS_NET-6.md  `08f70137fbd5753a1ede0cdd0512377d3a7a0c657ae1ab15911a39d10fd1000b`
- ANEKS_FV-0.md   `7d36010821a8f4e14bc4e0c291b6b8666f55f5285b8ceb3bed993348a6b0f834`

## §3. C1 — lustro + siatka + różnicówka (729a44c)
- `fv_mirror.py`: lustro 1:1 czterech elementów ze stanem zreifikowanym (`_braking_dist` ←
  shield.py:97-99; `_geofence_violation` ← :101-112; `_pos_monitor` ← :76-94; `safe_descend_step` ←
  safe_descend.py:20-49). Progi z produkcji (`shield_thresholds()` / `d5_cfg()`), nie z pamięci.
- `fv_diff_grid.json`: siatka deterministyczna, progi z produkcji (r_e=32, v_e=20, v_max=3, a_brake=2,
  dt=0.05, debounce=2, hyst=100, desc_fast_dur=16/3, desc_total=407/42). 54 wpisy. NIETYKALNA po C1.
- `tests_fv_diff.py`: różnicówka trójwarstwowa + P1-consistency (F1).

## §4. Różnicówka — bieg (sweep)
- siatka: braking_dist 24 · geofence 15 · pos_monitor 10 · safe_descend 5 = 54
- fuzz {0..4}: 100000 / funkcję (×4 funkcje = 400000)
- fikstura D5: 11 plików, 4221 ticków (1791 descending)
- **ROZBIEŻNOŚCI: 0** (finalny bieg czysty; zero poprawek lustra — `REJESTR_ROZBIEZNOSCI.md`).
- stat: `results/FV/diff_stats.json`.

## §5. C2 — dowód O1 + domknięcie
- `d5_verify.py` (prover z3) + `certs/P6_d5.json`: O1 PROVED, 10/10 obligacji unsat.
  N*=194 kroków fazy zejścia (Δ=dt=0.05s ⇒ t_touchdown 9.700s). Twierdzenia (a)–(d) PRE_FV §3/O1.
  A1-zegar jako jawne assumption z cytatami (now=time.monotonic(): bench_flight.py:371,
  gate_run_r03.py:280). Stałe z config (V5).
- `certs_selfcheck.py`: +1 linia mapy (P6_d5 ← d5_verify.py). `certs_selfcheck` PASS **7/7**.
- pytest offline: pełna lista `tests_*.py` = **98 passed** (w tym różnicówka 10 + D5 3). Zero regresji.
  (`r01/brake_test.py` nie jest testem — skrypt pomiarowy wymagający rclpy/ROS, poza kolekcją offline;
  problem preegzystujący, niezwiązany z tą sesją.)

## §6. Status predykcji (bez rozliczania — rozliczenie przy RAPORT_FV, ANEKS_FV-0 §3)
- P-FV-1 (O1 w ≤1 sesji): O1 dowiedzione w S1 — trend spełnienia, rozliczenie przy RAPORT_FV.
- P-FV-2 (≥1 rozbieżność wymagająca poprawki LUSTRA): w S1 **0 rozbieżności** — trend NIE-spełnienia;
  rozliczenie przy RAPORT_FV (nie tutaj).
- P-FV-3 (O4 w ≤1 sesji): poza zakresem S1.

## §7. Bramka nogi (PRE_FV §5) — stan po S1
O1 dowiedzione ∧ różnicówka czysta. O2 (histereza) = S2 (poza zakresem S1). PASS nogi wymaga O1 ∧ O2;
po S1 stan = O1 zaliczone, czeka O2. TRIPWIRE nie wyzwolony (0 rozbieżności, żaden kontrprzykład na
produkcji). ŚMIERĆ nie zachodzi (lustro wiarygodne bez reifikacji produkcji).

**STOP-FV1.** Push = Olga. Ratyfikacja: ANEKS_FV-1.
