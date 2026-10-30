# RECON_WABIK3 — recon nogi WABIK-III „tor i geometria zbliżenia" — STOP-WABIK3R

Wykonawca · 30.10.2026 · PROMPT_WABIK3_S0. **0 bootów, 0 SITL, 0 treningu, zero edycji
istniejących plików**; nowe pliki wyłącznie `results/WABIK3_RECON/**`. Wszystko policzone na
zamrożonym benchu WABIK-II: 126 lotów = 11 S2 (TP 6 / FP 3 / ORB 2) + 115 NULL (litera
`wabik_sig2.py:load_null`; NULL v=0 36 / v=0.5 38 / v=1.0 41).

## Raport płaski

- **R1:** `box` w percep_feed to top-1 detektora PRZED bramką admisji. Pozostałych detekcji klatki
  nie loguje nikt, a w kampaniach NULL nie ma klatek. **Śledzenia ≥ 2 obiektów NIE da się odtworzyć
  offline**, potrzebne jest nowe logowanie. Wariant bez dotykania plików zamrożonych: zrzut klatek
  kamery + nowy replay det_v2 ze wszystkimi ramkami.
- **R2 (DCPA/TCPA): TAK, istnieje konfiguracja spełniająca kryterium WABIK-II, ale jako
  KANDYDAT z selekcji na tym samym zbiorze.** Streak 4 s na W′ = ruch ∧ strefa ∧ podłoga ∧ ¬atak,
  gdzie atak = cel przechodzi < 7 m od DRONA w ciągu 10 s. Odwołanie: podłoga albo ≥ 1 s ataku.
  Wynik: **TP ≤ 15 s 5/6, FP 0/3, ORB odwołane 2/2, NULL_final 10/115** (baza: 0/6, 0/3, 2/2,
  13/115). Koszty: wyspa wąska w R (R = 5 i R = 9 odpadają), NULL_ever 51/115, etykieta na ORB
  wisi 21–25 s przed odwołaniem.
  Krawędź Pareto (TP≤15, NULL_final) przy FP 0 ∧ ORB 2/2: **(3, 0) · (4, 2) · (5, 10)**.
- **R3 (tor): NIE.** Żaden z 8 estymatorów v_rad przy NIEZMIENIONEJ regule 475c972e nie daje TP
  ≤ 15 s (wszystkie 0/6). Odrzut skoków 0.5 m obniża NULL_final do 4, ale zabiera 2 TP.
- **R4 (mikro-sygnatura): ZAMKNĄĆ przy biurku.** Podłoga szumu toru celu statycznego: MAD 0.21 m
  (p10–p90 0.12–0.46 m), czyli 6.7 px przy 8.5 m. Residuum M5 w oknie 1 s wynosi 3–5 cm we
  wszystkich klasach. Przy dopasowanej prędkości brak separacji (AUC TP vs NULL v=1.0: 0.59).
- **R5 (wędrowcy):** 13/115 NULL-final = **12 wolnych krążących (v=0.5) z GT NIGDY < 5 m** (definicyjnie
  wabiko-podobne; 6 różnych scenariuszy) + **1 percepcja** (v=1.0, AKW r12 c08_s04: pierwszy track
  po 21.45 s, GT dochodzi do home, track nigdy < 5 m).

## §0. Bramka — PASS

