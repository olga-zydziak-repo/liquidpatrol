#!/usr/bin/env python3
"""results/TEACH/tools/teach_s2_cien.py — ocena bootu cienia S2 (PROMPT_TEACH_S2 §4 „Cień”, ANEKS_TEACH-2 §3; 0 bootów — tylko zapis).

Okno oceny: od chwili cienia (meta nadir_obs „teach”.„t_cien”) do końca misji epizodu (ostatni tick rama.jsonl epizodu w fazie
approach / hold / orbit, bez zejścia).
Bramka obrazu (PRE §6 z brzmieniem ANEKS_TEACH-2): największy błąd przyjętej poprawki |p_fix − GT(t_fix)| ≤ 1.00 m; przyjętych ≥ 90%
kadrów okna (kadry = wiersze nf w oknie); zero detekcji zgodnych z manifestem w całym boocie (teach_analyze.zgodnosc_detekcji).
Do raportu: błąd p50 / p95 / max; przerwy z pokryciem (teach_analyze.zrodlo_teach, flaga = chwila cienia); klatki kluczowe
i wiązania; reszta kursu klatek kluczowych (θ_k wobec błędu kursu EKF e_k = kurs GT − kurs EKF w chwili klatki) i środka (t_k wobec
punktu pod kamerą z pozy GT); czas producenta na klatkę i klatki zgubione (summary n_drop); opóźnienie pierwszej poprawki; udział
pikseli nieruchomych w kadrach rejestratora (kadry z wysokości ≥ 6 m, rozstawione ≥ 3 m w poziomie: odchylenie jasności piksela
< 2.0 w ≥ 12 kadrach ⇒ nieruchomy); sprawdzian F1 na żywo (zmiany flagi rzeczywistej gnss_rz, zatrzask t_flagi_rz w chwili startu,
zamknięcia mapy). Wybór 6 kadrów rejestratora do repo (równo w czasie lotu na wysokości).
Użycie: teach_s2_cien.py <katalog_bootu> <katalog_kadrów_stanowiska>. Wyjście: <boot>/cien_s2.json, <boot>/kadry/ (6 PNG),
<boot>/maska_kandydat.png (gdy udział ≥ 0.5%).
"""
import glob
import json
import math
import os
import shutil
import sys

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/TEACH/tools"), os.path.join(ROOT, "results/ORTO_RECON/tools"),
                os.path.join(ROOT, "results/TEACH_RECON/tools")]
import teach_analyze as A                                            # noqa: E402

MISJA = ("approach", "hold", "orbit")
PROG_BLAD, PROG_PRZYJ, PROG_MASKI = 1.00, 0.90, 0.005


def kurs(R):
    return math.atan2(R[1, 0], R[0, 0])


