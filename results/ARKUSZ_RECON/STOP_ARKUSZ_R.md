# STOP_ARKUSZ_R — ARKUSZ, recon przy biurku: dowód z mechanizmu

LiquidPatrol · wykonawca · 20.11.2026 · PROMPT_ARKUSZ_S0 (sha256 3c11cafd…, byte-check PASS z wklejki), [CO-ARKUSZ-0] `db497e4c`.
**0 bootów**: żadnego gz / PX4 / kolejki. Sieć, wagi, cechy, osłona i kod lotu bez zmian.

**Śmierci: zaszła Ś4; Ś1, Ś2, Ś3 nie zaszły.** Udział czasu pobytu z dowiedzionym lematem na najlepszym szczeblu: **0%** (obok 0% PĘTLI).
Żaden szczebel (D1, D2, D3; k = 1 na wszystkich 5 095 605 parach, k = 1, 10, 20 na próbie 400 komórek) nie dowiódł lematu dla
ani jednej komórki. Każda procedura przedziałowa zdała test poprawności (10⁶ punktów, 0 wyjątków), więc to nie jest Ś1.
Arkusz istnieje (R1: wariancja niewyjaśniona na lotach testowych 0.22% w medianie, w modelu 0 komórek pofałdowanych), stany
czułe są rzadkie i w pętli nie mają znaczenia w sensie Ś3 (R2). Dowód nie przechodzi z trzech przyczyn, zmierzonych osobno:
(1) w zwykłej metryce pudełkowej krok sieci rozdmuchuje resztę 2.7–3.4 razy na tick (‖|∂F/∂h|‖∞ p50 3.46; ρ(|∂F/∂h|) p50 2.12,
więc żadne skalowanie diagonalne nie pomaga), choć promień spektralny ∂F/∂h ma p50 0.92; (2) baza własna, w której krok jest
skurczem (‖|T⁻¹JT|‖∞ p50 0.92), nie jest ciągła między sąsiednimi komórkami (‖|T_c′⁻¹ J T_c|‖∞ p50 1.14, cond T p50 52);
(3) człon promienia jakobianu przedziałowego na pudełku komórki daje 5–7 razy więcej niż człon środka, a przy składaniu k kroków rośnie
wykładniczo (półszerokość ograniczenia ~10¹³ przy k = 10). Ponadto lemat w brzmieniu promptu przy k = 10 i 20 jest **fałszywy**
w części komórek: ciągi wejść dopuszczalnych (stałe pchnięcie δ = ±Δ) wyprowadzają prawdziwe stany z arkusza o ponad 0.25
w komórkach niosących 10.7% (k = 10) i 20.4% (k = 20) czasu pobytu; przy k = 1 kontrprzykład jest jeden (1 komórka).
Stąd przy tych wejściach nie istnieje cienka (≤ 0.25 od arkusza) niezmiennicza rodzina zbiorów zawierająca dane, w żadnym
kształcie; sufit punktu stałego z próbek potwierdza to dla postaci D1 i D2 (99.99% i 99.97% czasu ponad limitem).

## R1 — arkusz

Mapa: dopasowanie afiniczne w komórce siatki (d, θ, vr, vt) i jej sąsiadach (±1; przy < 30 punktach ±2, ±3), regresory
[1, d, θ, vr, vt, rel_z, vd, wiek] względem środka komórki, grzbiet 1e-6 (`tools/ar_wspolne.py`). Odniesienie: jedna mapa
afiniczna globalna.

### (a) Loty — 15 lotów, ticki misji ≥ 30 s od pierwszego kroku sieci; test p03, p07, p09, p12, p13 (`r1.json` → R1_1_loty)

