#!/usr/bin/env python3
"""results/NAD2_RECON/tools/nad2_r5.py — PROMPT_NAD2_S0 R5: tabela kandydacka U(τ, koszyk, tryb) i replay osłony (0 bootów).

Obwiednia: U = z · (F(koszyk, tryb) + G(τ)), u′ = U + Δ_D5; z ∈ {A: 1.5, B: 1.25} mnoży oba składniki (max). F = max błędu
zakotwiczenia a (R3) wariantu w oknie bez GNSS 12 cięć S4 (poziomo); G = maksimum bieżące przyrostu EKF (R2, poziomo, okno
przesuwne). Przedziały τ: [0, .25], (.25, .45], (.45, .65], (.65, .85], (.85, 1.05], potem co 1 s do 22 s; G przedziału = G_kum
górnej krawędzi. Monotoniczność: G rosnące z konstrukcji; F maksimum bieżące po koszyku; komórka (koszyk, tryb) o n < 100
dziedziczy F najbliższego wyższego koszyka tego trybu o n ≥ 100; gdy takiego brak — F = max puli trybu (wszystkie koszyki),
oznaczone „pula” (odstępstwo nazwane w raporcie).
τ*(koszyk, tryb) = górna krawędź ostatniego przedziału (od zera, bez przerw) z u′ ≤ m_p50 = 5.79 (reguła PRE §3); REFUSE(τ*)
przy τ ≥ τ* − 2·dt (dt = 0.05).
Replay per tick (rama.jsonl, faza misji, od flagi utraty GNSS do zejścia) cięcia: poprawka wariantu = ostatnia przyjęta klatka
replayu R3 dostępna w chwili ticku po zegarze mono: mono przybycia klatki + czas detekcji + EPS_DOST ≤ mono ticku (kalibracja na
zapisie T0Z0C0: EPS_DOST = 5 ms daje 2 z 27 241 ticków, w których replay widzi poprawkę wcześniej niż rama w locie, i ~1.6% ticków
ostrożniejszych o jedną klatkę; t_frame ≤ sim dawało ~10% ticków optymistycznych — odrzucone); τ_osł = sim − t_fix′,
τ_prawd = t_próbki EKF ticku (R1a) − t_a′; przedział wybiera max(τ_osł, τ_prawd). p_corr′ = p_EKF + (p_fix′ − p_anchor′).
Bariera: REFUSE ⇔ τ_osł ≥ τ* − 2·dt ∨ r_est > R_E − d_stop − u′; r_est w dwóch wersjach: „lot” = |p_EKF| (tak liczyła
osłona w S4: driver podaje jej own = EKF bez Δ) i „przesłanka” = |p_corr′| (tę wielkość zakłada P9_nadir). Komórka dostępna ⇔
zero REFUSE w fazach misji ∧ zero ticków u′ > m (wersja „przesłanka” rozstrzyga; „lot” obok).
(iii) τ dopuszczalne per komórka: największa krawędź z u′ ≤ m (para / jeden, najgorszy koszyk ⇒ liczba klatek 5 Hz).
(iv) tabela statyczna 48 komórek r4_margin: u′(τ ≤ 0.25) najgorszego dopuszczonego (koszyk, tryb) wobec m.
(v) sprawdzian e_corr′ ≤ U na 4 cięciach S2 (dane spoza FREEZE) i zapas max e_corr′/U na S4.
Wyjście: results/NAD2_RECON/r5_tabela.json.
"""
import bisect
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nad2_dane as D
import nad2_r3 as R3

R_E, D_STOP, DD5, M_P50, DT = 32.0, 2.85, 1.524, 5.79, 0.05
EPS_DOST = 0.005
KRAW = [0.25, 0.45, 0.65, 0.85, 1.05] + [float(k) for k in range(2, 23)]
REGULY = {"A": 1.5, "B": 1.25}
N_MIN = 100


def przedzial(tau):
    i = bisect.bisect_left(KRAW, tau - 1e-9)
    return min(i, len(KRAW) - 1) if tau <= KRAW[-1] else None


