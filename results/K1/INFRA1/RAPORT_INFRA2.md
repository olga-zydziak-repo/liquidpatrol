# RAPORT_INFRA2 — most gz↔PX4: pętla timejump lockstepu (cel właściwy)

LiquidPatrol · zadanie infrastrukturalne · otwarte przez INFRA-1 shakeout FAIL (N3) · 2026-08-24
Status: **SCOPING** — plan badawczy. Żadnej zmiany nie wdraża się bez ratyfikacji Olgi (SI-1: jedna
zmiana harnessu; SI-2: nigdy sędzia/osłona/kryteria).

## §0. Dlaczego INFRA-2 istnieje (wejście z INFRA-1)

INFRA-1 sfalsyfikował hipotezę obciążenia (RAPORT_INFRA1 §1) i przez zamrożony shakeout N3 postawił
diagnozę: **pętla `time jump detected → Resetting time synchroniser` jest TRWAŁĄ własnością mostu
gz↔PX4**, nie artefaktem przejściowym. Dowód (RAPORT_INFRA1 §4): 4 kolejne arm-faile
(S boot4/5/6 + E boot0 pre-reset) **oraz** E boot1 **po pełnym resecie operatorskim** — wszystkie
headless, load-niezależne (boot6@18 ≡ boot0@2.25 ≡ boot1@1.98), GPU-driver-reset-niezależne.

Objaw terminalny (cytat `E/p0_0/boot1/px4.log`, tożsamy z boot0):
`[timesync] time jump detected. Resetting time synchroniser.` ×8 →
`[uxrce_dds_client] time sync no longer converged` → `time sync converged` (cykl), przy
`Preflight Fail: High Gyro Bias / horizontal velocity unstable`, który NIGDY się nie czyści →
`Arming denied: Resolve system health failures first`. Skorelowane z gz RTF deep-stalls
(min_rtf 0.004, 8× rtf<0.5 w oknie preflight).

Środowisko (zakotwiczone): **Gazebo Sim 8.14.0**, **PX4 v1.16.2**, WSL2 (kernel 6.18.33.2),
render mesa-d3d12/NVIDIA, lockstep_scheduler (init `setting initial absolute time`).

## §1. Hipoteza robocza (do ROZSTRZYGNIĘCIA, nie założona)

Zegar symulacji gz podawany do lockstep_schedulera PX4 **skacze/zawiesza się** (deep-stall RTF do 0.004),
przekracza próg detekcji timejump PX4 → timesync reset → estymator (EKF2) resetuje horyzont →
Gyro Bias/velocity-unstable nie zbiega w 300 s → arm denied. **Źródło skoku zegara nieustalone** —
to jest przedmiot INFRA-2.

## §2. Kandydaci do ZBADANIA (żaden nie jest jeszcze remedium)

Kolejność = od najtańszego/najbardziej diagnostycznego do najbardziej inwazyjnego. Każdy kandydat ma
mieć **pomiar rozstrzygający** zanim cokolwiek się wdroży.

- **C1 — źródło zegara sim / krok fizyki gz.** Zmierzyć rzeczywisty `max_step_size` i real-time
  update rate świata (`worlds/default.sdf` `<physics>`), oraz czy gz dostarcza zegar monotonicznie pod
  stallami. Pomiar: skorelować `rtf_stream.jsonl` (sim,wall,rtf) z sygnaturami timejump w px4.log w tej
  samej osi czasu. Pytanie: czy timejump ZAWSZE poprzedza deep-stall (przyczyna=gz), czy odwrotnie.
- **C2 — próg detekcji timejump w PX4.** Gdzie PX4 v1.16.2 uznaje „time jump" (lockstep_scheduler /
  timesync). Czy stall N ms przekracza sztywny próg. Pomiar: rozmiar skoku sim-time z logu vs próg w
  źródle PX4. UWAGA: dotknięcie progu = zmiana zachowania estymatora → NIE bez osobnej ratyfikacji.
