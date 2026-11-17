#!/usr/bin/env python3
"""results/TEACH2_RECON/tools/t2r_dane.py — wspólne dla reconu TEACH-II (PROMPT_TEACH2_S0; 0 bootów).

Klatki lotu z zapisu (wiersze nf z nadir_obs.jsonl: chwila klatki, migawka EKF q FRD→NED i pozycja NED, flaga GNSS jako stan przy
klatce), poza GT z trace.jsonl (orto_r2.GT, interpolacja do chwili klatki) — WYŁĄCZNIE do renderu kadru i oceny. Render kadru jak
w W2 z S1 (teach_w2.zadanie.render: orto_r2.Kam.poza + renderuj z łaty 2024-04-27, piksel teach_r34.PIKSEL_T). Moduł lotu
harness/teach_map.Producent w wariancie z results/TEACH/s1/tor.json, bez żadnej zmiany.
Chwile lotu: start epizodu (zdarzenie episode_start), koniec misji jak sędzia lotu (S3: sedzia_s3.json okno_misji; cień S2:
cien_s2.json koniec_misji), flaga z ULG (sedzia_s3.json os_czasu.flaga_ulg).
"""
import copy
import json
import os
import sys

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/NAD3_RECON/tools")]
from harness import teach_map as TM                      # noqa: E402
import nad3_dane as N3                                   # noqa: E402

T, R2 = TM.T, TM.R2
TEACH = os.path.join(ROOT, "results/TEACH")
DANE = os.path.join(ROOT, "results/TEACH_RECON/dane")
OUT = os.path.join(ROOT, "results/TEACH2_RECON")
WARIANT = json.load(open(os.path.join(TEACH, "s1/tor.json")))["tor"]["wariant_K"]


def katalog(nazwa):
    for s in ("s3", "s2"):
        d = os.path.join(TEACH, s, nazwa)
        if os.path.isdir(d):
            return d
    raise FileNotFoundError(nazwa)


def lot(nazwa):
    """Klatki i chwile lotu TEACH (S2 / S3)."""
    d = katalog(nazwa)
    ev = N3.jl(d, "trace.jsonl", "event")
    st = [e for e in ev if e.get("ev") == "episode_start"]
    assert len(st) == 1, (nazwa, len(st))
    t_ep = st[0]["sim"]
    flaga = None
    sp = os.path.join(d, "sedzia_s3.json")
    if os.path.exists(sp):
        s = json.load(open(sp))
        koniec = s["epizody"][0]["okno_misji"][1]
        flaga = (s["zrodlo"].get("os_czasu") or {}).get("flaga_ulg")
        zr = s["zrodlo"]
    else:
        c = json.load(open(os.path.join(d, "cien_s2.json")))
        koniec, zr = c["koniec_misji"], None
    g = R2.GT(d)
    kl = []
    for r in N3.jl(d, "nadir_obs.jsonl", "nf"):
        p, q, dtg = g(r["sim"])
        kl.append({"sim": r["sim"], "ekf_q": r.get("ekf_q"), "ekf_pos": r.get("ekf_pos"), "gnss": r.get("gnss"),
                   "gt_p": p, "gt_q": q, "gt_dt": dtg})
    return {"nazwa": nazwa, "d": d, "t_ep": t_ep, "koniec": koniec, "flaga": flaga, "klatki": kl, "zrodlo": zr,
            "scen": st[0].get("scenario_id")}


class Render:
    def __init__(self, lata):
        import cv2
        self.kam = R2.Kam(R2.kamera())
        self.teren = cv2.imread(os.path.join(DANE, f"{lata}_2024-04-27.png"))
        assert self.teren is not None, lata

    def __call__(self, k):
        C, Rk = self.kam.poza(np.asarray(k["gt_p"]), R2.rotm(k["gt_q"]))
        fr, _ = self.kam.renderuj(self.teren, T.PIKSEL_T, C, Rk)
        return fr


def klon(P):
    """Kopia stanu producenta (bez obiektów cv2: Dop, Prost, Kam — te z nowego obiektu)."""
    Q = TM.Producent(wariant=P.wariant, maska=P.maska)
    for k, v in vars(P).items():
        if k in ("D", "pr", "kam"):
            continue
        setattr(Q, k, copy.deepcopy(v))
    return Q


def rozklad(x, nd=4):
    x = [v for v in x if v is not None]
    if not x:
        return None
    return {"n": len(x), "p50": round(float(np.median(x)), nd), "p95": round(float(np.quantile(x, .95)), nd),
            "max": round(float(max(x)), nd)}


def przerwy(t0, t_ok, t1):
    ts = [t0] + sorted(t for t in t_ok if t0 <= t <= t1) + [t1]
    g = np.diff(ts)
    duze = [(round(a, 3), round(b - a, 3)) for a, b in zip(ts[:-1], ts[1:]) if b - a > 1.15]
    return {"max": round(float(g.max()), 3) if len(g) else None, "gt_115": int((g > 1.15).sum()), "lista_gt_115": duze}
