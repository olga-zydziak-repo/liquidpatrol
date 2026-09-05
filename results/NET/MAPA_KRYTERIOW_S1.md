# MAPA KRYTERIÓW — noga sieci, sesja 1 (PROMPT_NET_S1 I0.3, reguła W2)

LiquidPatrol · pozycja 3 · sesja 1 (trening offline, ZERO SITL) · pierwsza czynność sesji.
Reguła W2 (ANEKS_BENCH-2 §3): **kryterium bez źródła NIE ISTNIEJE**; wątpliwość = pytanie do CC, nie zastosowanie.
Łańcuch: PRE_NET.md + ANEKS_NET-0.md (ratyf. 5.09) + PROMPT_NET_S1.md.

## Kryteria bramkujące tej sesji

| # | kryterium | wartość | źródło |
|---|---|---|---|
| G1 | git czysty (origin/master..HEAD puste) | 0 commitów | PROMPT_NET_S1 I0.1 / SR-1 |
| G2 | frozen nietknięty (piny + zestaw ławki) | bajt-identyczne | I0.2 / SR-2; PRE_NET §4 |
| G3 | dane = WYŁĄCZNIE sukcesy D6 | 114 demonstracji (oczekiwane; rozjazd ⇒ STOP) | PRE_NET **N2**; I0.5 |
| G4 | wykluczenia z datasetu | ticki `stall=1` + faza `reset` | PRE_NET **N2** (od ANEKS-0) |
| G5 | wejścia = `bench/features.py` | import, nie kopia; sha `9adc1505` | PRE_NET **N2**; I1/SR-2 |
| G6 | cel treningu (etykieta) | `cmd_v_ned` | PRE_NET **N2** |
| G7 | strata | MSE | PRE_NET **N2** |
| G8 | podział TEST | seed % 4 == 0 (ziarna 4, 8) — dotykany RAZ/ramię po zamknięciu selekcji | PRE_NET **N2**; I0.3; SR-3 |
| G9 | podział VAL (selekcja modelu) | ziarno 2 z TRAIN | PRE_NET **N2**; I0.3 |
| G10 | podział TRAIN | reszta (ziarna 1,3,5,6,7,9,10) | PRE_NET **N2** |
| G11 | hiperparametry zamrożone przed 1. epoką | `net/train_config.json` w N-B1 | PRE_NET **N2**; I1; SR-4 |
| G12 | test kontraktu 10⁴ (saturacja tanh×V_MAX) | 10⁴ losowych wejść, \|v̂\|≤V_MAX | PRE_NET **N1/N3(iii)**; I1 |
| G13 | **BRAMKA ROLLOUTU N3(i)** | analog-D6 (wejście≤25s ∧ frac[6,10]≥0.85 ∧ d_min≥4) w **≥10/12 komórek** siatki × ziarna TEST, model punktowy FEED-B | PRE_NET **N3(i)**; I2 krok 4 |
| G14 | RMS(v̂−v_nauczyciel) na TEST | mediana+IQR — DIAGNOSTYKA, NIE bramka | PRE_NET **N3(ii)**; I2 krok 3 |
| G15 | TEST dotykany raz/ramię po zamknięciu selekcji | naruszenie = ramię spalone (zapisane) | PRE_NET **N2/N3**; SR-3 |
| G16 | DAgger | **TYLKO** sesja 2, trigger = FAIL G13 w sesji 1; weto Olgi „DAgger nie" | PRE_NET **N4** + ANEKS_NET-0 §1; SR-7 |
| G17 | cap sesji pozycji 3 | ≤ 2 sesje | PRE_NET **N5**; ANEKS_NET-0 §1 |
| G18 | ZERO bootów SITL, zero zmian w harness/ | — | PROMPT_NET_S1 nagłówek; SR-5 |

## Konsekwencje werdyktów (nie bramki, ale zapisane)
- Ramię bez PASS G13 po wyczerpaniu capu = nie lata (PRE_NET N3). FAIL w sesji 1 = zapisany FAIL; ratunek = DAgger dopiero w sesji 2 (G16).
- Oba ramiona bez PASS ⇒ pozycja 4 się nie otwiera, slot skryptowy na stałe (PRE_NET N3, wynik pełnoprawny).
- Kolejność sztywna I2: trening → selekcja(VAL) → TEST(raz) → G13. Po G13 żadnego powrotu do treningu tego ramienia w tej sesji (SR-3).

## Reguły odziedziczone (ANEKS_NET-0 §2)
- Drivery sesji z decyzjami start/odrocz żyją w repo z hashem — **zero skryptów efemerycznych** (z ANEKS_BENCH-4/O1). W tej sesji ZERO bootów ⇒ brak drivera lotów; skrypty analizy/treningu są wersjonowane w `net/`.
- Numeracja: ratyfikacje tylko z kolejnym numerem ANEKS_NET-n.

## Poza zakresem sesji 1 (SR-7)
DAgger (do sesji 2), loty SITL, strojenie egzekutora, pozycja 4. Egzekutor-wyrocznia `840514361e` + params `12c14adb` = źródło etykiet, NIGDY strojony.
