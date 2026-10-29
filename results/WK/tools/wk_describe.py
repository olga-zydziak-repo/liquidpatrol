#!/usr/bin/env python3
"""results/WK/tools/wk_describe.py — kontrole dymu i pomiary opisowe nogi WK (PRE_WK §2.1/§3, PROMPT §2.1/§2.7).

Per boot (zero bramek poza kontrolami dymu wypisanymi jawnie):
  MANIFEST: blok "wk" (świat, sha świata, pin x500_base), blok "perc2" (pin mono_cam, sonda preflight),
            world_hash.txt, valid_V2p per epizod.
  WIATR ZAŁADOWANY (dym): oś ciągu z ulogu (vehicle_attitude, ciąg = −R[:,2] w NED) uśredniona po tickach
            HOLD (cmd_v_ned = 0, dron trzyma pozycję): składowa pozioma wskazuje, skąd wieje (dron pochyla
            się POD wiatr). Wiatr +x ENU = na wschód ⇒ oczekiwane ciąg_E < 0 i przechył > baza stock.
            Dryf: mediana |GT drona − pozycja na początku okna hold| na tickach hold (GT z trace).
  ADMISJA: liczba ENTRY w percep_feed (brama struktura∧MTI, feed_vision.py:186); klatki z mti_ok.
  OPISOWE per epizod: alt_max i mediana cmd_vz (ticki aktywne), przechył p50/p95 (ulog, ticki aktywne),
            obecność celu w kadrze (rzut GT na kadr przy zapisanej orientacji — wk_r3_view.py, recon),
            czas do pierwszego track_valid od startu epizodu (demo.jsonl; track przeżywający z poprzedniego
            epizodu daje 0.0 — opisowe).

Użycie: wk_describe.py <out.json> <katalog_boota>...
"""
import bisect
import json
import math
import os
import statistics as st
import sys

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "results", "WK_RECON", "tools"))
from r02.mti import quat_to_R  # noqa: E402
from wk_r3_view import boot_stats as view_stats, load_ulog, nearest  # noqa: E402


def pct(xs, q):
    s = sorted(xs)
    return round(s[int(q * (len(s) - 1))], 3) if s else None


def describe(d):
    man = json.load(open(os.path.join(d, "manifest.json")))
    att, _ = load_ulog(os.path.join(d, "boot.ulg"))
    ats = list(att[0])
    rows = [json.loads(ln) for ln in open(os.path.join(d, "demo.jsonl"))]
    hold_thr_e, hold_thr_n, hold_tilt, act_tilt = [], [], [], []
    for r in rows:
        q = att[1][nearest(ats, r["t_sim"] * 1e6)]
        R = quat_to_R(q)
        thrust = -R[:, 2]
        tilt = math.degrees(math.acos(max(-1.0, min(1.0, R[2, 2]))))
        if any(abs(c) > 0 for c in r["cmd_v_ned"]):
            act_tilt.append(tilt)
        else:
            hold_thr_n.append(float(thrust[0])); hold_thr_e.append(float(thrust[1])); hold_tilt.append(tilt)
    # dryf w hold z demo (own_pos EKF; GT pozycji drona ≈ EKF: |EKF−GT| ~0.1 m, w_judge)
    drift = []
    seg0 = None
    for r in rows:
        if not any(abs(c) > 0 for c in r["cmd_v_ned"]):
            if seg0 is None:
                seg0 = r["own_pos_ned"]
            drift.append(math.hypot(r["own_pos_ned"][0] - seg0[0], r["own_pos_ned"][1] - seg0[1]))
        else:
            seg0 = None
    # percep_feed
    n_entry = n_frames = n_mti = n_box = 0
    pf = os.path.join(d, "percep_feed.jsonl")
    if os.path.exists(pf):
        for ln in open(pf):
            r = json.loads(ln)
            if "t_frame" not in r:
                continue
            n_frames += 1
            n_entry += r.get("ev") == "ENTRY"
            n_box += r.get("box") is not None
            n_mti += bool(r.get("mti_ok"))
    # per epizod
    eps = {}
    for r in rows:
        eps.setdefault(r["scenario_id"], []).append(r)
    per = []
    vs = view_stats(d)
    for sid, er in eps.items():
        act = [r for r in er if any(abs(c) > 0 for c in r["cmd_v_ned"])]
        t0 = er[0]["t_sim"]
        acq = next((r["t_sim"] - t0 for r in er if r.get("track_valid")), None)
        per.append({"scenario_id": sid,
                    "alt_max_m": round(max(-r["own_pos_ned"][2] for r in er), 3),
                    "cmd_vz_med": round(st.median([r["cmd_v_ned"][2] for r in act]), 4) if act else None,
                    # pierwszy wiersz epizodu z track_valid (track może przetrwać z poprzedniego epizodu ⇒ 0.0)
                    "t_pierwszy_track_valid_s": None if acq is None else round(acq, 3),
                    "w_kadrze_frac": vs.get("per_epizod_frac_inview", {}).get(sid)})
    wk = man.get("wk", {})
    p2 = man.get("perc2", {})
    sonda = (p2.get("sondy") or [{}])[0].get("sonda", {}) if p2.get("sondy") else {}
    return {
        "boot": os.path.relpath(d, ROOT),
        "wk": wk, "pin_mono_cam": p2.get("pin_mono_cam_model_sdf"),
        "world_hash_txt": open(os.path.join(d, "world_hash.txt")).read().strip()
                          if os.path.exists(os.path.join(d, "world_hash.txt")) else None,
        "sonda_preflight_rc": p2.get("sonda_preflight_rc"), "uzbrojony_po_sondzie": p2.get("uzbrojony_po_sondzie"),
        "sonda": {k: sonda.get(k) for k in ("dt_p50_s_na_klatke", "frac_delt_gt_0p10", "hz_p50", "werdykt")},
        "n_episodes": man.get("n_episodes"), "n_valid_V2p": man.get("n_valid_V2p"),
        "wiatr": {"hold_n": len(hold_tilt),
                  "hold_ciag_N_sr": round(float(np.mean(hold_thr_n)), 4) if hold_thr_n else None,
                  "hold_ciag_E_sr": round(float(np.mean(hold_thr_e)), 4) if hold_thr_e else None,
                  "hold_przechyl_p50": pct(hold_tilt, 0.5), "hold_przechyl_p95": pct(hold_tilt, 0.95),
                  "hold_dryf_p50_m": pct(drift, 0.5), "hold_dryf_p95_m": pct(drift, 0.95)},
        "przechyl_aktywny_p50": pct(act_tilt, 0.5), "przechyl_aktywny_p95": pct(act_tilt, 0.95),
        "percep": {"n_frames": n_frames, "n_box": n_box, "n_ENTRY": n_entry,
                   "frac_mti_ok": round(n_mti / n_frames, 4) if n_frames else None},
        "epizody": per,
    }


def main():
    out, dirs = sys.argv[1], sys.argv[2:]
    res = [describe(os.path.abspath(d)) for d in dirs]
    for r in res:
        print(json.dumps({k: r[k] for k in ("boot", "wk", "sonda_preflight_rc", "n_valid_V2p", "wiatr",
                                            "przechyl_aktywny_p50", "przechyl_aktywny_p95", "percep")},
                         ensure_ascii=False))
        for e in r["epizody"]:
            print("   ", e)
    json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
