#!/usr/bin/env python3
"""results/WK3/tools/wk3_kadr.py — CEL W KADRZE + przechył per epizod (PROMPT_WK3_S1 §1.3, PRE_WK3 §3).

DEFINICJA (FROZEN przed lotami, idzie verbatim do raportu):
  Tick = wiersz demo.jsonl (tick inferencji sieci) epizodu. GT celu = najbliższy wiersz gt_intruder.jsonl
  (|Δt_sim| ≤ 0.1 s) PRZEFILTROWANY świadkiem ERRATUM-DMIN (|ned − cmd_ned| ≤ 1 m; tick bez świadka
  wypada z mianownika i jest liczony osobno). Orientacja drona = najbliższy vehicle_attitude z ulogu
  (most czasu t_sim = ulog_us·1e-6, sprawdzany jak wk_r3_view: mediana |z_ulog − own_z| < 0.10 m).
  Rzut geometrią wk_r3_view.project (FX/FY/CX/CY z r02/mti.py, CAM_OFF_FRD z harness/feed_vision.py).
  „W KADRZE" ⇔ wk_r3_view.in_frame: cel przed kamerą (z_opt > 0) i środek celu w prostokącie obrazu
  zwężonym o margines MTI 10 px z każdej strony — pionowo = pół-pole 40.4° po marginesie, poziomo = pole
  kamery po marginesie. Kierunek wypadnięcia: DÓŁ (v ≥ IMG_H − 10), GÓRA (v ≤ 10), BOK (u poza pasem
  przy v w pasie, albo z_opt ≤ 0 = za kamerą).
  „Wypadnięcie poprzedza utratę tracka": utrata = przejście track_valid true → false; poprzedza, gdy
  w oknie [t_utraty − 2.0 s, t_utraty] jest ≥ 1 tick poza kadrem.
Import (READ-ONLY, nie kopia): results/WK_RECON/tools/wk_r3_view.py.

Użycie: wk3_kadr.py <out.json> <katalog_boota>...
"""
import bisect
import json
import math
import os
import statistics as st
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "results", "WK_RECON", "tools"))
from r02.mti import quat_to_R  # noqa: E402
from wk_r3_view import BORDER, IMG_H, in_frame, load_ulog, nearest, project  # noqa: E402

WITNESS_M = 1.0
GT_DT = 0.1
PRE_LOSS_S = 2.0


def pct(vals, q):
    return round(vals[int(q * (len(vals) - 1))], 2)


def side_of(u, v):
    if u is None:
        return "bok"
    if v >= IMG_H - BORDER:
        return "dol"
    if v <= BORDER:
        return "gora"
    return "bok"


def boot_kadr(d):
    att, lp = load_ulog(os.path.join(d, "boot.ulg"))
    ats, lts = list(att[0]), list(lp[0])
    gt = [json.loads(ln) for ln in open(os.path.join(d, "gt_intruder.jsonl")) if ln.strip()]
    gt_t = [g["t_sim"] for g in gt]
    eps, dz = {}, []
    for ln in open(os.path.join(d, "demo.jsonl")):
        r = json.loads(ln)
        eps.setdefault(r["scenario_id"], []).append(r)
    out = {"boot": os.path.relpath(d, ROOT), "epizody": {}}
    for sid, rows in eps.items():
        t0 = rows[0]["t_sim"]
        ticks, n_bez_swiadka, tilts = [], 0, []
        for r in rows:
            t_us = r["t_sim"] * 1e6
            dz.append(abs(lp[1][nearest(lts, t_us)] - r["own_pos_ned"][2]))
            q = att[1][nearest(ats, t_us)]
            R0 = None
            gi = min(max(bisect.bisect_left(gt_t, r["t_sim"]), 0), len(gt_t) - 1)
            if gi > 0 and abs(gt_t[gi - 1] - r["t_sim"]) < abs(gt_t[gi] - r["t_sim"]):
                gi -= 1
            g = gt[gi]
            ok_gt = (abs(g["t_sim"] - r["t_sim"]) <= GT_DT and g.get("episode_id") == r["episode_id"])
            if ok_gt and math.dist(g["ned"], g["cmd_ned"]) > WITNESS_M:
                n_bez_swiadka += 1
                ok_gt = False
            if ok_gt:
                u, v, R0 = project(g["ned"], r["own_pos_ned"], q)
                inv = in_frame(u, v)
                ticks.append({"t": r["t_sim"] - t0, "in": inv, "side": None if inv else side_of(u, v),
                              "valid": bool(r["track_valid"])})
            if R0 is None:
                R0 = quat_to_R(q)
            tilts.append(math.degrees(math.acos(max(-1.0, min(1.0, R0[2, 2])))))
        n = len(ticks)
        outs = [x for x in ticks if not x["in"]]
        # utraty tracka (true -> false) na wszystkich tickach epizodu
        losses = []
        for a, b in zip(rows, rows[1:]):
            if a["track_valid"] and not b["track_valid"]:
                losses.append(b["t_sim"] - t0)
        out_t = [x["t"] for x in outs]
        pre = [tl for tl in losses if any(tl - PRE_LOSS_S <= t <= tl for t in out_t)]
        tl_sorted = sorted(tilts)
        out["epizody"][sid] = {
            "n_tickow": len(rows), "n_z_gt_swiadek": n, "n_bez_swiadka": n_bez_swiadka,
            "frac_poza_kadrem": round(len(outs) / n, 4) if n else None,
            "frac_poza_dol": round(sum(x["side"] == "dol" for x in outs) / n, 4) if n else None,
            "frac_poza_gora": round(sum(x["side"] == "gora" for x in outs) / n, 4) if n else None,
            "frac_poza_bok": round(sum(x["side"] == "bok" for x in outs) / n, 4) if n else None,
            "pierwsze_wypadniecie_t_rel": round(out_t[0], 2) if out_t else None,
            "utraty_tracka_t_rel": [round(t, 2) for t in losses],
            "utraty_poprzedzone_wypadnieciem_t_rel": [round(t, 2) for t in pre],
            "przechyl_p50_p95_max": [pct(tl_sorted, 0.5), pct(tl_sorted, 0.95), round(tl_sorted[-1], 2)],
        }
    out["most_dz_med_m"] = round(st.median(dz), 4) if dz else None
    out["most_ok"] = bool(dz and st.median(dz) < 0.10)
    return out


def main():
    out, dirs = sys.argv[1], sys.argv[2:]
    res = [boot_kadr(os.path.abspath(d)) for d in dirs]
    for b in res:
        print(b["boot"], "most", b["most_dz_med_m"], b["most_ok"])
        for sid, e in b["epizody"].items():
            print(" ", sid, "poza", e["frac_poza_kadrem"], "dol/gora/bok", e["frac_poza_dol"], e["frac_poza_gora"],
                  e["frac_poza_bok"], "utraty", e["utraty_tracka_t_rel"], "poprzedzone",
                  e["utraty_poprzedzone_wypadnieciem_t_rel"], "przechyl", e["przechyl_p50_p95_max"])
    json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
