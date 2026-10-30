#!/usr/bin/env python3
"""results/WABIK3_RECON/tools/wabik3_uderzajacy.py — reprodukcja ANEKS_WABIK3-1 §2 w repo (CO-WABIK3R §6.2):
koszt etykiety „wabik" liczony na celach, które UDERZAJĄ. NOWY plik; importy READ-ONLY:
  wabik3_recon.py 5dbc94ec (load_bench, r2_arrays, streak_rule, progi FREEZE) — silnik kandydata;
  wabik_sig2.py a8397cb4 (evaluate = baza(i), litera v1 T_FLAG 12);
  bench.scenarios.position_at — GT celu z manifestu.

Definicje (ANEKS_WABIK3-1 §2, verbatim w treści):
  uderzający   = epizod NULL, którego GT (krok 0.1 s) schodzi < 5 m od home w oknie lotu [0, t1−t0);
  niedochodzący = pozostałe;
  etykieta na uderzającym = flaga KIEDYKOLWIEK;
  wchodzący w chwili flagi = średnia 1 s z v_trk·p̂ (demo.jsonl trk_vel_ned · jednostkowe trk_pos wzgl. home)
    < −0.2 m/s; oddalający > +0.2; pozostałe styczne;
  „prosto" = pierwsze zejście GT < 5 m w ≤ 1.5× czasu lotu prostego 15→5 m (10 m / v);
  trwanie etykiety = t_odwołania − t_flagi, a bez odwołania do ostatniej próbki epizodu;
  przyczyna odwołania: podłoga (dh_min < 5) / atak (≥ 1 s ataku) / brak.
Kandydat: dron · H 10 s · R 7 m · T 4 s · odwołanie podłoga+atak (konfiguracja reconu R2).
Krawędź uczciwa: streak podłoga+atak, ref ∈ {home, dron} × H ∈ {10, ∞} × R ∈ {3,5,7,9,11} ×
  T ∈ {4,6,8,10,12} (100), warunek FP(S2) 0 ∧ ORB 2/2; dla każdej wartości TP≤15 — min liczby
  uderzających z etykietą.

Użycie: wabik3_uderzajacy.py  → results/WABIK3_RECON/r2_uderzajacy.json + tabela na stdout.
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
for p in (ROOT, HERE, os.path.join(ROOT, "results", "WABIK2", "tools")):
    if p not in sys.path:
        sys.path.insert(0, p)
import wabik3_recon as R  # noqa: E402  (READ-ONLY)
import wabik_sig2 as W2  # noqa: E402  (READ-ONLY)
from bench import scenarios as S  # noqa: E402

FLOOR = R.FLOOR


def gt_class(e):
    dur = e["t1"] - e["t0"]
    t_hit = None
    t = 0.0
    while t < dur:
        g = S.position_at(e["man"], t)
        if math.hypot(g[0], g[1]) < FLOOR:
            t_hit = t
            break
        t = round(t + 0.1, 10)
    return t_hit


def candidate(a, e, ref="dron", H=10.0, Rr=7.0, T=4.0):
    """Etykieta reguły streak z maską zbliżenia + odwołanie podłoga+atak; zwraca też przyczynę."""
    d, tc = (a["dD"], a["tD"]) if ref == "dron" else (a["dH"], a["tH"])
    hor = np.inf if H is None else H
    atak = (tc > 0) & (tc < hor) & (d < Rr)
    mv = (a["spd"] > R.V_MOVE) & (a["dh"] < R.R_ZONE) & (a["dh_min"] >= FLOOR)
    rx = np.zeros(len(atak), bool)
    s0 = None
    for i in range(len(atak)):
        if atak[i]:
            s0 = a["ts"][i] if s0 is None else s0
            rx[i] = a["ts"][i] - s0 >= 1.0
        else:
            s0 = None
    r = R.streak_rule(a["ts"], mv & ~atak, a["dh_min"], T, rx, t0=e["t_first"])
    cause = None
    if r["t_rev"] is not None:
        t_abs = e["t_first"] + r["t_rev"]
        i = int(np.argmin(np.abs(a["ts"] - t_abs)))
        cause = "podloga" if a["dh_min"][i] < FLOOR else "atak"
    return r, cause


def at_flag(a, t_abs):
    """(v_rad 1 s [m/s; ujemne = wchodzi], |p| od home [m]) w chwili flagi (demo, trk_vel_ned)."""
    m = (a["ts"] >= t_abs - 1.0) & (a["ts"] <= t_abs + 1e-6)
    if not m.any():
        i = int(np.argmin(np.abs(a["ts"] - t_abs)))
        m = np.zeros(len(a["ts"]), bool); m[i] = True
    p = a["p"][m]; v = a["v"][m]
    n = np.hypot(p[:, 0], p[:, 1]); n[n < 1e-6] = 1e-6
    vr = (v[:, 0] * p[:, 0] + v[:, 1] * p[:, 1]) / n
    return float(np.mean(vr)), float(a["dh"][m][-1])


def kier(vr):
    return "wchodzi" if vr < -0.2 else ("oddala" if vr > 0.2 else "styczny")


def main():
    eps = R.load_bench()
    A = {}
    for e in eps:
        a = R.r2_arrays(e)
        if a is not None:
            D = e["demo"]
            a["p"] = np.array([x[1] for x in D]); a["v"] = np.array([x[2] for x in D])
        A[e["id"]] = a
    null = [e for e in eps if e["rodz"] == "NULL"]
    rows = []
    for e in null:
        t_hit = gt_class(e)
        a = A[e["id"]]
        row = dict(id=e["id"], sid=e["sid"], v=e["v"], uderzajacy=t_hit is not None,
                   t_gt_lt5_s=t_hit, prosto=(t_hit is not None and e["v"] > 0 and
                                             t_hit <= 1.5 * 10.0 / e["v"]))
        # kandydat
        r, cause = candidate(a, e)
        row["kand"] = dict(ever=r["ever"], final=r["final"], t_flag=r["t_flag"], t_rev=r["t_rev"],
                           przyczyna=cause)
        if r["ever"]:
            t_abs = e["t_first"] + r["t_flag"]
            vr, dist = at_flag(a, t_abs)
            end = r["t_rev"] if r["t_rev"] is not None else float(a["ts"][-1] - e["t_first"])
            row["kand"].update(v_rad=round(vr, 3), kier=kier(vr), dh=round(dist, 2),
                               trwanie=round(end - r["t_flag"], 2))
        # baza(i) — litera v1
        b = W2.evaluate(e["rows"])
        row["baza"] = dict(ever=b["ever"], final=b["final"], t_flag=b["t_flag_od_pierwszej"],
                           t_rev=b["t_revoke"])
        if b["ever"]:
            t_abs = e["t_first"] + b["t_flag_od_pierwszej"]
            vr, dist = at_flag(a, t_abs)
            end = b["t_revoke"] if b["t_revoke"] is not None else float(e["rows"][-1][0] - e["t_first"])
            row["baza"].update(v_rad=round(vr, 3), kier=kier(vr), dh=round(dist, 2),
                               trwanie=round(end - b["t_flag_od_pierwszej"], 2))
        rows.append(row)

    U = [r for r in rows if r["uderzajacy"]]
    N = [r for r in rows if not r["uderzajacy"]]
    med = lambda xs: round(float(np.median(xs)), 2) if xs else None  # noqa: E731
    kU = [r for r in U if r["kand"]["ever"]]
    bU = [r for r in U if r["baza"]["ever"]]
    out = {
        "uderzajacy": len(U), "uderzajacy_v1": sum(r["v"] == 1.0 for r in U),
        "uderzajacy_v05": sum(r["v"] == 0.5 for r in U),
        "niedochodzacy": len(N), "niedoch_v0": sum(r["v"] == 0.0 for r in N),
        "niedoch_v05": sum(r["v"] == 0.5 for r in N),
        "kand_U": len(kU), "kand_U_v05": sum(r["v"] == 0.5 for r in kU),
        "kand_U_v1": sum(r["v"] == 1.0 for r in kU),
        "kand_U_kier": {k: sum(r["kand"]["kier"] == k for r in kU) for k in ("wchodzi", "styczny", "oddala")},
        "kand_U_dh_med": med([r["kand"]["dh"] for r in kU]),
        "kand_U_tflag_med": med([r["kand"]["t_flag"] for r in kU]),
        "kand_U_odw": {k: sum(r["kand"]["przyczyna"] == k for r in kU) for k in ("podloga", "atak", None)},
        "kand_U_trwanie_podloga_med": med([r["kand"]["trwanie"] for r in kU if r["kand"]["przyczyna"] == "podloga"]),
        "kand_U_trwanie_atak_med": med([r["kand"]["trwanie"] for r in kU if r["kand"]["przyczyna"] == "atak"]),
        "kand_U_trwanie_med_p90_max": [med([r["kand"]["trwanie"] for r in kU]),
                                       round(float(np.percentile([r["kand"]["trwanie"] for r in kU], 90)), 2),
                                       round(max(r["kand"]["trwanie"] for r in kU), 2)],
        "prosto": sum(r["prosto"] for r in U), "prosto_kand": sum(r["prosto"] and r["kand"]["ever"] for r in U),
        "c08_s01_kand": [(r["id"], r["kand"]["t_flag"], r["kand"].get("v_rad"), r["kand"].get("trwanie"))
                         for r in U if r["sid"] == "c08_s01" and r["kand"]["ever"]],
        "baza_U": len(bU), "baza_U_final": sum(r["baza"]["final"] for r in U),
        "baza_U_final_ids": [r["id"] for r in U if r["baza"]["final"]],
        "baza_U_kier": {k: sum(r["baza"]["kier"] == k for r in bU) for k in ("wchodzi", "styczny", "oddala")},
        "baza_U_vrad_min_max": [min(r["baza"]["v_rad"] for r in bU), max(r["baza"]["v_rad"] for r in bU)],
        "baza_U_dh_med": med([r["baza"]["dh"] for r in bU]),
        "baza_U_tflag_min": min(r["baza"]["t_flag"] for r in bU),
        "baza_U_trwanie_med_max": [med([r["baza"]["trwanie"] for r in bU]), round(max(r["baza"]["trwanie"] for r in bU), 2)],
        "kand_N_ever_final": [sum(r["kand"]["ever"] for r in N), sum(r["kand"]["final"] for r in N)],
        "baza_N_ever_final": [sum(r["baza"]["ever"] for r in N), sum(r["baza"]["final"] for r in N)],
    }
    # uczciwa krawędź (100 konfiguracji)
    s2 = [e for e in eps if e["rodz"] != "NULL"]
    Uids = {r["id"] for r in U}
    grid = []
    for ref in ("home", "dron"):
        for H in (10.0, None):
            for Rr in (3.0, 5.0, 7.0, 9.0, 11.0):
                for T in (4.0, 6.0, 8.0, 10.0, 12.0):
                    tp = fp = orb = 0
                    for e in s2:
                        r, _ = candidate(A[e["id"]], e, ref, H, Rr, T)
                        if e["rodz"] == "TP":
                            tp += int(r["ever"] and r["t_flag"] is not None and r["t_flag"] <= 15.0)
                        elif e["rodz"] == "FP":
                            fp += int(r["ever"])
                        else:
                            orb += int(not r["final"])
                    nu = sum(int(candidate(A[e["id"]], e, ref, H, Rr, T)[0]["ever"])
                             for e in null if e["id"] in Uids)
                    grid.append(dict(ref=ref, H=H, R=Rr, T=T, TP_le15=tp, FP=fp, ORB=orb, U_etykieta=nu))
    ok = [g for g in grid if g["FP"] == 0 and g["ORB"] == 2]
    edge = {}
    for g in ok:
        k = g["TP_le15"]
        if k not in edge or g["U_etykieta"] < edge[k]:
            edge[k] = g["U_etykieta"]
    out["krawedz_TP_do_minU"] = dict(sorted(edge.items()))
    out["n_konfiguracji"] = len(grid)
    json.dump(dict(podsumowanie=out, siatka=grid, epizody=rows),
              open(os.path.join(ROOT, "results", "WABIK3_RECON", "r2_uderzajacy.json"), "w"),
              indent=1, ensure_ascii=False, default=str)
    print(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
