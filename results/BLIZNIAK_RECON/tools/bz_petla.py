#!/usr/bin/env python3
"""results/BLIZNIAK_RECON/tools/bz_petla.py — R2 ławka offline i model pętli (PROMPT_BLIZNIAK_S0 §4; 0 bootów).

Sterowniki (wsadowo, jak NetController z net/rollout_eval.py): cechy bench.features (rel, v, wiek, valid), clip_age,
standaryzacja (input_mean/std modelu), NCP20/GRU21 step_np ze stanem od zera, TinyMLP z oknem 5 standaryzowanych wektorów
(na starcie zera), komenda = clip_v(y, 3.0) na trzech wyjściach.
Model pętli: silnik PĘTLI bez zmian w treści (pl_naped: napęd N z r3_naped.json — poziom 7 ticków / 0.3 s, pion 1 tick /
0.1 s; szum AR(1) z szum_rel.json; wiek tracka = mediana z lotów r2b.json), tu przepisany na wymienny sterownik.
Wariant W: komenda pionowa = clip(0.5·(rel_z − 2), ±1). Start: dron w home na 8 m, v = 0; intruz pl_intruz (6–11 m, 10 m).
Ziarno wsadu (rodzina r, v_max j) = 70000 + 100·r + j (wariant „siec” w (e): 71000 + …); intruz default_rng(ziarno),
szum default_rng(ziarno + 7919) — te same dla wszystkich sterowników.
Miary per tick (od pierwszego kroku sieci, t = 0): dystans prawdziwy i z cech, prędkość styczna |v_xy · u⊥| (u = wersor
od drona do celu, prawdziwy), prędkość celu, kąt drona wokół celu (do okrążeń na minutę: |Σ Δφ| / 2π na minutę).
"""
import json
import math
import os
import sys
import time

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "results/PETLA_RECON/tools"))
from net.models import NCP20, TinyMLP                    # noqa: E402
from net.models_liq import GRU21                         # noqa: E402
from net.dataset import AGE_CAP                          # noqa: E402
import pl_naped as PN                                    # noqa: E402
import pl_intruz as PI                                   # noqa: E402

OUT = os.path.join(ROOT, "results/BLIZNIAK_RECON")
PET = os.path.join(ROOT, "results/PETLA_RECON")
NAPED = json.load(open(os.path.join(PET, "r3_naped.json")))["napedy"]["N"]
WIEK = float(json.load(open(os.path.join(PET, "r2b.json")))["wiek_tracka"]["mediana"])
WAGI = os.path.join(OUT, "wagi")
RAMIONA_NCP = ("Z", "K", "B90", "B50", "B30", "C3", "C12")


def model(nazwa):
    if nazwa == "Z":
        return NCP20.load(os.path.join(ROOT, "net/frozen/ncp.npz"))
    if nazwa == "GRU":
        return GRU21.load(os.path.join(ROOT, "net/frozen/gru.npz"))
    if nazwa == "MLP":
        return TinyMLP.load(os.path.join(ROOT, "net/frozen/mlp.npz"))
    return NCP20.load(os.path.join(WAGI, nazwa + ".npz"))


def clip_v(y, vmax=3.0):
    n = np.linalg.norm(y, axis=1, keepdims=True)
    return y * np.where(n > vmax, vmax / np.maximum(n, 1e-12), 1.0)


class Ster:
    def __init__(self, m, B):
        self.m, self.B = m, B
        if m.ARM == "mlp":
            self.win = [np.zeros((B, 8)) for _ in range(m.K)]
        else:
            self.h = np.zeros((B, m.H))

    def krok(self, x):
        x = x.copy(); x[:, 6] = np.minimum(x[:, 6], AGE_CAP)
        xs = (x - self.m.input_mean) / self.m.input_std
        if self.m.ARM == "mlp":
            self.win.pop(0); self.win.append(xs)
            y = self.m.forward(np.concatenate(self.win, 1))
        else:
            y, self.h, _ = self.m.step_np(xs, self.h)
        return clip_v(y)


