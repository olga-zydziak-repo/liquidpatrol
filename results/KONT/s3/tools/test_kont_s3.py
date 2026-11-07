"""results/KONT/s3/tools/test_kont_s3.py — testy deterministyczne S3 (PROMPT_KONT_S3 §3; bez SITL).

T0 pass-through: KONT_MODE=0 ⇒ decyzje bajtowo identyczne ze starą osłoną na fiksturze 8 lotów S2 i fiksturze FV
   (4221/1791 ticków), wejścia zrekonstruowane (ANEKS_KONT-3b §1.5); FV dodatkowo vs decyzje zapisane w trace.
T1 maszyna stanów (próg T* − 2·dt, ANEKS_KONT-4 §2.1), T1′ wiek flagi przy REFUSE < 22.000 s na 8 fiksturach S2,
T2 bariera nominalna (R_nom = 27.30, ANEKS_KONT-3b §1.7; R-G-NOM pod ABORT/HOLD/RETURN, ANEKS_KONT-4 §2.2),
T3 tablica ε_b, T4 trzymanie yaw.

Uruchom: PYTHONPATH=.:.certdeps python3 -m pytest -q results/KONT/s3/tools/test_kont_s3.py
"""
from __future__ import annotations
import hashlib
import json
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import r03.config as C
from r01.shield import (PatrolShield, ALLOW, HOLD, REFUSE, POS_DEGRADED, GEOFENCE, ABORT, M_PATROL, M_ABORT,
                        M_HOLD, M_RETURN, M_OBSERVE)
from r03 import kont_shield as KS
from r03.kont_shield import KontShield, R_NOM, T_STAR_S, r_kont, K_NOMINAL, K_KONT, K_REFUSE
from r03.kont_gate import KontCommand, is_pos_refuse
from r03.controllers.safe_descend import safe_descend_step, new_state
from r01.proofs import p9_kont_verify as P

DT = C.DT
IN = (5.0, 0.0, -10.0)
V0 = (0.0, 0.0, 0.0)


def _mk(kont=True):
    s = KontShield(kont_mode=kont)
    s.reset()
    s.pos_debounce_ticks = C.DEBOUNCE_TICKS
    s.pos_hyst_ticks = int(round(C.HYST_M_S / C.DT))
    return s


def _st(s, k, pos=IN, target=None, cs=True, now=None, pos_flag=None, mode=M_PATROL):
    return s.step(k, pos, V0, target if target is not None else pos, mode=mode, pos_flag=pos_flag,
                  cs_gnss_pos=cs, now=now)


# ------------------------------------ T0 --------------------------------------
def _old_new_traces(ticks):
    old = PatrolShield(); old.reset()
    new = KontShield(kont_mode=False); new.reset()
    for k, t in enumerate(ticks):
        old.step(k, t["pos"], t["vel"], t["target"], mode=t["mode"], pos_flag=t["pos_flag"])
        new.step(k, t["pos"], t["vel"], t["target"], mode=t["mode"], pos_flag=t["pos_flag"],
                 cs_gnss_pos=t.get("cs_gnss_pos"), now=t.get("now"))
    return (json.dumps(old.trace, ensure_ascii=False), json.dumps(new.trace, ensure_ascii=False),
            (old.n_pos_enter, old.terminal, old.state), (new.n_pos_enter, new.terminal, new.state))


def test_t0_s2_fixture_bytewise():
    n = 0
    for fl in P.s2_flights():
        ticks, _ = P.s2_fixture(fl)
        a, b, sa, sb = _old_new_traces(ticks)
        assert a == b and sa == sb, fl
        n += len(ticks)
    assert n > 17000


def _fv_ticks():
    man = json.load(open(os.path.join(ROOT, "results/FV/FIXTURE_D5_MANIFEST.json")))
    out = []
    for e in man["files"]:
        p = os.path.join(ROOT, e["path"])
        assert hashlib.sha256(open(p, "rb").read()).hexdigest() == e["sha256"], e["path"]
        rows = [json.loads(l) for l in open(p) if '"t": "tick"' in l]
        assert len(rows) == e["ticks"]
        out.append((e["path"], rows))
    return man, out


def test_t0_fv_fixture_bytewise_and_recorded():
    man, files = _fv_ticks()
    tot = ndesc = match = 0
    for path, rows in files:
        ticks = [{"pos": r["pos"], "vel": (0.0, 0.0, 0.0), "target": r["pos"], "mode": M_PATROL,
                  "pos_flag": bool(r["dr"])} for r in rows]
        a, b, sa, sb = _old_new_traces(ticks)
        assert a == b and sa == sb, path
        rec = [(r["decision"], r["reason"]) for r in rows]
        got = [(d["decision"], d.get("reason")) for d in json.loads(b)]
        match += sum(1 for x, y in zip(rec, got) if x == y)
        tot += len(rows); ndesc += sum(1 for r in rows if r["descending"])
    assert tot == man["totals"]["ticks_total"] == 4221
    assert ndesc == man["totals"]["ticks_descending"] == 1791
    assert match == tot, f"zgodność z decyzjami zapisanymi: {match}/{tot}"


