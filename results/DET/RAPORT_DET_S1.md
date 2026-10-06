# RAPORT_DET_S1 — narzędzia + dolot 12/12 + etykiety korpusu (STOP-DET1)

CC-wykonawca · 06.10.2026 · wykonanie PROMPT_DET_S1 / PRE_DET §2-§3 · commity sesji:
579ff1b (ARCH-1 PRE_DET) → 12d2b59 (narzędzia+FREEZE_DET+T4) → ten (dolot+etykiety+raport).
**Zero treningu** (zgodnie z promptem; wagi bazowe pobrane ≠ trening).

## §0. TL;DR

**Dolot KOMPLET 12/12 VALID za pierwszym podejściem** (pula powtórek 0/2 nietknięta;
P-DET-1 trafia). Korpus nowy: **6 154 pozytywy + 59 negatywów** z 12 komórek, pełna
kadencja ~15 Hz, 0 REFUSE / 0 breach we wszystkich bootach. **Walidacja przyrządu replay
T4: PASS** (p95 31.49 m ∈ [20.45, 81.8]). **Bramka wizualna etykiet: PASS 60/60**
(0 bootów z ≥2/5 rażąco obok; skrining automatyczny całego korpusu: 2/6154 = 0.03%
klatek bez sylwetki w boxie). Frakcja nieba 0.10 % < 5 % ⇒ **kwalifikator „na tle
naziemnym" obowiązuje** (PRE §0). Dataset zbudowany wg splitu FROZEN:
TRAIN 4 344 / VAL 1 095 / TEST 1 275. Czeka ANEKS_DET-1 (zwolnienie treningu S2).

## §1. Bramka §0 + narzędzia (sha w FREEZE_DET)

Bramka: origin 11bf694, ahead pusty, porcelain pełny, piny 5/5, certy 9/9, sha 8/8
zgodne (w tym det_labels **8f7430cd** — FROZEN, zero edycji przez całą sesję).
ARCH-1: PRE_DET.md verbatim w korzeniu (commit 579ff1b).

- **T1 driver zrzutu** `results/DET/tools/detS1_boot.sh` (sha a7313b3c…): baza
  stageA_boot.sh (S2) — różnice wykonane: (1) **JEDYNA zmiana funkcjonalna:**
  `--frames-hz 1000` dla shadow_feed_live.py = zapis KAŻDEJ przetworzonej klatki
  (S2 default 2.0; zero edycji shadow_feed_live/frozen); (2) przeniesione lekcje 2A:
  bridge z czystym PYTHONPATH (lekcja C1 S3), topic MONO deterministyczny, KIND=det
  (czysta metadana), OUTDIR results/DET/collect. Klatki lokalnie przez .git/info/exclude,
  sha zbioru per boot w manifeście.
- **T2** `make_dataset.py` (e958cc48…), **T3** `det_replay.py` (de0feb37…) — opis
  w FREEZE_DET; det_replay = FeedVision acc81df7 TE SAME BAJTY + detektor wstrzykiwany
  (world | .pt nc=1), poza pokładowa z shadow_feed (zero GT w torze), sędziowanie
  po fakcie.
- **FREEZE_DET init:** wagi bazowe pobrane PRZED treningiem (PRE §4):
  yolov8n.pt `f59b3d83…`, yolov8s.pt `1f47a78b…` (assets v8.4.0).

## §2. T4 — walidacja przyrządu replay: **PASS**

Replay S2b-A2b z YOLO-World (9b2c17ab): **err p95 = 31.489 m ∈ [20.45, 81.8]**
(= [0.5×, 2×] × 40.9 lotne) · frakcja top-1-na-celu **10.4 %** — zgodność jakościowa
z lotem (~3–12 %) · admisja strukturalnie żywa (ENTRY 2, FEED_EXPIRE 2, fresh=10
wyłącznie gate=mti). Zastrzeżenie jawne: klatki A2b z S2b są zdecymowane 2 Hz —
walidacja na nich; korpus dolotu jest ~15 Hz (replay S2 będzie wierniejszy niż sama
walidacja). Artefakty: `results/DET/t4_replay_A2b_world.json` (+ .replay.jsonl).

