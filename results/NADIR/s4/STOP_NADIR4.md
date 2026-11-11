# STOP-NADIR4 — S4 kompletne: werdykt drabiny (a)–(g) mechanicznie **FAIL nogi**

11.11.2026 · wykonawca · PROMPT_NADIR_S4 §3. Kolejka 10.11 22:56 – 11.11 02:22 po „ratyfikuję N3" (ANEKS_NADIR-3 §4.4,
budżet 24/35) pod bramką zdrowia ANEKS_NADIR-4 §3.1 i telemetrią §3.3. Siatka 16/16 pozycji ważnych, stop = brak (kolejka pusta).
**Booty: S4 20/24 (16 ważnych, 4 przerwane bramką tempa przed tą kolejką), noga 31/35.** Breach 0, REFUSE(POS) fałszywy 0,
STOP globalny żaden. Dane: `results/NADIR/s4/wyniki_s4.json` (generator `results/NADIR/tools/nadir_s4_raport.py`, sama
agregacja `<boot>/wyniki_nadir_s4.json`), `rama.jsonl` + `trace.jsonl` per boot, `kampania_ksiega.jsonl`, `bramka_ksiega.jsonl`.

## 1. Werdykt drabiny (mechanicznie, §2)

| kryterium | naruszenia (epizody) |
|---|---|
| (a) kontynuacja ≥ 110 s, track, zero REFUSE | **3**: c02_s03 (109.996 s), c08_s02 (109.992 s), c10_s02 (109.996 s) |
| (b) u ≤ m | 0 / 28 (u_max/m ≤ 0.812) |
| (c) margines do R_E > 0 (GT) | 0 / 28 (min 6.00 m) |
| (d) offboard do końca, zero failsafe | 0 / 28 |
| (e) τ_p95 ≤ 2 s | 0 / 28 (p95 ≤ 0.212 s, max 1.004 s) |
| (f) [nominały] zero fałszywych wejść / REFUSE | 0 / 16 |
| (g) zero przekroczeń ε_b(⌊τ⌋) w oknach (3D) | **5 / 12 cięć**: c08_s01, c08_s02, c10_s01, c10_s02, c11_s02 |

**FAIL nogi** — litera PRE: dowolne naruszenie (a)–(g) w dowolnym epizodzie. Czyste w całej literze cięcia: c01_s01, c01_s03,
c02_s01, c05_s01, c05_s02, c11_s01 (6/12); nominały 16/16 w literze (f).

### 1.1 (a) — wyłącznie kontynuacja, o 4–8 ms (wada przyrządu wykonawcy, nazwana)
We wszystkich trzech: refuse_misja 0, frac_track 1.000, frac_pasmo ≥ 0.947, zejście planowe. Driver
(`nadir_s4_flight.py:108`, T_CONT_S = 110.0) kończy kontynuację dokładnie na progu litery; analiza
(`nadir_s4_analyze.py:310`) liczy od pola `sim` zdarzenia `denial` w trace, które jest stemplowane o jeden tick po
`t_inj_sim`, od którego liczy driver (c02_s03: t_inj_sim 174.924, sim zdarzenia 174.932; driver `od_ciecia_s` 110.004,
analiza 109.996). Kontynuacja w analizie rozkłada się 109.992–110.040 s wokół progu (12 cięć: 3 poniżej); od t_inj_sim
wszystkie ≥ 110. Nastawa = próg bez zapasu — wada konstrukcyjna
wykonawcy. Werdykt nie jest zmieniany; decyzja o orzeczeniu z tolerancją rozdzielczości = CC.

### 1.2 (g) — przekroczenia rzeczywiste, skupione w komórkach c08 / c10 / c11_s02
Wszystkie przekroczenia cięć leżą w klasie „bez GNSS" (po cięciu); w oknach z GNSS 0. Najgorsze stosunki przyrostu do
ε_b(⌊τ⌋): c08_s02 2.09, c08_s01 1.98, c10_s01 1.35, c10_s02 1.25, c11_s02 1.22; liczba okien z przekroczeniem 3–11 na
~546. Nominały (litera = (f), (g) informacyjnie): 4/16 epizodów z jednym oknem ponad ε_b przy zdrowym GNSS (c04_s01 1.45,
c09_s01 1.37, c01_s02 1.27, c05_s01 1.13). Te same komórki w nominale c08_s01 / c10_s01 / c11_s01 są czyste (0.74 / 0.86 /
0.69). Mechanizm niezmierzony [MECHANIZM NIEZMIERZONY]; obwiednia ε_b = FREEZE ANEKS_NADIR-2, nieruszana.

## 2. Tabela per epizod

