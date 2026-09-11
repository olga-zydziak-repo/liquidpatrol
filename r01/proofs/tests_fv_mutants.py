#!/usr/bin/env python3
"""r01/proofs/tests_fv_mutants.py — M-krok: mutanty lustra vs produkcja (ANEKS_FV-1 §5, PROMPT_FV_S2 §2).

Dowodzi ADEKWATNOŚCI różnicówki: dla KAŻDEGO z 27 mutantów (katalog `results/FV/MUTANTY.md`, prereg CM1)
istnieje ≥1 rozbieżność mutant-lustro↔PRODUKCJA na siatce/fuzz (te same ziarna {0..4} i liczności co S1).
Mutacje WYŁĄCZNIE tu, w pamięci; `fv_mirror.py` na dysku NIETKNIĘTY (import produkcji dozwolony).
Wyjątek mutanta (crash) też liczy się jako WYKRYCIE (zachowanie ≠ produkcja).

Uruchom: PYTHONPATH=.certdeps python3 -m r01.proofs.tests_fv_mutants run
         python3 -m pytest r01/proofs/tests_fv_mutants.py -q
"""
from __future__ import annotations
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(_HERE))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from r01.proofs import fv_mirror as M
from r01.proofs.tests_fv_diff import (
    _load_grid, _fuzz_cases, FUZZ_SEEDS,
    prod_braking, prod_geofence, prod_pos_seq, prod_d5_seq,
)


# ============================ MUTANTY (in-memory) ============================
def mut_braking(vel, th, mut):
    hyp = math.hypot(float(vel[0]), float(vel[1]))
    v_max, a_brake = th["v_max"], th["a_brake"]
    vh = max(hyp, v_max) if mut == "bd_clamp_min_max" else min(hyp, v_max)
    return (vh * vh) / (2.0 * a_brake)


def mut_geofence(pos, vel, target, th, mut):
    r_e, v_e, v_max, a_brake = th["r_e"], th["v_e"], th["v_max"], th["a_brake"]
    tr = math.hypot(float(target[0]), float(target[1]))
    pr = math.hypot(float(pos[0]), float(pos[1]))
    brake = mut_braking(vel, th, "none")           # clean braking (mutacja bd osobno)
    tz, pz = abs(float(target[2])), abs(float(pos[2]))

    if mut == "gf_re_strict":
        c_re = tr >= r_e
    elif mut == "gf_neg_re":
        c_re = not (tr > r_e)
    else:
        c_re = tr > r_e

    if mut == "gf_pr_strict":
        c_pr = pr + brake >= r_e
    elif mut == "gf_neg_pr":
        c_pr = not (pr + brake > r_e)
    else:
        c_pr = pr + brake > r_e

    vet = (tz >= v_e) if mut == "gf_vet_strict" else (tz > v_e)
    vep = (pz >= v_e) if mut == "gf_vep_strict" else (pz > v_e)
    if mut == "gf_neg_ve":
        c_ve = not ((tz > v_e) or (pz > v_e))
    else:
        c_ve = vet or vep

    d_re = f"cel poza R_E ({tr:.1f}>{r_e:.0f})"
    d_pr = f"pozycja+hamowanie poza R_E ({pr:.1f}+brake>{r_e:.0f})"
    d_ve = f"pion poza V_E (>{v_e:.0f})"
    order = [(c_re, d_re), (c_pr, d_pr), (c_ve, d_ve)]
    if mut == "gf_swap_re_pr":
        order = [(c_pr, d_pr), (c_re, d_re), (c_ve, d_ve)]
    elif mut == "gf_swap_pr_ve":
        order = [(c_re, d_re), (c_ve, d_ve), (c_pr, d_pr)]
    for cond, det in order:
        if cond:
            return True, det
    return False, None


