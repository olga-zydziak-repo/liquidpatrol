# ANEKS_ARKUSZ-1 — zamknięcie pozycji przy biurku: arkusz jest, dowodu na tych wagach nie ma

LiquidPatrol · CC · 20.11.2026 · łańcuch ARKUSZ, po STOP-ARKUSZ-R
(9e627e38 na origin). Do ratyfikacji sygnałem **„ratyfikuję
ARKUSZ-1"**. Sygnały bez numeru albo nazwy odrzucasz.

## §1. Weryfikacja CC z repo (wykonaniem, własnym kodem)

Krok sieci, silnik pętli, siatka komórek i arytmetyka przedziałowa
napisane osobno, bez kodu wykonawcy.

1. **Stan.** db497e4c [CO-ARKUSZ-0] i 9e627e38 na origin. Bloki
   KSIĘGI i KIERUNKÓW równe blokom z promptu co do znaku, 39 wierszy
   dopisanych, zero usuniętych. STOP nie dotyka niczego poza
   `results/ARKUSZ_RECON/` (43 pliki).
2. **Arkusz na lotach.** Sonda CC sprzed promptu (mapa z drzew, te
   same pięć lotów testowych) dała 0.3% wariancji niewyjaśnionej
   i resztę p99 0.060; wykonawca mapą afiniczną w komórkach 0.22%
   i 0.057. Dwie różne mapy, ten sam wynik.
3. **Arkusz w modelu.** Własne biegi (600 po 120 s, 1.08 mln stanów,
   45 611 komórek): półszerokość pudełek stanu p50 0.031, p99 0.093,
   max 0.176, żadna ponad 0.25.
4. **Arkusz na innej kampanii** (tego recon nie liczył). Mapa
   z 15 lotów TEACH przyłożona do 48 lotów NCP nogi LIQ: inny feed,
   GNSS, 48 scenariuszy ławki. Replay 67 586 ticków, komenda zgodna
   z logiem do 0.0018 m/s. Reszta w normie max: p50 0.074, p99 0.28,
   max 0.67; ponad 0.25 w 1.4% ticków po ósmej sekundzie. Połowa
   ticków LIQ leży poza zakresem sytuacji z lotów, na których mapa
   powstała, a reszta jest tam taka sama (p99 0.28 wobec 0.28).
   Arkusz przenosi się więc między kampaniami, ale jest kilkakrotnie
   grubszy niż na lotach tej samej kampanii (p50 0.074 wobec 0.014,
   p99 0.28 wobec 0.115).
5. **Pięć lotów FAIL z LIQ** (d_dmin) nie odstaje od arkusza: 0.05%
   ticków ponad 0.25 wobec 1.5% w lotach zaliczonych. W dziesięciu
   sekundach przed minimum dystansu z cech reszta zostaje poniżej
   0.28 i nie narasta ku minimum w żadnym z pięciu.
6. **Stany czułe.** Sonda CC (po 20 krokach mediana 0.066, wzrost
   w 0.03% prób) leży między dwoma rozkładami wykonawcy (0.056
   i 0.005%; 0.093 i 0.052%).
7. **Jakobian kroku** na 23 040 stanach własnych biegów (kontrola
   różnicami skończonymi 1e-10): promień spektralny mediana 0.921,
   p99 0.968, max 1.042; promień macierzy modułów mediana 2.10;
   norma max mediana 3.42. U wykonawcy 0.92, 2.12 i 3.46.
8. **Pudełka.** Punkt stały po grafie przejść kodem CC: rozejście do
   pełnego zakresu stanu w dwóch iteracjach, półszerokość p50 0.82
   już po pierwszej. Test procedury na 200 000 punktów bez wyjątku.
