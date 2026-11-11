#!/usr/bin/env python3
"""results/NAD2_RECON/tools/nad2_dane.py — wspólne wczytanie danych bootu NADIR S4/S2 dla reconu NAD2 (PROMPT_NAD2_S0; 0 bootów).

Źródła (READ-ONLY): <boot>/trace.jsonl (gt, event, tk), <boot>/rama.jsonl (tick misji: p_ekf, p_corr, τ, kosz, faza),
<boot>/nadir_obs.jsonl (wiersze nf: detekcje, migawka EKF przy przybyciu klatki, fx), wyciąg ULG results/NAD2_RECON/ulg/<boot>.jsonl.gz
(nad2_wyciag_ulg.py). Czas: sim [s]; ULG µs/1e6 = sim (SITL lockstep; potwierdzone dopasowaniem wartości w R1).
GT: wiersze gt trace (gz ENU, x=E, y=N, z=up) → NED: N = y, E = x, D = −z (jak nadir_s4_analyze.e3_series), interpolacja liniowa
po polu sim. Okna: misja = faza ∈ {approach, hold, orbit} przed zejściem planowym (jak analizator); bez GNSS = od flagi
cs_gnss_pos → 0 (ULG) po denial; z GNSS = misja przed flagą (cięcia); nominały = misja.
"""
import bisect
import gzip
import json
import math
import os

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
OUT = os.path.join(ROOT, "results/NAD2_RECON")
ULG = os.path.join(OUT, "ulg")
S4 = os.path.join(ROOT, "results/NADIR/s4")
S2 = os.path.join(ROOT, "results/NADIR/s2")
CIECIA_S4 = ["c01_s01_r4", "c01_s03", "c02_s01", "c02_s03", "c05_s01", "c05_s02", "c08_s01", "c08_s02", "c10_s01", "c10_s02",
             "c11_s01", "c11_s02"]
NOM_S4 = ["nom_b1_r2", "nom_b2", "nom_b3", "nom_b4"]
CIECIA_S2 = ["c02_s01", "c05_s01_r2", "c08_s02", "c11_s02_r2"]          # 4 ważne cięcia S2 (STOP_NADIR2), próba spoza FREEZE
MISJA = ("approach", "hold", "orbit")
MARG = json.load(open(os.path.join(ROOT, "results/KONT_RECON/r4_margin.json")))["tabela_scenariuszy"]


def pct(x, q):
    x = np.asarray(x, float)
    return None if x.size == 0 else round(float(np.quantile(x, q)), 4)


def rozklad(x):
    x = np.asarray(x, float)
    if x.size == 0:
        return {"n": 0}
    return {"n": int(x.size), "p50": pct(x, .5), "p95": pct(x, .95), "p99": pct(x, .99), "max": round(float(x.max()), 4),
            "min": round(float(x.min()), 4), "srednia": round(float(x.mean()), 4)}


def jl(p, typ=None):
    out = []
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


def czytaj_ulg(boot):
    out = {}
    with gzip.open(os.path.join(ULG, f"{boot}.jsonl.gz"), "rt") as f:
        for l in f:
            r = json.loads(l)
            out[r["temat"]] = r if r["temat"] == "_meta" else {k: np.array(v) for k, v in r["dane"].items()}
    return out


