#!/usr/bin/env bash
# harness/run_boot.sh — JEDEN wrapper bootu programu (PROMPT_INFRA3 §B1.1 + bramka procesowa ANEKS_INFRA3-3 §3).
# Kompozycja ISTNIEJĄCYCH mechanizmów, kolejność jak run_k1_boot.sh. Parametry przez env.
# Przyrządy zamkniętych serii (k1/run_k1_boot.sh, acts/run_act.sh, run_A3.sh) NIETKNIĘTE.
#
# Env: FLIGHT=empty|gate_r03|arm_n (dom. empty) · WORLD (dom. default) · BOOT_N (dom. 1) ·
#      OUTDIR (dom. results/INFRA3/B/boot<BOOT_N>) · SETTLE_S (dom. 90, MIN 90 — niżej odrzucane) ·
#      INTRUDER=0|1 · INTRUDER_POSE (dom. jak run_act.sh) · FILM=0|1 ·
#      ARM/POINT/KIND (dla finalize; empty→ARM=E) · SCEN/K1_POINT/CONTROLLER (passthrough) · K1_HOVER_S.
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"

FLIGHT="${FLIGHT:-empty}"
WORLD="${WORLD:-default}"
BOOT_N="${BOOT_N:-1}"
OUTDIR="${OUTDIR:-$ROOT/results/INFRA3/B/boot${BOOT_N}}"
SETTLE_S="${SETTLE_S:-90}"
INTRUDER="${INTRUDER:-0}"
INTRUDER_POSE="${INTRUDER_POSE:-position: {x: 7, y: 0, z: 11.5}}"
FILM="${FILM:-0}"
KIND="${KIND:-crit}"
# ARM/POINT: nazewnictwo finalize. empty→E; gate_r03/arm_n wymagają POINT.
case "$FLIGHT" in
  empty|bench) ARM="${ARM:-E}"; POINT="${POINT:-0.0}";;
  gate_r03) ARM="${ARM:-S}"; POINT="${POINT:?POINT wymagany dla gate_r03}";;
  arm_n)    ARM="${ARM:-N}"; POINT="${POINT:?POINT wymagany dla arm_n}";;
  *) echo "FLIGHT nieznany: $FLIGHT (empty|gate_r03|arm_n)"; exit 2;;
esac

# --- GUARD: SETTLE_S < 90 ODRZUCONE (§B1.1 pkt 6; test B1.2 iv) — przed czymkolwiek ciężkim ---
if awk "BEGIN{exit !($SETTLE_S < 90)}"; then
  echo "[run_boot] SETTLE_S=$SETTLE_S < 90 — ODRZUCONE (minimum 90 s settle EKF)"; exit 2
fi
mkdir -p "$OUTDIR"

source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true
source env_gpu.sh >/dev/null 2>&1 || true
export HEADLESS=1 GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA RENDER_BACKEND="mesa-d3d12"
B0SP="$ROOT/.b0deps/lib/python3.12/site-packages"

teardown(){ pkill -9 -f 'gz sim' 2>/dev/null; pkill -9 -f 'bin/px4' 2>/dev/null; pkill -9 -f MicroXRCEAgent 2>/dev/null
  pkill -9 -f mavsdk_server 2>/dev/null; pkill -9 -f 'gate_run_r03' 2>/dev/null; pkill -9 -f 'k1_arm_n' 2>/dev/null
  pkill -9 -f 'infra1_empty_flight' 2>/dev/null; pkill -9 -f 'rtf_sampler' 2>/dev/null
  pkill -9 -f 'parameter_bridge' 2>/dev/null; pkill -9 -f 'ruby.*gz' 2>/dev/null; sleep 2; }

