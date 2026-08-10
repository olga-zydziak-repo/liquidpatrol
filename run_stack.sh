#!/usr/bin/env bash
# run_stack.sh — uruchamia pelny stack R0.0 do soaku/bootow.
#   PX4 SITL (gz_x500_mono_cam) + gz serwer + GUI (D3D12) + MicroXRCEAgent.
# NIE mostkuje kamery (robi to osobno wolajacy, po discovery topiku).
# Uzycie: MODEL=gz_x500_mono_cam ./run_stack.sh
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL="${MODEL:-gz_x500_mono_cam}"
WORLD="${WORLD:-default}"
PX4_DIR="$ROOT/PX4-Autopilot/build/px4_sitl_default"
LOGDIR="${LOGDIR:-/tmp/r0_soak}"
mkdir -p "$LOGDIR"
LOGDIR="$(cd "$LOGDIR" && pwd)"   # ABSOLUTNY — px4 startuje po `cd rootfs`; relatywny LOGDIR gubił px4.log

# shellcheck disable=SC1091
source "$ROOT/env_gpu.sh"

echo "[stack] czyszcze stare procesy…"
pkill -9 -f "MicroXRCEAgent" 2>/dev/null
pkill -9 -f "px4_sitl_default/bin/px4" 2>/dev/null
pkill -9 -f "gz sim" 2>/dev/null
pkill -9 -f "ruby.*gz" 2>/dev/null
sleep 2

echo "[stack] start MicroXRCEAgent (udp4 :8888)…"
setsid nohup MicroXRCEAgent udp4 -p 8888 > "$LOGDIR/agent.log" 2>&1 &
echo "  agent pid=$!"
sleep 1

echo "[stack] start PX4 SITL model=$MODEL world=$WORLD (GUI on, D3D12)…"
cd "$PX4_DIR/rootfs"
export PX4_SIM_MODEL="$MODEL"
export PX4_GZ_WORLD="$WORLD"
unset HEADLESS                  # HEADLESS puste => GUI wystartuje (px4-rc.gzsim)
# Kanoniczne wywolanie (Tools/simulation/sitl_multiple_run.sh:31): rootfs = build/.../etc
setsid nohup "$PX4_DIR/bin/px4" -i 0 -d "$PX4_DIR/etc" > "$LOGDIR/px4.log" 2>&1 &
echo "  px4 pid=$!"
echo "[stack] czekam na swiat gz (scene ready)…"
for i in $(seq 1 40); do
  if gz topic -l 2>/dev/null | grep -q "/clock"; then
    echo "[stack] gz world up (po ${i}s)"; break
  fi
  sleep 1
done
echo "[stack] gotowe. Logi: $LOGDIR/{agent,px4}.log"
