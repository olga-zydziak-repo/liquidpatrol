# ANEKS_PETLA-1 — zamknięcie pozycji przy biurku: zdania „pętla nie dochodzi do odmowy" nie da się dowieść dla sieci takiej, jaka leci

LiquidPatrol · CC · 18.11.2026 · łańcuch PĘTLA, po STOP-PETLA-R
(859b02c8 na origin). Do ratyfikacji sygnałem **„ratyfikuję
PETLA-1"**. Sygnały bez numeru albo nazwy odrzucasz.

## §1. Weryfikacja CC z repo (wykonaniem, własnym kodem)

Krok sieci, silnik pętli i rodziny torów napisane osobno, bez kodu
wykonawcy i bez `net/models.py`.

1. **Stan.** b2146b1b [CO-TEACH2-2], edb4b5fd [CO-PETLA-0]
   i 859b02c8 na origin. `ANEKS_TEACH2-2.md` w korzeniu z sumą
   fae46515…ce12; bloki KSIĘGI i KIERUNKÓW obu commitów równe blokom
   z dokumentów, zero usuniętych wierszy. STOP nie dotyka niczego
   poza `results/PETLA_RECON/`.
2. **R2.** Liczby (a) i (b) wykonawca odtworzył swoim kodem; różnice
   to jeden tick w koszyku 10–10.5 m i inna granica „po 30 s"
   (45 388 wobec 45 686 stanów).
3. **Trzy kontrprzykłady, po 6000 ticków.** Stan i komenda z zapisu
   równe własnemu krokowi sieci do 1e-15. Cechy równe pozycjom
   z zapisu (w drugim z szumem o odchyleniu 0.31 / 0.33 / 0.04 m).
   Intruz w kole 11.000 m, najwyżej 0.500 / 0.997 / 0.500 m/s, na
   10 m. Zdarzenie w 34.90, 41.40 i 49.75 s, w górę, jak w raporcie.
4. **Skąd się bierze.** We wszystkich trzech dron wznosi się od
   pierwszego ticka (komenda pionowa −0.19 … −0.20 m/s przy stanie
   zerowym) i po 20 s jest na 16.8–17.6 m. Potem już tylko pełznie
   w górę.
5. **Start w lotach wygląda inaczej.** Pierwsza inferencja w 15
   lotach przypada na wysokości 7.8–8.5 m, czyli 2 m **pod**
   intruzem, w odległości 4.3–9.7 m. Sieć wznosi się wtedy do
   11.4–12.3 m w 15 s i staje; największa wysokość w pierwszych 30 s
   to 12.2–12.8 m. Prompt kazał startować z 12 m przy stanie zerowym.
6. **Zliczenie zdarzeń z plików biegów.** 56 zdarzeń w 126 000
   biegów sieci (7 rodzin × 5 napędów × szum i bez × dwie prędkości
   × 900), wszystkie w górę; czas zdarzenia w kwartylach 44.8 / 55.0
   / 71.8 s, 50 z 56 przed setną sekundą. Wariant W: 0 w 126 000.
7. **Powtórzenie własnym kodem, napęd N.**
   - Start z 12 m: 28 zdarzeń w 50 400 biegach (0.056%; u wykonawcy
     w napędzie N 15 w 25 200, czyli 0.060%). W 23 z nich wysokość
     wyszła poza ±3 m w pierwszych 20 s i już nie wróciła; w 4
     zdarzenie wyszło z lotu ustalonego, po co najmniej 60 s
     w normie.
   - Start z 8 m, jak w lotach: **2 zdarzenia w 50 400 biegach**,
     jedno z lotu ustalonego (w normie do 104. sekundy).
   - Wysokość po 20 s: przy starcie z 12 m 99.9. percentyl 15.8 m
     i maksimum 19.0 m; przy starcie z 8 m 14.1 i 14.7 m.
8. **Wariant W własnym kodem.** 0 zdarzeń w 25 200 biegach dla
   każdego ze startów; dystans prawdziwy do 11.08 m, promień drona
   do 20.74 m, odchylenie wysokości do 0.15 m.
