# RECON_NADIR — druga kamera w dół + znaczniki naziemne (PROMPT_NADIR_S0, 0 bootów)

Wykonawca · 9.11.2026 · łańcuch NADIR, po CO-KOTW-2 (`d5094aef` na origin). Sesja deskowa: zero bootów, SITL,
renderów, treningu; zero edycji istniejących plików; nowe pliki wyłącznie `results/NADIR_RECON/**`.
Kamera nadir i znaczniki istnieją tu tylko jako liczby.

## Raport płaski

- **Pokrycie z pełną postawą** (FANTOM S2, s = 15 m, fazy misji): ≥1 znacznik 99.96%, ≥2 naraz 53.6%,
  max przerwa 0.54 s, r_h p50 6.7 m.
  - Te same dane z samym yaw (warunki CC): 99.93% / 64.8% / 1.63 s / 6.7 m.
  - Liczby CC (99.9% / 61% / 1.01 s / 6.5 m / 4.4 cm/px) **zgadzają się dla ≥1, r_h i skali**.
  - **Przechyły nie psują pojedynczego pokrycia ani przerw.** Zabierają ~11 pp pokrycia parą (65 → 54%).
  - Postawa: odchylenie od pionu p50 3.2°, p95 ≤ 11.4°. Do 42.6° tylko w ~2 s szarpnięć na początku i końcu epizodu.
- **ε_fix p50 jednym wierszem:** 0.37 m (OPT) / 0.65 m (ZMIERZ, δψ 5.8°) w trybie 1. W trybie 12 (para, gdy jest)
  0.26 / 0.36 m. Liczone w locie na siatce s = 10.
- **Werdykt R5: NIE pusty. Dopuszczalnych jest 264 z 540 kombinacji** (s × przesunięcie × bramka detekcji ×
  wariant × tryb).
  - Komplet 48/48 komórek: s = 10 m, przesunięcie 0, tryb 1 lub 12, warianty OPT i ZMIERZ, przy każdej bramce
    poza W 0.5 z ID.
  - Najmniejszy zapas: 0.61 m (OPT), **0.11 m (ZMIERZ tryb 1)** w c08_s02 (m 2.99).
  - s = 20 m odpada w całości przy przesunięciu 0 (przerwy orbity do 7.8 s).
- **Bezterminowość:** spełniona trywialnie. τ_max w fazach misji wynosi 0.0 s (s10 geometria), ≤ 0.96 s (s10, ID W1),
  1.3 s (s15) wobec 70 s.
  - **Zejścia D5 częściowo wypadają z pokrycia:** pokrycie 24–48%, τ do 7.1 s (s10) i 10.8 s (s20); poniżej ~6 m
    kadr robi się za mały.
  - Budżetu to nie łamie, bo Δ_D5 = 1.524 zdjęto z zejść całkiem bez poprawek. Litera warunku („zejścia nie
    wypadają z pokrycia”) jest jednak niespełniona — nazywam to wprost.
- **Detekcja rachunkiem:**
  - **W = 1 m z ID przechodzi:** bok ≥ 18 px w 99.9% próbek misji przy s = 10.
  - **W = 0.5 m przechodzi tylko jako centroid bez ID:** p50 11 px, ≥ 12 px w 16% próbek. ID przy W = 0.5 pada,
    jak przewidział prompt.
  - W = 2 m: 39–44 px.
  - Progi to założenia do S1 (§R4).
- **Ryzyko R4 jednym zdaniem:** znaczniki są w stożku centralnym kamery misji prawie zawsze (99.6% próbek,
  22–33 m, skrót sin 21°, 2.8 px p50 dla W 1 m), a w ≤ 5° od intruza w 39% próbek (s10). W paśmie [5, 18] m nie
  zdarza się to wcale. Czy det_v2 na nich strzela, rozstrzyga dopiero S1. Bramka pozycji przewidywanej zostaje
  warunkiem PRE.
