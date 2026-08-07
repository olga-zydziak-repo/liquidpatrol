# CALIB_R02 — stałe habitatu kanału/OBSERVE (krok 0 R0.2, wg R02-A4)

Data: 2026-08-07. Reżim: **budowa, krok kalibracji (A4)**. Poprzednik: `RAPORT_B0.md` (PASS),
kanał `r02/target_channel.py` + `r02/config_r02.py`. Kryteria wyboru **zamrożone w PRE_R02 §2.3/§4**.

## Status wg A4 (jawnie): **PROWIZORYCZNE, ZWIĄZANE Z POMIAREM W BRAMCE**

Zgodnie z **R02-A4**: wartości albo pochodzą z pomiaru habitatu (histogram age-at-ENTRY / rozkład
luk detekcji na żywym mono 320×240), **albo są jawnie prowizoryczne i związane z pomiarem w bramce**.
Wybieramy tę drugą ścieżkę na etapie kroku 0: **reguły wyboru zamrożone tu; liczby = punkt startowy,
walidowany/mierzony w bramce G1–G5** (G1: ε_FP; G2: T_ack, f_fov, D_safe; G4: θ_age). **Żadna liczba
NIE jest skopiowana z G2/LiquidSight** (G2 = prowieniencja SEMANTYKI, nie liczby; „liczby się nie
przenoszą", A2 R0.1). Zamrożenie ostateczne = **zatwierdzenie Olgi** (wzorzec S3c0), przed bramką.

## Tabela stałych (źródło = `r02/config_r02.py`, jedno źródło prawdy — A2)

| Stała | Wartość prow. | Reguła wyboru (ZAMROŻONA, PRE §2.3/§4) | Gdzie mierzona/walidowana |
|---|---|---|---|
| `ENTRY_K` | **3** (ZAMROŻONE, 0ter) | k kolejnych klatek @1 Hz ≈3 s; rewizja tylko pomiarem | G1/G2 |
| `ENTRY_MOVE_THR` | 0.15 | maks. ruch środka boxa/klatkę @1 Hz dla „spójnej lokalizacji"; z rozkładu przesunięć intruza v≈3 m/s w FOV | G1 (brak fałszywych serii) / G2 |
| `L_DELIVER_S` | 0.10 | podłoga age = latencja E2E kamera→most→detektor→kanał; B0 zmierzył inferencję (p95 ≤22 ms), transport BEST_EFFORT dopełnia | R3/G2 (pomiar E2E) |
| `THETA_AGE_S` | 3.0 | **P95 naturalnych luk detekcji** na żywym strumieniu; separacja histogramów | **G4** (zachowanie na age+sufit) |
| `D_SAFE_M` | 8.0 | z FOV kamery + margines; > obwiednia intruza; „bez zbliżania" | **G2** (0 naruszeń dystansu) |
| `T_ACK_S` | ≈4.1 | = `k·DET_DT + L_deliver + margines` (wyliczone, nie zgadnięte) | **G2** (ENTRY ≤ T_ack) |
| `F_FOV` | 0.8 | min. udział klatek z celem w FOV podczas OBSERVE | **G2** |
| `EPS_FP_PER_MIN` | 0.0 | cel: 0 fałszywych ENTRY na pustej scenie/min | **G1** (mierzy jawnie) |
| `INTRUDER_ALT_M` | 10.0 | z SDF aktora (r02/intruder_driver z=10) — geometria, nie kalibracja | — |

### Kandydaci (2–3 punkty do decyzji Olgi, wzorzec S3c0)
- **θ_age** ∈ {2.0, **3.0**, 5.0} s — 3.0 = ~3 ticki detektora zmostkowane ZOH (środek). Węższy sufit
  (2.0) = szybsze wyjście z OBSERVE po utracie; szerszy (5.0) = dłuższe mostkowanie martwego pola.
  **Rozstrzygnięcie: G4** — jeśli martwe pole > θ_age systematycznie łamie G4, to nazwany tryb
  porażki (SR-4) — ale najpierw poszerzyć θ_age w granicach zdrowego rozsądku, nie sięgać po rdzeń uczony.
- **D_safe** ∈ {6.0, **8.0**, 10.0} m — 8.0 środek; walidacja G2 (0 naruszeń, cel w FOV ≥ f_fov).
- **move_thr** ∈ {0.10, **0.15**, 0.20} — 0.15 środek; G1 (brak fałszywych serii na szumie).

## Zastrzeżenia (uczciwie)
1. **Nie zbudowano histogramu luk detekcji offline** w kroku 0: rozkład luk na mono 320×240 jest
   funkcją TEJ pętli (kamera→most→detektor) przy żywym symie — mierzalny dopiero z żywym strumieniem,
   co jest równoważne wejściu w bramkę. Zamiast fabrykować histogram bez pętli, wiążemy θ_age z **G4**
   (A4 dosłownie: „prowizoryczna i związana z pomiarem w bramce"). To wynik uczciwy, nie zaległość.
2. **conf poza kanałem (A1):** żadna z tych stałych nie jest progiem conf. `move_thr` to próg
   GEOMETRYCZNY (ruch środka), nie confidence — ENTRY jest strukturalny (0ter/R1-B), nie conf.
3. Zmiana którejkolwiek stałej po bramce = **strojenie po fakcie** (zakazane, §4/SR-5). Wartości
   zamrażamy PRZED bramką; bramka mierzy i albo potwierdza, albo daje wynik NEGATYWNY (pełnoprawny).

## Zamrożenie
Reguły wyboru: **ZAMROŻONE** (ten dokument + PRE §2.3). Liczby: **prowizoryczne, w kodzie
`r02/config_r02.py`**, oznaczone `[PROWIZORYCZNE/A4]`. Ostateczny freeze liczb = decyzja Olgi.
