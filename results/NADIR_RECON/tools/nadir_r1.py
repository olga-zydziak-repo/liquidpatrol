#!/usr/bin/env python3
"""results/NADIR_RECON/tools/nadir_r1.py — R1/R2/R4(i)/R5 PROMPT_NADIR_S0: druga kamera w dół nad siatką znaczników.

Baza: results/KOTW_RECON/tools/kotw_r1.py (load, CAM, F, EDGE, W, H — import READ-ONLY, plik nietknięty) i konwencje
kotw2_obwod.py (rotmats skopiowane): poza GT drona z trace.jsonl "gt" (ENU, kwaternion body FLU→świat, ~31 Hz),
fazy z demo.jsonl, zdarzenia z trace.jsonl "event".
Kamera nadir (HIPOTETYCZNA, tylko liczby): sztywno w body w środku ciężkości, oś optyczna −z_body; obraz 640×480,
f = 269.5 px (jak mono_cam), szerokość obrazu wzdłuż osi poprzecznej body (u = −y_b, v = −x_b: góra kadru = przód).
Stożek centralny jak w admisji: edge ≥ 0.10 (kotw_r1.EDGE) ⇒ ±43.5° (poprzecznie) × ±35.4° (wzdłużnie).
Postawa: PEŁNY kwaternion (roll+pitch+yaw) z GT — to jest różnica wobec rachunku CC (sam yaw).
Znaczniki: węzły siatki kwadratowej s ∈ {10, 15, 20} m, przesunięcie siatki off ∈ {0, s/2}, |węzeł| ≤ R_E = 32 m, z = 0.
Rozmiar w px: znacznik kwadratowy W×W osiowo w ENU, rzut środka ± W/2 wzdłuż E i N; px = min z dwóch długości boków
(liczone dla W = 1 m, skaluje się liniowo z W).
Fazy próbki GT: approach/hold/orbit (demo.jsonl w oknie epizodu), zejscie_D5 (od "refuse" do "episode_end"),
wznoszenie (przed 1. epizodem, z > 0.3 m), miedzy_epizodami, po_misji; z ≤ 0.3 m = ziemia (pominięte w statystykach).
R2 (model poprawki, liczony per próbka dla znacznika najbliższego w poziomie):
  rad = D/cosθ·(δθ + px/f) + δz·tanθ;  lat = r_h·tan δψ + D·(δθ + px/f);  ε1 = hypot(rad, lat)
  (θ = kąt padania od pionu, D = zasięg skośny, r_h = odległość pozioma, alt/cos²θ = D/cosθ).
  Tryb 2 (para w kadrze, partner = widoczny znacznik o największej bazie L): kurs z pary δψ2 = atan(hypot(ea, eb)/L),
  ea/eb = błąd różnicowy piksela znacznika (D/cosθ·px/f; błąd postawy wspólny dla obu, nie obraca pary);
  wysokość z pary δz2 = min(δz, alt²·√2·px/(f·L)); ε2 = ε1 z δψ2 i δz2 dla znacznika najbliższego.
  Tryb 12: ε2 gdy para w kadrze, inaczej ε1. Tryb 1: tylko ε1 (kurs z EKF).
R5 piła per próbka: u(t) = ε_fix(ostatnia obserwacja) + ε_b(τ) + Δ_D5, τ = t − t_ostatniej obserwacji
  (ε_b z s2_freeze_bf.json ae19f66c, koszyk ⌊τ⌋; τ ≥ 70 s ⇒ brak krzywej = nie domyka). Asocjacja po siatce:
  e_as(t) = ε_fix(ostatnia) + ε_b(τ) + ε_obs(t) przy każdej obserwacji; myli się, gdy e_as ≥ s/2.
R4(i) kamera misji (kotw_r1: poziomo do przodu, montaż .12 .03 .242): znaczniki w kadrze / w stożku centralnym,
  zasięg, depresja (skrót perspektywiczny = sin depresji), px = f·W/D·sin(dep), kąt do intruza ≤ 5°.
Env NADIR_SAMYAW=1: postawa zredukowana do samego yaw (powtórzenie warunków rachunku CC).
Użycie: nadir_r1.py <out.json> <kampania=glob> ...
"""
import bisect, glob, json, math, os, sys
import numpy as np

