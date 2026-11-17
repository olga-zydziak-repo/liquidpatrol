# ANEKS_TEACH-5 — zamknięcie nogi: bramka S3 werdykt V-A — 12 z 12 cięć dostępnych na trzech terenach, litera bez naruszeń w 14 lotach; jedno cięcie na styku na krawędzi mapy

LiquidPatrol · CC · 17.11.2026 · łańcuch TEACH, po STOP-TEACH-3
(5ad2555e na origin). Do ratyfikacji sygnałem **„ratyfikuję
TEACH-5"**. Sygnały bez numeru albo nazwy odrzucasz.

## §1. Weryfikacja CC z repo (wykonaniem, własnym kodem)

Tabela wpisana z liczb PRE §4, nie z pliku FREEZE; e′ liczone
z wierszy ramy jako |p_corr − GT|; koniec misji to komenda zejścia
planowego albo pierwsza odmowa; chwila flagi z ULG.

1. **Stan.** f31cf1ce, c934c820, 5ad2555e na origin; ANEKS_TEACH-4
   w korzeniu z sumą b4604d2e…. Od 64f38b03 kod lotu, osłona,
   provery, tor, tabela, światy i manifest bez zmian; zmieniły się
   tylko narzędzia wokół lotu.
2. **Przesłanka.** 12 cięć, 30 475 ticków utraty, ocenione 29 865:
   **zero przekroczeń e′ ≤ U′**, największe zużycie granicy 0.31
   (osiedle, c05, powtórzenie a). Nieocenione 610, wszystkie po
   zatrzasku τ\* w zejściu planowym; w misji 0 w każdym locie.
   26 ticków przed pierwszą poprawką: e′/U′ do 0.10.
3. **Replay osłony z tabeli PRE.** Przedział, R, u′, τ = czas ticku
   − t_fix i decyzja: 0 różnic w 30 475 tickach. `r_est` = |p_corr|
   w każdym ticku utraty.
4. **(B2), (B4).** Największy r_GT 19.16 m przy R_E 32 m. `nav_state`
   14 we wszystkich próbkach epizodów, failsafe 0, breach brak.
   REFUSE wyłącznie po komendzie zejścia: pierwszy 6.8–11.1 s po niej.
5. **Nominały.** N1 1563 ticki, N2 1524 ticki: wszystkie NOMINAL
   i ALLOW, akwizycja w obu. Błąd poprawki cienia do 0.258 m (parking,
   c10) i 0.449 m (łąka, c05), przyjęte 191 z 191 i 182 z 182.
6. **Dostępność (D1) własnym kodem: 12 z 12.** Kontynuacja
   110.50–110.53 s, track 1.000 w każdym locie, pasmo 0.918–1.000.
7. **Ważność.**
   - Flaga w ULG spada raz na lot; osłona w utracie 0.084–0.096 s
     później.
   - Zamknięcie mapy jedno na lot, 0.000–0.172 s po fladze; ostatni
     kadr mapy 0.228–0.400 s przed flagą. Po fladze żadnego kadru
     mapy, klatki kluczowej ani wiązania w 12 z 12; w nominałach
     żadnego po chwili cienia.
   - Znaczniki: 6 detekcji surowych na 19 856 klatek 14 lotów (ID 17
     i 37, bok do 7.8 px), zgodnych z manifestem 0.
   - Chwila flagi pusta we wszystkich wierszach producenta.
8. **Poprawki.** W oknach od zamknięcia do końca misji 6629 kadrów,
   przyjęte 6615. Największy błąd wobec GT: parking 0.730 m, osiedle
   0.757 m, łąka 0.754 m; mediana w locie 0.18–0.43 m. Georeferencja
   rozwiązana osobnym kodem z zapisanych wiązań (474–588 na lot)
   równa zapisanej w 14 z 14; 6615 poprawek policzonych z klatki
   kluczowej, wektora i tej georeferencji równe datagramowi do
   0.0001 m.
9. **Pętla.** Błąd własny EKF w misji do 3.3–7.6 m, e′ do
   0.58–1.47 m.

Liczby raportu wykonawcy potwierdzone. Dwie różnice bez wpływu na
osąd: trzecia cyfra max e′/U′ (chwila odczytu GT) i reszta kursu
klatek kluczowych po georeferencji (CC do 2.3°, raport do 4.4°;
obserwabla bez progu, różnica w odczycie GT przy obrocie
nierozstrzygnięta).

Nie powtarzane: bramka zdrowia i tempo stanowiska, czasy producenta,
próba na sucho budowy S3. Liczba klatek zgubionych i czas zamknięcia
mapy odczytane z zapisów lotów.

## §2. Werdykt

1. Litera bezpieczeństwa B1–B5: **0 naruszeń** w 12 cięciach
   i 2 nominałach.
2. Dostępność: **12 z 12** przy progu 9; parking 4 z 4, osiedle
   4 z 4, łąka 4 z 4.
3. **Werdykt V-A. TEACH — CLOSED, PASS.** Loty 14 z 14 ważne, rezerwa
   nietknięta. Budżet nogi 19 z 24.

## §3. Zdanie, które stoi

