"""r01/proofs/p9_kont_verify.py — certy nogi KONT: P9_kont, P1_kont, P7_kont, P5_kont + lustro nakładki
(PROMPT_KONT_S3 §2, ANEKS_KONT-3 §2, ANEKS_KONT-3b §1; układ plików: ANEKS_KONT-3b §1.6).

Kanoniczne certy P1…P8 i ich provery NIETKNIĘTE. Ten plik jest proverem czterech NOWYCH certów
r01/proofs/certs/{P1,P5,P7,P9}_kont.json; każdy zapisuje model_sha256 = sha256(tego pliku).

=== PREREJESTRACJA OBLIGACJI (przed pierwszym biegiem) ===

Stałe: s2_freeze_bf.json z asercją sha256 (ae19f66c…, ANEKS_KONT-3 §2), wymierne (Fraction); R_E i d_stop
z r01/config.py; R_nom = 27.30 z ANEKS_KONT-3b §1.7 (jedyna liczba spoza nośnika). R(k) = R_E − d_stop −
ε_b(k) − Δ_D5.

P9_kont (z3, arytmetyka liniowa), dla KAŻDEGO koszyka k ∈ {0…21}:
  M_k  (oczek. unsat): przesłanki ∧ ¬(r_c ≤ R_E ∧ r_d ≤ R_E), przesłanki =
       0 ≤ r_est ≤ R(k) ∧ 0 ≤ ε ≤ ε_b(k) ∧ 0 ≤ Δ ≤ Δ_D5 ∧ 0 ≤ s ≤ d_stop ∧ |r_c − r_est| ≤ ε ∧ r_d ≤ r_est + ε + s + Δ
       (r_c = r_true w kontynuacji przy ostatnim ALLOW koszyka k; r_d = r_true w dowolnej chwili zejścia po
       REFUSE: hamowanie od ostatniego ALLOW ≤ d_stop = reakcja + hamowanie R0.1, dryf zejścia ≤ Δ_D5).
  Se_k (oczek. sat): ε = ε_b(k)+δ przy r_est = R(k), s = d_stop, Δ = Δ_D5 ⇒ r_d > R_E istnieje.
  Sr_k (oczek. sat): r_est = R(k)+δ przy ε = ε_b(k).   SΔ_k (oczek. sat): Δ = Δ_D5+δ.
  Arytmetyka (asercje, nie z3): T*: ε_b(k)+Δ_D5 ≤ m_p50 dla k ≤ 21 ∧ ε_b(22)+Δ_D5 > m_p50 (koszyk 22 NIE jest
  kontrprzykładem twierdzenia — reguła PRE §3, ANEKS_KONT-3b §2); R_nom ≤ R(0) (wejście w KONT gwarantowane,
  3b §1.7); R(k) nierosnąca; ⌊a·dt⌋ ≤ 21 dla każdego wieku a < T*/dt ticków; tablica kont_shield ≡ JSON.

P1_kont (z3, 1-indukcja; wzorzec r01/proofs/verify.py): automat nakładki. Stan (tm, rsn, st, ph), ph ∈
  {NOM, KONT, KREF}; wejścia geo, mode, pos_bad, auth_ok, kflag (monitor GNSS w utracie), kviol (t_KONT ≥ T* ∨
  r_est > R(⌊t_KONT⌋)), nom (r_est > R_nom ∧ cel na zewnątrz). Priorytet: latch > R-POS > R-KONT > R-G >
  R-G-NOM > abort > hold > return > {OBSERVE∧auth | R-AUTH} > patrol. Obligacje P1a–P1h (jak kanon, z
  przesłankami KONT), P1i–P1n (KONT, R-G-NOM) + nom_applied (NRA): applied R-G-NOM nie ma składowej na zewnątrz.

P7_kont: wyczerpująca enumeracja grafu monitora GNSS + licznika t_KONT (ticki; stałe produkcji: debounce,
  hyst, T*/dt) na LUSTRZE; stara flaga POS: P7_posmon (kanon) + iloczyn obu monitorów enumerowany w pełni na
  instancji zredukowanej (brak sprzężenia). z3-duplikat kroku (unsat).

P5_kont: konformancja lustro ≡ produkcja (r03/kont_shield.KontShield) i model tau_kont ≡ produkcja na:
  siatce prereg (results/KONT/s3/p5_kont_grid.json, budowana raz komendą `grid`), fuzz ≥ 10⁵ epizodów,
  fiksturze S2 (8 lotów, wejścia zrekonstruowane: ANEKS_KONT-3b §1.5). Kryterium: 0 rozbieżności.

Uruchom: PYTHONPATH=.certdeps python3 -m r01.proofs.p9_kont_verify grid|p9|p1|p7|p5|all
"""
from __future__ import annotations
import bisect
import hashlib
import json
import math
import os
import random
import re
import sys
from collections import deque
from fractions import Fraction

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(_HERE))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from r01.config import R_E as CFG_R_E, DELTA_MARGIN as CFG_DSTOP
from r01.proofs import fv_mirror as FM

CERTS = os.path.join(_HERE, "certs")
FREEZE = os.path.join(ROOT, "results/KONT/s2/s2_freeze_bf.json")
FREEZE_SHA256 = "ae19f66c6807de6c824bf0fd723965258b15b77963eb866afb78d3dd3740ae4a"
GRID = os.path.join(ROOT, "results/KONT/s3/p5_kont_grid.json")
R_NOM_STR = "27.30"                     # ANEKS_KONT-3b §1.7
S2_DIR = os.path.join(ROOT, "results/KONT/s2")


def _self_sha():
    return hashlib.sha256(open(__file__, "rb").read()).hexdigest()


def _fr(x):
    return Fraction(str(x))


def load_freeze():
    raw = open(FREEZE, "rb").read()
    sha = hashlib.sha256(raw).hexdigest()
    assert sha == FREEZE_SHA256, f"sha nośnika zamrożenia {sha} ≠ {FREEZE_SHA256}"
    F = json.loads(raw)
    tstar = int(F["T_star_s"])
    return {
        "json": F, "sha256": sha,
        "eps": [_fr(x) for x in F["eps_b_obwiednia"]],
        "delta": _fr(F["delta_D5"]), "tstar": tstar, "m_p50": _fr(F["m_p50"]),
        "r_e": _fr(CFG_R_E), "d_stop": _fr(CFG_DSTOP), "r_nom": Fraction(R_NOM_STR),
    }


def R_of(c, k):
    return c["r_e"] - c["d_stop"] - c["eps"][k] - c["delta"]


# ================================ P9_kont =====================================
def prove_p9():
    import z3
    c = load_freeze()
    T = c["tstar"]
    rv = lambda q: z3.RealVal(str(q))
    DELTA = z3.RealVal("1/1000")
    RE, DS, DD = rv(c["r_e"]), rv(c["d_stop"]), rv(c["delta"])
    per_k = {}
    for k in range(T):
        Rk, Ek = rv(R_of(c, k)), rv(c["eps"][k])
        r_est, eps, dl, s, rc, rd = z3.Reals("r_est eps dl s rc rd")
        pre = z3.And(r_est >= 0, r_est <= Rk, eps >= 0, eps <= Ek, dl >= 0, dl <= DD, s >= 0, s <= DS,
                     rc - r_est <= eps, r_est - rc <= eps, rd <= r_est + eps + s + dl)
        out = {}
        so = z3.Solver(); so.add(pre); so.add(z3.Not(z3.And(rc <= RE, rd <= RE)))
        out["main"] = str(so.check())
        so = z3.Solver(); so.add(r_est == Rk, eps == Ek + DELTA, s == DS, dl == DD, rd == r_est + eps + s + dl, rd > RE)
        out["sharp_eps"] = str(so.check())
        so = z3.Solver(); so.add(r_est == Rk + DELTA, eps == Ek, s == DS, dl == DD, rd == r_est + eps + s + dl, rd > RE)
        out["sharp_R"] = str(so.check())
        so = z3.Solver(); so.add(r_est == Rk, eps == Ek, s == DS, dl == DD + DELTA, rd == r_est + eps + s + dl, rd > RE)
        out["sharp_delta"] = str(so.check())
        per_k[k] = out
    dt = Fraction(1, 20)
    from r01.config import DT as CFG_DT
    from r03 import kont_shield as KS
    arith = {
        "tstar_rule_k_le_21": all(c["eps"][k] + c["delta"] <= c["m_p50"] for k in range(T)),
        "tstar_rule_k22_breaks": c["eps"][T] + c["delta"] > c["m_p50"],
        "r_nom_le_R0": c["r_nom"] <= R_of(c, 0),
        "R_nonincreasing": all(R_of(c, k + 1) <= R_of(c, k) for k in range(T - 1)),
        "dt_is_1_20": _fr(CFG_DT) == dt,
        "bucket_index_le_21": all(math.floor(a * dt) <= T - 1 for a in range(int(T / dt))),
        "kont_shield_table_eq_json": (list(KS.EPS_B) == [float(x) for x in c["eps"][:T]]
                                      and _fr(KS.DELTA_D5) == c["delta"] and KS.T_STAR_S == T
                                      and Fraction(str(KS.R_NOM)) == c["r_nom"]
                                      and KS.FREEZE_SHA256 == FREEZE_SHA256),
    }
    ok = all(v["main"] == "unsat" and v["sharp_eps"] == "sat" and v["sharp_R"] == "sat"
             and v["sharp_delta"] == "sat" for v in per_k.values()) and all(arith.values())
    numbers = {"R_k": {k: str(R_of(c, k)) for k in range(T)}, "R_0_float": float(R_of(c, 0)),
               "R_21_float": float(R_of(c, T - 1)), "eps22_plus_delta": str(c["eps"][T] + c["delta"])}
    return ok, per_k, arith, numbers, c


