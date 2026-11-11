"""r01/proofs/p9_nad2_verify.py — certy nogi NADIR-II: P9_nad2, P1_nad2, P7_nad2, P5_nad2 (PROMPT_NAD2_S1 §R, PRE_NAD2 §3–§5,
ANEKS_NAD2-1 §2). NOWY plik; provery i certy NADIR-I / KONT / kanon NIETKNIĘTE (r01/proofs/p9_nadir_verify.py,
p9_kont_verify.py, fv_mirror.py importowane READ-ONLY). Każdy cert zapisuje model_sha256 = sha256(tego pliku).

=== PREREJESTRACJA OBLIGACJI (przed pierwszym biegiem) ===
Stałe: s2_freeze_bf.json (ae19f66c — R_E, d_stop, Δ_D5, m_p50 przez KV.load_freeze), tabela U z r03/nadir_shield (F_NAD2, G_NAD2,
KRAW_NAD2, ZAPAS_NAD2, TAU_STAR_NAD2, TAU_EPS_NAD2) ≡ results/NAD2/s1/freeze_U.json (sha256 tabeli, asercja), PRE_NAD2.md i
ANEKS_NAD2-1.md (sha256 asercja). Arytmetyka wymiernie (Fraction). Pole = (przedział i ∈ 0…4, koszyk k ∈ 0…4, tryb ∈ {para,
jeden}); U(i,k,t) = 3/2·(F(k,t) + G(i)); R(i,k,t) = R_E − d_stop − U(i,k,t) − Δ_D5.

C1 P9_nad2 (z3, LRA), dla KAŻDEGO pola (50 obligacji):
  M (oczek. unsat): przesłanki ∧ ¬(r_c ≤ R_E ∧ r_d ≤ R_E), przesłanki =
       0 ≤ r_est ≤ R(i,k,t) ∧ 0 ≤ ε ≤ U(i,k,t) ∧ 0 ≤ Δ ≤ Δ_D5 ∧ 0 ≤ s ≤ d_stop ∧ |r_c − r_est| ≤ ε ∧ r_d ≤ r_est + ε + s + Δ.
  ZAŁOŻENIE wypisane w cercie: |p_corr − GT| ≤ U(przedział osłony, koszyk, tryb) ORAZ r_est osłony = |p_corr| (r_c, r_d
  promienie prawdziwe; ε = błąd pozycji ramy poprawionej).
  Ostrość (oczek. sat, δ = 1/1000): ε = U+δ; r_est = R+δ; Δ = Δ_D5+δ.
  Arytmetyka (asercje): tabela osłony ≡ freeze_U.json (sha), sha PRE/ANEKS; R nierosnąca w i oraz w k (dla każdego trybu);
  u′(4,k,t) ≤ m_p50 dla każdego pola (τ* = 1.05 s z reguły PRE §3: cała tabela pod m_p50); próg REFUSE(τ*) τ ≥ τ* − 2·dt
  = 0.95 s ⇒ τ + TAU_EPS ≤ 1.05 (przedział zawsze zdefiniowany w ALLOW); próg w tickach = 19 (całkowity); pole przy braku
  poprawki (jeden, 4) ma największe U w każdym przedziale; dt = 1/20.
C2 P1_nad2 (z3, 1-indukcja): automat nakładki — w NAD2 _decide = KontShield._decide (nietknięty); bariera tabeli U jako
  predykat kviol; model = p9_kont_verify._p1_model (P1a–P1o + nom_applied) + P1p: liście wzajemnie wyłączne i wyczerpujące.
C3 P5_nad2: (a) konformancja LUSTRO NAD2 (mirror_step_nad2 — wybór ramy po monitorze, bariera tabeli, przeliczenie applied)
  ≡ produkcja (r03/nadir_shield.NadirShield nadir_mode=1, nad2=1) na: fiksturze 12 cięć + 4 nominałów S4 (wejścia z rama.jsonl
  + tk + demo; Δ′, t_fix, koszyk, tryb z replayu NOWEJ litery: harness/nadir_fix.Rama(litera="NAD2") na zapisanych klatkach,
  dostępność poprawki po mono przybycia + detekcja + 5 ms — recon R5), fuzzie ≥ 10⁵ epizodów, siatce brzegów (budowana w
  kodzie, deterministyczna); tau_kont (P1) ≡ produkcja na fiksturze i 2000 epizodach fuzzu; 0 rozbieżności, pełne pokrycie
  reguł, przyczyn, ram i pól.
  (b) OBLIGACJA WEJŚCIA na ścieżce drivera (results/NAD2/tools/nad2_krok.krok) na tickach fikstury S4: r_est osłony = |p_corr|
  (do 1e-6 m) w 100% ticków utraty (KONT, KONT_REFUSE) i = |p_EKF| w 100% ticków NOMINAL; tick przejścia w obu kierunkach
  (epizody syntetyczne NOMINAL→KONT→NOMINAL); MUTANT ze starą ścieżką (osłona bez pozycji poprawionej ⇒ r_est = |p_EKF|)
  wykryty.
  (c) applied decyzji = applied ramy wybranej przeliczone do EKF (applied − Δ w N, E) w 100% ticków utraty, = bez zmian
  w NOMINAL; pozycja bramki komend (R-G-NOM) = pozycja ramy wybranej.
  Passthrough T0: NadirShield(nadir_mode=0) z nad2 włączonym ≡ KontShield ≡ PatrolShield bajtowo (fuzz, siatka).
C4 P7_nad2: wyczerpująca enumeracja grafu monitora GNSS + zegara τ (ticki, stałe produkcji; próg 19 ticków) na LUSTRZE, osobno
  dla każdego pola (wejście poprawki ∈ {brak, pole}); z3-duplikat kroku; osiągalność REFUSE(bariera) w każdym wieku < progu.

Uruchom: PYTHONPATH=.certdeps:. python3 -m r01.proofs.p9_nad2_verify p9|p1|p7|p5|all
"""
from __future__ import annotations
import hashlib
import json
import math
import os
import random
import sys
from fractions import Fraction

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(_HERE))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from r01.proofs import fv_mirror as FM                              # READ-ONLY
from r01.proofs import p9_kont_verify as KV                         # READ-ONLY
from r01.proofs import p9_nadir_verify as PN                        # READ-ONLY (graf P7, passthrough, pomocniki)

CERTS = os.path.join(_HERE, "certs")
PRE = os.path.join(ROOT, "PRE_NAD2.md")
ANEKS = os.path.join(ROOT, "ANEKS_NAD2-1.md")
TRYBY = ("para", "jeden")
NI, NK = 5, 5
T_MARGIN_TICKS = KV.T_MARGIN_TICKS
CIECIA_S4 = ("c01_s01_r4", "c01_s03", "c02_s01", "c02_s03", "c05_s01", "c05_s02", "c08_s01", "c08_s02", "c10_s01", "c10_s02",
             "c11_s01", "c11_s02")
