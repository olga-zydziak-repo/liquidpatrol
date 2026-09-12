"""r01/proofs/geo_cont_verify.py — O3 (zawieranie geofence↔P2), ewentualny cert P8_geo_cont.

Noga FV, PRE_FV §3/O3 + decyzja F3. Twierdzenie ZAWIERANIA (d2) na LUSTRZE geofence
(fv_mirror.geofence_violation ≡ produkcja r01/shield.py:101-112; różnicówka tests_fv_diff.py + M-krok
tests_fv_mutants.py: 0 rozbieżności, 27/27 mutantów wykrytych). NIEBRAMKUJĄCE (PRE_FV §5).

=== PREREJESTRACJA (CO3, PRZED pierwszym biegiem solvera) — obligacje i domena WYPISANE ===

Predykat (1:1 lustro): geofence_violation(pos,vel,target) = True gdy KTÓRYKOLWIEK:
  (1) tr > r_e                         tr = hypot(target_x,target_y)                 [shield.py:104-105]
  (2) pr + braking > r_e               pr = hypot(pos_x,pos_y);                       [shield.py:107-108]
                                       braking = min(hypot(vx,vy), v_max)² / (2·a_brake)  [_braking_dist :97-99]
  (3) |target_z| > v_e  OR  |pos_z| > v_e                                             [shield.py:110-111]
¬violation ⟺ (tr ≤ r_e) ∧ (pr + braking ≤ r_e) ∧ (|target_z| ≤ v_e ∧ |pos_z| ≤ v_e).

Inv_P2 (cel twierdzenia) — stałe WYMIERNE wczytane z P2.json (nie przepisane ręcznie):
  bariera:  pr + vn²/(2·a_brake) ≤ R_E     gdzie vn = hypot(vx,vy)  (pełna norma pozioma).
  (to jest ANTECEDENT twierdzenia P2.json "Inv(p,v)=0≤v≤v_max ∧ p+v²/(2a)≤R_E ⇒ p≤R_E";
   człon 0≤v≤v_max jest częścią domeny D poniżej.)

Domena D (PRE_FV §3/O3; F3 — clamp kodu, granice z config `plik:linia`):
  - |v| ≤ v_max:            vn ≤ v_max          [clamp MPC_XY_VEL_MAX; V_MAX r01/config.py:24]
  - pozycje w kopercie:     pr ≤ R_env          [R_env = GF_MAX_HOR_DIST=37, r01/config.py:35 —
                                                 fizyczna obwiednia osiągalna przed natywnym GF]
  - pion w [-V_E, V_E]:     -v_e ≤ pos_z ≤ v_e, -v_e ≤ target_z ≤ v_e   [V_E=20, r01/config.py:31]

UWAGA SEMANTYCZNA (F3 — „norma pełna vs po klampie", wymóg jednej linii z kodu):
  produkcyjny `_braking_dist` liczy vh = min(hypot(vx,vy), v_max) (shield.py:98). Na domenie D
  (vn ≤ v_max) klamp jest NIEAKTYWNY ⇒ vh = vn ⇒ braking = vn²/(2·a_brake) = człon bariery Inv_P2.
  Klamp `min(·,v_max)` odwzorowany 1:1 w z3 przez z3.If(vn ≤ v_max, vn, v_max) — NIE upraszczam ręcznie;
  równość vh=vn wynika z ograniczenia domeny, którą solver ma w założeniach.

Obligacje (sformułowania grafowe/logiczne WYPISANE tu przed biegiem):
  G1  (bramkowa, oczek. unsat): ∀ (pos,vel,target) ∈ D: ¬violation ⇒ Inv_P2.
                                z3: negacja  D ∧ ¬violation ∧ ¬(bariera)  = unsat.
  G2  (informacyjna, oczek. unsat): to samo przy v_max=31/10 (stałe P2_vmax3p1.json) — klamp i Inv
                                oba na 3.1 (kontrfaktyk spójności z P2_vmax3p1: MPC_XY_VEL_MAX=3.1).
  G3  (kontrola niepustości, oczek. sat): ∃ (pos,vel,target) ∈ D: ¬violation (domena nie pusta/trywialna).

Kontrprzykład MODELOWY (G1/G2 sat) ⇒ ZERO łatania domeny/zdań (S3-B): pełny punkt do raportu +
przepuszczenie przez PRODUKCYJNY `_geofence_violation` i Inv_P2 numerycznie (artefakt NRA vs własność
kodu) + sekcja STOP. Potwierdzony na produkcji przy wejściu osiągalnym ⇒ TRIPWIRE (PRE_FV §5, S3-C).

=== LEMATY O4 (L2 — kompozycja; prerejestracja przed dowodzeniem, PRE_FV §3/O4 + F6) ===
  L1: |y_net| ≤ v_max architektonicznie. Głowa sieci y = tanh(·)·V_MAX (net/models.py:12 CfC, :57 MLP);
      |tanh| ≤ 1 ⇒ |y| ≤ V_MAX. (dowód jednozdaniowy, RAPORT_FV §O4, bez certu.)
  L2: clip_v(v, vmax) (r03/controllers/common.py:10-16) zwraca v gdy |v|≤vmax, inaczej v·(vmax/|v|)
      o normie dokładnie vmax ⇒ |clip_v(v,vmax)| ≤ vmax dla dowolnego v (bezwarunkowo, nawet gdyby L1
      zawiodło). Kompozycja: |v_cmd| ≤ v_max (L2) ∧ ¬violation ⇒ (przez O3 G1, jeśli PROVED)
      pr + v_cmd²/(2a) ≤ R_E = antecedent P2 ⇒ (P2.json) pr ≤ R_E. Założenie jawne: lustro≡produkcja
      dla predykatu (różnicówka S1 + M-krok). Zero twierdzeń o locie — wyłącznie o kodzie i modelu.

Uruchom: PYTHONPATH=.certdeps python3 -m r01.proofs.geo_cont_verify
Bez bootów/GPU/instalacji. z3 z .certdeps. Budżet solvera O3c: ≤ 60 min łącznie (te NRA = ms).
"""
from __future__ import annotations
import hashlib
import json
import os
import sys
import time
from fractions import Fraction