| miara | CC | wykonawca, siatka | siatka ×2 | ocena |
|---|---|---|---|---|
| ticki misji | 45 686 | 45 388 (uczące 33 822, testowe 11 566) | — | różnica 298 (odch. 1) |
| war. niewyjaśniona, mediana neuronów | 0.3% | **0.22%** | 0.26% | zgodne co do rzędu |
| war. niewyjaśniona, najgorszy neuron | 1.4% | **0.90%** | 1.18% | różnica (lepiej) |
| reszta |h − Φ| per wpis p50 / p99 | 0.006 / 0.060 | **0.0044 / 0.057** | 0.0041 / 0.071 | zgodne |
| reszta p99.9 / max | — | 0.138 / **1.23** | 0.180 / 0.50 | — |
| reszta w normie max per tick p50 / p99 / max | — | 0.014 / 0.115 / 1.23 | 0.013 / 0.153 / 0.50 | — |
| rozrzut neuronu (std, mediana) | 0.31 | 0.313 | — | zgodne |
| błąd komendy poziomej p50 / p99 | 0.08 / 0.51 m/s | **0.051 / 0.485** | 0.050 / 0.652 | zgodne co do p99 |
| błąd komendy p99.9 / max | — / 1.14 | 1.31 / **2.63** | 1.64 / 3.17 | różnica max (2.63 vs 1.14) |
| odniesienie: mapa globalna, war. niewyj. mediana | — | 7.8% (reszta p99 0.30) | — | — |
| historia (s sprzed 0.5 s i 1.0 s) | „nic nie dodaje” | 0.216% → 0.215%, p99 0.0565 → 0.0565 (11 466 ticków) | — | zgodne |

Pokrycie testu: 100% (siatka), 99.4% (×2); sąsiedztwo ±1 dla 91.5% ticków. Dwudziestu najgorszych ticków (lista w
`r1.json` → `najgorsze_20`, wektory `r1_loty_wektory.npz`): 11 z p07 tick 772–781 (t 32.2–32.6 s, faza orbit, d 7.7–7.9 m,
własna prędkość ~0.3 m/s — orbita jeszcze nieustalona, rel_z 2.6, vd +0.12; reszta do 1.23, błąd komendy do 2.63 m/s),
p03 tick 1114–1168 (vd −0.6…−0.7 m/s, rel_z 0.7–2.8: silny ruch pionowy), p12 tick 1158–1244 (rel_z 0.55, vr +1.2).
Wspólne: sytuacje rzadkie w danych uczących (mała prędkość własna na początku okna albo rel_z daleko od 2); track ważny,
wiek 0.02–0.10 s (dla p07 tick 736–778 sprawdzony ręcznie: krok sieci w każdym ticku, track i p_corr gładkie).

### (b) Z samych wag (`r1.json` → R1_5_wagi; okna 160 kroków)

| miara (norma max) | CC | loty (9 078 ticków) | model W (400) | ocena |
|---|---|---|---|---|
| od zera: max | 0.002 | **0.0019** (p99 4.2e-5) | 0.0012 | zgodne |
| od losowego U(−1, 1)²⁰: p99 / max | 0.0001 / 0.09 | 0.00016 / **0.0068** | 0.0001 / 0.0027 | p99 zgodne, max różnica (inny stan losowy) |
| punkt stały przy zamrożonym wejściu: p99 | 0.165 | **0.266** (max 1.18) | 0.188 (max 0.22) | różnica, ten sam wniosek: stan niesie opóźnienie |

### (c) Model pętli, wariant W (`r1.json` → R1_2_model_W; `tools/ar_biegi.py`)

Biegi: 7 rodzin PĘTLI × v_max 1.0 / 0.5 × 150 = **2100 biegów** po 90 s, start 8 m, stan zerowy; stany t ≥ 30 s: **2.52 mln**;
mapa na 1050 biegach parzystych, test na 1050 nieparzystych. Dystans z cech ≤ 10.44 m (prawdziwy ≤ 10.60 m).

