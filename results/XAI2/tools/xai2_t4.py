#!/usr/bin/env python3
"""results/XAI2/tools/xai2_t4.py — T4′ prawo pościgu od nowa (PRE_XAI2 §2) + M6 + tabela M1–M5.

KROK 0b (PROMPT §1.5): litera kierunku orbity NAUCZYCIELA — scenarios.py:70
(orbit_dir = rng.choice(["CW","CCW"]) z ziarna scenariusza), konsument:
bench_flight.py:310 → make_controller(..., orbit_dir=ep["orbit_dir"]) →
r03/controllers/orbit_executor.py:93-96. Sieć NIE MA takiego wejścia
(features.py: 8 cech). MAPOWANIE ZNAKU (wyprowadzenie z litery egzekutora):
out = (own−trk)/d = −r̂; CCW ⇒ tan=(−out_e, out_n) = (r̂_e, −r̂_n) = −t̂,
więc lot CCW nauczyciela ma v_tan = v_h·t̂ < 0; CW ⇒ v_tan > 0.

T4a: d ≥ 12 m ⇒ v_rad > 0;  T4b: d ≤ 4 m ⇒ v_rad < 0  (progi FROZEN PRE §2).
Różnicówka na wszystkich tickach inferencji korpusu w dziedzinie; v_rad/v_tan
z y SUROWEGO (głowa przed clip_v) i rel odnormalizowanego (PRE §1).
n < 30 w dziedzinie ⇒ NIEROZSTRZYGALNE. Po przejściu różnicówki:
ε-rury (ε_x=0.02 znorm. wszystkie 8 cech, ε_h=0.01) przedziałówką ia_* →
% ticków certyfikowanych; próba globalna: pudełko (d ∈ dziedzina, kierunek
θ w 8 sektorach po 45°, x₂..x₇ ∈ p1–p99 pudełka S1, h ∈ Box_h) adaptacyjną
bisekcją z budżetem 20k komórek → % objętości parametryzacji.

Czułość: M6 (Wo,bo→−Wo,−bo) MUSI obalić każde przechodzące T4a/T4b;
M1–M5 z S1 nogi XAI w tabeli obok (różnicówka T4a/T4b per mutant,
krok mutanta = jego własny step_np — M4/M5 są strukturalne).

Użycie: xai2_t4.py <pudelko_s1.json> <t4.json> <mutanty.json>
"""
import collections
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xai2_common import (ROOT, V_MAX, corpus_index, fresh_model, ia_vrad_sign,
                         install, jd, make_m6, make_mutant, raw_pass, rel_raw,
                         replay_all, sid_orbit_dir, v_rad_tan)

D_FAR, D_NEAR = 12.0, 4.0
EPS_X, EPS_H = 0.02, 0.01
BUDGET = 20000


def model_pass(m, rep):
    """Przebieg epizodu krokiem WŁASNYM MUTANTA (m.step_np — M4/M5 strukturalne).
    Zwraca y_raw (T,3) na tickach inferencji (NaN poza)."""
    T = len(rep["t"])
    h = np.zeros((1, m.H))
    y_raw = np.full((T, 3), np.nan)
    for i in range(T):
        if rep["infer"][i]:
            y, h, _ = m.step_np(rep["x"][i][None, :], h)
            y_raw[i] = y[0]
    return y_raw


