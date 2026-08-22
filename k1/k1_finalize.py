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


def _jdefault(o):
    """Konwersja skalarów numpy (np.float64/np.bool_) do natywnych typów przy json.dump."""
    if hasattr(o, "item"):
        return o.item()
    raise TypeError(f"nie-serializowalny: {type(o)}")


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


def _physical_touchdown_sim(gt, t_inj_sim, ground=0.5, airborne=1.0):
    """sim FIZYCZNEGO touchdownu (GT z≤ground po locie ≥airborne), po wstrzyknięciu. Mirror sędziego.
    (Zdarzenie 'touchdown' w trace to timer bramki ~8 s — NIE fizyczny; do roszczenia H1 liczy się fizyczny.)"""
    seen = False
    for r in gt:
        if r.get("sim", -1) < t_inj_sim:
            if r.get("z", 0.0) >= airborne:
                seen = True
            continue
        if r.get("z", 0.0) >= airborne:
            seen = True
        if seen and r.get("z", 0.0) <= ground:
            return r["sim"]
    return None


def _ulog_sim_offset(ulog_path, gt, ev_by):
    """C takie że sim = ulog_hrt/1e6 + C (ulog boot-relative == gz sim pod lockstep, mały offset
    boot px4↔gz). Kotwica: pierwsze wejście OFFBOARD — nav_state==14 w ulogu ↔ event 'offboard' w trace.
    Zwraca C [s] lub None."""
    try:
        ud, _ = J.read_ulog(ulog_path)
    except Exception:
        return None
    vs = ud.get("vehicle_status", {})
    hrt_offb = None
    for t, v in zip(vs.get("timestamp", []), vs.get("nav_state", [])):
        if int(v) == 14:                       # NAVIGATION_STATE_OFFBOARD
            hrt_offb = t / 1e6
            break
    offb = ev_by.get("offboard")
    if hrt_offb is None or offb is None:
        return None
    gcand = [g for g in gt if "mono" in g and "sim" in g]
    if not gcand:
        return None
    gnear = min(gcand, key=lambda r: abs(r["mono"] - offb["mono"]))
    return round(gnear["sim"] - hrt_offb, 4)


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
    t_inj_sim = px4_inj_us = ulog_sim_C = None
    if denial:
        gnear = _nearest(gt, denial["mono"], "sim")
        if gnear:
            t_inj_sim = gnear["sim"]
        # ulog↔sim: ulog hrt jest BOOT-RELATIVE (== gz sim pod lockstep), ekf.ts jest EPOCH — NIE używać
        # ekf.ts do pinu. C = sim − ulog_hrt z kotwicy OFFBOARD (nav_state 14 ↔ event 'offboard').
        # px4_inj_us dobrane tak, by offset sędziego = C: offset = t_inj_sim − px4_inj_us/1e6 = C.
        ulog_sim_C = _ulog_sim_offset(a.ulog, gt, ev_by) if a.ulog and os.path.exists(a.ulog) else None
        if t_inj_sim is not None:
            C = ulog_sim_C if ulog_sim_C is not None else 0.0
            px4_inj_us = (t_inj_sim - C) * 1e6
        stamps.update(t_inj_sim=t_inj_sim, px4_inj_us=px4_inj_us, ulog_sim_C=ulog_sim_C,
                      gt_dt=round(abs(gnear["mono"] - denial["mono"]), 4) if gnear else None)
    # R3 stemple ramienia N
    for k in ("land_cmd_sent", "land_ack"):
        if k in ev_by:
            stamps[k] = {kk: vv for kk, vv in ev_by[k].items() if kk in ("mono", "result")}
    refuse_sim = None
    if a.arm == "S" and "refuse_pos_land" in ev_by:
        rn = _nearest(gt, ev_by["refuse_pos_land"]["mono"], "sim")
        refuse_sim = rn["sim"] if rn else None
        stamps["refuse_sim"] = refuse_sim

    # touchdown: FIZYCZNY (GT z≤0.5) do roszczenia H1; zdarzenie-timer bramki = informacyjne
    touchdown_event_sim = None
    if "touchdown" in ev_by:
        tn = _nearest(gt, ev_by["touchdown"]["mono"], "sim")
        touchdown_event_sim = tn["sim"] if tn else None
    touchdown_sim = _physical_touchdown_sim(gt, t_inj_sim) if t_inj_sim is not None else None
    stamps["touchdown_sim"] = touchdown_sim                     # FIZYCZNY (segment roszczenia)
    stamps["touchdown_event_sim"] = touchdown_event_sim         # timer bramki (informacyjny)

    # H1 (ANEKS_K1-4): nakładka stalla (rtf<0.5) na okno reakcji denial→REFUSE (S) / denial→ack-land (N)
    stall_in_reaction = None

    # habitat (H1 lockstep + H2 na segmencie roszczenia [t_inj_sim, touchdown_FIZYCZNY]) — progi frozen
    hab = None
    hab_detail = None
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from acts import habitat_gate as HG
        samples = HG.load_rtf(a.out_dir)
        if samples:
            h1 = HG.h1_lockstep(a.out_dir, samples)
            # H1 (ANEKS_K1-4): stall (rtf<0.5) nakładający się na okno reakcji — INFORMACYJNE, nie bramkuje
            react_end = refuse_sim if a.arm == "S" else (
                (lambda ln: (_nearest(gt, ln["mono"], "sim") or {}).get("sim"))(ev_by["land_ack"])
                if "land_ack" in ev_by else None)
            if t_inj_sim is not None and react_end is not None:
                lo, hi = min(t_inj_sim, react_end), max(t_inj_sim, react_end)
                stalls = [s for s in samples if lo <= s.get("sim", -1) <= hi and s.get("rtf", 1) < 0.5]
                stall_in_reaction = {"window_s": [round(lo, 3), round(hi, 3)],
                                     "n_stall": len(stalls),
                                     "overlap": len(stalls) > 0,
                                     "min_rtf": round(min([s["rtf"] for s in stalls], default=1.0), 3)}
            seg_m = None
            dsim_ok = None
            a3_strict = None
            seg = []
            if t_inj_sim is not None and touchdown_sim is not None:
                seg = [s for s in samples if t_inj_sim <= s.get("sim", -1) <= touchdown_sim]
                if len(seg) >= 3:
                    seg_m = HG.seg_metrics(seg)
                    # PRE_K1 §2: bieg ważny habitatowo = timejump=0 ∧ Δsim/Δwall ≥ 0.95 w epizodzie.
                    # (p10≥0.99 / frac<0.5=0 to progi A3-strict — INFORMACYJNE, NIE bramka K1.)
                    dsim_ok = bool(seg_m.get("dsim_dwall", 0.0) >= HG.H2_DSIM_DWALL_MIN)
                    a3_strict = HG.h2_pass(seg_m)   # [bool, reason] — tylko do wglądu
            verdict = "VALID" if (h1.get("pass") and dsim_ok) else "INVALID(habitat)"
            hab = verdict
            hab_detail = {"criterion": "PRE_K1 §2: timejump=0 ∧ Δsim/Δwall≥0.95",
                          "h1": h1, "dsim_dwall_ok": dsim_ok, "h2_claim": seg_m,
                          "a3_strict_h2_informacyjne": a3_strict,
                          "stall_in_reaction_window": stall_in_reaction,
                          "claim_seg_s_PHYS": [t_inj_sim, touchdown_sim], "n_seg": len(seg)}
            with open(os.path.join(a.out_dir, "habitat.json"), "w") as f:
                json.dump({"verdict": verdict, **hab_detail}, f, indent=2, default=_jdefault)
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
        json.dump(manifest, f, indent=2, default=_jdefault)

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
        json.dump(judge_out, f, indent=2, default=_jdefault)

    # H2 (ANEKS_K1-4): sanity warstwy finalize/raportu (sędzia nietknięty) — do STOP-u R2
    sanity = {}
    if isinstance(judge_out, dict) and judge_out.get("t_td_s") is not None:
        ginj = min([g for g in gt if "sim" in g], key=lambda r: abs(r["sim"] - t_inj_sim), default=None)
        h0 = round(ginj["z"], 3) if ginj else None
        from r03 import config as C                              # stałe D5 z config, NIE z pamięci
        sw = C.H_SWITCH_AGL
        GROUND = 0.5                                              # próg touchdownu GT (jak sędzia)
        ALT_NOM = 8.0                                             # gate: desc_fast_dur na NOMINALE (nie h0)
        desc_fast_dur = (ALT_NOM - sw) / C.V_DESC_FAST           # gate przełącza fazę PO CZASIE (~4.0 s)
        t_exp = None
        if h0 is not None:
            t_ph1 = (h0 - GROUND) / C.V_DESC_FAST                # czas do z=0.5 gdyby cała faza1
            if t_ph1 <= desc_fast_dur:                           # touchdown przed h_switch (czas) → faza1
                t_exp = t_ph1
            else:                                                # przełącza na 0.7 po desc_fast_dur
                h_sw = h0 - C.V_DESC_FAST * desc_fast_dur
                t_exp = desc_fast_dur + (h_sw - GROUND) / C.V_DESC_LAND
        sanity["t_td"] = {"measured_s": judge_out["t_td_s"], "h0_m": h0,
                          "profil_D5": {"V_DESC_FAST": C.V_DESC_FAST, "V_DESC_LAND": C.V_DESC_LAND,
                                        "H_SWITCH_AGL": sw, "desc_fast_dur_gate_s": round(desc_fast_dur, 3)},
                          "expected_from_h0_s": round(t_exp, 3) if t_exp is not None else None,
                          "note": ("h0 z GT (nie nominał 8 m — wczesny punkt, dron w climbie). "
                                   "Gate przełącza fazę PO CZASIE (nominał ALT=8) → przy h0<8 touchdown "
                                   "w fazie1 (1.5 m/s), stąd t_td≈(h0-0.5)/1.5.")}
        tdr = judge_out["t_td_s"]
        nav = (judge_out.get("ulog") or {}).get("nav_state_seq") or []
        sanity["nav_seq_annotated"] = [{"rel_s": t, "nav": n, "post_touchdown": (t > tdr)}
                                       for (t, v, n) in nav]
    manifest["stall_in_reaction_window"] = stall_in_reaction
    manifest["sanity"] = sanity
    with open(os.path.join(a.out_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2, default=_jdefault)

    print(json.dumps({"manifest": "manifest.json", "judge": "judge.json",
                      "t_inj_sim": t_inj_sim, "px4_inj_us": px4_inj_us,
                      "judge_frozen": judge_frozen,
                      "verdict_fields": sorted(judge_out.keys()) if isinstance(judge_out, dict) else None}))


if __name__ == "__main__":
    main()
