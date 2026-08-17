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

---

## AKTUALIZACJA (sesja 2, 2026-08-17) — po pushu B5-STOP przez Olgę, re-send PROMPT_D_BUILD_5

SR-G5 spełniony (Olga pushnęła commity B5-STOP). Podjęto próbę odblokowania sanity-live A1 z fixami
harness/runner (bez zmian frozen: spec/świat/sędzia/percepcja/r01 NIETKNIĘTE; sędzia 79b1e936…).

### Fix 1 (KOREKTA §0/§2, WAŻNA i ZACHOWANA): manifest emitowany PO bring_up
Poprzednio manifest szedł PRZED `bring_up` → crash bootu/health był „PO manifeście" = **próba** (§0),
błędnie zżerając budżet ≤3. §0 jasno intencjonuje env boot-fail = **nie-próba**. Naprawione:
`gate_run_r02._emit_act_manifest` wołany PO `bring_up` (po arm; pole `armed_before_manifest`).
Weryfikacja: envfail5/6 **NIE mają manifestu** = poprawnie nie-próby; envfail1–4 (stary porządek) miały
manifest = były błędnie klasyfikowane. **Wszystkie 6 to env boot-fail (dron NIGDY nie uzbrojony) —
licznik prób A1 = 0** (żadna choreografia nigdy nie ruszyła).

### Fix 2 (diagnostyczny): tor LIVE (bridge+detektor) startuje PO arm; settle całkowicie czysty
`_start_live_detector` startuje mono-bridge+detector_node dopiero po `bring_up` (wzorzec REGATE:
arm ZANIM YOLO). Settle 210 s bez żadnego obciążenia LIVE.

### Wynik: 2 kolejne env-fail (razem 6) — przyczyna NADAL niedomknięta
| # | konfiguracja bring_up | wynik | EKF |
|---|---|---|---|
| 5 | czysty settle 210 s, bridge/detektor po arm | `BRAK health` | home set, gyro 1, brak nav-fail |
| 6 | jw. (detektor NIGDY nie wystartował — fail przed nim) | `BRAK health` | jw. |

**OBALONE hipotezy (łącznie):** 2-kamery-render, YOLO-w-settle, gyro-glitch, obciążenie-detektora-przy-arm,
długość-settle. **EKF ZDROWY** (home set, gyro czyste, zero nav-fail). Blokada = `telemetry.health()`
MAVSDK nigdy gotowe / `No connection to GCS` — **łącze MAVSDK↔PX4 nie ustanawia się w torze
`run_act_live.sh` (GT_FED=0)**, podczas gdy **B4 GT-fed (`run_act.sh`) armował NIEZAWODNIE przy
CIĘŻSZYM środowisku bring_up (aktywny film-bridge)**. Różnica środowiska bootu między
`run_act.sh`(działa) a `run_act_live.sh`(fail) nie znaleziona w artefaktach; A3 (`run_A3.sh`, PX4_GZ_WORLD
w run_stack) też armował. Najbardziej spójne z **intermittent arm-fail projektu** (dokum. ANEKS-H/E2),
lecz 6/6 fail w LIVE vs niezawodny arm GT-fed sugeruje różnicę systematyczną NIEZIDENTYFIKOWANĄ.