9. **Napęd.** Własne dopasowanie pionu na skokach zejścia daje to
   samo (0.05 s + 0.1 s, błąd 0.056 m/s); zmierzone czasy narastania
   to 0.18 s do połowy skoku i 0.37 s do 90%. W1 liczone per
   składową wychodzi CC na 0.100 m/s, co odpowiada 0.142 wykonawcy
   dla wektora.
10. **Opis stanów (R7).** 30 zapisanych najgorszych punktów
    przeliczone własnym krokiem: zgodne do 1e-15. Przy dystansie
    10.5–12.8 m sieć każe się w nich oddalać z prędkością od 1.1 do
    3.0 m/s. W opisie Ω1 wszystkie 20 stanów tych punktów leży
    w zakresie z lotów.
11. **Rachunek (R6).** 24.84 − 2.786 − 1.364 − 11.106 = 9.58 m;
    z dystansem z R5 9.83 m.

Niesprawdzone przez CC: W2 per lot (liczby zgodne z wcześniejszą
sondą CC na czterech lotach), przebieg szukania, czasy.

## §2. Werdykt

Recon rozstrzygnięty. **Ś2 i Ś5 zachodzą, Ś1, Ś3 i Ś4 nie.**

Pozycja **PĘTLA — CLOSED-BY-RECON, 0 bootów.** Zdania „w misji pętla
sieć–napęd–osłona nie dochodzi do odmowy" nie da się dowieść dla
sieci takiej, jaka leci:

- w pionie jest fałszywe na modelu: istnieją tory intruza z klasy
  lotów, po których wysokość dochodzi do granicy pionowej osłony;
- w poziomie nie ma go czym dowieść: każdy z trzech opisów zbioru
  stanów zawiera punkty, w których sieć ucieka od celu, więc zdanie
  jest na tych opisach fałszywe, a nie tylko niecertyfikowalne.
  Dowód wymagałby opisu wiążącego stan sieci z historią wejścia.

## §3. Zdania, które stoją

Wolno:

- Komenda pionowa sieci kopiuje własną prędkość pionową z wejścia
  (nachylenie 0.955 na 45 tys. ticków misji). O wysokości sieć wie
  tylko przez rel_z, z czułością 0.038 1/s, czyli stałą czasową
  około 26 s; w odpowiedzi ustalonej znak bywa odwrotny (17–24%
  z 400 stanów, zależnie od próby).
- W pętli nie ma odniesienia wysokości ani dolnej granicy: osłona
  sprawdza tylko |z| > 20 m.
- Sieć startowana ze stanu zerowego wznosi się o około 4 m. W lotach
  startuje 2 m pod intruzem i kończy na wysokości orbity.
  Wystartowana od razu z wysokości orbity przestrzeliwuje.
- Na modelu pętli istnieją tory intruza (koło 11 m, do 1 m/s),
  po których wysokość ucieka w górę do 20 m. Zdarzenie jest rzadkie
  i nieodporne: znika przy przesunięciu toru o 0.05 s. W 15 lotach
  nie zaszło.
- Z wysokością trzymaną regulatorem zewnętrznym model w 126 000
  biegów po 300 s i w szukaniu nie przekroczył dystansu 11.18 m ani
  promienia 20.81 m.
- Nierówność trójkąta przy przesłankach dowodu zamyka się dla koła
  intruza do 9.58 m w przedziale 0 tabeli i poniżej 8 m od
  przedziału 2; loty z kołem 11.0 m mieszczą się tylko przy błędach
  zmierzonych.

Nie wolno:

- „Sieć nie doprowadzi osłony do odmowy", „dowód obejmuje sieć",
  „pętla zweryfikowana formalnie".
- Podawać 56 zdarzeń ani ich udziału jako częstości w locie: większość
  pochodzi ze startu, którego w lotach nie ma.
- „Wiek tracka odwraca pościg" (§4).
- Przenosić liczb modelu na gz bez nazwania modelu.

