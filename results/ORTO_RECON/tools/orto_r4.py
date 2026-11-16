#!/usr/bin/env python3
"""results/ORTO_RECON/tools/orto_r4.py — PROMPT_ORTO_S0 R4/R5: łańcuch poprawek z ortofotomapy na klatkach R2 (0 bootów).

Klatka = rzut płaskiego gruntu z „świata” przy pozie GT (orto_r2.Kam.renderuj); wariant „para”: świat = edycja starsza (2012-04-28),
mapa = nowsza (2025-08-12); wariant „kontrola”: świat = mapa (ta sama edycja po obu stronach). Kandydat (orto_r3) widzi wyłącznie
klatkę, migawkę EKF z klatki (q, pozycja) i predykcję.
Łańcuch (jak rama B+ NAD3, poziomo): stan Δ (E, N) i t_fix. Na starcie (chwila cięcia) Δ = 0, t_fix = t_cięcia (ostatnia pozycja
z GNSS). Klatka: pred = EKF(t) + Δ; τ = t − t_fix; promień szukania R_szuk(τ). Wynik kandydata → poprawka pojazdu; jeśli reguła
przyjmie: Δ = poprawka − EKF(t), t_fix = t. Błąd = |poprawka − GT pojazdu| (GT = rama modelu z trace, ta sama co e_corr NAD3).
Reguły: „wszystko” (R4: każdy wynik przyjęty — ogon błędu przed odrzucaniem) i siatka reguł R5:
  cechy (K1, K2): n_inl ≥ a ∧ [|skala − 1| ≤ 0.10 ∧ |kąt| ≤ 10°]? ∧ |poprawka − pred| ≤ g0 + VR·τ;
  NCC (K3):       szczyt ≥ c ∧ iloraz do drugiego szczytu ≥ q ∧ |poprawka − pred| ≤ g0 + VR·τ.
Przerwy: odstępy między kolejnymi przyjętymi poprawkami łącznie z [cięcie, pierwsza] i [ostatnia, koniec misji].
Tryby: `strojenie` — loty c05 (6), wszystkie reguły, oba warianty; `ocena` — wszystkie 13 lotów, reguła „wszystko” + reguła wybrana
(results/ORTO_RECON/r5_reguly.json, z orto_r5.py) — zapis per klatka.
Wyjście: results/ORTO_RECON/r4_<tryb>.json(.gz). Równolegle po (lot, łata, wariant); cv2 jednowątkowo w procesie.
Użycie: orto_r4.py strojenie | ocena [n_proc]
"""
import gzip
import itertools
import json
import math
import os
import sys
import time
from multiprocessing import Pool

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orto_r2 as R2
import orto_r3 as R3

OUT = R2.OUT
DANE = os.path.join(OUT, "dane")
LATY = ("A", "B", "C")
WARIANTY = ("para", "kontrola")
PROG_D, PROG_S = 1.37, 2.28            # NAD3: rachunek dostępności / bezpieczeństwa (E_d, E_s z freeze_G sprawdzian_PRE_4)


def reguly(kand):
    out = [{"id": "wszystko"}]
    g0s = (1.5, 3.0, None)
    if kand == "K3_NCC":
        for c, q, g0 in itertools.product((0.3, 0.4, 0.5, 0.6, 0.7, 0.8), (1.0, 1.1, 1.2, 1.3), g0s):
            out.append({"id": f"c{c}_q{q}_g{g0}", "c": c, "q": q, "g0": g0})
    else:
        for a, geo, g0 in itertools.product((4, 6, 8, 12, 20, 30), (True, False), g0s):
            out.append({"id": f"a{a}_geo{int(geo)}_g{g0}", "a": a, "geo": geo, "g0": g0})
    return out


def przyjmij(r, wyn, innow, tau):
    if wyn is None or not wyn.get("ok"):
        return False
    if r["id"] == "wszystko":
        return True
    if r.get("g0") is not None and innow > r["g0"] + R3.VR * tau:
        return False
    if "c" in r:
        return wyn["szczyt"] >= r["c"] and wyn["iloraz"] >= r["q"]
    if wyn["n_inl"] < r["a"]:
        return False
    return not r["geo"] or (abs(wyn["skala"] - 1) <= 0.10 and abs(wyn["kat"]) <= 10.0)


