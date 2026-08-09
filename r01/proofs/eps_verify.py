"""r01/proofs/eps_verify.py — P2-ε: forma PLATEAU (R0.3a), twierdzenie zawierania z błędem pozycji.

Twierdzenie WARUNKOWE (A-plateau, [A4], walidowane w bramce D13c):
  (r_est ≤ R_route') ∧ (0 ≤ ε ≤ ε_cap) ∧ (r_true ≤ r_est + ε) ∧ (0 ≤ v ≤ v_max)
    ⇒  r_true + d_stop ≤ R_E        (pozycja PRAWDZIWA + hamowanie nie opuszcza obwiedni)
gdzie  R_route' = R_E − d_stop − ε_cap  (reguła D11),  d_stop = DELTA_MARGIN (react+brake, R0.1).

Dowód: r_true ≤ r_est + ε ≤ R_route' + ε_cap = R_E − d_stop  ⇒  r_true + d_stop ≤ R_E.
Zawieranie NIE zależy od czasu ani kształtu narastania błędu — tylko od OGRANICZENIA ε ≤ ε_cap.
Człon Land pokryty przez cap: skoro r_true ≤ R_E − d_stop przez CAŁY epizod aż do touchdown
(D13c), przyziemienie spełnia r_true ≤ R_E bez osobnego członu t_land·rate (model rate OBALONY B1).

Osobny cert `certs/P2_eps.json`; kanoniczny P2.json NIETKNIĘTY. Stałe wymierne (Fraction).
ε_cap: env EPS_CAP (ułamek, np. '7/4') — ZAMROŻONY po B1-bis (ANEKS-4). Domyślnie robocze 7/4.

Uruchom: EPS_CAP=7/4 PYTHONPATH=.certdeps python3 -m r01.proofs.eps_verify
"""
from __future__ import annotations
import hashlib, json, os, sys
from fractions import Fraction
import z3

from r01.config import R_E as CFG_R_E, DELTA_MARGIN as CFG_DSTOP, V_MAX as CFG_VMAX

_HERE = os.path.dirname(os.path.abspath(__file__))
CERT = os.path.join(_HERE, "certs", "P2_eps.json")


def _fr(x):
    return Fraction(str(x))


# --- stałe wymierne ---------------------------------------------------------
# ε_cap ZAMROŻONE ANEKS-4 = 37/4 (r03/config.py, z max ε_pos episode dwufazowego 6.023).
try:
    from r03.config import EPS_CAP_FR as _CAP_DEFAULT
except Exception:
    _CAP_DEFAULT = "37/4"
EPS_CAP_STR = os.environ.get("EPS_CAP", _CAP_DEFAULT)
EPS_CAP = Fraction(EPS_CAP_STR)
DSTOP   = _fr(CFG_DSTOP)          # d_stop = DELTA_MARGIN (2.85 = 57/20)
RE      = _fr(CFG_R_E)            # 32
VMAXF   = _fr(CFG_VMAX)           # 3
RROUTE_P = RE - DSTOP - EPS_CAP   # R_route' (reguła D11)

REz = z3.RealVal(str(RE)); DSTOPz = z3.RealVal(str(DSTOP)); CAPz = z3.RealVal(str(EPS_CAP))
RRPz = z3.RealVal(str(RROUTE_P)); VMAXz = z3.RealVal(str(VMAXF))
DELTA = z3.RealVal("1/1000")     # δ > 0 dla ostrości dwustronnej


def prove():
    res = {}
    r_est, eps, r_true, v = z3.Reals("r_est eps r_true v")

    # (a) GŁÓWNE: przesłanki ⇒ r_true + d_stop ≤ R_E  (sprawdź NEGACJĘ → unsat)
    pre = z3.And(r_est >= 0, r_est <= RRPz,
                 eps >= 0, eps <= CAPz,
                 r_true >= 0, r_true <= r_est + eps,
                 v >= 0, v <= VMAXz)
    s = z3.Solver(); s.add(pre); s.add(z3.Not(r_true + DSTOPz <= REz))
    res["main_containment"] = str(s.check())        # oczekiwane unsat

    # (b1) OSTROŚĆ CAP: ε = ε_cap + δ przy r_est=R_route', r_true=r_est+ε → naruszenie ISTNIEJE (sat)
    s = z3.Solver()
    s.add(r_est == RRPz, eps == CAPz + DELTA, r_true == r_est + eps)
    s.add(r_true + DSTOPz > REz)
    res["sharp_cap_plus_delta"] = str(s.check())     # oczekiwane sat (kontrprzykład)

    # (b2) OSTROŚĆ GEOMETRIA: r_est = R_route' + δ przy ε=ε_cap → naruszenie ISTNIEJE (sat)
    s = z3.Solver()
    s.add(r_est == RRPz + DELTA, eps == CAPz, r_true == r_est + eps)
    s.add(r_true + DSTOPz > REz)
    res["sharp_route_plus_delta"] = str(s.check())   # oczekiwane sat

    # (b3) DOMKNIĘCIE OSTROŚCI: dokładnie na progu (ε=ε_cap, r_est=R_route') NIE ma naruszenia (unsat)
    s = z3.Solver()
    s.add(r_est == RRPz, eps == CAPz, r_true == r_est + eps)
    s.add(r_true + DSTOPz > REz)
    res["boundary_exact_safe"] = str(s.check())      # oczekiwane unsat (na progu bezpiecznie)

    # (c) LAND: r_true ≤ R_E − d_stop na progu (touchdown pokryty przez cap, bez członu t_land)
    s = z3.Solver()
    s.add(pre); s.add(z3.Not(r_true <= REz - DSTOPz))
    res["land_covered_by_cap"] = str(s.check())      # oczekiwane unsat

    return res


