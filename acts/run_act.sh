#!/usr/bin/env bash
# acts/run_act.sh <A1|A2> [RUN] — DEMO-B B4 rehearsal online (SITL, headless, ANEKS-H). Boot world_demo_<ACT>
# (z kamerą filmową), spawn intruza (MODEL), bridge+capture kamery filmowej (pipeline R2), scenariusz
# gate_run_r02 SCEN=<ACT> GT_FED=1 (kanał deterministyczny; token path B1). NIE próba (B5). Wzorzec mti_run.sh.
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
B0SP="$ROOT/.b0deps/lib/python3.12/site-packages"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true
source env_gpu.sh >/dev/null 2>&1 || true
export HEADLESS=1 GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA RENDER_BACKEND="mesa-d3d12"
ACT="$1"; RUN="${2:-rehearsal_online_1}"
[ "$ACT" = "A1" ] || [ "$ACT" = "A2" ] || { echo "użycie: run_act.sh A1|A2 [RUN]"; exit 2; }
WORLD="world_demo_${ACT}"
OUTDIR="$ROOT/results/demo/rehearsal/${ACT}/${RUN}"; mkdir -p "$OUTDIR" "$OUTDIR/frames"
cp "$ROOT/worlds/${WORLD}.sdf" "$ROOT/PX4-Autopilot/Tools/simulation/gz/worlds/${WORLD}.sdf"
sha256sum "$ROOT/worlds/${WORLD}.sdf" | tee "$OUTDIR/world_hash.txt"

teardown(){ pkill -9 -f 'gz sim' 2>/dev/null; pkill -9 -f 'bin/px4' 2>/dev/null; pkill -9 -f MicroXRCEAgent 2>/dev/null
  pkill -9 -f mavsdk_server 2>/dev/null; pkill -9 -f 'parameter_bridge' 2>/dev/null; pkill -9 -f 'gate_run_r02' 2>/dev/null
  pkill -9 -f 'ruby.*gz' 2>/dev/null; sleep 2; }
teardown

LOGDIR="$OUTDIR" WORLD="$WORLD" MODEL=gz_x500_mono_cam bash run_stack.sh > "$OUTDIR/stack.log" 2>&1
sleep 3
GUI=$(pgrep -af 'gz sim -g|gz-gui' | grep -v pgrep || echo "brak")
echo "GUI_PROCS=[$GUI]" | tee "$OUTDIR/headless_proof.txt"
for i in $(seq 1 40); do gz topic -l 2>/dev/null | grep -q "/world/${WORLD}/clock" && break; sleep 1; done

# kamera FILMOWA (sensor 'film' w modelu film_cam) → bridge + zapis klatek (pipeline R2)
FILM=""; for i in $(seq 1 40); do FILM=$(gz topic -l 2>/dev/null | grep -iE "film.*image$" | head -1); [ -n "$FILM" ] && break; sleep 1; done
echo "FILM_TOPIC=$FILM" | tee "$OUTDIR/film_topic.txt"
[ -z "$FILM" ] && { echo "[act] BRAK kamery filmowej"; teardown; exit 5; }
setsid nohup ros2 run ros_gz_bridge parameter_bridge "${FILM}@sensor_msgs/msg/Image[gz.msgs.Image" > "$OUTDIR/bridge.log" 2>&1 &
sleep 3

gz service -s /world/${WORLD}/create --reqtype gz.msgs.EntityFactory --reptype gz.msgs.Boolean --timeout 3000 \
  --req "sdf_filename: \"$ROOT/r02/intruder_model.sdf\", name: \"intruder\", pose: {position: {x: 7, y: 0, z: 11.5}}" > "$OUTDIR/spawn.log" 2>&1

echo "[act] 150 s settle EKF (ANEKS-H)"; sleep 150
grep -ci 'time jump\|Resetting time sync' "$OUTDIR/stack.log" > "$OUTDIR/timejump_pre.txt" 2>/dev/null || echo 0 > "$OUTDIR/timejump_pre.txt"

# KADR-CHECK (§3): intruz w pierścieniu (x=7.86) → 1 klatka filmowa PRZED rehearsalem
gz service -s /world/${WORLD}/set_pose --reqtype gz.msgs.Pose --reptype gz.msgs.Boolean --timeout 3000 \
  --req 'name: "intruder", position: {x: 7.86, y: 0, z: 11.5}, orientation: {w: 1.0}' > /dev/null 2>&1
sleep 2
python3 "$ROOT/r02/capture_frame.py" "$FILM" "$OUTDIR/frames/kadr_check.npy" 8 > "$OUTDIR/kadr_check.log" 2>&1 || true

# grabber klatek filmowych w tle (pipeline kamera→pliki, R2) — co ~2 s, positional capture_frame
( for i in $(seq 1 20); do python3 "$ROOT/r02/capture_frame.py" "$FILM" "$OUTDIR/frames/f_$(printf %02d $i).npy" 3 >/dev/null 2>&1; sleep 2; done ) &
GRABBER=$!

TRACE="$OUTDIR/trace.jsonl" GT_FED=1 SCENARIO="$ACT" PX4_GZ_WORLD="$WORLD" HEADLESS=1 \
  PYTHONPATH="$B0SP:$ROOT:${PYTHONPATH:-}" python3 -m r02.gate_run_r02 > "$OUTDIR/act.log" 2>&1
RC=$?
kill "$GRABBER" 2>/dev/null
grep -ci 'time jump\|Resetting time sync' "$OUTDIR/stack.log" > "$OUTDIR/timejump_post.txt" 2>/dev/null || true
grep -ciE 'High Gyro Bias|velocity unstable|horizontal velocity' "$OUTDIR/px4.log" > "$OUTDIR/ekf_health_hits.txt" 2>/dev/null || echo 0 > "$OUTDIR/ekf_health_hits.txt"
teardown
echo "[act] $ACT $RUN DONE rc=$RC → $OUTDIR"; exit $RC
