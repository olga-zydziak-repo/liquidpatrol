#!/usr/bin/env bash
# render_check.sh — odtwarzalny dowod, ze Gazebo renderuje na GPU D3D12 (nie llvmpipe).
# Uruchamia gz -v4 na pusty swiat na ~20s pod env_gpu, czyta GL_RENDERER z ogre2.log.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$HERE/env_gpu.sh"

echo "[render_check] start gz (20s)…"
timeout 20 gz sim -v4 -r empty.sdf > /tmp/gz_render_check.log 2>&1
echo "[render_check] gz exit: $? (124=timeout=OK, 144=GPU pad)"

OGRE="$HOME/.gz/rendering/ogre2.log"
echo "[render_check] GL renderer z $OGRE:"
grep -iE "GL_VENDOR|GL_RENDERER|GL_VERSION" "$OGRE" | tail -3 | sed 's/^[0-9:]* //'

if grep -qi "D3D12 (NVIDIA" "$OGRE"; then
  echo "[render_check] WERDYKT: GPU D3D12/NVIDIA  ✓"
elif grep -qi "llvmpipe" "$OGRE"; then
  echo "[render_check] WERDYKT: llvmpipe (SOFTWARE)  ✗  — env_gpu nie zadzialalo"
else
  echo "[render_check] WERDYKT: nieokreslony — sprawdz $OGRE"
fi
