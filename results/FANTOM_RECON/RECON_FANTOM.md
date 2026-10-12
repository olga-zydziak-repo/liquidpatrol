# RECON_FANTOM — recon pozycji FANTOM-START (czysty start epizodu) — STOP-FANTOMR

Wykonawca · 12.10.2026 · PROMPT_FANTOM_S0. Zero bootów, zero SITL, zero edycji
istniejących plików; narzędzie `tools/fantom_recon.py` (NOWE; importuje READ-ONLY
z reakw_recon), dane z artefaktów kampanii AKW S3, DET S4 i smoke S2.

**WYNIK GŁÓWNY: dźwignia ZMIERZONA i ŻYWA — górna granica konwersji 6/6 fantomowych
porażek przy czystym starcie** (3×c08 z dowodem wprost empirycznym: te same scenariusze
PRZESZŁY w DET przy czystym starcie; c01/c05/c06: siostry komórek 3/3 PASS, przewidywana
akwizycja 5.6–9.3 s przy budżecie 23 s). Oba prerejestrowane sanity-checki CC
potwierdzone, nie założone: c01_s01 (v=0) KONWERTUJE (akwizycja czystego startu 5.6 s);
c08×3 (bearing 0) — skan w ogóle NIEpotrzebny, cel w stożku podczas dwell
(akwizycja ~1.2 s). Rekomendowana rodzina dźwigni: **(i) KONSUMENT** (kwarantanna
tracków sprzed startu w następcy wrappera; zero dotykania percepcji/choreografii).

## §0. Bramka wejścia — PASS

origin/master zawiera 6f05758d (CO-REAKW) ✓ · ahead pusty ✓ · porcelain pusty ✓ ·
piny 5/5 PASS, certy 9/9 PASS; sha zgodne: akw_scan b94cdeae, rejestr 4f58d204,
det_v2 775ead15, percep 38a3a765, klient 79633489, rejestr feedów ee1481f9, bench
05137098/8ec0fcfb, ncp 0337d5ea. **Kolizja nazwy:** „fantom" w repo wyłącznie jako
słownictwo (komentarze REAKW_RECON/testów), zero przestrzeni nazw; rekomendacja:
env `FANTOM_*`, katalog `results/FANTOM/`, kontroler (jeśli powstanie) `net_fantom`.

## §R1. Choreografia stagingu — gdzie rodzi się fantom (plik:linia + pomiar)

**Sekwencja między epizodami (bench_flight.py):** po epizodzie dron leci na home
(`_fly_to_home_hover`, :290-305; podczas resetu komenda yaw=0 — nos na PÓŁNOC);
intruz jest komenderowany `set_pose` do pozy startowej NOWEGO epizodu i bramkowany
TOL_START (`_intruder_start_gate`, :259-287, GzPoseClient @SETPOSE_HZ, 5 s → retry →
INVALID_START); dopiero potem `t0_sim` + event `episode_start` (:337-339). Kontroler
jest budowany i resetowany PER EPIZOD przed bramką startu (`make_controller` +
`ctrl.reset()`, :310-312); klient feedu V2 też powstaje per epizod (:320-321), ALE
**kanał percepcji żyje w boot-globalnym percep_proc** — lock przenosi się między
epizodami. **Marker startu dla KONSUMENTA istnieje i jest darmowy: `reset()`**
(wrapper wie, że zaczyna się nowy epizod; pierwszy `step()` po reset ≈ t0) — zero
dotykania percepcji.

**Pomiar źródła fantomu (6 porażek; `r1_phantom.json`):** fantom ma DWIE podklasy:

