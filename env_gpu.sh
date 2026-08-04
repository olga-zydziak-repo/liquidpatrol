#!/usr/bin/env bash
# env_gpu.sh — wymusza akceleracje GPU (D3D12) dla renderu OpenGL pod WSL2.
# Zmierzone w RECON_R0: bez tych zmiennych renderer = llvmpipe (software).
# Z nimi: D3D12 (NVIDIA GeForce RTX 5070 Ti Laptop GPU), OpenGL 4.6.
# Uzycie:  source env_gpu.sh   (przed uruchomieniem gz / Gazebo)
export GALLIUM_DRIVER=d3d12
export MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
export LIBGL_ALWAYS_SOFTWARE=0
# vblank off — nie limituj FPS do odswiezania kompozytora WSLg (pomiar RTF/FPS)
export vblank_mode=0
echo "[env_gpu] GALLIUM_DRIVER=$GALLIUM_DRIVER MESA_D3D12_DEFAULT_ADAPTER_NAME=$MESA_D3D12_DEFAULT_ADAPTER_NAME"
