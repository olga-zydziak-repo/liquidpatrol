#!/usr/bin/env bash
# install_ros2_jazzy.sh — ROS 2 Jazzy (desktop) + ros_gz (most Gazebo Harmonic) na Ubuntu 24.04.
# Metoda: ros-apt-source .deb (aktualna). Idempotentne.
set -euo pipefail

echo "[1/5] universe + narzedzia"
sudo apt-get install -y -qq software-properties-common curl
sudo add-apt-repository -y universe
sudo apt-get update -qq

echo "[2/5] repo ROS2 (ros-apt-source)"
ROS_APT_SOURCE_VERSION=$(curl -fsSL https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F '"tag_name"' | awk -F'"' '{print $4}')
CODENAME=$(. /etc/os-release && echo "$VERSION_CODENAME")
curl -fsSL -o /tmp/ros2-apt-source.deb \
  "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.${CODENAME}_all.deb"
sudo apt-get install -y /tmp/ros2-apt-source.deb
sudo apt-get update -qq

echo "[3/5] ros-jazzy-desktop (duze)"
sudo apt-get install -y ros-jazzy-desktop

echo "[4/5] ros_gz (most Gazebo Harmonic <-> ROS2) + dev tools"
sudo apt-get install -y ros-jazzy-ros-gz python3-colcon-common-extensions python3-vcstool

echo "[5/5] weryfikacja"
# shellcheck disable=SC1091
source /opt/ros/jazzy/setup.bash
echo "ROS_DISTRO=$ROS_DISTRO ; ros2 = $(command -v ros2)"
echo "[OK] ROS2 Jazzy gotowe"
