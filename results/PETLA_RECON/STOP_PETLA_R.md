# STOP-PETLA-R — recon PĘTLA przy biurku: co da się dowieść o pętli sieć–napęd–osłona i gdzie ona pęka

LiquidPatrol · wykonawca · 18.11.2026 · PROMPT_PETLA_S0 (sha256 a73c5cb9,
„sha ok” Olgi, sygnał „otwieram pętlę”). Commity przed reconem:
- [CO-TEACH2-2] `b2146b1b`;
- [CO-PETLA-0] `edb4b5fd`.

**0 bootów.** Sieć, cechy, osłona i kod lotu bez zmian.

**Śmierci:**
- **Ś2 zachodzi:** H-PION potwierdzona na modelu.
- **Ś5 zachodzi:** żaden opis Ω nie certyfikuje niczego, 0%.
- **Ś1 nie zachodzi.**
- **Ś3 nie zachodzi.**
- **Ś4 nie zachodzi** w przedziale 0 tabeli. W przedziałach 2–9 ρ* jest poniżej 8 m (§R6).

**Wierność modelu jest zdana:**
- **W1:** 0.142 m/s przy progu 0.15.
- **W2:** 13 z 15 lotów przy progu 12.

**Najważniejsze:**
- **Ucieczka wysokości.** Zachodzi w napędzie N i we wszystkich czterech napędach odchylonych, przy 1.0 i 0.5 m/s, z szumem i bez. Zawsze w górę, najwcześniej po 30.2 s.
- **Rzadkość.** Ucieczka jest rzadka: 0–7 na 900 biegów na napęd, łącznie 56 na 63 000 biegów sieci w rodzinach.
- **Kruchość.** Zdarzenie siedzi na ostrzu: w najlepszym otwartym kontrprzykładzie znika już przy przesunięciu toru o +0.05 s. Odporność trzech najlepszych to 0, 1 i 0 z 20 powtórzeń.
- **Bez kanału pionowego sieci** (wariant W) pościg w poziomie trzyma dystans ≤ 11.18 m i promień drona ≤ 20.81 m.

## R1 — mapa odmów (z kodu)

**Droga od wejścia do komendy:**
1. **Cechy.** `bench/features.py:23-32`: rel = trk − own, gdzie own = p_corr (`results/TEACH/tools/teach_flight.py:671-677`). trk także jest w ramie p_corr, bo percepcja przy `NADIR_MODE=1` bierze own_pos z ramy B+ (`harness/percep_proc.py:128-151`). Wektor względny jest więc spójny ramowo, a jego błąd ~1 m nie zależy od dryfu EKF (R2).
2. **Obcięcie wieku i normalizacja.** `clip_age` z wiekiem ≤ 1.0 (`net/dataset.py:104-112`), potem (x − mean)/std (`r03/controllers/net_controller.py:87-88`).
3. **Krok sieci.** `NCP20.step_np` (`net/models.py:127-138`), potem `clip_v` do |v| ≤ 3.0 (`r03/controllers/common.py:10-16`).
4. **Cel pozycyjny.** tgt = own_net + v·1.0 s (`net_controller.py:118`). Do ramy EKF wraca jako sp_EKF = sp_net + (p_EKF − p_corr) (`teach_flight.py:678-680`).
5. **Utrata tracka.** Gdy feed nie istnieje, track jest nieważny albo wiek > 1.0 s: v = 0, sieć nie robi kroku, stan zamrożony, faza „hold” (`net_controller.py:106-111`).
6. **Owijki.**
   - `SkanScan` i `AkwScan` zmieniają wyłącznie yaw w hold (`skan2_scan.py:79-96`, `akw_scan.py:91-109`).
   - `FantomScan` prowadzi kwarantannę K1 od startu epizodu: delegat widzi „brak tracku”, sieć nie robi kroku, dopóki nie zajdzie jedno z trzech: A (track invalid → valid), B (skok > 5 m) albo C (3.0 s) (`fantom_scan.py`).
   - Stan sieci zeruje się per epizod: `ctrl.reset()` w `teach_flight.py:619-621` woła `net_controller.py:69-75`.

