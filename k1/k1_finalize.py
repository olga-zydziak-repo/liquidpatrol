#!/usr/bin/env python3
"""
k1_finalize.py — po biegu (PRE_K1 §3.2/§3.3, ridery R2/R5). Parsuje trace, wyprowadza stemple,
buduje manifest R5, uruchamia ZAMROŻONEGO sędziego k1_judge (asercja hasza) → judge.json.

Wyprowadzenie stempli (bez modyfikacji sędziego/gate):
  denial_on.mono → t_inj_sim = sim najbliższego wiersza gt; px4_inj_us = ts(px4 s)·1e6 najbliższego ekf.
  (ramię S) refuse_pos_land.mono → refuse_sim = sim najbliższego gt.
Sędzia dostaje: --gt=trace (filtr t=='gt'), --ekf=trace (S, ε_pos), --ulog, --t-inj, --px4-inj-us, --arm.

Manifest R5: arm, point, boot_n, kind, sha_harness, sha_k1_judge, ulog, stemple, preflight, habitat.
"""
import os, sys, json, argparse, hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))          # k1/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root
import k1_judge as J

FROZEN_JUDGE_SHA = "4e0dc0afffda099837a002191a5540fd95d6de13cb88e7233433d67b1b998ae1"


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()


def load_trace(path):
    gt, ekf, events, meta, outcome = [], [], [], None, None
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            t = r.get("t")
            if t == "gt":
                gt.append(r)
            elif t == "ekf":
                ekf.append(r)
            elif t == "event":
                events.append(r)
            elif t == "meta":
                meta = r
            elif t == "outcome":
                outcome = r
    return gt, ekf, events, meta, outcome


