# PROFIL_REGATE — profil lotu z charakteryzacji ENTRY-once (PROMPT_D_P3 T0, read-only)

Rekonstrukcja profilu lotu z biegów REGATE, w których zmierzono `cov_entry_once=1.0 @7/9 m`
(live-MTI, struktura∧MTI). **Każda liczba: `plik:linia`.** Bez zmian w kodzie (T0 = recon).
Źródło główne: `results/R02/mti/mti_flight.py`; biegi `results/R02/mti/REGATE/regate{1,2,3}`.

## §0 — Spójność charakteryzacji (warunek: brak rozjazdu ⇒ brak STOP)

Trzy booty, kryterium `AM2.2` (`aggregate_regate.py:89`). **Zgodne:**

| boot | cov_entry_once @7m | @9m | false_entry@7m | t_entry@7m | t_entry@9m |
|------|-----|-----|-----|-----|-----|
| regate1 | 1.0 | 1.0 | 0 | 2.17 | 1.63 |
| regate2 | 1.0 | 1.0 | 0 | 2.22 | 2.75 |
| regate3 | 1.0 | 1.0 | 0 | 5.98 | 10.87 |

(`results/R02/mti/REGATE/regate{1,2,3}/result.json`). Werdykt (+): mediana `cov_entry_once=1.0`
@7 i @9 m, admisja na wszystkich bootach (`B_regate_aggregate.json` `plus_verdict`). `t_entry`
p95 ≈ max = **10.87 s** (n=6, {7,9}) — to źródło `entry_expected_by` w spec A1/A2. **Profil czytelny
jednoznacznie ⇒ T0 NIE STOP.**

## §1 — Profil lotu drona w oknie ENTRY (EGO-MOTION — sedno)

Okno ENTRY = `run_dwell(label, R, dur, gt_present)` (`mti_flight.py:312`); `dur = DWELL_S`.
**Ruch własny biegnie RÓWNOLEGLE z pętlą decyzji przez CAŁE okno** (`mti_flight.py:320`
`motion_task = asyncio.ensure_future(observe_motion(dur))`).

- **Wysokość:** `HOVER_ALT = 9.0` m (`mti_flight.py:32`); takeoff do niej (`:216`), trzymana
  (składowa down prędkości = 0, `observe_motion` `:265`).
- **Trajektoria = KWADRAT prędkościowy** (`observe_motion`, `mti_flight.py:259-267`):
  - nogi NED `[(2.5,0),(0,2.5),(-2.5,0),(0,-2.5)]` (`:261`) — legs_v = **2.5 m/s** (domyślny,
    `run_dwell` woła `observe_motion(dur)` bez legs_v, `:320`; sygnatura `:259`);
  - **2.0 s / noga** (`:266` `asyncio.sleep(2.0)`) ⇒ ~**5 m / noga**; cykl 4 nogi = 8 s;
    przez `DWELL_S=30 s` ⇒ ~15 nóg ≈ 3.75 okrążenia; setpoint prędkości co nogę (`:265`).
  - stop `VelocityNedYaw(0,0,0,0)` na końcu (`:267`).
- **Yaw = 0 trzymany** przez całe okno (`VelocityNedYaw(vn, ve, 0, 0)` — 4. pole yaw=0, `:265`).
  Kamera stała-forward; ruch jest TRANSLACYJNY (bez obrotu). Ego-motion translacyjny daje
  przepływ tła, który derotacja MTI kasuje → rezyduum tła spada → widoczny ruch WZGLĘDNY celu.
- **Warm-up:** `run_dwell` śpi **2.0 s** przed pętlą decyzji (`:317`), by re-placer ustawił cel
  i MTI się rozgrzało.

## §2 — Umiejscowienie intruza w REGATE (WAŻNE: intruz ŚLEDZI drona)

`replacer()` (`mti_flight.py:170-189`), wątek daemon (`:197`). **Kadencja 16.7 Hz** (`sleep(0.06)` `:189`).

- **Czyta BIEŻĄCĄ pozę drona co iterację** (`xyz, yaw = gz_drone_pose()` `:175`) → intruz
  utrzymywany **dead-ahead względem drona** na zasięgu R:
  - horizontal `R_h = sqrt(R² − DALT²)` (`:180`), `DALT = 1.5` (`:40`);
  - `ix = xyz[0] + R_h·cos(yaw) + osc·(−sin yaw)` (`:184-185`), analogicznie `iy` (`:186`);
  - **oscylacja boczna `osc = 1.5·sin(2π·0.3·t)`** m @0.3 Hz (`:182`);
  - **pionowa `vosc = 0.6·sin(2π·0.23·t)`** m @0.23 Hz (`:183`); `iz = xyz[2] + DALT + vosc` (`:187`).
- **KONSEKWENCJA:** ponieważ intruz śledzi pozę drona, **geometria WZGLĘDNA (zasięg R dead-ahead,
  DALT) jest STAŁA** mimo 5-metrowych nóg ego-motion. Ruch własny porusza TŁO; cel zostaje
  centralnie w kadrze na R. To jest DOKŁADNIE skonfigurowany warunek, w którym `cov_entry_once=1.0`.