NOM_S4 = ("nom_b1_r2", "nom_b2", "nom_b3", "nom_b4")
S4 = os.path.join(ROOT, "results/NADIR/s4")
EPS_DOST = 0.005


def _self_sha():
    return hashlib.sha256(open(__file__, "rb").read()).hexdigest()


def consts():
    from r03 import nadir_shield as NS
    c = KV.load_freeze()
    chk = NS.nad2_tabela_check(ROOT)
    assert all(chk.values()), chk
    assert hashlib.sha256(open(PRE, "rb").read()).hexdigest() == NS.NAD2_PRE_SHA256
    assert hashlib.sha256(open(ANEKS, "rb").read()).hexdigest() == NS.NAD2_ANEKS_SHA256
    fr = lambda x: Fraction(str(x))
    c["G"] = [fr(x) for x in NS.G_NAD2]
    c["F"] = {t: [fr(x) for x in NS.F_NAD2[t]] for t in TRYBY}
    c["kraw"] = [fr(x) for x in NS.KRAW_NAD2]
    c["zapas"], c["tau_star"], c["tau_eps"] = fr(NS.ZAPAS_NAD2), fr(NS.TAU_STAR_NAD2), fr(NS.TAU_EPS_NAD2)
    c["tabela_check"] = chk
    return c


def U_of(c, i, k, t):
    return c["zapas"] * (c["F"][t][k] + c["G"][i])


def R_of(c, i, k, t):
    return c["r_e"] - c["d_stop"] - U_of(c, i, k, t) - c["delta"]


# ================================ C1 P9_nad2 =====================================
def prove_p9():
    import z3
    from r01.config import DT as CFG_DT
    from r03 import nadir_shield as NS
    c = consts()
    rv = lambda q: z3.RealVal(str(q))
    D = z3.RealVal("1/1000")
    RE, DS, DD = rv(c["r_e"]), rv(c["d_stop"]), rv(c["delta"])
    per = {}
    for t in TRYBY:
        for i in range(NI):
            for k in range(NK):
                Rk, Uk = rv(R_of(c, i, k, t)), rv(U_of(c, i, k, t))
                r_est, eps, dl, s, rc, rd = z3.Reals("r_est eps dl s rc rd")
                pre = z3.And(r_est >= 0, r_est <= Rk, eps >= 0, eps <= Uk, dl >= 0, dl <= DD, s >= 0, s <= DS,
                             rc - r_est <= eps, r_est - rc <= eps, rd <= r_est + eps + s + dl)
                out = {}
                so = z3.Solver(); so.add(pre); so.add(z3.Not(z3.And(rc <= RE, rd <= RE))); out["main"] = str(so.check())
                for nm, (r0, e0, d0) in {"sharp_U": (Rk, Uk + D, DD), "sharp_R": (Rk + D, Uk, DD), "sharp_delta": (Rk, Uk, DD + D)}.items():
                    so = z3.Solver()
                    so.add(r_est == r0, eps == e0, s == DS, dl == d0, rd == r_est + eps + s + dl, rd > RE)
                    out[nm] = str(so.check())
                per[f"{t}_i{i}_k{k}"] = out
    dt = Fraction(1, 20)
    thr = c["tau_star"] - T_MARGIN_TICKS * dt
    arith = {
        "tabela_oslony_eq_freeze": all(c["tabela_check"].values()),
        "R_nonincreasing_in_i": all(R_of(c, i + 1, k, t) <= R_of(c, i, k, t) for t in TRYBY for k in range(NK) for i in range(NI - 1)),
        "R_nonincreasing_in_k": all(R_of(c, i, k + 1, t) <= R_of(c, i, k, t) for t in TRYBY for i in range(NI) for k in range(NK - 1)),
        "u_prim_le_m_p50_all_fields": all(U_of(c, i, k, t) + c["delta"] <= c["m_p50"] for t in TRYBY for i in range(NI) for k in range(NK)),
        "tau_star_eq_last_edge": c["tau_star"] == c["kraw"][-1],
        "dt_is_1_20": Fraction(str(CFG_DT)) == dt,
        "thr_plus_eps_le_last_edge": thr + c["tau_eps"] <= c["kraw"][-1],
        "thr_ticks_integer_19": (thr / dt).denominator == 1 and int(thr / dt) == 19,
        "pole_brak_max_U_each_i": all(U_of(c, i, 4, "jeden") == max(U_of(c, i, k, t) for t in TRYBY for k in range(NK)) for i in range(NI)),
        "pole_brak_eq_shield": NS.POLE_BRAK_NAD2 == ("jeden", 4),
        "shield_u_eq_rational": all(abs(Fraction(str(NS.u_nad2(i, k, t))) - (U_of(c, i, k, t) + c["delta"])) <= Fraction(1, 10 ** 9)
                                    for t in TRYBY for i in range(NI) for k in range(NK)),
    }
    opis = {"u_prim_tau_le_025": {t: [float(U_of(c, 0, k, t) + c["delta"]) for k in range(NK)] for t in TRYBY},
            "R_tau_le_025": {t: [float(R_of(c, 0, k, t)) for k in range(NK)] for t in TRYBY}, "R_nom": float(c["r_nom"]),
            "R_min": float(min(R_of(c, i, k, t) for t in TRYBY for i in range(NI) for k in range(NK))),
            "uwaga": "R_nom 27.30 > R przy każdym polu: wejście w utratę przy r ∈ (R, R_nom] ⇒ REFUSE(bariera) — dostępność, nie "
                     "bezpieczeństwo (twierdzenie główne trzyma)."}
    ok = all(v["main"] == "unsat" and all(v[x] == "sat" for x in ("sharp_U", "sharp_R", "sharp_delta")) for v in per.values()) \
        and all(arith.values())
    return ok, per, arith, opis, c


# ============================ LUSTRO nakładki NAD2 ============================
ALLOW, HOLD, REFUSE = KV.ALLOW, KV.HOLD, KV.REFUSE
M_PATROL, M_HOLD, M_RETURN, M_ABORT, M_OBSERVE = KV.M_PATROL, KV.M_HOLD, KV.M_RETURN, KV.M_ABORT, KV.M_OBSERVE


