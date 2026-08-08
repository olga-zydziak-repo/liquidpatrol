#!/usr/bin/env bash
# r02/run_signal_sweep.sh — STATYCZNY sweep sygnału (bez lotu): stack + most + detektor + sweep.
# Dron na ziemi (kamera Północ), intruz przesuwany przez zasięgi. Teardown po PID.
set -o pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$ROOT"
LOGDIR="${LOGDIR:-/tmp/r02/SWEEP}"; mkdir -p "$LOGDIR"
WORLD=default; B0SP="$ROOT/.b0deps/lib/python3.12/site-packages"; PIDS=()
cleanup() {
  for p in "${PIDS[@]}"; do kill "$p" 2>/dev/null; done
  pkill -9 -f "signal_sweep" 2>/dev/null; pkill -9 -f "detector_node" 2>/dev/null
  pkill -9 -f "ros_gz_bridge/parameter_bridge" 2>/dev/null
  pkill -9 -f "px4_sitl_default/bin/px4" 2>/dev/null; pkill -9 -f "gz sim" 2>/dev/null
  pkill -9 -x MicroXRCEAgent 2>/dev/null; sleep 2
}
trap cleanup EXIT

echo "[sweep] === STATYCZNY sweep sygnału ==="
MODEL=gz_x500_mono_cam ./run_stack.sh > "$LOGDIR/stack.log" 2>&1
IMG_TOPIC=""
for i in $(seq 1 40); do
  IMG_TOPIC=$(gz topic -l 2>/dev/null | grep -E "imager/image$" | head -1)
  [ -n "$IMG_TOPIC" ] && break; sleep 1
done
[ -z "$IMG_TOPIC" ] && { echo "[sweep] BRAK kamery — STOP"; exit 2; }
echo "[sweep] kamera: $IMG_TOPIC"
source /opt/ros/jazzy/setup.bash; source "$ROOT/ros2_ws/install/setup.bash"
setsid nohup ros2 run ros_gz_bridge parameter_bridge \
  "${IMG_TOPIC}@sensor_msgs/msg/Image[gz.msgs.Image" > "$LOGDIR/bridge.log" 2>&1 &
PIDS+=($!); sleep 3
# spawn intruza (start daleko; sweep go przestawi)
gz service -s "/world/${WORLD}/create" --reqtype gz.msgs.EntityFactory --reptype gz.msgs.Boolean \
  --timeout 3000 --req "sdf_filename: \"$ROOT/r02/intruder_model.sdf\", name: \"intruder\", pose: {position: {x: 8, y: 0, z: 2}}" > "$LOGDIR/spawn.log" 2>&1
echo "[sweep] intruz: $(cat $LOGDIR/spawn.log)"
YOLO_WEIGHTS="$ROOT/.b0deps/weights/yolov8s-worldv2.pt" \
  PYTHONPATH="$B0SP:$ROOT:${PYTHONPATH:-}" setsid nohup python3 -m r02.detector_node \
  --image-topic "$IMG_TOPIC" > "$LOGDIR/detector.log" 2>&1 &
PIDS+=($!); echo "[sweep] detektor pid=${PIDS[-1]}"; sleep 8
echo "[sweep] start sweep"
PYTHONPATH="$ROOT:${PYTHONPATH:-}" python3 -m r02.signal_sweep "$WORLD" "$LOGDIR/sweep.jsonl" 2>&1 | tee "$LOGDIR/sweep.log"
echo "[sweep] === koniec sweep ==="