def test_t0_env_default_is_off():
    os.environ.pop(KS.KONT_MODE_ENV, None)
    assert KontShield().kont_mode is False
    os.environ[KS.KONT_MODE_ENV] = "0"
    assert KontShield().kont_mode is False
    os.environ[KS.KONT_MODE_ENV] = "1"
    try:
        assert KontShield().kont_mode is True
    finally:
        os.environ.pop(KS.KONT_MODE_ENV, None)


# ------------------------------------ T1 --------------------------------------
def test_t1_entry_after_debounce_clock_backdated():
    s = _mk()
    _st(s, 0, cs=False, now=10.0)
    assert s.kont_phase() == K_NOMINAL
    d = _st(s, 1, cs=False, now=10.05)
    assert s.kont_phase() == K_KONT and d["decision"] == ALLOW and s.n_kont_enter == 1
    assert abs(d["kont"]["t_kont"] - 0.05) < 1e-9           # zegar od pierwszego ticka flagi
    s2 = _mk()
    _st(s2, 0, cs=False, now=0.0); _st(s2, 1, cs=True, now=0.05); _st(s2, 2, cs=False, now=0.10)
    assert s2.kont_phase() == K_NOMINAL                       # przerwany bieg nie wchodzi


def test_t1_refuse_at_tstar_within_tick():
    s = _mk()
    last_allow = first_ref = None
    for i in range(int(25 / DT)):
        d = _st(s, i, cs=False, now=i * DT)
        if d["decision"] == ALLOW:
            last_allow = d["kont"]["t_kont"]
        elif first_ref is None:
            first_ref = d
    thr = T_STAR_S - KS.T_MARGIN_TICKS * DT                   # 21.9 (DT = r01/config.py:41 przez r03/config)
    assert last_allow < thr
    assert first_ref["rule"] == KS.R_KONT and first_ref["reason"] == POS_DEGRADED and first_ref["detail"] == "T*"
    assert thr - 1e-9 <= first_ref["kont"]["t_kont"] <= thr + DT + 1e-9


def test_t1prim_true_flag_age_at_refuse_below_22():
    C_ = P.mirror_consts()
    for fl in P.s2_flights():
        o = P.s2_offline_decisions(fl, C_)
        assert o["n_kont_enter"] == 1, (fl, o)
        assert o["refuse_minus_flag_s"] < 22.000, (fl, o)     # ANEKS_KONT-4 §2.1


def test_t1_barrier_per_bucket():
    for k in (0, 9, 21):
        R = r_kont(k, 32.0)
        for off, exp in ((-0.001, ALLOW), (0.0, ALLOW), (0.001, REFUSE)):        # ALLOW ⇔ r_est ≤ R(k)
            s = _mk()
            pos = (R + off, 0.0, -10.0)
            _st(s, 0, pos=pos, cs=False, now=0.0)
            _st(s, 1, pos=(0.0, 0.0, -10.0), cs=False, now=DT)
            d = _st(s, 2, pos=pos, cs=False, now=k + 0.5)
            assert d["decision"] == exp, (k, off, d)
            if exp == REFUSE:
                assert d["rule"] == KS.R_KONT and d["detail"] == "bariera" and d["kont"]["k"] == k


def test_t1_return_nominal_hysteresis_and_second_episode():
    s = _mk()
    M = s.pos_hyst_ticks
    for i, now in enumerate((0.0, DT, 22.5)):
        d = _st(s, i, cs=False, now=now)
    assert d["decision"] == REFUSE and s.kont_phase() == K_REFUSE
    k = 3
    for j in range(M - 1):
        d = _st(s, k, cs=True, now=22.5 + (j + 1) * DT); k += 1
        assert d["decision"] == REFUSE                        # REFUSE trzyma do M
    d = _st(s, k, cs=True, now=22.5 + M * DT); k += 1
    assert s.kont_phase() == K_NOMINAL and d["decision"] == ALLOW   # odwracalny jak POS_DEGRADED
    for j in range(2):
        d = _st(s, k, cs=False, now=40.0 + j * DT); k += 1
    assert s.kont_phase() == K_KONT and s.n_kont_enter == 2 and abs(d["kont"]["t_kont"] - DT) < 1e-9


def test_t1_old_pos_monitor_armed_in_kont():
    s = _mk()
    _st(s, 0, cs=False, now=0.0); _st(s, 1, cs=False, now=DT)
    d = _st(s, 2, cs=False, now=2 * DT, pos_flag=True)
    assert d["decision"] == ALLOW
    d = _st(s, 3, cs=False, now=3 * DT, pos_flag=True)
    assert d["rule"] == "R-POS" and d["reason"] == POS_DEGRADED     # ANEKS_KONT-3b §1.4
    assert KontCommand(True).descend(1.5, 33.0)[3] == 33.0


