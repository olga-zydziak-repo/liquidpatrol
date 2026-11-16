# STOP-ORTOR-DECYZJA — recon ORTO-S0 zamknięty decyzją Olgi

Recon ORTO-S0 (PROMPT_ORTO_S0, sha256 f1d514ab…, 0 bootów) zamknięty sygnałem Olgi 16.11 „zamykam ORTO-S0 decyzją”, w trakcie
biegu oceny R5. Wykonano R1–R4 oraz R5 do etapu strojenia na sześciu cięciach c05. Nie wykonano: oceny na sześciu cięciach c10
i locie długim (bieg przerwany przy 42/78 zadaniach), R6, R7, R8. Raport nie zawiera werdyktu Ś1–Ś4 ani rozliczenia predykcji
P-ORTO-R1…R7 — to robi CC w aneksie.

## Wykonane

**R1 — dane** (commit `664d8459` łaty, `70de170d` dane). Narzędzia `tools/orto_uklad.py`, `tools/orto_r1.py`, `tools/orto_r1_spr.py`.

- Para na wszystkich łatach: „świat” 2012-04-28 (PL-1992), „mapa” 2025-08-12 (PL-2000:S6 przeliczona do PL-1992).
- Okna mają 100 × 100 m przy pikselu 0.10 m.
- Pochodzenie danych: `dane/pochodzenie.json`.
- Sprawdzian przeliczenia układów: 0.04–0.05 px (A, B).
- TrueOrtho jest puste we wszystkich łatach, więc użyto zwykłej ortofotomapy.
- Źródło łaty C (lotnisko) jest zgrubione do metrów we wszystkich 10 edycjach.
- Pliki wyników: `r1_dane.json`, `r1_sprawdziany.json`, `r1_opis.json`.

**R2 — kadry i sprawdzian** (commit `1b5971f4`). Narzędzie `tools/orto_r2.py`.

- Kamera z przypiętego `x500_nadir2_flow/model.sdf` (l.115, 128, 130, 132–133, 141) z pozą `x500_base` 0.24 m.
- Reprojekcja znaczników NAD2 (62 656 detekcji): p50 0.28 px, p95 0.57 px, max 2.98 px.
- Klatki: 8609 (12 cięć S3 NAD3 oraz lot długi `L_c10_s01`).
- Pliki wyników: `r2_kamera.json`, `r2_sprawdzian.json`, `r2_klatki.json.gz`.

**R3 — kandydaci** (`tools/orto_r3.py`, ten commit):

- K1 SIFT i K2 AKAZE (po CLAHE): knn k = 8 do całej mapy łaty, filtr okna szukania, test ilorazu 0.8, `estimateAffinePartial2D` RANSAC 3 px.
- K3 NCC: gradient, szablon ±6.5 m, `TM_CCOEFF_NORMED`, szczyt i iloraz do drugiego szczytu.
- Wejście kandydata to kadr, q oraz pozycja i wysokość z EKF, plus pozycja przewidywana. Łańcuch jak rama B+ NAD3: Δ = 0 przy cięciu, promień szukania min(4 + 3τ, 20) m.

**R4/R5 — strojenie na c05** (`tools/orto_r4.py strojenie`, `tools/orto_r5.py wybor`, ten commit).

- 6 cięć c05: p01, p03_r2, p06, p08, p11, p13.
- Siatka reguł: 72 na kandydata cechowego, 72 dla NCC.
- Wybór leksykograficzny: (1) max błąd przyjętej ≤ 1.0 m; (2) najmniejsza max przerwa, potem najwięcej przyjętych; (3) gdy nic nie spełnia (1), najmniejszy max błąd.
- Pliki wyników: `r4_strojenie.json.gz`, `r5_reguly.json`.

## Wyniki strojenia (6 cięć c05, 3313 klatek na łatę)

Kolumny „wszystko” to R4 przed odrzucaniem: p50 jest medianą p50 po lotach, max jest maksimum łącznym. Pozostałe kolumny to reguła
wybrana na tych samych lotach, czyli wynik w próbie, nie ocena.

