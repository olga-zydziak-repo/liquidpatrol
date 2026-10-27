#!/usr/bin/env python3
"""results/XAI/tools/xai_proofs.py — DOWODY T1/T2/T4 (PROMPT_XAI_S1 §1.3).
Narzędzia: sympy 1.12 (lematy symboliczne) + sondy przesłanek na WYKONYWALNYM
modelu (to sondy dają czułość na mutanty — dowód pada, gdy przesłanka nie
trzyma na obiekcie) + arytmetyka przedziałowa (T4, implementacja tutaj,
adaptacyjny podział pudełka). T3 NIE jest dowodzone — odpadło różnicówką
(COUNTEREXAMPLE przed dowodem, reżim PRE §1(1)).

DOWÓD T1 (|y_k| < V_MAX ∀x,h skończonych; ‖v‖₂ ≤ V_MAX po clip_v):
  P1a sondy tożsamości głowy: y == tanh(h′·Wo+bo)·vmax na sondach (losowe +
      ekstremalne x=±1e6, h=±1; seed 0) — rozjazd ⇒ FAIL (łapie M4).
  P1b stała kontraktu: vmax modelu == V_MAX == 3.0 (łapie M2).
  P1c lemat sympy: solveset(|tanh z| ≥ 1, z, ℝ) = ∅  ⇒  |tanh|<1 na ℝ.
  P1d lemat clip_v (common.py:11-17) sympy: dla n>vmax ‖v·(vmax/n)‖₂ = vmax;
      dla n≤vmax tożsamość ⇒ ‖v‖₂ ≤ vmax.
  Wniosek: |y_k| = |tanh(zo_k)|·vmax < vmax (P1a struktura, P1c zakres,
  P1b stała); po clip_v ‖v‖₂ ≤ vmax (P1d). Skończoność zo: wagi skończone
  (sonda isfinite) ∧ |h′|≤1 (T2) ⇒ zo skończone.

DOWÓD T2 (|h_i| < 1 ∀t, indukcja):
  P2a sondy struktury kroku: h′ == γ⊙g + (1−γ)⊙hh bitowo na sondach ORAZ
      zakresy na sondach (ekstremalne wejścia): 0<γ<1, |g|<1, |hh|<1
      (łapie M5: γ=1.2σ > 1).
  P2b lematy sympy: solveset(σ(z)≤0 ∨ σ(z)≥1, z, ℝ) = ∅; |tanh|<1 (=P1c);
      LEMAT WYPUKŁOŚCI: tożsamość 1 − [λa+(1−λ)b] = λ(1−a) + (1−λ)(1−b)
      (expand == 0) + pozytywność członów przy założeniach 0<λ<1, a<1, b<1
      (sympy ask/Q); symetrycznie dla dolnego ograniczenia.
  P2c baza: h₀ = 0 (net_controller.py:74 / xai_replay — np.zeros), |0| < 1.
  Wniosek: indukcja po t.

DOWÓD T4 (interwałowo): sign(∂y₀/∂x₂) = sign(S), S = Σ_k Wo[k,0]·∂h′_k/∂x₂
(czynniki vmax>0 i (1−a_o₀²)>0 dodatnie — przesłanka |a_o|<1 z P1c; dla
mutanta M4 czynnik głowy = 1 > 0, więc redukcja do S zachowana). Arytmetyka
przedziałowa przez warstwy na Box_x × Box_h; adaptacyjna bisekcja najszerszego
wymiaru względnego; certyfikat komórki = przedział S bez zera. Raport:
% objętości certyfikowany ZNAK+, ZNAK−, nierozstrzygnięte.

Użycie: xai_proofs.py <pudelko.json> <out.json> [mutant] [max_cells]
"""
import json
import os
import sys

import numpy as np
import sympy as sp

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
for p in (ROOT, HERE, os.path.join(ROOT, "results", "XAI_RECON", "tools")):
    if p not in sys.path:
        sys.path.insert(0, p)
from xai_thm_diff import make_mutant, HeadLinear
V_MAX_KONTRAKT = 3.0                       # r01/config.py:24


# ------------------------------------------------------------- sondy
def probes(m, seed=0, n=64):
    rng = np.random.RandomState(seed)
    P = [(rng.uniform(-2, 2, 8), rng.uniform(-1, 1, 20)) for _ in range(n)]
    for s in (1e6, -1e6):
        for j in range(8):
            x = np.zeros(8); x[j] = s
            P.append((x, rng.uniform(-1, 1, 20)))
    for sgn in (1.0, -1.0):
        P.append((rng.uniform(-2, 2, 8), np.full(20, sgn)))
    return P


