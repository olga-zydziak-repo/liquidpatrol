#!/usr/bin/env bash
# acts/run_act_live.sh <A1|A2> <RUN> — DEMO-B B5 bieg LIVE (detektor YOLO, ZERO GT-fed). Boot world_demo_<ACT>,
# bridge kamery MONO drona (→detector_node) + kamery FILMOWEJ (→capture), spawn+driver intruza (MODEL),
# scenariusz gate_run_r02 SCENARIO=<ACT> BEZ GT_FED (kanał z detector_node przez ChannelSub). Token path B1.
# Manifest PRZED scenariuszem (§2). Wzorzec run_act.sh + livefed/a1_run.sh. Artefakty w podanym OUTDIR.
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
B0SP="$ROOT/.b0deps/lib/python3.12/site-packages"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true
source env_gpu.sh >/dev/null 2>&1 || true
export HEADLESS=1 GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA RENDER_BACKEND="mesa-d3d12"
ACT="$1"; RUN="${2:-proba_1}"
[ "$ACT" = "A1" ] || [ "$ACT" = "A2" ] || { echo "użycie: run_act_live.sh A1|A2 RUN"; exit 2; }
WORLD="world_demo_${ACT}"
OUTDIR="$3"; [ -z "$OUTDIR" ] && OUTDIR="$ROOT/results/demo/${ACT}/${RUN}"
mkdir -p "$OUTDIR/frames"
cp "$ROOT/worlds/${WORLD}.sdf" "$ROOT/PX4-Autopilot/Tools/simulation/gz/worlds/${WORLD}.sdf"

teardown(){ pkill -9 -f 'gz sim' 2>/dev/null; pkill -9 -f 'px4_sitl' 2>/dev/null; pkill -9 -f MicroXRCEAgent 2>/dev/null
  pkill -9 -f mavsdk_server 2>/dev/null; pkill -9 -f 'parameter_bridge' 2>/dev/null; pkill -9 -f 'detector_node' 2>/dev/null
  pkill -9 -f 'gate_run_r02' 2>/dev/null; pkill -9 -f 'ruby.*gz' 2>/dev/null; sleep 2; }
teardown
# D3 fix (5R3): higiena GPS — reset leftover EKF2_GPS_CTRL=0 (po A3) do 7 przed bootem
python3 "$ROOT/acts/ensure_gps_enabled.py" 2>&1 | tee -a "${OUT:-$OUTDIR}/gps_hygiene.txt" || python3 "$ROOT/acts/ensure_gps_enabled.py"

# MANIFEST emitowany PRZEZ RUNNER PO bring_up (§0/§2 reconc.): env-fail bootu/health = NIE-próba
# (crash PRZED manifestem), crash choreografii = próba. Env dla runnera:
HEAD=$(git rev-parse HEAD)
export MANIFEST_OUT="$OUTDIR/manifest.json"
export WORLD_SDF="$ROOT/worlds/${WORLD}.sdf"
export HEAD_SHA="$HEAD"

LOGDIR="$OUTDIR" WORLD="$WORLD" PX4_GZ_WORLD="$WORLD" MODEL=gz_x500_mono_cam bash run_stack.sh > "$OUTDIR/stack.log" 2>&1
sleep 3
echo "GUI_PROCS=[$(pgrep -af 'gz sim -g|gz-gui' | grep -v pgrep || echo brak)]" | tee "$OUTDIR/headless_proof.txt"
for i in $(seq 1 40); do gz topic -l 2>/dev/null | grep -q "/world/${WORLD}/clock" && break; sleep 1; done

# kamera MONO drona (detektor) + kamera FILMOWA (capture)
MONO=""; for i in $(seq 1 40); do MONO=$(gz topic -l 2>/dev/null | grep -E "imager/image$" | head -1); [ -n "$MONO" ] && break; sleep 1; done
FILM=$(gz topic -l 2>/dev/null | grep -iE "film.*image$" | head -1)
echo "MONO=$MONO FILM=$FILM" | tee "$OUTDIR/topics.txt"
[ -z "$MONO" ] && { echo "[live] BRAK kamery mono"; teardown; exit 5; }
sleep 3
gz service -s /world/${WORLD}/create --reqtype gz.msgs.EntityFactory --reptype gz.msgs.Boolean --timeout 3000 \
  --req "sdf_filename: \"$ROOT/r02/intruder_model.sdf\", name: \"intruder\", pose: {position: {x: 7.86, y: 0, z: 11.5}}" > "$OUTDIR/spawn.log" 2>&1

