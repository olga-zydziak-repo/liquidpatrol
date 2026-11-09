"""r01/proofs/p9_nadir_verify.py — certy nogi NADIR: P9_nadir, P1_nadir, P7_nadir, P5_nadir + lustro nakładki
(PROMPT_NADIR_S3 §R, PRE_NADIR §2.4–§3, ANEKS_NADIR-2 §2).

Kanoniczne certy i certy KONT oraz ich provery NIETKNIĘTE (r01/proofs/p9_kont_verify.py importowany READ-ONLY: monitor
GNSS lustra, automat P1, pomocniki). Ten plik jest proverem czterech NOWYCH certów r01/proofs/certs/{P1,P5,P7,P9}_nadir.json;
każdy zapisuje model_sha256 = sha256(tego pliku).

=== PREREJESTRACJA OBLIGACJI (przed pierwszym biegiem) ===

Stałe: s2_freeze_bf.json (ae19f66c, asercja) — ε_b, Δ_D5, m_p50; ANEKS_NADIR-2.md (sha 6587ad67…, potwierdzone przez
Olgę) — ε_fix_freeze per koszyk r_h (0.305/0.293/0.227/0.582) parsowane z tabeli §2 i porównane z r03/nadir_shield.py;
R_E, d_stop z r01/config.py; wszystko wymiernie (Fraction). R(k, j) = R_E − d_stop − ε_fix(j) − ε_b(k) − Δ_D5.

P9_nadir (z3, LRA), dla KAŻDEGO koszyka j ∈ {0…3} i kubełka k ∈ {0…τ*(j)−1}:
  M_kj (oczek. unsat): przesłanki ∧ ¬(r_c ≤ R_E ∧ r_d ≤ R_E), przesłanki =
       0 ≤ r_est ≤ R(k,j) ∧ 0 ≤ ε_f ≤ ε_fix(j) ∧ 0 ≤ ε_d ≤ ε_b(k) ∧ ε = ε_f + ε_d ∧ 0 ≤ Δ ≤ Δ_D5 ∧ 0 ≤ s ≤ d_stop ∧
       |r_c − r_est| ≤ ε ∧ r_d ≤ r_est + ε + s + Δ (A-nadir: błąd pozycji ramy = błąd poprawki + przyrost dryfu EKF od
       poprawki; r_c = r_true przy ostatnim ALLOW, r_d = r_true w zejściu).
  Ostrość (oczek. sat, δ = 1/1000): ε_f = ε_fix(j)+δ; ε_d = ε_b(k)+δ; r_est = R(k,j)+δ; Δ = Δ_D5+δ.
  Arytmetyka (asercje): τ*(j) z reguły PRE §3: ε_fix(j)+ε_b(k)+Δ_D5 ≤ m_p50 dla k < τ*(j) ∧ > m_p50 dla k = τ*(j), równe
  r03/nadir_shield.TAU_STAR_S; R(k,j) nierosnąca w k; ⌊a·dt⌋ ≤ τ*(j)−1 dla wieku a < (τ*(j) − 2·dt)/dt ticków; tablica
  nadir_shield ≡ aneks; R_H_MAX i KOSZ_M zgodne w nadir_shield i harness/nadir_fix; u(0, j) ≤ m komórki c08_s02 (2.99,
  ANEKS_NADIR-2 §2). Opisowo (nie obligacja): R_nom ≤ R(0, j) (dostępność wejścia w utratę bez natychmiastowego REFUSE).

P1_nadir (z3, 1-indukcja): automat nakładki — w NADIR_MODE=1 _decide = KontShield._decide (nietknięty), bariera piły
  w miejscu R-KONT jako predykat kviol; model = p9_kont_verify._p1_model (te same obligacje P1a–P1o + nom_applied)
  + P1p: liście automatu wzajemnie wyłączne i wyczerpujące (wyłączność reguł).

P7_nadir: wyczerpująca enumeracja grafu monitora GNSS + zegara τ (ticki, stałe produkcji: debounce, hyst, progi
  τ*(j)/dt) na LUSTRZE, osobno dla każdego koszyka j (wejście poprawki ∈ {brak, j}); instancja zredukowana z pełnym
  przełączaniem koszyków; z3-duplikat kroku (unsat).

P5_nadir: konformancja lustro ≡ produkcja (r03/nadir_shield.NadirShield, nadir_mode=1) i model tau_kont (P1) ≡ produkcja
  na: siatce prereg (results/NADIR/s3/p5_nadir_grid.json, budowana raz komendą `grid`), fuzz ≥ 10⁵ epizodów, fiksturze
  S2 (4 cięcia: wejścia z rama.jsonl + tk + demo, t_fix/koszyk z obserwacji literą r_h < 8). Passthrough (T0): NadirShield
  nadir_mode=0 ≡ KontShield (kont_mode=1) i ≡ PatrolShield (kont_mode=0) bajtowo (pełny dict decyzji) na siatce i fuzzie.
  Kryterium: 0 rozbieżności, pełne pokrycie reguł i przyczyn.

Uruchom: PYTHONPATH=.certdeps:. python3 -m r01.proofs.p9_nadir_verify grid|p9|p1|p7|p5|all
"""
from __future__ import annotations
import bisect
import copy
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

from r01.proofs import fv_mirror as FM
from r01.proofs import p9_kont_verify as KV                       # READ-ONLY

CERTS = os.path.join(_HERE, "certs")
ANEKS = os.path.join(ROOT, "ANEKS_NADIR-2.md")
ANEKS_SHA256 = "6587ad678d542adfb7cc8ce331921323fcf62fd075fdd686c2d63c59e8904989"
GRID = os.path.join(ROOT, "results/NADIR/s3/p5_nadir_grid.json")
S2 = os.path.join(ROOT, "results/NADIR/s2")
S2_CIECIA = ("c08_s02", "c11_s02_r2", "c05_s01_r2", "c02_s01")
M_C08 = Fraction("2.99")                 # najwęższa komórka (results/KONT_RECON/r4_margin.json), ANEKS_NADIR-2 §2
T_MARGIN_TICKS = KV.T_MARGIN_TICKS
J_N = 4


def _self_sha():
    return hashlib.sha256(open(__file__, "rb").read()).hexdigest()


def load_aneks():
    raw = open(ANEKS, "rb").read()
    sha = hashlib.sha256(raw).hexdigest()
    assert sha == ANEKS_SHA256, f"sha ANEKS_NADIR-2 {sha} ≠ {ANEKS_SHA256}"
    rows = re.findall(r"^\| (\d)–(\d) \| ([0-9.]+) \| \*\*([0-9.]+)\*\* \|$", raw.decode("utf8"), re.M)
    assert [(int(a), int(b)) for a, b, _, _ in rows] == [(0, 2), (2, 4), (4, 6), (6, 8)], rows
    return {"sha256": sha, "eps_fix": [Fraction(r[3]) for r in rows], "max_zmierzony": [Fraction(r[2]) for r in rows]}


def consts():
    c = KV.load_freeze()
    a = load_aneks()
    c["eps_fix"] = a["eps_fix"]
    c["aneks"] = a
    c["tau_star"] = [tau_star_rule(c, j) for j in range(J_N)]
    return c


def tau_star_rule(c, j):
    k = 0
    while c["eps_fix"][j] + c["eps"][k] + c["delta"] <= c["m_p50"]:
        k += 1
    return k


def R_of(c, k, j):
    return c["r_e"] - c["d_stop"] - c["eps_fix"][j] - c["eps"][k] - c["delta"]


