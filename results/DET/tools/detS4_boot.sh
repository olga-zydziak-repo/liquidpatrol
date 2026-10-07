#!/usr/bin/env bash
# results/DET/tools/detS4_boot.sh — driver bootu KAMPANII C nogi DET (ANEKS_DET-3 §3.3).
# Jeden boot = 4 epizody rundy dla JEDNEGO ramienia {B, V2}. Reżim jak dolot/smoke
# (GZ_IP=127.0.0.1, proc_gate SUSTAINED CLEAN 3×30 s, cooldown ≥300 s, wyłączność, REPO-2).
#   ramię B  : env JAK LIQ (FEED default B — zero FEED w env, bajty ścieżki LIQ), KIND=det.
#   ramię V2 : env JAK detS3_smoke.sh VERBATIM (FEED=V2, DETV2_SOCK/CLIENT_LOG, PYTHONPATH=B0SP);
#              percep+bridge startują PO '"ev": "armed"'; teardown SIGTERM→summary; zero sierot.
#              DODATEK driver-side (zero zmian kodu frozen): tail -F przechwytuje client_e2e.jsonl
#              do client_e2e_full.jsonl, bo klient FROZEN otwiera log w trybie "w" PER EPIZOD
#              (4 epizody/boot ⇒ plik źródłowy niesie tylko ostatni epizod — właściwość klienta,
#              odnotowana w raporcie; przechwyt jest czysto odczytowy).
# Manifest 1. klasy post-boot: net_arm/weights_sha (FREEZE_SHA ncp 0337d5ea…), det_arm, det_round;
# dla V2 blok feed_v2 z sha logów percep/klienta (ANEKS_DET-3 §3.3).
#
# Użycie: detS4_boot.sh <BOOT_N> <NAZWA_pod_results/DET/camp> <ARM B|V2> <RUNDA> <EP_IDS_csv>
#   np.:  detS4_boot.sh 14 r1_B B 1 0,1,2,3
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
BN="${1:?BOOT_N}"; NAME="${2:?NAZWA}"; ARM="${3:?ARM}"; RND="${4:?RUNDA}"; EPIDS="${5:?EP_IDS}"
OUTDIR="$ROOT/results/DET/camp/$NAME"
MONLOG="$ROOT/results/DET/camp/detS4_monitor.log"
B0SP="$ROOT/.b0deps/lib/python3.12/site-packages"
WORLD=world_demo_A3
MONO=/world/$WORLD/model/x500_mono_cam_0/link/camera_link/sensor/imager/image
mkdir -p "$ROOT/results/DET/camp"

if [ -f "$OUTDIR/manifest.json" ]; then
  echo "[detS4 $NAME] REPO-2: $OUTDIR zawiera manifest.json — ODMOWA bootu" | tee -a "$MONLOG"; exit 4
fi
COLL="$(pgrep -af 'run_boot|gz sim|bin/px4|bench_flight|MicroXRCEAgent|percep_proc' 2>/dev/null | grep -v -e "$$" -e detS4 -e pgrep)"
if [ -n "$COLL" ]; then
  echo "[detS4 $NAME] ENV-BLOCK: kolizja procesowa — NIE startuję:" | tee -a "$MONLOG"; echo "$COLL" | tee -a "$MONLOG"; exit 3
fi

last=$(cat results/.last_boot_end 2>/dev/null || echo 0); now=$(date +%s)
rem=$(( 300 - (now - last) )); [ $rem -lt 0 ] && rem=0
echo "[detS4 $NAME $(date +%H:%M:%S)] cooldown ${rem}s" | tee -a "$MONLOG"; sleep $rem

echo "[detS4 $NAME $(date +%H:%M:%S)] czekam na SUSTAINED CLEAN (3× co 30s)..." | tee -a "$MONLOG"
streak=0
while [ $streak -lt 3 ]; do
  if python3 harness/proc_gate.py --self $$ > /tmp/pg_det_$BN.log 2>&1; then
    streak=$((streak+1)); echo "[detS4 $NAME $(date +%H:%M:%S)] CLEAN ${streak}/3" >> "$MONLOG"
  else
    streak=0; echo "[detS4 $NAME $(date +%H:%M:%S)] brudny: $(head -1 /tmp/pg_det_$BN.log)" >> "$MONLOG"
  fi
  [ $streak -lt 3 ] && sleep 30
done
echo "[detS4 $NAME $(date +%H:%M:%S)] SUSTAINED CLEAN" | tee -a "$MONLOG"

mkdir -p "$OUTDIR"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true
export GZ_IP=127.0.0.1
echo "GZ_IP=$GZ_IP (habitat 05.10)" > "$OUTDIR/.gz_ip_proof"

