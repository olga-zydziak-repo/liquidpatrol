# RAPORT_U2 — uplift wizualny world_demo_v2: STOP na bramce świata (H2/RTF), rollback v1.0

Data: 2026-08-21. Zakres: PROMPT_D_U2 — wizualnie bogatszy świat + powtórka prób.
**Wynik: STOP U2 na §3b (bramka habitatu, 2/2 biegi kontrolne FAIL). Rollback = tag v1.0.**
Demo v1.0 pozostaje kompletne i niezmienione (§8).

## [0] Prereq — PASS
origin/master..HEAD puste (Olga pushnęła v1), tag `v1.0` @b3bc7a5 istnieje (baza rollbacku).

## [2] Zmiany świata (wizualne, wykonane)
Generator **`worlds/gen_world_demo_v2.py`** (NOWY). `worlds/gen_world_demo_v1.py` i `world_demo_v1.sdf`
**NIETKNIĘTE** (hash a76a38c8 frozen) — v2 REUŻYWA v1 (HEADER/kamera/pole-brył 84, paralaksa §2d).
Wzbogacenie **wyłącznie WIZUALNE, ZERO nowych kolizji** (1 collision = ground_plane):
- niebo `background` 0.7-szary → `0.52 0.66 0.85` (błękit);
- podłoże `ground_plane` szary → trawiaste `0.36 0.45 0.28`;
- drzewa (pień cylinder + korona ellipsoid), zabudowa (skyline box), skały (ellipsoid) — **POZA strefą
  operacji** (r > CLEAR_ZONE=18 m; akcja ≤15 m), tło w kadrze kamery;
- fill-light miękki (sky-fill), słońce `sunUTC` nietknięte.
Podgląd wizualny: `results/demo/A1_v2/v2_preview_frame.png` — **uplift potwierdzony** (błękitne niebo,
zielona trawa, drzewa, skyline z głębią/paralaksą, dron w locie). Determinizm: osobny `SEED_ENR`.

## [3] BRAMKA ŚWIATA — FAIL (2/2 biegi kontrolne, bez osądu)
[3a] kadr-check: dron+intruz+akcja W KADRZE (34 klatki filmowe/bieg) — OK.
[3b] habitat na biegu A1-kształtnym: **H1 lockstep PASS** (timejump=0) w obu; **H2 (segment roszczeń
`dwell_observe` [23,49]) FAIL** w obu:

| bieg | modeli | Δsim/Δwall (≥0.95) | frac<0.5 (=0) | min_rtf | H2 |
|------|-------:|-------------------:|--------------:|--------:|----|
| v1 (odniesienie, proba_1) | 84 | **0.9955** | 0.0 | 0.841 | PASS |
| control_1 | 166 | 0.933 | 0.0037 | 0.008 | FAIL |
| control_2 (redukcja assetów §3b: trees 44→12, bldg 16→10, rocks 22→6) | 112 | **0.822** | 0.0037 | 0.004 | FAIL |

**ZNALEZISKO (deviacja od premisy §3b):** redukcja assetów (166→112) **NIE poprawiła** — Δsim/Δwall
spadło (0.933→0.822), frac<0.5 bez zmiany, **deep-stalle** (min ~0.005; jedna klatka ~200× dłuższa)
w OBU biegach v2, brak w v1 (min 0.841). ⇒ koszt jest **render-load/hitch-dominated** (cienie/tessellacja
sceny wzbogaconej PRZY równoczesnym przechwytywaniu filmu w dwell), **nie liniowy w liczbie modeli**.
Certyfikacyjny próg Δsim/Δwall≥0.95 (wierność sim-time roszczeń) niespełniony niezawodnie.

## [4]–[7] NIEWYKONANE
Bramka świata blokuje próby dowodowe. Sędzia `79b1e936`, spec, roszczenia, plansze §1c, HUD — NIETKNIĘTE.
(Luka niezależna: [5] HUD odwołuje `PROMPT_D_U1 [2]-[3]`, nieobecne w repo — wymagane od Olgi przy wznowieniu.)

## STOP / ROLLBACK (§3b, §8)
Per §3b (druga porażka ⇒ STOP U2, powrót do v1.0) i §8 (demo kompletne niezależnie):
- `worlds/world_demo_A1.sdf`, `worlds/world_demo_A3.sdf` PRZYWRÓCONE do v1.0;
- `gen_world_demo_v2.py` + artefakty kontrolne (`results/demo/A1_v2/`) ZACHOWANE jako dowód U2
  (regeneracja v2 natychmiastowa gdyby wznowić z innym lewarem).
- Demo dostarczane pozostaje **v1.0** (mp4/konsola HTML/próby A1+A3 VALID) — nietknięte.

## Kierunki (gdyby Olga wznowiła U2 osobnym promptem — poza budżetem §8)
Lewary poza §3b (render-hitch, nie count): (a) film-capture OFF w dwell (RTF gate) a ON tylko do
montażu z osobnego biegu; (b) LOD twardy — korony/skały jako box zamiast ellipsoid (mniej tessellacji/
cieni), cast_shadows=false na tle; (c) rozgrzewka renderu przed oknem roszczeń; (d) rewizja progu H2 dla
świata filmowego. Żaden nie mieści się w pre-rejestracji §3b — wymaga ratyfikacji.
