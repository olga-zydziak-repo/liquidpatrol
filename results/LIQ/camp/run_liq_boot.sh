#!/bin/bash
# results/LIQ/camp/run_liq_boot.sh — driver bootu nogi LIQ S2 (PROMPT_LIQ_S2 §0.5/§1).
# Wzór: net/run_fly_boot.sh (F2) BEZ EDYCJI tamtego pliku (kod nogi zamknięty w S1; driver żyje
# w results/LIQ/** — jedyna dozwolona ścieżka zapisu). Różnice vs F2:
#   * OUTDIR pod results/LIQ/camp/ · KIND=liq · REPO-2: ODMOWA bootu w katalog z manifest.json
#     (zamiast rm -rf) · ramię gru przez CONTROLLER=gru (bez NET_ARM) · post-inject weights_sha
#     z FREEZE_SHA (ncp) / FREEZE_SHA_LIQ (gru) + echo arm_monitor z meta trace do manifestu.
# Pełne uzbrojenie domyślne ławki: K2_LEGACY_UNARMED NIE jest ustawiane (K2 D1, ANEKS_K2-6 §4).
#
# Użycie:
#   run_liq_boot.sh <BOOT_N> <OUTNAME> <ARM ncp|gru> smoke <EP_IDS>       # §3: niekryterialny
#   run_liq_boot.sh <BOOT_N> <OUTNAME> <ARM ncp|gru> crit  <QUEUE_STATE>  # §4: kolejka (pop zrobiony)
set -u
ROOT=/home/olga/projects/liquidpatrol
cd "$ROOT"
BN="$1"; OUT="$2"; ARM="$3"; MODE="$4"; ARG5="${5:-}"
OUTDIR="$ROOT/results/LIQ/camp/$OUT"
MONLOG="$ROOT/results/LIQ/camp/liq_monitor.log"

# REPO-2: odmowa bootu w katalog z manifestem (żadnego rm -rf na wynikach)
if [ -f "$OUTDIR/manifest.json" ]; then
  echo "[$OUT] REPO-2: $OUTDIR zawiera manifest.json — ODMOWA bootu" | tee -a "$MONLOG"; exit 4
fi

echo "[$OUT $(date +%H:%M:%S)] cooldown przed czekaniem na host" | tee -a "$MONLOG"
now=$(date +%s); last=$(cat results/.last_boot_end 2>/dev/null || echo 0)
remain=$(( 300 - (now - last) )); [ $remain -lt 0 ] && remain=0
echo "[$OUT] cooldown ${remain}s" | tee -a "$MONLOG"; sleep $remain

echo "[$OUT $(date +%H:%M:%S)] czekam na SUSTAINED CLEAN (3× co 30s)..." | tee -a "$MONLOG"
streak=0
while [ $streak -lt 3 ]; do
  if python3 harness/proc_gate.py --self $$ > /tmp/pg_liq_$BN.log 2>&1; then
    streak=$((streak+1)); echo "[$OUT $(date +%H:%M:%S)] CLEAN ${streak}/3" >> "$MONLOG"
  else
    [ $streak -gt 0 ] && echo "[$OUT $(date +%H:%M:%S)] streak zerwany: $(head -1 /tmp/pg_liq_$BN.log)" >> "$MONLOG"
    streak=0; echo "[$OUT $(date +%H:%M:%S)] brudny: $(head -1 /tmp/pg_liq_$BN.log)" >> "$MONLOG"
  fi
  [ $streak -lt 3 ] && sleep 30
done
echo "[$OUT $(date +%H:%M:%S)] SUSTAINED CLEAN" | tee -a "$MONLOG"

# ramię → env kontrolera (PROMPT_LIQ_S2 §1: NCP = ścieżka F2 bez jednej zmiany; GRU = rejestr)
if [ "$ARM" = "ncp" ]; then CTRL_ENV="CONTROLLER=net NET_ARM=ncp"; else CTRL_ENV="CONTROLLER=$ARM"; fi
COMMON="FLIGHT=bench $CTRL_ENV INTRUDER=1 WORLD=world_demo_A3 FILM=0 BOOT_N=$BN OUTDIR=$OUTDIR KIND=liq"
if [ "$MODE" = "smoke" ]; then
  NEP=$(( $(echo "$ARG5" | tr -cd ',' | wc -c) + 1 ))
  env $COMMON BENCH_EPISODE_IDS="$ARG5" BENCH_EPISODES=$NEP \
    bash harness/run_boot.sh > "${OUTDIR}_launch.log" 2>&1
else
  env $COMMON BENCH_QUEUE="$ARG5" \
    bash harness/run_boot.sh > "${OUTDIR}_launch.log" 2>&1
fi
RC=$?
echo "[$OUT $(date +%H:%M:%S)] wrapper rc=$RC" | tee -a "$MONLOG"
tail -2 "${OUTDIR}_launch.log" | tee -a "$MONLOG"

# post-krok prowieniencji: weights_sha (kontroler ODMÓWIŁBY lotu przy rozjeździe — przelot dowodzi
# zgodności z FREEZE) + arm_monitor z meta trace → manifest 1. klasy (PROMPT_LIQ_S2 §0.5)
python3 - "$OUTDIR" "$ARM" <<'PY'
import json, os, sys
outdir, arm = sys.argv[1], sys.argv[2]
sys.path.insert(0, "/home/olga/projects/liquidpatrol")
mp = os.path.join(outdir, "manifest.json")
if os.path.exists(mp):
    if arm == "ncp":
        from r03.controllers.net_controller import FREEZE_SHA
        wsha = FREEZE_SHA["ncp"]
    else:
        from r03.controllers.liq_controller import FREEZE_SHA_LIQ
        wsha = FREEZE_SHA_LIQ[arm]
    armmon = None
    tp = os.path.join(outdir, "trace.jsonl")
    if os.path.exists(tp):
        for l in open(tp):
            if '"k2_arm_monitor"' in l:
                armmon = json.loads(l).get("k2_arm_monitor"); break
    m = json.load(open(mp))
    m["liq_arm"] = arm
    m["weights_sha"] = wsha
    m["arm_monitor"] = armmon
    json.dump(m, open(mp, "w"), indent=2)
    print(f"[{arm}] weights_sha={wsha[:16]} arm_monitor={armmon} → manifest")
PY
