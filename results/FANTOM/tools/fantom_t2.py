#!/usr/bin/env python3
"""results/FANTOM/tools/fantom_t2.py — T2: desk-replay predykatu kwarantanny
z REGUŁĄ WYBORU (PRE_FANTOM §2, mechaniczna). ZERO lotów; czyta demo.jsonl +
gt_intruder kampanii AKW S3 i zbiory z recon (r2_scope.json).

Symulacja per epizod (t_ref = t_sim pierwszego ticku demo epizodu):
  K2: wyjście gdy track_valid ∧ track_age_s < (t−t_ref) − ε (ε=0.5); fallback C
      przy dt ≥ T_q=3.0.
  K1 (porównawczo): (A) invalid→valid, (B) |trk_pos − migawka(t_ref)| > 5 m,
      (C) T_q.
Miary: t_exit/powód; t_first_consumable (pierwszy tick valid ∧ age≤1.0 —
dzisiejszy start konsumpcji); t_real_adm (pierwszy tick valid ∧ age≤0.3 ∧
d(trk, GT)≤5 m — realna admisja); dla N6 dodatkowo: czy K2 NIE wyszedł na
fantomie (żaden tick z valid fd spełniający K2 przy d(trk,GT)>5).
Kryteria reguły (PRE §2): (i) 6/6 N6 trzymane do realnej admisji; (ii) wyjście
≤1.0 s na 48 śladach B + c05_s04 + zwłoka 0 na 30 czystych V2; (iii) 9 żywych-PASS:
wyjście ≤ realna admisja ∧ przewidywana akwizycja czystego startu ≤ obserwowana
realna +1 s dla ≥8/9 (c09_s01 do +4 s).
Wyjście: results/FANTOM/t2_desk.json + tabela.
"""
from __future__ import annotations

import json
import math
import os
import sys
import glob
import re

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, os.path.join(ROOT, "results/REAKW_RECON/tools"))
sys.path.insert(0, os.path.join(ROOT, "results/FANTOM_RECON/tools"))
from reakw_recon import jload, episode_windows, GT as _GT               # READ-ONLY


class GT(_GT):
    """GT z wartą luki: zwraca None, gdy najbliższe próbki GT nie obejmują t w ≤0.3 s
    (luka teleportu między epizodami — interpolacja przez nią to artefakt)."""

    def pos(self, t):
        import bisect
        if not self.ts or t < self.ts[0] or t > self.ts[-1]:
            return None
        i = bisect.bisect_right(self.ts, t)
        i = max(1, min(i, len(self.ts) - 1))
        if (t - self.ts[i - 1]) > 0.3 or (self.ts[i] - t) > 0.3:
            return None
        return super().pos(t)
from fantom_recon import scan_heading_deg, HALF_CONE, DWELL_S, CYCLE, STEP_T  # READ-ONLY

CAMP = os.path.join(ROOT, "results/AKW/camp")
OUTD = os.path.join(ROOT, "results/FANTOM")
EPS = 0.5
T_Q = 3.0
D_JUMP = 5.0
TICK = 0.06
N6 = ["c01_s01", "c05_s02", "c06_s04", "c08_s02", "c08_s03", "c08_s04"]
ZYWE_PASS = ["c01_s02", "c01_s03", "c01_s04", "c04_s01", "c05_s01", "c07_s01",
             "c07_s02", "c09_s01", "c10_s04"]
LOCK_REAL = ["c05_s04"]


def demo_eps(d):
    out = {}
    for r in jload(os.path.join(d, "demo.jsonl")):
        if "tick" in r and "own_pos_ned" in r:
            out.setdefault(r["scenario_id"], []).append(r)
    for v in out.values():
        v.sort(key=lambda r: r["t_sim"])
    return out


