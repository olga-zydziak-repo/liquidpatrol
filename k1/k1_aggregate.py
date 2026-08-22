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

# ANEKS_K1-7 G2: progi checku parowania S↔N (ZAMROŻONE przed 1. biegiem N). Warstwa agregatu, NIE sędzia.
# Kinematyka wstrzyknięcia z manifest.inj_info (oba ramiona z EKF — spójny instrument). Niezgodność ⇒
# punkt NIESPAROWANY, oba loty jako diag, punkt liczy się ponownie w budżecie lotów.
PAIR_TOL = {"dr_m": 1.0, "dspeed_mps": 0.3, "dheading_deg": 10.0}


def _ang_diff(a, b):
    """Różnica kątów [deg] w [-180,180], wartość bezwzględna."""
    if a is None or b is None:
        return None
    d = (a - b + 180.0) % 360.0 - 180.0
    return abs(d)


def pairing_check(inj_N, inj_S, tol=PAIR_TOL):
    """G2: czy S i N wstrzyknięto w tym samym stanie kinematycznym. Zwraca (paired: bool, detail)."""
    if not inj_N or not inj_S:
        return None, {"reason": "brak inj_info dla jednego z ramion"}
    rN, rS = inj_N.get("r_est_ekf"), inj_S.get("r_est_ekf")
    vN, vS = inj_N.get("speed_h_ekf"), inj_S.get("speed_h_ekf")
    hN, hS = inj_N.get("heading_deg_ekf"), inj_S.get("heading_deg_ekf")
    dr = (abs(rN - rS) if (rN is not None and rS is not None) else None)
    dv = (abs(vN - vS) if (vN is not None and vS is not None) else None)
    dh = _ang_diff(hN, hS)
    dr_ok = (dr is not None and dr <= tol["dr_m"])
    dv_ok = (dv is not None and dv <= tol["dspeed_mps"])
    dh_ok = (dh is not None and dh <= tol["dheading_deg"])
    paired = bool(dr_ok and dv_ok and dh_ok)
    return paired, {"dr_m": (round(dr, 3) if dr is not None else None), "dr_ok": dr_ok,
                    "dspeed_mps": (round(dv, 3) if dv is not None else None), "dspeed_ok": dv_ok,
                    "dheading_deg": (round(dh, 3) if dh is not None else None), "dheading_ok": dh_ok,
                    "tol": tol, "paired": paired}


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


