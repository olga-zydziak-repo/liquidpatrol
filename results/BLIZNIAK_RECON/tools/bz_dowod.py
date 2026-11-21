#!/usr/bin/env python3
"""results/BLIZNIAK_RECON/tools/bz_dowod.py — R3 lemat U i R4 zdanie S (PROMPT_BLIZNIAK_S0 §5–§6; 0 bootów).

Dziedzina 𝒟: d 4.0–15.0 m, θ dowolny, (v_r, v_t) w kole |v| ≤ 3.2 m/s (siatka: pudełka 0.25 m/s przecinające koło, wartości
przycięte do ±3.2), rel_z 1.85–2.15, vd ±0.08, wiek 0.024–0.15 (≤ AGE_CAP, clip_age bez skutku), valid = 1.
Siatka: d 0.25 m, θ 2π/64, v_r i v_t 0.25 m/s. Komórka c = pudełko (d, θ, v_r, v_t) × pełne przedziały (rel_z, vd, wiek).
X_j(c): pudełko sytuacji o (d, θ, v_r, v_t) odległych od c o ≤ j·Δ, przycięte do 𝒟; (rel_z, vd, wiek) pełne.
Cechy: x = (d cos θ, d sin θ, rel_z, v_r cos θ − v_t sin θ, v_r sin θ + v_t cos θ, vd, wiek, 1), standaryzacja modelu.
Lemat U: h_t ∈ U_k(c) = F̂(X_0, F̂(X_1, … F̂(X_{k−1}, H_init))), H_init = [−1, 1]²⁰ („pudełko”), albo rozwinięcie od zera
+ B(W)^k w normie max („zero”); dla bliźniaka przecięcie obu. Do S: h_{t−1} ∈ U_k^(1)(c) = to samo z X_1 … X_k.
Komenda: y = 3·tanh(Wo^T F(x_t, h_{t−1}) + bo); ku_raw = y_x cos θ + y_y sin θ; clip_v: ku ≥ ku_raw_lo · min(1, 3/‖y‖_max)
gdy ku_raw_lo > 0 (dla ku_raw_lo ≤ 0 zdanie niedowiedzione).
Szczeble F̂ / ku: E1 — przedziały naturalne; E2 — ostatni krok i odczyt w postaci średniej wartości (jakobian przedziałowy po
(s_t, h_{t−1})), przecięte z E1; E3 — E2 z podziałem X_0 na 2 części w (d, θ, v_r, v_t) (16 pudełek) i X_1 na 3 części
w tych samych współrzędnych (81 pudełek) dla U^(1) — tylko komórki, w których E2 nie dowodzi.
Zaokrąglenia: jawny zapas ZAPAS = 1e-9 na każdym ograniczeniu (bez zaokrąglania kierunkowego; float64, błąd względny ~1e-15).
"""
import math
import os
import sys

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from net.models import NCP20                             # noqa: E402

ZAPAS = 1e-9
DD, NS, DV = 0.25, 64, 0.25
DOM = {"d": (4.0, 15.0), "v": 3.2, "rz": (1.85, 2.15), "vd": (-0.08, 0.08), "wiek": (0.024, 0.15)}
DELTA_A = np.array([0.321, 0.0528, 0.238, 0.123])


def sig(z):
    return 1.0 / (1.0 + np.exp(-z))


def B(m):
    A = np.maximum(np.abs(m.Wg), np.abs(m.Wh)) + 0.5 * np.abs(m.Wt)
    s = np.abs(m.Wb[8:]).sum(0)
    return float((s[:, None] * A).sum(0).max())


# ---------------------------------------------------------------- przedziały
def imul(al, ah, bl, bh):
    p = np.stack([al * bl, al * bh, ah * bl, ah * bh])
    return p.min(0), p.max(0)


def icos(lo, hi):
    cl, ch = np.cos(lo), np.cos(hi)
    l, h = np.minimum(cl, ch), np.maximum(cl, ch)
    has0 = np.ceil(lo / (2 * math.pi)) * 2 * math.pi <= hi
    hasp = np.ceil((lo - math.pi) / (2 * math.pi)) * 2 * math.pi + math.pi <= hi
    return np.where(hasp, -1.0, l), np.where(has0, 1.0, h)


