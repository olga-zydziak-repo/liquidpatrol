#!/usr/bin/env python3
"""results/ORTO_RECON/tools/orto_r1.py — PROMPT_ORTO_S0 R1: edycje ortofotomapy dla trzech łat i pobranie okien (0 bootów).

Usługi (adresy ze strony https://www.geoportal.gov.pl/dane/ortofotomapa → /pl/dane/ortofotomapa-orto/, pobrana 15.11.2026):
  - WFS skorowidzów   https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WFS/Skorowidze (warstwy gugik:SkorowidzOrtofomapy<rok>,
    atrybuty: godło, akt_rok, piksel, kolor, akt_data (data nalotu), układ, url_do_pobrania, wlk_pliku_mb);
  - pliki arkuszy GeoTIFF z url_do_pobrania (opendata.geoportal.gov.pl) — czytane ŻĄDANIAMI HTTP Range wyłącznie dla kafli okna
    (TIFF kafelkowany 256 × 256, JPEG YCbCr z JPEGTables, georeferencja ModelPixelScale + ModelTiepoint w układzie arkusza:
    PL-1992 albo PL-2000:S6 — okno zawsze przeliczane do siatki PL-1992 przez orto_uklad);
  - WMS HighResolution (bieżąca edycja) — sprawdzian odczytu okna; WMS TrueOrtho — sprawdzenie istnienia ortofotomapy prawdziwej.
Okno: kwadrat 80 m + margines 10 m z każdej strony (100 × 100 m) wokół środka łaty w PL-1992, osie: wiersze = północ w górę.
Edycje: wszystkie arkusze z pikselem ≤ 0.10 m pokrywające całe okno 100 m (jeśli okno leży na styku arkuszy tej samej edycji —
mozaika z kilku arkuszy tej samej daty). Para pomiarowa: dwie edycje o największym odstępie dat nalotu („świat” = starsza,
„mapa” = nowsza); kontrola: ta sama edycja („mapa”) po obu stronach.
Sprawdziany (układy, WMS HighResolution, TrueOrtho, ostrość źródła): orto_r1_spr.py → r1_sprawdziany.json.
Wyjście: results/ORTO_RECON/dane/<łata>_<rola>_<data>.png (RGB, natywny piksel arkusza, siatka PL-1992, północ w górę),
results/ORTO_RECON/dane/pochodzenie.json, results/ORTO_RECON/r1_dane.json.
"""
import hashlib
import io
import json
import math
import os
import re
import struct
import sys
import time
import urllib.request

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orto_uklad as UK

ROOT = "/home/olga/projects/liquidpatrol"
OUT = os.path.join(ROOT, "results/ORTO_RECON")
DANE = os.path.join(OUT, "dane")
WFS = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WFS/Skorowidze"
WMS_HR = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/HighResolution"
WMS_TRUE = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/TrueOrtho"
LATA = None                                         # lata warstw z GetCapabilities WFS (nie każdy rok ma warstwę)


def lata_wfs():
    t = http(f"{WFS}?SERVICE=WFS&REQUEST=GetCapabilities").decode("utf8", "replace")
    return sorted({int(r) for r in re.findall(r"<Name>gugik:SkorowidzOrtofomapy(\d{4})</Name>", t)})
OKNO_M = 100.0
PIKSEL_MAX = 0.10
UA = {"User-Agent": "LiquidPatrol-ORTO-recon/1.0"}


def http(url, zakres=None, proby=4):
    for k in range(proby):
        try:
            req = urllib.request.Request(url, headers=dict(UA, **({"Range": f"bytes={zakres[0]}-{zakres[1]}"} if zakres else {})))
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except Exception as ex:                          # noqa: BLE001 — ponowienie przy chwilowym błędzie sieci
            if k == proby - 1:
                raise
            time.sleep(2 + 3 * k)


