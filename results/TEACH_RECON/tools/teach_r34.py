#!/usr/bin/env python3
"""results/TEACH_RECON/tools/teach_r34.py — PROMPT_TEACH_S0 R3 (mapa z klatek sprzed cięcia) i R4 (lokalizacja po cięciu), 0 bootów.

Klatki renderowane z terenu 2024-04-27 (results/TEACH_RECON/dane, piksel 0.05 m) przy pozie GT (orto_r2.Kam.renderuj) i prostowane
przy postawie i wysokości EKF z migawki klatki (orto_r3.Prost: siatka 0.1 m/px, ±15 m, N do góry, środek = punkt pod kamerą).
Prostowanie z EKF w każdej klatce bieżącej i w klatkach kluczowych M1/M2 — dla nich dopasowanie nie zależy od wariantu i jest buforowane;
M1 i M2 różnią się wyłącznie georeferencją. M0 ma własne prostowanie klatek kluczowych (poza GT) i własny bufor.

R3 — klatki kluczowe z serii „przed” (decyzja po stronie drona, poza EKF): klatka staje się kluczową, gdy pokrycie jej śladu na gruncie
(siatka 0.5 m, ślad z 16 × 12 promieni przy pozie EKF) przez sumę śladów dotychczasowych kluczowych spada poniżej 70 %.
Georeferencja klatki kluczowej (punkt pod kamerą c, obrót e, skala s):
  M0 idealna — klatka kluczowa wyprostowana przy pozie GT (prost_R), c = kamera GT, e = 0, s = 1 (kontrola przyrządu; naprawa 1:
               pierwsza wersja prostowała klatki kluczowe M0 przy postawie EKF i korygowała tylko kurs i skalę — r4_przed_naprawa/);
  M1 surowa  — c = pozycja EKF + (R_EKF·t)_EN, e = 0, s = 1;
  M2         — jak M1, e = ψ_kal: jedna poprawka kursu na lot (osobno na rodzaj cech), wyłącznie z fazy przed cięciem: pary klatek
               kluczowych (odległość EKF ≥ 3 m, przewidywane pokrycie ≥ 30 %), dopasowanie j → i daje przesunięcie obrazu r (w ramie
               prostowania i), EKF daje d; e_ij = kąt(d) − kąt(r); ψ_kal = średnia kołowa ważona |d| po parach z ≥ 12 inlierami.
  Prostowanie przy kursie EKF obraca obraz o −e (e = błąd kursu), więc przesunięcie prawdziwe = s·Rz(e)·r.
R4 — łańcuch jak recon ORTO (rama B+ NAD3): przy cięciu Δ = 0; pred = EKF + Δ; τ = t − t_fix. Kandydaci: do trzech klatek kluczowych
o największym przewidywanym pokryciu (dwa kwadraty o pół-boku a = h_EKF·(H/2)/F wokół pred kamery i c klatki), pokrycie > 0.
Dopasowanie: cechy (orto_r3.Cechy: SIFT / AKAZE po CLAHE, maska prostowania) kadru i klatki, knn 2 + iloraz 0.8, estimateAffinePartial2D
RANSAC 3 px (ziarno stałe); poprawka z klatki o największej liczbie inlierów: punkt pod kamerą = c + s·Rz(e)·r, pojazd = punkt
− (R_EKF·t)_EN. Reguła przyjęcia zamrożona `a12_geo0_g1.5` (results/ORTO_RECON/r5_reguly.json): n_inl ≥ 12 ∧ |poprawka − pred| ≤ 1.5 + 3τ.
Ocena (tylko tu GT): błąd = |poprawka − GT pojazdu (x, y)|; odległość |r| od środka klatki kluczowej; pokrycie prawdziwe (poza GT
kadru i klatki kluczowej, te same kwadraty).
Zapis cząstkowy po każdym (lot, łata): results/TEACH_RECON/r4_czesci/<lot>_<łata>.json.gz; istniejące pomijane (wznowienie).
Budżet: procesy ≤ 8, cv2 jednowątkowo (procesy × wątki ≤ 8). Użycie: teach_r34.py [n_proc]
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
sys.path.insert(0, os.path.join(ROOT, "results/ORTO_RECON/tools"))
import orto_r2 as R2
import orto_r3 as R3

NF = R3.NF
OUT = os.path.join(ROOT, "results/TEACH_RECON")
CZ = os.path.join(OUT, "r4_czesci")
LATY = ("S", "M", "J")
RODZAJE = ("K1_SIFT", "K2_AKAZE")
WARIANTY = ("M0", "M1", "M2")
PIKSEL_T = 0.05
PROG_KF = 0.70
SIATKA_KF = 0.5
N_KAND = 3
A_MIN, G0 = 12, 1.5                     # a12_geo0_g1.5
KAL_D_MIN, KAL_POKR_MIN = 3.0, 0.30


def kurs(R):
    return math.atan2(R[1, 0], R[0, 0])


def zawin(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def rz(e):
    c, s = math.cos(e), math.sin(e)
    return np.array([[c, -s], [s, c]])


def pokrycie(p, q, a):
    return max(0.0, 1 - abs(p[0] - q[0]) / (2 * a)) * max(0.0, 1 - abs(p[1] - q[1]) / (2 * a))


class Dop:
    """Cechy wyprostowanego kadru + dopasowanie podobieństwa kadr j → kadr i (bez okna; obrazy małe)."""

    def __init__(self, rodzaj):
        self.c = R3.Cechy(rodzaj, np.zeros((64, 64, 3), np.uint8))          # detektor i norma z orto_r3; mapa nieużywana
        self.bf = cv2.BFMatcher(self.c.norm)
        self.n = int(round(2 * R3.S_PROST / R3.RHO))

    def cechy(self, rect, mask):
        m = cv2.erode(mask, np.ones((9, 9), np.uint8))                 # jak orto_r3.Cechy.klatka: bez cech na krawędzi maski
        kp, ds = self.c.det_k.detectAndCompute(R3.clahe(rect), m)
        return (np.float32([k.pt for k in kp]) if kp else np.zeros((0, 2), np.float32)), ds

    def dopasuj(self, fj, fi):
        """Zwraca (n_inl, r_EN [m] = środek kadru j w ramie prostowania i względem środka i, kąt [°], skala) albo None."""
        (pj, dj), (pi, di) = fj, fi
        if dj is None or di is None or len(pj) < 3 or len(pi) < 3:
            return None
        mm = self.bf.knnMatch(dj, di, k=2)
        dobre = [m[0] for m in mm if len(m) == 2 and m[0].distance < R3.RATIO * m[1].distance]
        if len(dobre) < 3:
            return None
        A = pj[[m.queryIdx for m in dobre]]; B = pi[[m.trainIdx for m in dobre]]
        cv2.setRNGSeed(12345)
        M, inl = cv2.estimateAffinePartial2D(A, B, method=cv2.RANSAC, ransacReprojThreshold=R3.RANSAC_PX)
        if M is None:
            return None
        c = self.n / 2 - 0.5
        x, y = M @ np.array([c, c, 1.0])
        return (int(inl.sum()), ((x - c) * R3.RHO, -(y - c) * R3.RHO), math.degrees(math.atan2(M[1, 0], M[0, 0])),
                float(math.hypot(M[0, 0], M[1, 0])))


def prost_R(pr, kam, klatka, Rb, z_model):
    """orto_r3.Prost przy danej macierzy FLU→ENU i wysokości ramy modelu (poza GT) — tylko georeferencja M0."""
    off = Rb @ kam.t_link
    hc = z_model + off[2]
    Rk = Rb @ kam.R_cz
    P = np.stack([pr.dE.ravel(), pr.dN.ravel(), np.full(pr.dE.size, -hc)], 1)
    uv, d = kam.rzut(np.zeros(3), Rk, P)
    mx = uv[:, 0].reshape(pr.n, pr.n).astype(np.float32)
    my = uv[:, 1].reshape(pr.n, pr.n).astype(np.float32)
    ok = (d.reshape(pr.n, pr.n) > 0) & (mx >= 0) & (my >= 0) & (mx <= kam.W - 1) & (my <= kam.H - 1)
    mx[~ok] = -10; my[~ok] = -10
    return cv2.remap(klatka, mx, my, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT), ok.astype(np.uint8) * 255


def zadanie(arg):
    lot, lata = arg
    cv2.setNumThreads(1)
    t_start = time.time()
    kam = R2.Kam(R2.kamera())
    pr = R3.Prost(kam)
    teren = cv2.imread(os.path.join(OUT, "dane", f"{lata}_2024-04-27.png"))
    K = [k for k in json.load(gzip.open(os.path.join(OUT, "r2_klatki.json.gz"), "rt")) if k["lot"] == lot]
    przed = sorted([k for k in K if k["seria"] == "przed"], key=lambda k: k["sim"])
    po = sorted([k for k in K if k["seria"] == "po"], key=lambda k: k["sim"])
    D = {rd: Dop(rd) for rd in RODZAJE}

    def przygotuj(k):
        Rg = R2.rotm(k["gt_q"]); Re = NF.ekf_R(k["ekf_q"])
        C, Rk = kam.poza(np.array(k["gt_p"]), Rg)
        fr, fpoza = kam.renderuj(teren, PIKSEL_T, C, Rk)
        rect, mask, off = pr(fr, k["ekf_q"], k["ekf_pos"])
        ekf_en = np.array([k["ekf_pos"][1], k["ekf_pos"][0]])
        Ce = Re @ kam.t_link
        hc_e = -k["ekf_pos"][2] + Ce[2]
        return {"sim": k["sim"], "fr": fr, "Rg": Rg, "z_gt": k["gt_p"][2], "rect": rect, "mask": mask, "off": np.asarray(off), "ekf_en": ekf_en, "gt_en": np.array(k["gt_p"][:2]),
                "cam_gt": C[:2], "cam_ekf": ekf_en + np.asarray(off), "h_gt": C[2], "h_ekf": hc_e, "e": zawin(kurs(Rg) - kurs(Re)),
                "Re": Re, "poza": fpoza, "a": hc_e * (kam.H / 2) / kam.F}

    # --- R3: klatki kluczowe (decyzja drona z pozy EKF)
    su = np.arange(16) * (kam.W - 1) / 15; sv = np.arange(12) * (kam.H - 1) / 11
    pokryte = set()
    kf = []
    for k in przed:
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
        xs = np.arange(math.floor(x0 / SIATKA_KF), math.ceil(x1 / SIATKA_KF) + 1)
        ys = np.arange(math.floor(y0 / SIATKA_KF), math.ceil(y1 / SIATKA_KF) + 1)
        komorki = {(int(i), int(j)) for i in xs for j in ys
                   if cv2.pointPolygonTest(hull, (float(i * SIATKA_KF), float(j * SIATKA_KF)), False) >= 0}
        if not komorki:
            continue
        frac = len(komorki & pokryte) / len(komorki)
        if frac < PROG_KF:
            kf.append(przygotuj(k))
            pokryte |= komorki
    for x in kf:
        rect_gt, mask_gt = prost_R(pr, kam, x["fr"], x["Rg"], x["z_gt"])          # M0: prostowanie klatki kluczowej przy pozie GT
        for rd in RODZAJE:
            x[rd] = D[rd].cechy(x["rect"], x["mask"])
            x[rd + "_gt"] = D[rd].cechy(rect_gt, mask_gt)

    # --- M2: kalibracja kursu z fazy przed cięciem
    kal = {}
    for rd in RODZAJE:
        par = []
        for i in range(len(kf)):
            for j in range(len(kf)):
                if i == j:
                    continue
                d = kf[j]["cam_ekf"] - kf[i]["cam_ekf"]
                if np.linalg.norm(d) < KAL_D_MIN or pokrycie(kf[i]["cam_ekf"], kf[j]["cam_ekf"], kf[i]["a"]) < KAL_POKR_MIN:
                    continue
                w = D[rd].dopasuj(kf[j][rd], kf[i][rd])
                if w is None or w[0] < A_MIN:
                    continue
                r = np.array(w[1])
                if np.linalg.norm(r) < 1e-6:
                    continue
                par.append((zawin(math.atan2(d[1], d[0]) - math.atan2(r[1], r[0])), float(np.linalg.norm(d)), i, j))
        if par:
            s = sum(w * math.sin(e) for e, w, _, _ in par); c = sum(w * math.cos(e) for e, w, _, _ in par)
            psi = math.atan2(s, c)
        else:
            psi = 0.0
        e_kf = np.array([x["e"] for x in kf])
        kal[rd] = {"psi_kal_deg": round(math.degrees(psi), 3), "n_par": len(par),
                   "par_rozrzut_deg": round(float(np.degrees(np.std([zawin(e - psi) for e, _, _, _ in par]))), 3) if par else None,
                   "blad_kursu_kf_przed_deg": {"p50": round(float(np.degrees(np.median(np.abs(e_kf)))), 3),
                                               "max": round(float(np.degrees(np.abs(e_kf).max())), 3)} if len(kf) else None,
                   "blad_kursu_kf_po_kal_deg": {"p50": round(float(np.degrees(np.median(np.abs([zawin(e - psi) for e in e_kf])))), 3),
                                                "max": round(float(np.degrees(np.max(np.abs([zawin(e - psi) for e in e_kf])))), 3)}
                   if len(kf) else None, "_psi": psi}

    def geo(x, war, rd):
        if war == "M0":
            return x["cam_gt"], 0.0, 1.0                                   # klatka kluczowa wyprostowana przy pozie GT
        return x["cam_ekf"], (kal[rd]["_psi"] if war == "M2" else 0.0), 1.0

    # --- R4: łańcuch po cięciu
    bufor = {}
    t_cut = po[0]["sim"] - po[0]["od_ciecia"] if po else None
    st = {(w, rd): {"d": np.zeros(2), "t_fix": t_cut, "kl": []} for w in WARIANTY for rd in RODZAJE}
    t_dop = []
    for fi, k in enumerate(po):
        x = przygotuj(k)
        t0 = time.perf_counter()
        fx = {rd: D[rd].cechy(x["rect"], x["mask"]) for rd in RODZAJE}
        t_cechy = (time.perf_counter() - t0) * 1e3
        t_m = 0.0
        for rd in RODZAJE:
            for war in WARIANTY:
                s = st[(war, rd)]
                pred = x["ekf_en"] + s["d"]
                tau = k["sim"] - s["t_fix"]
                pc = pred + x["off"]
                kand = sorted(((pokrycie(pc, geo(y, war, rd)[0], x["a"]), i) for i, y in enumerate(kf)), reverse=True)
                kand = [i for p, i in kand[:N_KAND] if p > 0]
                best = None
                for i in kand:
                    zr = rd + "_gt" if war == "M0" else rd
                    if (fi, i, zr) not in bufor:
                        t1 = time.perf_counter()
                        bufor[(fi, i, zr)] = D[rd].dopasuj(fx[rd], kf[i][zr])
                        t_m += (time.perf_counter() - t1) * 1e3
                    w = bufor[(fi, i, zr)]
                    if w is not None and (best is None or w[0] > best[1][0]):
                        best = (i, w)
                rec = [round(k["sim"], 3), round(tau, 3), None, 0, None, None, None, None]
                if best is not None:
                    i, w = best
                    c, e, sc = geo(kf[i], war, rd)
                    cam = c + sc * (rz(e) @ np.array(w[1]))
                    fix = cam - x["off"]
                    err = float(np.linalg.norm(fix - x["gt_en"]))
                    innow = float(np.linalg.norm(fix - pred))
                    ok = w[0] >= A_MIN and innow <= G0 + R3.VR * tau
                    pk_gt = pokrycie(x["cam_gt"], kf[i]["cam_gt"], x["a"])
                    rec = [round(k["sim"], 3), round(tau, 3), round(err, 4), int(ok), w[0], round(float(np.hypot(*w[1])), 3),
                           round(pk_gt, 3), round(innow, 3)]
                    if ok:
                        s["d"] = fix - x["ekf_en"]
                        s["t_fix"] = k["sim"]
                s["kl"].append(rec)
        t_dop.append([round(t_cechy, 2), round(t_m, 2)])
    wyn = {"lot": lot, "lata": lata, "n_przed": len(przed), "n_po": len(po), "n_kf": len(kf), "t_ciecia": t_cut,
           "t_konca": po[-1]["sim"] if po else None,
           "kf": [{"sim": round(x["sim"], 3), "cam_ekf": [round(v, 3) for v in x["cam_ekf"]], "cam_gt": [round(float(v), 3) for v in x["cam_gt"]],
                   "e_deg": round(math.degrees(x["e"]), 3), "h_ekf": round(float(x["h_ekf"]), 3), "h_gt": round(float(x["h_gt"]), 3),
                   "n_cech": {rd: len(x[rd][0]) for rd in RODZAJE}} for x in kf],
           "kal": {rd: {kk: v for kk, v in kal[rd].items() if not kk.startswith("_")} for rd in RODZAJE},
           "klatki": {f"{w}/{rd}": st[(w, rd)]["kl"] for w in WARIANTY for rd in RODZAJE},
           "pola_klatki": ["sim", "tau", "blad", "przyjeta", "n_inl", "odl_od_kf", "pokrycie_gt", "innowacja"],
           "czas_ms": t_dop, "n_dopasowan": len(bufor), "zegar_s": round(time.time() - t_start, 1)}
    return wyn


def main():
    npr = min(int(sys.argv[1]) if len(sys.argv) > 1 else 8, 8)
    os.makedirs(CZ, exist_ok=True)
    loty = sorted({k["lot"] for k in json.load(gzip.open(os.path.join(OUT, "r2_klatki.json.gz"), "rt"))})
    zad = [(l, a) for a in LATY for l in loty]
    zad.sort(key=lambda z: z[0] != "L_c10_s01")
    nazwa = lambda z: os.path.join(CZ, f"{z[0]}_{z[1]}.json.gz")
    zad = [z for z in zad if not os.path.exists(nazwa(z))]
    t0 = time.time()
    print(time.strftime("%T"), "do zrobienia", len(zad), "procesy", npr, flush=True)
    with Pool(npr) as p:
        for w in p.imap_unordered(zadanie, zad):
            fn = nazwa((w["lot"], w["lata"]))
            with gzip.open(fn + ".tmp", "wt") as f:
                json.dump(w, f)
            os.replace(fn + ".tmp", fn)
            sk = {kk: (sum(r[3] for r in v), max((r[2] for r in v if r[3]), default=None)) for kk, v in w["klatki"].items()}
            print(time.strftime("%T"), f"{time.time() - t0:.0f}s", w["lot"], w["lata"], "kf", w["n_kf"], "kal",
                  {rd: v["psi_kal_deg"] for rd, v in w["kal"].items()}, sk, flush=True)


if __name__ == "__main__":
    main()
