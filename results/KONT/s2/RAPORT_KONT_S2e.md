# RAPORT_KONT_S2e — STOP-KONT2e: werdykt D4 = W-A; skok w zejściu występuje w 5/5 lotach, bez związku z prędkością styczną; 0 bootów

**Werdykt prereg (ANEKS_KONT-1e §3): W-A — skok jest właściwością zejścia D5 pod przepływem.** W-B i W-C odpadają mechanicznie (§2). Z jednym nazwanym odchyleniem: to nie są „resety” w sensie liczników, liczniki pokazują 0.

**Skutek wg 1e §3, liczby do zamrożenia przez ANEKS_KONT-2:** przy n = 5 Δ_D5 = 1.5 × 2.802 = 4.20 m i T* = 4 s < 10 s. Reguła bierze maksima, więc kolejne loty mogą T* tylko obniżyć. **Śmierć S2 orzeczona nierównością, bez 3 pozostałych lotów.** Nogi nie zamykam, to robi ANEKS_KONT-2. Loty `c11_s04`, `c08_s02b`, `c02_s01` nie poleciały.

## 1. Dane D4b

Dowody: `results/KONT/s2/d4/d4.json`, narzędzie `results/KONT/tools/kont_d4.py`. Okno ±3 s od początku zejścia, ulogi 5 lotów. Kontrola: 69 okien 3 s na orbicie po odcięciu, w każdym locie.

| lot | Δ kanon [m] | v styczna GT [m/s] | wektor skoku 3 s [m] | kontrola max [m] | rezyduum 3 s [m] | kontrola max [m] | resety xy / vxy / heading | trace−ulog max [m] |
|---|---|---|---|---|---|---|---|---|
| `c08_s02a_r2` | 1.03 | 2.30 | **3.69** | 1.31 | 3.00 | 1.27 | 0 | 0.041 |
| `c11_s02_r3` | 0.95 | 2.32 | **1.82** | 1.65 | 1.21 | 1.20 | 0 | 0.024 |
| `c11_s03_r4` | 0.76 | 1.55 | **2.07** | 1.26 | 1.82 | 1.05 | 0 | 0.028 |
| `c08_s04_r3` | **2.80** | 1.85 | **3.24** | 1.81 | 2.94 | 1.42 | 0 | 0.027 |
| `c00_s02_r3` | 0.76 | 1.87 | **1.25** | 1.16 | 1.30 | 1.07 | 0 | 0.027 |

- **Wektor skoku** = największa zmiana wektora błędu EKF−GT w 3 s od początku zejścia, ten sam dla 15 s. **Rezyduum** = przyrost pozycji EKF minus całka jej własnej prędkości, bez GT.
- **Pearson v–Δ −0.10, Spearman 0.10; v–wektor 0.28 / −0.10; v–rezyduum 0.08.** n = 5, zakres v tylko 1.55–2.32 m/s.

Linie w `d4.json`: `wektor_skoku_3s` 418, 896, 1326, 1772, 2186; `xy_reset_counter` 74, 600, 1078, 1508, 1954; `trace_vs_ulog_xy_max_m` 242, 720, 1150, 1596, 2010; `v_styczna_gt_w_zejsciu` 66, 592, 1070, 1500, 1946.

| lot | szczyt rate roll/pitch [s] | szczyt innowacji flow [s] | szczyt odjazdu pozycji [s] | odjazd [m/s] | fused w oknie | test ratio max (orbita p95) | jakość min |
|---|---|---|---|---|---|---|---|
| `c08_s02a_r2` | +0.16 | +0.24 | +1.12 | 4.71 | 0.970 | 5.38 (0.01) | 140 |
| `c11_s02_r3` | +0.17 | +0.30 | +0.81 | 2.27 | 0.983 | 1.88 (0.01) | 134 |
| `c11_s03_r4` | +0.13 | +0.24 | +1.15 | 3.33 | 0.993 | 1.46 (0.02) | 153 |
| `c08_s04_r3` | +0.12 | +0.26 | +1.08 | 5.09 | 0.990 | 1.74 (0.01) | 153 |
| `c00_s02_r3` | +0.16 | +0.29 | +0.35 | 1.94 | 0.997 | 2.26 (0.01) | 153 |

Na orbicie fused 1.000 i rejected 0.000 we wszystkich lotach.

## 2. Werdykt, kryterium po kryterium

