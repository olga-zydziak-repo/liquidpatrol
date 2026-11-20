#!/usr/bin/env python3
"""results/ARKUSZ_RECON/tools/ar_r3k.py — R3 lemat arkusza k = 10 i 20, szczeble D2/D3 (PROMPT_ARKUSZ_S0 §5; 0 bootów).

Próba komórek źródłowych (odchylenie: nie wszystkie komórki): 200 jednostajnie po komórkach i 200 z wagą czasu pobytu (rng 555).
Zmienne: s_0 ∈ c (6), reszta e ∈ E_c (20; D3: h = Φ_c(s_0) + T_c e), wejścia s_1..s_k niezależnie w S_j = (c ⊕ jΔ) ∩ obwiednia
dziedziny (nadzbiór wejść dopuszczalnych: pomija sprzężenie kolejnych kroków i zajętość komórek pośrednich).
Forma Taylora 1. rzędu składana krok po kroku: wartość w środku z0 liczona dokładnie, jakobian przedziałowy J_j = M_j·(Wh^T J_{j−1}
+ Wx^T ∂xn/∂s_j) (M_j = ∂h′/∂u na pudełku U_j), obwiednia H_j = h_j(z0) ± (|Jc| + Jr)·r przecięta z naturalnym rozszerzeniem.
Komórki docelowe c′: zajęte, przecinające S_k; s_k ograniczone do S_k ∩ c′; reszta G = h_k − Φ_c′(s_k) (D3: T_c′^{-1} G) wobec
zbioru startowego E_c′ (obwiednia danych +10% + 1e-3, jak w ar_r3_bieg). Test poprawności: 10⁶ punktów (20 komórek
× 50 000 trajektorii): obwiednia h_k i reszta G wobec komórki końcowej c′ (gdy zajęta) w ograniczeniu z sprawdz().
"""
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ar_wspolne as AW                                  # noqa: E402
import ar_r3 as R                                        # noqa: E402

OUT = AW.OUT


def jxs(Sl, Sh):
    xl, xh, Jl, Jh = R.x_box(Sl, Sh)
    Pc = R.WX.T[None] @ ((Jl + Jh) / 2); Pr = R.WXa.T[None] @ ((Jh - Jl) / 2)
    return xl, xh, Pc, Pr


def lancuch(Dz, c, k, El, Eh, poziom, dom_lo, dom_hi):
    """Taylor przez k kroków dla jednej komórki źródłowej. Zwraca (h_k(z0), Jc, Jr, r, z0-bloki, S_k)."""
    T = Dz.T[c] if poziom == "D3" else np.eye(20)
    nv = 6 + 20 + 6 * k
    r = np.zeros(nv); r[:6] = Dz.w[c]; r[6:26] = (Eh[c] - El[c]) / 2
    e0 = (El[c] + Eh[c]) / 2
    hc = Dz.phi[c] + T @ e0
    Jc = np.zeros((20, nv)); Jr = np.zeros((20, nv))
    Jc[:, :6] = Dz.A[c]; Jc[:, 6:26] = T
    D = Dz.delta
    Hl = hc - (np.abs(Jc) @ r); Hh = hc + (np.abs(Jc) @ r)
    for j in range(1, k + 1):
        Sl = np.maximum(Dz.sc[c] - Dz.w[c] - j * D, dom_lo); Sh = np.minimum(Dz.sc[c] + Dz.w[c] + j * D, dom_hi)
        sj = (Sl + Sh) / 2
        cols = slice(26 + 6 * (j - 1), 26 + 6 * j)
        r[cols] = (Sh - Sl) / 2
        xl, xh, Pc, Pr = jxs(Sl[None], Sh[None])
        a = R.imv(xl, xh, R.WX, R.WXa); b = R.imv(Hl[None], Hh[None], R.WH_, R.WHa)
        Fl, Fh, Ml, Mh = R.F_box(a[0] + b[0] + R.B0, a[1] + b[1] + R.B0)
        x0 = AW.norm(AW.cechy(np.r_[sj, R.WIEK][None]))
        hc = AW.F(x0, hc[None])[0]
        # P = Wh^T J_{j−1} (+ Wx^T Jx w kolumnach s_j)
        Pc_all = R.WH_.T @ Jc; Pr_all = R.WHa.T @ Jr
        Pc_all[:, cols] += Pc[0]; Pr_all[:, cols] += Pr[0]
        Mc, Mr = (Ml[0] + Mh[0]) / 2, (Mh[0] - Ml[0]) / 2
        Jc, Jr = Mc @ Pc_all, np.abs(Mc) @ Pr_all + Mr @ np.abs(Pc_all) + Mr @ Pr_all + R.PAD
        rad = (np.abs(Jc) + Jr) @ r
        Hl, Hh = np.maximum(hc - rad, Fl[0]), np.minimum(hc + rad, Fh[0])
    return hc, Jc, Jr, r, Sl, Sh


