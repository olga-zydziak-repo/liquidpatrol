#!/usr/bin/env python3
"""results/KOTW_RECON/r2/tools/kotw2_obwod.py — R1′ i R4′ PROMPT_KOTW_R2: kotwice na obwodzie strefy.

Baza: results/KOTW_RECON/tools/kotw_r1.py (recon 1) — te same źródła i konwencje, importowane READ-ONLY (load, CAM, F,
EDGE, W, H; plik nietknięty): poza GT drona z trace.jsonl "gt" (ENU, kwaternion body FLU→świat), fazy z demo.jsonl,
kamera z pinu mono_cam (f = 269.5 px, 640×480, poziomo do przodu), stożek centralny edge ≥ 0.10.
Nowe: n kotwic na okręgu R_a, azymuty φ0 + 2πk/n (φ0 ∈ {0, π/n}; 0 = oś E, przeciwnie do zegara w ENU), punkt kotwicy
na wysokości h. Widoczność kotwicy = stożek centralny ∧ zasięg w [3, 45] m (∧ opcjonalnie f·W/D ≥ 10 px — założenie
z reconu 1, niezmierzone). Intruz: gt_intruder.jsonl "ned" (N, E, D) → ENU (E, N, −D), najbliższy t_sim ≤ 0.1 s;
filtr-świadek |ned − cmd_ned| > 1 m raportowany obok (reguła ERRATUM-DMIN).
Wyjście per (konfiguracja, epizod): okna/przerwy dla trybów „1” (≥ 1 kotwica) i „2” (≥ 2 kotwice naraz), zasięgi,
kąt między kotwicami γ (poziomy, z kamery) w klatkach z 2 kotwicami, r_max drona w przerwie startowej, oraz R4′:
odsetek próbek z kotwicą w stożku w odległości kątowej ≤ 5° od intruza przy zasięgu kotwicy w [5, 18] m.
Użycie: kotw2_obwod.py <out.json> <kampania=glob> ...
"""
import bisect, glob, json, math, os, sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../tools"))
import kotw_r1 as K1   # READ-ONLY: load, CAM, F, EDGE, W, H

F, EDGE, IW, IH = K1.F, K1.EDGE, K1.W, K1.H
RA, NS, HS, PHI = (32.0, 36.0), (2, 4, 6), (2.0, 4.0), ("0", "pol")
RMIN, RMAX, MIN_PX, WS = 3.0, 45.0, 10.0, (None, 0.5, 1.0)
GAP_MERGE_S = K1.GAP_MERGE_S
R4_DEG, R4_BAND = 5.0, (5.0, 18.0)


def rotmats(q):
    w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    R = np.empty((len(q), 3, 3))
    R[:, 0, 0] = 1 - 2 * (y * y + z * z); R[:, 0, 1] = 2 * (x * y - w * z); R[:, 0, 2] = 2 * (x * z + w * y)
    R[:, 1, 0] = 2 * (x * y + w * z); R[:, 1, 1] = 1 - 2 * (x * x + z * z); R[:, 1, 2] = 2 * (y * z - w * x)
    R[:, 2, 0] = 2 * (x * z - w * y); R[:, 2, 1] = 2 * (y * z + w * x); R[:, 2, 2] = 1 - 2 * (x * x + y * y)
    return R                                                     # body→świat


def projekcja(Rm, cam, pts):
    """pts (A,3) świat → (N,A): central, zasięg, azymut kamery [rad], wektor jednostkowy w ramie kamery."""
    d = pts[None, :, :] - cam[:, None, :]                         # N,A,3
    b = np.einsum("nji,naj->nai", Rm, d)                          # świat→body (R^T d)
    rng = np.linalg.norm(d, axis=2)
    fwd = b[:, :, 0]
    with np.errstate(divide="ignore", invalid="ignore"):
        u = IW / 2 - F * b[:, :, 1] / fwd
        v = IH / 2 - F * b[:, :, 2] / fwd
    cx, cy = u / IW, v / IH
    central = (fwd > 0.1) & (np.minimum(np.minimum(cx, 1 - cx), np.minimum(cy, 1 - cy)) >= EDGE)
    az = np.arctan2(b[:, :, 1], b[:, :, 0])
    unit = b / np.maximum(rng[:, :, None], 1e-9)
    return central, rng, az, unit


