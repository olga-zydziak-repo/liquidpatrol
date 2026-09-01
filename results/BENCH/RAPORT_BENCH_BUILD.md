# RAPORT_BENCH_BUILD — ławka: build + shakeout (STOP-1)

LiquidPatrol · pozycja 2 · wejście PRE_BENCH + ANEKS_BENCH-0 (aneks wygrywa) · CC 1.09.2026 · push=Olga.
Commity: B0 `055bd3e` (docs) · B1 `843de36` (build+freeze) · B2 (shakeout, ten commit). Bez lotów kryterialnych (SR-4).

## §1. D0 (pełny: `results/BENCH/D0_build.md`)

- **Saturacja |v| ≤ V_MAX = TYLKO w kontrolerze** (`route_follower.py:42` / `orbit_executor` `common.clip_v`);
  gate nie obcina (`gate_run_r03.py:298` wysyła cmd["v_ned"] bez sprawdzenia), `k1_finalize.vmax_check` = pomiar
  post-hoc. **P-BB1 potwierdzone.** Egzekutor saturuje własne wyjście, test kontraktu 10⁴ pilnuje.
- Sim-time: z `header.stamp` próbek `pose/info`/`dynamic_pose` (gate `:82`); feed/egzekutor liczą filtry w sim (P2).
- Wrapper env passthrough: `case "$FLIGHT"` inline env; delta = 2 linie (§6/N1).
- sha pinów zgodne (shield 1c584964, config 4c440e42, gate c3ccabe0, base 7fc45cf2, sędziowie 4e0dc0af/79b1e936).

## §2. Artefakty A–I + testy (bez SITL, verbatim)

```
pytest bench/tests_scenarios.py bench/tests_orbit_executor.py bench/tests_demo_features.py
       bench/tests_bench_judge.py harness/tests_track_feed.py harness/tests_intruder_motion.py
       tests_controller_split.py tests_harness_infra3.py  →  38 passed
```
- **A** `bench/scenarios.py`+`scenario_manifest.json`: 120 ep (blok1 s1-4=48, blok2 s5-10=72, TEST seed%4==0),
  dysk 18 m (cap dur na czas wyjścia z dysku), determinizm bit-w-bit.
- **B** `harness/intruder_motion.py`: set_pose 20 Hz `position_at`, `gt_intruder.jsonl` (poza ZASTOSOWANA z pose/info,
  ramka `drv2ned`), deterministyczna trajektoria, set_pose liczone.
- **C** `harness/track_feed.py` FEED-B: L 0.20/σ 0.5/0.3/p_drop 0.05 w ±10%, σ_v regresji 0.55±30%, pozycja RAW,
  sim-inwariant pod stallem wall.
- **D** `orbit_executor.py`+`common.py`+`executor_params.json`: prawo D3, |v|≤VMAX zawsze; no-gz grep, replay-det,
  kontrakt 10⁴, model punktowy 12/12 (wejście ≤25 s ∧ frac ≥0.85).
- **E+F** `demo_logger.py`+`features.py`: wektor 8-wym (ANEKS P1, bez v_intr), dwie ścieżki bit-identyczne, brak null.
- **G** `bench_flight.py`: osłona P2-ε w pętli, orbita, orkiestracja 4 epizodów, bramka startu/resetu.
- **H** `bench_judge.py`+7 testów syntetycznych: SUKCES(r8/1m/s), FAIL(a hover / b r12 / c 1.5-orbity / d przelot /
  e REFUSE), D9 (stall sim-robust: metryki bez zmian, V1 FAIL, V2/V3 wg cap).

## §3. Zamrożenie (pełny: `results/BENCH/FREEZE_BENCH.md`)

sha256 zamrożonego zestawu (11 plików) + piny bez zmian. Po B1 strojenie = nowa seria (SR-3). FEED-B i wektor cech 8
zamrożone; „pod emulowanym track-feedem (10 Hz, L 0.20, σ 0.5/0.3, p_drop 0.05)" — etykieta każdej tabeli wyników.

