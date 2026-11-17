#!/usr/bin/env python3
"""results/TEACH2/tools/teach2_lot.py — sędzia lotu długiego TEACH-II (PRE_TEACH2 §5, PROMPT_TEACH2_S1 §3); wzór
results/TEACH/tools/teach_s3_lot.py (nietknięty, importowany READ-ONLY: meta_spr, kurs_kf, przerwa_tau, POZ).

Narzędzia: teach_analyze (B1–B4, D1, źródło, ważność 3 z 4; stała T_CONT nadpisana w tym procesie parametrem — litera dostępności
z kontynuacją 600 s (D-L), w regresji 110 s), teach_s3_spr (sprawdzian lotu: replay osłony, poprawki, georeferencja — bez zmian),
nad3_s2_spr.b1_nieocenione (READ-ONLY).
  ważność = analizator ważny ∧ sprawdzian 100 % ∧ meta zgodna (teach_s3_lot.meta_spr dla łaty S, cięcie; + parametry lotu długiego
    z meta drivera: manifest i suma, T_CONT_S, WALL_MAX_CUT_S, KONT_INJECT_T) ∧ „denial” po t_entry;
  litera = B1–B4 z analizatora ∧ ticki B1 nieocenione w fazie misji = 0;
  (D-L) = D1 analizatora przy T_CONT = parametr (600 s): kontynuacja ≥ T_CONT od t_inj_sim ∧ track ≥ 0.85 ∧ pasmo ≥ 0.85 ∧ zero
    REFUSE w misji;
  werdykt PRE §5: L-C — naruszenie B1–B4; L-A — zero naruszeń i (D-L); L-B — zero naruszeń, (D-L) niespełnione (odmowa w misji:
    czas kontynuacji do odmowy i mechanizm);
  powtórka dopuszczona (PRE §5): REFUSE(τ*) w misji ≤ 3 s od flagi ULG i w chwili flagi trwała klatka fazy mapy > 0.5 s.
    „Trwała w chwili flagi”: wiersz nf fazy mapy z czasem producenta (wlaczony: ms_cechy + ms_dop) T > 0.5 s, którego przedział
    [sim wiersza, sim wiersza + T] (czas sim ≈ ścienny przy tempie ~0.95; przybliżenie nazwane) zawiera chwilę flagi.
Obserwable §3: okna po 100 s od flagi ULG do końca misji (ostatnie okno krótsze) — błąd poprawki, udział przyjętych, przerwy,
e′ i max e′/U′ (ticki utraty liczone tu tą samą formułą co analizator: e′ = |p_corr − GT(timestamp_sample)|, U′ = tabela lotu w
przedziale, koszyku i trybie osłony; regresja: max całości = analizator), τ, błąd własny EKF i kursu EKF, r_max GT, najmniejszy
zapas bariery, track, pasmo, punkty zgodne p5 / p50; mapa, oś czasu, wolne klatki fazy mapy (> 0.2 s), klatki zgubione (luki
w ciągu 5 Hz wierszy nf, osobno faza mapy i lokalizacji; całość z summary n_drop), pamięć procesu producenta (próbnik kolejki
<boot>/pamiec_producenta.jsonl, VmRSS przy klatce zamknięcia), detekcje surowe.
Zapis: <boot>/sedzia_teach2.json, <boot>/poprawki_teach2.jsonl (każda przyjęta poprawka: klatka, klatka kluczowa, wektor r,
zgodne, innowacja, p_fix NE, migawka EKF, GT NE, błąd), <boot>/georef_teach2.json (georeferencja z wiązaniami), kadry 12 na boot.
Użycie: teach2_lot.py <katalog_bootu> [--t-cont 600] [--kadry KATALOG] [--bez-parametrow-L]
"""
import glob
import json
import math
import os
import shutil
import sys

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/TEACH/tools"), os.path.join(ROOT, "results/NAD3/tools")]
import teach_analyze as A                                          # noqa: E402
import teach_s3_spr as SPR                                         # noqa: E402
import teach_s3_lot as LOT                                         # noqa: E402

