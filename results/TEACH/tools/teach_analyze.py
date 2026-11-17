#!/usr/bin/env python3
"""results/TEACH/tools/teach_analyze.py — analizator nogi TEACH (PROMPT_TEACH_S1 §1.4, PRE_TEACH §6) = KOPIA
results/NAD3/tools/nad3_analyze.py (nietknięty) ze zmianami oznaczonymi „TEACH:” wyłącznie:
  - tabela z meta lotu „teach”.„oslona” (punkt TEACH, sha sprawdzana r03/nadir_shield.nad3_tabela); `--tabela PLIK` tylko na sucho
    (lot bez producenta TEACH: ważność = fałsz z powodem);
  - B1–B5 jak NAD3 z e′ = |p_corr − GT(t próbki EKF)| (p_corr = p_EKF + Δ z datagramu producenta mapy) wobec U′ tabeli TEACH;
  - źródło (nadir_obs.jsonl, wiersze nf z polami fx / teach / gnss): błąd poprawki |p_fix − GT(t_fix)| per przyjęta poprawka
    (t_fix = czas klatki) p50 / p95 / max; przerwy między przyjętymi od flagi do końca misji (z [flaga, pierwsza] i [ostatnia,
    koniec misji]) z największym pokryciem prawdziwym kadrów przerwy przez klatki kluczowe (poza GT, teach_r34.pokrycie, pół-bok
    a kadru) — „w mapie” ≥ 0.50; opóźnienie pierwszej przyjętej poprawki po fladze (czas sim); skok |Δ| przy pierwszej poprawce;
    liczba klatek kluczowych i wiązań; czas producenta na klatkę (mapa / lokalizacja: cechy + dopasowanie) i czas zamknięcia;
  - warunki ważności lotu (PRE_TEACH §6): zero detekcji znaczników w kamerze w dół przez cały lot; żadna klatka kluczowa ani
    wiązanie po fladze (kadr włączony do mapy z czasem ≥ chwila flagi ULG, klatka kluczowa georeferencji po fladze); georeferencja
    rozwiązana dokładnie raz. Niespełnienie ⇒ lot nieważny (nie FAIL nogi).
ANEKS_TEACH-2 §3 (TEACH-2A): świadek tezy = zero detekcji ZGODNYCH Z MANIFESTEM — ID z manifestu znaczników v2 i punkt gruntu
środka detekcji (promień piksela uv przy pozie GT kadru, kamera w dół z przypiętego modelu — orto_r2.Kam, przecięty z płaszczyzną
z = z znacznika) nie dalej niż 1.0 m od pozycji tego ID; detekcje surowe jako obserwabla (liczba, ID, bok). Funkcja zgodnosc_detekcji
liczy też poza lotem TEACH (sprawdziany aneksu §4.3).
PROMPT_TEACH_S3 §1 (TEACH-3S): zapis wyniku odporny na typy numpy (lot bez żadnej przyjętej poprawki kończy się osądem); ważność
w nominale (bez cięcia) wobec chwili cienia z meta nadir_obs („teach”.„t_cien”); nowe pola źródła: największy błąd poprawki w pierwszej
i drugiej połowie okna misji [flaga, koniec misji], udział przyjętych w oknie [klatka zamknięcia, koniec misji], oś czasu (chwila flagi
z ULG, wejście osłony w utratę, klatka zamknięcia, ostatni kadr mapy — także wobec flagi).
Wyjście <boot>/wyniki_teach.json. Nagłówek oryginału:
results/NAD3/tools/nad3_analyze.py — analizator nogi NADIR-III (PROMPT_NAD3_S1 §1.3, PRE_NAD3 §6) = KOPIA
results/NAD2/tools/nad2_analyze.py (nietknięty) ze zmianami oznaczonymi „NAD3:” wyłącznie:
  - tabela punktu z meta lotu (trace meta „nad3”.„oslona”: ścieżka i sha256_tabeli; sha sprawdzana r03/nadir_shield.nad3_tabela);
    brak meta nad3 albo niezgodność ⇒ lot nieważny (powód w wyniku);
  - (B1) e′ = |p_corr zdegradowane − GT(t próbki EKF)| (p_corr ticku = p_EKF + Δ′ z datagramu po degradacji) wobec
    U′ = zapas·(F + E + G) przedziału użytego przez osłonę; (B4) reguła REFUSE z τ* tabeli (τ ≥ τ* − 2·dt) i R′ tabeli;
  - obserwable PRE §6 per epizod: τ zrealizowane w misji (p50/p95/max), skok Δ′ per zmiana stanu ramy (p50/p95/max),
    odrzucenia bramki predykcji tracku (percep_feed.jsonl.summary.json: n_pred_odrzut), r_max GT w misji po fladze,
    max e′/U′, REFUSE w misji z przyczyną; błąd poprawki a′ wobec 1.5·(F + E). Nagłówek oryginału:
results/NAD2/tools/nad2_analyze.py — analizator nogi NADIR-II (PROMPT_NAD2_S1 §1.5; PRE_NAD2 §5, ANEKS_NAD2-1 §2).

Litera bezpieczeństwa (każde naruszenie w dowolnym epizodzie = FAIL nogi):
  (B1) e_corr(tick) ≤ U(przedział UŻYTY PRZEZ OSŁONĘ, koszyk, tryb) w każdym ticku fazy utraty (KONT, KONT_REFUSE) z przedziałem;
       e_corr = |p_corr − GT(timestamp_sample próbki EKF ticku)| poziomo (kanon czasu ANEKS_NAD2-1 §2.1); próbka EKF ticku =
       vehicle_local_position z ULG dopasowana PO WARTOŚCI do p_ekf ticku (okno [sim − 0.4, sim + 0.1] s; recon R1);
  (B2) margines do R_E > 0 w każdej chwili (GT, od startu epizodu do końca/przyziemienia);
  (B3) r_est osłony (rama.jsonl: nad2.r_est) = |p_corr| (do 1e-3 m) w każdym ticku utraty;
  (B4) offboard do końca i zero natywnego failsafe od flagi utraty do przyziemienia (ULG vehicle_status: nav_state 14,
       failsafe 0); zero fałszywych REFUSE(POS) (REFUSE(POS) w epizodzie bez cięcia); każdy REFUSE(POS) zgodny z regułą
       (τ ≥ 0.95 s albo r_est > R z tabeli, przeliczone z ticku) i zakończony przyziemieniem GT;
  (B5) nominały: zero ticków fazy ≠ NOMINAL i zero REFUSE.
Litera dostępności: (D1) cięcie dostępne ⇔ kontynuacja od t_inj_sim ≥ 110 s ∧ track ≥ 0.85 ∧ pasmo 6–10 m ≥ 0.85 (jak (a) S4)
  ∧ zero REFUSE w fazach misji; próg nogi ≥ 10 z 12.
Obserwable bez progu: u′ wobec m per tick (r4_margin), błąd zakotwiczenia poprawek a wobec 1.5·F (poprawki z obs ramy:
  |p_fix − GT(t_a)|, t_a = timestamp_sample próbki EKF migawki), przyrost EKF w oknach między poprawkami wobec 1.5·G (ostatnie
  okno domykane KOŃCEM EPIZODU), rozkład τ i przedziałów, tryby, klatki bez poprawki, zapas bariery, bias kursu (δψ par), tempo,
  horyzont prawdziwy − (τ + 0.012 s).
Raport płaski: e_corr i błąd poprawki per epizod (pola e_corr, a_poprawek). Wyjście: <boot>/wyniki_nad3.json (NAD3; albo `out`).
Użycie: nad2_analyze.py <katalog_bootu> [...]
"""
import bisect
import json
import math
import os
import sys

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/KONT/tools")]
from r03 import nadir_shield as NS

