#!/usr/bin/env python3
"""results/PETLA_RECON/tools/pl_r7.py — R7: wykonalność dowodu zdania S arytmetyką przedziałową (PROMPT_PETLA_S0 §9; ≤ 30 min).

Zdanie S: dla dystansu z cech d ∈ [10.5, 13.0] m, dowolnego namiaru φ, prędkości poziomej |v_h| ≤ 3.2 m/s, rel_z ∈ [0, 4] m,
|own_vd| ≤ 1 m/s, wieku tracka ∈ [0, 0.15] s (track ważny) i stanu sieci h ∈ Ω: składowa komendy ku celowi ≥ 0.5 m/s.
Komenda = clip_v(tanh(·)·3) (common.py:10-16); kierunek ku celowi = (cos φ, sin φ); clip_v skaluje wektor ⇒ ku_clip ≥
min(ku_raw, ku_raw·3/|y|) przy ku_raw > 0 (dolne ograniczenie przedziałowe).
Wejście parametryzowane w ramie celu: (d, φ, v_r, v_t, rel_z, own_vd, age) + stan; v_n, v_e = v_r·u + v_t·t; |v_h| ≤ 3.2
nadpisane pudełkiem v_r, v_t ∈ [−3.2, 3.2] (nadzbiór — konserwatywne); v_t dzielone na znak (komórki Ω3).
Opisy Ω (ze stanów lotów misji z R2 i stanów biegów R5 — wariant W, 7 rodzin, napęd N, szum, próbkowanie co 20 ticków):
  Ω1 — pudełko p1–p99 per neuron;  Ω2 — pudełko w osiach PCA (8 pierwszych p1–p99, reszta |z| ≤ max obserwowane),
  h = μ + V·z (przedziałowo: środek ± |V|·promień);  Ω3 — per komórka (16 sektorów namiaru × znak v_t) pudełko min–max
  powiększone o 10 % szerokości.
Certyfikacja: kolejka bisekcji per sektor (budżet 20 000 komórek), podział wymiaru o największej szerokości względnej (wejście
i współrzędne stanu); komórka certyfikowana, gdy dolne ograniczenie ku ≥ 0.5. Udział objętości = suma objętości (względnych)
certyfikowanych. Próbkowanie: 10⁵ punktów losowych jednostajnie z każdego Ω (wejście i stan), liczba łamiących S, 10 najgorszych.
Wyjście: results/PETLA_RECON/r7.json, r7_stany.npz, r7_najgorsze_<Ω>.npy.
"""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pl_siec as PS                                     # noqa: E402
import pl_r2b as R2B                                     # noqa: E402

OUT = os.path.join(PS.ROOT, "results/PETLA_RECON")
M = PS.M
DLO, VH, RZ, VD = (10.5, 13.0), 3.2, (0.0, 4.0), (-1.0, 1.0)
PROG = 0.5
BUDZET = 20000
NSEK = 16


def stany():
    fn = os.path.join(OUT, "r7_stany.npz")
    if os.path.exists(fn):
        z = np.load(fn)
        return z["X"], z["H"], z["zrodlo"]
    W = dict(np.load(os.path.join(OUT, "r2_wektory.npz"), allow_pickle=True))
    hp = R2B.h_prev(W)
    m = W["misja"].astype(bool)
    X, H = [W["x"][m]], [hp[m]]
    import pl_bieg as PB
    import pl_intruz as PI
    for i, r in enumerate(PI.RODZINY):
        res = PB.bieg(r, "N", True, 1.0, wariant="W", B=200, ziarno=900000 + i, zbierz=20)
        X.append(res["stany_x"]); H.append(res["stany_h"])
    zr = np.r_[np.zeros(len(X[0])), np.ones(sum(len(x) for x in X[1:]))]
    X, H = np.concatenate(X), np.concatenate(H)
    np.savez_compressed(fn, X=X, H=H, zrodlo=zr)
    return X, H, zr


