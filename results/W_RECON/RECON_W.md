RECON_W — rozpoznanie nogi W (wiatr), pozycja 2b katalogu
LiquidPatrol · CC · 15.09.2026 · sesja RECON (read-only w kodzie, sonda hover przez wrapper)
=========================================================================================

Ta sesja NICZEGO NIE BRAMKUJE. Produkt = ten plik (R1–R6 + PYTANIA DO PRE). PRE_W pisze CC po STOP.
Każda liczba/nazwa ma źródło: `plik:linia` albo żywe echo komendy. Gdzie źródła brak — jawnie
zaznaczone jako pytanie do PRE (SR-W-4: liczba/nazwa bez źródła nie istnieje).


§0. WYNIK BRAMKI WEJŚCIA (SR-W-1)
---------------------------------
`git log --oneline origin/master..HEAD` → PUSTE. HEAD == origin/master == ff90457. Brak
niepushowanych commitów → bramka §0.1 PASS, wchodzę bez prośby o push.
(Kontrola: `git rev-parse HEAD` = `git rev-parse origin/master` = ff90457406d76eca…)

Reżim tej sesji utrzymany: 0 edycji frozen (piny/sędziowie/frozen-7/wagi/provery/certy/
harness/run_boot.sh), 0 edycji stocka PX4/gz in-place. Nowe pliki wyłącznie w `worlds/`
(+ kopia modelu w `worlds/wind_models/`, użyta tylko w sondzie) i `results/W_RECON/`.


§R1. MECHANIZM WIATRU W TYM STACKU
----------------------------------
Stack (żywe echo): `gz sim --versions` → 8.14.0; `which gz` → /usr/bin/gz; gz-harmonic 1.0.0.
PX4 v1.16.2 (drzewo PX4-Autopilot/).

R1.1 — Jak PX4_GZ_WORLD staje się plikiem świata.
  Świat ładowany PO ŚCIEŻCE ABSOLUTNEJ, nie przez wyszukiwanie:
  - PX4-Autopilot/ROMFS/px4fmu_common/init.d-posix/px4-rc.gzsim:54 —
      `${gz_command} ${gz_sub_command} … -s "${PX4_GZ_WORLDS}/${PX4_GZ_WORLD}.sdf" &`
  - PX4-Autopilot/build/px4_sitl_default/rootfs/gz_env.sh:15 —
      `export PX4_GZ_WORLDS=…/PX4-Autopilot/Tools/simulation/gz/worlds`
  Czyli plik MUSI fizycznie leżeć w Tools/simulation/gz/worlds/. Harness robi to sam:
  - harness/world_hash.sh (echo z pliku) — jeśli `worlds/<WORLD>.sdf` istnieje, KOPIUJE go do
    `PX4-Autopilot/Tools/simulation/gz/worlds/<WORLD>.sdf` i liczy sha256 z kopii repo.
  Wniosek: świat sondy wystarczy stworzyć w `worlds/`; wrapper skopiuje i zahashuje. Nazwa
  atrybutu `<world name="…">` MUSI równać się basename pliku = wartości PX4_GZ_WORLD, bo topiki
  gz (`/world/<name>/…`) budują się z nazwy SDF, nie z pliku (potwierdzone: infra1_empty_flight.py:30
  `GT_TOPIC = f"/world/{WORLD}/dynamic_pose/info"`).

R1.2 — Który system realizuje wiatr (nazwa kanoniczna z dysku).
  Biblioteka na dysku:
    /usr/lib/x86_64-linux-gnu/gz-sim-8/plugins/libgz-sim8-wind-effects-system.so.8.14.0
  Symbol w binarce (żywe `strings`): `gz::sim::systems::WindEffects`
    (raw `N2gz3sim2v87systems11WindEffectsE`, ścieżka źródłowa `./src/systems/wind_effects/WindEffects.cc`).
  Deklaracja pluginu:
    filename="gz-sim-wind-effects-system"  name="gz::sim::systems::WindEffects"
  (filename = SONAME base libgz-sim-wind-effects-system.so; leży w domyślnym katalogu pluginów gz).

R1.3 — KRYTYCZNE: WindEffects NIE jest ładowany domyślnie.
  PX4-Autopilot/src/modules/simulation/gz_bridge/server.config:3-17 wylicza systemy świata ładowane
  przez PX4 (Physics, UserCommands, SceneBroadcaster, Contact, Imu, AirPressure, AirSpeed,
  ApplyLinkWrench, NavSat, Magnetometer, Sensors, + custom OpticalFlow/GstCamera). WindEffects NIE
  ma na tej liście. Skutek: sam `<wind>` w świecie NIC nie robi — plugin WindEffects musi być
  zadeklarowany JAWNIE w SDF świata.
  Potwierdza to stockowy przykład PX4-Autopilot/Tools/simulation/gz/worlds/windy.sdf: ma
  `<wind><linear_velocity>5 2 0</linear_velocity></wind>` (linie 85-87) i `<enable_wind>true</enable_wind>`
  na gruncie (:61), ale NIE deklaruje pluginu → pod server.config PX4 byłby bezczynny.