- **W-B odpada.** Warunek: „ulog nie pokazuje resetów ani wychylenia pozycji; trace rozjeżdża się z ulogiem”. Ulog pokazuje wychylenie, a trace zgadza się z nim do 0.041 m.
- **W-C odpada.** Warunek: „resety tylko przy wysokiej prędkości stycznej; Δ pozostałych lotów koreluje z ich prędkością wejścia”. Odjazd jest w 5/5 lotach, także przy najniższej prędkości 1.55 m/s, a korelacja jest bliska zera. Najwyższa Δ przypada na v = 1.85 m/s, nie na 2.32 m/s.
- **W-A zostaje.** „Występują przy tym profilu niezależnie od prędkości stycznej albo bez wyraźnego dyskryminatora”: w każdym locie skok przewyższa maksimum 69 okien kontrolnych. W `c11_s02_r3` i `c00_s02_r3` przewaga jest jednak mała (1.82 vs 1.65; 1.25 vs 1.16).

**Odchylenie od litery W-A:** tekst mówi „resety realne”. Liczniki `xy_reset_counter`, `vxy_reset_counter`, `heading_reset_counter`, `reset_count_pos_ne` i `reset_count_vel_ne` pokazują 0 zmian od odcięcia do +15 s we wszystkich lotach. Największy krok w jednej próbce to 0.045 m. To płynny odjazd z szybkością 1.9–5.1 m/s przy raportowanej prędkości ok. 0.3 m/s, a nie skok dyskretny. Sygnatura z 1e §1 jest realna, ale jej nazwa „reset pozycji” nie: CC może ją poprawić w ANEKS_KONT-2. Na wynik W-A to nie wpływa.

## 3. Trzy rzeczy, które CC powinien zobaczyć przed zamknięciem

1. **Δ = 2.80 m nie jest wyjątkiem, wyjątkowa jest tylko jej skalarna postać.** Wektor skoku w `c08_s02a_r2` (3.69 m) jest większy niż w `c08_s04_r3` (3.24 m), a Δ wyszła 1.03 m, bo skok dodał się do istniejącego błędu 1.88 m pod innym kątem. Δ z `kont_s2_analyze.py:109` to przyrost |ε|, a więc zależy od geometrii. Reguła PRE §3 jest stosowana bez zmian, ale przy niekorzystnym kącie Δ mogłaby sięgnąć ok. 3.7 m. Wzmacnia to W-A.
2. **Kolejność zdarzeń pasuje do hamowania, ale D4 tego nie rozstrzyga.** W 5/5 lotach: najpierw szczyt rate roll/pitch (+0.12–0.17 s), potem szczyt innowacji flow (+0.24–0.30 s), potem odjazd pozycji (w 4/5 +0.81–1.15 s; `c00_s02_r3` +0.35 s). Komenda to `v_ned = (0, 0, vdesc)` (`r03/controllers/safe_descend.py:20-30`, wołane w `kont_s2_probe.py:331`), czyli hamowanie i opadanie naraz. To korelacja czasowa, a mechanizm jest [MECHANIZM NIEZMIERZONY]. Każdy lot hamował z co najmniej 1.55 m/s, więc nie ma zejścia bez hamowania, a zakres prędkości jest wąski. **D4 wyklucza W-C w brzmieniu prereg (zależność od prędkości), ale nie wyklucza, że przyczyną jest sam fakt hamowania.** Prereg kieruje to do W-A i nie otwieram tego sama. Ewentualny test brake-first wymagałby nowego dokumentu.
3. **T* jest wrażliwe na jedną wartość.** Ta sama reguła na tych samych krzywych daje T* = 4 s przy Δ_D5 = 4.20 m (koszyk 3: 1.5 × 0.928 + 4.20 = 5.60; koszyk 4: 1.5 × 1.244 + 4.20 = 6.07 > 5.79) i T* = 39 s przy następnej w kolejności Δ_D5 = 1.54 m. To opis wrażliwości, nie propozycja zmiany: maksimum jest regułą zamrożoną przed danymi. R_nom ≈ 24.83 m, daleko powyżej progu 11.0 m, więc śmierć wynika tylko z T*.

## 4. D4a: bias żyroskopu

| lot | launcher | bias max na ziemi | bias przy odcięciu | bias przy zejściu | błąd yaw przy starcie / odcięciu [°] |
|---|---|---|---|---|---|
| `c08_s02a_r2` | stary | 0.00023 | 0.00071 | 0.00078 | 6.39 / −1.61 |
| `c11_s02_r3` | stary | 0.00018 | 0.00050 | 0.00117 | 6.35 / −4.90 |
| `c11_s03_r4` | s2d | **0.15000** | 0.00092 | 0.00129 | **20.50** / −0.73 |
| `c08_s04_r3` | s2d | 0.00019 | 0.00057 | 0.00070 | 6.42 / −2.27 |
| `c00_s02_r3` | s2d | **0.15000** | 0.00071 | 0.00151 | 6.43 / −4.11 |

Linie w `d4.json`: `bias_max_ziemia` 14, 540, 1018, 1448, 1894; `bias_ciecie` 17, 543, 1021, 1451, 1897.