## §3. Dolot — 12/12 VALID (tabela FROZEN PRE §2, kolejność rosnąca)

| boot | scenariusz/ep | V2′ dsw | REFUSE/breach | jpg (15 Hz) | żywość 30 s (≥100) | frames_set_sha8 | rc |
|---|---|---|---|---|---|---|---|
| D01 | c00_s05/48 | 0.9575 | 0/0 | 537 | 176 PASS | b734db94 | 0 |
| D02 | c01_s06/61 | 0.9894 | 0/0 | 650 | 182 PASS | cd63572e | 134* |
| D03 | c02_s07/74 | 0.9979 | 0/0 | 781 | 257 PASS | 3a8e43a8 | 0 |
| D04 | c03_s08/87 | 0.9981 | 0/0 | 544 | 167 PASS | 40d32bf9 | 0 |
| D05 | c04_s09/100 | 0.9888 | 0/0 | 639 | 228 PASS | d4bb0065 | 0 |
| D06 | c05_s10/113 | 0.9893 | 0/0 | 529 | 174 PASS | 959224b8 | 0 |
| D07 | c06_s05/54 | 0.9910 | 0/0 | 949 | 284 PASS | 34bad9ac | 0 |
| D08 | c07_s06/67 | 0.9948 | 0/0 | 555 | 170 PASS | 24cce4f6 | 0 |
| D09 | c08_s07/80 | 0.9967 | 0/0 | 563 | 191 PASS | 78722a7b | 0 |
| D10 | c09_s08/93 | 0.9897 | 0/0 | 756 | 243 PASS | d7aaf483 | 0 |
| D11 | c10_s09/106 | 0.9888 | 0/0 | 784 | 264 PASS | aadc60a0 | 0 |
| D12 | c11_s10/119 | 0.9897 | 0/0 | 749 | 249 PASS | a4606014 | 0 |

Razem **8 036 jpg (~0.9 GB lokalnie)**. Reżim jak 2A: GZ_IP=127.0.0.1, proc_gate,
cooldown ≥300 s, wyłączność; manifesty 1. klasy (net_arm=ncp, weights_sha 0337d5ea,
sha zbioru klatek). *rc=134 D02 = sygnał teardownu (kill bridge'a przez driver po
zakończeniu bootu; finalize i manifest kompletne, V2′ PASS) — kosmetyka, nie odchyłka
ważności. **Pula powtórek: 0/2.**

## §4. Etykiety nowego korpusu (det_labels 8f7430cd, zero edycji; H_REAL=0.5 FROZEN)

| boot | pozytywy | negatywy | F1 no_gt | F2 no_intr_gt | F3 | Z p5/p50/p95/max [m] |
|---|---|---|---|---|---|---|
| D01 | 400 | 6 | 50 | 81 | 6 | 7.3/8.4/9.4/13.9 |
| D02 | 499 | 0 | 55 | 96 | 0 | 7.7/8.2/9.2/14.1 |
| D03 | 579 | 12 | 70 | 120 | 12 | 7.6/8.2/9.1/12.4 |
| D04 | 411 | 2 | 43 | 88 | 2 | 7.5/8.2/8.6/13.1 |
| D05 | 499 | 5 | 53 | 82 | 5 | 7.2/8.4/9.2/13.3 |
| D06 | 420 | 0 | 39 | 70 | 1 | 7.1/8.0/11.1/14.9 |
| D07 | 691 | 8 | 101 | 149 | 8 | 7.3/8.4/9.5/11.6 |
| D08 | 428 | 7 | 46 | 74 | 7 | 7.0/8.6/9.4/12.4 |
| D09 | 435 | 3 | 59 | 66 | 3 | 6.5/8.3/9.8/12.7 |
| D10 | 576 | 0 | 54 | 126 | 2 | 6.5/7.9/10.0/14.9 |
| D11 | 620 | 8 | 55 | 101 | 8 | 6.9/8.3/10.2/10.7 |
| D12 | 596 | 8 | 67 | 78 | 8 | 7.1/9.0/10.0/11.9 |
| **Σ** | **6 154** | **59** | 692 | 1 131 | 62 | łącznie 6.5–14.9 |

