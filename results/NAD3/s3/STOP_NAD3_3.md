# STOP-NAD3-3 — bramka NADIR-III: werdykt V-A — zero naruszeń B1–B5 w 14/14 lotach, P1 dostępne 4/4 (próg 3); booty S3 14/17, rezerwa 0/3, noga 18/22

15.11.2026 · wykonawca · PROMPT_NAD3_S3 (sha256 1d10fcb1), ANEKS_NAD3-3 (4fed63d3, „ratyfikuję NAD3-3”).

**Werdykt literą PRE §6: V-A.**
- Litera bezpieczeństwa czysta w każdym locie: B1–B4 w 12 cięciach, B1–B5 w 8 epizodach 2 nominałów.
- Próg dostępności P1 spełniony: 4 z 4 cięć P1 dostępnych według D1.
- Zmierzone wymaganie: „1 Hz, błąd do 1.0 m przy zadaniu do 20 m”. Granice 1.37 m i 2.28 m pozostają rachunkiem sprawdzonym w punktach P2 i P3.
- Wszystkie 14 lotów ważne:
  - replay producenta (fx, fx_deg) i osłony 100%;
  - meta zgodna z punktem;
  - najwyżej jedna poprawka na slot.
- Cięć bez wejścia 0, bootów nieważnych stanowiskowo 0.
- Odmowy w misji: 2, obie REFUSE(bariera) przy biasie na zewnątrz w c10 (P2 i P3), zgodne z regułą, B4 czyste. REFUSE(τ\*) w misji: 0.

**Booty:**

| | zużyte | budżet |
|---|---|---|
| S3 | 14 | 17 (rezerwa 0 z 3) |
| noga NADIR-III | 18 | ≤ 22 (S2 4 + S3 14) |

## Bramka §0 i budowa

- origin ⊇ `15eed5cd`; sumy 1d10fcb1 / 4fed63d3 i ratyfikacja; **[CO-NAD3-3] `f6b01e06`**; selfcheck certów 20/20; sumy tabel P1–P3 i manifestu v2 = strażnik boota.
- **[S3-BUDOWA] `3ba25358`:**
  - kolejka `nad3_s3_run.py`;
  - sędzia lotu `nad3_s3_lot.py`;
  - próba na sucho PASS 5/5: plan, strażnik 14/14, driver ↔ intruz, 9 scenariuszy reguł, sędzia na lotach S2.
- **[S3-BUDOWA-FIX] `81c7ecbf`:** odczyt `tasklist.exe` w stronie kodowej Windows (moja wada: scenariusz procesów był tylko na atrapie). Kontrola procesów na żywo przed każdym bootem: Chrome 0, ChatGPT 0 w 14/14.
- **[S3-POPRAWKA-BRAMKA] `0567bcbc`:**
  - po pozycji 2 kolejka zawisła na 31 min w strażniku procesów bootu pozycji 3;
  - przyczyna: proces kolejki 2.4–2.9% CPU, bo wątki gz-transport przyrządu bramki zdrowia zostawały w procesie;
  - przerwana przed startem stosu, boot niezużyty;
  - poprawka: bramka w procesie potomnym, wzór `nad2_s3_run.py`. Moja wada — kolejkę skopiowałem ze wzoru sprzed tej poprawki NAD2;
  - test na żywo: CPU rodzica po bramce 0.0%;
  - od pozycji 3 strażnik przepuszcza boot od razu.
- **Poprawka sędziego** (w commicie raportu): wykrywanie odmowy w misji. Tick zatrzasku ma już `desc = true`, bo D5 startuje w tym samym ticku, więc sędzia w locie pominął odmowę pozycji 7. Analizator (litera, D1) policzył ją poprawnie, decyzje kolejki nie były dotknięte. Wszystkie 14 lotów przeliczone poprawionym sędzią (`nad3_s3_raport.py` ⇒ `wyniki_s3.json`).
- Kod lotu, osłony, degradacji, tabele i manifest bez zmian od `69128dba` (manifest v2 od `d7aad182`).
- Bramka zdrowia: NO-GO w pierwszej próbie przed pozycjami 8 (tempo 0.856) i 13 (0.900), w obu bez wskazanego ciężkiego procesu; druga próba GO. Tempo lotów 0.971–0.977.

## 14 pozycji

Litera: B1–B4 dla cięć, B5 dla nominałów. „Odmowa w zejściu” to zatrzask τ\* po komendzie zejścia planowego (znaczniki wychodzą z kadru przy ziemi, jak w NAD2).

