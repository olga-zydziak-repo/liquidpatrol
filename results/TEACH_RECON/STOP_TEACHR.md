# STOP-TEACHR — recon TEACH: Ś1 i Ś2 zachodzą literą

Wynik: **Ś1 i Ś2 zachodzą literą** (PROMPT_TEACH_S0, sha256 e64e298b…, 0 bootów).

**Ś1 — przyrząd.** Mapa M0 na łacie S daje największy błąd przyjętej poprawki 0.24 m (SIFT) i 0.28 m (AKAZE) na 13 lotach, ale w locie długim przerwy sięgają 3.6 s (SIFT) i 5.8 s (AKAZE), czyli ponad 1.15 s. Na 12 cięciach NAD3 przerwy wynoszą ≤ 0.4 s dla SIFT; AKAZE ma do 1.4 s, tylko na p04.
- Jedyna naprawa przyrządu usunęła część błędową: przed naprawą max błąd M0 był 0.76 m. Przerw naprawa nie usunęła.
- Przerwy nie pochodzą z przyrządu. Lot długi wylatuje nad teren, którego dron nie widział przed cięciem: pokrycie prawdziwe spada do 1–10 %, a przez ok. 1.4 s nie ma żadnej klatki kluczowej z dodatnim pokryciem przewidywanym.

**Ś2 — kierunek.** Na żadnej łacie żaden rodzaj cech z mapą M1 ani M2 nie mieści się na wszystkich 13 lotach w 1.37 m. Największe błędy przyjętych poprawek: M1 1.81–1.86 m, M2 1.91–1.97 m.
- Błąd ten sam na trzech łatach, więc decyduje georeferencja z EKF, nie teren.
- Błąd rośnie z odległością od środka klatki kluczowej (M1, łata S, max): 0.65 m przy 0–3 m, 0.92 m przy 3–6 m, 1.56 m przy 6–10 m, 1.81 m ponad 10 m.
- Jedna poprawka kursu na lot (M2) nie pomaga, bo błąd kursu klatek kluczowych zmienia się w obrębie lotu.

**Ś3 nie zachodzi:** wariant V1 z R7 zostawia kamerze przepływu i kamerze misji obraz jak w NAD3. Lotem tego nie sprawdzano.

Czas zegara całego dopasowania: 314 s (bieg przed naprawą) + 447 s (bieg po naprawie) = 12.7 min, w budżecie 60 min. Wszystkie biegi: 8 procesów × 1 wątek cv2.

## R1 — łaty i teren

Narzędzia `tools/teach_r1_podglad.py` i `tools/teach_r1.py` (czytnik i przeliczenie z `results/ORTO_RECON/tools/orto_r1.py` przez import).

Łaty wybrałem po obejrzeniu edycji 2024, czyli WMS HighResolution: 9 kandydatów, okna 400 m, w `r1_podglad_kandydatow.jpg`. Wybór zapisałem w commicie `cf7a0fc1` [R1-LATY], przed dopasowaniem (`laty.json`, odrzucone kandydatki z powodem):

| Łata | Klasa | Środek | Arkusz 2024-04-27 | Energia gradientu po rozmyciu do 0.8 m | Piksel efektywny |
|---|---|---|---|---|---|
| S | parking z liniami i rzędami aut, jezdnie, mało koron (Magnolia Park) | 51.1185 N 16.9905 E | M-33-34-D-b-4-2, PL-1992 | 4.6 % | 0.2 m |
| M | łata A reconu ORTO (Sępolno), środek bez zmian | 51.1015 N 17.0870 E | M-33-35-C-a-4-3, PL-1992 | 3.9 % | 0.2 m |
| J | łąka / nieużytek ze ścieżkami (Ołtaszyn) | 51.0570 N 17.0400 E | M-33-35-C-c-1-4, PL-1992 | 1.8 % | 0.1 m |

Sprawdzian J (`orto_r1_spr.ostrosc`): źródło nie jest zgrubione. Dla porównania lotnisko w ORTO zachowywało 64 % energii przy 0.8 m.

Okna mają 100 × 100 m przy pikselu 0.05 m (2000 × 2000 px). Pochodzenie z sha256 jest w `dane/pochodzenie.json`, opis w `r1_dane.json`.

