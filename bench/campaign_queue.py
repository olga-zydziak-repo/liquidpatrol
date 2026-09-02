#!/usr/bin/env python3
"""bench/campaign_queue.py — kolejka kampanii blok1/48 z ponowieniami (ANEKS_BENCH-1 C8, PRE §3/D8).

Stan trwały (JSON) współdzielony między bootami. Inicjalizacja z manifestu blok 1: 48 × {scenario_id,
episode_id, attempt=1}. Driver sesji: `pop --n 4` (pending→in_flight) → boot (bench_flight czyta in_flight,
NIE listę rozwiązaną; attempt propagowany do ep_meta) → `record --outdir` (aktualizacja z werdyktów).

Reguły aktualizacji po boocie (per scenariusz in_flight, dopasowanie po scenario_id):
  • ważna próba (V2′)                    → DONE (liczy się PIERWSZA ważna; scenariusz nie wraca)
  • INVALID_START albo V2′-nieważny      → re-append na koniec z attempt+1 (twardy cap attempt ≤ 3)
  • 3 nieważne próby (attempt==3 pada)   → UNRESOLVED (listowany; NIE liczy się do sukcesów ani porażek)
  • brak danych / env (crash, stub)      → re-append na koniec BEZ inkrementu (env nie pali próby, PRE/D8)
`> 4 UNRESOLVED w bloku ⇒ STOP sesji dla CC` (should_stop).

Rdzeń testowalny bez SITL: `record(statuses)` (dict scenario_id→status) i przejścia kolejki.
`record_from_outdir(outdir)` wywodzi statusy z manifestu bench_finalize + zdarzeń invalid_start w trace.
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

CAP = 3                 # twardy cap attempt ≤ 3
UNRESOLVED_STOP = 4     # > 4 UNRESOLVED ⇒ STOP sesji dla CC
VALID, INV_START, INV_V2P, MISSING = "valid", "invalid_start", "invalid_v2p", "missing"


class CampaignQueue:
    def __init__(self, path):
        self.path = path
        self.state = json.load(open(path)) if os.path.exists(path) else None

    # -------- inicjalizacja / trwałość --------
    @classmethod
    def init_from_manifest(cls, path, manifest, block=1):
        eps = [e for e in manifest["episodes"] if e.get("block") == block]
        pending = [{"episode_id": e["episode_id"], "scenario_id": e["scenario_id"], "attempt": 1} for e in eps]
        q = cls.__new__(cls)
        q.path = path
        q.state = {"block": block, "n_total": len(pending), "batches": 0,
                   "pending": pending, "in_flight": [], "done": [], "unresolved": []}
        q.save()
        return q

    def save(self):
        with open(self.path, "w") as f:
            json.dump(self.state, f, indent=2)

    # -------- pop / read --------
    def pop_batch(self, n):
        """pending→in_flight (do n). Stare in_flight (crash bez record) wraca na CZOŁO pending (env-retry)."""
        s = self.state
        if s["in_flight"]:
            s["pending"] = s["in_flight"] + s["pending"]
            s["in_flight"] = []
        batch = s["pending"][:n]
        s["pending"] = s["pending"][n:]
        s["in_flight"] = batch
        s["batches"] += 1
        self.save()
        return batch

    def current_batch(self):
        """Wpisy in_flight (to, co bench_flight ma odlecieć). Nie mutuje."""
        return list(self.state["in_flight"])

    # -------- record --------
    def record(self, statuses):
        """statuses: {scenario_id: valid|invalid_start|invalid_v2p|missing}. Aktualizuje in_flight → done/pending/unresolved."""
        s = self.state
        for entry in s["in_flight"]:
            sid = entry["scenario_id"]
            st = statuses.get(sid, MISSING)
            if st == VALID:
                s["done"].append({**entry, "result": VALID})
            elif st in (INV_START, INV_V2P):
                if entry["attempt"] >= CAP:
                    s["unresolved"].append({**entry, "last": st})
                else:
                    s["pending"].append({"episode_id": entry["episode_id"], "scenario_id": sid,
                                         "attempt": entry["attempt"] + 1})
            else:                                          # MISSING (env/crash) — bez inkrementu
                s["pending"].append({"episode_id": entry["episode_id"], "scenario_id": sid,
                                     "attempt": entry["attempt"]})
        s["in_flight"] = []
        self.save()

    def record_from_outdir(self, outdir):
        """Wywodzi statusy in_flight z manifestu bench_finalize (valid_V2p) + invalid_start w trace."""
        statuses = self.statuses_from_outdir(outdir, [e["scenario_id"] for e in self.state["in_flight"]])
        self.record(statuses)
        return statuses

    @staticmethod
    def statuses_from_outdir(outdir, scenario_ids):
        """Dla podanych scenario_id: valid / invalid_v2p (z manifestu) lub invalid_start (z trace) lub missing."""
        st = {}
        man = os.path.join(outdir, "manifest.json")
        if os.path.exists(man):
            try:
                m = json.load(open(man))
                for ep in m.get("episodes", []):
                    sid = ep.get("scenario_id")
                    if sid in scenario_ids:
                        st[sid] = VALID if ep.get("valid_V2p") else INV_V2P
            except Exception:
                pass
        trace = os.path.join(outdir, "trace.jsonl")
        if os.path.exists(trace):
            try:
                with open(trace) as f:
                    for line in f:
                        if '"invalid_start"' not in line:
                            continue
                        r = json.loads(line)
                        if r.get("ev") == "invalid_start":
                            # invalid_start nie tworzy episode_end → nie ma go w manifeście; oznacz jeśli nierozstrzygnięty
                            sid = _sid_for_episode(outdir, r.get("episode_id"))
                            if sid in scenario_ids and sid not in st:
                                st[sid] = INV_START
            except Exception:
                pass
        for sid in scenario_ids:
            st.setdefault(sid, MISSING)
        return st

    # -------- zapytania --------
    def should_stop(self):
        return len(self.state["unresolved"]) > UNRESOLVED_STOP

    def is_complete(self):
        return not self.state["pending"] and not self.state["in_flight"]

    def summary(self):
        s = self.state
        return {"block": s["block"], "n_total": s["n_total"], "batches": s["batches"],
                "pending": len(s["pending"]), "in_flight": len(s["in_flight"]),
                "done": len(s["done"]), "unresolved": len(s["unresolved"]),
                "unresolved_ids": [e["scenario_id"] for e in s["unresolved"]],
                "should_stop": self.should_stop(), "complete": self.is_complete()}


def _sid_for_episode(outdir, episode_id):
    """scenario_id epizodu — z gt_intruder/trace (episode_start) bo invalid_start loguje tylko episode_id."""
    trace = os.path.join(outdir, "trace.jsonl")
    if episode_id is None or not os.path.exists(trace):
        return None
    with open(trace) as f:
        for line in f:
            if '"episode_start"' in line or '"intruder_start_gate"' in line:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if r.get("episode_id") == episode_id and r.get("scenario_id"):
                    return r["scenario_id"]
    return None


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    pi = sub.add_parser("init"); pi.add_argument("--manifest", required=True); pi.add_argument("--state", required=True); pi.add_argument("--block", type=int, default=1)
    pp = sub.add_parser("pop"); pp.add_argument("--state", required=True); pp.add_argument("--n", type=int, default=4)
    pr = sub.add_parser("record"); pr.add_argument("--state", required=True); pr.add_argument("--outdir", required=True)
    ps = sub.add_parser("status"); ps.add_argument("--state", required=True)
    a = ap.parse_args()
    if a.cmd == "init":
        m = json.load(open(a.manifest))
        q = CampaignQueue.init_from_manifest(a.state, m, block=a.block)
        print(json.dumps(q.summary()))
    elif a.cmd == "pop":
        q = CampaignQueue(a.state)
        batch = q.pop_batch(a.n)
        print(json.dumps(batch))
    elif a.cmd == "record":
        q = CampaignQueue(a.state)
        st = q.record_from_outdir(a.outdir)
        summ = q.summary()
        print(json.dumps({"statuses": st, "summary": summ}))
        if summ["should_stop"]:
            print(f"[campaign_queue] STOP: UNRESOLVED={summ['unresolved']} > {UNRESOLVED_STOP}", file=sys.stderr)
            sys.exit(7)
    elif a.cmd == "status":
        print(json.dumps(CampaignQueue(a.state).summary()))


if __name__ == "__main__":
    main()
