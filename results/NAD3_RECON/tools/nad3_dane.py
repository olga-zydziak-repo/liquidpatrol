#!/usr/bin/env python3
"""results/NAD3_RECON/tools/nad3_dane.py — wczytanie 13 lotów NAD2 dla reconu NADIR-III (PROMPT_NAD3_S0 §2; 0 bootów).

Loty: 12 cięć bramki S3 (results/NAD2/s3/<boot>, boot ważny z STOP_NAD2_3) i lot długi results/NAD2/s4/L_c10_s01 (pliki .gz).
Źródła (READ-ONLY): trace.jsonl (gt, event), rama.jsonl (tick: p_ekf, p_corr, d_ne, seq, ph, nad2, nadir, obs = datagramy, które
dotarły do drivera w tym ticku), nadir_obs.jsonl (wiersze nf: detekcje, migawka EKF, fx = datagram producenta z d_ne i t_fix),
ulg.jsonl.gz (wyciąg ULG w katalogu bootu). Czas: sim [s] = ULG µs / 1e6 (SITL lockstep).
Kanon jak results/NAD2/tools/nad2_analyze.py: GT trace (ENU x=E, y=N, z=up) → NED; e_corr = |p_corr − GT(t_s)| poziomo, t_s =
timestamp_sample próbki vehicle_local_position dopasowanej PO WARTOŚCI do p_ekf ticku w oknie [sim − 0.4, sim + 0.1] s;
utrata = ph ∈ {KONT, KONT_REFUSE}; misja = phase ∈ {approach, hold, orbit} ∧ ¬desc ∧ sim < zejście planowe.
Pamięć podręczna (npz/pickle) w scratchpadzie sesji albo $NAD3_CACHE — nie w repo.
"""
import bisect
import gzip
import json
import math
import os
import pickle

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
OUT = os.path.join(ROOT, "results/NAD3_RECON")
S3 = os.path.join(ROOT, "results/NAD2/s3")
S4 = os.path.join(ROOT, "results/NAD2/s4")
CIECIA = {"c01_s01": "c01_s01", "c01_s03": "c01_s03_r2", "c02_s01": "c02_s01", "c02_s03": "c02_s03",
          "c05_s01": "c05_s01_r2", "c05_s02": "c05_s02", "c08_s01": "c08_s01", "c08_s02": "c08_s02", "c10_s01": "c10_s01",
          "c10_s02": "c10_s02", "c11_s01": "c11_s01", "c11_s02": "c11_s02"}            # komórka → boot ważny (STOP_NAD2_3)
LOT_DLUGI = ("L_c10_s01", os.path.join(S4, "L_c10_s01"))
MISJA = ("approach", "hold", "orbit")
UTRATA = ("KONT", "KONT_REFUSE")
CACHE = os.environ.get("NAD3_CACHE", "/tmp/claude-1000/-home-olga-projects-liquidpatrol/8ae8f6cb-345f-452f-9041-28f95502f571/"
                                     "scratchpad/nad3_cache")


def loty():
    """[(nazwa, katalog, komórka)] — 12 cięć, potem lot długi."""
    out = [(b, os.path.join(S3, b), c) for c, b in CIECIA.items()]
    return out + [(LOT_DLUGI[0], LOT_DLUGI[1], "c10_s01")]


def otworz(d, nazwa):
    p = os.path.join(d, nazwa)
    if os.path.exists(p):
        return open(p)
    return gzip.open(p + ".gz", "rt")


def jl(d, nazwa, typ=None):
    out = []
    with otworz(d, nazwa) as f:
        for l in f:
            if typ is not None and f'"{typ}"' not in l:
                continue
            try:
                r = json.loads(l)
            except ValueError:
                continue
            if typ is None or r.get("t") == typ:
                out.append(r)
    return out


def czytaj_ulg(d):
    out = {}
    with gzip.open(os.path.join(d, "ulg.jsonl.gz"), "rt") as f:
        for l in f:
            r = json.loads(l)
            out[r["temat"]] = r if r["temat"] == "_meta" else {k: np.array(v) for k, v in r["dane"].items()}
    return out


def pct(x, q):
    x = np.asarray(x, float)
    return None if x.size == 0 else round(float(np.quantile(x, q)), 4)


def rozklad(x):
    x = np.asarray(x, float)
    if x.size == 0:
        return {"n": 0}
    return {"n": int(x.size), "p50": pct(x, .5), "p95": pct(x, .95), "p99": pct(x, .99), "max": round(float(x.max()), 4)}


