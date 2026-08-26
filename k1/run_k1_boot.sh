#!/usr/bin/env bash
# k1/run_k1_boot.sh ARM POINT BOOT_N [KIND] — jeden boot K1 (PRE_K1 §2, ridery R1–R5).
#   ARM=S → osłona (gate_run_r03 SCEN=K1, ścieżka R0.3a NIETKNIĘTA, tylko punkt wstrzyknięcia)
#   ARM=N → natywny failsafe (k1_arm_n: EKF2_GPS_CTRL=0 + action.land δ=0, setpointy milkną po acku)
# Boot świeży, headless, 90 s konwergencji EKF, ulog kopiowany do OUTDIR (nigdy /tmp), habitat+sędzia.
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
ARM="${1:?arm N|S}"; POINT="${2:?point 0.2..0.8}"; BOOT_N="${3:-1}"; KIND="${4:-crit}"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source "$ROOT/ros2_ws/install/setup.bash" 2>/dev/null || true
source env_gpu.sh >/dev/null 2>&1 || true
export HEADLESS=1 GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA RENDER_BACKEND="mesa-d3d12"
WORLD="default"
PSTR=$(python3 -c "print(str($POINT).replace('.','_'))")
OUTDIR="$ROOT/results/K1/$ARM/p${PSTR}/boot${BOOT_N}"; mkdir -p "$OUTDIR"
B0SP="$ROOT/.b0deps/lib/python3.12/site-packages"

teardown(){ pkill -9 -f 'gz sim' 2>/dev/null; pkill -9 -f 'px4' 2>/dev/null; pkill -9 -f MicroXRCEAgent 2>/dev/null
  pkill -9 -f mavsdk_server 2>/dev/null; pkill -9 -f 'gate_run_r03' 2>/dev/null; pkill -9 -f 'k1_arm_n' 2>/dev/null
  pkill -9 -f 'rtf_sampler' 2>/dev/null; pkill -9 -f 'ruby.*gz' 2>/dev/null; sleep 2; }

# B4 (ANEKS_K1-5): dowód czystej maszyny (orphany przed teardownem) + cooldown od poprzedniego bootu.
# Cooldown ≥5 min egzekwuje orkiestrator (odstęp między wywołaniami); tu tylko POMIAR do manifestu.
ORPH_PAT='gz sim|px4 |MicroXRCEAgent|mavsdk_server|gate_run_r03|k1_arm_n|rtf_sampler|ruby.*gz'
# pgrep -c drukuje '0' i kończy się kodem 1 przy braku trafień → NIE dokładać '|| echo 0' (dawało "0\n0")
ORPH_PRE=$(pgrep -fc "$ORPH_PAT" 2>/dev/null); ORPH_PRE=${ORPH_PRE:-0}
LAST_END_F="$ROOT/results/K1/.last_boot_end"; NOW_T=$(date +%s)
if [ -f "$LAST_END_F" ]; then COOLDOWN=$(( NOW_T - $(cat "$LAST_END_F") )); else COOLDOWN=-1; fi
teardown
ORPH_POST=$(pgrep -fc "$ORPH_PAT" 2>/dev/null); ORPH_POST=${ORPH_POST:-0}
python3 -c "import json;json.dump({'orphans_pre_teardown':$ORPH_PRE,'orphans_post_teardown':$ORPH_POST,'cooldown_s_since_last_boot':$COOLDOWN,'one_boot_per_cycle':True},open('$OUTDIR/b4_state.json','w'))"

# R4: certs_selfcheck (ramię S) — log przed bootem
if [ "$ARM" = "S" ]; then
  PYTHONPATH=".:.certdeps:${PYTHONPATH:-}" python3 -m r01.proofs.certs_selfcheck > "$OUTDIR/certs_selfcheck.log" 2>&1
  echo "certs_selfcheck rc=$?" | tee -a "$OUTDIR/certs_selfcheck.log"
fi

# higiena EKF2_GPS_CTRL (B5R3): reset persisted param do 7 przed bootem (leftover po GPS-denied)
python3 acts/ensure_gps_enabled.py > "$OUTDIR/gps_hygiene.txt" 2>&1