# ================================ P9_nadir =====================================
def prove_p9():
    import z3
    from r01.config import DT as CFG_DT
    from r03 import nadir_shield as NS
    from harness import nadir_fix as NFX
    c = consts()
    rv = lambda q: z3.RealVal(str(q))
    D = z3.RealVal("1/1000")
    RE, DS, DD = rv(c["r_e"]), rv(c["d_stop"]), rv(c["delta"])
    per = {}
    for j in range(J_N):
        for k in range(c["tau_star"][j]):
            Rk, Ef, Eb = rv(R_of(c, k, j)), rv(c["eps_fix"][j]), rv(c["eps"][k])
            r_est, ef, ed, eps, dl, s, rc, rd = z3.Reals("r_est ef ed eps dl s rc rd")
            pre = z3.And(r_est >= 0, r_est <= Rk, ef >= 0, ef <= Ef, ed >= 0, ed <= Eb, eps == ef + ed, dl >= 0, dl <= DD,
                         s >= 0, s <= DS, rc - r_est <= eps, r_est - rc <= eps, rd <= r_est + eps + s + dl)
            out = {}
            so = z3.Solver(); so.add(pre); so.add(z3.Not(z3.And(rc <= RE, rd <= RE))); out["main"] = str(so.check())
            for nm, (r0, f0, b0, d0) in {"sharp_eps_fix": (Rk, Ef + D, Eb, DD), "sharp_eps_b": (Rk, Ef, Eb + D, DD),
                                         "sharp_R": (Rk + D, Ef, Eb, DD), "sharp_delta": (Rk, Ef, Eb, DD + D)}.items():
                so = z3.Solver()
                so.add(r_est == r0, ef == f0, ed == b0, eps == ef + ed, s == DS, dl == d0, rd == r_est + eps + s + dl, rd > RE)
                out[nm] = str(so.check())
            per[f"j{j}_k{k}"] = out
    dt = Fraction(1, 20)
    arith = {
        "tau_star_rule_eq_shield": c["tau_star"] == list(NS.TAU_STAR_S),
        "tau_star_rule_breaks_at_tau_star": all(c["eps_fix"][j] + c["eps"][c["tau_star"][j]] + c["delta"] > c["m_p50"]
                                                for j in range(J_N)),
        "R_nonincreasing_in_k": all(R_of(c, k + 1, j) <= R_of(c, k, j) for j in range(J_N)
                                    for k in range(c["tau_star"][j] - 1)),
        "dt_is_1_20": Fraction(str(CFG_DT)) == dt,
        "bucket_index_lt_tau_star": all(math.floor(a * dt) <= c["tau_star"][j] - 1 for j in range(J_N)
                                        for a in range(int((Fraction(c["tau_star"][j]) - T_MARGIN_TICKS * dt) / dt))),
        "shield_eps_fix_eq_aneks": [Fraction(str(x)) for x in NS.EPS_FIX_FREEZE] == c["eps_fix"],
        "shield_aneks_sha_eq": NS.ANEKS_SHA256 == ANEKS_SHA256,
        "eps_fix_eq_1_5_max": all(abs(c["eps_fix"][j] - Fraction(3, 2) * c["aneks"]["max_zmierzony"][j]) <= Fraction(1, 1000)
                                  for j in range(J_N)),
        "shield_eps_b_delta_eq_freeze": (list(NS.EPS_B) == [float(x) for x in c["eps"][:22]]
                                         and Fraction(str(NS.DELTA_D5)) == c["delta"]),
        "r_h_max_8_shield_eq_fix": NS.R_H_MAX == NFX.R_H_MAX == 8.0 and NS.KOSZ_M == NFX.KOSZ_M == 2.0,
        "j_worst_is_max_eps_fix": c["eps_fix"][NS.J_WORST] == max(c["eps_fix"]),
        "u0_le_m_c08_all_j": all(c["eps_fix"][j] + c["eps"][0] + c["delta"] <= M_C08 for j in range(J_N)),
    }
    opis = {"R_nom_le_R0_per_j": {j: bool(c["r_nom"] <= R_of(c, 0, j)) for j in range(J_N)},
            "R0_per_j": {j: float(R_of(c, 0, j)) for j in range(J_N)}, "R_nom": float(c["r_nom"]),
            "u0_per_j": {j: float(c["eps_fix"][j] + c["eps"][0] + c["delta"]) for j in range(J_N)},
            "uwaga": "R_nom > R(0, j): wejście w utratę GNSS przy r_est ∈ (R(0,j), R_nom] ⇒ natychmiastowy REFUSE(bariera) "
                     "— dostępność, nie bezpieczeństwo (zawieranie trzyma twierdzenie główne)."}
    ok = all(v["main"] == "unsat" and all(v[x] == "sat" for x in ("sharp_eps_fix", "sharp_eps_b", "sharp_R", "sharp_delta"))
             for v in per.values()) and all(arith.values())
    return ok, per, arith, opis, c


# ============================ LUSTRO nakładki NADIR ===========================
ALLOW, HOLD, REFUSE = KV.ALLOW, KV.HOLD, KV.REFUSE
M_PATROL, M_HOLD, M_RETURN, M_ABORT, M_OBSERVE = KV.M_PATROL, KV.M_HOLD, KV.M_RETURN, KV.M_ABORT, KV.M_OBSERVE


def mirror_consts():
    th = FM.shield_thresholds()
    c = consts()
    return {**th, "tau_star": c["tau_star"], "thr": [ts - T_MARGIN_TICKS * th["dt"] for ts in c["tau_star"]],
            "R": [[float(R_of(c, k, j)) for k in range(c["tau_star"][j])] for j in range(J_N)],
            "r_nom": float(c["r_nom"]), "j_worst": max(range(J_N), key=lambda j: c["eps_fix"][j])}


def new_mirror_state():
    st = KV.new_mirror_state()
    st["fx"] = {"t_fix": None, "j": None, "tau": None, "jeff": None}
    return st


def nadir_barrier_step(g, fx, now, viol_at, thr, j_worst):
    """Bariera piły na stanie zreifikowanym. viol_at(tau, j) — r_est > R(⌊tau⌋, j); thr[j] — próg τ*(j) − 2·dt."""
    g["t"] = None
    fx["tau"], fx["jeff"] = None, None
    if not g["kont"]:
        return
    g["t"] = now - g["kont_t0"]
    t0, j = (g["kont_t0"], j_worst) if fx["t_fix"] is None else (fx["t_fix"], fx["j"])
    tau = now - t0
    if tau < 0:
        tau = 0.0
    fx["tau"], fx["jeff"] = tau, j
    if g["kref"]:
        return
    if tau >= thr[j]:
        g["kref"], g["cause"] = True, "τ*"
    elif viol_at(tau, j):
        g["kref"], g["cause"] = True, "bariera"


