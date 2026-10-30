#!/usr/bin/env bash
# results/WK3/tools/wk3_boot.sh — driver bootu nogi WK-III „porywy" (PRE_WK3 §2, PROMPT_WK3_S1 §1.1). KOPIA
# results/WK2/tools/wk2_boot.sh (cf0959ef, nietknięty) ze zmianami WYŁĄCZNIE: (D1) lista światów = world_wk3_p1 /
# world_wk3_p2 z pełnym sha (inny świat ⇒ ODMOWA), (D2) katalog wyjścia results/WK3/booty (REPO-2),
# (D3) komunikaty. Piny, profil, sonda, blok manifestu nietknięte.
# --- nagłówek kopii (wk2_boot.sh) ---
# results/WK2/tools/wk2_boot.sh — driver bootu nogi WK-II (PRE_WK2 §2, PROMPT_WK2_S1). KOPIA
# results/WK/tools/wk_boot.sh (ecf8071c, nietknięty) ze zmianami WYŁĄCZNIE: (D1) lista światów = światy
# WK2 z zaszytymi sha (G: s=0.63; S: s=0.46 — wiatrowe S dopisuje się NOWYM plikiem, nie edycją),
# (D2) katalog wyjścia results/WK2/booty (REPO-2, PROMPT_WK2_S1 §0.3). Odchylenie od litery PRE_WK2 §2
# („wk_boot.sh bez zmian") — ten driver odrzuca światy spoza world_wk_* (linie 29-34) i pisze do
# results/WK/ — decyzja Olgi 29.10 (nowy driver), nazwana w RAPORT_WK2_S1.
# --- nagłówek kopii (wk_boot.sh) ---
# results/WK/tools/wk_boot.sh — driver bootu nogi WIATR-KAMERA (PRE_WK §2, PROMPT_WK_S1 §1.3).
# KOPIA results/PERC2/tools/perc2_s2_boot.sh (nietknięty) ze zmianami WYŁĄCZNIE: WORLD=world_wk_*
# (4. argument, sha świata sprawdzana PRZED bootem), prepend GZ_SIM_RESOURCE_PATH na worlds/wind_models
# (kopia x500_base z enable_wind, FREEZE_W), pin x500_base 13c9174d obok pinu mono_cam (rozjazd = STOP),
# blok "wk" (sha świata + piny) w manifeście, katalog wyjścia results/WK/. Reszta = litera oryginału:
# --- nagłówek oryginału ---
#   ścieżki results/PERC2/s2 + log monitora perc2_s2_monitor.log + samowykluczenie procesowe,
#   KIND=perc2 (etykieta finalize), ramię zawsze V2 (test celowany; ramienia B w S2 nie ma),
#   PIN PROWIENIENCJI mono_cam/model.sdf PRZED startem (FREEZE_PERC2_OPS; rozjazd = STOP),
#   GUARD: PERC2_FASTDDS_PROFILE MUSI być ustawiony i mieć sha a68a450b… (remedium S1) — ODMOWA bez,
#   percep+bridge startują PRZED uzbrojeniem (w oknie settle ≥90 s run_boot), z profilem FastDDS
#     (wyłącznie most obrazu + percep; XRCE/PX4 na transportach domyślnych),
#   SONDA KADENCJI przed uzbrojeniem (perc2_sonda LIVE 35 s, próg FROZEN): FAIL ⇒ natychmiastowy
#     kill run_boot PRZED uzbrojeniem (boot się nie uzbraja; remedium i POWTÓRKA = nowy boot;
#     drugi FAIL z rzędu egzekwuje wołający — budżet powtórek środowiskowych ANEKS §3.3),
#   manifest: blok "perc2" (pin, profil, sondy[] preflight) obok bloków fantom/feed_v2 (verbatim).
# Reżim bez zmian: GZ_IP, proc_gate SUSTAINED CLEAN 3×30 s, cooldown ≥300 s, REPO-2, wyłączność,
# CONTROLLER=net_fantom (e435ed7e) + FANTOM_QLOG, FEED=V2, tail -F client_e2e_full.
#
# Użycie: wk3_boot.sh <BOOT_N> <NAZWA_pod_results/WK3/booty> <EP_IDS_csv> <WORLD=world_wk3_p1|world_wk3_p2>
#   np.:  wk3_boot.sh 1 p1_b1 0,1,2,3 world_wk3_p1
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
BN="${1:?BOOT_N}"; NAME="${2:?NAZWA}"; EPIDS="${3:?EP_IDS}"; WORLD="${4:?WORLD}"
OUTDIR="$ROOT/results/WK3/booty/$NAME"
MONLOG="$ROOT/results/WK3/booty/wk3_monitor.log"
B0SP="$ROOT/.b0deps/lib/python3.12/site-packages"
case "$WORLD" in
  world_wk3_p1) WORLD_SHA_EXPECTED="fe96b0965ccce76aa49db44cd1d5200761356a7a1829efc996359a90e69f2105";;
  world_wk3_p2) WORLD_SHA_EXPECTED="e47ef38030c5095d9a5f09e86349a07a2aadda5c7ec2c085d906553dcbb179dc";;
  *) echo "[wk3 $NAME] GUARD: WORLD=$WORLD spoza listy światów WK3 — ODMOWA"; exit 5;;
