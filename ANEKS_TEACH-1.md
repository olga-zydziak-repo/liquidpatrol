# ANEKS_TEACH-1 — zamknięcie reconu TEACH-S0: śmierć Ś2 dla mapy georeferowanej wprost z EKF; samo dopasowanie do mapy z własnego lotu działa na każdym terenie; decyzja o drugim podejściu

LiquidPatrol · CC · 16.11.2026 · łańcuch TEACH, po STOP-TEACHR
(41e0aadc na origin). Do ratyfikacji jednym z dwóch sygnałów:
**„ratyfikuję TEACH-1, druga mapa"** albo **„ratyfikuję TEACH-1,
zamykam"**. Sygnały bez numeru albo nazwy odrzucasz.

## §1. Weryfikacja CC (z repo, własnym kodem)

1. **Łańcuch commitów.** d3e6df8b: ANEKS_ORTO-1 w korzeniu, sha256
   ee5fa95b… zgodny. 8fe0b9a2: predykcje w KSIĘDZE przed wynikiem.
   cf7a0fc1: łaty przed dopasowaniem. 41e0aadc: STOP.
2. **Tabela wyników.** Policzona od nowa z `r4_czesci/` (39 plików,
   8609 kadrów na łatę): wszystkie 18 wierszy raportu identyczne.
3. **Mechanizm, niezależnie od obrazów.** Model z samych zapisanych
   póz (GT i EKF, bez renderu i bez cech) przewiduje błąd poprawki M1
   dla każdego kadru: klatka kluczowa wyprostowana przy postawie EKF,
   jej środek w pozycji EKF. Na 6777 z 8550 przyjętych kadrów, dla
   których klatkę kluczową da się jednoznacznie rozpoznać po zapisanej
   odległości, różnica między błędem wykonawcy a modelem wynosi p50
   0.008 m, p95 0.041 m, max 0.115 m. Cały błąd M1 to georeferencja
   klatki kluczowej; dopasowanie obrazu dokłada centymetry.
4. **Kurs klatek kluczowych.** 122 klatki w 13 lotach, policzone
   osobno: błąd kursu p50 2.8°, p95 6.4°, max 14.0°; zgodne z raportem
   do 0.02°. W obrębie lotu błąd zmienia znak: w p02 z +6.6° na −4.1°
   w 2.2 s.
5. **Przerwy.** Wszystkie przerwy SIFT ponad 1.15 s leżą w locie
   długim; dla M0 i M1 policzone osobno: w miejscach, gdzie kadr
   pokrywa się z najlepszą klatką kluczową najwyżej w 32%. Na 12
   cięciach NAD3 największa przerwa SIFT to 0.4 s, na każdej łacie
   i każdej mapie.
6. **Pozycja EKF przed cięciem.** We wszystkich 13 lotach pozycja EKF
   wyprzedza GT o 0.10–0.12 s razy prędkość (do 0.3 m przy 2.9 m/s).
   Po odjęciu tego składnika zostaje reszta do 0.09–0.21 m i stałe
   przesunięcie do 0.06 m. Zmierzone wcześniej „0.2–0.4 m błędu
   pozycji" to więc głównie przesunięcie w czasie. Przyczyny nie
   ustalono (kandydat: kompensacja opóźnienia GNSS w EKF; do
   sprawdzenia w parametrach).

## §2. Werdykt

1. **Ś2 zachodzi literą, samym błędem i także bez lotu długiego.**
   Na 12 cięciach NAD3, SIFT, na każdej łacie: M1 daje 1.81–1.83 m
   (p02) i 1.56–1.57 m (p13); M2 daje 1.93–1.94 m (p02), 1.66–1.68 m
   (p14) i tuż ponad progiem 1.372–1.397 m (p04). Próg to 1.37 m.
2. **Ś1 zachodzi literą przez klauzulę przerw, nie przez błąd.** M0 na
   łacie S: 0.24 m (SIFT), 0.28 m (AKAZE), przy progu 0.5 m. Przerwa
   3.6 s powstaje w locie długim tam, gdzie dron wylatuje poza obszar
   widziany przed cięciem. Na 12 cięciach M0 / SIFT daje 0.21 m
   i przerwy do 0.4 s. Przyrząd jest sprawny; klauzula była błędem
   projektu CC (§5).
