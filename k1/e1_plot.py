#!/usr/bin/env python3
"""ANEKS_K1-12 E1: wykres nałożenia profili z(t)/r(t) + tor poziomy, S boot3 vs N boot4, armed→inject."""
import json, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BOOTS = {"S": "results/K1/S/p0_2/boot3/trace.jsonl", "N": "results/K1/N/p0_2/boot4/trace.jsonl"}
WP = [(14.071, 14.071), (14.071, -14.071)]   # narożnik-0, narożnik-1 (NED north,east)
COL = {"S": "#1f77b4", "N": "#d62728"}


def load(path):
    gts, evs = [], {}
    for ln in open(path):
        try:
            r = json.loads(ln)
        except Exception:
            continue
        if r.get("t") == "gt":
            gts.append({"mono": r["mono"], "sim": r["sim"], "north": r["y"], "east": r["x"],
                        "up": r["z"], "r": math.hypot(r["y"], r["x"])})
        elif r.get("t") == "event":
            evs.setdefault(r["ev"], r["mono"])
    return gts, evs


fig, ax = plt.subplots(1, 3, figsize=(16, 5))
for arm, p in BOOTS.items():
    gts, evs = load(p)
    t0 = evs["armed"]
    t_off = evs["offboard"] - t0
    t_inj = evs["denial_on"] - t0
    seg = [g for g in gts if t0 - 0.1 <= g["mono"] <= evs["denial_on"] + 0.1]
    t = [g["mono"] - t0 for g in seg]
    z = [g["up"] for g in seg]
    r = [g["r"] for g in seg]
    north = [g["north"] for g in seg]
    east = [g["east"] for g in seg]
    lbl = f"{arm} ({'osłona' if arm=='S' else 'natywny'})"
    ax[0].plot(t, z, color=COL[arm], label=lbl)
    ax[1].plot(t, r, color=COL[arm], label=lbl)
    ax[2].plot(east, north, color=COL[arm], label=lbl)
    for a in (ax[0], ax[1]):
        a.axvline(t_off, color=COL[arm], ls=":", alpha=0.5)
        a.axvline(t_inj, color=COL[arm], ls="--", alpha=0.7)
    ax[2].scatter([east[-1]], [north[-1]], color=COL[arm], marker="X", s=90, zorder=5)

ax[0].set_title("z(t) — wysokość [m] (armed→inject)\n: offboard  -- inject")
ax[0].set_xlabel("t od armed [s]"); ax[0].set_ylabel("z_up [m]"); ax[0].legend(); ax[0].grid(alpha=0.3)
ax[1].set_title("r(t) — promień poziomy [m]\n: offboard  -- inject")
ax[1].set_xlabel("t od armed [s]"); ax[1].set_ylabel("r=hypot(N,E) [m]"); ax[1].legend(); ax[1].grid(alpha=0.3)
ax[2].set_title("tor poziomy (E-N), X=inject")
ax[2].set_xlabel("east [m]"); ax[2].set_ylabel("north [m]")
ax[2].scatter([w[1] for w in WP], [w[0] for w in WP], marker="s", color="k", s=60, label="wp0,wp1")
ax[2].plot([WP[0][1], WP[1][1]], [WP[0][0], WP[1][0]], "k--", alpha=0.4, label="leg1 nominalna")
ax[2].legend(); ax[2].grid(alpha=0.3); ax[2].set_aspect("equal", "box")

fig.suptitle("ANEKS_K1-12 E1 — rozjazd ramion S↔N @0.2 zaczyna się w TAKEOFFIE (przed offboard/narożnikiem)",
             fontsize=12, weight="bold")
fig.tight_layout()
fig.savefig("results/K1/e1_divergence.png", dpi=110)
print("PNG → results/K1/e1_divergence.png")