# ============================ LUSTRO nakładki =================================
ALLOW, HOLD, REFUSE = "ALLOW", "HOLD", "REFUSE"
PATROL, HOLDING, RETURNING, DONE, OBSERVING, POSDEG, NOAUTH = \
    "PATROL", "HOLDING", "RETURNING", "DONE", "OBSERVING", "POSDEG", "NOAUTH"
GEOFENCE, ABORT, POS_DEGRADED, NO_AUTH = "GEOFENCE", "ABORT", "POS_DEGRADED", "NO_AUTH"
M_PATROL, M_HOLD, M_RETURN, M_ABORT, M_OBSERVE = "PATROL", "HOLD", "RETURN", "ABORT", "OBSERVE"


def mirror_consts():
    """Stałe lustra: progi z produkcji (fv_mirror.shield_thresholds), zamrożenie z JSON (float), R_nom 3b."""
    th = FM.shield_thresholds()
    c = load_freeze()
    T = c["tstar"]
    return {**th, "tstar": T, "R_k": [float(c["r_e"] - c["d_stop"]) - float(c["eps"][k]) - float(c["delta"])
                                      for k in range(T)],
            "eps": [float(x) for x in c["eps"][:T]], "delta": float(c["delta"]),
            "d_stop": float(c["d_stop"]), "r_nom": float(c["r_nom"])}


def new_mirror_state():
    return {"terminal": None, "state": PATROL, "pos": FM.new_pos_state(),
            "g": {"g_bad": 0, "g_healthy": 0, "run_t0": None, "kont": False, "kont_t0": None,
                  "kref": False, "cause": None, "n_enter": 0, "t": None}}


def g_monitor_step(g, lost, now, deb, hyst):
    """Monitor GNSS (stan zreifikowany). lost=None ⇒ bez zmian."""
    if lost is None:
        return g
    if lost:
        if g["g_bad"] == 0:
            g["run_t0"] = now
        g["g_bad"] += 1
        g["g_healthy"] = 0
        if g["g_bad"] >= deb and not g["kont"]:
            g["kont"] = True
            g["kont_t0"] = g["run_t0"]
            g["n_enter"] += 1
    else:
        g["g_bad"] = 0
        if g["kont"]:
            g["g_healthy"] += 1
            if g["g_healthy"] >= hyst:
                g["kont"] = False
                g["kref"] = False
                g["g_healthy"] = 0
                g["kont_t0"] = None
                g["cause"] = None
    return g


def g_barrier_step(g, now, viol_at, tstar):
    """viol_at(t) — czy r_est narusza barierę koszyka ⌊t⌋ (w produkcji: r_est > R(⌊t⌋))."""
    g["t"] = None
    if not g["kont"]:
        return g
    t = now - g["kont_t0"]
    g["t"] = t
    if g["kref"]:
        return g
    if t >= tstar:
        g["kref"], g["cause"] = True, "T*"
    elif viol_at(t):
        g["kref"], g["cause"] = True, "bariera"
    return g


def m_outward(pos, target):
    px, py = float(pos[0]), float(pos[1])
    r = math.hypot(px, py)
    if r == 0.0:
        return 0.0
    return ((float(target[0]) - px) * px + (float(target[1]) - py) * py) / r


def m_strip(vx, vy, pos):
    px, py = float(pos[0]), float(pos[1])
    r = math.hypot(px, py)
    if r == 0.0:
        return vx, vy
    ux, uy = px / r, py / r
    vr = vx * ux + vy * uy
    if vr <= 0.0:
        return vx, vy
    return vx - vr * ux, vy - vr * uy


def mirror_step(st, k, inp, C):
    """Jeden tick nakładki w KONT_MODE=1 na stanie zreifikowanym. inp: pos, vel, target, mode, pos_flag, auth_ok,
    cs_gnss_pos, now, r_est. Zwraca rdzeń decyzji (porównywany z produkcją) + fazę."""
    pos, vel, target = inp["pos"], inp["vel"], inp["target"]
    now = k * C["dt"] if inp.get("now") is None else float(inp["now"])
    r_est = math.hypot(float(pos[0]), float(pos[1])) if inp.get("r_est") is None else float(inp["r_est"])
    g = st["g"]
    cs = inp.get("cs_gnss_pos")
    g_monitor_step(g, None if cs is None else (not cs), now, C["debounce_ticks"], C["hyst_ticks"])
    g_barrier_step(g, now, lambda t: r_est > C["R_k"][int(math.floor(t))], C["tstar"])
    FM.pos_monitor_step(st["pos"], inp.get("pos_flag"), C["debounce_ticks"], C["hyst_ticks"])
    hold = [float(pos[0]), float(pos[1]), float(pos[2])]
    mode, auth_ok = inp.get("mode", M_PATROL), inp.get("auth_ok", True)

    def out(d):
        ph = "KONT_REFUSE" if g["kref"] else ("KONT" if g["kont"] else "NOMINAL")
        return {**d, "phase": ph, "t_kont": g["t"], "cause": g["cause"], "n_enter": g["n_enter"]}

    if st["terminal"] is not None:
        r, rule = st["terminal"]
        return out({"state": DONE, "decision": REFUSE, "reason": r, "rule": rule, "applied": hold})
    if st["pos"]["pos_refuse"]:
        st["state"] = POSDEG
        return out({"state": POSDEG, "decision": REFUSE, "reason": POS_DEGRADED, "rule": "R-POS",
                    "action": "VELOCITY_DESCENT", "applied": hold})
    if g["kref"]:
        st["state"] = POSDEG
        return out({"state": POSDEG, "decision": REFUSE, "reason": POS_DEGRADED, "rule": "R-KONT",
                    "detail": g["cause"], "action": "VELOCITY_DESCENT_YAW_HOLD", "applied": hold})
    viol, detail = FM.geofence_violation(pos, vel, target, C["r_e"], C["v_e"], C["v_max"], C["a_brake"])
    if viol:
        st["terminal"] = (GEOFENCE, "R-G"); st["state"] = DONE
        return out({"state": DONE, "decision": REFUSE, "reason": GEOFENCE, "rule": "R-G", "detail": detail,
                    "applied": hold})
    if r_est > C["r_nom"] and m_outward(pos, target) > 0.0:
        ax, ay = m_strip(float(target[0]) - float(pos[0]), float(target[1]) - float(pos[1]), pos)
        return out({"state": st["state"], "decision": REFUSE, "reason": GEOFENCE, "rule": "R-G-NOM",
                    "detail": f"r_est>R_nom ({r_est:.2f}>{C['r_nom']:.2f}), składowa na zewnątrz odjęta",
                    "applied": [float(pos[0]) + ax, float(pos[1]) + ay, float(target[2])]})
    if mode == M_ABORT:
        st["terminal"] = (ABORT, "R-A"); st["state"] = DONE
        return out({"state": DONE, "decision": REFUSE, "reason": ABORT, "rule": "R-A",
                    "detail": "operator abort", "applied": hold})
    if mode == M_HOLD:
        st["state"] = HOLDING
        return out({"state": HOLDING, "decision": HOLD, "reason": None, "rule": "R-H", "applied": hold})
    if mode == M_RETURN:
        st["state"] = RETURNING
        return out({"state": RETURNING, "decision": HOLD, "reason": None, "rule": "R-R",
                    "detail": "return→RTL(MAVSDK)", "applied": hold})
    tg = [float(target[0]), float(target[1]), float(target[2])]
    if mode == M_OBSERVE:
        if not auth_ok:
            st["state"] = NOAUTH
            return out({"state": NOAUTH, "decision": REFUSE, "reason": NO_AUTH, "rule": "R-AUTH",
                        "detail": "eskalacja OBSERVE bez tokenu operatora", "applied": hold})
        st["state"] = OBSERVING
        return out({"state": OBSERVING, "decision": ALLOW, "reason": None, "rule": "R-O", "applied": tg})
    st["state"] = PATROL
    return out({"state": PATROL, "decision": ALLOW, "reason": None, "rule": "R-P", "applied": tg})