def mirror_consts():
    th = FM.shield_thresholds()
    c = consts()
    R = {t: [[float(R_of(c, i, k, t)) for k in range(NK)] for i in range(NI)] for t in TRYBY}
    return {**th, "thr": float(c["tau_star"]) - T_MARGIN_TICKS * th["dt"], "kraw": [float(x) for x in c["kraw"]],
            "tau_eps": float(c["tau_eps"]), "R": R, "r_nom": float(c["r_nom"])}


def m_przedzial(tau, C):
    t = tau + C["tau_eps"]
    for i, kr in enumerate(C["kraw"]):
        if t <= kr:
            return i
    return None


def new_mirror_state():
    st = KV.new_mirror_state()
    st["fx"] = {"t_fix": None, "j": None, "tryb": None, "tau": None, "jeff": None, "teff": None, "i": None}
    return st


def nad2_barrier_step(g, fx, now, r_est, C):
    g["t"] = None
    fx["tau"] = fx["jeff"] = fx["teff"] = fx["i"] = None
    if not g["kont"]:
        return
    g["t"] = now - g["kont_t0"]
    if fx["t_fix"] is None:
        t0, t, j = g["kont_t0"], "jeden", 4
    else:
        t0, t, j = fx["t_fix"], fx["tryb"], fx["j"]
    tau = now - t0
    if tau < 0:
        tau = 0.0
    i = m_przedzial(tau, C)
    fx["tau"], fx["jeff"], fx["teff"], fx["i"] = tau, j, t, i
    if g["kref"]:
        return
    if tau >= C["thr"] or i is None:
        g["kref"], g["cause"] = True, "τ*"
    elif r_est > C["R"][t][i][j]:
        g["kref"], g["cause"] = True, "bariera"


def mirror_step_nad2(st, k, inp, C):
    pe, te = inp["pos"], inp["target"]
    pc, tc = inp.get("pos_corr"), inp.get("target_corr")
    vel = inp["vel"]
    now = k * C["dt"] if inp.get("now") is None else float(inp["now"])
    g, fx = st["g"], st["fx"]
    if inp.get("t_fix") is not None and inp.get("kosz") is not None:
        fx["t_fix"], fx["j"] = float(inp["t_fix"]), int(inp["kosz"])
        fx["tryb"] = inp.get("tryb") if inp.get("tryb") in TRYBY else "jeden"
    cs = inp.get("cs_gnss_pos")
    KV.g_monitor_step(g, None if cs is None else (not cs), now, C["debounce_ticks"], C["hyst_ticks"])
    corr = g["kont"] and pc is not None and tc is not None
    pos, target = (pc, tc) if corr else (pe, te)
    dn, de = (float(pc[0]) - float(pe[0]), float(pc[1]) - float(pe[1])) if corr else (0.0, 0.0)
    r_est = math.hypot(float(pos[0]), float(pos[1]))
    nad2_barrier_step(g, fx, now, r_est, C)
    FM.pos_monitor_step(st["pos"], inp.get("pos_flag"), C["debounce_ticks"], C["hyst_ticks"])
    hold = [float(pos[0]), float(pos[1]), float(pos[2])]
    mode, auth_ok = inp.get("mode", M_PATROL), inp.get("auth_ok", True)

    def out(d):
        a = d["applied"]
        if corr:
            d = {**d, "applied": [float(a[0]) - dn, float(a[1]) - de, float(a[2])]}
        ph = "KONT_REFUSE" if g["kref"] else ("KONT" if g["kont"] else "NOMINAL")
        return {**d, "phase": ph, "t_kont": g["t"], "cause": g["cause"], "n_enter": g["n_enter"], "tau": fx["tau"],
                "j": fx["jeff"], "tryb": fx["teff"], "i": fx["i"], "rama": "corr" if corr else "ekf", "r_est": r_est}

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
        return out({"state": "DONE", "decision": REFUSE, "reason": "GEOFENCE", "rule": "R-G", "detail": detail, "applied": hold})
    if mode == M_ABORT:
        st["terminal"] = ("ABORT", "R-A"); st["state"] = "DONE"
        return out({"state": "DONE", "decision": REFUSE, "reason": "ABORT", "rule": "R-A", "detail": "operator abort",
                    "applied": hold})
    if mode == M_HOLD:
        st["state"] = "HOLDING"
        return out({"state": "HOLDING", "decision": HOLD, "reason": None, "rule": "R-H", "applied": hold})
    if mode == M_RETURN:
        st["state"] = "RETURNING"
        return out({"state": "RETURNING", "decision": HOLD, "reason": None, "rule": "R-R", "detail": "return→RTL(MAVSDK)",
                    "applied": hold})
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
    n2 = d.get("nad2") or {}
    return {**{k: d.get(k) for k in CORE}, "phase": sh.kont_phase(), "t_kont": sh._t_kont, "cause": sh.kont_cause,
            "n_enter": sh.n_kont_enter, "tau": sh._tau, "j": sh._j_eff, "tryb": sh._tryb_eff, "i": sh._przedzial,
            "rama": n2.get("rama"), "r_est": sh._r_est}


def mir_core(m):
    return {**{k: m.get(k) for k in CORE},
            **{k: m[k] for k in ("phase", "t_kont", "cause", "n_enter", "tau", "j", "tryb", "i", "rama", "r_est")}}


def _new_prod(hyst=None, nad2=True, nadir=True, kont=True):
    from r03.nadir_shield import NadirShield
    sh = NadirShield(kont_mode=kont, nadir_mode=nadir, nad2=nad2)
    sh.reset()
    if hyst is not None:
        sh.pos_hyst_ticks = hyst
    return sh


