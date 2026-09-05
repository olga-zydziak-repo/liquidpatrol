#!/bin/bash
# net/fly_campaign_step.sh — jeden krok kampanii F2 (WERSJONOWANY, ANEKS_NET-0 §2).
# Przetwarza właśnie zakończony boot (breach-guard → judge → record → commit), potem popuje i uruchamia następny.
# Breach ⇒ STOP (exit 2, NIE uruchamia następnego — PRE_NET N7/SR-5).
#
# Użycie: net/fly_campaign_step.sh <DONE_OUT> <DONE_QUEUE> <NEXT_BOOTN> <NEXT_OUT> <NEXT_ARM> <NEXT_QUEUE>
#   NEXT_* puste ("" "" "") ⇒ tylko przetwórz DONE (ostatni boot, bez następnego).
set -u
ROOT=/home/olga/projects/liquidpatrol
cd "$ROOT"
DOUT="$1"; DQ="$2"; NBN="${3:-}"; NOUT="${4:-}"; NARM="${5:-}"; NQ="${6:-}"
name=$(basename "$DOUT")

if grep -q "ENV-BLOCK" "${DOUT}_launch.log" 2>/dev/null; then
  echo "[$name] ENV-BLOCK — record (missing→re-append) bez commitu artefaktów lotu"
  python3 -m bench.campaign_queue record --state "$DQ" --outdir "$DOUT" >/dev/null
  git add "$DOUT/manifest.json" "$DQ" "${DOUT}_launch.log" results/NET/FLY/fly_monitor.log 2>/dev/null
  git commit -q -m "NET F2 $name ENV-BLOCK (proc_gate, missing→re-append)" >/dev/null || true
else
  BR=$(grep -c '"ev": "breach"' "$DOUT/trace.jsonl" 2>/dev/null); BR=${BR:-0}
  if [ "$BR" != "0" ]; then
    echo "[$name] !!! BREACH ($BR) — STOP F2 (SR-5/N7). Nie uruchamiam następnego."
    python3 -m bench.campaign_analyze "$DOUT" 2>&1 | head -6
    exit 2
  fi
  echo "[$name] breach=0. Wynik:"
  python3 -m bench.campaign_analyze "$DOUT" 2>&1 | head -4
  python3 -m bench.campaign_queue record --state "$DQ" --outdir "$DOUT" \
    | python3 -c "import json,sys;d=json.load(sys.stdin)['summary'];print('  queue done',d['done'],'pending',d['pending'])"
  git add "$DOUT/" 2>/dev/null; git reset -q "$DOUT/boot.ulg" 2>/dev/null
  git add "$DQ" "${DOUT}_launch.log" results/NET/FLY/fly_monitor.log 2>/dev/null
  git commit -q -m "NET F2 $name" >/dev/null; echo "  commit $(git rev-parse --short HEAD)"
fi

if [ -n "$NBN" ]; then
  echo "[next] pop $NARM b→ $NOUT"
  python3 -m bench.campaign_queue pop --state "$NQ" --n 4 \
    | python3 -c "import json,sys;print('  batch',[e['scenario_id'] for e in json.load(sys.stdin)])"
  bash net/run_fly_boot.sh "$NBN" "$NOUT" "$NARM" crit "$NQ"
fi