def wfs_edycje(x, y, pol=OKNO_M / 2):
    bbox = f"{x - pol},{y - pol},{x + pol},{y + pol},urn:ogc:def:crs:EPSG::2180"
    out = []
    for rok in LATA or lata_wfs():
        url = (f"{WFS}?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=gugik:SkorowidzOrtofomapy{rok}&BBOX={bbox}")
        t = http(url).decode("utf8", "replace")
        for m in re.finditer(r"<wfs:member>(.*?)</wfs:member>", t, re.S):
            f = m.group(1)
            g = lambda k: (re.search(rf"<gugik:{k}>([^<]*)</gugik:{k}>", f) or [None, None])[1]
            dt = re.search(r"<gugik:akt_data[^>]*><gml:timePosition>([^<]+)</gml:timePosition>", f)
            pos = re.search(r"<gml:posList[^>]*>([^<]+)</gml:posList>", f)
            pts = [float(v) for v in pos.group(1).split()] if pos else []
            poly = list(zip(pts[0::2], pts[1::2]))
            out.append({"rok": rok, "godlo": g("godlo"), "akt_rok": g("akt_rok"), "piksel": float(g("piksel") or "nan"), "kolor": g("kolor"),
                        "zrodlo": g("zrodlo_danych"), "uklad": g("uklad_xy"), "modul": g("modul_archiwizacji"), "nr_zglosz": g("nr_zglosz"),
                        "akt_data": dt.group(1) if dt else None, "url": g("url_do_pobrania"), "wlk_mb": g("wlk_pliku_mb"),
                        "wypelniony": g("czy_ark_wypelniony"), "poligon_2180": poly})
    return out


def w_poligonie(px, py, poly):
    c = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > py) != (y2 > py) and px < x1 + (py - y1) * (x2 - x1) / (y2 - y1):
            c = not c
    return c


def pokrywa(poly, x, y, pol):
    return all(w_poligonie(x + dx, y + dy, poly) for dx in (-pol, pol) for dy in (-pol, pol))


class _Bufor:
    """Widok bajtów pliku zdalnego: blok od offsetu `o0` w pamięci, reszta doczytywana Range — indeksowanie jak bytes."""

    def __init__(self, o0, blok, url):
        self.o0, self.b, self.url = o0, blok, url

    def __len__(self):
        return self.o0 + len(self.b)

    def __getitem__(self, s):
        a, z = s.start, s.stop
        if a >= self.o0 and z <= self.o0 + len(self.b):
            return self.b[a - self.o0:z - self.o0]
        return http(self.url, (a, z - 1))


