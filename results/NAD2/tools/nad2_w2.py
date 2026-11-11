#!/usr/bin/env python3
"""results/NAD2/tools/nad2_w2.py — PROMPT_NAD2_S1 §R W2: replay S4 nową literą i tabelą (0 bootów; ANEKS_NAD2-1 §1.3 odniesienie).

Kod PRODUKCYJNY w pętli: harness/nadir_fix.Rama(litera="NAD2") na zapisanych klatkach nf (dostępność poprawki w ticku po mono
przybycia + detekcja + 5 ms — recon R5), osłona r03/nadir_shield.NadirShield(nadir_mode=1, nad2=1) wołana przez driverową
ścieżkę results/NAD2/tools/nad2_krok.krok z pozycją/celem w obu ramach (p_EKF, sp_EKF z rama.jsonl; p_corr′ = p_EKF + Δ′,
cel′ = sp_EKF + Δ′), cs_gnss_pos i pos_flag z tk, now = sim. Per cięcie, ticki fazy misji przed zejściem:
  (B1) e_corr = |p_corr′ − GT(timestamp_sample próbki EKF ticku)| poziomo wobec U PRZEDZIAŁU UŻYTEGO PRZEZ OSŁONĘ (ticki utraty);
  max e_corr/U; REFUSE (liczba, reguły); zapas bariery min (R − r_est osłony); ticki trybu „jeden” w utracie; obserwabla
  horyzont prawdziwy − (τ + 0.012 s) (oczekiwanie ≤ 0); (B3) r_est osłony = |p_corr′| (1e-6) w tickach utraty.
Wyjście: results/NAD2/s1/w2_replay.json.
"""
import bisect
import json
import math
import os
import sys

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/NAD2_RECON/tools"), os.path.join(ROOT, "results/NAD2/tools")]
import nad2_dane as D
import nad2_krok
from harness import nadir_fix as NF
from r03 import nadir_shield as NS

EPS_DOST = 0.005


class _Rama:
    t_fix = kosz = tryb = None


def replay(n, rama_out=None):
    b = D.Boot(n)
    tk = {r["tick"]: r for r in D.jl(os.path.join(b.d, "trace.jsonl"), "tk")}
    demo = {r["tick"]: r for r in D.jl(os.path.join(b.d, "demo.jsonl"))}
    rv = NF.Rama(litera="NAD2")
    fixy = []
    for r in b.nf:
        fx = rv.obserwacja(r["sim"], r["det"], r.get("ekf_q"), r.get("ekf_pos"))
        if fx["ok"]:
            fixy.append((r["mono"] + r.get("ms", 0.0) / 1000.0 + EPS_DOST, fx["t_frame"], fx["kosz"], fx["tryb"], list(rv.d_ne),
                         r["ekf_pos"]))
    av = [f[0] for f in fixy]
    sh = NS.NadirShield(kont_mode=True, nadir_mode=True, nad2=True); sh.reset()
    rama = _Rama()
    o = {"n_ticki_utraty_misja": 0, "B1_przekroczenia": 0, "max_e_do_U": 0.0, "refuse": 0, "refuse_reguly": {}, "zapas_min": None,
         "ticki_jeden": 0, "B3_zle": 0, "horyzont_minus_tau_eps_max": None, "przedzialy": {}, "e_corr_max": 0.0, "pierwszy_refuse": None}
    for r in sorted(b.rama, key=lambda x: x["tick"]):
        if r["desc"]:
            break
        t, dm = tk.get(r["tick"]), demo.get(r["tick"])
        if t is None or dm is None:
            continue
        i = bisect.bisect_right(av, r["mono"]) - 1
        pe, se = r["p_ekf"], r["sp_ekf"]
        dne, t_a = [0.0, 0.0], None
        if i >= 0:
            _, tf, kk, tr, dne, pa = fixy[i]
            rama.t_fix, rama.kosz, rama.tryb = tf, kk, tr
            ka, _ = b.dopasuj(pa, tf, okno=(-0.3, 0.3))
            t_a = float(b.vts[ka]) if ka is not None else tf
        pc = [pe[0] + dne[0], pe[1] + dne[1], pe[2]]
        sc = [se[0] + dne[0], se[1] + dne[1], se[2]]
        d, pb = nad2_krok.krok(sh, r["tick"], pe, pc, dm["own_vel_ned"], se, sc, "PATROL", t["pf"], t["cs"], r["sim"], None, rama)
        if rama_out is not None:                     # test analizatora: wiersz ramy w formacie drivera NAD2
            rama_out.write(json.dumps({"sim": r["sim"], "mono": r["mono"], "tick": r["tick"], "ep": r["ep"], "p_ekf": pe, "p_corr": pc,
                                       "ph": sh.kont_phase(), "nadir": d.get("nadir"), "nad2": d.get("nad2"), "tryb": rama.tryb,
                                       "desc": r["desc"], "phase": r.get("phase"), "obs": []}) + "\n")
        if not b.misja(r):
            continue
        utrata = sh.kont_phase() != "NOMINAL"
        if d["decision"] == "REFUSE":
            o["refuse"] += 1
            o["refuse_reguly"][str(d.get("rule"))] = o["refuse_reguly"].get(str(d.get("rule")), 0) + 1
            if o["pierwszy_refuse"] is None:
                o["pierwszy_refuse"] = {"sim": r["sim"], "rule": d.get("rule"), "cause": sh.kont_cause, "tau": sh._tau}
        if not utrata:
            continue
        o["n_ticki_utraty_misja"] += 1
        o["B3_zle"] += int(abs(sh._r_est - math.hypot(pc[0], pc[1])) > 1e-6)
        ip, j, tr = sh._przedzial, sh._j_eff, sh._tryb_eff
        o["przedzialy"][str(ip)] = o["przedzialy"].get(str(ip), 0) + 1
        if tr == "jeden":
            o["ticki_jeden"] += 1
        if ip is None:
            continue
        U = NS.u_nad2(ip, j, tr) - NS.DELTA_D5
        ks, _ = b.dopasuj(pe, r["sim"])
        t_s = float(b.vts[ks]) if ks is not None else r["sim"]
        e = float(np.hypot(pc[0] - b.gt(t_s)[0][0], pc[1] - b.gt(t_s)[0][1]))
        o["e_corr_max"] = max(o["e_corr_max"], e)
        o["max_e_do_U"] = max(o["max_e_do_U"], e / U)
        o["B1_przekroczenia"] += int(e > U)
        zap = NS.r_nad2(ip, j, tr, sh.cfg.r_e) - sh._r_est
        o["zapas_min"] = zap if o["zapas_min"] is None else min(o["zapas_min"], zap)
        if t_a is not None:
            h = (t_s - t_a) - (sh._tau + NS.TAU_EPS_NAD2)
            o["horyzont_minus_tau_eps_max"] = h if o["horyzont_minus_tau_eps_max"] is None else max(o["horyzont_minus_tau_eps_max"], h)
    for k in ("max_e_do_U", "zapas_min", "horyzont_minus_tau_eps_max", "e_corr_max"):
        if o[k] is not None:
            o[k] = round(o[k], 4)
    fr = sum(1 for x in b.nf if x.get("ekf_pos") is not None and b.klasa(x["sim"]) == "bez_GNSS")
    o["scenario"] = b.scen[b.denial["episode_id"]]
    return o


