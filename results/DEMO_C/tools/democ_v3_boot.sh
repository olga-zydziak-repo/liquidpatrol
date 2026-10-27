#!/usr/bin/env bash
# results/DEMO_C/tools/democ_v3_boot.sh — driver bootu AKTU 4 (PROMPT_DEMOC_V3 §1-§2).
# KOPIA wzoru results/WABIK/tools/wabik_s1_boot.sh (reżim OPS + BENCH_MANIFEST;
# oryginał NIETKNIĘTY) ze zmianami DEKLAROWANYMI:
#   katalog results/DEMO_C/s3_wabik (§0.3), KIND=democ_v3, TRAJ zawsze '-' (JEDEN
#   obiekt w świecie — scenariusz wabika grany torem intruza, litera WABIK S2),
#   FILM=1 + zrzutniki klatek democ_framedump (cam pełne / world 10 fps) +
#   podmiana mostu filmowego run_boota na most z profilem (fix zmierzony DEMO-C D1).
# Reżim OPS: pin model.sdf + world_hash PRZED stackiem, profil FastDDS, sonda
# przed uzbrojeniem (FAIL ⇒ kill przed uzbrojeniem). Twarde STOPy po locie
# egzekwuje wołający (breach / REFUSE(POS)).
#
# Użycie: democ_v3_boot.sh <BOOT_N> <NAZWA> <EP_IDS_csv> <BENCH_MANIFEST>
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
BN="${1:?BOOT_N}"; NAME="${2:?NAZWA}"; EPIDS="${3:?EP_IDS}"; BMAN="${4:?BENCH_MANIFEST}"
OUTDIR="$ROOT/results/DEMO_C/s3_wabik/$NAME"
MONLOG="$ROOT/results/DEMO_C/s3_wabik/democ_v3_monitor.log"
B0SP="$ROOT/.b0deps/lib/python3.12/site-packages"
WORLD=world_demo_A3
MONO=/world/$WORLD/model/x500_mono_cam_0/link/camera_link/sensor/imager/image
MODEL_SDF="$ROOT/PX4-Autopilot/Tools/simulation/gz/models/mono_cam/model.sdf"
PIN_EXPECTED="3354ae1e8bcb99cec143317fce607e460b13a451bc59f1da98e50e5ddd0ee64c"
PROFIL_SHA16="a68a450b91c2ab51"
mkdir -p "$ROOT/results/DEMO_C/s3_wabik"

if [ -z "${DEMOC_FASTDDS_PROFILE:-}" ] || [ ! -f "$DEMOC_FASTDDS_PROFILE" ]; then
  echo "[democV3 $NAME] GUARD: DEMOC_FASTDDS_PROFILE nieustawiony — ODMOWA" | tee -a "$MONLOG"; exit 5
fi
PSHA="$(sha256sum "$DEMOC_FASTDDS_PROFILE" | cut -c1-16)"
[ "$PSHA" != "$PROFIL_SHA16" ] && { echo "[democV3 $NAME] GUARD: profil sha=$PSHA — ODMOWA" | tee -a "$MONLOG"; exit 5; }
[ -f "$OUTDIR/manifest.json" ] && { echo "[democV3 $NAME] REPO-2: manifest istnieje — ODMOWA" | tee -a "$MONLOG"; exit 4; }
COLL="$(pgrep -af 'run_boot|gz sim|bin/px4|bench_flight|MicroXRCEAgent|percep_proc|framedump' 2>/dev/null | grep -v -e "$$" -e democ_v3_boot -e pgrep)"
[ -n "$COLL" ] && { echo "[democV3 $NAME] ENV-BLOCK kolizja:" | tee -a "$MONLOG"; echo "$COLL" | tee -a "$MONLOG"; exit 3; }

PIN_GOT="$(sha256sum "$MODEL_SDF" | cut -d' ' -f1)"
[ "$PIN_GOT" != "$PIN_EXPECTED" ] && { echo "[democV3 $NAME] PIN FAIL model.sdf — STOP" | tee -a "$MONLOG"; exit 6; }
echo "[democV3 $NAME] PIN OK profil=$PSHA eps=$EPIDS bman=$BMAN" | tee -a "$MONLOG"