origin/master == HEAD == `6084beb6` (STOP-DEMOC-6), `origin/master..HEAD` puste, porcelain czysty
poza nazwanymi `??` (wideo/jpg DEMO_C). FROZEN zgodne (sha256/8): `wabik_sig.py` 475c972e,
`wabik_sig2.py` a8397cb4, `s1_tabela.json` a54e7667, `wabik_manifest.json` 046fa12b,
`wabik_motion.py` e690850c, `percep_proc.py` 38a3a765.
**Odchylenie nazwane (etykieta):** PROMPT §0.2 podaje „feed_vision 79633489”. To sha
`harness/feed_vision_proc.py`, klienta FEED=V2 (FREEZE_DET.md:46), i ten plik jest zgodny. Sam
`harness/feed_vision.py` ma sha `acc81df7`, zgodnie z tym, co cytuje `percep_proc.py:93`
(„acc81df7 READ-ONLY”). Oba pliki są niezmienione od ostatniego commita, który ich dotyczył.
**Kotwica implementacyjna** (asercja w narzędziu): baza(i) policzona w `wabik3_recon.py` odtwarza
`s1_tabela` baza(i) co do liczb: TP≤15 0/6, FP 0/3, ORB 2/2, NULL ever/final 23/13. Estymator E0
z R3 odtwarza też czas flagi każdego epizodu S2 co do 0.01 s.
**Zegar kryterium:** od pierwszej klatki z trk (litera v1 / `wabik_sig2` „od pierwszej”).
Pierwsze przejście narzędzia liczyło od pierwszej próbki z oknem i dawało rozjazd z kotwicą
(TP 2/6 w E0). Kotwica złapała to przed raportem. Wszystkie liczby niżej są po poprawce.

## R1. Co jest w feedzie

- `box` = **top-1 detektora przed bramką**: `harness/det_v2.py:57` (`i = int(r.boxes.conf.argmax())`,
  `predict(conf=0.001)` bez bramkowania). Zapis w `harness/feed_vision.py:221-229` na każdej klatce,
  niezależnie od bramki.
- `trk_pos_ned` = **po bramce**: niepuste wyłącznie gdy `fresh`, czyli koniunkcja admisyjna
  struktura∧MTI albo okno predykcji (`feed_vision.py:194-208`).
- `trk_vel_ned` **nie ma w percep_feed**. Jest w `demo.jsonl` (klient feedu; regresja z okna,
  `feed_vision.py:_trk_vel`) i z tej litery liczone jest R2.
- Surowych detekcji (wszystkich ramek z conf) **nie loguje nic**: `percep_proc.py` zapisuje tylko
  wiersz `FeedVision._ingest`, a `percep_stdout.log` to liczniki (`percep_proc.py:160`).
  `results/DET/tools/det_replay.py` replayuje na klatkach, których kampanie NULL nie mają: brak
  katalogów `frames` w `results/{DET,AKW,FANTOM}/camp/*`.
- **Werdykt:** śledzenia ≥ 2 obiektów nie da się odtworzyć offline. **Wycena dopisania:**
  - (i) logowanie wszystkich ramek w `det_v2.top1` / `FeedVision._ingest` = **dotyka zamrożonych**
    det_v2.py e801f7d5 / feed_vision.py acc81df7 (FREEZE_DET), czyli osobna noga i ANEKS;
  - (ii) **bez dotykania**: zrzut klatek kamery pokładowej (`democ_framedump.py`, sprawdzony w DEMO_C;
    koszt zmierzony z kamerą świata: dsim/dwall 0.95, sama kamera pokładowa mniej) + NOWY replay
    offline det_v2 ze wszystkimi ramkami (te same wagi 775ead15, `model.predict` bez argmax).
    Rekomendacja: (ii).

## R2. Geometria zbliżenia (DCPA/TCPA) — pomiar główny (`r2_dcpa_tabela.json`)

Per tick `demo.jsonl` z `track_valid`. Względem HOME: p = trk, v = trk_vel. Względem DRONA:
p = trk − own, v = trk_vel − own_vel. Wzory: TCPA = −p·v/|v|², DCPA = |p + v·max(TCPA, 0)|,
DCPA wygładzona średnią kroczącą 1 s. „Atak” = TCPA > 0 (∧ TCPA < H) ∧ DCPA < R.

**Rozkłady cech per klasa (p10 / p50 / p90 median epizodów):**

