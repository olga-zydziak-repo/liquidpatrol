#!/usr/bin/env bash
# r2_probe.sh <LABEL> <WORLD_SDF_PATH> <WORLD_NAME> — SONDA R2 (jedyna sonda nogi D).
# Bootuje PX4+gz (HEADLESS, lockstep) na podanym świecie, ustala scenę, próbkuje RTF ~30s
# i liczy time-jumpy (px4.log + stack.log). Pomiar PAROWANY: baseline (bez kamery filmowej)
# vs probe (z kamerą 1280x720@30 always_on) pod IDENTYCZNYM tłem → delta izoluje koszt kamery.
# NIE lata, NIE nagrywa — tylko RTF/lockstep. Artefakty results/demo/recon/ (SR-D6).
set -o pipefail   # NIE -u: source /opt/ros/jazzy/setup.bash odwołuje się do unbound vars (jak mti_run.sh)
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
LABEL="$1"; WORLD_SDF="$2"; WORLD_NAME="$3"
OUT="$ROOT/results/demo/recon/$LABEL"; mkdir -p "$OUT"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source env_gpu.sh >/dev/null 2>&1 || true
export HEADLESS=1 GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA RENDER_BACKEND="mesa-d3d12"

teardown(){ pkill -9 -f 'gz sim' 2>/dev/null; pkill -9 -f 'bin/px4' 2>/dev/null; pkill -9 -f MicroXRCEAgent 2>/dev/null
  pkill -9 -f 'ruby.*gz' 2>/dev/null; sleep 2; }
teardown

cp "$WORLD_SDF" "$ROOT/PX4-Autopilot/Tools/simulation/gz/worlds/${WORLD_NAME}.sdf"
sha256sum "$WORLD_SDF" | tee "$OUT/world_hash.txt"
nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader 2>/dev/null | tee "$OUT/gpu_at_start.txt"

LOGDIR="$OUT" WORLD="$WORLD_NAME" MODEL=gz_x500_mono_cam bash run_stack.sh > "$OUT/stack.log" 2>&1
GUI=$(pgrep -af 'gz sim -g|gz-gui' | grep -v pgrep || echo "brak")
echo "GUI=[$GUI]" | tee "$OUT/headless_proof.txt"

# czekaj na scenę
for i in $(seq 1 40); do gz topic -l 2>/dev/null | grep -q "/world/${WORLD_NAME}/clock" && break; sleep 1; done
# potwierdź, że kamera filmowa istnieje (probe) lub nie (baseline)
gz topic -l 2>/dev/null | grep -iE "film|image" | tee "$OUT/camera_topics.txt" || true

echo "[r2] settle 30s"; sleep 30
TJ_PRE=$(grep -ci 'time jump\|Resetting time sync' "$OUT/px4.log" 2>/dev/null || echo 0)

echo "[r2] próbkuję RTF 25× @1.2s"
: > "$OUT/rtf_samples.txt"
for i in $(seq 1 25); do
  timeout 5 gz topic -et "/world/${WORLD_NAME}/stats" -n 1 2>/dev/null | grep -m1 real_time_factor | grep -oE '[0-9.]+' >> "$OUT/rtf_samples.txt"
  sleep 1.2
done
TJ_POST=$(grep -ci 'time jump\|Resetting time sync' "$OUT/px4.log" 2>/dev/null || echo 0)
TJ_WINDOW=$((TJ_POST - TJ_PRE))

python3 - "$OUT" "$LABEL" "$TJ_PRE" "$TJ_POST" "$TJ_WINDOW" <<'PY'
import sys, json, statistics as st
out, label, tjp, tjq, tjw = sys.argv[1:6]
vals = [float(x) for x in open(f"{out}/rtf_samples.txt") if x.strip()]
m = {"label": label, "rtf_n": len(vals),
     "rtf_median": round(st.median(vals),4) if vals else None,
     "rtf_min": round(min(vals),4) if vals else None,
     "rtf_max": round(max(vals),4) if vals else None,
     "rtf_p10": round(sorted(vals)[max(0,int(0.1*len(vals))-0)],4) if len(vals)>5 else None,
     "timejump_pre": int(tjp), "timejump_post": int(tjq), "timejump_in_window": int(tjw)}
json.dump(m, open(f"{out}/r2_metrics.json","w"), indent=2)
print(json.dumps(m, indent=2))
PY
teardown
echo "[r2] $LABEL DONE → $OUT"
