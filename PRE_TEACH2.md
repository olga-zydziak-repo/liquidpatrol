# PRE_TEACH2 — TEACH-II: lot 10 minut bez GNSS i bez znaczników na mapie z pierwszego przebiegu wzoru

LiquidPatrol · CC · 17.11.2026 · łańcuch TEACH2, po STOP-TEACH2R
(7c466e53 na origin). Do ratyfikacji sygnałem **„ratyfikuję
PRE_TEACH2"**. Sygnały bez numeru albo nazwy odrzucasz.

## §1. Weryfikacja reconu (CC z repo, własnym kodem)

1. **Stan.** 936cab8c i 7c466e53 na origin. Bloki KSIĘGI i KIERUNKÓW
   z promptu dopisane dosłownie, bez usunięć. Od 5ad2555e kod lotu,
   osłona, tor, tabela, światy i narzędzia TEACH bez zmian; nowe pliki
   tylko w `results/TEACH2_RECON/`.
2. **Geometria (R2).** Na 12 cięciach bramki, od wejścia do zejścia:
   największa odległość dron–intruz 11.17 m (osiedle, c10, a).
   Promień przewidywany 22.17 m, zapas do bariery 2.67 m. Liczba
   raportu potwierdzona; rachunek CC z promptu (10.7 m) stał na trzech
   lotach.
3. **Nauka z innego przebiegu (R3).** Z wierszy 72 przebiegów:
   - warunek Ś1 spełnia 24 z 24 par na każdej łacie;
   - okno „wspólne": 27 543 klatki, wszystkie przyjęte, największy
     błąd 0.422 m;
   - okno „dalej": 24 843 klatki, wszystkie przyjęte, największy błąd
     0.646 m (c05) i 0.380 m (c10); największa przerwa 0.2 s;
   - mapy nauki mają 372–390 kadrów, tyle, ile lot uczący ma kadrów
     od 6 m do końca misji (policzone osobno z lotów). Kadry lotu
     powtarzającego do mapy nie weszły.
   Samych błędów CC nie policzył od nowa: wyniki nie niosą wektorów
   poprawek ani wiązań.
4. **Wierność.** Wartości odniesienia z lotów (0.730 / 0.428 m,
   0.436 / 0.251 m) są z rachunku CC; bieg reconu jest wykonawcy:
   różnica największego błędu −0.009 i +0.002 m. Mapa reconu ma tyle
   kadrów i klatek kluczowych co w locie (177 / 9 i 185 / 10).
5. **Znalezisko R4 w kodzie.** `harness/teach_map.py`,
   `_wlacz_do_mapy`: nowa klatka kluczowa przegląda wszystkie
   wcześniejsze kadry i dopasowuje te, do których trójki weszła. To
   praca wątku roboczego producenta. Migawki EKF i flagi robi wątek
   obrazu przy nadejściu klatki, a odbiór tematów idzie w wątku
   głównym, więc pozy zostają świeże. Skutki są dwa: klatki zgubione
   w fazie mapy i zamknięcie opóźnione, jeśli wolna klatka trwa
   w chwili flagi.
6. **Nie sprawdzane przez CC:** czasy (stanowisko) i błędy klatka po
   klatce.

## §2. Rozliczenie reconu

- **Żadna śmierć nie zachodzi.** P-TEACH2-R1 … R7: 7 z 7 przy sumie
  szans 4.70.
- **Mapa z innego lotu działa lepiej niż mapa z 33 s własnego.**
  W oknie „wspólne" największy błąd to 0.42 m wobec 0.73 m w bramce.
  Dłuższa nauka z GNSS daje więcej kotwic.
- **Dopasowanie sięga dalej niż wskaźnik z pozycji.** Mapa z 75 s
  obsłużyła 73–146 s epizodu bez jednej odrzuconej klatki. Rachunek
  pokrycia CC był ostrożny.
- **c05 rośnie na krawędzi nauki, c10 nie.** W c05 największy błąd
  w oknach po 20 s idzie od 0.35 do 0.65 m, w c10 zostaje
  w 0.27–0.39 m.
- **Zamknięcie mapy z 200 s:** 206 ms na parkingu, do 270 ms na
  osiedlu. Render osiedla i łąki daje więcej cech niż obraz gz, więc
  ich czasy są górną oceną. Mapa: 1013 kadrów, 16 klatek kluczowych,
  2998 wiązań.
- **Wolne klatki kluczowe (R4):** na parkingu trzy klatki fazy mapy
  ponad 0.2 s, najdłuższa 0.62 s; na osiedlu do 1.81 s.
