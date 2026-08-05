# PRE_R01 — dokument przed budową R0.1 (patrol perymetru pod osłoną)

Data: 2026-08-05. Poprzednik: `RAPORT_R0.md` (bramka R0.0 PASS, tryb GPU/D3D12), `results/R01/recon_R01.md` (ETAP R — pomiary R1–R5 + mapa portu).

> **STATUS: [PROPOZYCJA] — do ratyfikacji Olgi. Budowa DOPIERO po ratyfikacji.** Wszystkie sekcje oznaczone [PROPOZYCJA] to propozycje wykonawcy oparte na pomiarach recon; liczby-kryteria są **zamrożone przed pomiarem bramkowym** i **dwustronne** (jawny próg pass/fail).

---

## §1 — Cel R0.1 (jedno zdanie)

Egzekutor **offboard** (bez komponentów uczonych) lata **patrol perymetru po waypointach** w Gazebo, a każde przejście trasy i każda komenda przechodzą przez **osłonę runtime ALLOW/HOLD/REFUSE(reason)** z **księgowością trójwynikową** (SUKCES / ODMOWA / PORAZKA — odmowa ≠ porażka). Slot pilota/estymatora **jawnie pusty** (wchodzi w R0.2). To test **portu architektury osłony na dynamikę PX4**, nie systemu percepcji.

---

## §2 — [PROPOZYCJA] Architektura węzłów

```
                    ┌─────────────── komendy (start/hold/resume/return/abort)
                    │   ADMISJA (authz.py port): parse gramatyki → HMAC-SHA256 → łańcuch PCDL
                    │   REFUSE(NO_MATCH) poza gramatyką; tylko ALLOW wykonywane
                    ▼
   patrol_planner ──► SHIELD (tick) ──► setpoint_publisher (XRCE) ──► PX4 SITL ──► Gazebo
   (generator          │  ALLOW→przepuść setpoint                     │  (offboard)
    waypointów pętli)   │  HOLD →podmień na hold-setpoint(pozycja)     │
                        │  REFUSE→akcja bezpieczna + latch + STOP      ▼
                        │                              [warstwa POD osłoną]
                        └──► TRACE (jsonl per tick: k,state,decision,reason,rule,pos,t)
                                                        GEOFENCE natywny PX4 (GF_*) — ostatnia siatka
```

- **patrol_planner** — czysto proceduralny generator setpointów pętli perymetru (bez uczenia). Slot uczonego pilota = pusty; planer podaje kolejny waypoint/setpoint.
- **shield** — port `s3c1/shield.py`: `step()` per tick zwraca `{decision, reason, rule}`; `outcome()` księguje SUKCES/ODMOWA/PORAZKA z asercją rozłączności. Reasons R0.1: `GEOFENCE`, `COMMAND_INVALID`, `STALE_CMD`, (`STREAM_GUARD` — patrz §4).
- **setpoint_publisher** — jedyny węzeł publikujący na `/fmu/in/trajectory_setpoint` + `/fmu/in/offboard_control_mode`. Osłona jest **jedyną** ścieżką do publishera (kontrakt: żaden setpoint nie omija osłony).
- **źródła komend** — przez admisję+HMAC (port `authz.py`+`memory.py`); komendy spoza gramatyki → REFUSE(NO_MATCH), niewykonane.
- **trace** — każdy tick osłony do `jsonl` (odtwarzalny dowód przebiegu; wejście do P5-konformancji i księgowości bramki).
- **geofence natywny** — `GF_*` jako niezależna ostatnia warstwa (R2), egzekwowana przez commander niezależnie od osłony.

Centralizacja configu: `geo_lim`/obwiednia w **jednym** miejscu, współdzielona przez admisję i osłonę (rozbieżność z portu — recon R0).

---

## §3 — [PROPOZYCJA] Płaszczyzna sterowania (uzasadnienie pomiarowe)

**Wybór: HYBRYDA — setpointy przez XRCE, arm/mode/RTL przez MAVSDK (heartbeat).**

Uzasadnienie z recon R1 (zmierzone):
- Strumień setpointów XRCE @50 Hz: jitter std **0.21 ms**, mniej warstw niż MAVLink (wprost do uORB) → osłona wpięta w strumień XRCE ma czysty, niskolatencyjny kanał egzekucji.
- Arm czysto-XRCE **odrzucony** (`No connection to GCS`) → potrzebny heartbeat MAVLink. MAVSDK dostarcza go i uzbraja niezawodnie (R0.0). Zatem MAVSDK zarządza arm/tryb/RTL, XRCE niesie setpointy pod osłoną.
- Alternatywa odnotowana: pełny MAVSDK offboard (prościej, jedna warstwa; wyższa latencja ingress przez mavlink_receiver) — **odrzucona jako główna**, bo osłona ma egzekwować wysokoczęsty strumień, a XRCE daje niższą latencję i bezpośredni uORB. Decyzja do potwierdzenia w BUILD pierwszym lotem offboard.

