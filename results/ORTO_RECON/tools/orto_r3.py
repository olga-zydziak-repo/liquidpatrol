#!/usr/bin/env python3
"""results/ORTO_RECON/tools/orto_r3.py — PROMPT_ORTO_S0 R3: kandydaci dopasowania klatki do ortofotomapy (klasyczne, deterministyczne).

Wejścia kandydata (tylko to, co dron ma bez GNSS): klatka, postawa EKF (q FRD→NED z migawki klatki), wysokość EKF (−z), predykcja pozycji
= ostatnia przyjęta poprawka + przyrost EKF od jej czasu (przed pierwszą przyjętą: pozycja EKF z chwili cięcia + przyrost, Δ = 0).
Prawda (GT) wyłącznie w ocenie (orto_r4.py), nigdy w kandydacie.

Wspólny krok — prostowanie: klatka rzutowana na płaski grunt przy postawie i wysokości EKF do siatki 0.1 m/px, N do góry, środek =
punkt pod kamerą, ±S_PROST m (maska pikseli z klatki). Geometria kamery z orto_r2.Kam (model.sdf + x500_base). Wysokość kamery =
−z_EKF + (R_EKF·t)_z, t = poza nadir_link względem ramy modelu (stała konstrukcyjna drona, nie GNSS).
Kandydaci:
  (skład wybrany próbą na klatkach cięć c05 — zbiór strojenia R5 — przed biegiem R4: CLAHE dla cech, gradient dla NCC, wzorzec ±6.5 m)
  K1 „SIFT”   — CLAHE (3.0, 8×8), cechy SIFT (cv2, 1500 w klatce, 30 000 na mapie), k = 8 najbliższych w całej mapie raz na klatkę,
                test ilorazu 0.8 na dwóch najbliższych w oknie szukania (brak drugiego w oknie ⇒ k-ty, test ostrzejszy), RANSAC podobieństwa (estimateAffinePartial2D,
                próg 3 px = 0.3 m, ziarno RNG stałe) → przesunięcie, kąt, skala, liczba inlierów;
  K2 „AKAZE”  — CLAHE, cechy AKAZE (deskryptor binarny, Hamming), test ilorazu 0.8, ten sam RANSAC;
  K3 „NCC”    — korelacja znormalizowana (TM_CCOEFF_NORMED) modułu gradientu (Sobel po rozmyciu σ 1.5 px) środkowego kwadratu ±6.5 m
                wyprostowanej klatki w wycinku mapy wokół
                predykcji ±(7 + R_szuk) m; szczyt z dopasowaniem paraboli (subpiksel), jakość = szczyt i iloraz do drugiego szczytu
                (poza kołem 1 m); obrót z EKF (tylko przesunięcie).
Promień szukania R_szuk(τ) = min(R0 + VR·τ, R_MAX), τ = wiek ostatniej przyjętej poprawki (dryf EKF: G NAD3 2.35 m przy 1.15 s).
Wynik kandydata: pozycja pojazdu (E, N) = pozycja kamery z dopasowania − (R_EKF·t)_EN; brak wyniku = za mało cech / brak modelu RANSAC.
"""
import math
import os
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orto_r2 as R2

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, os.path.join(ROOT, "harness"))
import nadir_fix as NF                                         # READ-ONLY: ekf_R (q FRD→NED → macierz FLU→ENU)

RHO = 0.1                 # m/px siatki prostowania i mapy
S_PROST = 15.0            # ±m wyprostowanej klatki
S_NCC = 6.5               # ±m wzorca NCC (kwadrat zawsze w kadrze: przekątna 9.2 m < pół-wysokość kadru 9.7 m przy 11 m)
R0, VR, R_MAX = 4.0, 3.0, 20.0
POL = 50.0                # okno mapy ±50 m (R1)
RATIO = 0.8
KNN = 8                   # sąsiedzi w całej mapie liczeni raz na klatkę; okno szukania filtruje (Cechy.dopasuj)
RANSAC_PX = 3.0
KANDYDACI = ("K1_SIFT", "K2_AKAZE", "K3_NCC")


def r_szuk(tau):
    return R_MAX if tau is None else min(R0 + VR * tau, R_MAX)


