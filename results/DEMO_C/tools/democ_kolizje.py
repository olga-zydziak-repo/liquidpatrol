#!/usr/bin/env python3
"""results/DEMO_C/tools/democ_kolizje.py — przyrząd kolizji napisów (PROMPT_DEMOC_V71 §3). NOWY plik.

Rejestrator instalowany w procesie kroku (democ_en_71.py) PO podmianie tłumaczącej: owija ImageDraw.text, ImageDraw.rectangle,
cv2.putText, cv2.rectangle, democ_overlay_v5.draw_brain i cv2.VideoWriter.write. Zdarzenia klatki w kolejności rysowania:
  - napis: prostokąt w układzie klatki 1920×1080 (PIL: textbbox; cv2: getTextSize, linia bazowa wliczona); cv2 na obrazie
    640×640 = panel mapy wklejany w (0, 56); cv2 na obrazie 480×640 = klatka nadir aktu 7 wklejana w (660, 690) w skali 0.625;
  - wypełnienie: PIL rectangle z fill (alfa ≥ 200), cv2.rectangle z grubością < 0, region draw_brain (przyciemnienie 85%).
Zamknięcie klatki (VideoWriter.write): cień (ten sam tekst przesunięty o (2, 2)) scalony z napisem; napis zasłonięty w całości
późniejszym wypełnieniem usunięty, zasłonięty częściowo = kolizja „zasłonięty”; przecięcia napis–napis (pole > 0) i wyjścia poza
panel (panel = najmniejszy z tabeli kroku, który zawiera lewy górny róg napisu; brak panelu = „poza panelami”).
Montaż dwuetapowy: env KOLIZJE_BAZA = rejestr etapu 1, jego napisy klatki k wchodzą na początek zdarzeń klatki k etapu 2.
Wyjście: env KOLIZJE_OUT (json: klatki z napisami i kolizjami).
"""
import json
import os

PANELE = {
    "std": {"top": (0, 0, 1920, 56), "map": (0, 56, 640, 640), "hud": (0, 696, 640, 324), "cam": (640, 56, 1280, 964),
            "caption": (0, 1020, 1920, 60)},
    "brain": {"brain": (1596, 736, 312, 236)},
    "nadir": {"nadir": (656, 664, 408, 356)},
    "akt5": {"top": (0, 0, 1920, 56), "steps": (0, 56, 1000, 206), "clip": (0, 262, 960, 540), "pca": (990, 60, 900, 420),
             "spark": (990, 514, 900, 134), "net": (1000, 660, 890, 230), "theorem": (0, 912, 1920, 48),
             "honesty": (0, 962, 1920, 56), "caption": (0, 1020, 1920, 60)},
    "aktB": {"top": (0, 0, 1920, 56), "map": (40, 60, 1000, 1000), "right": (1060, 56, 860, 964), "caption": (0, 1020, 1920, 60)},
    "karta": {"frame": (0, 0, 1920, 1080)},
}


def inter(a, b):
    w = min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0])
    h = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
    return w * h if w > 0 and h > 0 else 0


def inside(a, p):
    return a[0] >= p[0] and a[1] >= p[1] and a[0] + a[2] <= p[0] + p[2] and a[1] + a[3] <= p[1] + p[3]


class Rej:
    def __init__(self, panele, out, baza=None):
        self.panele = panele
        self.out = out
        self.baza = json.load(open(baza))["klatki"] if baza else None
        self.ev = []
        self.klatki = []

    def tekst(self, txt, rect, zr):
        if rect[2] > 0 and rect[3] > 0:
            self.ev.append(("t", txt, [int(round(v)) for v in rect], zr))

    def fill(self, rect):
        self.ev.append(("f", None, [int(round(v)) for v in rect], None))

    def panel_of(self, r):
        best = None
        for nm, p in self.panele.items():
            if p[0] <= r[0] + 1 < p[0] + p[2] and p[1] <= r[1] + 1 < p[1] + p[3]:
                if best is None or p[2] * p[3] < best[1][2] * best[1][3]:
                    best = (nm, p)
        return best

    def zamknij(self):
        k = len(self.klatki)
        ev = []
        if self.baza is not None:
            ev += [("t", t["tekst"], t["rect"], "etap1") for t in self.baza[k]["napisy"]]
        ev += self.ev
        self.ev = []
        # cień: ten sam tekst w (x+2, y+2) tuż przed napisem
        teksty = []
        for i, e in enumerate(ev):
            if e[0] != "t":
                continue
            t = {"tekst": e[1], "rect": list(e[2]), "zr": e[3], "i": i}
            if teksty and teksty[-1]["tekst"] == t["tekst"] and teksty[-1]["rect"][0] == t["rect"][0] + 2 \
                    and teksty[-1]["rect"][1] == t["rect"][1] + 2 and teksty[-1]["i"] == i - 1:
                s = teksty.pop()
                x0, y0 = min(s["rect"][0], t["rect"][0]), min(s["rect"][1], t["rect"][1])
                x1 = max(s["rect"][0] + s["rect"][2], t["rect"][0] + t["rect"][2])
                y1 = max(s["rect"][1] + s["rect"][3], t["rect"][1] + t["rect"][3])
                t["rect"] = [x0, y0, x1 - x0, y1 - y0]
            teksty.append(t)
        kol, zywe = [], []
        for t in teksty:
            pozniej = [e[2] for e in ev[t["i"] + 1:] if e[0] == "f"]
            cover = [f for f in pozniej if inter(f, t["rect"]) > 0]
            if any(inside(t["rect"], f) for f in cover):
                continue
            if cover:
                kol.append({"typ": "zasłonięty", "a": t["tekst"], "rect_a": t["rect"]})
            zywe.append(t)
        for i in range(len(zywe)):
            for j in range(i + 1, len(zywe)):
                a, b = zywe[i], zywe[j]
                if inter(a["rect"], b["rect"]) > 0:
                    kol.append({"typ": "napis-napis", "a": a["tekst"], "b": b["tekst"], "rect_a": a["rect"], "rect_b": b["rect"]})
        for t in zywe:
            p = self.panel_of(t["rect"])
            t["panel"] = p[0] if p else None
            if p is None:
                kol.append({"typ": "poza panelami", "a": t["tekst"], "rect_a": t["rect"]})
            elif not inside(t["rect"], p[1]):
                kol.append({"typ": "poza panelem", "a": t["tekst"], "panel": p[0], "rect_a": t["rect"]})
        self.klatki.append({"napisy": [{"tekst": t["tekst"], "rect": t["rect"], "panel": t["panel"]} for t in zywe], "kolizje": kol})

    def zapisz(self):
        json.dump({"panele": self.panele, "klatki": self.klatki}, open(self.out, "w"), ensure_ascii=False)


