# AB_TEMPO — diagnostyka tempa po STOP-NADIR1-TEMPO (0 bootów lotnych; decyzja Olgi 9.11 „tryb wydajny ustawiony, rób test A/B”)

Narzędzie `results/NADIR/tools/nadir_ab.py`; dane `ab_tempo.json`, `rtf_*.jsonl`, `nadir_ab.log`. Goły gz bez PX4,
świat world_nadir_A3, statyczny rig na (5, 5, 12), konsumenci klatek jak w boocie (nadir z detekcją ArUco).
Przebiegi naprzemiennie A, B, A, B; dsim/dwall z regresji po oknie 120 s po rozgrzewce 20 s.

| przebieg | dsim/dwall | imager Hz | przepływ Hz | nadir Hz |
|---|---|---|---|---|
| A z nadirem | 0.6230 | 9.59 | 31.65 | 9.59 |
| B bez nadiru | 0.6982 | 10.74 | 35.41 | — |
| A z nadirem | 0.6117 | 9.50 | 31.34 | 9.50 |
| B bez nadiru | 0.6918 | 10.66 | 35.16 | — |
| **średnia** | **A 0.617 / B 0.695** | | | |

- **Druga kamera kosztuje ~11% tempa** (A/B = 0.888, powtarzalne: różnica 0.07–0.08 w obu parach).
- Poziom bezwzględny tego stanowiska testowego jest niższy niż w boocie (konsumenci klatek w jednym procesie Pythona).
  Liczy się stosunek. Przeniesiony na najlepsze tempo bootów KONT S4 w trybie wydajnym (0.97–0.98) daje
  **~0.86–0.87 < 0.93** — zgodnie ze zmierzonym b2 0.854.
- **Wniosek:** spadek tempa w b2 tłumaczy sam drugi render, a nie stanowisko. Hipoteza (a) potwierdzona w granicach
  tego testu, (b) nie jest potrzebna.
- **Skażenie, nazwane:** pierwsze dwie próby testu odrzucone, dane w scratchpadzie poza repo.
  - Próba 1: `teardown` (`pkill -f "gz sim"`) zabił moją własną powłokę, bo jej linia polecenia zawierała ten napis.
  - Proces potomny `nadir_ab.py` żył dalej i w próbie 2 równolegle uruchomił drugi serwer gz z tym samym światem
    (reset czasu sim, przeplecione pliki RTF).
  - Czysty przebieg (ten): 0 cofnięć sim i wall we wszystkich 4 plikach.
