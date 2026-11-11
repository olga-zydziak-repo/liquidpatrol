# PRE_NAD2 — NADIR-II: lot bez GNSS pod ważnym dowodem zawierania; przesłanka mierzona na błędzie pozycji poprawionej; litera przyjęcia Z2 z korektą kursu T1; osłona w ramie poprawionej; bezpieczeństwo i dostępność sądzone osobno; świeża bramka 12 + 4; ≤ 22 booty

LiquidPatrol · CC · 11.11.2026 · łańcuch NAD2, po STOP-NAD2R
(641a5ee8 na origin). Do ratyfikacji sygnałem **„ratyfikuję
PRE_NAD2"**. Sygnały bez numeru albo nazwy odrzucasz.

## §1. Weryfikacja reconu przez CC (z repo, wykonaniem)

1. **CO-N5:** ANEKS_NADIR-5 byte-check PASS (286d2ac0…); bloki
   KSIĘGI i KIERUNKÓW verbatim, append-only; predykcje reconu
   w KSIĘDZE przed pierwszym wynikiem; recon dotknął wyłącznie
   `results/NAD2_RECON/`; 0 bootów.
2. **R1 — własny kod na wyciągach ULG.** 27 253 ticki misji bez GNSS
   dopasowane po wartości w 100%. Próbka EKF ticku jest o 8 ms
   starsza od zegara ticku (zakres −24…+12 ms); opóźnienie klatki:
   mediana 8 ms, p95 16 ms. Błąd pozycji poprawionej z GT w chwili
   próbki EKF: p50 0.121 / p95 0.249 / p99 0.399 / **max 0.677 m**,
   bez składowej zależnej od prędkości. **Hipoteza CC o spóźnieniu
   ok. 0.09 s jest obalona**; przesunięcie `gt_judge` nie dotyczy
   próbek ticku.
3. **R2 — okno przesuwne, własny kod:** 0.625 / 1.072 / 1.458 /
   1.789 / 2.063 m dla horyzontów 0.25 / 0.45 / 0.65 / 0.85 / 1.05 s
   — zgodne z raportem do trzeciej cyfry.
4. **R3 — własna pętla replayu** (geometria z `harness.nadir_fix`):
   bieżąca litera odtwarza 27 800 zapisanych decyzji w 100%
   (|Δp_fix| ≤ 5e-5 m). T1Z2C0 w oknie bez GNSS: 6602 klatki, 0 bez
   poprawki, 6591 par, 11 poprawek jednym znacznikiem; błąd
   zakotwiczenia pary per koszyk 0.190 / 0.235 / 0.230 / 0.211 /
   0.258 m (raport: 0.197 / 0.237 / 0.234 / 0.211 / 0.258 — różnica
   ≤ 0.007 m).
5. **R5 — własny rachunek:** 27 253 ticki, 0 przekroczeń przesłanki
   (max e_corr′/U 0.399), 0 REFUSE, zapas bariery min 1.71 m
   (c11_s02), τ max 0.232 s.
6. **Znalezisko wykonawcy potwierdzone:** w S4 `r_est` osłony równał
   się |p_EKF| (do 0.0006 m w każdym ticku), a od |p_corr| odbiegał
   do 7.0 m (mediana 0.96 m). Osłona S3/S4 sądziła promień z surowego
   EKF, P9_nadir zakładał pozycję poprawioną. Fikstura P5_nadir
   i replikacja certów przez CC tego nie widziały — obie porównują
   lustro z produkcją na tych samych wejściach.

## §2. Rozstrzygnięcia CC po reconie

1. **Wariant: T1Z2C0, reguła A** — z prerejestrowanej reguły wyboru,
   bez wyjątku. (T0, Z2) jest liczbowo równy i prostszy; kolejność
   zapisana przez CC go pominęła i zostaje, jak zapisano.
2. **Obwiednia trybu „jeden" z puli 11 obserwacji — odrzucona.**
   F_jeden bierze się z rozwiązania jednym znacznikiem (z T1)
   policzonego we wszystkich 6602 klatkach okna bez GNSS: max per
   koszyk 0.253 / 0.329 / 0.440 / 0.442 / 0.340 m (n 550 / 2632 /
   3034 / 366 / 20). Zgodne z raportem dla T1Z0 (0.437 m).