# ------------------------------------ T2 --------------------------------------
def test_t2_nominal_barrier():
    assert R_NOM == 27.30
    for r, exp in ((R_NOM - 0.01, ALLOW), (R_NOM, ALLOW), (R_NOM + 0.01, REFUSE), (27.50, REFUSE)):
        s = _mk()
        d = _st(s, 0, pos=(r, 0.0, -10.0), target=(r + 1.0, 0.0, -10.0))
        assert d["decision"] == exp, (r, d)
        if exp == REFUSE:
            assert d["rule"] == KS.R_G_NOM and d["reason"] == GEOFENCE and s.terminal is None
            assert math.hypot(d["applied"][0], d["applied"][1]) <= r + 1e-12
    s = _mk()
    r = R_NOM + 0.01
    d = _st(s, 0, pos=(r, 0.0, -10.0), target=(r - 1.0, 0.0, -10.0))
    assert d["decision"] == ALLOW                             # do środka zawsze ALLOW
    d = _st(s, 1, pos=(r, 0.0, -10.0), target=(r + 1.0, 2.0, -10.0))
    assert d["rule"] == KS.R_G_NOM and d["applied"][0] == r and d["applied"][1] == 2.0   # styczna zachowana
    d = _st(s, 2, pos=(r, 0.0, -10.0), target=(r - 0.5, 0.0, -10.0))
    assert d["decision"] == ALLOW and s.terminal is None      # bez zatrzasku
    kc = KontCommand(True)
    v = kc.patrol({"rule": KS.R_G_NOM}, (2.0, 1.5, 0.0), 10.0, (r, 0.0, -10.0))
    assert v == (0.0, 1.5, 0.0, 10.0)
    assert KontCommand(False).patrol({"rule": KS.R_G_NOM}, (2.0, 1.5, 0.0), 10.0, (r, 0.0, -10.0))[0] == 2.0


def test_t2_nominal_barrier_below_abort_hold_return():
    r = R_NOM + 0.01
    out = (r + 1.0, 0.5, -10.0)
    for md, rule, dec in ((M_HOLD, "R-H", HOLD), (M_RETURN, "R-R", HOLD), (M_ABORT, "R-A", REFUSE)):
        for cs in (True, False):
            s = _mk()
            d = _st(s, 0, pos=(r, 0.0, -10.0), target=out, cs=cs, mode=md)
            assert d["rule"] == rule and d["decision"] == dec, (md, cs, d)
            assert d["applied"] == [r, 0.0, -10.0]             # cel/zawis nietknięty przez R-G-NOM
    s = _mk()
    d = s.step(0, (r, 0.0, -10.0), V0, out, mode=M_OBSERVE, auth_ok=False, cs_gnss_pos=True)
    assert d["rule"] == KS.R_G_NOM                            # R-G-NOM nad R-AUTH (klasa ALLOW)


# ------------------------------------ T3 --------------------------------------
def test_t3_eps_table_matches_freeze():
    f = KS.freeze_check(ROOT)
    assert f["sha_ok"] and f["eps_ok"] and f["delta_ok"] and f["tstar_ok"], f
    assert f["r_nom_json"] == 27.51 and f["r_nom_code"] == 27.30          # 3b §1.7: jedyna liczba zmieniona
    assert R_NOM <= r_kont(0, 32.0)


# ------------------------------------ T4 --------------------------------------
def test_t4_yaw_hold_descend():
    cfg = {"v_desc_fast": C.V_DESC_FAST, "v_desc_land": C.V_DESC_LAND, "desc_fast_dur": 2.0, "desc_total": 5.0}
    for kont, expect in ((True, 76.58), (False, 0.0)):
        kc = KontCommand(kont)
        st = new_state()
        yaws = []
        for i, heading in enumerate((76.58, 10.0, -100.0, 0.0)):
            vdesc, _, _, st = safe_descend_step(st, float(i), cfg)
            cmd = kc.descend(vdesc, heading)
            assert cmd[:3] == (0.0, 0.0, vdesc)
            yaws.append(cmd[3])
        assert yaws == [expect] * 4, (kont, yaws)
    kc = KontCommand(True)
    kc.descend(1.5, 50.0); kc.release()
    assert kc.descend(1.5, -20.0)[3] == -20.0                 # nowy epizod łapie nowy heading


def test_t4_refuse_classifier():
    assert is_pos_refuse({"decision": REFUSE, "reason": POS_DEGRADED})
    assert not is_pos_refuse({"decision": REFUSE, "reason": GEOFENCE})