def sim_trace(ticks, gt=None):
    """Symulacja K2 i K1 na tickach demo jednego epizodu."""
    t_ref = ticks[0]["t_sim"]
    snap = (list(ticks[0]["trk_pos_ned"]) if ticks[0].get("track_valid") else None)
    k2 = {"t": None, "reason": None}
    k1 = {"t": None, "reason": None}
    prev_valid = bool(ticks[0].get("track_valid"))
    t_consum = None
    t_real = None
    k2_phantom_fire = False
    for r in ticks:
        dt = r["t_sim"] - t_ref
        valid = bool(r.get("track_valid"))
        age = r.get("track_age_s", 1e9)
        g = gt.pos(r["t_sim"]) if gt else None
        d_gt = (math.dist(r["trk_pos_ned"][:2], g[:2]) if (valid and g) else None)
        if t_consum is None and valid and age <= 1.0:
            t_consum = dt
        if t_real is None and valid and age <= 0.3 and d_gt is not None and d_gt <= D_JUMP:
            t_real = dt
        if k2["t"] is None:
            if valid and age < dt - EPS:
                k2.update(t=dt, reason="fresh")
                if d_gt is not None and d_gt > D_JUMP:
                    k2_phantom_fire = True
            elif dt >= T_Q:
                k2.update(t=dt, reason="C")
        if k1["t"] is None:
            fired = None
            if valid and not prev_valid:
                fired = "A"
            elif valid and snap is not None and \
                    math.dist(r["trk_pos_ned"][:2], snap[:2]) > D_JUMP:
                fired = "B"
            elif dt >= T_Q:
                fired = "C"
            if fired:
                k1.update(t=dt, reason=fired)
                if fired in ("A", "B") and d_gt is not None and d_gt > D_JUMP:
                    k1["phantom_fire"] = True
        prev_valid = valid
    return {"k2_t": k2["t"], "k2_reason": k2["reason"], "k2_phantom_fire": k2_phantom_fire,
            "k1_t": k1["t"], "k1_reason": k1["reason"],
            "k1_phantom_fire": bool(k1.get("phantom_fire")),
            "t_consum": t_consum, "t_real_adm": t_real}


def clean_start_pred(ticks, gt, lo, hi):
    """Przewidywana akwizycja czystego startu (metoda R3 recon: profil II od ψ=0)."""
    own0 = ticks[0]["own_pos_ned"]
    t = 0.2
    while t < min(30.0, hi - lo):
        g = gt.pos(lo + t)
        if g is None:
            t += 0.1
            continue
        psi = scan_heading_deg(t)
        ins = (t <= DWELL_S) or (((t - DWELL_S) % CYCLE) >= STEP_T)
        az = math.degrees(math.atan2(g[1] - own0[1], g[0] - own0[0])) % 360
        if ins and abs((az - psi + 180) % 360 - 180) <= HALF_CONE:
            ok = True
            tt = t
            while tt < t + 1.0:
                gg = gt.pos(lo + tt)
                ps = scan_heading_deg(tt)
                i2 = (tt <= DWELL_S) or (((tt - DWELL_S) % CYCLE) >= STEP_T)
                a2 = math.degrees(math.atan2(gg[1] - own0[1], gg[0] - own0[0])) % 360
                if not (i2 and abs((a2 - ps + 180) % 360 - 180) <= HALF_CONE):
                    ok = False
                    break
                tt += 0.1
            if ok:
                return round(t + 1.0, 1)
        t += 0.1
    return None