# ============ 1. B4 (orphany + cooldown) + inwentarz + BRAMKA PROCESOWA §3 ============
ORPH_PAT='gz sim|bin/px4|MicroXRCEAgent|mavsdk_server|gate_run_r03|k1_arm_n|infra1_empty_flight|rtf_sampler|ruby.*gz'
ORPH_PRE=$(pgrep -fc "$ORPH_PAT" 2>/dev/null); ORPH_PRE=${ORPH_PRE:-0}
# marker program-wide + fallback K1 dla pierwszego bootu
LAST_END_F="$ROOT/results/.last_boot_end"
[ -f "$LAST_END_F" ] || LAST_END_F="$ROOT/results/K1/.last_boot_end"
NOW_T=$(date +%s)
if [ -f "$LAST_END_F" ]; then COOLDOWN=$(( NOW_T - $(cat "$LAST_END_F") )); else COOLDOWN=-1; fi
ps aux --sort=-%cpu | head -20 > "$OUTDIR/proc_inventory.txt"
cp "$OUTDIR/proc_inventory.txt" "$OUTDIR/proc_inventory_pre.txt"
teardown
ORPH_POST=$(pgrep -fc "$ORPH_PAT" 2>/dev/null); ORPH_POST=${ORPH_POST:-0}
python3 -c "import json;json.dump({'orphans_pre_teardown':$ORPH_PRE,'orphans_post_teardown':$ORPH_POST,'cooldown_s_since_last_boot':$COOLDOWN,'cooldown_src':'$(basename $(dirname $LAST_END_F))','one_boot_per_cycle':True},open('$OUTDIR/b4_state.json','w'))"

# BRAMKA PROCESOWA (§3): env-block przy cudzym procesie >2% CPU lub loadavg>1.5. Semantyka I2a.
if ! python3 harness/proc_gate.py --self "$PPID" > "$OUTDIR/proc_gate.log" 2>&1; then
  cat "$OUTDIR/proc_gate.log" | tee "$OUTDIR/env_block.txt"
  python3 harness/stub_manifest.py --out-dir "$OUTDIR" --arm "$ARM" --point "$POINT" --boot "$BOOT_N" \
    --rc 0 --finalize-rc 0 --run-id "envblock-b${BOOT_N}" >/dev/null 2>&1
  python3 -c "import json;p='$OUTDIR/manifest.json';m=json.load(open(p));m['kind']='env-block';m['reason']='proc_gate: cudzy proces >2% CPU lub loadavg>1.5 (§3)';json.dump(m,open(p,'w'),indent=2)"
  echo "[run_boot b$BOOT_N] ENV-BLOCK (proc_gate §3) — boot nie startuje"; teardown; exit 3
fi
echo "[run_boot b$BOOT_N] proc_gate §3 CLEAN"

# ============ 2. certs_selfcheck (gate_r03) ============
if [ "$FLIGHT" = "gate_r03" ]; then
  PYTHONPATH=".:.certdeps:${PYTHONPATH:-}" python3 -m r01.proofs.certs_selfcheck > "$OUTDIR/certs_selfcheck.log" 2>&1
  echo "certs_selfcheck rc=$?" | tee -a "$OUTDIR/certs_selfcheck.log"
fi

# ============ 3. higiena GPS + CAL_MAG (zawsze) ============
python3 acts/ensure_gps_enabled.py > "$OUTDIR/gps_hygiene.txt" 2>&1
python3 acts/ensure_mag_baseline.py > "$OUTDIR/mag_hygiene.txt" 2>&1

# ============ 4. bramka obciążenia I2a (LOAD_MAX 8.0, 10 min) ============
LOAD_MAX="${K1_LOAD_MAX:-8.0}"; LOAD_WAIT_MAX="${K1_LOAD_WAIT_MAX:-600}"
_lt0=$(date +%s); _load_ok=0; _l1="?"
while :; do
  _l1=$(cut -d' ' -f1 /proc/loadavg)
  if awk "BEGIN{exit !($_l1 < $LOAD_MAX)}"; then _load_ok=1; break; fi
  [ $(( $(date +%s) - _lt0 )) -ge "$LOAD_WAIT_MAX" ] && break
  echo "[run_boot b$BOOT_N] load $_l1 ≥ $LOAD_MAX — czekam"; sleep 30
