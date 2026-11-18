#!/usr/bin/env python3
"""results/PETLA_RECON/tools/pl_naped.py — R3 model napędu i silnik pętli (PROMPT_PETLA_S0 §5; 0 bootów).

Klasa modelu (ustalona z góry, osobno poziom i pion): opóźnienie k ∈ {0..10} ticków (dt 0.05 s) i inercja pierwszego rzędu
τ ∈ {0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0} s: v[i+1] = v[i] + α·(c[i−k] − v[i]), α = 1 − exp(−dt/τ).
Poziom: komenda wysłana (cmd_v_ned z demo; w misji ALLOW = komenda sieci) → prędkość EKF (own_vel), symulacja swobodna na każdym
ciągłym odcinku misji od zmierzonej prędkości na jego początku; dopasowanie na lotach o parzystym indeksie listy posortowanej
(pl_dane.loty), ocena (W1: RMSE wektora prędkości poziomej ≤ 0.15 m/s) na nieparzystych.
Pion: skoki komendy w fazie zejścia (tk „cmd”[2]: 0 → 1.5 → 0.7 m/s) → vz z wierszy „ekf” trace (wyższa częstotliwość, mono),
interpolowane na chwile ticków; symulacja swobodna od początku zejścia; dopasowanie na wszystkich lotach.
Silnik `Petla`: B równoległych biegów, stan drona (p, v NED), bufory opóźnień, stan sieci; wejście sieci = [rel + szum, v, wiek,
1]; szum AR(1) per oś z R2 (szum_rel.json); wariant W: komenda pionowa sieci zastąpiona vd = clip(0.5·(rel_z − 2), ±1).
"""
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pl_dane as PD                                     # noqa: E402
import pl_siec as PS                                     # noqa: E402

OUT = os.path.join(PD.ROOT, "results/PETLA_RECON")
DT = 0.05
KS = range(0, 11)
TAUS = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0)
W1_PROG = 0.15                                           # m/s (prompt §5; tolerancja w progu)


def sym1(c, v0, k, tau):
    """Symulacja swobodna: c (T,d) komenda, v0 (d,) → v (T,d)."""
    a = 1 - math.exp(-DT / tau)
    T = len(c)
    v = np.zeros_like(c)
    v[0] = v0
    for i in range(T - 1):
        ci = c[i - k] if i - k >= 0 else c[0] * 0 + v0
        v[i + 1] = v[i] + a * (ci - v[i])
    return v


def odcinki_poziom(L):
    s = L["misja"].astype(bool)
    idx = np.where(s)[0]
    cuts = np.where(np.diff(idx) > 1)[0]
    return [seg for seg in np.split(idx, cuts + 1) if len(seg) > 40]


def rmse_poziom(loty_L, k, tau):
    se, n = 0.0, 0
    for L in loty_L:
        for seg in odcinki_poziom(L):
            c, v = L["cmd"][seg][:, :2], L["vel"][seg][:, :2]
            vs = sym1(c, v[0], k, tau)
            se += ((vs - v) ** 2).sum(); n += len(seg)
    return math.sqrt(se / n)


def dane_pion(d):
    """Zejście: (cmd_vd na tickach, vz z wierszy ekf interpolowane po mono)."""
    tk = [r for r in PD.jl(os.path.join(d, "trace.jsonl"), "tk") if r.get("desc")]
    ek = PD.jl(os.path.join(d, "trace.jsonl"), "ekf")
    if not tk or not ek:
        return None
    em = np.array([r["mono"] for r in ek]); ez = np.array([r["vz"] for r in ek])
    tm = np.array([r["mono"] for r in tk]); c = np.array([r["cmd"][2] for r in tk])
    vz = np.interp(tm, em, ez)
    return c, vz


