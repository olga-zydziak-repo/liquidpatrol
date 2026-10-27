#!/usr/bin/env python3
"""results/XAI/tools/xai_thm_diff.py — pomiary pudełka + RÓŻNICÓWKA T1–T4
(PROMPT_XAI_S1 §1.1/§1.2; PRE_XAI §1/§2.2). Zero edycji istniejących;
replayer recon IMPORTEM (results/XAI_RECON/tools/xai_replay.py, FROZEN
ac9551ab), wagi ncp 0337d5ea czytane kopią przez model_of().

Korpus = korpus atlasu recon: LIQ 48 epizodów ramienia NCP (indeks epizodów
sędziowanych po erratum z erratum_sweep.json) + próbka OPS (FANTOM r1_V2,
DEMO_C d1_proba; net_fantom) = 53 epizody.

Tryby:
  measure <out.json>          — pudełko wejść p1–p99 (cechy znorm.), pudełko
                                stanu p1–p99 per neuron, pasmo bramek orbity
                                (średnie per neuron) + δ = p99 |gate−średnia
                                fazowa| na tickach orbity (liczby do FREEZE).
  diff <pudelko.json> <out.json> [mutant] [korpus=full|mini]
                              — różnicówka:
    T1: skan |y_raw_k| (głowa przed clip_v) po wszystkich tickach inferencji
        + ‖v‖₂ po clip_v; kontrprzykłady |y_raw_k| ≥ V_MAX; margines.
    T2: skan |h_i| po WSZYSTKICH tickach; kontrprzykłady ≥ 1; margines.
    T3: na tickach spełniających założenie (gate_i ∈ [lo,hi] ∀i): dokładny
        jakobian ∂h′/∂h = C·D analitycznie, norma spektralna; kontrprzykłady
        ‖J‖₂ ≥ 1; licznik ticków poza założeniem; max norma.
    T4: znak ∂y₀/∂x₂ analitycznie na tickach korpusu ORAZ różnice skończone
        (centralne, eps=1e-3 znorm.) na siatce 3⁸ pudełka × 5 stanów h
        z korpusu (seed 0).
  Mutanty (PRE §1 reżim (3); konfiguracje nazwane, WYŁĄCZNIE w pamięci):
    M1_znak   — znak jednej losowej wagi (seed 1, pozycja z rng po spłaszczeniu)
    M2_skala  — wszystkie parametry ×1.5 ŁĄCZNIE z vmax npz (kontrakt V_MAX!)
    M3_zero   — wyzerowanie neuronu (kolumny Wg/Wh/Wt + wiersz Wo; seed 3)
    M4_glowa  — strukturalny: głowa BEZ tanh (y = zo·vmax) — łamie T1
    M5_bramka — strukturalny: gate = 1.2·σ (poza (0,1)) — łamie T2
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
XRT = os.path.join(ROOT, "results", "XAI_RECON", "tools")
for p in (ROOT, XRT):
    if p not in sys.path:
        sys.path.insert(0, p)

import xai_replay as XR                      # FROZEN ac9551ab — importem
from xai_replay import load_eps, replay_episode, V_MAX
from net.models import NCP20, _sig

OUTD = os.path.join(ROOT, "results", "XAI")


# ----------------------------------------------------------------- korpus
def corpus_index(mini=False):
    d = json.load(open(os.path.join(ROOT, "results", "POSCIG_RECON", "erratum_sweep.json")))
    eps = []
    for c in d["cases"]:
        if ":ncp:" in c["label"]:
            if mini and not any(b in c["dir"] for b in ("r1_ncp", "r5_ncp")):
                continue
            eps.append({"dir": os.path.join(ROOT, c["dir"]), "eid": c["episode_id"],
                        "sid": c["scenario_id"], "fantom": False})
    ops = [("results/FANTOM/camp/r1_V2", True), ("results/DEMO_C/booty/d1_proba", True)]
    for dd, f in ops:
        full = os.path.join(ROOT, dd)
        for (eid, att), rows in sorted(load_eps(full).items()):
            eps.append({"dir": full, "eid": eid, "sid": rows[0]["scenario_id"], "fantom": f})
    return eps


def replay_all(index):
    reps = []
    for c in index:
        eps = load_eps(c["dir"])
        k = max(kk for kk in eps if kk[0] == c["eid"])
        r = replay_episode(eps[k], "ncp", fantom=c["fantom"])
        r["sid"] = c["sid"]
        reps.append(r)
    return reps


# ------------------------------------------------------------- mutanty
class HeadLinear(NCP20):
    """M4_glowa: y = zo·vmax (bez tanh) — reszta kroku bez zmian."""

    def step_np(self, x, h):
        concat = np.concatenate([x, h], axis=1)
        bb = np.tanh(concat @ self.Wb + self.bb0)
        g = np.tanh(bb @ self.Wg + self.bg)
        hh = np.tanh(bb @ self.Wh + self.bh)
        gate = _sig(bb @ self.Wt + self.bt)
        h2 = gate * g + (1.0 - gate) * hh
        zo = h2 @ self.Wo + self.bo
        y = zo * self.vmax                         # BEZ tanh
        return y, h2, (concat, bb, g, hh, gate, h2, zo, h)


class GateUnbounded(NCP20):
    """M5_bramka: gate = 1.2·σ(zt) — wypukłość kombinacji ZŁAMANA."""

    def step_np(self, x, h):
        concat = np.concatenate([x, h], axis=1)
        bb = np.tanh(concat @ self.Wb + self.bb0)
        g = np.tanh(bb @ self.Wg + self.bg)
        hh = np.tanh(bb @ self.Wh + self.bh)
        gate = 1.2 * _sig(bb @ self.Wt + self.bt)
        h2 = gate * g + (1.0 - gate) * hh
        a_o = np.tanh(h2 @ self.Wo + self.bo)
        y = a_o * self.vmax
        return y, h2, (concat, bb, g, hh, gate, h2, a_o, h)


def fresh_model():
    return NCP20.load(os.path.join(ROOT, "net", "frozen", "ncp.npz"))


def make_mutant(name):
    m = fresh_model()
    if name == "M1_znak":
        rng = np.random.RandomState(1)
        keys = sorted(m.params())
        sizes = [m.params()[k].size for k in keys]
        tot = int(np.sum(sizes))
        pick = rng.randint(tot)
        for k, s in zip(keys, sizes):
            if pick < s:
                arr = getattr(m, k)
                arr.flat[pick] *= -1.0
                m._mut = f"{k}.flat[{pick}] *= -1"
                break
            pick -= s
    elif name == "M2_skala":
        for k, v in m.params().items():
            v *= 1.5
        m.vmax *= 1.5
        m._mut = "wszystkie parametry ×1.5 + vmax ×1.5 (npz-metadana)"
    elif name == "M3_zero":
        rng = np.random.RandomState(3)
        n = rng.randint(m.H)
        m.Wg[:, n] = 0; m.Wh[:, n] = 0; m.Wt[:, n] = 0; m.Wo[n, :] = 0
        m._mut = f"neuron {n} wyzerowany (kolumny Wg/Wh/Wt + wiersz Wo)"
    elif name == "M4_glowa":
        m2 = HeadLinear(m.vmax, hidden=m.H, bb=m.BB)
        m2.set_params(m.params())
        m2.input_mean, m2.input_std = m.input_mean, m.input_std
        m2._mut = "głowa bez tanh: y = zo·vmax"
        m = m2
    elif name == "M5_bramka":
        m2 = GateUnbounded(m.vmax, hidden=m.H, bb=m.BB)
        m2.set_params(m.params())
        m2.input_mean, m2.input_std = m.input_mean, m.input_std
        m2._mut = "gate = 1.2·σ(zt)"
        m = m2
    else:
        m._mut = "oryginał"
    return m


def install(model):
    """Podmiana modelu w cache replayera recon (API słownika, zero edycji kodu)."""
    XR._MODELS["ncp"] = model


# --------------------------------------------------- rachunki analityczne
def step_full(m, xs, h_prev):
    """Krok + wielkości pochodne (modelem AKTUALNYM — też mutantem)."""
    y, h2, cache = m.step_np(xs[None, :], h_prev[None, :])
    concat, bb, g, hh, gate, _, a_o, _ = cache
    return (y[0], h2[0], bb[0], g[0], hh[0], gate[0], a_o[0])


def jac_h(m, bb, g, hh, gate):
    """∂h′/∂h = C·D; C_jk = ∂h′_k/∂bb_j, D_ji… orientacja: J[k,i]."""
    C = (gate * (1 - g * g))[None, :] * m.Wg + ((1 - gate) * (1 - hh * hh))[None, :] * m.Wh \
        + ((g - hh) * gate * (1 - gate))[None, :] * m.Wt          # (BB,H): C[j,k] = ∂h′_k/∂bb_j
    D = (1 - bb * bb)[:, None] * m.Wb[m.IN:, :].T                 # (BB,H): D[j,i] = ∂bb_j/∂h_i
    # J[k,i] = Σ_j C[j,k]·D[j,i]
    return C.T @ D


def dy0_dx2(m, bb, g, hh, gate, a_o):
    """∂y₀/∂x₂ analitycznie (głowa przed clip_v). Czynnik głowy wg modelu:
    tanh → (1−a_o₀²); M4_glowa (liniowa) → 1 (pochodna zo·vmax)."""
    dbb = (1 - bb * bb) * m.Wb[2, :]                              # ∂bb_j/∂x₂
    dh2 = ((gate * (1 - g * g))[None, :] * m.Wg
           + ((1 - gate) * (1 - hh * hh))[None, :] * m.Wh
           + ((g - hh) * gate * (1 - gate))[None, :] * m.Wt).T @ dbb   # (H,)
    head = 1.0 if isinstance(m, HeadLinear) else (1 - a_o[0] ** 2)
    return float(m.vmax * head * (m.Wo[:, 0] @ dh2))


# --------------------------------------------------------------- measure
def measure(out_json):
    install(fresh_model())
    reps = replay_all(corpus_index())
    X, H, G, PH = [], [], [], []
    for r in reps:
        mm = r["infer"]
        X.append(r["x"][mm]); G.append(r["gate"][mm]); PH.append(r["phase"][mm])
        H.append(r["h"])                       # stan po KAŻDYM ticku (też hold)
    X, G, PH = np.concatenate(X), np.concatenate(G), np.concatenate(PH)
    H = np.concatenate(H)
    orb = PH == "orbit"
    mean_orb = G[orb].mean(0)
    delta = float(np.percentile(np.abs(G[orb] - mean_orb[None, :]).max(axis=1), 99))
    out = {"n_ep": len(reps), "n_tick_infer": int(len(X)), "n_tick_all": int(len(H)),
           "box_x_p1": [round(float(v), 4) for v in np.percentile(X, 1, axis=0)],
           "box_x_p99": [round(float(v), 4) for v in np.percentile(X, 99, axis=0)],
           "box_h_p1": [round(float(v), 4) for v in np.percentile(H, 1, axis=0)],
           "box_h_p99": [round(float(v), 4) for v in np.percentile(H, 99, axis=0)],
           "gate_mean_orbit": [round(float(v), 4) for v in mean_orb],
           "pasmo_orbit": [round(float(mean_orb.min()), 4), round(float(mean_orb.max()), 4)],
           "delta_p99": round(delta, 4),
           "zalozenie_T3": [round(float(mean_orb.min() - delta), 4),
                            round(float(mean_orb.max() + delta), 4)],
           "gate_global_min": round(float(G.min()), 4),
           "gate_global_max": round(float(G.max()), 4)}
    json.dump(out, open(out_json, "w"), indent=1)
    print(json.dumps({k: out[k] for k in ("n_ep", "n_tick_infer", "pasmo_orbit",
                                          "delta_p99", "zalozenie_T3")}))
    print("box_x p1 :", out["box_x_p1"], "\nbox_x p99:", out["box_x_p99"])


# ------------------------------------------------------------------ diff
def diff(pud_json, out_json, mutant="orig", korpus="full"):
    pud = json.load(open(pud_json))
    lo, hi = pud["zalozenie_T3"]
    m = make_mutant(mutant)
    install(m)
    reps = replay_all(corpus_index(mini=(korpus == "mini")))
    t1_max_abs_y = 0.0; t1_cex = 0; t1_vnorm_max = 0.0
    t2_max_h = 0.0; t2_cex = 0
    t3_in = 0; t3_out = 0; t3_cex = 0; t3_max = 0.0; t3_cex_przyklad = None
    t4_pos = 0; t4_neg = 0; t4_zero = 0; t4_przyklad_neg = None
    n_inf = 0
    for r in reps:
        hprev = np.zeros(m.H)
        for i in range(len(r["t"])):
            if r["infer"][i]:
                n_inf += 1
                xs = r["x"][i]
                y, h2, bb, g, hh, gate, a_o = step_full(m, xs, hprev)
                ay = float(np.abs(y).max())
                t1_max_abs_y = max(t1_max_abs_y, ay)
                if ay >= V_MAX:
                    t1_cex += 1
                t1_vnorm_max = max(t1_vnorm_max, float(np.linalg.norm(r["y"][i])))
                if np.all((gate >= lo) & (gate <= hi)):
                    t3_in += 1
                    nrm = float(np.linalg.svd(jac_h(m, bb, g, hh, gate),
                                              compute_uv=False)[0])
                    t3_max = max(t3_max, nrm)
                    if nrm >= 1.0:
                        t3_cex += 1
                        if t3_cex_przyklad is None:
                            t3_cex_przyklad = {"sid": r["sid"], "t": float(r["t"][i]),
                                               "norma": round(nrm, 4)}
                else:
                    t3_out += 1
                d4 = dy0_dx2(m, bb, g, hh, gate, np.atleast_1d(a_o))
                if d4 > 0:
                    t4_pos += 1
                elif d4 < 0:
                    t4_neg += 1
                    if t4_przyklad_neg is None:
                        t4_przyklad_neg = {"sid": r["sid"], "t": float(r["t"][i]),
                                           "wartosc": round(d4, 5)}
                else:
                    t4_zero += 1
                hprev = h2
            ah = float(np.abs(r["h"][i]).max())
            t2_max_h = max(t2_max_h, ah)
            if ah >= 1.0:
                t2_cex += 1
    # T4: siatka 3^8 pudełka × 5 stanów h z korpusu (seed 0), FD centralne 1e-3
    rng = np.random.RandomState(0)
    p1 = np.array(pud["box_x_p1"]); p99 = np.array(pud["box_x_p99"])
    grid1d = [np.array([a, (a + b) / 2, b]) for a, b in zip(p1, p99)]
    pool_h = np.concatenate([r["h"][r["infer"]] for r in reps])
    hs = pool_h[rng.choice(len(pool_h), 5, replace=False)]
    gpos = gneg = gzero = 0
    eps = 1e-3
    mesh = np.stack(np.meshgrid(*grid1d, indexing="ij"), -1).reshape(-1, 8)
    for hrow in hs:
        hb = np.repeat(hrow[None, :], len(mesh), axis=0)
        xp = mesh.copy(); xp[:, 2] += eps
        xm = mesh.copy(); xm[:, 2] -= eps
        yp, _, _ = m.step_np(xp, hb)
        ym, _, _ = m.step_np(xm, hb)
        dfd = (yp[:, 0] - ym[:, 0]) / (2 * eps)
        gpos += int((dfd > 0).sum()); gneg += int((dfd < 0).sum())
        gzero += int((dfd == 0).sum())
    out = {"mutant": mutant, "mutant_opis": getattr(m, "_mut", "oryginał"),
           "korpus": korpus, "n_ep": len(reps), "n_tick_infer": n_inf,
           "V_MAX_kontrakt": 3.0, "vmax_modelu": float(m.vmax),
           "T1": {"max_abs_y_raw": round(t1_max_abs_y, 6),
                  "margines": round(3.0 - t1_max_abs_y, 6), "kontrprzyklady": t1_cex,
                  "max_norm_v_po_clip": round(t1_vnorm_max, 6)},
           "T2": {"max_abs_h": round(t2_max_h, 6),
                  "margines": round(1.0 - t2_max_h, 6), "kontrprzyklady": t2_cex},
           "T3": {"zalozenie": [lo, hi], "ticki_w_zalozeniu": t3_in,
                  "ticki_poza": t3_out, "max_norma_spektralna": round(t3_max, 4),
                  "kontrprzyklady": t3_cex, "przyklad": t3_cex_przyklad},
           "T4": {"korpus_pos": t4_pos, "korpus_neg": t4_neg, "korpus_zero": t4_zero,
                  "przyklad_neg": t4_przyklad_neg,
                  "siatka_pos": gpos, "siatka_neg": gneg, "siatka_zero": gzero,
                  "siatka_n": int(len(mesh) * len(hs))}}
    json.dump(out, open(out_json, "w"), indent=1)
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    if sys.argv[1] == "measure":
        measure(sys.argv[2])
    elif sys.argv[1] == "diff":
        diff(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "orig",
             sys.argv[5] if len(sys.argv) > 5 else "full")
