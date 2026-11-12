# ANEKS_NAD2-4 — lot długi rozliczony: 600.5 s bez GNSS w jednym locie, zero odmów w misji, B1–B4 bez naruszeń; błąd pozycji poprawionej płaski (p95 0.19–0.25 m) przy błędzie własnym EKF do 20.6 m; bias kursu dochodzi do ok. 5° i w drugiej połowie lotu nie ma trendu; noga NADIR-II bez otwartych pozycji

CC · 12.11.2026 · łańcuch NAD2, po STOP-NAD2-4 (65a1b1aa na origin).
Rozlicza lot obserwacyjny z PRE_NAD2 §5 S4 (1 boot z 2, poza
budżetem nogi). Nie zmienia żadnej liczby zamrożonej, więc
ratyfikacji nie wymaga. Sygnały bez numeru albo nazwy odrzucasz.

## §1. Weryfikacja CC z repo (wykonaniem, własnym kodem)

1. **Zamknięcia:** ANEKS_NAD2-2 (8b8d8d30…) i ANEKS_NAD2-3
   (210d2d8d…) byte-check PASS. Bloki KSIĘGI verbatim, w kolejności:
   zamknięcie bramki, predykcje lotu długiego (zapisane przed lotem),
   decyzja o ruchu intruza. Blok KIERUNKÓW verbatim. Oba pliki
   append-only.
2. **Kod:** diff bd975df5…65a1b1aa pusty dla `harness/`, `r01/`,
   `r03/`, tabeli, kroku drivera, launchera, analizatora,
   `bench/scenarios.py` i manifestu bramki. W `nad2_flight.py`,
   `nad2_boot.sh` i `nad2_ulg.py` zmieniło się 6 linii — odczyt env
   z wartościami domyślnymi bramki; doszły narzędzia S4. Meta lotu:
   tabela 6a118fd4, krok c6844f98, fix 3baa340e jak w bramce; driver
   7d86609e (w bramce 35f2dd70 — różnica to dwie linie env).
3. **Boot:** jeden, ważny; bramka zdrowia GO (0.948), tempo bootu
   0.978 przy progu 0.93. Rezerwa nieużyta.
4. **Ruch intruza:** poleciało wahadło (manifest 967e6799, pozycja 2
   ANEKS_NAD2-3). Komendy z `gt_intruder.jsonl` zgadzają się ze
   wzorem wahadła do 1e-4 m przez 644 s; od wzoru pozycji 1
   odbiegają do 28 m. Krok komendy odpowiada v·dt przy v = 1.0 m/s
   (największy 0.092 m przy odstępie 0.092 s), tor lustrzany
   względem 200., 400. i 600. sekundy wzoru. Droga w fazie bez GNSS
   600 m, w ostatnich 100 s 99.9 m. Skoków nie było.
5. **Litera** (kontynuacja 600.516 s od `t_inj_sim`):
   - (B1) 12 246 ticków z tabelą (12 077 w misji, 169 w zejściu),
     **0 przekroczeń**; max e_corr/U 0.412, max e_corr 0.54 m;
   - (B2) margines do R_E min 7.635 m;
   - (B3) `r_est` = |p_corr| w 12 270/12 270 ticków KONT; w NOMINAL
     rama EKF w 700/700;
   - (B4) `nav_state` 14 i failsafe 0 od flagi do przyziemienia
     (1211 próbek ULG); zdarzeń breach i REFUSE(POS) 0; 26 ticków
     KONT_REFUSE, wszystkie po komendzie zejścia, z przyczyną τ*.
6. **Wierność:** 3941 klatek — decyzja zgodna w 100%; 3244 przyjęte
   poprawki — tryb i koszyk zgodne w 100%, |Δp_fix| ≤ 5e-5 m;
   bariera z logu = `r_nad2` w 12 244/12 244 ticków.
7. **Misja:** track 1.000, pasmo 0.981; zero REFUSE; τ max 0.400 s
   (jedna klatka bez poprawki, 4 ticki w drugim przedziale); tryb
   „jeden" w 12 tickach z 12 077; zapas bariery min 1.864 m; horyzont
   prawdziwy nie przekroczył τ + 0.012 s.
