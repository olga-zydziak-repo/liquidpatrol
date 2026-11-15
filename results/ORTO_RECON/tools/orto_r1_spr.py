#!/usr/bin/env python3
"""results/ORTO_RECON/tools/orto_r1_spr.py — sprawdziany R1 (PROMPT_ORTO_S0 R1; 0 bootów; sieć: tylko usługi GUGiK z orto_r1).

(s1) przeliczenie układów: ta sama edycja (2012-04-28) z arkusza PL-1992 i z arkusza PL-2000:S6, oba okna w siatce PL-1992 przez
     orto_r1.okno; przesunięcie korelacją fazową [px 0.1 m] i odpowiedź — sprawdza własne wzory orto_uklad (dwa różne odwzorowania).
(s2) okno każdej edycji RGB wobec WMS HighResolution GetMap tego samego prostokąta (1000 × 1000 px = 0.1 m): która edycja jest
     serwowana (największa odpowiedź) i przesunięcie wobec niej.
(s3) TrueOrtho: GetMap warstw PrawdziwaOrtofotomapa i Skorowidze w prostokącie łaty — czy obraz niepusty (odchylenie jasności).
(s4) ostrość źródła per edycja: energia gradientu po rozmyciu do piksela f·p (f = 2, 4, 8, 16) względem oryginału; „piksel efektywny”
     = najmniejsze f·p, przy którym zostaje < 50 % energii gradientu (miara opisowa, nie zamrożenie).
Wyjście: results/ORTO_RECON/r1_sprawdziany.json; podglądy w katalogu z argumentu (scratchpad), nie w repo.
Użycie: orto_r1_spr.py <katalog_podgladow>
"""
import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orto_r1 as R
import orto_uklad as UK

POL = R.OKNO_M / 2


def szary(a):
    return np.float32(cv2.cvtColor(a, cv2.COLOR_BGR2GRAY))


def do_01(a, p):
    return a if abs(p - 0.1) < 1e-9 else cv2.resize(a, (1000, 1000), interpolation=cv2.INTER_AREA)


def korel(a, b):
    w = cv2.createHanningWindow(a.shape[1::-1], cv2.CV_32F)
    (dx, dy), r = cv2.phaseCorrelate(szary(a), szary(b), w)
    return {"dx_px": round(dx, 3), "dy_px": round(dy, 3), "odpowiedz": round(r, 4)}


def ostrosc(a, p):
    g = szary(a)
    e0 = float(np.mean(cv2.Sobel(g, cv2.CV_32F, 1, 0) ** 2 + cv2.Sobel(g, cv2.CV_32F, 0, 1) ** 2))
    out, eff = {}, None
    for f in (2, 4, 8, 16):
        n = g.shape[0] // f
        b = cv2.resize(cv2.resize(g, (n, n), interpolation=cv2.INTER_AREA), g.shape[1::-1], interpolation=cv2.INTER_LINEAR)
        e = float(np.mean(cv2.Sobel(b, cv2.CV_32F, 1, 0) ** 2 + cv2.Sobel(b, cv2.CV_32F, 0, 1) ** 2))
        out[f"{f * p:.2f}m"] = round(e / e0, 3)
        if eff is None and e / e0 < 0.5:
            eff = round(f * p, 2)
    return {"energia_po_rozmyciu": out, "piksel_efektywny_m": eff}


def main():
    pod = sys.argv[1]
    os.makedirs(pod, exist_ok=True)
    R.LATA = R.lata_wfs()
    L = json.load(open(os.path.join(R.OUT, "laty.json")))["laty"]
    wyn = {}
    for nm, l in L.items():
        xN, yE = UK.wgs84_do_2180(l["lat"], l["lon"])
        ed = [e for e in R.wfs_edycje(xN, yE) if e["piksel"] <= R.PIKSEL_MAX + 1e-9 and e["url"] and R.pokrywa(e["poligon_2180"], xN, yE, POL)]
        w = {"s1": None, "s2": {}, "s3": {}, "s4": {}}
        okna = {}
        for e in sorted(ed, key=lambda e: (e["akt_data"], e["uklad"])):
            if e["kolor"] != "RGB":
                continue
            try:
                t = R.TiffZdalny(e["url"])
            except KeyError as ex:                              # TIFF paskowy (bez tagów kafli 322/323) — czytnik obsługuje tylko kafle
                w["s4"][f"{e['akt_data']} {e['uklad']}"] = {"nieczytany": f"brak tagu {ex} (TIFF paskowy)", "arkusz": e["godlo"],
                                                            "wlk_mb": e["wlk_mb"]}
                continue
            im, geo = R.okno(t, e["uklad"], xN, yE, POL, t.sx)
            if im is None:
                continue
            okna[(e["akt_data"], e["uklad"])] = (im, t.sx)
            w["s4"][f"{e['akt_data']} {e['uklad']}"] = dict(ostrosc(im, t.sx), piksel_m=t.sx, arkusz=e["godlo"])
            cv2.imwrite(os.path.join(pod, f"{nm}_{e['akt_data']}_{e['uklad'].replace(':', '')}.jpg"), cv2.resize(im, (500, 500)))
            print(nm, e["akt_data"], e["uklad"], w["s4"][f"{e['akt_data']} {e['uklad']}"]["piksel_efektywny_m"], flush=True)
        a, b = okna.get(("2012-04-28", "PL-1992")), okna.get(("2012-04-28", "PL-2000:S6"))
        if a and b:
            w["s1"] = dict(korel(do_01(*a), do_01(*b)), para="2012-04-28 PL-1992 vs PL-2000:S6")
        X0, X1, Y0, Y1 = yE - POL, yE + POL, xN - POL, xN + POL
        hr, q = R.wms_getmap(R.WMS_HR, "Raster", X0, Y0, X1, Y1, 1000, 1000)
        cv2.imwrite(os.path.join(pod, f"{nm}_WMS_HR.jpg"), cv2.resize(hr, (500, 500)))
        w["s2"] = {"zapytanie": q, "edycje": {f"{k[0]} {k[1]}": korel(hr, do_01(*v)) for k, v in okna.items()}}
        best = max(w["s2"]["edycje"].items(), key=lambda kv: kv[1]["odpowiedz"])
        w["s2"]["serwowana"] = best[0]
        for war in ("PrawdziwaOrtofotomapa", "Skorowidze"):
            try:
                im, q = R.wms_getmap(R.WMS_TRUE, war, X0, Y0, X1, Y1, 500, 500)
                w["s3"][war] = {"zapytanie": q, "odchylenie_jasnosci": round(float(szary(im).std()), 2) if im is not None else None,
                                "srednia": round(float(szary(im).mean()), 1) if im is not None else None}
                if im is not None:
                    cv2.imwrite(os.path.join(pod, f"{nm}_TRUE_{war}.jpg"), im)
            except Exception as ex:                      # noqa: BLE001 — brak warstwy = wynik, nie awaria
                w["s3"][war] = {"blad": str(ex)}
        wyn[nm] = w
        print(nm, "s1", w["s1"], "s2", best, "s3", {k: v.get("odchylenie_jasnosci") for k, v in w["s3"].items()}, flush=True)
    json.dump(wyn, open(os.path.join(R.OUT, "r1_sprawdziany.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