def isin(lo, hi):
    return icos(lo - math.pi / 2, hi - math.pi / 2)


def imv(lo, hi, W):
    c, r = (lo + hi) / 2, (hi - lo) / 2
    cc, rr = c @ W, r @ np.abs(W)
    return cc - rr - ZAPAS, cc + rr + ZAPAS


def sq1(lo, hi):
    a, b = lo * lo, hi * hi
    mn = np.where((lo <= 0) & (hi >= 0), 0.0, np.minimum(a, b))
    return 1 - np.maximum(a, b), 1 - mn


def s1s(lo, hi):
    a, b = lo * (1 - lo), hi * (1 - hi)
    return np.minimum(a, b), np.where((lo <= 0.5) & (hi >= 0.5), 0.25, np.maximum(a, b))


class Siec:
    def __init__(self, m):
        self.m = m
        self.WX, self.WH = m.Wb[:8], m.Wb[8:]
        self.mean, self.std = m.input_mean, m.input_std
        self.B_nominal = B(m)
        self.B = self.B_nominal * (1 + 1e-12) + 1e-15        # jawny zapas na zaokrąglenia rachunku B(W)

    # ---- punktowo
    def F(self, xn, h):
        m = self.m
        b = np.tanh(xn @ self.WX + h @ self.WH + m.bb0)
        s = sig(b @ m.Wt + m.bt)
        return s * np.tanh(b @ m.Wg + m.bg) + (1 - s) * np.tanh(b @ m.Wh + m.bh)

    def y(self, h2):
        return 3.0 * np.tanh(h2 @ self.m.Wo + self.m.bo)

    def ku(self, xn, h, th):
        """Składowa ku celowi po clip_v (punktowo)."""
        y = self.y(self.F(xn, h))
        n = np.linalg.norm(y, axis=1)
        sc = np.where(n > 3.0, 3.0 / np.maximum(n, 1e-12), 1.0)
        return (y[:, 0] * np.cos(th) + y[:, 1] * np.sin(th)) * sc

    # ---- przedziałowo
    def x_box(self, Sl, Sh):
        """Sytuacja (P,7) [d, θ, vr, vt, rel_z, vd, wiek] → xn (P,8) przedział i jakobian dxn/ds (P,8,7) przedział."""
        dl, dh = Sl[:, 0], Sh[:, 0]
        cl, ch = icos(Sl[:, 1], Sh[:, 1]); nl, nh = isin(Sl[:, 1], Sh[:, 1])
        x0 = imul(dl, dh, cl, ch); x1 = imul(dl, dh, nl, nh)
        a = imul(Sl[:, 2], Sh[:, 2], cl, ch); b = imul(Sl[:, 3], Sh[:, 3], nl, nh)
        a2 = imul(Sl[:, 2], Sh[:, 2], nl, nh); b2 = imul(Sl[:, 3], Sh[:, 3], cl, ch)
        P = len(Sl); one = np.ones(P)
        xl = np.stack([x0[0], x1[0], Sl[:, 4], a[0] - b[1], a2[0] + b2[0], Sl[:, 5], Sl[:, 6], one], 1)
        xh = np.stack([x0[1], x1[1], Sh[:, 4], a[1] - b[0], a2[1] + b2[1], Sh[:, 5], Sh[:, 6], one], 1)
        xnl, xnh = (xl - self.mean) / self.std, (xh - self.mean) / self.std
        Jl = np.zeros((P, 8, 7)); Jh = np.zeros((P, 8, 7))
        def put(i, j, iv):
            Jl[:, i, j], Jh[:, i, j] = iv[0] / self.std[i], iv[1] / self.std[i]
        put(0, 0, (cl, ch)); put(0, 1, imul(-dh, -dl, nl, nh))
        put(1, 0, (nl, nh)); put(1, 1, imul(dl, dh, cl, ch))
        put(2, 4, (one, one))
        t1 = imul(-Sh[:, 2], -Sl[:, 2], nl, nh); t2 = imul(Sl[:, 3], Sh[:, 3], cl, ch); put(3, 1, (t1[0] - t2[1], t1[1] - t2[0]))
        put(3, 2, (cl, ch)); put(3, 3, (-nh, -nl))
        t1 = imul(Sl[:, 2], Sh[:, 2], cl, ch); t2 = imul(Sl[:, 3], Sh[:, 3], nl, nh); put(4, 1, (t1[0] - t2[1], t1[1] - t2[0]))
        put(4, 2, (nl, nh)); put(4, 3, (cl, ch))
        put(5, 5, (one, one)); put(6, 6, (one, one))
        return xnl - ZAPAS, xnh + ZAPAS, Jl, Jh

    def F_box(self, xl, xh, Hl, Hh, jac=False):
        m = self.m
        a = imv(xl, xh, self.WX); b = imv(Hl, Hh, self.WH)
        Ul, Uh = a[0] + b[0] + m.bb0, a[1] + b[1] + m.bb0
        bl, bh = np.tanh(Ul), np.tanh(Uh)
        gl, gh = imv(bl, bh, m.Wg); gl, gh = np.tanh(gl + m.bg), np.tanh(gh + m.bg)
        ql, qh = imv(bl, bh, m.Wh); ql, qh = np.tanh(ql + m.bh), np.tanh(qh + m.bh)
        tl, th = imv(bl, bh, m.Wt); sl, sh = sig(tl + m.bt), sig(th + m.bt)
        p1 = imul(sl, sh, gl, gh); p2 = imul(1 - sh, 1 - sl, ql, qh)
        Fl, Fh = np.maximum(p1[0] + p2[0] - ZAPAS, -1.0), np.minimum(p1[1] + p2[1] + ZAPAS, 1.0)
        if not jac:
            return Fl, Fh
        a1 = imul(sl, sh, *sq1(gl, gh)); a2 = imul(1 - sh, 1 - sl, *sq1(ql, qh)); a3 = imul(gl - qh, gh - ql, *s1s(sl, sh))
        Jl = np.zeros(Ul.shape + (20,)); Jh = np.zeros_like(Jl)
        for aa, W in ((a1, m.Wg), (a2, m.Wh), (a3, m.Wt)):
            q_ = np.stack([aa[0][:, :, None] * W.T[None], aa[1][:, :, None] * W.T[None]])
            Jl += q_.min(0); Jh += q_.max(0)
        d = sq1(bl, bh)
        Ml, Mh = imul(Jl, Jh, d[0][:, None, :], d[1][:, None, :])     # dh′/du (P, H, BB)
        return Fl, Fh, Ml - ZAPAS, Mh + ZAPAS

    def y_box(self, Hl, Hh):
        a = imv(Hl, Hh, self.m.Wo)
        return 3 * np.tanh(a[0] + self.m.bo), 3 * np.tanh(a[1] + self.m.bo)