## §4. Predykcja modelu punktowego + FEED-B (`point_model_prediction.json`) — PREDYKCJA, nie pomiar

12/12 komórek: wejście w pasmo ≤ 2.8 s, frac[6,10] = 1.0 (egzekutor odporny na szum/opóźnienie/zanik FEED-B na
idealnym śledzeniu punktowym). SITL różni się dynamiką PX4 (patrz §5/§6).

## §5. Shakeout (2 booty diag, `results/BENCH/shakeout/boot{1,2}`; NIE liczą się do p_exec ani zbioru)

Boot1 i boot2: te same 4 epizody (id 0,5,10,11 = c00 v0/0°, c05 v0.5/90°, c10 v1.0/180°, c11 v1.0/270°, seed 1).
Sędzia `bench_judge`; d_min = 3D min; d_min_orb = min po 3 s (bez tranzientu granicznego). Wszystko sim/GT.

| epizod | boot | wejście[s] | frac[6,10] | frac[7,9] | omiat.[°] | d_min | d_min_orb | REFUSE | breach | D6 | V1/V2/V3 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| c00 v0/0° | 1 | 0.0 | 0.949 | 0.933 | 955 | 7.30 | 8.22 | 0 | F | **✓** | ✗/✗/✓ |
| c00 | 2 | 0.0 | 0.953 | — | 958 | 7.29 | 8.60 | 0 | F | **✓** | ✗/✗/✓ |
| c05 v0.5/90° | 1 | 2.62 | 0.925 | 0.901 | 1015 | 7.61 | 7.61 | 0 | F | **✓** | ✗/✓/✓ |
| c05 | 2 | 2.65 | 0.931 | — | 1022 | 8.09 | 8.09 | 0 | F | **✓** | ✗/✓/✓ |
| c10 v1.0/180° | 1 | 0.0 | 0.995 | 0.676 | 927 | 7.77 | 7.77 | 0 | F | **✓** | ✗/✓/✓ |
| c10 | 2 | 0.18 | 0.995 | — | 929 | 8.13 | 8.13 | 0 | F | **✓** | ✗/✓/✓ |
| c11 v1.0/270° | 1 | 5.14 | 0.976 | 0.613 | 1103 | 0.26 | 3.23 | 0 | F | **✗(d)** | ✗/✓/✓ |
| c11 | 2 | 5.26 | 0.974 | — | 1094 | 1.23 | 3.76 | 0 | F | **✗(d)** | ✗/✓/✓ |

**Sukces D6: 3/4 (oba booty).** Powtarzalność boot1↔boot2: Δfrac[6,10] ≤ 0.006 na epizod (c00 .004, c05 .006,
c10 .000, c11 .001) — egzekutor deterministyczny na tych ziarnach. **0 REFUSE, 0 breach we wszystkich 8 epizodach.**
|v| max wysłane ≤ V_MAX (saturacja `clip_v`, dowód w demo `cmd_v_ned`). Stalle: 2–4 deep-runy/epizod, najdłuższy 0.0 s
(pojedyncze próbki), Δsim/Δwall 0.952–0.958. Ważność: **V1 odrzuca 4/4** (każdy deep-stall), **V2 1/4** (c00 n_deep=4>3),
**V3 0/4** — zgodne z D9 (V2). Wierszy demo/epizod ~1400 (boot1 5665, boot2 5669 łącznie).

**Predykcje: P-BB2 przekroczone** (4/4 weszły w pasmo, frac≥0.85 w 4/4), **P-BB3 ✓** (0 REFUSE), **P-BB4 ✓**
(V1 100%≥50%, V2 25%≤25%). **P-BB5 chybione** (pierwszy problem to d_min c11, nie bramka resetu — reset trzymał in_gate=True).

## §6. Odchylenia i noty (problemy NIE naprawione — SR-5/SR-3: znalezisko do STOP-1, nie strojenie)

