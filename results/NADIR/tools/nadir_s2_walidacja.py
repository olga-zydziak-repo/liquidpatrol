#!/usr/bin/env python3
"""results/NADIR/tools/nadir_s2_walidacja.py — PROMPT_NADIR_S2 §1.5: walidacja sucha przed lotami (0 bootów), replay logów.

(A) Passthrough NADIR_MODE=0, rdzeń feedu: harness/feed_vision.py z HEAD (9f7cdd74, przed zmianą) vs bieżący przy
    NADIR_MODE=0 — ten sam strumień wejść z percep_feed.jsonl (push_own(own_pos, own_q) + ingest_box(box, mti_ok)) z bootów
    NADIR S1 v2 i KONT S4; porównanie per wiersz: zdarzenie, wiersz logu rdzenia (bez pola "wall" = zegar ścienny), sample(t),
    oraz feed_sha. Wymóg: 0 różnic. Ten sam replay przy NADIR_MODE=1 = podgląd bramki predykcji (odrzucenia z klasą: track
    na intruzie / track zastany) — opisowo.
(B) NADIR_MODE=1, tożsamość setpointu: producent harness/nadir_fix.Rama na wierszach nf z nadir_obs.jsonl S1 v2 (det, migawka
    EKF), datagramy przez prawdziwe gniazdo UDS do RamaKlient; strumień ticków = wiersze ekf z trace.jsonl (po mono), sp_net
    syntetyczny (p_corr + 7 m pod kątem tick·0.1 rad); wymóg: max |(sp_EKF − sp_net) − (p_EKF − p_corr)| ≤ 1e−9.
(C) |p_corr − GT| na logach S1: (i) per przyjęta poprawka |p_fix − GT(t_klatki)| poziomo (GT interpolowane po sim, jak
    nadir_s1v2_analyze), koszyki r_h (r_h z GT do znacznika „najbliższego” poprawki), tryb jeden/para osobno; wymóg: tryb jeden
    = wzór S1 „ekf” (nadir_s1v2_analyze.fix1, ta sama klatka i znacznik) co do 1e−4 m (zaokrąglenie logu), para: p95 ≤ p95 S1
    para w koszyku (n1/r3_poprawka.json). Errata przed lotami: pierwsza wersja wymagała p95 trybu jeden ≤ p95 S1 „ekf”
    w koszyku — źle postawione (poprawki trybu jeden to podzbiór obserwacji S1, klatki z jednym przyjętym znacznikiem; koszyk
    0–2: 36 ze 160, p95 0.209 vs 0.201 przy błędach identycznych wartość w wartość) — zostaje opisowo pod "per_koszyk";
    (ii) |p_corr − GT| per tick EKF w fazach misji (GT po mono, jak gt_judge), wymóg: p95 ≤ p95 S1 tryb 1 „ekf” łącznie
    (1.04 m) — litera §1.5.
FAIL dowolnego ⇒ STOP przed lotami. Wyjście: results/NADIR/s2/walidacja_sucha.json.
"""
import bisect
import importlib.util
import json
import math
import os
import subprocess
import sys
import tempfile

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/NADIR/tools")]
import nadir_s1v2_analyze as A                               # READ-ONLY: GT, fazy, faza_at, load, RH_BINS, pct
from harness import nadir_fix as NF
from r02.target_channel import Box

OUT = os.path.join(ROOT, "results/NADIR/s2/walidacja_sucha.json")
S1V2 = [os.path.join(ROOT, "results/NADIR/s1", b) for b in ("b2v2_c08", "b3v2_c05c11")]
BASE = "9f7cdd74"


def load_fv(path, name, mode):
    if mode is None:
        os.environ.pop("NADIR_MODE", None)
    else:
        os.environ["NADIR_MODE"] = mode
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    os.environ.pop("NADIR_MODE", None)
    return m


class Cap:
    def __init__(self):
        self.rows = []

    def write(self, s):
        r = json.loads(s)
        r.pop("wall", None)
        self.rows.append(r)

    def flush(self):
        pass

    def close(self):
        pass


def replay_feed(mod, rows):
    fv = mod.FeedVision(detector=None, log_path=None)
    cap = Cap()
    fv._log = cap
    evs, samples = [], []
    for r in rows:
        if r.get("own_pos_ned") is not None:
            fv.push_own(r["t_frame"], r["own_pos_ned"], r["own_q"])
        b = r["box"]
        box = Box(b[0], b[1], b[2], b[3], r["conf"]) if b else None
        evs.append(fv.ingest_box(r["t_frame"], box, r["mti_ok"]))
        samples.append(fv.sample(r["t_frame"]))
    return fv, evs, samples, cap.rows


