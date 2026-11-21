#!/usr/bin/env python3
"""results/BLIZNIAK_RECON/tools/bz_afin.py — szczebel E3: formy afiniczne (PROMPT_BLIZNIAK_S0 §5; 0 bootów).

Postać: v = c + A·ε + [−e, e], ε ∈ [−1, 1]^n (symbole: stan początkowy h_init (20) i 7 współrzędnych sytuacji na każdy krok),
reszta e ≥ 0 per wymiar (przedział, bez nowych symboli). Wsadowo po komórkach: c (P,m), A (P,m,n), e (P,m).
Operacje (każda poprawna dla wszystkich ε ∈ [−1,1]^n):
  liniowa  W: c′ = c·W, A′ = W^T·A, e′ = |W|^T·e;
  cechy    x(s): x(s0) + Jx(s0)·(s − s0) ± (|Jx_int − Jx(s0)|·r_s) — wartość średnia z jakobianem przedziałowym na pudełku;
  f ∈ {tanh, sig} na [l, u] (z formy: c ± (Σ|A| + e)): sieczna α = (f(u) − f(l))/(u − l); odchylenie f(z) − α z na [l, u]
           ograniczone wartościami w końcach i w punktach f′(z) = α leżących w [l, u] (dla tanh: z = ±atanh(√(1 − α)); dla sig:
           σ(1−σ) = α); f ≈ α·v + β ± γ (β środek, γ półszerokość zakresu odchylenia); szerokość < 1e-9 ⇒ stała ± zapas;
  iloczyn  a·b: c_a c_b + c_a A_b + c_b A_a ± (|c_a| e_b + |c_b| e_a + R_a R_b), R = Σ|A| + e.
Zapas na zaokrąglenia: ZAPAS = 1e-9 dodawany do e po każdej operacji nieliniowej.
"""
import math

import numpy as np

import bz_dowod as BD

ZAPAS = 1e-9


class Af:
    __slots__ = ("c", "A", "e")

    def __init__(self, c, A, e):
        self.c, self.A, self.e = c, A, e

    def rad(self):
        return np.abs(self.A).sum(-1) + self.e

    def lin(self, W, b=None):
        c = self.c @ W + (0 if b is None else b)
        A = np.einsum("pmn,mk->pkn", self.A, W)
        e = self.e @ np.abs(W)
        return Af(c, A, e)

    def __add__(self, o):
        return Af(self.c + o.c, self.A + o.A, self.e + o.e)

    def skal(self, a, b=0.0):
        return Af(a * self.c + b, a * self.A, abs(a) * self.e)


def _odch_tanh(l, u, a):
    """Zakres f(z) − a z na [l, u], f = tanh. Punkty krytyczne: tanh′ = 1 − tanh² = a."""
    cand = [np.tanh(l) - a * l, np.tanh(u) - a * u]
    s = np.sqrt(np.clip(1 - a, 0, 1))
    for sg in (-1, 1):
        z = np.arctanh(np.clip(sg * s, -1 + 1e-15, 1 - 1e-15))
        ok = (z >= l) & (z <= u)
        v = np.tanh(z) - a * z
        cand.append(np.where(ok, v, cand[0]))
    C = np.stack(cand)
    return C.min(0), C.max(0)


def _odch_sig(l, u, a):
    sg = lambda z: 1 / (1 + np.exp(-z))
    cand = [sg(l) - a * l, sg(u) - a * u]
    disc = np.clip(1 - 4 * a, 0, None)
    for k in (-1, 1):
        sv = np.clip((1 + k * np.sqrt(disc)) / 2, 1e-15, 1 - 1e-15)
        z = np.log(sv / (1 - sv))
        ok = (z >= l) & (z <= u)
        cand.append(np.where(ok, sg(z) - a * z, cand[0]))
    C = np.stack(cand)
    return C.min(0), C.max(0)


def akt(v, f):
    r = v.rad()
    l, u = v.c - r, v.c + r
    fn = np.tanh if f == "tanh" else (lambda z: 1 / (1 + np.exp(-z)))
    w = u - l
    waskie = w < 1e-9
    a = np.where(waskie, 0.0, (fn(u) - fn(l)) / np.where(waskie, 1.0, w))
    lo, hi = (_odch_tanh if f == "tanh" else _odch_sig)(l, u, a)
    beta, gam = (lo + hi) / 2, (hi - lo) / 2
    # wąskie: stała f(c) ± (f(u) − f(l)) (monotoniczne)
    beta = np.where(waskie, fn(v.c), beta); gam = np.where(waskie, np.abs(fn(u) - fn(l)), gam)
    c = a * v.c + beta
    A = a[..., None] * v.A
    e = np.abs(a) * v.e + gam + ZAPAS
    return Af(c, A, e)


def mnoz(x, y):
    Rx, Ry = x.rad(), y.rad()
    c = x.c * y.c
    A = x.c[..., None] * y.A + y.c[..., None] * x.A
    e = np.abs(x.c) * y.e + np.abs(y.c) * x.e + Rx * Ry + ZAPAS
    # uwaga: człon (Aε)(Bε) mieści się w ±(Σ|A|)(Σ|B|) ≤ Rx·Ry; pozostałe części iloczynu reszt też w Rx·Ry.
    return Af(c, A, e)


