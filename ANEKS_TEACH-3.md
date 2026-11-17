# ANEKS_TEACH-3 — flaga GNSS w producencie jako stan przy klatce, bez stempla wiadomości; kadr z bufora nie wchodzi do mapy; S2 wznowiony przed smoke; 4 z 24 bootów

LiquidPatrol · CC · 17.11.2026 · łańcuch TEACH, po STOP-TEACH-2-FLAGA
(8d80ab01 na origin). Do ratyfikacji sygnałem **„ratyfikuję
TEACH-3"**. Sygnały bez numeru albo nazwy odrzucasz.

## §1. Weryfikacja CC (z repo, własnym kodem)

1. **Stan.** 54e4ebec, 8f902dd0, 5cfbf3c2, 8d80ab01 na origin;
   ANEKS_TEACH-2 w korzeniu z sumą 878fce80…; kod lotu bez zmian od
   34fd058b. Bootów nogi 4 z 24.
2. **Cienie C1 i C2 policzone od nowa** z wierszy producenta i GT:
   - błąd poprawki p50 / p95 / max: 0.339 / 0.422 / 0.486 m (C1,
     parking) i 0.166 / 0.318 / 0.360 m (C2, łąka) — jak w raporcie;
   - przyjęte 193 z 193 i 199 z 199 kadrów okna, przerwy 0.2 s;
   - georeferencja rozwiązana osobnym kodem z zapisanych wiązań (540
     i 573) równa zapisanej do piątej cyfry;
   - poprawki policzone z numeru klatki kluczowej, wektora i tej
     georeferencji równe datagramowi do 0.0001 m;
   - żadnego wiązania ani klatki kluczowej po chwili cienia;
   - detekcji znaczników surowych 0 na 1094 i 1115 klatek.
3. **Kurs klatek kluczowych na obrazie z gz:** błąd EKF do 9.9°
   (C1) i 4.4° (C2); po georeferencji reszta do 2.5° i 1.2°.
4. **Świat ST1 / ST2:** przyjęty z raportu i z `st_porownanie.json`;
   obrazów CC nie porównywał.
5. **Usterka potwierdzona.** Zatrzask flagi w wierszach cienia to
   1 794 869 451.44 przy klatce sim 65.6 s i 1 794 869 493.39 przy
   105.8 s. Przesunięcie wobec sim rośnie o 1.8 s na 40 s czasu sim
   (w C2 o 1.1 s), więc stempel idzie z zegarem ściennym. W kodzie
   producenta `on_flags` to jedyne miejsce, w którym stempel
   wiadomości wchodzi do logiki. Driver bierze czas z zegara gz,
   a stempel tylko zapisuje.
6. **Pomiar CC na 12 cięciach NAD3** (ULG, ślad drivera, wiersze
   producenta):
   - zmiana flagi dociera do subskrybenta w granicach 0.02 s od
     chwili z ULG, obraz około 0.01 s po ujęciu;
   - w 2 z 12 lotów klatka została ujęta 0.000 s i 0.004 s po fladze
     (p14, p09). To wyścig: taka klatka może nadejść przed wiadomością
     z flagą;
   - przy regule z §3 ostatni kadr mapy leży we wszystkich 12 lotach
     co najmniej 0.2 s przed flagą.
7. **Koszt reguły z §3, z danych reconu:** ostatni kadr sprzed cięcia
   nie jest klatką kluczową w żadnym z 39 przebiegów. Bez jego trzech
   wiązań największy błąd przebiegu zmienia się najwyżej o 0.004 m,
   obrót klatek o 0.07°, przesunięcie o 0.006 m. Innowacja przy
   pierwszym wyniku po cięciu nie przekracza 0.37 m, przy bramce
   1.5 m.

## §2. Błąd projektu CC

- PROMPT_TEACH_S1 §1.2 i poprawka F1 mówiły o „chwili flagi" bez
  nazwania podstawy czasu. Przegląd kodu po S1 przeczytał
  `m.timestamp` i jej nie sprawdził. Własny sprawdzian sekwencji
  flagi CC zrobił na ULG, który jest w czasie sim.
- Stempel epoki był w śladach NAD3 od początku (wiersze „flag",
  pole `ts`).
- Usterkę złapał sprawdzian na żywo z PROMPT_TEACH_S2 §4 (flaga
  rzeczywista i zatrzask w wierszach cienia), przed smoke.
- Wykonawca: STOP zasadny, odchylenia 1–9 przyjęte.

## §3. Rozstrzygnięcie

1. **Wybór: N2 w postaci zachowawczej.** N1 dodaje subskrypcję i nie
   usuwa wyścigu z §1 pkt 6. N3 wymaga zegara sim tak samo jak N1,
   a przesunięcie nie jest stałe.
2. **Litera** (zastępuje F1 z PROMPT_TEACH_S2 §1; dotyczy lotu, nie
   cienia):
   - producent dostaje flagę jako stan w chwili nadejścia klatki, tak
     jak migawkę EKF. Chwili flagi nie dostaje. Stempel wiadomości
     idzie wyłącznie do rejestru;
   - utrata to stan flagi 0 przy klatce. Mapa zamyka się raz, przy
     pierwszej klatce w utracie, gdy mapa nie jest pusta (F2 bez
     zmian);
   - gdy chwila flagi nie jest podana, kadr czekający w buforze nie
     wchodzi do mapy;
   - chwilą zamknięcia jest czas tej pierwszej klatki; od niej liczy
     się τ bramki innowacji.