MISJA = ("approach", "hold", "orbit")
UTRATA = ("KONT", "KONT_REFUSE")
EPIZOD = 10
P_L = {"rodzaj": "ciecie", "lata": "S", "epizod": EPIZOD, "powt": "L1", "t_cien": None}
INFO_MAN = os.path.join(ROOT, "results/TEACH2/teach2_manifest.json")
PARAM_L = {"T_CONT_S": 600.5, "WALL_MAX_CUT_S": 1000.0, "k2_inject_t": 200.0}
T_CONT_L = 600.0
OKNO_S = 100.0
WOLNA_S, WOLNA_POWT_S, POWT_OD_FLAGI_S = 0.2, 0.5, 3.0
N_KADROW = 12


def q(x, nd=4):
    x = [v for v in x if v is not None]
    return {"n": len(x), "p50": round(float(np.median(x)), nd), "p95": round(float(np.quantile(x, .95)), nd),
            "max": round(float(max(x)), nd)} if x else None


def meta_L(d, parametry=True):
    m = LOT.meta_spr(d, P_L)
    if not parametry:
        return m
    tm = next((r for r in A.jl(os.path.join(d, "trace.jsonl"), "meta")), {})
    s4 = tm.get("s4n") or {}
    info = json.load(open(INFO_MAN))
    pola = {"manifest": s4.get("manifest") == info["manifest"] and s4.get("sha_manifest") == info["sha256"],
            "T_CONT_S": s4.get("T_CONT_S") == PARAM_L["T_CONT_S"], "WALL_MAX_CUT_S": s4.get("WALL_MAX_CUT_S") == PARAM_L["WALL_MAX_CUT_S"],
            "KONT_INJECT_T": tm.get("k2_inject_t") == PARAM_L["k2_inject_t"]}
    m["pola"].update(pola)
    m["ok"] = all(m["pola"].values())
    m["wartosci"].update({"manifest": s4.get("manifest"), "sha_manifest": s4.get("sha_manifest"), "T_CONT_S": s4.get("T_CONT_S"),
                          "WALL_MAX_CUT_S": s4.get("WALL_MAX_CUT_S"), "k2_inject_t": tm.get("k2_inject_t")})
    return m


def kadry(d, kadry_dir, pose, n=N_KADROW):
    pl = sorted(glob.glob(os.path.join(kadry_dir, "*.png"))) if kadry_dir else []
    wyb, ost = [], None
    for f in pl:
        t = float(os.path.basename(f)[:-4])
        p, _ = pose(t)
        if p[2] < 6.0:
            continue
        if ost is None or math.hypot(p[0] - ost[0], p[1] - ost[1]) >= 3.0:
            wyb.append((t, f)); ost = p
    os.makedirs(os.path.join(d, "kadry"), exist_ok=True)
    for i in (np.linspace(0, len(wyb) - 1, min(n, len(wyb))).astype(int) if wyb else []):
        shutil.copy(wyb[i][1], os.path.join(d, "kadry", os.path.basename(wyb[i][1])))
    return {"kadry_stanowiska": len(pl), "do_repo": min(n, len(wyb))}