## §4. Co wyszło poza planem

**Błędy CC.**

- Stan początkowy w prompcie (12 m, stan zerowy) wpisany z opisu,
  nie z lotu. Większość zdarzeń reconu to przestrzelenie po takim
  starcie: 23 z 28 w powtórzeniu CC. Litera Ś2 stoi, bo została
  zapisana dla tej klasy; przy starcie jak w lotach zdarzenie
  istnieje w napędzie N (2 z 50 400), a w napędach odchylonych nie
  było liczone.
- Sonda CC z §1(e) promptu zawyżyła częstość (do 16 z 900): pion
  miał w niej inercję 0.4 s zamiast zmierzonej 0.1 s i ten sam start.
- Ś4 zapisana bez wskazania przedziału tabeli. Rozliczona dla
  przedziału 0, jak (c).
- Udział odwrotnego znaku podany jako jedna liczba (14.7%) z jednej
  próby 400 stanów; trzy próby dają 17–24%.

**Błędy wykonawcy.**

- „56 na 63 000 biegów": biegów sieci było 126 000.
- Silnik pętli opóźnia komendę o tick więcej, niż mówi tabela
  napędów: 8 i 2 ticki zamiast dopasowanych 7 i 1. Wniosków to nie
  zmienia (dopasowane 0.35 s leży między H− a N silnika), ale
  tabela nie opisuje tego, co liczono.
- „Sam wiek tracka odwraca pościg przy d ≥ 9 m" napisane bez
  porównania z wiekiem faktycznym. Na tych samych 7240 stanach
  przy wieku faktycznym najmniejsza składowa ku celowi to −1.600,
  przy podmienionym −1.607 … −1.638; wiek przesuwa ją najwyżej
  o 0.19 m/s. Od 10.5 m zostaje 0.85–0.88 m/s przy każdym wieku.

**Co recon dał ponad pytanie.** Trzy rzeczy, których nie było
w żadnym raporcie: kanał pionowy sieci nie jest regulatorem
wysokości; start sieci ma niezapisany warunek wstępny (wysokość
zawisu home); litera dostępności liczy ticki ściany R-G-NOM jako
odmowę, choć lot trwa.

## §5. Proces

- Sekwencja czysta: ratyfikacja TEACH2-2, otwarcie, recon i STOP
  w jednej sesji, 25 minut liczenia przy budżecie 120.
- Wymóg „wektory, nie statystyki" zadziałał: kontrprzykłady dały się
  sprawdzić tick po ticku, a zliczenie zdarzeń z plików wykryło błąd
  mianownika.
- Lekcja do następnych promptów: stan początkowy symulacji wpisuje
  się z pierwszego ticka lotów (wysokość, dystans, prędkość), a wynik
  podaje osobno dla startu i dla lotu ustalonego.
- Lekcja druga: zdanie o wpływie zmiennej wymaga wartości
  odniesienia obok.

## §6. Rozliczenie predykcji

- P-PETLA-R1 (0.90) ✓ — 0.0027 m/s na 57 222 tickach; 0.883 m/s.
- P-PETLA-R2 (0.75) ✓ — W1 0.142 przy progu 0.15, W2 13 z 15.
- P-PETLA-R3 (0.90) ✓ — mediana 0.992; znak odwrotny 23.75%.
- P-PETLA-R4 (0.60) ✓ — Ś2 zachodzi, z zastrzeżeniem z §4.
- P-PETLA-R5 (0.40) ✗ — odporność 0, 1 i 0 z 20.
- P-PETLA-R6 (0.75) ✓ — 11.18 m i 20.81 m.
- P-PETLA-R7 (0.85) ✓ — 9.58 m.
- P-PETLA-R8 (0.70) ✓ — 9.83 m w przedziale 0.
- P-PETLA-R9 (0.30) ✗ — certyfikowane 0.0%.

7 z 9 przy sumie szans 6.15.

## §7. KSIĘGA (append-only przy commicie §CO)