def mut_pos_step(st, flag, deb, hyst, mut):
    if flag is None:
        return st
    deb_thr = deb
    if mut == "pm_deb_plus1":
        deb_thr = deb + 1
    elif mut == "pm_deb_minus1":
        deb_thr = deb - 1
    hyst_thr = hyst
    if mut == "pm_hyst_plus1":
        hyst_thr = hyst + 1
    elif mut == "pm_hyst_minus1":
        hyst_thr = hyst - 1
    inc = 2 if mut == "pm_badinc2" else 1

    branch = flag
    if mut in ("pm_neg_flag", "pm_swap_branches"):
        branch = not flag

    if branch:
        st["pos_bad"] += inc
        st["pos_healthy"] = 0
        deb_hit = (st["pos_bad"] > deb_thr) if mut == "pm_deb_strict" else (st["pos_bad"] >= deb_thr)
        refuse_guard = st["pos_refuse"] if mut == "pm_neg_refuse_guard" else (not st["pos_refuse"])
        if deb_hit and refuse_guard:
            st["pos_refuse"] = True
            st["n_pos_enter"] += 1
    else:
        st["pos_bad"] = 0
        exit_guard = (not st["pos_refuse"]) if mut == "pm_neg_refuse_exit" else st["pos_refuse"]
        if exit_guard:
            st["pos_healthy"] += 1
            hyst_hit = (st["pos_healthy"] > hyst_thr) if mut == "pm_hyst_strict" else (st["pos_healthy"] >= hyst_thr)
            if hyst_hit:
                st["pos_refuse"] = False
                st["pos_healthy"] = 0
    return st


def mut_sd_step(st, now, cfg, mut):
    events = []
    init_guard = st["descending"] if mut == "sd_neg_descending" else (not st["descending"])
    if init_guard:
        st["descending"] = True
        st["desc_t0"] = now
        events.append("refuse_pos_land")
    el = now - st["desc_t0"]
    fast_cond = (el <= cfg["desc_fast_dur"]) if mut == "sd_fast_strict" else (el < cfg["desc_fast_dur"])
    if fast_cond:
        vdesc = cfg["v_desc_land"] if mut == "sd_swap_phase" else cfg["v_desc_fast"]
    else:
        hsw_guard = st["h_switched"] if mut == "sd_neg_hswitch" else (not st["h_switched"])
        if hsw_guard:
            events.append("h_switch")
            st["h_switched"] = True
        vdesc = cfg["v_desc_fast"] if mut == "sd_swap_phase" else cfg["v_desc_land"]
    touchdown = False
    td_cond = (el > cfg["desc_total"]) if mut == "sd_total_strict" else (el >= cfg["desc_total"])
    td_guard = st["td"] if mut == "sd_neg_td" else (not st["td"])
    if td_cond and td_guard:
        events.append("touchdown")
        st["td"] = True
        touchdown = True
    return vdesc, events, touchdown, st


# ============================ MAPY / KATALOG ================================
MUT_FN = {}
for m in ["bd_clamp_min_max"]:
    MUT_FN[m] = "braking"
for m in ["gf_re_strict", "gf_pr_strict", "gf_vet_strict", "gf_vep_strict",
          "gf_neg_re", "gf_neg_pr", "gf_neg_ve", "gf_swap_re_pr", "gf_swap_pr_ve"]:
    MUT_FN[m] = "geofence"
for m in ["pm_deb_strict", "pm_hyst_strict", "pm_deb_plus1", "pm_deb_minus1",
          "pm_hyst_plus1", "pm_hyst_minus1", "pm_badinc2", "pm_neg_flag",
          "pm_neg_refuse_guard", "pm_neg_refuse_exit", "pm_swap_branches"]:
    MUT_FN[m] = "pos_monitor"
for m in ["sd_fast_strict", "sd_total_strict", "sd_neg_descending",
          "sd_neg_hswitch", "sd_neg_td", "sd_swap_phase"]:
    MUT_FN[m] = "safe_descend"

ALL_MUTANTS = list(MUT_FN.keys())


# ============================ WYKRYWANIE ===================================
def _mir_pos_seq(flags, th, mut):
    st = M.new_pos_state()
    out = []
    for f in flags:
        mut_pos_step(st, f, th["debounce_ticks"], th["hyst_ticks"], mut)
        out.append((st["pos_bad"], st["pos_healthy"], st["pos_refuse"], st["n_pos_enter"]))
    return out


