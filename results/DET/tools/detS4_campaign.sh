#!/usr/bin/env bash
# results/DET/tools/detS4_campaign.sh — ORKIESTRATOR kampanii C (ANEKS_DET-3 §3).
# 12 rund × 2 booty {B, V2}; rotacja naprzemienna (nieparzyste B→V2, parzyste V2→B).
# Per boot: detS4_boot.sh → detS4_analyze.py → decyzje:
#   * stop_now (breach / REFUSE(POS)) ⇒ plik STOP + natychmiastowy koniec (ANEKS §3.5);
#   * manifest brak / rc!=0 / epizod nieważny (V2′ ∨ żywość) ⇒ JEDNA powtórka bootu
#     (sufiks 'r'), pula zapasu ŁĄCZNIE 3 booty (ANEKS §3.4) — po wyczerpaniu wypadanie parowe;
#   * budżet: launches ≤ 27 (24+3) ⇒ twardy STOP (ANEKS §3.8, budżet nogi ≤40/45 po S4).
# Stan: results/DET/camp/campaign_state.json {next_boot_n, spares_used, launches}.
# Wznawialność: boot z gotowym detS4_summary.json jest pomijany (przerwanie tylko na
# granicy rundy — skrypt przerwany między bootami wznawia od brakującego bootu tej rundy).
# RĘCZNE ZATRZYMANIE na granicy rundy: touch results/DET/camp/PAUSE (sprawdzane przed rundą).
#
# Użycie: detS4_campaign.sh [R_START] [R_END]   (dom. 1 12)
set -u
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
TOOLS="$ROOT/results/DET/tools"
CAMP="$ROOT/results/DET/camp"
STATE="$CAMP/campaign_state.json"
MONLOG="$CAMP/detS4_monitor.log"
RS="${1:-1}"; RE="${2:-12}"
mkdir -p "$CAMP"

[ -f "$STATE" ] || echo '{"next_boot_n": 14, "spares_used": 0, "launches": 0}' > "$STATE"

st_get() { python3 -c "import json;print(json.load(open('$STATE'))['$1'])"; }
st_inc() { python3 - "$1" <<'PY'
import json, sys
p = "/home/olga/projects/liquidpatrol/results/DET/camp/campaign_state.json"
s = json.load(open(p)); s[sys.argv[1]] += 1
if sys.argv[1] == "launches":
    s["next_boot_n"] += 1
json.dump(s, open(p, "w"))
PY
}

run_one() {  # run_one <NAME> <ARM> <RND> <EPIDS> → rc: 0 ok-wszystko-ważne, 5 nieważne/braki, 9 STOP
  local NAME="$1" ARM="$2" RND="$3" EPIDS="$4"
  local OUTDIR="$CAMP/$NAME"
  if [ -f "$OUTDIR/detS4_summary.json" ]; then
    echo "[camp] $NAME już zanalizowany — pomijam (wznowienie)" | tee -a "$MONLOG"
  else
    local L U BN
    L=$(st_get launches); U=$(st_get spares_used)
    if [ "$L" -ge 27 ]; then
      echo "BUDGET: launches=$L >= 27 — twardy STOP (ANEKS §3.8)" | tee -a "$MONLOG" | tee "$CAMP/STOP"; return 9
    fi
    BN=$(st_get next_boot_n)
    st_inc launches
    bash "$TOOLS/detS4_boot.sh" "$BN" "$NAME" "$ARM" "$RND" "$EPIDS" >> "$MONLOG" 2>&1
    local BRC=$?
    echo "[camp] $NAME boot_n=$BN rc=$BRC" | tee -a "$MONLOG"
    if [ ! -f "$OUTDIR/manifest.json" ]; then
      echo "[camp] $NAME BEZ manifestu (crash/env rc=$BRC)" | tee -a "$MONLOG"; return 5
    fi
    python3 "$TOOLS/detS4_analyze.py" "$OUTDIR" > /dev/null 2>>"$MONLOG" || {
      echo "[camp] $NAME analiza PADŁA" | tee -a "$MONLOG"; return 5; }
  fi
  python3 - "$OUTDIR" <<'PY'
import json, os, sys
s = json.load(open(os.path.join(sys.argv[1], "detS4_summary.json")))
if s.get("stop_now"):
    sys.exit(9)
if s.get("missing_manifest") or s.get("rc") not in (0, None) or \
   s["n_valid_final"] < s["n_episodes"] or s["n_episodes"] < 4:
    sys.exit(5)
sys.exit(0)
PY
  local ARC=$?
  if [ $ARC -eq 9 ]; then
    echo "S-BEZP STOP: breach lub REFUSE(POS) w $NAME (ANEKS §3.5)" | tee -a "$MONLOG" | tee "$CAMP/STOP"
  fi
  return $ARC
}

for RND in $(seq "$RS" "$RE"); do
  if [ -f "$CAMP/STOP" ]; then echo "[camp] STOP obecny — koniec" | tee -a "$MONLOG"; exit 9; fi
  if [ -f "$CAMP/PAUSE" ]; then echo "[camp] PAUSE — zatrzymanie na granicy rundy $RND" | tee -a "$MONLOG"; exit 7; fi
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
      if [ "$U" -lt 3 ] && [ ! -f "$CAMP/${NAME}r/detS4_summary.json" ]; then
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
  python3 "$TOOLS/detS4_pairs.py" > "$CAMP/pairs_after_r${RND}.txt" 2>&1 || true
  echo "=== RUNDA $RND DONE $(date +%H:%M:%S) ===" | tee -a "$MONLOG"
done
echo "[camp] KAMPANIA DONE (rundy $RS-$RE)" | tee -a "$MONLOG"
