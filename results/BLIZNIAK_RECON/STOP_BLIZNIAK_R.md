# STOP_BLIZNIAK_R — BLIŹNIAK, recon przy biurku: uczeń kurczący z konstrukcji, dowód prawa pościgu, cena dowodliwości

LiquidPatrol · wykonawca · 21.11.2026 · PROMPT_BLIZNIAK_S0 (sha256 389c9341…, byte-check PASS z wklejki), [CO-BLIZNIAK-0] `3b7f7f95`.
**0 bootów.** `net/frozen/`, cechy, osłona, sterownik i kod lotu bez zmian; nowe wagi tylko w `wagi/`.

**Śmierci: zaszła Ś3** — dla B30 przy Δ_A S(0.3) jest dowiedzione we wszystkich komórkach dopiero od **d₁ = 10.5 m** (od 10.0 m
w 99.934% komórek, 471 wyjątków). **Ś2, Ś4, Ś5 nie zaszły.** **Ś1** dla ramion dowodu nie (wszystkie procedury: 0 wyjątków
w testach 10⁶; B(W) z wag B30 = 0.3 i B50 = 0.5 dokładnie), ale **literalnie zaszła dla B90 i C3**: B(W) z zapisanych wag
przekracza γ o 1 ulp (3.3·10⁻¹⁶ i 4.4·10⁻¹⁶, zaokrąglenie rzutu `Wb[8:] *= cel/b`); nie przerwałem pracy, bo żadne z nich
nie niesie dowodu — do oceny CC (odchylenie 1). Najmniejsze d₁ na B30, Δ_A, szczebel E3: **S(0.3) 10.5 m, S(1.0) 11.75 m**
(S(0.6) 11.25, S(1.2) 12.25). Przy Δ_B (moje, wersja okrojona): S(0.3) 11.0 m. **Kandydata do lotów nie ma**: bliźniaki
krążą w modelu 1.48 m/s wobec Z 1.745 (próg Z − 0.10 = 1.645) i w najgorszej rodzinie 0.98–1.03 m/s wobec GRU 1.34.

## R1 — trening (`tools/bz_trening.py`, `wagi/`)

Przepis z §3 bez zmian; wszystkie ramiona wybrały epokę 899 (VAL malał do końca). B₀ = B(W_Z) = 32.39.

| ramię | γ | sha256 (pocz.) | VAL łącznie | VAL N / E / D | CC | ocena | B(W) z wag | norma max kroku p50 / p99 / max | ρ p50 / p99 / max |
|---|---|---|---|---|---|---|---|---|---|
| Z | — | 0337d5ea | 0.04853 | 0.0644 / 0.0782 / 0.0030 | 0.0485 | zgodne | 32.39 | 3.42 / 3.96 / 4.24 | 0.919 / 0.986 / 1.416 |
| K | — | 20ab8fed | 0.04136 | 0.0536 / 0.0674 / 0.0030 | 0.0414 | zgodne | 36.84 | 3.47 / 4.31 / 4.66 | 0.920 / 0.986 / 1.517 |
| B90 | 0.9 | 22290c10 | 0.04734 | 0.0636 / 0.0744 / 0.0040 | 0.0473 | zgodne | 0.9 + 3.3e-16 | 0.322 / 0.361 / 0.372 | 0.105 / 0.123 / 0.127 |
| B50 | 0.5 | dc3b9c38 | 0.04791 | 0.0647 / 0.0749 / 0.0041 | 0.0479 | zgodne | 0.5 | 0.184 / 0.207 / 0.214 | 0.056 / 0.067 / 0.069 |
| B30 | 0.3 | c9f121e2 | 0.04814 | 0.0652 / 0.0752 / 0.0041 | 0.0481 | zgodne | 0.3 | 0.112 / 0.126 / 0.131 | 0.032 / 0.039 / 0.040 |
| C3 | 3.0 | d50611c2 | 0.04652 | 0.0616 / 0.0743 / 0.0037 | 0.0465 | zgodne | 3.0 + 4.4e-16 | 0.946 / 1.075 / 1.099 | 0.377 / 0.420 / 0.440 |
| C12 | 12.0 | a2a5b0c3 | 0.04512 | 0.0613 / 0.0710 / 0.0031 | — | — | 12.0 | 1.865 / 2.078 / 2.383 | 0.881 / 0.953 / 1.087 |

