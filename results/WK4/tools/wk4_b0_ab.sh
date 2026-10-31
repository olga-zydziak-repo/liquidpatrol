#!/usr/bin/env bash
# results/WK4/tools/wk4_b0_ab.sh — B0 diagnoza zacięć w GOŁYM gz (PRE_WK4 §2 B0.1; 0 bootów, bez PX4).
# Serwer jak px4-rc.gzsim:53 (`gz sim --verbose=1 -r -s <świat>`, env z rootfs/gz_env.sh + prepend
# worlds/wind_models jak driver), izolowany GZ_PARTITION, GZ_IP=127.0.0.1. Próbnik = wk4_zaciecia.py live
# (subskrybent /world/<W>/clock w Pythonie — obecny w KAŻDYM wariancie, bo to on mierzy).
# Warianty:  i   world_wk4 + publikator 746a958b (D2, 20 Hz, log do pliku)
#            ii  world_wk4 bez publikatora
#            iii world_wk3_p2 (bez publikatora; sam subskrybent zegara = próbnik)
#            iv  world_wk4 + publikator 746a958b z logiem do /dev/null
#            v   world_wk4 + publikator v2 napędzany /stats (podaj ścieżkę jako $3)
# Użycie: wk4_b0_ab.sh <wariant> <czas_ściany_s> [publikator_v2.py]
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
V="${1:?wariant}"; SECS="${2:?czas}"; PV2="${3:-}"
OUT="$ROOT/results/WK4/b0"; mkdir -p "$OUT"
SER="$ROOT/results/WK4_RECON/series/D2.json"; SER_SHA="6e09f653d44d3c40d78e22d0365e903af8c27300ec4b590c26b2cdcbc9544b64"
PUB="$ROOT/results/WK4_RECON/tools/wk4_publisher.py"
case "$V" in i|ii|iv|v) W=world_wk4;; iii) W=world_wk3_p2;; *) echo "wariant?"; exit 2;; esac
. "$ROOT/PX4-Autopilot/build/px4_sitl_default/rootfs/gz_env.sh"
export GZ_SIM_RESOURCE_PATH="$ROOT/worlds/wind_models:$GZ_SIM_RESOURCE_PATH"
export GZ_IP=127.0.0.1 GZ_PARTITION="wk4b0_${V}_$$"
TAG="ab_${V}_$(date +%H%M%S)"
setsid gz sim --verbose=1 -r -s "$ROOT/worlds/$W.sdf" > "$OUT/${TAG}_gz.log" 2>&1 &
GZ=$!
PP=""
case "$V" in
  i)  setsid python3 "$PUB" "$SER" "$SER_SHA" "$W" 40 "$OUT/${TAG}_pub.jsonl" 20 > "$OUT/${TAG}_pub.out" 2>&1 & PP=$!;;
  iv) setsid python3 "$PUB" "$SER" "$SER_SHA" "$W" 40 /dev/null 20 > "$OUT/${TAG}_pub.out" 2>&1 & PP=$!;;
  v)  setsid python3 "$PV2" "$SER" "$SER_SHA" "$W" 40 "$OUT/${TAG}_pub.jsonl" 20 > "$OUT/${TAG}_pub.out" 2>&1 & PP=$!;;
esac
python3 "$ROOT/results/WK4/tools/wk4_zaciecia.py" live "$W" "$SECS" "$OUT/${TAG}_clock.jsonl"
[ -n "$PP" ] && { kill -TERM -"$PP" 2>/dev/null; sleep 1; kill -9 -"$PP" 2>/dev/null; }
kill -9 -"$GZ" 2>/dev/null; sleep 1
python3 "$ROOT/results/WK4/tools/wk4_zaciecia.py" analiza "$OUT/${TAG}_clock.jsonl" > "$OUT/${TAG}_zaciecia.json"
python3 -c "import json;r=json.load(open('$OUT/${TAG}_zaciecia.json'));print('$TAG', 'zaciecia',r['n'],'suma',r['suma_wall_s'],'odstepy',r['odstepy_t_sim'][:5],'t',[z['t_sim'] for z in r['zaciecia']][:5],'rtf',r['dsim_dwall'],'sim',r['sim_total_s'])"
