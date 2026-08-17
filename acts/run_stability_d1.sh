#!/usr/bin/env bash
# acts/run_stability_d1.sh <BOOT_N> — DEMO-B B5R3 D1: JEDEN boot z JAWNYM cyklem życia mavsdk_server
# (test leadu zombie-serwera). Przed probe: kill+wait mavsdk_server po nazwie + ss weryfikacja 14540/50051
# wolne; spawn mavsdk_server explicite (udpin 14540, gRPC 50051); klient bez auto-spawnu. Po biegu: ss freed.
# Zmiana WYŁĄCZNIE harness (SR-I1); świat/spec/sędzia/r01 nietknięte.
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
B0SP="$ROOT/.b0deps/lib/python3.12/site-packages"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true
source env_gpu.sh >/dev/null 2>&1 || true
export HEADLESS=1 GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA RENDER_BACKEND="mesa-d3d12"
MAVSDK_BIN="$HOME/.local/lib/python3.12/site-packages/mavsdk/bin/mavsdk_server"
N="${1:-1}"; WORLD="world_demo_A1"
OUT="$ROOT/results/demo/stability/d1_boot_${N}"; mkdir -p "$OUT"

teardown(){ pkill -9 -f 'gz sim' 2>/dev/null; pkill -9 -f 'px4_sitl' 2>/dev/null; pkill -9 -f MicroXRCEAgent 2>/dev/null
  pkill -9 -f mavsdk_server 2>/dev/null; pkill -9 -f 'parameter_bridge' 2>/dev/null; pkill -9 -f live_stability_probe 2>/dev/null
  pkill -9 -f 'ruby.*gz' 2>/dev/null; sleep 2; }
teardown
# V0/D1 higiena: potwierdź porty wolne PRZED bootem
{ echo "== pre-boot procs =="; pgrep -af 'mavsdk|px4|gz sim' | grep -v pgrep
  echo "== ss 14540/50051 pre-boot =="; ss -ulpn 2>/dev/null | grep -E ':14540|:14550'; ss -tlpn 2>/dev/null | grep ':50051'
  echo "(puste = wolne)"; } > "$OUT/hygiene_pre.txt" 2>&1

cp "$ROOT/worlds/${WORLD}.sdf" "$ROOT/PX4-Autopilot/Tools/simulation/gz/worlds/${WORLD}.sdf"
LOGDIR="$OUT" WORLD="$WORLD" PX4_GZ_WORLD="$WORLD" MODEL=gz_x500_mono_cam bash run_stack.sh > "$OUT/stack.log" 2>&1
sleep 3
echo "GUI=[$(pgrep -af 'gz sim -g|gz-gui' | grep -v pgrep || echo brak)]" | tee "$OUT/headless_proof.txt"
for i in $(seq 1 40); do gz topic -l 2>/dev/null | grep -q "/world/${WORLD}/clock" && break; sleep 1; done
MONO=""; for i in $(seq 1 40); do MONO=$(gz topic -l 2>/dev/null | grep -E "imager/image$" | head -1); [ -n "$MONO" ] && break; sleep 1; done
[ -n "$MONO" ] && setsid nohup ros2 run ros_gz_bridge parameter_bridge "${MONO}@sensor_msgs/msg/Image[gz.msgs.Image" > "$OUT/bridge_mono.log" 2>&1 &
sleep 2
gz service -s /world/${WORLD}/create --reqtype gz.msgs.EntityFactory --reptype gz.msgs.Boolean --timeout 3000 \
  --req "sdf_filename: \"$ROOT/r02/intruder_model.sdf\", name: \"intruder\", pose: {position: {x: 7.86, y: 0, z: 11.5}}" > "$OUT/spawn.log" 2>&1

echo "[d1 boot $N] 150 s settle EKF"; sleep 150

# --- JAWNY cykl życia mavsdk_server (D1) ---
pkill -9 -f mavsdk_server 2>/dev/null; sleep 1
{ echo "== ss 14540/50051 przed spawnem serwera =="; ss -ulpn 2>/dev/null | grep -E ':14540|:14550'; ss -tlpn 2>/dev/null | grep ':50051'; echo "(puste=wolne)"; } > "$OUT/hygiene_preserver.txt" 2>&1
setsid nohup "$MAVSDK_BIN" -p 50051 "udpin://0.0.0.0:14540" > "$OUT/mavsdk_server.log" 2>&1 &
MSRV=$!
sleep 4
{ echo "== ss PO spawnie serwera (14540 udp + 50051 grpc) =="; ss -ulpn 2>/dev/null | grep -E ':14540'; ss -tlpn 2>/dev/null | grep ':50051'
  echo "== mavsdk_server proc =="; pgrep -af mavsdk_server | grep -v pgrep; } > "$OUT/hygiene_postserver.txt" 2>&1

# klient BEZ auto-spawnu → łączy się do naszego serwera
MAVSDK_SERVER_ADDR="localhost" MAVSDK_SERVER_PORT=50051 HOVER_ALT=9.0 HOVER_HOLD_S=10 \
  PYTHONPATH="$B0SP:$ROOT:${PYTHONPATH:-}" python3 "$ROOT/acts/live_stability_probe.py" "$OUT/probe.json" > "$OUT/probe.log" 2>&1
RC=$?
{ echo "== ss PO probe (przed teardown) =="; ss -ulpn 2>/dev/null | grep -E ':14540'; ss -tlpn 2>/dev/null | grep ':50051'; } > "$OUT/hygiene_postprobe.txt" 2>&1
teardown
echo "[d1 boot $N] DONE rc=$RC → $OUT"; exit $RC
