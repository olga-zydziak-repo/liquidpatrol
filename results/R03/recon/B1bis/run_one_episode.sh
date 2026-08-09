#!/usr/bin/env bash
# run_one_episode.sh <name> <state>  — jeden lot EPISODE na świeżym, w pełni skonwergowanym boocie (90 s).
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
source /opt/ros/jazzy/setup.bash 2>/dev/null || true
source ros2_ws/install/setup.bash 2>/dev/null || true
source env_gpu.sh >/dev/null 2>&1 || true
export HEADLESS=1
FL="$ROOT/results/R03/recon/B1bis/episode"; mkdir -p "$FL"
MET="$FL/metrics_episode.jsonl"
name="$1"; state="$2"
pkill -9 -f "MicroXRCEAgent" 2>/dev/null; pkill -9 -f "px4_sitl_default/bin/px4" 2>/dev/null
pkill -9 -f "gz sim" 2>/dev/null; pkill -9 -f "ruby.*gz" 2>/dev/null; sleep 3
LOGDIR="$FL" MODEL=gz_x500_mono_cam bash run_stack.sh >"$FL/boot_${name}.log" 2>&1
echo "[one] $name boot done, settling 90s (konwergencja EKF)…"; sleep 90
out="$FL/${name}.jsonl"; flog="$FL/${name}.flylog"
B1_OUT="$out" B1_DUR=90 python3 results/R03/recon/B1bis/b1bis_record.py >"$FL/rec_${name}.log" 2>&1 &
rp=$!; sleep 2
MODE=episode EPISODE_STATE="$state" T_PRE=1.0 python3 results/R03/recon/B1bis/b1bis_fly.py >"$flog" 2>&1
wait $rp 2>/dev/null
if ! grep -q "EVENT touchdown" "$flog"; then echo "[one] $name: brak touchdown (W1)"; exit 1; fi
post=$(grep -oE "EKF2_GPS_CTRL post=[0-9]+" "$flog" | grep -oE "[0-9]+$"); echo "[one] $name post=$post"
python3 - "$name" "$state" "$out" "$flog" "$MET" <<'PY'
import sys, json
sys.path.insert(0,'results/R03/recon/B1bis/instrument')
import gt_judge as J
name,state,out,flog,met=sys.argv[1:6]
den=touch=None
for line in open(flog):
    if "EVENT denial_on" in line: den=float(line.split("mono=")[1].split()[0])
    if "EVENT touchdown" in line: touch=float(line.split("mono=")[1].split()[0])
ekf,gt=J.load(out)
fdr=next((r["mono"] for r in sorted(ekf,key=lambda r:r["mono"]) if r.get("dead_reckoning")),None)
res=J.compute_drift(ekf,gt,swap=True)
res.update({"name":name,"state":state,"t_flag_s":round(fdr-den,3) if (fdr and den) else None,
            "episode_dr_s":round(touch-den,2) if (touch and den) else None})
open(met,"a").write(json.dumps(res)+"\n")
print(f"[one] {name}: eps_pos={res['max_drift']} p95={res.get('healthy_p95_eps')} valid={res.get('healthy_valid')} "
      f"t_flag={res['t_flag_s']} epi_dr={res['episode_dr_s']} @2s={res.get('drift_at_2s')} @5s={res.get('drift_at_5s')} resets={res.get('resets')}")
PY
pkill -9 -f "MicroXRCEAgent" 2>/dev/null; pkill -9 -f "px4_sitl_default/bin/px4" 2>/dev/null
pkill -9 -f "gz sim" 2>/dev/null
echo "[one] $name DONE"
