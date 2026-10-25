#!/usr/bin/env bash
# results/PERC2/tools/perc2_s1_boot.sh — driver BOOTU DIAGNOSTYCZNEGO S1 nogi PERCEPCJA-II
# (PRE_PERC2 §2 / PROMPT_PERC2_S1 §1). KOPIA reżimu fantomS2_boot.sh ograniczona do:
# higiena (REPO-2, kolizja procesowa, cooldown 300 s, proc_gate SUSTAINED CLEAN 3×30 s)
# + PIN PROWIENIENCJI (world_hash wzorem dotychczasowym + sha256 mono_cam/model.sdf —
#   rozjazd = STOP bootu PRZED startem stacka; naprawa luki z RECON_PERC2 §R4)
# + stack: MicroXRCEAgent + PX4 SITL (gz_x500_mono_cam, world_demo_A3, HEADLESS=1)
#   przez run_stack.sh (FROZEN, bez edycji) + most ros_gz_bridge na topiku imagera.
# BEZ bench_flight, BEZ uzbrojenia, BEZ sędziego (S1: diagnostyka kadencji przed
# uzbrojeniem; percep_proc startowany per PRÓBA przez perc2_trial.sh).
# Driver czeka na plik STOP ($OUTDIR/.stop) albo TTL 1800 s, potem sprząta i finalizuje
# manifest (zbiera sonda_*.json / gzhz_*.json / gpu_*.json z prób do pola 1. klasy).
#
# Użycie: perc2_s1_boot.sh <BOOT_N> <NAZWA_pod_results/PERC2/s1>
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
BN="${1:?BOOT_N}"; NAME="${2:?NAZWA}"
OUTDIR="$ROOT/results/PERC2/s1/$NAME"
MONLOG="$ROOT/results/PERC2/s1/perc2_s1_monitor.log"
WORLD=world_demo_A3
MONO=/world/$WORLD/model/x500_mono_cam_0/link/camera_link/sensor/imager/image
MODEL_SDF="$ROOT/PX4-Autopilot/Tools/simulation/gz/models/mono_cam/model.sdf"
PIN_EXPECTED="3354ae1e8bcb99cec143317fce607e460b13a451bc59f1da98e50e5ddd0ee64c"
TTL_S=1800
mkdir -p "$ROOT/results/PERC2/s1"

if [ -f "$OUTDIR/manifest.json" ]; then
  echo "[perc2S1 $NAME] REPO-2: $OUTDIR zawiera manifest.json — ODMOWA bootu" | tee -a "$MONLOG"; exit 4
fi
COLL="$(pgrep -af 'run_boot|gz sim|bin/px4|bench_flight|MicroXRCEAgent|percep_proc' 2>/dev/null | grep -v -e "$$" -e perc2_s1_boot -e pgrep)"
if [ -n "$COLL" ]; then
  echo "[perc2S1 $NAME] ENV-BLOCK: kolizja procesowa — NIE startuję:" | tee -a "$MONLOG"; echo "$COLL" | tee -a "$MONLOG"; exit 3
fi

last=$(cat results/.last_boot_end 2>/dev/null || echo 0); now=$(date +%s)
rem=$(( 300 - (now - last) )); [ $rem -lt 0 ] && rem=0
echo "[perc2S1 $NAME $(date +%H:%M:%S)] cooldown ${rem}s" | tee -a "$MONLOG"; sleep $rem

echo "[perc2S1 $NAME $(date +%H:%M:%S)] czekam na SUSTAINED CLEAN (3× co 30s)..." | tee -a "$MONLOG"
streak=0
while [ $streak -lt 3 ]; do
  if python3 harness/proc_gate.py --self $$ > /tmp/pg_perc2s1_$BN.log 2>&1; then
    streak=$((streak+1)); echo "[perc2S1 $NAME $(date +%H:%M:%S)] CLEAN ${streak}/3" >> "$MONLOG"
  else
    streak=0; echo "[perc2S1 $NAME $(date +%H:%M:%S)] brudny: $(head -1 /tmp/pg_perc2s1_$BN.log)" >> "$MONLOG"
  fi
  [ $streak -lt 3 ] && sleep 30
done
echo "[perc2S1 $NAME $(date +%H:%M:%S)] SUSTAINED CLEAN" | tee -a "$MONLOG"

mkdir -p "$OUTDIR"

# --- PIN PROWIENIENCJI: model.sdf + world_hash (PRZED startem stacka) --------------
PIN_GOT="$(sha256sum "$MODEL_SDF" | cut -d' ' -f1)"
if [ "$PIN_GOT" != "$PIN_EXPECTED" ]; then
  echo "[perc2S1 $NAME] PIN FAIL mono_cam/model.sdf: got=$PIN_GOT want=$PIN_EXPECTED — STOP bootu" | tee "$OUTDIR/pin_fail.txt" | tee -a "$MONLOG"
  exit 6
fi
bash harness/world_hash.sh "$WORLD" "$OUTDIR" >> "$MONLOG" 2>&1 || { echo "[perc2S1 $NAME] world_hash FAIL" | tee -a "$MONLOG"; exit 6; }
echo "[perc2S1 $NAME] PIN OK model.sdf=$PIN_GOT" | tee -a "$MONLOG"

