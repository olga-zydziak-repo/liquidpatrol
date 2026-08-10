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
  pkill -9 -f 'r03.gate_run_r03' 2>/dev/null; pkill -9 -f 'health_probe\|confirm_probe' 2>/dev/null  # osierocony egzekutor/sonda
  sleep 3
}
zombie_check() {
  # proces-wzorce + osierocone trzymacze portów UDP osłony (14540 MAVSDK, 8888 agent) — wzorzec gz/px4 ich nie łapie
  local z pz; z=$(pgrep -af 'bin/px4|gz sim|MicroXRCEAgent|mavsdk_server|r03.gate_run_r03|health_probe' | grep -v pgrep)
  pz=$(ss -lunp 2>/dev/null | grep -E ':14540|:8888|:50051' | grep -oE 'pid=[0-9]+' | sort -u)
  if [ -n "$z" ] || [ -n "$pz" ]; then
    echo "[gate1] ZOMBIE po teardown: $z ; porty: $pz"
    pkill -9 -f 'bin/px4|gz sim|MicroXRCEAgent|mavsdk_server|r03.gate_run_r03|health_probe' 2>/dev/null
    echo "$pz" | grep -oE '[0-9]+' | xargs -r kill -9 2>/dev/null; sleep 2
  else
    echo "[gate1] brak zombie (procesy + porty 14540/8888/50051 czyste)"
  fi
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
  # R-D3: bieg z zatrutym paramem na wejściu (event harness_invalid) NIE liczy się, choćby uzbroił.
  INVALID=""; grep -q '"ev": "harness_invalid"' "$BD/run.jsonl" 2>/dev/null && INVALID=1
  if [ "$rc" = "0" ] && [ -z "$INVALID" ] && grep -q '"ev": "armed"' "$BD/run.jsonl" 2>/dev/null && grep -q '"ev": "done"' "$BD/run.jsonl" 2>/dev/null; then
    echo "[gate1] $SCEN boot#$boot OK (uzbrojony, bieg zaliczony)"; OKBOOT="$boot"
    cp "$BD/run.jsonl" "$BASE/run.jsonl"; break
  else
    DROPPED=$((DROPPED+1))
    # Odrzut NIE jest „flakiness". Klasa błędu jest DETERMINISTYCZNA: zatruty param na wejściu (R-D3) →
    # harness_invalid; ARM/HEALTH FAIL → zwykle ten sam mechanizm (patrz FINDING_health_blocker.md).
    if [ -n "$INVALID" ]; then
      echo "[gate1] $SCEN boot#$boot ODRZUCONY: HARNESS_INVALID (zatruty param na wejściu, R-D3; self-heal zrobiony, retry)"
    else
      echo "[gate1] $SCEN boot#$boot ODRZUCONY rc=$rc (arm/health FAIL; mechanizm, nie losowość — patrz DIAG poniżej)"
    fi
    # LUKA LOGOWANIA (DIAG): przy odrzucie wypisz PRZYCZYNĘ do run.log — konsola PX4 (preflight-fail)
    # i EKF2_GPS_CTRL z bootu — żeby nie grzebać w px4.log. px4/agent/boot.log powstają zawsze (run_stack).
    { echo "--- DIAG odrzutu boot#$boot rc=$rc invalid=${INVALID:-0} ---";
      echo "[px4 preflight/health tail]"; grep -aE 'Preflight|Fail|health|GPS|home set' "$BD/px4.log" 2>/dev/null | tail -15;
      echo "[executor tail]"; tail -8 "$BD/run.log" 2>/dev/null;
    } >> "$BD/run.log"
  fi
done
teardown; zombie_check
echo "[gate1] $SCEN DONE ok_boot=${OKBOOT:-NONE} dropped_boots=$DROPPED"
[ -n "$OKBOOT" ]
