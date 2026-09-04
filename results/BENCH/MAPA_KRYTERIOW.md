# MAPA KRYTERIÓW BRAMKUJĄCYCH — kampania blok1/48 (ANEKS_BENCH-2 §3 W2)

LiquidPatrol · ławka · sesja kryterialna blok 1 · pierwsza czynność sesji (łapacz kryteriów widmowych).
Reguła W2: **kryterium bez źródła NIE ISTNIEJE**; wątpliwość = pytanie do CC, nie zastosowanie.
Łańcuch CC obowiązujący: PRE_BENCH.md (D1–D10, ratyf.) + ANEKS_BENCH-1 + -1a + -2.

---

## A. WAŻNOŚĆ EPIZODU — D9 = V2′
Źródło: **PRE_BENCH §2 D9** (H1 timejump=0; H2′ per epizod) **skorygowane ANEKS_BENCH-1a §2 R1**.
Reguła V2′: najdłuższy pojedynczy deep-stall (rtf<0.5) **≤ 1.5 s wall** ∧ **Δsim/Δwall ≥ 0.90** ∧ **timejump = 0**.
RÓŻNICA wobec PRE D9: PRE miał dodatkowo „liczba deep-stalli ≤ 3" jako bramkę — **ANEKS-1a §2 R1 ZDJĄŁ cap liczby** (liczba raportowana, NIEBRAMKUJĄCA; blipy 4×0.05 s = szum próbnika). Realizacja: override slotu „V2" params sędziego `bench_judge 8ec0fcfb` (frozen, NIETKNIĘTY): max_deep_stall=∞. Bramkuje agregacja (`campaign_analyze`), nie sędzia.
Env-nieważny/INVALID_START ≠ V2′-nieważny: patrz E/F.

## B. SUKCES EPIZODU — D6 (wszystkie 5 warunków łącznie)
Źródło: **PRE_BENCH §2 D6 (a)–(e)**.
- (a) wejście w pasmo [6,10] m w **≤ 25 s** od startu epizodu (entry_max_s=25)
- (b) frakcja czasu w paśmie **≥ 0.85** w fazie orbity T_orb=70 s
- (c) skumulowany omiatany namiar względem intruza **≥ 630°** w T_orb
- (d) **d_min ≥ 4 m** (3D separacja)
- (e) **0 REFUSE ∧ breach = False**
Wszystko w czasie SIM z GT. p_exec = udane D6 / ważne (V2′).

## C. d_min — ABSOLUTNE kryterium bezpieczeństwa (≥ 4 m per epizod)
Źródło: **PRE_BENCH §2 D3 + D6(d)**, potwierdzone **ANEKS_BENCH-2 §2 R1**.
d_min to statystyka porządkowa pojedynczego punktu — NIE jest kryterium repowtarzalności. Pozostaje wyłącznie absolutnym progiem bezpieczeństwa per epizod (≥ 4 m).

## D. BRAMKA PROCESOWA (§3, wrapper)
Źródło: **PRE_BENCH §3 SR-6**. Reguła: cudzy proces > 2 % CPU **lub** loadavg > 1.5 ⇒ **env-block**, boot nie startuje (kind=env-block, nie liczy się). Harness: `run_boot.sh:62` (`proc_gate.py`). Wtórna kontrola loadavg I2a w pętli.