class Lot:
    """Jeden lot NAD2: ticki (wszystkie i utraty), strumień datagramów fx po seq, GT, EKF."""

    def __init__(self, nazwa, d, kom):
        self.nazwa, self.d, self.kom = nazwa, d, kom
        tr = jl(d, "trace.jsonl")
        self.ev = [r for r in tr if r.get("t") == "event"]
        gt = sorted([r for r in tr if r.get("t") == "gt"], key=lambda r: r["sim"])
        self.gt_t = np.array([r["sim"] for r in gt])
        self.gt_ned = np.array([[r["y"], r["x"], -r["z"]] for r in gt])
        armed = self.e1("armed")
        self.gt_home = armed["gt_home"] if armed else [0.0, 0.0]
        self.gt_xy = np.array([[r["x"], r["y"]] for r in gt])
        self.rama = sorted(jl(d, "rama.jsonl"), key=lambda r: r["tick"])
        self.nf = [r for r in jl(d, "nadir_obs.jsonl", "nf") if "fx" in r]
        self.fx = {r["fx"]["seq"]: r["fx"] for r in self.nf}
        self.u = czytaj_ulg(d)
        v = self.u["vehicle_local_position"]
        self.vt, self.vts = v["timestamp"], v["timestamp_sample"]
        self.vp = np.stack([v["x"], v["y"], v["z"]], 1)
        self.denial = self.e1("denial")
        self.t_inj = self.denial["t_inj_sim"] if self.denial else None
        self.ep_cut = self.denial["episode_id"] if self.denial else None
        self.zp = {e["episode_id"]: e["sim"] for e in self.ev if e.get("ev") == "zejscie_planowe"}
        self.t_zp = self.zp.get(self.ep_cut)
        land = self.e1("gt_przyziemienie")
        self.t_land = land["sim"] if land else None
        self.t_flag = None
        fl = self.u["estimator_status_flags"]
        for t, val in zip(fl["timestamp"], fl["cs_gnss_pos"]):
            if self.denial is not None and val == 0 and t >= self.denial["sim"] - 0.5:
                self.t_flag = float(t)
                break
        self.scen = {e["episode_id"]: e["scenario_id"] for e in self.ev if e.get("ev") == "episode_start"}

    def e1(self, n):
        return next((e for e in self.ev if e.get("ev") == n), None)

    def gt(self, t):
        t = np.atleast_1d(np.asarray(t, float))
        return np.stack([np.interp(t, self.gt_t, self.gt_ned[:, i]) for i in range(3)], 1)

    def r_gt(self, t):
        """Promień GT od home (jak B2 analizatora: gz x, y minus gt_home)."""
        t = np.atleast_1d(np.asarray(t, float))
        x = np.interp(t, self.gt_t, self.gt_xy[:, 0]) - self.gt_home[0]
        y = np.interp(t, self.gt_t, self.gt_xy[:, 1]) - self.gt_home[1]
        return np.hypot(x, y)

    def t_probki(self, p, t_ref, okno=(-0.4, 0.1)):
        i0, i1 = bisect.bisect_left(self.vt, t_ref + okno[0]), bisect.bisect_right(self.vt, t_ref + okno[1])
        if i1 <= i0:
            return None
        dd = np.linalg.norm(self.vp[i0:i1] - np.asarray(p, float), axis=1)
        return float(self.vts[i0 + int(np.argmin(dd))])

    def ekf_w(self, t):
        return np.stack([np.interp(t, self.vts, self.vp[:, i]) for i in range(3)], -1)

    def misja(self, r):
        return r.get("phase") in MISJA and not r.get("desc") and (self.t_zp is None or r["sim"] < self.t_zp)


def ticki_utraty(L):
    """Tablice ticków utraty epizodu cięcia (ph ∈ UTRATA i pola nad2), z t_s i GT(t_s) — wejście replayu R4/R5."""
    rr = [r for r in L.rama if r["ep"] == L.ep_cut and r.get("ph") in UTRATA and r.get("nad2") is not None]
    sim = np.array([r["sim"] for r in rr])
    pe = np.array([r["p_ekf"] for r in rr])
    pc = np.array([r["p_corr"] for r in rr])
    seq = np.array([r["seq"] for r in rr])
    ts = np.array([np.nan if (x := L.t_probki(r["p_ekf"], r["sim"])) is None else x for r in rr])
    g = L.gt(np.nan_to_num(ts, nan=0.0))
    return {"sim": sim, "p_ekf": pe, "p_corr": pc, "seq": seq, "t_s": ts, "gt": g,
            "misja": np.array([L.misja(r) for r in rr]), "r_gt": L.r_gt(sim),
            "ph": [r["ph"] for r in rr], "przedzial": [r["nad2"].get("przedzial") for r in rr],
            "tryb": [r["nad2"].get("tryb") for r in rr], "j": [(r.get("nadir") or {}).get("j") for r in rr],
            "tau": [(r.get("nadir") or {}).get("tau") for r in rr], "r_est": np.array([r["nad2"]["r_est"] for r in rr]),
            "R_k": [r.get("R_k") for r in rr], "t_fix": [r.get("t_fix") for r in rr], "d_ne": np.array([r["d_ne"] for r in rr]),
            "dec": [r.get("dec") for r in rr], "phase": [r.get("phase") for r in rr]}


def wczytaj(nazwa, d, kom, odswiez=False):
    """Lot + ticki utraty z pamięci podręcznej (pickle w CACHE)."""
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, f"{nazwa}.pkl")
    if os.path.exists(p) and not odswiez:
        return pickle.load(open(p, "rb"))
    L = Lot(nazwa, d, kom)
    L.tu = ticki_utraty(L)
    L.u = {k: L.u[k] for k in ("vehicle_local_position", "estimator_status_flags", "vehicle_status", "vehicle_attitude")}
    pickle.dump(L, open(p, "wb"))
    return L


if __name__ == "__main__":
    import nad3_dane as _N                                    # pickle klasy Lot pod nazwą modułu, nie __main__
    for n, d, k in loty():
        L = _N.wczytaj(n, d, k, odswiez=True)
        tu = L.tu
        print(n, k, "ticki", len(L.rama), "utraty", len(tu["sim"]), "misja", int(tu["misja"].sum()), "fx", len(L.fx),
              "t_flag", L.t_flag, "zp", L.t_zp, "bez t_s", int(np.isnan(tu["t_s"]).sum()), flush=True)
