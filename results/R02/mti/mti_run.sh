#!/usr/bin/env bash
# mti_run.sh <RUN> — B4/B5 bieg MTI w world_demo_v1 (headless, ANEKS-H). Kopiuje świat, boot, bridge kamery,
# spawn intruza, mti_flight.py (YOLO+MTI+brama). Env: PHASES, DWELL_S, FP_EMPTY_S, FP_BG_S, RANGES. Artefakty
# w results/R02/mti/<STEP>/<RUN>/ (SR-N6). Wzorzec a1_run.sh.
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
B0SP="$ROOT/.b0deps/lib/python3.12/site-packages"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true
source env_gpu.sh >/dev/null 2>&1 || true
export HEADLESS=1
export GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA; export RENDER_BACKEND="mesa-d3d12"
WORLD="world_demo_v1"
STEP="${STEP:-B4}"; RUN="${1:-run}"
OUTDIR="$ROOT/results/R02/mti/$STEP/$RUN"; mkdir -p "$OUTDIR"
cp "$ROOT/worlds/world_demo_v1.sdf" "$ROOT/PX4-Autopilot/Tools/simulation/gz/worlds/world_demo_v1.sdf"
sha256sum "$ROOT/worlds/world_demo_v1.sdf" | tee "$OUTDIR/world_hash.txt"

teardown(){ pkill -9 -f 'gz sim' 2>/dev/null; pkill -9 -f 'bin/px4' 2>/dev/null; pkill -9 -f MicroXRCEAgent 2>/dev/null
  pkill -9 -f mavsdk_server 2>/dev/null; pkill -9 -f 'parameter_bridge' 2>/dev/null; pkill -9 -f 'mti_flight' 2>/dev/null
  pkill -9 -f 'ruby.*gz' 2>/dev/null; sleep 2; }
teardown

LOGDIR="$OUTDIR" WORLD="$WORLD" MODEL=gz_x500_mono_cam bash run_stack.sh > "$OUTDIR/stack.log" 2>&1
sleep 3; GUI=$(pgrep -af 'gz sim -g|gz-gui' | grep -v pgrep || echo "brak")
echo "GUI_PROCS=[$GUI]  gz_server=[$(pgrep -af 'gz sim .*-r|gz sim -s' | grep -v pgrep | head -1)]" | tee "$OUTDIR/headless_proof.txt"

for i in $(seq 1 40); do gz topic -l 2>/dev/null | grep -q "/world/${WORLD}/clock" && break; sleep 1; done
IMG=""; for i in $(seq 1 40); do IMG=$(gz topic -l 2>/dev/null | grep -E "imager/image$" | head -1); [ -n "$IMG" ] && break; sleep 1; done
[ -z "$IMG" ] && { echo "[mti] BRAK kamery"; teardown; exit 5; }
echo "[mti] kamera: $IMG"

setsid nohup ros2 run ros_gz_bridge parameter_bridge "${IMG}@sensor_msgs/msg/Image[gz.msgs.Image" > "$OUTDIR/bridge.log" 2>&1 &
sleep 3
gz service -s /world/${WORLD}/create --reqtype gz.msgs.EntityFactory --reptype gz.msgs.Boolean --timeout 3000 \
  --req "sdf_filename: \"$ROOT/r02/intruder_model.sdf\", name: \"intruder\", pose: {position: {x: 7, y: 0, z: 10}}" > "$OUTDIR/spawn.log" 2>&1

echo "[mti] 150 s settle EKF (world_demo_v1 — zbieżność EKF+GCS wolna, ANEKS-H contention margin)"; sleep 150
grep -ci 'time jump\|Resetting time sync' "$OUTDIR/stack.log" > "$OUTDIR/timejump_pre.txt" 2>/dev/null || echo 0 > "$OUTDIR/timejump_pre.txt"

OUTDIR="$OUTDIR" IMG_TOPIC="$IMG" HEADLESS=1 RENDER_BACKEND="$RENDER_BACKEND" PX4_GZ_WORLD="$WORLD" \
  PHASES="${PHASES:-sweep,fp_empty,fp_bg}" DWELL_S="${DWELL_S:-30}" FP_EMPTY_S="${FP_EMPTY_S:-300}" FP_BG_S="${FP_BG_S:-300}" \
  RANGES="${RANGES:-5,7,9}" YOLO_WEIGHTS="$ROOT/.b0deps/weights/yolov8s-worldv2.pt" \
  PYTHONPATH="$B0SP:$ROOT:${PYTHONPATH:-}" python3 results/R02/mti/mti_flight.py > "$OUTDIR/mti.log" 2>&1
RC=$?
grep -ci 'time jump\|Resetting time sync' "$OUTDIR/stack.log" > "$OUTDIR/timejump_post.txt" 2>/dev/null || true
grep -ciE 'High Gyro Bias|velocity unstable|horizontal velocity' "$OUTDIR/px4.log" > "$OUTDIR/ekf_health_hits.txt" 2>/dev/null || echo 0 > "$OUTDIR/ekf_health_hits.txt"
teardown
echo "[mti] $RUN DONE rc=$RC → $OUTDIR"; exit $RC