def klatki_lotu(lot):
    K = json.load(gzip.open(os.path.join(OUT, "r2_klatki.json.gz"), "rt"))
    return [k for k in K if k["lot"] == lot]


def zadanie(arg):
    lot, lata, wariant, tryb, wybrane = arg
    cv2.setNumThreads(1)
    kam = R2.Kam(R2.kamera())
    pr = R3.Prost(kam)
    mapa = cv2.imread(os.path.join(DANE, f"{lata}_mapa_2025-08-12.png"))
    swiat = mapa if wariant == "kontrola" else cv2.imread(os.path.join(DANE, f"{lata}_swiat_2012-04-28.png"))
    det = {"K1_SIFT": R3.Cechy("K1_SIFT", mapa), "K2_AKAZE": R3.Cechy("K2_AKAZE", mapa), "K3_NCC": R3.NCC(mapa)}
    K = klatki_lotu(lot)
    t_cut = K[0]["sim"] - K[0]["od_ciecia"]
    t_end = K[-1]["sim"]
    if tryb == "strojenie":
        RG = {kd: reguly(kd) for kd in det}
    else:
        RG = {kd: [{"id": "wszystko"}] + ([wybrane[f"{lata}/{wariant}/{kd}"]] if wybrane.get(f"{lata}/{wariant}/{kd}") else [])
              for kd in det}
    st = {kd: {r["id"]: {"d": np.zeros(2), "t_fix": t_cut, "acc": [], "err_acc": [], "err_all": [], "brak": 0, "klatki": []}
               for r in RG[kd]} for kd in det}
    czasy = {kd: [] for kd in det}
    czas_prost = []
    poza_okn = 0
    for k in K:
        p_gt = np.array(k["gt_p"])
        C, Rk = kam.poza(p_gt, R2.rotm(k["gt_q"]))
        fr, fpoza = kam.renderuj(swiat, R3.RHO, C, Rk)
        poza_okn += fpoza > 0
        t0 = time.perf_counter()
        rect, mask, off = pr(fr, k["ekf_q"], k["ekf_pos"])
        czas_prost.append((time.perf_counter() - t0) * 1e3)
        ekf_en = np.array([k["ekf_pos"][1], k["ekf_pos"][0]])
        gt_en = p_gt[:2]
        for kd, D in det.items():
            t0 = time.perf_counter()
            fk = D.klatka(rect, mask)
            t_k = (time.perf_counter() - t0) * 1e3
            for r in RG[kd]:
                s = st[kd][r["id"]]
                pred = ekf_en + s["d"]
                tau = k["sim"] - s["t_fix"]
                t0 = time.perf_counter()
                w = D.dopasuj(fk, pred + off, R3.r_szuk(tau))
                if r["id"] == "wszystko":
                    czasy[kd].append(t_k + (time.perf_counter() - t0) * 1e3)
                fix = None if not (w and w.get("ok")) else np.array(w["cam_en"]) - off
                err = None if fix is None else float(np.linalg.norm(fix - gt_en))
                innow = None if fix is None else float(np.linalg.norm(fix - pred))
                ok = przyjmij(r, w, innow, tau)
                if fix is None:
                    s["brak"] += 1
                else:
                    s["err_all"].append(err)
                if ok:
                    s["d"] = fix - ekf_en
                    s["t_fix"] = k["sim"]
                    s["acc"].append(k["sim"])
                    s["err_acc"].append(err)
                if tryb == "ocena":
                    s["klatki"].append([round(k["sim"], 3), None if err is None else round(err, 4), int(ok),
                                        round(float(np.linalg.norm(pred - gt_en)), 4), round(tau, 3),
                                        None if not w or not w.get("ok") else {kk: (round(v, 4) if isinstance(v, float) else v)
                                                                                for kk, v in w.items() if kk not in ("ok", "cam_en")}])
    wyn = {"lot": lot, "lata": lata, "wariant": wariant, "n_klatek": len(K), "t_cut": t_cut, "t_end": t_end,
           "klatki_z_pikselami_poza_oknem": int(poza_okn), "czas_prost_ms_p50": float(np.median(czas_prost)),
           "czas_ms_p50": {kd: float(np.median(v)) for kd, v in czasy.items()},
           "czas_ms_p95": {kd: float(np.quantile(v, .95)) for kd, v in czasy.items()}, "kand": {}}
    for kd in det:
        wyn["kand"][kd] = {}
        for r in RG[kd]:
            s = st[kd][r["id"]]
            ts = [t_cut] + s["acc"] + [t_end]
            gaps = np.diff(ts)
            ea = np.array(s["err_acc"]); eall = np.array(s["err_all"])
            o = {"regula": r, "n": len(K), "brak": s["brak"], "n_wynik": len(eall), "n_przyj": len(ea),
                 "err_all": None if not len(eall) else {"p50": float(np.quantile(eall, .5)), "p95": float(np.quantile(eall, .95)),
                                                         "p99": float(np.quantile(eall, .99)), "max": float(eall.max()),
                                                         "gt_137": int((eall > PROG_D).sum()), "gt_228": int((eall > PROG_S).sum())},
                 "err_acc_max": float(ea.max()) if len(ea) else None, "err_acc_p50": float(np.median(ea)) if len(ea) else None,
                 "acc_gt_137": int((ea > PROG_D).sum()), "acc_gt_100": int((ea > 1.0).sum()), "acc_gt_228": int((ea > PROG_S).sum()),
                 "przerwa_max": float(gaps.max()), "przerwy_gt_115": int((gaps > 1.15).sum()), "przerwy_gt_215": int((gaps > 2.15).sum())}
            if tryb == "ocena":
                o["klatki"] = s["klatki"]
            wyn["kand"][kd][r["id"]] = o
    return wyn


