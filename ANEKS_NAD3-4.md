# ANEKS_NAD3-4 — zamknięcie nogi: bramka S3 werdykt V-A — litera bezpieczeństwa bez naruszeń w 12 cięciach i 8 epizodach nominalnych, P1 dostępne 4 z 4; zmierzony kontrakt źródła: 1 Hz, błąd do 1.0 m

LiquidPatrol · CC · 15.11.2026 · łańcuch NAD3, po STOP-NAD3-3
(8ddcb40c na origin). Do ratyfikacji sygnałem **„ratyfikuję NAD3-4"**.
Sygnały bez numeru albo nazwy odrzucasz.

## §1. Weryfikacja CC z repo (wykonaniem, własnym kodem)

Tabele trzech punktów wpisane z liczb PRE §4, nie z plików FREEZE;
e′ liczone z wierszy ramy jako |p_corr − GT|; koniec misji to komenda
zejścia planowego albo pierwsza odmowa.

1. **Przesłanka.** 12 cięć, 25 278 ticków utraty, ocenione 24 285:
   **zero przekroczeń e′ ≤ U′**, największe zużycie granicy 0.539
   (P3, c05, na zewnątrz). Nieocenione 993 — wszystkie po zatrzasku
   τ\* w zejściu; w misji 0 w każdym z 12 lotów.
2. **Bariera i wejście osłony.** Bariera z mojego wzoru zgodna
   z zapisem w każdym ocenionym ticku; `r_est` = |p_corr| w każdym
   ticku utraty.
3. **Degradacja.** Między cięciem a końcem misji poprawki co 1.000 s
   w 12 z 12 lotów. Wektor błędu 1.00 / 1.75 / 2.75 m z dokładnością
   0.0001 m, w całości radialny, znak zgodny z planem w każdej
   poprawce.
4. **Odmowy w misji: dwie, obie bariera, obie c10 przy biasie na
   zewnątrz.** P2 po 8.94 s od cięcia (`r_est` 21.194 > 21.125 m,
   r_GT 19.137 m); P3 po 7.88 s (19.832 > 19.625 m, r_GT 16.832 m).
   W pozostałych dziesięciu cięciach kontynuacja 110.5 s, a zatrzask
   τ\* dopiero 4.3–10.0 s po komendzie zejścia.
5. **(B2).** Największy r_GT w całym locie 19.22 m przy R_E 32 m.
6. **Nominały.** 8 z 8 epizodów, 12 463 ticki: wszystkie NOMINAL
   i ALLOW przy włączonej degradacji; akwizycja 8 z 8.
7. **Kod.** Od S1 (69128dba) w kodzie lotu, osłonie, degradacji,
   analizatorze i tabelach zmienił się jeden plik: strażnik manifestu
   w `nad3_boot.sh` (ANEKS_NAD3-1).

Liczby raportu wykonawcy potwierdzone. Różnice w trzeciej cyfrze
max e′/U′ wynikają z chwili odczytu GT.

## §2. Werdykt

1. Litera bezpieczeństwa B1–B5: **0 naruszeń** w 12 cięciach
   i 8 epizodach nominalnych.
2. Dostępność P1: **4 z 4** przy progu 3.
3. **Werdykt V-A. NADIR-III — CLOSED, PASS.** Loty 14 z 14 ważne,
   rezerwa nietknięta. Budżet nogi 18 z 22.

## §3. Zdanie, które stoi

Dowód zawierania i osłona z NADIR-II działają bez zmiany reguły, gdy
poprawka pozycji przychodzi raz na sekundę z błędem ograniczonym do
1.0 m: sieć NCP-20 prowadzi zadanie przez 110 s po utracie GNSS
w 4 z 4 lotów, bez odmowy, przy promieniu do 18.9 m i zapasie bariery
co najmniej 2.2 m. Przy większym błędzie bezpieczeństwo nie pęka —
osłona odmawia wcześniej: przy 1.75 m i 2.75 m odmowa zapadła w lotach,
w których dron wyszedł poza promień dopuszczony regułą, a w pozostałych
zadanie trwało pełne 110 s. Na 12 lotach z błędem 1.0–2.75 m przesłanka
|p_corr − GT| ≤ U′ trzymała w każdym z 24 285 ticków, przy największym
zużyciu granicy 54%.

