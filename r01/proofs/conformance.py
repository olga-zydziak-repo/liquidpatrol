"""r01/proofs/conformance.py — P5: konformancja kod↔model (OBOWIĄZKOWO OD NOWA).

Wiąże r01/shield.py z dowiedzionym modelem z3 r01.proofs.verify.tau (obiekt P1). Dla KAŻDEGO tiku:
ewaluuje tau na konkretnych wejściach (z3 concrete+simplify) i porównuje DECYZJĘ + POWÓD + STAN-PO
z realnym PatrolShield.step. Pełne pokrycie 7 przejść + latch dla każdego reason. Zgodność ⇒ P1
dotyczy KODU egzekutora PX4, nie fikcji. Cert: r01/proofs/certs/P5.json.
Uruchom: PYTHONPATH=.certdeps python3 -m r01.proofs.conformance
"""
from __future__ import annotations
import hashlib, json, os, sys, random
import z3

from r01.shield import (PatrolShield, ALLOW as S_ALLOW, HOLD as S_HOLD, REFUSE as S_REFUSE,
                        GEOFENCE, COMMAND_INVALID, STALE_CMD, ABORT, POS_DEGRADED, NO_AUTH,
                        PATROL, HOLDING, RETURNING, DONE, OBSERVING, POSDEG, NOAUTH,
                        M_PATROL, M_HOLD, M_RETURN, M_ABORT, M_OBSERVE)
from r01.proofs.verify import (tau, ALLOW, HOLD, REFUSE, NONE, GEOFENCE as M_GEO,
                               COMMAND_INVALID as M_CI, STALE_CMD as M_ST, ABORT_R as M_AB,
                               POS_DEGRADED_R as M_POS, NO_AUTH_R as M_AUTH,
                               PATROL as MP, HOLDING as MH, RETURNING as MR, DONE as MD, OBSERVING as MO,
                               POSDEG as M_POSDEG, NOAUTH as M_NOAUTH,
                               M_PATROL as MM_P, M_HOLD as MM_H, M_RETURN as MM_R, M_ABORT as MM_A,
                               M_OBSERVE as MM_O)

CERT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "certs", "P5.json")

DEC_ID = {S_ALLOW: ALLOW, S_HOLD: HOLD, S_REFUSE: REFUSE}
RSN_ID = {None: NONE, GEOFENCE: M_GEO, COMMAND_INVALID: M_CI, STALE_CMD: M_ST, ABORT: M_AB,
          POS_DEGRADED: M_POS, NO_AUTH: M_AUTH}
STATE_ID = {PATROL: MP, HOLDING: MH, RETURNING: MR, DONE: MD, OBSERVING: MO, POSDEG: M_POSDEG,
            NOAUTH: M_NOAUTH}
MODE_ID = {M_PATROL: MM_P, M_HOLD: MM_H, M_RETURN: MM_R, M_ABORT: MM_A, M_OBSERVE: MM_O}
LEAVES = ["latch", "pos", "geo", "abort", "hold", "return", "observe", "no_auth", "patrol"]  # DEMO-B: +no_auth


def sh_pre(sh):
    tm = sh.terminal is not None
    rsn = RSN_ID[sh.terminal[0]] if tm else NONE
    return {"tm": tm, "rsn": rsn, "st": STATE_ID[sh.state]}


def eval_tau(pre, geo, mode_i, pos_bad, auth_ok):
    c = {"tm": z3.BoolVal(pre["tm"]), "rsn": z3.IntVal(pre["rsn"]), "st": z3.IntVal(pre["st"])}
    cp, dec, dec_reason, _ = tau(c, z3.BoolVal(geo), z3.IntVal(mode_i), z3.BoolVal(pos_bad),
                                 z3.BoolVal(auth_ok))
    b = lambda e: z3.is_true(z3.simplify(e))
    i = lambda e: z3.simplify(e).as_long()
    return i(dec), i(dec_reason), {"tm": b(cp["tm"]), "rsn": i(cp["rsn"]), "st": i(cp["st"])}


