#!/usr/bin/env python3
"""results/WK4_RECON/tools/wk4_dryden.py — R2: generator przebiegów turbulencji Drydena (0 bootów).

Forma niskiej wysokości MIL-F-8785C — WZORY Z PROMPT_WK4_S0 §R2 (litera normy niedostępna offline;
przyjęte i nazwane w raporcie). h w stopach (h = 10 m = 32.808 ft):
  L_w = h,  L_u = L_v = h / (0.177 + 0.000823·h)^1.2
  σ_w = 0.1·W20,  σ_u = σ_v = σ_w / (0.177 + 0.000823·h)^0.4
  H_u(s)     = σ_u·√(2L_u/(πV)) / (1 + (L_u/V)s)
  H_{v,w}(s) = σ·√(L/(πV))·(1 + √3(L/V)s) / (1 + (L/V)s)²
Decyzje metodyczne (nazwane): V = Ū (prędkość adwekcji = średni wiatr; hipoteza Taylora), W20 = Ū.
Widmo jednostronne w ω (rad/s) całkuje się do σ² ⇒ wejście = biały szum o jednostronnej gęstości 1,
czyli intensywności dwustronnej q = π (E[η(t)η(t+τ)] = π·δ(τ)).
Dyskretyzacja DOKŁADNA (nie Euler): stan filtra (A, B, C) → Ad = e^{A dt}, Qd z metody Van Loana;
stan początkowy losowany z rozkładu stacjonarnego (dyskretna Lapunowa) — bez transjentu.
Ziarno JEDNO dla nogi (SEED), strumienie u/v/w z jednego generatora w stałej kolejności; profile
D2…D6 różnią się wyłącznie Ū (skala σ, L/V). Układ: Ū wzdłuż +x ENU; wx = Ū + u, wy = v, wz = w.

Użycie: wk4_dryden.py gen     → results/WK4_RECON/series/D<Ū>.json (+ .sha256) i walidacja_serii.json
        wk4_dryden.py p2      → miary P2 WK-III tą samą miarą (dopisywane do walidacji)
"""
import hashlib
import json
import math
import os
import sys

import numpy as np
from scipy.linalg import expm, solve_discrete_lyapunov

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, ".."))
SEED = 20261030          # ZAMROŻONE dla całej nogi WK-IV (data decyzji Olgi); nie dobierane pod wynik
DT = 0.05                # 20 Hz
T_TOT = 420.0
H_M = 10.0
H_FT = H_M / 0.3048
PROFILE = [2.0, 3.0, 4.0, 5.0, 6.0]


def skale(U):
    den = 0.177 + 0.000823 * H_FT
    Lw = H_FT * 0.3048
    Lu = H_FT / den ** 1.2 * 0.3048
    sw = 0.1 * U
    su = sw / den ** 0.4
    return dict(L_u=Lu, L_v=Lu, L_w=Lw, s_u=su, s_v=su, s_w=sw)


def ss_u(s, L, V):
    """H_u: pierwszego rzędu; stan x, ẋ = −x/τ + η, y = K·x/τ … zapis ogólny przez (A,B,C)."""
    tau = L / V
    K = s * math.sqrt(2 * L / (math.pi * V))
    A = np.array([[-1.0 / tau]]); B = np.array([[1.0]]); C = np.array([[K / tau]])
    return A, B, C


def ss_vw(s, L, V):
    """H = K(1+√3 τ s)/(1+τ s)² — postać sterowalna."""
    tau = L / V
    K = s * math.sqrt(L / (math.pi * V))
    # (1+τs)² = τ²s² + 2τs + 1 ⇒ s² + (2/τ)s + 1/τ²
    a1, a0 = 2.0 / tau, 1.0 / tau ** 2
    A = np.array([[0.0, 1.0], [-a0, -a1]]); B = np.array([[0.0], [1.0]])
    # licznik K(1+√3τ s)/τ² = (K/τ²) + (K√3/τ) s
    C = np.array([[K / tau ** 2, K * math.sqrt(3) / tau]])
    return A, B, C


def discretize(A, B, q, dt):
    n = A.shape[0]
    M = np.zeros((2 * n, 2 * n))
    M[:n, :n] = -A; M[:n, n:] = B @ B.T * q; M[n:, n:] = A.T
    E = expm(M * dt)
    Ad = E[n:, n:].T
    Qd = Ad @ E[:n, n:]
    return Ad, (Qd + Qd.T) / 2


