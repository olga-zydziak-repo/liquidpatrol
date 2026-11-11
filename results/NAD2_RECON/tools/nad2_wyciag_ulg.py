#!/usr/bin/env python3
"""results/NAD2_RECON/tools/nad2_wyciag_ulg.py — PROMPT_NAD2_S0 §0.5: wyciąg z lokalnego boot.ulg do repo (0 bootów, ULG tylko czytany).

Per boot results/NAD2_RECON/ulg/<boot>.jsonl.gz, jeden wiersz JSON na temat, kolumnowo:
  {"temat": T, "pola": [...], "dane": {pole: [wartości]}}  — czas w sekundach (µs ULG / 1e6; w SITL lockstep = czas sim gz,
  sprawdzone dopasowaniem wartości p_ekf z rama.jsonl w R1).
Okno: od pierwszego episode_start (ENTRY epizodu; trace driver) − 1 s do gt_przyziemienie (cięcia) / ostatniego episode_end
(nominały) + 1 s.
Tematy: vehicle_local_position (timestamp, timestamp_sample, x, y, z, vx, vy, vz, heading), vehicle_attitude (timestamp,
timestamp_sample, q[0..3]) — pełna częstość; dla R4: estimator_status_flags (cs_gnss_pos, cs_opt_flow, cs_inertial_dead_reckoning
jeśli jest), estimator_aid_src_optical_flow (innowacje, test_ratio, fused, innovation_rejected), estimator_optical_flow_vel
(vel_ne, vel_ne_filtered), vehicle_angular_velocity (xyz) — decymowane do ≤ 50 Hz. Zaokrąglenie: pozycje 1e-4 m, prędkości 1e-4,
q 1e-6, czas 1e-6 s. Limit 3 MB na boot (asercja).
Użycie: nad2_wyciag_ulg.py <boot> [<boot> …]   (boot = nazwa katalogu w results/NADIR/s4; „s2:<boot>” = results/NADIR/s2,
wyjście s2_<boot>.jsonl.gz — próba kontrolna R5 (v))
"""
import gzip
import json
import os
import sys

import numpy as np
from pyulog import ULog

ROOT = "/home/olga/projects/liquidpatrol"
S4 = os.path.join(ROOT, "results/NADIR/s4")
OUT = os.path.join(ROOT, "results/NAD2_RECON/ulg")
LIMIT = 3 * 1024 * 1024
TEMATY = {
    "vehicle_local_position": (["timestamp", "timestamp_sample", "x", "y", "z", "vx", "vy", "vz", "heading"], None),
    "vehicle_attitude": (["timestamp", "timestamp_sample", "q[0]", "q[1]", "q[2]", "q[3]"], None),
    "estimator_status_flags": (["timestamp", "cs_gnss_pos", "cs_opt_flow", "cs_inertial_dead_reckoning", "cs_baro_hgt",
                                "cs_rng_hgt"], None),
    "estimator_aid_src_optical_flow": (["timestamp", "timestamp_sample", "innovation[0]", "innovation[1]", "test_ratio[0]",
                                        "test_ratio[1]", "fused", "innovation_rejected", "observation[0]", "observation[1]"], 50.0),
    "estimator_optical_flow_vel": (["timestamp", "timestamp_sample", "vel_ne[0]", "vel_ne[1]", "vel_ne_filtered[0]",
                                    "vel_ne_filtered[1]"], 50.0),
    "vehicle_angular_velocity": (["timestamp", "timestamp_sample", "xyz[0]", "xyz[1]", "xyz[2]"], 50.0),
}


S2 = os.path.join(ROOT, "results/NADIR/s2")


def katalog(boot):
    return (S2, boot[3:], "s2_" + boot[3:]) if boot.startswith("s2:") else (S4, boot, boot)


def okno(boot):
    kat, nazwa, _ = katalog(boot)
    ev = [json.loads(l) for l in open(os.path.join(kat, nazwa, "trace.jsonl")) if '"event"' in l]
    st = [e["sim"] for e in ev if e.get("ev") == "episode_start"]
    land = [e["sim"] for e in ev if e.get("ev") == "gt_przyziemienie"]
    end = [e["sim"] for e in ev if e.get("ev") == "episode_end"]
    return min(st) - 1.0, (land[-1] if land else max(end)) + 1.0


def zaokr(pole, a):
    if pole.startswith("timestamp"):
        return [round(float(x) / 1e6, 6) for x in a]
    if a.dtype.kind in "iub":
        return [int(x) for x in a]
    dec = 6 if pole.startswith("q[") else 4
    return [round(float(x), dec) for x in a]


def wyciag(boot):
    t0, t1 = okno(boot)
    kat, nazwa, wyj = katalog(boot)
    u = ULog(os.path.join(kat, nazwa, "boot.ulg"), list(TEMATY))
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, f"{wyj}.jsonl.gz")
    meta = {"temat": "_meta", "boot": boot, "okno_sim": [round(t0, 3), round(t1, 3)], "zrodlo": "boot.ulg (lokalny, .gitignore)",
            "czas": "s = timestamp µs / 1e6 (SITL lockstep = sim)"}
    n = {}
    with gzip.open(p, "wt") as f:
        f.write(json.dumps(meta) + "\n")
        for x in u.data_list:
            if x.multi_id != 0 or x.name not in TEMATY:
                continue
            pola, hz = TEMATY[x.name]
            pola = [k for k in pola if k in x.data]
            ts = x.data["timestamp"] / 1e6
            sel = np.flatnonzero((ts >= t0) & (ts <= t1))
            if hz:
                keep, last = [], -1e9
                for i in sel:
                    if ts[i] - last >= 1.0 / hz - 1e-9:
                        keep.append(i); last = ts[i]
                sel = np.array(keep, dtype=int)
            f.write(json.dumps({"temat": x.name, "pola": pola, "dane": {k: zaokr(k, x.data[k][sel]) for k in pola}}) + "\n")
            n[x.name] = int(len(sel))
    size = os.path.getsize(p)
    assert size <= LIMIT, (boot, size)
    print(boot, "okno", round(t0, 2), round(t1, 2), "MB", round(size / 2**20, 2), n, flush=True)


def czytaj(boot):
    """Wczytanie wyciągu: {temat: {pole: np.array}} + meta."""
    out = {}
    with gzip.open(os.path.join(OUT, f"{boot}.jsonl.gz"), "rt") as f:
        for l in f:
            r = json.loads(l)
            out[r["temat"]] = r if r["temat"] == "_meta" else {k: np.array(v) for k, v in r["dane"].items()}
    return out


if __name__ == "__main__":
    for b in sys.argv[1:]:
        wyciag(b)
