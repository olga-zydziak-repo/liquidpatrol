#!/usr/bin/env python3
"""results/NADIR/tools/nadir_s4_analyze.py — litera S4 NADIR per boot (PROMPT_NADIR_S4 §R, PRE_NADIR §3 + ANEKS_NADIR-2 §3 (g)).
PRERejestracja definicji (commit przed pierwszym bootem S4); z GT, ramy i ulogu, nie z listy zdarzeń.

Stałe (asercje): ε_fix_freeze, τ*(j), R_H_MAX, J_WORST z r03/nadir_shield.py (sha aneksu w osłonie); ε_b i Δ_D5 z
results/KONT/s2/s2_freeze_bf.json (sha ae19f66c), prefiks ε_b[0:22] ≡ kont_shield.EPS_B; m komórki = results/KONT_RECON/
r4_margin.json tabela_scenariuszy[scenariusz].m; R_E = 32 m; pasmo [6, 10] m i 0.85 = kanon ławki (jak kont_s4_analyze (c)).
Czas = sim (ulog PX4 w lockstepie = sim; S2: opóźnienie flagi 0.000–0.004 s).

Fazy misji (tick ramy / tk): phase ∈ {approach, hold, orbit} w epizodzie przed zejściem; t_zejscia = zdarzenie
„zejscie_planowe” (driver, ≥ 110 s od cięcia) albo pierwszy REFUSE(POS) epizodu (litera (a) złamana). Liczenie REFUSE: ticki
faz misji przed zejściem planowym (bez filtra desc — tick REFUSE uruchamiający zejście ma już desc = True); τ, u, koszt
kontrfaktyczny: ticki faz misji przed t_zejscia.
Cięcie: t_cut = sim zdarzenia „denial”; t_flag = pierwsze cs_gnss_pos 1→0 w ulogu po t_cut − 0.5 s.

Ważność bootu (przyrząd, nie litera): selftest gt_judge (sha 447efaa2) ∧ V2′ kanoniczne per epizod (bench/campaign_analyze.
judge_boot: Δsim/Δwall ≥ 0.90 ∧ deep-stall ≤ 1.5 s ∧ timejump 0) ∧ zegar (skan2_zegar --check) ∧ [cięcie] xy_valid (ulog)
w [t_flag, t_zejscia].

Litera epizodu cięcia:
 (a) zdarzenie zejscie_planowe ∧ kontynuacja t_zejscia − t_cut ≥ 110 s ∧ 0 ticków REFUSE (każda reguła, z R-G-NOM) w fazach
     misji epizodu ∧ track/orbita w [t_flag, t_zejscia]: frac(ticków z ważnym trackiem) ≥ 0.85 ∧ frac(d_GT dron–intruz ∈
     [6, 10] m) ≥ 0.85 (definicja (c) KONT S4 = kanon ławki).
 (b) ∀ tick faz misji epizodu (z GNSS i bez): u = ε_fix_freeze(j) + ε_b(⌊τ⌋) + Δ_D5 ≤ m; τ = sim − t_fix ramy, j = koszyk
     ostatniej przyjętej poprawki (rama.kosz), brak poprawki ⇒ j = J_WORST i τ od początku epizodu (koszyk nieznany przy
     znanym t_fix — dane sprzed S3 bez pola kosz — ⇒ j = J_WORST, τ z ramy); ⌊τ⌋ ≥ τ*(j) ⇒ u
     nieokreślone = naruszenie. Kontrola krzyżowa z u osłony (d["nadir"]["u"], ticki KONT) — liczba niezgodności.
 (c) min_t (R_E − r_GT(t)) > 0 od episode_start do przyziemienia GT (wiersze gt i tk), r_GT względem home GT przy uzbrojeniu.
 (d) ulog: nav_state = 14 ∧ failsafe = 0 w [t_flag, przyziemienie GT] (offboard do końca, zero natywnego failsafe).
 (e) p95 τ po tickach faz misji epizodu ≤ 2 s.
 (g) okna między poprawkami: okno = [poprawka i, poprawka i+1), poprawka = rekord producenta fx.ok (litera przyjęcia z r_h < 8);
     e(t) = p_EKF − GT w 3D (N, E, D; GT ENU→NED), parowanie po mono z korektą skew (gt_judge.compute_drift), przyrost
     inc(t) = |e(t) − e(t_i)|, τ = sim(t) − t_fix_i; przekroczenie ⇔ inc > ε_b(⌊τ⌋). Wymóg: 0 przekroczeń w oknach
     rozpoczętych w fazach misji (z_GNSS ∪ bez_GNSS); okna zejścia osobno. Miara 2D (N, E — metoda S2 R1) raportowana obok.
Ramię nominalne:
 (f) w każdym epizodzie: 0 ticków z fazą KONT ≠ NOMINAL (fałszywe wejścia) ∧ 0 ticków REFUSE (każda reguła).
     Koszt bariery = REFUSE z bariery piły (przyczyna „bariera”/„τ*”) — 0 z definicji bez wejścia w KONT; obok koszt
     kontrfaktyczny: ticki faz misji, w których gdyby GNSS zniknął, bariera dałaby REFUSE (r_est > R(⌊τ⌋, j) albo
     τ ≥ τ*(j) − 2·dt). (b), (c), (d) w oknie epizodów, (e), (g) — raportowane jako obserwable.
Obserwable bez progu (per epizod): czas ENTRY, τ p50/p95/max (cała misja i po cięciu), koszyki użytych poprawek, odrzucenia
literą r_h < 8, koszt bariery (+ kontrfaktyczny, min zapas R(k, j) − r_est), bias kursu z par (p50, trend °/s), u_max/m,
u_live (ε_fix na żywo z GT zamiast freeze, jak S2 R4).
Użycie: nadir_s4_analyze.py <boot_dir> [...]; wyjście <boot_dir>/wyniki_nadir_s4.json.
"""
import bisect
import hashlib
import json
import math
import os
import sys

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/NADIR/tools"), os.path.join(ROOT, "results/KONT/tools"),
                os.path.join(ROOT, "results/R03/recon/B1bis/instrument")]