MISJA = ("approach", "hold", "orbit")
UTRATA = ("KONT", "KONT_REFUSE")
T_CONT, FRAC_MIN, BAND, R_E = 110.0, 0.85, (6.0, 10.0), 32.0
MARG = json.load(open(os.path.join(ROOT, "results/KONT_RECON/r4_margin.json")))["tabela_scenariuszy"]
PRZYZ_TOL = 0.002


def jl(p, typ=None):
    out = []
    if not os.path.exists(p):
        return out
    for l in open(p):
        if typ is not None and f'"{typ}"' not in l:
            continue
        try:
            r = json.loads(l)
        except ValueError:
            continue
        if typ is None or r.get("t") == typ:
            out.append(r)
    return out


def ulg(d):
    from pyulog import ULog
    p = os.path.join(d, "boot.ulg")
    if not os.path.exists(p):
        return None
    u = ULog(p, ["vehicle_local_position", "estimator_status_flags", "vehicle_status"])
    return {x.name: x.data for x in u.data_list if x.multi_id == 0}


T3 = None                                                            # NAD3: tabela punktu lotu (nad3_tabela)
TABELA_SUCHO = None                                                  # TEACH: --tabela (tylko na sucho)


def U_of(i, k, tr):
    return NS.u_nad3(T3, i, k, tr) - NS.DELTA_D5                    # NAD3: U′ tabeli punktu


def tabela_lotu(d):
    """TEACH: tabela z meta trace „teach”.„oslona” (ścieżka + sha) sprawdzona przez osłonę, punkt TEACH; None ⇒ lot nieważny."""
    if TABELA_SUCHO is not None:
        return NS.nad3_tabela(TABELA_SUCHO, json.load(open(TABELA_SUCHO))["sha256_tabeli"])
    m = next((r for r in jl(os.path.join(d, "trace.jsonl"), "meta")), None)
    o = ((m or {}).get("teach") or {}).get("oslona") or {}
    if not o.get("tabela"):
        return None
    T = NS.nad3_tabela(o["tabela"], o.get("sha256_tabeli"))
    return T if T["punkt"] == "TEACH" else None