def _step_prod(sh, k, inp):
    return sh.step(k, inp["pos"], inp["vel"], inp["target"], mode=inp.get("mode", M_PATROL), pos_flag=inp.get("pos_flag"),
                   auth_ok=inp.get("auth_ok", True), cs_gnss_pos=inp.get("cs_gnss_pos"), now=inp.get("now"),
                   t_fix=inp.get("t_fix"), kosz_j=inp.get("kosz"), tryb=inp.get("tryb"), pos_corr=inp.get("pos_corr"),
                   target_corr=inp.get("target_corr"))


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
        d = _step_prod(sh, k, inp)
        m = mirror_step_nad2(st, k, inp, Cm)
        pc, mc = prod_core(d, sh), mir_core(m)
        if pc != mc:
            return [{"k": k, "in": inp, "prod": pc, "mir": mc}]
        if coverage is not None:
            coverage.add(d.get("rule"))
            coverage.add("rama:" + mc["rama"])
            if d.get("rule") == "R-KONT":
                coverage.add("cause:" + str(sh.kont_cause))
            if sh._kont and mc["i"] is not None:
                coverage.add(f"pole:{mc['tryb']}_i{mc['i']}_k{mc['j']}")
            if sh.n_kont_enter >= 2:
                coverage.add("second_episode")
            if sh._kont and sh._t_fix is None:
                coverage.add("utrata_bez_poprawki")
        if tau_bind:
            z3, V, NOM, KONT, KREF, sv, inv, tau = model
            c = {"tm": z3.BoolVal(pre["tm"]), "rsn": z3.IntVal(pre["rsn"]), "st": z3.IntVal(pre["st"]), "ph": z3.IntVal(pre["ph"])}
            t, i, j, tr = sh._tau, sh._przedzial, sh._j_eff, sh._tryb_eff
            kviol = bool(sh._kont and t is not None and (t >= C["thr"] or i is None or sh._r_est > C["R"][tr][i][j]))
            pu = inp["pos_corr"] if mc["rama"] == "corr" else inp["pos"]
            tu = inp["target_corr"] if mc["rama"] == "corr" else inp["target"]
            nom = bool(sh._r_est > C["r_nom"] and KV.m_outward(pu, tu) > 0.0)
            geo = FM.geofence_violation(pu, inp["vel"], tu, C["r_e"], C["v_e"], C["v_max"], C["a_brake"])[0]
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
    """T0: NadirShield(nadir=0, nad2=1) ≡ KontShield(kont=1) i NadirShield(nadir=0, kont=0, nad2=1) ≡ PatrolShield (pełny dict)."""
    from r03.kont_shield import KontShield
    from r01.shield import PatrolShield
    pairs = [(_new_prod(hyst, nad2=True, nadir=False, kont=True), KontShield(kont_mode=True)),
             (_new_prod(hyst, nad2=True, nadir=False, kont=False), PatrolShield())]
    for a, b in pairs:
        b.reset()
        if hyst is not None:
            b.pos_hyst_ticks = hyst
        if latch is not None:
            a.latch_refuse(*latch); b.latch_refuse(*latch)
    for k, inp in enumerate(ticks):
        kw = dict(mode=inp.get("mode", M_PATROL), pos_flag=inp.get("pos_flag"), auth_ok=inp.get("auth_ok", True))
        kk = dict(kw, cs_gnss_pos=inp.get("cs_gnss_pos"), now=inp.get("now"), r_est=inp.get("r_est"))
        for idx, (a, b) in enumerate(pairs):
            da = a.step(k, inp["pos"], inp["vel"], inp["target"], **kk, t_fix=inp.get("t_fix"), kosz_j=inp.get("kosz"),
                        tryb=inp.get("tryb"), pos_corr=inp.get("pos_corr"), target_corr=inp.get("target_corr"))
            db = b.step(k, inp["pos"], inp["vel"], inp["target"], **(kk if idx == 0 else kw))
            if json.dumps(da, sort_keys=True, default=str) != json.dumps(db, sort_keys=True, default=str):
                return [{"k": k, "para": ["Nadir(0,nad2)≡Kont(1)", "Nadir(0,0,nad2)≡Patrol"][idx], "a": da, "b": db}]
    return []


def fuzz_episode(rng, C):
    long_ep = rng.random() < 0.1
    n = rng.randint(120, 320) if long_ep else rng.randint(1, 40)
    p_lost = rng.choice([0.05, 0.3, 0.7, 0.95])
    p_fix = rng.choice([0.0, 0.02, 0.3, 0.9])
    hyst = None if long_ep else rng.choice([None, 1, 2, 3, 5])
    now = rng.uniform(0.0, 5.0)
    big = rng.random() < 0.3
    lost = rng.random() < p_lost
    off = (rng.uniform(-9, 9), rng.uniform(-9, 9)) if rng.random() < 0.8 else (0.0, 0.0)
    ticks = []
    Rs = [C["R"][t][i][k] for t in TRYBY for i in range(NI) for k in range(NK)]
    for _ in range(n):
        if rng.random() < 0.15:
            lost = rng.random() < p_lost
        if rng.random() < 0.05:
            off = (rng.uniform(-9, 9), rng.uniform(-9, 9))
        cs = None if rng.random() < 0.03 else (not lost)
        ang = rng.uniform(0, 2 * math.pi)
        r = rng.choice([rng.uniform(0, 40), rng.uniform(22.0, 28.0), C["r_nom"] + rng.uniform(-0.05, 0.05),
                        rng.choice(Rs) + rng.uniform(-0.05, 0.05)])
        pc = (r * math.cos(ang), r * math.sin(ang), -rng.uniform(0, 25))
        pe = (pc[0] - off[0], pc[1] - off[1], pc[2])
        tc = (pc[0] + rng.uniform(-3, 3), pc[1] + rng.uniform(-3, 3), -rng.uniform(0, 25))
        te = (tc[0] - off[0], tc[1] - off[1], tc[2])
        tk = {"pos": pe, "pos_corr": pc, "vel": (rng.uniform(-4, 4), rng.uniform(-4, 4), rng.uniform(-2, 2)),
              "target": te, "target_corr": tc,
              "mode": rng.choices([M_PATROL, M_HOLD, M_RETURN, M_ABORT, M_OBSERVE], [0.8, 0.05, 0.05, 0.02, 0.08])[0],
              "pos_flag": None if rng.random() < 0.3 else (rng.random() < 0.08), "auth_ok": rng.random() < 0.8,
              "cs_gnss_pos": cs, "now": now}
        if rng.random() < 0.02:
            tk["pos_corr"] = None
        if rng.random() < p_fix:
            tk["t_fix"] = now - rng.choice([0.0, rng.uniform(0.0, 0.3), rng.uniform(-0.03, 0.0)])
            tk["kosz"] = rng.randrange(NK)
            tk["tryb"] = rng.choice(TRYBY + (None,))
        ticks.append(tk)
        now += rng.uniform(0.2, 1.5) if big else rng.choice([C["dt"], rng.uniform(0.0, 0.3)])
    return ticks, hyst