def wsad(m, rodzina, vmax, zr, B, T, wariant="W"):
    rng = np.random.default_rng(zr)
    I = PI.Intruz(rodzina, B, vmax, rng)
    sz = PN.Szum(B, np.random.default_rng(zr + 7919), wl=True)
    S = Ster(m, B)
    p = np.tile([0.0, 0.0, -8.0], (B, 1)); v = np.zeros((B, 3))
    bh = [np.zeros((B, 2)) for _ in range(NAPED["kh"] + 1)]; bv = [np.zeros(B) for _ in range(NAPED["kv"] + 1)]
    ah, av = 1 - math.exp(-PN.DT / NAPED["th"]), 1 - math.exp(-PN.DT / NAPED["tv"])
    q = I.pos3()
    n = int(round(T / PN.DT))
    rec = {k: np.zeros((n, B), np.float32) for k in ("d", "df", "vt", "vq", "phi", "relz", "ku")}
    qprev = q.copy()
    for k in range(n):
        rel = q - p + sz.krok()
        x = np.concatenate([rel, v, np.full((B, 1), WIEK), np.ones((B, 1))], 1)
        c = S.krok(x)
        cfull = c.copy()
        if wariant == "W":
            c[:, 2] = np.clip(0.5 * (rel[:, 2] - 2.0), -1.0, 1.0)
        bh.append(c[:, :2]); ch = bh.pop(0); bv.append(c[:, 2]); cv = bv.pop(0)
        r_ = q[:, :2] - p[:, :2]; dd = np.hypot(r_[:, 0], r_[:, 1]); u = r_ / np.maximum(dd, 1e-9)[:, None]
        rec["d"][k] = dd; rec["df"][k] = np.hypot(x[:, 0], x[:, 1])
        rec["vt"][k] = np.abs(-v[:, 0] * u[:, 1] + v[:, 1] * u[:, 0])
        rec["vq"][k] = np.hypot(*(q[:, :2] - qprev[:, :2]).T) / PN.DT
        rec["phi"][k] = np.arctan2(-r_[:, 1], -r_[:, 0])
        rec["relz"][k] = q[:, 2] - p[:, 2]
        uf = x[:, :2] / np.maximum(rec["df"][k], 1e-9)[:, None]
        rec["ku"][k] = (cfull[:, :2] * uf).sum(1)
        v[:, :2] += ah * (ch - v[:, :2]); v[:, 2] += av * (cv - v[:, 2])
        p = p + v * PN.DT
        qprev = q
        q = I.krok(p)
    return rec


def petla(nazwa, B=150, T=90.0):
    m = model(nazwa)
    out = {}
    for r, rod in enumerate(PI.RODZINY):
        for j, vm in enumerate((1.0, 0.5)):
            out[(r, j)] = wsad(m, rod, vm, 70000 + 100 * r + j, B, T)
    return out


def q(a, ps=(1, 50, 99)):
    a = np.asarray(a, float).ravel()
    d = {f"p{p}": float(np.percentile(a, p)) for p in ps}
    d["max"] = float(a.max())
    return d


def staty(recs, sel=None):
    """recs: lista rec (n, B); sel: funkcja (rec) → maska (n, B)."""
    D, DF, VT, OK, LAP, MIN = [], [], [], [], [], []
    for rec in recs:
        msk = sel(rec) if sel else np.ones_like(rec["d"], bool)
        D.append(rec["d"][msk]); DF.append(rec["df"][msk]); VT.append(rec["vt"][msk])
    D, DF, VT = map(np.concatenate, (D, DF, VT))
    return {"n": int(len(D)), "d": q(D), "d_cech": q(DF), "vt_srednia": float(VT.mean()), "udzial_vt_lt_1": float((VT < 1.0).mean())}


def okrazenia(recs, t0, t1):
    """Okrążenia na minutę w oknie [t0, t1) s: |Σ Δφ| / 2π / czas."""
    L = []
    for rec in recs:
        a, b = int(t0 / PN.DT), int(t1 / PN.DT)
        dphi = np.diff(np.unwrap(rec["phi"][a:b].astype(np.float64), axis=0), axis=0)
        L.append(np.abs(dphi.sum(0)) / (2 * math.pi) / ((b - a) * PN.DT / 60))
    L = np.concatenate(L)
    return {"srednia": float(L.mean()), "p50": float(np.median(L))}