8. **Okna po 100 s od cięcia:**
   - e_corr p95: 0.253 / 0.202 / 0.196 / 0.193 / 0.247 / 0.203 m;
     max e_corr/U: 0.35 / 0.31 / 0.41 / 0.34 / 0.29 / 0.28;
   - składniki przesłanki: przyrost EKF do 0.49, zakotwiczenie do
     0.67 dopuszczalnego; żaden nie ma trendu w czasie (przyrost p95
     0.14–0.18 w każdym oknie);
   - błąd własny EKF, mediana: 2.4 / 4.9 / 8.5 / 10.9 / 13.1 /
     17.0 m; max 20.6 m; nachylenie 2.9 m na 100 s;
   - bias kursu z par, mediana: −0.04 / +2.68 / +3.80 / +5.04 /
     +4.51 / +5.28°; nachylenie +2.1° na 100 s w pierwszych 300 s,
     +0.2° na 100 s w ostatnich 300 s (przedział 90%: −0.5 do +0.6);
   - zapas bariery min: 2.45 / 3.56 / 4.28 / 3.90 / 1.86 / 4.00 m.
9. **Zgodność z raportem pełna** — liczby raportu odtworzone co do
   zaokrąglenia.

## §2. Wynik

1. **Lot doleciał 600.5 s bez GNSS, bez odmowy osłony i bez
   naruszenia litery bezpieczeństwa.** Przesłanka dowodu trzymała
   w każdym ticku przez dziesięć minut; największe zużycie granicy
   41% (bramka: 37%).
2. **Błąd pozycji poprawionej nie rośnie z czasem,** choć błąd własny
   estymatora rośnie w przybliżeniu liniowo i w dziesiątej minucie
   przekracza połowę promienia strefy. Przesłanka zużywa przyrost
   między poprawkami, nie dryf bezwzględny, a tego przyrostu czas
   lotu nie powiększył.
3. **Bias kursu nie jest stały** — P-NAD2-L4 chybiona. Przez
   pierwsze 300 s rósł o ok. 2° na 100 s, do ok. 5°; w ostatnich
   300 s trend jest nieodróżnialny od zera. Na e_corr się nie
   przełożył: para znaczników wyznacza obrót i zdejmuje go
   z poprawki, a przyrost EKF między poprawkami nie urósł. Rama
   koryguje pozycję, nie kurs. Co bias robi po 600 s, jest
   niezmierzone — to nazwana granica zdania o braku limitu czasu.
4. **Dopisek do zdania z ANEKS_NAD2-2 §3:** zmierzone jest 110 s na
   lot w dwunastu lotach i 600 s w jednym locie (c10_s01, intruz
   w ruchu przez cały czas).

To jeden lot w jednej komórce: pokazuje brak narastania błędu
w czasie, nie zastępuje próby wielu lotów i nie zmienia werdyktu
bramki. Pozostałe granice bez zmian: SITL, jedna sceneria, pełna
widoczność znaczników.

## §3. Rozliczenia

- **Predykcje:** P-NAD2-L1 (0.70) ✓; L2 (0.85) ✓; L3 (0.75) ✓ —
  0.203 m wobec progu 0.32 m; L4 (0.60) ✗ — 5.28° wobec 3°.
- **✗ projektowe CC:** próg ciągłości 1e-6 m w ANEKS_NAD2-3 był
  ostrzejszy niż rozdzielczość generatora, który zaokrągla początki
  odcinków do 1e-4 m. Przedłużenie tym samym generatorem i ziarnem
  odpadło o 2e-5 m na jednym szwie odcinków. Skoki tej samej natury
  (do 1.6e-4 m) ma wzór bramki; ten sam próg odrzuciłby 5 z 80
  ruchomych epizodów manifestu bramki. Poleciało wahadło — zgodnie
  z literą aneksu i bez szkody dla pomiaru, ale pozycja 1 odpadła
  przez mój próg, nie przez wadę wzoru.
- **Wykonawca:** STOP przed lotem zamiast intruza ze skokami;
  przejście na pozycję 2 literą aneksu, bez naginania progu; własne
  kryterium kroku komendy w teście na sucho zmienione po pierwszym
  przebiegu i nazwane w raporcie (ciągłość sądzi T2). Usterka
  etykiety bez wpływu na wynik: pole `pozycja_aneksu` w
  `testy_s4.json` ma wartość 1 przy manifeście wahadła; manifest
  i raport podają pozycję 2.

## §4. KSIĘGA (append-only przy commicie §CO)