| klasa | n | DCPA_home [m] | DCPA_dron [m] | frakcja ataku (home, R 5) | t do DCPA_min(4 s) > 5 m [s] |
|---|---|---|---|---|---|
| TP | 6 | 10.5 / **12.0** / 14.7 | 8.2 / 8.3 / 8.6 | 0.00 / **0.01** / 0.19 | 3.9 / 8.3 / 14.6 |
| FP (atakujące) | 3 | 1.5 / **2.9** / 3.6 | 8.0 / 8.3 / 8.7 | 0.45 / **0.47** / 0.50 | 15.8 / 18.8 / 21.9 (2/3) |
| ORB | 2 | 10.1 / 10.2 / 10.2 | 8.3 / 8.4 / 8.4 | 0.23 / 0.24 / 0.25 | 10.5 / 12.2 / 14.0 |
| NULL v=0 | 36 | 12.9 / 13.6 / 14.2 | 8.2 / 8.2 / 8.3 | 0.02 / 0.04 / 0.06 | 3.9 / 3.9 / 10.0 |
| NULL v=0.5 | 38 | 3.5 / **6.7** / 9.8 | 8.0 / 8.2 / 8.4 | 0.07 / 0.33 / 0.49 | 5.1 / 17.0 / 35.4 |
| NULL v=1.0 | 41 | 2.1 / **4.2** / 6.8 | 7.8 / 8.2 / 8.7 | 0.34 / 0.42 / 0.48 | 3.9 / 17.7 / 25.9 |

DCPA względem home separuje TP od atakujących i ruchomych NULL wyraźnie, na poziomie mediany
epizodu (12.0 vs 2.9 / 4.2 / 6.7 m). DCPA względem drona ma medianę ~8.2 m we wszystkich klasach
(dron krąży na 6–10 m), więc separuje dopiero w regule z horyzontem.

**Siatka (lista zamknięta, 208 konfiguracji):**
- rodzina STREAK: ref ∈ {home, dron} × H ∈ {∞, 10 s} × R ∈ {3, 5, 7, 9} m × T ∈ {4, 6, 8, 10, 12} s ×
  odwołanie ∈ {podłoga (litera FREEZE), podłoga + ≥ 1 s ataku};
- rodzina FRAC (home): R × T ∈ {4, 6, 8, 10} × φ ∈ {0, 0.1, 0.2}.

Predykat ruchu, strefy i podłogi to litera FREEZE_WABIK (0.30 / 18 / 5.0). Warunek v_rad < 0.30
zastąpiono ¬atak. Progi FREEZE nie są zmienione, warianty żyją wyłącznie w nowym narzędziu.

**Wynik: dopuszczonych 4/208**, wszystkie przy ref = dron, R = 7, T ∈ {4, 6}, odwołanie podłoga+atak:

| konfiguracja | TP≤15 | TP_final | FP | ORB odw. | NULL ever | NULL final |
|---|---|---|---|---|---|---|
| dron · H 10 · R 7 · T 4 | **5/6** | 5/6 | **0/3** | **2/2** | 51 | **10** (wszystkie v=0.5) |
| dron · H 10 · R 7 · T 6 | 5/6 | 5/6 | 0/3 | 2/2 | 40 | 11 |
| dron · H ∞ · R 7 · T 4 | 5/6 | 2/6 | 0/3 | 2/2 | 51 | 11 |
| dron · H ∞ · R 7 · T 6 | 5/6 | 2/6 | 0/3 | 2/2 | 40 | 11 |
| *baza(i) FREEZE (odniesienie)* | 0/6 | 4/6 | 0/3 | 2/2 | 23 | 13 |

Czasy flagi TP najlepszego kandydata (H 10, R 7, T 4) wobec bazy:

| | w00a | w00b | w01a | w01b | w02a | w02b |
|---|---|---|---|---|---|---|
| kandydat [s] | 9.8 | 7.4 | 10.1 | 22.3 | 11.8 | 4.2 |
| baza [s] | 17.6 | 21.0 | 15.5 | 24.9 | — | — |

