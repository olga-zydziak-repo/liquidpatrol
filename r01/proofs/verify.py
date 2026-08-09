"""r01/proofs/verify.py — P1 (własności automatu osłony R0.1) przez 1-indukcję w z3.

Port kształtu z liquidsight/proofs/verify.py; MODEL = lustro r01/shield.py:_decide (nowy automat).
Automat R0.2 (7 liści — R0.1 + OBSERVE): wejścia geo(Bool, naruszenie geofence — arytmetyka
bariery należy do P2-analog), mode∈{PATROL,HOLD,RETURN,ABORT,OBSERVE}. Stan: tm(terminal), rsn, st.
7 liści (priorytet): latch, geo, abort, hold, return, OBSERVE, patrol.
OBSERVE = klasa ALLOW PONIŻEJ R-G (jak patrol) — geofence nadrzędny z priorytetu (PRE_R02 §2.4).

Zobowiązania: BAZA Inv(c0), KROK Inv(c) ⇒ Inv(c') ∧ P1(a..d). z3 sprawdza NEGACJĘ (oczekiwane UNSAT).
Uruchom: PYTHONPATH=.certdeps python3 -m r01.proofs.verify
"""
from __future__ import annotations
import hashlib, json, os, sys
import z3

_HERE = os.path.dirname(os.path.abspath(__file__))
CERT = os.path.join(_HERE, "certs", "P1.json")

# enumeracje (Int) — muszą zgadzać się z r01/shield.py oraz conformance.py
ALLOW, HOLD, REFUSE = 0, 1, 2
NONE, GEOFENCE, COMMAND_INVALID, STALE_CMD, ABORT_R = 0, 1, 2, 3, 4
PATROL, HOLDING, RETURNING, DONE, OBSERVING = 0, 1, 2, 3, 4
M_PATROL, M_HOLD, M_RETURN, M_ABORT, M_OBSERVE = 0, 1, 2, 3, 4


def _sv(p):
    return {"tm": z3.Bool(p+"tm"), "rsn": z3.Int(p+"rsn"), "st": z3.Int(p+"st")}


def domain(c):
    # st ∈ {PATROL,HOLDING,RETURNING,DONE,OBSERVING} = 0..4 (R0.2: +OBSERVING)
    return z3.And(c["rsn"] >= 0, c["rsn"] <= 4, c["st"] >= 0, c["st"] <= 4)


def inv(c):
    """Niezmiennik: terminal ⇒ (reason ≠ NONE ∧ stan = DONE); (stan=DONE) ⇔ terminal."""
    I1 = z3.Implies(c["tm"], z3.And(c["rsn"] != NONE, c["st"] == DONE))
    I2 = (c["st"] == DONE) == c["tm"]
    return z3.And(domain(c), I1, I2)


def valid(mode):
    # mode ∈ {PATROL,HOLD,RETURN,ABORT,OBSERVE} = 0..4 (R0.2: +OBSERVE)
    return z3.And(mode >= 0, mode <= 4)


def tau(c, geo, mode):
    """Relacja przejścia — lustro r01.shield._decide. Zwraca (post, decision, leaves).
    Priorytet (7 liści): latch > geo > abort > hold > return > OBSERVE > patrol.
    OBSERVE i patrol = klasa ALLOW PONIŻEJ R-G — R-G (L_geo) ma priorytet nad oboma (PRE_R02 §2.4)."""
    L_latch = c["tm"]
    base = z3.Not(c["tm"])
    L_geo = z3.And(base, geo)
    ok = z3.And(base, z3.Not(geo))
    L_abort = z3.And(ok, mode == M_ABORT)
    L_hold = z3.And(ok, mode == M_HOLD)
    L_return = z3.And(ok, mode == M_RETURN)
    L_observe = z3.And(ok, mode == M_OBSERVE)               # R0.2: 7. liść (ALLOW, poniżej R-G)
    L_patrol = z3.And(ok, mode == M_PATROL)
    dec = z3.If(z3.Or(L_latch, L_geo, L_abort), REFUSE,
                z3.If(z3.Or(L_hold, L_return), HOLD, ALLOW))  # L_observe ∨ L_patrol → ALLOW
    tm2 = z3.Or(L_latch, L_geo, L_abort)
    rsn2 = z3.If(L_latch, c["rsn"], z3.If(L_geo, GEOFENCE, z3.If(L_abort, ABORT_R, NONE)))
    st2 = z3.If(tm2, DONE, z3.If(L_hold, HOLDING,
               z3.If(L_return, RETURNING, z3.If(L_observe, OBSERVING, PATROL))))
    cp = {"tm": tm2, "rsn": rsn2, "st": st2}
    leaves = {"L_geo": L_geo, "L_patrol": L_patrol, "L_observe": L_observe}
    return cp, dec, leaves


