# RAPORT_R0 — domknięcie bramki R0.0

Status: **KOMPLETNY**. Bramka R0.0 (PRE_R0 §3 + aneksy A1–A5) domknięta w sesji 2 (2026-08-05).
Poprzednik: `PRE_R0.md` (ratyfikowany, aneksy A1–A5), `SESJA2_START.md` (zamrożona kolejność).

## WERDYKT BRAMKI: **PASS — tryb GPU (D3D12)**

Wszystkie cztery warunki §3 + wszystkie aneksy A1–A5 spełnione i udokumentowane. Zejście na software **nie było konieczne** — cała bramka zaliczona z akceleracją GPU (D3D12/RTX 5070 Ti), nie llvmpipe. Reguła stopu §4 / A5 nie aktywowana (0 padów o sygnaturze pada).

---

## 1. Co postawione (stack)

PX4 SITL **v1.16.2** + Gazebo **Harmonic 8.14.0** + ROS 2 **Jazzy** (+`ros_gz`, `px4_msgs` release/1.16) + **MicroXRCE-DDS-Agent v2.4.3** (most PX4↔ROS2) + MAVSDK-Python. WSL2 / Ubuntu 24.04.4 / RTX 5070 Ti. Render wymuszony na GPU D3D12 przez `env_gpu.sh`.

Skrypty odtwarzalności w repo: `install_ros2_jazzy.sh`, `install_gazebo_harmonic.sh`, `install_px4.sh`, `install_microxrce.sh`, `env_gpu.sh`, `render_check.sh`, `run_stack.sh`, `soak_monitor.sh`, `run_boots.sh`, `run_hello_mission.py`, `mavsdk_telemetry_check.py`, `a1_topic_rate.py`.

## 2. Wyniki bramki §3 (zamrożonej przed budową)

| # | Kryterium §3 | Wynik | Dowód |
|---|---|:---:|---|
| §3.1 | hello-mission 3× bez pada GPU | **PASS** | 3× na 1 instancji (sesja 1) **+ 3× NIEZALEŻNY boot** (zaostrzenie, sesja 2) → `hello_mission_runs.md`, `independent_boots.md` |
| §3.2 | Render GPU (D3D12, NIE llvmpipe) + RTF | **PASS** | `GL_RENDERER = D3D12 (RTX 5070 Ti)` podczas misji/soaku/3×boot; RTF raportowany → `s32_gpu_mission.md`, `render_fingerprint.md` |
| §3.3 | Telemetria offboard z Pythona | **PASS** | MAVSDK: połączenie, health armable, strumień pozycji ciągły (każdy boot) → `hello_mission_runs.md` |
| §3.4 | Powtarzalność (skrypty) | **PASS** | pełny łańcuch `install_*.sh` + launchery/monitory w repo |

## 3. Wyniki aneksów A1–A5

| Aneks | Kryterium | Wynik | Kluczowa liczba | Dowód |
|---|---|:---:|---|---|
| **A1** | Żywe ogniwa: `/fmu/out/vehicle_odometry` ≥10 Hz cały lot + ≥1 topik gz→ROS2 | **PASS** | odom **99.9 Hz** (min 97), `/clock` **249.7 Hz** — jednoczesny uXRCE-DDS + ros_gz_bridge | `a1_link_liveness.md` |
| **A2** | Soak ≥15 min z `gz_x500_mono_cam`→ROS2, bez pada | **PASS** | **927 s**, kamera **15.8→11.8 Hz** (ciągła), 0 padów | `a2_soak.md` |
| **A3** | Renderer z logu + pin wersji | **PASS** (dowód) | D3D12; Mesa 25.2.8 / WSL2 6.18.33.2 / WSLg 1.0.73.2 / NVIDIA 577.13 | `render_fingerprint.md` |
| **A4** | Misja domknięta (itemy+land+disarm), pozycja bez przerwy >1 s; RTF | **PASS** (bramka) / raport (RTF) | max przerwa **≤0.03 s**; RTF avg **0.99982** (29 prób) | `hello_mission_runs.md`, `a2_soak.md`, `independent_boots.md` |
| **A5** | Zejście po ≥3 padach tej samej sygnatury LUB budżet §4 | **NIE aktywowane** | **0 padów** o sygnaturze pada; próg 0/3 | poniżej + `a2_soak.md` |

## 4. Stabilność / ryzyko GPU (rdzeń §4)

Ryzyko główne (exit-144 / `dxg ioctl -22` — pad sterownika GPU pod obciążeniem) **NIE zmaterializowało się jako pad**. Przez cały realny stress (soak 927 s z renderem kamery D3D12 + 3× boot z misją): **CaptureCrash = 0, oops/BUG/panic = 0, 0 śmierci procesu.**

