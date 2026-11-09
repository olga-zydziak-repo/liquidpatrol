#!/usr/bin/env python3
"""results/NADIR/tools/nadir_s2_analyze.py — analiza bootów S2 NADIR (PROMPT_NADIR_S2 §R1–§R5). Prerejestracja definicji
(commit przed pierwszym bootem S2).

Wejścia per boot (results/NADIR/s2/<nazwa>/): trace.jsonl (gt ENU + kwaternion, ekf, tk, zdarzenia), rama.jsonl (driver,
log ramy per tick), nadir_obs.jsonl (wiersze nf z rekordem producenta "fx"), percep_feed.jsonl (rdzeń feedu, "pred_odrzut"),
gt_intruder.jsonl, demo.jsonl, boot.ulg, rtf_stream.jsonl. Litera KONT S4 (V2′, t_flag z ulogu, REFUSE, (a)–(f), ε od t_flag)
— results/KONT/tools/kont_s4_analyze.analyze importem (READ-ONLY; zapisuje wyniki_s4.json w katalogu bootu), porównanie
z bootem KONT S4 tego samego scenariusza (results/KONT/s4/<scenariusz>/wyniki_s4.json).
Stałe: ε_b = eps_b_obwiednia, Δ_D5 = 1.524 z results/KONT/s2/s2_freeze_bf.json (sha ae19f66c, asercja); m komórki =
results/KONT_RECON/r4_margin.json tabela_scenariuszy[scenariusz].m.
Poprawka = wiersz nf z fx.ok; t_fix = stempel sim klatki, chwila EKF poprawki = mono przybycia klatki (migawka EKF producenta).

R1 okna ważności B: okno = [poprawka k, poprawka k+1) (ostatnie do końca epizodu/przyziemienia). Błąd EKF e(t) = (p_EKF − GT)
poziomo, wektor, parowanie po mono z korektą skew (gt_judge._paired_series/compute_drift, jak kont_s4_analyze); przyrost
inc(t) = |e(t) − e(t_fix)|, τ = sim(t) − t_fix; przekroczenie ⇔ inc(t) > ε_b(⌊τ⌋). Klasy okien: „z_GNSS” (przed t_flag),
„bez_GNSS” (t_flag ≤ t < REFUSE), „zejscie_D5” (od REFUSE — osobno, poza wymogiem). Wymóg: 0 przekroczeń w oknach z_GNSS ∪
bez_GNSS. Okna z τ > 2 s raportowane z liczbą (litera: τ do 2 s).
R2 ε_fix na żywo: per poprawka |p_fix − GT(t_klatki)| poziomo (GT po sim, interpolacja jak nadir_s1v2_analyze); osobno
kandydat „jeden” (rekord fx.jeden) i „para” (fx.para, gdy jest i nie odrzucona) i „użyta”; koszyki r_h 0–2/…/10+ (r_h z GT
kamery do znacznika najbliższego poprawki); przed i po t_flag; max per koszyk (dane do FREEZE 1.5 × max). Bias kursu δψ z par
w czasie: przed t_flag, bez GNSS (do REFUSE); p50 i trend (nachylenie δψ(t) °/s). Odrzucone obserwacje: udział i powody
(z fx.odrz i fx.powod) per klatkę i per detekcję.
R3 sieć na p_corr: t_entry, kontynuacja do REFUSE i przyczyna (T*/bariera), (c) pasmo/track w oknie bez GNSS — z litery KONT S4
vs boot KONT S4 tego samego scenariusza; REFUSE poza barierą = każdy REFUSE ≠ R-KONT(T*/bariera) w epizodzie; skoki p_corr
= |Δ(d_ne)| przy zmianie stanu ramy (rama.jsonl), rozkład vs skala szumu GNSS ramienia nominalnego KONT = |e(t+0.2 s) − e(t)|
(EKF − GT) w epizodach nominalnych ważnych bootów nom_* KONT S4; V2′ i bramka tempa settle (kont_tempo.json).
R4 piła pod misją: per tick rama.jsonl w fazach approach/hold/orbit (bez zejścia): ε_fix_live = błąd R2 poprawki obowiązującej
w ticku, u = ε_fix_live + ε_b(⌊τ⌋) + Δ_D5 vs m; max u, ticki z u > m; τ p95/max per epizod; ogony τ (okna > 1 s) z węzłem
manifestu najbliższym pozycji GT — przy węzłach koron (id 0, 8, 15, 16, 22, 32, 35) czy nie.
R5 bramka predykcji: odrzucenia pred_odrzut per epizod z klasą (box ≤ 3 m od intruza GT ∧ predykcja ≤ 3 m ⇒ „intruz przy
tracku na intruzie” = odrzucenie prawdziwego intruza; box przy intruzie, predykcja dalej ⇒ „intruz przy tracku zastanym”;
box > 3 m ⇒ „box nie na intruzie”), w epizodzie / poza.
Użycie: nadir_s2_analyze.py <boot_dir> [...]; wyjście results/NADIR/s2/{r1_okna,r2_eps_fix,r3_siec,r4_pila}.json.
"""
import bisect
import hashlib
import json
import math
import os
import sys

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/NADIR/tools"), os.path.join(ROOT, "results/KONT/tools"),
                os.path.join(ROOT, "results/R03/recon/B1bis/instrument")]
