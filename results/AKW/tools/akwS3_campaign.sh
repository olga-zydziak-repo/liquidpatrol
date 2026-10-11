#!/usr/bin/env bash
# results/AKW/tools/akwS3_campaign.sh — ORKIESTRATOR kampanii AKW S3 (ANEKS_AKW-2 §4).
# KOPIA results/DET/tools/detS4_campaign.sh (FROZEN, nietknięty) ze zmianami WYŁĄCZNIE:
#   ścieżki (results/AKW/{tools,camp}), driver akwS3_boot.sh, analiza akw_analyze.py,
#   summary akw_summary.json, parowanie akw_pairs.py, stan next_boot_n=5 (booty nogi
#   1–4 zużyte: S1 3 + re-smoke 1), budżet launches ≤27 (24+3, ANEKS_AKW-2 §5),
#   + BEZPIECZNIK MODU (ANEKS_AKW-2 §3, NOWY blok po każdym boocie V2): wolny mod
#   (dt p50 percep_feed ≥0.1 s po ≥300 rekordach) z ZEREM admisji (fresh) przy celu
#   w FOV w epizodach ŚLEPYCH (bearing≠0) ⇒ FUSE_TRIP; przerwanie NA GRANICY RUNDY
#   (STOP po domknięciu rundy i parowaniu) + STOP-ANEKS. Pierwszy wolny mod
#   z admisjami >0 logowany wprost (zamyka ryzyko pomiarem).
# 12 rund × 2 booty {B, V2}; rotacja naprzemienna (nieparzyste B→V2, parzyste V2→B).
# Twarde STOPy VERBATIM: stop_now (breach/REFUSE(POS)) ⇒ STOP natychmiast; budżet;
# nieważny boot ⇒ JEDNA powtórka 'r', pula zapasu 3; wznawialność per gotowe summary;
# RĘCZNE ZATRZYMANIE: touch results/AKW/camp/PAUSE (granica rundy).
#
# Użycie: akwS3_campaign.sh [R_START] [R_END]   (dom. 1 12)
set -u
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
TOOLS="$ROOT/results/AKW/tools"
CAMP="$ROOT/results/AKW/camp"
STATE="$CAMP/campaign_state.json"
MONLOG="$CAMP/akwS3_monitor.log"
B0SP="$ROOT/.b0deps/lib/python3.12/site-packages"
RS="${1:-1}"; RE="${2:-12}"
mkdir -p "$CAMP"

[ -f "$STATE" ] || echo '{"next_boot_n": 5, "spares_used": 0, "launches": 0}' > "$STATE"

st_get() { python3 -c "import json;print(json.load(open('$STATE'))['$1'])"; }
st_inc() { python3 - "$1" <<'PY'
import json, sys
p = "/home/olga/projects/liquidpatrol/results/AKW/camp/campaign_state.json"
s = json.load(open(p)); s[sys.argv[1]] += 1
if sys.argv[1] == "launches":
    s["next_boot_n"] += 1
json.dump(s, open(p, "w"))
PY
}