3. **Tryb cienia i replay z podaną chwilą:** bez zmian.
4. **Co to gwarantuje.** Kadr jest w mapie tylko wtedy, gdy po nim
   nadeszła klatka, która widziała jeszcze flagę 1. Został więc ujęty
   przed prawdziwą flagą, o ile flaga nie spóźnia się względem obrazu
   o więcej niż 0.2 s. Zmierzone: flaga wyprzedza obraz o około
   0.02 s.
5. **Bez zmian:** PRE_TEACH, w tym warunek ważności „żadna klatka
   kluczowa ani wiązanie po fladze" (flaga z ULG); tabela; tor;
   budżet.
6. **Numeracja:** aneks po S2 nosi numer ANEKS_TEACH-4.

## §4. Wznowienie S2

1. Bramka: `origin/master` zawiera `8d80ab01`; sha256 tego pliku
   zgodne z podanym przez Olgę; sygnał „ratyfikuję TEACH-3" obecny.
2. Commit **[CO-TEACH-3]**: aneks verbatim w korzeniu (byte-check),
   blok §5 do KSIĘGI, append-only.
3. Zmiana kodu wg §3 pkt 2, tylko w `harness/nadir_obs.py`
   i `harness/teach_map.py`, oznaczona „TEACH-3:". Commit
   **[S2-FLAGA]**.
4. Sprawdziany przed bootem. Niepowodzenie któregokolwiek ⇒ STOP bez
   bootu, z liczbami.
   - **Testy:** sekwencje z `test_teach_s2.py` przepisane na flagę
     jako stan (0 → 1 → 0 → 1 → mapa → 0; zero przez cały czas): jedno
     zamknięcie, mapa niepusta, kadr z bufora odrzucony, τ = 0 przy
     pierwszej klatce po zamknięciu.
   - **W2 na łacie S** (ścieżka z podaną chwilą): 13 z 13 bez różnicy.
   - **W2-lot, 39 przebiegów** (ścieżka lotu): flaga 0 od pierwszej
     klatki z czasem ≥ chwila cięcia, bez podanej chwili. Oczekiwane:
     mapa ma jeden kadr mniej niż w reconie i żadnego kadru z czasem
     ≥ chwila cięcia; liczba przyjętych różni się najwyżej o 1,
     największy błąd przebiegu najwyżej o 0.02 m (rachunek CC:
     0.004 m).
   - **W2-wyścig, łata S, 13 przebiegów:** flaga 0 o jedną klatkę
     później. Oczekiwane: kadry mapy te same co w reconie, θ_k i t_k
     równe reconowi do 0.0001, żadnego kadru mapy z czasem ≥ chwila
     cięcia.
   - **Próba na sucho ze stemplem epoki:** proces `nadir_obs`
     dostaje wiadomości flagi ścieżką `on_flags`, ze stemplem jak
     w boocie (sim + 1.79·10⁹ s, rosnące przesunięcie). Lot
     syntetyczny p01: jedno zamknięcie, przyjętych co najmniej 90%
     kadrów po cięciu, B1–B4, lot ważny.
   - **Ostrość próby:** to samo wejście na kodzie z 34fd058b daje
     zero przyjętych poprawek.
   - W1-obs bez zmiany wyniku; nowe sumy obu plików w raporcie.
5. Boot SM i raport wg PROMPT_TEACH_S2 §3–§6. Dodatkowo w raporcie
   SM: czas klatki zamknięcia, chwila flagi z ULG i wejście osłony
   w utratę; czas ostatniego kadru mapy wobec flagi z ULG.

## §5. KSIĘGA (append-only przy commicie [CO-TEACH-3])

```
## TEACH — ANEKS_TEACH-3 (17.11.2026): flaga jako stan, S2 przed smoke
- S2 po 4 bootach (4/24): świat ST1 / ST2 PASS; cienie C1 (parking)
  i C2 (łąka) przechodzą bramkę obrazu za pierwszym razem — błąd
  poprawki max 0.49 / 0.36 m, przyjętych 100%, zero detekcji
  znaczników. P-TEACH-3 ✓, P-TEACH-4 ✓.
- CC własnym kodem: błędy C1 / C2 z GT jak w raporcie; georeferencja
  z zapisanych wiązań równa zapisanej; poprawki z wierszy równe
  datagramowi do 0.0001 m; żadnego wiązania po chwili cienia.
- STOP przed smoke: chwila flagi w producencie brana ze stempla
  wiadomości DDS, który jest w czasie epoki, nie sim. W locie
  z cięciem każda poprawka zostałaby odrzucona. Złapane sprawdzianem
  na żywo w bootach cienia.
- Rozstrzygnięcie: flaga jako stan przy klatce, bez stempla; kadr
  z bufora nie wchodzi do mapy. Pomiar CC na 12 cięciach NAD3: flaga
  dociera w 0.02 s; w 2 z 12 lotów klatka ujęta 0–4 ms po fladze
  (wyścig); przy nowej regule ostatni kadr mapy co najmniej 0.2 s
  przed flagą. Koszt z danych reconu: błąd przebiegu ± 0.004 m.
- ✗ projektowe CC: „chwila flagi" bez nazwanej podstawy czasu
  w dwóch promptach; przegląd kodu nie sprawdził podstawy czasu
  stempla; własny sprawdzian zrobiony na ULG (czas sim). Lekcja:
  każda wielkość czasu w kodzie lotu ma nazwaną podstawę; stempel
  wiadomości DDS nie jest czasem sim.
- Predykcja CC przed smoke:
  - P-TEACH-11 (0.70): SM ważny, B1–B4 bez naruszeń, zero REFUSE
    w misji, największy błąd poprawki ≤ 1.00 m.
```