**Odmowy w misji w porządku osłony** (latch > R-POS > R-KONT/piła > R-G > abort/hold/return > R-G-NOM > OBSERVE/R-AUTH > patrol, `r03/kont_shield.py:21`, `r03/nadir_shield.py:19`):

**latch (R-T)** — zatrzask z R-G albo R-A (`r01/shield.py:147-151`).
- Wynika z innej odmowy.

**R-POS** — `pos_flag` z dead-reckoning z debounce/histerezą (`r01/shield.py:76-95, 153-160`). Uzbrojony po cięciu albo po wejściu (`teach_flight.py:693-697`). Akcja: D5 z zatrzaśnięciem do ziemi.
- Sieć nie ma na nią wpływu; to zdrowie estymatora.

**R-KONT, przyczyna τ\*** — τ ≥ τ\* − 2·dt = 2.05 s (`r03/nadir_shield.py:311`). Tylko bez GNSS. Zatrzask do NOMINAL, akcja D5.
- Sieć może ją wywołać pośrednio, wyprowadzając drona poza obszar mapy. W locie i w R3 TEACH-II: 0.

**R-KONT, przyczyna bariera** — r_est > R(i), R(0) = 24.84 m … R(9) = 21.13 m (`nadir_shield.py:313`, `r_nad3`:143). Tylko bez GNSS; zatrzask, D5.
- Sieć może ją wywołać sama, ruchem poziomym (§R6).

**R-G poziomo** — |cel| > R_E = 32 albo pozycja + hamowanie > 32 (`r01/shield.py:101-109`). Zatrzask (terminal), w driverze zawis i koniec epizodu (`teach_flight.py:752-756, 804-805`).
- Bez GNSS wynika z innej odmowy: przy r_est ≤ R(0) = 24.84 cel ≤ 27.84 i pozycja + hamowanie ≤ 27.09 < 32, więc bariera piły jest zawsze pierwsza.
- Z GNSS sieć może ją wywołać sama, tylko przeskokiem ponad R-G-NOM: cel > 32 wymaga r > 29.0 m, czyli 1.7 m za R_nom. Przeskok modelu przy 3 m/s wynosi ok. 3·(0.35 + 0.3) = 1.95 m. Niezmierzone.

**R-G pionowo** — |cel_z| > V_E = 20 albo |pos_z| > 20 (`r01/shield.py:110-111`), cel_z = z + vd·1 s. Zatrzask, zawis, koniec epizodu.
- Sieć może ją wywołać sama (kanał pionowy, H-PION), z GNSS i bez. z w ramie poprawionej = z EKF, bo Δ jest tylko w N i E.

**abort / hold / return** — tryby operatora (`r01/shield.py:169-185`).
- Sieć nie ma na nie wpływu; tryb misji to PATROL.

**R-G-NOM** — r_est > R_nom = 27.30 ∧ cel na zewnątrz (`r03/kont_shield.py:200-205`). Bez zatrzasku: składowa na zewnątrz odjęta (`r03/kont_gate.py:40-45`), lot trwa (`teach_flight.py:743-751`).
- Z GNSS sieć może ją wywołać sama.
- Bez GNSS wynika z innej odmowy: R_nom > R(i) dla każdego i, więc bariera jest pierwsza.

**OBSERVE / R-AUTH** — tryb OBSERVE.
- Nie dotyczy, misja to PATROL.

**Dolna granica wysokości: nie istnieje.** Osłona sprawdza tylko |z| > V_E (`r01/shield.py:110`). Bramka komend przy ALLOW i R-G-NOM przepuszcza vd bez zmian (`r03/kont_gate.py:40-45`). Driver zna wysokość tylko przy przyziemieniu w zejściu (`Z_GROUND`, `teach_flight.py:155, 739`). Sieć ma o wysokości wyłącznie rel_z (`teach_flight.py:401`: „sieć nie dostaje komendy wysokości”).