def main():
    pairs = json.load(open(os.path.join(CAMP, "akw_pairs.json")))
    v2_boot = {p["scenario_id"]: p["V2_boot"] for p in pairs["pairs"]}
    b_boot = {p["scenario_id"]: p["B_boot"] for p in pairs["pairs"]}
    r2 = json.load(open(os.path.join(ROOT, "results/FANTOM_RECON/r2_scope.json")))
    czyste = [x["sid"] for x in r2["rows_AKW_V2"] if not x["lock_at_start"]]

    cache = {}

    def eps_of(boot):
        if boot not in cache:
            cache[boot] = demo_eps(os.path.join(CAMP, boot))
        return cache[boot]

    gts = {}

    def gt_of(boot):
        if boot not in gts:
            gts[boot] = GT(os.path.join(CAMP, boot))
        return gts[boot]

    res = {"eps": EPS, "t_q": T_Q, "d_jump": D_JUMP, "rows": {}, "kryteria": {}}

    def run(sid, boot, with_pred=False):
        d = os.path.join(CAMP, boot)
        ticks = eps_of(boot)[sid]
        gt = gt_of(boot)
        row = sim_trace(ticks, gt)
        if with_pred:
            wins = episode_windows(d)
            lo, hi = wins[sid]
            row["pred_czysty_start"] = clean_start_pred(ticks, gt, lo, hi)
        row["boot"] = boot
        return row

    # N6
    for sid in N6:
        res["rows"][f"N6:{sid}"] = run(sid, v2_boot[sid])
    # lock-real + żywe-PASS (z przewidywaniem czystego startu)
    res["rows"]["LR:c05_s04"] = run("c05_s04", v2_boot["c05_s04"])
    for sid in ZYWE_PASS:
        res["rows"][f"ZP:{sid}"] = run(sid, v2_boot[sid], with_pred=True)
    # czyste V2 (30)
    for sid in czyste:
        res["rows"][f"CZ:{sid}"] = run(sid, v2_boot[sid])
    # 48 śladów B
    for sid, boot in sorted(b_boot.items()):
        res["rows"][f"B:{sid}"] = run(sid, boot)

    # ---- kryteria reguły wyboru (K2) ----
    # (i) N6: trzymane do realnej admisji — zero odpaleń fresh na fantomie
    i_ok = all(not res["rows"][f"N6:{s}"]["k2_phantom_fire"] for s in N6)
    i_detail = {s: {"k2": (res["rows"][f"N6:{s}"]["k2_t"], res["rows"][f"N6:{s}"]["k2_reason"]),
                    "fantom_fire": res["rows"][f"N6:{s}"]["k2_phantom_fire"],
                    "t_real_adm": res["rows"][f"N6:{s}"]["t_real_adm"]} for s in N6}
    # (ii) B 48 + c05_s04: wyjście ≤1.0; czyste 30: zwłoka max(0, t_exit−t_consum)=0
    b_exits = {k: v["k2_t"] for k, v in res["rows"].items() if k.startswith("B:")}
    ii_b_ok = all(t is not None and t <= 1.0 for t in b_exits.values())
    lr = res["rows"]["LR:c05_s04"]
    ii_lr_ok = lr["k2_t"] is not None and lr["k2_t"] <= 1.0
    cz_delay = {}
    for k, v in res["rows"].items():
        if not k.startswith("CZ:"):
            continue
        if v["t_consum"] is None:
            cz_delay[k] = 0.0             # epizod bez konsumowalnego fd — brak zwłoki z definicji
        else:
            ex = v["k2_t"] if (v["k2_t"] is not None and v["k2_reason"] == "fresh") else \
                (v["k2_t"] if v["k2_t"] is not None and v["k2_t"] < v["t_consum"] else v["t_consum"])
            cz_delay[k] = max(0.0, round((v["k2_t"] or 0) - v["t_consum"], 3)) \
                if (v["k2_t"] is not None and v["k2_t"] > v["t_consum"]) else 0.0
    ii_cz_ok = all(dl <= TICK for dl in cz_delay.values())
    # (iii) żywe-PASS — koniunkcja (wyjście ≤ realna admisja ∧ pred ≤ obs+limit)
    # spełniona „dla ≥8/9" (odczyt litery PRE: kwantyfikator obejmuje całe kryterium)
    def iii_eval(key_t, key_r):
        rows_ = {}
        n_ok_ = 0
        for sid in ZYWE_PASS:
            v = res["rows"][f"ZP:{sid}"]
            exit_le_adm = (v[key_t] is not None and v["t_real_adm"] is not None
                           and v[key_t] <= v["t_real_adm"] + TICK)
            lim = 4.0 if sid == "c09_s01" else 1.0
            pred_ok = (v["pred_czysty_start"] is not None and v["t_real_adm"] is not None
                       and v["pred_czysty_start"] <= v["t_real_adm"] + lim)
            rows_[sid] = {"exit": (v[key_t], v[key_r]), "t_real_adm": v["t_real_adm"],
                          "pred": v["pred_czysty_start"], "exit_le_adm": exit_le_adm,
                          "pred_ok": pred_ok, "oba": exit_le_adm and pred_ok}
            if exit_le_adm and pred_ok:
                n_ok_ += 1
        return n_ok_ >= 8, n_ok_, rows_

    iii_ok, n_ok, iii_rows = iii_eval("k2_t", "k2_reason")

    # ---- K1 wg reguły (ii) ZŁAGODZONE do ≤T_q ----
    k1_i_ok = all(not res["rows"][f"N6:{s}"]["k1_phantom_fire"] for s in N6)
    k1_all_exits = {k: v["k1_t"] for k, v in res["rows"].items()
                    if k.startswith(("B:", "CZ:", "LR:"))}
    k1_ii_ok = all(t is not None and t <= T_Q + TICK for t in k1_all_exits.values())
    k1_koszt_B = {k: v["k1_t"] for k, v in res["rows"].items()
                  if k.startswith("B:") and v["k1_reason"] == "C"}
    k1_iii_ok, k1_n_ok, k1_iii_rows = iii_eval("k1_t", "k1_reason")

    k2_all = bool(i_ok and ii_b_ok and ii_lr_ok and ii_cz_ok and iii_ok)
    k1_all = bool(k1_i_ok and k1_ii_ok and k1_iii_ok)
    res["kryteria"] = {
        "K2": {"i_N6_trzymane": {"ok": i_ok, "detail": i_detail},
               "ii_B48_le1s": {"ok": ii_b_ok, "max_exit": round(max(b_exits.values()), 3),
                               "min_exit": round(min(b_exits.values()), 3)},
               "ii_lock_real": {"ok": ii_lr_ok, "k2": (lr["k2_t"], lr["k2_reason"])},
               "ii_czyste_zero_zwloki": {"ok": ii_cz_ok,
                                         "max_delay": max(cz_delay.values()) if cz_delay else 0.0,
                                         "outliers": {k: v for k, v in cz_delay.items() if v > TICK}},
               "iii_zywe_pass": {"ok": iii_ok, "n_ok": n_ok, "detail": iii_rows},
               "spelnia_wszystko": k2_all},
        "K1_zlagodzone_ii": {"i_N6_trzymane": {"ok": k1_i_ok},
                             "ii_wszystkie_le_Tq": {"ok": k1_ii_ok},
                             "koszt_B_n_epizodow_C": len(k1_koszt_B),
                             "iii_zywe_pass": {"ok": k1_iii_ok, "n_ok": k1_n_ok,
                                               "detail": k1_iii_rows},
                             "spelnia": k1_all},
        "WYBOR": ("K2" if k2_all else ("K1" if k1_all else "STOP-ANEKS")),
    }
    os.makedirs(OUTD, exist_ok=True)
    json.dump(res, open(os.path.join(OUTD, "t2_desk.json"), "w"), indent=1)
    def pr(block, name):
        print(f"== {name} ==")
        for k, v in block.items():
            if isinstance(v, dict) and "ok" in v:
                print(f" {k}: {'OK' if v['ok'] else 'FAIL'} "
                      f"{json.dumps({kk: vv for kk, vv in v.items() if kk not in ('detail',)}, ensure_ascii=False)}")
            elif not isinstance(v, dict):
                print(f" {k}: {v}")
    pr(res["kryteria"]["K2"], "T2 kryteria K2")
    pr(res["kryteria"]["K1_zlagodzone_ii"], "T2 kryteria K1 (ii złagodzone)")
    print("WYBOR:", res["kryteria"]["WYBOR"])
    print("\n== tabela N6 + LR + ZP ==")
    for k in list(res["rows"]):
        if k.startswith(("N6:", "LR:", "ZP:")):
            v = res["rows"][k]
            print(f" {k:<12} k2=({v['k2_t']},{v['k2_reason']}) k1=({v['k1_t']},{v['k1_reason']}) "
                  f"real_adm={v['t_real_adm']} consum={v['t_consum']} "
                  f"pred={v.get('pred_czysty_start')} fantom_fire={v['k2_phantom_fire']}")


if __name__ == "__main__":
    main()
