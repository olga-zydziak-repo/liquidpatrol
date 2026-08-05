# PRE_R01 — dokument przed budową R0.1 (patrol perymetru pod osłoną)

Data: 2026-08-05. Poprzednik: `RAPORT_R0.md` (bramka R0.0 PASS, tryb GPU/D3D12), `results/R01/recon_R01.md` (ETAP R — pomiary R1–R5 + mapa portu).

> **STATUS: RATYFIKOWANE 2026-08-05** (bazowy commit PRE `d7a0b67`) **z aneksami R01-A1…A4** (poniżej — wiążące, wpięte do §3/§5/§7/§8). Rozbieżności (§10) zaakceptowane w brzmieniu z PRE, w tym `COM_OBL_RC_ACT`→Hold/Return wobec braku `COM_OBL_ACT`/`GF_COUNT` w v1.16.2. Tick 20 Hz zaakceptowany (nowy habitat — liczby z LiquidSight się nie przenoszą). Warunek wejścia w budowę: **push do remote** (Olga wykonuje). Sekcje [PROPOZYCJA] pozostają propozycjami wykonawcy opartymi na recon; liczby-kryteria **zamrożone przed pomiarem bramkowym**, **dwustronne**.

---

## ANEKSY R01-A1…A4 (wiążące, ratyfikowane 2026-08-05)

- **A1 — niezmiennik płaszczyzn:** MAVSDK **wyłącznie** arm/disarm/tryby (+heartbeat); setpointy **WYŁĄCZNIE** XRCE przez osłonę; **żadnych komend ruchu po MAVSDK**. Dowód w bramce: trace misji wykazuje **zero motion-komend po ścieżce MAVSDK**. → wpięte do §3, §7.
- **A2 — zawieranie geometria↔P2:** liczby misji i założenia twierdzenia domykają się **jedną nierównością zawierania**; margines **wyliczony z założeń** (`v_max`, tick 20 Hz, aktywacja ≤125 ms, dynamika hamowania), nie z ręki; jeśli się nie domyka → **poszerzamy obwiednię, nie osłabiamy twierdzenia**. → wpięte do §5, §8.
- **A3 — warstwa-0 mierzalna:** natywny geofence `GF_*` skonfigurowany **NA ZEWNĄTRZ** obwiedni osłony (obwiednia + zapas), akcja Hold/RTL. Kryterium bramki: **0 odpaleń natywnego GF** we wszystkich scenariuszach (osłona uprzedza). Plus **jeden celowy test warstwy-0** (S4): urwanie strumienia → reakcja natywna po ~1.03 s wg `COM_OBL_RC_ACT`, **zalogowana jako scenariusz, nie jako pad**. → wpięte do §5, §7.
- **A4 — kamera:** konfiguracja **zamrożona poniżej progu saturacji** wg danych R3 (rozdzielczość/rate z pomiaru); częstotliwość kamery **raportowana** z płaskością w oknie misji — **metryka raportowana, NIE bramkująca** R0.1. → wpięte do §5, §7.

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

