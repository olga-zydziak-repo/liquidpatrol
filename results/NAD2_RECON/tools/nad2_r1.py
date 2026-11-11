#!/usr/bin/env python3
"""results/NAD2_RECON/tools/nad2_r1.py — PROMPT_NAD2_S0 R1: łańcuch czasu (0 bootów).

(a) Każdy tick misji rama.jsonl: próbka p_ekf dopasowana PO WARTOŚCI do vehicle_local_position z wyciągu ULG (okno
    [sim − 0.4, sim + 0.1] s, min |Δp|; log 125 Hz, p_ekf z 4 cyframi) ⇒ t_próbki − rama.sim w obu konwencjach
    (timestamp, timestamp_sample); niepewność = reszta dopasowania i odstęp próbek 8 ms.
(b) Wiersze nf (migawka EKF przy przybyciu klatki): ekf_pos → VLP po wartości, ekf_q → vehicle_attitude po wartości;
    opóźnienie klatki L = t_próbki − t_frame (t_frame = stempel sim obrazu = nf.sim).
(c) e_corr(tick) = |p_corr − GT(t_próbki EKF użytej w ticku)| (oś timestamp_sample), poziomo i 3D; składowe wzdłuż / w poprzek
    toru (kierunek prędkości GT), regresja składowej wzdłuż toru na prędkość GT. Obok dla porównania: GT w chwili ticku (rama.sim).
(d) Zmiana przechyłu / pochylenia między t_frame a próbką postawy użytej przez obserwatora i wkład h·tan(Δ).
Wyjście: results/NAD2_RECON/r1_czas.json (per boot + łącznie per klasa).
"""
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nad2_dane as D


def r1_boot(b):
    o = {"boot": b.boot, "t_flag": b.t_flag, "t_inj": b.t_inj}
    # (a)
    dts, dtss, res = [], [], []
    ticks = []
    for r in b.rama:
        if not b.misja(r):
            continue
        i, d = b.dopasuj(r["p_ekf"], r["sim"])
        if i is None:
            continue
        dts.append(b.vt[i] - r["sim"]); dtss.append(b.vts[i] - r["sim"]); res.append(d)
        ticks.append((r, i))
    o["a_tick"] = {"t_ts_minus_sim": D.rozklad(dts), "t_tss_minus_sim": D.rozklad(dtss), "reszta_m": D.rozklad(res),
                   "frac_reszta_lt_1e-3": round(float(np.mean(np.array(res) < 1e-3)), 4) if res else None}
    # (b)
    L, Lts, Lq, resb = [], [], [], []
    dro, dpi, wklad = [], [], []
    for r in b.nf:
        if r.get("ekf_pos") is None or r.get("ekf_q") is None:
            continue
        tf = r["sim"]
        i, d = b.dopasuj(r["ekf_pos"], tf, okno=(-0.3, 0.3))
        if i is None:
            continue
        L.append(b.vts[i] - tf); Lts.append(b.vt[i] - tf); resb.append(d)
        k, dq = b.dopasuj_q(r["ekf_q"], tf, okno=(-0.3, 0.3))
        if k is not None:
            Lq.append(b.ats[k] - tf)
            q0, _ = b.q_w(tf)
            r0, p0, _ = D.rpy(q0)
            r1, p1, _ = D.rpy(r["ekf_q"])
            h = -r["ekf_pos"][2]
            dro.append(math.degrees(r1 - r0)); dpi.append(math.degrees(p1 - p0))
            wklad.append(h * math.tan(math.hypot(r1 - r0, p1 - p0)))
    o["b_klatka"] = {"L_tss": D.rozklad(L), "L_ts": D.rozklad(Lts), "L_q_tss": D.rozklad(Lq), "reszta_m": D.rozklad(resb)}
    o["d_postawa"] = {"d_przechyl_deg": D.rozklad(np.abs(dro)), "d_pochylenie_deg": D.rozklad(np.abs(dpi)),
                      "wklad_h_tan_m": D.rozklad(wklad)}
    # (c)
    kl = {}
    for r, i in ticks:
        ts = b.vts[i]
        g = b.gt(ts)[0]
        g0 = b.gt(r["sim"])[0]
        pc = np.array(r["p_corr"])
        e = pc - g
        e0 = pc - g0
        v = b.gt_v(ts)[0][:2]
        sp = float(np.linalg.norm(v))
        u = v / sp if sp > 0.2 else None
        c = kl.setdefault(b.klasa(r["sim"]), {"h": [], "d3": [], "h_sim": [], "wzdl": [], "poprz": [], "v": []})
        c["h"].append(float(np.hypot(e[0], e[1]))); c["d3"].append(float(np.linalg.norm(e))); c["h_sim"].append(float(np.hypot(e0[0], e0[1])))
        if u is not None:
            c["wzdl"].append(float(e[:2] @ u)); c["poprz"].append(float(e[0] * u[1] - e[1] * u[0])); c["v"].append(sp)
    o["c_ecorr"] = {}
    for k, c in kl.items():
        reg = None
        if len(c["v"]) > 10:
            A = np.vstack([c["v"], np.ones(len(c["v"]))]).T
            sl, ic = np.linalg.lstsq(A, np.array(c["wzdl"]), rcond=None)[0]
            reg = {"nachylenie_s": round(float(sl), 4), "wyraz_wolny_m": round(float(ic), 4),
                   "r": round(float(np.corrcoef(c["v"], c["wzdl"])[0, 1]), 3), "n": len(c["v"])}
        o["c_ecorr"][k] = {"poziomo": D.rozklad(c["h"]), "3d": D.rozklad(c["d3"]), "poziomo_GT_w_ticku": D.rozklad(c["h_sim"]),
                           "wzdluz_toru": D.rozklad(c["wzdl"]), "w_poprzek_abs": D.rozklad(np.abs(c["poprz"])),
                           "regresja_wzdluz_na_v": reg}
    return o, kl, L, dts, dtss