Norma kroku i ρ: 25 200 stanów z modelu pętli na ramię (`r1_jakobian.json`), jakobian analityczny, kontrola różnicami ≤ 2.5·10⁻¹⁰;
CC: Z 3.4, C3 0.95, B90 0.32, B50 0.18, B30 0.11 — zgodne. **B50 dwa razy: wagi identyczne co do bitu** (`B50.npz` = `B50_bis.npz`).
Cena ograniczenia wobec uczciwej kontroli K: B30 +16.4% VAL (0.04814 / 0.04136), B50 +15.8%, B90 +14.5%.
Wyprowadzenie B(W) sprawdzone: |∂h′_k/∂b_j| ≤ σ|Wg| + (1 − σ)|Wh| + |g − q|·σ′·|Wt| ≤ A[j,k]; |∂b_j/∂h_i| ≤ |Wb[8+i, j]|;
suma wiersza ∂h′/∂h ≤ Σ_j s[j]·A[j,k] dla każdego x i h — B ogranicza normę max jednostajnie. W dowodzie B z wag ×(1 + 1e-12) + 1e-15.

## R2 — ławka i lot w modelu (`tools/bz_petla.py`, `r2_*.json`, tabela per rodzina `r2_tabela_rodzin.json`)

**(a) Ławka offline** (FEED-B): każde ramię NCP (Z, K, B90, B50, B30, C3, C12) **12/12** na ziarnach TEST i **120/120** na wszystkich
— zgodne z CC. Najmniejszy udział w paśmie: Z 0.940, K 0.953, B90 0.967, B50 0.973, B30 0.980, C3 0.982, C12 0.930; największy
czas wejścia 3.3–3.55 s; najmniejszy d_min: Z 5.26, K 5.11, B90 5.98, B50 5.93, B30 6.45, C3 5.83, C12 6.64 m.

**(b) Model pętli** (7 rodzin × 2 v_max × 150 biegów × 90 s, wariant W, start 8 m, szum, ziarna 70000 + 100·r + j wspólne;
2100 biegów na sterownik). Prędkość styczna |v_t| własna, po 30 s (w nawiasie: pierwsze 30 s):

| sterownik | średnia v_t | CC | ocena | udział v_t < 1 | najgorsza rodzina (podejście) | CC | okrążenia/min | d prawdziwy p1/p50/p99/max |
|---|---|---|---|---|---|---|---|---|
| Z | 1.745 (1.697) | 1.75 | zgodne | 4.3% (11.2%) | 1.499 | 1.36 | 1.86 | 6.95 / 8.27 / 9.69 / 10.61 |
| K | 1.740 (1.667) | 1.76 | zgodne | 3.9% | 1.496 | — | 1.86 | 6.99 / 8.27 / 9.65 / 10.60 |
| B90 | 1.484 (1.227) | 1.54 | różnica −0.06 | 12.3% | 1.028 | 0.82–0.84 | 1.51 | 6.89 / 8.22 / 9.69 / 10.59 |
| B50 | 1.475 (1.215) | 1.54 | różnica −0.07 | 13.0% | 0.980 | 0.82–0.84 | 1.50 | 6.89 / 8.22 / 9.69 / 10.74 |
| B30 | 1.478 (1.222) | 1.54 | różnica −0.06 | 13.1% | 0.988 | 0.82–0.84 | 1.51 | 6.90 / 8.22 / 9.70 / 10.60 |
| C3 | 1.533 (1.316) | 1.58 | różnica −0.05 | 10.3% | 1.086 | — | 1.57 | 6.91 / 8.22 / 9.69 / 10.49 |
| C12 | 1.725 (1.572) | — | — | 4.3% | 1.464 | — | 1.81 | 7.01 / 8.26 / 9.68 / 10.70 |
| GRU | 1.674 (1.583) | 1.69 | zgodne | 8.3% | 1.336 | 1.10 | 1.61 | 6.82 / 8.20 / 9.75 / 10.62 |
| MLP k=5 | 0.294 (0.358) | 0.29 | zgodne | 99.5% | 0.270 | — | 0.32 | 5.25 / 8.42 / 10.51 / 11.99 |