| miara | CC | wykonawca, siatka | siatka ×2 | ocena |
|---|---|---|---|---|
| war. niewyjaśniona mediana / najgorszy neuron | 0.11% / 1.2% | **0.070% / 0.58%** | 0.076% / 0.62% | różnica (lepiej) |
| reszta p99 / p99.9 / max | 0.041 / 0.080 / 0.40 | **0.034 / 0.066 / 0.49** | 0.036 / 0.076 / 0.67 | zgodne |
| komórki zajęte | 67 431 | **62 507** | 370 967 | różnica (odch. 2–3) |
| z ≥ 8 stanami (udział stanów) | 23 195 (93.1%) | **30 605 (96.1%)** | 89 729 (71.3%) | różnica |
| półszerokość pudełka p50 / p99 / max (≥ 8) | 0.058 / 0.108 / 0.176 | **0.055 / 0.105 / 0.152** | 0.032 / 0.064 / 0.105 | zgodne |
| pofałdowane > 0.25 | 0 | **0 (z ≥ 8 i wszystkie)** | 0 | zgodne |
| błąd komendy poziomej p50 / p99 / max | — | 0.061 / 0.294 / 2.31 m/s | 0.061 / 0.325 / 3.09 | — |
| odniesienie: mapa globalna | — | war. niewyj. 20.1%, reszta p99 0.43 | — | — |

**Wymiar arkusza** (R1.3; komórki z ≥ 30 stanami, 9 812): 99% zmienności stanu niosą **6 kierunków** w medianie (rozkład 4: 146,
5: 3 606, 6: 6 060; max 6) — tyle, ile współrzędnych sytuacji zmienia się w komórce (d, θ, vr, vt, rel_z, vd; wiek stały).
Reszta po odjęciu mapy: 3 kierunki w medianie (1–6). Siatka ×2: mediana 6, max 7.

**Sieć jak leci, pion z sieci** (R1.4; 7 × 2 × 50 = 700 biegów, 0.84 mln stanów; dystans z cech do 11.94 m):
war. niewyjaśniona 0.16% (najgorszy neuron 1.7%), reszta p99 0.047, max 1.67; 41 134 komórki, 16 379 z ≥ 8 stanami;
półszerokość p50 / p99 / max 0.074 / 0.242 / 0.333; **pofałdowanych 128 z 16 379 (0.78%)** — poniżej progu Ś2, ale nie zero;
wymiar 6 w medianie (max 7), reszta 4. Wysokość z sieci pogrubia arkusz (rel_z i vd wędrują).

## R2 — stany czułe (`r2.json`, `tools/ar_r2.py`)

### (e) Pętla otwarta, 10⁶ prób na amplitudę, model W

Zaburzenie dwiema metodami: jednostajne U(−a, a)²⁰ i narożniki a·(±1)²⁰ (prompt nie określa; CC leży pomiędzy).
Wzmocnienie ‖Δh_k‖∞/‖δ‖∞, a = 0.05 (a = 0.15 daje to samo do ±0.02 w medianie):

| k | CC med / p99 / >1 | jednostajne med / p99 / max / >1 | narożniki med / p99 / max / >1 |
|---|---|---|---|
| 1 | 0.985 / — / 49% | 0.768 / 1.54 / 2.73 / 20.6% | 1.279 / 2.47 / 3.81 / 77.7% |
| 2 | — | 0.446 / 1.07 / 1.88 / 1.72% | 0.742 / 1.72 / 2.66 / 23.6% |
| 5 | — | 0.213 / 0.79 / 1.62 / 0.118% | 0.354 / 1.28 / 2.51 / 4.51% |
| 10 | 0.16 / 0.82 / 0.29% | 0.133 / 0.57 / 1.62 / 0.0114% | 0.221 / 0.94 / 2.66 / 0.651% |
| 20 | 0.066 / 0.47 / 0.03% | **0.056 / 0.34 / 2.17 / 0.0050%** (50) | **0.093 / 0.55 / 3.43 / 0.052%** (517) |
| 40 | 0.012 / 0.17 / 0.01%, max 3.3 | 0.010 / 0.12 / 2.29 / 0.0024% | 0.017 / 0.21 / 6.50 / 0.0138% |
| 80 | — | 0.0004 / 0.015 / 1.31 / 0.0003% | 0.0006 / 0.025 / 2.38 / 0.0013% |
| 160 | — | ~0 / ~0 / 0.10 / 0 | ~0 / ~0 / 0.23 / 0 |

