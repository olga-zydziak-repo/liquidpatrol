#!/usr/bin/env bash
# r02/run_attrib.sh — sonda atrybucyjna STATYCZNA (tor A): stack+most+detektor, dron NA ZIEMI,
# intruz w zadanej pozie (INTRUDER_POSE="x,y,z"), przechwyt klatki+meta+conf. Teardown po PID.
# Użycie: INTRUDER_POSE="7,0,1.9" OUT_PREFIX=/tmp/r02/ATTR/static ./r02/run_attrib.sh
set -o pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$ROOT"
LOGDIR="${LOGDIR:-/tmp/r02/ATTR}"; mkdir -p "$LOGDIR"
WORLD=default; B0SP="$ROOT/.b0deps/lib/python3.12/site-packages"; PIDS=()
IP="${INTRUDER_POSE:-7,0,1.9}"; OUT="${OUT_PREFIX:-$LOGDIR/static}"
cleanup() { for p in "${PIDS[@]}"; do kill "$p" 2>/dev/null; done
  pkill -9 -f "attrib_probe" 2>/dev/null; pkill -9 -f "detector_node" 2>/dev/null
  pkill -9 -f "ros_gz_bridge/parameter_bridge" 2>/dev/null
  pkill -9 -f "px4_sitl_default/bin/px4" 2>/dev/null; pkill -9 -f "gz sim" 2>/dev/null
  pkill -9 -x MicroXRCEAgent 2>/dev/null; sleep 2; }
trap cleanup EXIT

MODEL=gz_x500_mono_cam ./run_stack.sh > "$LOGDIR/stack.log" 2>&1
IMG=""; for i in $(seq 1 40); do IMG=$(gz topic -l 2>/dev/null | grep -E "imager/image$" | head -1); [ -n "$IMG" ] && break; sleep 1; done
[ -z "$IMG" ] && { echo "[attr] BRAK kamery"; exit 2; }
echo "[attr] kamera: $IMG"
source /opt/ros/jazzy/setup.bash; source "$ROOT/ros2_ws/install/setup.bash"
setsid nohup ros2 run ros_gz_bridge parameter_bridge "${IMG}@sensor_msgs/msg/Image[gz.msgs.Image" > "$LOGDIR/bridge.log" 2>&1 &
PIDS+=($!); sleep 3
gz service -s "/world/${WORLD}/create" --reqtype gz.msgs.EntityFactory --reptype gz.msgs.Boolean \
  --timeout 3000 --req "sdf_filename: \"$ROOT/r02/intruder_model.sdf\", name: \"intruder\", pose: {position: {x: 8, y: 0, z: 2}}" > "$LOGDIR/spawn.log" 2>&1
IFS=',' read -r IX IY IZ <<< "$IP"
for t in 1 2 3; do gz service -s "/world/${WORLD}/set_pose" --reqtype gz.msgs.Pose --reptype gz.msgs.Boolean \
  --timeout 3000 --req "name: \"intruder\", position: {x: $IX, y: $IY, z: $IZ}, orientation: {w: 1.0}" >/dev/null 2>&1; sleep 1; done
echo "[attr] intruz poza: $(gz model -m intruder -p 2>/dev/null | grep -A1 XYZ | tail -1)"
YOLO_WEIGHTS="$ROOT/.b0deps/weights/yolov8s-worldv2.pt" PYTHONPATH="$B0SP:$ROOT:${PYTHONPATH:-}" \
  setsid nohup python3 -m r02.detector_node --image-topic "$IMG" > "$LOGDIR/detector.log" 2>&1 &
PIDS+=($!); sleep 10
echo "[attr] przechwyt klatki → $OUT"
PYTHONPATH="$B0SP:$ROOT:${PYTHONPATH:-}" python3 -m r02.attrib_probe "$IMG" "$OUT" 15 2>&1 | tee "$LOGDIR/probe.log"
echo "[attr] === koniec ==="
