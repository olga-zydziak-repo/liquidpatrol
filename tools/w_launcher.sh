#!/usr/bin/env bash
# tools/w_launcher.sh — driver sesji nogi W (wiatr). NIE edytuje frozen harness/run_boot.sh.
# Realizuje PRE_W §8 (lock+pgrep wyłączności) i §9 (guard OUTDIR + odmowa przy istniejącym manifeście),
# oraz W9 (prepend GZ_SIM_RESOURCE_PATH=worlds/wind_models — dowód R1.7). Boot idzie WYŁĄCZNIE przez
# run_boot.sh (SR-W-8), który honoruje env OUTDIR (run_boot.sh:16: OUTDIR="${OUTDIR:-...}").
#
# Użycie:  w_launcher.sh <WORLD> <OUTDIR_REL_pod_results/W>   (np. probe/boot1_s0)
# Env passthrough (opcjonalne): FLIGHT (dom. empty), K1_HOVER_S (dom. 90), SETTLE_S (dom. 90),
#   BOOT_N (dom. 1), ARM/POINT/KIND — przekazywane do run_boot.sh.
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
WORLD="${1:?WORLD (np. world_wind_s0)}"
OUTREL="${2:?OUTDIR_REL pod results/W (np. probe/boot1_s0)}"
OUTDIR="$ROOT/results/W/$OUTREL"
LOCK="$ROOT/results/W/.executor_lock"
mkdir -p "$ROOT/results/W"

# --- §9 guard: docelowy OUTDIR z manifest.json ⇒ ODMOWA (REPO-2, incydent 25.08) ---
if [ -f "$OUTDIR/manifest.json" ]; then
  echo "[w_launcher] ODMOWA: $OUTDIR zawiera manifest.json (REPO-2 guard §9) — boot nie startuje"; exit 4
fi

# --- §8 wyłączność: żywy lock ⇒ ODMOWA ---
if [ -f "$LOCK" ]; then
  OLDPID="$(cat "$LOCK" 2>/dev/null)"
  if [ -n "$OLDPID" ] && kill -0 "$OLDPID" 2>/dev/null; then
    echo "[w_launcher] ODMOWA: żywy executor_lock pid=$OLDPID (§8) — boot nie startuje"; exit 5
  fi
  echo "[w_launcher] stale lock (pid=$OLDPID martwy) — przejmuję"
fi

# --- §8 pgrep wyłączności: cudzy proces bootowy ⇒ env_block, zero wojny killi (precedens 16.09) ---
COLL="$(pgrep -af 'run_sonda_boot|run_boot|gz sim|bin/px4' 2>/dev/null | grep -v -e "$$" -e 'w_launcher' -e pgrep)"
if [ -n "$COLL" ]; then
  echo "[w_launcher] ENV-BLOCK (§8): kolizja procesowa — NIE startuję (zero killi):"; echo "$COLL"; exit 3
fi

echo "$$" > "$LOCK"
trap 'rm -f "$LOCK"' EXIT

# --- W9: prepend modelu z enable_wind (dowód R1.7); gz_env.sh:19 dopisuje stock po naszym ---
export GZ_SIM_RESOURCE_PATH="$ROOT/worlds/wind_models${GZ_SIM_RESOURCE_PATH:+:$GZ_SIM_RESOURCE_PATH}"

FLIGHT="${FLIGHT:-empty}"; K1_HOVER_S="${K1_HOVER_S:-90}"; SETTLE_S="${SETTLE_S:-90}"; BOOT_N="${BOOT_N:-1}"
echo "[w_launcher] START world=$WORLD OUTDIR=$OUTDIR FLIGHT=$FLIGHT hover=$K1_HOVER_S lock=$$ gz_res=$GZ_SIM_RESOURCE_PATH"
FLIGHT="$FLIGHT" WORLD="$WORLD" BOOT_N="$BOOT_N" OUTDIR="$OUTDIR" \
  K1_HOVER_S="$K1_HOVER_S" SETTLE_S="$SETTLE_S" KIND="${KIND:-wind_probe}" \
  bash harness/run_boot.sh
RC=$?
echo "[w_launcher] DONE rc=$RC world=$WORLD → $OUTDIR"
exit "$RC"