import nadir_s1v2_analyze as S1A                             # READ-ONLY: GT, fazy, faza_at, load, pct, RH_BINS
import kont_s4_analyze as K4                                 # READ-ONLY: litera KONT S4
import gt_judge as J                                         # READ-ONLY
from harness import nadir_fix as NF

S2 = os.path.join(ROOT, "results/NADIR/s2")
FREEZE = os.path.join(ROOT, "results/KONT/s2/s2_freeze_bf.json")
FREEZE_SHA = "ae19f66c6807de6c824bf0fd723965258b15b77963eb866afb78d3dd3740ae4a"
MARG = json.load(open(os.path.join(ROOT, "results/KONT_RECON/r4_margin.json")))["tabela_scenariuszy"]
KORONY = {0, 8, 15, 16, 22, 32, 35}
MISJA = ("approach", "hold", "orbit")
ZN = {z["id"]: z for z in json.load(open(NF.MANIFEST))["znaczniki"]}
pct = S1A.pct


def epsb(eps_b, tau):
    k = int(tau)
    return eps_b[min(k, len(eps_b) - 1)]


def seria_e(tr):
    """Wektor e(t) = p_EKF − GT (N, E) po mono, skew jak gt_judge.compute_drift (okno zdrowe przed pierwszym dr)."""
    ekf = sorted([r for r in tr if r.get("t") == "ekf"], key=lambda r: r["mono"])
    gt = sorted([r for r in tr if r.get("t") == "gt" and "sim" in r], key=lambda r: r["mono"])
    m = J.compute_drift(ekf, gt) if any(r.get("dead_reckoning") for r in ekf) else None
    ts = (m["skew_hat_s"] if m and m["skew_applied"] else 0.0)
    s = J._paired_series(ekf, gt, True, ts)
    return np.array([x[0] for x in s]), np.array([[x[1], x[2]] for x in s]), (m or {}).get("skew_hat_s")


