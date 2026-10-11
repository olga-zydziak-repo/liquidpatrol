# RECON_REAKW — recon nogi RE-AKW (re-akwizycja kierunkowa z trk_vel_ned) — STOP-REAKWR

Wykonawca · 12.10.2026 · PROMPT_REAKW_S0. Zero bootów, zero SITL, zero edycji
istniejących plików; narzędzie `tools/reakw_recon.py` (NOWE), dane WYŁĄCZNIE
z artefaktów kampanii AKW S3 (`results/AKW/camp`) i GT.

**WYNIK GŁÓWNY (uprzedzając szczegóły, bo rozstrzyga o kształcie nogi):** replay
kierunkowy R3 na zbiorze odniesienia (14 porażek V2 kampanii AKW) **FALSYFIKUJE
dźwignię „pamięć kierunku z trk_vel_ned" w kształcie z ANEKS_AKW-3 §7: górna granica
konwersji przy REALNYM fd = 0/14.** Jakość trk_vel_ned przy żywym tracku jest dobra
(R1: 3.9–17° przy v=1.0), ale w chwilach UTRATY w porażkach nośnik umiera dokładnie
wtedy, gdy jest potrzebny: 6/9 utrat to fantomy F2 (fd wskazuje staging, 83–175° od
celu), 2/9 ma vel-śmieć (7.6–16.8 m/s — artefakt okna linreg na skoku), 1/9 ma ślepy
odcinek 0.3 s (kierunek nieistotny); 5/14 porażek NIE MA żadnej utraty po akwizycji
(czysty pościg — sufit mechanizmu). Szczegóły i uczciwe opcje w R3/R5.

## §0. Bramka wejścia — PASS

origin/master zawiera eac656e (CO-AKW) ✓ · ahead pusty ✓ · porcelain pusty ✓ ·
FROZEN wykonaniem: piny 5/5 PASS, certy 9/9 PASS; sha zgodne: akw_scan **b94cdeae**,
rejestr 4f58d204, det_v2 775ead15, percep_proc 38a3a765, klient 79633489, rejestr
feedów ee1481f9, bench 05137098/8ec0fcfb, ncp 0337d5ea, feed_vision acc81df7.
**Kolizja nazwy:** „REAKW"/„RE-AKW" występuje w repo wyłącznie w dokumentach
(ANEKS_AKW-3, KIERUNKI, RAPORT_AKW — wzmianki o pozycji katalogu); zero kodu, env,
katalogów. Rekomendacja: prefiks env `REAKW_*`, katalog `results/REAKW/`, kontroler
(jeśli powstanie) — nazwa rejestru `net_reakw`.

## §R1. Co wrapper widzi w chwili utraty + czym jest trk_vel_ned

**Kontrakt (iden­tyczny we wszystkich trzech producentach):** `{trk_pos_ned,
trk_vel_ned, track_age_s, track_valid, feed_sha}` — `harness/track_feed.py:74-78`
(FeedB._out), `harness/feed_vision.py:243-252` (FeedVision.sample),
`harness/feed_vision_proc.py:6-8,61-76` (klient V2 w locie, ZOH ostatniej wiadomości
UDS; nota: trk_vel ZOH z t_frame, odchyłka okna ≤~0.07 s).

**Semantyka po utracie (V2):** `FeedVision.sample` trzyma OSTATNIĄ pozycję
z rosnącym age (`feed_vision.py:246-248`; valid = locked ∧ pos), ALE:
- `trk_vel_ned` = linreg na oknie **1.0 s** z próbek ŚWIEŻYCH (`_trk_vel`,
  `feed_vision.py:234-240`; `VEL_WINDOW_S=1.0` :50) — po ~1 s bez fresh okno ma <2
  próbki ⇒ **[0,0,0]**. Vel umiera szybciej, niż konsument orzeka utratę
  (TRACK_LOSS_S=1.0, `net_controller.py:35,106-111`).
