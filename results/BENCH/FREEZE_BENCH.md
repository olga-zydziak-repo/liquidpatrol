# FREEZE_BENCH — zamrożenie ławki przed pierwszym lotem kryterialnym (PROMPT_BENCH_BUILD I3, PRE §7)

Baza build `055bd3e`+ (commit B1). Po B1: strojenie = nowa seria (SR-3 PRE, nowy `executor_params_sha`).
sha256 zamrożonego zestawu:

| plik | sha256 |
|---|---|
| `bench/bench_judge.py` | `8ec0fcfbb7e46953d868553dcfbfcee20dddfdfa337e2d9f34e86117377ed7d2` |
| `bench/features.py` | `9adc15056b4811492f22d4c06ea9a273d2f43a0e61a30f61f997a3e5a5e2d572` |
| `bench/scenarios.py` | `fe4f2aebfb1cf83382a8f021041103ed483f4274f087f9e6dc7398563754d8a4` |
| `bench/demo_logger.py` | `929cb9aa1b59b0be7ae1c0a3aaeeccf017e158535b7a5f09df8263d4df7272c6` |
| `bench/bench_flight.py` | `7b1eff82a71bd850c0e00e0b7671f91480639b56ae9d542c69c6cf4ccadad755` |
| `harness/track_feed.py` (FEED-B params D1) | `674d78ab7966d0ffc4881f058a75bc564ec42741d3e208bf59812c5a519043e8` |
| `harness/intruder_motion.py` | `c58d308deddaf653f136a29e0f5413ec2c66e25ea20205a573c460e51567eeee` |
| `r03/controllers/orbit_executor.py` | `840514361e4ae5e93ddbb0dd31a7dae81832805b90abccc334d84bbd043730d4` |
| `r03/controllers/common.py` | `07c61c4d7778afc7d67479ebc38acc23e38fe1c2e776e627b251f93b1db64dac` |
| `bench/executor_params.json` | `12c14adb83efc762e2b2c8f3119d747bdcac5ae865250e9be7ed4a7c40844d9c` |
| `results/BENCH/scenario_manifest.json` | `e0527026df01b488e38e79307c258bf447ad68f2da0c7db3fac3810f0a388fd7` |

**Piny NIEZMIENIONE:** `r01/shield.py` `1c584964…`, `r03/config.py` `4c440e42…`, `r03/gate_run_r03.py`
`c3ccabe0…`, `r03/controllers/base.py` `7fc45cf2…`, sędziowie K1 `4e0dc0af…` / DEMO `79b1e936…`.

**FEED-B (zamrożone wartości, ANEKS D1):** f=10 Hz, L=0.20 s, σ_xy=0.5, σ_z=0.3, p_drop=0.05, pozycja RAW,
trk_vel=regresja liniowa 1.0 s w czasie sim. Powtarzane w każdej tabeli wyników (etykieta „pod emulowanym track-feedem").

**Wektor cech (8, ANEKS P1):** [rel_x, rel_y, rel_z, own_vn, own_ve, own_vd, track_age_s, track_valid].

**Delta wrappera (G/I):** `harness/run_boot.sh` — 2 linie (`empty|bench` etykieta ARM + gałąź dispatch `bench)`);
diff verbatim w RAPORT §2. Reszta wrappera bez zmian.
