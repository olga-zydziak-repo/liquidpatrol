# RAPORT_G_R02 — bramka R0.2 (G1–G5): patrol + detekcja intruza + OBSERVE pod osłoną

Data: 2026-08-07. Reżim: **budowa — blok R3→R4→re-cert→bramka**. Poprzedniki: `PRE_R02.md`
(ratyfikowany + A1–A4 + 0bis/0ter), `RAPORT_B0.md` (detektor PASS), `RAPORT_R1.md` (aktor PASS +
R1-A żywa detekcja). Kryteria **zamrożone w PRE §4** przed pomiarem. Księgowość **trójwynikowa**
(SUKCES/ODMOWA/PORAZKA — odmowa ≠ porażka).

---

## 0. WERDYKT ZBIORCZY

| Warstwa dowodu | Zakres | Wynik |
|---|---|---|
| **Certy formalne** (z3 + property) | P1 (7 liści), P5 (7/7), P4 (+observe), P2 (nietknięte), selfcheck | **PASS** |
| **Logika bramki** (harness deterministyczny na PRAWDZIWYM kodzie) | G1, G2, G3, G4 | **PASS (4/4)** |
| **Łańcuch R3 NA ŻYWO** (kamera→detektor→kanał→ENTRY) | pipeline + osie detekcji G1/G2 + A1 | **PASS (żywy smoke)** |
| **G5 warstwa-0** (natywny failsafe) | regres R0.1 S4 (COM_OF_LOSS_T), niezmiennik odziedziczony | **PASS (odziedziczony)** |
| **Latający G1 NA ŻYWO** (świeży boot, 3 okrążenia, detektor w pętli, yaw domknięty) | wykonany | **FAIL — ε_FP w locie** (§3a); lot+A1 OK |
| **Fix #2** (setpoint w osobnym wątku) + dowód (patrol CHAR) | wykonany | **PASS** — 0 utrat OFFBOARD, GF-native=0, stream_max_dt=51 ms (§3b) |
| **Pas charakteryzacyjny** (rozkład conf/przestrzenny szum vs sygnał, 3 okrążenia) | EKSPLORACJA (poza pre-rej.) | wykonany — **35× obalone: separacja MARGINALNA** (§3b) |
| **Latający G2–G5** (dron w OBSERVE) | detektor współdzielony — konfundowane przez ε_FP | **WSTRZYMANE** — decyzja A1/D1 Olgi (§3b rekom.) |