def leaf_of(pre, geo, mode_i, pos_bad, auth_ok):
    if pre["tm"]:
        return "latch"
    if pos_bad:               # R0.3a: R-POS poniżej latch, ponad R-G
        return "pos"
    if geo:
        return "geo"
    if mode_i == MM_O and not auth_ok:   # DEMO-B: R-AUTH w gałęzi OBSERVE (dominowany przez latch/pos/geo)
        return "no_auth"
    return {MM_A: "abort", MM_H: "hold", MM_R: "return", MM_O: "observe", MM_P: "patrol"}[mode_i]


def run_episode(sh, ticks, coverage, mism):
    """ticks: lista (pos, vel, target, mode_str[, pos_flag[, auth_ok]]). Porównuje tau≡shield per tik.
    pos_bad (wejście tau) = shield._pos_refuse PO _pos_monitor (stan który widział _decide).
    auth_ok (DEMO-B) = 6. element (default True — zgodność wsteczna R0.2/R0.3a bez tokenu)."""
    for k, tick in enumerate(ticks):
        pos, vel, target, mode = tick[0], tick[1], tick[2], tick[3]
        pos_flag = tick[4] if len(tick) > 4 else None
        auth_ok = tick[5] if len(tick) > 5 else True
        pre = sh_pre(sh)      # stan PRZED krokiem (monitor nie zmienia tm/rsn/st)
        geo = sh._geofence_violation(pos, vel, target)[0]
        mode_i = MODE_ID[mode]
        d = sh.step(k, pos, vel, target, mode=mode, pos_flag=pos_flag, auth_ok=auth_ok)
        pos_bad = bool(sh._pos_refuse)     # wartość, którą _decide użył (monitor już zaktualizował)
        m_dec, m_reason, m_post = eval_tau(pre, geo, mode_i, pos_bad, auth_ok)
        coverage.add(leaf_of(pre, geo, mode_i, pos_bad, auth_ok))
        s_dec = DEC_ID[d["decision"]]
        s_reason = RSN_ID[d.get("reason")]         # powód WYEMITOWANY w tym ticku (nie persystentny)
        s_post = sh_pre(sh)
        if (m_dec != s_dec or m_reason != s_reason
                or any(m_post[x] != s_post[x] for x in ("tm", "rsn", "st"))):
            mism.append({"k": k, "pre": pre, "geo": geo, "mode": mode, "pos_bad": pos_bad,
                         "model": {"dec": m_dec, "reason": m_reason, **m_post},
                         "shield": {"dec": s_dec, "reason": s_reason, **s_post}})
            return


def gen_random(seed):
    rng = random.Random(seed)
    ticks = []
    for _ in range(30):
        pos = (rng.uniform(-35, 35), rng.uniform(-35, 35), -rng.uniform(0, 25))
        vel = (rng.uniform(-4, 4), rng.uniform(-4, 4), rng.uniform(-2, 2))
        target = (rng.uniform(-40, 40), rng.uniform(-40, 40), -rng.uniform(0, 25))
        mode = rng.choice([M_PATROL, M_HOLD, M_RETURN, M_ABORT, M_OBSERVE])
        pos_flag = rng.random() < 0.25          # R0.3a: losowa flaga utraty aidingu
        auth_ok = rng.random() < 0.5            # DEMO-B: losowy token (pokrycie L_observe/L_auth)
        ticks.append((pos, vel, target, mode, pos_flag, auth_ok))
    return ticks


