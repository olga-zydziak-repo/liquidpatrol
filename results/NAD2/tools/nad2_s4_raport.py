#!/usr/bin/env python3
"""results/NAD2/tools/nad2_s4_raport.py — PROMPT_NAD2_S4 §2: lot długi — B1–B4 (z analizatora nad2_analyze, wyniki_nad2.json, bez
przeliczania) i obserwable w przedziałach po 100 s od cięcia (t_inj_sim), faza misji (przed zejscie_planowe) + zejście osobno.

Definicje jak w analizatorze i nad2_s3_raport (te same wzory, okna dopasowania próbki EKF po wartości):
  e_corr = |p_corr − GT(ts)| poziomo, ts = timestamp_sample próbki EKF ticku; e/U z U_of(przedział, koszyk, tryb);
  błąd własny EKF = |p_EKF − GT(ts)| poziomo; błąd zakotwiczenia a = |p_fix − GT(t_a)| wobec 1.5·F (przedział wg t_frame);
  przyrost EKF = |(p_EKF − GT)(ts) − (p_EKF − GT)(t_a migawki)| wobec 1.5·G(przedział ticku); bias kursu = mediana δψ par
  (obs ramy, para nieodrzucona); zapas bariery = r_nad2 − r_est; klatki bez poprawki = nf producenta z fx.ok = False;
  track = trk_valid ticków tk (bez desc), pasmo = |intr − GT| ∈ [6, 10] m; fuzja przepływu = estimator_status_flags.cs_opt_flow
  (udział 1), cs_gnss_pos (udział 1); nav_state (zbiór); tempo = Δsim/Δwall z rtf_stream.jsonl.
Wyjście: <boot>/obserwable_s4.json (--okna: obserwable_s4_okna.json — okna predykcji L3/L4), tabela markdown na stdout.
Użycie: nad2_s4_raport.py <katalog_bootu> [--okna]
"""
import bisect
import json
import math
import os
import sys

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/NAD2/tools")]
from r03 import nadir_shield as NS
import nad2_analyze as A

UTRATA = ("KONT", "KONT_REFUSE")
MISJA = ("approach", "hold", "orbit")
KROK = 100.0
OKNA = "--okna" in sys.argv[2:]   # predykcje L3/L4: pierwsze 100 s od cięcia i ostatnie 100 s przed zejscie_planowe


