# STOP-TEACHR2 — recon TEACH-S0B: żyje (Ś1 i Ś2 nie zachodzą)

Werdykt: **żyje.** PROMPT_TEACH_S0B, sha256 0543618a…, 0 bootów.

**Ś1 nie zachodzi.** Wariant M1 policzony nowym torem odtwarza `results/TEACH_RECON/r5_wyniki.json` na 6 z 6 par (łata × rodzaj cech): ta sama liczba przyjętych poprawek, ten sam największy błąd z dokładnością do 0.001 m. Naprawa przyrządu nie była potrzebna.

**Ś2 nie zachodzi.** Mapa M4 (spięta obrazem, zakotwiczona w torze EKF) z cechami SIFT spełnia oba warunki na **każdej** łacie:

| Łata | 12 cięć: max błąd | 12 cięć: max przerwa | Lot długi: max błąd | Przerwy w mapie > 2.15 s |
|---|---|---|---|---|
| S | 0.73 m | 1.4 s | 0.85 m | 0 |
| M | 0.75 m | 0.2 s | 0.95 m | 0 |
| J | 0.71 m | 0.2 s | 0.90 m | 0 |

M4 z AKAZE spełnia warunki tylko na łacie M. Na S i J ma na 12 cięciach przerwy 4.0 s i 3.4 s.

M3 (same kotwice) nie spełnia warunków na żadnej łacie. Na 12 cięciach mieści się w 1.04–1.15 m, ale w locie długim daje 1.42–1.67 m.

Wszystkie przerwy ponad 1.15 s, na każdej łacie, mapie i rodzaju cech, leżą **poza mapą**: największe pokrycie prawdziwe ich kadrów to 0.02–0.41.

Czas zegara całego dopasowania: **388 s** (8 procesów × 1 wątek cv2), w budżecie 30 min. Doliczając próbę na sucho na jednym locie (10 s) i pomiar czasu R7 (jeden proces, ok. 40 s), razem poniżej 8 min.

## R1 — sprawdzian przyrządu

Narzędzie `tools/teach2_r5.py` → `r1_sprawdzian.json`, wynik `zgodne_wszystkie: true`:

| Łata / cechy | Przyjęte S0 = S0B | Max S0 = S0B [m] |
|---|---|---|
| S / SIFT | 8550 = 8550 | 1.8138 = 1.8138 |
| S / AKAZE | 8447 = 8447 | 1.8190 = 1.8190 |
| M / SIFT | 8574 = 8574 | 1.8263 = 1.8263 |
| M / AKAZE | 8476 = 8476 | 1.8505 = 1.8505 |
| J / SIFT | 8588 = 8588 | 1.8277 = 1.8277 |
| J / AKAZE | 8436 = 8436 | 1.8587 = 1.8587 |

## R2 — wiązania sprzed cięcia

Narzędzie `tools/teach2.py` (funkcja `wiazania`), zapis `wiazania/<lot>_<łata>.json.gz`, pola [sim_j, k, r_E, r_N, zgodne, przyjęte].

Każdy kadr serii „przed” (2365 na łatę) wiąże się z ≤ 3 klatkami kluczowymi o pokryciu przewidywanym z EKF ≥ 30 %. Daje to 7110 wiązań na łatę i rodzaj cech, w tym 122 wiązania klatek kluczowych z samymi sobą (r = 0).

Przyjęte:
- SIFT: 7082 / 7096 / 7100 (S / M / J);
- AKAZE: 7069 / 7013 / 7054.

Odrzucenia wynikają wyłącznie z liczby zgodnych punktów < 12 albo braku modelu. Test odległości (| |r| − d_EKF | ≤ 1.5 m) nie odrzucił niczego.

## R3 — georeferencja

`teach2.rozwiaz`: Gauss–Newton, 6 iteracji, wagi 1 / 5 / 0.05, skala 1.

Per lot i klatkę kluczową: θ_k, t_k, liczba wiązań, θ_k − e_k i |t_k − cam_gt(k)| są w `czesci/*.json.gz` (pole `kf[].geo`). Podsumowanie w `r3_georeferencja.json`.

Łata S, SIFT, 122 klatki kluczowe w 13 lotach (S, M, J różnią się o setne):

