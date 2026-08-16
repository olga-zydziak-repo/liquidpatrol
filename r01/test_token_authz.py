#!/usr/bin/env python3
"""r01/test_token_authz.py — DETERMINISTYCZNE testy tokenu operatora (DEMO-B, blok B1; bez SITL).

Egzekwuje semantykę ANEKS_D1 §Semantyka na REALNYM automacie osłony (r01.shield) i REALNEJ warstwie
authz (r01.authz) — przeszukanie przestrzeni stanów SWEEPEM (nie próbki losowe bez ziarna). Pokrywa
(§4 PROMPT_D_BUILD_1):
  (i)   ¬token ⇒ OBSERVE nieosiągalne z ŻADNEGO stanu automatu;
  (ii)  token nie zmienia ŻADNEJ decyzji poza otwarciem OBSERVE;
  (iii) EXPIRE konsumuje token; re-admisja bez nowego tokenu ⇒ REFUSE(NO_AUTH);
  (iv)  pre-autoryzacja i zły admission_seq odrzucane (PREAUTH);
  (v)   nonce-reuse odrzucany (NONCE_REUSE);
  (vi)  R-G i R-POS DOMINUJĄ nad R-AUTH (wektory krzyżowe);
  (vii) PermissionError z mode_of() przy KAŻDEJ decyzji ≠ALLOW.
Uruchom: python3 -m pytest r01/test_token_authz.py  (albo python3 r01/test_token_authz.py)
"""
from __future__ import annotations
import itertools
from r01.shield import (PatrolShield, ALLOW, REFUSE, HOLD, OBSERVING, NOAUTH, DONE, POSDEG,
                        NO_AUTH, POS_DEGRADED, GEOFENCE, ABORT, COMMAND_INVALID, STALE_CMD,
                        M_PATROL, M_HOLD, M_RETURN, M_ABORT, M_OBSERVE)
from r01.authz import Authorizer

IN = (0.0, 0.0, -10.0)      # w obwiedni (¬geo)
FAR = (45.0, 0.0, -10.0)    # poza R_E (geo)
V0 = (0.0, 0.0, 0.0)
MODES = [M_PATROL, M_HOLD, M_RETURN, M_ABORT, M_OBSERVE]


def _fresh():
    sh = PatrolShield(); sh.reset(); return sh


def _pos_degraded():
    """Osłona wprowadzona w POS_DEGRADED (2 ticki flagi, debounce)."""
    sh = _fresh()
    sh.step(0, IN, V0, IN, mode=M_PATROL, pos_flag=True)
    sh.step(1, IN, V0, IN, mode=M_PATROL, pos_flag=True)
    assert sh._pos_refuse
    return sh


def _latched():
    """Osłona zatrzaśnięta (terminal) przez ABORT."""
    sh = _fresh()
    sh.step(0, IN, V0, IN, mode=M_ABORT)
    assert sh.terminal is not None
    return sh


# --------------------------------------------------------------------------- (i)
def test_no_token_no_observe_from_any_state():
    """(i) Bez tokenu (auth_ok=False) stan NIGDY nie staje się OBSERVING — z żadnego pre-stanu,
    dla żadnej kombinacji geo/pos_flag. Eskalacja OBSERVE bez tokenu ⇒ REFUSE (NO_AUTH lub dominujący)."""
    n = 0
    for pre_name, mk in [("fresh", _fresh), ("pos_deg", _pos_degraded), ("latched", _latched)]:
        for tgt in (IN, FAR):
            for pos_flag in (None, True, False):
                sh = mk()
                d = sh.step(99, IN, V0, tgt, mode=M_OBSERVE, pos_flag=pos_flag, auth_ok=False)
                assert d["state"] != OBSERVING, (pre_name, tgt, pos_flag, d)
                assert d["decision"] != ALLOW, (pre_name, tgt, pos_flag, d)
                n += 1
    assert n == 3 * 2 * 3


