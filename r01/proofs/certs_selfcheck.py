#!/usr/bin/env python3
"""r01/proofs/certs_selfcheck.py — GUARD prowieniencji certów (model_sha256 ↔ prover).

Dla KAŻDEGO certu w r01/proofs/certs/ porównuje zapisane `model_sha256` z aktualnym
sha256 pliku prover, którego `__file__` był hashowany przy generacji certu. Rozjazd =
GŁOŚNY FAIL (exit 1) z jawnym wskazaniem, który cert nie odpowiada swojemu prover.

Geneza (rozjazd P2.json po commicie 45667f9): prover `geofence.py` zmieniony ADDYTYWNIE
(gałąź V_MAX_PROVE) i uruchomiony, ale kanoniczny cert nieregenerowany/niezacommitowany
w tym samym commicie → self-hash certu (c388bf) przestał wskazywać prover w repo (150b22).
Treść dowodowa była niezmieniona, ale prowieniencja rozjechana. Ten guard łapie to od razu.

LEKCJA HIGIENY (repo): sesja uruchamiająca prover kończy się CZYSTYM DRZEWEM albo COMMITEM.

Uruchom: python3 -m r01.proofs.certs_selfcheck
  - na KONIEC każdej sesji dotykającej proofs/;
  - jako PIERWSZE sprawdzenie planu re-certyfikacji R0.2 (przed P1/P4/P5) — patrz PRE_R02 §5.
Bez zależności (stdlib) — nie wymaga z3.
"""
from __future__ import annotations
import hashlib
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
CERTS = os.path.join(_HERE, "certs")

# cert -> plik prover, którego __file__ jest hashowany do model_sha256.
# (weryfikacja: każdy prover liczy hashlib.sha256(open(__file__,"rb").read()).)
PROVER_OF = {
    "P1.json": "verify.py",
    "P2.json": "geofence.py",
    "P2_vmax3p1.json": "geofence.py",   # ten sam prover, override V_MAX_PROVE=3.1
    "P4.json": "p4_verify.py",
    "P5.json": "conformance.py",
    "P2_eps.json": "eps_verify.py",     # R0.3a: P2-ε (forma plateau/A-episode)
}


def _sha(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def check():
    rows = []
    for cert_name, prover_name in sorted(PROVER_OF.items()):
        cert_path = os.path.join(CERTS, cert_name)
        prover_path = os.path.join(_HERE, prover_name)
        row = {"cert": cert_name, "prover": prover_name}
        if not os.path.exists(cert_path):
            row.update(ok=False, err="BRAK CERTU")
        elif not os.path.exists(prover_path):
            row.update(ok=False, err="BRAK PROVERA")
        else:
            recorded = json.load(open(cert_path)).get("model_sha256")
            actual = _sha(prover_path)
            row.update(recorded=recorded, actual=actual, ok=(recorded == actual))
        rows.append(row)
    return rows


def main():
    rows = check()
    bad = [r for r in rows if not r["ok"]]
    print("=== certs_selfcheck: prowieniencja model_sha256 ↔ prover ===")
    for r in rows:
        if r["ok"]:
            print(f"  OK    {r['cert']:16s} ← {r['prover']:16s} {r['actual'][:16]}…")
        elif "err" in r:
            print(f"  FAIL  {r['cert']:16s} ← {r['prover']:16s} {r['err']}")
        else:
            print(f"  FAIL  {r['cert']:16s} ← {r['prover']:16s} ROZJAZD prowieniencji")
            print(f"        cert.model_sha256 = {r.get('recorded')}")
            print(f"        sha256(prover)    = {r.get('actual')}")
    if bad:
        print(f"!! {len(bad)} rozjazd(y): cert(y) NIE odpowiada(ją) swojemu prover.")
        print("   NAPRAW: zregeneruj cert (uruchom prover) i ZACOMMITUJ, albo git checkout prover.")
        print("   LEKCJA: sesja uruchamiająca prover kończy się czystym drzewem albo commitem.")
        sys.exit(1)
    print(f"WERDYKT certs_selfcheck: PASS ({len(rows)}/{len(rows)} zgodne)")


if __name__ == "__main__":
    main()