Udziały CC (4.5 / 3.6 / 8.6 / 9.3–9.6 / 99.6%) liczone na 600 biegach po 120 s — u mnie po 30 s z 90 s; rząd zgodny, liczby różne.
Najgorsza rodzina u wszystkich to „podejście”; moje wartości wyższe od CC (inna długość biegów i zakres zapisu). Dystans z cech po 30 s:
max 10.25–10.52 m dla NCP/GRU, 11.71 dla MLP.

**(c) Kalibracja:** Z 1.745 > GRU 1.674 > MLP 0.294, MLP < 0.6 m/s — **skalibrowany; Ś5 nie zachodzi.**

**(d) H-PAMIĘĆ** (v_t średnia; cel stoi < 0.05 m/s po 10 s / cel > 0.4 m/s po 10 s / pierwsze 10 s):
Z 1.852 / 1.725 / 1.584; K 1.832 / 1.722 / 1.525; B30 1.558 / 1.465 / 0.915. **Różnica B30 − Z: −0.294 / −0.260 / −0.669 m/s.**
Przy stojącym celu strata jest taka sama jak przy celu w ruchu (odniesienie: K − Z −0.020 / −0.003 / −0.059); największa w pierwszych
10 s. Hipoteza, że pamięć służy prędkości celu, w tej postaci się nie potwierdza; zgodne z częścią „orbita nieustalona”.

**(e) Pion z sieci, B30:** 700 biegów × 300 s, start 8 m — **0 zdarzeń ucieczki wysokości** (|rel_z − 2| > 8 po 20 s).

**Reguła kandydata:** B90/B50/B30 mają B < 1, ale średnia v_t 1.475–1.484 < Z − 0.10 = 1.645 i najgorsza rodzina 0.98–1.03 < GRU
1.336 (również „łącznie”: 1.39–1.40 < 1.63). **Kandydata brak.**

## R3 — dowód na bliźniaku (`tools/bz_dowod.py`, `bz_afin.py`, `bz_r3e.py`, `bz_r3m.py`; wyniki `r3_B30_A.json`, `r3_B30_B.json`)

Dziedzina 𝒟 i klasa 𝒞 jak w §5; komórki od 8.0 m (Δ_A: 1 003 520 komórek), k = 5 (B30: 0.3⁵ = 0.00243 ≤ 0.005).
- **E1 — przedziały naturalne:** U_k półszerokość p50 0.550, p99 0.715, max 0.786 (min 0.337); ograniczenie ku w każdej komórce
  ≈ −4.4 m/s — **S nigdzie**. Przyczyna: zawijanie przez 20 neuronów i szerokie pudełka X_j.
- **E2 — wartość średnia z jakobianem przedziałowym** po całej historii (zmienne: h_init i 7 współrzędnych sytuacji na krok):
  środek jakobianu daje rozrzut 0.10 (zgodny z próbkami), ale promień jakobianu 0.41 — **S nigdzie** (ten sam −4.4).
  Sprawdziłem też wariant ze skurczem B(W) jako kulą Lipschitza (`U_skurcz`) — bez poprawy; nie wchodzi do wyników.