# ---------------------------------------------------------------- siatka
def komorki(dmin=4.0, dmax=15.0):
    """Wszystkie komórki 𝒟 z d w [dmin, dmax]: tablica (N, 4) dolnych krawędzi [d, θ, vr, vt] i górnych."""
    dlo = np.arange(dmin, dmax - 1e-9, DD)
    tlo = -math.pi + np.arange(NS) * 2 * math.pi / NS
    vlo = np.arange(-3.25, 3.25 - 1e-9, DV)
    vv = np.array([(a, b) for a in vlo for b in vlo
                   if math.hypot(max(0.0, abs(a + DV / 2) - DV / 2), max(0.0, abs(b + DV / 2) - DV / 2)) <= DOM["v"]])
    D, T, V = np.meshgrid(np.arange(len(dlo)), np.arange(NS), np.arange(len(vv)), indexing="ij")
    D, T, V = D.ravel(), T.ravel(), V.ravel()
    lo = np.stack([dlo[D], tlo[T], vv[V, 0], vv[V, 1]], 1)
    hi = lo + np.array([DD, 2 * math.pi / NS, DV, DV])
    lo[:, 2:] = np.maximum(lo[:, 2:], -DOM["v"]); hi[:, 2:] = np.minimum(hi[:, 2:], DOM["v"])
    return lo, hi


