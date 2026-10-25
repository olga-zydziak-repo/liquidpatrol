# RECON_PERC2 — recon pozycji PERCEPCJA-II (admisja niezawodna / daleki wzrok) — STOP-PERC2R

CC · 25.10.2026 · wykonanie PROMPT_PERC2_S0. **Zero bootów, zero SITL, zero treningu,
zero edycji istniejących plików**; narzędzia NOWE w `results/PERC2_RECON/tools/`
(perc2_r1 / perc2_r2 / perc2_r3), dane WYŁĄCZNIE z istniejących artefaktów
(36 bootów V2 trzech kampanii DET S4 / AKW S3 / FANTOM S2, zbiory klatek ery DET,
TRANSIT_RECON); FROZEN importowane READ-ONLY (poscig_recon — Episode/manifest;
det_labels **8f7430cd** — etykieta on-target). Czeka decyzja CC: **PRE_PERC2 dla
wybranej ścieżki ALBO aneks odraczający z wyceną**.

**WYNIK GŁÓWNY (uprzedzając szczegóły):**

1. **Anatomia kadencji rozwiązana do liczby:** mody 14.71 / 7.58 / 5.10 Hz to
   k = 1/2/3 ticki sensora pominięte na siatce 15 Hz × fizyka 4 ms (dt_p50 = 0.068 /
   0.132 / 0.196 s = 17/33/49 kroków fizyki; 92–100 % delt na siatce). Sufit =
   `update_rate 15` sensora (mono_cam/model.sdf:64). **Wyborem k steruje stan GPU
   hosta**: jedyny korelat modu w 36 bootach to czas ściennej pracy GPU inferencji
   (push_frame p50 13.3–16.1 ms @SZYBKI/ŚREDNI vs 25.0–27.2 ms @WOLNY, ×1.8 przy
   identycznych wagach), przy rtf 0.995–1.004 i stałych 20 procesach — fizyka,
   transport i liczba procesów WYKLUCZONE pomiarem. **Gwarancja ≥10 Hz leży w lidze
   OPS** (stan GPU hosta + sonda preflight), nie w percepcji (inferencja ma zapas
   2.5–5×) i nie w świecie (zmiana rate = dotyk NIEHASHOWANEGO modelu — §R4).
2. **Model łańcucha admisji ZWALIDOWANY (sanity prereg PASS):** P(run≥3 | n, p̂) DP
   na 7 oknach radialnych ≤5.1 Hz daje E = 3.08 admisji przy obserwowanych 4
   (P(obs=4) = 0.243, masa rozkładu na [2,5] = 99.9 %), a na kotwicy szybkiej
   c08_s01 @14.71 Hz P = 1.0 (p̂ = 0.993, max run 405). Model przewiduje OBA reżimy:
   loterię @5 Hz i pewnik @14 Hz.
3. **Krzywa P(det|Z) poza ~15 m NIE ISTNIEJE w danych:** w 49 330 klatkach in-FOV
   trzech kampanii NIE MA ANI JEDNEJ klatki z celem w kadrze przy dh > 16 m —
   „ściana detekcji" (15? 20? 25 m) jest NIEROZSTRZYGALNA deskiem; to ściana KORPUSU
   EKSPOZYCJI profilu misji, nie zmierzona granica detektora. W 4–15 m detektor NIE
   jest składnikiem ograniczającym (P_on_tgt 0.91–1.00); pas admisji [5,18] rozkłada
   się na: dolne zbocze <4 m = kolaps conf detektora (cel 129–309 px poza korpusem),
   górne zbocze 12–15 m = **MTI gasnące JEDNAKOWO we wszystkich modach** (0.56/0.55/
   0.57 @14 m — składowa rozmiarowa residuum, NIE kadencyjna).
4. **Mechanizm MTI-czołowego zmierzony:** w oknach czołowych @WOLNY ruch pozorny
   środka boxa to p50 13.5–44.6 px/klatkę (p90 20–95 T / 39–271 F) — **p90 przekracza
   próg dopasowania persystencji 64 px** (0.10 znorm., mti.py:40), a klatki mti_F mają
   systematycznie większe skoki niż mti_T; @SZYBKI p50 2.45 px/kl (zapas 7×).
   Intensywność residuum (diff_thr 22) z metadanych NIEMIERZALNA — nazwane.
