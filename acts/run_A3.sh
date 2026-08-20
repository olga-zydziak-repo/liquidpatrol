#!/usr/bin/env bash
# acts/run_A3.sh [RUN] — DEMO-B B4 rehearsal AKT 3 (GPS-denied) w world_demo_A3 (kamera filmowa), SITL.
# Wyprowadzone z r03/run_gate_one.sh: boot + 90 s preflight EKF + gate_run_r03 SCEN=S2 (denial w patrolu
# → REFUSE(POS_DEGRADED) → velocity-descent → touchdown). Ścieżka R0.3a NIETKNIĘTA (proven RAPORT_R03A S2:
# touchdown 14.84 ≤ R_E, REFUSE 0.091 s). S2 t-denial (12 s) mapuje spec radial-denial (oba: containment).
# NIE próba (B5). Bridge+capture kamery filmowej (pipeline R2). Wzorzec run_act.sh.
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true
source env_gpu.sh >/dev/null 2>&1 || true
export HEADLESS=1 GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA RENDER_BACKEND="mesa-d3d12"
RUN="${1:-rehearsal_online_1}"; WORLD="world_demo_A3"
OUTDIR="$ROOT/results/demo/rehearsal/A3/${RUN}"; mkdir -p "$OUTDIR/frames"
cp "$ROOT/worlds/${WORLD}.sdf" "$ROOT/PX4-Autopilot/Tools/simulation/gz/worlds/${WORLD}.sdf"
sha256sum "$ROOT/worlds/${WORLD}.sdf" | tee "$OUTDIR/world_hash.txt"

teardown(){ pkill -9 -f 'gz sim' 2>/dev/null; pkill -9 -f 'px4_sitl' 2>/dev/null; pkill -9 -f MicroXRCEAgent 2>/dev/null
  pkill -9 -f mavsdk_server 2>/dev/null; pkill -9 -f ros_gz_bridge 2>/dev/null; pkill -9 -f 'gate_run_r03' 2>/dev/null
  pkill -9 -f 'ruby.*gz' 2>/dev/null; sleep 2; }
teardown

LOGDIR="$OUTDIR" WORLD="$WORLD" PX4_GZ_WORLD="$WORLD" MODEL=gz_x500_mono_cam bash run_stack.sh > "$OUTDIR/stack.log" 2>&1
sleep 3
echo "GUI_PROCS=[$(pgrep -af 'gz sim -g|gz-gui' | grep -v pgrep || echo brak)]" | tee "$OUTDIR/headless_proof.txt"
for i in $(seq 1 40); do gz topic -l 2>/dev/null | grep -q "/world/${WORLD}/clock" && break; sleep 1; done
# ANEKS_D7 §7b: próbnik sim↔wall (bramka habitatu). In-process /clock, ubijany przy teardown.
setsid nohup python3 -m acts.rtf_sampler --world "$WORLD" --out "$OUTDIR/rtf_stream.jsonl" > "$OUTDIR/rtf_sampler.log" 2>&1 &
RTF_SAMPLER=$!
FILM=""; for i in $(seq 1 40); do FILM=$(gz topic -l 2>/dev/null | grep -iE "film.*image$" | head -1); [ -n "$FILM" ] && break; sleep 1; done
echo "FILM_TOPIC=$FILM" | tee "$OUTDIR/film_topic.txt"
[ -n "$FILM" ] && { setsid nohup ros2 run ros_gz_bridge parameter_bridge "${FILM}@sensor_msgs/msg/Image[gz.msgs.Image" > "$OUTDIR/bridge.log" 2>&1 & sleep 3; }

echo "[A3] 90 s preflight EKF (B1-bis)"; sleep 90
grep -ci 'time jump\|Resetting time sync' "$OUTDIR/stack.log" > "$OUTDIR/timejump_pre.txt" 2>/dev/null || echo 0 > "$OUTDIR/timejump_pre.txt"
[ -n "$FILM" ] && python3 "$ROOT/r02/capture_frame.py" "$FILM" "$OUTDIR/frames/kadr_check.npy" 8 > "$OUTDIR/kadr_check.log" 2>&1 || true
[ -n "$FILM" ] && ( for i in $(seq 1 15); do python3 "$ROOT/r02/capture_frame.py" "$FILM" "$OUTDIR/frames/f_$(printf %02d $i).npy" 3 >/dev/null 2>&1; sleep 1.5; done ) & GRABBER=$!

SCEN="S2" GATE_OUT="$OUTDIR/trace.jsonl" PX4_GZ_WORLD="$WORLD" HEADLESS=1 \
  PYTHONPATH=".:.certdeps:${PYTHONPATH:-}" python3 -m r03.gate_run_r03 > "$OUTDIR/act.log" 2>&1
RC=$?
kill "$GRABBER" 2>/dev/null
kill -TERM "$RTF_SAMPLER" 2>/dev/null; sleep 1   # §7b: flush próbnika przed teardown gz
grep -ci 'time jump\|Resetting time sync' "$OUTDIR/stack.log" > "$OUTDIR/timejump_post.txt" 2>/dev/null || true
grep -ciE 'High Gyro Bias|velocity unstable|horizontal velocity' "$OUTDIR/px4.log" > "$OUTDIR/ekf_health_hits.txt" 2>/dev/null || echo 0 > "$OUTDIR/ekf_health_hits.txt"
# ANEKS_D7 §7c: ocena habitatu A3 (H1∧H2 na denial→touchdown) do artefaktów próby.
B0SP="$ROOT/.b0deps/lib/python3.12/site-packages"
PYTHONPATH="$B0SP:$ROOT:${PYTHONPATH:-}" python3 -m acts.habitat_gate A3 "$OUTDIR" --out "$OUTDIR/habitat.json" 2>&1 | tee "$OUTDIR/habitat.log"
HAB=${PIPESTATUS[0]}
teardown
echo "[A3] $RUN DONE rc=$RC habitat_rc=$HAB → $OUTDIR"; exit $RC