MANIFEST_V2 = os.path.join(ROOT, "results/NADIR/s1/n1/manifest_znaczniki_v2.json")
PROG_ZGODNOSCI_M = 1.0
_KAM = {}


def kamera_nadir():
    if "k" not in _KAM:
        sys.path[:0] = [os.path.join(ROOT, "results/ORTO_RECON/tools")]
        import orto_r2 as R2
        _KAM["k"] = (R2, R2.Kam(R2.kamera()))
    return _KAM["k"]


def punkt_gruntu(p_enu, q, uv, z):
    """TEACH-2A: punkt (E, N) przecięcia promienia piksela uv (indeksy pikseli jak uv detektora) z płaszczyzną z, poza GT (p ENU,
    q FLU→ENU); None, gdy promień nie trafia płaszczyzny."""
    R2, kam = kamera_nadir()
    C, Rk = kam.poza(np.asarray(p_enu, float), R2.rotm(q))
    dcz = np.array([1.0, -(uv[0] + 0.5 - kam.W / 2) / kam.F, -(uv[1] + 0.5 - kam.H / 2) / kam.F])
    r = Rk @ dcz
    if r[2] >= -1e-9:
        return None
    t = (z - C[2]) / r[2]
    return C[:2] + t * r[:2]


def zgodnosc_detekcji(wpisy, gt_pose):
    """TEACH-2A: wpisy = [(sim, [det {id, uv, bok}])]; zwraca obserwable surowe i zgodne z manifestem (ANEKS_TEACH-2 §3.1)."""
    man = {z["id"]: z for z in json.load(open(MANIFEST_V2))["znaczniki"]}
    sur, zg, odl = [], [], []
    for sim, det in wpisy:
        if not det:
            continue
        p, q = gt_pose(sim)
        for m in det:
            sur.append({"sim": sim, "id": m["id"], "bok": m.get("bok")})
            z = man.get(m["id"])
            if z is None:
                continue
            g = punkt_gruntu(p, q, m["uv"], z["z"])
            if g is None:
                continue
            dd = float(np.hypot(g[0] - z["E"], g[1] - z["N"]))
            odl.append(dd)
            if dd <= PROG_ZGODNOSCI_M:
                zg.append({"sim": sim, "id": m["id"], "bok": m.get("bok"), "odl_m": round(dd, 4)})
    boki = [x["bok"] for x in sur if x["bok"] is not None]
    return {"surowe": {"n": len(sur), "id": sorted({x["id"] for x in sur}), "bok_max": max(boki) if boki else None,
                       "n_kadrow": len({x["sim"] for x in sur})},
            "zgodne": {"n": len(zg), "id": sorted({x["id"] for x in zg}),
                       "odl_p95": round(float(np.quantile([x["odl_m"] for x in zg], .95)), 4) if zg else None,
                       "odl_max": round(max(x["odl_m"] for x in zg), 4) if zg else None, "lista": zg[:50]},
            "odl_wszystkich_z_manifestu": {"n": len(odl), "min": round(min(odl), 4) if odl else None}}


def _json_default(x):                                                # TEACH-3S: typy numpy w zapisie wyniku
    return x.item() if hasattr(x, "item") else str(x)