def boot(d):
    tr = S1A.load(os.path.join(d, "trace.jsonl"))
    evs = [r for r in tr if r.get("t") == "event"]
    ev1 = lambda n: next((e for e in evs if e["ev"] == n), None)
    k4 = K4.analyze(d)                                         # litera KONT S4 (zapisuje wyniki_s4.json)
    ep0 = ev1("episode_start")
    epi = k4["epizody"][0] if k4.get("epizody") else {}
    scen = ep0["scenario_id"] if ep0 else None
    gt = S1A.GT(os.path.join(d, "trace.jsonl"))
    rows, rt, _ = S1A.fazy(os.path.join(d, "demo.jsonl"))
    g = sorted([r for r in tr if r.get("t") == "gt" and "sim" in r], key=lambda r: r["mono"])
    gm, gs = np.array([r["mono"] for r in g]), np.array([r["sim"] for r in g])
    m2s = lambda t: float(np.interp(t, gm, gs))
    t_flag = epi.get("t_flag")
    ref = epi.get("refuse") or {}
    t_ref = ref.get("sim")
    t_land = epi.get("t_land")
    t_ep0 = ep0["sim"] if ep0 else None
    en = ev1("episode_end")
    t_end = t_land or (en["sim"] if en else None)
    nf = sorted([r for r in S1A.load(os.path.join(d, "nadir_obs.jsonl"), "nf") if "fx" in r], key=lambda r: r["mono"])
    # --- R2: błędy poprawek
    fixes = []
    odrz_pow, n_det, n_kl, n_kl_ok = {}, 0, 0, 0
    for fr in nf:
        fx = fr["fx"]
        ph, _ = S1A.faza_at(rows, rt, fr["sim"])
        w_ep = t_ep0 is not None and fr["sim"] >= t_ep0 and (t_end is None or fr["sim"] <= t_end)
        if w_ep:
            n_kl += 1; n_kl_ok += int(fx["ok"]); n_det += fx["n_det"]
            for o in fx["odrz"]:
                odrz_pow[o["powod"]] = odrz_pow.get(o["powod"], 0) + 1
            if not fx["ok"]:
                k = "klatka_" + fx.get("powod", "?")
                odrz_pow[k] = odrz_pow.get(k, 0) + 1
        if not fx["ok"]:
            continue
        gg = gt.at(fr["sim"])
        if gg is None:
            continue
        p0, q = gg
        cam = p0 + S1A.rotm(q) @ NF.MOUNT
        e_ne = lambda p: math.hypot(p[1] - p0[0], p[0] - p0[1])
        idn = fx["jeden"]["id"]
        rec = {"t": fr["sim"], "mono": fr["mono"], "faza": ph, "w_ep": w_ep, "tryb": fx["tryb"],
               "rh": math.hypot(ZN[idn]["E"] - cam[0], ZN[idn]["N"] - cam[1]),
               "bez_gnss": t_flag is not None and fr["sim"] >= t_flag, "po_refuse": t_ref is not None and fr["sim"] >= t_ref,
               "uzyta": e_ne(fx["p_fix_ne"]), "jeden": e_ne(fx["jeden"]["p_ne"]),
               "para": e_ne(fx["para"]["p_ne"]) if fx.get("para") and not fx["para"].get("odrzucona") else None,
               "dpsi": fx["para"]["dpsi_deg"] if fx.get("para") else None, "seq": fx["seq"]}
        fixes.append(rec)
    # --- R1: okna
    tser = S1A.load(os.path.join(d, "trace.jsonl"))
    if t_flag is not None:
        cut = ev1("denial"); land = ev1("gt_przyziemienie")
        for r in tser:
            if r.get("t") == "ekf":
                r["dead_reckoning"] = cut is not None and cut["mono"] <= r["mono"] <= (land["mono"] if land else 1e18)
    em, ev, skew = seria_e(tser)
    eps_b = json.load(open(FREEZE))["eps_b_obwiednia"]
    okna = []
    fx_all = [f for f in fixes]
    for i, f in enumerate(fx_all):
        if t_ep0 is None or f["t"] < t_ep0 or (t_end is not None and f["t"] > t_end):
            continue
        m0 = f["mono"]
        m1 = fx_all[i + 1]["mono"] if i + 1 < len(fx_all) else (em[-1] if len(em) else m0)
        e0 = np.array([np.interp(m0, em, ev[:, 0]), np.interp(m0, em, ev[:, 1])])
        sel = np.flatnonzero((em > m0) & (em < m1))
        klasa = "zejscie_D5" if f["po_refuse"] else ("bez_GNSS" if f["bez_gnss"] else "z_GNSS")
        worst, n_prz, tau_max = 0.0, 0, 0.0
        for j in sel:
            tau = m2s(em[j]) - f["t"]
            inc = float(np.linalg.norm(ev[j] - e0))
            b = epsb(eps_b, tau)
            worst = max(worst, inc / b)
            n_prz += int(inc > b)
            tau_max = max(tau_max, tau)
        okna.append({"t_fix": round(f["t"], 3), "klasa": klasa, "tau_max": round(tau_max, 3), "n_probek": int(len(sel)),
                     "max_inc_do_eps_b": round(worst, 4), "przekroczenia": n_prz})
    r1 = {"skew_s": skew, "okna": {}}
    for kl in ("z_GNSS", "bez_GNSS", "zejscie_D5"):
        o = [x for x in okna if x["klasa"] == kl]
        r1["okna"][kl] = {"n": len(o), "z_przekroczeniem": sum(x["przekroczenia"] > 0 for x in o),
                          "max_inc_do_eps_b": max((x["max_inc_do_eps_b"] for x in o), default=None),
                          "tau_gt_2s": sum(x["tau_max"] > 2.0 for x in o),
                          "najgorsze": sorted(o, key=lambda x: -x["max_inc_do_eps_b"])[:5]}
    r1["przekroczenia_w_wymogu"] = r1["okna"]["z_GNSS"]["z_przekroczeniem"] + r1["okna"]["bez_GNSS"]["z_przekroczeniem"]
    # --- R4: piła per tick
    rama = S1A.load(os.path.join(d, "rama.jsonl"))
    err_by_seq = {f["seq"]: f["uzyta"] for f in fixes}
    seq_ok = sorted(err_by_seq)
    m_cell = MARG.get(scen, {}).get("m")
    dd5 = json.load(open(FREEZE))["delta_D5"]
    ut, taus, ogony, u_over, bez_fix = [], [], [], 0, 0
    for r in rama:
        if r.get("phase") not in MISJA or r.get("desc") or r.get("tau") is None:
            if r.get("phase") in MISJA and not r.get("desc") and r.get("tau") is None:
                bez_fix += 1
            continue
        k = bisect.bisect_right(seq_ok, r["seq"]) - 1
        if k < 0:
            continue
        ef = err_by_seq[seq_ok[k]]
        u = ef + epsb(eps_b, r["tau"]) + dd5
        bg = t_flag is not None and r["sim"] >= t_flag
        ut.append((r["sim"], u, ef, r["tau"], bg))
        taus.append(r["tau"])
        if m_cell is not None and u > m_cell:
            u_over += 1
    # ogony τ > 1 s: najbliższy węzeł do GT
    prev = None
    for r in rama:
        if r.get("phase") not in MISJA or r.get("desc") or r.get("tau") is None or r.get("gt") is None:
            continue
        if r["tau"] > 1.0 and (prev is None or r["t_fix"] != prev):
            prev = r["t_fix"]
            x, y = r["gt"][0], r["gt"][1]
            nid = min(ZN, key=lambda i: math.hypot(ZN[i]["E"] - x, ZN[i]["N"] - y))
            ogony.append({"t_fix": r["t_fix"], "wezel": nid, "d_wezla": round(math.hypot(ZN[nid]["E"] - x, ZN[nid]["N"] - y), 2),
                          "korona": nid in KORONY})
    for r in rama:                                             # τ max okna ogona = ostatni tick z tym t_fix
        pass
    tau_okna = {}
    for r in rama:
        if r.get("phase") in MISJA and not r.get("desc") and r.get("tau") is not None:
            tau_okna[r["t_fix"]] = max(tau_okna.get(r["t_fix"], 0.0), r["tau"])
    for o in ogony:
        o["tau_max"] = round(tau_okna.get(o["t_fix"], 0.0), 3)
    r4 = {"scenariusz": scen, "m": m_cell, "n_tickow": len(ut), "ticki_bez_poprawki": bez_fix,
          "u_max": round(max((x[1] for x in ut), default=0), 3), "u_max_bez_GNSS": round(max((x[1] for x in ut if x[4]), default=0), 3),
          "ticki_u_gt_m": u_over, "u_p95": pct([x[1] for x in ut], .95),
          "najgorszy": (lambda w: {"sim": w[0], "u": round(w[1], 3), "eps_fix": round(w[2], 3), "tau": w[3], "bez_GNSS": w[4]})(
              max(ut, key=lambda x: x[1])) if ut else None,
          "tau_p95": pct(taus, .95), "tau_max": round(max(taus), 3) if taus else None, "ogony_tau_gt_1s": ogony,
          "ogony_przy_koronach": sum(o["korona"] for o in ogony)}
    r4["PASS"] = m_cell is not None and u_over == 0
    # --- R3: sieć
    skoki = []
    last = None
    for r in rama:
        if last is not None and r["d_ne"] != last:
            skoki.append(math.hypot(r["d_ne"][0] - last[0], r["d_ne"][1] - last[1]))
        last = r["d_ne"]
    pf = [x for x in S1A.load(os.path.join(d, "percep_feed.jsonl")) if "t_frame" in x]
    intr = sorted(S1A.load(os.path.join(d, "gt_intruder.jsonl")), key=lambda r: r["t_sim"])
    it = [r["t_sim"] for r in intr]

    def d_intr(t, p):
        j = min(bisect.bisect_left(it, t), len(intr) - 1) if intr else None
        return math.dist(p, intr[j]["ned"]) if intr and abs(intr[j]["t_sim"] - t) <= 0.1 else None
    r5 = {"odrzucenia": [], "klasy": {}}
    for x in pf:
        o = x.get("pred_odrzut")
        if not o:
            continue
        dc, dp = d_intr(x["t_frame"], o["cand"]), d_intr(x["t_frame"], o["pred"])
        kl = ("box_nie_na_intruzie" if dc is None or dc > 3 else
              "intruz_przy_tracku_na_intruzie" if dp is not None and dp <= 3 else "intruz_przy_tracku_zastanym")
        w_ep = t_ep0 is not None and x["t_frame"] >= t_ep0 and (t_end is None or x["t_frame"] <= t_end)
        r5["odrzucenia"].append({"t": x["t_frame"], "w_ep": w_ep, "klasa": kl, "d": o["d"], "prog": o["prog"],
                                 "d_cand_intruz": None if dc is None else round(dc, 2), "d_pred_intruz": None if dp is None else round(dp, 2)})
        key = kl + ("_w_epizodzie" if w_ep else "_poza")
        r5["klasy"][key] = r5["klasy"].get(key, 0) + 1
    r5["odrzucenia_prawdziwego_intruza"] = sum(o["klasa"] == "intruz_przy_tracku_na_intruzie" for o in r5["odrzucenia"])
    r5["PASS"] = r5["odrzucenia_prawdziwego_intruza"] == 0
    ref_k4 = os.path.join(ROOT, "results/KONT/s4", scen or "-", "wyniki_s4.json")
    kk = json.load(open(ref_k4)) if os.path.exists(ref_k4) else None
    kke = (kk or {}).get("epizody", [{}])[0] if kk else {}
    refuse_inne = [e for e in evs if e["ev"] == "refuse" and not (e.get("reason") == "POS_DEGRADED")]
    tempo = json.load(open(os.path.join(d, "kont_tempo.json"))) if os.path.exists(os.path.join(d, "kont_tempo.json")) else None
    r3 = {"scenariusz": scen, "t_entry": epi.get("t_entry"), "t_entry_kont_s4": kke.get("t_entry"),
          "kontynuacja_s": epi.get("kontynuacja_s"), "kontynuacja_kont_s4": kke.get("kontynuacja_s"),
          "przyczyna_konca": epi.get("przyczyna_konca"), "przyczyna_kont_s4": kke.get("przyczyna_konca"),
          "c_frac_track": epi.get("c_frac_track"), "c_frac_pasmo": epi.get("c_frac_pasmo"),
          "c_kont_s4": [kke.get("c_frac_track"), kke.get("c_frac_pasmo")],
          "litera_kont_s4": {k: epi.get(k) for k in ("a_ok", "b_ok", "c_ok", "d_ok", "e_ok", "f_ok", "v2p_ok")},
          "refuse": ref, "refuse_poza_bariera": len(refuse_inne), "breach": any(e["ev"] in ("breach", "breach_gt") for e in evs),
          "skoki_p_corr": {"n": len(skoki), "p50": pct(skoki, .5), "p95": pct(skoki, .95), "max": round(max(skoki), 3) if skoki else None},
          "v2p": epi.get("v2p"), "tempo_settle": tempo, "wazny_k4": k4.get("wazny"), "powod_niewazny_k4": k4.get("powod_niewazny")}
    r2 = {"fixes": fixes, "klatki_w_epizodzie": n_kl, "klatki_z_poprawka": n_kl_ok, "detekcje_w_epizodzie": n_det,
          "odrzucenia_powody": odrz_pow}
    return {"boot": os.path.basename(d.rstrip("/")), "scenariusz": scen, "t_flag": t_flag, "t_ref": t_ref,
            "r1": r1, "r2": r2, "r3": r3, "r4": r4, "r5": r5}