sys.path.insert(0, "/home/olga/projects/liquidpatrol/results/KOTW_RECON/tools")
import kotw_r1 as K1   # READ-ONLY

ROOT = "/home/olga/projects/liquidpatrol"
F, EDGE, IW, IH = K1.F, K1.EDGE, K1.W, K1.H
SS, OFFS = (10.0, 15.0, 20.0), ("0", "pol")
R_E = 32.0
Z_GROUND = 0.3
GAP_MERGE_S = K1.GAP_MERGE_S
FZ = json.load(open(os.path.join(ROOT, "results/KONT/s2/s2_freeze_bf.json")))
EPS, D5 = np.array(FZ["eps_b_obwiednia"]), FZ["delta_D5"]
YAW = json.load(open(os.path.join(ROOT, "results/KOTW_RECON/r2/r2p_yaw.json")))
PSI_Z = max(v["residuum_kont"]["absmax"] for v in YAW.values())
WAR = {"OPT": dict(px=1, psi=2.0, th=0.5, dz=0.2), "ZMIERZ": dict(px=2, psi=PSI_Z, th=0.5, dz=0.2),
       "ZMIERZ_h1.8": dict(px=2, psi=PSI_Z, th=0.5, dz=1.8)}
TRYBY = ("1", "2", "12")
# Bramki detekcji (ZAŁOŻENIA do sondy S1, nie pomiar): bok znacznika w px ≥ próg; px = W · px(W = 1 m).
#   CEN5 — centroid plamy bez ID (≈ minimalny kandydat OpenCV ArUco: minMarkerPerimeterRate 0.03 × 640 px = 19.2 px
#   obwodu ⇒ 4.8 px boku); ID12 — ArUco 4×4 (6 komórek z ramką) przy 2 px/komórkę; ID18 — 3 px/komórkę.
DETEKTORY = {"CEN5": 5.0, "ID12": 12.0, "ID18": 18.0}
WS = (0.5, 1.0, 2.0)
BRAMKI = [("geom", 0.0)] + [(f"{d}_W{w:g}", thr / w) for d, thr in DETEKTORY.items() for w in WS]
FAZY_R5 = ("approach", "hold", "orbit", "zejscie_D5")
PXB = np.array([0, 2, 4, 6, 8, 10, 12, 15, 20, 25, 30, 40, 60, 1e9])          # koszyki px (W = 1 m)
ALTB = np.array([0.3, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 20])     # koszyki wysokości


def rotmats(q):
    w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    R = np.empty((len(q), 3, 3))
    R[:, 0, 0] = 1 - 2 * (y * y + z * z); R[:, 0, 1] = 2 * (x * y - w * z); R[:, 0, 2] = 2 * (x * z + w * y)
    R[:, 1, 0] = 2 * (x * y + w * z); R[:, 1, 1] = 1 - 2 * (x * x + z * z); R[:, 1, 2] = 2 * (y * z - w * x)
    R[:, 2, 0] = 2 * (x * z - w * y); R[:, 2, 1] = 2 * (y * z + w * x); R[:, 2, 2] = 1 - 2 * (x * x + y * y)
    return R


