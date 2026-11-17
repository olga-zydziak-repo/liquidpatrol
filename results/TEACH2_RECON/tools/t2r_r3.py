#!/usr/bin/env python3
"""results/TEACH2_RECON/tools/t2r_r3.py — PROMPT_TEACH2_S0 §5: wierność przyrządu i R3 nauka z innego przebiegu (0 bootów).

Wierność (--tryb wiernosc): lot bramki S3 na własnej łacie, wszystkie klatki zapisu po kolei z flagą GNSS z wiersza (stan przy
klatce, jak w locie: Producent.obserwacja bez chwili flagi); okno od klatki zamknięcia do końca misji: udział przyjętych, błąd
poprawki |fix − GT_EN| p50 / max — wobec lotu (prompt §5: p01 0.730 / 0.428, p02 0.436 / 0.251; tolerancja max ±0.15, p50 ±0.08,
udział ≥ 99 %).
R3 (--tryb r3): mapa z lotu uczącego (klatki do końca misji z flagą 1; moduł sam pomija klatki poniżej 6 m), zamknięcie po
ostatnim kadrze (kadr z bufora wchodzi — ostatni kadr nauki; Producent._wlacz_do_mapy + _zamknij, ta sama ścieżka co w locie),
stan po zamknięciu klonowany dla każdego z 6 lotów powtarzających tej samej komórki. Lot powtarzający: klatki od pierwszej z
wysokością EKF ≥ 6 m do końca misji, każda z własną migawką EKF, flaga 0, czas przesunięty: pierwsza klatka 0.2 s po ostatnim
kadrze nauki. Okna wg czasu epizodu lotu powtarzającego: „wspolne” t_ep ≤ koniec misji nauki (czas epizodu nauki), „dalej” później.
Zapis cząstkowy po każdym przebiegu: <OUT>/r3_czesci/<nauka>_<łata>_<powt>.json.gz; podsumowanie <OUT>/r3.json.
Użycie: t2r_r3.py --tryb wiernosc|r3 [--procesy N] [--laty S,M,J]
"""
import argparse
import gzip
import json
import os
import resource
import sys
import time
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t2r_dane as D                                      # noqa: E402

TM = D.TM
NAUKA = {"c05": ["c1_cien_S_c05", "p10_N2_J_c05_cien"], "c10": ["p05_N1_S_c10_cien", "c2_cien_J_c10"]}
POWT = {"c05": ["p01_S_c05_a", "p03_S_c05_b", "p06_M_c05_a", "p08_M_c05_b", "p11_J_c05_a", "p13_J_c05_b"],
        "c10": ["p02_S_c10_a", "p04_S_c10_b", "p07_M_c10_a", "p09_M_c10_b", "p12_J_c10_a", "p14_J_c10_b"]}
WIERNOSC = {"p01_S_c05_a": ("S", 0.730, 0.428), "p02_S_c10_a": ("S", 0.436, 0.251)}
CZ = os.path.join(D.OUT, "r3_czesci")


def wiersz(sim, t_ep, reg, k):
    w = {"sim": round(sim, 3), "t_ep": round(t_ep, 3), "ok": 0, "k": None, "zgodne": None, "err": None, "innow": None}
    if reg.get("k") is not None:
        fix = np.array(reg["fix_en"])
        w.update(k=reg["k"], zgodne=reg["zgodne"], ok=int(reg["ok"]), innow=round(reg["innowacja"], 4),
                 err=round(float(np.linalg.norm(fix - np.asarray(k["gt_p"][:2]))), 4))
    return w


def wiernosc(nazwa):
    import cv2
    cv2.setNumThreads(1)
    t0 = time.time()
    lata, ref_max, ref_p50 = WIERNOSC[nazwa]
    L = D.lot(nazwa)
    ren = D.Render(lata)
    P = TM.Producent(wariant=D.WARIANT)
    rows, t_zamk, georef = [], None, None
    for k in L["klatki"]:
        if k["sim"] > L["koniec"]:
            break
        pos = k["ekf_pos"]
        potrzebny = pos is not None and (-pos[2] >= TM.H_MIN or P.zamknieta or P.kadry)
        img = ren(k) if potrzebny else None
        P.obserwacja(k["sim"], img, k["ekf_q"], pos, k["gnss"])
        reg = P.rejestr
        if "georef" in reg:
            t_zamk, georef = k["sim"], reg["georef"]
        if reg.get("faza") == "lok":
            rows.append(wiersz(k["sim"], k["sim"] - L["t_ep"], reg, k))
    okn = [r for r in rows if t_zamk <= r["sim"] <= L["koniec"]]
    acc = [r for r in okn if r["ok"]]
    e = [r["err"] for r in acc]
    udz = len(acc) / len(okn)
    mx, p50 = max(e), float(np.median(e))
    lot_s = L["zrodlo"]["blad_poprawki"]
    wyn = {"lot": nazwa, "lata": lata, "t_zamkniecia": t_zamk, "t_zamkniecia_lot": L["zrodlo"]["os_czasu"]["klatka_zamkniecia"],
           "koniec_misji": L["koniec"], "kadry_okna": len(okn), "przyjete": len(acc), "udzial": round(udz, 4),
           "max": round(mx, 4), "p50": round(p50, 4), "ref_prompt": {"max": ref_max, "p50": ref_p50},
           "lot_sedzia": lot_s, "d_max": round(mx - ref_max, 4), "d_p50": round(p50 - ref_p50, 4),
           "n_kadrow_mapy": georef["n_kadrow_mapy"], "n_kf": georef["n_kf"], "n_wiazan": georef["n_wiazan"],
           "n_kadrow_mapy_lot": L["zrodlo"]["georef"]["n_kadrow_mapy"], "n_kf_lot": L["zrodlo"]["georef"]["n_kf"],
           "zegar_s": round(time.time() - t0, 1)}
    wyn["pass"] = udz >= 0.99 and abs(wyn["d_max"]) <= 0.15 and abs(wyn["d_p50"]) <= 0.08
    return wyn