3. **Ś3 nie zachodzi** rachunkiem z przypiętych masek; lotem
   niesprawdzone.
4. **Recon TEACH-S0 — CLOSED.** 0 bootów, 12.7 min obliczeń.
   Zamknięta przy biurku jest mapa, w której każda klatka kluczowa
   dostaje pozycję i kurs wprost z EKF, z co najwyżej jedną stałą
   kursu na lot.

## §3. Co ten wynik mówi, a czego nie

**Mówi:**
- Dopasowanie kadru do mapy z własnego lotu działa na parkingu, na
  osiedlu i na łące jednakowo: przy idealnej georeferencji błąd max
  0.23–0.28 m, przyjętych 97.8–99.7% kadrów, 20 ms na kadr (SIFT)
  albo 12 ms (AKAZE). Wyniki trzech łat różnią się o setne metra.
- Mapa georeferowana wprost z EKF nie mieści się w progu. Błąd rośnie
  z odległością od środka klatki kluczowej (max 0.65 m do 3 m, 1.81 m
  ponad 10 m), czyli tak, jak działa dźwignia kursu.
- Jedna stała kursu na lot nie pomaga, a nawet szkodzi (poprawek
  ponad 1.0 m: 486 wobec 185), bo błąd kursu zmienia się między
  klatkami kluczowymi razem ze znakiem.

**Mówi też, ale to zapas, a nie argument:** w rachunku kontraktu na
siatce klatki (R6) mapa M1 „mieści się z odmowami": bariera zostaje
ponad 20 m do przerwy 2.0 s. Próg 1.37 m pochodzi z kontraktu
mierzonego przy 1 Hz, a to źródło daje 5 Hz. Progu się z tego powodu
nie rusza.

**Nie mówi nic o:**
- mapie, w której wzajemne położenie klatek kluczowych pochodzi
  z obrazu, a z EKF tylko zakotwiczenie całości — tego wariantu recon
  nie miał, bo M2 dopuszczał jedną stałą;
- terenie z rzeźbą i obiektami o wysokości (render z płaskiej
  ortofotomapy);
- pracy poza obszarem widzianym przed cięciem inaczej niż przez
  przerwy.

## §4. Rachunek CC z zapisanych póz (rachunek, nie pomiar)

Ten sam model geometryczny, który odtwarza błąd M1, pozwala policzyć
mapę spiętą obrazem. Każdy kadr sprzed cięcia jest dopasowany do
najwyżej trzech klatek kluczowych. Niewiadome to obrót i przesunięcie
każdej klatki kluczowej; wiążą je dwa rodzaje równań: kadr ma leżeć
tam, gdzie widzi go EKF (kotwica), a jego położenie liczone z dwóch
klatek kluczowych ma być to samo (spójność). Pomiary obrazu wzięte
z modelu z szumem 0.05–0.15 m na składową, pozycje z prawdziwych
zapisów EKF.

- Kotwice i spójność razem: na 12 cięciach błąd max 0.91–0.94 m przy
  szumie 0.05–0.08 m i 1.12 m przy 0.15 m; p95 0.54–0.67 m. W locie
  długim max 0.81–0.88 m i 1.11 m.
- Same kotwice, każda klatka kluczowa osobno: 1.15–1.39 m na 12
  cięciach i 1.45–1.47 m w locie długim. Za mało.
- Dolną granicę wyznacza wyprzedzenie EKF z §1 pkt 6 i błąd skali
  niskich klatek kluczowych (do 2% przy 6–8 m).
- Pułapka: wersja z wolną skalą rozjeżdża się przy mocnej spójności
  (mediana błędu 1.9 m), bo równania spójności nagradzają kurczenie
  mapy. Skala ma być stała.

Założenie rachunku: dopasowanie kadrów sprzed cięcia jest tak dokładne
jak po cięciu (zmierzona nadwyżka ponad geometrię: p95 0.04 m). Wśród
dopasowań z co najmniej 12 zgodnymi punktami trafiają się jednak
grube pomyłki: 19 na 51 654 w M0, wszystkie w locie długim na łacie M,
przy pokryciu do 28%, z błędem 22–26 m. Wiązania sprzed cięcia
potrzebują własnego sita.

