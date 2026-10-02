# RAPORT_LIQ_S1 — trening kontroli, bramka offline, FREEZE_LIQ (zero bootów) → STOP-LIQ1

LiquidPatrol · CC · 02.10.2026 · PROMPT_LIQ_S1 · PRE_LIQ ratyfikowany (ARCH-1 w tym S1).
Sesja bez SITL: zero bootów, zero dotykania światów/harnessu/sędziów/osłony.

## §0. Bramka wejścia i FROZEN (wykonaniem)
origin/master = `b4f0225` ✓, ahead pusty ✓, porcelain pusty ✓. ARCH-1: `PRE_LIQ.md` skopiowany
VERBATIM (sha256 obu kopii `9e7eb36f22be8773…` — byte-identyczne), **pierwszy commit sesji**.
Piny 5/5 (check_shield_frozen=True) · certy 9/9 (certs_selfcheck PASS) · sha 4/4 (bench_judge
8ec0fcfb, features 9adc1505, ncp.npz 0337d5ea, mlp.npz 1d190023). Nazwa launchera sondy:
PRE §7 mówi `w_launcher_stock.sh`, prompt §0.4 ujednolica do LIQ ⇒ `tools/liq_launcher_stock.sh`
(mapowanie jawne, litera promptu późniejsza i wprost o nazwach).

## §1. ECHO-FREEZE (przed pierwszą epoką; po tym echu nic nie drgnęło)
**(a) net/train_config.json VERBATIM:**
```
{"vmax": 3.0,
 "ncp": {"hidden": 20, "bb": 20, "lr": 0.003, "epochs": 1000, "seed": 1, "grad_clip": 5.0,
          "beta1": 0.9, "beta2": 0.999, "lr_schedule": {"milestones": [500, 800], "gamma": 0.5}},
 "mlp": {"hidden": 32, "k": 5, "lr": 0.001, "batch": 512, "epochs": 80, "seed": 1,
          "grad_clip": 5.0, "beta1": 0.9, "beta2": 0.999}}
```
Mapowanie per ramię (literalne z promptu §1(a), zero pozycji niejednoznacznych po tej regule):
| pole | GRU h=21 | MLP k=20 h=11 | źródło |
|------|----------|----------------|--------|
| lr / epochs(cap) / grad_clip / β1β2 / lr_schedule / seed | 0.003 / 1000 / 5.0 / 0.9,0.999 / [500,800]×0.5 / 1 | identycznie | gałąź ncp (komplet) |
| batch | — (tor sekwencyjny, full-batch jak train_ncp) | 512 | FORMAT toru okiennego, gałąź mlp |
| architektura | hidden 21 | k=20, hidden 11 | PRE §1 (budżet ±5%) |
Nota jawna: literalne mapowanie daje MLP-k20 lr 0.003 i cap 1000 (≠ historyczne mlp 0.001/80) —
to wybór litery promptu („to samo" = komplet ncp; batch jako jedyny FORMAT), echo przed treningiem.
**(b) Próg bramki offline VERBATIM:** G13′ = ANEKS_NET-1 §2 (results/NET/MAPA_KRYTERIOW_S2.md:10):
„**BRAMKA N3(i) = PER ROLLOUT ≥ 20/24** — analog-D6 (wejście≤25s ∧ frac≥0.85 ∧ d_min≥4) w ≥20/24
rolloutów (komórka×ziarno TEST 4,8); widoki per-komórka (oba/którekolwiek) raportowane opisowo
(zastępuje S1 «oba ziarna»)". Przyrząd: net/rollout_eval.py (model punktowy FEED-B, seed FeedB =
ziarno scenariusza); sanity wyroczni w tej sesji: **12/12** (reprodukcja buildu ławki).
**(c) Split WYKONANIEM** (resolve_first_valid, ta sesja): 114 D6 → **TRAIN 81 / VAL 10 / TEST 23** ✓.
**(d) Środowisko:** numpy **1.26.4** (oczekiwane ✓), Python 3.12.3.

## §2. Trening (wyłącznie seed 1 lata; results/LIQ/train/)
Nowe pliki toru: `net/models_liq.py` (GRU21: wariant combined-input [x,h], 1 bias/bramkę,
n=tanh([x, r·h]Wn+bn), głowa tanh·vmax jak NCP; MLPk20: TinyMLP z K=20/h=11, własny save/load)
+ `net/train_liq.py` (wrapper; importy z net/train.py/dataset.py/rollout_eval.py — **zero edycji
istniejących plików toru**). **Dowód poprawności BPTT GRU: gradient-check numeryczny max błąd
względny 4.14e-07.** Parametry z count_params na ZAPISANYCH wagach: **GRU 1956 · MLP-k20 1939**
(oczekiwane trafione co do sztuki; NCP 1903).