| Łata | Wariant | Kandydat | Wszystko: wyników / klatek | Wszystko: p50 / max błędu [m] | Wybór | Reguła | Przyjęte | Max błąd przyjętej [m] | Max przerwa [s] | Przerwy > 1.15 / > 2.15 s | Przyjęte > 1.37 m |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A | para | K1_SIFT | 192 / 3313 | 39.53 / 217.21 | najmniejszy błąd | a4_geo0_g1.5 | 34 | 37.69 | 52.6 | 38 / 36 | 34 |
| A | para | K2_AKAZE | 194 / 3313 | 41.99 / 263.52 | najmniejszy błąd | a4_geo0_gNone | 1 | 20.07 | 110.4 | 7 / 6 | 1 |
| A | para | K3_NCC | 3138 / 3313 | 25.43 / 60.62 | najmniejszy błąd | c0.4_q1.2_g1.5 | 10 | 2.09 | 106.2 | 12 / 12 | 4 |
| A | kontrola | K1_SIFT | 3313 / 3313 | 0.10 / 0.22 | dopuszczalny | a12_geo0_g1.5 | 3313 | 0.22 | 0.2 | 0 / 0 | 0 |
| A | kontrola | K2_AKAZE | 3313 / 3313 | 0.10 / 0.21 | dopuszczalny | a12_geo0_g1.5 | 3313 | 0.21 | 0.2 | 0 / 0 | 0 |
| A | kontrola | K3_NCC | 3138 / 3313 | 0.12 / 0.85 | dopuszczalny | c0.3_q1.0_g1.5 | 2918 | 0.85 | 10.0 | 20 / 9 | 0 |
| B | para | K1_SIFT | 129 / 3313 | 34.48 / 370.55 | najmniejszy błąd | a4_geo0_g1.5 | 4 | 54.28 | 110.4 | 10 / 10 | 4 |
| B | para | K2_AKAZE | 210 / 3313 | 38.89 / 342.81 | nic nie przyjmuje | — | — | — | — | — | — |
| B | para | K3_NCC | 3138 / 3313 | 36.39 / 63.41 | nic nie przyjmuje | — | — | — | — | — | — |
| B | kontrola | K1_SIFT | 3313 / 3313 | 0.10 / 0.22 | dopuszczalny | a12_geo0_g1.5 | 3313 | 0.22 | 0.2 | 0 / 0 | 0 |
| B | kontrola | K2_AKAZE | 3313 / 3313 | 0.10 / 0.20 | dopuszczalny | a12_geo0_g1.5 | 3313 | 0.20 | 0.2 | 0 / 0 | 0 |
| B | kontrola | K3_NCC | 3138 / 3313 | 0.12 / 0.65 | dopuszczalny | c0.3_q1.0_g1.5 | 2913 | 0.62 | 9.4 | 19 / 9 | 0 |
| C | para | K1_SIFT | 0 / 3313 | — | nic nie przyjmuje | — | — | — | — | — | — |
| C | para | K2_AKAZE | 0 / 3313 | — | nic nie przyjmuje | — | — | — | — | — | — |
| C | para | K3_NCC | 3138 / 3313 | 11.83 / 31.33 | najmniejszy błąd | c0.3_q1.1_gNone | 6 | 18.23 | 107.0 | 12 / 12 | 6 |
| C | kontrola | K1_SIFT | 0 / 3313 | — | nic nie przyjmuje | — | — | — | — | — | — |
| C | kontrola | K2_AKAZE | 0 / 3313 | — | nic nie przyjmuje | — | — | — | — | — | — |
| C | kontrola | K3_NCC | 3138 / 3313 | 0.12 / 0.76 | dopuszczalny | c0.3_q1.0_g1.5 | 3133 | 0.74 | 3.0 | 13 / 3 | 0 |

Opisowo, bez werdyktu:

- Na parze 2012 → 2025 żadna reguła na żadnej łacie nie mieści się w 1.0 m na c05. Najmniejszy max błąd przyjętej to 2.09 m (A, NCC, 10 przyjętych).
- Na kontroli A i B cechy dają max 0.20–0.22 m bez przerw ponad 0.2 s.
- Na łacie C cechy nie dają wyniku nawet na kontroli (źródło zgrubione).

## Czasy na klatkę (ms)

Wszystkie pomiary pod obciążeniem: 22 procesy równolegle na 24 rdzeniach, cv2 jednowątkowo w procesie. Pomiaru jednego procesu bez
obciążenia nie wykonano.

| Etap | p50 zadań strojenia: min / mediana / max | `r7_czas.json`: próba 3 klatek, łata A, para, wątki domyślne, łącznie z prostowaniem |
|---|---|---|
| prostowanie | mediana 15.0 | — |
| K1 SIFT (cechy + knn + dopasowanie) | 18 / 9574 / 12008 | p50 164, p95 182 (~5.5 Hz) |
| K2 AKAZE | 12 / 131 / 251 | p50 44, p95 48 (~21 Hz) |
| K3 NCC | 1.4 / 4.9 / 5.5 | p50 11, p95 21 (~47 Hz) |

