#!/usr/bin/env python3
"""bench/paired_analyze.py — analiza parowana lotów sieci (PROMPT_NET_FLY N-F1b, PRE_NET N7).

Pary PER SCENARIUSZ (ziarna 1–4, te same co mianownik ławki):
  - sieć↔egzekutor: D6 sieci (loty poz.4) vs D6 egzekutora (kampania ławki blok 1).
  - NCP↔MLP: D6 obu ramion.
Zestawienia zgodne/niezgodne (BEZ języka istotności — N7, zakaz klasy K1). Licznik REFUSE per ramię
z przyczynami z trace (sekcja tezy: „osłona zawiera zły kontroler", bez limitu STOP).

Rdzeń czysty (dict in/out) — testowalny bez lotów. Loadery czytają manifesty/trace gdy dostępne.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def pair(a, b):
    """a,b = dict scenario_id→bool(D6). Zwraca zgodność parowaną na WSPÓLNYCH scenariuszach.
    concordant = oba TRUE lub oba FALSE; discordant = różne (z kierunkiem a_only_pass / b_only_pass)."""
    common = sorted(set(a) & set(b))
    conc = disc = a_only = b_only = 0
    pairs = []
    for sid in common:
        av, bv = bool(a[sid]), bool(b[sid])
        if av == bv:
            conc += 1
        else:
            disc += 1
            if av and not bv:
                a_only += 1
            else:
                b_only += 1
        pairs.append({"scenario_id": sid, "a": av, "b": bv, "concord": av == bv})
    return {"n": len(common), "concordant": conc, "discordant": disc,
            "a_only_pass": a_only, "b_only_pass": b_only,
            "only_in_a": sorted(set(a) - set(b)), "only_in_b": sorted(set(b) - set(a)),
            "pairs": pairs}


def refuse_ledger(episode_records):
    """episode_records = lista {scenario_id, refuse_events:[{t,reason}]}. Zwraca licznik REFUSE per przyczyna
    + lista zdarzeń (czas, przyczyna, scenariusz). Bez limitu STOP — pomiar tezy (N7)."""
    events = []
    by_reason = {}
    for r in episode_records:
        for e in r.get("refuse_events", []):
            events.append({"scenario_id": r["scenario_id"], "t": e.get("t"), "reason": e.get("reason")})
            by_reason[e.get("reason")] = by_reason.get(e.get("reason"), 0) + 1
    return {"n_refuse": len(events), "by_reason": by_reason, "events": events}


# --------------------------- loadery danych rzeczywistych ---------------------------
def oracle_d6_block1():
    """D6 egzekutora per scenariusz ziaren 1–4 (pierwsza ważna próba, kampania ławki blok 1).
    Zwraca dict scenario_id→bool. Źródło: net.d0_dataset.resolve_first_valid (success_D6)."""
    from net.d0_dataset import resolve_first_valid
    first = resolve_first_valid()
    return {sid: bool(v["success_D6"]) for sid, v in first.items()
            if v["seed"] in (1, 2, 3, 4)}


def net_d6(arm, fly_dir=None):
    """D6 sieci per scenariusz z manifestów lotów poz.4 (results/NET/FLY/<arm>/boot*/manifest.json).
    Pierwsza ważna (V2′) próba. Zwraca dict scenario_id→bool. Pusty gdy brak lotów (build)."""
    import glob
    fly_dir = fly_dir or os.path.join(ROOT, "results", "NET", "FLY", arm)
    out = {}
    for mp in sorted(glob.glob(os.path.join(fly_dir, "boot*", "manifest.json"))):
        m = json.load(open(mp))
        for ep in sorted(m.get("episodes", []), key=lambda e: e.get("attempt", 0)):
            sid = ep.get("scenario_id")
            if ep.get("valid_V2p") and sid not in out:
                out[sid] = bool(ep.get("success_D6"))
    return out


def refuse_from_traces(arm, fly_dir=None):
    """REFUSE-ledger z trace lotów ramienia (zdarzenia 'refuse' z reason)."""
    import glob
    fly_dir = fly_dir or os.path.join(ROOT, "results", "NET", "FLY", arm)
    recs = {}
    for tp in sorted(glob.glob(os.path.join(fly_dir, "boot*", "trace.jsonl"))):
        for line in open(tp):
            if '"refuse"' not in line:
                continue
            try:
                e = json.loads(line)
            except Exception:
                continue
            if e.get("ev") == "refuse":
                sid = e.get("scenario_id") or f"ep{e.get('episode_id')}"
                recs.setdefault(sid, {"scenario_id": sid, "refuse_events": []})
                recs[sid]["refuse_events"].append({"t": e.get("sim") or e.get("t"), "reason": e.get("reason")})
    return refuse_ledger(list(recs.values()))


if __name__ == "__main__":
    orc = oracle_d6_block1()
    print(f"egzekutor D6 (ziarna 1-4): {sum(orc.values())}/{len(orc)}")
    for arm in ("ncp", "mlp"):
        nd = net_d6(arm)
        print(f"{arm}: {len(nd)} scenariuszy z lotów (0 = brak, build)")
