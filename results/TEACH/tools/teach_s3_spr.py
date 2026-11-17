#!/usr/bin/env python3
"""results/TEACH/tools/teach_s3_spr.py — sprawdzian lotu bramki S3 TEACH (PROMPT_TEACH_S3 §1, ANEKS_TEACH-4 §2: replay = czwarty
warunek ważności PRE §6); wzór results/NAD3/tools/nad3_s2_spr.py (nietknięty, część osłony). Trzy części, każda 100% albo lista różnic:

(o) osłona: r03/nadir_shield.NadirShield(nad3, tabela i suma z meta lotu „teach”.„oslona”) wołana przez results/NAD3/tools/nad3_krok.krok
    (ścieżka drivera teach_flight) na wejściach ticku z zapisu (rama.jsonl: p_EKF, sp_EKF, sp_net; trace tk: pf, cs, dr; demo: prędkość);
    stan ramy = klient: datagramy dostarczone w ticku (rama „obs”, numery seq) wzięte w pełnej postaci z wierszy nf producenta (fx) —
    w trybie cienia nic nie jest dostarczane. Per tick: przedział, τ (1e-4), R_k, faza, decyzja, reguła, d_ne klienta (5e-7), tick
    zatrzasku.
(p) poprawki: każda przyjęta poprawka (fx.ok) policzona od nowa z wiersza: klatka kluczowa k i wektor r (rejestr „teach”), zapisana
    georeferencja (θ_k, t_k), migawka EKF wiersza (off = (R_EKF·t_link)_EN, orto_r3.Prost) ⇒ fix_EN = Rz(θ_k)·r + t_k − off;
    |p_fix_ne − datagram| ≤ 0.0002 m, |d_ne − (p_fix_ne − p_EKF)| ≤ 0.0002 m.
(g) georeferencja: wiązania z rejestru zamknięcia (czas kadru, k, r_E, r_N, zgodne, przyjęte) + cam_EKF kadrów i klatek kluczowych
    z migawek EKF ich wierszy nf ⇒ teach2.rozwiaz (tor odniesienia, READ-ONLY, wariant M4) ⇒ θ_k ≤ 0.0001°, t_k ≤ 0.0001 m wobec
    zapisanej; cam_EKF klatek kluczowych wobec zapisanych (zaokrąglenie 4 cyfry) ≤ 0.0001 m.
Wyjście: <boot>/sprawdzian_s3.json („ok”, „procent”, listy różnic). Użycie: teach_s3_spr.py <katalog_bootu>
"""
import json
import math
import os
import sys

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/NAD3/tools")]
import nad3_krok                                                   # noqa: E402  READ-ONLY (ścieżka drivera)
from harness import teach_map as TM                                # noqa: E402
from r03 import config as C                                        # noqa: E402
from r03 import nadir_shield as NS                                 # noqa: E402

TOL_FIX, TOL_TH, TOL_T, TOL_TAU, TOL_DNE = 2e-4, 1e-4, 1e-4, 1e-4, 5e-7
_KAM = {}


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


def off_en(q):
    if "k" not in _KAM:
        _KAM["k"] = TM.R2.Kam(TM.R2.kamera())
    return (TM.NF.ekf_R(q) @ _KAM["k"].t_link)[:2]


def cam_ekf(row):
    p = row["ekf_pos"]
    return np.array([p[1], p[0]]) + off_en(row["ekf_q"])


def _maxd(a, b):
    if a is None or b is None:
        return 0.0 if a == b else float("inf")
    return max(abs(x - y) for x, y in zip(a, b))


