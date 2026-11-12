#!/usr/bin/env python3
"""results/NAD2/tools/nad2_s3_raport.py — PROMPT_NAD2_S3 §2: werdykt mechaniczny i tabela per epizod z bootów ważnych księgi S3.

Litera (z analizatora nad2_analyze, wyniki_nad2.json per boot, bez przeliczania): B1–B5 — liczba epizodów z naruszeniem; D1 — ile
z 12 cięć dostępnych (próg ≥ 10) i które niedostępne z przyczyną.
Obserwable (bez progu), liczone tu z rama.jsonl, trace.jsonl, nadir_obs.jsonl i boot.ulg (lokalny):
  - fazy misji cięcia = ticki utraty przed komendą planowego zejścia (zdarzenie zejscie_planowe; PROMPT_NAD2_S3 doprecyzowanie 1):
    τ max, przedziały, tryby, ticki KONT_REFUSE (REFUSE misji), zapas bariery min, r_est max; zejście: ticki KONT_REFUSE i τ max;
  - klatki bez poprawki = rekordy nf producenta w oknie [t_flag, zejście) z fx.ok = False (t_flag = denial w trace);
  - horyzont prawdziwy = ts(próbka EKF ticku) − ta(próbka EKF migawki poprawki), obie dopasowane po wartości jak w analizatorze;
    max (horyzont − (τ + 0.012 s)); przyrost EKF = |(p_EKF − GT)(ts) − (p_EKF − GT)(ta)| poziomo wobec 1.5 · G(przedział ticku);
  - z analizatora: e_corr p50/p95/max, max e_corr/U, margines R_E, a poprawek wobec 1.5 · F, bias kursu, ticki u′ > m, tempo.
Wyjście: results/NAD2/s3/wyniki_s3.json; tabela markdown na stdout. Użycie: nad2_s3_raport.py
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

S3 = os.path.join(ROOT, "results/NAD2/s3")
UTRATA = ("KONT", "KONT_REFUSE")


def jl(p, typ=None):
    return A.jl(p, typ)


def obserwable_ciecia(d, ep):
    ev = jl(os.path.join(d, "trace.jsonl"), "event")
    e1 = lambda n: next((e for e in ev if e.get("ev") == n), None)
    zp, den = e1("zejscie_planowe"), e1("denial")
    t_zp = zp["sim"] if zp else 1e18
    gt = sorted(jl(os.path.join(d, "trace.jsonl"), "gt"), key=lambda r: r["sim"])
    gt_t = np.array([g["sim"] for g in gt])
    gt_ned = np.array([[g["y"], g["x"], -g["z"]] for g in gt])
    GT = lambda t: np.array([np.interp(t, gt_t, gt_ned[:, i]) for i in range(2)])
    u = A.ulg(d)
    v = u["vehicle_local_position"]
    vt, vts = v["timestamp"] / 1e6, v["timestamp_sample"] / 1e6
    vp = np.stack([v["x"], v["y"]], 1)

    def probka(p, t_ref, okno):
        i0, i1 = bisect.bisect_left(vt, t_ref + okno[0]), bisect.bisect_right(vt, t_ref + okno[1])
        if i1 <= i0:
            return None
        k = i0 + int(np.argmin(np.linalg.norm(vp[i0:i1] - np.asarray(p[:2], float), axis=1)))
        return float(vts[k]), vp[k]

    rama = sorted((r for r in jl(os.path.join(d, "rama.jsonl")) if r["ep"] == ep), key=lambda r: r["tick"])
    migawki = {}
    for r in rama:
        for ob in r.get("obs") or []:
            if ob.get("ok") and ob.get("p_ekf_fix") is not None:
                migawki[round(ob["t_frame"], 3)] = ob["p_ekf_fix"]
    m = {"t_zejscia": zp["sim"] if zp else None, "tau_max": None, "przedzialy": {}, "tryby": {}, "refuse_ticki": 0, "zapas_min": None,
         "r_est_max": None, "horyzont_nadwyzka_max_s": None, "przyrost_do_1_5G_max": None, "ticki": 0}
    z = {"ticki_refuse": 0, "tau_max": None}
    cache = {}
    for r in rama:
        n2, ph = r.get("nad2"), r.get("ph")
        if ph not in UTRATA or n2 is None:
            continue
        tau = (r.get("nadir") or {}).get("tau")
        if r["sim"] >= t_zp:
            z["ticki_refuse"] += int(ph == "KONT_REFUSE")
            if tau is not None:
                z["tau_max"] = tau if z["tau_max"] is None else max(z["tau_max"], tau)
            continue
        m["ticki"] += 1
        m["refuse_ticki"] += int(ph == "KONT_REFUSE")
        i, tr, j = n2.get("przedzial"), n2.get("tryb"), (r.get("nadir") or {}).get("j")
        m["przedzialy"][str(i)] = m["przedzialy"].get(str(i), 0) + 1
        m["tryby"][str(tr)] = m["tryby"].get(str(tr), 0) + 1
        m["r_est_max"] = n2["r_est"] if m["r_est_max"] is None else max(m["r_est_max"], n2["r_est"])
        if tau is not None:
            m["tau_max"] = tau if m["tau_max"] is None else max(m["tau_max"], tau)
        if i is None or j is None:
            continue
        zr = NS.r_nad2(i, j, tr, A.R_E) - n2["r_est"]
        m["zapas_min"] = zr if m["zapas_min"] is None else min(m["zapas_min"], zr)
        tf = r.get("t_fix")
        if tau is None or tf is None or round(tf, 3) not in migawki:
            continue
        pt = probka(r["p_ekf"], r["sim"], (-0.4, 0.1))
        if round(tf, 3) not in cache:
            cache[round(tf, 3)] = probka(migawki[round(tf, 3)], tf, (-0.3, 0.3))
        pa = cache[round(tf, 3)]
        if pt is None or pa is None:
            continue
        nad = (pt[0] - pa[0]) - (tau + NS.TAU_EPS_NAD2)
        m["horyzont_nadwyzka_max_s"] = nad if m["horyzont_nadwyzka_max_s"] is None else max(m["horyzont_nadwyzka_max_s"], nad)
        g = float(np.linalg.norm((pt[1] - GT(pt[0])) - (pa[1] - GT(pa[0]))))
        q = g / (NS.ZAPAS_NAD2 * NS.G_NAD2[i])
        m["przyrost_do_1_5G_max"] = q if m["przyrost_do_1_5G_max"] is None else max(m["przyrost_do_1_5G_max"], q)
    nf = [r for r in jl(os.path.join(d, "nadir_obs.jsonl"), "nf") if "fx" in r]
    t0 = den["sim"] if den else 1e18
    okno = [r for r in nf if t0 <= r["sim"] < t_zp]
    m["klatki_okno"], m["klatki_bez_poprawki"] = len(okno), sum(1 for r in okno if not r["fx"].get("ok"))
    for k in ("tau_max", "zapas_min", "r_est_max", "horyzont_nadwyzka_max_s", "przyrost_do_1_5G_max"):
        if m[k] is not None:
            m[k] = round(m[k], 4)
    return {"misja": m, "zejscie": z, "refuse_pos_land": e1("refuse_pos_land") is not None}


def main():
    ks = [json.loads(l) for l in open(os.path.join(S3, "kampania_ksiega.jsonl")) if l.strip()]
    wazne = [w for w in ks if w["wazny"]]
    epi, booty = [], []
    for w in wazne:
        d = os.path.join(S3, w["nazwa"])
        an = json.load(open(os.path.join(d, "wyniki_nad2.json")))
        tempo = (w.get("tempo") or {}).get("dsim_dwall_settle")
        booty.append({"nazwa": w["nazwa"], "pozycja": w["pozycja"], "boot_s3": w["boot_s3"], "tempo": tempo, "sprawdziany": w["sprawdziany"],
                      "ulg_MB": (w.get("ulg") or {}).get("MB")})
        for o in an["epizody"]:
            row = {"boot": w["nazwa"], "pozycja": w["pozycja"], "tempo": tempo, **o}
            if o["ciecie"]:
                row["obs"] = obserwable_ciecia(d, o["episode_id"])
            epi.append(row)
    lit = {b: [f"{r['boot']}/{r['scenario_id']}" for r in epi if b in r and not r[b]["ok"]] for b in ("B1", "B2", "B3", "B4", "B5")}
    ciecia = [r for r in epi if r["ciecie"]]
    d1_nie = [{"cięcie": r["scenario_id"], "boot": r["boot"], "D1": r["D1"]} for r in ciecia if not r["D1"]["dostepne"]]
    werdykt = {"B_naruszenia_epizodow": {b: len(v) for b, v in lit.items()}, "B_naruszenia": lit,
               "bezpieczenstwo_PASS": all(not v for v in lit.values()),
               "D1_dostepne": sum(r["D1"]["dostepne"] for r in ciecia), "D1_z": len(ciecia), "D1_niedostepne": d1_nie,
               "D1_PASS": sum(r["D1"]["dostepne"] for r in ciecia) >= 10 and len(ciecia) == 12,
               "epizody_ciec": len(ciecia), "epizody_nominalne": len(epi) - len(ciecia)}
    werdykt["PASS"] = werdykt["bezpieczenstwo_PASS"] and werdykt["D1_PASS"]
    out = {"prompt": "PROMPT_NAD2_S3 (sha256 c7e294a8)", "werdykt": werdykt, "booty_wazne": booty,
           "booty_zuzyte": len(ks), "budzet": 19, "noga": 2 + len(ks), "epizody": epi}
    json.dump(out, open(os.path.join(S3, "wyniki_s3.json"), "w"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps(werdykt, ensure_ascii=False))
    f = lambda x, n=3: "—" if x is None else (f"{x:.{n}f}" if isinstance(x, float) else str(x))
    print("\n| epizod | boot | kontynuacja [s] | max e_corr/U | margines R_E [m] | zapas bariery min misja [m] | τ max misja [s] | tryby (ticki misji) | REFUSE misja / zejście (ticki) | tempo |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for r in ciecia:
        m, z = r["obs"]["misja"], r["obs"]["zejscie"]
        print(f"| {r['scenario_id']} | {r['boot']} | {f(r['D1']['kontynuacja_od_t_inj_s'])} | {f(r['B1']['max_e_do_U'])} | {f(r['B2']['margines_min'])} | "
              f"{f(m['zapas_min'])} | {f(m['tau_max'])} | {', '.join(f'{k} {v}' for k, v in m['tryby'].items())} | {m['refuse_ticki']} / {z['ticki_refuse']} | {f(r['tempo'], 4)} |")
    print("\n| nominał | epizod | B1–B5 | margines R_E [m] | ticki ≠ NOMINAL | REFUSE | tempo |")
    print("|---|---|---|---|---|---|---|")
    for r in epi:
        if r["ciecie"]:
            continue
        print(f"| {r['boot']} | {r['scenario_id']} | {'PASS' if r['bezpieczenstwo_ok'] else 'FAIL'} | {f(r['B2']['margines_min'])} | "
              f"{r['B5']['ticki_nie_nominal']} | {r['B5']['refuse']} | {f(r['tempo'], 4)} |")
    print("\n| epizod | e_corr p50/p95/max [m] | a max / 1.5F | przyrost EKF max / 1.5G | max (horyzont − (τ+0.012)) [s] | klatki bez poprawki | r_est max [m] | u′>m ticki | bias kursu p50 [°] | τ max zejście [s] |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for r in ciecia:
        m, z, e, a = r["obs"]["misja"], r["obs"]["zejscie"], r["e_corr"] or {}, r["a_poprawek"] or {}
        print(f"| {r['scenario_id']} | {f(e.get('p50'))}/{f(e.get('p95'))}/{f(e.get('max'))} | {f(a.get('max_do_1_5F'))} | {f(m['przyrost_do_1_5G_max'])} | "
              f"{f(m['horyzont_nadwyzka_max_s'])} | {m['klatki_bez_poprawki']}/{m['klatki_okno']} | {f(m['r_est_max'])} | {r['u_prim_gt_m_ticki']} | "
              f"{f((r['bias_kursu_par'] or {}).get('p50'), 2)} | {f(z['tau_max'])} |")


if __name__ == "__main__":
    main()