**Litera dostępności a R-G-NOM.** Tick R-G-NOM ma dec = REFUSE, więc `teach_analyze.py:418` liczy go do „REFUSE w misji” i (D1) albo (D-L) staje się niespełnione, choć lot trwa.

## R2 — replay i obwiednie (`r2.json`, `r2b.json`, `r2_wektory.npz`)

| liczba | CC | tu | |
|---|---|---|---|
| ticki inferencji (15 lotów) | 57 222 | 57 222 | zgodne |
| największa różnica komendy (replay vs log) | do 0.003 m/s | 0.0027 m/s, 0 ticków ponad 0.005 | zgodne |
| ticki misji (ALLOW, bez zejścia, z inferencją) | 54 563 | 54 563 | zgodne |
| ku min przy d 10–10.5 m (n, < 1 m/s) | −0.001 (519, 107) | −0.0007 (518, 107) | n różni się o 1 |
| ku min przy 10.5–11 m (n) | 0.883 (102) | 0.883 (102) | zgodne |
| ku min przy 11–11.5 m (n) | 1.533 (7) | 1.533 (7) | zgodne |
| największy dystans w misji: z cech / prawdziwy | 11.11 / 11.17 | 11.106 / 11.174 | zgodne |
| po misji, 11–11.5 m: ku min | 0.14 | 0.140 | zgodne |
| po misji, od 13 m: ku min | 2.07 | 2.074 | zgodne |

- **Obwiednie cech w misji:**
  - rel_x −10.04…9.70, rel_y −9.37…11.09, rel_z −4.16…3.72;
  - v_n −2.59…2.53, v_e −2.75…2.78, v_d −1.30…0.94;
  - wiek 0…1.0, valid = 1.
- **Stan sieci** w [−0.864, 0.876]. 8 pierwszych składowych głównych niesie 99.22% wariancji.
- **Wiek tracka:** mediana 0.064 s, p95 0.096 s, max 0.996 s; ponad 0.15 s 66 ticków, ponad 0.5 s 22.
- **Wiek podmieniony** na 0.2 / 0.5 / 1.0 s na stanach z lotów:
  - najmniejsza składowa ku celowi przy d ≥ 9 m: −1.61 / −1.62 / −1.64 m/s (p1 −1.00 / −1.02 / −1.06);
  - zmiana komendy pionowej: max 0.026 / 0.071 / 0.147 m/s.

  Sam wiek tracka odwraca pościg poziomy przy d ≥ 9 m.
- **Błąd wektora względnego** (poziomo):
  - pierwsze 30 s: p50 0.40 m, p99 1.32 m, max 11.96 m (akwizycja);
  - reszta: p50 0.26 m, p99 1.07 m, max 1.364 m (CC: 1.40).
- **e_trk:**
  - pierwsze 30 s: max 11.99 m;
  - reszta: p50 0.42 m, p99 1.01 m, max 1.601 m (CC: 1.60).
- **Szum per oś po 30 s** (AR(1) do W2, R4, R5):
  - N: std 0.310 m, czas korelacji 4.3 s;
  - E: std 0.320 m, czas korelacji 4.4 s;
  - D: std 0.034 m, czas korelacji 1.8 s.

## R3 — model napędu (`r3_naped.json`, `r3_w2.json`)

**Dopasowanie:**
- **Poziom** (loty parzyste listy): opóźnienie 7 ticków (0.35 s), inercja 0.3 s. RMSE dopasowania 0.136 m/s.
- **W1 na lotach nieparzystych: 0.142 m/s, PASS.** Per lot 0.127–0.148.
- **Pion** (skoki komendy zejścia 0 → 1.5 → 0.7 m/s, wiersze `ekf`, 13 lotów z zejściem): opóźnienie 1 tick (0.05 s), inercja 0.1 s, RMSE 0.056 m/s. Dopasowanie leży na brzegu siatki (najmniejsze τ).

**Napędy:**