def mirror_step(st, k, inp, C):
    pos, vel, target = inp["pos"], inp["vel"], inp["target"]
    now = k * C["dt"] if inp.get("now") is None else float(inp["now"])
    r_est = math.hypot(float(pos[0]), float(pos[1])) if inp.get("r_est") is None else float(inp["r_est"])
    g, fx = st["g"], st["fx"]
    if inp.get("t_fix") is not None and inp.get("kosz") is not None:
        fx["t_fix"], fx["j"] = float(inp["t_fix"]), int(inp["kosz"])
    cs = inp.get("cs_gnss_pos")
    KV.g_monitor_step(g, None if cs is None else (not cs), now, C["debounce_ticks"], C["hyst_ticks"])
    nadir_barrier_step(g, fx, now, lambda t, j: r_est > C["R"][j][int(math.floor(t))], C["thr"], C["j_worst"])
    FM.pos_monitor_step(st["pos"], inp.get("pos_flag"), C["debounce_ticks"], C["hyst_ticks"])
    hold = [float(pos[0]), float(pos[1]), float(pos[2])]
    mode, auth_ok = inp.get("mode", M_PATROL), inp.get("auth_ok", True)

    def out(d):
        ph = "KONT_REFUSE" if g["kref"] else ("KONT" if g["kont"] else "NOMINAL")
        return {**d, "phase": ph, "t_kont": g["t"], "cause": g["cause"], "n_enter": g["n_enter"], "tau": fx["tau"],
                "j": fx["jeff"]}

    if st["terminal"] is not None:
        r, rule = st["terminal"]
        return out({"state": "DONE", "decision": REFUSE, "reason": r, "rule": rule, "applied": hold})
    if st["pos"]["pos_refuse"]:
        st["state"] = "POSDEG"
        return out({"state": "POSDEG", "decision": REFUSE, "reason": "POS_DEGRADED", "rule": "R-POS",
                    "action": "VELOCITY_DESCENT", "applied": hold})
    if g["kref"]:
        st["state"] = "POSDEG"
        return out({"state": "POSDEG", "decision": REFUSE, "reason": "POS_DEGRADED", "rule": "R-KONT",
                    "detail": g["cause"], "action": "VELOCITY_DESCENT_YAW_HOLD", "applied": hold})
    viol, detail = FM.geofence_violation(pos, vel, target, C["r_e"], C["v_e"], C["v_max"], C["a_brake"])
    if viol:
        st["terminal"] = ("GEOFENCE", "R-G"); st["state"] = "DONE"
        return out({"state": "DONE", "decision": REFUSE, "reason": "GEOFENCE", "rule": "R-G", "detail": detail,
                    "applied": hold})
    if mode == M_ABORT:
        st["terminal"] = ("ABORT", "R-A"); st["state"] = "DONE"
        return out({"state": "DONE", "decision": REFUSE, "reason": "ABORT", "rule": "R-A",
                    "detail": "operator abort", "applied": hold})
    if mode == M_HOLD:
        st["state"] = "HOLDING"
        return out({"state": "HOLDING", "decision": HOLD, "reason": None, "rule": "R-H", "applied": hold})
    if mode == M_RETURN:
        st["state"] = "RETURNING"
        return out({"state": "RETURNING", "decision": HOLD, "reason": None, "rule": "R-R",
                    "detail": "return→RTL(MAVSDK)", "applied": hold})
    if r_est > C["r_nom"] and KV.m_outward(pos, target) > 0.0:
        ax, ay = KV.m_strip(float(target[0]) - float(pos[0]), float(target[1]) - float(pos[1]), pos)
        return out({"state": st["state"], "decision": REFUSE, "reason": "GEOFENCE", "rule": "R-G-NOM",
                    "detail": f"r_est>R_nom ({r_est:.2f}>{C['r_nom']:.2f}), składowa na zewnątrz odjęta",
                    "applied": [float(pos[0]) + ax, float(pos[1]) + ay, float(target[2])]})
    tg = [float(target[0]), float(target[1]), float(target[2])]
    if mode == M_OBSERVE:
        if not auth_ok:
            st["state"] = "NOAUTH"
            return out({"state": "NOAUTH", "decision": REFUSE, "reason": "NO_AUTH", "rule": "R-AUTH",
                        "detail": "eskalacja OBSERVE bez tokenu operatora", "applied": hold})
        st["state"] = "OBSERVING"
        return out({"state": "OBSERVING", "decision": ALLOW, "reason": None, "rule": "R-O", "applied": tg})
    st["state"] = "PATROL"
    return out({"state": "PATROL", "decision": ALLOW, "reason": None, "rule": "R-P", "applied": tg})


CORE = KV.CORE


def prod_core(d, sh):
    return {**{k: d.get(k) for k in CORE}, "phase": sh.kont_phase(), "t_kont": sh._t_kont, "cause": sh.kont_cause,
            "n_enter": sh.n_kont_enter, "tau": sh._tau, "j": sh._j_eff}


def mir_core(m):
    return {**{k: m.get(k) for k in CORE}, **{k: m[k] for k in ("phase", "t_kont", "cause", "n_enter", "tau", "j")}}


# ================================ P1_nadir (z3) ===============================
def prove_p1():
    import z3
    res = dict(KV.prove_p1())
    z3m, V, NOM, KONT, KREF, sv, inv, tau = KV._p1_model()
    c = sv("c_")
    geo, pos_bad, auth_ok, kflag, kviol, nom = z3.Bools("geo pos_bad auth_ok kflag kviol nom")
    mode = z3.Int("mode")
    cp, dec, rsn, L = tau(c, geo, mode, pos_bad, auth_ok, kflag, kviol, nom)
    pre = z3.And(inv(c), V.valid(mode))
    lv = list(L.values())
    excl = z3.And(*[z3.Not(z3.And(a, b)) for i, a in enumerate(lv) for b in lv[i + 1:]])
    s = z3.Solver(); s.add(pre); s.add(z3.Not(excl)); res["P1p_leaves_exclusive"] = str(s.check())
    s = z3.Solver(); s.add(pre); s.add(z3.Not(z3.Or(*lv))); res["P1p_leaves_exhaustive"] = str(s.check())
    return res, len(lv)


# ================================ P7_nadir =====================================
def _abs_step(state, lost, bar, fix, deb, hyst, thr, j_worst, agemax):
    """Krok LUSTRA (monitor GNSS + bariera piły) na stanie abstrakcyjnym (gb, gh, kont, kref, hf, age, j); zegar w
    tickach (now całkowite, N+1 = bieżący tick). fix ∈ {None, j'} — poprawka przyjęta w tym ticku (t_fix = now).
    age = ticki od poprawki (hf) albo od zera zegara utraty (¬hf ∧ kont), saturowany do agemax."""
    gb, gh, kont, kref, hf, age, j = state
    N = 10 ** 6
    g = {"g_bad": gb, "g_healthy": gh, "run_t0": (N - (gb - 1)) if gb >= 1 else None, "kont": kont,
         "kont_t0": (N - age) if (kont and not hf) else (N - 5 if kont else None), "kref": kref, "cause": None,
         "n_enter": 0, "t": None}
    fx = {"t_fix": (N - age) if hf else None, "j": j if hf else None, "tau": None, "jeff": None}
    if fix is not None:
        fx["t_fix"], fx["j"] = N + 1, fix
    KV.g_monitor_step(g, lost, N + 1, deb, hyst)
    nadir_barrier_step(g, fx, N + 1, lambda t, jj: bar, thr, j_worst)
    hf2 = fx["t_fix"] is not None
    if hf2:
        age2 = min(N + 1 - fx["t_fix"], agemax)
    else:
        age2 = min(N + 1 - g["kont_t0"], agemax) if g["kont"] else 0
    s2 = (min(g["g_bad"], deb), g["g_healthy"], g["kont"], g["kref"], hf2, age2, fx["j"] if hf2 else None)
    return s2, (not kont) and g["kont"], kont and not g["kont"]