def simulate(A, B, C, q, dt, n, rng):
    Ad, Qd = discretize(A, B, q, dt)
    P = solve_discrete_lyapunov(Ad, Qd)
    Lq = np.linalg.cholesky(Qd + 1e-15 * np.eye(len(Qd)))
    Lp = np.linalg.cholesky(P + 1e-15 * np.eye(len(P)))
    x = Lp @ rng.standard_normal(len(P))
    y = np.empty(n)
    for k in range(n):
        y[k] = float((C @ x)[0])
        x = Ad @ x + Lq @ rng.standard_normal(len(x))
    var_stat = float((C @ P @ C.T)[0, 0])
    return y, var_stat


def t_1e(y, dt):
    y = y - y.mean()
    n = len(y)
    f = np.fft.rfft(y, 2 * n)
    ac = np.fft.irfft(f * np.conj(f))[:n]
    ac /= ac[0]
    i = int(np.argmax(ac < math.exp(-1)))
    return i * dt if i > 0 else None


def t_1e_teoria(rodz, tau):
    if rodz == "u":
        return tau
    # R(τ) ∝ (1 − x/2)e^{−x}, x = τ/T ⇒ rozwiązanie (1 − x/2)e^{−x} = e^{−1}
    x = 0.5
    for _ in range(60):
        f = (1 - x / 2) * math.exp(-x) - math.exp(-1)
        df = (-0.5 - (1 - x / 2)) * math.exp(-x)
        x -= f / df
    return x * tau


def miary(t, wx, wy, wz, U=None, cel=None, LV=None):
    wh = np.hypot(wx, wy)
    th = np.degrees(np.arctan2(wy, wx))
    m = dict(sigma_x=round(float(np.std(wx)), 4), sigma_y=round(float(np.std(wy)), 4),
             sigma_z=round(float(np.std(wz)), 4), srednia_x=round(float(np.mean(wx)), 4),
             wh_min=round(float(wh.min()), 3), wh_max=round(float(wh.max()), 3),
             sigma_kier_deg=round(float(np.std(th)), 2),
             frac_odwrocenia=round(float(np.mean(wx < 0)), 5))
    # pasmo: częstotliwość, poniżej której leży 90 % mocy składowej x (i y)
    for nm, sig in (("x", wx), ("y", wy), ("z", wz)):
        s = sig - sig.mean()
        if np.allclose(s, 0):
            m[f"f90_{nm}_Hz"] = None
            continue
        P = np.abs(np.fft.rfft(s)) ** 2; fr = np.fft.rfftfreq(len(s), t[1] - t[0])
        c = np.cumsum(P) / P.sum()
        m[f"f90_{nm}_Hz"] = round(float(fr[np.searchsorted(c, 0.9)]), 4)
    if U is not None:
        m["sigma_kier_oczek_deg"] = round(math.degrees(math.atan(cel["s_v"] / U)), 2)
        for k, (sig, s_cel, rodz, LVk) in {"u": (wx, cel["s_u"], "u", LV["u"]),
                                            "v": (wy, cel["s_v"], "vw", LV["v"]),
                                            "w": (wz, cel["s_w"], "vw", LV["w"])}.items():
            sr = float(np.std(sig))
            m[f"{k}_sigma_real/cel"] = round(sr / s_cel, 4)
            m[f"{k}_sigma_ok_10pct"] = bool(abs(sr / s_cel - 1) <= 0.10)
            te = t_1e(sig, t[1] - t[0])
            m[f"{k}_t1e_s"] = round(te, 2) if te else None
            m[f"{k}_L/V_s"] = round(LVk, 2)
            m[f"{k}_t1e_teoria_s"] = round(t_1e_teoria(rodz, LVk), 2)
            m[f"{k}_t1e_ok_25pct_LV"] = bool(te is not None and abs(te / LVk - 1) <= 0.25)
            m[f"{k}_t1e_ok_25pct_teoria"] = bool(te is not None and abs(te / t_1e_teoria(rodz, LVk) - 1) <= 0.25)
    return m