def komorka(X):
    phi = np.arctan2(X[:, 1], X[:, 0])
    sek = ((phi + np.pi) / (2 * np.pi) * NSEK).astype(int) % NSEK
    u = np.stack([np.cos(phi), np.sin(phi)], 1)
    vt = -u[:, 1] * X[:, 3] + u[:, 0] * X[:, 4]
    return sek, (vt >= 0).astype(int)


# ---------- arytmetyka przedziałowa
def _lin(lo, hi, W, b):
    c, r = (lo + hi) / 2, (hi - lo) / 2
    cc = c @ W + b
    rr = r @ np.abs(W)
    return cc - rr, cc + rr


def _cosI(a, b):
    """Przedział cos na [a, b] (b − a ≤ 2π)."""
    lo, hi = np.minimum(np.cos(a), np.cos(b)), np.maximum(np.cos(a), np.cos(b))
    k0 = np.ceil(a / np.pi); k1 = np.floor(b / np.pi)
    for k in range(-3, 4):
        s = (k >= k0) & (k <= k1)
        if k % 2 == 0:
            hi = np.where(s, 1.0, hi)
        else:
            lo = np.where(s, -1.0, lo)
    return lo, hi


def _mul(al, ah, bl, bh):
    c = np.stack([al * bl, al * bh, ah * bl, ah * bh])
    return c.min(0), c.max(0)


def ku_dolne(B):
    """B: (n, 7 + 2·H?) — tu słownik przedziałów: d, phi, vr, vt, rz, vd, age (lo, hi) i h (lo, hi) (n, H). Zwraca dolne ku."""
    cl, ch = _cosI(B["phi"][0], B["phi"][1])
    sl, sh = _cosI(B["phi"][0] - np.pi / 2, B["phi"][1] - np.pi / 2)
    rx = _mul(B["d"][0], B["d"][1], cl, ch); ry = _mul(B["d"][0], B["d"][1], sl, sh)
    # v = vr·u + vt·t, t = (−sin, cos)
    a1 = _mul(B["vr"][0], B["vr"][1], cl, ch); a2 = _mul(B["vt"][0], B["vt"][1], -sh, -sl)
    vn = (a1[0] + a2[0], a1[1] + a2[1])
    b1 = _mul(B["vr"][0], B["vr"][1], sl, sh); b2 = _mul(B["vt"][0], B["vt"][1], cl, ch)
    ve = (b1[0] + b2[0], b1[1] + b2[1])
    xl = np.stack([rx[0], ry[0], B["rz"][0], vn[0], ve[0], B["vd"][0], B["age"][0], np.ones_like(rx[0])], 1)
    xh = np.stack([rx[1], ry[1], B["rz"][1], vn[1], ve[1], B["vd"][1], B["age"][1], np.ones_like(rx[0])], 1)
    xl, xh = (xl - PS.MEAN) / PS.STD, (xh - PS.MEAN) / PS.STD
    lo, hi = np.concatenate([xl, B["h"][0]], 1), np.concatenate([xh, B["h"][1]], 1)
    zl, zh = _lin(lo, hi, M.Wb, M.bb0); bl, bh = np.tanh(zl), np.tanh(zh)
    gl, gh = [np.tanh(v) for v in _lin(bl, bh, M.Wg, M.bg)]
    hl, hh = [np.tanh(v) for v in _lin(bl, bh, M.Wh, M.bh)]
    tl, th = [1 / (1 + np.exp(-v)) for v in _lin(bl, bh, M.Wt, M.bt)]
    # h2 = gate·g + (1−gate)·hh = hh + gate·(g − hh)
    dl, dh = gl - hh, gh - hl
    p = _mul(tl, th, dl, dh)
    h2l, h2h = hl + p[0], hh + p[1]
    ol, oh = _lin(h2l, h2h, M.Wo, M.bo)
    yl, yh = np.tanh(ol) * 3.0, np.tanh(oh) * 3.0
    kx = _mul(yl[:, 0], yh[:, 0], cl, ch); ky = _mul(yl[:, 1], yh[:, 1], sl, sh)
    kul = kx[0] + ky[0]
    ny = np.sqrt((np.maximum(np.abs(yl), np.abs(yh)) ** 2).sum(1))
    return np.where(kul > 0, np.minimum(kul, kul * 3.0 / np.maximum(ny, 3.0)), kul)