## R2 — klatki

Narzędzie `tools/teach_r2.py`, plik wynikowy `r2_klatki.json.gz`, liczności w `r2_loty.json`.

Loty i seria „po” są identyczne z reconem ORTO R2: 12 cięć S3 NAD3 i lot długi, razem 8609 klatek.

Seria „przed” obejmuje klatki z wysokością EKF ≥ 6 m: 173–193 na lot, razem 2365. Render z terenu 2024 przy pozie GT (`orto_r2.Kam`).

## R3 — mapa

Narzędzie `tools/teach_r34.py`.
- **Klatki kluczowe** (decyzja drona z pozy EKF): nowa klatka kluczowa, gdy pokrycie śladu przez dotychczasowe spada poniżej 70 %. Daje to 8–11 klatek kluczowych na lot.
- **M0:** klatka kluczowa wyprostowana przy pozie GT, środek z kamery GT.
- **M1:** prostowanie i środek z EKF.
- **M2:** jak M1 plus jedna poprawka kursu na lot. Liczona z par klatek kluczowych sprzed cięcia jako kąt(przesunięcie EKF) − kąt(przesunięcie obrazu): pary o odległości ≥ 3 m, pokryciu ≥ 30 % i ≥ 12 inlierach, średnia kołowa ważona |d|.

Błąd kursu klatek kluczowych przed kalibracją i po niej (łata S, SIFT; pełne dane per łata i rodzaj w `r5_wyniki.json` → `kalibracja`):

| Lot | ψ_kal [°] | Pary | Błąd kursu przed: p50 / max [°] | Po kalibracji: p50 / max [°] |
|---|---|---|---|---|
| L_c10_s01 | 1.46 | 54 | 3.24 / 6.09 | 2.82 / 4.63 |
| p01 | 1.77 | 46 | 1.61 / 8.06 | 2.24 / 6.29 |
| p02 | −0.48 | 46 | 4.11 / 6.57 | 3.63 / 7.06 |
| p03_r2 | 1.65 | 45 | 1.78 / 8.65 | 2.05 / 7.00 |
| p04 | −1.20 | 44 | 2.93 / 4.06 | 2.12 / 4.51 |
| p06 | 1.41 | 47 | 2.25 / 8.27 | 2.24 / 6.86 |
| p07 | −0.76 | 35 | 2.30 / 5.04 | 3.05 / 5.80 |
| p08 | 2.67 | 45 | 3.02 / 11.21 | 0.86 / 8.55 |
| p09 | −0.43 | 65 | 3.04 / 3.91 | 2.78 / 4.35 |
| p11 | 1.17 | 33 | 1.43 / 6.37 | 1.00 / 5.20 |
| p12 | 0.27 | 42 | 1.92 / 5.10 | 1.92 / 5.37 |
| p13 | 3.04 | 45 | 4.12 / 13.98 | 1.61 / 10.93 |
| p14 | −1.07 | 52 | 3.16 / 5.20 | 2.80 / 6.25 |

Rozrzut kąta między parami wynosi 2.4–4.3°, czyli tyle, ile sam błąd kursu. Jedna stała na lot nie zdejmuje błędu, który zmienia się między klatkami kluczowymi.

## R4/R5 — lokalizacja po cięciu i wyniki

Łańcuch jak w ORTO R3 (Δ = 0 przy cięciu). Kandydatami są do 3 klatek kluczowych o największym przewidywanym pokryciu. Dopasowanie: SIFT / AKAZE, knn 2 z ilorazem 0.8, RANSAC podobieństwa. Reguła zamrożona `a12_geo0_g1.5`, bez strojenia.

Wyniki (`tools/teach_r5.py` → `r5_wyniki.json`), razem 13 lotów, 8609 klatek na łatę:

