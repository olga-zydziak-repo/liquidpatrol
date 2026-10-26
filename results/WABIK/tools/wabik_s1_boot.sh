#!/usr/bin/env bash
# results/WABIK/tools/wabik_s1_boot.sh — driver bootu S1 nogi WABIK (PRE_WABIK §2.3,
# PROMPT_WABIK_S1 §1.2/§1.6). KOPIA reżimu results/PERC2/tools/perc2_s2_boot.sh
# (FROZEN wzorzec; oryginał nietknięty) ze zmianami WYŁĄCZNIE:
#   ścieżki results/WABIK/s1 + log monitora wabik_s1_monitor.log + KIND=wabik,
#   DRUGI SPAWN EntityFactory (name="wabik", ten sam r02/intruder_model.sdf, poza
#     startowa z manifestu WABIK dla zadanej trajektorii) po wstaniu świata,
#   start results/WABIK/tools/wabik_motion.py (pusher wabika; --t0-from-trace),
#   dowód spawnu: gz model --list → wabik_spawn.txt (oba obiekty) → manifest.
# Tor INTRUDER=1 bez zmian (kotwica czystości: intruz = scenariusz historyczny
# z manifestu DOMYŚLNEGO). Reżim OPS: pin model.sdf + world_hash PRZED stackiem,
# profil FastDDS (most obrazu + percep), sonda kadencji przed uzbrojeniem
# (FAIL ⇒ kill przed uzbrojeniem). Smoke UZBROJONY — twarde STOPy egzekwowane
# po locie z manifestu/trace (breach / REFUSE(POS)).
#
# Użycie: wabik_s1_boot.sh <BOOT_N> <NAZWA> <EP_IDS_csv> <TRAJ_ID|-> [BENCH_MANIFEST|-]
#   np.:  wabik_s1_boot.sh 1 s1_smoke 8 W-LOITER -
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
BN="${1:?BOOT_N}"; NAME="${2:?NAZWA}"; EPIDS="${3:?EP_IDS}"; TRAJ="${4:--}"; BMAN="${5:--}"
SDIR="${WABIK_S_DIR:-s1}"
OUTDIR="$ROOT/results/WABIK/$SDIR/$NAME"
MONLOG="$ROOT/results/WABIK/$SDIR/wabik_s1_monitor.log"
B0SP="$ROOT/.b0deps/lib/python3.12/site-packages"
WORLD=world_demo_A3
MONO=/world/$WORLD/model/x500_mono_cam_0/link/camera_link/sensor/imager/image
MODEL_SDF="$ROOT/PX4-Autopilot/Tools/simulation/gz/models/mono_cam/model.sdf"
PIN_EXPECTED="3354ae1e8bcb99cec143317fce607e460b13a451bc59f1da98e50e5ddd0ee64c"
PROFIL_SHA16="a68a450b91c2ab51"
WMAN="$ROOT/results/WABIK/wabik_manifest.json"
mkdir -p "$ROOT/results/WABIK/$SDIR"

if [ -z "${WABIK_FASTDDS_PROFILE:-}" ] || [ ! -f "$WABIK_FASTDDS_PROFILE" ]; then
  echo "[wabikS1 $NAME] GUARD: WABIK_FASTDDS_PROFILE nieustawiony — ODMOWA (reżim OPS)" | tee -a "$MONLOG"; exit 5
fi
PSHA="$(sha256sum "$WABIK_FASTDDS_PROFILE" | cut -c1-16)"
[ "$PSHA" != "$PROFIL_SHA16" ] && { echo "[wabikS1 $NAME] GUARD: profil sha=$PSHA — ODMOWA" | tee -a "$MONLOG"; exit 5; }
[ -f "$OUTDIR/manifest.json" ] && { echo "[wabikS1 $NAME] REPO-2: manifest istnieje — ODMOWA" | tee -a "$MONLOG"; exit 4; }
COLL="$(pgrep -af 'run_boot|gz sim|bin/px4|bench_flight|MicroXRCEAgent|percep_proc|wabik_motion' 2>/dev/null | grep -v -e "$$" -e wabik_s1_boot -e pgrep)"
[ -n "$COLL" ] && { echo "[wabikS1 $NAME] ENV-BLOCK kolizja:" | tee -a "$MONLOG"; echo "$COLL" | tee -a "$MONLOG"; exit 3; }

PIN_GOT="$(sha256sum "$MODEL_SDF" | cut -d' ' -f1)"
[ "$PIN_GOT" != "$PIN_EXPECTED" ] && { echo "[wabikS1 $NAME] PIN FAIL model.sdf — STOP" | tee -a "$MONLOG"; exit 6; }
echo "[wabikS1 $NAME] PIN OK model.sdf=$PIN_GOT profil=$PSHA eps=$EPIDS traj=$TRAJ bman=$BMAN" | tee -a "$MONLOG"

