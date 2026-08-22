#!/usr/bin/env python3
"""k1/k1_shield_pins.py — zapięte sha256 modułów osłony (PRE_K1 / ANEKS_K1-2 W2(b)).

Baza: `6db3393` (aktualna baza certyfikowana R03A 4/4 → B1 token → B3 trace → §0 erratum).
shield.py i config.py bajt-identyczne 6db3393↔0ce4d8e↔(ANEKS_K1-6 F2) — K1 ich NIE tknął (piny NIEZMIENIONE).
gate_run_r03.py RE-BASELINED (ANEKS_K1-6 F2): naprawa defektu stale-dist w gałęzi SCEN=K1 (f_along
względem AKTUALNEGO celu; K1_POINT był ignorowany, wstrzyknięcie kolapsowało do narożnika). Zmiana
OGRANICZONA do gałęzi K1 — blok is_pos/zejścia/shield.step NIETKNIĘTY; S2/S3/S4 identyczne (test).
Dowód diff: ANEKS_SHA §W3 (K1_POINT-fix). Pin 19967de2… (0ce4d8e) → 72619513… (po naprawie).

k1_finalize przy KAŻDYM biegu S liczy sha256 tych plików i porównuje z SHIELD_PINS.
Niezgodność ⇒ bieg nieważny (shield_frozen=False). SR-K3-analog dla warstwy osłony.
"""
import os, hashlib

SHIELD_PINS = {
    "r01/shield.py":       "1c584964ddc85192c1381f5041e8ed3b7b81b984c92b8f33d5c685acd2cba2c2",
    "r03/config.py":       "4c440e4265574b68c2a3341105d5cb0ace07ed683cd0bca43228af356629752a",
    "r03/gate_run_r03.py": "72619513c682e76892c531ec3dae2d918da08da92017605dcba50103977cf58a",
}
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()


def check_shield_frozen():
    """Zwraca (frozen: bool, detail: dict{path: {'want','got','ok'}})."""
    detail, ok_all = {}, True
    for rel, want in SHIELD_PINS.items():
        p = os.path.join(_ROOT, rel)
        got = _sha(p) if os.path.exists(p) else None
        ok = (got == want)
        ok_all = ok_all and ok
        detail[rel] = {"want": want, "got": got, "ok": ok}
    return ok_all, detail


if __name__ == "__main__":
    frozen, det = check_shield_frozen()
    for rel, d in det.items():
        print(f"{'OK ' if d['ok'] else 'MISMATCH'} {rel} got={str(d['got'])[:16]} want={d['want'][:16]}")
    print("SHIELD FROZEN:", frozen)
    raise SystemExit(0 if frozen else 1)
