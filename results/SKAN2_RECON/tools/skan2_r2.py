#!/usr/bin/env python3
"""results/SKAN2_RECON/tools/skan2_r2.py — R2 PROMPT_SKAN2_S0: uspokojenie yaw po skoku skanu + speckle MTI.

Dane: percep_feed.jsonl (own_q per klatka = poza, którą widziała percepcja) w fazie skanu: od t0 epizodu
do pierwszej fresh na celu (skan2_r1: fresh ∧ |trk−GT|_xy ≤ 3 m), GT intruza z manifestu w det_labels.BootGeo.
Rampa = ciągły odcinek |yaw_rate| ≥ 30°/s trwający ≥ 0.3 s (krok 40° przy 60°/s = 0.667 s; akw_scan.py:39-41).
T15_final = czas od t_e do (ostatnia klatka z |yaw_rate| ≥ 15°/s w [t_e, t_e+0.95] + 1 klatka; okno ucięte
przed rozpędem NASTĘPNEJ rampy, który w danych startuje ~1.0 s po t_e) — uspokojenie
OSTATECZNE (wahnięcie po przeregulowaniu liczone); 1.2 ⇒ nos nie uspokoił się w całym stare.
Per rampa: kąt [°], prędkość p50 w rampie [°/s] (czy 60°/s jest realizowane), koniec rampy t_e = ostatnia
klatka ≥ 30°/s; od t_e: czas do |yaw_rate| < 15°/s utrzymanego ≥ 3 klatki (T15); czas do dryfu < 5°/klatkę
(T5, próg p99 fresh TRANSIT r1); przeregulowanie = maks. wychylenie yaw poza położenie końcowe (mediana yaw
w [t_e+0.6, t_e+1.1] s) w kierunku obrotu [°]; frakcja okna stare 1.2 s z |yaw_rate| < 15°/s.
Speckle (R2/R5b): klatki w [t_e, t_e+1.2 s] z mti_ok ∧ (cel poza kadrem ∨ box nie na celu) — koincydencja
MTI na tle; fresh bez celu (fresh ∧ |trk−GT|_xy > 3 m) w tym oknie — fałszywa świeża.
Użycie: skan2_r2.py <out.json> <bootdir>,<warstwa> ...
"""
import json
import math
import os
import sys

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, os.path.join(ROOT, "results/SKAN2_RECON/tools"))
import skan2_r1 as K                                     # noqa: E402  (geometria, GT z manifestu)


def med(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2] if xs else None


def analyze(d):
    eps = [(r["scenario_id"], r["t0_sim"]) for r in K.iter_jsonl(os.path.join(d, "trace.jsonl"))
           if r.get("t") == "event" and r.get("ev") == "episode_start" and r.get("scenario_id")]
    demo = list(K.iter_jsonl(os.path.join(d, "demo.jsonl")))
    pf = sorted((r for r in K.iter_jsonl(os.path.join(d, "percep_feed.jsonl"))
                 if r.get("t_frame") is not None and r.get("own_q")), key=lambda r: r["t_frame"])
    geo = K.BootGeo(d, 1.0, 60.0)
    out = []
    for sid, t0 in eps:
        drows = [r for r in demo if r.get("scenario_id") == sid]
        if not drows:
            continue
        tend = drows[-1]["t_sim"]
        its, ips, t = [], [], 0.0
        while t <= tend - t0 + 1.0:
            x, y, z = K.S.position_at(K.MAN[sid], t)
            its.append(t0 + t); ips.append([x, y, -z]); t += 0.05
        geo.its, geo.ips = its, ips
        fr = [r for r in pf if t0 <= r["t_frame"] <= tend]
        rows = []
        for r in fr:
            i = max(0, min(len(ips) - 1, int(round((r["t_frame"] - t0) / 0.05))))
            g = ips[i]
            fresh_on = fresh_off = False
            if r.get("fresh") and r.get("trk_pos_ned"):
                dd = math.hypot(r["trk_pos_ned"][0] - g[0], r["trk_pos_ned"][1] - g[1])
                fresh_on, fresh_off = dd <= K.FRESH_GATE_M, dd > K.FRESH_GATE_M
            lab = geo.label(r["t_frame"])
            on = False
            b = r.get("box")
            if b and lab.get("flag") == "OK":
                on = abs(b[0] * 640 - lab["box"][0]) <= lab["box"][2] / 2 and abs(b[1] * 480 - lab["box"][1]) <= lab["box"][3] / 2
            rows.append({"t": r["t_frame"], "yaw": K.yaw_of(r["own_q"]), "fresh_on": fresh_on, "fresh_off": fresh_off,
                         "mti_bg": bool(r.get("mti_ok")) and not on, "tgt_fov": lab.get("flag") == "OK"})
        t_acq = next((x["t"] for x in rows if x["fresh_on"]), None)
        sc = [x for x in rows if t_acq is None or x["t"] < t_acq]
        if len(sc) < 5:
            out.append({"sid": sid, "rampy": [], "t_acq_rel": t_acq and round(t_acq - t0, 3)})
            continue
        # unwrap yaw
        uw = [sc[0]["yaw"]]
        for a, b2 in zip(sc, sc[1:]):
            uw.append(uw[-1] + K.wrap(b2["yaw"] - a["yaw"]))
        for x, y in zip(sc, uw):
            x["yu"] = y
        for i in range(1, len(sc)):
            dt = sc[i]["t"] - sc[i - 1]["t"]
            sc[i]["rate"] = (sc[i]["yu"] - sc[i - 1]["yu"]) / dt if dt > 0 else 0.0
            sc[i]["dpf"] = abs(sc[i]["yu"] - sc[i - 1]["yu"])
        sc[0]["rate"], sc[0]["dpf"] = 0.0, 0.0
        ramps, cur = [], None
        for i, x in enumerate(sc):
            if abs(x["rate"]) >= 30.0:
                cur = [i, i] if cur is None else [cur[0], i]
            elif cur is not None:
                ramps.append(cur); cur = None
        if cur is not None:
            ramps.append(cur)
        res = []
        for i0, i1 in ramps:
            if sc[i1]["t"] - sc[i0]["t"] < 0.3:
                continue
            te = sc[i1]["t"]
            sgn = 1.0 if sc[i1]["yu"] >= sc[i0 - 1 if i0 > 0 else i0]["yu"] else -1.0
            ang = abs(sc[i1]["yu"] - sc[max(0, i0 - 1)]["yu"])
            vr = med([abs(x["rate"]) for x in sc[i0:i1 + 1]])
            post = [x for x in sc[i1 + 1:] if x["t"] <= te + 2.0]
            t15 = t5 = None
            for j in range(len(post)):
                if t5 is None and post[j]["dpf"] < 5.0:
                    t5 = round(post[j]["t"] - te, 3)
                if t15 is None and all(abs(p["rate"]) < 15.0 for p in post[j:j + 3]) and len(post[j:j + 3]) == 3:
                    t15 = round(post[j]["t"] - te, 3)
            fin = [x["yu"] for x in post if te + 0.6 <= x["t"] <= te + 1.1]
            over = None
            if fin:
                yf = med(fin)
                over = round(max(0.0, max((x["yu"] - yf) * sgn for x in post if x["t"] <= te + 1.1)), 2)
            st = [x for x in post if x["t"] <= te + 1.2]
            loud = [x["t"] for x in st if abs(x["rate"]) >= 15.0 and x["t"] <= te + 0.95]
            t15f = round(loud[-1] - te + (st[1]["t"] - st[0]["t"] if len(st) > 1 else 0.068), 3) if loud else 0.0
            q = round(sum(1 for x in st if abs(x["rate"]) < 15.0) / len(st), 2) if st else None
            w12 = [x for x in sc if te <= x["t"] <= te + 1.2]
            res.append({"t_e_rel": round(te - t0, 3), "kat_deg": round(ang, 1), "v_rampy_p50": vr and round(vr, 1),
                        "T15_s": t15, "T15_final_s": t15f, "T5_s": t5, "przeregulowanie_deg": over, "frac_spokoj_w_1p2": q,
                        "n_kl_1p2": len(w12), "mti_tlo_1p2": sum(1 for x in w12 if x["mti_bg"]),
                        "mti_tlo_bez_celu_1p2": sum(1 for x in w12 if x["mti_bg"] and not x["tgt_fov"]),
                        "fresh_bez_celu_1p2": sum(1 for x in w12 if x["fresh_off"])})
        hz = 1.0 / med([b2["t"] - a["t"] for a, b2 in zip(sc, sc[1:])])
        out.append({"sid": sid, "hz": round(hz, 2), "t_acq_rel": t_acq and round(t_acq - t0, 3), "rampy": res})
    return out