import z3

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(_HERE))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

CERTS = os.path.join(_HERE, "certs")
CERT = os.path.join(CERTS, "P8_geo_cont.json")


def _self_sha() -> str:
    return hashlib.sha256(open(__file__, "rb").read()).hexdigest()


def _q(fr: Fraction):
    return z3.Q(fr.numerator, fr.denominator)


def _inv_constants(cert_name):
    """Inv_P2 stałe WYMIERNE wczytane z certu (nie przepisane ręcznie): v_max, R_E, a_brake."""
    c = json.load(open(os.path.join(CERTS, cert_name)))["constants_rational"]
    return {k: Fraction(c[k]) for k in ("v_max", "R_E", "a_brake")}


def _predicate_constants():
    """Stałe predykatu/domeny z PRODUKCJI config (V5, cytaty). r_e/v_e = shield cfg; R_env = natywny GF."""
    import r01.config as C
    return {
        "r_e": Fraction(str(C.R_E)),                 # r01/config.py:30 (==32)
        "v_e": Fraction(str(C.V_E)),                 # r01/config.py:31 (==20)
        "r_env": Fraction(str(C.GF_MAX_HOR_DIST)),   # r01/config.py:35 (==37)
        "v_max_cfg": Fraction(str(C.V_MAX)),         # r01/config.py:24 (==3.0)
    }


