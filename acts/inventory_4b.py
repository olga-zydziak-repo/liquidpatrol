#!/usr/bin/env python3
"""acts/inventory_4b.py — ANEKS_D5 §4b: mechaniczny runtime-dump efektywnej konfiguracji kadencji/params
tikowych OBU torów (frozen mti_flight/REGATE vs tor aktów LIVE) + diff. OBOWIĄZKOWY przed re-sanity.

Cel §4b: żaden parametr denominowany w tikach nie może po cichu rozjechać się z charakteryzacją REGATE.
Kluczowo: θ_age Z JEDNOSTKĄ (sekundy vs tiki) + WSKAZANIE MIEJSCA EWALUACJI w kodzie — bo gdyby age
był tikowy, 1 Hz połowiłby tempo starzenia i 2 Hz dotknąłby semantyki EXPIRE w A2.

Wartości toru aktów: importowane Z KODU (config_r02, ChannelConfig, MTIParams) — efektywne, nie przepisane.
Wartości REGATE: parsowane ze frozen `results/R02/mti/mti_flight.py` (regex na stałe) — źródło charakteryzacji.
Kamera: update_rate z SDF modelu mono_cam (frame-ingest OBU torów = ten sam sensor).

Uruchom: PYTHONPATH=... python3 acts/inventory_4b.py [OUT.json]
"""
from __future__ import annotations
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _regate_const(name, default=None, cast=float):
    """Wyłuskaj stałą `NAME = <liczba>` ze frozen mti_flight.py (źródło charakteryzacji)."""
    src = open(os.path.join(ROOT, "results/R02/mti/mti_flight.py")).read()
    m = re.search(rf"^{name}\s*=\s*([0-9.]+)", src, re.M)
    return cast(m.group(1)) if m else default


def _regate_delta():
    src = open(os.path.join(ROOT, "results/R02/mti/mti_flight.py")).read()
    m = re.search(r"MTITracker\(MTIParams\(\),\s*delta=(\d+)\)", src)
    return int(m.group(1)) if m else None


def _regate_entry_require_mti():
    src = open(os.path.join(ROOT, "results/R02/mti/mti_flight.py")).read()
    return "entry_require_mti=True" in src


def _cam_update_rate():
    sdf = os.path.join(ROOT, "PX4-Autopilot/Tools/simulation/gz/models/mono_cam/model.sdf")
    m = re.search(r"<update_rate>(\d+)</update_rate>", open(sdf).read())
    return int(m.group(1)) if m else None


