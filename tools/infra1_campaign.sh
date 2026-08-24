#!/usr/bin/env bash
# tools/infra1_campaign.sh [START] [COUNT] — INFRA-1 I3: seria pustych bootów walidacyjnych.
# Każdy: bash k1/run_k1_boot.sh E 0.0 <n> (zahartowany boot I2 + pusty lot 60 s hover). Między bootami
# cooldown ≥5 min (COOLDOWN_S) + sweep orphanów. env-block (exit 3) NIE liczy się — slot powtarzany.
# 10 znaczy 10 KOLEJNYCH bootów, każdy trafia do tabeli (tools/infra1_gate.py), zero wybierania.
set -uo pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
START="${1:-1}"; COUNT="${2:-10}"
COOLDOWN_S="${COOLDOWN_S:-300}"
# ANEKS_INFRA1-4 X3/X4: I3 wyłącznie na CZYSTEJ maszynie.
IDLE_MAX_FIRST="${IDLE_MAX_FIRST:-1.0}"   # X3: load1 < 1.0 przed PIERWSZYM bootem (spoczynek)
CONTENTION_MAX="${CONTENTION_MAX:-2.0}"   # X4: tripwire kontencji między bootami (po sweep+cooldown maszyna ~idle)
FOREIGN_PAT="${FOREIGN_PAT:-src.runner.gate2}"  # znane cudze zadanie; + heurystyka %CPU poniżej
LOG="$ROOT/results/K1/INFRA1/campaign.log"
mkdir -p "$ROOT/results/K1/INFRA1"
export K1_SESSION_BOOT_COUNT="${K1_SESSION_BOOT_COUNT:-1}" K1_ENV_RESTART="${K1_ENV_RESTART:-wsl-shutdown}"

ORPH_PAT='gz sim|px4 |MicroXRCEAgent|mavsdk_server|gate_run_r03|k1_arm_n|rtf_sampler|ruby.*gz|infra1_empty_flight'
sweep(){ pkill -9 -f 'gz sim' 2>/dev/null; pkill -9 -f 'px4 ' 2>/dev/null; pkill -9 -f MicroXRCEAgent 2>/dev/null
  pkill -9 -f mavsdk_server 2>/dev/null; pkill -9 -f 'ruby.*gz' 2>/dev/null; pkill -9 -f infra1_empty_flight 2>/dev/null
  pkill -9 -f rtf_sampler 2>/dev/null; sleep 3; }

# X4: kontencja = znane cudze zadanie żyje LUB obcy proces >50% CPU spoza naszego stacku. Zwraca 0=jest.
foreign_busy(){
  pgrep -f "$FOREIGN_PAT" >/dev/null 2>&1 && { echo "foreign=$FOREIGN_PAT"; return 0; }
  local hit
  hit=$(ps -eo pcpu,args --sort=-pcpu 2>/dev/null | awk 'NR>1 && $1>50' \
    | grep -vE 'run_k1_boot|px4|gz sim|ruby.*gz|MicroXRCE|mavsdk|rtf_sampler|infra1_empty_flight|infra1_campaign|pyulog|ulog|python3 -c|awk |grep |ps ' \
    | head -1)
  [ -n "$hit" ] && { echo "foreign_cpu=[$hit]"; return 0; }
  return 1
}

echo "=== INFRA-1 campaign START=$START COUNT=$COUNT cooldown=${COOLDOWN_S}s $(date) ===" | tee -a "$LOG"

# X3: bramka czystego startu — gate2 zakończone ∧ load spoczynkowy < IDLE_MAX_FIRST przed 1. bootem.
_l1=$(cut -d' ' -f1 /proc/loadavg); _fb=$(foreign_busy || true)
if foreign_busy >/dev/null 2>&1 || awk "BEGIN{exit !($_l1 >= $IDLE_MAX_FIRST)}"; then
  echo "[campaign] X3 REFUSE start: load1=$_l1 (max $IDLE_MAX_FIRST) foreign=[$_fb] — maszyna NIE spoczynkowa. I3 tylko na czystej." | tee -a "$LOG"
  exit 6
fi
echo "[campaign] X3 OK: load1=$_l1 < $IDLE_MAX_FIRST, brak cudzych zadań — start serii." | tee -a "$LOG"

n="$START"; done_ct=0; attempts_this=0
while [ "$done_ct" -lt "$COUNT" ]; do
  # X4: kontencja w środku dziesiątki skaża porównywalność → przerwij serię, licz OD NOWA (nie doliczaj).
  _l1=$(cut -d' ' -f1 /proc/loadavg)
  if _fb=$(foreign_busy); then
    echo "[campaign] X4 ABORT: kontencja w środku serii (done=$done_ct/$COUNT): $_fb load1=$_l1 — SERIA SKAŻONA, licz od nowa (nie doliczam)." | tee -a "$LOG"; exit 5
  fi
  if awk "BEGIN{exit !($_l1 >= $CONTENTION_MAX)}"; then
    echo "[campaign] X4 ABORT: load1=$_l1 ≥ $CONTENTION_MAX po cooldown (done=$done_ct/$COUNT) — obca kontencja, SERIA SKAŻONA, licz od nowa." | tee -a "$LOG"; exit 5
  fi
  orph=$(pgrep -fc "$ORPH_PAT" 2>/dev/null); orph=${orph:-0}
  echo "[campaign] boot$n : orphans_pre=$orph load1=$_l1 $(date)" | tee -a "$LOG"
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
