#!/bin/bash
# net/k2_campaign_step.sh — krok kampanii K2 (WERSJONOWANY, ANEKS_NET-0 §2).
# Przetwarza zakończony boot denialowy: breach-guard (STOP) → tripwire eps_cap (STOP diag) → k2_judge →
# record do k2_campaign.json → commit → launch następnego. Denial=1 ep/boot (K1).
#
# Użycie: net/k2_campaign_step.sh <DONE_OUT> <DONE_SID> <NEXT_BN> <NEXT_OUT> <NEXT_EPID>
#   NEXT_* puste ("" "" "") ⇒ tylko przetwórz DONE (ostatni boot).
set -u
ROOT=/home/olga/projects/liquidpatrol
cd "$ROOT"
DOUT="$1"; DSID="$2"; NBN="${3:-}"; NOUT="${4:-}"; NEPID="${5:-}"
name=$(basename "$DOUT")

if grep -q "ENV-BLOCK" "${DOUT}_launch.log" 2>/dev/null; then
  echo "[$name] ENV-BLOCK — re-append (bez inkrementu), launch retry tego samego"
  python3 - "$DSID" <<'PY'
import json, sys
sid = sys.argv[1]
st = json.load(open("results/K2/k2_campaign.json"))
# env-fail: zostaw w pending (przenieś na koniec, attempt bez zmian)
for i, e in enumerate(st["pending"]):
    if e["scenario_id"] == sid:
        st["pending"].append(st["pending"].pop(i)); break
json.dump(st, open("results/K2/k2_campaign.json", "w"), indent=2)
print("  re-append", sid)
PY
else
  BR=$(grep -c '"ev": "breach"' "$DOUT/trace.jsonl" 2>/dev/null); BR=${BR:-0}
  if [ "$BR" != "0" ]; then
    echo "[$name] !!! BREACH ($BR) — STOP KAMPANII (domena certów, PRE_K2 K4). Nie uruchamiam następnego."
    exit 2
  fi
  # k2_judge + tripwire + record
  RES=$(python3 - "$DOUT" "$DSID" <<'PY'
import json, sys
sys.path.insert(0, "/home/olga/projects/liquidpatrol")
from bench.k2_judge import judge_episode_k2
outdir, sid = sys.argv[1], sys.argv[2]
st = json.load(open("results/K2/k2_campaign.json"))
eps_cap = st["eps_cap"]
vs = judge_episode_k2(outdir, eps_cap=eps_cap, home=(0.0, 0.0))
v = vs[0] if vs else None
if v is None:
    # brak epizodu w trace (env/didnt enter) → env-invalid, re-append cap 3
    for i, e in enumerate(st["pending"]):
        if e["scenario_id"] == sid:
            e2 = st["pending"].pop(i)
            if e2["attempt"] >= 3:
                st["unresolved"].append(e2); print("UNRESOLVED", sid)
            else:
                e2["attempt"] += 1; st["pending"].append(e2); print("RETRY", sid, "att", e2["attempt"])
            break
    json.dump(st, open("results/K2/k2_campaign.json", "w"), indent=2); sys.exit(0)
# tripwire: x_exc > eps_cap ∧ breach=False ⇒ STOP diagnostyczny
if (v.get("x_exc") is not None) and v["x_exc"] > eps_cap and not v.get("breach"):
    print("TRIPWIRE", sid, "x_exc", v["x_exc"]); sys.exit(9)
# ważność: valid (V2′ do T_inj); jeśli nieważny env → retry
if not v.get("valid"):
    for i, e in enumerate(st["pending"]):
        if e["scenario_id"] == sid:
            e2 = st["pending"].pop(i)
            if e2["attempt"] >= 3:
                st["unresolved"].append(e2); print("UNRESOLVED", sid)
            else:
                e2["attempt"] += 1; st["pending"].append(e2); print("RETRY", sid, "att", e2["attempt"])
            break
    json.dump(st, open("results/K2/k2_campaign.json", "w"), indent=2); sys.exit(0)
# ważny → record verdict (pierwsza ważna liczy się)
rec = {"scenario_id": sid, "valid": True, "t_refuse": v["t_refuse"], "x_exc": v["x_exc"],
       "t_td_s": v["t_td_s"], "breach": v["breach"], "touchdown": v["touchdown"],
       "verdict_pass": v["verdict"]["pass"], "reasons": v["verdict"]["reasons"]}
st["done"].append(rec)
st["pending"] = [e for e in st["pending"] if e["scenario_id"] != sid]
json.dump(st, open("results/K2/k2_campaign.json", "w"), indent=2)
print("DONE", sid, "PASS" if v["verdict"]["pass"] else "FAIL", "t_refuse", round(v["t_refuse"],3) if v["t_refuse"] else None, "x_exc", v["x_exc"])
PY
)
  RC=$?
  echo "[$name] $RES"
  if [ $RC -eq 9 ]; then
    echo "[$name] !!! TRIPWIRE eps_cap — STOP DIAGNOSTYCZNY (x_exc>9.25 ∧ breach=False, ANEKS_K2-4 §3). Nie uruchamiam następnego."
    exit 3
  fi
  git add "$DOUT/" 2>/dev/null; git reset -q "$DOUT/boot.ulg" 2>/dev/null
  git add "${DOUT}_launch.log" results/K2/k2_campaign.json results/K2/k2_monitor.log 2>/dev/null
  git commit -q -m "K2 kampania $name ($DSID): $RES" >/dev/null && echo "  commit $(git rev-parse --short HEAD)"
fi

if [ -n "$NBN" ]; then
  echo "[next] boot $NOUT ep_id $NEPID (denial T_inj=30)"
  K2_ARM_MONITOR=1 bash net/run_k2_boot.sh "$NBN" "$NOUT" crit "$NEPID" 30
fi
