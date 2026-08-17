#!/usr/bin/env python3
"""tools/act_judge.py — DEMO-B B4 (PROMPT_D_BUILD_4 §2): SĘDZIA WAŻNOŚCI aktu.

Kryteria ważności z PRE_D §5 implementowane 1:1 (cytat kryterium → warunek). Wejście = trace +
manifest + spec; wyjście = werdykt VALID/INVALID + lista kryteriów (ok/detail/source). ZERO progów
spoza PRE_D §5 / spec / frozen config. „Trace kompletny" = ten sam asert co generator napisów
(gen_subtitles.REQUIRED_EVENTS) — jedno źródło prawdy.

BUDOWANY PRZED ISTNIENIEM JAKIEJKOLWIEK PRÓBY (§2) i FREEZOWANY (hash w ANEKS_D3) — sędzia nie może
ewoluować pod próby (antyselekcja). Zmiana po FREEZE = adnotacja + ratyfikacja Olgi.

Uruchom: python3 tools/act_judge.py <trace.jsonl> <acts/AX_spec.yaml> [manifest.json]
"""
from __future__ import annotations
import json
import math
import os
import sys

import yaml

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools import gen_subtitles as G          # noqa: E402  (jedno źródło: load_trace/detect_events/REQUIRED)
from r01.config import R_E                    # noqa: E402  (frozen obwiednia)
from r02.config_r02 import THETA_AGE_S, D_SAFE_M  # noqa: E402

# Progi ANEKS-H (habitat ważny) — z ANEKS-H / RAPORT_R02/REGATE (RTF ~1.0, timejump 0).
RTF_LO, RTF_HI = 0.97, 1.03
DSAFE_TOL = 0.5                                # min_d ≥ D_safe − 0.5 (config_r02 dsafe_violations)
REFUSE_POS_MAX_S = 0.15                        # PRE_D §5 A3: REFUSE(POS_DEGRADED) ≤ 0.15 s
ENTRY_MODE_MIN, ENTRY_MODE_MAX = 7.0, 9.0     # dwell 7–9 m (PRE_D §5 A1; fallback gdy spec bez band)


def _range3d(pos, intr):
    if not pos or not intr:
        return None
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(pos[:3], intr[:3])))


def _crit(name, ok, detail, source):
    return {"name": name, "ok": bool(ok), "detail": detail, "source": source}


def _aneks_h(manifest, crits):
    """Boot ANEKS-H ważny (PRE_D §5 „boot ANEKS-H ważny"): headless ∧ RTF~1.0 ∧ timejump 0 ∧
    EKF zdrowy ∧ world hash zgodny ∧ trace kompletny."""
    if manifest is None:
        crits.append(_crit("aneks_h_valid", False, "brak manifestu (nie można ocenić ANEKS-H)",
                           "PRE_D §5 / ANEKS-H"))
        return False
    a = manifest.get("aneks_h", {})
    rtf_ok = (isinstance(a.get("rtf_start"), (int, float)) and isinstance(a.get("rtf_end"), (int, float))
              and RTF_LO <= a["rtf_start"] <= RTF_HI and RTF_LO <= a["rtf_end"] <= RTF_HI)
    ok = (bool(a.get("headless")) and rtf_ok and int(a.get("timejump", 1)) == 0
          and int(a.get("ekf_health_hits", 1)) == 0 and bool(a.get("world_hash_matches")))
    crits.append(_crit("aneks_h_valid", ok,
                       {"headless": a.get("headless"), "rtf": [a.get("rtf_start"), a.get("rtf_end")],
                        "timejump": a.get("timejump"), "ekf_health_hits": a.get("ekf_health_hits"),
                        "world_hash_matches": a.get("world_hash_matches")},
                       "PRE_D §5 (boot ANEKS-H ważny); RTF∈[0.97,1.03], timejump 0"))
    return ok


def _trace_complete(trace, act, spec, crits):
    found = G.detect_events(trace, act, spec)
    missing = [ev for ev in G.REQUIRED_EVENTS[act] if ev not in found or found[ev].get("t") is None]
    crits.append(_crit("trace_complete", not missing,
                       {"missing": missing, "required": G.REQUIRED_EVENTS[act]},
                       "PRE_D §5 trace kompletny (asert = gen_subtitles.REQUIRED_EVENTS)"))
    return found, not missing


def judge_A1(trace, spec, found, crits):
    band = spec.get("geometry", {}).get("ring_band_m", [ENTRY_MODE_MIN, ENTRY_MODE_MAX])
    lo, hi = float(band[0]), float(band[1])
    ticks = trace["ticks"]
    # ENTRY w dwell 7–9 m: przy pierwszym locku range3d ∈ [lo,hi]
    entry_t = found.get("entry", {}).get("t")
    entry_rng = None
    prev = False
    for r in ticks:
        lk = bool(r.get("locked"))
        if lk and not prev:
            entry_rng = _range3d(r.get("pos"), r.get("intr_ned")); break
        prev = lk
    crits.append(_crit("entry_in_dwell_ring", entry_rng is not None and lo <= entry_rng <= hi,
                       {"entry_range3d": entry_rng, "band": [lo, hi]},
                       "PRE_D §5 A1 „ENTRY osiągnięte w reżimie dwell 7–9 m"))
    # REFUSE(NO_AUTH) PRZED tokenem
    t_na = found.get("refuse_no_auth", {}).get("t"); t_gr = found.get("grant", {}).get("t")
    crits.append(_crit("no_auth_before_token", t_na is not None and t_gr is not None and t_na < t_gr,
                       {"t_refuse_no_auth": t_na, "t_grant": t_gr},
                       "PRE_D §5 A1 „REFUSE(NO_AUTH) pokazane PRZED tokenem"))
    # po tokenie OBSERVE z 0 naruszeń D_safe
    obs_after = [r for r in ticks if r.get("mode") == "OBSERVE" and r.get("decision") == "ALLOW"
                 and G._tick_time(r) is not None and t_gr is not None and G._tick_time(r) >= t_gr]
    min_ds = [r.get("min_d") for r in obs_after if isinstance(r.get("min_d"), (int, float))]
    dsafe_ok = bool(obs_after) and (not min_ds or min(min_ds) >= D_SAFE_M - DSAFE_TOL)
    crits.append(_crit("observe_after_token_dsafe_ok", dsafe_ok,
                       {"observe_ticks_after_token": len(obs_after),
                        "min_d": (min(min_ds) if min_ds else None), "floor": D_SAFE_M - DSAFE_TOL},
                       "PRE_D §5 A1 „po tokenie OBSERVE z 0 naruszeń D_safe (config_r02 D_safe=5.32)"))