- po **FEED_EXPIRE** (θ_age 3.0 s, `feed_vision.py:174-185`) kanał jest resetowany:
  `_last_pos=None, _issued=[]` ⇒ sample zwraca **pos [0,0,0], valid False** — feed
  NIE pamięta nic.

**Wniosek kontraktowy:** wrapper NIE dostaje użytecznej pamięci z fd w chwili utraty
— musi buforować ostatni DOBRY stan sam (jak dziś buforuje ψ_last). Wpięcie:
`AkwScan` deleguje `set_feed` przez `__getattr__` (`akw_scan.py:74-75`) — RE-AKW
wymagałoby nadpisania `set_feed` w wrapperze (buforowanie przy track_valid ∧ age
małym), zero zmian kontraktów; bench woła `feed.sample → ctrl.set_feed` per tick
(`bench_flight.py:359-360`). FeedB (B): hold-last pos, valid pozostaje True przy
dropie (`track_feed.py:93-96`), ta sama śmierć vel po 1 s (:66-72) — symetria
zachowana, ale B tracku nie traci (wyrocznia).

**Jakość trk_vel_ned na ważnych trackach (age≤0.3) — kampania AKW, demo.jsonl,
GT różnicą centralną ±0.25 s (`vel_quality.json`):**

| ramię | v_intr | n | \|Δv\|_xy p50/p90 [m/s] | błąd kąta kierunku p50/p90 [°] |
|---|---|---|---|---|
| V2 | 0.0 | 24953 | 0.079 / 0.221 | (kurs GT niezdefiniowany; szum modułu 0.08) |
| V2 | 0.5 | 17573 | 0.101 / 0.307 | **6.0 / 24.1** |
| V2 | 1.0 | 18354 | 0.137 / 0.484 | **3.9 / 17.0** |
| B  | 0.5 | 22484 | 0.673 / 1.259 | 42.0 / 127.0 |
| B  | 1.0 | 22410 | 0.688 / 1.316 | 23.8 / 72.3 |

Przy ŻYWYM tracku V2 ekstrapolacja ma sens (kierunek 4–17°). Paradoks nogi: ta
jakość jest dostępna tylko wtedy, gdy nie jest potrzebna (track żywy); w porażkach
w chwili utraty bufor niesie fantom albo śmieć (R3). Nota: vel B (wyrocznia
z szumem σ_xy=0.5, linreg 1 s) jest ~5× gorszy kierunkowo niż V2 — pinhole V2 po
akwizycji jest po prostu dokładniejszy (spójne z DET/AKW err_fresh).

## §R2. Przestrzeń zachowania (projekt bez budowy; rachunek)

Szkic z ANEKS_AKW-3 §7: utrata → dwell 2.0 (bez zmian) → obrót do ψ_pred(Δt) =
azymut(last_pos + last_vel·Δt − own) → sektor lokalny wokół ψ_pred → po T_local
powrót do pełnego skanu (profil II bez zmian).

**Rachunek błędu ψ_pred** (szum z R1, zasięgi 5–15 m z R3): błąd poprzeczny ≈
|δv|·Δt + v·Δt·sin(δθ); przy p90 (δv 0.48, δθ 17°, v=1.0): Δt=2 s → ~1.5 m → ~8°
@11 m; Δt=4 s → ~3.1 m → ~16°; Δt=8 s → ~6.2 m → ~32°. Do tego manewr celu (R4):
10.8% okien 2 s i 28.1% okien 5 s ze zmianą kursu >45° (v=1.0). ⇒ okno użyteczności
ψ_pred: **Δt ≤ ~4 s** (p90 błędu < pół-stożka 43.45°), potem szybka degradacja.
Kandydaci parametrów (gdyby noga szła): sektor = ψ_pred ± 1 krok (pokrycie
±(43.45+40)=±83°), T_local = 2 cykle (3.7 s), brama wiarygodności bufora
**|v|≤3 m/s** (KONIECZNA — R3 łapie vel 7.6–16.8 m/s z okna linreg na skoku
refreshu/teleportu) + świeżość bufora ≤1.0 s przed utratą.