def ticki_utraty(d, rama, ep, gt):
    """Ticki utraty epizodu: (sim, e′, U′, τ, zapas bariery, r_est) — ta sama formuła co teach_analyze.analyze (A.T3 ustawione)."""
    u = A.ulg(d)
    v = u["vehicle_local_position"]
    vt, vts = v["timestamp"] / 1e6, v["timestamp_sample"] / 1e6
    vp = np.stack([v["x"], v["y"], v["z"]], 1)
    gt_t = np.array([g["sim"] for g in gt])
    gt_ned = np.array([[g["y"], g["x"], -g["z"]] for g in gt])
    import bisect

    def t_probki(p, t_ref, okno=(-0.4, 0.1)):
        i0, i1 = bisect.bisect_left(vt, t_ref + okno[0]), bisect.bisect_right(vt, t_ref + okno[1])
        if i1 <= i0:
            return None
        dd = np.linalg.norm(vp[i0:i1] - np.asarray(p, float), axis=1)
        return float(vts[i0 + int(np.argmin(dd))])
    out = []
    for r in rama:
        n2, ph = r.get("nad2"), r.get("ph")
        if r["ep"] != ep or ph not in UTRATA or n2 is None:
            continue
        i, tr, j = n2.get("przedzial"), n2.get("tryb"), (r.get("nadir") or {}).get("j")
        tau = (r.get("nadir") or {}).get("tau")
        w = {"sim": r["sim"], "tick": r["tick"], "tau": tau, "e": None, "U": None, "zapas": None, "r_est": n2.get("r_est"),
             "faza": r.get("phase"), "desc": bool(r.get("desc"))}
        if i is not None and j is not None:
            w["U"] = A.U_of(i, j, tr)
            w["zapas"] = A.NS.r_nad3(A.T3, i, j, tr, A.R_E) - n2["r_est"]
            ts = t_probki(r["p_ekf"], r["sim"])
            if ts is not None:
                g = np.array([np.interp(ts, gt_t, gt_ned[:, k]) for k in range(3)])
                w["e"] = float(math.hypot(r["p_corr"][0] - g[0], r["p_corr"][1] - g[1]))
        out.append(w)
    return out


def faza_mapy(nf, t_flag, t_ep):
    """Wolne klatki fazy mapy, klatki zgubione (luki ciągu 5 Hz), wolna klatka w chwili flagi."""
    wolne, trwa = [], []
    for r in nf:
        w = (r.get("teach") or {}).get("wlaczony")
        if not w:
            continue
        T = (w["ms_cechy"] + w["ms_dop"]) / 1e3
        if T > WOLNA_S:
            wolne.append({"sim_wiersza": r["sim"], "t_ep": round(w["sim"] - t_ep, 2), "kadr": w["n"], "kf": w["kf"], "n_dop": w["n_dop"],
                          "s": round(T, 3)})
        if t_flag is not None and r["sim"] <= t_flag <= r["sim"] + T + 1e-6:
            trwa.append({"sim_wiersza": r["sim"], "s": round(T, 3), "kf": w["kf"], "n_dop": w["n_dop"]})
    sims = [r["sim"] for r in nf]
    t_zamk = next((r["sim"] for r in nf if (r.get("teach") or {}).get("georef")), None)
    zg_mapa = zg_lok = 0
    for a, b in zip(sims[:-1], sims[1:]):
        n = int(round((b - a) / 0.2)) - 1
        if n <= 0:
            continue
        if t_zamk is None or b <= t_zamk:
            zg_mapa += n
        else:
            zg_lok += n
    wolna_flaga = [x for x in trwa if x["s"] > WOLNA_POWT_S]
    return {"wolne_gt_0p2s": wolne, "n_wolnych": len(wolne), "zgubione_faza_mapy": zg_mapa, "zgubione_lokalizacja": zg_lok,
            "klatka_trwajaca_w_chwili_flagi": trwa[0] if trwa else None,
            "wolna_gt_0p5s_w_chwili_flagi": bool(wolna_flaga), "przyblizenie": "przedział klatki w czasie sim [sim wiersza, + czas producenta]"}


def pamiec(d, nf):
    p = os.path.join(d, "pamiec_producenta.jsonl")
    if not os.path.exists(p):
        return None
    pr = [json.loads(l) for l in open(p) if l.strip()]
    zam = next((r for r in nf if (r.get("teach") or {}).get("georef")), None)
    if not pr or zam is None:
        return {"probek": len(pr)}
    przed = [x for x in pr if x["mono"] <= zam["mono"] and x.get("rss_mb") is not None]
    return {"probek": len(pr), "vmrss_mb_przy_zamknieciu": przed[-1]["rss_mb"] if przed else None,
            "vmhwm_mb_przy_zamknieciu": przed[-1].get("hwm_mb") if przed else None,
            "vmrss_mb_max": max((x["rss_mb"] for x in pr if x.get("rss_mb") is not None), default=None)}