last=$(cat results/.last_boot_end 2>/dev/null || echo 0); now=$(date +%s)
rem=$(( 300 - (now - last) )); [ $rem -lt 0 ] && rem=0
echo "[democV3 $NAME $(date +%H:%M:%S)] cooldown ${rem}s" | tee -a "$MONLOG"; sleep $rem
streak=0
while [ $streak -lt 3 ]; do
  if python3 harness/proc_gate.py --self $$ > /tmp/pg_democv3_$BN.log 2>&1; then streak=$((streak+1));
  else streak=0; echo "[democV3 $NAME $(date +%H:%M:%S)] brudny: $(head -1 /tmp/pg_democv3_$BN.log)" >> "$MONLOG"; fi
  [ $streak -lt 3 ] && sleep 30
done
echo "[democV3 $NAME $(date +%H:%M:%S)] SUSTAINED CLEAN" | tee -a "$MONLOG"

mkdir -p "$OUTDIR"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true
export GZ_IP=127.0.0.1

SOCK="$OUTDIR/percep.sock"
env FLIGHT=bench CONTROLLER=net_fantom NET_ARM=ncp INTRUDER=1 WORLD=$WORLD FILM=1 KIND=democ_v3 \
  BENCH_MANIFEST="$BMAN" BOOT_N="$BN" OUTDIR="$OUTDIR" BENCH_EPISODE_IDS="$EPIDS" \
  FANTOM_QLOG="$OUTDIR/fantom_qlog.jsonl" FEED=V2 DETV2_SOCK="$SOCK" \
  DETV2_CLIENT_LOG="$OUTDIR/client_e2e.jsonl" PYTHONPATH="$B0SP" \
  bash harness/run_boot.sh > "${OUTDIR}_launch.log" 2>&1 &
BOOT=$!
echo "[democV3 $NAME] run_boot pid=$BOOT" | tee -a "$MONLOG"
tail -n +1 -F "$OUTDIR/client_e2e.jsonl" > "$OUTDIR/client_e2e_full.jsonl" 2>/dev/null &
TL=$!

TOP=""
for i in $(seq 1 90); do
  kill -0 "$BOOT" 2>/dev/null || break
  TOP=$(gz topic -l 2>/dev/null | grep -F "$MONO" | head -1); [ -n "$TOP" ] && break; sleep 1
done
PP=""; BR=""; FD=""; WR=""; FBR=""; SONDA_RC=9
if [ -n "$TOP" ]; then
  export FASTRTPS_DEFAULT_PROFILES_FILE="$DEMOC_FASTDDS_PROFILE"
  echo "$FASTRTPS_DEFAULT_PROFILES_FILE" > "$OUTDIR/.fastdds_profile"
  setsid nohup ros2 run ros_gz_bridge parameter_bridge "${MONO}@sensor_msgs/msg/Image[gz.msgs.Image" \
    > "$OUTDIR/bridge_mono.log" 2>&1 &
  BR=$!
  setsid nohup env PYTHONPATH="$B0SP:$ROOT:${PYTHONPATH:-}" FASTRTPS_DEFAULT_PROFILES_FILE="$DEMOC_FASTDDS_PROFILE" \
    python3 "$ROOT/harness/percep_proc.py" --topic "$MONO" --world $WORLD \
    --sock "$SOCK" --log "$OUTDIR/percep_feed.jsonl" > "$OUTDIR/percep_stdout.log" 2>&1 &
  PP=$!
  setsid nohup env FASTRTPS_DEFAULT_PROFILES_FILE="$DEMOC_FASTDDS_PROFILE" \
    python3 "$ROOT/results/DEMO_C/tools/democ_framedump.py" "$MONO" "$OUTDIR/cam" 0 1800 \
    > "$OUTDIR/framedump_cam.log" 2>&1 &
  FD=$!
  FT=""
  for i in $(seq 1 40); do FT=$(cat "$OUTDIR/film_topic.txt" 2>/dev/null | cut -d= -f2); [ -n "$FT" ] && break; sleep 1; done
  if [ -n "$FT" ]; then
    FBPID=$(pgrep -f "parameter_bridge.*film" | head -1)
    [ -n "$FBPID" ] && { kill -9 "$FBPID" 2>/dev/null; sleep 1; }
    setsid nohup env FASTRTPS_DEFAULT_PROFILES_FILE="$DEMOC_FASTDDS_PROFILE" \
      ros2 run ros_gz_bridge parameter_bridge "${FT}@sensor_msgs/msg/Image[gz.msgs.Image" \
      > "$OUTDIR/bridge_film_profil.log" 2>&1 &
    FBR=$!
    setsid nohup env FASTRTPS_DEFAULT_PROFILES_FILE="$DEMOC_FASTDDS_PROFILE" \
      python3 "$ROOT/results/DEMO_C/tools/democ_framedump.py" "$FT" "$OUTDIR/world" 10 1800 \
      > "$OUTDIR/framedump_world.log" 2>&1 &
    WR=$!
  fi
  echo "[democV3 $NAME] przed uzbrojeniem: bridge=$BR percep=$PP cam=$FD world=${WR:-brak} filmbr=${FBR:-brak} — sonda 35 s" | tee -a "$MONLOG"
  for i in $(seq 1 30); do [ -s "$OUTDIR/percep_feed.jsonl" ] && break; sleep 1; done
  python3 "$ROOT/results/PERC2/tools/perc2_sonda.py" --feed "$OUTDIR/percep_feed.jsonl" \
    --window 35 --label "preflight_$NAME" --out "$OUTDIR/sonda_preflight.json" >> "$MONLOG" 2>&1
  SONDA_RC=$?
  echo "[democV3 $NAME $(date +%H:%M:%S)] sonda preflight rc=$SONDA_RC (0=PASS)" | tee -a "$MONLOG"
  if [ "$SONDA_RC" != "0" ]; then
    echo "[democV3 $NAME] SONDA FAIL — boot NIE uzbraja się" | tee -a "$MONLOG"
    kill -TERM "$BOOT" 2>/dev/null; sleep 5; kill -9 "$BOOT" 2>/dev/null
  fi