5. **Rekomendacja: ścieżka (i) OPS-KADENCJA** — najtańsza, zero dotyku zamrożonych,
   usuwa loterię admisji czołowej i (ważniejsze) SPRZĘŻENIE każdej przyszłej kampanii
   ze stanem hosta; pozostałe ścieżki czekają z triggerami (§R6).

## §0. Bramka wejścia — PASS

`git fetch` → origin/master zawiera **c3ea5168 (CO-TRANSIT)** ✓ · `origin/master..HEAD`
puste ✓ · porcelain pełny pusty ✓. FROZEN wykonaniem: **piny 5/5** (k1_shield_pins:
SHIELD FROZEN True; shield 1c584964 · config 4c440e42 · gate_run 5647ae20 · base
7fc45cf2 · safe_descend e3c1040b) · **certy 9/9** (certs_selfcheck PASS). Sha
przeliczone i ZGODNE: fantom_scan **e435ed7e** · rejestr `r03/controllers/__init__.py`
**87203d29** · akw_scan **b94cdeae** · bench_flight `05137098` · bench_judge
`8ec0fcfb` · ncp `0337d5ea` · FREEZE_DET w całości (det_v2.pt **775ead15** ·
det_v2.py e801f7d5 · percep_proc **38a3a765** · feed_vision_proc **79633489** ·
feed_registry **ee1481f9** · feed_vision acc81df7).
**Reguła erratum zastosowana:** odległości dh/Z do krzywych = GT z manifestu
analitycznie; świadek |ned−cmd|_xy>1 m zliczony OBOK na surowym gt_intruder:
**DET 42/123 811 · AKW 40/170 625 · FANTOM 54/171 590 próbek** (wyłącznie brzegi
startów epizodów — tranzient teleportu; ERRATUM_DMIN.md §2).
**Kolizja nazwy „PERC2": BRAK** (zero trafień w kodzie, env, katalogach results).
Rekomendacja: env **`PERC2_*`**, katalog **`results/PERC2/`**, ewentualny nowy feed
jako wpis additive w rejestrze (wzór `_mk_v2`, feed_registry.py:36-53).

## §R1. Anatomia kadencji + model łańcucha admisji

**Tor percepcji (plik:linia):** sensor `imager` 640×480, hfov 1.74 rad, **update_rate
15** — `PX4-Autopilot/Tools/simulation/gz/models/mono_cam/model.sdf:50-64` (model
spawnowany przez PX4: run_boot.sh:102 `MODEL=gz_x500_mono_cam`) → most
`ros_gz_bridge parameter_bridge` (fantomS2_boot.sh:85-86, analogicznie akwS3/detS4)
→ ROS2 BEST_EFFORT depth=1 (percep_proc.py:145-149) → `on_img`: `push_frame` =
inferencja det_v2 + MTI + sample (percep_proc.py:133-141, wall mierzony per klatka
do summary) → datagram UDS → FeedVisionProc (klient ławki).

**Siatka i mody (pomiar, 36 bootów V2 — `r1_kadencja.json`):** fizyka 4 ms
(`real_time_update_rate 250`, world_demo_A3.sdf:10); sensor 15 Hz na siatce 250 Hz
= tick co 16–17 kroków. Zmierzone dt_p50: **0.068 s (14.71 Hz, k=1) · 0.132 s
(7.58 Hz, k=2) · 0.196 s (5.10 Hz, k=3)** = dokładnie 17/33/49 kroków fizyki;
frakcja delt na siatce ticków (±8 ms): 0.92–1.00. Mody per kampania:

| kampania | SZYBKI (k=1) | ŚREDNI (k=2) | WOLNY (k=3) |
|---|---|---|---|
| DET S4 | 6 | 6 | 0 |
| AKW S3 | 2 | 10 | 0 |
| FANTOM S2 | 1 (r1) | 2 (r2–r3) | **9 (r4–r12)** |

