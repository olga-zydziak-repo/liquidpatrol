#!/usr/bin/env bash
# install_microxrce.sh — Micro-XRCE-DDS-Agent (most PX4 uXRCE-DDS <-> ROS2).
# Pin v2.4.3 (zgodny z klientem PX4 v1.16.2 / microcdr 2.0.1). Superbuild sciaga Fast-CDR/Fast-DDS.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_TAG="v2.4.3"
cd "$ROOT"

if command -v MicroXRCEAgent >/dev/null 2>&1; then
  echo "[xrce] MicroXRCEAgent juz zainstalowany: $(command -v MicroXRCEAgent)"; exit 0
fi

echo "[1/3] klon Agent $AGENT_TAG"
if [ ! -d Micro-XRCE-DDS-Agent/.git ]; then
  git clone -b "$AGENT_TAG" --depth 1 https://github.com/eProsima/Micro-XRCE-DDS-Agent.git
fi
cd Micro-XRCE-DDS-Agent

echo "[2/3] build (cmake superbuild, -j4 limit RAM)"
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -DUAGENT_BUILD_TESTS=OFF
make -j4
sudo make install
sudo ldconfig /usr/local/lib/

echo "[3/3] weryfikacja"
command -v MicroXRCEAgent && MicroXRCEAgent --help >/dev/null 2>&1 && echo "[OK] MicroXRCEAgent zainstalowany"
