#!/usr/bin/env python3
"""results/ARKUSZ_RECON/tools/ar_r3.py — R3 drabina dowodu, lemat arkusza k = 1 (PROMPT_ARKUSZ_S0 §5; 0 bootów).

Dziedzina: biegi_W.npz (wariant W), komórki siatki podstawowej (d 0.25 m, θ 64 sektory, vr/vt 0.25 m/s) zajęte przez stany
t ≥ 30 s; rel_z i vd poza siatką — pudełko globalne [min, max] zaobserwowane; wiek stały 0.064 (silnik PĘTLI).
Wejścia dopuszczalne: s′ w komórce zajętej c′, |s′ − s| ≤ Δ per współrzędna, Δ = 1.2 × max zmiana na tick w biegach.
Para (c, c′): s ∈ c (pudełko 6D), s′ ∈ c′ ∩ (c ⊕ Δ) (pudełko), stan h ∈ Z_c. Lemat dla c′: obraz ⊆ Z_c′ dla każdej pary wchodzącej.
Szczeble:
  D1 — Z_c = pudełko stanu; obraz F(x(S′), Z_c) w naturalnym rozszerzeniu przedziałowym.
  D2 — Z_c = {Φ_c(s) + e : s ∈ c, e ∈ E_c}; G = F(x(s′), Φ_c(s) + e) − Φ_c′(s′); obraz w postaci średniej wartości:
       G(z0) ± (|Jc| + Jr)·r, J = jakobian przedziałowy na całym pudełku zmiennych (s, s′, e); przecięty z naturalnym
       rozszerzeniem F(U) − Φ_c′(S′) (oba poprawne).
  D3 — jak D2, reszta e = T_c ẽ, ẽ ∈ Ẽ_c; T_c = rzeczywista baza własna ∂F/∂h w środku komórki (bloki 2×2 dla par
       zespolonych, kolumny o max |·| = 1, porządek |λ| malejąco, znak: największy wpis dodatni); obraz w ẽ′ = T_c′^{-1} G.
Punkt stały: E_c (Ẽ_c) startuje z obwiedni reszt danych (+10% szerokości + 1e-3), rośnie do obwiedni obrazów; komórka, której
półszerokość w jednostkach stanu (|T_c|·r_Ẽ) przekracza CAP = 0.25, zostaje zamrożona na tym, co ma, i ma lemat niedowiedziony.
Sufit empiryczny: to samo z obrazami z próbek (punkty losowe) zamiast ograniczeń — dolne oszacowanie każdego niezmiennika tej postaci.
Test poprawności: 10⁶ punktów losowych (10⁴ par × 100) z pudełek wejściowych, obraz każdego w wyliczonym ograniczeniu.
"""
import json
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ar_wspolne as AW                                  # noqa: E402

OUT = AW.OUT
CAP = 0.25
PAD = 1e-9
WX, WH_, B0 = AW.WBX, AW.WBH, AW.BB0
WXa, WHa = np.abs(WX), np.abs(WH_)
MEANX, STDX = AW.MEAN, AW.STD
WIEK = 0.064


# ---------------------------------------------------------------- przedziały
def imul(al, ah, bl, bh):
    p = np.stack([al * bl, al * bh, ah * bl, ah * bh])
    return p.min(0), p.max(0)


def icos(lo, hi):
    """cos na [lo, hi] (szerokość < 2π)."""
    cl, ch = np.cos(lo), np.cos(hi)
    l, h = np.minimum(cl, ch), np.maximum(cl, ch)
    k0 = np.ceil(lo / (2 * math.pi)); has0 = k0 * 2 * math.pi <= hi
    kp = np.ceil((lo - math.pi) / (2 * math.pi)); hasp = kp * 2 * math.pi + math.pi <= hi
    return np.where(hasp, -1.0, l), np.where(has0, 1.0, h)


def isin(lo, hi):
    return icos(lo - math.pi / 2, hi - math.pi / 2)


def imv(lo, hi, W, Wa):
    """Przedział (P,n) razy macierz punktowa (n,m)."""
    c, r = (lo + hi) / 2, (hi - lo) / 2
    cc, rr = c @ W, r @ Wa
    return cc - rr - PAD, cc + rr + PAD