def _self_sha():
    return hashlib.sha256(open(__file__, "rb").read()).hexdigest()


EXPECT = {
    "main_containment": "unsat",
    "sharp_cap_plus_delta": "sat",
    "sharp_route_plus_delta": "sat",
    "boundary_exact_safe": "unsat",
    "land_covered_by_cap": "unsat",
}


def main():
    res = prove()
    ok = all(res[k] == EXPECT[k] for k in EXPECT)
    print("=== P2-ε dowód (z3, forma plateau) ===")
    print(f"  ε_cap={EPS_CAP} d_stop={DSTOP} R_E={RE} → R_route'={RROUTE_P} ({float(RROUTE_P):.3f}); "
          f"half-side'={float(RROUTE_P)/(2**0.5):.3f}")
    for k in EXPECT:
        mark = "✓" if res[k] == EXPECT[k] else f"!! (oczek. {EXPECT[k]})"
        print(f"  {k}: {res[k]}  {mark}")
    verdict = "PROVED" if ok else "UNPROVEN"
    print(f"WERDYKT P2-ε: {verdict}")
    if not ok:
        sys.exit(1)
    cert = {
        "property": "P2-eps", "verdict": "PROVED",
        "method": "z3 NRA — twierdzenie warunkowe plateau + ostrość dwustronna",
        "z3_lib": z3.get_version_string(), "obligations": res,
        "theorem": "(r_est≤R_route') ∧ (0≤ε≤ε_cap) ∧ (r_true≤r_est+ε) ⇒ r_true+d_stop≤R_E",
        "rule_D11": "R_route' = R_E − d_stop − ε_cap",
        "constants_rational": {
            "eps_cap": str(EPS_CAP), "d_stop": str(DSTOP), "R_E": str(RE),
            "R_route_prime": str(RROUTE_P), "v_max": str(VMAXF),
        },
        "R_route_prime_float": float(RROUTE_P),
        "half_side_prime_float": float(RROUTE_P) / (2 ** 0.5),
        "sharpness": "kontrprzykład przy ε_cap+δ ORAZ R_route'+δ (sat); próg dokładny bezpieczny (unsat)",
        "land_note": "człon t_land·rate USUNIĘTY (model rate OBALONY B1); Land pokryty przez ε_cap "
                     "obowiązujący do touchdown (D13c) — r_true ≤ R_E−d_stop przez cały epizod",
        "assumptions": [
            "A-plateau [A4]: ε_pos ≤ ε_cap przez cały epizod DR→Land (walidowane w bramce D13c)",
            "ε_cap z reguły D10 (1.5×max(max_drift) B1∪B1-bis, zaokrągl. w górę do ćwiartki), ZAMROŻONE ANEKS-4",
            "r_true ≤ r_est + ε_pos (nierówność trójkąta radialna, worst-case oś)",
            "d_stop = DELTA_MARGIN = v_max·t_react + v_max²/2a_brake (R0.1, frozen)",
            "koperta R_E NIETYKANA (D11: kurczymy trasę R_route', nie rozciągamy świata)",
        ],
        "canonical_P2_untouched": True,
        "code_refs": {"config": "r01/config.py (R_E, DELTA_MARGIN, V_MAX)",
                      "route_r03": "r03/config.py (R_route', half-side' — D11)"},
        "model_sha256": _self_sha(),
    }
    os.makedirs(os.path.dirname(CERT), exist_ok=True)
    if os.path.exists(CERT):
        old = json.load(open(CERT))
        print(f"cert istnieje — zgodność sha: {'TAK' if old.get('model_sha256')==cert['model_sha256'] else 'NIE'}")
    json.dump(cert, open(CERT, "w"), indent=2, ensure_ascii=False)
    print(f"zapisano {CERT} (sha={cert['model_sha256'][:16]}…)")


if __name__ == "__main__":
    main()
