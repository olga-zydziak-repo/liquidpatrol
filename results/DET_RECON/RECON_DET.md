# RECON_DET — recon nogi DET (detektor-v2): etykiety z GT, ratunek YOLO, plan treningu

CC · 06.10.2026 · wykonanie PROMPT_DET_S0. Zero bootów, zero SITL, zero treningu;
nowe pliki wyłącznie `results/DET_RECON/**`. Narzędzia: `tools/det_labels.py`,
`tools/det_sweep.py`, `tools/det_mti_derot.py`. Czeka PRE_DET (numerowany).

## §0. Bramka wejścia — PASS

origin/master zawiera 40ccbdc (CO-2A), `origin/master..HEAD` puste na starcie, porcelain
pełny. FROZEN wykonaniem: **piny 5/5** (k1_shield_pins: SHIELD FROZEN True), **certy 9/9**
(certs_selfcheck PASS), sha kluczowe zgodne: bench_judge `8ec0fcfb`, features `9adc1505`,
ncp FREEZE `0337d5ea`, yolo `9b2c17ab`, feed_vision `acc81df7`, bench_flight `05137098`,
percep_judge `363c37b7`. **Kolizja nazwy „DET": BRAK** — żaden katalog/łańcuch/aneks nie
używa „DET" jako nogi; sąsiedzi leksykalni to `det_hz`/`DETHZ` (parametr kadencji
detektora w driverach 2A) i `r02/detector_node.py` — grep-odróżnialne; rekomendacja do
PRE: prefiks env `DETV2_`, katalog `results/DET/`.

## §R1. Inwentarz surowca (klatki LOKALNE, gitignore przez .git/info/exclude)

| boot | scenariusz | jpg | quat gt | gt_intruder | shadow_feed (14.7 Hz) | sha zbioru vs manifest |
|---|---|---|---|---|---|---|
| S2 A1_c08_s03_r4 | c08_s03 | 165 | TAK | TAK | 1284 wierszy (973 z boxem) | **ZGODNY** d683a1fd |
| S2 A2_c11_s01 | c11_s01 | 146 | TAK | TAK | 540 (413) | **ZGODNY** 419f5e43 |
| S2b A1b_c08_s03 | c08_s03 | 152 | TAK | TAK | 687 (560) | **ZGODNY** e7e88a98 |
| S2b A2b_c11_s01 | c11_s01 | 174 | TAK | TAK | 1358 (1183) | **ZGODNY** 30181c2c |

Razem **637 jpg 640×480 mono** (kamera pokładowa STOCK), komplet {klatki+gt_intruder+gt
własne+quat} w 4/4 (quat od edycji D5 — wszystkie booty S2+). **Zapis klatek jest
ZDECYMOWANY: dt p50 = 0.528 s (~2 Hz)** vs shadow_feed pełne 14.7 Hz — konsekwencje w R3/R6.
Booty sondy C1/C1r/C2: quat+GT są, **jpg = 0** (FEED=V in-process nie zapisuje klatek).
Inne ery: r02 `C1_provenance` 25×npy 480×640×3 (pokładowa, tło-niebo, BEZ zsynchronizowanego
GT per klatka — nieużyteczne do etykiet); ery demo/DEMO_V3 ~6.3k npy **1280×720 = kamera
FILMOWA świata, nie pokładowa — POZA powierzchnią treningu**.

## §R2. Pipeline etykiet z GT — ZBUDOWANY i ZWALIDOWANY

`tools/det_labels.py`: GT intruza (NED APPLIED) + poza własna GT (trace t:"gt" ENU+quat
POZY GZ) + projekcja **1:1 z kanonu** `results/2A/tools/coverage_real.py`
(R_ned←frd = M(ned←enu)·R(enu←body_gz)·M(body_gz←frd); pinhole f_px=270; offset FRD
(0.12,−0.03,−0.242)) ⇒ box: w_px=FX·2.5/Z (kanon W_real), h_px=FX·**0.5**/Z (prior pionu
z wizualiów intruder_model.sdf: korpus 0.32 + rotory ~0.2 — WALIDOWANY niżej).

**Filtry (zliczone, nie ciche):** F1 brak gt ±0.06 s → DROP (58 klatek/637); F2 poza
zakresem gt_intruder → DROP (78 — intruz w pozycji nieznanej, klatka NIE jest bezpiecznym
negatywem); F3 za plecami/poza FOV → NEGATYW pusta etykieta (153); F4 Z>60 m → 0.
**Wynik: 348 pozytywów + 153 negatywy** (labels/ format YOLO + meta.jsonl + stats.json).
Zasięgi pozytywów: **Z p5/p50/p95 = 6.1/7.9/9.6 m, max 11.7** — korpus to niemal wyłącznie
pasmo orbity (konsekwencja dla splitu, R6).

