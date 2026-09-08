#!/bin/bash
# net/run_k2_boot.sh — driver lotu K2 (WERSJONOWANY, ANEKS_NET-0 §2). Sieć + denial pod osłoną.
# Sustained-CLEAN → cooldown → boot bench CONTROLLER=net NET_ARM=ncp z hookiem denialu K2_INJECT_T.
# Zapisy results/K2/**. Nominał (bez K2_INJECT_T) = identyczny jak dotąd.
#
# Użycie:
#   net/run_k2_boot.sh <BOOT_N> <OUTNAME> <KIND diag|crit|nominal> <EP_IDS csv|-> <K2_INJECT_T|-> [QUEUE|-]
set -u
ROOT=/home/olga/projects/liquidpatrol
cd "$ROOT"
BN="$1"; OUT="$2"; KIND="$3"; EPIDS="$4"; INJ="$5"; QUEUE="${6:-}"
OUTDIR="$ROOT/results/K2/$OUT"
MON="$ROOT/results/K2/k2_monitor.log"
mkdir -p "$ROOT/results/K2"

now=$(date +%s); last=$(cat results/.last_boot_end 2>/dev/null || echo 0)
remain=$(( 300 - (now - last) )); [ $remain -lt 0 ] && remain=0
echo "[$OUT $(date +%H:%M:%S)] cooldown ${remain}s" | tee -a "$MON"; sleep $remain
echo "[$OUT] czekam SUSTAINED CLEAN (3× co 30s)" | tee -a "$MON"; streak=0
while [ $streak -lt 3 ]; do
  if python3 harness/proc_gate.py --self $$ >/tmp/pg_k2.log 2>&1; then streak=$((streak+1));
  else streak=0; echo "[$OUT $(date +%H:%M:%S)] brudny: $(head -1 /tmp/pg_k2.log)" >> "$MON"; fi
  [ $streak -lt 3 ] && sleep 30
done
echo "[$OUT $(date +%H:%M:%S)] CLEAN" | tee -a "$MON"

rm -rf "$OUTDIR"
ENVX="FLIGHT=bench CONTROLLER=net NET_ARM=ncp FILM=0 WORLD=world_demo_A3 INTRUDER=1 BOOT_N=$BN OUTDIR=$OUTDIR KIND=$KIND"
[ "$EPIDS" != "-" ] && ENVX="$ENVX BENCH_EPISODE_IDS=$EPIDS"
[ "$INJ" != "-" ]   && ENVX="$ENVX K2_INJECT_T=$INJ"
[ -n "$QUEUE" ] && [ "$QUEUE" != "-" ] && ENVX="$ENVX BENCH_QUEUE=$QUEUE"
env $ENVX bash harness/run_boot.sh > "${OUTDIR}_launch.log" 2>&1
RC=$?
echo "[$OUT $(date +%H:%M:%S)] wrapper rc=$RC" | tee -a "$MON"
tail -2 "${OUTDIR}_launch.log" | tee -a "$MON"

# post-krok: weights_sha do manifestu (net_controller odmówiłby przy rozjeździe → przelot dowodzi zgodności)
python3 - "$OUTDIR" <<'PY'
import json, os, sys
outdir = sys.argv[1]
sys.path.insert(0, "/home/olga/projects/liquidpatrol")
from r03.controllers.net_controller import FREEZE_SHA
mp = os.path.join(outdir, "manifest.json")
if os.path.exists(mp):
    m = json.load(open(mp)); m["net_arm"] = "ncp"; m["weights_sha"] = FREEZE_SHA["ncp"]
    json.dump(m, open(mp, "w"), indent=2)
    print("weights_sha:", FREEZE_SHA["ncp"][:16])
PY
