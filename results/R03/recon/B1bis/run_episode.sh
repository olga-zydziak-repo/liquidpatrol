#!/usr/bin/env bash
# run_episode.sh — loty EPISODE (§3ter, A-episode): profil t_pre=1.0s v_max -> Land->touchdown.
# ≥2 stany (straight,corner) × ≥2 loty. Świeży boot per lot. Fly logi PERSYSTENTNE (t_flag).
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source ros2_ws/install/setup.bash 2>/dev/null || true
source env_gpu.sh >/dev/null 2>&1 || true
set -o pipefail
export HEADLESS=1
FL="$ROOT/results/R03/recon/B1bis/episode"; mkdir -p "$FL"
MET="$FL/metrics_episode2.jsonl"; : > "$MET"   # profil DWUFAZOWY (§3quater)

FLIGHTS=(
  "p_c1_corner corner"
  "p_c2_corner corner"
  "p_c3_corner corner"
  "p_s1_straight straight"
  "p_s2_straight straight"
)

boot() {
  pkill -9 -f "MicroXRCEAgent" 2>/dev/null; pkill -9 -f "px4_sitl_default/bin/px4" 2>/dev/null
  pkill -9 -f "gz sim" 2>/dev/null; pkill -9 -f "ruby.*gz" 2>/dev/null; sleep 3
  LOGDIR="$FL" MODEL=gz_x500_mono_cam bash run_stack.sh >"$FL/boot_$1.log" 2>&1
  # run_stack czeka na gz /clock; XRCE ~2-5 s; fly ma arm-retry. 90 s: PEŁNA konwergencja EKF
  # (eph → 0.150 floor po 90 s; 15 s dawało eph 0.22 = broken → flyaway/W5-fail). NIE load (24 rdzenie).
  sleep 90
}

run_one() {
  local name="$1" state="$2" out="$FL/${name}.jsonl" flog="$FL/${name}.flylog"
  echo "[epi] === $name state=$state ==="
  B1_OUT="$out" B1_DUR=95 python3 results/R03/recon/B1bis/b1bis_record.py >"$FL/rec_${name}.log" 2>&1 &
  local rp=$!
  sleep 2
  MODE=episode EPISODE_STATE="$state" T_PRE=1.0 python3 results/R03/recon/B1bis/b1bis_fly.py >"$flog" 2>&1
  wait $rp 2>/dev/null
  if ! grep -q "EVENT denial_on" "$flog"; then echo "[epi] $name: W1 FAIL (brak denial_on)"; return 1; fi
  if ! grep -q "EVENT touchdown" "$flog"; then echo "[epi] $name: brak touchdown"; return 1; fi
  local post=$(grep -oE "EKF2_GPS_CTRL post=[0-9]+" "$flog" | grep -oE "[0-9]+$")
  echo "[epi] $name: post EKF2_GPS_CTRL=$post"
  python3 - "$name" "$state" "$out" "$flog" "$MET" <<'PY' | tee "$FL/analysis_${name}.tmp"
import sys, json, math
sys.path.insert(0,'results/R03/recon/B1bis/instrument')
import gt_judge as J
name,state,out,flog,met=sys.argv[1:6]
# t_flag = pierwszy dead_reckoning=True - denial_on (mono, wspolny zegar procesow)
den=None; touch=None
for line in open(flog):
    if "EVENT denial_on" in line: den=float(line.split("mono=")[1].split()[0])
    if "EVENT touchdown" in line: touch=float(line.split("mono=")[1].split()[0])
ekf,gt=J.load(out)
first_dr=next((r["mono"] for r in sorted(ekf,key=lambda r:r["mono"]) if r.get("dead_reckoning")), None)
t_flag = (first_dr-den) if (first_dr and den) else None
res=J.compute_drift(ekf,gt,swap=True)  # max_drift = eps_pos przez okno DR (denial->touchdown+)
res.update({"name":name,"state":state,"t_flag_s":round(t_flag,3) if t_flag else None,
            "denial_mono":den,"touch_mono":touch,
            "episode_dr_s":round(touch-den,2) if (touch and den) else None})
open(met,"a").write(json.dumps(res)+"\n")
print(f"[epi] {name}: eps_pos(max)={res['max_drift']} p95={res.get('healthy_p95_eps')} valid={res.get('healthy_valid')} "
      f"t_flag={res['t_flag_s']}s epi_dr={res['episode_dr_s']}s resets={res.get('resets')}")
print("VALID" if res.get("healthy_valid") else "INVALID")
PY
  grep -q "^VALID$" "$FL/analysis_${name}.tmp" 2>/dev/null && return 0 || return 1
}

echo "[epi] START loty=${#FLIGHTS[@]}"
for spec in "${FLIGHTS[@]}"; do
  read -r name state <<<"$spec"
  ok=0
  for att in 1 2 3; do
    boot "$name"
    if run_one "$name" "$state"; then ok=1; break; fi
    echo "[epi] $name proba $att nieudana (W1/W5)"
  done
  [ "$ok" = 0 ] && echo "[epi] $name ODRZUCONY"
done
pkill -9 -f "MicroXRCEAgent" 2>/dev/null; pkill -9 -f "px4_sitl_default/bin/px4" 2>/dev/null
pkill -9 -f "gz sim" 2>/dev/null; pkill -9 -f "ruby.*gz" 2>/dev/null
echo "[epi] DONE"
