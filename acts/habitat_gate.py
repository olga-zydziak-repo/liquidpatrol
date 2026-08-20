#!/usr/bin/env python3
"""acts/habitat_gate.py — ANEKS_D7 §7b/§7c: KRYTERIUM HABITATU per bieg (H1/H2/H3/H4).

Rewizja kryterium §5c/§6d (D7 §7a): stare porównywało bieg scenariuszowy do statycznego baseline'u R2.
Nowe kryterium habitatu ocenia RTF/lockstep w SEGMENTACH, z granicami wyprowadzonymi z CHOREOGRAFII (spec),
NIGDY z przebiegu RTF (§7c antyselekcja). Ten skrypt + progi commitowane PRZED pierwszą próbą.

  H1 (twarde) lockstep CAŁEGO biegu:  timejump_total == 0  ∧  sim monotoniczny (bez cofnięć/nieciągłości).
  H2 (twarde) segmenty ROSZCZEŃ:      frac(rtf<0.5) == 0  ∧  p10(rtf) ≥ 0.99  ∧  Δsim/Δwall(fit) ≥ 0.95.
  H3 prowieniencja:                    lista wielkości + skąd (sim vs wall); żadna teza na zegarze ściennym.
  H4 tranzyt/start/RTL:                dipy raportowane liczbowo, oznaczone planszą „transit"; ZERO bramki.

Progi H2 (D7 §7b — USTANOWIONE TERAZ, commitowane; p10/frac z klasy R2, Δsim/Δwall jako dopuszczenie
narzutu scenariusza — NIE udawać, że pochodzi z R2):
"""
from __future__ import annotations
import argparse, glob, json, os, re, sys

# ── PROGI HABITATU (D7 §7b, FREEZE — commit przed pierwszą próbą, §7c antyselekcja) ────────────────
H2_FRAC_LT_05_MAX = 0.0     # frac(rtf<0.5) == 0%  (klasa R2: baseline frac<0.5 ≈ 0)
H2_P10_MIN        = 0.99    # p10(rtf) ≥ 0.99      (klasa R2: baseline p10 0.9971)
H2_DSIM_DWALL_MIN = 0.95    # Δsim/Δwall(fit) ≥ 0.95  (NOWY próg — dopuszczenie narzutu scenariusza,
                            #   NIE z R2; R2 baseline Δsim/Δwall ~0.9998. Ustanowiony D7 §7b.)
RTF_CLIP = 2.0              # chwilowy rtf > RTF_CLIP = artefakt kwantyzacji zegara → przytnij do metryk frac/p10


# ── ładowanie próbek RTF ──────────────────────────────────────────────────────────────────────────
def load_rtf(run_dir):
    p = os.path.join(run_dir, "rtf_stream.jsonl")
    if not os.path.exists(p):
        raise FileNotFoundError(f"brak rtf_stream.jsonl w {run_dir} (próbnik nie wystartował?)")
    S = []
    for ln in open(p):
        ln = ln.strip()
        if not ln:
            continue
        d = json.loads(ln)
        sim = d.get("sim", d.get("sim_s"))   # nowy float `sim`, fallback stary int `sim_s`
        S.append({"wall": float(d["wall"]), "sim": float(sim), "rtf": float(d["rtf"])})
    S.sort(key=lambda r: r["wall"])
    return S


def _pct(xs, q):
    if not xs:
        return None
    ys = sorted(xs)
    i = q * (len(ys) - 1)
    lo = int(i); hi = min(lo + 1, len(ys) - 1)
    return ys[lo] + (ys[hi] - ys[lo]) * (i - lo)


def _lin_slope(xs, ys):
    """Δsim/Δwall = nachylenie regresji sim↔wall (odporne na obcięcie int / szum)."""
    n = len(xs)
    if n < 2:
        return None
    mx = sum(xs) / n; my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    return num / den if den > 0 else None


def seg_metrics(samples):
    """Metryki H2/H4 dla listy próbek {wall,sim,rtf}."""
    if not samples:
        return {"n": 0, "frac_lt_05": None, "p10": None, "dsim_dwall": None, "min_rtf": None, "median_rtf": None}
    rtf = [min(s["rtf"], RTF_CLIP) for s in samples]
    frac = sum(1 for r in rtf if r < 0.5) / len(rtf)
    dsw = _lin_slope([s["wall"] for s in samples], [s["sim"] for s in samples])
    return {
        "n": len(samples),
        "frac_lt_05": round(frac, 4),
        "p10": round(_pct(rtf, 0.10), 4),
        "median_rtf": round(_pct(rtf, 0.50), 4),
        "min_rtf": round(min(rtf), 4),
        "dsim_dwall": round(dsw, 4) if dsw is not None else None,
    }


