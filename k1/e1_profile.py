#!/usr/bin/env python3
"""ANEKS_K1-12 E1: nałożenie profili z(t)/r(t) obu ważnych bootów (S boot3, N boot4) od armed do inject.
GT (gz ENU) → NED: north=y, east=x, up=z. r_horiz=hypot(north,east). Zero lotów — tylko odczyt trace."""
import json, math, sys

BOOTS = {
    "S": "results/K1/S/p0_2/boot3/trace.jsonl",
    "N": "results/K1/N/p0_2/boot4/trace.jsonl",
}
WP0 = (14.071424945612295, 14.071424945612295)   # narożnik-0 (NED north,east)


def load(path):
    gts, evs = [], {}
    for ln in open(path):
        try:
            r = json.loads(ln)
        except Exception:
            continue
        if r.get("t") == "gt":
            # ENU→NED
            north, east, up = r["y"], r["x"], r["z"]
            gts.append({"mono": r["mono"], "sim": r["sim"], "north": north, "east": east,
                        "up": up, "r": math.hypot(north, east)})
        elif r.get("t") == "event":
            evs.setdefault(r["ev"], r["mono"])
    return gts, evs


def nearest(gts, mono, key):
    return min(gts, key=lambda g: abs(g[key] - mono))


def main():
    data = {}
    for arm, p in BOOTS.items():
        gts, evs = load(p)
        data[arm] = (gts, evs)

    # profile od offboard do inject, oś: sim-time i wall-time od offboard
    print("=== E1: profile od OFFBOARD do INJECT (GT, NED) ===\n")
    rows = {}
    for arm, (gts, evs) in data.items():
        t_off_mono = evs["offboard"]
        t_inj_mono = evs["denial_on"]
        g_off = nearest(gts, t_off_mono, "mono")
        g_inj = nearest(gts, t_inj_mono, "mono")
        seg = [g for g in gts if t_off_mono - 0.2 <= g["mono"] <= t_inj_mono + 0.2]
        # dystans poziomy przebyty (całka |Δpos|)
        dist_trav = 0.0
        for a, b in zip(seg, seg[1:]):
            dist_trav += math.hypot(b["north"] - a["north"], b["east"] - a["east"])
        # moment przejścia narożnika-0: min odległości do WP0
        g_corner = min(seg, key=lambda g: math.hypot(g["north"] - WP0[0], g["east"] - WP0[1]))
        d_corner = math.hypot(g_corner["north"] - WP0[0], g_corner["east"] - WP0[1])
        rows[arm] = dict(
            t_off=t_off_mono, t_inj=t_inj_mono,
            wall_off2inj=t_inj_mono - t_off_mono,
            sim_off=g_off["sim"], sim_inj=g_inj["sim"], sim_off2inj=g_inj["sim"] - g_off["sim"],
            z_off=g_off["up"], z_inj=g_inj["up"], r_inj=g_inj["r"],
            corner_sim=g_corner["sim"], corner_mono=g_corner["mono"], corner_d=d_corner,
            corner_z=g_corner["up"], corner_r=g_corner["r"],
            dist_trav=dist_trav, seg=seg,
        )
        print(f"[{arm}] offboard@z={g_off['up']:.2f}m  →  inject@z={g_inj['up']:.2f}m r={g_inj['r']:.2f}m")
        print(f"     wall off→inj = {rows[arm]['wall_off2inj']:.2f}s | sim off→inj = {rows[arm]['sim_off2inj']:.2f}s "
              f"| RTF = {rows[arm]['sim_off2inj']/rows[arm]['wall_off2inj']:.3f}")
        print(f"     narożnik-0 najbliżej: d={d_corner:.2f}m @sim={g_corner['sim']:.2f} z={g_corner['up']:.2f} r={g_corner['r']:.2f}")
        print(f"     dystans poziomy przebyty off→inj = {dist_trav:.2f}m\n")

    # divergencja w czasie: align obu od offboard po SIM-time, próbkuj wspólną siatkę
    print("=== divergencja z(t) i r(t) vs sim-time od offboard (align na offboard) ===")
    print(f"{'t_sim':>6} | {'z_S':>6} {'z_N':>6} {'Δz':>6} | {'r_S':>6} {'r_N':>6} {'Δr':>6}")
    def resample(arm, trel):
        gts, evs = data[arm]
        sim0 = rows[arm]["sim_off"]
        target = sim0 + trel
        g = min(rows[arm]["seg"], key=lambda x: abs(x["sim"] - target))
        return g
    tmax = min(rows["S"]["sim_off2inj"], rows["N"]["sim_off2inj"])
    t = 0.0
    while t <= tmax + 1e-6:
        gS, gN = resample("S", t), resample("N", t)
        print(f"{t:6.1f} | {gS['up']:6.2f} {gN['up']:6.2f} {gS['up']-gN['up']:6.2f} | "
              f"{gS['r']:6.2f} {gN['r']:6.2f} {gS['r']-gN['r']:6.2f}")
        t += 0.5

    # zapis CSV do wykresu
    with open("results/K1/e1_profiles.csv", "w") as f:
        f.write("arm,t_sim_from_off,mono,z_up,r_horiz,north,east\n")
        for arm in ("S", "N"):
            sim0 = rows[arm]["sim_off"]
            for g in rows[arm]["seg"]:
                f.write(f"{arm},{g['sim']-sim0:.4f},{g['mono']:.4f},{g['up']:.4f},{g['r']:.4f},{g['north']:.4f},{g['east']:.4f}\n")
    print("\nCSV → results/K1/e1_profiles.csv")


if __name__ == "__main__":
    main()
