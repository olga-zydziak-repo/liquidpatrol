#!/usr/bin/env python3
"""results/WK3_RECON/tools/wk3_wind_rekon.py — odtworzenie chwilowego wiatru z ruchu ciała-sondy.

Prawo siły zmierzone w RECON_WK2 §R1: F = m·f(s)·(w − v) dla ogniwa z enable_wind; dla sondy (masa 1 kg,
bez grawitacji, jedyna siła = wiatr) a = f(s)·(w − v) ⇒ w = v + a/f(s). f(s) wyznaczany z przebiegu
STAŁEGO wiatru (probe_const: w ≡ 2.0 m/s z wind_info) jako stała relaksacji v → w: v(t) = w(1 − e^{−f t}).
v, a z poz 100 Hz różnicami centralnymi i wygładzeniem średnią ruchomą (okno 9 próbek = 0.09 s).
Wyjście: przebieg |w_h|(t), kierunek (deg, 0 = +x ENU), statystyki (średnia, min, max, okres z FFT, faza
sinusa przez dopasowanie MNK przy znanym okresie z SDF).

Użycie: wk3_wind_rekon.py <probe.json> <f_s> [--period P] [--out out.json]
"""
import argparse
import json

import numpy as np


def rekon(poses, f):
    P = np.array(poses, float)
    P = P[np.argsort(P[:, 0])]
    _, idx = np.unique(P[:, 0], return_index=True)
    P = P[idx]
    t, x, y = P[:, 0], P[:, 1], P[:, 2]
    k = 9
    ker = np.ones(k) / k
    def d(u):
        du = np.gradient(u, t)
        return np.convolve(du, ker, mode="same")
    vx, vy = d(x), d(y)
    ax, ay = d(vx), d(vy)
    wx, wy = vx + ax / f, vy + ay / f
    sl = slice(k, len(t) - k)
    return t[sl], wx[sl], wy[sl], vx[sl], vy[sl]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("probe"); ap.add_argument("f", type=float)
    ap.add_argument("--period", type=float, default=None); ap.add_argument("--out", default=None)
    a = ap.parse_args()
    d = json.load(open(a.probe))
    t, wx, wy, vx, vy = rekon(d["sonda_ciala_t_x_y_z"], a.f)
    m = np.hypot(wx, wy)
    ang = np.degrees(np.arctan2(wy, wx))
    res = {"probe": a.probe, "f_s": a.f, "n": int(len(t)), "t_od_do": [float(t[0]), float(t[-1])],
           "w_mag_srednia": round(float(m.mean()), 4), "w_mag_min": round(float(m.min()), 4),
           "w_mag_max": round(float(m.max()), 4), "w_mag_std": round(float(m.std()), 4),
           "kier_sredni_deg": round(float(ang.mean()), 2), "kier_min_deg": round(float(ang.min()), 2),
           "kier_max_deg": round(float(ang.max()), 2),
           "wind_info_bazowy": d["probki_t_vx_vy_vz"][0][1:] if d["probki_t_vx_vy_vz"] else None}
    if a.period:
        for nm, sig in (("mag", m), ("kier", ang)):
            A = np.vstack([np.ones_like(t), np.sin(2 * np.pi * t / a.period), np.cos(2 * np.pi * t / a.period)]).T
            c, *_ = np.linalg.lstsq(A, sig, rcond=None)
            amp = float(np.hypot(c[1], c[2])); ph = float(np.degrees(np.arctan2(c[2], c[1])))
            resid = float(np.std(sig - A @ c))
            res[f"sin_{nm}"] = {"srednia": round(float(c[0]), 4), "amplituda": round(amp, 4),
                                "faza_deg_wzgl_sin_t_sim": round(ph, 1), "resid_std": round(resid, 4)}
    # okres dominujący (FFT) magnitudy
    if len(t) > 64:
        tt = np.linspace(t[0], t[-1], len(t)); mm = np.interp(tt, t, m) - m.mean()
        F = np.abs(np.fft.rfft(mm)); fr = np.fft.rfftfreq(len(tt), tt[1] - tt[0])
        i = int(np.argmax(F[1:]) + 1); res["okres_dominujacy_mag_s"] = round(float(1 / fr[i]), 3)
    print(json.dumps(res, ensure_ascii=False))
    if a.out:
        res["przebieg_t_w_kier"] = [[round(float(a_), 3), round(float(b), 4), round(float(c_), 2)]
                                    for a_, b, c_ in zip(t[::5], m[::5], ang[::5])]
        json.dump(res, open(a.out, "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
