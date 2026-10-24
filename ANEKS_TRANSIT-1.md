# ANEKS_TRANSIT-1 — ZMIERZONY SUFIT PROFILU MISJI: zamknięcie pozycji AKW-TRANSIT + pozycja-następca PERCEPCJA-II (CO-TRANSIT)

CC · 25.10.2026 · łańcuch TRANSIT (po STOP-TRANSITR, commit 0954f55 na origin).
Aneks zamykający POZYCJĘ na etapie recon, samowykonalny (§4): zero bootów wydanych,
zero do wydania; sesja CO deskowa. Sygnały bez numeru odrzucasz.

## §1. Przyjęcie STOP-TRANSITR

Przyjęte po weryfikacji CC z repo wykonaniem: zakres = wyłącznie
results/TRANSIT_RECON/** (7 plików); **geometria generatora potwierdzona literą**
(bench/scenarios.py:53 — przy r>14 heading = atan2(−y,−x), prosto na home:
bliski najazd jest deterministyczną cechą KAŻDEGO epizodu v=1.0, nie pechem
ziaren); **arytmetyka sufitu odtworzona niezależnie** (łuk po dwell 273.1°, n=4
stare bez klina ⇒ koniec okna najgorszego azymutu 11.15 s; pas admisji dh≥5 przy
celu radialnym v=1.0 zamyka się o 10.0 s; 11.15 > 10.0); **anatomia zweryfikowana
na SUROWYCH klatkach percep_feed** (c08_s03, okno 2.20–3.25 s: box 6/6 klatek,
on-target, conf 0.37–0.64, mti_ok F-T-T-F-F-T ⇒ max run central∧mti = 2 < k=3,
fresh 0/6 — detektor widział, admisja padła, dokładnie klasa (ii)); r1/r2/r3
spójne wewnętrznie i z danymi zweryfikowanymi wcześniej (t_acq vs telemetria
FANTOM, bliskie przejścia vs POSCIG mod B, t_entry pasywne 4.91–5.20); reguła
erratum zastosowana wzorcowo (manifest + świadek obok; werdykty T6 realne).
Kalibracja uczciwości przyrządu (CH0 przewiduje 3/6 geometrycznie, realnie 0/6 —
liczby konwersji jawnie nazwane górną granicą) — wpis do rejestru dobrych praktyk.

## §2. WERDYKT: pozycja AKW-TRANSIT ZAMKNIĘTA — ZMIERZONY SUFIT PROFILU MISJI

Sześć pozostałych porażek kamery ma jeden, w pełni zmierzony sufit o trzech
składowych, z których każda jest przybita do rzeczy zamrożonej:

1. **Admisja, nie pokrycie:** klasa (ii) 6/6 — cel był w stożku, detektor go
   widział, padała koincydencja central∧MTI (k=3 kolejnych klatek; @5 Hz run
   doszedł do 0–2). Kontrprzykład w identycznej geometrii: c08_s02 @5 Hz run=3
   (ENTRY 2.33 s), c08_s01 @14.3 Hz runy w setkach — **admisja czołowa przy 5 Hz
   to zmierzona loteria (4/7), przy 14 Hz pewnik.** Percepcja FROZEN.
2. **Strefa martwa i pas admisji:** żadna realna admisja kampanii nie zaszła
   bliżej niż dh 5.01 m (3267 klatek fresh); pas [5,18] m odzwierciedla korpus
   detektora (etykiety 5.75–14.9 m). Cel radialny opuszcza pas o t=10.0 s.
3. **Arytmetyka przeglądu vs próg konwersji:** t\* = 10.75–11.41 s (wiążące
   d_min ≥4 — pościgowiec musi opuścić home PRZED ślepym przejściem), a
   gwarantowane pokrycie najgorszego azymutu w nietykalnych kończy się ≥11.15 s.
   **Nie istnieje choreografia skanu bez prioru, która gwarantuje okno
   admitowalne przed zamknięciem pasa admisji.** Warianty "domykające 6/6"
   (CH90/CH87) robią to wyrównaniem do korytarzy SIATKI — stres bazą +45° daje
   0/6 i regresję 5/6 kontroli; kampania na nich mierzyłaby zgodność choreografii
   z generatorem, nie zdolność misji. Mikro-orbita nie gwarantuje separacji
   (0–50% faz) i łamie założenie statycznego tła MTI; wysokość poza ligą
   (kontrakt misji/percepcji).

**Zdanie kanoniczne (do cytowań):** „Z 7 pozostałych par kamery: 6 to zmierzony
sufit PROFILU MISJI — zawis na home + separacja ≥4 m + cel przecinający dysk,
przy zamrożonej percepcji i reżimie skanu — o trzech składowych (deterministyczny
najazd generatora; loteria admisji czołowej @5 Hz / strefa martwa dh<5; przegląd
perymetru 11.15 s > pas admisji 10.0 s); 1 to wariancja pościgu na komórce
granicznej. Podniesienie sufitu wymaga dotknięcia rzeczy zamrożonych — to
pozycja PERCEPCJA-II, nie choreografia."

**Sonda (R5 iii) ODRZUCONA:** mierzy wyłącznie stopę loterii MTI czołowego,
a rachunku sufitu (min-360 vs t\*) żadna stopa nie uchyla — booty kupują tylko
informację werdyktową. Stopa loterii wchodzi do aktywów pozycji-następcy.
Pozycja zamyka się kosztem **0 bootów** (czwarte rozstrzygnięcie kierunku deskiem).
KSIĘGA bez rozliczenia — PRE nie powstało.

## §3. Pozycja katalogowa NOWA: PERCEPCJA-II (admisja niezawodna / daleki wzrok) — NIE otwierana tym aneksem

Następca, który jako jedyny REALNIE podnosi sufit, bo adresuje jego zamrożone
składowe — nowa era percepcji z własnym FREEZE (wzór nogi DET):

- **Mechanizm ZMIERZONY** (ten recon, poziom klatki): koincydencja central∧MTI
  @5 Hz ma margines ~2 klatek na cały łańcuch (k=3 + persystencja 3/4 + warmup);
  @14.3 Hz działa w setkach; pas admisji [5,18] m = odbicie korpusu etykiet
  (97% w 5–10 m, max 14.9).
- **Dźwignie nazwane, NIEZMIERZONE** (recon zaczyna od ich pomiaru): (a) podłoga
  kadencji percepcji — skąd mody 5.10/7.58/14.71 Hz i co kosztuje gwarancja ≥10 Hz
  (tor percep_proc / compute, nie progi admisji); (b) persystencja MTI nad celem
  czołowym (residuum derotacji pod diff_thr/min_area — progi dziś FROZEN);
  (c) zasięg i rozdzielczość: krzywa P(detekcja|Z) na istniejących klatkach
  (desk, zero lotów), potem ewentualnie rozdzielczość sensora / korpus
  dystansowy / imgsz — detektor-v3 pod nową nazwą, taśma etykiet projektowych
  działa na każdej odległości za darmo.
- **Zbieżności (jawnie):** TRANSIT (podniesienie sufitu 6 par), wątek
  dalekiego wzroku i rozpoznawania WABIKÓW (oba potrzebują pikseli na dystansie
  — ta sama dźwignia rozdzielczości/korpusu), przyszłe sim-to-real (szum
  realnej kamery wchodzi w ten sam tor).
- **Trigger:** przed roszczeniem pełnej siatki v=1.0 ponad dzisiejszy sufit albo
  przed jakimkolwiek wątkiem wymagającym detekcji >15 m (wabiki, dystans).
  Aktywa: r1_anatomia (klatka po klatce), progi empiryczne (podłoga dh 5.01,
  dryf p99 5°/kl), stopa loterii 4/7, korpus Z-stats, T6 jako zbiór odniesienia.
  Flaga: [MECHANIZM ZMIERZONY / DŹWIGNIE NIEZMIERZONE].

## §4. Zlecenie CO-TRANSIT — commit zamykający (samowykonalny; jeden commit, zero bootów)

Bramka: `git log origin/master..HEAD` puste ⇒ dalej; inny stan ⇒ STOP. Pliki
(lista zamknięta): korzeń `ANEKS_TRANSIT-1.md` (ARCH-1, verbatim, pierwszy
w commicie); EDYCJA `KIERUNKI_PO_PLANIE.md`: pozycja AKW-TRANSIT →
**CLOSED-BY-RECON (zmierzony sufit profilu misji)** z odsyłaczem do
`results/TRANSIT_RECON/RECON_TRANSIT.md` i zdaniem kanonicznym §2; dopisana
pozycja **PERCEPCJA-II** wg §3 (mechanizm/dźwignie/zbieżności/trigger/aktywa/
flaga); nota przy zdaniu o rezyduum kamery (33/40): odsyłacz do zdania
kanonicznego. ŻADNYCH edycji KSIĘGI, raportów ani kodu. Raport płaski:
diff-stat, pełna treść zmian KIERUNKÓW, porcelain. STOP. Push = Olga
(„wypchnięte").

## §5. Status i dalej

Pozycja AKW-TRANSIT: CLOSED (0 bootów, 1 sesja deskowa + CO). Rezyduum kamery
jest od dziś w całości rozliczone: **6 = sufit profilu misji (zmierzony co do
klatki i co do arytmetyki), 1 = wariancja pościgu, 2 near-missy omiatania poniżej
progu pozycji** — program nie ma już ani jednej porażki bez mechanizmu. Katalog:
PERCEPCJA-II (następca z aktywami), GT-CZYSTOŚĆ (narzędziowa), 1b(ii) weryfikacja
sieci, 2d VIO, 2c adwersarz/wabiki (zbieżny z PERCEPCJA-II); warstwa 0 bez zmian.
Breach 0 / REFUSE 0 pozostaje prawdą o wszystkim, co kiedykolwiek poleciało
uzbrojone.