- **C3 — plugin/most gz↔PX4 (gz_bridge, ros_gz).** Wersja pluginu vs Gazebo 8.14.0; czy `gz_bridge`
  PX4 (nie ros_gz kamery) gubi takty pod obciążeniem renderu. Pomiar: boot z rendererem `null`
  (headless bez mesa-d3d12) vs obecny mesa-d3d12 — czy pipeline renderu (nawet headless) współdzieli
  wątek/zegar z fizyką. To testuje, czy „headless" u nas naprawdę odcina render.
- **C4 — PX4_SIM_SPEED_FACTOR / tryb lockstep.** Czy jawne ustawienie speed factor=1.0 lub wyłączenie
  lockstepu (tryb non-lockstep, jeśli wspierany v1.16.2) usuwa pętlę. UWAGA: non-lockstep zmienia
  semantykę czasu całego stacku K1 → wymaga re-walidacji habitatu i osobnej ratyfikacji.
- **C5 — WSL2 / sterownik GPU d3d12.** `vblank_mode` override (widoczny w px4.log:23), throttling
  D3D12 pod WSL. Pomiar: `GALLIUM_DRIVER=llvmpipe` (CPU-only render) vs d3d12 — czy programowy render
  eliminuje deep-stalle. Rozstrzyga, czy korzeń D8 jest w ścieżce GPU.

## §2-WYK. WYKONANE (ANEKS_INFRA2-1, CC 2026-08-24): C1 werdykt + C5 status

### C1 — zegar/lockstep (READ-ONLY, zero bootów) — WERDYKT: **lockstep AKTYWNY, sim-clock ZDROWY**

Źródło: ulog `results/K1/E/p0_0/boot1/boot.ulg` (4m35s, env-fail boot; okno preflight z 8 timejumpami).
Dane surowe: `C1_clock_analysis.json`.

