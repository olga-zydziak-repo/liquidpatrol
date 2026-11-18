#!/usr/bin/env python3
"""results/PETLA_RECON/tools/pl_r2.py — R2: replay 15 lotów i obwiednie (PROMPT_PETLA_S0 §4). Wyjście: results/PETLA_RECON/r2.json,
r2_wektory.npz (per tick misji: lot, t, cechy surowe, stan po ticku, komenda, d z cech, d prawdziwy, składowa ku celowi, błędy)."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pl_dane as PD                                     # noqa: E402
import pl_siec as PS                                     # noqa: E402

OUT = os.path.join(PD.ROOT, "results/PETLA_RECON")
TOL_REPLAY = 0.005                                       # m/s — próg P-PETLA-R1 (zaokrąglenie wejść logu do 1e-3 / 1e-4)


def main():
    W = {k: [] for k in ("lot", "t", "t_od_inf", "x", "h", "v", "d_cech", "d_gt", "ku", "rel_err", "etrk", "misja", "infer", "faza")}
    per = []
    for d in PD.loty():
        L = PD.wczytaj(d)
        R = PS.replay(L)
        inf = R["infer"]
        dv = np.abs(R["v"] - L["cmd"]).max(axis=1)
        mis = L["misja"].astype(bool)
        t_inf0 = L["t"][inf][0]
        rel = L["trk"][:, :2] - L["net"][:, :2]
        d_c = np.hypot(rel[:, 0], rel[:, 1])
        relgt = L["intr"][:, :2] - L["gt"][:, :2]
        d_g = np.hypot(relgt[:, 0], relgt[:, 1])
        u = rel / np.maximum(d_c[:, None], 1e-9)
        ku = (R["v"][:, :2] * u).sum(1)
        rel_err = np.hypot(*(rel - relgt).T)
        e_trk = np.hypot(*((L["net"][:, :2] + rel) - L["intr"][:, :2]).T)      # pozycja intruza w ramie sieci − prawda
        per.append({"lot": str(L["nazwa"]), "ticki": int(len(inf)), "infer": int(inf.sum()), "misja": int(mis.sum()),
                    "misja_infer": int((mis & inf).sum()), "dv_max": float(dv.max()), "dv_max_infer": float(dv[inf].max()),
                    "n_ponad_tol": int((dv > TOL_REPLAY).sum()), "d_cech_max_misja": float(np.nanmax(d_c[mis & inf])),
                    "d_gt_max_misja": float(np.nanmax(d_g[mis & inf]))})
        sel = inf
        for k, val in (("lot", np.full(len(inf), len(per) - 1)), ("t", L["t"]), ("t_od_inf", L["t"] - t_inf0), ("x", R["x"]), ("h", R["h"]),
                       ("v", R["v"]), ("d_cech", d_c), ("d_gt", d_g), ("ku", ku), ("rel_err", rel_err), ("etrk", e_trk),
                       ("misja", mis), ("infer", inf), ("faza", L["faza"])):
            W[k].append(val[sel])
        print(per[-1], flush=True)
    W = {k: np.concatenate(v) for k, v in W.items()}
    np.savez_compressed(os.path.join(OUT, "r2_wektory.npz"), **W, loty=np.array([p["lot"] for p in per]))
    m = W["misja"].astype(bool)
    out = {"per_lot": per, "ticki_infer": int(W["infer"].sum()), "ticki_misji_infer": int(m.sum()),
           "ticki_misji_wszystkie": int(sum(PD.wczytaj(d)["misja"].sum() for d in PD.loty())),
           "dv_max_infer": float(max(p["dv_max_infer"] for p in per)), "n_ponad_tol_0p005": int(sum(p["n_ponad_tol"] for p in per)),
           "tol": TOL_REPLAY}
    # (b) pościg w poziomie: składowa ku celowi wg dystansu z cech, tylko misja
    b = {}
    for lo, hi in ((10.0, 10.5), (10.5, 11.0), (11.0, 11.5), (11.5, 12.0)):
        s = m & (W["d_cech"] >= lo) & (W["d_cech"] < hi)
        b[f"{lo}-{hi}"] = {"n": int(s.sum()), "min_ku": float(W["ku"][s].min()) if s.any() else None,
                           "n_ku_lt_1": int((W["ku"][s] < 1.0).sum())}
    out["b_misja"] = b
    out["d_cech_max_misja"], out["d_gt_max_misja"] = float(W["d_cech"][m].max()), float(np.nanmax(W["d_gt"][m]))
    nm = (~m) & W["infer"].astype(bool)
    bz = {}
    for lo, hi in ((11.0, 11.5), (11.5, 13.0), (13.0, 15.0)):
        s = nm & (W["d_cech"] >= lo) & (W["d_cech"] < hi)
        bz[f"{lo}-{hi}"] = {"n": int(s.sum()), "min_ku": float(W["ku"][s].min()) if s.any() else None}
    out["b_poza_misja"] = bz
    json.dump(out, open(os.path.join(OUT, "r2.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: out[k] for k in out if k != "per_lot"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
