#!/usr/bin/env python3
"""results/PETLA_RECON/tools/pl_r4a.py — R4 bez napędu (PROMPT_PETLA_S0 §6, pierwsza część; 0 bootów).

Na stanach misji z R2 (tick inferencji ≥ 30 s od pierwszej inferencji; stan przed tickiem = stan po poprzednim ticku lotu):
  - zależność komendy pionowej sieci vd od własnej prędkości pionowej z wejścia (own_vd): korelacja, nachylenie MNK,
    mediana |vd − own_vd|;
  - czułość jednokrokowa: różnica skończona ∂vd/∂own_vd (δ = 0.01 m/s) i ∂vd/∂rel_z (δ = 0.01 m), stan przed tickiem;
  - czułość ustalona: 400 stanów losowych (ziarno 0); wejście zamrożone, sieć iterowana 400 kroków (20 s) od stanu przed tickiem,
    vd_ss(rel_z + 0.1) − vd_ss(rel_z) / 0.1 i to samo dla own_vd; „znak odwrotny” = ∂vd_ss/∂rel_z < 0 (dron wyżej ⇒ komenda
    mniej w dół; NED: rel_z = z_cel − z_dron, większe = dron wyżej);
  - tablice odpowiedzi ustalonej (stan zerowy, 400 kroków, wiek = mediana lotów): pościg po prostej (cel 9.2 m, namiar co 30°,
    prędkość własna 1 m/s ku celowi, own_vd 0) i orbita (cel 8.0 m, prędkość styczna 2 m/s, oba kierunki), rel_z 1–8 m.
Wyjście: results/PETLA_RECON/r4a.json, r4a_wektory.npz.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pl_siec as PS                                     # noqa: E402
import pl_r2b as R2B                                     # noqa: E402

OUT = os.path.join(PS.ROOT, "results/PETLA_RECON")
N_SS = 400


def ustalona(X, h0, n=N_SS):
    h = h0.copy()
    xs = PS.norm(X)
    for _ in range(n):
        v, h = PS.krok(xs, h)
    return v


def main():
    W = dict(np.load(os.path.join(OUT, "r2_wektory.npz"), allow_pickle=True))
    hp = R2B.h_prev(W)
    m = W["misja"].astype(bool) & (W["t_od_inf"] >= 30.0)
    X, Hp, V = W["x"][m], hp[m], W["v"][m]
    vd, ovd = V[:, 2], X[:, 5]
    out = {"n_stanow": int(m.sum()), "korelacja_vd_ownvd": float(np.corrcoef(vd, ovd)[0, 1]),
           "nachylenie_vd_ownvd": float(np.polyfit(ovd, vd, 1)[0]), "mediana_abs_vd_minus_ownvd": float(np.median(np.abs(vd - ovd)))}
    v0, _ = PS.krok(PS.norm(X), Hp)
    sens = {}
    for nm, j, dl in (("own_vd", 5, 0.01), ("rel_z", 2, 0.01)):
        Xd = X.copy(); Xd[:, j] += dl
        vdd, _ = PS.krok(PS.norm(Xd), Hp)
        s = (vdd[:, 2] - v0[:, 2]) / dl
        sens[nm] = {"mediana": float(np.median(s)), "p5": float(np.percentile(s, 5)), "p95": float(np.percentile(s, 95)),
                    "udzial_ujemnych": float((s < 0).mean())}
        np.save(os.path.join(OUT, f"r4a_sens_{nm}.npy"), s)
    out["czulosc_jednokrokowa"] = sens
    out["stala_czasowa_relz_s"] = float(1.0 / sens["rel_z"]["mediana"]) if sens["rel_z"]["mediana"] > 0 else None
    rng = np.random.default_rng(0)
    idx = rng.choice(len(X), 400, replace=False)
    Xs, Hs = X[idx], Hp[idx]
    base = ustalona(Xs, Hs)
    ss = {}
    for nm, j, dl in (("rel_z", 2, 0.1), ("own_vd", 5, 0.1)):
        Xd = Xs.copy(); Xd[:, j] += dl
        s = (ustalona(Xd, Hs)[:, 2] - base[:, 2]) / dl
        ss[nm] = {"mediana": float(np.median(s)), "udzial_odwrotny": float((s < 0).mean()) if nm == "rel_z" else None,
                  "p5": float(np.percentile(s, 5)), "p95": float(np.percentile(s, 95))}
    out["czulosc_ustalona_400"] = ss
    np.savez_compressed(os.path.join(OUT, "r4a_wektory.npz"), idx=idx, X=Xs, H=Hs, base=base)
    wiek = float(json.load(open(os.path.join(OUT, "r2b.json")))["wiek_tracka"]["mediana"])
    nam = np.arange(-180, 180, 30)
    rz = np.arange(1.0, 8.01, 1.0)
    tab_p, tab_o = {}, {}
    for geom in ("poscig", "orbita_ccw", "orbita_cw"):
        rows = []
        for b in nam:
            a = np.radians(b)
            u = np.array([np.cos(a), np.sin(a)])
            for z in rz:
                if geom == "poscig":
                    rel, vh = 9.2 * u, 1.0 * u
                else:
                    t = np.array([-u[1], u[0]]) * (1 if geom == "orbita_ccw" else -1)
                    rel, vh = 8.0 * u, 2.0 * t
                rows.append([rel[0], rel[1], z, vh[0], vh[1], 0.0, wiek, 1.0])
        Xg = np.array(rows)
        v = ustalona(Xg, np.zeros((len(Xg), PS.H)))
        T = v[:, 2].reshape(len(nam), len(rz))
        dT = np.diff(T, axis=1)
        (tab_p if geom == "poscig" else tab_o)[geom] = {"namiary_deg": nam.tolist(), "rel_z": rz.tolist(), "vd_ss": T.round(4).tolist(),
                                                        "namiary_vd_maleje_z_rel_z": [int(nam[i]) for i in range(len(nam)) if (dT[i] < 0).all()],
                                                        "namiary_wznoszenie_przy_rel_z_ge_4": [int(nam[i]) for i in range(len(nam)) if (T[i, 3:] < 0).all()]}
    out["tablica_poscig"] = tab_p
    out["tablica_orbita"] = tab_o
    json.dump(out, open(os.path.join(OUT, "r4a.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if not k.startswith("tablica")}, ensure_ascii=False, indent=1))
    for g, t in {**tab_p, **tab_o}.items():
        print(g, "vd maleje z rel_z:", t["namiary_vd_maleje_z_rel_z"], "| wznoszenie przy rel_z≥4:", t["namiary_wznoszenie_przy_rel_z_ge_4"])


if __name__ == "__main__":
    main()