3. **Dostępność sądzi decyzja osłony (REFUSE), nie rachunek
   u′ ≤ m.** m = R_E − d_stop − r_max scenariusza, a r_max pochodzi
   z 1–3 wcześniejszych epizodów. Loty S4 odbiegały od niego w obie
   strony (c10_s01 +3.2 m, c11_s01 +1.8 m, c08_s02 −2.9 m), więc
   u′ ≤ m nie rozstrzyga, czy osłona odmówi. Rozstrzyga zapas
   bariery przy faktycznym promieniu: w replayu S4 najmniejszy mają
   c11_s02 (1.71 m), c11_s01 (1.86 m) i c10_s01 (2.44 m). Jeśli
   c08_s02 albo c11_s02 dolecą do promienia historycznego (26.13–
   26.16 m), bariera (26.03–26.39 m) zostawi im od −0.13 do
   +0.26 m — stąd próg dostępności 10 z 12, bez wskazywania komórek
   z góry.
   Definicja „komórki dostępnej" z promptu reconu (CC) mieszała oba
   rachunki; u′ wobec m zostaje obserwablą.
4. **Wejście osłony w ramie poprawionej jest naprawą obowiązkową**
   (pytanie 1 raportu): bez niej żadna tabela nie czyni P9 ważnym.
5. **τ* = 1.05 s** przyjęte (pytanie 4). Przesłanką jest suma —
   e_corr ≤ U; składniki (a ≤ 1.5 · F, przyrost ≤ 1.5 · G) są
   obserwablami (pytania 3, 5).

## §3. Architektura — różnice wobec NADIR-I

1. **Litera przyjęcia Z2:** ID z manifestu v2 ∧ środek w stożku
   (krawędź ≥ 0.10) ∧ bok ≥ 16 px ∧ reszta < s/2 ∧ najbliższy
   znacznik r_h < 10 m. Partner pary bez limitu r_h (największa
   baza). Strażnik spójności pary bez zmian. Koszyk = ⌊r_h / 2⌋ ∈
   {0…4}.
2. **Korekta kursu T1:** poprawka jednym znacznikiem obraca wektor
   poziomy o `dpsi` ostatniej przyjętej pary, jeśli para ma ≤ 2 s;
   inaczej bez korekty. Datagram ramy niesie tryb poprawki.
3. **Rama B+ bez zmian** (próbka EKF przy przybyciu klatki — C0).
4. **Osłona:** tabela U(przedział τ, koszyk, tryb) zamiast
   ε_fix_freeze + ε_b(⌊τ⌋); bariera R = R_E − d_stop − (U + Δ_D5);
   τ > τ* ⇒ REFUSE(τ*). **W fazie KONT wszystkie wejścia pozycyjne
   osłony (pozycja, cel; r_est liczony z pozycji) są w ramie
   poprawionej, a wyjście osłony jest przeliczane do ramy EKF przed
   wysłaniem.** W NOMINAL wejścia bez zmian. Przy `NADIR_MODE=0`
   passthrough bitowy.
5. **Nietknięte:** wagi sieci, EKF i parametry PX4, kanon percepcji
   misji, jądro `r01/shield.py`, R_nom, d_stop, Δ_D5, manifest v2.

## §4. FREEZE (z danych S4; sądzą wyłącznie świeże loty)

- **Przedziały τ:** [0, 0.25], (0.25, 0.45], (0.45, 0.65], (0.65,
  0.85], (0.85, 1.05] s. Przedział wybiera większa z wartości:
  τ osłony i horyzont prawdziwy.
- **G (przyrost błędu EKF, okno przesuwne, poziomo):** 0.6251 /
  1.0722 / 1.4583 / 1.7894 / 2.0638 m.
- **F_para (błąd zakotwiczenia, koszyki 0–4):** 0.1968 / 0.2372 /
  0.2372 / 0.2372 / 0.2577 m (`r5_tabela.json`).
- **F_jeden (koszyki 0–4):** 0.253 / 0.329 / 0.440 / 0.442 /
  0.442 m (§2.2 po maksimum bieżącym; liczby CC — wykonawca
  odtwarza je narzędziem w S1; różnica > 0.01 m ⇒ STOP).
- **Reguła:** U = 1.5 · (F + G); u′ = U + Δ_D5. Pole o n < 100
  bierze maksimum z wartości własnej, maksimum bieżącego niższych
  koszyków i puli trybu.
- **Zakres wartości:** u′ przy τ ≤ 0.25 s od 2.757 m (para, koszyk
  0) do 3.125 m (jeden, koszyki 3–4); bariera 26.03–26.39 m.
- Brak poprawki od wejścia w utratę ⇒ najgorsze pole (jeden,
  koszyk 4) — jak w NADIR-I.

Na danych S4 tabela daje max e_corr′/U = 0.40 i zapas bariery
≥ 1.71 m. To warunek konieczny, nie dowód.

## §5. Etapy, litera, śmierci, budżet

