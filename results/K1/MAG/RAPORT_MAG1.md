# RAPORT_MAG1 — forensyka trybu „Strong magnetic interference" (offline, zero bootów)

CC, 27.08.2026. Read-only na artefaktach K1 (ulogi + logi + źródło PX4 v1.16.2 `54f0455`).
Zero zmian kodu. Zero bootów. Sędzia/osłona/piny NIETKNIĘTE.

---

## F2 — Cytat źródła: co wyzwala „Strong magnetic interference"

**Warstwa raportująca** — `src/modules/commander/HealthAndArmingChecks/checks/estimatorCheck.cpp:196–223`:

```cpp
if ((_param_com_arm_mag_str.get() >= 1)
    && (!context.isArmed() && estimator_status.pre_flt_fail_mag_field_disturbed)) {
    ...
    mavlink_log_critical(reporter.mavlink_log_pub(), "Preflight Fail: Strong magnetic interference");
}
```

Wielkości logowane: `mag_strength_gs` vs `mag_strength_ref_gs` (± `EKF2_MAG_CHK_STR`),
`mag_inclination_deg` vs `mag_inclination_ref_deg` (± `EKF2_MAG_CHK_INC`).

**Warstwa decydująca** — `src/modules/ekf2/EKF/aid_sources/magnetometer/mag_control.cpp:496–556`
`Ekf::checkMagField()` ustawia `_control_status.flags.mag_field_disturbed`:

```cpp
_mag_strength = mag_sample.length();                    // mag_sample = SUROWE − CAL_MAG offset
if (STRENGTH bit) {
  if (finite(_wmm_field_strength_gauss))
    if (!isMeasuredMatchingExpected(_mag_strength, _wmm_field_strength_gauss, mag_check_strength_tolerance_gs))
      mag_field_disturbed = true;                       // |zmierzone − WMM| > tol
}
```
`isMeasuredMatchingExpected(m,e,g) = (m>=e−g) && (m<=e+g)`. Zdrowie wraca dopiero po
`min_mag_health_time_us` bez dysturbacji (histereza, linia 551–555).

**Zmierzona wielkość:** długość SKORYGOWANEGO wektora mag (surowe − `CAL_MAG*OFF`) vs
referencja WMM. **Próg** (parametry z ulogu S@0.65 b2): `EKF2_MAG_CHECK=1` (tylko STRENGTH),
`EKF2_MAG_CHK_STR=0.20 Gs`, `COM_ARM_MAG_STR=2`.

> Niuans: `COM_ARM_MAG_STR=2` ⇒ w `estimatorCheck.cpp:201` `required_groups_mag=NavModes::None`
> (check formalnie OPCJONALNY). Ale `mavlink_log_critical` „Preflight Fail" pada zawsze, a
> `mag_field_disturbed=true` INHIBUJE fuzję mag w EKF → degraduje yaw/atitude/height. Mag jest
> więc i objawem, i przyczyną górną współwystępujących fault-ów.

---

## F1 — Strumień zmierzony (estimator_status), clean vs fail

`ulog2csv -m estimator_status`; okno preflight (0→~120 s), wiersze z `strength>0`:

| miara | clean (S@0.5 b1, YOFF −0.1417) | fail (S@0.65 b2, YOFF −0.1506) |
|---|---|---|
| `mag_strength_gs` mean | 0.2587 | 0.2789 |
| `mag_strength_ref_gs` mean (WMM) | 0.4780 | 0.4747 |
| wiersze `\|meas−ref\|>0.20` (tol) | **12.6 %** | **88.9 %** |
| `pre_flt_fail_mag_field_disturbed==1` | **0 / 12076 (0 %)** | **12570 / 14249 (88.2 %)** |

Referencja WMM stabilna (~0.478 w obu). Zmienia się SKORYGOWANA siła zmierzona: offset
kalibracyjny przesuwa rozkład tak, że w fail-boocie 89 % preflight-u przekracza bramkę 0.20 Gs
w sposób TRWAŁY (histereza `min_mag_health_time` przekroczona) → `mag_field_disturbed`.
⇒ **dane surowe nie są „skażone fizyką" — dryfuje korekta z persystowanego CAL_MAG.**

---

## F3 — Audyt trwałości między bootami (kandydat główny)