import nadir_s1v2_analyze as S1A                             # READ-ONLY: GT, rotm, load, pct
import kont_s4_analyze as K4                                 # READ-ONLY: load, ev1, trans, zegar_ok, judge_boot, X, J
from harness import nadir_fix as NF
from harness.intruder_motion import gz_to_ned
from r03 import nadir_shield as NS
from r03.kont_shield import EPS_B as EPS_B_SHIELD

J, X = K4.J, K4.X
FREEZE = os.path.join(ROOT, "results/KONT/s2/s2_freeze_bf.json")
FREEZE_SHA = "ae19f66c6807de6c824bf0fd723965258b15b77963eb866afb78d3dd3740ae4a"
GT_SHA8 = "447efaa2"
MARG = json.load(open(os.path.join(ROOT, "results/KONT_RECON/r4_margin.json")))["tabela_scenariuszy"]
MISJA = ("approach", "hold", "orbit")
R_E, T_CONT, TAU_P95_MAX, V2P_MIN = 32.0, 110.0, 2.0, 0.90
BAND, FRAC_MIN = (6.0, 10.0), 0.85
DT, T_MARGIN_TICKS = 0.05, 2
ZN = {z["id"]: z for z in json.load(open(NF.MANIFEST))["znaczniki"]}
pct = S1A.pct


def stale():
    raw = open(FREEZE, "rb").read()
    assert hashlib.sha256(raw).hexdigest() == FREEZE_SHA
    F = json.loads(raw)
    assert tuple(F["eps_b_obwiednia"][:len(EPS_B_SHIELD)]) == tuple(EPS_B_SHIELD)
    assert F["delta_D5"] == NS.DELTA_D5
    assert NS.EPS_FIX_FREEZE == (0.305, 0.293, 0.227, 0.582) and NS.TAU_STAR_S == (22, 22, 22, 21) and NS.J_WORST == 3
    assert hashlib.sha256(open(os.path.join(J.__file__), "rb").read()).hexdigest()[:8] == GT_SHA8
    return F["eps_b_obwiednia"], F["delta_D5"]


