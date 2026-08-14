#!/usr/bin/env bash
# a1_run.sh <RUN> — A1 dyskryminator 0b (detektor w pętli POD OBSERVE-motion, headless). Habitat H.1:
# HEADLESS zweryfikowany, RTF, time-jump zapisane. Wzorzec b0_run.sh. Artefakty NIE w /tmp.
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
B0SP="$ROOT/.b0deps/lib/python3.12/site-packages"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true
source env_gpu.sh >/dev/null 2>&1 || true
export HEADLESS=1
export GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA; export RENDER_BACKEND="mesa-d3d12"
RUN="${1:-run}"
OUTDIR="$ROOT/results/R02/livefed/A1/$RUN"; mkdir -p "$OUTDIR"

teardown(){ pkill -9 -f 'gz sim' 2>/dev/null; pkill -9 -f 'bin/px4' 2>/dev/null; pkill -9 -f MicroXRCEAgent 2>/dev/null
  pkill -9 -f mavsdk_server 2>/dev/null; pkill -9 -f 'parameter_bridge' 2>/dev/null; pkill -9 -f 'detector_node' 2>/dev/null
  pkill -9 -f 'ruby.*gz' 2>/dev/null; pkill -9 -x yes 2>/dev/null; sleep 2; }
teardown

LOGDIR="$OUTDIR" MODEL=gz_x500_mono_cam bash run_stack.sh > "$OUTDIR/stack.log" 2>&1
sleep 3; GUI=$(pgrep -af 'gz sim -g|gz-gui' | grep -v pgrep || echo "brak")
echo "GUI_PROCS=[$GUI]  gz_server=[$(pgrep -af 'gz sim .*-r|gz sim -s' | grep -v pgrep | head -1)]" | tee "$OUTDIR/headless_proof.txt"

IMG=""; for i in $(seq 1 40); do IMG=$(gz topic -l 2>/dev/null | grep -E "imager/image$" | head -1); [ -n "$IMG" ] && break; sleep 1; done
[ -z "$IMG" ] && { echo "[a1] BRAK kamery"; teardown; exit 5; }
echo "[a1] kamera: $IMG"

setsid nohup ros2 run ros_gz_bridge parameter_bridge "${IMG}@sensor_msgs/msg/Image[gz.msgs.Image" > "$OUTDIR/bridge.log" 2>&1 &
sleep 3

gz service -s /world/default/create --reqtype gz.msgs.EntityFactory --reptype gz.msgs.Boolean --timeout 3000 \
  --req "sdf_filename: \"$ROOT/r02/intruder_model.sdf\", name: \"intruder\", pose: {position: {x: 7, y: 0, z: 10}}" > "$OUTDIR/spawn.log" 2>&1

YOLO_WEIGHTS="$ROOT/.b0deps/weights/yolov8s-worldv2.pt" PYTHONPATH="$B0SP:$ROOT:${PYTHONPATH:-}" \
  setsid nohup python3 -m r02.detector_node --image-topic "$IMG" > "$OUTDIR/detector.log" 2>&1 &
echo "[a1] detektor start; 90 s settle EKF + wagi"; sleep 90

grep -ci 'time jump\|Resetting time sync' "$OUTDIR/stack.log" > "$OUTDIR/timejump_pre.txt" 2>/dev/null || echo 0 > "$OUTDIR/timejump_pre.txt"

OUTDIR="$OUTDIR" IMG_TOPIC="$IMG" HEADLESS=1 RENDER_BACKEND="$RENDER_BACKEND" \
  PYTHONPATH="$B0SP:$ROOT:${PYTHONPATH:-}" python3 results/R02/livefed/a1_flight.py > "$OUTDIR/a1.log" 2>&1
RC=$?
grep -ci 'time jump\|Resetting time sync' "$OUTDIR/stack.log" > "$OUTDIR/timejump_post.txt" 2>/dev/null || true
# zdrowie EKF (H.1 zaostrzenie E2): brak High Gyro Bias / velocity unstable
grep -ciE 'High Gyro Bias|velocity unstable|horizontal velocity' "$OUTDIR/px4.log" > "$OUTDIR/ekf_health_hits.txt" 2>/dev/null || echo 0 > "$OUTDIR/ekf_health_hits.txt"
teardown
echo "[a1] $RUN DONE rc=$RC → $OUTDIR"; exit $RC