def oslona(d, nf):
    m = next((r for r in jl(os.path.join(d, "trace.jsonl"), "meta")), {})
    ml = (m.get("teach") or {}).get("oslona") or {}
    fx = {r["fx"]["seq"]: r["fx"] for r in nf if r.get("fx")}
    rama = sorted(jl(os.path.join(d, "rama.jsonl")), key=lambda r: r["tick"])
    tk = {r["tick"]: r for r in jl(os.path.join(d, "trace.jsonl"), "tk")}
    demo = {r["tick"]: r for r in jl(os.path.join(d, "demo.jsonl"))}
    sh = NS.NadirShield(nadir_mode=True, kont_mode=True, nad3=True, tabela=ml.get("tabela"), tabela_sha=ml.get("sha256_tabeli"))
    sh.reset()
    sh.pos_debounce_ticks = C.DEBOUNCE_TICKS
    sh.pos_hyst_ticks = int(round(C.HYST_M_S / C.DT))

    class Kl:
        d_ne, t_fix, kosz, tryb = [0.0, 0.0], None, None, None
    kl = Kl()
    w = {"n": 0, "przedzial": 0, "tau": 0, "R_k": 0, "faza": 0, "dec": 0, "rule": 0, "d_ne": 0, "brak_tk": 0, "brak_datagramu": 0}
    lat_z = lat_r = None
    lista = []
    for r in rama:
        for ob in r.get("obs") or []:
            mm = fx.get(ob["seq"])
            if mm is None:
                w["brak_datagramu"] += 1
                continue
            kl.d_ne, kl.t_fix = list(mm["d_ne"]), mm["t_fix"]
            if mm.get("ok"):
                kl.kosz, kl.tryb = mm.get("kosz"), mm.get("tryb")
        t, dm = tk.get(r["tick"]), demo.get(r["tick"])
        if t is None or dm is None:
            w["brak_tk"] += 1
            continue
        pe = r["p_ekf"]
        own = [pe[0] + kl.d_ne[0], pe[1] + kl.d_ne[1], pe[2]]
        dd, _ = nad3_krok.krok(sh, r["tick"], pe, own, dm["own_vel_ned"], r["sp_ekf"], r["sp_net"], "PATROL", t["pf"], t["cs"], r["sim"],
                               t.get("dr"), kl)
        w["n"] += 1
        n2, nd = dd.get("nad2") or {}, dd.get("nadir") or {}
        lt = (r.get("nadir") or {}).get("tau")
        pom = {"przedzial": n2.get("przedzial") != (r.get("nad2") or {}).get("przedzial"),
               "tau": (lt is None) != (nd.get("tau") is None) or (lt is not None and abs(nd["tau"] - lt) > TOL_TAU),
               "R_k": dd["kont"].get("R_k") != r.get("R_k"), "faza": sh.kont_phase() != r.get("ph"),
               "dec": dd.get("decision") != r.get("dec"), "rule": dd.get("rule") != r.get("rule"),
               "d_ne": _maxd(kl.d_ne, r["d_ne"]) > TOL_DNE}
        for k, v in pom.items():
            w[k] += int(v)
        if any(pom.values()) and len(lista) < 50:
            lista.append({"tick": r["tick"], "sim": r["sim"], "pola": [k for k, v in pom.items() if v],
                          "zapis": {"dec": r.get("dec"), "rule": r.get("rule"), "ph": r.get("ph"), "R_k": r.get("R_k"), "tau": lt},
                          "replay": {"dec": dd.get("decision"), "rule": dd.get("rule"), "ph": sh.kont_phase(), "R_k": dd["kont"].get("R_k"),
                                     "tau": nd.get("tau")}})
        if lat_z is None and r.get("ph") == "KONT_REFUSE":
            lat_z = r["tick"]
        if lat_r is None and sh.kont_phase() == "KONT_REFUSE":
            lat_r = r["tick"]
    zle = sum(w[k] for k in ("przedzial", "tau", "R_k", "faza", "dec", "rule", "d_ne"))
    w.update(zatrzask_zapis=lat_z, zatrzask_replay=lat_r, roznice=lista,
             ticki_zgodne=w["n"] - len({x["tick"] for x in lista}) if zle <= 50 else None)
    w["ok"] = (w["n"] > 0 and w["brak_tk"] == 0 and w["brak_datagramu"] == 0 and lat_z == lat_r and zle == 0)
    return w