def pctl(xs, q):
    xs = sorted(x for x in xs if x is not None)
    return round(xs[min(len(xs) - 1, int(-(-q * len(xs) // 1)) - 1)], 3) if xs else None


def main():
    res = {}
    for a in sys.argv[2:]:
        d, lab = a.split(",")
        res.setdefault(lab, {})[d] = analyze(os.path.join(ROOT, d))
    summ = {}
    for lab, boots in res.items():
        rs = [r for eps in boots.values() for e in eps for r in e["rampy"]]
        # tylko kroki skanu (kąt 30–50°) — odsiewa obroty sieci/odbicia
        rs = [r for r in rs if 30.0 <= r["kat_deg"] <= 55.0]
        nst = [r["T15_s"] for r in rs]
        summ[lab] = {"n_krokow": len(rs),
                     "kat_p50": pctl([r["kat_deg"] for r in rs], 0.5),
                     "v_rampy_p50": pctl([r["v_rampy_p50"] for r in rs], 0.5),
                     "T15_p50": pctl(nst, 0.5), "T15_p90": pctl(nst, 0.9), "T15_brak": sum(1 for x in nst if x is None),
                     "T15_final_p50": pctl([r["T15_final_s"] for r in rs], 0.5),
                     "T15_final_p90": pctl([r["T15_final_s"] for r in rs], 0.9),
                     "T15_final_ge_0p95": sum(1 for r in rs if r["T15_final_s"] >= 0.95),
                     "T5_p50": pctl([r["T5_s"] for r in rs], 0.5), "T5_p90": pctl([r["T5_s"] for r in rs], 0.9),
                     "przereg_p50": pctl([r["przeregulowanie_deg"] for r in rs], 0.5),
                     "przereg_p90": pctl([r["przeregulowanie_deg"] for r in rs], 0.9),
                     "frac_spokoj_1p2_p50": pctl([r["frac_spokoj_w_1p2"] for r in rs], 0.5),
                     "kl_1p2": sum(r["n_kl_1p2"] for r in rs),
                     "mti_tlo_1p2": sum(r["mti_tlo_1p2"] for r in rs),
                     "mti_tlo_bez_celu_1p2": sum(r["mti_tlo_bez_celu_1p2"] for r in rs),
                     "fresh_bez_celu_1p2": sum(r["fresh_bez_celu_1p2"] for r in rs)}
    json.dump({"warstwy": summ, "per_boot": res}, open(sys.argv[1], "w"), indent=1)
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