## §5. Błędy projektu CC

- **Ś1 mieszało przyrząd z pokryciem.** Klauzula przerw obejmowała lot
  długi, choć CC sam zmierzył w nim odcinek 6.4 s z pokryciem poniżej
  połowy. Ten sam błąd siedzi w P-TEACH-R1 (0.85).
- **M2 zakładało stały błąd kursu w locie.** Rozrzut zmierzony
  wcześniej (p50 2.9°, max 15.2°) już temu przeczył; rozkładu
  w obrębie lotu CC nie sprawdził przed wyceną 0.65.
- **Wynik bez wektorów.** Prompt nie wymagał zapisu numeru klatki
  kluczowej ani wektorów przesunięcia i błędu, więc mechanizmu nie
  dało się rozłożyć z samych wyników.
- **Pokrycie liczone nie tą miarą.** „Pokrycie nie jest wąskim
  gardłem" opierało się na sumie wszystkich kadrów sprzed cięcia. Po
  przerzedzeniu do 8–11 klatek kluczowych z jedną z nich pokrywa się
  w połowie tylko 65% kadrów lotu długiego.

Wykonawca trzymał się litery. Odchylenia 1–12 raportu przyjęte;
jedyna naprawa przyrządu (prostowanie klatek M0 przy pozie GT) była
zgodna z promptem i potrzebna: przed nią M0 dawało 0.76 m na p02. STOP
bez drugiej drogi — tak, jak miało być.

## §6. Rozliczenie predykcji reconu

- P-TEACH-R1 (0.85) ✗ — błąd 0.24 m mieści się, ale są przerwy do
  3.6 s w locie długim.
- P-TEACH-R2 (0.35) ✗ — M1, łata S: 1.81 m.
- P-TEACH-R3 (0.65) ✗ — M2, łata S: 1.93 m.
- P-TEACH-R4 (0.55) ✗ — M2, łata M: 1.94 m.
- P-TEACH-R5 (0.30) ✗ — M2, łata J: 1.94 m, przerwa 2.6 s.
- P-TEACH-R6 (0.60) ✗ — M2, łata S, lot długi: przerwa 2.8 s.
- P-TEACH-R7 (0.60) ✓ — SIFT p95 24 ms, AKAZE 14 ms.

1 z 7 przy sumie szans 3.90. Wszystkie chybienia w stronę optymizmu,
cztery z nich na kalibracji kursu i na pokryciu lotu długiego.

## §7. Decyzja

**„druga mapa"** — drugi i ostatni recon przy biurku nogi TEACH
(PROMPT_TEACH_S0B). Zmienia się wyłącznie georeferencja klatek
kluczowych: mapa spięta obrazem i zakotwiczona w torze EKF sprzed
cięcia, jak w §4. Łaty, kadry, wybór klatek kluczowych, dopasowanie
i reguła przyjęcia zostają. Progi Ś2 zostają: 1.37 m i 2.15 s.
Przerwy liczone są osobno w mapie i poza nią. Śmierć zamyka nogę;
trzeciego podejścia do mapy z własnego lotu nie ma.

**„zamykam"** — noga TEACH zamknięta przy biurku. Wykonawca robi
wyłącznie commit [CO-TEACH-1].

Rekomendacja CC: druga mapa. Porażka ma jedną zmierzoną przyczynę,
którą da się odtworzyć bez obrazów; poprawka jest metodą znaną
(mozaika zakotwiczona w torze GNSS), a nie nowym pomysłem; koszt to
jedna sesja i kilkanaście minut obliczeń. Szansa, że druga mapa
zmieści się w 1.37 m na 12 cięciach: 0.75. Szansa na 1.0 m: 0.40.

Zastrzeżenie: to trzeci recon przy biurku w wątku lotu bez znaczników
(ORTO, TEACH-S0, TEACH-S0B) i wciąż żaden lot.

## §8. KSIĘGA (append-only przy commicie [CO-TEACH-1])