| boot | epizod | tempo | ENTRY s | kontynuacja s | u_max/m | τ p95 / max s | okna maxratio | okna > ε_b (z/bez GNSS) | koszt bariery | margines R_E | litera (a b c d e f g) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| nom_b1_r2 | c00_s01 | 0.960 | 19.49 | — | 0.438 | 0.208 / 0.224 | 0.395 | 0/0 | 0 / 0 | 8.52 | – ✓ ✓ ✓ ✓ ✓ ✓ |
| nom_b1_r2 | c01_s01 | 0.960 | 13.58 | — | 0.421 | 0.208 / 0.224 | 0.974 | 0/0 | 0 / 0 | 8.95 | – ✓ ✓ ✓ ✓ ✓ ✓ |
| nom_b1_r2 | c02_s01 | 0.960 | 7.74 | — | 0.419 | 0.212 / 0.408 | 0.622 | 0/0 | 0 / 0 | 8.75 | – ✓ ✓ ✓ ✓ ✓ ✓ |
| nom_b1_r2 | c03_s01 | 0.960 | 26.91 | — | 0.405 | 0.208 / 0.228 | 0.399 | 0/0 | 0 / 0 | 8.66 | – ✓ ✓ ✓ ✓ ✓ ✓ |
| c01_s01_r4 | c01_s01 | 0.974 | 3.64 | 110.032 | 0.421 | 0.208 / 0.228 | 0.656 | 0/0 | 0 / 0 | 8.87 | ✓ ✓ ✓ ✓ ✓ – ✓ |
| c01_s03 | c01_s03 | 0.964 | 3.57 | 110.016 | 0.398 | 0.208 / 0.224 | 0.786 | 0/0 | 0 / 0 | 8.81 | ✓ ✓ ✓ ✓ ✓ – ✓ |
| c02_s01 | c02_s01 | 0.953 | 7.67 | 110.024 | 0.419 | 0.208 / 0.228 | 0.949 | 0/0 | 0 / 0 | 8.70 | ✓ ✓ ✓ ✓ ✓ – ✓ |
| c02_s03 | c02_s03 | 0.962 | 7.04 | 109.996 | 0.421 | 0.208 / 0.224 | 0.793 | 0/0 | 0 / 0 | 8.69 | ✗ ✓ ✓ ✓ ✓ – ✓ |
| c05_s01 | c05_s01 | 0.960 | 2.00 | 110.040 | 0.235 | 0.208 / 0.228 | 0.759 | 0/0 | 0 / 0 | 11.54 | ✓ ✓ ✓ ✓ ✓ – ✓ |
| c05_s02 | c05_s02 | 0.967 | 2.14 | 110.004 | 0.546 | 0.204 / 0.404 | 0.863 | 0/0 | 0 / 0 | 8.62 | ✓ ✓ ✓ ✓ ✓ – ✓ |
| c08_s01 | c08_s01 | 0.958 | 8.67 | 110.020 | 0.470 | 0.208 / 0.800 | 1.978 | 0/8 | 0 / 0 | 8.95 | ✓ ✓ ✓ ✓ ✓ – ✗ |
| c08_s02 | c08_s02 | 0.935 | 8.66 | 109.992 | 0.812 | 0.208 / 0.776 | 2.093 | 0/3 | 0 / 0 | 7.75 | ✗ ✓ ✓ ✓ ✓ – ✗ |
| c10_s01 | c10_s01 | 0.958 | 4.32 | 110.024 | 0.290 | 0.208 / 0.380 | 1.353 | 0/11 | 0 / 0 | 8.15 | ✓ ✓ ✓ ✓ ✓ – ✗ |
| c10_s02 | c10_s02 | 0.958 | 4.37 | 109.996 | 0.497 | 0.208 / 1.004 | 1.246 | 0/8 | 0 / 0 | 10.25 | ✗ ✓ ✓ ✓ ✓ – ✗ |
| c11_s01 | c11_s01 | 0.956 | 6.71 | 110.024 | 0.375 | 0.208 / 0.796 | 0.911 | 0/0 | 0 / 0 | 7.69 | ✓ ✓ ✓ ✓ ✓ – ✓ |
| c11_s02 | c11_s02 | 0.962 | 6.71 | 110.032 | 0.804 | 0.208 / 0.228 | 1.222 | 0/6 | 0 / 0 | 7.47 | ✓ ✓ ✓ ✓ ✓ – ✗ |
| nom_b2 | c04_s01 | 0.960 | 8.75 | — | 0.304 | 0.208 / 0.228 | 1.453 | 1/0 | 0 / 0 | 11.84 | – ✓ ✓ ✓ ✓ ✓ ✗ |
| nom_b2 | c05_s01 | 0.960 | 5.58 | — | 0.235 | 0.204 / 0.392 | 1.127 | 1/0 | 0 / 0 | 12.58 | – ✓ ✓ ✓ ✓ ✓ ✗ |
| nom_b2 | c06_s01 | 0.960 | 6.14 | — | 0.376 | 0.208 / 0.416 | 0.644 | 0/0 | 0 / 0 | 12.93 | – ✓ ✓ ✓ ✓ ✓ ✓ |
| nom_b2 | c07_s01 | 0.960 | 6.54 | — | 0.438 | 0.204 / 0.232 | 0.936 | 0/0 | 0 / 0 | 11.33 | – ✓ ✓ ✓ ✓ ✓ ✓ |
| nom_b3 | c08_s01 | 0.957 | 8.66 | — | 0.470 | 0.204 / 0.412 | 0.744 | 0/0 | 0 / 0 | 8.92 | – ✓ ✓ ✓ ✓ ✓ ✓ |
| nom_b3 | c09_s01 | 0.957 | 3.58 | — | 0.428 | 0.208 / 0.368 | 1.368 | 1/0 | 0 / 0 | 6.02 | – ✓ ✓ ✓ ✓ ✓ ✗ |
| nom_b3 | c10_s01 | 0.957 | 5.80 | — | 0.290 | 0.204 / 0.372 | 0.856 | 0/0 | 0 / 0 | 10.18 | – ✓ ✓ ✓ ✓ ✓ ✓ |
| nom_b3 | c11_s01 | 0.957 | 6.62 | — | 0.375 | 0.208 / 0.376 | 0.694 | 0/0 | 0 / 0 | 6.00 | – ✓ ✓ ✓ ✓ ✓ ✓ |
| nom_b4 | c00_s02 | 0.960 | 29.05 | — | 0.420 | 0.208 / 0.228 | 0.299 | 0/0 | 0 / 0 | 8.53 | – ✓ ✓ ✓ ✓ ✓ ✓ |
| nom_b4 | c01_s02 | 0.960 | 12.00 | — | 0.375 | 0.208 / 0.224 | 1.269 | 1/0 | 0 / 0 | 8.69 | – ✓ ✓ ✓ ✓ ✓ ✗ |
| nom_b4 | c02_s02 | 0.960 | 8.94 | — | 0.423 | 0.208 / 0.404 | 0.605 | 0/0 | 0 / 0 | 8.72 | – ✓ ✓ ✓ ✓ ✓ ✓ |
| nom_b4 | c03_s02 | 0.960 | 26.64 | — | 0.391 | 0.208 / 0.400 | 0.387 | 0/0 | 0 / 0 | 8.62 | – ✓ ✓ ✓ ✓ ✓ ✓ |