def _build_common(v_max, r_e, a_brake, v_e, r_env):
    """Zwraca (domain_and_pred_constraints, barrier, vn) dla zadanych stałych (z3.Q)."""
    px, py, pz = z3.Reals("px py pz")
    vx, vy = z3.Reals("vx vy")
    tx, ty, tz = z3.Reals("tx ty tz")
    pr, tr, vn = z3.Reals("pr tr vn")

    defs = [
        pr >= 0, pr * pr == px * px + py * py,      # pr = hypot(px,py)
        tr >= 0, tr * tr == tx * tx + ty * ty,      # tr = hypot(tx,ty)
        vn >= 0, vn * vn == vx * vx + vy * vy,      # vn = hypot(vx,vy)
    ]
    vhc = z3.If(vn <= v_max, vn, v_max)             # 1:1 min(hypot,v_max)  shield.py:98
    braking = (vhc * vhc) / (2 * a_brake)

    domain = [
        vn <= v_max,                                 # |v| ≤ v_max  (clamp domain)
        pr <= r_env,                                 # pozycje w kopercie
        pz >= -v_e, pz <= v_e, tz >= -v_e, tz <= v_e,  # pion w [-V_E, V_E]
    ]
    not_viol = [
        tr <= r_e,                                   # ¬(clause 1)
        pr + braking <= r_e,                         # ¬(clause 2)
        z3.And(tz >= -v_e, tz <= v_e, pz >= -v_e, pz <= v_e),  # ¬(clause 3)
    ]
    # barrier (Inv_P2) budowany przez wywołującego: barrier_lhs ≤ R_E (R_E z certu Inv).
    return dict(vars=dict(px=px, py=py, pz=pz, vx=vx, vy=vy, tx=tx, ty=ty, tz=tz,
                          pr=pr, tr=tr, vn=vn),
                defs=defs, domain=domain, not_viol=not_viol,
                barrier_lhs=pr + (vn * vn) / (2 * a_brake))


def _check(assertions, want_model=False, timeout_ms=600000):
    s = z3.Solver()
    s.set("timeout", timeout_ms)
    s.add(assertions)
    t0 = time.monotonic()
    r = s.check()
    dt = time.monotonic() - t0
    status = "unsat" if r == z3.unsat else ("sat" if r == z3.sat else str(r))
    model = None
    if want_model and r == z3.sat:
        m = s.model()
        model = {str(d): str(m[d]) for d in m.decls()}
    return status, dt, model


def prove():
    pc = _predicate_constants()
    r_e = _q(pc["r_e"]); v_e = _q(pc["v_e"]); r_env = _q(pc["r_env"])
    res = {}; times = {}; models = {}

    # --- G1 + G3 : stałe Inv z P2.json ---
    inv1 = _inv_constants("P2.json")
    vmax1 = _q(inv1["v_max"]); RE1 = _q(inv1["R_E"]); ab1 = _q(inv1["a_brake"])
    b1 = _build_common(vmax1, r_e, ab1, v_e, r_env)
    barrier1 = b1["barrier_lhs"] <= RE1
    # G1: negacja  D ∧ ¬viol ∧ ¬bariera
    g1 = b1["defs"] + b1["domain"] + b1["not_viol"] + [z3.Not(barrier1)]
    res["G1_containment"], times["G1_containment"], models["G1_containment"] = _check(g1, want_model=True)
    # G3: D ∧ ¬viol  (niepustość)
    g3 = b1["defs"] + b1["domain"] + b1["not_viol"]
    res["G3_nonempty"], times["G3_nonempty"], models["G3_nonempty"] = _check(g3, want_model=True)

    # --- G2 : stałe Inv z P2_vmax3p1.json (klamp i Inv oba 3.1) ---
    inv2 = _inv_constants("P2_vmax3p1.json")
    vmax2 = _q(inv2["v_max"]); RE2 = _q(inv2["R_E"]); ab2 = _q(inv2["a_brake"])
    b2 = _build_common(vmax2, r_e, ab2, v_e, r_env)
    barrier2 = b2["barrier_lhs"] <= RE2
    g2 = b2["defs"] + b2["domain"] + b2["not_viol"] + [z3.Not(barrier2)]
    res["G2_containment_vmax3p1"], times["G2_containment_vmax3p1"], models["G2_containment_vmax3p1"] = \
        _check(g2, want_model=True)

    return res, times, models, pc, inv1, inv2


