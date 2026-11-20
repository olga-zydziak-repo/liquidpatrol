#!/usr/bin/env python3
"""results/ARKUSZ_RECON/tools/ar_wspolne.py — wspólne dla reconu ARKUSZ (PROMPT_ARKUSZ_S0; 0 bootów).

Sieć: wagi net/frozen/ncp.npz przez pl_siec (READ-ONLY); tu własna implementacja kroku (F) i jakobianów.
Krok CfC: u = Wb^T [x; h] + bb0, b = tanh(u), g = tanh(Wg^T b + bg), hh = tanh(Wh^T b + bh), σ = sig(Wt^T b + bt),
h' = σ·g + (1 − σ)·hh; komenda y = tanh(Wo^T h' + bo)·vmax, potem clip_v (|y| ≤ 3). h' zależy od (x, h) tylko przez u.
Sytuacja (z cech widzianych przez sieć, nie z prawdy): s = (d, θ, vr, vt, rel_z, vd, wiek):
d = |rel_xy|, θ = atan2(rel_y, rel_x), u = rel_xy/d, vr = v_xy·u (własna prędkość ku celowi), vt = v_xy·u⊥, u⊥ = (−u_y, u_x).
Siatka: klucz (⌊d/Δd⌋, sektor θ z NS, ⌊vr/Δv⌋, ⌊vt/Δv⌋); rel_z, vd, wiek tylko w dopasowaniu (odchylenie 1 w STOP).
Mapa afiniczna komórki: regresja stanu na [1, d−d_c, θ−θ_c (zawinięte), vr, vt, rel_z, vd, wiek] po punktach komórki i
sąsiadów (±1 w każdym wymiarze siatki), grzbiet λ = 1e-6 względnie; za mało punktów (< MIN_PKT) ⇒ sąsiedztwo ±2.
"""
import math
import os
import sys

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
OUT = os.path.join(ROOT, "results/ARKUSZ_RECON")
sys.path.insert(0, os.path.join(ROOT, "results/PETLA_RECON/tools"))
import pl_siec as PS                                     # noqa: E402

M = PS.M
WB, BB0 = M.Wb, M.bb0
WBX, WBH = WB[:8], WB[8:]
WG, BG, WH, BH, WT, BT, WO, BO = M.Wg, M.bg, M.Wh, M.bh, M.Wt, M.bt, M.Wo, M.bo
MEAN, STD, H, VMAX = M.input_mean, M.input_std, M.H, M.vmax
DT = 0.05
NAZWY_S = ("d", "theta", "vr", "vt", "rel_z", "vd", "wiek")


def sig(z):
    return 1.0 / (1.0 + np.exp(-z))


def F(xn, h):
    """Krok stanu: xn (B,8) znormalizowane, h (B,H) → h'."""
    u = xn @ WBX + h @ WBH + BB0
    b = np.tanh(u)
    return sig(b @ WT + BT) * np.tanh(b @ WG + BG) + (1 - sig(b @ WT + BT)) * np.tanh(b @ WH + BH)


def komenda(h2):
    y = np.tanh(h2 @ WO + BO) * VMAX
    n = np.linalg.norm(y, axis=-1, keepdims=True)
    return y * np.where(n > 3.0, 3.0 / np.maximum(n, 1e-12), 1.0)


def dF_du(u):
    """Jakobian h' wzgl. u w punktach: u (B,20) → (B,H,20)."""
    b = np.tanh(u)
    g = np.tanh(b @ WG + BG); hh = np.tanh(b @ WH + BH); sg = sig(b @ WT + BT)
    # dh'/db = WG·diag(σ(1−g²)) + WH·diag((1−σ)(1−hh²)) + WT·diag((g−hh)σ(1−σ)) (transponowane do (H, BB))
    a1 = sg * (1 - g * g); a2 = (1 - sg) * (1 - hh * hh); a3 = (g - hh) * sg * (1 - sg)
    Jb = a1[:, :, None] * WG.T[None] + a2[:, :, None] * WH.T[None] + a3[:, :, None] * WT.T[None]
    return Jb * (1 - b * b)[:, None, :]


def norm(x):
    return PS.norm(x)


def sytuacja(x):
    """x (N,8) surowe cechy → s (N,7)."""
    d = np.hypot(x[:, 0], x[:, 1])
    th = np.arctan2(x[:, 1], x[:, 0])
    ux, uy = x[:, 0] / np.maximum(d, 1e-9), x[:, 1] / np.maximum(d, 1e-9)
    vr = x[:, 3] * ux + x[:, 4] * uy
    vt = -x[:, 3] * uy + x[:, 4] * ux
    return np.stack([d, th, vr, vt, x[:, 2], x[:, 5], np.minimum(x[:, 6], 1.0)], 1)


def cechy(s):
    """s (N,7) → x (N,8) surowe (valid = 1)."""
    d, th, vr, vt = s[:, 0], s[:, 1], s[:, 2], s[:, 3]
    c, n = np.cos(th), np.sin(th)
    return np.stack([d * c, d * n, s[:, 4], vr * c - vt * n, vr * n + vt * c, s[:, 5], s[:, 6], np.ones(len(s))], 1)


