# ANEKS_K1-1 — instrumentacja K1 zamrożona (§3.1 diff · §3.2 sędzia · §3.3 agregat)

PRE_K1 §3 · 2026-08-22 · **przed pierwszym bootem.** Erratum §0 = commit `5a6a18d`.
Ten aneks zamraża łańcuch pomiarowy K1 hashami. Po pierwszym biegu: nic w sędzim/agregacie/progach
się nie zmienia (SR-K3; poprawka błędu = nowy hash + jawne przeliczenie wszystkich biegów).

## §3.1 — diff plików łańcucha mechanizmu, v1.16.0 → v1.16.2

PX4 stoi na **v1.16.2** (`git -C PX4-Autopilot describe` = v1.16.2, HEAD `54f0455`), zgodnie z PRE §1.
Diff wykonany na zestawie plików cytowanych w §1 (ścieżki v1.16.2; część nazw z pamięci v1.16.0
była nieaktualna — skorygowane poniżej):

| element mechanizmu (PRE §1) | plik v1.16.2 | diff 1.16.0→1.16.2 |
|---|---|---|
| `valid_timeout_max` = 5 s (5'000'000 µs) | `src/modules/ekf2/EKF/common.h:482` | **bez zmian** |
| gaśnięcie xy-aiding po timeout | `src/modules/ekf2/EKF/ekf_helper.cpp:880,906` | **bez zmian** |
| `xy_valid` / stan estymatora | `src/modules/ekf2/EKF/ekf.h` | zmiana JEST, **nie dotyka** xy_valid/valid_timeout (patrz niżej) |
| `local_position_invalid_relaxed` (dawniej „EstimatorChecks.cpp") | `src/modules/commander/HealthAndArmingChecks/checks/estimatorCheck.cpp` | **bez zmian** |
| warunek trybu AUTO_LAND | `src/modules/commander/ModeUtil/mode_requirements.cpp` | **bez zmian** |
| fallback DESCEND | `src/modules/commander/failsafe/framework.cpp` | **bez zmian** |
| „blind land" (kontroler pozycji) | `src/modules/mc_pos_control/MulticopterPositionControl.cpp` | **bez zmian** |

**Jedyna różnica w całym łańcuchu** — `ekf.h`, sygnatura `fuseDirectStateMeasurement` dostaje parametr
`constrain_variances=true` (strażnik rekurencji przy `constrainStateVariances`). Zweryfikowane: hunk
**nie dotyka** `xy_valid`, `isLocalHorizontalPositionValid`, `valid_timeout_max` (grep hunka = 0 trafień).
Zmiana ortogonalna do ścieżki utrata-GNSS → xy_valid → failsafe → DESCEND → blind-land.

**Wniosek §3.1:** mechanizm z PRE §1 (czytany z v1.16.0) stoi bajtowo na v1.16.2. Zero uzupełnień
cytatów wymaganych przed biegami. (Korekta nazw: `EstimatorChecks.cpp`→`estimatorCheck.cpp`,
`mc_pos_control.cpp`→`MulticopterPositionControl.cpp` — to renamy między wersjami, nie zmiany logiki.)

## §3.2 — sędzia `k1_judge.py` ZAMROŻONY

```
sha256(k1/k1_judge.py) = 36c7c22acf9eac7605c9e70d160d783b6c5c2dd8a1bee8cb6360af1fc0517048
```
Metryki per bieg (GT z gz sim-time + ulog PX4): `r_max`, `r_td`, `x_exc`, `t_td`, `breach (r_max>R_E)`,
sekwencja `nav_state` z czasami (`vehicle_status`), `t_xy_valid_off` (`vehicle_local_position.xy_valid`),
`t_dead_reckoning_on` (`estimator_status_flags.cs_inertial_dead_reckoning`), ack `NAV_LAND`
(`vehicle_command_ack`, cmd=21); ramię S: `t_refuse`, `ε_pos_touchdown` (EKF↔GT, swap ENU→NED).
`R_E` importowane z `r01/config.py` (asercja =32.0). Pin ulog→sim: `--px4-inj-us` lub ack NAV_LAND (N, δ=0).

**Unit-test (`--selftest`) PASS:** syntetyczna trajektoria GT z podstawionym home i skewem osi sim —
`r_max`/`r_td`/`x_exc`/`inj_xy` niezmiennicze względem skewu, `t_td` po regule touchdown (z≤0.5 m),
estymacja home z okna nieruchomego, `breach` TRUE gdy `r_max>32`. Smoke-test `read_ulog` na realnym
ulogu (`2026-08-21/15_41_05.ulg`): topiki i pola parsują się, `nav_state∈{4,5,14,18}`, snapshot
parametrów (`EKF2_GPS_CTRL=7`, `COM_POS_LOW_ACT=3`, …) czytany.

## §3.3 — agregat `k1_aggregate.py` ZAMROŻONY

```
sha256(k1/k1_aggregate.py) = b576fa7ba628f596908b0780bd586f61f10719bb61e44fa127d7fe8d0523e334
```
Parowanie po punkcie (N vs S), tylko 5 punktów kryterialnych prostej `{0.2,0.35,0.5,0.65,0.8}`
(informacyjne `info`/`is_corner` wykluczone). Liczy `breach_N`, `breach_S`, `Δx_exc=N−S` per punkt,
`mediana(Δ)`, `pooled_std` (odchylenie std Δ po punktach, ddof=1), `IQR(Δ)`, i **werdykt §4**:
(−) breach_S≥1 (pierwszeństwo, STOP) · (+) breach_S=0 ∧ breach_N≥1 ∧ med>pstd · (±) breach_N=breach_S=0
∧ med>pstd · (0) breach_N=0 ∧ |med|≤pstd (śmierć pozycji 1) · MIXED (inaczej).

**Unit-test (`--selftest`) PASS:** wszystkie 5 gałęzi werdyktu na syntetycznych wynikach +
wykluczenie informacyjnych.

## Status bramy startu biegów

- Erratum §0: commit `5a6a18d` ✔
- Sędzia + agregat zamrożone hashami (ten aneks) ✔ — po commicie tego aneksu brama SR-K2 spełniona.
- §3.1 diff: mechanizm stoi na v1.16.2 ✔ — brak uzupełnień przed biegami.

**Dopiero po commicie tego aneksu wolno bootować.** Push = Olga.