class TiffZdalny:
    """Kafelkowany GeoTIFF czytany żądaniami Range: nagłówek IFD, tablice offsetów kafli, JPEGTables, georeferencja."""

    def __init__(self, url):
        self.url = url
        h = http(url, (0, 262143))
        self.bo = "<" if h[:2] == b"II" else ">"
        bo = self.bo
        off = struct.unpack(bo + "I", h[4:8])[0]
        if off + 2 + 12 * 64 > len(h):                    # IFD na końcu pliku (np. edycje 2012) — blok spod offsetu, reszta Range
            h = _Bufor(off, http(url, (off, off + 65535)), url)
        n = struct.unpack(bo + "H", h[off:off + 2])[0]
        self.tag = {}
        rozm = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 7: 1, 11: 4, 12: 8, 16: 8}
        fmt = {1: "B", 2: "c", 3: "H", 4: "I", 5: "II", 7: "B", 11: "f", 12: "d", 16: "Q"}
        for i in range(n):
            tg, ty, c, v = struct.unpack(bo + "HHI4s", h[off + 2 + 12 * i:off + 14 + 12 * i])
            dl = rozm[ty] * c
            if dl <= 4:
                raw = v[:dl]
            else:
                o = struct.unpack(bo + "I", v)[0]
                raw = h[o:o + dl] if o + dl <= len(h) else http(url, (o, o + dl - 1))
            if ty == 7 or ty == 2:
                val = raw
            else:
                val = list(struct.unpack(bo + fmt[ty][-1] * (c * (2 if ty == 5 else 1)), raw))
            self.tag[tg] = (ty, val)
        self.W, self.H = self.tag[256][1][0], self.tag[257][1][0]
        self.tw, self.th = self.tag[322][1][0], self.tag[323][1][0]
        self.offs, self.cnts = self.tag[324][1], self.tag[325][1]
        self.jt = self.tag.get(347, (None, None))[1]
        self.compr, self.photo = self.tag[259][1][0], self.tag[262][1][0]
        sx, sy, _ = self.tag[33550][1]
        tp = self.tag[33922][1]                     # i, j, k, X, Y, Z — GeoTIFF: X = easting? (sprawdzane GeoKeys poniżej)
        self.sx, self.sy, self.tp = sx, sy, tp
        self.ntx = math.ceil(self.W / self.tw)

    def _tablice(self):
        """Pierwszy blok SOI…EOI z JPEGTables bez EOI (edycje 2012 mają kilka sklejonych bloków — cv2 nie czyta całości); po długościach segmentów."""
        if not hasattr(self, "_tb"):
            jt, i = bytes(self.jt), 2
            while jt[i + 1] != 0xD9:
                i += 2 + jt[i + 2] * 256 + jt[i + 3]
            self._tb = jt[:i]
        return self._tb

    def kafel(self, ti, tj):
        k = tj * self.ntx + ti
        b = http(self.url, (self.offs[k], self.offs[k] + self.cnts[k] - 1))
        assert self.compr == 7, self.compr
        js = (self._tablice() + b[2:]) if self.jt else b
        im = cv2.imdecode(np.frombuffer(js, np.uint8), cv2.IMREAD_COLOR)
        return im, len(b)


