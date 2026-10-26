#!/usr/bin/env bash
# results/DEMO_C/tools/democ_boot.sh — driver bootu DEMO-C (PROMPT_DEMO_C §1.3/§2).
# DWUTRYBOWY, kopie reżimów istniejących (zero edycji czegokolwiek):
#   AKT12 — reżim perc2_s2_boot.sh 1:1 (CONTROLLER=net_fantom, FEED=V2, percep+most
#           PRZED uzbrojeniem, sonda-bramka) + FILM=1 + zrzutniki klatek,
#   AKT3  — reżim net/run_k2_boot.sh 1:1 (CONTROLLER=net, FEED emulowany B,
#           K2_INJECT_T) + reżim OPS: percep w trybie SHADOW (osobny proces, sock
#           donikąd — NIE karmi kontrolera; wyłącznie sonda kadencji + dowód) +
#           FILM=1 + zrzutniki. Percepcja w akcie 3 pozostaje EMULOWANA (napis).
# Wspólne (reżim OPS, FREEZE_PERC2_OPS): checklist → PIN model.sdf + world_hash
# PRZED stackiem (rozjazd=STOP) → profil FastDDS dla mostu obrazu, percep ORAZ
# zrzutników → sonda kadencji przed uzbrojeniem (FAIL ⇒ kill PRZED uzbrojeniem;
# powtórka = nowy boot; drugi FAIL egzekwuje wołający). Twarde STOPy po locie
# egzekwuje wołający z manifestu/trace (breach / REFUSE poza oknem denialu).
#
# Użycie: democ_boot.sh <BOOT_N> <NAZWA_pod_results/DEMO_C/booty> <AKT12|AKT3> <EP_IDS_csv> [K2_INJECT_T]
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
BN="${1:?BOOT_N}"; NAME="${2:?NAZWA}"; TRYB="${3:?AKT12|AKT3}"; EPIDS="${4:?EP_IDS}"; INJ="${5:-}"
OUTDIR="$ROOT/results/DEMO_C/booty/$NAME"
MONLOG="$ROOT/results/DEMO_C/booty/democ_monitor.log"
B0SP="$ROOT/.b0deps/lib/python3.12/site-packages"
WORLD=world_demo_A3
MONO=/world/$WORLD/model/x500_mono_cam_0/link/camera_link/sensor/imager/image
MODEL_SDF="$ROOT/PX4-Autopilot/Tools/simulation/gz/models/mono_cam/model.sdf"
PIN_EXPECTED="3354ae1e8bcb99cec143317fce607e460b13a451bc59f1da98e50e5ddd0ee64c"
PROFIL_SHA16="a68a450b91c2ab51"
mkdir -p "$ROOT/results/DEMO_C/booty"

if [ -z "${DEMOC_FASTDDS_PROFILE:-}" ] || [ ! -f "$DEMOC_FASTDDS_PROFILE" ]; then
  echo "[democ $NAME] GUARD: DEMOC_FASTDDS_PROFILE nieustawiony — ODMOWA (reżim OPS obowiązkowy)" | tee -a "$MONLOG"; exit 5
fi
PSHA="$(sha256sum "$DEMOC_FASTDDS_PROFILE" | cut -c1-16)"
[ "$PSHA" != "$PROFIL_SHA16" ] && { echo "[democ $NAME] GUARD: profil sha=$PSHA != $PROFIL_SHA16 — ODMOWA" | tee -a "$MONLOG"; exit 5; }
[ -f "$OUTDIR/manifest.json" ] && { echo "[democ $NAME] REPO-2: manifest istnieje — ODMOWA" | tee -a "$MONLOG"; exit 4; }
COLL="$(pgrep -af 'run_boot|gz sim|bin/px4|bench_flight|MicroXRCEAgent|percep_proc|framedump' 2>/dev/null | grep -v -e "$$" -e democ_boot -e pgrep)"
[ -n "$COLL" ] && { echo "[democ $NAME] ENV-BLOCK kolizja:" | tee -a "$MONLOG"; echo "$COLL" | tee -a "$MONLOG"; exit 3; }

PIN_GOT="$(sha256sum "$MODEL_SDF" | cut -d' ' -f1)"
[ "$PIN_GOT" != "$PIN_EXPECTED" ] && { echo "[democ $NAME] PIN FAIL model.sdf got=$PIN_GOT — STOP" | tee -a "$MONLOG"; exit 6; }
echo "[democ $NAME] PIN OK model.sdf=$PIN_GOT profil=$PSHA tryb=$TRYB eps=$EPIDS inj=${INJ:--}" | tee -a "$MONLOG"