def h2_pass(m):
    if m["n"] == 0:
        return False, "0 próbek w segmencie"
    fails = []
    if m["frac_lt_05"] > H2_FRAC_LT_05_MAX:
        fails.append(f"frac<0.5={m['frac_lt_05']}>{H2_FRAC_LT_05_MAX}")
    if m["p10"] < H2_P10_MIN:
        fails.append(f"p10={m['p10']}<{H2_P10_MIN}")
    if m["dsim_dwall"] is None or m["dsim_dwall"] < H2_DSIM_DWALL_MIN:
        fails.append(f"Δsim/Δwall={m['dsim_dwall']}<{H2_DSIM_DWALL_MIN}")
    return (len(fails) == 0), ("; ".join(fails) if fails else "PASS")


# ── H1: lockstep całego biegu ───────────────────────────────────────────────────────────────────────
def h1_lockstep(run_dir, samples):
    tj = 0
    for fn in ("timejump_pre.txt", "timejump_post.txt"):
        p = os.path.join(run_dir, fn)
        if os.path.exists(p):
            try:
                tj += int(open(p).read().strip() or "0")
            except ValueError:
                pass
    # sim monotoniczny (bez cofnięć); nieciągłość = skok sim wstecz albo skok wprzód >> upływu wall
    back = 0; fwd_jump = 0
    for a, b in zip(samples, samples[1:]):
        dsim = b["sim"] - a["sim"]; dwall = b["wall"] - a["wall"]
        if dsim < -1e-6:
            back += 1
        if dwall > 0 and dsim > dwall + 1.0:   # sim wyprzedza wall o >1 s = nieciągłość zegara
            fwd_jump += 1
    ok = (tj == 0) and (back == 0) and (fwd_jump == 0)
    return {"pass": ok, "timejump_total": tj, "sim_backsteps": back, "sim_fwd_jumps": fwd_jump}


# ── segmentacja z CHOREOGRAFII (§7c: granice ze spec, NIGDY z RTF) ───────────────────────────────────
def _spec(act):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    import yaml
    return yaml.safe_load(open(os.path.join(root, "acts", f"{act}_spec.yaml")))


def segments_A1A2(act, run_dir):
    """A1/A2: okna w trace-t (= time.time()-t0, wall-elapsed) → unix przez manifest.arm_wall_unix →
    selekcja próbek rtf_stream po `wall`. Granice = STAŁE spec timeline_s (niezależne od biegu i od RTF)."""
    sp = _spec(act); tl = sp["timeline_s"]
    man = json.load(open(os.path.join(run_dir, "manifest.json")))
    t0 = man.get("arm_wall_unix")
    if not t0:
        raise ValueError("manifest.arm_wall_unix brak — bieg starym runnerem (przed §7b)")
    segs = []
    if act == "A1":
        rh = tl["intruder_ring_hold"]                       # [23.0, 49.0] dwell+OBSERVE (spec timeline_s)
        segs = [
            ("takeoff_patrol_transit", "transit", 0.0, tl["patrol_until"], "spec.segments.patrol_transit_in [0,20]"),
            ("approach", "transit", tl["patrol_until"], tl["intruder_approach"][1], "spec.intruder_approach [20,23]"),
            ("dwell_observe", "claim", rh[0], rh[1], "spec.intruder_ring_hold [23,49] = dwell_confirm+OBSERVE (D7 dwell+OBSERVE)"),
            ("rtl_land", "transit", rh[1], None, "po OBSERVE: RTL/land — brak roszczenia"),
        ]
    else:  # A2
        e0 = tl["ep0_ring_hold"]; eg = tl["expire_gap"]; ret = tl["intruder_return"]; e1 = tl["ep1_ring_hold"]
        segs = [
            ("takeoff_patrol_transit", "transit", 0.0, tl["patrol_until"], "spec.segments.patrol_transit_in [0,20]"),
            ("approach", "transit", tl["patrol_until"], e0[0], "spec.intruder_approach [20,23]"),
            ("ep0_dwell_observe", "claim", e0[0], e0[1], "spec.ep0_ring_hold [23,45] = dwell+OBSERVE ep0"),
            ("leave_expire", "claim", eg[0], eg[1], "spec.expire_gap [45,51] = target-lost/EXPIRE (dron hover — bramkowane zachowawczo)"),
            ("intruder_return", "transit", eg[1], e1[0], "spec.intruder_return [51,54] — intruz w tranzycie"),
            ("ep1_dwell_observe", "claim", e1[0], e1[1], "spec.ep1_ring_hold [54,74] = dwell+OBSERVE ep1"),
            ("rtl_land", "transit", e1[1], None, "po ep1: RTL/land — brak roszczenia"),
        ]
    out = []
    for name, kind, a, b, src in segs:
        w0 = t0 + a
        w1 = t0 + b if b is not None else float("inf")
        out.append({"name": name, "kind": kind, "sim_lo": a, "sim_hi": b, "src": src,
                    "sel": ("wall", w0, w1)})
    return out