Typ W-ZBLIŻ (w02), w WABIK-II „strukturalnie niemożliwy”, zostaje oflagowany w 4–12 s.

**Krawędź Pareto (TP≤15, NULL_final) przy FP 0 ∧ ORB 2/2:**

| punkt | konfiguracja | TP_final |
|---|---|---|
| (3, 0) | dron · R 9 · T 4 · podłoga+atak | **0/6** — odwołanie atakiem cofa wszystkie wabiki |
| (4, 2) | home · R 9 · T 4 · podłoga+atak | **2/6** |
| (5, 10) | kandydat wyżej | 5/6 |

Punkty (3, 0) i (4, 2) są zdegenerowane i nie nadają się na kandydatów.

**Kwalifikatory (obowiązkowe):**
1. **Selekcja na tym samym zbiorze:** 208 konfiguracji, 4 dopuszczone, wszystkie na JEDNEJ wartości R.
   Sąsiedzi odpadają: R = 5 daje NULL_final 15, R = 9 daje TP 3/6 i TP_final 0. Wyspa jest wąska,
   więc to KANDYDAT do PRE z walidacją na świeżych wariantach w locie, nie werdykt.
2. **NULL_ever 40–51/115:** flaga chwilowo zapala się na 35–44% zwykłych lotów i jest odwoływana
   (baza: 23). Kryterium WABIK-II tego nie liczy, a operacyjnie to migotanie etykiety.
3. **ORB:** flaga pada po 7.8 / 6.4 s, odwołanie (podłogą, nie atakiem) po 33.1 / 28.5 s. Zła etykieta
   na manewrze pod orbitą wisi więc 25 / 22 s (baza: 11 s). Czas zyskany na wabiku jest też czasem
   dłuższej pomyłki na manewrze.
4. **Ref = dron:** „atak” znaczy zbliżenie do DRONA (który krąży wokół celu), nie do chronionego
   punktu. Wersje względem home dochodzą najwyżej do (4, 2), czyli TP≤15 = 4/6. Mechanizm przewagi
   wersji „dron” jest NIEZMIERZONY.

## R3. Tor — ile szumu da się zdjąć (`r3_estymatory.json`)

Reguła 475c972e BEZ ZMIAN (W, T_FLAG 12, streak, odwołanie). Zmienia się wyłącznie estymator
speed / v_rad. Estymatory:
- **E0** = litera FREEZE (2 punkty, 1 s; kotwica);
- **med1 / med2** = mediana różnic klatkowych w 1 / 2 s;
- **ls1 / ls2** = MNK w 1 / 2 s;
- **ts2** = Theil–Sen 2 s;
- **jump_0.5 / jump_1.0** = odrzut klatek o skoku > J od ostatniej przyjętej + E0.

| estymator | TP≤15 | TP_final | FP | ORB | NULL ever/final | TP: p95 v_rad (med) | TP: frakcja pików ≥ 0.30 | przerwania licznika TP / NULL v0.5 |
|---|---|---|---|---|---|---|---|---|
| E0 (kotwica) | 0/6 | 4 | 0 | 2 | 23 / 13 | 0.86 | 16.4% | 12 / 96 |
| med1 | 0/6 | 4 | 0 | 2 | 16 / 9 | 0.81 | 19.7% | 30 / 151 |
| med2 | 0/6 | 4 | 0 | 2 | 27 / 14 | 0.72 | 18.0% | 15 / 69 |
| ls1 | 0/6 | 4 | 0 | 2 | 25 / 14 | 0.81 | 15.1% | 12 / 79 |
| ls2 | 0/6 | 4 | 0 | 2 | 31 / 15 | 0.74 | 12.6% | 10 / 45 |
| ts2 | 0/6 | 4 | 0 | 2 | 31 / 15 | 0.74 | 11.1% | 10 / 41 |
| jump_0.5 | 0/6 | 2 | 0 | 2 | 6 / 4 | 0.24 | 3.9% | 4 / 24 |
| jump_1.0 | 0/6 | 3 | 0 | 2 | 19 / 13 | 0.34 | 6.5% | 11 / 69 |

