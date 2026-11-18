# ANEKS_TEACH2-2 — zamknięcie pozycji: lot długi werdykt L-A — 600 s bez GNSS i bez znaczników na mapie z 200 s własnego lotu, litera bez naruszeń, bez odmowy

LiquidPatrol · CC · 18.11.2026 · łańcuch TEACH2, po STOP-TEACH2-1
(3b989e84 na origin). Do ratyfikacji sygnałem **„ratyfikuję
TEACH2-2"**. Sygnały bez numeru albo nazwy odrzucasz.

## §1. Weryfikacja CC z repo (wykonaniem, własnym kodem)

Tabela wpisana z liczb PRE_TEACH §4; e′ liczone z wierszy ramy jako
|p_corr − GT|; koniec misji to komenda zejścia planowego; chwila
flagi z ULG.

1. **Stan.** 004de58a, 44650ca9 i 3b989e84 na origin; ANEKS_TEACH2-1
   w korzeniu z sumą df5909ab…. Kod lotu, osłona, driver, tor, tabela,
   świat i narzędzia TEACH bez zmian.
2. **Przebieg.** Start epizodu 139.65 s, wejście po 6.28 s, flaga
   z ULG 345.948 s (206.3 s epizodu), zejście planowe 946.456 s.
   Kontynuacja 600.52 s od cięcia.
3. **Przesłanka.** 12 696 ticków utraty, ocenione 12 638: **zero
   przekroczeń e′ ≤ U′**, największe zużycie granicy 0.24.
   Nieocenione 58, wszystkie po zatrzasku τ\* w zejściu; w misji 0.
   Osiem ticków przed pierwszą poprawką: e′/U′ do 0.10.
4. **Replay osłony z tabeli PRE.** Przedział, R, u′, τ i decyzja:
   0 różnic w 12 696 tickach. `r_est` = |p_corr| w każdym.
5. **(B2), (B4).** Największy r_GT 19.48 m przy R_E 32 m; `nav_state`
   14 w 1623 z 1623 próbek, failsafe 0, breach brak. REFUSE tylko po
   komendzie zejścia, pierwszy 8.8 s po niej.
6. **(D-L) własnym kodem.** Kontynuacja 600.52 s, track 1.000, pasmo
   0.971, REFUSE w misji 0.
7. **Ważność.**
   - Zamknięcie mapy jedno, klatką 0.052 s po fladze; ostatni kadr
     mapy 0.348 s przed flagą. Po fladze żadnego kadru mapy, klatki
     kluczowej ani wiązania (1041 kadrów, 15 klatek kluczowych, 3119
     wiązań).
   - Znaczniki: 2 detekcje surowe na 4784 klatki (ID 37, bok do
     5 px), zgodnych z manifestem 0.
   - Chwila flagi pusta we wszystkich wierszach.
8. **Poprawki.** 3003 kadry okna misji, 3003 przyjęte; błąd wobec GT
   p50 / p95 / max 0.234 / 0.352 / 0.449 m; największa przerwa 0.2 s.
   Georeferencja rozwiązana osobnym kodem z 3119 zapisanych wiązań
   równa zapisanej; 3003 poprawki z klatki kluczowej, wektora i tej
   georeferencji równe datagramowi do 0.0001 m.
9. **W czasie, okna po 100 s od flagi:**
   - największy błąd poprawki: 0.369, 0.449, 0.432, 0.393, 0.411,
     0.401 m; prosta przez błąd: −0.005 m na 100 s;
   - błąd własny EKF: do 3.5, 5.5, 8.0, 10.3, 15.2, 17.4 m; korelacja
     z błędem poprawki −0.11;
   - punkty zgodne w 5. percentylu: 118–179 przy progu 12;
   - przechył EKF: mediana od 0.25° do 0.50°, p95 do 0.96°.
10. **Faza mapy.** Ciąg 4784 klatek bez luki (największy odstęp
    0.20 s), więc zgubionych klatek nie ma. Najcięższa klatka
    kluczowa, piętnasta w 166.5 s epizodu: 157 dopasowań w 108 ms.
11. **Pierwsza poprawka w osłonie.** Zamknięcie mapy 383 ms; pierwszy
    tick osłony z poprawką 0.464 s po fladze; do tego czasu τ doszło
    do 0.38 s przy zatrzasku 2.05 s.

Liczby raportu wykonawcy potwierdzone. Reszta kursu klatek kluczowych
po georeferencji wychodzi CC na 0.7°, w raporcie 1.1° (obserwabla bez
progu). Czasy producenta i pamięć odczytane z zapisów lotu.

