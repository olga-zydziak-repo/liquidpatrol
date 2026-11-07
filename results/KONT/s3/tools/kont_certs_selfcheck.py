#!/usr/bin/env python3
"""results/KONT/s3/tools/kont_certs_selfcheck.py — selfcheck prowieniencji WSZYSTKICH certów (PROMPT_KONT_S3 §2).

Kanon: r01.proofs.certs_selfcheck.check() (FROZEN, 9 certów, bez zmian). KONT: P1_kont, P5_kont, P7_kont, P9_kont
↔ sha256(r01/proofs/p9_kont_verify.py). `--prover PATH` podmienia plik provera KONT (protokół oczekiwanej
niezgodności: kopia z dopiskiem ⇒ oczekiwany FAIL czterech certów KONT, kanon bez zmian).

Uruchom: python3 results/KONT/s3/tools/kont_certs_selfcheck.py [--prover PATH]
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

KONT_CERTS = ("P1_kont.json", "P5_kont.json", "P7_kont.json", "P9_kont.json")


def main():
    prover = os.path.join(ROOT, "r01/proofs/p9_kont_verify.py")
    if "--prover" in sys.argv:
        prover = sys.argv[sys.argv.index("--prover") + 1]
    actual = hashlib.sha256(open(prover, "rb").read()).hexdigest()
    rows = CS.check()
    for name in KONT_CERTS:
        rec = json.load(open(os.path.join(CS.CERTS, name))).get("model_sha256")
        rows.append({"cert": name, "prover": os.path.basename(prover), "recorded": rec, "actual": actual,
                     "ok": rec == actual})
    print(f"=== kont_certs_selfcheck (prover KONT: {prover}) ===")
    for r in rows:
        tag = "OK  " if r["ok"] else "FAIL"
        print(f"  {tag}  {r['cert']:18s} ← {r['prover']:20s} {str(r.get('actual'))[:16]}…"
              + ("" if r["ok"] else f"  zapisane {str(r.get('recorded'))[:16]}…"))
    bad = [r for r in rows if not r["ok"]]
    print(f"WERDYKT kont_certs_selfcheck: {'PASS' if not bad else 'FAIL'} ({len(rows) - len(bad)}/{len(rows)} zgodne)")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
