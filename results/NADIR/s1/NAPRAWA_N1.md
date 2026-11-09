# NAPRAWA_N1 — raport cząstkowy ANEKS_NADIR-1 §CO (1)–(4), 0 bootów lotnych

Wykonawca · 9.11.2026. Bramka: origin/master = 4603ee90. CO-N1 `e564a98a`: aneks w korzeniu, sha256 z wklejki
`c80f1fe8fc0836bfff480e861bd69a5c790e6d078d0ebdedb477f78f2e6c89ac` (CC nie podał — do potwierdzenia przez Olgę) +
KSIĘGA §3 append-only. Sygnał „ratyfikuję N1” nie padł ⇒ budżet S1 ≤ 4 (2 użyte, zostają b2′ i b3′, zero rezerwy).

## Raport płaski

- **(1) Kadencja: 5 Hz** (`n1/ab_kadencja.json`, `tools/nadir_n1_ab.py`). A/B gołego gz przeplatany
  B, A5, A3, A2, B, A2, A3, A5, B (po 120 s, detekcja włączona, 0 cofnięć czasu we wszystkich 9 plikach).
  - B (bez nadiru): 0.905 / 0.926 / 0.905 → średnia 0.912.
  - A5: 0.928 / 0.927 → stosunek 1.017 → przeniesione na 0.97 = **0.987**.
  - A3: 0.908 / 0.924 → 1.004 → 0.974.
  - A2: 0.925 / 0.923 → 1.013 → 0.983.
  - Wszystkie ≥ 0.94, więc wybieram najwyższą: **5 Hz**. Przy ≤ 5 Hz koszt drugiej kamery mieści się w szumie sesji
    (±0.01), wbrew liniowej ekstrapolacji z 9.6 Hz.
  - **Zastrzeżenie, nazwane:** poziom bezwzględny tej sesji (B 0.91) jest dużo wyższy niż w poprzednim A/B (B 0.69,
    zaraz po restarcie maszyny). Stanowisko ma wariancję między sesjami, którą ten pomiar uśrednia tylko w sesji.
    Ostatecznie rozstrzyga bramka tempa w boocie.
- **(2) Montaż v2: pod płozy, (0, 0, −0.215) m względem base_link.**
  - Geometria z `x500_base/model.sdf` (collision_3/4): płozy y = ±0.132, z środka −0.2195, spód −0.227. Kamera leży
    na wysokości płóz, między nimi (płozy ~85–90° od osi optycznej, poza stożkiem ±43.5°). Nogi, silniki i czujnik
    przepływu są nad kamerą. Prześwit na ziemi 0.025 m.
  - **Maska kadłuba v2: 0.0% kadru i 0.0% stożka** (wymóg ≤ 2%) — `n1/maska_v2.json`, ta sama metoda dwóch póz;
    klatki `n1/nadir_v2_*.png` czyste.
- **(3) Manifest v2** (`n1/manifest_znaczniki_v2.json`, `tools/nadir_n1_manifest.py`, świat `worlds/world_nadir2_A3.sdf`
  sha 7f2bbe13…, assert bajtowy vs world_kont_A3):
  - Węzły z listy aneksu przesunięte do wolnego miejsca z asercją vs SDF: id 1 o 0.35 m, 4 o 0.71, 7 o 0.79,
    14 o 2.06, 24 o 1.03, 27 o 0.75, 31 o 1.46 m (wszystkie ≤ s/2).
  - **Znalezisko — mój parser był niepełny:** `nadir_gen.bryly` brał tylko pierwszy box modelu, więc korony drzew
    (box ~3.9 m na wysokości ~4.6 m) umykały. Pełny parser (każdy visual box, margines 1.0 m) wskazuje **7 kolejnych
    węzłów zasłoniętych z góry albo tuż przy bryle: id 0, 8, 15, 16, 22, 32, 35** (korony tree_9/0/11/3/10, skrzynki
    tex_38/39, budynek bldg_7).
  - Aneks pozwala przesuwać tylko listę 7, więc tych **nie ruszałam**. W desk-bramce liczę je jako niewidoczne
    (konserwatywnie). Decyzja o nich — CC.
- **(4) Desk-bramka pokrycia §2.5: PASS przy 5 Hz** (`n1/desk_pokrycie_v2.json`, `tools/nadir_n1_desk.py`).
  - Narzędzie reconu (import READ-ONLY), manifest v2, montaż v2, maska v2, pełna postawa, bok ≥ 18 px, siatka klatek
    5 Hz, 7 węzłów dodatkowo zasłoniętych = niewidoczne.
  - **≥ 1 znacznik w 99.948% klatek misji** (wymóg ≥ 99.9%): approach 99.945 / hold 99.955 / orbit 99.948.
  - **τ_max 1.8 s** (wymóg ≤ 2 s), najgorszy epizod c08_s04 (SKAN2 bA_c08).
  - Dla porównania: 3 Hz i 2 Hz dają 99.946% przy τ_max 2.0 s (na granicy).
  - **Zapas jest cienki:** 0.048 pp ponad wymogiem i 0.2 s do progu τ — wynik konserwatywny. Bez 7 dodatkowo
    zasłoniętych węzłów byłby lepszy.
- **Pin v2** `n1/pin_nadir_v2.json`: model `x500_nadir2_flow` (sha 1fa0c57d…), montaż −0.215, 5 Hz, OpenCV 4.6.0
  systemowe — FROZEN.
- **Wszystkie bramki przechodzą ⇒ b2′ i b3′** (`tools/nadir_s1v2_*` = kopie v1 z zamianą nazw modelu i świata,
  asercje; analiza `nadir_s1v2_analyze.py` z offsetem montażu: poprawka daje środek kamery, dron = kamera − R·montaż).

## Wady wykonawcy

- Parser brył z S1 był niepełny (korony drzew); wyszło przy manifeście v2, poprawione nowym parserem. Liczba „7/37 pod
  bryłami” z STOP-NADIR1-TEMPO była zaniżona — pełny parser daje 14/37 w v1 (z marginesem 1.0 m zamiast 0.7 m).