def georef_i_poprawki(nf):
    po_sim = {round(r["sim"], 3): r for r in nf}
    geo_r = [r for r in nf if (r.get("teach") or {}).get("georef")]
    out = {"n_zamkniec": len(geo_r)}
    if len(geo_r) != 1:
        out["poprawki"] = {"ok": False, "powod": f"zamknięć {len(geo_r)}"}
        out["georef"] = {"ok": False, "powod": f"zamknięć {len(geo_r)}"}
        return out
    G = geo_r[0]["teach"]["georef"]
    th = {k["k"]: math.radians(k["theta_deg"]) for k in G["kf"]}
    tt = {k["k"]: np.array(k["t"]) for k in G["kf"]}
    # (p) poprawki
    zle, n, dmax, lista = 0, 0, 0.0, []
    for r in nf:
        f = r.get("fx") or {}
        if not f.get("ok"):
            continue
        n += 1
        t = r["teach"]
        k, rv = t["k"], np.array(t["r"])
        fix = TM.T.rz(th[k]) @ rv + tt[k] - off_en(r["ekf_q"])
        p = [float(fix[1]), float(fix[0])]
        e1 = _maxd(p, f["p_fix_ne"])
        e2 = _maxd([f["p_fix_ne"][0] - r["ekf_pos"][0], f["p_fix_ne"][1] - r["ekf_pos"][1]], f["d_ne"])
        e = max(e1, e2)
        dmax = max(dmax, e)
        if e > TOL_FIX:
            zle += 1
            if len(lista) < 50:
                lista.append({"sim": r["sim"], "seq": f["seq"], "k": k, "d_p_fix": round(e1, 7), "d_d_ne": round(e2, 7)})
    out["poprawki"] = {"n": n, "niezgodne": zle, "max_abs_m": round(dmax, 7), "roznice": lista, "ok": zle == 0}
    # (g) georeferencja
    wz, brak = [], []
    for w in G["wiazania"]:
        row = po_sim.get(round(w[0], 3))
        if row is None or not row.get("ekf_q"):
            brak.append(w[0]); continue
        wz.append(list(w) + [cam_ekf(row).tolist()])
    kfs, d_cam = [], 0.0
    for k in G["kf"]:
        row = po_sim.get(round(k["sim"], 3))
        if row is None or not row.get("ekf_q"):
            brak.append(k["sim"]); continue
        c = cam_ekf(row)
        d_cam = max(d_cam, _maxd(c.tolist(), k["cam_ekf"]))
        kfs.append({"cam_ekf": c})
    if brak:
        out["georef"] = {"ok": False, "powod": "brak wiersza nf kadru", "brak": brak[:20]}
        return out
    Gr = TM.T2.rozwiaz(kfs, wz, TM.WARIANT_MAPY)
    d_th = max((abs(math.degrees(Gr[k["k"], 0]) - k["theta_deg"]) for k in G["kf"]), default=0.0)
    d_t = max((_maxd(Gr[k["k"], 1:].tolist(), k["t"]) for k in G["kf"]), default=0.0)
    out["georef"] = {"n_kf": len(G["kf"]), "n_wiazan": len(wz), "n_przyjetych": sum(w[5] for w in wz), "d_theta_deg": round(d_th, 8),
                     "d_t_m": round(d_t, 8), "d_cam_ekf_kf_m": round(d_cam, 8),
                     "ok": d_th <= TOL_TH and d_t <= TOL_T and d_cam <= 1e-4}
    return out


def sprawdz(d, zapis=True):
    nf = jl(os.path.join(d, "nadir_obs.jsonl"), "nf")
    o = {"oslona": oslona(d, nf), **georef_i_poprawki(nf)}
    czesci = [o["oslona"]["ok"], o["poprawki"]["ok"], o["georef"]["ok"]]
    o["ok"] = all(czesci)
    o["procent"] = 100.0 if o["ok"] else round(100.0 * sum(czesci) / 3, 1)
    if zapis:
        json.dump(o, open(os.path.join(d, "sprawdzian_s3.json"), "w"), ensure_ascii=False, indent=1, default=str)
    return o


if __name__ == "__main__":
    o = sprawdz(sys.argv[1])
    print(json.dumps({"ok": o["ok"], "oslona": {k: o["oslona"][k] for k in ("n", "ok", "zatrzask_zapis", "zatrzask_replay")},
                      "poprawki": {k: o["poprawki"].get(k) for k in ("n", "niezgodne", "max_abs_m", "ok")},
                      "georef": {k: v for k, v in o["georef"].items() if k != "brak"}}, ensure_ascii=False))