done
if [ "$_load_ok" != "1" ]; then
  echo "ENV-BLOCK load1=$_l1 max=$LOAD_MAX" | tee "$OUTDIR/env_block.txt"
  python3 harness/stub_manifest.py --out-dir "$OUTDIR" --arm "$ARM" --point "$POINT" --boot "$BOOT_N" --rc 0 --finalize-rc 0 >/dev/null 2>&1
  python3 -c "import json;p='$OUTDIR/manifest.json';m=json.load(open(p));m['kind']='env-block';m['reason']='I2a loadavg';json.dump(m,open(p,'w'),indent=2)"
  teardown; echo "[run_boot b$BOOT_N] ENV-BLOCK (load $_l1)"; exit 3
fi

# ============ 5. świat + hash ============
bash harness/world_hash.sh "$WORLD" "$OUTDIR" > "$OUTDIR/world_hash.log" 2>&1 || { echo "world_hash FAIL"; teardown; exit 2; }

# ============ 6. stack + headless + clock + RTF + watchdog + settle + timejump_pre ============
BOOT_T0=$(date +%s)
LOGDIR="$OUTDIR" WORLD="$WORLD" PX4_GZ_WORLD="$WORLD" MODEL=gz_x500_mono_cam bash run_stack.sh > "$OUTDIR/stack.log" 2>&1
sleep 3
echo "GUI_PROCS=[$(pgrep -af 'gz sim -g|gz-gui' | grep -v pgrep || echo brak)]" | tee "$OUTDIR/headless_proof.txt"
for i in $(seq 1 40); do gz topic -l 2>/dev/null | grep -q "/world/${WORLD}/clock" && break; sleep 1; done
setsid nohup python3 -m acts.rtf_sampler --world "$WORLD" --out "$OUTDIR/rtf_stream.jsonl" > "$OUTDIR/rtf_sampler.log" 2>&1 &
RTF=$!
setsid nohup python3 tools/infra2_ekf_watchdog.py \
  --px4-bin "$ROOT/PX4-Autopilot/build/px4_sitl_default/bin" \
  --out "$OUTDIR/ekf_watchdog.json" > "$OUTDIR/ekf_watchdog.log" 2>&1 &
WD=$!
echo "[run_boot b$BOOT_N] watchdog EKF2 (preflight-only, max 2 reinity) pid=$WD" | tee -a "$OUTDIR/ekf_watchdog.log"

# ============ 7. intruz (INTRUDER=1) + dowód obecności; film (FILM=1) ============
FILM_TOPIC=""
if [ "$FILM" = "1" ]; then
  for i in $(seq 1 40); do FILM_TOPIC=$(gz topic -l 2>/dev/null | grep -iE "film.*image$" | head -1); [ -n "$FILM_TOPIC" ] && break; sleep 1; done
  echo "FILM_TOPIC=$FILM_TOPIC" | tee "$OUTDIR/film_topic.txt"
  [ -n "$FILM_TOPIC" ] && setsid nohup ros2 run ros_gz_bridge parameter_bridge "${FILM_TOPIC}@sensor_msgs/msg/Image[gz.msgs.Image" > "$OUTDIR/bridge.log" 2>&1 &
fi
if [ "$INTRUDER" = "1" ]; then
  gz service -s /world/${WORLD}/create --reqtype gz.msgs.EntityFactory --reptype gz.msgs.Boolean --timeout 3000 \
    --req "sdf_filename: \"$ROOT/r02/intruder_model.sdf\", name: \"intruder\", pose: {${INTRUDER_POSE}}" > "$OUTDIR/spawn.log" 2>&1
  sleep 2
  if gz model --list 2>/dev/null | grep -qi 'intruder'; then MODEL_IN_STATE=1; else MODEL_IN_STATE=0; fi
  echo "model_in_state=$MODEL_IN_STATE" | tee "$OUTDIR/model_in_state.txt"