def sq01(lo, hi):
    """1 − x² na [lo, hi]."""
    a, b = lo * lo, hi * hi
    mx = np.maximum(a, b); mn = np.where((lo <= 0) & (hi >= 0), 0.0, np.minimum(a, b))
    return 1 - mx, 1 - mn


def s1s(lo, hi):
    """σ(1 − σ) na [lo, hi] ⊂ (0, 1)."""
    a, b = lo * (1 - lo), hi * (1 - hi)
    mx = np.where((lo <= 0.5) & (hi >= 0.5), 0.25, np.maximum(a, b))
    return np.minimum(a, b), mx


def x_box(Sl, Sh):
    """Pudełko sytuacji (P,6) [d, θ, vr, vt, rel_z, vd] → pudełko cech znormalizowanych (P,8) i jakobian przedziałowy dxn/ds (P,8,6)."""
    dl, dh = Sl[:, 0], Sh[:, 0]
    cl, ch = icos(Sl[:, 1], Sh[:, 1]); nl, nh = isin(Sl[:, 1], Sh[:, 1])
    vrl, vrh, vtl, vth = Sl[:, 2], Sh[:, 2], Sl[:, 3], Sh[:, 3]
    x0 = imul(dl, dh, cl, ch); x1 = imul(dl, dh, nl, nh)
    a = imul(vrl, vrh, cl, ch); b = imul(vtl, vth, nl, nh); x3 = (a[0] - b[1], a[1] - b[0])
    a2 = imul(vrl, vrh, nl, nh); b2 = imul(vtl, vth, cl, ch); x4 = (a2[0] + b2[0], a2[1] + b2[1])
    P = len(Sl)
    xl = np.stack([x0[0], x1[0], Sl[:, 4], x3[0], x4[0], Sl[:, 5], np.full(P, WIEK), np.ones(P)], 1)
    xh = np.stack([x0[1], x1[1], Sh[:, 4], x3[1], x4[1], Sh[:, 5], np.full(P, WIEK), np.ones(P)], 1)
    xnl, xnh = (xl - MEANX) / STDX, (xh - MEANX) / STDX
    Jl = np.zeros((P, 8, 6)); Jh = np.zeros((P, 8, 6))
    def put(i, j, iv):
        Jl[:, i, j], Jh[:, i, j] = iv[0] / STDX[i], iv[1] / STDX[i]
    put(0, 0, (cl, ch)); put(0, 1, imul(-dh, -dl, nl, nh))          # ∂(d cos θ)/∂θ = −d sin θ
    put(1, 0, (nl, nh)); put(1, 1, imul(dl, dh, cl, ch))
    put(2, 4, (np.ones(P), np.ones(P)))
    t1 = imul(-vrh, -vrl, nl, nh); t2 = imul(vtl, vth, cl, ch); put(3, 1, (t1[0] - t2[1], t1[1] - t2[0]))
    put(3, 2, (cl, ch)); put(3, 3, (-nh, -nl))
    t1 = imul(vrl, vrh, cl, ch); t2 = imul(vtl, vth, nl, nh); put(4, 1, (t1[0] - t2[1], t1[1] - t2[0]))
    put(4, 2, (nl, nh)); put(4, 3, (cl, ch))
    put(5, 5, (np.ones(P), np.ones(P)))
    return xnl - PAD, xnh + PAD, Jl, Jh