**Ciągłość strumienia + failsafe (zmierzone/z kodu):**
- Osłona MUSI utrzymywać strumień: publikować `offboard_control_mode`+`trajectory_setpoint` z okresem **< COM_OF_LOSS_T (1.0 s)**. Zmierzono: przerwa >1.0 s → `offboard_control_signal_lost` po **1.03 s**.
- **Kluczowa zasada projektowa:** HOLD i REFUSE **nie zatrzymują strumienia** — dalej publikują hold-setpoint. Zatrzymanie strumienia = zejście do natywnego failsafe PX4 (`COM_OBL_RC_ACT`), który jest **ostatnią warstwą**, nie podstawową reakcją osłony.
- Parametry do ustawienia w R0.1: `COM_OF_LOSS_T` (zostawić 1.0 s), `COM_OBL_RC_ACT` (proponuję **5=Hold** lub **3=Return** — do zamrożenia w §7), `GF_ACTION`, `GF_MAX_HOR_DIST`, `GF_MAX_VER_DIST`.

---

## §4 — [PROPOZYCJA] Tick osłony i semantyka HOLD/REFUSE w terminach PX4

Osłona tyka z częstotliwością publikacji setpointów (proponuję **20 Hz**; zmierzone 50 Hz trywialnie utrzymywalne, 20 Hz daje zapas). Na każdy tick:

| Werdykt | Co robi osłona | Co robi dron (PX4) | Księgowość |
|---|---|---|---|
| **ALLOW** | przepuszcza setpoint planera na `/fmu/in/trajectory_setpoint` | leci do następnego waypointu perymetru | ścieżka do SUKCES |
| **HOLD** | podmienia setpoint na **hold-pozycji** (bieżąca pozycja, prędkość 0), dalej publikuje @tick | loiter w miejscu (offboard utrzymany, bo strumień żyje) | HOLD (nie porażka; wznawialne) |
| **REFUSE(reason)** | latch terminalny; publikuje **hold-setpoint** (nie urywa strumienia) + wyzwala **akcję bezpieczną** przez MAVSDK (proponuję: Hold→po Δt Return) | zatrzymuje się, potem bezpieczny powrót/ląd wg polityki | **ODMOWA** (rozłączna z SUKCES/PORAZKA) |

- **HOLD** = stan przejściowy (np. komenda `hold`, chwilowy brak następnego waypointu). Wznawiany komendą `resume`.
- **REFUSE** = trwały (latch): próba wyjścia za płot (`GEOFENCE`), komenda spoza gramatyki (`COMMAND_INVALID`/NO_MATCH), przeterminowana komenda (`STALE_CMD`). Akcja bezpieczna zdefiniowana i zalogowana; **odmowa księgowana jako ODMOWA, nigdy jako PORAZKA** (asercja z `outcome()`).
- **STREAM_GUARD** (opcja do decyzji): jeśli planer nie dostarcza setpointu, osłona sama utrzymuje hold-setpoint, by nie stracić offboard (< 1.0 s). To realizacja „ciągłości strumienia" z §3.

---

## §5 — [PROPOZYCJA] Świat + trasa

- **Świat:** `default` (ground+sun, najtańszy) + opcjonalne lekkie znaczniki perymetru (4 słupki w rogach). Kamera `mono_cam` leci w tle jako obciążenie (R3).
- **Trasa perymetru:** prostokąt **40 m × 40 m** (środek w Home), **4 waypointy narożne**, wysokość **10 m** (AGL), prędkość przelotu **3 m/s**. Pętla zamknięta, kierunek stały.
- **Obwiednia geofence (osłona + natywny GF):** półbok **25 m** (perymetr 20 m + margines 5 m) w poziomie, **15 m** w pionie. `GF_MAX_HOR_DIST=25`, `GF_MAX_VER_DIST=15`. Osłona-geofence (port P2) egzekwuje **wewnątrz** (przed natywnym GF) na tej samej obwiedni z jawnym marginesem reakcji.
- **Kamera (stabilny load, R3):** [PROPOZYCJA] `640×480 @ 15 Hz`, `visualize=false` — kryterium stabilności dwustronne w §6.

---

## §6 — [PROPOZYCJA] Zestaw komend R0.1 (gramatyka zamknięta)

