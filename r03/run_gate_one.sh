#!/usr/bin/env bash
# run_gate_one.sh <SCEN> [S1_MIN] — świeży boot + 90 s konwergencji + jeden bieg bramki R0.3a.
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source ros2_ws/install/setup.bash 2>/dev/null || true
source env_gpu.sh >/dev/null 2>&1 || true
export HEADLESS=1
SCEN="$1"; S1M="${2:-5}"
FL="$ROOT/results/R03/gate"; mkdir -p "$FL"
WD="$FL"     # logi do repo (nie /tmp — scratchpad bywa czyszczony i ubija bg)
pkill -9 -f mavsdk_server 2>/dev/null; pkill -9 -f "px4_sitl_default/bin/px4" 2>/dev/null
pkill -9 -f "gz sim" 2>/dev/null; pkill -9 -f MicroXRCEAgent 2>/dev/null; pkill -9 -f "ruby.*gz" 2>/dev/null
sleep 4
LOGDIR="$FL" MODEL=gz_x500_mono_cam bash run_stack.sh >"$FL/boot_${SCEN}.log" 2>&1
echo "[gate1] $SCEN boot done, settle 90 s"; sleep 90
SCEN="$SCEN" S1_MIN="$S1M" GATE_OUT="$FL/${SCEN}_run.jsonl" \
    PYTHONPATH=".:.certdeps:$PYTHONPATH" python3 -m r03.gate_run_r03 >"$WD/gate_${SCEN}_run.log" 2>&1
echo "[gate1] $SCEN run done"
# teardown
pkill -9 -f mavsdk_server 2>/dev/null; pkill -9 -f "px4_sitl_default/bin/px4" 2>/dev/null
pkill -9 -f "gz sim" 2>/dev/null; pkill -9 -f MicroXRCEAgent 2>/dev/null
echo "[gate1] $SCEN DONE"