def fit():
    loty = PD.loty()
    LL = [PD.wczytaj(d) for d in loty]
    par, npar = LL[0::2], LL[1::2]
    siatka = {(k, t): rmse_poziom(par, k, t) for k in KS for t in TAUS}
    kh, th = min(siatka, key=siatka.get)
    w1 = rmse_poziom(npar, kh, th)
    w1_per = {str(L["nazwa"]): rmse_poziom([L], kh, th) for L in npar}
    PV = [dane_pion(d) for d in loty]
    PV = [x for x in PV if x is not None]

    def rmse_pion(k, t):
        se, n = 0.0, 0
        for c, vz in PV:
            vs = sym1(c[:, None], np.array([vz[0]]), k, t)[:, 0]
            se += ((vs - vz) ** 2).sum(); n += len(c)
        return math.sqrt(se / n)
    sp = {(k, t): rmse_pion(k, t) for k in KS for t in TAUS}
    kv, tv = min(sp, key=sp.get)
    out = {"poziom": {"k_tick": kh, "opoznienie_s": kh * DT, "tau_s": th, "rmse_dopasowanie": siatka[(kh, th)], "W1_rmse_test": w1,
                      "W1_per_lot": w1_per, "W1_pass": w1 <= W1_PROG, "prog": W1_PROG,
                      "loty_dopasowanie": [str(L["nazwa"]) for L in par], "loty_test": [str(L["nazwa"]) for L in npar],
                      "siatka": {f"{k},{t}": v for (k, t), v in siatka.items()}},
           "pion": {"k_tick": kv, "opoznienie_s": kv * DT, "tau_s": tv, "rmse": sp[(kv, tv)], "n_lotow": len(PV),
                    "siatka": {f"{k},{t}": v for (k, t), v in sp.items()}}}
    out["napedy"] = napedy(out)
    json.dump(out, open(os.path.join(OUT, "r3_naped.json"), "w"), ensure_ascii=False, indent=1)
    return out


def napedy(f):
    kh, th, kv, tv = f["poziom"]["k_tick"], f["poziom"]["tau_s"], f["pion"]["k_tick"], f["pion"]["tau_s"]
    return {"N": {"kh": kh, "th": th, "kv": kv, "tv": tv},
            "P-": {"kh": kh, "th": th, "kv": kv, "tv": tv * 0.5}, "P+": {"kh": kh, "th": th, "kv": kv, "tv": tv * 2.0},
            "H-": {"kh": max(0, kh - 2), "th": th, "kv": kv, "tv": tv}, "H+": {"kh": kh + 2, "th": th, "kv": kv, "tv": tv}}


class Szum:
    """AR(1) per oś: x' = φ·x + σ·sqrt(1−φ²)·w, φ = exp(−dt/τc); średnia stała dodana."""

    def __init__(self, B, rng, wl=True):
        sz = json.load(open(os.path.join(OUT, "szum_rel.json")))
        self.mu = np.array([sz[a]["srednia"] for a in "NED"])
        self.sd = np.array([sz[a]["std"] for a in "NED"])
        self.phi = np.exp(-DT / np.array([max(sz[a]["czas_korelacji_s"], DT) for a in "NED"]))
        self.rng, self.wl = rng, wl
        self.x = rng.standard_normal((B, 3)) * self.sd if wl else np.zeros((B, 3))

    def krok(self):
        if not self.wl:
            return np.zeros_like(self.x)
        self.x = self.phi * self.x + self.sd * np.sqrt(1 - self.phi ** 2) * self.rng.standard_normal(self.x.shape)
        return self.x + self.mu


class Petla:
    """B biegów: dron (p, v), bufory komend, stan sieci. krok(q) → komenda; q (B,3) pozycja intruza NED."""

    def __init__(self, B, nap, p0, v0, wiek, szum, wariant="siec"):
        self.B, self.n = B, nap
        self.p, self.v = p0.copy(), v0.copy()
        self.h = np.zeros((B, PS.H))
        self.bh = [np.zeros((B, 2)) for _ in range(nap["kh"] + 1)]
        self.bv = [np.zeros(B) for _ in range(nap["kv"] + 1)]
        self.ah, self.av = 1 - math.exp(-DT / nap["th"]), 1 - math.exp(-DT / nap["tv"])
        self.wiek, self.szum, self.wariant = wiek, szum, wariant
        self.x = None

    def krok(self, q):
        rel = q - self.p + self.szum.krok()
        B = self.B
        x = np.concatenate([rel, self.v, np.full((B, 1), self.wiek), np.ones((B, 1))], 1)
        self.h_przed = self.h
        c, self.h = PS.krok(PS.norm(x), self.h)
        if self.wariant == "W":
            c = c.copy()
            c[:, 2] = np.clip(0.5 * (rel[:, 2] - 2.0), -1.0, 1.0)
        self.x, self.c = x, c
        self.bh.append(c[:, :2]); ch = self.bh.pop(0)
        self.bv.append(c[:, 2]); cv = self.bv.pop(0)
        self.v[:, :2] += self.ah * (ch - self.v[:, :2])
        self.v[:, 2] += self.av * (cv - self.v[:, 2])
        self.p += self.v * DT
        return c