def zrodlo_teach(d, GTp, t_flag, t_konca, gt_pose):
    """TEACH: obserwable i ważność źródła z nadir_obs.jsonl; GTp(t) = GT NED, gt_pose(t) = (p ENU, q FLU→ENU)."""
    nf = jl(os.path.join(d, "nadir_obs.jsonl"), "nf")
    meta = next((r for r in jl(os.path.join(d, "nadir_obs.jsonl"), "meta")), {})
    t_cien = (meta.get("teach") or {}).get("t_cien")                 # TEACH-3S: nominał — ważność wobec chwili cienia
    t_waz = t_flag if t_flag is not None else (float(t_cien) if t_cien is not None else None)
    out = {"meta_litera": meta.get("litera"), "wariant_K": (meta.get("teach") or {}).get("wariant_K"),
           "n_klatek": len(nf), "n_det_znacznikow": int(sum(r.get("n", 0) for r in nf)),
           "n_klatek_z_detekcja": sum(1 for r in nf if r.get("n", 0))}
    out["detekcje"] = zgodnosc_detekcji([(r["sim"], r.get("det")) for r in nf], gt_pose)          # TEACH-2A
    tr = [r for r in nf if r.get("teach") is not None]
    if not tr:
        out.update(wazny=False, powod_niewazny="brak producenta TEACH w nadir_obs.jsonl")
        return out
    wl = [r["teach"]["wlaczony"] for r in tr if r["teach"].get("wlaczony")]
    geo = [r for r in tr if r["teach"].get("georef")]
    G = geo[0]["teach"]["georef"] if geo else None
    po_fladze_mapa = [w for w in wl if t_waz is not None and w["sim"] >= t_waz]                      # TEACH-3S: t_waz
    kf_po = [k for k in (G or {}).get("kf", []) if t_waz is not None and k["sim"] >= t_waz]
    wz_po = [w for w in (G or {}).get("wiazania", []) if t_waz is not None and w[0] >= t_waz]
    out["warunki_waznosci"] = {"zero_detekcji_zgodnych_z_manifestem": out["detekcje"]["zgodne"]["n"] == 0,   # TEACH-2A
                               "brak_mapy_po_fladze": not po_fladze_mapa and not kf_po and not wz_po, "georef_raz": len(geo) == 1}
    out["kadry_mapy_po_fladze"], out["kf_po_fladze"], out["wiazania_po_fladze"] = len(po_fladze_mapa), len(kf_po), len(wz_po)
    out["chwila_waznosci"] = {"t": t_waz, "zrodlo": "flaga ULG" if t_flag is not None else ("chwila cienia" if t_waz is not None else None)}
    t_zamk = geo[0]["sim"] if geo else None                           # TEACH-3S: oś czasu
    t_ost = max((w["sim"] for w in wl), default=None)
    out["os_czasu"] = {"flaga_ulg": t_flag, "klatka_zamkniecia": t_zamk, "ostatni_kadr_mapy": t_ost,
                       "zamkniecie_wobec_flagi_s": round(t_zamk - t_waz, 4) if (t_zamk is not None and t_waz is not None) else None,
                       "ostatni_kadr_wobec_flagi_s": round(t_ost - t_waz, 4) if (t_ost is not None and t_waz is not None) else None}
    out["wazny"] = all(out["warunki_waznosci"].values())
    if not out["wazny"]:
        out["powod_niewazny"] = [k for k, v in out["warunki_waznosci"].items() if not v]
    if G is not None:
        out["georef"] = {k: G[k] for k in ("t_flagi", "n_kadrow_mapy", "n_kf", "n_wiazan", "n_wiazan_przyjetych", "n_dop_pozno",
                                           "ms_zamkniecie", "ms_rozwiazanie", "wariant_K")}
        out["georef"]["ms_od_flagi_do_georef"] = geo[0]["teach"].get("ms_od_flagi_do_georef")
    # błąd poprawki i przerwy (od flagi do końca misji)
    ok = [r for r in nf if (r.get("fx") or {}).get("ok")]
    err = []
    for r in ok:
        g = GTp(r["fx"]["t_frame"])
        err.append(float(math.hypot(r["fx"]["p_fix_ne"][0] - g[0], r["fx"]["p_fix_ne"][1] - g[1])))
    out["blad_poprawki"] = ({"n": len(err), "p50": round(float(np.median(err)), 4), "p95": round(float(np.quantile(err, .95)), 4),
                             "max": round(max(err), 4)} if err else None)
    if t_waz is not None and t_konca is not None:                    # TEACH-3S: połowy okna misji i udział przyjętych
        srod = t_waz + (t_konca - t_waz) / 2
        e1 = [e for r, e in zip(ok, err) if t_waz <= r["fx"]["t_frame"] < srod]
        e2 = [e for r, e in zip(ok, err) if srod <= r["fx"]["t_frame"] <= t_konca]
        out["blad_poprawki_polowy"] = {"okno": [t_waz, t_konca], "srodek": round(srod, 3),
                                       "max_pierwsza": round(max(e1), 4) if e1 else None, "n_pierwsza": len(e1),
                                       "max_druga": round(max(e2), 4) if e2 else None, "n_druga": len(e2)}
        if t_zamk is not None:
            okn = [r for r in nf if t_zamk <= r["sim"] <= t_konca]
            npr = sum(1 for r in okn if (r.get("fx") or {}).get("ok"))
            out["udzial_przyjetych_okna"] = {"okno": [t_zamk, t_konca], "kadry": len(okn), "przyjete": npr,
                                             "udzial": round(npr / len(okn), 4) if okn else None}
    if t_flag is not None:
        t_ok = [r["fx"]["t_frame"] for r in ok if r["fx"]["t_frame"] >= t_flag and (t_konca is None or r["fx"]["t_frame"] <= t_konca)]
        out["opoznienie_pierwszej_poprawki_s"] = round(t_ok[0] - t_flag, 3) if t_ok else None
        first = next((r for r in ok if r["fx"]["t_frame"] >= t_flag), None)
        out["skok_delta_pierwsza_m"] = round(math.hypot(*first["fx"]["d_ne"]), 4) if first else None
        if t_konca is not None and G is not None:
            sys.path[:0] = [os.path.join(ROOT, "results/TEACH_RECON/tools"), os.path.join(ROOT, "results/ORTO_RECON/tools")]
            import orto_r2 as R2
            import teach_r34 as T34
            kam = R2.Kam(R2.kamera())

            def cam_gt(t):
                p, q = gt_pose(t)
                return kam.poza(np.array(p), R2.rotm(q))[0]
            kfc = [cam_gt(k["sim"])[:2] for k in G["kf"]]
            ts = [t_flag] + t_ok + [t_konca]
            lst = []
            for a, b in zip(ts[:-1], ts[1:]):
                if b - a > 1.15:
                    kad = [r for r in nf if a < r["sim"] < b and r.get("ekf_pos")]
                    pm = 0.0
                    for r in kad:
                        c = cam_gt(r["sim"])
                        ax = c[2] * (kam.H / 2) / kam.F
                        pm = max([pm] + [T34.pokrycie(c[:2], q, ax) for q in kfc])
                    lst.append({"od_flagi": round(a - t_flag, 2), "s": round(b - a, 3), "pokrycie_max": round(pm, 3), "w_mapie": pm >= 0.5})
            gaps = np.diff(ts)
            out["przerwy"] = {"max": round(float(gaps.max()), 3), "gt_115": int((gaps > 1.15).sum()), "gt_215": int((gaps > 2.15).sum()),
                              "lista_gt_115": lst}
    mp = [r["teach"]["wlaczony"] for r in tr if r["teach"].get("wlaczony")]
    lk = [r["teach"] for r in tr if r["teach"].get("faza") == "lok" and r["teach"].get("ms_cechy") is not None]
    q = lambda x: ({"p50": round(float(np.median(x)), 2), "p95": round(float(np.quantile(x, .95)), 2), "max": round(max(x), 2)} if x else None)
    out["czas_ms"] = {"mapa": q([w["ms_cechy"] + w["ms_dop"] for w in mp]), "lokalizacja": q([x["ms_cechy"] + x["ms_dop"] for x in lk]),
                      "detektor_znacznikow": q([r["ms"] for r in nf if r.get("ms") is not None])}
    try:
        sm = json.load(open(os.path.join(d, "nadir_obs.jsonl.summary.json")))
        out["n_drop"], out["n_img"] = sm.get("n_drop"), sm.get("n_img")
    except (OSError, ValueError):
        pass
    return out


