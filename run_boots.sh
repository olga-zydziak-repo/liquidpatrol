#!/usr/bin/env bash
# run_boots.sh — pkt6: 3x NIEZALEZNY boot stacku, kazdy z hello-mission.
# Kazda iteracja: swiezy launch (gz_x500 + GUI D3D12 + agent) -> hello-mission ->
# wynik + RTF + renderer + sprawdzenie pada (CaptureCrash/oops) -> teardown.
# Teardown kill = znany benign artefakt (exit-144/dxg-2/-512), NIE pad (patrz teardown_dmesg_note.md).
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
N="${N:-3}"
MODEL="${MODEL:-gz_x500}"
BUILD="$ROOT/PX4-Autopilot/build/px4_sitl_default"
OUT="/tmp/r0_boots"; mkdir -p "$OUT"
RESULT="$OUT/boots_result.log"; : > "$RESULT"
# (bez ROS: bazowy gz_x500 bez mostu kamery; misja przez MAVSDK-Python, nie ROS)

kill_all() {
  pkill -9 -f "px4_sitl_default/bin/px4" 2>/dev/null
  pkill -9 -f "gz sim" 2>/dev/null
  pkill -9 -f "ruby.*gz|/ruby" 2>/dev/null
  pkill -9 -f "MicroXRCEAgent" 2>/dev/null
  pkill -9 -f "parameter_bridge" 2>/dev/null
  sleep 3
}

for i in $(seq 1 "$N"); do
  echo "==================== BOOT $i/$N ====================" | tee -a "$RESULT"
  kill_all
  base_cap=$(dmesg 2>/dev/null | grep -cE "CaptureCrash")
  base_oops=$(dmesg 2>/dev/null | grep -cE "kernel BUG|Oops:| general protection|Kernel panic - not syncing")

  # --- launch stack ---
  source "$ROOT/env_gpu.sh" >/dev/null 2>&1
  setsid nohup MicroXRCEAgent udp4 -p 8888 > "$OUT/agent_$i.log" 2>&1 &
  sleep 1
  ( cd "$BUILD/rootfs"
    export PX4_SIM_MODEL="$MODEL" PX4_GZ_WORLD=default
    unset HEADLESS
    setsid nohup "$BUILD/bin/px4" -i 0 -d "$BUILD/etc" > "$OUT/px4_$i.log" 2>&1 & )
  # czekaj na swiat gz
  up=no
  for s in $(seq 1 40); do
    if gz topic -l 2>/dev/null | grep -q "/clock"; then up=yes; break; fi
    sleep 1
  done
  rend=$(grep -iE "GL_RENDERER" "$HOME/.gz/rendering/ogre2.log" 2>/dev/null | tail -1 | sed 's/.*GL_RENDERER = //')
  rtf=$(timeout 4 gz topic -e -t /world/default/stats 2>/dev/null | grep -m1 real_time_factor | awk '{print $2}')
  echo "[boot$i] gz_up=$up renderer=$rend RTF=$rtf" | tee -a "$RESULT"

  # --- hello-mission ---
  mres="MISSION-FAIL"
  if [ "$up" = yes ]; then
    if timeout 260 python3 "$ROOT/run_hello_mission.py" > "$OUT/mission_$i.log" 2>&1; then
      mres=$(grep -oE "WYNIK: (PASS|FAIL)" "$OUT/mission_$i.log" | tail -1)
    else
      mres=$(grep -oE "WYNIK: (PASS|FAIL)|TIMEOUT" "$OUT/mission_$i.log" | tail -1)
      [ -z "$mres" ] && mres="MISSION-FAIL(rc)"
    fi
  fi
  # A4 gap z logu misji
  gap=$(grep -oE "max przerwa pozycji: [0-9.]+s" "$OUT/mission_$i.log" | tail -1)
  echo "[boot$i] mission=$mres  $gap" | tee -a "$RESULT"

  # --- pad check PRZED teardownem (spontaniczny) ---
  cap=$(dmesg 2>/dev/null | grep -cE "CaptureCrash")
  oops=$(dmesg 2>/dev/null | grep -cE "kernel BUG|Oops:| general protection|Kernel panic - not syncing")
  if [ "$cap" -gt "$base_cap" ] || [ "$oops" -gt "$base_oops" ]; then
    echo "[boot$i] !!! PAD SPONTANICZNY: CaptureCrash $base_cap->$cap oops $base_oops->$oops" | tee -a "$RESULT"
    dmesg 2>/dev/null | tail -30 | tee -a "$RESULT"
  else
    echo "[boot$i] pad-check: brak nowego CaptureCrash/oops w trakcie biegu (spontanicznie) OK" | tee -a "$RESULT"
  fi

  kill_all
  echo "[boot$i] teardown done" | tee -a "$RESULT"
done
echo "==================== PODSUMOWANIE ====================" | tee -a "$RESULT"
grep -E "\[boot[0-9]+\] (mission=|gz_up=|pad-check|PAD)" "$RESULT" | tee -a "$RESULT" >/dev/null
echo "boots log: $RESULT"
