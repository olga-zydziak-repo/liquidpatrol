# PRE_WABIK2 — prerejestracja nogi WABIK-II / REGUŁA CZASOWA (naprawa offline-first + potwierdzenie na świeżych wariantach)

CC · 27.10.2026 · po CO-WABIK (cd8f93bf; werdykt (i): warstwa cech działa,
sfalsyfikowana reguła czasowa — trzy zmierzone mechanizmy). Wymaga ratyfikacji
Olgi; po niej PROMPT_WABIK2_S1 — na start nogi wklejasz DWA dokumenty.

## §1. Teza i dźwignia (FROZEN)

**Dźwignia = wyłącznie nowa reguła agregacji czasowej na TYM SAMYM predykacie
klatkowym W(t).** Cechy i progi klatkowe z FREEZE_WABIK są NIETYKALNE
(V_MOVE 0.30 · V_RAD_MAX 0.30 · DH_MIN_FLOOR 5.0 · R_ZONE 18 · WIN 1.0 s —
podłoga, która dała twarde zero FP, zostaje). **Przestrzeń wariantów (lista
zamknięta — żadnego fishingu):** (A) streak z tolerancją ≤K kolejnych klatek
niespełnienia, K ∈ {2, 3, 5}; (B) udział czasu: frac(W) ≥ θ w oknie przesuwnym
T_dec, θ ∈ {0.80, 0.85, 0.90}, T_dec ∈ {8, 10, 12} s; (C) zegar od początku
ciągłego segmentu śledzenia (naprawa stale-klatek brzegu) — ortogonalny,
składalny z A/B. Limit TP bez zmian: etykieta w ≤15 s śledzenia (spójność
z (i)). Semantyka odwołania przy złamaniu podłogi — bez zmian.
**Anty-overfit (FROZEN):** selekcja wariantu WYŁĄCZNIE na danych już
zalogowanych (S2 nogi (i) + NULL); potwierdzenie w locie WYŁĄCZNIE na
świeżych wariantach trajektorii, których reguła nigdy nie widziała
(W-LOITER r=9/11 vs 10/12 · W-STYCZNY b=6/10 vs 8/12 · W-ZBLIŻ 6.5/9 m
vs 7/8.5 · nowe ziarna; wpisy additive w manifeście). GRANICE UCZCIWOŚCI
z (i) bez zmian: wabik-jak-atak nierozróżnialny z definicji; jeden obiekt
w świecie naraz; klasyfikator nie steruje lotem.

## §2. Sesja S1 — selekcja offline + FREEZE (budżet: 0 bootów)

1. **`wabik_sig2.py`** (NOWY plik; wabik_sig.py v1 NIETYKALNY — porównywalność
   wstecz): rodziny A/B/C parametrycznie; replay na feedach S2 nogi (i)
   (6 TP + 3 FP + 2 ORB) i na NULL (115 epizodów ramienia percepcyjnego).
   Tabela WSZYSTKICH wariantów z pełnymi liczbami — także odrzuconych.
2. **KRYTERIUM SELEKCJI (FROZEN, litera):** wariant dopuszczony ⇔
   offline TP ≥5/6 (etykieta ≤15 s) ∧ FP-S2 0/3 ∧ ORB: etykieta końcowa
   ≠ „wabik" 2/2 (flaga-przed-odwołaniem dopuszczalna) ∧ NULL final-flag
   ≤13/115 (nie gorzej niż reguła (i) na populacji normalnej). Z dopuszczonych
   wybierz wariant o NAJMNIEJSZEJ zmianie względem (i) (liczba aktywnych
   mechanizmów A/B/C); tie-break: najniższy NULL final-flag.
3. Jeśli zwycięzca nie domyka W-ZBLIŻ w ≤15 s offline: rodzina ZBLIŻ wchodzi
   do lotu jako OPISOWA (flaga-kiedykolwiek), a zdania zamrożone S2 liczą się
   na pozostałych dwóch rodzinach (TP ≥3/4) — decyzja zapisana w FREEZE_WABIK2
   PRZY SELEKCJI, nigdy po locie.
