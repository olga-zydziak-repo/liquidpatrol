# RAPORT_KONT_S2f — STOP-KONT2f: werdykt Y-a; trzymanie yaw usuwa odjazd w 3/3 zejściach, T* = 22 s, R_nom = 27.51 m, koszt bariery 0/48

**Werdykt prereg (ANEKS_KONT-2b §2): Y-a.** Wszystkie 3 zejścia z wektorem skoku ≤ kontrola, więc wg reguły mechanizm = skok yaw. **Wg reguły PRE §3 przy n = 8: Δ_D5 = 1.524 m, T* = 22 s ≥ 10 s, R_nom = 27.51 m.** Skutek wg §2: ANEKS_KONT-3 zamraża, a noga idzie do S3 z akcją „D5 + trzymanie yaw”. Liczby nie są zamrożone. Decyzja należy do CC po przeliczeniu z repo.

## 1. Tabela D4 i Δ per zejście

Dowody: `results/KONT/s2/d4/d4_y.json` (`wektor_skoku_3s` linie 332, 772, 1256), `results/KONT/s2/d4/d4_yaw.json`, `kont_s2_probe_y.py:347,357`.

| lot | sonda | obrót 3 s [°] | yaw rate max [rad/s] | v styczna [m/s] | wektor skoku 3 s [m] | kontrola max [m] | rezyduum 3 s [m] | kontrola max [m] | odjazd szczyt [m/s] | Δ kanon [m] |
|---|---|---|---|---|---|---|---|---|---|---|
| `c11_s04_r3` | **Y** | 0.1 | 0.22 | 2.19 | **0.72** | 1.54 | 1.01 | 1.41 | 1.57 | **1.02** |
| `c08_s02b_r2` | **Y** | 0.2 | 0.28 | 1.52 | **0.46** | 1.20 | 0.65 | 1.00 | 0.95 | **0.09** |
| `c02_s01_r4` | **Y** | 0.2 | 0.24 | 1.89 | **0.31** | 2.20 | 0.67 | 2.18 | 1.08 | **0.10** |
| `c08_s02a_r2` | yaw 0 | 123.2 | 2.97 | 2.30 | 3.69 | 1.31 | 3.00 | 1.27 | 4.71 | 1.03 |
| `c11_s02_r3` | yaw 0 | 51.1 | 1.59 | 2.32 | 1.82 | 1.65 | 1.21 | 1.20 | 2.27 | 0.95 |
| `c11_s03_r4` | yaw 0 | 112.4 | 2.92 | 1.55 | 2.07 | 1.26 | 1.82 | 1.05 | 3.33 | 0.76 |
| `c08_s04_r3` | yaw 0 | 134.4 | 3.10 | 1.85 | 3.24 | 1.81 | 2.94 | 1.42 | 5.09 | 2.80 |
| `c00_s02_r3` | yaw 0 | 56.0 | 1.73 | 1.87 | 1.25 | 1.16 | 1.30 | 1.07 | 1.94 | 0.76 |

- **Rozdział:** 5/5 ponad kontrolą przy yaw = 0, 3/3 poniżej przy trzymaniu yaw. Zakres prędkości się pokrywa (1.52–2.19 wobec 1.55–2.32 m/s).
- **Hamowanie zostało i bez skoku yaw nie daje odjazdu:** rate roll/pitch 1.50–1.69 rad/s (poprzednio 1.12–1.83), szczyt innowacji flow nadal przy +0.26–0.30 s (0.75–1.23), fused 0.990–0.993.
- **Trzymanie yaw zadziałało** w 3/3: obrót ≤ 0.2°, yaw rate poniżej p99 orbity.
- Trace zgodny z ulogiem do 0.025 m.

## 2. Liczby wg PRE §3, n = 8 (opis, `s2_freeze_bf.json`)

ε_b(0⁺) = 0.116 m, Δ_D5 = 1.5 × 1.016 = **1.524 m** (stara 4.203 m obok), **T* = 22 s**, **R_nom = 27.51 m**, koszt bariery **0/48** (r_max 26.16 m). Przeliczone osobnym kodem, ten sam wynik.