```
## NADIR-II — lot długi rozliczony (ANEKS_NAD2-4, 12.11.2026)
- Lot L (c10_s01, 1 boot, poza budżetem nogi): 600.516 s bez GNSS,
  0 REFUSE w misji, B1–B4 bez naruszeń — B1 12 246 ticków, max
  e_corr/U 0.412, max e_corr 0.54 m; margines do R_E min 7.635 m;
  zapas bariery min 1.864 m; intruz w ruchu cały lot (wahadło,
  600 m drogi). CC przeliczył całość własnym kodem z repo; zgodność
  z raportem pełna.
- Okna po 100 s: e_corr p95 0.19–0.25 m przez cały lot (płasko)
  przy błędzie własnym EKF rosnącym ok. 2.9 m na 100 s, do 20.6 m;
  składniki przesłanki bez trendu (przyrost do 0.49, zakotwiczenie
  do 0.67 dopuszczalnego). Bias kursu z par: −0.04° → +5.28°;
  +2.1° na 100 s w pierwszych 300 s, w ostatnich 300 s trend
  nieodróżnialny od zera (+0.2, przedział 90%: −0.5 do +0.6).
  Rama koryguje pozycję, nie kurs; po 600 s niezmierzone.
- P-NAD2-L1 (0.70) ✓, P-NAD2-L2 (0.85) ✓, P-NAD2-L3 (0.75) ✓,
  P-NAD2-L4 (0.60) ✗ (5.28° > 3°). Lot długi: 3/4 przy sumie szans
  2.90.
- ✗ projektowe CC: próg ciągłości 1e-6 m (ANEKS_NAD2-3) poniżej
  rozdzielczości generatora (początki odcinków zaokrąglane do
  1e-4 m) — przedłużenie generatorem odpadło o 2e-5 m; ten sam próg
  odrzuciłby 5 z 80 ruchomych epizodów manifestu bramki. Poleciało
  wahadło, bez szkody dla pomiaru. Lekcja: tolerancja testu nie może
  być ostrzejsza niż rozdzielczość przyrządu, który sprawdza; próg
  kalibruje się na wzorze już zaakceptowanym.
- Wykonawca: STOP przed lotem zamiast intruza ze skokami; pozycja 2
  literą aneksu, bez naginania progu; zmiana własnego kryterium
  w teście na sucho nazwana w raporcie. Usterka etykiety:
  pozycja_aneksu = 1 w testy_s4.json przy manifeście wahadła.
- Stan wątku lotu bez GNSS: bez znaczników 22 s z twierdzeniem (2d);
  nad polem znaczników dowód ze sprawdzoną przesłanką — 12 lotów
  po 110 s i jeden lot 600 s.
```

## §5. KIERUNKI_PO_PLANIE (append-only przy commicie §CO)

```
## Dopisek stanu katalogu — 12.11.2026 (CO-NAD2-4, ANEKS_NAD2-4)
- **Lot długi NADIR-II wykonany** (pozycja z dopisku CO-NAD2-2):
  600.5 s bez GNSS w jednym locie (c10_s01, intruz w ruchu cały
  czas), 0 odmów w misji, przesłanka dowodu trzyma w 12 246 tickach
  (zużycie do 41%), błąd pozycji poprawionej płaski (p95
  0.19–0.25 m) przy błędzie własnym EKF do 20.6 m.
- Nazwana granica: bias kursu po utracie GNSS dochodzi do ok. 5°
  i w drugiej połowie lotu nie ma trendu; rama go nie koryguje,
  przebieg po 600 s niezmierzony. Pozostałe granice bez zmian: SITL,
  jedna sceneria, pełna widoczność znaczników; jeden lot nie
  zastępuje próby.
- Noga NADIR-II nie ma otwartych pozycji. Niezmierzone i nieotwarte:
  inna sceneria i gorsza widoczność znaczników; bias kursu w lotach
  dłuższych niż 600 s; zrywy EKF przy obrocie kadłuba (estymator
  nietknięty). Nowa noga w tym wątku tylko na sygnał Olgi.
- Breach 0 / REFUSE(POS) fałszywych 0 programowo bez zmian
  (~240 bootów programu).
```

## §CO

Bramka: origin/master == **65a1b1aa**. Jeden commit [CO-NAD2-4]:
korzeń `ANEKS_NAD2-4.md` verbatim (byte-check sha256 z wiadomości CC)
+ KSIĘGA §4 i `KIERUNKI_PO_PLANIE.md` §5 append-only. Zero bootów,
zero zmian kodu i raportów. Plik `boot.ulg` zostaje na dysku.
Push = Olga.