**Punkt wpięcia potwierdzony:** wyłącznie `r03/controllers/akw_scan.py` — nadpisanie
`set_feed` (bufor) + gałąź po-utracie w `step` (`akw_scan.py:91-106`; profil pełnego
skanu, ψ_last, reset, pass-through nietknięte); rejestr bez zmian (wrapper ten sam,
`make_controller("net_akw")`); bench/osłona/percepcja nietykalne (dowód łańcucha:
`bench_flight.py:359-360` jedyny most feed→kontroler).

## §R3. Replay kierunkowy na 14 porażkach V2 (desk; `dir_replay.json`)

Metoda: utrata = przejście track→hold w demo.jsonl (po akwizycji; pierwszy hold
epizodu to AKWIZYCJA, nie re-akwizycja); dla każdej utraty ψ_pred z (a) ostatniego
ticku track (raw) i (b) bufora świeżego age≤0.3 (buf, z bramą |v|≤3); porównanie
z azymutem GT w Δt∈{2,4,8} s; stożek ±43.45°, krok 40°.

| porażka | utrat | t_utraty [s] | ślepy odcinek [s] | bufor: \|v\| [m/s] | err ψ_pred vs GT @2/4/8 s [°] | w stożku ≤1 krok? | klasa |
|---|---|---|---|---|---|---|---|
| c01_s01 | 3 | 1.07 | **22.3** | 0.24 | 100/100/98 | ✗ | **fantom-start** |
| | | 29.2 / 41.2 | 0.16 / 0.41 | 0.34 / 0.07 | 2–19 | ✓ | reakw. natychmiastowa (nieistotna) |
| c05_s02 | 1 | 0.92 | **21.9** | 0.03 | 118/117/116 | ✗ | **fantom-start** |
| c06_s04 | 2 | 1.07 | **9.5** | 0.18 | 167/168/168 | ✗ | **fantom-start** (druga utrata 0.15 s — nieistotna) |
| c08_s02 | 1 | 0.92 | **26.8** | 0.00 | 91/91/84 | ✗ | **fantom-start** |
| c08_s03 | 1 | 0.92 | **14.7** | 0.07 | 92/92/84 | ✗ | **fantom-start** |
| c08_s04 | 1 | 0.97 | **20.5** | 0.01 | 92/91/83 | ✗ | **fantom-start** |
| c09_s02 | 0 | — | — | — | — | — | **bez utraty (pościg)** |
| c09_s03 | 0 | — | — | — | — | — | **bez utraty (pościg)** |
| c10_s01 | 0 | — | — | — | — | — | **bez utraty (pościg)** |
| c10_s03 | 0 | — | — | — | — | — | **bez utraty (pościg)** |
| c11_s01 | 1 | 14.4 | **9.1** | **12.03 (śmieć)** | 138/163/169 | ✗ (brama odrzuca) | vel-śmieć |
| c11_s02 | 1 | 13.5 | 0.31 | **3.09 (śmieć)** | 6–37 | ✓ | reakw. natychmiastowa (nieistotna) |
| c11_s03 | 0 | — | — | — | — | — | **bez utraty (pościg)** |
| c11_s04 | 2 | 14.2 | **13.1** | **7.61 (śmieć)** | 69/88/105 | ✗ (brama odrzuca) | vel-śmieć (druga utrata 0.05 s — nieistotna) |

**Rozbiór (liczby wprost):**
- **5/14 bez żadnej utraty po akwizycji** — track trzymany do końca, D6 i tak pada:
  czysty deficyt pościgu przy v=1.0. ŻADNA strategia re-akwizycji ich nie dotyczy —
  **sufit mechanizmu nazwany uczciwie: ≥5/14 poza zasięgiem nogi.**
