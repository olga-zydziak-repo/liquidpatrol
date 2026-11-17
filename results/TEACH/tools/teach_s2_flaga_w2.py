#!/usr/bin/env python3
"""results/TEACH/tools/teach_s2_flaga_w2.py — W2-lot i W2-wyścig (ANEKS_TEACH-3 §4.4; 0 bootów).

Jak teach_w2.zadanie (render reconu, migawki EKF z r2_klatki, porównanie z results/TEACH_RECON2/czesci, klucz M4/K1_SIFT), ale
ścieżką lotu: Producent.obserwacja bez podanej chwili flagi (t_flagi=None), flaga jako stan przy klatce.
  lot     — flaga 0 od pierwszej klatki z czasem ≥ chwila cięcia (39 przebiegów). Oczekiwane: mapa ma o jeden kadr mniej niż recon
            i żaden kadr mapy nie ma czasu ≥ chwila cięcia; liczba przyjętych różni się najwyżej o 1, największy błąd przebiegu
            najwyżej o 0.02 m.
  wyscig  — flaga 0 o jedną klatkę później (pierwsza klatka po cięciu jeszcze z flagą 1; łata S, 13 przebiegów). Oczekiwane: kadry
            mapy te same co w reconie, θ_k i t_k równe reconowi do 0.0001, żaden kadr mapy z czasem ≥ chwila cięcia.
Kadry mapy reconu = seria „przed” (wszystkie z czasem < chwila cięcia, z wysokością ≥ H_MIN) — recon włączał kadr z bufora.
Użycie: teach_s2_flaga_w2.py --tryb lot|wyscig [--laty S,M,J] [--procesy N] [--wyj katalog]
Wyjście: <wyj>/w2_<tryb>.json.
"""
import argparse
import gzip
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/TEACH/tools")]
from harness import teach_map as TM                      # noqa: E402
import teach_w2 as W                                     # noqa: E402

T, R2 = TM.T, TM.R2
TOL_ERR_LOT, TOL_GEO = 0.02, 1e-4


