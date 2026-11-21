# ANEKS_BLIZNIAK-1 — zamknięcie pozycji przy biurku: bliźniak jest dowodliwy i nie ma czym lecieć

LiquidPatrol · CC · 21.11.2026 · łańcuch BLIŹNIAK, po STOP-BLIZNIAK-R
(33249b72 na origin). Do ratyfikacji sygnałem **„ratyfikuję
BLIŹNIAK-1"**. Sygnały bez numeru albo nazwy odrzucasz.

## §1. Weryfikacja CC z repo (wykonaniem, własnym kodem)

1. **Stan.** 3b7f7f95 [CO-BLIZNIAK-0] i 33249b72 na origin. Bloki
   KSIĘGI i KIERUNKÓW równe blokom z promptu co do znaku, 45 wierszy
   dopisanych, zero usuniętych. STOP nie dotyka niczego poza
   `results/BLIZNIAK_RECON/`.
2. **Wagi.** Trening wykonawcy i sonda CC dały te same sieci: różnica
   wag B30 3.9·10⁻¹⁰, B50 2.1·10⁻⁹, B90 5.2·10⁻¹¹. K różni się
   o 2.2·10⁻³ przy tym samym błędzie VAL (0.04136 wobec 0.04137).
   Błąd VAL każdego ramienia przeliczony rachunkiem CC: zgodny do
   piątej cyfry.
3. **Ograniczenie B(W)** z zapisanych wag, rachunkiem CC: B30 = 0.3
   i B50 = 0.5 dokładnie; B90 ponad 0.9 o 3.3·10⁻¹⁶. Które z ramion
   C3 i C12 wychodzi ponad swoje γ, zależy od kolejności sumowania
   (u wykonawcy C3, u CC C12). To szum ostatniego bitu.
4. **Ławka offline B30** na wagach wykonawcy: 12/12 i 120/120.
5. **Model pętli silnikiem CC** na wagach wykonawcy (600 biegów po
   120 s), prędkość styczna średnio i w najgorszej rodzinie: Z 1.75
   i 1.36; GRU 1.69 i 1.10; C12 1.75 i 1.26; C3 1.58 i 0.85; B30
   1.54 i 0.82 m/s. U wykonawcy (2100 biegów po 90 s): 1.745 i 1.50;
   1.674 i 1.34; 1.725 i 1.46; 1.533 i 1.09; 1.478 i 0.99. Kolejność
   i odstępy te same.
6. **Profil prawa pościgu** przeliczony z tablic wykonawcy
   (1 003 520 komórek): S(0.3) we wszystkich komórkach od 10.5 m,
   S(0.6) od 11.25, S(1.0) od 11.75, S(1.2) od 12.25 m. Od 10.0 m
   471 wyjątków, pokrycie 99.934%. E1 i E2 nie dają 0.3 w żadnej
   komórce (maksimum −0.43 i −0.42 m/s).
7. **Niezależny test poprawności dowodu.** Własny krok sieci
   i własny generator historii (klasa Δ_A, start z dowolnego stanu,
   6 i 9 kroków): 96 547 komórek, w tym 30 000 o najmniejszym zapasie
   u wykonawcy i wszystkie wyjątki, razem 6 179 008 historii.
   Naruszeń ograniczenia E3: zero. Najmniejszy zapas między komendą
   a ograniczeniem 0.32 m/s. Najmniejsza składowa ku celowi: 0.74 m/s
   od 10.0 m, 1.36 od 10.5 m (wykonawca 0.776 i 1.324).
8. **Wyjątki przy 10.0 m.** 400 z 471 leży w komórkach z prędkością
   własną ponad 3.0 m/s, czyli ponad to, co sterownik umie zadać.
   Opis w raporcie (v_r −2.5…−1.0) jest węższy niż tablice
   (−3.2…1.75).
9. **Przesłanki na lotach TEACH**, rachunek CC na tickach misji
   15 lotów: P1 przy Δ_A 99.28%, wiek tracka ponad 0.15 s w 0.02%
   ticków, łącznie P1–P3 99.23% (wykonawca 99.23%).