def obwiednia_F(rek_s4, kosze):
    """F[tryb][kosz] z okna bez GNSS 12 cięć S4 (błąd zakotwiczenia a, poziomo) + dziedziczenie n < 100 + monotoniczność."""
    surowe = {"para": {k: [] for k in kosze}, "jeden": {k: [] for k in kosze}}
    for rek in rek_s4.values():
        for x in rek:
            if x["ok"] and x["misja"] and x["klasa"] == "bez_GNSS":
                surowe[x["tryb"]][x["kosz"]].append(x["a"])
    F, opis = {}, {}
    for tr, d in surowe.items():
        F[tr], opis[tr] = {}, {}
        pula = [v for k in kosze for v in d[k]]
        for k in kosze:
            if len(d[k]) >= N_MIN:
                F[tr][k], src = max(d[k]), "wlasna"
            else:
                wyz = [kk for kk in kosze if kk > k and len(d[kk]) >= N_MIN]
                if wyz:
                    F[tr][k], src = max(d[wyz[0]]), f"dziedziczy_{wyz[0]}"
                else:
                    F[tr][k], src = (max(pula) if pula else max(max(v) for v in surowe["para"].values() if v)), f"pula_trybu_n{len(pula)}"
            opis[tr][k] = {"n": len(d[k]), "max_wlasny": round(max(d[k]), 4) if d[k] else None, "zrodlo": src}
        bieg = 0.0
        for k in kosze:
            bieg = max(bieg, F[tr][k]); F[tr][k] = bieg
            opis[tr][k]["F"] = round(bieg, 4)
    return F, opis


def tablica(F, G, z, kosze):
    """u′[tryb][kosz][i] i τ*[tryb][kosz]."""
    u, ts = {}, {}
    for tr in F:
        u[tr], ts[tr] = {}, {}
        for k in kosze:
            u[tr][k] = [z * (F[tr][k] + G[i]) + DD5 for i in range(len(KRAW))]
            last = None
            for i, x in enumerate(u[tr][k]):
                if x <= M_P50:
                    last = i
                else:
                    break
            ts[tr][k] = KRAW[last] if last is not None else 0.0
    return u, ts


def ticki(b, rek):
    """Ticki misji od flagi do zejścia z poprawką wariantu (ostatnia przyjęta klatka z t_frame ≤ sim)."""
    fixy = [x for x in rek if x["ok"]]
    av = [x["mono"] + x["ms"] / 1000.0 + EPS_DOST for x in fixy]
    ep = b.denial["episode_id"]
    t_end = b.zp.get(ep)
    if t_end is None:
        ref = [e["sim"] for e in b.ev if e.get("ev") == "refuse" and e.get("episode_id", ep) == ep]
        t_end = min(ref) if ref else 1e18
    out = []
    for r in b.rama:
        if r.get("ep") != ep or r["sim"] < b.t_flag or r["sim"] >= t_end or r.get("phase") not in D.MISJA or r.get("desc"):
            continue
        i = bisect.bisect_right(av, r["mono"]) - 1
        if i < 0:
            continue
        f = fixy[i]
        k, d = b.dopasuj(r["p_ekf"], r["sim"])
        t_s = float(b.vts[k]) if k is not None else r["sim"]
        pe = np.array(r["p_ekf"])
        dne = np.array(f["p_fix"]) - np.array(f["p_anchor"][:2])
        pc = pe[:2] + dne
        g = b.gt(t_s)[0][:2]
        out.append({"sim": r["sim"], "tau_osl": max(0.0, r["sim"] - f["t_frame"]), "tau_prawd": max(0.0, t_s - f["t_a"]),
                    "tryb": f["tryb"], "kosz": f["kosz"], "t_fix": f["t_frame"], "r_lot": float(np.hypot(pe[0], pe[1])),
                    "r_prz": float(np.hypot(pc[0], pc[1])), "e_corr": float(np.linalg.norm(pc - g)), "tau_zapis": r.get("tau"),
                    "t_fix_zapis": r.get("t_fix")})
    return out