Ocena: rząd zgodny, liczby różne (zależą od rozkładu zaburzenia). Po 160 krokach (8 s) żadna próba nie ma wzmocnienia > 1.

**Stany czułe** (wzmocnienie po 20 krokach > 1; jednostajne 50, narożniki 517): dystans jak wszędzie (p50 8.2 vs 8.26 m), ale
**mała prędkość styczna** — vt p50 0.44 (narożniki 0.65) m/s wobec 1.73 m/s dla wszystkich prób; vt > 0 w 92% (83%) wobec
77%; rodziny „odcinki” i „krążenie” (27 + 16 z 50; 189 + 196 z 517), „ucieczka” i „postój” prawie nigdy. Różnicę niesie
neuron 2 (40 z 50; 308 z 517), potem 6. Spadek poniżej 0.2: mediana 60 kroków (3.0 s), max 115 (151) kroków; nie spadło w
160 krokach: 0. Czyli: czułość pojawia się, gdy orbita nie jest ustalona (dron prawie stoi bokiem do celu).

### Pętla zamknięta (525 000 prób na amplitudę: 14 wsadów × 150 biegów × t₀ ∈ {30, 40, 50, 60, 70} s × 50 kopii, 10 s)

| miara | ±0.05 | ±0.15 (odniesienie) |
|---|---|---|
| max różnica komendy poziomej p50 / p99 / p99.9 / max | 0.16 / 0.51 / 2.49 / 4.13 m/s | 0.48 / 1.56 / 3.28 / 4.26 |
| max różnica dystansu w 10 s p50 / p99 / p99.9 / max | 0.016 / 0.125 / 0.559 / **2.28 m** | 0.047 / 0.369 / 1.33 / 3.01 |
| różnica dystansu > 1 m | **199 (0.038%)** | 1 019 (0.194%) |
| zmiana kierunku obiegu (ostatnie 5 s) | 1 195 (0.23%) | 3 628 (0.69%) |

Różnice > 1 m przy ±0.05: „odcinki” 121, „krążenie” 36, „wahadło” 23, „podejście” 10, „nagonka” 9, „postój” i „ucieczka” 0.

**Udział czasu w sytuacjach czułych** (tick czuły = któraś z 8 prób ±0.05 ma wzmocnienie po 20 krokach > 1): model W
**0.032%** (63 z 200 000 ticków), loty **0.086%** (39 z 45 088 ticków misji z 20 kolejnymi krokami).

Ś3: różnica dystansu > 1 m w 0.038% prób (próg 0.1%) i czas w sytuacjach czułych 0.03–0.09% (próg 1%) — **nie zachodzi**.

## R3 — drabina dowodu (`r3.json`, `r3k.json`, `r3f.json`, `r3e.json`; tablica `r3_tabela.json`)

Dziedzina: 62 507 komórek zajętych przez stany modelu W (t ≥ 30 s); rel_z ∈ [1.878, 2.124], vd ∈ [−0.056, 0.057] (pudełko
globalne), wiek 0.064. Δ (1.2 × max zmiana na tick w biegach R1): d 0.321 m, θ 0.0528 rad, vr 0.238, vt 0.123 m/s, rel_z
0.0495 m, vd 0.0119 m/s. Pary (c, c′): **5 095 605** (81.5 na komórkę). Zbiory startowe: obwiednia danych +10% + 1e-3;
punkt stały do CAP = 0.25 (półszerokość w jednostkach stanu), potem komórka zamrożona i niedowiedziona.

Szczeble (po jednym zdaniu):
- **D1 — pudełka:** 0% komórek, 0% czasu; obraz kroku ma półszerokość p50 0.96 (max 1.45) przy pudełkach startowych p50
  0.044 — rozejście w jednym kroku, jak (d) u CC; 10.4 s na wszystkie pary.
