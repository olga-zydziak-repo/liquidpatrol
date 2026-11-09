#!/usr/bin/env bash
# results/NADIR/tools/nadir_s2_boot.sh — KOPIA nadir_s1v2_boot.sh (nietknięty), PROMPT_NADIR_S2 §R: zmiany wyłącznie: katalog results/NADIR/s2,
# launcher nadir_s2_launch.sh (FLIGHT=nadir_s2), NADIR_MODE=1 + gniazda ramy B+ (driver rama_drv.sock, percepcja rama_perc.sock — own_pos = p_corr;
# producent nadir_obs wysyła do obu po starcie percepcji), nadir_s2_flight w strażnikach, zamknięcie nadir_obs do 10 s przed SIGKILL
# (§1.6), blok manifestu nadir_s2. Cięcie GNSS z argumentu INJECT_T jak KONT S4 (30 s po t_entry). Nagłówek oryginału:
# results/NADIR/tools/nadir_s1v2_boot.sh — KOPIA nadir_s1_boot.sh (nietknięty), ANEKS_NADIR-1: świat world_nadir2_A3, model x500_nadir2_flow, launcher v2.
# results/NADIR/tools/nadir_s1_boot.sh — KOPIA results/KONT/tools/kont_s4_boot.sh (nietknięty), PROMPT_NADIR_S1 §2: zmiany wyłącznie:
# katalog results/NADIR/s1, świat world_nadir_A3, model x500_nadir_flow_0 (topic imagera), launcher nadir_s1_launch.sh,
# PASYWNY harness/nadir_obs.py (start po moście imagera, stop przed teardown; BEZ .b0deps w PYTHONPATH — OpenCV 4.6.0 systemowe jak b1; NADIR_FLIP=0 — b1: tekstury nielustrzane, obraz odbity daje fałszywe ID). Boot nominalny (INJECT „-”), KONT_MODE=1 jak S4
# (nakładka bez odcięcia = ramię nominalne). Nagłówek oryginału:
# results/KONT/tools/kont_s4_boot.sh — KOPIA kont_s2y_boot.sh (oryginał nietknięty), PROMPT_KONT_S4 §0.2/§1: zmiany wyłącznie:
# katalog results/KONT/s4, FLIGHT=kont_s4 przez kont_s4_launch.sh, env CONTROLLER=net_skan2 NET_ARM=ncp KONT_MODE=1,
# lista epizodów (BENCH_EPISODE_IDS) i KONT_INJECT_T z argumentów (boot nominalny: „-"), blok manifestu kont_s4.
# Użycie: PERC2_FASTDDS_PROFILE=<xml> kont_s4_boot.sh <BOOT_N> <NAZWA> <EPIZODY csv> <INJECT_T|->. Nagłówek oryginału:
# results/KONT/tools/kont_s2y_boot.sh — kopia kont_s2d_boot.sh (oryginał nietknięty), ANEKS_KONT-2b §3.4: launcher harness/kont_boot_s2y.sh, nazwa procesu kont_s2_probe_y. Oryginał: kopia kont_s2_boot.sh (oryginał nietknięty), ANEKS_KONT-1c §3–§5: launcher harness/kont_boot_s2d.sh, odczyt initial absolute time (< 500 000 µs ⇒ boot przerwany przed uzbrojeniem, to nie FAIL sondy), wartości fazy w manifeście, pkill -f zastąpione kont_inw.py. Oryginał: lot S2 (PROMPT_KONT_S2 §S2.2) = kont_s1_boot.sh, zmiany: ścieżki s2, argument EPIZOD, FEED=V2 przez percep_proc (R-4), harness/kont_boot_s2.sh. Oryginał: Boot B/C sondy KONT (PROMPT_KONT_S1 §3): reżim results/SKAN2/tools/skan2_s1_boot.sh
# (REPO-2, kolizja, pin, profil FastDDS, cooldown 300 s, proc_gate 3×30 s, most+percep przed uzbrojeniem, sonda 35 s, zegar2)
# nad harness/kont_boot_s2.sh.
# Sonda: bramka S1 = podłoga PRE §4(iv) hz_p50 ≥ 10; werdykt FROZEN perc2_sonda (14.7 Hz) zapisany obok. Pod podłogą boot się nie uzbraja.
# Użycie: PERC2_FASTDDS_PROFILE=<xml> kont_s2_boot.sh <BOOT_N> <NAZWA> <EPIZOD>
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
BN="${1:?BOOT_N}"; NAME="${2:?NAZWA}"; EPIDS="${3:?EPIZODY}"; INJ="${4:?INJECT_T|-}"
NEP=$(echo "$EPIDS" | tr ',' '\n' | grep -c .)
OUTDIR="$ROOT/results/NADIR/s2/$NAME"
MONLOG="$ROOT/results/NADIR/s2/nadir_s2_monitor.log"
mkdir -p "$ROOT/results/NADIR/s2"
B0SP="$ROOT/.b0deps/lib/python3.12/site-packages"
WORLD=world_nadir2_A3
MONO=/world/$WORLD/model/x500_nadir2_flow_0/link/camera_link/sensor/imager/image
MODEL_SDF="$ROOT/PX4-Autopilot/Tools/simulation/gz/models/mono_cam/model.sdf"
PIN_EXPECTED="3354ae1e8bcb99cec143317fce607e460b13a451bc59f1da98e50e5ddd0ee64c"
PROFIL_SHA16_EXPECTED="a68a450b91c2ab51"

