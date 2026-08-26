#!/usr/bin/env python3
"""
tools/infra1_spike_stats.py — G1 (ANEKS_E1-2): statystyka głębokich stalli mostu gz↔px4 z dziesiątki E1d
(attempt-3, boot120-129) + przełożenie na okna roszczenia K1.

OFFLINE, read-only na rtf_stream.jsonl w oknie hoveru [hover_start_sim, hover_end_sim] (proxy segmentu lotu).
Per boot: liczba spajków (spójne runy rtf<0.5), głębokość (min rtf/run), położenie (sim startu), czas trwania.
Okno-hit: dla okna długości w [s] umieszczonego równomiernie w oknie hoveru — frakcja położeń startu, w których
[t,t+w] zawiera ≥1 próbkę deep-stall = miara sumy [d-w, d] (clip do okna) / (he-hs-w). w∈{3 (S), 8 (N)}.
"""
import os, json
import numpy as np

DEEP = 0.5
WINDOWS = {"S_3s": 3.0, "N_8s": 8.0}
BOOTS = list(range(120, 130))


def load_rtf(d):
    pts = []
    p = os.path.join(d, "rtf_stream.jsonl")
    if not os.path.exists(p):
        return pts
    for line in open(p, errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        s, rtf = r.get("sim"), r.get("rtf")
        if s is not None and rtf is not None:
            pts.append((float(s), float(rtf)))
    pts.sort()
    return pts


def hover_window(d):
    m = json.load(open(os.path.join(d, "manifest.json")))
    hw = m.get("hover_window_sim") or [None, None]
    return hw[0], hw[1]


def spikes_in(pts, lo, hi):
    """Spójne runy rtf<DEEP w [lo,hi]. Zwraca listę (sim_start, sim_end, min_rtf, dur)."""
    seg = [(s, r) for s, r in pts if lo <= s <= hi]
    runs = []
    i, n = 0, len(seg)
    while i < n:
        if seg[i][1] < DEEP:
            j = i
            mn = seg[i][1]
            while j < n and seg[j][1] < DEEP:
                mn = min(mn, seg[j][1])
                j += 1
            s0, s1 = seg[i][0], seg[j - 1][0]
            runs.append((round(s0, 3), round(s1, 3), round(mn, 4), round(s1 - s0, 3)))
            i = j
        else:
            i += 1
    return seg, runs


def window_hit_fraction(deep_positions, lo, hi, w):
    """Frakcja startów t∈[lo,hi-w], dla których [t,t+w] zawiera deep-sample = miara ∪[d-w,d] / (hi-w-lo)."""
    span = (hi - w) - lo
    if span <= 0 or not deep_positions:
        return 0.0
    # przedziały startów trafiających: t∈[d-w, d] (bo d∈[t,t+w] ⇔ t∈[d-w,d])
    ivs = sorted((max(lo, d - w), min(hi - w, d)) for d in deep_positions)
    ivs = [(a, b) for a, b in ivs if b >= a]
    if not ivs:
        return 0.0
    merged = [list(ivs[0])]
    for a, b in ivs[1:]:
        if a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    cov = sum(b - a for a, b in merged)
    return min(1.0, cov / span)


def main():
    rows = []
    for b in BOOTS:
        d = f"results/K1/E/p0_0/boot{b}"
        pts = load_rtf(d)
        lo, hi = hover_window(d)
        if lo is None or hi is None or not pts:
            rows.append({"boot": b, "err": "brak okna/rtf"})
            continue
        seg, runs = spikes_in(pts, lo, hi)
        deep_pos = [s for s, r in seg if r < DEEP]
        depths = [r[2] for r in runs]
        row = {
            "boot": b, "hover_lo": round(lo, 2), "hover_hi": round(hi, 2),
            "n_samples": len(seg), "n_deep_samples": len(deep_pos),
            "n_spikes": len(runs), "min_rtf": (min(depths) if depths else None),
            "spikes": runs,
            "hit_frac": {k: round(window_hit_fraction(deep_pos, lo, hi, w), 4) for k, w in WINDOWS.items()},
        }
        rows.append(row)

    ok = [r for r in rows if "err" not in r]
    agg = {
        "n_boots": len(ok),
        "spikes_per_boot_mean": round(float(np.mean([r["n_spikes"] for r in ok])), 2) if ok else None,
        "spikes_per_boot_range": [min(r["n_spikes"] for r in ok), max(r["n_spikes"] for r in ok)] if ok else None,
        "min_rtf_overall": min((r["min_rtf"] for r in ok if r["min_rtf"] is not None), default=None),
        "hit_frac_mean": {k: round(float(np.mean([r["hit_frac"][k] for r in ok])), 4) for k in WINDOWS} if ok else None,
        "hit_frac_max": {k: round(float(np.max([r["hit_frac"][k] for r in ok])), 4) for k in WINDOWS} if ok else None,
    }
    out = {"spec": "G1 ANEKS_E1-2 — spajki mostu E1d attempt-3 (boot120-129), okno hoveru",
           "deep_threshold_rtf": DEEP, "windows_s": WINDOWS, "per_boot": rows, "aggregate": agg}
    json.dump(out, open("results/K1/INFRA1/G1_spike_stats.json", "w"), indent=2)

    print("=== G1 spajki per boot (okno hoveru) ===")
    print("boot | n_spike | min_rtf | hit%_S(3s) | hit%_N(8s) | pozycje spajków (sim:min_rtf)")
    for r in ok:
        pos = " ".join(f"{s[0]}:{s[2]}" for s in r["spikes"][:6])
        print(f"{r['boot']} | {r['n_spikes']:^7} | {r['min_rtf']} | "
              f"{100*r['hit_frac']['S_3s']:.1f}% | {100*r['hit_frac']['N_8s']:.1f}% | {pos}")
    print(f"\nAGG: spikes/boot={agg['spikes_per_boot_mean']} (range {agg['spikes_per_boot_range']}), "
          f"min_rtf={agg['min_rtf_overall']}")
    print(f"hit_frac MEAN: S(3s)={100*agg['hit_frac_mean']['S_3s']:.1f}%  N(8s)={100*agg['hit_frac_mean']['N_8s']:.1f}%")
    print(f"hit_frac MAX : S(3s)={100*agg['hit_frac_max']['S_3s']:.1f}%  N(8s)={100*agg['hit_frac_max']['N_8s']:.1f}%")
    print("JSON → results/K1/INFRA1/G1_spike_stats.json")


if __name__ == "__main__":
    main()
