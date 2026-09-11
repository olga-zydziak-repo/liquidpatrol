# RAPORT_FV_S2 — sesja S2: M-krok (mutanty) + O2 (histereza, cert P7) — STOP-FV2? nie, ANEKS_FV-1a

CC · 11.09.2026 · noga FV (poz.1b), S2 wg PROMPT_FV_S2. Zero bootów/GPU/treningu/instalacji.
Narzędzia: z3 (`.certdeps`) + stdlib + numpy z repo.

## §1. Bramka wejścia
`git log origin/master..HEAD` puste (S1 pushnięte przez Olgę) → dalej. ANEKS_FV-1.md nieobecny w
Downloads/repo — jego commit ARCH-1 odroczony (treść operacyjna niesiona przez PROMPT_FV_S2 §2/§3;
lista zamknięta §0.4 go nie wymienia). Odnotowane, ni blokujące.

## §2. M-krok (adekwatność przyrządu PRZED O2)
- **CM1 (4a84f20):** katalog 27 mutantów prereg (`results/FV/MUTANTY.md`), 4 klasy × 4 funkcje, lista
  nietykalna. Klasa (ii) bez miejsca w geofence (progi=parametry) i safe_descend (stałe float) — jawnie 0.
- **CM2 (5856a92):** `tests_fv_mutants.py` (mutanty w pamięci, `fv_mirror.py` nietknięty; oracle=produkcja).
  Sanity IDENTITY (mut='none') = 0 rozbieżności. **WYKRYTE 27/27 = 100%**, 0 przeżywających ⇒ grid2
  NIEPOTRZEBNA (0 iteracji). Wykrycie dominująco siatką (25/27); tylko dwa swap-mutanty geofence wymagały
  fuzz (potrzeba dwóch warunków bramki prawdziwych naraz). `sd_neg_descending` wykryty przez crash
  (el=now−None) = zachowanie ≠ produkcja. Nota: `pm_neg_flag`(iii) i `pm_swap_branches`(iv) behawioralnie
  zbieżne — różnią się klasą, oba zabite.
- **M5:** finalny bieg pełnej różnicówki (siatka 54 + fuzz 4×10⁵ + fikstura 4221/1791) na niemutowanym
  lustrze = **0 rozbieżności**. Przyrząd adekwatny i lustro wierne.

## §3. O2 — histereza `_pos_monitor` (CO2, cert P7_posmon)
Prover `posmon_verify.py`: enumeracja osiągalnego grafu FSM (BFS) na lustrze ≡ produkcja + z3-duplikat.
- **Abstrakcja (jawna, sound):** `pos_bad` w kodzie NIE capowany (shield.py:83), ale czytany wyłącznie
  przez `>=debounce` (shield.py:85) i resetowany do 0 na False (shield.py:89) ⇒ saturacja
  `min(pos_bad,debounce)` zachowuje zachowanie. `pos_healthy∈{0..hyst-1}` z natury (reset przy `>=hyst`).
  Bez tej abstrakcji surowy graf byłby nieskończony.
- **Graf:** **n_stanów=103, n_krawędzi=206** (≪ 10⁶ — S2-E niewyzwolony). Σ={True,False}; None=no-op
  (pętla własna, poza grafem).
- **(a)** każde wejście REFUSE(POS) (r:False→True) tylko na True ∧ pos_bad=debounce−1=1; **min bieg True
  do wejścia = 2 = debounce**. PASS.
- **(b)** każde wyjście (r:True→False) tylko na False ∧ pos_healthy=hyst−1=99; **min bieg False do
  wyjścia = 100 = hyst**. PASS.
- **(c)** **min cykl zdegradowany→czysty→zdegradowany = 102 = hyst+debounce** (wyjście wymaga hyst
  czystych, ponowne wejście debounce bad — brak trzepotania szybszego niż histereza).
- **z3-duplikat (O2d):** step-inwarianty (a-step) `¬r∧r' ⇒ input=True ∧ pos_bad≥deb−1` i (b-step)
  `r∧¬r' ⇒ input=False ∧ pos_healthy≥hyst−1` — **oba unsat** (własność zachodzi). Enumeracja jest metodą
  podstawową (PRE §3/O2); z3 potwierdza krok lokalnie.
- **O2f:** mapa `certs_selfcheck.py` +P7 (diff verbatim niżej), `certs_selfcheck` PASS **8/8**.

## §4. Domknięcia
- **CLARIFY-1 (ANEKS_FV-1 §3):** produkcyjna formuła desc_total VERBATIM —
  `bench_flight.py:75`: `"desc_total": max(0.0, (C.ALT_M - C.H_SWITCH_AGL) / C.V_DESC_FAST) + C.H_SWITCH_AGL / C.V_DESC_LAND + 1.5`
  (identyczna w `gate_run_r03.py:224`: `desc_total = desc_fast_dur + C.H_SWITCH_AGL / C.V_DESC_LAND + 1.5`).
- **pytest offline** (pełna lista `tests_*.py`): **100 passed** (S1 98 + tests_fv_mutants 2). Zero regresji.
- **SR-FV-7:** drzewo czyste w zakresie proofs/ po CO2; selfcheck 8/8 wklejony do raportu STOP.

## §5. Bramka nogi (PRE_FV §5) — stan po S2
**O1 ∧ O2 dowiedzione** (certy P6+P7, provery + wpisy selfcheck) ∧ **różnicówka czysta** (0 rozbieżności,
M5) ∧ **przyrząd adekwatny** (M-krok 27/27). To spełnia definicję **PASS nogi** (O1∧O2∧różnicówka czysta).
O3 (geofence↔P2) i O4 (złożenie) = S3, niebramkujące. TRIPWIRE niewyzwolony (0 kontrprzykładów na
produkcji). ŚMIERĆ nie zachodzi. Werdykt formalny nogi = przy RAPORT_FV (ANEKS_FV-2), nie tutaj.

## §6. Diff mapy certs_selfcheck.py (verbatim)
```diff
@@ -36,6 +36,7 @@ PROVER_OF = {
     "P5.json": "conformance.py",
     "P2_eps.json": "eps_verify.py",     # R0.3a: P2-ε (forma plateau/A-episode)
     "P6_d5.json": "d5_verify.py",       # FV/O1: D5 safe_descend_step (lustro ≡ produkcja)
+    "P7_posmon.json": "posmon_verify.py",  # FV/O2: histereza _pos_monitor (enumeracja grafu + z3)
 }
```

**STOP S2.** Push = Olga. Ratyfikacja: **ANEKS_FV-1a** (go na S3 = O3 + O4). Commity: CM1 4a84f20,
CM2 5856a92, CO2 (ten).
