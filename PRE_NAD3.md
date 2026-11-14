# PRE_NAD3 — NADIR-III: zdegradowane źródło poprawki przy zadaniu do 20 m; jedna częstość (1 Hz), trzy poziomy błędu (1.0 / 1.75 / 2.75 m); tabela U′ z G unii 25 lotów i krawędziami na siatce klatki; τ* parametrem tabeli; bezpieczeństwo sądzone w każdym locie, dostępność progiem tylko w punkcie z zapasem; ≤ 22 booty

LiquidPatrol · CC · 14.11.2026 · łańcuch NAD3, po STOP-NAD3R
(300f0cd4 na origin). Do ratyfikacji sygnałem **„ratyfikuję
PRE_NAD3"**. Sygnały bez numeru albo nazwy odrzucasz.

## §1. Weryfikacja reconu przez CC (z repo, wykonaniem)

1. **Reprodukcja.** Sześć narzędzi `results/NAD3_RECON/tools/`
   uruchomionych na czystym klonie 300f0cd4 oddaje wszystkie siedem
   plików JSON bajt w bajt (`git status` pusty po przebiegu).
   Wierność replayu 13/13.
2. **R2 — własny kod.** r_max GT w tickach misji po fladze, liczony
   z `rama.jsonl` i `trace.jsonl` bez narzędzi wykonawcy: 13 lotów
   zgodnych z raportem do 0.01 m (c05_s01 19.59, c08_s01 25.57, lot
   długi 24.37). Promień > 20 m w 11 z 12 cięć.
3. **D4 — własny kod.** Okno przesuwne błędu EKF na wyciągach ULG.
   Tabela `r5_tabela.json` odtworzona z 12 cięć NADIR S4 do czwartej
   cyfry (0.6251 / 1.0722 / 1.4583 / 1.7894 / 2.0638 / 2.7657 /
   2.9781). Świeże G z NAD2 zgodne z raportem do trzeciej cyfry:
   12 cięć 2.144 przy 1.05 s i 3.033 przy 2 s; lot długi 2.216
   i 3.200. **Znalezisko potwierdzone:** od τ = 0.85 s tabela NAD2 nie
   ogranicza z góry lotów, które na niej poleciały.
4. **D2 — własny kod.** Odstęp klatek nadir 0.2 s w 100% klatek
   okna bez GNSS we wszystkich 13 lotach (551–552 klatki na cięcie,
   3002 w locie długim).
5. **D1, D3 i powierzchnia.** Wzory R1 przeliczone niezależnie:
   przy τ zrealizowanym wartości E_s / E_d dla r = 18, 20, 22, 24 m
   zgodne z tabelą raportu do 0.01 m. D3 jest poprawne i nie jest
   usterką: osłona nie zna kierunku błędu, więc błąd wchodzi raz do
   bariery i raz do `r_est`.