| Łata | Mapa / cechy | Udział przyjętych | Błąd p50 [m] | p95 [m] | max [m] | Przyjęte > 1.0 / > 1.37 / > 2.28 m | Max przerwa [s] | Przerwy > 1.15 / > 2.15 s |
|---|---|---|---|---|---|---|---|---|
| S | M0 / SIFT | 0.994 | 0.075 | 0.150 | 0.236 | 0 / 0 / 0 | 3.6 | 4 / 2 |
| S | M0 / AKAZE | 0.981 | 0.071 | 0.142 | 0.282 | 0 / 0 / 0 | 5.8 | 12 / 5 |
| S | M1 / SIFT | 0.993 | 0.381 | 0.833 | 1.814 | 185 / 29 / 0 | 2.6 | 6 / 1 |
| S | M1 / AKAZE | 0.981 | 0.367 | 0.812 | 1.819 | 176 / 26 / 0 | 5.8 | 12 / 7 |
| S | M2 / SIFT | 0.993 | 0.418 | 1.035 | 1.930 | 486 / 67 / 0 | 2.8 | 6 / 2 |
| S | M2 / AKAZE | 0.982 | 0.415 | 1.040 | 1.926 | 522 / 66 / 0 | 5.8 | 11 / 7 |
| M | M0 / SIFT | 0.996 | 0.074 | 0.149 | 0.236 | 0 / 0 / 0 | 3.0 | 2 / 2 |
| M | M0 / AKAZE | 0.985 | 0.071 | 0.140 | 0.253 | 0 / 0 / 0 | 5.2 | 9 / 4 |
| M | M1 / SIFT | 0.996 | 0.385 | 0.884 | 1.826 | 280 / 39 / 0 | 2.4 | 3 / 1 |
| M | M1 / AKAZE | 0.985 | 0.374 | 0.865 | 1.851 | 254 / 37 / 0 | 5.4 | 9 / 4 |
| M | M2 / SIFT | 0.996 | 0.421 | 1.073 | 1.942 | 584 / 81 / 0 | 2.6 | 3 / 1 |
| M | M2 / AKAZE | 0.984 | 0.418 | 1.058 | 1.915 | 548 / 56 / 0 | 5.4 | 8 / 5 |
| J | M0 / SIFT | 0.997 | 0.075 | 0.149 | 0.251 | 0 / 0 / 0 | 3.0 | 2 / 2 |
| J | M0 / AKAZE | 0.978 | 0.071 | 0.141 | 0.233 | 0 / 0 / 0 | 5.8 | 12 / 8 |
| J | M1 / SIFT | 0.998 | 0.385 | 0.841 | 1.828 | 204 / 28 / 0 | 2.4 | 1 / 1 |
| J | M1 / AKAZE | 0.980 | 0.378 | 0.810 | 1.859 | 180 / 29 / 0 | 5.6 | 14 / 6 |
| J | M2 / SIFT | 0.998 | 0.417 | 1.030 | 1.941 | 500 / 65 / 0 | 2.6 | 1 / 1 |
| J | M2 / AKAZE | 0.980 | 0.414 | 1.004 | 1.970 | 432 / 60 / 0 | 5.6 | 13 / 6 |

Gdzie leżą przerwy i błędy:
- Wszystkie przerwy > 1.15 s są w locie długim albo, dla AKAZE, na p04 (na łacie J do 4.2 s). Na 12 cięciach NAD3 SIFT ma przerwę max 0.4 s na każdej łacie i każdej mapie.
- **Najgorsze loty M1, łata S, SIFT:** p02 1.81 m (26 przyjętych > 1.37 m), p13 1.56 m, L 1.42 m, p14 1.35 m. Pozostałe 9 lotów ≤ 1.25 m.
- **M2, łata S, SIFT, lot długi:** max 1.46 m, przerwa 2.8 s (6 przerw > 1.15 s, 2 > 2.15 s).

Błąd przyjętych w funkcji odległości od środka klatki kluczowej (łata S, SIFT, max [m]; pełne dane per łata, mapa i rodzaj w `r5_wyniki.json`):

| Mapa | 0–3 m | 3–6 m | 6–10 m | > 10 m |
|---|---|---|---|---|
| M0 | 0.21 | 0.21 | 0.21 | 0.24 |
| M1 | 0.65 | 0.92 | 1.56 | 1.81 |

Błąd w funkcji pokrycia prawdziwego (M1, łata S, SIFT), p50 / max [m]:

| Pokrycie | p50 | max |
|---|---|---|
| ≥ 50 % | 0.34 | 1.56 |
| 30–50 % | 0.60 | 1.75 |
| < 30 % | 0.61 | 1.81 |

