#!/usr/bin/env python3
"""results/TEACH_RECON2/tools/teach2.py — PROMPT_TEACH_S0B R1–R5, R7: mapa spięta obrazem i zakotwiczona w torze EKF (0 bootów).

Bez zmian z TEACH-S0 (results/TEACH_RECON/tools/teach_r34.py): import Dop, pokrycie, rz, zawin, kurs i stałych; kopia bez zmiany treści
(przeniesiona z ciała teach_r34.zadanie do funkcji): przygotuj(k) bez pól M0 (fr, Rg, z_gt — tu nieużywane), wybór klatek kluczowych
(próg pokrycia 70 %, siatka 0.5 m, ślad 16 × 12 promieni przy pozie EKF), łańcuch po cięciu (kandydaci: do 3 klatek kluczowych
o największym przewidywanym pokryciu > 0; poprawka z klatki o największej liczbie zgodnych; reguła a12_geo0_g1.5). Teren, kadry
(results/TEACH_RECON/r2_klatki.json.gz) i prostowanie przy postawie i wysokości EKF bez zmian.
Nowe (prompt R2/R3):
  R2 wiązania: kadr j serii „przed” ↔ do 3 klatek kluczowych o największym pokryciu przewidywanym z pozycji EKF (pokrycie(cam_ekf(j),
     cam_ekf(k), a_j) jak w S0), pokrycie ≥ 30 %; klatki kluczowe = wszystkie wybrane do chwili cięcia; kadr będący klatką kluczową
     wiąże się z sobą samym r = 0 bez dopasowania (jedno z trzech). Przyjęte: zgodnych ≥ 12 ∧ | |r_kj| − |cam_ekf(j) − cam_ekf(k)| | ≤ 1.5 m.
  R3 georeferencja: P_k(r) = Rz(θ_k)·r + t_k, skala 1. (A) P_k(r_kj) = cam_ekf(j) waga 1; (B) P_k(r_kj) = P_l(r_lj) dla par wiązań
     tego samego kadru, waga 5; prior θ_k = 0, t_k = cam_ekf(k), waga 0.05. Gauss–Newton od priora, 6 iteracji, kwadratowa strata.
     M1: θ = 0, t = cam_ekf (kontrola R1); M3: (A) + prior; M4: (A) + (B) + prior. Osobno na rodzaj cech (wiązania z tego rodzaju).
  R4: łańcuch S0 na wariant; punkt pod kamerą = P_k(r), pojazd = punkt − (R_EKF·t)_EN.
  Zapis: wiazania/<lot>_<łata>.json.gz, czesci/<lot>_<łata>.json.gz (pola w pliku). Pokrycia „prawdziwe” jak S0 (poza GT, kwadraty a).
Użycie: teach2.py [n_proc ≤ 8]
"""
import gzip
import json
import math
import os
import sys
import time
from multiprocessing import Pool

import cv2
import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, os.path.join(ROOT, "results/TEACH_RECON/tools"))
import teach_r34 as T

R2, R3, NF = T.R2, T.R3, T.NF
Dop, pokrycie, rz, zawin, kurs = T.Dop, T.pokrycie, T.rz, T.zawin, T.kurs
OUT = os.path.join(ROOT, "results/TEACH_RECON2")
SRC = T.OUT
RODZAJE = T.RODZAJE
WARIANTY = ("M1", "M3", "M4")
POKR_WIAZ, TOL_ODL = 0.30, 1.5
W_A, W_B, W_P = 1.0, 5.0, 0.05
ITER = 6


