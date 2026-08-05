#!/usr/bin/env bash
# camera_probe.sh — S3-3: rozdziel przyczyny niskiego Hz kamery (contention/most/QoS/RTF).
# Dla każdej konfiguracji: gz-side rate (gz-transport bezpośrednio) vs ROS2-bridge rate + RTF.
# Wynik = wejście do R0.2, NIE bramka R0.1.
set -uo pipefail
ROOT="$HOME/projects/liquidpatrol"; cd "$ROOT"
OUT="/tmp/r01/cam"; mkdir -p "$OUT"
set +u; source /opt/ros/jazzy/setup.bash 2>/dev/null; source ros2_ws/install/setup.bash 2>/dev/null; set -u
source env_gpu.sh >/dev/null 2>&1
CAM="/world/default/model/x500_mono_cam_0/link/camera_link/sensor/imager/image"

measure() {
  local tag="$1" w="$2" h="$3" rate="$4"
  echo "==== KONFIG $tag: ${w}x${h}@${rate} ===="
  pkill -9 -x px4 2>/dev/null||true; pkill -9 -x ruby 2>/dev/null||true
  pkill -9 -x MicroXRCEAgent 2>/dev/null||true; pkill -9 -f parameter_bridge 2>/dev/null||true; sleep 2
  # ustaw config kamery
  SDF="$ROOT/PX4-Autopilot/Tools/simulation/gz/models/mono_cam/model.sdf"
  sed -i -E "s#<width>[0-9]+</width>#<width>${w}</width>#; s#<height>[0-9]+</height>#<height>${h}</height>#; s#<update_rate>[0-9]+</update_rate>#<update_rate>${rate}</update_rate>#" "$SDF"
  MODEL=gz_x500_mono_cam timeout 70 ./run_stack.sh > "$OUT/boot_$tag.out" 2>&1 || true
  sleep 3
  # RTF
  RTF=$(timeout 4 gz topic -e -t /world/default/stats 2>/dev/null | grep -m1 real_time_factor | awk '{print $2}')
  # gz-side: czas na 15 wiadomosci kamery (gz-transport, bez ROS), echo->null
  local t0 t1 gzhz
  t0=$(date +%s.%N)
  timeout 25 gz topic -e -t "$CAM" -n 15 >/dev/null 2>&1 || true
  t1=$(date +%s.%N)
  gzhz=$(awk -v a="$t0" -v b="$t1" 'BEGIN{d=b-a; print (d>0)?15/d:0}')
  # ROS2-bridge rate (best_effort, 10s)
  setsid nohup ros2 run ros_gz_bridge parameter_bridge "${CAM}@sensor_msgs/msg/Image[gz.msgs.Image" > "$OUT/br_$tag.log" 2>&1 &
  sleep 2
  ROShz=$(timeout 16 python3 a1_topic_rate.py "$CAM" sensor_msgs/msg/Image 10 best_effort 2>&1 | grep -oE "avg=[0-9.]+" | head -1)
  pkill -9 -f parameter_bridge 2>/dev/null||true
  echo "[$tag] RTF=$RTF  gz_side_hz=$(printf '%.1f' "$gzhz")  ROS2_bridge_$ROShz  (img=${w}x${h}x3=$((w*h*3/1024))KB)"
}

measure "640x480_15" 640 480 15
measure "320x240_15" 320 240 15
measure "320x240_30" 320 240 30
# teardown + przywroc A4 (640x480@15)
pkill -9 -x px4 2>/dev/null||true; pkill -9 -x ruby 2>/dev/null||true
pkill -9 -x MicroXRCEAgent 2>/dev/null||true; pkill -9 -f parameter_bridge 2>/dev/null||true
sed -i -E "s#<width>[0-9]+</width>#<width>640</width>#; s#<height>[0-9]+</height>#<height>480</height>#; s#<update_rate>[0-9]+</update_rate>#<update_rate>15</update_rate>#" "$ROOT/PX4-Autopilot/Tools/simulation/gz/models/mono_cam/model.sdf"
echo "[cam] przywrocono A4 640x480@15"