def build_graph(deb, hyst, thr, j_worst, fixes):
    agemax = max(thr)
    init = (0, 0, False, False, False, 0, None)
    nodes = {init}
    edges = []
    q = deque([init])
    while q:
        s = q.popleft()
        for lost in (True, False):
            for bar in ((True, False) if s[2] or lost else (False,)):
                for fix in fixes:
                    d, en, ex = _abs_step(s, lost, bar, fix, deb, hyst, thr, j_worst, agemax)
                    edges.append((s, (lost, bar, fix), d, en, ex))
                    if d not in nodes:
                        nodes.add(d); q.append(d)
    return init, nodes, edges


def _p7_checks(nodes, edges, deb, hyst, thr, j_worst):
    jeff = lambda n: n[6] if n[4] else j_worst
    chk = {}
    enter_e = [(s, f, d) for (s, f, d, en, ex) in edges if en]
    exit_e = [(s, f, d) for (s, f, d, en, ex) in edges if ex]
    chk["a_enter_only_lost_after_deb"] = all(f[0] is True and s[0] == deb - 1 for (s, f, d) in enter_e) and bool(enter_e)
    chk["b_no_allow_in_utrata_age_ge_thr"] = all(n[5] < thr[jeff(n)] for n in nodes if n[2] and not n[3])
    lastok = [(s, f, d) for (s, f, d, en, ex) in edges
              if s[2] and not s[3] and f[2] is None and s[5] == thr[jeff(s)] - 1 and d[2]]
    chk["b_refuse_exactly_at_thr"] = bool(lastok) and all(d[3] for (s, f, d) in lastok)
    chk["c_exit_only_after_hyst_clears_kref"] = bool(exit_e) and all(
        f[0] is False and s[1] == hyst - 1 and not d[3] and not d[2] for (s, f, d) in exit_e)
    chk["d_kref_sticky_while_utrata_even_with_fix"] = all(d[3] for (s, f, d, en, ex) in edges if s[3] and d[2])
    chk["e_fix_resets_tau"] = all(d[4] and d[5] == 0 and d[6] == f[2] for (s, f, d, en, ex) in edges if f[2] is not None)
    bar_ref = {}
    for (s, f, d, en, ex) in edges:
        if s[2] and not s[3] and f[1] and d[2] and d[3] and f[2] is None:
            bar_ref.setdefault(jeff(s), set()).add(s[5])
    chk["f_bar_refuse_reachable_every_age_lt_thr"] = all(
        bar_ref.get(jj, set()) >= set(range(1, thr[jj] - 1)) for jj in bar_ref) and bool(bar_ref)
    chk["g_no_fix_uses_j_worst"] = all(n[5] < thr[j_worst] for n in nodes if n[2] and not n[3] and not n[4])
    return chk


def prove_p7():
    th = FM.shield_thresholds()
    c = consts()
    deb, hyst = th["debounce_ticks"], th["hyst_ticks"]
    dt = Fraction(str(th["dt"]))
    thr = []
    for ts in c["tau_star"]:
        x = (Fraction(ts) - T_MARGIN_TICKS * dt) / dt
        assert x.denominator == 1
        thr.append(int(x))
    jw = max(range(J_N), key=lambda j: c["eps_fix"][j])
    res, chk = {"thr_ticks": thr, "debounce": deb, "hyst": hyst, "j_worst": jw}, {}
    for j in range(J_N):
        init, nodes, edges = build_graph(deb, hyst, thr, jw, (None, j))
        cj = _p7_checks(nodes, edges, deb, hyst, thr, jw)
        res[f"graf_j{j}"] = {"n_states": len(nodes), "n_edges": len(edges)}
        chk.update({f"j{j}_{k}": v for k, v in cj.items()})
    # instancja zredukowana: pełne przełączanie koszyków i brak poprawki
    rthr = [6, 6, 6, 5]
    init, nodes, edges = build_graph(2, 3, rthr, 3, (None, 0, 1, 2, 3))
    cr = _p7_checks(nodes, edges, 2, 3, rthr, 3)
    res["zredukowana"] = {"deb": 2, "hyst": 3, "thr": rthr, "n_states": len(nodes), "n_edges": len(edges)}
    chk.update({f"red_{k}": v for k, v in cr.items()})
    z = _p7_z3(deb, hyst, thr, jw)
    return all(chk.values()) and all(v == "unsat" for v in z.values()), res, chk, z


def _p7_z3(deb, hyst, thr, jw):
    import z3
    gb, gh, age, j, jf = z3.Ints("gb gh age j jf")
    kont, kref, hf, lost, bar, fix = z3.Bools("kont kref hf lost bar fix")
    D, H, AM = z3.IntVal(deb), z3.IntVal(hyst), z3.IntVal(max(thr))
    THR = lambda x: z3.If(x == 0, thr[0], z3.If(x == 1, thr[1], z3.If(x == 2, thr[2], thr[3])))
    dom = z3.And(gb >= 0, gb <= D, gh >= 0, gh <= H - 1, age >= 0, age <= AM, j >= 0, j <= 3, jf >= 0, jf <= 3,
                 z3.Implies(z3.Not(kont), z3.And(z3.Not(kref), gh == 0, gb <= D - 1)),
                 z3.Implies(z3.And(z3.Not(kont), z3.Not(hf)), age == 0))
    gbL = gb + 1
    enterL = z3.And(z3.Not(kont), gbL >= D)
    kontL = z3.Or(kont, enterL)
    ghH = gh + 1
    exitH = z3.And(kont, ghH >= H)
    kontH = z3.And(kont, z3.Not(exitH))
    kont2 = z3.If(lost, kontL, kontH)
    hf2 = z3.Or(hf, fix)
    j2 = z3.If(fix, jf, j)
    inc = lambda a: z3.If(a + 1 < AM, a + 1, AM)
    age2 = z3.If(fix, 0, z3.If(hf, inc(age), z3.If(z3.And(lost, enterL), gb, z3.If(kont2, inc(age), 0))))
    jeff2 = z3.If(hf2, j2, jw)
    kref_pre = z3.And(kont2, kref)
    kref2 = z3.And(kont2, z3.Or(kref_pre, age2 >= THR(jeff2), bar))
    out = {}

    def unsat(f):
        s = z3.Solver(); s.add(dom); s.add(f)
        return "unsat" if s.check() == z3.unsat else "sat"
    out["z3_b_no_allow_age_ge_thr"] = unsat(z3.And(kont2, z3.Not(kref2), age2 >= THR(jeff2)))
    out["z3_d_kref_sticky_with_fix"] = unsat(z3.And(kont, kref, kont2, z3.Not(kref2)))
    out["z3_e_fix_resets"] = unsat(z3.And(fix, z3.Not(z3.And(hf2, age2 == 0, j2 == jf))))
    out["z3_c_exit_needs_hyst"] = unsat(z3.And(kont, z3.Not(kont2), z3.Not(z3.And(z3.Not(lost), gh >= H - 1))))
    return out


# ================================ P5_nadir =====================================
def _new_prod(hyst=None, nadir=True, kont=True):
    from r03.nadir_shield import NadirShield
    sh = NadirShield(kont_mode=kont, nadir_mode=nadir)
    sh.reset()
    if hyst is not None:
        sh.pos_hyst_ticks = hyst
    return sh


