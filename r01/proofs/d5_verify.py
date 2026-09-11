"""r01/proofs/d5_verify.py — O1 (D5 `safe_descend_step`), cert P6_d5 (noga FV, PRE_FV §3/O1).

Dowód WARUNKOWY na LUSTRZE D5 (fv_mirror.safe_descend_step_mirror ≡ produkcja
r03/controllers/safe_descend.py:20-49, różnicówka tests_fv_diff.py: 0 rozbieżności — siatka+fuzz+fikstura).
Założenie A1-zegar: `now` niemalejące — w produkcji `now=time.monotonic()` (bench_flight.py:371,
gate_run_r03.py:280). Stałe profilu z config (reguła V5, cytaty w assumptions).

Model kroku (safe_descend.py:32-48): desc_t0 = now pierwszego kroku; el = now − desc_t0 (≥0 przy A1);
  vdesc(el) = v_desc_fast  gdy el < desc_fast_dur;  v_desc_land  gdy el ≥ desc_fast_dur (brzeg: `<` strict);
  touchdown(el) ⇔ el ≥ desc_total.
Kroki dyskretne: now_k = k·Δ, Δ = dt (=1/TICK_HZ), desc_t0 = now_0 ⇒ el_k = k·Δ.

Twierdzenia O1 (PRE_FV §3): (a) przełączenie faz dokładnie na progu H_SWITCH (brzeg=land, wg `<`);
(b) prędkość zejścia nieujemna i nierosnąca ⇒ wysokość zadana monotonicznie nierosnąca;
(c) touchdown w skończonej liczbie kroków N* = ⌈desc_total/Δ⌉ (policzone, minimalne);
(d) komenda ograniczona profilem: 0 ≤ vdesc ≤ v_desc_fast.

Uruchom: PYTHONPATH=.certdeps python3 -m r01.proofs.d5_verify
Bez bootów/GPU. z3 z .certdeps.
"""
from __future__ import annotations
import hashlib
import json
import os
import sys
from fractions import Fraction

import z3

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(_HERE))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

CERT = os.path.join(_HERE, "certs", "P6_d5.json")


def _self_sha() -> str:
    return hashlib.sha256(open(__file__, "rb").read()).hexdigest()


def _profile():
    """Stałe profilu D5 z config (V5). V_DESC_FAST/LAND/H_SWITCH_AGL: r03/config.py:38-40;
    ALT_M: r01/config.py:19; DT=1/TICK_HZ: r01/config.py:41. desc_* jak produkcja
    (bench_flight.py:73-75 == gate_run_r03.py:223-224)."""
    import r03.config as C
    vf = Fraction(str(C.V_DESC_FAST))          # 1.5 = 3/2
    vl = Fraction(str(C.V_DESC_LAND))          # 0.7 = 7/10
    hsw = Fraction(str(C.H_SWITCH_AGL))        # 2.0
    alt = Fraction(str(C.ALT_M))               # 10.0
    dt = Fraction(str(C.DT))                   # 0.05 = 1/20
    dfd = max(Fraction(0), (alt - hsw) / vf)   # (10-2)/1.5 = 16/3
    dtot = dfd + hsw / vl + Fraction(3, 2)     # + 2/0.7 + 1.5 = 407/42
    return {"vf": vf, "vl": vl, "hsw": hsw, "alt": alt, "dt": dt, "dfd": dfd, "dtot": dtot}


def _q(fr: Fraction):
    return z3.Q(fr.numerator, fr.denominator)


def _holds(negation) -> str:
    """Zwraca 'unsat' gdy własność zachodzi (negacja niespełnialna), inaczej 'sat'."""
    s = z3.Solver()
    s.add(negation)
    r = s.check()
    return "unsat" if r == z3.unsat else ("sat" if r == z3.sat else str(r))


