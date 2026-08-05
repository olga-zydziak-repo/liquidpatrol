#!/usr/bin/env bash
# apply_camera_a4.sh — [A4] zamraża konfigurację kamery mono_cam PONIŻEJ progu saturacji (R3).
# 1280x960@30 visualize=true  →  640x480@15 visualize=false. Idempotentny.
# Powód (R3): 1280x960@30 saturuje render (≈13 Hz, min/s 4); 640x480@15 utrzymywalne z zapasem.
set -uo pipefail
SDF="$HOME/projects/liquidpatrol/PX4-Autopilot/Tools/simulation/gz/models/mono_cam/model.sdf"
[ -f "$SDF" ] || { echo "[A4] brak $SDF"; exit 1; }
sed -i 's#<width>1280</width>#<width>640</width>#' "$SDF"
sed -i 's#<height>960</height>#<height>480</height>#' "$SDF"
sed -i 's#<update_rate>30</update_rate>#<update_rate>15</update_rate>#' "$SDF"
sed -i 's#<visualize>true</visualize>#<visualize>false</visualize>#' "$SDF"
echo "[A4] mono_cam skonfigurowany:"
grep -E "<width>|<height>|<update_rate>|<visualize>" "$SDF" | sed 's/^ *//'
