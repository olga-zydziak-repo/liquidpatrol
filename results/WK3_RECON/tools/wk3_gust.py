#!/usr/bin/env python3
"""results/WK3_RECON/tools/wk3_gust.py — R3: wiatr zmienny widziany PRZEZ DRONA (boot nauczyciela), 0 miar misji.

Dane: ulog (vehicle_attitude, vehicle_local_position — wczytanie i bilans jak wk2_k.py 09e4b440, import),
demo.jsonl (okna phase == "orbit"). Most czasu t_sim = ulog_us·1e-6 (RECON_WK §R3).
Bilans sił poziomych: D = a_h − (T/m)·t_h (wk2_k), model oporu D = −k·(v − w).
Litera wiatru (RECON_WK3 §R1, zmierzona sondą): ENU, kierunek średniej +x (wschód):
  |w|(t) = W0·(1 + A·sin(2π t/Pm)),  θ(t) = Ad·sin(2π t/Pd) [deg],  w_ENU = |w|(cos θ, sin θ)
  ⇒ w_NED = (w_N, w_E) = (|w| sin θ, |w| cos θ).
Wyjście:
  (1) k przy wietrze z litery SDF: MNK D = −k(v − w_sdf) (bez wyrazu wolnego) i z wyrazem wolnym;
      k przy założeniu wiatru STAŁEGO = średnia (metoda wk2_k z wyrazem wolnym) — „czy porywy zmieniają k";
  (2) wiatr odtworzony przez drona: w_dr = v + D/k_ref (k_ref = 0.4939, kalibracja WK2), dopasowanie sinusa
      |w_dr| przy okresie z SDF (średnia, amplituda, faza wzgl. sin(2π t_sim/P)) wobec litery;
  (3) odpowiedź prędkości drona: sinus przy okresie porywu w składowej E prędkości (wzdłuż wiatru średniego)
      — amplituda i opóźnienie fazy względem porywu;
  (4) przechył p50/p95/max w oknach orbity.
Użycie: wk3_gust.py <boot_dir> <W0> <A> <Pm> <Ad> <Pd> [--out out.json]
"""
import argparse
import bisect
import json
import os
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "results", "WK2_RECON", "tools"))
from r02.mti import quat_to_R  # noqa: E402
from wk2_k import G, V_MIN, load, orbit_windows  # noqa: E402

K_REF = 0.4939


def sinfit(t, y, P):
    A = np.vstack([np.ones_like(t), np.sin(2 * np.pi * t / P), np.cos(2 * np.pi * t / P)]).T
    c, *_ = np.linalg.lstsq(A, y, rcond=None)
    return {"srednia": round(float(c[0]), 4), "amplituda": round(float(np.hypot(c[1], c[2])), 4),
            "faza_deg": round(float(np.degrees(np.arctan2(c[2], c[1]))), 1),
            "resid_std": round(float(np.std(y - A @ c)), 4)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("boot"); ap.add_argument("W0", type=float); ap.add_argument("A", type=float)
    ap.add_argument("Pm", type=float); ap.add_argument("Ad", type=float); ap.add_argument("Pd", type=float)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    att, lp = load(os.path.join(a.boot, "boot.ulg"))
    ats = att[0]
    T, V, D, TILT = [], [], [], []
    for lo, hi in orbit_windows(os.path.join(a.boot, "demo.jsonl")):
        m = (lp["timestamp"] >= lo * 1e6) & (lp["timestamp"] <= hi * 1e6)
        for i in np.where(m)[0]:
            v = np.array([lp["vx"][i], lp["vy"][i]])
            j = min(max(bisect.bisect_left(ats, lp["timestamp"][i]), 0), len(ats) - 1)
            R = quat_to_R(att[1][j]); th = -R[:, 2]
            if th[2] > -0.5:
                continue
            Tm = (lp["az"][i] - G) / th[2]
            D.append(np.array([lp["ax"][i], lp["ay"][i]]) - Tm * th[:2]); V.append(v)
            T.append(lp["timestamp"][i] / 1e6); TILT.append(float(np.degrees(np.arccos(np.clip(R[2, 2], -1, 1)))))
    T, V, D = np.array(T), np.array(V), np.array(D)
    mag = a.W0 * (1 + a.A * np.sin(2 * np.pi * T / a.Pm))
    th = np.radians(a.Ad * np.sin(2 * np.pi * T / a.Pd)) if a.Ad else np.zeros_like(T)
    Wsdf = np.stack([mag * np.sin(th), mag * np.cos(th)], 1)           # NED (N, E)
    rel = V - Wsdf
    k_sdf = float(-np.sum(D * rel) / np.sum(rel * rel))
    n = len(T)
    Ab = np.zeros((2 * n, 3)); y = np.concatenate([D[:, 0], D[:, 1]])
    Ab[:n, 0] = -rel[:, 0]; Ab[n:, 0] = -rel[:, 1]; Ab[:n, 1] = 1; Ab[n:, 2] = 1
    sol, *_ = np.linalg.lstsq(Ab, y, rcond=None)
    Ac = Ab.copy(); Ac[:n, 0] = -V[:, 0]; Ac[n:, 0] = -V[:, 1]               # wiatr „stały" (wk2_k)
    solc, *_ = np.linalg.lstsq(Ac, y, rcond=None)
    w_dr = V + D / K_REF
    sp = np.hypot(V[:, 0], V[:, 1]); okv = sp >= V_MIN
    tl = np.sort(np.array(TILT))
    res = {"boot": os.path.relpath(a.boot, ROOT), "n": n,
           "litera_sdf": {"W0": a.W0, "A_frac": a.A, "Pm_s": a.Pm, "Ad_deg": a.Ad, "Pd_s": a.Pd},
           "k_przy_wietrze_z_litery_bez_wyrazu": round(k_sdf, 4),
           "k_przy_wietrze_z_litery_z_wyrazem": round(float(sol[0]), 4),
           "bias_NE_przy_literze": [round(float(sol[1]), 4), round(float(sol[2]), 4)],
           "k_przy_zalozeniu_wiatru_stalego": round(float(solc[0]), 4),
           "bias_NE_wiatr_staly": [round(float(solc[1]), 4), round(float(solc[2]), 4)],
           "wiatr_odtworzony_przez_drona_mag": sinfit(T, np.hypot(w_dr[:, 0], w_dr[:, 1]), a.Pm),
           "wiatr_litera_mag_w_tych_chwilach": sinfit(T, mag, a.Pm),
           "residuum_wiatru_odtw_vs_litera_m_s": {
               "p50": round(float(np.median(np.hypot(*(w_dr - Wsdf).T))), 4),
               "p95": round(float(np.percentile(np.hypot(*(w_dr - Wsdf).T), 95)), 4)},
           "odpowiedz_predkosci_E_przy_okresie_porywu": sinfit(T, V[:, 1], a.Pm),
           "przechyl_orbita_p50_p95_max": [round(float(np.median(tl)), 2),
                                           round(float(tl[int(0.95 * (len(tl) - 1))]), 2), round(float(tl[-1]), 2)],
           "frac_probek_v_ponizej_V_MIN": round(float(1 - okv.mean()), 4)}
    if a.Ad:
        thd = np.degrees(np.arctan2(w_dr[:, 0], w_dr[:, 1]))              # kierunek względem +E (ENU +x)
        res["wiatr_odtworzony_kierunek"] = sinfit(T, thd, a.Pd)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    if a.out:
        json.dump(res, open(a.out, "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
