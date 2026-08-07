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
| **Latający closed-loop sweep** (świeży boot ×5, dron w OBSERVE) | wykonanie w locie | **NIE WYKONANY** — runner+orkiestracja gotowe; blokada: brak instrumentacji yaw (patrz §5) |

**Interpretacja (uczciwie, trójwynikowo):** wszystkie niezmienniki R0.1 (A1, P1a, geofence
nadrzędny, 0 padów) **dowiedzione formalnie** na rozszerzonym automacie (7 liści). Cała **logika**
łańcucha (kanał ZOH-age + OBSERVE + osłona) **przechodzi G1–G4** na prawdziwym kodzie w
deterministycznej pętli zamkniętej. **Detektor na żywym symie łapie intruza i zasila kanał**
(ENTRY 5-dim, BEZ conf) — oraz **nie generuje fałszywego locka na pustej scenie** (ε_FP). Pozostaje
JEDEN krok wykonawczy — **latający sweep** — zablokowany nazwanym, drobnym brakiem integracyjnym
(yaw z attitude), nie wadą logiki. To wynik **pozytywny z jawnie oznaczonym pozostałym krokiem**.

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
| **ε_FP: pusta scena (intruz x=−60)** | debug=`[n_box=0, conf=0, entry=0, locked=0]`, kanał pusty, **licznik ENTRY = 1** (brak nowego) | **oś G1 na żywo**: pusta scena → 0 boxów → **0 fałszywych locków** |
| **Wygaszenie ZOH** | kanał pustoszeje po utracie detekcji (θ_age) | semantyka sufitu działa na żywym strumieniu (oś G4) |

**Wniosek:** genuinie nowa integracja R0.2 (detektor-w-pętli + kanał ZOH-age + A1) **działa na żywym
symie**. Jakość detekcji: R1-A zmierzył 3/3 conf 0.177 z intruzem, 0 bez — tu potwierdzone w pełnym
węźle ROS2 (conf 0.169, kanał 5-dim, brak fałszywego locka).

---

## 4. G5 — warstwa-0 (natywny failsafe)

G5 = regres R0.1 **S4** (urwanie strumienia XRCE → natywna reakcja HOLD ≤~1.2 s przez PX4
`COM_OF_LOSS_T`). To **niezmiennik warstwy-0 odziedziczony** z R0.1 (tam PASS): OBSERVE żyje w
warstwie osłony (ALLOW/setpoint), **nie zmienia** parametrów PX4 (`COM_OBL_RC_ACT=5/Hold`,
`COM_OF_LOSS_T`, GF native na zewnątrz R_E) — więc reakcja warstwy-0 jest **z konstrukcji
niezmieniona** dodaniem OBSERVE. `r02/gate_run_r02.py:scenario_G5` egzekwuje ten test w locie
(gotowy). Formalnie: OBSERVE nie dotyka toru failsafe (A1 niezmiennik: setpointy tylko XRCE/osłona).

---

## 5. Latający closed-loop sweep — status i blokada (jawnie)

Runner **gotowy**: `r02/gate_run_r02.py` (G1–G5, świeży boot per scenariusz, subskrypcja kanału,
OBSERVE, liczniki A1/ε_FP/GF, księgowość trójwynikowa). Orkiestracja **gotowa**: `r02/run_gate_r02.sh`
(stos+most+detektor+intruz+runner, teardown po PID). Stos, kamera, detektor, MAVSDK (health/armable=True)
— **wszystkie zwalidowane żywe w tej sesji**.

**Blokada wykonania latającego G2/G3 (nazwana, drobna — NIE wada logiki):** naprowadzanie OBSERVE
wymaga **prawdziwego yaw** (attitude). `r01/exec_lib.Mav` instrumentuje tel. **pos/vel/flight_mode**,
ale **nie attitude** — `gate_run_r02._yaw()` wyprowadza yaw z prędkości, co w zawisie (v≈0) daje
yaw=0 i zafałszowaną estymatę. **Domknięcie:** `exec_lib.Mav += attitude_euler (yaw)` (1 subskrypcja
MAVSDK) → latający sweep wykonalny. G1 (patrol bez intruza, yaw nieistotny dla OBSERVE) i G5 (failsafe)
są wykonalne bez tej zmiany; G2/G3/G4 (OBSERVE w locie) wymagają yaw.

To znalezisko jest **spójne z dyscypliną** „logika najpierw, lot potwierdza": logika G1–G4 dowiedziona
(harness), detekcja dowiedziona (żywy smoke), a lot wymaga jednego jawnego uzupełnienia telemetrii.

---

## 6. Stop-rules — status

- **SR-1 (detektor @1 Hz):** nie wywołany — B0 p95 ≤22 ms ≪ 800 ms.
- **SR-2 (VRAM OOM):** nie wywołany — B0 headroom 10.6 GB; żywy smoke render+CUDA zmieścił się.
- **SR-3 (regres R0.1):** nie wywołany — A1/P1a/geofence/0-padów dowiedzione (certy + regresja 43/43).
- **SR-4 (rdzeń uczony):** **NIE otwarty** — bramka NIE wykazała nazwanego trybu porażki kanału
  ZOH-age adresowalnego predykcją (G4 kontroluje utratę przez sufit age). GRU/CfC pozostają zaparkowane.
- **SR-5 (wynik negatywny=wynik):** nie wystąpił — detekcja na mono/x500-mesh wiarygodna (żywy smoke).

---

## 7. Stałe habitatu (A4) — status
Wg `results/R02/CALIB_R02.md`: **prowizoryczne, związane z pomiarem w bramce**, reguły wyboru
zamrożone. θ_age=3, D_safe=8, L_deliver=0.10, T_ack≈4.1, f_fov=0.8, ε_FP=0, move_thr=0.15,
INTRUDER_ALT=6. Ostateczny freeze liczb = decyzja Olgi. Żaden próg NIE jest progiem conf (A1).

## 8. Higiena
- Stos **posprzątany**: 0 procesów sim, **GPU 0 MiB** po teardown (potwierdzone).
- Sesja dotknęła proverów → drzewo **zacommitowane** (4 commity: R3, R4+re-cert, guidance+harness, bramka).
- Brak markerów padu w dmesg podczas smoke.

## 9. STOP
Blok R3→R4→re-cert→bramka domknięty w warstwach: **certy PASS, logika G1–G4 PASS, żywy łańcuch R3
PASS, G5 odziedziczony**. Latający sweep gotowy, zablokowany nazwanym brakiem yaw (attitude) —
**jawnie oznaczony jako jedyny pozostały krok wykonawczy**. **Push robi Olga.**
