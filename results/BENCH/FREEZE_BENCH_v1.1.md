# FREEZE_BENCH v1.1 — po bramce startu intruza (PROMPT_BENCH_RESHAKEOUT §3)

Delta względem v1.0 (`FREEZE_BENCH.md`) WYŁĄCZNIE w plikach dozwolonych §2 (bramka startu = poprawka
HARNESSA, nie egzekutora). Podstawa: DECYZJA_STOP-1_CC.md (D9 V2→V1, bramka dozwolona).

## Zmienione (stary → nowy sha256)

| plik | v1.0 | v1.1 |
|---|---|---|
| `harness/intruder_motion.py` | `c58d308deddaf653f136a29e0f5413ec2c66e25ea20205a573c460e51567eeee` | `0397fa807982f5d389391583cf1c1b94018a243148fad08e92c94758c413630a` |
| `bench/bench_flight.py` | `7b1eff82a71bd850c0e00e0b7671f91480639b56ae9d542c69c6cf4ccadad755` | `df1250ad3e5ee0d85c7303ec0cf0bc71ea93f7a9d0c295fd76844702bf9c12a0` |

Zmiana: `intruder_start_gate` (czysta logika, testowalna) + `TOL_START=0.20` + async twin w `bench_flight`
(prestart set_pose do pozy startowej + hover, czekaj aż GT ≤ TOL, 5 s→retry→5 s→INVALID_START).

## NIEZMIENIONE (sha identyczne z v1.0 — potwierdzenie)

| plik | sha256 | =v1.0 |
|---|---|---|
| `r03/controllers/orbit_executor.py` (EGZEKUTOR) | `840514361e4ae5e93ddbb0dd31a7dae81832805b90abccc334d84bbd043730d4` | ✓ |
| `bench/executor_params.json` (PARAMETRY) | `12c14adb83efc762e2b2c8f3119d747bdcac5ae865250e9be7ed4a7c40844d9c` | ✓ |
| `bench/bench_judge.py` (SĘDZIA) | `8ec0fcfbb7e46953d868553dcfbfcee20dddfdfa337e2d9f34e86117377ed7d2` | ✓ |
| `harness/track_feed.py` (FEED) | `674d78ab7966d0ffc4881f058a75bc564ec42741d3e208bf59812c5a519043e8` | ✓ |
| `bench/features.py` (CECHY) | `9adc15056b4811492f22d4c06ea9a273d2f43a0e61a30f61f997a3e5a5e2d572` | ✓ |
| `bench/scenarios.py` | `fe4f2aebfb1cf83382a8f021041103ed483f4274f087f9e6dc7398563754d8a4` | ✓ |
| `bench/demo_logger.py` | `929cb9aa1b59b0be7ae1c0a3aaeeccf017e158535b7a5f09df8263d4df7272c6` | ✓ |
| `r03/controllers/common.py` | `07c61c4d7778afc7d67479ebc38acc23e38fe1c2e776e627b251f93b1db64dac` | ✓ |
| `results/BENCH/scenario_manifest.json` (MANIFEST) | `e0527026df01b488e38e79307c258bf447ad68f2da0c7db3fac3810f0a388fd7` | ✓ |

**Piny NIEZMIENIONE:** shield `1c584964…`, config `4c440e42…`, gate `c3ccabe0…`, base `7fc45cf2…`, sędziowie
K1/DEMO. **Egzekutor i parametry BAJT-W-BAJT z v1.0** — SR-3 respektowany (zero strojenia). Po B3: SR-3 wraca w pełni.