| sid | epizod w boocie | ostatni fresh przed t0 | trk@t0 | d(trk, SPAWN) | d(trk, …) | klasa |
|---|---|---|---|---|---|---|
| c08_s02 | **pierwszy** | −0.10 s (gate mti) | (−0.7, 6.7, −11.7) | 17.0 | staging-świata 0.3 | **spawn-w-świecie intruza** |
| c08_s03 | pierwszy | −0.11 s | (−0.6, 6.7, −11.6) | 16.9 | staging-świata 0.4 | spawn-w-świecie |
| c08_s04 | pierwszy | −0.07 s | (−0.7, 6.8, −11.7) | 17.0 | staging-świata 0.3 | spawn-w-świecie |
| c01_s01 | drugi | +0.03 s (window) | (15.1, 0.1, −9.9) | 21.2 | **koniec poprz. epizodu 0.2** | poprzedni epizod |
| c05_s02 | drugi | −0.09 s (mti) | (5.1, −3.4, −10.2) | 19.1 | koniec poprz. 0.8 | poprzedni epizod |
| c06_s04 | trzeci | +0.02 s (mti) | (8.6, −3.2, −10.3) | 23.8 | koniec poprz. 0.9 | poprzedni epizod |

- Podklasa „spawn-w-świecie" (pierwsze epizody bootów): intruz paruje w pozycji
  świata ≈(−1.0, 6.6, −11) — ta sama, którą S1 nazwał „stagingiem"; kamera łapie go
  1–4 razy w fazie przedstartowej. Podklasa „poprzedni epizod": kamera śledzi starego
  intruza przez CAŁĄ fazę resetu (56–65 freshów w [t0−10, t0]) aż do teleportu.
- Po t0: **zero freshów fantomu** (6/6) → FEED_EXPIRE przy ~0.92–1.07 s (θ_age 3.0
  liczony od ostatniej świeżej sprzed t0) → ślepy start 9.5–26.8 s (dekompozycja §R3).
- Czas admisji fantomu vs start: ostatni fresh −0.11…+0.03 s od t0 (admisje
  przedstartowe; pojedyncze stemple tuż po t0 to ogon kolejki klatek).
- Przypomnienie z REAKW potwierdzone: fantom ma świeże ticki fd w epizodzie
  (age≤0.3) — brama |v| ani świeżość NIE odróżnia; odróżnia go dopiero ZDARZENIE
  (expire / przeskok pozycji), stąd projekt kwarantanny w §R4.

## §R2. Zasięg zjawiska (`r2_scope.json`; fantom := lock@t0 z d(trk, GT_spawn)>5 m)

| korpus | epizody | lock@t0 | fantom@t0 | żywy (age≤1) | fantom-FAIL | fantom-PASS | czysty-FAIL |
|---|---|---|---|---|---|---|---|
| **AKW S3 V2** | 48 | 18 | **17** | 15 | **7**: 6 z expire (zbiór pozycji) + c10_s03 martwy@t0 | **9** (żywe) + 1 martwy | 7 (c09_s02/s03, c10_s01, c11_s01–s04) |
| DET S4 V2 | 48 | 15 | 11 | 10 | 6 | 5 | 29 (ślepe bez skanu — mechanizm DET) |
| AKW S3 B | 48 | 36 | 15* | — | (1: c09_s02 = trudna komórka) | 14 | 1 |

