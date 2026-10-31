# ANEKS_DET3-0 — PERCEPCJA-II (iii) „daleki wzrok / detektor-v3" zamknięta przy biurku: zasięg nie jest wąskim gardłem akwizycji; detektor widzi cel, misja go nie przyjmuje (CO-DET3-0)

CC · 31.10.2026 · łańcuch DET3 (po STOP-DET3R, commit 090521f8 na origin).
Aneks zamykający POZYCJĘ na etapie recon, samowykonalny (§5): zero bootów
wydanych, zero do wydania; sesja CO deskowa. Sygnały bez numeru odrzucasz.

## §1. Przyjęcie STOP-DET3R

Przyjęte po weryfikacji CC z repo wykonaniem. Zakres czysty: 60 nowych plików
pod `results/DET3_RECON/**`, zero delecji, zero edycji istniejących; 0 bootów,
0 treningu (sonda R4 nieodbyta decyzją Olgi „STOP bez sondy").

**R1 odtworzone klatka w klatkę, własnym joinem** etykiet (`results/DET/labels/*/
meta.jsonl`, flaga OK, box px, Z) z surowym replayem det_v2 (`r1/*.replay.jsonl`,
box znormalizowany, conf, mti_ok, fresh), definicja „YOLO na celu" = środek
top-1 w boxie etykiety (det_replay.py:149-152): 6 154 klatki, 12 bootów.
Per przedział Z: YOLO 0.999 / 0.998 / 1.000 / 0.930 / 0.889 (6–8 / 8–10 / 10–12 /
12–14 / 14–15 m); MTI(admisja) 0.970 / 0.990 / 0.845 / 0.535 / 0.667; fresh
1.000 / 0.997 / 0.831 / 0.442 / 0.444 — identycznie z tabelą reconu. Kontrola
czasu od wejścia celu w kadr identyczna: przy dt 0–1 s na 12–15 m 37/41 · 19/41 ·
13/41, przy dt 1–2 s **11/11 · 10/11 · 10/11**; ten sam spadek w pierwszej
sekundzie na 8–10 m (16/16 · 12/16 · 8/16 → 32/32 · 32/32 · 30/32). Cztery
chybienia YOLO przy Z ≥ 12 m wszystkie przy dt ≤ 0.33 s (D02 ×2, D06, D10);
chybień ogółem 11 / 6 154. Ogon jest cienki (52 klatki ≥ 12 m z 9 bootów, 9
klatek ≥ 14 m) i powyżej 14.9 m korpus nie ma ani jednej klatki — tak jest
podpisane w reconie i tak zostaje.

**R5c (detektor w rampie skanu) sprawdzone niezależnie na 3/6 epizodów T6**
z własnej geometrii etykiet (`det_labels.BootGeo`, rampa = |yaw_rate| > 15°/s,
okno przed pierwszą klatką fresh): c08_s03 — rampa 12/12, stare 5/5, pierwsze
trafienie 1.08 / 1.27 s, pierwsza fresh 19.42 s; c11_s02 — 5/5, 1/1, 29.32 /
30.64 s, fresh 31.10 s; c08_s04 — 10/11, 1/1, 2.48 / 4.33 s, fresh 26.11 s.
Co do liczby jak w `r5_rampa.json`. Zbiorczo (wg reconu, spójne z próbką):
257/263 klatek rampy i 89/92 stare z top-1 na celu przed akwizycją, w 48
epizodach FANTOM S2.

**R3 przyjęte literą** (brak zakodowanego progu odległości/rozmiaru/conf;
jedyny warunek to box zdegenerowany w_px ≤ 1, feed_vision.py:65). **R2**
przyjęte z JSON-ów (box 45×9 / 33.75×6.75 / 27×5.4 / 22.5×4.5 px na 15 / 20 /
25 / 30 m; inferencja daleko pod 60 ms; model idealny MTI pesymistyczny wobec
danych — residuum derotacji jest kanałem, którego rachunek nie widzi). Dwa
zastrzeżenia reconu zostają w kanonie: dane FANTOM S2 pochodzą z epoki
kadencji 5 Hz (przed PERC2), więc odstęp „widzi–przyjmuje" jest tam
zawyżony wobec dzisiejszego reżimu; ogon korpusu ≥ 12 m to 52 klatki.

## §2. WERDYKT: pozycja PERCEPCJA-II (iii) CLOSED-BY-RECON — zasięg nie jest wąskim gardłem

Pierwszy człon śmierci przy biurku z PROMPT_DET3_S0 §R6 jest spełniony
(oba składniki ≥ 0.9 na 12–15 m po rozgrzewce toru). Drugi człon — nowa rodzina
scenariuszy z range0 25/30 m — rozstrzygnięty przez Olgę 31.10 na NIE. Pozycja
zamyka się kosztem **0 bootów** (siódme rozstrzygnięcie kierunku deskiem).

**Zdanie kanoniczne (do cytowań):** „Na obecnym profilu misji (intruz od 15 m)
zasięg detektora nie ogranicza akwizycji: do granicy korpusu 14.9 m żaden
składnik toru nie traci celu pierwszy, a w 48 epizodach kampanii detektor miał
cel w 97.7 % klatek rampy skanu, zanim misja go przyjęła — w sześciu
najtrudniejszych epizodach 6–29 s wcześniej. Sufit akwizycji leży w rozgrzewce
admisji po wejściu celu w kadr i w geometrii przeglądu, nie we wzroku. Dalszy
wzrok (20–30 m) miałby sens wyłącznie dla większego perymetru i wymagałby
rozstrzygnięcia pomiarem, czy MTI w zawisie widzi cel na 20 m — pozycja
wyceniona, nieotwarta."

**Korekta kanonu katalogu (errata forward):** zdanie z ANEKS_TRANSIT-1 §3
i dopisku 25.10 „jedyny następca realnie podnoszący sufit" dotyczyło
PERCEPCJA-II jako całości; po tym reconie człon (iii) tego sufitu na obecnej
siatce NIE podnosi. Zostaje człon (ii) — rozgrzewka/admisja czołowa — i (poza
katalogiem) czas wpatrywania skanu, o którym niżej.

## §3. Co ten recon mówi o rozglądaniu się (nota, nie pozycja)

Arytmetyka TRANSIT (forma zamknięta: dwell 2 + 273.1°/60 + stare × n − 0.2 =
11.15 s przy kroku optymalnym 68.3°, n = 4) ma jeden człon, którego nikt nie
przeliczył po PERC2: **stare 1.2 s** było dobrane w epoce loterii 5 Hz. Przy
gwarantowanych 14.7 Hz admisja to run ≥ 3 (~0.2 s) plus rozgrzewka pary MTI
i persystencji — a R1 pokazuje, że ta rozgrzewka po wejściu celu w kadr trwa
do ~1 s (fresh 30–50 % w pierwszej sekundzie, ~100 % w drugiej). Rachunek:
przegląd najgorszego azymutu < 10.0 s wymaga stare < 0.91 s przy kroku 68.3°
(przy kroku 40°, n = 7: stare < 0.52 s). Margines jest więc wąski i zależy od
tego, jak szybko po starcie wpatrywania przychodzi admisja w dzisiejszym
reżimie — to da się zmierzyć z logów PERC2 S2 (14.7 Hz, T6 6/6 przy k=1) bez
lotu. Jeśli p95 latencji admisji po starcie wpatrywania + uspokojenie yaw
przekracza 0.9 s, rozglądanie się nie ma już taniej dźwigni. Kolejny recon
tylko decyzją Olgi; ocena CC: ~35 % szans, że rachunek przy biurku przejdzie.

## §4. Katalog i KSIĘGA (treść do skopiowania, append-only)

Dopisek do `KIERUNKI_PO_PLANIE.md`:

```
## Dopisek stanu katalogu — 31.10.2026 (CO-DET3-0, ANEKS_DET3-0 §2–§3)

- **PERCEPCJA-II (iii) daleki wzrok / detektor-v3** → **CLOSED-BY-RECON
  (0 bootów, 1 sesja deskowa + CO — siódme rozstrzygnięcie kierunku deskiem)**.
  Recon `results/DET3_RECON/RECON_DET3.md` (090521f8), R1 odtworzony przez CC
  klatka w klatkę: do 14.9 m żaden składnik toru nie traci celu pierwszy (po
  rozgrzewce: YOLO 11/11, MTI(admisja) 10/11, fresh 10/11 na 12–15 m — jak na
  8–10 m); w 48 epizodach FANTOM S2 detektor miał cel w **257/263 klatek rampy
  skanu** przed akwizycją (T6: 6–29 s przed pierwszą fresh). Na obecnej siatce
  (range0 15 m) zasięg nie zmienia nic; dla range0 25/30 m warunkiem byłoby
  MTI w zawisie na 20 m (model idealny mówi NIE, dane z residuum derotacji
  mówią „dalej niż model" — rozstrzygalne tylko pomiarem). Decyzja Olgi 31.10:
  bez nowej rodziny scenariuszy.
  **Zdanie kanoniczne:** „Zasięg detektora nie ogranicza akwizycji na obecnym
  profilu misji; sufit leży w rozgrzewce admisji po wejściu celu w kadr
  i w geometrii przeglądu, nie we wzroku."
  **Errata forward:** „jedyny następca realnie podnoszący sufit" (dopisek
  25.10) nie dotyczy członu (iii) na obecnej siatce. Aktywa: tabela czułości
  per Z (`r1/r1_tabela.json`), rachunek pikselowy 15–30 m, koszt inferencji
  vs imgsz, litera admisji (brak progów zasięgu), projekt kolekcji R4,
  rampa per epizod (`r5_rampa.json`).
- **Nota (NIE pozycja):** czas wpatrywania skanu 1.2 s pochodzi z epoki 5 Hz;
  przegląd < 10.0 s wymaga stare < 0.91 s przy kroku 68.3° (TRANSIT, forma
  zamknięta), a rozgrzewka admisji po wejściu celu w kadr trwa do ~1 s (R1).
  Pomiar latencji admisji po starcie wpatrywania w reżimie 14.7 Hz z logów
  PERC2 S2 (0 bootów) rozstrzyga, czy dźwignia istnieje; otwarcie wyłącznie
  decyzją Olgi.
- Stan: katalog 6 otwartych pozycji bez zmian (PERCEPCJA-II trwa z członem (ii);
  (iii) zamknięty). Breach 0 / REFUSE 0 programowo bez zmian.
```

Sekcja do `results/KSIEGA_PREDYKCJI.md`:

```
## POZYCJA PERCEPCJA-II (iii) daleki wzrok — ZAMKNIĘTA DESKIEM przy CO-DET3-0 (ANEKS_DET3-0, 31.10.2026)
Recon bez PRE i bez predykcji numerowanych. Jedna ocena CC do rozliczenia jako
kalibracja: w raporcie programu i w rozmowie 31.10 CC opisał daleki wzrok jako
„jedyną pozycję, która rusza zmierzony sufit" — recon pokazał, że na obecnej
siatce nie rusza go wcale (intruz startuje z 15 m; detektor widzi cel w 97.7 %
klatek rampy, zanim misja go przyjmie). **✗ kalibracyjne**: ocena wydana bez
sprawdzenia, gdzie startuje intruz względem granicy korpusu.

Lekcja kalibracyjna: zanim pozycja dostanie etykietę „rusza sufit", sprawdzić
literą manifestu, czy mechanizm pozycji w ogóle występuje w zakresie, w którym
sufit jest mierzony (tu: range0 15 m vs korpus do 14.9 m) — recon deskowy
zrobił to w pierwszym pytaniu i dlatego kosztował 0 bootów.
```

## §5. Zlecenie CO-DET3-0 — commit zamykający (samowykonalny; jeden commit, zero bootów)

Bramka: `git fetch` → origin/master == **090521f8**; `origin/master..HEAD`
puste ⇒ dalej; inny stan ⇒ STOP. Pliki (lista zamknięta): korzeń
**`ANEKS_DET3-0.md`** (ARCH-1, verbatim, pierwszy w commicie; byte-check
sha256 podany przez CC w wiadomości i potwierdzony przez Olgę „sha ok");
**EDYCJA `KIERUNKI_PO_PLANIE.md`** — dopisek §4 verbatim, append-only;
**EDYCJA `results/KSIEGA_PREDYKCJI.md`** — sekcja §4 verbatim, append-only.
ŻADNYCH edycji RECON_DET3, narzędzi, FREEZE, PRE ani kodu; żadnych bootów.
Raport płaski: diff-stat, pełna treść dopisków, porcelain. **Push = Olga
(„wypchnięte" — CC sprawdza byte-check, append-only, verbatim).** STOP.

## §6. Status

PERCEPCJA-II (iii): CLOSED-BY-RECON, 0 bootów. Program: wiatr zamknięty,
wabiki zamknięte, daleki wzrok zamknięty; katalog 6 pozycji; materiał na
zewnątrz (raport „Stan na 31 października", demo v6) spójny z repo. Jedyna
tania dźwignia techniczna, która została nazwana i niezmierzona, to czas
wpatrywania skanu (§3) — otwarcie wyłącznie decyzją Olgi.
