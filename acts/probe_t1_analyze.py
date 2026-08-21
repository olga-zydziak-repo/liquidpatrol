#!/usr/bin/env python3
"""acts/probe_t1_analyze.py — PROMPT_D_P3 T1 / ANEKS_D8 §3e: analiza post-hoc biegu PROBE (nie próba).

Łączy 3 strumienie instrumentacji §3e:
  trace.jsonl      — per-tick: pos(NED), intr_ned(NED świat-stały cel), locked, mode, yaw → ZASIĘG do celu
  mti_frame.jsonl  — per-klatka (detector_node, sim-time): diff_max, n_raw, n_kept, valid_frac
  dbg.jsonl        — det-kadencja: {dbg: n_box,conf,entry,locked,mti_ok,n_comps} + {channel: box cx,cy,w,h,age}

WERDYKT T1 (§3d Bieg 1) = PASS ⟺ ENTRY in-window ∧ mti_ok k=3 pod rząd ∧ box na celu (zasięg 7-9 m ∧ centralny).
Raport-nie-brama: czy ENTRY zaszło zanim cel wszedł w pierścień. Percepcja NIERAPORTOWALNA jako wynik aktu.

Uruchom: python3 acts/probe_t1_analyze.py <OUTDIR>
"""
from __future__ import annotations
import json, math, os, sys

import yaml

ENTRY_K = 3                 # k=3 pod rząd (config_r02 ENTRY_K)
DIFF_THR = 22              # MTIParams.diff_thr (mti.py) — próg diff_max
BAND_LO, BAND_HI = 7.0, 9.0
EDGE_MARGIN = 0.10        # ENTRY_EDGE_MARGIN — box centralny ⟺ cx,cy ∈ [0.1,0.9]
CENTRAL_MARGIN = 0.12    # ANEKS_D8 §5c: margines centralności |cy−0.5| ≤ 0.12 (dźwignia pionowa §5b)
CENTRAL_FRAC_MIN = 0.80  # §5c: central-ok w ≥80% klatek w kopercie


def _load_jsonl(path):
    out = []
    if not os.path.exists(path):
        return out
    with open(path) as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                out.append(json.loads(ln))
            except Exception:
                pass
    return out


def _med(xs):
    xs = sorted(x for x in xs if x is not None)
    n = len(xs)
    if n == 0:
        return None
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2.0


def _pctl(xs, p):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    i = min(len(xs) - 1, max(0, int(round(p / 100.0 * (len(xs) - 1)))))
    return xs[i]


def _longest_run(seq, val=1.0):
    best = cur = 0
    for x in seq:
        if x == val:
            cur += 1; best = max(best, cur)
        else:
            cur = 0
    return best


