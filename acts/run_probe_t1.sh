#!/usr/bin/env bash
# acts/run_probe_t1.sh [RUN] [OUTDIR] — PROMPT_D_P3 T1 / ANEKS_D8 §3c: bieg PROBE (nie próba, nie demo).
# world_demo_A1 + kanał LIVE (DEMO_MTI=1, progi frozen) + intruz wg spec (świat-stały) + EGO-MOTION drona
# (orbita wokół dwell, yaw na cel, v=2.5 m/s — wariant wdrożeniowy §3c). Instrumentacja §3e: MTI_FRAME_LOG
# (diff_max/n_kept, kadencja klatek), DBG_LOG (mti_ok/n_comps/box cx,cy, kadencja det), trace (zasięg/pos).
# Percepcja NIERAPORTOWALNA jako wynik aktu (SR-J2 probe). FILM OFF — izolacja pomiaru percepcji.
set -o pipefail
ROOT="/home/olga/projects/liquidpatrol"; cd "$ROOT"
RUN="${1:-proba_1}"
OUTDIR="${2:-$ROOT/results/demo/A1/probe_t1/$RUN}"
mkdir -p "$OUTDIR"

# §3c wariant wdrożeniowy: orbita wokół dwell. ρ=1.0 → zasięg ~7.0-9.0 m; v=2.5 z REGATE.
export PROBE_EGOMOTION=1
export PROBE_ORBIT_R="${PROBE_ORBIT_R:-1.0}"
export PROBE_ORBIT_V="${PROBE_ORBIT_V:-2.5}"
# ANEKS_D8 §5b (Bieg 2): dźwignia CENTROWANIA PIONOWEGO — wysokość dwell drona = wysokość pierścienia
# intruza (11.5 ENU) → DALT_eff~0 → cel na osi kamery (cy~0.5). REGATE elew 10.8° (PROFIL_REGATE:48,91)
# dała cy 0.28 (proba_1) > próg §5c 0.12; podniesienie drona centruje cel. Range 3D=poziomy 7.55-8.32∈[7,9].
export PROBE_ALT="${PROBE_ALT:-11.5}"
# §3e/§5c instrumentacja
export MTI_FRAME_LOG="$OUTDIR/mti_frame.jsonl"   # detector_node (dziedziczy env) — per-klatka diff_max/n_kept
export DECISION_FRAME_LOG="$OUTDIR/dec_frame.jsonl"  # §5c: per-decyzję sim_t + top1 cx,cy (bramka central-ok)
export DBG_LOG=1                                  # acts/dbg_logger — mti_ok/n_comps/box (kanał)
export FILM_CAPTURE=0                             # bez filmu: izolacja pomiaru percepcji (load-clean)

echo "[probe_t1] RUN=$RUN OUTDIR=$OUTDIR ρ=$PROBE_ORBIT_R v=$PROBE_ORBIT_V (ANEKS_D8 §3c Bieg 1)"
bash acts/run_act_live.sh A1 "$RUN" "$OUTDIR"
RC=$?
echo "[probe_t1] runner rc=$RC — analiza §3e:"
python3 acts/probe_t1_analyze.py "$OUTDIR" | tee "$OUTDIR/probe_t1_verdict.txt"
exit $RC