class Prost:
    def __init__(self, kam):
        self.kam = kam
        n = int(round(2 * S_PROST / RHO))
        x = (np.arange(n) + 0.5) * RHO - S_PROST
        self.dE, self.dN = np.meshgrid(x, -x)                    # wiersz 0 = północ
        self.n = n

    def __call__(self, klatka, ekf_q, ekf_pos):
        Rb = NF.ekf_R(ekf_q)
        t = self.kam.t_link
        off = Rb @ t
        hc = -ekf_pos[2] + off[2]
        Rk = Rb @ self.kam.R_cz
        P = np.stack([self.dE.ravel(), self.dN.ravel(), np.full(self.dE.size, -hc)], 1)   # względem kamery (0, 0, hc) → z = 0
        uv, d = self.kam.rzut(np.zeros(3), Rk, P)
        mx = uv[:, 0].reshape(self.n, self.n).astype(np.float32)
        my = uv[:, 1].reshape(self.n, self.n).astype(np.float32)
        ok = (d.reshape(self.n, self.n) > 0) & (mx >= 0) & (my >= 0) & (mx <= self.kam.W - 1) & (my <= self.kam.H - 1)
        mx[~ok] = -10; my[~ok] = -10
        im = cv2.remap(klatka, mx, my, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        return im, ok.astype(np.uint8) * 255, off[:2]


def szary(a):
    return a if a.ndim == 2 else cv2.cvtColor(a, cv2.COLOR_BGR2GRAY)


_CLAHE = cv2.createCLAHE(3.0, (8, 8))


def clahe(a):
    return _CLAHE.apply(szary(a))


def gradient(a):
    g = cv2.GaussianBlur(szary(a).astype(np.float32), (0, 0), 1.5)
    return np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1))


def px_do_en(x, y, pol=POL):
    return -pol + (x + 0.5) * RHO, pol - (y + 0.5) * RHO


def en_do_px(E, N, pol=POL):
    return (E + pol) / RHO - 0.5, (pol - N) / RHO - 0.5


class Cechy:
    """Detektor cech (SIFT / AKAZE) z mapą policzoną raz na łatę."""

    def __init__(self, rodzaj, mapa):
        self.rodzaj = rodzaj
        if rodzaj == "K1_SIFT":
            self.det_k = cv2.SIFT_create(nfeatures=1500)
            self.det_m = cv2.SIFT_create(nfeatures=30000)
            self.norm = cv2.NORM_L2
        else:
            self.det_k = self.det_m = cv2.AKAZE_create(threshold=0.0008)
            self.norm = cv2.NORM_HAMMING
        g = clahe(mapa)
        kp, ds = self.det_m.detectAndCompute(g, None)
        self.m_xy = np.array([k.pt for k in kp], np.float32).reshape(-1, 2)
        self.m_en = np.stack(px_do_en(self.m_xy[:, 0], self.m_xy[:, 1]), 1) if len(kp) else np.zeros((0, 2))
        self.m_ds = ds
        self.bf = cv2.BFMatcher(self.norm)

    def klatka(self, rect, maska):
        """Cechy klatki i k = KNN najbliższych w CAŁEJ mapie (raz na klatkę); okno szukania stosuje dopasuj()."""
        m = cv2.erode(maska, np.ones((9, 9), np.uint8))
        kp, ds = self.det_k.detectAndCompute(clahe(rect), m)
        xy = np.array([k.pt for k in kp], np.float32).reshape(-1, 2)
        if ds is None or len(xy) < 4 or self.m_ds is None:
            return None
        mm = self.bf.knnMatch(ds, self.m_ds, k=KNN)
        idx = np.array([[x.trainIdx for x in m] + [-1] * (KNN - len(m)) for m in mm], int)
        dist = np.array([[x.distance for x in m] + [np.inf] * (KNN - len(m)) for m in mm], float)
        return xy, idx, dist

    def dopasuj(self, fk, pred_cam_en, rs):
        """Test ilorazu na dwóch najbliższych W OKNIE spośród k = KNN; brak drugiego w oknie ⇒ drugi = k-ty (test ostrzejszy)."""
        if fk is None:
            return None
        xy, idx, dist = fk
        en = self.m_en[np.clip(idx, 0, None)]
        win = (idx >= 0) & (np.max(np.abs(en - pred_cam_en), 2) <= S_PROST + rs)
        if win.sum() < 3:
            return {"ok": False, "n_par": 0}
        cs = np.cumsum(win, 1)
        q = np.where(win.any(1))[0]
        j1 = np.argmax(win[q], 1)
        ma2 = win[q] & (cs[q] == 2)
        has2 = ma2.any(1)
        j2 = np.argmax(ma2, 1)
        d1 = dist[q, j1]
        d2 = np.where(has2, dist[q, j2], dist[q, KNN - 1])
        okr = d1 < RATIO * d2
        q, j1 = q[okr], j1[okr]
        if len(q) < 3:
            return {"ok": False, "n_par": int(len(q))}
        a = xy[q]
        b = self.m_xy[idx[q, j1]]
        cv2.setRNGSeed(12345)
        M, inl = cv2.estimateAffinePartial2D(a, b, method=cv2.RANSAC, ransacReprojThreshold=RANSAC_PX, maxIters=3000, confidence=0.999)
        if M is None:
            return {"ok": False, "n_par": int(len(q))}
        c = (S_PROST / RHO - 0.5)
        cx, cy = M @ np.array([c, c, 1.0])
        E, N = px_do_en(cx, cy)
        sk = math.hypot(M[0, 0], M[1, 0])
        kat = math.degrees(math.atan2(M[1, 0], M[0, 0]))
        return {"ok": True, "cam_en": [float(E), float(N)], "n_par": int(len(q)), "n_inl": int(inl.sum()), "skala": sk, "kat": kat}


