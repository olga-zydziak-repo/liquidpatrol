# ERRATUM #2 (scope V_MAX) — RAPORT_R03A, RAPORT_D_B5

Data: 2026-08-23. Podstawa: PROMPT_K1 / ANEKS_K1-8 (V4). Format jak `ERRATUM_42M.md` (§0):
adnotacja in-place + ten plik; liczby PO V2–V3, nie przed. Sędzia/osłona NIETKNIĘTE.

## Znalezisko (ANEKS_K1-7 G4 / K1-8 V2–V3)
`V_MAX = 3.0` (`r01/config.py:24`) był **limitem ZADANYM** — norma setpointu velocity
(`vn,ve = VMAX·dx/dist,VMAX·dy/dist`, `k1_arm_n.py:213` / `gate_run_r03.py:291`). Prędkość
**FAKTYCZNA** nie była sprawdzana pomiarem. Twierdzenie zawierania P2-ε (`RAPORT_R03A.md:19`,
`PRE_R03A.md:14/154-156`) opiera się na `d_stop = V_MAX·T_REACT + V_MAX²/(2·A_BRAKE) = 2.85 m`
(`r01/config.py:27`), gdzie `d_stop` = FIZYCZNA droga hamowania → zależy od faktycznej ‖v‖.
Przesłanka „faktyczna ‖v‖ ≤ V_MAX" była **niesprawdzona**. Klasa: defekt SCOPE'u zastosowania
twierdzenia (nie bug K1, nie bug osłony).

## Pomiar (S@0.2 boot3, 4 źródła, ANEKS_K1-8 V2)
| regime | GT (fiz.) | EKF /fmu | ulog vlp | setpoint |
|---|---|---|---|---|
| prosta (offboard approach) | **3.16** | 3.01 | 3.01 | 3.0 |
| **zakręt (corner0 transit, cruise)** | **5.34** | 3.74 | 3.74 | 3.0 |
| takeoff (pre-offboard) [info] | 5.26 | 0.92 | 4.84 | 3.0 |
| descent (post-denial) [poza scope] | 5.79 | 3.74 | 3.74 | 3.0 |
| landing skid [poza scope] | 7.94 | 16.62 | 16.62 | 3.0 |

- Na prostej dron trzyma zadaną (~3.16). **W zakręcie faktyczna GT = 5.34** (transient skrętu; 0.2
  leży w zakręcie, wektor v ∦ noga). **EKF/ulog to TEN SAM estymator** (vehicle_local_position) →
  oba **zaniżają** faktyczną o ~1.6 m/s w zakręcie. Osłona liczy na estymacie → jej margines optymistyczny.
- `r_apex_max` (GT, narożnik-0, jedyny sprzed wstrzyknięcia w tym locie) = **20.654 m** (ideał
  zredukowanej trasy 19.9; R_E=32).
- GT = przyrząd czysty (gładki, fizyczny, spójny między oknami; różnica centralna po cięciwie **zaniża**
  na krzywej → 5.34 jest DOLNYM oszacowaniem faktycznej). Booty K1 injectują w climbie (z~4.5, ALT=8
  nieosiągnięte — znane, ANEKS_K1-4 H2a); brak plateau prostej v_max, ale approach dał czystą prostą 3.16.

## Re-instancjonowanie twierdzenia (ANEKS_K1-8 V3, reguła prerejestrowana)
- `V_true_max` (zakręt, GT) = 5.342 m/s.
- `V_env = ceil((5.342 + 0.5)/0.5)·0.5 = 6.0 m/s`.
- `d_stop(V_env) = 6.0·0.20 + 6.0²/(2·2.0) = 10.2 m` (T_REACT=0.20, A_BRAKE=2.0 — `r01/config.py:25-26`).
- `C_margin = R_E − (r_apex_max + d_stop(V_env)) = 32 − (20.654 + 10.2) = **1.146 m > 0**`.
- **⇒ gwarancja formalna STOI w zmierzonej obwiedni.** K1 biegnie dalej na obecnej dynamice; każdy
  boot: checkpoint `‖v_GT‖_max ≤ V_env=6.0` w manifeście (`vmax_check`); przekroczenie = FLAGA
  (nie unieważnia, §4 bez zmian). Wspierające: realny KOINCYDENTNY `max(r+d_stop(v)) = 23.94 m`
  (margines do R_E = 8.06 m) — worst-case rozłączny (apex-r ⊕ V_env) jest konserwatywny.

## Korekta wcześniejszych liczb
- **RAPORT_R03A**: S4 narożnik `v=3.14 m/s` był ESTYMATĄ EKF; faktyczna GT w narożniku jest wyższa
  (analogicznie do K1, EKF zaniża ~1.6). „min margines zawierania **11.69 m**" policzony z limitem
  **zadanym/estymowanym**, nie faktycznym; przy V_env=6.0 margines analogiczny =
  `32 − (r_est + d_stop(6.0))`. Twierdzenie re-instancjonowane dla V_env (C_margin K1 = 1.146 > 0).
- **RAPORT_D_B5**: dynamika lotu ta sama (offboard velocity, ta sama trasa/limit); „V_MAX=3.0" tam też
  = limit zadany.

## Reguła od teraz (ANEKS_K1-8 V5)
Każda stała wchodząca do twierdzenia jako ograniczenie wielkości FIZYCZNEJ dostaje w manifeście
zmierzone maksimum z biegu + asercję względem obwiedni. **„Limit zadany ≠ limit faktyczny"** dołącza
do **„asercja ≠ pomiar"**.
