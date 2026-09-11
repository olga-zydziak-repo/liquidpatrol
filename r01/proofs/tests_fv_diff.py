#!/usr/bin/env python3
"""r01/proofs/tests_fv_diff.py — różnicówka LUSTRO↔PRODUKCJA (noga FV, PRE_FV §4, B2).

Trzy warstwy (produkcja importowana BEZ modyfikacji — piny nietykane, PRE_FV §2):
  (a) SIATKA deterministyczna `fv_diff_grid.json` — brzegi progów (debounce/hyst ±1 tick, R_E±, V_E±,
      v_max±, H_SWITCH±). Dla funkcji stanowych siatka to SEKWENCJE; porównanie wyjść ORAZ stanu per krok.
      Siatka jest NIETYKALNA po commicie C1 (prerejestracja wyboru wejść — PRE_FV §4a).
  (b) FUZZ z ziarnami {0,1,2,3,4}, ≥10⁵ przypadków na funkcję (generator deterministyczny, tu).
  (c) REGRESJA FIKSTURY: 4221/1791 ticków D5 z results/K1/S/**/trace.jsonl przez lustro D5 (własny loader).

Kryterium (PRE_FV §5): 0 rozbieżności końcowych na (a)+(b)+(c). Rozbieżność ⇒ poprawka WYŁĄCZNIE lustra
+ wpis do results/FV/REJESTR_ROZBIEZNOSCI.md. Rozbieżność potwierdzona NA PRODUKCJI przy wejściu
osiągalnym ⇒ TRIPWIRE (PRE_FV §5) — STOP, zero poprawek w r01/r03.

Uruchom: python3 -m r01.proofs.tests_fv_diff build   # emisja siatki (raz, przed C1)
         python3 -m r01.proofs.tests_fv_diff sweep    # pełny przemiał + stats do results/FV/
         python3 -m pytest r01/proofs/tests_fv_diff.py -q
"""
from __future__ import annotations
import json
import math
import os
import random
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(_HERE))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from r01.proofs import fv_mirror as M
from r01.shield import PatrolShield
from r03.controllers.safe_descend import safe_descend_step as PROD_D5, new_state as PROD_D5_STATE

GRID_PATH = os.path.join(_HERE, "fv_diff_grid.json")
FUZZ_SEEDS = [0, 1, 2, 3, 4]
FUZZ_PER_SEED = 20000               # ×5 ziaren = 100000 przypadków / funkcję

# jedna instancja do funkcji BEZSTANOWYCH (nie mutują stanu monitora/latcha)
_SHIELD = PatrolShield()
_SHIELD.reset()


# ============================ DRIVERY PRODUKCJI ==============================
def prod_braking(vel):
    return _SHIELD._braking_dist(vel)


def prod_geofence(pos, vel, target):
    return _SHIELD._geofence_violation(pos, vel, target)


def prod_pos_seq(flags):
    """Sekwencja pos_flag przez PRODUKCYJNY _pos_monitor; zwraca stan zreifikowany per krok."""
    s = PatrolShield()
    s.reset()
    out = []
    for f in flags:
        s._pos_monitor(f)
        out.append((s._pos_bad, s._pos_healthy, s._pos_refuse, s.n_pos_enter))
    return out


def prod_d5_seq(nows, cfg):
    st = PROD_D5_STATE()
    out = []
    for now in nows:
        v, e, td, st = PROD_D5(st, now, cfg)
        out.append((v, tuple(e), td, dict(st)))
    return out


# ============================== DRIVERY LUSTRA ===============================
def mir_braking(vel, th):
    return M.braking_dist(vel, th["v_max"], th["a_brake"])


def mir_geofence(pos, vel, target, th):
    return M.geofence_violation(pos, vel, target, th["r_e"], th["v_e"], th["v_max"], th["a_brake"])


def mir_pos_seq(flags, th):
    st = M.new_pos_state()
    out = []
    for f in flags:
        M.pos_monitor_step(st, f, th["debounce_ticks"], th["hyst_ticks"])
        out.append((st["pos_bad"], st["pos_healthy"], st["pos_refuse"], st["n_pos_enter"]))
    return out