**Korelaty (pomiar):** rtf_feed 0.995–1.004 we WSZYSTKICH bootach (fizyka zdrowa,
zero korelacji z modem) · n_proc inwentarza = 20 we wszystkich · e2e klient p50
0.056–0.084 s, p95 0.080–0.112 s (zgodne ze znanym 0.08–0.104; rośnie z modem
WTÓRNIE). **Jedyny silny korelat: push_frame wall p50** — SZYBKI/ŚREDNI 13.3–16.1 ms,
WOLNY **25.0–27.2 ms** (×1.8 na czysto-GPU pracy przy tych samych wagach 775ead15).
Chronologia FANTOM: WOLNY zaczyna się dokładnie od r4 = po restarcie hosta
(RAPORT_FANTOM_S2 §2) — restart wyleczył artefakt próbnika dsim, ale pozostawił
GPU w wolniejszym stanie przez 9 bootów. **Wniosek: sufit modów leży w pliku modelu
sensora (update_rate 15), a wyborem k steruje stan wydajności GPU hosta** (render gz i inferencja
dzielą GPU). Inferencja NIE jest przełykiem (13–27 ms ≪ 68 ms budżetu); transport
NIE jest (latencja stała, bez utraty przepustowości przy depth=1, bo callback 27 ms
< 68 ms); fizyka NIE jest (rtf 1.0). Zastrzeżenie uczciwe: render vs most nie jest
rozstrzygnięte OSTATECZNIE z logów (gz nie loguje rate'u publikacji) — rozstrzyga
sonda ops `gz topic -hz` na żywym stacku (wymaga SITL ⇒ poza tą sesją; do PRE).
Dekompozycja etapów (stemple dostępne): inferencja 13–27 ms (summary) + reszta
toru render→most→kolejka ≈ e2e − push ≈ 30–55 ms.

**Co kosztuje GWARANCJA ≥10 Hz:** 10 Hz leży MIĘDZY modami (k=2 = 7.58 < 10 <
14.71 = k=1) ⇒ gwarancja = utrzymanie k=1. Liga: **OPS/polityka hosta** (stan GPU:
zegary/persistence/kontencja; weryfikowalny preflight „sondą kadencji" przed
uzbrojeniem — narzędzie ops, zero dotyku percepcji; ewentualna bramka modu
w WAŻNOŚCI rundy = zmiana reguły kampanii = wyłącznie decyzja PRE). Dowód
osiągalności na tym hoście: 9/36 bootów historycznych @SZYBKI (DET 6, AKW 2,
FANTOM 1). Liga świata (update_rate 15→N) NIC nie kupuje, póki GPU-wall > ticku,
i dotyka pliku niehashowanego (§R4); liga percepcji — bez roboty (zapas inferencji).

**Model łańcucha admisji (sanity prereg):** ENTRY wymaga k=3 KOLEJNYCH klatek
central∧MTI (config_r02.py:27, target_channel.py:124-127). Model: klatki okna
niezależne z per-klatkowym p̂ zmierzonym w TYM oknie → P(∃ run≥3 w n) przez DP.
Okna-kotwice (TRANSIT §R3; wybór okna = max klatek z boxem przed t_acq+1 s,
dla FAIL przed bliskim przejściem z FROZEN r1_anatomia.json):

| okno | hz | n klatek | p̂(central∧mti) | max run | admisja realna | P_model(run≥3) |
|---|---|---|---|---|---|---|
| c08_s02 PASS | 5.0 | 8 | 0.375 | 3 | TAK (ENTRY 2.33 s) | 0.213 |
| c09_s03 PASS | ~5 | 14 | 1.000 | 14 | TAK | 1.000 |
| c09_s04 PASS | 5.0 | 10 | 0.500 | 5 | TAK | 0.508 |
| c10_s04 PASS | 5.1 | 4 | 1.000 | 4 | TAK | 1.000 |
| c08_s03 FAIL | 5.0 | 6 | 0.500 | 2 | NIE | 0.312 |
| c08_s04 FAIL | 5.1 | 3 | 0.000 | 0 | NIE | 0.000 |
| c10_s02 FAIL | 5.0 | 11 | 0.182 | 1 | NIE | 0.045 |
| **c08_s01 kotwica** | **14.71** | **416** | **0.993** | **405** | TAK | **1.000** |

Sanity: okna wolne obs = **4/7**, model E = **3.08**, P(obs=4) = 0.243, masa [2,5]
= 99.9 % ⇒ zgodny; kotwica szybka P = **1.0** ⇒ zgodny. **Model przewidział oba
reżimy — PASS.** Zastrzeżenie: niezależność per klatka zaniża korelacje seryjne
(run-y klastrują) — model jest dolnym oszacowaniem dyspersji, nazwane.

## §R2. Krzywe P(detekcja|Z) i P(admisja|Z, mod) — `r2_krzywe.json`

Przyrząd: 36 bootów V2 × epizody z `trace.jsonl` (episode_start, wzór erratum_sweep)
→ klatki percep_feed z celem W KADRZE wg etykiety FROZEN det_labels 8f7430cd
(z_max=200 jawnie, by nie ucinać krzywej; dh z manifestu). **49 330 klatek in-FOV.**

| dh [m] | n | P_box | P_on_tgt | conf p50 | P_central∧on | P_mti | P_fresh | P_conj∧on | lab w_px | yolo h_px |
|---|---|---|---|---|---|---|---|---|---|---|
| 0–2 | 53 | 0.72 | 0.57 | 0.017 | 0.47 | 0.28 | 0.23 | 0.23 | 378 | 26 |
| 2–4 | 169 | 0.82 | 0.69 | 0.197 | 0.63 | 0.41 | 0.37 | 0.38 | 268 | 30 |
| 4–6 | 395 | 0.99 | 0.94 | 0.795 | 0.87 | 0.74 | 0.80 | 0.67 | 137 | 28 |
| 6–8 | 11 489 | 1.00 | 1.00 | 0.789 | 0.99 | 0.98 | 0.99 | 0.97 | 90 | 18 |
| 8–10 | 34 853 | 1.00 | 1.00 | 0.790 | 1.00 | 0.99 | 1.00 | 0.99 | 80 | 16 |
| 10–12 | 1 129 | 1.00 | 0.98 | 0.806 | 0.94 | 0.87 | 0.89 | 0.84 | 65 | 13 |
| 12–14 | 596 | 1.00 | 0.95 | 0.771 | 0.83 | 0.78 | 0.71 | 0.68 | 55 | 11 |
| 14–16 | 642 | 0.99 | 0.95 | 0.716 | 0.88 | **0.56** | 0.50 | 0.52 | 49 | 11 |
| **16–30** | **4** | — | — | — | — | — | — | — | — | — |

**(a) Ściana >15 m = KORPUS EKSPOZYCJI, nie detektor:** zero klatek in-FOV przy
dh>16 m w trzech kampaniach (profil misji: zawis na home, perymetr r=15, FOV ±43°) —
pytania „ściana 15/20/25 m?" NIE da się rozstrzygnąć na istniejących klatkach;
każde roszczenie dalekiego wzroku wymaga NOWEJ kolekcji (§R4).
**(b) Detektor nie ogranicza w 4–15 m:** P_on_tgt 0.91–1.00, conf p50 0.72–0.81;
FP tła rzadkie (P_box−P_on_tgt ≤ 0.05).
**(c) Dolne zbocze (kolaps bliski) — drobno (1 m):** P_on_tgt 0.61@2–3 / 0.81@3–4 /
0.91@4–5 / 0.96@5–6 m; conf p50 **0.187–0.197 @2–4 m** = na progu θ_conf 0.1635
(config_r02.py:44) — cel 167–309 px szerokości, poza korpusem treningu (etykiety
5.75–14.9 m); do tego MTI 0.31–0.62. Strefa martwa dh<5 jest ZŁOŻONA
(conf-detektor + MTI + max_area), nie jednoskładnikowa.
**(d) Górne zbocze 12–15 m = MTI, i to NIEZALEŻNIE od kadencji:** P_mti @14–16 m:
SZYBKI 0.564 / ŚREDNI 0.552 / WOLNY 0.565 — składowa rozmiarowa residuum (cel
46–55 px, ruch radialny mały), **podniesienie kadencji NIE podnosi pasa górnego**;
kadencja decyduje o niezawodności ADMISJI (run k=3) W pasie (§R1), nie o zasięgu MTI.
**(e) px vs Z (pod wabiki):** etykieta w_px = 675/Z (zmierzone p50: 80@8.5 m,
46.6@14.5 m); YOLO h_px p50 16@8.5 m, 10@14.5 m.

## §R3. MTI-czołowy — mechanizm i mierzalność — `r3_mti.json`

**Mechanizm (metadane kampanii, okna czołowe-kotwice):** ruch środka boxa [px/klatkę]:

| okno | hz | klatki mti_T: dc p50/p90 [px/kl] | klatki mti_F: dc p50/p90 | w_px p50 |
|---|---|---|---|---|
| c08_s01 | 14.71 | **2.5 / 9.3** (n=413) | 69.5 / 160.8 (n=3) | 80 |
| c08_s02 | 5.0 | 38.7 / 94.9 (n=3) | 40.1 / 270.8 (n=5) | 51–57 |
| c09_s04 | 5.0 | 12.7 / 78.8 (n=5) | 26.7 / 39.6 (n=5) | 72–73 |
| c10_s04 | 5.1 | 20.0 / 20.2 (n=4) | — (n=0) | 133 |
| c08_s03 | 5.0 | 16.6 / 68.7 (n=3) | 44.6 / 65.9 (n=3) | 58–73 |
| c08_s04 | 5.1 | — (n=0) | 13.5 / 38.7 (n=3) | 55 |
| c10_s02 | 5.0 | 14.5 / 54.4 (n=2) | 22.0 / 146.7 (n=7) | 138–148 |

Progi FROZEN (r02/mti.py:28-40): diff_thr=22 · open_k=3 · min_area_px=8 ·
max_area_frac=0.20 · persist 3-z-4 · **persist_move_thr=0.10 znorm. = 64 px** (szer.).
Odczyt: @WOLNY ruch pozorny per klatka jest 5–20× większy niż @SZYBKI (odstęp 0.196
vs 0.068 s + jitter zawisu), **p90 sięga/przekracza próg dopasowania 64 px** —
tożsamość komponentu w oknie persystencji 3-z-4 rwie się losowo; klatki mti_F mają
systematycznie większe skoki niż mti_T w tym samym oknie (5/6 okien z danymi).
@SZYBKI p90 9.3 px = zapas 7× ⇒ pewnik. To mechanizm loterii czołowej zgodny
z modelem §R1. **NIEMIERZALNE z metadanych (nazwane):** intensywność residuum pod
diff_thr=22 i morfologią — wymaga surowych klatek.

**Mierzalność deskiem (tabela):**

| pomiar | desk? | substrat |
|---|---|---|
| ruch pozorny / persystencja vs progi | TAK (wykonane) | percep_feed metadane |
| residuum intensywności / re-run MTI z innymi progami | TYLKO na jpg | `results/DET/collect` + `labels/D*` |
| czołowość @WOLNY na jpg | **NIE** | zbiory DET: kadencje wyłącznie 7.58/14.71 |
| pas górny >14 m na jpg | **NIE** | zbiory DET: Z zdominowane 6–10 m, max ~15 |

Pokrycie zbiorów DET (12 zbiorów, 8 036 jpg): klatek „czołowych" (Z∈[5,18],
|Δśrodek|≤5 px/kl, Z malejące) = 34–99 na zbiór (~770 łącznie), najdłuższe segmenty
**2–6 klatek** — substrat do offline re-runów MTI jest CIENKI (pojedyncze segmenty
k≥3, zero WOLNY, zero >15 m). **Sonda kolekcyjna czołowa (wycena):** ~2–4 booty
driver-kopią detS1_boot (radialne najazdy w siatce dh × kadencja, zapis jpg, bez
sędziego). **Zmiana progów MTI = ERA PERCEPCJI** (FREEZE_PERC2; ewaluacja offline
na korpusie + det_replay **de0feb37** PRZED jakimkolwiek lotem — infrastruktura
istnieje i jest zamrożona w FREEZE_DET).