| # | punkt · komórka · bias | lot | ważny | litera | D1 | kontynuacja [s] | track / pasmo | odmowa w misji | odmowa w zejściu |
|---|---|---|---|---|---|---|---|---|---|
| 1 | P1 · c05 · na zewnątrz | p01_p1_c05_zew | ✓ | ✓ | ✓ | 110.54 | 1.000 / 1.000 | — | τ\* +8.42 s |
| 2 | P1 · c10 · na zewnątrz | p02_p1_c10_zew | ✓ | ✓ | ✓ | 110.54 | 1.000 / 0.955 | — | τ\* +6.02 s |
| 3 | P1 · c05 · do środka | p03_p1_c05_srod_r2 | ✓ | ✓ | ✓ | 110.51 | 1.000 / 1.000 | — | τ\* +6.32 s |
| 4 | P1 · c10 · do środka | p04_p1_c10_srod | ✓ | ✓ | ✓ | 110.54 | 1.000 / 0.924 | — | τ\* +5.67 s |
| 5 | nominał NA (P1, na zewnątrz; c00, c01, c05, c10) | p05_p1_nom_zew_NA | ✓ | ✓ B1–B5 4/4 | — | — | — | — | — |
| 6 | P2 · c05 · na zewnątrz | p06_p2_c05_zew | ✓ | ✓ | ✓ | 110.51 | 1.000 / 1.000 | — | τ\* +9.45 s |
| 7 | P2 · c10 · na zewnątrz | p07_p2_c10_zew | ✓ | ✓ | ✗ | — | — | **bariera, 8.94 s po cięciu** | — |
| 8 | P2 · c05 · do środka | p08_p2_c05_srod | ✓ | ✓ | ✓ | 110.52 | 1.000 / 0.993 | — | τ\* +4.34 s |
| 9 | P2 · c10 · do środka | p09_p2_c10_srod | ✓ | ✓ | ✓ | 110.54 | 1.000 / 0.932 | — | τ\* +9.98 s |
| 10 | nominał NB (P1, do środka; c01, c02, c05, c10) | p10_p1_nom_srod_NB | ✓ | ✓ B1–B5 4/4 | — | — | — | — | — |
| 11 | P3 · c05 · na zewnątrz | p11_p3_c05_zew | ✓ | ✓ | ✓ | 110.51 | 1.000 / 1.000 | — | τ\* +8.55 s |
| 12 | P3 · c10 · na zewnątrz | p12_p3_c10_zew | ✓ | ✓ | ✗ | — | — | **bariera, 7.88 s po cięciu** | — |
| 13 | P3 · c05 · do środka | p13_p3_c05_srod | ✓ | ✓ | ✓ | 110.54 | 1.000 / 1.000 | — | τ\* +4.91 s |
| 14 | P3 · c10 · do środka | p14_p3_c10_srod | ✓ | ✓ | ✓ | 110.52 | 1.000 / 0.956 | — | τ\* +6.16 s |

**B1 nieocenione:** 33–130 ticków na cięcie. Przyczyna jedyna: przedział None, bo τ + 0.012 s wyszło poza ostatnią krawędź po zatrzasku. **W fazie misji 0 we wszystkich 12 cięciach.**

**Nominały — akwizycja i promień:**

| nominał | c00 / c01 | c01 / c02 | c05 | c10 |
|---|---|---|---|---|
| NA (na zewnątrz) | c00: t_entry 8.90 s, r_max 18.411; c01: 3.77 s, 18.145 | — | 3.88 s, 16.209 | 5.29 s, 18.857 |
| NB (do środka) | — | c01: 2.11 s, 18.134; c02: 13.55 s, 18.271 | 3.82 s, 17.462 | 5.93 s, 18.794 |

Akwizycja jest w 8/8 epizodach, pustych dla B5 nie ma. REFUSE(POS) 0, ticki poza NOMINAL 0 przy włączonej degradacji (GNSS obecny).

## P1 wobec progu

**4/4 cięć dostępnych według D1** (próg ≥ 3), wszystkie bez odmowy w misji.

| # | max r_est w misji [m] | min zapas bariery [m] | r_max GT [m] |
|---|---|---|---|
| 1 | 16.71 | 5.54 | 15.39 |
| 2 | 20.03 | 2.22 | 18.08 |
| 3 | 15.14 | 7.17 | 15.76 |
| 4 | 18.48 | 3.77 | 18.87 |

## P2 i P3 — opisowo