else
  echo "[democV3 $NAME] topic kamery nie wstał — kill" | tee -a "$MONLOG"
  kill -TERM "$BOOT" 2>/dev/null; sleep 5; kill -9 "$BOOT" 2>/dev/null
fi

wait "$BOOT"; RC=$?
for P in "$PP" "$FD" "$WR"; do [ -n "$P" ] && kill -TERM "$P" 2>/dev/null; done
sleep 3
for P in "$PP" "$FD" "$WR"; do [ -n "$P" ] && kill -9 "$P" 2>/dev/null; done
for P in "$BR" "$FBR" "$TL"; do [ -n "$P" ] && kill -9 "$P" 2>/dev/null; done
pkill -9 -f 'px4_sitl_default/bin/px4' 2>/dev/null; pkill -9 -f 'MicroXRCEAgent' 2>/dev/null
pkill -9 -f 'gz sim' 2>/dev/null; pkill -9 -f 'ruby.*gz' 2>/dev/null
sleep 2; date +%s > results/.last_boot_end
echo "[democV3 $NAME $(date +%H:%M:%S)] wrapper rc=$RC sonda_rc=$SONDA_RC" | tee -a "$MONLOG"
tail -2 "${OUTDIR}_launch.log" | tee -a "$MONLOG"

python3 - "$OUTDIR" "$SONDA_RC" "$PIN_GOT" <<'PY'
import json, os, sys
outdir, src, pin = sys.argv[1:4]
mp = os.path.join(outdir, "manifest.json")
m = json.load(open(mp)) if os.path.exists(mp) else {"kind": "democ_v3", "armed": False}
sondy = []
sp = os.path.join(outdir, "sonda_preflight.json")
if os.path.exists(sp):
    sondy.append({"proba": "preflight", "sonda": json.load(open(sp))})
m["democ_v3"] = {"pin_mono_cam_model_sdf": pin,
                 "fastdds_profile": open(os.path.join(outdir, ".fastdds_profile")).read().strip()
                                    if os.path.exists(os.path.join(outdir, ".fastdds_profile")) else None,
                 "sonda_preflight_rc": int(src), "sondy": sondy,
                 "uzbrojony_po_sondzie": int(src) == 0,
                 "nota": "AKT 4: jeden obiekt w swiecie (scenariusz wabika grany torem intruza, "
                         "litera WABIK S2); klasyfikator wabik_sig v1 475c972e POSTHOC — nie steruje"}
json.dump(m, open(mp, "w"), indent=2)
print(f"[democV3] manifest: sonda_rc={src}")
PY
echo "[democV3 $NAME] DONE rc=$RC → $OUTDIR" | tee -a "$MONLOG"; exit "$RC"