- **NOWE w R3 — mechanizm, nie prereg:** sam wariant B (poprawka tylko w osłonie) **nie znosi limitu czasu misji**.
  - Sieć dostaje `own_pos` z EKF (`harness/feed_vision.py:5,287`), a setpointy są pozycjami w ramie EKF
    (`r01/exec_lib.py:40-43`, streamer `r02/gate_run_r02.py:305-333`).
  - Bez poprawki dron leci po dryfującym EKF. Osłona wie, gdzie jest, ale tylko blokuje. Na obwiedni ε_b misja
    w komórce p50 trwa wtedy ~21 s, tyle co T*.
  - Lot bez limitu wymaga, by poprawka dotarła do ramy wykonania. Możliwe są dwie drogi: **B+** (przesunięcie
    ramy w harnessie: skorygowany `own_pos` dla sieci, setpointy przesunięte z powrotem do ramy EKF; EKF
    nietknięty) albo **A** (EV do EKF2). Obie dotykają FROZEN, więc to decyzja CC (§R3).
- **Prereg śmierci przy biurku: nie zachodzi.**
  - R5 niepusty.
  - W = 1 m przechodzi detekcję rachunkiem.
  - Pełna postawa nie psuje przerw.
- **Wycena:** 4 etapy, ~20–27 bootów (§R6).
- Diff-stat i porcelain na końcu. Sygnał: **STOP-NADIRR**.

## §0. Bramka

- origin/master = `d5094aef` (CO-KOTW-2): `ANEKS_KOTW-2.md` w korzeniu, sha256 `4fb787ab…48fb9` PASS.
  `origin/master..HEAD` puste; porcelain czysty poza `?? results/DEMO_C/**`.
- FROZEN tylko do odczytu: `kotw_r1.py` importowany READ-ONLY (load, CAM, F, EDGE), `rotmats` skopiowane
  z `kotw2_obwod.py`.
  - Krzywa `s2_freeze_bf.json` (ae19f66c): ε_b(0) 0.323, ε_b(1) 0.462 … ε_b(69) 6.03.
  - Marginesy z `results/KONT_RECON/r4_margin.json` (48 komórek, m 2.99–14.4).
  - δψ_ZMIERZ = 5.81° z `results/KOTW_RECON/r2/r2p_yaw.json`.

## §R1. Pokrycie z pełną postawą

**Metoda** (`tools/nadir_r1.py`; surowe dane w `r1_pokrycie_raw.json.gz`, agregat w `r1_pokrycie.json`):
- **Korpus:** ten sam co KOTW. FANTOM S2 104 epizody, KONT S4 28, PERC2 S2 8, SKAN2 S1 8 — razem 148, 46 bootów,
  próbki GT ~31 Hz z całego lotu.
- **Kamera nadir:** oś optyczna −z_body, sztywna, w środku ciężkości. f = 269.5 px, 640×480, szerokość kadru
  poprzecznie do kadłuba.
  - Stożek centralny edge ≥ 0.10 (jak w admisji): ±43.5° × ±35.4°.
  - Rzut przez **pełny kwaternion z GT** (body FLU → ENU).
- **Siatka znaczników:** węzły s ∈ {10, 15, 20} m, |węzeł| ≤ R_E = 32 m, z = 0. Dwa przesunięcia:
  - „0” — węzeł w (0,0), czyli pod home i pod hold;
  - „pol” — siatka przesunięta o s/2.
- **Fazy:** approach / hold / orbit z `demo.jsonl`; zejscie_D5 od zdarzenia `refuse` do końca epizodu;
  wznoszenie / miedzy_epizodami / po_misji z osi czasu; z ≤ 0.3 m pominięte.
- **Przerwy:** dziury < 0.25 s łączone, jak w KOTW.
- **Rozmiar znacznika:** rzut boków ±W/2 wzdłuż E i N, bierzemy krótszy bok w px.
- **Kontrola CC:** ten sam kod z `NADIR_SAMYAW=1` (postawa zredukowana do yaw); agregat w
  `r1_pokrycie_samyaw.json`.

**Fazy misji, wszystkie kampanie (pełna postawa):**