def ku_celowi(c, x):
    d = np.hypot(x[:, 0], x[:, 1])
    return (c[:, 0] * x[:, 0] + c[:, 1] * x[:, 1]) / np.maximum(d, 1e-9)


class Siatka:
    def __init__(self, dd=0.25, ns=64, dv=0.25):
        self.dd, self.ns, self.dv = dd, ns, dv

    def klucze(self, s):
        k = np.stack([np.floor(s[:, 0] / self.dd), np.floor((s[:, 1] + math.pi) / (2 * math.pi) * self.ns) % self.ns,
                      np.floor(s[:, 2] / self.dv), np.floor(s[:, 3] / self.dv)], 1).astype(np.int64)
        return k

    def kod(self, k):
        k = np.asarray(k, np.int64)
        return (((k[..., 0] + 1000) * 4096 + (k[..., 1] % self.ns)) * 4096 + (k[..., 2] + 2000)) * 4096 + (k[..., 3] + 2000)

    def srodek(self, k):
        k = np.asarray(k, np.float64)
        return np.stack([(k[..., 0] + 0.5) * self.dd, (k[..., 1] + 0.5) / self.ns * 2 * math.pi - math.pi,
                         (k[..., 2] + 0.5) * self.dv, (k[..., 3] + 0.5) * self.dv], -1)

    def polszer(self):
        return np.array([self.dd / 2, math.pi / self.ns, self.dv / 2, self.dv / 2])


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def regresory(s, sr):
    """s (N,7), sr (4,) środek komórki → (N,8): [1, d−dc, θ−θc, vr−vrc, vt−vtc, rel_z−2, vd, wiek−0.064]."""
    return np.stack([np.ones(len(s)), s[:, 0] - sr[0], wrap(s[:, 1] - sr[1]), s[:, 2] - sr[2], s[:, 3] - sr[3],
                     s[:, 4] - 2.0, s[:, 5], s[:, 6] - 0.064], 1)


MIN_PKT = 30
LAM = 1e-6


def _fit(R, Y):
    A = R.T @ R
    A += LAM * np.trace(A) / len(A) * np.eye(len(A))
    return np.linalg.solve(A, R.T @ Y)


class Mapa:
    """Mapa afiniczna sytuacja → stan na siatce, uczona na (s, h)."""

    def __init__(self, siatka, s, h, kol_stale=()):
        self.g = siatka
        self.kol_stale = tuple(kol_stale)        # regresory pominięte (np. wiek stały w modelu)
        k = siatka.klucze(s)
        kod = siatka.kod(k)
        order = np.argsort(kod, kind="stable")
        self.kod_s = kod[order]
        self.s, self.h = s[order], h[order]
        self.uk, self.start, self.ile = np.unique(self.kod_s, return_index=True, return_counts=True)
        self.k_uk = k[order][self.start]
        self.wsp = {}

    def _punkty(self, k, r):
        g = self.g
        sas = np.array(np.meshgrid(*[np.arange(-r, r + 1)] * 4, indexing="ij")).reshape(4, -1).T
        kk = k[None] + sas
        kk[:, 1] %= g.ns
        kody = g.kod(kk)
        pos = np.minimum(np.searchsorted(self.uk, kody), len(self.uk) - 1)
        pos = pos[self.uk[pos] == kody]
        idx = [np.arange(self.start[p], self.start[p] + self.ile[p]) for p in pos]
        return np.concatenate(idx) if idx else np.zeros(0, np.int64)

    def wspolczynniki(self, k):
        kod = int(self.g.kod(k))
        if kod in self.wsp:
            return self.wsp[kod]
        sr = self.g.srodek(k)
        for r in (1, 2, 3):
            idx = self._punkty(np.asarray(k), r)
            if len(idx) >= MIN_PKT:
                break
        if len(idx) < 3:
            self.wsp[kod] = None
            return None
        R = regresory(self.s[idx], sr)
        if self.kol_stale:
            R[:, list(self.kol_stale)] = 0.0
        C = _fit(R, self.h[idx])
        self.wsp[kod] = (C, r, len(idx))
        return self.wsp[kod]

    def przewiduj(self, s):
        k = self.g.klucze(s)
        kod = self.g.kod(k)
        out = np.full((len(s), H), np.nan)
        rr = np.zeros(len(s), int)
        o = np.argsort(kod, kind="stable")
        _, st, ile = np.unique(kod[o], return_index=True, return_counts=True)
        for a, n in zip(st, ile):
            m = o[a:a + n]
            w = self.wspolczynniki(k[m[0]])
            if w is None:
                continue
            R = regresory(s[m], self.g.srodek(k[m[0]]))
            if self.kol_stale:
                R[:, list(self.kol_stale)] = 0.0
            out[m] = R @ w[0]
            rr[m] = w[1]
        return out, rr
