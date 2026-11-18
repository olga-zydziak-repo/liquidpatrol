#!/usr/bin/env python3
"""results/PETLA_RECON/tools/pl_dane.py — dane 15 lotów reconu PĘTLA (PROMPT_PETLA_S0 §1(a); 0 bootów).

Loty: 14 bramki TEACH S3 (results/TEACH/s3/p*) + lot długi TEACH-II (results/TEACH2/s1/L1_S_c10). Per tick (demo.jsonl ↔
rama.jsonl ↔ trace „tk”, złączone po numerze ticka): t, faza sieci, pozycja EKF (own), pozycja sieci p_corr (rama; bez GNSS
= EKF + Δ, przed cięciem = EKF), prędkość, track (trk_pos, wiek, ważność), komenda sieci z logu, decyzja osłony, faza osłony,
zejście, GT drona (rama „gt” ENU → NED), GT intruza (tk „intr”, NED), flaga misji (faza approach/hold/orbit, bez zejścia,
ALLOW — jak sędzia). Zapis: results/PETLA_RECON/dane/<lot>.npz (cache); GT tylko do oceny.
"""
import glob
import json
import os

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
OUT = os.path.join(ROOT, "results/PETLA_RECON/dane")
MISJA = ("approach", "hold", "orbit")


def loty():
    s3 = sorted(d for d in glob.glob(os.path.join(ROOT, "results/TEACH/s3/p[0-9][0-9]_*")) if os.path.isdir(d))
    return s3 + [os.path.join(ROOT, "results/TEACH2/s1/L1_S_c10")]


def jl(p, typ=None):
    out = []
    with open(p) as f:
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


def wczytaj(d, cache=True):
    nazwa = os.path.basename(d)
    fn = os.path.join(OUT, nazwa + ".npz")
    if cache and os.path.exists(fn):
        z = np.load(fn, allow_pickle=True)
        return {k: z[k] for k in z.files}
    demo = {r["tick"]: r for r in jl(os.path.join(d, "demo.jsonl"))}
    rama = {r["tick"]: r for r in jl(os.path.join(d, "rama.jsonl"))}
    tk = {r["tick"]: r for r in jl(os.path.join(d, "trace.jsonl"), "tk")}
    ev = jl(os.path.join(d, "trace.jsonl"), "event")
    ticks = sorted(set(demo) & set(rama) & set(tk))
    zp = next((e["sim"] for e in ev if e.get("ev") == "zejscie_planowe"), 1e18)
    st = next(e for e in ev if e.get("ev") == "episode_start")
    cut = next((e for e in ev if e.get("ev") == "denial"), None)
    T = len(ticks)
    a = {k: np.zeros((T, 3)) for k in ("own", "net", "vel", "trk", "cmd", "gt", "intr", "d_ne3")}
    s = {k: np.zeros(T) for k in ("t", "age", "valid", "tick", "misja", "desc", "allow", "kont")}
    faza, dec = [], []
    for i, k in enumerate(ticks):
        dm, rm, t = demo[k], rama[k], tk[k]
        s["t"][i], s["tick"][i] = dm["t_sim"], k
        a["own"][i] = dm["own_pos_ned"]
        a["net"][i] = rm["p_corr"] if rm.get("p_corr") is not None else dm["own_pos_ned"]
        a["vel"][i] = dm["own_vel_ned"]
        a["trk"][i] = dm["trk_pos_ned"]
        a["cmd"][i] = dm["cmd_v_ned"]
        g = rm.get("gt")
        a["gt"][i] = [g[1], g[0], -g[2]] if g else [np.nan] * 3
        a["intr"][i] = t.get("intr") or [np.nan] * 3
        s["age"][i], s["valid"][i] = dm["track_age_s"], float(bool(dm["track_valid"]))
        s["desc"][i] = float(bool(rm.get("desc")))
        s["allow"][i] = float(rm.get("dec") == "ALLOW")
        s["kont"][i] = float(rm.get("ph") in ("KONT", "KONT_REFUSE"))
        s["misja"][i] = float(dm["phase"] in MISJA and not rm.get("desc") and rm.get("dec") == "ALLOW" and dm["t_sim"] < zp)
        faza.append(dm["phase"]); dec.append(rm.get("dec"))
    out = dict(a, **s, faza=np.array(faza), dec=np.array(dec), nazwa=nazwa, t_ep0=st["sim"],
               t_cut=(cut["t_inj_sim"] if cut else np.nan), t_zp=(zp if zp < 1e17 else np.nan),
               scen=st.get("scenario_id"))
    os.makedirs(OUT, exist_ok=True)
    np.savez_compressed(fn, **out)
    return out


if __name__ == "__main__":
    for d in loty():
        x = wczytaj(d, cache=False)
        print(x["nazwa"], len(x["t"]), int(x["misja"].sum()), str(x["scen"]), flush=True)
