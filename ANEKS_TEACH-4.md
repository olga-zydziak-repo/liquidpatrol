# ANEKS_TEACH-4 — S2 rozliczony: smoke ważny, litera bez naruszeń, zero odmów w misji; zgoda na bramkę S3; 5 z 24 bootów

LiquidPatrol · CC · 17.11.2026 · łańcuch TEACH, po STOP-TEACH-2-SM
(64f38b03 na origin). Do ratyfikacji sygnałem **„ratyfikuję
TEACH-4"**. Sygnały bez numeru albo nazwy odrzucasz.

## §1. Weryfikacja CC (z repo, własnym kodem)

1. **Stan.** bc7a1b40, ab361d2b, 6f8c5313, 64f38b03 na origin;
   ANEKS_TEACH-3 w korzeniu z sumą 30abb4a4…. Kod lotu wobec 34fd058b
   zmieniony w dwóch plikach (`harness/nadir_obs.py`,
   `harness/teach_map.py`; 17 linii dodanych, 8 usuniętych), zgodnie
   z literą TEACH-3. Osłona, provery, tabela, `tor.json`, światy,
   model i manifest bez zmian od 9808a8be.
2. **Sprawdziany przy biurku** — z zapisanych wyników, bez powtarzania
   biegów:
   - W2-lot 39 z 39: mapa o jeden kadr mniejsza niż w reconie, żadnego
     kadru z czasem ≥ chwila cięcia, ostatni kadr mapy 0.21–0.40 s
     przed cięciem; największy błąd przebiegu zmienia się najwyżej
     o 0.0044 m, obrót klatek o 0.071°, przesunięcie o 0.0059 m
     (rachunek CC sprzed zmiany: 0.004 m / 0.07° / 0.006 m);
   - W2-wyścig 13 z 13: kadry mapy i georeferencja jak w reconie;
   - próba ze stemplem epoki: nowy kod 552 z 552 przyjętych w oknie
     misji, kod z 34fd058b na tym samym wejściu 0 z 552.
3. **SM policzony od nowa** z wierszy producenta, ramy, śladu drivera,
   GT i ULG; tabela wpisana z PRE §4, nie z pliku.
   - **Oś czasu:** flaga w ULG 173.268 s; osłona w utracie +0.088 s;
     pierwsza klatka z flagą 0 i zamknięcie mapy 173.400 s (+0.132 s);
     kadr 173.2 z bufora odrzucony; ostatni kadr mapy 173.0 s
     (−0.268 s). Zamknięcie jedno. Po fladze żadnego kadru mapy,
     klatki kluczowej ani wiązania (174 kadry, 9 klatek kluczowych,
     522 wiązania).
   - **(B1):** 2501 ticków utraty, 2439 ocenionych, przekroczeń 0.
     Największe e′/U′ 0.23 (0.233 z GT zapisanym przy ticku, 0.224
     z GT interpolowanym w czasie ticku; raport 0.229). 62 ticki
     nieocenione leżą po zatrzasku τ\* w zejściu planowym i na ziemi.
     Trzy ticki przed pierwszą poprawką: e′/U′ do 0.10.
   - **(B2):** r_GT max 15.36 m, margines 16.64 m. **(B3):** 0 z 2501.
     **(B4):** `nav_state` 14 w 306 z 306 próbek epizodu, failsafe 0,
     breach brak.
   - **Replay osłony z tabeli PRE:** przedział, R, u′, τ = czas ticku
     − t_fix i decyzja — 0 różnic w 2501 tickach utraty.
   - **REFUSE:** 63 ticki, pierwszy 292.10 s, czyli 8.3 s po zejściu
     planowym (283.77 s). W misji 0.
   - **(D1) własnym kodem:** kontynuacja 110.516 s, track 1.000,
     pasmo 1.000 (odległość od intruza 7.1–8.7 m).
   - **Poprawki:** okno od zamknięcia do końca misji 552 kadry, 552
     przyjęte. Błąd wobec GT p50 / p95 / max 0.313 / 0.504 / 0.567 m.
     Największa przerwa 0.2 s. Innowacja do 0.22 m przy bramce od
     1.5 m.
   - **Georeferencja** rozwiązana osobnym kodem z 522 zapisanych
     wiązań równa zapisanej do piątej cyfry; 552 poprawki policzone
     z klatki kluczowej, wektora i tej georeferencji równe datagramowi
     do 0.0001 m.
   - **Kurs klatek kluczowych:** błąd EKF do 6.6°, po georeferencji
     reszta do 1.8°.
   - **Znaczniki:** 1 detekcja surowa na 1481 klatek (ID 37, bok
     5 px, spoza manifestu), zgodnych z manifestem 0.
   - **Flaga w wierszach:** chwila flagi pusta we wszystkich 1481
     wierszach; stempel epoki tylko w rejestrze.