Wyniki przed naprawą przyrządu (M0 prostowane przy postawie EKF z poprawką kursu i skali; M0 S max 0.76 m na p02) są w `r4_przed_naprawa/`. M1 i M2 są w obu biegach identyczne.

## R6 — kontrakt

Narzędzie `tools/teach_r5.py` → `r6_kontrakt.json`. G z `results/NAD3/tools/nad3_freeze.py` (przez `orto_r5.g_siatka`), krawędzie na siatce klatki 0.2 s. Wzór: U′ = 1.5·(E + G(τ)), R = 32 − 2.85 − (U′ + 1.524).

Klasyfikacja zdania jest moja:
- „mieści się”: R(τ*) ≥ 20;
- „mieści się z odmowami”: R ≥ 20 do krawędzi τ_ok < τ*, a odmowa przy przerwie > τ_ok;
- „nie mieści się”: R < 20 już na pierwszej krawędzi.

- Łata S, mapa M0: SIFT, E = 0.24 m, τ* = 3.6 s, R(τ*) = 21.98 m — mieści się.
- Łata S, mapa M1: SIFT, E = 1.81 m, τ* = 2.6 s, R(τ*) = 19.62 m — mieści się z odmowami (odmowa przy przerwie > 2.0 s: 1 przerwa).
- Łata S, mapa M2: AKAZE, E = 1.93 m, τ* = 5.8 s, R(τ*) = 17.47 m — mieści się z odmowami (odmowa przy przerwie > 1.8 s: 7 przerw).
- Łata M, mapa M0: SIFT, E = 0.24 m, τ* = 3.0 s, R(τ*) = 21.98 m — mieści się.
- Łata M, mapa M1: SIFT, E = 1.83 m, τ* = 2.4 s, R(τ*) = 19.69 m — mieści się z odmowami (odmowa przy przerwie > 2.0 s: 1 przerwa).
- Łata M, mapa M2: AKAZE, E = 1.91 m, τ* = 5.4 s, R(τ*) = 17.63 m — mieści się z odmowami (odmowa przy przerwie > 1.8 s: 6 przerw).
- Łata J, mapa M0: AKAZE, E = 0.23 m, τ* = 5.8 s, R(τ*) = 20.01 m — mieści się.
- Łata J, mapa M1: SIFT, E = 1.83 m, τ* = 2.4 s, R(τ*) = 19.68 m — mieści się z odmowami (odmowa przy przerwie > 2.0 s: 1 przerwa).
- Łata J, mapa M2: SIFT, E = 1.94 m, τ* = 2.6 s, R(τ*) = 19.43 m — mieści się z odmowami (odmowa przy przerwie > 1.8 s: 1 przerwa).

Rachunek R6 nie zdejmuje Ś2. Ś2 jest progiem błędu 1.37 m, a E na M1 i M2 go przekracza.

## R7 — czas i świat

**Czas** (`tools/teach_r7_czas.py` → `r7_czas.json`): jeden proces, cv2 1 wątek, obciążenie maszyny ~1.7, lot p02, łata S, 200 klatek, dopasowanie do 3 klatek kluczowych.

| Etap | p50 [ms] | p95 [ms] |
|---|---|---|
| Render pomocniczy (tylko przyrząd) | 3.9 | 4.9 |
| Prostowanie | 1.7 | 1.9 |
| SIFT: cechy | 12.2 | 14.4 |
| SIFT: dopasowanie do 3 klatek kluczowych | 5.9 | 8.0 |
| **SIFT łącznie bez renderu** | **19.8** | **23.8** (≈ 42 Hz) |
| AKAZE: cechy | 7.1 | 8.7 |
| AKAZE: dopasowanie do 3 klatek kluczowych | 3.2 | 4.5 |
| **AKAZE łącznie bez renderu** | **12.1** | **14.3** (≈ 70 Hz) |

**Widoczność dziś** (z przypiętych plików):
- `x500_nadir2_flow/model.sdf` (sha 1fa0c57d…):
  - kamera misji „imager” ma maskę 4294967293 = ~bit 1 (l.21);
  - kamera przepływu „flow_camera” ma maskę 4294967291 = ~bit 2 (l.46);
  - lidar (`gpu_lidar`, l.85) i kamera w dół „nadir” (l.127) nie mają masek.