CORE = ("state", "decision", "reason", "rule", "applied", "detail", "action")


def prod_core(d, sh):
    core = {k: d.get(k) for k in CORE}
    t = sh._t_kont
    return {**core, "phase": sh.kont_phase(), "t_kont": t, "cause": sh.kont_cause, "n_enter": sh.n_kont_enter}


def mir_core(m):
    return {**{k: m.get(k) for k in CORE}, "phase": m["phase"], "t_kont": m["t_kont"], "cause": m["cause"],
            "n_enter": m["n_enter"]}


# ================================ P1_kont (z3) ================================
def _p1_model():
    import z3
    from r01.proofs import verify as V
    NOM, KONT, KREF = 0, 1, 2

    def sv(p):
        return {"tm": z3.Bool(p + "tm"), "rsn": z3.Int(p + "rsn"), "st": z3.Int(p + "st"), "ph": z3.Int(p + "ph")}

    def inv(c):
        return z3.And(V.inv(c), c["ph"] >= 0, c["ph"] <= 2)

    def tau(c, geo, mode, pos_bad, auth_ok, kflag, kviol, nom):
        ph2 = z3.If(z3.Not(kflag), NOM, z3.If(z3.Or(c["ph"] == KREF, kviol), KREF, KONT))
        kref = ph2 == KREF
        L_latch = c["tm"]
        base = z3.Not(c["tm"])
        L_pos = z3.And(base, pos_bad)
        a1 = z3.And(base, z3.Not(pos_bad))
        L_kont = z3.And(a1, kref)
        a2 = z3.And(a1, z3.Not(kref))
        L_geo = z3.And(a2, geo)
        a3 = z3.And(a2, z3.Not(geo))
        L_nom = z3.And(a3, nom)
        ok = z3.And(a3, z3.Not(nom))
        L_abort = z3.And(ok, mode == V.M_ABORT)
        L_hold = z3.And(ok, mode == V.M_HOLD)
        L_return = z3.And(ok, mode == V.M_RETURN)
        L_observe = z3.And(ok, mode == V.M_OBSERVE, auth_ok)
        L_auth = z3.And(ok, mode == V.M_OBSERVE, z3.Not(auth_ok))
        L_patrol = z3.And(ok, mode == V.M_PATROL)
        dec = z3.If(z3.Or(L_latch, L_pos, L_kont, L_geo, L_nom, L_abort, L_auth), V.REFUSE,
                    z3.If(z3.Or(L_hold, L_return), V.HOLD, V.ALLOW))
        tm2 = z3.Or(L_latch, L_geo, L_abort)
        rsn2 = z3.If(L_latch, c["rsn"], z3.If(L_geo, V.GEOFENCE, z3.If(L_abort, V.ABORT_R, V.NONE)))
        dec_reason = z3.If(L_latch, c["rsn"], z3.If(z3.Or(L_pos, L_kont), V.POS_DEGRADED_R,
                           z3.If(z3.Or(L_geo, L_nom), V.GEOFENCE, z3.If(L_abort, V.ABORT_R,
                                 z3.If(L_auth, V.NO_AUTH_R, V.NONE)))))
        st2 = z3.If(tm2, V.DONE, z3.If(z3.Or(L_pos, L_kont), V.POSDEG, z3.If(L_nom, c["st"],
                    z3.If(L_auth, V.NOAUTH, z3.If(L_hold, V.HOLDING, z3.If(L_return, V.RETURNING,
                          z3.If(L_observe, V.OBSERVING, V.PATROL)))))))
        cp = {"tm": tm2, "rsn": rsn2, "st": st2, "ph": ph2}
        leaves = {"L_pos": L_pos, "L_kont": L_kont, "L_geo": L_geo, "L_nom": L_nom, "L_observe": L_observe,
                  "L_auth": L_auth, "L_patrol": L_patrol, "L_abort": L_abort, "L_hold": L_hold,
                  "L_return": L_return, "L_latch": L_latch}
        return cp, dec, dec_reason, leaves

    return z3, V, NOM, KONT, KREF, sv, inv, tau


def prove_p1():
    z3, V, NOM, KONT, KREF, sv, inv, tau = _p1_model()
    c = sv("c_")
    geo, pos_bad, auth_ok, kflag, kviol, nom = z3.Bools("geo pos_bad auth_ok kflag kviol nom")
    mode = z3.Int("mode")
    cp, dec, rsn, L = tau(c, geo, mode, pos_bad, auth_ok, kflag, kviol, nom)
    kref2 = cp["ph"] == KREF
    tm = c["tm"]
    P = {
        "P1a": z3.Implies(dec == V.ALLOW, z3.And(z3.Not(geo), z3.Not(pos_bad), z3.Not(tm), z3.Not(kref2), z3.Not(nom))),
        "P1b": z3.And(z3.Implies(geo, dec == V.REFUSE),
                      z3.Implies(z3.And(z3.Not(tm), z3.Not(pos_bad), z3.Not(kref2), geo),
                                 z3.And(rsn == V.GEOFENCE, cp["tm"]))),
        "P1c": z3.Implies(dec == V.REFUSE, z3.Or(rsn == V.GEOFENCE, rsn == V.COMMAND_INVALID, rsn == V.STALE_CMD,
                                                 rsn == V.ABORT_R, rsn == V.POS_DEGRADED_R, rsn == V.NO_AUTH_R)),
        "P1d": z3.Implies(tm, z3.And(cp["tm"], dec == V.REFUSE)),
        "P1e": z3.Implies(L["L_observe"], z3.And(z3.Not(geo), z3.Not(pos_bad), z3.Not(tm), z3.Not(kref2),
                                                 z3.Not(nom), dec == V.ALLOW)),
        "P1f": z3.Implies(z3.And(z3.Not(tm), pos_bad), z3.And(dec == V.REFUSE, rsn == V.POS_DEGRADED_R)),
        "P1g": z3.Implies(L["L_observe"], auth_ok),
        "P1h": z3.Implies(z3.And(z3.Not(tm), z3.Not(pos_bad), z3.Not(kref2), z3.Not(geo), z3.Not(nom),
                                 mode == V.M_OBSERVE, z3.Not(auth_ok)),
                          z3.And(dec == V.REFUSE, rsn == V.NO_AUTH_R, z3.Not(cp["tm"]))),
        # KONT
        "P1i_kont_refuse_pos_reversible": z3.Implies(z3.And(z3.Not(tm), kref2),
                                                     z3.And(dec == V.REFUSE, rsn == V.POS_DEGRADED_R,
                                                            z3.Not(cp["tm"]), cp["st"] == V.POSDEG)),
        "P1j_kref_sticky": z3.Implies(z3.And(c["ph"] == KREF, kflag), kref2),
        "P1k_exit_only_by_monitor": z3.And(z3.Implies(z3.Not(kflag), cp["ph"] == NOM),
                                           z3.Implies(z3.And(c["ph"] == KREF, cp["ph"] != KREF), z3.Not(kflag))),
        "P1l_rgnom_nonlatch_state_kept": z3.Implies(z3.And(z3.Not(tm), z3.Not(pos_bad), z3.Not(kref2),
                                                           z3.Not(geo), nom),
                                                    z3.And(dec == V.REFUSE, rsn == V.GEOFENCE,
                                                           z3.Not(cp["tm"]), cp["st"] == c["st"])),
        "P1m_order_pos_kont_over_geo_over_nom": z3.And(
            z3.Implies(z3.And(z3.Not(tm), pos_bad), z3.Not(cp["tm"])),
            z3.Implies(z3.And(z3.Not(tm), kref2), z3.Not(cp["tm"])),
            z3.Implies(z3.And(z3.Not(tm), z3.Not(pos_bad), z3.Not(kref2), geo), cp["tm"])),
        "P1n_kont_allow_needs_no_violation": z3.Implies(z3.And(dec == V.ALLOW, kflag),
                                                         z3.And(z3.Not(kviol), c["ph"] != KREF)),
    }
    res = {}
    c0 = {"tm": z3.BoolVal(False), "rsn": z3.IntVal(V.NONE), "st": z3.IntVal(V.PATROL), "ph": z3.IntVal(NOM)}
    s = z3.Solver(); s.add(z3.Not(inv(c0))); res["base"] = str(s.check())
    pre = z3.And(inv(c), V.valid(mode))
    for name, goal in [("inv_step", inv(cp)), *P.items()]:
        s = z3.Solver(); s.add(pre); s.add(z3.Not(goal)); res[name] = str(s.check())
    # nom_applied (NRA): applied = t − max(0,u)·p/|p|², u = (t−p)·p ⇒ (applied−p)·p ≤ 0 i składowa styczna zachowana
    px, py, tx, ty = z3.Reals("px py tx ty")
    n2 = px * px + py * py
    u = (tx - px) * px + (ty - py) * py
    ax = (tx - px) - z3.If(u > 0, u, 0) * px / n2
    ay = (ty - py) - z3.If(u > 0, u, 0) * py / n2
    s = z3.Solver(); s.add(n2 > 0); s.add(z3.Not(z3.And(ax * px + ay * py <= 0,
                                                     ax * (-py) + ay * px == (tx - px) * (-py) + (ty - py) * px)))
    res["nom_applied_no_outward_tangent_kept"] = str(s.check())
    return res