def main(d):
    jl = A.jl
    an = json.load(open(os.path.join(d, "wyniki_nad2.json")))
    ev = jl(os.path.join(d, "trace.jsonl"), "event")
    e1 = lambda n: next((e for e in ev if e.get("ev") == n), None)
    cut, zp, land = e1("denial"), e1("zejscie_planowe"), e1("gt_przyziemienie")
    ep = cut["episode_id"]
    t_inj = cut["t_inj_sim"]
    t_zp = zp["sim"] if zp else 1e18
    gt = sorted(jl(os.path.join(d, "trace.jsonl"), "gt"), key=lambda r: r["sim"])
    gt_t = np.array([g["sim"] for g in gt])
    gt_ned = np.array([[g["y"], g["x"], -g["z"]] for g in gt])
    GT = lambda t: np.array([np.interp(t, gt_t, gt_ned[:, i]) for i in range(2)])
    from pyulog import ULog
    u = {x.name: x.data for x in ULog(os.path.join(d, "boot.ulg"), ["vehicle_local_position", "estimator_status_flags",
                                                                       "vehicle_status"]).data_list if x.multi_id == 0}
    v = u["vehicle_local_position"]
    vt, vts = v["timestamp"] / 1e6, v["timestamp_sample"] / 1e6
    vp = np.stack([v["x"], v["y"]], 1)

    def probka(p, t_ref, okno):
        i0, i1 = bisect.bisect_left(vt, t_ref + okno[0]), bisect.bisect_right(vt, t_ref + okno[1])
        if i1 <= i0:
            return None
        k = i0 + int(np.argmin(np.linalg.norm(vp[i0:i1] - np.asarray(p[:2], float), axis=1)))
        return float(vts[k]), vp[k]

    kosz = lambda t: "zejscie" if t >= t_zp else f"{int((t - t_inj) // KROK) * 100:03d}"
    if OKNA:
        kosz = lambda t: "pierwsze_100" if t_inj <= t < t_inj + KROK else ("ostatnie_100" if t_zp - KROK <= t < t_zp else "_")
    B = {}
    nb = lambda k: B.setdefault(k, {"e": [], "eU": 0.0, "ekf": [], "a_do_F": 0.0, "przyrost_do_G": 0.0, "dpsi": [], "zapas_min": None,
                                     "r_est_max": None, "tau_max": None, "przedzialy": {}, "tryby": {}, "refuse_ticki": 0, "ticki": 0,
                                     "klatki": 0, "klatki_bez": 0, "trk": [], "pasmo": [], "flow": [], "gnss": [], "nav": set(),
                                     "tempo": None})
    rama = sorted((r for r in jl(os.path.join(d, "rama.jsonl")) if r["ep"] == ep), key=lambda r: r["tick"])
    migawki, cache = {}, {}
    for r in rama:
        for ob in r.get("obs") or []:
            if not ob.get("ok") or ob.get("p_ekf_fix") is None:
                continue
            migawki[round(ob["t_frame"], 3)] = ob["p_ekf_fix"]
            if ob["t_frame"] < t_inj:
                continue
            b = nb(kosz(ob["t_frame"]))
            pa = probka(ob["p_ekf_fix"], ob["t_frame"], (-0.3, 0.3))
            if pa is not None and ob.get("kosz") is not None and ob.get("tryb") in NS.TRYBY_NAD2:
                g = GT(pa[0])
                a = float(math.hypot(ob["p_fix_ne"][0] - g[0], ob["p_fix_ne"][1] - g[1]))
                b["a_do_F"] = max(b["a_do_F"], a / (NS.ZAPAS_NAD2 * NS.F_NAD2[ob["tryb"]][ob["kosz"]]))
            if ob.get("para") and not ob["para"].get("odrzucona"):
                b["dpsi"].append(ob["para"]["dpsi_deg"])
    for r in rama:
        n2, ph = r.get("nad2"), r.get("ph")
        if ph not in UTRATA or n2 is None:
            continue
        b = nb(kosz(r["sim"]))
        b["ticki"] += 1
        b["refuse_ticki"] += int(ph == "KONT_REFUSE")
        i, tr, j = n2.get("przedzial"), n2.get("tryb"), (r.get("nadir") or {}).get("j")
        tau = (r.get("nadir") or {}).get("tau")
        b["przedzialy"][str(i)] = b["przedzialy"].get(str(i), 0) + 1
        b["tryby"][str(tr)] = b["tryby"].get(str(tr), 0) + 1
        b["r_est_max"] = n2["r_est"] if b["r_est_max"] is None else max(b["r_est_max"], n2["r_est"])
        if tau is not None:
            b["tau_max"] = tau if b["tau_max"] is None else max(b["tau_max"], tau)
        pt = probka(r["p_ekf"], r["sim"], (-0.4, 0.1))
        if pt is not None:
            g = GT(pt[0])
            b["ekf"].append(float(np.linalg.norm(pt[1] - g)))
        if i is None or j is None:
            continue
        zr = NS.r_nad2(i, j, tr, A.R_E) - n2["r_est"]
        b["zapas_min"] = zr if b["zapas_min"] is None else min(b["zapas_min"], zr)
        if pt is not None:
            pc = r["p_corr"]; g = GT(pt[0])
            e = float(math.hypot(pc[0] - g[0], pc[1] - g[1]))
            b["e"].append(e); b["eU"] = max(b["eU"], e / A.U_of(i, j, tr))
        tf = r.get("t_fix")
        if pt is None or tf is None or round(tf, 3) not in migawki:
            continue
        if round(tf, 3) not in cache:
            cache[round(tf, 3)] = probka(migawki[round(tf, 3)], tf, (-0.3, 0.3))
        pa = cache[round(tf, 3)]
        if pa is None:
            continue
        gr = float(np.linalg.norm((pt[1] - GT(pt[0])) - (pa[1] - GT(pa[0]))))
        b["przyrost_do_G"] = max(b["przyrost_do_G"], gr / (NS.ZAPAS_NAD2 * NS.G_NAD2[i]))
    for r in jl(os.path.join(d, "nadir_obs.jsonl"), "nf"):
        if "fx" in r and r["sim"] >= t_inj:
            b = nb(kosz(r["sim"]))
            b["klatki"] += 1; b["klatki_bez"] += int(not r["fx"].get("ok"))
    for r in jl(os.path.join(d, "trace.jsonl"), "tk"):
        if r.get("ep") != ep or r["sim"] < t_inj or r.get("desc"):
            continue
        b = nb(kosz(r["sim"]))
        b["trk"].append(r["trk_valid"])
        if r.get("intr") is not None:
            g = GT(r["sim"]); b["pasmo"].append(6.0 <= math.hypot(g[0] - r["intr"][0], g[1] - r["intr"][1]) <= 10.0)
    fl = u["estimator_status_flags"]
    for t, f1, f2 in zip(fl["timestamp"] / 1e6, fl["cs_opt_flow"], fl["cs_gnss_pos"]):
        if t >= t_inj and t <= (land["sim"] if land else 1e18):
            b = nb(kosz(t)); b["flow"].append(int(f1)); b["gnss"].append(int(f2))
    vs = u["vehicle_status"]
    for t, n in zip(vs["timestamp"] / 1e6, vs["nav_state"]):
        if t >= t_inj and t <= (land["sim"] if land else 1e18):
            nb(kosz(t))["nav"].add(int(n))
    rtf = [json.loads(l) for l in open(os.path.join(d, "rtf_stream.jsonl")) if '"sim"' in l] if os.path.exists(os.path.join(d, "rtf_stream.jsonl")) else []
    rtf = [(float(r["sim"]), float(r["wall"])) for r in rtf if r.get("sim") is not None and r.get("wall") is not None]
    for k in list(B):
        s = [x for x in rtf if kosz(x[0]) == k and x[0] >= t_inj]
        if len(s) > 1 and s[-1][1] > s[0][1]:
            B[k]["tempo"] = round((s[-1][0] - s[0][0]) / (s[-1][1] - s[0][1]), 4)
    out = {}
    q = lambda xs, p: round(float(np.quantile(xs, p)), 4) if xs else None
    B.pop("_", None)
    for k in sorted(B):
        b = B[k]
        out[k] = {"e_corr": {"p50": q(b["e"], .5), "p95": q(b["e"], .95), "max": round(max(b["e"]), 4) if b["e"] else None, "n": len(b["e"])},
                  "max_e_do_U": round(b["eU"], 4), "a_max_do_1_5F": round(b["a_do_F"], 4), "przyrost_max_do_1_5G": round(b["przyrost_do_G"], 4),
                  "bias_kursu_p50_deg": round(float(np.median(b["dpsi"])), 3) if b["dpsi"] else None, "n_par": len(b["dpsi"]),
                  "ekf_wlasny": {"p50": q(b["ekf"], .5), "max": round(max(b["ekf"]), 4) if b["ekf"] else None},
                  "zapas_bariery_min": None if b["zapas_min"] is None else round(b["zapas_min"], 4),
                  "r_est_max": None if b["r_est_max"] is None else round(b["r_est_max"], 4), "tau_max": b["tau_max"],
                  "przedzialy": b["przedzialy"], "tryby": b["tryby"], "refuse_ticki": b["refuse_ticki"], "ticki": b["ticki"],
                  "klatki_bez_poprawki": b["klatki_bez"], "klatki": b["klatki"],
                  "track": round(float(np.mean(b["trk"])), 3) if b["trk"] else None,
                  "pasmo": round(float(np.mean(b["pasmo"])), 3) if b["pasmo"] else None,
                  "cs_opt_flow": round(float(np.mean(b["flow"])), 3) if b["flow"] else None,
                  "cs_gnss_pos": round(float(np.mean(b["gnss"])), 3) if b["gnss"] else None,
                  "nav_state": sorted(b["nav"]), "tempo": b["tempo"]}
    o = next(x for x in an["epizody"] if x["ciecie"])
    wyn = {"boot": os.path.basename(d.rstrip("/")), "t_inj_sim": t_inj, "zejscie_planowe_sim": zp["sim"] if zp else None,
           "kontynuacja_s": o["D1"]["kontynuacja_od_t_inj_s"], "przyziemienie": land is not None,
           "refuse": [e for e in ev if e.get("ev") == "refuse"][:5],
           "B": {b: o[b] for b in ("B1", "B2", "B3", "B4")}, "D1": o["D1"], "przedzialy_100s": out}
    json.dump(wyn, open(os.path.join(d, "obserwable_s4_okna.json" if OKNA else "obserwable_s4.json"), "w"), ensure_ascii=False, indent=1, default=str)
    f = lambda x, n=3: "—" if x is None else (f"{x:.{n}f}" if isinstance(x, float) else str(x))
    print(json.dumps({k: wyn[k] for k in ("boot", "kontynuacja_s", "przyziemienie")} | {b: o[b]["ok"] for b in ("B1", "B2", "B3", "B4")}))
    print("\n| przedział [s od cięcia] | e_corr p50/p95/max [m] | max e/U | a/1.5F | przyrost/1.5G | bias kursu p50 [°] (pary) | EKF p50/max [m] | zapas bariery min [m] | r_est max [m] | τ max [s] |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for k, r in out.items():
        e = r["e_corr"]
        print(f"| {k} | {f(e['p50'])}/{f(e['p95'])}/{f(e['max'])} | {f(r['max_e_do_U'])} | {f(r['a_max_do_1_5F'])} | {f(r['przyrost_max_do_1_5G'])} | "
              f"{f(r['bias_kursu_p50_deg'], 2)} ({r['n_par']}) | {f(r['ekf_wlasny']['p50'])}/{f(r['ekf_wlasny']['max'])} | {f(r['zapas_bariery_min'])} | "
              f"{f(r['r_est_max'])} | {f(r['tau_max'])} |")
    print("\n| przedział | przedziały τ (ticki) | tryby (ticki) | REFUSE ticki | klatki bez poprawki | track | pasmo | cs_opt_flow | cs_gnss_pos | nav_state | tempo |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for k, r in out.items():
        print(f"| {k} | {', '.join(f'{a}:{b}' for a, b in sorted(r['przedzialy'].items()))} | {', '.join(f'{a} {b}' for a, b in r['tryby'].items())} | "
              f"{r['refuse_ticki']} | {r['klatki_bez_poprawki']}/{r['klatki']} | {f(r['track'])} | {f(r['pasmo'])} | {f(r['cs_opt_flow'])} | "
              f"{f(r['cs_gnss_pos'])} | {r['nav_state']} | {f(r['tempo'], 4)} |")


if __name__ == "__main__":
    main(sys.argv[1])  # --okna czytane z sys.argv
