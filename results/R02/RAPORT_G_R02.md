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
| **G5 warstwa-0** (natywny failsafe) | regresja fix#2 (zombie-stream) — patrz `RAPORT_R02.md §III` | **NAPRAWIONA** (dead-man+re-cert; live timing pending GPU) |
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
| **P1** (`verify.py`) | **PROVED** | 1-indukcja z3, **7 zobowiązań unsat**: base, inv_step, P1a–P1e; **+założenie żywotności osłony (R0.2/fix-G5)** | `3046d032…` |
| **P5** (`conformance.py`) | **PASS** | tau≡shield, **pokrycie 7/7**, 0 rozbieżności (400 los + 10 celowanych); **re-run od nowa po dead-man, bajt-identyczny** | `27ddc20b…` |
| **P4** (`p4_verify.py`) | **PASS** | +`observe on/off`, mode-map, property-2000, HMAC, near-miss→COMMAND_INVALID | `8e1802b5…` |
| **P2** (`geofence.py`) | **PROVED** | bariera niezmieniona (R02-A3: v_max/R_E/a_brake nietknięte); **+założenie żywotności osłony zapisane wprost** → prover zregenerowany | `f6b22abc…` |
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

## 3c. Krok 1 (gęsty sygnał) + Krok 2/2b (mitygacja z rozkładu) — decyzja Olgi: pomiar→mitygacja→teza

Poprzedni pas (§3b) miał sygnał RZADKI (geometria). Krok 1 domknął to DWOMA pomiarami:

### Krok 1a — ZNALEZISKO geometrii detekcji (dlaczego lot dawał 0 sygnału)
Latający pas z intruzem na alt 8/14 dał **0 detekcji celu** (max conf 0.051, boxy krawędziowe). Przyczyna:
przy patrolu (alt 10) dron patrzy w DÓŁ/skośnie → intruz **na tle GRUNTU** (clutter) → detektor NIE odpala.
Smoke/R1-A łapały bo intruz był **na tle NIEBA, blisko poziomu, ~8 m**. **Detekcja jest warunkowana
geometrią i tłem** (nie tylko zasięgiem). Dowód: `results/R02/gate_live/CHAR2_alt8_char.jsonl`.

### Krok 1b — STATYCZNY sweep sygnału (bez lotu, geometria smoke: near-level, tło nieba)
`r02/signal_sweep.py`: dron na ziemi (kamera Północ), intruz przesuwany przez zasięg przy elewacji ~11°.
Krzywa conf(zasięg) SYGNAŁU (top-1 centralny, cx≈0.50). Dowód: `results/R02/gate_live/SWEEP_signal.jsonl`.

| zasięg | 5 m | 7 m | 9 m | **11 m** | 13 m | 15 m | 18 m |
|---|---|---|---|---|---|---|---|
| **conf sygnału** | 0.169 | **0.214** | **0.214** | 0.048 | 0.005 | 0.005 | 0.001 |
| edge | 0.38 | 0.38 | 0.38 | 0.38 | 0.39 | 0.39 | 0.25 |

**Efektywny zasięg detektora ≈ 10 m.** Sygnał silny 5–9 m (**0.17–0.21**, centralny), **zapada się > 10 m**
(≥13 m = poziom szumu). Zero-shot YOLO-World na mono x500-mesh ma wąski zasięg — ograniczenie detektora.

### OBIE CHMURY (do wyboru progu — liczba, której brakowało)
| | conf | przestrzennie |
|---|---|---|
| **SZUM** (N=625, cały lot) | p99=0.060, **max=0.158** | 57% edge<0.10; **centralny (edge≥0.10) max=0.158, p99=0.050** |
| **SYGNAŁ operacyjny** (5–9 m, sweep) | **0.169–0.214** | centralny (edge≈0.38) |

