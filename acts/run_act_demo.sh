#!/usr/bin/env bash
# acts/run_act_demo.sh <A1|A2> <RUN> [OUTDIR] — DEMO-B ANEKS_D6: bieg aktu z kanałem GT-fed (§1a) —
# manifest-po-arm (§0/§2), kamera filmowa (montaż), teleport FF widocznego intruza (sim_t, §7a/§6a),
# ZERO live-MTI (gt_mode pomija detektor+mono-bridge). Konfig B4-detekcji + infra B5 (manifest/film/FF).
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
B0SP="$ROOT/.b0deps/lib/python3.12/site-packages"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true
source env_gpu.sh >/dev/null 2>&1 || true
export HEADLESS=1 GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA RENDER_BACKEND="mesa-d3d12"
ACT="$1"; RUN="${2:-proba_1}"
[ "$ACT" = "A1" ] || [ "$ACT" = "A2" ] || { echo "użycie: run_act_demo.sh A1|A2 RUN"; exit 2; }
WORLD="world_demo_${ACT}"
OUTDIR="$3"; [ -z "$OUTDIR" ] && OUTDIR="$ROOT/results/demo/${ACT}/${RUN}"
mkdir -p "$OUTDIR/frames"
cp "$ROOT/worlds/${WORLD}.sdf" "$ROOT/PX4-Autopilot/Tools/simulation/gz/worlds/${WORLD}.sdf"

teardown(){ pkill -9 -f 'gz sim' 2>/dev/null; pkill -9 -f 'px4_sitl' 2>/dev/null; pkill -9 -f MicroXRCEAgent 2>/dev/null
  pkill -9 -f mavsdk_server 2>/dev/null; pkill -9 -f 'parameter_bridge' 2>/dev/null; pkill -9 -f 'gate_run_r02' 2>/dev/null
  pkill -9 -f 'ruby.*gz' 2>/dev/null; sleep 2; }
teardown
# D3 higiena GPS (A3 zostawia EKF2_GPS_CTRL=0)
python3 "$ROOT/acts/ensure_gps_enabled.py" 2>&1 | tee -a "$OUTDIR/gps_hygiene.txt" || python3 "$ROOT/acts/ensure_gps_enabled.py"

HEAD=$(git rev-parse HEAD)
export MANIFEST_OUT="$OUTDIR/manifest.json" WORLD_SDF="$ROOT/worlds/${WORLD}.sdf" HEAD_SHA="$HEAD"

LOGDIR="$OUTDIR" WORLD="$WORLD" PX4_GZ_WORLD="$WORLD" MODEL=gz_x500_mono_cam bash run_stack.sh > "$OUTDIR/stack.log" 2>&1
sleep 3
echo "GUI_PROCS=[$(pgrep -af 'gz sim -g|gz-gui' | grep -v pgrep || echo brak)]" | tee "$OUTDIR/headless_proof.txt"
for i in $(seq 1 40); do gz topic -l 2>/dev/null | grep -q "/world/${WORLD}/clock" && break; sleep 1; done
FILM=$(gz topic -l 2>/dev/null | grep -iE "film.*image$" | head -1)
echo "FILM=$FILM" | tee "$OUTDIR/topics.txt"
sleep 3
gz service -s /world/${WORLD}/create --reqtype gz.msgs.EntityFactory --reptype gz.msgs.Boolean --timeout 3000 \
  --req "sdf_filename: \"$ROOT/r02/intruder_model.sdf\", name: \"intruder\", pose: {position: {x: 7.86, y: 0, z: 11.5}}" > "$OUTDIR/spawn.log" 2>&1

echo "[demo] 210 s settle EKF (jak B4/B5)"; sleep 210
grep -ci 'time jump\|Resetting time sync' "$OUTDIR/stack.log" > "$OUTDIR/timejump_pre.txt" 2>/dev/null || echo 0 > "$OUTDIR/timejump_pre.txt"

# kamera filmowa (montaż) — bridge + grabber (za flagą FILM_CAPTURE, domyślnie 1 dla dema)
GRABBER=""
if [ "${FILM_CAPTURE:-1}" = "1" ] && [ -n "$FILM" ]; then
  setsid nohup ros2 run ros_gz_bridge parameter_bridge "${FILM}@sensor_msgs/msg/Image[gz.msgs.Image" > "$OUTDIR/bridge_film.log" 2>&1 &
  python3 "$ROOT/r02/capture_frame.py" "$FILM" "$OUTDIR/frames/kadr_check.npy" 8 > "$OUTDIR/kadr_check.log" 2>&1 || true
  ( for i in $(seq 1 60); do python3 "$ROOT/r02/capture_frame.py" "$FILM" "$OUTDIR/frames/f_$(printf %03d $i).npy" 2 >/dev/null 2>&1; sleep 1.0; done ) & GRABBER=$!
fi

# scenariusz GT-fed (§1a): GT_FED=1 → gt_channel (B4), detektor LIVE POMINIĘTY. Teleport FF widoczny intruz.
TRACE="$OUTDIR/trace.jsonl" GT_FED=1 SCENARIO="$ACT" PX4_GZ_WORLD="$WORLD" HEADLESS=1 CONTENTION="${CONTENTION:-none}" \
  PYTHONPATH="$B0SP:$ROOT:${PYTHONPATH:-}" python3 -m r02.gate_run_r02 > "$OUTDIR/act.log" 2>&1
RC=$?
kill "$GRABBER" 2>/dev/null
grep -ci 'time jump\|Resetting time sync' "$OUTDIR/stack.log" > "$OUTDIR/timejump_post.txt" 2>/dev/null || true
grep -ciE 'High Gyro Bias|velocity unstable|horizontal velocity' "$OUTDIR/px4.log" > "$OUTDIR/ekf_health_hits.txt" 2>/dev/null || echo 0 > "$OUTDIR/ekf_health_hits.txt"
teardown
echo "[demo] $ACT $RUN DONE rc=$RC → $OUTDIR"; exit $RC