def aggregate(runs, inj_by=None):
    """inj_by (opc.): {(round(point,3), arm): inj_info} z manifestów → check parowania G2.
    Punkt niesparowany kinematycznie jest WYKLUCZANY z kryterium (oba loty → diag, punkt do powtórki)."""
    # tylko punkty kryterialne, tylko biegi bez flagi informacyjnej
    crit = [r for r in runs if not r.get("info") and not r.get("is_corner") and _is_crit(r.get("point"))]
    by_point = {}
    for r in crit:
        by_point.setdefault(round(r["point"], 3), {})[r["arm"]] = r

    rows, deltas = [], []
    breach_N = breach_S = 0
    paired_points = []
    unpaired_points = []
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
        # G2: check parowania kinematycznego (jeśli mamy inj_info obu ramion)
        pcheck = None
        if inj_by is not None and N and S:
            paired, pdetail = pairing_check(inj_by.get((pt, "N")), inj_by.get((pt, "S")))
            pcheck = pdetail
            row["pairing"] = pdetail
        if N and S:
            kinematically_paired = (pcheck is None) or bool(pcheck.get("paired"))  # brak inj_by ⇒ nie egzekwuj
            if not kinematically_paired:
                row["excluded"] = "unpaired-kinematics"      # oba loty → diag, punkt do powtórki
                unpaired_points.append(pt)
            else:
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
        "unpaired_points": unpaired_points,
        "breach_N": breach_N, "breach_S": breach_S,
        "median_delta_x_exc": round(med, 3) if med is not None else None,
        "pooled_std": round(pstd, 3),
        "iqr_delta": _iqr(deltas),
        "verdict": verdict,
        "rationale": rationale,
        "R_E": 32.0,
        "pairing_tol": PAIR_TOL,
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

    # G2: check parowania — progi zamrożone
    def _inj(r, v, h):
        return {"r_est_ekf": r, "speed_h_ekf": v, "heading_deg_ekf": h}
    paired, det = pairing_check(_inj(13.0, 3.7, 45.0), _inj(13.5, 3.5, 50.0))
    cp = (paired is True and det["dr_ok"] and det["dspeed_ok"] and det["dheading_ok"])
    ok = ok and cp
    print(f"-- G2 sparowane (dr .5≤1, dv .2≤.3, dh 5≤10): paired={paired} {'PASS' if cp else 'FAIL'}")
    paired, det = pairing_check(_inj(13.0, 3.7, 45.0), _inj(15.0, 3.5, 50.0))  # dr=2.0>1.0
    cu = (paired is False and det["dr_ok"] is False)
    ok = ok and cu
    print(f"-- G2 niesparowane (dr=2.0>1.0): paired={paired} {'PASS' if cu else 'FAIL'}")
    paired, det = pairing_check(_inj(13.0, 3.7, 10.0), _inj(13.2, 3.5, 25.0))  # dh=15>10
    cu2 = (paired is False and det["dheading_ok"] is False)
    ok = ok and cu2
    print(f"-- G2 niesparowane (dh=15>10): paired={paired} {'PASS' if cu2 else 'FAIL'}")
    # G2 integracja: niesparowany punkt WYKLUCZONY z kryterium (oba → diag)
    runs = [_mk("N", 0.2, 20.0, True), _mk("S", 0.2, 3.0, False),
            _mk("N", 0.5, 10.0, False), _mk("S", 0.5, 3.0, False)]
    inj_by = {(0.2, "N"): _inj(13.0, 3.7, 45.0), (0.2, "S"): _inj(18.0, 3.5, 50.0),   # dr=5 → unpaired
              (0.5, "N"): _inj(14.0, 3.1, 200.0), (0.5, "S"): _inj(14.2, 3.0, 201.0)}  # paired
    a = aggregate(runs, inj_by=inj_by)
    ce = (a["unpaired_points"] == [0.2] and a["n_pairs"] == 1 and a["breach_N"] == 0)  # 0.2 wykluczony
    ok = ok and ce
    print(f"-- G2 integracja: unpaired={a['unpaired_points']} n_pairs={a['n_pairs']} bN={a['breach_N']} "
          f"(0.2 wykluczony, breach N z 0.2 nie liczony) {'PASS' if ce else 'FAIL'}")

    print(f"\nWYNIK: {'PASS — agregat zwalidowany' if ok else 'FAIL'}")
    return ok


def main():
    ap = argparse.ArgumentParser(description="k1_aggregate (PRE_K1 §3.3)")
    ap.add_argument("runs", nargs="*", help="pliki JSON wyników sędziego (albo glob)")
    ap.add_argument("--glob", default=None, help="glob do wyników, np. 'results/K1/**/judge.json'")
    ap.add_argument("--manifests", default=None, help="glob do manifestów (inj_info → check parowania G2)")
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
    # G2: inj_info z manifestów (tylko biegi ważne — run_valid nie False) keyed po (point, arm)
    inj_by = None
    if a.manifests:
        inj_by = {}
        for mp in glob.glob(a.manifests, recursive=True):
            try:
                m = json.load(open(mp))
            except Exception:
                continue
            if m.get("run_valid") is False:      # niesparuj z lotem diag/invalid
                continue
            pt, arm, inj = m.get("point"), m.get("arm"), m.get("inj_info")
            if pt is not None and arm and inj:
                inj_by[(round(pt, 3), arm)] = inj
    agg = aggregate(load_runs(paths), inj_by=inj_by)
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