- **D2 — współrzędne arkusza:** 0% (k = 1 wszystkie pary; k = 1, 10, 20 próba); ograniczenie reszty półszerokość p50 1.43
  przy k = 1 (rzeczywisty rozrzut z próbek ~0.04): człon promienia jakobianu przedziałowego daje ~5× więcej niż jego środek,
  a sam środek bloku reszty ma wzmocnienie ~2.7 na krok, więc punktu stałego w tej metryce nie ma; przy k = 10 i 20 złożona
  forma Taylora rośnie do ~10¹³ i ~10²⁸; 169 s.
- **D3 — współrzędne arkusza z metryką z rozkładu jakobianu:** 0%; w bazie własnej krok w komórce jest skurczem (‖|T⁻¹JT|‖∞
  p50 0.92), ale przejście między komórkami nie (p50 1.14), a cond T p50 52 (max 1.4·10⁴) rozdmuchuje ograniczenia (p50 198
  przy k = 1); 209 s.
- **D4 — zonotopy:** niewykonane.

| szczebel | k | zakres | dowiedzione (komórki / czas) | ograniczenie reszty, półszer. p50 | operacje (pary × iteracje) | czas | test 10⁶ |
|---|---|---|---|---|---|---|---|
| D1 | 1 | wszystkie | 0 / 0 | 0.96 (obraz stanu) | 5 095 605 | 10 s | 0 wyjątków (×2) |
| D2 | 1 | wszystkie | 0 / 0 | 1.43 | 5 095 605 | 169 s | 0 (×2) |
| D3 | 1 | wszystkie | 0 / 0 | 198 | 5 095 605 | 209 s | 0 (×2) |
| D2 | 1 / 10 / 20 | próba 400 źródeł | 0 par z 39 663 / 2 482 612 / 5 563 650 | 1.5 / 3·10¹³ / 2·10²⁸ | — | 5 / 23 / 45 s | 0 (×3) |
| D3 | 1 / 10 / 20 | próba 400 źródeł | 0 / 0 / 0 | 27 / 7·10¹⁴ / 4·10²⁹ | — | 6 / 25 / 57 s | 0 (×3) |

Testy poprawności: każdy 10⁶ punktów (10⁴ par × 100; dla k-krokowych 20 komórek × 50 000 trajektorii, sprawdzana obwiednia
h_k i reszta wobec c′), zero wyjątków; najmniejszy zapas D1 0.083, D2 0.207, D3 0.58. Zaokrąglenia: zapas 1e-9 na każdym
etapie, bez arytmetyki z kierunkowym zaokrąglaniem (przesłanka otwarta, niżej).

**Sufit — czy lemat w ogóle jest prawdziwy** (`tools/ar_r3f.py`, `r3f.json`): 200 000 startów ze stanów prawdziwych, ciągi
dokładnie dopuszczalne (|s_j − s_{j−1}| ≤ Δ, wszystkie s_j w komórkach zajętych). Kontrprzykład postaci D2/D3: reszta od
arkusza w komórce końcowej > 0.25; postaci D1: brak pudełka o półszerokości ≤ 0.25 obejmującego dane komórki i stan końcowy.

| k | strategia | dopuszczalne | reszta p50 / p99 / max | kontrprzykł. D2/D3 (czas komórek) | kontrprzykł. D1 (czas) |
|---|---|---|---|---|---|
| 1 | dane (odniesienie) | 200 000 | 0.013 / 0.053 / 0.199 | 0 | 0 |
| 1 | losowe | 193 139 | 0.032 / 0.082 / 0.207 | 0 | 0 |
| 1 | pchnięcie ±Δ | 190 046 | 0.037 / 0.094 / 0.259 | 1 (0.0001%) | 0 |
| 10 | losowe | 68 131 | 0.062 / 0.194 / 0.356 | 66 (0.18%) | 0 |
| 10 | pchnięcie ±Δ | 7 057 | 0.137 / 0.440 / 0.614 | 1 629 (**10.7%**) | 96 (0.61%) |
| 10 | pchnięcie ±Δ/2 | 20 336 | 0.080 / 0.276 / 0.385 | 464 (1.02%) | 0 |
| 20 | losowe | 15 765 | 0.080 / 0.234 / 0.343 | 88 (0.18%) | 0 |
| 20 | pchnięcie ±Δ | 5 903 | 0.111 / 0.602 / 0.891 | 2 481 (**20.4%**) | 585 (4.78%) |
| 20 | pchnięcie ±Δ/2 | 7 218 | 0.106 / 0.397 / 0.559 | 690 (3.80%) | 23 (0.03%) |

