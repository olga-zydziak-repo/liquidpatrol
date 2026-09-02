#!/usr/bin/env python3
"""bench/tests_campaign_queue.py — kolejka kampanii bez SITL: przejścia (valid/invalid_start/invalid_v2p/
requeue/cap), UNRESOLVED, STOP >4, propagacja attempt, roll-up campaign."""
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from bench import scenarios as S
from bench.campaign_queue import CampaignQueue, CAP, UNRESOLVED_STOP
from bench.campaign_analyze import aggregate_campaign


def _q(td):
    m = S.gen_manifest()
    return CampaignQueue.init_from_manifest(os.path.join(td, "q.json"), m), m


def test_init_48_attempt1():
    with tempfile.TemporaryDirectory() as td:
        q, m = _q(td)
        s = q.summary()
        assert s["n_total"] == 48 and s["pending"] == 48
        assert all(e["attempt"] == 1 for e in q.state["pending"])
        assert q.state["pending"][0]["episode_id"] == q.state["pending"][0]["episode_id"]  # ma episode_id


def test_pop_moves_to_in_flight():
    with tempfile.TemporaryDirectory() as td:
        q, m = _q(td)
        b = q.pop_batch(4)
        assert len(b) == 4 and len(q.state["in_flight"]) == 4 and len(q.state["pending"]) == 44
        # reload z dysku: trwałość
        q2 = CampaignQueue(q.path)
        assert len(q2.state["in_flight"]) == 4


def test_valid_done_first_valid_counts():
    with tempfile.TemporaryDirectory() as td:
        q, m = _q(td)
        b = q.pop_batch(4)
        sids = [e["scenario_id"] for e in b]
        q.record({sids[0]: "valid", sids[1]: "valid", sids[2]: "valid", sids[3]: "valid"})
        assert len(q.state["done"]) == 4 and len(q.state["pending"]) == 44 and not q.state["in_flight"]
        assert all(d["result"] == "valid" for d in q.state["done"])


def test_invalid_requeue_attempt_increment():
    with tempfile.TemporaryDirectory() as td:
        q, m = _q(td)
        b = q.pop_batch(4)
        sid0 = b[0]["scenario_id"]
        q.record({sid0: "invalid_start", b[1]["scenario_id"]: "invalid_v2p",
                  b[2]["scenario_id"]: "valid", b[3]["scenario_id"]: "valid"})
        # dwa nieważne wracają na KONIEC z attempt 2
        req = [e for e in q.state["pending"] if e["scenario_id"] in (sid0, b[1]["scenario_id"])]
        assert len(req) == 2 and all(e["attempt"] == 2 for e in req)
        assert q.state["pending"][-1]["scenario_id"] in (sid0, b[1]["scenario_id"])   # na koniec
        assert len(q.state["done"]) == 2


def test_cap_three_invalid_then_unresolved():
    with tempfile.TemporaryDirectory() as td:
        q, m = _q(td)
        target = None
        # goń jeden scenariusz przez 3 nieważne próby
        for expected_attempt in (1, 2, 3):
            # popni aż target (pierwszy raz dowolny) znajdzie się w in_flight
            b = q.pop_batch(4)
            if target is None:
                target = b[0]["scenario_id"]
            # jeśli target nie w tej paczce, oznacz wszystkie valid i popni dalej aż trafi
            while target not in [e["scenario_id"] for e in q.state["in_flight"]]:
                q.record({e["scenario_id"]: "valid" for e in q.state["in_flight"]})
                b = q.pop_batch(4)
            tgt_entry = [e for e in q.state["in_flight"] if e["scenario_id"] == target][0]
            assert tgt_entry["attempt"] == expected_attempt, (expected_attempt, tgt_entry)
            st = {e["scenario_id"]: ("invalid_v2p" if e["scenario_id"] == target else "valid")
                  for e in q.state["in_flight"]}
            q.record(st)
        # po 3. nieważnej: UNRESOLVED, brak attempt 4 nigdzie
        assert target in [e["scenario_id"] for e in q.state["unresolved"]]
        assert all(e["attempt"] <= CAP for e in q.state["pending"] + q.state["unresolved"] + q.state["done"])
        assert target not in [e["scenario_id"] for e in q.state["pending"]]


def test_missing_requeue_no_increment():
    """Brak danych/env (crash) → re-append BEZ inkrementu (nie pali próby)."""
    with tempfile.TemporaryDirectory() as td:
        q, m = _q(td)
        b = q.pop_batch(4)
        sid0 = b[0]["scenario_id"]
        q.record({})                                        # zero statusów = wszystkie MISSING
        assert len(q.state["pending"]) == 48 and not q.state["done"] and not q.state["unresolved"]
        assert all(e["attempt"] == 1 for e in q.state["pending"])


def test_stale_in_flight_returns_to_front_on_pop():
    with tempfile.TemporaryDirectory() as td:
        q, m = _q(td)
        b1 = q.pop_batch(4)
        # crash bez record → drugi pop: stare in_flight wraca na CZOŁO
        b2 = q.pop_batch(4)
        assert [e["scenario_id"] for e in b2] == [e["scenario_id"] for e in b1]


def test_should_stop_over_4_unresolved():
    with tempfile.TemporaryDirectory() as td:
        q, m = _q(td)
        # ręcznie: 5 unresolved > 4 → STOP
        q.state["unresolved"] = [{"scenario_id": f"x{i}", "episode_id": i, "attempt": 3} for i in range(5)]
        assert q.should_stop() is True
        q.state["unresolved"] = q.state["unresolved"][:4]
        assert q.should_stop() is False


def test_aggregate_campaign_first_valid_and_unresolved():
    # manifesty bench_finalize (syntetyczne): scenariusz A ważny na 2. próbie (1. invalid), B nigdy ważny (unresolved)
    manifests = [
        {"episodes": [
            {"scenario_id": "cA", "attempt": 1, "valid_V2p": False, "success_D6": False},
            {"scenario_id": "cB", "attempt": 1, "valid_V2p": False, "success_D6": False},
            {"scenario_id": "cC", "attempt": 1, "valid_V2p": True, "success_D6": True}]},
        {"episodes": [
            {"scenario_id": "cA", "attempt": 2, "valid_V2p": True, "success_D6": False},   # ważny ale D6 fail
            {"scenario_id": "cB", "attempt": 2, "valid_V2p": False, "success_D6": False}]},
    ]
    qstate = {"unresolved": [{"scenario_id": "cB"}]}
    agg = aggregate_campaign(manifests, queue_state=qstate)
    assert agg["n_resolved"] == 2 and agg["n_success"] == 1                 # cC sukces, cA ważny-ale-fail
    assert agg["unresolved_ids"] == ["cB"] and agg["n_unresolved"] == 1
    assert agg["resolved_first_valid"]["cA"]["attempt"] == 2               # PIERWSZA ważna = 2. próba
    assert agg["resolved_first_valid"]["cC"]["success_D6"] is True


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_") and callable(f):
            f(); print(f"OK {n}")
    print("tests_campaign_queue: ALL PASS")