def analyze(d, out=None):
    global T3
    try:
        T3 = tabela_lotu(d)                                          # NAD3
    except NS.NadirStartError as e:
        T3, _t3err = None, str(e)
    else:
        _t3err = "brak meta teach"
    ev = jl(os.path.join(d, "trace.jsonl"), "event")
    gt = sorted(jl(os.path.join(d, "trace.jsonl"), "gt"), key=lambda r: r["sim"])
    tk = jl(os.path.join(d, "trace.jsonl"), "tk")
    rama = sorted(jl(os.path.join(d, "rama.jsonl")), key=lambda r: r["tick"])
    res = {"boot": os.path.basename(d.rstrip("/")), "epizody": []}
    e1 = lambda n, ep=None: next((e for e in ev if e.get("ev") == n and (ep is None or e.get("episode_id") == ep)), None)
    armed = e1("armed")
    if armed is None or not rama:
        res.update(wazny=False, powod_niewazny="brak uzbrojenia albo pętli")
        return res
    if T3 is None:                                                   # NAD3: bez tabeli punktu nie ma litery
        res.update(wazny=False, powod_niewazny=f"tabela TEACH: {_t3err}")
        return res
    res["tabela_teach"] = {"punkt": T3["punkt"], "E": T3["E"], "sha256_tabeli": T3["sha"], "tau_star": T3["tau_star"]}   # TEACH
    gx0, gy0 = armed["gt_home"]
    gt_t = np.array([g["sim"] for g in gt])
    gt_ned = np.array([[g["y"], g["x"], -g["z"]] for g in gt])
    GT = lambda t: np.array([np.interp(t, gt_t, gt_ned[:, i]) for i in range(3)])
    u = ulg(d)
    vt = vts = vp = None
    if u is not None:
        v = u["vehicle_local_position"]
        vt, vts = v["timestamp"] / 1e6, v["timestamp_sample"] / 1e6
        vp = np.stack([v["x"], v["y"], v["z"]], 1)

    def t_probki(p, t_ref, okno=(-0.4, 0.1)):
        if vt is None:
            return None
        i0, i1 = bisect.bisect_left(vt, t_ref + okno[0]), bisect.bisect_right(vt, t_ref + okno[1])
        if i1 <= i0:
            return None
        dd = np.linalg.norm(vp[i0:i1] - np.asarray(p, float), axis=1)
        return float(vts[i0 + int(np.argmin(dd))])
    cut = e1("denial")
    t_inj = cut["t_inj_sim"] if cut else None
    t_flag = None
    if cut is not None and u is not None:
        fl = u["estimator_status_flags"]
        for t, val in zip(fl["timestamp"] / 1e6, fl["cs_gnss_pos"]):
            if val == 0 and t >= cut["sim"] - 0.5:
                t_flag = float(t); break
    land = e1("gt_przyziemienie")
    for st in [e for e in ev if e.get("ev") == "episode_start"]:
        ep, scen = st["episode_id"], st["scenario_id"]
        en, zp = e1("episode_end", ep), e1("zejscie_planowe", ep)
        c_ep = cut if (cut is not None and cut.get("episode_id") == ep) else None
        refs = [e for e in ev if e.get("ev") == "refuse" and e.get("episode_id") == ep]
        t_end = land["sim"] if (land and c_ep) else (en["sim"] if en else 1e18)
        rr = [r for r in rama if r["ep"] == ep]
        tks = [r for r in tk if r["ep"] == ep]
        m = MARG.get(scen, {}).get("m")
        o = {"episode_id": ep, "scenario_id": scen, "m": m, "ciecie": c_ep is not None}
        # (B1) (B3) obserwable per tick utraty
        b1, b3, n_ut, eU, e_list, hor, przedz, tryby, zap, u_gt_m, taus = 0, 0, 0, 0.0, [], None, {}, {}, None, 0, []
        for r in rr:
            n2, ph = r.get("nad2"), r.get("ph")
            if ph not in UTRATA or n2 is None:
                continue
            n_ut += 1
            pc = r["p_corr"]
            b3 += int(abs(n2["r_est"] - math.hypot(pc[0], pc[1])) > 1e-3)
            i, tr, j = n2.get("przedzial"), n2.get("tryb"), (r.get("nadir") or {}).get("j")
            przedz[str(i)] = przedz.get(str(i), 0) + 1
            tryby[str(tr)] = tryby.get(str(tr), 0) + 1
            tau = (r.get("nadir") or {}).get("tau")
            if tau is not None:
                taus.append(tau)
            if i is None or j is None:
                continue
            Uv = U_of(i, j, tr)
            if m is not None and Uv + NS.DELTA_D5 > m:
                u_gt_m += 1
            zr = NS.r_nad3(T3, i, j, tr, R_E) - n2["r_est"]               # NAD3
            zap = zr if zap is None else min(zap, zr)
            ts = t_probki(r["p_ekf"], r["sim"])
            if ts is None:
                continue
            g = GT(ts)
            e = float(math.hypot(pc[0] - g[0], pc[1] - g[1]))
            e_list.append(e)
            eU = max(eU, e / Uv)
            b1 += int(e > Uv)
        o["B1"] = {"ok": b1 == 0 and n_ut > 0 if c_ep else b1 == 0, "przekroczenia": b1, "ticki_utraty": n_ut, "max_e_do_U": round(eU, 4),
                   "ticki_ocenione": len(e_list)}
        o["B3"] = {"ok": b3 == 0 and (n_ut > 0 if c_ep else True), "zle": b3, "ticki_utraty": n_ut}   # cięcie bez ticków utraty z polami NAD2 ⇒ FAIL
        o["e_corr"] = ({"p50": round(float(np.median(e_list)), 4), "p95": round(float(np.quantile(e_list, .95)), 4),
                        "max": round(max(e_list), 4), "n": len(e_list)} if e_list else None)
        o["przedzialy"], o["tryby_ticki"], o["zapas_bariery_min"] = przedz, tryby, (round(zap, 4) if zap is not None else None)
        o["u_prim_gt_m_ticki"] = u_gt_m
        o["tau"] = ({"p50": round(float(np.median(taus)), 4), "p95": round(float(np.quantile(taus, .95)), 4), "max": round(max(taus), 4)}
                    if taus else None)
        # (B2) margines GT
        t0 = st["sim"]
        sel = (gt_t >= t0) & (gt_t <= (t_end if t_end < 1e17 else gt_t[-1]))
        rg = np.hypot(np.array([g["x"] for g in gt])[sel] - gx0, np.array([g["y"] for g in gt])[sel] - gy0)
        o["B2"] = {"ok": bool(rg.size) and float(R_E - rg.max()) > 0, "margines_min": round(float(R_E - rg.max()), 3) if rg.size else None}
        # (B4)
        nav = None
        if c_ep is not None and u is not None and t_flag is not None:
            vs = u["vehicle_status"]
            vtt = vs["timestamp"] / 1e6
            sel = (vtt >= t_flag) & (vtt <= (land["sim"] if land else t_end))
            poza = sorted(set(int(x) for x in vs["nav_state"][sel] if x != 14))
            fsm = int(vs["failsafe"][sel].max()) if sel.any() else None
            nav = {"nav_poza_14": poza, "failsafe_max": fsm, "ok": bool(sel.any()) and not poza and fsm == 0}
        pos_refs = [e for e in refs if e.get("reason") == "POS_DEGRADED"]
        falszywe = len(pos_refs) if c_ep is None else 0
        zgodne = 0
        for e in pos_refs:
            r = min(rr, key=lambda x: abs(x["sim"] - e["sim"])) if rr else None
            n2 = (r or {}).get("nad2") or {}
            tau = ((r or {}).get("nadir") or {}).get("tau")
            i, tr, j = n2.get("przedzial"), n2.get("tryb"), ((r or {}).get("nadir") or {}).get("j")
            ok_r = (tau is not None and tau >= T3["tau_star"] - 2 * 0.05) or i is None or \
                   (j is not None and n2.get("r_est") is not None and n2["r_est"] > NS.r_nad3(T3, i, j, tr, R_E))   # NAD3
            zgodne += int(bool(ok_r) and land is not None)
        o["B4"] = {"ok": (nav is None or nav["ok"]) and falszywe == 0 and zgodne == len(pos_refs) and (c_ep is None or nav is not None),
                   "nav": nav, "refuse_pos": len(pos_refs), "refuse_pos_falszywe": falszywe, "refuse_pos_zgodne_z_regula": zgodne}
        # (B5)
        if c_ep is None:
            nn = sum(1 for r in tks if r.get("phase") in MISJA and r.get("ph") not in (None, "NOMINAL"))
            nref = sum(1 for r in tks if r.get("dec") == "REFUSE")
            o["B5"] = {"ok": nn == 0 and nref == 0, "ticki_nie_nominal": nn, "refuse": nref}
        # (D1)
        if c_ep is not None:
            kont = round(zp["sim"] - t_inj, 3) if (zp and t_inj is not None) else None
            win = [r for r in tks if t_flag is not None and zp is not None and t_flag <= r["sim"] <= zp["sim"] and not r.get("desc")]
            ft = float(np.mean([r["trk_valid"] for r in win])) if win else 0.0
            dg = []
            for r in win:
                if r.get("intr") is None:
                    continue
                g = GT(r["sim"])
                dg.append(math.hypot(g[0] - r["intr"][0], g[1] - r["intr"][1]))
            fp = float(np.mean([BAND[0] <= x <= BAND[1] for x in dg])) if dg else 0.0
            nref_m = sum(1 for r in tks if r.get("phase") in MISJA and r.get("dec") == "REFUSE" and (zp is None or r["sim"] < zp["sim"]))
            o["D1"] = {"dostepne": kont is not None and kont >= T_CONT and ft >= FRAC_MIN and fp >= FRAC_MIN and nref_m == 0,
                       "kontynuacja_od_t_inj_s": kont, "frac_track": round(ft, 3), "frac_pasmo": round(fp, 3), "refuse_misja": nref_m}
        # obserwabla: błąd zakotwiczenia poprawek (obs ramy) wobec 1.5·F; bias kursu z par
        a_list, a_ratio, dpsi = [], 0.0, []
        for r in rr:
            for ob in r.get("obs") or []:
                if not ob.get("ok") or ob.get("p_ekf_fix") is None:
                    continue
                ta = t_probki(ob["p_ekf_fix"], ob["t_frame"], okno=(-0.3, 0.3))
                if ta is None:
                    continue
                g = GT(ta)
                a = float(math.hypot(ob["p_fix_ne"][0] - g[0], ob["p_fix_ne"][1] - g[1]))
                a_list.append(a)
                if ob.get("kosz") is not None and ob.get("tryb") in NS.TRYBY_NAD2:                 # NAD3: a′ wobec 1.5·(F + E)
                    a_ratio = max(a_ratio, a / (T3["zapas"] * (T3["F"][ob["tryb"]][ob["kosz"]] + T3["E"])))
                if ob.get("para") and not ob["para"].get("odrzucona"):
                    dpsi.append(ob["para"]["dpsi_deg"])
        o["a_poprawek"] = ({"n": len(a_list), "p95": round(float(np.quantile(a_list, .95)), 4), "max": round(max(a_list), 4),
                            "max_do_1_5F": round(a_ratio, 4)} if a_list else None)
        o["bias_kursu_par"] = {"n": len(dpsi), "p50": round(float(np.median(dpsi)), 3)} if dpsi else None
        # NAD3: obserwable PRE §6 (bez progu)
        mis = [r for r in rr if r.get("phase") in MISJA and not r.get("desc") and (zp is None or r["sim"] < zp["sim"])]
        mis_ut = [r for r in mis if r.get("ph") in UTRATA]
        tm = [((r.get("nadir") or {}).get("tau")) for r in mis_ut]
        tm = [x for x in tm if x is not None]
        dd, prev = [], None
        for r in rr:
            if r.get("ph") in UTRATA and prev is not None and r["d_ne"] != prev:
                dd.append(math.hypot(r["d_ne"][0] - prev[0], r["d_ne"][1] - prev[1]))
            prev = r["d_ne"]
        t_fl = t_flag if t_flag is not None else -1e18
        rgt = [math.hypot(g["x"] - gx0, g["y"] - gy0) for g in gt if mis and t_fl <= g["sim"] <= mis[-1]["sim"]
               and g["sim"] >= mis[0]["sim"]]
        try:
            npo = json.load(open(os.path.join(d, "percep_feed.jsonl.summary.json"))).get("n_pred_odrzut")
        except (OSError, ValueError):
            npo = None
        ref_m = [e for e in refs if e.get("reason") == "POS_DEGRADED" and (zp is None or e["sim"] < zp["sim"])]
        o["nad3_obserwable"] = {"tau_misja": ({"p50": round(float(np.median(tm)), 4), "p95": round(float(np.quantile(tm, .95)), 4),
                                               "max": round(max(tm), 4)} if tm else None),
                                "skok_delta": ({"n": len(dd), "p50": round(float(np.median(dd)), 4), "p95": round(float(np.quantile(dd, .95)), 4),
                                                "max": round(max(dd), 4)} if dd else None),
                                "n_pred_odrzut": npo, "r_max_gt_misja_po_fladze": round(max(rgt), 3) if rgt else None,
                                "max_e_do_U": o["B1"]["max_e_do_U"],
                                "refuse_misja": [{"sim": e["sim"], "detail": e.get("detail"), "rule": e.get("rule")} for e in ref_m]}
        lit = [o["B1"]["ok"], o["B2"]["ok"], o["B3"]["ok"], o["B4"]["ok"]] + ([o["B5"]["ok"]] if "B5" in o else [])
        o["bezpieczenstwo_ok"] = all(lit)
        res["epizody"].append(o)
    try:
        res["tempo"] = json.load(open(os.path.join(d, "kont_tempo.json")))
    except (OSError, ValueError):
        res["tempo"] = None
    res["bezpieczenstwo_ok"] = all(o["bezpieczenstwo_ok"] for o in res["epizody"])
    gq = sorted(jl(os.path.join(d, "trace.jsonl"), "gt"), key=lambda r: r["sim"])                     # TEACH: źródło i ważność
    gq_t = np.array([g["sim"] for g in gq])

    def gt_pose(t):
        i = int(np.clip(np.searchsorted(gq_t, t), 1, len(gq_t) - 1))
        a = float(np.clip((t - gq_t[i - 1]) / max(gq_t[i] - gq_t[i - 1], 1e-9), 0, 1))
        A, B = gq[i - 1], gq[i]
        p = [(1 - a) * A[k] + a * B[k] for k in ("x", "y", "z")]
        qa = np.array([A["qw"], A["qx"], A["qy"], A["qz"]]); qb = np.array([B["qw"], B["qx"], B["qy"], B["qz"]])
        if qa @ qb < 0:
            qb = -qb
        qq = (1 - a) * qa + a * qb
        return p, (qq / np.linalg.norm(qq)).tolist()
    c_eps = [o for o in res["epizody"] if o["ciecie"]]
    zp_c = e1("zejscie_planowe", cut["episode_id"]) if cut else None
    t_kon = zp_c["sim"] if zp_c else None
    if cut is None:                                                  # TEACH-3S: nominał — koniec misji epizodu (bez zejścia)
        mis_all = [r["sim"] for r in rama if r.get("phase") in MISJA and not r.get("desc")]
        t_kon = max(mis_all) if mis_all else None
    res["teach"] = zrodlo_teach(d, GT, t_flag, t_kon, gt_pose)
    ut0 = next((r["sim"] for r in rama if r.get("ph") not in (None, "NOMINAL")), None)          # TEACH-3S: wejście osłony w utratę
    res["teach"].setdefault("os_czasu", {})["wejscie_oslony_w_utrate"] = ut0
    if ut0 is not None and t_flag is not None:
        res["teach"]["os_czasu"]["wejscie_oslony_wobec_flagi_s"] = round(ut0 - t_flag, 4)
    res["wazny"] = bool(res["teach"].get("wazny"))
    if not res["wazny"]:
        res["powod_niewazny"] = res["teach"].get("powod_niewazny")
    json.dump(res, open(out or os.path.join(d, "wyniki_teach.json"), "w"), ensure_ascii=False, indent=1,
              default=_json_default)                                 # TEACH; TEACH-3S: typy numpy
    return res


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--tabela" in args:                                           # TEACH: na sucho
        i = args.index("--tabela"); TABELA_SUCHO = args[i + 1]; del args[i:i + 2]
    wyj = None
    if "--out" in args:
        i = args.index("--out"); wyj = args[i + 1]; del args[i:i + 2]
    for d in args:
        r = analyze(d, wyj)
        print(r["boot"], "ważny", r.get("wazny"), r.get("powod_niewazny"), "teach", {k: (r.get("teach") or {}).get(k) for k in
              ("n_det_znacznikow", "blad_poprawki", "opoznienie_pierwszej_poprawki_s", "przerwy")})
        for o in r["epizody"]:
            print(r["boot"], o["scenario_id"], {k: o[k]["ok"] for k in ("B1", "B2", "B3", "B4", "B5") if k in o}, o.get("D1"),
                  "e_corr", o["e_corr"], "a", o["a_poprawek"])