def F_box(Ul, Uh, z_jac=True):
    """Pudełko u (P,20) → pudełko h′ (P,20) i (opcjonalnie) jakobian przedziałowy dh′/du (P,20,20) (Ml, Mh)."""
    bl, bh = np.tanh(Ul), np.tanh(Uh)
    gl, gh = imv(bl, bh, AW.WG, np.abs(AW.WG)); gl, gh = np.tanh(gl + AW.BG), np.tanh(gh + AW.BG)
    hl, hh = imv(bl, bh, AW.WH, np.abs(AW.WH)); hl, hh = np.tanh(hl + AW.BH), np.tanh(hh + AW.BH)
    tl, th = imv(bl, bh, AW.WT, np.abs(AW.WT)); sl, sh = AW.sig(tl + AW.BT), AW.sig(th + AW.BT)
    p1 = imul(sl, sh, gl, gh); p2 = imul(1 - sh, 1 - sl, hl, hh)
    Hl, Hh = p1[0] + p2[0] - PAD, p1[1] + p2[1] + PAD
    if not z_jac:
        return Hl, Hh, None, None
    g2 = sq01(gl, gh); h2 = sq01(hl, hh)
    a1 = imul(sl, sh, *g2); a2 = imul(1 - sh, 1 - sl, *h2); a3 = imul(gl - hh, gh - hl, *s1s(sl, sh))
    Jl = np.zeros(Ul.shape + (20,)); Jh = np.zeros_like(Jl)
    for a, W in ((a1, AW.WG), (a2, AW.WH), (a3, AW.WT)):
        WT_ = W.T[None]                                            # (1, H, BB)
        q = np.stack([a[0][:, :, None] * WT_, a[1][:, :, None] * WT_])
        Jl += q.min(0); Jh += q.max(0)
    d = sq01(bl, bh)
    Ml, Mh = imul(Jl, Jh, d[0][:, None, :], d[1][:, None, :])
    return Hl, Hh, Ml - PAD, Mh + PAD


def mm_ip(Ml, Mh, Pm):
    """Macierz przedziałowa (P,a,b) × punktowa (P,b,c) lub (b,c) → (c, r)."""
    Mc, Mr = (Ml + Mh) / 2, (Mh - Ml) / 2
    return Mc @ Pm, Mr @ np.abs(Pm)


def mm_ii(Ml, Mh, Pl, Ph):
    Mc, Mr = (Ml + Mh) / 2, (Mh - Ml) / 2
    Pc, Pr = (Pl + Ph) / 2, (Ph - Pl) / 2
    return Mc @ Pc, np.abs(Mc) @ Pr + Mr @ np.abs(Pc) + Mr @ Pr


