#!/usr/bin/env python3
"""results/REAKW_RECON/tools/reakw_recon.py — recon RE-AKW (PROMPT_REAKW_S0 §R).
ZERO lotów, zero edycji istniejących plików — czyta WYŁĄCZNIE artefakty kampanii
AKW S3 (results/AKW/camp) i GT.

Tryby:
  vel   (R1): jakość trk_vel_ned vs vel_GT na tickach ważnych tracków, per v_intr,
        per ramię (V2 i B) — rozkłady |Δv|, błąd kąta kierunku, błąd modułu.
  dir   (R3): replay kierunkowy na porażkach V2 — per epizod-porażka: zdarzenia
        utraty tracku z demo.jsonl; dla każdej utraty ψ_pred(Δt) z ostatniego
        ważnego fd (pos+vel) vs FAKTYCZNY azymut GT celu i faktyczny yaw komendy;
        czy cel w stożku ENTRY (±43.45°) wokół ψ_pred po ≤1–2 krokach; strata
        czasowa ślepego skanu; klasyfikacja „nie-kierunek" (sufit mechanizmu).
  man   (R4): manewrowość celu z GT — zmiana kursu GT w oknach 2/5 s (per v_intr).

Wyjścia: results/REAKW_RECON/{vel_quality.json, dir_replay.json, maneuver.json}.
"""
from __future__ import annotations

import argparse
import bisect
import json
import math
import os
import glob

ROOT = "/home/olga/projects/liquidpatrol"
CAMP = os.path.join(ROOT, "results/AKW/camp")
OUTD = os.path.join(ROOT, "results/REAKW_RECON")

HALF_CONE = 86.9 / 2          # stożek ENTRY efektywny (edge-margin 0.10), recon AKW R2
STEP_DEG = 40.0
TRACK_LOSS_S = 1.0            # net_controller.py:35
V_CELLS = {0.0: (0, 1, 2, 3), 0.5: (4, 5, 6, 7), 1.0: (8, 9, 10, 11)}

V2_FAILURES = ["c01_s01", "c05_s02", "c06_s04", "c08_s02", "c08_s03", "c08_s04",
               "c09_s02", "c09_s03", "c10_s01", "c10_s03", "c11_s01", "c11_s02",
               "c11_s03", "c11_s04"]


def jload(p):
    out = []
    for ln in open(p):
        ln = ln.strip()
        if ln:
            try:
                out.append(json.loads(ln))
            except json.JSONDecodeError:
                pass
    return out


def v_of_cell(sid):
    c = int(sid.split("_")[0][1:])
    for v, cells in V_CELLS.items():
        if c in cells:
            return v
    return None


class GT:
    def __init__(self, bootdir):
        g = jload(os.path.join(bootdir, "gt_intruder.jsonl"))
        self.ts = [r["t_sim"] for r in g]
        self.ps = [r["ned"] for r in g]

    def pos(self, t):
        if not self.ts or t < self.ts[0] or t > self.ts[-1]:
            return None
        i = bisect.bisect_right(self.ts, t)
        i = max(1, min(i, len(self.ts) - 1))
        t0, t1 = self.ts[i - 1], self.ts[i]
        a = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
        return [self.ps[i - 1][k] + a * (self.ps[i][k] - self.ps[i - 1][k]) for k in range(3)]

    def vel(self, t, h=0.25):
        p0, p1 = self.pos(t - h), self.pos(t + h)
        if p0 is None or p1 is None:
            return None
        return [(p1[k] - p0[k]) / (2 * h) for k in range(3)]


def ang_diff_deg(a, b):
    d = math.degrees(a - b)
    while d > 180:
        d -= 360
    while d < -180:
        d += 360
    return d


def pct(xs, q):
    if not xs:
        return None
    s = sorted(xs)
    return round(s[min(len(s) - 1, int(q * (len(s) - 1)))], 3)


def demo_ticks(bootdir):
    return [r for r in jload(os.path.join(bootdir, "demo.jsonl"))
            if "tick" in r and "own_pos_ned" in r]


# ---------- R1: jakość vel ----------

