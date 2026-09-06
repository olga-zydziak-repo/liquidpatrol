#!/bin/bash
# net/run_fly_boot.sh — driver lotu pozycji 4 (WERSJONOWANY w repo, ANEKS_NET-0 §2 / ANEKS_BENCH-4 O1).
# Sustained-CLEAN (3× co 30s, odporność na flapping dreamforge) → cooldown ≥5min → boot bench z siecią.
#
# Użycie:
#   net/run_fly_boot.sh <BOOT_N> <OUTNAME> <ARM ncp|mlp> diag                # smoke: EP_IDS shakeout, kind=diag
#   net/run_fly_boot.sh <BOOT_N> <OUTNAME> <ARM ncp|mlp> crit <QUEUE_STATE>  # kryterialny: kolejka C8
set -u
ROOT=/home/olga/projects/liquidpatrol
cd "$ROOT"
BN="$1"; OUT="$2"; ARM="$3"; MODE="$4"; QSTATE="${5:-}"; MANIFEST="${6:-}"
OUTDIR="$ROOT/results/NET/FLY/$OUT"
MONLOG="$ROOT/results/NET/FLY/fly_monitor.log"
mkdir -p "$ROOT/results/NET/FLY"

echo "[$OUT $(date +%H:%M:%S)] cooldown przed czekaniem na host" | tee -a "$MONLOG"
now=$(date +%s); last=$(cat results/.last_boot_end 2>/dev/null || echo 0)
remain=$(( 300 - (now - last) )); [ $remain -lt 0 ] && remain=0
echo "[$OUT] cooldown ${remain}s" | tee -a "$MONLOG"; sleep $remain

echo "[$OUT $(date +%H:%M:%S)] czekam na SUSTAINED CLEAN (3× co 30s)..." | tee -a "$MONLOG"
streak=0
while [ $streak -lt 3 ]; do
  if python3 harness/proc_gate.py --self $$ > /tmp/pg_fly_$BN.log 2>&1; then
    streak=$((streak+1)); echo "[$OUT $(date +%H:%M:%S)] CLEAN ${streak}/3" >> "$MONLOG"
  else
    [ $streak -gt 0 ] && echo "[$OUT $(date +%H:%M:%S)] streak zerwany: $(head -1 /tmp/pg_fly_$BN.log)" >> "$MONLOG"
    streak=0; echo "[$OUT $(date +%H:%M:%S)] brudny: $(head -1 /tmp/pg_fly_$BN.log)" >> "$MONLOG"
  fi
  [ $streak -lt 3 ] && sleep 30
done
echo "[$OUT $(date +%H:%M:%S)] SUSTAINED CLEAN" | tee -a "$MONLOG"

rm -rf "$OUTDIR"
COMMON="FLIGHT=bench CONTROLLER=net NET_ARM=$ARM INTRUDER=1 WORLD=world_demo_A3 FILM=0 BOOT_N=$BN OUTDIR=$OUTDIR"
if [ "$MODE" = "diag" ]; then
  env $COMMON KIND=diag BENCH_EPISODE_IDS="0,5,10,11" \
    bash harness/run_boot.sh > "${OUTDIR}_launch.log" 2>&1
else
  MENV=""; [ -n "$MANIFEST" ] && MENV="BENCH_MANIFEST=$MANIFEST"        # F3: fresh manifest s11-s13
  env $COMMON KIND=crit BENCH_QUEUE="$QSTATE" $MENV \
    bash harness/run_boot.sh > "${OUTDIR}_launch.log" 2>&1
fi
RC=$?
echo "[$OUT $(date +%H:%M:%S)] wrapper rc=$RC" | tee -a "$MONLOG"
tail -2 "${OUTDIR}_launch.log" | tee -a "$MONLOG"

# post-krok: wstrzyknij weights_sha + net_arm do manifestu (prowieniencja — net_controller ODMÓWIŁBY
# lotu przy rozjeździe wag, więc przelot dowodzi zgodności z FREEZE_NET; driver zapisuje zweryfikowany sha)
python3 - "$OUTDIR" "$ARM" <<'PY'
import json, os, sys
outdir, arm = sys.argv[1], sys.argv[2]
sys.path.insert(0, "/home/olga/projects/liquidpatrol")
from r03.controllers.net_controller import FREEZE_SHA
mp = os.path.join(outdir, "manifest.json")
if os.path.exists(mp):
    m = json.load(open(mp))
    m["net_arm"] = arm
    m["weights_sha"] = FREEZE_SHA[arm]
    json.dump(m, open(mp, "w"), indent=2)
    print(f"[{arm}] weights_sha wstrzyknięty do manifestu: {FREEZE_SHA[arm][:16]}")
PY