def build_grid(C):
    """Brzegi NAD2 (deterministycznie): przedziały τ (krawędź − ε, krawędź), próg τ*, bariera ±1 mm w każdym polu przy τ
    w środku przedziału, brak poprawki ⇒ (jeden, 4), przejście ramy NOMINAL→KONT→NOMINAL, zatrzask odporny na poprawkę,
    R-G-NOM w ramie poprawionej, priorytety."""
    deb, hyst, dt = C["debounce_ticks"], C["hyst_ticks"], C["dt"]
    eps = []
    OFF = (3.0, -2.0)

    def T(now, pc=(5.0, 0.0, -10.0), tc=None, cs=False, **kw):
        tc = pc if tc is None else tc
        return {"pos": [pc[0] - OFF[0], pc[1] - OFF[1], pc[2]], "pos_corr": list(pc), "target": [tc[0] - OFF[0], tc[1] - OFF[1], tc[2]],
                "target_corr": list(tc), "vel": [0.0, 0.0, 0.0], "cs_gnss_pos": cs, "now": now, **kw}

    def run(name, seq, hyst_override=None, latch=None):
        eps.append({"name": name, "hyst": hyst_override, "latch": latch, "ticks": seq})
    for tryb in TRYBY:
        for k in range(NK):
            for i in range(NI):
                mid = (C["kraw"][i] + (C["kraw"][i - 1] if i else 0.0)) / 2 - C["tau_eps"]
                mid = max(mid, 0.0)
                for off in (-0.001, 0.001):
                    r = C["R"][tryb][i][k] + off
                    p = (r, 0.0, -10.0)
                    run(f"bar_{tryb}_i{i}_k{k}_{'pod' if off < 0 else 'nad'}",
                        [T(0.0, p, t_fix=0.0, kosz=k, tryb=tryb), T(dt, p), T(mid, p)])
    for kr in C["kraw"]:
        for tt in (kr - C["tau_eps"] - 1e-4, kr - C["tau_eps"] + 1e-4):
            if 0 <= tt < C["thr"] + 0.2:
                run(f"kraw_{kr}_{tt:.4f}", [T(0.0, t_fix=0.0, kosz=2, tryb="para"), T(dt), T(tt)])
    for tend in (C["thr"] - dt, C["thr"] - 0.001, C["thr"], C["thr"] + 0.001):
        run(f"tau_star_{tend:.3f}", [T(0.0, t_fix=0.0, kosz=0, tryb="para"), T(dt), T(tend)])
    run("no_fix_worst", [T(0.0), T(dt), T(0.5), T(C["thr"] - 0.001), T(C["thr"])])
    run("no_fix_bar_worst", [T(0.0, (C["R"]["jeden"][0][4] + 0.001, 0.0, -10.0)), T(dt, (C["R"]["jeden"][0][4] + 0.001, 0.0, -10.0))])
    seq = [T(i * dt, cs=True, t_fix=0.0, kosz=0, tryb="para") for i in range(3)]
    seq += [T((3 + i) * dt) for i in range(deb + 1)]
    seq += [T((3 + deb + 1 + i) * dt, cs=True) for i in range(hyst + 1)]
    run("rama_nominal_kont_nominal", seq)
    run("latch_survives_fix", [T(0.0, t_fix=0.0, kosz=3, tryb="jeden"), T(dt), T(1.2), T(1.25, t_fix=1.25, kosz=0, tryb="para"), T(1.3)])
    for r in (C["r_nom"] - 0.01, C["r_nom"] + 0.01):
        for tgt, nm in (((r + 1.0, 0.0, -10.0), "out"), ((r - 1.0, 0.0, -10.0), "in"), ((r, 1.0, -10.0), "tan")):
            run(f"nom_kont_{r:.2f}_{nm}", [T(0.0, (r, 0.0, -10.0), tgt, t_fix=0.0, kosz=0, tryb="para"),
                                           T(dt, (r, 0.0, -10.0), tgt)])
            run(f"nom_nominal_{r:.2f}_{nm}", [T(0.0, (r, 0.0, -10.0), tgt, cs=True)])
    FAR = (45.0, 0.0, -10.0)
    run("prio_pos_over_kont", [T(x, pos_flag=True, t_fix=0.0, kosz=0, tryb="para") for x in (0.0, dt, 1.2)])
    run("prio_kont_over_geo", [T(0.0, t_fix=0.0, kosz=0, tryb="para"), T(dt), T(1.2, tc=FAR)])
    run("prio_latch_over_kont", [T(x) for x in (0.0, dt, 1.2)], latch=("STALE_CMD", "adm"))
    for md, auth in ((M_HOLD, True), (M_RETURN, True), (M_OBSERVE, True), (M_OBSERVE, False), (M_ABORT, True)):
        run(f"mode_utrata_{md}_{auth}", [T(0.0, mode=md, auth_ok=auth, t_fix=0.0, kosz=2, tryb="jeden"), T(dt, mode=md, auth_ok=auth)])
    run("brak_ramy_poprawionej", [dict(T(0.0, t_fix=0.0, kosz=1, tryb="para"), pos_corr=None), dict(T(dt), pos_corr=None)])
    return eps


# ---------------------------- fikstura S4 (nowa litera) ----------------------------
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


def s4_fixture(boot):
    """Wejścia nakładki z lotu S4 po ticku (rama.jsonl + tk + demo), od episode_start do pierwszego ticku zejścia; poprawki
    z replayu NOWEJ litery (Rama(litera="NAD2") na zapisanych klatkach nf, dostępność po mono przybycia + detekcja + 5 ms);
    pos = p_EKF, pos_corr = p_EKF + Δ′, cel EKF = sp_EKF, cel poprawiony = sp_EKF + Δ′ (N, E)."""
    import bisect
    from harness import nadir_fix as NF
    d = os.path.join(S4, boot)
    rama = sorted(_load(os.path.join(d, "rama.jsonl")), key=lambda r: r["tick"])
    tk = {r["tick"]: r for r in _load(os.path.join(d, "trace.jsonl"), "tk")}
    demo = {r["tick"]: r for r in _load(os.path.join(d, "demo.jsonl"))}
    rv = NF.Rama(litera="NAD2")
    fixy = []
    for r in _load(os.path.join(d, "nadir_obs.jsonl"), "nf"):
        if "fx" not in r:
            continue
        fx = rv.obserwacja(r["sim"], r["det"], r.get("ekf_q"), r.get("ekf_pos"))
        if fx["ok"]:
            fixy.append((r["mono"] + r.get("ms", 0.0) / 1000.0 + EPS_DOST, fx["t_frame"], fx["kosz"], fx["tryb"], list(rv.d_ne)))
    av = [f[0] for f in fixy]
    ticks = []
    for r in rama:
        if r["desc"]:
            break
        t, dm = tk.get(r["tick"]), demo.get(r["tick"])
        if t is None or dm is None:
            continue
        i = bisect.bisect_right(av, r["mono"]) - 1
        pe, se = r["p_ekf"], r["sp_ekf"]
        inp = {"pos": pe, "vel": dm["own_vel_ned"], "target": se, "mode": M_PATROL, "pos_flag": t["pf"], "auth_ok": True,
               "cs_gnss_pos": t["cs"], "now": r["sim"], "pos_corr": list(pe), "target_corr": list(se)}
        if i >= 0:
            _, tf, kk, tr, dne = fixy[i]
            inp["pos_corr"] = [pe[0] + dne[0], pe[1] + dne[1], pe[2]]
            inp["target_corr"] = [se[0] + dne[0], se[1] + dne[1], se[2]]
            inp["t_fix"], inp["kosz"], inp["tryb"] = tf, kk, tr
        ticks.append(inp)
    return ticks


