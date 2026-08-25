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

### S1 (ANEKS_INFRA2-2). Obalone hipotezy CC — kampania INFRA (rejestr)

1. **Hipoteza obciążenia CPU (M4)** — OBALONA pomiarem (INFRA-1 §1): arm-fail niezależny od load (boot6@18 ≡ boot0@2.25).
2. **„Headless ⇒ lockstep stabilny" (`run_stack.sh:34-37`)** — SFALSYFIKOWANA (INFRA-1 §4): boot1 headless, pętla timejump trwa.
3. **Łańcuch przyczynowy N1 „stall → timejump → EKF (reset/gyro-bias)"** — OBALONY przez C1+C2: zegar sim idealny (Δt IMU 4000µs, 0 stalli), „time jump" = artefakt uxrce Timesync (`Timesync.cpp:69`), a EKF (na osi sim) **zbiegł** (innowacje czyste od sim 20.6s). Timejump NIE psuje EKF.
4. **Środek zaradczy I2b („arm po zbieżności = czekaj na Ready")** — WŁASNY środek CC, OBALONY przez C2: nie tylko nie leczył, ale **wprowadzał deadlock** (Ready⇐GCS⇐MAVSDK⇐moduł lotu, który I2b odraczał), gwarantując env-fail każdego bootu. To pierwsza obalona pozycja, która jest MOIM remedium, nie hipotezą o świecie. Skutek: werdykt shakeoutu N3 wycofany (ANEKS_INFRA1-3 W1), I2b zrewertowany (W2, P0a).

### C2 (ANEKS_INFRA2-2 S2) — zbieżność vs timeout, READ-ONLY na ulogu — WERDYKT: **DEADLOCK HARNESSU I2b**

**(a) czas sim w oknie:** boot1 sim span **273 s** (RTF_avg 0.948, wall 287 s) — harness poddał się @300 s wall ≈ 273 s sim. **Czasu sim było dosyć.**

**(b) zbieżność estymatora na osi sim (boot1):** wszystkie `pre_flt_fail_innov_*` = 0 **ciągiem od sim 20.6 s do 273 s** (okno 252 s); `vel/pos/hgt_test_ratio` końcowe 0.004/0.004/0.007; `gyro_bias|.|` koniec **0.00046 rad/s** (max 0.135 wcześnie). **EKF ZBIEGŁ — to NIE „realna niezbieżność".** ALE: `pre_flight_checks_pass=0` zawsze, `armed=0/544`, **`gcs_connection_lost=1` przez wszystkie 544 próbki**, 0× „Ready for takeoff".

**(c) porównanie z N boot4 (zaarmował, STARY harness):** EKF czysty od sim **0 s**; `gcs_connection_lost` 1→0 @sim **92.1 s**; `pre_flight_checks_pass=1` @**92.1 s** (dokładnie wtedy); armed @94.2 s. ⇒ **OSTATNIĄ bramką był GCS**, wyczyszczony gdy moduł lotu (MAVSDK) się podłączył (stary flow `sleep 90`→moduł startuje bezwarunkowo).

**PRZYCZYNA ŹRÓDŁOWA — DEADLOCK I2b:** I2b czeka na „Ready for takeoff" PRZED startem modułu lotu. „Ready" ⇐ `pre_flight_checks_pass=1` ⇐ wyczyszczenie „No connection to GCS" ⇐ klient MAVSDK/GCS ⇐ **moduł lotu, który I2b odracza DO PO „Ready". Circular.** Dowód: boot1 moduł lotu NIGDY nie ruszył (`act.log`=komunikat env-fail I2b), 0 MAVSDK w `stack.log`, GCS nieczyszczony, EKF czysty → „Ready" strukturalnie nieosiągalne. **Każdy boot z I2b (E/S/N po INFRA-1) nie osiągnie „Ready" niezależnie od zdrowia maszyny.**

**KONSEKWENCJA DLA INFRA-1 (istotna):** **werdykt shakeoutu N3 (FAIL → „trwała patologia mostu gz↔PX4") jest NIEWAŻNY jako dowód.** Shakeout boot0/boot1 użył harnessu I2b → deadlock **przed** próbą arm → NIGDY nie przetestował, czy maszyna armuje po resecie. EKF boot1 faktycznie zbiegł (czysty 252 s) — silna przesłanka, że blokerem był harness, nie most. **Osobno:** pierwotne env-faile S boot4/5/6 (STARY harness) to INNY, realny tryb — moduł lotu ruszył, MAVSDK podłączony, arm **DENIED** przez health (`arm niegotowe retry #0..#15`, 40×) — ten tryb pozostaje realny i nieobjaśniony przez deadlock. Dane: `C2_convergence_analysis.json`.

**WERDYKT S2:** boot1 = **deadlock harnessu I2b** (ani niezbieżność EKF, ani zwykły wall-timeout). Bliżej strony „trywialny fix harnessu" (S3) niż „niezbieżność". **C5 (render) NIE jest właściwym następnym pomiarem** — deadlock nie ma związku z renderem.

### C5 — alternatywny backend renderu (jeden boot, gałąź E) — **ODROCZONY (nie warrantowany przez C2)**

Przygotowany: transientna zmiana `run_k1_boot.sh:12` → `GALLIUM_DRIVER=llvmpipe LIBGL_ALWAYS_SOFTWARE=1` (software render), reszta identyczna, kryterium = N3. **Boot NIE wykonany:** bramka I2a poprawnie zablokowała start — maszyna obciążona **niezależnym zadaniem Olgi** `src.runner.gate2 --run-id gate2-krok3 --jobs 8` (8 workerów, 8/24 rdzeni, loadavg≈8 ≥ próg 8.0). **Nie tknięto zadania Olgi.** Uruchomienie C5 pod tym obciążeniem skaziłoby pomiar dokładnie konfundatorem load↔render, który INFRA-1 wyeliminował (gdyby load chwilowo dipnął <8.0, boot ruszyłby skażony). Transient zrewertowany do byte-identycznego (`run_k1_boot.sh` clean, frozen-4 ✓). **C5 czeka na wolne okno maszyny** (po zakończeniu `gate2-krok3` albo w oknie wskazanym przez Olgę). Wynik binarny wejdzie tu po wykonaniu.

### §2-PROP (Q2). Propozycja poprawki konfiguracyjnej — **PROPOZYCJA, NIE WDROŻONA** (SI-1: wymaga ratyfikacji Olgi)

Po C2 właściwym celem jest **deadlock harnessu I2b** (nie lockstep, nie render, nie uxrce). Propozycje do ratyfikacji, żadna nie wdrożona, zasada „jedna zmiana" (SI-1):

- **P0 (GŁÓWNA, per S3) — usuń deadlock I2b.** I2b (`run_k1_boot.sh:73-87`) gatuje START modułu lotu na „Ready for takeoff", którego nie da się osiągnąć bez modułu lotu (MAVSDK→GCS). Dwa czyste warianty (jeden do wyboru przy ratyfikacji):
  - **P0a (rewert):** przywróć stary flow — moduł lotu startuje po `sleep 90` **bezwarunkowo** (jak N boot4/S4/5/6/R0.3a — wszystkie armowały). Najmniej kodu, znany-dobry.
  - **P0b (re-key sygnału):** jeśli chcemy zachować „arm-po-zbieżności", odmierzaj zbieżność z **osi sim / stanu EKF** (np. `pre_flt_fail_innov_*`=0 przez K s sim, dostępne w uORB/ulog), NIE ze stringa „Ready" (który zależy od GCS). Wtedy moduł lotu (MAVSDK) musi też startować w oknie oczekiwania, by GCS mógł się wyczyścić — inaczej deadlock wraca.
  - **Uwaga S3:** „odmierzanie okna w czasie sim zamiast wall" (pierwotna trywialna hipoteza Olgi) **NIE wystarcza** — sygnał „Ready" jest nieosiągalny niezależnie od długości okna. To deadlock, nie zwykły timeout.
- **P1 (render) — ZDJĘTA z kolejki jako następny krok.** C2 pokazał, że blokerem shakeoutu był harness, nie render. C5 pozostaje pomiarem opcjonalnym (jakość danych gz) **tylko na sygnał Olgi**, nie jako następstwo.
- **P2 (`UXRCE_DDS_SYNCT=0`) — zdegradowana do kosmetyki.** Uciszyłaby komunikaty „time jump" (`module.yaml:88`), ale C1/C2 pokazały, że timejump NIE psuje EKF ani nie blokuje arm (bloker=GCS/deadlock). Nie remedium; ewentualnie higiena logów, osobno.

**Rekomendacja:** wdrożyć wyłącznie **P0** (jeden wariant, po ratyfikacji), potem — skoro shakeout I2b był nieważny — **powtórzyć bramkę zdrowia maszyny na naprawionym harnessie** (pusty boot E armuje end-to-end), zanim zapadną decyzje kalendarzowe INFRA-1/K1.

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

## §2-WYK2. WYKONANE (ANEKS_INFRA2-3, CC 2026-08-25): I3 FAIL + mechanizm bias żyroskopu

I3 (dziesiątka) odpalona na CZYSTEJ maszynie po rewercie deadlocku I2b — **WERDYKT FAIL: 4/8 arm** (pełna
tabela + analiza w `RAPORT_INFRA1.md §6`). To domyka pytanie „czy po naprawie deadlocku maszyna armuje":
**nie niezawodnie** — arm-fail intermittentny ~50%, load-niezależny, to realny tryb S boot4/5/6.

**Mechanizm ZLOKALIZOWANY (Y4, offline z ulogów):** w bootach FAIL estymata **bias żyroskopu EKF ucieka
do ~0.14–0.15 rad/s** (monotoniczna dywergencja, nie wolna zbieżność), w PASS zostaje ~0 (0.0002). Bloker
arm = **`Preflight Fail: High Gyro Bias`** (nie innowacje — `pre_flt_fail_innov` czyste w OBU klasach).
⇒ **300 s okno jest bez znaczenia** — bias nie zbiega, on dywerguje; więcej czasu pogarsza. To **nie
wyścig o sekundy** — to genuinie zła estymata.

**Hipoteza rozgrzewki (CC#5, Y3): OBALONA danymi** — deep-stalle płaskie (7–8/boot, PASS≈FAIL), boot5
(5. boot, fail między PASS) łamie monotoniczność, oś czasu-WSL skażona (uptime dryf). Nie ma
deterministycznego „rozgrzania". Zostaje: stochastyczna dywergencja bias pod deep-stallami mostu.

**Kierunek (Y5):** Y4 NIE wyszło puste — wskazuje wprost na most gz↔PX4 jako źródło: **deep RTF-stalle
(rtf do 0.001, 7–8/boot w KAŻDYM bocie) psują całkowanie IMU w EKF → runaway gyro bias**, ale liczba
stalli sama nie różnicuje PASS/FAIL, więc bloker jest w **fazie/timingu stalli** względem inicjalizacji
estymatora, albo w treści danych IMU dostarczanych przez most podczas stalla (np. zdublowane/opóźnione
próbki, całkowane jako fałszywy obrót). **Pierwszy pomiar INFRA-2 właściwego = C5 (render/backend GPU)**
jako najtańszy sprawdzian, czy backend renderu zmienia częstość/głębokość stalli mostu (i przez to
częstość dywergencji bias). C5 tylko na sygnał Olgi (SI: jeden boot gałąź E, llvmpipe/software).

## §2-WYK3. WYKONANE (ANEKS_INFRA2-4, CC 2026-08-26): Z1 forensyka IMU — WERDYKT: **STRUMIEŃ ZDROWY**

Offline, zero bootów, na ulogach I3: FAIL {boot1,3,5} vs PASS {boot4,7}. Cztery miary (`Z1_imu_forensics.json`,
`tools/infra2_imu_forensics.py`):

| miara | FAIL {1,3,5} | PASS {4,7} | werdykt |
|-------|--------------|------------|---------|
| **(a) Δt `sensor_combined`** | 100.0% w 4000±100 µs, 0 dup, 0 gap, maxgap=4000 µs | 100% (b7: 1 gap 8000 µs, benign) | **czysta cadencja** |
| **(b) sample-and-hold (6 wartości bitowo=)** | **0 próbek**, 0 runów | 0 próbek | **brak zamrożenia** |
| **(c) okna 1 s zerowej wariancji gyro** | **0/214** | 0/174 | **brak martwych okien** |
| **(d) surowy gyro std, okno preflight [10,85] s** | **~0.00062 rad/s /oś** | **~0.00062 rad/s /oś** | **IDENTYCZNY** |

Piki gyro >0.05 rad/s w PASS (19079 w b4, absmax 26 rad/s) = **REALNY LOT po arm** (konfundator lot-vs-brak-lotu),
nie defekt strumienia — po ograniczeniu do wspólnego okna preflight [10,85] s (oba na ziemi) gyro/accel są
statystycznie **nieodróżnialne** (accel ≈ [0.05, 0.07, −9.80] = grawitacja; b7 lekko przechylony).

**Zagadka rozstrzygająca:** karmiony **czystym, płaskim gyro** (std 0.0006), EKF i tak produkuje dziko różne
biasy. Trajektoria `|gyro_bias|`:

| boot | @20 s | @50 s | @85 s | koniec | arm |
|------|------:|------:|------:|-------:|:---:|
| FAIL b1 | 0.147 | 0.183 | 0.177 | 0.150 | — |
| FAIL b3 | 0.107 | 0.127 | 0.134 | 0.138 | — |
| FAIL b5 | 0.137 | 0.134 | 0.155 | 0.150 | — |
| PASS b4 | 0.121 | 0.088 | 0.087 | **0.036** | 93.3 s |
| PASS b7 | 0.0001 | 0.0001 | 0.0001 | 0.0002 | 94.8 s |

Dyskryminator to **nie „czy bias urósł"** (b4 urósł jak faile) lecz **„czy zszedł poniżej progu przed oknem
arm"**: w FAIL bias **zatrzaskuje się 0.10–0.19 od sim ~20 s i NIE wraca**; b4 startuje wysoko, ale estymator
**odzyskuje** (→0.036); b7 czysty od startu. Bias jest już wysoki @20 s, gdy surowy gyro jest płaski.

**WERDYKT Z1: strumień IMU ZDROWY** (cadencja + wartości, obie klasy identyczne). **Dywergencja biasu to
fenomen EKF-WEWNĘTRZNY** — inicjalizacja/konwergencja stanu bias albo kolejność fuzji, NIE most dostarczający
zepsute próbki IMU.

**Z2 — gałąź „zdrowy strumień" (per ANEKS): C5 NIE jest warrantowany przyczynowo.** Prerejestrowana premisa
C5 (mniej deep-stalli ⇒ mniej odcinków hold ⇒ bias ~0 ⇒ arm) jest **falsyfikowana u podstawy**: hold=0 w
ogóle, IMU czyste niezależnie od stalli, a bias jest wysoki od sim ~20 s. Redukcja stalli renderu nie ma
kanału, przez który miałaby leczyć bias. **STOP — decyzja na danych, bez zgadywania.** Następny cut
(init/konwergencja EKF, kolejność fuzji, mag/baro) = osobny ANEKS od Olgi; NIE uruchamiam nic poza Z1.

## §2-WYK4. WYKONANE (ANEKS_INFRA2-5rev, CC 2026-08-26): V1 oś czasu źródeł — RÓŻNICUJE, ale NIE przez brak źródła

Offline, zero bootów, ulogi I3: b4 (odzysk 0.12→0.036), b7 (czysty), FAIL {1,3,5} (zatrzask).
`tools/infra2_fusion_timeline.py` + `V1_fusion_timeline.json`.

**(a) Wejście źródeł do fuzji [sim s] — `estimator_status_flags`:**

| boot | klasa | arm | tilt_align | yaw_align | baro_hgt | mag | gnss_pos | gps_hgt |
|------|-------|----:|-----------:|----------:|---------:|----:|---------:|--------:|
| 4 | PASS-recover | 93.3 | 14.57 | 15.68 | 3.73 | 15.68 | 15.68 | 3.44 |
| 7 | PASS-clean | 94.8 | 1.88 | 2.94 | 2.13 | 2.94 | 2.95 | 1.92 |
| 1 | FAIL | — | 6.57 | 7.68 | 3.57 | 7.68 | 7.70 | 3.31 |
| 3 | FAIL | — | 31.73 | 32.82 | 3.73 | 32.82 | 32.84 | 3.44 |
| 5 | FAIL | — | 29.98 | 31.07 | 3.59 | 31.07 | 31.10 | 3.31 |

Kolejność wejścia **identyczna** we wszystkich (tilt→yaw→mag/gnss; baro @~3.5 s, gnss @alignment).
**Alignment-latency NIE separuje** — b1 (FAIL) wyrównał @6.6 s, WCZEŚNIEJ niż b4 (recover) @14.6 s.
Wszystkie źródła obecne w każdym bocie; brak brakującego/martwego źródła.

**(b/e) Resety, time_slip, filter_fault — TU jest separacja:**

| boot | klasa | filter_fault | fs_bad_acc_vertical | reset_count_vel_d | reset_hgt_to_baro (zdarz.) | time_slip |
|------|-------|-------------:|--------------------:|------------------:|---------------------------:|----------:|
| 4 | PASS-recover | **0** | nigdy | 4 | 12 | 0.0 |
| 7 | PASS-clean | **0** | nigdy | 2 | 1 | 0.0 |
| 1 | FAIL | **1024** | 33.46 s | **32** | **35** | 0.0 |
| 3 | FAIL | **1024** | 54.82 s | **14** | **47** | 0.0 |
| 5 | FAIL | **1024** | 40.66 s | **22** | **55** | 0.0 |

**(c) tło:** baro (`vehicle_air_data`) kadencja 60 ms czysta (0% poza), hold 6–12 (kwantyzacja, benign) —
NIE zamrożone; mag (`vehicle_magnetometer`) hold=0 w obu — NIE zamrożone. Źródła wspomagające żywe.
**(d) px4.log ×8:** `High Gyro Bias` = 42/17/8/13 (FAIL b1/2/3/5) vs 0/0/0/1 (PASS b4/6/7/8);
`horizontal velocity unstable` = 30/20/13/25 vs 3/1/0/1; brak sztormu „No valid Baro"; `ekf2 missing data`
= 1 benign na starcie. Separacja HighGyroBias FAIL↔PASS spójna z tabelą (b).

**WERDYKT V1: oś czasu RÓŻNICUJE klasy — ale NIE przez brak/opóźnienie źródła wspomagającego.**
Separatory (czyste): `filter_fault_flags` FAIL=1024/PASS=0; `fs_bad_acc_vertical` FAIL wszystkie/PASS nigdy;
sztorm resetów pionu (`reset_count_vel_d` 14–32 vs 2–4, `reset_hgt_to_baro` 35–55 vs 1–12). Nie-separatory:
kolejność/dostępność źródeł, alignment-latency, `time_slip` (0.0 wszędzie), żywotność baro/mag. **Zatrzask
koreluje z WEWNĘTRZNYM sztormem faultu pionu (acc_vertical + height/vel_d reset + filter_fault 1024), nie
z brakiem źródła.** Fakt czasowy z tabeli: bias wysoki @~20 s (Z1) POPRZEDZA `fs_bad_acc_vertical` @33–55 s —
podane bez rozstrzygania kierunku przyczyny.

**V2 — STOP offline.** Oś czasu różnicuje, lecz hipoteza V1 (brak/opóźnienie źródła) NIE potwierdzona;
separator jest wewnętrzny, a jego KORZEŃ (dlaczego pion faultuje / co destabilizuje filtr) jest
nieodczytywalny z tej tabeli — bez interpretacji ponad tabelę. Następny krok = **eksperyment różnicowy na
parametrach inicjalizacji EKF / źródle faultu `acc_vertical`, OSOBNY dokument**, nie ta sesja.

## §5. Co JEST już ustalone (nie badać ponownie)

- Obciążenie CPU NIE jest driverem (INFRA-1 §1, pomiar). ✗ nie wracać.
- Strumień IMU (cadencja + wartości) ZDROWY w FAIL — brak hold, brak gap, gyro identyczny z PASS (Z1). ✗ nie wracać.
- Zatrzask NIE koreluje z brakiem/opóźnieniem źródła wspomagającego — wszystkie wchodzą w tej samej kolejności (V1). ✗ nie wracać.
- Separator FAIL↔PASS = fault pionu: filter_fault=1024, fs_bad_acc_vertical, sztorm reset_hgt/vel_d (V1). → dalej: różnicowy init EKF.
- time_slip=0.0 w FAIL i PASS — zegar estymatora nie ślizga (V1, spójne z C1). ✗ nie badać.
- Bias diverguje na CZYSTYM płaskim gyro ⇒ przyczyna EKF-wewnętrzna, nie most/IMU (Z1). → dalej: init/fuzja/mag/baro.
- C5 (render backend) NIE warrantowany przyczynowo — premisa hold-pod-stallami falsyfikowana (Z1/Z2). ✗ nie strzelać.
- Okno 300 s NIE jest za krótkie — bias żyroskopu DYWERGUJE, nie zbiega wolno (Y4). ✗ nie „dać więcej czasu".
- Rozgrzewka (numer bootu / czas-od-startu) NIE tłumaczy fail (Y3, boot5 wyłom, stalle płaskie). ✗ nie wracać.
- Timejumpy NIE różnicują arm (6–7 w PASS i FAIL) — artefakt uxrce (C1). ✗ nie bramkować nimi.
- Kontencja GUI NIE jest driverem — boot1 headless a pętla trwa (`GUI_PROCS=[brak]`). ✗ nie wracać.
- Stan sterownika GPU po restarcie NIE leczy — reset operatorski wykonany, FAIL identyczny. ✗ nie wracać.
- Osłona/sędzia/kryteria K1 zamrożone i nietknięte przez całe INFRA-1/2 (hashe w RAPORT_INFRA1). ✗ nie ruszać.