**(a) Konfiguracja uruchomienia (cytaty):**
- gz: `gz sim --verbose=1 -r -s <world>.sdf &` (`px4-rc.gzsim:54`; `-r`=run-on-start, `-s`=server-only, `HEADLESS`⇒bez gui).
- most: moduł PX4 `gz_bridge start -w default -n x500_mono_cam_0` (`px4-rc.gzsim:133`).
- **lockstep AKTYWNY:** `[lockstep_scheduler] setting initial absolute time` (px4.log). IMU 250 Hz (`IMU_INTEG_RATE 250`, `px4-rc.simulator:4`).
- fizyka świata (`default.sdf`): `<physics type=ode> max_step_size=0.004 real_time_factor=1.0 real_time_update_rate=250`.
- `PX4_SIM_SPEED_FACTOR` **NIE ustawiony** (`px4-rc.gzsim:139` pominięte) → brak override RTF. Env mostu: `gz_env.sh` (PX4_GZ_PLUGINS, server.config).
- **Atrybucja frazy:** `time jump detected. Resetting time synchroniser.` = `src/lib/timesync/Timesync.cpp:69`, klasa `Timesync` używana przez **`uxrce_dds_client`** (synchronizacja hrt/sim ↔ zegar hosta agenta ROS2). Próg: `MAX_DEVIATION_SAMPLE=100ms` ∧ `MAX_CONSECUTIVE_HIGH_DEVIATION=10` (>10 kolejnych próbek offsetu >100ms ⇒ reset; komentarz `Timesync.cpp:67`: „most likely due to a time jump on the offboard system").

**(b) Oś hrt vs sim vs różnica (na jednej skali, z ulogu):**
- **Oś SIM (hrt) — `sensor_combined`, n=68291:** Δt między kolejnymi próbkami IMU = **4000µs DOKŁADNIE dla wszystkich** (min=max=median=4000). **0 cofnięć, 0 stalli >50ms.** Zegar sim (na którym działa EKF) jest idealnie monotoniczny i jednorodny.
- **Oś RÓŻNICY — `timesync_status`, n=275:** `observed_offset` span **15.48 s**, **9 skoków >100ms** przy hrt [2.14, 3.12, 18.32, 49.96, 82.42, 147.02, 179.64, 211.12, 243.45] s, magnitudy ~2.0–2.4 s każdy.
- **Wniosek (b): skoki są WYŁĄCZNIE w RÓŻNICY sim↔wall, NIE w sim, NIE w hrt.** Oś sim czysta; „time jump" to reset filtra offsetu sim-vs-wall.

**(c) Rozkład Δt IMU wokół timejumpów:** brak jakiegokolwiek rozjazdu w Δt IMU — 68290/68291 interwałów w kubełku ≤4.1ms, zero w 4.1ms–∞. Timejumpy NIE mają odpowiednika w kadencji IMU (sim płynie równo także w trakcie każdego z 8 zdarzeń).

**Korelacja z RTF (rtf_stream, wall-time):** 8 deep-stalli `rtf<0.5` przy sim [2.14, 17.48, 49.70, 81.96, 146.46, 178.68, 210.93, 243.18] s (min_rtf 0.0035, **okres ~32 s**) = 8 skoków offsetu **1:1**. Mechanizm: każdy deep-stall zamraża sim na ~2 s w WALL-time → hrt(sim) zostaje ~2 s za zegarem agenta → offset >100ms → time-jump.

**WERDYKT C1: lockstep AKTYWNY i zdrowy.** „time jump detected" **NIE jest awarią lockstepu** — to artefakt `uxrce_dds` Timesync (referowanego do zegara ściennego) pod deep-stallami RTF w wall-time. **Zawęża N1:** gz NIE psuje zegara sim (jest idealny 4ms); zamraża sim w wall-time. Ponieważ EKF pracuje na osi sim (czystej), mechanizm N1 „timejump→EKF-reset→gyro-bias" wymaga rewizji — ale to **domena C2 (Q4: nie wchodzę)**.

### C5 — alternatywny backend renderu (jeden boot, gałąź E) — **ODROCZONY (maszyna obciążona)**

Przygotowany: transientna zmiana `run_k1_boot.sh:12` → `GALLIUM_DRIVER=llvmpipe LIBGL_ALWAYS_SOFTWARE=1` (software render), reszta identyczna, kryterium = N3. **Boot NIE wykonany:** bramka I2a poprawnie zablokowała start — maszyna obciążona **niezależnym zadaniem Olgi** `src.runner.gate2 --run-id gate2-krok3 --jobs 8` (8 workerów, 8/24 rdzeni, loadavg≈8 ≥ próg 8.0). **Nie tknięto zadania Olgi.** Uruchomienie C5 pod tym obciążeniem skaziłoby pomiar dokładnie konfundatorem load↔render, który INFRA-1 wyeliminował (gdyby load chwilowo dipnął <8.0, boot ruszyłby skażony). Transient zrewertowany do byte-identycznego (`run_k1_boot.sh` clean, frozen-4 ✓). **C5 czeka na wolne okno maszyny** (po zakończeniu `gate2-krok3` albo w oknie wskazanym przez Olgę). Wynik binarny wejdzie tu po wykonaniu.

### §2-PROP (Q2). Propozycja poprawki konfiguracyjnej — **PROPOZYCJA, NIE WDROŻONA** (SI-1: wymaga ratyfikacji Olgi)

C1 wykazał rozjazd osi (sim↔wall), ale **NIE wykazał błędnej konfiguracji lockstepu** (lockstep zdrowy). Stąd propozycja NIE jest zmianą lockstepu. Dwie ścieżki, obie do ratyfikacji, żadna nie wdrożona:

- **P1 (driver, preferowana kolejność): najpierw POMIAR C5, potem ewentualna zmiana renderu.** Skoro deep-stall wall-time (~32 s okres) to rzeczywisty driver, a env wymusza render D3D12/GPU (`env_gpu.sh`), to zmiana backendu renderu jest kandydatem na remedium — ale **dopiero po** binarnym pomiarze C5 (software render). Bez pomiaru = zgadywanie. Żadnej zmiany `env_gpu.sh`/renderu teraz.
- **P2 (symptom, warunkowa): `UXRCE_DDS_SYNCT=0`.** Param `UXRCE_DDS_SYNCT` (`module.yaml:88`, domyślnie >0) włącza filtr Timesync referowany do zegara ściennego agenta — źródło komunikatów „time jump". W SITL hrt≡sim, więc referencja do zegara ściennego jest **z założenia nietrafna** pod RTF<1. `=0` uciszyłby timejumpy i użył hrt/sim bezpośrednio (`uxrce_dds_client.cpp:215,327`). **ZASTRZEŻENIE ROZSTRZYGAJĄCE:** reset Timesync dotyka wyłącznie znakowania czasem wiadomości DDS, **nie EKF** (EKF pracuje na hrt/sim, która jest czysta) — więc **czy `SYNCT=0` naprawia ARM (`High Gyro Bias`/`velocity unstable`) jest NIEZNANE i leży w C2 (Q4: nie wchodzę).** P2 = kandydat do przetestowania w C2, nie remedium tu i teraz.

**Rekomendacja:** nie wdrażać nic przed (i) pomiarem C5 i (ii) werdyktem C2 co do rzeczywistej przyczyny ARM-fail. C1 przesunął podejrzenie z „skażony zegar sim" na „zdrowy zegar sim + artefakt timesync + otwarte pytanie o EKF".

## §3. Protokół badawczy (jak nie oszukać samych siebie)

- Każdy kandydat = **1 pomiar diagnostyczny na pustym bootcie (gałąź E)**, sędzia/osłona/kryteria K1
  NIETKNIĘTE (SI-2). Reużyć `run_k1_boot.sh E` + `infra1_empty_flight.py` + `infra1_shakeout_check.py`
  jako miarę (kryterium zamrożone — nie ruszać).
- **Falsyfikacja przed wdrożeniem:** kandydat awansuje do „remedium" tylko gdy pomiar POKAŻE różnicę
  (arm_ok=true ∧ tj≤1 ∧ 0 deep-stall) — nie na podstawie samej wiarygodności. To ta sama dyscyplina co
  N1 (hipoteza obciążenia upadła przez pomiar).
- **Jedna zmiana na raz** (SI-1). Po znalezieniu remedium: 1 zmiana harnessu → dziesiątka I3 (≥9/10) na
  NIEZMIENIONYCH kryteriach → dopiero wtedy K1 wznawia.
- Bez „powtarzania do skutku". Wiele bootów tego samego kandydata = pomiar rozkładu, nie selekcja
  najlepszego.

## §4. Zależności kalendarzowe (N5 — bez udawania)

K1 **nie wznawia się** przed rozstrzygnięciem INFRA-2 (znalezienie i zwalidowanie remedium mostu).
Pakiet na **2026-09-01** = **DEMO-B v1.0 + erraty + `RAPORT_K1_B1_STOP.md`** jako uczciwy status:
noga K1 wstrzymana na infrastrukturze symulatora, nie na logice osłony/sędziego (te są zamrożone i
zweryfikowane). INFRA-2 to praca do zaplanowania, nie „czekanie aż maszyna sama się naprawi".

## §5. Co JEST już ustalone (nie badać ponownie)

- Obciążenie CPU NIE jest driverem (INFRA-1 §1, pomiar). ✗ nie wracać.
- Kontencja GUI NIE jest driverem — boot1 headless a pętla trwa (`GUI_PROCS=[brak]`). ✗ nie wracać.
- Stan sterownika GPU po restarcie NIE leczy — reset operatorski wykonany, FAIL identyczny. ✗ nie wracać.
- Osłona/sędzia/kryteria K1 zamrożone i nietknięte przez całe INFRA-1/2 (hashe w RAPORT_INFRA1). ✗ nie ruszać.