## §R4. Daleki wzrok — wycena ścieżki detektor-v3

**Sensor (plik:linia):** 640×480, hfov 1.74 rad (= 99.7° = 2·atan(320/270) —
zgodność z intrinsics FROZEN FX=270, r02/mti.py:18-20), update_rate 15 —
`mono_cam/model.sdf:53-64`. Trening det_v2: imgsz **640** = natywna szerokość
(FREEZE_DET: `imgsz=640`) ⇒ **upscale imgsz nic nie kupuje** (zero nowej informacji).
**Rachunek pikselowy** (W=2.5 m, H=0.5 m — kanon pinhole det_labels):
w_px = 675/Z · h_px = 135/Z:

| Z [m] | 15 | 20 | 25 | 30 | 40 |
|---|---|---|---|---|---|
| w_px | 45 | 34 | 27 | 22.5 | 17 |
| h_px | 9.0 | 6.8 | 5.4 | 4.5 | 3.4 |

Korpus det_v2 kończy się na 14.9 m (48 px szer.). **15–25 m (27–45 px szer.) =
osiągalne dla v3 bez zmiany sensora; 30–40 m (3–4.5 px wys.) = granica fizyczna
natywnej rozdzielczości** — tam dźwignią jest dopiero sensor, a to:
**LUKA PROWIENIENCJI (znalezisko):** `mono_cam/model.sdf` jest **GITIGNOROWANY**
(.gitignore:2 `PX4-Autopilot/`) i **POZA world_hash** (harness/world_hash.sh hashuje
wyłącznie `worlds/*.sdf`) — sufit kadencji (rate 15) i rozdzielczość sensora żyją
w pliku bez wersji i bez pinu; dzisiejszy sha256(8) = **3354ae1e**. Zmiana sensora
byłaby dziś NIEWIDOCZNA dla manifestów kampanii. ⇒ FREEZE_PERC2 MUSI pinować
model.sdf; zmiana rozdzielczości dotyka nadto intrinsics FROZEN (FX=270 w mti.py:18
i det_labels) = pełna era percepcji + świata.
**Wycena v3 (bez otwierania):** kolekcja 15–40 m ~**4–6 bootów** (wzór ery DET:
12 bootów → 8 036 klatek; scenariusze kolekcyjne we WŁASNYM pliku driver-kopii —
zero dotyku zamrożonego manifestu/scenarios) → etykiety det_labels (taśma projekcyjna
działa na każdym dystansie; z_max to parametr) → trening v8n ~0.7 h pod nazwą
**det_v3** (receptura FROZEN jako wzór verbatim) → **ewaluacja offline det_replay
+ bramka T (wzór theta_star/T2) — zero lotów do decyzji**; kampania lotna osobną
decyzją po offline.

