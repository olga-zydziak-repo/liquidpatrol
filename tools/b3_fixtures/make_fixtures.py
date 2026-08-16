#!/usr/bin/env python3
"""tools/b3_fixtures/make_fixtures.py — DETERMINISTYCZNE golden fixtures dla gen_subtitles (B3 §3).

Emituje SYNTETYCZNE trace'y per klasa aktu (JAWNIE oznaczone `"fixture": true` w wierszu schema —
NIE dowód, nie pomiar). Odzwierciedlają schemat trace v2 (r02: tick z kluczem k; r03: t=="tick").
Geometria intruza NED tak, by range3d(drone,intruz) ∈ [7,9] podczas OBSERVE (koperta scharakteryzowana).
Bez losowości/zegara → bajt-stabilne (snapshot testy).

Uruchom: python3 tools/b3_fixtures/make_fixtures.py   → A1_fixture.jsonl, A2_fixture.jsonl, A3_fixture.jsonl
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = {"t": "schema", "v": 2, "fixture": True,
          "tick_fields": ["k", "t", "decision", "reason", "rule", "mode", "state", "locked", "age",
                          "conj", "intr_ned", "pos", "min_d", "auth_ok", "admission_seq"]}
DRONE = [0.0, 0.0, -10.0]                      # NED dwell
INTR_RING = [7.86, 0.0, -11.5]                # NED; range3d = sqrt(7.86^2+1.5^2)=8.00
INTR_LOW = [7.0, 0.0, -3.0]                    # nisko/clutter (przed/po) — poza kopertą
CONJ_ON = {"box": True, "central": True, "mti_ok": True}
CONJ_OFF = {"box": False, "central": False, "mti_ok": None}


def tick(k, t, decision, reason, rule, mode, state, locked, age, conj, intr, pos=None,
         min_d=None, auth_ok=True, seq=-1):
    return {"k": k, "t": round(t, 3), "decision": decision, "reason": reason, "rule": rule,
            "mode": mode, "state": state, "locked": locked, "age": age, "conj": conj,
            "intr_ned": intr, "pos": pos or DRONE, "min_d": min_d, "auth_ok": auth_ok,
            "admission_seq": seq}


def write(name, rows):
    path = os.path.join(HERE, name)
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return path


def a1():
    r = [dict(SCHEMA)]
    k = 0
    # patrol/transit (poza kopertą, brak locka)
    for i in range(3):
        r.append(tick(k, 1.0 + i, "ALLOW", None, "R-P", "PATROL", "PATROL", False, None,
                      CONJ_OFF, None, pos=[float(i), 0.0, -10.0])); k += 1
    # dwell approach (intruz w kopercie, jeszcze streak < k)
    for i in range(2):
        r.append(tick(k, 4.0 + i, "ALLOW", None, "R-P", "PATROL", "PATROL", False, 0.1,
                      CONJ_ON, INTR_RING)); k += 1
    # ENTRY + REFUSE(NO_AUTH) (locked, mode OBSERVE żądany, auth_ok False)
    for i in range(3):
        r.append(tick(k, 6.0 + i, "REFUSE", "NO_AUTH", "R-AUTH", "OBSERVE", "NOAUTH", True, 0.1,
                      CONJ_ON, INTR_RING, auth_ok=False, seq=0)); k += 1
    r.append({"k": k, "t": 8.0, "event": "refuse_no_auth", "admission_seq": 0})
    # grant
    r.append({"k": k, "t": 8.5, "event": "token_issued", "op": "operator", "admission_seq": 0,
              "decision": "ALLOW", "reason": None})
    # OBSERVE (claim: range3d 8.0 ∈ [7,9], min_d ≥ D_safe-0.5)
    for i in range(6):
        r.append(tick(k, 9.0 + i, "ALLOW", None, "R-O", "OBSERVE", "OBSERVING", True, 0.1,
                      CONJ_ON, INTR_RING, min_d=5.40, auth_ok=True, seq=0)); k += 1
    return r


def a2():
    r = [dict(SCHEMA)]
    k = 0
    for i in range(2):
        r.append(tick(k, 1.0 + i, "ALLOW", None, "R-P", "PATROL", "PATROL", False, None,
                      CONJ_OFF, None, pos=[float(i), 0.0, -10.0])); k += 1
    # ep0 ENTRY + NO_AUTH + grant + OBSERVE
    for i in range(2):
        r.append(tick(k, 4.0 + i, "REFUSE", "NO_AUTH", "R-AUTH", "OBSERVE", "NOAUTH", True, 0.1,
                      CONJ_ON, INTR_RING, auth_ok=False, seq=0)); k += 1
    r.append({"k": k, "t": 5.5, "event": "refuse_no_auth", "admission_seq": 0})
    r.append({"k": k, "t": 5.8, "event": "token_issued", "op": "operator", "admission_seq": 0,
              "decision": "ALLOW", "reason": None})
    for i in range(3):
        r.append(tick(k, 6.0 + i, "ALLOW", None, "R-O", "OBSERVE", "OBSERVING", True, 0.1,
                      CONJ_ON, INTR_RING, min_d=5.42, auth_ok=True, seq=0)); k += 1
    # EXPIRE (intruz odlatuje, token skonsumowany, locked False)
    r.append({"k": k, "t": 9.5, "event": "token_consumed", "admission_seq": 0, "n": 1})
    for i in range(2):
        r.append(tick(k, 10.0 + i, "ALLOW", None, "R-P", "PATROL", "PATROL", False, None,
                      CONJ_OFF, INTR_LOW, seq=0)); k += 1
    # powrót → re-ENTRY (admission_seq 1) + NO_AUTH + grant2 + OBSERVE
    for i in range(2):
        r.append(tick(k, 13.0 + i, "REFUSE", "NO_AUTH", "R-AUTH", "OBSERVE", "NOAUTH", True, 0.1,
                      CONJ_ON, INTR_RING, auth_ok=False, seq=1)); k += 1
    r.append({"k": k, "t": 14.5, "event": "refuse_no_auth", "admission_seq": 1})
    r.append({"k": k, "t": 14.8, "event": "token_issued", "op": "operator", "admission_seq": 1,
              "decision": "ALLOW", "reason": None})
    for i in range(3):
        r.append(tick(k, 16.0 + i, "ALLOW", None, "R-O", "OBSERVE", "OBSERVING", True, 0.1,
                      CONJ_ON, INTR_RING, min_d=5.39, auth_ok=True, seq=1)); k += 1
    return r


def a3():
    # format r03: meta + tick (t=="tick") + event (ev=...)
    r = [{"t": "meta", "scen": "S2", "schema_v": 2, "eps_cap": 9.25, "R_E": 32.0, "fixture": True}]
    tk = 0
    # patrol outbound (r_est rośnie do triggera 18)
    for i, re in enumerate([4.0, 10.0, 16.0]):
        r.append({"t": "tick", "tick": tk, "mono": 1.0 + i, "r_est": re, "margin_R_E": round(32.0 - re, 3),
                  "decision": "ALLOW", "reason": None, "state": "PATROL",
                  "pos": [re, 0.0, -10.0], "dr": False, "descending": False}); tk += 1
    # denial na r_est≈18
    r.append({"t": "event", "mono": 4.0, "ev": "denial_on", "r_est_at_cut": 18.0, "speed_at_cut": 3.0})
    # REFUSE(POS_DEGRADED) + descent (r_est ~const, margin ~14)
    r.append({"t": "event", "mono": 4.1, "ev": "refuse_pos_land"})
    for i in range(3):
        re = 18.0 + 0.2 * i
        r.append({"t": "tick", "tick": tk, "mono": 4.2 + i, "r_est": round(re, 3),
                  "margin_R_E": round(32.0 - re, 3), "decision": "REFUSE", "reason": "POS_DEGRADED",
                  "state": "POSDEG", "pos": [re, 0.0, -10.0 + 3.0 * i], "dr": True, "descending": True}); tk += 1
    r.append({"t": "event", "mono": 7.5, "ev": "touchdown"})
    r.append({"t": "outcome", "n_pos_enter": 1, "terminal": None})
    return r


def main():
    write("A1_fixture.jsonl", a1())
    write("A2_fixture.jsonl", a2())
    write("A3_fixture.jsonl", a3())
    print("[fixtures] A1/A2/A3_fixture.jsonl zapisane (deterministyczne, oznaczone fixture)")


if __name__ == "__main__":
    main()