class Lot:
    """Kadry jednego (lot, łata), kamera, prostowanie, teren — wspólne dla wiązań, rozwiązania i łańcucha."""

    def __init__(self, lot, lata):
        self.lot, self.lata = lot, lata
        self.kam = R2.Kam(R2.kamera())
        self.pr = R3.Prost(self.kam)
        self.teren = cv2.imread(os.path.join(SRC, "dane", f"{lata}_2024-04-27.png"))
        K = [k for k in json.load(gzip.open(os.path.join(SRC, "r2_klatki.json.gz"), "rt")) if k["lot"] == lot]
        self.przed = sorted([k for k in K if k["seria"] == "przed"], key=lambda k: k["sim"])
        self.po = sorted([k for k in K if k["seria"] == "po"], key=lambda k: k["sim"])
        self.D = {rd: Dop(rd) for rd in RODZAJE}

    def przygotuj(self, k):
        kam, pr = self.kam, self.pr
        Rg = R2.rotm(k["gt_q"]); Re = NF.ekf_R(k["ekf_q"])
        C, Rk = kam.poza(np.array(k["gt_p"]), Rg)
        fr, fpoza = kam.renderuj(self.teren, T.PIKSEL_T, C, Rk)
        rect, mask, off = pr(fr, k["ekf_q"], k["ekf_pos"])
        ekf_en = np.array([k["ekf_pos"][1], k["ekf_pos"][0]])
        Ce = Re @ kam.t_link
        hc_e = -k["ekf_pos"][2] + Ce[2]
        return {"sim": k["sim"], "rect": rect, "mask": mask, "off": np.asarray(off), "ekf_en": ekf_en, "gt_en": np.array(k["gt_p"][:2]),
                "cam_gt": C[:2], "cam_ekf": ekf_en + np.asarray(off), "h_gt": C[2], "h_ekf": hc_e, "e": zawin(kurs(Rg) - kurs(Re)),
                "Re": Re, "poza": fpoza, "a": hc_e * (kam.H / 2) / kam.F}

    def klatki_kluczowe(self):
        kam = self.kam
        su = np.arange(16) * (kam.W - 1) / 15; sv = np.arange(12) * (kam.H - 1) / 11
        pokryte = set()
        kf, idx = [], []
        for n, k in enumerate(self.przed):
            Re = NF.ekf_R(k["ekf_q"])
            Ce, Rke = kam.poza(np.array([k["ekf_pos"][1], k["ekf_pos"][0], -k["ekf_pos"][2]]), Re)
            E, Nn = kam.grunt(Ce, Rke)
            Es, Ns = E[np.ix_(sv.astype(int), su.astype(int))], Nn[np.ix_(sv.astype(int), su.astype(int))]
            ok = np.isfinite(Es)
            if not ok.any():
                continue
            x0, x1, y0, y1 = Es[ok].min(), Es[ok].max(), Ns[ok].min(), Ns[ok].max()
            poly = np.stack([Es[ok], Ns[ok]], 1).astype(np.float32)
            hull = cv2.convexHull(poly)
            xs = np.arange(math.floor(x0 / T.SIATKA_KF), math.ceil(x1 / T.SIATKA_KF) + 1)
            ys = np.arange(math.floor(y0 / T.SIATKA_KF), math.ceil(y1 / T.SIATKA_KF) + 1)
            komorki = {(int(i), int(j)) for i in xs for j in ys
                       if cv2.pointPolygonTest(hull, (float(i * T.SIATKA_KF), float(j * T.SIATKA_KF)), False) >= 0}
            if not komorki:
                continue
            frac = len(komorki & pokryte) / len(komorki)
            if frac < T.PROG_KF:
                kf.append(self.przygotuj(k)); idx.append(n)
                pokryte |= komorki
        for x in kf:
            for rd in RODZAJE:
                x[rd] = self.D[rd].cechy(x["rect"], x["mask"])
        self.kf, self.kf_idx = kf, idx
        return kf


def wiazania(L, czasy=None):
    """R2: lista na rodzaj [sim_j, k, r_E, r_N, zgodne, przyjęte] + dane kadru (cam_ekf j) do rozwiązania."""
    kf = L.kf
    out = {rd: [] for rd in RODZAJE}
    for n, k in enumerate(L.przed):
        t0 = time.perf_counter()
        sam = L.kf_idx.index(n) if n in L.kf_idx else None
        x = kf[sam] if sam is not None else L.przygotuj(k)
        kand = sorted(((pokrycie(x["cam_ekf"], y["cam_ekf"], x["a"]), i) for i, y in enumerate(kf)), reverse=True)
        kand = [i for p, i in kand[:T.N_KAND] if p >= POKR_WIAZ]
        if sam is not None and sam not in kand:                    # sam ze sobą ma pokrycie 1 — zawsze wśród trzech
            kand = [sam] + kand[:T.N_KAND - 1]
        for rd in RODZAJE:
            fx = x[rd] if sam is not None else L.D[rd].cechy(x["rect"], x["mask"])
            for i in kand:
                if i == sam:
                    out[rd].append([round(k["sim"], 3), i, 0.0, 0.0, None, 1, x["cam_ekf"].tolist()])
                    continue
                w = L.D[rd].dopasuj(fx, kf[i][rd])
                if w is None:
                    out[rd].append([round(k["sim"], 3), i, None, None, 0, 0, x["cam_ekf"].tolist()])
                    continue
                d_ekf = float(np.linalg.norm(x["cam_ekf"] - kf[i]["cam_ekf"]))
                ok = w[0] >= T.A_MIN and abs(math.hypot(*w[1]) - d_ekf) <= TOL_ODL
                out[rd].append([round(k["sim"], 3), i, round(w[1][0], 4), round(w[1][1], 4), w[0], int(ok), x["cam_ekf"].tolist()])
        if czasy is not None:
            czasy.append((time.perf_counter() - t0) * 1e3)
    return out