def cechy_af(S, Sl, Sh, kol, n):
    """Forma afiniczna xn (P,8) z sytuacji w pudełku [Sl, Sh] (P,7); symbole sytuacji w kolumnach kol (7) z n."""
    P = len(Sl)
    s0, rs = (Sl + Sh) / 2, (Sh - Sl) / 2
    xn0 = BD.srodek_x(S, s0)
    _, _, Jl, Jh = S.x_box(Sl, Sh)
    # jakobian w środku (dokładny)
    d, th, vr, vt = s0[:, 0], s0[:, 1], s0[:, 2], s0[:, 3]
    c, sn = np.cos(th), np.sin(th)
    J0 = np.zeros((P, 8, 7))
    J0[:, 0, 0] = c; J0[:, 0, 1] = -d * sn
    J0[:, 1, 0] = sn; J0[:, 1, 1] = d * c
    J0[:, 2, 4] = 1
    J0[:, 3, 1] = -vr * sn - vt * c; J0[:, 3, 2] = c; J0[:, 3, 3] = -sn
    J0[:, 4, 1] = vr * c - vt * sn; J0[:, 4, 2] = sn; J0[:, 4, 3] = c
    J0[:, 5, 5] = 1; J0[:, 6, 6] = 1
    J0 = J0 / S.std[None, :, None]
    dev = np.maximum(np.abs(Jl - J0), np.abs(Jh - J0))
    A = np.zeros((P, 8, n))
    A[:, :, kol] = J0 * rs[:, None, :]
    e = np.einsum("pxs,ps->px", dev, rs) + ZAPAS
    return Af(xn0, A, e)


def krok(S, h, x):
    m = S.m
    u = x.lin(S.WX) + h.lin(S.WH, m.bb0)
    b = akt(u, "tanh")
    g = akt(b.lin(m.Wg, m.bg), "tanh")
    q = akt(b.lin(m.Wh, m.bh), "tanh")
    s = akt(b.lin(m.Wt, m.bt), "sig")
    # h′ = s·g + (1 − s)·q = q + s·(g − q)
    gq = Af(g.c - q.c, g.A - q.A, g.e + q.e)
    return q + mnoz(s, gq)


def przytnij(v, lo=-1.0, hi=1.0):
    """Stan zawsze w (−1, 1): nie zmienia formy, służy tylko pudełku do raportu."""
    r = v.rad()
    return np.maximum(v.c - r, lo), np.minimum(v.c + r, hi)


def lancuch_af(S, lo4, hi4, D, js, nadpisz=None):
    P = len(lo4); n = 20 + 7 * len(js)
    h = Af(np.zeros((P, 20)), np.zeros((P, 20, n)), np.zeros((P, 20)))
    h.A[:, :, :20] = np.eye(20)[None]
    for i, j in enumerate(js):
        Sl, Sh = (nadpisz or {}).get(j) or BD.Xj(lo4, hi4, j, D)
        x = cechy_af(S, Sl, Sh, list(range(20 + 7 * i, 27 + 7 * i)), n)
        h = krok(S, h, x)
    return h


def U_af(S, lo4, hi4, k, D, j0=0):
    h = lancuch_af(S, lo4, hi4, D, list(range(j0 + k - 1, j0 - 1, -1)))
    return przytnij(h)


def ku_af(S, lo4, hi4, D, k, X0=None, nadpisz=None):
    """Dolna granica ku po clip_v: łańcuch przez X_k … X_1, krok X_0 (komórka albo pod-pudełko), odczyt; cos/sin θ_t jako
    forma afiniczna w symbolu θ_t (wartość średnia: cos θ0 − sin θ0·(θ − θ0) ± max|cos|·r²/2)."""
    m = S.m
    js = list(range(k, -1, -1))
    P = len(lo4); n = 20 + 7 * len(js)
    h = Af(np.zeros((P, 20)), np.zeros((P, 20, n)), np.zeros((P, 20)))
    h.A[:, :, :20] = np.eye(20)[None]
    for i, j in enumerate(js):
        if j == 0:
            Sl, Sh = BD.pelne(lo4, hi4) if X0 is None else X0
        else:
            Sl, Sh = (nadpisz or {}).get(j) or BD.Xj(lo4, hi4, j, D)
        x = cechy_af(S, Sl, Sh, list(range(20 + 7 * i, 27 + 7 * i)), n)
        h = krok(S, h, x)
    a = akt(h.lin(m.Wo, m.bo), "tanh")
    y = a.skal(3.0)
    # u = (cos θ, sin θ), θ w symbolu kolumny 20 + 7·k + 1
    kt = 20 + 7 * k + 1
    th0, rt = (Sl[:, 1] + Sh[:, 1]) / 2, (Sh[:, 1] - Sl[:, 1]) / 2
    def kier(f, df, sgn):
        A = np.zeros((P, 1, n)); A[:, 0, kt] = df(th0) * rt
        return Af(f(th0)[:, None], A, (rt * rt / 2)[:, None] + ZAPAS)
    cu = kier(np.cos, lambda t: -np.sin(t), 1); su = kier(np.sin, np.cos, 1)
    yx = Af(y.c[:, :1], y.A[:, :1], y.e[:, :1]); yy = Af(y.c[:, 1:2], y.A[:, 1:2], y.e[:, 1:2])
    ku = mnoz(yx, cu) + mnoz(yy, su)
    lo_raw = (ku.c - ku.rad())[:, 0]
    yr = y.rad()
    yl, yh = np.maximum(y.c - yr, -3), np.minimum(y.c + yr, 3)
    return BD.ku_dolne(lo_raw, (yl, yh)), przytnij(h)
