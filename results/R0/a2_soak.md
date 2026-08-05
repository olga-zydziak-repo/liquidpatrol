# A2 — soak pod obciążeniem (bramka §3 pkt 6) — 2026-08-05

Stack: PX4 SITL **v1.16.2** (`gz_x500_mono_cam`) + Gazebo **Harmonic 8.14.0** (serwer `-r -s` + GUI `gz sim -g`, **D3D12**) + MicroXRCE-DDS-Agent v2.4.3 + `ros_gz_bridge` (kamera→ROS2), ROS2 Jazzy. WSL2 / RTX 5070 Ti.
Launcher: `run_stack.sh` (model=`gz_x500_mono_cam`, GUI/GPU); monitor: `soak_monitor.sh`.

## Wynik: **PASS** — 927 s ciągłego symu z aktywną kamerą mostkowaną do ROS2, bez pada

| Kryterium A2 | Wymóg | Zmierzone | Werdykt |
|---|---|---|:---:|
| Czas ciągłego symu | ≥15 min (900 s) | **927 s** (30 próbek co ~30 s) | **PASS** |
| Sensor kamery aktywny + mostkowany do ROS2 | tak, niezerowo | topik `…/imager/image` → `sensor_msgs/msg/Image`, **15.8 Hz** na starcie, **11.8 Hz po 15 min** (ciągły) | **PASS** |
| Bez pada | brak śmierci procesu / CaptureCrash / oops | **CaptureCrash=0, oops=0**, wszystkie procesy żywe do końca (agent+px4+gz serwer+GUI+bridge) | **PASS** |
| RTF (A4, niebramkujący) | raportowany | min **0.9982** / avg **0.99982** / max **1.0011** (29 próbek) | raport |
| GPU (niebramkujący) | raportowany | ~25 % util, 930 MiB (nvidia-smi 1×, wg A5) | raport |

Renderer PODCZAS i PO soaku: `GL_RENDERER = D3D12 (NVIDIA GeForce RTX 5070 Ti Laptop GPU)`, GL 4.6 — **nie llvmpipe**. Kamera x500_mono_cam renderowana ogre2/D3D12 na serwerze gz przez cały czas = realny stress GPU (intencja §4).

Topik kamery (auto-scoped przez gz): `/world/default/model/x500_mono_cam_0/link/camera_link/sensor/imager/image`.
Metoda pomiaru kamery: `a1_topic_rate.py` z jawnym QoS **best_effort** (most obrazów publikuje SENSOR_DATA/best_effort → `ros2 topic hz` domyślnie RELIABLE nie odbiera — ten sam mechanizm co A1). Uwaga: werdykt „FAIL" z `a1_topic_rate.py` dotyczy progu ≥10 Hz z **A1** i NIE ma zastosowania do kamery — A2 wymaga jedynie strumienia niezerowego i raportowanego.

## Dyscyplina A5 — sygnatury dmesg podczas soaku (jawnie, uczciwie)

W dmesg obecne są następujące wpisy sterownika WSL `dxgkrnl`. **Kluczowe: żadna z tych sygnatur NIE przyrosła podczas 927 s okna soaku** — wszystkie pochodzą z bootu WSL i/lub fazy pomiarowej PRZED startem monitora. Podczas samego soaku: 0 nowych.

| Sygnatura dmesg | Liczba (koniec soaku) | Przyrost w oknie soaku | Ocena wg A5 |
|---|---:|:---:|---|
| `CaptureCrash` (śmierć procesu) | **0** | 0 | brak — kryterium pada NIE zaszło |
| `kernel BUG / Oops / panic-not-syncing` | **0** | 0 | brak (uwaga: `panic=-1` w cmdline to param bootowy WSL, nie zdarzenie) |
| `dxgkrnl fortify: field-spanning write` (dxgvmbus.c:3093/3095) `WARNING` | 2 | **0** | **NIE pad** — kernel `WARNING` (`Tainted:[W]=WARN`, nie die), znany benign WSL2-6.18 fortify false-positive; 1× przy boocie [3.6 s], 1× w fazie pomiaru [864 s]; wątek `queue1:src` (worker renderu gz). GPU op kończą się poprawnie. |
| `dxgkio_escape: Ioctl failed: -75` (EOVERFLOW) | 134 | **0** | **NIE pad** — ścieżka escape ioctl dxgk, benign; brak korelacji ze śmiercią procesu |
| `dxgkio_query_adapter_info: Ioctl failed: -22` | 52 | +8 (poza soakiem) | **NIE pad** — szum `nvidia-smi`/`glxinfo` (ustalone empirycznie w §3.2); brak koincydencji ze śmiercią procesu |

**Nowa sygnatura odnotowana (zaostrzenie precyzji A5):** `dxgkrnl fortify field-spanning write` + zalew `dxgkio_escape: -75` pojawiają się pod obciążeniem renderu kamery D3D12. Obie to **kernel-side WARN/benign** sterownika Microsoft `dxgkrnl` (WSL2 kernel 6.18), NIE awaria: brak oops, brak śmierci procesu, sim w pełni zdrowy (RTF ~1.0, D3D12, kamera+px4+gz żyją). Sygnatura ta jest RÓŻNA od sygnatury pada A5 (`dxg -22` KOINCYDENTNE ze śmiercią procesu / `CaptureCrash`). Blok WARNING zapisany: `results/R0/a2_dmesg_warning_block.txt`.

**Werdykt A5:** 0 padów. Próg „≥3 pady tej samej sygnatury" NIE osiągnięty (0/3). Zejście po drabinie (§4) NIE aktywowane. Bramka A2 zaliczona w trybie **GPU** (nie software).

## Artefakty
- `results/R0/soak_monitor.log` (kopia: `/tmp/r0_soak/soak_monitor.log`) — 30 próbek zdrowia + RTF.
- `results/R0/a2_dmesg_warning_block.txt` — pełny blok kernel WARNING (dxgkrnl fortify).
- Launcher/monitor w repo: `run_stack.sh`, `soak_monitor.sh`.
