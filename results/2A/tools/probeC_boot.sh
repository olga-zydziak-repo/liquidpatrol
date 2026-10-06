#!/usr/bin/env bash
# results/2A/tools/probeC_boot.sh — driver bootu C-SONDY BEZPIECZEŃSTWA (ANEKS_2A-2 §3).
# Różnica vs stageA_boot.sh (S2): FEED=V AKTYWNIE karmi kontroler (rejestr D6, zero edycji
# frozen) — FeedVisionLive żyje W PROCESIE bench_flight (import leniwy feed_registry:28),
# więc .b0deps wchodzi do PYTHONPATH drzewa bootu (precedens: run_boot.sh:173 finalize już
# działa z B0SP; nota prowieniencyjna: numpy w procesie ławki 2.4.4 zamiast 1.26.4).
# Bridge kamery startuje PO '"ev": "armed"' (lekcja B5/D — nie dotykać okna settle/arm);
# make_feed (ładowanie YOLO) dzieje się >=12 s po armed (takeoff sleep), bridge zdąży.
# Strumień offboard w czasie ładowania YOLO podtrzymuje mavsdk_server (re-send ostatniego
# setpointu, proces zewnętrzny) — hover na zerze, nie zerwanie.
# Guardy 1:1 ze stageA_boot.sh: REPO-2, pgrep wyłączności, cooldown >=300 s, GZ_IP habitat.
#
# Użycie: probeC_boot.sh <BOOT_N> <NAZWA_pod_results/2A/probeC> <EP_ID>
#   C1: probeC_boot.sh 1 C1_c11_s01 11        (c11_s01 nominalny, seed 1, CCW)
#   C2: probeC_boot.sh 2 C2_c08_s03 32        (c08_s03, seed 3, CW)
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
BN="${1:?BOOT_N}"; NAME="${2:?NAZWA}"; EPID="${3:?EP_ID}"
OUTDIR="$ROOT/results/2A/probeC/$NAME"
B0SP="$ROOT/.b0deps/lib/python3.12/site-packages"
WORLD=world_demo_A3
MONO=/world/$WORLD/model/x500_mono_cam_0/link/camera_link/sensor/imager/image

# --- REPO-2 guard: istniejący manifest ⇒ ODMOWA ---
if [ -f "$OUTDIR/manifest.json" ]; then
  echo "[probeC] ODMOWA: $OUTDIR zawiera manifest.json (REPO-2)"; exit 4
fi
# --- wyłączność (wzór stageA/liq_launcher): cudzy proces bootowy ⇒ ODMOWA, zero killi ---
COLL="$(pgrep -af 'run_boot|gz sim|bin/px4|bench_flight|MicroXRCEAgent' 2>/dev/null | grep -v -e "$$" -e probeC_boot -e pgrep)"
if [ -n "$COLL" ]; then
  echo "[probeC] ENV-BLOCK: kolizja procesowa — NIE startuję:"; echo "$COLL"; exit 3
fi
# --- cooldown >=300 s ---
last=$(cat results/.last_boot_end 2>/dev/null || echo 0); now=$(date +%s)
rem=$(( 300 - (now - last) )); [ $rem -lt 0 ] && rem=0
echo "[probeC $NAME] cooldown ${rem}s"; sleep $rem

mkdir -p "$OUTDIR"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true

# HABITAT 05.10 (stageA/diag0/1/2): transport gz na loopback dla całego drzewa bootu.
export GZ_IP=127.0.0.1
echo "GZ_IP=$GZ_IP (mitygacja habitat 05.10, dowód: stageA/diag2_gzip)" > "$OUTDIR/.gz_ip_proof"