- **Założenie 1c §3 w oknie pomiaru: utrzymane.** Bias przy odcięciu to 0.0005–0.0009 we wszystkich lotach, z obu launcherów. **Nie ma wpływu biasu na ε do nazwania.** Także `c00_s02_r3`, najgorszy na ε, ma bias przy odcięciu w normie, więc biasem tego nie wytłumaczę.
- **Hipoteza z 1e §3 (timestamp_sample 0) nie ma poparcia w logu.** `vehicle_imu` z sample 0: 0 w 5/5, `sensor_combined` z timestamp 0: 0 w 5/5. Gyro w pierwszych 5 s nie przekracza 0.0025 rad/s. Pierwsza próbka biasu w ulogu to 0, a „~0.10 na pierwszej próbce” z mojego raportu S2d to pierwsza próbka watchdoga, przy ok. 11 s. Co działo się przed pierwszym logowanym wpisem, tego ulog nie mówi.
- **Co widać:** w 2/3 bootów s2d bias dochodzi do limitu 0.15 na osiach x/y zaraz przy starcie EKF2, ok. 8.0 s.
  - `c00_s02_r3`: x/y przy limicie tylko 8.06–8.14 s, potem rośnie oś z: bz 0.078–0.128, a błąd yaw obraca się na ziemi przez pełne koło w ok. 45 s, aż do reinitu.
  - `c11_s03_r4`: x/y przy limicie 8.0–10.18 s, oś z najwyżej 0.035. Bias opada sam, ale pojazd startuje z błędem yaw 20.5° wobec zwykłych 6.4°, a do odcięcia błąd wraca do −0.73°.
  - Mechanizm: [MECHANIZM NIEZMIERZONY]. Stary launcher: 0/2. n za małe na wniosek.
- **Na przyszłość:** gdyby launcher s2d miał służyć dalej, watchdog łapie tylko przypadek `c00_s02_r3`. Start z błędem 20.5° przeszedł bez reakcji.

## 5. Wady i ograniczenia

- **Odrzucony pomiar:** próba porównania ze stanem filtra (`estimator_states`) była nieważna, bo `states[7..8]` nie zmieniają się w oknie, więc w tej wersji PX4 nie są pozycją. Usunęłam ją z narzędzia, a mechanizmu odjazdu w samym filtrze nie mierzyłam.
- **Błąd opisowy:** `e_opis` w `d4.json` liczony jest z offsetem GT z 20 s przed odcięciem, a nie przez gt_judge. Kanonem pozostaje Δ z `wyniki.json`. Różnice są do ok. 0.3 m na starcie zejścia.
- **Kontrola:** okna orbity mają inną dynamikę niż zejście, ale są jedynym porównaniem w tych danych. W dwóch lotach przewaga nad kontrolą jest mała (§2).
- **Liczba lotów:** n = 5, a nie 8. Wg 1e §3 nierówność wystarcza, a PRE §3 wymaga ≥ 8 do zamrożenia. Różnicę rozstrzyga ANEKS_KONT-2. **`kont_s2_freeze_g.py` nieuruchomiony.**

## 6. Metryka przeskoków i stan

- **Wg 1e §2:** przeskoki od startu: 0/5. Zdarzenia na ziemi: 1 restart estymatora (`c00_s02_r3`, sim 64.7 s, `SLOW_bias>0.08_no_decrease_30s`). `kont_s2_analyze.py:79` liczy dalej starą metodą i nie jest zmieniany.
- **Budżet bez zmian:** S2′ 5/12, noga 21/45. **0 bootów w tej sesji.**
- **P-KONT-3 (T* ≥ 30 s, 0.55):** wg tych liczb nie spełniona, rozliczenie w ANEKS_KONT-2. **P-KONT-4:** koszt bariery przy R_nom ≈ 24.83 m rozliczy ANEKS_KONT-2.
- **Nie dotknięto:** certów, kodu osłony, PX4, parametrów EKF2, starych raportów i narzędzi. Nowe pliki: `kont_d4.py`, `s2/d4/d4.json`, ten raport. Push = Olga.

## 7. Do rozstrzygnięcia przez CC

1. **Przyjęcie W-A i zamknięcie nogi w ANEKS_KONT-2 z T* = 4 s,** przy n = 5.
2. **Punkt 2 z §3:** czy przed zamknięciem nazwać w dokumencie, że hipoteza hamowania nie została rozstrzygnięta. Rekomenduję to nazwać w zdaniu zamykającym: „T* = 4 s przy zejściu D5 z hamowaniem równoczesnym”. Liczba jest wtedy uczciwa co do warunku, ale W-A niczego nie otwiera.
3. **KSIĘGA:** poza 1e §4: odchylenie „resety”, Δ skalarna vs wektor, bias s2d.

**Liczby nie są zamrożone** — zamraża je ANEKS_KONT-2 od CC po przeliczeniu z repo.

STOP-KONT2e.