### (a) Pliki stanu przeżywające boot (rootfs)
```
parameters.bson         852 B  mtime 08-27_01:41   ← zawiera CAL_MAG0_{X,Y,Z}OFF, EKF2_MAG_DECL
parameters_backup.bson  852 B  mtime 08-27_01:41
dataman              1.2 MB    mtime 08-05_13:35   (stały, nieistotny)
eeprom/              pusty                          (nieistotny)
```
`strings parameters.bson` ⇒ obecne `CAL_MAG0_XOFF/YOFF/ZOFF`. mtime 01:41 leży MIĘDZY
S@0.65 b1 (01:26) a b2 (01:44) ⇒ plik zapisywany w trakcie serii (commit paramów na disarm/shutdown).

### (b) Czy harness czyści? — **NIE.**
`grep parameters.bson|param_reset|CAL_MAG|rm .*bson` po `k1/*.sh k1/*.py tools/infra1_*.py` = **0 trafień**.
Jedyna higiena paramów: `acts/ensure_gps_enabled.py` resetuje WYŁĄCZNIE `EKF2_GPS_CTRL→7`
(B5R3). `CAL_MAG*` nie jest dotykane nigdy — persystuje 1:1 z bootu na boot.

### (c) Diff CAL_MAG w czasie sesji — **PEŁZA MONOTONICZNIE + ZATRZASKUJE:**

| boot | data | CAL_MAG0_YOFF | ZOFF |
|---|---|---|---|
| S 0.2 b1 | 08-22 | −0.1026 | 0.1401 |
| S 0.2 b7 / b99 / S 0.35 b1 | 08-26 17–18h | −0.1369 | 0.1544 |
| S 0.35 b2 / S 0.5 b1,b2 / N 0.35 / N 0.5 b1,b2 | 08-26 19–20h | −0.1417 | 0.1546 |
| **N 0.5 b3,b4 · S 0.5 b3 · S 0.65 b1,b2** | **08-26 23h→08-27** | **−0.1506** | 0.1547 |

Wartości IDENTYCZNE między kolejnymi bootami danego przedziału = czytane z `parameters.bson`,
nie estymowane od zera. EKF2 uczy biasu mag w locie i zapisuje (`EKF2::UpdateMagCalibration`,
`EKF2.cpp:2714`; `_mag_cal.cal_available`) → param store → następny boot ładuje narosłą wartość.

### (d) Era R0.3a / DEMO-B
Ten sam `parameters.bson` (backup `parameters.bson.pre5r3_backup` z 08-17) — mechanizm persystencji
istnieje od dawna, nigdy nie czyszczony. Różnica: kampania K1 robi WIELE cykli arm/lot na sesję
(E1d 10 bootów + seria punktów), więc offset przekracza bramkę `checkMagField` dopiero teraz.
Wcześniejsze ery = mniej cykli/sesję ⇒ nie dobił do progu.

---

## F4 — Tabela pozycji sesyjnej (korelacja liczbą)

| boot | mtime | CAL_MAG0_YOFF | arm | mag-fail | wd_reinits |
|---|---|---|---|---|---|
| S 0.2 b99 | 08-26 17:36 | −0.1369 | ARM (rv=T) | no | 1 |
| S 0.2 b7 | 08-26 18:02 | −0.1369 | ARM (rv=T) | no | 1 |
| S 0.35 b1 | 08-26 18:57 | −0.1369 | ARM (rv=F, diag) | no | 0 |
| S 0.35 b2 | 08-26 19:14 | −0.1417 | ARM (rv=T) | no | 1 |
| N 0.35 b1 | 08-26 19:30 | −0.1417 | ARM (rv=T) | no | 1 |
| S 0.5 b1 | 08-26 19:49 | −0.1417 | ARM (rv=T) | no | 0 |
| N 0.5 b1 | 08-26 20:06 | −0.1417 | ARM (rv=T) | no | 0 |
| N 0.5 b2 | 08-26 20:23 | −0.1417 | ARM (rv=T) | no | 1 |
| S 0.5 b2 | 08-26 20:40 | −0.1417 | ARM (rv=F, diag) | no | 0 |
| **N 0.5 b3** | 08-26 23:40 | **−0.1506** | **DENY** | **YES** | 1 |
| **N 0.5 b4** | 08-26 23:59 | **−0.1506** | **DENY** | **YES** | 1 |
| **S 0.5 b3** | 08-27 01:08 | **−0.1506** | **DENY** | **YES** | 1 |
| **S 0.65 b1** | 08-27 01:26 | **−0.1506** | **DENY** | **YES** | 1 |
| **S 0.65 b2** | 08-27 01:44 | **−0.1506** | **DENY** | **YES** | 1 |