def pelne(lo4, hi4):
    P = len(lo4)
    Sl = np.c_[lo4, np.full(P, DOM["rz"][0]), np.full(P, DOM["vd"][0]), np.full(P, DOM["wiek"][0])]
    Sh = np.c_[hi4, np.full(P, DOM["rz"][1]), np.full(P, DOM["vd"][1]), np.full(P, DOM["wiek"][1])]
    return Sl, Sh


def Xj(lo4, hi4, j, delta):
    lo = lo4 - j * delta; hi = hi4 + j * delta
    lo[:, 0] = np.maximum(lo[:, 0], DOM["d"][0]); hi[:, 0] = np.minimum(hi[:, 0], DOM["d"][1])
    lo[:, 2:] = np.maximum(lo[:, 2:], -DOM["v"]); hi[:, 2:] = np.minimum(hi[:, 2:], DOM["v"])
    return pelne(lo, hi)


def U(S, lo4, hi4, k, delta, j0=0):
    """h ∈ U: rozwinięcie przez X_{j0+k−1} … X_{j0} (najstarszy pierwszy). Przecięcie: od [−1,1] i od zera + B^k."""
    P = len(lo4)
    Hb = (-np.ones((P, 20)), np.ones((P, 20)))
    Hz = (np.zeros((P, 20)), np.zeros((P, 20)))
    for j in range(j0 + k - 1, j0 - 1, -1):
        Sl, Sh = Xj(lo4, hi4, j, delta)
        xl, xh, _, _ = S.x_box(Sl, Sh)
        Hb = S.F_box(xl, xh, *Hb)
        Hz = S.F_box(xl, xh, *Hz)
    if S.B < 1:
        e = S.B ** k + ZAPAS
        Hz = (np.maximum(Hz[0] - e, -1), np.minimum(Hz[1] + e, 1))
        return np.maximum(Hb[0], Hz[0]), np.minimum(Hb[1], Hz[1])
    return Hb


def ku_E1(S, Sl, Sh, Hl, Hh):
    xl, xh, _, _ = S.x_box(Sl, Sh)
    Fl, Fh = S.F_box(xl, xh, Hl, Hh)
    yl, yh = S.y_box(Fl, Fh)
    cl, ch = icos(Sl[:, 1], Sh[:, 1]); nl, nh = isin(Sl[:, 1], Sh[:, 1])
    a = imul(yl[:, 0], yh[:, 0], cl, ch); b = imul(yl[:, 1], yh[:, 1], nl, nh)
    return a[0] + b[0] - ZAPAS, (yl, yh)