def main():
    boots = D.CIECIA_S4 + D.NOM_S4
    out, laczne, Lall, ta, tb = {"boot": {}}, {}, [], [], []
    for n in boots:
        b = D.Boot(n)
        o, kl, L, dts, dtss = r1_boot(b)
        out["boot"][n] = o
        Lall += L; ta += dts; tb += dtss
        for k, c in kl.items():
            z = laczne.setdefault(k, {kk: [] for kk in c})
            for kk in c:
                z[kk] += c[kk]
        print(n, "L_tss p50", o["b_klatka"]["L_tss"].get("p50"), "tick dt_tss p50", o["a_tick"]["t_tss_minus_sim"].get("p50"),
              "e_corr bez", (o["c_ecorr"].get("bez_GNSS") or {}).get("poziomo", {}).get("max"), flush=True)
    out["lacznie"] = {"L_tss": D.rozklad(Lall), "tick_t_ts_minus_sim": D.rozklad(ta), "tick_t_tss_minus_sim": D.rozklad(tb)}
    for k, c in laczne.items():
        A = np.vstack([c["v"], np.ones(len(c["v"]))]).T
        sl, ic = np.linalg.lstsq(A, np.array(c["wzdl"]), rcond=None)[0]
        out["lacznie"][k] = {"e_corr_poziomo": D.rozklad(c["h"]), "e_corr_3d": D.rozklad(c["d3"]),
                             "e_corr_poziomo_GT_w_ticku": D.rozklad(c["h_sim"]), "wzdluz_toru": D.rozklad(c["wzdl"]),
                             "w_poprzek_abs": D.rozklad(np.abs(c["poprz"])),
                             "regresja_wzdluz_na_v": {"nachylenie_s": round(float(sl), 4), "wyraz_wolny_m": round(float(ic), 4),
                                                      "r": round(float(np.corrcoef(c["v"], c["wzdl"])[0, 1]), 3), "n": len(c["v"])}}
    med = out["lacznie"]["L_tss"]["p50"]
    out["regula_osi_czasu"] = {"mediana_L_s": med, "prog_s": 0.05, "wybor": "C1" if med is not None and med >= 0.05 else "C0"}
    json.dump(out, open(os.path.join(D.OUT, "r1_czas.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out["lacznie"].items()}, ensure_ascii=False)[:3000])
    print(out["regula_osi_czasu"])


if __name__ == "__main__":
    main()