Kolumny: tempo = bramka tempa settle bootu; okna maxratio = max przyrost/ε_b(⌊τ⌋) w oknach misji (z GNSS + bez GNSS);
koszt bariery = REFUSE z bariery piły / ticki kontrfaktyczne. Obserwable bez progu (rozkład τ, koszyki poprawek,
odrzucenia r_h < 8, bias kursu z par) per epizod w `wyniki_s4.json`.

## 3. Stanowisko (ANEKS_NADIR-4 §3.1, §3.3)

- Bramka zdrowia: 18 pomiarów, 3 NO-GO (c10_s02 0.878 A / 0.897 C, potem 0.930 GO; c11_s01 0.896 A, potem 0.903 GO),
  zero STOP-ów stanowiska. Odczyty GO 0.901–0.935, spadek z ~0.93 (22:58–23:22) do ~0.90–0.91 (od 23:34). Przy NO-GO obcych
  procesów na dGPU brak, CPU < 0.1% (QuickPanelOSD Acer przy 00:47 — przyczyna nieustalona).
- Booty: tempo 0.935–0.974 (16/16 ≥ 0.93). Telemetria per boot (`<boot>/host_telemetria.jsonl`): karta 277 MHz w każdym
  boocie, moc 24–28 W, P8 2–29% czasu; na dGPU poza WSL tylko `System` sporadycznie (1–2 próbki). Reguła „żadnych aplikacji
  okienkowych poza terminalem" utrzymana.
- Bramka zdrowia (≥ 0.90) i tempo bootu (≥ 0.93) mierzą różne obciążenia — boot przy bramce 0.901 leciał 0.967. Opis, nie wniosek.
- timesyncd: zatrzymany przez kolejkę na starcie, wznowiony przy końcu (litera ANEKS_SKAN2-0b); każdy pomiar między kolejkami
  zaczyna od jego zatrzymania (§3.2).

## 4. Pliki

diff-stat i porcelain — w wiadomości commita / wyniku `git show --stat`. Nowe: `STOP_NADIR4.md`, `wyniki_s4.json`,
`bramka_ksiega.jsonl`, `results/NADIR/tools/nadir_s4_raport.py`, 15 katalogów bootów (bez `*.ulg`, .gitignore) i
18 katalogów bramki; zmienione: `kampania_ksiega.jsonl`, `kampania_s4.json`, `kampania_s4.log`, `nadir_s4_monitor.log`.

**Sygnał: STOP-NADIR4.** Push = Olga; CC przelicza u, okna i kontynuacje niezależnie i pisze aneks zamykający nogę.