- **✗ CC:**
  - odległość dron–intruz policzona na trzech lotach zamiast
    dwunastu;
  - prompt nie wymagał wektorów poprawek i wiązań w wynikach, więc
    błędów R3 nie da się odtworzyć z GT. To powtórzona lekcja
    z ANEKS_TEACH-1 §5;
  - szanse znów za niskie: 7 z 7 przy 4.70, po 9 z 9 przy 6.35
    w bramce.
- Odchylenia 1–9 raportu przyjęte.

## §3. Rozstrzygnięcia CC

1. **Nauka 200 s.** Pełny przebieg wzoru z GNSS, potem cięcie
   (`KONT_INJECT_T` 200). Wahadło wraca po tym samym wzorze, więc cały
   lot bez GNSS leży nad terenem widzianym w nauce.
2. **Komórka c10, ziarno s01**, jak lot 10-minutowy w NADIR-II.
   Manifest wahadła z manifestu NAD3 v2: pięć nóg po 200 s.
3. **Łata S (parking).** Najniższy czas producenta; tam leciał smoke.
4. **Bez nominału długiego w cieniu.** Wymagałby zmiany drivera,
   a pierwszy lot długi mierzy to samo z GT. Bezpieczeństwo trzyma
   osłona.
5. **Kod lotu bez zmian mimo znaleziska R4.** Ryzyko nazwane: wolna
   klatka kluczowa w chwili flagi opóźnia pierwszą poprawkę. Na
   parkingu najgorszy zmierzony przypadek to 0.62 s klatki i 0.21 s
   zamknięcia, czyli pierwsza poprawka około 1.0 s po fladze przy
   zatrzasku 2.05 s. Reguła powtórki zapisana w §5.
6. **Jeden lot.** To pomiar pokazowy, jak lot długi w NADIR-II, nie
   bramka statystyczna. Inne tereny i komórka c05 są poza tą pozycją.

## §4. FREEZE

Bez zmian z PRE_TEACH §4, z sumami strażnika boota: tabela (E 1.00 m,
τ\* 2.15 s, zatrzask 2.05 s, bariera 24.84 m przy τ ≤ 0.35 s), osłona,
sieć, certy, tor mapy w wariancie K, reguła przyjęcia, świat i model,
flaga wg ANEKS_TEACH-3, świadek znaczników wg ANEKS_TEACH-2. Kamera
przepływu nad szachownicą.

Nowe, tylko parametry i narzędzia:
- manifest wahadła z v2 (generator przez import `wahadlo`), długość
  1000 s; suma zapisana przy budowie i trzymana przez strażnika;
- cięcie 200 s po wejściu; kontynuacja 600.5 s od `t_inj_sim`;
- bezpiecznik czasu ściennego 1000 s; limit wyciągu ULG 10 MB;
- litera dostępności z kontynuacją 600 s.

Geometria przewidywana: promień drona do 22.17 m.

## §5. Etapy, litera, werdykt, budżet

**S1 — budowa i próba na sucho (0 bootów).** Narzędzia
w `results/TEACH2/tools/`: generator wahadła, kolejka, sędzia
i analizator lotu długiego. Sprawdzian lotu z S3 bez zmian. Zmiana
w `harness/`, osłonie albo driverze ⇒ STOP przed zmianą.

**S2 — lot długi (≤ 3 booty: lot i dwie rezerwy).**

*Ważność lotu:* zero detekcji znaczników zgodnych z manifestem; żaden
kadr mapy, klatka kluczowa ani wiązanie po fladze z ULG; zamknięcie
jedno; cięcie po wejściu; sprawdzian lotu 100%; meta zgodna.

*Litera bezpieczeństwa:* (B1) e′ ≤ U′ w każdym ticku utraty; (B2)
r_GT < R_E; (B3) `r_est` = |p_corr| w każdym ticku KONT; (B4) po
REFUSE zejście wg reguły, `nav_state` 14, failsafe 0, zero breach.

*Dostępność (D-L):* kontynuacja ≥ 600 s od `t_inj_sim` ∧ track ≥ 0.85
∧ pasmo ≥ 0.85 ∧ zero REFUSE w misji.

**Werdykt:**
- **L-A:** zero naruszeń i (D-L) spełnione — lot 10 minut bez GNSS
  i bez znaczników na mapie z własnego przebiegu.
- **L-B:** zero naruszeń, odmowa w misji — bezpieczeństwo trzyma,
  10 minut niepotwierdzone; czas kontynuacji i mechanizm odmowy
  w raporcie.
- **L-C:** naruszenie B1–B4 — FAIL.

**Powtórka lotu, zapisana przed lotem.** Dopuszczona tylko w dwóch
przypadkach:
- boot nieważny stanowiskowo albo cięcie bez wejścia;
- REFUSE(τ\*) w ciągu 3 s od flagi, gdy w chwili flagi trwała klatka
  fazy mapy dłuższa niż 0.5 s. To ograniczenie przepustowości
  producenta znane przed lotem; lot zostaje w raporcie jako
  znalezisko.