def gen():
    os.makedirs(os.path.join(OUT, "series"), exist_ok=True)
    n = int(round(T_TOT / DT)) + 1
    t = np.round(np.arange(n) * DT, 4)
    wal = {"seed": SEED, "dt": DT, "T": T_TOT, "h_m": H_M, "V": "= Ū (adwekcja)", "W20": "= Ū",
           "zrodlo_wzorow": "PROMPT_WK4_S0 §R2 (MIL-F-8785C forma niskiej wysokości; norma niedostępna offline)",
           "profile": {}}
    for U in PROFILE:
        rng = np.random.default_rng(SEED)          # to samo ziarno dla każdego profilu (jedno dla nogi)
        sk = skale(U)
        u, vu = simulate(*ss_u(sk["s_u"], sk["L_u"], U), math.pi, DT, n, rng)
        v, vv = simulate(*ss_vw(sk["s_v"], sk["L_v"], U), math.pi, DT, n, rng)
        w, vw = simulate(*ss_vw(sk["s_w"], sk["L_w"], U), math.pi, DT, n, rng)
        wx, wy, wz = U + u, v, w
        name = f"D{int(U)}"
        doc = {"profil": name, "U": U, "seed": SEED, "dt": DT, "skale": {k: round(x, 4) for k, x in sk.items()},
               "kolumny": ["t", "wx", "wy", "wz"], "uklad": "ENU, Ū wzdłuż +x",
               "t": t.tolist(), "wx": np.round(wx, 5).tolist(), "wy": np.round(wy, 5).tolist(),
               "wz": np.round(wz, 5).tolist()}
        p = os.path.join(OUT, "series", f"{name}.json")
        json.dump(doc, open(p, "w"))
        sha = hashlib.sha256(open(p, "rb").read()).hexdigest()
        open(p + ".sha256", "w").write(f"{sha}  {name}.json\n")
        LV = {"u": sk["L_u"] / U, "v": sk["L_v"] / U, "w": sk["L_w"] / U}
        m = miary(t, wx, wy, wz, U, sk, LV)
        m["sigma_stacjonarne_teoria"] = {"u": round(math.sqrt(vu), 4), "v": round(math.sqrt(vv), 4),
                                         "w": round(math.sqrt(vw), 4)}
        m["cel"] = {k: round(x, 4) for k, x in sk.items()}
        m["sha256"] = sha
        wal["profile"][name] = m
        print(f"[{name}] sha {sha[:16]} σ real/cel u {m['u_sigma_real/cel']} v {m['v_sigma_real/cel']} "
              f"w {m['w_sigma_real/cel']} | t1e u {m['u_t1e_s']} (L/V {m['u_L/V_s']}) v {m['v_t1e_s']} "
              f"(teoria {m['v_t1e_teoria_s']}) w {m['w_t1e_s']} (teoria {m['w_t1e_teoria_s']}) | "
              f"|w| {m['wh_min']}..{m['wh_max']} σθ {m['sigma_kier_deg']} (oczek {m['sigma_kier_oczek_deg']}) "
              f"odwr {m['frac_odwrocenia']}")
    # P2 WK-III tą samą miarą (litera RECON_WK3 R2 / wk3_gust)
    mag = 2.0 * (1 + 0.8 * np.sin(2 * np.pi * t / 4.0))
    th = np.radians(30.0 * np.sin(2 * np.pi * t / 11.0))
    wal["P2_WK3"] = miary(t, mag * np.cos(th), mag * np.sin(th), np.zeros_like(t))
    print("[P2]", wal["P2_WK3"])
    json.dump(wal, open(os.path.join(OUT, "walidacja_serii.json"), "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__" and (len(sys.argv) < 2 or sys.argv[1] == "gen"):
    gen()


def mc(n_seed=200):
    """DIAGNOSTYKA (nie selekcja): rozkład σ zrealizowanego / cel na 420 s przy ziarnach 1..n_seed —
    czy ±10 % jest w ogóle osiągalne przy L/V tej skali. Zamrożone SEED nie zmienia się."""
    n = int(round(T_TOT / DT)) + 1
    out = {}
    for U in (2.0, 6.0):
        sk = skale(U)
        r = {"u": [], "v": [], "w": []}
        for sd in range(1, n_seed + 1):
            rng = np.random.default_rng(sd)
            r["u"].append(np.std(simulate(*ss_u(sk["s_u"], sk["L_u"], U), math.pi, DT, n, rng)[0]) / sk["s_u"])
            r["v"].append(np.std(simulate(*ss_vw(sk["s_v"], sk["L_v"], U), math.pi, DT, n, rng)[0]) / sk["s_v"])
            r["w"].append(np.std(simulate(*ss_vw(sk["s_w"], sk["L_w"], U), math.pi, DT, n, rng)[0]) / sk["s_w"])
        out[f"D{int(U)}"] = {k: {"p5_p50_p95": np.percentile(v, [5, 50, 95]).round(3).tolist(),
                                 "frac_w_10pct": round(float(np.mean(np.abs(np.array(v) - 1) <= 0.1)), 3)}
                             for k, v in r.items()}
        print(f"[mc D{int(U)}]", out[f"D{int(U)}"])
    wal = json.load(open(os.path.join(OUT, "walidacja_serii.json")))
    wal["diagnostyka_mc_200_ziaren"] = out
    json.dump(wal, open(os.path.join(OUT, "walidacja_serii.json"), "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "mc":
    mc()