| napęd | opóźnienie poziomu | inercja poziomu | opóźnienie pionu | inercja pionu |
|---|---|---|---|---|
| N | 0.35 s | 0.3 s | 0.05 s | 0.1 s |
| P− | 0.35 s | 0.3 s | 0.05 s | 0.05 s |
| P+ | 0.35 s | 0.3 s | 0.05 s | 0.2 s |
| H− | 0.25 s | 0.3 s | 0.05 s | 0.1 s |
| H+ | 0.45 s | 0.3 s | 0.05 s | 0.1 s |

**W2: 13 z 15 lotów, PASS.**

| lot | wynik W2 |
|---|---|
| p01–p08, p10, p11, p13, p14, L1 | spełnione |
| p09 | mediana dystansu +0.70 m (próg ±0.6) |
| p12 | promień −1.56 m (próg ±1.5) |

## R4 — H-PION (`r4a.json`, `r45.json`, `r45_czesci/`, `szukanie_r4.json`, `kontr.json`)

**Bez napędu** (45 388 stanów misji po 30 s) — potwierdzam (e):
- **Komenda pionowa a własna prędkość pionowa:** korelacja 0.994, nachylenie 0.955, mediana |vd − own_vd| 0.013 m/s.
- **Czułość jednokrokowa:**
  - na own_vd: mediana 0.992 (p5 0.74, p95 1.30);
  - na rel_z: mediana +0.038 1/s (stała czasowa 26.3 s), ujemna w 8.7% stanów.
- **Czułość ustalona** (400 stanów, 20 s z zamrożonym wejściem):
  - na rel_z: mediana +0.030, **znak odwrotny w 23.75%** (CC: 14.7%);
  - na own_vd: mediana 0.76.
- **Tablica pościgu po prostej:** wznoszenie przy rel_z ≥ 4 i vd malejące z rel_z dla namiarów −150°, −120° i −90°. Zgodne z CC.
- **Orbita:**
  - CCW: wznoszenie przy rel_z ≥ 4 dla −120°, −90°, 30°, 60° i 90°;
  - CW: dla −150°, −120°, −90°, 0° i 30°.

**W pętli, rodziny** (wariant „sieć jak leci”, 900 biegów × 300 s). Zdarzenia |rel_z − 2| > 8 m, zapis „z szumem / bez szumu”:

| v 1.0 m/s | N | P− | P+ | H− | H+ |
|---|---|---|---|---|---|
| postój | 0/0 | 0/0 | 1/0 | 0/0 | 0/0 |
| wahadło | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| odcinki | 1/0 | 1/0 | 0/0 | 0/0 | 1/0 |
| krążenie | 1/0 | 0/0 | 1/0 | 0/0 | 1/0 |
| ucieczka | 1/0 | 2/1 | 1/0 | 2/0 | 0/0 |
| podejście | 0/0 | 0/1 | 1/0 | 1/1 | 0/0 |
| nagonka | 0/0 | 1/0 | 1/0 | 0/0 | 1/0 |

| v 0.5 m/s | N | P− | P+ | H− | H+ |
|---|---|---|---|---|---|
| postój | 1/1 | 1/0 | 0/1 | 0/0 | 1/1 |
| wahadło | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| odcinki | 0/0 | 0/0 | 1/0 | 0/0 | 0/0 |
| krążenie | 0/2 | 0/1 | 0/1 | 2/0 | 0/0 |
| ucieczka | 2/3 | 3/0 | 2/1 | 2/0 | 1/1 |
| podejście | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |
| nagonka | 2/1 | 2/0 | 0/0 | 0/2 | 0/0 |

- **Zdarzenia razem:** przy 1.0 m/s 21, przy 0.5 m/s 35.
- **Kierunek:** wszystkie w górę, żadne w dół.
- **Czas do zdarzenia:** min 30.2 s (0.5 m/s) i 33.4 s (1.0 m/s).
- **Po zdarzeniu:** pościg się rozpada. Mediana największego dystansu po zdarzeniu wynosi 121 m (1.0) i 145 m (0.5). Model nie ma osłony; w locie R-G pionowy zatrzasnąłby zawis przy 20 m.

**Szukanie R4** (CEM: populacja 300, elita 30, 200 iteracji, napęd N, szum):
- zdarzenie w 8 iteracjach; najlepsze 224.3 m w iteracji 32 (t_ev 41.4 s);
- rozkład szukania nie skupił się na zdarzeniu: mediana populacji na końcu 2.72 m.

