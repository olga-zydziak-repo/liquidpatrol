# ANEKS_D2 — DEMO-B blok B2: adnotacje ratyfikacyjne + FREEZE światów aktów

Aneks do `ANEKS_D1.md` / `PRE_D.md`. Zapis decyzji z 16.08.2026 dla bloku B2 (PROMPT_D_BUILD_2 §0)
oraz kanoniczny rejestr **zamrożonych hashy światów** per akt (§2 FREEZE). Wzorzec korekt zachowany.

## Adnotacje ratyfikowane

- **A4 — domknięcie luki cert↔konfiguracja (RAPORT_D_B1 pkt 5):** wszystkie akty biegną z
  **`token_gated=True`** — ZAMROŻONE. `auth_ok=True` (domyślny w `shield.step`) to tryb **legacy**
  wyłącznie dla zgodności wstecznej R0.2/R0.3a i leży **poza** roszczeniem tokenowym. Obligacje
  tokenowe P1g/P1h/P4-token obowiązują end-to-end **tylko przy `token_gated=True`**. Runner per-akt
  (B4) dostanie **assert `token_gated is True`** na starcie + echo flagi w manifeście i trace.
  (Naniesione też jako A-auth w `P1.json:assumptions` — B1.)
- **A5 — uczciwość HITL:** operator w aktach = **skryptowany sygnatariusz** (zdarzenie `grant`
  o zadanym `sim_t`/triggerze). Napisy i plansze mówią wprost: „operator: skrypt podpisujący,
  HITL symulowany" — zero sugestii żywego człowieka w pętli. Egzekwowane w B3 (napisy) i B6 (plansze).

## FREEZE światów aktów (§2)

Generacja: `worlds/gen_world_demo_v1.py` (rozszerzony parametrycznie, B2). Terrain = seed `20260815`
(84 bryły, NIEZMIENIONE). Kamera filmowa per akt = par. sondy R2 (1280×720@30, always_on, statyczna),
skadrowana aim-at-centroid akcji aktu. **Intruz NIE pieczony w świat** (frozen finding RAPORT_R1 §1:
skinless `<actor>` segfaultuje serwer gz) — model `r02/intruder_model.sdf` spawnowany w runtime,
sterowany przez runner per-akt (B4) wg `acts/<AKT>_spec.yaml`.

| Świat | sha256 | uwagi |
|---|---|---|
| `worlds/world_demo_v1.sdf` | `a76a38c83cc774d325222688cb2b2055f0565bb54eec11c33f99ec361b1c83b0` | terrain frozen (ANEKS-H) — BAJT-identyczny po rozszerzeniu generatora |
| `worlds/world_demo_A1.sdf` | `d7e3db2492ccb8ae87fb8810a92095d5e8667f83ef6a268d347fe44452349ccb` | +kamera A1 (kadr na midpoint dron↔intruz) |
| `worlds/world_demo_A2.sdf` | `dd0c85e26ea20615346f6ac837b15ff1ffef6a215908a3b007a38dd70b8d8ce4` | +kamera A2 (jw., zapas na wyjście/powrót) |
| `worlds/world_demo_A3.sdf` | `486a0cea3bf2d946e8e9f559428b7f3dcf13cb2e9804935764e4f02395334c60` | +kamera A3 (zejście velocity-descent) |

Kadry kamer (aim-at-centroid, ENU; `_cam_pose` w generatorze):

| Akt | cam_pos (x,y,z) | centroid | pitch [rad] | yaw [rad] |
|---|---|---|---|---|
| A1 | (10, −14, 8) | (3.93, 0, 10.75) | 0.1783 | 1.9799 |
| A2 | (12, −16, 8) | (3.93, 0, 10.75) | 0.1523 | 2.0379 |
| A3 | (14, −18, 7) | (13, 0, 4) | −0.1649 | 1.6263 |

**Reguła:** zmiana świata po freeze = **nowy hash + jawna adnotacja** (nigdy cicha podmiana — SR-C3).
Walidacja loadowalności bez serwera: `gz sdf -k` → **Valid.** dla A1/A2/A3 (brak regresji actor-crash).

**Kadr pikselowy** (czy kamera faktycznie obejmuje akcję w pikselach) NIE jest weryfikowany w B2
(rehearsal offline geometria/timing, bez renderu — §3). Pozy kamer są **geometrycznie wycelowane**
w centroid akcji; weryfikacja pikselowa = pierwsza próba B5 (albo osobny render-check). Zapisane jawnie.