esac
WIND_SDF="$ROOT/worlds/wind_models/x500_base/model.sdf"
WIND_PIN_EXPECTED="13c9174d4195b730e594d2c9b1de9041492885aaffdb1895bbbe787476b7e214"
MONO=/world/$WORLD/model/x500_mono_cam_0/link/camera_link/sensor/imager/image
MODEL_SDF="$ROOT/PX4-Autopilot/Tools/simulation/gz/models/mono_cam/model.sdf"
PIN_EXPECTED="3354ae1e8bcb99cec143317fce607e460b13a451bc59f1da98e50e5ddd0ee64c"
PROFIL_SHA16_EXPECTED="a68a450b91c2ab51"
mkdir -p "$ROOT/results/WK3/booty"

if [ -n "${AKW_SCAN_DPS:-}" ] || [ -n "${AKW_DWELL_S:-}" ]; then
  echo "[perc2S2 $NAME] GUARD: AKW_SCAN_DPS/AKW_DWELL_S w env — lot bramkowy lata na FROZEN; ODMOWA" | tee -a "$MONLOG"; exit 5
fi
if [ -z "${PERC2_FASTDDS_PROFILE:-}" ] || [ ! -f "$PERC2_FASTDDS_PROFILE" ]; then
  echo "[perc2S2 $NAME] GUARD: PERC2_FASTDDS_PROFILE nieustawiony/nie istnieje — ODMOWA (remedium S1 obowiązkowe)" | tee -a "$MONLOG"; exit 5
fi
PSHA="$(sha256sum "$PERC2_FASTDDS_PROFILE" | cut -c1-16)"
if [ "$PSHA" != "$PROFIL_SHA16_EXPECTED" ]; then
  echo "[perc2S2 $NAME] GUARD: profil FastDDS sha=$PSHA != $PROFIL_SHA16_EXPECTED — ODMOWA" | tee -a "$MONLOG"; exit 5
fi
if [ -f "$OUTDIR/manifest.json" ]; then
  echo "[perc2S2 $NAME] REPO-2: $OUTDIR zawiera manifest.json — ODMOWA bootu" | tee -a "$MONLOG"; exit 4
fi
COLL="$(pgrep -af 'run_boot|gz sim|bin/px4|bench_flight|MicroXRCEAgent|percep_proc' 2>/dev/null | grep -v -e "$$" -e perc2_s2_boot -e pgrep)"
if [ -n "$COLL" ]; then
  echo "[perc2S2 $NAME] ENV-BLOCK: kolizja procesowa — NIE startuję:" | tee -a "$MONLOG"; echo "$COLL" | tee -a "$MONLOG"; exit 3
fi

