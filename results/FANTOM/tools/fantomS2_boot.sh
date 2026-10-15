#!/usr/bin/env bash
# results/FANTOM/tools/fantomS2_boot.sh — driver bootu KAMPANII S2 (ANEKS_FANTOM-1 §4.3).
# NOWA KOPIA fantomS1_boot.sh (stare narzędzia nietknięte); zmiany WYŁĄCZNIE: nazwa,
# log monitora fantomS2_monitor.log, samowykluczenie procesowe, POPRAWKA kosmetycznego
# printu manifestu (net_akw -> net_fantom; zlecona ANEKS_FANTOM-1 §1b).
# Odziedziczone z fantomS1 (kopii akwS3_boot):
# CONTROLLER=net_fantom, KIND=fantom (etykieta finalize), ścieżki results/FANTOM/camp,
# log monitora fantomS1_monitor.log, samowykluczenie procesowe, env FANTOM_QLOG
# (dziennik diagnostyczny kwarantanny do OUTDIR), blok manifestu "fantom"
# (fantom_scan_sha256 na żywo + parametry K1 + zdarzenia kwarantanny z qlog).
# Profil II FROZEN b94cdeae i kwarantanna K1 e435ed7e w kodzie (zero env funkcjonalnych).
# KOPIA results/DET/tools/detS4_boot.sh (FROZEN, nietknięty) ze zmianami WYŁĄCZNIE:
#   CONTROLLER=net → net_akw (OBA ramiona — PRE_AKW §5: pod FeedB skan nieaktywny ⇒ net_akw≡net,
#     dowód test §3.1 pass-through bajtowy + kontrola pass(B)_new vs 47/48 DET),
#   KIND=det → akw, ścieżki results/DET/camp → results/AKW/camp, log monitora, prefiksy,
#   GUARD: env AKW_SCAN_DPS/AKW_DWELL_S USTAWIONE ⇒ ODMOWA (kampania/smoke = FROZEN 30/2.0),
#   manifest: blok "akw" (controller_sha=sha(akw_scan.py), registry_sha, parametry FROZEN).
# Reżim bez zmian: GZ_IP, proc_gate SUSTAINED CLEAN 3×30 s, cooldown ≥300 s, wyłączność,
# REPO-2; ramię V2: percep+bridge po '"ev": "armed"', tail -F przechwyt client_e2e_full.
#
# Użycie: akwS3_boot.sh <BOOT_N> <NAZWA_pod_results/AKW/camp> <ARM B|V2> <RUNDA> <EP_IDS_csv>
#   np.:  akwS3_boot.sh 5 r1_B B 1 0,1,2,3
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
BN="${1:?BOOT_N}"; NAME="${2:?NAZWA}"; ARM="${3:?ARM}"; RND="${4:?RUNDA}"; EPIDS="${5:?EP_IDS}"
OUTDIR="$ROOT/results/FANTOM/camp/$NAME"
MONLOG="$ROOT/results/FANTOM/camp/fantomS2_monitor.log"
B0SP="$ROOT/.b0deps/lib/python3.12/site-packages"
WORLD=world_demo_A3
MONO=/world/$WORLD/model/x500_mono_cam_0/link/camera_link/sensor/imager/image
mkdir -p "$ROOT/results/FANTOM/camp"

if [ -n "${AKW_SCAN_DPS:-}" ] || [ -n "${AKW_DWELL_S:-}" ]; then
  echo "[fantomS2 $NAME] GUARD: AKW_SCAN_DPS/AKW_DWELL_S w env — lot bramkowy lata na FROZEN; ODMOWA" | tee -a "$MONLOG"; exit 5
fi
if [ -f "$OUTDIR/manifest.json" ]; then
  echo "[fantomS2 $NAME] REPO-2: $OUTDIR zawiera manifest.json — ODMOWA bootu" | tee -a "$MONLOG"; exit 4
fi
COLL="$(pgrep -af 'run_boot|gz sim|bin/px4|bench_flight|MicroXRCEAgent|percep_proc' 2>/dev/null | grep -v -e "$$" -e fantomS2_boot -e fantomS2_campaign -e pgrep)"
if [ -n "$COLL" ]; then
  echo "[fantomS2 $NAME] ENV-BLOCK: kolizja procesowa — NIE startuję:" | tee -a "$MONLOG"; echo "$COLL" | tee -a "$MONLOG"; exit 3
fi

last=$(cat results/.last_boot_end 2>/dev/null || echo 0); now=$(date +%s)
rem=$(( 300 - (now - last) )); [ $rem -lt 0 ] && rem=0
echo "[fantomS2 $NAME $(date +%H:%M:%S)] cooldown ${rem}s" | tee -a "$MONLOG"; sleep $rem

echo "[fantomS2 $NAME $(date +%H:%M:%S)] czekam na SUSTAINED CLEAN (3× co 30s)..." | tee -a "$MONLOG"
streak=0
while [ $streak -lt 3 ]; do
  if python3 harness/proc_gate.py --self $$ > /tmp/pg_fantoms2_$BN.log 2>&1; then
    streak=$((streak+1)); echo "[fantomS2 $NAME $(date +%H:%M:%S)] CLEAN ${streak}/3" >> "$MONLOG"
  else
    streak=0; echo "[fantomS2 $NAME $(date +%H:%M:%S)] brudny: $(head -1 /tmp/pg_fantoms2_$BN.log)" >> "$MONLOG"
  fi
  [ $streak -lt 3 ] && sleep 30
done
echo "[fantomS2 $NAME $(date +%H:%M:%S)] SUSTAINED CLEAN" | tee -a "$MONLOG"