EXPECT = {
    "G1_containment": "unsat",
    "G2_containment_vmax3p1": "unsat",
    "G3_nonempty": "sat",
}


def _numeric_recheck(model, inv):
    """Przepuszcza kontrprzykład modelowy przez PRODUKCYJNY _geofence_violation i Inv_P2 numerycznie.
    Rozstrzyga artefakt NRA (wymierność) vs własność kodu ZANIM nazwiemy (PRE_FV §3/O3d)."""
    from r01.shield import PatrolShield
    def g(name, default=0.0):
        return float(Fraction(model.get(name, str(default)).replace(" ", "")))
    pos = (g("px"), g("py"), g("pz")); vel = (g("vx"), g("vy")); tgt = (g("tx"), g("ty"), g("tz"))
    s = PatrolShield(); s.reset()
    viol, detail = s._geofence_violation(pos, vel, tgt)
    import math
    pr = math.hypot(pos[0], pos[1]); vn = math.hypot(vel[0], vel[1])
    barrier_lhs = pr + vn * vn / (2 * float(inv["a_brake"]))
    inv_holds = barrier_lhs <= float(inv["R_E"])
    return {"pos": pos, "vel": vel, "target": tgt, "prod_violation": bool(viol), "detail": detail,
            "barrier_lhs": barrier_lhs, "R_E": float(inv["R_E"]), "inv_P2_holds": inv_holds}