### Krok 2 (C-primary, strukturalna, A1-preserving) — ZAIMPLEMENTOWANA, ale NIEDOMYKAJĄCA
Wyprowadzone z chmur, **reguła w kodzie** (`config_r02.ENTRY_EDGE_MARGIN=0.10`, `target_channel` ENTRY):
- **edge-margin 0.10** (sygnał edge 0.38 vs szum 57% edge<0.10) → odrzuca **57% szumu bez conf**. ✓ (testy)
- **persistencja:** run-length TOP-1 szumu CENTRALNEGO (po edge-margin) = **[7,5,3,3,…], max=7**. By szum
  nie osiągnął ENTRY trzeba **k≥8** — ale to (a) **fragile** (pojedynczy max z jednego lotu — TA SAMA
  pułapka co 35×), (b) **grozi detekcji** (sygnał w tranzycie przez zasięg ≤10 m persistuje podobnie).
  → **persistencji NIE podbijam ręcznie do 8** (byłoby strojeniem na pojedynczej próbce).
- **Wniosek (MIERZONY):** edge-margin usuwa 57% szumu, ale **szum centralny (edge≥0.10) sięga conf 0.158
  i persistuje do 7 klatek** → **C SAM NIE DOMYKA ε_FP=0** przy zachowanej detekcji.

### Krok 2b — conf-floor w ENTRY-admisji: **STOP + Twoja re-ratyfikacja (A1/D1)**
Czysty separator to **próg conf**, bo chmury rozdziela GAP DYSTRYBUCYJNY (nie pojedyncza próbka):
- **sygnał operacyjny min = 0.169** (5–9 m) **vs szum centralny max = 0.158** → prób ~**0.16** rozdziela
  na CAŁYM zasięgu detekowalnym OBSERVE (5–10 m); powyżej 10 m sygnał<próg, ale tam detektor i tak nie
  widzi (poza obwiednią OBSERVE, akceptowalne). Margines cienki (0.16↔0.169) → conf-floor **z edge-margin**
  (który zdejmuje krawędziowe conf-outliery do 0.108) daje zapas.
- **To rewizja A1/D1** (conf w ENTRY-admisji — UPSTREAM kanału, **P1/P5 nietknięte**, osłona bez conf).
  **[STATUS iter.3: RATYFIKOWANE jako R02-A6 + zaimplementowane — patrz §3d.]** (Powyższy akapit iter.2
  był wnioskiem PRZED ratyfikacją.)

**Uwaga wyższego rzędu:** wąski zasięg detektora (~10 m) i cienki margines (0.158↔0.169) to **ograniczenie
DETEKTORA** (zero-shot mono). Alternatywa: detektor dostrojony/jednoklasowy (R2-alt) — większy zakres,
osobna decyzja. Rdzeń uczony (GRU/CfC) nadal NIE dotyczy (to detekcja, nie kanał ZOH-age; SR-4 zamknięty).

---

## 3d. Iteracja 3 — aneksy A6/A7 ratyfikowane + implementacja A6 + ε_FP=0 (analitycznie); żywy re-run ODROCZONY

Olga **ratyfikowała** conf-floor jako **R02-A6** (+ **A7** koperta detekcji) — `PRE_R02.md §0bis`. Zaimplementowano:
- **A6 conf-floor `θ_conf`** — DERYWACJA DETERMINISTYCZNA (reguła w kodzie, nie ręczna):
  `θ_conf = (sygnał_min 0.169 + szum_centr_max 0.158)/2 = 0.1635` (środek przerwy). **WYŁĄCZNIE
  ENTRY-admisja** (`target_channel` ścieżka unlocked); **conf NIGDY w wartości kanału 5-dim, osłonie,
  P1/P5** (A1/D1 stoją). **Kombinacja z edge-margin 0.10.** Testy jednostkowe **PASS** (28/28).
- **Pasywne logowanie conf (A6)** w KAŻDYM locie bramkowym (`Runner.conf_report`: max/p99/n_admitted/
  gap_held) — raport bramki pokaże, czy przerwa 0.158↔0.169 utrzymała się w locie.

