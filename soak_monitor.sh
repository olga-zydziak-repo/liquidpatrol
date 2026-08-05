#!/usr/bin/env bash
# soak_monitor.sh — A2 soak monitor. Zaklada dzialajacy stack (agent+px4+gz+GUI+bridge).
# Loguje zdrowie co 30s przez SOAK_S sekund. Kryterium pada (A5): smierc procesu /
# CaptureCrash / oops / zatrzymanie renderu — NIE bare dxg-22 ani fortify-WARN.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOAK_S="${SOAK_S:-900}"
INT=30
LOG="/tmp/r0_soak/soak_monitor.log"
source "$ROOT/env_gpu.sh" >/dev/null 2>&1

# PID-y kluczowych procesow
P_AGENT=$(pgrep -f "MicroXRCEAgent" | head -1)
P_PX4=$(pgrep -f "px4_sitl_default/bin/px4" | head -1)
P_GZS=$(pgrep -f "gz sim --verbose.*-r -s" | head -1)
P_GZG=$(pgrep -f "gz sim -g" | head -1)
P_BR=$(pgrep -f "lib/ros_gz_bridge/parameter_bridge" | head -1)

# baseline dmesg — liczniki sygnatur pada
base_capture=$(dmesg 2>/dev/null | grep -cE "CaptureCrash")
base_oops=$(dmesg 2>/dev/null | grep -cE "kernel BUG|Oops:| general protection|Kernel panic - not syncing")

echo "[soak] START t0, budzet ${SOAK_S}s. PID agent=$P_AGENT px4=$P_PX4 gzS=$P_GZS gzG=$P_GZG bridge=$P_BR" | tee "$LOG"
echo "[soak] baseline: CaptureCrash=$base_capture oops=$base_oops" | tee -a "$LOG"

t0=$SECONDS
min_rtf=9.99; max_rtf=0; n=0; sum_rtf=0
verdict="PASS"
while [ $((SECONDS - t0)) -lt "$SOAK_S" ]; do
  el=$((SECONDS - t0))
  # zywotnosc procesow
  dead=""
  for pair in "agent:$P_AGENT" "px4:$P_PX4" "gzS:$P_GZS" "gzG:$P_GZG" "bridge:$P_BR"; do
    nm=${pair%%:*}; pid=${pair##*:}
    if [ -n "$pid" ] && ! kill -0 "$pid" 2>/dev/null; then dead="$dead $nm(pid$pid)"; fi
  done
  # sygnatury pada w dmesg
  cap=$(dmesg 2>/dev/null | grep -cE "CaptureCrash")
  oops=$(dmesg 2>/dev/null | grep -cE "kernel BUG|Oops:| general protection|Kernel panic - not syncing")
  # RTF
  rtf=$(timeout 4 gz topic -e -t /world/default/stats 2>/dev/null | grep -m1 real_time_factor | awk '{print $2}')
  [ -z "$rtf" ] && rtf="NA"
  if [ "$rtf" != "NA" ]; then
    n=$((n+1)); sum_rtf=$(awk -v a="$sum_rtf" -v b="$rtf" 'BEGIN{print a+b}')
    min_rtf=$(awk -v a="$min_rtf" -v b="$rtf" 'BEGIN{print (b<a)?b:a}')
    max_rtf=$(awk -v a="$max_rtf" -v b="$rtf" 'BEGIN{print (b>a)?b:a}')
  fi
  line="[soak] t=${el}s alive_ok=$([ -z "$dead" ] && echo yes || echo NO) RTF=$rtf CaptureCrash=$cap oops=$oops"
  echo "$line" | tee -a "$LOG"
  if [ -n "$dead" ]; then
    echo "[soak] !!! PAD: martwe procesy:$dead — zrzut dmesg" | tee -a "$LOG"
    dmesg 2>/dev/null | tail -40 >> "$LOG"
    verdict="PAD-PROCES"; break
  fi
  if [ "$cap" -gt "$base_capture" ] || [ "$oops" -gt "$base_oops" ]; then
    echo "[soak] !!! PAD: nowy CaptureCrash/oops w dmesg" | tee -a "$LOG"
    dmesg 2>/dev/null | tail -40 >> "$LOG"
    verdict="PAD-DMESG"; break
  fi
  sleep "$INT"
done

avg_rtf=$(awk -v s="$sum_rtf" -v n="$n" 'BEGIN{print (n>0)?s/n:0}')
echo "[soak] KONIEC. elapsed=$((SECONDS - t0))s verdict=$verdict" | tee -a "$LOG"
echo "[soak] RTF: min=$min_rtf max=$max_rtf avg=$avg_rtf (n=$n prob)" | tee -a "$LOG"
echo "[soak] procesy zywe na koniec: $(pgrep -af 'MicroXRCEAgent|px4_sitl_default/bin/px4|gz sim|parameter_bridge' | grep -vE 'grep|snapshot' | wc -l)/5" | tee -a "$LOG"