Sieć NCP-20 z osłoną i dowodem z NADIR-II, bez zmiany kodu sieci,
osłony i reguły, prowadzi zadanie przez 110 s po utracie GNSS bez
znaczników naziemnych, gdy poprawkę pozycji daje mapa zbudowana
z własnej kamery w dół przed utratą: 12 z 12 lotów na trzech terenach,
bez odmowy w misji. Przesłanka |p_corr − GT| ≤ U′ trzymała w każdym
z 29 865 ticków przy największym zużyciu granicy 31%. Błąd poprawki
nie przekroczył 0.76 m przy błędzie własnym EKF do 7.6 m. Źródło
spełnia kontrakt z NADIR-III (co najmniej 1 Hz, błąd do 1.0 m)
wszędzie tam, gdzie kadr leży w mapie.

**Granice zdania:** SITL. Teren to płaski obraz ortofotomapy; mapę
i lot dzieli kilkadziesiąt sekund, więc światło się nie zmienia. Dron
lokalizuje się tylko tam, gdzie patrzył przed utratą GNSS. Kamera
przepływu pracuje nad szachownicą jak w NAD3. Horyzont 110 s, dwa
powtórzenia na komórkę. Zdanie nie mówi nic o rzeźbie terenu, o mapie
starszej niż lot, o locie poza mapę ani o przepływie optycznym nad
prawdziwym terenem.

## §4. Gdzie było ciasno i co wyszło poza planem

- **Zapas dopasowania kończy się na krawędzi mapy w kilka sekund.**
  W mapie jest duży: mediana punktów zgodnych w locie 164–684 przy
  progu 12, a tylko 3 z 6615 przyjętych poprawek miały ich mniej niż
  20. Przy wylocie na 15–19 m od środka najbliższej klatki kluczowej
  liczba spada z setek poniżej progu w około 4 s lotu. Błąd poprawki
  pozostaje przy tym zwykły aż do ostatniej przyjętej klatki.
- **Dwa cięcia c10 wyszły na krawędź.** Parking, powtórzenie b:
  przerwa 1.2 s (5 klatek), 60 s po fladze. Osiedle, powtórzenie a:
  przerwa 2.0 s (9 klatek), 32 s po fladze.
- **W locie nad osiedlem o odmowie zdecydował jeden punkt i jeden
  tick.** Klatka kończąca przerwę została przyjęta przy dokładnie 12
  punktach zgodnych, przy τ = 2.02 s. Zatrzask leży na 2.05 s, więc
  następny tick osłony byłby odmową. W tej samej przerwie zapas
  bariery spadł do 1.9 m (w pozostałych lotach co najmniej 4.9 m).
  Dostępność 12 z 12 stoi literą; w treści jedno cięcie jest na
  styku.
- **Reguła przyjęcia zadziałała w obie strony.** Pierwsza odrzucona
  klatka każdej przerwy leżała przy przewidywaniu (9 i 11 punktów,
  innowacja 0.1–0.2 m), więc próg 12 odrzucił tam dobrą poprawkę.
  Kolejne miały 3–9 punktów i innowację 14–24 m. Fałszywa poprawka
  nie weszła żadna. Progu danymi S3 się nie rusza.
- **Promień decyduje.** c05 lata do 16.4 m i w sześciu lotach nie
  straciła ani jednej klatki. c10 sięga 17.9–19.2 m i tam leżą obie
  przerwy.
- **Teren nie różnicuje błędu.** Największy błąd na trzech łatach
  różni się o 0.03 m; ustawia go lot, tak jak w reconie. Osiedle,
  pierwszy raz w gz i od razu w pętli: 4 z 4, z największą liczbą
  punktów zgodnych.
- **W c05 największy błąd przypada na drugą połowę okna w 6 z 6
  lotów**, w c10 w 1 z 6. To wzór przechyłu EKF z ANEKS_TEACH-4 §1.
- **Powtórzenia nie są kopiami.** Wejście 0.04–5.8 s po starcie
  epizodu, cięcie 30.0–35.8 s. Największy błąd w parze różni się
  najwyżej o 0.18 m.

## §5. Proces

- Kolejka przeszła 14 pozycji bez STOP-u. Sprawdzian lotu, którego
  brakowało w S2, powstał w budowie S3 i dał 100% w 14 lotach.
- Odchylenia 1–6 raportu przyjęte. Sprawdzian georeferencji liczy
  wykonawca solverem toru, nie osobnym kodem (odchylenie 2); osobnym
  kodem policzył ją CC: 14 z 14 zgodnych.
- Bramka zdrowia sześć razy zatrzymała start przed bootem; żaden
  boot nie przepadł.
- Wiersze producenta nie zapisują pokrycia kadru mapą; przy
  przerwach liczył je sędzia. CC ocenił położenie z odległości do
  klatek kluczowych.

## §6. Rozliczenie predykcji

- P-TEACH-5 (0.85) ✓ — zero przekroczeń w smoke i 12 cięciach, max
  0.31 przy progu 0.60.