def cele(Dz, Sl, Sh):
    """Komórki zajęte przecinające S_k (θ z przesunięciem najbliżej środka S_k)."""
    lo4, hi4 = Dz.sc[:, :4] - Dz.w[:, :4], Dz.sc[:, :4] + Dz.w[:, :4]
    th = Dz.sc[:, 1] + 0 * Sl[1]
    sh = AW.wrap(th - (Sl[1] + Sh[1]) / 2) + (Sl[1] + Sh[1]) / 2
    lo4 = lo4.copy(); hi4 = hi4.copy(); lo4[:, 1] = sh - Dz.w[:, 1]; hi4[:, 1] = sh + Dz.w[:, 1]
    ok = ((lo4 <= Sh[:4]) & (hi4 >= Sl[:4])).all(1)
    return np.where(ok)[0], sh


def sprawdz(Dz, c, k, El, Eh, poziom, dom_lo, dom_hi):
    hc, Jc, Jr, r, Sl, Sh = lancuch(Dz, c, k, El, Eh, poziom, dom_lo, dom_hi)
    cel, sh = cele(Dz, Sl, Sh)
    cs = slice(len(r) - 6, len(r))
    rad_inne = ((np.abs(Jc) + Jr)[:, :cs.start] @ r[:cs.start])
    sk0 = (Sl + Sh) / 2
    scd = Dz.sc[cel].copy(); scd[:, 1] = sh[cel]
    lo = np.maximum(Sl, scd - Dz.w[cel]); hi = np.minimum(Sh, scd + Dz.w[cel])
    sp0, rp = (lo + hi) / 2, (hi - lo) / 2
    dlt = sp0 - sk0
    Jsc, Jsr = Jc[:, cs], Jr[:, cs]
    C = hc[None] + dlt @ Jsc.T - Dz.Phi(cel, sp0, scd)
    Jd = Jsc[None] - Dz.A[cel]
    rad = rad_inne[None] + np.abs(dlt) @ Jsr.T + np.einsum("phj,pj->ph", np.abs(Jd) + Jsr[None], rp)
    if poziom == "D3":
        Ti = Dz.Ti[cel]
        C = np.einsum("phj,pj->ph", Ti, C); rad = np.einsum("phj,pj->ph", np.abs(Ti), rad)
    glo, ghi = C - rad, C + rad
    ok = (glo >= El[cel]).all(1) & (ghi <= Eh[cel]).all(1)
    return cel, ok, np.abs(rad).max(1), (glo, ghi, scd)


