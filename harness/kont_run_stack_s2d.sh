#!/usr/bin/env bash
# harness/kont_run_stack_s2d.sh — kopia run_stack.sh (oryginał nietknięty), ANEKS_KONT-1c §3: serwer gz startuje PRZED PX4 (te same argumenty co px4-rc.gzsim, które wykrywa działający świat), PX4 dopiero przy czasie sim ≥ 0.5 s; pkill -f zastąpione kont_inw.py. Oryginał: uruchamia pelny stack R0.0 do soaku/bootow.
#   PX4 SITL (gz_x500_mono_cam) + gz serwer + GUI (D3D12) + MicroXRCEAgent.
# NIE mostkuje kamery (robi to osobno wolajacy, po discovery topiku).
# Uzycie: MODEL=gz_x500_mono_cam ./run_stack.sh
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL="${MODEL:-gz_x500_mono_cam}"
WORLD="${WORLD:-default}"
PX4_DIR="$ROOT/PX4-Autopilot/build/px4_sitl_default"
LOGDIR="${LOGDIR:-/tmp/r0_soak}"
mkdir -p "$LOGDIR"
LOGDIR="$(cd "$LOGDIR" && pwd)"   # ABSOLUTNY — px4 startuje po `cd rootfs`; relatywny LOGDIR gubił px4.log

# shellcheck disable=SC1091
source "$ROOT/env_gpu.sh"

echo "[stack] czyszcze stare procesy…"
python3 "$ROOT/results/KONT/tools/kont_inw.py" KILL MicroXRCEAgent px4 gz
sleep 2

echo "[stack] start MicroXRCEAgent (udp4 :8888)…"
setsid nohup MicroXRCEAgent udp4 -p 8888 > "$LOGDIR/agent.log" 2>&1 &
echo "  agent pid=$!"
sleep 1

echo "[stack] start PX4 SITL model=$MODEL world=$WORLD (HEADLESS='${HEADLESS:-}', D3D12)…"
cd "$PX4_DIR/rootfs"
export PX4_SIM_MODEL="$MODEL"
export PX4_GZ_WORLD="$WORLD"
# HEADLESS: jeśli wołający USTAWIŁ (bramka: HEADLESS=1) → BEZ GUI. GUI (`gz sim -g`) potrafi ciągnąć
# >180% CPU i głodzić lockstep → „time jump / Resetting time synchroniser" → EKF reset → High Gyro Bias /
# horizontal velocity unstable → „Arming denied: Resolve system health failures". Bez GUI sim jest stabilny
# i arm przechodzi. Soak (nie ustawia HEADLESS) → GUI jak dotąd. px4-rc.gzsim: puste/unset => GUI.
[ -n "${HEADLESS:-}" ] || unset HEADLESS
# ANEKS_KONT-1c §3: gz przed PX4, bramka czasu sim
. ./gz_env.sh
setsid nohup gz sim --verbose="${GZ_VERBOSE:-1}" -r -s "${PX4_GZ_WORLDS}/${WORLD}.sdf" > "$LOGDIR/gz_server.log" 2>&1 &
echo "  gz pid=$!"
python3 "$ROOT/results/KONT/tools/kont_gz_czas.py" --world "$WORLD" --min 0.5 --out "$LOGDIR/px4_join.json" || { echo "[stack] FAZA: gz nie osiągnął 0.5 s, PX4 nie startuje"; exit 2; }
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
# jak w oryginale stos wraca, gdy rcS widzi świat
for i in $(seq 1 40); do grep -q "Gazebo world is ready" "$LOGDIR/px4.log" 2>/dev/null && break; sleep 1; done
echo "[stack] gotowe. Logi: $LOGDIR/{agent,px4}.log"