last=$(cat results/.last_boot_end 2>/dev/null || echo 0); now=$(date +%s)
rem=$(( 300 - (now - last) )); [ $rem -lt 0 ] && rem=0
echo "[wabikS1 $NAME $(date +%H:%M:%S)] cooldown ${rem}s" | tee -a "$MONLOG"; sleep $rem
streak=0
while [ $streak -lt 3 ]; do
  if python3 harness/proc_gate.py --self $$ > /tmp/pg_wabik_$BN.log 2>&1; then streak=$((streak+1));
  else streak=0; echo "[wabikS1 $NAME $(date +%H:%M:%S)] brudny: $(head -1 /tmp/pg_wabik_$BN.log)" >> "$MONLOG"; fi
  [ $streak -lt 3 ] && sleep 30
done
echo "[wabikS1 $NAME $(date +%H:%M:%S)] SUSTAINED CLEAN" | tee -a "$MONLOG"

mkdir -p "$OUTDIR"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true
export GZ_IP=127.0.0.1

SOCK="$OUTDIR/percep.sock"
ENVX="FLIGHT=bench CONTROLLER=net_fantom NET_ARM=ncp INTRUDER=1 WORLD=$WORLD FILM=0 KIND=wabik"
[ "$BMAN" != "-" ] && ENVX="$ENVX BENCH_MANIFEST=$BMAN"
env $ENVX BOOT_N="$BN" OUTDIR="$OUTDIR" BENCH_EPISODE_IDS="$EPIDS" \
  FANTOM_QLOG="$OUTDIR/fantom_qlog.jsonl" FEED=V2 DETV2_SOCK="$SOCK" \
  DETV2_CLIENT_LOG="$OUTDIR/client_e2e.jsonl" PYTHONPATH="$B0SP" \
  bash harness/run_boot.sh > "${OUTDIR}_launch.log" 2>&1 &
BOOT=$!
echo "[wabikS1 $NAME] run_boot pid=$BOOT" | tee -a "$MONLOG"
tail -n +1 -F "$OUTDIR/client_e2e.jsonl" > "$OUTDIR/client_e2e_full.jsonl" 2>/dev/null &
TL=$!

TOP=""
for i in $(seq 1 90); do
  kill -0 "$BOOT" 2>/dev/null || break
  TOP=$(gz topic -l 2>/dev/null | grep -F "$MONO" | head -1); [ -n "$TOP" ] && break; sleep 1
done
PP=""; BR=""; WM=""; SONDA_RC=9
if [ -n "$TOP" ]; then
  # ---- DRUGI SPAWN: wabik (EntityFactory; ta sama bryła wizualiów) ----
  if [ "$TRAJ" != "-" ]; then
    WPOSE=$(python3 - "$WMAN" "$TRAJ" <<'PY'
import json, sys
sys.path.insert(0, "/home/olga/projects/liquidpatrol")
from common.frames import ned2drv, drv2gz
man = json.load(open(sys.argv[1])); tr = man["wabik_trajektorie"][sys.argv[2]]
s0 = tr["segments"][0]
gx, gy, gz = drv2gz(ned2drv([s0["x0"], s0["y0"], -tr["z"]]))
print(f"position: {{x: {gx:.2f}, y: {gy:.2f}, z: {gz:.2f}}}")
PY
)
    gz service -s /world/${WORLD}/create --reqtype gz.msgs.EntityFactory --reptype gz.msgs.Boolean --timeout 3000 \
      --req "sdf_filename: \"$ROOT/r02/intruder_model.sdf\", name: \"wabik\", pose: {${WPOSE}}" > "$OUTDIR/wabik_spawn.log" 2>&1
    sleep 2
    gz model --list 2>/dev/null | tee "$OUTDIR/wabik_spawn.txt" | grep -qi 'wabik' \
      && echo "[wabikS1 $NAME] SPAWN wabik OK ($WPOSE)" | tee -a "$MONLOG" \
      || echo "[wabikS1 $NAME] SPAWN wabik FAIL" | tee -a "$MONLOG"
    setsid nohup env PYTHONPATH="$ROOT:${PYTHONPATH:-}" \
      python3 "$ROOT/results/WABIK/tools/wabik_motion.py" --world $WORLD \
      --traj results/WABIK/wabik_manifest.json --traj-id "$TRAJ" \
      --outdir "$OUTDIR" --t0-from-trace > "$OUTDIR/wabik_motion.log" 2>&1 &
    WM=$!
  fi
  export FASTRTPS_DEFAULT_PROFILES_FILE="$WABIK_FASTDDS_PROFILE"
  echo "$FASTRTPS_DEFAULT_PROFILES_FILE" > "$OUTDIR/.fastdds_profile"
  setsid nohup ros2 run ros_gz_bridge parameter_bridge "${MONO}@sensor_msgs/msg/Image[gz.msgs.Image" \
    > "$OUTDIR/bridge_mono.log" 2>&1 &
  BR=$!
  setsid nohup env PYTHONPATH="$B0SP:$ROOT:${PYTHONPATH:-}" FASTRTPS_DEFAULT_PROFILES_FILE="$WABIK_FASTDDS_PROFILE" \
    python3 "$ROOT/harness/percep_proc.py" --topic "$MONO" --world $WORLD \
    --sock "$SOCK" --log "$OUTDIR/percep_feed.jsonl" > "$OUTDIR/percep_stdout.log" 2>&1 &
  PP=$!
  echo "[wabikS1 $NAME] przed uzbrojeniem: bridge=$BR percep=$PP wabik_motion=${WM:-brak} — sonda 35 s" | tee -a "$MONLOG"
  for i in $(seq 1 30); do [ -s "$OUTDIR/percep_feed.jsonl" ] && break; sleep 1; done
  python3 "$ROOT/results/PERC2/tools/perc2_sonda.py" --feed "$OUTDIR/percep_feed.jsonl" \
    --window 35 --label "preflight_$NAME" --out "$OUTDIR/sonda_preflight.json" >> "$MONLOG" 2>&1
  SONDA_RC=$?
  echo "[wabikS1 $NAME $(date +%H:%M:%S)] sonda preflight rc=$SONDA_RC (0=PASS)" | tee -a "$MONLOG"
  if [ "$SONDA_RC" != "0" ]; then
    echo "[wabikS1 $NAME] SONDA FAIL — boot NIE uzbraja się" | tee -a "$MONLOG"
    kill -TERM "$BOOT" 2>/dev/null; sleep 5; kill -9 "$BOOT" 2>/dev/null
  fi
