#!/usr/bin/env python3
"""results/DEMO_C/tools/democ_judge.py — werdykty ujęć DEMO-C (PROMPT_DEMO_C §1.1/§5).

Akty 1–2: D6 PEŁNĄ LITERĄ zamrożonego sędziego (import analyze_boot z
results/PERC2/tools/perc2_s2_analyze.py — ten sam przyrząd co S2 nogi PERC2:
GT intruza z MANIFESTU analitycznie, świadek |ned−cmd|_xy>1 m OBOK, sędzia
bench_judge 8ec0fcfb importem) + ważność/breach/REFUSE z manifestu bootu.
Akt 3: kryterium kampanii K2 (trace: denial → refuse(POS_DEGRADED) → touchdown;
breach 0; t_refuse od injektu) — wzór k2_campaign.json.
Wyjście: results/DEMO_C/democ_werdykty.json (NOWY plik; zero dotyku artefaktów PERC2).

Użycie: democ_judge.py <bootdir_akt12> [<bootdir_akt12>...] --akt3 <bootdir>
"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
for p in (ROOT, os.path.join(ROOT, "results", "PERC2", "tools")):
    if p not in sys.path:
        sys.path.insert(0, p)

from perc2_s2_analyze import analyze_boot, iter_jsonl   # przyrząd 1:1 z S2 PERC2

OUTD = os.path.join(ROOT, "results", "DEMO_C")


def akt3_verdict(d):
    evs = {}
    for r in iter_jsonl(os.path.join(d, "trace.jsonl")):
        if r.get("t") == "event":
            evs.setdefault(r.get("ev"), r)
    man = json.load(open(os.path.join(d, "manifest.json")))
    ep = man["episodes"][0]
    t_inj = evs.get("denial", {}).get("sim")
    t_ref = evs.get("refuse", {}).get("sim")
    t_td = evs.get("touchdown", {}).get("sim")
    ok = (t_inj is not None and t_ref is not None and t_td is not None
          and evs["refuse"].get("reason") == "POS_DEGRADED"
          and not ep.get("breach") and ep.get("valid_V2p"))
    return {"scenario_id": ep["scenario_id"], "valid": ep.get("valid_V2p"),
            "breach": ep.get("breach"), "t_inj_sim": t_inj,
            "t_refuse_po_inj_s": (round(t_ref - t_inj, 3) if t_inj and t_ref else None),
            "refuse_reason": evs.get("refuse", {}).get("reason"),
            "t_touchdown_po_inj_s": (round(t_td - t_inj, 3) if t_inj and t_td else None),
            "kryterium_K2": "PASS" if ok else "FAIL",
            "refuse_przed_denialem": None if not t_inj else
                any(True for r in iter_jsonl(os.path.join(d, "trace.jsonl"))
                    if r.get("t") == "event" and r.get("ev") == "refuse" and r.get("sim", 1e18) < t_inj)}


def main():
    args = sys.argv[1:]
    akt3 = None
    if "--akt3" in args:
        i = args.index("--akt3")
        akt3 = args[i + 1]
        args = args[:i] + args[i + 2:]
    out = {"zrodla": "akty 1-2: perc2_s2_analyze.analyze_boot (sedzia FROZEN 8ec0fcfb, "
                     "GT manifest + swiadek OBOK); akt 3: kryterium K2 z trace",
           "akty12": {}, "akt3": None}
    for d in args:
        rows = analyze_boot(d)
        man = json.load(open(os.path.join(d, "manifest.json")))
        pokl = {e["scenario_id"]: e for e in man["episodes"]}
        br = []
        for r in rows:
            p = pokl.get(r["sid"], {})
            br.append({"sid": r["sid"], "valid": p.get("valid_V2p"),
                       "breach": p.get("breach"), "refuse_count": p.get("refuse_count"),
                       "D6_sedzia_manifest_GT": r["sedzia_D6_opisowo"]["success_D6"],
                       "fail_reasons": r["sedzia_D6_opisowo"]["fail_reasons"],
                       "d_min_sedzia": r["sedzia_D6_opisowo"]["d_min_m"],
                       "t_entry": r["sedzia_D6_opisowo"]["t_entry_s"],
                       "D6_pokladowo": p.get("success_D6"), "d_min_pokladowo": p.get("d_min_m"),
                       "swiadek": r["swiadek_erratum"], "t_acq_s": r["t_acq_s"],
                       "kadencja_lotu": r["kadencja_lotu"],
                       "gt_val_p50_m": r["gt_manifest_val_p50_m"]})
        out["akty12"][os.path.basename(d.rstrip("/"))] = br
        for b in br:
            print(f"[{os.path.basename(d)} {b['sid']}] valid={b['valid']} breach={b['breach']} "
                  f"refuse={b['refuse_count']} D6_sedzia={b['D6_sedzia_manifest_GT']} "
                  f"d_min={b['d_min_sedzia']} (pokł. {b['D6_pokladowo']}/{b['d_min_pokladowo']}) "
                  f"świadek={b['swiadek']['n_artefakt']}/{b['swiadek']['n_wierszy']} t_acq={b['t_acq_s']}")
    if akt3:
        out["akt3"] = {os.path.basename(akt3.rstrip("/")): akt3_verdict(akt3)}
        print("[akt3]", json.dumps(out["akt3"]))
    json.dump(out, open(os.path.join(OUTD, "democ_werdykty.json"), "w"), indent=1)
    print("zapisano democ_werdykty.json")


if __name__ == "__main__":
    main()