Niesprawdzone przez CC: podział H-PAMIĘĆ, przebieg przy Δ_B, kontrola
na Z i K kodem wykonawcy, szukanie kierowane kontrprzykładów, pion
z sieci, rachunek złożenia.

## §2. Werdykt

Recon rozstrzygnięty. **Ś3 zachodzi. Ś2, Ś4 i Ś5 nie.** Ś1 zachodzi
co do litery dla ramienia B90 (ostatni bit), bez wpływu na wynik:
dowód stoi na B30, którego B(W) wynosi dokładnie 0.3. Decyzja
wykonawcy, by nie przerywać, jest przyjęta; przyczyna leży
w przepisie CC (§4).

Pozycja **BLIŹNIAK — CLOSED-BY-RECON, 0 bootów.**

- Na bliźniaku B30 prawo pościgu jest dowiedzione. Próg wyszedł
  10.5 m, nie 10.0 m zapisane w Ś3.
- Kandydata do lotów nie ma. W modelu pętli, który ustawia NCP, GRU
  i MLP w kolejności z lotów, bliźniaki krążą wolniej niż GRU.
- Ten sam kod dowodu na sieci zamrożonej i na jej uczciwej kontroli
  nie dowodzi niczego.

## §3. Zdania, które stoją

Wolno:

- Dla sieci B30 (architektura NCP-20, ograniczenie kroku 0.3
  policzone z wag) dowiedziono: przy każdej historii wejść z klasy 𝒞
  na dziedzinie 𝒟 i każdym stanie sprzed sześciu ticków komenda
  pozioma ma składową ku celowi co najmniej 0.3 m/s, gdy dystans
  wynosi co najmniej 10.5 m, i co najmniej 1.0 m/s od 11.75 m. To
  pierwsze ścisłe zdanie o sieci w programie.
- Stan B30 od piątego ticka po włączeniu leży w pudełku
  wyznaczonym przez bieżącą sytuację, o półszerokości najwyżej 0.31,
  niezależnie od stanu początkowego.
- Dowód jest ostrożny: prawdziwy próg z próbek leży między 9.5
  a 10.0 m, a zapas między komendą a ograniczeniem nigdzie nie
  spada poniżej 0.32 m/s.
- Przesłanki dowodu są spełnione w 99.1–99.2% ticków misji lotów
  z kamerą.
- Cena: błąd naśladowania +16% wobec kontroli; orbita w modelu pętli
  1.48 wobec 1.745 m/s, w najgorszej rodzinie 0.98–1.03 wobec 1.34
  dla GRU.
- Orbita wraca dopiero przy ograniczeniu 12, gdy krok w jednym kroku
  rozszerza (norma max 1.9): 1.725 m/s. Przy ograniczeniu 3 (norma
  0.95) już jej nie ma: 1.533 m/s.
- Ławka offline nie rozróżnia żadnego ramienia; model pętli
  rozróżnia.
- Strata bliźniaka jest taka sama przy stojącym celu i przy celu
  w ruchu, a największa w pierwszych 10 s (−0.67 m/s).

Nie wolno:

- „Sieć programu ma dowód". Dowód dotyczy bliźniaka, który nie lata.
- „Prawo dowiedzione od 10 m".
- „Bliźniak lata gorzej" jako fakt z lotu. To wskaźnik modelu
  skalibrowanego na trzech sterownikach.
- Podawać ρ* z rachunku złożenia (7.14 i 5.90 m bez GNSS, 12.39
  i 11.14 m ze ścianą GNSS) jako dowiedzione: przełożenie komendy na
  dystans jest w nim założone, a wzór jest propozycją wykonawcy.
- „Pamięć sieci służy prędkości celu".
- Rozciągać wymiany pamięć za dowód poza tę architekturę, te wejścia
  i to ograniczenie.

## §4. Co wyszło poza planem

**Błędy CC.**

