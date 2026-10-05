#!/usr/bin/env bash
# results/2A/tools/stageA_boot.sh — driver bootu etapu A nogi 2A (PROMPT_2A_S2 §1).
# Boot ławki przez FROZEN harness/run_boot.sh (FLIGHT=bench, FEED=B default — kontroler NIE widzi
# percepcji, tryb cienia PRE §3) + równolegle bridge kamery i SHADOW FEED-V (shadow_feed_live.py).
# LEKCJA B5/D (acts/run_act_live.sh:50-57, gate_run_r02.py:1089): bridge+YOLO w oknie settle/arm
# = env-fail health ⇒ shadow startuje DOPIERO po '"ev": "armed"' w trace.jsonl.
# Guardy wzorem tools/liq_launcher_stock.sh: REPO-2 (manifest w OUTDIR ⇒ ODMOWA), pgrep wyłączności,
# cooldown ≥300 s z results/.last_boot_end. Zero edycji frozen plików.
#
# Użycie: stageA_boot.sh <BOOT_N> <NAZWA_pod_results/2A/stageA> <EP_ID> [DET_HZ]
#   A1: stageA_boot.sh 1 A1_c08_s03 32        (c08_s03, najgorszy desk f60)
#   A2: stageA_boot.sh 2 A2_c11_s01 11        (c11_s01, nominalny)
#   retry PRE §3 A(ii): ... <EP_ID> 5         (det 5 Hz)
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
BN="${1:?BOOT_N}"; NAME="${2:?NAZWA}"; EPID="${3:?EP_ID}"; DETHZ="${4:-}"
OUTDIR="$ROOT/results/2A/stageA/$NAME"
B0SP="$ROOT/.b0deps/lib/python3.12/site-packages"
WORLD=world_demo_A3

# --- REPO-2 guard: istniejący manifest ⇒ ODMOWA ---
if [ -f "$OUTDIR/manifest.json" ]; then
  echo "[stageA] ODMOWA: $OUTDIR zawiera manifest.json (REPO-2)"; exit 4
fi
# --- wyłączność (wzór liq_launcher §8): cudzy proces bootowy ⇒ ODMOWA, zero killi ---
COLL="$(pgrep -af 'run_boot|gz sim|bin/px4|bench_flight|MicroXRCEAgent' 2>/dev/null | grep -v -e "$$" -e stageA_boot -e pgrep)"
if [ -n "$COLL" ]; then
  echo "[stageA] ENV-BLOCK: kolizja procesowa — NIE startuję:"; echo "$COLL"; exit 3
fi
# --- cooldown ≥300 s ---
last=$(cat results/.last_boot_end 2>/dev/null || echo 0); now=$(date +%s)
rem=$(( 300 - (now - last) )); [ $rem -lt 0 ] && rem=0
echo "[stageA $NAME] cooldown ${rem}s"; sleep $rem

mkdir -p "$OUTDIR"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true

# HABITAT 05.10 (diag0/1/2 w results/2A/stageA): po reboocie hosta (docker br-*/veth UP) pub/sub
# gz-transport do px4 głodował — sensory gz nie wchodziły do uORB (ekf2: 0 eventów, 3× HEALTH
# TIMEOUT pre-arm), choć zewnętrzny CLI je odbierał. Dowód fixu: diag2_gzip ekf2 1473 update'ów.
# Przypięcie transportu do loopback dla CAŁEGO drzewa bootu (stack, bench, bridge, shadow) —
# mitygacja środowiskowa, zero zmian w frozen kodzie/świecie/modelu.
export GZ_IP=127.0.0.1
echo "GZ_IP=$GZ_IP (mitygacja habitat 05.10, dowód: stageA/diag2_gzip)" > "$OUTDIR/.gz_ip_proof"

# --- boot ławki w tle (FROZEN run_boot.sh; FEED nieustawiony = default B verbatim) ---
env FLIGHT=bench CONTROLLER=net NET_ARM=ncp INTRUDER=1 WORLD=$WORLD FILM=0 KIND=2a \
  BOOT_N="$BN" OUTDIR="$OUTDIR" BENCH_EPISODE_IDS="$EPID" \
  bash harness/run_boot.sh > "${OUTDIR}_launch.log" 2>&1 &
BOOT=$!
echo "[stageA $NAME] run_boot pid=$BOOT ep=$EPID (FEED=B default, SHADOW po armed)"