- `worlds/world_nadir2_A3.sdf` (sha 7f2bbe13…):
  - ground_plane ma flagi domyślne (l.21–29), więc widzą go wszyscy;
  - kont_decal ma flagi 2 (l.1302): widzi go kamera przepływu i kamera w dół, nie widzi kamera misji;
  - 37 znaczników ma flagi 4 (od l.1315): widzi je kamera misji i kamera w dół, nie widzi kamera przepływu.

Żaden bit nie jest wyłączony jednocześnie przez maskę misji i maskę przepływu.

**Warianty:**

- **V1 (zostawia obraz jak w NAD3).** Teren jako płaszczyzna z teksturą i `visibility_flags` 8 (bit 3) w nowym świecie. Maska kamery misji ~(bit 1 | bit 3) = 4294967285, maska kamery przepływu ~(bit 2 | bit 3) = 4294967283, opcjonalnie maska lidaru ~bit 3.
  - Zmieniają się przypięty `model.sdf` (nowy sha) i świat (nowy plik, `worlds/` w tym etapie bez zmian).
  - Kamera przepływu i kamera misji nie widzą warstwy, więc obraz zostaje jak w NAD3, a tabela G i detektor obowiązują. Warunek do sprawdzenia: sama zmiana maski nie zmienia obrazu.
- **V2.** Tekstura na ground_plane, flagi domyślne. Zmienia się tylko świat, ale obraz kamery przepływu i kamery misji się zmienia, więc G i detektor do ponownego pomiaru. Nie jest jak w NAD3.
- **V3.** Sama flaga warstwy bez zmiany masek. Niemożliwe: żaden bit nie jest wyłączony u obu kamer naraz.

**Sprawdzenie V1 lotem:**
1. Dwa booty statyczne, w świecie NAD3 i w świecie z warstwą, przy tym samym modelu z nowymi maskami. Porównanie pikselowe klatek kamery przepływu i kamery misji w tej samej pozie: oczekiwana różnica 0.
2. Trzeci boot ze starym modelem jako odniesienie maski.

Razem 3 booty przed jakimkolwiek lotem nogi.

## R8 — plan i pytania do PRE

Przy Ś1 i Ś2 literą plan lotów nie ma podstawy.

Kandydat warunkowy (tylko jeśli PRE zmieni literę Ś1 albo źródło kursu):
- łata S, mapa M1, SIFT, reguła `a12_geo0_g1.5`, V1;
- 3 booty statyczne R7 plus 12 cięć jak S3 NAD3 (6 komórek × 2) plus lot długi;
- razem ≈ 16 bootów.

Pytania (dwie nazwane odpowiedzi):
1. Przerwy z pokrycia w Ś1:
   - **„LITERA”**: przerwa M0 to Ś1 bez względu na przyczynę;
   - **„POKRYCIE-OSOBNO”**: Ś1 sprawdza przyrząd (błąd M0), a przerwy z braku mapy idą do Ś2 i do kontraktu z odmowami.
2. Źródło kursu dla mapy:
   - **„KURS-NA-KLATKĘ”**: kurs każdej klatki kluczowej z łańcucha dopasowań sprzed cięcia (więcej niż jedna poprawka na lot, wbrew literze M2);
   - **„KURS-Z-EKF”**: zostaje kurs EKF, a dźwignią jest zmniejszenie odległości od środka klatki kluczowej (gęstsze klatki kluczowe, kandydaci po odległości).
3. Pokrycie po cięciu:
   - **„TRASA-UCZĄCA”**: faza przed cięciem obejmuje obszar misji;
   - **„MAPA-ROSNĄCA”**: przyjęte poprawki po cięciu dopisują klatki do mapy (ryzyko kumulacji błędu).
4. Rodzaj cech:
   - **„SIFT”**: mniej przerw (max 2.4–2.8 s M1/M2 wobec 5.4–5.8 s AKAZE);
   - **„AKAZE”**: szybszy (p95 14 ms wobec 24 ms).

## Liczby do rozliczenia predykcji (bez rozliczenia)