class NCC:
    def __init__(self, mapa):
        self.g = gradient(mapa)
        n = int(round(S_NCC / RHO))
        self.n = n

    def klatka(self, rect, maska):
        c = rect.shape[0] // 2
        t = gradient(rect)[c - self.n:c + self.n, c - self.n:c + self.n]
        mk = maska[c - self.n:c + self.n, c - self.n:c + self.n]
        if mk.min() == 0 or t.std() < 1e-3:
            return None
        return t

    def dopasuj(self, t, pred_cam_en, rs):
        if t is None:
            return None
        x, y = en_do_px(*pred_cam_en)
        r = int(math.ceil((S_NCC + rs) / RHO))
        x0, y0 = int(round(x)) - r, int(round(y)) - r
        x1, y1 = x0 + 2 * r, y0 + 2 * r
        if x0 < 0 or y0 < 0 or x1 > self.g.shape[1] or y1 > self.g.shape[0]:
            xa, ya, xb, yb = max(x0, 0), max(y0, 0), min(x1, self.g.shape[1]), min(y1, self.g.shape[0])
            if xb - xa <= t.shape[1] or yb - ya <= t.shape[0]:
                return None
            x0, y0, x1, y1 = xa, ya, xb, yb
        s = self.g[y0:y1, x0:x1]
        if s.std() < 1e-3:
            return {"ok": False}
        res = cv2.matchTemplate(s, t, cv2.TM_CCOEFF_NORMED)
        _, pk, _, (px, py) = cv2.minMaxLoc(res)
        dx = dy = 0.0
        if 0 < px < res.shape[1] - 1:
            a, b, c = res[py, px - 1], res[py, px], res[py, px + 1]
            den = a - 2 * b + c
            dx = 0.5 * (a - c) / den if abs(den) > 1e-9 else 0.0
        if 0 < py < res.shape[0] - 1:
            a, b, c = res[py - 1, px], res[py, px], res[py + 1, px]
            den = a - 2 * b + c
            dy = 0.5 * (a - c) / den if abs(den) > 1e-9 else 0.0
        rr = res.copy()
        e = int(round(1.0 / RHO))
        rr[max(0, py - e):py + e + 1, max(0, px - e):px + e + 1] = -1
        drugi = float(rr.max()) if rr.size else -1.0
        cx = x0 + px + dx + self.n - 0.5                 # nadir kamery leży we wzorcu w indeksie n − 0.5 (środek siatki ±S_PROST)
        cy = y0 + py + dy + self.n - 0.5
        E, N = px_do_en(cx, cy)
        return {"ok": True, "cam_en": [float(E), float(N)], "szczyt": float(pk), "drugi": drugi,
                "iloraz": float(pk / drugi) if drugi > 1e-6 else float("inf")}


def czas_ms(f, *a):
    t0 = time.perf_counter()
    r = f(*a)
    return r, (time.perf_counter() - t0) * 1e3