9. **Kontrprzykłady do lematu k-krokowego** odtworzone. Własne Δ:
   0.309 m, 0.0506 rad, 0.231 i 0.116 m/s (wykonawca 0.321, 0.0528,
   0.238, 0.123). Stałe pchnięcie z 200 000 prawdziwych stanów,
   miarą odległość od pudełka danych komórki końcowej:
   - k = 1: cztery przypadki ponad 0.25, największy 0.295;
   - k = 10: max 0.61, komórki startowe niosą 11.3% czasu (10.7%);
   - k = 20: max 0.84, 24.4% czasu (20.4%).
10. **Skąd kontrprzykłady.** W biegach dystans zmienia się przez 20
    ticków najwyżej o 2.66 m, namiar o 0.47 rad. Stałe pchnięcie ±Δ
    daje 6.18 m i 1.01 rad, czyli 2.3 i 2.2 raza więcej; dla
    prędkości 1.6 raza. Klasa wejść z promptu dopuszcza ciągi,
    których pętla nie umie wytworzyć.
11. **Jedna metryka kwadratowa** (poza promptem). Szukana macierz,
    w której krok jest skurczem na stanach arkusza; uczenie na
    11 520 stanach, ocena na 11 520 z innych biegów. Najlepsza
    znaleziona: wzmocnienie mediana 1.02, p99 1.13, max 1.17, skurcz
    w 32% stanów (w normie zwykłej w żadnym, mediana 1.71). To
    szukanie gradientowe, nie dowód nieistnienia.
12. **Tablica.** Zera w `r3_tabela.json` zgodne z raportem.

Niesprawdzone przez CC: kod szczebli D2 i D3, pętla zamknięta z R2
(525 000 prób), R4 warunkowe, sufit punktu stałego, wymiar arkusza.

## §2. Werdykt

Recon rozstrzygnięty. **Ś4 zachodzi, Ś1, Ś2 i Ś3 nie.**

Pozycja **ARKUSZ — CLOSED-BY-RECON, 0 bootów.**

- Arkusz istnieje. Zmierzony dwiema mapami na lotach, w modelu
  i z samych wag, przez wykonawcę i przez CC, oraz na drugiej
  kampanii.
- Lematu arkusza na wagach zamrożonych nie dowodzi żaden szczebel:
  0% czasu pobytu. Przyczyna jest zmierzona. Krok sieci ma promień
  spektralny 0.92, ale macierz modułów jakobianu ma promień 2.1,
  więc rekurencja półszerokości pudełek nie ma punktu stałego przy
  żadnym skalowaniu osi. Sieć kurczy dopiero po kilku do kilkunastu
  krokach
  (po 10 mediana 0.13–0.22), a złożenie ograniczeń
  przedziałowych przez 10 kroków rośnie do 10¹³.
- Lemat k-krokowy w brzmieniu promptu jest fałszywy. To błąd CC
  w definicji wejść (§4), nie właściwość sieci.

Dowód obejmujący sieć na wagach, które lecą, jest po dwóch
podejściach zamknięty: PĘTLA (pudełka w przestrzeni cech) i ARKUSZ
(pudełka stanu, współrzędne arkusza, baza własna, jedna metryka
kwadratowa).

## §3. Zdania, które stoją

Wolno:

- W locie ustalonym stan sieci jest funkcją bieżącej sytuacji
  (dystans, namiar, prędkości własne, różnica wysokości). Na lotach
  testowych sytuacja wyjaśnia 99.8% wariancji stanu, reszta p99 0.057
  przy rozrzucie neuronu 0.31; sytuacja sprzed 0.5 i 1.0 s nic nie
  dodaje. Arkusz ma sześć wymiarów.
- Na 48 lotach innej kampanii ta sama mapa zostawia resztę p50 0.074
  i p99 0.28.
- Pamięć sieci jest skończona: ostatnie 8 s wejścia odtwarza stan
  do 0.002.
- Zaburzenie stanu o ±0.05 po 20 krokach rośnie w 0.005–0.05% prób.
  Stany czułe leżą tam, gdzie orbita nie jest ustalona (mała
  prędkość styczna); pętla spędza w nich 0.03% czasu w modelu
  i 0.09% w lotach.