| ramię | best_val (epoka) | final train/val | wall-time | nota |
|-------|------------------|-----------------|-----------|------|
| GRU h=21 | **0.04901 @999** | 0.04635 / 0.04901 | **397.3 s** | val malał do capu 1000 — WYNIK (zero strojenia; cap=prawo z ANEKS_NET-1 §3.1 przyznane z góry) |
| MLP k=20 h=11 | **0.01794 @989** | 0.01664 / 0.01813 | **214.1 s** | zbieżny pod capem |
(Luka R2.8 domknięta: wall-time mierzony i zapisany w train_meta.json.)

## §3. Bramka offline G13′ + dyspersja
| ramię | rollouty OK /24 | per-cell oba / którekolwiek | werdykt |
|-------|------------------|------------------------------|---------|
| NCP kanoniczny 0337d5ea | **24/24** | 12 / 12 | PASS (punkt odniesienia przyrządu) |
| **GRU seed1** | **24/24** | 12 / 12 | **PASS ⇒ LATA (S2)** |
| **MLP-k20 seed1** | **1/24** | 0 / 1 | **FAIL ⇒ NIE LATA** (PRE §2) |
Zdanie kanonu dla MLP-k20 (PRE §2, verbatim): „pod zamrożonym torem treningu NCP kontrola
MLP-k20 nie osiągnęła progu offline pozycji 3; porównanie lotne niewykonane". Obserwacja
opisowa: MLP-k20 ma NAJLEPSZE val-MSE z trójki (0.0179 vs 0.049) i NAJGORSZY rollout —
rozjazd MSE↔zamknięta pętla widoczny już w modelu punktowym (przy k=5 ujawnił go dopiero SITL).

**Dyspersja (opisowa, zero selekcji, zero lotów; wagi w results/LIQ/offline_dispersion/):**
| ramię | s1 (kanon/kampania) | s2 | s3 |
|-------|----------------------|----|----|
| NCP | 24/24 (wagi kanoniczne) | 24/24 (val .0515) | 24/24 (val .0457) |
| GRU | 24/24 (val .0490) | 23/24 (val .0487) | 24/24 (val .0501) |
| MLP-k20 | 1/24 (val .0179) | **0/24** (val .0171) | **1/24** (val .0158) |
Kolaps okna k=20 jest stabilny między ziarnami init; parytet NCP↔GRU offline również.

## §4. FREEZE_LIQ, kontroler, rejestr, launcher, smoke
1. **FREEZE_LIQ** (`net/frozen/FREEZE_LIQ.md`, PRZED jakimkolwiek lotem):
   gru.npz `5ec027555b8fc0bf12007a3dea0fdb5629fc46cdbbd859150b6963c4cdaac383` (1956) ·
   mlp20.npz `74b5ae7d041bb776c9352c19f80582ecaea6bb8c429cae6d5e1a89a2ea8a6c8e` (1939)
   + echo configu + numpy. mlp20 zamrożony dla tożsamości WYNIKU (nie lata).
2. **Kontroler** `r03/controllers/liq_controller.py`: klon kontraktu NetController
   (set_feed/step/reset/begin_reset, hover-hold przy utracie tracka, tgt=pos+v·T_LOOKAHEAD,
   clip_v), inferencja GRU21/MLPk20; **guard: sha256 wag vs FREEZE_SHA_LIQ ⇒ RuntimeError
   ODMOWA LOTU** (liq_controller.py:57-61). controller_sha `6d72437f7dd16d83…`.
3. **Wartości CONTROLLER= Z KODU** (r03/controllers/__init__.py po edycji): `"gru"` → LiqGru ·
   `"mlp20"` → LiqMlp20 (obok route/orbit/net). Env dodatkowy: ŻADEN (ramię = nazwa rejestru;
   w odróżnieniu od net/NET_ARM). Diff rejestru VERBATIM:
```
+from r03.controllers.liq_controller import LiqGru, LiqMlp20
     "net": NetController,
+    "gru": LiqGru,          # LIQ (PRE_LIQ §7, SR-9): kontrola rekurencji, wagi net/frozen/gru.npz
+    "mlp20": LiqMlp20,      # LIQ (PRE_LIQ §7, SR-9): kontrola okna k=20, wagi net/frozen/mlp20.npz
```
4. **Smoke offline (bez SITL):** `make_controller("gru"/"mlp20", params=…, orbit_dir=…, vmax=…)`
   — sygnatura fabryki ławki kompatybilna (lekcja route→orbit domknięta wykonaniem); replay
   nagranego feedu epizodu D6 c11_s01 (boot3/attempt1, 1378 ticków): wyjścia skończone
   1378/1378, |v|max=3.000 ≤ vmax, fazy approach→orbit. **Negatywny test guardu: podmiana
   oczekiwanego sha ⇒ RuntimeError ODMOWA LOTU ✓.** Regresja istniejących testów po edycji
   rejestru: pytest tests_net + tests_net_controller + tests_orbit_executor + test_k1_shield
   = **22 passed**.
5. **Launcher sondy** `tools/liq_launcher_stock.sh` (UŻYCIE dopiero S3): kopia w_launcher.sh
   minus bezwarunkowy prepend wind_models (w_launcher.sh:42); lock/pgrep/guard OUTDIR/przepływ
   1:1; w miejscu prependu echo GZ_SIM_RESOURCE_PATH do `$OUTDIR/.gz_resource_path_proof`
   (dowód „stock" per boot). Pełny diff: 2 hunki (nagłówek komentarza + linia prependu →
   mkdir+echo dowodu) — verbatim w §4-diff poniżej.
```
41,42c42,45
< # --- W9: prepend modelu z enable_wind (dowód R1.7); gz_env.sh:19 dopisuje stock po naszym ---
< export GZ_SIM_RESOURCE_PATH="$ROOT/worlds/wind_models${GZ_SIM_RESOURCE_PATH:+:$GZ_SIM_RESOURCE_PATH}"
---
> # --- LIQ/S3 (PRE_LIQ §5): BEZ prependu wind_models — dron = STOCK x500_base z drzewa PX4.
> # Jedyna różnica vs tools/w_launcher.sh (frozen): usunięta dźwignia kopii modelu (w_launcher.sh:42).
> # Echo GZ_SIM_RESOURCE_PATH do OUTDIR jako dowód „stock" (manifest sondy).
> mkdir -p "$OUTDIR"
> echo "GZ_SIM_RESOURCE_PATH=${GZ_SIM_RESOURCE_PATH:-<puste>}" > "$OUTDIR/.gz_resource_path_proof"
```

## §5. Zadanie biurkowe sondy (read-only; metodologia spójna: z_max = max(−own_pos_ned[2]) z demo.jsonl per epizod)
**(i) kampania W L0/net — model enable_wind, świat world_wind_s0, c11:** s01 **18.45** ·
s02 **14.43** · s03 **15.68** m.
**(ii) noga NET F2 ramię ncp — model STOCK, świat world_demo_A3:** F2 **ZAWIERA c11 wprost**
(nie trzeba odpowiednika): c11_s01 **13.27** · c11_s02 **13.03** · c11_s03 **12.86** ·
c11_s04 **13.19** m.
Vs progi PRE §5 (sonda: NIEOBECNE ≤13.0 w 2/2 · POTWIERDZONE ≥15.0 w ≥1/2): historyczny stock
siedzi OKRAKIEM na progu 13.0 (2/4 nieznacznie powyżej), enable_wind wyraźnie wyżej (2/3 ≥15.0).
Zastrzeżenie WPROST: (ii) to INNY świat (A3) niż sonda (world_wind_s0) — porównanie biurkowe
jest poglądowe; rozstrzyga sonda S3 (świat stały, jedyna zmienna = model).

## §6. Higiena i commity
Pliki: dokładnie lista zamknięta §0.4 (PRE_LIQ.md; models_liq, train_liq, gru.npz, mlp20.npz,
FREEZE_LIQ.md, liq_controller.py, liq_launcher_stock.sh, results/LIQ/**; jedna edycja:
rejestr +2). Commit 1 = ARCH-1 (PRE_LIQ). Commit 2 = całość S1. Porcelain po commitach pusty.
Zero bootów, zero dotknięć frozen (piny/certy/sha re-potwierdzone wykonaniem). Push = Olga.
Czeka: **PROMPT_LIQ_S2** (smoke lotny 2 booty + rundy 1–6); przy FAIL MLP-k20 skład rund S2
= decyzja CC w S2 (PRE §3 zakładał 3 ramiona; lotne są 2: NCP + GRU — parowanie i przeplot
bez zmian, scenariusze MLP-k20 bez lotów per PRE §2). STOP-LIQ1.