6. **Punkt, w którym CC nie zgadza się z raportem** (R4, „czego replay
   nie widzi", pkt 3). Raport przewiduje, że przy biasie do środka tor
   drona przesunie się o E na zewnątrz. Z kodu wynika co innego:
   track intruza powstaje jako p_corr + wektor z kamery
   (`harness/percep_proc.py:129-151`), a sieć dostaje różnicę
   track − p_corr (`bench/features.py:29`) i oddaje prędkość
   (`net_controller.py:117`). Stałe przesunięcie ramy znosi się więc
   w wejściu sieci. Przesunięcie toru może dać tylko zmiana Δ w czasie.
   Rozstrzygają loty — predykcja P-NAD3-4.

## §2. Rozliczenie reconu i błędy CC

- **Predykcje reconu:** R1 ✓, R2 ✓, R3 ✓, R4 ✗, R5 ✓, R6 ✗ — 4/6 przy
  sumie szans 4.25.
- **Błędy CC w PROMPT_NAD3_S0:**
  - wzór τ = (K+1)/f + 0.05 pomijał siatkę klatki 5 Hz i dodatek
    osłony 0.012 s; „4 Hz" nie leży na siatce kamery;
  - „bias na zewnątrz najgorszy dla bariery" — odwrotnie: dla
    przesłanki najgorszy jest bias do środka, na zewnątrz jest
    najgorszy dla dostępności;
  - rachunek §1 liczył tylko bezpieczeństwo. Z dostępnością wymaganie
    przy 20 m i 1 Hz spada z 3.0 m do 1.4 m.
- **Wykonawca:** wymiana decymatora przed wynikami, bias w obu
  kierunkach, punkt „dost" i τ zrealizowane zamiast wzoru CC —
  odchylenia nazwane i trafne. Przyjęte.

## §3. Rozstrzygnięcia CC (pytania 1–9 raportu)

1. **Geometria — (A), nowy manifest.** Intruz bliżej środka. Tabela
   `r4_margin` myli się o −4.5…+3.0 m, więc wybór komórek odpada.
   Promień sprawdzają loty nominalne przed degradacją (S2).
2. **Składanie błędu — (a):** U′ = 1.5 · (F_zn + E + G). Dla
   przyszłego źródła E będzie liczbą zmierzoną, jak F i G, i dostanie
   ten sam zapas. Wynik nogi czyta się wtedy wprost jako wymaganie.
3. **τ\* — (A), parametr tabeli.** Bez tego 1 Hz nie istnieje.
4. **G — (B), unia.** 12 cięć NADIR S4 + 12 cięć NAD2 S3 + lot
   długi. To nadal maksimum z próby, nie ograniczenie dowiedzione.
5. **Model w lotach — bias radialny w obu kierunkach.** Na zewnątrz
   mierzy dostępność, do środka bezpieczeństwo w pętli zamkniętej,
   czego replay nie widzi. Szum biały i błąd wolnozmienny zostają
   w replayu; w lotach ich nie ma — nazwana granica nogi.
6. **Granica punktu środkowego** — rozwiązana układem punktów (§4):
   środkowy leży między granicą dostępności a granicą bezpieczeństwa.
7. **Skok Δ — (A), bez ograniczenia tempa.** Kontrakt źródła w tej
   nodze: błąd ograniczony i wolnozmienny. Szum biały 2 m przy 1 Hz
   wychodzi poza zakres treningu (p95 3.37 m wobec p99.9 2.65 m)
   i nie leci.
8. **Decymacja — (B):** tylko częstości dzielące 5 Hz. W lotach jedna:
   1 Hz, bez gubienia (K = 0). Zależność od częstości i gubienia
   zostaje w replayu.
9. **Miejsce degradacji — (A):** `harness/nadir_obs.py:142-143`, za
   producentem, oba konsumenty dostają ten sam stan. Zmiana pliku
   producenta potwierdzona; `nadir_fix.py` nietknięty.

Dlaczego jedna częstość i trzy poziomy błędu, a nie trzy pary (f, E)
z raportu: przy trzech parach nie da się rozdzielić wpływu częstości
od wpływu błędu na dwunastu lotach. Stała częstość daje czystą
drabinę: pod granicą dostępności, między granicami, nad granicą
bezpieczeństwa.

## §4. FREEZE

- **Zadanie:** r_zad = 20.0 m. Manifest NAD3: RANGE0 = 10.0 m,
  DISK_R = 11.0 m, próg zawracania 8.5 m; reszta generatora bez zmian.
- **Częstość:** 1 Hz na sztywnej siatce slotów, K = 0.
- **Krawędzie τ:** 0.35 / 0.55 / 0.75 / 0.95 / 1.15 s (wielokrotność
  odstępu klatki + 0.15 s; zapas do krawędzi ≥ 0.11 s zamiast
  0.01 s). Dodatek osłony 0.012 s bez zmian.
- **τ\* = 1.15 s**, próg zatrzasku 21 ticków (τ\* − 2 · dt = 1.05 s).
- **G (unia 25 lotów, okno [flaga, zejście planowe], siatka 0.01 s,
  maksimum bieżące):** 0.8573 / 1.2703 / 1.6614 / 2.0590 / 2.3471 m.
  Liczby CC; wykonawca odtwarza je narzędziem w S1, różnica > 0.01 m
  ⇒ STOP.
- **F_zn:** z `freeze_U.json` bez zmian (para 0.1968–0.2577, jeden
  0.2562–0.4527).
- **Reguła:** U′ = 1.5 · (F_zn + E + G); u′ = U′ + Δ_D5; bariera
  R = R_E − d_stop − u′. Stałe R_E 32.0, d_stop 2.85, Δ_D5 1.524 bez
  zmian.
- **Granice przy r_zad i najgorszym polu:** dostępność E_d = 1.37 m,
  bezpieczeństwo E_s = 2.28 m.
- **Punkty:**
  - **P1 — E = 1.00 m.** Najniższa bariera 21.93 m; przy biasie na
    zewnątrz zapas do promienia zadania 0.93 m.
  - **P2 — E = 1.75 m.** Najniższa bariera 20.80 m; bias na zewnątrz
    daje odmowę, gdy dron przekroczy 19.05 m.
  - **P3 — E = 2.75 m.** Najniższa bariera 19.30 m, poniżej promienia
    zadania; bias na zewnątrz daje odmowę powyżej 16.55 m.
- **Model:** E = ±E_max · p̂_fix (kierunek od środka strefy przez
  poprawkę), stały znak w locie.
- **Komórki:** c05 i c10 z manifestu NAD3, ziarno s01. Każdy punkt:
  2 komórki × 2 kierunki biasu = 4 cięcia.
- Brak poprawki od wejścia w utratę ⇒ najgorsze pole, jak w NAD2.

Tabela P3 z założenia nie spełnia u′ ≤ m(r_zad). To punkt, w którym
osłona ma odmówić.

## §5. Architektura — różnice wobec NAD2

1. **Degradacja:** nowy moduł `harness/nad3_degrad.py` (z narzędzia
   reconu), wołany w `nadir_obs.py` między wyliczeniem poprawki
   a wysyłką. Parametry z env (`NAD3_DEGRAD`: E_max, znak, częstość,
   ziarno). Wyłączony ⇒ zwraca ten sam obiekt, datagram bajtowo jak
   w NAD2.
2. **Osłona:** reżim „nad3" w `r03/nadir_shield.py` obok „nad2":
   krawędzie, G, E i τ\* czytane z tabeli punktu
   (`results/NAD3/s1/freeze_U_P{1,2,3}.json`, sha w meta lotu). Reżim
   „nad2" i jego stałe zostają bez zmian.
3. **Certy:** nowe pliki P9/P5/P7_nad3; stare zostają. Asercje τ\* =
   ostatnia krawędź i próg całkowity w tickach liczone z tabeli.
   Asercja wykonalności u′ ≤ m(r_zad) jest zapisywana per punkt: ma
   być prawdziwa dla P1 i P2, fałszywa dla P3.
4. **Rejestr:** poprawka czysta i zdegradowana w osobnych polach,
   E per poprawka, ziarno w manifeście lotu.
5. **Nietknięte:** wagi sieci, EKF i parametry PX4, kanon percepcji
   misji, `r01/shield.py`, `harness/nadir_fix.py`, `freeze_U.json`
   NAD2, manifest znaczników v2, reguła zejścia D5.

## §6. Etapy, litera, śmierci, budżet

**S1 — budowa, FREEZE, certy (0 bootów).** Kod wg §5; narzędzie
FREEZE odtwarza G unii; trzy tabele z sumami; P9/P5/P7_nad3.
Wierność: nowy kod z parametrami NAD2 (krawędzie, G, τ\* = 1.05,
E = 0, 5 Hz) odtwarza zapis 13 lotów w 100%. **Śmierć S1:** cert nie
przechodzi ∨ wierność < 100% ∨ G nie odtwarza się w 0.01 m ∨ nowy
FAIL testów.

**S2 — geometria i smoke (≤ 4 booty).**
- 2 booty nominalne na manifeście NAD3, bez degradacji i bez cięcia:
  r_max GT w misji per epizod, jakość misji wg kryteriów nominałów
  NAD2.
- 1 boot: passthrough bitowy przy `NAD3_DEGRAD` wyłączonym.
- 1 boot: cięcie c05 w punkcie P1, bias na zewnątrz.
- **Bramka geometrii:** r_max ≤ 19.5 m w każdym epizodzie nominalnym.
  Przekroczenie ⇒ STOP, jedna korekta manifestu aneksem (intruz
  o 1 m bliżej), drugiej nie ma.
- **Śmierć S2:** naruszenie litery bezpieczeństwa ⇒ FAIL nogi;
  passthrough różny bitowo ⇒ STOP; sieć nie trzyma zadania na nowym
  manifeście (kryteria nominałów NAD2 niespełnione w ponad 1 z 8
  epizodów) ⇒ śmierć geometrii, noga zamknięta z wynikiem.
- Danych S2 nie wolno użyć do zmiany tabel. STOP po S2 i aneks CC
  przed bramką.

**S3 — bramka (≤ 17 bootów: 12 cięć + 2 nominały + 3 rezerwy
stanowiska).** 1 cięcie na boot, kontynuacja 110.5 s od `t_inj_sim`,
wyciąg ULG per boot do repo. Nominały z modułem degradacji włączonym
(P1) i GNSS obecnym.

*Litera bezpieczeństwa — każde naruszenie w dowolnym epizodzie to FAIL
nogi:*
- (B1) e′ ≤ U′ w każdym ticku utraty, e′ = |p_corr zdegradowane −
  GT(t próbki EKF)|;
- (B2) r_GT < R_E przez cały lot;
- (B3) `r_est` osłony = |p_corr zdegradowane| w 100% ticków KONT;
- (B4) po REFUSE zejście wg reguły, `nav_state` 14, failsafe 0, zero
  breach;
- (B5) w nominałach zero REFUSE(POS) fałszywych.

*Dostępność:*
- **P1 — próg:** co najmniej 3 z 4 cięć bez REFUSE w misji, track
  i pasmo wg D1 z NAD2.
- **P2, P3 — opisowo.** Sądzi się zgodność z regułą: REFUSE(bariera)
  zapada wtedy i tylko wtedy, gdy `r_est` przekroczył barierę z tabeli
  punktu. REFUSE(τ\*) w którymkolwiek locie jest znaleziskiem
  (spóźniona poprawka), nie naruszeniem.

*Obserwable (bez progu):* max e′/U′ per lot; τ zrealizowane; skok Δ
per poprawka; odrzucenia bramki predykcji tracku; różnica r_max GT
między lotami tej samej komórki i punktu przy przeciwnym znaku biasu.

**Werdykt:**
- **V-A:** zero naruszeń B1–B5 i próg P1 spełniony — wymaganie
  „1 Hz, błąd do 1.0 m przy zadaniu do 20 m" zmierzone w pętli;
  granice 1.37 m i 2.28 m pozostają rachunkiem sprawdzonym w dwóch
  punktach kontrolnych.
- **V-B:** zero naruszeń, próg P1 niespełniony — bezpieczeństwo
  trzyma, dostępność przy 1 m i 1 Hz niepotwierdzona; wynik
  negatywny z mechanizmem.
- **V-C:** jakiekolwiek naruszenie B1–B5 — FAIL nogi.

**Budżet:** ≤ 22 booty (S2 4 + S3 17 + 1 na korektę geometrii).
Po FAIL bramki trzeciego podejścia w tej architekturze nie ma.

## §7. Zakres zdania końcowego

SITL, jedna sceneria, błąd wstrzykiwany i ograniczony z konstrukcji,
bias o stałym znaku, źródłem nadal są znaczniki. Noga nie mówi nic
o ogonie błędu prawdziwego dopasowania do mapy ani o szumie
szybkozmiennym. Mówi, jaki kontrakt musi spełnić źródło, żeby dowód
i osłona NAD2 działały bez zmian.

## §8. KSIĘGA (append-only przy commicie §CO)

```
## NADIR-III — PRE (PRE_NAD3, 14.11.2026)
- Recon rozliczony: P-NAD3-R1 ✓, R2 ✓, R3 ✓, R4 ✗, R5 ✓, R6 ✗ —
  4/6 przy sumie szans 4.25. CC odtworzył JSON-y reconu bajt w bajt
  i własnym kodem: r_max 13 lotów (do 0.01 m), tabelę r5 (do 4.
  cyfry), świeże G NAD2 (do 3. cyfry), odstęp klatek 0.2 s.
- ✗ projektowe CC w PROMPT_NAD3_S0: wzór τ bez siatki klatki 5 Hz
  i dodatku osłony; odwrócony kierunek najgorszego biasu; rachunek
  wymagań bez dostępności (przy 20 m i 1 Hz: 3.0 m → 1.37 m).
  Lekcja: wymaganie na źródło liczy się z obu stron — przesłanki
  i odmowy — i na siatce czasu przyrządu, nie wzoru.
- Dopisek do NAD2 (bez zmiany werdyktu): tabela G z NADIR S4 nie
  ogranicza z góry lotów NAD2 od τ = 0.85 s (do +0.15 m przy 1.05 s,
  +0.43 m przy 2 s w locie długim). W NAD2 τ nie przekroczyło 0.40 s,
  a przesłanką była suma e_corr ≤ U.
- Predykcje CC, przed pierwszym lotem:
  - P-NAD3-1 (0.80): bramka geometrii przechodzi na pierwszym
    manifeście (r_max ≤ 19.5 m w 8/8 epizodów nominalnych).
  - P-NAD3-2 (0.75): P1 — 4/4 cięcia bez REFUSE w misji.
  - P-NAD3-3 (0.90): zero przekroczeń przesłanki w 12 cięciach,
    max e′/U′ ≤ 0.75.
  - P-NAD3-4 (0.65): bias do środka nie przesuwa toru — różnica
    r_max GT między lotami o przeciwnym znaku biasu < 1.0 m w co
    najmniej 4 z 6 par.
  - P-NAD3-5 (0.75): P3, bias na zewnątrz — REFUSE(bariera) w 2/2,
    B4 czyste.
  - P-NAD3-6 (0.60): P2 — najwyżej 1 REFUSE w 4 cięciach.
  - P-NAD3-7 (0.70): zero REFUSE(τ*) w 12 cięciach.
```

## §9. KIERUNKI_PO_PLANIE (append-only przy commicie §CO)

```
## Dopisek stanu katalogu — 14.11.2026 (CO-NAD3-0, PRE_NAD3)
- **NADIR-III — otwarta, PRE ratyfikowany.** Zdegradowane źródło
  poprawki: znaczniki z wstrzykniętym błędem ograniczonym, 1 Hz,
  zadanie do 20 m (nowy manifest, intruz bliżej środka), trzy
  poziomy błędu 1.0 / 1.75 / 2.75 m. Cel: zmierzony kontrakt dla
  przyszłego źródła absolutnego bez znaczników.
- Recon (0 bootów): wymaganie wyznacza dostępność, nie
  bezpieczeństwo — osłona liczy błąd źródła dwukrotnie. Przy 20 m
  i 1 Hz: dostępność do 1.37 m, bezpieczeństwo do 2.28 m.
- Budżet ≤ 22 booty. Dopasowanie obrazu do mapy otwiera się dopiero
  z liczbami tej nogi jako bramką wejścia.
```
