#!/usr/bin/env bash
# r02/run_gate_r02.sh — orkiestracja ŻYWEJ bramki R0.2 (świeży boot per scenariusz, PRE §4).
# Stos: MicroXRCEAgent + PX4 SITL (gz_x500_mono_cam) + gz + GUI (run_stack.sh) + most kamery
#       (ros_gz_bridge) + węzeł detektora (env ROS2+torch) + intruz (gz create + intruder_driver)
#       + runner bramki (r02/gate_run_r02.py). TEARDOWN po PID (nie pkill -f ruby — lekcja R1).
# Użycie: SCENARIO=G1|G2|G3|G4|G5 ./r02/run_gate_r02.sh
set -o pipefail    # NIE -u: skrypty setup ROS (AMENT_TRACE_SETUP_FILES) nie są nounset-czyste
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
SCEN="${SCENARIO:-G1}"
LOGDIR="${LOGDIR:-/tmp/r02/$SCEN}"; mkdir -p "$LOGDIR"
WORLD=default
B0SP="$ROOT/.b0deps/lib/python3.12/site-packages"
PIDS=()
cleanup() {
  echo "[gate] teardown…"
  for p in "${PIDS[@]}"; do kill "$p" 2>/dev/null; done
  pkill -9 -f "gate_run_r02" 2>/dev/null
  pkill -9 -f "detector_node" 2>/dev/null
  pkill -9 -f "intruder_driver" 2>/dev/null
  pkill -9 -f "parameter_bridge" 2>/dev/null
  pkill -9 -f "MicroXRCEAgent" 2>/dev/null
  pkill -9 -f "px4_sitl_default/bin/px4" 2>/dev/null
  pkill -9 -f "gz sim" 2>/dev/null
  sleep 2
}
trap cleanup EXIT

echo "[gate] === SCENARIO=$SCEN — świeży boot ==="
# 1) stos (agent+px4+gz+GUI)
MODEL=gz_x500_mono_cam ./run_stack.sh > "$LOGDIR/stack.log" 2>&1
# 2) czekaj na kamerę gz
IMG_TOPIC=""
for i in $(seq 1 40); do
  IMG_TOPIC=$(gz topic -l 2>/dev/null | grep -E "imager/image$" | head -1)
  [ -n "$IMG_TOPIC" ] && { echo "[gate] kamera gz: $IMG_TOPIC (po ${i}s)"; break; }
  sleep 1
done
[ -z "$IMG_TOPIC" ] && { echo "[gate] BRAK topiku kamery — STOP"; exit 2; }

# 3) most kamery gz→ROS2. ros_gz_bridge ZACHOWUJE nazwę topiku (ROS topic == gz topic).
#    Kierunek gz→ros = sufiks '[' (zwalidowane w żywym smoke R3, results/R02/smoke_R3_live_*.log).
source /opt/ros/jazzy/setup.bash; source "$ROOT/ros2_ws/install/setup.bash"
ROS_IMG="$IMG_TOPIC"     # bridge nie zmienia nazwy
setsid nohup ros2 run ros_gz_bridge parameter_bridge \
  "${IMG_TOPIC}@sensor_msgs/msg/Image[gz.msgs.Image" > "$LOGDIR/bridge.log" 2>&1 &
PIDS+=($!); echo "[gate] most kamery pid=$! (gz==ros:$IMG_TOPIC)"
sleep 3

# 4) spawn intruza (model, nie actor — R1) na wysokości 6 m (paralaksa bearing-only)
gz service -s "/world/${WORLD}/create" --reqtype gz.msgs.EntityFactory \
  --reptype gz.msgs.Boolean --timeout 3000 \
  --req "sdf_filename: \"$ROOT/r02/intruder_model.sdf\", name: \"intruder\", pose: {position: {x: 12, y: 0, z: 14}}" \
  > "$LOGDIR/spawn.log" 2>&1
echo "[gate] intruz spawn: $(cat $LOGDIR/spawn.log)"

