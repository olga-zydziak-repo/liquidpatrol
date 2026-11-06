# RAPORT_KONT_S2d — D3 PASS, potem STOP-KONT2-PRZESKOK (R-5): „przeskok” to restart EKF2 przez watchdog na ziemi, 47.7 s przed startem; loty 4/8 lub 5/8, do decyzji CC

**D3 PASS: `c11_s03_r4` wstał w rozgrzanej sesji, bez restartu WSL i bez sprzątania SHM.** Po nim kolejne dwa booty też wstały: 3/3 z launcherem s2d wobec 14/14 FAIL ze starym. Kolejka zatrzymała się na twardym STOP z R-5 po `c00_s02_r3`, zgodnie z literą. Nie ruszam dalej, czekam na dokument CC.

**Werdykt S2 według PRE §4: BRAK.** Mniej niż 8 lotów, zamrożenia nie było. Liczby poniżej to opis.

## 1. Korekty z ANEKS_KONT-1d

- **Budżet:** boot `c11_s03_r3` nieliczony (§2.1), więc `kampania_d.json` z 3/12 pozostaje dowodem, a poprawny stan przed tą kolejką to 2/12.
- **Etykieta r3:** „FAIL D3 przy initial absolute time < 500 000 µs = test niewykonany, STOP-KONT2c z tą etykietą, bez przejścia na restart WSL” (ANEKS_KONT-1d §2.4).
- **Próba na sucho:** PASS, `results/KONT/s2/stack_dryrun/`, 0 bootów.

## 2. Booty

| boot | nazwa | initial absolute time | sensor_combined | sonda | n_frames | wynik |
|---|---|---|---|---|---|---|
| 3/12 (nr 17) | `c11_s03_r4` (D3) | 7 424 000 µs | 63 814 | PASS | 3925 | **D3 PASS, lot ważny** |
| 4/12 (nr 18) | `c08_s04_r3` | 7 496 000 µs | 62 458 | PASS | 3852 | lot ważny |
| 5/12 (nr 19) | `c00_s02_r3` | 7 496 000 µs | 62 413 | PASS | 3878 | ważny wg analizy, **STOP R-5** |

| lot | ε(0⁺) p95 | ε 10 s | ε 20 s | ε 30 s | ε 60 s | ε 70 s | ε max | Δ max | r_GT max | reinit EKF2 |
|---|---|---|---|---|---|---|---|---|---|---|
| `c08_s02a_r2` | 0.030 | 0.80 | 1.34 | 1.06 | 1.25 | 1.83 | 1.93 | 1.03 | 22.71 | 0 |
| `c11_s02_r3` | 0.016 | 2.01 | 0.83 | 0.83 | 1.03 | 1.57 | 2.01 | 0.95 | 25.13 | 0 |
| `c11_s03_r4` | 0.077 | 0.57 | 1.54 | 0.35 | 1.52 | 2.36 | 2.49 | 0.76 | 25.90 | 0 |
| `c08_s04_r3` | 0.063 | 1.00 | 2.06 | 2.12 | 0.92 | 0.50 | 2.46 | **2.80** | 25.05 | 0 |
| `c00_s02_r3` | 0.040 | 1.52 | 1.86 | 1.22 | 3.67 | 3.48 | **4.02** | 0.76 | 23.26 | **1** |

Wartości w metrach. Wszystkie: xy_valid całe okno, nav 14 do przyziemienia, zejście z końca okna, breach 0, REFUSE 0, V2′ 0.94–0.96, zegar 0 skoków. Fazy: loty 1–2 przy 16/20 ms, kolejne przy 7.4–7.5 s.

## 3. Hipoteza fazy: co pokazuje D3, a czego nie

- **Pokazuje:** 3/3 bootów s2d wstało na tym samym, rozgrzanym stanowisku, które wcześniej dawało FAIL. Pozostałości SHM były na miejscu.
- **Nie rozdziela dwóch rzeczy:** launcher zmienia jednocześnie kolejność startu (gz przed PX4) i fazę dołączenia. Faza wyszła 7.4–7.5 s, nie ok. 0.5 s. D3 nie odróżnia więc „faza ≥ 0.5 s” od „gz już stoi, gdy PX4 startuje”, a próg 0.5 s nie jest zmierzony.
- **Mechanizm wewnątrz PX4 nadal niezmierzony.**
- **Korekta RAPORT_KONT_S2b §2:** `ekf2 missing data` nie jest już wyróżnikiem awarii. Pojawia się przy starcie we wszystkich 3 bootach s2d, a potem EKF2 rusza. Wyróżnikiem zostaje urwany `sensor_combined`.

## 4. STOP-KONT2-PRZESKOK: co się stało w `c00_s02_r3`

**Zmierzone:**

- `infra2_ekf_watchdog` wykonał **REINIT #1** (`SLOW_bias>0.08_no_decrease_30s`) przy sim 64.7 s: `ekf2 stop` + `ekf2 start`, bias 0.128 → 0.00017.
- Przy 66.72 s w `estimator_status_flags` spadają **wszystkie** flagi naraz: gnss_pos, gnss_vel, opt_flow, baro, tilt, yaw, rng. Wracają do 69.22 s. To restart filtra, a nie utrata GNSS: GPS w tym oknie fix 3, 10 satelitów, eph 0.9.
- Pojazd stał na ziemi: `cs_in_air` wstaje przy 112.39 s, **47.7 s po przeskoku**. **W powietrzu w nominale przeskoków 0.**
- `kont_s2_analyze.py` liczy przeskoki od pierwszego włączenia flagi, więc obejmuje też ziemię.