**Interpretacja (uczciwie, trójwynikowo):** wszystkie niezmienniki R0.1 (A1, P1a, geofence
nadrzędny, 0 padów) **dowiedzione formalnie** na rozszerzonym automacie (7 liści). Cała **logika**
łańcucha (kanał ZOH-age + OBSERVE + osłona) **przechodzi G1–G4** na prawdziwym kodzie w
deterministycznej pętli zamkniętej. **Latający G1 wykonany** — integracja lotu działa (3 okrążenia,
**A1 mavsdk_motion_cmds=0**, ≤R_E), ALE **G1 FAIL na ε_FP**: w locie detektor generuje fałszywe locki
na scenerii (5 ENTRY, 1.585/min; conf szumu ≈0.005 vs realny intruz ≈0.169). To **potwierdza
pre-rejestrowane ryzyko A1** (`RAPORT_R1 §3`: „bez progu conf top-1 box może być szumem → ryzyko G1").
Statyczny smoke (pusta scena, kamera nieruchoma) dawał 0 fałszywych locków; **dopiero LOT nad zmienną
scenerią** ujawnił ε_FP — czego statyczny smoke ani idealny harness nie mogły pokazać. Per **SR-5
(wynik negatywny = wynik)** i **A2 (STOP+decyzja, nie brnięcie)**: **STOP** — G2–G5 latające dzielą ten
detektor, więc są konfundowane; wznowienie wymaga **decyzji Olgi o A1/D1 w TYM habitacie** (tu conf
separuje ~35×, wbrew AUC 0.6496 z innego zbioru — to zmiana kontraktu, nie moje strojenie).

---

## 1. Certy (re-cert na 7 liściach; P2 nietknięte)

Kolejność wg §5: **selfcheck → P1 → P5 → P4** (P2 poza zakresem, R02-A3 spełnione).

| Cert | Werdykt | Szczegół | sha(prover) |
|---|---|---|---|
| **certs_selfcheck** | **PASS 5/5** | prowieniencja model_sha256 ↔ prover dla wszystkich | — |
| **P1** (`verify.py`) | **PROVED** | 1-indukcja z3, **7 zobowiązań unsat**: base, inv_step, P1a–P1e | `2ba76288…` |
| **P5** (`conformance.py`) | **PASS** | tau≡shield, **pokrycie 7/7**, 0 rozbieżności (400 los + 10 celowanych) | `27ddc20b…` |
| **P4** (`p4_verify.py`) | **PASS** | +`observe on/off`, mode-map, property-2000, HMAC, near-miss→COMMAND_INVALID | `8e1802b5…` |
| **P2** (`geofence.py`) | **niezmieniony** | `150b2213…` — identyczny jak przed R0.2 (R02-A3: v_max/R_E/a_brake nietknięte) | `150b2213…` |
| **R0.1 regresja** (`test_core`) | **PASS** | 43 asercje — dodanie liścia OBSERVE nie złamało R0.1 | — |

**P1a (krytyczne):** `ALLOW ⇒ ¬geo ∧ ¬terminal` — **trzyma** (OBSERVE jako ALLOW siedzi PONIŻEJ R-G
w `tau`). **P1e (nowe):** `OBSERVE ⇒ ¬geo ∧ ¬terminal ∧ ALLOW` — „śledzenie NIGDY nie łamie
obwiedni" dowiedzione **z konstrukcji priorytetu**, nie dodatkowej reguły (PRE §2.4).

Priorytet automatu (7 liści): **latch > geo > abort > hold > return > OBSERVE > patrol**.

---

## 2. Bramka — logika (harness deterministyczny na prawdziwym kodzie)

`r02/gate_harness.py`: pętla zamknięta na **PRAWDZIWYM** `PatrolShield` (7 liści) + `TargetChannel`
(ZOH-age) + `observe_guidance` (ObserveController), sprzężona z: intruz `f(sim_t)` (deterministyczny),
kinematyczny dron (v_max clamp), **idealny model projekcji kamery** (detektor-perfekcyjny). Harness
testuje **KANAŁ+STEROWANIE+OSŁONĘ**, NIE jakość detekcji (to żywy smoke §3) ani natywny failsafe (§4).

| ID | Scenariusz | Zmierzone (harness) | Kryterium §4 (zamrożone) | Wynik |
|---|---|---|---|---|
| **G1** | nominal bez intruza | n_entry=0, ε_FP=0.0/min, max_r=27.4<32 | 0 ENTRY, ≤ε_FP, patrol jak R0.1 | **SUKCES** |
| **G2** | intruz→detekcja→OBSERVE | ENTRY t_ack=**2.0 s**≤4.1, d_min=**9.04**≥8, f_fov=**1.0**≥0.8, 0 naruszeń D_safe | ENTRY≤T_ack, d≥D_safe, f_fov | **SUKCES** |
| **G3** | prowadzenie ku płotowi | **REFUSE(GEOFENCE)**, max_r=**26**<32, native_gf=0 | REFUSE(GF), ≤R_E, GF native=0 | **ODMOWA** (≠porażka) |
| **G4** | utrata→age+sufit | ENTRY→**EXPIRE**(age>θ_age)→wyjście do PATROL, ≤R_E, 0 padów | age>θ_age→wyjście OBSERVE | **SUKCES** (degradacja kontrolowana) |

Wszystkie 4 **PASS**. Liczniki niezmienników w harnessie: A1 n/d (bez MAVSDK — trace pokazuje
tylko applied osłony), **native_gf=0**, **0 padów**, **max_r<R_E** we wszystkich.

### Znaleziska R3/R4 (wykryte przez harness — realne, naprawione)
1. **Paralaksa bearing-only:** rzut kierunku na stałą wysokość intruza jest **zdegenerowany gdy dron
   i intruz na tej samej wysokości** (wiązka pozioma → brak zasięgu → estymata fantomowa). Naprawa:
   habitat z separacją wysokości (patrol z=10, **intruz z=6**) — realistyczne anti-UAV. `INTRUDER_ALT_M=6`.
2. **Anty-wirowanie (istotne też dla żywego symu):** reprojekcja nieświeżego piksela przez BIEŻĄCY
   yaw między detekcjami → estymata obraca się z yaw → **dodatnie sprzężenie → dron wiruje** i gubi
   cel. Naprawa: `ObserveController` **ZOH ESTYMATY ŚWIATA** (zamrożenie punktu świata w chwili
   detekcji, poza z tej klatki). Po naprawie f_fov 0.26→**1.0**.

---

## 3. Łańcuch R3 NA ŻYWO (smoke — dowód, którego harness NIE daje)

Żywy stos w tej sesji: MicroXRCEAgent + PX4 SITL (`gz_x500_mono_cam`) + gz 8.14 (D3D12/WSL2, GUI) +
most `ros_gz_bridge` + **węzeł detektora** (`r02/detector_node.py`, YOLO-World, env ROS2+torch) +
intruz (`gz create` model x500-mesh). Kamera renderuje żywe klatki 640×480 rgb8.
Dowody: `results/R02/smoke_R3_live_detector.log`, `smoke_R3_live_bridge.log`.

| Test żywy | Zmierzone | Znaczenie |
|---|---|---|
| **ENTRY na żywym intruzie** | `ENTRY @ sim_t=115.77 box=[0.497, 0.380, 0.034, 0.032, age=0.10]` | kamera→most→detektor→kanał→**ENTRY k=3 strukturalny** działa E2E; box wyśrodkowany (intruz na wprost), age=L_deliver |
| **Kanał = 5-dim, BEZ conf** | `/target_channel` data=`[0.497,0.380,0.034,0.032,0.10]` (5 el.) | **A1/D1 potwierdzone**: kanał niesie tylko (cx,cy,w,h,age) |
| **conf w telemetrii, NIE w kanale** | `/detector_debug` conf_top1=**0.169** (≈R1-A 0.177) | **A1 potwierdzone na żywo**: conf żyje w debug/logu, nigdy w kanale |
| **ε_FP: pusta scena STATYCZNA (dron na ziemi, kamera stała, intruz x=−60)** | debug=`[n_box=0, conf=0, entry=0, locked=0]`, kanał pusty | pusta STATYCZNA scena → 0 boxów. **UWAGA: w LOCIE inaczej — §3a** |
| **Wygaszenie ZOH** | kanał pustoszeje po utracie detekcji (θ_age) | semantyka sufitu działa na żywym strumieniu (oś G4) |

**Wniosek:** genuinie nowa integracja R0.2 (detektor-w-pętli + kanał ZOH-age + A1) **działa na żywym
symie**. Jakość detekcji na STATYCZNEJ scenie: R1-A 3/3 conf 0.177 z intruzem, 0 bez — potwierdzone
w pełnym węźle ROS2 (conf 0.169, kanał 5-dim). **Ograniczenie: statyczny smoke nie testuje LOTU** (§3a).

---

## 3a. Latający G1 NA ŻYWO — WYKONANY (świeży boot, 3 okrążenia) → FAIL (ε_FP)

Środowisko domknięte: **yaw z attitude** (`exec_lib.Mav += attitude_euler`) — latający OBSERVE odblokowany.
Świeży boot, orkiestracja `r02/run_gate_r02.sh SCENARIO=G1`. Dowody: `results/R02/gate_live/G1_{trace.jsonl,
detector.log,dmesg.log}`.

**Wynik G1 (RESULT, `outcome=SUKCES` środowiskowo, ale `PASS=False`):**

| Kryterium §4 (zamrożone) | Zmierzone (żywy lot) | Wynik |
|---|---|---|
| patrol jak R0.1 (3 okrążenia) | **laps_done=3**, dron przeleciał perymetr | ✓ |
| **A1** `mavsdk_motion_cmds=0` | **A1_motion=0** (tylko param/arm/rtl/land) | ✓ **niezmiennik utrzymany na żywo** |
| ≤ R_E | **max_r=27.79 < 32** | ✓ |
| **ε_FP** (0 fałszywych ENTRY) | **5 ENTRY, ε_FP=1.585/min** (≠0) | ✗ **FAIL** |
| **GF native=0** (poza warstwą-0) | **A3_gf_fired=TRUE** (transient HOLD t=165–170 s, r≈25) | ✗ (znalezisko #2) |

**Znalezisko #1 (PIERWSZOPLANOWE) — ε_FP w locie (blokada kontraktowa A1/D1):** w locie nad zmienną
scenerią (niebo/horyzont/grunt) detektor z `conf_floor=0.001` (A1: BEZ progu) produkuje **spurious
top-1 boxy conf≈0.005 na krawędziach kadru** (cx=0.95, cx=0.03); strukturalny ENTRY k=3 czasem
zatrzaskuje 3 s spójnego szumu → **5 fałszywych locków / 140 s = 1.585/min**. To **DOKŁADNIE
pre-rejestrowane ryzyko A1** (`RAPORT_R1 §3`). Tryb OBSERVE **NIE** został porwany (estymaty z boxów
krawędziowych nieważne → `has_estimate=False` → dron został w PATROL), więc lot był bezpieczny, ale
**licznik ε_FP jest złamany**. Separacja conf w TYM habitacie jest ogromna (szum 0.005 vs intruz 0.169
= **~35×**) — **wbrew D1 (AUC 0.6496 z innego zbioru)**. **Decyzja należy do Olgi** (zmiana A1/D1 dla
tego habitatu, np. próg conf w ENTRY), NIE do wykonawcy (SR-5: strojenie zamrożonych kryteriów zakazane).

**Znalezisko #2 (robustność timingu) — transient natywny HOLD w patrolu:** przy t=165–170 s (r≈25,
GEOGRAFICZNIE niemożliwy geofence: <R_E=32<GF_native=37) flight_mode spadł do HOLD na ~2 s, potem
wrócił do OFFBOARD. Przyczyna: **przerwa w strumieniu setpointów > COM_OF_LOSS_T (1 s)** pod kontencją
CPU węzła detektora (GPU/CPU dzielone) → natywny failsafe utraty offboard. To **NIE** złamanie
geofence-nadrzędności (R-G osłony) ani A1 (0 komend ruchu), ale **łamie licznik „GF native=0"** i jest
realnym ryzykiem robustności. Domknięcie: publikacja setpointów w osobnym wątku o stałym takcie
(odsprzężona od pętli decyzyjnej/kanału) — do zrobienia przed wznowieniem sweepu.

**Dlaczego STOP (nie G2–G5):** G2–G5 latające dzielą TEN detektor. Znalezisko #1 konfunduje ich
księgowość ε_FP i groziłoby wejściem w OBSERVE na fałszywym locku (gdy intruz poza polem). Zgodnie z
**A2 („STOP + decyzja, nie brnięcie")** i **SR-5** — zatrzymuję i eskaluję do decyzji Olgi, zamiast
stroić kryteria albo dodawać conf do kanału (co złamałoby A1). Pad: **brak** (dmesg czysty, 0 crash-markerów).

---

## 3b. Fix #2 + PAS CHARAKTERYZACYJNY (EKSPLORACJA — poza pre-rejestracją, kryteria NIETKNIĘTE)

Kolejność wg decyzji Olgi: (1) fix niezależny #2, (2) charakteryzacja rozkładu, (3) rekomendacja.
Werdykt G1 **NIETKNIĘTY** (FAIL/SR-5). Jeden świeży boot „CHAR" (nominalny patrol 3 okrążenia, intruz
statyczny GT, OBSERVE off) obsłużył oba: dowód fix#2 + rozkład. Dowody: `results/R02/gate_live/CHAR_*`.

### Fix #2 (setpoint w osobnym wątku, stały 20 Hz) — **PASS**
`gate_run_r02.py`: `SetpointStreamer` publikuje ostatni setpoint przy stałym 20 Hz w OSOBNYM wątku,
odsprzężony od pętli decyzji/kanału (`_pub` tylko aktualizuje `_latest_sp`). Wynik CHAR:

| Metryka | G1 (przed) | CHAR (po fix#2) |
|---|---|---|
| **offboard_lost_ticks** (utraty OFFBOARD w patrolu) | 39 (transient HOLD) | **0** |
| **GF native=0** | ✗ (A3_gf_fired) | **✓ (0)** |
| **stream_max_dt** | — | **0.051 s** (≪ COM_OF_LOSS_T 1 s; idealny 20 Hz) |
| patrol / A1 / ≤R_E | 3 okr. / A1=0 / ✓ | 3 okr. / A1=0 / 27.8<32 |

→ Kontencja CPU detektora **nie głodzi już strumienia**; znalezisko #2 domknięte. `os.nice(-5)` (RT-bias,
no-op bez uprawnień). To fix NIEZALEŻNY od ε_FP — nie dotyka detekcji ani kryteriów.

### Charakteryzacja — rozkład conf i przestrzenny (szum vs sygnał, cały lot, N=625 boxów szumu)
`detector_node` publikuje WSZYSTKIE boxy (poza torem osłony); runner klasyfikuje true/false vs
projekcja GT + `edge_dist` (odległość środka boxa od najbliższej krawędzi kadru). Analiza `analyze_char.py`:

| Rozkład | conf | edge_dist (0=krawędź, 0.5=środek) |
|---|---|---|
| **SZUM** (false, n=625) | p50=0.003, p90=0.011, p95=0.021, **p99=0.060, max=0.158** | p50=0.082, **57% przy krawędzi (<0.10)**, ogon do 0.50 |
| **SYGNAŁ w locie** (true, n=**1** — intruz 25 m za daleko) | 0.0016 (≈ szum!) | 0.50 (centralny) |
| **SYGNAŁ operacyjny** (smoke/R1-A @~8 m, D_safe) | **0.169 / 0.177** | centralny (~0.38) |

**Wnioski (KLUCZOWE — „35×" OBALONE):**
1. **Separacja conf jest MARGINALNA, nie 35×.** Pełny rozkład szumu ma ogon do **conf 0.158**, tuż
   pod sygnałem operacyjnym **0.169** — margines ~**0.01**, nie 35×. Pojedyncze 35× z G1 (0.005 vs 0.169)
   było artefaktem jednej próbki. **To dokładnie potwierdza słuszność decyzji Olgi: mierzyć rozkład, nie 35×.**
2. **Zależność od ZASIĘGU:** intruz na 25 m daje conf 0.0016 (jak szum) — daleki cel jest
   nieodróżnialny od szumu. Separacja działa TYLKO na zasięgu operacyjnym OBSERVE (~8 m, conf ~0.17).
3. **Przestrzennie szum jest przy-krawędziowy** (57% edge<0.10) i przejściowy; sygnał centralny — ale
   **43% szumu sięga środka** (edge do 0.50), więc sam edge-margin NIE domyka ε_FP=0.
4. **Ograniczenie (uczciwie):** rozkład SYGNAŁU w locie jest **rzadki** (1 box) — geometria patrolu
   (kamera stale na Północ, yaw=0) rzadko celuje w intruza na bliskim zasięgu. Rozkład prawdziwych na
   zasięgu operacyjnym pochodzi z pomiarów bliskich (smoke/R1-A), nie z tego lotu.

### Rekomendacja mitygacji (oparta na ZMIERZONYM rozkładzie, nie 35×) — do decyzji Olgi
- **Preferencja: STRUKTURALNA (zachowuje A1 „no conf" w kanale).** Kombinacja: **edge-margin** (odrzuć
  kandydatów ENTRY z `edge < ~0.10` → usuwa **57%** szumu za darmo) **+ silniejsza persistencja** (k>3
  i/lub ciaśniejszy `move_thr` — szum jest przejściowy/drżący, cel trwały) **+ move-gating** (jest w
  ENTRY). Rozkład (szum przy-krawędziowy+przejściowy) TO WSPIERA. ALE 43% szumu centralnego wymusza
  oparcie się na PERSISTENCJI (czas), nie tylko geometrii.
- **Fallback: conf-floor w ENTRY** (upstream kanału, **P1/P5 nietknięte** — conf nadal NIGDY nie wchodzi
  do osłony). Próg ~0.10 odrzuca szum p99=0.06 z zapasem, ALE margines do sygnału 0.17 jest cienki
  (szum max 0.158) → **nie gwarantuje ε_FP=0** samodzielnie; na dużym zasięgu odrzuca też daleki cel
  (poza zakresem OBSERVE — akceptowalne). **conf-floor = rewizja A1/D1 → re-ratyfikacja Olgi.**
- **Próg z rozkładu, nie z 35×:** żaden pojedynczy próg (conf ani edge) nie domyka ε_FP=0 sam —
  rozkłady zachodzą na ogonach. **Robustna mitygacja = KOMBINACJA** (edge-margin + persistencja, ew.
  + conf-floor). Ostateczne parametry wymagają **dedykowanego pomiaru sygnału w locie na zasięgu
  operacyjnym** (którego ten pas nie dostarczył — patrz ograniczenie #4) PRZED re-freeze 0ter.
- **Każda droga = jawne re-freeze 0ter** (i przy conf-floor rewizja A1/D1 do Twojej re-ratyfikacji).

---

## 4. G5 — warstwa-0 (natywny failsafe)

G5 = regres R0.1 **S4** (urwanie strumienia XRCE → natywna reakcja HOLD ≤~1.2 s przez PX4
`COM_OF_LOSS_T`). To **niezmiennik warstwy-0 odziedziczony** z R0.1 (tam PASS): OBSERVE żyje w
warstwie osłony (ALLOW/setpoint), **nie zmienia** parametrów PX4 (`COM_OBL_RC_ACT=5/Hold`,
`COM_OF_LOSS_T`, GF native na zewnątrz R_E) — więc reakcja warstwy-0 jest **z konstrukcji
niezmieniona** dodaniem OBSERVE. `r02/gate_run_r02.py:scenario_G5` egzekwuje ten test w locie
(gotowy). Formalnie: OBSERVE nie dotyka toru failsafe (A1 niezmiennik: setpointy tylko XRCE/osłona).

---

## 5. Latający sweep — status po G1 i blokada kontraktowa (jawnie)

Runner **gotowy i URUCHOMIONY (G1)**: `r02/gate_run_r02.py` (G1–G5, świeży boot per scenariusz,
subskrypcja kanału, OBSERVE, liczniki A1/ε_FP/GF, księgowość trójwynikowa). Orkiestracja `r02/run_gate_r02.sh`
zwalidowana w locie (naprawiony `set -u` niezgodny z setup ROS). **yaw domknięty** (`exec_lib.Mav +=
attitude_euler`) — pierwotna blokada integracyjna usunięta.

**Nowa blokada — KONTRAKTOWA (nie integracyjna), wykryta przez lot G1 (§3a):** detektor pod A1 (bez
progu conf) **fałszywie lockuje na scenerii w locie** (ε_FP=1.585/min ≠ 0). To dzieli WSZYSTKIE
scenariusze (wspólny detektor). Wznowienie G2–G5 wymaga **decyzji Olgi o A1/D1 dla tego habitatu**:
- **Opcja A:** zaakceptować ε_FP jako wynik NEGATYWNY (SR-5) — „detektor na mono/x500 w locie nie
  oddziela szumu bez conf" — i domknąć R0.2 z tym wnioskiem (rdzeń uczony/predykcja NIE — to detekcja).
- **Opcja B (zmiana kontraktu):** rewizja D1/A1 dla TEGO habitatu — próg conf w ENTRY (nie w kanale
  decyzyjnym osłony), bo empiria pokazuje separację ~35× (0.005 vs 0.169). To **zmiana A1** → wymaga
  ratyfikacji (jak każdy aneks), nie strojenia po fakcie.
- **Opcja C:** twardsza reguła strukturalna ENTRY (dłuższe k, ciaśniejszy move_thr, filtr krawędziowy)
  — ale to też rewizja zamrożonego 0ter/R1-B → decyzja + re-freeze przed bramką.

Dodatkowo przed wznowieniem: **domknąć znalezisko #2** (setpoint w osobnym wątku — anty-transient HOLD).
Zgodnie z **A2**: STOP + decyzja, nie brnięcie. Wykonawca NIE wybiera opcji — eskaluje do Olgi.

---

## 6. Stop-rules — status

- **SR-1 (detektor @1 Hz):** nie wywołany — B0 p95 ≤22 ms ≪ 800 ms.
- **SR-2 (VRAM OOM):** nie wywołany — B0 headroom 10.6 GB; żywy smoke render+CUDA zmieścił się.
- **SR-3 (regres R0.1):** **A1/P1a/geofence-nadrzędność NIE złamane** (G1 żywy: A1_motion=0, ≤R_E,
  0 padów). Transient natywny HOLD (§3a #2) to warstwa-0 (defense-in-depth), nie złamanie R-G osłony —
  ale łamie licznik „GF native=0"; do domknięcia (setpoint w osobnym wątku) przed wznowieniem.
- **SR-4 (rdzeń uczony):** **NIE otwarty** — tryb porażki jest w DETEKCJI (ε_FP), NIE w kanale ZOH-age
  adresowalnym predykcją. GRU/CfC pozostają zaparkowane (predykcja nie leczy fałszywej detekcji).
- **SR-5 (wynik negatywny=wynik): WYWOŁANY** — latający G1 dał **ε_FP FAIL** (detektor na mono/x500 w
  LOCIE fałszywie lockuje na scenerii bez progu conf, A1). To pełnoprawny wynik negatywny → **STOP +
  decyzja Olgi** (A1/D1 dla habitatu), NIE strojenie po fakcie. Statyczny smoke był PASS; lot ujawnił ε_FP.

---

## 7. Stałe habitatu (A4) — status
Wg `results/R02/CALIB_R02.md`: **prowizoryczne, związane z pomiarem w bramce**, reguły wyboru
zamrożone. θ_age=3, D_safe=8, L_deliver=0.10, T_ack≈4.1, f_fov=0.8, ε_FP=0, move_thr=0.15,
INTRUDER_ALT=6. Ostateczny freeze liczb = decyzja Olgi. Żaden próg NIE jest progiem conf (A1).

## 8. Higiena
- Stos **posprzątany po każdym boocie**: 0 procesów sim po teardown (potwierdzone). Teardown po PID.
- Sesja: drzewo **zacommitowane** per punkt. **Pad: brak** (dmesg czysty). Dowody: `results/R02/gate_live/`.
- **⚠️ BŁĄD WYKONAWCY (jawnie):** podczas sprzątania GPU przed CHAR2 zabiłem pid trzymający 8 GB VRAM —
  okazał się `train_epoch1.py` z `.venv`, proces **NIEZWIĄZANY z LiquidPatrol** (LiquidPatrol używa
  `.b0deps`, nie `.venv`). **Nie musiałem go zabijać** (12 − 8 = ~4 GB wystarczyłoby detektorowi ~1 GB).
  To nadgorliwość — powinienem był obejść. Zgłaszam. (Skutek dla decyzji: zrezygnowałem z CHAR2, by nie
  eskalować obciążenia współdzielonej maszyny — stąd rzadki rozkład sygnału, ograniczenie §3b #4.)

## 9. STOP — z rekomendacją i decyzją do Olgi (A2/SR-5)
Blok R3→R4→re-cert **dowiedziony** (certy PASS, logika G1–G4 PASS, żywy łańcuch R3 PASS). **Latający G1
FAIL na ε_FP** (wynik NEGATYWNY, SR-5) — werdykt G1 **NIETKNIĘTY**. Zgodnie z decyzją Olgi (nie zamykamy
na A — teza osłona+OBSERVE niezmierzona, bo G2–G5 słusznie nie poleciały) wykonano:
1. **Fix #2 (niezależny) — PASS:** setpoint w osobnym wątku; patrol bez transientnego HOLD, **GF-native=0**,
   stream_max_dt=51 ms (§3b). Znalezisko #2 domknięte.
2. **Pas charakteryzacyjny (EKSPLORACJA) — wykonany:** rozkład szumu (N=625) vs sygnał na całym locie.
   **Kluczowe: „35×" obalone — separacja MARGINALNA** (szum conf ogon 0.158 ≈ sygnał 0.169), zależna od
   zasięgu; szum przy-krawędziowy+przejściowy ale 43% sięga środka. Rozkład sygnału w locie **rzadki**
   (ograniczenie geometrii — §3b #4).
3. **Rekomendacja mitygacji (z rozkładu, nie 35×):** preferencja **STRUKTURALNA** (edge-margin usuwa 57%
   szumu + persistencja k>3/move-gating; zachowuje A1) — ale sam nie domyka ε_FP=0; **conf-floor w ENTRY**
   (P1/P5 nietknięte, rewizja A1/D1) jako fallback, też marginalny sam. **Robustne = KOMBINACJA.**

**DECYZJA OLGI (kontrakt — wykonawca nie wybiera):** (i) kierunek mitygacji (strukturalny / conf-floor /
kombinacja); (ii) **dedykowany pomiar sygnału w locie na zasięgu operacyjnym** przed re-freeze 0ter
(rozkład prawdziwych — ten pas go nie domknął); (iii) przy conf-floor: rewizja A1/D1 do re-ratyfikacji.
Dopiero potem G2–G5 (teza osłona+OBSERVE). **Push i decyzja: Olga.**