def gnss_szum():
    """|e(t+0.2) − e(t)| (EKF − GT) w epizodach nominalnych ważnych bootów nom_* KONT S4 — skala szumu GNSS."""
    out = []
    base = os.path.join(ROOT, "results/KONT/s4")
    for b in sorted(os.listdir(base)):
        d = os.path.join(base, b)
        w = os.path.join(d, "wyniki_s4.json")
        if not (b.startswith("nom_") and os.path.isdir(d) and os.path.exists(w) and json.load(open(w)).get("wazny")):
            continue
        tr = S1A.load(os.path.join(d, "trace.jsonl"))
        evs = [r for r in tr if r.get("t") == "event"]
        win = [(s["mono"], e["mono"]) for s, e in zip([x for x in evs if x["ev"] == "episode_start"], [x for x in evs if x["ev"] == "episode_end"])]
        em, ev, _ = seria_e(tr)
        for a, z in win:
            idx = np.flatnonzero((em >= a) & (em <= z - 0.2))
            for j in idx[::5]:
                e2 = np.array([np.interp(em[j] + 0.2, em, ev[:, 0]), np.interp(em[j] + 0.2, em, ev[:, 1])])
                out.append(float(np.linalg.norm(e2 - ev[j])))
    return {"n": len(out), "p50": pct(out, .5), "p95": pct(out, .95), "max": round(max(out), 3) if out else None}