mode_fuse() {  # mode_fuse <OUTDIR> — bezpiecznik modu (tylko V2); tworzy $CAMP/FUSE_TRIP przy zadziałaniu
  PYTHONPATH="$B0SP:$ROOT" python3 - "$1" "$CAMP" <<'PY'
import json, math, os, sys
outdir, camp = sys.argv[1], sys.argv[2]
sys.path.insert(0, "/home/olga/projects/liquidpatrol/results/DET_RECON/tools")
from det_labels import BootGeo                      # frozen 8f7430cd (READ-ONLY)
pf = os.path.join(outdir, "percep_feed.jsonl")
if not os.path.exists(pf):
    print("[fuse] brak percep_feed — pomijam"); sys.exit(0)
rows = [json.loads(l) for l in open(pf) if l.strip()]
rows = [r for r in rows if r.get("t_frame") is not None]
rows.sort(key=lambda r: r["t_frame"])
if len(rows) < 300:
    print(f"[fuse] {len(rows)} rekordów (<300) — mod nieorzeczony"); sys.exit(0)
ts = [r["t_frame"] for r in rows]
dts = sorted(b - a for a, b in zip(ts, ts[1:]) if 0 < b - a < 0.5)
p50 = dts[len(dts) // 2] if dts else 0.0
slow = p50 >= 0.1
# okna epizodów ŚLEPYCH (bearing != 0) z trace + manifestu epizodów
wins = []
cur = None
for ln in open(os.path.join(outdir, "trace.jsonl")):
    try:
        e = json.loads(ln)
    except json.JSONDecodeError:
        continue
    if e.get("t") != "event":
        continue
    if e.get("ev") == "episode_start":
        cur = {"sid": e.get("scenario_id"), "lo": e.get("t0_sim")}
    elif e.get("ev") == "invalid_start":
        cur = None
    elif e.get("ev") == "episode_end" and cur:
        cell = int(cur["sid"].split("_")[0][1:])
        if cell % 4 != 0:                            # bearing != 0 => ślepy
            wins.append((cur["lo"], e["sim"]))
        cur = None
geo = BootGeo(outdir, 1.0, 60.0)
n_fov = n_fresh = n_conj = 0
for r in rows:
    t = r["t_frame"]
    if not any(lo <= t <= hi for lo, hi in wins):
        continue
    if geo.label(t).get("flag") != "OK":
        continue
    n_fov += 1
    if r.get("fresh"):
        n_fresh += 1
    b = r.get("box")
    if b and min(b[0], 1 - b[0], b[1], 1 - b[1]) >= 0.10 and r.get("mti_ok"):
        n_conj += 1
mode = "WOLNY" if slow else "SZYBKI"
msg = (f"[fuse] {os.path.basename(outdir)}: mod {mode} (dt p50 {p50:.4f} s = "
       f"{(1/p50 if p50 else 0):.2f} Hz), ślepe@FOV n={n_fov}, admisje fresh={n_fresh}, "
       f"koniunkcja central∧mti={n_conj}")
print(msg)
open(os.path.join(outdir, "akw_mode_fuse.json"), "w").write(json.dumps(
    {"mode": mode, "dt_p50_s": round(p50, 4), "n_fov_blind": n_fov,
     "n_fresh_blind_fov": n_fresh, "n_conj_blind_fov": n_conj}, indent=1))
if slow and n_fov > 0 and n_fresh == 0:
    open(os.path.join(camp, "FUSE_TRIP"), "a").write(msg + "\n")
    print("[fuse] BEZPIECZNIK MODU ZADZIAŁAŁ — przerwanie na granicy rundy")
elif slow and n_fresh > 0:
    print("[fuse] WOLNY mod z admisjami >0 — ryzyko §3 zamknięte pomiarem (wpis do raportu)")
PY
}

run_one() {  # run_one <NAME> <ARM> <RND> <EPIDS> → rc: 0 ok-wszystko-ważne, 5 nieważne/braki, 9 STOP
  local NAME="$1" ARM="$2" RND="$3" EPIDS="$4"
  local OUTDIR="$CAMP/$NAME"
  if [ -f "$OUTDIR/akw_summary.json" ]; then
    echo "[camp] $NAME już zanalizowany — pomijam (wznowienie)" | tee -a "$MONLOG"
  else
    local L U BN
    L=$(st_get launches); U=$(st_get spares_used)
    if [ "$L" -ge 27 ]; then
      echo "BUDGET: launches=$L >= 27 — twardy STOP (ANEKS_AKW-2 §5)" | tee -a "$MONLOG" | tee "$CAMP/STOP"; return 9
    fi
    BN=$(st_get next_boot_n)
    st_inc launches
    bash "$TOOLS/akwS3_boot.sh" "$BN" "$NAME" "$ARM" "$RND" "$EPIDS" >> "$MONLOG" 2>&1
    local BRC=$?
    echo "[camp] $NAME boot_n=$BN rc=$BRC" | tee -a "$MONLOG"
    if [ ! -f "$OUTDIR/manifest.json" ]; then
      echo "[camp] $NAME BEZ manifestu (crash/env rc=$BRC)" | tee -a "$MONLOG"; return 5
    fi
    PYTHONPATH="$B0SP:$ROOT" python3 "$TOOLS/akw_analyze.py" "$OUTDIR" > /dev/null 2>>"$MONLOG" || {
      echo "[camp] $NAME analiza PADŁA" | tee -a "$MONLOG"; return 5; }
    [ "$ARM" = "V2" ] && mode_fuse "$OUTDIR" | tee -a "$MONLOG"
  fi
  python3 - "$OUTDIR" <<'PY'
import json, os, sys
s = json.load(open(os.path.join(sys.argv[1], "akw_summary.json")))
if s.get("stop_now"):
    sys.exit(9)
if s.get("missing_manifest") or s.get("rc") not in (0, None) or \
   s["n_valid_final"] < s["n_episodes"] or s["n_episodes"] < 4:
    sys.exit(5)
sys.exit(0)
PY
  local ARC=$?
  if [ $ARC -eq 9 ]; then
    echo "S-BEZP STOP: breach lub REFUSE(POS) w $NAME (ANEKS_AKW-2 §4.5)" | tee -a "$MONLOG" | tee "$CAMP/STOP"
  fi
  return $ARC
}

for RND in $(seq "$RS" "$RE"); do
  if [ -f "$CAMP/STOP" ]; then echo "[camp] STOP obecny — koniec" | tee -a "$MONLOG"; exit 9; fi
  if [ -f "$CAMP/PAUSE" ]; then echo "[camp] PAUSE — zatrzymanie na granicy rundy $RND" | tee -a "$MONLOG"; exit 7; fi
  if [ -f "$CAMP/FUSE_TRIP" ]; then
    echo "[camp] BEZPIECZNIK MODU — przerwanie na granicy rundy $RND (ANEKS_AKW-2 §3)" | tee -a "$MONLOG" | tee "$CAMP/STOP"; exit 9
  fi
  BASE=$(( 4 * (RND - 1) ))
  EPIDS="$BASE,$((BASE+1)),$((BASE+2)),$((BASE+3))"
  if [ $(( RND % 2 )) -eq 1 ]; then ORDER="B V2"; else ORDER="V2 B"; fi
  echo "=== RUNDA $RND (eps $EPIDS; kolejność $ORDER) $(date +%H:%M:%S) ===" | tee -a "$MONLOG"
  for ARM in $ORDER; do
    NAME="r${RND}_${ARM}"
    run_one "$NAME" "$ARM" "$RND" "$EPIDS"; RC=$?
    if [ $RC -eq 9 ]; then exit 9; fi
    if [ $RC -eq 5 ]; then
      U=$(st_get spares_used)
      if [ "$U" -lt 3 ] && [ ! -f "$CAMP/${NAME}r/akw_summary.json" ]; then
        echo "[camp] $NAME nieważny — powtórka ${NAME}r (zapas $((U+1))/3)" | tee -a "$MONLOG"
        st_inc spares_used
        run_one "${NAME}r" "$ARM" "$RND" "$EPIDS"; RC2=$?
        if [ $RC2 -eq 9 ]; then exit 9; fi
        [ $RC2 -eq 5 ] && echo "[camp] ${NAME}r też nieważny — wypadanie parowe" | tee -a "$MONLOG"
      else
        echo "[camp] $NAME nieważny — zapas wyczerpany/powtórka istnieje — wypadanie parowe" | tee -a "$MONLOG"
      fi
    fi
  done
  python3 "$TOOLS/akw_pairs.py" > "$CAMP/pairs_after_r${RND}.txt" 2>&1 || true
  if [ -f "$CAMP/FUSE_TRIP" ]; then
    echo "[camp] BEZPIECZNIK MODU po rundzie $RND — STOP na granicy rundy (ANEKS_AKW-2 §3)" | tee -a "$MONLOG" | tee "$CAMP/STOP"; exit 9
  fi
  echo "=== RUNDA $RND DONE $(date +%H:%M:%S) ===" | tee -a "$MONLOG"
done
echo "[camp] KAMPANIA DONE (rundy $RS-$RE)" | tee -a "$MONLOG"