def analiza(nazwa, out):
    recs = list(out.values())
    t = np.arange(recs[0]["d"].shape[0]) * PN.DT
    w = {"lacznie": staty(recs), "pierwsze_30s": staty(recs, lambda r: (t < 30)[:, None] & np.ones_like(r["d"], bool)),
         "po_30s": staty(recs, lambda r: (t >= 30)[:, None] & np.ones_like(r["d"], bool)),
         "okrazenia_po_30s": okrazenia(recs, 30, t[-1] + PN.DT)}
    per = {}
    for r, rod in enumerate(PI.RODZINY):
        rr = [out[(r, 0)], out[(r, 1)]]
        per[rod] = {"po_30s": staty(rr, lambda x: (t >= 30)[:, None] & np.ones_like(x["d"], bool)), "okrazenia": okrazenia(rr, 30, t[-1] + PN.DT)}
    w["per_rodzina"] = per
    w["najgorsza_rodzina_vt"] = min((v["po_30s"]["vt_srednia"], k) for k, v in per.items())
    # H-PAMIĘĆ: cel stoi (< 0.05 m/s), cel > 0.4 m/s (po 10 s), pierwsze 10 s
    w["H_pamiec"] = {"cel_stoi": staty(recs, lambda x: (t >= 10)[:, None] & (x["vq"] < 0.05)),
                     "cel_ruch_gt_0_4": staty(recs, lambda x: (t >= 10)[:, None] & (x["vq"] > 0.4)),
                     "pierwsze_10s": staty(recs, lambda x: (t < 10)[:, None] & np.ones_like(x["d"], bool))}
    return w


def pion_siec(nazwa, B=50, T=300.0):
    m = model(nazwa)
    ev, n = 0, 0
    tev = []
    for r, rod in enumerate(PI.RODZINY):
        for j, vm in enumerate((1.0, 0.5)):
            rec = wsad(m, rod, vm, 71000 + 100 * r + j, B, T, wariant="siec")
            t = np.arange(rec["relz"].shape[0]) * PN.DT
            dz = np.abs(rec["relz"][t >= 20.0] - 2.0) > 8.0
            hit = dz.any(0)
            ev += int(hit.sum()); n += B
            tev += list((np.argmax(dz, 0)[hit] * PN.DT + 20.0).tolist())
    return {"biegi": n, "zdarzenia_ucieczki": ev, "t_zdarzen": tev}


def lawka(nazwa):
    from net import rollout_eval as RE
    from bench import scenarios as S
    m = model(nazwa)
    tab, npass = RE.gate_arm(m)
    tab_all, np_all, ntot = RE.gate_on_seeds(m, list(S.SEEDS))
    ps = [p for r in tab_all for p in r["per_seed"]]
    return {"gate_arm_TEST": npass, "wszystkie": [np_all, ntot],
            "min_frac": min(p["frac"] for p in ps), "max_t_entry": max((p["t_entry"] or 1e9) for p in ps),
            "min_d_min": min((p["d_min"] or 0) for p in ps)}


if __name__ == "__main__":
    tryb, nazwa = sys.argv[1], sys.argv[2]
    a = time.time()
    if tryb == "petla":
        out = petla(nazwa)
        w = analiza(nazwa, out)
        np.savez_compressed(os.path.join(OUT, f"petla_{nazwa}.npz"),
                            **{f"{k}_{r}_{j}": v[k][::4] for (r, j), v in out.items() for k in ("d", "df", "vt", "vq")})
    elif tryb == "lawka":
        w = lawka(nazwa)
    elif tryb == "pion":
        w = pion_siec(nazwa)
    w["czas_s"] = time.time() - a
    json.dump(w, open(os.path.join(OUT, f"r2_{tryb}_{nazwa}.json"), "w"), ensure_ascii=False, indent=1)
    print(nazwa, tryb, json.dumps({k: v for k, v in w.items() if k != "per_rodzina"}, ensure_ascii=False)[:800], flush=True)