fi

echo "[run_boot b$BOOT_N] settle ${SETTLE_S}s preflight EKF"; sleep "$SETTLE_S"
grep -ci 'time jump\|Resetting time sync' "$OUTDIR/stack.log" > "$OUTDIR/timejump_pre.txt" 2>/dev/null || echo 0 > "$OUTDIR/timejump_pre.txt"

# ============ 8. moduł lotu ============
case "$FLIGHT" in
  gate_r03)
    SCEN="${SCEN:-K1}" K1_POINT="${K1_POINT:-$POINT}" CONTROLLER="${CONTROLLER:-route}" \
      GATE_OUT="$OUTDIR/trace.jsonl" PX4_GZ_WORLD="$WORLD" HEADLESS=1 B1_MODEL=x500_mono_cam_0 \
      PYTHONPATH=".:.certdeps:${PYTHONPATH:-}" python3 -m r03.gate_run_r03 > "$OUTDIR/act.log" 2>&1
    RC=$?; HARNESS_FILE="$ROOT/r03/gate_run_r03.py";;
  arm_n)
    K1_POINT="${K1_POINT:-$POINT}" GATE_OUT="$OUTDIR/trace.jsonl" PX4_GZ_WORLD="$WORLD" HEADLESS=1 B1_MODEL=x500_mono_cam_0 \
      PYTHONPATH=".:.certdeps:${PYTHONPATH:-}" python3 k1/k1_arm_n.py > "$OUTDIR/act.log" 2>&1
    RC=$?; HARNESS_FILE="$ROOT/k1/k1_arm_n.py";;
  empty)
    K1_HOVER_S="${K1_HOVER_S:-60}" GATE_OUT="$OUTDIR/trace.jsonl" PX4_GZ_WORLD="$WORLD" HEADLESS=1 B1_MODEL=x500_mono_cam_0 \
      PYTHONPATH=".:${PYTHONPATH:-}" python3 tools/infra1_empty_flight.py > "$OUTDIR/act.log" 2>&1
    RC=$?; HARNESS_FILE="$ROOT/tools/infra1_empty_flight.py";;
  bench) GATE_OUT="$OUTDIR/trace.jsonl" PX4_GZ_WORLD="$WORLD" HEADLESS=1 B1_MODEL=x500_mono_cam_0 PYTHONPATH=".:.certdeps:${PYTHONPATH:-}" python3 -m bench.bench_flight > "$OUTDIR/act.log" 2>&1; RC=$?; HARNESS_FILE="$ROOT/bench/bench_flight.py";;
esac

# ============ 9. post: term RTF/watchdog, timejump_post, health, ulog + sha ============
kill -TERM "$RTF" 2>/dev/null
[ -n "$WD" ] && { kill -TERM "$WD" 2>/dev/null; sleep 7; }   # watchdog dopisuje ekf_watchdog.json na SIGTERM
sleep 1
grep -ci 'time jump\|Resetting time sync' "$OUTDIR/stack.log" > "$OUTDIR/timejump_post.txt" 2>/dev/null || echo 0 > "$OUTDIR/timejump_post.txt"
grep -ciE 'High Gyro Bias|velocity unstable|horizontal velocity' "$OUTDIR/px4.log" > "$OUTDIR/ekf_health_hits.txt" 2>/dev/null || echo 0 > "$OUTDIR/ekf_health_hits.txt"
ULG=$(find "$ROOT/PX4-Autopilot/build/px4_sitl_default/rootfs/log" -name '*.ulg' -newermt "@$BOOT_T0" 2>/dev/null | xargs -r ls -t 2>/dev/null | head -1)
if [ -n "$ULG" ]; then
  cp "$ULG" "$OUTDIR/boot.ulg"; echo "$ULG" > "$OUTDIR/ulog_src.txt"
  python3 -c "import hashlib,os;p='$OUTDIR/boot.ulg';h=hashlib.sha256(open(p,'rb').read()).hexdigest();open('$OUTDIR/ulog_sha.txt','w').write(f'{h}  {os.path.getsize(p)}\n')"