[ -f "${PERC2_FASTDDS_PROFILE:-}" ] || { echo "[kont $NAME] GUARD: brak PERC2_FASTDDS_PROFILE" | tee -a "$MONLOG"; exit 5; }
PSHA="$(sha256sum "$PERC2_FASTDDS_PROFILE" | cut -c1-16)"
[ "$PSHA" = "$PROFIL_SHA16_EXPECTED" ] || { echo "[kont $NAME] GUARD: profil sha=$PSHA" | tee -a "$MONLOG"; exit 5; }
[ -f "$OUTDIR/manifest.json" ] && { echo "[kont $NAME] REPO-2: manifest istnieje — ODMOWA" | tee -a "$MONLOG"; exit 4; }
COLL="$(pgrep -af 'run_boot|kont_boot|kont_s2_campaign_x|gz sim|bin/px4|bench_flight|kont_s4_flight|nadir_s2_flight|MicroXRCEAgent|percep_proc|nadir_obs' 2>/dev/null | grep -v -e "$$" -e kont_s4_boot -e kont_s4_launch -e nadir_s2_boot -e pgrep)"
[ -n "$COLL" ] && { echo "[kont $NAME] ENV-BLOCK: kolizja: $COLL" | tee -a "$MONLOG"; exit 3; }
PIN_GOT="$(sha256sum "$MODEL_SDF" | cut -d' ' -f1)"
[ "$PIN_GOT" = "$PIN_EXPECTED" ] || { echo "[kont $NAME] PIN FAIL $PIN_GOT" | tee -a "$MONLOG"; exit 6; }
echo "[kont $NAME] PIN OK model.sdf=$PIN_GOT profil=$PSHA" | tee -a "$MONLOG"

last=$(cat results/.last_boot_end 2>/dev/null || echo 0); now=$(date +%s)
rem=$(( 300 - (now - last) )); [ $rem -lt 0 ] && rem=0
echo "[kont $NAME $(date +%H:%M:%S)] cooldown ${rem}s" | tee -a "$MONLOG"; sleep $rem
streak=0
while [ $streak -lt 3 ]; do
  if python3 harness/proc_gate.py --self $$ > "/tmp/pg_kont_$BN.log" 2>&1; then streak=$((streak+1)); else streak=0; echo "[kont $NAME] brudny: $(head -1 /tmp/pg_kont_$BN.log)" >> "$MONLOG"; fi
  [ $streak -lt 3 ] && sleep 30
done
echo "[kont $NAME $(date +%H:%M:%S)] SUSTAINED CLEAN" | tee -a "$MONLOG"

mkdir -p "$OUTDIR"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true
export GZ_IP=127.0.0.1
SOCK="$OUTDIR/percep.sock"
RS_DRV="$OUTDIR/rama_drv.sock"; RS_PERC="$OUTDIR/rama_perc.sock"   # PROMPT_NADIR_S2 §1: gniazda ramy B+
python3 "$ROOT/results/SKAN2/tools/skan2_zegar.py" "$OUTDIR/zegar2.jsonl" & ZG=$!
INJ_ENV=""; [ "$INJ" != "-" ] && INJ_ENV="KONT_INJECT_T=$INJ"
env FLIGHT=nadir_s2 NADIR_MODE=1 NADIR_SOCK_DRIVER="$RS_DRV" INTRUDER=1 FILM=0 KIND=kont_s4 BOOT_N="$BN" OUTDIR="$OUTDIR" PYTHONPATH="$B0SP" \
  CONTROLLER=net_skan2 NET_ARM=ncp KONT_MODE=1 BENCH_EPISODE_IDS="$EPIDS" BENCH_EPISODES="$NEP" $INJ_ENV \
  FEED=V2 DETV2_SOCK="$SOCK" DETV2_CLIENT_LOG="$OUTDIR/client_e2e.jsonl" FANTOM_QLOG="$OUTDIR/fantom_qlog.jsonl" \
  bash "$ROOT/results/NADIR/tools/nadir_s2_launch.sh" "$WORLD" > "${OUTDIR}_launch.log" 2>&1 &