def czesc_a(dirs):
    orig = os.path.join(tempfile.mkdtemp(), "feed_vision_base.py")
    open(orig, "w").write(subprocess.check_output(["git", "show", f"{BASE}:harness/feed_vision.py"], cwd=ROOT).decode())
    cur = os.path.join(ROOT, "harness/feed_vision.py")
    m0 = load_fv(orig, "fv_base", None)
    m1 = load_fv(cur, "fv_mode0", None)
    m2 = load_fv(cur, "fv_mode1", "1")
    assert not m1.NADIR_MODE and m2.NADIR_MODE
    res = {"baza": f"{BASE}:harness/feed_vision.py", "boots": {}, "roznice_mode0": 0, "wiersze": 0}
    for d in dirs:
        rows = [r for r in A.load(os.path.join(d, "percep_feed.jsonl")) if "t_frame" in r]
        f0, e0, s0, l0 = replay_feed(m0, rows)
        f1, e1, s1, l1 = replay_feed(m1, rows)
        n_diff = sum(1 for i in range(len(rows)) if e0[i] != e1[i] or s0[i] != s1[i] or l0[i] != l1[i])
        n_diff += int(f0.feed_sha != f1.feed_sha)
        f2, e2, s2, l2 = replay_feed(m2, rows)
        intr = sorted(A.load(os.path.join(d, "gt_intruder.jsonl")), key=lambda r: r["t_sim"])
        it = [r["t_sim"] for r in intr]

        def d_intr(t, p):
            j = min(bisect.bisect_left(it, t), len(intr) - 1) if intr else None
            return math.dist(p, intr[j]["ned"]) if intr and abs(intr[j]["t_sim"] - t) <= 0.1 else None
        odrz = []
        for i, lr in enumerate(l2):
            o = lr.get("pred_odrzut")
            if o:
                dc, dp = d_intr(lr["t_frame"], o["cand"]), d_intr(lr["t_frame"], o["pred"])
                klasa = ("box_nie_na_intruzie" if dc is None or dc > 3 else
                         "intruz_przy_tracku_na_intruzie" if dp is not None and dp <= 3 else "intruz_przy_tracku_zastanym")
                odrz.append({"t": lr["t_frame"], "d": o["d"], "prog": o["prog"], "d_cand_intruz": None if dc is None else round(dc, 2),
                             "d_pred_intruz": None if dp is None else round(dp, 2), "klasa": klasa})
        kl = {}
        for o in odrz:
            kl[o["klasa"]] = kl.get(o["klasa"], 0) + 1
        res["boots"][os.path.relpath(d, ROOT)] = {
            "wiersze": len(rows), "roznice_mode0": n_diff, "feed_sha_base": f0.feed_sha[:16], "feed_sha_mode0": f1.feed_sha[:16],
            "mode1": {"n_pred_odrzut": f2.n_pred_odrzut, "klasy": kl, "fresh_mode0": f1.n_fresh, "fresh_mode1": f2.n_fresh,
                      "entry_mode0": sum(e == "ENTRY" for e in e1), "entry_mode1": sum(e == "ENTRY" for e in e2),
                      "przyklady": odrz[:6]}}
        res["roznice_mode0"] += n_diff
        res["wiersze"] += len(rows)
        print("A", os.path.basename(d), len(rows), "różnic", n_diff, "odrzuceń m1", f2.n_pred_odrzut, kl, flush=True)
    res["PASS"] = res["roznice_mode0"] == 0
    return res