- **E3 — formy afiniczne** (`bz_afin.py`: c + A·ε + przedział reszty; tanh i sigmoid linearyzowane sieczną ze ścisłym
  odchyleniem; iloczyn bramek z członem kwadratowym) **z podziałem adaptacyjnym** (etap 1: θ w X₁ na 3, θ w X₀ na 4 dla komórek
  < 1.2 m/s; etap 2: θ w X₂ na 2, (θ, v_r, v_t) w X₁ na (4, 2, 2), (d, θ) w X₀ na (2, 4) dla komórek ≥ 9.5 m nadal < 0.3).
  U_k półszerokość **p50 0.211, p99 0.276, max 0.311** (min 0.113) — połowa E1. Etapy: 259 493 bez podziału, 676 803 etap 1,
  67 224 etap 2. Czas łącznie ok. 7.6 h procesora (7 procesów, ok. 65 min zegara).
- **Testy poprawności** (każdy 10⁶ historii z 𝒞, start z U(−1,1)²⁰, (rel_z, vd, wiek) losowo co tick): ku ≥ ograniczenie E1, E2, E3
  komórki — **0 wyjątków** (Δ_A i Δ_B); h_t w pudełku U_k (E1 i E3, 10⁴ komórek × 100) — **0 wyjątków**; zapas 1e-9 jawny
  na każdej operacji, bez zaokrąglania kierunkowego.
- **Kontrola Z i K** tym samym kodem (`r3_kontrola_ZK.json`; 20 000 komórek, k = 5, Δ_A): U_k półszerokość **1.0 we wszystkich
  komórkach** (E1 i E3), ku E3 bez podziału p50 −7.7, udział ≥ 0.3 od 10 m: 0. B30 na tych samych komórkach: U 0.211, ku E3 bez podziału p50 +0.11, udział ≥ 0.3 od 10 m 65.1%.
  Test 10⁶: 0 wyjątków.

## R4 — prawo pościgu

**Profil S(v, d₁)**, B30, szczebel E3 (E1 i E2: brak d₁ dla każdego v):

| | S(0.3) | S(0.6) | S(1.0) | S(1.2) |
|---|---|---|---|---|
| Δ_A | **10.5 m** | 11.25 m | 11.75 m | 12.25 m |
| Δ_B (okrojone, odch. 6) | **11.0 m** | 14.25 m | brak (do 14.75) | brak |

**Pokrycie** (udział komórek z dowiedzionym S(0.3); w nawiasie liczba wyjątków):

| d₁ | 9.5 | 9.75 | 10.0 | 10.5 | 11.0 |
|---|---|---|---|---|---|
| Δ_A | 98.01% (15 665) | 99.43% (4 297) | **99.934% (471)** | 100% | 100% |
| Δ_B | 89.40% (83 571) | 93.38% (49 812) | 96.70% (23 672) | 99.77% (1 461) | 100% |

Wyjątki przy 10.0 m (Δ_A): duża prędkość własna od celu i bokiem (v_r −2.5…−1.0, |v_t| 2.0–3.0 m/s), namiar w kilku sektorach
(θ ≈ −2.45…−2.26 rad i symetrycznie); ograniczenie 0.22–0.30 m/s. Przy Δ_B te same okolice prędkości.

**Próbki 10⁷ historii** (min ku po clip_v; Δ_A / Δ_B): od 9.0 m −0.30 / 0.23; od 9.5 m **0.258** / 0.228; od 9.75 m 0.488 / 0.596;
od 10.0 m **0.776** / 0.809; od 10.5 m 1.324 / 1.246; od 11.0 m 1.633 / 1.611. CC (4.9 mln, inna dziedzina): 0.42 od 9.75 m,
0.70 od 10.0, 1.19 od 10.5, 1.59 od 11.0 — zgodne co do rzędu. Prawdziwy próg S(0.3) leży więc między 9.5 a 10.0 m; dowód
zamyka się 0.5 m (Δ_A) i 1.0 m (Δ_B) dalej.