def test(Dz, cs, k, El, Eh, poziom, dom_lo, dom_hi, rng, n_traj=50000):
    """Punkty losowe: trajektorie s_0 ~ U(c), e ~ U(E_c), s_j ~ U(S_j); (1) h_k w obwiedni Taylora, (2) reszta G wobec c′ = komórki s_k
    (gdy zajęta) w ograniczeniu z sprawdz()."""
    wyj, wyjG, n, nG = 0, 0, 0, 0
    for c in cs:
        hc, Jc, Jr, r, _, _ = lancuch(Dz, c, k, El, Eh, poziom, dom_lo, dom_hi)
        cel, ok, _, (glo, ghi, scd) = sprawdz(Dz, c, k, El, Eh, poziom, dom_lo, dom_hi)
        poz = {int(ci): i for i, ci in enumerate(cel)}
        T = Dz.T[c] if poziom == "D3" else np.eye(20)
        rad = (np.abs(Jc) + Jr) @ r
        s0 = Dz.sc[c] + Dz.w[c] * rng.uniform(-1, 1, (n_traj, 6))
        e = El[c] + (Eh[c] - El[c]) * rng.uniform(0, 1, (n_traj, 20))
        h = Dz.phi[c] + (s0 - Dz.sc[c]) @ Dz.A[c].T + e @ T.T
        for j in range(1, k + 1):
            Sl = np.maximum(Dz.sc[c] - Dz.w[c] - j * Dz.delta, dom_lo); Sh = np.minimum(Dz.sc[c] + Dz.w[c] + j * Dz.delta, dom_hi)
            s = Sl + (Sh - Sl) * rng.uniform(0, 1, (n_traj, 6))
            h = AW.F(AW.norm(AW.cechy(np.c_[s, np.full(n_traj, R.WIEK)])), h)
        wyj += int(((h < hc - rad) | (h > hc + rad)).sum()); n += n_traj
        kod = Dz.g.kod(Dz.g.klucze(np.c_[s, np.full(n_traj, R.WIEK)]))
        pos = np.minimum(np.searchsorted(Dz.uk, kod), Dz.nc - 1)
        m = (Dz.uk[pos] == kod) & np.isin(pos, cel)
        if m.any():
            ii = np.array([poz[int(q)] for q in pos[m]])
            ss = s[m].copy(); ss[:, 1] = scd[ii, 1] + AW.wrap(ss[:, 1] - scd[ii, 1])
            G = h[m] - Dz.Phi(pos[m], ss, scd[ii])
            if poziom == "D3":
                G = np.einsum("phj,pj->ph", Dz.Ti[pos[m]], G)
            wyjG += int(((G < glo[ii]) | (G > ghi[ii])).sum()); nG += int(m.sum())
    return {"punkty": n, "wyjatki_obwiedni_hk": wyj, "punkty_reszty": nG, "wyjatki_reszty": wyjG, "zdany": wyj == 0 and wyjG == 0}


if __name__ == "__main__":
    import pickle
    fn = os.path.join(OUT, "r3k.json")
    wyn = json.load(open(fn)) if os.path.exists(fn) else {}
    pk = sys.argv[1]
    Dz = pickle.load(open(pk, "rb"))
    ci = Dz.cel_stanu
    def hull(v):
        L = np.full((Dz.nc, 20), np.inf); H = np.full((Dz.nc, 20), -np.inf)
        np.minimum.at(L, ci, v); np.maximum.at(H, ci, v)
        w = H - L
        return {"El": L - 0.1 * w - 1e-3, "Eh": H + 0.1 * w + 1e-3}
    z = {"D2": hull(Dz.e_dane), "D3": hull(np.einsum("phj,pj->ph", Dz.Ti[ci], Dz.e_dane))}
    dom_lo = np.r_[Dz.sc[:, :4].min(0) - Dz.w[0, :4], Dz.rz[0], Dz.vd[0]]
    dom_hi = np.r_[Dz.sc[:, :4].max(0) + Dz.w[0, :4], Dz.rz[1], Dz.vd[1]]
    rng = np.random.default_rng(555)
    p_ = Dz.ile / Dz.ile.sum()
    proba = {"jednostajna": rng.choice(Dz.nc, 200, replace=False), "czas": rng.choice(Dz.nc, 200, replace=False, p=p_)}
    for poziom in ("D2", "D3"):
        El, Eh = z[poziom]["El"], z[poziom]["Eh"]
        for k in (1, 10, 20):
            a = time.time()
            o = {}
            for nm, cs in proba.items():
                n_ok_src, n_par, n_par_ok, radmed = 0, 0, 0, []
                for c in cs:
                    cel, ok, rad, _ = sprawdz(Dz, c, k, El, Eh, poziom, dom_lo, dom_hi)
                    n_ok_src += int(ok.all()); n_par += len(ok); n_par_ok += int(ok.sum()); radmed.append(np.median(rad))
                o[nm] = {"zrodla": len(cs), "zrodla_wszystkie_cele_ok": n_ok_src, "pary": n_par, "pary_ok": n_par_ok,
                         "polszer_ograniczenia_reszty_mediana": float(np.median(radmed)), "max_mediana": float(np.max(radmed))}
            o["test"] = test(Dz, proba["jednostajna"][:20], k, El, Eh, poziom, dom_lo, dom_hi, np.random.default_rng(77 + k))
            o["czas_s"] = time.time() - a
            wyn[f"{poziom}_k{k}"] = o
            print(poziom, k, o, flush=True)
            json.dump(wyn, open(fn, "w"), ensure_ascii=False, indent=1)