BOOT=$!
echo "[kont $NAME] kont_boot pid=$BOOT" | tee -a "$MONLOG"

TOP=""
for i in $(seq 1 90); do
  kill -0 "$BOOT" 2>/dev/null || break
  TOP=$(gz topic -l 2>/dev/null | grep -F "$MONO" | head -1); [ -n "$TOP" ] && break; sleep 1
done
PP=""; NO=""; BR=""; SONDA_RC=9; ARM_OK=0; T0_US=""; FAZA_OK=0
for i in $(seq 1 60); do
  kill -0 "$BOOT" 2>/dev/null || break
  T0_US=$(grep -oE 'initial absolute time to [0-9]+' "$OUTDIR/px4.log" 2>/dev/null | head -1 | awk '{print $NF}'); [ -n "$T0_US" ] && break; sleep 1
done
[ -n "$T0_US" ] && [ "$T0_US" -ge 500000 ] && FAZA_OK=1
echo "[kont $NAME $(date +%H:%M:%S)] initial absolute time ${T0_US:-brak} us faza_ok=$FAZA_OK" | tee -a "$MONLOG"
if [ "$FAZA_OK" != "1" ]; then
  echo "[kont $NAME] FAZA < 500000 us — boot przerwany przed uzbrojeniem" | tee -a "$MONLOG"
  python3 "$ROOT/results/KONT/tools/kont_inw.py" KILL nadir_s2_flight >/dev/null; kill -TERM "$BOOT" 2>/dev/null; sleep 5; kill -9 "$BOOT" 2>/dev/null
elif [ -n "$TOP" ]; then
  { echo "MONO=$MONO"; gz topic -l 2>/dev/null; } > "$OUTDIR/topics.txt"
  export FASTRTPS_DEFAULT_PROFILES_FILE="$PERC2_FASTDDS_PROFILE"
  setsid nohup ros2 run ros_gz_bridge parameter_bridge "${MONO}@sensor_msgs/msg/Image[gz.msgs.Image" > "$OUTDIR/bridge_v2.log" 2>&1 &
  BR=$!
  setsid nohup env NADIR_MODE=1 NADIR_SOCK_PERCEP="$RS_PERC" PYTHONPATH="$B0SP:$ROOT:${PYTHONPATH:-}" FASTRTPS_DEFAULT_PROFILES_FILE="$PERC2_FASTDDS_PROFILE" \
    python3 "$ROOT/harness/percep_proc.py" --topic "$MONO" --world $WORLD --sock "$SOCK" --log "$OUTDIR/percep_feed.jsonl" > "$OUTDIR/percep_stdout.log" 2>&1 &
  PP=$!
  for i in $(seq 1 20); do [ -S "$RS_PERC" ] && break; sleep 1; done
  setsid nohup env NADIR_MODE=1 NADIR_FIX_SOCKS="$RS_DRV:$RS_PERC" NADIR_FLIP=0 PYTHONPATH="$ROOT:${PYTHONPATH:-}" FASTRTPS_DEFAULT_PROFILES_FILE="$PERC2_FASTDDS_PROFILE" \
    python3 "$ROOT/harness/nadir_obs.py" --world $WORLD --model x500_nadir2_flow_0 --out "$OUTDIR/nadir_obs.jsonl" > "$OUTDIR/nadir_obs_stdout.log" 2>&1 &
  NO=$!
  for i in $(seq 1 30); do [ -s "$OUTDIR/percep_feed.jsonl" ] && break; sleep 1; done
  python3 "$ROOT/results/PERC2/tools/perc2_sonda.py" --feed "$OUTDIR/percep_feed.jsonl" --window 35 --label "preflight_$NAME" --out "$OUTDIR/sonda_preflight.json" >> "$MONLOG" 2>&1
  SONDA_RC=$?
  ARM_OK=$(python3 -c "import json;print(int(json.load(open('$OUTDIR/sonda_preflight.json')).get('hz_p50',0)>=10.0))" 2>/dev/null || echo 0)
  echo "[kont $NAME $(date +%H:%M:%S)] sonda rc_FROZEN=$SONDA_RC podloga10Hz=$ARM_OK" | tee -a "$MONLOG"
  if [ "$ARM_OK" != "1" ]; then
    echo "[kont $NAME] POD PODŁOGĄ — boot się NIE uzbraja" | tee -a "$MONLOG"
    python3 "$ROOT/results/KONT/tools/kont_inw.py" KILL nadir_s2_flight >/dev/null; kill -TERM "$BOOT" 2>/dev/null; sleep 5; kill -9 "$BOOT" 2>/dev/null
  fi
