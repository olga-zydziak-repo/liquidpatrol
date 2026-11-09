#!/usr/bin/env python3
"""results/NADIR/s3/tools/nadir_certs_selfcheck.py — selfcheck prowieniencji certów NADIR (PROMPT_NADIR_S3 §R) = wzór
results/KONT/s3/tools/kont_certs_selfcheck.py (nietknięty): kanon r01.proofs.certs_selfcheck.check() + P1/P5/P7/P9_nadir
↔ sha256(r01/proofs/p9_nadir_verify.py). `--prover PATH` podmienia plik provera (protokół oczekiwanej niezgodności).

Uruchom: python3 results/NADIR/s3/tools/nadir_certs_selfcheck.py [--prover PATH]
"""
from __future__ import annotations
import hashlib
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from r01.proofs import certs_selfcheck as CS

NADIR_CERTS = ("P1_nadir.json", "P5_nadir.json", "P7_nadir.json", "P9_nadir.json")


def main():
    prover = os.path.join(ROOT, "r01/proofs/p9_nadir_verify.py")
    if "--prover" in sys.argv:
        prover = sys.argv[sys.argv.index("--prover") + 1]
    actual = hashlib.sha256(open(prover, "rb").read()).hexdigest()
    rows = CS.check()
    for name in NADIR_CERTS:
        rec = json.load(open(os.path.join(CS.CERTS, name))).get("model_sha256")
        rows.append({"cert": name, "prover": os.path.basename(prover), "recorded": rec, "actual": actual,
                     "ok": rec == actual})
    print(f"=== nadir_certs_selfcheck (prover NADIR: {prover}) ===")
    for r in rows:
        tag = "OK  " if r["ok"] else "FAIL"
        print(f"  {tag}  {r['cert']:18s} ← {r['prover']:20s} {str(r.get('actual'))[:16]}…"
              + ("" if r["ok"] else f"  zapisane {str(r.get('recorded'))[:16]}…"))
    bad = [r for r in rows if not r["ok"]]
    print(f"WERDYKT nadir_certs_selfcheck: {'PASS' if not bad else 'FAIL'} ({len(rows) - len(bad)}/{len(rows)} zgodne)")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