**Litera:** R-5 mówi „jeden przeskok w nominale gdziekolwiek w S2 ⇒ STOP”, więc STOP jest poprawny. Czy restart na ziemi ma być liczony, to już sprawa reguły, a nie moja decyzja.

**Rozjazd liczników:** kolejka przerwała pętlę przed zliczeniem, więc `kampania_d2.json` ma `wazne=4`, a `c00_s02_r3/wyniki.json` ma `wazny=true`. `kont_s2_freeze_g.py` liczy po `wyniki.json`, więc policzyłby ten lot. Nie uruchamiałam go.

## 5. Nowe ryzyko: wysoki bias żyroskopu przy starcie s2d

| boot | launcher | pierwsza próbka bias | bias max | reinit |
|---|---|---|---|---|
| `c08_s02a_r2` | stary | 0.00023 | 0.00023 | 0 |
| `c11_s02_r3` | stary | 0.00016 | 0.00017 | 0 |
| `c11_s03_r4` | s2d | **0.10254** | 0.10254, opada do 0.0001 | 0 |
| `c08_s04_r3` | s2d | 0.00019 | 0.00019 | 0 |
| `c00_s02_r3` | s2d | **0.10557** | 0.12785, rośnie | 1 |

W boocie `c00_s02_r3` `px4.log` ma też `Preflight Fail: High Gyro Bias`. Bias > 0.05 miał 2/3 bootów s2d i 0/2 lotów ze starym launcherem. W kampaniach od K2 reinity praktycznie zniknęły (0 w K2, NET, DET, AKW, FANTOM, SKAN2, WK*), a wcześniej były częste w K1 i W. Przy tak małym n związek z s2d jest tylko podejrzeniem, [MECHANIZM NIEZMIERZONY]. Ma jednak znaczenie, bo 1c §3 zakłada, że faza nie wpływa na mierzone wielkości: dla ε z tych lotów tego nie sprawdzono.

Najwyższy ε (4.02 m) ma lot z reinitem. Przy n = 5 nie wiem, czy to związek, czy rozrzut.

## 6. Δ = 2.80 m w `c08_s04_r3` i co to znaczy dla T*

- **Przebieg:** ε 0.32 m na początku zejścia (z_GT 12.0), 3.0 m po 1.9 s (z_GT 9.4), potem ok. 2 m do ziemi. Skok w pierwszych 2 s zejścia, [MECHANIZM NIEZMIERZONY]. Inne loty mają Δ 0.76–1.03 m.
- **Opis, bez zamrożenia:** reguła PRE §3 na obecnych lotach daje Δ_D5 ≈ 4.20 m, R_nom ≈ 24.8 m i **T* ≈ 4 s, czyli poniżej progu śmierci S2 (10 s)**. Wynik jest taki sam dla n = 4 i n = 5, bo decyduje o nim ta jedna Δ.
- **Bez tej Δ** T* byłby wyraźnie większy, ale i tak `c00_s02_r3` (ε 3.67–4.02 m przy 60–70 s) daje 1.5×ε powyżej budżetu przed końcem okna.
- **R_nom** ≈ 24.8 m jest daleko powyżej progu 11.0 m.
- **Zmiana względem ANEKS_KONT-1b §5:** tam po jednym locie T* wychodził w okolicy 70 s. Reguły nie ruszam: tak ma działać, jeśli ten skok jest prawdziwy. Pozostały 3 loty mogą tę Δ tylko podnieść, bo reguła bierze maksimum. Sens dalszych lotów zależy więc od oceny CC.

## 7. Budżet, zegar, stan

- **S2′: 5/12. Noga: 21/45** (S1 2 + S2 14 + S2′ 5). Rezerwa S2′: 7. Brakuje `c11_s04`, `c08_s02b`, `c02_s01`.
- **Zegar:** 0 skoków w próbnikach i `zegar2`; timesyncd po kolejce `active`. `time jump` w `px4.log` to osobny sygnał timesync XRCE, obecny też w D1.
- **Sieroty:** inwentarz pusty po kolejce.
- **Edycje w miejscu (wyjątek 1d §2.2):** `kont_run_stack_s2d.sh` i `kont_s2_campaign_d.py`, diff w `56c77d83`.
- **Nie dotknięto:** certów, kodu osłony, PX4, parametrów EKF2, watchdoga, starych raportów. Push = Olga.

## 8. Do rozstrzygnięcia przez CC

1. **Reguła przeskoku.** Rekomendacja: liczyć przeskoki od `cs_in_air`, a reinit watchdoga na ziemi nazwać osobno. To zmiana po danych, więc wymaga dokumentu.
2. **`c00_s02_r3` jako lot 5/8.** Rekomendacja: zaliczyć, jeśli przejdzie (1). Lot jest najgorszy na ε, więc jego odrzucenie wyglądałoby na czyszczenie danych w dobrą stronę.
3. **Bias przy starcie s2d (§5).** Czy badać przy biurku i czy to narusza założenie 1c §3. Propozycja: porównać ulogi 5 lotów na `estimator_sensor_bias` i start `sensor_combined`.
4. **Δ i sens dalszych lotów (§6).** Czy najpierw rozebrać skok z `c08_s04_r3` z ulogu (0 bootów), zanim poleci reszta. Rekomendacja: tak, bo śmierć S2 (T* < 10 s) wisi na tej jednej wartości.
5. **KSIĘGA przy ANEKS_KONT-2:** wada z 1d §2.3 oraz nowe punkty z §3 i §5 tego raportu.

**Liczby tego raportu nie są zamrożone** — zamraża je ANEKS_KONT-2 od CC po przeliczeniu z repo.

STOP.