def judge_A2(trace, spec, found, crits):
    ticks = trace["ticks"]
    # EXPIRE na θ_age: expire wykryte ∧ age dobił do θ_age przed nim
    t_exp = found.get("expire", {}).get("t")
    ages = [r.get("age") for r in ticks if isinstance(r.get("age"), (int, float))]
    age_reached = bool(ages) and max(ages) >= THETA_AGE_S * 0.9
    crits.append(_crit("expire_at_theta_age", t_exp is not None and age_reached,
                       {"t_expire": t_exp, "max_age": (max(ages) if ages else None), "theta_age": THETA_AGE_S},
                       "PRE_D §5 A2 „EXPIRE na θ_age (config_r02 θ_age=3.0)"))
    # powrót → re-ENTRY pełną koniunkcją (conj box∧central∧mti_ok przy re-ENTRY, admission_seq→1)
    readmit_full = False; readmit_seq = None
    prev = False
    for r in ticks:
        lk = bool(r.get("locked"))
        if lk and not prev and r.get("admission_seq") == 1:
            c = r.get("conj") or {}
            readmit_full = bool(c.get("box") and c.get("central") and c.get("mti_ok"))
            readmit_seq = r.get("admission_seq"); break
        prev = lk
    crits.append(_crit("readmit_full_conjunction", readmit_full,
                       {"admission_seq": readmit_seq, "conj_at_readmit": "box∧central∧mti_ok"},
                       "PRE_D §5 A2 re-admisja pełną koniunkcją + B1 admission_seq"))
    # nowy token wymagany: grant2 dla epizodu 1 ∧ token ep0 skonsumowany (expire present)
    g2 = found.get("grant2")
    crits.append(_crit("new_token_required", g2 is not None and t_exp is not None,
                       {"t_grant2": (g2 or {}).get("t"), "expire_consumed": t_exp is not None},
                       "PRE_D §5 A2 (per-cel) nowy token wymagany + B1 consume_tokens"))


def judge_A3(trace, spec, found, crits):
    ticks = trace["ticks"]
    # REFUSE(POS_DEGRADED) ≤ 0.15 s od denial
    t_den = found.get("denial", {}).get("t"); t_pos = found.get("refuse_pos", {}).get("t")
    dt = (t_pos - t_den) if (t_den is not None and t_pos is not None) else None
    crits.append(_crit("refuse_pos_within_015", dt is not None and dt <= REFUSE_POS_MAX_S,
                       {"t_denial": t_den, "t_refuse_pos": t_pos, "delta_s": dt, "max": REFUSE_POS_MAX_S},
                       "PRE_D §5 A3 „REFUSE(POS_DEGRADED) ≤ 0.15 s"))
    # touchdown ≤ R_E: touchdown wykryte ∧ r_est w chwili touchdown ≤ R_E
    td = found.get("touchdown"); r_ests = [r.get("r_est") for r in ticks if isinstance(r.get("r_est"), (int, float))]
    td_r = r_ests[-1] if r_ests else None
    crits.append(_crit("touchdown_within_R_E", td is not None and td_r is not None and td_r <= R_E,
                       {"touchdown_seen": td is not None, "touchdown_r_est": td_r, "R_E": R_E},
                       "PRE_D §5 A3 „touchdown ≤ R_E (r01.config R_E=32)"))


JUDGES = {"A1": judge_A1, "A2": judge_A2, "A3": judge_A3}


def judge(trace_path, spec_path, manifest_path=None):
    trace = G.load_trace(trace_path)
    spec = yaml.safe_load(open(spec_path))
    act = spec["act"]
    manifest = json.load(open(manifest_path)) if manifest_path and os.path.exists(manifest_path) else None
    crits = []
    _aneks_h(manifest, crits)
    found, complete = _trace_complete(trace, act, spec, crits)
    if complete:                                 # kryteria aktu tylko gdy trace kompletny (inaczej brak zdarzeń)
        JUDGES[act](trace, spec, found, crits)
    valid = all(c["ok"] for c in crits)
    return {"act": act, "verdict": "VALID" if valid else "INVALID",
            "criteria": crits, "violated": [c["name"] for c in crits if not c["ok"]]}


def main():
    if len(sys.argv) < 3:
        print("użycie: act_judge.py <trace> <spec> [manifest]"); sys.exit(2)
    manifest = sys.argv[3] if len(sys.argv) > 3 else None
    v = judge(sys.argv[1], sys.argv[2], manifest)
    print(f"=== SĘDZIA {v['act']}: {v['verdict']} ===")
    for c in v["criteria"]:
        print(f"  {'OK  ' if c['ok'] else 'FAIL'} {c['name']}: {c['detail']}")
    if v["violated"]:
        print(f"NARUSZONE: {v['violated']}")
    sys.exit(0 if v["verdict"] == "VALID" else 1)


if __name__ == "__main__":
    main()