def rozwiaz(kf, wz, wariant):
    """R3: θ_k, t_k (K × 3) dla M1 / M3 / M4 z przyjętych wiązań jednego rodzaju cech."""
    K = len(kf)
    x = np.zeros(3 * K)
    for k in range(K):
        x[3 * k + 1:3 * k + 3] = kf[k]["cam_ekf"]
    if wariant == "M1":
        return x.reshape(K, 3)
    przyj = [w for w in wz if w[5]]
    A = [(w[1], np.array([w[2], w[3]]), np.array(w[6])) for w in przyj]
    B = []
    if wariant == "M4":
        po_kadrze = {}
        for w in przyj:
            po_kadrze.setdefault(w[0], []).append((w[1], np.array([w[2], w[3]])))
        for lst in po_kadrze.values():
            for a in range(len(lst)):
                for b in range(a + 1, len(lst)):
                    B.append((lst[a], lst[b]))
    x0 = x.copy()
    for _ in range(ITER):
        rows, res = [], []

        def P(k, r):
            th = x[3 * k]
            c, s = math.cos(th), math.sin(th)
            p = np.array([c * r[0] - s * r[1], s * r[0] + c * r[1]]) + x[3 * k + 1:3 * k + 3]
            dth = np.array([-s * r[0] - c * r[1], c * r[0] - s * r[1]])
            return p, dth

        for k, r, cj in A:
            p, dth = P(k, r)
            for d in range(2):
                J = np.zeros(3 * K); J[3 * k] = dth[d]; J[3 * k + 1 + d] = 1.0
                rows.append(W_A * J); res.append(W_A * (p[d] - cj[d]))
        for (k, rk), (l, rl) in B:
            pk, dk = P(k, rk); pl, dl = P(l, rl)
            for d in range(2):
                J = np.zeros(3 * K)
                J[3 * k] += dk[d]; J[3 * k + 1 + d] += 1.0
                J[3 * l] -= dl[d]; J[3 * l + 1 + d] -= 1.0
                rows.append(W_B * J); res.append(W_B * (pk[d] - pl[d]))
        for i in range(3 * K):
            J = np.zeros(3 * K); J[i] = 1.0
            rows.append(W_P * J); res.append(W_P * (x[i] - x0[i]))
        Jm, rv = np.array(rows), np.array(res)
        dx = np.linalg.lstsq(Jm, -rv, rcond=None)[0]
        x = x + dx
    return x.reshape(K, 3)


def lancuch(L, geo):
    """R4 jak S0 (bufor dopasowań wspólny dla wariantów); geo[(war, rd)] = K × 3 (θ, t_E, t_N)."""
    kf, po = L.kf, L.po
    bufor = {}
    t_cut = po[0]["sim"] - po[0]["od_ciecia"] if po else None
    st = {(w, rd): {"d": np.zeros(2), "t_fix": t_cut, "kl": []} for w in WARIANTY for rd in RODZAJE}
    for fi, k in enumerate(po):
        x = L.przygotuj(k)
        fx = {rd: L.D[rd].cechy(x["rect"], x["mask"]) for rd in RODZAJE}
        pk_max = max((pokrycie(x["cam_gt"], y["cam_gt"], x["a"]) for y in kf), default=0.0)
        for rd in RODZAJE:
            for war in WARIANTY:
                G = geo[(war, rd)]
                s = st[(war, rd)]
                pred = x["ekf_en"] + s["d"]
                tau = k["sim"] - s["t_fix"]
                pc = pred + x["off"]
                kand = sorted(((pokrycie(pc, G[i, 1:], x["a"]), i) for i, y in enumerate(kf)), reverse=True)
                kand = [i for p, i in kand[:T.N_KAND] if p > 0]
                best = None
                for i in kand:
                    if (fi, i, rd) not in bufor:
                        bufor[(fi, i, rd)] = L.D[rd].dopasuj(fx[rd], kf[i][rd])
                    w = bufor[(fi, i, rd)]
                    if w is not None and (best is None or w[0] > best[1][0]):
                        best = (i, w)
                rec = [round(k["sim"], 3), round(tau, 3), None, None, None, None, None, None, None, 0, None, None, round(pk_max, 3)]
                if best is not None:
                    i, w = best
                    cam = rz(G[i, 0]) @ np.array(w[1]) + G[i, 1:]
                    fix = cam - x["off"]
                    err = float(np.linalg.norm(fix - x["gt_en"]))
                    innow = float(np.linalg.norm(fix - pred))
                    ok = w[0] >= T.A_MIN and innow <= T.G0 + R3.VR * tau
                    rec = [round(k["sim"], 3), round(tau, 3), i, round(w[1][0], 4), round(w[1][1], 4), w[0], round(float(fix[0]), 4),
                           round(float(fix[1]), 4), round(err, 4), int(ok), round(innow, 4),
                           round(pokrycie(x["cam_gt"], kf[i]["cam_gt"], x["a"]), 3), round(pk_max, 3)]
                    if ok:
                        s["d"] = fix - x["ekf_en"]
                        s["t_fix"] = k["sim"]
                s["kl"].append(rec)
    return st, t_cut, len(bufor)