- Próg Ś3 (10.0 m) postawiony z minimum próbek (0.70 m/s przy
  wymaganych 0.3), bez sondy luzu samej metody ograniczającej. Metoda
  gubi co najmniej 0.32 m/s w każdej komórce. Szansa 0.70, chybiona.
- Przepis rzutu bez zapasu: wagi po rzucie mogą mieć B(W) ponad γ
  o ostatni bit. Stąd Ś1 co do litery.
- Sonda przesłanek liczona na wszystkich tickach z krokiem sieci,
  nie na tickach misji. Stąd w prompcie 0.81 m dla Δ_B w dystansie
  (jest 0.44–0.46 m) i 0.46% ticków z wiekiem ponad 0.15 s (jest
  0.02%).
- H-PAMIĘĆ w postaci „prędkość celu" obalona.

**Wykonawca.** Błędów w liczbach CC nie znalazł. Odchylenia istotne
dla zdań z §3: dziedzina dowodu od 8 m, nie od 4 m; B50 bez dowodu;
kontrola na Z i K na próbie 20 000 komórek; E2 policzony inaczej,
niż opisano; rachunek złożenia własnym wzorem.

**Co recon dał ponad pytanie.** Ramię C12: bez niego krzywa ceny
kończyłaby się na „docisk szkodzi", a mówi „orbita wymaga kroku,
który rozszerza". Podział straty na stojący cel, cel w ruchu i start.

## §5. Co to znaczy dla programu

Na krzywej ceny szybka orbita i krok rozszerzający w jednym kroku
występują razem: żadne z siedmiu ramion nie ma jednego bez drugiego.
A krok rozszerzający to właśnie to, czego nie da się dowieść. Po
trzech nogach (PĘTLA, ARKUSZ, BLIŹNIAK) zdanie
„dowód obejmuje sieć, która leci" jest dla NCP-20 z tymi wejściami
zamknięte, z podaną przyczyną i z kontrprzykładem konstrukcyjnym:
sieć dowodliwa istnieje i nie ma czym lecieć.

Otwarte i nietknięte: czy podanie uczniowi tego, co ma nauczyciel
(kierunek obiegu, prędkość celu), pozwoliłoby sieci bez pamięci
trzymać orbitę. Wynik (d) wskazuje raczej na start orbity niż na
prędkość celu.

## §6. Proces

- Recon: 116 minut, zero bootów. Trening z sond CC odtworzony przez
  wykonawcę z różnicą wag rzędu 10⁻⁹.
- Reguła kandydata zapisana przed wynikiem zadziałała: lotów nie ma
  i nikt ich nie musiał odwoływać.
- Lekcja: szansę progu dowodu stawia się z sondy luzu metody, nie
  z minimum próbek.
- Lekcja: przepis, który ma dać wagi spełniające ograniczenie,
  rzutuje z jawnym zapasem.
- Lekcja: sonda przesłanek używa tego samego wyboru ticków co wynik.

## §7. Rozliczenie predykcji

- P-BLIZ-1 (0.90) ✓ — 0.04136, 0.04734, 0.04791, 0.04814.
- P-BLIZ-2 (0.90) ✓ — 12/12 i 120/120.
- P-BLIZ-3 (0.85) ✓ — kolejność zachowana, MLP 0.294 m/s.
- P-BLIZ-4 (0.85) ✗ — średnie poniżej GRU, ale B90 w najgorszej
  rodzinie ma 1.028 m/s, ponad zapisane 1.0.
- P-BLIZ-5 (0.85) ✓ — C3 1.533 m/s.
- P-BLIZ-6 (0.40) ✓ — C12 1.725 wobec K 1.740 m/s.
- P-BLIZ-7 (0.70) ✗ — Ś3 zachodzi.
- P-BLIZ-8 (0.45) ✗ — S(1.0) od 11.75 m.
- P-BLIZ-9 (0.90) ✓ — półszerokość 1.0.
- P-BLIZ-10 (0.85) ✓ — zero kontrprzykładów.
- P-BLIZ-11 (0.50) ✗ — −0.294 wobec −0.260 m/s.
- P-BLIZ-12 (0.10) ✗ — kandydata brak.

