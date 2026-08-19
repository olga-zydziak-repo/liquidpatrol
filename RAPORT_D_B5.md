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

---

## AKTUALIZACJA-7 (PROMPT_D_BUILD_5F — ratyfikacja ANEKS_D5 pełnym tekstem) — §2 ROZBIEŻNOŚĆ KADENCJI DECYZJI → STOP

**§1 wykonane (ratyfikowane):** ANEKS_D5 pełny tekst wpisany; echo `demo_mti` w manifeście
(`build_manifest`+`_emit_act_manifest`, klasa A4/token_gated, SR-K1); spec `intruder_lateral_osc_m`
1.0→1.5 A1/A2 (nowe hashe A1=`48a50c8d`, A2=`02441d93`); sonda `OSC_OVERRIDE` usunięta (trajektoria =
czysta f(spec)). Judge intakt `79b1e936`, progi/tracker/światy/`r01` nietknięte, regresja 80 passed,
selfcheck 6/6. Commit `ec3b70f`.

**§3.1 re-sanity A1 (informacyjne, SR-J2) — n_entry=0 mimo ±1.5.** Boot ZDROWY (manifest:
`demo_mti=true`, `armed_before_manifest=true`, `ekf2_gps_ctrl_bson=absent(default 7)`,
spec_hash=48a50c8d, judge 79b1e936). YOLO widzi cel (n_box>0 na 43/43 klatkach), conf pasywne
(max 0.10 — MTI jest bramą, nie conf). **`mti_ok=1` tylko 6/43 sporadycznie, NIGDY 3 pod rząd →
k=3 nie domyka → brak locka/ENTRY.**

