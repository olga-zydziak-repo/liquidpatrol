# D0 — inwentarz INFRA-3 (przed jakąkolwiek zmianą)

Baza: `3065b8b` · `git log origin/master..HEAD` puste (I0.1 PASS) · CC 2026-08-30.
Wykonane PRZED edycją. Liczby/linie z ODCZYTU plików, nie z pamięci.

## (a) sha256 plików pinowanych i sędziów

| plik | sha256 (zmierzone) | źródło pinu | zgodne? |
|---|---|---|---|
| `r01/shield.py` | `1c584964ddc85192c1381f5041e8ed3b7b81b984c92b8f33d5c685acd2cba2c2` | `k1_shield_pins.py` SHIELD_PINS + ANEKS_SHA:155 | ✅ |
| `r03/config.py` | `4c440e4265574b68c2a3341105d5cb0ace07ed683cd0bca43228af356629752a` | `k1_shield_pins.py` SHIELD_PINS + ANEKS_SHA:156 | ✅ |
| `r03/gate_run_r03.py` | `72619513c682e76892c531ec3dae2d918da08da92017605dcba50103977cf58a` | `k1_shield_pins.py` SHIELD_PINS + ANEKS_SHA §W3:419 | ✅ (jedyny plik pinowany, który INFRA-3 A1 zmienia) |
| `k1/k1_judge.py` | `4e0dc0afffda099837a002191a5540fd95d6de13cb88e7233433d67b1b998ae1` | ANEKS_SHA:10 (`0ce4d8e`) / §W1 | ✅ |
| `tools/act_judge.py` | `79b1e9367b85bf7c29f97dc5ea9757052be68a26903e48c0a237f941526a671a` | PROMPT_INFRA3 I0.2 (sędzia DEMO-B) | ✅ |

Wszystkie zgodne ⇒ brama I0.3(a) PASS, brak STOP.

## (b) bloki w `gate_run_r03.py` produkujące setpoint / stan trasy (numery linii z odczytu)

| linie | co produkuje | pola |
|---|---|---|
| 200 | init trasy `wps = C.corner_waypoints_r03()` | `wps` |
| 206–207 | init stanu trasy `seg_i = 0` / `dist = 1e9` | `seg_i`, `dist` |
| 225 | wybór wp bieżącego segmentu `wp = wps[seg_i % len(wps)]` | `wp` (STARY, przed inkrementem) |
| 226–227 | wektor do celu `dx, dy = wp - pos` / `dist = hypot(dx,dy)` | `dx`, `dy`, `dist` |
| 228–229 | inkrement segmentu `if dist < 1.0 and not descending: seg_i += 1` | `seg_i` (PO inkremencie) |
| 230 | setpoint pozycji `tgt = (wp[0], wp[1], -ALT)` (ze STAREGO wp) | `tgt` |
| 291 | setpoint prędkości `vn, ve = (VMAX·dx/dist, VMAX·dy/dist)` (0,0 gdy dist≤1e-3) | `vn`, `ve` (ze STAREGO wp) |

Kolejność efektywna: wp(stary) → dx,dy,dist → inkrement seg_i → tgt(stary wp) → v_ned(stary wp).
Zwracane `seg_i` po inkremencie — tak czyta go trigger K1 (`_cur = wps[seg_i]`, 240) i trigger S4 (`seg_i >= 1`, 234).
`dist` (do STAREGO wp) czyta trigger S4 (234). `wps` czyta trigger K1 (239–241).

Bloki, które NIE są setpointem (NIE dotykam): denial injection K1/S4/S2/S3 (232–258), decyzja osłony
`shield.step` (260), zejście D5 `is_pos`/`V_DESC_FAST`/`H_SWITCH`/`td` (268–289), trace v2 (263–266).

## (c) mechanizmy przed-lotowe / bootowe i ich lokalizacja

