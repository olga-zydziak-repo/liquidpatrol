# RAPORT K4b — 3 booty nominalne z uzbrojonym monitorem POS (ANEKS_K2-1 K4b) — PASS

LiquidPatrol · K2 · ramię (−) toru POS: nominał z UZBROJONYM monitorem (bez denialu). Kryterium: 0 fałszywych REFUSE(POS).

## Wynik
| boot | komórki | k2_arm_monitor | epizody | REFUSE(POS) | REFUSE_all | breach | certs_rc |
|---|---|---|---|---|---|---|---|
| k4b_b1 | c00-c03_s01 | True | 4 | 0 | 0 | 0 | 0 |
| k4b_b2 | c04-c07_s01 | True | 4 | 0 | 0 | 0 | 0 |
| k4b_b3 | c08-c11_s01 | True | 4 | 0 | 0 | 0 | 0 |
| **RAZEM** | 12 komórek | **3/3** | **12** | **0** | 0 | 0 | 0 |

## Ustalenia
- **Monitor POS uzbrojony (pos_flag=dr od wejścia w pasmo) w 3/3 bootach** — potwierdzone z meta trace (k2_arm_monitor=True); wszystkie epizody weszły w pasmo (t_entry 2.5-2.9 s), więc monitor był aktywny w fazie orbity.
- **0 fałszywych REFUSE(POS) w 12 epizodach** przy zdrowym GPS (dead_reckoning=False → pos_flag=False → osłona nie odmawia). **KRYTERIUM K4b PASS.**
- 0 breach, 0 REFUSE jakiegokolwiek typu, certs_selfcheck_rc=0 (B5) we wszystkich.
- **P-K2-5** (0 fałszywych REFUSE w nominale z uzbrojonym monitorem, p≈0.8): **TRAFIONE.**
- Luka B3 (monitor nieuzbrojony bez denialu) domknięta flagą `K2_ARM_MONITOR` (commit a5b15d3, harness) — wymóg K4b PRE_K2 spełniony; nominał bez flagi pozostaje identyczny.

## Nota
Ramię (−) K4b (0/12 z uzbrojonym monitorem) raportowane OSOBNO od bazy lotów NCP 0/84 (tam monitor był NIEUZBROJONY — bez wartości dowodowej dla toru POS, ANEKS_K2-1 §1). K4b jest właściwym ramieniem (−) toru POS.

## STOP — czeka na CC
Po raporcie K4b + linii CC → sygnał „ANEKS_K2-3: kampania go" (12 ep kryterialnych). UWAGA: eps_cap kryterialny wciąż do ustalenia (PRE/K1) — w k2_judge argument, nie zaszyty.