| siatka | ≥1 | ≥2 | max przerwa ≥1 [s] | max przerwa orbity | r_h p50/p95 [m] | kąt padania p50/p95/max [°] |
|---|---|---|---|---|---|---|
| s10 „0” | 1.0000 | 0.967 | 0.0 | 0.0 | 3.8 / 5.8 | 17 / 25 / 33 |
| s10 „pol” | 1.0000 | 0.9998 | 0.0 | 0.0 | 4.1 / 6.9 | 18 / 34 / 44 |
| s15 „0” | 0.9995 | 0.518 | 1.3 | 1.3 | 6.7 / 9.9 | 28 / 39 / 52 |
| s15 „pol” | 0.962 | 0.739 | 26.1 (hold) | 1.3 | 5.7 / 10.3 | 25 / 42 / 54 |
| s20 „0” | 0.878 | 0.097 | 7.8 | 7.8 | 6.7 / 12.2 | 29 / 45 / 62 |
| s20 „pol” | 0.835 | 0.204 | 29.1 (hold) | 5.0 | 7.8 / 12.5 | 32 / 46 / 64 |

- **Przesunięcie siatki ma znaczenie przy hold.** Hold ~8.4 m nad (0,0) przy s ≥ 15 i siatce „pol” nie ma
  znacznika w kadrze przez 26–29 s.
  - Wniosek projektowy: **węzeł pod punktem hold/home**, czyli siatka „0”.
- **Porównanie z CC** (FANTOM S2, s15 „0”, fazy misji):
  - sam yaw: 99.93 / 64.8% / 1.63 s / r_h 6.69;
  - pełna postawa: 99.96 / 53.6% / 0.54 s / 6.70.
  - **Zgadza się** pokrycie ≥1, r_h i skala alt/f = 12/269.5 = 4.45 cm/px.
  - **Nie zgadza się** pokrycie parą: przechyły zabierają 11 pp.
  - Max przerwy: różnica metody (u mnie łączenie dziur 0.25 s i stożek 0.8). Przy pełnej postawie wychodzi
    **krótsza**, nie dłuższa.
- **Postawa:** odchylenie osi z_b od pionu p50 3.2° (mediana bootów), p95 do 11.4°.
  - Max 42.6° w 6 bootach FANTOM, ok. 68 próbek na boot. To szarpnięcia tuż po `episode_start` i przy powrocie
    po `episode_end` (r8_B: 110.2 s i 417.7 s), nie artefakt.
- **Rozmiar znacznika (krótszy bok najbliższego widocznego, fazy misji):**
  - W 0.5 m: p5 / p50 = 9.8 / 11.1 px;
  - W 1 m: 19.6 / 22.2 px;
  - W 2 m: 39.2 / 44.4 px.
  - Hold (~8.4 m) daje +20%.
- **Profil wysokości** (s10 „0”, cały lot):
  - ≥ 7 m: 100%;
  - 6–7 m: 99.3%;
  - 5–6 m: 95%;
  - 4–5 m: 86%;
  - < 4 m: 68–74% (to głównie wznoszenie nad węzłem home).
  - Przy s15 pokrycie 100% dopiero od ~11 m; przy s20 nie ma go na żadnej wysokości (84–99%).
  - Geometria: kadr centralny ±0.71·alt na krótszej osi gwarantuje węzeł dopiero przy alt ≳ s.
- **Zejścia D5** (12 epizodów KONT S4): pokrycie 45% / 48% / 34% / 45% / 24% / 30% (s10 „0” … s20 „pol”);
  τ_max 7.1 / 6.5 / 9.2 / 9.3 / 10.8 / 10.0 s.

## §R2. Model poprawki nadir

**Model** (`nadir_r1.eps_fix`, tabela analityczna w `r2_poprawka.json`, wartości z lotu w `r5_pila.json`).
θ to kąt padania od pionu, D zasięg skośny, r_h odległość pozioma, a = δθ + px/f.
- rad = D/cosθ · a + δz · tanθ (człon postawy i piksela; alt/cos²θ = D/cosθ; człon skali).
- lat = r_h · tan δψ + D · a (człon kursu).
- ε1 = hypot(rad, lat).
- **Tryb 2 (para):** kurs z pary δψ2 = atan(√(e_a² + e_b²)/L). e_a i e_b to błędy różnicowe piksela,
  D/cosθ · px/f; błąd postawy jest wspólny dla obu znaczników i pary nie obraca. Skala z pary:
  δz2 = min(δz, alt² · √2 · px/(f·L)).