| Mapa | \|θ_k − e_k\| p50 / p95 / max [°] | \|t_k − cam_gt(k)\| p50 / p95 / max [m] |
|---|---|---|
| M1 | 2.78 / 6.36 / 13.98 | 0.160 / 0.319 / 0.377 |
| M3 | 1.70 / 3.30 / 4.10 | 0.154 / 0.272 / 0.325 |
| M4 | 1.40 / 2.05 / 2.20 | 0.118 / 0.251 / 0.374 |

Wiązań na klatkę kluczową: min 26, p50 53.

## R4/R5 — lokalizacja po cięciu i wyniki

Łańcuch S0 na wariant (`teach2.lancuch`), zapis `czesci/<lot>_<łata>.json.gz`, pola [sim, τ, k, r_E, r_N, zgodne, poprawka_E, poprawka_N, błąd, przyjęta, innowacja, pokrycie z k, pokrycie największe].

Wyniki (`r5_wyniki.json`). „12” to 12 cięć, „L” to lot długi; przerwy w mapie i poza mapą wg największego pokrycia prawdziwego ≥ 0.50:

| Łata | Mapa / cechy | Seria | Udział przyjętych | Błąd p50 [m] | p95 [m] | max [m] | Przyjęte > 1.0 / > 1.37 / > 2.28 m | Max przerwa [s] | Przerwy > 1.15 / > 2.15 s | Max przerwa w mapie / poza mapą [s] |
|---|---|---|---|---|---|---|---|---|---|---|
| S | M1 / SIFT | 12 | 1.000 | 0.400 | 0.869 | 1.814 | 150 / 27 / 0 | 0.4 | 0 / 0 | 0 / 0 |
| S | M1 / SIFT | L | 0.981 | 0.342 | 0.798 | 1.425 | 35 / 2 / 0 | 2.6 | 6 / 1 | 0 / 2.6 |
| S | M3 / SIFT | 12 | 0.998 | 0.336 | 0.646 | 1.054 | 12 / 0 / 0 | 1.4 | 1 / 0 | 0 / 1.4 |
| S | M3 / SIFT | L | 0.982 | 0.317 | 0.840 | 1.539 | 83 / 12 / 0 | 2.6 | 6 / 2 | 0 / 2.6 |
| S | M4 / SIFT | 12 | 0.999 | 0.303 | 0.530 | 0.732 | 0 / 0 / 0 | 1.4 | 1 / 0 | 0 / 1.4 |
| S | M4 / SIFT | L | 0.981 | 0.163 | 0.390 | 0.846 | 0 / 0 / 0 | 2.4 | 6 / 2 | 0 / 2.4 |
| S | M4 / AKAZE | 12 | 0.994 | 0.295 | 0.520 | 0.717 | 0 / 0 / 0 | 4.0 | 3 / 1 | 0 / 4.0 |
| S | M4 / AKAZE | L | 0.952 | 0.158 | 0.372 | 0.775 | 0 / 0 / 0 | 5.8 | 11 / 5 | 0 / 5.8 |
| M | M3 / SIFT | 12 | 1.000 | 0.335 | 0.648 | 1.122 | 21 / 0 / 0 | 0.2 | 0 / 0 | 0 / 0 |
| M | M3 / SIFT | L | 0.991 | 0.307 | 0.841 | 1.666 | 90 / 22 / 0 | 2.4 | 3 / 1 | 0 / 2.4 |
| M | M4 / SIFT | 12 | 1.000 | 0.303 | 0.537 | 0.753 | 0 / 0 / 0 | 0.2 | 0 / 0 | 0 / 0 |
| M | M4 / SIFT | L | 0.989 | 0.160 | 0.390 | 0.946 | 0 / 0 / 0 | 2.2 | 3 / 1 | 0 / 2.2 |
| M | M4 / AKAZE | 12 | 0.998 | 0.296 | 0.525 | 0.743 | 0 / 0 / 0 | 1.6 | 2 / 0 | 0 / 1.6 |
| M | M4 / AKAZE | L | 0.960 | 0.158 | 0.358 | 0.795 | 0 / 0 / 0 | 5.4 | 8 / 4 | 0 / 5.4 |
| J | M3 / SIFT | 12 | 1.000 | 0.336 | 0.656 | 1.040 | 14 / 0 / 0 | 0.2 | 0 / 0 | 0 / 0 |
| J | M3 / SIFT | L | 0.995 | 0.315 | 0.837 | 1.637 | 91 / 22 / 0 | 2.4 | 1 / 1 | 0 / 2.4 |
| J | M4 / SIFT | 12 | 1.000 | 0.302 | 0.533 | 0.708 | 0 / 0 / 0 | 0.2 | 0 / 0 | 0 / 0 |
| J | M4 / SIFT | L | 0.992 | 0.162 | 0.405 | 0.902 | 0 / 0 / 0 | 2.2 | 3 / 1 | 0 / 2.2 |
| J | M4 / AKAZE | 12 | 0.994 | 0.295 | 0.520 | 0.709 | 0 / 0 / 0 | 3.4 | 3 / 1 | 0 / 3.4 |
| J | M4 / AKAZE | L | 0.950 | 0.160 | 0.377 | 0.789 | 0 / 0 / 0 | 5.6 | 12 / 5 | 0 / 5.6 |