- **Żywy fantom szkodzi SELEKTYWNIE: 9/15 żywych przeszło mimo fantomu** (koszt
  fantomu ≈ expire ~1 s + dwell 2 s + skan od ψ fantomu; wystarcza budżetu poza
  cienkim marginesem). c10_s03: fantom **martwy@t0** (age 1.23 >1.0 — konsument
  w hold od ticku 0, ψ_last=0 po reset) ⇒ jego porażka NIE jest fantomowa (pościg;
  spójne z REAKW „bez utraty"). Czyste-FAIL (7) = pościg v=1.0 — poza zasięgiem.
- **Sufit nagrody pozycji: dokładnie 6 epizodów** (fantom żywy ∧ expire ∧ FAIL);
  ryzyko regresji dotyczy 9 żywych-PASS (rachunek §R5).
- *Ramię B: etykieta „fantom" to artefakt migawki pierwszego ticku — FeedB
  (wyrocznia GT+szum) trzyma hold-last poprzedniej pozycji TYLKO do pierwszej
  próbki GT w epizodzie (f=10 Hz ⇒ ≤0.1 s; track_feed.py:81-100). Symetria
  potwierdzona: w B nie ma analogicznego stanu przedepizodowego dłuższego niż
  0.1 s; obie porażki B to v=1.0 (trudność komórek, nie start).
- **c00 smoke S2 (resmoke_r1_V2): TA SAMA klasa** — fantom żywy (age@t0 0.076,
  d_spawn 17.1, expire 0.94 s) ⇒ wchodzi do zbioru odniesienia pozycji (podtyp:
  cel statyczny po czystym starcie też wymaga admisji MTI — w AKW r1_V2 c00_s01
  przeszedł, 4.2 s).

## §R3. Replay czystego startu na 6 fantomach (POMIAR DŹWIGNI; `r3_cleanstart.json`)

Metoda: kontrfaktycznie zero tracku na starcie ⇒ delegat hold od t0 ⇒ profil II od
ψ_last=0 (reset; nos północ — fizyczny stan po resecie, bo `_fly_to_home_hover`
komenduje yaw=0) ⇒ z GT: pierwsza chwila, gdy cel jest w stożku ±43.45° wokół ψ(t)
profilu II w oknie STARE nieprzerwanie ≥1.0 s (proxy warmupu MTI Δ=3 + k=3) ⇒
przewidywana akwizycja +1 s. Empiryka kontrolna: wyniki SIÓSTR komórki (inne ziarna,
w tym 7 sióstr z ŻYWYM fantomem!) i tego samego sidu w DET.

| sid | ślepota obserwowana [s] | dekompozycja: expire+dwell / skan-od-ψ-fantomu | czysty start: przewidywana akwizycja [s] | margines do t_A=23 | siostry V2 D6 | ten sid w DET | werdykt |
|---|---|---|---|---|---|---|---|
| c01_s01 (b90, v=0) | 22.3 | ~3.1 / 19.2 | **5.6** | 17.4 | 3/3 ✓ | ✗ (ślepy, bez skanu) | **konwertuje** |
| c05_s02 (b90, v=0.5) | 21.9 | ~2.9 / 19.0 | **5.6** | 17.4 | 3/3 ✓ | ✗ | **konwertuje** |
| c06_s04 (b180, v=0.5) | 9.5 | ~3.1 / 6.4 | **9.3** | 13.7 | 3/3 ✓ | ✗ | **konwertuje** |
| c08_s02 (b0, v=1.0) | 26.8 | ~2.9 / 23.9 | **1.2** (dwell wystarcza) | 21.8 | 1/3 (s01 ✓, s03/s04 = fantomy) | **✓ PASS w DET** | **konwertuje** |
| c08_s03 (b0, v=1.0) | 14.7 | ~2.9 / 11.8 | **1.2** | 21.8 | jw. | **✓ PASS w DET** | **konwertuje** |
| c08_s04 (b0, v=1.0) | 20.5 | ~3.0 / 17.5 | **1.2** | 21.8 | jw. | **✓ PASS w DET** | **konwertuje** |

- **Sanity-check 1 (c01_s01, v=0): POTWIERDZONY** — konwertuje; mechanizm jest tym,
  czym go nazwano (fantom+skan-od-złego-ψ, nie „cel statyczny niewykrywalny" —
  siostry v=0 z fantomami przeszły, admisja statycznego celu w stare działa
  empirycznie w całej siatce c00–c03).
- **Sanity-check 2 (c08×3, bearing 0): POTWIERDZONY** — przy czystym starcie skan
  jest NIEPOTRZEBNY: cel w stożku od t0, nos północ (dwell), przewidywana admisja
  ~1.2 s; empirycznie te same scenariusze przeszły w DET (nos stale północ) —
  najmocniejszy dowód dźwigni w danych.
- Dekompozycja ślepoty: stały koszt (a) expire 0.92–1.07 + dwell 2.0 ≈ 3 s; reszta
  (6.4–23.9 s) to (b) skan startujący od ψ fantomu × (c) koincydencja z celem
  ruchomym (admisja wieloprzebiegowa). Czysty start eliminuje (b) w całości
  i redukuje (a) do dwell.
- **Górna granica konwersji: 6/6** (z zastrzeżeniem uczciwym: konwersja D6 wymaga
  jeszcze pościgu po akwizycji — dla c08 dowodzi jej DET-PASS, dla c01/c05/c06
  siostry 3/3). Przełożenie na Δ: 12 → ~6 (pozostają: 7 czystych-FAIL pościgowych
  + c10_s03 martwy-fantom-pościgowy).

## §R4. Przestrzeń dźwigni — dwie rodziny, punkty wpięcia

**(i) KONSUMENT — kwarantanna tracków sprzed startu (REKOMENDOWANA):**
następca wrappera (nowa klasa w rejestrze, +1 linia additive — wzorzec AkwScan/SR-9),
nadpisuje `set_feed` (wzorzec delegacji: akw_scan.py:74-75; most per tick:
bench_flight.py:359-360) i `reset()` (marker startu epizodu: bench_flight.py:310-312).
Reguła (szkic do PRE): po `reset()` fd jest NIEWIDOCZNY dla delegata (traktowany jak
invalid ⇒ hold ⇒ dwell+profil II od ψ_last=0) do PIERWSZEGO z trzech zdarzeń:
(A) przejście invalid→valid fd (czyste ENTRY po expire), (B) przeskok trk_pos
o >5 m względem wartości z chwili reset (przechwyt realnego celu bramą mti kanału —
obserwowany w danych jako „przechwyt"), (C) upływ T_q = θ_age = 3.0 s (fallback:
track odświeżany nieprzerwanie 3 s w epizodzie nie może być fantomem stagingu —
fantom traci źródło admisji w t0; chroni przed ślepotą na lock-real@start, 1/48
w AKW). Wszystkie trzy zdarzenia widoczne w fd (zero GT, zero percepcji). GRANICA
UCZCIWOŚCI: wrapper decyduje wyłącznie, co SAM konsumuje; percepcja/admisja/
telemetria NIETKNIĘTE — fantom zostaje w logach percepcji (żadnego „czyszczenia"
prawdy pomiarowej). Koszt: zero nowych komponentów, zero zmian choreografii,
porównywalność kampanii zachowana (ta sama siatka/driver/profil II FROZEN).

**(ii) CHOREOGRAFIA — zmiana stagingu w driverze:** staging kontrolują
`_intruder_start_gate` (bench_flight.py:259-287) + world-spawn intruza ≈(−1, 6.6)
+ intruder_motion — wszystko w **bench_flight.py (FROZEN dziedziczony 05137098)**
i świecie; „spawn poza FOV / dopiero na starcie" wymagałoby edycji frozen bencha
LUB świata, dotyka OBU ramion i obu kampanii-wzorców (DET S4 i AKW S3 latały z tą
choreografią — zmiana osłabia porównywalność Δ_new2 z Δ=12/Δ=34 u KORZENIA),
a fantom klasy „poprzedni epizod" (3/6) wynika z samego przejścia między epizodami,
nie ze stagingu-parkingu — spawn-fix go nie usuwa. **Odrzucona rachunkiem.**

## §R5. Ryzyka (mechanizmy, liczby)

- **Regresja na 9 żywych-fantom-PASS** (kwarantanna zamienia „śledź fantom ~1 s →
  expire → skan od ψ fantomu" na czysty start): przewidywana akwizycja czystego
  startu vs obserwowana: c04_s01 1.2 vs 15.8 (DUŻO lepiej), c01_s02/s04 5.6 vs 6.5,
  c05_s01 5.6 vs 8.2, c10_s04 9.3 vs 10.1 (lepiej/równo), c07_s02 13.1 vs 12.3
  (neutral; siostra czysta c07_s03 przeszła z 13.2), c07_s01 13.1 (obs. skażona
  freshem fantomu; siostry ✓), **c09_s01 5.6 vs 1.6 (+4 s — jedyny realny kandydat
  regresji**; komórka c09 i tak 2/4, scenariusz graniczny). Bilans: nagroda 6,
  ryzyko ~1 granicznego — wyraźnie dodatni.
- **Koszt re-admisji po kwarantannie:** czysty start = admisja w oknach stare;
  warmup MTI Δ=3 + k=3 @7.58 Hz ≈ 0.8 s < stare 1.2 s (rachunek S2); empirycznie
  kampania S3: admisja ślepych 96–99% w obu modach — bez zmian (kwarantanna nie
  zmienia admisji, tylko konsumpcję).
- **Bezpiecznik modu:** nietknięty (liczy admisje percepcji przy celu w FOV —
  niezależne od konsumenta).
- **θ_age/FEED_EXPIRE:** kwarantanna NIE przedłuża życia tracków — przeciwnie,
  opóźnia konsumpcję; kanał żyje po staremu.
- **Osłona:** `shield.step(k, pos, vel, target, …)` (r01/shield.py:121) konsumuje
  target KOMENDY (tgt z cmd kontrolera), nie track percepcji; kwarantanna ⇒ cmd
  hold (tgt=own, v=0) — stan przechodzony w każdym hold programu; REFUSE pod hold
  konstrukcyjnie nieaktywny (dowód całą nogą AKW: REFUSE 0 ×29 bootów).
- **Oscylacje:** zero nowych stanów skanu — kwarantanna to przedłużenie istniejącej
  gałęzi hold o warunek wejścia; profil II bez zmian (FROZEN b94cdeae); wyjście
  z kwarantanny jednorazowe per epizod (A/B/C), pętla niemożliwa.

## §R6. Projekt kampanii — wycena + higiena

- **(i) Pełna powtórka 12×{B, V2} verbatim** (progi PRE_2A zamrożone; Δ_new2
  porównywalne wprost z Δ_new=12 i Δ=34): 24+3 booty, 1–2 sesje (~7 h). Przewidywanie
  z desku: Δ_new2 ≈ 6 (konwersja 6/6) — kampania rozstrzyga progiem (≤4 przeżywa /
  ≥10 śmierć) na pełnej siatce. W ODRÓŻNIENIU od REAKW tu kampania jest uzasadniona:
  dźwignia zmierzona z niezerową przewidywaną konwersją, a wynik zmienia werdykt
  siatki (34/48 → ~40/48).
- **(ii) Sonda celowana:** 6 fantom-FAIL + kontrola regresji (3–4 z żywych-PASS,
  w tym c09_s01) + c00 ⇒ ~10–11 epizodów = 3 booty V2 (+1 smoke) — tanio (4 booty),
  ale BEZ zamrożonej interpretacji progowej na pełnej siatce (podzbiór nielosowy;
  wynik mechanizmowy, nie werdyktowy) — słabość nazwana wprost.
- **Rekomendacja:** smoke 1 boot (epizody c08_s02-podobne + kontrola c09_s01) →
  przy PASS pełna powtórka (i). Sufit bootów nogi (propozycja do PRE): smoke 1(+1)
  + kampania 24+3 + zapas ⇒ **≤30**.
- **FREEZE_FANTOM:** sha nowego wrappera + rejestru po wpisie, parametry kwarantanny
  (T_q=3.0 s, D_jump=5 m — oba sprzężone z istniejącymi stałymi: θ_age i REFRESH_GATE;
  NIE per-klatka — zdarzeniowe), marker startu = reset() (bez env); dziedziczone
  FREEZE_AKW/DET verbatim. Nazwa: `net_fantom`, env `FANTOM_*` (tylko diagnostyka),
  `results/FANTOM/`.
- **NIE wolno dotknąć:** percepcji (det_v2/FeedVision/MTI/progi admisji), osłony,
  sieci/wag, rejestru feedów, profilu skanu II (b94cdeae), choreografii
  bencha/drivera — zmiana WYŁĄCZNIE w tym, co konsument robi z trackami sprzed
  startu epizodu (nowy wrapper + test + 1 linia rejestru).

## Artefakty

`tools/fantom_recon.py` (r1/r2/r3) · `r1_phantom.json` · `r2_scope.json` ·
`r3_cleanstart.json`. Dalej: **PRE_FANTOM numerowany** (zamrozi dźwignię+parametry,
testy, smoke, wariant kampanii z progami, śmierć pozycji, budżet, predykcje —
z regułami kalibracyjnymi: progi zdarzeniowe nie per-klatka [tu nie ma sprzężenia
z kadencją], interakcja nazwana-a-niezmierzona ⇒ korekta głęboka [tu dźwignia jest
ZMIERZONA deskiem: 6/6 górne, flaga wg ANEKS_REAKW-1 §3 = MECHANIZM ZMIERZONY]).
Sygnały bez numeru odrzucam. STOP-FANTOMR.