## §R5. Architektura ery i porównywalność

- **Nowy feed = wpis ADDITIVE w rejestrze** (feed_registry.py:49-53, wzór V→V2:
  `_mk_v3`/`V3`); stare ramię V2 zostaje do porównań A/B; jeden punkt prawdy sha
  wzorem `det_v2.feed_sha_v2()`.
- **Zarys FREEZE_PERC2:** sha wag (det_v3.pt) + toru (kopie, nie edycje: wariant
  mti/percep_proc pod nową nazwą) + narzędzi ewaluacji (det_replay wariant) +
  **PIN `mono_cam/model.sdf` (dziś 3354ae1e)** + world jak dotąd + (ścieżka ops)
  definicja sondy kadencji preflight z progiem per-klatkowym (np. dt_p50 ≤ 0.07 s
  w oknie 30 s — jednostka sprzężona z kadencją JAWNIE per-klatka, reguła
  ANEKS_AKW-1).
- **Ważność kampanii:** dziś mod = telemetria OPISOWA (ANEKS_FANTOM-2; dowód skali:
  całe T6 poleciało @WOLNY w kampanii WAŻNEJ, a FANTOM miał 9/12 bootów WOLNY po
  restarcie hosta — wynik kampanii był sprzężony z losowaniem stanu hosta).
  **Bramka modu w ważności rundy = zmiana reguły kampanii ⇒ wyłącznie decyzją PRE.**