# SETTLE EKF CAŁKOWICIE BEZ obciążenia LIVE (bridge/detektor) — jak B4 GT-fed który armował czysto.
# Bridge mono + detektor startują DOPIERO PO settle (4 env-fail w poprzedniej sesji: bridge/YOLO w
# oknie settle/arm → EKF/nav-health nie zbiega → BRAK health). Diagnostyka: izolacja obciążenia settle.
echo "[live] 210 s settle EKF (BEZ bridge/detektora — czysta zbieżność jak B4)"; sleep 210
grep -ci 'time jump\|Resetting time sync' "$OUTDIR/stack.log" > "$OUTDIR/timejump_pre.txt" 2>/dev/null || echo 0 > "$OUTDIR/timejump_pre.txt"
# Bridge mono + detektor uruchamia SCENARIUSZ (gate_run_r02) PO bring_up/arm — diagnoza: obciążenie
# LIVE przy arm blokowało MAVSDK/GCS ('No connection to GCS', 5 env-fail). Env dla runnera:
export LIVE_DETECTOR_TOPIC="$MONO"
export DETECTOR_LOG="$OUTDIR/detector.log"
export YOLO_WEIGHTS="$ROOT/.b0deps/weights/yolov8s-worldv2.pt"
if [ "${FILM_CAPTURE:-0}" = "1" ] && [ -n "$FILM" ]; then
  setsid nohup ros2 run ros_gz_bridge parameter_bridge "${FILM}@sensor_msgs/msg/Image[gz.msgs.Image" > "$OUTDIR/bridge_film.log" 2>&1 &
fi
GRABBER=""
if [ "${FILM_CAPTURE:-0}" = "1" ] && [ -n "$FILM" ]; then
  python3 "$ROOT/r02/capture_frame.py" "$FILM" "$OUTDIR/frames/kadr_check.npy" 8 > "$OUTDIR/kadr_check.log" 2>&1 || true
  ( for i in $(seq 1 40); do python3 "$ROOT/r02/capture_frame.py" "$FILM" "$OUTDIR/frames/f_$(printf %03d $i).npy" 2 >/dev/null 2>&1; sleep 1.2; done ) & GRABBER=$!
fi

# P0/P1 (5P): logger DBG detektora (sonda, SR-J2 probe_*) — subskrybuje detector_debug/target_channel
if [ "${DBG_LOG:-0}" = "1" ]; then
  setsid nohup python3 "$ROOT/acts/dbg_logger.py" "$OUTDIR/dbg.jsonl" 120 > "$OUTDIR/dbg_logger.log" 2>&1 &
fi

# scenariusz LIVE (BEZ GT_FED) — kanał z detector_node
TRACE="$OUTDIR/trace.jsonl" SCENARIO="$ACT" PX4_GZ_WORLD="$WORLD" HEADLESS=1 \
  PYTHONPATH="$B0SP:$ROOT:${PYTHONPATH:-}" python3 -m r02.gate_run_r02 > "$OUTDIR/act.log" 2>&1
RC=$?
kill "$GRABBER" 2>/dev/null
grep -ci 'time jump\|Resetting time sync' "$OUTDIR/stack.log" > "$OUTDIR/timejump_post.txt" 2>/dev/null || true
grep -ciE 'High Gyro Bias|velocity unstable|horizontal velocity' "$OUTDIR/px4.log" > "$OUTDIR/ekf_health_hits.txt" 2>/dev/null || echo 0 > "$OUTDIR/ekf_health_hits.txt"
teardown
echo "[live] $ACT $RUN DONE rc=$RC → $OUTDIR"; exit $RC