def ocen(d, kadry_dir):
    import cv2
    import orto_r2 as R2
    from harness import nadir_fix as NF
    nfm = A.jl(os.path.join(d, "nadir_obs.jsonl"))
    meta = next(r for r in nfm if r.get("t") == "meta")
    nf = [r for r in nfm if r.get("t") == "nf"]
    t_c = float(meta["teach"]["t_cien"])
    gt = sorted(A.jl(os.path.join(d, "trace.jsonl"), "gt"), key=lambda r: r["sim"])
    gt_t = np.array([g["sim"] for g in gt])
    gt_ned = np.array([[g["y"], g["x"], -g["z"]] for g in gt])
    GTp = lambda t: np.array([np.interp(t, gt_t, gt_ned[:, i]) for i in range(3)])
    g2 = R2.GT.__new__(R2.GT)
    g2.t, g2.p = gt_t, np.array([[g["x"], g["y"], g["z"]] for g in gt])
    q = np.array([[g["qw"], g["qx"], g["qy"], g["qz"]] for g in gt])
    for i in range(1, len(q)):
        if q[i] @ q[i - 1] < 0:
            q[i] = -q[i]
    g2.q = q
    pose = lambda t: (lambda r: (r[0].tolist(), r[1].tolist()))(g2(t))
    ev = A.jl(os.path.join(d, "trace.jsonl"), "event")
    st = next(e for e in ev if e.get("ev") == "episode_start")
    armed = next(e["sim"] for e in ev if e.get("ev") == "armed")
    rama = A.jl(os.path.join(d, "rama.jsonl"))
    mis = [r["sim"] for r in rama if r.get("ep") == st["episode_id"] and r.get("phase") in MISJA and not r.get("desc")]
    t_k = max(mis)
    okno = [r for r in nf if t_c <= r["sim"] <= t_k]
    przyj = [r for r in okno if r["fx"]["ok"]]
    err = [float(math.hypot(r["fx"]["p_fix_ne"][0] - GTp(r["fx"]["t_frame"])[0], r["fx"]["p_fix_ne"][1] - GTp(r["fx"]["t_frame"])[1]))
           for r in przyj]
    det = A.zgodnosc_detekcji([(r["sim"], r.get("det")) for r in nf], pose)
    z = A.zrodlo_teach(d, GTp, t_c, t_k, pose)
    bramka = {"blad_max": round(max(err), 4) if err else None, "udzial_przyjetych": round(len(przyj) / len(okno), 4) if okno else None,
              "zgodne_z_manifestem": det["zgodne"]["n"]}
    bramka["ok"] = bool(err) and max(err) <= PROG_BLAD and len(przyj) / len(okno) >= PROG_PRZYJ and det["zgodne"]["n"] == 0
    # klatki kluczowe wobec GT
    kam = R2.Kam(R2.kamera())
    geo = next(r["teach"]["georef"] for r in nf if (r.get("teach") or {}).get("georef"))
    nf_t = {round(r["sim"], 3): r for r in nf}
    res_th, res_t = [], []
    for k in geo["kf"]:
        r = nf_t.get(round(k["sim"], 3))
        p, qq = pose(k["sim"])
        Rg = R2.rotm(qq)
        C = kam.poza(np.array(p), Rg)[0]
        if r is not None and r.get("ekf_q"):
            e = (kurs(Rg) - kurs(NF.ekf_R(r["ekf_q"])) + math.pi) % (2 * math.pi) - math.pi
            res_th.append(abs(((math.radians(k["theta_deg"]) - e) + math.pi) % (2 * math.pi) - math.pi))
        res_t.append(float(np.hypot(k["t"][0] - C[0], k["t"][1] - C[1])))
    # piksele nieruchome w kadrach rejestratora
    pl = sorted(glob.glob(os.path.join(kadry_dir, "*.png")))
    wyb, ost = [], None
    for f in pl:
        t = float(os.path.basename(f)[:-4])
        p, _ = pose(t)
        if p[2] < 6.0:
            continue
        if ost is None or math.hypot(p[0] - ost[0], p[1] - ost[1]) >= 3.0:
            wyb.append((t, f)); ost = p
    nier = None
    if len(wyb) >= 12:
        stos = np.stack([cv2.imread(f, cv2.IMREAD_GRAYSCALE).astype(np.float32) for _, f in wyb])
        sd = stos.std(0)
        m = sd < 2.0
        nier = {"n_kadrow": len(wyb), "udzial": round(float(m.mean()), 5), "pikseli": int(m.sum())}
        if m.mean() >= PROG_MASKI:
            mk = cv2.dilate(m.astype(np.uint8) * 255, np.ones((11, 11), np.uint8))
            cv2.imwrite(os.path.join(d, "maska_kandydat.png"), np.where(mk > 0, 0, 255).astype(np.uint8))
            nier["maska_kandydat"] = "maska_kandydat.png (0 = piksel pominięty, margines 5 px)"
    os.makedirs(os.path.join(d, "kadry"), exist_ok=True)
    if wyb:
        for i in np.linspace(0, len(wyb) - 1, min(6, len(wyb))).astype(int):
            shutil.copy(wyb[i][1], os.path.join(d, "kadry", os.path.basename(wyb[i][1])))
    # F1 na żywo
    zmiany, prev = [], "x"
    for r in nf:
        if r.get("gnss_rz") != prev:
            zmiany.append([r["sim"], r.get("gnss_rz"), r.get("t_flagi_rz")]); prev = r.get("gnss_rz")
    przy_starcie = next(r for r in nf if r["sim"] >= armed)
    zamk = [r["sim"] for r in nf if (r.get("teach") or {}).get("georef")]
    q_ = lambda x: {"p50": round(float(np.median(x)), 4), "p95": round(float(np.quantile(x, .95)), 4), "max": round(max(x), 4)} if x else None
    try:
        sm = json.load(open(os.path.join(d, "nadir_obs.jsonl.summary.json")))
    except (OSError, ValueError):
        sm = {}
    out = {"boot": os.path.basename(d.rstrip("/")), "t_cien": t_c, "koniec_misji": t_k, "kadry_okna": len(okno), "przyjete_okna": len(przyj),
           "bramka_obrazu": bramka, "blad_poprawki_okna": q_(err), "detekcje": det,
           "przerwy": z.get("przerwy"), "opoznienie_pierwszej_poprawki_s": z.get("opoznienie_pierwszej_poprawki_s"),
           "georef": z.get("georef"), "kf_reszta_kursu_deg": q_([math.degrees(x) for x in res_th]), "kf_reszta_srodka_m": q_(res_t),
           "czas_ms": z.get("czas_ms"), "n_drop": sm.get("n_drop"), "n_img": sm.get("n_img"), "n_proc": sm.get("n_proc"),
           "piksele_nieruchome": nier, "kadry_rejestratora": len(pl),
           "F1": {"zmiany_flagi_rzeczywistej": zmiany, "start_sim": armed, "zatrzask_w_chwili_startu": przy_starcie.get("t_flagi_rz"),
                  "zamkniecia": zamk, "zamkniecie_w_chwili_cienia": len(zamk) == 1 and zamk[0] >= t_c,
                  "ok": przy_starcie.get("t_flagi_rz") is None and len(zamk) == 1},
           "fazy": sorted({(r.get("teach") or {}).get("faza") for r in nf} - {None})}
    json.dump(out, open(os.path.join(d, "cien_s2.json"), "w"), ensure_ascii=False, indent=1, default=str)
    return out


if __name__ == "__main__":
    o = ocen(sys.argv[1], sys.argv[2])
    print(json.dumps({k: v for k, v in o.items() if k not in ("detekcje",)}, ensure_ascii=False, indent=1, default=str)[:4000])