def props(c, cp, dec, geo, leaves):
    """P1(a)–(d)."""
    # P1a: ALLOW ⇒ ¬geo ∧ ¬terminal (osłona przepuszcza tylko gdy geofence-bezpiecznie)
    P1a = z3.Implies(dec == ALLOW, z3.And(z3.Not(geo), z3.Not(c["tm"])))
    # P1b: geo ⇒ REFUSE ∧ (¬term ∧ geo ⇒ reason=GEOFENCE)
    P1b = z3.And(z3.Implies(geo, dec == REFUSE),
                 z3.Implies(z3.And(z3.Not(c["tm"]), geo), cp["rsn"] == GEOFENCE))
    # P1c: REFUSE ⇒ reason ∈ {GEOFENCE, COMMAND_INVALID, STALE_CMD, ABORT}
    P1c = z3.Implies(dec == REFUSE, z3.Or(cp["rsn"] == GEOFENCE, cp["rsn"] == COMMAND_INVALID,
                                          cp["rsn"] == STALE_CMD, cp["rsn"] == ABORT_R))
    # P1d: terminal monotoniczny (raz REFUSE — zawsze REFUSE): terminal ⇒ terminal' ∧ REFUSE
    P1d = z3.Implies(c["tm"], z3.And(cp["tm"], dec == REFUSE))
    # P1e (R0.2): OBSERVE aktywny ⇒ ¬geo ∧ ¬terminal ∧ ALLOW (7. liść siedzi PONIŻEJ R-G —
    #  śledzenie NIGDY nie łamie obwiedni Z KONSTRUKCJI priorytetu, nie dodatkowej reguły; PRE §2.4)
    P1e = z3.Implies(leaves["L_observe"], z3.And(z3.Not(geo), z3.Not(c["tm"]), dec == ALLOW))
    return {"P1a": P1a, "P1b": P1b, "P1c": P1c, "P1d": P1d, "P1e": P1e}


def prove():
    c = _sv("c_")
    geo = z3.Bool("geo"); mode = z3.Int("mode")
    cp, dec, leaves = tau(c, geo, mode)
    P = props(c, cp, dec, geo, leaves)
    results = {}
    # BAZA: c0 = reset (tm=False, rsn=NONE, st=PATROL)
    c0 = {"tm": z3.BoolVal(False), "rsn": z3.IntVal(NONE), "st": z3.IntVal(PATROL)}
    sb = z3.Solver(); sb.add(z3.Not(inv(c0)))
    results["base"] = str(sb.check())
    # KROK
    pre = z3.And(inv(c), valid(mode))
    for name, goal in [("inv_step", inv(cp)), *[(k, v) for k, v in P.items()]]:
        s = z3.Solver(); s.add(pre); s.add(z3.Not(goal))
        results[name] = str(s.check())
    return results


def _self_sha():
    return hashlib.sha256(open(__file__, "rb").read()).hexdigest()