**Kontrprzykłady** (`tools/bz_kontr.py`, `r4_kontr_B30_*.json`; L = 5, 10, 60; losowe 10⁶, pchnięcie ±Δ 10⁶, ±Δ/2 10⁶,
kierowane 4000 × 400): **0 kontrprzykładów** przy Δ_A i Δ_B. Najmniejsze ku od 10.0 m: kierowane 0.780 (L 10, Δ_A), 0.778 (L 5, Δ_B);
losowe 0.97–1.17; pchnięcia 0.94–1.08. Stałe pchnięcie przez 60 kroków zawsze wychodzi z 𝒟 (0 dopuszczalnych). **Ś4 nie zachodzi.**

**Przesłanki na lotach TEACH** (`tools/bz_przeslanki.py`, `r4_przeslanki.json`; ticki misji od 1 s po pierwszym kroku sieci;
Δ z 10 lotów, ocena na p03, p07, p09, p12, p13 — 14 490 ticków):
- Δ_B moje (99.9. percentyl, 39 751 zmian): **d 0.438 m** (CC 0.81), v_t 0.142 m/s (CC 0.146); θ 0.046, v_r 0.125 (≤ Δ_A).
- P1 Δ_A **99.19%**, Δ_B **99.63%** (przekroczenia Δ_A: d 0.61%, θ 0.09%, v_r 0.007%, v_t 0.19%; zmiana d p99.9 0.50 m, max 1.81 m).
- P2 (d 4–15 m, |v| ≤ 3.2) **100%** (d 4.14–11.11 m, |v| max 3.16).
- P3 (wiek 0.024–0.15, track ważny) **99.94%** (wiek > 0.15 s: 0.02%).
- Łącznie P1–P3: **99.12% (Δ_A), 99.57% (Δ_B)**. Na wszystkich 15 lotach: 99.23% / 99.72%.
- P4 (wysokość z regulatora) założona.

**Rachunek złożenia** (`tools/bz_rachunek.py`, `r4_rachunek.json`; rachunek, nie dowód):

| | v_q 0.5 (Δ_A) | v_q 1.0 (Δ_A) | v_q 0.5 (Δ_B) |
|---|---|---|---|
| użyte S | v 0.6 od 11.25 m | v 1.2 od 12.25 m | v 0.6 od 14.25 m |
| + opóźnienie 0.35 s (start 3.2 m/s od celu) | +1.30 m | +1.47 m | +1.30 m |
| + inercja 0.3 s | +1.00 m | +1.07 m | +1.00 m |
| D z cech | 13.55 m | 14.79 m | 16.55 m |
| + ε_rel 1.364 → D prawdziwy | 14.91 m | 16.16 m | 17.91 m |
| ρ* ściana GNSS 27.30 m | 12.39 m | 11.14 m | 9.39 m |
| ρ* przedział 0 bez GNSS (24.84 − 2.786) | 7.14 m | 5.90 m | 4.14 m |

Dla v_q 1.0 przy Δ_B brak dowiedzionego v > 1.0. Składniki: profil S — dowiedziony (E3, na 𝒟 i 𝒞); P1–P3 — zmierzone;
napęd N — zmierzony (PĘTLA); przełożenie komendy ku celowi na prędkość radialną bez strat na obrót wersora — **założone**;
ε_rel — zmierzone (PĘTLA); U′(0) — przesłanka dowodu P9_teach; wysokość z regulatora — założona; intruz ≤ v_q — klasa.
Porównanie: PĘTLA dla Z (dystans zmierzony, nie dowiedziony) ρ* 9.58 m w przedziale 0; tu z dowiedzionego profilu 7.14 / 5.90 m.

## Krzywa ceny (`krzywa_ceny.json`)

