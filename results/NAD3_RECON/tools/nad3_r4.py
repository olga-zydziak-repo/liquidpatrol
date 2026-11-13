#!/usr/bin/env python3
"""results/NAD3_RECON/tools/nad3_r4.py — PROMPT_NAD3_S0 R4 + R5: replay degradacji na 13 zapisanych lotach NAD2 (0 bootów).

Wierność (najpierw, STOP przy braku):
  (A) producent: harness/nadir_fix.Rama(litera NAD2) na wierszach nf nadir_obs.jsonl (detekcje + migawka EKF) odtwarza zapisane fx:
      ok, tryb, ids, kosz, t_fix, |Δd_ne| i |Δp_fix| ≤ 5e-5 m;
  (B) konsument + bramka: strumień fx (po seq) → nad3_degrad.Degradacja w trybie passthrough ORAZ {model: zero} (E_max = 0,
      pełna częstość, K = 0) → emulacja RamaKlient (d_ne, t_fix z ostatniego datagramu, kosz/tryb z ostatniego ok) w seq ticku
      (rama.jsonl: seq) → bariera osłony r03/nadir_shield._nad2_barrier (funkcje przedzial_nad2, r_nad2, stałe; reguła
      zatrzasku przepisana 1:1 z :174-193) → porównanie per tick utraty z zapisem: d_ne, τ, przedział, R_k, zatrzask REFUSE.
Degradacja: ten sam łańcuch z konfiguracją modelu; tabela U′ przeliczona regułą R1 (krawędzie τ i G z r5_tabela do 22 s,
  (a) U′ = 1.5·(F_zn(koszyk, tryb) + E_max + G), (b) U′ = 1.5·(F_zn + G) + E_max); τ_proj(f, K) = max τ zrealizowane w misji
  przy E = 0 na 13 lotach (siatka 5 Hz: przerwa 1/f zaokrąglona w górę do 0.2 s + opóźnienie dostarczenia), τ*′ = τ_proj + 2·dt
  + 1 ms (parametr, nie krawędź tabeli), REFUSE(τ*) przy τ ≥ τ*′ − 2·dt; przedział z τ + 0.012 s (jak osłona). Miary na tickach utraty w misji:
  ticki e′ > U′, max e′/U′, REFUSE (zatrzask w misji: tak/nie, przyczyna, czas od flagi), min zapas osłony R′ − r_est′ (ticki
  ALLOW), min zapas prawdziwy (R_E − d_stop − Δ_D5) − r_GT, τ max zrealizowane; R5: |ΔΔ| na dostarczoną poprawkę.
Punkty R4 per lot: r = r_max misji po fladze (r2_promien.json), granica E_b = E_max(a|b)(r, f, K) z F_zn najgorszym (jeden
  0.4527) i G przedziału τ_proj, punkty E_b − 0.5, E_b, E_b + 0.5 (obcięte do ≥ 0; E_b < 0 ⇒ „niewykonalne przy r lotu”)
  oraz „dost” = granica dostępności (u′ + E ≤ m: bias na zewnątrz przesuwa r_est o E).
Pętla otwarta: tor drona, EKF, GT i percepcja są z zapisu — replay nie widzi reakcji sieci i osłony na zdegradowaną ramę.
Wyjście: results/NAD3_RECON/r4_wiernosc.json, r4_replay.json, r5_skok.json.
"""
import json
import math
import os
import sys

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.dirname(os.path.abspath(__file__))]
import nad3_dane as N
import nad3_degrad as DG
from harness.nadir_fix import Rama
from r03 import nadir_shield as NS