**H-PION: potwierdzona na modelu.** Zdarzenie zachodzi w napędzie N i we wszystkich czterech odchylonych.

**Trzy najlepsze kontrprzykłady otwarte** (napęd N; ranking po najwcześniejszym zdarzeniu). Każdy odtwarza się bitowo z wsadu.

| # | źródło (ziarno, indeks) | t_ev | max \|rel_z − 2\| | odporność: z szumem / bez szumu | pliki |
|---|---|---|---|---|---|
| 0 | postój 0.5 m/s bez szumu (ziarno 71017, indeks 318) | 34.9 s | 226.9 m | 0/20 / 0/20 | `kontr_0_log.npy`, `kontr_0_manifest.json` |
| 1 | szukanie R4 (ziarno 500032, indeks 169) | 41.4 s | 224.3 m | 1/20 / 2/20 | `kontr_1_log.npy`, `kontr_1_manifest.json` |
| 2 | krążenie 0.5 m/s bez szumu (ziarno 101017, indeks 846) | 49.75 s | 208.1 m | 0/20 / 1/20 | `kontr_2_log.npy`, `kontr_2_manifest.json` |

- **Kontrprzykład 0** zachodzi przy przesunięciu toru 0 i −0.05 s, a przy +0.05 s już nie: max |rel_z − 2| spada do 4.8 m.
- **Eksport torów do manifestu:** sprawdziany ANEKS_TEACH2-1 zdane we wszystkich trzech:
  - krok 0.0500 / 0.0997 / 0.0500 m przy progach 0.051 / 0.1007 / 0.051 m;
  - promień 11.000 m;
  - zgodność z zapisem do 4e-9 m.
- **Zapis per tick** (`pl_bieg.KOLUMNY_LOGU`): t, pozycja intruza, p i v drona, 8 cech, 20 stanów sieci, komenda.

## R5 — pościg w poziomie (`r45.json`, `szukanie_r5.json`)

**Wariant W** (pion regulatorem vd = clip(0.5·(rel_z − 2), ±1)), rodziny × napędy × szum:

| v | ucieczek | dystans prawdziwy max | dystans z cech max | promień max | ku min przy d z cech ≥ 10.5 / 11 / 12 m |
|---|---|---|---|---|---|
| 1.0 | 0 | 11.18 m | 10.86 m | 20.81 m | 1.956 m/s / nie osiągnięto / nie osiągnięto |
| 0.5 | 0 | 10.63 m | 10.02 m | 20.77 m | nie osiągnięto |

Szukanie R5 (cel: dystans prawdziwy) dało najlepiej 11.153 m przy promieniu 19.91 m. **Ś3 nie zachodzi.**

**Sieć jak leci, biegi bez ucieczki:**

| v | dystans max | z cech max | promień max | ku min przy ≥ 10.5 / 11 / 12 m |
|---|---|---|---|---|
| 1.0 | 12.64 m | 12.43 m | 22.11 m | 0.203 / 0.806 / 1.89 m/s |
| 0.5 | 12.04 m | 11.93 m | 22.18 m | 0.48 / 1.07 m/s / nie osiągnięto |

## R6 — rachunek złożenia (`r6.json`)

Łańcuch nierówności (w ramie p_corr, poziomo):
1. |q| ≤ ρ — definicja klasy.
2. |trk| ≤ ρ + e_trk — algebra.
3. r_est = |p_corr| ≤ |trk| + |rel_net| = ρ + e_trk + D — `features.py:28-29`, `nadir_shield.py:326-330`.
4. e_trk ≤ e′ + ε_rel — algebra.
5. e′ ≤ U′(i) — przesłanka istniejącego dowodu (P9_teach); w lotach 0 przekroczeń.
6. ε_rel ≤ 1.364 m — zmierzona: 45 388 ticków po 30 s. W pierwszych 30 s do 11.96 m, czyli poza przesłanką.
7. D ≤ D_max — zmierzona (loty 11.106 m) albo z modelu (R5: 10.856 m).
8. ALLOW ⇔ r_est ≤ R(i) — `nadir_shield.py:311-313`, tabela z sumą.

