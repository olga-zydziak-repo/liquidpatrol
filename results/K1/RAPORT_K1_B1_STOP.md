# RAPORT_K1 — cap B1: trzeci kolejny env-fail na (S,0.2) ⇒ K1 STOP

LiquidPatrol · noga K1 · ANEKS_K1-14 (PROMPT_K1_RETRY) · sesja po `wsl --shutdown` · 2026-08-24

## Werdykt

Trzy kolejne env-faile (arm-fail na health-failures) na punkcie (S,0.2):
**boot4 → boot5 → boot6**. Osiągnięty kap **B1** (§2.B) ⇒ **K1 STOP**.
Retry §1 wykonany dokładnie raz (boot6), zgodnie z M3/S1. Zero prób hartowania
(M5/S2): settle 90 s i arm_retry 40× nietknięte, żaden parametr PX4 nie tknięty.

## Trzy env-faile — dowód (cytaty, SR-K6)

Wszystkie trzy: `act.log` → `ARM FAILED — boot niezdatny (retry przez wrapper)`
po 40 retry; `px4.log` → 40× `Arming denied: Resolve system health failures first`.
`run_valid=None`, `habitat=INVALID(habitat)`, `judge=skipped` (brak denial_on/t_inj_sim).
Boot legalny: `b4` orphany 0/0, `one_boot_per_cycle=true`, `certs_selfcheck` PASS rc=0,
shield+k1_judge frozen (piny OK), timejump 0/0, headless (GUI brak). Problem NIE w kodzie —
w niezbieżności EKF/nav-health przy starcie.

| boot | arm-denied | High Gyro | High Accel | horiz.vel unstable | ekf2 missing | Baro invalid | ekf_hits | cooldown[s] |
|------|-----------:|----------:|-----------:|-------------------:|-------------:|-------------:|---------:|------------:|
| boot4 | 40 | 1 | 2 | 0 | 1 | 1 | 1 | 3483 |
| boot5 | 40 | 6 | 2 | 3 | 1 | 1 | 9 | 313 |
| boot6 | 40 | 4 | 1 | 1 | 1 | 1 | 5 | 2139 |

Diagnoza (§2.B oczekiwana, potwierdzona): **High Gyro/Accelerometer Bias**,
**horizontal velocity unstable**, + `ekf2 missing data` / `No valid data from Baro 0`
/ `No connection to GCS` — klasyczna niezbieżność EKF2 i czujników w oknie preflight.

## Stan maszyny (boot6, §0.4, z manifestu)

- `mem_free ≈ 27.3 GB` (`mem_available ≈ 29.7 GB`) — pamięć NIE jest wąskim gardłem.
- **`loadavg = [18.15, 18.32, 14.45]`** (1/5/15 min) — obciążenie ~18 utrzymane przez
  całe okno bootu. To jedyny wyróżnik środowiska po restarcie WSL.
- `session_boot_count=1`, `env_restart=wsl-shutdown`.

Hipoteza (NIE weryfikowana w tej sesji — to materiał zadania infra): wysoki load
po `wsl --shutdown` wydłuża/rozstraja konwergencję EKF w oknie 90 s → intermittent
arm-fail. mem_free wyklucza głód pamięci; przyczyna po stronie CPU-contention/harmonogramu.

## Budżety i liczniki po sesji

- **(S,0.2): 1/3 przeleciany, 2 zostają** (bez zmian — env-faile nie konsumują budżetu, `run_valid=None`).
- Streak env-fail (S,0.2): **3/3 kolejne → cap B1 osiągnięty**.
- (N,0.2): 2/3; N boot4 = ważny kandydat pary (nietknięty).
- Licznik dstop FAIL: 1/3 (bez zmian — brak lotu).

## Czego NIE zrobiono (dyscyplina M-rule)

- Zero strojenia settle/arm_retry/parametrów PX4 (M5/S2).
- Dokładnie jeden boot lotny w sesji (M3/S1).
- Jedyna zmiana kodu: `k1/k1_finalize.py` — warstwa manifestu §0.4
  (`session`: mem_free/load/session_boot_count/env_restart). Sędzia i piny nietknięte.

## Następny krok (poza tą sesją)

Zadanie infrastrukturalne wg **M4** — hartowanie bootu + bramka 9/10 pustych bootów —
wchodzi WYŁĄCZNIE osobnym dokumentem CC po tym raporcie. Ta sesja go nie otwiera.
