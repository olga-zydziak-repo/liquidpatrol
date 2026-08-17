# RAPORT_D_B5 — DEMO-B blok B5: sanity-live A1 zablokowane (SR-G6 STOP) + infrastruktura LIVE

Data: 2026-08-17. Zakres: B5 — sanity-live, próby dowodowe, detektor LIVE. **STOP na SR-G6**
(cztery niepowodzenia środowiska boot/health w konfiguracji LIVE; przyczyna niedomknięta →
„nie brnąć"). Reżim bez zmian; **push = Olga**.

## Stan wejściowy / wyjściowy (SR-G5, SR-G4, SR-G1)

- **SR-G5 (pierwsza czynność):** `git log origin/master..HEAD` = PUSTE (Olga pushnęła B4). HEAD =
  origin/master = `7b87808` na starcie. (Wcześniej STOP na SR-G5 bo B4 niepushowany; Olga pushnęła.)
- **`certs_selfcheck`: 6/6 ×2.** `r01/proofs/`+`shield.py` NIETKNIĘTE (SR-G1). **Sędzia niezmieniony:
  `sha256(act_judge.py)=79b1e936…`** (SR-G4 spełniony — sędzia nie ruszany).
- **Zero prób dowodowych** (SR-G3: A1 sanity-live jest warunkiem prób A1; nie przeszła → brak prób).
  **Zero biegów A2** (bramka sanity nieosiągnięta). **Zero zmian spec/świata/sędziego/percepcji.**

## Co ZBUDOWANE (infrastruktura LIVE, gotowa)

- `acts/run_act_live.sh` — launcher LIVE: boot świata aktu, bridge kamery MONO drona → `detector_node`
  (YOLO), scenariusz `gate_run_r02` **BEZ GT_FED** (kanał z detektora przez ChannelSub), token path B1,
  manifest PRZED scenariuszem (§2/SR-G2). Kamera filmowa za flagą `FILM_CAPTURE` (domyślnie 0 — diagnoza).
- `r02/gate_run_r02.py` — wątek teleportu aktora ustawia `_intr_ned` także w trybie LIVE (poza aktora
  jest znaną GT choreografii — sterujemy nim; NIE roszczenie percepcji), by sędzia mógł liczyć geometrię
  ENTRY-in-ring w LIVE. Additive, kryte 76 testami deterministycznymi (regresja PASS).

## §1 — Sanity-live A1: CZTERY niepowodzenia boot/health (nie-próby, §0)

Wszystkie **przed emisją decyzji scenariusza** (crash na `bring_up` — nie-próba wg §0), zachowane w
`results/demo/rehearsal/A1/rehearsal_live_envfail{1..4}/` (logi; frame'y usunięte/gitignore):

| # | konfiguracja | wynik `bring_up` | gyro-err (px4) |
|---|---|---|---|
| 1 | detektor podczas settle, film+mono bridge | `BRAK health` | 1 |
| 2 | jw. | `BRAK health` | **0** |
| 3 | detektor PO settle (fix #1), film+mono bridge | `BRAK health` | 12 |
| 4 | mono-only (film OFF, fix #2), detektor po settle | `BRAK health` | 1 |

**Mechanizm:** `Mav.wait_ready(30)` (MAVSDK `telemetry.health()`, udpin PX4) NIE osiąga gotowości —
EKF/nav-health nie zbiega w oknie. `Preflight Fail: No connection to the ground control station`.

**Hipotezy TESTOWANE i NIEPOTWIERDZONE (dlatego SR-G6, nie ślepe retry):**
1. *Przeciążenie 2 kamer (mono+film) renderem* → OBALONE: mono-only (#4) też fail; gyro czyste.
2. *Ładowanie YOLO w trakcie settle* → OBALONE: detektor po settle (#3, #4) też fail.
3. *Glitch gyro/IMU* → OBALONE: #2 miał **0** błędów gyro i mimo to `BRAK health`.
Wniosek: przyczyna = **niezbieżność EKF/nav-health w boocie LIVE**, niepryzpisana jednoznacznie;
najbardziej spójna z **udokumentowanym intermittentnym arm-fail tego projektu pod kontencją**
(ANEKS-H/E2, High Gyro Bias), możliwie zaostrzonym obciążeniem toru LIVE (bridge mono + detektor).

**Dowód, że maszyneria działa:** B4 GT-fed (A1/A2), A3 (gate_run_r03) i REGATE (mono+YOLO live) armowały
CZYSTO na tej samej maszynerii — problem jest specyficzny dla tej serii bootów LIVE, nie dla kodu.

## SR-G6 — decyzja STOP

Cztery niepowodzenia środowiska, przyczyna niedomknięta mimo dwóch fixów diagnostycznych → **STOP**
(reguła „nie brnąć"). Dalsze booty „na oślep" naruszałyby ducha SR-G6. **Nie luzowano progów,
choreografii, spec ani sędziego.** Decyzja co dalej należy do Olgi.

## Propozycje domknięcia (do ratyfikacji Olgi — poza tą sesją)

1. **Hartowanie bootu (harness):** przed scenariuszem — twarda pre-bramka „EKF/nav-health gotowe"
   (poll `telemetry.health()` z dłuższym oknem / adaptacyjnie) ZANIM `bring_up`; retry bootu wg §0
   (nie-próba). Bez zmian spec/świata/sędziego.
2. **Kontencja środowiska:** zapewnić brak równoległych obciążeń (fabryka) w oknie prób — czysty GPU/CPU
   był na starcie, ale intermittent może wracać; ewentualnie sekwencjonować bridge/detektor.
3. **Wideo filmowe LIVE:** jeśli boot ustabilizowany, `FILM_CAPTURE=1`; jeśli 2-kamerowy render okaże
   się dodatkowo obciążać — osobne przejście na wideo albo obniżenie `update_rate` kamery filmowej
   (ZMIANA ŚWIATA → nowy hash + adnotacja ANEKS_D2, SR-F4/G4 — wymaga ratyfikacji).
4. **A2 (bramka sanity) i próby** — dopiero po stabilnym boocie LIVE.

## STOP

B5 nieukończony: infrastruktura LIVE zbudowana i gotowa; sanity-live A1 zablokowane 4× niepowodzeniem
boot/health (SR-G6). Sędzia zamrożony niezmieniony (79b1e936…), `r01` nietknięte, selfcheck 6/6 ×2,
76 testów regresji PASS. **Wznowienie B5 = po ratyfikacji przez Olgę ścieżki hartowania bootu
(propozycje wyżej). Push = Olga.**