# ================================ P7_kont =====================================
def _g_abstract_step(state, lost, bar, deb, hyst, tt):
    """Krok LUSTRA monitora GNSS + bariery na stanie abstrakcyjnym (gb_sat, gh, kont, kref, age_sat), zegar w
    tickach (now całkowite). bar = wejście „r_est > R(⌊t⌋)" (wolne). Zwraca (stan', enter, exit)."""
    gb, gh, kont, kref, age = state
    N = 10 ** 6
    g = {"g_bad": gb, "g_healthy": gh, "run_t0": (N - (gb - 1)) if gb >= 1 else None, "kont": kont,
         "kont_t0": (N - age) if kont else None, "kref": kref, "cause": None, "n_enter": 0, "t": None}
    g_monitor_step(g, lost, N + 1, deb, hyst)
    g_barrier_step(g, N + 1, lambda t: bar, tt)
    age2 = min(N + 1 - g["kont_t0"], tt) if g["kont"] else 0
    s2 = (min(g["g_bad"], deb), g["g_healthy"], g["kont"], g["kref"], age2)
    return s2, (not kont) and g["kont"], kont and not g["kont"]


SIGMA_G = [(True, True), (True, False), (False, True), (False, False)]   # (lost, bar)


def build_g_graph(deb, hyst, tt):
    init = (0, 0, False, False, 0)
    nodes = {init}
    edges = []
    q = deque([init])
    while q:
        s = q.popleft()
        for lost, bar in SIGMA_G:
            d, en, ex = _g_abstract_step(s, lost, bar, deb, hyst, tt)
            edges.append((s, (lost, bar), d, en, ex))
            if d not in nodes:
                nodes.add(d)
                q.append(d)
    return init, nodes, edges


def _dist(edges, src, pred, edge_pred=None):
    adj = {}
    for s, f, d, en, ex in edges:
        adj.setdefault(s, []).append((f, d, en, ex))
    seen = {src}
    q = deque([(src, 0)])
    while q:
        s, n = q.popleft()
        for f, d, en, ex in adj.get(s, []):
            if (edge_pred and edge_pred(s, f, d, en, ex)) or (pred and pred(d)):
                return n + 1
            if d not in seen:
                seen.add(d)
                q.append((d, n + 1))
    return None


def prove_p7():
    th = FM.shield_thresholds()
    c = load_freeze()
    deb, hyst = th["debounce_ticks"], th["hyst_ticks"]
    dt = _fr(th["dt"])
    tt_fr = Fraction(c["tstar"]) / dt
    assert tt_fr.denominator == 1
    tt = int(tt_fr)
    init, nodes, edges = build_g_graph(deb, hyst, tt)
    enter_e = [(s, f, d) for (s, f, d, en, ex) in edges if en]
    exit_e = [(s, f, d) for (s, f, d, en, ex) in edges if ex]
    allow_kont = [n for n in nodes if n[2] and not n[3]]
    res, chk = {}, {}
    chk["a_enter_only_lost_bad_deb_minus_1_age_backdated"] = all(
        f[0] is True and s[0] == deb - 1 and d[4] == deb - 1 for (s, f, d) in enter_e)
    res["a_min_lost_run_to_enter"] = _dist(edges, init, None, lambda s, f, d, en, ex: en)
    chk["a_min_run_eq_deb"] = res["a_min_lost_run_to_enter"] == deb
    chk["b_no_kont_allow_with_age_ge_T"] = all(n[4] < tt for n in allow_kont)
    res["b_max_age_kont_allow_ticks"] = max(n[4] for n in allow_kont)
    edges_from_last = [(s, f, d) for (s, f, d, en, ex) in edges if s[2] and not s[3] and s[4] == tt - 1]
    chk["b_refuse_at_age_T_exactly"] = all((not d[2]) or d[3] for (s, f, d) in edges_from_last) and \
        len(edges_from_last) > 0
    post_enter = (deb, 0, True, False, deb - 1)
    res["b_min_ticks_enter_to_refuse_by_time_no_bar"] = _dist(
        [e for e in edges if not e[1][1]], post_enter, lambda d: d[3])
    chk["b_time_refuse_at_T"] = res["b_min_ticks_enter_to_refuse_by_time_no_bar"] == tt - (deb - 1)
    chk["c_exit_only_healthy_gh_hyst_minus_1_clears_kref"] = all(
        f[0] is False and s[1] == hyst - 1 and not d[3] and not d[2] for (s, f, d) in exit_e)
    res["c_min_healthy_run_to_exit"] = _dist(edges, post_enter, lambda d: not d[2])
    chk["c_min_run_eq_hyst"] = res["c_min_healthy_run_to_exit"] == hyst
    chk["d_kref_sticky_while_kont"] = all(d[3] for (s, f, d, en, ex) in edges if s[3] and d[2])
    res["e_min_reenter_cycle"] = _dist(edges, post_enter, None, lambda s, f, d, en, ex: en)
    chk["e_cycle_eq_hyst_plus_deb"] = res["e_min_reenter_cycle"] == hyst + deb
    bar_ref = {s[4] for (s, f, d, en, ex) in edges if s[2] and not s[3] and f[1] and d[3] and d[2]}
    chk["f_bar_refuse_every_age_lt_T"] = bar_ref == set(range(deb - 1, tt))
    res["graph"] = {"n_states": len(nodes), "n_edges": len(edges), "T_ticks": tt, "debounce": deb, "hyst": hyst}
    # iloczyn z monitorem POS na instancji zredukowanej: brak sprzężenia
    from r01.proofs import posmon_verify as PV
    rd, rh, rt = 2, 3, 6
    gi, gn, ge = build_g_graph(rd, rh, rt)
    pn, pe = PV.build_graph(rd, rh)
    pinit = (0, 0, False)
    prod_nodes = {(pinit, gi)}
    q = deque([(pinit, gi)])
    nprod_e = 0
    while q:
        ps, gs = q.popleft()
        for pf in (True, False):
            pd, _ = PV._step_abstract(ps, pf, rd, rh)
            for lost, bar in SIGMA_G:
                gd = _g_abstract_step(gs, lost, bar, rd, rh, rt)[0]
                nprod_e += 1
                if (pd, gd) not in prod_nodes:
                    prod_nodes.add((pd, gd)); q.append((pd, gd))
    chk["g_product_reduced_eq_cartesian"] = prod_nodes == {(a, b) for a in pn for b in gn}
    res["g_product_reduced"] = {"deb": rd, "hyst": rh, "T_ticks": rt, "n_states": len(prod_nodes),
                                "n_edges": nprod_e, "pos_states": len(pn), "gnss_states": len(gn)}
    z = _p7_z3(deb, hyst, tt)
    return all(chk.values()) and all(v == "unsat" for v in z.values()), res, chk, z