Krzywe ε_b, surowa i obwiednia (zapis „dwie krzywe ε_b: n = 8” z §4 aneksu czytam tak; CC może chcieć inaczej):

| koszyk k | 0 | 5 | 9 | 10 | 15 | 20 | 21 | **22** | 23 | 30 | 40 | 50 | 60 | 63 | 69 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ε_b surowa [m] | 0.323 | 2.362 | 3.105 | 3.478 | 3.188 | 3.303 | 3.738 | **4.325** | 4.567 | 3.183 | 4.983 | 4.980 | 5.505 | 6.030 | 5.710 |
| ε_b obwiednia [m] | 0.323 | 2.362 | 3.105 | 3.478 | 3.478 | 3.478 | 3.738 | **4.325** | 4.567 | 4.567 | 4.983 | 5.095 | 5.505 | 6.030 | 6.030 |
| + Δ_D5, budżet 5.79 m | 1.847 | 3.886 | 4.629 | 5.002 | 5.002 | 5.002 | 5.262 | **5.849** | 6.091 | 6.091 | 6.507 | 6.619 | 7.029 | 7.554 | 7.554 |

- **Wrażliwość:** koszyk 22 przekracza budżet tylko o 0.059 m (ε 2.883 m, lot `c02_s01_r4`, próg 2.844 m). Koszyk 21 ma zapas 0.53 m.
- **Porównanie:** na samych 5 starych krzywych przy tej Δ_D5 T* byłby 39 s, więc nowe loty obniżyły T*, zgodnie z zasadą monotoniczności. Bez `c00_s02_r3` T* zostaje 22 s, więc wynik nie zależy od zaliczenia tego lotu.

## 3. Czego to nie dowodzi

- **n = 3 zejścia Y, przypisanie nielosowe,** inne scenariusze niż w lotach yaw = 0. Reguła jest spełniona z dużym zapasem w `c02_s01_r4` i `c08_s02b_r2`, a w `c11_s04_r3` zapas jest mniejszy (0.72 wobec 1.54 m).
- **Mechanizm wewnątrz filtra niezmierzony.** Wiemy, że usunięcie skoku yaw usuwa odjazd. Tezy o derotacji przepływu nie mierzyłam: [MECHANIZM NIEZMIERZONY].
- **Δ_Y = 1.02 m (`c11_s04_r3`) nie jest skokiem z pierwszych 3 s.** ε rośnie o ok. 0.6 m w pierwszej sekundzie, potem powoli do 3.34 m przy +5.6 s (z_GT 4.1 m) i spada. Przyczyny nie badałam. Δ jest skalarne, więc zależy od kąta jak w S2e §3.1: pozostałe dwa loty (0.09–0.10 m) mają wektor 0.31–0.46 m.
- **Grunt nadal SITL z dekalem, bez wiatru.** Liczby są dla akcji, której D5 w produkcji dziś nie wykonuje: `r03/gate_run_r03.py:284` komenduje yaw = 0.

## 4. Stanowisko

| lot | restart na ziemi | bias max na ziemi | bias przy odcięciu | yaw przed startem [°] | ε max [m] | r_GT max [m] |
|---|---|---|---|---|---|---|
| `c11_s04_r3` | **1** (sim 63.97 s, bias 0.125) | **0.15** | 0.00107 | 6.43 | 2.38 | 25.90 |
| `c08_s02b_r2` | 0 | 0.00012 | 0.00088 | 6.42 | 2.58 | 18.83 |
| `c02_s01_r4` | 0 | 0.00017 | 0.00042 | 6.38 | 3.79 | 23.35 |

