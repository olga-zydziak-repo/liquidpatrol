#!/usr/bin/env python3
"""results/TEACH_RECON/tools/teach_r1.py — PROMPT_TEACH_S0 R1: teren łat S, M, J z jednej edycji 2024-04-27 (0 bootów; sieć: GUGiK).

Łaty z results/TEACH_RECON/laty.json (commit przed dopasowaniem). Edycja z WFS Skorowidze (gugik:SkorowidzOrtofomapy2024), arkusz
GeoTIFF pokrywający okno 100 × 100 m (preferowany PL-1992), okno w siatce PL-1992, N do góry, piksel arkusza (0.05 m) — czytnik
i przeliczenie z results/ORTO_RECON/tools/orto_r1.py (import, bez zmian). Sprawdzian ostrości jak orto_r1_spr.ostrosc (energia gradientu
po rozmyciu; „piksel efektywny” = najmniejsze f·p z < 50 % energii) — dla łaty J wymóg promptu: źródło nie jest zgrubione.
Wyjście: results/TEACH_RECON/dane/<łata>_2024-04-27.png, dane/pochodzenie.json, r1_dane.json.
"""
import hashlib
import json
import os
import sys
import time

import cv2

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, os.path.join(ROOT, "results/ORTO_RECON/tools"))
import orto_r1 as R
import orto_r1_spr as SPR
import orto_uklad as UK

OUT = os.path.join(ROOT, "results/TEACH_RECON")
DANE = os.path.join(OUT, "dane")
EDYCJA = "2024-04-27"
POL = 50.0


def main():
    R.LATA = [r for r in R.lata_wfs() if str(r) == EDYCJA[:4]]
    L = json.load(open(os.path.join(OUT, "laty.json")))["laty"]
    os.makedirs(DANE, exist_ok=True)
    poch = {"zrodlo_strony": "https://www.geoportal.gov.pl/dane/ortofotomapa (adresy usług jak w recon ORTO R1)",
            "data_pobrania": time.strftime("%F"), "pliki": {}}
    wyn = {}
    for nm, l in L.items():
        xN, yE = UK.wgs84_do_2180(l["lat"], l["lon"])
        ed = [e for e in R.wfs_edycje(xN, yE) if e["akt_data"] == EDYCJA and e["url"] and R.pokrywa(e["poligon_2180"], xN, yE, POL)]
        ed.sort(key=lambda e: e["uklad"] != "PL-1992")
        if not ed:
            raise SystemExit(f"{nm}: brak arkusza {EDYCJA} pokrywającego okno")
        e = ed[0]
        t = R.TiffZdalny(e["url"])
        im, geo = R.okno(t, e["uklad"], xN, yE, POL, t.sx)
        if im is None:
            raise SystemExit(f"{nm}: okno poza arkuszem {geo}")
        fn = f"{nm}_{EDYCJA}.png"
        cv2.imwrite(os.path.join(DANE, fn), im)
        sha = hashlib.sha256(open(os.path.join(DANE, fn), "rb").read()).hexdigest()
        poch["pliki"][fn] = {"lata": nm, "usluga": R.WFS, "warstwa": f"gugik:SkorowidzOrtofomapy{EDYCJA[:4]}", "arkusz": e["godlo"],
                             "url_zrodla": e["url"], "edycja_nr_zglosz": e["nr_zglosz"], "data_nalotu": e["akt_data"],
                             "uklad_arkusza": e["uklad"], "uklad_okna": "PL-1992 (EPSG:2180)", "piksel_m": geo["piksel"],
                             "okno_2180": {"X_wsch": [yE - POL, yE + POL], "Y_poln": [xN - POL, xN + POL]}, "geo_okna": geo,
                             "rozmiar_px": list(im.shape[:2]), "sha256": sha}
        wyn[nm] = {"lat": l["lat"], "lon": l["lon"], "x_2180": round(xN, 3), "y_2180": round(yE, 3), "klasa": l["klasa"], "plik": fn,
                   "piksel_m": t.sx, "arkusz": e["godlo"], "uklad_arkusza": e["uklad"], "ostrosc": SPR.ostrosc(im, t.sx)}
        print(nm, fn, im.shape, e["godlo"], e["uklad"], wyn[nm]["ostrosc"], flush=True)
    json.dump(poch, open(os.path.join(DANE, "pochodzenie.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(wyn, open(os.path.join(OUT, "r1_dane.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
