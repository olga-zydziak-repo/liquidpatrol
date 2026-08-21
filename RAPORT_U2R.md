# RAPORT_U2R — finalne wznowienie U2: świat v3 (bramka ZDANA) + próby + montaż długi

Data: 2026-08-22. Zakres: PROMPT_D_U2R. **Wynik: SUKCES bramki i prób; montaż długi na v3.**
Roszczenia/plansze §1c/sędzia `79b1e936`/spec NIETKNIĘTE. v1/v2 generatory i materiał v1.0 NIETKNIĘTE.

## [2] Zmiany świata (world v3, `worlds/gen_world_demo_v3.py` — NOWY)
Zostaje z v2: niebo (`background 0.52 0.66 0.85`), trawiaste podłoże, odległy backdrop (skyline
zabudowy). **Naprawa kosztu renderu (przyczyna FAIL U2): `cast_shadows=false` na WSZYSTKICH dekoracjach**
(pole brył + drzewa + zabudowa + skały; słońce/scene-shadows zostają → cień dynamicznego intruza/drona
w HUD). Korony LOW-POLY (box zamiast ellipsoid), mniej drzew (14/11/7 = 116 modeli). Strefa operacji
płaska z=0, **ZERO nowych kolizji** (1 collision = ground_plane).

## [4] BRAMKA ŚWIATA — PASS (1. bieg ważny, progi byte-identyczne)
| bieg | dwell Δsim/Δwall (≥0.95) | frac<0.5 (=0) | min_rtf | H1 timejump | H2 |
|------|-------------------------:|--------------:|--------:|-------------|----|
| U2 v2 (odniesienie, FAIL) | 0.822–0.933 | 0.0037 | 0.004 | 0 | FAIL |
| **U2R v3 control_1** | **0.9997** | **0.0** | **0.93** | 0 | **PASS** |
Kadr-check [4a]: dron+intruz+akcja w kadrze (42 klatki filmowe). **Potwierdza: shadows/tessellacja
dekoracji były przyczyną render-hitch U2** — usunięcie ich naprawia RTF z dużym zapasem.

## [5] PRÓBY DOWODOWE — pierwsza ważna, sędzia FROZEN 79b1e936
| akt | próba | JUDGE | HABITAT | world_hash v3 | echa |
|-----|-------|-------|---------|---------------|------|
| **A1** | `results/demo/A1_v3/proba_1` | **VALID** | VALID | bf95b7bc | detection_channel=gt_fed, intruder_slaved=True |
| **A3** | `results/demo/rehearsal/A3/v3_1` | **VALID** | VALID | adc91803 | detection_channel=n/a (A3 intruz absent) |
ensure_gps przed każdym bootem (gps_hygiene). A1 z `U2R_SLAVE=1`.

## [3] Scenografia intruza + rozjazd model↔tor
`r02/intruder_model.sdf` = PRYMITYWY (mesh DAE nadpisywał kolor SDF): kadłub+ramiona pomarańcz, 4 rotory,
**span ~2.4 m** (×~5 vs v1.0). Slaving `U2R_SLAVE=1`: `_channel_step` GT czyta `self._intr_ned`
(teleport = JEDYNE źródło) zamiast `gt_intruder_fn(wall_t)` → **trace intr_ned ≡ pozycja modelu (single
source, rozjazd ≤ latencja set_pose, sub-0.5 m z konstrukcji)**. Echo `intruder_slaved`/`track_source`
w manifeście.
**ZNALEZISKO (uczciwie):** intruz jest POWIĘKSZONY i OBECNY (rzuca wyraźny cień quada), ale renderuje się
BLADO z ~24 m film-cam (mała jasność sylwetki vs niebo/dekoracja). Marker-on-silhouette [6] wymaga
WIDOCZNEJ sylwetki; tu trzymamy **datum toru GT** (U1R §2b: diament+leader+„GT track · range", cyan) —
honest, bo box-on-silhouette jest warunkowe. Rozjazd geometryczny toru = sub-0.5 m (slaving); ograniczenie
jest RENDEROWEJ WIDOCZNOŚCI, nie pozycji. (Domknięcie: film-cam bliżej / model jaśniejszy — poza frozen.)

## [7] MONTAŻ DŁUGI — `results/demo/DEMO_B_A1_A3_v3.mp4` (+`_h264`)
**109 s** (≥90), 8 faz każda ≥8 s (≥3.5), sim_t w rogu, kompresje ×N jawne, wyłącznie klatki osądzone.
Cut-lista (sim_t → czas ekranowy):
| akt | faza | sim_t | ekran | ×N |
|-----|------|-------|-------|----|
| A1 | takeoff / patrol | 0–22 | 12.6 s | ×1 |
| A1 | intruder approach | 22–25 | 8.0 s | (wolniej) |
| A1 | ENTRY / REFUSE / OBSERVE | 25–52 | 27.6 s | ×1 |
| A1 | RTL / land | 52–54 | 8.0 s | (wolniej) |
| A3 | GPS nominal | nominal | 12.1 s | ×1 |
| A3 | REFUSE · POS_DEGRADED | degrad. | 8.0 s | — |
| A3 | controlled descent | descent | 8.0 s | (wolniej) |
| A3 | touchdown (contained) | touchdown | 8.0 s | (wolniej) |
HUD: datum toru + pasek MODE + token + §1c. Manifest montażu: `_manifest.json` (sha klatek + cut-lista).

## Prowieniencja / rollback
Świat v3, próby v3, montaż — NOWE pliki OBOK v1.0 (v1.0 mp4/konsola/HUD/A1+A3 proba_1 NIETKNIĘTE).
Rollback = tag v1.0. Budżet [9]: 1 sesja. Commity niepushnięte (push=Olga).