(F2 = ogon klatek po oknie gt_intruder — DROP z konstrukcji; F3 dzieli się na
out_of_fov/behind — szczegóły w labels/*/stats.json.)

- **Bramka wizualna (PRE §2): PASS.** 60 PNG (5/boot, `results/DET/labels/*/sample/`)
  obejrzane w całości: 0 bootów z ≥2/5 „rażąco obok" — każda etykieta na sylwetce lub
  w pełnym przekryciu. Obserwacja drobna (nie-bramkowa): box bywa ciasny pionowo
  względem dysku rotorów (prior H_REAL=0.5) — spójne z IoU 0.49–0.60 z recon; bez korekt
  (FROZEN, ANEKS-owalne).
- **Skrining automatyczny całego korpusu** (`results/DET/labels/screen_summary.json`):
  klatki bez ciemnej sylwetki w boxie 2/6154 (0.03 %) — D02 ×1, D10 ×1.
- **Frakcja nieba (klasyfikator pierścienia z recon): 6/6154 = 0.10 % < 5 % ⇒
  kwalifikator „na tle naziemnym" OBOWIĄZUJE** dla zdań bramek (PRE §0). Nota
  jakościowa: wczesne klatki epizodów bywają z celem na jasnym tle przy horyzoncie
  (tam YOLO-World wizualnie trafiał — spójne z lekcją „na tle nieba"); pierścień liczy
  je konserwatywnie do terenu.
- Zasięgi: korpus zdominowany pasmem orbity (p50 ~8.2 m), ogon do 14.9 m z faz
  approach — szerzej niż stary korpus (max 11.7).

## §5. Dataset (T2) — split FROZEN PRE §3

`results/DET/dataset/` (lokalnie, gitignore; manifest COMMITOWANY
`results/DET/dataset_manifest.json`, labels_set_sha256 `33dbebba…`):

| split | komórki | booty | pozytywy | negatywy |
|---|---|---|---|---|
| TRAIN | c00 c01 c03 c05 c07 c08 c10 c11 | 12 (8 dolot + 4 stare 2A) | 4 157 | 187 |
| VAL | c02 c04 | 2 | 1 078 | 17 |
| TEST | c06 c09 | 2 | 1 267 | 8 |

dataset.yaml zawiera WYŁĄCZNIE train+val (TEST poza yaml, PRE §4); komórki TEST w S1
dotknięte wyłącznie zapisem klatek i etykiet (zero ewaluacji — zakaz §5 promptu
dotrzymany). Stary korpus 2A (637→501 rekordów z etykietą) wyłącznie TRAIN.

## §6. FREEZE_DET (stan po S1)

Wagi: yolov8n `f59b3d83…` · yolov8s `1f47a78b…` · worldv2 `9b2c17ab…` (tylko shadow/T4).
Narzędzia: det_labels `8f7430cd…` · det_replay `de0feb37…` · make_dataset `e958cc48…` ·
detS1_boot `a7313b3c…`. Przepis treningu FROZEN (echo PRE §4). Pełny plik:
`results/DET/FREEZE_DET.md`.

## §7. Budżet i status

Dolot **12/12 VALID, pula 0/2** ⇒ noga: 12 bootów lotnych z ≤45. Porcelain przy STOP:
artefakty sesji (collect bez frames/ulg, labels, dataset_manifest, raport). Push = Olga.
Dalej: **ANEKS_DET-1** (werdykt S1, zwolnienie treningu S2 — przepis i split już FROZEN).
STOP.