- Krok sieci nie jest skurczem w jednym kroku w żadnej z badanych
  metryk; po 160 krokach żadna z miliona prób nie ma wzmocnienia
  ponad 0.23.
- Dowodu obejmującego sieć nie ma, i wiadomo dlaczego.

Nie wolno:

- „Dowód z mechanizmu", „lemat arkusza dowiedziony", „sieć
  zweryfikowana".
- Podawać d₀ = 9.5 m z R4 jako dowiedzione: liczone warunkowo, bez
  lematu.
- „Arkusz jest własnością sieci". To własność pętli: przy wejściach,
  jakich pętla nie wytwarza, stan schodzi z arkusza o 0.6–0.9.
- „Odległość od arkusza ostrzega przed porażką": pięć lotów FAIL
  z LIQ leży bliżej arkusza niż loty zaliczone.
- Podawać liczby z §5 jako wynik.

## §4. Co wyszło poza planem

**Błędy CC.**

- Wejścia dopuszczalne lematu zapisane jako osobne ograniczenie
  zmiany na tick dla każdej współrzędnej. Taka klasa nie ma pamięci,
  więc dopuszcza tę samą zmianę przez 20 ticków z rzędu: ponad dwa
  razy więcej, niż pętla umie. Lemat k-krokowy w tym brzmieniu jest
  fałszywy. Wykazał to wykonawca szukaniem, którego prompt nie
  zamawiał.
- Szanse kroku dowodu (P-6 0.55, P-7 0.30, P-8 0.50) postawione
  z sondy zjawiska, nie z sondy samego kroku. Własna sonda CC
  z 19.11 pokazała rozejście pudełek w dwóch iteracjach i ta
  informacja nie weszła do szans. Suma szans trzech predykcji 1.35,
  trafień zero.
- P-ARKUSZ-3 zapisana bez rozkładu zaburzenia; dwa rozsądne rozkłady
  dają 0.005% i 0.052%, czyli wynik po obu stronach dolnej granicy.

**Wykonawca.** Błędów w liczbach CC nie znalazł. D4 pominięty bez
uzasadnienia w raporcie; k = 10 i 20 tylko na 400 komórkach, co
raport podaje.

**Co recon dał ponad pytanie.** Szukanie kontrprzykładów i sufit
punktu stałego: bez nich wynik brzmiałby „szczeble za słabe", a jest
„zdanie fałszywe". Rozdzielenie trzech przyczyn porażki szczebli.
Wymiar arkusza.

## §5. Sonda CC po reconie (poza zakresem nogi; nie jest wynikiem)

Pytanie: czy przeszkoda dowodu leży w zadaniu i architekturze, czy
w wagach.

Uczeń o tej samej architekturze (NCP-20, 1903 parametry), na tych
samych danych i tej samej stracie, kodem treningu z repo. Jeden
dodatek: po każdym kroku optymalizatora rzut na ograniczenie
‖∂h′/∂h‖ ≤ 0.90 w normie max, ważne dla każdego stanu i wejścia. Dla
sieci zamrożonej to samo ograniczenie wynosi 32.4. Start z wag
zamrożonych, 900 epok, 4 minuty.

- **Naśladowanie.** Błąd na VAL 0.0473 wobec 0.0485 sieci
  zamrożonej; krzywa jeszcze malała.
- **Lot w modelu pętli** (wysokość z zewnątrz, 600 biegów po 120 s).
  Dystans p50 8.30 m, p99 9.58, max 10.32; sieć zamrożona 8.32, 9.55,
  10.32. Prędkość styczna średnio 1.54 m/s wobec 1.75; czas
  z prędkością styczną poniżej 1 m/s 9.3% wobec 4.5%.
- **Pudełka zwykłą arytmetyką przedziałową.** Punkt stały istnieje
  po 10 iteracjach (sieć zamrożona: rozejście w dwóch). Pudełka są
  grube, półszerokość p50 0.71, i prawo pościgu z nich nie wychodzi.