- **Tryb 12:** para, gdy jest w kadrze, inaczej tryb 1.
- **Warianty:**
  - OPT: px 1, δψ 2°, δθ 0.5°, δz 0.2 m;
  - ZMIERZ: px 2, δψ 5.81°, δθ 0.5°, δz 0.2 m;
  - ZMIERZ_h1.8: δz 1.8 m (bias wysokości z KONT S1).
  - δθ, δz i px to **założenia** (niezmierzone).

**ε_fix [m] przy alt 12 m, dron poziomo, tryb 1 / para L = 15 m:**

| r_h | θ | px (W 1 m) | OPT | ZMIERZ | ZMIERZ_h1.8 | ZMIERZ para |
|---|---|---|---|---|---|---|
| 0 | 0° | 22.5 | 0.21 | 0.27 | 0.27 | 0.27 |
| 4 | 18° | 20.2 | 0.38 | 0.67 | 1.02 | 0.37 |
| 6 | 27° | 18.0 | 0.47 | 0.90 | 1.41 | 0.44 |
| 8 | 34° | 15.6 | 0.58 | 1.13 | 1.81 | 0.52 |
| 10 | 40° | 13.3 | 0.69 | 1.36 | 2.23 | 0.63 |
| 14 | 49° | 9.5 | 0.93 | 1.86 | 3.08 | 0.89 |

- **Strome kąty nie mnożą błędu pary** (`para_bez_mnozenia`). ε2 / ε1 przy *idealnym* kursie wynosi:
  - OPT: 0.90–0.97;
  - ZMIERZ: 1.08–1.15;
  - ZMIERZ_h1.8: 0.33–0.40 (para zbija bias wysokości).
  - δψ z pary: 0.5–1.2°.
- **Kontrast z obwodem KOTW:** tam para przecinała pierścienie zasięgu pod kątem γ (1/sin γ). Tu każdy znacznik
  daje pełną pozycję 2D (rad ≈ lat), a para służy tylko do kursu i skali.
- **W locie** (mediana p50 epizodów, s10 „0”):
  - tryb 1: OPT 0.37, ZMIERZ 0.65, ZMIERZ_h1.8 0.98 m;
  - tryb 12: 0.26 / 0.36 / 0.36 m.
- **Asocjacja.** Znacznik z ID (klasa ArUco) myli się tylko przy błędnym dekodowaniu. Centroid bez ID kojarzy się
  z najbliższym węzłem siatki i myli, gdy e_as = ε_fix(poprzednia) + ε_b(τ) + ε_obs ≥ s/2.
  - Max e_as w locie, s10 „0” (s/2 = 5): OPT 1.42, ZMIERZ 2.41, **ZMIERZ_h1.8 5.17 — przekracza**.
  - s15 „0” (s/2 = 7.5): 2.36 / 4.40 / 7.13.
  - s20 „0” (s/2 = 10): 4.43 / 7.17 / 11.88.
  - **Centroid bez ID jest bezpieczny tylko przy δz ≤ 0.2 m albo w trybie z parą.** Pomyłka asocjacji to błąd
    o całe s, który się utrwala, więc rekomendacja to ID.

## §R3. Droga wstrzyknięcia (inwentarz)

- **Wariant B** (RECON_KOTW §R3, `r03/kont_shield.py:13,56,149-160`): zegar τ od ostatniej przyjętej poprawki
  zastępuje t_KONT; r_est = |p_fix + (p_EKF(t) − p_EKF(t_fix))|; bariera ε_fix + ε_b(τ) + Δ_D5.
  - **Kadencja ~1 s niczego w nim nie zmienia.** Ta sama krzywa, ten sam P9_kont z resetem zegara; τ_max
    w misji ≤ 1.3 s, więc pracuje tylko koszyk ε_b(0..1) = 0.32–0.46 m.
  - Warunek ważności B jest nadal niezmierzony (RECON_KOTW §R3): przyrost dryfu w późnym oknie [t_fix, t_fix + τ]
    ≤ ε_b(τ). Przy τ ≤ 1.3 s chodzi o przyrost w 1 s — S2 go zmierzy.
