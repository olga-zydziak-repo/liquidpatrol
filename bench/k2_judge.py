#!/usr/bin/env python3
"""bench/k2_judge.py — glue-sędzia K2 (PROMPT_K2_BUILD B6, PRE_K2 K4). ZERO zmian w zamrożonych sędziach.

Składa dwa istniejące przyrządy przez IMPORT (nie kopię):
  - ważność epizodu DO T_inj: `bench_judge` (V2′) na oknie [t0, t_inj] — czy sieć weszła i orbitowała zdrowo.
  - metryki denialu PO T_inj: `k1_judge.gt_metrics` (r_max, x_exc od punktu wstrzyknięcia, t_td, breach).
  - t_refuse: z trace (denial → refuse POS), pasmo [0.05, 0.15] s (ANEKS_K2-1, dziedziczone z K1).

Werdykt (+) per epizod (PRE_K2 K4): t_refuse∈[0.05,0.15] ∧ touchdown (D5 wykonane) ∧ breach=False ∧
x_exc ≤ eps_cap ∧ sekwencja bez natywnego failsafe. `eps_cap` = ARGUMENT (wartość z PRE/K1, nie zaszyta —
SR-6). Drabina nogi (ANEKS_K2-1): 12/12 PASS · 1 porażka przejęcia na ważnym = NIEROZSTRZYGNIĘTE · ≥2 = FAIL.

Zero SITL. Czyste funkcje (verdict/band) testowalne syntetycznie.
"""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from k1.k1_judge import gt_metrics, load_gt          # frozen — import, nie kopia
from bench.bench_judge import judge_episode, _load_drone_ned, _load_intr_ned, _load_rtf

TREFUSE_BAND = (0.05, 0.15)                           # ANEKS_K2-1 §1 (dziedziczone z K1)
NATIVE_FAILSAFE_EVENTS = ("NAV_LAND", "nav_land", "auto_land", "AUTO.LAND", "failsafe")


def trefuse_in_band(t_refuse, band=TREFUSE_BAND):
    """True ⇔ t_refuse w [lo, hi] domkniętym. Brzeg 0.04/0.16 ⇒ False (pasmo dwustronne)."""
    if t_refuse is None:
        return False
    return band[0] <= t_refuse <= band[1]


def episode_verdict(t_refuse, touchdown, breach, x_exc, eps_cap, native_failsafe):
    """Werdykt (+) epizodu K2 (PRE_K2 K4). Wszystkie warunki łącznie. eps_cap = z PRE/K1 (arg)."""
    reasons = []
    if not trefuse_in_band(t_refuse):
        reasons.append(f"t_refuse={t_refuse} poza {TREFUSE_BAND}")
    if not touchdown:
        reasons.append("brak touchdown (D5 niedokończone)")
    if breach:
        reasons.append("breach")
    if x_exc is None or x_exc > eps_cap:
        reasons.append(f"x_exc={x_exc} > eps_cap={eps_cap}")
    if native_failsafe:
        reasons.append("natywny failsafe w sekwencji")
    return {"pass": len(reasons) == 0, "reasons": reasons}


def leg_verdict(n_valid, n_pass):
    """Drabina nogi (ANEKS_K2-1 §1): 12/12 PASS · dokładnie 1 porażka na ważnym = NIEROZSTRZYGNIĘTE · ≥2 = FAIL."""
    fails = n_valid - n_pass
    if n_valid == 12 and n_pass == 12:
        return "PASS"
    if fails == 1:
        return "NIEROZSTRZYGNIETE"
    if fails >= 2:
        return "FAIL"
    return "NIEKOMPLETNE"                             # <12 ważnych epizodów


# --------------------------- odczyt trace lotu K2 (gdy dostępny) ---------------------------
def _events(trace):
    return [json.loads(l) for l in open(trace) if '"t": "event"' in l]


def judge_episode_k2(outdir, eps_cap, home=None):
    """Zwraca listę werdyktów epizodów z trace K2 (denial + refuse POS + touchdown + gt).
    Ważność do T_inj = bench_judge V2′; metryki po T_inj = k1_judge.gt_metrics."""
    trace = os.path.join(outdir, "trace.jsonl")
    drone = _load_drone_ned(trace)
    intr = _load_intr_ned(os.path.join(outdir, "gt_intruder.jsonl"))
    rtf = _load_rtf(os.path.join(outdir, "rtf_stream.jsonl"))
    gt = load_gt(trace)                               # gt rows (dla k1_judge)
    evs = _events(trace)
    out = []
    cur = None
    denial_sim = refuse_sim = td_sim = None
    for e in evs:
        ev = e.get("ev")
        if ev == "episode_start":
            cur = {"id": e["episode_id"], "sid": e["scenario_id"], "lo": e["sim"]}
            denial_sim = refuse_sim = td_sim = None
        elif ev == "denial" and cur:
            denial_sim = e.get("t_inj_sim", e.get("sim"))
        elif ev == "refuse" and cur and e.get("reason") == "POS_DEGRADED":
            if refuse_sim is None:
                refuse_sim = e.get("sim")
        elif ev == "touchdown" and cur:
            td_sim = e.get("sim")
        elif ev == "episode_end" and cur:
            cur["hi"] = e.get("sim"); cur["breach"] = bool(e.get("breach"))
            cur["denied"] = bool(e.get("denied")); cur["t_inj"] = e.get("t_inj_sim", denial_sim)
            # ważność do T_inj (V2′) — okno [lo, t_inj] (jeśli denial) lub [lo, hi]
            t_cut = cur["t_inj"] if cur["t_inj"] is not None else cur["hi"]
            dg = [(t, q) for t, q in drone if cur["lo"] <= t <= t_cut]
            v = judge_episode(dg, intr, rtf=rtf, refuse_count=0, breach=False, timejump=0)
            valid = v.get("valid_V2", v.get("valid_campaign_V2p", False))
            # metryki denialu po T_inj
            if cur["t_inj"] is not None:
                gm = gt_metrics(gt, cur["t_inj"], home=home)
                x_exc = gm.get("x_exc"); breach = gm.get("breach") or cur["breach"]
                t_td = gm.get("t_td_s")
            else:
                x_exc = None; breach = cur["breach"]; t_td = None
            t_refuse = (refuse_sim - denial_sim) if (refuse_sim and denial_sim) else None
            native = any(str(e2.get("ev", "")) in NATIVE_FAILSAFE_EVENTS for e2 in evs)
            verd = episode_verdict(t_refuse, td_sim is not None, breach, x_exc, eps_cap, native)
            out.append({"episode_id": cur["id"], "scenario_id": cur["sid"], "valid": bool(valid),
                        "t_refuse": t_refuse, "x_exc": x_exc, "t_td_s": t_td, "breach": breach,
                        "touchdown": td_sim is not None, "verdict": verd})
            cur = None
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir")
    ap.add_argument("--eps-cap", type=float, required=True)
    a = ap.parse_args()
    vs = judge_episode_k2(a.outdir, a.eps_cap)
    for v in vs:
        print(v["scenario_id"], "valid", v["valid"], "t_refuse", v["t_refuse"], "x_exc", v["x_exc"],
              "td", v["touchdown"], "PASS", v["verdict"]["pass"], v["verdict"]["reasons"])
