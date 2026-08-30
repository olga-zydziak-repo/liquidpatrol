#!/usr/bin/env bash
# harness/world_hash.sh <WORLD> <OUTDIR> — hash świata (PROMPT_INFRA3 §B1.1 pkt 5).
#   worlds/<WORLD>.sdf istnieje  → kopia do PX4 + sha256 świata z worlds/ → world_hash.txt = "<sha>  worlds/<W>.sdf"
#   stockowy (tylko w PX4 worlds) → world_hash.txt = "stock:<W> <sha>  <ścieżka stock>"
# Wypisuje też sha na stdout. Zwraca 0 gdy policzył hash, 2 gdy nie znalazł świata.
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"
WORLD="${1:?WORLD}"; OUTDIR="${2:?OUTDIR}"
PX4_WORLDS="$ROOT/PX4-Autopilot/Tools/simulation/gz/worlds"
mkdir -p "$OUTDIR"
SRC_REPO="$ROOT/worlds/${WORLD}.sdf"
SRC_STOCK="$PX4_WORLDS/${WORLD}.sdf"
if [ -f "$SRC_REPO" ]; then
  cp "$SRC_REPO" "$PX4_WORLDS/${WORLD}.sdf"           # kopia do PX4 (wzór run_act.sh)
  SHA=$(sha256sum "$SRC_REPO" | cut -d' ' -f1)
  echo "$SHA  worlds/${WORLD}.sdf" | tee "$OUTDIR/world_hash.txt"
elif [ -f "$SRC_STOCK" ]; then
  SHA=$(sha256sum "$SRC_STOCK" | cut -d' ' -f1)
  echo "stock:${WORLD} $SHA  $SRC_STOCK" | tee "$OUTDIR/world_hash.txt"
else
  echo "BRAK świata ${WORLD} (ani worlds/ ani stock)" | tee "$OUTDIR/world_hash.txt"
  exit 2
fi