def mir_d5_seq(nows, cfg):
    st = M.new_descend_state()
    out = []
    for now in nows:
        v, e, td, st = M.safe_descend_step_mirror(st, now, cfg)
        out.append((v, tuple(e), td, dict(st)))
    return out


# ============================ BUDOWA SIATKI (C1) =============================
def build_grid():
    """Deterministyczna siatka brzegów progów. Progi z PRODUKCJI (fv_mirror.shield_thresholds / d5_cfg).
    Emitowana raz przed C1 i NIETYKALNA (PRE_FV §4a)."""
    th = M.shield_thresholds()
    d5 = M.d5_cfg()
    r_e, v_e, v_max = th["r_e"], th["v_e"], th["v_max"]
    a_brake, dt = th["a_brake"], th["dt"]
    deb, hyst = th["debounce_ticks"], th["hyst_ticks"]
    dfd, dtot = d5["desc_fast_dur"], d5["desc_total"]
    eps = 0.1

    # -- braking_dist: |v| wokół v_max (clamp) --
    braking = []
    for mag in [0.0, v_max - eps, v_max, v_max + eps, 2.0 * v_max, 0.5 * v_max]:
        for (ux, uy) in [(1.0, 0.0), (0.0, 1.0), (0.7071, 0.7071), (-0.7071, 0.7071)]:
            braking.append([mag * ux, mag * uy])

    # -- geofence: target radial ~R_E; pos+brake ~R_E; pion ~V_E --
    geofence = []
    for rad in [r_e - eps, r_e, r_e + eps]:
        for (ux, uy) in [(1.0, 0.0), (0.7071, 0.7071)]:
            geofence.append({"pos": [0.0, 0.0, 0.0], "vel": [0.0, 0.0],
                             "target": [rad * ux, rad * uy, 0.0]})
    # pos radial + braking(v_max) na brzegu R_E: braking(v_max)=v_max²/(2a)
    brake_vmax = (v_max * v_max) / (2.0 * a_brake)
    for pr in [r_e - brake_vmax - eps, r_e - brake_vmax, r_e - brake_vmax + eps]:
        geofence.append({"pos": [pr, 0.0, 0.0], "vel": [v_max, 0.0],
                         "target": [0.0, 0.0, 0.0]})
    # pion V_E na brzegu (target_z i pos_z)
    for vz in [v_e - eps, v_e, v_e + eps]:
        geofence.append({"pos": [0.0, 0.0, 0.0], "vel": [0.0, 0.0], "target": [0.0, 0.0, vz]})
        geofence.append({"pos": [0.0, 0.0, vz], "vel": [0.0, 0.0], "target": [0.0, 0.0, 0.0]})

    # -- pos_monitor: sekwencje na brzegach debounce/hyst ±1 --
    pm = []
    pm.append([True] * deb)                       # dokładnie debounce → wejście
    pm.append([True] * max(1, deb - 1))           # debounce-1 → brak wejścia
    pm.append([True] * (deb + 1))                 # debounce+1
    pm.append([True] * deb + [False] * hyst)      # wejście + dokładnie hyst czystych → wyjście
    pm.append([True] * deb + [False] * (hyst - 1))  # hyst-1 → brak wyjścia
    pm.append([True] * deb + [False] * (hyst + 1))  # hyst+1
    pm.append([True, False, True, True])          # reset pos_bad przed wejściem, potem wejście
    pm.append([True] * deb + [False] * (hyst - 1) + [True] + [False] * hyst)  # heal-reset przed hyst, re-bad
    pm.append([None, True, True, None, False])    # None ⇒ brak zmian
    pm.append([True] * deb + [False] * 3 + [True] * deb)  # wejście→częściowe zdrowie→re-bad (już refuse)

    # -- safe_descend: sekwencje now na brzegach desc_fast_dur / desc_total (desc_t0 = now[0]=0) --
    sd = []
    sd.append([0.0, dfd - dt, dfd, dfd + dt])
    sd.append([0.0, dtot - dt, dtot, dtot + dt])
    sd.append([0.0])                              # sam start (refuse_pos_land)
    sd.append([0.0, dfd, dtot])                   # brzegi dokładne
    sd.append([round(i * dt, 4) for i in range(0, int(dtot / dt) + 3)])  # monotoniczny przemiał do touchdown

    return {
        "provenance": {
            "thresholds_source": "fv_mirror.shield_thresholds() ← r01/config.py:ShieldConfig + r01/shield.py:72-74",
            "d5_source": "fv_mirror.d5_cfg() ← bench_flight.py:73-75 / gate_run_r03.py:223-224",
            "r_e": r_e, "v_e": v_e, "v_max": v_max, "a_brake": a_brake, "dt": dt,
            "debounce_ticks": deb, "hyst_ticks": hyst,
            "desc_fast_dur": dfd, "desc_total": dtot,
            "note": "NIETYKALNE po commicie C1 (PRE_FV §4a). Zmiana ⇒ nowy ANEKS_FV-n.",
        },
        "braking_dist": braking,
        "geofence": geofence,
        "pos_monitor": pm,
        "safe_descend": sd,
    }


