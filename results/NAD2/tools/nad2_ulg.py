#!/usr/bin/env python3
"""results/NAD2/tools/nad2_ulg.py — PROMPT_NAD2_S2 §1.2: wyciąg ULG bootu NAD2 do repo (<boot>/ulg.jsonl.gz, ≤ 3 MB).

Tematy, pola, zaokrąglenie, decymacja i okno jak w reconie (results/NAD2_RECON/tools/nad2_wyciag_ulg.py — TEMATY i zaokr
importowane READ-ONLY): od pierwszego episode_start − 1 s do gt_przyziemienie (cięcie) / ostatniego episode_end (nominał) + 1 s;
czas w s (µs/1e6 = sim). Dodatkowo vehicle_status (nav_state, failsafe) — B4 analizatora z repo.
Użycie: nad2_ulg.py <katalog_bootu> [...]
"""
import gzip
import json
import os
import sys

import numpy as np
from pyulog import ULog

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, os.path.join(ROOT, "results/NAD2_RECON/tools"))
import nad2_wyciag_ulg as W

TEMATY = dict(W.TEMATY)
TEMATY["vehicle_status"] = (["timestamp", "nav_state", "failsafe", "arming_state"], None)
LIMIT = int(float(os.environ.get("NAD2_ULG_LIMIT_MB", "3")) * 1024 * 1024)   # S4 lot długi (ANEKS_NAD2-3 §2): env, dom. 3 MB


def okno(d):
    ev = [json.loads(l) for l in open(os.path.join(d, "trace.jsonl")) if '"event"' in l]
    st = [e["sim"] for e in ev if e.get("ev") == "episode_start"]
    land = [e["sim"] for e in ev if e.get("ev") == "gt_przyziemienie"]
    end = [e["sim"] for e in ev if e.get("ev") == "episode_end"]
    return min(st) - 1.0, (land[-1] if land else max(end)) + 1.0


def wyciag(d):
    t0, t1 = okno(d)
    u = ULog(os.path.join(d, "boot.ulg"), list(TEMATY))
    p = os.path.join(d, "ulg.jsonl.gz")
    n = {}
    with gzip.open(p, "wt") as f:
        f.write(json.dumps({"temat": "_meta", "boot": os.path.basename(d.rstrip("/")), "okno_sim": [round(t0, 3), round(t1, 3)],
                            "zrodlo": "boot.ulg (lokalny, .gitignore)", "czas": "s = timestamp µs / 1e6 (SITL lockstep = sim)"}) + "\n")
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
            f.write(json.dumps({"temat": x.name, "pola": pola, "dane": {k: W.zaokr(k, x.data[k][sel]) for k in pola}}) + "\n")
            n[x.name] = int(len(sel))
    size = os.path.getsize(p)
    assert size <= LIMIT, (d, size)
    return {"plik": p, "MB": round(size / 2 ** 20, 2), "n": n, "okno": [round(t0, 2), round(t1, 2)]}


if __name__ == "__main__":
    for d in sys.argv[1:]:
        print(json.dumps(wyciag(d), ensure_ascii=False))