### SR-G6 — STOP DEFINITYWNY
Sześć env-fail, cztery celowane fixy, przyczyna niepinowalna z artefaktów → **STOP** („nie brnąć").
**Zero prób dowodowych, zero A2, zero zmian frozen, sędzia 79b1e936… niezmieniony, r01 nietknięte,
selfcheck 6/6 ×2.** Fix manifest-po-arm ZACHOWANY (poprawność §0). Rekomendacja dla Olgi (poza sesją):
1. **Debug łącza MAVSDK/GCS** w torze LIVE: diff sekwencji bootu `run_act.sh`(działa) vs `run_act_live.sh`
   linia-po-linii; sprawdzić bind portu 14540 / kolejność mavlink onboard; ewentualnie boot-retry pętla
   (każdy nie-próba §0) do pierwszego zdrowego bootu.
2. Alternatywa architektury: arm w-procesie stylem `mti_flight` (dowiedziony live w REGATE) zamiast
   `gate_run_r02.bring_up` + osobny detektor.
3. Zapewnić brak kontencji (fabryka) w oknie prób.

---

## AKTUALIZACJA-3 (sesja 3, PROMPT_D_BUILD_5R2) — rdzeń mti_flight: topologia FALSYFIKOWANA → opcja 1

Wznowienie rdzeniem `mti_flight` (ANEKS_D4). Zbudowano `acts/live_stability_probe.py` (sterowanie
połączeniem/arm/offboard **1:1 z mti_flight**: raw `System()` udpin 14540, health 90 s [global+home],
arm-retry 60×, takeoff, offboard, hover, land) + `acts/run_stability.sh` (habitat aktu world_demo_A1
+ mono bridge, jak mti_run.sh; higiena env ANEKS_D4 c). T1 seria bootów stabilności:

| boot | MAVSDK connect | health (global+home) 90 s | arm | verdict |
|---|---|---|---|---|
| 1 | **TAK @ 0.91 s** | **TIMEOUT @ 90 s** | nie | FAIL |
| 2 | **TAK** | **TIMEOUT @ 90 s** | nie | FAIL |

### Wynik: topologia mti_flight NIE jest naprawą (fallback T1)
- **Łącze MAVSDK USTANAWIA SIĘ** (connect @0.91 s, 2/2) — więc problem to NIE połączenie/topologia.
  Fallback „nie ustanowi łącza w ≤2 bootach" ściśle nie zaszedł, ALE cel (zdrowy/uzbrajalny boot)
  nieosiągnięty 2/2 → hipoteza „to topologia" **FALSYFIKOWANA**.
- **Blokada = `telemetry.health()` nie zbiega** (global+home OK nigdy w 90 s), przy **ZDROWYM EKF/GPS**
  (px4.log: zero błędów GPS/EKF/fusion, `vehicle_gps_position` publikowane; jedyny Preflight Fail =
  „No connection to GCS").
- **DOWÓD KLUCZOWY:** B4 GT-fed (armed, ten sam świat world_demo_A1) miał **TĘ SAMĄ** warning
  „No connection to GCS" (×2) a mimo to osiągnął „Ready for takeoff" → armed. Warning jest
  **przejściowy/nieblokujący**; różnica = czy `telemetry.health()` dostarcza zdrowy komunikat
  (B4 dostaje, tor LIVE/stability nie), NIEZALEŻNIE od topologii MAVSDK (obie: raw System / exec_lib.Mav).
- **LEAD dla opcji 1:** zaobserwowano **zalegający `mavsdk_server` na udpin 14540** po biegach.
  `System()` (mavsdk py) auto-spawnuje mavsdk_server; stary związany z 14540 → nowy klient łączy się do
  MARTWEGO serwera → brak telemetrii z bieżącego PX4 → health timeout. Teardown kill mavsdk_server ISTNIEJE
  (run_stability + mti_run), ale zaleganie obserwowane → wyścig/hygiena portu 14540 = pierwszy podejrzany.

### SR-G6/H — STOP → opcja 1 (osobny prompt, SR-H3 nie mieszać ścieżek)
Topologia mti_flight nie odblokowała bootu (2/2 health-timeout) → **STOP**. Rekomendacja **opcja 1**:
diff sekwencji bootu `run_act.sh`(DZIAŁA, GT-fed) vs `run_act_live.sh`/`run_stability.sh`(FAIL) linia-po-linii,
ze szczególnym sprawdzeniem: **(i) higiena mavsdk_server / bind 14540** (jawny kill+wait przed startem;
zweryfikować brak stale servera); (ii) kolejność mavlink onboard vs klient; (iii) param COM_* datalink/GCS.
**Zero prób, zero A2, sędzia 79b1e936 niezmieniony, r01 nietknięte, selfcheck 6/6 ×2.** Zbudowana sonda
+ launcher stabilności ZOSTAJĄ (narzędzie diagnostyczne dla opcji 1).

---

## AKTUALIZACJA-4 (sesja 4, PROMPT_D_BUILD_5R3) — PRZYCZYNA ŹRÓDŁOWA ZNALEZIONA I NAPRAWIONA

Drzewo decyzyjne opcji 1 (V0→D1→D2→D3) doprowadziło do **przyczyny źródłowej całej sagi B5**.

### V0 — higiena: boot startował czysto
`ss -ulpn`/`pgrep` przed bootem: porty 14540/50051 WOLNE, brak stale procs. `pkill -f mavsdk_server`
łapie serwer. Boot 5R2 był naprawdę czysty. (hygiene_pre.txt)

### D1 — lead zombie-serwera OBALONY
Jawny cykl życia serwera (spawn `mavsdk_server` explicite, klient `System(mavsdk_server_address=…)`
bez auto-spawnu, `ss` weryfikacja): serwer **odkrył PX4** ("System discovered") ale health **nadal
TIMEOUT @90 s**. Zombie-serwer nie był przyczyną.

### D2 — LOKALIZACJA segmentu (instrumentacja strumienia health)
Log pól health per komunikat: **`gpos=False home=True lpos=True armable=False`**, komunikaty health
DOCHODZĄ (telemetria płynie). Segment = **`is_global_position_ok` (EKF/GPS global) nigdy True**, NIE
serwer/mavlink/klient. **Kontrola tor DZIAŁAJĄCY:** `run_act.sh` A1 **GT-fed** (config który armował w B4)
uruchomiony PONOWNIE → **TEŻ `BRAK health`**. ⇒ awaria **NIE jest LIVE-specyficzna, NIE launcher/topologia**
— dotyczy KAŻDEGO toru. Środowisko idle (load 1.36, GPU 0%, brak fabryki) ⇒ nie kontencja.

### PRZYCZYNA ŹRÓDŁOWA: leftover `EKF2_GPS_CTRL=0` w persystowanym `parameters.bson`
Testy **A3 (gate_run_r03, GPS-denied)** ustawiają `EKF2_GPS_CTRL=0` (wyłącz GPS). Wartość **PERSYSTUJE
w PX4 SITL `rootfs/parameters.bson`** między bootami; zostawiona na 0 (restore nie zapisał się / teardown
-9 przed save) ⇒ EKF bez GPS ⇒ `is_global_position_ok` nigdy True ⇒ health timeout ⇒ arm-fail.
**B4 armował ZANIM parametr utknął na 0.** Weryfikacja bson: `\x10EKF2_GPS_CTRL\x00` + int32 = **0**.

**WSZYSTKIE wcześniejsze „przyczyny" (6 env-fail sesja1/2, topologia mti_flight sesja3, „No connection
to GCS") były POCHODNĄ tego jednego parametru.** „No connection to GCS" = warning przejściowy (był też
w B4 armującym) — nigdy nie był blokadą.

### D3 — FIX minimalną deltą + WERYFIKACJA
Reset `EKF2_GPS_CTRL 0→7` (default, GPS ON) w bson (surgical, backup). Boot weryfikacyjny sondą stabilności:
**`gpos=True home=True lpos=True armable=True`; health OK @ 0.52 s; armed (attempts=1); takeoff alt 7.5;
hover 10 s OK; land; VERDICT OK.** (results/demo/stability/d3_verify/boot_1/)

**FIX (harness, poza frozen):** `acts/ensure_gps_enabled.py` — reset EKF2_GPS_CTRL→7 w bson PRZED każdym
bootem LIVE; wpięte do `run_act_live.sh` + `run_stability.sh` (po teardown). Zero zmian frozen
(świat/spec/sędzia/r01/kamera). Historyczne komentarze w launcherach (obciążenie/detektor jako „przyczyna")
SUPERSEDED — właściwa przyczyna = parametr GPS.

### T1 — bramka stabilności 3/3 ZALICZONA (po fixie GPS)
Seria 3 czystych bootów LIVE (`run_stability.sh`, higiena GPS aktywna): boot_1/2/3 = **VERDICT OK**
(health @ 0.56/0.55/0.40 s, armed attempts=1, takeoff+hover 10 s+land). Fix DETERMINISTYCZNY potwierdzony.
**T1 ⇒ odblokowane T2** (PROMPT_D_BUILD_5 §1–§3: sanity A1 → bramka A2 EXPIRE → próby A1→A3→A2).

### T2 §1 — A1 sanity-live: BOOT/ARM/PIPELINE DZIAŁA end-to-end; ENTRY live NIE pada (percepcja)
Pełny tor LIVE (higiena GPS → boot → **arm** → manifest-po-arm `armed_before_manifest=true` → detektor
YOLO LIVE po arm → choreografia): **dron ARMOWAŁ** (fix GPS działa w pełnym torze LIVE, zero „BRAK health"),
intruz teleportowany do pierścienia (intr_ned parking→ring), detektor załadowany i publikuje @1 Hz. ALE
`n_entry=0` (528 ticków PATROL, locked=0) — **detektor YOLO nie zablokował intruza** w world_demo_A1.
Sanity §1 informacyjne (percepcja NIERAPORTOWALNA) — jego cel (potwierdzenie że ENV/boot naprawiony)
OSIĄGNIĘTY. **Luka percepcji live (YOLO nie lockuje w world_demo_A1 vs REGATE world_demo_v1) = OSOBNA
sprawa, POZA zakresem 5R3** (który był „diagnoza+fix launchera"). Wymaga własnego promptu (dlaczego live
detekcja nie pada tu vs REGATE: geometria/kadr mono/koperta/próg — spec i światy zamrożone, ścieżka STOP→
adnotacja→ratyfikacja jeśli trzeba).

## PODSUMOWANIE 5R3: PRZYCZYNA ŹRÓDŁOWA NAPRAWIONA, BOOT ODBLOKOWANY
- **Znaleziona i naprawiona przyczyna 4-sesyjnej blokady:** leftover `EKF2_GPS_CTRL=0` (po A3 GPS-denied)
  w persystowanym `parameters.bson` → GPS off → `is_global_position_ok` False → health timeout → arm-fail.
- **Fix (harness):** `acts/ensure_gps_enabled.py` (reset →7 przed bootem) w `run_act_live.sh`+`run_stability.sh`.
- **Zweryfikowane:** T1 3/3 czyste booty (health 0.4–0.56 s) + A1 sanity dron armuje end-to-end.
- **Kontrakty frozen nietknięte** (świat/spec/sędzia 79b1e936/r01), selfcheck 6/6.
- **NASTĘPNE:** luka percepcji live (osobny prompt) → potem T2 próby A1→A3→A2.

---

## AKTUALIZACJA-5 (sesja 5, PROMPT_D_BUILD_5P) — luka percepcji live ZDIAGNOZOWANA → ANEKS_D5 (ratyfikacja)

### H0 — higiena prowieniencji GPS
Manifest per bieg dostaje `ekf2_gps_ctrl_bson` (echo stanu z persystowanego bson — cicha regresja
`ensure_gps_enabled` widoczna w prowieniencji 1. biegu). Oś czasu przyczyny SPÓJNA: B4 A1/A2/A3 armowały;
A3 (ostatni w B4) ustawił `EKF2_GPS_CTRL=0` → wszystkie kolejne booty (env-fail1..6, sesje 1–3) padały —
„B4 armował ZANIM param utknął na 0" potwierdzone.

### P0 — diagnoza (sonda DBG `probe_dbg_1`; SR-J2 probe, NIE próba)
Trace sanity-live A1: `conj=None` przez cały ring (485/485) — **architektura LIVE: kanał+conj żyją w
OSOBNYM procesie `detector_node`**, gate'owy patch (b) ich nie widzi; gate dostał `age=None` (kanał pusty).
Sonda DBG (`/liquidpatrol/detector_debug`): **YOLO WYKRYWA cel** (n_box>0 22/22, 16–32 boxy) ale
**`conf_top1` median 0.116 < θ_conf 0.1635** (< signal_min 0.169); `entry=0/locked=0`; kanał pusty 22×.

**Wariant rozstrzygnięty (poza czterema z promptu — to KONFIG BRAMY):** LIVE `detector_node` używa
`entry_require_mti=False` ⇒ brama `box∧central∧conf-floor`; intruz borderline-conf ODRZUCONY. **REGATE
(charakteryzacja) używał `entry_require_mti=True` — brama `box∧central∧MTI`, conf PASYWNE** — ten sam cel
lockuje. `detector_node` NIE liczy MTI → spada na conf-floor → rozjazd z charakteryzacją. **NIE oscylacja
(P3 nie dotyczy — LIVE nie używa MTI), NIE wiring (kanał dociera pusty), NIE geometria (YOLO widzi).**

### FIX = ścieżka ANEKS_D5 (SR-J1: percepcja) → STOP na ratyfikacji Olgi
Propozycja (ANEKS_D5, NIE zastosowana): przywrócić w torze LIVE scharakteryzowaną bramę `box∧central∧MTI`
(port MTITracker `mti_flight`→`detector_node` + `entry_require_mti=True`; ZERO zmiany progów — charakteryzacja
frozen; zmienia się tylko aktywna brama conf-floor→MTI). Po ratyfikacji: implementacja → nowy hash detektora
→ re-sanity → bramka A2 → próby A1→A3→A2.

**Kryterium śmierci NIE osiągnięte** (koniunkt zidentyfikowany: MTI-nieobecność w LIVE; fix istnieje ale
percepcja ⇒ ratyfikacja). **STOP.** Sędzia `79b1e936` niezmieniony, spec/światy/progi/`r01` NIETKNIĘTE,
selfcheck 6/6. Narzędzia `dbg_logger.py`/`live_stability_probe.py` ZOSTAJĄ.

---

## AKTUALIZACJA-6 (sesja 5-cd, PROMPT_D_BUILD_5P re-send = ratyfikacja ANEKS_D5) — brama MTI + P3

**ANEKS_D5 ratyfikowane (re-send).** Implementacja bramy `struktura∧MTI` w torze LIVE (`detector_node`
`DEMO_MTI=1`, MTI przy 15 Hz `_on_image`, `entry_require_mti=True`, zero zmiany progów). Re-sanity:
brama MTI aktywna ale `mti_ok=0` przy oscylacji spec **±1.0** (n_comps≈0-2). **Sonda P3 (`OSC_OVERRIDE=1.5`,
SR-J2): mti_ok=1/entry=1/detektor-locked=1** → **P3 POTWIERDZONY: ±1.0 za mała, ±1.5 (charakteryzacja)
budzi MTI**. FIX = powrót spec ±1.5 (korekta rozbieżności B2) = **ANEKS_D5 propozycja druga → STOP na
ratyfikacji** (SR-J1 spec frozen). Po ratyfikacji: spec ±1.5 → nowy hash A1/A2 → re-sanity → bramka A2 →
próby A1→A3→A2. Sędzia `79b1e936` niezmieniony, progi/światy/`r01` nietknięte, selfcheck 6/6, regresja 37.
