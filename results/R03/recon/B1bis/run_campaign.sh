#!/usr/bin/env bash
# run_campaign.sh — siatka B1-bis: świeży boot per lot, recorder streaming + fly, analiza gt_judge.
# Uruchamiać w tle. Loty: nazwa MODE DENIAL_S (przez pozycje w tablicy FLIGHTS).
ROOT="/home/olga/projects/liquidpatrol"
cd "$ROOT"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source ros2_ws/install/setup.bash 2>/dev/null || true
source env_gpu.sh >/dev/null 2>&1 || true
set -o pipefail
export HEADLESS=1
FL="$ROOT/results/R03/recon/B1bis/flights"
WD=/tmp/r03bbis
mkdir -p "$FL" "$WD"
MET="$FL/metrics.jsonl"

# lista lotów (pozostałe do siatki 6): "nazwa MODE DENIAL_S"
FLIGHTS=(
  "f2_hover hover 70"
  "f3_straight straight 70"
  "f4_straight120 straight 125"
  "f5_corner corner 70"
  "f6_corner corner 70"
)

boot() {
  echo "[camp] boot fresh stack…"
  pkill -9 -f "MicroXRCEAgent" 2>/dev/null; pkill -9 -f "px4_sitl_default/bin/px4" 2>/dev/null
  pkill -9 -f "gz sim" 2>/dev/null; pkill -9 -f "ruby.*gz" 2>/dev/null; sleep 3
  LOGDIR="$WD" MODEL=gz_x500_mono_cam bash run_stack.sh >"$WD/boot_$1.log" 2>&1
  # czekaj na XRCE vehicle_local_position (publisher)
  for i in $(seq 1 60); do
    if timeout 4 ros2 topic info /fmu/out/vehicle_local_position 2>/dev/null | grep -q "Publisher count: [1-9]"; then
      echo "[camp] XRCE up (po ${i}s)"; break; fi
    sleep 1
  done
  sleep 12   # konwergencja EKF/GPS/home
}

run_one() {
  local name="$1" mode="$2" den="$3"
  local dur=$(python3 -c "print(int($den)+55)")
  local out="$FL/${name}.jsonl"
  echo "[camp] === LOT $name mode=$mode denial=${den}s dur=${dur}s ==="
  B1_OUT="$out" B1_DUR="$dur" python3 results/R03/recon/B1bis/b1bis_record.py >"$WD/rec_${name}.log" 2>&1 &
  local rp=$!
  sleep 2
  MODE="$mode" DENIAL_S="$den" python3 results/R03/recon/B1bis/b1bis_fly.py >"$WD/fly_${name}.log" 2>&1
  wait $rp 2>/dev/null
  # walidacja W1: czy doszło do denial_on i done?
  if ! grep -q "EVENT denial_on" "$WD/fly_${name}.log"; then
    echo "[camp] $name: W1 FAIL (brak denial_on) — nieważny"; return 1
  fi
  local post=$(grep -oE "EKF2_GPS_CTRL post=[0-9]+" "$WD/fly_${name}.log" | grep -oE "[0-9]+$")
  echo "[camp] $name: post EKF2_GPS_CTRL=$post (W4: musi 7)"
  # analiza
  python3 results/R03/recon/B1bis/instrument/gt_judge.py "$out" --json >"$WD/metric_${name}.json" 2>>"$WD/metric_${name}.err"
  python3 - "$name" "$mode" "$den" "$WD/metric_${name}.json" "$MET" <<'PY'
import sys, json
name, mode, den, mfile, met = sys.argv[1:6]
try:
    m = json.load(open(mfile))
except Exception as e:
    m = {"error": str(e)}
m.update({"name": name, "mode": mode, "denial_s": float(den)})
with open(met, "a") as f:
    f.write(json.dumps(m) + "\n")
print(f"[camp] {name}: max_drift={m.get('max_drift')} p95={m.get('healthy_p95_eps')} "
      f"valid={m.get('healthy_valid')} skew={m.get('skew_hat_s')} dr_win={m.get('dr_window_s')} "
      f"resets={m.get('resets')}")
PY
  return 0
}

echo "[camp] START $(date -u +%H:%M:%S)  loty=${#FLIGHTS[@]}"
for spec in "${FLIGHTS[@]}"; do
  read -r name mode den <<<"$spec"
  ok=0
  for attempt in 1 2; do
    boot "$name"
    if run_one "$name" "$mode" "$den"; then ok=1; break; fi
    echo "[camp] $name: próba $attempt nieudana, retry…"
  done
  [ "$ok" = 0 ] && echo "[camp] $name: ODRZUCONY po 2 próbach"
done
# teardown
pkill -9 -f "MicroXRCEAgent" 2>/dev/null; pkill -9 -f "px4_sitl_default/bin/px4" 2>/dev/null
pkill -9 -f "gz sim" 2>/dev/null; pkill -9 -f "ruby.*gz" 2>/dev/null
echo "[camp] DONE $(date -u +%H:%M:%S)"
