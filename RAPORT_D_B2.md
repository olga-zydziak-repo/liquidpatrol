# RAPORT_D_B2 — DEMO-B blok B2: choreografia intruza + światy aktów

Data: 2026-08-16. Zakres: **wyłącznie B2** — choreografia (specs), światy per akt, rehearsale
walidacyjne. NIE: re-wiring runnera per-akt (B4), patche trace/napisy (B3), nagrania (B5), montaż (B6).
**`r01/` NIETKNIĘTE.** Reżim bez zmian; prowieniencja per liczba; FAIL=FAIL; **push = Olga**.

## Stan wejściowy / wyjściowy (SR-C5, SR-C1)

- **SR-C5:** HEAD = origin/master = `cdf4929` po pushu Olgi (B1: `c25707e`→`cdf4929`), drzewo czyste.
  (Sesja startowa najpierw stanęła na SR-C5 gdy B1 był niepushowany — Olga pushnęła, wznowiono.)
- **`certs_selfcheck` bieg #1 (start): PASS 6/6** · **bieg #2 (koniec): PASS 6/6** — `r01/` nietknięte (SR-C1).
- Łańcuch commitów B2 (niepushowane):
  - `<C1>` §0/§2: ANEKS_D2 (A4/A5) + FREEZE światów.
  - `<C2>` §1/§2: generator parametryczny + światy A1/A2/A3 + specs aktów.
  - `<C3>` §3: rehearsale offline + verdicts.
  - `<C4>` §4: RAPORT_D_B2.

## §0 — Adnotacje (ANEKS_D2)

- **A4:** akty biegną `token_gated=True` (ZAMROŻONE); `auth_ok=True` legacy = poza roszczeniem; runner
  B4 dostanie assert + echo flagi. Domyka lukę cert↔config z RAPORT_D_B1 pkt 5.
- **A5:** operator = skryptowany sygnatariusz (HITL symulowany); napisy/plansze mówią to wprost.

## §1 — Choreografia per akt (specs z prowieniencją)

Pliki `acts/A1_spec.yaml`, `acts/A2_spec.yaml`, `acts/A3_spec.yaml` — KAŻDA liczba z `source:`.
Kluczowe wielkości i źródła:

**Geometria pierścienia (A1/A2):** dron dwell-hover NED `(0,0,−10)` (alt 10 = `ALT_M`, r01.config);
intruz dead-ahead ENU `(7.86, 0, 11.5)` → **range 3D = 8.00 m** (`INTRUDER_ALT_M=11.5` config_r02,
1.5 m nad patrolem; koperta 5–9 m środek 7 config_r02 A7; d*≈8 PRE_D §5; horizontal=√(8²−1.5²)=7.86);
osc ±1.0 m (< REGATE ±1.5). Pasmo ważności 3D **[7,9] m** (PRE_D §5 / REGATE).

**Timing ENTRY:** `t_entry_p95 = 10.87 s` — **max z valid boots REGATE, pierścień {7,9} m**
(`time_to_entry_s_raw` 7m [2.17, 2.22, 5.98], 9m [1.63, 2.75, 10.87]; p95≈max, n=6). A1 dwell w
pierścieniu = 26 s = p95 10.87 + grant 3.0 + OBSERVE 10.0 + margines 2.13 → ENTRY-okno [23, 33.87]
mieści się; worst-case ENTRY+grant+OBSERVE = 46.87 ≤ 49 (koniec ring_hold).

**Operator (A5):** `grant` na trigger `on_entry + 3.0 s` — 3 s widoczności `REFUSE(NO_AUTH)` przed
grantem (DECISION 20 Hz `TICK_HZ` r01.config; DET 1 Hz `DET_HZ` config_r02 → NO_AUTH co tick od locka).

**A2 EXPIRE:** intruz „poza zasięg" = ENU `(70,0,11.5)` (horizontal 70 ≫ 9 koperty); `expire_gap = 6.0 s
= k·θ_age`, **k=2.0 ≥ 1.5** (`THETA_AGE_S=3.0` config_r02). Re-admisja: `admission_seq 0→1` na re-ENTRY,
`grant_2` wymaga NOWEGO tokenu (ep0 skonsumowany na EXPIRE — kontrakt B1 `consume_tokens`). Dwa beaty.

**A3 GPS-denied (bez tokenu):** denial `EKF2_GPS_CTRL=0` (R0.3a NIETKNIĘTY) na trigger
`drone_radial_reaches_outbound(18.0)`. `R_route' = R_E − d_stop − ε_cap = 32 − 2.25 − 9.25 = 20.5 m`
(`V_MAX=3`, `A_BRAKE=2` → d_stop=2.25; ε_cap=9.25 RAPORT_R03A). r_inj 18 ≤ 20.5 ⇒ **touchdown ≤
r_inj+ε_cap+d_stop = 29.5 < R_E=32** (containment; S2 demonstrował 14.84 m). `REFUSE(POS_DEGRADED)
≤ 0.15 s` (S2 0.091). velocity-descent dwufazowy (AUTO.LAND wykluczony; plansza kontrastu 42 m).
> ⚠ ERRATUM_42M (PRE_K1 §0): „42 m” = asercja 09.08, bieg niezachowany (brak kodu/trace/ulog) — superseded by K1 measurement (PRE_K1). Zob. results/K1/ERRATUM_42M.md

**Tranzyty (D3(b)):** każdy segment `transit` oznaczony `beyond characterized envelope`; roszczenie
percepcji WYŁĄCZNIE w dwell/OBSERVE (D3(a)).

## §2 — Światy per akt (FREEZE)