def siatka(s, off):
    o = 0.0 if off == "0" else s / 2
    k = int(R_E // s) + 2
    return np.array([[i * s + o, j * s + o, 0.0] for i in range(-k, k + 1) for j in range(-k, k + 1)
                     if math.hypot(i * s + o, j * s + o) <= R_E])


def nadir_uv(Rm, pos, pts):
    """(N,A) u, v [px], głębokość wzdłuż osi optycznej (−z_b)."""
    d = pts[None, :, :] - pos[:, None, :]
    b = np.einsum("nji,naj->nai", Rm, d)
    depth = -b[:, :, 2]
    with np.errstate(divide="ignore", invalid="ignore"):
        u = IW / 2 + F * (-b[:, :, 1]) / depth
        v = IH / 2 + F * (-b[:, :, 0]) / depth
    return u, v, depth


def histo(x, edges):
    return np.histogram(np.clip(x, edges[0], edges[-1] - 1e-9), bins=edges)[0].tolist()


def okna(ts, fl):
    w, cur = [], None
    for i in np.flatnonzero(fl):
        t = ts[i]
        if cur is not None and t - cur[1] <= GAP_MERGE_S:
            cur[1] = t
        else:
            if cur is not None:
                w.append(cur)
            cur = [t, t]
    if cur is not None:
        w.append(cur)
    return w


def fazy_boot(gs, z, rows, ev):
    fz = np.array(["miedzy_epizodami"] * len(gs), dtype=object)
    sc = np.array([None] * len(gs), dtype=object)
    epi = np.full(len(gs), -1)
    eps = {}
    for r in rows:
        eps.setdefault(r["episode_id"], []).append(r)
    first = min((rr[0]["t_sim"] for rr in eps.values()), default=gs[-1])
    for e in eps.values():
        e.sort(key=lambda r: r["t_sim"])
    last = max((rr[-1]["t_sim"] for rr in eps.values()), default=gs[0])
    fz[gs < first] = "wznoszenie"
    fz[gs > last] = "po_misji"
    refuse = {x.get("episode_id"): x["sim"] for x in ev if x.get("ev") == "refuse"}
    for ep, rr in eps.items():
        t0, t1 = rr[0]["t_sim"], rr[-1]["t_sim"]
        i0, i1 = np.searchsorted(gs, t0), np.searchsorted(gs, t1, side="right")
        rt = [r["t_sim"] for r in rr]
        for i in range(i0, i1):
            fz[i] = rr[min(bisect.bisect_left(rt, gs[i]), len(rr) - 1)]["phase"]
            if ep in refuse and gs[i] >= refuse[ep]:
                fz[i] = "zejscie_D5"
        sc[i0:i1] = rr[0]["scenario_id"]; epi[i0:i1] = ep
    fz[z <= Z_GROUND] = "ziemia"
    return fz, sc, epi


def eps_fix(v, D, cth, tth, rh, alt, L, ea_eb):
    """ε1 (L None) albo ε2 (para) per próbka; wszystkie wektory (N,)."""
    a = math.radians(v["th"]) + v["px"] / F
    if L is None:
        psi, dz = math.radians(v["psi"]), v["dz"]
    else:
        with np.errstate(divide="ignore", invalid="ignore"):
            psi = np.arctan(ea_eb / L)
            dz = np.minimum(v["dz"], alt ** 2 * math.sqrt(2) * v["px"] / (F * L))
    rad = D / cth * a + dz * tth
    lat = rh * np.tan(psi) + D * a
    return np.hypot(rad, lat)


def boot(d, kamp, out, r4out, prof):
    tr, dm, gi = (os.path.join(d, x) for x in ("trace.jsonl", "demo.jsonl", "gt_intruder.jsonl"))
    if not (os.path.exists(tr) and os.path.exists(dm)):
        return
    gt = sorted([g for g in K1.load(tr, "gt") if "qw" in g and "sim" in g], key=lambda g: g["sim"])
    ev = K1.load(tr, "event")
    rows = K1.load(dm)
    if not rows or len(gt) < 10:
        return
    bname = os.path.basename(d.rstrip("/"))
    gs = np.array([g["sim"] for g in gt])
    pos = np.array([[g["x"], g["y"], g["z"]] for g in gt])
    q = np.array([[g["qw"], g["qx"], g["qy"], g["qz"]] for g in gt])
    if os.environ.get("NADIR_SAMYAW"):                             # kontrola: rachunek CC bez przechyłów
        psi = np.arctan2(2 * (q[:, 0] * q[:, 3] + q[:, 1] * q[:, 2]), 1 - 2 * (q[:, 2] ** 2 + q[:, 3] ** 2))
        q = np.stack([np.cos(psi / 2), 0 * psi, 0 * psi, np.sin(psi / 2)], axis=1)
    Rm = rotmats(q)
    fz, sc, epi = fazy_boot(gs, pos[:, 2], rows, ev)
    alt = np.maximum(pos[:, 2], 0.05)
    tilt = np.degrees(np.arccos(np.clip(Rm[:, 2, 2], -1, 1)))     # odchylenie osi z_b od pionu
    lot = fz != "ziemia"
    r_xy = np.hypot(pos[:, 0], pos[:, 1])
    out.setdefault("_postawa", []).append({"kampania": kamp, "boot": bname,
                                         "tilt_p50": round(float(np.median(tilt[lot])), 2),
                                         "tilt_p95": round(float(np.percentile(tilt[lot], 95)), 2),
                                         "tilt_max": round(float(tilt[lot].max()), 2)})
    for s in SS:
        for off in OFFS:
            A = siatka(s, off)
            u, v, depth = nadir_uv(Rm, pos, A)
            cx, cy = u / IW, v / IH
            vis = (depth > 0.1) & (np.minimum(np.minimum(cx, 1 - cx), np.minimum(cy, 1 - cy)) >= EDGE)
            nv = vis.sum(axis=1)
            dvec = A[None, :, :] - pos[:, None, :]
            rh_all = np.hypot(dvec[:, :, 0], dvec[:, :, 1])
            rhv = np.where(vis, rh_all, np.inf)
            j1 = rhv.argmin(axis=1)
            ii = np.arange(len(gs))
            has1 = nv >= 1
            rh = rh_all[ii, j1]
            D = np.linalg.norm(dvec[ii, j1], axis=1)
            cth = np.clip(alt / np.maximum(D, 1e-6), 1e-3, 1)
            tth = rh / alt
            theta = np.degrees(np.arccos(cth))
            # px boku znacznika W = 1 m (najbliższy widoczny)
            c = A[j1]
            pxs = []
            for e in (np.array([0.5, 0, 0]), np.array([0, 0.5, 0])):
                pa = nadir_uv_pts(Rm, pos, c + e); pb = nadir_uv_pts(Rm, pos, c - e)
                pxs.append(np.hypot(pa[0] - pb[0], pa[1] - pb[1]))
            px1 = np.minimum(*pxs)
            # partner pary: widoczny znacznik o największej bazie L od najbliższego
            has2 = nv >= 2
            L = np.full(len(gs), np.nan); ea_eb = np.full(len(gs), np.nan)
            if has2.any():
                base = np.linalg.norm(A[None, :, :2] - c[:, None, :2], axis=2)
                base = np.where(vis, base, -1.0)
                j2 = base.argmax(axis=1)
                L = np.where(has2, base[ii, j2], np.nan)
                D2 = np.linalg.norm(dvec[ii, j2], axis=1)
                c2 = np.clip(alt / np.maximum(D2, 1e-6), 1e-3, 1)
                cP = A[j2]
                pxs2 = []
                for e_ in (np.array([0.5, 0, 0]), np.array([0, 0.5, 0])):
                    pa = nadir_uv_pts(Rm, pos, cP + e_); pb = nadir_uv_pts(Rm, pos, cP - e_)
                    pxs2.append(np.hypot(pa[0] - pb[0], pa[1] - pb[1]))
                px2 = np.where(has2, np.minimum(*pxs2), 0.0)
            else:
                px2 = np.zeros(len(gs))
            key = f"s{int(s)}_{off}"
            o = out.setdefault(key, {"epizody": [], "fazy": {}, "profil_alt": {}})
            # agregaty per faza (wszystkie próbki w locie)
            for f in np.unique(fz[lot]):
                m = fz == f
                a_ = o["fazy"].setdefault(f"{kamp}|{f}", {"n": 0, "n1": 0, "n2": 0, "nv_hist": [0] * 8, "px_hist_W1": [0] * (len(PXB) - 1),
                                             "rh": [], "theta": [], "przerwy": []})
                a_["n"] += int(m.sum()); a_["n1"] += int((m & has1).sum()); a_["n2"] += int((m & has2).sum())
                a_["nv_hist"] = [x + y for x, y in zip(a_["nv_hist"], np.bincount(np.minimum(nv[m], 7), minlength=8).tolist())]
                a_["px_hist_W1"] = [x + y for x, y in zip(a_["px_hist_W1"], histo(px1[m & has1], PXB))]
                a_["rh"] += np.round(rh[m & has1][::10], 2).tolist(); a_["theta"] += np.round(theta[m & has1][::10], 1).tolist()
                a_["px_W1"] = a_.get("px_W1", []) + np.round(px1[m & has1][::10], 1).tolist()
            # przerwy ≥1 znacznik per spójny odcinek fazy (okna z łączeniem dziur < 0.25 s jak w KOTW)
            seg_start = 0
            for i in range(1, len(gs) + 1):
                if i == len(gs) or fz[i] != fz[seg_start]:
                    f = fz[seg_start]
                    if f != "ziemia":
                        ts = gs[seg_start:i]
                        for tryb, fl in (("1", has1[seg_start:i]), ("2", has2[seg_start:i])):
                            w = okna(ts, fl)
                            prev, prz = ts[0], []
                            for a, b in w:
                                if a - prev > 0:
                                    prz.append(round(float(a - prev), 3))
                                prev = b
                            if ts[-1] - prev > 0:
                                prz.append(round(float(ts[-1] - prev), 3))
                            o["fazy"][f"{kamp}|{f}"].setdefault("przerwy_" + tryb, []).extend([x for x in prz if x > GAP_MERGE_S])
                            fk = o["fazy"][f"{kamp}|{f}"]
                            fk["max_przerwa_" + tryb] = max(fk.get("max_przerwa_" + tryb, 0.0), max(prz, default=0.0))
                    seg_start = i
            # profil wysokości (cały lot)
            ab = np.digitize(alt, ALTB) - 1
            for k in range(len(ALTB) - 1):
                m = lot & (ab == k)
                if m.any():
                    p = o["profil_alt"].setdefault(f"{ALTB[k]:g}-{ALTB[k+1]:g}", {"n": 0, "n1": 0, "n2": 0})
                    p["n"] += int(m.sum()); p["n1"] += int((m & has1).sum()); p["n2"] += int((m & has2).sum())
            # R2/R5 per epizod: piła u(t), asocjacja, przerwy
            for ep in np.unique(epi[epi >= 0]):
                m = (epi == ep) & lot
                idx = np.flatnonzero(m)
                if len(idx) < 10:
                    continue
                t = gs[idx]
                e = {"kampania": kamp, "boot": bname, "ep": int(ep), "scenario": sc[idx[0]], "T_s": round(float(t[-1] - t[0]), 2),
                     "r_max": round(float(r_xy[idx].max()), 2), "W": {}}
                fe = fz[idx]
                for gn, gthr in BRAMKI:
                  h1 = has1[idx] & (px1[idx] >= gthr); h2 = has2[idx] & h1 & (px2[idx] >= gthr)
                  for vn, vv in WAR.items():
                      e1 = eps_fix(vv, D[idx], cth[idx], tth[idx], rh[idx], alt[idx], None, None)
                      if has2.any():
                          ed = np.hypot(D[idx] / cth[idx], D2[idx] / c2[idx]) * vv["px"] / F
                          e2 = eps_fix(vv, D[idx], cth[idx], tth[idx], rh[idx], alt[idx], L[idx], ed)
                      else:
                          e2 = np.full(len(idx), np.nan)
                      for tryb in TRYBY:
                          if tryb == "1":
                              obs, ef = h1, e1
                          elif tryb == "2":
                              obs, ef = h2, e2
                          else:
                              obs, ef = h1, np.where(h2, e2, e1)
                          u_, tau_, eas, efl = piła(t, obs, ef)
                          rec = {"obs_frac": round(float(obs.mean()), 4)}
                          if obs.any():
                              rec["eps_fix_p50"] = round(float(np.median(ef[obs])), 3)
                              rec["eps_fix_p95"] = round(float(np.percentile(ef[obs], 95)), 3)
                              rec["eps_fix_max"] = round(float(ef[obs].max()), 3)
                          rec["e_as_max"] = round(float(np.nanmax(eas)), 3) if np.isfinite(eas).any() else None
                          for f in FAZY_R5:
                              mf = fe == f
                              if mf.any():
                                  k = int(np.nanargmax(np.where(mf, u_, -np.inf))) if np.isfinite(u_[mf]).any() else None
                                  rec[f] = {"tau_max": round(float(np.nanmax(tau_[mf])), 3) if np.isfinite(tau_[mf]).any() else None, "u_max": None if k is None else round(float(u_[k]), 3),
                                            "u_tau": None if k is None else round(float(tau_[k]), 3),
                                            "u_efix": None if k is None else round(float(efl[k]), 3)}
                          # start: od t0 epizodu do 1. obserwacji
                          f0 = np.flatnonzero(obs)
                          rec["start_tau"] = round(float(t[f0[0]] - t[0]), 3) if len(f0) else None
                          rec["start_efix"] = round(float(ef[f0[0]]), 3) if len(f0) else None
                          rec["start_rmax"] = round(float(r_xy[idx][: (f0[0] + 1) if len(f0) else len(idx)].max()), 2)
                          e["W"][f"{gn}|{vn}|{tryb}"] = rec
                o["epizody"].append(e)
    # R4(i): kamera misji a znaczniki (s = 10, 15, 20; off 0) — pozioma kamera kotw_r1
    intr = K1.load(gi) if os.path.exists(gi) else []
    intr.sort(key=lambda r: r["t_sim"]); it = np.array([r["t_sim"] for r in intr])
    cam = pos + np.einsum("nij,j->ni", Rm, np.array(K1.CAM))
    ipos = None
    if len(it):
        j = np.clip(np.searchsorted(it, gs), 0, len(it) - 1)
        ok = np.abs(it[j] - gs) <= 0.1
        ipos = np.array([[intr[k]["ned"][1], intr[k]["ned"][0], -intr[k]["ned"][2]] for k in j])
        ipos[~ok] = np.nan
    for s in SS:
        A = siatka(s, "0")
        d_ = A[None, :, :] - cam[:, None, :]
        b = np.einsum("nji,naj->nai", Rm, d_)
        rng = np.linalg.norm(d_, axis=2)
        fwd = b[:, :, 0]
        with np.errstate(divide="ignore", invalid="ignore"):
            cx = (IW / 2 - F * b[:, :, 1] / fwd) / IW; cy = (IH / 2 - F * b[:, :, 2] / fwd) / IH
        inside = (fwd > 0.1) & (cx >= 0) & (cx <= 1) & (cy >= 0) & (cy <= 1)
        central = inside & (np.minimum(np.minimum(cx, 1 - cx), np.minimum(cy, 1 - cy)) >= EDGE)
        dep = np.degrees(np.arcsin(np.clip(-d_[:, :, 2] / rng, -1, 1)))
        pxw1 = F / rng * np.sin(np.radians(dep))                          # krótszy bok (skrót) dla W = 1 m
        r = r4out.setdefault(f"s{int(s)}", {"n": 0, "n_kadr": 0, "n_central": 0, "n_central_5_18": 0, "n_central_orbit": 0, "n_orbit": 0,
                                            "zasieg": [], "dep": [], "pxw1": [], "n_int": 0, "hit5": 0, "hit5_5_18": 0, "hit5_orbit": 0})
        r["n"] += int(lot.sum()); r["n_kadr"] += int((inside.any(axis=1) & lot).sum()); r["n_central"] += int((central.any(axis=1) & lot).sum())
        r["n_central_5_18"] += int(((central & (rng >= 5) & (rng <= 18)).any(axis=1) & lot).sum())
        orb = fz == "orbit"
        r["n_orbit"] += int(orb.sum()); r["n_central_orbit"] += int((central.any(axis=1) & orb).sum())
        cm = central & lot[:, None]
        r["zasieg"] += np.round(rng[cm][::20], 2).tolist(); r["dep"] += np.round(dep[cm][::20], 1).tolist(); r["pxw1"] += np.round(pxw1[cm][::20], 2).tolist()
        if ipos is not None:
            di = ipos - cam
            ib = np.einsum("nji,nj->ni", Rm, di)
            iu = ib / np.linalg.norm(ib, axis=1, keepdims=True)
            unit = b / np.maximum(rng[:, :, None], 1e-9)
            ang = np.degrees(np.arccos(np.clip(np.einsum("nai,ni->na", unit, iu), -1, 1)))
            valid = ~np.isnan(ipos[:, 0]) & lot
            h5 = (central & (ang <= 5.0)).any(axis=1)
            r["n_int"] += int(valid.sum()); r["hit5"] += int((h5 & valid).sum())
            r["hit5_5_18"] += int(((central & (ang <= 5.0) & (rng >= 5) & (rng <= 18)).any(axis=1) & valid).sum())
            r["hit5_orbit"] += int((h5 & valid & orb).sum())


def nadir_uv_pts(Rm, pos, P):
    d = P - pos
    b = np.einsum("nji,nj->ni", Rm, d)
    depth = np.maximum(-b[:, 2], 1e-3)
    return IW / 2 + F * (-b[:, 1]) / depth, IH / 2 + F * (-b[:, 0]) / depth


def piła(t, obs, ef):
    """u(t) = ε_fix(ostatnia obs.) + ε_b(τ) + Δ_D5; e_as przy obserwacjach = ε_fix(poprzednia) + ε_b(τ⁻) + ε_obs."""
    n = len(t)
    u = np.full(n, np.nan); tau = np.full(n, np.nan); eas = np.full(n, np.nan); efl = np.full(n, np.nan)
    last_t, last_e = None, None
    for i in range(n):
        if obs[i]:
            if last_t is not None:
                tp = t[i] - last_t
                k = int(tp)
                eas[i] = last_e + (EPS[k] if k < len(EPS) else np.inf) + ef[i]
            last_t, last_e = t[i], ef[i]
        if last_t is None:
            continue
        tau[i] = t[i] - last_t
        k = int(tau[i])
        efl[i] = last_e
        u[i] = last_e + (EPS[k] if k < len(EPS) else np.inf) + D5
    return u, tau, eas, efl


def main():
    out, r4out = {}, {}
    for arg in sys.argv[2:]:
        kamp, pat = arg.split("=", 1)
        for d in sorted(glob.glob(pat)):
            if os.path.isdir(d):
                boot(d, kamp, out, r4out, None)
                print(".", end="", flush=True)
    json.dump({"opis": __doc__.split("\n\n")[0], "F_px": round(F, 2), "edge": EDGE, "s_m": SS, "off": OFFS, "R_E": R_E,
               "warianty": WAR, "bramki": BRAMKI, "detektory_px": DETEKTORY, "psi_zmierz_deg": PSI_Z, "px_koszyki_W1": PXB.tolist(), "alt_koszyki": ALTB.tolist(),
               "konfiguracje": out, "r4_kamera_misji": r4out}, open(sys.argv[1], "w"), ensure_ascii=False)
    print()
    print({k: len(v["epizody"]) for k, v in out.items() if not k.startswith("_")})


if __name__ == "__main__":
    main()