class _RamaStub:
    def __init__(self):
        self.t_fix = self.kosz = self.tryb = None


def obligacja_wejscia(fixtures, mutant=False):
    """(b) + (c) na ścieżce drivera nad2_krok.krok. mutant=True: stara ścieżka (osłona bez pozycji poprawionej)."""
    sys.path.insert(0, os.path.join(ROOT, "results/NAD2/tools"))
    import nad2_krok
    wyn = {"ticki_utraty": 0, "ticki_nominal": 0, "r_est_zly": 0, "applied_zly": 0, "bramka_zla": 0, "max_dr": 0.0}
    for ticks in fixtures:
        sh = _new_prod()
        rama = _RamaStub()
        for k, inp in enumerate(ticks):
            if inp.get("t_fix") is not None:
                rama.t_fix, rama.kosz, rama.tryb = inp["t_fix"], inp["kosz"], inp["tryb"]
            own_net = inp["pos_corr"] if inp.get("pos_corr") is not None else inp["pos"]
            tgt_net = inp["target_corr"] if inp.get("target_corr") is not None else inp["target"]
            if mutant:
                d = sh.step(k, inp["pos"], inp["vel"], inp["target"], mode=M_PATROL, pos_flag=inp.get("pos_flag"),
                            cs_gnss_pos=inp.get("cs_gnss_pos"), now=inp.get("now"), t_fix=rama.t_fix, kosz_j=rama.kosz, tryb=rama.tryb)
                pb = inp["pos"]
            else:
                d, pb = nad2_krok.krok(sh, k, inp["pos"], own_net, inp["vel"], inp["target"], tgt_net, M_PATROL, inp.get("pos_flag"),
                                       inp.get("cs_gnss_pos"), inp.get("now"), None, rama)
            utrata = sh.kont_phase() != "NOMINAL"
            ref = own_net if utrata else inp["pos"]
            dr = abs(sh._r_est - math.hypot(float(ref[0]), float(ref[1])))
            wyn["max_dr"] = max(wyn["max_dr"], dr)
            wyn["ticki_utraty" if utrata else "ticki_nominal"] += 1
            wyn["r_est_zly"] += int(dr > 1e-6)
            n2 = d.get("nad2") or {}
            ar = n2.get("applied_rama")
            if ar is not None and d.get("applied") is not None:
                dn, de = (own_net[0] - inp["pos"][0], own_net[1] - inp["pos"][1]) if utrata else (0.0, 0.0)
                exp = [ar[0] - dn, ar[1] - de, ar[2]]
                wyn["applied_zly"] += int(max(abs(exp[q] - d["applied"][q]) for q in range(3)) > 1e-9)
            elif not mutant:
                wyn["applied_zly"] += 1
            wyn["bramka_zla"] += int(list(pb) != list(ref))
    wyn["max_dr"] = round(wyn["max_dr"], 9)
    wyn["PASS"] = wyn["r_est_zly"] == 0 and wyn["applied_zly"] == 0 and wyn["bramka_zla"] == 0 and wyn["ticki_utraty"] > 0
    return wyn


def przejscia_ramy(C):
    """Tick przejścia w obu kierunkach: pierwszy tick fazy KONT w ramie poprawionej, pierwszy tick po powrocie NOMINAL w EKF."""
    sys.path.insert(0, os.path.join(ROOT, "results/NAD2/tools"))
    import nad2_krok
    deb, hyst, dt = C["debounce_ticks"], C["hyst_ticks"], C["dt"]
    OFF = (4.0, -3.0)
    seq = [(True, 0.0)] * 3 + [(False, 0.0)] * (deb + 2) + [(True, 0.0)] * (hyst + 2)
    sh = _new_prod()
    rama = _RamaStub(); rama.t_fix, rama.kosz, rama.tryb = 0.0, 1, "para"
    prev, wej, wyj = "NOMINAL", [], []
    for k, (cs, _) in enumerate(seq):
        pc = [6.0, 1.0, -10.0]; pe = [pc[0] - OFF[0], pc[1] - OFF[1], pc[2]]
        rama.t_fix = k * dt
        d, pb = nad2_krok.krok(sh, k, pe, pc, [0, 0, 0], pe, pc, M_PATROL, None, cs, k * dt, None, rama)
        ph = sh.kont_phase()
        if prev == "NOMINAL" and ph != "NOMINAL":
            wej.append({"k": k, "rama": d["nad2"]["rama"], "r_est": sh._r_est, "r_corr": math.hypot(pc[0], pc[1])})
        if prev != "NOMINAL" and ph == "NOMINAL":
            wyj.append({"k": k, "rama": d["nad2"]["rama"], "r_est": sh._r_est, "r_ekf": math.hypot(pe[0], pe[1])})
        prev = ph
    ok = (len(wej) == 1 and wej[0]["rama"] == "corr" and abs(wej[0]["r_est"] - wej[0]["r_corr"]) < 1e-9 and
          len(wyj) == 1 and wyj[0]["rama"] == "ekf" and abs(wyj[0]["r_est"] - wyj[0]["r_ekf"]) < 1e-9)
    return ok, {"wejscie": wej, "wyjscie": wyj}


def prove_p5(fuzz_n=100000, tau_random=2000, seed0=0):
    C = mirror_consts()
    cov, mism, pt = set(), [], []
    n = {"grid": 0, "fuzz": 0, "fixture": 0, "tau": 0, "passthrough": 0}
    for e in build_grid(C):
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
    fixt = {}
    for b in CIECIA_S4 + NOM_S4:
        ticks = s4_fixture(b)
        fixt[b] = ticks
        mism += run_conformance_episode(ticks, C, None, cov, tau_bind=True)
        n["fixture"] += len(ticks); n["tau"] += len(ticks)
    wej = obligacja_wejscia(list(fixt.values()))
    mut = obligacja_wejscia([fixt[b] for b in CIECIA_S4], mutant=True)
    przej_ok, przej = przejscia_ramy(C)
    need = {"R-POS", "R-KONT", "R-G", "R-G-NOM", "R-A", "R-H", "R-R", "R-O", "R-AUTH", "R-P", "cause:τ*", "cause:bariera",
            "second_episode", "utrata_bez_poprawki", "rama:corr", "rama:ekf"} | \
           {f"pole:{t}_i{i}_k{k}" for t in TRYBY for i in range(NI) for k in range(NK)}
    missing = sorted(need - cov)
    mutant_wykryty = mut["r_est_zly"] > 0 or mut["bramka_zla"] > 0
    ok = not mism and not pt and not missing and wej["PASS"] and mutant_wykryty and przej_ok
    return ok, mism, pt, sorted(x for x in cov if x), missing, n, {"wejscie": wej, "mutant": mut, "mutant_wykryty": mutant_wykryty,
                                                                   "przejscia_ramy": przej, "przejscia_ok": przej_ok}


