"""r01/proofs/p9_teach_verify.py — certy nogi TEACH: P9_teach, P7_teach, P5_teach (PROMPT_TEACH_S1 §3, PRE_TEACH §3.6, §4–§5). NOWY
plik = KOPIA r01/proofs/p9_nad3_verify.py (nietknięty) ze zmianami oznaczonymi „TEACH:” wyłącznie:
  - tabela: jedna tabela FREEZE results/TEACH/s1/freeze_U_TEACH.json (punkt „TEACH”, E = 1.00 m, F = 0, dziesięć krawędzi do
    2.15 s, τ* = 2.15 s, próg zatrzasku 41 ticków), wczytywana przez osłonę r03/nadir_shield.nad3_tabela (nietknięta); PRE_TEACH.md
    z sumą; wykonalność oczekiwana prawda;
  - liczba krawędzi: NI = 10 (asercja = długość krawędzi tabeli); siatka brzegów i fuzz jako kopie p9_nad2_verify.build_grid /
    fuzz_episode z NI tabeli (oryginały mają NI = 5 jako stałą modułu) i czasami prób zatrzasku przesuniętymi za próg tabeli
    (oryginał: 1.2 s > próg 1.05 s; tu próg 2.05 s);
  - fikstura P5_teach: 13 lotów reconu (12 cięć NAD3 S3 + lot długi NAD2) × łaty S, M, J ze strumieniem poprawek mapy
    (results/TEACH/tools/teach_strumien.py, wariant z results/TEACH/s1/tor.json); obligacja wejścia na ścieżce drivera
    results/NAD3/tools/nad3_krok.krok (driver TEACH woła ją bez zmian); mutant: osłona dostaje pozycję i cel BEZ poprawki (p_EKF);
  - mutanty ostrości przesunięte do τ* = 2.15 s (P9: τ* = 2.10, zamiana G[2] ↔ G[3]; P7: τ* = 2.12 — próg niecałkowity,
    τ* = 2.20 przy progu 41; P5: krawędź 0.75 → 0.80).
Uruchom: PYTHONPATH=.certdeps:. python3 -m r01.proofs.p9_teach_verify p9|p7|p5|all
Nagłówek oryginału:
r01/proofs/p9_nad3_verify.py — certy nogi NADIR-III: P9_nad3, P7_nad3, P5_nad3 (PROMPT_NAD3_S1 §3, PRE_NAD3 §4–§5). NOWY plik;
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
PRE = os.path.join(ROOT, "PRE_TEACH.md")                            # TEACH
PRE_SHA = "ee1a4bb70129dde42cf7b2fba0bfa6807bae9aeac676e2e031e0d22eb8ab0e54"
TABELE = {"TEACH": os.path.join(ROOT, "results/TEACH/s1/freeze_U_TEACH.json")}   # TEACH: jedna tabela
WYKONALNE_OCZ = {"TEACH": True}                                     # TEACH
R_ZAD = Fraction(20)
TRYBY, NK = N2.TRYBY, N2.NK
NI = 10                                                             # TEACH: dziesięć krawędzi (asercja w consts)
PROG = 41                                                           # TEACH: próg zatrzasku (τ* − 2·dt)/dt
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
    assert len(c["kraw"]) == NI == len(c["G"]), (len(c["kraw"]), NI)                     # TEACH
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
        "thr_ticks_integer_eq_prog": (thr / dt).denominator == 1 and int(thr / dt) == c["prog"] == PROG,   # TEACH: 41
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
    d = tempfile.mkdtemp(prefix="teach_mutant_")                     # TEACH
    p = os.path.join(d, f"{nazwa}.json")
    json.dump(doc, open(p, "w"), ensure_ascii=False, indent=1)
    return p


def ostrosc_p9():
    """TEACH: mutanty tabeli TEACH: τ* = 2.10 (≠ ostatnia krawędź), G[2] > G[3] (R rosnąca w i). Odrzucenie = osłona odmawia startu
    (NadirStartError) albo prover zwraca UNPROVEN."""
    from r03 import nadir_shield as NS
    out = {}

    def g_nierosnace(t):
        t["G"][2], t["G"][3] = t["G"][3], t["G"][2]
    for nm, z in (("tau_star_2_10", lambda t: t.update(tau_star_s=2.10)), ("G_nierosnace", g_nierosnace)):   # TEACH
        p = mutant_tabeli(TABELE["TEACH"], z, nm)
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
    thr1 = progi["TEACH"]                                           # TEACH
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
    return all(chk.values()) and all(v == "unsat" for v in z.values()) and thr1 == PROG, res, chk, z   # TEACH: 41


def ostrosc_p7():
    """TEACH: mutanty τ* = 2.12 (próg niecałkowity), τ* = 2.20 przy progu tabeli 41 (próg ≠ (τ* − 2·dt)/dt)."""
    from r03 import nadir_shield as NS
    out = {}
    for nm, z in (("tau_star_2_12", lambda t: t.update(tau_star_s=2.12, krawedzie_tau_s=t["krawedzie_tau_s"][:-1] + [2.12])),
                  ("tau_star_2_20_prog_41", lambda t: t.update(tau_star_s=2.20, krawedzie_tau_s=t["krawedzie_tau_s"][:-1] + [2.20]))):
        p = mutant_tabeli(TABELE["TEACH"], z, nm)
        try:
            c = consts(p)
            x = (c["tau_star"] - T_MARGIN_TICKS * Fraction(1, 20)) / Fraction(1, 20)
            out[nm] = {"odrzucony": not (x.denominator == 1 and int(x) == c["prog"] == PROG), "przez": "asercja progu P7"}
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


def fikstura(wariant):
    """TEACH: 13 lotów reconu × łaty S, M, J: wejścia ticku z zapisu + stan ramy ze strumienia poprawek mapy (teach_strumien);
    zwraca listę (ticki, ticki_bez_poprawki) — bez poprawki = pozycja i cel w ramie EKF (wejście mutanta)."""
    sys.path[:0] = [os.path.join(ROOT, "results/TEACH/tools"), os.path.join(ROOT, "results/NAD3_RECON/tools")]
    import teach_strumien as TS
    out = []
    for n, d in TS.loty():
        L = TS.wczytaj_lot(n, d)
        for lata in TS.LATY:
            st = TS.strumien(L, TS.czesc(n, lata, wariant))
            out.append(TS.ticki(L, st))
    return out


# TEACH: siatka brzegów i fuzz — kopie p9_nad2_verify.build_grid / fuzz_episode z NI tabeli; próby zatrzasku za progiem tabeli
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
    Rs = [C["R"][t][i][k] for t in TRYBY for i in range(NI) for k in range(NK)]                 # TEACH: NI tabeli
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
              "mode": rng.choices([M_PATROL, N2.M_HOLD, N2.M_RETURN, N2.M_ABORT, N2.M_OBSERVE], [0.8, 0.05, 0.05, 0.02, 0.08])[0],
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
    """TEACH: kopia p9_nad2_verify.build_grid — bariera ±1 mm w każdym z NI × 5 × 2 pól, krawędzie, próg τ*, brak poprawki,
    przejście ramy, zatrzask odporny na poprawkę (czasy prób: próg tabeli + 0.15 s zamiast 1.2 s), R-G-NOM, priorytety."""
    deb, hyst, dt = C["debounce_ticks"], C["hyst_ticks"], C["dt"]
    eps = []
    OFF = (3.0, -2.0)
    TL = C["thr"] + 0.15                                                                         # TEACH: za progiem (2.05 s)

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
    run("latch_survives_fix", [T(0.0, t_fix=0.0, kosz=3, tryb="jeden"), T(dt), T(TL), T(TL + 0.05, t_fix=TL + 0.05, kosz=0, tryb="para"),
                               T(TL + 0.1)])
    for r in (C["r_nom"] - 0.01, C["r_nom"] + 0.01):
        for tgt, nm in (((r + 1.0, 0.0, -10.0), "out"), ((r - 1.0, 0.0, -10.0), "in"), ((r, 1.0, -10.0), "tan")):
            run(f"nom_kont_{r:.2f}_{nm}", [T(0.0, (r, 0.0, -10.0), tgt, t_fix=0.0, kosz=0, tryb="para"),
                                           T(dt, (r, 0.0, -10.0), tgt)])
            run(f"nom_nominal_{r:.2f}_{nm}", [T(0.0, (r, 0.0, -10.0), tgt, cs=True)])
    FAR = (45.0, 0.0, -10.0)
    run("prio_pos_over_kont", [T(x, pos_flag=True, t_fix=0.0, kosz=0, tryb="para") for x in (0.0, dt, TL)])
    run("prio_kont_over_geo", [T(0.0, t_fix=0.0, kosz=0, tryb="para"), T(dt), T(TL, tc=FAR)])
    run("prio_latch_over_kont", [T(x) for x in (0.0, dt, TL)], latch=("STALE_CMD", "adm"))
    for md, auth in ((N2.M_HOLD, True), (N2.M_RETURN, True), (N2.M_OBSERVE, True), (N2.M_OBSERVE, False), (N2.M_ABORT, True)):
        run(f"mode_utrata_{md}_{auth}", [T(0.0, mode=md, auth_ok=auth, t_fix=0.0, kosz=2, tryb="jeden"), T(dt, mode=md, auth_ok=auth)])
    run("brak_ramy_poprawionej", [dict(T(0.0, t_fix=0.0, kosz=1, tryb="para"), pos_corr=None), dict(T(dt), pos_corr=None)])
    return eps


class _RamaStub:
    def __init__(self):
        self.t_fix = self.kosz = self.tryb = None


def obligacja_wejscia(pary, path, sha, mutant=False):
    """(b) na ścieżce drivera nad3_krok.krok: r_est = |p_corr| w utracie, = |p_EKF| w NOMINAL. TEACH: mutant=True: osłona dostaje
    pozycję i cel BEZ poprawki (rama EKF) — wymaganie liczone wobec p_corr."""
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
        for e in build_grid(C):                                       # TEACH: siatka z NI tabeli
            latch = tuple(e["latch"]) if e["latch"] else None
            mism += run_conformance_episode(e["ticks"], C, prod, e["hyst"], cov, tau_bind=True, latch=latch)
            if latch is None:
                pt += passthrough_episode(e["ticks"], path, sha, e["hyst"])
                n["passthrough"] += len(e["ticks"])
            n["grid"] += len(e["ticks"]); n["tau"] += len(e["ticks"])
        rng = random.Random(seed0 + 7)                                # TEACH: ziarno stałe (jedna tabela)
        for i in range(fuzz_n):
            ticks, hyst = fuzz_episode(rng, C)                        # TEACH: fuzz z NI tabeli
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
        wariant = json.load(open(os.path.join(ROOT, "results/TEACH/s1/tor.json")))["tor"]["wariant_K"]   # TEACH
        pary = fikstura(wariant)
        for ticks, _ in pary:
            mism += run_conformance_episode(ticks, C, prod, None, cov, tau_bind=False)
            n["fixture"] += len(ticks)
        wej = obligacja_wejscia(pary, path, sha)
        mut = obligacja_wejscia(pary, path, sha, mutant=True)
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
                  "przejscia_ok": przej_ok, "przejscia": przej, "tabela_sha256": sha, "wariant_K": wariant, "n_lotow_fikstury": len(pary)}
        print(f"  P5_teach {p}: ok={ok} ticki={n} rozb={len(mism)} pt={len(pt)} brak={missing} wejście={wej['PASS']} "
              f"mutant={mutant_wykryty} przejścia={przej_ok}", flush=True)
    return ok_all, res


def ostrosc_p5():
    """TEACH: mutant: produkcja z tabelą TEACH o krawędzi 0.75 → 0.80 (sha przeliczona), lustro ze stałymi FREEZE — siatka brzegów."""
    p = mutant_tabeli(TABELE["TEACH"], lambda t: t["krawedzie_tau_s"].__setitem__(2, 0.80), "kraw2_0_80")
    c = consts(TABELE["TEACH"])
    C = mirror_consts(c)
    sha_m = _sha_pliku(p)
    prod = lambda: _new_prod(p, sha_m)
    mism = []
    for e in build_grid(C):                                           # TEACH
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


A_TEACH = ("A-teach (PRE_TEACH §4, §6): |p_corr − GT(czas próbki EKF)| ≤ U′(przedział osłony) poziomo, p_corr = p_EKF + Δ z poprawki "
           "mapy własnego lotu (harness/teach_map, M4 / SIFT, a12_geo0_g1.5), U′ = 1.5·(F + E + G), F = 0, E = 1.00 m, G z unii 25 lotów "
           "(38 lotów nie podnosi pola); oraz r_est osłony = |p_corr| (obligacja wejścia P5_teach (b)). Walidowane w bramce S3 jako (B1) "
           "i (B3); naruszenie = FAIL nogi.")                          # TEACH


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
    print(f"WERDYKT P9_teach: {'PROVED' if ok_all else 'UNPROVEN'}")
    if not ok_all:
        sys.exit(1)
    c = consts(TABELE["TEACH"])
    _write("P9_teach.json", {
        "property": "P9_teach", "verdict": "PROVED",
        "method": "z3 LRA na tabeli TEACH × pole (przedział τ 0…9 × koszyk 0…4 × tryb) + ostrość trójstronna (U′, R, Δ_D5); "
                  "tabela jako parametr wczytywany przez osłonę (sha); mutanty tabeli odrzucone",
        "z3_lib": z3.get_version_string(), "tabele": tab, "ostrosc_mutanty_tabeli": ostr,
        "theorem": "∀ pole tabeli TEACH: 0≤r_est≤R ∧ 0≤ε≤U′ ∧ 0≤Δ≤Δ_D5 ∧ 0≤s≤d_stop ∧ |r_c−r_est|≤ε ∧ r_d≤r_est+ε+s+Δ ⇒ "
                   "r_c≤R_E ∧ r_d≤R_E; R = R_E − d_stop − U′ − Δ_D5, U′ = 1.5·(F + E + G(przedział)), F = 0, E = 1.00 m; "
                   "wykonalność u′ ≤ m(20 m) prawdziwa (asercja zgodności z polem tabeli)",
        "constants": {"freeze": "results/KONT/s2/s2_freeze_bf.json", "freeze_sha256": c["sha256"], "R_E": str(c["r_e"]),
                      "d_stop": str(c["d_stop"]), "delta_D5": str(c["delta"]), "m_p50": str(c["m_p50"]), "r_zad": str(R_ZAD),
                      "pre": "PRE_TEACH.md", "pre_sha256": PRE_SHA},
        "assumptions": [A_TEACH,
                        "A-react (R0.1): przemieszczenie od ostatniego ALLOW do zatrzymania ≤ d_stop (r01/config.py:24-27).",
                        "A-D5 (ANEKS_KONT-3): dryf zejścia ≤ Δ_D5 od REFUSE do przyziemienia.",
                        "Brak poprawki od wejścia w utratę ⇒ pole (jeden, koszyk 4) = najgorsze, τ od zera zegara utraty.",
                        "Przedział τ wybiera osłona z τ + 0.012 s; (B1) sądzi wobec U′ przedziału użytego przez osłonę."],
        "code_refs": {"bariera": "r03/nadir_shield.py:NadirShield._nad3_barrier, r_nad3, przedzial_nad3, nad3_tabela",
                      "rama": "r03/nadir_shield.py:NadirShield._step_nad3", "driver": "results/NAD3/tools/nad3_krok.py:krok",
                      "zrodlo": "harness/teach_map.py", "prover": "r01/proofs/p9_teach_verify.py"},
        "model_sha256": _self_sha()})


def main_p7():
    ok, res, chk, z = prove_p7()
    ostr = ostrosc_p7()
    ostr_ok = all(v["odrzucony"] for v in ostr.values())
    print("=== P7_teach: graf monitora GNSS + zegara τ (enumeracja, per pole, próg z tabeli) ===")
    print(f"  {res}\n  checks fail: {[k for k, v in chk.items() if not v]}\n  z3: {z}\n  ostrość: {ostr}")
    ok = ok and ostr_ok
    print(f"WERDYKT P7_teach: {'PROVED' if ok else 'UNPROVEN'}")
    if not ok:
        sys.exit(1)
    _write("P7_teach.json", {
        "property": "P7_teach", "verdict": "PROVED",
        "method": "wyczerpująca enumeracja osiągalnego grafu (BFS) monitora GNSS + zegara τ na LUSTRZE (p9_nadir_verify.build_graph/"
                  "_p7_checks, READ-ONLY), osobno dla każdego z 10 pól (tryb × koszyk); próg τ* − 2·dt = 41 ticków z tabeli TEACH; "
                  "instancja zredukowana; z3-duplikat kroku; mutanty tabeli odrzucone",
        "obligations": res, "checks": chk, "z3_duplicate": z, "ostrosc_mutanty_tabeli": ostr,
        "theorem": "(a) wejście w utratę tylko na fladze po debounce; (b) brak ALLOW w utracie przy τ ≥ 2.05 s, REFUSE dokładnie przy "
                   "progu 41 ticków; (c) wyjście tylko po hyst zdrowych tickach, czyści zatrzask; (d) zatrzask trwa w utracie także "
                   "po nowej poprawce; (e) poprawka zeruje τ i ustawia pole; (f) REFUSE z bariery osiągalny w każdym wieku < progu; "
                   "(g) brak poprawki ⇒ pole (jeden, 4)",
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
    print(f"WERDYKT P5_teach: {'PASS' if ok else 'FAIL'}")
    if not ok:
        sys.exit(1)
    _write("P5_teach.json", {
        "property": "P5_teach", "verdict": "PASS",
        "method": "per-tick konformancja: lustro (p9_nad2_verify.mirror_step_nad2 ze stałymi tabeli TEACH) ≡ r03/nadir_shield.NadirShield "
                  "(nadir_mode=1, nad3, tabela TEACH) na siatce brzegów i fuzzie z 10 przedziałami + tau_kont (P1) ≡ produkcja; "
                  "obligacja wejścia na ścieżce drivera (nad3_krok.krok) na fiksturze 13 lotów × 3 łaty ze strumieniem poprawek mapy, "
                  "mutant bez poprawki; przejścia ramy; passthrough NADIR_MODE=0 z nad3 ≡ KontShield pełnym dictem; mutant krawędzi "
                  "tabeli wykryty",
        "z3_lib": z3.get_version_string(), "tabele": {p: {k: v for k, v in r.items() if k not in ("mismatches", "passthrough")}
                                                      for p, r in res.items()},
        "ostrosc_mutanty_tabeli": ostr,
        "fuzz": {"episodes_per_tabela": FUZZ_N, "tau_bound_per_tabela": TAU_FUZZ, "seed": 7, "passthrough_per_tabela": FUZZ_N // 8},
        "fixture": "13 lotów reconu TEACH (12 cięć NAD3 S3 + L_c10_s01) × łaty S, M, J: wejścia z rama.jsonl + tk + demo; strumień "
                   "poprawek mapy z W2/W4 (results/TEACH/tools/teach_strumien.py) dostarczany w miejscu seq datagramu lotu",
        "binds": "P7_teach (lustro monitora i zegara τ), P9_teach (założenie r_est = |p_corr|)",
        "model_sha256": _self_sha()})


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    for name, fn in (("p9", main_p9), ("p7", main_p7), ("p5", main_p5)):
        if cmd in (name, "all"):
            fn()


if __name__ == "__main__":
    main()