## §3 — Percepcja / kanał (kontrakty frozen — tylko cytowane, NIETYKANE)

- MTI tracker `MTITracker(MTIParams(), delta=3)` — baseline 200 ms (`:195`).
- `MTIParams`: `diff_thr=22, open_k=3, close_k=5, border_erode=10, min_area_px=8,
  max_area_frac=0.2, persist_m=3, persist_window=4, persist_move_thr=0.1`
  (`regate1/result.json` `params.mti`).
- Kanał `entry_require_mti=True` (`:196`) — brama struktura∧MTI (`decide_once` `:288-291`:
  `mti_ok = box_matches_component(box, comps, mti_center_thr)`, `central = edge_dist ≥ entry_edge_margin`,
  `gate = box ∧ central ∧ mti_ok`).
- `DECISION_HZ = 2.0` (`:41`) — kadencja tików decyzji (`period = 1/DECISION_HZ` `:321,328`).
- YOLO `yolov8s-worldv2.pt`, klasa „drone", `imgsz=640 conf=0.001` (`:281,236`); ładowany PO
  arm+start+freeze-offset (redukcja kontencji EKF, `:233-236`).
- Offset kamera↔attitude zamrożony w oknie spokojnym `freeze_offset(45)` (`:231`); parowanie
  klatka↔attitude PO TREŚCI (`pair_by_content`, `:249`).
- Zasięgi: `RANGES` default `5,7,9` (`:35`); `mti_run.sh:43` `RANGES=5,7,9`, `DWELL_S=30` (`:42`).

## §4 — Sekwencja czasowa boot→ENTRY (cytowana)

1. MAVSDK connect → health ≤90 s (`:199-208`); arm z retry (`:210-215`).
2. `set_takeoff_altitude(9)` + `takeoff` (`:216`); czekaj `alt ≥ HOVER_ALT−1.5` (`:217-221`); +4 s (`:222`).
3. offboard `set_velocity_ned(0,0,0,0)` → `start()` (`:223-227`); +4 s spokój (`:230`).
4. `freeze_offset(45)` (`:231`); YOLO load (`:234-236`); mti_worker start (`:257`).
5. `run_dwell`: `RP.mode=track`, `RP.R=R`, `RP.t0=now` (`:315-316`); warm-up 2.0 s (`:317`);
   `observe_motion(dur)` równolegle (`:320`); pętla decyzji @2 Hz przez `DWELL_S=30 s` (`:322-328`).

## §5 — TRANSPLANT DO AKTÓW: rozbieżność ram (do rozstrzygnięcia w T1, NIE zgadywana)

Charakteryzacja (§1–§2) i akty A1/A2 różnią się RAMĄ intruza — odnotowane, nie rozwiązane w T0:

| aspekt | REGATE (charakteryzacja) | akty A1/A2 (spec) |
|--------|--------------------------|-------------------|
| dron w oknie ENTRY | KWADRAT 2.5 m/s, nogi 5 m (`:261,266`) | dwell-hold `[0,0,-10]` (A1_spec `drone_dwell_ned`) |
| intruz | **ŚLEDZI drona** dead-ahead na R (`:175`) | **świat-stały pierścień** `[7.86,0,11.5]` ENU |
| geometria względna | **STAŁA** (R dead-ahead mimo ego-motion) | zależna od pozy drona |
| alt dron / DALT | 9 / 1.5 (`:32,40`) | 10 / 1.5 (intruz 11.5) — **DALT zgodne** |
| R_h dla R=8 | `sqrt(8²−1.5²)=7.86` (`:180`) | `7.86` (ring) — **zgodne** |

**Ryzyko transplantu (do T1, z fallbackiem GT-fed):** jeśli w akcie dron wykona kwadrat
2.5 m/s przy intruzie na ŚWIAT-STAŁYM pierścieniu (bez śledzenia), zasięg dron→intruz zmienia
się z nogami (±5 m wokół 8 m → poza pasmo 7–9), a cel dryfuje w kadrze. REGATE utrzymywał
zasięg STAŁY przez śledzenie. **T1 (≤2 biegi, „intruz wg spec") empirycznie rozstrzyga, czy sam
ego-motion drona (bez śledzenia intruza) odtwarza ENTRY+mti_ok; FAIL ⇒ auto-powrót GT-fed
(różnica poza profilem — świat/tło/geometria — to nowa noga, nie demo).** Dwie opcje projektowe
dla T2 wynikają z tej tabeli (mniejsze nogi ego-motion vs intruz-śledzący), obie ratyfikowalne
DOPIERO po PASS T1 — nie zapadają w T0.

## §6 — Wartości do T2 (spec A1/A2, po PASS T1)

Profil-do-wstawienia w oknie ENTRY (choreografia runnera, świat NIETKNIĘTY): `HOVER_ALT=9`
(albo alt aktu 10 — do decyzji T2), kwadrat `legs_v=2.5 m/s`, `2.0 s/noga`, `yaw=0`,
osc boczna `±1.5 @0.3 Hz`, pionowa `0.6 @0.23 Hz`, DALT `1.5`, `DECISION_HZ=2.0`, dwell `DWELL_S`
pokrywające `t_entry_p95=10.87 s`. Źródła: §1–§4 powyżej.
