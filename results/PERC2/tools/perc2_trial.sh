#!/usr/bin/env bash
# results/PERC2/tools/perc2_trial.sh — JEDNA PRÓBA macierzy stan×remedium (PRE_PERC2 §2.1)
# na żywym stacku postawionym przez perc2_s1_boot.sh. Per próba:
#   1) snapshot stanu GPU (nvidia-smi query) → gpu_<TRIAL>.json,
#   2) start percep_proc (FROZEN 38a3a765, READ-ONLY wykonaniem) z logiem
#      percep_feed_<TRIAL>.jsonl na DURATION s, równolegle perc2_gzhz.py (poziom gz),
#   3) SIGTERM percep → summary.json (push_frame_wall p50/p95) → push_<TRIAL>.json,
#   4) sonda kadencji POSTHOC na feedzie próby → sonda_<TRIAL>.json.
# Zero dotyku percepcji (uruchomienie ≠ edycja); zero uzbrojenia; czysty ops.
#
# Użycie: perc2_trial.sh <OUTDIR> <TRIAL> <DURATION_S>
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
OUTDIR="${1:?OUTDIR}"; TRIAL="${2:?TRIAL}"; DUR="${3:?DURATION_S}"
B0SP="$ROOT/.b0deps/lib/python3.12/site-packages"
WORLD=world_demo_A3
MONO=/world/$WORLD/model/x500_mono_cam_0/link/camera_link/sensor/imager/image
FEED="$OUTDIR/percep_feed_${TRIAL}.jsonl"

source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true
export GZ_IP=127.0.0.1
# remedium C2 (liga ops): profil transportu FastDDS dla percep/liczników (PERC2_FASTDDS_PROFILE)
[ -n "${PERC2_FASTDDS_PROFILE:-}" ] && export FASTRTPS_DEFAULT_PROFILES_FILE="$PERC2_FASTDDS_PROFILE"

nvidia-smi --query-gpu=pstate,clocks.sm,clocks.max.sm,power.draw,power.limit,temperature.gpu,utilization.gpu --format=csv,noheader > "$OUTDIR/gpu_${TRIAL}.pre.txt" 2>&1

setsid nohup env PYTHONPATH="$B0SP:$ROOT:${PYTHONPATH:-}" \
  python3 "$ROOT/harness/percep_proc.py" --topic "$MONO" --world $WORLD \
  --sock "$OUTDIR/percep_${TRIAL}.sock" --log "$FEED" > "$OUTDIR/percep_${TRIAL}.stdout.log" 2>&1 &
PP=$!
echo "[trial $TRIAL] percep pid=$PP, czekam na pierwsze klatki..."
for i in $(seq 1 60); do [ -s "$FEED" ] && break; sleep 1; done

python3 "$ROOT/results/PERC2/tools/perc2_gzhz.py" --topic "$MONO" --window "$DUR" \
  --label "$TRIAL" --out "$OUTDIR/gzhz_${TRIAL}.json" > /dev/null 2>"$OUTDIR/gzhz_${TRIAL}.err" &
GZP=$!

sleep "$DUR"
nvidia-smi --query-gpu=pstate,clocks.sm,power.draw,power.limit,temperature.gpu,utilization.gpu --format=csv,noheader > "$OUTDIR/gpu_${TRIAL}.post.txt" 2>&1
python3 - "$OUTDIR" "$TRIAL" <<'PYEOF'
import json, sys
outdir, trial = sys.argv[1:3]
rows = {}
for ph in ("pre", "post"):
    try:
        rows[ph] = open(f"{outdir}/gpu_{trial}.{ph}.txt").read().strip()
    except OSError:
        rows[ph] = None
json.dump({"proba": trial, "pola": "pstate, clocks.sm, [clocks.max.sm,] power.draw, power.limit, temp, util", **rows},
          open(f"{outdir}/gpu_{trial}.json", "w"), indent=1)
PYEOF

wait "$GZP" 2>/dev/null
kill -TERM "$PP" 2>/dev/null
for i in $(seq 1 15); do kill -0 "$PP" 2>/dev/null || break; sleep 1; done
kill -9 "$PP" 2>/dev/null
sleep 1
if [ -f "$FEED.summary.json" ]; then cp "$FEED.summary.json" "$OUTDIR/push_${TRIAL}.json"; fi
python3 "$ROOT/results/PERC2/tools/perc2_sonda.py" --feed "$FEED" --posthoc \
  --label "$TRIAL" --out "$OUTDIR/sonda_${TRIAL}.json"; RC=$?
echo "[trial $TRIAL] sonda rc=$RC (0=PASS 1=FAIL 2=za mało danych)"
exit $RC
