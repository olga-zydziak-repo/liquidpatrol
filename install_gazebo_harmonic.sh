#!/usr/bin/env bash
# install_gazebo_harmonic.sh — Gazebo Harmonic (gz-sim) na Ubuntu 24.04.
# Zrodlo: packages.osrfoundation.org (oficjalne). Idempotentne.
set -euo pipefail

echo "[1/3] zaleznosci repo"
sudo apt-get update -qq
sudo apt-get install -y -qq curl lsb-release gnupg

echo "[2/3] klucz + repo OSRF"
sudo curl -fsSL https://packages.osrfoundation.org/gazebo.gpg \
  --output /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" \
  | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null
sudo apt-get update -qq

echo "[3/3] gz-harmonic"
sudo apt-get install -y gz-harmonic

echo "[OK] gz --versions:"; gz sim --versions 2>/dev/null || gz --versions