- **NOWE — B sam nie znosi limitu misji (mechanizm).** Osłona B wie, gdzie jest dron, ale niczego nie poprawia:
  - sieć dostaje `own_pos_ned` z EKF (`harness/feed_vision.py:5,152,228,287`);
  - wykonanie idzie przez setpointy **pozycyjne w ramie EKF**: `OffboardControlMode.position = True`
    (`r01/exec_lib.py:40-43`), streamer 20 Hz (`r02/gate_run_r02.py:305-333`).
  - Dron leci więc trajektorią zadaną w ramie EKF, przesuniętą o dryf EKF e(t). Osłona B z poprawną pozycją
    przepuszcza tylko, dopóki e(t) ≤ m − (ε_fix + ε_b(τ) + Δ_D5).
  - Na obwiedni (ta sama krzywa, która zdefiniowała T*) w komórce p50: m 5.79 − 0.37 − 0.32 − 1.52 = 3.58 m.
    ε_b(20) = 3.478 ≤ 3.58 < ε_b(21) = 3.738, więc **~21 s, tyle co T* = 22 s.**
  - Osłona zostaje bezterminowa (zawieranie), ale **misja nie**. Po przekroczeniu bariera daje REFUSE.
- **Co znosi limit:** poprawka musi dotrzeć do ramy, w której wykonuje się zadanie.
  - **B+ (rama w harnessie):** skorygowane p_corr zamiast `own_pos` z EKF dla sieci i feedu; setpointy wracają
    do ramy EKF przez sp_EKF = sp_net + (p_EKF − p_corr).
    - Nie rusza EKF, PX4, wag sieci ani detektora.
    - Dotyka `feed_vision` (źródło `own_pos`, FROZEN w kanonie percepcji) i streamera.
    - Sieć dostaje wtedy pozycję z błędem ≤ ε_fix + ε_b(≤ 1 s), mniejszym niż w 2d. Czy to „w rozkładzie” sieci,
      sprawdzi S2.
  - **A (EV → EKF2):** przy s10 przerwy w misji wynoszą 0–0.96 s, poniżej timeoutu „no aid” 1 s
    (`ev_pos_control.cpp:269`). Cykl timeout → `reset_pos_to_vision` (`:217-224`) w misji więc nie zachodzi;
    w zejściach D5 tak (τ do 7 s).
    - A przestaje być zdyskwalifikowany timeoutem, **ale przestawia kanon estymatora** i unieważnia samą krzywą
      ε_b (dryf EKF z EV to inny proces) oraz charakteryzację sieci z 2d.
- **Rekomendacja z mechanizmu: B (osłona, bez zmian) + B+ (rama).**
  - B+ to jedyna droga, w której każda liczba bariery zostaje z 2d i P9_kont stoi literą: ε_b liczy przyrost
    dryfu tego samego, nietkniętego EKF.
  - A wymienia estymator, a z nim obwiednię, na której stoi dowód.
  - Obie drogi dotykają FROZEN — **decyzja CC**.
  - Jeśli żadna, NADIR daje „osłonę bez limitu, misję ~T*”, czyli nic ponad 2d.

## §R4. Percepcja i detekcja

**(i) Kamera misji a znaczniki** (`r4_kamera_misji.json`; pozioma kamera kotw_r1, siatka „0”):

| s | w stożku centralnym | w stożku przy 5–18 m | zasięg p5/p50 | depresja p50/p95 | px krótszego boku W1 p50/p95/max | ≤ 5° od intruza | to samo w [5,18] m |
|---|---|---|---|---|---|---|---|
| 10 | 99.6% | 5.4% | 22 / 33 m | 21° / 33° | 2.8 / 6.5 / 32 | 38.6% | 0 |
| 15 | 98.6% | 6.9% | 21 / 32 m | 23° / 33° | 3.3 / 6.7 / 19 | 14.0% | 0 |
| 20 | 94.0% | 0.8% | 22 / 33 m | 22° / 32° | 3.0 / 6.1 / 19 | 11.1% | 0 |