def czesc_bc(dirs):
    r3 = json.load(open(os.path.join(ROOT, "results/NADIR/s1/n1/r3_poprawka.json")))
    s1_jeden = {k: v["p95"] for k, v in r3["tryb1"]["ekf"].items()}
    s1_para = {k: v["p95"] for k, v in r3["para"]["ekf"].items()}
    s1_lacz = r3["laczne"]["ekf"]["p95"]
    zn = {z["id"]: z for z in json.load(open(NF.MANIFEST))["znaczniki"]}
    fix_recs, pc_err, sp_dev, tau_all = [], [], 0.0, []
    for d in dirs:
        prod = NF.Rama()
        sp = os.path.join(tempfile.mkdtemp(), "rama.sock")
        kl = NF.RamaKlient(sp)
        send = NF.nadawca([sp])
        gt = A.GT(os.path.join(d, "trace.jsonl"))
        rows, rt, _ = A.fazy(os.path.join(d, "demo.jsonl"))
        nf = sorted(A.load(os.path.join(d, "nadir_obs.jsonl"), "nf"), key=lambda r: r["mono"])
        tr = A.load(os.path.join(d, "trace.jsonl"))
        ekf = sorted([r for r in tr if r.get("t") == "ekf"], key=lambda r: r["mono"])
        g = sorted([r for r in tr if r.get("t") == "gt" and "sim" in r], key=lambda r: r["mono"])
        gm = np.array([r["mono"] for r in g]); gs = np.array([r["sim"] for r in g])
        gx = np.array([r["x"] for r in g]); gy = np.array([r["y"] for r in g])
        j = 0
        for k, e in enumerate(ekf):
            while j < len(nf) and nf[j]["mono"] <= e["mono"]:
                fr = nf[j]; j += 1
                fx = prod.obserwacja(fr["sim"], fr["det"], fr.get("ekf_q"), fr.get("ekf_pos"))
                send(fx)
                if fx["ok"]:
                    gg = gt.at(fr["sim"])
                    if gg is not None:
                        p0, q = gg
                        cam = p0 + A.rotm(q) @ NF.MOUNT
                        ph, _ = A.faza_at(rows, rt, fr["sim"])
                        idn = fx["jeden"]["id"] if fx["tryb"] == "jeden" else fx["para"]["ids"][0]
                        rh = math.hypot(zn[idn]["E"] - cam[0], zn[idn]["N"] - cam[1])
                        err = math.hypot(fx["p_fix_ne"][1] - p0[0], fx["p_fix_ne"][0] - p0[1])
                        s1v = None
                        if fx["tryb"] == "jeden":                     # wzór S1 'ekf' 1:1 na tej samej obserwacji
                            m = next(x for x in fr["det"] if x["id"] == idn)
                            Re = A.ekf_R(fr["ekf_q"]); z_e = -fr["ekf_pos"][2] + (Re @ A.MOUNT)[2]
                            s1v = float(np.linalg.norm(A.fix1(Re, z_e, m["uv"][0], m["uv"][1], A.ZN[idn])
                                                       - (Re @ A.MOUNT)[:2] - p0[:2]))
                        fix_recs.append({"tryb": fx["tryb"], "rh": rh, "err": err, "faza": ph, "s1": s1v})
            kl.drain(); kl.odbierz_nowe()
            p_ekf = [e["x"], e["y"], e["z"]]
            pc = kl.p_corr(p_ekf)
            a = k * 0.1
            sp_net = [pc[0] + 7 * math.cos(a), pc[1] + 7 * math.sin(a), pc[2]]
            sp_e = NF.sp_ekf(sp_net, p_ekf, pc)
            sp_dev = max(sp_dev, max(abs((sp_e[i] - sp_net[i]) - (p_ekf[i] - pc[i])) for i in range(3)))
            if not (gm[0] <= e["mono"] <= gm[-1]):
                continue
            sim = float(np.interp(e["mono"], gm, gs))
            ph, _ = A.faza_at(rows, rt, sim)
            if ph in ("approach", "hold", "orbit"):
                gn, ge = float(np.interp(e["mono"], gm, gy)), float(np.interp(e["mono"], gm, gx))
                pc_err.append(math.hypot(pc[0] - gn, pc[1] - ge))
                if kl.t_fix is not None:
                    tau_all.append(sim - kl.t_fix)
        kl.close()
    out = {"B_sp_max_odchylka": sp_dev, "B_PASS": sp_dev <= 1e-9}
    mis = [r for r in fix_recs if r["faza"] in ("approach", "hold", "orbit")]
    kos, ok = {}, True
    for tryb, ref in (("jeden", s1_jeden), ("para", s1_para)):
        for lo, hi in A.RH_BINS:
            e = [r["err"] for r in mis if r["tryb"] == tryb and lo <= r["rh"] < hi]
            key = f"{lo}-{hi}"
            if not e:
                continue
            p95 = A.pct(e, .95)
            okb = ref.get(key) is None or p95 <= ref[key]
            if tryb == "para":
                ok &= okb
            kos[f"{tryb} {key}"] = {"n": len(e), "p50": A.pct(e, .5), "p95": p95, "s1_p95": ref.get(key), "p95_le_s1": okb}
    jd = [abs(r["err"] - r["s1"]) for r in mis if r["tryb"] == "jeden"]
    tozs = max(jd) if jd else 0.0
    ok &= tozs <= 1e-4
    out["C_poprawki"] = {"n": len(mis), "n_para": sum(r["tryb"] == "para" for r in mis),
                         "jeden_max_odchylka_od_wzoru_S1_m": tozs, "jeden_n": len(jd), "per_koszyk": kos,
                         "nota": "per_koszyk dla trybu jeden opisowo (podzbiór obserwacji S1) — errata przed lotami, docstring",
                         "PASS": ok}
    p95 = A.pct(pc_err, .95)
    out["C_p_corr"] = {"n_tickow": len(pc_err), "p50": A.pct(pc_err, .5), "p95": p95, "max": round(max(pc_err), 3),
                       "s1_tryb1_ekf_p95": s1_lacz, "PASS": p95 <= s1_lacz,
                       "tau_p95": A.pct(tau_all, .95), "tau_max": round(max(tau_all), 3) if tau_all else None}
    return out


def main():
    dirs_a = S1V2 + [os.path.join(ROOT, "results/KONT/s4", b) for b in ("c08_s02", "c11_s02", "c05_s01", "c02_s01")]
    res = {"opis": __doc__.split("\n\n")[0], "A_passthrough_feed": czesc_a(dirs_a)}
    res.update(czesc_bc(S1V2))
    res["PASS"] = res["A_passthrough_feed"]["PASS"] and res["B_PASS"] and res["C_poprawki"]["PASS"] and res["C_p_corr"]["PASS"]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(res, open(OUT, "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "A_passthrough_feed"}, ensure_ascii=False, indent=1))
    print("A PASS", res["A_passthrough_feed"]["PASS"], "| CAŁOŚĆ", "PASS" if res["PASS"] else "FAIL")
    sys.exit(0 if res["PASS"] else 1)


if __name__ == "__main__":
    main()
