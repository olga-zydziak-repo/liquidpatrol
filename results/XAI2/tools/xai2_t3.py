#!/usr/bin/env python3
"""results/XAI2/tools/xai2_t3.py — KROK 0 (śmierć S1) + T3′ (PRE_XAI2 §2) + M7.

KROK 0 (PRE §3, PROMPT §1.1):
  (i)   asercja mapowania indeks → nazwa → (mean, std) z npz (xai2_common);
  (ii)  replay WŁASNYM krokiem z h₀=0 vs xai_replay: max |Δy| ≤ 1e-12 pełny korpus;
  (iii) klasyfikator autonomii na kontrolach syntetycznych: obrót 2D o 2π/50
        ⇒ OKRESOWY p=50; kontrakcja h′=0.5h+c ⇒ PUNKT STAŁY.

T3′(a) ZAPOMINANIE: per epizod N=32 losowych h₀ ~ U(−0.99,0.99)²⁰ (jeden
RandomState(0), losowania kolejno w porządku korpusu) + referencja h₀=0;
replay na zalogowanych wejściach; para ZBIEŻNA ⇔ ‖h_end−h_end^ref‖₂ < 1e-6.
τ = czas od 1. ticku inferencji do PIERWSZEGO ticku, od którego ‖Δh‖₂ < 1e-6
już do końca. λ₁: warunkowy wykładnik Lapunowa metodą QR (k=1: v←Jv, r=‖v‖,
akumulacja log r / Δt_sim; jakobian 1. ticku inferencji pominięty — brak Δt).

T3′(b) AUTONOMIA: K=200 x* z ticków orbity + 50 z podejścia (RandomState(1),
bez zwracania); 10 startów = [0, h z logu (stan replayu PO wylosowanym ticku),
8 losowych U(−0.99,0.99)]; M=5000 iteracji. Klasy per PRE §2(b); norma nawrotu
‖·‖₂ (PRE nie precyzuje; wybór nazwany). AGREGACJA per wejście (reguła
mechaniczna, walidowana kontrolami (iii)): wszystkie starty FIXED
(‖h_M−h_{M−1}‖∞<1e-10) ∧ rozrzut końców <1e-6 ⇒ PUNKT_STALY; wszystkie FIXED
∧ rozrzut >1e-3 ⇒ WIELOSTABILNY; ≥1 start OKRESOWY (nie-FIXED z nawrotem
p≤500 <1e-8) ⇒ OKRESOWY (p = min po startach okresowych); inaczej INNY.

WERDYKT (prereg PRE §2): H-ECHO ⇔ (a)≥95% zbieżnych ∧ (b)≥95% orbitalnych
PUNKT_STALY; H-GEN ⇔ (b)≥50% orbitalnych OKRESOWY; inaczej MIESZANY.

M7_rekurencja: Wb[8:28,:]×k, k∈{2,3,5} — werdykt T3′ per k ((a)+(b) tą samą
maszynerią; x*/h-z-logu z replayu ORYGINAŁU — mutant nie ma własnego logu).

Użycie: xai2_t3.py <krok0.json> <t3.json>
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xai2_common import (OUTD, V_MAX, assert_mapping, corpus_index, fresh_model,
                         install, jac_h, jd, make_m7, raw_pass, replay_all, step_vec)

M_ITER = 5000
TAIL = 501          # stany h_{M-500}..h_M


def clipv_vec(y):
    n = np.linalg.norm(y, axis=-1, keepdims=True)
    s = np.where(n > V_MAX, V_MAX / np.maximum(n, 1e-300), 1.0)
    return y * s


# ------------------------------------------------------------- T3'(a)
def forgetting(m, reps, rng, with_lyap):
    frac_num = frac_den = 0
    taus, dy_po_tau, cex = [], [], []
    lam_ep = []
    lam_phase = {}
    for rep in reps:
        H0 = np.vstack([np.zeros((1, 20)), rng.uniform(-0.99, 0.99, (32, 20))])
        h = H0.copy()
        idx = np.where(rep["infer"])[0]
        if len(idx) == 0:
            continue
        Ds = np.zeros((len(idx), 32))
        dY = np.zeros((len(idx), 32))
        q = None
        t_prev = None
        s_logr = 0.0
        s_dt = 0.0
        for j, i in enumerate(idx):
            X = np.repeat(rep["x"][i][None, :], 33, axis=0)
            y_raw, h, bb, g, hh, gate = step_vec(m, X, h)
            yc = clipv_vec(y_raw)
            Ds[j] = np.linalg.norm(h[1:] - h[0], axis=1)
            dY[j] = np.abs(yc[1:] - yc[0]).max(axis=1)
            if with_lyap:
                J = jac_h(m, bb[0], g[0], hh[0], gate[0])
                if q is None:
                    q = np.ones(20) / math.sqrt(20.0)
                else:
                    v = J @ q
                    r = float(np.linalg.norm(v))
                    q = v / r
                    dt = float(rep["t"][i] - t_prev)
                    s_logr += math.log(r)
                    s_dt += dt
                    ph = str(rep["phase"][i])
                    acc = lam_phase.setdefault(ph, [0.0, 0.0])
                    acc[0] += math.log(r)
                    acc[1] += dt
                t_prev = rep["t"][i]
        conv = Ds[-1] < 1e-6
        frac_num += int(conv.sum())
        frac_den += 32
        for b in range(32):
            if conv[b]:
                above = np.where(Ds[:, b] >= 1e-6)[0]
                j0 = (above[-1] + 1) if len(above) else 0
                taus.append(float(rep["t"][idx[j0]] - rep["t"][idx[0]]))
                dy_po_tau.append(float(dY[j0:, b].max()))
            elif len(cex) < 5:
                cex.append({"sid": rep["sid"], "h0_idx": b, "D_end": float(Ds[-1, b])})
        if with_lyap and s_dt > 0:
            lam_ep.append({"sid": rep["sid"], "lambda1": round(s_logr / s_dt, 4)})
    res = {"n_par": frac_den, "n_zbiezne": frac_num,
           "frakcja_zbieznych": round(frac_num / max(frac_den, 1), 6),
           "tau_s": {"p50": round(float(np.median(taus)), 3) if taus else None,
                     "p90": round(float(np.percentile(taus, 90)), 3) if taus else None,
                     "max": round(float(np.max(taus)), 3) if taus else None},
           "max_dy_po_tau": round(float(np.max(dy_po_tau)), 9) if dy_po_tau else None,
           "kontrprzyklady_przyklad": cex}
    if with_lyap:
        lam = [e["lambda1"] for e in lam_ep]
        res["lambda1_per_epizod"] = {"p50": round(float(np.median(lam)), 4),
                                     "min": round(float(np.min(lam)), 4),
                                     "max": round(float(np.max(lam)), 4),
                                     "n_dodatnich": int(sum(1 for v in lam if v > 0))}
        res["lambda1_per_faza"] = {ph: {"lambda1": round(a[0] / a[1], 4),
                                        "dt_sum_s": round(a[1], 1)}
                                   for ph, a in sorted(lam_phase.items()) if a[1] > 0}
        res["lambda1_epizody"] = lam_ep
    return res


# ------------------------------------------------------------- T3'(b)
def run_frozen(stepf, H0):
    """Iteruje h←stepf(h) M_ITER razy; zwraca bufor ostatnich TAIL stanów."""
    h = H0.copy()
    buf = np.empty((TAIL,) + h.shape)
    for it in range(M_ITER):
        h = stepf(h)
        if it >= M_ITER - TAIL:
            buf[it - (M_ITER - TAIL)] = h
    return buf


def classify_starts(buf):
    """buf (TAIL, S, H) → lista klas per start + dane."""
    hM, hM1 = buf[-1], buf[-2]
    out = []
    for s in range(buf.shape[1]):
        fixed = bool(np.abs(hM[s] - hM1[s]).max() < 1e-10)
        per_p = None
        if not fixed:
            diffs = np.linalg.norm(hM[s][None, :] - buf[-501:-1][::-1, s, :], axis=1)
            ok = np.where(diffs < 1e-8)[0]          # diffs[p-1] = ‖h_M − h_{M−p}‖₂
            per_p = int(ok[0] + 1) if len(ok) else None
        out.append({"fixed": fixed, "p": per_p, "end": hM[s]})
    return out


def classify_input(starts):
    ends = np.stack([s["end"] for s in starts])
    if all(s["fixed"] for s in starts):
        dmax = float(max(np.linalg.norm(ends[a] - ends[b])
                         for a in range(len(ends)) for b in range(a + 1, len(ends))))
        if dmax < 1e-6:
            return "PUNKT_STALY", None
        if dmax > 1e-3:
            return "WIELOSTABILNY", None
        return "INNY", None
    pp = [s["p"] for s in starts if (not s["fixed"]) and s["p"] is not None]
    if pp:
        return "OKRESOWY", int(min(pp))
    return "INNY", None


def krok0_iii():
    """Kontrole syntetyczne klasyfikatora (śmierć S1 (iii))."""
    rng = np.random.RandomState(2)
    th = 2 * math.pi / 50
    R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
    H0 = np.vstack([np.zeros((1, 2)), rng.uniform(-0.99, 0.99, (1, 2)),
                    rng.uniform(-0.99, 0.99, (8, 2))])
    cls_rot, p_rot = classify_input(classify_starts(run_frozen(lambda H: H @ R.T, H0)))
    c = rng.uniform(-0.5, 0.5, 20)
    H0c = np.vstack([np.zeros((1, 20)), rng.uniform(-0.99, 0.99, (1, 20)),
                     rng.uniform(-0.99, 0.99, (8, 20))])
    cls_con, _ = classify_input(classify_starts(run_frozen(lambda H: 0.5 * H + c, H0c)))
    ok = (cls_rot == "OKRESOWY" and p_rot == 50 and cls_con == "PUNKT_STALY")
    return {"obrot_2d": {"klasa": cls_rot, "p": p_rot, "oczekiwane": "OKRESOWY p=50"},
            "kontrakcja": {"klasa": cls_con, "oczekiwane": "PUNKT_STALY"},
            "pass": bool(ok)}


def autonomy(m, picks):
    """picks: lista (x*, h_log, faza). Batch 10 startów × wejście."""
    rng = np.random.RandomState(1)
    rows_x, rows_h = [], []
    for x, hlog, _ in picks:
        starts = np.vstack([np.zeros((1, 20)), hlog[None, :],
                            rng.uniform(-0.99, 0.99, (8, 20))])
        rows_x.append(np.repeat(x[None, :], 10, axis=0))
        rows_h.append(starts)
    X = np.concatenate(rows_x)
    H0 = np.concatenate(rows_h)
    buf = run_frozen(lambda H: step_vec(m, X, H)[1], H0)
    res = []
    for q in range(len(picks)):
        st = classify_starts(buf[:, 10 * q:10 * (q + 1), :])
        cls, p = classify_input(st)
        rho = None
        if cls == "PUNKT_STALY":
            hstar = st[0]["end"]
            _, _, bb, g, hh, gate = step_vec(m, picks[q][0][None, :], hstar[None, :])
            rho = float(np.abs(np.linalg.eigvals(
                jac_h(m, bb[0], g[0], hh[0], gate[0]))).max())
        res.append({"faza": picks[q][2], "klasa": cls, "p": p, "rho": rho})
    return res


def summarize_b(res):
    out = {}
    for faza in ("orbit", "approach"):
        sub = [r for r in res if r["faza"] == faza]
        cnt = {}
        for r in sub:
            cnt[r["klasa"]] = cnt.get(r["klasa"], 0) + 1
        rhos = [r["rho"] for r in sub if r["rho"] is not None]
        out[faza] = {"n": len(sub), "klasy": cnt,
                     "frakcja_punkt_staly": round(cnt.get("PUNKT_STALY", 0) / max(len(sub), 1), 4),
                     "frakcja_okresowy": round(cnt.get("OKRESOWY", 0) / max(len(sub), 1), 4),
                     "rho_max": round(float(np.max(rhos)), 6) if rhos else None,
                     "rho_p50": round(float(np.median(rhos)), 6) if rhos else None}
    return out


def verdict(frac_a, sum_b):
    fo = sum_b["orbit"]
    if frac_a >= 0.95 and fo["frakcja_punkt_staly"] >= 0.95:
        return "H-ECHO"
    if fo["frakcja_okresowy"] >= 0.50:
        return "H-GEN"
    return "MIESZANY"


def main():
    out_k0, out_t3 = sys.argv[1], sys.argv[2]
    m = fresh_model()
    install(m)
    # KROK 0 (i)
    k0 = {"i_mapowanie": assert_mapping(m)}
    print("KROK0(i) mapowanie:", "PASS" if k0["i_mapowanie"]["pass"] else "FAIL")
    # korpus + KROK 0 (ii)
    reps = replay_all(corpus_index())
    dmax = 0.0
    for rep in reps:
        _, dm = raw_pass(m, rep)
        dmax = max(dmax, dm)
    k0["ii_replay_wlasny"] = {"max_dy": dmax, "prog": 1e-12, "pass": bool(dmax <= 1e-12)}
    print(f"KROK0(ii) max|Δy|={dmax:.3e}", "PASS" if dmax <= 1e-12 else "FAIL")
    # KROK 0 (iii)
    k0["iii_kontrole_klasyfikatora"] = krok0_iii()
    print("KROK0(iii):", k0["iii_kontrole_klasyfikatora"])
    k0["pass"] = bool(k0["i_mapowanie"]["pass"] and k0["ii_replay_wlasny"]["pass"]
                      and k0["iii_kontrole_klasyfikatora"]["pass"])
    jd(k0, out_k0)
    if not k0["pass"]:
        print("ŚMIERĆ S1 — STOP-ANEKS (PRE §3)")
        sys.exit(2)
    # T3'(a) oryginał
    a = forgetting(m, reps, np.random.RandomState(0), with_lyap=True)
    print("T3'(a):", a["frakcja_zbieznych"], a["tau_s"], a.get("lambda1_per_faza"))
    # T3'(b): losowanie x* (ziarno 1, bez zwracania) z puli ticków per faza
    pool = {"orbit": [], "approach": []}
    for e, rep in enumerate(reps):
        for i in np.where(rep["infer"])[0]:
            ph = str(rep["phase"][i])
            if ph in pool:
                pool[ph].append((e, int(i)))
    rngs = np.random.RandomState(1)
    picks = []
    for faza, K in (("orbit", 200), ("approach", 50)):
        sel = rngs.choice(len(pool[faza]), K, replace=False)
        for s in sel:
            e, i = pool[faza][int(s)]
            picks.append((reps[e]["x"][i].copy(), reps[e]["h"][i].copy(), faza))
    b = autonomy(m, picks)
    sb = summarize_b(b)
    w = verdict(a["frakcja_zbieznych"], sb)
    print("T3'(b):", sb, "WERDYKT:", w)
    # M7 per k
    m7 = {}
    for k in (2, 3, 5):
        mk = make_m7(k)
        ak = forgetting(mk, reps, np.random.RandomState(0), with_lyap=False)
        bk = summarize_b(autonomy(mk, picks))
        m7[f"k={k}"] = {"a_frakcja": ak["frakcja_zbieznych"], "b": bk,
                        "werdykt": verdict(ak["frakcja_zbieznych"], bk)}
        print(f"M7 k={k}:", m7[f'k={k}']["werdykt"], "a=", ak["frakcja_zbieznych"],
              "orbit=", bk["orbit"]["klasy"])
    jd({"a_zapominanie": a, "b_autonomia": sb,
        "b_szczegoly_n": len(b), "werdykt_T3prim": w, "M7_rekurencja": m7,
        "parametry": {"N": 32, "ziarno_a": 0, "prog_zbieznosci": 1e-6,
                      "K_orbit": 200, "K_approach": 50, "ziarno_b": 1,
                      "M_iteracji": M_ITER, "starty": "0, h_z_logu, 8×U(−0.99,0.99)",
                      "norma_nawrotu": "L2 (wybór nazwany)"}}, out_t3)


if __name__ == "__main__":
    main()