python3 - "$OUTDIR" "$BN" "$NAME" "$PIN_GOT" <<'PYEOF'
import json, sys, time
outdir, bn, name, pin = sys.argv[1:5]
wh = open(f"{outdir}/world_hash.txt").read().strip()
json.dump({"kind": "perc2_s1_diag", "boot": int(bn), "name": name,
           "world": "world_demo_A3", "world_hash": wh,
           "pin_mono_cam_model_sdf": pin,
           "pin_expected": pin, "armed": False, "judge": None,
           "t_start_unix": int(time.time()), "sondy": []},
          open(f"{outdir}/manifest.json", "w"), indent=1)
PYEOF

source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true
export GZ_IP=127.0.0.1
echo "GZ_IP=$GZ_IP" > "$OUTDIR/.gz_ip_proof"
# (remedium C2 — profil FastDDS — eksportowany DOPIERO po starcie stacka, przed mostem:
#  agent XRCE i PX4 mają zostać na transportach domyślnych)

echo "[perc2S1 $NAME $(date +%H:%M:%S)] start stacka (HEADLESS=1)..." | tee -a "$MONLOG"
HEADLESS=1 LOGDIR="$OUTDIR" WORLD="$WORLD" PX4_GZ_WORLD="$WORLD" MODEL=gz_x500_mono_cam \
  bash run_stack.sh > "$OUTDIR/stack.log" 2>&1

TOP=""
for i in $(seq 1 60); do
  TOP=$(gz topic -l 2>/dev/null | grep -F "$MONO" | head -1); [ -n "$TOP" ] && break; sleep 1
done
if [ -z "$TOP" ]; then
  echo "[perc2S1 $NAME] topic imagera nie wstał — STOP" | tee -a "$MONLOG"
else
  { echo "MONO=$MONO"; gz topic -l 2>/dev/null; } > "$OUTDIR/topics.txt"
  # remedium C2 (liga ops): profil transportu FastDDS WYŁĄCZNIE dla mostu obrazu
  # (i prób percep przez perc2_trial.sh) — env PERC2_FASTDDS_PROFILE
  if [ -n "${PERC2_FASTDDS_PROFILE:-}" ]; then
    export FASTRTPS_DEFAULT_PROFILES_FILE="$PERC2_FASTDDS_PROFILE"
    echo "[perc2S1 $NAME] FASTDDS profil mostu: $FASTRTPS_DEFAULT_PROFILES_FILE" | tee -a "$MONLOG"
    echo "$FASTRTPS_DEFAULT_PROFILES_FILE" > "$OUTDIR/.fastdds_profile"
  fi
  setsid nohup ros2 run ros_gz_bridge parameter_bridge "${MONO}@sensor_msgs/msg/Image[gz.msgs.Image" \
    > "$OUTDIR/bridge_v2.log" 2>&1 &
  BR=$!
  echo "[perc2S1 $NAME $(date +%H:%M:%S)] stack up, bridge pid=$BR; czekam na .stop (TTL ${TTL_S}s); próby = perc2_trial.sh" | tee -a "$MONLOG"
  t0=$(date +%s)
  while [ ! -f "$OUTDIR/.stop" ] && [ $(( $(date +%s) - t0 )) -lt $TTL_S ]; do sleep 5; done
  kill -9 "$BR" 2>/dev/null
fi

echo "[perc2S1 $NAME $(date +%H:%M:%S)] sprzątam stack..." | tee -a "$MONLOG"
pkill -9 -f 'percep_proc' 2>/dev/null
pkill -9 -f 'parameter_bridge' 2>/dev/null
pkill -9 -f 'px4_sitl_default/bin/px4' 2>/dev/null
pkill -9 -f 'MicroXRCEAgent' 2>/dev/null
pkill -9 -f 'gz sim' 2>/dev/null; pkill -9 -f 'ruby.*gz' 2>/dev/null
sleep 2
date +%s > results/.last_boot_end

# finalize: sondy/gzhz/gpu z prób do manifestu (pole 1. klasy)
python3 - "$OUTDIR" <<'PYEOF'
import glob, json, os, sys
outdir = sys.argv[1]
m = json.load(open(f"{outdir}/manifest.json"))
sondy = []
for p in sorted(glob.glob(f"{outdir}/sonda_*.json")):
    trial = os.path.basename(p)[6:-5]
    row = {"proba": trial, "sonda": json.load(open(p))}
    for pref in ("gzhz", "gpu", "push"):
        q = f"{outdir}/{pref}_{trial}.json"
        if os.path.exists(q):
            row[pref] = json.load(open(q))
    sondy.append(row)
m["sondy"] = sondy
json.dump(m, open(f"{outdir}/manifest.json", "w"), indent=1)
print(f"[perc2S1] manifest zfinalizowany: {len(sondy)} prob")
PYEOF
echo "[perc2S1 $NAME $(date +%H:%M:%S)] KONIEC bootu" | tee -a "$MONLOG"
