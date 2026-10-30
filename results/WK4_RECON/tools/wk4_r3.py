#!/usr/bin/env python3
"""results/WK4_RECON/tools/wk4_r3.py — R1(f)(g) + R3: zgodność odtworzenia przebiegu w świecie sondy z plikiem.

Wejście: przebiegi wk4_windprobe.py --series (świat probe_wk4: wiatr bazowy 0, time_for_rise 0.01 h+v).
Rekonstrukcja w = v + a/f (wk4_windprobe.rekon3, f = 0.397). Odniesienie = wartość pliku w chwili t:
i = floor((t − t_off)/dt) (litera publikatora). Okno porównania: [t_off + 2 s, koniec − 1 s].
Miary: RMSE per składowa, σ_rekon/σ_plik, opóźnienie z max korelacji krzyżowej (krok 0.01 s, ±1 s),
determinizm: max |Δw| między dwoma startami tego samego pliku (wspólna siatka 0.01 s).

Użycie: wk4_r3.py <out.json> <probe_a.json> [<probe_b.json> ...]
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from wk4_windprobe import rekon3  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))


def ref_series(d, tg):
    s = json.load(open(os.path.join(ROOT, "results", "WK4_RECON", d["series"]) if not os.path.isabs(d["series"])
                       and not os.path.exists(d["series"]) else d["series"]))
    i = np.clip(((tg - d["t_off"]) / s["dt"]).astype(int), 0, len(s["wx"]) - 1)
    return np.array(s["wx"])[i], np.array(s["wy"])[i], np.array(s["wz"])[i]


def grid_of(d):
    t, wx, wy, wz = rekon3(d["poses"])
    lo, hi = d["t_off"] + 2.0, t[-1] - 1.0
    tg = np.round(np.arange(lo, hi, 0.01), 4)
    return tg, np.interp(tg, t, wx), np.interp(tg, t, wy), np.interp(tg, t, wz)


def delay(a, b, dt=0.01, maxlag=100):
    a = a - a.mean(); b = b - b.mean()
    best, lag_b = -2, 0
    for L in range(-maxlag, maxlag + 1):
        if L >= 0:
            c = np.corrcoef(a[L:], b[:len(b) - L])[0, 1]
        else:
            c = np.corrcoef(a[:L], b[-L:])[0, 1]
        if c > best:
            best, lag_b = c, L
    return round(lag_b * dt, 3), round(float(best), 4)


def main():
    out = {}
    runs = {}
    for p in sys.argv[2:]:
        d = json.load(open(p))
        tg, rx, ry, rz = grid_of(d)
        fx, fy, fz = ref_series(d, tg)
        r = {"rate_Hz": d["rate"], "seria": d["series"], "okno_s": [float(tg[0]), float(tg[-1])]}
        for nm, rec, ref in (("x", rx, fx), ("y", ry, fy), ("z", rz, fz)):
            lag, cc = delay(rec, ref)
            r[nm] = {"rmse": round(float(np.sqrt(np.mean((rec - ref) ** 2))), 4),
                     "sigma_rekon/sigma_plik": round(float(np.std(rec) / np.std(ref)), 4),
                     "srednia_rekon": round(float(rec.mean()), 4), "srednia_plik": round(float(ref.mean()), 4),
                     "opoznienie_s": lag, "korelacja_max": cc}
        r["zgodnosc_PRE"] = bool(all(abs(r[c]["sigma_rekon/sigma_plik"] - 1) <= 0.10 and r[c]["opoznienie_s"] <= 0.1
                                     for c in ("x", "y", "z")))
        out[os.path.basename(p)] = r
        runs[os.path.basename(p)] = (tg, rx, ry, rz, d)
        print(os.path.basename(p), json.dumps(r, ensure_ascii=False))
    # determinizm: pary tego samego pliku przy tej samej częstotliwości
    keys = list(runs)
    det = {}
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a, b = runs[keys[i]], runs[keys[j]]
            if a[4]["series"] != b[4]["series"] or a[4]["rate"] != b[4]["rate"]:
                continue
            lo, hi = max(a[0][0], b[0][0]), min(a[0][-1], b[0][-1])
            tg = np.round(np.arange(lo, hi, 0.01), 4)
            dw = np.max(np.abs(np.stack([np.interp(tg, a[0], a[k]) - np.interp(tg, b[0], b[k]) for k in (1, 2, 3)])), axis=0)
            pa = {round(x[0], 3): x[1:4] for x in a[4]["publikacje"]}
            pb = {round(x[0], 3): x[1:4] for x in b[4]["publikacje"]}
            com = set(pa) & set(pb)
            det[f"{keys[i]} vs {keys[j]}"] = {
                "max_abs_dw": round(float(dw.max()), 5), "p99_abs_dw": round(float(np.percentile(dw, 99)), 5),
                "prog_0p02_ok": bool(dw.max() <= 0.02),
                "publikacje_n_a_b": [len(pa), len(pb)], "publikacje_wspolne_t": len(com),
                "publikacje_t_sim_identyczne_frac": round(len(com) / max(len(pa), 1), 4)}
            print("DET", keys[i], keys[j], det[f"{keys[i]} vs {keys[j]}"])
    json.dump({"przebiegi": out, "determinizm": det}, open(sys.argv[1], "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
