#!/usr/bin/env bash
# acts/run_stability.sh <BOOT_N> — DEMO-B B5R2 T1: jeden czysty boot sondy stabilności (rdzeń mti_flight)
# w habitacie aktu (world_demo_A1 + mono bridge, jak mti_run.sh). Kryterium: MAVSDK→health→arm→takeoff→
# ≥10s hover→shutdown. Higiena env (ANEKS_D4 c). Wynik: results/demo/stability/boot_<N>/probe.json + logi.
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
B0SP="$ROOT/.b0deps/lib/python3.12/site-packages"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true
source env_gpu.sh >/dev/null 2>&1 || true
export HEADLESS=1 GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA RENDER_BACKEND="mesa-d3d12"
N="${1:-1}"; WORLD="world_demo_A1"
OUT="$ROOT/results/demo/stability/boot_${N}"; mkdir -p "$OUT"

# higiena env (ANEKS_D4 c): kill stale + zrzut ps
teardown(){ pkill -9 -f 'gz sim' 2>/dev/null; pkill -9 -f 'px4_sitl' 2>/dev/null; pkill -9 -f MicroXRCEAgent 2>/dev/null
  pkill -9 -f mavsdk_server 2>/dev/null; pkill -9 -f 'parameter_bridge' 2>/dev/null; pkill -9 -f detector_node 2>/dev/null
  pkill -9 -f live_stability_probe 2>/dev/null; pkill -9 -f 'ruby.*gz' 2>/dev/null; sleep 2; }
teardown
ps aux 2>/dev/null | grep -iE 'gz|px4|ros2|detector|mavsdk' | grep -v grep > "$OUT/ps_before.txt" || true

cp "$ROOT/worlds/${WORLD}.sdf" "$ROOT/PX4-Autopilot/Tools/simulation/gz/worlds/${WORLD}.sdf"
LOGDIR="$OUT" WORLD="$WORLD" PX4_GZ_WORLD="$WORLD" MODEL=gz_x500_mono_cam bash run_stack.sh > "$OUT/stack.log" 2>&1
sleep 3
echo "GUI=[$(pgrep -af 'gz sim -g|gz-gui' | grep -v pgrep || echo brak)]" | tee "$OUT/headless_proof.txt"
for i in $(seq 1 40); do gz topic -l 2>/dev/null | grep -q "/world/${WORLD}/clock" && break; sleep 1; done
# mono bridge PRZED settle (jak mti_run.sh — działał)
MONO=""; for i in $(seq 1 40); do MONO=$(gz topic -l 2>/dev/null | grep -E "imager/image$" | head -1); [ -n "$MONO" ] && break; sleep 1; done
[ -n "$MONO" ] && setsid nohup ros2 run ros_gz_bridge parameter_bridge "${MONO}@sensor_msgs/msg/Image[gz.msgs.Image" > "$OUT/bridge_mono.log" 2>&1 &
sleep 2
gz service -s /world/${WORLD}/create --reqtype gz.msgs.EntityFactory --reptype gz.msgs.Boolean --timeout 3000 \
  --req "sdf_filename: \"$ROOT/r02/intruder_model.sdf\", name: \"intruder\", pose: {position: {x: 7.86, y: 0, z: 11.5}}" > "$OUT/spawn.log" 2>&1

echo "[stab boot $N] 150 s settle EKF (jak mti_run.sh)"; sleep 150
# sonda stabilności — rdzeń mti_flight (health 90s + arm-retry)
HOVER_ALT=9.0 HOVER_HOLD_S=10 PYTHONPATH="$B0SP:$ROOT:${PYTHONPATH:-}" \
  python3 "$ROOT/acts/live_stability_probe.py" "$OUT/probe.json" > "$OUT/probe.log" 2>&1
RC=$?
grep -ci 'time jump\|Resetting time sync' "$OUT/stack.log" > "$OUT/timejump.txt" 2>/dev/null || true
teardown
echo "[stab boot $N] DONE rc=$RC → $OUT"; exit $RC
