#!/usr/bin/env python3
"""results/TEACH/tools/teach_w2.py — W2 wierność mapy, W3 czas, wejście W4 (PROMPT_TEACH_S1 §4; 0 bootów).

Moduł lotu harness/teach_map.Producent karmiony kadrami reconu w kolejności czasu: seria „przed” (flaga GNSS 1), potem seria „po”
(flaga 0, chwila flagi = chwila cięcia reconu t_ciecia = sim − od_cięcia). Kadr = render jak w reconie (teach2.Lot.przygotuj: poza
GT, orto_r2.Kam.renderuj z łaty 2024-04-27, piksel 0.05 m); migawki EKF z results/TEACH_RECON/r2_klatki.json.gz. GT wyłącznie
tutaj (ocena), nigdy w producencie.
Wiersz kadru po cięciu w formacie reconu (teach2.lancuch, pola_klatki): [sim, τ, k, r_E, r_N, zgodne, poprawka_E, poprawka_N, błąd,
przyjęta, innowacja, pokrycie_z_k, pokrycie_największe]; pokrycia prawdziwe z poz GT (teach_r34.pokrycie, kwadraty a kadru).
Porównanie z results/TEACH_RECON2/czesci/<lot>_<łata>.json.gz, klucz „M4/K1_SIFT”: liczba przyjętych, największy błąd (tol.
0.001 m), θ_k (tol. 0.0001°) i t_k (tol. 0.0001 m) wszystkich klatek kluczowych, wiersz po wierszu (k, zgodne, przyjęta).
Czas (W3): czas wywołania Producent.obserwacja na kadr (bez renderu) w fazie mapy i lokalizacji, czas od klatki flagi do gotowej
georeferencji, opóźnienie pierwszej przyjętej poprawki po fladze (czas sim).
Użycie: teach_w2.py --wariant K|K′ --procesy N [--laty S,M,J] [--loty a,b] [--wyj katalog] [--bez-zapisu-czesci]
Wyjście: <wyj>/czesci_<wariant>/<lot>_<łata>.json.gz i <wyj>/w2_<wariant>.json (podsumowanie).
"""
import argparse
import gzip
import json
import math
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, ROOT)
from harness import teach_map as TM                      # noqa: E402

T2, T, R2 = TM.T2, TM.T, TM.R2
SRC = os.path.join(ROOT, "results/TEACH_RECON")
REF = os.path.join(ROOT, "results/TEACH_RECON2/czesci")
KLUCZ = "M4/K1_SIFT"
TOL_ERR, TOL_TH, TOL_T = 0.001, 1e-4, 1e-4
_K = {}


def klatki():
    if "K" not in _K:
        _K["K"] = json.load(gzip.open(os.path.join(SRC, "r2_klatki.json.gz"), "rt"))
    return _K["K"]