Uwagi do czasów:

- Najmniejsze wartości dla cech (18 ms i 12 ms) pochodzą z łaty C, gdzie mapa ma 28 punktów kluczowych.
- Wartości SIFT rzędu 10 s to knn do 30 000 punktów mapy przy rywalizacji 22 procesów.
- `r7_czas.json` to próba przyrządu `tools/orto_r7_czas.py` na 3 klatkach przy działającym biegu oceny. Nie jest to pomiar R7.

## Niewykonane

- **Ocena R5** na c10 i locie długim przerwana przy 42 z 78 zadań. Zapisane zadania są w katalogu `r4_ocena_NIEPELNA/` (po jednym pliku na lot, łatę i wariant, plus `bieg.log`). Lista gotowych i brakujących jest w `NIEPELNA.json`.
  - Zadań z lotów oceny jest 22: p02, p04, p07 (A, B, C), p09 (tylko C) i `L_c10_s01` (tylko C).
  - Pliki nie są scalone do `r4_ocena.json.gz` i nie liczono z nich żadnych zestawień.
- **R4 na lotach oceny i zestawienie R4/R5** (`orto_r5.py zestaw`) nie zostały uruchomione.
- **R6:** nie liczono.
- **R7:** zebrano tylko fakty widoczności z przypiętych plików, bez wariantów i wyceny:
  - W `x500_nadir2_flow/model.sdf` (sha 1fa0c57d…):
    - imager ma maskę 4294967293 (= ~bit1), l.21;
    - flow_camera ma maskę 4294967291 (= ~bit2), l.46;
    - lidar (l.85) i nadir (l.127) nie mają masek.
  - W `worlds/world_nadir2_A3.sdf` (sha 7f2bbe13…):
    - ground_plane ma flagi domyślne, l.21–29;
    - kont_decal ma flagi 2, l.1302;
    - 37 znaczników ma flagi 4 (od l.1315).
- **R8:** nie wykonano.

## Odchylenia od promptu

1. Commity: zamiast jednego commitu STOP są trzy wcześniejsze (`664d8459` łaty przed dopasowaniem, `70de170d` R1, `1b5971f4` R2) i ten jeden [STOP-ORTOR-DECYZJA], zgodnie z sygnałem Olgi.
2. Środki łat podałem z pamięci planu miasta, bez podglądu. Okno ma 100 × 100 m (prompt: łata 80 × 80 m), żeby zostawić margines pod kadr.
3. Archiwalnego WMS nie użyłem. Edycje wziąłem z arkuszy GeoTIFF (WFS Skorowidze, HTTP Range). Układy przeliczałem własnym kodem (szereg Krügera, `orto_uklad.py`), sprawdzonym s1.
4. Arkusz 2014 jako TIFF paskowy jest nieczytany przez czytnik; nie wchodzi do pary.
5. Kompozycję kandydatów (CLAHE, k = 8, ±6.5 m, parametry detektorów) dobrałem próbami wyłącznie na klatkach c05, czyli na zbiorze strojenia.
6. knn cech kadru liczony jest raz na klatkę do całej mapy łaty, potem filtrowany do okna szukania. To przybliżenie dopasowania w oknie: ratio test bierze pierwszych dwóch sąsiadów w oknie, a z k = 8 z całej mapy w oknie może nie znaleźć się żaden.
7. Łańcuch startuje z EKF w chwili cięcia (Δ = 0). Pozycja przewidywana to ostatnia przyjęta poprawka plus przyrost EKF, zgodnie z promptem.
8. Kryterium wyboru reguły (leksykograficzne, powyżej) jest moje, prompt go nie określa.
9. W R5 „najmniejszy błąd” oznacza regułę wybraną, gdy żadna nie spełnia 1.0 m. Liczby w tabeli dotyczą lotów strojenia.
10. Pierwszy bieg strojenia przerwałem z powodu tempa (knn per reguła) i przebudowałem. Pierwszy bieg oceny przepadł przy restarcie komputera. Drugi bieg oceny, z zapisem cząstkowym, przerwano sygnałem Olgi.

0 bootów. Sieć: wyłącznie usługi GUGiK. `worlds/` bez zmian. Bez pushu.