Pozostałe wiersze (M1 i M3 z AKAZE, M1 dla M i J) są w `r5_wyniki.json`. Każdy z nich ma max błąd ≥ 1.05 m.

Błąd w funkcji odległości od środka klatki kluczowej (łata S, SIFT, 12 cięć, max [m]). Zależność od odległości, wyraźna w M1 i M3, w M4 prawie znika:

| Mapa | 0–3 m | 3–6 m | 6–10 m | > 10 m |
|---|---|---|---|---|
| M3 | 0.60 | 0.69 | 0.89 | 1.05 |
| M4 | 0.54 | 0.62 | 0.72 | 0.73 |

M4 wg pokrycia z k, max: 0.72 m przy ≥ 50 %, 0.73 m przy 30–50 %, 0.73 m przy < 30 %. Mediana błędu M4 na 12 cięciach (0.30 m) jest wyraźnie wyższa niż w locie długim (0.16 m).

Per lot, M4 / SIFT, łata S, max błąd: p02 0.73, p06 0.72, p01 0.68, p13 0.63, p03 0.62, p08 0.61, p07 0.55, p11 0.52, p14 0.48, p09 0.44, p04 0.40, p12 0.30, L 0.85 m. Jedyna przerwa > 1.15 s na 12 cięciach to p02 (1.4 s, pokrycie ≤ 0.28).

## R6 — kontrakt

Narzędzie `teach2_r5.py` → `r6_kontrakt.json`. Wzory jak S0: U′ = 1.5·(E + G(τ)), R = 32 − 2.85 − (U′ + 1.524). Dostępność τ_dost = największa krawędź z R − E ≥ 20 m. Wiersze dla SIFT (AKAZE w pliku):

- Łata S, M4, 12 cięć: E = 0.73 m, τ* = 1.4 s, R(τ*) = 22.59 m — mieści się; dostępność do 3.8 s.
- Łata S, M4, lot długi: E = 0.85 m, τ* = 2.4 s, R(τ*) = 21.16 m — mieści się; dostępność do 3.6 s.
- Łata M, M4, 12 cięć: E = 0.75 m, τ* = 0.2 s, R(τ*) = 25.75 m — mieści się; dostępność do 3.8 s.
- Łata M, M4, lot długi: E = 0.95 m, τ* = 2.2 s, R(τ*) = 21.16 m — mieści się; dostępność do 2.4 s.
- Łata J, M4, 12 cięć: E = 0.71 m, τ* = 0.2 s, R(τ*) = 25.81 m — mieści się; dostępność do 4.0 s.
- Łata J, M4, lot długi: E = 0.90 m, τ* = 2.2 s, R(τ*) = 21.22 m — mieści się; dostępność do 3.6 s.
- Łata S, M3, 12 cięć: E = 1.05 m, τ* = 1.4 s, R(τ*) = 22.11 m — mieści się; dostępność do 2.0 s.
- Łata S, M3, lot długi: E = 1.54 m, τ* = 2.6 s, R(τ*) = 20.03 m — mieści się; dostępność do 1.2 s.
- Łata M i J, M3, lot długi: E = 1.67 / 1.64 m, τ* = 2.4 s — mieści się z odmowami (odmowa przy przerwie > 2.2 s: 1 przerwa); dostępność do 1.0 s.

## R7 — czas

Narzędzie `tools/teach2_r7_czas.py` → `r7_czas.json`. Jeden proces, cv2 1 wątek, łata S, loty p02, p13 i L.