# ================================ C2 P1_nad2 =====================================
def prove_p1():
    return PN.prove_p1()


# ================================ C4 P7_nad2 =====================================
def prove_p7():
    th = FM.shield_thresholds()
    c = consts()
    deb, hyst = th["debounce_ticks"], th["hyst_ticks"]
    dt = Fraction(str(th["dt"]))
    x = (c["tau_star"] - T_MARGIN_TICKS * dt) / dt
    assert x.denominator == 1
    thr1 = int(x)
    pola = [(t, k) for t in TRYBY for k in range(NK)]
    jw = pola.index(("jeden", 4))
    thr = [thr1] * len(pola)
    res, chk = {"thr_ticks": thr1, "debounce": deb, "hyst": hyst, "pole_brak": "jeden_k4", "n_pol": len(pola)}, {}
    for f, (t, k) in enumerate(pola):
        init, nodes, edges = PN.build_graph(deb, hyst, thr, jw, (None, f))
        cj = PN._p7_checks(nodes, edges, deb, hyst, thr, jw)
        res[f"graf_{t}_k{k}"] = {"n_states": len(nodes), "n_edges": len(edges)}
        chk.update({f"{t}_k{k}_{kk}": v for kk, v in cj.items()})
    rthr = [6] * len(pola)
    init, nodes, edges = PN.build_graph(2, 3, rthr, jw, (None,) + tuple(range(len(pola))))
    cr = PN._p7_checks(nodes, edges, 2, 3, rthr, jw)
    res["zredukowana"] = {"deb": 2, "hyst": 3, "thr": 6, "n_states": len(nodes), "n_edges": len(edges)}
    chk.update({f"red_{k}": v for k, v in cr.items()})
    z = PN._p7_z3(deb, hyst, [thr1] * 4, 3)
    return all(chk.values()) and all(v == "unsat" for v in z.values()), res, chk, z


# =================================== CLI =====================================
def _write(name, cert):
    p = os.path.join(CERTS, name)
    if os.path.exists(p):
        old = json.load(open(p))
        print(f"  {name} istnieje — zgodność sha: {'TAK' if old.get('model_sha256') == cert['model_sha256'] else 'NIE'}")
    json.dump(cert, open(p, "w"), indent=2, ensure_ascii=False)
    print(f"  zapisano {p}")


A_NAD2 = ("A-nad2 (PRE_NAD2 §4, ANEKS_NAD2-1 §2): |p_corr − GT(czas próbki EKF)| ≤ U(przedział osłony, koszyk, tryb) poziomo, "
          "U = 1.5·(F + G) z danych S4 (kanon czasu timestamp_sample); oraz r_est osłony = |p_corr| (obligacja wejścia P5_nad2 (b)). "
          "Walidowane w bramce S3 jako (B1) i (B3); naruszenie = FAIL nogi.")


def main_p9():
    import z3
    ok, per, arith, opis, c = prove_p9()
    print("=== P9_nad2: zawieranie z tabelą U (z3, per pole przedział × koszyk × tryb) ===")
    bad = {k: v for k, v in per.items() if not (v["main"] == "unsat" and all(v[x] == "sat" for x in v if x != "main"))}
    print(f"  obligacji: {len(per)}, niespełnionych: {len(bad)} {list(bad)[:5]}\n  arytmetyka: {arith}\n  opisowo: {opis}")
    print(f"WERDYKT P9_nad2: {'PROVED' if ok else 'UNPROVEN'}")
    if not ok:
        sys.exit(1)
    _write("P9_nad2.json", {
        "property": "P9_nad2", "verdict": "PROVED",
        "method": "z3 LRA per pole (przedział τ 0…4 × koszyk 0…4 × tryb para|jeden) + ostrość trójstronna (U, R, Δ_D5)",
        "z3_lib": z3.get_version_string(), "obligations": per, "arithmetic": arith, "opisowo": opis,
        "theorem": "∀ pole: 0≤r_est≤R ∧ 0≤ε≤U ∧ 0≤Δ≤Δ_D5 ∧ 0≤s≤d_stop ∧ |r_c−r_est|≤ε ∧ r_d≤r_est+ε+s+Δ ⇒ r_c≤R_E ∧ r_d≤R_E; "
                   "R = R_E − d_stop − U − Δ_D5, U = 1.5·(F(koszyk, tryb) + G(przedział)); ostrość: każda z trzech wielkości +δ łamie",
        "constants": {"freeze": "results/KONT/s2/s2_freeze_bf.json", "freeze_sha256": c["sha256"],
                      "tabela": "results/NAD2/s1/freeze_U.json", "tabela_check": c["tabela_check"],
                      "F": {t: [str(x) for x in c["F"][t]] for t in TRYBY}, "G": [str(x) for x in c["G"]],
                      "krawedzie": [str(x) for x in c["kraw"]], "zapas": str(c["zapas"]), "tau_star": str(c["tau_star"]),
                      "tau_eps": str(c["tau_eps"]), "R_E": str(c["r_e"]), "d_stop": str(c["d_stop"]), "delta_D5": str(c["delta"]),
                      "m_p50": str(c["m_p50"])},
        "assumptions": [A_NAD2,
                        "A-react (R0.1): przemieszczenie od ostatniego ALLOW do zatrzymania ≤ d_stop (r01/config.py:24-27).",
                        "A-D5 (ANEKS_KONT-3): dryf zejścia ≤ Δ_D5 od REFUSE do przyziemienia.",
                        "Brak poprawki od wejścia w utratę ⇒ pole (jeden, koszyk 4), τ od zera zegara utraty.",
                        "Przedział τ wybiera osłona z τ + 0.012 s; (B1) sądzi wobec U przedziału użytego przez osłonę (ANEKS_NAD2-1 §2.4)."],
        "code_refs": {"bariera": "r03/nadir_shield.py:NadirShield._nad2_barrier, r_nad2, przedzial_nad2",
                      "rama": "r03/nadir_shield.py:NadirShield._step_nad2", "driver": "results/NAD2/tools/nad2_krok.py:krok",
                      "litera": "harness/nadir_fix.py:Rama (litera NAD2)", "prover": "r01/proofs/p9_nad2_verify.py"},
        "model_sha256": _self_sha()})