class Boot:
    def __init__(self, boot, katalog=S4):
        self.boot = boot
        self.d = os.path.join(katalog, boot)
        tr = jl(os.path.join(self.d, "trace.jsonl"))
        self.ev = [r for r in tr if r.get("t") == "event"]
        gt = sorted([r for r in tr if r.get("t") == "gt"], key=lambda r: r["sim"])
        self.gt_t = np.array([r["sim"] for r in gt])
        self.gt_ned = np.array([[r["y"], r["x"], -r["z"]] for r in gt])
        self.rama = jl(os.path.join(self.d, "rama.jsonl"))
        self.nf = [r for r in jl(os.path.join(self.d, "nadir_obs.jsonl"), "nf") if "fx" in r]
        ul = boot if katalog == S4 else f"s2_{boot}"
        self.u = czytaj_ulg(ul) if os.path.exists(os.path.join(ULG, f"{ul}.jsonl.gz")) else None
        e1 = lambda n: next((e for e in self.ev if e.get("ev") == n), None)
        self.denial = e1("denial")
        self.t_inj = self.denial["t_inj_sim"] if self.denial else None
        self.zp = {e["episode_id"]: e["sim"] for e in self.ev if e.get("ev") == "zejscie_planowe"}
        self.t_flag = None
        if self.denial is not None and self.u is not None:
            fl = self.u["estimator_status_flags"]
            for t, v in zip(fl["timestamp"], fl["cs_gnss_pos"]):
                if v == 0 and t >= self.denial["sim"] - 0.5:
                    self.t_flag = float(t)
                    break
        self.scen = {e["episode_id"]: e["scenario_id"] for e in self.ev if e.get("ev") == "episode_start"}
        if self.u is not None:
            v = self.u["vehicle_local_position"]
            self.vt, self.vts = v["timestamp"], v["timestamp_sample"]
            self.vp = np.stack([v["x"], v["y"], v["z"]], 1)
            self.vv = np.stack([v["vx"], v["vy"], v["vz"]], 1)
            a = self.u["vehicle_attitude"]
            self.at, self.ats = a["timestamp"], a["timestamp_sample"]
            self.aq = np.stack([a["q[0]"], a["q[1]"], a["q[2]"], a["q[3]"]], 1)

    def gt(self, t):
        t = np.atleast_1d(np.asarray(t, float))
        return np.stack([np.interp(t, self.gt_t, self.gt_ned[:, i]) for i in range(3)], 1)

    def gt_v(self, t, h=0.05):
        return (self.gt(np.asarray(t) + h) - self.gt(np.asarray(t) - h)) / (2 * h)

    def klasa(self, sim):
        if self.t_flag is not None and sim >= self.t_flag:
            return "bez_GNSS"
        return "z_GNSS" if self.denial is not None else "nominal"

    def misja(self, r):
        ep = r.get("ep")
        return r.get("phase") in MISJA and not r.get("desc") and (ep not in self.zp or r["sim"] < self.zp[ep])

    def dopasuj(self, p, t_ref, okno=(-0.4, 0.1)):
        """Indeks próbki vehicle_local_position o wartości p (NED, 4 cyfry) w oknie czasu [t_ref+okno]: min |Δp|."""
        i0 = bisect.bisect_left(self.vt, t_ref + okno[0])
        i1 = bisect.bisect_right(self.vt, t_ref + okno[1])
        if i1 <= i0:
            return None, None
        d = np.linalg.norm(self.vp[i0:i1] - np.asarray(p, float), axis=1)
        k = int(np.argmin(d))
        return i0 + k, float(d[k])

    def dopasuj_q(self, q, t_ref, okno=(-0.4, 0.1)):
        i0 = bisect.bisect_left(self.at, t_ref + okno[0])
        i1 = bisect.bisect_right(self.at, t_ref + okno[1])
        if i1 <= i0:
            return None, None
        qq = self.aq[i0:i1]
        d = np.minimum(np.linalg.norm(qq - np.asarray(q, float), axis=1), np.linalg.norm(qq + np.asarray(q, float), axis=1))
        k = int(np.argmin(d))
        return i0 + k, float(d[k])

    def ekf_w(self, t):
        """Pozycja EKF (NED) interpolowana na czas próbki t (oś timestamp_sample)."""
        return np.stack([np.interp(t, self.vts, self.vp[:, i]) for i in range(3)], -1)

    def q_w(self, t):
        """Postawa EKF w czasie t (oś timestamp_sample), najbliższa próbka (q nie interpolowane liniowo)."""
        i = int(np.clip(np.searchsorted(self.ats, t), 0, len(self.ats) - 1))
        if i > 0 and abs(self.ats[i - 1] - t) < abs(self.ats[i] - t):
            i -= 1
        return [float(x) for x in self.aq[i]], float(self.ats[i])


def rpy(q):
    w, x, y, z = q
    roll = math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
    pitch = math.asin(max(-1.0, min(1.0, 2 * (w * y - z * x))))
    yaw = math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
    return roll, pitch, yaw