T5 = json.load(open(os.path.join(ROOT, "results/NAD2_RECON/r5_tabela.json")))["stale"]
KRAW_X, G_X = list(T5["krawedzie_tau"]), list(T5["G_poziomo"])
DT = 0.05
EPS = NS.TAU_EPS_NAD2
F_ZN_WORST = max(NS.F_NAD2["jeden"])
R_E = T5["R_E"]                                    # = cfg.r_e osłony (r01 config)
MODELE = [("bias_do_srodka", {"model": "bias_rad", "kierunek": "do_srodka"}),
          ("bias_na_zewnatrz", {"model": "bias_rad", "kierunek": "na_zewnatrz"}),
          ("bialy", {"model": "bialy"}), ("wolny_2s", {"model": "wolny", "T_c": 2.0}), ("wolny_10s", {"model": "wolny", "T_c": 10.0})]
FK = [(4, 0), (2, 0), (1, 0), (1, 1)]


# ---------------- wierność A: producent ----------------
def wiernosc_A(L):
    R = Rama(litera="NAD2")
    n = zle = 0
    max_d = 0.0
    przyklad = None
    for row in L.nf:
        fx = R.obserwacja(row["sim"], row["det"], row["ekf_q"], row["ekf_pos"])
        z = row["fx"]
        n += 1
        ok = fx["ok"] == z["ok"] and fx.get("tryb") == z.get("tryb") and fx.get("ids") == z.get("ids") and \
            fx.get("kosz") == z.get("kosz") and fx.get("t_fix") == z.get("t_fix") and fx["seq"] == z["seq"]
        d = max(abs(a - b) for a, b in zip(fx["d_ne"], z["d_ne"]))
        if fx.get("p_fix_ne") is not None and z.get("p_fix_ne") is not None:
            d = max(d, max(abs(a - b) for a, b in zip(fx["p_fix_ne"], z["p_fix_ne"])))
        max_d = max(max_d, d)
        if not ok or d > 5e-5:
            zle += 1
            if przyklad is None:
                przyklad = {"seq": z["seq"], "zapis": {k: z.get(k) for k in ("ok", "tryb", "ids", "kosz", "d_ne")},
                            "replay": {k: fx.get(k) for k in ("ok", "tryb", "ids", "kosz", "d_ne")}}
    return {"n_fx": n, "niezgodne": zle, "max_abs_d": round(max_d, 7), "zgodnosc": round(1 - zle / max(n, 1), 6), "przyklad": przyklad}


# ---------------- łańcuch: degradacja → klient → stan per tick ----------------
def strumien(L):
    return [L.fx[s] for s in sorted(L.fx)]


def klient(L, cfg, passthrough=False):
    """Przetworzony strumień → stan klienta po każdym seq: dict seq → (dn, de, t_fix, kosz, tryb); oraz lista dostarczonych."""
    dg = DG.Degradacja(None if passthrough else cfg)
    st = {}
    dn = de = 0.0
    tf = kz = tr = None
    dost = []
    for fx in strumien(L):
        o = dg.przetworz(fx)
        if passthrough:
            assert o is fx
        dn, de, tf = o["d_ne"][0], o["d_ne"][1], o["t_fix"]
        if o.get("ok"):
            kz, tr = o.get("kosz"), o.get("tryb")
            dost.append((float(o["t_frame"]), dn, de))
        st[o["seq"]] = (dn, de, tf, kz, tr)
    return st, dost


def stan_tickow(L, st):
    tu = L.tu
    s_sorted = np.array(sorted(st))
    idx = np.searchsorted(s_sorted, tu["seq"], side="right") - 1
    rows = [st[s_sorted[i]] if i >= 0 else (0.0, 0.0, None, None, None) for i in idx]
    d = np.array([[r[0], r[1]] for r in rows])
    tf = np.array([np.nan if r[2] is None else r[2] for r in rows])
    return d, tf, [r[3] for r in rows], [r[4] for r in rows]


def przedzial(tau, kraw):
    t = tau + EPS
    i = np.searchsorted(np.array(kraw), t - 1e-12, side="left")
    return np.where(i < len(kraw), i, -1)