- **Oszacowanie pierwszego rzędu** tego, co dałyby formy afiniczne.
  Nie jest ograniczeniem ścisłym: człony krzywizny pominięte.
  Rzeczywista norma kroku w środkach komórek p50 0.32, max 0.375.
  Punkt stały po 7 iteracjach, półszerokość p50 0.114, max 0.204:
  wszystkie komórki poniżej 0.25. To samo oszacowanie na sieci
  zamrożonej rozchodzi się w trzech iteracjach (norma kroku p50
  3.44).
- **Prawo pościgu w tym oszacowaniu**, liczone bez pudełkowania
  stanu przed odczytem. Przy dystansie od 9.5 m składowa komendy ku
  celowi co najmniej 0.52 m/s (0.3 po przycięciu normy) w 99.7%
  komórek i 98.3% czasu, minimum 0.50. Od 10 m w każdej komórce,
  minimum 0.89. Od 9.25 m w 93%, minimum 0.27.

Czego sonda nie mówi: ograniczenia ścisłego (krzywizna,
zaokrąglenia), pełnego zbioru przejść dopuszczalnych, modelu wejść
z twardą obwiednią szumu, zachowania w gz. Wolniejsza orbita to
kierunek, w którym w LIQ przegrywało GRU.

Wniosek sondy: przeszkoda leży w wagach. Trening nie prosił sieci
o skurcz w jednym kroku, więc go nie ma; uczeń, którego o to
poproszono, naśladuje nauczyciela tak samo.

## §6. Proces

- Recon: 52 minuty liczenia, zero bootów.
- Lekcja: przed promptem dowodu sonduje się sam krok dowodu, nie
  tylko zjawisko, na którym dowód ma stanąć, i z tej sondy stawia
  szansę.
- Lekcja: klasa wejść w lemacie o układzie z pamięcią sama musi
  pamiętać (ograniczenie zmiany skumulowanej albo zamknięta pętla).
- Lekcja: szukanie kontrprzykładów zamawia się w prompcie razem
  z dowodem. Drugi raz z rzędu rozstrzygnęło więcej niż dowód.

## §7. Rozliczenie predykcji

- P-ARKUSZ-1 (0.90) ✓ — 0.22% i 0.057.
- P-ARKUSZ-2 (0.85) ✓ — 0 z 30 605 komórek.
- P-ARKUSZ-3 (0.85) ✗ — 0.0050% przy rozkładzie jednostajnym, poniżej
  przedziału; 0.052% w narożnikach, w przedziale. Liczona jako
  chybiona, bo predykcja nie nazwała rozkładu.
- P-ARKUSZ-4 (0.60) ✓ — 0.038% prób; 0.03% i 0.09% czasu.
- P-ARKUSZ-5 (0.90) ✓ — D1 0%.
- P-ARKUSZ-6 (0.55) ✗ — Ś4 zachodzi.
- P-ARKUSZ-7 (0.30) ✗ — 0%.
- P-ARKUSZ-8 (0.50) ✗ — 0 komórek.

4 z 8 przy sumie szans 5.45.

## §8. KSIĘGA (append-only przy commicie §CO)