Lemat k = 10 / 20 jest więc fałszywy dla cienkich zbiorów w komórkach niosących co najmniej 10.7% / 20.4% czasu (dolne
ograniczenie, szukanie losowe). Przyczyna: Δ to maksimum zmiany per współrzędna, a ciąg z tą samą zmianą przez 10–20 ticków
(dystans o 0.32 m na tick przy małym vr) jest fizycznie niespójny z prędkościami, które sieć widzi — sieć całkuje taki ciąg
i schodzi z arkusza. Przy k = 1 lemat empirycznie się trzyma (reszta ≤ 0.26).

**Sufit punktu stałego przy k = 1, wejścia dokładnie dopuszczalne** (`tools/ar_r3e.py`, `r3e.json`): zbiory startowe jak
w dowodzie, obrazy z próbek (64 na komórkę i iterację, połowa w narożnikach pudełka; s′ = s + δ, |δ| ≤ Δ, c′ = komórka s′).
To dolne oszacowanie każdej niezmienniczej rodziny tej postaci zawierającej dane. Postać D2: po 7 iteracjach zamrożone
(potrzebna odległość od arkusza > 0.25) 84.1% czasu, po 15 iteracjach **99.97%** (62373 komórek), stabilnych
0.0096% komórek. Postać D1: po 7 iteracjach 98.6%, po 15 **99.99%** (62364 komórek).
(Rozprzężony sufit z `r3.json`, nadzbiór wejść: D1 96.4% po 6 iteracjach, D2 98.6%, D3 100% od razu.)

**Wniosek z sufitu.** Gdyby lemat k = 1 zachodził dla wszystkich komórek z jakąkolwiek rodziną zbiorów odległych od arkusza
o ≤ 0.25 i zawierających dane, to przez indukcję zachodziłby dla każdego k — a kontrprzykłady k = 20 z prawdziwych stanów
kończą 0.89 od arkusza. Zatem przy wejściach dopuszczalnych w brzmieniu promptu **cienka niezmiennicza rodzina nie istnieje
w żadnym kształcie**; Ś4 nie jest wyłącznie słabością szczebli. Udział komórek, które mogą mieć lemat dowiedziony
pojedynczo (z innymi komórkami nieniezmienniczymi), pozostaje możliwy, ale żaden szczebel go nie wykazał.

## R4 — prawo na arkuszu (`r4.json`, `tools/ar_r4.py`)

**W sensie promptu: pusto** — brak komórek z dowiedzionym lematem na żadnym szczeblu.
Warunkowo, **bez dowodu lematu** (Z_c = obwiednia danych +10% + 1e-3, wszystkie 62 507 komórek; procedura przedziałowa ku
celowi zdała test 10⁶ punktów, 0 wyjątków): półszerokość przedziału komendy p50 0.61, p99 1.43, max 2.86 m/s. S′ (ku celowi
≥ 0.3 m/s) dla d₀: 9.00 → 91.2% (11 606 komórek), 9.25 → 98.8% (6 845), **9.50 → 99.91% (3 348)**, 9.75 i więcej → 100%;
**najmniejsze d₀ z ≥ 99% = 9.5 m** (warunkowo). Empirycznie (min ku po stanach danych w komórce): 8.50 → 99.78%, od 9.00 →
100%, najmniejsze d₀ z ≥ 99% = 8.5 m; przy d ≥ 9.5 m min ku po 31 073 stanach = 1.21 m/s (p1 1.34). Szerokość przedziału
warunkowego (p50 0.61 m/s) bierze się z pudełka całej komórki, nie z reszty arkusza.