else
  echo "BRAK ulog" > "$OUTDIR/ulog_src.txt"
fi

teardown

# ============ 10. finalize wg FLIGHT + łapacz klasy (stub) + augmentacja manifestu ============
if [ "$FLIGHT" = "empty" ]; then
  PYTHONPATH="$B0SP:$ROOT:${PYTHONPATH:-}" python3 tools/infra1_empty_finalize.py \
    --out-dir "$OUTDIR" --boot "$BOOT_N" --rc "$RC" --harness-sha-file "$HARNESS_FILE" 2>&1 | tee "$OUTDIR/finalize.log"
  FIN_RC=${PIPESTATUS[0]}
elif [ "$FLIGHT" = "bench" ]; then                        # ANEKS_BENCH-1a §2 R2: manifest ławki (nie k1_finalize)
  ULGARG=""; [ -f "$OUTDIR/boot.ulg" ] && ULGARG="--ulog $OUTDIR/boot.ulg"
  PYTHONPATH="$B0SP:$ROOT:${PYTHONPATH:-}" python3 bench/bench_finalize.py \
    --out-dir "$OUTDIR" --boot "$BOOT_N" --rc "$RC" --harness-sha-file "$HARNESS_FILE" --arm "$ARM" --point "$POINT" $ULGARG 2>&1 | tee "$OUTDIR/finalize.log"
  FIN_RC=${PIPESTATUS[0]}
else
  ULGARG=""; [ -f "$OUTDIR/boot.ulg" ] && ULGARG="--ulog $OUTDIR/boot.ulg"
  CERTS=""; [ "$FLIGHT" = "gate_r03" ] && CERTS="--certs-selfcheck $OUTDIR/certs_selfcheck.log"
  PYTHONPATH="$B0SP:$ROOT:${PYTHONPATH:-}" python3 k1/k1_finalize.py \
    --trace "$OUTDIR/trace.jsonl" --arm "$ARM" --point "$POINT" --boot "$BOOT_N" --kind "$KIND" \
    $ULGARG --harness-sha-file "$HARNESS_FILE" --out-dir "$OUTDIR" $CERTS 2>&1 | tee "$OUTDIR/finalize.log"
  FIN_RC=${PIPESTATUS[0]}
fi
# łapacz: finalize rc≠0 LUB brak manifest.json ⇒ stub (lekcja R5)
if [ "$FIN_RC" != "0" ] || [ ! -f "$OUTDIR/manifest.json" ]; then
  echo "[run_boot b$BOOT_N] finalize rc=$FIN_RC lub brak manifestu → stub_manifest"
  python3 harness/stub_manifest.py --out-dir "$OUTDIR" --arm "$ARM" --point "$POINT" --boot "$BOOT_N" \
    --rc "$RC" --finalize-rc "$FIN_RC" 2>&1 | tee -a "$OUTDIR/finalize.log"
fi
# augmentacja: world_hash + ulog_sha + model_in_state → manifest (nie dotyka sędziego)
MIS_ARG=""; [ "$INTRUDER" = "1" ] && MIS_ARG="--model-in-state ${MODEL_IN_STATE:-0}"
PYTHONPATH="$B0SP:$ROOT:${PYTHONPATH:-}" python3 harness/augment_manifest.py --out-dir "$OUTDIR" \
  --world-hash-file "$OUTDIR/world_hash.txt" --ulog "$OUTDIR/boot.ulg" $MIS_ARG 2>&1 | tee -a "$OUTDIR/finalize.log"

# ============ 11. marker końca (program-wide) ============
date +%s > "$ROOT/results/.last_boot_end"
echo "[run_boot b$BOOT_N] DONE flight=$FLIGHT world=$WORLD rc=$RC finalize=$FIN_RC → $OUTDIR"; exit "$RC"