# PIN PROWIENIENCJI przed czymkolwiek (FREEZE_PERC2_OPS)
PIN_GOT="$(sha256sum "$MODEL_SDF" | cut -d' ' -f1)"
if [ "$PIN_GOT" != "$PIN_EXPECTED" ]; then
  echo "[perc2S2 $NAME] PIN FAIL mono_cam/model.sdf: got=$PIN_GOT want=$PIN_EXPECTED — STOP bootu" | tee -a "$MONLOG"; exit 6
fi
echo "[perc2S2 $NAME] PIN OK model.sdf=$PIN_GOT profil=$PSHA" | tee -a "$MONLOG"
WIND_PIN_GOT="$(sha256sum "$WIND_SDF" | cut -d' ' -f1)"
if [ "$WIND_PIN_GOT" != "$WIND_PIN_EXPECTED" ]; then
  echo "[wk $NAME] PIN FAIL x500_base (wind) model.sdf: got=$WIND_PIN_GOT want=$WIND_PIN_EXPECTED — STOP bootu" | tee -a "$MONLOG"; exit 6
fi
[ -d "$ROOT/worlds/wind_models/x500_base/meshes" ] || { echo "[wk $NAME] brak binariów x500_base/meshes (README) — STOP bootu" | tee -a "$MONLOG"; exit 6; }
WORLD_SHA_GOT="$(sha256sum "$ROOT/worlds/$WORLD.sdf" | cut -d' ' -f1)"
if [ "$WORLD_SHA_GOT" != "$WORLD_SHA_EXPECTED" ]; then
  echo "[wk $NAME] SHA ŚWIATA FAIL $WORLD: got=$WORLD_SHA_GOT want=$WORLD_SHA_EXPECTED — STOP bootu" | tee -a "$MONLOG"; exit 6
fi
echo "[wk $NAME] PIN OK x500_base(wind)=$WIND_PIN_GOT świat $WORLD=$WORLD_SHA_GOT" | tee -a "$MONLOG"

last=$(cat results/.last_boot_end 2>/dev/null || echo 0); now=$(date +%s)
rem=$(( 300 - (now - last) )); [ $rem -lt 0 ] && rem=0
echo "[perc2S2 $NAME $(date +%H:%M:%S)] cooldown ${rem}s" | tee -a "$MONLOG"; sleep $rem

echo "[perc2S2 $NAME $(date +%H:%M:%S)] czekam na SUSTAINED CLEAN (3× co 30s)..." | tee -a "$MONLOG"
streak=0
while [ $streak -lt 3 ]; do
  if python3 harness/proc_gate.py --self $$ > /tmp/pg_perc2s2_$BN.log 2>&1; then
    streak=$((streak+1)); echo "[perc2S2 $NAME $(date +%H:%M:%S)] CLEAN ${streak}/3" >> "$MONLOG"
  else
    streak=0; echo "[perc2S2 $NAME $(date +%H:%M:%S)] brudny: $(head -1 /tmp/pg_perc2s2_$BN.log)" >> "$MONLOG"
  fi
  [ $streak -lt 3 ] && sleep 30
done
echo "[perc2S2 $NAME $(date +%H:%M:%S)] SUSTAINED CLEAN" | tee -a "$MONLOG"

mkdir -p "$OUTDIR"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true
export GZ_IP=127.0.0.1
# prepend modelu z enable_wind (wzór tools/w_launcher.sh:42; gz_env.sh dopisuje stock PO naszym)
export GZ_SIM_RESOURCE_PATH="$ROOT/worlds/wind_models${GZ_SIM_RESOURCE_PATH:+:$GZ_SIM_RESOURCE_PATH}"
echo "GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH" > "$OUTDIR/.gz_resource_path"
echo "GZ_IP=$GZ_IP" > "$OUTDIR/.gz_ip_proof"