| ramię | B(W) | VAL | v_t po 30 s | najgorsza rodzina | ławka | dowód S(0.3) |
|---|---|---|---|---|---|---|
| Z | 32.39 | 0.04853 | 1.745 | 1.499 | 12 / 120 | nie (U = pełny zakres) |
| K | 36.84 | 0.04136 | 1.740 | 1.496 | 12 / 120 | nie (U = pełny zakres) |
| C12 | 12.0 | 0.04512 | 1.725 | 1.464 | 12 / 120 | nie liczony (B ≥ 1) |
| C3 | 3.0 | 0.04652 | 1.533 | 1.086 | 12 / 120 | nie liczony (B ≥ 1) |
| B90 | 0.9 | 0.04734 | 1.484 | 1.028 | 12 / 120 | nie liczony (budżet) |
| B50 | 0.5 | 0.04791 | 1.475 | 0.980 | 12 / 120 | nie liczony (budżet) |
| B30 | 0.3 | 0.04814 | 1.478 | 0.988 | 12 / 120 | **tak, od 10.5 m (Δ_A), 11.0 m (Δ_B)** |

Spadek orbity przychodzi między B(W) 12 a 3 (C12 1.725, C3 1.533) i dalej się nie pogłębia (B90–B30 1.475–1.484); VAL rośnie
monotonicznie z dociskiem.

## Przesłanki twierdzenia o pętli

1. Profil S(v, d₁) dla B30 na 𝒟 i 𝒞 — **dowiedziony** (E3, testy 0 wyjątków), S(0.3) od 10.5 m.
2. Lemat U (stan w pudełku od k-tego ticka po włączeniu sieci, dowolny stan początkowy) — **dowiedziony** (E3, półszerokość ≤ 0.311).
3. Wejścia lotu w 𝒞 (P1) — **zmierzone**: 99.19% / 99.63% ticków; poza nimi zdanie nie mówi nic.
4. Sytuacja w 𝒟 (P2) i track (P3) — **zmierzone**: 100% i 99.94%.
5. Wysokość z regulatora (P4) — **założona** (PION nieotwarty); B30 z pionem z sieci: 0 ucieczek w 700 biegach (informacyjnie).
6. Przełożenie komendy na dystans (napęd, obrót wersora) — **rachunek z założeniem A1**, nie dowód.
7. ε_rel i U′(0) — **zmierzone / przesłanka dowodu istniejącego**.
8. Zaokrąglenia — **jawny zapas 1e-9**, nie arytmetyka kierunkowa (otwarte formalnie).
9. Bliźniak w locie — **nie lata**; cena w modelu: orbita −0.27 m/s (−15%), najgorsza rodzina −0.51 m/s wobec Z.

## Liczby do rozliczenia (bez rozliczenia)

- P-BLIZ-1: VAL K 0.04136 (CC 0.0414), B90 0.04734 (0.0473), B50 0.04791 (0.0479), B30 0.04814 (0.0481).
- P-BLIZ-2: B30 i B50 — 12/12 TEST, 120/120 wszystkie.
- P-BLIZ-3: Ś5 nie zachodzi; MLP 0.294 m/s.
- P-BLIZ-4: v_t B90 1.484, B50 1.475, B30 1.478 wobec GRU 1.674; najgorsza rodzina 1.028 / 0.980 / 0.988 m/s.
- P-BLIZ-5: C3 1.533 m/s.
- P-BLIZ-6: C12 1.725 wobec K 1.740 m/s (różnica 0.015).
- P-BLIZ-7: Ś3 zachodzi — S(0.3) od 10.5 m (od 10.0 m 99.934%).
- P-BLIZ-8: S(1.0) od 11.75 m (B30, Δ_A).
- P-BLIZ-9: Z i K — U_k półszerokość 1.0 (pełny zakres) w 20 000 komórek.
- P-BLIZ-10: Ś4 nie zachodzi — 0 kontrprzykładów; min ku od 10 m 0.776 (próbki, Δ_A) / 0.778 (kierowane, Δ_B).
- P-BLIZ-11: B30 − Z przy stojącym celu −0.294, przy celu w ruchu −0.260 m/s.
- P-BLIZ-12: kandydata brak.

