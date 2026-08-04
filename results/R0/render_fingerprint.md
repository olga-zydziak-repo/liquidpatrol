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