```
## ARKUSZ — recon i zamknięcie pozycji (ANEKS_ARKUSZ-1, 20.11.2026)
- CLOSED-BY-RECON, 0 bootów. Ś4 zachodzi, Ś1–Ś3 nie. Lemat arkusza
  dowiedziony dla 0% czasu pobytu na każdym szczeblu (D1, D2, D3).
- Arkusz istnieje: loty testowe 0.22% wariancji niewyjaśnionej,
  reszta p99 0.057; model 0 komórek pofałdowanych; wymiar 6; z wag
  stan odtwarzany z 8 s wejścia do 0.002. CC: ta sama mapa na 48
  lotach LIQ zostawia resztę p50 0.074, p99 0.28.
- Stany czułe rzadkie: po 20 krokach wzrost w 0.005–0.05% prób,
  0.03% czasu w modelu i 0.09% w lotach.
- Przyczyna porażki dowodu zmierzona: promień spektralny kroku 0.92,
  promień macierzy modułów jakobianu 2.1, norma max 3.4; skurcz
  dopiero wielokrokowy, złożenie ograniczeń przez 10 kroków 10¹³.
  CC: jedna metryka kwadratowa daje skurcz w 32% stanów.
- Lemat k-krokowy w brzmieniu promptu fałszywy: stałe pchnięcie ±Δ
  przez 10 i 20 ticków wyprowadza stan o 0.6–0.9 od arkusza
  w komórkach niosących 10.7% i 20.4% czasu (CC: 11.3% i 24.4%).
- Predykcje 4/8 przy sumie szans 5.45 (✗ 3, 6, 7, 8).
- ✗ CC: klasa wejść lematu bez pamięci; szanse kroku dowodu
  postawione z sondy zjawiska, mimo własnej sondy z rozejściem
  pudełek; P-3 bez rozkładu zaburzenia.
- Sonda CC po reconie (nie wynik): uczeń o tej samej architekturze
  z rzutem na ‖∂h′/∂h‖ ≤ 0.90 w normie max naśladuje nauczyciela
  jak sieć zamrożona (VAL 0.0473 wobec 0.0485); pudełka mają punkt
  stały; w oszacowaniu pierwszego rzędu prawo pościgu od 9.5 m
  w 99.7% komórek. Orbita w modelu wolniejsza (1.54 wobec 1.75 m/s).
- Lekcje:
  - przed promptem dowodu sonduje się sam krok dowodu i z tej sondy
    stawia szansę;
  - klasa wejść w lemacie o układzie z pamięcią sama musi pamiętać;
  - szukanie kontrprzykładów zamawia się razem z dowodem.
```

## §9. KIERUNKI_PO_PLANIE (append-only przy commicie §CO)

```
## Dopisek stanu katalogu — 20.11.2026 (CO-ARKUSZ-1, ANEKS_ARKUSZ-1)
- **ARKUSZ — CLOSED-BY-RECON.** Arkusz stanów sieci zmierzony; lemat
  arkusza niedowiedziony (0%), lemat k-krokowy w brzmieniu promptu
  fałszywy. Sieć, osłona i kod lotu bez zmian.
- **Dowód obejmujący sieć na wagach zamrożonych — zamknięty** po
  dwóch podejściach (PĘTLA, ARKUSZ). Nie otwierać ponownie rodziną
  pudełek, współrzędnych arkusza ani jednej metryki kwadratowej:
  promień macierzy modułów jakobianu kroku wynosi 2.1.
- **Kandydat BLIŹNIAK — nieotwarty, osobną decyzją Olgi.** Uczeń
  o tej samej architekturze, kurczący z konstrukcji, i dowód prawa
  pościgu na nim; sieć zamrożona jako kontrola. Najpierw recon przy
  biurku (0 bootów), loty dopiero po jego przejściu. Sonda CC
  w ANEKS_ARKUSZ-1 §5. Zakłada wynik PION-u.
- **KOPIA** — nieotwarta; prompt z 19.11 nieaktualny (bramka
  6d8cbaf0). Rekomendacja CC: jedna noga treningu, nie dwie; dźwignie
  KOPII do rozważenia w BLIŹNIAKU.
- **PION, ŚCIANA** — bez zmian (PION: rekomendacja przyjęta 19.11,
  pozycja nieotwarta).
- **Pakowanie** (artykuł, nota, film) — odłożone; każda kolejna noga
  je przesuwa.
```

## §CO

Bramka: origin/master == **9e627e38**. Jeden commit [CO-ARKUSZ-1]:
korzeń `ANEKS_ARKUSZ-1.md` verbatim (byte-check sha256 z wiadomości
CC) + KSIĘGA §8 i `KIERUNKI_PO_PLANIE.md` §9 append-only. Zero
bootów, zero zmian kodu i raportów. Push = Olga.