def cmd_vel():
    res = {}
    for arm_glob, armk in (("r*_V2", "V2"), ("r*_B", "B")):
        per_v = {v: {"dv_abs": [], "ang_err": [], "spd_est": [], "spd_gt": [], "n": 0}
                 for v in V_CELLS}
        for d in sorted(glob.glob(os.path.join(CAMP, arm_glob))):
            if not os.path.isdir(d):
                continue
            gt = GT(d)
            for r in demo_ticks(d):
                if not r.get("track_valid") or r.get("track_age_s", 9) > 0.3:
                    continue
                v = v_of_cell(r["scenario_id"])
                vg = gt.vel(r["t_sim"])
                if v is None or vg is None:
                    continue
                ve = r["trk_vel_ned"]
                B = per_v[v]
                B["n"] += 1
                dv = math.dist(ve[:2], vg[:2])
                B["dv_abs"].append(dv)
                se = math.hypot(*ve[:2])
                sg = math.hypot(*vg[:2])
                B["spd_est"].append(se)
                B["spd_gt"].append(sg)
                if sg > 0.2 and se > 0.05:
                    B["ang_err"].append(abs(ang_diff_deg(math.atan2(ve[1], ve[0]),
                                                         math.atan2(vg[1], vg[0]))))
        res[armk] = {str(v): {"n": B["n"],
                              "dv_xy_p50": pct(B["dv_abs"], .5), "dv_xy_p90": pct(B["dv_abs"], .9),
                              "ang_err_deg_p50": pct(B["ang_err"], .5),
                              "ang_err_deg_p90": pct(B["ang_err"], .9),
                              "n_ang": len(B["ang_err"]),
                              "spd_est_p50": pct(B["spd_est"], .5),
                              "spd_gt_p50": pct(B["spd_gt"], .5)}
                     for v, B in per_v.items()}
    os.makedirs(OUTD, exist_ok=True)
    json.dump(res, open(os.path.join(OUTD, "vel_quality.json"), "w"), indent=1)
    print(json.dumps(res, indent=1))


# ---------- R3: replay kierunkowy ----------

def episode_windows(bootdir):
    wins = {}
    cur = None
    for e in jload(os.path.join(bootdir, "trace.jsonl")):
        if e.get("t") != "event":
            continue
        if e.get("ev") == "episode_start":
            cur = {"sid": e.get("scenario_id"), "lo": e.get("t0_sim")}
        elif e.get("ev") == "invalid_start":
            cur = None
        elif e.get("ev") == "episode_end" and cur:
            wins[cur["sid"]] = (cur["lo"], e["sim"])
            cur = None
    return wins


def cmd_dir():
    # mapuj porażki -> boot V2 (pierwsza ważna próba = r{N}_V2, siatka AKW)
    pairs = json.load(open(os.path.join(CAMP, "akw_pairs.json")))
    fail_boot = {p["scenario_id"]: p["V2_boot"] for p in pairs["pairs"]
                 if p["scenario_id"] in V2_FAILURES}
    out = []
    for sid, boot in sorted(fail_boot.items()):
        d = os.path.join(CAMP, boot)
        gt = GT(d)
        wins = episode_windows(d)
        lo, hi = wins[sid]
        ticks = [r for r in demo_ticks(d) if r["scenario_id"] == sid]
        ticks.sort(key=lambda r: r["t_sim"])
        # zdarzenia utraty: tick z phase hold, poprzedni tick track (age<=1.0 na poprzednim)
        losses = []
        prev = None
        for r in ticks:
            if prev is not None and r["phase"] == "hold" and prev["phase"] != "hold":
                losses.append((prev, r))
            prev = r
        ep = {"sid": sid, "boot": boot, "t0": lo, "n_losses": len(losses), "losses": []}
        for last_ok, first_hold in losses:
            t_loss = first_hold["t_sim"]
            own = first_hold["own_pos_ned"]
            lp, lv = last_ok["trk_pos_ned"], last_ok["trk_vel_ned"]
            # wariant BUFOROWANY: ostatni tick ze ŚWIEŻYM trackiem (age<=0.3) przed utratą
            buf = None
            for r in ticks:
                if r["t_sim"] >= t_loss:
                    break
                if r.get("track_valid") and r.get("track_age_s", 9) <= 0.3:
                    buf = r
            # klasyfikacja utraty: fantom-start = zero świeżych ticków w epizodzie przed utratą
            fresh_in_ep = buf is not None
            # brama wiarygodności vel (plauzybilność): |v|<=3.0 m/s
            bv = buf["trk_vel_ned"] if buf else None
            gate_ok = fresh_in_ep and math.hypot(bv[0], bv[1]) <= 3.0
            # koniec ślepego odcinka: następny tick track po t_loss
            t_reacq = None
            for r in ticks:
                if r["t_sim"] > t_loss and r["phase"] != "hold":
                    t_reacq = r["t_sim"]
                    break
            blind_s = round((t_reacq - t_loss), 2) if t_reacq else round(hi - t_loss, 2)
            L = {"t_loss_rel": round(t_loss - lo, 2), "blind_s": blind_s,
                 "reacq": t_reacq is not None,
                 "fresh_in_ep": fresh_in_ep, "gate_ok": bool(gate_ok),
                 "spd_last_vel": round(math.hypot(lv[0], lv[1]), 2),
                 "spd_buf_vel": (round(math.hypot(bv[0], bv[1]), 2) if bv else None),
                 "buf_age_before_loss_s": (round(t_loss - buf["t_sim"], 2) if buf else None)}
            # ψ_pred (raw / buforowany) vs GT w horyzontach Δt od chwili utraty
            for dt in (2.0, 4.0, 8.0):
                t = t_loss + dt
                g = gt.pos(t)
                if g is None or t > hi:
                    L[f"dt{dt:g}"] = None
                    continue
                ownt = min((r for r in ticks if r["t_sim"] >= t),
                           key=lambda r: r["t_sim"], default=first_hold)["own_pos_ned"]
                psi_gt = math.atan2(g[1] - ownt[1], g[0] - ownt[0])
                rng = math.dist(ownt[:2], g[:2])

                def err_of(p0, v0, dt_eff):
                    pr = [p0[k] + v0[k] * dt_eff for k in range(3)]
                    return abs(ang_diff_deg(math.atan2(pr[1] - ownt[1], pr[0] - ownt[0]),
                                            psi_gt))
                e_raw = err_of(lp, lv, dt)
                e_buf = (err_of(buf["trk_pos_ned"], buf["trk_vel_ned"],
                                t - buf["t_sim"]) if buf else None)
                L[f"dt{dt:g}"] = {
                    "rng_m": round(rng, 1),
                    "err_raw_deg": round(e_raw, 1),
                    "err_buf_deg": (round(e_buf, 1) if e_buf is not None else None),
                    "buf_in_cone": (e_buf is not None and e_buf <= HALF_CONE),
                    "buf_in_1step": (e_buf is not None and e_buf <= HALF_CONE + STEP_DEG),
                    "buf_in_2step": (e_buf is not None and e_buf <= HALF_CONE + 2 * STEP_DEG)}
            ep["losses"].append(L)
        out.append(ep)
    os.makedirs(OUTD, exist_ok=True)
    json.dump(out, open(os.path.join(OUTD, "dir_replay.json"), "w"), indent=1)
    for ep in out:
        print(f"== {ep['sid']} ({ep['boot']}): utrat {ep['n_losses']}")
        for L in ep["losses"]:
            print("  ", json.dumps(L))


