"""r01/test_core.py — testy jednostkowe rdzenia (bez env/ROS). Uruchom: python3 -m r01.test_core"""
from __future__ import annotations
from r01 import config
from r01.config import ShieldConfig, R_E, R_ROUTE, corner_waypoints
from r01.shield import (PatrolShield, ALLOW, HOLD, REFUSE, GEOFENCE, ABORT,
                        M_PATROL, M_HOLD, M_ABORT)
from r01.language import parse, in_grammar
from r01.authz import Authorizer
from r01.memory import SemanticMemory

N = 0
def ok(cond, msg):
    global N
    assert cond, "FAIL: " + msg
    N += 1

# --- A2 zawieranie ---------------------------------------------------------
def test_containment():
    cfg = ShieldConfig()
    ok(cfg.containment_ok(), "A2: nierówność zawierania musi się domykać")
    ok(R_ROUTE + cfg.delta_margin <= cfg.r_e, f"A2: R_route+Δ={R_ROUTE+cfg.delta_margin:.2f} ≤ R_E={cfg.r_e}")
    # narożniki trasy wewnątrz R_E
    for (x, y, z) in corner_waypoints():
        ok((x*x+y*y) ** 0.5 <= cfg.r_e, "narożnik trasy wewnątrz R_E")

# --- Osłona ----------------------------------------------------------------
def test_shield_allow_nominal():
    s = PatrolShield(); s.reset()
    d = s.step(0, pos=(0,0,-10), vel=(0,0,0), target=(20,20,-10), mode=M_PATROL)
    ok(d["decision"] == ALLOW, "nominal w obwiedni → ALLOW")
    ok(d["applied"] == [20.0,20.0,-10.0], "ALLOW przepuszcza setpoint planera")

def test_shield_refuse_geofence_target():
    s = PatrolShield(); s.reset()
    d = s.step(0, pos=(0,0,-10), vel=(0,0,0), target=(45,0,-10), mode=M_PATROL)  # 45>32
    ok(d["decision"] == REFUSE and d["reason"] == GEOFENCE, "cel poza R_E → REFUSE(GEOFENCE)")
    ok(d["applied"] == [0.0,0.0,-10.0], "REFUSE stosuje hold-setpoint (nie urywa strumienia)")
    # latch: kolejny tick nawet nominalny nadal REFUSE
    d2 = s.step(1, pos=(0,0,-10), vel=(0,0,0), target=(0,0,-10), mode=M_PATROL)
    ok(d2["decision"] == REFUSE, "REFUSE zatrzaśnięty (terminal latch)")

def test_shield_refuse_predictive():
    s = PatrolShield(); s.reset()
    # pozycja blisko obwiedni + duża prędkość na zewnątrz → pozycja+hamowanie > R_E
    d = s.step(0, pos=(31,0,-10), vel=(3,0,0), target=(31.5,0,-10), mode=M_PATROL)
    ok(d["decision"] == REFUSE and d["reason"] == GEOFENCE, "predykcja pozycja+hamowanie>R_E → REFUSE")

def test_shield_hold():
    s = PatrolShield(); s.reset()
    d = s.step(0, pos=(5,5,-10), vel=(0,0,0), target=(20,20,-10), mode=M_HOLD)
    ok(d["decision"] == HOLD, "tryb HOLD → HOLD")
    ok(d["applied"] == [5.0,5.0,-10.0], "HOLD stosuje pozycję bieżącą")
    ok(s.n_hold_enter == 1, "licznik HOLD-enter")

def test_shield_abort():
    s = PatrolShield(); s.reset()
    d = s.step(0, pos=(0,0,-10), vel=(0,0,0), target=(20,20,-10), mode=M_ABORT)
    ok(d["decision"] == REFUSE and d["reason"] == ABORT, "ABORT → REFUSE(ABORT)")