# INFRA-1 I2a (jedna zmiana, semantyka „nie startuj/nie armuj na chorej maszynie"): bramka obciążenia
# PRZED startem stacku. loadavg(1-min) < LOAD_MAX; czekaj do LOAD_WAIT_MAX próbkując co 30 s; przekroczenie
# ⇒ env-block (boot się NIE zaczyna; nie liczy się nigdzie — to nie lot ani env-fail arm). Zmiana
# WYŁĄCZNIE przed-lotowa, symetryczna dla ramion; nie dotyka segmentu roszczenia (denial→touchdown).
LOAD_MAX="${K1_LOAD_MAX:-8.0}"; LOAD_WAIT_MAX="${K1_LOAD_WAIT_MAX:-600}"
_lt0=$(date +%s); _load_ok=0; _l1="?"
while :; do
  _l1=$(cut -d' ' -f1 /proc/loadavg)
  if awk "BEGIN{exit !($_l1 < $LOAD_MAX)}"; then _load_ok=1; break; fi
  [ $(( $(date +%s) - _lt0 )) -ge "$LOAD_WAIT_MAX" ] && break
  echo "[K1 $ARM p$POINT b$BOOT_N] load $_l1 ≥ $LOAD_MAX — czekam (env-load-wait)"; sleep 30
done
if [ "$_load_ok" != "1" ]; then
  echo "ENV-BLOCK load1=$_l1 max=$LOAD_MAX wait=${LOAD_WAIT_MAX}s" | tee "$OUTDIR/env_block.txt"
  python3 -c "import json;json.dump({'arm':'$ARM','point':$POINT,'boot_n':$BOOT_N,'kind':'env-block','run_valid':None,'load1_at_block':float('$_l1'),'load_max':$LOAD_MAX,'reason':'loadavg1>=LOAD_MAX przez LOAD_WAIT_MAX s — boot nie wystartowal (I2a)'},open('$OUTDIR/manifest.json','w'),indent=2)"
  teardown
  echo "[K1 $ARM p$POINT b$BOOT_N] ENV-BLOCK (load $_l1) — nie liczy sie"; exit 3
fi

BOOT_T0=$(date +%s)
LOGDIR="$OUTDIR" WORLD="$WORLD" PX4_GZ_WORLD="$WORLD" MODEL=gz_x500_mono_cam bash run_stack.sh > "$OUTDIR/stack.log" 2>&1
sleep 3
echo "GUI_PROCS=[$(pgrep -af 'gz sim -g|gz-gui' | grep -v pgrep || echo brak)]" | tee "$OUTDIR/headless_proof.txt"
for i in $(seq 1 40); do gz topic -l 2>/dev/null | grep -q "/world/${WORLD}/clock" && break; sleep 1; done
setsid nohup python3 -m acts.rtf_sampler --world "$WORLD" --out "$OUTDIR/rtf_stream.jsonl" > "$OUTDIR/rtf_sampler.log" 2>&1 &
RTF=$!
# INFRA2-6/E1 (SI-1, TYLKO gałąź E — infra, nie certyfikowany lot K1): watchdog reinitu EKF2 wewnątrz
# bootu. Read-only sampler co 5 s po sockecie daemona PX4 (px4-listener) + `ekf2 stop/start` przy triggerze
# zatrzasku (V1). ŻADNEGO abortu/relaunchu/zmiany EKF2_*/okna arm. Osłona/sędzia/piny/harness lotu S∧N NIETKNIĘTE.
WD=""
if [ "$ARM" = "E" ]; then
  setsid nohup python3 tools/infra2_ekf_watchdog.py \
    --px4-bin "$ROOT/PX4-Autopilot/build/px4_sitl_default/bin" \
    --out "$OUTDIR/ekf_watchdog.json" > "$OUTDIR/ekf_watchdog.log" 2>&1 &
  WD=$!
  echo "[K1 $ARM p$POINT b$BOOT_N] E1 watchdog EKF2 pid=$WD" | tee -a "$OUTDIR/ekf_watchdog.log"
fi
# INFRA-1 ANEKS_INFRA1-3 W2 (P0a): REWERT I2b. Moduł lotu startuje BEZWARUNKOWO po 90 s settle —
# stan znany-dobry (N boot4 / S4-6 / R0.3a armowały). I2b czekał na 'Ready for takeoff' PRZED startem
# modułu lotu, co tworzyło DEADLOCK: 'Ready'⇐pre_flight_checks_pass⇐wyczyszczenie 'No connection to GCS'
# ⇐klient MAVSDK⇐moduł lotu, który I2b odraczał (dowód C2, RAPORT_INFRA2 §C2). I2a (bramka obciążenia,
# wyżej) ZACHOWANA — nie brała udziału w deadlocku. timejump raportowany (nie bramkujący, per C1).
echo "[K1 $ARM p$POINT b$BOOT_N] settle 90 s preflight EKF"; sleep 90
grep -ci 'time jump\|Resetting time sync' "$OUTDIR/stack.log" > "$OUTDIR/timejump_pre.txt" 2>/dev/null || echo 0 > "$OUTDIR/timejump_pre.txt"