# ---------- R4: manewrowość celu ----------

def cmd_man():
    res = {}
    for v, cells in V_CELLS.items():
        if v == 0.0:
            res[str(v)] = {"nota": "cel statyczny — kurs niezdefiniowany"}
            continue
        turns2, turns5 = [], []
        for d in sorted(glob.glob(os.path.join(CAMP, "r*_V2"))):
            if not os.path.isdir(d):
                continue
            gt = GT(d)
            wins = episode_windows(d)
            for sid, (lo, hi) in wins.items():
                if int(sid.split("_")[0][1:]) not in cells:
                    continue
                t = lo + 1.0
                while t + 5.0 < hi:
                    v0 = gt.vel(t)
                    v2 = gt.vel(t + 2.0)
                    v5 = gt.vel(t + 5.0)
                    if v0 and v2 and math.hypot(*v0[:2]) > 0.2 and math.hypot(*v2[:2]) > 0.2:
                        turns2.append(abs(ang_diff_deg(math.atan2(v2[1], v2[0]),
                                                       math.atan2(v0[1], v0[0]))))
                    if v0 and v5 and math.hypot(*v0[:2]) > 0.2 and math.hypot(*v5[:2]) > 0.2:
                        turns5.append(abs(ang_diff_deg(math.atan2(v5[1], v5[0]),
                                                       math.atan2(v0[1], v0[0]))))
                    t += 1.0
        res[str(v)] = {"n2": len(turns2), "turn2s_p50": pct(turns2, .5), "turn2s_p90": pct(turns2, .9),
                       "n5": len(turns5), "turn5s_p50": pct(turns5, .5), "turn5s_p90": pct(turns5, .9),
                       "frac_turn2s_gt45": round(sum(1 for x in turns2 if x > 45) / len(turns2), 3) if turns2 else None,
                       "frac_turn5s_gt45": round(sum(1 for x in turns5 if x > 45) / len(turns5), 3) if turns5 else None}
    os.makedirs(OUTD, exist_ok=True)
    json.dump(res, open(os.path.join(OUTD, "maneuver.json"), "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["vel", "dir", "man"])
    a = ap.parse_args()
    {"vel": cmd_vel, "dir": cmd_dir, "man": cmd_man}[a.mode]()
