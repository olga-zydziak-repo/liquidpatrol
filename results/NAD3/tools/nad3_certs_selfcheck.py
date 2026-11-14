#!/usr/bin/env python3
"""results/NAD3/tools/nad3_certs_selfcheck.py — selfcheck prowieniencji certów NADIR-III (PROMPT_NAD3_S1 §3) = wzór
results/NAD2/tools/nad2_certs_selfcheck.py (nietknięty): kanon r01.proofs.certs_selfcheck.check() + P1/P5/P7/P9_nad2 ↔
sha256(r01/proofs/p9_nad2_verify.py) + P5/P7/P9_nad3 ↔ sha256(r01/proofs/p9_nad3_verify.py) + tabele punktów NAD3
(results/NAD3/s1/freeze_U_P{1,2,3}.json) wczytane przez osłonę (r03/nadir_shield.nad3_tabela: sha, stałe, próg) z sumą zapisaną
w P9_nad3. `--prover PATH` podmienia plik provera NAD3 (protokół oczekiwanej niezgodności).

Uruchom: python3 results/NAD3/tools/nad3_certs_selfcheck.py [--prover PATH]
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

PARY = (("r01/proofs/p9_nad2_verify.py", ("P1_nad2.json", "P5_nad2.json", "P7_nad2.json", "P9_nad2.json")),
        ("r01/proofs/p9_nad3_verify.py", ("P5_nad3.json", "P7_nad3.json", "P9_nad3.json")))


def main():
    rows = CS.check()
    for prover, certs in PARY:
        p = os.path.join(ROOT, prover)
        if prover.endswith("p9_nad3_verify.py") and "--prover" in sys.argv:
            p = sys.argv[sys.argv.index("--prover") + 1]
        actual = hashlib.sha256(open(p, "rb").read()).hexdigest()
        for name in certs:
            cp = os.path.join(CS.CERTS, name)
            rec = json.load(open(cp)).get("model_sha256") if os.path.exists(cp) else None
            rows.append({"cert": name, "prover": os.path.basename(p), "recorded": rec, "actual": actual, "ok": rec == actual})
    tab = NS.nad2_tabela_check(ROOT)
    rows.append({"cert": "tabela_U_nad2", "prover": "freeze_U.json", "recorded": NS.NAD2_TABELA_SHA256, "actual": str(tab),
                 "ok": all(tab.values())})
    p9 = json.load(open(os.path.join(CS.CERTS, "P9_nad3.json"))) if os.path.exists(os.path.join(CS.CERTS, "P9_nad3.json")) else {}
    for punkt in ("P1", "P2", "P3"):
        path = os.path.join(ROOT, f"results/NAD3/s1/freeze_U_{punkt}.json")
        rec = ((p9.get("tabele") or {}).get(punkt) or {}).get("tabela_sha256")
        try:
            T = NS.nad3_tabela(path, rec)
            rows.append({"cert": f"tabela_U_nad3_{punkt}", "prover": os.path.basename(path), "recorded": rec, "actual": T["sha"], "ok": True})
        except NS.NadirStartError as e:
            rows.append({"cert": f"tabela_U_nad3_{punkt}", "prover": os.path.basename(path), "recorded": rec, "actual": f"kod {e.kod}",
                         "ok": False})
    print("=== nad3_certs_selfcheck ===")
    for r in rows:
        tag = "OK  " if r["ok"] else "FAIL"
        print(f"  {tag}  {r['cert']:20s} ← {r['prover']:20s} {str(r.get('actual'))[:16]}…"
              + ("" if r["ok"] else f"  zapisane {str(r.get('recorded'))[:16]}…"))
    bad = [r for r in rows if not r["ok"]]
    print(f"WERDYKT nad3_certs_selfcheck: {'PASS' if not bad else 'FAIL'} ({len(rows) - len(bad)}/{len(rows)} zgodne)")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