def segments_A3(act, run_dir):
    """A3: refuse_descent [on_denial, on_touchdown] = segment roszczenia (D7 denial→touchdown).
    Granice zdarzeniowe (mono z trace/act.log — WYKONANA choreografia, nie RTF) → sim przez gt (mono,sim)."""
    tr = os.path.join(run_dir, "trace.jsonl")
    gt = []  # (mono, sim)
    denial_mono = None; touch_mono = None; ticks_mono = []
    for ln in open(tr):
        ln = ln.strip()
        if not ln:
            continue
        d = json.loads(ln)
        if d.get("t") == "gt":
            gt.append((d["mono"], d["sim"]))
        elif d.get("t") == "event" and d.get("ev") == "denial_on":
            denial_mono = d["mono"]
        elif d.get("t") == "tick":
            ticks_mono.append(d["mono"])
    # touchdown z act.log (autorytatywny wydruk gate S2), fallback = ostatni tick
    al = os.path.join(run_dir, "act.log")
    if os.path.exists(al):
        m = re.search(r"touchdown mono=([0-9.]+)", open(al).read())
        if m:
            touch_mono = float(m.group(1))
    if touch_mono is None and ticks_mono:
        touch_mono = ticks_mono[-1]
    if denial_mono is None or touch_mono is None or len(gt) < 2:
        raise ValueError(f"A3: brak denial/touchdown/gt (denial={denial_mono} touch={touch_mono} gt={len(gt)})")
    gt.sort()

    def mono2sim(mono):
        # interpolacja liniowa po parach gt (mono,sim)
        if mono <= gt[0][0]:
            return gt[0][1]
        if mono >= gt[-1][0]:
            return gt[-1][1]
        for (m0, s0), (m1, s1) in zip(gt, gt[1:]):
            if m0 <= mono <= m1:
                f = (mono - m0) / (m1 - m0) if m1 > m0 else 0.0
                return s0 + (s1 - s0) * f
        return gt[-1][1]

    d_sim = mono2sim(denial_mono); t_sim = mono2sim(touch_mono)
    return [
        {"name": "patrol_transit", "kind": "transit", "sim_lo": gt[0][1], "sim_hi": d_sim,
         "src": "spec.segments.patrol_transit [0,on_denial] — mono→sim(gt)", "sel": ("sim", gt[0][1], d_sim)},
        {"name": "refuse_descent", "kind": "claim", "sim_lo": d_sim, "sim_hi": t_sim,
         "src": "spec.segments.refuse_descent [on_denial,on_touchdown] — mono→sim(gt)", "sel": ("sim", d_sim, t_sim)},
    ]


def select(samples, sel):
    axis, lo, hi = sel
    return [s for s in samples if lo <= s[axis] <= hi]