- **Żaden estymator nie przesuwa TP do ≤ 15 s.** Najszybszy TP: w01a 15.3 s przy ls1, wobec 15.51
  s w E0.
- Wygładzanie zmniejsza przerwania licznika, ale pozostałe 11–18% pików v_rad ≥ 0.30 na TP
  nadal rwie 12-s streak.
- Odrzut skoków obcina piki (TP 3.9%), lecz naiwny filtr gubi dane po prawdziwym przesunięciu
  tracka (brak re-kotwiczenia) i odbiera flagę w00a / w01b.
- **Krawędź Pareto R3:** (0, 4), czyli z punktu widzenia czasu na decyzję pusta.

**Skoki |Δtrk_pos| między kolejnymi świeżymi klatkami** (frakcja par):

| próg | TP | FP | ORB | NULL v0 | NULL v0.5 | NULL v1 |
|---|---|---|---|---|---|---|
| J 0.5 m | 1.5% | 0.7% | 0.6% | 1.2% | 2.2% | 7.9% |
| J 1.0 m | 0.5% | 0.4% | 0.2% | 0.4% | 0.7% | 1.4% |

**Odchylenie nazwane:** „24.3%” z PROMPT (ANEKS_WABIK-1:17) to INNA miara: atrybucja trk do
najbliższego z DWÓCH obiektów w smoke S1 A. W benchu 126 lotów jest jeden obiekt na lot, więc
przeskok tożsamości między obiektami nie może zajść. Na tym samym smoke A miara skokowa daje
4.95% (J 0.5) / 1.98% (J 1.0) wobec 24.3% atrybucji. **Skok pozycyjny nie wykrywa przeskoku
tożsamości** (obiekty bliżej niż próg skoku), co jest argumentem za R1 (ii) przed MULTI-TARGET.

## R4. Mikro-sygnatura (`r4_mikro.json`)

**Rachunek pikselowy:**
- FX = FY = 270 px (`r02/mti.py:18`), obraz 640×480. Przy 15 m 1 px = 5.6 cm, więc sylwetka
  9 px ≈ 0.50 m.
- Kadencja 14.7 Hz daje ~15 próbek na okno 1 s.

**Szum śladu celu statycznego** (NULL v=0, 36 lotów, zasięg mediana 8.5 m):

| | p10 | p50 | p90 |
|---|---|---|---|
| MAD pozycji [m] | 0.12 | **0.21** | 0.46 |
| [px przy 8.5 m] | 3.8 | 6.7 | 14.3 |

Przy 15 m to samo 0.21 m daje 3.8 px. Szum zawiera błąd projekcji z attitude drona, nie tylko
jitter ramki.

**Metryki gładkości** (okna 1 s, mediana epizodu):
- **M5** (residuum po wielomianie 2. st., p50): **3.2 cm** u statycznych, 3.5 / 4.4 cm u NULL
  v = 0.5 / 1.0, **4.8 cm u TP**, 4.2 cm u FP.
- **AUC TP vs NULL v=1.0** (ta sama prędkość): M1 0.004 / M2 0.68 / M5 **0.59**.
- **AUC TP vs NULL v=0.5:** M5 0.89 i M1 0.23. To zmiennik prędkości i krzywizny toru (TP lata
  v = 1.0 po łukach), nie mikro-ruch.

**Werdykt: ZAMKNĄĆ przy biurku (w tym symulatorze i tą kamerą).**
- W symulatorze wabik i cel to TEN SAM model fizyczny, a `wabik_motion.py` jest kinematyczny,
  więc mikro-sygnatury nie ma czego mierzyć.