**Walidacja (a) — IoU etykieta↔YOLO na wierszach shadow_feed (pełna kadencja, nie tylko jpg):**

| boot | n box YOLO | z etykietą OK | YOLO na celu | IoU p50 (na celu) |
|---|---|---|---|---|
| A1_r4 (S2) | 973 | 354 | 25 (7.1%) | 0.186 |
| A2 (S2) | 413 | 142 | 3 (2.1%) | 0.153 |
| A1b (S2b) | 560 | 480 | 4 (0.8%) | **0.603** |
| A2b (S2b) | 1183 | 967 | 71 (7.3%) | **0.485** (p90 0.637) |

Frakcje „na celu" odtwarzają znaną historię S2b (top-1 poza celem ~88–97%) — spójność
niezależna. IoU 0.49–0.60 na głównej próbie (S2b, n=75) = etykieta geometryczna trafia
w sylwetkę; niskie IoU na S2 (n=28) to boxy YOLO łapiące fragmenty (rotory) przy
zdegenerowanej geometrii sprzed N1 — nie podważa pipeline'u.
**Walidacja (b):** 20 PNG (5/boot, `labels/*/sample/`) — wizualnie etykieta siedzi na
sylwetce intruza (w próbce A2b YOLO-na-celu niemal pokrywa etykietę; w próbce A1 YOLO
obok — klasyka). W kadrach widoczny też CIEŃ własny drona (→ R8).

## §R3. Baseline-C — ratunek YOLO tanio: **NIE ISTNIEJE w przebadanej przestrzeni**

Sweep na 348 klatkach z etykietą (`tools/det_sweep.py`, top-1 = argmax conf, „na celu" =
środek w boxie etykiety). **Tło: klasyfikator per-klatka (pierścień wokół etykiety,
mean>190∧std<14 ⇒ niebo) dał 348/348 TEREN — wiersz „tło-niebo" jest w tym korpusie
NIEOBSADZONY** (lekcja „na tle nieba trafiał" zostaje jakościowa z S2/r02; r02 25 klatek
nieba nie ma GT).

| wariant | top1_on [%] | any_on [%] | conf_on p50 | conf_top1_off p50 | ms/klatkę |
|---|---|---|---|---|---|
| P1 ["drone"]@640 (kanon) | 5.5 | 13.8 | 0.0021 | 0.0068 | 17.1 |
| P2 ["quadcopter"]@640 | 3.2 | 5.2 | 0.0032 | 0.0029 | 11.1 |
| P3 ["drone","quadcopter","uav"]@640 | 6.9 | 25.0 | 0.0023 | 0.0104 | 11.9 |
| P4 ["small dark quadcopter drone flying"]@640 | 3.7 | 21.0 | 0.0021 | 0.0166 | 12.7 |
| P5 ["aircraft"]@640 | 4.6 | 42.2 | 0.0028 | **0.0882** | 16.8 |
| P1@960 / P1@1280 | 4.0 / 6.9 | 7.8 / 10.6 | — | — | 13.2 / 16.2 |
| P3@960 / **P3@1280 (najlepszy)** | 7.5 / **10.3** | 14.9 / 19.3 | 0.0020 | 0.0038 | 16.4 |

**Werdykt WPROST: żaden wariant nie zbliża się do progu 80% na terenie — maksimum 10.3%
(P3@1280).** Separator conf nie istnieje (conf_on p50 0.002 ≤ conf_off; P5 ma any_on 42%,
ale strzela wysokim conf w budynki — separator odwrotny). Tabela progu θ (P3@1280):
θ=0.005 → TP-frames 7.2% przy FP-frames 27.9%; θ=0.1 → TP 0.3%. **Kształt nogi = trening,
alternatywy promptowe zamknięte danymi.**