def run_conformance_episode(ticks, C, hyst=None, coverage=None, tau_bind=False, latch=None):
    from r01.proofs.conformance import RSN_ID, STATE_ID, MODE_ID, DEC_ID
    sh = _new_prod(hyst)
    Cm = dict(C)
    if hyst is not None:
        Cm["hyst_ticks"] = hyst
    st = new_mirror_state()
    if latch is not None:
        sh.latch_refuse(*latch); st["terminal"] = latch; st["state"] = "DONE"
    model = KV._p1_model() if tau_bind else None
    phid = {"NOMINAL": 0, "KONT": 1, "KONT_REFUSE": 2}
    for k, inp in enumerate(ticks):
        pre = {"tm": sh.terminal is not None, "rsn": RSN_ID[sh.terminal[0]] if sh.terminal is not None else 0,
               "st": STATE_ID[sh.state], "ph": phid[sh.kont_phase()]}
        geo = sh._geofence_violation(inp["pos"], inp["vel"], inp["target"])[0]
        d = sh.step(k, inp["pos"], inp["vel"], inp["target"], mode=inp.get("mode", M_PATROL),
                    pos_flag=inp.get("pos_flag"), auth_ok=inp.get("auth_ok", True), cs_gnss_pos=inp.get("cs_gnss_pos"),
                    now=inp.get("now"), r_est=inp.get("r_est"), t_fix=inp.get("t_fix"), kosz_j=inp.get("kosz"))
        m = mirror_step(st, k, inp, Cm)
        pc, mc = prod_core(d, sh), mir_core(m)
        if pc != mc:
            return [{"k": k, "in": inp, "prod": pc, "mir": mc}]
        if coverage is not None:
            coverage.add(d.get("rule"))
            if d.get("rule") == "R-KONT":
                coverage.add("cause:" + str(sh.kont_cause))
                coverage.add(f"refuse_j{sh._j_eff}")
            if sh.n_kont_enter >= 2:
                coverage.add("second_episode")
            if sh._kont and sh._t_fix is None:
                coverage.add("utrata_bez_poprawki")
            if sh._kont and sh._t_fix is not None:
                coverage.add(f"utrata_j{sh._j}")
            if inp.get("t_fix") is not None and sh._kont and sh._tau is not None and sh._tau == 0.0:
                coverage.add("tau_zero")
        if tau_bind:
            z3, V, NOM, KONT, KREF, sv, inv, tau = model
            c = {"tm": z3.BoolVal(pre["tm"]), "rsn": z3.IntVal(pre["rsn"]), "st": z3.IntVal(pre["st"]),
                 "ph": z3.IntVal(pre["ph"])}
            t, j = sh._tau, sh._j_eff
            kviol = bool(sh._kont and t is not None and (t >= C["thr"][j] or sh._r_est > C["R"][j][int(math.floor(t))]))
            nom = bool(sh._r_est > C["r_nom"] and KV.m_outward(inp["pos"], inp["target"]) > 0.0)
            cp, dec, rsn, _ = tau(c, z3.BoolVal(geo), z3.IntVal(MODE_ID[inp.get("mode", M_PATROL)]),
                                  z3.BoolVal(bool(sh._pos_refuse)), z3.BoolVal(inp.get("auth_ok", True)),
                                  z3.BoolVal(bool(sh._kont)), z3.BoolVal(kviol), z3.BoolVal(nom))
            ev = lambda e: z3.simplify(e)
            post = {"tm": z3.is_true(ev(cp["tm"])), "st": ev(cp["st"]).as_long(), "ph": ev(cp["ph"]).as_long()}
            s_post = {"tm": sh.terminal is not None, "st": STATE_ID[sh.state], "ph": phid[sh.kont_phase()]}
            if ev(dec).as_long() != DEC_ID[d["decision"]] or ev(rsn).as_long() != RSN_ID[d.get("reason")] or post != s_post:
                return [{"k": k, "in": inp, "tau": post, "prod": {"dec": d["decision"], "rsn": d.get("reason"), **s_post}}]
    return []


def passthrough_episode(ticks, hyst=None, latch=None):
    """T0: NadirShield(nadir=0, kont=1) ≡ KontShield(kont=1) i NadirShield(nadir=0, kont=0) ≡ PatrolShield, pełny dict."""
    from r03.kont_shield import KontShield
    from r01.shield import PatrolShield
    pairs = [(_new_prod(hyst, nadir=False, kont=True), KontShield(kont_mode=True)),
             (_new_prod(hyst, nadir=False, kont=False), PatrolShield())]
    for a, b in pairs:
        b.reset()
        if hyst is not None:
            b.pos_hyst_ticks = hyst
        if latch is not None:
            a.latch_refuse(*latch); b.latch_refuse(*latch)
    for k, inp in enumerate(ticks):
        kw = dict(mode=inp.get("mode", M_PATROL), pos_flag=inp.get("pos_flag"), auth_ok=inp.get("auth_ok", True))
        kk = dict(kw, cs_gnss_pos=inp.get("cs_gnss_pos"), now=inp.get("now"), r_est=inp.get("r_est"))
        for i, (a, b) in enumerate(pairs):
            if i == 0:
                da = a.step(k, inp["pos"], inp["vel"], inp["target"], **kk)
                db = b.step(k, inp["pos"], inp["vel"], inp["target"], **kk)
            else:
                da = a.step(k, inp["pos"], inp["vel"], inp["target"], **kk)
                db = b.step(k, inp["pos"], inp["vel"], inp["target"], **kw)
            if json.dumps(da, sort_keys=True, default=str) != json.dumps(db, sort_keys=True, default=str):
                return [{"k": k, "para": ["Nadir(0)≡Kont(1)", "Nadir(0,0)≡Patrol"][i], "a": da, "b": db}]
    return []


def _tick(pos, vel=(0.0, 0.0, 0.0), target=None, **kw):
    return {"pos": list(pos), "vel": list(vel), "target": list(target if target is not None else pos), **kw}