**Kontrakt dla źródła poprawki**, przy zadaniu do 20 m od środka
strefy: poprawka absolutna co najmniej raz na sekundę; błąd ograniczony
i wolnozmienny. Zmierzone w pętli: 1.0 m. Z rachunku, sprawdzonego
w dwóch punktach kontrolnych: dostępność do 1.37 m, bezpieczeństwo do
2.28 m.

**Granice zdania:** SITL, jedna sceneria. Błąd jest wstrzyknięty,
ograniczony z konstrukcji, radialny, o stałym znaku; źródłem nadal są
znaczniki. Zdanie nie mówi nic o ogonie błędu prawdziwego źródła ani
o szumie szybkozmiennym. Próg P1 stoi na czterech lotach. Wynik
dotyczy lotów z akwizycją celu i wysokości misji, nie zejścia.

## §4. Gdzie było ciasno i co wyszło poza planem

- **Odmowa zapada tuż przed następną poprawką.** Obie odmowy padły
  w ostatnim przedziale τ (0.95–0.96 s), gdy U′ jest największe.
  Moment odmowy ustawia więc częstość, nie tylko błąd. W P2 o odmowie
  zdecydowało 0.07 m.
- **Geometria zdecydowała o drabinie.** Komórka c05 lata do 16.1 m
  i pozostała dostępna nawet przy 2.75 m (zapas bariery min 1.09 m).
  Odmowy stoją na c10. Wymaganie zależy od promienia faktycznego.
- **Kierunek błędu zmienia tor, ale nie o E.** W czterech parach
  o pełnych oknach lot z biasem do środka poleciał dalej o 0.37–0.79 m.
  W c05 pięć lotów bez biasu do środka mieści się w 15.39–15.53 m,
  trzy z biasem do środka w 15.76–16.14 m; różnica nie rośnie z E.
  Obie hipotezy sprzed lotów są w treści odrzucone: „przesunięcie
  o E" (wykonawca) i „brak przesunięcia" (CC). Mechanizm niezmierzony;
  kandydat: zmiana Δ co sekundę przechodząca przez filtr tracku.
- **Skok ramy do 5.44 m** (około 2E) przy przejściu blisko środka,
  gdy kierunek biasu się odwraca — artefakt modelu radialnego. W tym
  locie track i pasmo 1.000; bramka predykcji tracku (6 m) nie została
  przekroczona. Pięć lotów miało skok ponad zakres treningowy
  (2.65 m).
- **Odrzucenia bramki predykcji tracku:** do 51 na lot, bez wpływu na
  zadanie.

## §5. Proces

Dwie poprawki narzędzi w trakcie kampanii. Kolejka zawisła przed
pozycją 3 (wątki bramki zdrowia w procesie kolejki) i została
poprawiona commitem 0567bcbc bez STOP-u i bez sygnału; boot nie
przepadł. To ta sama wada i ta sama droga naprawy co w NAD2 —
kolejkę skopiowano ze wzoru sprzed tamtej poprawki, a reguła
z ANEKS_NAD2-2 §5 (zmiana narzędzia w kampanii przechodzi przez STOP)
znów nie zadziałała. Sędzia lotu pominął odmowę pozycji 7 i został
poprawiony przed raportem; analizator litery liczył ją poprawnie.
Obie zmiany dotyczą narzędzi wokół lotu, kod lotu jest nietknięty
(§1.7), a CC przeliczył wynik niezależnie — werdyktu nie dotykają.
Na przyszłość: jeden wzorzec kolejki z naniesionymi poprawkami,
kopiowany w całości.

## §6. Rozliczenie predykcji PRE

- P-NAD3-1 (0.80) ✓ — bramka promienia na pierwszym manifeście, pięć
  epizodów z misją (ANEKS_NAD3-2).
- P-NAD3-2 (0.75) ✓ — P1 4 z 4 bez odmowy w misji.
- P-NAD3-3 (0.90) ✓ — zero przekroczeń, max 0.539 przy progu 0.75.
- P-NAD3-4 (0.65) ✓ literą — |Δ r_max| < 1.0 m w 5 z 6 par. W treści
  teza CC „tor się nie ruszy" nie trzyma (§4).
