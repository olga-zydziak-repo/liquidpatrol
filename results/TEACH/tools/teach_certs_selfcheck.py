#!/usr/bin/env python3
"""results/TEACH/tools/teach_certs_selfcheck.py — selfcheck prowieniencji certów TEACH (PROMPT_TEACH_S1 §3) = KOPIA
results/NAD3/tools/nad3_certs_selfcheck.py (nietknięty) ze zmianami oznaczonymi „TEACH:”: + P5/P7/P9_teach ↔
sha256(r01/proofs/p9_teach_verify.py) + tabela TEACH (results/TEACH/s1/freeze_U_TEACH.json) wczytana przez osłonę
(r03/nadir_shield.nad3_tabela: sha, stałe, próg) z sumą zapisaną w P9_teach. Certy i tabele NAD2 / NAD3 jak w oryginale.
`--prover PATH` podmienia plik provera TEACH (protokół oczekiwanej niezgodności).

Uruchom: python3 results/TEACH/tools/teach_certs_selfcheck.py [--prover PATH]
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
        ("r01/proofs/p9_nad3_verify.py", ("P5_nad3.json", "P7_nad3.json", "P9_nad3.json")),
        ("r01/proofs/p9_teach_verify.py", ("P5_teach.json", "P7_teach.json", "P9_teach.json")))      # TEACH


def main():
    rows = CS.check()
    for prover, certs in PARY:
        p = os.path.join(ROOT, prover)
        if prover.endswith("p9_teach_verify.py") and "--prover" in sys.argv:                          # TEACH
            p = sys.argv[sys.argv.index("--prover") + 1]
        actual = hashlib.sha256(open(p, "rb").read()).hexdigest()
        for name in certs:
            cp = os.path.join(CS.CERTS, name)
            rec = json.load(open(cp)).get("model_sha256") if os.path.exists(cp) else None
            rows.append({"cert": name, "prover": os.path.basename(p), "recorded": rec, "actual": actual, "ok": rec == actual})
    tab = NS.nad2_tabela_check(ROOT)
    rows.append({"cert": "tabela_U_nad2", "prover": "freeze_U.json", "recorded": NS.NAD2_TABELA_SHA256, "actual": str(tab),
                 "ok": all(tab.values())})
    for nazwa_p9, sciezki in (("P9_nad3.json", {pk: f"results/NAD3/s1/freeze_U_{pk}.json" for pk in ("P1", "P2", "P3")}),
                              ("P9_teach.json", {"TEACH": "results/TEACH/s1/freeze_U_TEACH.json"})):           # TEACH
        p9 = json.load(open(os.path.join(CS.CERTS, nazwa_p9))) if os.path.exists(os.path.join(CS.CERTS, nazwa_p9)) else {}
        for punkt, rel in sciezki.items():
            path = os.path.join(ROOT, rel)
            rec = ((p9.get("tabele") or {}).get(punkt) or {}).get("tabela_sha256")
            try:
                T = NS.nad3_tabela(path, rec)
                rows.append({"cert": f"tabela_U_{punkt}", "prover": os.path.basename(path), "recorded": rec, "actual": T["sha"], "ok": True})
            except NS.NadirStartError as e:
                rows.append({"cert": f"tabela_U_{punkt}", "prover": os.path.basename(path), "recorded": rec, "actual": f"kod {e.kod}",
                             "ok": False})
    print("=== teach_certs_selfcheck ===")
    for r in rows:
        tag = "OK  " if r["ok"] else "FAIL"
        print(f"  {tag}  {r['cert']:20s} ← {r['prover']:22s} {str(r.get('actual'))[:16]}…"
              + ("" if r["ok"] else f"  zapisane {str(r.get('recorded'))[:16]}…"))
    bad = [r for r in rows if not r["ok"]]
    print(f"WERDYKT teach_certs_selfcheck: {'PASS' if not bad else 'FAIL'} ({len(rows) - len(bad)}/{len(rows)} zgodne)")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