**§2 ROZBIEŻNOŚĆ Z CHARAKTERYZACJĄ (obowiązkowy STOP, §2 „każda różnica ⇒ STOP"):** kadencja
tiku DECYZYJNEGO (akumulacja ENTRY k=3) ≠ REGATE.
- REGATE (`results/R02/mti/mti_flight.py`): **`DECISION_HZ=2.0`** (L41; L321 `period=1/DECISION_HZ`)
  → `on_frame` @2 Hz → **k=3 = 1.5 s**. `cov_entry_once=1.0` mierzone przy 2 Hz.
- tor aktu (`detector_node._on_tick`): **`DET_HZ=1.0`** (`config_r02` L22) → `on_frame` @1 Hz →
  **k=3 = 3.0 s**. (MTI-push zgadza się: 15 Hz w obu.)
- Mechanizm: rezyduum derotacji MTI zeruje się w punktach zwrotnych oscylacji (prędkość względna=0
  2×/okres → migotanie @~0.6 Hz). Okno **3 s @1 Hz** zawsze przecina zero-crossing; **1.5 s @2 Hz**
  mieści się w jednej fazie ruchu. Stąd 1 Hz = ENTRY LOSOWE (P3 sonda złapała przez zbieg faz;
  re-sanity nie) — tor prób wymaga determinizmu, którego 2 Hz REGATE dawał, a 1 Hz nie.

**Fix (do ratyfikacji dokumentem, SR-K2/K3 — poza §1.1):** wyrównać kadencję decyzji toru LIVE do
`DECISION_HZ=2.0` == REGATE (restauracja charakteryzacji, ta sama klasa co §1.1). Miejsce najmniejszej
delty: `_start_live_detector` startuje `detector_node` bez `--det-hz` → dopisać `--det-hz 2.0`
(parametr harnessu; **`DET_HZ` w `config_r02` NIETKNIĘTY** — 1 Hz zostaje domyślną charakteryzacją R0.2,
2 Hz to wartość MTI-REGATE dla demo). Progi (k=3, θ_conf, θ_age, MTI_CENTER_THR) BEZ ZMIAN.
**STOP — decyzja wraca dokumentem.** Po ratyfikacji: re-sanity A1 (lock+ENTRY w [23,33.87]) → bramka
A2 EXPIRE → próby A1→A3→A2. Push = Olga.

---

## AKTUALIZACJA-8 / §FINAL (PROMPT_D_FINAL — ratyfikacja ANEKS_D5 §4) — RE-SANITY A1 @2 Hz OBALA PREMISĘ §4a → STOP (SR-8)

Data: 2026-08-18. **Werdykt sesji: TWARDY STOP przed bramką A2 i przed próbami.** Ratyfikowane §4a/§4b
wykonane i zweryfikowane, ale **informacyjne re-sanity A1 @2 Hz falsyfikuje premisę §4a** (2 Hz ⇒
determinizm ⇒ ENTRY w oknie): `n_entry=0` w 2/2 biegach. **Przyczyna źródłowa ZNALEZIONA i różna od
kadencji decyzji**; fix wymaga dotknięcia choreografii (teleport intruza) ⇒ ratyfikacja Olgi (SR-8).

### Stan wejściowy / higiena
- **§0 brama (0):** na starcie `origin/master..HEAD` = `6b395be` (niepushowany §4a/§4b) ⇒ STOP zgłoszony;
  Olga **pushnęła `6b395be`** (`origin/master==HEAD==6b395be`), brama czysta, wznowiono.
- **`certs_selfcheck` 6/6 ×2** (start i koniec). `r01/proofs/`+`shield.py` NIETKNIĘTE (SR-1).
  **Sędzia `tools/act_judge.py` sha256=`79b1e9367b85bf7c…` NIETKNIĘTY** (SR-6). Progi/tracker/percepcja/
  spec/światy — nie ruszane. **Zero prób dowodowych, zero biegów A2** (bramka ENTRY nieosiągnięta).

### §2.1 — Inwentarz 4b: ZGODNE + θ_age zweryfikowane u źródła (PRZED bramką A2, §4b)
- `acts/inventory_4b.py` re-run w env ROS = **bit-w-bit identyczny** z zacommitowanym
  `results/demo/inventory_4b.json`; **`diffs: []`, WERDYKT ZGODNE**. §4a wiring potwierdzony w
  ścieżce LIVE: `DEMO_DECISION_HZ=2.0` (`gate_run_r02.py:40`) → `--det-hz` (`:993`) → echo `det_hz`
  w manifeście (`:1024`); **`DET_HZ=1.0` w `config_r02.py:22` NIETKNIĘTY** (osobna kadencja klatek R0.2).
- **θ_age = 3.0 SEKUNDY, EWALUACJA CZASOWA (sim-time), NIE tiki** — zweryfikowane u źródła:
  `target_channel.py:162/186/194` `age=(t−t_last_det)+l_deliver`, `t`=sim-time (docstring `:182`);
  dodatkowo `tick_time`@20 Hz osłony (`:196–202`), też czasowe. **⇒ zmiana 1→2 Hz NIE dotyka semantyki
  EXPIRE w A2** (gdyby age był tikowy, 1 Hz połowiłby starzenie). §4b θ_age werdykt: kalibracja EXPIRE
  zachowana.
- **§4c rekonsyliacja P3:** sonda P3 `entry=1` przy ±1.5 @1 Hz = trafienie LOSOWEJ FAZY (okno 3 s @1 Hz
  między zerami rezyduum); re-sanity determinsytyczne @1 Hz nie trafiało. **Nie sprzeczność** — sonda była
  jednostrzałowa, re-sanity uśrednia. (Uwaga: @2 Hz — patrz niżej — problem NIE jest już fazą, lecz
  brakiem sygnału MTI w ogóle podczas oscylacji.)

### §2.2 — Re-sanity A1 @2 Hz: n_entry=0 (2/2), premisa §4a OBALONA
Dwa biegi LIVE (pełna brama struktura∧MTI, `DEMO_MTI=1`, boot zdrowy, GPS ON, headless):
`results/demo/A1/resanity_2hz_s6/` i `…/resanity_2hz_dbg_s6/` (drugi z sondą DBG, SR-J2 probe).
- **Manifest (oba): echa POPRAWNE** — `det_hz=2.0`, `demo_mti=true`, `token_gated=true`,
  `armed_before_manifest=true`, `ekf2_gps_ctrl_bson=absent(default 7)`, `contention=none`,
  judge `79b1e936…`, HEAD `6b395be`. Detektor LIVE `pub … @ 2.0 Hz` (log). Boot zdrowy, R3 stall p95=1.01
  ticka (pętla OK).
- **Wynik: `n_entry=0`, `granted=false`, ZERO ticków `locked=true`** w OBU biegach. YOLO widzi cel
  (n_box 14–29/tick, 87/87 ticków), **conf PASYWNE i niskie** (max 0.086–0.192) — MTI jest bramą.
- **Detektor: dokładnie 1 ENTRY na bieg, POZA oknem.** Mapowanie (kotwica: pierwszy tick trace
  `k=0 @ t=9.212` = start pętli choreografii = tuż po starcie detektora; wall detektora `763.138`):
  `wall ≈ runner_t + 753.9`. Okno ring-hold `runner_t[23,49]≈wall[776.9,802.9]`; **jedyny ENTRY @
  wall 809.6 = runner_t≈55.7 — ~1.7 s PO zamknięciu pętli (hold+5=54), w RTL**; box `cy≈0.80/0.81`
  (nisko w kadrze = NIE intruz pierścienia, który jest wysoko: alt+1.5).

### PRZYCZYNA ŹRÓDŁOWA (różna od kadencji decyzji): KADENCJA RUCHU intruza 2 Hz ≪ REGATE ~16.7 Hz
Porównanie 1:1 z frozen charakteryzacją:
- **REGATE `results/R02/mti/mti_flight.py:189` `replacer()`: `time.sleep(0.06)` → ~16.7 Hz** teleport
  (per-klatkę, ~kadencja kamery 15 Hz). Oscylacja `1.5·sin(2π·0.3·t)` aplikowana PŁYNNIE → ruch względny
  na KAŻDEJ klatce → komponenty MTI trwałe → `cov_entry_once=1.0` (REGATE world_demo_v1.1).
- **Tor aktów `gate_run_r02.py:966` `_telethread()`: `time.sleep(0.5)` → 2 Hz** teleport. Ta sama
  oscylacja SAMPLOWANA co 0.5 s → intruz STATYCZNY ~7 z ~7.5 klatek między skokami. Kamera 15 Hz.
- **Mechanizm (dlaczego to zabija MTI, nie tylko „aliasuje"):** MTI = różnicowanie klatek + filtr
  TRWAŁOŚCI `persist_m=3 / persist_window=4` (komponent w ≥3 z 4 ostatnich klatek). Ruch skokowy 2 Hz
  daje motion w 1–2 izolowanych klatkach na skok → **filtr trwałości ODRZUCA** → `n_comps=0`. Tylko ruch
  CIĄGŁY (REGATE per-klatkę; albo w torze aktów — duży zjazd park-transition na końcu) daje trwałe
  komponenty.
- **Dowód empiryczny (DBG, `resanity_2hz_dbg_s6/dbg.jsonl`, 87 ticków):**
  - **W OKNIE pierścienia (dbg-t 23–51, 56 ticków): `mti_ok=1` = 0/56, `n_comps` sporadyczne 0–2
    (max 2), ENTRY=0, lock=0.** MTI NIGDY nie przeszło bramy podczas oscylacji ±1.5.
  - **POZA oknem (dbg-t 52–58, duży park-transition + RTL): `n_comps` skok do 39, `mti_ok=1` ×7,
    k=3 domyka → 1 ENTRY (dbg-t 57.5, cy≈0.81).** To jedyny lock — post-window, nieistotny dla aktu.
  - Globalnie `mti_ok=1` 7/87 (8%), `n_comps=0` 69/87 (79%), max consecutive `mti_ok`=5 (wszystkie
    w post-window transicie).
- **Wniosek:** §4a (`det_hz` 1→2) celował w kadencję DECYZJI; realny bloker to kadencja RUCHU intruza
  (wejście MTI). Przy 2 Hz teleporcie 15-Hz-owy sygnał MTI jest z natury sporadyczny → żadna kadencja
  decyzji tego nie naprawi. Premisa §4a (2 Hz ⇒ determinizm ⇒ ENTRY) **obalona pomiarem, 2/2**.

### ZNALEZISKO WTÓRNE: inwentarz §4b był NIEZUPEŁNY (pominął kadencję ruchu intruza)
§4b miał złapać KAŻDY parametr tikowy rozjeżdżający się z REGATE. Zinwentaryzował kadencje
decyzji/MTI-push/kanału/klatki (wszystkie równe) ale **NIE ujął kadencji drive'u intruza** (teleport
0.5 s tor aktów vs 0.06 s REGATE — różnica ~8×). Dlatego werdykt „ZGODNE zero różnic" był prawdziwy w
swoim zakresie, a mimo to zachowanie się rozjeżdża. **To jest ta różnica, której §4b szukał — poza
swoją tablicą.** (Uczciwość prowieniencji: tablica inwentarza pozostaje poprawna dla swoich wierszy;
brakowało wiersza `intruder_teleport_hz`.)

### KONSEKWENCJA: bramka A2 i próby ZABLOKOWANE tą samą przyczyną
Bramka A2 EXPIRE (§2.3) wymaga NAJPIERW locka ep0 (ENTRY), by było co EXPIROWAĆ; próby A1/A2 (§2.4)
wymagają ENTRY w oknie. Bez in-window ENTRY — **cały tor dowodowy zablokowany**. Uruchamianie prób
byłoby brnięciem w znany bloker (3× INVALID gwarantowane) — sprzeczne z „nie brnąć" i FAIL=FAIL.
**Zero prób. Zero biegów A2.**

### STOP + PROPOZYCJA DO RATYFIKACJI (SR-8 — NIE zaimplementowana)
Fix minimalną deltą, klasa „restauracja charakteryzacji" jak §4a: **wyrównać kadencję teleportu intruza
toru aktów do REGATE** — `gate_run_r02.py:966` `time.sleep(0.5)` → `time.sleep(0.06)` (== `mti_flight.py:189`).
- **Co NIE ruszane:** progi (k=3, θ_conf, θ_age, MTI_CENTER_THR, persist_*), tracker, percepcja
  (`detector_node`), spec (hashe A1/A2), światy, sędzia `79b1e936`, `r01`. Oscylacja pozostaje
  `1.5·sin(2π·0.3·t)` — zmienia się WYŁĄCZNIE gęstość jej próbkowania w teleportcie (choreografia
  runnera, nie SDF, nie spec).
- **Ryzyka do sprawdzenia po ratyfikacji:** (a) `gz set_pose` @~16.7 Hz — REGATE to robi (`sleep(0.06)`),
  więc wykonalne, ale zmierzyć obciążenie/latencję usługi gz przy jednoczesnym bridge+YOLO (kontencja);
  (b) czy `intr_ned` w trace (2 Hz→~16.7 Hz zapis) nie puchnie — logować rozsądnie; (c) re-weryfikacja
  §4b z DOPISANYM wierszem `intruder_teleport_hz` (REGATE 16.7 / akt 16.7).
- **Alternatywa (gdyby set_pose @16.7 Hz był zbyt kosztowny):** ruch ciągły przez interpolację pozy w
  gz (plugin/velocity) zamiast dyskretnego set_pose — większa przebudowa, mniej preferowana.
- **Po ratyfikacji:** re-sanity A1 (lock+ENTRY w [23,33.87]) → bramka A2 EXPIRE → próby A1→A3→A2.

### Prowieniencja / artefakty tej sesji
- `results/demo/A1/resanity_2hz_s6/` (bieg 1) i `resanity_2hz_dbg_s6/` (bieg 2 + DBG) — manifesty, trace v2,
  detector.log, dbg.jsonl; `frames/` gitignore. **NIE-próby** (re-sanity informacyjne, SR-J2 probe) —
  werdykt percepcji nieraportowalny jako wynik aktu.
- `results/demo/A1/resanity_5F_2hz/` — bieg poprzedniej sesji PRZERWANY w settle (0 klatek, brak
  manifestu, brak werdyktu) — odnotowany jako NIE-bieg; zachowany bez interpretacji.
- **selfcheck 6/6 ×2.** Sędzia i frozen nietknięte. **Push = Olga.**

### STOP
Decyzja wraca dokumentem CC pełnym tekstem (ratyfikacja fixu teleportu albo inna dyspozycja).

---

## AKTUALIZACJA-9 / §5 (ANEKS_D5 §5 ratyf. — kadencja ruchu intruza) — 5a/5b OK, §5c RTF POZA BUDŻETEM → W3→W3'→O2 STOP

Data: 2026-08-18. Fix teleportu (§5a) i pełny sweep temporalny (§5b) wykonane i czyste, ale **twarda
bramka kosztu §5c (RTF pod pełnym obciążeniem) NIE przechodzi**: sim biegnie ~0.65× realtime.
Drzewo werdyktu (prereg ANEKS_D5 §5c/W3/W3'/O1-O3): **W3 → W3' → O2 → STOP programowy z pełnym zrzutem.**
`certs_selfcheck` 6/6 ×2, sędzia `79b1e936` i `r01` NIETKNIĘTE. **Push = Olga.**

### §5a — teleport 0.5→0.06 s (== REGATE) + echo teleport_hz — WYKONANE
`gate_run_r02.py`: `DEMO_TELEPORT_DT=0.06`, `DEMO_TELEPORT_HZ=16.7` (weryfikacja grepem: `_telethread`
sleep w L974, nie ufano numerowi); `time.sleep(0.5)→time.sleep(DEMO_TELEPORT_DT)`; echo `teleport_hz`
w `_emit_act_manifest` obok `det_hz`/`demo_mti`/`token_gated`/`ekf2_gps_ctrl` (bieg z teleport_hz≠16.7 =
INVALID). Oscylacja `1.5·sin(2π·0.3·t)` BEZ ZMIAN. Progi/tracker/percepcja/spec/hashe/światy/sędzia/r01
nietknięte. Regresja **72 passed**.

### §5b — sweep temporalny (AST, 4b-v2) — ZGODNE
`acts/temporal_sweep_5b.py` (AST, kompletność Z KODU — nie z ręcznej listy): ekstrakcja WSZYSTKICH
`sleep/create_timer` + stałych temporalnych obu torów (REGATE `mti_flight` vs akt `gate_run_r02`+
`detector_node`+`act_common`; shared `config_r02`/`target_channel`/`mti`). Rola KLUCZOWA (producent ruchu,
pominięty w §4b) = sleep GŁÓWNEJ pętli (bezpośrednie dziecko `while`, nie continue-branch trybu off/far):
**REGATE `mti_flight.py:189`=0.06 s == akt `gate_run_r02.py:974`=0.06 s**; decision 2.0==2.0. **WERDYKT:
ZGODNE — zero różnic kadencji semantycznej.** `results/demo/temporal_sweep_5b.json`.

### §5c — RTF pod PEŁNYM obciążeniem: robust Δsim/Δwall (pojedyncza subskrypcja /stats)
Sampler `gz topic -n 1` (per-próbka) był NIEWIARYGODNY — kontenduje z 16.7 Hz `gz service set_pose`
(bimodalne 0.04/1.0, n=18). Zastąpiony `scratchpad/rtf_stream.py` (JEDNA subskrypcja `/world/W/stats`,
2700+ próbek, RTF_avg = Δsim/Δwall = ODPORNE na jitter chwilowy).

- **cost_probe_5c_v2 (FILM=1, teleport 16.7Hz, bridge+YOLO): RTF_avg=0.69** (Δwall 46.4 s → Δsim 32 s =
  **14 s desync wall↔sim**); inst median 0.9997, **min 0.039, p10 0.040, frac<0.5=32%**. `n_entry=0`.
- **BUDŻET ANEKS-H = RTF~1.0** (R2 sonda: median 0.9998, min 0.978). RTF_avg 0.69 i frac<0.5=32% (stalle do
  ~4% RTF, których habitat R2 NIGDY nie miał) ⇒ **POZA BUDŻETEM → W3.** (Mediana ~1.0 = pozór; koszt to
  okresowe głębokie stalle, nie mediana.)

### W3 (read-only) — mechanizm set_pose: TRANSPORT RÓWNY → hipoteza transportu OBALONA (W3')
- REGATE `mti_flight.py:50` `gz_set_intruder`: `subprocess.run(["gz","service",…set_pose…], capture_output=True)`.
- akt `r02/intruder_driver.py` `set_pose`: `subprocess.run(["gz","service",…set_pose…], capture_output=True)`.
- **Identyczny mechanizm (subprocess-per-call), oba @16.7 Hz** (tylko `--timeout 2000` vs `3000`, bez wpływu).
  REGATE osiąga RTF~1.0 tym SAMYM mechanizmem ⇒ transport NIE jest przyczyną ⇒ **W3'**: różnicowy podejrzany
  = obciążenie NIEOBECNE w REGATE (zapis klatek/film).

### W3' — ablacja FILM_CAPTURE=0: FILM OCZYSZCZONY, budżet NIE przywrócony → O2
`ablation_nofilm_5c` (FILM_CAPTURE=0 — w `run_act_live.sh` gate'uje CAŁY podsystem filmowy: bridge L60
∧ grabber L64; potwierdzone: **brak `bridge_film.log`, 0 klatek**). Reszta identyczna (+DBG_LOG=1, obc.≈0).

| bieg | RTF_avg | median | min | frac<0.5 |
|---|---|---|---|---|
| FILM=1 (v2) | 0.689 | 1.000 | 0.039 | 32% |
| **FILM=0 (ablacja)** | **0.652** | 1.000 | 0.037 | **34%** |

**RTF praktycznie IDENTYCZNY bez filmu (0.65 vs 0.69, stalle 34% vs 32%).** Spowolnienie jest STAŁE ~0.65×
(każda sim-sekunda = ~13 jednorodnych próbek streamu; bimodalny inst-RTF = artefakt łapania serwera gz
w busy/idle). **Film OCZYSZCZONY.** Ponieważ pełna ablacja filmu (bridge w całości) NIE przywraca budżetu ⇒
**O2 terminal: STOP programowy z pełnym zrzutem, BEZ trzeciej ablacji w tej sesji.**

### KOSZT REZYDUALNY (nie ablowany dalej per O2) + hipoteza
Stalle ~0.65× są w stacku no-film: **mono `ros_gz_bridge` (parameter_bridge 15 Hz 640×480) + YOLO detektor +
teleport 16.7 Hz (subprocess-per-call)**. **Hipoteza wiodąca (NIE testowana — cap O2):** teleport 16.7 Hz =
**~8× więcej spawnów `gz service` na sekundę** niż stary 2 Hz (16.7 vs 2 handshake'ów transportu gz/s) →
churn połączeń okresowo blokuje pętlę serwera gz → stalle. Wcześniejsze biegi 2 Hz (resanity_2hz_*) kończyły
się „zdrowo" — spójne z tym, że dopiero 16.7 Hz churn tipuje stack. REGATE ma lżejszy, in-process stack
(bez osobnego `ros_gz_bridge`, XRCE, MAVSDK obok) → toleruje ten sam mechanizm przy RTF~1.0.

### O3 (bonus) — NIEZALICZONY: ENTRY nie pada in-window (bo RTF≠1)
Warunek O3 = ENTRY in-window przy RTF≈1; RTF był 0.65, więc precondycja niespełniona. DBG (ablacja):
**in-window `mti_ok=0`, `n_comps` 0–1 (max 1); ENTRY tylko POST-window** (dbg-t 52.9–59.9, park-transition,
box cy≈0.84). Zgodne z W-kontraktem: teleport liczy fazę z ZEGARA ŚCIENNEGO, percepcja z SIM-TIME; przy
RTF 0.65 (34% czasu w stallu) faza ruchu w sim-time jest zdesynchronizowana → oscylacja ±1.5 nie generuje
trwałego MTI. **Te same stalle łamią §5c (koszt) I in-window ENTRY (desync).** Konformancja fazy do sim_t
(W-kontrakt) do wdrożenia w dokumencie fixu kosztu.

### STOP (O2) — pełny zrzut; decyzja Olgi dokumentem
Artefakty (surowe): `results/demo/A1/{cost_probe_5c,cost_probe_5c_v2,ablation_nofilm_5c}/` (manifesty z
`teleport_hz=16.7`, `rtf_stream.jsonl`, trace, dbg, logi; `frames/` gitignore). **§5c NIE przechodzi —
bramka A2 i próby POZOSTAJĄ zamknięte** (tylko PASS §5c pod pełnym obciążeniem je otwiera). Kierunki do
ratyfikacji (jeden dokument, jedna gałąź — SR-8): **(a)** trwały klient `set_pose` (gz transport in-process,
ZERO subprocess churn — ulepszenie PONAD REGATE) ± redukcja obciążenia mono-bridge; **(b)** konformancja
fazy teleportu do `sim_t` (W-kontrakt: wykonanie spec, nie zmiana) — w tym samym pakiecie; **(c)** po fixie
POWTÓRKA §5c pod PEŁNYM obciążeniem — dopiero PASS otwiera A2. Progi/percepcja/spec/hashe/światy/sędzia
`79b1e936`/`r01` NIETKNIĘTE. selfcheck 6/6 ×2.

---

## AKTUALIZACJA-10 / §6 (ANEKS_D5 §6 ratyf.) — trwały klient set_pose: CHURN POTWIERDZONY i głębokie stalle USUNIĘTE, ale rezyduum ~8% + kadencja 9.25 Hz → STOP na decyzję

Data: 2026-08-19. §6a (trwały klient) + §6b (faza sim_t) zbudowane; §6d (powtórka §5c pod pełnym obciążeniem)
**dramatycznie poprawia RTF — hipoteza churnu z §5c/O2 POTWIERDZONA** (głębokie stalle znikają), ale **nie
domyka bramki**: pozostaje ~8% spowolnienie i efektywna kadencja 9.25 Hz < 16.7 (§6a). To NIE 6e (churn nie
sfalsyfikowany — potwierdzony); rezyduum to INNY, mniejszy efekt = latencja synchronicznej usługi set_pose.
`certs_selfcheck` 6/6 ×2, sędzia/spec/światy/progi/`r01` NIETKNIĘTE. **STOP — decyzja Olgi dokumentem. Push=Olga.**

### §6a — trwały klient set_pose in-process (zero subprocess churn)
`r02/intruder_driver.py::GzPoseClient` (gz.transport13 `Node` + gz.msgs10 Pose/Boolean): jeden `Node`,
`node.request(/world/W/set_pose, Pose, Boolean, timeout)` reużywany — ZERO spawnów procesów w pętli ruchu
(poprzednio `subprocess.run(gz service)` per-call). `_telethread` przełączony (fallback subprocess gdy
gz.transport niedostępny). Echo `teleport_backend` w manifeście; **`teleport_backend=gz.transport13(persistent)`
potwierdzony w biegu**. Regresja 72 passed. Ulepszenie ponad REGATE (który też był per-call CLI).

### §6b — faza ruchu z sim_t (W-kontrakt)
`GzPoseClient` subskrybuje `/world/W/clock` → `sim_t()`; `_telethread` liczy `phase = sim_t − sim0`
(kotwica `sim0` do zera choreografii `r.t0`), tick pętli pozostaje wall (sleep). Pozycja intruza = f(sim_t) =
wykonanie spec (nie zmiana). Trajektoria bez zmian.

### §6d — powtórka §5c (FILM=1, pełne obciążenie), robust sampler
`results/demo/A1/recheck_5c_6d/` (backend persistent, DBG_LOG=1). Sampler `rtf_stream.py` (jedna subskrypcja
/stats). **UWAGA metodologiczna:** inst-`real_time_factor` gz uśredniony = 0.9994 (mediana 1.0), ALE
prawdziwe tempo `Δsim/Δwall` (fit liniowy, odporny na truncację sim_s do sekund) = **0.919** — inst-RTF
przeocza KRÓTKIE zamrożenia (podczas nich /stats też milczy → niepróbkowane). Prawda = fit + profil ogona.

| metryka | subprocess §5c (FILM=1) | **§6d persistent (FILM=1)** | R2 baseline (budżet ANEKS-H) |
|---|---|---|---|
| głębokie stalle `frac<0.5` | 32% | **0.0%** | ~0% |
| min RTF | 0.039 | **0.915** | 0.978 |
| p10 | 0.040 | **0.9987** | 0.9971 |
| mean inst-RTF | ~1.0 (mediana, mylące) | 0.9994 | 0.9998 |
| **Δsim/Δwall (fit)** | 0.69 | **0.919** | ~1.0 |
| teleport eff. Hz | ~kilka | **9.25** | (cel 16.7) |

- **CHURN POTWIERDZONY:** usunięcie spawnów subprocess = **głębokie stalle znikają** (`frac<0.5` 32%→**0%**,
  min 0.039→**0.915**). Profil ogona (frac<0.5, p10) w klasie R2. **6e NIE zachodzi** (stalle nie pozostały).
- **ALE nie PASS §6d:** (1) `Δsim/Δwall=0.919` — ~8% poniżej budżetu ~1.0 (R2 avg 0.9998), min 0.915 nieco
  poniżej R2 0.978; (2) **§6a niespełnione: efektywna kadencja 9.25 Hz < 16.7 Hz.**
- **PRZYCZYNA REZYDUUM:** usługa set_pose jest SYNCHRONICZNA — `node.request` blokuje pętlę ~108 ms/wywołanie
  (czeka na reply serwera gz), co (a) kapuje kadencję do 9.25 Hz, (b) sprzęga pętlę z krokiem symu i wnosi
  ~8% narzutu (krótkie zamrożenia niepróbkowane w inst-RTF). Nie churn spawnów (ten usunięty) — latencja
  request-reply usługi.
- **Percepcja:** `n_entry=0` nadal, ale MTI trafia CENTRALNIE (box cy≈0.497 vs pre-fix cy≈0.82); DBG in-window
  mti_ok wciąż głównie na końcu (dbg-t 53–60) — spójne z resztkowym desyncem/kadencją 9.25 Hz. ENTRY prawdop.
  domyka się po usunięciu rezyduum (RTF→1, kadencja→16.7). (Trend boxa między biegami jest szumny — nie
  nadinterpretuję.)

### STOP — pełny zrzut; kierunki do ratyfikacji (jedna gałąź, SR-8)
§5c wciąż nie przechodzi (avg 0.919 < budżet ∧ kadencja 9.25 < 16.7), więc **bramka A2 i próby POZOSTAJĄ
zamknięte**. Churn potwierdzony i główny efekt usunięty; rezyduum = latencja SYNCHRONICZNEJ usługi set_pose.
Opcje (per §6a „service ALBO publisher" i 6e „world-plugin"):
- **(a) WORLD-PLUGIN ruchu intruza po stronie symulatora** (pozycja=f(sim_t) w pętli update świata, poza
  klientem) — ZERO request-reply, kadencja = krok symu, zero narzutu klienta. Najczystsze; **zmienia świat →
  nowy hash → ratyfikacja (ANEKS_D2/SR)**. Rekomendacja wiodąca.
- **(b) NIE-BLOKUJĄCE ustawianie pozy** z klienta (fire-and-forget: request w osobnym wątku / krótki timeout
  bez oczekiwania na reply — pole `ekwiwalentny publisher` §6a) — mniejsza delta, ale ryzyko gubienia
  ustawień; do zweryfikowania czy serwer i tak przetwarza żądanie.
- **(c) diagnoza 108 ms latencji usługi** (czy set_pose jest throttlowany do kroku render/GUI) przed wyborem.
Po fixie: POWTÓRKA §6d pod pełnym obciążeniem (kryteria §6d bez zmian). Progi/percepcja/spec/hashe/światy/
sędzia `79b1e936`/`r01` NIETKNIĘTE. Artefakty: `results/demo/A1/recheck_5c_6d/`. selfcheck 6/6 ×2.
