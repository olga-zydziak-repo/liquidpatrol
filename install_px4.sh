#!/usr/bin/env bash
# install_px4.sh — PX4-Autopilot v1.16.2 (SITL) + zaleznosci, build px4_sitl_default.
# Pin: v1.16.2 (stabilny tag; ratyfikowany §2 PRE_R0). Build z -j6 (limit RAM 15 GB).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

PX4_TAG="v1.16.2"

echo "[1/4] klon PX4 (rekurencyjny)"
if [ ! -d PX4-Autopilot/.git ]; then
  git clone --recursive https://github.com/PX4/PX4-Autopilot.git
fi
cd PX4-Autopilot
git checkout "$PX4_TAG"
git submodule update --init --recursive

echo "[2/4] zaleznosci (ubuntu.sh, bez NuttX — SITL nie potrzebuje)"
bash Tools/setup/ubuntu.sh --no-nuttx

echo "[3/4] build px4_sitl_default (-j6, limit RAM)"
nice make px4_sitl_default -j6

echo "[4/4] weryfikacja binarki"
ls -la build/px4_sitl_default/bin/px4 && echo "[OK] PX4 SITL $PX4_TAG zbudowany"
