#!/usr/bin/env bash
# results/DEMO_V3/tools/run_demo_v3_boot.sh — driver bootu demo (PROMPT_DEMO_V3 §0.4/§3).
# Boot idzie WYŁĄCZNIE przez tools/w_launcher.sh (frozen) → harness/run_boot.sh (frozen).
# w_launcher zakotwicza OUTDIR pod results/W/ — OUTREL "../DEMO_V3/<dir>" daje efektywnie
# results/DEMO_V3/<dir> bez dotykania zamrożonego launchera (guardy manifestu/locka działają).
# Równolegle: film_recorder.py (JEDEN proces, zero churnu subprocess — lekcja D §5c) zapisuje
# klatki z kamery filmowej zbridżowanej przez run_boot (FILM=1) + stemple sim-time.
#
# Użycie: run_demo_v3_boot.sh <WORLD> <SUBDIR_pod_DEMO_V3> <EPISODE_ID> <CONTROLLER> <BOOT_N>
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
WORLD="${1:?WORLD}"; SUB="${2:?SUBDIR}"; EPID="${3:?EPISODE_ID}"; CTRL="${4:?CONTROLLER}"; BOOTN="${5:?BOOT_N}"
OUT="$ROOT/results/DEMO_V3/$SUB"
mkdir -p "$OUT"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true
FILM_TOPIC="/world/${WORLD}/model/film_cam/link/l/sensor/film/image"
python3 "$ROOT/results/DEMO_V3/tools/film_recorder.py" "$FILM_TOPIC" "$OUT" 8 1500 > "$OUT/film_recorder.log" 2>&1 &
REC=$!
FLIGHT=bench KIND=demo BOOT_N="$BOOTN" CONTROLLER="$CTRL" W_ARM_ALWAYS=1 \
  BENCH_EPISODES=1 BENCH_EPISODE_IDS="$EPID" INTRUDER=1 FILM=1 \
  bash "$ROOT/tools/w_launcher.sh" "$WORLD" "../DEMO_V3/$SUB"
RC=$?
sleep 2; kill "$REC" 2>/dev/null; wait "$REC" 2>/dev/null
echo "[run_demo_v3_boot] DONE rc=$RC → $OUT (frames: $(ls "$OUT/frames" 2>/dev/null | wc -l))"
exit "$RC"