def _p7_z3(deb, hyst, tt):
    import z3
    gb, gh, age = z3.Ints("gb gh age")
    kont, kref, lost, bar = z3.Bools("kont kref lost bar")
    D, H, T = z3.IntVal(deb), z3.IntVal(hyst), z3.IntVal(tt)
    # dziedzina = niezmiennik grafu: poza KONT g_bad < debounce (wejście następuje przy g_bad = debounce);
    # jego indukcyjność sprawdzana niżej (z3_inv_step), osiągalność potwierdza enumeracja
    dom = z3.And(gb >= 0, gb <= D, gh >= 0, gh <= H - 1, age >= 0, age <= T,
                 z3.Implies(z3.Not(kont), z3.And(z3.Not(kref), age == 0, gh == 0, gb <= D - 1)))
    # gałąź lost
    gbL = gb + 1
    enterL = z3.And(z3.Not(kont), gbL >= D)
    kontL = z3.Or(kont, enterL)
    ageL = z3.If(enterL, gb, z3.If(kont, z3.If(age + 1 < T, age + 1, T), 0))   # wejście: wiek = gb = deb−1
    # gałąź healthy
    ghH = gh + 1
    exitH = z3.And(kont, ghH >= H)
    kontH = z3.And(kont, z3.Not(exitH))
    ageH = z3.If(kontH, z3.If(age + 1 < T, age + 1, T), 0)
    kont2 = z3.If(lost, kontL, kontH)
    age2 = z3.If(lost, ageL, ageH)
    krefH = z3.And(kontH, kref)
    kref_pre = z3.If(lost, z3.And(kontL, kref), krefH)
    kref2 = z3.And(kont2, z3.Or(kref_pre, age2 >= T, bar))
    out = {}

    def unsat(f):
        s = z3.Solver(); s.add(dom); s.add(f)
        return "unsat" if s.check() == z3.unsat else "sat"
    out["z3_a_enter_step"] = unsat(z3.And(z3.Not(kont), kont2, z3.Not(z3.And(lost, gb >= D - 1, age2 == D - 1))))
    out["z3_b_allow_age_lt_T"] = unsat(z3.And(kont2, z3.Not(kref2), age2 >= T))
    out["z3_c_exit_step"] = unsat(z3.And(kont, z3.Not(kont2), z3.Not(z3.And(z3.Not(lost), gh >= H - 1))))
    out["z3_d_kref_sticky"] = unsat(z3.And(kont, kref, kont2, z3.Not(kref2)))
    gb2 = z3.If(lost, z3.If(gbL < D, gbL, D), 0)
    gh2 = z3.If(lost, 0, z3.If(kontH, ghH, 0))
    out["z3_inv_step"] = unsat(z3.Not(z3.And(gb2 >= 0, gb2 <= D, gh2 >= 0, gh2 <= H - 1, age2 >= 0, age2 <= T,
                                              z3.Implies(z3.Not(kont2), z3.And(z3.Not(kref2), age2 == 0, gh2 == 0,
                                                                               gb2 <= D - 1)))))
    return out


# ================================ P5_kont =====================================
def _new_prod(C, hyst=None):
    from r03.kont_shield import KontShield
    sh = KontShield(kont_mode=True)
    sh.reset()
    if hyst is not None:
        sh.pos_hyst_ticks = hyst
    return sh


def run_conformance_episode(ticks, C, hyst=None, coverage=None, tau_bind=False, latch=None):
    """Produkcja ≡ lustro (+ opcjonalnie tau_kont ≡ produkcja). Zwraca listę rozbieżności (pierwsza wystarcza)."""
    from r01.proofs.conformance import RSN_ID, STATE_ID, MODE_ID, DEC_ID
    sh = _new_prod(C, hyst)
    Cm = dict(C)
    if hyst is not None:
        Cm["hyst_ticks"] = hyst
    st = new_mirror_state()
    if latch is not None:
        sh.latch_refuse(*latch); st["terminal"] = latch; st["state"] = DONE
    diffs = []
    model = _p1_model() if tau_bind else None
    for k, inp in enumerate(ticks):
        pre_tm = sh.terminal is not None
        pre = {"tm": pre_tm, "rsn": RSN_ID[sh.terminal[0]] if pre_tm else 0, "st": STATE_ID[sh.state],
               "ph": {"NOMINAL": 0, "KONT": 1, "KONT_REFUSE": 2}[sh.kont_phase()]}
        geo = sh._geofence_violation(inp["pos"], inp["vel"], inp["target"])[0]
        d = sh.step(k, inp["pos"], inp["vel"], inp["target"], mode=inp.get("mode", M_PATROL),
                    pos_flag=inp.get("pos_flag"), auth_ok=inp.get("auth_ok", True),
                    cs_gnss_pos=inp.get("cs_gnss_pos"), now=inp.get("now"), r_est=inp.get("r_est"))
        m = mirror_step(st, k, inp, Cm)
        pc, mc = prod_core(d, sh), mir_core(m)
        if pc != mc:
            diffs.append({"k": k, "in": inp, "prod": pc, "mir": mc})
            return diffs
        if coverage is not None:
            coverage.add(d.get("rule"))
            if d.get("rule") == "R-KONT":
                coverage.add("cause:" + str(sh.kont_cause))
            if sh.n_kont_enter >= 2:
                coverage.add("second_episode")
        if tau_bind:
            z3, V, NOM, KONT, KREF, sv, inv, tau = model
            c = {"tm": z3.BoolVal(pre["tm"]), "rsn": z3.IntVal(pre["rsn"]), "st": z3.IntVal(pre["st"]),
                 "ph": z3.IntVal(pre["ph"])}
            t = sh._t_kont
            kviol = bool(sh._kont and t is not None and (t >= C["tstar"] or
                         sh._r_est > C["R_k"][int(math.floor(t))]))
            nom = bool(sh._r_est > C["r_nom"] and m_outward(inp["pos"], inp["target"]) > 0.0)
            cp, dec, rsn, _ = tau(c, z3.BoolVal(geo), z3.IntVal(MODE_ID[inp.get("mode", M_PATROL)]),
                                  z3.BoolVal(bool(sh._pos_refuse)), z3.BoolVal(inp.get("auth_ok", True)),
                                  z3.BoolVal(bool(sh._kont)), z3.BoolVal(kviol), z3.BoolVal(nom))
            ev = lambda e: z3.simplify(e)
            mdec, mrsn = ev(dec).as_long(), ev(rsn).as_long()
            post = {"tm": z3.is_true(ev(cp["tm"])), "st": ev(cp["st"]).as_long(), "ph": ev(cp["ph"]).as_long()}
            s_post = {"tm": sh.terminal is not None, "st": STATE_ID[sh.state],
                      "ph": {"NOMINAL": 0, "KONT": 1, "KONT_REFUSE": 2}[sh.kont_phase()]}
            if mdec != DEC_ID[d["decision"]] or mrsn != RSN_ID[d.get("reason")] or post != s_post:
                diffs.append({"k": k, "in": inp, "tau": {"dec": mdec, "rsn": mrsn, **post},
                              "prod": {"dec": d["decision"], "rsn": d.get("reason"), **s_post}})
                return diffs
    return diffs


def _tick(pos, vel=(0.0, 0.0, 0.0), target=None, **kw):
    return {"pos": list(pos), "vel": list(vel), "target": list(target if target is not None else pos), **kw}