def main():
    res = prove()
    allunsat = all(v == "unsat" for v in res.values())
    print("=== P1 dowód (z3) — automat osłony R0.1 ===")
    for k, v in res.items():
        print(f"  {k}: {v}" + ("  ✓" if v == "unsat" else "  !! (SPODZIEWANO unsat)"))
    verdict = "PROVED" if allunsat else "UNPROVEN"
    print(f"WERDYKT P1: {verdict}")
    if not allunsat:
        print("!! Któreś zobowiązanie NIE jest unsat — kontrprzykład (zasada: UNPROVEN, nie zmiękczamy).")
        sys.exit(1)
    cert = {
        "property": "P1", "verdict": "PROVED", "method": "1-induction (z3)",
        "z3_pip": "5.0.0.0", "z3_lib": z3.get_version_string(), "obligations": res,
        "automaton": "r01/shield.py:_decide (7 liści: latch>geo>abort>hold>return>OBSERVE>patrol; "
                     "ALLOW/HOLD/REFUSE, reasons GEOFENCE/COMMAND_INVALID/STALE_CMD/ABORT)",
        "leaves": 7,
        "properties": {
            "P1a": "ALLOW ⇒ ¬geo ∧ ¬terminal (przepuszcza tylko geofence-bezpiecznie)",
            "P1b": "geo ⇒ REFUSE ∧ (¬term ∧ geo ⇒ reason=GEOFENCE)",
            "P1c": "REFUSE ⇒ reason ∈ {GEOFENCE,COMMAND_INVALID,STALE_CMD,ABORT}",
            "P1d": "terminal monotoniczny: terminal ⇒ terminal' ∧ REFUSE (latch)",
            "P1e": "OBSERVE ⇒ ¬geo ∧ ¬terminal ∧ ALLOW (7. liść poniżej R-G — śledzenie nie łamie obwiedni)",
        },
        "assumptions": [
            "geo = boolowski predykat naruszenia geofence; arytmetyka bariery (radial+"
            "hamowanie) jest przedmiotem P2-analog (osobne twierdzenie warunkowe)",
            "ŻYWOTNOŚĆ OSŁONY (warunek EGZEKWOWANY kodem, dopisany R0.2/fix-G5): P1 opisuje decyzję "
            "ŻYWEJ osłony — produkującej werdykt co tick. Martwa pętla decyzyjna NIE jest objęta P1 "
            "(werdykt wtedy nie powstaje). Regresja fix#2 (odsprzężony streamer) mogła utrzymywać "
            "stary setpoint mimo martwej osłony (zombie-stream) → PX4 nie widział utraty offboard. "
            "Domknięte kodem: dead-man streamera — brak odświeżenia setpointu przez N ticków (N=6=0.3 s "
            "@20 Hz [PROWIZORYCZNE/A4: N>max legalnego stalla pętli; live-fed re-derywacja z rozkładu "
            "stalli w torze C]) ⇒ strumień MILKNIE ⇒ natywny failsafe warstwy-0 (COM_OF_LOSS_T). "
            "Własność 'martwa osłona ⇒ bezpieczne przejęcie warstwy-0' jest więc WYMUSZONA, nie "
            "założona (egzekutor r02/gate_run_r02.py:_streamer; dowód własności r02/test_deadman.py PASS)."],
        "code_refs": {"shield": "r01/shield.py:_decide", "config": "r01/config.py (R_E, obwiednia)"},
        "note_discrepancy": "ABORT dodane jako 4. reason (operator) poza 3 z PRE_R01 §8 — jawnie",
        "model_sha256": _self_sha(),
    }
    os.makedirs(os.path.dirname(CERT), exist_ok=True)
    if os.path.exists(CERT):
        old = json.load(open(CERT))
        same = (old.get("model_sha256") == cert["model_sha256"] and old.get("obligations") == res)
        print(f"certyfikat istnieje — zgodność: {'TAK' if same else 'NIE (zmiana!)'}")
    json.dump(cert, open(CERT, "w"), indent=2, ensure_ascii=False)
    print(f"zapisano {CERT}  (sha={cert['model_sha256'][:16]}…)")


if __name__ == "__main__":
    main()