**Sygnatury dmesg pod obciążeniem GPU (jawnie, uczciwie):**
- `dxgkrnl fortify: field-spanning write` (`WARNING`, dxgvmbus.c:3093/3095) — kernel WARN (`Tainted:[W]`, nie die), znany benign WSL2-kernel-6.18 false-positive; 0 przyrostu w oknie soaku. Blok: `a2_dmesg_warning_block.txt`.
- `dxgkio_escape: -75` (EOVERFLOW) flood — ścieżka escape ioctl dxgk, benign; 0 przyrostu w soaku.
- `query_adapter_info: -22` — szum `nvidia-smi`/`glxinfo` (ustalone empirycznie §3.2), 0 koincydencji ze śmiercią procesu.

**Zaostrzenie A5 #3 (ta sesja, empiryczne):** pod renderem kamery D3D12 pojawia się NOWA sygnatura (`fortify WARN` + `escape -75`), RÓŻNA od sygnatury pada A5. Kryterium pada pozostaje: **`dxg`/awaria sterownika KOINCYDENTNA ze śmiercią procesu** (`CaptureCrash`/SIGABRT/zatrzymanie renderu). Bare WARN/`-75`/`-22` bez śmierci procesu = NIE pad, nie kumulować. Weryfikacja soaku: 0 nowych sygnatur pada w 927 s.

Teardown (intencjonalny kill stacku) generuje benign exit-144 + `dxg -2`/`-512` (`ERESTARTSYS` z przerwanego syscalla) — artefakt zarządzania procesami, NIE pad (`teardown_dmesg_note.md`).

## 5. Fingerprint środowiska

Ubuntu 24.04.4 LTS · kernel/WSL2 6.18.33.2-microsoft-standard-WSL2 · WSLg 1.0.73.2 · Mesa 25.2.8 · NVIDIA 577.13 · GPU RTX 5070 Ti Laptop · gz-sim 8.14.0 · ROS 2 Jazzy · PX4 v1.16.2 · MicroXRCE-DDS-Agent v2.4.3. GL: D3D12, OpenGL 4.6. Pełne: `render_fingerprint.md`.

## 6. Rozbieżności (rejestr)

1. **Ionic → Harmonic** — zaakceptowane w PRE (LTS 2028 vs EOL Ionic 09.2026).
2. **RAM 15 GB → build PX4 `-j6`** (nie `-j24`) — bez OOM. Zadziałało.
3. **Render GPU nie domyślny** — wymaga `env_gpu.sh` (D3D12); domyślnie llvmpipe.
4. **apt IPv6 w WSL pada** — wymuszony `ForceIPv4` (`/etc/apt/apt.conf.d/99force-ipv4`).
5. **Push przed etapem B — NIEZREALIZOWANY (proceduralna).** Push nieinteraktywny niemożliwy po stronie asystenta. Kolejność PRE→build udowodniona **łańcuchem commitów** (`a720cd6` PRE → `22d997f` RATYFIKOWANE → commity budowy) — historia git świadczy o porządku niezależnie od momentu push. Push wykonuje Olga. Bez wpływu na integralność porządku PRE→B.
6. **`ros2 topic hz` bez opcji QoS w Jazzy (metodyczna, zaostrzenie).** Domyślnie RELIABLE → nie odbiera BEST_EFFORT tematów PX4 `/fmu/out` ani mostu kamery. Pomiary A1/A2 wykonane własnym `a1_topic_rate.py` z jawnym QoS best_effort + binowaniem per-sekunda (min/s, nie tylko avg). To zaostrzenie, nie złagodzenie.
7. **Nowa sygnatura dmesg pod GPU-load (zaostrzenie precyzji A5)** — patrz §4; benign, nie liczona do progu A5.
8. **Tożsamość git nieustawiona w sesji 2 (proceduralna)** — ustawiona lokalnie `olga <pogromcawszy@gmail.com>` (spójnie z poprzednimi commitami) przed commitami sesji 2.

## 7. Zakres — co NIE zostało zrobione (jawnie)

R0.0 to test **infrastruktury**, nie systemu. Płaszczyzna sterowania R0.1 (MAVSDK vs XRCE offboard przez `px4_msgs`) pozostaje **OTWARTA** — R0.0 jej nie przesądza. Slot pilota/estymatora oraz port z `liquidsight` (osłona ALLOW/HOLD/REFUSE, Z3, gramatyka/admisja komend) — przyszłe fazy (PRE §5).

## 8. Konkluzja

**Bramka R0.0 ZALICZONA (PASS) w trybie GPU (D3D12).** Stack PX4 SITL + Gazebo + ROS 2 stoi stabilnie na tej maszynie; hello-mission powtarzalny (3× na instancji + 3× niezależny boot), render na GPU udowodniony podczas obciążenia, telemetria offboard i oba mosty (uXRCE-DDS, ros_gz_bridge) żywe, soak 15 min z kamerą bez pada. Zejście na software nie było potrzebne. Push do remote wykonuje Olga.