def diff_t4(m, reps, y_raw_per_ep):
    """Różnicówka T4a/T4b + materiał T4c. y_raw_per_ep: lista (T,3) per epizod."""
    res = {"T4a": {"n": 0, "cex": 0, "przyklady": [], "v_rad_min": None},
           "T4b": {"n": 0, "cex": 0, "przyklady": [], "v_rad_max": None}}
    t4c = []
    vmin_a, vmax_b = np.inf, -np.inf
    d_all_min, d_all_max = np.inf, -np.inf
    for rep, yr in zip(reps, y_raw_per_ep):
        idx = np.where(rep["infer"])[0]
        if len(idx) == 0:
            continue
        x = rep["x"][idx]
        rel_n, rel_e = rel_raw(fresh_model(), x)   # mean/std z npz (niemutowane)
        d, v_rad, v_tan = v_rad_tan(yr[idx], rel_n, rel_e)
        t0 = float(rep["t"][idx[0]])
        d_all_min, d_all_max = min(d_all_min, d.min()), max(d_all_max, d.max())
        for key, mask, bad in (("T4a", d >= D_FAR, lambda v: v <= 0),
                               ("T4b", d <= D_NEAR, lambda v: v >= 0)):
            n = int(mask.sum())
            res[key]["n"] += n
            if n:
                vb = v_rad[mask]
                cx = bad(vb)
                res[key]["cex"] += int(cx.sum())
                for j in np.where(mask)[0][bad(v_rad[mask])][:max(0, 3 - len(res[key]["przyklady"]))]:
                    i = idx[j]
                    res[key]["przyklady"].append(
                        {"sid": rep["sid"], "t": round(float(rep["t"][i]), 3),
                         "d": round(float(d[j]), 3), "v_rad": round(float(v_rad[j]), 4),
                         "czas_od_1_inferencji_s": round(float(rep["t"][i]) - t0, 3)})
        if (d >= D_FAR).any():
            vmin_a = min(vmin_a, float(v_rad[d >= D_FAR].min()))
        if (d <= D_NEAR).any():
            vmax_b = max(vmax_b, float(v_rad[d <= D_NEAR].max()))
        band = (d >= 6.0) & (d <= 10.0)
        if band.sum() >= 10:
            vt = v_tan[band]
            frac_neg = float((vt < 0).mean())
            staly = bool((vt < 0).all() or (vt > 0).all())
            siec = "CCW" if frac_neg > 0.5 else "CW"       # mapowanie z litery egzekutora
            t4c.append({"sid": rep["sid"], "n_band": int(band.sum()),
                        "frac_vtan_ujemne": round(frac_neg, 4), "staly_znak": staly,
                        "kierunek_sieci": siec, "orbit_dir_scenariusza": sid_orbit_dir(rep["sid"])})
    res["T4a"]["v_rad_min"] = round(vmin_a, 4) if np.isfinite(vmin_a) else None
    res["T4b"]["v_rad_max"] = round(vmax_b, 4) if np.isfinite(vmax_b) else None
    res["d_korpus"] = [round(d_all_min, 3), round(d_all_max, 3)]
    return res, t4c


def eps_tubes(m, reps, y_raw_per_ep, key):
    """Certyfikacja ε-rur per tick dziedziny. key: 'T4a' (lo>0) / 'T4b' (hi<0)."""
    n_cert = n_tot = 0
    for rep, yr in zip(reps, y_raw_per_ep):
        idx = np.where(rep["infer"])[0]
        if len(idx) == 0:
            continue
        x = rep["x"][idx]
        rel_n, rel_e = rel_raw(m, x)
        d = np.hypot(rel_n, rel_e)
        mask = (d >= D_FAR) if key == "T4a" else (d <= D_NEAR)
        hprev = np.zeros(20)
        # h_prev per tick: stan po poprzednim ticku (hold mrozi stan)
        hs = np.vstack([np.zeros((1, 20)), rep["h"][idx[:-1]]])
        for j in np.where(mask)[0]:
            xl, xh = x[j] - EPS_X, x[j] + EPS_X
            hl, hh_ = hs[j] - EPS_H, hs[j] + EPS_H
            lo, hi, dlo = ia_vrad_sign(m, xl, xh, hl, hh_)
            n_tot += 1
            if dlo > 0 and ((key == "T4a" and lo > 0) or (key == "T4b" and hi < 0)):
                n_cert += 1
    return {"n_rur": n_tot, "n_cert": n_cert,
            "pct": round(100.0 * n_cert / max(n_tot, 1), 2)}