def build_grid(C):
    """Siatka prereg NADIR: brzegi τ*(j), bariera per (k, j), poprawka resetuje τ, brak poprawki ⇒ j_worst, poprawka
    sprzed utraty, τ ujemne obcięte, przełączenie koszyka, zatrzask odporny na poprawkę, histereza/drugi epizod,
    R-G-NOM, priorytety. Czas w `now`."""
    deb, hyst, dt = C["debounce_ticks"], C["hyst_ticks"], C["dt"]
    eps = []
    IN = (5.0, 0.0, -10.0)

    def run(name, seq, hyst_override=None, latch=None):
        eps.append({"name": name, "hyst": hyst_override, "latch": latch, "ticks": seq})
    L = lambda now, **kw: _tick(kw.pop("pos", IN), cs_gnss_pos=False, now=now, **kw)
    for j in range(J_N):
        thr = C["thr"][j]
        for tend in (thr - dt, thr - 0.001, thr, thr + 0.001):
            run(f"tau_star_j{j}_{tend:.3f}", [L(0.0, t_fix=0.0, kosz=j), L(dt), L(5.0), L(tend)])
        for k in sorted({0, 1, 2, 10, C["tau_star"][j] - 1}):
            for off in (-0.001, 0.001):
                r = C["R"][j][k] + off
                run(f"bar_j{j}_k{k}_{'pod' if off < 0 else 'nad'}",
                    [L(0.0, pos=(r, 0.0, -10.0), t_fix=0.0, kosz=j), L(dt, pos=(r, 0.0, -10.0)),
                     L(k + 0.5, pos=(r, 0.0, -10.0))])
    run("fix_resets_tau", [L(0.0, t_fix=0.0, kosz=0), L(dt), L(15.0), L(15.05, t_fix=15.0, kosz=1), L(30.0), L(36.95),
                           L(37.0, t_fix=37.0, kosz=2)])
    run("no_fix_worst", [L(0.0), L(dt), L(10.0), L(C["thr"][C["j_worst"]] - 0.001), L(C["thr"][C["j_worst"]])])
    run("no_fix_bar_worst", [L(0.0, pos=(C["R"][C["j_worst"]][0] + 0.001, 0.0, -10.0)),
                             L(dt, pos=(C["R"][C["j_worst"]][0] + 0.001, 0.0, -10.0))])
    run("fix_before_entry", [_tick(IN, cs_gnss_pos=True, now=0.0, t_fix=0.0, kosz=0)] +
        [_tick(IN, cs_gnss_pos=True, now=x) for x in (10.0, 20.0)] + [L(21.0), L(21.05), L(22.0)])
    run("tau_negative_clamped", [L(0.0), L(dt), L(1.0, t_fix=1.02, kosz=3), L(1.05)])
    run("latch_survives_fix", [L(0.0, t_fix=0.0, kosz=3), L(dt), L(25.0), L(25.05, t_fix=25.05, kosz=0), L(25.1)])
    for (j1, j2) in ((0, 3), (3, 0), (1, 2)):
        r = (C["R"][j1][0] + C["R"][j2][0]) / 2
        run(f"switch_j{j1}_j{j2}", [L(0.0, pos=(r, 0.0, -10.0), t_fix=0.0, kosz=j1), L(dt, pos=(r, 0.0, -10.0)),
                                    L(0.2, pos=(r, 0.0, -10.0), t_fix=0.2, kosz=j2), L(0.25, pos=(r, 0.0, -10.0))])
    seq = [L(i * dt, t_fix=0.0, kosz=0) for i in range(deb)]
    seq += [_tick(IN, cs_gnss_pos=True, now=(deb + i) * dt) for i in range(hyst)]
    seq += [L((deb + hyst + i) * dt) for i in range(deb + 1)]
    run("hyst_exit_second_episode", seq)
    seq = [L(x, t_fix=0.0, kosz=1) for x in (0.0, dt, 23.0)]
    seq += [_tick(IN, cs_gnss_pos=True, now=23.0 + (i + 1) * dt) for i in range(hyst)]
    run("refuse_then_reversal", seq)
    for r in (C["r_nom"] - 0.01, C["r_nom"] + 0.01):
        for tgt, nm in (((r + 1.0, 0.0, -10.0), "out"), ((r - 1.0, 0.0, -10.0), "in"), ((r, 1.0, -10.0), "tan")):
            run(f"nom_{r:.2f}_{nm}", [_tick((r, 0.0, -10.0), target=tgt, cs_gnss_pos=True, now=0.0)])
    FAR = (45.0, 0.0, -10.0)
    run("prio_pos_over_kont", [L(x, pos_flag=True, t_fix=0.0, kosz=0) for x in (0.0, dt, 23.0)])
    run("prio_kont_over_geo", [L(0.0, t_fix=0.0, kosz=0), L(dt), L(23.0, target=FAR)])
    run("prio_geo_over_nom", [_tick((27.4, 0.0, -10.0), target=FAR, cs_gnss_pos=True, now=0.0)])
    run("prio_latch_over_kont", [L(x) for x in (0.0, dt, 23.0)], latch=("STALE_CMD", "adm"))
    for md, auth in ((M_HOLD, True), (M_RETURN, True), (M_OBSERVE, True), (M_OBSERVE, False), (M_ABORT, True)):
        run(f"mode_{md}_{auth}", [_tick(IN, mode=md, auth_ok=auth, cs_gnss_pos=True, now=0.0)])
        run(f"mode_utrata_{md}_{auth}", [L(0.0, mode=md, auth_ok=auth, t_fix=0.0, kosz=2), L(dt, mode=md, auth_ok=auth)])
    run("none_inputs", [_tick(IN, now=0.0), _tick(IN, cs_gnss_pos=None, now=dt)])
    return {"provenance": {"prover": "r01/proofs/p9_nadir_verify.py:build_grid", "debounce": deb, "hyst": hyst,
                           "tau_star": C["tau_star"], "dt": dt, "R_nom": C["r_nom"],
                           "note": "NIETYKALNE po commicie (prereg). Zmiana ⇒ dokument CC."},
            "episodes": eps}


def fuzz_episode(rng, C):
    long_ep = rng.random() < 0.1
    n = rng.randint(120, 320) if long_ep else rng.randint(1, 40)
    p_lost = rng.choice([0.05, 0.3, 0.7, 0.95])
    p_fix = rng.choice([0.0, 0.02, 0.3, 0.9])
    hyst = None if long_ep else rng.choice([None, 1, 2, 3, 5])
    now = rng.uniform(0.0, 5.0)
    big = rng.random() < 0.5
    lost = rng.random() < p_lost
    ticks = []
    for _ in range(n):
        if rng.random() < 0.15:
            lost = rng.random() < p_lost
        cs = None if rng.random() < 0.03 else (not lost)
        ang = rng.uniform(0, 2 * math.pi)
        r = rng.choice([rng.uniform(0, 40), rng.uniform(22.0, 28.0), C["r_nom"] + rng.uniform(-0.05, 0.05),
                        C["R"][rng.randrange(J_N)][0] + rng.uniform(-0.05, 0.05)])
        pos = (r * math.cos(ang), r * math.sin(ang), -rng.uniform(0, 25))
        tk = {"pos": pos, "vel": (rng.uniform(-4, 4), rng.uniform(-4, 4), rng.uniform(-2, 2)),
              "target": (pos[0] + rng.uniform(-3, 3), pos[1] + rng.uniform(-3, 3), -rng.uniform(0, 25)),
              "mode": rng.choices([M_PATROL, M_HOLD, M_RETURN, M_ABORT, M_OBSERVE], [0.8, 0.05, 0.05, 0.02, 0.08])[0],
              "pos_flag": None if rng.random() < 0.3 else (rng.random() < 0.08), "auth_ok": rng.random() < 0.8,
              "cs_gnss_pos": cs, "now": now, "r_est": (None if rng.random() < 0.9 else r + rng.uniform(-0.5, 0.5))}
        if rng.random() < p_fix:
            tk["t_fix"] = now - rng.choice([0.0, rng.uniform(0.0, 0.3), rng.uniform(-0.03, 0.0)])
            tk["kosz"] = rng.randrange(J_N)
        ticks.append(tk)
        now += rng.uniform(0.3, 3.0) if big else rng.choice([C["dt"], rng.uniform(0.0, 0.2)])
    return ticks, hyst


def _load(p, typ=None):
    out = []
    for line in open(p):
        if typ and f'"t": "{typ}"' not in line:
            continue
        try:
            out.append(json.loads(line))
        except ValueError:
            pass
    return out