- **6/9 utrat = fantom-start** (t_utraty 0.9–1.1 s; c01_s01, c05_s02, c06_s04,
  3×c08): lock F2 na stagingu sprzed teleportu, FEED_EXPIRE ~1 s po starcie, ślepy
  odcinek 9.5–26.8 s. **ψ_pred (nawet z bufora ŚWIEŻEGO age≤0.3) wskazuje 83–175°
  OD celu** — pamięć kierunku jest tu ANTYSYGNAŁEM; brama |v|≤3 NIE odróżnia fantomu
  (fantom jest wolny), `fresh_in_ep` też nie (fantom ma świeże ticki fd age≤0.3
  w epizodzie — zmierzone w dir_replay.json). Sektor-najpierw POGORSZYŁBY te przypadki o T_local.
  **DOPRECYZOWANIE MECHANIZMU c08 względem RAPORT_AKW §4.2:** „skan odkręca nos od
  celu" = w danych dokładnie fantom-F2 → expire → skan OD ψ fantomu; to interakcja
  fantom×skan (klasa c00 z S1, teraz kosztująca pary), nie brak pamięci kierunku.
- **2/9 utrat = vel-śmieć** (c11_s01, c11_s04: |v| bufora 7.6–16.8 m/s — okno linreg
  łapie skok pozycji refreshu window-gate/teleportu): brama plauzybilności odrzuca ⇒
  zachowanie NEUTRALNE (pełny skan jak dziś); bez bramy — err 69–169° (szkodzi).
- **1/9 = ślepy odcinek 0.31 s** (c11_s02) — reakwizycja natychmiastowa, kierunek bez
  znaczenia.

**Konwersja górna: przy REALNYM ψ_pred (fd + brama) = 0/14; bez bramy < 0
(pogorszenie 6 fantomów + 2 śmieci).** Przy IDEALNYM kierunku (wyrocznia GT
w chwili utraty — NIEDOSTĘPNA z kontraktu): kandydatów 8 (6 fantomowych + c11_s01
+ c11_s04; skrócenie ślepych odcinków z 9.1–26.8 s do ~3–4 s), ale to wymaga
informacji, której feed po utracie nie niesie — ideał mierzy wartość INNEGO
mechanizmu (anty-fantom / zewnętrzny prior), nie pamięci trk_vel_ned. Strata czasowa
ślepych odcinków per porażka: kolumna wyżej (9.1 / 9.5 / 13.1 / 14.7 / 20.5 / 21.9 /
22.3 / 26.8 s — wszystkie rzędu lub powyżej pełnego przeglądu 16.8 s, bo cel
TRANSITUJE i wymaga koincydencji ze stare — admisja wieloprzebiegowa jak c00 S1).

## §R4. Ryzyka (mechanizmy, liczby)

- **Szum vel → błąd ψ_pred:** rachunek w R2 (p90 ~8°@2 s → ~32°@8 s); okno
  użyteczności ≤~4 s. Rozkłady: `vel_quality.json`.
- **Manewr celu (`maneuver.json`):** trajektorie segmentowe — mediana zmiany kursu
  ~0°, ale ogon: v=1.0 → 10.8% okien 2 s i **28.1% okien 5 s ze zmianą >45°**
  (v=0.5: 9.5%/24.8%). Ekstrapolacja >4–5 s psuje się nawet przy idealnym vel.
- **θ_age/FEED_EXPIRE:** pamięć wrappera żyłaby dłużej niż kanał (kanał zeruje się
  przy expire — `feed_vision.py:174-185`). To zachowanie warstwy misji, nie
  percepcja — ale GRANICA UCZCIWOŚCI: bufor wolno konsumować TYLKO do decyzji „dokąd
  patrzeć", nigdy jako źródło tracku/admisji (ENTRY nadal wyłącznie brama
  struktura∧MTI). Ryzyko nazwane: fantom-start pokazuje, że bufor bywa antysygnałem.
- **Symetria ramienia B:** net_akw pod wyrocznią nie wchodzi w hold (track ciągły,
  drop p=0.05 trzyma valid=True — `track_feed.py:93-96`) ⇒ pass-through nietknięty;
  gałąź po-utracie w B martwa (jak skan w AKW). Test §3.1 bez zmian.
