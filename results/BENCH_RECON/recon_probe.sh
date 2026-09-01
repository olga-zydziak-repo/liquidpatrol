#!/usr/bin/env bash
# results/BENCH_RECON/recon_probe.sh <WORLD> <OUTDIR> — RECON pomiary żywe (read-only, SR-5).
# Uruchamiane RÓWNOLEGLE do harness/run_boot.sh w oknie żywym sim (settle+hover). Zero sądzenia.
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true
WORLD="${1:-world_demo_A3}"; OUTDIR="${2:?OUTDIR}"; mkdir -p "$OUTDIR"
DP="/world/${WORLD}/dynamic_pose/info"

echo "[recon] czekam na intruza w $DP (max 120s)"
for i in $(seq 1 120); do
  gz topic -e -t "$DP" -n 1 2>/dev/null | grep -q 'name: "intruder"' && { echo "[recon] intruz obecny @${i}s"; break; }
  sleep 1
done

# R2.1 — żywe listy topików (SR-4: tylko z echa)
echo "[recon] gz topic -l"; gz topic -l 2>/dev/null | sort > "$OUTDIR/recon_gz_topics.txt"
echo "[recon] ros2 topic list"; timeout 15 ros2 topic list 2>/dev/null | sort > "$OUTDIR/recon_ros2_topics.txt"
grep -iE 'pose|intruder|clock|model' "$OUTDIR/recon_gz_topics.txt" > "$OUTDIR/recon_gz_pose_topics.txt" 2>/dev/null || true

# R2.2 — częstotliwość pozy: policz wiadomości dynamic_pose/info przez 10 s
echo "[recon] freq dynamic_pose/info (10s)"
( timeout 10 gz topic -e -t "$DP" 2>/dev/null | grep -c 'sim_time\|header' ) > "$OUTDIR/recon_pose_rawcount.txt" 2>&1 || true
# alternatywnie pose/info świata (per-model statyczne)
gz topic -l 2>/dev/null | grep -qE "^/world/${WORLD}/pose/info$" && \
  ( timeout 10 gz topic -e -t "/world/${WORLD}/pose/info" 2>/dev/null | grep -c 'header' ) > "$OUTDIR/recon_poseinfo_rawcount.txt" 2>&1 || echo "brak pose/info" > "$OUTDIR/recon_poseinfo_rawcount.txt"

# R2.3 — RÓWNOLEGŁA subskrypcja + zapis jsonl (20s) + pomiar RTF w tym oknie
echo "[recon] parallel_sub 20s + RTF baseline"
RTF_BEFORE=$(tail -5 "$OUTDIR/rtf_stream.jsonl" 2>/dev/null | python3 -c "import sys,json;xs=[json.loads(l).get('rtf') for l in sys.stdin if l.strip()];print(round(sum(x for x in xs if x)/max(1,len([x for x in xs if x])),3) if xs else 'na')" 2>/dev/null)
python3 "$ROOT/results/BENCH_RECON/parallel_sub.py" "$WORLD" 20 "$OUTDIR/recon_parallel_sub.jsonl" > "$OUTDIR/recon_parallel_sub_summary.json" 2>"$OUTDIR/recon_parallel_sub.err" || true
RTF_DURING=$(tail -10 "$OUTDIR/rtf_stream.jsonl" 2>/dev/null | python3 -c "import sys,json;xs=[json.loads(l).get('rtf') for l in sys.stdin if l.strip()];print(round(sum(x for x in xs if x)/max(1,len([x for x in xs if x])),3) if xs else 'na')" 2>/dev/null)
echo "{\"rtf_before_sub\": \"$RTF_BEFORE\", \"rtf_during_sub\": \"$RTF_DURING\"}" > "$OUTDIR/recon_rtf_impact.json"

# R1 — set_pose żywy test: GzPoseClient (in-process, apply_hz) prowadzi scripted_pose ~8s; read-back + applied_hz
echo "[recon] set_pose test (GzPoseClient scripted_pose ~8s)"
PYTHONPATH=".:${PYTHONPATH:-}" timeout 30 python3 - "$WORLD" > "$OUTDIR/recon_setpose.json" 2>"$OUTDIR/recon_setpose.err" <<'PY' || true
import sys, time, json
world = sys.argv[1]
from r02.intruder_driver import GzPoseClient, scripted_pose, gz_clock
cli = GzPoseClient(world, apply_hz=20.0)
t0 = gz_clock(world) or 0.0
samples = []
tw = time.monotonic()
while time.monotonic() - tw < 8.0:
    st = (cli.sim_t() or 0.0)
    x, y, z = scripted_pose(st)      # deterministyczna f(sim_t)
    cli.set_pose(x, y, z)            # async → worker aplikuje @apply_hz
    samples.append({"sim_t": round(st,3), "y_cmd": round(y,3)})
    time.sleep(0.05)
time.sleep(0.5)
out = {"applied_hz": round(cli.applied_hz(),2) if hasattr(cli,"applied_hz") else None,
       "ok_rate": round(cli.ok_rate(),3) if hasattr(cli,"ok_rate") else None,
       "n_cmd": len(samples), "y_cmd_first": samples[0]["y_cmd"] if samples else None,
       "y_cmd_last": samples[-1]["y_cmd"] if samples else None,
       "note": "scripted_pose = czysta f(sim_t) → determinizm z konstrukcji (bez fizyki/losu)"}
print(json.dumps(out))
PY

echo "[recon] DONE → $OUTDIR"
ls -1 "$OUTDIR"/recon_* 2>/dev/null
