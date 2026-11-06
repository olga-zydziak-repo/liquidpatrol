#!/usr/bin/env bash
# results/KONT/s2/stack_dryrun/run_dryrun.sh — próba na sucho ANEKS_KONT-1d §2.3: bajtowo ta sama kopia harness/kont_run_stack_s2d.sh w piaskownicy, w której bin/px4 to atrapa; gz i agent prawdziwe. Środowisko jak w harness/kont_boot_s2d.sh. Użycie: run_dryrun.sh <katalog piaskownicy>
set -o pipefail
ROOT=/home/olga/projects/liquidpatrol; OUT=$ROOT/results/KONT/s2/stack_dryrun; SB="${1:?piaskownica}"
P=$SB/PX4-Autopilot/build/px4_sitl_default
mkdir -p "$SB/harness" "$P/bin"
cp "$ROOT/harness/kont_run_stack_s2d.sh" "$SB/harness/"
ln -sfn "$ROOT/env_gpu.sh" "$SB/env_gpu.sh"; ln -sfn "$ROOT/results" "$SB/results"
ln -sfn "$ROOT/PX4-Autopilot/build/px4_sitl_default/rootfs" "$P/rootfs"
cp "$OUT/px4_stub.py" "$P/bin/px4"; chmod +x "$P/bin/px4"
sha256sum "$ROOT/harness/kont_run_stack_s2d.sh" "$SB/harness/kont_run_stack_s2d.sh" | cut -c1-16 > "$OUT/sha_kopii.txt"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true
export GZ_IP=127.0.0.1 HEADLESS=1 DRY_OUT="$OUT"
T0=$(date +%s.%N)
env -u GZ_SIM_RESOURCE_PATH -u GZ_SIM_SYSTEM_PLUGIN_PATH LOGDIR="$OUT" WORLD=world_kont_A3 PX4_GZ_WORLD=world_kont_A3 MODEL=gz_x500_mono_cam_flow PX4_SYS_AUTOSTART=4010 PX4_SIM_MODEL=gz_x500_mono_cam_flow \
  timeout 180 bash "$SB/harness/kont_run_stack_s2d.sh" > "$OUT/stack.log" 2>&1
RC=$?
T1=$(date +%s.%N)
python3 "$ROOT/results/KONT/tools/kont_inw.py" LIST gz px4 MicroXRCEAgent > "$OUT/procesy_po_stosie.txt"
python3 "$ROOT/results/KONT/tools/kont_inw.py" KILL gz px4 MicroXRCEAgent > /dev/null; sleep 2
python3 "$ROOT/results/KONT/tools/kont_inw.py" LIST gz px4 MicroXRCEAgent > "$OUT/procesy_po_kill.txt"
echo "{\"rc\": $RC, \"t0\": $T0, \"t1\": $T1}" > "$OUT/wynik_stosu.json"