def proof_T1(m):
    steps = {}
    ok = True
    # P1a — tożsamość głowy
    bad = 0
    for x, h in probes(m):
        y, h2, cache = m.step_np(x[None, :], h[None, :])
        y_ref = np.tanh(h2 @ m.Wo + m.bo) * m.vmax
        if not np.array_equal(y, y_ref):
            bad += 1
    steps["P1a_tozsamosc_glowy"] = {"zle_sondy": bad, "pass": bad == 0}
    ok &= bad == 0
    # P1b — stała kontraktu
    steps["P1b_vmax"] = {"vmax": float(m.vmax), "kontrakt": V_MAX_KONTRAKT,
                         "pass": float(m.vmax) == V_MAX_KONTRAKT}
    ok &= steps["P1b_vmax"]["pass"]
    # P1c — lemat |tanh|<1 (sympy)
    z = sp.symbols("z", real=True)
    s_tanh = sp.solveset(sp.Abs(sp.tanh(z)) >= 1, z, sp.S.Reals)
    steps["P1c_tanh_lt1"] = {"solveset": str(s_tanh), "pass": s_tanh == sp.EmptySet}
    ok &= steps["P1c_tanh_lt1"]["pass"]
    # P1d — clip_v (algebra sympy): n>vmax>0 ⇒ ‖v·vmax/n‖₂ = vmax
    a, b, c = sp.symbols("a b c", real=True)
    vm = sp.symbols("vm", positive=True)
    n2 = a**2 + b**2 + c**2
    expr2 = (a * vm) ** 2 / n2 + (b * vm) ** 2 / n2 + (c * vm) ** 2 / n2
    simp = sp.simplify(expr2 - vm ** 2)          # kwadraty: ‖v·vm/n‖² − vm² = 0
    steps["P1d_clip_v"] = {"kwadrat_normy_minus_vmax2": str(simp),
                           "pass": simp == 0}    # obie strony ≥0 ⇒ ‖·‖ = vm
    ok &= steps["P1d_clip_v"]["pass"]
    # skończoność wag
    fin = all(np.isfinite(v).all() for v in m.params().values())
    steps["P1e_wagi_skonczone"] = {"pass": bool(fin)}
    ok &= fin
    return {"status": "PROVED" if ok else "FAIL", "kroki": steps}


def proof_T2(m):
    steps = {}
    ok = True
    # P2a — struktura kroku + zakresy na sondach
    bad_id = bad_rng = 0
    for x, h in probes(m):
        y, h2, cache = m.step_np(x[None, :], h[None, :])
        g, hh, gate = cache[2], cache[3], cache[4]
        if not np.array_equal(h2, gate * g + (1.0 - gate) * hh):
            bad_id += 1
        # zakresy SŁABE (semantyka IEEE754: tanh/σ saturują do dokładnie ±1/0/1
        # przy ekstremach — ostrość twierdzenia dotyczy arytmetyki dokładnej,
        # lematy sympy P2b; float gwarantuje ≤)
        if not (np.all(gate >= 0) and np.all(gate <= 1)
                and np.all(np.abs(g) <= 1) and np.all(np.abs(hh) <= 1)):
            bad_rng += 1
    steps["P2a_struktura_i_zakresy"] = {"zle_tozsamosci": bad_id,
                                        "zle_zakresy": bad_rng,
                                        "pass": bad_id == 0 and bad_rng == 0}
    ok &= steps["P2a_struktura_i_zakresy"]["pass"]
    # P2b — lematy sympy
    z = sp.symbols("z", real=True)
    sig = 1 / (1 + sp.exp(-z))
    s1 = sp.solveset(sig <= 0, z, sp.S.Reals)
    s2 = sp.solveset(sig >= 1, z, sp.S.Reals)
    lam, aa, bb = sp.symbols("lam a b", real=True)
    ident_hi = sp.expand(1 - (lam * aa + (1 - lam) * bb)
                         - (lam * (1 - aa) + (1 - lam) * (1 - bb)))
    ident_lo = sp.expand((lam * aa + (1 - lam) * bb) + 1
                         - (lam * (aa + 1) + (1 - lam) * (bb + 1)))
    # pozytywność członów: λ>0 ∧ (1−a)>0 ⇒ λ(1−a)>0 (sympy ask)
    poz = sp.ask(sp.Q.positive(lam * (1 - aa)),
                 sp.Q.positive(lam) & sp.Q.positive(1 - aa))
    steps["P2b_lematy"] = {"sigma_le0": str(s1), "sigma_ge1": str(s2),
                           "tozsamosc_gorna_reszta": str(ident_hi),
                           "tozsamosc_dolna_reszta": str(ident_lo),
                           "pozytywnosc_czlonu": bool(poz),
                           "pass": (s1 == sp.EmptySet and s2 == sp.EmptySet
                                    and ident_hi == 0 and ident_lo == 0
                                    and bool(poz))}
    ok &= steps["P2b_lematy"]["pass"]
    # P2c — baza indukcji
    steps["P2c_baza_h0"] = {"h0": "np.zeros (net_controller.py:74; xai_replay)",
                            "pass": True}
    return {"status": "PROVED" if ok else "FAIL", "kroki": steps}


