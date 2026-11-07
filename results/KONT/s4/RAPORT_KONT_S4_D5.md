# RAPORT_KONT_S4_D5 — diagnoza inicjalizacji estymatora przy biurku (ANEKS_KONT-4c §2): werdykt **W-R**, 0 bootów

Wykonawca · 8.11.2026 · łańcuch KONT. Narzędzie i dane: `results/KONT/s4/d5diag/kont_d5diag.py`, `d5diag.json` (wszystko
z ulogów; błąd yaw = yaw `vehicle_attitude` − yaw `vehicle_attitude_groundtruth`, oba z PX4; czas = sim).

**Wynik jednym zdaniem:** przy dołączeniu PX4 około 7.5 s czasu symulacji estymator w części bootów startuje
z biasem żyroskopu ponad 0.08 już w pierwszej próbce i traci fuzję kierunku z magnetometru; reinit EKF2
(`px4-ekf2 stop` → `start`, watchdog) czyści bias i heading w 3/3 przypadkach, w których się wydarzył.

## §1. Zestawienie (pkt 1–3)

| boot | grupa | initial abs. time | bias max 30 s | `cs_mag_hdg` | reinit watchdoga | błąd yaw przed → po reinicie | błąd yaw przed uzbr./asercją |
|---|---|---|---|---|---|---|---|
| nom_b1 | S4 | 7.604 s | 0.150 | 1→0 przy 11.1 s, 1 przy 15.3 s | 64.5 s, bias 0.150→0.0002 | **93.4° → 6.36°** | (driver padł) |
| nom_b1_r2 | S4 | 7.448 s | 0.130 | 1→0 przy 14.8 s, bez powrotu | brak (próg SLOW nie zaszedł) | — | **51.6° (75.1° przy końcu)** |
| nom_b2 | S4 | 7.496 s | 0.150 | 1 od 9.3 s | brak (próbki ≤ 0.073 od 11 s) | — | **13.3°**, płasko |
| c11_s04_r3 | S2-Y | 7.420 s | 0.150 | 1→0 przy 10.4 s, 1 przy 69.0 s | 64.0 s, bias 0.125→0.0002 | **141.5° → 6.37°** | 6.43° |
| c08_s02b_r2 | S2-Y | 7.504 s | 0.0001 | 1 od 9.1 s | brak | — | 6.42° |
| c02_s01_r4 | S2-Y | 7.440 s | 0.0002 | 1 od 9.6 s | brak | — | 6.38° |
| c00_s02_r3 | S2 | 7.496 s | 0.150 | 1→0 przy 14.0 s, 1 przy 69.3 s | 64.7 s, bias 0.128→0.0002 | −1.0° → 6.38° | 6.42° |
| SKAN2 bA_c08 | stary launcher | 1.112 s | 0.0003 | 1 od 2.8 s | brak | — | 6.32° |
| SKAN2 bB_c1011 | stary launcher | 0.420 s | 0.0003 | 1 od 2.6 s | brak | — | 6.45° |
| PERC2 bA_c08 | stary launcher | 0.112 s | 0.0003 | 1 od 2.9 s | brak | — | 6.54° |
| PERC2 bB_c1011 | stary launcher | 1.092 s | 0.0003 | 1 od 2.8 s | brak | — | 6.28° |

- **Pkt 1 (yaw(t)):** w bootach zdrowych błąd stoi na 6.3–6.5° (stały offset GT–EKF, ta sama wartość w obu
  launcherach — poziom odniesienia asercji). W złych bootach yaw EKF stoi płasko na błędnej wartości (nom_b2: rozrzut
  < 1° w 30 s przed asercją) albo dryfuje (nom_b1_r2: 51.6° przy asercji, 75.1° na końcu logu). Każdy reinit przywrócił
  6.36–6.38°.
- **Pkt 2 (magnetometr):** `EKF2_MAG_TYPE` 0, `EKF2_MAG_CHECK` 1, `EKF2_MAG_CHK_STR` 0.2, `EKF2_DECL_TYPE` 3,
  `SYS_HAS_MAG` 1 we wszystkich bootach (z `initial_parameters`). `cs_mag_fault` 0 wszędzie. W 4/5 złych bootów fuzja
  kierunku z magnetometru (`cs_mag_hdg`, razem z `cs_mag_heading_consistent`) gaśnie w 10–15 s i wraca dopiero po
  reinicie; nom_b2 ma `cs_mag_hdg`=1, a mimo to błąd 13.3° stoi płasko. Mechanizm wewnętrzny filtra:
  [MECHANIZM NIEZMIERZONY].
- **Pkt 3 (faza):** zły start (bias > 0.08 w pierwszej próbce `estimator_sensor_bias`, t ≈ 7.9–8.1 s) w **5/9** bootów
  nowego launchera (dołączenie 7.42–7.60 s) i **0/4** bootów starego launchera (0.11–1.11 s). Związek z fazą
  dołączenia jest zgodny z hipotezą 4c §2.3, ale przy n = 9/4 to korelacja, nie mechanizm. Pierwsze próbki
  `sensor_combined`/`vehicle_imu` w tabeli JSON.

## §2. Pkt 4 — tor S4 wykluczony pomiarem

Bias > 0.08 pojawia się w pierwszej próbce estymatora: nom_b1_r2 przy t = 7.9 s, nom_b2 i nom_b1 przy 8.1 s,
c11_s04_r3 przy 7.9 s. Driver S4 startuje po settle 90 s, a kontrola yaw odbywa się przy 109.5 s (nom_b1_r2)
i 111.5 s (nom_b2). Stan estymatora jest więc zepsuty około 100 s przed pierwszą instrukcją drivera (preflight,
selfcheck, intruder_motion) — żadna różnica toru S4 względem S2 nie może być przyczyną. Ten sam zły start wystąpił
w S2 (c11_s04_r3, c00_s02_r3), gdzie naprawił go reinit watchdoga przed uzbrojeniem.

Dlaczego watchdog nie zadziałał w nom_b1_r2 i nom_b2: jego trigger SLOW wymaga |bias| > 0.08 bez spadku przez 30 s
po 60 s sim, a w tych bootach bias spadł poniżej 0.08 w próbkach watchdoga (od 11 s: 0.107→0.070, ≤ 0.073), podczas
gdy błąd yaw pozostał. Sam próg biasu nie wykrywa zepsutego headingu — potrzebna jest kontrola yaw.

## §3. Werdykt

**W-R** (4c §2): reinit EKF2 czyści heading i bias — 3/3 reinity w danych (nom_b1 93.4° → 6.36°, c11_s04_r3
141.5° → 6.37°, c00_s02_r3 → 6.38°; bias 0.125–0.150 → 0.0002). Mitygacja §3 wchodzi w życie: wymuszony reinit
(`do_reinit` z `tools/infra2_ekf_watchdog.py:134`, ten sam kod importem), oczekiwanie na konwergencję, kontrola
|błąd yaw| ≤ 10° i |bias| < 0.08 (`BIAS_SLOW` watchdoga) przed `intruder_motion`, maks. 2 podejścia.

Zastrzeżenie: n = 3 reiniterów, wszystkie po zepsutym starcie; reinit w boocie zdrowym nie był obserwowany (ryzyko
odwrotne — reinit psujący dobry start — niezmierzone; asercja yaw pozostaje bramką).