def s2_fixture(boot):
    """Wejścia nakładki z lotu S2 (rama.jsonl + tk + demo, po ticku): pos = p_EKF, cel = sp_EKF, vel z demo,
    cs_gnss_pos i pos_flag z tk, now = sim; t_fix/koszyk z obserwacji przyjętych w danym ticku, litera r_h < 8
    (najbliższy znacznik poprawki, rh_est producenta) — od episode_start do pierwszego ticku zejścia."""
    from r03.nadir_shield import kosz
    d = os.path.join(S2, boot)
    rama = sorted(_load(os.path.join(d, "rama.jsonl")), key=lambda r: r["tick"])
    tk = {r["tick"]: r for r in _load(os.path.join(d, "trace.jsonl"), "tk")}
    demo = {r["tick"]: r for r in _load(os.path.join(d, "demo.jsonl"))}
    ticks, n_odrz_rh = [], 0
    for r in rama:
        if r["desc"]:
            break
        t, dm = tk.get(r["tick"]), demo.get(r["tick"])
        if t is None or dm is None:
            continue
        inp = {"pos": r["p_ekf"], "vel": dm["own_vel_ned"], "target": r["sp_ekf"], "mode": M_PATROL,
               "pos_flag": t["pf"], "auth_ok": True, "cs_gnss_pos": t["cs"], "now": r["sim"], "r_est": None}
        for o in r["obs"]:
            if o.get("ok"):
                j = kosz(o["jeden"]["rh_est"])
                if j is None:
                    n_odrz_rh += 1
                    continue
                inp["t_fix"], inp["kosz"] = o["t_frame"], j
        ticks.append(inp)
    return ticks, {"n_ticks": len(ticks), "n_poprawek_odrzuconych_rh_ge_8": n_odrz_rh}


def s2_offline(boot, C):
    ticks, meta = s2_fixture(boot)
    sh = _new_prod()
    first, taus, js = {}, [], {}
    for k, inp in enumerate(ticks):
        d = sh.step(k, inp["pos"], inp["vel"], inp["target"], mode=M_PATROL, pos_flag=inp["pos_flag"],
                    cs_gnss_pos=inp["cs_gnss_pos"], now=inp["now"], t_fix=inp.get("t_fix"), kosz_j=inp.get("kosz"))
        ph = sh.kont_phase()
        if sh._tau is not None:
            taus.append(sh._tau)
            js[sh._j_eff] = js.get(sh._j_eff, 0) + 1
        if ph not in first:
            first[ph] = {"now": inp["now"], "tau": sh._tau, "j": sh._j_eff, "cause": sh.kont_cause, "rule": d.get("rule"),
                         "r_est": round(sh._r_est, 3)}
    taus.sort()
    return {**meta, "fazy_pierwsze": first, "n_kont_enter": sh.n_kont_enter,
            "tau_utrata_p95": round(taus[int(0.95 * len(taus))], 3) if taus else None,
            "tau_utrata_max": round(taus[-1], 3) if taus else None, "koszyki_w_utracie": js,
            "refuse_offline": "KONT_REFUSE" in first}


def prove_p5(fuzz_n=100000, tau_random=2000, seed0=0):
    C = mirror_consts()
    grid = json.load(open(GRID))
    cov, mism, pt = set(), [], []
    n = {"grid": 0, "fuzz": 0, "fixture": 0, "tau": 0, "passthrough": 0}
    for e in grid["episodes"]:
        latch = tuple(e["latch"]) if e["latch"] else None
        mism += run_conformance_episode(e["ticks"], C, e["hyst"], cov, tau_bind=True, latch=latch)
        pt += passthrough_episode(e["ticks"], e["hyst"], latch)
        n["grid"] += len(e["ticks"]); n["tau"] += len(e["ticks"]); n["passthrough"] += len(e["ticks"])
    rng = random.Random(seed0)
    for i in range(fuzz_n):
        ticks, hyst = fuzz_episode(rng, C)
        tb = i < tau_random
        mism += run_conformance_episode(ticks, C, hyst, cov, tau_bind=tb)
        if i < fuzz_n // 4:
            pt += passthrough_episode(ticks, hyst)
            n["passthrough"] += len(ticks)
        n["fuzz"] += len(ticks)
        if tb:
            n["tau"] += len(ticks)
        if len(mism) > 5 or len(pt) > 5:
            break
    fx = {}
    for b in S2_CIECIA:
        ticks, meta = s2_fixture(b)
        mism += run_conformance_episode(ticks, C, None, cov, tau_bind=True)
        n["fixture"] += len(ticks); n["tau"] += len(ticks)
        fx[b] = s2_offline(b, C)
    need = {"R-POS", "R-KONT", "R-G", "R-G-NOM", "R-A", "R-H", "R-R", "R-O", "R-AUTH", "R-P", "cause:τ*", "cause:bariera",
            "second_episode", "utrata_bez_poprawki", "tau_zero"} | {f"utrata_j{j}" for j in range(J_N)} | \
           {f"refuse_j{j}" for j in range(J_N)}
    missing = sorted(need - cov)
    return (not mism and not pt and not missing), mism, pt, sorted(x for x in cov if x), missing, n, fx


# =================================== CLI =====================================
def _write(name, cert):
    p = os.path.join(CERTS, name)
    if os.path.exists(p):
        old = json.load(open(p))
        print(f"  {name} istnieje — zgodność sha: {'TAK' if old.get('model_sha256') == cert['model_sha256'] else 'NIE'}")
    json.dump(cert, open(p, "w"), indent=2, ensure_ascii=False)
    print(f"  zapisano {p}")


A_NADIR = ("A-nadir (ANEKS_NADIR-2 §3.2, PROMPT_NADIR_S3 C1): (i) przyrost dryfu EKF w oknie między poprawkami "
           "≤ ε_b(⌊τ⌋) (miara 3D; zmierzone S2: 440 okien bez GNSS, max 0.94, 0 przekroczeń); (ii) |p_fix − GT| ≤ "
           "ε_fix_freeze(koszyk) (zmierzone S2 + litera przyjęcia r_h < 8 m); stąd |r_true − r_est(ramy)| ≤ ε_fix + ε_b. "
           "Walidowane w S4 jako (g); przekroczenie = FAIL nogi.")


def main_p9():
    import z3
    ok, per, arith, opis, c = prove_p9()
    print("=== P9_nadir: zawieranie z barierą piły (z3, per koszyk × kubełek) ===")
    bad = {k: v for k, v in per.items() if not (v["main"] == "unsat" and all(v[x] == "sat" for x in v if x != "main"))}
    print(f"  obligacji (j, k): {len(per)}, niespełnionych: {len(bad)} {list(bad)[:5]}")
    print(f"  τ*: {c['tau_star']}  arytmetyka: {arith}\n  opisowo: {opis}")
    print(f"WERDYKT P9_nadir: {'PROVED' if ok else 'UNPROVEN'}")
    if not ok:
        sys.exit(1)
    _write("P9_nadir.json", {
        "property": "P9_nadir", "verdict": "PROVED",
        "method": "z3 LRA per koszyk j∈{0…3} × kubełek k∈{0…τ*(j)−1} + ostrość czterostronna (ε_fix, ε_b, R, Δ_D5)",
        "z3_lib": z3.get_version_string(), "obligations": per, "arithmetic": arith, "opisowo": opis,
        "theorem": "∀j, ∀k<τ*(j): 0≤r_est≤R(k,j) ∧ 0≤ε_f≤ε_fix(j) ∧ 0≤ε_d≤ε_b(k) ∧ ε=ε_f+ε_d ∧ 0≤Δ≤Δ_D5 ∧ 0≤s≤d_stop ∧ "
                   "|r_c−r_est|≤ε ∧ r_d≤r_est+ε+s+Δ ⇒ r_c≤R_E ∧ r_d≤R_E; R(k,j)=R_E−d_stop−u(k,j), "
                   "u(k,j)=ε_fix_freeze(j)+ε_b(k)+Δ_D5; ostrość: każda z czterech wielkości +δ łamie (δ=1/1000)",
        "constants": {"freeze": "results/KONT/s2/s2_freeze_bf.json", "freeze_sha256": c["sha256"],
                      "aneks": "ANEKS_NADIR-2.md", "aneks_sha256": c["aneks"]["sha256"],
                      "eps_fix_freeze": [str(x) for x in c["eps_fix"]], "tau_star_s": c["tau_star"],
                      "R_E": str(c["r_e"]), "d_stop": str(c["d_stop"]), "delta_D5": str(c["delta"]),
                      "m_p50": str(c["m_p50"]), "r_h_max": 8, "eps_b": [str(x) for x in c["eps"][:max(c["tau_star"])]]},
        "assumptions": [A_NADIR,
                        "A-react (R0.1): przemieszczenie od ostatniego ALLOW do zatrzymania ≤ d_stop (r01/config.py:24-27).",
                        "A-D5 (ANEKS_KONT-3): dryf zejścia ≤ Δ_D5 od REFUSE do przyziemienia.",
                        "Brak poprawki od wejścia w utratę ⇒ τ od zera zegara utraty, koszyk najgorszy (j=3).",
                        "τ*(j) z reguły PRE §3 (ε_fix(j)+ε_b(k)+Δ_D5 ≤ m_p50 dla k<τ*); twierdzenie nie wymusza τ* — "
                        "bariera zawiera dla każdego k<τ*."],
        "code_refs": {"bariera": "r03/nadir_shield.py:NadirShield._kont_barrier, r_pila",
                      "litera_rh": "harness/nadir_fix.py:Rama.obserwacja (R_H_MAX)", "prover": "r01/proofs/p9_nadir_verify.py"},
        "model_sha256": _self_sha()})