## §2. Werdykt

1. Litera bezpieczeństwa B1–B4: **0 naruszeń.**
2. Dostępność (D-L): **spełniona**, bez odmowy w misji.
3. **Werdykt L-A. TEACH-II — CLOSED, PASS.** Lot ważny w pierwszym
   boocie, rezerwy nietknięte. Budżet 1 z 3.

## §3. Zdanie, które stoi

Sieć NCP-20 z osłoną i dowodem z NADIR-II, bez zmiany kodu sieci,
osłony, reguły i toru mapy, prowadzi zadanie przez 600 s po utracie
GNSS bez znaczników naziemnych, gdy poprawkę pozycji daje mapa
zbudowana z własnej kamery w dół podczas 200 s lotu z GNSS: jeden lot
nad parkingiem, bez odmowy. Przesłanka |p_corr − GT| ≤ U′ trzymała
w każdym z 12 638 ticków przy największym zużyciu granicy 24%. Błąd
poprawki nie przekroczył 0.45 m i nie rósł w czasie, podczas gdy błąd
własny EKF doszedł do 17.4 m.

**Granice zdania:** SITL, jeden lot, jeden teren (płaski obraz
ortofotomapy parkingu), jedna komórka. Naukę i lot bez GNSS dzieli
kilka minut, światło się nie zmienia. Dron lata bez GNSS tylko nad
terenem, nad którym wcześniej leciał z GNSS. Kamera przepływu pracuje
nad szachownicą. Zdanie nie mówi nic o innych terenach w locie długim,
o mapie z innego dnia, o rzeźbie terenu ani o budowaniu mapy bez GNSS.

## §4. Gdzie było ciasno i co wyszło poza planem

- **Ciasno nie było nigdzie w locie.** Najmniejszy zapas bariery
  4.87 m, τ w misji do 0.38 s, punktów zgodnych zawsze ponad sto.
  Krawędź mapy, która w bramce dała lot na styku, tu nie wystąpiła:
  nauka pokryła całe zadanie.
- **Dłuższa nauka dała lepszą mapę, nie tylko większą.** Największy
  błąd 0.45 m wobec 0.76 m w bramce, przy mapie sześć razy większej.
  To samo pokazał recon.
- **Zamknięcie mapy w locie trwało 383 ms, przy biurku 206 ms.**
  Różnica leży w rozwiązaniu georeferencji liczonym pod obciążeniem
  symulacji (342 ms wobec 136 ms wg raportu). Próg predykcji 0.40 s
  przeszedł o 17 ms. Przy dłuższej nauce ten czas rośnie dalej.
- **Wolnych klatek kluczowych w gz nie było.** Recon dawał do 0.62 s
  na renderze parkingu; w locie najdłuższa klatka fazy mapy trwała
  0.13 s. Render ma więcej cech niż obraz gz.
- **Promień drona 19.48 m** przy przewidywanym górnym 22.17 m.
- **Pasmo najniższe w oknie 400–500 s: 0.942** (z raportu), przy
  progu 0.85.

## §5. Proces

- Jeden STOP przed lotem, na progu sprawdzianu manifestu bez
  tolerancji (ANEKS_TEACH2-1, błąd CC). Kolejka, sędzia i sprawdzian
  lotu przeszły bez poprawek.
- Odchylenia 1–5 raportu przyjęte. „Pierwszą poprawkę po fladze"
  raport liczy czasem klatki (0.052 s); do osłony dotarła po 0.464 s.
  W PRE tej różnicy nie nazwano.
- Wyniki lotu niosą wektory poprawek i wiązania, więc georeferencję
  i poprawki dało się policzyć od nowa.

## §6. Rozliczenie predykcji

- P-TEACH2-1 (0.85) ✗ — rozliczona w ANEKS_TEACH2-1.
- P-TEACH2-2 (0.75) ✓ — L-A w pierwszym ważnym locie.
- P-TEACH2-3 (0.90) ✓ — zero przekroczeń, max 0.24.
- P-TEACH2-4 (0.75) ✓ — 0.449 m przy progu 0.80.
- P-TEACH2-5 (0.80) ✓ — 3003 z 3003, bez przerwy ponad 0.2 s.
- P-TEACH2-6 (0.70) ✓ — zamknięcie 0.383 s, poprawka w osłonie po
  0.464 s; pierwszy warunek o 17 ms.