# ── H3 prowieniencja (stała treść — weryfikacja obecności pól sim) ────────────────────────────────────
def h3_provenance(samples):
    have_sim = all("sim" in s for s in samples[:5]) if samples else False
    return {
        "pass": have_sim,
        "note": ("Metryki kosztu (Δsim/Δwall, frac<0.5, p10) liczone z gz sim-clock (rtf_stream.sim) vs "
                 "unix wall — z definicji sim-derived. Zegar wewn. osłony (trace `t`, age, θ_age) = "
                 "time.time()-t0 (wall-elapsed); pod H1-lockstep (RTF≈1, timejump=0) wall≡sim w tolerancji, "
                 "więc choreografia i semantyka θ_age wierne w sim. Tezy warstwy certyfikowanej (default-deny "
                 "tokenu, consume/re-admisja=porządek zdarzeń; POS_DEGRADED dominacja; containment=promień "
                 "touchdown) są niezmiennicze względem ramki zegara. → żadna teza NIE stoi na zegarze ściennym; "
                 "H1-lockstep jest warunkiem umożliwiającym i sam jest bramkowany."),
        "quantities": {
            "sim_derived_cost": ["dsim_dwall", "frac_lt_05", "p10", "min_rtf", "median_rtf"],
            "wall_elapsed_internal_but_faithful_under_H1": ["trace.t", "age", "theta_age", "choreography_timeline_s"],
            "frame_invariant_result": ["token_default_deny", "consume/readmission_order", "POS_DEGRADED_dominance",
                                       "touchdown_radial", "admission_seq"],
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("act", choices=["A1", "A2", "A3"])
    ap.add_argument("run_dir")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    out = args.out or os.path.join(args.run_dir, "habitat.json")

    samples = load_rtf(args.run_dir)
    segfn = segments_A3 if args.act == "A3" else segments_A1A2
    segs = segfn(args.act, args.run_dir)

    H1 = h1_lockstep(args.run_dir, samples)
    H3 = h3_provenance(samples)

    seg_reports = []
    claim_fail = 0
    for sg in segs:
        sel = select(samples, sg["sel"])
        m = seg_metrics(sel)
        rep = {"name": sg["name"], "kind": sg["kind"], "sim_window": [sg["sim_lo"], sg["sim_hi"]],
               "src": sg["src"], "metrics": m}
        if sg["kind"] == "claim":
            ok, why = h2_pass(m)
            rep["H2_pass"] = ok; rep["H2_note"] = why
            if not ok:
                claim_fail += 1
        else:
            rep["label"] = "beyond characterized envelope — transit"   # D7 §7b H4: raport, ZERO bramki
        seg_reports.append(rep)

    verdict = "VALID" if (H1["pass"] and claim_fail == 0) else "INVALID(habitat)"
    reason = []
    if not H1["pass"]:
        reason.append(f"H1 FAIL ({H1})")
    if claim_fail:
        reason.append(f"H2 FAIL na {claim_fail} segm. roszczeń")

    result = {
        "act": args.act, "run_dir": args.run_dir, "verdict": verdict,
        "reason": ("; ".join(reason) if reason else "H1∧H2 PASS"),
        "thresholds": {"H2_FRAC_LT_05_MAX": H2_FRAC_LT_05_MAX, "H2_P10_MIN": H2_P10_MIN,
                       "H2_DSIM_DWALL_MIN": H2_DSIM_DWALL_MIN,
                       "note": "D7 §7b: p10/frac z klasy R2; Δsim/Δwall NOWY (dopuszczenie narzutu scenariusza, nie R2)"},
        "n_rtf_samples": len(samples),
        "H1_lockstep": H1, "H3_provenance": H3, "segments": seg_reports,
    }
    json.dump(result, open(out, "w"), indent=2, ensure_ascii=False)

    print(f"\n=== HABITAT {args.act} → {verdict} ({result['reason']}) ===")
    print(f"H1 lockstep: {'PASS' if H1['pass'] else 'FAIL'}  timejump={H1['timejump_total']} "
          f"backsteps={H1['sim_backsteps']} fwd_jumps={H1['sim_fwd_jumps']}  (n_rtf={len(samples)})")
    for r in seg_reports:
        m = r["metrics"]
        if r["kind"] == "claim":
            print(f"  [claim ] {r['name']:20s} sim[{r['sim_window'][0]},{r['sim_window'][1]}] "
                  f"n={m['n']:4d} frac<0.5={m['frac_lt_05']} p10={m['p10']} Δs/Δw={m['dsim_dwall']} "
                  f"min={m['min_rtf']} → {'PASS' if r['H2_pass'] else 'FAIL: '+r['H2_note']}")
        else:
            print(f"  [transit] {r['name']:20s} sim[{r['sim_window'][0]},{r['sim_window'][1]}] "
                  f"n={m['n']:4d} frac<0.5={m['frac_lt_05']} p10={m['p10']} Δs/Δw={m['dsim_dwall']} "
                  f"min={m['min_rtf']}  (H4: raport, bez bramki)")
    print(f"→ habitat.json: {out}")
    sys.exit(0 if verdict == "VALID" else 3)


if __name__ == "__main__":
    main()