def okna(ts, fl):
    w, cur = [], None
    for i in np.flatnonzero(fl):
        t = ts[i]
        if cur is not None and t - cur[1] <= GAP_MERGE_S:
            cur[1] = t; cur[2].append(i)
        else:
            if cur is not None:
                w.append(cur)
            cur = [t, t, [i]]
    if cur is not None:
        w.append(cur)
    return w


def faza_dom(fz, i0, i1):
    seg = fz[i0:i1 + 1] or ["?"]
    return max(set(seg), key=seg.count)


def boot(d, kamp, out):
    tr, dm, gi = (os.path.join(d, x) for x in ("trace.jsonl", "demo.jsonl", "gt_intruder.jsonl"))
    if not (os.path.exists(tr) and os.path.exists(dm)):
        return
    gt = sorted([g for g in K1.load(tr, "gt") if "qw" in g and "sim" in g], key=lambda g: g["sim"])
    gs = np.array([g["sim"] for g in gt])
    rows = K1.load(dm)
    intr = K1.load(gi) if os.path.exists(gi) else []
    intr.sort(key=lambda r: r["t_sim"]); it = np.array([r["t_sim"] for r in intr])
    eps = {}
    for r in rows:
        eps.setdefault(r["episode_id"], []).append(r)
    for ep, rr in eps.items():
        rr.sort(key=lambda r: r["t_sim"])
        t0, t1 = rr[0]["t_sim"], rr[-1]["t_sim"]
        i0, i1 = np.searchsorted(gs, t0), np.searchsorted(gs, t1, side="right")
        seg = gt[i0:i1]
        if len(seg) < 10:
            continue
        rt = [r["t_sim"] for r in rr]
        fz = [rr[min(bisect.bisect_left(rt, g["sim"]), len(rr) - 1)]["phase"] for g in seg]
        ts = np.array([g["sim"] - t0 for g in seg])
        pos = np.array([[g["x"], g["y"], g["z"]] for g in seg])
        q = np.array([[g["qw"], g["qx"], g["qy"], g["qz"]] for g in seg])
        Rm = rotmats(q)
        cam = pos + np.einsum("nij,j->ni", Rm, np.array(K1.CAM))
        r_xy = np.hypot(pos[:, 0], pos[:, 1])
        # intruz (ENU) per próbka
        ipos, iwit = None, None
        if len(it):
            j = np.clip(np.searchsorted(it, gs[i0:i1]), 0, len(it) - 1)
            ok = np.abs(it[j] - gs[i0:i1]) <= 0.1
            ipos = np.array([[intr[k]["ned"][1], intr[k]["ned"][0], -intr[k]["ned"][2]] for k in j])
            iwit = np.array([math.dist(intr[k]["ned"], intr[k]["cmd_ned"]) > 1.0 for k in j])
            ipos[~ok] = np.nan
        for Ra in RA:
            for n in NS:
                for ph in PHI:
                    p0 = 0.0 if ph == "0" else math.pi / n
                    for h in HS:
                        A = np.array([[Ra * math.cos(p0 + 2 * math.pi * k / n), Ra * math.sin(p0 + 2 * math.pi * k / n), h] for k in range(n)])
                        central, rng, az, unit = projekcja(Rm, cam, A)
                        geo = central & (rng >= RMIN) & (rng <= RMAX)
                        cfg = f"R{int(Ra)}_n{n}_{ph}_h{int(h)}"
                        rec = out.setdefault(cfg, [])
                        e = {"kampania": kamp, "boot": os.path.basename(d.rstrip("/")), "ep": ep, "scenario": rr[0]["scenario_id"],
                             "T_s": round(float(ts[-1]), 2), "W": {}}
                        # R4′ (bez progu px — ryzyko percepcji nie zależy od użyteczności poprawki)
                        if ipos is not None:
                            di = ipos - cam
                            ib = np.einsum("nji,nj->ni", Rm, di)
                            iu = ib / np.linalg.norm(ib, axis=1, keepdims=True)
                            ang = np.degrees(np.arccos(np.clip(np.einsum("nai,ni->na", unit, iu), -1, 1)))
                            hit = (central & (rng >= R4_BAND[0]) & (rng <= R4_BAND[1]) & (ang <= R4_DEG)).any(axis=1)
                            valid = ~np.isnan(ipos[:, 0])
                            e["r4"] = {"n": int(valid.sum()), "hit": int((hit & valid).sum()),
                                       "hit_orbit": int(sum(1 for i in np.flatnonzero(hit & valid) if fz[i] == "orbit")),
                                       "n_orbit": int(sum(1 for i in np.flatnonzero(valid) if fz[i] == "orbit")),
                                       "hit_swiadek_ned_cmd_gt1m": int((hit & valid & iwit).sum())}
                        for Wm in WS:
                            dmax = min(RMAX, F * Wm / MIN_PX) if Wm else RMAX
                            vis = geo & (rng <= dmax)
                            nv = vis.sum(axis=1)
                            rngv = np.where(vis, rng, np.inf)
                            near = rngv.min(axis=1)
                            # γ dla klatek z ≥ 2 kotwicami: największy kąt poziomy między parą widocznych
                            gam = np.full(len(ts), np.nan); r2 = np.full((len(ts), 2), np.nan)
                            for i in np.flatnonzero(nv >= 2):
                                idx = np.flatnonzero(vis[i])
                                best = None
                                for a in range(len(idx)):
                                    for b in range(a + 1, len(idx)):
                                        g = abs(az[i, idx[a]] - az[i, idx[b]])
                                        if best is None or g > best[0]:
                                            best = (g, rng[i, idx[a]], rng[i, idx[b]])
                                gam[i] = best[0]; r2[i] = best[1:]
                            wrec = {"frac_1": round(float((nv >= 1).mean()), 4), "frac_2": round(float((nv >= 2).mean()), 4),
                                    "frac_1_orbit": round(float(np.mean([nv[i] >= 1 for i in range(len(ts)) if fz[i] == "orbit"] or [0])), 4),
                                    "frac_2_orbit": round(float(np.mean([nv[i] >= 2 for i in range(len(ts)) if fz[i] == "orbit"] or [0])), 4)}
                            for tryb, fl in (("1", nv >= 1), ("2", nv >= 2)):
                                w = okna(ts, fl)
                                prz, prev, prev_i = [], 0.0, 0
                                for a, b, idx in w:
                                    ia = idx[0]
                                    prz.append({"dl": round(float(a - prev), 2), "faza": faza_dom(fz, prev_i, ia), "r_max": round(float(r_xy[prev_i:ia + 1].max()), 2)})
                                    prev, prev_i = b, idx[-1]
                                prz.append({"dl": round(float(ts[-1] - prev), 2), "faza": faza_dom(fz, prev_i, len(ts) - 1), "r_max": round(float(r_xy[prev_i:].max()), 2), "cenz": True})
                                okn = []
                                for a, b, idx in w:
                                    o = {"t0": round(float(a), 2), "dl": round(float(b - a), 2), "faza": faza_dom(fz, idx[0], idx[-1]),
                                         "zasieg_min": round(float(near[idx].min()), 2)}
                                    if tryb == "2":
                                        # najlepsza klatka pary: max sin γ przy najmniejszym max(zasięg)
                                        sc = [(math.sin(gam[i]) / max(r2[i]), i) for i in idx if not np.isnan(gam[i])]
                                        _, ib_ = max(sc)
                                        o.update(gamma_deg=round(math.degrees(gam[ib_]), 1), r_a=round(float(r2[ib_][0]), 2), r_b=round(float(r2[ib_][1]), 2))
                                    okn.append(o)
                                wrec[tryb] = {"okna": okn, "przerwy": prz}
                            e["W"][str(Wm)] = wrec
                        rec.append(e)


def main():
    out = {}
    for arg in sys.argv[2:]:
        kamp, pat = arg.split("=", 1)
        for d in sorted(glob.glob(pat)):
            if os.path.isdir(d):
                boot(d, kamp, out)
    json.dump({"opis": __doc__.split("\n\n")[0], "R_a": RA, "n": NS, "h": HS, "phi0": PHI, "zasieg": [RMIN, RMAX],
               "min_px": MIN_PX, "W": [w for w in WS if w], "r4": {"kat_deg": R4_DEG, "pasmo_m": R4_BAND}, "konfiguracje": out},
              open(sys.argv[1], "w"), ensure_ascii=False)
    print({k: len(v) for k, v in out.items()})


if __name__ == "__main__":
    main()