- P-TEACH-6 (0.70) ✓ — 12 z 12.
- P-TEACH-7 (0.65) ✓ — 0.730 / 0.757 / 0.754 m.
- P-TEACH-8 (0.60) ✓ — łąka gorsza od parkingu o 0.024 m.
- P-TEACH-9 (0.75) ✓ — o jeden tick (§4).
- P-TEACH-10 (0.50) ✓ — V-A.
- P-TEACH-12 (0.75) ✓ — 0.757 m przy progu 0.80.
- P-TEACH-13 (0.75) ✓ — osiedle 4 z 4, jedno na styku.
- P-TEACH-14 (0.80) ✓ — klatek zgubionych 0 w 14 lotach, zamknięcie
  mapy do 48 ms.

Bramka: 9 z 9 przy sumie szans 6.35. Noga od PRE: 13 z 14 przy 9.85.
Z reconem: 21 z 28 przy 18.30. Dziewięć trafień bramki wisi na jednym
mechanizmie (źródło działa w mapie), więc nie jest to dziewięć
niezależnych prób. Szanse zapisane przed lotami były za niskie:
recon dawał te same liczby co loty.

## §7. KSIĘGA (append-only przy commicie §CO)

```
## TEACH — bramka i zamknięcie nogi (ANEKS_TEACH-5, 17.11.2026)
- Werdykt V-A. 12 cięć (parking, osiedle, łąka × c05, c10 × 2)
  i 2 nominały w cieniu: B1–B5 bez naruszeń; dostępne 12/12 (próg 9).
  14/14 lotów ważnych, rezerwa 0/3, noga 19/24.
- Przesłanka: 29 865 ticków, zero przekroczeń, max e′/U′ 0.31. CC
  odtworzył własnym kodem z tabelą wpisaną z PRE §4; replay osłony
  0 różnic na 30 475 tickach; georeferencja z zapisanych wiązań
  zgodna w 14/14; 6615 poprawek zgodnych z datagramem do 0.0001 m.
- Błąd poprawki max 0.730 / 0.757 / 0.754 m (S / M / J) przy błędzie
  własnym EKF do 7.6 m. Przyjęte 6615 z 6629 kadrów okien misji.
- REFUSE w misji 0. Dwie przerwy źródła, obie c10 na krawędzi mapy:
  1.2 s i 2.0 s. W drugiej klatka kończąca przerwę przyjęta przy 12
  punktach zgodnych (próg 12) i τ 2.02 s (zatrzask 2.05 s).
- Predykcje bramki 9/9 przy sumie szans 6.35; noga od PRE 13/14 przy
  9.85; z reconem 21/28 przy 18.30.
- Lekcje:
  - na krawędzi mapy liczba punktów zgodnych spada z setek poniżej
    12 w około 4 s lotu, 15–19 m od środka klatki kluczowej; błąd
    poprawki do końca zwykły;
  - dostępność na mapie z własnego lotu zależy od tego, czy zadanie
    mieści się w obszarze widzianym przed utratą, nie od terenu;
  - wynik 12/12 trzeba czytać razem z zapasem: jedno cięcie dzielił
    od odmowy jeden tick;
  - po udanym locie w pętli szanse z reconu należy podnieść, zamiast
    przepisywać je sprzed lotu;
  - warunek ważności bez narzędzia nie jest sprawdzany (replay w S2).
```

## §8. KIERUNKI_PO_PLANIE (append-only przy commicie §CO)

```
## Dopisek stanu katalogu — 17.11.2026 (CO-TEACH-5, ANEKS_TEACH-5)
- **TEACH — CLOSED, PASS (V-A).** Lot bez GNSS i bez znaczników
  z poprawką z mapy zbudowanej przez drona przed utratą: 12/12 cięć
  na parkingu, osiedlu i łące, 110 s, bez odmowy w misji; litera
  bezpieczeństwa bez naruszeń w 14 lotach; błąd poprawki do 0.76 m.
  Sieć, osłona i reguła bez zmiany kodu.
- **Pozycje nieotwarte, osobnymi decyzjami Olgi:**
  - lot długi z okrążeniem uczącym. Warunek z tej bramki: mapa ma
    pokryć cały obszar zadania z zapasem (c10 sięga 19.2 m, próg
    dopasowania leży 15–19 m od środka klatki kluczowej). Pierwszy
    krok przy biurku: mapa z okrążenia wobec klatek lotu
    10-minutowego;
  - teren dla wszystkich kamer z nowym pomiarem G.
- Obserwacje bez pozycji: liczba punktów zgodnych maleje przez około
  4 s przed krawędzią mapy — sygnał wyprzedzający, dziś nieużywany;
  pierwsza klatka za krawędzią leży przy przewidywaniu mimo 9–11
  punktów; wiersze producenta nie zapisują pokrycia kadru mapą.
```

## §CO

Bramka: origin/master == **5ad2555e**. Jeden commit [CO-TEACH-5]:
korzeń `ANEKS_TEACH-5.md` verbatim (byte-check sha256 z wiadomości CC)
+ KSIĘGA §7 i `KIERUNKI_PO_PLANIE.md` §8 append-only. Zero bootów,
zero zmian kodu i raportów. Push = Olga.