def _nearest(rows, mono, key):
    cand = [r for r in rows if key in r and "mono" in r]
    if not cand:
        return None
    return min(cand, key=lambda r: abs(r["mono"] - mono))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", required=True)
    ap.add_argument("--arm", required=True, choices=["N", "S"])
    ap.add_argument("--point", type=float, required=True)
    ap.add_argument("--boot", type=int, required=True)
    ap.add_argument("--kind", default="crit", choices=["crit", "info"])
    ap.add_argument("--ulog", default=None)
    ap.add_argument("--harness-sha-file", dest="harness_file", required=True,
                    help="plik kodu harnessu do sha (gate_run_r03.py dla S, k1_arm_n.py dla N)")
    ap.add_argument("--habitat", default=None, help="habitat.json (opc.)")
    ap.add_argument("--certs-selfcheck", default=None, help="log certs_selfcheck (S, R4)")
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()

    gt, ekf, events, meta, outcome = load_trace(a.trace)
    ev_by = {}
    for e in events:
        ev_by.setdefault(e.get("ev"), e)     # pierwszy każdego typu

    denial = ev_by.get("denial_on")
    stamps = {"denial_on_mono": denial.get("mono") if denial else None}
    t_inj_sim = px4_inj_us = None
    if denial:
        gnear = _nearest(gt, denial["mono"], "sim")
        enear = _nearest(ekf, denial["mono"], "ts")
        if gnear:
            t_inj_sim = gnear["sim"]
        if enear:
            px4_inj_us = enear["ts"] * 1e6
        stamps.update(t_inj_sim=t_inj_sim, px4_inj_us=px4_inj_us,
                      gt_dt=round(abs(gnear["mono"] - denial["mono"]), 4) if gnear else None,
                      ekf_dt=round(abs(enear["mono"] - denial["mono"]), 4) if enear else None)
    # R3 stemple ramienia N
    for k in ("land_cmd_sent", "land_ack"):
        if k in ev_by:
            stamps[k] = {kk: vv for kk, vv in ev_by[k].items() if kk in ("mono", "result")}
    refuse_sim = None
    if a.arm == "S" and "refuse_pos_land" in ev_by:
        rn = _nearest(gt, ev_by["refuse_pos_land"]["mono"], "sim")
        refuse_sim = rn["sim"] if rn else None
        stamps["refuse_sim"] = refuse_sim

    # touchdown sim (do segmentu roszczenia habitatu)
    touchdown_sim = None
    if "touchdown" in ev_by:
        tn = _nearest(gt, ev_by["touchdown"]["mono"], "sim")
        touchdown_sim = tn["sim"] if tn else None
    stamps["touchdown_sim"] = touchdown_sim

    # habitat (H1 lockstep + H2 na segmencie roszczenia [t_inj_sim, touchdown_sim]) — progi frozen
    hab = None
    hab_detail = None
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from acts import habitat_gate as HG
        samples = HG.load_rtf(a.out_dir)
        if samples:
            h1 = HG.h1_lockstep(a.out_dir, samples)
            seg_ok = None
            seg_m = None
            if t_inj_sim is not None and touchdown_sim is not None:
                seg = [s for s in samples if t_inj_sim <= s.get("sim", -1) <= touchdown_sim]
                if len(seg) >= 3:
                    seg_m = HG.seg_metrics(seg)
                    seg_ok = HG.h2_pass(seg_m)
            verdict = "VALID" if (h1.get("pass") and seg_ok) else "INVALID(habitat)"
            hab = verdict
            hab_detail = {"h1": h1, "h2_claim": seg_m, "h2_pass": seg_ok,
                          "claim_seg_s": [t_inj_sim, touchdown_sim], "n_seg": len(seg) if t_inj_sim and touchdown_sim else 0}
            with open(os.path.join(a.out_dir, "habitat.json"), "w") as f:
                json.dump({"verdict": verdict, **hab_detail}, f, indent=2)
    except Exception as e:
        hab_detail = {"error": str(e)}
    if a.habitat and os.path.exists(a.habitat):     # override zewn.
        try:
            hab = json.load(open(a.habitat)).get("verdict")
        except Exception:
            pass

    # sha sędziego — SR-K3 tripwire
    judge_sha = sha256_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), "k1_judge.py"))
    judge_frozen = (judge_sha == FROZEN_JUDGE_SHA)

    # W2(b) — asercja hashy osłony (ramię S): niezgodność ⇒ bieg nieważny
    import k1_shield_pins as SP
    shield_frozen, shield_detail = SP.check_shield_frozen()

    # K3 (ANEKS_K1-3): wynik certs_selfcheck (ramię S) — parsowany z logu, do manifestu
    certs = {"log": a.certs_selfcheck, "pass": None, "rc": None}
    if a.certs_selfcheck and os.path.exists(a.certs_selfcheck):
        txt = open(a.certs_selfcheck, errors="replace").read()
        certs["pass"] = ("WERDYKT certs_selfcheck: PASS" in txt)
        for ln in txt.splitlines():
            if "rc=" in ln:
                try:
                    certs["rc"] = int(ln.split("rc=")[-1].strip().split()[0])
                except Exception:
                    pass

    # K2 (ANEKS_K1-3): linia pochodzenia osłony — jawne założenie ramienia S (→ RAPORT_K1)
    PROVENANCE_ARM_S = ("osłona w stanie 6db3393 (4/4 a088367 → D_B1 01f47e8 token → "
                        "D_B3 e732c10 trace v2 → 5a6a18d erratum); ścieżka POS_DEGRADED→D5 "
                        "bajt-identyczna z 4/4 wg ANEKS_SHA §W2")

    manifest = {
        "arm": a.arm, "point": a.point, "boot_n": a.boot, "kind": a.kind,
        "sha_harness": sha256_file(a.harness_file), "harness_file": a.harness_file,
        "sha_k1_judge": judge_sha, "k1_judge_frozen": judge_frozen,
        "shield_frozen": shield_frozen, "shield_pins": shield_detail,
        "ulog": a.ulog, "ulog_exists": bool(a.ulog and os.path.exists(a.ulog)),
        "stamps": stamps,
        "harness_valid": (meta or {}).get("harness_valid"),
        "harness_poison": (meta or {}).get("harness_poison"),
        "habitat_verdict": hab,
        "certs_selfcheck": certs,
        "provenance_arm_s": (PROVENANCE_ARM_S if a.arm == "S" else None),
        "n_gt": len(gt), "n_ekf": len(ekf), "n_events": len(events),
        "events": [e.get("ev") for e in events],
    }
    os.makedirs(a.out_dir, exist_ok=True)
    with open(os.path.join(a.out_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    # --- sędzia (jeśli mamy komplet do policzenia) ---
    judge_out = {"skipped": True, "reason": None}
    if not judge_frozen:
        judge_out["reason"] = f"SR-K3: k1_judge sha {judge_sha[:16]} != frozen {FROZEN_JUDGE_SHA[:16]}"
    elif a.arm == "S" and not shield_frozen:
        bad = [k for k, v in shield_detail.items() if not v["ok"]]
        judge_out["reason"] = f"W2(b): osłona niezamrożona {bad} — bieg S NIEWAŻNY"
    elif t_inj_sim is None:
        judge_out["reason"] = "brak denial_on / t_inj_sim — nie mogę policzyć"
    else:
        ns = argparse.Namespace(
            gt=a.trace, ulog=a.ulog, t_inj=t_inj_sim, arm=a.arm,
            px4_inj_us=px4_inj_us, home=None, point=a.point,
            refuse_sim=refuse_sim, ekf=(a.trace if a.arm == "S" else None))
        try:
            judge_out = J.judge(ns)
        except Exception as e:
            judge_out = {"error": str(e), "t_inj_sim": t_inj_sim, "px4_inj_us": px4_inj_us}
    with open(os.path.join(a.out_dir, "judge.json"), "w") as f:
        json.dump(judge_out, f, indent=2)

    print(json.dumps({"manifest": "manifest.json", "judge": "judge.json",
                      "t_inj_sim": t_inj_sim, "px4_inj_us": px4_inj_us,
                      "judge_frozen": judge_frozen,
                      "verdict_fields": sorted(judge_out.keys()) if isinstance(judge_out, dict) else None}))


if __name__ == "__main__":
    main()
