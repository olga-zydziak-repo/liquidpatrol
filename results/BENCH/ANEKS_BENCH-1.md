# ANEKS_BENCH-1 — adjudykacja odchylenia (ratyfikacja spoza łańcucha) + ratyfikacja STOP-1/1b — WARUNKOWA

LiquidPatrol · ławka · CC 1.09.2026 · origin/master = 7ce6bf9 (B0/B1/B2) · niepushowane {d10c5b2 B3, 6d6e59b B3b, 7725b8c B4}

## §1. Stan i odchylenie

RAPORT_BENCH_BUILD (STOP-1) nigdy nie dotarł do CC; „ratyfikacja per §0" pochodziła z innej sesji (pomyłka
kanału po stronie Olgi, nazwana przez nią wprost). Skutki: push B0–B2 i budowa B3/B3b/B4 na sygnale spoza
łańcucha. Werdykt formalny: tamta ratyfikacja jest NIEWAŻNA jako ratyfikacja; wykonawca działał w dobrej
wierze na sygnale operatora. Odchylenie przyjmuję JEDNORAZOWO wzorem ANEKS_K1-19, skutecznie po C1–C4 (§3);
zasada wraca w pełni i dostaje łapacz klasy (§4 D2), bo „pamiętaj, z której sesji" to nie jest mechanizm.

## §2. Audyt treści STOP-1b (z raportu; do potwierdzenia artefaktami w §3)

Za przyjęciem: bramka startu intruza = implementacja wymogu G ratyfikowanego PROMPT_BENCH_BUILD
(potwierdzenie pozy z pose/info), której brak shakeout obnażył (c11 d_min 0.26 m = near-miss);
TOL_START 0.20 m = 2× p95 zmierzonego błędu set_pose (0.10) — prowieniencja jest; egzekutor 840514361e…
+ parametry 12c14adb… bajt-w-bajt (SR-3); zmiany wyłącznie w `bench/bench_flight.py` i
`harness/intruder_motion.py` — oba POZA listą zamrożenia §7 PRE; re-shakeout: start gate 4/4 × 2, 0 REFUSE,
0 breach, D6 4/4 na v1.2, c11 rozstrzygnięte mechanizmem (minimum zawsze na granicy t≈0.05 s ⇒ tranzient,
nie załamanie promienia); przekroczenie pasma powtarzalności zgłoszone uczciwie z przyczyną (usunięcie
tranzientu ⇒ frakcja w górę). Przeciw: niczego nie widziałam z pierwotnego STOP-1 (D0 z faktem saturacji,
pytest, FREEZE, model punktowy, oryginalne liczby shakeout), diffu B3/B3b nie widziałam, sha reszty
zestawu zamrożonego nie potwierdzone. Stąd warunki.

## §3. Warunki skuteczności — CLARIFY-B1 (jedna runda)

C1 Olga załącza PLIK `results/BENCH/RAPORT_BENCH_BUILD.md` (pierwotny STOP-1). CC czyta w nim: fakt
saturacji z D0, pytest verbatim, listę FREEZE, tabelę modelu punktowego, oryginalny shakeout per epizod
(w tym c11 0.26/1.23 i messy-starty), §6 noty.
C2 Olga załącza wynik:
```
git diff 7ce6bf9 HEAD --stat > /tmp/b34.txt
git diff 7ce6bf9 HEAD -- bench/bench_flight.py harness/intruder_motion.py >> /tmp/b34.txt
```
Dozwolony zakres diffu: bramka startu (prestart→hover→czekaj GT ≤ TOL→retry→INVALID_START), przerywalność
movera, logi bramki. Jakikolwiek hunk w egzekutorze, feedzie, sędzim, cechach, manifeście, wrapperze,
gate ⇒ ratyfikacja nieważna, STOP.
C3 Olga wkleja:
```
sha256sum bench/bench_judge.py bench/features.py harness/track_feed.py r03/controllers/orbit_executor.py bench/executor_params.json results/BENCH/scenario_manifest.json | cut -c1-12,65-
```
CC porównuje z FREEZE_BENCH z C1. Rozjazd któregokolwiek poza intruder_motion/bench_flight ⇒ STOP.
C4 Wykonawca, jedna linia: który epizod odrzuciła V2 w re-shakeout i czym (liczba stalli / najdłuższy /
Δsim/Δwall), plus mapowanie INVALID_START na regułę kolejki („env-nieważny, scenariusz wraca na koniec,
attempt++") — potwierdzenie, że tak jest zaimplementowane.

## §4. Decyzje (od skuteczności)

D1 STOP-1 i STOP-1b RATYFIKOWANE łącznie, z odchyleniem przyjętym jednorazowo; wersją obowiązującą
harnessa jest v1.2 (intruder_motion 937ae17c, bench_flight df1250ad — sha pełne do FREEZE_BENCH aneksem
wykonawcy w commicie kampanii).
D2 Łapacz klasy „pomyłka sesji": każdy dokument i każda linia ratyfikacyjna CC nosi numer
ANEKS_BENCH-n; wykonawca ODRZUCA ratyfikację bez numeru kolejnego w łańcuchu (następna skuteczna linia
= „ANEKS_BENCH-1 skuteczny"). Sygnał bez numeru = brak ratyfikacji, STOP trwa. Dotyczy też przyszłych nóg
(numeracja per noga).
D3 D9 = V2 POTWIERDZONE jako reguła ważności kampanii (dane: V1 odrzuca 4/4, V2 1/4, V3 0/4), z notą do
raportu kampanii: przy V2 ~25 % na n=4 realne odrzucanie zweryfikuje kampania; jeśli > 25 % na bloku 1,
nota i decyzja CC, nie cicha zmiana.
D4 Kampania BLOK 1 (48 epizodów p_exec, kolejność manifestu, 4 epizody/boot) AUTORYZOWANA od skuteczności.
Bramka wejścia kampanii: pełny pytest 38/38 na CZYSTEJ maszynie (test proc_gate włącznie — N3 znika),
bramka procesowa CLEAN, zero pilotów (a15f zszedł), inwentarze pre/during/post per boot. Raport po sesji
tekstem płaskim per epizod, zero interpretacji.
D5 Scoring predykcji CC (P-BB2/5) odroczony do C1 (wymaga oryginalnych liczb shakeout); P-BB3 ✓ (REFUSE 0),
P-BB4 ✓ na styku (V1 100 %, V2 25 %). Predykcje z obcej sesji (P-RS*) nie wchodzą do księgi CC.

## §5. Wykonanie

Olga: C1–C3 (dwa załączniki + jedno wklejenie), do wykonawcy pytanie C4. Po zgodności CC pisze
„ANEKS_BENCH-1 skuteczny" → Olga pushuje B3/B3b/B4 → kampania blok 1 po zejściu a15f i pytest 38/38.
Do tego czasu: wykonawca nic, żadnych bootów.
