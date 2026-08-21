# RAPORT_U2R-2 — sesja 2/2: widoczny intruz + box-on-silhouette (ZAMYKA U2R)

Data: 2026-08-22. Zakres: PROMPT_D_U2R-2. **Wynik: SUKCES — intruz wyraźnie widoczny, marker
box-on-silhouette [6].** Roszczenia/plansze §1c/sędzia `79b1e936`/spec/strefa NIETKNIĘTE. v1.0/v3
artefakty NIETKNIĘTE. Budżet U2R zamknięty (2 sesje).

## Diagnoza rozstrzygnięta (znalezisko rdzenia)
Rozjazd markera ciągnący się przez U1R/U2R miał DWIE przyczyny, rozdzielone dopiero teraz:
1. **KONTRAST** (jak wskazała Olga): intruz był mid-tone (szary/pomarańcz washout) → niewidoczny.
2. **BUG KONWENCJI E/N** (właściwa przyczyna 250 px rozjazdu, mylnie przypisana „bladości/divergence" w U1R):
   `intruder_driver.set_pose` używa `gz_x = intr_ned[0]` (East), więc `intr_ned` to **[E, N, −U]**, a nie
   [N, E, D]. `hud_render._enu` zamieniało E/N (poprawne dla DRONA `mav.pos=[N,E,D]`, błędne dla intruza).
   **Fix: `_enu_intr` BEZ zamiany** → rzut = pozycja modelu; box ląduje NA sylwetce.

## [1]/[3] Dźwignie (materiał + kamera) — PREVIEW [2] przed bramką
- (a) `r02/intruder_model.sdf`: materiał **grafit matowy** (diffuse 0.14, ambient 0.10, spec 0.02) →
  ciemna sylwetka (dark-on-bright). Rozmiar ~2.4 m (bez zmian; §1: kątowo wystarcza).
- (b) `worlds/gen_world_demo_v3_1.py` (v3 NIETKNIĘTY): kamera A1 podniesiona (10,−14,8)→**(11,−13,11.5)**,
  aim (5,0,11.2) → ring rzutowany blisko horyzontu (tło skyline/niebo, sylwetka kontrastuje).
- **PREVIEW** (`acts/preview_ring.sh`, spawn intruz na ringu, 1 klatka PRZED bramką): ring proj (825,379)
  na WIDOCZNEJ ciemnej sylwetce — region **min=24** vs niebo 237 = WYSOKI KONTRAST. `results/demo/A1_v3_1/preview_contrast.png`.

## [4] BRAMKA v3.1 — PASS (1. bieg kontrolny, progi byte-identyczne)
| | dwell Δsim/Δwall (≥0.95) | frac<0.5 (=0) | min_rtf | H1 timejump | H2 |
|---|--------------------------:|--------------:|--------:|-------------|----|
| control_1 | **1.0000** | **0.0** | 0.985 | 0 | **PASS** |
Kadr-check [4a]: dron + intruz + akcja w kadrze; **box NA ciemnej sylwetce** (min 24–35 pod boxem).

## [5] PRÓBY — pierwsza ważna, sędzia FROZEN 79b1e936
| akt | próba | JUDGE | HABITAT | world_hash | echa |
|-----|-------|-------|---------|-----------|------|
| **A1** | `results/demo/A1_v3_1/control_1` | **VALID** | VALID | v3.1 | gt_fed, intruder_slaved=True |
| **A3** | `results/demo/rehearsal/A3/v3_1` (reużyta v3) | **VALID** | VALID | v3 | świat A3 niezmieniony (brak intruza) |
control_1 służy jako bramka i pierwsza-ważna próba A1 v3.1 (pełny bieg VALID, ensure_gps, komplet ech).

## [6] HUD box-on-silhouette + 3 klatki sanity
Marker = box „GT-fed track (admitted) · range" (dozwolony: rozjazd ≤0.5 m slaving + naprawa E/N).
3 klatki sanity z boxem NA sylwetce (nie cień-zastępczo), `results/demo/hud_control_v31/`:
- approach/entry: box (846,379) min=35 · OBSERVE-mid: (805,379) min=24 · OBSERVE-late: (820,379) min=33.
16/40 klatek A1 ma box na sylwetce (min<80).

## [7] MONTAŻ — `results/demo/DEMO_B_A1_A3_v3_1.mp4` (+`_h264`)
**109 s** (≥90), 8 faz każda ≥8 s (≥3), sim_t w rogu, kompresje ×N jawne, wyłącznie klatki osądzone.
Cut-lista: A1 patrol 11.7s · approach 8s · ENTRY/REFUSE/OBSERVE 27.8s · land 8s | A3 nominal 12.3s ·
POS_DEGRADED 8s · descent 8s · touchdown 8s. Manifest `_manifest.json` (sha klatek + cut-lista).

## Prowieniencja / rollback
Nowe pliki OBOK v1.0/v3 (nietknięte). Rollback = tag v1.0. Commity niepushnięte (push=Olga).