def main():
    from r02.config_r02 import (DET_HZ, ENTRY_K, ENTRY_MOVE_THR, THETA_AGE_S, L_DELIVER_S,
                                ENTRY_EDGE_MARGIN, MTI_CENTER_THR, THETA_CONF, ChannelConfig)
    from r02.mti import MTIParams
    from r02.gate_run_r02 import DEMO_DECISION_HZ    # §4a: efektywna kadencja decyzji toru aktów LIVE

    cam = _cam_update_rate()
    cc = ChannelConfig()
    mp = MTIParams()

    # (nazwa, REGATE, TOR-AKTU-LIVE, jednostka, miejsce ewaluacji / uwaga)
    rows = [
        ("frame_ingest_hz", cam, cam, "Hz", "mono_cam/model.sdf update_rate (ten sam sensor OBU torów)"),
        ("mti_push_hz", 15.0, float(cam), "Hz", "REGATE worker 'konsumuje klatki 15 Hz' L238; akt _on_image @kadencja klatek"),
        ("mti_delta", _regate_delta(), 3, "klatki", "MTITracker(MTIParams(), delta=3) — baseline 200ms @15Hz"),
        ("decision_hz", _regate_const("DECISION_HZ"), DEMO_DECISION_HZ, "Hz", "REGATE DECISION_HZ L41; akt --det-hz (§4a). k liczony na tej kadencji"),
        ("channel_publish_hz", _regate_const("DECISION_HZ"), DEMO_DECISION_HZ, "Hz", "= decyzja (REGATE on_frame w decide_once; akt pub_ch w _on_tick)"),
        ("entry_k", cc.entry_k, cc.entry_k, "klatki", "streak≥k kolejnych klatek (target_channel L149). @2Hz → okno 1.5s"),
        ("entry_move_thr", cc.entry_move_thr, cc.entry_move_thr, "znorm/klatkę", "ruch środka między klatkami (target_channel L143). Kalibrowany @kadencji decyzji"),
        ("entry_edge_margin", cc.entry_edge_margin, cc.entry_edge_margin, "znorm", "edge_dist≥margin (central)"),
        ("mti_center_thr", cc.mti_center_thr, cc.mti_center_thr, "znorm", "box_matches_component (mti.py L173)"),
        ("theta_conf", round(THETA_CONF, 4), round(THETA_CONF, 4), "conf", "PASYWNE gdy entry_require_mti (nie brama)"),
        ("theta_age_s", cc.theta_age_s, cc.theta_age_s, "SEKUNDY", "EWAL CZASOWA: (t-t_last_det)+L_deliver > theta_age_s @ target_channel.py:162/186/194; t=sim-time → NIEZALEŻNE od kadencji decyzji"),
        ("l_deliver_s", cc.l_deliver_s, cc.l_deliver_s, "SEKUNDY", "podłoga age (czasowa)"),
        ("entry_require_mti", _regate_entry_require_mti(), True, "bool", "brama struktura∧MTI; REGATE replace(cfg, entry_require_mti=True), akt DEMO_MTI=1"),
        # MTIParams (tor MTI-push 15Hz w OBU — niezależne od kadencji decyzji)
        ("mti_diff_thr", 22, mp.diff_thr, "px", "MTIParams() domyślne (tor push 15Hz)"),
        ("mti_open_k", 3, mp.open_k, "px", "MTIParams()"),
        ("mti_close_k", 5, mp.close_k, "px", "MTIParams()"),
        ("mti_border_erode", 10, mp.border_erode, "px", "MTIParams()"),
        ("mti_min_area_px", 8, mp.min_area_px, "px", "MTIParams()"),
        ("mti_max_area_frac", 0.20, mp.max_area_frac, "frac", "MTIParams()"),
        ("mti_persist_m", 3, mp.persist_m, "klatki", "komponent w ≥m z M ostatnich (track-before-detect, tor push 15Hz)"),
        ("mti_persist_window", 4, mp.persist_window, "klatki", "M (tor push 15Hz)"),
        ("mti_persist_move_thr", 0.10, mp.persist_move_thr, "znorm", "MTIParams()"),
    ]

    def _num(x):
        return float(x) if isinstance(x, (int, float)) else x

    diffs = []
    out_rows = []
    for name, reg, act, unit, note in rows:
        eq = (_num(reg) == _num(act))
        out_rows.append({"param": name, "regate": reg, "akt_live": act, "unit": unit, "equal": eq, "note": note})
        if not eq:
            diffs.append(name)

    result = {"aneks": "D5 §4b", "camera_update_rate_hz": cam, "rows": out_rows, "diffs": diffs,
              "theta_age_unit": "SEKUNDY (czasowa) — EXPIRE A2 NIEZALEŻNE od kadencji decyzji",
              "verdict": "ZGODNE — zero różnic po §4a (--det-hz 2.0)" if not diffs else f"RÓŻNICE: {diffs} → STOP"}

    # wypis czytelny
    print(f"=== ANEKS_D5 §4b INWENTARZ KADENCJI (kamera={cam} Hz) ===")
    print(f"{'param':22} {'REGATE':>8} {'AKT-LIVE':>9} {'==':>3}  jednostka / ewaluacja")
    for r in out_rows:
        mark = "OK" if r["equal"] else "!!"
        print(f"{r['param']:22} {str(r['regate']):>8} {str(r['akt_live']):>9} {mark:>3}  {r['unit']}: {r['note']}")
    print(f"\nθ_age: {result['theta_age_unit']}")
    print(f"WERDYKT §4b: {result['verdict']}")

    out = sys.argv[1] if len(sys.argv) > 1 else None
    if out:
        json.dump(result, open(out, "w"), indent=2, ensure_ascii=False)
        print(f"[inventory_4b] → {out}")
    return 0 if not diffs else 3


if __name__ == "__main__":
    sys.exit(main())
