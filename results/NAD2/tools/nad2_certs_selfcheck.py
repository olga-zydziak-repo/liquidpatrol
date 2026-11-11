#!/usr/bin/env python3
"""results/NAD2/tools/nad2_certs_selfcheck.py — selfcheck prowieniencji certów NADIR-II (PROMPT_NAD2_S1 §R) = wzór
results/NADIR/s3/tools/nadir_certs_selfcheck.py (nietknięty): kanon r01.proofs.certs_selfcheck.check() + P1/P5/P7/P9_nadir
↔ p9_nadir_verify.py + P1/P5/P7/P9_nad2 ↔ sha256(r01/proofs/p9_nad2_verify.py) + zgodność stałych tabeli osłony z freeze_U.json.
`--prover PATH` podmienia plik provera NAD2 (protokół oczekiwanej niezgodności).

Uruchom: python3 results/NAD2/tools/nad2_certs_selfcheck.py [--prover PATH]
"""
from __future__ import annotations
import hashlib
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from r01.proofs import certs_selfcheck as CS
from r03 import nadir_shield as NS

PARY = (("r01/proofs/p9_nadir_verify.py", ("P1_nadir.json", "P5_nadir.json", "P7_nadir.json", "P9_nadir.json")),
        ("r01/proofs/p9_nad2_verify.py", ("P1_nad2.json", "P5_nad2.json", "P7_nad2.json", "P9_nad2.json")))


def main():
    rows = CS.check()
    for prover, certs in PARY:
        p = os.path.join(ROOT, prover)
        if prover.endswith("p9_nad2_verify.py") and "--prover" in sys.argv:
            p = sys.argv[sys.argv.index("--prover") + 1]
        actual = hashlib.sha256(open(p, "rb").read()).hexdigest()
        for name in certs:
            rec = json.load(open(os.path.join(CS.CERTS, name))).get("model_sha256")
            rows.append({"cert": name, "prover": os.path.basename(p), "recorded": rec, "actual": actual, "ok": rec == actual})
    tab = NS.nad2_tabela_check(ROOT)
    rows.append({"cert": "tabela_U", "prover": "freeze_U.json", "recorded": NS.NAD2_TABELA_SHA256, "actual": str(tab), "ok": all(tab.values())})
    print("=== nad2_certs_selfcheck ===")
    for r in rows:
        tag = "OK  " if r["ok"] else "FAIL"
        print(f"  {tag}  {r['cert']:18s} ← {r['prover']:20s} {str(r.get('actual'))[:16]}…"
              + ("" if r["ok"] else f"  zapisane {str(r.get('recorded'))[:16]}…"))
    bad = [r for r in rows if not r["ok"]]
    print(f"WERDYKT nad2_certs_selfcheck: {'PASS' if not bad else 'FAIL'} ({len(rows) - len(bad)}/{len(rows)} zgodne)")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