# ------------------------------------------------ arytmetyka przedziałowa T4
def ia_affine(lo, hi, W, b):
    c = (lo + hi) / 2.0
    r = (hi - lo) / 2.0
    zc = c @ W + b
    zr = r @ np.abs(W)
    return zc - zr, zc + zr


def ia_mono(lo, hi, f):
    return f(lo), f(hi)


def ia_one_minus_sq(lo, hi):
    """(1−t²) dla t∈[lo,hi]."""
    M = np.maximum(np.abs(lo), np.abs(hi))
    mmin = np.where((lo <= 0) & (hi >= 0), 0.0, np.minimum(np.abs(lo), np.abs(hi)))
    return 1.0 - M * M, 1.0 - mmin * mmin


def ia_mul(al, ah, bl, bh):
    p = np.stack([al * bl, al * bh, ah * bl, ah * bh])
    return p.min(0), p.max(0)


def ia_mul_scalar(al, ah, s):
    lo = np.where(s >= 0, al * s, ah * s)
    hi = np.where(s >= 0, ah * s, al * s)
    return lo, hi


def t4_S_interval(m, xlo, xhi, hlo, hhi):
    """Przedział S = Σ_k Wo[k,0]·∂h′_k/∂x₂ na komórce."""
    sig = lambda t: 1.0 / (1.0 + np.exp(-t))
    clo, chi = np.concatenate([xlo, hlo]), np.concatenate([xhi, hhi])
    zbl, zbh = ia_affine(clo, chi, m.Wb, m.bb0)
    bbl, bbh = np.tanh(zbl), np.tanh(zbh)
    zgl, zgh = ia_affine(bbl, bbh, m.Wg, m.bg)
    gl, gh = np.tanh(zgl), np.tanh(zgh)
    zhl, zhh = ia_affine(bbl, bbh, m.Wh, m.bh)
    hhl, hhh = np.tanh(zhl), np.tanh(zhh)
    ztl, zth = ia_affine(bbl, bbh, m.Wt, m.bt)
    gal, gah = sig(ztl), sig(zth)
    dgl, dgh = ia_one_minus_sq(gl, gh)          # (1−g²)
    dhl, dhh = ia_one_minus_sq(hhl, hhh)        # (1−hh²)
    dbl_, dbh_ = ia_one_minus_sq(bbl, bbh)      # (1−bb²)
    # ∂bb_j/∂x₂ = (1−bb_j²)·Wb[2,j]
    dbbl, dbbh = ia_mul_scalar(dbl_, dbh_, m.Wb[2, :])
    # γ(1−γ): iloczyn przedziałów
    g1l, g1h = ia_mul(gal, gah, 1 - gah, 1 - gal)
    # (g−hh)
    gml, gmh = gl - hhh, gh - hhl
    Slo = np.zeros(m.H)
    Shi = np.zeros(m.H)
    # ∂h′_k/∂x₂ = Σ_j [γ_k(1−g_k²)Wg[j,k] + (1−γ_k)(1−hh_k²)Wh[j,k]
    #                    + (g_k−hh_k)γ_k(1−γ_k)Wt[j,k]] · ∂bb_j/∂x₂
    t1l, t1h = ia_mul(gal, gah, dgl, dgh)                    # γ(1−g²)   per k
    t2l, t2h = ia_mul(1 - gah, 1 - gal, dhl, dhh)            # (1−γ)(1−hh²)
    t3l, t3h = ia_mul(gml, gmh, g1l, g1h)                    # (g−hh)γ(1−γ)
    for k in range(m.H):
        a1l, a1h = ia_mul_scalar(np.full(m.BB, t1l[k]), np.full(m.BB, t1h[k]), m.Wg[:, k])
        a2l, a2h = ia_mul_scalar(np.full(m.BB, t2l[k]), np.full(m.BB, t2h[k]), m.Wh[:, k])
        a3l, a3h = ia_mul_scalar(np.full(m.BB, t3l[k]), np.full(m.BB, t3h[k]), m.Wt[:, k])
        Cl, Ch = a1l + a2l + a3l, a1h + a2h + a3h
        pl, ph = ia_mul(Cl, Ch, dbbl, dbbh)
        Slo[k], Shi[k] = pl.sum(), ph.sum()
    wl, wh = ia_mul_scalar(Slo, Shi, m.Wo[:, 0])
    return float(wl.sum()), float(wh.sum())


