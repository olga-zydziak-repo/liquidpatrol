#!/usr/bin/env python3
"""results/NAD2_RECON/tools/nad2_r4.py — PROMPT_NAD2_S0 R4: zrywy błędu EKF przy hamowaniu (opis mechanizmu, bez strojenia; 0 bootów).

Serie przekroczeń wskazane przez CC (sekundy od t_inj_sim). Dla każdej serii okno [t0 − 1 s, t1 + 1 s] i porównanie z bazą
(całe okno bez GNSS tego bootu): prędkość EKF (vehicle_local_position vx, vy) wobec prędkości GT (różniczka GT), błąd
prędkości |v_EKF − v_GT|, przyspieszenie poziome GT, prędkość kątowa (vehicle_angular_velocity), fuzja przepływu
(estimator_aid_src_optical_flow: fused, innovation_rejected, test_ratio, innowacja; estimator_optical_flow_vel: vel_ne wobec
v_GT). Predyktor (opisowo): na całym oknie bez GNSS 12 cięć — częstość zrywu (|Δe| w 0.25 s > 0.4 m) warunkowo na
przesłankach (|a| ≥ 2, |ω| ≥ próg, odrzucona innowacja przepływu, test_ratio ≥ 1).
Wyjście: results/NAD2_RECON/r4_zrywy.json.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nad2_dane as D

SERIE = {"c08_s01": [(28.3, 28.9), (64.3, 64.5)], "c08_s02": [(8.4, 8.6)],
         "c10_s01": [(5.2, 5.6), (51.2, 51.4), (59.4, 60.0), (72.4, 72.4)],
         "c10_s02": [(32.7, 33.3), (80.5, 80.9), (88.9, 88.9)],
         "c11_s02": [(87.3, 87.5), (90.3, 90.3), (103.1, 103.5)]}
DT = 0.02


def sygnaly(b, t):
    """Sygnały na siatce t (sim)."""
    gp = b.gt(t)
    gv = np.gradient(gp[:, :2], DT, axis=0)
    ga = np.linalg.norm(np.gradient(gv, DT, axis=0), axis=1)
    ga = np.convolve(ga, np.ones(5) / 5, mode="same")
    ev = np.stack([np.interp(t, b.vts, b.vv[:, i]) for i in range(2)], 1)
    e = b.ekf_w(t) - gp
    of = b.u["estimator_aid_src_optical_flow"]
    ofv = b.u["estimator_optical_flow_vel"]
    av = b.u["vehicle_angular_velocity"]
    near = lambda tt, x: x[np.clip(np.searchsorted(tt, t), 0, len(tt) - 1)]
    w = np.linalg.norm(np.stack([np.interp(t, av["timestamp"], av[f"xyz[{i}]"]) for i in range(3)], 1), axis=1)
    tr = np.maximum(near(of["timestamp"], of["test_ratio[0]"]), near(of["timestamp"], of["test_ratio[1]"]))
    rej = near(of["timestamp"], of["innovation_rejected"]).astype(float)
    fus = near(of["timestamp"], of["fused"]).astype(float)
    inn = np.hypot(near(of["timestamp"], of["innovation[0]"]), near(of["timestamp"], of["innovation[1]"]))
    fv = np.stack([np.interp(t, ofv["timestamp"], ofv[f"vel_ne[{i}]"]) for i in range(2)], 1)
    vmag = np.linalg.norm(gv, axis=1)
    hamuje = np.gradient(vmag, DT) < 0
    return {"e": e, "gv": gv, "ga": ga, "dv": np.linalg.norm(ev - gv, axis=1), "w": w, "tr": tr, "rej": rej, "fus": fus,
            "inn": inn, "dv_flow": np.linalg.norm(fv - gv, axis=1), "v": vmag, "hamuje": hamuje}


def opis(s, sel):
    f = lambda x: round(float(x), 3)
    return {"dv_ekf_gt_max": f(s["dv"][sel].max()), "dv_ekf_gt_p50": f(np.median(s["dv"][sel])), "a_gt_max": f(s["ga"][sel].max()),
            "v_gt_max": f(s["v"][sel].max()), "w_max_rad_s": f(s["w"][sel].max()), "test_ratio_max": f(s["tr"][sel].max()),
            "frac_odrzucona": f(s["rej"][sel].mean()), "frac_fuzja": f(s["fus"][sel].mean()), "innowacja_max": f(s["inn"][sel].max()),
            "dv_przeplyw_gt_max": f(s["dv_flow"][sel].max()), "frac_hamuje": f(s["hamuje"][sel].mean())}


def main():
    out = {"serie": {}, "baza": {}, "predyktor": {}}
    pool = {k: [] for k in ("zryw", "a2", "w", "rej", "tr1", "hamuje")}
    for n in D.CIECIA_S4:
        b = D.Boot(n)
        t1 = b.zp[b.denial["episode_id"]]
        t = np.arange(b.t_flag, t1, DT)
        s = sygnaly(b, t)
        out["baza"][n] = opis(s, np.ones(t.size, bool))
        L = int(round(0.25 / DT))
        de = np.zeros(t.size)
        de[:-L] = np.linalg.norm(s["e"][L:, :2] - s["e"][:-L, :2], axis=1)
        pool["zryw"].append(de > 0.4); pool["a2"].append(s["ga"] >= 2); pool["w"].append(s["w"] >= 0.5)
        pool["rej"].append(s["rej"] > 0); pool["tr1"].append(s["tr"] >= 1); pool["hamuje"].append(s["hamuje"])
        for (a, z) in SERIE.get(n, []):
            sel = (t >= b.t_inj + a - 1) & (t <= b.t_inj + z + 1)
            core = (t >= b.t_inj + a) & (t <= b.t_inj + z + 0.2)
            o = opis(s, sel)
            o["zryw_dE_025_max"] = round(float(de[core].max()), 3) if core.any() else None
            out["serie"][f"{n}@{a}-{z}"] = o
            print(n, a, z, o, flush=True)
    P = {k: np.concatenate(v) for k, v in pool.items()}
    base = float(P["zryw"].mean())
    for k in ("a2", "w", "rej", "tr1", "hamuje"):
        c = P[k]
        out["predyktor"][k] = {"udzial_chwil": round(float(c.mean()), 4), "P_zryw_gdy": round(float(P["zryw"][c].mean()), 4) if c.any() else None,
                               "P_zryw_gdy_nie": round(float(P["zryw"][~c].mean()), 4), "pokrycie_zrywow": round(float(c[P["zryw"]].mean()), 4) if P["zryw"].any() else None}
    out["predyktor"]["_baza_P_zryw"] = round(base, 5)
    out["predyktor"]["_def"] = "zryw ⇔ |e(t+0.25)−e(t)| poziomo > 0.4 m; ω ≥ 0.5 rad/s; a ≥ 2 m/s²; rej = innowacja przepływu odrzucona; tr1 = test_ratio ≥ 1"
    json.dump(out, open(os.path.join(D.OUT, "r4_zrywy.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(out["predyktor"], ensure_ascii=False))


if __name__ == "__main__":
    main()
