#!/usr/bin/env python3
"""results/PERC2_RECON/tools/perc2_r3.py — R3 PROMPT_PERC2_S0: MTI-czołowy — mechanizm
(z metadanych kampanii) i mierzalność (pokrycie zbiorów klatek ery DET).

A. MECHANIZM: w oknach czołowych-kotwicach (te same co R1) per klatka z boxem on-frame:
   ruch środka boxa [px/klatkę], wzrost szerokości [px/klatkę], rozmiar [px] — kontrast
   klatek mti_ok=T vs F, zestawiony z progami FROZEN: persist_move_thr 0.10 znorm.
   (r02/mti.py:40 ⇒ 64 px poziomo), min_area_px 8 (mti.py:35), diff_thr 22 (mti.py:30
   — intensywność residuum, NIEmierzalna z metadanych: nazwane).
B. POKRYCIE ZBIORÓW DET (results/DET/labels/D*/meta.jsonl, klatki results/DET/collect):
   per zbiór: kadencja, klatki OK, segmenty CZOŁOWE (Z∈[5,18], |Δśrodek|≤5 px/kl,
   Z malejące) — czy offline re-run MTI z innymi progami ma na czym mierzyć czołowość.
Wyjście: r3_mti.json + stdout.
"""
import json
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
for p in (ROOT, os.path.join(ROOT, "results", "POSCIG_RECON", "tools")):
    if p not in sys.path:
        sys.path.insert(0, p)

from poscig_recon import Episode, interp, iter_jsonl  # READ-ONLY

OUTD = os.path.join(ROOT, "results", "PERC2_RECON")
HALF_CONE = 43.45
GAP_S = 0.6
ANCHORS = [("c08_s01", "SZYBKI"), ("c08_s02", "WOLNY_PASS"), ("c09_s04", "WOLNY_PASS"),
           ("c10_s04", "WOLNY_PASS"), ("c08_s03", "WOLNY_FAIL"), ("c08_s04", "WOLNY_FAIL"),
           ("c10_s02", "WOLNY_FAIL")]
_TR1 = json.load(open(os.path.join(ROOT, "results", "TRANSIT_RECON", "r1_anatomia.json")))
T_DMIN = {e["sid"]: e["bliskie_przejscie"]["t_rel"] for e in _TR1["episodes"]}


def pct(xs, q):
    if not xs:
        return None
    xs = sorted(xs)
    return xs[min(len(xs) - 1, max(0, int(round(q * (len(xs) - 1)))))]


def yaw_of(q):
    w, x, y, z = q
    return math.degrees(math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z)))


def wrap(a):
    return (a + 180.0) % 360.0 - 180.0


def window_frames(sid, grp):
    """Okno radialne jak w R1 (max n_box przed t_acq+1 / przed d_min dla FAIL)."""
    epi = Episode("FANTOM_S2", "V2", sid)
    d = os.path.join(ROOT, epi.dir)
    t0, tend = epi.t0, epi.t_end_demo
    pf = [r for r in iter_jsonl(os.path.join(d, "percep_feed.jsonl"))
          if r.get("t_frame") is not None and r.get("own_q") and t0 <= r["t_frame"] <= tend]
    pf.sort(key=lambda r: r["t_frame"])
    rows = []
    for r in pf:
        yw = yaw_of(r["own_q"])
        g = interp(epi.intr, r["t_frame"])
        op = r["own_pos_ned"]
        az = math.degrees(math.atan2(g[1] - op[1], g[0] - op[0]))
        be = wrap(az - yw)
        rows.append({"t": r["t_frame"] - t0, "in_cone": abs(be) <= HALF_CONE,
                     "box": r.get("box"), "mti": bool(r.get("mti_ok")),
                     "dh": math.hypot(g[0] - op[0], g[1] - op[1])})
    covs, cur = [], None
    for row in rows:
        if row["in_cone"]:
            if cur is None or (row["t"] - cur[-1]["t"]) > GAP_S:
                cur = []
                covs.append(cur)
            cur.append(row)
        else:
            cur = None
    tcut = (epi.t_acq + 1.0) if epi.t_acq is not None else 1e9
    tdmin = T_DMIN.get(sid)
    if grp == "WOLNY_FAIL" and tdmin is not None:
        tcut = min(tcut, tdmin)
    cands = [c for c in covs if c[0]["t"] < tcut
             and (grp != "WOLNY_FAIL" or tdmin is None or c[-1]["t"] < tdmin)
             and sum(1 for x in c if x["box"]) >= 3]
    return max(cands, key=lambda c: sum(1 for x in c if x["box"])) if cands else []


