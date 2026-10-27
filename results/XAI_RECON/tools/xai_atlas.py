#!/usr/bin/env python3
"""results/XAI_RECON/tools/xai_atlas.py — atlas aktywacji NCP-20 + kontrast GRU
(PROMPT_XAI_S0 §R2/§R3/§R4). Wymaga kotwicy R1 PASS (xai_anchor.json).

Korpus: pełna siatka LIQ 48×2 ramiona — indeks epizodów Z WERDYKTAMI po
erratum = results/POSCIG_RECON/erratum_sweep.json (cases LIQ:*, judge_filtered)
+ próbka OPS (FANTOM r1_V2, DEMO_C d1_proba — net_fantom, percepcja prawdziwa).

LISTA POMIARÓW ZAMKNIĘTA (prereg §R2, metody nazwane):
 (a) separowalność FAZ approach/orbit (tylko ticki inferencji; hold wykluczony
     — stan zamrożony, sieć nie widzi wejść): dwuklasowy współczynnik Fishera
     J = (wᵀΔμ)²/(wᵀS_w w), w = pinv(S_w)Δμ; trafność najbliższego centroidu
     (split: epizody parzyste→train / nieparzyste→test po indeksie siatki);
     silhouette na podpróbce 4000 (seed 0, euklides).
 (b) wymiar efektywny: PCA (SVD na scentrowanym h, ticki inferencji, pula
     ramienia) — liczba składowych na 90%/95% wariancji.
 (c) role neuronów: |Pearson| h_i × {8 cech znorm., d, cos(bearing),
     sin(bearing), y_vn, y_ve, y_vd}; per neuron max korelat; progi werdyktu:
     ≥0.8 czytelny / 0.5–0.8 częściowy / <0.5 splątany.
 (d) bramka czasu per neuron w czasie (CfC: gate=σ(Wt·bb+bt), models.py:133;
     GRU: bramka retencji z, models_liq.py:54 — obserwabla ANALOGICZNA, niuans
     w raporcie): średnie fazowe; skok na granicy approach→orbit = |mean gate
     [t,t+1s] − [t−1s,t]| vs baseline losowych okien wewnątrz fazy (50/epizod,
     seed 0); liczba neuronów ratio>2.
 (e) saliency chwilowe: Jacobian ∂y_raw/∂x_norm różnicą centralną eps=1e-4
     przy ZAMROŻONYM h (ścieżka rekurencyjna WYKLUCZONA — ograniczenie nazwane;
     y_raw = tanh·V_MAX przed clip_v), co 5. tick inferencji; średnie |J| per
     faza.
KONTRAST §R3: (a-c,e) na 48 lotach GRU; (b19) 19 epizodów przewagi
(NCP PASS ∧ GRU FAIL po erratum): CROSS-REPLAY open-loop — model GRU na
WEJŚCIACH zalogowanych lotu NCP (te same wejścia, zero sprzężenia) vs komendy
NCP; rozjazd |Δv| i kąt horyzontalny per faza/bin dystansu; kontrola = 29
epizodów zgodnych (oba PASS). Analiza OPISOWA (mechanizm-kandydat).

Wyjścia: xai_atlas_ncp.json, xai_atlas_gru.json, xai_proba_ops.json,
xai_kontrast.json + PNG w png/. Zero edycji istniejących.
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from xai_replay import load_eps, replay_episode, model_of, V_MAX

OUTD = os.path.join(ROOT, "results", "XAI_RECON")
PNGD = os.path.join(OUTD, "png")
RNG = np.random.RandomState(0)
XN = ["rel_x", "rel_y", "rel_z", "own_vn", "own_ve", "own_vd", "age", "valid"]
CORR_NAMES = XN + ["d", "cos_brg", "sin_brg", "y_vn", "y_ve", "y_vd"]


def liq_index():
    d = json.load(open(os.path.join(ROOT, "results", "POSCIG_RECON", "erratum_sweep.json")))
    idx = {"ncp": [], "gru": []}
    for c in d["cases"]:
        if not c["label"].startswith("LIQ"):
            continue
        arm = "ncp" if ":ncp:" in c["label"] else "gru"
        idx[arm].append({"sid": c["scenario_id"], "eid": c["episode_id"],
                         "dir": os.path.join(ROOT, c["dir"]),
                         "success": bool(c["judge_filtered"]["success_D6"]),
                         "fail_reasons": c["judge_filtered"]["fail_reasons"]})
    for a in idx:
        idx[a].sort(key=lambda e: e["sid"])
    return idx


def replay_case(case, arm, fantom=False):
    eps = load_eps(case["dir"])
    atts = [k for k in eps if k[0] == case["eid"]]
    k = max(atts)                                  # ostatni attempt = sędziowany
    rep = replay_episode(eps[k], arm, fantom=fantom)
    rep["sid"] = case["sid"]
    return rep


def pool(reps):
    """Pula ticków inferencji: H, GATE, X, Y, D, PH, EPI (indeks epizodu)."""
    Hs, Gs, Xs, Ys, Ds, Ps, Es = [], [], [], [], [], [], []
    for i, r in enumerate(reps):
        m = r["infer"]
        Hs.append(r["h"][m]); Gs.append(r["gate"][m]); Xs.append(r["x"][m])
        Ys.append(r["y"][m]); Ds.append(r["d"][m]); Ps.append(r["phase"][m])
        Es.append(np.full(int(m.sum()), i))
    return (np.concatenate(Hs), np.concatenate(Gs), np.concatenate(Xs),
            np.concatenate(Ys), np.concatenate(Ds), np.concatenate(Ps),
            np.concatenate(Es))


def fisher2(Ha, Ho):
    mu = Ha.mean(0) - Ho.mean(0)
    Sw = np.cov(Ha.T) * (len(Ha) - 1) + np.cov(Ho.T) * (len(Ho) - 1)
    Sw /= (len(Ha) + len(Ho) - 2)
    w = np.linalg.pinv(Sw) @ mu
    J = float((w @ mu) ** 2 / (w @ Sw @ w))
    return J


def silhouette(Z, lab, n_per_class=2000):
    """Silhouette na podpróbce ZBALANSOWANEJ (n/klasę, seed 0) — klasy 95/5
    unieważniałyby metrykę niezbalansowaną."""
    idx = []
    for c in np.unique(lab):
        j = np.where(lab == c)[0]
        idx.append(RNG.choice(j, size=min(n_per_class, len(j)), replace=False))
    i = np.concatenate(idx)
    Z, lab = Z[i], lab[i]
    D = np.sqrt(((Z[:, None, :] - Z[None, :, :]) ** 2).sum(-1))
    s = []
    for j in range(len(Z)):
        same = lab == lab[j]; same[j] = False
        a = D[j][same].mean() if same.any() else 0.0
        b = D[j][~same].mean()
        s.append((b - a) / max(a, b))
    return float(np.mean(s))


def separability(H, PH, EPI):
    m = np.isin(PH, ["approach", "orbit"])
    H, PH, EPI = H[m], PH[m], EPI[m]
    Ha, Ho = H[PH == "approach"], H[PH == "orbit"]
    if len(Ha) < 50 or len(Ho) < 50:
        return {"n_approach": int(len(Ha)), "n_orbit": int(len(Ho))}
    J = fisher2(Ha, Ho)
    tr = (EPI % 2 == 0)
    ca = H[tr & (PH == "approach")].mean(0)
    co = H[tr & (PH == "orbit")].mean(0)
    pred = np.where(np.linalg.norm(H[~tr] - ca, axis=1)
                    < np.linalg.norm(H[~tr] - co, axis=1), "approach", "orbit")
    rec = {c: float((pred[PH[~tr] == c] == c).mean()) for c in ("approach", "orbit")
           if (PH[~tr] == c).any()}
    sil = silhouette(H, PH)
    return {"n_approach": int(len(Ha)), "n_orbit": int(len(Ho)),
            "fisher_J": round(J, 3),
            "recall_approach": round(rec.get("approach", float("nan")), 4),
            "recall_orbit": round(rec.get("orbit", float("nan")), 4),
            "balanced_acc": round(float(np.mean(list(rec.values()))), 4),
            "silhouette_bal2k": round(sil, 3)}


def pca_dim(H):
    Hc = H - H.mean(0)
    s = np.linalg.svd(Hc, compute_uv=False)
    var = s ** 2 / (s ** 2).sum()
    cum = np.cumsum(var)
    return {"n_90": int(np.searchsorted(cum, 0.90) + 1),
            "n_95": int(np.searchsorted(cum, 0.95) + 1),
            "var_top5": [round(float(v), 4) for v in var[:5]]}


def roles(H, X, Y, D):
    brg = np.arctan2(X[:, 1], X[:, 0])     # bearing z cech znorm. (monotonia zachowana przy std>0)
    C = np.column_stack([X, D, np.cos(brg), np.sin(brg), Y])
    out = []
    kat = {"czytelny": 0, "czesciowy": 0, "splatany": 0}
    live = C.std(0) > 1e-9                 # 'valid'≡1 na tickach inferencji — zdegenerowana
    for i in range(H.shape[1]):
        r = np.array([abs(np.corrcoef(H[:, i], C[:, j])[0, 1]) if live[j] else np.nan
                      for j in range(C.shape[1])])
        j = int(np.nanargmax(r))
        v = float(r[j])
        k = "czytelny" if v >= 0.8 else ("czesciowy" if v >= 0.5 else "splatany")
        kat[k] += 1
        out.append({"neuron": i, "max_korelat": CORR_NAMES[j], "abs_r": round(v, 3),
                    "kategoria": k})
    return {"neurony": out, "kategorie": kat}


def gate_phase(reps, H_n):
    """(d): średnie fazowe bramki + skok na granicy approach→orbit vs baseline."""
    ga, go = [], []
    trans, base = [], []
    W = 20                                      # 1 s @20 Hz
    for r in reps:
        m = r["infer"]
        g, ph = r["gate"], r["phase"]
        ga.append(g[m & (ph == "approach")]); go.append(g[m & (ph == "orbit")])
        idx = np.where((ph[1:] == "orbit") & (ph[:-1] == "approach"))[0]
        if len(idx) and idx[0] >= W and idx[0] + W < len(ph):
            i = idx[0] + 1
            pre, post = g[i - W:i], g[i:i + W]
            if not (np.isnan(pre).any() or np.isnan(post).any()):
                trans.append(np.abs(np.nanmean(post, 0) - np.nanmean(pre, 0)))
        ii = np.where(m)[0]
        for _ in range(50):
            c = RNG.choice(ii[(ii >= W) & (ii < len(ph) - W)]) if len(ii) > 2 * W else None
            if c is None:
                break
            seg = ph[c - W:c + W]
            if (seg == seg[0]).all() and not np.isnan(g[c - W:c + W]).any():
                base.append(np.abs(g[c:c + W].mean(0) - g[c - W:c].mean(0)))
    ga, go = np.concatenate(ga), np.concatenate(go)
    tr = np.mean(trans, 0) if trans else np.full(H_n, np.nan)
    bs = np.mean(base, 0) if base else np.full(H_n, np.nan)
    ratio = tr / np.maximum(bs, 1e-9)
    return {"gate_mean_approach": [round(float(v), 3) for v in ga.mean(0)],
            "gate_mean_orbit": [round(float(v), 3) for v in go.mean(0)],
            "delta_faz_max": round(float(np.abs(ga.mean(0) - go.mean(0)).max()), 3),
            "n_przejsc": len(trans),
            "skok_granicy_ratio": [round(float(v), 2) for v in ratio],
            "n_neuronow_ratio_gt2": int((ratio > 2.0).sum())}, (ga, go, tr, bs)


def saliency(reps, arm):
    m = model_of(arm)
    eps = 1e-4
    acc = {"approach": [], "orbit": []}
    for r in reps:
        ii = np.where(r["infer"])[0][::5]
        # odtwórz h wejściowe: h PO ticku poprzednim = r["h"][i-1] (i=0 → zera)
        for i in ii:
            ph = r["phase"][i]
            if ph not in acc:
                continue
            h = r["h"][i - 1][None, :] if i > 0 else np.zeros((1, m.H))
            xs = r["x"][i]
            J = np.zeros((3, 8))
            for j in range(8):
                xp, xm = xs.copy(), xs.copy()
                xp[j] += eps; xm[j] -= eps
                yp, _, _ = m.step_np(xp[None, :], h)
                ym, _, _ = m.step_np(xm[None, :], h)
                J[:, j] = (yp[0] - ym[0]) / (2 * eps)
            acc[ph].append(np.abs(J))
    return {ph: np.mean(v, 0) for ph, v in acc.items() if v}


def analyze_arm(reps, arm):
    H, G, X, Y, D, PH, EPI = pool(reps)
    sep = separability(H, PH, EPI)
    dim = pca_dim(H)
    rol = roles(H, X, Y, D)
    gat, gat_raw = gate_phase(reps, H.shape[1])
    sal = saliency(reps, arm)
    res = {"arm": arm, "n_ep": len(reps), "n_tick_infer": int(len(H)),
           "a_separowalnosc": sep, "b_pca": dim, "c_role": rol, "d_bramka": gat,
           "e_saliency_mean_abs": {ph: [[round(float(v), 3) for v in row] for row in M]
                                   for ph, M in sal.items()}}
    return res, (H, G, X, Y, D, PH, EPI), gat_raw, sal


# ------------------------------------------------------------------ PNG
def png_raster(r, arm, sid, path):
    fig, ax = plt.subplots(3, 1, figsize=(12, 7), sharex=True,
                           gridspec_kw={"height_ratios": [4, 4, 1]})
    t = r["t"] - r["t"][0]
    ax[0].imshow(r["h"].T, aspect="auto", cmap="RdBu_r", vmin=-1, vmax=1,
                 extent=[t[0], t[-1], r["h"].shape[1] - 0.5, -0.5])
    ax[0].set_ylabel("neuron (stan h)")
    ax[0].set_title(f"{arm.upper()} — epizod {sid}: stan ukryty / bramka czasu / faza")
    g = np.where(np.isnan(r["gate"]), np.nan, r["gate"])
    ax[1].imshow(g.T, aspect="auto", cmap="viridis", vmin=0, vmax=1,
                 extent=[t[0], t[-1], g.shape[1] - 0.5, -0.5])
    ax[1].set_ylabel("neuron (gate)")
    cols = {"hold": 0.0, "approach": 0.5, "orbit": 1.0}
    ph = np.array([cols.get(p, np.nan) for p in r["phase"]])[None, :]
    ax[2].imshow(ph, aspect="auto", cmap="plasma", vmin=0, vmax=1,
                 extent=[t[0], t[-1], 0, 1])
    ax[2].set_yticks([]); ax[2].set_xlabel("czas epizodu [s]")
    ax[2].set_title("faza: ciemna=hold · środek=approach · jasna=orbit", fontsize=8)
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


def png_pca(H, PH, arm, path):
    Hc = H - H.mean(0)
    U, s, Vt = np.linalg.svd(Hc, full_matrices=False)
    P = Hc @ Vt[:2].T
    i = RNG.choice(len(P), size=min(6000, len(P)), replace=False)
    fig, ax = plt.subplots(figsize=(7, 6))
    for ph, c in (("approach", "tab:blue"), ("orbit", "tab:orange")):
        m = PH[i] == ph
        ax.scatter(P[i][m, 0], P[i][m, 1], s=3, alpha=0.4, c=c, label=ph)
    var = (s ** 2 / (s ** 2).sum())[:2]
    ax.set_xlabel(f"PC1 ({var[0]*100:.0f}% war.)"); ax.set_ylabel(f"PC2 ({var[1]*100:.0f}%)")
    ax.legend(); ax.set_title(f"{arm.upper()}: przestrzeń stanu (PCA), kolor = faza")
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


def png_tau(gnc, ggr, path):
    fig, ax = plt.subplots(1, 2, figsize=(12, 4))
    for a, (ga, go, tr, bs), ttl in ((ax[0], gnc, "NCP-20 (CfC gate)"),
                                     (ax[1], ggr, "GRU-21 (bramka z)")):
        n = ga.shape[1]
        a.bar(np.arange(n) - 0.2, ga.mean(0), width=0.4, label="approach")
        a.bar(np.arange(n) + 0.2, go.mean(0), width=0.4, label="orbit")
        a.set_ylim(0, 1); a.set_title(ttl); a.set_xlabel("neuron"); a.legend(fontsize=8)
        a.set_ylabel("średnia bramka (retencja)")
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


def png_saliency(sal_n, sal_g, path):
    fig, ax = plt.subplots(2, 2, figsize=(11, 6), sharex=True, sharey=True)
    for row, (sal, nm) in enumerate(((sal_n, "NCP"), (sal_g, "GRU"))):
        for col, ph in enumerate(("approach", "orbit")):
            M = sal[ph]
            im = ax[row][col].imshow(M, aspect="auto", cmap="magma")
            ax[row][col].set_title(f"{nm} · {ph}", fontsize=9)
            ax[row][col].set_yticks([0, 1, 2], ["vn", "ve", "vd"])
            ax[row][col].set_xticks(range(8), XN, rotation=45, fontsize=7)
            fig.colorbar(im, ax=ax[row][col], shrink=0.8)
    fig.suptitle("saliency chwilowe |∂y/∂x| (FD, h zamrożone — bez ścieżki rekurencyjnej)")
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


def png_kontrast(r_ncp, y_gru, sid, path):
    t = r_ncp["t"] - r_ncp["t"][0]
    dv = np.linalg.norm(r_ncp["y"] - y_gru, axis=1)
    fig, ax = plt.subplots(2, 1, figsize=(12, 5), sharex=True)
    ax[0].plot(t, dv, lw=0.8)
    ax[0].set_ylabel("|v_NCP − v_GRU| [m/s]")
    ax[0].set_title(f"cross-replay open-loop na wejściach lotu NCP — {sid}")
    ax[1].plot(t, r_ncp["d"], lw=0.8, color="tab:red")
    ax[1].axhline(10.0, ls="--", lw=0.7, color="grey")
    ax[1].set_ylabel("dystans do tracka [m]"); ax[1].set_xlabel("czas epizodu [s]")
    for i in np.where((r_ncp["phase"][1:] == "orbit") & (r_ncp["phase"][:-1] == "approach"))[0][:1]:
        for a in ax:
            a.axvline(t[i + 1], color="k", lw=0.7, ls=":")
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


def main():
    idx = liq_index()
    adv = sorted(s["sid"] for s in idx["ncp"]
                 if s["success"] and not next(g["success"] for g in idx["gru"]
                                              if g["sid"] == s["sid"]))
    print(f"[index] LIQ 48+48; przewaga NCP∧¬GRU: {len(adv)}")

    reps = {a: [replay_case(c, a) for c in idx[a]] for a in ("ncp", "gru")}
    res_n, pool_n, graw_n, sal_n = analyze_arm(reps["ncp"], "ncp")
    res_g, pool_g, graw_g, sal_g = analyze_arm(reps["gru"], "gru")
    json.dump(res_n, open(os.path.join(OUTD, "xai_atlas_ncp.json"), "w"), indent=1)
    json.dump(res_g, open(os.path.join(OUTD, "xai_atlas_gru.json"), "w"), indent=1)
    print("[atlas] ncp:", json.dumps({k: res_n[k] for k in ("a_separowalnosc", "b_pca")}))
    print("[atlas] gru:", json.dumps({k: res_g[k] for k in ("a_separowalnosc", "b_pca")}))

    # próbka OPS (percepcja prawdziwa, wrapper net_fantom): FANTOM r1_V2 + DEMO_C d1_proba
    ops = []
    for d in ("results/FANTOM/camp/r1_V2", "results/DEMO_C/booty/d1_proba"):
        full = os.path.join(ROOT, d)
        for k, rows in sorted(load_eps(full).items()):
            r = replay_episode(rows, "ncp", fantom=True)
            r["sid"] = rows[0]["scenario_id"]
            ops.append(r)
    H, G, X, Y, D, PH, EPI = pool(ops)
    res_ops = {"n_ep": len(ops), "n_tick_infer": int(len(H)),
               "a_separowalnosc": separability(H, PH, EPI), "b_pca": pca_dim(H)}
    json.dump(res_ops, open(os.path.join(OUTD, "xai_proba_ops.json"), "w"), indent=1)
    print("[ops]", json.dumps(res_ops))

    # kontrast R3b: cross-replay GRU na wejściach lotów NCP (open-loop)
    kon = {"adv": [], "ctrl": []}
    for c in idx["ncp"]:
        r = reps["ncp"][idx["ncp"].index(c)]
        m = model_of("gru")
        h = np.zeros((1, m.H))
        yg = np.zeros_like(r["y"])
        for i in np.where(r["infer"])[0]:
            y, h, _ = m.step_np(r["x"][i][None, :], h)
            from r03.controllers.common import clip_v
            yg[i] = clip_v([float(y[0, 0]), float(y[0, 1]), float(y[0, 2])], V_MAX)
        mm = r["infer"]
        dv = np.linalg.norm(r["y"][mm] - yg[mm], axis=1)
        ph = r["phase"][mm]
        row = {"sid": c["sid"],
               "dv_p50": round(float(np.percentile(dv, 50)), 3),
               "dv_p50_approach": (round(float(np.percentile(dv[ph == "approach"], 50)), 3)
                                   if (ph == "approach").any() else None),
               "dv_p50_orbit": (round(float(np.percentile(dv[ph == "orbit"], 50)), 3)
                                if (ph == "orbit").any() else None)}
        kon["adv" if c["sid"] in adv else "ctrl"].append(row)
        if c["sid"] == "c08_s01":
            png_kontrast(r, yg, c["sid"], os.path.join(PNGD, "kontrast_c08_s01.png"))
    agg = {}
    for k in ("adv", "ctrl"):
        for f in ("dv_p50", "dv_p50_approach", "dv_p50_orbit"):
            v = [r[f] for r in kon[k] if r[f] is not None]
            agg[f"{k}_{f}_med"] = round(float(np.median(v)), 3)
    kon["agg"] = agg
    kon["adv_sids"] = adv
    kon["gru_fail_reasons_adv"] = {}
    for g in idx["gru"]:
        if g["sid"] in adv:
            for fr in g["fail_reasons"]:
                kon["gru_fail_reasons_adv"][fr] = kon["gru_fail_reasons_adv"].get(fr, 0) + 1
    json.dump(kon, open(os.path.join(OUTD, "xai_kontrast.json"), "w"), indent=1)
    print("[kontrast]", json.dumps(agg), kon["gru_fail_reasons_adv"])

    # PNG (R4)
    ex_n = next(r for r in reps["ncp"] if r["sid"] == "c03_s01")
    ex_g = next(r for r in reps["gru"] if r["sid"] == "c03_s01")
    png_raster(ex_n, "ncp", "c03_s01", os.path.join(PNGD, "ncp_raster_c03_s01.png"))
    png_raster(ex_g, "gru", "c03_s01", os.path.join(PNGD, "gru_raster_c03_s01.png"))
    png_pca(pool_n[0], pool_n[5], "ncp", os.path.join(PNGD, "ncp_pca_fazy.png"))
    png_pca(pool_g[0], pool_g[5], "gru", os.path.join(PNGD, "gru_pca_fazy.png"))
    png_tau(graw_n, graw_g, os.path.join(PNGD, "tau_bramki_fazy.png"))
    png_saliency(sal_n, sal_g, os.path.join(PNGD, "saliency_ncp_gru.png"))
    print("[png] zapisane w", PNGD)


if __name__ == "__main__":
    main()