def main_p1():
    import z3
    res, n_leaves = prove_p1()
    ok = all(v == "unsat" for v in res.values())
    print("=== P1_nad2: automat nakładki (z3, 1-indukcja) + wyłączność liści ===")
    for k, v in res.items():
        print(f"  {k}: {v}" + ("  ✓" if v == "unsat" else "  !! (SPODZIEWANO unsat)"))
    print(f"WERDYKT P1_nad2: {'PROVED' if ok else 'UNPROVEN'}")
    if not ok:
        sys.exit(1)
    _write("P1_nad2.json", {
        "property": "P1_nad2", "verdict": "PROVED",
        "method": "1-induction (z3) + NRA (nom_applied) + wyłączność/wyczerpanie liści (model = p9_kont_verify._p1_model)",
        "z3_lib": z3.get_version_string(), "obligations": res, "leaves": n_leaves,
        "automaton": "r03/nadir_shield.py:NadirShield (NADIR_MODE=1, nad2) — _decide = KontShield._decide (nietknięty); "
                     "latch > R-POS > R-KONT(tabela U) > R-G > abort > hold > return > R-G-NOM > {OBSERVE∧auth | R-AUTH} > patrol; "
                     "kviol = τ ≥ τ* − 2·dt ∨ przedział poza tabelą ∨ r_est(rama wybrana) > R(przedział, koszyk, tryb)",
        "model_source": {"file": "r01/proofs/p9_kont_verify.py:_p1_model/prove_p1 (READ-ONLY)",
                         "sha256": hashlib.sha256(open(KV.__file__, "rb").read()).hexdigest()},
        "assumptions": ["geo/pos_bad/kflag/kviol/nom = predykaty liczone w kodzie w ramie wybranej; arytmetyka tabeli = P9_nad2, "
                        "monitor + zegar τ = P7_nad2, zgodność kod↔model = P5_nad2 (tau_bind na fiksturze S4 i fuzzie)."],
        "model_sha256": _self_sha()})


def main_p7():
    ok, res, chk, z = prove_p7()
    print("=== P7_nad2: graf monitora GNSS + zegara τ (enumeracja, per pole) ===")
    print(f"  {res}\n  checks fail: {[k for k, v in chk.items() if not v]}\n  z3: {z}")
    print(f"WERDYKT P7_nad2: {'PROVED' if ok else 'UNPROVEN'}")
    if not ok:
        sys.exit(1)
    _write("P7_nad2.json", {
        "property": "P7_nad2", "verdict": "PROVED",
        "method": "wyczerpująca enumeracja osiągalnego grafu (BFS, stałe produkcji) monitora GNSS + zegara τ na LUSTRZE "
                  "(p9_nadir_verify.build_graph/_p7_checks, READ-ONLY), osobno dla każdego z 10 pól (tryb × koszyk); próg "
                  "τ* − 2·dt = 19 ticków; instancja zredukowana z pełnym przełączaniem pól; z3-duplikat kroku",
        "obligations": res, "checks": chk, "z3_duplicate": z,
        "theorem": "(a) wejście w utratę tylko na fladze po debounce; (b) brak ALLOW w utracie przy τ ≥ 0.95 s, REFUSE dokładnie przy "
                   "progu; (c) wyjście tylko po hyst zdrowych tickach, czyści zatrzask; (d) zatrzask trwa w utracie także po nowej "
                   "poprawce; (e) poprawka zeruje τ i ustawia pole; (f) REFUSE z bariery osiągalny w każdym wieku < progu; (g) brak "
                   "poprawki ⇒ pole (jeden, 4)",
        "model_sha256": _self_sha()})


def main_p5():
    import z3
    ok, mism, pt, cov, missing, n, ob = prove_p5()
    print("=== P5_nad2: konformancja lustro ≡ produkcja, tau ≡ produkcja, obligacja wejścia, passthrough T0 ===")
    print(f"  ticki: {n}  rozbieżności: {len(mism)}  passthrough: {len(pt)}  brak pokrycia: {missing}")
    print(f"  obligacja wejścia: {ob['wejscie']}\n  mutant (stara ścieżka): {ob['mutant']} wykryty={ob['mutant_wykryty']}")
    print(f"  przejścia ramy: {ob['przejscia_ok']} {ob['przejscia_ramy']}")
    for x in (mism[:1] + pt[:1]):
        print("  PIERWSZA ROZBIEŻNOŚĆ:", json.dumps(x, default=str, ensure_ascii=False)[:2500])
    print(f"WERDYKT P5_nad2: {'PASS' if ok else 'FAIL'}")
    if not ok:
        sys.exit(1)
    _write("P5_nad2.json", {
        "property": "P5_nad2", "verdict": "PASS",
        "method": "per-tick konformancja: lustro NAD2 (mirror_step_nad2) ≡ r03/nadir_shield.NadirShield (nadir_mode=1, nad2) "
                  "(decyzja, powód, reguła, stan, applied w ramie EKF, detail, akcja, faza, t_KONT, τ, pole, przedział, rama, r_est) "
                  "+ tau_kont (P1) ≡ produkcja; obligacja wejścia na ścieżce drivera (nad2_krok.krok) z mutantem; przejścia ramy; "
                  "passthrough NADIR_MODE=0 ≡ KontShield i ≡ PatrolShield pełnym dictem",
        "z3_lib": z3.get_version_string(), "ticks": n, "mismatches": 0, "passthrough_mismatches": 0, "coverage": cov,
        "fixture_s4": {"boots": list(CIECIA_S4 + NOM_S4), "rekonstrukcja": "s4_fixture: rama.jsonl + tk + demo; poprawki z replayu "
                       "Rama(litera=NAD2), dostępność mono + detekcja + 5 ms"},
        "obligacja_wejscia": ob["wejscie"], "mutant_stara_sciezka": ob["mutant"], "mutant_wykryty": ob["mutant_wykryty"],
        "przejscia_ramy": ob["przejscia_ramy"], "fuzz": {"episodes": 100000, "seed": 0, "tau_bound_episodes": 2000,
                                                          "passthrough_episodes": 25000},
        "binds": "P1_nad2 (tau_kont), P7_nad2 (lustro monitora i zegara τ), P9_nad2 (założenie r_est = |p_corr|)",
        "model_sha256": _self_sha()})


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    for name, fn in (("p9", main_p9), ("p1", main_p1), ("p7", main_p7), ("p5", main_p5)):
        if cmd in (name, "all"):
            fn()


if __name__ == "__main__":
    main()
