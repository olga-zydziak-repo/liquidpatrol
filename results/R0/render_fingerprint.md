# RENDER FINGERPRINT (A3) — 2026-08-04T21:41:59Z

## Werdykt: Gazebo Harmonic renderuje na GPU D3D12 (NIE llvmpipe)

### OGRE2 renderer (z ~/.gz/rendering/ogre2.log):
GL_VERSION = 4.6 (Compatibility Profile) Mesa 25.2.8-0ubuntu0.24.04.2
GL_VENDOR = Microsoft Corporation
GL_RENDERER = D3D12 (NVIDIA GeForce RTX 5070 Ti Laptop GPU)
GPU Vendor: microsoft
Device Name: D3D12 (NVIDIA GeForce RTX 5070 Ti Laptop GPU)

### Srodowisko wymuszajace GPU (env_gpu.sh):
GALLIUM_DRIVER=d3d12  MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA  LIBGL_ALWAYS_SOFTWARE=0

### Pinning wersji:
OS:            Ubuntu 24.04.4 LTS
Kernel/WSL:    6.18.33.2-microsoft-standard-WSL2
WSLg:          WSLg ( x86_64 ): 1.0.73.2
Gazebo (gz-sim): 8.14.0
Mesa:          Mesa 25.2.8
NVIDIA driver: 577.13 (WSL), 577.13 (Win)
GPU:           NVIDIA GeForce RTX 5070 Ti Laptop GPU

---

## ROZSZERZENIE SESJA 2 (A3, stan końcowy) — 2026-08-05

Pin wersji potwierdzony niezmieniony na koniec bramki; renderer weryfikowany **podczas** obciążenia (misja + soak kamery), nie tylko standalone.

| Warstwa | Wersja (pin, koniec sesji 2) | Źródło |
|---|---|---|
| OS | Ubuntu 24.04.4 LTS | `/etc/os-release` |
| Kernel / WSL2 | 6.18.33.2-microsoft-standard-WSL2 | `uname -r` |
| WSLg | 1.0.73.2 | (sesja 1, niezmienione) |
| Mesa | 25.2.8-0ubuntu0.24.04.2 | `glxinfo -B` (pod `env_gpu`) |
| GL renderer | **D3D12 (NVIDIA GeForce RTX 5070 Ti Laptop GPU)**, GL 4.6 | `glxinfo -B` / `~/.gz/rendering/ogre2.log` |
| Gazebo (gz-sim) | 8.14.0 | `gz sim --version` |
| ROS 2 | Jazzy | `$ROS_DISTRO` |
| PX4 | v1.16.2 | `git -C PX4-Autopilot describe --tags` |
| MicroXRCE-DDS-Agent | v2.4.3 | `install_microxrce.sh` (agent nie ma `--version`) |
| NVIDIA driver | 577.13 (WSL/Win) | (sesja 1, niezmienione) |
| GPU | NVIDIA GeForce RTX 5070 Ti Laptop GPU | — |

**Renderer PODCZAS obciążenia (nie standalone):**
- §3.2 misja z GUI: `GL_RENDERER = D3D12 (NVIDIA RTX 5070 Ti)`, RTF ~0.99 (`s32_gpu_mission.md`).
- A2 soak 927 s z kamerą: renderer D3D12 przez cały czas, RTF avg 0.99982 (`a2_soak.md`).
- 3× niezależny boot: renderer D3D12 w każdym (`independent_boots.md`).

**Zmienne wymuszające GPU** (`env_gpu.sh`, w repo): `GALLIUM_DRIVER=d3d12`, `MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA`, `LIBGL_ALWAYS_SOFTWARE=0`, `vblank_mode=0`. Bez nich renderer = llvmpipe (software). Odtwarzalny dowód: `render_check.sh`.

**Sygnatury dmesg pod obciążeniem GPU (sesja 2, jawnie):** `dxgkrnl fortify field-spanning WARN` + `dxgkio_escape -75` (EOVERFLOW) + `query_adapter_info -22` — wszystkie **benign** (kernel WARN / szum narzędzi), 0 koincydencji ze śmiercią procesu, 0 przyrostu w oknie soaku. Szczegóły + blok WARNING: `a2_soak.md`, `a2_dmesg_warning_block.txt`. Nie liczą się do progu A5 (patrz PRE §4, doprecyzowania #1/#2).