def _load_grid():
    with open(GRID_PATH) as f:
        return json.load(f)


# ================================ FUZZ =======================================
def _fuzz_cases(kind, seed):
    rnd = random.Random(seed)
    cases = []
    for _ in range(FUZZ_PER_SEED):
        if kind == "braking":
            cases.append([rnd.uniform(-6.0, 6.0), rnd.uniform(-6.0, 6.0)])
        elif kind == "geofence":
            cases.append({"pos": [rnd.uniform(-40, 40), rnd.uniform(-40, 40), rnd.uniform(-25, 25)],
                          "vel": [rnd.uniform(-6, 6), rnd.uniform(-6, 6)],
                          "target": [rnd.uniform(-40, 40), rnd.uniform(-40, 40), rnd.uniform(-25, 25)]})
        elif kind == "pos_monitor":
            n = rnd.randint(1, 25)
            seq = []
            for _ in range(n):
                r = rnd.random()
                seq.append(True if r < 0.45 else (False if r < 0.9 else None))
            cases.append(seq)
        elif kind == "safe_descend":
            n = rnd.randint(1, 40)
            t = rnd.uniform(0.0, 2.0)
            seq = [round(t, 6)]
            for _ in range(n - 1):
                t += rnd.uniform(0.0, 0.5)      # monotoniczny (A1-zegar)
                seq.append(round(t, 6))
            cases.append(seq)
    return cases


# ============================ FIKSTURA D5 (c) ================================
def _d5_fixture():
    """Własny loader (proofs/) fikstury 4221/1791 — bench/tests_safe_descend.py NIETYKANY.
    Zwraca listę (plik, [descending_bool per tick]) z results/K1/S/**/trace.jsonl."""
    import glob
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, "results/K1/S/**/trace.jsonl"), recursive=True)):
        seq = []
        for line in open(f):
            if '"t": "tick"' in line:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                seq.append(bool(r.get("descending")))
        if seq:
            out.append((f, seq))
    return out