```
## PĘTLA — recon i zamknięcie pozycji (ANEKS_PETLA-1, 18.11.2026)
- CLOSED-BY-RECON, 0 bootów. Ś2 i Ś5 zachodzą. Zdania „w misji pętla
  sieć–napęd–osłona nie dochodzi do odmowy" nie da się dowieść dla
  sieci takiej, jaka leci: w pionie fałszywe na modelu, w poziomie
  fałszywe na każdym z trzech opisów zbioru stanów (certyfikat 0%).
- Znaleziska: komenda pionowa sieci kopiuje własną prędkość pionową
  (nachylenie 0.955), trzymanie wysokości ze stałą czasową 26 s;
  w pętli brak odniesienia wysokości i dolnej granicy; sieć
  startowana ze stanu zerowego wznosi się o około 4 m (w lotach
  start 2 m pod intruzem).
- Model: 56 zdarzeń ucieczki wysokości w 126 000 biegów po 300 s,
  wszystkie w górę, 50 przed setną sekundą. CC własnym kodem: start
  z 12 m 28 w 50 400, start z 8 m jak w lotach 2 w 50 400. Wariant
  z wysokością trzymaną z zewnątrz: 0 zdarzeń, dystans do 11.18 m,
  promień do 20.81 m.
- Rachunek złożenia: przy przesłankach dowodu koło intruza do 9.58 m
  (przedział 0), loty miały 11.0 m.
- Predykcje 7/9 przy sumie szans 6.15 (✗ R5, R9).
- ✗ CC: stan początkowy symulacji wpisany z opisu, nie z lotu;
  sonda z niedopasowanym pionem; Ś4 bez przedziału; jedna próba dla
  udziału znaku. ✗ wykonawca: mianownik zdarzeń; opóźnienie silnika
  o tick większe niż w tabeli; wniosek o wieku tracka bez wartości
  odniesienia.
- Lekcje:
  - stan początkowy symulacji bierze się z pierwszego ticka lotów,
    a wynik podaje osobno dla startu i lotu ustalonego;
  - zdanie o wpływie zmiennej wymaga wartości odniesienia;
  - szukanie kontrprzykładów przed dowodem kosztowało 25 minut
    i zamknęło pytanie, którego dowód by nie zamknął.
```

## §8. KIERUNKI_PO_PLANIE (append-only przy commicie §CO)

```
## Dopisek stanu katalogu — 18.11.2026 (CO-PETLA-1, ANEKS_PETLA-1)
- **PĘTLA — CLOSED-BY-RECON.** Dowodu obejmującego wnętrze sieci nie
  będzie: zdanie o braku odmowy jest fałszywe na modelu w pionie
  i niecertyfikowalne w poziomie własnymi narzędziami. Sieć, osłona
  i kod lotu bez zmian.
- **Pozycje nieotwarte, osobnymi decyzjami Olgi:**
  - PION — wysokość poza siecią: komenda pionowa z regulatora na
    wysokość odniesienia, z dolną i górną granicą oraz certem
    obwiedni pionowej; wymaga PRE i lotów regresji. Zdejmuje
    ucieczkę wysokości i warunek wstępny startu;
  - ŚCIANA — reguła bez zatrzasku wewnątrz bariery piły bez GNSS,
    razem z poprawką litery dostępności (ticki ściany nie są
    odmową). Z PION-em daje zdanie o braku odmowy dla dowolnego
    sterownika o ograniczonej komendzie;
  - dowód relacyjny wnętrza sieci (opis stanu związany z historią
    wejścia albo narzędzia zewnętrzne) — nie otwierać bez nowego
    pomysłu na opis.
```

## §CO

Bramka: origin/master == **859b02c8**. Jeden commit [CO-PETLA-1]:
korzeń `ANEKS_PETLA-1.md` verbatim (byte-check sha256 z wiadomości CC)
+ KSIĘGA §7 i `KIERUNKI_PO_PLANIE.md` §8 append-only. Zero bootów,
zero zmian kodu i raportów. Push = Olga.