else
  echo "[kont $NAME] topic imagera nie wstał — kill" | tee -a "$MONLOG"; kill -TERM "$BOOT" 2>/dev/null; sleep 5; kill -9 "$BOOT" 2>/dev/null
fi
wait "$BOOT"; RC=$?
if [ -n "$NO" ]; then kill -TERM "$NO" 2>/dev/null; for i in $(seq 1 10); do kill -0 "$NO" 2>/dev/null || break; sleep 1; done; kill -9 "$NO" 2>/dev/null; fi   # §1.6: 10 s
if [ -n "$PP" ]; then kill -TERM -- -"$PP" 2>/dev/null || kill -TERM "$PP" 2>/dev/null; sleep 5; kill -9 "$PP" 2>/dev/null; fi
[ -n "$BR" ] && kill -9 "$BR" 2>/dev/null
kill -TERM "$ZG" 2>/dev/null
python3 "$ROOT/results/KONT/tools/kont_inw.py" KILL parameter_bridge px4 MicroXRCEAgent gz >/dev/null
sleep 2; date +%s > results/.last_boot_end
S4_EPIDS="$EPIDS" S4_INJ="$INJ" python3 - "$OUTDIR" "$BN" "$SONDA_RC" "$ARM_OK" "$PIN_GOT" "$PSHA" "${T0_US:-}" "$FAZA_OK" <<'PY'
import json, os, subprocess, sys
o, bn, rc, arm, pin, psha, t0us, faza = sys.argv[1:9]
mp = os.path.join(o, "manifest.json")
m = json.load(open(mp)) if os.path.exists(mp) else {"kind": "kont_probe"}
sp = os.path.join(o, "sonda_preflight.json"); ep = os.path.join(o, "kont_echo.json")
m["nadir_s2"] = {"rama": "B+ NADIR_MODE=1", "socks": ["rama_drv.sock", "rama_perc.sock"]}
m["kont_s4"] = {"boot": int(bn), "epizody": os.environ.get("S4_EPIDS"), "inject_t": os.environ.get("S4_INJ"), "offset": json.load(open(os.path.join(o, "kont_offset.json"))) if os.path.exists(os.path.join(o, "kont_offset.json")) else None, "sonda_rc_frozen": int(rc), "podloga_10hz_ok": int(arm), "uzbrojony": int(arm) == 1,
                "sonda": json.load(open(sp)) if os.path.exists(sp) else None, "echo": json.load(open(ep)) if os.path.exists(ep) else None,
                "pin_mono_cam_model_sdf": pin, "fastdds_profil_sha16": psha}
jp = os.path.join(o, "px4_join.json")
m["kont_s2d"] = {"aneks": "ANEKS_KONT-1c §3", "initial_absolute_time_us": int(t0us) if t0us else None, "faza_ok": faza == "1", "dolaczenie": json.load(open(jp)) if os.path.exists(jp) else None}
m["zegar"] = {"timesyncd": subprocess.run(["systemctl", "is-active", "systemd-timesyncd"], capture_output=True, text=True).stdout.strip(),
              "clocksource": open("/sys/devices/system/clocksource/clocksource0/current_clocksource").read().strip(), "aneks": "ANEKS_SKAN2-0b §2.2"}
json.dump(m, open(mp, "w"), indent=2, ensure_ascii=False)
PY
echo "[kont $NAME $(date +%H:%M:%S)] DONE rc=$RC sonda=$SONDA_RC" | tee -a "$MONLOG"; exit "$RC"