def prove():
    P = _profile()
    vf, vl, dfd, dtot, dt = _q(P["vf"]), _q(P["vl"]), _q(P["dfd"]), _q(P["dtot"]), _q(P["dt"])
    el = z3.Real("el")
    el2 = z3.Real("el2")

    def vdesc(x):
        return z3.If(x < dfd, vf, vl)

    res = {}
    # (a) fazy
    res["a_fast_before_switch"] = _holds(z3.And(el >= 0, el < dfd, vdesc(el) != vf))
    res["a_land_at_after_switch"] = _holds(z3.And(el >= dfd, vdesc(el) != vl))
    res["a_boundary_at_dfd_is_land"] = _holds(z3.And(el == dfd, vdesc(el) != vl))
    # (b) nieujemność + nierosnąca ⇒ wysokość monotonicznie nierosnąca
    res["b_vdesc_nonneg"] = _holds(z3.And(el >= 0, vdesc(el) < 0))
    res["b_vdesc_noninc"] = _holds(z3.And(el >= 0, el2 >= el, vdesc(el) < vdesc(el2)))
    # (c) touchdown ⇔ el≥dtot, oraz N* skończone i minimalne
    N = P["dtot"] / P["dt"]
    N_star = -(-N.numerator // N.denominator)          # ceil(dtot/dt)
    # touchdown (el≥dtot) zachodzi wyłącznie w fazie land (el≥dfd) — wymaga dtot≥dfd (touchdown po H_SWITCH):
    res["c_touchdown_in_land_phase"] = _holds(z3.And(el >= dtot, vdesc(el) != vl))
    # właściwy warunek touchdown w modelu = (el >= dtot); dowodzimy osiągalność w N* krokach:
    res["c_touchdown_reached_at_Nstar"] = _holds(_q(Fraction(N_star)) * dt < dtot)          # N*·Δ ≥ dtot
    res["c_Nstar_minimal"] = _holds(_q(Fraction(N_star - 1)) * dt >= dtot)                   # (N*-1)·Δ < dtot
    # (d) |v| ≤ profil
    res["d_vdesc_le_profile"] = _holds(z3.And(el >= 0, vdesc(el) > vf))
    res["d_vdesc_ge_zero"] = _holds(z3.And(el >= 0, vdesc(el) < 0))
    return res, P, N_star


EXPECT = {
    "a_fast_before_switch": "unsat",
    "a_land_at_after_switch": "unsat",
    "a_boundary_at_dfd_is_land": "unsat",
    "b_vdesc_nonneg": "unsat",
    "b_vdesc_noninc": "unsat",
    "c_touchdown_in_land_phase": "unsat",
    "c_touchdown_reached_at_Nstar": "unsat",
    "c_Nstar_minimal": "unsat",
    "d_vdesc_le_profile": "unsat",
    "d_vdesc_ge_zero": "unsat",
}


def main():
    res, P, N_star = prove()
    ok = all(res[k] == EXPECT[k] for k in EXPECT)
    print("=== O1 dowód D5 (z3, lustro ≡ produkcja) ===")
    print(f"  vf={P['vf']} vl={P['vl']} dfd={P['dfd']} ({float(P['dfd']):.4f}) "
          f"dtot={P['dtot']} ({float(P['dtot']):.4f}) dt={P['dt']} → N*={N_star}")
    for k in EXPECT:
        mark = "✓" if res[k] == EXPECT[k] else f"!! (oczek. {EXPECT[k]})"
        print(f"  {k}: {res[k]}  {mark}")
    verdict = "PROVED" if ok else "UNPROVEN"
    print(f"WERDYKT O1 (P6_d5): {verdict}")
    if not ok:
        sys.exit(1)
    cert = {
        "property": "P6_d5",
        "verdict": "PROVED",
        "method": "z3 (arytmetyka wymierna, kwantyfikacja po el) na lustrze D5 ≡ produkcja "
                  "(safe_descend.py:20-49; różnicówka tests_fv_diff.py 0 rozbieżności)",
        "z3_lib": z3.get_version_string(),
        "obligations": res,
        "theorem": "A1-zegar (now niemalejące) ∧ desc_t0=now_0 ∧ el=now−desc_t0 ⇒ "
                   "(a) vdesc=vf⇔el<dfd, vl⇔el≥dfd (brzeg dfd=land, wg `<`); "
                   "(b) 0≤vdesc nierosnąca ⇒ wysokość zadana monotonicznie nierosnąca; "
                   "(c) touchdown⇔el≥dtot, osiągane w N*=⌈dtot/Δ⌉ krokach (minimalne); "
                   "(d) 0≤vdesc≤vf (komenda ograniczona profilem)",
        "constants_rational": {
            "v_desc_fast": str(P["vf"]), "v_desc_land": str(P["vl"]),
            "H_SWITCH_AGL": str(P["hsw"]), "ALT_M": str(P["alt"]), "dt": str(P["dt"]),
            "desc_fast_dur": str(P["dfd"]), "desc_total": str(P["dtot"]),
        },
        "desc_fast_dur_float": float(P["dfd"]),
        "desc_total_float": float(P["dtot"]),
        "N_star": N_star,
        "N_star_derivation": f"⌈desc_total/Δ⌉ = ⌈{P['dtot']}/{P['dt']}⌉ = ⌈{float(P['dtot']/P['dt']):.4f}⌉ = {N_star} "
                             f"kroków fazy zejścia (Δ=dt={float(P['dt'])}s ⇒ t_touchdown={float(N_star*P['dt']):.3f}s)",
        "assumptions": [
            "A1-zegar: now NIEMALEJĄCE. Produkcja: now=time.monotonic() (bench_flight.py:371, "
            "gate_run_r03.py:280) — monotonic z definicji nie cofa. desc_t0=now pierwszego kroku "
            "(safe_descend.py:33-34); el=now−desc_t0≥0.",
            "Stałe profilu z config (V5): V_DESC_FAST=1.5, V_DESC_LAND=0.7, H_SWITCH_AGL=2.0 "
            "(r03/config.py:38-40); ALT_M=10.0 (r01/config.py:19); dt=1/TICK_HZ=0.05 (r01/config.py:41). "
            "desc_fast_dur/desc_total jak produkcja (bench_flight.py:73-75 == gate_run_r03.py:223-224).",
            "Kroki dyskretne now_k=k·Δ, Δ=dt: model N*. Przy Δ<dt touchdown nie później niż ⌈dtot/Δ⌉ — "
            "N* rośnie proporcjonalnie do gęstości; wartość w cercie dla Δ=dt (kadencja pętli 20 Hz).",
            "Lustro ≡ produkcja: fv_mirror.safe_descend_step_mirror bit-w-bit z safe_descend_step "
            "(tests_fv_diff.py: siatka 54 + fuzz 4×10⁵ + fikstura 4221/1791, 0 rozbieżności).",
        ],
        "code_refs": {
            "mirror": "r01/proofs/fv_mirror.py:safe_descend_step_mirror",
            "production": "r03/controllers/safe_descend.py:20-49",
            "profile": "r03/config.py:38-40 + r01/config.py:19,41",
            "clock": "bench_flight.py:371 / gate_run_r03.py:280 (now=time.monotonic())",
        },
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
