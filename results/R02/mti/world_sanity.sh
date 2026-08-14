#!/usr/bin/env bash
# world_sanity.sh — WARUNEK WEJŚCIA (nie bieg): smoke boot w world_demo_v1 (R-M1). Kopiuje świat z repo
# do PX4 worlds, boot headless, weryfikuje H.1 (HEADLESS/RTF/time-jump), arm + krótki zawis + ląd.
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true
source env_gpu.sh >/dev/null 2>&1 || true
export HEADLESS=1
export GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA; export RENDER_BACKEND="mesa-d3d12"
WORLD="world_demo_v1"
OUTDIR="$ROOT/results/R02/mti/sanity/run1"; mkdir -p "$OUTDIR"
# R-M1: świat DEMA = źródło prawdy w repo/worlds; kopiuj do PX4 worlds (gitignored) na czas biegu
cp "$ROOT/worlds/world_demo_v1.sdf" "$ROOT/PX4-Autopilot/Tools/simulation/gz/worlds/world_demo_v1.sdf"
sha256sum "$ROOT/worlds/world_demo_v1.sdf" | tee "$OUTDIR/world_hash.txt"

teardown(){ pkill -9 -f 'gz sim' 2>/dev/null; pkill -9 -f 'bin/px4' 2>/dev/null; pkill -9 -f MicroXRCEAgent 2>/dev/null
  pkill -9 -f mavsdk_server 2>/dev/null; pkill -9 -f 'parameter_bridge' 2>/dev/null; pkill -9 -f 'detector_node' 2>/dev/null
  pkill -9 -f 'ruby.*gz' 2>/dev/null; sleep 2; }
teardown

LOGDIR="$OUTDIR" WORLD="$WORLD" MODEL=gz_x500_mono_cam bash run_stack.sh > "$OUTDIR/stack.log" 2>&1
sleep 3; GUI=$(pgrep -af 'gz sim -g|gz-gui' | grep -v pgrep || echo "brak")
echo "GUI_PROCS=[$GUI]  gz_server=[$(pgrep -af 'gz sim .*-r|gz sim -s' | grep -v pgrep | head -1)]" | tee "$OUTDIR/headless_proof.txt"

# czekaj na świat gz (clock) + kamerę
for i in $(seq 1 40); do gz topic -l 2>/dev/null | grep -q "/world/${WORLD}/clock" && break; sleep 1; done
RTF=$(gz topic -et /world/${WORLD}/stats -n 1 2>/dev/null | grep -m1 real_time_factor)
echo "world=${WORLD} rtf=[$RTF]" | tee "$OUTDIR/rtf.txt"
IMG=$(gz topic -l 2>/dev/null | grep -E "imager/image$" | head -1); echo "kamera: $IMG" | tee "$OUTDIR/camera.txt"

echo "[sanity] 60 s settle EKF"; sleep 60
grep -ci 'time jump\|Resetting time sync' "$OUTDIR/stack.log" > "$OUTDIR/timejump.txt" 2>/dev/null || echo 0 > "$OUTDIR/timejump.txt"

# krótki zawis przez MAVSDK
OUTDIR="$OUTDIR" PX4_GZ_WORLD="$WORLD" python3 - <<'PY' > "$OUTDIR/hover.log" 2>&1
import asyncio, os, time
from mavsdk import System
async def main():
    d=System(); await d.connect(system_address="udpin://0.0.0.0:14540")
    async for s in d.core.connection_state():
        if s.is_connected: break
    ok=False
    async for h in d.telemetry.health():
        if h.is_global_position_ok and h.is_home_position_ok: ok=True; break
    print("[sanity] healthy=",ok, flush=True)
    if not ok: os._exit(3)
    for i in range(20):
        try: await d.action.arm(); print("[sanity] ARMED"); break
        except Exception as e:
            if i%4==0: print("arm retry",i,e)
            await asyncio.sleep(3)
    else: os._exit(2)
    await d.action.set_takeoff_altitude(9.0); await d.action.takeoff()
    await asyncio.sleep(12)
    async for pv in d.telemetry.position_velocity_ned():
        print("[sanity] alt=%.2f"% (-pv.position.down_m)); break
    async for a in d.telemetry.attitude_euler():
        print("[sanity] att pitch=%.2f roll=%.2f"%(a.pitch_deg,a.roll_deg)); break
    try: await d.action.land(); await asyncio.sleep(3)
    except Exception: pass
    os._exit(0)
asyncio.run(main())
PY
RC=$?
echo "[sanity] hover rc=$RC"; cat "$OUTDIR/hover.log"
teardown
echo "[sanity] DONE rc=$RC → $OUTDIR"; exit $RC