Generator `worlds/gen_world_demo_v1.py` rozszerzony parametrycznie (`--act A1|A2|A3`): dokłada kamerę
filmową (par. sondy R2) skadrowaną aim-at-centroid; nazwa świata `world_demo_<AKT>` (spójność topików).
**Default (bez `--act`) generuje `world_demo_v1.sdf` BAJT-w-BAJT identycznie** (hash `a76a38c8…`
zweryfikowany `diff` = identyczny; terrain/seed/kolejność nietknięte).

| Świat | sha256 (16) | `gz sdf -k` |
|---|---|---|
| world_demo_v1 | `a76a38c83cc774d3` | (frozen ANEKS-H) |
| world_demo_A1 | `d7e3db2492ccb8ae` | Valid. |
| world_demo_A2 | `dd0c85e26ea20615` | Valid. |
| world_demo_A3 | `486a0cea3bf2d946` | Valid. |

Pełne hashe + pozy kamer w `ANEKS_D2.md`. **Intruz NIE pieczony w świat** — patrz Rozbieżność 1.

## §3 — Rehearsale (offline geometria+timing, NIE dowód)

`results/demo/rehearsal/rehearse.py` — RE-DERYWUJE liczby z FROZEN źródeł (r01.config, config_r02,
REGATE aggregate, RAPORT_R03A) i porównuje ze spec (łapie dryf prowieniencji), po czym ocenia
kryteria ważności. **Nie dotyka percepcji** (§3: werdykty percepcyjne nieraportowalne — tu binarne sanity).

| Akt | rehearsali | verdict | sprawdzone |
|---|---|---|---|
| A1 | 1 | **PASS** | Δalt=1.5 frozen; range3d ∈ [8.00, 8.06] ⊂ [7,9]; t_entry_p95 10.87 == REGATE; ENTRY-okno w hold; grant+OBSERVE ≤ hold |
| A2 | 1 | **PASS** | range3d w paśmie; far 70 m ≫ 9; expire_gap 6.0 = k·θ_age; re-ENTRY w ep1; 2 beaty |
| A3 | 1 | **PASS** | R_route' 20.5 == frozen; r_inj 18 ≤ 20.5; touchdown 29.5 ≤ R_E; REFUSE ≤ 0.15; brak tokenu |

Artefakty: `results/demo/rehearsal/<AKT>/rehearsal_1/verdict.json`. **Kryterium wyjścia B2 spełnione:**
≥1 rehearsal/akt w tolerancjach + zamrożone hashe światów + specs z pełną prowieniencją.
Rehearsal ≠ próba aktu (licznik ≤3 „pierwsza ważna" startuje w B5).

## Rozbieżności (jawnie)

1. **Intruz: MODEL+runtime-teleport, NIE `<actor>` w świecie (odejście od §2 literalnego).** §2 wymienia
   „trajektoria aktora" jako parametr generatora świata. FROZEN finding **RAPORT_R1 §1**: skinless gz
   `<actor>` **segfaultuje serwer** (MeshManager.cc:150, SceneBroadcaster). Frozen rozwiązanie =
   `r02/intruder_model.sdf` (MODEL static, mesh x500) spawnowany w runtime + `set_pose` (jak MTI/REGATE).
   Dlatego generator dokłada **tylko kamerę**; trajektoria intruza f(sim_t) żyje w `acts/<AKT>_spec.yaml`
   i będzie sterowana przez runner per-akt (B4). Alternatywa (bake actor) resurektowałaby crash (SR-C6).
2. **Rehearsal jest OFFLINE (geometria/timing), nie SITL.** Runner per-akt (B4) jeszcze nie istnieje —
   nic nie wykonałoby choreografii w locie. Rehearsal offline bezpośrednio odpowiada SR-C2 (czy kryteria
   są choreograficznie osiągalne przy frozen progach) i jest zgodny z §3 („nie dowód percepcji").
   `gz sdf -k` dał `Valid.` (loadowalność bez serwera). **Pełny lot rehearsalowy = możliwy dopiero po B4.**
3. **Kadr pikselowy kamery nieweryfikowany w B2** (brak renderu bez SITL). Pozy kamer geometrycznie
   wycelowane w centroid akcji (aim-at-centroid); weryfikacja pikselowa = pierwsza próba B5. Zapisane
   w ANEKS_D2.
4. **t_entry_p95 = max (n=6), nie prawdziwy p95.** REGATE ma 3 booty × {7,9} m = 6 próbek; „p95" ≈ max
   10.87 s (boot regate3, ten z rtf_end collapse w teardown — pomiar ważny per ANEKS-H). Konserwatywnie:
   używam max jako p95. Jeśli B5 pokaże dłuższe ENTRY, okna dwell wymagają rewizji (progów NIE luzuję).
5. **d* geometryczny = 8.00 m, nie dokładnie „≈8".** Wybrałem horizontal 7.86 m by 3D = 8.00 (środek
   pasma). Osc ±1.0 daje 3D ∈ [8.00, 8.06] — całe wewnątrz [7,9]. Zapas do krawędzi pasma ~1 m.

## Kryteria ważności PRE_D §5 — osiągalne? (SR-C2)

TAK, choreograficznie osiągalne przy frozen progach: intruz mieści się w pierścieniu {7,9} w oknie dwell
dłuższym niż t_entry_p95; timing segmentów spójny; A3 touchdown w R_E przez frozen arytmetykę. **Żaden
próg nie był luzowany.** Gdyby okno t_entry fizycznie nie mieściło się — byłby STOP (SR-C2); nie wystąpił.

## STOP

Blok B2 domknięty: 3 specs z prowieniencją, 3 światy zamrożone (default byte-identyczny), 3 rehearsale
PASS (offline), selfcheck 6/6 ×2 (`r01/` nietknięte). **B3 (patche trace a/b/e/f + generator napisów
z asertem kompletności) — osobny prompt po przeczytaniu tego raportu przez Olgę. Push = Olga.**
