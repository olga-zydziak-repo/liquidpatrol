#!/usr/bin/env python3
"""results/WK2_RECON/tools/wk2_rtf.py — R4 WAŻNOŚĆ: rozkład dsim/dwall (pole manifestu per epizod, sędzia
bazowy 8ec0fcfb → bench_finalize) w grupach habitatów, żeby rozdzielić koszt WindEffects od kosztu percepcji.

Grupy (z manifestu: world_hash + obecność bloku feed_v2/perc2):
  A3 + percep (FEED=V2)      — PERC2 S2, FANTOM S2 V2      : percepcja TAK, WindEffects NIE
  A3 bez percep (FEED=B)     — LIQ ncp, FANTOM S2 B        : percepcja NIE, WindEffects NIE
  W (world_wind_*)           — kampania W                   : percepcja NIE, WindEffects TAK
  WK (world_wk_*) + percep   — noga WK                      : percepcja TAK, WindEffects TAK
  WK2 kalibracja             — ten recon                    : percepcja w tle, WindEffects TAK (skala ≠ 1)
Użycie: wk2_rtf.py <out.json> <katalog_boota>...
"""
import json
import os
import statistics as st
import sys


def group(m):
    wh = (m.get("world_hash") or "").split()[-1] if m.get("world_hash") else ""
    w = os.path.basename(wh).replace(".sdf", "")
    perc = ("feed_v2" in m) or ("perc2" in m)
    if w.startswith("world_wk2_"):
        return "WK2 kalibracja (" + w + ")"
    if w.startswith("world_wk_"):
        return "WK + percep"
    if w.startswith("world_wind_"):
        return "W (WindEffects, bez percep)"
    return "A3 + percep" if perc else "A3 bez percep"


def main():
    out, dirs = sys.argv[1], sys.argv[2:]
    g = {}
    for d in dirs:
        mp = os.path.join(d, "manifest.json")
        if not os.path.exists(mp):
            continue
        m = json.load(open(mp))
        for e in m.get("episodes", []):
            if e.get("dsim_dwall") is not None:
                g.setdefault(group(m), []).append((e["dsim_dwall"], e.get("n_deep_stall"), e.get("valid_V2p")))
    res = {}
    for k, v in sorted(g.items()):
        x = sorted(a for a, _, _ in v)
        res[k] = {"n_ep": len(x), "dsw_min": round(x[0], 4), "dsw_p10": round(x[int(0.1 * (len(x) - 1))], 4),
                  "dsw_p50": round(st.median(x), 4), "dsw_max": round(x[-1], 4),
                  "frac_lt_0p90": round(sum(1 for a in x if a < 0.90) / len(x), 4),
                  "n_deep_p50": st.median([b for _, b, _ in v if b is not None]) if any(b is not None for _, b, _ in v) else None,
                  "frac_valid_V2p": round(sum(1 for *_, c in v if c) / len(v), 4)}
        print(k, res[k])
    json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