def ku_E2(S, Sl, Sh, Hl, Hh):
    """Postać o wartości średniej dla ku_raw(s, h) na pudełku (s ∈ [Sl,Sh] (7), h ∈ [Hl,Hh] (20))."""
    m = S.m
    P = len(Sl)
    s0, rs = (Sl + Sh) / 2, (Sh - Sl) / 2
    h0, rh = (Hl + Hh) / 2, (Hh - Hl) / 2
    xl, xh, Jxl, Jxh = S.x_box(Sl, Sh)
    Fl, Fh, Ml, Mh = S.F_box(xl, xh, Hl, Hh, jac=True)
    # wartość w środku
    x0 = np.stack([s0[:, 0] * np.cos(s0[:, 1]), s0[:, 0] * np.sin(s0[:, 1]), s0[:, 4],
                   s0[:, 2] * np.cos(s0[:, 1]) - s0[:, 3] * np.sin(s0[:, 1]), s0[:, 2] * np.sin(s0[:, 1]) + s0[:, 3] * np.cos(s0[:, 1]),
                   s0[:, 5], s0[:, 6], np.ones(P)], 1)
    xn0 = (x0 - S.mean) / S.std
    y0 = S.y(S.F(xn0, h0))
    k0 = y0[:, 0] * np.cos(s0[:, 1]) + y0[:, 1] * np.sin(s0[:, 1])
    # dy/dh′ = 3(1 − a²) Wo^T, a ∈ tanh(Wo^T F + bo)
    al, ah_ = imv(Fl, Fh, m.Wo); al, ah_ = np.tanh(al + m.bo), np.tanh(ah_ + m.bo)
    d1 = sq1(al, ah_)                                                    # (P, 3)
    cl, ch = icos(Sl[:, 1], Sh[:, 1]); nl, nh = isin(Sl[:, 1], Sh[:, 1])
    # w = ∂ku_raw/∂h′ = 3 Σ_i u_i (1 − a_i²) Wo[:, i]  (P, 20), u = (cos, sin)
    wl = np.zeros((P, 20)); wh = np.zeros((P, 20))
    for i, (ul, uh) in enumerate(((cl, ch), (nl, nh))):
        g = imul(ul, uh, d1[0][:, i], d1[1][:, i])                        # (P,)
        t = np.stack([3 * g[0][:, None] * m.Wo[:, i][None], 3 * g[1][:, None] * m.Wo[:, i][None]])
        wl += t.min(0); wh += t.max(0)
    # ∂ku/∂h = w^T M Wh^T ; ∂ku/∂s = w^T M Wx^T Jx + y·∂u/∂θ (kolumna θ)
    wc, wr = (wl + wh) / 2, (wh - wl) / 2
    Mc, Mr = (Ml + Mh) / 2, (Mh - Ml) / 2
    vc = np.einsum("ph,phk->pk", wc, Mc)
    vr = np.einsum("ph,phk->pk", np.abs(wc), Mr) + np.einsum("ph,phk->pk", wr, np.abs(Mc)) + np.einsum("ph,phk->pk", wr, Mr)
    Jh_c, Jh_r = vc @ S.WH.T, vr @ np.abs(S.WH.T)                         # (P, 20)
    Pc = np.einsum("kx,pxs->pks", S.WX.T, (Jxl + Jxh) / 2); Pr = np.einsum("kx,pxs->pks", np.abs(S.WX.T), (Jxh - Jxl) / 2)
    Js_c = np.einsum("pk,pks->ps", vc, Pc)
    Js_r = np.einsum("pk,pks->ps", np.abs(vc), Pr) + np.einsum("pk,pks->ps", vr, np.abs(Pc)) + np.einsum("pk,pks->ps", vr, Pr)
    yl, yh = S.y_box(Fl, Fh)
    dth = imul(yl[:, 0], yh[:, 0], -nh, -nl); dth2 = imul(yl[:, 1], yh[:, 1], cl, ch)   # ∂(y·u)/∂θ = −y_x sin + y_y cos
    tl_, th_ = dth[0] + dth2[0], dth[1] + dth2[1]
    Js_c[:, 1] += (tl_ + th_) / 2; Js_r[:, 1] += (th_ - tl_) / 2
    R = ((np.abs(Jh_c) + Jh_r) * rh).sum(1) + ((np.abs(Js_c) + Js_r) * rs).sum(1)
    lo = k0 - R - ZAPAS - 1e-12 * np.abs(k0)
    l1, _ = ku_E1(S, Sl, Sh, Hl, Hh)
    return np.maximum(lo, l1), (yl, yh)


def ku_dolne(lo_raw, yb):
    yl, yh = yb
    nmax = np.sqrt((np.maximum(np.abs(yl), np.abs(yh)) ** 2).sum(1))
    sc = np.minimum(1.0, 3.0 / nmax)
    return np.where(lo_raw > 0, lo_raw * sc, lo_raw)


def k_dla(S, cel=0.005):
    return int(math.ceil(math.log(cel) / math.log(S.B))) if S.B < 1 else None


# ---------------------------------------------------------------- E2: forma Taylora po całej historii
def srodek_x(S, s0):
    P = len(s0)
    x = np.stack([s0[:, 0] * np.cos(s0[:, 1]), s0[:, 0] * np.sin(s0[:, 1]), s0[:, 4],
                  s0[:, 2] * np.cos(s0[:, 1]) - s0[:, 3] * np.sin(s0[:, 1]), s0[:, 2] * np.sin(s0[:, 1]) + s0[:, 3] * np.cos(s0[:, 1]),
                  s0[:, 5], s0[:, 6], np.ones(P)], 1)
    return (x - S.mean) / S.std


