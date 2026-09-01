#!/usr/bin/env bash
# results/BENCH_RECON/recon_probe2.sh <WORLD> <OUTDIR> — RECON boot2 (read-only, SR-5).
# Uzupełnia lukę boot1: mierzy pozę intruza W RUCHU (dynamic_pose/info) — częstotliwość, opóźnienie, rozmiar logu.
# Kolejność: uruchom MOVER (GzPoseClient scripted_pose) w tle → intruz staje się dynamiczny → parallel_sub mierzy.
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true
WORLD="${1:-world_demo_A3}"; OUTDIR="${2:?OUTDIR}"; mkdir -p "$OUTDIR"

echo "[recon2] czekam na /clock (max 120s)"
for i in $(seq 1 120); do gz topic -l 2>/dev/null | grep -q "/world/${WORLD}/clock" && { echo "clock @${i}s"; break; }; sleep 1; done

# pose/info: częstotliwość źródła STATYCZNEGO (wszystkie modele, periodyczne) — 10 s
echo "[recon2] pose/info freq (10s)"
( timeout 10 gz topic -e -t "/world/${WORLD}/pose/info" 2>/dev/null | grep -c 'header' ) > "$OUTDIR/recon2_poseinfo_count.txt" 2>&1 || echo "0" > "$OUTDIR/recon2_poseinfo_count.txt"

# MOVER w tle: GzPoseClient scripted_pose ~45s wall → intruz DYNAMICZNY
echo "[recon2] start MOVER (GzPoseClient scripted_pose ~45s)"
PYTHONPATH=".:${PYTHONPATH:-}" nohup python3 - "$WORLD" > "$OUTDIR/recon2_mover.json" 2>"$OUTDIR/recon2_mover.err" <<'PY' &
import sys, time, json
world = sys.argv[1]
from r02.intruder_driver import GzPoseClient, scripted_pose
cli = GzPoseClient(world, apply_hz=20.0)
tw = time.monotonic()
while time.monotonic() - tw < 45.0:
    st = cli.sim_t() or 0.0
    x, y, z = scripted_pose(st)
    cli.set_pose(x, y, z)
    time.sleep(0.05)
time.sleep(0.5)
print(json.dumps({"applied_hz": cli.applied_hz(), "ok_rate": cli.ok_rate(), "note":"mover"}))
PY
MOVER=$!
sleep 4   # niech intruz się rusza zanim mierzymy

# RTF baseline przed pomiarem
RTF_B=$(tail -5 "$OUTDIR/rtf_stream.jsonl" 2>/dev/null | python3 -c "import sys,json;xs=[json.loads(l).get('rtf') for l in sys.stdin if l.strip()];v=[x for x in xs if x];print(round(sum(v)/len(v),3) if v else 'na')" 2>/dev/null)

# parallel_sub 20s — TERAZ intruz w dynamic_pose/info (bo się rusza)
echo "[recon2] parallel_sub 20s (intruz w ruchu)"
python3 "$ROOT/results/BENCH_RECON/parallel_sub.py" "$WORLD" 20 "$OUTDIR/recon2_intruder_moving.jsonl" > "$OUTDIR/recon2_parallel_sub_summary.json" 2>"$OUTDIR/recon2_parallel_sub.err" || true

RTF_D=$(tail -8 "$OUTDIR/rtf_stream.jsonl" 2>/dev/null | python3 -c "import sys,json;xs=[json.loads(l).get('rtf') for l in sys.stdin if l.strip()];v=[x for x in xs if x];print(round(sum(v)/len(v),3) if v else 'na')" 2>/dev/null)
echo "{\"rtf_before_mover_sub\": \"$RTF_B\", \"rtf_during_mover_sub\": \"$RTF_D\"}" > "$OUTDIR/recon2_rtf_impact.json"

wait $MOVER 2>/dev/null
echo "[recon2] DONE → $OUTDIR"
cat "$OUTDIR/recon2_parallel_sub_summary.json" 2>/dev/null