def bariera(L, d, tf, kz, tr, tabela):
    """Zatrzask osłony na tickach utraty (emulacja _nad2_barrier). tabela: kraw, G, F(k, tr)->F, E_add, wariant, tau_star."""
    tu = L.tu
    sim = tu["sim"]
    t0 = sim[0]
    brak = np.isnan(tf)
    tau = np.maximum(0.0, sim - np.where(brak, t0, tf))
    i = przedzial(tau, tabela["kraw"])
    kk = np.array([NS.POLE_BRAK_NAD2[1] if (b or k is None) else k for b, k in zip(brak, kz)])
    tt = [NS.POLE_BRAK_NAD2[0] if (b or t is None) else (t if t in NS.TRYBY_NAD2 else "jeden") for b, t in zip(brak, tr)]
    F = np.array([NS.F_NAD2[t][k] for t, k in zip(tt, kk)])
    G = np.array([tabela["G"][x] if x >= 0 else np.nan for x in i])
    E = tabela["E"]
    if tabela["wariant"] == "a":
        U = NS.ZAPAS_NAD2 * (F + E + G)
    else:
        U = NS.ZAPAS_NAD2 * (F + G) + E
    R = R_E - NS.D_STOP - (U + NS.DELTA_D5)
    pc = tu["p_ekf"][:, :2] + d
    r_est = np.hypot(pc[:, 0], pc[:, 1])
    war = (tau >= tabela["tau_star"] - NS.T_MARGIN_TICKS * DT) | (i < 0) | (r_est > R)
    k_latch = int(np.argmax(war)) if war.any() else None
    przyczyna = None
    if k_latch is not None:
        przyczyna = "τ*" if (tau[k_latch] >= tabela["tau_star"] - NS.T_MARGIN_TICKS * DT or i[k_latch] < 0) else "bariera"
    e = np.hypot(pc[:, 0] - tu["gt"][:, 0], pc[:, 1] - tu["gt"][:, 1])
    return {"tau": tau, "i": i, "U": U, "R": R, "r_est": r_est, "e": e, "k_latch": k_latch, "przyczyna": przyczyna, "pc": pc}


TAB_NAD2 = {"kraw": list(NS.KRAW_NAD2), "G": list(NS.G_NAD2), "E": 0.0, "wariant": "a", "tau_star": NS.TAU_STAR_NAD2}


# ---------------- wierność B ----------------
def wiernosc_B(L):
    out = {}
    tu = L.tu
    for lab, cfg, pt in (("passthrough", None, True), ("zero", {"model": "zero"}, False)):
        st, _ = klient(L, cfg, passthrough=pt)
        d, tf, kz, tr = stan_tickow(L, st)
        b = bariera(L, d, tf, kz, tr, TAB_NAD2)
        dd = float(np.abs(d - tu["d_ne"]).max())
        log_tau = np.array([np.nan if x is None else x for x in tu["tau"]])
        dtau = float(np.nanmax(np.abs(np.round(b["tau"], 4) - log_tau)))
        log_i = np.array([-1 if x is None else x for x in tu["przedzial"]])
        rep_i = np.where(b["i"] >= 0, b["i"], -1)
        zle_i = int((log_i != rep_i).sum())
        log_latch = next((k for k, p in enumerate(tu["ph"]) if p == "KONT_REFUSE"), None)
        pc_log = tu["p_corr"][:, :2]
        dpc = float(np.abs(b["pc"] - pc_log).max())
        out[lab] = {"n_tickow": int(len(tu["sim"])), "max_abs_d_ne": round(dd, 7), "max_abs_tau": round(dtau, 6),
                    "przedzial_niezgodne": zle_i, "zatrzask_zapis": log_latch, "zatrzask_replay": b["k_latch"],
                    "zatrzask_zgodny": log_latch == b["k_latch"], "max_abs_p_corr_vs_zapis_4cyfry": round(dpc, 6),
                    "max_e_do_U": round(float(np.nanmax(np.where(np.array([x is not None for x in tu["przedzial"]]),
                                                                 b["e"] / b["U"], np.nan))), 4)}
        out[lab]["ok"] = dd <= 5e-5 and dtau <= 1e-3 and zle_i == 0 and out[lab]["zatrzask_zgodny"]
    return out


