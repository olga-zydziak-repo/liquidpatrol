#!/bin/bash
# net/run_demo_v2.sh — driver demo pozycji 5 (WERSJONOWANY, ANEKS_NET-0 §2). DEMO≠POMIAR.
# Bench boot FILM=1 CONTROLLER=net NET_ARM=ncp kind=demo + grabber klatek filmowych → results/DEMO_V2/<name>/.
# Bez zmian w harness/ (grabber równolegle subskrybuje mostkowany topik filmowy). Sustained-clean jak w lotach.
#
# Użycie:
#   net/run_demo_v2.sh <BOOT_N> <NAME> <EP_IDS csv> [MANIFEST]
set -u
ROOT=/home/olga/projects/liquidpatrol
cd "$ROOT"
BN="$1"; NAME="$2"; EPIDS="$3"; MANIFEST="${4:-}"
OUTDIR="$ROOT/results/DEMO_V2/$NAME"
MON="$ROOT/results/DEMO_V2/demo_monitor.log"
mkdir -p "$OUTDIR/frames" "$ROOT/results/DEMO_V2"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true

# cooldown + sustained-clean (3× co 30s)
now=$(date +%s); last=$(cat results/.last_boot_end 2>/dev/null || echo 0)
remain=$(( 300 - (now - last) )); [ $remain -lt 0 ] && remain=0
echo "[$NAME $(date +%H:%M:%S)] cooldown ${remain}s" | tee -a "$MON"; sleep $remain
echo "[$NAME] czekam SUSTAINED CLEAN" | tee -a "$MON"; streak=0
while [ $streak -lt 3 ]; do
  if python3 harness/proc_gate.py --self $$ >/tmp/pg_demo.log 2>&1; then streak=$((streak+1)); else streak=0; fi
  [ $streak -lt 3 ] && sleep 30
done
echo "[$NAME] CLEAN" | tee -a "$MON"

# launch boot (FILM=1, net, kind=demo) w tle
rm -rf "$OUTDIR"; mkdir -p "$OUTDIR/frames"
MENV=""; [ -n "$MANIFEST" ] && MENV="BENCH_MANIFEST=$MANIFEST"
( env FLIGHT=bench CONTROLLER=net NET_ARM=ncp FILM=1 WORLD=world_demo_A3 KIND=demo INTRUDER=1 \
      BOOT_N="$BN" OUTDIR="$OUTDIR" BENCH_EPISODE_IDS="$EPIDS" $MENV \
      bash harness/run_boot.sh > "${OUTDIR}_launch.log" 2>&1 ) &
BOOT_PID=$!

# grabber: gdy tylko topik filmowy w ros2, chwytaj klatki ~1 Hz aż boot się skończy
echo "[$NAME] czekam na topik filmowy..." | tee -a "$MON"
TOPIC=""
for i in $(seq 1 300); do
  TOPIC=$(ros2 topic list 2>/dev/null | grep -iE "film.*image$|film/image" | head -1)
  [ -n "$TOPIC" ] && break
  kill -0 $BOOT_PID 2>/dev/null || break
  sleep 2
done
echo "[$NAME] FILM_TOPIC=$TOPIC" | tee -a "$MON" "$OUTDIR/film_topic.txt"
n=0
if [ -n "$TOPIC" ]; then
  while kill -0 $BOOT_PID 2>/dev/null; do
    n=$((n+1))
    python3 -m r02.capture_frame "$TOPIC" "$OUTDIR/frames/f_$(printf %04d $n).npy" 2 >/dev/null 2>&1 || true
  done
fi
wait $BOOT_PID; RC=$?
echo "[$NAME $(date +%H:%M:%S)] boot rc=$RC · klatek=$n" | tee -a "$MON"
tail -2 "${OUTDIR}_launch.log" | tee -a "$MON"