**[A1] NIEZMIENNIK PŁASZCZYZN (wiążący):** MAVSDK obsługuje **wyłącznie** arm/disarm/przełączanie trybów + heartbeat. **Wszystkie setpointy ruchu idą WYŁĄCZNIE przez XRCE przez osłonę** — żadnej komendy ruchu (goto/setpoint/velocity) po ścieżce MAVSDK. `return home`/`abort` realizują tryb RTL/Land przez MAVSDK (przełączenie trybu, nie setpoint ruchu) — dozwolone jako komendy trybu, nie ruchu. Egzekwowane architektonicznie: `setpoint_publisher` (XRCE) to jedyny producent setpointów, za osłoną.

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
- **Trasa perymetru:** prostokąt **40 m × 40 m** (środek w Home), **4 waypointy narożne** w (±20, ±20) m, wysokość **10 m** (AGL), prędkość przelotu **3 m/s**. Pętla zamknięta, kierunek stały. **Maks. promień trasy od Home: R_route = √2·20 = 28.28 m** (narożnik).
- **[A2] Obwiednia osłony R_E (z nierówności zawierania, NIE z ręki):** margines reakcji Δ = `v_max·t_react + v_max²/(2·a_brake)`, gdzie `v_max=3 m/s`, `t_react ≤ 0.2 s` (tick 50 ms + aktywacja ≤125 ms), `a_brake` = **do zmierzenia w BUILD** (profil hamowania PX4; prowizorycznie konserwatywnie 2.0 m/s²). Prowizorycznie Δ = 3·0.2 + 9/(2·2) = **2.85 m**. Zawieranie: `R_route + Δ ≤ R_E` → 28.28 + 2.85 = 31.13 → **R_E = 32 m** (poziomo), **V_E = 20 m** (pionowo). Osłona-geofence (port P2) egzekwuje na R_E z marginesem Δ. **Uwaga: pierwotna obwiednia 25 m NIE zawierała narożnika trasy (28.3 m) — poszerzona do 32 m zgodnie z A2 (poszerzamy obwiednię, nie osłabiamy twierdzenia).** Jeśli zmierzone `a_brake < 2.0` → Δ rośnie → R_E poszerzana ponownie przed bramką.
- **[A3] Natywny geofence GF_* NA ZEWNĄTRZ R_E:** `GF_MAX_HOR_DIST = R_E + 5 = 37 m`, `GF_MAX_VER_DIST = V_E + 5 = 25 m`, `GF_ACTION = 2 (Hold)` lub `3 (Return)`. To warstwa-0 ostatniej szansy — osłona ma **uprzedzać** (kryterium 0 odpaleń, §7).
- **[A4] Kamera — konfiguracja zamrożona poniżej saturacji (R3):** `640×480 @ 15 Hz`, `visualize=false`, `always_on=1`. Uzasadnienie: R3 pokazał saturację przy 1280×960@30 (≈13 Hz avg); 640×480 to ≈4× tańszy render → 15 Hz z zapasem. Częstotliwość + płaskość w oknie misji **raportowane, NIE bramkujące** (§7).

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
  - Telemetria pozycji: brak przerwy **> 0.5 s** (PASS) / przerwa > 0.5 s (FAIL) — zaostrzenie względem A4-R0 (1 s).
  - Strumień setpointów: min okres między publikacjami **< 0.5 s** przez cały lot (PASS) / ≥ 0.5 s (FAIL).
  - **[A1]** trace misji: **0 motion-komend po ścieżce MAVSDK** (PASS) / jakakolwiek komenda ruchu po MAVSDK (FAIL).
  - **[A3]** **0 odpaleń natywnego GF** (`geofence_result` bez breach) (PASS) / ≥1 odpalenie (FAIL) — osłona uprzedza.
  - 0 padów GPU (sygnatura pada: `dxg -22` koincydentne ze śmiercią procesu).
  - Księgowość: **SUKCES** (0 ODMOWA, 0 PORAZKA).
  - **[A4] Raportowane, NIE bramkujące:** częstotliwość kamery + płaskość (min/s, avg) w oknie misji; RTF.

### S2 — Wymuszony HOLD (utrata strumienia komend / komenda `hold`)
- Bodziec: w trakcie okrążenia wyślij `hold` (wariant A) LUB odetnij źródło komend (wariant B).
- Kryteria:
  - Dron przechodzi w loiter (utrzymuje pozycję w promieniu **≤ 2 m** przez **≥ 10 s**) (PASS) / dryf > 2 m lub pad offboard (FAIL).
  - **Offboard utrzymany** (osłona publikuje hold-setpoint, `offboard_control_signal_lost=false` przez cały HOLD) (PASS) / utrata offboard (FAIL) — dowód że HOLD nie urywa strumienia.
  - `resume` wznawia pętlę, misja domknięta.
  - Księgowość: **HOLD** zaksięgowany odrębnie; wynik końcowy SUKCES (odmowa≠porażka; HOLD≠porażka).

### S3 — Wymuszona próba wyjścia za płot → REFUSE + akcja bezpieczna
- Bodziec: planer/komenda żąda waypointu **daleko poza obwiednią** (np. 45 m od Home ≫ R_E=32 m).
- Kryteria (to jest sedno R0.1):
  - Osłona zwraca **REFUSE(GEOFENCE)** i **NIE przepuszcza** setpointu poza płot (PASS) / setpoint przepuszczony lub dron przekracza R_E (FAIL).
  - Akcja bezpieczna wykonana (Hold, potem Return) — dron pozostaje **wewnątrz obwiedni** (max dystans od Home **≤ R_E = 32 m**) (PASS) / przekroczenie (FAIL).
  - **[A3] REFUSE wyprzedza natywny GF — 0 odpaleń GF** (`geofence_result` bez breach; dron nie osiąga 37 m) (PASS) / natywny GF odpalił (FAIL). Dowód: trace osłony REFUSE przed jakimkolwiek `geofence_result` breach. Natywny GF pozostaje uzbrojony jako ostatnia siatka (defense-in-depth).
  - Księgowość: **ODMOWA** (rozłączna, nie PORAZKA). Asercja `outcome()`: `(ODMOWA)⇔terminal-REFUSE`.

