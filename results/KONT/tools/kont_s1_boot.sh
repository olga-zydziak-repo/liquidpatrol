#!/usr/bin/env bash
# results/KONT/tools/kont_s1_boot.sh — Boot B/C sondy KONT (PROMPT_KONT_S1 §3): reżim results/SKAN2/tools/skan2_s1_boot.sh
# (REPO-2, kolizja, pin, profil FastDDS, cooldown 300 s, proc_gate 3×30 s, most+percep przed uzbrojeniem, sonda 35 s, zegar2)
# nad harness/kont_boot.sh. FEED=B: percep biegnie tylko po pomiar kadencji (iv), nic go nie czyta w sterowaniu.
# Sonda: bramka S1 = podłoga PRE §4(iv) hz_p50 ≥ 10; werdykt FROZEN perc2_sonda (14.7 Hz) zapisany obok. Pod podłogą boot się nie uzbraja.
# Użycie: PERC2_FASTDDS_PROFILE=<xml> kont_s1_boot.sh <BOOT_N> <NAZWA>
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
BN="${1:?BOOT_N}"; NAME="${2:?NAZWA}"
OUTDIR="$ROOT/results/KONT/s1/$NAME"
MONLOG="$ROOT/results/KONT/s1/kont_s1_monitor.log"
B0SP="$ROOT/.b0deps/lib/python3.12/site-packages"
WORLD=world_kont_A3
MONO=/world/$WORLD/model/x500_mono_cam_flow_0/link/camera_link/sensor/imager/image
MODEL_SDF="$ROOT/PX4-Autopilot/Tools/simulation/gz/models/mono_cam/model.sdf"
PIN_EXPECTED="3354ae1e8bcb99cec143317fce607e460b13a451bc59f1da98e50e5ddd0ee64c"
PROFIL_SHA16_EXPECTED="a68a450b91c2ab51"

[ -f "${PERC2_FASTDDS_PROFILE:-}" ] || { echo "[kont $NAME] GUARD: brak PERC2_FASTDDS_PROFILE" | tee -a "$MONLOG"; exit 5; }
PSHA="$(sha256sum "$PERC2_FASTDDS_PROFILE" | cut -c1-16)"
[ "$PSHA" = "$PROFIL_SHA16_EXPECTED" ] || { echo "[kont $NAME] GUARD: profil sha=$PSHA" | tee -a "$MONLOG"; exit 5; }
[ -f "$OUTDIR/manifest.json" ] && { echo "[kont $NAME] REPO-2: manifest istnieje — ODMOWA" | tee -a "$MONLOG"; exit 4; }
COLL="$(pgrep -af 'run_boot|kont_boot|gz sim|bin/px4|bench_flight|MicroXRCEAgent|percep_proc' 2>/dev/null | grep -v -e "$$" -e kont_s1_boot -e pgrep)"
[ -n "$COLL" ] && { echo "[kont $NAME] ENV-BLOCK: kolizja: $COLL" | tee -a "$MONLOG"; exit 3; }
PIN_GOT="$(sha256sum "$MODEL_SDF" | cut -d' ' -f1)"
[ "$PIN_GOT" = "$PIN_EXPECTED" ] || { echo "[kont $NAME] PIN FAIL $PIN_GOT" | tee -a "$MONLOG"; exit 6; }
echo "[kont $NAME] PIN OK model.sdf=$PIN_GOT profil=$PSHA" | tee -a "$MONLOG"

last=$(cat results/.last_boot_end 2>/dev/null || echo 0); now=$(date +%s)
rem=$(( 300 - (now - last) )); [ $rem -lt 0 ] && rem=0
echo "[kont $NAME $(date +%H:%M:%S)] cooldown ${rem}s" | tee -a "$MONLOG"; sleep $rem
streak=0
while [ $streak -lt 3 ]; do
  if python3 harness/proc_gate.py --self $$ > "/tmp/pg_kont_$BN.log" 2>&1; then streak=$((streak+1)); else streak=0; echo "[kont $NAME] brudny: $(head -1 /tmp/pg_kont_$BN.log)" >> "$MONLOG"; fi
  [ $streak -lt 3 ] && sleep 30
done
echo "[kont $NAME $(date +%H:%M:%S)] SUSTAINED CLEAN" | tee -a "$MONLOG"

mkdir -p "$OUTDIR"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true
export GZ_IP=127.0.0.1
SOCK="$OUTDIR/percep.sock"
python3 "$ROOT/results/SKAN2/tools/skan2_zegar.py" "$OUTDIR/zegar2.jsonl" & ZG=$!
env FLIGHT=kont_probe INTRUDER=1 FILM=0 KIND=kont BOOT_N="$BN" OUTDIR="$OUTDIR" PYTHONPATH="$B0SP" \
  bash harness/kont_boot.sh "$WORLD" > "${OUTDIR}_launch.log" 2>&1 &
BOOT=$!
echo "[kont $NAME] kont_boot pid=$BOOT" | tee -a "$MONLOG"

