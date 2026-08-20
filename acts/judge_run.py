#!/usr/bin/env python3
"""acts/judge_run.py — wrapper sędziego: woła FROZEN `tools/act_judge.judge` (sha 79b1e936, SR-M1 — NIE
modyfikowany) i zapisuje strukturalny `verdict.json` do artefaktów próby (ANEKS_D6 §4). Echo sha sędziego.

Uruchom: python3 -m acts.judge_run <trace> <spec> <manifest> [--out verdict.json]
"""
from __future__ import annotations
import argparse, hashlib, json, os, sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trace"); ap.add_argument("spec"); ap.add_argument("manifest")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    jpath = os.path.join(root, "tools", "act_judge.py")
    jsha = hashlib.sha256(open(jpath, "rb").read()).hexdigest()
    assert jsha.startswith("79b1e936"), f"SĘDZIA ZMIENIONY! sha={jsha[:16]} (SR-M1 naruszone)"
    sys.path.insert(0, root)
    from tools import act_judge as J
    v = J.judge(args.trace, args.spec, args.manifest if os.path.exists(args.manifest) else None)
    v["judge_sha256"] = jsha
    out = args.out or os.path.join(os.path.dirname(args.manifest), "verdict.json")
    json.dump(v, open(out, "w"), indent=2, ensure_ascii=False)
    print(f"=== SĘDZIA {v['act']}: {v['verdict']} (judge {jsha[:16]}…) ===")
    for c in v["criteria"]:
        print(f"  {'OK  ' if c['ok'] else 'FAIL'} {c['name']}: {c['detail']}")
    if v["violated"]:
        print(f"NARUSZONE: {v['violated']}")
    print(f"→ verdict.json: {out}")
    sys.exit(0 if v["verdict"] == "VALID" else 1)


if __name__ == "__main__":
    main()
