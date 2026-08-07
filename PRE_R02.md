# PRE_R02 — [PROPOZYCJA] pełne zadanie: patrol + detekcja intruza + tryb OBSERVE, pod osłoną

Status: **RATYFIKOWANA (2026-08-07) + aneksy R02-A1…A4 naniesione** — przed budową. Reżim recon: **R (tylko odczyt + pomiary nieinwazyjne)**.
Rozbieżności R-DIV-1…4 zaakceptowane w brzmieniu z PRE (R-DIV-1 potwierdzona: prompt się mylił, PRE ma rację). Budowa od bramki wczesnej **B0** po pushu (Olga).
Data: 2026-08-07. Poprzedniki: `RAPORT_R01.md` (R0.1 ZALICZONA — osłona/automat/certy P1/P2/P4/P5),
`RAPORT_P2.md §7.1` (zwycięzca pomiaru = **ZOH-age**, kandydaci uczeni GRU+Δt/CfC **zaparkowani**),
`results/R01/recon_R01.md` (R5 zasoby, sufit mostu). Prowieniencja semantyki kanału celu:
LiquidSight **3c/G2** (`~/projects/liquidsight` — D3 `(cx,cy,w,h,conf,age_s)` ZOH, θ_age z G2).

> **STOP po tym dokumencie.** Zero budowy. Wszystkie liczby oznaczone `[MIERZ]` są **do zmierzenia w R0.2**
> pod kryteriami **zamrożonymi w tym PRE** (dwustronnymi: PASS ∧ FAIL), zanim padnie pomiar. Liczby
> oznaczone `[ZMIERZONE]` pochodzą z recon nieinwazyjnego tej sesji lub z domkniętych faz.

---

## 0. Rozbieżności względem promptu — JAWNIE (czytać najpierw)

**R-DIV-1 (krytyczna) — kanał celu 5-dim NIE jest „przeniesiony w R0.1".**
Prompt: „kanał celu = semantyka ZOH-age już przeniesiona w R0.1 (5-dim cx,cy,w,h,age + ENTRY + sufit
wieku)". **Kod R0.1 tego nie zawiera.** `r01/shield.py:step(k,pos,vel,target,mode)` przyjmuje `target`
= **3-D waypoint NED** (x,y,z) z proceduralnego planera (`patrol_exec.py:Planner.target()` → `corner_waypoints()`).
Nie ma pola `age`, nie ma zdarzenia ENTRY, nie ma sufitu wieku, nie ma detektora ani kamery-jako-wejścia.
Co **jest** przeniesione w R0.1: automat osłony (6 liści), gramatyka/admisja/HMAC (P4), certy P1/P2/P5.
Co jest **decyzją z prowieniencją** (nie kodem): „semantyka kanału = ZOH-age" — wynik `RAPORT_P2 §7.1`
(offline proxy nie rekomenduje rdzenia uczonego) **+** wzorzec z LiquidSight 3c/G2 (`RAPORT_S3B1` D3).
**Konsekwencja dla zakresu:** kanał 5-dim+age+ENTRY+sufit to **budowa w R0.2**, nie „już mamy". Ten PRE
traktuje go jako komponent do zbudowania i pomiaru. Semantyka jest ustalona; implementacja PX4 — nowa.

