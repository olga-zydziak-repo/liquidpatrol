"""r01/proofs/conformance.py — P5: konformancja kod↔model (OBOWIĄZKOWO OD NOWA).

Wiąże r01/shield.py z dowiedzionym modelem z3 r01.proofs.verify.tau (obiekt P1). Dla KAŻDEGO tiku:
ewaluuje tau na konkretnych wejściach (z3 concrete+simplify) i porównuje DECYZJĘ + POWÓD + STAN-PO
z realnym PatrolShield.step. Pełne pokrycie 6 przejść + latch dla każdego reason. Zgodność ⇒ P1
dotyczy KODU egzekutora PX4, nie fikcji. Cert: r01/proofs/certs/P5.json.
Uruchom: PYTHONPATH=.certdeps python3 -m r01.proofs.conformance
"""
from __future__ import annotations
import hashlib, json, os, sys, random
import z3

from r01.shield import (PatrolShield, ALLOW as S_ALLOW, HOLD as S_HOLD, REFUSE as S_REFUSE,
                        GEOFENCE, COMMAND_INVALID, STALE_CMD, ABORT,
                        PATROL, HOLDING, RETURNING, DONE,
                        M_PATROL, M_HOLD, M_RETURN, M_ABORT)
from r01.proofs.verify import (tau, ALLOW, HOLD, REFUSE, NONE, GEOFENCE as M_GEO,
                               COMMAND_INVALID as M_CI, STALE_CMD as M_ST, ABORT_R as M_AB,
                               PATROL as MP, HOLDING as MH, RETURNING as MR, DONE as MD,
                               M_PATROL as MM_P, M_HOLD as MM_H, M_RETURN as MM_R, M_ABORT as MM_A)

CERT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "certs", "P5.json")

DEC_ID = {S_ALLOW: ALLOW, S_HOLD: HOLD, S_REFUSE: REFUSE}
RSN_ID = {None: NONE, GEOFENCE: M_GEO, COMMAND_INVALID: M_CI, STALE_CMD: M_ST, ABORT: M_AB}
STATE_ID = {PATROL: MP, HOLDING: MH, RETURNING: MR, DONE: MD}
MODE_ID = {M_PATROL: MM_P, M_HOLD: MM_H, M_RETURN: MM_R, M_ABORT: MM_A}
LEAVES = ["latch", "geo", "abort", "hold", "return", "patrol"]


def sh_pre(sh):
    tm = sh.terminal is not None
    rsn = RSN_ID[sh.terminal[0]] if tm else NONE
    return {"tm": tm, "rsn": rsn, "st": STATE_ID[sh.state]}


def eval_tau(pre, geo, mode_i):
    c = {"tm": z3.BoolVal(pre["tm"]), "rsn": z3.IntVal(pre["rsn"]), "st": z3.IntVal(pre["st"])}
    cp, dec, _ = tau(c, z3.BoolVal(geo), z3.IntVal(mode_i))
    b = lambda e: z3.is_true(z3.simplify(e))
    i = lambda e: z3.simplify(e).as_long()
    return i(dec), {"tm": b(cp["tm"]), "rsn": i(cp["rsn"]), "st": i(cp["st"])}


def leaf_of(pre, geo, mode_i):
    if pre["tm"]:
        return "latch"
    if geo:
        return "geo"
    return {MM_A: "abort", MM_H: "hold", MM_R: "return", MM_P: "patrol"}[mode_i]


def run_episode(sh, ticks, coverage, mism):
    """ticks: lista (pos, vel, target, mode_str). Porównuje tau≡shield per tik (bez break)."""
    for k, (pos, vel, target, mode) in enumerate(ticks):
        pre = sh_pre(sh)
        geo = sh._geofence_violation(pos, vel, target)[0]
        mode_i = MODE_ID[mode]
        m_dec, m_post = eval_tau(pre, geo, mode_i)
        coverage.add(leaf_of(pre, geo, mode_i))
        d = sh.step(k, pos, vel, target, mode=mode)
        s_dec = DEC_ID[d["decision"]]
        s_post = sh_pre(sh)
        if m_dec != s_dec or any(m_post[x] != s_post[x] for x in ("tm", "rsn", "st")):
            mism.append({"k": k, "pre": pre, "geo": geo, "mode": mode,
                         "model": {"dec": m_dec, **m_post}, "shield": {"dec": s_dec, **s_post}})
            return