PP=""; BR=""; TL=""
if [ "$ARM" = "V2" ]; then
  SOCK="$OUTDIR/percep.sock"
  env FLIGHT=bench CONTROLLER=net NET_ARM=ncp INTRUDER=1 WORLD=$WORLD FILM=0 KIND=det \
    BOOT_N="$BN" OUTDIR="$OUTDIR" BENCH_EPISODE_IDS="$EPIDS" \
    FEED=V2 DETV2_SOCK="$SOCK" DETV2_CLIENT_LOG="$OUTDIR/client_e2e.jsonl" PYTHONPATH="$B0SP" \
    bash harness/run_boot.sh > "${OUTDIR}_launch.log" 2>&1 &
  BOOT=$!
  echo "[detS4 $NAME] run_boot pid=$BOOT eps=$EPIDS (FEED=V2, sock=$SOCK)" | tee -a "$MONLOG"
  tail -n +1 -F "$OUTDIR/client_e2e.jsonl" > "$OUTDIR/client_e2e_full.jsonl" 2>/dev/null &
  TL=$!
  ARMED=0
  for i in $(seq 1 600); do
    if ! kill -0 "$BOOT" 2>/dev/null; then break; fi
    if grep -q '"ev": "armed"' "$OUTDIR/trace.jsonl" 2>/dev/null; then ARMED=1; break; fi
    sleep 1
  done
  if [ "$ARMED" = "1" ]; then
    { echo "MONO=$MONO"; gz topic -l 2>/dev/null; } > "$OUTDIR/topics.txt"
    setsid nohup ros2 run ros_gz_bridge parameter_bridge "${MONO}@sensor_msgs/msg/Image[gz.msgs.Image" \
      > "$OUTDIR/bridge_v2.log" 2>&1 &
    BR=$!
    setsid nohup env PYTHONPATH="$B0SP:$ROOT:${PYTHONPATH:-}" \
      python3 "$ROOT/harness/percep_proc.py" --topic "$MONO" --world $WORLD \
      --sock "$SOCK" --log "$OUTDIR/percep_feed.jsonl" > "$OUTDIR/percep_stdout.log" 2>&1 &
    PP=$!
    echo "[detS4 $NAME] po armed: bridge pid=$BR percep pid=$PP" | tee -a "$MONLOG"
  else
    echo "[detS4 $NAME] armed nie nadszedł — percep nie startuje" | tee "$OUTDIR/percep_fail.txt" | tee -a "$MONLOG"
  fi
  wait "$BOOT"; RC=$?
  if [ -n "$PP" ]; then
    kill -TERM -- -"$PP" 2>/dev/null || kill -TERM "$PP" 2>/dev/null
    for i in $(seq 1 10); do kill -0 "$PP" 2>/dev/null || break; sleep 1; done
    kill -9 "$PP" 2>/dev/null
  fi
  [ -n "$BR" ] && kill -9 "$BR" 2>/dev/null
  [ -n "$TL" ] && { sleep 1; kill "$TL" 2>/dev/null; }
else
  env FLIGHT=bench CONTROLLER=net NET_ARM=ncp INTRUDER=1 WORLD=$WORLD FILM=0 KIND=det \
    BOOT_N="$BN" OUTDIR="$OUTDIR" BENCH_EPISODE_IDS="$EPIDS" \
    bash harness/run_boot.sh > "${OUTDIR}_launch.log" 2>&1
  RC=$?
fi
echo "[detS4 $NAME $(date +%H:%M:%S)] wrapper rc=$RC" | tee -a "$MONLOG"
tail -2 "${OUTDIR}_launch.log" | tee -a "$MONLOG"

python3 - "$OUTDIR" "$ARM" "$RND" <<'PY'
import hashlib, json, os, sys
outdir, arm, rnd = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, "/home/olga/projects/liquidpatrol")
mp = os.path.join(outdir, "manifest.json")
if not os.path.exists(mp):
    print("[detS4] brak manifest.json — pomijam injekcję"); sys.exit(0)
m = json.load(open(mp))
from r03.controllers.net_controller import FREEZE_SHA
m["net_arm"] = "ncp"; m["weights_sha"] = FREEZE_SHA["ncp"]
m["det_arm"] = arm; m["det_round"] = int(rnd)
def fsha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None
if arm == "V2":
    m["feed_v2"] = {"role": "FEED=V2 AKTYWNY (det_v2 w osobnym procesie percepcji; kampania C S4)",
                    "det_v2_sha": "775ead150b9937453168538cb97c55f69166e27ddc2d93f71b3710e0e49832ce",
                    "percep_feed_sha256": fsha(os.path.join(outdir, "percep_feed.jsonl")),
                    "client_e2e_sha256": fsha(os.path.join(outdir, "client_e2e.jsonl")),
                    "client_e2e_full_sha256": fsha(os.path.join(outdir, "client_e2e_full.jsonl")),
                    "nota_client_log": "klient FROZEN otwiera log 'w' per epizod — client_e2e.jsonl "
                                       "niesie ostatni epizod; pelny przechwyt=client_e2e_full.jsonl (tail -F, driver)",
                    "nota_prowieniencja": "numpy ławki 2.4.4 (B0SP, import r02.mti przez klienta) — jak S4 2A"}
json.dump(m, open(mp, "w"), indent=2)
print(f"[detS4] manifest: net_arm=ncp det_arm={arm} runda={rnd}")
PY
echo "[detS4 $NAME] DONE rc=$RC → $OUTDIR" | tee -a "$MONLOG"; exit "$RC"