TOP=""
for i in $(seq 1 90); do
  kill -0 "$BOOT" 2>/dev/null || break
  TOP=$(gz topic -l 2>/dev/null | grep -F "$MONO" | head -1); [ -n "$TOP" ] && break; sleep 1
done
PP=""; BR=""; SONDA_RC=9; ARM_OK=0
if [ -n "$TOP" ]; then
  { echo "MONO=$MONO"; gz topic -l 2>/dev/null; } > "$OUTDIR/topics.txt"
  export FASTRTPS_DEFAULT_PROFILES_FILE="$PERC2_FASTDDS_PROFILE"
  setsid nohup ros2 run ros_gz_bridge parameter_bridge "${MONO}@sensor_msgs/msg/Image[gz.msgs.Image" > "$OUTDIR/bridge_v2.log" 2>&1 &
  BR=$!
  setsid nohup env PYTHONPATH="$B0SP:$ROOT:${PYTHONPATH:-}" FASTRTPS_DEFAULT_PROFILES_FILE="$PERC2_FASTDDS_PROFILE" \
    python3 "$ROOT/harness/percep_proc.py" --topic "$MONO" --world $WORLD --sock "$SOCK" --log "$OUTDIR/percep_feed.jsonl" > "$OUTDIR/percep_stdout.log" 2>&1 &
  PP=$!
  for i in $(seq 1 30); do [ -s "$OUTDIR/percep_feed.jsonl" ] && break; sleep 1; done
  python3 "$ROOT/results/PERC2/tools/perc2_sonda.py" --feed "$OUTDIR/percep_feed.jsonl" --window 35 --label "preflight_$NAME" --out "$OUTDIR/sonda_preflight.json" >> "$MONLOG" 2>&1
  SONDA_RC=$?
  ARM_OK=$(python3 -c "import json;print(int(json.load(open('$OUTDIR/sonda_preflight.json')).get('hz_p50',0)>=10.0))" 2>/dev/null || echo 0)
  echo "[kont $NAME $(date +%H:%M:%S)] sonda rc_FROZEN=$SONDA_RC podloga10Hz=$ARM_OK" | tee -a "$MONLOG"
  if [ "$ARM_OK" != "1" ]; then
    echo "[kont $NAME] POD PODŁOGĄ — boot się NIE uzbraja" | tee -a "$MONLOG"
    pkill -9 -f 'kont_probe' 2>/dev/null; kill -TERM "$BOOT" 2>/dev/null; sleep 5; kill -9 "$BOOT" 2>/dev/null
  fi
else
  echo "[kont $NAME] topic imagera nie wstał — kill" | tee -a "$MONLOG"; kill -TERM "$BOOT" 2>/dev/null; sleep 5; kill -9 "$BOOT" 2>/dev/null
fi
wait "$BOOT"; RC=$?
if [ -n "$PP" ]; then kill -TERM -- -"$PP" 2>/dev/null || kill -TERM "$PP" 2>/dev/null; sleep 5; kill -9 "$PP" 2>/dev/null; fi
[ -n "$BR" ] && kill -9 "$BR" 2>/dev/null
kill -TERM "$ZG" 2>/dev/null
pkill -9 -f 'parameter_bridge' 2>/dev/null; pkill -9 -f 'px4_sitl_default/bin/px4' 2>/dev/null; pkill -9 -f 'MicroXRCEAgent' 2>/dev/null
pkill -9 -f 'gz sim' 2>/dev/null; pkill -9 -f 'ruby.*gz' 2>/dev/null
sleep 2; date +%s > results/.last_boot_end
python3 - "$OUTDIR" "$BN" "$SONDA_RC" "$ARM_OK" "$PIN_GOT" "$PSHA" <<'PY'
import json, os, subprocess, sys
o, bn, rc, arm, pin, psha = sys.argv[1:7]
mp = os.path.join(o, "manifest.json")
m = json.load(open(mp)) if os.path.exists(mp) else {"kind": "kont_probe"}
sp = os.path.join(o, "sonda_preflight.json"); ep = os.path.join(o, "kont_echo.json")
m["kont_s1"] = {"boot": int(bn), "sonda_rc_frozen": int(rc), "podloga_10hz_ok": int(arm), "uzbrojony": int(arm) == 1,
                "sonda": json.load(open(sp)) if os.path.exists(sp) else None, "echo": json.load(open(ep)) if os.path.exists(ep) else None,
                "pin_mono_cam_model_sdf": pin, "fastdds_profil_sha16": psha}
m["zegar"] = {"timesyncd": subprocess.run(["systemctl", "is-active", "systemd-timesyncd"], capture_output=True, text=True).stdout.strip(),
              "clocksource": open("/sys/devices/system/clocksource/clocksource0/current_clocksource").read().strip(), "aneks": "ANEKS_SKAN2-0b §2.2"}
json.dump(m, open(mp, "w"), indent=2, ensure_ascii=False)
PY
echo "[kont $NAME $(date +%H:%M:%S)] DONE rc=$RC sonda=$SONDA_RC" | tee -a "$MONLOG"; exit "$RC"