def build_grid(C):
    """Siatka prereg: brzegi debounce/hyst/T*/koszyków/R_nom/R-G-NOM, priorytety, drugi epizod. Czas w `now`."""
    deb, hyst, T, dt = C["debounce_ticks"], C["hyst_ticks"], C["tstar"], C["dt"]
    eps = []
    IN = (5.0, 0.0, -10.0)

    def run(name, seq, hyst_override=None, latch=None):
        eps.append({"name": name, "hyst": hyst_override, "latch": latch, "ticks": seq})

    # debounce 1 tick / dokładnie deb / deb+1
    for n in (deb - 1, deb, deb + 1):
        run(f"g_debounce_{n}", [_tick(IN, cs_gnss_pos=False, now=i * dt) for i in range(n)] +
            [_tick(IN, cs_gnss_pos=True, now=n * dt)])
    # T* brzeg: wiek T−dt (ALLOW), T (REFUSE), T+dt — zegar gruby (krok 1 s) i drobny
    for tend in (T - dt, T, T + dt):
        seq = [_tick(IN, cs_gnss_pos=False, now=0.0), _tick(IN, cs_gnss_pos=False, now=dt)]
        seq += [_tick(IN, cs_gnss_pos=False, now=x) for x in (5.0, 10.0, 21.0, tend)]
        run(f"g_tstar_{tend:.2f}", seq)
    # bariera w koszyku k: r_est tuż pod/nad R(k)
    for k in (0, 1, 9, 10, 21):
        for off in (-0.001, 0.001):
            r = C["R_k"][k] + off
            seq = [_tick((r, 0.0, -10.0), cs_gnss_pos=False, now=0.0)] + \
                  [_tick((r, 0.0, -10.0), cs_gnss_pos=False, now=k + 0.5)]
            run(f"g_bar_k{k}_{'pod' if off < 0 else 'nad'}", seq)
    # histereza: wejście, hyst−1 zdrowych (zostaje), hyst (NOMINAL), drugi epizod
    seq = [_tick(IN, cs_gnss_pos=False, now=i * dt) for i in range(deb)]
    seq += [_tick(IN, cs_gnss_pos=True, now=(deb + i) * dt) for i in range(hyst)]
    seq += [_tick(IN, cs_gnss_pos=False, now=(deb + hyst + i) * dt) for i in range(deb + 1)]
    run("g_hyst_exit_second_episode", seq)
    seq = [_tick(IN, cs_gnss_pos=False, now=i * dt) for i in range(deb)]
    seq += [_tick(IN, cs_gnss_pos=True, now=(deb + i) * dt) for i in range(hyst - 1)]
    seq += [_tick(IN, cs_gnss_pos=False, now=(deb + hyst) * dt)]
    run("g_hyst_minus_1_flicker", seq)
    # REFUSE z KONT, potem powrót GNSS ≥ M ⇒ NOMINAL (odwracalny)
    seq = [_tick(IN, cs_gnss_pos=False, now=x) for x in (0.0, dt, 22.5)]
    seq += [_tick(IN, cs_gnss_pos=True, now=22.5 + (i + 1) * dt) for i in range(hyst)]
    run("g_refuse_then_reversal", seq)
    # R-G-NOM: r_est 27.29 / 27.31 na zewnątrz / do środka / stycznie
    for r in (C["r_nom"] - 0.01, C["r_nom"] + 0.01):
        for tgt, nm in (((r + 1.0, 0.0, -10.0), "out"), ((r - 1.0, 0.0, -10.0), "in"), ((r, 1.0, -10.0), "tan"),
                        ((r + 0.5, 0.5, -10.0), "out_tan")):
            run(f"nom_{r:.2f}_{nm}", [_tick((r, 0.0, -10.0), target=tgt, cs_gnss_pos=True, now=0.0)])
    # priorytety: R-POS nad R-KONT, R-KONT nad R-G, R-G nad R-G-NOM, R-G-NOM nad abort, latch nad wszystkim
    FAR = (45.0, 0.0, -10.0)
    run("prio_pos_over_kont", [_tick(IN, cs_gnss_pos=False, pos_flag=True, now=x) for x in (0.0, dt, 23.0)])
    run("prio_kont_over_geo", [_tick(IN, cs_gnss_pos=False, now=0.0), _tick(IN, cs_gnss_pos=False, now=dt),
                               _tick(IN, target=FAR, cs_gnss_pos=False, now=23.0)])
    run("prio_geo_over_nom", [_tick((27.4, 0.0, -10.0), target=FAR, cs_gnss_pos=True, now=0.0)])
    run("prio_nom_over_abort", [_tick((27.4, 0.0, -10.0), target=(28.0, 0.0, -10.0), mode=M_ABORT,
                                      cs_gnss_pos=True, now=0.0)])
    run("prio_latch_over_kont", [_tick(IN, cs_gnss_pos=False, now=x) for x in (0.0, dt, 23.0)],
        latch=("STALE_CMD", "adm"))
    for md in (M_HOLD, M_RETURN, M_OBSERVE):
        run(f"mode_{md}", [_tick(IN, mode=md, cs_gnss_pos=True, now=0.0)])
    run("no_auth", [_tick(IN, mode=M_OBSERVE, auth_ok=False, cs_gnss_pos=True, now=0.0)])
    run("none_inputs", [_tick(IN, now=0.0), _tick(IN, cs_gnss_pos=None, now=dt)])
    return {"provenance": {"prover": "r01/proofs/p9_kont_verify.py:build_grid", "debounce": deb, "hyst": hyst,
                           "T_star_s": T, "dt": dt, "R_nom": C["r_nom"],
                           "note": "NIETYKALNE po commicie (prereg). Zmiana ⇒ dokument CC."},
            "episodes": eps}


def fuzz_episode(rng, C):
    long_ep = rng.random() < 0.1
    n = rng.randint(120, 320) if long_ep else rng.randint(1, 40)
    p_lost = rng.choice([0.05, 0.3, 0.7, 0.95])
    hyst = None if long_ep else rng.choice([None, 1, 2, 3, 5])
    now = rng.uniform(0.0, 5.0)
    big_steps = rng.random() < 0.5
    lost = rng.random() < p_lost
    ticks = []
    for _ in range(n):
        if rng.random() < 0.15:
            lost = rng.random() < p_lost
        cs = None if rng.random() < 0.03 else (not lost)
        ang = rng.uniform(0, 2 * math.pi)
        r = rng.choice([rng.uniform(0, 40), rng.uniform(22.0, 28.0), C["r_nom"] + rng.uniform(-0.05, 0.05)])
        pos = (r * math.cos(ang), r * math.sin(ang), -rng.uniform(0, 25))
        vel = (rng.uniform(-4, 4), rng.uniform(-4, 4), rng.uniform(-2, 2))
        tgt = (pos[0] + rng.uniform(-3, 3), pos[1] + rng.uniform(-3, 3), -rng.uniform(0, 25))
        mode = rng.choices([M_PATROL, M_HOLD, M_RETURN, M_ABORT, M_OBSERVE], [0.8, 0.05, 0.05, 0.02, 0.08])[0]
        pf = None if rng.random() < 0.3 else (rng.random() < 0.08)
        ticks.append({"pos": pos, "vel": vel, "target": tgt, "mode": mode, "pos_flag": pf,
                      "auth_ok": rng.random() < 0.8, "cs_gnss_pos": cs, "now": now,
                      "r_est": (None if rng.random() < 0.9 else r + rng.uniform(-0.5, 0.5))})
        now += rng.uniform(0.3, 3.0) if big_steps else rng.choice([C["dt"], rng.uniform(0.0, 0.2)])
    return ticks, hyst


# ------------------------ fikstura S2 (rekonstrukcja wejść) --------------------
def _t_lookahead():
    src = open(os.path.join(ROOT, "r03/controllers/net_controller.py")).read()
    m = re.search(r"^T_LOOKAHEAD = ([0-9.]+)", src, re.M)
    return float(m.group(1))


def s2_flights():
    F = json.load(open(FREEZE))
    return list(F["loty_wazne"])


def s2_fixture(flight):
    """Wejścia nakładki zrekonstruowane z trace S2 (ANEKS_KONT-3b §1.5): tick = wiersz `ctl` od episode_start do
    descent_start; pos/vel = ostatni rekord `ekf` (mono ≤ ctl.mono); cel = pos + v_ctl·T_LOOKAHEAD
    (net_controller.py:34); cs_gnss_pos = ostatnia zmiana z ulog_wyciag (ts = czas sim) ≤ ctl.sim; pos_flag = ekf.dr;
    now = ctl.sim (zegar koszyków ε_b, kont_s2_analyze.py:3)."""
    d = os.path.join(S2_DIR, flight)
    ekf, ctl, ev = [], [], {}
    for line in open(os.path.join(d, "trace.jsonl")):
        r = json.loads(line)
        if r["t"] == "ekf":
            ekf.append(r)
        elif r["t"] == "ctl":
            ctl.append(r)
        elif r["t"] == "event":
            ev.setdefault(r["ev"], r)
    ekf.sort(key=lambda r: r["mono"])
    em = [r["mono"] for r in ekf]
    flips = [(r["ts"], bool(r["wartosc"])) for r in (json.loads(l) for l in open(os.path.join(d, "ulog_wyciag.jsonl")))
             if r.get("topic") == "estimator_status_flags" and r.get("pole") == "cs_gnss_pos"]
    flips.sort()
    fts = [f[0] for f in flips]
    TL = _t_lookahead()
    t0, t1 = ev["episode_start"]["mono"], ev["descent_start"]["mono"]
    ticks = []
    for c in ctl:
        if not (t0 <= c["mono"] < t1):
            continue
        i = bisect.bisect_right(em, c["mono"]) - 1
        if i < 0:
            continue
        e = ekf[i]
        j = bisect.bisect_right(fts, c["sim"]) - 1
        cs = flips[j][1] if j >= 0 else None
        pos = (e["x"], e["y"], e["z"])
        v = c["v"]
        ticks.append({"pos": pos, "vel": (e["vx"], e["vy"], e["vz"]),
                      "target": (pos[0] + v[0] * TL, pos[1] + v[1] * TL, pos[2] + v[2] * TL),
                      "mode": M_PATROL, "pos_flag": bool(e["dr"]), "auth_ok": True, "cs_gnss_pos": cs,
                      "now": c["sim"], "r_est": None})
    return ticks, {"t_flag_sim": next((t for t, v in flips if not v and t >= ev["cut"]["sim"] - 0.5), None),
                   "cut_sim": ev["cut"]["sim"], "descent_sim": ev["descent_start"]["sim"]}