def main():
    raw = open(FREEZE, "rb").read()
    assert hashlib.sha256(raw).hexdigest() == FREEZE_SHA
    res = [boot(d) for d in sys.argv[1:]]
    allf = [f for r in res for f in r["r2"]["fixes"] if f["w_ep"] and not f["po_refuse"] and f["faza"] in MISJA]
    r2 = {"per_boot": {}, "koszyki": {}}
    for kand in ("uzyta", "jeden", "para"):
        for gn in ("z_GNSS", "bez_GNSS"):
            for lo, hi in S1A.RH_BINS:
                e = [f[kand] for f in allf if f[kand] is not None and lo <= f["rh"] < hi and f["bez_gnss"] == (gn == "bez_GNSS")]
                if e:
                    r2["koszyki"][f"{kand} {gn} {lo}-{hi}"] = {"n": len(e), "p50": pct(e, .5), "p95": pct(e, .95), "max": round(max(e), 3)}
    for r in res:
        fx = [f for f in r["r2"]["fixes"] if f["w_ep"] and not f["po_refuse"]]
        dz = [f for f in fx if f["dpsi"] is not None]
        def trend(xs):
            if len(xs) < 5:
                return None
            t = np.array([x["t"] for x in xs]); y = np.array([x["dpsi"] for x in xs])
            return round(float(np.polyfit(t - t[0], y, 1)[0]), 4)
        pre = [f for f in dz if not f["bez_gnss"]]; post = [f for f in dz if f["bez_gnss"]]
        r2["per_boot"][r["boot"]] = {
            "scenariusz": r["scenariusz"], "n_poprawek": len(fx), "n_para": sum(f["tryb"] == "para" for f in fx),
            "uzyta_p95": pct([f["uzyta"] for f in fx], .95), "uzyta_max": round(max((f["uzyta"] for f in fx), default=0), 3),
            "dpsi_z_GNSS": {"n": len(pre), "p50": pct([f["dpsi"] for f in pre], .5), "trend_deg_s": trend(pre)},
            "dpsi_bez_GNSS": {"n": len(post), "p50": pct([f["dpsi"] for f in post], .5), "trend_deg_s": trend(post)},
            "klatki_w_epizodzie": r["r2"]["klatki_w_epizodzie"], "klatki_z_poprawka": r["r2"]["klatki_z_poprawka"],
            "frac_klatek_z_poprawka": round(r["r2"]["klatki_z_poprawka"] / max(r["r2"]["klatki_w_epizodzie"], 1), 4),
            "detekcje": r["r2"]["detekcje_w_epizodzie"], "odrzucenia_powody": r["r2"]["odrzucenia_powody"]}
    r2["max_dla_freeze"] = {k: v["max"] for k, v in r2["koszyki"].items() if k.startswith("uzyta")}
    r2["obserwacje"] = {r["boot"]: r["r2"]["fixes"] for r in res}
    gs = gnss_szum()
    r3 = {r["boot"]: r["r3"] for r in res}
    r3["skala_szumu_GNSS_nominal_KONT_0.2s"] = gs
    json.dump({r["boot"]: dict(r["r1"], scenariusz=r["scenariusz"]) for r in res}, open(os.path.join(S2, "r1_okna.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(r2, open(os.path.join(S2, "r2_eps_fix.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(r3, open(os.path.join(S2, "r3_siec.json"), "w"), ensure_ascii=False, indent=1)
    json.dump({r["boot"]: dict(r["r4"], r5=r["r5"]) for r in res}, open(os.path.join(S2, "r4_pila.json"), "w"), ensure_ascii=False, indent=1)
    for r in res:
        print(r["boot"], r["scenariusz"], "R1 przekroczenia", r["r1"]["przekroczenia_w_wymogu"],
              {k: (v["n"], v["z_przekroczeniem"], v["max_inc_do_eps_b"]) for k, v in r["r1"]["okna"].items()},
              "| R4 u_max", r["r4"]["u_max"], "m", r["r4"]["m"], ">m", r["r4"]["ticki_u_gt_m"], "τ p95/max", r["r4"]["tau_p95"], r["r4"]["tau_max"],
              "| R5", r["r5"]["klasy"], "| R3", {k: r["r3"][k] for k in ("t_entry", "t_entry_kont_s4", "kontynuacja_s", "przyczyna_konca",
                                                                         "refuse_poza_bariera", "breach", "skoki_p_corr")}, flush=True)
    print("R2 koszyki", json.dumps({k: v for k, v in r2["koszyki"].items() if k.startswith("uzyta")}, ensure_ascii=False))
    print("szum GNSS", gs)


if __name__ == "__main__":
    main()
