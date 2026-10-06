# RAPORT_DET_S2 — trening v8n + bramka T: T2 PASS na TEST (1.365 m ≤ 3.0) — STOP-DET2

CC-wykonawca · 06.10.2026 · wykonanie ANEKS_DET-1 §4 (zero bootów, GPU) · commity sesji:
9a838eb (ARCH-1 ANEKS_DET-1) → ten (trening+bramka+raport).

## §0. TL;DR

**Fine-tune yolov8n na etykietach projekcyjnych NAPRAWIA ogniwo wskazane przez 2A.**
Jedno przejście TEST na held-out komórkach c06+c09: **T2 err p95 pooled = 1.365 m ≤ 3.0
⇒ PASS — kampania C ODBLOKOWANA** (warunek 1/2; drugi = smoke S3). T1 top-1-na-celu
**100.0 % / 99.8 %** (próg opisowy 80 % — kontrast z 3–12 % YOLO-World w locie 2A
i 10.3 % maksimum sweepa recon). Eskalacja v8s NIE zaszła (VAL p95 0.725/0.778 ≪ 3.0);
jeden run, seed 1, zero fallbacków OOM. Model finalny: `net/frozen/det_v2.pt`
sha `775ead15…`. Błąd toru percepcji na niewidzianych komórkach ≈ poziom referencji
FeedB (1.258 m p95). P-DET-2 ✓ i P-DET-3 ✓ (formalnie przy zamknięciu).

## §1. Bramka §4.1 + ARCH-1

origin aab2e6f, ahead pusty, porcelain pełny; piny 5/5, certy 9/9; det_labels 8f7430cd,
det_replay de0feb37, wagi bazowe f59b3d83/1f47a78b; **re-hash zbioru etykiet przed
treningiem: 33dbebba ZGODNY (6 714 rekordów)**. ARCH-1: ANEKS_DET-1.md verbatim
w korzeniu (commit 9a838eb).

## §2. Trening v8n (przepis FROZEN, bez odstępstw)

`model=yolov8n.pt(f59b3d83) data=dataset.yaml(nc=1) epochs=100 imgsz=640 batch=16
seed=1 deterministic=True device=0 workers=4 patience=30 cache=False`, reszta = domyślne
ultralytics 8.4.115. Przebieg: **99 epok, EarlyStopping (brak poprawy 30 epok), best
@69, 0.733 h wall na RTX 5070 Ti, fallbacków OOM: 0.** Metryki detekcyjne best na VAL
(informacyjne): P 0.985 · R 0.985 · mAP50 0.980 · mAP50-95 0.717. Podsumowanie liczbowe:
`results/DET/train_v8n_summary.json` + `train_v8n_results.csv` (katalog runs/ poza repo).

## §3. Replay VAL per komórka (det_replay de0feb37, rzeczywiste dt) + decyzja eskalacji

| komórka/boot | kadencja (§2a aneksu) | err fresh vs GT p50/p95/max [m] (n) | T1 na-celu | admisja |
|---|---|---|---|---|
| c02 / D03 | pełna 14.7 Hz | 0.579 / **0.725** / 0.880 (575) | 99.7 % (577/579) | ENTRY 1, FEED_EXPIRE 1, fresh 582 (mti 559 / window 23) |
| c04 / D05 | połówkowa 7.6 Hz | 0.536 / **0.778** / 0.884 (492) | 100.0 % (499/499) | ENTRY 1, fresh 622 (mti 593 / window 29) |

**Decyzja eskalacji (ANEKS §4.4): VAL err p95 = 0.725/0.778 ≤ 3.0 ⇒ eskalacja v8s NIE
URUCHOMIONA.** Model finalny = v8n (jeden run). Nota kadencji D05: bias konserwatywny
(k=3 wolniejsze) — mimo to 100 % na-celu; bez wpływu na decyzję.

**θ\* (opisowy, wybrany na VAL — do runtime NIE wchodzi):** rozkłady conf na VAL:
on-target n=1076 p01=0.744 p50=0.792; off-target n=2 (max 0.805 — jeden box tła
z wysokim conf, pełnej separacji brak) ⇒ θ\*=0.372 (p01/2; `theta_star_val.json`).

## §4. TEST — JEDNO przejście (c06+c09, model finalny v8n)

| komórka/boot | kadencja | err fresh vs GT p50/p95/max [m] (n) | T1 na-celu | admisja |
|---|---|---|---|---|
| c06 / D07 | pełna 14.7 Hz | 1.234 / **1.388** / 1.602 (686) | **100.0 %** (691/691) | ENTRY 1, FEED_EXPIRE 1, fresh 696 (mti 688 / window 8) |
| c09 / D10 | pełna 14.7 Hz | 1.202 / **1.344** / 1.843 (576) | **99.8 %** (575/576) | ENTRY 1, FEED_EXPIRE 1, fresh 583 (mti 560 / window 23) |

**T2 (nośnik werdyktu), pooled na 1 262 próbkach świeżych: p50 1.218 / p95 1.365 /
max 1.843 m ⇒ p95 1.365 ≤ 3.0 — PASS** (`T2_test_pooled.json`). Oba booty TEST pełnej
kadencji (ANEKS §2a — bramka na czystym materiale). **T1 ≥ 80 %: PASS z sufitem.**
**θ\*=0.372 raportowany na TEST: TP 1 266/1 267 klatek FOV (99.9 %), FP 1 (0.08 %).**
Po TEST zero dalszych treningów/ewaluacji (zakaz dotrzymany; TEST dotknięty dokładnie
RAZ w całej nodze).

Nota uczciwa: err rośnie VAL→TEST (p95 0.73–0.78 → 1.34–1.39) — realna luka
generalizacji między komórkami; wielokrotnie poniżej progu i na poziomie referencji
FeedB (1.258). Kwalifikator PRE §0 obowiązuje: wynik „na tle naziemnym" (niebo 0.10 %
korpusu), SITL, ta sama scena/symulator, komórki held-out, scenariusze kampanii
rozłączne ze zbiorem treningowym.

## §5. Artefakty i FREEZE_DET

`net/frozen/det_v2.pt` = best.pt v8n seed1, sha256
`775ead150b9937453168538cb97c55f69166e27ddc2d93f71b3710e0e49832ce` → FREEZE_DET
(wiersz FINALNY). Replaye: `replay_val_v8n_*.json(+.replay.jsonl)` ×2,
`replay_TEST_v8n_*.json(+.replay.jsonl)` ×2, `T2_test_pooled.json`,
`theta_star_val.json`, podsumowanie treningu ×2 pliki.

## §6. Budżet i status

S2 = 0 bootów (noga: 12 z ≤45 bez zmian). Porcelain przy STOP: artefakty S2 + ten
raport. Nota higieniczna: AMP-check ultralytics auto-pobrał `yolo26n.pt` do CWD
(artefakt diagnostyczny trenera, nie uczestniczy w wagach) — plik USUNIĘTY, nie wchodzi
do inwentarza. Push = Olga. Dalej: **ANEKS_DET-2** (werdykt bramki T; przy PASS — zwolnienie
budowy FEED=V2 i smoke S3 per PRE §6). STOP.
