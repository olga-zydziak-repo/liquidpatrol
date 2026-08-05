#!/usr/bin/env bash
# run_scenario.sh — świeży boot + kamera-load (A4) + scenariusz bramki + Hz kamery + dmesg-check.
# Dyscyplina: KAŻDY scenariusz na świeżym boocie (zaostrzenie jawne, wzorzec R0.0).
# Użycie: r01/run_scenario.sh S1|S2|S3|S4
set -uo pipefail
ROOT="$HOME/projects/liquidpatrol"; cd "$ROOT"
SC="${1:?podaj scenariusz S1|S2|S3|S4}"
OUT="/tmp/r01"; mkdir -p "$OUT"
set +u
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source ros2_ws/install/setup.bash 2>/dev/null || true
set -u
source env_gpu.sh >/dev/null 2>&1

echo "==== $SC: teardown stare + baseline dmesg ===="
pkill -9 -x px4 2>/dev/null || true; pkill -9 -x ruby 2>/dev/null || true
pkill -9 -x MicroXRCEAgent 2>/dev/null || true; pkill -9 -x mavsdk_server 2>/dev/null || true
pkill -9 -f parameter_bridge 2>/dev/null || true; sleep 2
BASE_CAP=$(dmesg 2>/dev/null | grep -cE "CaptureCrash")

echo "==== $SC: boot stack (gz_x500_mono_cam, kamera-load A4) ===="
MODEL=gz_x500_mono_cam timeout 70 ./run_stack.sh > "$OUT/boot_$SC.out" 2>&1 || true
sleep 1
CAM="/world/default/model/x500_mono_cam_0/link/camera_link/sensor/imager/image"
setsid nohup ros2 run ros_gz_bridge parameter_bridge "${CAM}@sensor_msgs/msg/Image[gz.msgs.Image" > "$OUT/cam_bridge_$SC.log" 2>&1 &
# A4: pomiar Hz kamery w tle (raportowany, nie bramkujący)
( timeout 50 python3 a1_topic_rate.py "$CAM" sensor_msgs/msg/Image 45 best_effort > "$OUT/cam_hz_$SC.log" 2>&1 ) &

echo "==== $SC: gate_run ===="
SCENARIO="$SC" TRACE="$OUT/gate_$SC.jsonl" timeout 300 python3 -m r01.gate_run 2>&1 | grep -vE "^INFO|mavlink_command_sender" | tail -15
RC=$?

echo "==== $SC: teardown + dmesg-check ===="
pkill -9 -x px4 2>/dev/null || true; pkill -9 -x ruby 2>/dev/null || true
pkill -9 -x MicroXRCEAgent 2>/dev/null || true; pkill -9 -x mavsdk_server 2>/dev/null || true
pkill -9 -f parameter_bridge 2>/dev/null || true; sleep 2
CAP=$(dmesg 2>/dev/null | grep -cE "CaptureCrash")
OOPS=$(dmesg 2>/dev/null | grep -cE "kernel BUG|Oops:|Kernel panic - not syncing")
echo "[$SC] dmesg: CaptureCrash $BASE_CAP->$CAP  oops=$OOPS  (pad tylko gdy dxg-22 koincydentne ze smiercia)"
echo "[$SC] kamera Hz (A4, raportowane):" ; grep -E "wiadomosci|avg" "$OUT/cam_hz_$SC.log" 2>/dev/null | tail -1
echo "[$SC] gate_run rc=$RC"