# =============================== POMIAR ======================================
def run_all(verbose=False):
    """Pełny przemiał: zwraca stats + listę rozbieżności (surowe wejścia). Nie asertuje."""
    th = M.shield_thresholds()
    d5 = M.d5_cfg()
    grid = _load_grid()
    stats = {"grid": {}, "fuzz": {}, "fixture": {}}
    diffs = []

    def cmp_braking(vel):
        a, b = prod_braking(vel), mir_braking(vel, th)
        if a != b:
            diffs.append({"fn": "braking_dist", "in": {"vel": vel}, "prod": a, "mir": b})

    def cmp_geofence(c):
        a = prod_geofence(c["pos"], c["vel"], c["target"])
        b = mir_geofence(c["pos"], c["vel"], c["target"], th)
        if a != b:
            diffs.append({"fn": "geofence", "in": c, "prod": list(a), "mir": list(b)})

    def cmp_pos(flags):
        a, b = prod_pos_seq(flags), mir_pos_seq(flags, th)
        if a != b:
            diffs.append({"fn": "pos_monitor", "in": {"flags": flags}, "prod": a, "mir": b})

    def cmp_d5(nows):
        a, b = prod_d5_seq(nows, d5), mir_d5_seq(nows, d5)
        if a != b:
            diffs.append({"fn": "safe_descend", "in": {"nows": nows}, "prod": a, "mir": b})

    # (a) siatka
    for v in grid["braking_dist"]:
        cmp_braking(v)
    for c in grid["geofence"]:
        cmp_geofence(c)
    for s in grid["pos_monitor"]:
        cmp_pos(s)
    for s in grid["safe_descend"]:
        cmp_d5(s)
    stats["grid"] = {"braking_dist": len(grid["braking_dist"]), "geofence": len(grid["geofence"]),
                     "pos_monitor": len(grid["pos_monitor"]), "safe_descend": len(grid["safe_descend"])}

    # (b) fuzz
    fz = {"braking": 0, "geofence": 0, "pos_monitor": 0, "safe_descend": 0}
    for seed in FUZZ_SEEDS:
        for v in _fuzz_cases("braking", seed):
            cmp_braking(v); fz["braking"] += 1
        for c in _fuzz_cases("geofence", seed):
            cmp_geofence(c); fz["geofence"] += 1
        for s in _fuzz_cases("pos_monitor", seed):
            cmp_pos(s); fz["pos_monitor"] += 1
        for s in _fuzz_cases("safe_descend", seed):
            cmp_d5(s); fz["safe_descend"] += 1
    stats["fuzz"] = fz

    # (c) fikstura
    fx = _d5_fixture()
    tot = 0; ndesc = 0
    for _, seq in fx:
        st_p = PROD_D5_STATE(); st_m = M.new_descend_state()
        for idx, desc in enumerate(seq):
            tot += 1
            if not desc:
                continue
            now = idx * th["dt"]
            ndesc += 1
            vp, ep, tp, st_p = PROD_D5(st_p, now, d5)
            vm, em, tm, st_m = M.safe_descend_step_mirror(st_m, now, d5)
            if (vp, ep, tp, st_p) != (vm, em, tm, st_m):
                diffs.append({"fn": "safe_descend_fixture", "in": {"file": _, "idx": idx, "now": now},
                              "prod": [vp, ep, tp, dict(st_p)], "mir": [vm, em, tm, dict(st_m)]})
    stats["fixture"] = {"files": len(fx), "ticks_total": tot, "ticks_descending": ndesc}

    return {"stats": stats, "diffs": diffs}


# =============================== PYTEST ======================================
def _th():
    return M.shield_thresholds()


def test_grid_braking():
    th = _th()
    for v in _load_grid()["braking_dist"]:
        assert prod_braking(v) == mir_braking(v, th), v


def test_grid_geofence():
    th = _th()
    for c in _load_grid()["geofence"]:
        assert prod_geofence(c["pos"], c["vel"], c["target"]) == \
               mir_geofence(c["pos"], c["vel"], c["target"], th), c


def test_grid_pos_monitor():
    th = _th()
    for s in _load_grid()["pos_monitor"]:
        assert prod_pos_seq(s) == mir_pos_seq(s, th), s


def test_grid_safe_descend():
    d5 = M.d5_cfg()
    for s in _load_grid()["safe_descend"]:
        assert prod_d5_seq(s, d5) == mir_d5_seq(s, d5), s


def test_fuzz_braking():
    th = _th()
    for seed in FUZZ_SEEDS:
        for v in _fuzz_cases("braking", seed):
            assert prod_braking(v) == mir_braking(v, th), (seed, v)


def test_fuzz_geofence():
    th = _th()
    for seed in FUZZ_SEEDS:
        for c in _fuzz_cases("geofence", seed):
            assert prod_geofence(c["pos"], c["vel"], c["target"]) == \
                   mir_geofence(c["pos"], c["vel"], c["target"], th), (seed, c)


def test_fuzz_pos_monitor():
    th = _th()
    for seed in FUZZ_SEEDS:
        for s in _fuzz_cases("pos_monitor", seed):
            assert prod_pos_seq(s) == mir_pos_seq(s, th), (seed, s)


def test_fuzz_safe_descend():
    d5 = M.d5_cfg()
    for seed in FUZZ_SEEDS:
        for s in _fuzz_cases("safe_descend", seed):
            assert prod_d5_seq(s, d5) == mir_d5_seq(s, d5), (seed, s)