def zadanie(arg):
    lot, lata = arg
    cv2.setNumThreads(1)
    t0 = time.time()
    L = Lot(lot, lata)
    kf = L.klatki_kluczowe()
    wz = wiazania(L)
    geo, t_rozw = {}, {}
    for rd in RODZAJE:
        for war in WARIANTY:
            a = time.perf_counter()
            geo[(war, rd)] = rozwiaz(kf, wz[rd], war)
            t_rozw[f"{war}/{rd}"] = round((time.perf_counter() - a) * 1e3, 2)
    st, t_cut, n_dop = lancuch(L, geo)
    wyn = {"lot": lot, "lata": lata, "n_przed": len(L.przed), "n_po": len(L.po), "n_kf": len(kf), "t_ciecia": t_cut,
           "t_konca": L.po[-1]["sim"] if L.po else None,
           "kf": [{"sim": round(x["sim"], 3), "cam_ekf": [round(float(v), 4) for v in x["cam_ekf"]],
                   "cam_gt": [round(float(v), 4) for v in x["cam_gt"]], "e_deg": round(math.degrees(x["e"]), 4),
                   "h_ekf": round(float(x["h_ekf"]), 3), "h_gt": round(float(x["h_gt"]), 3),
                   "n_wiazan": {rd: sum(1 for w in wz[rd] if w[1] == i and w[5]) for rd in RODZAJE},
                   "geo": {f"{war}/{rd}": {"theta_deg": round(math.degrees(geo[(war, rd)][i, 0]), 4),
                                           "t": [round(float(v), 4) for v in geo[(war, rd)][i, 1:]],
                                           "theta_minus_e_deg": round(math.degrees(zawin(geo[(war, rd)][i, 0] - x["e"])), 4),
                                           "t_minus_cam_gt_m": round(float(np.linalg.norm(geo[(war, rd)][i, 1:] - x["cam_gt"])), 4)}
                           for war in WARIANTY for rd in RODZAJE}} for i, x in enumerate(kf)],
           "klatki": {f"{w}/{rd}": st[(w, rd)]["kl"] for w in WARIANTY for rd in RODZAJE},
           "pola_klatki": ["sim", "tau", "k", "r_E", "r_N", "zgodne", "poprawka_E", "poprawka_N", "blad", "przyjeta", "innowacja",
                           "pokrycie_z_k", "pokrycie_najwieksze"],
           "t_rozwiazania_ms": t_rozw, "n_dopasowan_po": n_dop, "zegar_s": round(time.time() - t0, 1)}
    wzap = {"lot": lot, "lata": lata, "pola": ["sim_j", "k", "r_E", "r_N", "zgodne", "przyjete"],
            "wiazania": {rd: [w[:6] for w in wz[rd]] for rd in RODZAJE}}
    return wyn, wzap


def main():
    npr = min(int(sys.argv[1]) if len(sys.argv) > 1 else 8, 8)
    for d in ("czesci", "wiazania"):
        os.makedirs(os.path.join(OUT, d), exist_ok=True)
    loty = sorted({k["lot"] for k in json.load(gzip.open(os.path.join(SRC, "r2_klatki.json.gz"), "rt"))})
    zad = [(l, a) for a in T.LATY for l in loty]
    zad.sort(key=lambda z: z[0] != "L_c10_s01")
    nazwa = lambda d, z: os.path.join(OUT, d, f"{z[0]}_{z[1]}.json.gz")
    zad = [z for z in zad if not os.path.exists(nazwa("czesci", z))]
    t0 = time.time()
    print(time.strftime("%T"), "do zrobienia", len(zad), "procesy", npr, flush=True)
    with Pool(npr) as p:
        for w, wz in p.imap_unordered(zadanie, zad):
            z = (w["lot"], w["lata"])
            for d, obj in (("wiazania", wz), ("czesci", w)):
                with gzip.open(nazwa(d, z) + ".tmp", "wt") as f:
                    json.dump(obj, f)
                os.replace(nazwa(d, z) + ".tmp", nazwa(d, z))
            sk = {kk: (sum(r[9] for r in v), max((r[8] for r in v if r[9]), default=None)) for kk, v in w["klatki"].items()}
            print(time.strftime("%T"), f"{time.time() - t0:.0f}s", w["lot"], w["lata"], "kf", w["n_kf"], sk, flush=True)


if __name__ == "__main__":
    main()