# ---------------- degradacja ----------------
TAU_PROJ = {}                                       # (f, K) → max τ zrealizowane w misji przy E = 0 na 13 lotach


def tau_proj(loty):
    for f, K in FK:
        mx = 0.0
        for L in loty:
            st, _ = klient(L, {"model": "zero", "f": f, "K": K, "ziarno": 1})
            d, tf, kz, tr = stan_tickow(L, st)
            tau = L.tu["sim"] - tf
            mx = max(mx, float(np.nanmax(tau[L.tu["misja"]])))
        TAU_PROJ[(f, K)] = round(mx, 4)
    return {f"f{f}_K{K}": {"tau_cc": round((K + 1) / f + 0.05, 3), "tau_zrealizowane": v} for (f, K), v in TAU_PROJ.items()}


def tabela_deg(f, K, E, wariant):
    """τ*′ = τ_proj + 2·dt + 1 ms (parametr, nie krawędź): REFUSE(τ*) nie odpala w pracy nominalnej źródła; przedział
    najgorszy przed REFUSE = przedział τ_proj (+ 0.012 s)."""
    tp = TAU_PROJ[(f, K)]
    return {"kraw": KRAW_X, "G": G_X, "E": E, "wariant": wariant, "tau_star": round(tp + NS.T_MARGIN_TICKS * DT + 0.001, 4),
            "tau_max": tp, "i_max": int(np.searchsorted(np.array(KRAW_X), tp + 0.001 + EPS - 1e-12))}


def granica(r, f, K, wariant, dost=False):
    """E_b bezpieczeństwa (u′(τ_proj) ≤ m(r), rachunek R1) albo dostępności (dost: r_est ≤ r + E przy biasie na zewnątrz,
    czyli u′ + E ≤ m(r) — E liczy się drugi raz, bo przesuwa r_est)."""
    tab = tabela_deg(f, K, 0.0, wariant)
    m = R_E - NS.D_STOP - r
    g = G_X[tab["i_max"]]
    if wariant == "a":
        return (m - NS.DELTA_D5 - NS.ZAPAS_NAD2 * (F_ZN_WORST + g)) / (NS.ZAPAS_NAD2 + (1.0 if dost else 0.0))
    return (m - NS.DELTA_D5 - NS.ZAPAS_NAD2 * (F_ZN_WORST + g)) / (2.0 if dost else 1.0)


def miary(L, b, dost, tab):
    tu = L.tu
    ms = tu["misja"]
    ocen = ms & (b["i"] >= 0)
    eU = b["e"] / b["U"]
    kl = b["k_latch"]
    allow = np.ones(len(ms), bool)
    if kl is not None:
        allow[kl:] = False
    am = allow & ms
    rgt = np.hypot(tu["gt"][:, 0], tu["gt"][:, 1])
    refuse_misja = kl is not None and bool(ms[kl])
    dd = np.array([math.hypot(dost[k][1] - dost[k - 1][1], dost[k][2] - dost[k - 1][2]) for k in range(1, len(dost))
                   if L.t_flag <= dost[k][0] <= (L.t_zp or 1e18)])
    return {"e_gt_U": int((b["e"][ocen] > b["U"][ocen]).sum()), "max_e_do_U": round(float(np.nanmax(eU[ocen])), 4) if ocen.any() else None,
            "refuse_misja": refuse_misja, "przyczyna": b["przyczyna"] if refuse_misja else None,
            "t_refuse_od_flagi": round(float(tu["sim"][kl] - L.t_flag), 2) if refuse_misja else None,
            "zapas_oslony_min": round(float((b["R"] - b["r_est"])[am].min()), 3) if am.any() else None,
            "zapas_prawdziwy_min": round(float((R_E - NS.D_STOP - NS.DELTA_D5 - rgt)[ms].min()), 3),
            "tau_max_misja": round(float(b["tau"][ms].max()), 3), "tau_star": tab["tau_star"],
            "skok": N.rozklad(dd)}