- P-NAD3-5 (0.75) ✗ — P3 na zewnątrz: odmowa w 1 z 2 (c10 tak, c05
  nie). Predykcja zakładała promień obu komórek ponad 16.55 m.
- P-NAD3-6 (0.60) ✓ — P2: jedna odmowa w czterech cięciach.
- P-NAD3-7 (0.70) ✗ literą — REFUSE(τ\*) zapadł w zejściu w 10 z 12
  cięć; w misji 0 z 12. Predykcja nie wyłączała zejścia, choć wzór
  był znany z NAD2.

Bramka: 5 z 7 przy sumie szans 5.15. Cała noga z reconem: 9 z 13
przy sumie 9.40.

## §7. KSIĘGA (append-only przy commicie §CO)

```
## NADIR-III — bramka i zamknięcie nogi (ANEKS_NAD3-4, 15.11.2026)
- Werdykt V-A. 12 cięć (3 poziomy błędu × 2 komórki × 2 kierunki
  biasu) i 2 nominały: B1–B5 bez naruszeń; P1 dostępne 4/4 (próg 3).
  14/14 lotów ważnych, rezerwa 0/3, noga 18/22.
- Przesłanka: 24 285 ticków, zero przekroczeń, max e′/U′ 0.539.
  CC odtworzył własnym kodem z tabelami wpisanymi z PRE §4.
- Odmowy w misji: 2, obie REFUSE(bariera) w c10 na zewnątrz (P2 po
  8.94 s, P3 po 7.88 s). REFUSE(τ*) w misji 0.
- Kontrakt źródła przy zadaniu do 20 m: 1 Hz, błąd ograniczony;
  zmierzone 1.0 m; rachunek 1.37 m (dostępność) i 2.28 m
  (bezpieczeństwo).
- Predykcje bramki 5/7 przy sumie szans 5.15 (✗ P-NAD3-5, ✗ literą
  P-NAD3-7); noga łącznie 9/13 przy 9.40.
- Lekcje:
  - wymaganie na źródło wyznacza dostępność, nie bezpieczeństwo —
    osłona liczy błąd dwa razy;
  - odmowa zapada w ostatnim przedziale τ, więc częstość ustawia jej
    moment;
  - błąd stały znosi się w wejściu sieci, błąd zmienny w czasie
    przechodzi przez filtr tracku i przesuwa tor o ułamek E;
  - predykcja o odmowach musi nazywać fazę lotu;
  - zmiana narzędzia w kampanii bez STOP-u — drugi raz (NAD2, NAD3).
```

## §8. KIERUNKI_PO_PLANIE (append-only przy commicie §CO)

```
## Dopisek stanu katalogu — 15.11.2026 (CO-NAD3-4, ANEKS_NAD3-4)
- **NADIR-III — CLOSED, PASS (V-A).** Zdegradowane źródło poprawki:
  dowód i osłona NAD2 znoszą poprawkę 1 Hz z błędem do 1.0 m przy
  zadaniu do 20 m (4/4 lotów); przy 1.75 i 2.75 m osłona odmawia
  zgodnie z regułą, bezpieczeństwo bez naruszeń w 12 cięciach.
- **Następna pozycja wątku, nieotwarta: źródło absolutne bez
  znaczników** (dopasowanie obrazu z kamery w dół do mapy scenerii).
  Bramka wejścia z tej nogi: błąd największy, nie typowy, do 1.0 m
  przy co najmniej 1 Hz, bez skoków poza granicę. Pierwszy krok to
  pomiar ogona błędu na zapisanych klatkach, przy biurku. Otwarcie
  tylko decyzją Olgi.
- Obserwacje bez pozycji: tor zależy od kierunku błędu o 0.4–0.8 m
  (mechanizm niezmierzony); admisja celu stojącego (dopisek
  CO-NAD3-2).
```

## §CO

Bramka: origin/master == **8ddcb40c**. Jeden commit [CO-NAD3-4]:
korzeń `ANEKS_NAD3-4.md` verbatim (byte-check sha256 z wiadomości CC)
+ KSIĘGA §7 i `KIERUNKI_PO_PLANIE.md` §8 append-only. Zero bootów,
zero zmian kodu i raportów. Push = Olga.
