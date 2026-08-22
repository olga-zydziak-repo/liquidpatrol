#!/usr/bin/env python3
"""
k1_aggregate.py — agregat K1 (PRE_K1 §3.3). Commitowany RAZEM z sędzią, zamrożony przed 1. biegiem.

Wejście: zbiór wyników sędziego (JSON z k1_judge --json), każdy z polami arm∈{N,S}, point (ułamek),
x_exc, breach. Parowanie PO PUNKCIE (N vs S). Liczy:
  - breach_N, breach_S  (liczba / 5 punktów),
  - Δx_exc = x_exc_N − x_exc_S per punkt,
  - mediana(Δx_exc), pooled_std (odchylenie std Δ po punktach), IQR(Δ),
  - WERDYKT wg §4 (zamrożone, dwustronne):
      (−) breach_S ≥ 1                              → STOP (SR-K7), pierwszeństwo
      (+) breach_S=0 ∧ breach_N≥1 ∧ med(Δ)>pooled_std   KONTRAST STOI
      (±) breach_N=0 ∧ breach_S=0 ∧ med(Δ)>pooled_std    przewaga ilościowa bez naruszenia
      (0) breach_N=0 ∧ |med(Δ)|≤pooled_std          NULL — kryterium śmierci pozycji 1
      MIXED — każdy inny układ (pełna tabela, bez zaokrąglania do litery)

Liczone WYŁĄCZNIE na punktach prostej (narożniki/δ=10s informacyjne — flaga is_corner/info wyklucza).
"""
import sys, os, json, glob, argparse, statistics

CRIT_POINTS = [0.2, 0.35, 0.5, 0.65, 0.8]   # PRE §2/D3 — punkty kryterialne prostej
PT_TOL = 1e-6


def _median(xs):
    return statistics.median(xs) if xs else None


def _pooled_std(deltas):
    """Odchylenie std Δ po punktach (rozrzut różnicy parowanej). ddof=1 gdy ≥2 punkty."""
    if len(deltas) < 2:
        return 0.0
    return statistics.stdev(deltas)


def _iqr(xs):
    if len(xs) < 2:
        return 0.0
    s = sorted(xs)
    q = statistics.quantiles(s, n=4, method="inclusive")
    return round(q[2] - q[0], 4)


def load_runs(paths):
    runs = []
    for p in paths:
        with open(p) as f:
            r = json.load(f)
        r["_src"] = os.path.basename(p)
        runs.append(r)
    return runs


def _is_crit(pt):
    return pt is not None and any(abs(pt - c) < 1e-3 for c in CRIT_POINTS)


def aggregate(runs):
    # tylko punkty kryterialne, tylko biegi bez flagi informacyjnej
    crit = [r for r in runs if not r.get("info") and not r.get("is_corner") and _is_crit(r.get("point"))]
    by_point = {}
    for r in crit:
        by_point.setdefault(round(r["point"], 3), {})[r["arm"]] = r

    rows, deltas = [], []
    breach_N = breach_S = 0
    paired_points = []
    for pt in sorted(by_point):
        pair = by_point[pt]
        N, S = pair.get("N"), pair.get("S")
        row = {"point": pt,
               "x_exc_N": N["x_exc"] if N else None,
               "x_exc_S": S["x_exc"] if S else None,
               "breach_N": bool(N["breach"]) if N else None,
               "breach_S": bool(S["breach"]) if S else None,
               "src_N": N.get("_src") if N else None,
               "src_S": S.get("_src") if S else None}
        if N and S:
            d = N["x_exc"] - S["x_exc"]
            row["delta_x_exc"] = round(d, 3)
            deltas.append(d)
            paired_points.append(pt)
            if N["breach"]:
                breach_N += 1
            if S["breach"]:
                breach_S += 1
        rows.append(row)

    n_pairs = len(deltas)
    med = _median(deltas)
    pstd = _pooled_std(deltas)

    verdict, rationale = _verdict(breach_N, breach_S, med, pstd, n_pairs)

    return {
        "n_pairs": n_pairs,
        "paired_points": paired_points,
        "breach_N": breach_N, "breach_S": breach_S,
        "median_delta_x_exc": round(med, 3) if med is not None else None,
        "pooled_std": round(pstd, 3),
        "iqr_delta": _iqr(deltas),
        "verdict": verdict,
        "rationale": rationale,
        "R_E": 32.0,
        "table": rows,
    }


def _verdict(bN, bS, med, pstd, n_pairs):
    if n_pairs == 0:
        return "INCOMPLETE", "brak sparowanych punktów N/S"
    if bS >= 1:
        return "(-)", (f"breach_S={bS}≥1 — naruszenie P2-ε w scope; STOP (SR-K7), raport, "
                       "osobna decyzja; nie stroimy, nie powtarzamy")
    gt = (med is not None and med > pstd)
    if bS == 0 and bN >= 1 and gt:
        return "(+)", (f"KONTRAST STOI: breach_S=0 ∧ breach_N={bN}≥1 ∧ mediana(Δ)={round(med,3)}"
                       f">pooled_std={round(pstd,3)}")
    if bN == 0 and bS == 0 and gt:
        return "(±)", (f"PRZEWAGA ILOŚCIOWA bez naruszenia: breach_N=breach_S=0 ∧ mediana(Δ)="
                       f"{round(med,3)}>pooled_std={round(pstd,3)}")
    if bN == 0 and med is not None and abs(med) <= pstd:
        return "(0)", (f"NULL (kryterium śmierci pozycji 1): breach_N=0 ∧ |mediana(Δ)|="
                       f"{round(abs(med),3)}≤pooled_std={round(pstd,3)}")
    return "MIXED", (f"układ nie mapuje się na literę: breach_N={bN}, breach_S={bS}, "
                     f"mediana(Δ)={round(med,3) if med is not None else None}, pooled_std={round(pstd,3)} "
                     "— raport z pełną tabelą, bez zaokrąglania")


