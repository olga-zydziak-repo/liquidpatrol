#!/usr/bin/env python3
"""results/NAD3_RECON/tools/nad3_r7.py — PROMPT_NAD3_S0 R7: trzy punkty kandydackie do lotów, przewidywanie z replayu (0 bootów).

Promień zadania r = 20 m (droga R2: intruz bliżej środka; jedyny zapisany lot z r_max ≤ 20 m to c05_s01_r2, 19.594 m — replay
na nim; pozostałe 12 lotów z r_max 21.7–25.6 m liczone dla porównania: przy r_lotu > r zadania odmowa osłony jest oczekiwana).
Granice z rachunku R1 przy τ_proj (nad3_r4.TAU_PROJ), F_zn najgorsze 0.4527, G z tabeli r5 i świeże G z NAD2 (r1_wymagania.json):
  bezpieczeństwo (a): E_s = (m − Δ_D5)/1.5 − G − F_zn;  dostępność (a): E_d = (m − Δ_D5 − 1.5·(F_zn + G))/2.5.
Powierzchnia E_s / E_d przy τ_proj dla r 14–27 m × (f, K) z FK (wariant a) — „powierzchnia_tau_proj”.
Punkty: P1 (zapas) 4 Hz, K = 0, E = 1.0; P2 (granica) 1 Hz, K = 1, E = 1.0; P3 (nad) 1 Hz, K = 1, E = 2.0. Modele jak R4, ziarna
1–3 dla modeli losowych. Wyjście: results/NAD3_RECON/r7_kandydaci.json.
"""
import json
import os
import sys

sys.path[:0] = ["/home/olga/projects/liquidpatrol", os.path.dirname(os.path.abspath(__file__))]
import nad3_dane as N
import nad3_r4 as R

R_ZAD = 20.0
PUNKTY = [("P1_zapas", 4, 0, 1.0), ("P2_granica", 1, 1, 1.0), ("P3_nad", 1, 1, 2.0)]


def granice(r, f, K, G_swieze):
    tab = R.tabela_deg(f, K, 0.0, "a")
    m = R.R_E - R.NS.D_STOP - r
    out = {}
    for lab, g in (("G_tabela", R.G_X[tab["i_max"]]), ("G_NAD2", G_swieze[str(R.KRAW_X[tab["i_max"]])]["G"])):
        out[lab] = {"G": g, "E_s": round((m - R.NS.DELTA_D5) / 1.5 - g - R.F_ZN_WORST, 3),
                    "E_d": round((m - R.NS.DELTA_D5 - 1.5 * (R.F_ZN_WORST + g)) / 2.5, 3)}
    out["tau_proj"], out["tau_star"], out["przedzial"] = tab["tau_max"], tab["tau_star"], tab["i_max"]
    return out


def main():
    G_sw = json.load(open(os.path.join(N.OUT, "r1_wymagania.json")))["G_NAD2_swieze"]["krawedzie"]
    loty = [N.wczytaj(*x) for x in N.loty()]
    R.tau_proj(loty)
    out = {"r_zadania": R_ZAD, "tau_proj": {f"f{f}_K{K}": v for (f, K), v in R.TAU_PROJ.items()},
           "powierzchnia_tau_proj": {f"r{r}_f{f}_K{K}": granice(float(r), f, K, G_sw) for r in range(14, 28) for f, K in R.FK},
           "punkty": {}}
    for nm, f, K, E in PUNKTY:
        o = {"f": f, "K": K, "E_max": E, "granice_r20": granice(R_ZAD, f, K, G_sw), "replay": {}}
        for L in loty:
            rows = []
            for mn, mc in R.MODELE:
                for z in ((1, 2, 3) if mn in ("bialy", "wolny_2s", "wolny_10s") else (1,)):
                    m = R.przebieg(L, dict(mc, E_max=E, f=f, K=K, ziarno=z), R.tabela_deg(f, K, E, "a"))
                    m.pop("skok")
                    rows.append({"model": mn, "ziarno": z, **m})
            o["replay"][L.nazwa] = {"n_przebiegow": len(rows), "refuse_misja": sum(r["refuse_misja"] for r in rows),
                                    "przyczyny": sorted(set(str(r["przyczyna"]) for r in rows if r["refuse_misja"])),
                                    "e_gt_U": sum(r["e_gt_U"] for r in rows), "max_e_do_U": max(r["max_e_do_U"] for r in rows),
                                    "zapas_oslony_min": min((r["zapas_oslony_min"] for r in rows if r["zapas_oslony_min"] is not None),
                                                            default=None),
                                    "per_model": {f'{r["model"]}/{r["ziarno"]}': [r["refuse_misja"], r["przyczyna"], r["t_refuse_od_flagi"],
                                                                                   r["max_e_do_U"], r["zapas_oslony_min"]] for r in rows}}
        out["punkty"][nm] = o
        c = o["replay"]["c05_s01_r2"]
        print(nm, o["granice_r20"], "c05_s01:", c["refuse_misja"], "/", c["n_przebiegow"], c["przyczyny"], c["max_e_do_U"],
              c["zapas_oslony_min"], "| inne loty z REFUSE:", sum(1 for k, v in o["replay"].items() if v["refuse_misja"]), flush=True)
    json.dump(out, open(os.path.join(N.OUT, "r7_kandydaci.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
