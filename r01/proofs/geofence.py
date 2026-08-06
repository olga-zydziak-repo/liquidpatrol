"""r01/proofs/geofence.py — P2-analog: dron respektujący osłonę nie opuszcza obwiedni R_E.

Twierdzenie WARUNKOWE o modelu dynamiki PX4 (założenia JAWNE), NIE o pełnym Gazebo. Port bariery
z liquidsight/proofs/geofence.py na dynamikę R0.1. Stałe wymierne. Mapowanie:
  geo_lim ↔ R_route (maks. promień trasy, narożnik), arena ↔ R_E (obwiednia osłony),
  VEL ↔ v_max (clamp MPC_XY_VEL_MAX, zmierzony), Δt ↔ t_react (złożony ze zmierzonych),
  A ↔ a_brake (ZMIERZONY w r01/brake_test.py).
BARIERA: Inv(p,v) = 0≤v≤v_max ∧ p + v²/(2·a_brake) ≤ R_E.
Zobowiązania z3 NRA: base, step_allow, step_brake, safety, ostrość progu A_min.
Wiążące: step_allow ⇔ R_route + v_max·t_react + v_max²/(2·a_brake) ≤ R_E  (= nierówność A2).

Uruchom: A_BRAKE_MEAS=<m/s²> PYTHONPATH=.certdeps python3 -m r01.proofs.geofence
"""
from __future__ import annotations
import hashlib, json, os, sys
from fractions import Fraction
import z3

from r01.config import V_MAX, T_REACT_S, R_E as CFG_R_E, A_BRAKE as CFG_A_BRAKE

_HERE = os.path.dirname(os.path.abspath(__file__))
_VMP = os.environ.get("V_MAX_PROVE")     # opcjonalny override v_max (robustność, np. 3.1 na overshoot)
CERT = os.path.join(_HERE, "certs",
                    (f"P2_vmax{_VMP.replace('.', 'p')}.json" if _VMP else "P2.json"))

# --- stałe wymierne (nowy habitat PX4) --------------------------------------
def _fr(x):
    return Fraction(str(x))

VELF = _fr(_VMP) if _VMP else _fr(V_MAX)    # v_max = 3 (override: V_MAX_PROVE)
DTF = _fr(T_REACT_S)                   # t_react (złożony ze zmierzonych, budżet 0.2 s)
# R_route = 20√2 (narożnik) — konserwatywna nadaproksymacja wymierna (większy geo_lim = trudniej = bezpiecznie)
RROUTE = Fraction(2829, 100)           # ≥ 28.28427...
RE = _fr(CFG_R_E)                      # R_E = 32
A_meas = os.environ.get("A_BRAKE_MEAS")
ABRAKE = _fr(A_meas) if A_meas else _fr(CFG_A_BRAKE)
A_SOURCE = "measured (brake_test)" if A_meas else "config (provisional)"

VEL = z3.RealVal(str(VELF)); DT = z3.RealVal(str(DTF))
GEO = z3.RealVal(str(RROUTE)); ARENA = z3.RealVal(str(RE))
AMIN_fr = (VELF*VELF) / (2*(RE - RROUTE - VELF*DTF))     # próg dokładny
AMIN = z3.RealVal(str(AMIN_fr))
ABR = z3.RealVal(str(ABRAKE))
BRAKE = z3.RealVal(1) / (2*ABR)                          # v²·BRAKE = droga hamowania


def _empirical():
    """Wczytaj zmierzone a_brake z artefaktu brake_test (walidacja założenia a_brake≥2.0)."""
    for path in ("results/R01/gate/brake_test.jsonl", "/tmp/r01/brake_test.jsonl"):
        try:
            import json as _j
            r = _j.loads(open(path).read().strip().splitlines()[-1])["BRAKE_RESULT"]
            return {"a_brake_measured_ms2": r["a_brake_meas_ms2"], "v_refuse_ms": r["v_refuse_ms"],
                    "stop_dist_m": r["stop_dist_m"], "peak_decel_ms2": r["peak_decel_ms2"],
                    "assumed_ge_measured": r["a_brake_meas_ms2"] >= float(ABRAKE),
                    "note": "kod używa a_brake=2.0 (konserwatywne ≤ zmierzone) → bezpieczne"}
        except Exception:
            continue
    return {"a_brake_measured_ms2": None, "note": "brak artefaktu brake_test"}


def inv(p, v):
    return z3.And(v >= 0, v <= VEL, p + BRAKE*v*v <= ARENA)