Port `language.py` z nowym leksykonem. Gramatyka:
```
start patrol | hold | resume | return home | abort
```
- `start patrol` — rozpocznij pętlę perymetru (ALLOW jeśli dron uzbrojony i w obwiedni).
- `hold` — HOLD (loiter), wznawialne.
- `resume` — wznów pętlę po hold.
- `return home` — RTL (przez MAVSDK).
- `abort` — REFUSE terminalny + akcja bezpieczna (Hold→Land).
Komendy podpisane HMAC, admitowane przez `authz.py`; spoza gramatyki → REFUSE(NO_MATCH). Pamięć korekt (`memory.py`) opcjonalna w R0.1 (aliasy komend) — do decyzji.

---

## §7 — [PROPOZYCJA] Scenariusze bramki (kryteria ZAMROŻONE, dwustronne)

Księgowość trójwynikowa per scenariusz. **Odmowa osłony w S3 to WYNIK POZYTYWNY bramki (ODMOWA), nie porażka.**

### S1 — Nominal: N okrążeń bez interwencji
- Warunek: **N=3** pełne okrążenia perymetru (4 wp każde), bez REFUSE, bez HOLD niezamierzonego.
- Kryteria (zamrożone, dwustronne):
  - Wszystkie waypointy osiągnięte, każdy w promieniu **≤ 1.5 m** (PASS) / > 1.5 m lub pominięty (FAIL).
  - Telemetria pozycji bez przerwy **> 0.5 s** (PASS) / przerwa > 0.5 s (FAIL) — zaostrzenie względem A4 (1 s).
  - Strumień setpointów: min okres między publikacjami **< 0.5 s** przez cały lot (PASS) / ≥ 0.5 s (FAIL).
  - 0 padów GPU (sygnatura pada: `dxg -22` koincydentne ze śmiercią procesu).
  - Kamera-load stabilny: **min/s ≥ 12 Hz** przy celu 15 Hz (PASS) / < 12 Hz (FAIL) — konfiguracja z §5.
  - Księgowość: **SUKCES** (0 ODMOWA, 0 PORAZKA).

### S2 — Wymuszony HOLD (utrata strumienia komend / komenda `hold`)
- Bodziec: w trakcie okrążenia wyślij `hold` (wariant A) LUB odetnij źródło komend (wariant B).
- Kryteria:
  - Dron przechodzi w loiter (utrzymuje pozycję w promieniu **≤ 2 m** przez **≥ 10 s**) (PASS) / dryf > 2 m lub pad offboard (FAIL).
  - **Offboard utrzymany** (osłona publikuje hold-setpoint, `offboard_control_signal_lost=false` przez cały HOLD) (PASS) / utrata offboard (FAIL) — dowód że HOLD nie urywa strumienia.
  - `resume` wznawia pętlę, misja domknięta.
  - Księgowość: **HOLD** zaksięgowany odrębnie; wynik końcowy SUKCES (odmowa≠porażka; HOLD≠porażka).

### S3 — Wymuszona próba wyjścia za płot → REFUSE + akcja bezpieczna
- Bodziec: planer/komenda żąda waypointu **poza obwiednią** (np. 30 m od Home > 25 m limit).
- Kryteria (to jest sedno R0.1):
  - Osłona zwraca **REFUSE(GEOFENCE)** i **NIE przepuszcza** setpointu poza płot (PASS) / setpoint przepuszczony lub dron przekracza obwiednię osłony (FAIL).
  - Akcja bezpieczna wykonana (Hold, potem Return) — dron pozostaje **wewnątrz obwiedni** (max dystans od Home **≤ 25 m**) (PASS) / przekroczenie (FAIL).
  - **REFUSE wyprzedza natywny GF** — osłona reaguje zanim zadziała `GF_ACTION` (dowód: trace osłony REFUSE przed `geofence_result` breach). Natywny GF pozostaje uzbrojony jako ostatnia siatka (weryfikacja defense-in-depth: gdyby osłona zawiodła, GF by złapał).
  - Księgowość: **ODMOWA** (rozłączna, nie PORAZKA). Asercja `outcome()`: `(ODMOWA)⇔terminal-REFUSE`.

### Reguła nadrzędna księgowości
Każdy scenariusz klasyfikowany trójwynikowo. **PORAZKA** = dryf/nieosiągnięcie/pad BEZ odmowy LUB wrong-action (setpoint za płot przepuszczony). **ODMOWA** = osłona zatrzymała misję (terminal REFUSE). **SUKCES** = cel osiągnięty bez odmowy i bez wrong-action.

---

## §8 — [PROPOZYCJA] Plan certyfikatów