- **P-TEACH-R1** (M0, S, ≤ 0.5 m i żadnej przerwy > 1.15 s na 13 lotach): max 0.24 m (SIFT) / 0.28 m (AKAZE). Przerwy > 1.15 s: 4 (SIFT, max 3.6 s) / 12 (AKAZE, max 5.8 s), w locie długim, a dla AKAZE także na p04.
- **P-TEACH-R2** (M1, S, max ≤ 1.0 m): 1.81 m (SIFT) / 1.82 m (AKAZE).
- **P-TEACH-R3** (M2, S, max ≤ 1.0 m): 1.93 m (SIFT) / 1.93 m (AKAZE).
- **P-TEACH-R4** (M2, M, max ≤ 1.0 m): 1.94 m (SIFT) / 1.91 m (AKAZE).
- **P-TEACH-R5** (M2, J, ≤ 1.37 m i przerwy ≤ 2.15 s): SIFT max 1.94 m, przerwa max 2.6 s (1 > 2.15 s); AKAZE 1.97 m, 5.6 s (6 > 2.15 s).
- **P-TEACH-R6** (M2, S, lot długi, żadnej przerwy > 2.15 s): SIFT max przerwa 2.8 s (2 przerwy > 2.15 s); AKAZE 5.8 s (7).
- **P-TEACH-R7** (czas lepszego rodzaju ≤ 200 ms): SIFT p50 19.8 / p95 23.8 ms; AKAZE p50 12.1 / p95 14.3 ms.

## Odchylenia od promptu

1. **Naprawa przyrządu (jedna).** Pierwsza wersja M0 prostowała klatki kluczowe przy postawie EKF i poprawiała tylko kurs (GT − EKF) i skalę wysokości. Wbrew literze R3 („poza GT”) dała max 0.76 m (p02). Naprawa: prostowanie klatek kluczowych M0 przy pozie GT. Wyniki sprzed naprawy w `r4_przed_naprawa/`.
2. **Próby na sucho przed biegami.** Przed pełnym biegiem uruchomiłem jedno zadanie (p07, łata S) i po nim projektu nie zmieniałem. Po naprawie uruchomiłem jedno zadanie (p02, S), wyłącznie dla sprawdzenia naprawy.
3. **Prostowanie** na siatce 0.1 m/px (`orto_r3.Prost`), mimo terenu 0.05 m. Ta sama siatka co w ORTO.
4. **Pokrycie przy wyborze klatek kluczowych:** ślad z 16 × 12 promieni przy pozie EKF, siatka 0.5 m. Pokrycie przewidywane kandydatów i pokrycie prawdziwe w R5: dwa kwadraty o pół-boku h·(H/2)/F, bez obrotu.
5. **Kalibracja M2:** pary, progi (≥ 3 m, ≥ 30 %, ≥ 12 inlierów), wagi |d| i osobna kalibracja dla każdego rodzaju cech to moje wybory, ustalone przed biegiem.
6. **Seria „przed”:** wszystkie klatki od początku zapisu do cięcia z wysokością EKF ≥ 6 m (selekcja po wysokości EKF, nie GT).
7. **Reguła `a12_geo0_g1.5`** bez progu geometrii; okno szukania zastąpione wyborem 3 klatek kluczowych. Bramka innowacji 1.5 + 3τ.
8. **Klasyfikacja zdań R6** jest moja (opis w R6).
9. **R7 czas:** klatki kluczowe do dopasowania wybierane po odległości od pozycji EKF kamery, nie z łańcucha. Pomiar dotyczy samego kosztu.
10. **`orto_r3.Cechy`** tworzona z atrapą mapy 64 × 64. Używane są tylko detektor i norma.
11. **Commity:** oprócz [STOP-TEACHR] jest wcześniejszy `cf7a0fc1` [R1-LATY] (wymóg R1: środki przed dopasowaniem) oraz bramka `d3e6df8b` [CO-ORTO-1] i `8fe0b9a2` [S0-KSIEGA].
12. **Waiter procesu:** moje oczekiwanie na pierwszy bieg zapętliło się na własnej linii poleceń (wzorzec `pgrep` pasował do samego siebie). Zatrzymałem je ręcznie. Czas zegara pierwszego biegu wziąłem z dziennika (314 s), nie z pliku znacznika.

0 bootów. Sieć: wyłącznie usługi GUGiK (podgląd WMS i arkusze 2024). `worlds/` bez zmian. Bez pushu.