def mozaika(tiff, i0, j0, i1, j1):
    """Piksele źródła [i0, i1) × [j0, j1) (kolumny, wiersze) z kafli pobranych Range; poza plikiem zero."""
    out = np.zeros((j1 - j0, i1 - i0, 3), np.uint8)
    pobrane, nk = 0, 0
    for tj in range(max(0, j0) // tiff.th, (min(j1, tiff.H) - 1) // tiff.th + 1):
        for ti in range(max(0, i0) // tiff.tw, (min(i1, tiff.W) - 1) // tiff.tw + 1):
            im, nb = tiff.kafel(ti, tj)
            pobrane += nb; nk += 1
            a0, b0 = ti * tiff.tw, tj * tiff.th
            xs0, ys0 = max(i0, a0), max(j0, b0)
            xs1, ys1 = min(i1, a0 + tiff.tw, tiff.W), min(j1, b0 + tiff.th, tiff.H)
            out[ys0 - j0:ys1 - j0, xs0 - i0:xs1 - i0] = im[ys0 - b0:ys1 - b0, xs0 - a0:xs1 - a0]
    return out, pobrane, nk


def okno(tiff, uklad, xN, yE, pol, piksel):
    """Okno 2·pol × 2·pol m w siatce PL-1992 (wiersze od północy, kolumny na wschód), piksel = `piksel`, środek (xN, yE) w EPSG:2180.
    Mapa pikseli: PL-1992 → WGS84 → układ arkusza (uklad z WFS) liczona na rzadkiej siatce co 1 m i interpolowana liniowo; próbkowanie
    dwuliniowe (cv2.remap). Dla arkusza PL-1992 mapa jest tożsamością (piksel w piksel)."""
    n = int(round(2 * pol / piksel))
    krok = max(1, int(round(1.0 / piksel)))
    g = np.arange(0, n + 1, krok)
    gx, gy = np.meshgrid(g, g)
    E1992 = yE - pol + (gx + 0.5) * piksel
    N1992 = xN + pol - (gy + 0.5) * piksel
    col = np.zeros(gx.shape); row = np.zeros(gx.shape)
    for a in range(gx.shape[0]):
        for b in range(gx.shape[1]):
            if uklad == "PL-1992":
                Ns, Es = N1992[a, b], E1992[a, b]
            else:
                la, lo = UK.p2180_do_wgs84(N1992[a, b], E1992[a, b])
                Ns, Es = UK.wgs84_do_tm(la, lo, uklad)
            col[a, b] = (Es - tiff.tp[3]) / tiff.sx - 0.5
            row[a, b] = (tiff.tp[4] - Ns) / tiff.sy - 0.5
    if krok > 1:                                       # interpolacja dwuliniowa węzłów g w środkach wszystkich pikseli
        xs = np.arange(n) / krok
        mc, mr = _interp2(col, xs), _interp2(row, xs)
    else:
        mc, mr = col[:n, :n].astype(np.float32), row[:n, :n].astype(np.float32)
    i0, i1 = int(math.floor(mc.min())) - 2, int(math.ceil(mc.max())) + 3
    j0, j1 = int(math.floor(mr.min())) - 2, int(math.ceil(mr.max())) + 3
    if i0 < 0 or j0 < 0 or i1 > tiff.W or j1 > tiff.H:
        return None, {"poza_arkuszem": [i0, j0, i1, j1, tiff.W, tiff.H]}
    src, pobrane, nk = mozaika(tiff, i0, j0, i1, j1)
    out = cv2.remap(src, mc - i0, mr - j0, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    tozsamosc = uklad == "PL-1992" and abs(tiff.sx - piksel) < 1e-12
    return out, {"piksel": piksel, "uklad_zrodla": uklad, "kafle": nk, "bajty": pobrane, "zrodlo_px": [i0, j0, i1, j1],
                 "mapa_tozsamosc": bool(tozsamosc)}


def _interp2(gridv, xs):
    """Dwuliniowa interpolacja siatki gridv (węzły co 1 jednostkę) w punktach xs × xs."""
    n = len(xs)
    x0 = np.clip(np.floor(xs).astype(int), 0, gridv.shape[1] - 2); fx = xs - x0
    y0 = x0; fy = fx
    a = gridv[np.ix_(y0, x0)]; b = gridv[np.ix_(y0, x0 + 1)]; c = gridv[np.ix_(y0 + 1, x0)]; d = gridv[np.ix_(y0 + 1, x0 + 1)]
    FX, FY = np.meshgrid(fx, fy)
    return ((1 - FY) * ((1 - FX) * a + FX * b) + FY * ((1 - FX) * c + FX * d)).astype(np.float32)


def wms_getmap(url, warstwa, X0, Y0, X1, Y1, w, h):
    """WMS 1.3.0, EPSG:2180 (oś 1 = northing): BBOX = minN, minE, maxN, maxE."""
    q = (f"{url}?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS={warstwa}&STYLES=&CRS=EPSG:2180&BBOX={Y0},{X0},{Y1},{X1}"
         f"&WIDTH={w}&HEIGHT={h}&FORMAT=image/png")
    b = http(q)
    im = cv2.imdecode(np.frombuffer(b, np.uint8), cv2.IMREAD_COLOR)
    return im, q


def main():
    global LATA
    LATA = lata_wfs()
    L = json.load(open(os.path.join(OUT, "laty.json")))["laty"]
    os.makedirs(DANE, exist_ok=True)
    wynik, poch = {}, {"zrodlo_strony": "https://www.geoportal.gov.pl/dane/ortofotomapa → https://www.geoportal.gov.pl/pl/dane/ortofotomapa-orto/",
                       "data_pobrania": time.strftime("%F"), "pliki": {}}
    for nm, l in L.items():
        xN, yE = UK.wgs84_do_2180(l["lat"], l["lon"])
        ed = wfs_edycje(xN, yE)
        hr = [e for e in ed if e["piksel"] <= PIKSEL_MAX + 1e-9]
        grupy = {}
        for e in hr:
            grupy.setdefault((e["akt_data"], e["piksel"], e["nr_zglosz"]), []).append(e)
        edycje = []
        for (dt, pk, zg), es in sorted(grupy.items(), key=lambda k: (k[0][0] or "")):
            pelne = sorted([e for e in es if pokrywa(e["poligon_2180"], xN, yE, OKNO_M / 2)], key=lambda e: e["uklad"] != "PL-1992")
            edycje.append({"akt_data": dt, "piksel": pk, "nr_zglosz": zg, "kolor": es[0]["kolor"], "arkusze": [e["godlo"] for e in es],
                           "arkusz_pokrywa_okno": pelne[0]["godlo"] if pelne else None, "url": pelne[0]["url"] if pelne else None,
                           "wlk_mb": pelne[0]["wlk_mb"] if pelne else None, "uklad": (pelne or es)[0]["uklad"], "zrodlo": es[0]["zrodlo"]})
        uzyteczne = [e for e in edycje if e["url"] and e["kolor"] in ("RGB", None)]
        para = None
        if len(uzyteczne) >= 2:
            lat_ = sorted(uzyteczne, key=lambda e: e["akt_data"])
            para = {"swiat": lat_[0], "mapa": lat_[-1]}
        w = {"lat": l["lat"], "lon": l["lon"], "x_2180": round(xN, 3), "y_2180": round(yE, 3), "klasa_zamierzona": l["klasa"],
             "wszystkie_edycje": [{k: e[k] for k in ("rok", "godlo", "piksel", "kolor", "akt_data", "zrodlo")} for e in ed],
             "edycje_le_10cm": edycje, "lata_le_10cm": sorted({e["akt_data"][:4] for e in edycje if e["akt_data"]}),
             "para": {k: {kk: v[kk] for kk in ("akt_data", "piksel", "arkusz_pokrywa_okno", "nr_zglosz", "uklad")} for k, v in para.items()} if para else None}
        # pobranie okien pary
        if para:
            for rola, e in para.items():
                t = TiffZdalny(e["url"])
                X0, X1, Y0, Y1 = yE - OKNO_M / 2, yE + OKNO_M / 2, xN - OKNO_M / 2, xN + OKNO_M / 2
                im, geo = okno(t, e["uklad"], xN, yE, OKNO_M / 2, t.sx)
                if im is None:
                    raise SystemExit(f"{nm} {rola}: okno poza arkuszem {geo}")
                fn = f"{nm}_{rola}_{e['akt_data']}.png"
                cv2.imwrite(os.path.join(DANE, fn), im)
                sha = hashlib.sha256(open(os.path.join(DANE, fn), "rb").read()).hexdigest()
                poch["pliki"][fn] = {"lata": nm, "rola": rola, "usluga": WFS, "warstwa": f"gugik:SkorowidzOrtofomapy{e['akt_data'][:4]}",
                                     "arkusz": e["arkusz_pokrywa_okno"], "url_zrodla": e["url"], "edycja_nr_zglosz": e["nr_zglosz"],
                                     "data_nalotu": e["akt_data"], "uklad_arkusza": e["uklad"], "uklad_okna": "PL-1992 (EPSG:2180)", "piksel_m": geo["piksel"],
                                     "okno_2180": {"X_wsch": [X0, X1], "Y_poln": [Y0, Y1]}, "geo_okna": geo, "rozmiar_px": list(im.shape[:2]),
                                     "tiff": {"W": t.W, "H": t.H, "kafel": [t.tw, t.th], "kompresja": t.compr, "fotometria": t.photo,
                                              "piksel": [t.sx, t.sy], "tiepoint": t.tp}, "sha256": sha}
                w[f"okno_{rola}"] = fn
        wynik[nm] = w
        print(nm, "x,y", round(xN, 1), round(yE, 1), "edycje ≤10 cm:", [(e["akt_data"], e["piksel"], bool(e["url"])) for e in edycje],
              "para:", para and (para["swiat"]["akt_data"], para["mapa"]["akt_data"]), flush=True)
    json.dump(poch, open(os.path.join(DANE, "pochodzenie.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(wynik, open(os.path.join(OUT, "r1_dane.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
