#!/usr/bin/env bash
# results/W_RECON/run_sonda_boot.sh — launcher sondy wiatru (noga W, RECON_W §R2).
# NIE edytuje frozen harness/run_boot.sh. Wstrzykuje model z enable_wind przez GZ_SIM_RESOURCE_PATH
# (gz_env.sh:19 DOPISUJE do tej zmiennej → nasza kopia x500_base rozwiązuje się PIERWSZA dla model://x500_base).
# Boot WYŁĄCZNIE przez harness/run_boot.sh (SR-W-2/-6). FLIGHT=empty = hover-only (tools/infra1_empty_flight.py).
# Użycie:  run_sonda_boot.sh <BOOT_N> <WORLD>
set -o pipefail
ROOT=/home/olga/projects/liquidpatrol
cd "$ROOT"
BOOT_N="${1:?BOOT_N}"; WORLD="${2:?WORLD (world_wind_s0|s3|s6)}"
export GZ_SIM_RESOURCE_PATH="$ROOT/worlds/wind_models${GZ_SIM_RESOURCE_PATH:+:$GZ_SIM_RESOURCE_PATH}"
FLIGHT=empty WORLD="$WORLD" BOOT_N="$BOOT_N" \
  OUTDIR="$ROOT/results/W_RECON/boot${BOOT_N}" \
  K1_HOVER_S=90 SETTLE_S=90 KIND=wind_sonda \
  bash harness/run_boot.sh