- Podłoga szumu residuum 1 s to 3–5 cm (~1 px przy 15 m). Mikro-ruch musiałby mieć amplitudę
  ≳ 2× podłoga (≳ 6–10 cm, 1–2 px przy 15 m) w paśmie < 7 Hz (Nyquist przy 14.7 Hz), żeby był
  w ogóle mierzalny. Wibracje skali wirnika (mm–cm, setki Hz) leżą poza zasięgiem.
- Otwarcie IMITACJE wymaga innej kamery (rozdzielczość / kadencja) albo realnego sprzętu.

## R5. Wędrowcy — 13/115 NULL-final (`r5_wedrowcy.json`)

| lot | v | bearing | 1. trk [s] | dh_min trk / GT [m] | w strefie [s] | flaga [s] | klasa |
|---|---|---|---|---|---|---|---|
| DET_S4 r11 c04_s04 | 0.5 | 0 | 1.92 | 5.89 / 6.08 | 72.1 | 31.9 | GT nigdy < 5 m |
| AKW_S3 r2 c04_s01 | 0.5 | 0 | 15.82 | 5.22 / 5.20 | 59.9 | 17.8 | GT nigdy < 5 m |
| AKW_S3 r8 c05_s03 | 0.5 | 90 | 5.31 | 5.37 / 5.51 | 72.0 | 19.2 | GT nigdy < 5 m |
| AKW_S3 r8 c06_s03 | 0.5 | 180 | 11.38 | 6.21 / 6.32 | 70.6 | 19.7 | GT nigdy < 5 m |
| AKW_S3 r11 c04_s04 | 0.5 | 0 | 1.28 | 6.04 / 6.08 | 69.6 | 31.3 | GT nigdy < 5 m |
| AKW_S3 r11 c05_s04 | 0.5 | 90 | 5.01 | 8.44 / 8.57 | 67.0 | 18.5 | GT nigdy < 5 m |
| AKW_S3 r11 c06_s04 | 0.5 | 180 | 0.02 | 6.41 / 6.42 | 59.0 | 27.1 | GT nigdy < 5 m |
| **AKW_S3 r12 c08_s04** | **1.0** | 0 | **21.45** | 5.62 / **0.00** | 50.0 | 37.8 | **percepcja** (późna akwizycja; track nie widział zbliżenia) |
| FANTOM_S2 r2 c04_s01 | 0.5 | 0 | 14.84 | 5.14 / 5.20 | 61.5 | 18.5 | GT nigdy < 5 m |
| FANTOM_S2 r8 c05_s03 | 0.5 | 90 | 5.79 | 5.53 / 5.51 | 61.1 | 26.8 | GT nigdy < 5 m |
| FANTOM_S2 r8 c06_s03 | 0.5 | 180 | 9.14 | 6.20 / 6.32 | 67.8 | 18.5 | GT nigdy < 5 m |
| FANTOM_S2 r11 c05_s04 | 0.5 | 90 | 5.16 | 8.46 / 8.57 | 70.6 | 18.2 | GT nigdy < 5 m |
| FANTOM_S2 r11 c06_s04 | 0.5 | 180 | 9.25 | 6.52 / 6.42 | 69.2 | 54.6 | GT nigdy < 5 m |

- **12/13 = klasa definicyjna:** wolny cel (v=0.5) krążący w strefie, który W PRAWDZIE (GT
  z manifestu) nigdy nie zszedł < 5 m. Track zgadza się z GT co do ≤ 0.2 m.
- Reguła z podłogą 5 m nie ma informacji, by go odróżnić. To 6 różnych scenariuszy (c04_s01,
  c04_s04, c05_s03, c05_s04, c06_s03, c06_s04 + powtórzenia w trzech kampaniach).
- **PRE powinno tę klasę rozdzielić w kryterium JAWNIE.** Linia planszy v6 („wolny cel, który
  tylko krąży, pozostaje nierozróżnialny”) jest zgodna z liczbą.
