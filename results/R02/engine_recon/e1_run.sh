#!/usr/bin/env bash
# e1_run.sh <RUN> — E1 (lot+headless) / E2 (lot+headless+STRESS_CPU). Diagnostyka renderu w LOCIE.
# Jednozmienny względem §6: GUI off (HEADLESS=1, weryfikowany). Intruz dead-ahead na wysokości drona
# (INTR_GZ, domyślnie 7,0,9 → poziomo i pionowo centralnie) → pomiar renderu odporny na kołysanie zawisu.
# E2: STRESS_CPU=N → stress-ng obciąża CPU (RTF < 1.0), test hipotezy unifikującej (kontencja → FAIL).
set -o pipefail    # NIE -u: skrypty setup ROS (AMENT_TRACE_SETUP_FILES) nie są nounset-czyste (lekcja R1)
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source ros2_ws/install/setup.bash 2>/dev/null || true
source env_gpu.sh >/dev/null 2>&1 || true
export HEADLESS=1
RUN="${1:-flight_headless_clean}"
OUTDIR="$ROOT/results/R02/engine_recon/E1_confirm/$RUN"; mkdir -p "$OUTDIR"
if [ "${RENDER:-d3d12}" = "llvmpipe" ]; then export LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe; export RENDER_BACKEND="llvmpipe"
else export GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA; export RENDER_BACKEND="mesa-d3d12"; fi
INTR="${INTR_GZ:-7,0,9}"

teardown(){ pkill -9 -f 'gz sim' 2>/dev/null; pkill -9 -f 'bin/px4' 2>/dev/null; pkill -9 -f MicroXRCEAgent 2>/dev/null
  pkill -9 -f mavsdk_server 2>/dev/null; pkill -9 -f 'ruby.*gz' 2>/dev/null; pkill -9 -f stress-ng 2>/dev/null; pkill -9 -x yes 2>/dev/null; sleep 2; }
teardown
# E2: kontencja CPU wstrzykiwana W ZAWISIE przez e1_flight.py (STRESS_N × yes>/dev/null), NIE przed bootem
# — health/arm mają przejść bez stresu, kontencja uderza w okno renderu (izolacja render-pod-kontencją).

LOGDIR="$OUTDIR" MODEL=gz_x500_mono_cam bash run_stack.sh > "$OUTDIR/stack.log" 2>&1
# WERYFIKACJA HEADLESS (SR-E4)
sleep 3; GUI=$(pgrep -af 'gz sim -g|gz-gui' | grep -v pgrep || echo "brak")
echo "GUI_PROCS=[$GUI]  gz_server=[$(pgrep -af 'gz sim -s|gz sim .*-r' | grep -v pgrep | head -1)]" | tee "$OUTDIR/headless_proof.txt"

for i in $(seq 1 40); do gz topic -l 2>/dev/null | grep -qE 'imager/image$' && break; sleep 1; done
IFS=',' read -r IX IY IZ <<< "$INTR"
gz service -s /world/default/create --reqtype gz.msgs.EntityFactory --reptype gz.msgs.Boolean --timeout 3000 \
  --req "sdf_filename: \"$ROOT/r02/intruder_model.sdf\", name: \"intruder\", pose: {position: {x: $IX, y: $IY, z: $IZ}}" > "$OUTDIR/spawn.log" 2>&1
echo "[e1] intruz spawn: $(cat $OUTDIR/spawn.log)"
echo "[e1] 90 s settle EKF"; sleep 90

# RTF + time-jump (E2 diagnostyka; etykieta przyrządu: gz /stats, log gz)
gz topic -et /world/default/stats -n 1 2>/dev/null | grep -iA1 real_time_factor | head -4 > "$OUTDIR/rtf.txt" || true
grep -ci 'time jump\|Resetting time sync' "$OUTDIR/stack.log" > "$OUTDIR/timejump_count.txt" 2>/dev/null || echo 0 > "$OUTDIR/timejump_count.txt"
echo "[e1] RTF: $(cat $OUTDIR/rtf.txt | tr '\n' ' ')  timejumps=$(cat $OUTDIR/timejump_count.txt)"

INTR_GZ="$INTR" OUTDIR="$OUTDIR" RENDER_BACKEND="$RENDER_BACKEND" STRESS_N="${STRESS_N:-0}" PYTHONPATH=".:${PYTHONPATH:-}" \
  python3 results/R02/engine_recon/e1_flight.py > "$OUTDIR/e1.log" 2>&1
RC=$?
# re-sprawdź time-jump po locie
grep -ci 'time jump\|Resetting time sync' "$OUTDIR/stack.log" > "$OUTDIR/timejump_count.txt" 2>/dev/null || true
teardown
echo "[e1] $RUN DONE rc=$RC → $OUTDIR"; exit $RC