- **Ryzyka:** (1) regresja na 33/40 — KAŻDA zmiana percepcji przechodzi ewaluację
  offline (det_replay na korpusie + re-run okien kotwic §R1/R3) PRZED lotem;
  (2) FP tła przy czulszym MTI — mierzalne offline na jpg (frakcja komponentów poza
  etykietą); (3) porównywalność: nowe ramię = NOWA ERA — stare werdykty literą,
  łańcuch Δ 34→12→7 cytowany ZAWSZE z kwalifikatorem er; (4) symetria B: ramię
  B bez percepcji — nietknięte.

## §R6. Wycena ścieżek + rekomendacja

| ścieżka | booty | dotyka zamrożonych? | co odzyskuje |
|---|---|---|---|
| **(i) OPS-KADENCJA**: polityka hosta GPU + sonda kadencji preflight (narzędzie ops) + ewent. bramka modu (PRE) | desk 0 + **1–2** (sonda stanu) + test celowany T6-geometrie **~6–8**; pełna kampania 24+3 ~27 | **NIC** (percepcja/progi/świat nietknięte; reguła ważności tylko decyzją PRE) | admisja czołowa z loterii→pewnik (c08: 2/6 T6 gwarantowanie; model §R1); **likwiduje sprzężenie KAŻDEJ przyszłej kampanii ze stanem hosta** — warunek rzetelności dalszych er |
| (ii) MTI-czołowy (era progów) | sonda kolekcyjna 2–4 + offline 0 + kampania ~27 | progi MTI FROZEN ⇒ era + FREEZE_PERC2 | czołowość @WOLNY — ale (i) usuwa ją TANIEJ bez ery; pas górny 12–15 m (jedyny unikalny zysk) |
| (iii) detektor-v3 / daleki wzrok | kolekcja 4–6 + trening (0 bootów) + offline 0; kampania osobno | wagi/feed (era additive); >25–30 m wymaga sensora = era świata + intrinsics (POZA skalą — luka 3354ae1e) | krzywa P(det|Z) 15–40 m (dziś NIE istnieje w danych) + substrat wabików |
| (iv) kombinacja | (i) → (iii) na trigger | jw. | (i) jest WARUNKIEM metrologicznym (iii): bez stabilnej kadencji pomiary nowej ery są sprzężone ze stanem hosta |