else
  echo "[wabikS1 $NAME] topic kamery nie wstał — kill" | tee -a "$MONLOG"
  kill -TERM "$BOOT" 2>/dev/null; sleep 5; kill -9 "$BOOT" 2>/dev/null
fi

wait "$BOOT"; RC=$?
for P in "$PP" "$WM"; do [ -n "$P" ] && kill -TERM "$P" 2>/dev/null; done
sleep 3
for P in "$PP" "$WM"; do [ -n "$P" ] && kill -9 "$P" 2>/dev/null; done
[ -n "$BR" ] && kill -9 "$BR" 2>/dev/null
[ -n "$TL" ] && kill "$TL" 2>/dev/null
pkill -9 -f 'px4_sitl_default/bin/px4' 2>/dev/null; pkill -9 -f 'MicroXRCEAgent' 2>/dev/null
pkill -9 -f 'gz sim' 2>/dev/null; pkill -9 -f 'ruby.*gz' 2>/dev/null
sleep 2; date +%s > results/.last_boot_end
echo "[wabikS1 $NAME $(date +%H:%M:%S)] wrapper rc=$RC sonda_rc=$SONDA_RC" | tee -a "$MONLOG"
tail -2 "${OUTDIR}_launch.log" | tee -a "$MONLOG"

python3 - "$OUTDIR" "$TRAJ" "$SONDA_RC" "$PIN_GOT" <<'PY'
import json, os, sys
outdir, traj, src, pin = sys.argv[1:5]
mp = os.path.join(outdir, "manifest.json")
m = json.load(open(mp)) if os.path.exists(mp) else {"kind": "wabik_s1", "armed": False}
sondy = []
sp = os.path.join(outdir, "sonda_preflight.json")
if os.path.exists(sp):
    sondy.append({"proba": "preflight", "sonda": json.load(open(sp))})
spawn_txt = ""
st = os.path.join(outdir, "wabik_spawn.txt")
if os.path.exists(st):
    spawn_txt = open(st).read()
m["wabik"] = {"traj_id": traj, "pin_mono_cam_model_sdf": pin,
              "fastdds_profile": open(os.path.join(outdir, ".fastdds_profile")).read().strip()
                                 if os.path.exists(os.path.join(outdir, ".fastdds_profile")) else None,
              "sonda_preflight_rc": int(src), "sondy": sondy,
              "spawn_proof_gz_model_list": spawn_txt.strip().splitlines(),
              "spawn_wabik_ok": ("wabik" in spawn_txt),
              "uzbrojony_po_sondzie": int(src) == 0,
              "nota": "wabik POZA sedzia (gt_intruder tylko intruz); GT wabika = wabik_motion.jsonl"}
json.dump(m, open(mp, "w"), indent=2)
print(f"[wabikS1] manifest: traj={traj} sonda_rc={src} spawn_ok={'wabik' in spawn_txt}")
PY
echo "[wabikS1 $NAME] DONE rc=$RC → $OUTDIR" | tee -a "$MONLOG"; exit "$RC"