| # | bias | odmowa w misji: czas od cięcia / przyczyna / r_est / bariera / r_GT | bez odmowy: max r_est / min zapas bariery |
|---|---|---|---|
| 6 | P2 c05 zew | — | 17.54 / 3.66 m |
| 7 | P2 c10 zew | **8.94 s / bariera / 21.194 / 21.125 / 19.137 m** (τ 0.96 s, przedział 4) | (do odmowy: max 21.135 / min 0.422 m) |
| 8 | P2 c05 środ | — | 14.93 / 6.26 m |
| 9 | P2 c10 środ | — | 17.68 / 3.61 m |
| 11 | P3 c05 zew | — | 18.61 / **1.09 m** |
| 12 | P3 c10 zew | **7.88 s / bariera / 19.832 / 19.625 / 16.832 m** (τ 0.948 s, przedział 4) | (do odmowy: max 19.752 / min 0.305 m) |
| 13 | P3 c05 środ | — | 13.75 / 5.96 m |
| 14 | P3 c10 środ | — | 16.77 / 2.85 m |

- Obie odmowy zapadły w przedziale 4 (τ + 0.012 s w (0.95, 1.15]; τ 0.960 i 0.948 s), czyli tuż przed następną poprawką 1 Hz, gdy U′ jest największe, a r_est (prawda + E na zewnątrz) największy.
- Przy odmowie r_est − r_GT wyniosło 2.06 m (P2, E 1.75) i 3.00 m (P3, E 2.75).
- Po odmowie zejście D5, nav_state 14, failsafe 0, przyziemienie przy r_GT 18.99 m (#7) i 17.90 m (#12). B4 „zgodna z regułą” 1/1 w obu lotach.

## Obserwable per cięcie

| # | max e′/U′ | e′ p50 / p95 / max [m] | τ misja p50 / p95 / max [s] | skok Δ′ p50 / p95 / max [m] | odrzucenia bramki predykcji | r_max / r̄ GT w misji [m] | t_entry [s] |
|---|---|---|---|---|---|---|---|
| 1 | 0.432 | 1.17 / 1.49 / 1.80 | 0.516 / 0.964 / 1.020 | 0.43 / 0.78 / 1.22 | 1 | 15.39 / 8.32 | 3.04 |
| 2 | 0.448 | 1.12 / 1.53 / 2.14 | 0.520 / 0.964 / 1.020 | 0.44 / 1.11 / 1.52 | 51 | 18.08 / 8.99 | 4.50 |
| 3 | 0.358 | 0.84 / 1.02 / 1.39 | 0.516 / 0.965 / 1.020 | 0.36 / 0.74 / 0.99 | 3 | 15.76 / 8.40 | 3.01 |
| 4 | 0.436 | 0.87 / 1.11 / 1.96 | 0.516 / 0.968 / 1.020 | 0.37 / 0.91 / 1.90 | 23 | 18.87 / 9.55 | 4.86 |
| 6 | 0.494 | 1.90 / 2.22 / 2.55 | 0.516 / 0.968 / 1.024 | 0.53 / 0.96 / 1.56 | 16 | 15.47 / 8.27 | 3.03 |
| 7 | 0.448 | 1.74 / 1.91 / 2.11 | 0.512 / 0.964 / 1.020 | 0.32 / 0.59 / 0.83 | 1 | 19.12 / 7.56 | 6.02 |
| 8 | 0.439 | 1.61 / 1.76 / 1.97 | 0.516 / 0.964 / 1.020 | 0.48 / 1.13 / 3.26 | 2 | 16.14 / 8.58 | 3.02 |
| 9 | 0.461 | 1.63 / 1.87 / 2.44 | 0.520 / 0.968 / 1.024 | 0.44 / 1.01 / 3.42 | 25 | 18.97 / 9.50 | 6.40 |
| 11 | **0.538** | 2.89 / 3.19 / 3.71 | 0.516 / 0.968 / 1.024 | 0.69 / 1.24 / 2.72 | 42 | 15.44 / 8.27 | 3.00 |
| 12 | 0.502 | 2.81 / 3.02 / 3.24 | 0.518 / 0.964 / 1.012 | 0.32 / 0.67 / 0.69 | 0 | 16.76 / 7.42 | 5.65 |
| 13 | 0.500 | 2.61 / 2.77 / 3.12 | 0.516 / 0.968 / 1.020 | 0.59 / 1.24 / **5.44** | 7 | 16.11 / 8.46 | 2.43 |
| 14 | 0.512 | 2.65 / 2.90 / 3.28 | 0.520 / 0.967 / 1.028 | 0.61 / 1.23 / 2.71 | 26 | 18.97 / 10.12 | 6.25 |

- **Decymacja:** odstęp t_fix dostarczonych 1.000 s we wszystkich lotach poza #11 (min 0.8 / max 1.2 s — klatka w slocie przesunięta o jedną, najwyżej jedna poprawka na slot zachowana).
- **Skok Δ′ ponad zakres treningowy** (rel p99.9 2.65 m, recon R5): #8 3.26, #9 3.42, #11 2.72, #13 **5.44 m**, #14 2.71 m — wszystkie przy biasie radialnym, gdy p̂_fix zmienia kierunek przy przejściu blisko środka (max ≈ 2E). Bramka predykcji tracku (próg 6 m) nie została przekroczona. Opisowo, bez progu.

## Sześć par (do środka − na zewnątrz)

| para | r_max do środka / na zewnątrz [m] | Δ r_max [m] | r̄ do środka / na zewnątrz [m] | Δ r̄ [m] |
|---|---|---|---|---|
| P1 / c05 | 15.758 / 15.393 | +0.365 | 8.400 / 8.315 | +0.085 |
| P1 / c10 | 18.869 / 18.076 | +0.793 | 9.553 / 8.986 | +0.567 |
| P2 / c05 | 16.141 / 15.472 | +0.669 | 8.582 / 8.272 | +0.310 |
| P2 / c10 | 18.969 / 19.120 | −0.151 | 9.504 / 7.562 | +1.942 |
| P3 / c05 | 16.110 / 15.439 | +0.671 | 8.457 / 8.270 | +0.187 |
| P3 / c10 | 18.969 / 16.759 | **+2.210** | 10.116 / 7.420 | +2.696 |

**Zastrzeżenie:** w parach P2 / c10 i P3 / c10 lot „na zewnątrz” skończył misję odmową po 8.9 s i 7.9 s od cięcia, a „do środka” leciał pełne 110.5 s. r_max i r̄ porównują więc okna różnej długości. Pozostałe 4 pary mają pełne okna po obu stronach: Δ r_max od +0.37 do +0.79 m, zawsze dodatnie (do środka dalej).

## Liczby do rozliczenia predykcji (rozlicza CC)

| predykcja | liczby |
|---|---|
| P-NAD3-2 (P1 — 4/4 cięć bez REFUSE w misji) | 4/4 bez REFUSE w misji |
| P-NAD3-3 (0 przekroczeń w 12 cięciach, max e′/U′ ≤ 0.75) | przekroczeń 0; max e′/U′ 0.538 (#11) |
| P-NAD3-4 (\|Δ r_max\| < 1.0 m w ≥ 4 z 6 par) | 5/6 par z \|Δ\| < 1.0 m (wyjątek P3 / c10, +2.21 m, okna nierówne) |
| P-NAD3-5 (P3 na zewnątrz — REFUSE(bariera) 2/2, B4 czyste) | c10: REFUSE(bariera); c05: brak odmowy; B4 czyste 2/2 |
| P-NAD3-6 (P2 — najwyżej 1 REFUSE w 4 cięciach) | 1/4 (c10 na zewnątrz, bariera) |
| P-NAD3-7 (0 REFUSE(τ\*) w 12 cięciach) | w misji 0/12; w zejściu planowym 10/12 (pozostałe 2 zatrzaśnięte wcześniej barierą) |
| P-NAD3-1 (geometria) | rozliczona w ANEKS_NAD3-2 |

## Odchylenia od promptu (nazwane)

1. **Przestój 31 min przed pozycją 3** (wątki bramki zdrowia w procesie kolejki). Kolejka przerwana SIGINT przed startem stosu, boot niezużyty. Poprawka `0567bcbc`, wznowienie pod nazwą `p03_p1_c05_srod_r2` (stub pierwszej próby zostaje).
2. **Sędzia lotu poprawiony po pozycji 7** (odmowa z `desc = true`). Decyzje kolejki i litera nietknięte. Raport liczony od nowa poprawioną wersją dla 14/14 lotów.
3. **Nominały:** sędzia uruchamia sprawdziany w trybie „z degradacją” (fx_deg, decymacja, meta) także dla lotów bez cięcia. Ticki B1 w nominałach to 0 (GNSS obecny).
4. **Boot nieważny stanowiskowo w kolejce** = bramka tempa drivera (`kont_tempo.json` ok = false przed epizodem), liczony do rezerwy. W S3 nie wystąpił.
5. **Pary c10 przy biasie na zewnątrz w P2 i P3** porównują okna różnej długości (odmowa w misji) — podane bez korekty.

## Reprodukcja

```
export PYTHONDONTWRITEBYTECODE=1
python3 results/NAD3/tools/nad3_s3_dryrun.py        # próba na sucho (0 bootów)
python3 results/NAD3/tools/nad3_s3_raport.py        # sędzia ponownie na 14 lotach ⇒ wyniki_s3.json
```

**Sygnał: STOP-NAD3-3.** Push robi Olga. CC weryfikuje z repo własnym kodem i oddaje ANEKS_NAD3-4 (zamknięcie nogi).