def main():
    tryb = sys.argv[1]
    npr = int(sys.argv[2]) if len(sys.argv) > 2 else 22
    loty = sorted({k["lot"] for k in json.load(gzip.open(os.path.join(OUT, "r2_klatki.json.gz"), "rt"))})
    wybrane = {}
    if tryb == "strojenie":
        loty = [l for l in loty if "_c05_" in l]
    else:
        wybrane = json.load(open(os.path.join(OUT, "r5_reguly.json")))["wybrane"]
    zad = [(l, a, w, tryb, wybrane) for l in loty for a in LATY for w in WARIANTY]
    zad.sort(key=lambda z: z[0] != "L_c10_s01")                    # najdłuższy lot najpierw
    cz = os.path.join(OUT, f"r4_{tryb}_czesci")                     # zapis cząstkowy (wznowienie po przerwie); usuwany po scaleniu
    os.makedirs(cz, exist_ok=True)
    nazwa = lambda z: os.path.join(cz, f"{z[0]}_{z[1]}_{z[2]}.json.gz")
    out = [json.load(gzip.open(nazwa(z), "rt")) for z in zad if os.path.exists(nazwa(z))]
    zad = [z for z in zad if not os.path.exists(nazwa(z))]
    print("wznowienie: gotowe", len(out), "do zrobienia", len(zad), flush=True)
    with Pool(npr) as p:
        for w in p.imap_unordered(zadanie, zad):
            with gzip.open(nazwa((w["lot"], w["lata"], w["wariant"])) + ".tmp", "wt") as f:
                json.dump(w, f)
            os.replace(nazwa((w["lot"], w["lata"], w["wariant"])) + ".tmp", nazwa((w["lot"], w["lata"], w["wariant"])))
            out.append(w)
            print(time.strftime("%T"), w["lot"], w["lata"], w["wariant"], "ms", {k: round(v, 1) for k, v in w["czas_ms_p50"].items()},
                  {kd: (v["wszystko"]["n_wynik"], v["wszystko"]["err_all"] and round(v["wszystko"]["err_all"]["p50"], 2))
                   for kd, v in w["kand"].items()}, flush=True)
    fn = os.path.join(OUT, f"r4_{tryb}.json.gz")
    with gzip.open(fn, "wt") as f:
        json.dump(out, f)
    print("zapis", fn)


if __name__ == "__main__":
    main()