def s2_offline_decisions(flight, C):
    """Pole decyzji odtwarzane offline: przebieg nakładki na fiksturze lotu (podsumowanie do raportu)."""
    ticks, meta = s2_fixture(flight)
    sh = _new_prod(C)
    first = {}
    n_gnom = 0
    for k, inp in enumerate(ticks):
        d = sh.step(k, inp["pos"], inp["vel"], inp["target"], mode=M_PATROL, pos_flag=inp["pos_flag"],
                    cs_gnss_pos=inp["cs_gnss_pos"], now=inp["now"])
        ph = sh.kont_phase()
        if d.get("rule") == "R-G-NOM":
            n_gnom += 1
        if ph not in first:
            first[ph] = {"now": inp["now"], "t_kont": sh._t_kont, "r_est": round(sh._r_est, 3),
                         "cause": sh.kont_cause, "rule": d.get("rule")}
    tf = meta["t_flag_sim"]
    out = {"n_ticks": len(ticks), "t_flag_sim": tf, "n_kont_enter": sh.n_kont_enter, "n_R_G_NOM": n_gnom,
           "n_R_POS_dr": sum(1 for x in sh.trace if x.get("rule") == "R-POS")}
    if "KONT" in first:
        out["kont_entry_minus_flag_s"] = round(first["KONT"]["now"] - tf, 3) if tf is not None else None
    if "KONT_REFUSE" in first:
        r = first["KONT_REFUSE"]
        out.update(refuse_t_kont_s=round(r["t_kont"], 3), refuse_cause=r["cause"], refuse_r_est=r["r_est"],
                   refuse_minus_flag_s=round(r["now"] - tf, 3) if tf is not None else None)
    return out


def prove_p5(fuzz_n=100000, tau_random=2000, seed0=0):
    C = mirror_consts()
    grid = json.load(open(GRID))
    cov = set()
    mism = []
    n_ticks = {"grid": 0, "fuzz": 0, "fixture": 0, "tau": 0}
    for e in grid["episodes"]:
        latch = tuple(e["latch"]) if e["latch"] else None
        mism += run_conformance_episode(e["ticks"], C, e["hyst"], cov, tau_bind=True, latch=latch)
        n_ticks["grid"] += len(e["ticks"]); n_ticks["tau"] += len(e["ticks"])
    rng = random.Random(seed0)
    for i in range(fuzz_n):
        ticks, hyst = fuzz_episode(rng, C)
        tb = i < tau_random
        mism += run_conformance_episode(ticks, C, hyst, cov, tau_bind=tb)
        n_ticks["fuzz"] += len(ticks)
        if tb:
            n_ticks["tau"] += len(ticks)
        if len(mism) > 5:
            break
    fx = {}
    for fl in s2_flights():
        ticks, meta = s2_fixture(fl)
        mism += run_conformance_episode(ticks, C, None, cov, tau_bind=False)
        n_ticks["fixture"] += len(ticks)
        fx[fl] = s2_offline_decisions(fl, C)
    need = {"R-POS", "R-KONT", "R-G", "R-G-NOM", "R-A", "R-H", "R-R", "R-O", "R-AUTH", "R-P",
            "cause:T*", "cause:bariera", "second_episode"}
    missing = sorted(need - cov)
    return (not mism and not missing), mism, sorted(x for x in cov if x), missing, n_ticks, fx


# =================================== CLI =====================================
def _write(name, cert):
    p = os.path.join(CERTS, name)
    if os.path.exists(p):
        old = json.load(open(p))
        print(f"  {name} istnieje — zgodność sha: {'TAK' if old.get('model_sha256') == cert['model_sha256'] else 'NIE'}")
    json.dump(cert, open(p, "w"), indent=2, ensure_ascii=False)
    print(f"  zapisano {p}")


def main_p9():
    import z3
    ok, per_k, arith, numbers, c = prove_p9()
    print("=== P9_kont: zawieranie z barierą czasową (z3, per koszyk) ===")
    for k, v in per_k.items():
        print(f"  k={k:2d} R(k)={float(R_of(c, k)):.3f} ε_b={float(c['eps'][k]):.3f}: {v}")
    print(f"  arytmetyka: {arith}")
    print(f"WERDYKT P9_kont: {'PROVED' if ok else 'UNPROVEN'}")
    if not ok:
        sys.exit(1)
    _write("P9_kont.json", {
        "property": "P9_kont", "verdict": "PROVED", "method": "z3 LRA per koszyk k∈{0…T*−1} + ostrość dwustronna",
        "z3_lib": z3.get_version_string(), "obligations": {str(k): v for k, v in per_k.items()},
        "arithmetic": arith, "numbers": numbers,
        "theorem": "∀k≤21: 0≤r_est≤R(k) ∧ 0≤ε≤ε_b(k) ∧ 0≤Δ≤Δ_D5 ∧ 0≤s≤d_stop ∧ |r_c−r_est|≤ε ∧ r_d≤r_est+ε+s+Δ "
                   "⇒ r_c≤R_E ∧ r_d≤R_E; R(k)=R_E−d_stop−ε_b(k)−Δ_D5; ostrość: ε_b(k)+δ, R(k)+δ, Δ_D5+δ łamią (δ=1/1000)",
        "constants": {"freeze": "results/KONT/s2/s2_freeze_bf.json", "freeze_sha256": c["sha256"],
                      "R_E": str(c["r_e"]), "d_stop": str(c["d_stop"]), "delta_D5": str(c["delta"]),
                      "T_star_s": c["tstar"], "m_p50": str(c["m_p50"]), "R_nom": str(c["r_nom"]),
                      "R_nom_source": "ANEKS_KONT-3b §1.7", "eps_b": [str(x) for x in c["eps"][:c["tstar"]]]},
        "assumptions": [
            "A-kont [A4] (ANEKS_KONT-3 §2): ε(t) ≤ ε_b(⌊t_KONT⌋) przez całą KONT i w ticku REFUSE (ciągłość: "
            "ostatni ALLOW koszyka k, REFUSE w następnym ticku); Δ ≤ Δ_D5 od REFUSE do przyziemienia (zejście "
            "D5 + trzymanie yaw); walidowane w S4, przekroczenie = FAIL nogi.",
            "A-flag (ANEKS_KONT-3b §1.3): t_KONT od pierwszego ticka flagi cs_gnss_pos=0; opóźnienie "
            "odcięcie→flaga 0.004–0.016 s (8/8 S2) poza zegarem.",
            "A-react (R0.1): przemieszczenie poziome od ostatniego ALLOW do zatrzymania ≤ d_stop = "
            "V_MAX·T_REACT + V_MAX²/(2·A_BRAKE) (r01/config.py:24-27).",
            "|r_true − r_est| ≤ ε: ε = |pos_EKF − (pos_GT ⊖ T_home)| (PRE_KONT Q2), promień przez nierówność trójkąta.",
            "Twierdzenie nie wymusza T*: bariera R(k) zawiera dla każdego k; T* = 22 s z reguły m_p50 "
            "(asercje tstar_rule_*).",
        ],
        "code_refs": {"bariera": "r03/kont_shield.py:r_kont/_kont_barrier", "prover": "r01/proofs/p9_kont_verify.py"},
        "model_sha256": _self_sha()})