def ocen(tk, u, ts, z, F, G, m):
    """Replay osłony na tickach jednej komórki."""
    o = {"n": len(tk), "refuse_prz": 0, "refuse_lot": 0, "u_gt_m": 0, "zapas_min_prz": None, "zapas_min_lot": None,
         "pierwszy_refuse_prz": None, "premisa_przekr": 0, "max_e_do_U": 0.0, "tau_max": 0.0, "przedzial_max": 0}
    for t in tk:
        tau = max(t["tau_osl"], t["tau_prawd"])
        i = przedzial(tau)
        o["tau_max"] = max(o["tau_max"], tau)
        tr, k = t["tryb"], t["kosz"]
        if i is None:
            o["refuse_prz"] += 1; o["refuse_lot"] += 1; o["u_gt_m"] += 1
            continue
        o["przedzial_max"] = max(o["przedzial_max"], i)
        uu = u[tr][k][i]
        U = uu - DD5
        if m is not None and uu > m:
            o["u_gt_m"] += 1
        Rb = R_E - D_STOP - uu
        tstar = t["tau_osl"] >= ts[tr][k] - 2 * DT
        for wer, r in (("prz", t["r_prz"]), ("lot", t["r_lot"])):
            if tstar or r > Rb:
                o[f"refuse_{wer}"] += 1
                if wer == "prz" and o["pierwszy_refuse_prz"] is None:
                    o["pierwszy_refuse_prz"] = {"sim": t["sim"], "tau": round(tau, 3), "przyczyna": "τ*" if tstar else "bariera"}
            zap = Rb - r
            key = f"zapas_min_{wer}"
            o[key] = zap if o[key] is None else min(o[key], zap)
        e_ratio = t["e_corr"] / U if U > 0 else float("inf")
        o["max_e_do_U"] = max(o["max_e_do_U"], e_ratio)
        o["premisa_przekr"] += int(t["e_corr"] > U)
    for k in ("zapas_min_prz", "zapas_min_lot", "max_e_do_U", "tau_max"):
        if o[k] is not None:
            o[k] = round(o[k], 4)
    o["dostepna"] = o["refuse_prz"] == 0 and o["u_gt_m"] == 0
    o["dostepna_lot"] = o["refuse_lot"] == 0 and o["u_gt_m"] == 0
    return o


