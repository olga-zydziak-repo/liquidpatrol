#!/usr/bin/env bash
# tools/infra1_campaign.sh [START] [COUNT] — INFRA-1 I3: seria pustych bootów walidacyjnych.
# Każdy: bash k1/run_k1_boot.sh E 0.0 <n> (zahartowany boot I2 + pusty lot 60 s hover). Między bootami
# cooldown ≥5 min (COOLDOWN_S) + sweep orphanów. env-block (exit 3) NIE liczy się — slot powtarzany.
# 10 znaczy 10 KOLEJNYCH bootów, każdy trafia do tabeli (tools/infra1_gate.py), zero wybierania.
set -uo pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
START="${1:-1}"; COUNT="${2:-10}"
COOLDOWN_S="${COOLDOWN_S:-300}"
LOG="$ROOT/results/K1/INFRA1/campaign.log"
mkdir -p "$ROOT/results/K1/INFRA1"
export K1_SESSION_BOOT_COUNT="${K1_SESSION_BOOT_COUNT:-1}" K1_ENV_RESTART="${K1_ENV_RESTART:-wsl-shutdown}"

ORPH_PAT='gz sim|px4 |MicroXRCEAgent|mavsdk_server|gate_run_r03|k1_arm_n|rtf_sampler|ruby.*gz|infra1_empty_flight'
sweep(){ pkill -9 -f 'gz sim' 2>/dev/null; pkill -9 -f 'px4 ' 2>/dev/null; pkill -9 -f MicroXRCEAgent 2>/dev/null
  pkill -9 -f mavsdk_server 2>/dev/null; pkill -9 -f 'ruby.*gz' 2>/dev/null; pkill -9 -f infra1_empty_flight 2>/dev/null
  pkill -9 -f rtf_sampler 2>/dev/null; sleep 3; }

echo "=== INFRA-1 campaign START=$START COUNT=$COUNT cooldown=${COOLDOWN_S}s $(date) ===" | tee -a "$LOG"
n="$START"; done_ct=0; attempts_this=0
while [ "$done_ct" -lt "$COUNT" ]; do
  orph=$(pgrep -fc "$ORPH_PAT" 2>/dev/null); orph=${orph:-0}
  echo "[campaign] boot$n : orphans_pre=$orph load1=$(cut -d' ' -f1 /proc/loadavg) $(date)" | tee -a "$LOG"
  sweep
  bash k1/run_k1_boot.sh E 0.0 "$n" > "$ROOT/results/K1/INFRA1/boot${n}.launch.log" 2>&1
  rc=$?
  if [ "$rc" = "3" ]; then
    attempts_this=$((attempts_this+1))
    echo "[campaign] boot$n ENV-BLOCK (rc=3, nie liczy sie) attempt=$attempts_this" | tee -a "$LOG"
    if [ "$attempts_this" -ge 5 ]; then
      echo "[campaign] STOP: 5 env-block pod rzad na slocie $n — maszyna chora, przerwa" | tee -a "$LOG"; exit 4
    fi
    sleep 120; continue
  fi
  attempts_this=0; done_ct=$((done_ct+1))
  sm=$(python3 -c "import json;m=json.load(open('results/K1/E/p0_0/boot${n}/manifest.json'));print('arm_ok=%s landed=%s habitat=%s conv_s=%s load1=%s ekf_hits=%s'%(m.get('arm_ok'),m.get('landed'),m.get('habitat_verdict'),m.get('conv_s'),(m.get('session',{}).get('loadavg') or [None])[0],m.get('ekf_health_hits')))" 2>/dev/null || echo "manifest-read-fail")
  echo "[campaign] boot$n DONE rc=$rc | $sm" | tee -a "$LOG"
  n=$((n+1))
  if [ "$done_ct" -lt "$COUNT" ]; then
    echo "[campaign] cooldown ${COOLDOWN_S}s przed nastepnym..." | tee -a "$LOG"; sleep "$COOLDOWN_S"
  fi
done
echo "=== INFRA-1 campaign KONIEC: $done_ct bootow $(date) ===" | tee -a "$LOG"