def main():
    outdir = sys.argv[1]
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    trace = _load_jsonl(os.path.join(outdir, "trace.jsonl"))
    mti = _load_jsonl(os.path.join(outdir, "mti_frame.jsonl"))
    dec = _load_jsonl(os.path.join(outdir, "dec_frame.jsonl"))   # §5c: per-decyzję sim_t + top1 cx,cy
    dbg_all = _load_jsonl(os.path.join(outdir, "dbg.jsonl"))
    dbg = [d for d in dbg_all if d.get("topic") == "dbg"]
    chan = [d for d in dbg_all if d.get("topic") == "channel"]

    # okno pierścienia (spec A1)
    spec = yaml.safe_load(open(os.path.join(root, "acts", "A1_spec.yaml")))
    tl = spec["timeline_s"]
    ring = tl.get("intruder_ring_hold") or tl.get("ep0_ring_hold") or [0, 9999]
    ring_lo, ring_hi = float(ring[0]), float(ring[1])

    recs = [r for r in trace if isinstance(r, dict) and "pos" in r and "k" in r]

    # ── ANEKS_D8 §4b: bramka gotowości detektora — zegar choreografii/okna kotwiczony do TEJ chwili
    # (nie do arm). trace `t` jest ścienny-od-arm; okno pierścienia [ring_lo,ring_hi] jest w sim-fazie
    # od startu choreografii. Zamiast konwersji sim↔wall (RTF nieznane a priori) używamy sygnałów
    # ZEGARO-AGNOSTYCZNYCH: (a) intruz „na pierścieniu" ⟺ plateau wysokości intr_ned; (b) ENTRY-in-window
    # ⟺ zasięg-w-locku ∈ paśmie 7-9 m. To NIE proxy czasowe — to mierzone wielkości geometryczne (§3e).
    ready_ev = next((r for r in trace if isinstance(r, dict) and r.get("event") == "detector_ready"), None)
    ready_t = ready_ev.get("ready_wall_s") if ready_ev else None
    choreo_sim0 = ready_ev.get("sim_t0") if ready_ev else None    # §5c: kotwica sim fazy choreografii
    ready_timeout = any(isinstance(r, dict) and r.get("event") == "detector_ready_timeout" for r in trace)

    # ── ZASIĘG do świat-stałego celu (§3e: koperta 7-9 m) ──
    ranges = []          # (t, range3d, range_h, alt_up)
    for r in recs:
        intr = r.get("intr_ned"); pos = r.get("pos")
        if intr and pos and len(intr) == 3 and len(pos) >= 3:
            dN, dE, dD = intr[0] - pos[0], intr[1] - pos[1], intr[2] - pos[2]
            ranges.append((r["t"], math.sqrt(dN * dN + dE * dE + dD * dD), math.hypot(dN, dE), -intr[2]))
    # okno „intruz na pierścieniu" z PLATEAU WYSOKOŚCI intruza (ring z wyższe niż park; zegaro-agnostyczne).
    alts = [x[3] for x in ranges]
    alt_max = max(alts) if alts else None
    def _at_ring(x):     # x=(t,r3,rh,alt_up); na pierścieniu ⟺ blisko szczytu wysokości (nie park/approach)
        return alt_max is not None and x[3] >= alt_max - 1.5
    rng_ring = [x for x in ranges if _at_ring(x)] or ranges
    r3 = [x[1] for x in rng_ring]
    band_frac = (sum(1 for v in r3 if BAND_LO <= v <= BAND_HI) / len(r3)) if r3 else None
    # zakres czasowy okna pierścienia (raport) + szybkie odpytanie zasięgu w chwili t
    ring_t_lo = min((x[0] for x in rng_ring), default=None)
    ring_t_hi = max((x[0] for x in rng_ring), default=None)
    def _range_at(t):
        best = None; bestd = 1e9
        for (tt, v, _rh, _a) in ranges:
            dd = abs(tt - t)
            if dd < bestd:
                bestd = dd; best = v
        return best

    # ── ENTRY / lock (trace autorytatywny) ──
    entry_t = None; prev_lock = False; n_entry = 0
    for r in recs:
        lk = bool(r.get("locked"))
        if lk and not prev_lock:
            n_entry += 1
            if entry_t is None:
                entry_t = r["t"]
        prev_lock = lk
    # §4b: ENTRY-in-window ZEGARO-AGNOSTYCZNE = ENTRY po gotowości detektora ∧ zasięg-w-locku w paśmie 7-9 m
    # (±0.5 m na osc/DALT). Zastępuje stałe okno ścienne [ring_lo,ring_hi+5] (nietrafne po przekotwiczeniu).
    rng_at_entry = _range_at(entry_t) if entry_t is not None else None
    after_ready = (ready_t is None) or (entry_t is not None and entry_t >= ready_t - 0.5)
    entry_in_window = bool(entry_t is not None and after_ready
                           and rng_at_entry is not None and (BAND_LO - 0.5) <= rng_at_entry <= (BAND_HI + 0.5))
    # raport-nie-brama: pierwsze wejście celu w pierścień (zasięg pierwszy raz w paśmie) vs ENTRY
    first_in_ring_t = next((t for (t, v, _rh, _a) in ranges if BAND_LO <= v <= BAND_HI), None)
    entry_before_ring = (entry_t is not None and first_in_ring_t is not None and entry_t < first_in_ring_t)

    # ── mti_ok k=3 pod rząd (dbg det-kadencja) ──
    mti_seq = [d.get("mti_ok") for d in dbg]            # 1.0 / 0.0 / -1.0(nieaktywne)
    mti_run = _longest_run(mti_seq, 1.0)
    n_mti_ok = sum(1 for x in mti_seq if x == 1.0)
    n_comps = [d.get("n_comps") for d in dbg if d.get("n_comps") is not None]

    # ── box na celu (kanał: cx,cy) — stabilność + centralność ──
    box_pts = [(d["val"][0], d["val"][1]) for d in chan if not d.get("empty") and len(d.get("val", [])) >= 2]
    cxs = [p[0] for p in box_pts]; cys = [p[1] for p in box_pts]
    cx_med, cy_med = _med(cxs), _med(cys)
    def _std(xs, m):
        return math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs)) if xs and m is not None else None
    cx_std, cy_std = _std(cxs, cx_med), _std(cys, cy_med)
    central = (cx_med is not None and EDGE_MARGIN <= cx_med <= 1 - EDGE_MARGIN
               and EDGE_MARGIN <= cy_med <= 1 - EDGE_MARGIN)
    box_on_target = bool(box_pts) and central          # perceptual: kanał wydał centralny box
    # §3e ATRYBUCJA (raport, nie brama percepcji): czy profil UTRZYMAŁ kopertę 7-9 m (§3a/§3b).
    envelope_held = (band_frac is not None and band_frac >= 0.5
                     and _med(r3) is not None and BAND_LO <= _med(r3) <= BAND_HI)

    # ── ANEKS_D8 §5c: BRAMKA ILOŚCIOWA central-ok (dźwignia centrowania pionowego §5b) ──
    # Okno pierścienia w sim-fazie: [choreo_sim0+ring_lo, choreo_sim0+ring_hi]. Klatki „w kopercie" =
    # decyzje w tym oknie z boxem (nbox>0). central-ok ⟺ |cy−0.5| ≤ 0.12 (margines pionowy §5b steruje).
    dec_recs = [d for d in dec if isinstance(d, dict) and d.get("t") is not None]
    if choreo_sim0 is not None:
        sim_lo, sim_hi = choreo_sim0 + ring_lo, choreo_sim0 + ring_hi
        env_frames = [d for d in dec_recs if sim_lo <= d["t"] <= sim_hi and (d.get("nbox") or 0) > 0
                      and d.get("cy") is not None]
    else:                                             # brak kotwicy sim → wszystkie klatki z boxem (fallback)
        env_frames = [d for d in dec_recs if (d.get("nbox") or 0) > 0 and d.get("cy") is not None]
    cy_margins = [abs(d["cy"] - 0.5) for d in env_frames]
    cx_margins = [abs(d["cx"] - 0.5) for d in env_frames if d.get("cx") is not None]
    n_central_ok = sum(1 for m in cy_margins if m <= CENTRAL_MARGIN)
    central_ok_frac = (n_central_ok / len(cy_margins)) if cy_margins else None
    central_gate = central_ok_frac is not None and central_ok_frac >= CENTRAL_FRAC_MIN

    # ── MTI mechanizm (klatki): diff_max vs próg, n_kept ──
    diffs = [m.get("diff_max") for m in mti if m.get("diff_max") is not None]
    nkept = [m.get("n_kept") for m in mti if m.get("n_kept") is not None]

    # §5c: PASS Biegu 2 = ENTRY in-window ∧ central-ok ≥80% klatek w kopercie (∧ mti k=3 — ENTRY tego wymaga).
    passed = bool(entry_in_window and mti_run >= ENTRY_K and box_on_target and central_gate)
    borderline = (not passed) and (mti_run in (ENTRY_K - 1, ENTRY_K - 2) or (n_entry > 0 and not entry_in_window)
                                   or (band_frac is not None and 0.3 <= band_frac < 0.5))
    # §4d: bieg który pada WYŁĄCZNIE na mechanice okna/rozgrzewki (timeout gotowości, ZERO percepcji) = NIE-BIEG.
    non_run = bool(ready_timeout or (ready_t is not None and len(dbg) == 0 and len(mti) == 0))

    rep = {
        "outdir": outdir,
        "verdict": "PASS" if passed else "FAIL",
        "borderline": borderline,
        "non_run(§4d)": non_run,
        "criteria": {
            "entry_in_window": entry_in_window,
            "mti_ok_run>=3": mti_run >= ENTRY_K,
            "box_on_target": box_on_target,
            "central_gate_5c(>=80%)": central_gate,
        },
        "central_ok_5c": {"n_env_frames": len(env_frames), "central_ok_frac": round(central_ok_frac, 3) if central_ok_frac is not None else None,
                          "frac_min": CENTRAL_FRAC_MIN, "cy_margin_med": round(_med(cy_margins), 3) if cy_margins else None,
                          "cy_margin_p90": round(_pctl(cy_margins, 90), 3) if cy_margins else None,
                          "cx_margin_med": round(_med(cx_margins), 3) if cx_margins else None,
                          "margin_thr": CENTRAL_MARGIN, "drone_alt_lever": "§5b vertical-centering (PROBE_ALT)"},
        "detector_ready(§4b)": {"ready_wall_s": ready_t, "timeout": ready_timeout,
                                 "window_clock": "sim_t@detector_ready" if ready_t is not None else "wall@arm"},
        "envelope_held(report-only,§3e)": envelope_held,
        "entry": {"n_entry": n_entry, "entry_t": entry_t, "range_at_entry_m": round(rng_at_entry, 2) if rng_at_entry is not None else None,
                  "ring_dwell_t": [round(ring_t_lo, 1) if ring_t_lo is not None else None, round(ring_t_hi, 1) if ring_t_hi is not None else None],
                  "entry_before_ring(report-only)": entry_before_ring, "first_in_ring_t": first_in_ring_t},
        "range_to_target_m": {"n": len(rng_ring), "min": round(min(r3), 2) if r3 else None,
                               "med": round(_med(r3), 2) if r3 else None, "max": round(max(r3), 2) if r3 else None,
                               "band_frac_7_9": round(band_frac, 3) if band_frac is not None else None},
        "mti": {"n_dbg_ticks": len(dbg), "mti_ok_longest_run": mti_run, "n_mti_ok": n_mti_ok,
                "n_comps_med": _med(n_comps), "n_comps_max": max(n_comps) if n_comps else None},
        "box_channel": {"n_box_samples": len(box_pts), "cx_med": round(cx_med, 3) if cx_med is not None else None,
                        "cy_med": round(cy_med, 3) if cy_med is not None else None,
                        "cx_std": round(cx_std, 3) if cx_std is not None else None,
                        "cy_std": round(cy_std, 3) if cy_std is not None else None, "central": central},
        "mti_frame_mechanism": {"n_frames": len(mti), "diff_max_med": _med(diffs),
                                 "diff_max_p90": _pctl(diffs, 90), "diff_thr": DIFF_THR,
                                 "diff_over_thr_frac": round(sum(1 for v in diffs if v is not None and v > DIFF_THR) / len(diffs), 3) if diffs else None,
                                 "n_kept_med": _med(nkept), "n_kept_max": max(nkept) if nkept else None},
        "note": "PROBE (§3d Bieg 1) — NIE próba, NIE materiał dema; percepcja nieraportowalna jako wynik aktu (SR-J2)",
    }
    print(json.dumps(rep, indent=2, ensure_ascii=False))
    json.dump(rep, open(os.path.join(outdir, "probe_t1.json"), "w"), indent=2, ensure_ascii=False)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
