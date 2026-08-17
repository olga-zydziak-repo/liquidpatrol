#!/usr/bin/env python3
"""tools/test_act_judge.py — testy sędziego ważności (B4 §2/§3). Deterministyczne, bez SITL.

Pozytywne: fixtures B4 (_valid.jsonl + _manifest.json) → VALID, wszystkie kryteria PRE_D §5.
Negatywne: usunięte zdarzenie ⇒ INVALID (trace_complete + nazwa); naruszony próg ⇒ INVALID
z właściwym kryterium; brak manifestu ⇒ aneks_h_valid FAIL. Plus: B3 fixtures są trace-kompletne.
Uruchom: python3 -m pytest tools/test_act_judge.py
"""
from __future__ import annotations
import json
import os
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools import act_judge as J   # noqa: E402

B4 = os.path.join(_HERE, "b4_fixtures")
B3 = os.path.join(_HERE, "b3_fixtures")
ACTS = os.path.join(ROOT, "acts")


def _spec(a):
    return os.path.join(ACTS, f"{a}_spec.yaml")


def _judge_valid(a):
    return J.judge(os.path.join(B4, f"{a}_valid.jsonl"), _spec(a), os.path.join(B4, f"{a}_manifest.json"))


# --- pozytywne ------------------------------------------------------------------
def test_A1_valid():
    v = _judge_valid("A1"); assert v["verdict"] == "VALID", v["violated"]


def test_A2_valid():
    v = _judge_valid("A2"); assert v["verdict"] == "VALID", v["violated"]


def test_A3_valid():
    v = _judge_valid("A3"); assert v["verdict"] == "VALID", v["violated"]


def test_all_pre_d_criteria_present():
    """Każdy akt ma zaimplementowane kryteria PRE_D §5 (nazwy widoczne w werdykcie)."""
    exp = {"A1": {"aneks_h_valid", "trace_complete", "entry_in_dwell_ring", "no_auth_before_token",
                  "observe_after_token_dsafe_ok"},
           "A2": {"aneks_h_valid", "trace_complete", "expire_at_theta_age", "readmit_full_conjunction",
                  "new_token_required"},
           "A3": {"aneks_h_valid", "trace_complete", "refuse_pos_within_015", "touchdown_within_R_E"}}
    for a, names in exp.items():
        v = _judge_valid(a)
        got = {c["name"] for c in v["criteria"]}
        assert names <= got, (a, names - got)


# --- negatywne: usunięte zdarzenie ---------------------------------------------
def test_removed_event_invalid_with_name():
    """Usuń grant (token_issued ALLOW) z A1 → INVALID, trace_complete naruszone, 'grant' w missing."""
    src = open(os.path.join(B4, "A1_valid.jsonl")).read().splitlines()
    kept = [ln for ln in src if not (('"event": "token_issued"' in ln) and ('"decision": "ALLOW"' in ln))]
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "broken.jsonl"); open(p, "w").write("\n".join(kept) + "\n")
        v = J.judge(p, _spec("A1"), os.path.join(B4, "A1_manifest.json"))
        assert v["verdict"] == "INVALID"
        assert "trace_complete" in v["violated"]
        tc = [c for c in v["criteria"] if c["name"] == "trace_complete"][0]
        assert "grant" in tc["detail"]["missing"]


# --- negatywne: naruszony próg -------------------------------------------------
def test_A3_refuse_too_slow_invalid():
    """Przesuń refuse_pos > 0.15 s od denial → INVALID na refuse_pos_within_015."""
    rows = [json.loads(l) for l in open(os.path.join(B4, "A3_valid.jsonl")) if l.strip()]
    for r in rows:                                  # opóźnij POS ticki i event
        if r.get("ev") == "refuse_pos_land":
            r["mono"] = 4.3
        if r.get("t") == "tick" and r.get("reason") == "POS_DEGRADED":
            r["mono"] = r["mono"] + 0.3
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "slow.jsonl")
        open(p, "w").write("\n".join(json.dumps(r) for r in rows) + "\n")
        v = J.judge(p, _spec("A3"), os.path.join(B4, "A3_manifest.json"))
        assert v["verdict"] == "INVALID" and "refuse_pos_within_015" in v["violated"], v


def test_A1_no_auth_after_token_invalid():
    """Gdyby REFUSE(NO_AUTH) padło PO grancie → INVALID na no_auth_before_token."""
    rows = [json.loads(l) for l in open(os.path.join(B4, "A1_valid.jsonl")) if l.strip()]
    for r in rows:
        if r.get("event") == "refuse_no_auth":
            r["t"] = 99.0
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "swap.jsonl")
        open(p, "w").write("\n".join(json.dumps(r) for r in rows) + "\n")
        v = J.judge(p, _spec("A1"), os.path.join(B4, "A1_manifest.json"))
        assert v["verdict"] == "INVALID" and "no_auth_before_token" in v["violated"], v


# --- negatywne: brak manifestu (ANEKS-H) ---------------------------------------
def test_missing_manifest_fails_aneks_h():
    v = J.judge(os.path.join(B4, "A1_valid.jsonl"), _spec("A1"), None)
    assert v["verdict"] == "INVALID" and "aneks_h_valid" in v["violated"]


# --- B3 fixtures są trace-kompletne (dimension structural) ----------------------
def test_b3_fixtures_trace_complete():
    for a in ("A1", "A2", "A3"):
        trace = J.G.load_trace(os.path.join(B3, f"{a}_fixture.jsonl"))
        found = J.G.detect_events(trace, a, __import__("yaml").safe_load(open(_spec(a))))
        missing = [ev for ev in J.G.REQUIRED_EVENTS[a] if ev not in found or found[ev].get("t") is None]
        assert not missing, (a, missing)


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn(); print(f"  PASS  {fn.__name__}")
    print(f"WERDYKT test_act_judge: PASS ({len(fns)}/{len(fns)})")


if __name__ == "__main__":
    _run_all()