def zadanie(arg):
    lot, lata, tryb = arg
    import cv2
    cv2.setNumThreads(1)
    t0 = time.time()
    kam = R2.Kam(R2.kamera())
    teren = cv2.imread(os.path.join(W.SRC, "dane", f"{lata}_2024-04-27.png"))
    K = [k for k in W.klatki() if k["lot"] == lot]
    przed = sorted([k for k in K if k["seria"] == "przed"], key=lambda k: k["sim"])
    po = sorted([k for k in K if k["seria"] == "po"], key=lambda k: k["sim"])
    t_cut = po[0]["sim"] - po[0]["od_ciecia"]
    assert przed[-1]["sim"] < t_cut <= po[0]["sim"]

    def render(k):
        C, Rk = kam.poza(np.array(k["gt_p"]), R2.rotm(k["gt_q"]))
        fr, _ = kam.renderuj(teren, T.PIKSEL_T, C, Rk)
        return fr, C[:2]

    P = TM.Producent(wariant="K")
    cam_gt = {}
    for k in przed:
        fr, cg = render(k)
        cam_gt[round(k["sim"], 6)] = cg
        P.obserwacja(k["sim"], fr, k["ekf_q"], k["ekf_pos"], 1)
    kl, georef, t_zamk, odrz, t_first = [], None, None, None, None
    for j, k in enumerate(po):
        fr, cg = render(k)
        cam_gt[round(k["sim"], 6)] = cg
        fl = 1 if (tryb == "wyscig" and j == 0) else 0
        rec = P.obserwacja(k["sim"], fr, k["ekf_q"], k["ekf_pos"], fl)              # TEACH-3: bez chwili flagi
        reg = P.rejestr
        if "georef" in reg:
            georef, t_zamk, odrz = reg["georef"], k["sim"], reg.get("odrzucony_z_bufora")
        if reg.get("faza") != "lok":
            continue
        gt_en = np.array(k["gt_p"][:2])
        row = [round(k["sim"], 3), round(reg["tau"], 3), None, None, None, None, None, None, None, 0, None]
        if reg.get("k") is not None:
            fix = np.array(reg["fix_en"])
            row = [round(k["sim"], 3), round(reg["tau"], 3), reg["k"], round(reg["r"][0], 4), round(reg["r"][1], 4), reg["zgodne"],
                   round(float(fix[0]), 4), round(float(fix[1]), 4), round(float(np.linalg.norm(fix - gt_en)), 4), int(reg["ok"]),
                   round(reg["innowacja"], 4)]
            if rec["ok"] and t_first is None:
                t_first = k["sim"]
        kl.append(row)
    ref = json.load(gzip.open(os.path.join(W.REF, f"{lot}_{lata}.json.gz"), "rt"))
    rk = ref["klatki"][W.KLUCZ]
    acc, racc = [r for r in kl if r[9]], [r for r in rk if r[9]]
    mx = max((r[8] for r in acc), default=None)
    rmx = max((r[8] for r in racc), default=None)
    sim_mapy = [round(x["sim"], 6) for x in P.kadry]
    n_mapy_ref = sum(1 for k in przed if -k["ekf_pos"][2] >= TM.H_MIN)                 # recon: kadr z bufora włączony
    kf_ref = {round(y["sim"], 6): y for y in ref["kf"]}
    d_th = d_t = 0.0
    kf_wsp = all(round(x["sim"], 6) in kf_ref for x in georef["kf"]) and len(georef["kf"]) == len(ref["kf"])
    for x in georef["kf"]:
        y = kf_ref.get(round(x["sim"], 6))
        if y is not None:
            d_th = max(d_th, abs(x["theta_deg"] - y["geo"][W.KLUCZ]["theta_deg"]))
            d_t = max(d_t, max(abs(a - b) for a, b in zip(x["t"], y["geo"][W.KLUCZ]["t"])))
    n_po_cieciu = sum(1 for s in sim_mapy if s >= t_cut)
    por = {"t_ciecia": round(t_cut, 4), "t_zamkniecia": round(t_zamk, 4), "odrzucony_z_bufora": odrz,
           "ostatni_kadr_mapy": max(sim_mapy), "ostatni_przed_ciecia": round(przed[-1]["sim"], 4),
           "n_kadrow_mapy": len(sim_mapy), "n_kadrow_mapy_ref": n_mapy_ref, "n_kadrow_mapy_po_cieciu": n_po_cieciu,
           "n_kf": len(georef["kf"]), "n_kf_ref": len(ref["kf"]), "kf_te_same": kf_wsp,
           "d_theta_deg": round(d_th, 7), "d_t_m": round(d_t, 7),
           "n_przyj": len(acc), "n_przyj_ref": len(racc), "max": mx, "max_ref": rmx,
           "d_max": None if mx is None or rmx is None else round(mx - rmx, 4),
           "opoznienie_pierwszej_poprawki_s": None if t_first is None else round(t_first - t_cut, 3)}
    if tryb == "lot":
        por["pass"] = (por["n_kadrow_mapy"] == n_mapy_ref - 1 and n_po_cieciu == 0 and odrz is not None
                       and abs(len(acc) - len(racc)) <= 1 and (mx is None and rmx is None or
                                                               (mx is not None and rmx is not None and abs(mx - rmx) <= TOL_ERR_LOT)))
    else:
        por["pass"] = (por["n_kadrow_mapy"] == n_mapy_ref and sim_mapy == sorted(round(k["sim"], 6) for k in przed
                                                                                  if -k["ekf_pos"][2] >= TM.H_MIN)
                       and n_po_cieciu == 0 and kf_wsp and d_th <= TOL_GEO and d_t <= TOL_GEO)
    return {"lot": lot, "lata": lata, "tryb": tryb, "porownanie": por, "zegar_s": round(time.time() - t0, 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tryb", required=True, choices=("lot", "wyscig"))
    ap.add_argument("--laty", default="S,M,J")
    ap.add_argument("--procesy", type=int, default=8)
    ap.add_argument("--wyj", default=os.path.join(ROOT, "results/TEACH/s2/flaga"))
    a = ap.parse_args()
    loty = sorted({k["lot"] for k in W.klatki()})
    zad = [(l, s, a.tryb) for s in a.laty.split(",") for l in loty]
    zad.sort(key=lambda z: z[0] != "L_c10_s01")
    os.makedirs(a.wyj, exist_ok=True)
    t0 = time.time()
    wyn = []
    with Pool(min(a.procesy, 8)) as p:
        for w in p.imap_unordered(zadanie, zad):
            wyn.append(w)
            print(time.strftime("%T"), f"{time.time() - t0:.0f}s", w["lot"], w["lata"], w["porownanie"], flush=True)
    wyn.sort(key=lambda w: ("SMJ".index(w["lata"]), w["lot"]))
    out = {"tryb": a.tryb, "n": len(wyn), "n_pass": sum(w["porownanie"]["pass"] for w in wyn),
           "pass_wszystkie": all(w["porownanie"]["pass"] for w in wyn), "wyniki": wyn, "sumy_toru": TM.sumy_toru(),
           "zegar_s": round(time.time() - t0, 1)}
    json.dump(out, open(os.path.join(a.wyj, f"w2_{a.tryb}.json"), "w"), ensure_ascii=False, indent=1)
    print("pass_wszystkie", out["pass_wszystkie"], out["n_pass"], "/", out["n"], flush=True)


if __name__ == "__main__":
    main()