- **1/13 = percepcja:** pierwszy track po 21.45 s, GT dochodzi do home (0.0 m), track nie
  widział zbliżenia. Ta sama klasa co pozycja PERCEPCJA-II.
- Kandydat R2 (H 10, R 7, T 4) zostawia 10 z nich: 9 z listy bazy + 1 nowy (DET_S4 r11 c05_s04,
  v = 0.5, ten sam scenariusz co AKW / FANTOM r11). Lot percepcyjny c08_s04 schodzi.

## R6. Wycena + rekomendacja

| ścieżka | stan deskowy | booty S2 |
|---|---|---|
| **(a) DCPA/TCPA-first** | jest kandydat spełniający kryterium WABIK-II na benchu (5/6 · 0/3 · 2/2 · 10/115) z 4 kwalifikatorami R2 | ≤ 4: świeże warianty trajektorii z manifestu (W-LOITER / W-STYCZNY / W-ZBLIŻ z innym r / b / głębokością zbliżenia + 1 atakujący + 1 M-POD-ORBITĄ), kandydat zamrożony przed lotem, NULL bez nowych lotów (bench) |
| **(b) tor-first** | **NIE** sam z siebie (R3: 0/6 we wszystkich 8 estymatorach) | nie uzasadnione |
| **(c) obie** | tor może być drugorzędnym reduktorem NULL (jump_0.5: NULL_final 4), ale naiwny odrzut zabiera TP; sensowny dopiero z re-kotwiczeniem | dopiero po (a) |

**Co zmienia odpowiedź pilota:**
- **Obrona ZAKŁADA uzbrojenie każdego celu:** czas na decyzję nie jest miarą, a etykieta służy
  priorytetyzacji. Liczy się wtedy wyłącznie FP 0 (nigdy nie zdjąć atakującego) i odwołanie ORB.
  Kandydat (a) to spełnia. Kosztem jest NULL_ever 51/115 i dłuższa zła etykieta na ORB (22–25 s).
  Etykieta nie może wtedy zdejmować uwagi z celu.
- **Obrona ODRÓŻNIA wabik:** kandydat (a) daje medianę ~10 s wobec ≥ 15.5 s w bazie i 2/6 nigdy.
  Kryterium PRE musi wtedy dodać ograniczenie okna złej etykiety na ORB i migotania NULL_ever,
  których WABIK-II nie liczył.

**Propozycje do PRE (rozstrzyga PRE, nie recon):**
- **Kryterium:** WABIK-II 1:1 + (i) TP_final ≥ 5/6, (ii) okno złej etykiety ORB ≤ X s,
  (iii) NULL_ever ≤ Y (raport). Wędrowcy v = 0.5 z GT ≥ 5 m jako klasa JAWNA (osobny mianownik).
- **Śmierć:** kandydat zamrożony przed lotem nie daje TP ≥ 5/6 w ≤ 15 s na świeżych wariantach
  ALBO jakikolwiek FP ⇒ ścieżka (a) zamknięta. MULTI-TARGET wymaga wcześniej R1 (ii).

## Pliki (nowe; sha256/16)

| plik | sha |
|---|---|
| `tools/wabik3_recon.py` | 5dbc94ec0a3c2b97 |
| `r2_dcpa_tabela.json` | 7cee6f96ae02da61 |
| `r3_estymatory.json` | 9ff5dd7bf6652d4f |
| `r4_mikro.json` | 67e086b8ff4a779c |
| `r5_wedrowcy.json` | 783f5406eba9caa8 |

Odtworzenie: `python3 results/WABIK3_RECON/tools/wabik3_recon.py all` (kotwice są asercjami).

Diff-stat i porcelain: commit STOP-WABIK3R. W commicie WYŁĄCZNIE `results/WABIK3_RECON/**`
(6 plików nowych), zero edycji istniejących. W drzewie zostają tylko nazwane `??` DEMO_C.

**Push = Olga („wypchnięte”; CC przelicza niezależnie krawędź Pareto). STOP-WABIK3R.**