```
## TEACH — zamknięcie reconu S0 (ANEKS_TEACH-1, 16.11.2026)
- Recon TEACH-S0 CLOSED, śmierć Ś2 literą: mapa z klatek sprzed
  cięcia georeferowana wprost z EKF (M1) albo z jedną stałą kursu na
  lot (M2) daje max błąd przyjętej poprawki 1.81–1.86 m i 1.92–1.97 m
  przy progu 1.37 m, tak samo na trzech łatach, także na samych 12
  cięciach NAD3. Ś1 literą przez przerwy lotu długiego (do 3.6 s poza
  obszarem widzianym przed cięciem), nie przez błąd. 0 bootów.
- Kontrola M0 (georeferencja idealna): max 0.23–0.28 m, przyjętych
  97.8–99.7%, na 12 cięciach przerwy SIFT do 0.4 s; parking, osiedle
  i łąka bez różnicy. Czas kadru: SIFT p95 24 ms, AKAZE 14 ms.
- CC własnym kodem: tabela 18/18 wierszy; model z samych póz odtwarza
  błąd M1 kadr po kadrze (p95 różnicy 0.04 m, max 0.115 m na 6777
  kadrach) — błąd to georeferencja klatki kluczowej, nie dopasowanie;
  kurs klatek kluczowych p50 2.8°, p95 6.4°, max 14.0°, ze zmianą
  znaku w locie; pozycja EKF przed cięciem wyprzedza GT o 0.10–0.12 s
  razy prędkość.
- Predykcje 1/7 przy sumie szans 3.90 (✓ tylko R7); chybienia
  w stronę optymizmu.
- ✗ projektowe CC: Ś1 mieszało przyrząd z pokryciem; M2 zakładało
  stały błąd kursu w locie; wynik bez wektorów i numeru klatki
  kluczowej; pokrycie liczone sumą kadrów zamiast klatkami kluczowymi.
- Lekcje: kryterium przyrządu bada tylko przyrząd; zanim wyceni się
  poprawkę stałą, sprawdza się, czy błąd jest stały; wynik per kadr
  niesie wektory, nie same moduły.
- Rachunek CC z póz (nie pomiar): mapa spięta obrazem i zakotwiczona
  w torze EKF, obrót i przesunięcie na klatkę kluczową, skala stała —
  max 0.9–1.1 m na 12 cięciach; same kotwice bez spójności 1.15–1.39 m.
```

## §9. KIERUNKI_PO_PLANIE (append-only przy commicie [CO-TEACH-1])

Przy sygnale „druga mapa":

```
## Dopisek stanu katalogu — 16.11.2026 (CO-TEACH-1, ANEKS_TEACH-1)
- **TEACH, recon S0 — CLOSED przy biurku (Ś2).** Mapa z własnego lotu
  georeferowana wprost z EKF: poza progiem 1.37 m przez błąd kursu
  klatek kluczowych. Dopasowanie do takiej mapy przy georeferencji
  idealnej: 0.2–0.3 m na każdym terenie.
- **TEACH, recon S0B — otwarty** (PROMPT_TEACH_S0B): mapa spięta
  obrazem i zakotwiczona w torze EKF sprzed cięcia. Drugie i ostatnie
  podejście przy biurku; śmierć zamyka nogę.
```

Przy sygnale „zamykam":

```
## Dopisek stanu katalogu — 16.11.2026 (CO-TEACH-1, ANEKS_TEACH-1)
- **TEACH — CLOSED przy biurku (Ś2), decyzją Olgi bez drugiego
  podejścia.** Mapa z własnego lotu georeferowana wprost z EKF: poza
  progiem 1.37 m przez błąd kursu klatek kluczowych. Dopasowanie do
  takiej mapy przy georeferencji idealnej: 0.2–0.3 m na każdym
  terenie.
- Pozycja nieotwarta: mapa spięta obrazem i zakotwiczona w torze EKF
  (rachunek CC: 0.9–1.1 m). Otwarcie tylko decyzją Olgi.
- Wątek lotu bez znaczników: dwa wyniki przy biurku (ORTO, TEACH),
  bez lotu.
```