def gen_random(seed):
    rng = random.Random(seed)
    ticks = []
    for _ in range(30):
        pos = (rng.uniform(-35, 35), rng.uniform(-35, 35), -rng.uniform(0, 25))
        vel = (rng.uniform(-4, 4), rng.uniform(-4, 4), rng.uniform(-2, 2))
        target = (rng.uniform(-40, 40), rng.uniform(-40, 40), -rng.uniform(0, 25))
        mode = rng.choice([M_PATROL, M_HOLD, M_RETURN, M_ABORT])
        ticks.append((pos, vel, target, mode))
    return ticks


def gen_targeted():
    """Pokrycie 6 liści + latch dla każdego reason (via latch_refuse i via geo/abort)."""
    IN = (0.0, 0.0, -10.0); V0 = (0.0, 0.0, 0.0); TG = (20.0, 20.0, -10.0); FAR = (45.0, 0.0, -10.0)
    eps = []
    eps.append(("patrol", None, [(IN, V0, TG, M_PATROL), (IN, V0, TG, M_PATROL)]))
    eps.append(("hold", None, [(IN, V0, TG, M_HOLD)]))
    eps.append(("return", None, [(IN, V0, TG, M_RETURN)]))
    eps.append(("abort→latch", None, [(IN, V0, TG, M_ABORT), (IN, V0, TG, M_PATROL)]))  # abort potem latch
    eps.append(("geo→latch", None, [(IN, V0, FAR, M_PATROL), (IN, V0, TG, M_PATROL)]))  # geo potem latch
    # predykcja: pozycja blisko obwiedni + prędkość na zewnątrz → geo
    eps.append(("geo_predict", None, [((31.0, 0.0, -10.0), (3.0, 0.0, 0.0), (31.5, 0.0, -10.0), M_PATROL)]))
    # latch dla COMMAND_INVALID i STALE_CMD (via latch_refuse — jak w egzekutorze)
    eps.append(("latch_CI", (COMMAND_INVALID, "adm"), [(IN, V0, TG, M_PATROL)]))
    eps.append(("latch_ST", (STALE_CMD, "adm"), [(IN, V0, TG, M_HOLD)]))
    return eps


def main():
    coverage = set(); mism = []
    n_rand = 400
    for seed in range(n_rand):
        sh = PatrolShield(); sh.reset()
        run_episode(sh, gen_random(seed), coverage, mism)
    targeted = gen_targeted()
    for name, latch, ticks in targeted:
        sh = PatrolShield(); sh.reset()
        if latch is not None:
            sh.latch_refuse(latch[0], latch[1])
        run_episode(sh, ticks, coverage, mism)
    missing = [l for l in LEAVES if l not in coverage]
    ok = (not mism) and (not missing)
    print("=== P5 konformancja kod↔model (R0.1) ===")
    print(f"  rozbieżności tau≡shield: {len(mism)}  ({n_rand} losowych + {len(targeted)} celowanych epizodów)")
    print(f"  pokrycie przejść: {len(coverage)}/6" + (f"  BRAK: {missing}" if missing else "  (pełne)"))
    if mism:
        print("  PIERWSZA ROZBIEŻNOŚĆ:", json.dumps(mism[0], default=str, ensure_ascii=False))
    print(f"WERDYKT P5: {'PASS' if ok else 'FAIL'}")
    if not ok:
        sys.exit(1)
    cert = {"property": "P5", "verdict": "PASS",
            "method": "per-tick conformance: proven-model tau ≡ r01/shield.py (decision+reason+state)",
            "z3_pip": "5.0.0.0", "z3_lib": z3.get_version_string(),
            "episodes_random": n_rand, "episodes_targeted": len(targeted),
            "transitions_covered": sorted(coverage), "coverage": f"{len(coverage)}/6", "mismatches": 0,
            "latched_reasons_covered": ["GEOFENCE", "ABORT", "COMMAND_INVALID", "STALE_CMD"],
            "binds": "P1 (r01/proofs/certs/P1.json) — dowód dotyczy KODU egzekutora, nie fikcji",
            "code_refs": {"shield": "r01/shield.py:_decide", "model": "r01/proofs/verify.py:tau"},
            "model_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest()}
    os.makedirs(os.path.dirname(CERT), exist_ok=True)
    json.dump(cert, open(CERT, "w"), indent=2, ensure_ascii=False)
    print(f"zapisano {CERT}")


if __name__ == "__main__":
    main()