- **Inaczej niż w KOTW:** tam kotwica była w kadrze 21–35% orbity. Tu płaskie znaczniki są w dolnym kadrze
  kamery misji **prawie stale**.
  - Są małe i mocno skrócone: skrót sin(dep) ≈ 0.36, 3 px p50 dla W 1 m, do 32 px na najbliższych.
  - To statyczne, kontrastowe obiekty na gruncie. MTI nie kompensuje paralaksy (`r02/mti.py:3-4`), brama ENTRY
    nie ma minimum ruchu (`r02/config_r02.py:28-30`), a refresh tracku nie ma bramki predykcji
    (`harness/feed_vision.py:196-203`).
- **W paśmie admisyjnym [5, 18] m koincydencja z intruzem wynosi 0.** Znaczniki w kadrze przy 5–18 m to 1–7%
  próbek (niska wysokość, pochylenie).
- **Warunki PRE:**
  - bramka pozycji przewidywanej (jak w KOTW);
  - S1 mierzy fałszywe detekcje det_v2 na świecie ze znacznikami (top-1, admisja k = 3, przejęcie tracku);
  - **identyczność klatek misji poza znacznikami.**

**(ii) Detektor nadir.** Nie ma OpenCV (`import cv2` → brak modułu), więc progi biorę z dokumentacji.
- OpenCV ArUco `DetectorParameters`: `minMarkerPerimeterRate` domyślnie 0.03 największego wymiaru obrazu, czyli
  19.2 px obwodu przy 640 px ≈ **4.8 px boku** — minimalny kandydat.
  - Aruco3: obraz kanoniczny znacznika 16–32 px.
  - Ani dokumentacja, ani wyszukiwanie nie podają empirycznej tabeli minimalnego rozmiaru dla niezawodnego ID.
- **Przyjęte progi — ZAŁOŻENIA do sondy S1, nie pomiar:**
  - CEN5: centroid plamy bez ID, ≥ 5 px boku;
  - ID12: ArUco 4×4, 6 komórek z ramką, 2 px na komórkę, ≥ 12 px;
  - ID18: 3 px na komórkę, ≥ 18 px.
- **Zderzenie z R1** (fazy misji, s10 „0”):

| W | p5 / p50 px | ≥ 5 | ≥ 12 | ≥ 18 | ID przechodzi? |
|---|---|---|---|---|---|
| 0.5 m | 9.8 / 11.1 | 100% | 16% | 0.01% | **nie** (tylko centroid) |
| 1 m | 19.6 / 22.2 | 100% | 100% | 99.9% | **tak** (ID12 i ID18) |
| 2 m | 39.2 / 44.4 | 100% | 100% | 100% | tak |

- Rozmiar to krótszy bok najbliższego znacznika przy pełnej postawie. Rozmycie ruchu (90 px/s przy 4 m/s na 12 m)
  i okluzja przez nogi x500 w stożku ±43° nie są modelowane — S1.

## §R5. Piła bez limitu

**Rachunek** (`tools/nadir_r2r5.py` → `r5_pila.json`):
- Per próbka GT: u(t) = ε_fix(ostatnia obs.) + ε_b(⌊τ⌋) + Δ_D5, τ = t − t_ostatniej obs.
- Obserwacja wymaga znacznika w stożku centralnym ∧ px ≥ progu bramki (najbliższy znacznik; w trybie 2
  także partner).
- Komórka domyka się, gdy każdy jej epizod ma obserwację ∧ max u w fazach misji ≤ m_komórki.
  - Zejścia D5 są poza u, bo Δ_D5 już je wycenia, zdjęte bez poprawek.
- Dopuszczalna kombinacja (jak KOTW R5′) wymaga naraz:
  - ≥ 24/48 komórek;
  - najgorsza orbita siatki się domyka (max τ w orbicie; remis łamany największym u, bo przy nadirze τ ≈ 0
    w wielu epizodach);
  - start się domyka (ε_fix + ε_b(τ_s) + Δ_D5 ≤ R_E − D_STOP − r_max);
  - τ_max < 70 s;
  - dla CEN5 dodatkowo asocjacja e_as < s/2.
- 540 kombinacji: 6 siatek × 10 bramek (geom, CEN5/ID12/ID18 × W) × 3 warianty × tryby 1 / 2 / 12.