def u_tick(tau, j, eps_b, dd5):
    """u = ε_fix_freeze(j) + ε_b(⌊τ⌋) + Δ_D5; None ⇔ ⌊τ⌋ ≥ τ*(j) (u nieokreślone ⇒ naruszenie (b))."""
    k = int(math.floor(max(0.0, tau)))
    if k >= NS.TAU_STAR_S[j]:
        return None, k
    return NS.EPS_FIX_FREEZE[j] + eps_b[k] + dd5, k


def gt_series(gt):
    g = sorted(gt, key=lambda r: r["mono"])
    return (np.array([r["mono"] for r in g]), np.array([r["sim"] for r in g]),
            np.array([[r["x"], r["y"], r["z"]] for r in g]))


def e3_series(ekf, gt, ts):
    """e(t) = p_EKF − GT w NED 3D po mono EKF (GT interpolowane liniowo w mono + ts)."""
    gm, _, gp = gt_series(gt)
    em = np.array([r["mono"] for r in ekf])
    ok = (em + ts >= gm[0]) & (em + ts <= gm[-1])
    em = em[ok]
    ek = np.array([[r["x"], r["y"], r["z"]] for r in ekf])[ok]
    gx, gy, gz = (np.interp(em + ts, gm, gp[:, i]) for i in range(3))
    return em, np.stack([ek[:, 0] - gy, ek[:, 1] - gx, ek[:, 2] + gz], axis=1)   # ENU→NED: N=y, E=x, D=−z


def okna(fixes, em, e, m2s, eps_b, t_flag, t_desc, wymiar):
    out = []
    for i, f in enumerate(fixes):
        m0 = f["mono"]
        m1 = fixes[i + 1]["mono"] if i + 1 < len(fixes) else (em[-1] if len(em) else m0)
        e0 = np.array([np.interp(m0, em, e[:, c]) for c in range(e.shape[1])])
        sel = np.flatnonzero((em > m0) & (em < m1))
        klasa = ("zejscie" if t_desc is not None and f["t"] >= t_desc else
                 "bez_GNSS" if t_flag is not None and f["t"] >= t_flag else "z_GNSS")
        worst, n_prz, tau_max = 0.0, 0, 0.0
        for j in sel:
            tau = m2s(em[j]) - f["t"]
            inc = float(np.linalg.norm(e[j, :wymiar] - e0[:wymiar]))
            b = eps_b[min(int(max(tau, 0.0)), len(eps_b) - 1)]
            worst = max(worst, inc / b)
            n_prz += int(inc > b)
            tau_max = max(tau_max, tau)
        out.append({"t_fix": round(f["t"], 3), "klasa": klasa, "tau_max": round(tau_max, 3), "n_probek": int(len(sel)),
                    "max_inc_do_eps_b": round(worst, 4), "przekroczenia": n_prz})
    res = {}
    for kl in ("z_GNSS", "bez_GNSS", "zejscie"):
        o = [x for x in out if x["klasa"] == kl]
        res[kl] = {"n": len(o), "z_przekroczeniem": sum(x["przekroczenia"] > 0 for x in o),
                   "max_inc_do_eps_b": max((x["max_inc_do_eps_b"] for x in o), default=None),
                   "tau_gt_2s": sum(x["tau_max"] > 2.0 for x in o),
                   "najgorsze": sorted(o, key=lambda x: -x["max_inc_do_eps_b"])[:3]}
    res["przekroczenia_misja"] = res["z_GNSS"]["z_przekroczeniem"] + res["bez_GNSS"]["z_przekroczeniem"]
    return res


def nav_ok(vs, t0, t1):
    vt = vs["timestamp"] / 1e6
    m = (vt >= t0) & (vt <= t1)
    poza = sorted(set(int(x) for x in vs["nav_state"][m] if x != 14))
    fsm = int(vs["failsafe"][m].max()) if m.any() else None
    return {"nav_poza_14": poza, "failsafe_max": fsm, "ok": bool(m.any()) and not poza and fsm == 0}