mkdir -p "$OUTDIR"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true
export GZ_IP=127.0.0.1
echo "GZ_IP=$GZ_IP (habitat 05.10)" > "$OUTDIR/.gz_ip_proof"

PP=""; BR=""; TL=""
if [ "$ARM" = "V2" ]; then
  SOCK="$OUTDIR/percep.sock"
  env FLIGHT=bench CONTROLLER=net_fantom NET_ARM=ncp INTRUDER=1 WORLD=$WORLD FILM=0 KIND=fantom \
    BOOT_N="$BN" OUTDIR="$OUTDIR" BENCH_EPISODE_IDS="$EPIDS" FANTOM_QLOG="$OUTDIR/fantom_qlog.jsonl" \
    FEED=V2 DETV2_SOCK="$SOCK" DETV2_CLIENT_LOG="$OUTDIR/client_e2e.jsonl" PYTHONPATH="$B0SP" \
    bash harness/run_boot.sh > "${OUTDIR}_launch.log" 2>&1 &
  BOOT=$!
  echo "[fantomS2 $NAME] run_boot pid=$BOOT eps=$EPIDS (FEED=V2, CONTROLLER=net_fantom, sock=$SOCK)" | tee -a "$MONLOG"
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
    echo "[fantomS2 $NAME] po armed: bridge pid=$BR percep pid=$PP" | tee -a "$MONLOG"
  else
    echo "[fantomS2 $NAME] armed nie nadszedł — percep nie startuje" | tee "$OUTDIR/percep_fail.txt" | tee -a "$MONLOG"
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
  env FLIGHT=bench CONTROLLER=net_fantom NET_ARM=ncp INTRUDER=1 WORLD=$WORLD FILM=0 KIND=fantom \
    BOOT_N="$BN" OUTDIR="$OUTDIR" BENCH_EPISODE_IDS="$EPIDS" FANTOM_QLOG="$OUTDIR/fantom_qlog.jsonl" \
    bash harness/run_boot.sh > "${OUTDIR}_launch.log" 2>&1
  RC=$?
fi
echo "[fantomS2 $NAME $(date +%H:%M:%S)] wrapper rc=$RC" | tee -a "$MONLOG"
tail -2 "${OUTDIR}_launch.log" | tee -a "$MONLOG"

python3 - "$OUTDIR" "$ARM" "$RND" <<'PY'
import hashlib, json, os, sys
outdir, arm, rnd = sys.argv[1], sys.argv[2], sys.argv[3]
ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, ROOT)
mp = os.path.join(outdir, "manifest.json")
if not os.path.exists(mp):
    print("[fantom] brak manifest.json — pomijam injekcję"); sys.exit(0)
m = json.load(open(mp))
from r03.controllers.net_controller import FREEZE_SHA
def fsha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None
m["net_arm"] = "ncp"; m["weights_sha"] = FREEZE_SHA["ncp"]
m["akw_arm"] = arm; m["akw_round"] = int(rnd)
qlog = []
qp = os.path.join(outdir, "fantom_qlog.jsonl")
if os.path.exists(qp):
    for ln in open(qp):
        ln = ln.strip()
        if ln:
            try:
                qlog.append(json.loads(ln))
            except json.JSONDecodeError:
                pass
m["fantom"] = {"controller": "net_fantom",
               "fantom_scan_sha256": fsha(os.path.join(ROOT, "r03/controllers/fantom_scan.py")),
               "akw_scan_sha256": fsha(os.path.join(ROOT, "r03/controllers/akw_scan.py")),
               "registry_sha256": fsha(os.path.join(ROOT, "r03/controllers/__init__.py")),
               "predykat": {"wybor_T2": "K1", "T_q_s": 3.0, "d_jump_m": 5.0,
                            "eps_K2_nieuzyty_s": 0.5, "marker": "reset() per epizod"},
               "scan_profile_delegata": {"mode": "step_stare", "step_deg": 40.0,
                                         "slew_dps": 60.0, "stare_s": 1.2, "dwell_s": 2.0,
                                         "frozen": "b94cdeae (ANEKS_AKW-2 par.2)"},
               "q_events": qlog,
               "nota": "PRE_FANTOM par.1: jedyna zmiana systemu = co konsument robi "
                       "z trackami sprzed startu epizodu; kwarantanna K1 (A/B/C)"}
if arm == "V2":
    m["feed_v2"] = {"role": "FEED=V2 AKTYWNY (det_v2 w osobnym procesie percepcji; noga AKW)",
                    "det_v2_sha": "775ead150b9937453168538cb97c55f69166e27ddc2d93f71b3710e0e49832ce",
                    "percep_feed_sha256": fsha(os.path.join(outdir, "percep_feed.jsonl")),
                    "client_e2e_sha256": fsha(os.path.join(outdir, "client_e2e.jsonl")),
                    "client_e2e_full_sha256": fsha(os.path.join(outdir, "client_e2e_full.jsonl")),
                    "nota_client_log": "klient FROZEN otwiera log 'w' per epizod — client_e2e.jsonl "
                                       "niesie ostatni epizod; pelny przechwyt=client_e2e_full.jsonl (tail -F, driver)",
                    "nota_prowieniencja": "numpy lawki 2.4.4 (B0SP, import r02.mti przez klienta) — jak S4 2A/DET"}
json.dump(m, open(mp, "w"), indent=2)
print(f"[fantom] manifest: net_arm=ncp controller=net_fantom akw_arm={arm} runda={rnd}")
PY
echo "[fantomS2 $NAME] DONE rc=$RC → $OUTDIR" | tee -a "$MONLOG"; exit "$RC"
