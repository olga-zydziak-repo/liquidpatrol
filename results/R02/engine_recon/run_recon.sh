#!/usr/bin/env bash
# run_recon.sh <DISC> <RUN> — jeden bieg ENGINE-RECON (diagnostyka renderu, NIE budowa).
# Konfiguracja przez env: CAM_KIND, CAM_Z, INTR_KIND, INTR_RANGE, RENDER (d3d12|llvmpipe).
# HEADLESS wymuszony i WERYFIKOWANY: gz sim -s (server-only) → zero procesów GUI (SR-E4).
# Artefakty: results/R02/engine_recon/<DISC>/<RUN>/ (frame.npy, frame.png, result.json, world_as_run.sdf).
set -uo pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
DISC="$1"; RUN="$2"
OUTDIR="$ROOT/results/R02/engine_recon/$DISC/$RUN"; mkdir -p "$OUTDIR"

export CAM_KIND="${CAM_KIND:-standalone}"; export CAM_Z="${CAM_Z:-9.0}"
export INTR_KIND="${INTR_KIND:-mesh}"; export INTR_RANGE="${INTR_RANGE:-7.0}"
RENDER="${RENDER:-d3d12}"

# render backend (habitat kontrolowany po 4845a92)
if [ "$RENDER" = "llvmpipe" ]; then
  export LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe; export RENDER_BACKEND="llvmpipe(software)"
else
  export GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA; export RENDER_BACKEND="mesa-d3d12"
fi
export GZ_SIM_RESOURCE_PATH="$ROOT/PX4-Autopilot/Tools/simulation/gz/models:${GZ_SIM_RESOURCE_PATH:-}"
export HEADLESS=1
export GZ_VER="$(gz sim --version 2>/dev/null | head -1)"

echo "[recon] $DISC/$RUN CAM_KIND=$CAM_KIND CAM_Z=$CAM_Z INTR=$INTR_KIND range=$INTR_RANGE RENDER=$RENDER_BACKEND"

# teardown poprzednich
pkill -9 -f 'gz sim' 2>/dev/null; pkill -9 -f 'ruby.*gz' 2>/dev/null; sleep 2

# generuj świat + kopia as-run (prowieniencja §6)
OUT="$OUTDIR/world_as_run.sdf" python3 results/R02/engine_recon/gen_world.py

# boot gz. Domyślnie SERVER-ONLY (headless z definicji). RECON_GUI=1 → bieg DIAGNOSTYCZNY z GUI (D3/D0.5-kontrola:
# świadomie włączony GUI jako narzędzie; oznaczony, NIEporównywalny z headless — SR-E4 nie egzekwuje headless).
if [ "${RECON_GUI:-0}" = "1" ]; then
  export HEADLESS=0
  setsid nohup gz sim -r -v1 "$OUTDIR/world_as_run.sdf" > "$OUTDIR/gz.log" 2>&1 &
  GZ_PID=$!; echo "[recon] gz (server+GUI) pid=$GZ_PID — BIEG DIAGNOSTYCZNY GUI-ON (oznaczony)"; echo "GUI_DIAGNOSTIC" > "$OUTDIR/GUI_DIAGNOSTIC"
  sleep 6
  GUI_PROCS=$(pgrep -af 'gz sim -g|gz-gui|ruby.*gz' | grep -v pgrep | head -3 || echo "brak")
  echo "[recon] GUI-ON: GUI_PROCS=[$GUI_PROCS]"
else
  setsid nohup gz sim -s -r -v1 "$OUTDIR/world_as_run.sdf" > "$OUTDIR/gz.log" 2>&1 &
  GZ_PID=$!; echo "[recon] gz -s pid=$GZ_PID (server-only)"
  # WERYFIKACJA HEADLESS (SR-E4): żaden proces GUI nie może istnieć
  sleep 4
  if pgrep -af 'gz sim -g|gz-gui' | grep -v pgrep >/dev/null 2>&1; then
    echo "[recon] !! GUI WYKRYTE — bieg NIEWAŻNY (SR-E4)"; echo "HEADLESS_VIOLATION" > "$OUTDIR/HEADLESS_VIOLATION"
  fi
  GUI_PROCS=$(pgrep -af 'gz sim -g|gz-gui' | grep -v pgrep || echo "brak")
  echo "[recon] weryfikacja headless: GUI_PROCS=[$GUI_PROCS]"
fi

# czekaj na topik kamery
IMG=""
for i in $(seq 1 40); do
  IMG=$(gz topic -l 2>/dev/null | grep -E "imager/image$" | head -1)
  [ -n "$IMG" ] && break; sleep 1
done
if [ -z "$IMG" ]; then
  echo "[recon] BRAK topiku imager/image po 40s — środowiskowo nieudany bieg"; echo "NO_TOPIC" > "$OUTDIR/NO_TOPIC"
  gz topic -l 2>/dev/null | head -30 > "$OUTDIR/topics.txt"
  pkill -9 -f 'gz sim' 2>/dev/null; exit 5
fi
echo "[recon] topik kamery: $IMG"; export IMG_TOPIC="$IMG"; export DISC RUN
gz topic -l 2>/dev/null > "$OUTDIR/topics.txt"

# przechwyt + pomiar + enumeracja
PYTHONPATH=".:${PYTHONPATH:-}" python3 results/R02/engine_recon/grab.py "$IMG" "$OUTDIR"
RC=$?

pkill -9 -f 'gz sim' 2>/dev/null; pkill -9 -f 'ruby.*gz' 2>/dev/null; sleep 1
echo "[recon] $DISC/$RUN DONE rc=$RC → $OUTDIR"
exit $RC