| mechanizm | plik implementacji | wołany z | uwaga |
|---|---|---|---|
| watchdog EKF2 (reinit, preflight-only) | `tools/infra2_ekf_watchdog.py` | `k1/run_k1_boot.sh:80–84` (BEZWARUNKOWO E∧S∧N) | max 2 reinity, kończy @arm |
| higiena CAL_MAG (reset do baseline S@0.2 b7) | `acts/ensure_mag_baseline.py` | `k1/run_k1_boot.sh:45` | przed KAŻDYM bootem |
| higiena GPS (`EKF2_GPS_CTRL`→7) | `acts/ensure_gps_enabled.py` | `k1/run_k1_boot.sh:40` | leftover po GPS-denied |
| bramka obciążenia I2a (LOAD_MAX 8.0, 10 min) | inline w wrapperze | `k1/run_k1_boot.sh:51–64` | env-block, boot się nie zaczyna |
| próbnik RTF (habitat sim↔wall) | `acts/rtf_sampler.py` | `k1/run_k1_boot.sh:71`, `acts/run_A3.sh:28` | — |
| dowód headless (`gz sim -g` brak) | inline | `k1_boot:69`, `run_act:26–27`, `run_A3:25` | wszystkie trzy |
| hash świata + kopia do PX4 | inline `sha256sum` | `acts/run_act.sh:16–17`, `acts/run_A3.sh:15–16` | hash z `worlds/<W>.sdf` |
| spawn intruza (MODEL) | `gz service .../create` na `r02/intruder_model.sdf` | `acts/run_act.sh:37–38` | tylko A1/A2 (A3 GPS-denied bez intruza) |
| kopia ulogu → `boot.ulg` + `ulog_src.txt` | inline `find -newermt` | `k1/run_k1_boot.sh:116–117` | tylko K1 |
| certs_selfcheck | `r01.proofs.certs_selfcheck` | `k1/run_k1_boot.sh:34–37` | tylko ARM=S |
| finalize (K1 S/N) | `k1/k1_finalize.py` | `k1/run_k1_boot.sh:130–132` | manifest+habitat+sędzia 4e0dc0af |
| finalize (K1 E pusty) | `tools/infra1_empty_finalize.py` | `k1/run_k1_boot.sh:124–125` | manifest pustego bootu |
| finalize (A3) | `acts/build_a3_manifest.py`+`habitat_gate.py`+`finalize_manifest.py`+`judge_run.py` | `acts/run_A3.sh:48–52` | sędzia act_judge 79b1e936 |
| settle EKF | inline `sleep` | k1_boot:90 (90 s), run_act:40 (150 s), run_A3:34 (90 s) | — |

## (d) macierz ścieżka × mechanizm (proza per ścieżka)

**Ścieżka K1 — `k1/run_k1_boot.sh` (ARM=S osłona / N natywny / E pusty).** MA: watchdog EKF2 (bezwarunkowy),
higienę CAL_MAG, higienę GPS, bramkę obciążenia I2a, próbnik RTF, dowód headless, kopię ulogu, certs_selfcheck
(tylko S), finalize (k1_finalize S/N, infra1_empty_finalize E), settle 90 s, timejump pre/post, b4_state (orphany+cooldown).
NIE MA: hasha świata (świat = stockowy `default`, niekopiowany, niehashowany), spawnu intruza.

**Ścieżka aktów A1/A2 — `acts/run_act.sh`.** MA: hash świata (`world_demo_A*` z `worlds/`, kopia do PX4 +
sha256), spawn intruza (`r02/intruder_model.sdf`), bridge+capture kamery filmowej, dowód headless, settle 150 s,
timejump pre/post. NIE MA: watchdoga EKF2, higieny CAL_MAG, higieny GPS, bramki obciążenia I2a, próbnika RTF,
kopii ulogu, certs_selfcheck, b4_state (orphany/cooldown), osobnego finalize (gate_run_r02 pisze trace, sędzia offline).

**Ścieżka aktu A3 (GPS-denied) — `acts/run_A3.sh`.** MA: hash świata (`world_demo_A3`), próbnik RTF, bridge+capture
kamery filmowej, dowód headless, settle 90 s, timejump pre/post, finalize (build_a3_manifest→habitat_gate→
finalize_manifest→judge_run act_judge). NIE MA: watchdoga EKF2, higieny CAL_MAG, higieny GPS, bramki obciążenia I2a,
spawnu intruza (GPS-denied bez celu), kopii ulogu, certs_selfcheck, b4_state.

**Predykcja CC potwierdzona odczytem:** `run_act.sh` i `run_A3.sh` NIE mają watchdoga, higieny mag ani bramki
obciążenia; `run_k1_boot.sh` NIE ma hasha świata ani spawnu intruza. ✅ (to jest luka, którą domyka wrapper §B —
`harness/run_boot.sh` łączy WSZYSTKIE mechanizmy w jednej kompozycji.)

## Noty

- N1: `k1/run_k1_boot.sh` używa świata stockowego `default` (linia 13) — brak hasha świata jest zamierzony dla K1,
  ale program (który będzie latał w światach z `worlds/`) potrzebuje hasha zawsze; stąd §B1.1 krok 5.
- N2: `run_act.sh` (A1/A2) nie ma finalize w skrypcie — sędzia DEMO-B (`act_judge.py`) uruchamiany offline po próbie.
  A3 finalizuje w skrypcie. Wrapper §B parametryzuje finalize przez `FLIGHT` (k1_finalize / infra1_empty_finalize).
