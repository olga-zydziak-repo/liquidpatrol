# ANEKS_DEMO3-1 — errata bramki świata (próg przeszczepiony między pętlami) + go na akty

CC · 29.09.2026 · łańcuch DEMO3. Samowykonalny: sesja 2 wykonuje §5 i STOP.

## §1. Właścicielstwo błędu

Bramka FAIL 2/2 to skutek MOJEGO progu, nie świata i nie pipeline'u — liczby wykonawcy to
pokazują wprost: biegi kontrolne (0.9383 / 0.9366) siedzą na MEDIANIE kanonicznej kampanii W
(0.938, 17/17 VALID), czyli estetyka v3 + rejestrator kosztują ~zero. Błąd: przeszczepiłem
próg U2 (Δsim/Δwall ≥0.95) byte-identycznie z pętli GATE (gdzie U2R dawał 0.9997) do materiału
z pętli ŁAWKI, której populacja na tym hoście to ~0.94 i której RATYFIKOWANY reżim ważności to
V2′ (≥0.90 ∧ longest_stall ≤1.5 ∧ timejump=0, ANEKS_BENCH-1a, 2.09). Zaostrza sprawę to, że
właściwe liczby sam cytowałem w ANEKS_W-1b §5 („wszystkie ≥0.90, pod regułą ważności KAMPANII
te habitaty by przeszły") — błąd był unikalny. Klasa: **próg przeniesiony między pętlami bez
sprawdzenia populacji przyrządu** — czwarta instancja rodziny cross-loop (c11-bez-źródła,
atrybucja REPO, route→orbit, teraz próg U2). Wpis do księgi błędów CC. Wykonawca zachował się
wzorcowo: zero trzeciej drogi, STOP z liczbami i martwym fallbackiem nazwanym po imieniu.

## §2. Rozstrzygnięcie Q1 — TAK, i dlaczego to NIE jest luzowanie bramki po wyniku

Zakaz programu dotyczy luzowania kryteriów DOWODOWYCH po obejrzeniu danych. Tu zachodzą trzy
warunki, które czynią korektę errata, nie negocjacją:
(a) reguła zastępująca (V2′) ISTNIEJE i jest ratyfikowana od 2.09 — poprzedza te biegi
o cztery tygodnie i jest reżimem ważności dokładnie tej pętli, którą filmujemy; nie powstała
pod te dane;
(b) DEMO ≠ POMIAR — z bootów demo nie powstaje żaden werdykt; bramka chroni jakość materiału
i uczciwość podpisu, nie dowód; żądanie od filmu habitatu lepszego niż miała kanoniczna
kampania W jest niespójnością, nie ostrożnością;
(c) reguła trwała od dziś (**DEMO-1**): bramka habitatu materiału filmowego = reżim ważności
pętli, z której materiał pochodzi (gate → progi U2; ławka → V2′), zawsze ze źródłem.

Zatem: bramka świata DEMO_V3 = **V2′ ∧ kadr-check**; control_1/control_2 spełniają ją
retroaktywnie (0.938/0.937 ≥0.90, timejump 0, kadr OK) ⇒ **bramka PASS, świat v3 przyjęty,
akty lecą bez nowych biegów kontrolnych**.

WARUNEK FILMOWY (żeby korekta nie kosztowała efektu, na którym zależy Oldze): Δsim/Δwall ~0.94
oznacza ~6% dryfu zegara — montaż MUSI budować oś czasu z **stempli sim-time** klatek
(film_recorder już je pisze), nie z nominalnego fps; do raportu: maksymalna przerwa sim-time
między kolejnymi klatkami per akt (sanity płynności) — widoczny freeze >1 s w materiale aktu
⇒ powtórka tego aktu, nie zmiana progu.

## §3. Q2 i Q3

Q2 (surowy świat + kamera) — ODRZUCONE jako ścieżka główna: Q1 rozwiązuje problem bez
poświęcania wizji. Zapis porządkowy do raportu: fallback §2 promptu był martwy technicznie
(zamrożone world_wind_s* bez kamery — grep 0) — moja druga usterka w tym prompcie, ta sama
klasa „fallback niezweryfikowany wykonalnie"; nowy fallback po tym aneksie jest zbędny (świat
v3 przeszedł), więc nie buduję trzeciej drogi. Q3 — NIE.

## §4. Minimapa

ZOSTAJE, jako zawartość panelu (nie odchylenie): top-down z trasą, intruzem, dyskiem R_E=32
i pozycją drona, dane wyłącznie z trace, skala podpisana; wchodzi w sanity 3 klatek jak reszta
panelu (pozycje na minimapie vs trace verbatim).

## §5. Wykonanie — sesja 2 (akty + montaż)

1. Bramka wejścia: origin/master MUSI zawierać e526612 + 4550af8 + 1c7cc22 (prośba o push,
   jeśli brak). ARCH-1: `ANEKS_DEMO3-1.md` do korzenia pierwszym commitem.
2. Akty wg PROMPT_DEMO_V3 §1/§3 bez zmian (ziarna jawnie, W_ARM_ALWAYS=1, FILM=1, wyłączność,
   cooldowny); sejw wg §4 (≤2 podejścia, fallback trace-driven z epizodu kryterialnego).
   Budżet: zostało 6/8 bootów.
3. Montaż wg §1+§5 promptu z warunkiem sim-time z §2 tego aneksu; minimapa wg §4; captions
   i plansze do CAPTIONS_VERBATIM (kanony sprawdzam przy STOP — EN renderingi zdań WOLNO
   podlegają mojej weryfikacji słowo po słowie, nie parafrazie).
4. STOP-D3: raport płaski wg §8 promptu + wynik warunku płynności per akt. Ratyfikacja wróci
   jako **ANEKS_DEMO3-2** (werdykt kanoniczności + zamknięcie dema).
