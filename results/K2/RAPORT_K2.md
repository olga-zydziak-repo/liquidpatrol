# RAPORT_K2 — sieć orbituje, denial GNSS, osłona przejmuje (STOP-K2c)

**Pozycja 6.** Kontroler UCZONY (NCP-20, wagi `net/frozen/ncp.npz` sha `0337d5ea`==FREEZE_NET) orbituje intruza pod osłoną PatrolShield. W ~30s po ENTRY wstrzykiwany jest **realny** denial GNSS (`EKF2_GPS_CTRL=0`); osłona musi wykryć degradację (EKF `dead_reckoning`→`pos_flag`), wydać **REFUSE(POS_DEGRADED)** w budżecie K1 i wykonać **D5** (zejście prędkościowe dwufazowe) do touchdownu, bez przebicia koperty R_E=32m.

Pierwszy niepusty ledger REFUSE osłony z kontrolerem uczonym za sterami i pierwsze niezerowe wykonanie ścieżki REFUSE pętli ławki.

---

## §1. Werdykt — DRABINA: **PASS (12/12)**

| kryterium (ANEKS_K2-1 drabina) | wynik |
|---|---|
| ważne (valid V2′ do T_inj) | **12 / 12** |
| verdykty epizodu (+) | **12 / 12** |
| **DRABINA nogi** | **PASS** (12/12; próg: 12/12=PASS · 1=NIEROZSTRZYGNIĘTE(STOP) · ≥2=FAIL) |
| unresolved / niekompletne | 0 |

Kampania: 12 epizodów denialowych, **1 epizod/boot** (denial kończy boot — K1), 12 bootów, budżet K5′ (≤15 bootów / ≤2 sesje) niewyczerpany. Kolejka bez env-fail (0 re-append), bez tripwire, bez STOP.

---

## §2. Metryki agregatowe

| metryka | wynik | bramka | ocena |
|---|---|---|---|
| t_refuse (denial→REFUSE) | min 0.104 · max 0.116 s | pasmo [0.05, 0.15] s | **wszystkie w paśmie** |
| x_exc (wychylenie od T_inj) | mediana **1.809** · min 1.529 · max 2.592 m | tripwire eps_cap=9.25 | **wszystkie ≪ cap** (brak tripwire) |
| breach (przebicie R_E=32) | **0 / 12** | =0 | **PASS** |
| touchdown | 12 / 12 | wymagane | **PASS** |
| t_td (denial→touchdown) | ≈ 9.8 s (stały, D5 dwufazowe) | — | jednorodny |
| certs_selfcheck_rc | 0 / 12 | =0 | **PASS** |

**Predykcje recon (PRE_K2 / ANEKS_K2-1):**
- **P-K2-2** (t_refuse w paśmie na wszystkich ważnych) → **potwierdzona** (12/12 w [0.05,0.15]).
- **P-K2-3** (mediana x_exc 2.0–3.5m) → **NIETRAFIONA w kierunku bezpiecznym**: mediana 1.809m, poniżej przewidzianego zakresu (zapowiedziane już przez diag 1.797m). Osłona wychyla mniej, niż zakładał recon.
- **P-K2-4** (0 breach) → **potwierdzona** (0/12).
- **P-K2-1** (predykcja defektu przy pierwszym wykonaniu REFUSE+D5) → **NIEZREALIZOWANA**: diag i wszystkie 12 epizodów czyste za pierwszym strzałem.

---

## §3. Ledger denialowy — sekwencja zdarzeń verbatim (12/12)

Każdy epizod: `denial → REFUSE(POS_DEGRADED) [~0.11s] → D5 zejście → touchdown → denial_boot_end`. Czasy w sim-time.