# ---------------------------------------------------------------- dziedzina
class Dziedzina:
    def __init__(self, plik="biegi_W.npz"):
        a = time.time()
        z = np.load(os.path.join(OUT, plik))
        x = z["x"]; h = z["h"]
        nb, nt = x.shape[:2]
        s7 = AW.sytuacja(x.reshape(-1, 8))
        ds = np.diff(s7.reshape(nb, nt, 7), axis=1); ds[..., 1] = AW.wrap(ds[..., 1])
        self.delta = 1.2 * np.abs(ds).max((0, 1))[:6]
        self.s = s7[:, :6]; self.h = h.reshape(-1, AW.H)
        self.g = AW.Siatka()
        k = self.g.klucze(s7); kod = self.g.kod(k)
        o = np.argsort(kod, kind="stable")
        self.uk, st, self.ile = np.unique(kod[o], return_index=True, return_counts=True)
        self.k = k[o][st]
        self.nc = len(self.uk)
        self.cel_stanu = np.empty(len(kod), np.int64); self.cel_stanu[o] = np.repeat(np.arange(self.nc), self.ile)
        self.rz = (self.s[:, 4].min(), self.s[:, 4].max()); self.vd = (self.s[:, 5].min(), self.s[:, 5].max())
        sr4 = self.g.srodek(self.k)
        self.sc = np.c_[sr4, np.full(self.nc, sum(self.rz) / 2), np.full(self.nc, sum(self.vd) / 2)]
        self.w = np.tile(np.r_[self.g.polszer(), (self.rz[1] - self.rz[0]) / 2, (self.vd[1] - self.vd[0]) / 2], (self.nc, 1))
        # mapa na wszystkich biegach
        mp = AW.Mapa(self.g, s7, self.h, (7,))
        self.phi = np.zeros((self.nc, AW.H)); self.A = np.zeros((self.nc, AW.H, 6))
        for i in range(self.nc):
            C = mp.wspolczynniki(self.k[i])[0]
            self.phi[i] = C[0] + C[5] * (self.sc[i, 4] - 2.0) + C[6] * self.sc[i, 5]
            self.A[i] = C[1:7].T
        self.e_dane = self.h - self.Phi(self.cel_stanu, self.s)
        self.pary()
        print(f"dziedzina: {self.nc} komórek, {len(self.pc)} par, Δ={np.round(self.delta, 4)}, {time.time() - a:.0f}s", flush=True)

    def Phi(self, ci, s, sc=None):
        sc = self.sc[ci] if sc is None else sc
        dsv = s - sc; dsv[:, 1] = AW.wrap(dsv[:, 1])
        return self.phi[ci] + np.einsum("phj,pj->ph", self.A[ci], dsv)

    def pary(self):
        g, D = self.g, self.delta
        rd = int(math.ceil(D[0] / g.dd)); rt = int(math.ceil(D[1] / (2 * math.pi / g.ns))); rv = int(math.ceil(max(D[2], D[3]) / g.dv))
        off = np.array(np.meshgrid(np.arange(-rd, rd + 1), np.arange(-rt, rt + 1), np.arange(-rv, rv + 1), np.arange(-rv, rv + 1), indexing="ij")).reshape(4, -1).T
        PC, PD = [], []
        for o in off:
            kk = self.k + o; kk[:, 1] %= g.ns
            kod = g.kod(kk)
            pos = np.minimum(np.searchsorted(self.uk, kod), self.nc - 1)
            ok = self.uk[pos] == kod
            PC.append(np.where(ok)[0]); PD.append(pos[ok])
        pc, pd = np.concatenate(PC), np.concatenate(PD)
        # pudełko s′ = c′ ∩ (c ⊕ Δ), θ c′ przesunięte najbliżej c
        lo_c, hi_c = self.sc[pc] - self.w[pc] - D, self.sc[pc] + self.w[pc] + D
        scd = self.sc[pd].copy(); scd[:, 1] = self.sc[pc, 1] + AW.wrap(self.sc[pd, 1] - self.sc[pc, 1])
        lo, hi = np.maximum(lo_c, scd - self.w[pd]), np.minimum(hi_c, scd + self.w[pd])
        ok = (lo <= hi).all(1)
        self.pc, self.pd, self.Sl, self.Sh, self.scd = pc[ok], pd[ok], lo[ok], hi[ok], scd[ok]

    def baza(self):
        """T_c (D3) z ∂F/∂h w środku komórki."""
        xn = AW.norm(AW.cechy(np.c_[self.sc, np.full(self.nc, WIEK)]))
        u = xn @ WX + self.phi @ WH_ + B0
        J = AW.dF_du(u) @ WH_.T
        T = np.zeros((self.nc, 20, 20)); rho = np.zeros(self.nc)
        for i in range(self.nc):
            w, V = np.linalg.eig(J[i])
            o = np.lexsort((np.angle(w), -np.abs(w))); w, V = w[o], V[:, o]
            cols, j = [], 0
            while j < 20:
                if abs(w[j].imag) < 1e-10:
                    cols.append(V[:, j].real); j += 1
                else:
                    cols += [V[:, j].real, V[:, j].imag]; j += 2
            Tc = np.array(cols).T
            Tc /= np.abs(Tc).max(0)
            Tc *= np.sign(Tc[np.abs(Tc).argmax(0), np.arange(20)])
            T[i] = Tc; rho[i] = np.abs(w).max()
        self.T, self.Ti, self.rho = T, np.linalg.inv(T), rho


# ---------------------------------------------------------------- obrazy
def obraz_D1(Dz, idx, Zl, Zh):
    pc, pd = Dz.pc[idx], Dz.pd[idx]
    xl, xh, _, _ = x_box(Dz.Sl[idx], Dz.Sh[idx])
    a = imv(xl, xh, WX, WXa); b = imv(Zl[pc], Zh[pc], WH_, WHa)
    Hl, Hh, _, _ = F_box(a[0] + b[0] + B0, a[1] + b[1] + B0, False)
    return Hl, Hh