def zadanie(arg):
    lot, lata, wariant = arg
    import cv2
    cv2.setNumThreads(1)
    t0 = time.time()
    kam = R2.Kam(R2.kamera())
    teren = cv2.imread(os.path.join(SRC, "dane", f"{lata}_2024-04-27.png"))
    K = [k for k in klatki() if k["lot"] == lot]
    przed = sorted([k for k in K if k["seria"] == "przed"], key=lambda k: k["sim"])
    po = sorted([k for k in K if k["seria"] == "po"], key=lambda k: k["sim"])
    t_cut = po[0]["sim"] - po[0]["od_ciecia"]

    def render(k):
        Rg = R2.rotm(k["gt_q"])
        C, Rk = kam.poza(np.array(k["gt_p"]), Rg)
        fr, _ = kam.renderuj(teren, T.PIKSEL_T, C, Rk)
        return fr, C[:2]

    P = TM.Producent(wariant=wariant)
    cam_gt = {}
    ms_mapa, ms_lok = [], []
    for k in przed:
        fr, cg = render(k)
        cam_gt[round(k["sim"], 6)] = cg
        a = time.perf_counter()
        P.obserwacja(k["sim"], fr, k["ekf_q"], k["ekf_pos"], 1)
        ms_mapa.append((time.perf_counter() - a) * 1e3)
    kl, ms_zamk, georef, t_first = [], None, None, None
    n_flag_wiaz = 0
    for k in po:
        fr, cg = render(k)
        a = time.perf_counter()
        rec = P.obserwacja(k["sim"], fr, k["ekf_q"], k["ekf_pos"], 0, t_flagi=t_cut)
        dt = (time.perf_counter() - a) * 1e3
        reg = P.rejestr
        if "georef" in reg:
            ms_zamk, georef = reg["ms_od_flagi_do_georef"], reg["georef"]
            ms_lok.append(dt - ms_zamk)
        else:
            ms_lok.append(dt)
        Re = TM.NF.ekf_R(k["ekf_q"])
        Ce = Re @ kam.t_link
        a_x = (-k["ekf_pos"][2] + Ce[2]) * (kam.H / 2) / kam.F
        pk_max = max((T.pokrycie(cg, cam_gt[round(y["sim"], 6)], a_x) for y in P.kf), default=0.0)
        gt_en = np.array(k["gt_p"][:2])
        row = [round(k["sim"], 3), round(reg["tau"], 3), None, None, None, None, None, None, None, 0, None, None, round(pk_max, 3)]
        if reg.get("k") is not None:
            i = reg["k"]
            fix = np.array(reg["fix_en"])
            err = float(np.linalg.norm(fix - gt_en))
            row = [round(k["sim"], 3), round(reg["tau"], 3), i, round(reg["r"][0], 4), round(reg["r"][1], 4), reg["zgodne"],
                   round(float(fix[0]), 4), round(float(fix[1]), 4), round(err, 4), int(reg["ok"]), round(reg["innowacja"], 4),
                   round(T.pokrycie(cg, cam_gt[round(P.kf[i]["sim"], 6)], a_x), 3), round(pk_max, 3)]
            if rec["ok"] and t_first is None:
                t_first = k["sim"]
        kl.append(row)
    # porównanie z reconem
    ref = json.load(gzip.open(os.path.join(REF, f"{lot}_{lata}.json.gz"), "rt"))
    rk = ref["klatki"][KLUCZ]
    acc, racc = [r for r in kl if r[9]], [r for r in rk if r[9]]
    mx = max((r[8] for r in acc), default=None)
    rmx = max((r[8] for r in racc), default=None)
    d_th = max((abs(x["theta_deg"] - y["geo"][KLUCZ]["theta_deg"]) for x, y in zip(georef["kf"], ref["kf"])), default=0.0)
    d_t = max((max(abs(a - b) for a, b in zip(x["t"], y["geo"][KLUCZ]["t"])) for x, y in zip(georef["kf"], ref["kf"])), default=0.0)
    d_sim = max((abs(x["sim"] - y["sim"]) for x, y in zip(georef["kf"], ref["kf"])), default=0.0)
    rozn_wierszy = sum(1 for a_, b_ in zip(kl, rk) if (a_[2], a_[5], a_[9]) != (b_[2], b_[5], b_[9]))
    por = {"n_kf": len(georef["kf"]), "n_kf_ref": len(ref["kf"]), "d_sim_kf": d_sim, "n_przyj": len(acc), "n_przyj_ref": len(racc),
           "max": mx, "max_ref": rmx, "d_theta_deg": round(d_th, 7), "d_t_m": round(d_t, 7), "n_wierszy": len(kl), "n_wierszy_ref": len(rk),
           "wiersze_rozne_k_zgodne_przyjeta": rozn_wierszy}
    por["zgodne"] = (por["n_kf"] == por["n_kf_ref"] and d_sim < 1e-6 and por["n_przyj"] == por["n_przyj_ref"] and len(kl) == len(rk)
                     and (mx is None and rmx is None or abs(mx - rmx) <= TOL_ERR) and d_th <= TOL_TH and d_t <= TOL_T)
    q = lambda x, p: round(float(np.quantile(x, p)), 2) if len(x) else None
    czas = {"ms_mapa": {"p50": q(ms_mapa, .5), "p95": q(ms_mapa, .95), "max": round(max(ms_mapa), 2)},
            "ms_lok": {"p50": q(ms_lok, .5), "p95": q(ms_lok, .95), "max": round(max(ms_lok), 2)},
            "ms_od_flagi_do_georef": ms_zamk, "ms_wiazania_przy_zamknieciu": georef["ms_wiazania"],
            "ms_rozwiazanie": georef["ms_rozwiazanie"], "n_dop_pozno": georef["n_dop_pozno"],
            "opoznienie_pierwszej_poprawki_s": None if t_first is None else round(t_first - t_cut, 3)}
    wyn = {"lot": lot, "lata": lata, "wariant": wariant, "t_ciecia": t_cut, "t_konca": po[-1]["sim"], "n_przed": len(przed),
           "n_po": len(po), "georef": georef, "klatki": {KLUCZ: kl}, "porownanie": por, "czas": czas,
           "pola_klatki": ref["pola_klatki"], "zegar_s": round(time.time() - t0, 1), "n_flag_wiaz": n_flag_wiaz}
    return wyn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wariant", default="K", choices=TM.WARIANTY_K)
    ap.add_argument("--procesy", type=int, default=8)
    ap.add_argument("--laty", default="S,M,J")
    ap.add_argument("--loty", default="")
    ap.add_argument("--wyj", default=os.path.join(ROOT, "results/TEACH/s1"))
    a = ap.parse_args()
    import cv2
    loty = sorted({k["lot"] for k in klatki()})
    if a.loty:
        loty = [l for l in loty if l in a.loty.split(",")]
    zad = [(l, s, a.wariant) for s in a.laty.split(",") for l in loty]
    zad.sort(key=lambda z: z[0] != "L_c10_s01")
    tag = "K" if a.wariant == "K" else "K2"
    cz = os.path.join(a.wyj, f"czesci_{tag}")
    os.makedirs(cz, exist_ok=True)
    t0 = time.time()
    print(time.strftime("%T"), "zadań", len(zad), "procesy", a.procesy, "cv2", cv2.__version__, sys.executable, flush=True)
    wyn = []
    with Pool(min(a.procesy, 8)) as p:
        for w in p.imap_unordered(zadanie, zad):
            fn = os.path.join(cz, f"{w['lot']}_{w['lata']}.json.gz")
            with gzip.open(fn + ".tmp", "wt") as f:
                json.dump(w, f)
            os.replace(fn + ".tmp", fn)
            wyn.append({k: w[k] for k in ("lot", "lata", "porownanie", "czas", "zegar_s")})
            print(time.strftime("%T"), f"{time.time() - t0:.0f}s", w["lot"], w["lata"], w["porownanie"], w["czas"]["ms_od_flagi_do_georef"],
                  flush=True)
    wyn.sort(key=lambda w: ("SMJ".index(w["lata"]), w["lot"]))
    out = {"wariant": a.wariant, "cv2": cv2.__version__, "python": sys.version.split()[0], "interpreter": sys.executable,
           "procesy": a.procesy, "zgodne_wszystkie": all(w["porownanie"]["zgodne"] for w in wyn), "n": len(wyn), "wyniki": wyn,
           "sumy_toru": TM.sumy_toru(), "zegar_s": round(time.time() - t0, 1)}
    json.dump(out, open(os.path.join(a.wyj, f"w2_{tag}.json"), "w"), ensure_ascii=False, indent=1)
    print("zgodne_wszystkie", out["zgodne_wszystkie"], flush=True)


if __name__ == "__main__":
    main()