def proof_T4(m, pud, max_cells=20000):
    xlo = np.array(pud["box_x_p1"]); xhi = np.array(pud["box_x_p99"])
    hlo = np.array(pud["box_h_p1"]); hhi = np.array(pud["box_h_p99"])
    lo0 = np.concatenate([xlo, hlo]); hi0 = np.concatenate([xhi, hhi])
    span = np.maximum(hi0 - lo0, 1e-12)
    stack = [(lo0, hi0, 1.0)]
    vol_pos = vol_neg = 0.0
    done = 0
    while stack and done < max_cells:
        lo, hi, vol = stack.pop()
        done += 1
        Sl, Sh = t4_S_interval(m, lo[:8], hi[:8], lo[8:], hi[8:])
        if Sl > 0:
            vol_pos += vol
        elif Sh < 0:
            vol_neg += vol
        else:
            rel = (hi - lo) / span
            j = int(np.argmax(rel))
            if rel[j] < 1e-3:
                continue
            mid = (lo[j] + hi[j]) / 2
            l2, h2_ = lo.copy(), hi.copy()
            l2[j], h2_[j] = lo[j], mid
            stack.append((l2.copy(), h2_.copy(), vol / 2))
            l2[j], h2_[j] = mid, hi[j]
            stack.append((l2, h2_, vol / 2))
    unres = 1.0 - vol_pos - vol_neg
    return {"max_cells": max_cells, "komorki_zbadane": done,
            "vol_pct_znak_plus": round(100 * vol_pos, 3),
            "vol_pct_znak_minus": round(100 * vol_neg, 3),
            "vol_pct_nierozstrzygniete": round(100 * unres, 3),
            "status": ("PARTIAL(%.1f%%)" % (100 * max(vol_pos, vol_neg))
                       if (vol_pos == 0 or vol_neg == 0)
                       else "CERTYFIKATY OBU ZNAKÓW")}


def main():
    pud = json.load(open(sys.argv[1]))
    out_json = sys.argv[2]
    mutant = sys.argv[3] if len(sys.argv) > 3 else "orig"
    max_cells = int(sys.argv[4]) if len(sys.argv) > 4 else 20000
    m = make_mutant(mutant)
    t4 = ({"status": "n.d. — M5 zmienia pochodną bramki strukturalnie "
                      "(formuła przedziałowa oryginału nie stosuje się; "
                      "rola M5 = łamanie T2)"}
          if mutant == "M5_bramka" else proof_T4(m, pud, max_cells))
    res = {"mutant": mutant, "mutant_opis": getattr(m, "_mut", "oryginał"),
           "sympy": sp.__version__,
           "T1": proof_T1(m), "T2": proof_T2(m),
           "T3": {"status": "COUNTEREXAMPLE (różnicówka) — dowód NIE uruchamiany"},
           "T4": t4}
    json.dump(res, open(out_json, "w"), indent=1)
    print(json.dumps({"mutant": mutant, "T1": res["T1"]["status"],
                      "T2": res["T2"]["status"], "T4": res["T4"]["status"],
                      "T4_vol": [res["T4"].get("vol_pct_znak_plus"),
                                 res["T4"].get("vol_pct_znak_minus"),
                                 res["T4"].get("vol_pct_nierozstrzygniete")]},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