def main():
    r1 = json.load(open(os.path.join(D.OUT, "r1_czas.json")))
    r2 = json.load(open(os.path.join(D.OUT, "r2_przyrost.json")))
    G = [r2["G_kum"]["poziomo"][str(k)] for k in KRAW]
    G3 = [r2["G_kum"]["3d"][str(k)] for k in KRAW]
    B4 = {n: D.Boot(n) for n in D.CIECIA_S4}
    B2 = {n: D.Boot(n, D.S2) for n in D.CIECIA_S2}
    scen = {n: b.scen[b.denial["episode_id"]] for n, b in {**B4, **B2}.items()}
    out = {"stale": {"R_E": R_E, "d_stop": D_STOP, "delta_D5": DD5, "m_p50": M_P50, "krawedzie_tau": KRAW, "G_poziomo": G, "G_3d_info": G3,
                     "N_MIN": N_MIN, "reguly": REGULY}, "warianty": {}}
    # kalibracja: T0Z0C0 ⇒ t_fix′ = zapisane t_fix ramy
    cal = []
    for T, Z, C in R3.WARIANTY:
        name = f"{T}{Z}{C}"
        kosze = [0, 1, 2, 3, 4] if Z == "Z2" else [0, 1, 2, 3]
        rek4 = {n: R3.replay(b, T, Z, C, gt_id=False) for n, b in B4.items()}
        rek2 = {n: R3.replay(b, T, Z, C, gt_id=False) for n, b in B2.items()}
        F, Fopis = obwiednia_F(rek4, kosze)
        tk4 = {n: ticki(b, rek4[n]) for n, b in B4.items()}
        tk2 = {n: ticki(b, rek2[n]) for n, b in B2.items()}
        if name == "T0Z0C0":
            for n, tk in tk4.items():
                zz = [t for t in tk if t["t_fix_zapis"] is not None]
                ok = sum(1 for t in zz if abs(t["t_fix"] - t["t_fix_zapis"]) < 1e-3)
                wcz = sum(1 for t in zz if t["t_fix"] > t["t_fix_zapis"] + 1e-3)
                cal.append({"boot": n, "zgodne": ok, "replay_wczesniej": wcz, "replay_pozniej": len(zz) - ok - wcz, "n": len(zz)})
        dist = np.array([t["tau_prawd"] - t["tau_osl"] for tk in tk4.values() for t in tk])
        ow = {"F": Fopis, "tau_prawd_minus_tau_osl": D.rozklad(dist), "reguly": {}}
        for rn, z in REGULY.items():
            u, ts = tablica(F, G, z, kosze)
            cel = {}
            for n, tk in tk4.items():
                cel[scen[n]] = ocen(tk, u, ts, z, F, G, D.MARG[scen[n]]["m"])
                cel[scen[n]]["boot"] = n
            dost = sorted(s for s, c in cel.items() if c["dostepna"])
            niedost = sorted(s for s, c in cel.items() if not c["dostepna"])
            s1 = len(dost) < 10
            s2 = any(s not in ("c08_s02", "c11_s02") for s in niedost)
            # (iii) τ dopuszczalne: najgorszy koszyk trybu
            tdop = {}
            for s in cel:
                m = D.MARG[s]["m"]
                tdop[s] = {}
                for tr in ("para", "jeden"):
                    kw = max(kosze, key=lambda k: F[tr][k])
                    last = None
                    for i in range(len(KRAW)):
                        if u[tr][kw][i] <= m:
                            last = i
                        else:
                            break
                    tdop[s][tr] = {"tau_s": KRAW[last] if last is not None else 0.0,
                                   "klatki_5Hz": int(math.floor((KRAW[last] if last is not None else 0.0) / 0.2 + 1e-9))}
            # (iv) tabela statyczna 48 komórek
            uw = max(u[tr][k][0] for tr in u for k in kosze)
            stat = {s: {"m": v["m"], "u0_najgorszy": round(uw, 3), "zapas": round(v["m"] - uw, 3)} for s, v in D.MARG.items()}
            # (v) sprawdzian S2 — ten sam rachunek przesłanki na danych spoza FREEZE
            s2c = {}
            for n, tk in tk2.items():
                c = ocen(tk, u, ts, z, F, G, D.MARG[scen[n]]["m"])
                s2c[n] = {"n": c["n"], "premisa_przekr": c["premisa_przekr"], "max_e_do_U": c["max_e_do_U"], "refuse_prz": c["refuse_prz"],
                          "tau_max": c["tau_max"]}
            ow["reguly"][rn] = {"tau_star": {tr: {str(k): v for k, v in d.items()} for tr, d in ts.items()},
                                "u0": {tr: {str(k): round(u[tr][k][0], 3) for k in kosze} for tr in u},
                                "komorki": cel, "dostepne": dost, "niedostepne": niedost, "n_dostepnych": len(dost),
                                "S1": s1, "S2": s2, "zywa": not s1 and not s2,
                                "n_dostepnych_lot": sum(1 for c in cel.values() if c["dostepna_lot"]),
                                "tau_dopuszczalne": tdop, "statyczna_48": stat,
                                "sprawdzian_S2": s2c, "zapas_S4_max_e_do_U": round(max(c["max_e_do_U"] for c in cel.values()), 4)}
            print(name, rn, "dostępne", len(dost), "niedost", niedost, "Ś1", s1, "Ś2", s2, "lot", ow["reguly"][rn]["n_dostepnych_lot"],
                  "S2 przekr", {n: v["premisa_przekr"] for n, v in s2c.items()}, "S4 e/U", ow["reguly"][rn]["zapas_S4_max_e_do_U"], flush=True)
        out["warianty"][name] = ow
    out["kalibracja_t_fix_T0Z0C0"] = cal
    # reguła wyboru PROMPT_NAD2_S0 §2
    os_c = r1["regula_osi_czasu"]["wybor"]
    kol = [("T0", "Z0"), ("T1", "Z0"), ("T1", "Z1"), ("T1", "Z2"), ("T0", "Z1"), ("T0", "Z2")]
    zywe_A = [f"{t}{z}{c}" for (t, z, c) in R3.WARIANTY if out["warianty"][f"{t}{z}{c}"]["reguly"]["A"]["zywa"]]
    reg = "A" if zywe_A else "B"
    kand = [f"{t}{z}{os_c}" for t, z in kol]
    best = max(kand, key=lambda v: (out["warianty"][v]["reguly"][reg]["n_dostepnych"], -kand.index(v)))
    out["wybor"] = {"os_czasu": os_c, "regula": reg, "zywe_przy_A": zywe_A,
                    "zywe_przy_B": [f"{t}{z}{c}" for (t, z, c) in R3.WARIANTY if out["warianty"][f"{t}{z}{c}"]["reguly"]["B"]["zywa"]],
                    "wariant": best, "n_dostepnych": out["warianty"][best]["reguly"][reg]["n_dostepnych"],
                    "zywy": out["warianty"][best]["reguly"][reg]["zywa"],
                    "kierunek_umiera": not any(out["warianty"][v]["reguly"][r]["zywa"] for v in out["warianty"] for r in REGULY)}
    json.dump(out, open(os.path.join(D.OUT, "r5_tabela.json"), "w"), ensure_ascii=False, indent=1)
    print("KALIBRACJA", cal)
    print("WYBOR", out["wybor"])


if __name__ == "__main__":
    main()