| # | boot | scenario | denial@sim | touchdown@sim | t_refuse (s) | x_exc (m) | breach | (+) |
|---|---|---|---|---|---|---|---|---|
| 1 | k2c_b1 | c00_s01 | 141.512 | 151.312 | 0.108 | 1.618 | 0 | ✓ |
| 2 | k2c_b2 | c03_s01 | 141.376 | 151.204 | 0.104 | 1.730 | 0 | ✓ |
| 3 | k2c_b3 | c05_s01 | 138.920 | 148.748 | 0.104 | 1.790 | 0 | ✓ |
| 4 | k2c_b4 | c07_s01 | 141.612 | 151.440 | 0.112 | 1.818 | 0 | ✓ |
| 5 | k2c_b5 | c09_s01 | 140.884 | 150.700 | 0.116 | 2.143 | 0 | ✓ |
| 6 | k2c_b6 | c11_s01 | 140.448 | 150.276 | 0.108 | 1.529 | 0 | ✓ |
| 7 | k2c_b7 | c00_s02 | 141.248 | 151.084 | 0.108 | 1.641 | 0 | ✓ |
| 8 | k2c_b8 | c03_s02 | 141.140 | 150.968 | 0.108 | 1.800 | 0 | ✓ |
| 9 | k2c_b9 | c05_s02 | 141.064 | 150.888 | 0.108 | 2.317 | 0 | ✓ |
| 10 | k2c_b10 | c07_s02 | 142.152 | 151.976 | 0.116 | 1.933 | 0 | ✓ |
| 11 | k2c_b11 | c09_s02 | 142.744 | 152.580 | 0.116 | 2.592 | 0 | ✓ |
| 12 | k2c_b12 | c11_s02 | 141.708 | 151.540 | 0.108 | 2.224 | 0 | ✓ |

Reprezentatywny epizod (k2c_b1) rozwinięty: `denial@sim141.512` (EKF2_GPS_CTRL→0) → osłona wykrywa `dead_reckoning`, `pos_flag` uzbrojony → `REFUSE(POS_DEGRADED)@+0.108s` → D5: faza szybka (v=1.5 m/s) → przełączenie na v=0.7 m/s @ H_SWITCH_AGL=2.0m → `touchdown@sim151.312` (t_td 9.8s) → `denial_boot_end@sim151.316`. Wychylenie od momentu wstrzyknięcia x_exc=1.618m, koperta R_E=32 nienaruszona.

---

## §4. Raport (−) uzbrojenia — zysk uboczny

Osobno od ścieżki (+): faza NOMINALNA (przed denialem) w każdym z 12 bootów miała **monitor pozycji uzbrojony** (`K2_ARM_MONITOR=1`, ~30s zdrowego lotu z GNSS).

- **Fałszywe REFUSE(POS) w fazie nominalnej: 0 / 12 bootów.** Uzbrojony monitor nie wyzwolił się ani razu na zdrowej pozycji.
- Łącznie z K4b (raport `RAPORT_K4b.md`): ścieżka (−) osłony nie generuje fałszywych odmów pozycyjnych.

Osłona przejmuje **tylko** gdy pozycja realnie degraduje — nie na fałszywym alarmie. Znalezisko zgodne z kryterium dwustronnym K2.

---

## §5. Przyrządy i piny (tożsamość dowodu)

| element | stan |
|---|---|
| wagi NCP | `net/frozen/ncp.npz` sha `0337d5ea` (==FREEZE_NET); `weights_sha` w manifeście każdego bootu |
| osłona (5 pinów) | shield.py `1c584964` · config.py `4c440e42` · gate_run_r03.py `5647ae20` · base.py `7fc45cf2` · **safe_descend.py `e3c1040b`** (D5 współdzielone gate↔ławka) — `check_shield_frozen()`=True |
| sędzia epizodu | `bench/k2_judge.py` frozen `b4ef92ce` (V2′ do T_inj + k1_judge.gt_metrics po T_inj) |
| sędzia ławki | bench_judge V2′ `8ec0fcfb` · features `9adc1505` · scenario_manifest `e0527026` |
| D5 (ekstrakcja) | `safe_descend_step` bit-w-bit vs blok inline gate_run_r03 na 4221 tickach (1791 descending) — ANEKS_K2-2 ceremonia INFRA-3 |

---

## §6. Kanon (K6) i dług

- **K6:** noga PASS (12/12). Ścieżka REFUSE→D5 osłony działa pod kontrolerem uczonym i realnym denialem GNSS; wychylenie ≪ eps_cap, zero przebić, odmowa w budżecie K1.
- **Dług D1** (ANEKS_K2-4 §2): domyślny stan monitora — obecnie `pos_flag=None` gdy brak denialu/braku flagi `K2_ARM_MONITOR`. Po STOP-K2c przełączyć na **armed-by-default** z legacy `K2_LEGACY_UNARMED` (do decyzji CC).
- **Push:** wszystkie commity kampanii (1e58658 → 788bb26) **NIEPUSHOWANE** (push=Olga).

**STOP-K2c** — czekam na ratyfikację werdyktu PASS (12/12) i decyzję o losie slotu / długu D1.
