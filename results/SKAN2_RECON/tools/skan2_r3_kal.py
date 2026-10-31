#!/usr/bin/env python3
"""results/SKAN2_RECON/tools/skan2_r3_kal.py — R3: kalibracja modelu B (obrót do azymutu + latencja) na profilu
FROZEN (krok 40°, slew 60°/s, stare 1.2 s, dwell 2.0 s; akw_scan.py:38-42) wobec zmierzonej akwizycji.

Epizody z azymutem celu STAŁYM w fazie skanu: komórki v=0 (c00–c03) oraz v=1.0 radialne (c08–c11; kurs
prosto na home, bench/scenarios.py:52-54), z warstw a (PERC2 S2) i a2 (WK/WK2/WK3). Kąt do pokrycia
θ = (bearing − 43.45°) mod 360 (skan CCW = yaw rosnący, akw_scan.py:12-13, start ψ=0 po kwarantannie).
Przewidywanie: t_pred = dwell + T_rot(θ) (+0 dla θ ≤ 0: cel w stożku od startu). Obserwacja: t_fresh_on
(skan2_r1). Offset = obs − pred. Wyłączone: epizody z dh < 5 m w chwili t_pred (strefa martwa) i ucięte.
Wyjście: r3_kalibracja.json + wydruk.
"""
import json, math, os, sys
sys.path.insert(0, "/home/olga/projects/liquidpatrol/results/SKAN2_RECON/tools")
import skan2_r1 as K
import skan2_r3 as R

d = json.load(open(os.path.join(R.OUT, "r1_zdarzenia_any.json")))
bw = ("wk0_b1", "wk0_b2", "g0_b1", "g0_b2")
rows = []
for pop in ("a", "a2"):
    for b, eps in d[pop].items():
        for ep in eps:
            sc = K.MAN[ep["sid"]]
            v, brg = sc["cell"]["v_intr"], sc["cell"]["bearing_deg"]
            if v not in (0.0, 1.0) or ep["t_fresh_on_rel"] is None:
                continue
            th = (brg - R.HALF) % 360.0
            if brg == 0:
                th = 0.0
            pred = 2.0 + (R.t_rot(th, 40.0, 1.2) if th > 0 else 0.0)
            x, y, _ = K.S.position_at(sc, pred)
            dh = math.hypot(x, y)
            rows.append({"warstwa": "a" if pop == "a" else ("a2_bez_wiatru" if os.path.basename(b) in bw else "a2_wiatr"),
                         "boot": os.path.basename(b), "sid": ep["sid"], "v": v, "bearing": brg,
                         "t_pred": round(pred, 2), "t_obs": ep["t_fresh_on_rel"], "dh_przy_pred": round(dh, 1),
                         "offset": round(ep["t_fresh_on_rel"] - pred, 2)})
ok = [r for r in rows if r["dh_przy_pred"] >= 5.0 and r["bearing"] != 0]
def p(xs, q):
    xs = sorted(xs); return xs[math.ceil(q * len(xs)) - 1] if xs else None
summ = {w: {"n": len([r for r in ok if r["warstwa"] == w]),
            "offset_p50": p([r["offset"] for r in ok if r["warstwa"] == w], 0.5),
            "offset_p90": p([r["offset"] for r in ok if r["warstwa"] == w], 0.9),
            "offset_max": max([r["offset"] for r in ok if r["warstwa"] == w], default=None)}
        for w in ("a", "a2_bez_wiatru", "a2_wiatr")}
bwall = [r["offset"] for r in ok if r["warstwa"] in ("a", "a2_bez_wiatru")]
summ["a+a2bw"] = {"n": len(bwall), "offset_p50": p(bwall, 0.5), "offset_p90": p(bwall, 0.9), "offset_max": max(bwall)}
json.dump({"wiersze": rows, "warstwy": summ}, open(os.path.join(R.OUT, "r3_kalibracja.json"), "w"), indent=1)
for r in rows: print(r)
print(json.dumps(summ, indent=1))
