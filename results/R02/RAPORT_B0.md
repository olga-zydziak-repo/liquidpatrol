# RAPORT_B0 — bramka wczesna R0.2: pomiar detektora (latencja / Hz / VRAM)

Data: 2026-08-07. Reżim: **budowa, krok B0** (R02-A2 — pomiar detektora ZANIM kod zależny).
Poprzednik: `PRE_R02.md` (ratyfikowane + R02-A1…A4, push wykonany). Kryteria **zamrożone w PRE §4**
przed pomiarem. Artefakty: `results/R02/b0_latency.json`, `results/R02/b0_detector_bench.py`,
`results/R02/b0_install.log`.

## WERDYKT B0: **PASS** (obie osie, z ogromnym zapasem)

| Oś (kryterium §4, dwustronne) | Zmierzone (worst) | Próg | Wynik |
|---|---|---|---|
| **L_det** latencja @1 Hz | **p95 = 22.4 ms** (idle) / 13.2 ms (sim) | PASS ≤800 ms; FAIL >1000 ms | **PASS** (~36× zapas) |
| **VRAM** peak (sim+detektor) | **1583 MiB** | PASS ≤11264; FAIL >12227 | **PASS** (headroom 10.6 GB) |
| RTF symu (raportowany, niebramkujący) | util GPU 8% (sim statyczny) | — | nota: brak stresu |

**Decyzja (A2):** w budżecie → **kontynuować budowę** (aktor, kanał, OBSERVE). Bez fallbacku
(lżejszy model / niższa częstotliwość / rozdzielczość) — nie był potrzebny.

## 1. Konfiguracja pomiaru

- **Sprzęt:** RTX 5070 Ti Laptop, **12 227 MiB VRAM**, driver 577.13, **compute cap 12.0 (sm_120, Blackwell)**, WSL2.
- **Stos ML:** **torch 2.11.0+cu128** (sm_120 wspierane — zweryfikowane: `cuda_available=True`,
  matmul GPU OK), **ultralytics 8.4.115**, opencv 5.0.0. venv `.b0deps` (gitignored).
- **Detektor:** YOLO-World `yolov8s-worldv2.pt` (24.7 MB, pobrane), `set_classes(["drone"])`, imgsz=640, conf=0.001.
- **Klatka:** syntetyczna 320×240 mono→3ch (gradient + blob). N=30 wywołań, warmup 3, kadencja 1 Hz.
- **VRAM:** nvidia-smi (globalny): idle baseline≈0 → after_load = ślad detektora; sim baseline=601 (sam sim) → peak=sim+detektor.

## 2. Wyniki

| Reżim | p95 | med | mean | osiągalny Hz (1-strum.) | VRAM peak | headroom | ślad detektora |
|---|---|---|---|---|---|---|---|
| **idle** (bez symu) | 22.4 ms | 20.5 ms | 20.2 ms | 48.8 | 982 MiB | 11 245 MiB | 982 MiB |
| **sim** (kontencja render↔CUDA) | 13.2 ms | 8.5 ms | 8.9 ms | 117.8 | 1583 MiB | 10 644 MiB | 982 MiB |

- **Latencja detektora ≪ tick 1 Hz** (~36× zapasu do progu; ~75× do sekundy). Nawet szybki kanał
  12 Hz jest latencyjnie wykonalny (p95 13–22 ms < 83 ms/klatkę), gdyby był potrzebny.
- **Ślad VRAM detektora = 982 MiB**; z symem peak 1583 MiB → **headroom 10.6 GB** z 12.

## 3. Interpretacja i zastrzeżenia (uczciwie — trójwynikowo)

1. **Inwersja idle vs sim (sim SZYBSZY) — artefakt zegarów GPU, nie błąd.** W idle GPU schodzi w
   niższy stan zegara między wywołaniami @1 Hz (min 11.9 ms); przy żywym symie GPU trzyma boost
   (min 7.0 ms). Kontencja renderu **nie pogorszyła** latencji inferencji — margines mocy ogromny.
2. **Zakres B0 = latencja/Hz/VRAM detektora, NIE jakość detekcji ani latencja E2E.** Klatka
   syntetyczna: latencja inferencji jest content-niezależna (letterbox do 640, stały koszt).
   **Nie mierzono:** czy detektor łapie intruza (to G1/G2), ani transportu kamera→most→węzeł
   (L_deliver — R3, później). B0 mierzy dokładnie to, co §4 zamroziło jako bramkę wczesną.
3. **Render symu był LEKKI** (scena statyczna, dron na ziemi, util 8%, sim VRAM 601 MiB). Przy locie
   + aktorze-intruzie render wzrośnie — ale headroom (10.6 GB, GPU 8%) absorbuje to z zapasem;
   aktor to lekki model wizualny (kinematyczny). Ryzyko kontencji: **skwantyfikowane jako nieblokujące**.
4. **Prowieniencja hipotezy vs pomiar:** LiquidSight mierzył YOLO-World 63 ms @1 Hz na INNYM sprzęcie
   (`RAPORT_S3B1:103`). Tu **zmierzone od nowa na TYM sprzęcie** — 13–22 ms p95, szybciej (nowszy GPU
   + cu128). Liczba LiquidSight nieprzeniesiona (spójne z „liczby się nie przenoszą").

## 4. Higiena / stan

- Stack postawiony (`run_stack.sh`, MODEL=gz_x500_mono_cam) i **posprzątany** — 0 procesów sim, VRAM=0 po teardown.
- Znalezisko operacyjne (odnotowane): `run_stack.sh > $LOGDIR/log` wymaga wcześniejszego `mkdir -p $LOGDIR`
  (powłoka tworzy plik przekierowania PRZED `mkdir` w skrypcie) — inaczej redirect pada exit 1.
- venv `.b0deps` + wagi `.b0deps/weights/` gitignored; artefakty pomiaru w `results/R02/` (wersjonowane).

## 5. Następny krok (po decyzji)

B0 PASS → wolne dependent-code R0.2: aktor-intruz kinematyczny (R1) → węzeł detektora + kanał 5-dim
ZOH-age BEZ conf (R3/A1) → OBSERVE w osłonie + re-cert (R4/§5, pierwszy krok: `certs_selfcheck`).
Kadencja detektora **1 Hz** potwierdzona jako z ogromnym zapasem; rozdzielczość kamery 320×240
(< sufit mostu 256 KB) bez zmian.