- **Asercja yaw:** 3/3 PASS, 0 odrzuceń; poprawnie po restarcie w `c11_s04_r3`. Booty s2d łącznie: bias na limicie 3/6, restart watchdoga 2/6. Mechanizm niezmierzony. Bias przy odcięciu w normie we wszystkich 8 lotach.
- **Wg 1e §2:** przeskoki od startu 0/8, restart na ziemi w 2 lotach.
- **Nowe liczniki resetów:** `c11_s04_r3` vxy przy +13.14 s, `c02_s01_r4` xy i vxy przy +13.28 s. Przyziemienie GT było wcześniej (11.5 s w `c11_s04_r3`), więc to już po oknie Δ i na ziemi.
- **`cs_in_air` w `c02_s01_r4`:** krótki błysk 8.15–8.17 s przy starcie filtra, potem poprawnie od 112.43 s. Skutek: `nominal_powietrze_s` = 165.6 s w `wyniki.json` jest błędne, prawdziwa wartość to 61.3 s. Na przeskoki bez wpływu, bo lista jest pusta.

## 5. Moje wady i odstępstwa

1. **`STOP-KONT2-WYJATEK`** w `kampania_y.json`, z `wazne = 7` i dwoma lotami Y. To błąd mojej nakładki `kont_d4_y.py`: `t_air` z pierwszej próbki `cs_in_air`, a `d4a` padał na tym błysku. Stało się to po ostatnim locie, więc nic nie przerwało lotów. **Stan poprawny: 8/8 ważnych, 3 loty Y.** Plik zostaje jako dowód, poprawka w nowym `kont_d4_y2.py`, a `d4c` jest identyczne z logiem kolejki dla dwóch pierwszych lotów. Scenariusze na atrapach tego nie pokryły, bo atrapa zastępowała nakładkę.
2. **`kont_s2_freeze_bf.py` uruchomiony za wcześnie,** w jednej komendzie z nakładką, zanim reguła Y była rozstrzygnięta dla trzeciego lotu. Kolejność nie zmienia wyniku, bo Y-a się potwierdził, ale §2 stawia zamrożenie po Y-a. Plik `s2_freeze_bf.json` zostaje.
3. **Nowe pliki spoza listy §3.4:** `kont_s2y_boot.sh` (wywołuje launcher), `kont_d4_y2.py` (punkt 1).

## 6. Budżet, zegar, stan

- **S2′: 8/12. Noga: 24/45** (S1 2 + S2 14 + S2′ 8). S4 ≤ 16 + 1 się mieści.
- **Zegar:** 0 skoków, V2′ 0.95–0.96, timesyncd po kolejce `active`, inwentarz pusty.
- **Twarde STOPy:** breach 0, REFUSE 0, przeskoki w powietrzu 0. Faza 7.42–7.50 s, launcher s2y 3/3 wstał.
- **Nie dotknięto:** certów, kodu osłony, PX4, parametrów EKF2, oryginałów narzędzi, starych raportów. Push = Olga.

## 7. Do rozstrzygnięcia przez CC (ANEKS_KONT-3)

1. **Przyjęcie Y-a i zamrożenie:** T* = 22 s, Δ_D5 = 1.524 m, R_nom = 27.51 m, krzywa ε_b.
2. **Rozliczenia:** P-KONT-3 (T* ≥ 30 s): wg tych liczb ✗, 22 s. P-KONT-4 (koszt 0): wg tych liczb ✓, 0/48. P-KONT-5: n.r. przed S4. P-KONT-6: breach 0 przez 24 boty. Stary koszt 6/48 z 2b §3.6 dotyczył R_nom 24.83 m.
3. **S3:** akcja „D5 + trzymanie yaw”, obowiązkowo sprawdzenie cytatem, czy któryś cert zakłada yaw = 0. Nie sprawdzałam tego.
4. **Ryzyko stanowiska przed S4:** bias na limicie 3/6 bootów s2d. Asercja yaw go nie odsiewa, kiedy restart watchdoga naprawi filtr przed asercją, co jest pożądane, ale mechanizm jest nieznany.
5. **KSIĘGA:** wady z §5 oraz wada d4c z 2b §1.

**Liczby tego raportu nie są zamrożone** — zamraża je ANEKS_KONT-3 od CC po przeliczeniu z repo.

STOP-KONT2f.