def mech_a():
    out = []
    for sid, grp in ANCHORS:
        win = window_frames(sid, grp)
        prev = None
        dcT, dcF, dwT, dwF, wT, wF = [], [], [], [], [], []
        for x in win:
            b = x["box"]
            if not b:
                prev = None
                continue
            u, v, w = b[0] * 640, b[1] * 480, b[2] * 640
            if prev is not None:
                dc = math.hypot(u - prev[0], v - prev[1])
                dw = abs(w - prev[2])
                (dcT if x["mti"] else dcF).append(dc)
                (dwT if x["mti"] else dwF).append(dw)
            (wT if x["mti"] else wF).append(w)
            prev = (u, v, w)
        out.append({"sid": sid, "grupa": grp, "n_klatek": len(win),
                    "dh_okno": [round(win[0]["dh"], 1), round(win[-1]["dh"], 1)] if win else None,
                    "mti_T": {"n": len(wT), "dc_px_kl_p50": pct(dcT, 0.5), "dc_px_kl_p90": pct(dcT, 0.9),
                              "dw_px_kl_p50": pct(dwT, 0.5), "w_px_p50": pct(wT, 0.5)},
                    "mti_F": {"n": len(wF), "dc_px_kl_p50": pct(dcF, 0.5), "dc_px_kl_p90": pct(dcF, 0.9),
                              "dw_px_kl_p50": pct(dwF, 0.5), "w_px_p50": pct(wF, 0.5)}})
    return out


def coverage_b():
    base = os.path.join(ROOT, "results", "DET", "labels")
    sets = sorted(d for d in os.listdir(base) if d.startswith("D") and
                  os.path.isdir(os.path.join(base, d)))
    out = []
    for s in sets:
        meta = [r for r in iter_jsonl(os.path.join(base, s, "meta.jsonl"))
                if r.get("flag") == "OK"]
        meta.sort(key=lambda r: r["t"])
        n_frontal = 0
        seg = 0
        best_seg = 0
        dts = []
        zb = {}
        prev = None
        for r in meta:
            u, v, Z = r["uvZ"]
            zb[int(Z // 2) * 2] = zb.get(int(Z // 2) * 2, 0) + 1
            if prev is not None:
                dt = r["t"] - prev["t"]
                if 0 < dt < 0.5:
                    dts.append(dt)
                    dc = math.hypot(u - prev["uvZ"][0], v - prev["uvZ"][1])
                    dZ = Z - prev["uvZ"][2]
                    if 5.0 <= Z <= 18.0 and dc <= 5.0 and dZ < 0:
                        n_frontal += 1
                        seg += 1
                        best_seg = max(best_seg, seg)
                    else:
                        seg = 0
                else:
                    seg = 0
            prev = r
        out.append({"zbior": s, "n_OK": len(meta),
                    "hz_p50": round(1.0 / pct(dts, 0.5), 2) if dts else None,
                    "klatki_czolowe_5_18": n_frontal,
                    "najdluzszy_segment_czolowy_kl": best_seg,
                    "Z_bins": dict(sorted(zb.items()))})
    return out


def main():
    a = mech_a()
    print("=== A. MECHANIZM (okna czołowe) ===")
    for r in a:
        print(f"[{r['grupa']:10s} {r['sid']}] n={r['n_klatek']} dh={r['dh_okno']} "
              f"T(n={r['mti_T']['n']}, dc={r['mti_T']['dc_px_kl_p50']}, dw={r['mti_T']['dw_px_kl_p50']}, "
              f"w={r['mti_T']['w_px_p50']}) F(n={r['mti_F']['n']}, dc={r['mti_F']['dc_px_kl_p50']}, "
              f"dw={r['mti_F']['dw_px_kl_p50']}, w={r['mti_F']['w_px_p50']})")
    b = coverage_b()
    print("=== B. POKRYCIE ZBIORÓW DET ===")
    for r in b:
        print(f"[{r['zbior']}] OK={r['n_OK']} hz={r['hz_p50']} czołowe={r['klatki_czolowe_5_18']} "
              f"maxseg={r['najdluzszy_segment_czolowy_kl']} Zbins={r['Z_bins']}")
    json.dump({"progi_frozen": {"diff_thr": 22, "min_area_px": 8, "max_area_frac": 0.20,
                                "persist_m": 3, "persist_window": 4, "persist_move_thr": 0.10,
                                "zrodlo": "r02/mti.py:28-40"},
               "mechanizm_okna": a, "pokrycie_zbiorow_DET": b},
              open(os.path.join(OUTD, "r3_mti.json"), "w"), indent=1)
    print("zapisano r3_mti.json")


if __name__ == "__main__":
    main()