def werdykt(litera_ok, wazny, dl, odmowa, powtorka):
    if not litera_ok:
        return "L-C"
    if powtorka:
        return "powtorka"
    if not wazny:
        return None
    if dl:
        return "L-A"
    return "L-B"


def sedzia(d, t_cont=T_CONT_L, kadry_dir=None, parametry=True):
    A.T_CONT = float(t_cont)                                        # (D-L): kontynuacja jako parametr (moduł nietknięty)
    a = A.analyze(d)
    s = SPR.sprawdz(d)
    import nad3_s2_spr as N2S
    b1n = N2S.b1_nieocenione(d)
    tr = os.path.join(d, "trace.jsonl")
    ev = A.jl(tr, "event")
    gt = sorted(A.jl(tr, "gt"), key=lambda r: r["sim"])
    armed = next((e for e in ev if e.get("ev") == "armed"), None)
    gx0, gy0 = armed["gt_home"] if armed else (0.0, 0.0)
    rama = sorted(A.jl(os.path.join(d, "rama.jsonl")), key=lambda r: r["tick"])
    tks = A.jl(tr, "tk")
    tk = {r["tick"]: r for r in tks}
    nf = A.jl(os.path.join(d, "nadir_obs.jsonl"), "nf")
    gq_t = np.array([g["sim"] for g in gt])
    gt_ned = np.array([[g["y"], g["x"], -g["z"]] for g in gt])
    GT = lambda t: np.array([np.interp(t, gq_t, gt_ned[:, i]) for i in range(3)])

    def pose(t):
        i = int(np.clip(np.searchsorted(gq_t, t), 1, len(gq_t) - 1))
        g = gt[i] if abs(gt[i]["sim"] - t) < abs(gt[i - 1]["sim"] - t) else gt[i - 1]
        return [g["x"], g["y"], g["z"]], [g["qw"], g["qx"], g["qy"], g["qz"]]
    meta = meta_L(d, parametry)
    cut = next((e for e in ev if e.get("ev") == "denial"), None)
    st = next((e for e in ev if e.get("ev") == "episode_start"), None)
    ends = {e["episode_id"]: e for e in ev if e.get("ev") == "episode_end"}
    zp = {e["episode_id"]: e["sim"] for e in ev if e.get("ev") == "zejscie_planowe"}
    te = a.get("teach") or {}
    ww = te.get("warunki_waznosci") or {}
    oc = te.get("os_czasu") or {}
    t_flag = oc.get("flaga_ulg")
    out = {"boot": os.path.basename(d.rstrip("/")), "t_cont": float(t_cont), "tempo": (a.get("tempo") or {}).get("dsim_dwall_settle"),
           "analizator_wazny": a.get("wazny"), "warunki_waznosci": ww,
           "sprawdzian": {"ok": s["ok"], "procent": s["procent"], "oslona_ticki": s["oslona"]["n"], "poprawki": s["poprawki"].get("n"),
                          "georef": {k: s["georef"].get(k) for k in ("d_theta_deg", "d_t_m", "ok")}}, "meta": meta}
    o = next((x for x in a.get("epizody", []) if x["ciecie"]), None)
    ep = o["episode_id"] if o else (st or {}).get("episode_id")
    t_entry = (ends.get(ep) or {}).get("t_entry")
    out["wejscie"] = cut is not None and t_entry is not None and cut.get("inj_t_rel", -1) >= t_entry
    nwaz = []
    if not out["wejscie"]:
        nwaz.append("wejscie")
    if not s["ok"] or not meta["ok"]:
        nwaz.append("przyrzad")
    if not all(ww.values()) if ww else True:
        nwaz.append("swiat_kod")
    out["niewaznosc"] = nwaz
    out["wazny"] = not nwaz and bool(a.get("wazny"))
    out["b1_nieocenione"] = b1n
    out["b1_nieocenione_w_misji"] = sum(v["faza_misji"] for v in b1n["przyczyny"].values())
    t_ep0 = (st or {}).get("sim")
    if o is None:
        out.update(litera_ok=False, werdykt=None, powod="brak epizodu cięcia w analizatorze")
        json.dump(out, open(os.path.join(d, "sedzia_teach2.json"), "w"), ensure_ascii=False, indent=1, default=A._json_default)
        return out
    ms = [r for r in rama if r["ep"] == ep and r.get("phase") in MISJA and not r.get("desc") and r["sim"] < zp.get(ep, 1e18)]
    t_kon = ms[-1]["sim"] if ms else None
    e = {"episode_id": ep, "scenario_id": o["scenario_id"], "B": {k: (o.get(k) or {}).get("ok") for k in ("B1", "B2", "B3", "B4")},
         "B_szczegoly": {k: o.get(k) for k in ("B1", "B2", "B3", "B4")}, "D_L": o.get("D1"), "max_e_do_U": o["B1"]["max_e_do_U"],
         "e_corr": o.get("e_corr"), "tau": o.get("tau"), "obserwable": o.get("nad3_obserwable"), "t_entry": t_entry,
         "okno_misji": [ms[0]["sim"], t_kon] if ms else None, "zapas_bariery_min": o.get("zapas_bariery_min")}
    out["litera_ok"] = bool(o.get("bezpieczenstwo_ok") and a.get("bezpieczenstwo_ok") and out["b1_nieocenione_w_misji"] == 0)
    out["DL_dostepne"] = bool((o.get("D1") or {}).get("dostepne"))
    # odmowa w misji
    ref = next((r for r in rama if r["ep"] == ep and r.get("ph") == "KONT_REFUSE" and r["sim"] < zp.get(ep, 1e18)), None)
    fm = faza_mapy(nf, t_flag, t_ep0 or 0.0)
    G = te.get("georef")
    geo_full = next(((r.get("teach") or {}).get("georef") for r in nf if (r.get("teach") or {}).get("georef")), None)
    kf_gt = [pose(k["sim"])[0][:2] for k in (geo_full or {}).get("kf", [])]
    odm = None
    if ref is not None:
        g = min(gt, key=lambda x: abs(x["sim"] - ref["sim"]))
        przy = (tk.get(ref["tick"]) or {}).get("cause")
        odm = {"tick": ref["tick"], "sim": ref["sim"], "od_ciecia_s": round(ref["sim"] - cut["t_inj_sim"], 2) if cut else None,
               "od_flagi_s": round(ref["sim"] - t_flag, 3) if t_flag is not None else None, "przyczyna": przy,
               "r_est": round(ref["nad2"]["r_est"], 3), "bariera_R_k": ref.get("R_k"), "r_gt": round(math.hypot(g["x"] - gx0, g["y"] - gy0), 3),
               "tau": (ref.get("nadir") or {}).get("tau"), "kontynuacja_do_odmowy_s": round(ref["sim"] - cut["t_inj_sim"], 3) if cut else None}
        if przy == "τ*":
            pz = LOT.przerwa_tau(nf, ref["sim"], t_flag)
            kad = [r for r in nf if (pz["poczatek"] is None or r["sim"] > pz["poczatek"]) and r["sim"] <= ref["sim"]]
            pz["zgodne_w_kadrach"] = [(r.get("teach") or {}).get("zgodne") for r in kad]
            odl = [min(math.hypot(pose(r["sim"])[0][0] - k[0], pose(r["sim"])[0][1] - k[1]) for k in kf_gt) for r in kad] if kf_gt else []
            pz["odl_od_najblizszej_kf_m"] = {"min": round(min(odl), 2), "max": round(max(odl), 2)} if odl else None
            odm["przerwa_zrodla"] = pz
    e["odmowa_w_misji"] = odm
    out["powtorka_dopuszczona"] = bool(odm and odm["przyczyna"] == "τ*" and odm["od_flagi_s"] is not None
                                       and odm["od_flagi_s"] <= POWT_OD_FLAGI_S and fm["wolna_gt_0p5s_w_chwili_flagi"])
    # okna po 100 s
    tu = ticki_utraty(d, rama, ep, gt)
    tu_m = [w for w in tu if w["faza"] in MISJA and not w["desc"] and (t_kon is None or w["sim"] <= t_kon)]
    eU_all = max((w["e"] / w["U"] for w in tu if w["e"] is not None and w["U"]), default=0.0)
    out["regresja_eU"] = {"max_e_do_U_tu": round(eU_all, 4), "analizator": o["B1"]["max_e_do_U"],
                          "zgodne": abs(round(eU_all, 4) - o["B1"]["max_e_do_U"]) < 1e-4}
    fx = []
    for r in nf:
        f = r.get("fx") or {}
        if f.get("ok"):
            gg = GT(f["t_frame"])
            tch = r.get("teach") or {}
            fx.append({"sim": r["sim"], "k": tch.get("k"), "r": tch.get("r"), "zgodne": tch.get("zgodne"), "innowacja": tch.get("innowacja"),
                       "tau": tch.get("tau"), "p_fix_ne": f.get("p_fix_ne"), "ekf_pos": r.get("ekf_pos"), "ekf_q": r.get("ekf_q"),
                       "gt_ne": [round(float(gg[0]), 4), round(float(gg[1]), 4)],
                       "blad": round(float(math.hypot(f["p_fix_ne"][0] - gg[0], f["p_fix_ne"][1] - gg[1])), 4)})
    with open(os.path.join(d, "poprawki_teach2.jsonl"), "w") as f:
        for x in fx:
            f.write(json.dumps(x) + "\n")
    if geo_full is not None:
        json.dump(geo_full, open(os.path.join(d, "georef_teach2.json"), "w"), ensure_ascii=False)
    import teach_s2_cien as SC
    sys.path[:0] = [os.path.join(ROOT, "results/ORTO_RECON/tools")]
    import orto_r2 as R2
    from harness import nadir_fix as NF

    def okno(t0, t1):
        f_ok = [x for x in fx if t0 <= x["sim"] < t1]
        kad = [r for r in nf if t0 <= r["sim"] < t1 and (r.get("teach") or {}).get("faza") == "lok"]
        ts = [t0] + [x["sim"] for x in f_ok] + [t1]
        gaps = np.diff(ts)
        tw = [w for w in tu_m if t0 <= w["sim"] < t1]
        rm = [r for r in ms if t0 <= r["sim"] < t1]
        ekf = [math.hypot(r["p_ekf"][0] - r["gt"][1], r["p_ekf"][1] - r["gt"][0]) for r in rm if r.get("gt") and r.get("p_ekf")]
        kurs = []
        for r in kad:
            if r.get("ekf_q"):
                _, qq = pose(r["sim"])
                dk = (SC.kurs(R2.rotm(qq)) - SC.kurs(NF.ekf_R(r["ekf_q"])) + math.pi) % (2 * math.pi) - math.pi
                kurs.append(abs(math.degrees(dk)))
        rg = [math.hypot(g["x"] - gx0, g["y"] - gy0) for g in gt if t0 <= g["sim"] < t1]
        tw_k = [r for r in tks if r.get("ep") == ep and t0 <= r["sim"] < t1 and not r.get("desc")]
        dg = [math.hypot(GT(r["sim"])[0] - r["intr"][0], GT(r["sim"])[1] - r["intr"][1]) for r in tw_k if r.get("intr") is not None]
        zg = [((r.get("teach") or {}).get("zgodne") or 0) for r in kad]
        return {"okno": [round(t0, 3), round(t1, 3)], "blad_poprawki": q([x["blad"] for x in f_ok]),
                "kadry": len(kad), "przyjete": len(f_ok), "udzial": round(len(f_ok) / len(kad), 4) if kad else None,
                "przerwa_max": round(float(gaps.max()), 3), "przerwy_gt_115": int((gaps > 1.15).sum()),
                "e": q([w["e"] for w in tw]), "max_e_do_U": round(max((w["e"] / w["U"] for w in tw if w["e"] is not None and w["U"]), default=0.0), 4),
                "tau": q([w["tau"] for w in tw]), "blad_ekf": q(ekf, 3), "blad_kursu_ekf_deg": q(kurs, 3),
                "r_max_gt": round(max(rg), 3) if rg else None, "zapas_bariery_min": round(min((w["zapas"] for w in tw if w["zapas"] is not None), default=float("nan")), 3) if tw else None,
                "track": round(float(np.mean([r["trk_valid"] for r in tw_k])), 3) if tw_k else None,
                "pasmo": round(float(np.mean([6.0 <= x <= 10.0 for x in dg])), 3) if dg else None,
                "zgodne_p5": int(np.quantile(zg, .05)) if zg else None, "zgodne_p50": int(np.median(zg)) if zg else None}
    okna, cala = [], None
    if t_flag is not None and t_kon is not None:
        t = t_flag
        while t < t_kon - 1e-6:
            okna.append(okno(t, min(t + OKNO_S, t_kon + 1e-6)))
            t += OKNO_S
        cala = okno(t_flag, t_kon + 1e-6)
    out["misja"] = cala
    out["okna_100s"] = okna
    out["epizod"] = e
    rgm = [math.hypot(g["x"] - gx0, g["y"] - gy0) for g in gt if ms and ms[0]["sim"] <= g["sim"] <= t_kon]
    e["r_max_gt_misja"] = round(max(rgm), 3) if rgm else None
    e["r_max_gt_po_fladze"] = round(max([math.hypot(g["x"] - gx0, g["y"] - gy0) for g in gt if t_flag is not None and t_flag <= g["sim"] <= (t_kon or 0)]
                                        or [float("nan")]), 3)
    out["faza_mapy"] = fm
    out["pamiec_producenta"] = pamiec(d, nf)
    out["zrodlo"] = {k: te.get(k) for k in ("blad_poprawki", "blad_poprawki_polowy", "udzial_przyjetych_okna", "przerwy", "os_czasu",
                                            "opoznienie_pierwszej_poprawki_s", "skok_delta_pierwsza_m", "georef", "czas_ms", "n_drop",
                                            "n_img", "detekcje", "chwila_waznosci")}
    out["zrodlo"]["kurs_kf"] = LOT.kurs_kf(d, nf, pose)
    out["kadry"] = kadry(d, kadry_dir, pose)
    out["werdykt"] = werdykt(out["litera_ok"], out["wazny"], out["DL_dostepne"], odm, out["powtorka_dopuszczona"])
    json.dump(out, open(os.path.join(d, "sedzia_teach2.json"), "w"), ensure_ascii=False, indent=1, default=A._json_default)
    return out


if __name__ == "__main__":
    ar = sys.argv[1:]
    tc = float(ar[ar.index("--t-cont") + 1]) if "--t-cont" in ar else T_CONT_L
    kd = ar[ar.index("--kadry") + 1] if "--kadry" in ar else None
    o = sedzia(ar[0], tc, kd, parametry="--bez-parametrow-L" not in ar)
    print(json.dumps({k: o.get(k) for k in ("boot", "wazny", "niewaznosc", "litera_ok", "wejscie", "DL_dostepne", "werdykt",
                                            "powtorka_dopuszczona", "regresja_eU")}, ensure_ascii=False))