# --- czekaj na armed (albo śmierć bootu) — shadow NIE dotyka okna settle/arm ---
ARMED=0
for i in $(seq 1 600); do
  if ! kill -0 "$BOOT" 2>/dev/null; then break; fi
  if grep -q '"ev": "armed"' "$OUTDIR/trace.jsonl" 2>/dev/null; then ARMED=1; break; fi
  sleep 1
done

SH=""; BR=""
if [ "$ARMED" = "1" ]; then
  MONO=$(gz topic -l 2>/dev/null | grep -E "imager/image$" | head -1)
  { echo "MONO=$MONO"; echo "--- gz topic -l ---"; gz topic -l 2>/dev/null; } > "$OUTDIR/topics.txt"
  if [ -n "$MONO" ]; then
    setsid nohup ros2 run ros_gz_bridge parameter_bridge "${MONO}@sensor_msgs/msg/Image[gz.msgs.Image" \
      > "$OUTDIR/bridge_shadow.log" 2>&1 &
    BR=$!
    DETARG=""; [ -n "$DETHZ" ] && DETARG="--det-hz $DETHZ"
    setsid nohup env PYTHONPATH="$B0SP:$ROOT:${PYTHONPATH:-}" \
      python3 "$ROOT/results/2A/tools/shadow_feed_live.py" --topic "$MONO" --world $WORLD \
      --outdir "$OUTDIR" $DETARG > "$OUTDIR/shadow_stdout.log" 2>&1 &
    SH=$!
    echo "[stageA $NAME] SHADOW po armed: bridge pid=$BR shadow pid=$SH topic=$MONO det_hz=${DETHZ:-full}"
    sleep 5; { echo "--- ros2 topic list (po bridge) ---"; ros2 topic list 2>/dev/null; } >> "$OUTDIR/topics.txt"
  else
    echo "[stageA $NAME] BRAK topicu kamery — shadow nie startuje" | tee "$OUTDIR/shadow_fail.txt"
  fi
else
  echo "[stageA $NAME] armed nie nadszedł — shadow nie startuje" | tee -a "$OUTDIR/shadow_fail.txt"
fi

wait "$BOOT"; RC=$?
# --- zamknij shadow (SIGTERM → flush loga + shadow_summary.json); bridge ubija teardown run_boot ---
if [ -n "$SH" ]; then
  kill -TERM -- -"$SH" 2>/dev/null || kill -TERM "$SH" 2>/dev/null
  for i in $(seq 1 10); do kill -0 "$SH" 2>/dev/null || break; sleep 1; done
  kill -9 "$SH" 2>/dev/null
fi
[ -n "$BR" ] && kill -9 "$BR" 2>/dev/null

# --- prowieniencja do manifestu (wzór net/run_fly_boot.sh): net_arm/weights_sha NCP + sekcja shadow
#     (sha zbioru klatek = sha256 posortowanej listy "nazwa sha256(jpg)") ---
python3 - "$OUTDIR" "$DETHZ" <<'PY'
import glob, hashlib, json, os, sys
outdir, dethz = sys.argv[1], (sys.argv[2] or None)
sys.path.insert(0, "/home/olga/projects/liquidpatrol")
mp = os.path.join(outdir, "manifest.json")
if not os.path.exists(mp):
    print("[stageA] brak manifest.json — pomijam injekcję"); sys.exit(0)
m = json.load(open(mp))
from r03.controllers.net_controller import FREEZE_SHA
m["net_arm"] = "ncp"; m["weights_sha"] = FREEZE_SHA["ncp"]
frames = sorted(glob.glob(os.path.join(outdir, "frames", "*.jpg")))
h = hashlib.sha256()
for fp in frames:
    h.update((os.path.basename(fp) + " " + hashlib.sha256(open(fp, "rb").read()).hexdigest() + "\n").encode())
sf = os.path.join(outdir, "shadow_feed.jsonl")
m["shadow"] = {"role": "SHADOW FEED-V (kontrolera nie karmi; lot na FEED=B)",
               "det_hz": (float(dethz) if dethz else None),
               "n_frames_jpg": len(frames), "frames_set_sha256": h.hexdigest(),
               "shadow_feed_sha256": (hashlib.sha256(open(sf, "rb").read()).hexdigest()
                                      if os.path.exists(sf) else None)}
json.dump(m, open(mp, "w"), indent=2)
print(f"[stageA] manifest: net_arm=ncp weights_sha={m['weights_sha'][:16]} "
      f"frames={len(frames)} set_sha={h.hexdigest()[:16]}")
PY
echo "[stageA $NAME] DONE rc=$RC → $OUTDIR"; exit "$RC"
