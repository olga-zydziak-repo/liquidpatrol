#!/usr/bin/env python3
"""results/KOTW_RECON/r2/tools/kotw2_yaw.py — R2′: rozdzielenie biasu yaw (EKF heading − GT yaw) na artefakt dopasowania
czasu i błąd estymatora. Kopia podejścia results/KOTW_RECON/tools/kotw_yaw.py (nietknięty), zmiany: heading EKF
INTERPOLOWANY liniowo (po rozwinięciu kąta) na mono próbki GT zamiast najbliższego rekordu; prędkość yaw z GT (różnica
centralna); w oknie sprzed cięcia (20 s, GNSS zdrowy) regresja err = b + L·ψ̇ (L = opóźnienie [s], b = stały bias);
w kontynuacji residuum err − L·ψ̇ (bias b jest prawdziwym błędem kursu, którego używa poprawka — zostaje w budżecie).
Użycie: kotw2_yaw.py <katalog_bootu> ...   → JSON na stdout
"""
import json, math, os, sys
import numpy as np


def load(p, t):
    return [json.loads(l) for l in open(p) if f'"t": "{t}"' in l]


out = {}
for d in sys.argv[1:]:
    w = json.load(open(os.path.join(d, "wyniki_s4.json")))["epizody"][0]
    tc, tl = w["t_cut"], w["t_land"]
    tr = os.path.join(d, "trace.jsonl")
    ek = [e for e in load(tr, "ekf") if "heading" in e]
    gt = [g for g in load(tr, "gt") if "qw" in g]
    em = np.array([e["mono"] for e in ek]); eh = np.unwrap(np.array([e["heading"] for e in ek]))
    gm = np.array([g["mono"] for g in gt]); gsim = np.array([g["sim"] for g in gt])
    yaw = np.unwrap(np.array([math.pi / 2 - math.atan2(2 * (g["qw"] * g["qz"] + g["qx"] * g["qy"]),
                                                       1 - 2 * (g["qy"] ** 2 + g["qz"] ** 2)) for g in gt]))
    ok = (gm >= em[0]) & (gm <= em[-1])
    hi = np.interp(gm, em, eh)
    err = np.degrees((hi - yaw + np.pi) % (2 * np.pi) - np.pi)
    rate = np.degrees(np.gradient(yaw, gm))
    pre = ok & (gsim >= tc - 20) & (gsim < tc)
    kon = ok & (gsim >= tc) & (gsim <= tl)
    A = np.vstack([np.ones(pre.sum()), rate[pre]]).T
    (b, L), *_ = np.linalg.lstsq(A, err[pre], rcond=None)
    res_pre = err[pre] - L * rate[pre]
    res_kon = err[kon] - L * rate[kon]
    s = lambda v: {"mean": round(float(v.mean()), 2), "min": round(float(v.min()), 2), "max": round(float(v.max()), 2),
                   "absmax": round(float(np.abs(v).max()), 2)}
    out[os.path.basename(d)] = {"L_s": round(float(L), 4), "b_deg": round(float(b), 2),
                                "rate_pre_absmax_dps": round(float(np.abs(rate[pre]).max()), 1),
                                "surowy_pre": s(err[pre]), "residuum_pre": s(res_pre),
                                "surowy_kont": s(err[kon]), "residuum_kont": s(res_kon),
                                "dryf_kont_wzgl_b": s(res_kon - b)}
print(json.dumps(out, ensure_ascii=False, indent=1))