if [ "$ARM" = "S" ]; then
  SCEN="K1" K1_POINT="$POINT" GATE_OUT="$OUTDIR/trace.jsonl" PX4_GZ_WORLD="$WORLD" HEADLESS=1 B1_MODEL=x500_mono_cam_0 \
    PYTHONPATH=".:.certdeps:${PYTHONPATH:-}" python3 -m r03.gate_run_r03 > "$OUTDIR/act.log" 2>&1
  RC=$?; HARNESS_FILE="$ROOT/r03/gate_run_r03.py"
elif [ "$ARM" = "E" ]; then
  # INFRA-1 I3: scenariusz PUSTY (arm→takeoff→60 s hover OFFBOARD→land), BEZ denialu/sędziego/K1.
  # Waliduje wyłącznie hartowanie bootu (I2). Moduł lotu w tools/ (nie dotyka osłony/sędziego/kryteriów).
  HOVER_S="${K1_HOVER_S:-60}" GATE_OUT="$OUTDIR/trace.jsonl" PX4_GZ_WORLD="$WORLD" HEADLESS=1 B1_MODEL=x500_mono_cam_0 \
    PYTHONPATH=".:${PYTHONPATH:-}" python3 tools/infra1_empty_flight.py > "$OUTDIR/act.log" 2>&1
  RC=$?; HARNESS_FILE="$ROOT/tools/infra1_empty_flight.py"
else
  K1_POINT="$POINT" GATE_OUT="$OUTDIR/trace.jsonl" PX4_GZ_WORLD="$WORLD" HEADLESS=1 B1_MODEL=x500_mono_cam_0 \
    PYTHONPATH=".:.certdeps:${PYTHONPATH:-}" python3 k1/k1_arm_n.py > "$OUTDIR/act.log" 2>&1
  RC=$?; HARNESS_FILE="$ROOT/k1/k1_arm_n.py"
fi

kill -TERM "$RTF" 2>/dev/null
[ -n "$WD" ] && { kill -TERM "$WD" 2>/dev/null; sleep 7; }   # E1: watchdog dopisuje ekf_watchdog.json na SIGTERM
sleep 1
grep -ci 'time jump\|Resetting time sync' "$OUTDIR/stack.log" > "$OUTDIR/timejump_post.txt" 2>/dev/null || echo 0 > "$OUTDIR/timejump_post.txt"
grep -ciE 'High Gyro Bias|velocity unstable|horizontal velocity' "$OUTDIR/px4.log" > "$OUTDIR/ekf_health_hits.txt" 2>/dev/null || echo 0 > "$OUTDIR/ekf_health_hits.txt"

# ulog: skopiuj nowy .ulg tego bootu (PRE §2 — nigdy /tmp)
ULG=$(find "$ROOT/PX4-Autopilot/build/px4_sitl_default/rootfs/log" -name '*.ulg' -newermt "@$BOOT_T0" 2>/dev/null | xargs -r ls -t 2>/dev/null | head -1)
if [ -n "$ULG" ]; then cp "$ULG" "$OUTDIR/boot.ulg"; echo "$ULG" > "$OUTDIR/ulog_src.txt"; else echo "BRAK ulog" > "$OUTDIR/ulog_src.txt"; fi

teardown

# finalize
if [ "$ARM" = "E" ]; then
  # INFRA-1: manifest pustego bootu (arm_ok/habitat hover/conv_s/load/mem) — sędzia/osłona/kryteria NIETKNIĘTE.
  PYTHONPATH="$B0SP:$ROOT:${PYTHONPATH:-}" python3 tools/infra1_empty_finalize.py \
    --out-dir "$OUTDIR" --boot "$BOOT_N" --rc "$RC" --harness-sha-file "$HARNESS_FILE" 2>&1 | tee "$OUTDIR/finalize.log"
else
  # manifest R5 + habitat (H1∧H2 claim denial→touchdown) + sędzia frozen → judge.json
  ULGARG=""; [ -f "$OUTDIR/boot.ulg" ] && ULGARG="--ulog $OUTDIR/boot.ulg"
  CERTS=""; [ "$ARM" = "S" ] && CERTS="--certs-selfcheck $OUTDIR/certs_selfcheck.log"
  PYTHONPATH="$B0SP:$ROOT:${PYTHONPATH:-}" python3 k1/k1_finalize.py \
    --trace "$OUTDIR/trace.jsonl" --arm "$ARM" --point "$POINT" --boot "$BOOT_N" --kind "$KIND" \
    $ULGARG --harness-sha-file "$HARNESS_FILE" --out-dir "$OUTDIR" $CERTS 2>&1 | tee "$OUTDIR/finalize.log"
fi

date +%s > "$ROOT/results/K1/.last_boot_end"   # B4: znacznik końca bootu (cooldown następnego)
echo "[K1 $ARM p$POINT b$BOOT_N] DONE rc=$RC → $OUTDIR"; exit $RC