def mm(Ac, Ar, Bc, Br):
    """(P,a,b) × (P,b,c) przedziały w postaci środek ± promień."""
    return Ac @ Bc, np.abs(Ac) @ Br + Ar @ np.abs(Bc) + Ar @ Br


def lancuch(S, lo4, hi4, D, js, nadpisz=None):
    """Forma Taylora stanu po krokach z pudełkami X_j, j ∈ js (najstarszy pierwszy), od h_init ∈ [−1, 1]²⁰.
    Zmienne: h_init (20), potem 7 współrzędnych sytuacji na każdy krok. Zwraca hc (P,20), Jc, Jr (P,20,nv), r (P,nv), H (lo, hi)."""
    P = len(lo4); nk = len(js); nv = 20 + 7 * nk
    r = np.zeros((P, nv)); r[:, :20] = 1.0
    hc = np.zeros((P, 20))
    Jc = np.zeros((P, 20, nv)); Jc[:, :, :20] = np.eye(20)[None]
    Jr = np.zeros((P, 20, nv))
    Hl, Hh = -np.ones((P, 20)), np.ones((P, 20))
    for n, j in enumerate(js):
        Sl, Sh = (nadpisz or {}).get(j) or Xj(lo4, hi4, j, D)
        cols = slice(20 + 7 * n, 27 + 7 * n)
        r[:, cols] = (Sh - Sl) / 2
        xl, xh, Jxl, Jxh = S.x_box(Sl, Sh)
        Fl, Fh, Ml, Mh = S.F_box(xl, xh, Hl, Hh, jac=True)
        hc = S.F(srodek_x(S, (Sl + Sh) / 2), hc)
        Pc = np.einsum("kh,phv->pkv", S.WH.T, Jc); Pr = np.einsum("kh,phv->pkv", np.abs(S.WH.T), Jr)
        Pc[:, :, cols] += np.einsum("kx,pxs->pks", S.WX.T, (Jxl + Jxh) / 2)
        Pr[:, :, cols] += np.einsum("kx,pxs->pks", np.abs(S.WX.T), (Jxh - Jxl) / 2)
        Jc, Jr = mm((Ml + Mh) / 2, (Mh - Ml) / 2, Pc, Pr)
        Jr += ZAPAS
        rad = np.einsum("phv,pv->ph", np.abs(Jc) + Jr, r) + ZAPAS
        Hl, Hh = np.maximum(hc - rad, Fl), np.minimum(hc + rad, Fh)
    return hc, Jc, Jr, r, (Hl, Hh)