**S1 — budowa i certy (0 bootów).** Kod wg §3; narzędzie FREEZE
z sumą tabeli; P9/P1/P5/P7_nad2 (nowe pliki; stare zostają); P5_nad2
z **obligacją wejścia**: w replayu ścieżki drivera na tickach S4
`r_est` osłony = |p_corr| w 100% ticków KONT, a mutant ze starą
ścieżką jest wykrywany. Wierność: nowy kod z parametrami starej
litery odtwarza zapis S4 w 100%. Pełny zestaw testów PASS modulo
zastany. **Śmierć S1:** cert nie przechodzi ∨ ostrość nie trzyma ∨
wierność < 100% ∨ obligacja wejścia nie przechodzi ∨ nowy FAIL
testów ∨ F_jeden nie odtwarza się. CC replikuje provery po pushu.

**S2 — smoke (≤ 3 booty).** (1) Cięcie c11_s02 (najmniejszy zapas
bariery) pod nową literą; (2) nominał przy `NADIR_MODE=0`,
`KONT_MODE=0` — passthrough bitowy; (3) rezerwa. Sprawdza się: replay
offline odtwarza poprawki z lotu w 100%, tryb w datagramie, `r_est`
= |p_corr| w KONT. Danych smoke nie wolno użyć do zmiany tabeli.
**Śmierć S2:** naruszenie litery bezpieczeństwa (niżej) ⇒ FAIL nogi
już tutaj; brak wierności albo passthrough różny bitowo ⇒ STOP.
REFUSE w smoke jest obserwacją, nie śmiercią.

**S3 — bramka (≤ 19 bootów: 12 cięć + 4 nominały + 3 rezerwy
stanowiska).** Siatka i kolejność jak NADIR S4; 1 cięcie na boot;
kontynuacja liczona od `t_inj_sim`, nastawa drivera 110.5 s;
wyciąg ULG per boot do repo.

*Litera bezpieczeństwa — każde naruszenie w dowolnym epizodzie to
FAIL nogi:*
- **(B1)** e_corr(tick) ≤ U(przedział, koszyk, tryb) w każdym ticku
  fazy KONT; e_corr = |p_corr − GT(czas próbki EKF ticku)|, poziomo;
- **(B2)** margines do R_E > 0 w każdej chwili (GT);
- **(B3)** `r_est` osłony = |p_corr| (do 1e-3 m) w każdym ticku KONT;
- **(B4)** offboard do końca, zero natywnego failsafe, zero
  fałszywych REFUSE(POS); każdy REFUSE zgodny z regułą (bariera
  albo τ*) i zakończony zejściem;
- **(B5)** nominały: zero fałszywych wejść i zero REFUSE.

*Litera dostępności:*
- **(D1)** cięcie dostępne ⇔ kontynuacja ≥ 110 s od `t_inj_sim` ∧
  track/orbita ∧ zero REFUSE. **Próg: ≥ 10 z 12.** Poniżej progu —
  FAIL nogi (dowód ważny, zdolność niedostępna).

*Obserwable bez progu:* u′ wobec m per tick, a wobec 1.5 · F,
przyrost wobec 1.5 · G, rozkład τ i przedziałów, tryby, klatki bez
poprawki, zapas bariery, bias kursu, tempo.

Kampania dolatuje siatkę niezależnie od wyniku (pomiar); werdykt
mechanicznie w raporcie, bez strojenia. Stanowisko: bramka zdrowia
(przyrząd A ≥ 0.90, timesyncd zatrzymany), bramka tempa bootu 0.93,
żadnych aplikacji okienkowych poza terminalem.

**S4 — lot długi (opcjonalny; tylko po PASS bramki i osobnym
sygnale Olgi; ≤ 2 booty poza budżetem nogi).** Jedno cięcie
z kontynuacją 600 s, obserwacyjnie: czy błąd i bias kursu zostają
płaskie poza 110 s. Litera bezpieczeństwa obowiązuje jako STOP.

**Budżet nogi: ≤ 22 booty** (S2 3 + S3 19). STOPy globalne verbatim:
**breach ⇒ STOP; REFUSE(POS) fałszywy ⇒ STOP; budżet ⇒ STOP.**

**Po FAIL bramki trzeciego podejścia w tej architekturze nie ma.**
Wątek lotu bez GNSS zostaje wtedy na zdaniu „110 s zmierzone",
a dalszy krok wymagałby zmiany estymatora — poza katalogiem.

## §6. Predykcje (prereg)

- P-NAD2-1 (0.75): S1 przechodzi w całości bez zmiany projektu.
- P-NAD2-2 (0.80): litera bezpieczeństwa bramki bez naruszeń.
- P-NAD2-3 (0.85): dostępność ≥ 10 z 12.
- P-NAD2-4 (0.45): dostępność 12 z 12.
- P-NAD2-5 (0.60): bramka PASS.
- P-NAD2-6 (0.90): breach 0 w całej nodze.

W dwóch ostatnich nogach szanse CC były zawyżone (NADIR 2/4 przy
sumie 2.90; recon NAD2 3/5 przy 3.10). Ryzyka nazwane: ogon zrywów
znany z jednej kampanii; pętla zamknięta zmienia się przez nową
literę i nową ramę osłony; stanowisko.

