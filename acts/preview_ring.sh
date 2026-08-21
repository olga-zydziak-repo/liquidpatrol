#!/usr/bin/env bash
# acts/preview_ring.sh — U2R-2 §2: PREVIEW kontrastu sylwetki intruza. Boot world_demo_A1, spawn intruz
# na ringu (7.86,0,11.5), 1 klatka kamery filmowej. Bez settle/aktu. Ocena PRZED bramką.
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true
source env_gpu.sh >/dev/null 2>&1 || true
export HEADLESS=1 GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA RENDER_BACKEND="mesa-d3d12"
WORLD="world_demo_A1"; OUT="${1:-results/demo/A1_v3_1/preview}"; mkdir -p "$OUT"
cp "$ROOT/worlds/${WORLD}.sdf" "$ROOT/PX4-Autopilot/Tools/simulation/gz/worlds/${WORLD}.sdf"
teardown(){ pkill -9 -f 'gz sim'; pkill -9 -f 'bin/px4'; pkill -9 -f MicroXRCEAgent; pkill -9 -f parameter_bridge; pkill -9 -f 'ruby.*gz'; sleep 2; }
teardown
LOGDIR="$OUT" WORLD="$WORLD" PX4_GZ_WORLD="$WORLD" MODEL=gz_x500_mono_cam bash run_stack.sh > "$OUT/stack.log" 2>&1
sleep 3
for i in $(seq 1 40); do gz topic -l 2>/dev/null | grep -q "/world/${WORLD}/clock" && break; sleep 1; done
FILM=""; for i in $(seq 1 40); do FILM=$(gz topic -l 2>/dev/null | grep -iE "film.*image$" | head -1); [ -n "$FILM" ] && break; sleep 1; done
echo "FILM=$FILM"
gz service -s /world/${WORLD}/create --reqtype gz.msgs.EntityFactory --reptype gz.msgs.Boolean --timeout 3000 \
  --req "sdf_filename: \"$ROOT/r02/intruder_model.sdf\", name: \"intruder\", pose: {position: {x: 7.86, y: 0, z: 11.5}}" > "$OUT/spawn.log" 2>&1
sleep 8
setsid nohup ros2 run ros_gz_bridge parameter_bridge "${FILM}@sensor_msgs/msg/Image[gz.msgs.Image" > "$OUT/bridge.log" 2>&1 &
sleep 3
python3 "$ROOT/r02/capture_frame.py" "$FILM" "$OUT/preview.npy" 8 > "$OUT/cap.log" 2>&1
teardown
echo "[preview] done → $OUT/preview.npy"