**Separacja perfekcyjna przy YOFF ≈ −0.1506:** 9/9 bootów z |YOFF|≤0.1417 → mag-fail 0, arm OK;
5/5 bootów z YOFF=−0.1506 → mag-fail YES, arm DENY. Korelacja(mag-fail, YOFF≥próg) = **1.0**.
Dwa rv=False (diag) to preinj/flight-quality-drift, NIE mag — spójne.

Na fail-boocie (S@0.65 b2) ranking Preflight Fail: **Strong magnetic interference 58× (dominant)**,
No connection GCS 42× (artefakt braku arm), High Gyro Bias 20×, height not stable 6×, attitude 2×.
Watchdog zrobił reinit (n_reinits=1) — uratował gyro, ale `ekf2 start` **przeładowuje ten sam
persystowany CAL_MAG** ⇒ mag NIE do naprawienia reinitem (strukturalna granica watchdoga).

---

## F5 — WERDYKT

**Stan trwały między bootami:** narastający offset kalibracji magnetometru
(`CAL_MAG0_{X,Y,Z}OFF`) uczony w locie przez EKF2 i zapisywany do `parameters.bson`, którego
harness NIGDY nie czyści, pełza przez sesję i po ~sesji cykli arm/lot przekracza bramkę siły pola
`checkMagField` (|zmierzone − WMM| > `EKF2_MAG_CHK_STR`=0.20 Gs) przy YOFF≈−0.1506, dając trwałe
`mag_field_disturbed` → „Strong magnetic interference"; **ten sam gatunek co zatrzask biasu
żyroskopu — persystowany stan estymatora, nie fizyka — i z tego samego powodu NIEuleczalny przez
watchdog** (ekf2 stop/start przeładowuje ten sam persystowany CAL).

### PROPOZYCJA interwencji (NIE wdrożona — do ratyfikacji)
Higiena CAL_MAG przed bootem, dokładnie w formie już istniejącej `ensure_gps_enabled.py`
(przed-lotowo, symetrycznie S∧N∧E, ZERO dotyku sędziego/osłony/pinów/segmentu roszczenia):

- **Wariant B (baseline, preferowany):** przywróć `CAL_MAG0_*OFF` do zamrożonej migawki z
  wczesnego CZYSTEGO bootu (np. profil S@0.2 b7, arm-OK) przed każdym bootem. Bezpieczniejszy niż
  zerowanie — zachowuje kalibrację która armowała.
- **Wariant A (zero):** `CAL_MAG0_*OFF→0`. Ryzyko: świeży SITL może SAM wywołać mag-fail bez
  kalibracji → nowy tryb.

### Test PRZED użyciem (lekcja I2b — deadlock, który rewertowaliśmy P0a)
Interwencji NIE włączać do serii bez dowodu, że nie wprowadza NOWEGO trybu:
1. **Offline sanity:** wpisz baseline do `parameters.bson`, 1 boot E-branch (pusty) → sprawdź
   (a) mag-fail znika, (b) gyro/height niezależnie zdrowe, (c) brak nowego env-fail.
2. **Bramka wznowienia:** 2–3 booty z higieną CAL muszą armować bez mag-fail (i bez regresji
   innego trybu), zanim wznowimy 0.65/0.8. Jeśli którykolwiek wprowadzi nowy fault → REVERT,
   osobna rozmowa (jak I2b).
3. Symetria ramion, wyłącznie przed-lotowo; `k1_judge`/`shield`/piny/S∧N bez zmian.

### Zastrzeżenia wykonawcy (verbatim)
- `COM_ARM_MAG_STR=2` czyni check mag formalnie opcjonalnym; nie dowodzę, że mag jest JEDYNYM
  twardym blokerem arm — współwystępują gyro(20×)/height(6×). Dowodzę, że mag jest DOMINUJĄCYM
  objawem (58×) i górną przyczyną przez inhibicję fuzji, oraz że jego korzeń = persystowany CAL.
- Separacja F4 jest obserwacyjna (n=14 bootów, 1 sesja); próg −0.1506 to granica empiryczna tej
  sesji, nie stała fizyczna.
- Skok YOFF −0.1417→−0.1506 nastąpił w luce 20:40→23:40 (booty 0.5 dopalenie) — dokładny boot
  przekroczenia progu nie jest w tej próbie (brak ulogów pośrednich).

Artefakty: ta analiza; CSV w scratchpadzie (nietrwałe). Zero commitów kodu.