4. **Pętla domknięta.** Błąd własny EKF rośnie po cięciu do 5.05 m,
   błąd poprawki zostaje do 0.57 m, e′ do 0.65 m.
5. **Od czego zależy błąd poprawki w SM:** od odległości kadru od
   środka klatki kluczowej (korelacja +0.51) i od błędu przechyłu EKF
   (+0.48); od błędu własnego EKF nie (+0.06). Prosta przez błąd
   w czasie: +0.08 m na 100 s.
6. **Przechył EKF po utracie GNSS — pomiar na lotach już wykonanych**
   (ten sam EKF, niezależnie od źródła poprawki):
   - lot długi NAD2 (c10), 600 s: w oknach po 100 s p50 0.32–0.42°,
     p95 0.75–1.03°, bez wzrostu; przy 12 m wysokości to 0.16–0.22 m;
   - 12 cięć NAD3: po cięciu p95 0.40–0.75°, przed cięciem
     0.55–1.02°;
   - we wszystkich sześciu lotach komórki c05 mediana w drugiej
     połowie okna jest wyższa o 0.10–0.23°, tak jak w SM (+0.20°);
     w c10 tego nie ma.
   Wzrost z pkt 5 to wzór komórki c05, nie skutek źródła. W locie
   długim c10 przechył nie narasta; dla c05 poza 110 s pomiaru nie
   ma.
7. **Nie powtarzane:** biegi sprawdzianów z pkt 2, bramka zdrowia
   i tempo stanowiska, liczby rejestratora kadrów. Jeden kadr
   obejrzany: parking w kadrze, cień drona widoczny.

## §2. Rozliczenie

- **S2 PASS** po 5 bootach z 7 (ST1, ST2, C1, C2, SM). Noga 5 z 24.
- **P-TEACH-11 ✓** (0.567 m, zero REFUSE w misji). P-TEACH-5: część
  smoke spełniona (0 przekroczeń, 0.23); rozliczenie po bramce.
  Noga dotąd: 4 z 5 przy sumie szans 3.50 (✓ 1, 3, 4, 11; ✗ 2).