**R-DIV-2 — modalność.** P2/Anti-UAV = **IR**. Kamera symu R0.1 = **mono widzialna**
(`x500_mono_cam_0`, `RAPORT_R01 §6`). Detektor w pętli R0.2 działa na **mono widzialnej 320×240**,
nie IR. Liczby detekcji/latencji z P2 (IR) i z LiquidSight (RGB syntetyczne „{kolor}{kształt}")
**nie przenoszą się jako pomiar** — R0.2 mierzy od nowa na tym strumieniu (R-DIV-4).

**R-DIV-3 — rdzeń uczony poza zakresem.** Zgodnie z `RAPORT_P2 §7.1`: jedynym komponentem uczonym
R0.2 jest **detektor**. GRU+Δt/CfC **zaparkowane** — wracają wyłącznie osobnym PRE, jeśli bramka R0.2
wykaże **konkretny** tryb porażki adresowany predykcją (nie „na zapas"). Zapisane w stop-rules (§7).

**R-DIV-4 — pomiary detektora/GPU NIE są wykonane w tym recon.** `torch`/`ultralytics` **nieobecne**
w tym środowisku (`cv2` obecny) — latencji ani VRAM detektora **nie da się zmierzyć nieinwazyjnie**
(wymaga instalacji + pobrania wag = budowa). Liczby LiquidSight (YOLO-World 63 ms @1 Hz; OWLv2 1.6 s)
to **inny sprzęt/habitat** — cytowane jako *hipoteza wejściowa*, nie jako pomiar R0.2. Główny pomiar
reconu (latencja/Hz detektora na TYM sprzęcie z żywym symem) jest **zaplanowany, nie zaległy**.

---

## 0bis. Aneksy ratyfikacyjne (R02-A1…A4) — WIĄŻĄCE

**R02-A1 — kanał BEZ conf (jawnie).** Kanał celu = **5-dim `(cx,cy,w,h,age)`, BEZ `conf`**.
Prowieniencja decyzji: **3b po conf-shift + S3c0** (ROC conf **AUC 0.6496** → **D1: bez progu conf** —
conf słabo separuje, nie wnosi do decyzji). `conf` **może** żyć w **telemetrii/logach detektora**,
**nigdy** w kanale wejściowym ani w decyzjach osłony. Cytowana forma LiquidSight `D3=(cx,cy,w,h,conf,age_s)`
to **forma surowa detektora**, nie forma kanału. **Skutek:** znosi „θ_conf w detektorze / conf jako próg
publikacji" z §2.3/§4 — detektor publikuje top-1 box bez bramkowania conf (spójnie z D1); ewentualne
odrzucenia trafiają wyłącznie do logów, nie do kanału. Osłona nie widzi conf.

**R02-A2 — pomiar detektora = bramka wczesna B0.** Budowa **zaczyna się** od instalacji
(torch+ultralytics+wagi) i **pomiaru detektora przy działającym symie** wg kryteriów §4
(L_det latencja/Hz, VRAM headroom — **dwustronnie**), **ZANIM** powstanie jakikolwiek kod zależny
(kanał, OBSERVE, aktor). **B0 poza budżetem → STOP + decyzja** (lżejszy model / niższa częstotliwość /
niższa rozdzielczość), **nie brnięcie**. B0 jest pierwszym artefaktem R0.2 i warunkuje resztę.

**R02-A3 — OBSERVE a P2 (jawnie).** **Tryb OBSERVE nie zmienia `v_max`, clampów prędkości ani
obwiedni (`R_E`,`V_E`).** Setpoint OBSERVE respektuje te same wartości `config.py` co patrol.
**Jeśli którakolwiek z tych wielkości miałaby się zmienić — P2-analog wraca do re-dowodu PRZED bramką**
(wzorzec robustności v_max=3.1 z `RAPORT_R01 §5.4`). Bez zmiany tych wielkości: P2 niezmieniony.

**R02-A4 — sufit wieku θ_age (liczby się nie przenoszą).** Wartość θ_age dla tego habitatu **albo**
pochodzi ze **źródła pomiarowego w TYM habitacie** (histogram age-at-ENTRY / rozkład luk detekcji na
żywym strumieniu mono 320×240), **albo** jest **jawnie oznaczona jako prowizoryczna i związana z
pomiarem w bramce**. **NIE kopiuje się liczbowo z G2** — G2 jest prowieniencją **semantyki**
(ZOH+rosnący age, reguła wygaszenia), **nie liczby**. Zasada „liczby się nie przenoszą" (A2 R0.1)
obowiązuje też tu. To samo dotyczy `L_deliver`, `D_safe`, `T_ack`, `ε_FP`, `f_fov` — pomiar habitatu,
nie import.

---

## 0ter. Uzupełnienie po R1 (decyzja intruza + R1-A/R1-B) — WIĄŻĄCE

**Intruz = sylwetka x500** (mesh PX4/gz reużyty przez `model://`; `.glb` zewn. tylko fallback).
Zwalidowane mini-sanity (`RAPORT_R1 §3a`): pokrycie 3/3 conf 0.177 z intruzem, 0 boxów bez.

**R1-A (progi detekcji, jedna linia — zamrożone):** intruz „wykrywany" w klatce ⇔ top-1 box **pokrywa**
prawdziwą pozycję intruza (środek boxa w true-bbox z pixel-diff GT symu); scena bez intruza PASS ⇔
**brak** boxa spełniającego kryterium ENTRY (poniżej). Do bramki: `coverage_when_present ≥ 0.8` klatek
w-polu; `false_lock_when_absent = 0` zdarzeń ENTRY.

**R1-B (ENTRY strukturalny, NIE conf — A1/D1 stoi):** wejście w OBSERVE wymaga **spójnej detekcji przez
k = 3 kolejne klatki @1 Hz** (top-1 box w spójnej lokalizacji, ruch ≤ próg między klatkami), NIE progu
confidence. `age` liczony od pierwszej z serii k. Wartość **k=3** (≈3 s) zamrożona; do rewizji tylko
pomiarem w G1/G2. **G1 mierzy ε_FP jawnie** (liczba zdarzeń ENTRY na pustej scenie / min — cel 0).

---

## 1. Cel i teza

**Zadanie docelowe R0.2:** egzekutor lata **patrol perymetru** (jak R0.1), a gdy w polu widzenia
pojawia się **intruz**, **detektor** (jedyny komponent uczony) zasila **kanał celu ZOH-age**, na którym
osłona/planer wchodzą w **tryb OBSERVE** — utrzymanie celu w FOV z **dystansem bezpiecznym**, **bez
zbliżania**, i **NIGDY** łamiąc obwiednię geofence (REFUSE nadrzędny). Utrata detekcji → degradacja po
`age` z **sufitem wieku** → wyjście z OBSERVE.

**Teza R0.2 (pomiarowa, do zamrożenia w §4):** *pełny łańcuch kamera→detektor→kanał ZOH-age→osłona
utrzymuje cel w FOV z dystansem bezpiecznym, przy zachowaniu WSZYSTKICH niezmienników R0.1 (A1, P1a,
geofence nadrzędny, 0 padów), a detektor mieści się w budżecie latencji i zasobów (GPU dzielone).*
**Główny pomiar:** detektor (latencja, Hz, headroom). **Arbiter:** bramka w pętli zamkniętej (§4).

---

## 2. Architektura (R1–R6 → projekt)

### 2.1 R1 — intruz w świecie (aktor Gazebo)

| Wymiar | Opcje | **Propozycja** | Uzasadnienie |
|---|---|---|---|
| Typ | (a) druga jednostka latająca PX4 SITL; (b) kinematyczny model latający (pose-scripted); (c) obiekt naziemny | **(b) kinematyczny aktor latający** | typ zagrożenia = UAV (spójne z misją anti-UAV); pełny PX4 SITL #2 = **niedeterministyczny** (regulator) + drugi px4+XRCE = koszt zasobów; kinematyczny = deterministyczny i tani |
| Ruch | analityczna trajektoria f(t_sim) / skrypt waypointów po zegarze symu | **f(t_sim) deterministyczna** (bez fizyki, `SetPose` per krok symu) | **DETERMINIZM = powtarzalność scenariuszy** (wymóg bramki): ta sama trajektoria co do klatki między biegami; brak dryfu regulatora |
| Koszt SDF | model wizualny (mesh quad lub prosty prostopadłościan) bez kolizji/aerodynamiki | **model wizualny, physics OFF** dla aktora | nie obciąża fizyki; **obciąża render GPU** (nie rozmiar ramki mostu — ten stały przy rozdzielczości kamery, `RAPORT_R01 §6`) → wchodzi do headroomu GPU (R5) |
| Determinizm | seedy trajektorii per scenariusz, zamrożone | **seed=ID scenariusza**, log trajektorii do trace | odtwarzalność biegów bramki |

Uwaga: aktor kinematyczny NIE respektuje geofence drona (to intruz — ma go łamać/prowadzić w stronę
płotu w scenariuszu S3). Geofence chroni **naszego drona**, nie intruza.

### 2.2 R2 — detektor (GŁÓWNY POMIAR)

- **Kandydat wiodący:** YOLO-World (`yolov8s-worldv2`, ultralytics) — jak LiquidSight D1-live.
  Prowieniencja hipotezy: LiquidSight zmierzył **63.1 ms med / p95 ≤78 ms @1 Hz** (`RAPORT_S3B1:103`)
  → wykonalny @1 Hz. **[Uwaga R-DIV-4: inny sprzęt/habitat — R0.2 mierzy od nowa.]**
- **Alternatywa lżejsza (fallback jeśli budżet/headroom nie domyka):** detektor jednoklasowy
  (YOLOv8n/s trenowany/dostrojony pod „UAV" na mono, ~640) lub prosty detektor ruchu/kontrastu jako
  baseline nie-uczony. Wybór po pomiarze latencji+headroom, nie z góry.
- **Strumień:** mono widzialna, **320×240** (= 225 KB/ramkę, `RAPORT_R01 §6`; **< sufit mostu ~256 KB**
  → transport nie jest wąskim gardłem). Kadencja detektora: **1 Hz** (hipoteza; profil „256×256@1 Hz"
  z `RAPORT_R01 §6` mieści się pod progiem). Szybki kanał 64×64@12 Hz **nie** dla detektora (za mało
  pikseli na intruza) — zarezerwowany ewentualnie pod ruch/kinematykę.
- **Pomiar (R2 = bramka wczesna B0, R02-A2, [MIERZ]):** latencja detektora (med, p95) i osiągalny Hz
  na **RTX 5070 Ti / WSL2 / D3D12**, **przy żywym symie** (kontencja GPU render↔inferencja), reżimy
  jak LiquidSight R1 (idle-gap 1 s / równoległe obciążenie / keep-alive). Wpływ na headroom → R5.
  **B0 wykonywane PRZED jakimkolwiek kodem zależnym**; poza budżetem §4 → STOP + decyzja (nie brnięcie).

### 2.3 R3 — kanał celu end-to-end (kamera→detektor→ZOH-age→planer/osłona)

- **Format kanału (5-dim, decyzja):** `(cx, cy, w, h, age_s)` znormalizowany do rozdzielczości obrazu.
  **BEZ `conf` (R02-A1).** LiquidSight `D3=(cx,cy,w,h,conf,age_s)` to **forma surowa detektora**, nie
  kanału. Decyzja **D1** (3b po conf-shift + S3c0, ROC conf AUC 0.6496): **bez progu conf** — detektor
  publikuje **top-1 box bez bramkowania conf**; `conf` żyje wyłącznie w telemetrii/logach detektora,
  **nigdy** w kanale ani w decyzjach osłony. `[zamrożone: 5-dim (cx,cy,w,h,age), zero conf w kanale]`.
- **Semantyka ZOH-age:** przy detekcji → nadpisz `(cx,cy,w,h)`, `age_s := L_deliver`. Bez detekcji →
  ZOH ostatniej detekcji, `age_s += Δt`. **ENTRY** = zdarzenie pierwszego locka (age spada z „∞"/sufit
  do L_deliver) → warunek wejścia w OBSERVE. **Sufit wieku θ_age:** `age_s > θ_age` → cel „wygasły" →
  wyjście z OBSERVE (powrót do PATROL). (Wzorzec STALE_AT_DWELL z 3c: `age>θ_age → HOLD`,
  `PRE_3C0` D2; tu adaptowane na „wygaszenie celu obserwacji".)
- **Topiki/QoS:** kamera przez most ROS2 (`sensor_msgs/Image`, **BEST_EFFORT** — lekcja R0.1: reliable
  dławi), detektor = węzeł ROS2 subskrybujący obraz, publikujący kanał celu (nowy msg 5-dim, np.
  `Float32MultiArray` lub własny) @1 Hz do planera/osłony. Setpointy dalej **tylko XRCE przez osłonę**
  (niezmiennik A1 — nietknięty). Rozważyć **gz-transport bezpośrednio** w węźle detektora (omija most/DDS,
  `RAPORT_R01 §6` opcja 2) jeśli most okaże się wąski przy żywym symie — ale profil 320×240 już się mieści.
- **Częstotliwości ogniw:** kamera gz ~13–20 Hz (§6 R0.1) → most 320×240 ~15–29 Hz → detektor **1 Hz**
  (dławik = latencja inferencji) → kanał 1 Hz → osłona tyka **20 Hz** (ZOH między detekcjami).
- **Propozycja sufitu wieku θ_age dla tego habitatu (R02-A4):** **[MIERZ w R0.2]** — z histogramu
  `age-at-ENTRY` i rozkładu długości dziur detekcji na żywym strumieniu mono 320×240 (analog G2).
  **Liczba NIE kopiowana z G2** (G2 = prowieniencja semantyki, nie liczby; „liczby się nie przenoszą",
  A2 R0.1). Zamrażam **regułę** wyboru: θ_age = separacja histogramów (percentyl P95 naturalnych luk
  detekcji), zatwierdzenie przed bramką; **do pomiaru — prowizoryczna i związana z bramką**. To samo
  `L_deliver`, `D_safe`, `T_ack`, `ε_FP`, `f_fov` — pomiar habitatu, nie import.

### 2.4 R4 — semantyka trybu OBSERVE (osłona) + zakres re-certyfikacji

**Zachowanie:** OBSERVE utrzymuje cel w FOV z **dystansem bezpiecznym D_safe** (bez zbliżania):
setpoint obserwacji = pozycja utrzymująca `d(dron, estymata_celu_w_NED) ≥ D_safe` **i** cel w stożku
FOV, **z prędkością ≤ v_max**. Estymata celu w NED z detekcji obrazowej: **[decyzja projektowa R0.2]**
— rzut bearing-only (kierunek z (cx,cy)) na stałą wysokość intruza LUB pierścień D_safe wokół bieżącej
projekcji; **bez** rdzenia uczonego (R-DIV-3). D_safe **[MIERZ/ustal]** z FOV kamery i marginesu.

**Interakcja z geofence — KLUCZOWE (śledzenie NIGDY nie łamie obwiedni):**
W automacie R0.1 reguła **R-G (geofence)** ma priorytet **nad** wszystkimi trybami ruchu
(`shield.py:_decide` — R-T→R-G→R-A→R-H→R-R→R-P). OBSERVE wchodzi jako **nowy liść R-O na poziomie
R-P** (produkuje setpoint = decyzja klasy ALLOW), **poniżej R-G**. Skutek: setpoint OBSERVE goniący
intruza w stronę/za płot jest przecięty przez R-G dokładnie tak, jak waypoint patrolu (bariera na
`target` **i** `pos+hamowanie`, `shield.py:_geofence_violation`). **REFUSE(GEOFENCE) nadrzędny nad
OBSERVE — z konstrukcji priorytetu, nie dodatkowej reguły.** To domyka wymóg „śledzenie nigdy nie
łamie obwiedni".

**Zakres zmian automatu (nowe przejścia):**
- Nowy tryb `M_OBSERVE` + liść `L_observe` (klasa ALLOW, applied = setpoint obserwacji).
- Wejście: ENTRY (lock detektora, `age≤θ_age`) — **decyzja: kto przełącza tryb?** OBSERVE jest
  **auto-wyzwalany kanałem** (nie komendą operatora), ALE autorytet włączenia/wyłączenia OBSERVE
  wchodzi do **gramatyki** (P4) jako komenda `observe on/off` (default on) — by nie omijać admisji.
  Detektor daje ENTRY; gramatyka daje **pozwolenie**; osłona składa oba.
- Wyjście: `age>θ_age` (wygaśnięcie) → PATROL; lub HOLD/RETURN/ABORT/GEOFENCE (priorytet zachowany).

**Zakres re-certyfikacji (zmapowany na istniejące certy):**

| Cert | Wpływ | Zakres re-cert R0.2 |
|---|---|---|
| **P1** (`verify.py`) | **TAK** — automat rośnie 6→7 liści (`tau` +`L_observe`, +`M_OBSERVE`) | re-dowód 1-indukcji: **P1a musi trzymać** (OBSERVE=ALLOW ⇒ ¬geo∧¬term); P1b/c/d bez zmian treści, re-run |
| **P5** (`conformance.py`) | **TAK** — pokrycie 6→7 liści; `LEAVES += observe`; `MODE_ID += M_OBSERVE` | re-run konformancji tau≡shield, pokrycie 7/7, 0 rozbieżności |
| **P4** (`p4_verify.py`) | **TAK jeśli** dodajemy `observe on/off` do gramatyki (`language.py` +2 akcje) | re-run property-2000 + łańcuch HMAC; nowe akcje w tabeli, poza-gramatyką dalej COMMAND_INVALID |
| **P2/P2-analog** (bariera) | **NIE** (jeśli D_safe, v_max, R_E, a_brake, t_react niezmienione) | geofence-arytmetyka nietknięta; OBSERVE nie zmienia dynamiki hamowania. **Warunek:** setpoint OBSERVE respektuje v_max (clamp). Jeśli OBSERVE wprowadzi wyższe v → re-dowód P2 (jak robustność v_max=3.1 w R0.1). |
| Niezmiennik **A1** (setpointy tylko XRCE) | **NIE** — OBSERVE publikuje przez tę samą ścieżkę osłona→XRCE | dowód A1=0 w trace każdego scenariusza (jak R0.1) |

### 2.5 R5 — zasoby (GPU dzielone sim+detektor)

- **[ZMIERZONE recon]** GPU: **RTX 5070 Ti Laptop, 12 227 MiB VRAM** (idle 0 MiB, 0% — sim nie żył
  podczas sondy). RAM systemowy (R0.1 R5): sim+GUI+px4+agent+węzeł ≤ ~2.2 GB RSS, **≥13.5 GB wolne**
  z 15.7 GB; węzeł Python osłony pomijalny (~80–150 MB).
- **[MIERZ R0.2]** **VRAM headroom przy dzieleniu:** `VRAM(render D3D12 sim + aktor) + VRAM(kontekst
  CUDA + YOLO-World) ≤ 12 GB`, z marginesem. Kontekst CUDA + yolov8s ≈ rząd 1–2 GB (hipoteza,
  do pomiaru). Render sim + intruz — nieznany narzut, do pomiaru. **Kontencja render↔inferencja**
  (ta sama GPU pod D3D12+CUDA) może podbić latencję detektora — mierzone łącznie w R2.
- **Uwaga:** dodanie intruza-aktora podnosi render GPU (nie rozmiar ramki mostu). Wchodzi do headroomu.

### 2.6 R6 — szkic scenariuszy bramki (pełny w §4)

Nominal bez intruza → detekcja+OBSERVE → prowadzenie w stronę płotu→odmowa ścieżki → utrata detekcji→age+sufit.

---

## 3. Diagram łańcucha (ASCII)

```
 Gazebo(sim) --mono 320x240 @~15Hz--> [most ROS2 BEST_EFFORT, <256KB/ramkę]
   |  (+ aktor-intruz kinematyczny, f(t_sim), physics OFF)                |
   |                                                                       v
   |                                 [DETEKTOR uczony @1Hz, top-1 box, BEZ conf w kanale (A1)]-->
   |                                                                       |
   v                                                          [KANAŁ ZOH-age 5-dim (cx,cy,w,h,age)]
 [MAVSDK tel NED 20Hz]                                   ENTRY(lock)/ age+=Δt / age>θ_age→wygaś
   |                                                                       |
   v                                                                       v
 [OSŁONA @20Hz]  R-T > R-G(geofence) > R-A > R-H > R-R > R-O(OBSERVE) > R-P(patrol)
   |  applied-setpoint (ALLOW/HOLD/REFUSE)                                 |
   +--------------------- XRCE (JEDYNA ścieżka setpointów, A1) ------------> PX4
```

---

## 4. Bramka R0.2 — scenariusze z kryteriami DWUSTRONNYMI (zamrożone przed pomiarem)

Księgowość **trójwynikowa** (port `shield.outcome`): **SUKCES / ODMOWA / PORAZKA** (odmowa ≠ porażka).
Świeży boot per scenariusz (zaostrzenie R0.0/R0.1). Kryteria zamrożone TU, **przed** pomiarem.
Format: **PASS jeśli … ; FAIL jeśli …** (dwustronne — brak strojenia po fakcie).

**Niezmienniki globalne (każdy scenariusz):** A1 (`mavsdk_motion_cmds=0`); 0 padów; geofence nadrzędny;
osłona = jedyna ścieżka setpointów.

| ID | Scenariusz | PASS (dwustronnie) | FAIL | Wynik-typ |
|---|---|---|---|---|
| **G1** | **Nominal bez intruza** | 3 okrążenia patrolu jak R0.1 S1 (wp≤1.5 m, A1=0, GF=0, max_r<R_E), **detektor żywy ale 0 ENTRY** (0 fałszywych locków na pustej scenie, ≤ ε_FP/min) | ENTRY bez intruza > ε_FP; lub regres patrolu R0.1 | SUKCES |
| **G2** | **Intruz wchodzi → detekcja+OBSERVE** | ENTRY w ≤ T_ack s od wejścia intruza w FOV; przejście do OBSERVE; cel utrzymany w FOV udział ≥ f_fov klatek; `d(dron,intruz) ≥ D_safe` **przez cały OBSERVE** (0 naruszeń dystansu); A1=0 | brak ENTRY gdy intruz w FOV > T_ack; lub OBSERVE zbliża się `d<D_safe`; lub gubi FOV < f_fov | SUKCES |
| **G3** | **Intruz prowadzi w stronę płotu → odmowa ścieżki** | gdy setpoint OBSERVE naruszyłby obwiednię → **REFUSE(GEOFENCE)** (lub HOLD na barierze), **GF native=0** (osłona uprzedza), dron **nie** przekracza R_E (max_r<R_E), **śledzenie NIE łamie obwiedni** | dron przekracza R_E goniąc intruza; lub setpoint za płot przepuszczony (wrong-action=PORAZKA); lub native GF odpala przed osłoną | **ODMOWA** (≠porażka) |
| **G4** | **Utrata detekcji → zachowanie na age z sufitem** | po zniknięciu intruza: ZOH utrzymuje kanał, `age` rośnie; przy `age>θ_age` → **wyjście z OBSERVE do PATROL** (nie ślepy finisz na starej detekcji); brak dryfu/padu | trzyma OBSERVE po `age>θ_age`; lub goni ostatnią (starą) pozycję; lub pad/dryf | SUKCES (degradacja kontrolowana) |
| **G5** | **Warstwa-0 (regres R0.1 S4)** | urwanie strumienia XRCE → natywna reakcja HOLD ≤ ~1.2 s, ≤R_E, brak padu — **niezmiennik R0.1 utrzymany mimo OBSERVE** | regres reakcji warstwy-0 | reakcja warstwy-0 |

**Certy (re-run, PASS-warunek):** P1 PROVED (7 liści, P1a trzyma), P5 PASS (7/7, 0 rozbieżności),
P4 PASS (gramatyka +observe), P2 PROVED **bez zmian** (o ile v_max/R_E/a_brake nietknięte) lub re-dowód.

**Pomiary głównego toru (R2, dwustronne progi — [MIERZ], zamrożone TU):**
- **L_det (latencja detektora @1 Hz, żywy sim):** PASS jeśli **p95 ≤ 800 ms** (< tick 1 s, margines
  jak LiquidSight); FAIL jeśli p95 > 1000 ms (detektor nie nadąża @1 Hz → fallback lżejszy, R2 alt).
- **VRAM headroom:** PASS jeśli `VRAM(sim+aktor+CUDA+detektor) ≤ 11 GB` (margines ≥1 GB z 12); FAIL jeśli
  > 12 GB (OOM ryzyko → fallback lżejszy detektor / mniejsza rozdzielczość).
- **RTF symu z detektorem:** raportowany (nie bramkujący, A4-analog); nota jeśli RTF < 0.9 pod kontencją.

*(Wartości ε_FP, T_ack, f_fov, D_safe, θ_age, L_deliver domyka **krok 0 R0.2** — kalibracja OFFLINE/na
żywym strumieniu **przed** bramką, wzorzec S3c0: zaproponuj 2–3 punkty, zatwierdzenie Olgi, ZAMROŻENIE.
Reguły ich wyboru zamrożone tu; liczby = pomiar, nie zgadywanka w PRE.)*

---

## 5. Plan re-certyfikacji (szczegół)

0. **certs_selfcheck (GUARD — PIERWSZY krok, przed P1/P4/P5)** —
   `python3 -m r01.proofs.certs_selfcheck`: dla każdego certu `model_sha256 == sha256(jego prover)`.
   **Głośny FAIL (exit 1) przy rozjeździe** → napraw (regeneracja prover + commit) ZANIM ruszysz re-cert.
   Uruchamiany też na **koniec każdej sesji dotykającej `proofs/`**.
   **Lekcja higieny (repo): sesja uruchamiająca prover kończy się CZYSTYM DRZEWEM albo COMMITEM.**
1. **P1** — rozszerzyć `verify.py:tau` o `M_OBSERVE`/`L_observe` (klasa ALLOW), re-dowód 1-indukcji.
   Krytyczne zobowiązanie: **P1a** (`ALLOW ⇒ ¬geo ∧ ¬term`) — OBSERVE jako ALLOW **musi** siedzieć
   poniżej R-G w `tau`. Oczekiwane: 6/6 zobowiązań unsat (+ ewent. P1e: `OBSERVE ⇒ ¬geo`).
2. **P5** — `conformance.py`: `LEAVES += "observe"`, `MODE_ID += M_OBSERVE`, generator celowany +
   epizod OBSERVE i OBSERVE→geo→latch; pokrycie **7/7**, 0 rozbieżności tau≡shield.
3. **P4** — `language.py`: `+observe on/off` (2 akcje/tryby), `p4_verify.py` property-2000 re-run;
   poza-gramatyką dalej `COMMAND_INVALID`; łańcuch HMAC odtwarzalny.
4. **P2/P2-analog (R02-A3)** — **niezmieniony** o ile OBSERVE respektuje `v_max`, `R_E`, `a_brake`,
   `t_react` z `config.py`. Warunek weryfikowany w kodzie (clamp setpointu OBSERVE). **Jeśli
   którakolwiek z tych wielkości miałaby się zmienić — P2-analog WRACA do re-dowodu PRZED bramką**
   (wzorzec robustności v_max=3.1 z R0.1 §5.4). OBSERVE nie zmienia dynamiki hamowania.
5. **A1** — trace każdego scenariusza: `mavsdk_motion_cmds=0` (OBSERVE publikuje tylko przez XRCE/osłonę).

---

## 6. Budżet (szacunek, do zatwierdzenia)

| Pozycja | Koszt | Uwaga |
|---|---|---|
| **B0 (bramka wczesna, A2):** instalacja torch+ultralytics+wagi + **pomiar detektora z symem** (L_det/Hz/VRAM) | ~kilka GB dysk + 1 jednostka | **PIERWSZY artefakt**, przed kodem zależnym; poza budżetem → STOP |
| Krok 0: aktor-intruz kinematyczny (SDF+skrypt f(t_sim)) | 1 jednostka | deterministyczny, physics OFF; **po PASS B0** |
| Krok 0: węzeł detektora + kanał 5-dim ZOH-age (ROS2) | 1–2 jednostki | most/QoS jak R0.1; ZOH+age+ENTRY+θ_age |
| Krok 0: kalibracja θ_age/D_safe/L_deliver/T_ack/ε_FP/f_fov (habitat, A4) | 1 jednostka | **zamrożenie przed bramką; bez conf (A1)** |
| OBSERVE w osłonie (M_OBSERVE, R-O) + re-cert P1/P4/P5 | 1–2 jednostki | 7 liści; P1a krytyczne |
| Bramka G1–G5 (świeży boot per scen.) + pomiary R2/R5 | 2 jednostki | wall ~ jak R0.1 gate |
| **Główny pomiar:** L_det, Hz, VRAM headroom na TYM sprzęcie z symem | wliczone w bramkę | R-DIV-4 |

Pomiar RTF/zasobów: raportowany, nie bramkujący (A4-analog).

---

## 7. Stop-rules

- **SR-1 (detektor niewykonalny @1 Hz):** jeśli L_det p95 > 1000 ms na tym sprzęcie mimo fallbacku
  lżejszego → **STOP + RAPORT**, opcja: obniż rozdzielczość / kadencję, lub zmień kandydata; nie
  „naciągaj" ticku bramki.
- **SR-2 (VRAM OOM):** headroom < 0 (sim+detektor > 12 GB) → **STOP + RAPORT**; fallback rozdzielczość/model.
- **SR-3 (regres niezmiennika R0.1):** jakikolwiek scenariusz łamie A1, P1a, geofence-nadrzędność
  lub daje pad → **STOP** (niezmiennik R0.1 jest twardy, nie negocjowalny w R0.2).
- **SR-4 (rdzeń uczony — brama parkingu):** GRU+Δt/CfC wchodzą **wyłącznie** jeśli bramka R0.2 wykaże
  **konkretny, nazwany** tryb porażki kanału ZOH-age adresowalny predykcją (np. G4 systematycznie
  FAIL przez martwe pole dłuższe niż ZOH mostkuje). Wtedy → **osobny PRE**, nie rozszerzenie tego.
  Bez takiego dowodu — rdzeń uczony pozostaje zaparkowany (`RAPORT_P2 §7.1`).
- **SR-5 (wynik negatywny = wynik):** jeśli detektor na mono widzialnej 320×240 nie łapie intruza
  wiarygodnie (ε_FP/f_fov FAIL), to **pełnoprawny wynik NEGATYWNY** (jak P2) — raportuj, nie stroj
  po fakcie kryteriów zamrożonych w §4.

---

## 8. Co NIE wchodzi (zakres jawnie)

- Rdzeń uczony estymatora (GRU/CfC) — zaparkowany (§7 SR-4).
- IR / fuzja modalności — habitat = mono widzialna (R-DIV-2).
- Wiele intruzów / kooperacja / klasyfikacja typu — jeden intruz, detekcja binarna „intruz/nie".
- Zmiana bariery/dynamiki (v_max, R_E, a_brake) — o ile nie wymusi jej OBSERVE (§5.4).

---

## 9. Podsumowanie propozycji

R0.2 dokłada do zaliczonej osłony R0.1 **jeden komponent uczony (detektor)** i **kanał celu ZOH-age**
(semantyka z `RAPORT_P2 §7.1` + wzorzec LiquidSight 3c/G2), oraz **tryb OBSERVE** w osłonie — pod
twardym warunkiem zachowania WSZYSTKICH niezmienników R0.1 (A1, P1a, geofence nadrzędny, 0 padów).
Geofence-nadrzędność nad śledzeniem wynika **z priorytetu automatu** (R-G > R-O), nie z nowej reguły.
Główny pomiar reconu — latencja/Hz/VRAM detektora na TYM sprzęcie z żywym symem — jest **zaplanowany
z dwustronnymi kryteriami zamrożonymi tu**, bo `torch`/`ultralytics` nieobecne w env (nie da się zmierzyć
nieinwazyjnie). **Kluczowa rozbieżność:** kanał 5-dim/ENTRY/sufit-wieku **nie jest w kodzie R0.1** — to
budowa R0.2 (§0 R-DIV-1). Kandydaci GRU/CfC pozostają zaparkowani (osobny PRE tylko przy nazwanym
trybie porażki). **STOP — czeka na ratyfikację przed budową.**