def _cos_int(tl, th):
    lo, hi = min(math.cos(tl), math.cos(th)), max(math.cos(tl), math.cos(th))
    k0, k1 = math.ceil(tl / (2 * math.pi)), math.floor(th / (2 * math.pi))
    if k0 <= k1:
        hi = 1.0
    k0 = math.ceil((tl - math.pi) / (2 * math.pi))
    k1 = math.floor((th - math.pi) / (2 * math.pi))
    if k0 <= k1:
        lo = -1.0
    return lo, hi


def _sin_int(tl, th):
    return _cos_int(tl - math.pi / 2, th - math.pi / 2)


def _imul(al, ah, bl, bh):
    p = (al * bl, al * bh, ah * bl, ah * bh)
    return min(p), max(p)


def global_box(m, pud, key, d_rng):
    """Próba globalna: parametry (d, θ, x₂..x₇, h) = 28 wym.; bisekcja najszerszego
    względnie; certyfikat komórki = licznik v_rad bez zera właściwego znaku.
    Kolejka FIFO (wszerz): budżet rozkłada się równo na 8 sektorów."""
    xl9 = np.array(pud["box_x_p1"]); xh9 = np.array(pud["box_x_p99"])
    hl = np.array(pud["box_h_p1"]); hh_ = np.array(pud["box_h_p99"])
    lo0 = np.concatenate([[d_rng[0], 0.0], xl9[2:], hl])
    hi0 = np.concatenate([[d_rng[1], 2 * math.pi], xh9[2:], hh_])
    span = np.maximum(hi0 - lo0, 1e-12)
    sect = 2 * math.pi / 8
    stack = collections.deque()
    for s in range(8):
        l, h = lo0.copy(), hi0.copy()
        l[1], h[1] = s * sect, (s + 1) * sect
        stack.append((l, h, 1.0 / 8))
    vol_ok = 0.0
    done = 0
    while stack and done < BUDGET:
        lo, hi, vol = stack.popleft()
        done += 1
        cl, ch = _cos_int(lo[1], hi[1])
        sl, sh = _sin_int(lo[1], hi[1])
        rnl, rnh = _imul(lo[0], hi[0], cl, ch)
        rel_, reh_ = _imul(lo[0], hi[0], sl, sh)
        x0l = (rnl - m.input_mean[0]) / m.input_std[0]
        x0h = (rnh - m.input_mean[0]) / m.input_std[0]
        x1l = (rel_ - m.input_mean[1]) / m.input_std[1]
        x1h = (reh_ - m.input_mean[1]) / m.input_std[1]
        xlo = np.concatenate([[x0l, x1l], lo[2:8]])
        xhi = np.concatenate([[x0h, x1h], hi[2:8]])
        from xai2_common import ia_step_y
        ylo, yhi = ia_step_y(m, xlo, xhi, lo[8:], hi[8:])
        t1 = _imul(ylo[0], yhi[0], rnl, rnh)
        t2 = _imul(ylo[1], yhi[1], rel_, reh_)
        nl, nh = t1[0] + t2[0], t1[1] + t2[1]
        if (key == "T4a" and nl > 0) or (key == "T4b" and nh < 0):
            vol_ok += vol
        else:
            rel_w = (hi - lo) / span
            j = int(np.argmax(rel_w))
            if rel_w[j] < 1e-3:
                continue
            mid = (lo[j] + hi[j]) / 2
            a, b = lo.copy(), hi.copy()
            a[j], b[j] = lo[j], mid
            stack.append((a.copy(), b.copy(), vol / 2))
            a[j], b[j] = mid, hi[j]
            stack.append((a, b, vol / 2))
    return {"budzet": BUDGET, "komorki": done, "d_zakres": [round(d_rng[0], 3), round(d_rng[1], 3)],
            "pct_objetosci_cert": round(100.0 * vol_ok, 3)}


def status(n, cex, tubes):
    if n < 30:
        return "NIEROZSTRZYGALNE"
    if cex > 0:
        return "COUNTEREXAMPLE"
    if tubes and tubes["pct"] == 100.0:
        return "PROVED"
    if tubes:
        return f"PARTIAL({tubes['pct']}%)"
    return "PASS-DIFF"