- **N1 (wrapper 2 linie, nie 1):** `harness/run_boot.sh` ma DWA case (ARM-assignment + dispatch); FLIGHT=bench
  wymaga obu → 2 zmienione linie (`empty|bench` etykieta + gałąź `bench)`). Predykcja „jedna linia" chybiona o 1;
  nic poza tym w wrapperze. Diff verbatim:
  ```
  -  empty)    ARM="${ARM:-E}"; POINT="${POINT:-0.0}";;
  +  empty|bench) ARM="${ARM:-E}"; POINT="${POINT:-0.0}";;
  +  bench) GATE_OUT="$OUTDIR/trace.jsonl" ... python3 -m bench.bench_flight > "$OUTDIR/act.log" 2>&1; RC=$?; HARNESS_FILE="$ROOT/bench/bench_flight.py";;
  ```
- **N2 (c11 d_min < 4 — GŁÓWNE ZNALEZISKO, reprodukowalne):** dwa składniki, oba w obu bootach:
  (a) **tranzient graniczny** d_min 0.26/1.23 @ t≈0.27 s — intruz NIE zdążył przejść do pozy startowej epizodu
  (bench_flight bramka startu potwierdza ISTNIENIE intruza, nie że jest w pozie startowej; `intruder_motion` ma lag);
  (b) **załamanie promienia orbity** d_min_orb 3.23/3.76 < 4 — przy v_intr=1.0/270° orbita chwilowo zapada się poniżej
  pasma (frac[6,10] wciąż 0.976, więc krótkie wychylenie). Model punktowy tego NIE złapał (idealne śledzenie vs dynamika
  PX4 + feedforward trk_vel przy zmianie kursu intruza). Do STOP-1: (i) bramka startu „intruz w pozie startowej z pose/info"
  (PRE §3 — dziś niepełna); (ii) ewent. strojenie k_ff/k_r egzekutora = NOWA SERIA (SR-3). NIE tknięte.
- **N3 (feed vs GT wejście):** bench_flight raportuje `t_entry=None` dla c10 (jego licznik z feed-d [6,10]), a sędzia
  (GT) daje wejście 0.0/0.18 i frac 0.995. Rozjazd = szum/opóźnienie FEED-B na granicy pasma; sędzia GT jest rozstrzygający,
  egzekutor i tak wszedł w orbitę (frac 0.995). Licznik bench_flight to tylko log, nie kryterium.
- **N4 (KIND=diag → finalize stub):** FLIGHT=bench idzie w `k1_finalize` (else), który pada na trace ławki → stub manifest
  (kind=stub). Werdykt ławki = `episode_judges.json` z `bench_judge`, NIE manifest wrappera. Booty diag, zamierzone.
- **N5 (2× env-block dreamforge):** przed boot1 i boot2 (retry) bramka §3 odmówiła startu przy `dreamforge-arc` @75–100% CPU
  (`attempts_2_10.py`, `a15e_blind.py`) — env-block NIE liczy się do budżetu; live-walidacja bramki INFRA-3 §3 ×2. Booty
  poleciały po samoczynnym zejściu dreamforge (maszyna czysta, loadavg <0.8).
- **N6 (V2 vs „2s stall"):** PROMPT §5 „stall 2 s → V2 PASS" SPRZECZNE z ANEKS D9 (longest ≤1.5 s). Aneks wygrywa: sędzia
  ma V2 z cap 1.5 s; test dowodzi 1.4 s→V2 PASS, 2.0 s→V2 FAIL. Nota w `tests_bench_judge`.
- **Błąd w prawie sterowania:** poza N2(b) brak; 0 REFUSE/breach potwierdza zgodność z założeniami osłony w nominale.

## Werdykt build/shakeout
Ławka ZBUDOWANA i ZAMROŻONA; testy 38/38; shakeout 2 booty diag, powtarzalne, D6 3/4, 0 REFUSE, 0 breach, jedno
nazwane znalezisko (c11 d_min, N2). **STOP-1.** CC: ratyfikacja zamrożenia + wybór reguły D9 (V1/V2/V3 dane: V1 4/4,
V2 1/4, V3 0/4) + decyzja o N2 (bramka startu intruza / ewent. nowa seria egzekutora) + zgoda na kampanię (ANEKS_BENCH-1).