7 z 12 przy sumie szans 8.25.

## §8. KSIĘGA (append-only przy commicie §CO)

```
## BLIŹNIAK — recon i zamknięcie pozycji (ANEKS_BLIZNIAK-1, 21.11.2026)
- CLOSED-BY-RECON, 0 bootów. Ś3 zachodzi; Ś2, Ś4, Ś5 nie; Ś1 co do
  litery dla B90 (ostatni bit), bez wpływu na wynik.
- Na B30 (B(W) = 0.3 z wag) dowiedzione formami afinicznymi
  z podziałem: S(0.3) we wszystkich komórkach od 10.5 m, S(1.0) od
  11.75 m (Δ_A); od 10.0 m 99.934%, 471 wyjątków. Lemat U:
  półszerokość do 0.311 od piątego ticka. Test wykonawcy 10⁶
  i niezależny test CC 6.18 mln historii: zero naruszeń, zapas co
  najmniej 0.32 m/s.
- Ten sam kod na Z i K: pudełko stanu ma pełny zakres.
- Cena: VAL +16% wobec K; orbita w modelu pętli 1.48 wobec 1.745 m/s,
  poniżej GRU (1.674); kandydata do lotów brak. Orbita wraca przy
  B(W) = 12 (1.725 m/s), przy 3 już jej nie ma (1.533).
- Model pętli ustawia Z > GRU > MLP jak loty; ławka offline nie
  rozróżnia żadnego ramienia (każde 120/120).
- Przesłanki na lotach TEACH: 99.12% ticków misji (loty testowe),
  99.23% (wszystkie).
- H-PAMIĘĆ w postaci „prędkość celu" obalona; strata największa
  w pierwszych 10 s.
- Predykcje 7/12 przy sumie szans 8.25 (✗ 4, 7, 8, 11, 12).
- ✗ CC: próg Ś3 z minimum próbek zamiast z sondy luzu metody;
  przepis rzutu bez zapasu; sonda przesłanek na złym wyborze
  ticków; H-PAMIĘĆ.
- Lekcje:
  - szansę progu dowodu stawia się z sondy luzu metody;
  - rzut na ograniczenie z jawnym zapasem;
  - sonda przesłanek na tym samym wyborze ticków co wynik.
```

## §9. KIERUNKI_PO_PLANIE (append-only przy commicie §CO)

```
## Dopisek stanu katalogu — 21.11.2026 (CO-BLIZNIAK-1, ANEKS_BLIZNIAK-1)
- **BLIŹNIAK — CLOSED-BY-RECON.** Bliźniak dowodliwy istnieje
  (prawo pościgu od 10.5 m), kandydata do lotów brak. Sieć
  zamrożona, osłona i kod lotu bez zmian.
- **Dowód obejmujący sieć, która leci — zamknięty** dla NCP-20
  z obecnymi wejściami, po trzech nogach (PĘTLA, ARKUSZ, BLIŹNIAK).
  Zmierzone: szybka orbita występuje tylko razem z krokiem
  rozszerzającym w jednym kroku; krok kurczący daje dowód i wolną
  orbitę.
- **Kandydat WEJŚCIA — nieotwarty, bez rekomendacji otwarcia teraz:**
  uczeń bez pamięci z kierunkiem obiegu i prędkością celu na
  wejściu. Osobną decyzją Olgi.
- **KOPIA** — wycofana jako osobna pozycja.
- **PION** — bez zmian (rekomendacja przyjęta 19.11, pozycja
  nieotwarta). Nie blokuje pakowania.
- **ŚCIANA** — bez zmian.
- **Pakowanie** (artykuł, nota, film) — następne.
```

## §CO

Bramka: origin/master == **33249b72**. Jeden commit [CO-BLIZNIAK-1]:
korzeń `ANEKS_BLIZNIAK-1.md` verbatim (byte-check sha256 z wiadomości
CC) + KSIĘGA §8 i `KIERUNKI_PO_PLANIE.md` §9 append-only. Zero
bootów, zero zmian kodu i raportów. Push = Olga.