def przebieg(L, cfg, tab):
    st, dost = klient(L, cfg)
    d, tf, kz, tr = stan_tickow(L, st)
    b = bariera(L, d, tf, kz, tr, tab)
    return miary(L, b, dost, tab)


def main():
    R2 = json.load(open(os.path.join(N.OUT, "r2_promien.json")))["loty"]
    wA, wB = {}, {}
    loty = [N.wczytaj(*x) for x in N.loty()]
    for L in loty:
        wA[L.nazwa] = wiernosc_A(L)
        wB[L.nazwa] = wiernosc_B(L)
        print("wiernosc", L.nazwa, wA[L.nazwa]["zgodnosc"], wA[L.nazwa]["max_abs_d"], {k: v["ok"] for k, v in wB[L.nazwa].items()},
              wB[L.nazwa]["passthrough"]["max_e_do_U"], flush=True)
    ok = all(v["zgodnosc"] == 1.0 for v in wA.values()) and all(v[k]["ok"] for v in wB.values() for k in v)
    json.dump({"A_producent": wA, "B_klient_bramka": wB, "PASS": ok}, open(os.path.join(N.OUT, "r4_wiernosc.json"), "w"),
              ensure_ascii=False, indent=1)
    if not ok:
        print("WIERNOŚĆ < 100% — STOP przed degradacją")
        return
    tp = tau_proj(loty)
    print("tau_proj", tp, flush=True)
    # R4: punkty granicy
    rep = {"_tau_proj": tp}
    for L in loty:
        r = R2[L.nazwa]["r_max_misja_po_fladze"]
        for wariant in ("a", "b"):
            for f, K in FK:
                ebs = granica(r, f, K, wariant)
                ebd = granica(r, f, K, wariant, dost=True)
                for lab, eb, dE in (("pod", ebs, -0.5), ("granica", ebs, 0.0), ("nad", ebs, 0.5), ("dost", ebd, 0.0)):
                    E = max(0.0, eb + dE)
                    tab = tabela_deg(f, K, E, wariant)
                    for mn, mc in MODELE:
                        cfg = dict(mc, E_max=E, f=f, K=K, ziarno=1)
                        m = przebieg(L, cfg, tab)
                        m.pop("skok")
                        rep.setdefault(L.nazwa, []).append({"wariant": wariant, "f": f, "K": K, "punkt": lab, "r": r,
                                                            "E_b": round(eb, 4), "E": round(E, 4), "wykonalne": eb > 0,
                                                            "model": mn, **m})
        print("R4", L.nazwa, flush=True)
    json.dump(rep, open(os.path.join(N.OUT, "r4_replay.json"), "w"), ensure_ascii=False, indent=1)
    # R5: skok nastawy
    sk = {}
    for L in loty:
        o = {"naturalny_5Hz": przebieg(L, {"model": "zero"}, TAB_NAD2)["skok"]}
        for f in (4, 1):
            if (f, 0) not in TAU_PROJ:
                continue
            o[f"zero_f{f}"] = przebieg(L, {"model": "zero", "f": f}, tabela_deg(f, 0, 0.0, "a"))["skok"]
            for E in (1, 2, 3):
                for mn, mc in MODELE:
                    o[f"{mn}_E{E}_f{f}"] = przebieg(L, dict(mc, E_max=E, f=f, K=0, ziarno=1), tabela_deg(f, 0, E, "a"))["skok"]
        sk[L.nazwa] = o
        print("R5", L.nazwa, o["naturalny_5Hz"], o["bialy_E2_f1"], flush=True)
    json.dump(sk, open(os.path.join(N.OUT, "r5_skok.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