**Korekta (c):** ρ + D ≤ 20.69 m przy przesłankach dowodu (CC: 20.65) i ≤ 23.24 m przy błędach zmierzonych (zgodne).

| przedział i | R(i) | U′(i) | ρ* dowód, D loty | ρ* zmierzone, D loty | ρ* dowód, D R5 | ρ* zmierzone, D R5 |
|---|---|---|---|---|---|---|
| 0 | 24.84 | 2.79 | 9.58 | 12.13 | 9.83 | 12.38 |
| 1 | 24.22 | 3.41 | 8.35 | 11.51 | 8.60 | 11.76 |
| 2 | 23.63 | 3.99 | 7.17 | 10.93 | 7.42 | 11.18 |
| 3 | 23.04 | 4.59 | 5.98 | 10.33 | 6.23 | 10.58 |
| 4 | 22.61 | 5.02 | 5.12 | 9.90 | 5.37 | 10.15 |
| 5 | 22.27 | 5.36 | 4.44 | 9.56 | 4.69 | 9.81 |
| 6 | 21.99 | 5.64 | 3.88 | 9.28 | 4.13 | 9.53 |
| 7 | 21.79 | 5.84 | 3.48 | 9.08 | 3.73 | 9.33 |
| 8 | 21.40 | 6.22 | 2.71 | 8.69 | 2.96 | 8.94 |
| 9 | 21.13 | 6.50 | 2.16 | 8.42 | 2.41 | 8.67 |

## R7 — wykonalność dowodu zdania S (`r7.json`, `r7_najgorsze_*.npy`)

- **Zbiór stanów:** 446 563, w tym 54 563 z lotów i 392 000 z biegów R5 (wariant W, 7 rodzin, napęd N, szum, co 20 ticków).
- **Budżet:** 20 000 komórek na sektor, czyli 320 000 na opis. Arytmetyka przedziałowa sprawdzona na pudełkach zerowej szerokości (różnica wobec punktu 3e-15).

| opis | udział certyfikowany | czas | łamiące S w 10⁵ próbek | najgorsze ku |
|---|---|---|---|---|
| Ω1 (p1–p99 per neuron) | 0.0% | 1.8 s | 392 | −2.02 m/s |
| Ω2 (PCA: 8 osi p1–p99) | 0.0% | 1.7 s | 3478 | −2.65 m/s |
| Ω3 (16 sektorów × znak v_t, +10%) | 0.0% | 1.2 s | 8273 | −2.98 m/s |

**Ś5 zachodzi.** Pudełko wejścia (d 10.5–13, dowolny namiar w sektorze 22.5°, |v_h| ≤ 3.2, rel_z 0–4) razem z pudełkiem stanu jest za szerokie dla przedziałów przez 20 tanh. Dziesięć najgorszych punktów każdego opisu jest w plikach.

## Opcje (bez wyboru)

1. **Boot potwierdzający w gz** na wyeksportowanym torze (`kontr_0..2_manifest.json`). Odporność na modelu jest 0–2 z 20, więc pojedynczy boot najpewniej nie odtworzy zdarzenia.
2. **Wysokość poza siecią.** Pion trzymany regulatorem zewnętrznym (wariant W): w modelu zero ucieczek i pościg ≤ 11.18 m.
3. **Ściana bez zatrzasku wewnątrz bariery piły** (dziś R-G-NOM leży na 27.30 m, za barierą 24.84 m).
4. **Dowód poziomy na opisie z R7.** Na dziś 0% przy wszystkich trzech opisach.
5. **Zamknięcie wynikiem negatywnym:** zdanie „pętla nie dochodzi do odmowy w misji” jest fałszywe na modelu dla sieci takiej, jaka leci.

## Liczby do rozliczenia P-PETLA-R1 … R9 (bez rozliczenia)

