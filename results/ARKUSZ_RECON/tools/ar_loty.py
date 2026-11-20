#!/usr/bin/env python3
"""results/ARKUSZ_RECON/tools/ar_loty.py — dane lotów do R1.1 (PROMPT_ARKUSZ_S0 §3.1; 0 bootów).

15 lotów pl_dane.loty() (cache results/PETLA_RECON/dane, READ-ONLY), replay sieci pl_siec.replay (stan po ticku h, cechy x,
komenda v). Tick misji: misja > 0 (pl_dane: faza approach/hold/orbit, bez zejścia, ALLOW) ∧ krok sieci wykonany ∧ t − t(i0) ≥ 30 s,
i0 = pierwszy krok sieci. Zapis loty.npz: x, h, h0 (stan przed krokiem), c (komenda sieci), lot, tick, t, d_gt (prawdziwy dystans).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ar_wspolne as AW                                  # noqa: E402
import pl_dane as PD                                     # noqa: E402
import pl_siec as PS                                     # noqa: E402

TEST = ("p03", "p07", "p09", "p12", "p13")


def zbierz():
    zb = {k: [] for k in ("x", "h", "h0", "c", "lot", "tick", "t", "d_gt", "faza")}
    nazwy = []
    for li, d in enumerate(PD.loty()):
        L = PD.wczytaj(d)
        R = PS.replay(L)
        i0 = int(np.argmax(R["infer"]))
        tt = L["t"] - L["t"][i0]
        h0 = np.vstack([np.zeros((1, AW.H)), R["h"][:-1]])
        m = (L["misja"] > 0) & R["infer"] & (tt >= 30.0) & (np.arange(len(tt)) >= i0)
        nazwy.append(str(L["nazwa"]))
        zb["x"].append(R["x"][m]); zb["h"].append(R["h"][m]); zb["h0"].append(h0[m]); zb["c"].append(R["v"][m])
        zb["lot"].append(np.full(m.sum(), li)); zb["tick"].append(L["tick"][m]); zb["t"].append(tt[m])
        zb["d_gt"].append(np.hypot(*(L["intr"][m][:, :2] - L["gt"][m][:, :2]).T)); zb["faza"].append(L["faza"][m])
        print(nazwy[-1], int(m.sum()), flush=True)
    out = {k: np.concatenate(v) for k, v in zb.items()}
    out["nazwy"] = np.array(nazwy)
    np.savez(os.path.join(AW.OUT, "loty.npz"), **out)
    print("razem", len(out["t"]))


if __name__ == "__main__":
    zbierz()