def main_p1():
    import z3
    res, n_leaves = prove_p1()
    ok = all(v == "unsat" for v in res.values())
    print("=== P1_nadir: automat nakładki (z3, 1-indukcja) + wyłączność liści ===")
    for k, v in res.items():
        print(f"  {k}: {v}" + ("  ✓" if v == "unsat" else "  !! (SPODZIEWANO unsat)"))
    print(f"WERDYKT P1_nadir: {'PROVED' if ok else 'UNPROVEN'}")
    if not ok:
        sys.exit(1)
    _write("P1_nadir.json", {
        "property": "P1_nadir", "verdict": "PROVED", "method": "1-induction (z3) + NRA (nom_applied) + wyłączność/wyczerpanie liści",
        "z3_lib": z3.get_version_string(), "obligations": res, "leaves": n_leaves,
        "automaton": "r03/nadir_shield.py:NadirShield (NADIR_MODE=1) — _decide = r03/kont_shield.KontShield._decide (nietknięty); "
                     "latch > R-POS > R-KONT(bariera piły) > R-G > abort > hold > return > R-G-NOM > {OBSERVE∧auth | R-AUTH} > "
                     "patrol; kviol = τ ≥ τ*(j)−2·dt ∨ r_est > R(⌊τ⌋, j)",
        "model_source": {"file": "r01/proofs/p9_kont_verify.py:_p1_model/prove_p1 (READ-ONLY)",
                         "sha256": hashlib.sha256(open(KV.__file__, "rb").read()).hexdigest()},
        "properties": {"P1a…P1o, nom_applied": "jak P1_kont (kviol = bariera piły)",
                       "P1p": "dokładnie jeden liść automatu aktywny w każdym ticku (wyłączność i porządek reguł)"},
        "assumptions": ["geo/pos_bad/kflag/kviol/nom = predykaty liczone w kodzie; arytmetyka bariery = P9_nadir, "
                        "monitor + zegar τ = P7_nadir, zgodność kod↔model = P5_nadir (tau_bind)."],
        "model_sha256": _self_sha()})


def main_p7():
    ok, res, chk, z = prove_p7()
    print("=== P7_nadir: graf monitora GNSS + zegara τ (enumeracja) ===")
    print(f"  {res}\n  checks fail: {[k for k, v in chk.items() if not v]}\n  z3: {z}")
    print(f"WERDYKT P7_nadir: {'PROVED' if ok else 'UNPROVEN'}")
    if not ok:
        sys.exit(1)
    _write("P7_nadir.json", {
        "property": "P7_nadir", "verdict": "PROVED",
        "method": "wyczerpująca enumeracja osiągalnego grafu (BFS, stałe produkcji) monitora GNSS + zegara τ + koszyka na "
                  "LUSTRZE (KV.g_monitor_step + nadir_barrier_step ≡ produkcja, P5_nadir), osobno per koszyk; instancja "
                  "zredukowana z pełnym przełączaniem koszyków; z3-duplikat kroku",
        "obligations": res, "checks": chk, "z3_duplicate": z,
        "theorem": "(a) wejście w utratę tylko na fladze po debounce; (b) brak ALLOW w utracie przy τ ≥ τ*(j)−2·dt, REFUSE "
                   "dokładnie przy progu; (c) wyjście tylko po hyst zdrowych tickach, czyści zatrzask; (d) zatrzask trwa "
                   "w utracie także po nowej poprawce; (e) poprawka zeruje τ i ustawia koszyk; (f) REFUSE z bariery "
                   "osiągalny w każdym wieku < progu; (g) brak poprawki ⇒ próg koszyka najgorszego",
        "abstraction": "g_bad saturowany do debounce; wiek (τ w tickach) saturowany do max progu; bariera = wejście wolne; "
                       "poprawka = wejście ∈ {brak, j}; zegar w tickach (now = k·dt).",
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
    ok, mism, pt, cov, missing, n, fx = prove_p5()
    print("=== P5_nadir: konformancja lustro ≡ produkcja, tau ≡ produkcja, passthrough T0 ===")
    print(f"  ticki: {n}  rozbieżności: {len(mism)}  passthrough: {len(pt)}  pokrycie: {cov}  brak: {missing}")
    for b, v in fx.items():
        print(f"  fikstura {b}: {v}")
    for x in (mism[:1] + pt[:1]):
        print("  PIERWSZA ROZBIEŻNOŚĆ:", json.dumps(x, default=str, ensure_ascii=False)[:2000])
    print(f"WERDYKT P5_nadir: {'PASS' if ok else 'FAIL'}")
    if not ok:
        sys.exit(1)
    _write("P5_nadir.json", {
        "property": "P5_nadir", "verdict": "PASS",
        "method": "per-tick konformancja: lustro (mirror_step) ≡ r03/nadir_shield.NadirShield (decyzja, powód, reguła, stan, "
                  "applied, detail, akcja, faza, t_KONT, τ, koszyk, przyczyna, licznik) + tau_kont (P1) ≡ produkcja; "
                  "passthrough NADIR_MODE=0: ≡ KontShield i ≡ PatrolShield pełnym dictem",
        "z3_lib": z3.get_version_string(), "ticks": n, "mismatches": 0, "passthrough_mismatches": 0, "coverage": cov,
        "grid": {"path": "results/NADIR/s3/p5_nadir_grid.json", "sha256": hashlib.sha256(open(GRID, "rb").read()).hexdigest()},
        "fuzz": {"episodes": 100000, "seed": 0, "tau_bound_episodes": 2000, "passthrough_episodes": 25000},
        "fixture_s2": {"cuts": list(S2_CIECIA), "reconstruction": "s2_fixture (rama.jsonl + tk + demo, litera r_h<8)",
                       "offline_decisions": fx},
        "binds": "P1_nadir (tau_kont), P7_nadir (lustro monitora i zegara τ)",
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
