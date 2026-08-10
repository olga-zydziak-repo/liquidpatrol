#!/usr/bin/env bash
# run_gate_one.sh <SCEN> [S1_MIN] — jeden BIEG BRAMKI R0.3a ze świeżym bootem.
# HIGIENA (PROMPT_R03A_CLOSE): artefakty w results/R03/gate/<SCEN>/boot<N>/ (NIGDY /tmp — 2. incydent
# po klatkach C1); 90 s konwergencji EKF jako PREFLIGHT; retry bootu do 3× — bieg liczony DOPIERO po
# udanym uzbrojeniu (exit 0 + event 'armed'); nieudane boot-y logowane, NIE liczone; dmesg per bieg;
# teardown po PID + weryfikacja braku zombie; params przywrócone (SR-B5).
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source ros2_ws/install/setup.bash 2>/dev/null || true
source env_gpu.sh >/dev/null 2>&1 || true
export HEADLESS=1
SCEN="$1"; S1M="${2:-5}"
BASE="$ROOT/results/R03/gate/$SCEN"; mkdir -p "$BASE"

teardown() {
  pkill -9 -f mavsdk_server 2>/dev/null; pkill -9 -f "px4_sitl_default/bin/px4" 2>/dev/null
  pkill -9 -f "gz sim" 2>/dev/null; pkill -9 -f MicroXRCEAgent 2>/dev/null; pkill -9 -f "ruby.*gz" 2>/dev/null
  sleep 3
}
zombie_check() {
  local z; z=$(pgrep -af 'bin/px4|gz sim|MicroXRCEAgent|mavsdk_server' | grep -v pgrep)
  [ -n "$z" ] && { echo "[gate1] ZOMBIE po teardown: $z" ; pkill -9 -f 'bin/px4|gz sim|MicroXRCEAgent|mavsdk_server'; sleep 2; } || echo "[gate1] brak zombie"
}

DROPPED=0; OKBOOT=""
for boot in 1 2 3; do
  BD="$BASE/boot$boot"; mkdir -p "$BD"
  echo "[gate1] $SCEN boot#$boot — teardown + świeży boot"
  teardown; zombie_check
  LOGDIR="$BD" MODEL=gz_x500_mono_cam bash run_stack.sh >"$BD/boot.log" 2>&1
  echo "[gate1] $SCEN boot#$boot PREFLIGHT: 90 s konwergencji EKF (znalezisko B1-bis)"; sleep 90
  dmesg 2>/dev/null | tail -30 > "$BD/dmesg.txt" || echo "(dmesg niedostępny)" > "$BD/dmesg.txt"
  SCEN="$SCEN" S1_MIN="$S1M" GATE_OUT="$BD/run.jsonl" \
      PYTHONPATH=".:.certdeps:$PYTHONPATH" python3 -m r03.gate_run_r03 >"$BD/run.log" 2>&1
  rc=$?
  if [ "$rc" = "0" ] && grep -q '"ev": "armed"' "$BD/run.jsonl" 2>/dev/null && grep -q '"ev": "done"' "$BD/run.jsonl" 2>/dev/null; then
    echo "[gate1] $SCEN boot#$boot OK (uzbrojony, bieg zaliczony)"; OKBOOT="$boot"
    cp "$BD/run.jsonl" "$BASE/run.jsonl"; break
  else
    DROPPED=$((DROPPED+1))
    echo "[gate1] $SCEN boot#$boot ODRZUCONY rc=$rc (arm/health flakiness; NIE liczony jako bieg)"
  fi
done
teardown; zombie_check
echo "[gate1] $SCEN DONE ok_boot=${OKBOOT:-NONE} dropped_boots=$DROPPED"
[ -n "$OKBOOT" ]
