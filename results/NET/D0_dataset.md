# D0 — inwentarz zbioru demonstracji (PROMPT_NET_S1 I0.5)

LiquidPatrol · noga sieci sesja 1 · zbiór z ławki (+) PASS · skrypt `net/d0_dataset.py` (wersjonowany).
Źródło: `results/BENCH/campaign/*/demo.jsonl` + manifesty (odczyt). Zero SITL, frozen nietknięty.

## §1. Liczności głównego

- Scenariusze rozwiązane (pierwsza ważna V2′): **120 / 120**.
- **Udane demonstracje D6 (zbiór): 114** — zgodne z oczekiwaniem PRE_NET (114). Brak rozjazdu ⇒ brak STOP.
- Wykluczone z zbioru (D6 FAIL, poza „udanymi"): **6** — `c05_s01, c05_s08, c07_s02, c09_s02, c09_s03, c09_s06` (dokładnie klasa proximity wejścia c05/c07/c09; ANEKS_BENCH-3/RAPORT_BENCH §3).
- Wiersze demo (kept): **161 380** (total 161 380, bo wykluczenia stall/reset = 0 — patrz §4).
- Wiersze / epizod: min 1374, max 1449, średnio 1415.6.

## §2. Podział N2 (zamrożony: TEST = seed%4==0; VAL = seed 2; TRAIN = reszta)

| split | ziarna | epizody | wiersze (kept) |
|---|---|---|---|
| TRAIN | 1, 3, 5, 6, 7, 9, 10 | 81 | 114 705 |
| VAL | 2 | 10 | 14 158 |
| TEST | 4, 8 | 23 | 32 517 |
| **razem** | | **114** | **161 380** |

VAL = 10 (nie 12): wypadły `c07_s02`, `c09_s02` (D6 FAIL). TEST = 23 (nie 24): wypadł `c05_s08` (D6 FAIL).

## §3. Rozkład per komórka × ziarno (wiersze kept; FAIL = D6-porażka poza zbiorem; − = brak)

```
cell   s1     s2     s3     s4     s5     s6     s7     s8     s9     s10
c00  1449   1392   1434   1437   1431   1429   1432   1436   1444   1436
c01  1381   1428   1421   1423   1425   1422   1434   1425   1425   1429
c02  1427   1423   1433   1423   1411   1431   1428   1421   1424   1433
c03  1432   1425   1425   1429   1421   1428   1428   1424   1431   1423
c04  1428   1434   1424   1417   1427   1429   1435   1433   1427   1427
c05  FAIL   1419   1414   1412   1374   1376   1378   FAIL   1418   1425
c06  1382   1417   1413   1433   1411   1416   1420   1421   1420   1418
c07  1411   FAIL   1417   1379   1416   1428   1379   1418   1382   1419
c08  1422   1424   1377   1420   1428   1423   1430   1423   1427   1420
c09  1413   FAIL   FAIL   1379   1377   FAIL   1414   1417   1412   1425
c10  1377   1418   1423   1377   1413   1378   1379   1378   1414   1419
c11  1378   1378   1418   1376   1414   1381   1427   1416   1421   1414
```
Kolumny split: TRAIN={s1,s3,s5,s6,s7,s9,s10}, VAL={s2}, TEST={s4,s8}.
**Nota dla bramki N3(i):** w TEST (s4,s8) tylko `c05_s08` wypadła dla WYROCZNI — komórka c05 przy ziarnie 8 jest granicą nauczyciela (proximity), więc sieć też nie ma z niej lekcji (P-N5). Bramka ≥10/12 komórek zostawia margines na dziedziczoną granicę.

## §4. Wykluczenia stall/reset — ZNALEZISKO (jawne, do §odchylenia)

- Ticki `stall=1`: **0** w CAŁYM zbiorze demo (178 271 wierszy wszystkich booty). Flaga `stall` w `demo.jsonl` jest zawsze 0 — **logger nie wpiął jej do rtf<0.5**; deep-stalle istnieją WYŁĄCZNIE w `rtf_stream.jsonl` (zegar ścienny, osobny próbnik).
- Wiersze `phase=reset`: **0** — reset dzieje się po `episode_end` i NIE jest logowany do demo (phase tylko hold/approach/orbit: 225/4219/173827).
- **Konsekwencja:** wykluczenie N2 („ticki stall=1 i reset") jest tu trywialnie spełnione (0 do wykluczenia). To NIE ukrywa danych: metryki i cechy są w czasie SIM (D9), więc deep-stall zegara ściennego nie zniekształca geometrii ani `cmd_v_ned` logowanego per tick sim. Zbiór jest czysty w czasie sim niezależnie od flagi. **Zgłoszone CC jako odchylenie łagodne — flaga niewpięta w loggerze ławki (frozen, nie ruszam); brak wpływu na poprawność treningu w czasie sim.**

## §5. Aktywa (ścieżki, I0.5)

- `bench/features.py` sha **9adc1505** (zgodne, inaczej STOP) — importowane w treningu i locie (zero rozjazdu).
- Egzekutor-wyrocznia: `r03/controllers/orbit_executor.py` (sha `840514361e`) + `bench/executor_params.json` (sha `12c14adb`) — źródło etykiet `cmd_v_ned`, nigdy strojony.
- Model punktowy (`point_model`): przyrząd z buildu ławki = `bench/tests_orbit_executor.py::_sim_cell` / `test_kinematic_point_model_12_cells` (kinematyka: śledzenie cmd_v, accel≤2.0, |v|≤V_MAX, dt=0.05). Rollout N3(i) użyje TEJ SAMEJ kinematyki z FEED-B zamiast idealnego feedu; sanity = wyrocznia 12/12 (I1).
- GPU: RTX 5070 Ti Laptop 12 GB (kontekst; trening = CPU numpy, brak torch/jax — patrz N-B1).

## §6. Cel i cechy

- Wejście = 8 cech `bench/features.py`: [rel_x, rel_y, rel_z, own_vn, own_ve, own_vd, track_age_s, track_valid].
- Cel (etykieta) = `cmd_v_ned` (3D), MSE (N2). V_MAX z `r01.config`.