## §7. KSIĘGA i KIERUNKI (append-only przy commicie §CO)

```
## NADIR-II — recon rozliczony, otwarcie nogi (PRE_NAD2, 11.11.2026)
- Recon STOP-NAD2R (0 bootów): kierunek żyje, reguła wyboru wskazała
  T1Z2C0 · A. CC przeliczył R1, R2, R3 i R5 własnym kodem: zgodność
  co do trzeciej cyfry (F pary do 0.007 m); replay litery CC
  odtwarza 27 800 decyzji z lotu w 100%.
- P-NAD2-R1 (0.75) — ✗: opóźnienia klatki nie ma (mediana 8 ms, p95
  16 ms). ✗ metodyczne CC: hipoteza zbudowana na przesunięciu
  gt_judge bez sprawdzenia, że dotyczy ono próbek ticku. Parowanie
  z ANEKS_NADIR-5 §1.5 rozstrzygnięte: GT w chwili próbki EKF, max
  błędu pozycji poprawionej 0.677 m, ponad sumę składników 2 ticki
  (nie 40).
- P-NAD2-R2 (0.80) ✓, P-NAD2-R3 (0.65) ✓, P-NAD2-R4 (0.35) ✓,
  P-NAD2-R5 (0.55) ✗ (sam T1 zostawia 0.437 m). Recon: 3/5 przy
  sumie szans 3.10.
- Znalezisko wykonawcy, potwierdzone przez CC: w S3/S4 osłona
  liczyła r_est z surowego EKF (do 7.0 m od pozycji poprawionej,
  mediana 0.96 m), a P9_nadir zakładał pozycję poprawioną. ✗
  projektowe CC (PROMPT_NADIR_S3 nie nazwał wejścia osłony; replika
  certów i fikstura P5 porównują lustro z produkcją na tych samych
  wejściach) i ✗ wykonawcy (implementacja). Werdykt S4 bez zmian;
  warunek dowodu nie był spełniony także po stronie wejścia. Lekcja:
  każdy cert osłony ma obligację wejścia — wielkość z twierdzenia
  musi być tą, która w locie trafia do osłony.
- ✗ projektowe CC ×3 w prompcie reconu: kolejność „najprostszy"
  pominęła (T0, Z2); reguła „n < 100 dziedziczy wyższy koszyk"
  niewykonalna dla trybu jeden w Z2 (rozstrzygnięte w PRE §2.2);
  „komórka dostępna" z warunkiem u′ ≤ m — rachunkiem na promieniu
  historycznym z 1–3 epizodów, od którego loty S4 odbiegają
  o −2.9…+3.2 m; o odmowie rozstrzyga zapas bariery przy promieniu
  faktycznym (PRE §2.3).
- Wykonawca: sam wykrył i odrzucił własną wersję replayu zawyżającą
  dostępność w ok. 10% ticków; odstępstwa od litery nazwane wprost;
  R4 — zrywy to błąd prędkości z przepływu przy obrocie kadłuba
  (ω ≥ 0.5 rad/s), przyjmowany przez EKF bez odrzuceń.
- NADIR-II otwarta ratyfikacją PRE_NAD2. Predykcje: P-NAD2-1 (0.75)
  S1 w całości; P-NAD2-2 (0.80) litera bezpieczeństwa bez naruszeń;
  P-NAD2-3 (0.85) dostępność ≥ 10/12; P-NAD2-4 (0.45) dostępność
  12/12; P-NAD2-5 (0.60) bramka PASS; P-NAD2-6 (0.90) breach 0.
```

```
## Dopisek stanu katalogu — 11.11.2026 (CO-NAD2-0, PRE_NAD2)
- **NADIR-II — OTWARTA** (nowa pozycja po NADIR): ważny dowód
  zawierania dla lotu bez GNSS na znacznikach naziemnych. Przesłanka
  na błędzie pozycji poprawionej (tabela z danych S4, zapas 1.5),
  litera przyjęcia bez dziur (Z2 + T1), osłona w ramie poprawionej;
  bezpieczeństwo i dostępność sądzone osobno (próg dostępności
  10/12). Świeża bramka 12 + 4, budżet ≤ 22 booty. Po FAIL bramki
  trzeciego podejścia w tej architekturze nie ma.
```

## §CO

Bramka: origin/master == **641a5ee8** i sygnał „ratyfikuję PRE_NAD2"
w wiadomości Olgi. Jeden commit [CO-NAD2-0]: korzeń `PRE_NAD2.md`
verbatim (byte-check sha256 z wiadomości CC) + oba bloki §7
append-only. Potem PROMPT_NAD2_S1. Push = Olga.