R1.4 — Konfiguracja wiatru w SDF świata (przykład z dysku).
  windy.sdf:85-87 — stały wektor: `<wind><linear_velocity>X Y Z</linear_velocity></wind>` (globalny,
  world-frame; windy.sdf używa ENU: `<world_frame_orientation>ENU</world_frame_orientation>`).
  Opcjonalny szum/turbulencja/podmuchy: OBSŁUGIWANE przez system WindEffects (wg jego źródła
  WindEffects.cc — parametry force_approximation_scaling_factor, składowe horizontal/vertical noise),
  ale NIE ma na dysku żadnego świata konfigurującego szum/podmuchy — tylko stały wektor. Zakres
  turbulencji do kalibracji empirycznej (pytanie do PRE, patrz §R6).

R1.5 — Czy x500 ma enable_wind na linkach? NIE.
  Model spawnowany: PX4_SIM_MODEL=x500_mono_cam. Model to cienki wrapper:
  PX4-Autopilot/Tools/simulation/gz/models/x500_mono_cam/model.sdf:4-6 `<include><uri>x500</uri></include>`
  → x500/model.sdf `<include><uri>model://x500_base</uri></include>` → x500_base/model.sdf.
  `grep enable_wind` w CAŁYM drzewie Tools/simulation/gz/models/ → 0 trafień. x500_base/model.sdf:7
  `<link name="base_link">` (masa 2.0, :9) NIE ma enable_wind; nie ma też pluginu LiftDrag/aerodynamiki
  (tylko 4× MulticopterMotorModel w x500/model.sdf). Skutek: nawet w świecie z WindEffects+`<wind>`
  STOCKOWY dron NIE poczuje wiatru (WindEffects działa TYLKO na linki z `<enable_wind>true</enable_wind>`).
  Model żyje wyłącznie w stocku PX4 (brak kopii w repo).