- **Brak w raporcie SM — replay.** PRE §6 ma cztery warunki ważności
  lotu; raport podaje trzy. Replay osłony przez `nad3_krok`
  i przeliczenie poprawek oraz georeferencji z wierszy, wymagane
  w PROMPT_TEACH_S2 §4, nie zostały wykonane: narzędzia nie ma
  (STOP-TEACH-2: „nie jest napisane"), a raport SM tego nie nazywa.
  Replay zrobił CC (§1 pkt 3): 0 różnic. Lot ważny. W S3 replay jest
  warunkiem per lot, więc narzędzie powstaje w budowie S3, z próbą
  ostrości.
- **Odchylenia 1–5 raportu przyjęte.** Dwa długi narzędzi idą do
  budowy S3: analizator wywraca się przy locie bez żadnej przyjętej
  poprawki (właśnie taki lot byłby wynikiem negatywnym bramki);
  `test_analizator_zrodlo` czerwony od TEACH-2A.
- **✗ CC:** w ANEKS_TEACH-3 §4 próg „co najmniej 90% kadrów po
  cięciu" bez nazwanego końca okna. Wykonawca policzył najpierw do
  końca nagrania (86%, z zejściem i ziemią), potem w oknie misji
  (100%). Lekcja: ułamek zawsze z nazwanym oknem.
- `systemd-timesyncd` zatrzymany na sesję lotów; uruchomienie po
  sesji należy do Olgi.

## §3. Rozstrzygnięcie

1. **Zgoda na bramkę S3** wg PRE_TEACH §6, bez zmian litery: 12 cięć
   (łaty S, M, J × komórki c05, c10 × 2 powtórzenia), 2 nominały,
   3 rezerwy stanowiska; najwyżej 17 bootów, noga najwyżej 22 z 24.
2. **Obowiązuje:** świadek znaczników wg ANEKS_TEACH-2, flaga wg
   ANEKS_TEACH-3. Tabela, tor, progi i werdykty bez zmian.
3. **Nominały** (PRE wyznacza łatę, komórkę ustala ten aneks): jeden
   epizod, producent w cieniu, ścieżka jak C1 i C2. Po bloku S: łata
   S, epizod c10, chwila cienia 176.5 s. Po bloku M: łata J, epizod
   c05, chwila cienia 173.6 s. Z C1 i C2 daje to cień na obu
   komórkach łat S i J.
4. **Łata M leci od razu w pętli.** W gz jeszcze jej nie było: ani
   w boocie statycznym, ani w cieniu. Awaria źródła na M kosztuje
   dostępność (REFUSE(τ\*) jest znaleziskiem), nie bezpieczeństwo.
   Dodatkowego zatrzymania nie ma: w S3 żadna naprawa toru nie jest
   dopuszczona, więc STOP po pierwszym locie na M niczego by nie
   zmienił.
5. **S4** (lot długi z okrążeniem uczącym, teren dla wszystkich
   kamer) tym aneksem się nie otwiera.

## §4. KSIĘGA (append-only przy commicie [CO-TEACH-4])

```
## TEACH — ANEKS_TEACH-4 (17.11.2026): S2 rozliczony, zgoda na bramkę
- S2 PASS, 5 bootów (5/24). SM (łata S, c05): pierwszy lot bez GNSS
  i bez znaczników z poprawką z mapy w pętli — ważny, B1–B4 bez
  naruszeń, zero REFUSE w misji, kontynuacja 110.5 s. P-TEACH-11 ✓.
  Noga dotąd 4/5 przy sumie szans 3.50.
- CC własnym kodem: B1 0 przekroczeń na 2439 tickach, max e′/U′ 0.23;
  replay osłony z tabeli PRE 0 różnic na 2501 tickach utraty; błąd
  poprawki p50 / p95 / max 0.313 / 0.504 / 0.567 m, przyjętych 552
  z 552;
  georeferencja z 522 wiązań równa zapisanej; poprawki z wierszy
  równe datagramowi do 0.0001 m; ostatni kadr mapy 0.268 s przed
  flagą z ULG; zgodnych detekcji znaczników 0.
- Pętla: błąd własny EKF do 5.05 m, błąd poprawki do 0.57 m.
- Pomiar na lotach wykonanych: błąd przechyłu EKF po utracie GNSS nie
  rośnie w 600 s lotu długiego c10 (p95 0.75–1.03°, przy 12 m to
  0.16–0.22 m); w c05 mediana w drugiej połowie okna wyższa
  o 0.10–0.23° we wszystkich lotach, poza 110 s bez pomiaru.
- Brak w raporcie SM: replay (czwarty warunek ważności) niewykonany,
  narzędzia nie ma; zrobił go CC. Narzędzie w budowie S3.
- ✗ CC: próg „90% kadrów po cięciu" bez nazwanego końca okna.
  Lekcja: ułamek zawsze z nazwanym oknem.
- Predykcje CC przed bramką (P-TEACH-5 … 10 stoją bez zmian):
  - P-TEACH-12 (0.75): największy błąd poprawki w 12 cięciach
    ≤ 0.80 m.
  - P-TEACH-13 (0.75): blok M — 4 z 4 cięć dostępne.
  - P-TEACH-14 (0.80): w żadnym z 14 lotów producent nie gubi
    klatki, a zamknięcie mapy trwa ≤ 100 ms w każdym z 12 cięć.
```
