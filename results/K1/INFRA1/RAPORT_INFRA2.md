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