**Derotacja przed MTI (`tools/det_mti_derot.py`):** na 40 kolejnych parach A2b (orbita
~20°/s; UWAGA: dt par 0.528 s przez decymację zapisu — górne oszacowanie, nie replay):
mean|diff| tła 17.69 → 8.00 po derotacji (**redukcja 54.8%**) ⇒ człon rotacyjny
H=K·R·K⁻¹ DZIAŁA. Rezyduum to **paralaksa translacyjna** (orbita ~3 m/s; przy locie
1/15 s i klatterze w ~10–15 m przesunięcie ~3–5 px/klatkę > sub-piksel — krawędzie
klatteru migoczą nad diff_thr=22), czego derotacja ROTACYJNA nie usuwa Z KONSTRUKCJI —
zgodne z D1 nogi D („rezyduum translacji derotacji, nie nullowanie"). **Parametry
MTIParams nie ratują koincydencji pod orbitą; wierny test pełnej kadencji wymaga zrzutu
klatek 15 Hz (R6).**

## §R4. Kandydaci treningu

Stack: `.b0deps` ultralytics **8.4.115** + torch **2.11.0+cu128**, RTX 5070 Ti Laptop
**11.9 GB**. Pomiary inferencji @640 (50 klatek, cuda):
**v8s-worldv2 7.37 ms · v8n 6.20 ms · v8s 8.94 ms** (v8n 3.15 M / v8s 11.16 M param).
- **Ścieżka główna: fine-tune yolov8n/s jednoklasowo** („intruder") na etykietach R2.
  Szacunek czasu: 1–3k obrazów, 100 epok, batch 16 @640 ⇒ **v8n <1 h, v8s ~1–2 h** na tym
  GPU (dataloader-bound). Bazowe wagi yolov8n/s.pt **NIE są lokalnie** (jest tylko
  worldv2) — pobranie ~6/22 MB do ratyfikacji w PRE (zmiana inwentarza wag) ALBO
  fine-tune samego worldv2 (ultralytics wspiera; zostaje tor tekstowy — zbędny w locie).
- **Licencja: ultralytics = AGPL-3.0** (dotyczy też obecnego toru YOLO-World w 2A) — DO
  ODNOTOWANIA W PRE; dla SITL-badań bez dystrybucji binarnej ryzyko praktyczne niskie,
  ale decyzja jawna.
- **Alternatywa minimalna (gdyby AGPL/rozmiar przeszkadzał):** torchvision (BSD, jest
  w .b0deps) — SSDlite320-MobileNetV3 albo RetinaNet, trening własnym skryptem torch;
  koszt budowy większy (brak gotowej pętli), inferencja porównywalna; backbone pretrained
  też wymaga pobrania.

## §R5. Kontencja runtime (próg ~8 Hz in-process z 2A)

Zmierzone składowe toru per klatka: YOLO 7.4 ms + MTI **1.45 ms** + konwersja ≈ **~9–10 ms**,
a w locie S4 cykl przetwarzania wyniósł ~140–150 ms (6.7–7.2 Hz) ⇒ **gardłem nie jest
obliczenie, tylko kontencja GIL/egzekutora** z pętlą 20 Hz + mavsdk-grpc + logowaniem.
- (a) **szybszy model (v8n): zysk ~1.2 ms/klatkę — MARGINALNY** wobec ~130 ms kontencji.
- (b) **decymacja pos/att 100→20 Hz:** odciąża jednowątkowy egzekutor feedu (dziś pos+att
  oferują ~200 cb/s vs obraz 15; depth-1 dropuje, ale każdy obsłużony cb kosztuje slot
  pętli spin); zysk częściowy — NIE usuwa GIL-u z procesem sterowania. Desk-szacunek:
  odzysk rzędu dziesiątek ms/s, nie 130 ms/klatkę.
- (c) **osobny proces percepcji (projekt, bez budowy):** detektor+MTI+kanał w procesie
  potomnym (wzór r02/detector_node + shadow_feed_live S2 — oba już istniały); IPC:
  publikacja tracku na topic ROS2 (albo UDS/jsonl jak shadow-log) do cienkiego
  klienta-feedu w bench_flight. Budżet latencji: klatka 66 ms + inferencja 9 ms +
  IPC <5 ms ⇒ **p95 ≪ 0.25 s** (S2 shadow mierzył E2E 0.044–0.052 s w osobnym procesie —
  DOWÓD WYKONANIEM z 2A, że wariant (c) trzyma koperty). REKOMENDACJA do PRE: (c).

## §R6. Split uczciwości i dolot klatek

Dziś: **2/120 scenariuszy = 2/12 komórek (c08, c11), po 1 ziarnie; 348 pozytywów; 100%
teren; Z 6–10 m (orbita)** — split per komórka/ziarno NIEWYKONALNY (test=train geometrią),
zasięgowo zdegenerowany, nieba brak. **Dolot (szadow, bezpieczny — lot na FEED=B jak S2):**
- **12 bootów × 1 epizod: po 1 komórce c00–c11, ziarna rotowane** (żaden boot nie
  powtarza pary komórka×ziarno z korpusu 2A), zrzut klatek **PEŁNEJ kadencji 15 Hz**
  (usunięcie decymacji w driverze-narzędziu; odblokowuje też wierny replay MTI z R3).
- Wydajność: ~70–110 s epizodu ⇒ ~1.0–1.6k klatek/boot ≈ 25–35 MB lokalnie (gitignore,
  sha zbioru do manifestu jak S2); 12 bootów ⇒ **~12–18k klatek, ~0.4 GB, ~2.2 h**
  (6 min boot + 5 min cooldown), 1 sesja lotna. Minimum sensowne: 6 bootów (co druga
  komórka) ⇒ split 4+1+1 komórek, słabszy.
- Split proponowany do PRE: train 8 komórek / val 2 / test 2 (held-out KOMÓRKI, nie
  klatki), negatywy z F3 w treningu; bramka B liczona wyłącznie na komórkach testowych.

## §R7. Kosztorys nogi (booty/sesje)

| pozycja | booty | uwagi |
|---|---|---|
| dolot klatek (R6) | 6–12 | 1 sesja, SHADOW FEED=B |
| trening + ewaluacja offline | 0 | <2 h GPU; bramka B = sędzia 363c37b7 + progi PRE_2A verbatim na shadow-logach dolotu/istniejących |
| smoke LIVE detektora-v2 (1 boot FEED=V, żywość ANEKS_2A-3 §4) | 1–2 | przed kampanią |
| kampania C z PRE_2A (12 rund × {B,V}, ZAMROŻONA, nielatana) | 24 | werdykt Δ wg PRE_2A |
| zapas na INVALID/env | 3 | reżim powtórek jak 2A |
| **RAZEM** | **34–41** | **3–4 sesje lotne** |

## §R8. Higiena i ryzyka

- **Dysk:** 719 G wolne (korpus dolotu ~0.4 G — pomijalne). **Wersje:** torch 2.11.0+cu128,
  ultralytics 8.4.115, numpy 2.4.4 (B0SP) / 1.26.4 (system), GPU 11.9 GB.
- **Nazwa:** „DET" wolna (§0); env prefiks `DETV2_`.
- **Tryby porażki etykiet z projekcji (znane, do PRE):**
  1. **OKLUZJA** dekoracjami (budynki/drzewa między kamerą a celem) — projekcja NIE testuje
     widoczności; w próbce 20 PNG okluzji nie widać, ale frakcja nieznana (brak kanału
     głębi offline). Mitygacja do PRE: spot-check wizualny próbki per boot dolotu +
     odrzut klatek-outlierów (np. trening z label smoothing / IoU-sanity na podzbiorze).
  2. **Krawędź kadru** — obsłużone (clip + próg 2 px), zliczane.
  3. **Tranzient teleportu intruza** (SETPOSE 16.7 Hz, APPLIED vs render ±33 ms przy
     ~3 m/s ⇒ ~0.1 m ≈ 3 px) — mały, w szumie etykiety.
  4. **Cień własny drona** w kadrze (widoczny w próbkach) — naturalny dystraktor; zostaje
     w danych (uczciwe), odnotować w PRE.
  5. **Prior H_REAL=0.5 m** — IoU 0.49–0.60 z boxami YOLO-na-celu wystarczające na recon;
     PRE może zamrozić korektę po pierwszej walidacji na dolocie.
  6. **Korpus bez nieba** — po dolocie sprawdzić frakcję nieba; jeśli nadal ~0, zdanie
     bramki B ograniczone do tła naziemnego (jawnie w PRE).
- **Ryzyko licencyjne:** AGPL ultralytics (R4) — decyzja w PRE.
- **Decymacja zapisu klatek 2 Hz w driverze S2** — przy dolocie zrzut pełnej kadencji
  (zmiana w NARZĘDZIU-driverze, nie w frozen).

## STOP-DETR

Commit: RECON + `tools/` (det_labels, det_sweep, det_mti_derot) + etykiety/meta/stats +
sweep_results + 20 PNG próbki. Push = Olga („wypchnięte" wystarczy). Czeka **PRE_DET**
(numerowany; zamrozi: dane+split, architekturę, tor treningu z seedem, bramki B verbatim
z PRE_2A + próg in-process, kampanię C, śmierć kierunku, budżet). STOP.