- **R1:** replay 57 222 ticków, największa różnica 0.0027 m/s, 0 ticków ponad 0.005; w misji ku przy d ≥ 10.5 m min 0.883 m/s.
- **R2:** W1 0.142 m/s, W2 13/15, Ś1 nie zachodzi.
- **R3:** czułość jednokrokowa vd na own_vd, mediana 0.992; ustalona czułość na rel_z, znak odwrotny w 23.75% z 400 stanów.
- **R4:** Ś2 zachodzi (zdarzenia w N i w 4 z 4 napędów odchylonych).
- **R5:** najlepszy otwarty kontrprzykład odporny w 1/20 powtórzeń (z szumem) i 2/20 (bez szumu).
- **R6:** wariant W: dystans prawdziwy max 11.18 m, promień max 20.81 m; Ś3 nie zachodzi.
- **R7:** ρ* przy przesłankach dowodu dla D z lotów, przedział 0: 9.58 m.
- **R8:** ρ* przy przesłankach dowodu dla D z R5, przedział 0: 9.83 m. W przedziałach 2–9 od 7.42 do 2.41 m.
- **R9:** najlepszy opis Ω certyfikuje 0.0%.

## Odchylenia od promptu (każde osobno)

1. **(b) 10–10.5 m:** n = 518 zamiast 519; minimum −0.0007, nie −0.001.
2. **Znak odwrotny odpowiedzi ustalonej** 23.75% wobec 14.7% u CC. Moja definicja: 400 stanów losowych (ziarno 0) z misji po 30 s, 400 kroków z wejściem zamrożonym, różnica przy rel_z + 0.1 m.
3. **Pion dopasowany na brzegu siatki** (τ = 0.1 s, opóźnienie 1 tick). P− ma inercję 0.05 s, poza siatką klasy.
4. **H± = ±2 ticki** (±0.1 s).
5. **Model wejścia sieci:** rel prawdziwy + szum AR(1) per oś (średnia, std i czas korelacji z R2 po 30 s; również oś D). Prędkość własna = prędkość modelu. Wiek stały = mediana 0.064 s, track zawsze ważny. Bez utrat tracka i bez kwarantanny K1.
6. **Rodziny:**
   - postój — radialnie do krawędzi, potem stoi;
   - wahadło — start na tej samej średnicy 6–11 m;
   - odcinki — prędkość równa v_max, odbicie radialne na krawędzi;
   - krążenie — po dojściu do krawędzi.
7. **Szukanie:** CEM z celem szumiącym, wspólne liczby losowe w iteracji. Najlepszy wynik odtworzony przez wsad populacji z powielonym wektorem, bo szum wiersza zależy tylko od ziarna i B.
8. **Odporność:** 20 powtórzeń z szumem (ziarna 4242–4261) i przesunięciem s_k = −2 + 4k/19 s. Dla kontrprzykładów bez szumu dodatkowo 20 powtórzeń bez szumu z samym przesunięciem.
9. **Model bez osłony.** Biegi trwają po zdarzeniu, w locie R-G zatrzasnąłby zawis przy 20 m. „Dystans po zdarzeniu” opisuje model, nie lot.
10. **R7:** |v_h| ≤ 3.2 zastąpione pudełkiem v_r, v_t ∈ [−3.2, 3.2] (nadzbiór). Budżet 20 000 na sektor podzielony 2 × 10 000 na znak v_t. W Ω3 komórka z mniej niż 5 stanami bierze pudełko globalne.
11. **Ś4 liczona dla przedziału 0** (bariera główna, jak w (c)). Dla przedziałów 2–9 ρ* jest poniżej 8.0 m.
12. **`r7_stany.npz` (85 MB) nie jest w commicie.** Odtwarza go deterministycznie `pl_r7.stany()`: stany lotów z R2 i biegi R5 o ziarnach 900000–900006.
13. **Pamięć podręczna lotów** `dane/*.npz` (3.8 MB) jest w commicie; odtwarza ją `pl_dane.py`.

**Zegar:** ok. 25 min liczenia (R4/R5 8 procesów ok. 7 min, szukanie 2 × ok. 10 min równolegle), w budżecie 120 min.
