"""r01/proofs/p9_nad3_verify.py — certy nogi NADIR-III: P9_nad3, P7_nad3, P5_nad3 (PROMPT_NAD3_S1 §3, PRE_NAD3 §4–§5). NOWY plik;
provery i certy NAD2 / NADIR-I / KONT / kanon NIETKNIĘTE (r01/proofs/p9_nad2_verify.py — lustro NAD2, siatka, fuzz, rdzenie
porównania; p9_nadir_verify.py — graf P7; p9_kont_verify.py; fv_mirror.py — importowane READ-ONLY). Każdy cert zapisuje
model_sha256 = sha256(tego pliku).

=== PREREJESTRACJA OBLIGACJI (przed pierwszym biegiem) ===
Tabela jako PARAMETR: trzy tabele FREEZE results/NAD3/s1/freeze_U_P{1,2,3}.json (E = 1.00 / 1.75 / 2.75 m), wczytywane przez
r03/nadir_shield.nad3_tabela (sha256 kanonicznego JSON = pole pliku = suma z FREEZE). Stałe R_E / d_stop / Δ_D5 / m_p50 z
s2_freeze_bf.json (KV.load_freeze) — tabela musi je powtarzać. Arytmetyka wymiernie (Fraction). Pole = (przedział i ∈ 0…4,
koszyk k ∈ 0…4, tryb ∈ {para, jeden}); U′(i,k,t) = zapas·(F(k,t) + E + G(i)); R(i,k,t) = R_E − d_stop − U′ − Δ_D5.
C1 P9_nad3 (z3, LRA), dla KAŻDEJ tabeli i KAŻDEGO pola (3 × 50 obligacji):
  M (oczek. unsat): 0 ≤ r_est ≤ R ∧ 0 ≤ ε ≤ U′ ∧ 0 ≤ Δ ≤ Δ_D5 ∧ 0 ≤ s ≤ d_stop ∧ |r_c − r_est| ≤ ε ∧ r_d ≤ r_est + ε + s + Δ
       ∧ ¬(r_c ≤ R_E ∧ r_d ≤ R_E); ostrość (oczek. sat, δ = 1/1000): ε = U′+δ; r_est = R+δ; Δ = Δ_D5+δ.
  ZAŁOŻENIE: |p_corr′ − GT| ≤ U′(przedział osłony, koszyk, tryb) (p_corr′ = rama po degradacji, E wliczone) ORAZ r_est osłony
  = |p_corr′| (obligacja wejścia P5_nad3).
  Arytmetyka (asercje): tabela wczytana przez osłonę (sha); τ* = ostatnia krawędź; (τ* − 2·dt)/dt całkowite = próg tabeli
  (21); próg + dodatek ≤ ostatnia krawędź (przedział zawsze zdefiniowany w ALLOW); krawędzie rosnące; R nierosnąca w i oraz
  w k (dla każdego trybu); pole przy braku poprawki (jeden, 4) ma największe U′ w każdym przedziale; dt = 1/20; u_nad3
  produkcji = wymierne do 1e-9. ZAPISYWANE, NIE WYMAGANE: wykonalność u′ ≤ m(r_zad = 20 m) we wszystkich polach (oczekiwane
  P1 prawda, P2 prawda, P3 fałsz — zgodność z polem `wykonalne` tabeli jest asercją).
C4 P7_nad3: wyczerpująca enumeracja grafu monitora GNSS + zegara τ (PN.build_graph/_p7_checks, READ-ONLY) z progiem z tabeli
  (21 ticków; wspólny dla trzech tabel — asercja), osobno dla każdego z 10 pól; instancja zredukowana; z3-duplikat kroku.
C3 P5_nad3: (a) konformancja LUSTRO (p9_nad2_verify.mirror_step_nad2 ze stałymi z tabeli) ≡ produkcja (r03/nadir_shield.
  NadirShield nadir_mode=1, nad3, tabela) per tabela na: siatce brzegów (p9_nad2_verify.build_grid z τ* i krawędziami tabeli),
  fuzzie (p9_nad2_verify.fuzz_episode, ≥ 3 × 34 000 epizodów), fiksturze 13 lotów NAD2 z degradacją punktu (bias na zewnątrz
  i do środka; poprawki z replayu producenta Rama NAD2 → harness/nad3_degrad); tau_kont (P1) ≡ produkcja na siatce i 1000
  epizodach fuzzu na tabelę; 0 rozbieżności, pełne pokrycie reguł, przyczyn, ram i pól.
  (b) OBLIGACJA WEJŚCIA na ścieżce drivera (results/NAD3/tools/nad3_krok.krok) na fiksturze: r_est osłony = |p_corr′| (do 1e-6 m)
  w 100% ticków utraty, = |p_EKF| w NOMINAL; MUTANT podający osłonie pozycję CZYSTĄ (p_EKF + Δ bez degradacji) wykryty.
  (c) przejścia ramy NOMINAL→KONT→NOMINAL na nad3_krok. Passthrough: NadirShield(nadir_mode=0, nad3=True) ≡ KontShield.
OSTROŚĆ (każdy cert): mutant tabeli (sha przeliczona — zmiana semantyczna, nie zapisu) odrzucony: P9 — τ* ≠ ostatnia krawędź,
  G nierosnące; P7 — τ* bez całkowitego progu, próg tabeli ≠ (τ* − 2·dt)/dt; P5 — przesunięta krawędź τ w produkcji wobec
  lustra (rozbieżność konformancji).

Uruchom: PYTHONPATH=.certdeps:. python3 -m r01.proofs.p9_nad3_verify p9|p7|p5|all
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
import os
import random
import sys
import tempfile
from fractions import Fraction

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(_HERE))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from r01.proofs import fv_mirror as FM                              # READ-ONLY
from r01.proofs import p9_kont_verify as KV                         # READ-ONLY
from r01.proofs import p9_nadir_verify as PN                        # READ-ONLY (graf P7)
from r01.proofs import p9_nad2_verify as N2                         # READ-ONLY (lustro NAD2, siatka, fuzz, rdzenie)

CERTS = os.path.join(_HERE, "certs")
PRE = os.path.join(ROOT, "PRE_NAD3.md")
PRE_SHA = "56a1ac4396630d41b5e87f1161e090097b8b5f39d2a4ade793664a13c06a37da"
TABELE = {p: os.path.join(ROOT, f"results/NAD3/s1/freeze_U_{p}.json") for p in ("P1", "P2", "P3")}
WYKONALNE_OCZ = {"P1": True, "P2": True, "P3": False}
R_ZAD = Fraction(20)
TRYBY, NI, NK = N2.TRYBY, N2.NI, N2.NK
T_MARGIN_TICKS = KV.T_MARGIN_TICKS
M_PATROL = N2.M_PATROL
FUZZ_N, TAU_FUZZ = 34000, 1000


def _self_sha():
    return hashlib.sha256(open(__file__, "rb").read()).hexdigest()


def _sha_pliku(p):
    return json.load(open(p))["sha256_tabeli"]


def consts(path, sha=None):
    """Stałe tabeli (wymiernie) + wczytanie przez osłonę (sha); rzuca NadirStartError przy niezgodności."""
    from r03 import nadir_shield as NS
    c = KV.load_freeze()
    T = NS.nad3_tabela(path, sha or _sha_pliku(path))
    t = json.load(open(path))["tabela"]
    fr = lambda x: Fraction(str(x))
    c.update(G=[fr(x) for x in t["G"]], F={tr: [fr(x) for x in t["F"][tr]] for tr in TRYBY}, kraw=[fr(x) for x in t["krawedzie_tau_s"]],
             zapas=fr(t["zapas"]), E=fr(t["E"]), tau_star=fr(t["tau_star_s"]), tau_eps=fr(t["tau_eps_s"]), prog=int(t["prog_zatrzasku_ticki"]),
             T=T, path=path, tab_sha=T["sha"], tab_stale={"R_E": fr(t["R_E"]), "d_stop": fr(t["d_stop"]), "delta": fr(t["delta_D5"])})
    return c


def U_of(c, i, k, t):
    return c["zapas"] * (c["F"][t][k] + c["E"] + c["G"][i])


def R_of(c, i, k, t):
    return c["r_e"] - c["d_stop"] - U_of(c, i, k, t) - c["delta"]


# ================================ C1 P9_nad3 =====================================
def arytmetyka(c):
    from r01.config import DT as CFG_DT
    from r03 import nadir_shield as NS
    dt = Fraction(1, 20)
    thr = c["tau_star"] - T_MARGIN_TICKS * dt
    m_zad = c["r_e"] - c["d_stop"] - R_ZAD
    return {
        "stale_tabeli_eq_freeze": c["tab_stale"] == {"R_E": c["r_e"], "d_stop": c["d_stop"], "delta": c["delta"]},
        "kraw_rosnace": all(a < b for a, b in zip(c["kraw"], c["kraw"][1:])),
        "R_nonincreasing_in_i": all(R_of(c, i + 1, k, t) <= R_of(c, i, k, t) for t in TRYBY for k in range(NK) for i in range(NI - 1)),
        "R_nonincreasing_in_k": all(R_of(c, i, k + 1, t) <= R_of(c, i, k, t) for t in TRYBY for i in range(NI) for k in range(NK - 1)),
        "tau_star_eq_last_edge": c["tau_star"] == c["kraw"][-1],
        "dt_is_1_20": Fraction(str(CFG_DT)) == dt,
        "thr_plus_eps_le_last_edge": thr + c["tau_eps"] <= c["kraw"][-1],
        "thr_ticks_integer_eq_prog": (thr / dt).denominator == 1 and int(thr / dt) == c["prog"] == 21,
        "pole_brak_max_U_each_i": all(U_of(c, i, 4, "jeden") == max(U_of(c, i, k, t) for t in TRYBY for k in range(NK)) for i in range(NI)),
        "pole_brak_eq_shield": NS.POLE_BRAK_NAD2 == ("jeden", 4),
        "shield_u_eq_rational": all(abs(Fraction(str(NS.u_nad3(c["T"], i, k, t))) - (U_of(c, i, k, t) + c["delta"])) <= Fraction(1, 10 ** 9)
                                    for t in TRYBY for i in range(NI) for k in range(NK)),
    }, all(U_of(c, i, k, t) + c["delta"] <= m_zad for t in TRYBY for i in range(NI) for k in range(NK))


def prove_p9_tab(c):
    import z3
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
    arith, wyk = arytmetyka(c)
    ok_z3 = all(v["main"] == "unsat" and all(v[x] == "sat" for x in ("sharp_U", "sharp_R", "sharp_delta")) for v in per.values())
    return ok_z3 and all(arith.values()), per, arith, wyk


def mutant_tabeli(path, zmiana, nazwa):
    """Mutant semantyczny: kopia tabeli ze zmianą i PRZELICZONĄ sumą (zapis zgodny, treść zmieniona) — plik tymczasowy."""
    from r03 import nadir_shield as NS
    doc = copy.deepcopy(json.load(open(path)))
    zmiana(doc["tabela"])
    doc["sha256_tabeli"] = NS.tabela_sha(doc["tabela"])
    d = tempfile.mkdtemp(prefix="nad3_mutant_")
    p = os.path.join(d, f"{nazwa}.json")
    json.dump(doc, open(p, "w"), ensure_ascii=False, indent=1)
    return p


def ostrosc_p9():
    """Mutanty tabeli P1: τ* = 1.10 (≠ ostatnia krawędź), G[2] > G[3] (R rosnąca w i). Odrzucenie = osłona odmawia startu
    (NadirStartError) albo prover zwraca UNPROVEN."""
    from r03 import nadir_shield as NS
    out = {}

    def g_nierosnace(t):
        t["G"][2], t["G"][3] = t["G"][3], t["G"][2]
    for nm, z in (("tau_star_1_10", lambda t: t.update(tau_star_s=1.10)), ("G_nierosnace", g_nierosnace)):
        p = mutant_tabeli(TABELE["P1"], z, nm)
        try:
            ok = prove_p9_tab(consts(p))[0]
            out[nm] = {"odrzucony": not ok, "przez": "prover UNPROVEN" if not ok else None}
        except NS.NadirStartError as e:
            out[nm] = {"odrzucony": True, "przez": f"osłona kod {e.kod}"}
    return out


# ================================ C4 P7_nad3 =====================================
def prove_p7():
    th = FM.shield_thresholds()
    deb, hyst = th["debounce_ticks"], th["hyst_ticks"]
    dt = Fraction(str(th["dt"]))
    progi = {}
    for p, path in TABELE.items():
        c = consts(path)
        x = (c["tau_star"] - T_MARGIN_TICKS * dt) / dt
        assert x.denominator == 1 and int(x) == c["prog"], (p, x)
        progi[p] = int(x)
    assert len(set(progi.values())) == 1
    thr1 = progi["P1"]
    pola = [(t, k) for t in TRYBY for k in range(NK)]
    jw = pola.index(("jeden", 4))
    thr = [thr1] * len(pola)
    res, chk = {"thr_ticks": thr1, "progi_tabel": progi, "debounce": deb, "hyst": hyst, "pole_brak": "jeden_k4", "n_pol": len(pola)}, {}
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
    return all(chk.values()) and all(v == "unsat" for v in z.values()) and thr1 == 21, res, chk, z


def ostrosc_p7():
    """Mutanty: τ* = 1.12 (próg niecałkowity), τ* = 1.20 przy progu tabeli 21 (próg ≠ (τ* − 2·dt)/dt)."""
    from r03 import nadir_shield as NS
    out = {}
    for nm, z in (("tau_star_1_12", lambda t: t.update(tau_star_s=1.12, krawedzie_tau_s=t["krawedzie_tau_s"][:-1] + [1.12])),
                  ("tau_star_1_20_prog_21", lambda t: t.update(tau_star_s=1.20, krawedzie_tau_s=t["krawedzie_tau_s"][:-1] + [1.20]))):
        p = mutant_tabeli(TABELE["P1"], z, nm)
        try:
            c = consts(p)
            x = (c["tau_star"] - T_MARGIN_TICKS * Fraction(1, 20)) / Fraction(1, 20)
            out[nm] = {"odrzucony": not (x.denominator == 1 and int(x) == c["prog"] == 21), "przez": "asercja progu P7"}
        except NS.NadirStartError as e:
            out[nm] = {"odrzucony": True, "przez": f"osłona kod {e.kod}"}
    return out


# ================================ C3 P5_nad3 =====================================
def mirror_consts(c):
    th = FM.shield_thresholds()
    R = {t: [[float(R_of(c, i, k, t)) for k in range(NK)] for i in range(NI)] for t in TRYBY}
    return {**th, "thr": float(c["tau_star"]) - T_MARGIN_TICKS * th["dt"], "kraw": [float(x) for x in c["kraw"]],
            "tau_eps": float(c["tau_eps"]), "R": R, "r_nom": float(c["r_nom"])}


def _new_prod(path, sha, hyst=None):
    from r03.nadir_shield import NadirShield
    sh = NadirShield(kont_mode=True, nadir_mode=True, nad3=True, tabela=path, tabela_sha=sha)
    sh.reset()
    if hyst is not None:
        sh.pos_hyst_ticks = hyst
    return sh


def run_conformance_episode(ticks, C, prod, hyst=None, coverage=None, tau_bind=False, latch=None):
    """= p9_nad2_verify.run_conformance_episode z produkcją nad3 (prod: () → NadirShield) — kształt 1:1."""
    from r01.proofs.conformance import RSN_ID, STATE_ID, MODE_ID, DEC_ID
    sh = prod()
    if hyst is not None:
        sh.pos_hyst_ticks = hyst
    Cm = dict(C)
    if hyst is not None:
        Cm["hyst_ticks"] = hyst
    st = N2.new_mirror_state()
    if latch is not None:
        sh.latch_refuse(*latch); st["terminal"] = latch; st["state"] = "DONE"
    model = KV._p1_model() if tau_bind else None
    phid = {"NOMINAL": 0, "KONT": 1, "KONT_REFUSE": 2}
    for k, inp in enumerate(ticks):
        pre = {"tm": sh.terminal is not None, "rsn": RSN_ID[sh.terminal[0]] if sh.terminal is not None else 0,
               "st": STATE_ID[sh.state], "ph": phid[sh.kont_phase()]}
        d = N2._step_prod(sh, k, inp)
        m = N2.mirror_step_nad2(st, k, inp, Cm)
        pc, mc = N2.prod_core(d, sh), N2.mir_core(m)
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


def passthrough_episode(ticks, path, sha, hyst=None):
    """NadirShield(nadir_mode=0, nad3=True, tabela) ≡ KontShield(kont=1) pełnym dictem (reżim nad3 tylko w NADIR)."""
    from r03.kont_shield import KontShield
    from r03.nadir_shield import NadirShield
    a = NadirShield(kont_mode=True, nadir_mode=False, nad3=True, tabela=path, tabela_sha=sha); a.reset()
    b = KontShield(kont_mode=True); b.reset()
    if hyst is not None:
        a.pos_hyst_ticks = b.pos_hyst_ticks = hyst
    for k, inp in enumerate(ticks):
        kk = dict(mode=inp.get("mode", M_PATROL), pos_flag=inp.get("pos_flag"), auth_ok=inp.get("auth_ok", True),
                  cs_gnss_pos=inp.get("cs_gnss_pos"), now=inp.get("now"), r_est=inp.get("r_est"))
        da = a.step(k, inp["pos"], inp["vel"], inp["target"], **kk, t_fix=inp.get("t_fix"), kosz_j=inp.get("kosz"),
                    tryb=inp.get("tryb"), pos_corr=inp.get("pos_corr"), target_corr=inp.get("target_corr"))
        db = b.step(k, inp["pos"], inp["vel"], inp["target"], **kk)
        if json.dumps(da, sort_keys=True, default=str) != json.dumps(db, sort_keys=True, default=str):
            return [{"k": k, "a": da, "b": db}]
    return []


def fikstura(punkt, kierunek):
    """13 lotów NAD2: wejścia ticku z zapisu (p_EKF, sp_EKF, prędkość, cs, pf, sim) + stan ramy po degradacji punktu; zwraca
    listę (ticki, ticki_czyste) — czyste = ta sama rama bez degradacji (wejście mutanta)."""
    sys.path[:0] = [os.path.join(ROOT, "results/NAD3/tools"), os.path.join(ROOT, "results/NAD3_RECON/tools")]
    import nad3_dane as ND
    import nad3_w1 as W1
    from harness import nad3_degrad as DG
    E = json.load(open(TABELE[punkt]))["tabela"]["E"]
    out = []
    for n, d, kom in ND.loty():
        L = ND.wczytaj(n, d, kom)
        strumien, pw = W1.producent(L, None)
        assert pw["niezgodne"] == 0
        dg = DG.Degradacja({"model": "bias_rad", "kierunek": kierunek, "E_max": E, "f": 1, "K": 0, "ziarno": 1})
        deg = {s: dg.przetworz(strumien[s]) for s in sorted(strumien)}
        tk = {r["tick"]: r for r in ND.jl(L.d, "trace.jsonl", "tk")}
        demo = {r["tick"]: r for r in ND.jl(L.d, "demo.jsonl")}
        for wersja in (deg, strumien):
            seqs, ip = sorted(wersja), 0
            dne, tf, kz, tr = [0.0, 0.0], None, None, None
            ticks = []
            for r in L.rama:
                while ip < len(seqs) and seqs[ip] <= r["seq"]:
                    m = wersja[seqs[ip]]
                    dne, tf = list(m["d_ne"]), m["t_fix"]
                    if m.get("ok"):
                        kz, tr = m.get("kosz"), m.get("tryb")
                    ip += 1
                t, dm = tk[r["tick"]], demo[r["tick"]]
                pe, se = r["p_ekf"], r["sp_ekf"]
                inp = {"pos": pe, "vel": dm["own_vel_ned"], "target": se, "mode": M_PATROL, "pos_flag": t["pf"], "auth_ok": True,
                       "cs_gnss_pos": t["cs"], "now": r["sim"], "pos_corr": [pe[0] + dne[0], pe[1] + dne[1], pe[2]],
                       "target_corr": [se[0] + dne[0], se[1] + dne[1], se[2]]}
                if tf is not None and kz is not None:
                    inp["t_fix"], inp["kosz"], inp["tryb"] = tf, kz, tr
                ticks.append(inp)
            out.append(ticks)
    return [(out[2 * q], out[2 * q + 1]) for q in range(len(out) // 2)]


class _RamaStub:
    def __init__(self):
        self.t_fix = self.kosz = self.tryb = None


def obligacja_wejscia(pary, path, sha, mutant=False):
    """(b) na ścieżce drivera nad3_krok.krok: r_est = |p_corr′| w utracie, = |p_EKF| w NOMINAL. mutant=True: osłona dostaje
    pozycję i cel w ramie CZYSTEJ (bez degradacji) — wymaganie liczone wobec p_corr′."""
    sys.path.insert(0, os.path.join(ROOT, "results/NAD3/tools"))
    import nad3_krok
    wyn = {"ticki_utraty": 0, "ticki_nominal": 0, "r_est_zly": 0, "applied_zly": 0, "bramka_zla": 0, "max_dr": 0.0}
    for ticks, czyste in pary:
        sh = _new_prod(path, sha)
        rama = _RamaStub()
        for k, (inp, cz) in enumerate(zip(ticks, czyste)):
            src = cz if mutant else inp
            if src.get("t_fix") is not None:
                rama.t_fix, rama.kosz, rama.tryb = src["t_fix"], src["kosz"], src["tryb"]
            d, pb = nad3_krok.krok(sh, k, src["pos"], src["pos_corr"], src["vel"], src["target"], src["target_corr"], M_PATROL,
                                   src.get("pos_flag"), src.get("cs_gnss_pos"), src.get("now"), None, rama)
            utrata = sh.kont_phase() != "NOMINAL"
            ref = inp["pos_corr"] if utrata else inp["pos"]
            dr = abs(sh._r_est - math.hypot(float(ref[0]), float(ref[1])))
            wyn["max_dr"] = max(wyn["max_dr"], dr)
            wyn["ticki_utraty" if utrata else "ticki_nominal"] += 1
            wyn["r_est_zly"] += int(dr > 1e-6)
            n2 = d.get("nad2") or {}
            ar = n2.get("applied_rama")
            if ar is not None and d.get("applied") is not None:
                own = src["pos_corr"]
                dn, de = (own[0] - src["pos"][0], own[1] - src["pos"][1]) if utrata else (0.0, 0.0)
                exp = [ar[0] - dn, ar[1] - de, ar[2]]
                wyn["applied_zly"] += int(max(abs(exp[q] - d["applied"][q]) for q in range(3)) > 1e-9)
            else:
                wyn["applied_zly"] += 1
            wyn["bramka_zla"] += int(list(pb) != list(ref))
    wyn["max_dr"] = round(wyn["max_dr"], 9)
    wyn["PASS"] = wyn["r_est_zly"] == 0 and wyn["applied_zly"] == 0 and wyn["bramka_zla"] == 0 and wyn["ticki_utraty"] > 0
    return wyn


def przejscia_ramy(C, path, sha):
    sys.path.insert(0, os.path.join(ROOT, "results/NAD3/tools"))
    import nad3_krok
    deb, hyst, dt = C["debounce_ticks"], C["hyst_ticks"], C["dt"]
    OFF = (4.0, -3.0)
    seq = [True] * 3 + [False] * (deb + 2) + [True] * (hyst + 2)
    sh = _new_prod(path, sha)
    rama = _RamaStub(); rama.t_fix, rama.kosz, rama.tryb = 0.0, 1, "para"
    prev, wej, wyj = "NOMINAL", [], []
    for k, cs in enumerate(seq):
        pc = [6.0, 1.0, -10.0]; pe = [pc[0] - OFF[0], pc[1] - OFF[1], pc[2]]
        rama.t_fix = k * dt
        d, pb = nad3_krok.krok(sh, k, pe, pc, [0, 0, 0], pe, pc, M_PATROL, None, cs, k * dt, None, rama)
        ph = sh.kont_phase()
        if prev == "NOMINAL" and ph != "NOMINAL":
            wej.append({"k": k, "rama": d["nad2"]["rama"], "r_est": sh._r_est, "r_corr": math.hypot(pc[0], pc[1])})
        if prev != "NOMINAL" and ph == "NOMINAL":
            wyj.append({"k": k, "rama": d["nad2"]["rama"], "r_est": sh._r_est, "r_ekf": math.hypot(pe[0], pe[1])})
        prev = ph
    ok = (len(wej) == 1 and wej[0]["rama"] == "corr" and abs(wej[0]["r_est"] - wej[0]["r_corr"]) < 1e-9 and
          len(wyj) == 1 and wyj[0]["rama"] == "ekf" and abs(wyj[0]["r_est"] - wyj[0]["r_ekf"]) < 1e-9)
    return ok, {"wejscie": wej, "wyjscie": wyj}


KIERUNKI_FIKSTURY = {"P1": ("na_zewnatrz", "do_srodka"), "P2": ("na_zewnatrz",), "P3": ("do_srodka",)}


def prove_p5(fuzz_n=FUZZ_N, tau_random=TAU_FUZZ, seed0=0):
    res = {}
    ok_all = True
    for p, path in TABELE.items():
        c = consts(path)
        sha = c["tab_sha"]
        C = mirror_consts(c)
        prod = lambda: _new_prod(path, sha)
        cov, mism, pt = set(), [], []
        n = {"grid": 0, "fuzz": 0, "fixture": 0, "tau": 0, "passthrough": 0}
        for e in N2.build_grid(C):
            latch = tuple(e["latch"]) if e["latch"] else None
            mism += run_conformance_episode(e["ticks"], C, prod, e["hyst"], cov, tau_bind=True, latch=latch)
            if latch is None:
                pt += passthrough_episode(e["ticks"], path, sha, e["hyst"])
                n["passthrough"] += len(e["ticks"])
            n["grid"] += len(e["ticks"]); n["tau"] += len(e["ticks"])
        rng = random.Random(seed0 + int(p[1]))
        for i in range(fuzz_n):
            ticks, hyst = N2.fuzz_episode(rng, C)
            tb = i < tau_random
            mism += run_conformance_episode(ticks, C, prod, hyst, cov, tau_bind=tb)
            if i < fuzz_n // 8:
                pt += passthrough_episode(ticks, path, sha, hyst)
                n["passthrough"] += len(ticks)
            n["fuzz"] += len(ticks)
            if tb:
                n["tau"] += len(ticks)
            if len(mism) > 5 or len(pt) > 5:
                break
        wej, mut = None, None
        for kier in KIERUNKI_FIKSTURY[p]:
            pary = fikstura(p, kier)
            for ticks, _ in pary:
                mism += run_conformance_episode(ticks, C, prod, None, cov, tau_bind=False)
                n["fixture"] += len(ticks)
            w = obligacja_wejscia(pary, path, sha)
            m = obligacja_wejscia(pary, path, sha, mutant=True)
            wej = w if wej is None else {k: (wej[k] + w[k] if isinstance(w[k], int) and not isinstance(w[k], bool) else
                                             (max(wej[k], w[k]) if k == "max_dr" else (wej[k] and w[k]))) for k in w}
            mut = m if mut is None else {k: (mut[k] + m[k] if isinstance(m[k], int) and not isinstance(m[k], bool) else
                                             (max(mut[k], m[k]) if k == "max_dr" else (mut[k] and m[k]))) for k in m}
        przej_ok, przej = przejscia_ramy(C, path, sha)
        need = {"R-POS", "R-KONT", "R-G", "R-G-NOM", "R-A", "R-H", "R-R", "R-O", "R-AUTH", "R-P", "cause:τ*", "cause:bariera",
                "second_episode", "utrata_bez_poprawki", "rama:corr", "rama:ekf"} | \
               {f"pole:{t}_i{i}_k{k}" for t in TRYBY for i in range(NI) for k in range(NK)}
        missing = sorted(need - cov)
        mutant_wykryty = mut["r_est_zly"] > 0 or mut["bramka_zla"] > 0
        ok = not mism and not pt and not missing and wej["PASS"] and mutant_wykryty and przej_ok
        ok_all = ok_all and ok
        res[p] = {"ok": ok, "ticks": n, "mismatches": mism[:2], "passthrough": pt[:2], "missing": missing,
                  "coverage_n": len(cov), "obligacja_wejscia": wej, "mutant_czysta_rama": mut, "mutant_wykryty": mutant_wykryty,
                  "przejscia_ok": przej_ok, "przejscia": przej, "tabela_sha256": sha, "kierunki_fikstury": list(KIERUNKI_FIKSTURY[p])}
        print(f"  P5_nad3 {p}: ok={ok} ticki={n} rozb={len(mism)} pt={len(pt)} brak={missing} wejście={wej['PASS']} "
              f"mutant={mutant_wykryty} przejścia={przej_ok}", flush=True)
    return ok_all, res


def ostrosc_p5():
    """Mutant: produkcja z tabelą P1 o krawędzi 0.75 → 0.80 (sha przeliczona), lustro ze stałymi FREEZE P1 — siatka brzegów."""
    p = mutant_tabeli(TABELE["P1"], lambda t: t["krawedzie_tau_s"].__setitem__(2, 0.80), "kraw2_0_80")
    c = consts(TABELE["P1"])
    C = mirror_consts(c)
    sha_m = _sha_pliku(p)
    prod = lambda: _new_prod(p, sha_m)
    mism = []
    for e in N2.build_grid(C):
        latch = tuple(e["latch"]) if e["latch"] else None
        mism += run_conformance_episode(e["ticks"], C, prod, e["hyst"], None, latch=latch)
        if mism:
            break
    return {"kraw2_0_80": {"odrzucony": bool(mism), "przez": "rozbieżność konformancji lustro ≠ produkcja" if mism else None}}


# =================================== CLI =====================================
def _write(name, cert):
    p = os.path.join(CERTS, name)
    if os.path.exists(p):
        old = json.load(open(p))
        print(f"  {name} istnieje — zgodność sha: {'TAK' if old.get('model_sha256') == cert['model_sha256'] else 'NIE'}")
    json.dump(cert, open(p, "w"), indent=2, ensure_ascii=False)
    print(f"  zapisano {p}")


A_NAD3 = ("A-nad3 (PRE_NAD3 §4–§6): |p_corr′ − GT(czas próbki EKF)| ≤ U′(przedział osłony, koszyk, tryb) poziomo, p_corr′ = rama po "
          "degradacji (bias ograniczony |E| ≤ E_max wstrzyknięty w harness/nad3_degrad), U′ = 1.5·(F + E + G), G z unii 25 lotów; oraz "
          "r_est osłony = |p_corr′| (obligacja wejścia P5_nad3 (b)). Walidowane w bramce S3 jako (B1) i (B3); naruszenie = FAIL nogi.")


def main_p9():
    import z3
    assert hashlib.sha256(open(PRE, "rb").read()).hexdigest() == PRE_SHA
    ok_all, tab = True, {}
    for p, path in TABELE.items():
        c = consts(path)
        ok, per, arith, wyk = prove_p9_tab(c)
        wyk_plik = json.load(open(path))["wykonalne"]
        arith["wykonalne_eq_pole_tabeli"] = wyk == wyk_plik == WYKONALNE_OCZ[p]
        ok = ok and arith["wykonalne_eq_pole_tabeli"]
        bad = [k for k, v in per.items() if not (v["main"] == "unsat" and all(v[x] == "sat" for x in v if x != "main"))]
        print(f"  {p}: obligacji {len(per)}, niespełnionych {len(bad)}; arytmetyka {all(arith.values())}; wykonalne(r_zad 20) = {wyk}")
        tab[p] = {"ok": ok, "obligations": per, "arithmetic": arith, "wykonalne_r_zad_20": wyk, "tabela": os.path.relpath(path, ROOT),
                  "tabela_sha256": c["tab_sha"], "E": str(c["E"]), "G": [str(x) for x in c["G"]], "krawedzie": [str(x) for x in c["kraw"]],
                  "tau_star": str(c["tau_star"]), "prog_ticki": c["prog"],
                  "R_min": str(min(R_of(c, i, k, t) for t in TRYBY for i in range(NI) for k in range(NK)))}
        ok_all = ok_all and ok
    ostr = ostrosc_p9()
    ostr_ok = all(v["odrzucony"] for v in ostr.values())
    print(f"  ostrość (mutanty tabeli): {ostr}")
    ok_all = ok_all and ostr_ok
    print(f"WERDYKT P9_nad3: {'PROVED' if ok_all else 'UNPROVEN'}")
    if not ok_all:
        sys.exit(1)
    c = consts(TABELE["P1"])
    _write("P9_nad3.json", {
        "property": "P9_nad3", "verdict": "PROVED",
        "method": "z3 LRA per tabela (P1/P2/P3) × pole (przedział τ 0…4 × koszyk 0…4 × tryb) + ostrość trójstronna (U′, R, Δ_D5); "
                  "tabela jako parametr wczytywany przez osłonę (sha); mutanty tabeli odrzucone",
        "z3_lib": z3.get_version_string(), "tabele": tab, "ostrosc_mutanty_tabeli": ostr,
        "theorem": "∀ tabela ∈ {P1, P2, P3} ∀ pole: 0≤r_est≤R ∧ 0≤ε≤U′ ∧ 0≤Δ≤Δ_D5 ∧ 0≤s≤d_stop ∧ |r_c−r_est|≤ε ∧ r_d≤r_est+ε+s+Δ ⇒ "
                   "r_c≤R_E ∧ r_d≤R_E; R = R_E − d_stop − U′ − Δ_D5, U′ = 1.5·(F(koszyk, tryb) + E + G(przedział)); wykonalność "
                   "u′ ≤ m(20 m) zapisana, nie wymagana (P3: fałsz — dowód przechodzi, osłona ma odmówić)",
        "constants": {"freeze": "results/KONT/s2/s2_freeze_bf.json", "freeze_sha256": c["sha256"], "R_E": str(c["r_e"]),
                      "d_stop": str(c["d_stop"]), "delta_D5": str(c["delta"]), "m_p50": str(c["m_p50"]), "r_zad": str(R_ZAD),
                      "pre": "PRE_NAD3.md", "pre_sha256": PRE_SHA},
        "assumptions": [A_NAD3,
                        "A-react (R0.1): przemieszczenie od ostatniego ALLOW do zatrzymania ≤ d_stop (r01/config.py:24-27).",
                        "A-D5 (ANEKS_KONT-3): dryf zejścia ≤ Δ_D5 od REFUSE do przyziemienia.",
                        "Brak poprawki od wejścia w utratę ⇒ pole (jeden, koszyk 4), τ od zera zegara utraty.",
                        "Przedział τ wybiera osłona z τ + 0.012 s; (B1) sądzi wobec U′ przedziału użytego przez osłonę."],
        "code_refs": {"bariera": "r03/nadir_shield.py:NadirShield._nad3_barrier, r_nad3, przedzial_nad3, nad3_tabela",
                      "rama": "r03/nadir_shield.py:NadirShield._step_nad3", "driver": "results/NAD3/tools/nad3_krok.py:krok",
                      "degradacja": "harness/nad3_degrad.py", "prover": "r01/proofs/p9_nad3_verify.py"},
        "model_sha256": _self_sha()})


def main_p7():
    ok, res, chk, z = prove_p7()
    ostr = ostrosc_p7()
    ostr_ok = all(v["odrzucony"] for v in ostr.values())
    print("=== P7_nad3: graf monitora GNSS + zegara τ (enumeracja, per pole, próg z tabeli) ===")
    print(f"  {res}\n  checks fail: {[k for k, v in chk.items() if not v]}\n  z3: {z}\n  ostrość: {ostr}")
    ok = ok and ostr_ok
    print(f"WERDYKT P7_nad3: {'PROVED' if ok else 'UNPROVEN'}")
    if not ok:
        sys.exit(1)
    _write("P7_nad3.json", {
        "property": "P7_nad3", "verdict": "PROVED",
        "method": "wyczerpująca enumeracja osiągalnego grafu (BFS) monitora GNSS + zegara τ na LUSTRZE (p9_nadir_verify.build_graph/"
                  "_p7_checks, READ-ONLY), osobno dla każdego z 10 pól; próg τ* − 2·dt = 21 ticków liczony z tabel P1/P2/P3 "
                  "(wspólny); instancja zredukowana; z3-duplikat kroku; mutanty tabeli odrzucone",
        "obligations": res, "checks": chk, "z3_duplicate": z, "ostrosc_mutanty_tabeli": ostr,
        "theorem": "(a) wejście w utratę tylko na fladze po debounce; (b) brak ALLOW w utracie przy τ ≥ 1.05 s, REFUSE dokładnie przy "
                   "progu; (c) wyjście tylko po hyst zdrowych tickach, czyści zatrzask; (d) zatrzask trwa w utracie także po nowej "
                   "poprawce; (e) poprawka zeruje τ i ustawia pole; (f) REFUSE z bariery osiągalny w każdym wieku < progu; (g) brak "
                   "poprawki ⇒ pole (jeden, 4)",
        "model_sha256": _self_sha()})


def main_p5():
    import z3
    ok, res = prove_p5()
    ostr = ostrosc_p5()
    ostr_ok = all(v["odrzucony"] for v in ostr.values())
    print(f"  ostrość: {ostr}")
    ok = ok and ostr_ok
    for p, r in res.items():
        for x in r["mismatches"][:1] + r["passthrough"][:1]:
            print(f"  {p} PIERWSZA ROZBIEŻNOŚĆ:", json.dumps(x, default=str, ensure_ascii=False)[:2000])
    print(f"WERDYKT P5_nad3: {'PASS' if ok else 'FAIL'}")
    if not ok:
        sys.exit(1)
    _write("P5_nad3.json", {
        "property": "P5_nad3", "verdict": "PASS",
        "method": "per-tick konformancja: lustro (p9_nad2_verify.mirror_step_nad2 ze stałymi tabeli punktu) ≡ r03/nadir_shield.NadirShield "
                  "(nadir_mode=1, nad3, tabela P1/P2/P3) + tau_kont (P1) ≡ produkcja; obligacja wejścia na ścieżce drivera "
                  "(nad3_krok.krok) na fiksturze 13 lotów NAD2 z degradacją punktu, mutant z ramą czystą; przejścia ramy; "
                  "passthrough NADIR_MODE=0 z nad3 ≡ KontShield pełnym dictem; mutant krawędzi tabeli wykryty",
        "z3_lib": z3.get_version_string(), "tabele": {p: {k: v for k, v in r.items() if k not in ("mismatches", "passthrough")}
                                                      for p, r in res.items()},
        "ostrosc_mutanty_tabeli": ostr,
        "fuzz": {"episodes_per_tabela": FUZZ_N, "tau_bound_per_tabela": TAU_FUZZ, "seed": "0 + numer punktu",
                 "passthrough_per_tabela": FUZZ_N // 8},
        "fixture": "13 lotów NAD2 (12 cięć S3 + L_c10_s01): wejścia z rama.jsonl + tk + demo; strumień producenta z replayu Rama NAD2; "
                   "degradacja harness/nad3_degrad (bias_rad, f 1, K 0, ziarno 1) — P1 oba kierunki, P2 na zewnątrz, P3 do środka",
        "binds": "P7_nad3 (lustro monitora i zegara τ), P9_nad3 (założenie r_est = |p_corr′|)",
        "model_sha256": _self_sha()})


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    for name, fn in (("p9", main_p9), ("p7", main_p7), ("p5", main_p5)):
        if cmd in (name, "all"):
            fn()


if __name__ == "__main__":
    main()