last=$(cat results/.last_boot_end 2>/dev/null || echo 0); now=$(date +%s)
rem=$(( 300 - (now - last) )); [ $rem -lt 0 ] && rem=0
echo "[democ $NAME $(date +%H:%M:%S)] cooldown ${rem}s" | tee -a "$MONLOG"; sleep $rem
streak=0
while [ $streak -lt 3 ]; do
  if python3 harness/proc_gate.py --self $$ > /tmp/pg_democ_$BN.log 2>&1; then streak=$((streak+1));
  else streak=0; echo "[democ $NAME $(date +%H:%M:%S)] brudny: $(head -1 /tmp/pg_democ_$BN.log)" >> "$MONLOG"; fi
  [ $streak -lt 3 ] && sleep 30
done
echo "[democ $NAME $(date +%H:%M:%S)] SUSTAINED CLEAN" | tee -a "$MONLOG"

mkdir -p "$OUTDIR"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true
export GZ_IP=127.0.0.1

SOCK="$OUTDIR/percep.sock"
if [ "$TRYB" = "AKT12" ]; then
  env FLIGHT=bench CONTROLLER=net_fantom NET_ARM=ncp INTRUDER=1 WORLD=$WORLD FILM=1 KIND=democ \
    BOOT_N="$BN" OUTDIR="$OUTDIR" BENCH_EPISODE_IDS="$EPIDS" FANTOM_QLOG="$OUTDIR/fantom_qlog.jsonl" \
    FEED=V2 DETV2_SOCK="$SOCK" DETV2_CLIENT_LOG="$OUTDIR/client_e2e.jsonl" PYTHONPATH="$B0SP" \
    bash harness/run_boot.sh > "${OUTDIR}_launch.log" 2>&1 &
else
  env FLIGHT=bench CONTROLLER=net NET_ARM=ncp INTRUDER=1 WORLD=$WORLD FILM=1 KIND=democ_k2 \
    BOOT_N="$BN" OUTDIR="$OUTDIR" BENCH_EPISODE_IDS="$EPIDS" K2_INJECT_T="${INJ:?AKT3 wymaga K2_INJECT_T}" \
    bash harness/run_boot.sh > "${OUTDIR}_launch.log" 2>&1 &
fi
BOOT=$!
echo "[democ $NAME] run_boot pid=$BOOT" | tee -a "$MONLOG"
TL=""
[ "$TRYB" = "AKT12" ] && { tail -n +1 -F "$OUTDIR/client_e2e.jsonl" > "$OUTDIR/client_e2e_full.jsonl" 2>/dev/null & TL=$!; }

# ---- przed uzbrojeniem: profil → percep (+shadow w AKT3) → zrzutniki → sonda ----
TOP=""
for i in $(seq 1 90); do
  kill -0 "$BOOT" 2>/dev/null || break
  TOP=$(gz topic -l 2>/dev/null | grep -F "$MONO" | head -1); [ -n "$TOP" ] && break; sleep 1
done
PP=""; BR=""; FD=""; WR=""; SONDA_RC=9
if [ -n "$TOP" ]; then
  export FASTRTPS_DEFAULT_PROFILES_FILE="$DEMOC_FASTDDS_PROFILE"
  echo "$FASTRTPS_DEFAULT_PROFILES_FILE" > "$OUTDIR/.fastdds_profile"
  setsid nohup ros2 run ros_gz_bridge parameter_bridge "${MONO}@sensor_msgs/msg/Image[gz.msgs.Image" \
    > "$OUTDIR/bridge_mono.log" 2>&1 &
  BR=$!
  PSOCK="$SOCK"; [ "$TRYB" = "AKT3" ] && PSOCK="$OUTDIR/percep_shadow.sock"   # AKT3: shadow, nie karmi
  setsid nohup env PYTHONPATH="$B0SP:$ROOT:${PYTHONPATH:-}" FASTRTPS_DEFAULT_PROFILES_FILE="$DEMOC_FASTDDS_PROFILE" \
    python3 "$ROOT/harness/percep_proc.py" --topic "$MONO" --world $WORLD \
    --sock "$PSOCK" --log "$OUTDIR/percep_feed.jsonl" > "$OUTDIR/percep_stdout.log" 2>&1 &
  PP=$!
  setsid nohup env FASTRTPS_DEFAULT_PROFILES_FILE="$DEMOC_FASTDDS_PROFILE" \
    python3 "$ROOT/results/DEMO_C/tools/democ_framedump.py" "$MONO" "$OUTDIR/cam" 0 1800 \
    > "$OUTDIR/framedump_cam.log" 2>&1 &
  FD=$!
  FT=""
  for i in $(seq 1 40); do FT=$(cat "$OUTDIR/film_topic.txt" 2>/dev/null | cut -d= -f2); [ -n "$FT" ] && break; sleep 1; done
  if [ -n "$FT" ]; then
    # most filmowy run_boota ma transporty DOMYŚLNE (klatka 2.76 MB gubi się) —
    # podmiana na most z profilem (publisher strona profilu; pomiar D1: world 4.3 fps → fix)
    FBPID=$(pgrep -f "parameter_bridge.*film" | head -1)
    [ -n "$FBPID" ] && { kill -9 "$FBPID" 2>/dev/null; sleep 1; }
    setsid nohup env FASTRTPS_DEFAULT_PROFILES_FILE="$DEMOC_FASTDDS_PROFILE" \
      ros2 run ros_gz_bridge parameter_bridge "${FT}@sensor_msgs/msg/Image[gz.msgs.Image" \
      > "$OUTDIR/bridge_film_profil.log" 2>&1 &
    FBR=$!
    echo "[democ $NAME] most filmowy podmieniony na profilowany pid=$FBR" | tee -a "$MONLOG"
    setsid nohup env FASTRTPS_DEFAULT_PROFILES_FILE="$DEMOC_FASTDDS_PROFILE" \
      python3 "$ROOT/results/DEMO_C/tools/democ_framedump.py" "$FT" "$OUTDIR/world" 10 1800 \
      > "$OUTDIR/framedump_world.log" 2>&1 &
    WR=$!
  fi
  echo "[democ $NAME] przed uzbrojeniem: bridge=$BR percep=$PP($([ "$TRYB" = "AKT3" ] && echo SHADOW || echo FEED)) cam=$FD world=${WR:-brak} — sonda 35 s" | tee -a "$MONLOG"
  for i in $(seq 1 30); do [ -s "$OUTDIR/percep_feed.jsonl" ] && break; sleep 1; done
  python3 "$ROOT/results/PERC2/tools/perc2_sonda.py" --feed "$OUTDIR/percep_feed.jsonl" \
    --window 35 --label "preflight_$NAME" --out "$OUTDIR/sonda_preflight.json" >> "$MONLOG" 2>&1
  SONDA_RC=$?
  echo "[democ $NAME $(date +%H:%M:%S)] sonda preflight rc=$SONDA_RC (0=PASS)" | tee -a "$MONLOG"
  if [ "$SONDA_RC" != "0" ]; then
    echo "[democ $NAME] SONDA FAIL — boot NIE startuje do lotu (kill przed uzbrojeniem)" | tee -a "$MONLOG"
    kill -TERM "$BOOT" 2>/dev/null; sleep 5; kill -9 "$BOOT" 2>/dev/null
  fi