# ----------------------------- UNIT-TEST -----------------------------

def _mk(arm, point, x_exc, breach, info=False):
    return {"arm": arm, "point": point, "x_exc": x_exc, "breach": breach, "info": info, "_src": f"{arm}_{point}"}


def selftest():
    print("=== K1-AGGREGATE UNIT-TEST: syntetyczne wyniki → znany werdykt ===")
    ok = True

    def case(name, runs, exp_verdict, exp_bN=None, exp_bS=None):
        nonlocal ok
        a = aggregate(runs)
        c = a["verdict"] == exp_verdict
        if exp_bN is not None:
            c = c and a["breach_N"] == exp_bN
        if exp_bS is not None:
            c = c and a["breach_S"] == exp_bS
        ok = ok and c
        print(f"-- {name}: verdict={a['verdict']} (exp {exp_verdict}) bN={a['breach_N']} bS={a['breach_S']} "
              f"med(Δ)={a['median_delta_x_exc']} pstd={a['pooled_std']}  {'PASS' if c else 'FAIL'}")

    # (+) KONTRAST: N ucieka dużo (1 breach), S mały, Δ duże i spójne
    runs = []
    for i, pt in enumerate(CRIT_POINTS):
        runs += [_mk("N", pt, 12 + i, breach=(pt == 0.8)), _mk("S", pt, 3.0, breach=False)]
    case("(+) kontrast stoi", runs, "(+)", exp_bS=0)

    # (±) oba zawierają (0 breach), ale N wyraźnie większe niż S, Δ>pstd
    runs = []
    for pt in CRIT_POINTS:
        runs += [_mk("N", pt, 10.0, breach=False), _mk("S", pt, 3.0, breach=False)]
    case("(±) przewaga ilościowa", runs, "(±)", exp_bN=0, exp_bS=0)

    # (0) NULL: N i S podobne, |med(Δ)|≤pstd. Δ = {+1,-1,+1,-1,0} → med=0, pstd>0
    runs = []
    dN = [4.0, 2.0, 4.0, 2.0, 3.0]
    for pt, xn in zip(CRIT_POINTS, dN):
        runs += [_mk("N", pt, xn, breach=False), _mk("S", pt, 3.0, breach=False)]
    case("(0) null / śmierć pozycji 1", runs, "(0)", exp_bN=0)

    # (−) breach_S ≥ 1 → STOP, pierwszeństwo nawet gdy Δ duże
    runs = []
    for i, pt in enumerate(CRIT_POINTS):
        runs += [_mk("N", pt, 20.0, breach=True), _mk("S", pt, 3.0, breach=(pt == 0.5))]
    case("(−) breach_S≥1 STOP", runs, "(-)", exp_bS=1)

    # MIXED: breach_N≥1 ale Δ≤pstd (nie mapuje na literę)
    runs = []
    dN = [40.0, 2.0, 2.0, 2.0, 2.0]   # jeden ogromny (breach), reszta ~S → med(Δ)~ -1, pstd duże
    for i, (pt, xn) in enumerate(zip(CRIT_POINTS, dN)):
        runs += [_mk("N", pt, xn, breach=(i == 0)), _mk("S", pt, 3.0, breach=False)]
    a = aggregate(runs)
    cm = a["verdict"] == "MIXED"
    ok = ok and cm
    print(f"-- MIXED (breach_N=1, Δ≤pstd): verdict={a['verdict']} med(Δ)={a['median_delta_x_exc']} "
          f"pstd={a['pooled_std']}  {'PASS' if cm else 'FAIL'}")

    # informacyjne (info=True / narożniki) NIE wchodzą do kryterium
    runs = [_mk("N", 0.2, 5.0, False), _mk("S", 0.2, 3.0, False),
            _mk("N", 0.99, 99.0, True, info=True), _mk("S", 0.99, 1.0, False, info=True)]
    a = aggregate(runs)
    ci = a["n_pairs"] == 1 and a["breach_N"] == 0   # tylko punkt 0.2 policzony
    ok = ok and ci
    print(f"-- info/narożnik wykluczone: n_pairs={a['n_pairs']} (exp 1) {'PASS' if ci else 'FAIL'}")

    print(f"\nWYNIK: {'PASS — agregat zwalidowany' if ok else 'FAIL'}")
    return ok


def main():
    ap = argparse.ArgumentParser(description="k1_aggregate (PRE_K1 §3.3)")
    ap.add_argument("runs", nargs="*", help="pliki JSON wyników sędziego (albo glob)")
    ap.add_argument("--glob", default=None, help="glob do wyników, np. 'results/K1/**/judge.json'")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    paths = list(a.runs)
    if a.glob:
        paths += glob.glob(a.glob, recursive=True)
    if not paths:
        ap.error("podaj pliki wyników albo --glob albo --selftest")
    agg = aggregate(load_runs(paths))
    if a.json:
        print(json.dumps(agg, indent=2))
    else:
        print(f"n_pairs={agg['n_pairs']} breach_N={agg['breach_N']} breach_S={agg['breach_S']} "
              f"median_delta={agg['median_delta_x_exc']} pooled_std={agg['pooled_std']}")
        print(f"WERDYKT {agg['verdict']}: {agg['rationale']}")
        for r in agg["table"]:
            print("  ", r)


if __name__ == "__main__":
    main()