def okno(rows, t0, t1, flaga=None, granica=None):
    acc = [r for r in rows if r["ok"]]
    zg = [r["zgodne"] or 0 for r in rows]
    o = {"kadry": len(rows), "przyjete": len(acc), "udzial": round(len(acc) / len(rows), 4) if rows else None,
         "blad": D.rozklad([r["err"] for r in acc]),
         "przerwy": D.przerwy(t0, [r["t_ep"] for r in acc], t1) if rows else None,
         "zgodne_p5": int(np.quantile(zg, .05)) if zg else None, "zgodne_p50": int(np.median(zg)) if zg else None}
    if granica is not None and o["przerwy"]:
        dz = o["przerwy"]["lista_gt_115"]
        o["do_pierwszej_przerwy_s"] = round(dz[0][0] - granica, 3) if dz else None
    if flaga is not None:
        for nm, sub in (("przed_flaga", [r for r in rows if r["sim"] < flaga]), ("po_fladze", [r for r in rows if r["sim"] >= flaga])):
            a = [r for r in sub if r["ok"]]
            o[nm] = {"kadry": len(sub), "przyjete": len(a), "udzial": round(len(a) / len(sub), 4) if sub else None,
                     "blad": D.rozklad([r["err"] for r in a])}
    return o


def r3_zadanie(arg):
    nauka, lata, kom = arg
    import cv2
    cv2.setNumThreads(1)
    t0 = time.time()
    ren = D.Render(lata)
    L = D.lot(nauka)
    P = TM.Producent(wariant=D.WARIANT)
    ost = None
    for k in L["klatki"]:
        if k["sim"] > L["koniec"]:
            break
        pos = k["ekf_pos"]
        img = ren(k) if (pos is not None and -pos[2] >= TM.H_MIN) else None
        P.obserwacja(k["sim"], img, k["ekf_q"], pos, 1)
        ost = k["sim"]
    a = time.perf_counter()
    if P.bufor is not None:
        P._wlacz_do_mapy(P.bufor)
        P.bufor = None
    P._zamknij(ost)
    ms_zamk = round((time.perf_counter() - a) * 1e3, 2)
    g = P.georef
    mapa = {"n_kadrow_mapy": g["n_kadrow_mapy"], "n_kf": g["n_kf"], "n_wiazan": g["n_wiazan"],
            "n_wiazan_przyjetych": g["n_wiazan_przyjetych"], "ms_zamkniecie": g["ms_zamkniecie"], "ms_z_ostatnim_kadrem": ms_zamk,
            "ostatni_kadr": ost, "pierwszy_kadr_mapy": P.kadry[0]["sim"] if P.kadry else None}
    kon_ep = L["koniec"] - L["t_ep"]
    out = []
    for rep in POWT[kom]:
        t1 = time.time()
        R = D.lot(rep)
        kl = [k for k in R["klatki"] if k["sim"] <= R["koniec"]]
        i0 = next(i for i, k in enumerate(kl) if k["ekf_pos"] is not None and -k["ekf_pos"][2] >= TM.H_MIN)
        kl = kl[i0:]
        shift = ost + 0.2 - kl[0]["sim"]
        Q = D.klon(P)
        rows = []
        for k in kl:
            Q.obserwacja(k["sim"] + shift, ren(k), k["ekf_q"], k["ekf_pos"], 0)
            reg = Q.rejestr
            if reg.get("faza") == "lok":
                rows.append(wiersz(k["sim"], k["sim"] - R["t_ep"], reg, k))
        wsp = [r for r in rows if r["t_ep"] <= kon_ep]
        dal = [r for r in rows if r["t_ep"] > kon_ep]
        w = {"nauka": nauka, "lata": lata, "powt": rep, "komorka": kom, "koniec_nauki_ep": round(kon_ep, 3),
             "koniec_misji_ep": round(R["koniec"] - R["t_ep"], 3), "flaga_ep": round(R["flaga"] - R["t_ep"], 3),
             "wspolne": okno(wsp, wsp[0]["t_ep"], min(kon_ep, rows[-1]["t_ep"]), flaga=R["flaga"]) if wsp else None,
             "dalej": okno(dal, kon_ep, R["koniec"] - R["t_ep"], granica=kon_ep) if dal else None,
             "mapa": mapa, "zegar_s": round(time.time() - t1, 1)}
        ws = w["wspolne"]
        w["warunek_S1"] = bool(ws and ws["blad"] and ws["blad"]["max"] <= 1.00 and ws["przerwy"]["gt_115"] == 0)
        fn = os.path.join(CZ, f"{nauka}_{lata}_{rep}.json.gz")
        with gzip.open(fn + ".tmp", "wt") as f:
            json.dump(dict(w, wiersze=rows), f)
        os.replace(fn + ".tmp", fn)
        out.append(w)
        print(time.strftime("%T"), nauka, lata, rep, "S1", w["warunek_S1"],
              "wsp", ws and ws["blad"] and ws["blad"]["max"], ws and ws["przerwy"]["gt_115"],
              "dal", w["dalej"] and w["dalej"]["udzial"], w["dalej"] and w["dalej"]["przerwy"]["gt_115"], w["zegar_s"], flush=True)
    return {"nauka": nauka, "lata": lata, "mapa": mapa, "przebiegi": out, "zegar_s": round(time.time() - t0, 1),
            "rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tryb", required=True, choices=("wiernosc", "r3"))
    ap.add_argument("--procesy", type=int, default=8)
    ap.add_argument("--laty", default="S,M,J")
    a = ap.parse_args()
    t0 = time.time()
    if a.tryb == "wiernosc":
        with Pool(2) as p:
            wyn = p.map(wiernosc, list(WIERNOSC))
        out = {"wyniki": wyn, "pass": all(w["pass"] for w in wyn), "sumy_toru": TM.sumy_toru(), "wariant": D.WARIANT,
               "zegar_s": round(time.time() - t0, 1)}
        json.dump(out, open(os.path.join(D.OUT, "wiernosc.json"), "w"), ensure_ascii=False, indent=1)
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return
    os.makedirs(CZ, exist_ok=True)
    zad = [(n, s, kom) for kom in ("c10", "c05") for n in NAUKA[kom] for s in a.laty.split(",")]
    wyn = []
    with Pool(min(a.procesy, 8)) as p:
        for w in p.imap_unordered(r3_zadanie, zad):
            wyn.append(w)
            print(time.strftime("%T"), f"{time.time() - t0:.0f}s", "zadanie", w["nauka"], w["lata"], w["mapa"], w["zegar_s"], flush=True)
    wyn.sort(key=lambda w: ("SMJ".index(w["lata"]), w["nauka"]))
    per = {}
    for w in wyn:
        for x in w["przebiegi"]:
            per.setdefault(x["lata"], []).append(x)
    lat = {}
    for s, xs in per.items():
        def mx(okn):
            v = [(x[okn]["blad"]["max"], x["nauka"], x["powt"]) for x in xs if x[okn] and x[okn]["blad"]]
            return max(v) if v else None
        dal = [x["dalej"] for x in xs if x["dalej"]]
        c10 = [x["dalej"] for x in xs if x["dalej"] and x["komorka"] == "c10"]
        lat[s] = {"pary": len(xs), "pary_S1_ok": sum(x["warunek_S1"] for x in xs), "max_wspolne": mx("wspolne"), "max_dalej": mx("dalej"),
                  "dalej_udzial_lacznie": round(sum(o["przyjete"] for o in dal) / sum(o["kadry"] for o in dal), 4) if dal else None,
                  "dalej_udzial_c10": round(sum(o["przyjete"] for o in c10) / sum(o["kadry"] for o in c10), 4) if c10 else None,
                  "wspolne_przerwy_gt115": sum(x["wspolne"]["przerwy"]["gt_115"] for x in xs if x["wspolne"]),
                  "dalej_przerwy_gt115": sum(o["przerwy"]["gt_115"] for o in dal)}
    out = {"laty": lat, "S1_zachodzi": any(v["pary_S1_ok"] < 22 for v in lat.values()), "zadania": wyn,
           "sumy_toru": TM.sumy_toru(), "wariant": D.WARIANT, "procesy": a.procesy, "zegar_s": round(time.time() - t0, 1)}
    json.dump(out, open(os.path.join(D.OUT, "r3.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(lat, ensure_ascii=False, indent=1), "S1", out["S1_zachodzi"], flush=True)


if __name__ == "__main__":
    main()