def obraz_D23(Dz, idx, El, Eh, T=None, Ti=None):
    """Ograniczenie G na parach idx; E w ukł. T_c (D3) albo stanu (D2, T None)."""
    pc, pd = Dz.pc[idx], Dz.pd[idx]
    P = len(idx)
    Sl, Sh = Dz.Sl[idx], Dz.Sh[idx]
    s_l, s_h = Dz.sc[pc] - Dz.w[pc], Dz.sc[pc] + Dz.w[pc]
    s0, sp0 = Dz.sc[pc], (Sl + Sh) / 2
    rs, rsp = Dz.w[pc], (Sh - Sl) / 2
    e0, re = (El[pc] + Eh[pc]) / 2, (Eh[pc] - El[pc]) / 2
    Tc = T[pc] if T is not None else None
    # pudełko u
    xl, xh, Jxl, Jxh = x_box(Sl, Sh)
    phi_c, phi_r = Dz.phi[pc], np.einsum("phj,pj->ph", np.abs(Dz.A[pc]), rs)
    if Tc is None:
        hc, hr = phi_c + e0, phi_r + re
    else:
        hc, hr = phi_c + np.einsum("phj,pj->ph", Tc, e0), phi_r + np.einsum("phj,pj->ph", np.abs(Tc), re)
    a = imv(xl, xh, WX, WXa); b = imv(hc - hr, hc + hr, WH_, WHa)
    Ul, Uh = a[0] + b[0] + B0, a[1] + b[1] + B0
    Hl, Hh, Ml, Mh = F_box(Ul, Uh)
    # wartość w środku
    x0 = AW.norm(AW.cechy(np.c_[sp0, np.full(P, WIEK)]))
    h0 = Dz.phi[pc] + (Tc @ e0[:, :, None])[:, :, 0] if Tc is not None else Dz.phi[pc] + e0
    G0 = AW.F(x0, h0) - Dz.Phi(pd, sp0, Dz.scd[idx])
    # jakobiany
    c1, r1 = mm_ii(Ml, Mh, *(lambda c, r: (c - r, c + r))(*(WX.T[None] @ ((Jxl + Jxh) / 2), WXa.T[None] @ ((Jxh - Jxl) / 2))))
    Jsp_c, Jsp_r = c1 - Dz.A[pd], r1
    Jsc, Jsr = mm_ip(Ml, Mh, WH_.T[None] @ Dz.A[pc])
    Pe = WH_.T[None] @ Tc if Tc is not None else WH_.T
    Jec, Jer = mm_ip(Ml, Mh, Pe)
    if Ti is not None:
        Tid = Ti[pd]; Tia = np.abs(Tid)
        G0 = (Tid @ G0[:, :, None])[:, :, 0]
        Jsp_c, Jsp_r = Tid @ Jsp_c, Tia @ Jsp_r
        Jsc, Jsr = Tid @ Jsc, Tia @ Jsr
        Jec, Jer = Tid @ Jec, Tia @ Jer
    R = ((np.abs(Jsp_c) + Jsp_r) @ rsp[:, :, None] + (np.abs(Jsc) + Jsr) @ rs[:, :, None] + (np.abs(Jec) + Jer) @ re[:, :, None])[:, :, 0]
    lo, hi = G0 - R - PAD - 1e-12 * np.abs(G0), G0 + R + PAD + 1e-12 * np.abs(G0)
    if Ti is None:
        # naturalne rozszerzenie: H − Φ_c′(S′)
        pr = np.einsum("phj,pj->ph", np.abs(Dz.A[pd]), rsp)
        pcen = Dz.Phi(pd, sp0, Dz.scd[idx])
        lo, hi = np.maximum(lo, Hl - pcen - pr), np.minimum(hi, Hh - pcen + pr)
    return lo, hi, (Jsp_c, Jsp_r, Jsc, Jsr, Jec, Jer)