def test_fixture_d5_4221():
    th = _th(); d5 = M.d5_cfg()
    fx = _d5_fixture()
    tot = sum(len(s) for _, s in fx); ndesc = 0
    assert tot == 4221, tot
    for _, seq in fx:
        st_p = PROD_D5_STATE(); st_m = M.new_descend_state()
        for idx, desc in enumerate(seq):
            if not desc:
                continue
            ndesc += 1
            now = idx * th["dt"]
            rp = PROD_D5(st_p, now, d5); st_p = rp[3]
            rm = M.safe_descend_step_mirror(st_m, now, d5); st_m = rm[3]
            assert (rp[0], rp[1], rp[2], st_p) == (rm[0], rm[1], rm[2], st_m), (idx, now)
    assert ndesc == 1791, ndesc


def test_p1_consistency():
    """F1: lustro/jądro reprodukuje własności P1d/P1f/P1h (jedna asercja spójności, nie osobne
    twierdzenie). Napędza PRODUKCYJNY shield.step; potwierdza semantykę odwzorowaną w lustrze."""
    from r01.shield import (PatrolShield, REFUSE, ALLOW, POS_DEGRADED, GEOFENCE, NO_AUTH,
                            M_OBSERVE, DONE, POSDEG, NOAUTH)
    # P1f: pos_bad ∧ ¬terminal ⇒ REFUSE ∧ reason=POS_DEGRADED (po debounce)
    s = PatrolShield(); s.reset()
    for _ in range(s.pos_debounce_ticks):
        d = s.step(0, (0, 0, -10), (0, 0), (0, 0, -10), pos_flag=True)
    assert d["decision"] == REFUSE and d["reason"] == POS_DEGRADED and d["state"] == POSDEG
    # P1d: latch monotoniczny — po REFUSE(GEOFENCE) każdy kolejny tick trzyma REFUSE/GEOFENCE
    s = PatrolShield(); s.reset()
    d = s.step(0, (0, 0, 0), (0, 0), (100.0, 0.0, 0.0))     # target poza R_E ⇒ R-G latch
    assert d["decision"] == REFUSE and d["reason"] == GEOFENCE and d["state"] == DONE
    d2 = s.step(1, (0, 0, -10), (0, 0), (0, 0, -10))         # benign — latch trzyma
    assert d2["decision"] == REFUSE and d2["reason"] == GEOFENCE and d2["state"] == DONE
    # P1h: OBSERVE ∧ ¬auth_ok ⇒ REFUSE(NO_AUTH) NIETERMINALNY; auth_ok ⇒ ALLOW (odwracalny)
    s = PatrolShield(); s.reset()
    d = s.step(0, (0, 0, -10), (0, 0), (5.0, 0.0, -10.0), mode=M_OBSERVE, auth_ok=False)
    assert d["decision"] == REFUSE and d["reason"] == NO_AUTH and d["state"] == NOAUTH
    d2 = s.step(1, (0, 0, -10), (0, 0), (5.0, 0.0, -10.0), mode=M_OBSERVE, auth_ok=True)
    assert d2["decision"] == ALLOW and s.terminal is None


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        grid = build_grid()
        with open(GRID_PATH, "w") as f:
            json.dump(grid, f, indent=2, ensure_ascii=False)
        n = sum(len(grid[k]) for k in ("braking_dist", "geofence", "pos_monitor", "safe_descend"))
        print(f"siatka zapisana: {GRID_PATH} ({n} wpisów)")
        return
    if len(sys.argv) > 1 and sys.argv[1] == "sweep":
        res = run_all()
        os.makedirs(os.path.join(ROOT, "results/FV"), exist_ok=True)
        outp = os.path.join(ROOT, "results/FV", "diff_stats.json")
        with open(outp, "w") as f:
            json.dump(res, f, indent=2, ensure_ascii=False)
        print("=== różnicówka lustro↔produkcja ===")
        print("siatka:", res["stats"]["grid"])
        print("fuzz  :", res["stats"]["fuzz"])
        print("fikst.:", res["stats"]["fixture"])
        print(f"ROZBIEŻNOŚCI: {len(res['diffs'])}")
        for d in res["diffs"][:20]:
            print("  ", d["fn"], d["in"])
        print(f"stats → {outp}")
        return
    print("użycie: build | sweep")


if __name__ == "__main__":
    main()