4. **`results/WABIK2/FREEZE_WABIK2.md`:** zwycięski wariant z parametrami
   (jednostki jawne), sha narzędzia, pełna tabela selekcji, parametry świeżych
   wariantów lotu. **ŚMIERĆ S1 (prereg):** żaden wariant nie spełnia kryterium
   ⇒ STOP-ANEKS „reguła czasowa nieosiągalna przy tym szumie toru bez zmiany
   cech" — zero lotów wydanych, pozycja wraca do katalogu z tabelą jako
   aktywem. STOP-WABIK2-1: commit (narzędzie + FREEZE_WABIK2 +
   RAPORT_WABIK2_S1). Push = Olga.

## §3. Sesja S2 — potwierdzenie w locie (budżet ≤4 booty)

1. Bramka: origin zawiera STOP-WABIK2-1; FROZEN wykonaniem: komplet +
   FREEZE_WABIK (progi klatkowe) + FREEZE_WABIK2 (reguła). Każdy boot: reżim
   OPS (checklist + pin + profil + sonda). Loty UZBROJONE — twarde STOPy
   verbatim: breach ⇒ STOP; REFUSE(POS) ⇒ STOP; budżet ⇒ STOP; przerwania
   na granicach bootów. Jeden obiekt w świecie naraz.
2. **Epizody (8 w ≤4 bootach):** 6 TP świeżych (3 rodziny × 2 nowe warianty
   z §1) + 2 FP (c08_s03 wpis 1:1 + M-ŁUK na nowym ziarnie). Klasyfikator
   posthoc z percep_feed (nie steruje — równoważność werdyktowa jak w (i)).
3. **Zdania zamrożone:** **SUKCES = TP ≥5/6 z etykietą w ≤15 s ∧ FP 0/2**
   (przy wariancie ZBLIŻ-opisowym z §2.3: TP ≥3/4 na LOITER+STYCZNY ∧ ZBLIŻ
   raportowany opisowo ∧ FP 0/2); **FALSYFIKACJA PRZENOSZALNOŚCI = TP ≤2/6
   (odp. ≤1/4) na świeżych wariantach** ⇒ STOP-ANEKS (reguła przeuczona na
   zbiorze selekcji — wynik sam w sobie werdyktowy). Pomiędzy: strefa opisowa
   z dekompozycją per epizod i per mechanizm. Świadek-filtr obok każdego
   rachunku na GT.
4. **STOP-WABIK2-2:** commit (RAPORT_WABIK2_S2: tabela epizodów
   cechy/etykieta/czas-do-flagi vs offline-przewidywanie wariantu, sondy/piny,
   diff-stat, porcelain). Push = Olga. Po weryfikacji CC: ANEKS_WABIK2-1
   (werdykt, KSIĘGA, CO — zamknięcie wątku wabikowego w obu wynikach).

## §4. Predykcje CC (wskaźniki do KSIĘGI)

- **P-W2-1 (0.75):** selekcja offline znajduje wariant spełniający pełne
  kryterium §2.2 (mechanizmy naprawy celują wprost w trzy zmierzone przyczyny).
- **P-W2-2 (0.65):** zwycięzca potwierdza się na świeżych wariantach
  (SUKCES §3.3) — cięcie za przenoszalność z małej próby selekcyjnej.
- **P-W2-3 (0.80):** FP 0/2 w locie (podłoga klatkowa nietknięta).
- **P-W2-4 (0.85):** breach 0 / REFUSE 0 w całej nodze.

## §5. Budżet, higiena, nietykalne

Budżet nogi: S1 = 0 + S2 ≤4 ⇒ **sufit ≤4 booty**. Env `WABIK2_*`, katalog
`results/WABIK2/`, narzędzia WYŁĄCZNIE nowe pliki (driver-kopia z WABIK_S_DIR
dozwolona jak w (i)). **NIETYKALNE:** FREEZE_WABIK progi klatkowe (ich zmiana
= inna noga), wabik_sig.py v1, wabik_motion/manifest v1 (nowe wpisy additive),
percepcja w całości, sędzia 8ec0fcfb (świadek obok), osłona + piny, bench,
intruder_motion, worlds/*.sdf, kontroler + wagi, FREEZE_PERC2_OPS (reżim OPS
w każdym boocie). Raporty wstecz nietykalne; errata w przód.

Ratyfikacja: „ratyfikuję". Sygnały bez numeru wykonawca odrzuca.