def test_outcome_disjointness():
    # ODMOWA ⇔ terminal
    s = PatrolShield(); s.reset()
    s.step(0, pos=(0,0,-10), vel=(0,0,0), target=(45,0,-10), mode=M_PATROL)
    o = s.outcome(env_success=True)   # nawet env_success — odmowa wygrywa
    ok(o["wynik"] == "ODMOWA", "terminal → ODMOWA (rozłączna, nie SUKCES)")
    # SUKCES
    s2 = PatrolShield(); s2.reset()
    s2.step(0, pos=(0,0,-10), vel=(0,0,0), target=(20,20,-10), mode=M_PATROL)
    ok(s2.outcome(env_success=True)["wynik"] == "SUKCES", "bez odmowy + sukces → SUKCES")
    # PORAZKA (wrong_action)
    s3 = PatrolShield(); s3.reset()
    s3.step(0, pos=(0,0,-10), vel=(0,0,0), target=(0,0,-10), mode=M_PATROL)
    ok(s3.outcome(env_success=True, wrong_action=True)["wynik"] == "PORAZKA", "wrong_action → PORAZKA")
    # PORAZKA (brak sukcesu bez odmowy)
    s4 = PatrolShield(); s4.reset()
    s4.step(0, pos=(0,0,-10), vel=(0,0,0), target=(0,0,-10), mode=M_PATROL)
    ok(s4.outcome(env_success=False)["wynik"] == "PORAZKA", "brak sukcesu bez odmowy → PORAZKA")

# --- Gramatyka -------------------------------------------------------------
def test_grammar():
    for c, a in [("start patrol","START_PATROL"),("hold","HOLD"),("resume","RESUME"),
                 ("return home","RETURN_HOME"),("abort","ABORT")]:
        ok(parse(c).action == a, f"parse '{c}'")
    ok(parse("  START   Patrol ").action == "START_PATROL", "normalizacja")
    for bad in ["fly to the red box","land","", "patrol start","hold now"]:
        ok(parse(bad) is None, f"poza gramatyką: '{bad}'")

# --- Admisja + HMAC --------------------------------------------------------
def test_authz():
    a = Authorizer()
    r = a.admit("start patrol")
    ok(r["decision"] == "ALLOW" and r["mode"] == "PATROL", "ALLOW start patrol")
    ok(a.admit("land")["reason"] == "COMMAND_INVALID", "poza gramatyką → COMMAND_INVALID")
    ok(a.admit("hold", age_s=5.0)["reason"] == "STALE_CMD", "przeterminowana → STALE_CMD")
    ok(a.admit("start patrol", target_xy=(45,0))["reason"] == "GEOFENCE", "cel poza R_E → GEOFENCE")
    ok(a.verify_chain(), "łańcuch HMAC weryfikowalny")
    # tamper
    a.chain[0]["command_raw"] = "abort"
    ok(not a.verify_chain(), "sabotaż wykryty przez HMAC")
    # mode_of odmawia nie-ALLOW
    a2 = Authorizer(); rec = a2.admit("land")
    try:
        a2.mode_of(rec); ok(False, "mode_of powinien odmówić")
    except PermissionError:
        ok(True, "mode_of odmawia nie-ALLOW")

# --- Pamięć korekt ---------------------------------------------------------
def test_memory():
    m = SemanticMemory()
    m.learn("halt", "hold")
    ok(m.resolve("halt") == "hold", "alias rozwiązany przed parserem")
    ok(in_grammar(m.resolve("halt")), "rozwiązany alias ∈ gramatyka")
    try:
        m.learn("hold", "resume"); ok(False, "alias=słowo gramatyki powinien paść")
    except ValueError:
        ok(True, "zakaz nadpisania słowa gramatyki")
    try:
        m.learn("xyz", "land"); ok(False, "cel poza gramatyką powinien paść")
    except ValueError:
        ok(True, "cel aliasu poza gramatyką odrzucony")
    ok(m.verify_chain(), "łańcuch korekt weryfikowalny")

if __name__ == "__main__":
    for fn in [test_containment, test_shield_allow_nominal, test_shield_refuse_geofence_target,
               test_shield_refuse_predictive, test_shield_hold, test_shield_abort,
               test_outcome_disjointness, test_grammar, test_authz, test_memory]:
        fn()
    print(f"[r01.test_core] OK — {N} asercji, wszystkie testy PASS")