## Czego brakuje do twierdzenia o pętli

1. **Arkusz istnieje** (stany = funkcja sytuacji z małą resztą) — **zmierzone** na lotach i w modelu W (R1); nie dowiedzione.
2. **Lemat arkusza k = 1 dla wszystkich komórek** — **niedowiedziony** (0% na D1–D3); empirycznie bez kontrprzykładu poza 1
   komórką. Brakuje metryki, w której krok jest skurczem jednocześnie w komórce i między komórkami, oraz ciaśniejszego jakobianu
   (podział pudełek albo postać afiniczna). Sufit punktu stałego (dokładne wejścia, próbki): 99.97% czasu wymaga
   odległości od arkusza > 0.25 — a z kontrprzykładów k = 20 wynika, że cienka rodzina niezmiennicza nie istnieje.
3. **Lemat k-krokowy** — **fałszywy** przy wejściach dopuszczalnych w brzmieniu promptu (10.7% / 20.4% czasu); wymaga zawężenia
   wejść do fizycznie spójnych (zmiana d i θ zgodna z vr, vt i obwiednią szumu; spójność prędkości z napędem).
4. **Model wejść** — że wejścia pętli (napęd + intruz + szum) leżą w zbiorze dopuszczalnym: **otwarte**; szum AR(1) jest
   gaussowski, bez twardej obwiedni, a Δ wzięto z maksimum w biegach.
5. **Prawo S′ na arkuszu** — **warunkowo** (d₀ = 9.5 m), bez dowodu lematu.
6. **Złożenie S′ z napędem i geometrią do zdania o dystansie** — **niezbadane** w tej nodze (PĘTLA: przesłanki rachunku R6).
7. **PION** (wysokość z regulatora zewnętrznego) — **założony**; z pionem z sieci arkusz jest grubszy (0.78% komórek
   pofałdowanych, R1.4).
8. **Stany czułe bez znaczenia** — **empirycznie spełnione** (0.038% prób > 1 m, 0.03–0.09% czasu), nie dowodowo.
9. **Poprawność numeryczna** — zapas 1e-9 zamiast zaokrąglania kierunkowego: **otwarte** (formalnie potrzebne).

## Liczby do rozliczenia (bez rozliczenia)

- P-ARKUSZ-1: loty testowe — wariancja niewyjaśniona mediana **0.22%**, reszta p99 **0.057** (siatka ×2: 0.26%, 0.071).
- P-ARKUSZ-2: model W — komórek o półszerokości > 0.25: **0 z 30 605** (≥ 8 stanów) i 0 z 62 507 (wszystkie); Ś2 nie zachodzi.
- P-ARKUSZ-3: po 20 krokach wzmocnienie > 1 — **0.0050%** (jednostajne ±0.05), **0.052%** (narożniki ±0.05); ±0.15: 0.0064% / 0.073%.
- P-ARKUSZ-4: Ś3 — różnica dystansu > 1 m **0.038%** prób, czas w sytuacjach czułych **0.032%** (model) / **0.086%** (loty); Ś3 nie zachodzi.
- P-ARKUSZ-5: D1 — **0%** czasu pobytu.
- P-ARKUSZ-6: Ś4 — najlepszy szczebel **0%** czasu pobytu; Ś4 zachodzi.
- P-ARKUSZ-7: najlepszy szczebel **0%** (próg 90%).
- P-ARKUSZ-8: S′ dowiedzione — **0 komórek** (brak dowiedzionego lematu); warunkowo d₀ = 9.5 m (99.91% z 3 348 komórek).

## Odchylenia od promptu

1. **Ticki lotów:** 45 388 zamiast 45 686 — tick misji = misja ∧ krok sieci wykonany ∧ ≥ 30 s od pierwszego kroku sieci; żaden
   z sześciu sprawdzonych wariantów definicji nie dał 45 686.