## Odchylenia od promptu

1. **Ś1 literalnie dla B90 i C3** (B(W) z wag ponad γ o 1 ulp, zaokrąglenie rzutu); praca nieprzerwana, bo dowód stoi na B30
   (B = 0.3 dokładnie, w dowodzie z zapasem). Do decyzji CC.
2. **Szczebel E2** zrealizowany jako wartość średnia po całej historii (zmienne: stan początkowy i sytuacje), nie jako F̂ krok po
   kroku; daje to samo co E1 (−4.4). Wariant ze skurczem B(W) (`U_skurcz`, `ku_skurcz`) policzony na próbie i odrzucony.
3. **E3 = formy afiniczne z podziałem adaptacyjnym**, nie sam podział X₀/X₁ (2 i 3 części na wszystkie współrzędne
   kosztowałoby ok. 26 h na komórki ≥ 9.5 m); podział tylko w θ, d, v_r, v_t i tylko w komórkach, w których potrzebny.
4. **Dziedzina dowodu od 8.0 m**, nie od 4.0 m (profil S zaczyna się wyżej; lemat U policzony na tych samych komórkach).
   Komórki to pudełka 0.25 m/s przecinające koło |v| ≤ 3.2, przycięte do ±3.2 — nadzbiór koła.
5. **Δ_B**: moje 0.438 m w dystansie (CC 0.81); per prompt używam swoich.
6. **Δ_B okrojone w budżecie**: komórki od 9.5 m, etap 1 tylko dla ograniczeń < 0.3, bez etapu 2. Profil S(0.6…1.2) przy Δ_B jest
   przez to pesymistyczny; S(0.3) rozstrzygnięte.
7. **B50 dowodu nie liczyłem** (budżet; kolejność §2: B30 najpierw).
8. **Kontrola Z i K** na próbie 20 000 komórek, nie na całej dziedzinie.
9. **R2 (b)**: statystyki „po 30 s” i „pierwsze 30 s”, intruz: v_t celu = |Δq|/dt; okrążenia: |Σ Δφ| kąta drona wokół celu.
   Wektory w `petla_*.npz` co 4. tick.
10. **H-PAMIĘĆ**: „cel stoi” = prędkość celu < 0.05 m/s (po 10 s).
11. **(e)** biegi po 300 s (jak PĘTLA), nie 90 s.
12. **Rachunek złożenia**: wzór na przyrost dystansu przy opóźnieniu i inercji przy starcie z 3.2 m/s od celu; ściana z GNSS
    bez U′ (założenie). Moja propozycja, nie wzór z PĘTLI.
13. **Narzędzie `bz_r3.py`**: jego `main` (pierwsze podejście E1/E2 z U) nie był uruchamiany do wyników; używane są z niego
    `historie` i pomocnicze funkcje.
14. **Pliki poza commitem**: kawałki `r3e_B30_*_[0-6].npz` (scalone w `r3_B30_A.npz`, `r3_B30_B.npz`). Odtwarzanie:
    `bz_trening.py <ramię>` → `bz_petla.py petla|lawka|pion <ster>` → `bz_jakobian.py` → `bz_przeslanki.py` →
    `bz_r3e.py B30 A i 7` (i = 0…6) i `DMIN=9.5 OKROJONY=1 bz_r3e.py B30 B i 6` → `bz_r3m.py B30 A 7`, `bz_r3m.py B30 B 6`
    → `bz_kontrola.py` → `bz_kontr.py B30 A|B` → `bz_rachunek.py` → `bz_tabele.py`.
15. **Zegar**: start 13:52, koniec 15:48 (ok. 116 min w budżecie 180); procesy × wątki ≤ 8.