- P-TEACH2-7 (0.70) ✓ — ostatnie 100 s 0.401 m, pierwsze 0.369 m.
- P-TEACH2-8 (0.65) ✓ — zgubionych klatek 0.
- P-TEACH2-9 (0.65) ✓ — 19.48 m przy progu 20.5.

PRE: 8 z 9 przy sumie szans 6.75. Z reconem: 15 z 16 przy 11.45.
Jedyne chybienie to próg własnego sprawdzianu, nie zachowanie
systemu.

## §7. KSIĘGA (append-only przy commicie §CO)

```
## TEACH-II — lot długi i zamknięcie pozycji (ANEKS_TEACH2-2, 18.11.2026)
- Werdykt L-A w pierwszym boocie (1/3). 200 s nauki z GNSS, potem
  600.52 s bez GNSS i bez znaczników nad parkingiem (c10, wahadło v2):
  B1–B4 bez naruszeń, zero REFUSE w misji, track 1.000, pasmo 0.971.
- Przesłanka: 12 638 ticków, zero przekroczeń, max e′/U′ 0.24. CC
  odtworzył własnym kodem z tabelą wpisaną z PRE; replay osłony
  0 różnic na 12 696 tickach; georeferencja z 3119 wiązań zgodna;
  3003 poprawki zgodne z datagramem do 0.0001 m.
- Błąd poprawki p50 / p95 / max 0.234 / 0.352 / 0.449 m, przyjęte
  3003/3003; w oknach po 100 s max 0.37–0.45 m bez trendu, przy
  błędzie własnym EKF rosnącym do 17.4 m.
- Mapa 1041 kadrów / 15 klatek kluczowych / 3119 wiązań; zamknięcie
  383 ms w locie (206 ms przy biurku); poprawka w osłonie 0.464 s po
  fladze; zero zgubionych klatek, zero wolnych klatek kluczowych.
- Predykcje PRE 8/9 przy sumie szans 6.75 (✗ P-TEACH2-1); pozycja
  z reconem 15/16 przy 11.45.
- Lekcje:
  - mapa obejmująca całe zadanie zdejmuje jedyne ciasne miejsce
    bramki (krawędź mapy), a dłuższa nauka z GNSS zmniejsza błąd;
  - błąd poprawki z mapy nie zależy od dryfu EKF (korelacja −0.11
    przy dryfie do 17 m);
  - czasy z biurka nie przenoszą się na lot wprost: zamknięcie mapy
    pod obciążeniem symulacji trwało niemal dwa razy dłużej, a wolne
    klatki z renderu w gz nie wystąpiły;
  - „pierwsza poprawka po fladze" ma dwie miary: czas klatki i chwilę
    dotarcia do osłony; próg trzeba pisać na tej drugiej.
```

## §8. KIERUNKI_PO_PLANIE (append-only przy commicie §CO)

```
## Dopisek stanu katalogu — 18.11.2026 (CO-TEACH2-2, ANEKS_TEACH2-2)
- **TEACH-II — CLOSED, PASS (L-A).** Lot 10 minut bez GNSS i bez
  znaczników na mapie z 200 s własnego lotu z GNSS: jeden lot nad
  parkingiem, bez odmowy, litera bez naruszeń, błąd poprawki do
  0.45 m bez wzrostu w czasie. Sieć, osłona, tabela i tor mapy bez
  zmiany kodu.
- **Wątek lotu bez GNSS — stan:** ze znacznikami 10 minut (NADIR-II);
  zmierzony kontrakt źródła (NADIR-III); bez znaczników 12/12 na
  trzech terenach po 110 s (TEACH); bez znaczników 10 minut
  (TEACH-II).
- **Pozycje nieotwarte, osobnymi decyzjami Olgi:**
  - lot długi na osiedlu i łące oraz w komórce c05;
  - teren dla wszystkich kamer z nowym pomiarem G;
  - mapa z innego dnia albo przy innym świetle;
  - producent czasu rzeczywistego przy większych mapach (rozłożenie
    dopasowań, czas zamknięcia).
```

## §CO

Bramka: origin/master == **3b989e84**. Jeden commit [CO-TEACH2-2]:
korzeń `ANEKS_TEACH2-2.md` verbatim (byte-check sha256 z wiadomości CC)
+ KSIĘGA §7 i `KIERUNKI_PO_PLANIE.md` §8 append-only. Zero bootów,
zero zmian kodu i raportów. Push = Olga.
