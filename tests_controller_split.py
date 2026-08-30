#!/usr/bin/env python3
"""tests_controller_split.py — równoważność RouteFollower ↔ stary blok setpointów (INFRA-3 A1.3).

Bez SITL. Wchodzi do commita A1. Asercje bit-w-bit (SR-4: żadnej tolerancji).

(i)  referencja `ref_step` = DOSŁOWNA kopia starego bloku setpointów z `git show 3065b8b:r03/gate_run_r03.py`
     (linie 225–230 + 291), przepisana jako funkcja stanowa — NIE zmodyfikowana.
(ii) wejścia = wiersze `tick` (schemat v2: pola `pos`, `descending`) ze WSZYSTKICH ważnych i diag lotów S
     serii K1, które mają wiersze `tick` (`results/K1/S/**/trace.jsonl`). Trace R0.3a (`results/R03/gate/*`)
     są schematu v1 bez wierszy `tick` → POMIJANE i notowane (patrz `test_r03_v1_skipped`).
(iii) asercja: dla KAŻDEGO wiersza referencja i RouteFollower dają IDENTYCZNE (bit-w-bit) tgt, v_ned, seg_i, dist.
(iv) asercja sha: `r01/shield.py` == 1c584964…, `r03/config.py` == 4c440e42… po zmianie.
(v)  test syntetyczny przejścia narożnika: dist 1.01 → 0.99 → tgt/v_ned na ticku inkrementu wskazują STARY wp,
     następny tick NOWY wp.

Uruchamiane: `python3 -m pytest tests_controller_split.py -v` LUB `python3 tests_controller_split.py` (raport verbatim).
"""
import glob
import hashlib
import json
import math
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
import sys
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from r03 import config as C
from r01.config import V_MAX as VMAX
from r03.controllers.route_follower import RouteFollower

SHIELD_SHA = "1c584964ddc85192c1381f5041e8ed3b7b81b984c92b8f33d5c685acd2cba2c2"
CONFIG_SHA = "4c440e4265574b68c2a3341105d5cb0ace07ed683cd0bca43228af356629752a"


# --- (i) REFERENCJA — dosłowna kopia starego bloku (3065b8b:r03/gate_run_r03.py 225–230 + 291) ----------
# Stan trasy = seg_i (jak w pętli, lokalny). ALT/VMAX = parametry uprzęży (jak w gate).
class _RefState:
    def __init__(self):
        self.seg_i = 0


def ref_step(st, pos, descending, wps, ALT):
    # ↓↓↓ verbatim z 3065b8b (kolejność zachowana; ŻADNEJ modyfikacji logiki) ↓↓↓
    seg_i = st.seg_i
    wp = wps[seg_i % len(wps)]
    dx, dy = wp[0] - pos[0], wp[1] - pos[1]
    dist = math.hypot(dx, dy)
    if dist < 1.0 and not descending:
        seg_i += 1
    tgt = (wp[0], wp[1], -ALT)
    vn, ve = (VMAX * dx / dist, VMAX * dy / dist) if dist > 1e-3 else (0.0, 0.0)
    # ↑↑↑ verbatim ↑↑↑
    st.seg_i = seg_i
    return {"tgt": tgt, "v_ned": (vn, ve, 0.0), "seg_i": seg_i, "dist": dist}


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()


def _alt_for_scen(scen):
    # gate: ALT = 15.0 if SCEN == "S3" else 8.0
    return 15.0 if scen == "S3" else 8.0


def _corpus():
    """Zwraca listę (ścieżka, scen, [tick_rows]) dla lotów S/K1, które mają wiersze tick."""
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, "results/K1/S/**/trace.jsonl"), recursive=True)):
        scen = None
        ticks = []
        with open(f) as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if r.get("t") == "meta":
                    scen = r.get("scen")
                elif r.get("t") == "tick":
                    ticks.append(r)
        if ticks:
            out.append((f, scen, ticks))
    return out