2. **Siatka sytuacji 4-wymiarowa** (d, θ, vr, vt); rel_z, vd i wiek tylko jako regresory mapy i, w R3, pudełko globalne.
   Prompt mówi „prędkości co 0.25 m/s” — vd nie dzieliłem.
3. **Biegi modelu:** 7 rodzin PĘTLI (prompt w (c) mówi o sześciu; PĘTLA ma siedem), 2100 biegów po 90 s, stany od 30 s
   (2.52 mln, CC 1.53 mln). Stąd 62 507 komórek zamiast 67 431.
4. **Sąsiedztwo mapy** rozszerzane do ±2 / ±3, gdy w ±1 jest < 30 punktów (8.5% ticków lotów testowych, 0.4% modelu).
5. **Zaburzenie w R2:** prompt nie określa rozkładu „±0.05”; podaję jednostajny i narożniki.
6. **R2.3:** 525 000 prób na amplitudę (nie 10⁶; prompt nie wymaga 10⁶ dla pętli zamkniętej); kierunek obiegu = znak średniego
   momentu w ostatnich 5 s.
7. **R2.4:** tick czuły = któraś z 8 prób ma wzmocnienie > 1 po 20 krokach; model — próbka 200 000 ticków.
8. **R3, pary w postaci rozprzężonej:** w szczeblach D1–D3 zmienne s ∈ c i s′ ∈ c′ ∩ (c ⊕ Δ) są niezależne — nadzbiór wejść
   dopuszczalnych (pomija |s′ − s| ≤ Δ wewnątrz pary). Ograniczenia pozostają poprawne, ale luźniejsze. Sufit „rozprzężony” w
   `r3.json` dotyczy tej postaci; sufit dokładny to `r3f.json` i `r3e.json`.
9. **R3, k = 10 i 20:** tylko na próbie 400 komórek źródłowych (200 jednostajnie, 200 z wagą czasu), wejścia pośrednie
   w niezależnych pudełkach (c ⊕ jΔ), zbiory startowe bez punktu stałego. Wynik 0 na próbie przy ograniczeniach ~10¹³ uznaję
   za rozstrzygający; pełnego przebiegu nie robiłem.
10. **R3, punkt stały:** ≤ 6 iteracji, CAP = 0.25 w jednostkach stanu (próg z Ś2). Dla D3 miarą jest |T_c|·max|ẽ| — dla źle
    uwarunkowanych T_c już zbiór startowy przekracza CAP w części komórek.
11. **D4** niewykonany.
12. **Dodatki poza promptem:** szukanie kontrprzykładów (`ar_r3f.py`) i sufit sprzężony (`ar_r3e.py`); R4 warunkowo, jawnie
    oznaczone jako bez dowodu.
13. **Pliki poza commitem** (odtwarzalne z ziarna, > 50 MB): `biegi_W.npz` (1.1 GB), `biegi_siec.npz` (0.37 GB),
    `r1_R1_2_model_W_wektory.npz`, `r1_R1_4_model_siec_wektory.npz`, `r2_otwarta_wektory*.npz`, `r2_zamknieta_wektory.npz`. Kolejność odtworzenia:
    `ar_biegi.py W siec` → `ar_loty.py` → `ar_r1.py loty W siec wagi` → `ar_r2.py r21 r23 r24 r21z` → `ar_r3_bieg.py`
    → `ar_r3k.py <dz.pkl>` → `ar_r3f.py` → `ar_r3e.py <dz.pkl>` → `ar_r4.py <dz.pkl>` → `ar_tabela.py`
    (`dz.pkl` = pickle `ar_r3.Dziedzina()` po `baza()`).
14. **Literatura z §1** nie była czytana w tej sesji (sieć zakazana); nie cytuję jej.

Czas: start 00:07:48, koniec 01:00:36 (ok. 52 min) (zegar systemowy zgodny z monotonicznym); procesy × wątki ≤ 8.