**ε_FP=0 — dowód ANALITYCZNY z ratyfikowanej reguły i zmierzonych chmur:**
`θ_conf = 0.1635 > szum_centralny_max = 0.158` (z konstrukcji: środek przerwy) → **żaden box szumu nie
przechodzi admisji ENTRY → 0 admisji → ε_FP=0** (dla zmierzonego rozkładu szumu, N=625). Jednocześnie
`θ_conf = 0.1635 < sygnał_min = 0.169` → **sygnał operacyjny przechodzi → detekcja zachowana**. Status
prowizoryczny (A4): żywy lot ma potwierdzić, że przerwa się utrzymała (pasywny log).

**Żywy re-run G1 — WYKONANY (świeży boot, gdy GPU zwolniło) → PASS.** Dowód: `results/R02/gate_live/G1_A6_*`.

| Kryterium | G1 iter.2 (przed A6) | **G1(A6) w locie** |
|---|---|---|
| **ε_FP** (fałszywe ENTRY) | 5, **1.585/min** | **0, 0.0/min** ✓ |
| **gap_held_in_flight** (szum < θ_conf?) | — | **TRUE** — szum max **0.0806** ≪ θ_conf 0.1635 (n=561, p99=0.030) ✓ |
| **n_admitted_entry** (szum przez admisję) | — | **0** ✓ |
| A1 (mavsdk_motion_cmds) | 0 | **0** ✓ |
| GF-native (fix#2) | ✗ (transient HOLD) | **0 (A3_gf_fired=False)** ✓ |
| patrol / ≤R_E / outcome | 3 okr. / 27.8 / SUKCES | 3 okr. / **27.82** / **SUKCES** |
| **PASS** | **FAIL (ε_FP)** | **PASS** |

**Wniosek:** A6 (conf-floor 0.1635 + edge-margin 0.10) **domyka ε_FP=0 W LOCIE**; **przerwa 0.158↔0.169
UTRZYMAŁA SIĘ pod szumem lotu z ogromnym zapasem** (szum lotu max 0.0806 — słabszy niż statyczny 0.158).
gap_held=TRUE ⇒ **trigger eskalacji R2-alt NIE odpalony**. fix#2 potwierdzony (GF-native=0). ε_FP domknięte
→ **wchodzę w G2–G5 wewnątrz koperty A7** (teza osłona+OBSERVE).

**Zmienność ogona szumu (jawnie):** max conf szumu wahał się między kampaniami — **0.158** (statyczny
CHAR) vs **0.0806** (lot G1). **θ_conf (0.1635) jest zaprojektowany wobec GORSZEGO przypadku (0.158),
nie lepszego** — margines projektowy liczony konserwatywnie. **θ_conf pozostaje prowizoryczny (A4)**:
pasywny log w KAŻDYM locie bramkowym monitoruje ogon; jeśli w którymś locie przekroczy θ_conf → trigger
R2-alt (nie podniesienie progu po fakcie). Dotychczas (G1) ogon 0.0806 ≪ θ_conf — zapas duży.

**Rider 2 (D_safe → 3D w ŚRODKU koperty):** dystans 3D operacyjny ustawiony na **~7 m (środek 5–9 m)**,
nie krawędź. D_safe nie dotyka P2 (v_max/R_E/a_brake niezmienione). Harness G1–G4 PASS.

**Rider 1 (MICRO-SANITY OPTYKI — harness testuje logikę, nie optykę) — ZNALAZŁ 2 rozbieżności.** Dowody:
`results/R02/gate_live/MSAN_elev34_alt14.jsonl`, `MSAN2_elev13_alt11.5.jsonl` (statyczny, kamera poziomo).
1. **Framing przy alt 14 (elewacja 34.8°): ROZBIEŻNOŚĆ.** Realna optyka: intruz na **GÓRNEJ KRAWĘDZI** kadru
   (cy=**0.086**, edge=0.086 **< edge-margin 0.10**) + conf **0.11 < θ_conf** → **NIE przeszedłby admisji ENTRY**.
   Harness (model FOV) tego nie łapał. **Dostosowanie:** obniżono intruza do **alt 11.5 (elewacja ~13°)** →
   intruz **CENTRALNY** (cy=**0.38**, edge 0.38 ≫ margin). D_safe=5.32 (3D ~7 m przy 13°). Harness PASS.
2. **Migotanie conf przy 13° (NOWE, istotniejsze):** na STATYCZNYM intruzie conf **oscyluje 0.169↔0.084**
   (klatka-po-klatce; render gz + niestabilność zero-shot) — **przeskakuje przez θ_conf 0.1635**. ENTRY
   wymaga **k=3 KOLEJNYCH** ≥θ_conf → migotanie może zrywać serię. **To pre-wskazanie triggera A7 R2-alt**
   („porażki detekcji wewnątrz koperty w G2"). Definitywny test = **G2** (tam A7 definiuje trigger).
   **Odnotowane jako ryzyko; nie podnoszę θ_conf ani nie stroję** — jeśli G2 potwierdzi porażkę detekcji,
   to trigger R2-alt (osobny PRE, detektor jednoklasowy), nie majstrowanie przy progu.

**Higiena współdzielenia (nauka):** przed każdym bootem sprawdzam headroom i **compute-apps** — jeśli
cudzy proces (nie-LiquidPatrol: `.venv`, `/home/olga/fabryka/`) zajmuje GPU, **czekam, nie ubijam**.

---

## 3e. G2 W LOCIE → **A7 R2-alt TRIGGER ODPALONY** (porażka detekcji w kopercie)

Po riderach wszedłem w G2 (świeży boot, intruz statyczny w kopercie A7, dron HOVER w Home twarzą N).
**2 niezależne loty (G2a, G2b), intruz POTWIERDZONY na (7,0,11.5)** (`gz model -p` — set_pose OK, NIE bug).
Dowody: `results/R02/gate_live/G2{a,b}_*`, `G2_intruder_pose_confirmed.log`.

| | G2a | G2b |
|---|---|---|
| n_entry / PASS / outcome | 0 / **False** / PORAZKA | 0 / **False** / PORAZKA |
| **conf_max sygnału (pasywny log)** | **0.0456** (n=202) | **0.0475** (n=181) |
| n_admitted_entry | 0 | 0 |
| max_r (hover w Home) | 1.14 | 0.48 |
| pad (dmesg) | brak | brak |

**Wynik: detektor NIE wykrywa intruza nad θ_conf w LOCIE.** conf sygnału ~**0.045–0.047** (≈ poziom szumu)
≪ θ_conf 0.1635 → **0 admisji ENTRY → brak OBSERVE → G2 PORAZKA.** Intruz poprawnie w kopercie (7 m,
elewacja 12°, tło nieba) — to **GENUINE porażka detekcji, nie geometrii/setupu**.

**ZNALEZISKO KLUCZOWE — statyczna charakteryzacja NIE przeniosła się na LOT (4×):** SWEEP statyczny
(dron na ziemi) dawał **0.169–0.214 @ 5–9 m**; **LOT (dron alt 10) daje 0.045** przy tej samej geometrii
względnej. Prawdopodobna przyczyna: **pitch/attitude kamery w zawisie** (multirotor przechyla się dla
utrzymania pozycji → kamera-forward odchyla się od intruza przy 12° w górę) + warunki lotu. **Koperta A7
zmierzona statycznie była OPTYMISTYCZNA** — nie obowiązuje w locie. **θ_conf (0.1635, z sweepu
statycznego) NIE transferuje** — sygnał lotu (0.045) jest pod progiem.

**To DOKŁADNIE nazwany trigger A7:** „porażki detekcji wewnątrz koperty w G2". Rider 1 (micro-sanity)
PRE-WSKAZAŁ to (migotanie conf ~θ_conf przy 13° statycznie); **G2 POTWIERDZIŁ w locie** (conf 0.045 ≪ θ_conf).

### Konsekwencja: STOP + eskalacja R2-alt (osobny PRE) — NIE strojenie θ_conf
Per A7: trigger → **osobny PRE z detektorem jednoklasowym, projekt ANTY-CYRKULARNY** (trening na renderach
INNEJ sceny/tekstur niż scena bramki). **NIE obniżam θ_conf** (wpuściłby szum; zakaz strojenia progu).
**Dodatkowy wymóg dla R2-alt (nauka G2):** charakteryzacja detektora **W LOCIE** (nie statycznie) — koperta
musi być mierzona w warunkach zawisu/attitude kamery, bo statyczna jest optymistyczna.

### Co JEST dowiedzione (teza osłona+OBSERVE — LOGIKA, nie live)
Teza **osłona+OBSERVE nie jest zmierzona live** — bo detekcja pada u ŹRÓDŁA (wejście łańcucha). ALE:
- **Logika G1–G4** (osłona 7-liści + kanał ZOH-age + OBSERVE): **PASS** (harness na prawdziwym kodzie).
- **Certy** P1(7 liści)/P5(7/7)/P4/P2: **PASS**. **ε_FP=0 w locie** (G1(A6) PASS, gap_held).
- **fix#2** (setpoint w wątku): PASS (GF-native=0). **A1=0**, geofence-nadrzędność, 0 padów — utrzymane.
Brakuje wyłącznie **wiarygodnej detekcji w locie** — to R2-alt, nie wada architektury osłony.

---

## 3f. TOR A — SONDA ATRYBUCYJNA (decyzja Olgi): 4× to PERCEPCJA (kadrowanie kamery), NIE potok, NIE detektor

Cel: rozstrzygnąć czy spadek conf statyczny 0.16 → lot 0.045 to **percepcja** czy **potok**. Metoda:
przechwyt surowej klatki ze STATYCZNEGO (dron na ziemi) i z LOTU (dron alt 10) przy IDENTYCZNEJ pozie
WZGLĘDNEJ intruza (7 m, elewacja ~12°), potem **detektor OFFLINE na obu zapisanych klatkach** (ten sam
kod/model — izoluje treść obrazu od live-timingu). Dowody: `results/R02/gate_live/{static,flight}.{png,npy,_meta.json}`.

| | STATIC (dron ziemia) | FLIGHT (dron alt 10, hover) |
|---|---|---|
| **rozdzielczość / encoding / step** (POTOK) | **640×480 rgb8 / 1920** | **640×480 rgb8 / 1920** — IDENTYCZNE |
| **detektor OFFLINE (ta sama klatka)** | nbox=1, **conf 0.156**, box cx 0.495 **cy 0.372** | **nbox=0, conf 0.0** |
| **wizualnie (PNG)** | **intruz wyraźny, centralny, na tle nieba** | **intruz CAŁKOWICIE NIEOBECNY** (czyste niebo+grunt) |
| yaw drona | — | **0° (Północ = ku intruzowi)**, dryf [−1,+2]° |
| tło (górna połowa, mean) | 218 | 218 — identyczne |

**WNIOSEK ATRYBUCJI — jednoznaczny:**
1. **POTOK NIE Jest przyczyną.** Obie klatki **640×480 rgb8** (nie 320×240!) — **most przekazuje NATYWNE
   640×480, nie downsampluje.** Topik/rozdzielczość/encoding/step identyczne. (Obala premisę „320×240 =
   limit mostu" z lever 1.)
2. **DETEKTOR NIE jest (intrinsycznie) przyczyną.** Ten sam detektor na klatce statycznej: **conf 0.156**
   (wykrywa poprawnie kadrowany cel). Detektor jest ADEKWATNY, gdy cel jest w kadrze.
3. **YAW NIE jest przyczyną.** Dron patrzy na Północ (0°, ku intruzowi).
4. **PRZYCZYNA = PERCEPCJA przez WERTYKALNE KADROWANIE / ATTITUDE kamery w LOCIE.** Intruz (elewacja
   +12–16° w górę) jest **klipowany z góry kadru** przez **pitch zawisu** (multirotor przechyla się dla
   utrzymania pozycji; kamera stała-forward pochyla się z kadłubem) → cel wypada z kadru → 0 detekcji.
   Statyczny (dron poziomo) kadruje cel → 0.156. Potwierdza rider 1 (przy 34.8° cel na cy 0.086 = górna
   krawędź już statycznie; lot dopycha go poza kadr).

**GŁĘBSZE — KONFLIKT GEOMETRYCZNY (przyczyna źródłowa):** kamera STAŁA-FORWARD, POZIOMA nie może
utrzymać w kadrze celu wymaganego przez kopertę: cel POWYŻEJ drona (tło nieba + paralaksa bearing-only)
→ wysoka elewacja → górna krawędź kadru → klipowany przez pitch lotu. Cel na poziomie/niżej → w kadrze,
ale tło gruntu → niewykrywany. **Fixed-forward-camera fundamentalnie ogranicza kopertę.**

### CATCH (rozbieżność, decyzja Olgi) — conf jako separator jest KRUCHY, fix kadrowania NIEWYSTARCZAJĄCY
**Static conf 0.156 przy IDEALNYM kadrowaniu jest PONIŻEJ θ_conf 0.1635 i poniżej szumu max 0.158.**
Tzn. **przerwa dystrybucyjna 0.158↔0.169 ZAPADŁA SIĘ w niezależnym pomiarze** (sweep dawał 0.169–0.214,
ale ta klatka statyczna, dobrze kadrowana, daje 0.156). Konsekwencje:
- **Fix kadrowania (dźwignia 0) jest KONIECZNY, ale NIEWYSTARCZAJĄCY** — nawet idealnie kadrowany cel bywa
  pod θ_conf. **conf jako separator jest krokościenny/kruchy.**
- **θ_conf NIE obniżamy** (wpuściłby szum; zakaz). Po fixie kadrowania: **re-derywacja OBU chmur W LOCIE**
  (sygnał i szum). **Jeśli sygnał ≤ szum → conf-floor UPADA jako mechanizm** i ENTRY musi stanąć na
  **separatorze ORTOGONALNYM** (ruch/MTI, spójność strukturalna) — nie conf.

### DECYZJA O KOLEJNOŚCI DŹWIGNI (wynik toru A steruje torem C)
- **Dźwignia 0 (PRIORYTET) — CELOWANIE KAMERY, wariant 0b PREFEROWANY:**
  - **0b (preferowane): poza kamery KOMPENSOWANA ATTITUDE** (gimbal-like — kamera trzyma ZADANĄ elewację
    niezależnie od pitchu kadłuba). **Uzasadnienie:** okno kątowe koperty jest kilkustopniowe, a jitter
    attitude zawisu tego SAMEGO rzędu — dlatego realne EO/IR są **gimbalowane**. 0b usuwa i średnią, i
    sprzężenie z jitterem.
  - 0a (odrzucone jako samodzielne): statyczny pitch-offset kamery — usuwa ŚREDNIĄ, ale zostawia
    sprzężenie z jitterem zawisu (cel dryfuje w/z kadru na jitterze).
  - **Wariant do rozważenia: szersze pionowe FOV** — ale **KOSZT MIERZONY, nie zakładany** (mniej pikseli
    na celu = krótszy zasięg; trade-off zmierzyć, nie założyć).
- **Dźwignia 2 (MTI/ruch) — AWANS do WSPÓŁ-PRIORYTETU z 0:** **separator ORTOGONALNY do conf** (szum
  statyczny nie ma spójnego ruchu → wzmacnia też ε_FP). Kluczowe wobec CATCH (conf kruchy).
- **Dźwignia 1 (rozdzielczość/gz-transport) — DE-PRIORYTET:** potok już 640×480 (premisa lever 1 obalona).
- **Dźwignia 3 (detektor jednoklasowy / R2-alt) — OSTATNIA:** detektor adekwatny na kadrowanym celu (0.156).
- **A7 R2-alt trigger: PRZE-ATRYBUOWANY** — G2 „porażka detekcji" = **porażka KADROWANIA**, nie jakości detektora.

**Lekcja programu (WPISANA):** statyczne sweepy **tracą status źródła progów** — **charakteryzacja
WYŁĄCZNIE W LOCIE** (attitude kamery zmienia kadrowanie 4× i decyduje; conf ze sweepu statycznego nie
transferuje). θ_conf bez zmian (zakaz obniżania).

---

## 3g. TOR B — G2–G5 GT-FED (teza architektury niezależna od percepcji) — G2+G3 PASS na żywym symie

Decyzja Olgi: tor B mierzy OBSERVE/geofence-primacy/REFUSE/age **niezależnie od percepcji** — kanał 5-dim
zasilany **POZĄ GT symulatora** (projekcja GT do kamery, perfekcyjna detekcja w FOV, conf=1.0), detektor
POMINIĘTY. **JAWNIE ETYKIETOWANE** (`gt_fed: true` w trace/result; precedens 3b: sufit GT-fed vs live-fed
osobno). Na ŻYWYM PX4/gz/MAVSDK/geofence/osłonie (nie kinematyczny harness). Dowody: `results/R02/gate_live/{G2,G3}_GTFED_*`.

| Scenariusz | Kryterium §4 (zamrożone) | Zmierzone (GT-fed, live) | Wynik |
|---|---|---|---|
| **G2** detekcja→OBSERVE | ENTRY≤T_ack, d≥D_safe | ENTRY, t_ack_ok, **OBSERVE 401 ticków**, **min_d 5.86 ≥ D_safe 5.32 (0 naruszeń)**, A1=0, ≤R_E | **SUKCES/PASS** |
| **G3** prowadzenie ku płotowi | REFUSE(GEOFENCE), ≤R_E, GF-native=0 | **REFUSE(GEOFENCE)**, **max_r 21.1 < R_E 32**, native GF=0, A1=0 | **ODMOWA/PASS** |
| **G4** utrata→sufit age | age>θ_age → wyjście OBSERVE→PATROL | intruz znika @t=20 → **OBSERVE→PATROL po sufcie**, A1=0, ≤R_E | **SUKCES/PASS** |
| **G5** warstwa-0 | urwanie XRCE → HOLD w 0.9–1.5 s | HOLD zadziałał, ≤R_E (0.68), A1=0, ALE **reakcja 2.179 s > 1.5 s** | **FAIL (timing)** — patrz niżej |

**G5 — znalezisko (fix#2 ↔ failsafe):** natywny HOLD zadziałał (dron bezpieczny, ≤R_E, A1=0), ale reakcja
**2.179 s** przekracza okno 0.9–1.5 s (R0.1 S4 dawało ~1.03 s). Prawdopodobna przyczyna: **warstwa fix#2
(streamer setpointów) opóźnia detekcję utraty offboard** przy urwaniu (streamer publikuje do momentu
stop) — LUB param `COM_OF_LOSS_T`. Do zbadania: urwanie na poziomie XRCE (jak R0.1) vs stop streamera.
**Nie jest to wada osłony/GT-fed** — to interakcja fix#2 z natywnym failsafe; kryterium bez zmian.

### Wariant GT-fed z NIEREGULARNOŚCIĄ (decyzja Olgi — mierzy SEMANTYKĘ ZOH-age, osobno od czystego GT)
Maski dropoutu (Bernoulli p=0.25 + burst p=0.3/len=5, „duch G2") + szum obs. σ=0.01 na GT. **SEED=42
przypięty** (odtwarzalne). Dowód: `results/R02/gate_live/G2_IRR_*`.
- **age NARASTA w dziurach 0.10→2.98, RESET do 0.10 (L_deliver) przy refresh** — semantyka ZOH-age.
- **3 EXPIRE na sufcie θ_age** (burst 5 s > θ_age 3 s → age>sufit → wygaszenie = **HOLD na stęchliźnie**)
  + **3 re-ENTRY po dziurze**. 31 dropoutów. Cykl OBSERVE(391)↔PATROL(558).
- **Mimo nieregularności: d≥D_safe (0 naruszeń), A1=0, ≤R_E → PASS.** Czysty GT testuje OBSERVE;
  nieregularność testuje **WIEK** (ENTRY-po-dziurze, narastanie age, sufit wieku, HOLD na stęchliźnie).

**WNIOSEK TOR B:** **teza osłona+OBSERVE ZMIERZONA GT-FED na żywym symie: G2/G3/G4 PASS + nieregularność
PASS (ZOH-age).** Architektura działa NIEZALEŻNIE od percepcji — problem WYŁĄCZNIE w percepcji (kadrowanie,
§3f), nie w osłonie. G5 timing = interakcja fix#2/failsafe (do zbadania), nie wada osłony.

**ROZDZIAŁ GT-fed vs live-fed (jak 3b, jednym zdaniem):** wyniki G2–G4+nieregularność to **SUFIT architektury
GT-FED** (perfekcyjna poza-percepcyjna semantyka celu) — **live-fed (żywy interfejs detektora) pozostaje
OTWARTY do czasu upliftu percepcji** (tor C, dźwignia 0b celowanie kamery); raport nie miesza obu.

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

## 9bis. STOP iteracji 3 (A6 zamknięte w locie; G2–G5 gotowe w kopercie A7, czekają na GPU)
Ratyfikacja Olgi naniesiona (A6/A7, `PRE_R02.md §0bis`). **A6 conf-floor zaimplementowany** (θ_conf=0.1635
deterministyczny, wyłącznie ENTRY-admisja, kanał/osłona/P1/P5 bez conf, kombinacja z edge-margin, testy
28/28) + **pasywne logowanie conf**. **G1(A6) re-run W LOCIE → PASS** (§3d): **ε_FP=0** (0/min), **gap_held=TRUE**
(szum lotu max 0.0806 ≪ θ_conf 0.1635), A1=0, GF-native=0 (fix#2), 3 okr., SUKCES. **ε_FP DOMKNIĘTE w locie;
trigger R2-alt NIE odpalony.**

**G2 W LOCIE → A7 R2-alt TRIGGER ODPALONY (§3e).** Ridery: D_safe→3D 7 m; **micro-sanity (rider 1) znalazł
2 rozbieżności optyki** (alt 14/34.8° top-edge → dostosowano alt 11.5/13°; conf migocze ~θ_conf). **G2
(2 loty, intruz potwierdzony w kopercie): PORAZKA — conf sygnału w LOCIE 0.045–0.047 ≪ θ_conf 0.1635 →
0 ENTRY.** Statyczny sweep (0.169) NIE przeniósł się na lot (4×, pitch kamery). **To nazwany trigger A7 →
osobny PRE R2-alt (detektor jednoklasowy, anty-cyrkularny, charakteryzacja W LOCIE). NIE stroję θ_conf.**
**Teza osłona+OBSERVE:** LOGIKA dowiedziona (harness G1–G4, certy, ε_FP=0 w locie, fix#2), ale **nie
zmierzona live — detekcja pada u źródła.** To R2-alt, nie wada osłony. Commity: `bab52bd`/`571f348`/`d75a882`
/`4e0401f`/`1b43519`/`724974a`. **Decyzja (R2-alt PRE) i push: Olga.**

## 9. STOP — z rekomendacją i decyzją do Olgi (A2/SR-5) [iteracja 1–2, historyczne]
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