def _replay_one(scen, ticks):
    """Odtwarza cały ciąg tick przez referencję i RouteFollower; zwraca listę niezgodności."""
    ALT = _alt_for_scen(scen)
    wps = C.corner_waypoints_r03()
    st = _RefState()
    ctrl = RouteFollower(wps=C.corner_waypoints_r03(), vmax=VMAX, alt=ALT, wp_reach_m=1.0)
    ctrl.reset()
    mismatches = []
    for k, row in enumerate(ticks):
        pos = tuple(row["pos"])
        desc = bool(row.get("descending", False))
        ref = ref_step(st, pos, desc, wps, ALT)
        cmd = ctrl.step(row.get("tick", k), pos, (0.0, 0.0, 0.0), 0.0, desc)
        # bit-w-bit (SR-4): tuple/float dokładna równość
        if (cmd["tgt_ned"] != ref["tgt"] or cmd["v_ned"] != ref["v_ned"]
                or cmd["seg_i"] != ref["seg_i"] or cmd["dist"] != ref["dist"]):
            mismatches.append((k, row.get("tick"), ref, {
                "tgt_ned": cmd["tgt_ned"], "v_ned": cmd["v_ned"],
                "seg_i": cmd["seg_i"], "dist": cmd["dist"]}))
    return mismatches


# ----------------------------------- TESTY -----------------------------------
def test_sha_shield_config_unchanged():
    assert _sha(os.path.join(ROOT, "r01/shield.py")) == SHIELD_SHA
    assert _sha(os.path.join(ROOT, "r03/config.py")) == CONFIG_SHA


def test_equivalence_all_S_K1_traces():
    corpus = _corpus()
    assert corpus, "brak lotów S/K1 z wierszami tick — korpus pusty"
    total_ticks = 0
    for path, scen, ticks in corpus:
        mism = _replay_one(scen, ticks)
        total_ticks += len(ticks)
        assert not mism, f"NIEZGODNOŚĆ (SR-4) w {path}: {mism[:3]}"
    assert total_ticks > 0


def test_r03_v1_skipped():
    """R0.3a (results/R03/gate/*) schemat v1 — brak wierszy tick; jawnie pomijane (nota A1.3 ii)."""
    v1 = glob.glob(os.path.join(ROOT, "results/R03/**/trace.jsonl"), recursive=True)
    for f in v1:
        with open(f) as fh:
            has_tick = any(json.loads(l).get("t") == "tick"
                           for l in fh if l.strip().startswith("{"))
        assert not has_tick, f"nieoczekiwany wiersz tick w v1 {f}"


def test_synthetic_corner_crossing():
    """(v) dist 1.01 → 0.99: tick inkrementu wskazuje STARY wp, następny tick NOWY wp."""
    wps = [(10.0, 0.0, -8.0), (0.0, 10.0, -8.0)]
    ALT = 8.0
    ctrl = RouteFollower(wps=wps, vmax=VMAX, alt=ALT, wp_reach_m=1.0)
    ctrl.reset()
    st = _RefState()

    # tick A: pos taki, że dist do wps[0]=(10,0) wynosi 1.01 (>1.0) → brak inkrementu, cel = STARY wp[0]
    posA = (8.99, 0.0, -8.0)   # hypot(10-8.99, 0) = 1.01
    assert abs(math.hypot(10.0 - posA[0], 0.0) - 1.01) < 1e-9
    a = ctrl.step(0, posA, (0, 0, 0), 0.0, False)
    ra = ref_step(st, posA, False, wps, ALT)
    assert a["seg_i"] == 0 and ra["seg_i"] == 0
    assert a["tgt_ned"] == (10.0, 0.0, -8.0) == ra["tgt"]        # STARY wp[0]

    # tick B: dist do wps[0] = 0.99 (<1.0) → inkrement seg_i→1, ale tgt/v_ned NA TYM ticku = STARY wp[0]
    posB = (9.01, 0.0, -8.0)   # hypot(10-9.01, 0) = 0.99
    assert abs(math.hypot(10.0 - posB[0], 0.0) - 0.99) < 1e-9
    b = ctrl.step(1, posB, (0, 0, 0), 0.0, False)
    rb = ref_step(st, posB, False, wps, ALT)
    assert b["seg_i"] == 1 and rb["seg_i"] == 1                   # seg_i PO inkremencie
    assert b["tgt_ned"] == (10.0, 0.0, -8.0) == rb["tgt"]         # tgt na ticku inkrementu = STARY wp[0]
    assert b["v_ned"][0] > 0 and b["v_ned"][1] == 0.0            # prędkość ku STAREMU wp[0] (kier. +X)

    # tick C: następny tick → cel = NOWY wp[1]=(0,10)
    posC = (9.5, 0.0, -8.0)
    c = ctrl.step(2, posC, (0, 0, 0), 0.0, False)
    rc = ref_step(st, posC, False, wps, ALT)
    assert c["tgt_ned"] == (0.0, 10.0, -8.0) == rc["tgt"]         # NOWY wp[1]
    assert c["v_ned"] == rc["v_ned"]


