#!/usr/bin/env python3
"""results/TRANSIT_RECON/tools/transit_r2.py — R2 PROMPT_TRANSIT_S0: próg konwersji t*
per epizod T6 + kontrole.

t* = NAJPÓŹNIEJSZA akwizycja [s od t0], przy której idealny pościgowiec metody
R1-POSCIG (poscig_recon.feas_one — READ-ONLY import; koperta |v_cmd|≤3.0
r01/config.py:24; werdykt LITERĄ zamrożonego sędziego 8ec0fcfb na GT z manifestu —
wolnym od tranzientu teleportu, świadek erratum zliczony w R1 OBOK) jeszcze domyka D6.
Prefix do t_start = REALNE GT drona (ślepy zawis w hold) — sędzia widzi prawdziwy
ślepy początek, w tym ewentualny breach d_min przed startem pościgu.

Metoda: skan zgrubny 0.5 s na [0, 35], potem bisekcja do 0.05 s na ostatniej granicy
PASS→FAIL (t* = ostatni PASS przed PIERWSZYM FAIL — przy ogonie wynik bywa
niemonotoniczny na pojedynczych siatkach; raportujemy też pełną listę PASS-wysp).
Prowadzenie OGON (POSCIG R1: intercept nie zmienia werdyktów); intercept liczony
kontrolnie w t* (kolumna obok).

Osobno: czy wcześniejsza akwizycja ELIMINUJE bliskie przejście — d_min_m symulacji
przy starcie t* i przy starcie t_acq kontroli; kontrole realne (orbit przy przejściu)
z R1. Wyjście: results/TRANSIT_RECON/r2_tstar.json.
"""
import json
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
for p in (ROOT, os.path.join(ROOT, "results", "POSCIG_RECON", "tools")):
    if p not in sys.path:
        sys.path.insert(0, p)

from poscig_recon import Episode, feas_one, _SCEN   # READ-ONLY (metoda POSCIG R1)

OUTD = os.path.join(ROOT, "results", "TRANSIT_RECON")

T6 = ["c08_s03", "c08_s04", "c10_s02", "c11_s02", "c11_s03", "c11_s04"]
CTRL = ["c08_s01", "c08_s02", "c09_s03", "c09_s04", "c10_s01", "c10_s04"]


def t_star(epi, guidance="ogon"):
    """Zwraca (t*, wynik@t*, pierwszy_FAIL_po, wyspy) — ostatni PASS przed pierwszym FAIL."""
    grid = [x * 0.5 for x in range(0, 71)]            # 0..35 s
    res = []
    for t in grid:
        r = feas_one(epi, t, guidance)
        res.append((t, r))
    passes = [t for t, r in res if r["success_D6"]]
    if not passes:
        return None, None, (res[0][0], res[0][1]["fail_reasons"]), []
    # pierwszy FAIL po pierwszym PASS
    first_fail = next(((t, r["fail_reasons"]) for t, r in res
                       if t > passes[0] and not r["success_D6"]), None)
    if first_fail is None:
        t_lo = passes[-1]
        return t_lo, dict(res[[t for t, _ in res].index(t_lo)][1]), None, passes
    # bisekcja [ostatni PASS przed first_fail, first_fail]
    t_lo = max(t for t in passes if t < first_fail[0])
    t_hi = first_fail[0]
    r_lo = next(r for t, r in res if t == t_lo)
    while t_hi - t_lo > 0.05:
        tm = (t_lo + t_hi) / 2
        rm = feas_one(epi, tm, guidance)
        if rm["success_D6"]:
            t_lo, r_lo = tm, rm
        else:
            t_hi = tm
    # wyspy PASS po t_hi (uczciwość: niemonotoniczność raportowana, nie używana)
    islands = [t for t in passes if t > t_hi]
    return round(t_lo, 2), r_lo, (round(t_hi, 2), None), islands


def main():
    os.makedirs(OUTD, exist_ok=True)
    out = {"metoda": "feas_one POSCIG R1 (ogon; prefix=realne GT drona; sędzia FROZEN "
                     "8ec0fcfb na manifeście — świadek erratum w R1 obok)",
           "episodes": []}
    for grp, lst in (("T6", T6), ("CTRL", CTRL)):
        for sid in lst:
            epi = Episode("FANTOM_S2", "V2", sid)
            ts, r_at, ff, islands = t_star(epi, "ogon")
            row = {"sid": sid, "group": grp, "v_intr": _SCEN[sid]["cell"]["v_intr"],
                   "t_acq_real_s": (round(epi.t_acq, 2) if epi.t_acq is not None else None),
                   "t_star_s": ts,
                   "at_t_star": ({"d_min_m": r_at["d_min_m"], "sweep": r_at["sweep_deg"],
                                  "frac": r_at["frac_band"], "t_entry": r_at["t_entry_s"]}
                                 if r_at else None),
                   "pierwszy_FAIL_po_s": (ff[0] if ff else None),
                   "wyspy_PASS_po": islands,
                   "deficyt_akwizycji_s": (round(epi.t_acq - ts, 2)
                                           if (ts is not None and epi.t_acq is not None) else None),
                   "intercept_w_t_star": None, "sim_od_t_acq_real": None}
            if ts is not None:
                ri = feas_one(epi, ts, "intercept")
                row["intercept_w_t_star"] = {"success_D6": ri["success_D6"],
                                             "fail_reasons": ri["fail_reasons"]}
            if epi.t_acq is not None:
                rr = feas_one(epi, epi.t_acq, "ogon")
                row["sim_od_t_acq_real"] = {"success_D6": rr["success_D6"],
                                            "fail_reasons": rr["fail_reasons"],
                                            "d_min_m": rr["d_min_m"]}
            out["episodes"].append(row)
            print(f"[R2] {grp} {sid} t_acq={row['t_acq_real_s']} t*={ts} "
                  f"(dalej FAIL od {row['pierwszy_FAIL_po_s']}; wyspy {islands}) "
                  f"deficyt={row['deficyt_akwizycji_s']} "
                  f"dmin@t*={row['at_t_star']['d_min_m'] if row['at_t_star'] else None} "
                  f"int@t*={row['intercept_w_t_star']}")
    json.dump(out, open(os.path.join(OUTD, "r2_tstar.json"), "w"), indent=1)
    print("zapisano r2_tstar.json")


if __name__ == "__main__":
    main()