def install(tr, panele_nazwy):
    """tr: funkcja tłumacząca (democ_en.tr) — prostokąt liczony dla tekstu po tłumaczeniu (tak, jak rysowany)."""
    import cv2
    from PIL import ImageDraw
    panele = {}
    for nm in panele_nazwy:
        panele.update(PANELE[nm])
    rej = Rej(panele, os.environ["KOLIZJE_OUT"], os.environ.get("KOLIZJE_BAZA") or None)
    _text, _rect = ImageDraw.ImageDraw.text, ImageDraw.ImageDraw.rectangle

    def text(self, xy, txt, *a, **k):
        if self.im.size == (1920, 1080) and isinstance(txt, str):
            font = k.get("font") or (a[1] if len(a) > 1 else None)
            bb = self.textbbox(xy, tr(txt), font=font)
            rej.tekst(tr(txt), (bb[0], bb[1], bb[2] - bb[0], bb[3] - bb[1]), "pil")
        return _text(self, xy, txt, *a, **k)

    def rectangle(self, xy, fill=None, *a, **k):
        if self.im.size == (1920, 1080) and fill is not None:
            al = fill[3] if isinstance(fill, tuple) and len(fill) == 4 else 255
            if al >= 200:
                if len(xy) == 4:
                    x0, y0, x1, y1 = xy
                else:
                    (x0, y0), (x1, y1) = xy
                rej.fill((x0, y0, x1 - x0, y1 - y0))
        return _rect(self, xy, fill, *a, **k)
    ImageDraw.ImageDraw.text, ImageDraw.ImageDraw.rectangle = text, rectangle

    _pt, _cr = cv2.putText, cv2.rectangle

    def place(img, r):
        h, w = img.shape[:2]
        if (h, w) == (1080, 1920):
            return r
        if (h, w) == (640, 640):
            return (r[0], r[1] + 56, r[2], r[3])
        if (h, w) == (480, 640):
            s = 0.625
            return (660 + r[0] * s, 690 + r[1] * s, r[2] * s, r[3] * s)
        return None

    def put_text(img, text, org, fontFace, fontScale, color, thickness=1, *a, **k):
        (w, h), base = cv2.getTextSize(tr(text), fontFace, fontScale, thickness)
        r = place(img, (org[0], org[1] - h, w, h + base))
        if r is not None:
            rej.tekst(tr(text), r, "cv2")
        return _pt(img, text, org, fontFace, fontScale, color, thickness, *a, **k)

    def rect_cv(img, p1, p2, color, thickness=1, *a, **k):
        if thickness is not None and thickness < 0:
            r = place(img, (min(p1[0], p2[0]), min(p1[1], p2[1]), abs(p2[0] - p1[0]), abs(p2[1] - p1[1])))
            if r is not None:
                rej.fill(r)
        return _cr(img, p1, p2, color, thickness, *a, **k)
    cv2.putText, cv2.rectangle = put_text, rect_cv

    import importlib
    mods = []
    for nm in ("democ_overlay_v5", "democ_overlay_v5_71"):
        try:
            mods.append(importlib.import_module(nm))
        except ImportError:
            pass
    for M in mods:
        _db = M.draw_brain

        def draw_brain(canvas, region, *a, _db=_db, **k):
            if canvas.shape[:2] == (1080, 1920):
                rej.fill(region)
            return _db(canvas, region, *a, **k)
        M.draw_brain = draw_brain

    _VW = cv2.VideoWriter

    class VW:
        def __init__(self, *a, **k):
            self.v = _VW(*a, **k)

        def write(self, fr):
            rej.zamknij()
            return self.v.write(fr)

        def release(self):
            rej.zapisz()
            return self.v.release()

        def isOpened(self):
            return self.v.isOpened()
    cv2.VideoWriter = VW
    return rej