| Pomiar | p50 [ms] | p95 [ms] |
|---|---|---|
| Wiązanie na kadr sprzed cięcia: prostowanie, cechy SIFT i AKAZE, do 3 dopasowań na rodzaj, z renderem pomocniczym | 35.6 | 41.4 |
| Render pomocniczy (tylko przyrząd) | 3.6 | 4.9 |
| Rozwiązanie R3 na lot i rodzaj, M3 | 10.7 | 12.7 |
| Rozwiązanie R3 na lot i rodzaj, M4 | 28.8 | 31.6 |

Przy 5 Hz serii „przed” wiązanie zajmuje ~18 % czasu klatki dla obu rodzajów naraz, a jeden rodzaj mniej więcej połowę tego. Rozwiązanie M4 w chwili cięcia trwa ~30 ms.

Koszt kadru po cięciu jest jak w S0 R7: SIFT p95 24 ms, AKAZE 14 ms.

## R8 — świat, plan, pytania do PRE

**Świat: doprecyzowanie V1** (z przypiętych plików; numery linii jak w STOP-TEACHR R7):
- **Warstwa terenu:** nowy model w nowym świecie (kopia `worlds/world_nadir2_A3.sdf`, sha 7f2bbe13…). Płaszczyzna 100 × 100 m z teksturą łaty (`results/TEACH_RECON/dane/<łata>_2024-04-27.png`), `visibility_flags` 8 (bit 3), wysokość 0.005 m: nad ground_plane, pod znacznikami (z 0.03).
- **Kamera w dół „nadir” (l.127, dziś bez maski):** dodać `<visibility_mask>8</visibility_mask>`. Widzi wtedy tylko obiekty z bitem 3: warstwę terenu oraz obiekty z flagami domyślnymi (wszystkie bity), czyli ground_plane pod warstwą i sylwetki innych modeli. Nie widzi znaczników (flagi 4) ani szachownicy kont_decal (flagi 2).
  - Pytanie otwarte: obiekty z flagami domyślnymi (drony, intruz) pozostają widoczne. Jeśli kadr ma zawierać wyłącznie teren, trzeba im nadać flagi bez bitu 3, a to zmiana modeli.
- **Kamera misji „imager” (l.21):** 4294967293 → 4294967285 (~(bit 1 | bit 3)).
- **Kamera przepływu „flow_camera” (l.46):** 4294967291 → 4294967283 (~(bit 2 | bit 3)).
- **Lidar `gpu_lidar` (l.85, dziś bez maski):** dodać ~bit 3 (4294967287), żeby wysokość 5 mm warstwy nie zmieniała odległości.
- **Pliki zmieniane:**
  - przypięty `x500_nadir2_flow/model.sdf` (sha 1fa0c57d…) i jego kopia w `results/NADIR/s1/zrodla/`;
  - nowy plik świata;
  - nowy katalog modelu warstwy (SDF i tekstura);
  - zapisy pinów sha tam, gdzie są sprawdzane.
- **Booty statyczne: 2.**
  1. Stary model i stary świat (odniesienie).
  2. Nowy model i nowy świat.

  W tej samej pozie zawisu porównanie pikselowe klatek kamery przepływu i kamery misji (oczekiwana różnica 0) oraz odległości lidaru. Kamera w dół: brak detekcji znaczników w `nadir_obs` i teren w kadrze.

  Trzeci boot (nowy model, stary świat) tylko wtedy, gdy porównanie 1–2 nie wyjdzie zerowe, do rozdzielenia wpływu masek i warstwy.

**Kandydat planu lotów:**
- łata S, mapa M4, SIFT, reguła `a12_geo0_g1.5`, świat V1;
- 12 cięć jak S3 NAD3 (6 komórek × 2 kierunki) i lot długi;
- mapa liczona w chwili cięcia z wiązań sprzed cięcia;
- wycena: 2 booty statyczne + 12 + 1 + 1 rezerwa = **16 bootów**.

Przed lotami potrzebny jest port toru (render → kamera z gz, wiązania online, rozwiązanie w chwili cięcia) do kodu lotu. To praca bez bootów, ale poza tym reconem.

**Pytania do PRE (po dwie nazwane odpowiedzi):**
1. Świat:
   - **„PRZEPŁYW-JAK-NAD3”**: kamera przepływu nadal nad szachownicą, tabela G z NAD3 obowiązuje, teza węższa;
   - **„TEREN-DLA-WSZYSTKICH”**: wszystkie kamery widzą teren, G do ponownego pomiaru.
