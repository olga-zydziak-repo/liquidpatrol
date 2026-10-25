#!/usr/bin/env python3
"""results/PERC2/tools/perc2_sonda.py — SONDA KADENCJI (PRE_PERC2 §2.2; czysty ops).

Zero importów z toru percepcji: czyta WYŁĄCZNIE plik percep_feed.jsonl (metadane,
pole t_frame = stempel sensora w sim). Pomiar dt klatek w oknie ≥30 s.

PRÓG FROZEN (PRE_PERC2 §2.2, jednostki JAWNIE per-klatkowe):
  PASS ⇔ dt_p50 ≤ 0.070 s/klatkę ∧ frakcja delt > 0.10 s/klatkę ≤ 5 %.

Tryby:
  --live    (domyślny): czyta NOWE wiersze od chwili startu przez --window s (wall);
  --posthoc: czyta CAŁY plik (analiza po próbie).
Wyjście: JSON na stdout i do --out; exit 0=PASS, 1=FAIL, 2=za mało danych (<50 delt).
"""
import argparse
import json
import os
import sys
import time

THR_DT_P50 = 0.070      # [s/klatkę] FROZEN
THR_FRAC_SLOW = 0.05    # frakcja delt > 0.10 s/klatkę, FROZEN
SLOW_DT = 0.10          # [s/klatkę]
MIN_DELT = 50


def parse_tframes(lines):
    ts = []
    for ln in lines:
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        t = r.get("t_frame")
        if t is not None:
            ts.append(t)
    return ts


def deltas(ts):
    out = []
    for i in range(1, len(ts)):
        dt = ts[i] - ts[i - 1]
        if 0 < dt <= 2.0:
            out.append(dt)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feed", required=True)
    ap.add_argument("--window", type=float, default=35.0, help="okno pomiaru [s wall] (live)")
    ap.add_argument("--posthoc", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--label", default="")
    a = ap.parse_args()

    if a.posthoc:
        ts = parse_tframes(open(a.feed))
    else:
        # live: od bieżącego końca pliku, przez window s
        t_end = time.monotonic() + a.window
        pos = os.path.getsize(a.feed) if os.path.exists(a.feed) else 0
        buf = []
        while time.monotonic() < t_end:
            if os.path.exists(a.feed):
                sz = os.path.getsize(a.feed)
                if sz > pos:
                    with open(a.feed) as f:
                        f.seek(pos)
                        chunk = f.read(sz - pos)
                        pos = sz
                    buf.extend(chunk.splitlines())
            time.sleep(0.5)
        ts = parse_tframes(buf)

    dts = deltas(ts)
    res = {"label": a.label, "feed": a.feed,
           "tryb": "posthoc" if a.posthoc else f"live window={a.window}s",
           "prog_frozen": {"dt_p50_max_s_na_klatke": THR_DT_P50,
                           "frac_delt_gt_0p10_max": THR_FRAC_SLOW},
           "n_delt": len(dts)}
    if len(dts) < MIN_DELT:
        res["werdykt"] = "ZA_MALO_DANYCH"
        print(json.dumps(res))
        if a.out:
            json.dump(res, open(a.out, "w"), indent=1)
        sys.exit(2)
    s = sorted(dts)
    p50 = s[len(s) // 2]
    frac = sum(1 for d in dts if d > SLOW_DT) / len(dts)
    res.update({"dt_p50_s_na_klatke": round(p50, 4),
                "dt_p90_s_na_klatke": round(s[int(0.9 * (len(s) - 1))], 4),
                "frac_delt_gt_0p10": round(frac, 4),
                "hz_p50": round(1.0 / p50, 2),
                "span_sim_s": round(ts[-1] - ts[0], 1)})
    ok = (p50 <= THR_DT_P50) and (frac <= THR_FRAC_SLOW)
    res["werdykt"] = "PASS" if ok else "FAIL"
    print(json.dumps(res))
    if a.out:
        json.dump(res, open(a.out, "w"), indent=1)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