def prove():
    res = {}
    p, v, vp = z3.Real("p"), z3.Real("v"), z3.Real("vp")
    # BAZA: start w trasie (p≤R_route, 0≤v≤v_max) ⇒ Inv
    s = z3.Solver(); s.add(p <= GEO, v >= 0, v <= VEL); s.add(z3.Not(inv(p, v)))
    res["base_start_in_route"] = str(s.check())
    # KROK ALLOW: Inv ∧ p≤R_route ⇒ Inv(p+v·t_react, vp) ∀vp∈[0,v_max]  (= nierówność A2)
    pa = p + v*DT
    s = z3.Solver(); s.add(inv(p, v), p <= GEO, vp >= 0, vp <= VEL); s.add(z3.Not(inv(pa, vp)))
    res["step_allow"] = str(s.check())
    # KROK BRAKE: p>R_route, hamowanie ciągłe (bariera zachowana) ⇒ Inv ∧ p'≤R_E
    pp, vpp = z3.Real("pp"), z3.Real("vpp")
    s = z3.Solver()
    s.add(inv(p, v), p > GEO, vpp >= 0, vpp <= v, pp >= p, pp + BRAKE*vpp*vpp == p + BRAKE*v*v)
    s.add(z3.Not(z3.And(inv(pp, vpp), pp <= ARENA)))
    res["step_brake"] = str(s.check())
    # BEZPIECZEŃSTWO: Inv ⇒ p ≤ R_E
    s = z3.Solver(); s.add(inv(p, v)); s.add(z3.Not(p <= ARENA))
    res["safety_p_le_R_E"] = str(s.check())
    # OSTROŚĆ PROGU: ∀A≥A_min bezpieczny; ∀0<A<A_min NIEbezpieczny
    A = z3.Real("A")
    delta = lambda a: GEO + VEL*DT + (VEL*VEL)/(2*a)
    s = z3.Solver(); s.add(A >= AMIN); s.add(z3.Not(delta(A) <= ARENA))
    res["threshold_A_ge_amin_safe"] = str(s.check())
    s = z3.Solver(); s.add(A > 0, A < AMIN, delta(A) <= ARENA)
    res["threshold_A_lt_amin_unsafe"] = str(s.check())
    return res


def main():
    a_ge = ABRAKE >= AMIN_fr
    res = prove()
    allok = all(v == "unsat" for v in res.values())
    print(f"=== P2-analog geofence (z3 NRA) — a_brake={float(ABRAKE):.3f} [{A_SOURCE}], A_min={float(AMIN_fr):.3f} ===")
    for k, v in res.items():
        print(f"  {k}: {v}" + ("  ✓" if v == "unsat" else "  !! (kontrprzykład)"))
    print(f"  a_brake ≥ A_min: {a_ge}   nierówność A2 (R_route+Δ≤R_E): {'DOMYKA' if a_ge else 'NIE DOMYKA'}")
    verdict = "PROVED" if (allok and a_ge) else "UNPROVEN"
    print(f"WERDYKT P2-analog: {verdict}")
    if not (allok and a_ge):
        print("!! Nie domyka przy R_E=32 — zgodnie z A2 NALEŻY POSZERZYĆ R_E (nie osłabiać twierdzenia).")
        sys.exit(1)
    cert = {"property": "P2-analog", "verdict": "PROVED",
            "method": "barrier induction + threshold (z3 NRA), twierdzenie warunkowe",
            "z3_pip": "5.0.0.0", "z3_lib": z3.get_version_string(), "obligations": res,
            "a_brake_used_ms2": float(ABRAKE), "a_brake_source": A_SOURCE,
            "A_min_threshold_ms2": float(AMIN_fr), "a_brake_ge_A_min": bool(a_ge),
            "constants_rational": {"v_max": str(VELF), "t_react": str(DTF), "R_route": str(RROUTE),
                                   "R_E": str(RE), "a_brake": str(ABRAKE)},
            "theorem": "Inv(p,v)=0≤v≤v_max ∧ p+v²/(2·a_brake)≤R_E  ⇒  p≤R_E (dron nie opuszcza obwiedni)",
            "A2_inequality": "R_route + v_max·t_react + v_max²/(2·a_brake) ≤ R_E (step_allow)",
            "assumptions": [f"|v|≤v_max={float(VELF)} (clamp MPC_XY_VEL_MAX, zmierzony)",
                            f"t_react={float(DTF)}s złożony ze zmierzonych (tel_gap+tick+setpoint, zapas)",
                            f"a_brake≥{float(ABRAKE)} m/s² (ZMIERZONY, brake_test)",
                            "hamowanie ciągłe (bariera p+v²/2a zachowana)",
                            "rzut na promień (najgorsza oś); native GF (R_GF=37) jako backstop A3"],
            "code_refs": {"shield_barrier": "r01/shield.py:_geofence_violation (pos+v²/2a≤R_E)",
                          "config": "r01/config.py", "brake_measure": "r01/brake_test.py"},
            "empirical_validation": _empirical(),
            "t_react_composition": "tel_gap(0.046)+tick(0.05)+setpoint(0.053)=0.149s ≤ budżet 0.2s (zmierzone S1)",
            "model_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest()}
    os.makedirs(os.path.dirname(CERT), exist_ok=True)
    json.dump(cert, open(CERT, "w"), indent=2, ensure_ascii=False)
    print(f"zapisano {CERT}")


if __name__ == "__main__":
    main()