def _mir_d5_seq(nows, cfg, mut):
    st = M.new_descend_state()
    out = []
    for now in nows:
        v, e, td, st = mut_sd_step(st, now, cfg, mut)
        out.append((v, tuple(e), td, dict(st)))
    return out


def detect(mut):
    """Zwraca (warstwa, lokalizacja) pierwszej rozbieżności LUB None (mutant przeżył)."""
    th = M.shield_thresholds()
    d5 = M.d5_cfg()
    grid = _load_grid()
    fn = MUT_FN[mut]

    def diff_one(kind, case):
        try:
            if kind == "braking":
                return mut_braking(case, th, mut) != prod_braking(case)
            if kind == "geofence":
                return mut_geofence(case["pos"], case["vel"], case["target"], th, mut) != \
                       prod_geofence(case["pos"], case["vel"], case["target"])
            if kind == "pos_monitor":
                return _mir_pos_seq(case, th, mut) != prod_pos_seq(case)
            if kind == "safe_descend":
                return _mir_d5_seq(case, d5, mut) != prod_d5_seq(case, d5)
        except Exception:
            return True          # crash mutanta = wykrycie
        return False

    grid_key = {"braking": "braking_dist", "geofence": "geofence",
                "pos_monitor": "pos_monitor", "safe_descend": "safe_descend"}[fn]
    for i, case in enumerate(grid[grid_key]):
        if diff_one(fn, case):
            return ("siatka", f"{grid_key}#{i}")
    for seed in FUZZ_SEEDS:
        for j, case in enumerate(_fuzz_cases(fn if fn != "braking" else "braking", seed)):
            if diff_one(fn, case):
                return ("fuzz", f"seed{seed}#{j}")
    return None


# ============================== PYTEST ======================================
def _identity_divergences():
    """Szablony mutantów z mut='none' vs produkcja na CAŁEJ siatce (wierność szablonu = 0)."""
    th = M.shield_thresholds()
    d5 = M.d5_cfg()
    grid = _load_grid()
    bad = []
    for v in grid["braking_dist"]:
        if mut_braking(v, th, "none") != prod_braking(v):
            bad.append(("braking", v))
    for c in grid["geofence"]:
        if mut_geofence(c["pos"], c["vel"], c["target"], th, "none") != \
           prod_geofence(c["pos"], c["vel"], c["target"]):
            bad.append(("geofence", c))
    for s in grid["pos_monitor"]:
        if _mir_pos_seq(s, th, "none") != prod_pos_seq(s):
            bad.append(("pos_monitor", s))
    for s in grid["safe_descend"]:
        if _mir_d5_seq(s, d5, "none") != prod_d5_seq(s, d5):
            bad.append(("safe_descend", s))
    return bad


def test_identity_no_divergence():
    """Wierność szablonu: mut='none' = 0 rozbieżności vs produkcja (inaczej „wykrycia" są artefaktem)."""
    assert _identity_divergences() == [], _identity_divergences()


def test_all_27_mutants_detected():
    survivors = [m for m in ALL_MUTANTS if detect(m) is None]
    assert len(ALL_MUTANTS) == 27, len(ALL_MUTANTS)
    assert survivors == [], f"mutanty PRZEŻYŁY (luka pokrycia): {survivors}"


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        print(f"=== M-krok: {len(ALL_MUTANTS)} mutantów, oracle=produkcja ===")
        idbad = _identity_divergences()
        print(f"identity (none): {'OK 0-div' if not idbad else 'ROZJAZD! '+str(idbad[:3])}")
        survivors = []
        for m in ALL_MUTANTS:
            d = detect(m)
            if d is None:
                survivors.append(m)
                print(f"  PRZEŻYŁ  {m:22s} ({MUT_FN[m]})")
            else:
                print(f"  WYKRYTY  {m:22s} ({MUT_FN[m]:12s}) ← {d[0]}:{d[1]}")
        print(f"\nWYKRYTE {len(ALL_MUTANTS)-len(survivors)}/{len(ALL_MUTANTS)}"
              f"{' — 100%' if not survivors else ''}")
        if survivors:
            print(f"PRZEŻYLI: {survivors}  → grid2 (commit przed ponownym biegiem)")
        return
    print("użycie: run")


if __name__ == "__main__":
    main()