# --- boot ławki w tle (FROZEN run_boot.sh; FEED=V przez env TYLKO dla drzewa run_boot) ---
# LEKCJA C1 (RAPORT_2A_S3 §2a): globalny `export PYTHONPATH=$B0SP` w driverze ubija ros2 CLI
# (PackageNotFoundError: ros2cli — B0SP maskuje metadata dystrybucji) ⇒ bridge 0 klatek.
# B0SP/FEED idą WYŁĄCZNIE w env inwokacji run_boot; bridge niżej startuje z czystym PYTHONPATH.
env FLIGHT=bench CONTROLLER=net NET_ARM=ncp INTRUDER=1 WORLD=$WORLD FILM=0 KIND=2a \
  BOOT_N="$BN" OUTDIR="$OUTDIR" BENCH_EPISODE_IDS="$EPID" \
  FEED=V FEED_V_TOPIC="$MONO" FEED_V_LOG="$OUTDIR/feed_v.jsonl" PYTHONPATH="$B0SP" \
  bash harness/run_boot.sh > "${OUTDIR}_launch.log" 2>&1 &
BOOT=$!
echo "[probeC $NAME] run_boot pid=$BOOT ep=$EPID (FEED=V AKTYWNY, topic=$MONO)"

# --- czekaj na armed (albo śmierć bootu) — bridge NIE dotyka okna settle/arm ---
ARMED=0
for i in $(seq 1 600); do
  if ! kill -0 "$BOOT" 2>/dev/null; then break; fi
  if grep -q '"ev": "armed"' "$OUTDIR/trace.jsonl" 2>/dev/null; then ARMED=1; break; fi
  sleep 1
done

BR=""
if [ "$ARMED" = "1" ]; then
  { echo "MONO=$MONO"; echo "--- gz topic -l ---"; gz topic -l 2>/dev/null; } > "$OUTDIR/topics.txt"
  setsid nohup ros2 run ros_gz_bridge parameter_bridge "${MONO}@sensor_msgs/msg/Image[gz.msgs.Image" \
    > "$OUTDIR/bridge_feedv.log" 2>&1 &
  BR=$!
  echo "[probeC $NAME] bridge po armed: pid=$BR topic=$MONO"
  sleep 5; { echo "--- ros2 topic list (po bridge) ---"; ros2 topic list 2>/dev/null; } >> "$OUTDIR/topics.txt"
else
  echo "[probeC $NAME] armed nie nadszedł — bridge nie startuje" | tee "$OUTDIR/bridge_fail.txt"
fi

wait "$BOOT"; RC=$?
[ -n "$BR" ] && kill -9 "$BR" 2>/dev/null

# --- prowieniencja do manifestu (wzór stageA): net_arm/weights_sha NCP + sekcja feed_v AKTYWNY ---
PROBE_MONO_TOPIC="$MONO" python3 - "$OUTDIR" <<'PY'
import hashlib, json, os, sys
outdir = sys.argv[1]
sys.path.insert(0, "/home/olga/projects/liquidpatrol")
mp = os.path.join(outdir, "manifest.json")
if not os.path.exists(mp):
    print("[probeC] brak manifest.json — pomijam injekcję"); sys.exit(0)
m = json.load(open(mp))
from r03.controllers.net_controller import FREEZE_SHA
m["net_arm"] = "ncp"; m["weights_sha"] = FREEZE_SHA["ncp"]
fv = os.path.join(outdir, "feed_v.jsonl")
m["feed_v"] = {"role": "FEED=V AKTYWNY (karmi kontroler; C-sonda ANEKS_2A-2 §3)",
               "topic": os.environ.get("PROBE_MONO_TOPIC"),
               "feed_v_jsonl_sha256": (hashlib.sha256(open(fv, "rb").read()).hexdigest()
                                       if os.path.exists(fv) else None),
               "pythonpath_b0sp": True,
               "nota_prowieniencja": "numpy w procesie ławki 2.4.4 (B0SP) zamiast 1.26.4 — "
                                     "wymóg torch in-process; precedens finalize run_boot:173"}
json.dump(m, open(mp, "w"), indent=2)
print(f"[probeC] manifest: net_arm=ncp weights_sha={m['weights_sha'][:16]} "
      f"feed_v_sha={(m['feed_v']['feed_v_jsonl_sha256'] or 'BRAK')[:16]}")
PY
echo "[probeC $NAME] DONE rc=$RC → $OUTDIR"; exit "$RC"