def main():
    out = {"ciecia": {}}
    for n in D.CIECIA_S4:
        o = replay(n)
        out["ciecia"][n] = o
        print(n, o["scenario"], "ticki", o["n_ticki_utraty_misja"], "B1", o["B1_przekroczenia"], "e/U", o["max_e_do_U"], "REFUSE", o["refuse"],
              o["refuse_reguly"], "zapas", o["zapas_min"], "jeden", o["ticki_jeden"], "B3", o["B3_zle"], "h−τ", o["horyzont_minus_tau_eps_max"],
              o["przedzialy"], flush=True)
    C = out["ciecia"].values()
    out["lacznie"] = {"ticki": sum(c["n_ticki_utraty_misja"] for c in C), "B1_przekroczenia": sum(c["B1_przekroczenia"] for c in C),
                      "max_e_do_U": max(c["max_e_do_U"] for c in C), "refuse": sum(c["refuse"] for c in C),
                      "zapas_min": min(c["zapas_min"] for c in C), "ticki_jeden": sum(c["ticki_jeden"] for c in C),
                      "B3_zle": sum(c["B3_zle"] for c in C), "horyzont_minus_tau_eps_max": max(c["horyzont_minus_tau_eps_max"] for c in C),
                      "odniesienie_CC": "ANEKS_NAD2-1 §1.3: 27 253 ticki, 0 przekroczeń, max e_corr′/U 0.398, 0 REFUSE, zapas min 1.71 m (c11_s02)"}
    out["lacznie"]["min_zapas_komorka"] = min(out["ciecia"].items(), key=lambda kv: kv[1]["zapas_min"])[0]
    out["lacznie"]["max_e_do_U_komorka"] = max(out["ciecia"].items(), key=lambda kv: kv[1]["max_e_do_U"])[0]
    os.makedirs(os.path.join(ROOT, "results/NAD2/s1"), exist_ok=True)
    json.dump(out, open(os.path.join(ROOT, "results/NAD2/s1/w2_replay.json"), "w"), ensure_ascii=False, indent=1)
    print(out["lacznie"])


if __name__ == "__main__":
    main()