def gen_targeted():
    """Pokrycie 7 liści + latch dla każdego reason (via latch_refuse i via geo/abort)."""
    IN = (0.0, 0.0, -10.0); V0 = (0.0, 0.0, 0.0); TG = (20.0, 20.0, -10.0); FAR = (45.0, 0.0, -10.0)
    eps = []
    eps.append(("patrol", None, [(IN, V0, TG, M_PATROL), (IN, V0, TG, M_PATROL)]))
    eps.append(("hold", None, [(IN, V0, TG, M_HOLD)]))
    eps.append(("return", None, [(IN, V0, TG, M_RETURN)]))
    eps.append(("observe", None, [(IN, V0, TG, M_OBSERVE), (IN, V0, TG, M_OBSERVE)]))    # OBSERVE = ALLOW (7. liść)
    # OBSERVE goniący intruza ZA płot: setpoint poza R_E → R-G nadrzędny → REFUSE(GEOFENCE) → latch (G3)
    eps.append(("observe→geo→latch", None, [(IN, V0, FAR, M_OBSERVE), (IN, V0, TG, M_OBSERVE)]))
    eps.append(("abort→latch", None, [(IN, V0, TG, M_ABORT), (IN, V0, TG, M_PATROL)]))  # abort potem latch
    eps.append(("geo→latch", None, [(IN, V0, FAR, M_PATROL), (IN, V0, TG, M_PATROL)]))  # geo potem latch
    # predykcja: pozycja blisko obwiedni + prędkość na zewnątrz → geo
    eps.append(("geo_predict", None, [((31.0, 0.0, -10.0), (3.0, 0.0, 0.0), (31.5, 0.0, -10.0), M_PATROL)]))
    # latch dla COMMAND_INVALID i STALE_CMD (via latch_refuse — jak w egzekutorze)
    eps.append(("latch_CI", (COMMAND_INVALID, "adm"), [(IN, V0, TG, M_PATROL)]))
    eps.append(("latch_ST", (STALE_CMD, "adm"), [(IN, V0, TG, M_HOLD)]))
    # R0.3a — wektory celowane POS_DEGRADED (debounce, histereza, priorytet). pos_flag = 5. element.
    #  debounce 1-tick: NIE tripuje (patrol); 2-tick: tripuje (pos leaf)
    eps.append(("pos_debounce_1t", None, [(IN, V0, TG, M_PATROL, True), (IN, V0, TG, M_PATROL, False)]))
    eps.append(("pos_debounce_2t", None, [(IN, V0, TG, M_PATROL, True), (IN, V0, TG, M_PATROL, True)]))
    #  histereza: trip (2 bad), migotanie (1 healthy < M) wciąż POS, potem M(=2) healthy → re-ALLOW
    eps.append(("pos_hyst", None, [(IN, V0, TG, M_PATROL, True), (IN, V0, TG, M_PATROL, True),
                                    (IN, V0, TG, M_PATROL, False), (IN, V0, TG, M_PATROL, False),
                                    (IN, V0, TG, M_PATROL, False)]))
    #  R-POS ponad R-G: pos tripped + cel poza R_E → POS_DEGRADED (nie GEOFENCE)
    eps.append(("pos_above_geo", None, [(IN, V0, FAR, M_PATROL, True), (IN, V0, FAR, M_PATROL, True)]))
    #  latch ponad R-POS: ABORT (latch) potem pos_flag → wciąż ABORT
    eps.append(("latch_above_pos", None, [(IN, V0, TG, M_ABORT, False),
                                           (IN, V0, TG, M_PATROL, True), (IN, V0, TG, M_PATROL, True)]))
    # DEMO-B — wektory celowane NO_AUTH (R-AUTH). auth_ok = 6. element (pos_flag = 5.).
    #  (i) ¬token ⇒ nigdy OBSERVE: eskalacja bez tokenu → no_auth (REFUSE, ODWRACALNY, nie DONE)
    eps.append(("no_auth", None, [(IN, V0, TG, M_OBSERVE, None, False)]))
    #  (ii) token otwiera WYŁĄCZNIE OBSERVE: no_auth (¬token) → OBSERVE (token) — stan NOAUTH→OBSERVING, nie latch
    eps.append(("no_auth→token→observe", None, [(IN, V0, TG, M_OBSERVE, None, False),
                                                 (IN, V0, TG, M_OBSERVE, None, True)]))
    #  (ii-bis) odwracalność: token→OBSERVE potem cofnięcie (¬token) → z powrotem no_auth (nieterminalny)
    eps.append(("token→observe→revoke", None, [(IN, V0, TG, M_OBSERVE, None, True),
                                                (IN, V0, TG, M_OBSERVE, None, False)]))
    #  (v) R-G dominuje R-AUTH: OBSERVE za płot bez tokenu → GEOFENCE (nie NO_AUTH), latch
    eps.append(("geo_above_auth", None, [(IN, V0, FAR, M_OBSERVE, None, False), (IN, V0, TG, M_OBSERVE, None, False)]))
    #  (v) R-POS dominuje R-AUTH: pos_bad (2t) + OBSERVE bez tokenu → POS_DEGRADED (nie NO_AUTH)
    eps.append(("pos_above_auth", None, [(IN, V0, TG, M_OBSERVE, True, False), (IN, V0, TG, M_OBSERVE, True, False)]))
    #  latch dominuje R-AUTH: ABORT (latch) potem OBSERVE bez tokenu → wciąż ABORT
    eps.append(("latch_above_auth", None, [(IN, V0, TG, M_ABORT, None, False),
                                           (IN, V0, TG, M_OBSERVE, None, False)]))
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
        sh.pos_hyst_ticks = 2       # R0.3a: małe M dla wektorów histerezy (konformancja niezależna od M)
        if latch is not None:
            sh.latch_refuse(latch[0], latch[1])
        run_episode(sh, ticks, coverage, mism)
    missing = [l for l in LEAVES if l not in coverage]
    ok = (not mism) and (not missing)
    print("=== P5 konformancja kod↔model (R0.3a: +R-POS) ===")
    print(f"  rozbieżności tau≡shield: {len(mism)}  ({n_rand} losowych + {len(targeted)} celowanych epizodów)")
    print(f"  pokrycie przejść: {len(coverage)}/{len(LEAVES)}" + (f"  BRAK: {missing}" if missing else "  (pełne)"))
    if mism:
        print("  PIERWSZA ROZBIEŻNOŚĆ:", json.dumps(mism[0], default=str, ensure_ascii=False))
    print(f"WERDYKT P5: {'PASS' if ok else 'FAIL'}")
    if not ok:
        sys.exit(1)
    cert = {"property": "P5", "verdict": "PASS",
            "method": "per-tick conformance: proven-model tau ≡ r01/shield.py (decision+reason+state)",
            "z3_pip": "5.0.0.0", "z3_lib": z3.get_version_string(),
            "episodes_random": n_rand, "episodes_targeted": len(targeted),
            "transitions_covered": sorted(coverage), "coverage": f"{len(coverage)}/{len(LEAVES)}", "mismatches": 0,
            "latched_reasons_covered": ["GEOFENCE", "ABORT", "COMMAND_INVALID", "STALE_CMD"],
            "r03a_note": "8. liść R-POS (POS_DEGRADED, ODWRACALNY) pokryty: debounce 1t/2t, histereza "
                         "(flicker+re-ALLOW), priorytet latch>R-POS>R-G. Konformancja tau≡shield NIEZALEŻNA "
                         "od M (histereza) — tau bierze pos_bad=shield._pos_refuse po _pos_monitor.",
            "demob_note": "9. liść R-AUTH (NO_AUTH, ODWRACALNY) pokryty: (i) ¬token⇒no_auth, (ii) token⇒OBSERVE "
                          "i cofnięcie⇒no_auth (nieterminalny), (v) DOMINACJA R-G i R-POS oraz latch nad R-AUTH "
                          "(wektory krzyżowe geo_above_auth/pos_above_auth/latch_above_auth). auth_ok = wejście "
                          "walidowane w authz (P4); tu weryfikowana WYŁĄCZNIE zgodność gałęzi decyzji tau≡shield.",
            "binds": "P1 (r01/proofs/certs/P1.json) — dowód dotyczy KODU egzekutora, nie fikcji",
            "code_refs": {"shield": "r01/shield.py:_decide", "model": "r01/proofs/verify.py:tau"},
            "model_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest()}
    os.makedirs(os.path.dirname(CERT), exist_ok=True)
    json.dump(cert, open(CERT, "w"), indent=2, ensure_ascii=False)
    print(f"zapisano {CERT}")


if __name__ == "__main__":
    main()
