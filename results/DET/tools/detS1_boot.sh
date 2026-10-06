#!/usr/bin/env bash
# results/DET/tools/detS1_boot.sh — driver etapowy DOLOTU nogi DET (PRE_DET §2 / PROMPT_DET_S1 §1 T1).
# Baza: results/2A/tools/stageA_boot.sh (S2) z JEDNĄ zmianą funkcjonalną: decymacja zapisu
# klatek USUNIĘTA — shadow_feed_live.py dostaje --frames-hz 1000 (zapis KAŻDEJ przetworzonej
# klatki ~15 Hz; default S2 był 2.0). Zero edycji frozen plików i shadow_feed_live.py.
# Boot SHADOW: lot na FEED=B (default bench_flight verbatim), CONTROLLER=net NET_ARM=ncp;
# bridge + shadow startują PO '"ev": "armed"' (lekcja B5/D). Bridge z CZYSTYM PYTHONPATH
# (lekcja C1 S3 nogi 2A: B0SP globalnie ubija ros2 CLI); B0SP tylko w env shadow-procesu.
# Guardy: REPO-2, pgrep wyłączności, cooldown >=300 s, GZ_IP=127.0.0.1 (habitat 05.10).
#
# Użycie: detS1_boot.sh <BOOT_N> <NAZWA_pod_results/DET/collect> <EP_ID>
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
BN="${1:?BOOT_N}"; NAME="${2:?NAZWA}"; EPID="${3:?EP_ID}"
OUTDIR="$ROOT/results/DET/collect/$NAME"
B0SP="$ROOT/.b0deps/lib/python3.12/site-packages"
WORLD=world_demo_A3

if [ -f "$OUTDIR/manifest.json" ]; then
  echo "[detS1] ODMOWA: $OUTDIR zawiera manifest.json (REPO-2)"; exit 4
fi
COLL="$(pgrep -af 'run_boot|gz sim|bin/px4|bench_flight|MicroXRCEAgent' 2>/dev/null | grep -v -e "$$" -e detS1_boot -e pgrep)"
if [ -n "$COLL" ]; then
  echo "[detS1] ENV-BLOCK: kolizja procesowa — NIE startuję:"; echo "$COLL"; exit 3
fi
last=$(cat results/.last_boot_end 2>/dev/null || echo 0); now=$(date +%s)
rem=$(( 300 - (now - last) )); [ $rem -lt 0 ] && rem=0
echo "[detS1 $NAME] cooldown ${rem}s"; sleep $rem

mkdir -p "$OUTDIR"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true
export GZ_IP=127.0.0.1
echo "GZ_IP=$GZ_IP (habitat 05.10, dowód: results/2A/stageA/diag2_gzip)" > "$OUTDIR/.gz_ip_proof"

env FLIGHT=bench CONTROLLER=net NET_ARM=ncp INTRUDER=1 WORLD=$WORLD FILM=0 KIND=det \
  BOOT_N="$BN" OUTDIR="$OUTDIR" BENCH_EPISODE_IDS="$EPID" \
  bash harness/run_boot.sh > "${OUTDIR}_launch.log" 2>&1 &
BOOT=$!
echo "[detS1 $NAME] run_boot pid=$BOOT ep=$EPID (FEED=B default, SHADOW zrzut PEŁNEJ kadencji po armed)"

ARMED=0
for i in $(seq 1 600); do
  if ! kill -0 "$BOOT" 2>/dev/null; then break; fi
  if grep -q '"ev": "armed"' "$OUTDIR/trace.jsonl" 2>/dev/null; then ARMED=1; break; fi
  sleep 1
done

SH=""; BR=""
if [ "$ARMED" = "1" ]; then
  MONO=/world/$WORLD/model/x500_mono_cam_0/link/camera_link/sensor/imager/image
  { echo "MONO=$MONO"; echo "--- gz topic -l ---"; gz topic -l 2>/dev/null; } > "$OUTDIR/topics.txt"
  setsid nohup ros2 run ros_gz_bridge parameter_bridge "${MONO}@sensor_msgs/msg/Image[gz.msgs.Image" \
    > "$OUTDIR/bridge_shadow.log" 2>&1 &
  BR=$!
  setsid nohup env PYTHONPATH="$B0SP:$ROOT:${PYTHONPATH:-}" \
    python3 "$ROOT/results/2A/tools/shadow_feed_live.py" --topic "$MONO" --world $WORLD \
    --outdir "$OUTDIR" --frames-hz 1000 > "$OUTDIR/shadow_stdout.log" 2>&1 &
  SH=$!
  echo "[detS1 $NAME] SHADOW po armed: bridge pid=$BR shadow pid=$SH frames-hz=1000 (każda klatka)"
  sleep 5; { echo "--- ros2 topic list (po bridge) ---"; ros2 topic list 2>/dev/null; } >> "$OUTDIR/topics.txt"
else
  echo "[detS1 $NAME] armed nie nadszedł — shadow nie startuje" | tee -a "$OUTDIR/shadow_fail.txt"
fi

wait "$BOOT"; RC=$?
if [ -n "$SH" ]; then
  kill -TERM -- -"$SH" 2>/dev/null || kill -TERM "$SH" 2>/dev/null
  for i in $(seq 1 10); do kill -0 "$SH" 2>/dev/null || break; sleep 1; done
  kill -9 "$SH" 2>/dev/null
fi
[ -n "$BR" ] && kill -9 "$BR" 2>/dev/null

# prowieniencja (wzór stageA): net_arm/weights_sha NCP + sekcja shadow z sha ZBIORU klatek
python3 - "$OUTDIR" <<'PY'
import glob, hashlib, json, os, sys
outdir = sys.argv[1]
sys.path.insert(0, "/home/olga/projects/liquidpatrol")
mp = os.path.join(outdir, "manifest.json")
if not os.path.exists(mp):
    print("[detS1] brak manifest.json — pomijam injekcję"); sys.exit(0)
m = json.load(open(mp))
from r03.controllers.net_controller import FREEZE_SHA
m["net_arm"] = "ncp"; m["weights_sha"] = FREEZE_SHA["ncp"]
frames = sorted(glob.glob(os.path.join(outdir, "frames", "*.jpg")))
h = hashlib.sha256()
for fp in frames:
    h.update((os.path.basename(fp) + " " + hashlib.sha256(open(fp, "rb").read()).hexdigest() + "\n").encode())
sf = os.path.join(outdir, "shadow_feed.jsonl")
m["shadow"] = {"role": "SHADOW zrzut korpusu DET (kontrolera nie karmi; lot na FEED=B)",
               "det_hz": None, "frames_hz": 1000.0,
               "n_frames_jpg": len(frames), "frames_set_sha256": h.hexdigest(),
               "shadow_feed_sha256": (hashlib.sha256(open(sf, "rb").read()).hexdigest()
                                      if os.path.exists(sf) else None)}
json.dump(m, open(mp, "w"), indent=2)
print(f"[detS1] manifest: net_arm=ncp weights_sha={m['weights_sha'][:16]} "
      f"frames={len(frames)} set_sha={h.hexdigest()[:16]}")
PY
echo "[detS1 $NAME] DONE rc=$RC → $OUTDIR"; exit "$RC"
