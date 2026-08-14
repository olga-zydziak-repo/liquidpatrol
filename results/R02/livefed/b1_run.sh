#!/usr/bin/env bash
# b1_run.sh <RUN> — B1 attitude pod OBSERVE-motion (lot+headless). Bez detektora/intruza (mierzy tylko attitude).
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true
source env_gpu.sh >/dev/null 2>&1 || true
export HEADLESS=1 GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
RUN="${1:-run}"; OUTDIR="$ROOT/results/R02/livefed/B1/$RUN"; mkdir -p "$OUTDIR"
teardown(){ pkill -9 -f 'gz sim' 2>/dev/null; pkill -9 -f 'bin/px4' 2>/dev/null; pkill -9 -f MicroXRCEAgent 2>/dev/null
  pkill -9 -f mavsdk_server 2>/dev/null; pkill -9 -f 'ruby.*gz' 2>/dev/null; pkill -9 -x yes 2>/dev/null; sleep 2; }
teardown
LOGDIR="$OUTDIR" MODEL=gz_x500_mono_cam bash run_stack.sh > "$OUTDIR/stack.log" 2>&1
sleep 3; GUI=$(pgrep -af 'gz sim -g|gz-gui' | grep -v pgrep || echo "brak")
echo "GUI_PROCS=[$GUI]  gz_server=[$(pgrep -af 'gz sim .*-r|gz sim -s' | grep -v pgrep | head -1)]" | tee "$OUTDIR/headless_proof.txt"
for i in $(seq 1 40); do gz topic -l 2>/dev/null | grep -qE 'imager/image$' && break; sleep 1; done
echo "[b1] 90 s settle EKF"; sleep 90
grep -ci 'time jump\|Resetting time sync' "$OUTDIR/stack.log" > "$OUTDIR/timejump.txt" 2>/dev/null || echo 0 > "$OUTDIR/timejump.txt"
OUTDIR="$OUTDIR" HEADLESS=1 PYTHONPATH=".:${PYTHONPATH:-}" python3 results/R02/livefed/b1_flight.py > "$OUTDIR/b1.log" 2>&1
RC=$?
grep -ci 'time jump\|Resetting time sync' "$OUTDIR/stack.log" > "$OUTDIR/timejump.txt" 2>/dev/null || true
teardown; echo "[b1] $RUN DONE rc=$RC → $OUTDIR"; exit $RC