## E. BRAMKA STARTU INTRUZA (per epizod)
Źródło: **PRE_BENCH §3** („start: … pos_valid, intruz w pozie startowej"). Mechanizm (harness, `bench_flight._intruder_start_gate`): set_pose do pozy startowej + hover, czekaj aż GT intruza ≤ TOL_START; 5 s sim → retry → 5 s sim → **INVALID_START**. INVALID_START = epizod pominięty, **nie liczy się** (kolejka C8 re-append attempt+1). Wymóg: `INTRUDER=1` + model_in_state (inaczej pose None → cały boot INVALID_START, VOID).

## F. KOLEJKA Z PONOWIENIAMI — C8
Źródło: **PRE_BENCH §2 D8 + §3** + warunek C8 z **ANEKS_BENCH-1** (skuteczny). `campaign_queue.py` sha `89619514f0e9`, testy 9/9.
- 48 epizodów blok 1, **4/boot**, ściśle kolejnością kolejki (D8: „zero wybierania epizodów")
- ważna (V2′) = **done**; liczy się **PIERWSZA ważna próba** (D8)
- INVALID_START **lub** V2′-nieważny = re-append **attempt+1**
- twardy **cap attempt ≤ 3**
- 3 nieważne próby = **UNRESOLVED** (listowany, NIE liczy się ani do sukcesów, ani do porażek)
- env-fail/brak manifestu (crash) = re-append **BEZ inkrementu** (nie pali próby)
- **> 4 UNRESOLVED w bloku ⇒ STOP sesji dla CC**

## G. BUDŻETY
Źródło: **PRE_BENCH §2 D8**. Kampania ≤ 3 sesje / **≤ 40 bootów**; 4 epizody/boot; lot ≤ 10 min. Shakeout ≤ 2 booty diag (kind=diag, poza p_exec i zbiorem). Ta sesja = 12 bootów kryterialnych = 48 epizodów.

## H. ZERWANIA NA POZIOMIE SESJI (STOP dokumentem, nie strojeniem)
Źródło: **PRE_BENCH §1 + §3 SR-4/SR-5**.
- **breach** w JAKIMKOLWIEK epizodzie ⇒ STOP natychmiast (SR-5, domena certów)
- **≥ 2 REFUSE-nominal** w jednej sesji ⇒ STOP (§1/§3)
- wybieranie epizodów/bootów (SR-4) ⇒ seria nieważna
- naruszenie zbioru zamrożonego (SR-3/§7) ⇒ seria nieważna

## I. WERDYKT KAMPANII (dwustronny, po budżecie)
Źródło: **PRE_BENCH §1**.
- (+) PASS: p_exec **≥ 0.80** na ≥ 36 ważnych epizodach ∧ 0 REFUSE-nominal ∧ 0 breach ∧ ≥ 90 udanych demonstracji (§4)
- (−) ŚMIERĆ: p_exec **< 0.60**
- środek 0.60–0.80: NIEROZSTRZYGNIĘTE, dokument CC
Raport: p_exec + Wilson 95 %, mediana+IQR frakcji i omiatania (D6 nienasycone, PRE §2 D6/§3).

## J. BRAMKA WEJŚCIA KAMPANII (prekondycje sesji)
Źródło: **ANEKS_BENCH-2 §3 W1** (+ bench-campaign memory).
- push całości przez Olgę + linia „ANEKS_BENCH-1 skuteczny"
- czysty host (bez równoległych obciążeń; dreamforge/a15f zszedł)
- pełny **pytest Z proc_gate** zielony na czystym hoście
- **proc_gate CLEAN** na boocie
- **boot-0 diag PASS** — bramka ratyfikowana -1: manifest bench_finalize **bez stubu i bez null** ⇒ **ZALICZONE** (ANEKS_BENCH-2 §1 U1, commit `1197d01`)

## K. DRYF d_min MIĘDZY SESJAMI (poziom kampanii, nie per-boot)
Źródło: **ANEKS_BENCH-2 §2 R2**. Jeśli kampania pokaże dryf d_min **W DÓŁ** między sesjami (mediana per sesja) ⇒ sygnał STOP dla CC. NIE jest to próg per boot. Nota boot-0 vs reshakeout b2 (~0.4 m ciaśniej przy frac ≥) idzie do raportu jako diagnostyka.

## L. VOID booty
Źródło: **ANEKS_BENCH-2 §3 W3**. Boot VOID (błąd wywołania, pose None) = katalog przemianowany `*_void/` + jedna linia przyczyny w `run.log`, **nigdy kasowany**. Obowiązuje od teraz.

---

## KRYTERIA WIDMOWE — WYCOFANE (nie stosować)
- **Bramka repowtarzalności Δfrac ≤ 0.006 ∧ Δd_min ≤ 0.1 vs reshakeout b2**: rodowód **P-RS1 (widmowa sesja), BRAK numerowanego dokumentu CC** ⇒ WYCOFANA (**ANEKS_BENCH-2 §1 U1, §2 R1/R2**). Nie wchodzi na wejście kampanii ani jako próg per boot.

## PRECONDYCJA (nie bramka, ale unieważnia serię przy naruszeniu)
- **FROZEN-7 bajt-w-bajt** (SR-3 / PRE §7): bench_judge `8ec0fcfb`, features `9adc1505`, track_feed `674d78ab`, orbit_executor `840514361e`, executor_params `12c14adb`, scenario_manifest `e0527026`, piny. Egzekutor NIGDY nie strojony. Przyrząd kampanii zamrożony (FREEZE_CAMPAIGN): campaign_analyze `f31e81e3`, campaign_queue `89619514`, bench_finalize `508856dc`; harness lotu bench_flight `b8eb68ca` v1.3.