def main():
    pud = json.load(open(sys.argv[1]))
    out_t4, out_mut = sys.argv[2], sys.argv[3]
    m = fresh_model()
    install(m)
    reps = replay_all(corpus_index())
    yraw = []
    for rep in reps:
        rp, _ = raw_pass(m, rep)
        yraw.append(rp["y_raw"])
    diff, t4c = diff_t4(m, reps, yraw)
    print("diff:", json.dumps({k: {kk: diff[k][kk] for kk in ("n", "cex")}
                               for k in ("T4a", "T4b")}))
    d_lo, d_hi = diff["d_korpus"]
    out = {"krok0b": {
        "scenarios_py_70": 'orbit_dir = rng.choice(["CW", "CCW"])',
        "konsument": "bench_flight.py:310 → orbit_executor.py:93-96 (nauczyciel); "
                     "sieć bez tego wejścia (features.py: 8 cech)",
        "mapowanie_znaku": "CCW nauczyciela ⇒ v_tan<0 (tan=(r̂_e,−r̂_n)=−t̂); CW ⇒ v_tan>0"},
        "rozn": diff, "T4c": {"epizody": t4c}}
    # T4c agregacja
    if t4c:
        st = [e for e in t4c if e["staly_znak"]]
        zg = [e for e in t4c if e["orbit_dir_scenariusza"]
              and e["kierunek_sieci"] == e["orbit_dir_scenariusza"]]
        ccw = [e for e in t4c if e["kierunek_sieci"] == "CCW"]
        out["T4c"]["agregaty"] = {
            "n_epizodow_w_pasmie": len(t4c),
            "frakcja_staly_znak": round(len(st) / len(t4c), 4),
            "frakcja_kierunek_CCW": round(len(ccw) / len(t4c), 4),
            "frakcja_zgodna_z_orbit_dir": round(len(zg) / len(t4c), 4)}
    # dowody po różnicówce
    for key, d_rng in (("T4a", (D_FAR, d_hi + 0.5)), ("T4b", (max(0.2, d_lo - 0.5), D_NEAR))):
        r = diff[key]
        tubes = gb = None
        if r["n"] >= 30 and r["cex"] == 0:
            tubes = eps_tubes(m, reps, yraw, key)
            gb = global_box(m, pud, key, d_rng)
            print(key, "rury:", tubes, "global:", gb)
        out[key] = {"n": r["n"], "cex": r["cex"], "eps_rury": tubes,
                    "proba_globalna": gb, "status": status(r["n"], r["cex"], tubes)}
        print(key, "STATUS:", out[key]["status"])
    jd(out, out_t4)
    # ---- mutanty: M6 + M1..M5 (krok mutanta = jego step_np)
    tab = {}
    for name, mk in [("M6_odwrocenie", make_m6())] + \
                    [(n, make_mutant(n)) for n in
                     ("M1_znak", "M2_skala", "M3_zero", "M4_glowa", "M5_bramka")]:
        install(mk)
        reps_m = replay_all(corpus_index())
        ym = [model_pass(mk, rep) for rep in reps_m]
        dm, _ = diff_t4(mk, reps_m, ym)
        tab[name] = {"opis": getattr(mk, "_mut", ""),
                     "T4a": {"n": dm["T4a"]["n"], "cex": dm["T4a"]["cex"]},
                     "T4b": {"n": dm["T4b"]["n"], "cex": dm["T4b"]["cex"]}}
        print(name, tab[name])
    install(fresh_model())
    m6ok = {}
    for key in ("T4a", "T4b"):
        if out[key]["status"] in ("PROVED", "PARTIAL", "PASS-DIFF") or \
           out[key]["status"].startswith("PARTIAL"):
            m6ok[key] = tab["M6_odwrocenie"][key]["cex"] > 0
    jd({"tabela": tab, "M6_obala_przechodzace": m6ok,
        "M6_pass": all(m6ok.values()) if m6ok else None}, out_mut)


if __name__ == "__main__":
    main()