def test_descending_no_increment():
    """(C2 ANEKS_INFRA3-1) jedyna gałąź klauzuli bramkującej, której korpus lotów NIE ćwiczy:
    descending=True ∧ dist<1.0 ⇒ seg_i BEZ inkrementu — w OBU implementacjach identycznie."""
    wps = [(10.0, 0.0, -8.0), (0.0, 10.0, -8.0)]
    ALT = 8.0
    pos = (9.5, 0.0, -8.0)                      # dist do wps[0] = 0.5 < 1.0
    assert math.hypot(10.0 - pos[0], 0.0) < 1.0
    # RouteFollower: descending=True → brak inkrementu (seg_i zostaje 0)
    ctrl = RouteFollower(wps=wps, vmax=VMAX, alt=ALT, wp_reach_m=1.0); ctrl.reset()
    r = ctrl.step(0, pos, (0, 0, 0), 0.0, True)
    assert r["seg_i"] == 0, "descending=True nie może inkrementować seg_i (RouteFollower)"
    # referencja (stary blok): descending=True → brak inkrementu
    st = _RefState()
    rr = ref_step(st, pos, True, wps, ALT)
    assert rr["seg_i"] == 0, "descending=True nie może inkrementować seg_i (referencja)"
    # kontrast: descending=False PRZY TEJ SAMEJ pozycji → inkrement (obie)
    ctrl2 = RouteFollower(wps=wps, vmax=VMAX, alt=ALT, wp_reach_m=1.0); ctrl2.reset()
    st2 = _RefState()
    assert ctrl2.step(0, pos, (0, 0, 0), 0.0, False)["seg_i"] == 1
    assert ref_step(st2, pos, False, wps, ALT)["seg_i"] == 1


if __name__ == "__main__":
    print("=== A1.3 test równoważności RouteFollower ↔ stary blok (3065b8b) ===")
    print(f"sha r01/shield.py = {_sha(os.path.join(ROOT, 'r01/shield.py'))[:16]}  want {SHIELD_SHA[:16]}")
    print(f"sha r03/config.py = {_sha(os.path.join(ROOT, 'r03/config.py'))[:16]}  want {CONFIG_SHA[:16]}")
    assert _sha(os.path.join(ROOT, "r01/shield.py")) == SHIELD_SHA
    assert _sha(os.path.join(ROOT, "r03/config.py")) == CONFIG_SHA
    corpus = _corpus()
    print(f"\nkorpus S/K1 z wierszami tick: {len(corpus)} lotów")
    grand = 0
    for path, scen, ticks in corpus:
        mism = _replay_one(scen, ticks)
        grand += len(ticks)
        rel = os.path.relpath(path, ROOT)
        status = "OK  " if not mism else f"FAIL({len(mism)})"
        print(f"  {status} {rel}  scen={scen} ALT={_alt_for_scen(scen)} ticks={len(ticks)}")
        assert not mism, f"NIEZGODNOŚĆ SR-4: {mism[:3]}"
    print(f"\nŁącznie ticków porównanych bit-w-bit: {grand}  → WSZYSTKIE IDENTYCZNE")
    test_synthetic_corner_crossing()
    print("test syntetyczny przejścia narożnika: OK")
    test_descending_no_increment()
    print("test descending=True ∧ dist<1.0 ⇒ brak inkrementu seg_i (obie impl.): OK")
    test_r03_v1_skipped()
    print("R0.3a v1 (bez tick): pominięte zgodnie z A1.3(ii)")
    print("\nA1.3 PASS")