def ku_punkt(P):
    """P: słownik wartości punktowych (n,) i h (n, H). Zwraca ku po clip_v."""
    u = np.stack([np.cos(P["phi"]), np.sin(P["phi"])], 1)
    t = np.stack([-u[:, 1], u[:, 0]], 1)
    v = P["vr"][:, None] * u + P["vt"][:, None] * t
    x = np.stack([P["d"] * u[:, 0], P["d"] * u[:, 1], P["rz"], v[:, 0], v[:, 1], P["vd"], P["age"], np.ones_like(P["d"])], 1)
    y, _ = PS.krok(PS.norm(x), P["h"])
    return (y[:, :2] * u).sum(1), x


class Omega:
    def __init__(self, typ, X, H):
        self.typ = typ
        if typ == "O1":
            self.lo, self.hi = np.percentile(H, 1, 0), np.percentile(H, 99, 0)
        elif typ == "O2":
            self.mu = H.mean(0)
            ev, V = np.linalg.eigh(np.cov(H.T)); V = V[:, ::-1]
            Z = (H - self.mu) @ V
            self.V = V
            self.zlo, self.zhi = np.percentile(Z, 1, 0), np.percentile(Z, 99, 0)
            m = np.abs(Z).max(0)
            self.zlo[8:], self.zhi[8:] = -m[8:], m[8:]
        else:
            sek, zn = komorka(X)
            self.cel = {}
            for s in range(NSEK):
                for z in (0, 1):
                    sel = (sek == s) & (zn == z)
                    Hs = H[sel] if sel.sum() >= 5 else H
                    lo, hi = Hs.min(0), Hs.max(0)
                    w = hi - lo
                    self.cel[(s, z)] = (lo - 0.05 * w, hi + 0.05 * w, int(sel.sum()))

    def wym(self, s, z):
        """Przedziały współrzędnych stanu (lo, hi) w przestrzeni bisekcji."""
        if self.typ == "O1":
            return self.lo.copy(), self.hi.copy()
        if self.typ == "O2":
            return self.zlo.copy(), self.zhi.copy()
        lo, hi, _ = self.cel[(s, z)]
        return lo.copy(), hi.copy()

    def h_przedzial(self, lo, hi):
        if self.typ == "O2":
            c, r = (lo + hi) / 2, (hi - lo) / 2
            hc = self.mu + c @ self.V.T
            hr = r @ np.abs(self.V.T)
            return hc - hr, hc + hr
        return lo, hi

    def h_punkt(self, z):
        return self.mu + z @ self.V.T if self.typ == "O2" else z


WEJ = ("d", "phi", "vr", "vt", "rz", "vd", "age")


def certyfikuj(Om, s, zn, budzet=BUDZET):
    a0 = -np.pi + 2 * np.pi * s / NSEK
    base_lo = np.array([DLO[0], a0, -VH, 0.0 if zn else -VH, RZ[0], VD[0], 0.0])
    base_hi = np.array([DLO[1], a0 + 2 * np.pi / NSEK, VH, VH if zn else 0.0, RZ[1], VD[1], 0.15])
    hlo, hhi = Om.wym(s, zn)
    LO, HI = np.concatenate([base_lo, hlo])[None], np.concatenate([base_hi, hhi])[None]
    W0 = HI[0] - LO[0]
    W0[W0 <= 0] = 1.0
    vol, uzyte, cert = np.ones(1), 0, 0.0
    while len(LO) and uzyte < budzet:
        nb = min(len(LO), budzet - uzyte)
        lo, hi, vv = LO[:nb], HI[:nb], vol[:nb]
        LO, HI, vol = LO[nb:], HI[nb:], vol[nb:]
        uzyte += nb
        hl, hh = Om.h_przedzial(lo[:, 7:], hi[:, 7:])
        B = {k: (lo[:, i], hi[:, i]) for i, k in enumerate(WEJ)}
        B["h"] = (hl, hh)
        kl = ku_dolne(B)
        ok = kl >= PROG
        cert += vv[ok].sum()
        lo, hi, vv = lo[~ok], hi[~ok], vv[~ok]
        if not len(lo):
            continue
        j = np.argmax((hi - lo) / W0, 1)
        mid = (lo[np.arange(len(lo)), j] + hi[np.arange(len(lo)), j]) / 2
        l2, h1 = lo.copy(), hi.copy()
        h1[np.arange(len(lo)), j] = mid; l2[np.arange(len(lo)), j] = mid
        LO = np.concatenate([LO, lo, l2]); HI = np.concatenate([HI, h1, hi]); vol = np.concatenate([vol, vv / 2, vv / 2])
    return float(cert), uzyte