# --------------------------------------------------------------------------- (ii)
def test_token_only_affects_observe():
    """(ii) Dla trybów ≠OBSERVE token (auth_ok) nie zmienia decyzji/stanu/powodu. Dla OBSERVE
    (geofence-/pos-bezpiecznie, nie-terminal) token przełącza WYŁĄCZNIE NO_AUTH↔OBSERVE."""
    for mode in MODES:
        for pos_flag in (None, False):
            a = _fresh().step(0, IN, V0, IN, mode=mode, pos_flag=pos_flag, auth_ok=False)
            b = _fresh().step(0, IN, V0, IN, mode=mode, pos_flag=pos_flag, auth_ok=True)
            if mode == M_OBSERVE and not pos_flag:
                assert a["decision"] == REFUSE and a["reason"] == NO_AUTH and a["state"] == NOAUTH
                assert b["decision"] == ALLOW and b["state"] == OBSERVING
            else:
                assert (a["decision"], a["reason"], a["state"]) == (b["decision"], b["reason"], b["state"])


# --------------------------------------------------------------------------- (vi)
def test_geofence_dominates_no_auth():
    """(vi) R-G > R-AUTH: OBSERVE za płot bez tokenu ⇒ GEOFENCE (terminal), NIE NO_AUTH."""
    sh = _fresh()
    d = sh.step(0, IN, V0, FAR, mode=M_OBSERVE, auth_ok=False)
    assert d["decision"] == REFUSE and d["reason"] == GEOFENCE and d["state"] == DONE
    assert sh.terminal is not None                      # geofence LATCHUJE (R-AUTH nie)


def test_pos_degraded_dominates_no_auth():
    """(vi) R-POS > R-AUTH: pos_bad (2 ticki) + OBSERVE bez tokenu ⇒ POS_DEGRADED, NIE NO_AUTH."""
    sh = _fresh()
    sh.step(0, IN, V0, IN, mode=M_OBSERVE, pos_flag=True, auth_ok=False)
    d = sh.step(1, IN, V0, IN, mode=M_OBSERVE, pos_flag=True, auth_ok=False)
    assert d["decision"] == REFUSE and d["reason"] == POS_DEGRADED and d["state"] == POSDEG


def test_latch_dominates_no_auth():
    """(vi) latch > R-AUTH: po zatrzaśnięciu (ABORT) OBSERVE bez tokenu ⇒ wciąż ABORT."""
    sh = _latched()
    d = sh.step(1, IN, V0, IN, mode=M_OBSERVE, auth_ok=False)
    assert d["decision"] == REFUSE and d["reason"] == ABORT


# --------------------------------------------------------------------------- odwracalność
def test_no_auth_reversible_nonterminal():
    """R-AUTH ODWRACALNY: NO_AUTH nie latchuje; po nadaniu tokenu ta sama gałąź daje OBSERVE, a cofnięcie
    tokenu wraca do NO_AUTH (żadnego terminal-state pomiędzy)."""
    sh = _fresh()
    d0 = sh.step(0, IN, V0, IN, mode=M_OBSERVE, auth_ok=False)
    assert d0["reason"] == NO_AUTH and sh.terminal is None
    d1 = sh.step(1, IN, V0, IN, mode=M_OBSERVE, auth_ok=True)
    assert d1["decision"] == ALLOW and d1["state"] == OBSERVING and sh.terminal is None
    d2 = sh.step(2, IN, V0, IN, mode=M_OBSERVE, auth_ok=False)
    assert d2["reason"] == NO_AUTH and sh.terminal is None


# --------------------------------------------------------------------------- authz (iii)(iv)(v)
def test_authz_default_deny_and_preauth():
    """(iv) Default-deny + pre-autoryzacja zakazana (¬locked lub zły admission_seq ⇒ PREAUTH)."""
    a = Authorizer()
    assert a.token_auth_ok(0) is False
    assert a.issue_token("op", "n1", 0, locked=False, current_seq=0)["reason"] == "PREAUTH"
    assert a.issue_token("op", "n2", 3, locked=True, current_seq=0)["reason"] == "PREAUTH"
    assert a.token_auth_ok(0) is False
    # anti-bypass: gramatyczne admit('grant observe') NIE jest ważnym tokenem
    a.admit("grant observe")
    assert a.token_auth_ok(0) is False


def test_authz_grant_binds_episode_and_nonce_once():
    """(v) Ważny grant wiąże epizod; nonce jednorazowy (reuse ⇒ NONCE_REUSE)."""
    a = Authorizer()
    r = a.issue_token("op", "N", 0, locked=True, current_seq=0)
    assert r["decision"] == "ALLOW" and r["mode"] == "OBSERVE"
    assert a.token_auth_ok(0) is True and a.token_auth_ok(1) is False
    assert a.issue_token("op", "N", 0, locked=True, current_seq=0)["reason"] == "NONCE_REUSE"
    assert a.verify_chain()