def analyze(d):
    eps_b, dd5 = stale()
    st = __import__("subprocess").run([sys.executable, J.__file__, "--selftest"], capture_output=True, text=True)
    R = K4.load(d)
    evs, gt, tk = R["event"], R["gt"], R["tk"]
    res = {"boot": os.path.basename(d.rstrip("/")), "przyrzad_selftest": st.returncode == 0}
    res["zegar_ok"], res["zegar_skoki"] = K4.zegar_ok(os.path.join(d, "zegar2.jsonl"))
    armed = K4.ev1(evs, "armed")
    if armed is None or not tk:
        res.update(wazny=False, powod_niewazny="brak uzbrojenia albo pętli", epizody=[])
        json.dump(res, open(os.path.join(d, "wyniki_nadir_s4.json"), "w"), ensure_ascii=False, indent=1)
        return res
    gx0, gy0 = armed["gt_home"]
    rgt = lambda g: math.hypot(g["x"] - gx0, g["y"] - gy0)
    v2 = {v["episode_id"]: v for v in K4.judge_boot(d)}
    res["v2p_epizody"] = {str(k): {"valid": bool(v["valid_campaign_V2p"]), **v["stalls"]} for k, v in v2.items()}
    gm, gs, _ = gt_series(gt)
    m2s = lambda t: float(np.interp(t, gm, gs))
    rama = S1A.load(os.path.join(d, "rama.jsonl")) if os.path.exists(os.path.join(d, "rama.jsonl")) else []
    nf = sorted([r for r in S1A.load(os.path.join(d, "nadir_obs.jsonl"), "nf") if "fx" in r], key=lambda r: r["mono"])
    cut = K4.ev1(evs, "denial")
    ulg = os.path.join(d, "boot.ulg")
    u = K4.X.load(ulg)[1] if os.path.exists(ulg) else None
    t_flag = None
    if cut is not None and u is not None:
        fl = u["estimator_status_flags"]
        t_flag = next((t for t, v in K4.trans(fl["timestamp"], fl["cs_gnss_pos"]) if v == 0 and t >= cut["sim"] - 0.5), None)
    land = K4.ev1(evs, "gt_przyziemienie")
    # 3D/2D błąd EKF − GT; skew z okna zdrowego (jak S2 R1)
    ekf = R["ekf"]
    for r in ekf:
        r["dead_reckoning"] = cut is not None and cut["mono"] <= r["mono"] <= (land["mono"] if land else 1e18)
    md = J.compute_drift(ekf, gt) if cut is not None else None
    ts = (md["skew_hat_s"] if md and md["skew_applied"] else 0.0)
    em3, e3 = e3_series(ekf, gt, ts)
    s2 = J._paired_series(ekf, gt, True, ts)
    em2, e2 = np.array([x[0] for x in s2]), np.array([[x[1], x[2]] for x in s2])
    res["skew_s"] = md["skew_hat_s"] if md else None
    gtp = None
    eps_out = []
    for st_ev in [e for e in evs if e["ev"] == "episode_start"]:
        ep, scen = st_ev["episode_id"], st_ev["scenario_id"]
        en = K4.ev1(evs, "episode_end", ep)
        zp = K4.ev1(evs, "zejscie_planowe", ep)
        ref = next((e for e in evs if e["ev"] == "refuse" and e.get("episode_id") == ep), None)
        c_ep = cut if (cut is not None and cut.get("episode_id") == ep) else None
        t0, t0m = st_ev["sim"], st_ev["mono"]
        refp = next((e for e in evs if e["ev"] == "refuse" and e.get("episode_id") == ep and e.get("reason") == "POS_DEGRADED"), None)
        t_desc = zp["sim"] if zp else (refp["sim"] if refp else None)
        t_end = (land["sim"] if (land and c_ep) else (en["sim"] if en else None))
        t_end_m = (land["mono"] if (land and c_ep) else (en["mono"] if en else 1e18))
        m_cell = MARG.get(scen, {}).get("m")
        rows = [r for r in tk if r["ep"] == ep]
        mis = [r for r in rows if r.get("phase") in MISJA and (zp is None or r["sim"] < zp["sim"])]
        ram = [r for r in rama if r["ep"] == ep]
        przed = lambda r: t_desc is None or r["sim"] < t_desc
        rmis = [r for r in ram if r.get("phase") in MISJA and przed(r)]
        o = {"episode_id": ep, "scenario_id": scen, "m": m_cell, "ciecie": c_ep is not None, "t_entry": en.get("t_entry") if en else None,
             "n_tk": len(rows), "n_tk_misja": len(mis)}
        o["v2p"] = res["v2p_epizody"].get(str(ep))
        o["v2p_ok"] = bool(o["v2p"] and o["v2p"]["valid"])
        # REFUSE w fazach misji (każda reguła)
        ref_t = [r for r in mis if r["dec"] == "REFUSE"]
        o["refuse_misja"] = {"n": len(ref_t), "reguly": sorted({str(r["rule"]) for r in ref_t}),
                             "przyczyny": sorted({str(r.get("cause")) for r in ref_t}), "pierwszy_sim": ref_t[0]["sim"] if ref_t else None}
        o["refuse_po_zejsciu"] = sum(1 for r in rows if r.get("desc") and r["dec"] == "REFUSE")
        o["kont_ticki_nie_nominal"] = sum(1 for r in rows if r.get("phase") in MISJA and (c_ep is None or r["sim"] < c_ep["sim"]) and r["ph"] != "NOMINAL")
        o["koszt_bariery_refuse"] = sum(1 for r in ref_t if r.get("cause") in (NS.CAUSE_BARRIER, NS.CAUSE_TAUSTAR))
        # (c) margines GT
        gts = [g for g in gt if t0m <= g["mono"] <= t_end_m]
        rg = [rgt(g) for g in gts] + [r["r_gt"] for r in rows]
        o["r_gt_max"] = round(max(rg), 3) if rg else None
        o["margines_min_R_E"] = round(R_E - max(rg), 3) if rg else None
        o["c_ok"] = bool(rg) and R_E - max(rg) > 0
        # τ, u (b), (e), koszt kontrfaktyczny
        taus, us, u_naruszenia, u_none, niezg, kontrf, zapas_min = [], [], 0, 0, 0, 0, None
        taus_po, kosze = [], {}
        for r in rmis:
            if r.get("t_fix") is None:
                tau, j = r["sim"] - t0, NS.J_WORST
            elif r.get("kosz") is None:
                tau, j = r["tau"], NS.J_WORST
            else:
                tau, j = r["tau"], int(r["kosz"])
                kosze.setdefault(r["t_fix"], j)
            taus.append(max(tau, 0.0))
            if c_ep is not None and r["sim"] >= c_ep["sim"]:
                taus_po.append(max(tau, 0.0))
            uu, k = u_tick(tau, j, eps_b, dd5)
            if uu is None:
                u_none += 1
            else:
                us.append((r["sim"], uu, tau, j))
                if m_cell is not None and uu > m_cell:
                    u_naruszenia += 1
            nd = r.get("nadir") or {}
            if nd.get("u") is not None and uu is not None and abs(nd["u"] - round(uu, 4)) > 1e-3:
                niezg += 1
            r_est = math.hypot(r["p_ekf"][0], r["p_ekf"][1])
            if uu is None or tau >= NS.TAU_STAR_S[j] - T_MARGIN_TICKS * DT:
                kontrf += 1
            else:
                zap = NS.r_pila(k, j, R_E) - r_est
                zapas_min = zap if zapas_min is None else min(zapas_min, zap)
                kontrf += int(zap < 0)
        o["tau"] = {"p50": pct(taus, .5), "p95": pct(taus, .95), "max": round(max(taus), 3) if taus else None, "n": len(taus)}
        o["tau_po_cieciu"] = {"p50": pct(taus_po, .5), "p95": pct(taus_po, .95), "max": round(max(taus_po), 3) if taus_po else None,
                              "n": len(taus_po)}
        o["e_ok"] = bool(taus) and pct(taus, .95) <= TAU_P95_MAX
        o["u_max"] = round(max((x[1] for x in us), default=0.0), 4)
        o["u_max_do_m"] = round(o["u_max"] / m_cell, 4) if m_cell else None
        o["u_ticki_gt_m"], o["u_ticki_nieokreslone"], o["u_niezgodnosci_z_oslona"] = u_naruszenia, u_none, niezg
        o["b_ok"] = m_cell is not None and bool(us) and u_naruszenia == 0 and u_none == 0
        o["koszyki_poprawek"] = {str(j): sum(1 for v in kosze.values() if v == j) for j in range(4)}
        o["koszt_kontrfaktyczny_ticki"] = kontrf
        o["zapas_bariery_min"] = round(zapas_min, 3) if zapas_min is not None else None
        # poprawki producenta w epizodzie: odrzucenia r_h, bias kursu, ε_fix na żywo (u_live)
        fx_ep, odrz_rh, dpsi = [], 0, []
        gtI = S1A.GT(os.path.join(d, "trace.jsonl")) if gtp is None else gtp
        gtp = gtI
        for fr in nf:
            if not (fr["sim"] >= t0 and (t_end is None or fr["sim"] <= t_end)):
                continue
            fx = fr["fx"]
            odrz_rh += sum(1 for x in fx.get("odrz", []) if x.get("powod") == "rh")
            if not fx["ok"]:
                continue
            gg = gtI.at(fr["sim"])
            e_live = None
            if gg is not None:
                p0, _ = gg
                e_live = math.hypot(fx["p_fix_ne"][1] - p0[0], fx["p_fix_ne"][0] - p0[1])
            if fx.get("para") and not fx["para"].get("odrzucona"):
                dpsi.append((fr["sim"], fx["para"]["dpsi_deg"]))
            fx_ep.append({"t": fr["sim"], "mono": fr["mono"], "seq": fx["seq"], "e_live": e_live, "kosz": fx.get("kosz")})
        o["odrzucenia_rh"] = odrz_rh
        o["n_poprawek"] = len(fx_ep)
        o["n_poprawek_misja"] = sum(1 for f in fx_ep if t_desc is None or f["t"] < t_desc)
        o["eps_fix_live"] = {"p95": pct([f["e_live"] for f in fx_ep if f["e_live"] is not None], .95),
                             "max": round(max((f["e_live"] for f in fx_ep if f["e_live"] is not None), default=0.0), 3)}
        o["eps_fix_live_ponad_freeze"] = sum(1 for f in fx_ep if f["e_live"] is not None and f["kosz"] is not None
                                             and f["e_live"] > NS.EPS_FIX_FREEZE[int(f["kosz"])])
        el = {f["seq"]: f["e_live"] for f in fx_ep if f["e_live"] is not None}
        ul = [el[r["seq"]] + eps_b[min(int(max(r["tau"], 0)), len(eps_b) - 1)] + dd5 for r in rmis
              if r.get("seq") in el and r.get("tau") is not None]
        o["u_live_max"] = round(max(ul), 4) if ul else None
        if len(dpsi) >= 5:
            t_, y_ = np.array([x[0] for x in dpsi]), np.array([x[1] for x in dpsi])
            o["bias_kursu"] = {"n": len(dpsi), "p50": round(float(np.median(y_)), 3), "trend_deg_s": round(float(np.polyfit(t_ - t_[0], y_, 1)[0]), 4)}
        else:
            o["bias_kursu"] = {"n": len(dpsi)}
        # (g) okna
        fxw = [f for f in fx_ep]
        o["g_3d"] = okna(fxw, em3, e3, m2s, eps_b, t_flag if c_ep else None, t_desc, 3)
        o["g_2d"] = okna(fxw, em2, e2, m2s, eps_b, t_flag if c_ep else None, t_desc, 2)
        o["g_ok"] = o["g_3d"]["przekroczenia_misja"] == 0
        if c_ep is not None:
            o.update(t_cut=c_ep["sim"], t_flag=t_flag, t_zejscia=t_desc, t_land=land["sim"] if land else None,
                     zejscie_planowe=zp is not None, refuse_ev=({k: ref.get(k) for k in ("sim", "rule", "cause", "t_kont", "R_k", "r_est")} if ref else None))
            o["kontynuacja_s"] = round(t_desc - c_ep["sim"], 3) if t_desc is not None else None
            o["kontynuacja_od_flagi_s"] = round(t_desc - t_flag, 3) if (t_desc is not None and t_flag is not None) else None
            win = [r for r in rows if t_flag is not None and t_desc is not None and t_flag <= r["sim"] <= t_desc and not r.get("desc")]
            gmono = np.array([g["mono"] for g in gt])
            dgt = []
            for r in win:
                if r.get("intr") is None:
                    continue
                g = gt[int(np.clip(np.searchsorted(gmono, r["mono"]), 0, len(gt) - 1))]
                own = gz_to_ned([g["x"], g["y"], g["z"]])
                dgt.append(math.hypot(own[0] - r["intr"][0], own[1] - r["intr"][1]))
            o["frac_track"] = round(float(np.mean([r["trk_valid"] for r in win])), 3) if win else 0.0
            o["frac_pasmo"] = round(float(np.mean([BAND[0] <= x <= BAND[1] for x in dgt])), 3) if dgt else 0.0
            o["d_gt_p50"] = round(float(np.median(dgt)), 2) if dgt else None
            o["a_ok"] = (zp is not None and o["kontynuacja_s"] is not None and o["kontynuacja_s"] >= T_CONT
                         and o["refuse_misja"]["n"] == 0 and o["frac_track"] >= FRAC_MIN and o["frac_pasmo"] >= FRAC_MIN)
            if u is not None and t_flag is not None and land is not None:
                nv = nav_ok(u["vehicle_status"], t_flag, land["sim"])
                lp = u["vehicle_local_position"]
                lt = lp["timestamp"] / 1e6
                m2 = (lt >= t_flag) & (lt <= (t_desc if t_desc is not None else t_flag))
                o["xy_valid_do_zejscia"] = bool(m2.any()) and bool((lp["xy_valid"][m2] == 1).all())
            else:
                nv = {"ok": False, "uwaga": "brak ulogu, flagi albo przyziemienia"}
                o["xy_valid_do_zejscia"] = False
            o["d"] = nv
            o["d_ok"] = nv["ok"]
            o["litera_ok"] = all(o[k] for k in ("a_ok", "b_ok", "c_ok", "d_ok", "e_ok", "g_ok"))
        else:
            if u is not None and en is not None:
                nv = nav_ok(u["vehicle_status"], t0, en["sim"])
            else:
                nv = {"ok": False, "uwaga": "brak ulogu albo końca epizodu"}
            o["d"] = nv
            o["d_ok"] = nv["ok"]
            o["f_ok"] = o["kont_ticki_nie_nominal"] == 0 and o["refuse_misja"]["n"] == 0 and sum(1 for r in rows if r["dec"] == "REFUSE") == 0
            o["litera_ok"] = o["f_ok"]
        eps_out.append(o)
    res["epizody"] = eps_out
    pw = []
    if not res["przyrzad_selftest"]:
        pw.append("selftest GT")
    for o in eps_out:
        if not o["v2p_ok"]:
            pw.append(f"V2p {o['scenario_id']} {(o['v2p'] or {}).get('dsim_dwall')}")
        if o["ciecie"] and not o.get("xy_valid_do_zejscia"):
            pw.append(f"xy_valid {o['scenario_id']}")
    if res["zegar_ok"] is False:
        pw.append("zegar")
    res["wazny"] = not pw
    res["powod_niewazny"] = "; ".join(pw) or None
    res["litera_ok"] = bool(eps_out) and all(o["litera_ok"] for o in eps_out)
    json.dump(res, open(os.path.join(d, "wyniki_nadir_s4.json"), "w"), ensure_ascii=False, indent=1, default=str)
    return res


def main():
    for d in sys.argv[1:]:
        r = analyze(d)
        print(r["boot"], "ważny", r["wazny"], r["powod_niewazny"], "litera", r.get("litera_ok"))
        for o in r["epizody"]:
            print(" ", o["scenario_id"], {k: o.get(k) for k in ("a_ok", "b_ok", "c_ok", "d_ok", "e_ok", "f_ok", "g_ok", "kontynuacja_s",
                                                                 "u_max_do_m", "margines_min_R_E", "frac_track", "frac_pasmo",
                                                                 "koszt_bariery_refuse", "koszt_kontrfaktyczny_ticki", "t_entry")},
                  "τ", o["tau"], "g3d", o["g_3d"]["przekroczenia_misja"], o["g_3d"]["bez_GNSS"]["max_inc_do_eps_b"],
                  "g2d", o["g_2d"]["bez_GNSS"]["max_inc_do_eps_b"], flush=True)


if __name__ == "__main__":
    main()
