#!/usr/bin/env python3
"""tools/b4_fixtures/make_judge_fixtures.py — DETERMINISTYCZNE fixtures dla act_judge (B4 §2/§3).

SYNTETYCZNE trace'y + manifesty per akt, dostrojone do KRYTERIÓW WAŻNOŚCI PRE_D §5 (VALID). Jawnie
oznaczone `"fixture": true` (NIE dowód, NIE pomiar). Bez losowości/zegara → bajt-stabilne.
Różnią się od B3 fixtures (tamte pod snapshot napisów; te pod timing/geometrię sędziego, np. A3 ≤0.15 s).

Uruchom: python3 tools/b4_fixtures/make_judge_fixtures.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = {"t": "schema", "v": 2, "fixture": True}
DRONE = [0.0, 0.0, -10.0]
INTR_RING = [7.86, 0.0, -11.5]     # range3d = 8.00 ∈ [7,9]
INTR_LOW = [7.0, 0.0, -3.0]
CONJ_ON = {"box": True, "central": True, "mti_ok": True}
CONJ_OFF = {"box": False, "central": False, "mti_ok": None}


def tk(k, t, dec, rsn, rule, mode, state, locked, age, conj, intr, pos=None, min_d=None,
       auth_ok=True, seq=-1):
    return {"k": k, "t": round(t, 3), "decision": dec, "reason": rsn, "rule": rule, "mode": mode,
            "state": state, "locked": locked, "age": age, "conj": conj, "intr_ned": intr,
            "pos": pos or DRONE, "min_d": min_d, "auth_ok": auth_ok, "admission_seq": seq}


def manifest(act, world_hash="deadbeef"):
    return {"act": act, "head": "fixture", "world_hash": world_hash, "spec_hash": "fixture",
            "token_gated": True, "trace_schema_v": 2, "contention": "fixture",
            "aneks_h": {"headless": True, "rtf_start": 1.0, "rtf_end": 0.999, "timejump": 0,
                        "ekf_health_hits": 0, "world_hash_matches": True, "trace_complete": True,
                        "valid": True}}


def write(name, rows):
    with open(os.path.join(HERE, name), "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def a1():
    r = [dict(SCHEMA)]; k = 0
    for i in range(2):
        r.append(tk(k, 1.0 + i, "ALLOW", None, "R-P", "PATROL", "PATROL", False, None, CONJ_OFF, None,
                    pos=[float(i), 0.0, -10.0])); k += 1
    # ENTRY (locked, range3d 8.0) + REFUSE(NO_AUTH)
    for i in range(3):
        r.append(tk(k, 6.0 + i, "REFUSE", "NO_AUTH", "R-AUTH", "OBSERVE", "NOAUTH", True, 0.1,
                    CONJ_ON, INTR_RING, auth_ok=False, seq=0)); k += 1
    r.append({"k": k, "t": 8.0, "event": "refuse_no_auth", "admission_seq": 0})
    r.append({"k": k, "t": 8.5, "event": "token_issued", "op": "operator", "admission_seq": 0,
              "decision": "ALLOW", "reason": None})
    for i in range(6):
        r.append(tk(k, 9.0 + i, "ALLOW", None, "R-O", "OBSERVE", "OBSERVING", True, 0.1, CONJ_ON,
                    INTR_RING, min_d=5.40, auth_ok=True, seq=0)); k += 1
    return r


def a2():
    r = [dict(SCHEMA)]; k = 0
    for i in range(2):
        r.append(tk(k, 1.0 + i, "REFUSE", "NO_AUTH", "R-AUTH", "OBSERVE", "NOAUTH", True, 0.1,
                    CONJ_ON, INTR_RING, auth_ok=False, seq=0)); k += 1
    r.append({"k": k, "t": 2.5, "event": "refuse_no_auth", "admission_seq": 0})
    r.append({"k": k, "t": 2.8, "event": "token_issued", "op": "operator", "admission_seq": 0,
              "decision": "ALLOW", "reason": None})
    for i in range(3):
        r.append(tk(k, 3.0 + i, "ALLOW", None, "R-O", "OBSERVE", "OBSERVING", True, 0.1, CONJ_ON,
                    INTR_RING, min_d=5.42, auth_ok=True, seq=0)); k += 1
    # utrata: age rośnie (ZOH) do θ_age, potem EXPIRE
    for i, age in enumerate([1.5, 2.8, 3.2]):
        r.append(tk(k, 6.0 + i, "ALLOW", None, "R-O", "OBSERVE", "OBSERVING", True, age, CONJ_OFF,
                    INTR_LOW, min_d=5.42, auth_ok=True, seq=0)); k += 1
    r.append({"k": k, "t": 9.0, "event": "token_consumed", "admission_seq": 0, "n": 1})
    for i in range(2):
        r.append(tk(k, 9.0 + i, "ALLOW", None, "R-P", "PATROL", "PATROL", False, None, CONJ_OFF,
                    INTR_LOW, seq=0)); k += 1
    # re-ENTRY (admission_seq 1, pełna koniunkcja) + NO_AUTH + grant2 + OBSERVE
    for i in range(2):
        r.append(tk(k, 12.0 + i, "REFUSE", "NO_AUTH", "R-AUTH", "OBSERVE", "NOAUTH", True, 0.1,
                    CONJ_ON, INTR_RING, auth_ok=False, seq=1)); k += 1
    r.append({"k": k, "t": 13.5, "event": "refuse_no_auth", "admission_seq": 1})
    r.append({"k": k, "t": 13.8, "event": "token_issued", "op": "operator", "admission_seq": 1,
              "decision": "ALLOW", "reason": None})
    for i in range(3):
        r.append(tk(k, 15.0 + i, "ALLOW", None, "R-O", "OBSERVE", "OBSERVING", True, 0.1, CONJ_ON,
                    INTR_RING, min_d=5.39, auth_ok=True, seq=1)); k += 1
    return r


def a3():
    r = [{"t": "meta", "scen": "S2", "schema_v": 2, "eps_cap": 9.25, "R_E": 32.0, "fixture": True}]
    tick = 0
    for i, re in enumerate([4.0, 10.0, 16.0]):
        r.append({"t": "tick", "tick": tick, "mono": 1.0 + i, "r_est": re, "margin_R_E": round(32.0 - re, 3),
                  "decision": "ALLOW", "reason": None, "state": "PATROL", "pos": [re, 0.0, -10.0],
                  "dr": False, "descending": False}); tick += 1
    r.append({"t": "event", "mono": 4.0, "ev": "denial_on", "r_est_at_cut": 18.0, "speed_at_cut": 3.0})
    r.append({"t": "event", "mono": 4.09, "ev": "refuse_pos_land"})   # 0.09 s ≤ 0.15
    for i in range(3):
        re = 18.0 + 0.15 * i
        r.append({"t": "tick", "tick": tick, "mono": 4.1 + i, "r_est": round(re, 3),
                  "margin_R_E": round(32.0 - re, 3), "decision": "REFUSE", "reason": "POS_DEGRADED",
                  "state": "POSDEG", "pos": [re, 0.0, -10.0 + 3.0 * i], "dr": True, "descending": True}); tick += 1
    r.append({"t": "event", "mono": 7.5, "ev": "touchdown"})
    r.append({"t": "outcome", "n_pos_enter": 1, "terminal": None})
    return r


def main():
    write("A1_valid.jsonl", a1()); json.dump(manifest("A1"), open(os.path.join(HERE, "A1_manifest.json"), "w"), indent=2)
    write("A2_valid.jsonl", a2()); json.dump(manifest("A2"), open(os.path.join(HERE, "A2_manifest.json"), "w"), indent=2)
    write("A3_valid.jsonl", a3()); json.dump(manifest("A3"), open(os.path.join(HERE, "A3_manifest.json"), "w"), indent=2)
    print("[b4_fixtures] A1/A2/A3 _valid.jsonl + _manifest.json zapisane (fixture, judge-VALID)")


if __name__ == "__main__":
    main()