Każdy inny wynik pierwszego ważnego lotu jest werdyktem. Naruszenie
B1–B4, sprawdzian poniżej 100% albo niezgodna meta ⇒ STOP natychmiast.

**Budżet:** ≤ 3 booty. Po L-B albo L-C drugiego podejścia w tej
architekturze nie ma.

## §6. Zakres zdania końcowego

SITL, jeden lot, jeden teren (płaski obraz ortofotomapy parkingu),
jedna komórka. Nauka i lot bez GNSS dzieli kilka minut, światło się
nie zmienia. Dron lata bez GNSS tylko nad terenem, nad którym
wcześniej leciał z GNSS. Kamera przepływu pracuje nad szachownicą.
Zdanie nie mówi nic o innych terenach w locie długim, o mapie
z innego dnia, o rzeźbie terenu ani o budowaniu mapy bez GNSS.

## §7. KSIĘGA (append-only przy commicie [CO-TEACH2-1])

```
## TEACH-II — PRE (PRE_TEACH2, 17.11.2026)
- Recon rozliczony, żadna śmierć: P-TEACH2-R1…R7 7/7 przy sumie szans
  4.70. Mapa z jednego lotu obsługuje inny przebieg: 72/72 par, okno
  wspólne max 0.422 m, okno dalej max 0.646 m, przyjęte 52 386 z 52 386
  klatek. Zamknięcie mapy z 200 s: 206–270 ms (1013 kadrów, 16 klatek
  kluczowych). Promień przewidywany 22.17 m przy barierze 24.84 m.
- CC własnym kodem: warunek Ś1 z wierszy 24/24 na każdej łacie;
  geometria na 12 cięciach (11.17 m); mapy nauki tylko z kadrów lotu
  uczącego. Błędy R3 klatka po klatce i czasy nie sprawdzone.
- Znalezisko R4: nowa klatka kluczowa dopasowuje wszystkie wcześniejsze
  kadry, do których trójki weszła; pojedyncza klatka fazy mapy do
  0.62 s na parkingu (render osiedla 1.81 s). Kod lotu bez zmian;
  reguła powtórki w PRE §5.
- ✗ CC: odległość dron–intruz z trzech lotów zamiast dwunastu; wyniki
  reconu bez wektorów (powtórzona lekcja z TEACH-1); szanse za niskie
  drugi raz z rzędu.
- Decyzje: nauka 200 s, c10, parking, jeden lot, bez nominału w cieniu.
- Predykcje CC przed budową:
  - P-TEACH2-1 (0.85): budowa i próba na sucho bez STOP-u i bez
    zmiany harness, osłony i drivera.
  - P-TEACH2-2 (0.75): werdykt L-A w pierwszym ważnym locie.
  - P-TEACH2-3 (0.90): zero przekroczeń przesłanki, max e′/U′ ≤ 0.60.
  - P-TEACH2-4 (0.75): największy błąd poprawki w misji ≤ 0.80 m.
  - P-TEACH2-5 (0.80): przyjętych co najmniej 99.5% klatek okna misji
    i żadnej przerwy ponad 1.15 s.
  - P-TEACH2-6 (0.70): zamknięcie mapy w locie ≤ 0.40 s i pierwsza
    poprawka ≤ 0.8 s po fladze.
  - P-TEACH2-7 (0.70): największy błąd poprawki w ostatnich 100 s
    misji ≤ największy w pierwszych 100 s + 0.15 m.
  - P-TEACH2-8 (0.65): klatek zgubionych w fazie mapy najwyżej 15.
  - P-TEACH2-9 (0.65): promień drona (GT) w misji najwyżej 20.5 m.
```

## §8. KIERUNKI_PO_PLANIE (append-only przy commicie [CO-TEACH2-1])

```
## Dopisek stanu katalogu — 17.11.2026 (CO-TEACH2-1, PRE_TEACH2)
- **TEACH-II, recon — CLOSED, żyje.** Mapa z jednego lotu z GNSS
  obsługuje inny przebieg tej samej komórki: błąd do 0.42 m w części
  wspólnej wzoru, bez przerw, na parkingu, osiedlu i łące; 0 bootów.
- **TEACH-II — otwarta, PRE ratyfikowany.** Jeden lot: 200 s nauki
  z GNSS, potem 600 s bez GNSS i bez znaczników na wahadle c10 nad
  parkingiem. Sieć, osłona, tabela i tor mapy bez zmian. Budżet
  ≤ 3 booty.
- Obserwacja bez pozycji: producent w fazie mapy nie jest czasu
  rzeczywistego przy późnych klatkach kluczowych (kolejka 1, klatki
  gubione). Przy dłuższej nauce albo innym sprzęcie wymaga rozłożenia
  dopasowań w czasie.
```