def probki(Dz, idx, El, Eh, rng, n, T=None, Ti=None, poziom="D2"):
    """n punktów losowych na parę: obraz dokładny (P, n, 20)."""
    pc, pd = Dz.pc[idx], Dz.pd[idx]
    P = len(idx)
    s = Dz.sc[pc][:, None] + Dz.w[pc][:, None] * rng.uniform(-1, 1, (P, n, 6))
    sp = Dz.Sl[idx][:, None] + (Dz.Sh[idx] - Dz.Sl[idx])[:, None] * rng.uniform(0, 1, (P, n, 6))
    e = El[pc][:, None] + (Eh[pc] - El[pc])[:, None] * rng.uniform(0, 1, (P, n, 20))
    rep = lambda a: np.repeat(a, n, 0)
    s, sp, e = s.reshape(-1, 6), sp.reshape(-1, 6), e.reshape(-1, 20)
    xn = AW.norm(AW.cechy(np.c_[sp, np.full(len(sp), WIEK)]))
    if poziom == "D1":
        return AW.F(xn, e).reshape(P, n, 20)
    hpre = Dz.Phi(rep(pc), s)
    hpre = hpre + ((rep(T[pc]) @ e[:, :, None])[:, :, 0] if T is not None else e)
    G = AW.F(xn, hpre) - Dz.Phi(rep(pd), sp, rep(Dz.scd[idx]))
    if Ti is not None:
        G = (rep(Ti[pd]) @ G[:, :, None])[:, :, 0]
    return G.reshape(P, n, 20)


# ---------------------------------------------------------------- punkt stały
def hull_po_celu(pd, lo, hi, nc):
    L = np.full((nc, 20), np.inf); Hh = np.full((nc, 20), -np.inf)
    np.minimum.at(L, pd, lo); np.maximum.at(Hh, pd, hi)
    return L, Hh


def punkt_staly(Dz, poziom, El0, Eh0, iters=12, batch=20000, empiryczny=False, rng=None, n_emp=8, log=None):
    T = Dz.T if poziom == "D3" else None
    Ti = Dz.Ti if poziom == "D3" else None
    scale = np.abs(T).sum(2) if T is not None else np.ones((Dz.nc, 20))      # wiersz |T_c| → półszerokość w stanie
    El, Eh = El0.copy(), Eh0.copy()
    zamr = np.zeros(Dz.nc, bool)
    hist = []
    nP = len(Dz.pc)
    ops = 0
    t0 = time.time()
    for it in range(iters):
        L = np.full((Dz.nc, 20), np.inf); Hh = np.full((Dz.nc, 20), -np.inf)
        for st in range(0, nP, batch):
            idx = np.arange(st, min(st + batch, nP))
            if empiryczny:
                G = probki(Dz, idx, El, Eh, rng, n_emp, T, Ti, poziom)
                lo, hi = G.min(1), G.max(1)
            elif poziom == "D1":
                lo, hi = obraz_D1(Dz, idx, El, Eh); ops += len(idx)
            else:
                lo, hi, _ = obraz_D23(Dz, idx, El, Eh, T, Ti); ops += len(idx)
            np.minimum.at(L, Dz.pd[idx], lo); np.maximum.at(Hh, Dz.pd[idx], hi)
        wej = np.isfinite(L[:, 0])
        ok = wej & (L >= El - 1e-15).all(1) & (Hh <= Eh + 1e-15).all(1)
        ok |= ~wej
        nEl, nEh = np.where(wej[:, None], np.minimum(El, L), El), np.where(wej[:, None], np.maximum(Eh, Hh), Eh)
        if poziom == "D1":
            pw = (nEh - nEl) / 2
        else:
            pw = scale * np.maximum(np.abs(nEl), np.abs(nEh))                     # półszerokość reszty w jednostkach stanu (od 0)
        nowe_zamr = (pw > CAP).any(1) & ~zamr
        zamr |= nowe_zamr
        upd = ~zamr
        El = np.where(upd[:, None], nEl, El); Eh = np.where(upd[:, None], nEh, Eh)
        w = Dz.ile.astype(float)
        dow = ok & ~zamr
        rec = {"iter": it, "dowiedzione_komorki": float(dow.mean()), "dowiedzione_czas": float(w[dow].sum() / w.sum()),
               "zamrozone": int(zamr.sum()), "czas_s": time.time() - t0}
        hist.append(rec)
        if log:
            print(poziom, "emp" if empiryczny else "", rec, flush=True)
        if ok.all() or (ok | zamr).all():
            break
    return {"El": El, "Eh": Eh, "dowiedzione": dow, "zamrozone": zamr, "historia": hist, "operacje_par": ops,
            "polszer_stan": (scale * np.maximum(np.abs(El), np.abs(Eh))) if poziom != "D1" else (Eh - El) / 2}