def w2():
    f = json.load(open(os.path.join(OUT, "r3_naped.json")))
    nap = f["napedy"]["N"]
    wiek = float(json.load(open(os.path.join(OUT, "r2b.json")))["wiek_tracka"]["mediana"])
    wyn = []
    for i, d in enumerate(PD.loty()):
        L = PD.wczytaj(d)
        R = PS.replay(L)
        i0 = int(np.argmax(R["infer"]))
        sel = np.arange(i0, len(L["t"]))
        sel = sel[L["misja"][sel] > 0]
        i1 = sel[-1]
        rng = np.random.default_rng(1000 + i)
        P = Petla(1, nap, L["gt"][i0][None].copy(), L["vel"][i0][None].copy(), wiek, Szum(1, rng))
        pm, qm = [], []
        for j in range(i0, i1 + 1):
            P.krok(L["intr"][j][None])
            pm.append(P.p[0].copy()); qm.append(L["intr"][j])
        pm, qm = np.array(pm), np.array(qm)
        tt = L["t"][i0:i1 + 1] - L["t"][i0]
        okm = (tt >= 30.0) & (L["misja"][i0:i1 + 1] > 0)
        gl, ql = L["gt"][i0:i1 + 1], L["intr"][i0:i1 + 1]
        dl = np.hypot(*(ql[:, :2] - gl[:, :2]).T)[okm]; ds = np.hypot(*(qm[:, :2] - pm[:, :2]).T)[okm]
        rl = np.hypot(gl[:, 0], gl[:, 1])[okm]; rs = np.hypot(pm[:, 0], pm[:, 1])[okm]
        zl = (ql[:, 2] - gl[:, 2])[okm]; zs = (qm[:, 2] - pm[:, 2])[okm]
        m = {"lot": str(L["nazwa"]), "d_med": [float(np.median(dl)), float(np.median(ds))], "d_p99": [float(np.percentile(dl, 99)), float(np.percentile(ds, 99))],
             "r_max": [float(rl.max()), float(rs.max())], "relz_max": [float(zl.max()), float(zs.max())]}
        m["ok"] = {"d_med": abs(m["d_med"][1] - m["d_med"][0]) <= 0.6, "d_p99": abs(m["d_p99"][1] - m["d_p99"][0]) <= 1.0,
                   "r_max": abs(m["r_max"][1] - m["r_max"][0]) <= 1.5, "relz_max": abs(m["relz_max"][1] - m["relz_max"][0]) <= 2.0}
        m["pass"] = all(m["ok"].values())
        wyn.append(m)
        print(m, flush=True)
    out = {"naped": nap, "wiek_tracka": wiek, "loty": wyn, "n_pass": sum(w["pass"] for w in wyn), "W2_pass": sum(w["pass"] for w in wyn) >= 12}
    json.dump(out, open(os.path.join(OUT, "r3_w2.json"), "w"), ensure_ascii=False, indent=1)
    return out


if __name__ == "__main__":
    if "fit" in sys.argv[1:]:
        f = fit()
        print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "siatka"} if isinstance(v, dict) else v for k, v in f.items()}, ensure_ascii=False, indent=1))
    if "w2" in sys.argv[1:]:
        o = w2()
        print("W2", o["n_pass"], "/15", o["W2_pass"])
