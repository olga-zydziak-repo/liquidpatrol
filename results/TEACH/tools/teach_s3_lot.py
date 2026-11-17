#!/usr/bin/env python3
"""results/TEACH/tools/teach_s3_lot.py — sędzia pojedynczego lotu bramki S3 TEACH (PROMPT_TEACH_S3 §3, PRE_TEACH §6 z ANEKS_TEACH-2/3/4)
i par powtórzeń (§3 „Pary”); wzór results/NAD3/tools/nad3_s3_lot.py (nietknięty).

Wejście: katalog bootu po locie (po wyciągu ULG). Narzędzia: teach_analyze (B1–B5, D1, źródło, ważność 3 z 4), teach_s3_spr (czwarty
warunek: replay osłony, poprawki, georeferencja — 100%), nad3_s2_spr.b1_nieocenione (READ-ONLY: ticki utraty nieocenione z przyczyną),
teach_s2_cien.ocen (nominały: obserwacja cienia, kadry; READ-ONLY).
  ważność = analizator ważny (zero detekcji zgodnych z manifestem; żaden kadr mapy, klatka kluczowa ani wiązanie ≥ chwila flagi ULG —
    w nominale chwila cienia; georeferencja raz) ∧ sprawdzian 100% ∧ meta zgodna z pozycją ∧ (cięcie) „denial” po t_entry;
  rodzaj nieważności: „wejscie” (cięcie bez wejścia — rezerwa), „przyrzad” (sprawdzian < 100%, meta), „swiat_kod” (detekcja zgodna,
    mapa po fladze, drugie zamknięcie) — reguły §4 w kolejce;
  litera = B1–B4 (cięcie) / B1–B5 (nominał) z analizatora ∧ ticki B1 nieocenione w fazie misji = 0;
  odmowa w misji (cięcie): pierwszy tick KONT_REFUSE przed zejściem planowym — tick, czas od cięcia, przyczyna (tk „cause”), r_est,
    bariera R_k, r_GT; przy τ*: przerwa źródła, która do niej doprowadziła (początek, długość, pokrycie z analizatora, powody
    odrzucenia kadrów przerwy: brak_dopasowania / reguła / inne);
  obserwable §3: błąd poprawki (p50/p95/max, połowy okna), udział przyjętych, e′, max e′/U′, τ w misji, przerwy, oś czasu, mapa,
    czas producenta, klatki zgubione, kurs klatek kluczowych wobec GT przed i po georeferencji, największy błąd własny EKF w misji,
    r_max GT, track, pasmo, t_entry, odrzucenia bramki predykcji tracku.
Kadry: sześć kadrów rejestratora na boot do <boot>/kadry/ (jak S2: wysokość ≥ 6 m, rozstaw ≥ 3 m, równomiernie).
Wyjście: <boot>/sedzia_s3.json. Użycie: teach_s3_lot.py <katalog_bootu> <pozycja 1–14> [katalog_kadrów]
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

MISJA = ("approach", "hold", "orbit")
UTRATA = ("KONT", "KONT_REFUSE")
C05, C10 = 5, 10
TSHA = "7a56ba1b95f206415709d88595f868e07577d94bbeacc56f8065df9831688642"
SHA_OBS = "db96a4a71ebce8d38d704e9f66b191c6788045534c7401fc360daf8f3fd3ffff"
SHA_MAP = "4eefeddacbf6977d7e7e7bd544777c55260c622be899be667642aba9fb1fcd7e"
MODEL = "x500_teach_flow_0"
PLAN = [  # (pozycja, rodzaj, łata, epizod, powtórzenie, t_cien)
    (1, "ciecie", "S", C05, "a", None), (2, "ciecie", "S", C10, "a", None), (3, "ciecie", "S", C05, "b", None),
    (4, "ciecie", "S", C10, "b", None), (5, "nominal", "S", C10, "N1", 176.5),
    (6, "ciecie", "M", C05, "a", None), (7, "ciecie", "M", C10, "a", None), (8, "ciecie", "M", C05, "b", None),
    (9, "ciecie", "M", C10, "b", None), (10, "nominal", "J", C05, "N2", 173.6),
    (11, "ciecie", "J", C05, "a", None), (12, "ciecie", "J", C10, "a", None), (13, "ciecie", "J", C05, "b", None),
    (14, "ciecie", "J", C10, "b", None),
]
POZ = {p[0]: {"rodzaj": p[1], "lata": p[2], "epizod": p[3], "powt": p[4], "t_cien": p[5]} for p in PLAN}


def tor_sha():
    return json.load(open(os.path.join(ROOT, "results/TEACH/s1/tor.json")))["sha256_toru"]


def meta_spr(d, P):
    tr = os.path.join(d, "trace.jsonl")
    m = next((r for r in A.jl(tr, "meta")), {})
    te = m.get("teach") or {}
    ev = A.jl(tr, "event")
    pr = next((e for e in ev if e.get("ev") == "teach_producent"), {})
    nm = next((r for r in A.jl(os.path.join(d, "nadir_obs.jsonl"), "meta")), {}).get("teach") or {}
    try:
        mf = json.load(open(os.path.join(d, "manifest.json"))).get("teach") or {}
    except (OSError, ValueError):
        mf = {}
    cien = P["rodzaj"] == "nominal"
    t_c = nm.get("t_cien")
    pola = {"tabela": (te.get("oslona") or {}).get("sha256_tabeli") == TSHA and mf.get("tabela_sha256") == TSHA,
            "tor": pr.get("tor") == tor_sha() and pr.get("meta_tor") == tor_sha() and nm.get("sha256_toru") == tor_sha()
                   and mf.get("sha256_toru") == tor_sha() and bool(pr.get("zgodny")),
            "sha_producenta": te.get("sha_producent") == SHA_MAP and te.get("sha_obs") == SHA_OBS,
            "lata": m.get("world") == f"world_teach_{P['lata']}" and mf.get("lata") == P["lata"],
            "model": m.get("model") == MODEL,
            "cien": nm.get("cien") is cien and bool(pr.get("cien")) is cien and mf.get("cien") is cien
                    and ((t_c is None and not cien) or (cien and t_c is not None and abs(float(t_c) - P["t_cien"]) < 1e-9)),
            "etap": mf.get("etap") == "s3"}
    return {"pola": pola, "ok": all(pola.values()),
            "wartosci": {"world": m.get("world"), "model": m.get("model"), "sha_producent": te.get("sha_producent"),
                         "sha_obs": te.get("sha_obs"), "tor": pr.get("tor"), "cien": nm.get("cien"), "t_cien": t_c, "etap": mf.get("etap")}}


def kurs_kf(d, nf, pose):
    """Błąd kursu klatek kluczowych wobec GT przed georeferencją (|e_k| = |kurs GT − kurs EKF|) i po (|θ_k − e_k|), stopnie."""
    import teach_s2_cien as SC                                      # READ-ONLY: kurs(R)
    sys.path[:0] = [os.path.join(ROOT, "results/ORTO_RECON/tools")]
    import orto_r2 as R2
    from harness import nadir_fix as NF
    geo = next(((r.get("teach") or {}).get("georef") for r in nf if (r.get("teach") or {}).get("georef")), None)
    if geo is None:
        return None
    nf_t = {round(r["sim"], 3): r for r in nf}
    przed, po = [], []
    for k in geo["kf"]:
        r = nf_t.get(round(k["sim"], 3))
        if r is None or not r.get("ekf_q"):
            continue
        _, qq = pose(k["sim"])
        e = (SC.kurs(R2.rotm(qq)) - SC.kurs(NF.ekf_R(r["ekf_q"])) + math.pi) % (2 * math.pi) - math.pi
        przed.append(abs(math.degrees(e)))
        po.append(abs(math.degrees(((math.radians(k["theta_deg"]) - e) + math.pi) % (2 * math.pi) - math.pi)))
    return {"przed_max_deg": round(max(przed), 3) if przed else None, "po_max_deg": round(max(po), 3) if po else None, "n": len(po)}


def kadry(d, kadry_dir, pose):
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
    for i in (np.linspace(0, len(wyb) - 1, min(6, len(wyb))).astype(int) if wyb else []):
        shutil.copy(wyb[i][1], os.path.join(d, "kadry", os.path.basename(wyb[i][1])))
    return {"kadry_stanowiska": len(pl), "do_repo": min(6, len(wyb))}


def przerwa_tau(nf, t_ref, t_flag=None):
    """Przerwa źródła kończąca się zatrzaskiem τ* w t_ref: od ostatniej przyjętej poprawki (bez żadnej — od flagi ULG) do t_ref,
    powody odrzucenia kadrów."""
    ok = [r["sim"] for r in nf if (r.get("fx") or {}).get("ok") and r["sim"] <= t_ref and (t_flag is None or r["sim"] >= t_flag)]
    t0 = ok[-1] if ok else t_flag
    kad = [r for r in nf if (t0 is None or r["sim"] > t0) and r["sim"] <= t_ref]
    pow_ = {}
    for r in kad:
        k = (r.get("fx") or {}).get("powod") or "inne"
        pow_[k] = pow_.get(k, 0) + 1
    return {"poczatek": t0, "dlugosc_s": round(t_ref - t0, 3) if t0 is not None else None, "kadry": len(kad), "powody": pow_}


def sedzia(d, poz, kadry_dir=None):
    P = POZ[poz]
    a = A.analyze(d)
    s = SPR.sprawdz(d)
    import nad3_s2_spr as N2S                                       # READ-ONLY: b1_nieocenione
    b1n = N2S.b1_nieocenione(d)
    tr = os.path.join(d, "trace.jsonl")
    ev = A.jl(tr, "event")
    gt = sorted(A.jl(tr, "gt"), key=lambda r: r["sim"])
    armed = next((e for e in ev if e.get("ev") == "armed"), None)
    gx0, gy0 = armed["gt_home"] if armed else (0.0, 0.0)
    rama = sorted(A.jl(os.path.join(d, "rama.jsonl")), key=lambda r: r["tick"])
    tk = {r["tick"]: r for r in A.jl(tr, "tk")}
    nf = A.jl(os.path.join(d, "nadir_obs.jsonl"), "nf")
    gq_t = np.array([g["sim"] for g in gt])

    def pose(t):
        i = int(np.clip(np.searchsorted(gq_t, t), 1, len(gq_t) - 1))
        g = gt[i] if abs(gt[i]["sim"] - t) < abs(gt[i - 1]["sim"] - t) else gt[i - 1]
        return [g["x"], g["y"], g["z"]], [g["qw"], g["qx"], g["qy"], g["qz"]]
    meta = meta_spr(d, P)
    cut = next((e for e in ev if e.get("ev") == "denial"), None)
    ends = {e["episode_id"]: e for e in ev if e.get("ev") == "episode_end"}
    zp = {e["episode_id"]: e["sim"] for e in ev if e.get("ev") == "zejscie_planowe"}
    te = a.get("teach") or {}
    ww = te.get("warunki_waznosci") or {}
    out = {"pozycja": poz, **P, "boot": os.path.basename(d.rstrip("/")), "tempo": (a.get("tempo") or {}).get("dsim_dwall_settle"),
           "analizator_wazny": a.get("wazny"), "warunki_waznosci": ww, "sprawdzian": {"ok": s["ok"], "procent": s["procent"],
           "oslona_ticki": s["oslona"]["n"], "poprawki": s["poprawki"].get("n"), "georef": {k: s["georef"].get(k) for k in
           ("d_theta_deg", "d_t_m", "ok")}}, "meta": meta}
    t_entry = (ends.get(P["epizod"]) or {}).get("t_entry")
    if P["rodzaj"] == "ciecie":
        out["wejscie"] = cut is not None and t_entry is not None and cut.get("inj_t_rel", -1) >= t_entry
    else:
        out["wejscie"] = None
    nwaz = []
    if P["rodzaj"] == "ciecie" and not out["wejscie"]:
        nwaz.append("wejscie")
    if not s["ok"] or not meta["ok"]:
        nwaz.append("przyrzad")
    if not all(ww.values()) if ww else True:
        nwaz.append("swiat_kod")
    out["niewaznosc"] = nwaz
    out["wazny"] = not nwaz and bool(a.get("wazny"))
    out["b1_nieocenione"] = b1n
    out["b1_nieocenione_w_misji"] = sum(v["faza_misji"] for v in b1n["przyczyny"].values())
    out["epizody"] = []
    lit = True
    for o in a.get("epizody", []):
        ep = o["episode_id"]
        ms = [r for r in rama if r["ep"] == ep and r.get("phase") in MISJA and not r.get("desc") and r["sim"] < zp.get(ep, 1e18)]
        e = {"episode_id": ep, "scenario_id": o["scenario_id"], "ciecie": o["ciecie"],
             "B": {k: (o.get(k) or {}).get("ok") for k in ("B1", "B2", "B3", "B4", "B5") if k in o}, "B_szczegoly":
             {k: o.get(k) for k in ("B1", "B2", "B3", "B4", "B5") if k in o}, "D1": o.get("D1"), "max_e_do_U": o["B1"]["max_e_do_U"],
             "e_corr": o.get("e_corr"), "tau": o.get("tau"), "obserwable": o.get("nad3_obserwable"),
             "t_entry": (ends.get(ep) or {}).get("t_entry"), "okno_misji": [ms[0]["sim"], ms[-1]["sim"]] if ms else None}
        rg = [math.hypot(g["x"] - gx0, g["y"] - gy0) for g in gt if ms and ms[0]["sim"] <= g["sim"] <= ms[-1]["sim"]]
        e["r_max_gt_misja"] = round(max(rg), 3) if rg else None
        ekf_err = [math.hypot(r["p_ekf"][0] - r["gt"][1], r["p_ekf"][1] - r["gt"][0]) for r in ms if r.get("gt") and r.get("p_ekf")]
        e["max_blad_ekf_misja"] = round(max(ekf_err), 3) if ekf_err else None
        lit = lit and o.get("bezpieczenstwo_ok", False)
        if o["ciecie"]:
            ref = next((r for r in rama if r["ep"] == ep and r.get("ph") == "KONT_REFUSE" and r["sim"] < zp.get(ep, 1e18)), None)
            if ref is not None:
                g = min(gt, key=lambda x: abs(x["sim"] - ref["sim"]))
                przy = (tk.get(ref["tick"]) or {}).get("cause")
                e["odmowa_w_misji"] = {"tick": ref["tick"], "sim": ref["sim"], "od_ciecia_s": round(ref["sim"] - cut["t_inj_sim"], 2) if cut else None,
                                       "przyczyna": przy, "r_est": round(ref["nad2"]["r_est"], 3), "bariera_R_k": ref.get("R_k"),
                                       "r_gt": round(math.hypot(g["x"] - gx0, g["y"] - gy0), 3), "tau": (ref.get("nadir") or {}).get("tau")}
                if przy == "τ*":
                    t_fl = (te.get("os_czasu") or {}).get("flaga_ulg")
                    pz = przerwa_tau(nf, ref["sim"], t_fl)
                    lst = ((te.get("przerwy") or {}).get("lista_gt_115")) or []
                    if pz["poczatek"] is not None and t_fl is not None:
                        pz["pokrycie_max"] = next((x["pokrycie_max"] for x in lst if abs(x["od_flagi"] - (pz["poczatek"] - t_fl)) < 0.05), None)
                    e["odmowa_w_misji"]["przerwa_zrodla"] = pz
            else:
                e["odmowa_w_misji"] = None
            e["track"], e["pasmo"] = (o.get("D1") or {}).get("frac_track"), (o.get("D1") or {}).get("frac_pasmo")
        else:
            e["akwizycja"] = e["t_entry"] is not None
            e["B5_pusty"] = not e["akwizycja"]
        out["epizody"].append(e)
    out["litera_ok"] = bool(lit and a.get("bezpieczenstwo_ok") and out["b1_nieocenione_w_misji"] == 0)
    out["zrodlo"] = {k: te.get(k) for k in ("blad_poprawki", "blad_poprawki_polowy", "udzial_przyjetych_okna", "przerwy", "os_czasu",
                                            "opoznienie_pierwszej_poprawki_s", "skok_delta_pierwsza_m", "georef", "czas_ms", "n_drop",
                                            "n_img", "detekcje", "chwila_waznosci")}
    out["zrodlo"]["kurs_kf"] = kurs_kf(d, nf, pose)
    if P["rodzaj"] == "ciecie":
        ec = next((e for e in out["epizody"] if e["ciecie"]), None)
        out["D1_dostepne"] = bool(ec and (ec.get("D1") or {}).get("dostepne"))
        out["kadry"] = kadry(d, kadry_dir, pose)
    else:
        import teach_s2_cien as SC                                  # READ-ONLY: obserwacja cienia, kadry
        c = SC.ocen(d, kadry_dir or os.path.join(d, "brak_kadrow"))
        out["cien"] = {k: c.get(k) for k in ("t_cien", "koniec_misji", "kadry_okna", "przyjete_okna", "bramka_obrazu", "blad_poprawki_okna")}
    json.dump(out, open(os.path.join(d, "sedzia_s3.json"), "w"), ensure_ascii=False, indent=1, default=A._json_default)
    return out


def pary(wyniki):
    """wyniki: {pozycja: sedzia}. Sześć par (łata, komórka): b − a dla największego błędu poprawki, max e′/U′, r_max GT."""
    out = {}
    for lata in ("S", "M", "J"):
        for ep, kom in ((C05, "c05"), (C10, "c10")):
            w = {}
            for poz, P in POZ.items():
                if P["rodzaj"] == "ciecie" and P["lata"] == lata and P["epizod"] == ep and poz in wyniki:
                    e = next((x for x in wyniki[poz]["epizody"] if x["ciecie"]), None)
                    w[P["powt"]] = (wyniki[poz], e)
            if "a" in w and "b" in w and w["a"][1] and w["b"][1]:
                (sa, ea), (sb, eb) = w["a"], w["b"]
                ma, mb = (sa["zrodlo"].get("blad_poprawki") or {}).get("max"), (sb["zrodlo"].get("blad_poprawki") or {}).get("max")
                d_ = lambda x, y: round(y - x, 4) if (x is not None and y is not None) else None
                out[f"{lata}/{kom}"] = {"max_blad_a": ma, "max_blad_b": mb, "d_max_blad": d_(ma, mb),
                                        "eU_a": ea["max_e_do_U"], "eU_b": eb["max_e_do_U"], "d_eU": d_(ea["max_e_do_U"], eb["max_e_do_U"]),
                                        "r_max_a": ea["r_max_gt_misja"], "r_max_b": eb["r_max_gt_misja"],
                                        "d_r_max": d_(ea["r_max_gt_misja"], eb["r_max_gt_misja"])}
            else:
                out[f"{lata}/{kom}"] = None
    return out


if __name__ == "__main__":
    o = sedzia(sys.argv[1], int(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else None)
    print(json.dumps({k: o.get(k) for k in ("pozycja", "wazny", "niewaznosc", "litera_ok", "wejscie", "D1_dostepne")}, ensure_ascii=False))
