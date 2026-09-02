> **dokument spoza łańcucha CC, nieważny jako ratyfikacja — obowiązuje ANEKS_BENCH-1 (CC, 1.09)**
> (przeniesiony do external/ per ANEKS_BENCH-1a C6; zachowany dla śladu, nie stanowi linii ratyfikacyjnej)

---

# ANEKS_BENCH-1 — zgoda na kampanię blok1/48 (po STOP-1b)

LiquidPatrol · pozycja 2 (ławka) · CC 2.09.2026 · wejście: RAPORT_BENCH_BUILD.md + RAPORT_RESHAKEOUT.md
(STOP-1b) · ratyfikacja Olgi = push B3/B3b/B4 + tego pliku · aneks wygrywa z wcześniejszymi zapisami.

## §1. Ratyfikacje
1. Freeze v1.2 RATYFIKOWANY (bramka startu intruder_motion 937ae17c + bench_flight df1250ad + fix interruptible;
   egzekutor 840514361e i parametry 12c14adb bajt-w-bajt z B1). Wyjątek §4 użyty zgodnie z literą.
2. Werdykt N2/c11: (a) tranzient startu + stale tick movera; (b) załamanie promienia OBALONE dla scenariuszy
   manifestu (orbit-phase c11 = 5.84 m już w v1.1; minimum globalne zawsze t≈0.05 s). Wrażliwość na ostrzejsze
   manewry niezmierzona, poza zakresem; strojenie egzekutora = ewentualna nowa seria po kampanii (SR-3).

## §2. ERRATUM D9 (pomyłka CC ze STOP-1)
Skala V1>V2>V3 odczytana wspak. Obowiązuje D9 = V3: metryki w czasie sim; epizod nieważny WYŁĄCZNIE gdy
najdłuższy pojedynczy stall > 3 s wall. Diagnostyka V2 logowana, nieegzekwowana. Test inwariancji (kill-switch):
różnica > 0.01 mediany frac[6,10] lub > 0.1 m d_min między grupami (V2-flag vs bez) obala V3 ⇒ zaostrzenie do V2
+ re-run na cichym hoście. Wpis do rejestru pomyłek CC.

## §3. Kampania — zakres i przebieg
1. Boot-0 (diag): czwórka c00/c05/c10/c11 seed 1 na v1.2; PASS gdy Δfrac[6,10] ≤ 0.006 i Δd_min ≤ 0.1 m per epizod
   vs b2 STOP-1b. PASS ⇒ kryterialne; FAIL ⇒ STOP.
2. Kryterialny: blok1 = 48 epizodów (12 komórek × 4 ziarna), 4/boot ⇒ 12 bootów + boot-0. D6 na blok1
   (p_exec ≥ 0.80 PASS / < 0.60 śmierć; pasmo [6,10]; frac ≥ 0.85; omiatanie 630°; wejście ≤ 25 s; Wilson w raporcie).
   TEST = seed ≡ 0 mod 4 nietknięty; frac[7,9] raportowana.
3. Blok2 (72): opcjonalnie po blok1, bez wpływu na D6, decyzja po 12 bootach.
4. Re-run: epizod odrzucony przez V3 (stall > 3 s) ⇒ re-run z tym ziarnem później, licznik; > 6 re-runów ⇒ STOP.
5. Preflight kampanii: pełny pytest zielony na CZYSTYM hoście (z proc_gate), bramka §3 CLEAN, sha freeze v1.2+piny;
   kampania NIE równolegle z dreamforge.
6. Booty diag (shakeout/re-shakeout/boot-0) nie wchodzą do p_exec ani do zbioru.

## §4. Predykcje CC
P-K1 c11 4/4 ziarna. P-K2 żadna komórka nie łamie d_min > 1/4 ziaren. P-K3 p_exec ∈ [0.85,1.00], punktowo ≥ 0.90.
P-K4 REFUSE=0, breach=0 na 48. P-K5 boot-0 w paśmie. P-K6 V3 odrzuca 0; V2-flag ≤ 25 %; inwariancja nie obala V3.

## §5. Po kampanii (STOP-2)
CC: D6 z Wilsonem, predykcje, decyzja blok2 i ewent. strojenie egzekutora, przejście do PRE sieci (0.9·p_exec).
Wykonawca: raport tekstem płaskim. Push = Olga.