def main():
    res, times, models, pc, inv1, inv2 = prove()
    ok = all(res[k] == EXPECT[k] for k in EXPECT)
    total_solver = sum(times.values())
    print("=== O3 zawieranie geofence↔P2 (z3 NRA, lustro ≡ produkcja) ===")
    print(f"  predykat: r_e={pc['r_e']} v_e={pc['v_e']} R_env={pc['r_env']} v_max_cfg={pc['v_max_cfg']}")
    print(f"  Inv(P2.json): v_max={inv1['v_max']} R_E={inv1['R_E']} a_brake={inv1['a_brake']}")
    print(f"  Inv(P2_vmax3p1): v_max={inv2['v_max']} R_E={inv2['R_E']} a_brake={inv2['a_brake']}")
    for k in EXPECT:
        mark = "✓" if res[k] == EXPECT[k] else f"!! (oczek. {EXPECT[k]})"
        print(f"  {k}: {res[k]}  [{times[k]*1000:.1f} ms]  {mark}")
    print(f"  łączny czas solvera: {total_solver:.3f} s (budżet O3c 60 min)")

    # kontrprzykład modelowy na obligacji bramkowej/informacyjnej?
    cx = None
    for k in ("G1_containment", "G2_containment_vmax3p1"):
        if res[k] == "sat":
            inv = inv1 if k == "G1_containment" else inv2
            cx = {"obligation": k, "z3_model": models[k], "numeric": _numeric_recheck(models[k], inv)}
            print(f"  !! KONTRPRZYKŁAD MODELOWY na {k}:")
            print(f"     z3: {models[k]}")
            print(f"     numeryka produkcji: {cx['numeric']}")

    verdict = "PROVED" if ok else ("REFUTED_MODEL" if cx else "UNDETERMINED")
    print(f"WERDYKT O3 (P8_geo_cont): {verdict}")

    if verdict != "PROVED":
        # NIE zapisuj certu; raport i (przy sat) sekcja STOP/TRIPWIRE decyduje CC.
        sys.exit(0 if verdict == "REFUTED_MODEL" else 1)

    cert = {
        "property": "P8_geo_cont",
        "verdict": "PROVED",
        "gating": False,
        "method": "z3 NRA (zawieranie d2) na lustrze geofence ≡ produkcja "
                  "(shield.py:101-112; różnicówka tests_fv_diff.py + M-krok tests_fv_mutants.py: "
                  "0 rozbieżności, 27/27 mutantów wykrytych)",
        "z3_lib": z3.get_version_string(),
        "obligations": res,
        "solver_ms": {k: round(times[k] * 1000, 1) for k in times},
        "theorem": "∀ (pos,vel,target) ∈ D: ¬_geofence_violation(pos,vel,target) ⇒ "
                   "pr + vn²/(2·a_brake) ≤ R_E  (antecedent Inv_P2 z P2.json), "
                   "gdzie pr=hypot(pos_x,pos_y), vn=hypot(vx,vy).",
        "domain": {
            "abs_v_le_v_max": "vn ≤ v_max (clamp; na D klamp min(·,v_max) nieaktywny ⇒ vh=vn)",
            "positions_in_envelope": f"pr ≤ R_env = {pc['r_env']} (GF_MAX_HOR_DIST, r01/config.py:35)",
            "vertical": f"-V_E ≤ pos_z,target_z ≤ V_E, V_E = {pc['v_e']} (r01/config.py:31)",
        },
        "constants_rational": {
            "predicate": {"r_e": str(pc["r_e"]), "v_e": str(pc["v_e"]),
                          "R_env": str(pc["r_env"]), "v_max_cfg": str(pc["v_max_cfg"])},
            "inv_P2_from_P2.json": {k: str(v) for k, v in inv1.items()},
            "inv_P2_vmax3p1": {k: str(v) for k, v in inv2.items()},
        },
        "semantic_note": "produkcyjny _braking_dist używa min(hypot(vx,vy), v_max) (shield.py:98); "
                         "na domenie D (vn≤v_max) klamp nieaktywny ⇒ braking = vn²/(2·a_brake) = "
                         "człon bariery Inv_P2. Klamp odwzorowany 1:1 z3.If(vn≤v_max, vn, v_max), "
                         "równość vh=vn wynika z ograniczenia domeny (nie z ręcznego uproszczenia).",
        "assumptions": [
            "Lustro ≡ produkcja dla _geofence_violation: fv_mirror.geofence_violation 1:1 z "
            "r01/shield.py:101-112 (+_braking_dist :97-99, _radial :51-52); różnicówka tests_fv_diff.py "
            "(siatka 54 + fuzz 4×10⁵ + fikstura 4221/1791) 0 rozbieżności + M-krok tests_fv_mutants.py 27/27.",
            "Inv_P2 = antecedent twierdzenia P2.json (PROVED); stałe wymierne wczytane z P2.json / "
            "P2_vmax3p1.json (nie przepisane). Konkluzja pr≤R_E przez P2 (nie powtarzana tu).",
            "r_e predykatu (config, r01/config.py:30) = R_E Inv_P2 (P2.json) = 32 — zawieranie zależy od "
            "r_e ≤ R_E (nie jest wektorowo trywialne).",
            "V_env=6.0 (limit środowiska ≠ zadany) POZA zakresem O3 — erratum #2 (ERRATUM_VMAX.md), "
            "PRE_FV §3/O3; predykat NIE pokrywa V_env.",
        ],
        "code_refs": {
            "mirror": "r01/proofs/fv_mirror.py:geofence_violation",
            "production": "r01/shield.py:101-112 (_braking_dist :97-99, _radial :51-52)",
            "inv_source": "r01/proofs/certs/P2.json (theorem, constants_rational)",
            "config": "r01/config.py:24,30,31,35",
        },
        "model_sha256": _self_sha(),
    }
    os.makedirs(CERTS, exist_ok=True)
    if os.path.exists(CERT):
        old = json.load(open(CERT))
        print(f"cert istnieje — zgodność sha: {'TAK' if old.get('model_sha256')==cert['model_sha256'] else 'NIE'}")
    json.dump(cert, open(CERT, "w"), indent=2, ensure_ascii=False)
    print(f"zapisano {CERT} (sha={cert['model_sha256'][:16]}…)")


if __name__ == "__main__":
    main()
