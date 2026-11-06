#!/usr/bin/env python3
"""results/KONT/tools/kont_s2_freeze_bf.py — ANEKS_KONT-2b §3.1: kopia kont_s2_freeze_g.py (oryginał nietknięty), Δ wyłącznie z zejść sondy (lista lotów argumentem), ε_b ze wszystkich ważnych, stara Δ obok; każdy lot z listy musi być ważny; wyjście s2_freeze_bf.json. Użycie: kont_s2_freeze_bf.py <lot> [<lot> ...]. Oryginał: kopia kont_s2_freeze.py ze strażnikiem ANEKS_KONT-1b §2.4: n_ważnych < 8 ⇒ odmowa, kod wyjścia 2, brak zapisu. Oryginał: reguła PRE_KONT §3 literalnie (PROMPT_KONT_S2 §S2.1). Liczby NIE są zamrożone tym plikiem: zamraża je ANEKS_KONT-2.
ε_b(0⁺) = 1.5 × max p95 nominału (R-1b); ε_b(k) = 1.5 × max po ważnych lotach ε w koszyku [k, k+1), k ≥ 0, obwiednia niemalejąca od ε_b(0⁺).
Δ_D5 = 1.5 × max Δ. T* = największe t ≤ 70 przy ε_b(t) + Δ_D5 ≤ 5.79; koszyk k obowiązuje na [k, k+1), więc T* podane jako k+1 (koniec ostatniego dopuszczalnego koszyka), obok k.
Utrata xy_valid lub nav≠14 po odcięciu w locie ważnym ⇒ T* ≤ chwila utraty. Koszyk bez danych dalej niż lot: pokrywa go tylko to, co zmierzono; brak danych ⇒ koniec krzywej.
R_nom = 32 − 2.85 − ε_b(0⁺) − Δ_D5. Koszt = scenariusze z r4_margin.json z r_max > R_nom. Wyjście: results/KONT/s2/s2_freeze.json"""
import glob
import json
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
R_E, D_STOP, M_P50, T_MAX = 32.0, 2.85, 5.79, 70
R_P50 = 11.0
N_MIN = 8


def main():
    fl = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(ROOT, "results/KONT/s2/*/wyniki.json")))]
    val = [f for f in fl if f.get("wazny")]
    if len(val) < N_MIN:
        print(f"ODMOWA: n_ważnych = {len(val)} < {N_MIN} (PRE_KONT §3, ANEKS_KONT-1b §2.4), s2_freeze.json nie zapisany", file=sys.stderr)
        sys.exit(2)
    e0 = 1.5 * max(f["eps0_p95_nominal"] for f in val)
    loty = sys.argv[1:]
    sonda = [f for f in val if f["boot"] in loty]
    if not loty or len(sonda) != len(loty):
        print(f"ODMOWA: lista sondy {loty}, ważne z listy {[f['boot'] for f in sonda]}", file=sys.stderr)
        sys.exit(3)
    dmax = max(f["delta_max"] for f in sonda)
    dstara = max(f["delta_max"] for f in val if f["boot"] not in loty)
    D = 1.5 * dmax
    kmax = min(T_MAX, max(max(int(k) for k in f["koszyki"]) for f in val) + 1)
    raw, env = [], []
    cur = e0
    for k in range(kmax):
        vs = [f["koszyki"][str(k)] for f in val if str(k) in f["koszyki"]]
        b = 1.5 * max(vs) if vs else None
        raw.append(None if b is None else round(b, 3))
        if b is None:
            break
        cur = max(cur, b)
        env.append(round(cur, 3))
    ok = [k for k, v in enumerate(env) if v + D <= M_P50]
    # dopuszczalny tylko spójny prefiks obwiedni (niemalejąca, więc ok jest prefiksem)
    k_last = ok[-1] if ok else None
    t_star = (k_last + 1) if ok else 0
    loss = [t for f in val for t in (f.get("t_xy_utrata_s"), f.get("t_nav_utrata_s")) if t is not None]
    cap = min(loss) if loss else None
    if cap is not None:
        t_star = min(t_star, cap)
    r_nom = R_E - D_STOP - e0 - D
    tab = json.load(open(os.path.join(ROOT, "results/KONT_RECON/r4_margin.json")))["tabela_scenariuszy"]
    over = {k: v["r_max"] for k, v in tab.items() if v["r_max"] > r_nom}
    res = {"loty_sondy": loty, "delta_per_zejscie_sondy": {f["boot"]: f["delta_max"] for f in sonda}, "delta_stara_max": round(dstara, 3), "delta_D5_stara": round(1.5 * dstara, 3), "n_lotow": len(fl), "n_waznych": len(val), "loty_wazne": [f["boot"] for f in val], "eps_b_0plus": round(e0, 3), "p95_nominal_max": round(e0 / 1.5, 3), "delta_max": round(dmax, 3), "delta_D5": round(D, 3),
           "eps_b_surowa": raw, "eps_b_obwiednia": env, "m_p50": M_P50, "T_star_s": t_star, "k_ostatni_koszyk": k_last, "cap_utrata_s": cap, "R_nom": round(r_nom, 3), "koszt_bariery_scenariusze": len(over), "koszt_lista": over, "n_scen": len(tab),
           "smierc_Tstar_lt_10": t_star < 10, "smierc_Rnom_lt_11": r_nom < R_P50, "p_kont_3_Tstar_ge_30": t_star >= 30, "p_kont_4_koszt_0": len(over) == 0}
    json.dump(res, open(os.path.join(ROOT, "results/KONT/s2/s2_freeze_bf.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in res.items() if k not in ("eps_b_surowa",)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