# 5) intruz per scenariusz (G1: oddalony; CHAR: statyczny (25,0,6); CHAR2: statyczny sygnał (25,0,8))
[ "$SCEN" = "CHAR2" ] && CHAR_INTRUDER="${CHAR_INTRUDER:-25,0,8}"
CHAR_INTRUDER="${CHAR_INTRUDER:-25,0,6}"
case "$SCEN" in
  G1) ;;  # G1 bez intruza w polu — przesuń go daleko
  CHAR|CHAR2) ;; # intruz statyczny w GT (bez drivera) — ustawiony niżej
  G2) ;;  # G2 intruz STATYCZNY w polu N drona @~7m alt11.5 (koperta A7) — set_pose niżej
  G3) setsid nohup python3 -m r02.intruder_driver --world "$WORLD" --seconds 90 --x 12 --z 11.5 \
        --log "$LOGDIR/intruder.jsonl" > "$LOGDIR/intruder.log" 2>&1 & PIDS+=($!) ;;
  *)  setsid nohup python3 -m r02.intruder_driver --world "$WORLD" --seconds 90 --x 12 --z 11.5 \
        --log "$LOGDIR/intruder.jsonl" > "$LOGDIR/intruder.log" 2>&1 & PIDS+=($!) ;;
esac
[ "$SCEN" = "G1" ] && gz service -s "/world/${WORLD}/set_pose" --reqtype gz.msgs.Pose \
  --reptype gz.msgs.Boolean --timeout 3000 \
  --req 'name: "intruder", position: {x: -60, y: 0, z: 6}, orientation: {w: 1.0}' >/dev/null 2>&1
# G2: intruz statyczny w polu Północ drona (7,0,11.5) — koperta A7 (3D~7m, elewacja~12°, tło nieba)
if [ "$SCEN" = "G2" ]; then
  for try in 1 2 3; do
    gz service -s "/world/${WORLD}/set_pose" --reqtype gz.msgs.Pose --reptype gz.msgs.Boolean \
      --timeout 3000 --req 'name: "intruder", position: {x: 7, y: 0, z: 11.5}, orientation: {w: 1.0}' >/dev/null 2>&1
    sleep 1
  done
  # WERYFIKACJA pozy (bug: set_pose bywa ignorowane zaraz po spawnie)
  gz topic -e -t "/world/${WORLD}/dynamic_pose/info" -n 1 2>/dev/null | grep -A5 'name: "intruder"' | grep -E "x:|y:|z:" | head -3 > "$LOGDIR/intruder_pose.log"
  echo "[gate] G2 intruz poza: $(tr '\n' ' ' < $LOGDIR/intruder_pose.log)"
fi
if [ "$SCEN" = "CHAR" ] || [ "$SCEN" = "CHAR2" ]; then
  IFS=',' read -r CGX CGY CGZ <<< "$CHAR_INTRUDER"
  gz service -s "/world/${WORLD}/set_pose" --reqtype gz.msgs.Pose --reptype gz.msgs.Boolean \
    --timeout 3000 --req "name: \"intruder\", position: {x: $CGX, y: $CGY, z: $CGZ}, orientation: {w: 1.0}" >/dev/null 2>&1
  echo "[gate] CHAR: intruz statyczny GT=($CHAR_INTRUDER)"
fi

# 6) węzeł detektora (env ROS2+torch) — POMIJANY w GT-FED (tor B: kanał z pozy GT, bez percepcji)
if [ "${GT_FED:-0}" != "1" ]; then
  YOLO_WEIGHTS="$ROOT/.b0deps/weights/yolov8s-worldv2.pt" \
    PYTHONPATH="$B0SP:$ROOT:${PYTHONPATH:-}" setsid nohup python3 -m r02.detector_node \
    --image-topic "$ROS_IMG" > "$LOGDIR/detector.log" 2>&1 &
  DET_PID=$!; PIDS+=($DET_PID); echo "[gate] detektor pid=$DET_PID"
  sleep 8   # załadowanie wag YOLO-World (~3 s w smoke)
else
  echo "[gate] GT-FED=1 → detektor POMINIĘTY (kanał zasilany pozą GT symulatora)"
fi

# 7) runner bramki
echo "[gate] start runner G=$SCEN (GT_FED=${GT_FED:-0})"
SCENARIO="$SCEN" TRACE="$LOGDIR/gate_${SCEN}.jsonl" CHAR_INTRUDER="$CHAR_INTRUDER" GT_FED="${GT_FED:-0}" \
  CHAR_LOG="${CHAR_LOG:-$LOGDIR/char.jsonl}" \
  PYTHONPATH="$ROOT:${PYTHONPATH:-}" python3 -m r02.gate_run_r02 2>&1 | tee "$LOGDIR/gate.log"
RC=${PIPESTATUS[0]}
echo "[gate] runner exit=$RC. dmesg (ostatnie 20, na wypadek padu):"
dmesg 2>/dev/null | tail -20 > "$LOGDIR/dmesg.log" || echo "  (dmesg niedostępny bez uprawnień)"
echo "[gate] === koniec $SCEN (rc=$RC). Logi: $LOGDIR ==="
exit $RC