def ku_lancuch(S, lo4, hi4, D, k, X0=None, nadpisz=None):
    """Dolna granica ku po clip_v: h_{t−1} z łańcucha przez X_k … X_1, krok t z pudełkiem X_0 (domyślnie komórka, albo X0 = (lo4′, hi4′)
    pod-pudełko komórki), odczyt. Forma Taylora po wszystkich zmiennych; przecięta z E1 na tym samym pudełku."""
    m = S.m
    hc, Jc, Jr, r, (Hl, Hh) = lancuch(S, lo4, hi4, D, list(range(k, 0, -1)), nadpisz)
    P = len(lo4)
    Sl, Sh = pelne(lo4, hi4) if X0 is None else X0
    xl, xh, Jxl, Jxh = S.x_box(Sl, Sh)
    Fl, Fh, Ml, Mh = S.F_box(xl, xh, Hl, Hh, jac=True)
    s0 = (Sl + Sh) / 2
    h2c = S.F(srodek_x(S, s0), hc)
    y0 = S.y(h2c)
    k0 = y0[:, 0] * np.cos(s0[:, 1]) + y0[:, 1] * np.sin(s0[:, 1])
    al, ah_ = imv(Fl, Fh, m.Wo); al, ah_ = np.tanh(al + m.bo), np.tanh(ah_ + m.bo)
    d1 = sq1(al, ah_)
    cl, ch = icos(Sl[:, 1], Sh[:, 1]); nl, nh = isin(Sl[:, 1], Sh[:, 1])
    wl = np.zeros((P, 20)); wh = np.zeros((P, 20))
    for i, (ul, uh) in enumerate(((cl, ch), (nl, nh))):
        g = imul(ul, uh, d1[0][:, i], d1[1][:, i])
        t = np.stack([3 * g[0][:, None] * m.Wo[:, i][None], 3 * g[1][:, None] * m.Wo[:, i][None]])
        wl += t.min(0); wh += t.max(0)
    nv = r.shape[1] + 7
    rr = np.concatenate([r, (Sh - Sl) / 2], 1)
    Pc = np.zeros((P, 20, nv)); Pr = np.zeros((P, 20, nv))
    Pc[:, :, :-7] = np.einsum("kh,phv->pkv", S.WH.T, Jc); Pr[:, :, :-7] = np.einsum("kh,phv->pkv", np.abs(S.WH.T), Jr)
    Pc[:, :, -7:] = np.einsum("kx,pxs->pks", S.WX.T, (Jxl + Jxh) / 2)
    Pr[:, :, -7:] = np.einsum("kx,pxs->pks", np.abs(S.WX.T), (Jxh - Jxl) / 2)
    Qc, Qr = mm((Ml + Mh) / 2, (Mh - Ml) / 2, Pc, Pr)                      # dh_t/dz (P,20,nv)
    wc, wr = (wl + wh) / 2, (wh - wl) / 2
    Kc = np.einsum("ph,phv->pv", wc, Qc)
    Kr = np.einsum("ph,phv->pv", np.abs(wc), Qr) + np.einsum("ph,phv->pv", wr, np.abs(Qc)) + np.einsum("ph,phv->pv", wr, Qr)
    yl, yh = S.y_box(Fl, Fh)
    a1 = imul(yl[:, 0], yh[:, 0], -nh, -nl); a2 = imul(yl[:, 1], yh[:, 1], cl, ch)
    Kc[:, -6] += (a1[0] + a2[0] + a1[1] + a2[1]) / 2; Kr[:, -6] += (a1[1] + a2[1] - a1[0] - a2[0]) / 2    # kolumna θ_t
    lo = k0 - ((np.abs(Kc) + Kr) * rr).sum(1) - ZAPAS - 1e-12 * np.abs(k0)
    l1, _ = ku_E1(S, Sl, Sh, Hl, Hh)
    lo = np.maximum(lo, l1)
    return ku_dolne(lo, (yl, yh)), (Hl, Hh)


# ---------------------------------------------------------------- E2: skurcz B(W) + wartość średnia po wejściu
def podzial(Sl, Sh, czesci):
    """Pod-pudełka pudełka (P,7): czesci (7,) liczb części na współrzędną. Generator par (Sl′, Sh′)."""
    czesci = np.asarray(czesci)
    w = (Sh - Sl) / czesci
    for idx in np.ndindex(*czesci):
        a = Sl + np.array(idx) * w
        yield a, a + w