def main_p1():
    import z3
    res = prove_p1()
    ok = all(v == "unsat" for v in res.values())
    print("=== P1_kont: automat nakładki (z3, 1-indukcja) ===")
    for k, v in res.items():
        print(f"  {k}: {v}" + ("  ✓" if v == "unsat" else "  !! (SPODZIEWANO unsat)"))
    print(f"WERDYKT P1_kont: {'PROVED' if ok else 'UNPROVEN'}")
    if not ok:
        sys.exit(1)
    _write("P1_kont.json", {
        "property": "P1_kont", "verdict": "PROVED", "method": "1-induction (z3) + NRA (nom_applied)",
        "z3_lib": z3.get_version_string(), "obligations": res, "leaves": 11,
        "automaton": "r03/kont_shield.py:KontShield._decide (KONT_MODE=1): latch > R-POS > R-KONT > R-G > R-G-NOM > "
                     "abort > hold > return > {OBSERVE∧auth_ok | R-AUTH} > patrol; faza ph ∈ {NOMINAL, KONT, KONT_REFUSE}",
        "properties": {
            "P1a": "ALLOW ⇒ ¬geo ∧ ¬pos_bad ∧ ¬terminal ∧ ph'≠KONT_REFUSE ∧ ¬nom",
            "P1b": "geo ⇒ REFUSE; ¬term ∧ ¬pos ∧ ph'≠KREF ∧ geo ⇒ reason=GEOFENCE ∧ terminal'",
            "P1c": "REFUSE ⇒ reason ∈ {GEOFENCE,COMMAND_INVALID,STALE_CMD,ABORT,POS_DEGRADED,NO_AUTH}",
            "P1d": "terminal monotoniczny", "P1e": "OBSERVE ⇒ ALLOW przy ¬geo ¬pos ¬term ¬kref ¬nom",
            "P1f": "pos_bad ∧ ¬term ⇒ REFUSE(POS_DEGRADED)", "P1g": "OBSERVE-ALLOW ⇒ auth_ok",
            "P1h": "domknięcie R-AUTH (premisy z ¬kref ¬nom)",
            "P1i": "ph'=KONT_REFUSE ∧ ¬term ⇒ REFUSE(POS_DEGRADED) ∧ ¬terminal' ∧ st'=POSDEG (odwracalny jak POS_DEGRADED)",
            "P1j": "KONT_REFUSE zatrzaśnięty, dopóki monitor GNSS w utracie",
            "P1k": "powrót do NOMINAL wyłącznie przez monitor (¬kflag)",
            "P1l": "R-G-NOM: REFUSE(GEOFENCE) bez zatrzasku, stan bez zmian",
            "P1m": "kolejność frozen latch > R-POS > R-G (+ R-KONT w klasie R-POS) — ANEKS_KONT-3b §1.1",
            "P1n": "ALLOW w KONT ⇒ ¬kviol (t_KONT < T* ∧ r_est ≤ R(⌊t_KONT⌋)) ∧ faza ≠ KONT_REFUSE",
            "nom_applied": "applied R-G-NOM: (applied−p)·p ≤ 0, składowa styczna zachowana (NRA)"},
        "assumptions": ["geo/pos_bad/kflag/kviol/nom = predykaty liczone w kodzie; arytmetyka bariery = P9_kont, "
                        "monitory = P7_kont/P7_posmon, zgodność kod↔model = P5_kont.",
                        "Założenia kanonu P1 (A-auth, A-episode, żywotność osłony) bez zmian."],
        "model_sha256": _self_sha()})


def main_p7():
    ok, res, chk, z = prove_p7()
    print("=== P7_kont: graf monitora GNSS + t_KONT (enumeracja) ===")
    for k, v in res.items():
        print(f"  {k}: {v}")
    print(f"  checks: {chk}\n  z3: {z}")
    print(f"WERDYKT P7_kont: {'PROVED' if ok else 'UNPROVEN'}")
    if not ok:
        sys.exit(1)
    _write("P7_kont.json", {
        "property": "P7_kont", "verdict": "PROVED",
        "method": "wyczerpująca enumeracja osiągalnego grafu monitora GNSS + licznika t_KONT (BFS, stałe produkcji) "
                  "na lustrze (g_monitor_step/g_barrier_step ≡ produkcja, P5_kont); iloczyn z monitorem POS "
                  "enumerowany na instancji zredukowanej; z3-duplikat kroku",
        "obligations": res, "checks": chk, "z3_duplicate": z,
        "theorem": "(a) wejście w KONT tylko na fladze utraty po debounce, zegar cofnięty o debounce−1 ticków; "
                   "(b) brak ALLOW w KONT przy wieku ≥ T*/dt, REFUSE dokładnie przy wieku T*/dt (bez naruszenia bariery); "
                   "(c) wyjście do NOMINAL tylko po hyst zdrowych tickach, czyści KONT_REFUSE; "
                   "(d) KONT_REFUSE trwa do wyjścia; (e) min cykl ponownego wejścia = hyst + debounce (drugi epizod); "
                   "(f) REFUSE z bariery osiągalny w każdym wieku < T*",
        "abstraction": "g_bad saturowany do debounce (czytany tylko przez ≥debounce, jak P7_posmon); wiek saturowany "
                       "do T*/dt (czytany tylko przez ≥T* — bariera jest wejściem wolnym `bar`); zegar w tickach "
                       "(now = k·dt). Produkcja liczy t_KONT z `now` zmiennoprzecinkowego: REFUSE przy t_KONT ≥ 22.0 "
                       "z dokładnością ±1 tick (T1).",
        "composition": "monitor POS (P7_posmon, kanon) i monitor GNSS nie dzielą zmiennych ani wejść; osiągalny "
                       "iloczyn = iloczyn kartezjański (sprawdzone pełną enumeracją na instancji zredukowanej).",
        "constants": {"debounce_source": "r01/shield.py:72 (instancja)", "hyst_source": "r01/shield.py:73-74",
                      "T_star_ticks": res["graph"]["T_ticks"]},
        "model_sha256": _self_sha()})


def main_grid():
    if os.path.exists(GRID):
        print(f"siatka istnieje ({GRID}) — prereg nietykalna, nie nadpisuję")
        return
    g = build_grid(mirror_consts())
    os.makedirs(os.path.dirname(GRID), exist_ok=True)
    json.dump(g, open(GRID, "w"), indent=1, ensure_ascii=False)
    print(f"siatka zapisana: {GRID} ({len(g['episodes'])} epizodów)")


def main_p5():
    import z3
    ok, mism, cov, missing, n, fx = prove_p5()
    print("=== P5_kont: konformancja lustro ≡ produkcja, tau_kont ≡ produkcja ===")
    print(f"  ticki: {n}  rozbieżności: {len(mism)}  pokrycie: {cov}  brak: {missing}")
    for fl, v in fx.items():
        print(f"  fikstura {fl}: {v}")
    if mism:
        print("  PIERWSZA ROZBIEŻNOŚĆ:", json.dumps(mism[0], default=str, ensure_ascii=False)[:2000])
    print(f"WERDYKT P5_kont: {'PASS' if ok else 'FAIL'}")
    if not ok:
        sys.exit(1)
    grid_sha = hashlib.sha256(open(GRID, "rb").read()).hexdigest()
    _write("P5_kont.json", {
        "property": "P5_kont", "verdict": "PASS",
        "method": "per-tick konformancja: lustro nakładki (mirror_step) ≡ r03/kont_shield.KontShield (decyzja, powód, "
                  "reguła, stan, applied, detail, faza, t_KONT, przyczyna, licznik epizodów) oraz tau_kont (P1_kont) ≡ "
                  "produkcja (decyzja, powód, stan, terminal, faza)",
        "z3_lib": z3.get_version_string(), "ticks": n, "mismatches": 0, "coverage": cov,
        "grid": {"path": "results/KONT/s3/p5_kont_grid.json", "sha256": grid_sha},
        "fuzz": {"episodes": 100000, "seed": 0, "tau_bound_episodes": 2000},
        "fixture_s2": {"flights": s2_flights(), "reconstruction": "ANEKS_KONT-3b §1.5 (s2_fixture)",
                       "offline_decisions": fx},
        "binds": "P1_kont (tau_kont), P7_kont (lustro monitora)",
        "model_sha256": _self_sha()})


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd == "grid":
        return main_grid()
    for name, fn in (("p9", main_p9), ("p1", main_p1), ("p7", main_p7), ("p5", main_p5)):
        if cmd in (name, "all"):
            fn()


if __name__ == "__main__":
    main()