| Cert | Zakres R0.1 | Metoda | Status wejściowy |
|---|---|---|---|
| **P1** | Własności nowego automatu osłony (ALLOW⇒w obwiedni; geo⇒REFUSE(GEOFENCE); REFUSE⇒reason∈{GEOFENCE,COMMAND_INVALID,STALE_CMD}; żywy HOLD) | z3 1-indukcja (port `verify.py`) | **re-weryfikacja** na nowym automacie |
| **P4** | Admisja/gramatyka/HMAC nowego zestawu komend (§6); łańcuch weryfikowalny, sabotaż wykryty | property-based + HMAC (port `p4_verify.py`) | **re-weryfikacja** |
| **P5** | Konformancja kod↔model: model z3 ≡ `shield.step()` egzekutora PX4 na wszystkich przejściach | z3 concrete-eval (port `conformance.py`) | **OBOWIĄZKOWO OD NOWA** przeciw nowemu egzekutorowi |
| **P2-analog** | Geofence jako **twierdzenie warunkowe**: „dron respektujący osłonę nie opuszcza obwiedni" z **jawnymi założeniami** | bariera+próg z3 NRA (port `geofence.py`), przepisane na dynamikę PX4 | **od nowa**, założenia: (a) clamp prędkości `V_max` (zmierzyć), (b) czas reakcji osłony ≤ tick (50 ms) + margines do `COM_OF_LOSS_T`, (c) dystans hamowania z profilu decel PX4 (zmierzyć), (d) margines obwiedni 5 m |

**Żadna liczba nie przenosi się z LiquidSight** — `V_max`, decel, tick, margines, obwiednia = zmierzone/ustalone dla PX4 w BUILD, wpięte jako `constants_rational` nowych certów. Kształt dowodów (model=lustro kodu → indukcja/bariera UNSAT → cert z hashem+wersją z3) przenosi się 1:1. P3 (uczony pilot) **poza zakresem R0.1**.

---

## §9 — [PROPOZYCJA] Stop-rules i budżet

**Stop-rules (twarde):**
- Pad GPU o sygnaturze pada (`dxg -22` koincydentne ze śmiercią procesu / `CaptureCrash`) → STOP, dmesg do artefaktu, reguła A5 z RAPORT_R0 obowiązuje (≥3 pady tej samej sygnatury → zejście na software). `fortify WARN`/`escape -75`/bare `-22` = benign, nie liczą się.
- Jeśli hybryda XRCE+MAVSDK nie daje stabilnego offboard po **~1 sesji** prób → fallback: pełny MAVSDK offboard (§3 alternatywa), jawnie oznaczony.
- Jeśli osłona-w-strumieniu wprowadza jitter łamiący S1 (setpoint ≥ 0.5 s) → diagnoza + ewentualne obniżenie tick/optymalizacja, odnotowane.
- P5 (konformancja) FAIL → STOP: dowód nie dotyczy kodu, nie wolno raportować P1 jako wiążącego.

**Budżet:** [PROPOZYCJA] **2–3 sesje**: (1) port osłony/gramatyki/admisji + węzły + pierwszy lot offboard (płaszczyzna sterowania potwierdzona); (2) 3 scenariusze bramki + certy P1/P4/P5; (3) P2-analog + domknięcie RAPORT_R01. Bufor na arming-path (heartbeat) i strojenie kamery-load.

---

## §10 — Rozbieżności względem promptu R0.1 (jawnie)

1. `COM_OBL_ACT` i `GF_COUNT` z promptu **nie istnieją** w PX4 v1.16.2 — używamy `COM_OBL_RC_ACT` (0=Position default) i 5 param `GF_*` (bez GF_COUNT). (recon R1/R2)
2. Dryf kamery „15.8→11.8 Hz" przeformułowany na **wariancję saturacji renderu** (avg ~13 Hz, min/s 4) — nie monotoniczny dryf. Stabilizacja przez konfigurację (§5). (recon R3)
3. Nowe (poza promptem): arm czysto-XRCE blokowany brakiem heartbeatu GCS → wymusza hybrydę XRCE+MAVSDK (§3). (recon R1)
4. `COM_OBL_RC_ACT` domyślnie 0=Position — proponuję zmianę na 5=Hold/3=Return dla patrolu (do zamrożenia). (§3/§7)

---

## §11 — Co przenosi się / NIE przenosi (potwierdzenie)

- **Przenosi się (STRUKTURA/LOGIKA):** automat osłony, semantyka trójwynikowa, gramatyka+admisja+HMAC+pamięć korekt, kształt certów P1/P2/P4/P5, wzorzec integracji harness↔osłona.
- **NIE przenosi się (LICZBA):** wszystkie progi/stałe (obwiednia, V_max, decel, tick, θ_age, ceiling, leksykon, klucz) — nowy habitat PX4, mierzone od nowa.
- **NIE przenosi się (UCZONY):** pilot/estymator (P3, CfC, grounder) — slot pusty, R0.2.

---

**Po ratyfikacji → budowa wg §2–§8, bramka §7 (kryteria zamrożone), reguły §9, certy §8. Push robi Olga. STOP na PRE.**