SOCK="$OUTDIR/percep.sock"
env FLIGHT=bench CONTROLLER=net_fantom NET_ARM=ncp INTRUDER=1 WORLD=$WORLD FILM=0 KIND=perc2 \
  BOOT_N="$BN" OUTDIR="$OUTDIR" BENCH_EPISODE_IDS="$EPIDS" FANTOM_QLOG="$OUTDIR/fantom_qlog.jsonl" \
  FEED=V2 DETV2_SOCK="$SOCK" DETV2_CLIENT_LOG="$OUTDIR/client_e2e.jsonl" PYTHONPATH="$B0SP" \
  bash harness/run_boot.sh > "${OUTDIR}_launch.log" 2>&1 &
BOOT=$!
echo "[perc2S2 $NAME] run_boot pid=$BOOT eps=$EPIDS (FEED=V2, CONTROLLER=net_fantom)" | tee -a "$MONLOG"
tail -n +1 -F "$OUTDIR/client_e2e.jsonl" > "$OUTDIR/client_e2e_full.jsonl" 2>/dev/null &
TL=$!

# ---- percep + most PRZED uzbrojeniem (okno settle >=90 s), z profilem FastDDS ----
TOP=""
for i in $(seq 1 90); do
  if ! kill -0 "$BOOT" 2>/dev/null; then break; fi
  TOP=$(gz topic -l 2>/dev/null | grep -F "$MONO" | head -1); [ -n "$TOP" ] && break; sleep 1
done
PP=""; BR=""; SONDA_RC=9
if [ -n "$TOP" ]; then
  { echo "MONO=$MONO"; gz topic -l 2>/dev/null; } > "$OUTDIR/topics.txt"
  export FASTRTPS_DEFAULT_PROFILES_FILE="$PERC2_FASTDDS_PROFILE"
  echo "$FASTRTPS_DEFAULT_PROFILES_FILE" > "$OUTDIR/.fastdds_profile"
  setsid nohup ros2 run ros_gz_bridge parameter_bridge "${MONO}@sensor_msgs/msg/Image[gz.msgs.Image" \
    > "$OUTDIR/bridge_v2.log" 2>&1 &
  BR=$!
  setsid nohup env PYTHONPATH="$B0SP:$ROOT:${PYTHONPATH:-}" FASTRTPS_DEFAULT_PROFILES_FILE="$PERC2_FASTDDS_PROFILE" \
    python3 "$ROOT/harness/percep_proc.py" --topic "$MONO" --world $WORLD \
    --sock "$SOCK" --log "$OUTDIR/percep_feed.jsonl" > "$OUTDIR/percep_stdout.log" 2>&1 &
  PP=$!
  echo "[perc2S2 $NAME] PRZED uzbrojeniem: bridge pid=$BR percep pid=$PP — sonda kadencji LIVE 35 s" | tee -a "$MONLOG"
  for i in $(seq 1 30); do [ -s "$OUTDIR/percep_feed.jsonl" ] && break; sleep 1; done
  python3 "$ROOT/results/PERC2/tools/perc2_sonda.py" --feed "$OUTDIR/percep_feed.jsonl" \
    --window 35 --label "preflight_$NAME" --out "$OUTDIR/sonda_preflight.json" >> "$MONLOG" 2>&1
  SONDA_RC=$?
  echo "[perc2S2 $NAME $(date +%H:%M:%S)] sonda preflight rc=$SONDA_RC (0=PASS)" | tee -a "$MONLOG"
  if [ "$SONDA_RC" != "0" ]; then
    echo "[perc2S2 $NAME] SONDA FAIL — boot się NIE uzbraja: kill run_boot PRZED uzbrojeniem" | tee -a "$MONLOG"
    kill -TERM "$BOOT" 2>/dev/null; sleep 5; kill -9 "$BOOT" 2>/dev/null
  fi
else
  echo "[perc2S2 $NAME] topic imagera nie wstał w oknie settle — kill run_boot" | tee -a "$MONLOG"
  kill -TERM "$BOOT" 2>/dev/null; sleep 5; kill -9 "$BOOT" 2>/dev/null
fi

wait "$BOOT"; RC=$?
if [ -n "$PP" ]; then
  kill -TERM -- -"$PP" 2>/dev/null || kill -TERM "$PP" 2>/dev/null
  for i in $(seq 1 10); do kill -0 "$PP" 2>/dev/null || break; sleep 1; done
  kill -9 "$PP" 2>/dev/null