def test_authz_expire_consumes_readmission_needs_new():
    """(iii) EXPIRE konsumuje token; re-admisja (nowy epizod) bez nowego tokenu ⇒ auth_ok False."""
    a = Authorizer()
    a.issue_token("op", "N0", 0, locked=True, current_seq=0)
    assert a.token_auth_ok(0) is True
    assert a.consume_tokens(0) == 1
    assert a.token_auth_ok(0) is False        # konsumpcja
    assert a.token_auth_ok(1) is False        # nowy epizod: brak tokenu
    a.issue_token("op", "N1", 1, locked=True, current_seq=1)
    assert a.token_auth_ok(1) is True


def test_authz_tamper_on_token_fields_detected():
    """Podpis pokrywa operator_id/nonce/admission_seq — tamper wykryty."""
    a = Authorizer()
    a.issue_token("op", "N", 0, locked=True, current_seq=0)
    assert a.verify_chain()
    for field, val in [("nonce", "x"), ("admission_seq", 9), ("operator_id", "mallory")]:
        saved = a.chain[-1][field]; a.chain[-1][field] = val
        assert not a.verify_chain(), field
        a.chain[-1][field] = saved
    assert a.verify_chain()


# --------------------------------------------------------------------------- (vii)
def test_mode_of_denies_non_allow():
    """(vii) mode_of() rzuca PermissionError przy KAŻDEJ decyzji ≠ALLOW (w tym odrzucone tokeny)."""
    a = Authorizer()
    bad = [a.admit("land"),                                        # COMMAND_INVALID
           a.admit("hold", age_s=999),                             # STALE_CMD
           a.issue_token("op", "z", 0, locked=False, current_seq=0),  # PREAUTH
           a.issue_token("op", "z", 5, locked=True, current_seq=0)]   # PREAUTH (zły epizod)
    for rec in bad:
        try:
            a.mode_of(rec); assert False, ("brak PermissionError", rec)
        except PermissionError:
            pass


# --------------------------------------------------------------------------- integracja authz↔shield
def test_integration_authz_drives_shield_no_observe_without_token():
    """Punkt-dławik (r02/gate_run_r02.py:399): auth_ok = authz.token_auth_ok(seq) → shield.step.
    Odtwarza AKT1 DEMO-B: dwell(NO_AUTH) → token → OBSERVE → EXPIRE(konsumpcja) → re-admisja(NO_AUTH)."""
    az = Authorizer(); sh = _fresh(); seq = 0
    # epizod 0: eskalacja bez tokenu → NO_AUTH
    d = sh.step(0, IN, V0, IN, mode=M_OBSERVE, auth_ok=az.token_auth_ok(seq))
    assert d["reason"] == NO_AUTH
    # operator wydaje token dla epizodu 0 (locked) → OBSERVE
    az.issue_token("operator", "t0", seq, locked=True, current_seq=seq)
    d = sh.step(1, IN, V0, IN, mode=M_OBSERVE, auth_ok=az.token_auth_ok(seq))
    assert d["decision"] == ALLOW and d["state"] == OBSERVING
    # EXPIRE: konsumpcja → utrata autorytetu
    az.consume_tokens(seq)
    d = sh.step(2, IN, V0, IN, mode=M_OBSERVE, auth_ok=az.token_auth_ok(seq))
    assert d["reason"] == NO_AUTH
    # re-admisja (nowy epizod 1): stary token nie wskrzesza — trzeba nowego
    seq = 1
    d = sh.step(3, IN, V0, IN, mode=M_OBSERVE, auth_ok=az.token_auth_ok(seq))
    assert d["reason"] == NO_AUTH
    az.issue_token("operator", "t1", seq, locked=True, current_seq=seq)
    d = sh.step(4, IN, V0, IN, mode=M_OBSERVE, auth_ok=az.token_auth_ok(seq))
    assert d["decision"] == ALLOW and d["state"] == OBSERVING
    assert az.verify_chain()


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn(); print(f"  PASS  {fn.__name__}")
    print(f"WERDYKT test_token_authz: PASS ({len(fns)}/{len(fns)})")


if __name__ == "__main__":
    _run_all()