- **Oscylacja sektor↔pełny-skan:** przy T_local krótkim i wielokrotnych utratach
  (c01_s01 miał 3) ryzyko pętli sektorowej; wymagałoby licznika prób per utrata
  (1 sektor, potem pełny skan do skutku).

## §R5. Projekt kampanii — wycena dwóch wariantów (gdyby noga szła mimo R3)

- **(i) Pełna powtórka 12×{B, V2} verbatim** (progi PRE_2A zamrożone, Δ_new2
  porównywalne wprost z Δ=12 i Δ=34): ~24+3 booty, 1–2 sesje (~7 h), trzecia
  kampania-wzorzec. Siła: interpretacja progowa zamrożona; słabość: **R3 przewiduje
  Δ_new2 ≈ Δ_new (0/14 konwersji) — kampania potwierdziłaby desk za 27 bootów.**
- **(ii) Sonda celowana** na podzbiorze porażek (np. 3×c08 + c11 ×s01–s04 + kontrola
  2 pass-pary; ~8–10 bootów): tanio falsyfikuje/potwierdza na żywo. **Słabość
  nazwana wprost: bez zamrożonej interpretacji progowej** (podzbiór nielosowy,
  bez pary Δ; wynik tylko mechanizmowy, nie werdyktowy).
- **Rekomendacja:** przy obecnym kształcie dźwigni ŻADNA kampania nie jest
  uzasadniona — desk daje konwersję górną 0/14 (sonda potwierdzałaby zero, pełna
  kampania kosztowałaby 27 bootów na zero). Jeśli CC/Olga przeformułują pozycję
  (patrz niżej), smoke 1 boot na parach-regresjach c08 miałby sens dopiero dla
  NOWEJ dźwigni. Opcje przeformułowania (dane z tego recon): (a) klasa fantom-start
  — 6/9 utrat, wspólny mechanizm, ale dotyka admisji/choreografii benchu (percepcja
  FROZEN; wejście epizodu to artefakt teleportu stagingu — pytanie, czy to w ogóle
  cel programowy); (b) sufit pościgowy v=1.0 (5/14 bez utraty) — poza skanem,
  wymaga zmiany zachowania ŚCIGANIA (sieć/egzekutor — inna liga ryzyka);
  (c) zamknięcie katalogowej pozycji RE-AKW wynikiem recon (śmierć-kierunku na
  desku) — najtańsza uczciwa opcja.

## §R6. Higiena

Nazwa: `REAKW` (env `REAKW_*`, katalog `results/REAKW/`, kontroler `net_reakw`
jeśli powstanie — rejestr additive jak net_akw). Kolizji brak (§0). Sufit bootów
nogi (propozycja do PRE, jeśli powstanie): recon 0 + smoke ≤2 + sonda ≤10 albo
kampania 24+3 ⇒ ≤12 (sonda) / ≤29 (kampania). FREEZE_REAKW: sha wrappera po edycji
+ parametry kierunkowe (sektor, T_local, brama |v|, świeżość bufora) + odziedziczone
FREEZE_AKW/DET verbatim. **NIE wolno dotknąć:** percepcji (det_v2, FeedVision,
MTI, progi admisji), osłony, sieci/wag, rejestru feedów, profilu PEŁNEGO skanu
(step/stare/dwell FROZEN b94cdeae) — zmiana wyłącznie w gałęzi po-utracie wrappera
+ test profilu; pass-through §3.1 musi przejść bez zmian.

## Artefakty

`tools/reakw_recon.py` (vel/dir/man) · `vel_quality.json` · `dir_replay.json` ·
`maneuver.json`. Dalej: **PRE_REAKW numerowany** (decyzja CC/Olga nad opcjami R5;
reguła kalibracyjna ANEKS_AKW-3 §5 ma tu zastosowanie wprost — interakcja była
nazwana-a-niezmierzona, teraz jest ZMIERZONA deskiem: 0/14). Sygnały bez numeru
odrzucam. STOP-REAKWR.
