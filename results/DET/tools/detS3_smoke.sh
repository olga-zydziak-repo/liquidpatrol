#!/usr/bin/env bash
# results/DET/tools/detS3_smoke.sh — driver SMOKE FEED=V2 (ANEKS_DET-2 §4.4, PRE_DET §6).
# Boot ławki (FROZEN run_boot.sh): FEED=V2 przez rejestr — w procesie ławki tylko cienki
# klient UDS (DETV2_SOCK/DETV2_CLIENT_LOG); PERCEPCJA w OSOBNYM procesie
# (harness/percep_proc.py: det_v2 + rdzen FeedVision read-only + dedykowany egzekutor),
# startowana PO '"ev": "armed"' razem z bridge (lekcja B5/D). Bridge z CZYSTYM PYTHONPATH
# (lekcja C1 S3 2A). B0SP w env run_boot (klient importuje r02.mti przez feed_sha_v2 —
# nota numpy 2.4.4 jak S4 2A). Teardown: SIGTERM percep (flush summary) -> kill; zero sierot.
# Guardy: REPO-2, pgrep wylacznosci, cooldown >=300 s, GZ_IP=127.0.0.1.
#
# Uzycie: detS3_smoke.sh <BOOT_N> <NAZWA_pod_results/DET/smoke> <EP_ID>
#   smoke: detS3_smoke.sh 1 S1_c10_s01 10
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
BN="${1:?BOOT_N}"; NAME="${2:?NAZWA}"; EPID="${3:?EP_ID}"
OUTDIR="$ROOT/results/DET/smoke/$NAME"
B0SP="$ROOT/.b0deps/lib/python3.12/site-packages"
WORLD=world_demo_A3
MONO=/world/$WORLD/model/x500_mono_cam_0/link/camera_link/sensor/imager/image

if [ -f "$OUTDIR/manifest.json" ]; then
  echo "[detS3] ODMOWA: $OUTDIR zawiera manifest.json (REPO-2)"; exit 4
fi
COLL="$(pgrep -af 'run_boot|gz sim|bin/px4|bench_flight|MicroXRCEAgent|percep_proc' 2>/dev/null | grep -v -e "$$" -e detS3_smoke -e pgrep)"
if [ -n "$COLL" ]; then
  echo "[detS3] ENV-BLOCK: kolizja procesowa — NIE startuję:"; echo "$COLL"; exit 3
fi
last=$(cat results/.last_boot_end 2>/dev/null || echo 0); now=$(date +%s)
rem=$(( 300 - (now - last) )); [ $rem -lt 0 ] && rem=0
echo "[detS3 $NAME] cooldown ${rem}s"; sleep $rem

mkdir -p "$OUTDIR"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true
export GZ_IP=127.0.0.1
echo "GZ_IP=$GZ_IP (habitat 05.10)" > "$OUTDIR/.gz_ip_proof"

SOCK="$OUTDIR/percep.sock"

env FLIGHT=bench CONTROLLER=net NET_ARM=ncp INTRUDER=1 WORLD=$WORLD FILM=0 KIND=det \
  BOOT_N="$BN" OUTDIR="$OUTDIR" BENCH_EPISODE_IDS="$EPID" \
  FEED=V2 DETV2_SOCK="$SOCK" DETV2_CLIENT_LOG="$OUTDIR/client_e2e.jsonl" PYTHONPATH="$B0SP" \
  bash harness/run_boot.sh > "${OUTDIR}_launch.log" 2>&1 &
BOOT=$!
echo "[detS3 $NAME] run_boot pid=$BOOT ep=$EPID (FEED=V2, sock=$SOCK)"

ARMED=0
for i in $(seq 1 600); do
  if ! kill -0 "$BOOT" 2>/dev/null; then break; fi
  if grep -q '"ev": "armed"' "$OUTDIR/trace.jsonl" 2>/dev/null; then ARMED=1; break; fi
  sleep 1
done

PP=""; BR=""
if [ "$ARMED" = "1" ]; then
  { echo "MONO=$MONO"; gz topic -l 2>/dev/null; } > "$OUTDIR/topics.txt"
  setsid nohup ros2 run ros_gz_bridge parameter_bridge "${MONO}@sensor_msgs/msg/Image[gz.msgs.Image" \
    > "$OUTDIR/bridge_v2.log" 2>&1 &
  BR=$!
  setsid nohup env PYTHONPATH="$B0SP:$ROOT:${PYTHONPATH:-}" \
    python3 "$ROOT/harness/percep_proc.py" --topic "$MONO" --world $WORLD \
    --sock "$SOCK" --log "$OUTDIR/percep_feed.jsonl" > "$OUTDIR/percep_stdout.log" 2>&1 &
  PP=$!
  echo "[detS3 $NAME] po armed: bridge pid=$BR percep pid=$PP"
else
  echo "[detS3 $NAME] armed nie nadszedł — percep nie startuje" | tee "$OUTDIR/percep_fail.txt"
fi

wait "$BOOT"; RC=$?
if [ -n "$PP" ]; then
  kill -TERM -- -"$PP" 2>/dev/null || kill -TERM "$PP" 2>/dev/null
  for i in $(seq 1 10); do kill -0 "$PP" 2>/dev/null || break; sleep 1; done
  kill -9 "$PP" 2>/dev/null
fi
[ -n "$BR" ] && kill -9 "$BR" 2>/dev/null

python3 - "$OUTDIR" <<'PY'
import hashlib, json, os, sys
outdir = sys.argv[1]
sys.path.insert(0, "/home/olga/projects/liquidpatrol")
mp = os.path.join(outdir, "manifest.json")
if not os.path.exists(mp):
    print("[detS3] brak manifest.json — pomijam injekcję"); sys.exit(0)
m = json.load(open(mp))
from r03.controllers.net_controller import FREEZE_SHA
m["net_arm"] = "ncp"; m["weights_sha"] = FREEZE_SHA["ncp"]
def fsha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None
m["feed_v2"] = {"role": "FEED=V2 AKTYWNY (det_v2 w osobnym procesie percepcji; smoke S3)",
                "det_v2_sha": "775ead150b9937453168538cb97c55f69166e27ddc2d93f71b3710e0e49832ce",
                "percep_feed_sha256": fsha(os.path.join(outdir, "percep_feed.jsonl")),
                "client_e2e_sha256": fsha(os.path.join(outdir, "client_e2e.jsonl")),
                "nota_prowieniencja": "numpy ławki 2.4.4 (B0SP, import r02.mti przez klienta) — jak S4 2A"}
json.dump(m, open(mp, "w"), indent=2)
print(f"[detS3] manifest: net_arm=ncp feed_v2 percep_sha={str(m['feed_v2']['percep_feed_sha256'])[:16]}")
PY
echo "[detS3 $NAME] DONE rc=$RC → $OUTDIR"; exit "$RC"
