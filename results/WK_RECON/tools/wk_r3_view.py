#!/usr/bin/env python3
"""results/WK_RECON/tools/wk_r3_view.py — R3 PRZECHYŁ × KAMERA (PROMPT_WK_S0 §R3), 0 bootów.

Rzut GT intruza na kadr kamery z ZAPISANEJ orientacji lotu (ulog vehicle_attitude), na tickach
aktywnych epizodów (cmd_v_ned ≠ 0). Odpowiada na pytanie: gdyby w danym locie (np. kampania W,
feed emulowany) leciała kamera, czy cel byłby w kadrze — przy RZECZYWISTYM przechyle od wiatru
i RZECZYWISTEJ wysokości sieci (pełzanie R2).

Geometria literą programu (import READ-ONLY): FX/FY/CX/CY/IMG_W/IMG_H i quat_to_R z r02/mti.py,
CAM_OFF_FRD z harness/feed_vision.py:47; ramka optyczna jak feed_vision.box_to_ned (odwrotność):
p_frd = Rᵀ(gt − own) − cam_off; z_opt = x_frd, x_opt = y_frd, y_opt = z_frd; u = CX + FX·x/z, v = CY + FY·y/z.
W KADRZE ⇔ z_opt > 0 ∧ środek celu w prostokącie zwężonym o border_erode = 10 px (r02/mti.py:33 —
MTI odrzuca komponent dotykający marginesu, mti.py:113-116).

Most czasu: ulog timestamp [us] ≈ t_sim·1e6 (lockstep SITL; tools/w_tilt.py:16 — konwencja W).
SPRAWDZANY per boot: mediana |z_ulog(vehicle_local_position) − own_z(demo)| na tickach aktywnych
musi być < 0.10 m, inaczej boot odrzucony (pole most_ok=False).

RE-YAW (synteza kursu trybu kamerowego): kampania W latała harnessem 3a52e19f SPRZED naprawy N1
(rad→deg yaw na granicy MAVSDK, 5af1e542 05.10, bench_flight.py:398-403) — jej kurs NIE jest kursem
trybu kamerowego (kontroler celuje yaw = atan2(rel), net_controller.py:117). Synteza: oś ciągu
b3 = R[:,2] z ulogu ZACHOWANA (przechył od wiatru i manewru), kurs obrócony na cel:
x' = norm(h − (h·b3)b3), h = (cos ψ, sin ψ, 0), ψ = atan2(rel_e, rel_n); y' = b3 × x'; R' = [x' y' b3].
Pierwsze przybliżenie multikoptera: wektor ciągu nie zależy od kursu. WALIDACJA: na lotach kamerowych
(kurs już na cel) frakcja w kadrze z R' musi się zgadzać z frakcją z R (pole inview_reyaw obok inview).

Kąt osi kamery: pitch_cam = asin(−R[2,0]) (oś x FRD w NED; > 0 = kamera w górę).
Elewacja celu względem horyzontu: elev = atan2(−(gt_d − own_d), d_h) (< 0 = cel poniżej).

Użycie: wk_r3_view.py <out.json> <katalog_boota>...
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
from r02.mti import FX, FY, CX, CY, IMG_W, IMG_H, quat_to_R  # noqa: E402
from harness.feed_vision import CAM_OFF_FRD  # noqa: E402

BORDER = 10
sys.path.insert(0, os.path.join(ROOT, "results", "WK_RECON", "tools"))
from wk_r2_creep import classify  # noqa: E402


def load_ulog(path):
    from pyulog import ULog
    ul = ULog(path, ["vehicle_attitude", "vehicle_local_position"])
    att = lp = None
    for d in ul.data_list:
        if d.name == "vehicle_attitude" and att is None:
            att = (np.asarray(d.data["timestamp"], dtype=np.float64),
                   np.stack([d.data[f"q[{i}]"] for i in range(4)], axis=1))
        if d.name == "vehicle_local_position" and lp is None:
            lp = (np.asarray(d.data["timestamp"], dtype=np.float64), np.asarray(d.data["z"], dtype=np.float64))
    return att, lp


def nearest(ts, t_us):
    i = bisect.bisect_left(ts, t_us)
    if i <= 0:
        return 0
    if i >= len(ts):
        return len(ts) - 1
    return i if abs(ts[i] - t_us) < abs(ts[i - 1] - t_us) else i - 1


def load_gt(path):
    rows = [json.loads(ln) for ln in open(path) if ln.strip()]
    return [r["t_sim"] for r in rows], [r["ned"] for r in rows]


def project(gt, own, q):
    R = quat_to_R(q)
    p_ned = np.array(gt) - np.array(own)
    p_frd = R.T @ p_ned - np.array(CAM_OFF_FRD)
    z, x, y = p_frd[0], p_frd[1], p_frd[2]
    if z <= 0:
        return None, None, R
    return CX + FX * x / z, CY + FY * y / z, R


def reyaw(R, dn, de):
    b3 = R[:, 2]
    psi = math.atan2(de, dn)
    h = np.array([math.cos(psi), math.sin(psi), 0.0])
    x = h - (h @ b3) * b3
    x = x / np.linalg.norm(x)
    y = np.cross(b3, x)
    return np.stack([x, y, b3], axis=1)


def in_frame(u, v):
    return bool(u is not None and BORDER < u < IMG_W - BORDER and BORDER < v < IMG_H - BORDER)


def project_R(gt, own, R):
    p_frd = R.T @ (np.array(gt) - np.array(own)) - np.array(CAM_OFF_FRD)
    z, x, y = p_frd[0], p_frd[1], p_frd[2]
    if z <= 0:
        return None, None
    return CX + FX * x / z, CY + FY * y / z


def boot_stats(d):
    man = json.load(open(os.path.join(d, "manifest.json")))
    cls = classify(man, d)
    att, lp = load_ulog(os.path.join(d, "boot.ulg"))
    gt_t, gt_p = load_gt(os.path.join(d, "gt_intruder.jsonl"))
    ats = list(att[0]); lts = list(lp[0])
    out = {"boot": os.path.relpath(d, ROOT), **cls}
    dz, rows = [], []
    for ln in open(os.path.join(d, "demo.jsonl")):
        r = json.loads(ln)
        if not any(abs(c) > 0 for c in r["cmd_v_ned"]):
            continue
        t_us = r["t_sim"] * 1e6
        dz.append(abs(lp[1][nearest(lts, t_us)] - r["own_pos_ned"][2]))
        gi = bisect.bisect_left(gt_t, r["t_sim"])
        gi = min(max(gi, 0), len(gt_t) - 1)
        if abs(gt_t[gi] - r["t_sim"]) > 0.1:
            continue
        q = att[1][nearest(ats, t_us)]
        u, v, R = project(gt_p[gi], r["own_pos_ned"], q)
        dn, de = gt_p[gi][0] - r["own_pos_ned"][0], gt_p[gi][1] - r["own_pos_ned"][1]
        dh = math.hypot(dn, de)
        elev = math.degrees(math.atan2(-(gt_p[gi][2] - r["own_pos_ned"][2]), dh))
        pitch = math.degrees(math.asin(max(-1.0, min(1.0, -R[2, 0]))))
        tilt = math.degrees(math.acos(max(-1.0, min(1.0, R[2, 2]))))
        inview = in_frame(u, v)
        R2 = reyaw(R, dn, de)
        u2, v2 = project_R(gt_p[gi], r["own_pos_ned"], R2)
        pitch2 = math.degrees(math.asin(max(-1.0, min(1.0, -R2[2, 0]))))
        rows.append({"sid": r["scenario_id"], "d": dh, "elev": elev, "pitch": pitch, "tilt": tilt,
                     "u": u, "v": v, "inview": inview, "alt": -r["own_pos_ned"][2],
                     "u2": u2, "v2": v2, "inview2": in_frame(u2, v2), "pitch2": pitch2,
                     "v2_margin_px": (None if v2 is None else min(v2 - BORDER, IMG_H - BORDER - v2))})
    out["most_dz_med_m"] = round(st.median(dz), 4) if dz else None
    out["most_ok"] = bool(bool(dz) and st.median(dz) < 0.10)
    out["n"] = len(rows)
    if rows:
        out["frac_inview"] = round(sum(x["inview"] for x in rows) / len(rows), 4)
        out["frac_inview_band6_10"] = (lambda b: round(sum(x["inview"] for x in b) / len(b), 4) if b else None)(
            [x for x in rows if 6 <= x["d"] <= 10])
        out["frac_out_bottom"] = round(sum(1 for x in rows if x["v"] is not None and x["v"] >= IMG_H - BORDER) / len(rows), 4)
        out["frac_out_top"] = round(sum(1 for x in rows if x["v"] is not None and x["v"] <= BORDER) / len(rows), 4)
        out["frac_behind_or_side"] = round(sum(1 for x in rows if x["u"] is None or not (BORDER < x["u"] < IMG_W - BORDER)) / len(rows), 4)
        out["inview_reyaw"] = round(sum(x["inview2"] for x in rows) / len(rows), 4)
        b2 = [x for x in rows if 6 <= x["d"] <= 10]
        out["inview_reyaw_band6_10"] = round(sum(x["inview2"] for x in b2) / len(b2), 4) if b2 else None
        out["reyaw_out_bottom"] = round(sum(1 for x in rows if x["v2"] is not None and x["v2"] >= IMG_H - BORDER) / len(rows), 4)
        out["reyaw_out_top"] = round(sum(1 for x in rows if x["v2"] is not None and x["v2"] <= BORDER) / len(rows), 4)
        mg = sorted(x["v2_margin_px"] for x in rows if x["v2_margin_px"] is not None)
        if mg:
            out["reyaw_vmargin_px_p05"] = round(mg[int(0.05 * (len(mg) - 1))], 1)
            out["reyaw_vmargin_px_p50"] = round(mg[len(mg) // 2], 1)
        for k in ("tilt", "pitch", "pitch2", "elev", "alt"):
            vals = sorted(x[k] for x in rows)
            out[k + "_p50"] = round(vals[len(vals) // 2], 2)
            out[k + "_p05"] = round(vals[int(0.05 * (len(vals) - 1))], 2)
            out[k + "_p95"] = round(vals[int(0.95 * (len(vals) - 1))], 2)
        # per epizod: frakcja w kadrze
        per = {}
        for x in rows:
            per.setdefault(x["sid"], []).append(x["inview"])
        out["per_epizod_frac_inview"] = {k: round(sum(v) / len(v), 4) for k, v in per.items()}
        per2 = {}
        for x in rows:
            per2.setdefault(x["sid"], []).append(x["inview2"])
        out["per_epizod_inview_reyaw"] = {k: round(sum(v) / len(v), 4) for k, v in per2.items()}
    return out


def main():
    out, dirs = sys.argv[1], sys.argv[2:]
    res = []
    for d in dirs:
        need = ("manifest.json", "demo.jsonl", "boot.ulg", "gt_intruder.jsonl")
        if not all(os.path.exists(os.path.join(d, f)) for f in need):
            continue
        try:
            s = boot_stats(d)
        except Exception as e:  # noqa: BLE001 — log uszkodzony: zapisz i jedź dalej
            s = {"boot": os.path.relpath(d, ROOT), "blad": repr(e)}
        res.append(s)
        print(s.get("boot"), s.get("world"), s.get("controller"), s.get("feed"), "n", s.get("n"),
              "most", s.get("most_dz_med_m"), "inview", s.get("frac_inview"), "band", s.get("frac_inview_band6_10"),
              "REYAW", s.get("inview_reyaw"), s.get("inview_reyaw_band6_10"), "bottom", s.get("reyaw_out_bottom"),
              "vmargin p05", s.get("reyaw_vmargin_px_p05"), "tilt p50/p95", s.get("tilt_p50"), s.get("tilt_p95"),
              "pitch2 p05/p95", s.get("pitch2_p05"), s.get("pitch2_p95"), "alt p95", s.get("alt_p95"))
    json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