def probki(Om, n, rng):
    s = rng.integers(0, NSEK, n); zn = rng.integers(0, 2, n)
    P = {"d": rng.uniform(*DLO, n), "phi": -np.pi + 2 * np.pi * (s + rng.uniform(0, 1, n)) / NSEK,
         "vr": rng.uniform(-VH, VH, n), "vt": rng.uniform(0, VH, n) * np.where(zn == 1, 1, -1), "rz": rng.uniform(*RZ, n),
         "vd": rng.uniform(*VD, n), "age": rng.uniform(0, 0.15, n)}
    Hs = np.zeros((n, PS.H))
    for (ss, zz) in {(int(a), int(b)) for a, b in zip(s, zn)}:
        sel = (s == ss) & (zn == zz)
        lo, hi = Om.wym(ss, zz)
        z = lo + (hi - lo) * rng.uniform(0, 1, (sel.sum(), len(lo)))
        Hs[sel] = Om.h_punkt(z)
    P["h"] = Hs
    ku, x = ku_punkt(P)
    return ku, x, Hs


def main():
    t0 = time.time()
    X, H, zr = stany()
    out = {"n_stanow": int(len(X)), "z_lotow": int((zr == 0).sum()), "z_R5": int((zr == 1).sum()), "omega": {}}
    rng = np.random.default_rng(7)
    for typ in ("O1", "O2", "O3"):
        a = time.time()
        Om = Omega(typ, X, H)
        cert = []
        for s in range(NSEK):
            for zn in (0, 1):
                c, u = certyfikuj(Om, s, zn, BUDZET // 2)          # 20 000 na sektor = 2 × 10 000 (znak v_t)
                cert.append({"sektor": s, "znak_vt": zn, "udzial": c, "komorek": u})
        ku, x, Hs = probki(Om, 100000, rng)
        zle = ku < PROG
        o = np.argsort(ku)[:10]
        np.save(os.path.join(OUT, f"r7_najgorsze_{typ}.npy"), np.concatenate([ku[o, None], x[o], Hs[o]], 1))
        out["omega"][typ] = {"udzial_certyfikowany": float(np.mean([c["udzial"] for c in cert])), "per_komorka": cert,
                             "czas_s": round(time.time() - a, 1), "probki": 100000, "lamiace": int(zle.sum()),
                             "ku_min": float(ku.min()), "najgorsze_ku": [float(v) for v in ku[o]]}
        if typ == "O3":
            out["omega"][typ]["stany_w_komorkach"] = {f"{k[0]},{k[1]}": v[2] for k, v in Om.cel.items()}
        print(typ, out["omega"][typ]["udzial_certyfikowany"], out["omega"][typ]["lamiace"], out["omega"][typ]["czas_s"], flush=True)
        json.dump(out, open(os.path.join(OUT, "r7.json"), "w"), ensure_ascii=False, indent=1)
    out["czas_calosc_s"] = round(time.time() - t0, 1)
    json.dump(out, open(os.path.join(OUT, "r7.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