2. Lot długi:
   - **„TRASA-UCZĄCA”**: faza przed cięciem obejmuje obszar misji (przerwy poza mapą znikają z konstrukcji);
   - **„ODMOWA-POZA-MAPĄ”**: przerwa poza mapą to odmowa barierą. Zmierzone przerwy poza mapą M4 / SIFT do 2.4 s, dostępność do 2.4–3.6 s.
3. Rodzaj cech:
   - **„SIFT”**: przerwy na 12 cięciach ≤ 1.4 s, p95 24 ms;
   - **„AKAZE”**: p95 14 ms, ale przerwy do 4.0 s na 12 cięciach i 5.8 s w locie długim.
4. Sito wiązań sprzed cięcia:
   - **„SITO-ODLEGŁOŚCI”**: test | |r| − d_EKF | ≤ 1.5 m jak tu; w tym biegu nic nie odrzucił, a grube pomyłki z ANEKS_TEACH-1 §4 dotyczyły kadrów po cięciu;
   - **„SITO-RESZT”**: dodatkowo odrzucanie wiązań z resztą po rozwiązaniu ponad próg i drugie rozwiązanie.
5. Kadr kamery w dół:
   - **„TYLKO-TEREN”**: flagi bez bitu 3 także dla modeli dronów;
   - **„TEREN-I-OBIEKTY”**: modele z flagami domyślnymi pozostają widoczne.

## Liczby do rozliczenia predykcji (bez rozliczenia)

- **P-TEACH-R8** (M4, S, SIFT, 12 cięć: ≤ 1.37 m i przerwy ≤ 2.15 s): max 0.732 m, max przerwa 1.4 s.
- **P-TEACH-R9** (tamże ≤ 1.0 m): 0.732 m.
- **P-TEACH-R10** (M4, S, SIFT, lot długi ≤ 1.37 m): 0.846 m.
- **P-TEACH-R11** (M4, J, SIFT, 12 cięć ≤ 1.37 m): 0.708 m.
- **P-TEACH-R12** (M3, S, SIFT, 12 cięć ≤ 1.37 m): 1.054 m.
- **P-TEACH-R13** (M4, S, SIFT, 12 cięć, p95 ≤ 0.70 m): p95 0.530 m.
- **P-TEACH-R14** (M4, S, SIFT, lot długi, żadnej przerwy > 2.15 s w mapie): w mapie 0. Poza mapą 2 przerwy > 2.15 s (max 2.4 s).

## Odchylenia od promptu

1. **Kopia kodu S0** przeniesiona z ciała `teach_r34.zadanie` do funkcji: `Lot.przygotuj`, `Lot.klatki_kluczowe`, `lancuch`. Treść bez zmian, z trzema wyjątkami:
   - `przygotuj` nie zwraca pól M0 (`fr`, `Rg`, `z_gt`);
   - w łańcuchu klucz bufora to (kadr, klatka, rodzaj) bez wariantu M0;
   - georeferencja klatki to macierz (θ, t) zamiast funkcji `geo`.

   Zgodność R1 6/6 to potwierdza.
2. **Kadr będący klatką kluczową** wiąże się z sobą samym. Gdy w pierwszej trójce byłby inny zestaw, wstawiam siebie na pierwsze miejsce. W praktyce pokrycie z sobą wynosi 1, więc zawsze jest w trójce.
3. **Spójność (B)** dla każdej pary przyjętych wiązań tego samego kadru, łącznie z wiązaniem kadru kluczowego z samym sobą.
4. **Prior** nałożony na wszystkie trzy niewiadome klatki z wagą 0.05 (θ w radianach, t w metrach). Gauss–Newton przez `np.linalg.lstsq` na pełnej macierzy.
5. **Przerwy w mapie / poza mapą:** do przerwy należą kadry nieprzyjęte leżące ściśle wewnątrz przedziału. Dla przerwy końcowej także kadr końca misji.
6. **R6** liczony osobno dla 12 cięć, lotu długiego i razem. Klasyfikacja zdania jak w S0 (moja). τ_dost z krawędzi siatki G.
7. **R7:** wiązanie mierzone łącznie dla obu rodzajów cech i z renderem pomocniczym; render zmierzony osobno.
8. **Próba na sucho** jednego zadania (p07, łata S) przed pełnym biegiem. Po niej projektu nie zmieniałem.
9. **Commity bramki:** `eb187c68` [CO-TEACH-1] i `6bfd3892` [S0B-KSIEGA] przed tym [STOP-TEACHR2].

0 bootów. Sieć: żadna. `worlds/` bez zmian. Bez pushu.