else
  echo "[democ $NAME] topic kamery nie wstał — kill" | tee -a "$MONLOG"
  kill -TERM "$BOOT" 2>/dev/null; sleep 5; kill -9 "$BOOT" 2>/dev/null
fi

wait "$BOOT"; RC=$?
for P in "$PP" "$FD" "$WR"; do
  [ -n "$P" ] && { kill -TERM "$P" 2>/dev/null; }
done
sleep 3
for P in "$PP" "$FD" "$WR"; do [ -n "$P" ] && kill -9 "$P" 2>/dev/null; done
[ -n "$BR" ] && kill -9 "$BR" 2>/dev/null
[ -n "$TL" ] && kill "$TL" 2>/dev/null
pkill -9 -f 'px4_sitl_default/bin/px4' 2>/dev/null; pkill -9 -f 'MicroXRCEAgent' 2>/dev/null
pkill -9 -f 'gz sim' 2>/dev/null; pkill -9 -f 'ruby.*gz' 2>/dev/null
sleep 2; date +%s > results/.last_boot_end
echo "[democ $NAME $(date +%H:%M:%S)] wrapper rc=$RC sonda_rc=$SONDA_RC" | tee -a "$MONLOG"
tail -2 "${OUTDIR}_launch.log" | tee -a "$MONLOG"

python3 - "$OUTDIR" "$TRYB" "$SONDA_RC" "$PIN_GOT" <<'PY'
import json, os, sys
outdir, tryb, src, pin = sys.argv[1:5]
mp = os.path.join(outdir, "manifest.json")
m = json.load(open(mp)) if os.path.exists(mp) else {"kind": "democ", "armed": False}
sondy = []
sp = os.path.join(outdir, "sonda_preflight.json")
if os.path.exists(sp):
    sondy.append({"proba": "preflight", "sonda": json.load(open(sp))})
m["democ"] = {"tryb": tryb, "pin_mono_cam_model_sdf": pin,
              "fastdds_profile": open(os.path.join(outdir, ".fastdds_profile")).read().strip()
                                 if os.path.exists(os.path.join(outdir, ".fastdds_profile")) else None,
              "sonda_preflight_rc": int(src), "sondy": sondy,
              "percepcja": ("FEED=V2 det_v2 (karmi kontroler)" if tryb == "AKT12"
                            else "EMULOWANA (FeedB karmi kontroler); percep wylacznie SHADOW do sondy"),
              "uzbrojony_po_sondzie": int(src) == 0}
json.dump(m, open(mp, "w"), indent=2)
print(f"[democ] manifest: tryb={tryb} sonda_rc={src}")
PY
echo "[democ $NAME] DONE rc=$RC → $OUTDIR" | tee -a "$MONLOG"; exit "$RC"