def U_skurcz(S, lo4, hi4, k, D, j0=0, czesci=None):
    """Stan jako ĥ ± r (norma max). Krok: F(X_j, ĥ) przedziałowo po samym wejściu (E2 po x: wartość w środku + jakobian po x),
    potem ⊕ B·r (|F(x, h) − F(x, ĥ)|∞ ≤ B·|h − ĥ|∞ dla każdego x, B z wag z zapasem); przecięcie z E1. Start ĥ = 0, r = 1.
    Zwraca pudełko (lo, hi) stanu po rozwinięciu przez X_{j0+k−1} … X_{j0}."""
    assert S.B < 1
    P = len(lo4)
    El, Eh = -np.ones((P, 20)), np.ones((P, 20))
    hc = np.zeros((P, 20)); r = np.ones(P)
    for j in range(j0 + k - 1, j0 - 1, -1):
        SL, SH = Xj(lo4, hi4, j, D)
        cz = (czesci or {}).get(j, [1] * 7)
        Ml_, Mh_ = np.full((P, 20), np.inf), np.full((P, 20), -np.inf)
        for Sl, Sh in podzial(SL, SH, cz):
            # E2 po x przy stanie punktowym: F(x, hc) ∈ F(x0, hc) ± (|J_x|)·r_x, J_x = M·Wx^T·Jx na pod-pudełku
            xl, xh, Jxl, Jxh = S.x_box(Sl, Sh)
            Fl, Fh, Ml, Mh = S.F_box(xl, xh, hc, hc, jac=True)
            s0 = (Sl + Sh) / 2; rs = (Sh - Sl) / 2
            f0 = S.F(srodek_x(S, s0), hc)
            Pc = np.einsum("kx,pxs->pks", S.WX.T, (Jxl + Jxh) / 2); Pr = np.einsum("kx,pxs->pks", np.abs(S.WX.T), (Jxh - Jxl) / 2)
            Qc, Qr = mm((Ml + Mh) / 2, (Mh - Ml) / 2, Pc, Pr)
            rad = np.einsum("phs,ps->ph", np.abs(Qc) + Qr, rs) + ZAPAS
            Ml_ = np.minimum(Ml_, np.maximum(f0 - rad, Fl)); Mh_ = np.maximum(Mh_, np.minimum(f0 + rad, Fh))
        xl, xh, _, _ = S.x_box(SL, SH)
        e = S.B * r[:, None] + ZAPAS
        nl, nh = Ml_ - e, Mh_ + e
        E1l, E1h = S.F_box(xl, xh, El, Eh)
        El, Eh = np.maximum(nl, E1l), np.minimum(nh, E1h)
        hc = (El + Eh) / 2; r = ((Eh - El) / 2).max(1)
    return El, Eh


def ku_skurcz(S, lo4, hi4, D, k, X0=None, H1=None):
    """Dolna granica ku po clip_v. h_{t−1} ∈ H1 = U_skurcz przez X_k … X_1 (pudełko; ĥ = środek, r = max półszerokość).
    ku_raw(x, h) ≥ min_x ku_raw(x, ĥ) − W·B·r, W = max Σ_i |∂ku_raw/∂h′_i| na pudełku (h′ = F(x, h));
    min_x ku_raw(x, ĥ) z ku_E2 przy stanie punktowym, na pudełku X0 (domyślnie komórka). Przecięte z E1."""
    m = S.m
    if H1 is None:
        H1 = U_skurcz(S, lo4, hi4, k, D, j0=1)
    Hl, Hh = H1
    hc = (Hl + Hh) / 2; r = ((Hh - Hl) / 2).max(1)
    l0, h0_ = (lo4, hi4) if X0 is None else X0
    Sl, Sh = pelne(l0, h0_)
    lpt, _ = ku_E2(S, Sl, Sh, hc, hc)
    xl, xh, _, _ = S.x_box(Sl, Sh)
    Fl, Fh = S.F_box(xl, xh, Hl, Hh)
    al, ah_ = imv(Fl, Fh, m.Wo); al, ah_ = np.tanh(al + m.bo), np.tanh(ah_ + m.bo)
    d1 = sq1(al, ah_)
    cl, ch = icos(Sl[:, 1], Sh[:, 1]); nl, nh = isin(Sl[:, 1], Sh[:, 1])
    P = len(Sl)
    wl = np.zeros((P, 20)); wh = np.zeros((P, 20))
    for i, (ul, uh) in enumerate(((cl, ch), (nl, nh))):
        g = imul(ul, uh, d1[0][:, i], d1[1][:, i])
        t = np.stack([3 * g[0][:, None] * m.Wo[:, i][None], 3 * g[1][:, None] * m.Wo[:, i][None]])
        wl += t.min(0); wh += t.max(0)
    W = np.maximum(np.abs(wl), np.abs(wh)).sum(1)
    lo = lpt - W * S.B * r - ZAPAS
    l1, _ = ku_E1(S, Sl, Sh, Hl, Hh)
    lo = np.maximum(lo, l1)
    yl, yh = S.y_box(Fl, Fh)
    return ku_dolne(lo, (yl, yh))