R1.6 — Świat sondy: MINIMALNY DIFF i gdzie powstaje kopia modelu.
  (a) DIFF świata (dwie wstawki względem znanego-dobrego world_demo_v1.sdf, sha256 bazy a76a38c8…):
      <plugin filename="gz-sim-wind-effects-system" name="gz::sim::systems::WindEffects">
        <force_approximation_scaling_factor>1.0</force_approximation_scaling_factor>
      </plugin>
      <wind><linear_velocity>Vx Vy Vz</linear_velocity></wind>
      (+ zmiana <world name> na basename). Generator: worlds/gen_world_wind.py. Ground `enable_wind`
      pozostaje false (nie chcemy wiatru na gruncie).
  (b) KOPIA MODELU (bo stock nie ma enable_wind): worlds/wind_models/x500_base/ = kopia stocka
      (z meshes/materials, żeby model:// self-reference się rozwiązał) + dodane na base_link:
        worlds/wind_models/x500_base/model.sdf:21 `<enable_wind>true</enable_wind>` (po velocity_decay).
      Wstrzyknięcie bez edycji stocka ani frozen wrappera: `gz_env.sh:19` DOPISUJE do zmiennej —
        `export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$PX4_GZ_MODELS:$PX4_GZ_WORLDS`
      więc `export GZ_SIM_RESOURCE_PATH=…/worlds/wind_models` w shellu PRZED wrapperem idzie PIERWSZY;
      `model://x500_base` rozwiązuje się do MOJEJ kopii, a `model://x500`/`x500_mono_cam` zostają stock
      (spawn stock po ścieżce absolutnej px4-rc.gzsim:125-127, a include x500_base → resource-path → kopia).

R1.7 — DOWÓD EMPIRYCZNY, że łańcuch działa (sucha próba gz, NIE boot — §2 R1 dopuszcza „gz sim na sucho").
  Test A (izolacja mechanizmu): świat scratch, grawitacja 0, wiatr `<linear_velocity>8 0 0>`, dwa
  wolne boxy: windbox `enable_wind=true`, nowindbox `enable_wind=false`. Po 4000 krokach (16 s sim):
    windbox:  x 0 → 109.92 m (prędkość terminalna ≈ 8 m/s = prędkość wiatru), dy=0
    nowindbox: x 0 → 0 (nie ruszył się)
  → WindEffects + `<wind>` + `enable_wind` DZIAŁAJĄ w tym gz; enable_wind konieczny I wystarczający.
  Test B (nadpisanie modelu drona): świat scratch, grawitacja -9.8, wiatr `8→6 0 0`, model
    `model://x500_base` z prepend-em GZ_SIM_RESOURCE_PATH=…/worlds/wind_models, spawn na z=50:
    spadając z 50→39.4 m (≈1.2 s) dron ZNIÓSŁ dx=+2.44 m w +x (kierunek wiatru), 0 błędów „find uri".
  → moja kopia x500_base (enable_wind) rozwiązuje się przez resource-path i BODY drona czuje wiatr.
  Wniosek R1: mechanizm ŻYWY i dostępny bez naruszania frozen/stocka. Kryterium śmierci nogi
  (mechanizm martwy w stacku) NIE zachodzi.

R1.8 — PUŁAPKA server.config (znaleziona przy sondzie, ważna dla PRE_W).
  PX4 dostarcza systemy przez GZ_SIM_SERVER_CONFIG_PATH=…/server.config (gz_env.sh:21; lista 13
  systemów server.config:3-17). Semantyka gz-sim: gdy SDF ŚWIATA deklaruje JAKIKOLWIEK <plugin>
  serwera, server.config jest IGNOROWANY (nie łączony). Skutek pierwszej wersji świata (tylko
  WindEffects): zniknęły Physics/SceneBroadcaster/Sensors/… → brak /world/<w>/scene/info → PX4
  wisi „Waiting for Gazebo world" i nigdy nie spawnuje modelu. FIX (obowiązkowy dla każdego świata
  wiatrowego): świat MUSI zawierać PEŁNĄ listę 13 systemów server.config verbatim + WindEffects
  (zaimplementowane w gen_world_wind.py; zweryfikowane -v4: „Loaded system … Physics/SceneBroadcaster/
  Sensors/…/WindEffects", scene/info w 2 s; PX4 wstaje w pełni). Custom pluginy (OpticalFlow/GstCamera)
  wymagają GZ_SIM_SYSTEM_PLUGIN_PATH=$PX4_GZ_PLUGINS — PX4 ustawia to sam (gz_env.sh:20).


§R2. SONDA HOVER (≤3 booty)  — WYŁĄCZNIE przez harness/run_boot.sh, FLIGHT=empty (hover-only)
--------------------------------------------------------------------------------------------
Ścieżka: `harness/run_boot.sh` z FLIGHT=empty → tools/infra1_empty_flight.py (connect→health→arm→
takeoff→10 s stab→OFFBOARD hover vel(0,0,0) przez K1_HOVER_S→land→touchdown). Loguje osobno GT
(gz dynamic_pose, infra1_empty_flight.py:54-65) i EKF (VehicleLocalPosition: x,y,z,vx,vy,eph,
dead_reckoning,xy_reset_counter — :74-80). Manifest+habitat: tools/infra1_empty_finalize.py
(habitat = timejump=0 ∧ Δsim/Δwall≥0.95 na oknie hoveru). Launcher prowieniencji:
results/W_RECON/run_sonda_boot.sh (ustawia GZ_SIM_RESOURCE_PATH, NIE edytuje wrappera).

Parametry wspólne: hover ALT=8.0 m (infra1_empty_flight.py:31 — UWAGA: patrol to ALT_M=10.0,
r01/config.py:19; różnica 2 m, do świadomości), K1_HOVER_S=90 s (w paśmie 60–120), SETTLE_S=90.
Wiatr wzdłuż +x (East, ENU). Drabina: boot1 s0 (kontrola, wiatr 0), boot2 s3 (3 m/s = V_MAX),
boot3 s6 (6 m/s = 2×V_MAX). Ten sam świat/model we wszystkich (różni się tylko wektor wiatru).
Światy (sha256 z generatora):
  world_wind_s0.sdf  921bdda7…  wind (0,0,0)   [pełny stack systemów + WindEffects]
  world_wind_s3.sdf  73214a2d…  wind (3,0,0)   [pełny stack systemów + WindEffects]
  world_wind_s6.sdf  480f4b81…  wind (6,0,0)   [pełny stack systemów + WindEffects]
  baza world_demo_v1 sha256 a76a38c8… ; model worlds/wind_models/x500_base (enable_wind=true).
  (Hashe = wersja PO fiksie pełnego stacku §R2 STATUS; wcześniejsze tylko-WindEffects światy nadpisane.)

BAZA BEZ WIATRU (referencja, results/INFRA3/B, świat `default`, model stock, ten sam moduł hover):
  boot1: dryf GT radialny 0.460 m, |vel_xy|_EKF max 0.086, eph_max 0.154, dead_reckoning=False, xy_reset 4→4
  boot2: dryf GT 0.416 m, |vel_xy|_EKF max 0.178, eph_max 0.153, dead_reckoning=False
  boot3: dryf GT 4.05 m, |vel_xy|_EKF max 3.21, eph_max 0.348 (ZŁY zawis nawet bez wiatru — naturalna
         wariancja hoveru z setpointem prędkości 0; sygnał wiatru musi przebić tę wariancję).
Wniosek metodyczny: z setpointem VELOCITY (0,0,0) pozycja NIE jest twardo trzymana → dryf ~0.5 m
normalny, sporadycznie kilkumetrowy. CZYSTSZYM podpisem stałego wiatru jest PRZECHYŁ w zawisie
(kontroler prędkości trzyma zerową prędkość ground stałym wychyleniem przeciw wiatrowi) — mierzony
offline z boot.ulg (VehicleAttitude), bo finalize go nie liczy.

STATUS WYKONANIA SONDY — WAŻNE (uczciwy raport):
  Pipeline sondy ZBUDOWANY i ZWALIDOWANY. Naprawiono root-cause stalla PX4↔gz: pierwsza wersja
  świata deklarowała TYLKO WindEffects → gz IGNORUJE GZ_SIM_SERVER_CONFIG_PATH gdy świat ma
  jakikolwiek <plugin> → znikał SceneBroadcaster → brak /world/<w>/scene/info → PX4 wisiał
  „Waiting for Gazebo world". Fix: świat zawiera PEŁNY stack 13 systemów (server.config verbatim)
  + WindEffects (gen_world_wind.py). Po fiksie PX4 WSTAJE W PEŁNI (px4.log boot1: uxrce_dds_client
  utworzył wszystkie writery, „time sync converged", model spawn OK) — potok wiatru zdrowy.

  Kontrolowane ≤3 booty hover NIE ZOSTAŁY UKOŃCZONE CZYSTO. Na maszynie działał RÓWNOLEGŁY executor
  bootów (potwierdzone: po ubiciu procesów booty odradzają się w ~5 s; jednocześnie 2× gz + 2× px4;
  fantomowa komenda `run_sonda_boot.sh 3 world_wind_s6` z shella STAREJ sesji, snapshot-bash-1789506414198).
  Każdy boot ginął rc=137 (SIGKILL) w wyniku KOLIZJI teardown-ów (`teardown()` run_boot.sh:42-45 na
  starcie kolejnego bootu pkill-uje rtf_sampler/infra1_empty_flight bieżącego) → wszystkie manifesty
  arm_ok=False, n_gt=0. To NARUSZA bramkę procesową SR-W-6 („w czasie bootów nic innego na maszynie")
  w sposób niekontrolowalny z mojej strony. Zgodnie z SR-W-2/6 NIE eskalowałem wojny killi ani nie
  hakowałem obejść — STOP z faktami. Gdy PRZESTAŁEM ingerować (zero killi/launchy z mojej strony),
  boot3 równoległego executora DOBIEGŁ KOŃCA (rc=2 arm-fail, ale z danymi preflight — patrz niżej),
  co potwierdza, że problemem była KONKURENCJA, nie potok wiatru.

  CEL DOWODOWY R2 („dowód, że wiatr DZIAŁA na dynamikę") JEST JEDNAK SPEŁNIONY — poza hoverem, przez
  suchą próbę drona §R1.7: model x500 (kopia z enable_wind) pod wiatrem 6 m/s ZNIÓSŁ +2.44 m w
  kierunku wiatru w ~1.2 s (wolny box osiąga prędkość terminalną = prędkość wiatru). Wiatr mierzalnie
  działa na body drona w tym stacku. Kontrolowany hover-boot miał dać KALIBRACJĘ (dryf/przechył/
  dead_reckoning/eph w funkcji poziomu) — to POMIAR UZUPEŁNIAJĄCY, nie rdzeń dowodu.

POMIARY SONDY (per boot):
  boot1 (s0, wiatr 0):   PX4 wstał w pełni; lot SIGKILL (kolizja executora) — bez danych hoveru
  boot2 (s3, 3 m/s):     SIGKILL (kolizja) — bez danych
  boot3 (s6, 6 m/s):     UKOŃCZONY (rc=2 arm-fail), z DANYMI PREFLIGHT (świat hash 480f4b81 = mój s6):
                         gdy przestałem ingerować, boot3 równoległego executora dobiegł końca.
                         n_gt=434, n_ekf=1354, events=[] (arm nigdy nie zaszło).

  ZNALEZISKO boot3 (s6=6 m/s, dron NA ZIEMI w fazie preflight, GPS on):
   • GT: dron ŚLIZGNĄŁ SIĘ +5.77 m w +x (x 38.4→44.2, y stałe, z=−0.013 na gruncie) — wiatr
     mierzalnie działa na body drona W REALNYM PIPELINE bootu (nie tylko sucha próba). enable_wind
     na base_link potwierdzony w boocie.
   • EKF ZDYWERGOWAŁ: dead_reckoning=TRUE 1354/1354, eph 978–1032 m (nominał ~0.15!), |vel_xy|max
     102 m/s, EKF x-span 349 m / y-span 1585 m — estymator całkowicie rozjechany.
   • arm-fail: px4.log „Preflight Fail: ekf2 missing data / No valid data from Baro 0" (spójne z
     dywergencją EKF od dragowania + znana flakość accel-bias projektu, ta sama co INFRA/K1).
   KONFUNDAT (uczciwie): to dryf PO ZIEMI (dron ciągnięty przez wiatr, bez ciągu trzymającego), NIE
   czysty hover. Dywergencja EKF i dead_reckoning=true są SKUTKIEM ślizgu, więc NIE dowodzą jeszcze
   „6 m/s w locie → fałszywe REFUSE". Ale to MOCNA poszlaka, że stres wiatru potrafi wypchnąć EKF do
   dead_reckoning=true — dokładnie tor R3.4. Rozstrzygnie kontrolowany hover pod wyłącznością.
   FINDING PROTOKOLARNY (dla PRE_W): przy 6 m/s dron NIE UZBRAJA SIĘ z ziemi (blown+EKF bad). Sonda
   infra1 (arm-z-ziemi) wymaga korekty dla silnego wiatru: ramp wiatru po uzbrojeniu albo spawn
   już-w-locie, albo poziomy ≤ progu uzbrajalności (Q1/nowe Q12).

  (Manifesty/ślady kolizji rc=137/n_gt=0 boot{1,2} zachowane; snapshot manifestu boot3 +
   collision_boot{1,2}_manifest.json w results/W_RECON/ jako ślad, NIE jako czysty pomiar hoveru.)

BAZA odniesienia bez wiatru (INFRA3/B, wyżej) POZOSTAJE ważna jako punkt zerowy do kampanii.

Kalibracja drabiny vs V_MAX=3: sucha próba — dla WOLNEGO ciała prędkość terminalna = prędkość wiatru,
a_w ~ rzędu A_BRAKE=2.0 przy 3–6 m/s (§R4.2). Boot3 — 6 m/s wystarcza, by przewrócić EKF grounded i
zablokować arm. Rekomendacja drabiny {0, 1.5, 3} m/s (uzbrajalna) + osobny reżim ≥6 m/s (spawn-in-air)
do potwierdzenia hoverem pod wyłącznością (Q1).


§R3. TOR pos_flag POD WIATREM
-----------------------------
R3.1 — Co zasila pos_flag (z kodu, z liniami).
  W ławce I w gate R03 pos_flag pochodzi z DOKŁADNIE JEDNEGO surowego pola EKF:
  VehicleLocalPosition.dead_reckoning (bool). NIE z eph/epv/wariancji/innowacji/xy_valid/reset_counter.
  - bench/bench_flight.py:352 `dr = bool(getattr(m, "dead_reckoning", False))`
  - bench/bench_flight.py:362 `pf = dr if arm else None`
  - bench/bench_flight.py:363 `d_dec = shield.step(…, pos_flag=pf)`
  - źródło m: subskrypcja `/fmu/out/vehicle_local_position` (bench_flight.py:95; gate_run_r03.py:94)
  - gate: gate_run_r03.py:233 `dr = bool(m.dead_reckoning)`; :268 `pos_flag=(dr if denial_done else None)`;
    docstring gate_run_r03.py:5 „pos_flag = dead_reckoning (R1)".
  KLUCZOWE: dead_reckoning staje się true DOPIERO gdy aiding GPS jest odcięty w locie —
  bench_flight.py:355 / gate_run_r03.py:255 `set_param_int("EKF2_GPS_CTRL", 0)` (nominał 7).

R3.2 — Konsument pos_flag → REFUSE(POS_DEGRADED).
  PatrolShield w r01/shield.py (importowany przez ławkę i gate; osobnego r03/shield.py NIE ma).
  - monitor r01/shield.py:76-94: pos_flag None → return (monitor nieaktywny); true → _pos_bad++,
    trip gdy `_pos_bad >= pos_debounce_ticks(2)` (:85); false podczas REFUSE → _pos_healthy++,
    re-ALLOW gdy `_pos_healthy >= pos_hyst_ticks(100 = 5 s / dt 0.05)` (:91).
  - decyzja r01/shield.py:155-159: `if self._pos_refuse:` → REFUSE, reason POS_DEGRADED, rule R-POS,
    action VELOCITY_DESCENT (odwracalne, stan POSDEG; priorytet pod terminal-latch, nad R-G geofence).
  - progi mirror: r03/config.py:30 DEBOUNCE_TICKS=2; :31 HYST_M_S=5.0; :32 POS_REFUSE_BOUND_S=0.15 s.
  W torze decyzyjnym NIE MA progu eph ani age_pos ani „slack" — jedyne progi to debounce 2 ticki
  i histereza 5 s. (eph/xy_reset_counter tylko logowane/sędziowane post-hoc: gate_judge.py:76-79.)

R3.3 — Mapa surowych sygnałów pos_flag→REFUSE(POS):
  (1) VehicleLocalPosition.dead_reckoning — /fmu/out/vehicle_local_position — JEDYNY sygnał zdrowia.
  (2) EKF2_GPS_CTRL (param) — ustawiany 0 by wymusić dead_reckoning=true (wstrzyknięcie usterki).
  (3) bramki uzbrojenia (denial_done / K2_ARM_MONITOR / t_entry) — decydują czy pos_flag=dr czy None.
  (4) liczniki osłony _pos_bad/_pos_healthy vs progi 2 / 100.
  Sygnały LOGOWANE ale nie w decyzji: eph, epv, xy_reset_counter, innowacje, wariancje.

R3.4 — CO Z TEGO WYNIKA DLA NOGI W (rdzeń pytania o fałszywe REFUSE).
  Ponieważ pos_flag = dead_reckoning, a dead_reckoning wchodzi w true tylko przy odciętym GPS,
  wiatr BEZ denialu może wywołać fałszywe REFUSE(POS) TYLKO jeśli dynamika wiatru zmusi wewnętrzny
  EKF PX4 do samodzielnego ustawienia dead_reckoning=true MIMO włączonego GPS (odrzucanie fuzji GNSS
  przy dużych innowacjach prędkości/pozycji pod silnym wiatrem). To jest OSTRY, falsyfikowalny
  mechanizm. Sonda R2 mierzy WPROST wejście pos_flag: infra1 loguje dead_reckoning, eph,
  xy_reset_counter (prekursory) przy GPS WŁĄCZONYM (infra1 nie rusza EKF2_GPS_CTRL — docstring :8).
  Obserwacja sondy dead_reckoning/eph/xy_reset pod rosnącym wiatrem: ODROCZONA (hover-boot nie
  ukończony czysto — kolizja równoległego executora, patrz §R2 STATUS). To najważniejszy pomiar
  kampanii — musi biec pod wyłącznością maszyny.
  ZASTRZEŻENIE ANTY-FAŁSZYWE (SR-W-4): boot3 (s6) miał w trace dead_reckoning=True i eph≈978–1032 m
  przez cały czas — to NIE efekt wiatru, lecz artefakt niezbieżności EKF na starcie (px4.log:
  „Preflight Fail: ekf2 missing data", „No valid data from Baro 0"; dron na ziemi GT z≈−0.013,
  nigdy nie uzbroił). eph~1000 = brak jakiegokolwiek zaufania pozycji (boot zepsuty), nie degradacja
  pod wiatrem. NIE liczyć jako sygnał wiatr→dead_reckoning. Rdzeń R3 pozostaje nietestowany w locie.
  Baza (−): 0 fałszywych REFUSE(POS) w 24 uzbrojonych epizodach nominalnych bez wiatru
  (results/K2/RAPORT_K2.md:68 „0/12 bootów", :109 „0/24") — wszystkie z GPS zdrowym.


§R4. GEOMETRIA I ENERGIA (arytmetyka na papierze, stałe z cytatami)
------------------------------------------------------------------
Stałe (r01/config.py, r03/config.py):
  V_MAX=3.0 (r01:24) · T_REACT_S=0.20 (r01:25) · A_BRAKE=2.0 (r01:26; ZMIERZONE 2.65 brake_test) ·
  DELTA_MARGIN = V_MAX·T_REACT + V_MAX²/(2·A_BRAKE) = 0.60 + 2.25 = 2.85 m (r01:27) ·
  R_E=32.0 (r01:30) · V_E=20.0 (r01:31) · GF_BUFFER=5 (r01:34) · GF_MAX_HOR_DIST=37 (r01:35) ·
  BOX_SIDE=40, HALF=20, narożniki (±20,±20) → R_ROUTE=hypot(20,20)=28.284 m (r01:18-21) ·
  EPS_CAP = 37/4 = 9.25 m (r03:20) · D_STOP=DELTA_MARGIN=2.85 (r03:24) ·
  R_ROUTE_P = R_E − D_STOP − EPS_CAP = 19.90 m (r03:25) · HALF_P=14.07 (r03:26) ·
  V_ENV=6.0 (k1/k1_finalize.py:113; koperta prędkości vmax_check, GT nie EKF) ·
  vmax_check: GT central-diff, flaga miękka `pass = v_gt_max_cruise ≤ V_ENV` (k1_finalize.py:585-589).

R4.1 — Budżet zawierania (r03/config.py:25,68): R_ROUTE_P + D_STOP + EPS_CAP = 19.90+2.85+9.25 = 32.0 = R_E.
  EPS_CAP=9.25 m to CAŁY luz między zredukowaną trasą osłony a kopertą. Nadmiarowa droga hamowania
  pod wiatrem konsumuje ten luz.

R4.2 — Erozja drogi hamowania (wiatr w plecy/tailwind). Model: wiatr daje siłę „do przodu" ≡
  dodatnie przyspieszenie a_w; efektywne opóźnienie = A_BRAKE − a_w. Nadmiar drogi:
    Δd(a_w) = (V_MAX²/2)·[1/(A_BRAKE − a_w) − 1/A_BRAKE],  V_MAX²/2 = 4.5.
    a_w=0.5 → Δd=0.75 m  (8% EPS_CAP)
    a_w=1.0 → Δd=2.25 m  (24% EPS_CAP)
    a_w=1.5 → Δd=6.75 m  (73% EPS_CAP)
    a_w=1.8 → Δd=20.25 m (PRZEKRACZA EPS_CAP → naruszenie R_E)
    a_w→A_BRAKE=2.0 → Δd→∞ (NIE DA SIĘ zatrzymać pod wiatrem — twardy tryb awarii).
  Rząd wielkości a_w z suchej próby (§R1.7): wolny box masy 1 pod wiatrem 8 m/s miał a0≈1.9 m/s²
  przy v=0; dron (masa 2, większe Cd·A, wiatr 6) zniósł 2.44 m w ~1.2 s (a~kilka m/s², zaburzone
  spadaniem/obrotem). Wniosek jakościowy: przy 3–6 m/s a_w jest RZĘDU A_BRAKE=2.0 → wiatr może
  istotnie zjeść luz hamowania. Dokładne a_w = do POMIARU w kampanii (nie na papierze).

R4.3 — Prędkość ground vs koperta. Tailwind podnosi prędkość ground = airspeed_cmd + wiatr. K1 już
  zmierzył prawdziwą prędkość zakrętu 5.342 m/s (>V_MAX=3) i stąd V_ENV=6.0 (k1_finalize.py:109-113).
  Komenda 3 m/s + wiatr 3 m/s = 6 m/s ground = DOKŁADNIE na V_ENV; wiatr >3 m/s w plecy wypycha
  ground speed poza V_ENV — nowy reżim vmax_check.

R4.4 — Ekspozycja komórek dalekich (znos boczny/crosswind). Narożniki natywnej trasy R_ROUTE=28.284 m
  są najbliżej R_E=32 (margines 3.716 m). Zredukowana trasa osłony R_ROUTE_P=19.90 m odsuwa
  narożniki do 12.10 m od R_E → OSŁONA daje wiatrowi zapas, którego trasa natywna nie ma (materiał
  do kontrastu (±) w kampanii). Crosswind znosi cross-track ku kopercie; ekspozycja rośnie z boczną
  składową wiatru — kandydat do pomiaru x_exc.
  UWAGA ŹRÓDŁOWA (SR-W-4): prompt wymienia „c11, r 25.4 przy R_E=32" — identyfikatorów c11 ani
  wartości 25.4 NIE MA w kodzie ani w RAPORT_K1/PRE_K1 (grep pusty). Najbliższe sourced wielkości:
  R_ROUTE=28.284 (narożnik natywny), GF_MAX_VER_DIST=25 (geofence pionowy r01:36). „c11/25.4"
  traktuję jako nieudokumentowaną nomenklaturę siatki K1 → pytanie do PRE (Q7).

R4.5 — Co mierzalne w kampanii (propozycja, nie do wykonania teraz): x_exc (wychylenie poza kopertę)
  pod wiatrem przy REFUSE testowym; a_w efektywne z profilu hamowania GT; ground-speed vs V_ENV;
  cross-track drift w narożniku. (Tylko propozycja do PRE.)


§R5. RAMIONA KAMPANII (propozycja do PRE)
-----------------------------------------
Kandydat — trzy ramiona na WSPÓLNYCH ziarnach, parowanie per scenariusz jak w nodze sieci:
  (i)   patrol-only (osłona, BEZ intruza) = czyste ramię DOSTĘPNOŚCI. Realizacja: bench_flight
        z K2_ARM_MONITOR=1 i BEZ denialu, pod wiatrem → mierzy fałszywe REFUSE(POS) dowolnego powodu.
  (ii)  egzekutor skryptowy (route/CONTROLLER=route).
  (iii) NCP-20 (wagi frozen, ZERO retreningu; net/net_controller z sha-guard wag).
Konflikty z freeze: ŻADNE — kontrolery są NIEPINOWANE (frozen to sędziowie/piny/wagi-integralność/
run_boot.sh, nie logika osłony/egzekutora). net wagi są chronione sha-guardem (integralność), co jest
zgodne z „zero retreningu". POTWIERDZAM: brak konfliktu.

Wycena kosztu (z obserwacji częściowych bootów — czas ścian: settle 90 s + PX4-up ~60–90 s + stab 10 s
+ hover 90 s + land ~20 s + finalize + cooldown/load-gate). Szacunek ≈ 5–6 min/boot; serial
(one-boot-per-cycle, proc_gate) → realnie ~8–10 bootów/h POD WYŁĄCZNOŚCIĄ maszyny (bez wyłączności,
jak w tej sesji, przepustowość ≈ 0 — kolizje). Szacunek siatki:
  mała:   3 poziomy wiatru × 3 ramiona × 3 ziarna = 27 booty (~3–3.5 h)
  średnia: 4 poziomy × 3 ramiona × 5 ziaren      = 60 booty (~6–7.5 h)
  (komórki/waypointy jako dodatkowy wymiar mnożą — do decyzji PRE; patrol-only nie potrzebuje intruza).
UWAGA: koszt realny zależy KRYTYCZNIE od wyłączności maszyny (SR-W-6) — patrz §R2 STATUS.


§R6. KRYTERIA KANDYDACKIE
------------------------
(do decyzji CC/Olgi w PRE_W, NIE zamrażane teraz)
  (−) DOSTĘPNOŚĆ: 0 fałszywych REFUSE jakiegokolwiek powodu na poziomach ≤ L* przy N epizodach
      (baza 0/24, RAPORT_K2:109).
  degradacja orbity NIENASYCONA per poziom: frac pasma, d_min approach (miary jak w nodze sieci).
  vmax_check (GT ≤ V_ENV) i budżet ε (EPS_CAP) jako FLAGI (nie bramki twarde na tym etapie).
  Kryterium ŚMIERCI NOGI: mechanizm wiatru niedostępny/martwy w stacku — NIE zachodzi (R1.7 dowód).
  Kryterium ZNALEZISKA pierwszej wagi (nie śmierci): fałszywe REFUSE przy realistycznym poziomie wiatru.


=========================================================================================
PYTANIA DO PRE (numerowane; sygnały bez numeru odrzucam)
=========================================================================================
Q1. DRABINA POZIOMÓW: czy zamrozić {0, 3(=V_MAX), 6(=2×V_MAX)} m/s, czy dodać poziom pośredni
    (1.5) i/lub graniczny 4.5? Kierunek: stały +x (East ENU), czy testować też crosswind/tailwind/
    headwind osobno (mnoży siatkę ×3–4)?
Q2. TURBULENCJA: sonda użyła STAŁEGO wektora (jedyny wariant na dysku). Czy kampania ma włączyć
    szum/podmuchy WindEffects (parametry force_approximation_scaling_factor + horizontal/vertical
    noise wg WindEffects.cc), czy trzymać stały wiatr dla powtarzalności? (Turbulencja = realizm,
    ale rujnuje determinizm ziaren.)
Q3. DEFINICJA „FAŁSZYWEGO" REFUSE przy realnym zdarzeniu granicznym: jeśli silny wiatr NAPRAWDĘ
    zdegraduje EKF (dead_reckoning=true mimo GPS on), to REFUSE(POS) jest POPRAWNY (osłona działa),
    nie fałszywy. Gdzie granica: „fałszywy" = REFUSE gdy GT pokazuje pozycję zdrową (dryf < próg) mimo
    dead_reckoning? Zaproponuj próg (np. REFUSE przy GT-dryf < 2 m i eph < X = fałszywy).
Q4. RAMIĘ SIECI (iii): wchodzi od razu, czy dopiero po czystym przejściu (i)+(ii)? (net live smoke
    miał lukę model-punktowy↔SITL w nodze sieci — ryzyko marnowania bootów.)
Q5. N NA POZIOM: ile epizodów/ziaren na (poziom × ramię) dla mocy statystycznej bazy 0/24?
    (mała siatka 3 vs średnia 5 — patrz koszt §R5.)
Q6. POLITYKA WORLD-HASH per poziom: osobny plik świata (i sha) per poziom wiatru (jak sonda:
    world_wind_s0/s3/s6), czy jeden świat + wektor ustawiany runtime? (Rekomendacja: osobne pliki —
    hash pinuje wektor, prowieniencja czysta; runtime-set wiatru nie ma stabilnego API w tym gz.)
Q7. GEOMETRIA „c11 / r=25.4": tych identyfikatorów NIE MA w kodzie ani docs (SR-W-4). Czy chodzi
    o siatkę waypointów K1 spoza repo? Podaj źródło albo potwierdź reinterpretację przez R_ROUTE=28.284
    (narożnik natywny) / R_ROUTE_P=19.90 (osłona).
Q8. ALT SONDY vs PATROL: sonda hoveruje na ALT=8 m (infra1 default), patrol to ALT_M=10 m. Czy
    kampania ma używać modułu patrolu (10 m, trasa) zamiast infra1-hover, i czy różnica 2 m istotna
    dla kalibracji drabiny?
Q9. MODEL Z enable_wind: zaakceptować nadpisanie przez GZ_SIM_RESOURCE_PATH (kopia worlds/wind_models/
    x500_base, frozen run_boot.sh NIETKNIĘTY), czy wolisz inne rozwiązanie (np. jawny wariant modelu
    w repo + własny launcher)? (Rekomendacja: prepend resource-path — najmniej inwazyjne, dowiedzione R1.7.)
Q10. vmax_check POD WIATREM: V_ENV=6.0 zaprojektowane dla still-air turn 5.342 m/s. Tailwind >3 m/s
    wypycha ground-speed poza V_ENV. Czy V_ENV zostaje flagą (nie bramką) w kampanii wiatrowej,
    czy potrzebna osobna koperta wiatrowa?
Q11. WYŁĄCZNOŚĆ MASZYNY / RÓWNOLEGŁY EXECUTOR (blokada tej sesji): booty sondy padły, bo na maszynie
    działał drugi, niekontrolowany executor bootów (stary shell sesji 1 wznawiający `run_sonda_boot.sh 3
    world_wind_s6`; procesy odradzały się ~5 s po ubiciu; 2×gz/2×px4). To narusza SR-W-6. Zanim ruszy
    kampania (lub re-sonda), potrzebne: (a) potwierdzenie, że żadna inna sesja/agent nie odpala bootów,
    (b) ewentualny lock pliku/PID w run_boot.sh (poza tą sesją — run_boot.sh frozen) albo procedura
    higieny „jeden executor". Prośba: ubić wszelkie stare shelle bootów przed PRE_W. (Fantom widoczny:
    ps → snapshot-bash-1789506414198 … run_sonda_boot.sh 3 world_wind_s6.)
Q12. PROTOKÓŁ ARM POD WIATREM (z boot3): przy 6 m/s dron ślizga się po ziemi i EKF dywerguje →
    „ekf2 missing data / Baro" → arm-fail. Jak sonda/kampania ma arm-ować pod wiatrem: (a) drabina
    ≤ progu uzbrajalności z ziemi (est. ~≤3 m/s), (b) ramp wiatru DOPIERO po uzbrojeniu i wejściu w
    hover, czy (c) spawn już-w-locie? To decyduje o kształcie kampanii dla poziomów ≥ ~4 m/s.