**Wynik: 264/540 dopuszczalnych.**
- Według s: s10 125/180, s15 107/180, s20 32/180 — tylko „pol” w trybach 1 i 12, bez δz 1.8.
- Według bramki: ID przy W 0.5 0/108; geometria i W ≥ 1 po 31–37 na 54.
- Według wariantu i trybu: ZMIERZ_h1.8 w trybie 1 tylko 8/60 (bias wysokości); para to naprawia (tryb 2 31/60).

**Konfiguracje z kompletem i zapasem** (s10 „0”):

| bramka | wariant / tryb | komórki | max u siatki | min zapas (komórka) | τ_max misji | e_as max |
|---|---|---|---|---|---|---|
| ID18 W1 | OPT / 1 lub 12 | 48/48 | 2.39 | 0.61 (c08_s02) | 0.96 s | 1.41 |
| ID18 W1 | ZMIERZ / 1 lub 12 | 48/48 | 2.88 | **0.11** (c08_s02) | 0.96 s | 2.39 |
| geom | ZMIERZ / 12 | 48/48 | 2.41 | 0.60 (c08_s02) | 0.0 s | 2.15 |
| geom | ZMIERZ_h1.8 / 12 | 48/48 | 2.78 | 0.41 | 0.0 s | 5.17 |
| ID18 W1 | ZMIERZ_h1.8 / 1 | 44/48 | 3.54 | −0.54 (c08_s02) | 0.96 s | 5.17 |

- **Wąskie gardło to 4 komórki o małym marginesie:** c08_s02 / c08_s04 / c11_s02 / c11_s03, m 2.99–3.42.
  - Przy τ ≈ 0 zostaje ε_fix ≤ m − 0.32 − 1.52 ≈ 1.1–1.6 m, więc ZMIERZ w trybie 1 ledwo się mieści.
  - **Rachunek wymaga ID i trybu 12.**
- **Tryb 2 (tylko para) jest gorszy od 12:** hold przy s10 „0” nie ma pary (64%), więc τ dochodzi do 13 s w hold
  (c08_s04 −1.44).
- s15 „0”: OPT 48/48 (zapas 0.33), ZMIERZ 45/48 — c11_s02 −0.49 przy τ 1.26 s.
- s20 „0”: przerwa orbity 7.8 s (c11_s02) ⇒ u 4.91 > 3.02 przy OPT.
- **Bezterminowość:** τ_max w fazach misji 0–1.6 s (s10/s15 przy bramkach przechodzących), do 13.5 s (s20 „pol”);
  wszędzie < 70 s, gdzie są obserwacje.
  - Zejścia D5: τ do 7.1 s (s10), poza u — patrz Raport płaski.
- **Zastrzeżenie R3:** R5 to rachunek zawierania (osłona). „Bez limitu” dla misji wymaga B+ albo A.

## §R6. Wycena i śmierci dla PRE

Rekomendowana konfiguracja wejściowa: siatka s = 10 m z węzłem pod home/hold, znacznik W = 1 m z ID (ArUco 4×4),
tryb 12, osłona B + rama B+.

| etap | zakres | booty | śmierć |
|---|---|---|---|
| S1 sonda | wariant modelu x500 z drugą kamerą (nadir, f 270, 640×480) + świat ze znacznikami klasy dekalu (addytywny); identyczność klatek misji poza znacznikami; det_v2 na świecie ze znacznikami (top-1 / admisja k = 3 / przejęcie tracku); detekcja ID nadir na żywo (wymaga OpenCV z aruco — zmiana środowiska do zgody); pierwsza poprawka vs GT; tempo z drugim renderem | 2–3 (+1) | detekcja ID W1 w orbicie < 95% klatek ∨ ε_fix p95 > ZMIERZ z R2 ∨ fałszywa admisja / przejęcie tracku na znaczniku ∨ tempo < 0.93 z drugą kamerą ∨ okluzja nogami psuje stożek |
| S2 piła pod misją | loty bez GNSS, B offline + B+ w pętli; rozkład przyrostu dryfu w oknach ≤ 1 s (warunek ważności B); zachowanie sieci na p_corr | 4–6 | przyrost dryfu w oknie > ε_b(τ) ∨ max u > m w komórce siatki ∨ degradacja misji sieci na p_corr |
| S3 osłona τ-zegar | nakładka B + B+ (rama), certy P9 z resetem zegara, P1/P5/P7 | 0–1 | cert nie przechodzi |
| S4 bramka | epizody ≥ 5 × T* = 110 s bez GNSS, siatka cięć jak KONT S4 + nominały | 12–16 | breach ∨ u > m ∨ FP admisji ∨ REFUSE fałszywy |