fi
[ -n "$BR" ] && kill -9 "$BR" 2>/dev/null
[ -n "$TL" ] && { sleep 1; kill "$TL" 2>/dev/null; }
pkill -9 -f 'px4_sitl_default/bin/px4' 2>/dev/null; pkill -9 -f 'MicroXRCEAgent' 2>/dev/null
pkill -9 -f 'gz sim' 2>/dev/null; pkill -9 -f 'ruby.*gz' 2>/dev/null
sleep 2; date +%s > results/.last_boot_end
echo "[perc2S2 $NAME $(date +%H:%M:%S)] wrapper rc=$RC sonda_rc=$SONDA_RC" | tee -a "$MONLOG"
tail -2 "${OUTDIR}_launch.log" | tee -a "$MONLOG"

python3 - "$OUTDIR" "$BN" "$SONDA_RC" "$PIN_GOT" "$WORLD" "$WORLD_SHA_GOT" "$WIND_PIN_GOT" <<'PY'
import hashlib, json, os, sys
outdir, bn, sonda_rc, pin = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
wk_world, wk_world_sha, wk_wind_pin = sys.argv[5], sys.argv[6], sys.argv[7]
ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, ROOT)
mp = os.path.join(outdir, "manifest.json")
if not os.path.exists(mp):
    print("[perc2] brak manifest.json (boot nieuzbrojony/ubity) — manifest szkieletowy")
    m = {"kind": "perc2_s2", "boot": int(bn), "armed": False}
else:
    m = json.load(open(mp))
from r03.controllers.net_controller import FREEZE_SHA
def fsha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None
m["net_arm"] = "ncp"; m["weights_sha"] = FREEZE_SHA["ncp"]
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
               "scan_profile_delegata": {"mode": "step_stare", "step_deg": 40.0,
                                         "slew_dps": 60.0, "stare_s": 1.2, "dwell_s": 2.0,
                                         "frozen": "b94cdeae (ANEKS_AKW-2 par.2)"},
               "q_events": qlog}
m["feed_v2"] = {"role": "FEED=V2 AKTYWNY (det_v2 w osobnym procesie percepcji)",
                "det_v2_sha": "775ead150b9937453168538cb97c55f69166e27ddc2d93f71b3710e0e49832ce",
                "percep_feed_sha256": fsha(os.path.join(outdir, "percep_feed.jsonl")),
                "client_e2e_full_sha256": fsha(os.path.join(outdir, "client_e2e_full.jsonl")),
                "nota": "percep+most startowane PRZED uzbrojeniem (sonda preflight; ANEKS_PERC2-1 §3.2)"}
sondy = []
sp = os.path.join(outdir, "sonda_preflight.json")
if os.path.exists(sp):
    sondy.append({"proba": "preflight", "sonda": json.load(open(sp))})
m["perc2"] = {"pin_mono_cam_model_sdf": pin,
              "fastdds_profile": open(os.path.join(outdir, ".fastdds_profile")).read().strip()
                                 if os.path.exists(os.path.join(outdir, ".fastdds_profile")) else None,
              "sonda_preflight_rc": int(sonda_rc), "sondy": sondy,
              "uzbrojony_po_sondzie": int(sonda_rc) == 0}
m["wk"] = {"world": wk_world, "world_sha256": wk_world_sha,
           "pin_x500_base_wind_model_sdf": wk_wind_pin, "pin_mono_cam_model_sdf": pin,
           "gz_resource_path": open(os.path.join(outdir, ".gz_resource_path")).read().strip()
                               if os.path.exists(os.path.join(outdir, ".gz_resource_path")) else None}
json.dump(m, open(mp, "w"), indent=2)
print(f"[perc2] manifest: sonda_rc={sonda_rc} pin={pin[:8]} bloki fantom/feed_v2/perc2 wpisane")
PY
echo "[perc2S2 $NAME] DONE rc=$RC → $OUTDIR" | tee -a "$MONLOG"; exit "$RC"
