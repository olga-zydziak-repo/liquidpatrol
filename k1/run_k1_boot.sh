#!/usr/bin/env bash
# k1/run_k1_boot.sh ARM POINT BOOT_N [KIND] — jeden boot K1 (PRE_K1 §2, ridery R1–R5).
#   ARM=S → osłona (gate_run_r03 SCEN=K1, ścieżka R0.3a NIETKNIĘTA, tylko punkt wstrzyknięcia)
#   ARM=N → natywny failsafe (k1_arm_n: EKF2_GPS_CTRL=0 + action.land δ=0, setpointy milkną po acku)
# Boot świeży, headless, 90 s konwergencji EKF, ulog kopiowany do OUTDIR (nigdy /tmp), habitat+sędzia.
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
ARM="${1:?arm N|S}"; POINT="${2:?point 0.2..0.8}"; BOOT_N="${3:-1}"; KIND="${4:-crit}"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true
source env_gpu.sh >/dev/null 2>&1 || true
export HEADLESS=1 GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA RENDER_BACKEND="mesa-d3d12"
WORLD="default"
PSTR=$(python3 -c "print(str($POINT).replace('.','_'))")
OUTDIR="$ROOT/results/K1/$ARM/p${PSTR}/boot${BOOT_N}"; mkdir -p "$OUTDIR"
B0SP="$ROOT/.b0deps/lib/python3.12/site-packages"

teardown(){ pkill -9 -f 'gz sim' 2>/dev/null; pkill -9 -f 'px4' 2>/dev/null; pkill -9 -f MicroXRCEAgent 2>/dev/null
  pkill -9 -f mavsdk_server 2>/dev/null; pkill -9 -f 'gate_run_r03' 2>/dev/null; pkill -9 -f 'k1_arm_n' 2>/dev/null
  pkill -9 -f 'rtf_sampler' 2>/dev/null; pkill -9 -f 'ruby.*gz' 2>/dev/null; sleep 2; }
teardown

# R4: certs_selfcheck (ramię S) — log przed bootem
if [ "$ARM" = "S" ]; then
  PYTHONPATH=".:.certdeps:${PYTHONPATH:-}" python3 -m r01.proofs.certs_selfcheck > "$OUTDIR/certs_selfcheck.log" 2>&1
  echo "certs_selfcheck rc=$?" | tee -a "$OUTDIR/certs_selfcheck.log"
fi

# higiena EKF2_GPS_CTRL (B5R3): reset persisted param do 7 przed bootem (leftover po GPS-denied)
python3 acts/ensure_gps_enabled.py > "$OUTDIR/gps_hygiene.txt" 2>&1

BOOT_T0=$(date +%s)
LOGDIR="$OUTDIR" WORLD="$WORLD" PX4_GZ_WORLD="$WORLD" MODEL=gz_x500_mono_cam bash run_stack.sh > "$OUTDIR/stack.log" 2>&1
sleep 3
echo "GUI_PROCS=[$(pgrep -af 'gz sim -g|gz-gui' | grep -v pgrep || echo brak)]" | tee "$OUTDIR/headless_proof.txt"
for i in $(seq 1 40); do gz topic -l 2>/dev/null | grep -q "/world/${WORLD}/clock" && break; sleep 1; done
setsid nohup python3 -m acts.rtf_sampler --world "$WORLD" --out "$OUTDIR/rtf_stream.jsonl" > "$OUTDIR/rtf_sampler.log" 2>&1 &
RTF=$!
echo "[K1 $ARM p$POINT b$BOOT_N] 90 s preflight EKF"; sleep 90
grep -ci 'time jump\|Resetting time sync' "$OUTDIR/stack.log" > "$OUTDIR/timejump_pre.txt" 2>/dev/null || echo 0 > "$OUTDIR/timejump_pre.txt"

if [ "$ARM" = "S" ]; then
  SCEN="K1" K1_POINT="$POINT" GATE_OUT="$OUTDIR/trace.jsonl" PX4_GZ_WORLD="$WORLD" HEADLESS=1 B1_MODEL=x500_mono_cam_0 \
    PYTHONPATH=".:.certdeps:${PYTHONPATH:-}" python3 -m r03.gate_run_r03 > "$OUTDIR/act.log" 2>&1
  RC=$?; HARNESS_FILE="$ROOT/r03/gate_run_r03.py"
else
  K1_POINT="$POINT" GATE_OUT="$OUTDIR/trace.jsonl" PX4_GZ_WORLD="$WORLD" HEADLESS=1 B1_MODEL=x500_mono_cam_0 \
    PYTHONPATH=".:.certdeps:${PYTHONPATH:-}" python3 k1/k1_arm_n.py > "$OUTDIR/act.log" 2>&1
  RC=$?; HARNESS_FILE="$ROOT/k1/k1_arm_n.py"
fi

kill -TERM "$RTF" 2>/dev/null; sleep 1
grep -ci 'time jump\|Resetting time sync' "$OUTDIR/stack.log" > "$OUTDIR/timejump_post.txt" 2>/dev/null || echo 0 > "$OUTDIR/timejump_post.txt"
grep -ciE 'High Gyro Bias|velocity unstable|horizontal velocity' "$OUTDIR/px4.log" > "$OUTDIR/ekf_health_hits.txt" 2>/dev/null || echo 0 > "$OUTDIR/ekf_health_hits.txt"

# ulog: skopiuj nowy .ulg tego bootu (PRE §2 — nigdy /tmp)
ULG=$(find "$ROOT/PX4-Autopilot/build/px4_sitl_default/rootfs/log" -name '*.ulg' -newermt "@$BOOT_T0" 2>/dev/null | xargs -r ls -t 2>/dev/null | head -1)
if [ -n "$ULG" ]; then cp "$ULG" "$OUTDIR/boot.ulg"; echo "$ULG" > "$OUTDIR/ulog_src.txt"; else echo "BRAK ulog" > "$OUTDIR/ulog_src.txt"; fi

teardown

# finalize: manifest R5 + habitat (H1∧H2 claim denial→touchdown) + sędzia frozen → judge.json
ULGARG=""; [ -f "$OUTDIR/boot.ulg" ] && ULGARG="--ulog $OUTDIR/boot.ulg"
CERTS=""; [ "$ARM" = "S" ] && CERTS="--certs-selfcheck $OUTDIR/certs_selfcheck.log"
PYTHONPATH="$B0SP:$ROOT:${PYTHONPATH:-}" python3 k1/k1_finalize.py \
  --trace "$OUTDIR/trace.jsonl" --arm "$ARM" --point "$POINT" --boot "$BOOT_N" --kind "$KIND" \
  $ULGARG --harness-sha-file "$HARNESS_FILE" --out-dir "$OUTDIR" $CERTS 2>&1 | tee "$OUTDIR/finalize.log"

echo "[K1 $ARM p$POINT b$BOOT_N] DONE rc=$RC → $OUTDIR"; exit $RC
