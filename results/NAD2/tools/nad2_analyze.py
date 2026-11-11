#!/usr/bin/env python3
"""results/NAD2/tools/nad2_analyze.py — analizator nogi NADIR-II (PROMPT_NAD2_S1 §1.5; PRE_NAD2 §5, ANEKS_NAD2-1 §2).

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
Raport płaski: e_corr i błąd poprawki per epizod (pola e_corr, a_poprawek). Wyjście: <boot>/wyniki_nad2.json (albo `out`).
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


def U_of(i, k, tr):
    return NS.u_nad2(i, k, tr) - NS.DELTA_D5


def analyze(d, out=None):
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
            zr = NS.r_nad2(i, j, tr, R_E) - n2["r_est"]
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
            ok_r = (tau is not None and tau >= NS.TAU_STAR_NAD2 - 2 * 0.05) or i is None or \
                   (j is not None and n2.get("r_est") is not None and n2["r_est"] > NS.r_nad2(i, j, tr, R_E))
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
                if ob.get("kosz") is not None and ob.get("tryb") in NS.TRYBY_NAD2:
                    a_ratio = max(a_ratio, a / (NS.ZAPAS_NAD2 * NS.F_NAD2[ob["tryb"]][ob["kosz"]]))
                if ob.get("para") and not ob["para"].get("odrzucona"):
                    dpsi.append(ob["para"]["dpsi_deg"])
        o["a_poprawek"] = ({"n": len(a_list), "p95": round(float(np.quantile(a_list, .95)), 4), "max": round(max(a_list), 4),
                            "max_do_1_5F": round(a_ratio, 4)} if a_list else None)
        o["bias_kursu_par"] = {"n": len(dpsi), "p50": round(float(np.median(dpsi)), 3)} if dpsi else None
        lit = [o["B1"]["ok"], o["B2"]["ok"], o["B3"]["ok"], o["B4"]["ok"]] + ([o["B5"]["ok"]] if "B5" in o else [])
        o["bezpieczenstwo_ok"] = all(lit)
        res["epizody"].append(o)
    try:
        res["tempo"] = json.load(open(os.path.join(d, "kont_tempo.json")))
    except (OSError, ValueError):
        res["tempo"] = None
    res["bezpieczenstwo_ok"] = all(o["bezpieczenstwo_ok"] for o in res["epizody"])
    res["wazny"] = True
    json.dump(res, open(out or os.path.join(d, "wyniki_nad2.json"), "w"), ensure_ascii=False, indent=1)
    return res


if __name__ == "__main__":
    for d in sys.argv[1:]:
        r = analyze(d)
        for o in r["epizody"]:
            print(r["boot"], o["scenario_id"], {k: o[k]["ok"] for k in ("B1", "B2", "B3", "B4", "B5") if k in o}, o.get("D1"),
                  "e_corr", o["e_corr"], "a", o["a_poprawek"])