### S4 — [A3] Celowy test warstwy-0 (natywny failsafe utraty strumienia)
- Bodziec: **intencjonalne urwanie strumienia setpointów** (osłona przestaje publikować) w bezpiecznym punkcie wewnątrz obwiedni.
- Kryteria:
  - `offboard_control_signal_lost` po **~1.0–1.1 s** (zmierzone recon: 1.03 s = `COM_OF_LOSS_T`) → natywna akcja `COM_OBL_RC_ACT` (Hold/Return) (PASS) / brak reakcji lub reakcja > 1.5 s (FAIL).
  - Dron pozostaje **wewnątrz obwiedni** podczas reakcji (≤ R_E) (PASS) / wyjście (FAIL).
  - **Zdarzenie zalogowane jako SCENARIUSZ (kontrolowana reakcja warstwy-0), NIE jako pad.** exit-code/dmesg tylko jeśli towarzyszy `dxg -22` koincydentne ze śmiercią procesu.
- Cel S4: dowieść, że warstwa-0 (natywny failsafe) działa i jest mierzalna — komplementarnie do S1–S3, gdzie osłona ma ją uprzedzać (0 odpaleń GF). S4 to jedyny scenariusz, w którym warstwa natywna reaguje — celowo.

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

**[A2] Rdzeń zobowiązania P2-analog = jedna nierówność zawierania** (spina geometrię §5 z twierdzeniem):
```
R_route + Δ(v_max, t_react, a_brake)  ≤  R_E        (osłona zawiera trasę + margines)
R_E + zapas                            ≤  R_GF       (natywny GF na zewnątrz, A3)
gdzie Δ = v_max·t_react + v_max²/(2·a_brake)
```
Prowizorycznie: 28.28 + 2.85 = 31.13 ≤ **R_E=32** ; 32 + 5 = **R_GF=37**. Twierdzenie P2-analog: „dron respektujący osłonę (barierę na R_E z marginesem Δ) nigdy nie opuszcza R_E" — dowód bariera+próg z3 NRA. **Margines Δ wyliczony z założeń, nie przyjęty z ręki.** `a_brake` mierzone w BUILD; jeśli nierówność się nie domyka → **poszerzamy R_E (i R_GF), nie osłabiamy twierdzenia** (A2). Bramka S3 empirycznie waliduje twierdzenie (dron ≤ R_E), S4 waliduje warstwę-0.

**Żadna liczba nie przenosi się z LiquidSight** — `v_max`, `a_brake`, tick, Δ, R_E, R_GF = zmierzone/ustalone dla PX4 w BUILD, wpięte jako `constants_rational` nowych certów. Kształt dowodów (model=lustro kodu → indukcja/bariera UNSAT → cert z hashem+wersją z3) przenosi się 1:1. P3 (uczony pilot) **poza zakresem R0.1**.

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
4. `COM_OBL_RC_ACT` domyślnie 0=Position — zmiana na 5=Hold/3=Return dla patrolu (zaakceptowane przy ratyfikacji). (§3/§7)
5. **Korekta geometrii wymuszona przez A2 (przy ratyfikacji):** pierwotna obwiednia 25 m NIE zawierała narożnika trasy 40×40 m (28.3 m od Home). Zgodnie z A2 obwiednia osłony poszerzona do **R_E=32 m**, natywny GF do **37 m** — margines wyliczony z założeń, twierdzenie nietknięte. (§5/§8)

---

## §11 — Co przenosi się / NIE przenosi (potwierdzenie)

- **Przenosi się (STRUKTURA/LOGIKA):** automat osłony, semantyka trójwynikowa, gramatyka+admisja+HMAC+pamięć korekt, kształt certów P1/P2/P4/P5, wzorzec integracji harness↔osłona.
- **NIE przenosi się (LICZBA):** wszystkie progi/stałe (obwiednia, V_max, decel, tick, θ_age, ceiling, leksykon, klucz) — nowy habitat PX4, mierzone od nowa.
- **NIE przenosi się (UCZONY):** pilot/estymator (P3, CfC, grounder) — slot pusty, R0.2.

---

**RATYFIKOWANE z aneksami A1–A4. Warunek wejścia w budowę: push do remote (Olga wykonuje teraz). Następnie budowa wg §2–§8, bramka §7 (S1–S4, kryteria zamrożone), reguły §9, certy §8. STOP do czasu push.**