**Uwaga rachunkowa o TRANSIT:** teoremat sufitu (przegląd perymetru 11.15 s > pas
admisji 10.0 s) jest arytmetyką dwell/slew/stare NIEZALEŻNĄ od kadencji — ścieżka (i)
NIE otwiera ponownie pozycji AKW-TRANSIT (przewidywanie konwersji T6 @k=1: 2–3/6,
c08 z okien wczesnych); zysk (i) to niezawodność admisji w oknach, które SĄ, oraz
metrologia. Pas górny MTI (12–15 m) nie reaguje na kadencję (§R2d) — ścieżka (ii)
bez (i) nie ma uzasadnienia, a po (i) jej unikalny zysk jest wąski.

**Prerejestrowany punkt decyzyjny promptu:** „żadna ścieżka nie mieści się w skali"
NIE zachodzi — ścieżka (i) mieści się z zapasem (wariant minimalny ≤10 bootów).

**REKOMENDACJA:** **PRE_PERC2 w wariancie OPS-KADENCJA (i)** — progi dwuwarstwowe
wzór FANTOM (warstwa narzędziowa: sonda kadencji trzyma k=1 na N bootach; warstwa
pozycji: re-bieg T6-geometrii parowany, predykcje jako wskaźniki; jednostki
per-klatkowe; świadek-filtr w każdym werdykcie; ewaluacja offline przed lotami).
Sufit bootów nogi: **≤32** (sonda 2 + T6 8 + ewent. kampania 24+3 — poniżej
propozycji ≤30–35; wariant minimalny bez kampanii ≤10). Ścieżka (iii) czeka na
trigger (wabiki / roszczenie >15 m) z aktywami tego recon (krzywe, rachunek px,
luka pinu); ścieżka (ii) nie otwierana bez nazwanego celu pasa górnego.
**Czego NIE wolno dotknąć** (każda ścieżka): osłona + piny 5/5, sędzia 8ec0fcfb
(świadek obok), profil II akw_scan b94cdeae, kwarantanna fantom_scan e435ed7e,
wagi net/frozen (ncp 0337d5ea), rejestry poza wpisem additive, manifest scenariuszy
FROZEN; percepcja FROZEN (det_v2/percep_proc/mti) nietykalna w ścieżce (i),
w (ii)/(iii) wyłącznie KOPIE pod nowymi nazwami w nowej erze z FREEZE_PERC2.

## Artefakty

`results/PERC2_RECON/`: **RECON_PERC2.md** (ten plik) · `r1_kadencja.json`
(36 bootów: dt/k-hist/grid/rtf/push/e2e/nproc + model admisji z sanity) ·
`r2_krzywe.json` (49 330 klatek: kosze dh×mod, zbocze 1 m, px-vs-Z, świadek) ·
`r3_mti.json` (okna czołowe: dc/dw px/kl T-vs-F + pokrycie 12 zbiorów DET) ·
`tools/perc2_r1.py` · `tools/perc2_r2.py` · `tools/perc2_r3.py`.
**Zero bootów. Push = Olga.** Po STOP: CC pisze PRE_PERC2 (ścieżka wybrana) ALBO
aneks odraczający z wyceną.