**Razem ~20–27 bootów.**

**Prereg śmierci przy biurku (PROMPT §R6):**
- R5 pusty — **NIE** (264/540; 48/48 przy s10, ID W1, tryb 12, OPT i ZMIERZ).
- Żadne W ≤ 2 m nie daje detekcji rachunkiem R4 — **NIE** (W 1 m: ≥ 18 px w 99.9%; W 0.5 tylko centroid).
- Pokrycie z pełną postawą psuje przerwy ponad budżet piły — **NIE** (max przerwa misji s10 0.0 s, s15 1.3 s;
  pełna postawa nie gorsza od samego yaw).

⇒ **Śmierć przy biurku nie zachodzi.** Do decyzji CC zostaje mechanizm z R3: bez B+ albo A NADIR daje osłonę
bez limitu, ale misję ~T*.

**Założenia do sondy (niezmierzone):**
- δθ 0.5°, px 1–2, δz 0.2 m (1.8 jako czułość);
- progi detekcji CEN5 / ID12 / ID18;
- kamera w środku ciężkości, grunt płaski, brak okluzji nogami, brak rozmycia ruchu, kadencja ~15 Hz
  (+0.07 s do τ — koszyk ε_b(0) bez zmian);
- warunek ważności B (przyrost dryfu w późnym oknie).

## Reprodukcja

```
G=("FANTOM_S2=results/FANTOM/camp/r*" "PERC2_S2=results/PERC2/s2/b*" "SKAN2_S1=results/SKAN2/s1/b*" "KONT_S4=results/KONT/s4/[cn]*")
PYTHONDONTWRITEBYTECODE=1 python3 -W ignore results/NADIR_RECON/tools/nadir_r1.py /tmp/r1_raw.json "${G[@]}"
gzip -9 -n -c /tmp/r1_raw.json > results/NADIR_RECON/r1_pokrycie_raw.json.gz
NADIR_SAMYAW=1 PYTHONDONTWRITEBYTECODE=1 python3 -W ignore results/NADIR_RECON/tools/nadir_r1.py /tmp/r1_samyaw_raw.json "${G[@]}"
PYTHONDONTWRITEBYTECODE=1 python3 -W ignore results/NADIR_RECON/tools/nadir_r2r5.py results/NADIR_RECON /tmp/r1_samyaw_raw.json
```

- Surowy plik samego yaw (42 MB) jest poza repo; w repo jest jego agregat `r1_pokrycie_samyaw.json`.
- Surowy plik pełnej postawy jest skompresowany (`gzip -n`, bez znacznika czasu).

## Diff-stat i porcelain

```
 results/NADIR_RECON/RECON_NADIR.md          |    337 +
 results/NADIR_RECON/r1_pokrycie.json        |   4906 +
 results/NADIR_RECON/r1_pokrycie_raw.json.gz |    Bin 0 -> 3548781 bytes
 results/NADIR_RECON/r1_pokrycie_samyaw.json |   4901 +
 results/NADIR_RECON/r2_poprawka.json        |    454 +
 results/NADIR_RECON/r4_kamera_misji.json    |    113 +
 results/NADIR_RECON/r5_pila.json            | 252187 +++++++++++++++++++++++++
 results/NADIR_RECON/tools/nadir_r1.py       |    390 +
 results/NADIR_RECON/tools/nadir_r2r5.py     |    199 +
 9 files changed, 263487 insertions(+) — wyłącznie results/NADIR_RECON/**, zero modyfikacji istniejących plików
```
Porcelain po commicie: czysty poza `?? results/DEMO_C/**` (sprzed sesji).
