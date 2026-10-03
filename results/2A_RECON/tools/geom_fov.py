#!/usr/bin/env python3
"""results/2A_RECON/tools/geom_fov.py — R5 recon 2A: geometria kadru z ISTNIEJĄCYCH trace'ów (zero bootów).

Frakcja ticków z intruzem w kadrze kamery pokładowej dla siatki założeń:
  FOV poziomy {60°, 90°, 110°} × montaż {PRZOD: sztywny przód przy yaw komendowanym ku trackowi
  (rekonstrukcja atan2(trk−own) — DOKŁADNIE wzór net_controller.py:115, bez dynamiki yaw = optymistycznie),
  FOLLOW: idealny yaw-follow (az_err=0, górna granica — limituje tylko elewacja)}.
FOV pionowy z aspektu 640×480: vFOV = 2·atan(tan(hFOV/2)·0.75). Kamera POZIOMA (pitch=0) — pitch drona
NIELOGOWANY (trace: tylko pozycja; lekcja r02 §3f: przechył kadruje — to mierzy dopiero etap A).

Wejście: results/LIQ/camp/r{1..12}_{ncp,gru}/{demo.jsonl,gt_intruder.jsonl}.
GT intruza: kolumna "ned" (APPLIED, już NED przez drv2ned w intruder_motion), interpolacja liniowa w t_sim.
Fazy: liczone OSOBNO dla phase∈{approach,orbit} (hold/reset poza statystyką).
Wyjście: geom_fov.json (pełne per scenariusz per ramię) + markdown na stdout.
"""
import glob
import json
import math
import os
import sys

FOVS_DEG = [60.0, 90.0, 110.0]
ASPECT = 480.0 / 640.0
ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..")


def vfov(hfov_rad):
    return 2.0 * math.atan(math.tan(hfov_rad / 2.0) * ASPECT)


def wrap(a):
    while a > math.pi:
        a -= 2 * math.pi
    while a < -math.pi:
        a += 2 * math.pi
    return a


def load_jsonl(path):
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


def interp(ts, ps, t):
    """Interpolacja liniowa pozycji ps (lista [x,y,z]) po czasach ts (rosnące) w t. None poza zakresem od dołu."""
    if not ts or t < ts[0]:
        return None
    if t >= ts[-1]:
        return ps[-1]
    import bisect
    i = bisect.bisect_right(ts, t)
    t0, t1 = ts[i - 1], ts[i]
    a = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
    return [ps[i - 1][k] + a * (ps[i][k] - ps[i - 1][k]) for k in range(3)]


def analyze_boot(bootdir):
    demo = load_jsonl(os.path.join(bootdir, "demo.jsonl"))
    gti = load_jsonl(os.path.join(bootdir, "gt_intruder.jsonl"))
    gt_by_ep = {}
    for r in gti:
        gt_by_ep.setdefault(r["episode_id"], ([], []))
        gt_by_ep[r["episode_id"]][0].append(r["t_sim"])
        gt_by_ep[r["episode_id"]][1].append(r["ned"])
    out = {}
    for row in demo:
        ph = row["phase"]
        if ph not in ("approach", "orbit"):
            continue
        ep = row["episode_id"]
        if ep not in gt_by_ep:
            continue
        ts, ps = gt_by_ep[ep]
        gt = interp(ts, ps, row["t_sim"])
        if gt is None:
            continue
        own = row["own_pos_ned"]
        trk = row["trk_pos_ned"]
        dx, dy, dz = gt[0] - own[0], gt[1] - own[1], gt[2] - own[2]
        dh = math.hypot(dx, dy)
        az_los = math.atan2(dy, dx)
        el_los = math.atan2(-dz, dh)                     # NED: -dz = w górę
        yaw_cmd = math.atan2(trk[1] - own[1], trk[0] - own[0])   # net_controller.py:115
        az_err = wrap(az_los - yaw_cmd)
        key = (row["scenario_id"], ph)
        rec = out.setdefault(key, {"n": 0, "in": {}, "abs_el_sum": 0.0, "abs_az_sum": 0.0, "d_sum": 0.0})
        rec["n"] += 1
        rec["abs_el_sum"] += abs(el_los)
        rec["abs_az_sum"] += abs(az_err)
        rec["d_sum"] += math.hypot(dh, dz)
        for fd in FOVS_DEG:
            h2 = math.radians(fd) / 2.0
            v2 = vfov(math.radians(fd)) / 2.0
            rec["in"].setdefault(fd, {"przod": 0, "follow": 0})
            if abs(az_err) <= h2 and abs(el_los) <= v2:
                rec["in"][fd]["przod"] += 1
            if abs(el_los) <= v2:
                rec["in"][fd]["follow"] += 1
    return out


def main():
    res = {}          # arm -> scenario -> phase -> stats
    for arm in ("ncp", "gru"):
        boots = sorted(glob.glob(os.path.join(ROOT, "results", "LIQ", "camp", f"r*_{arm}")))
        boots = [b for b in boots if os.path.isdir(b) and not b.endswith("r")]
        agg = {}
        for b in boots:
            for (scen, ph), rec in analyze_boot(b).items():
                a = agg.setdefault(scen, {}).setdefault(ph, {"n": 0, "abs_el_sum": 0.0, "abs_az_sum": 0.0,
                                                             "d_sum": 0.0, "in": {fd: {"przod": 0, "follow": 0} for fd in FOVS_DEG}})
                a["n"] += rec["n"]
                a["abs_el_sum"] += rec["abs_el_sum"]
                a["abs_az_sum"] += rec["abs_az_sum"]
                a["d_sum"] += rec["d_sum"]
                for fd in FOVS_DEG:
                    a["in"][fd]["przod"] += rec["in"][fd]["przod"]
                    a["in"][fd]["follow"] += rec["in"][fd]["follow"]
        res[arm] = agg

    def frac(a, fd, m):
        return a["in"][fd][m] / a["n"] if a["n"] else float("nan")

    # markdown: tabela per scenariusz (NCP), fazy osobno
    print(f"vFOV(60/90/110) = {math.degrees(vfov(math.radians(60))):.1f} / "
          f"{math.degrees(vfov(math.radians(90))):.1f} / {math.degrees(vfov(math.radians(110))):.1f} deg\n")
    for arm in ("ncp", "gru"):
        print(f"\n## ramię {arm.upper()} — frakcja ticków w kadrze (PRZOD = yaw-komenda ku trackowi; FOLLOW = idealny yaw-follow)")
        print("| scenariusz | faza | n | f60_przod | f90_przod | f110_przod | f60_follow | f90_follow | f110_follow | med|az_err| [deg] | med|el| [deg] | d_sr [m] |")
        print("|---|---|---|---|---|---|---|---|---|---|---|---|")
        for scen in sorted(res[arm]):
            for ph in ("approach", "orbit"):
                a = res[arm][scen].get(ph)
                if not a:
                    continue
                print(f"| {scen} | {ph} | {a['n']} | "
                      + " | ".join(f"{frac(a, fd, 'przod'):.3f}" for fd in FOVS_DEG) + " | "
                      + " | ".join(f"{frac(a, fd, 'follow'):.3f}" for fd in FOVS_DEG)
                      + f" | {math.degrees(a['abs_az_sum'] / a['n']):.1f} | {math.degrees(a['abs_el_sum'] / a['n']):.1f}"
                      + f" | {a['d_sum'] / a['n']:.1f} |")
        # agregat globalny per faza
        for ph in ("approach", "orbit"):
            N = sum(res[arm][s][ph]["n"] for s in res[arm] if ph in res[arm][s])
            if not N:
                continue
            tot = {fd: {m: sum(res[arm][s][ph]["in"][fd][m] for s in res[arm] if ph in res[arm][s])
                        for m in ("przod", "follow")} for fd in FOVS_DEG}
            print(f"**AGREGAT {arm.upper()}/{ph}** (n={N}): "
                  + " · ".join(f"f{int(fd)} przod {tot[fd]['przod']/N:.3f} / follow {tot[fd]['follow']/N:.3f}"
                               for fd in FOVS_DEG))

    outp = os.path.join(os.path.dirname(__file__), "..", "geom_fov.json")
    with open(outp, "w") as f:
        json.dump({arm: {s: {ph: {"n": a["n"],
                                  "mean_abs_az_err_deg": math.degrees(a["abs_az_sum"] / a["n"]),
                                  "mean_abs_el_deg": math.degrees(a["abs_el_sum"] / a["n"]),
                                  "mean_d_m": a["d_sum"] / a["n"],
                                  "frac": {str(int(fd)): {m: frac(a, fd, m) for m in ("przod", "follow")}
                                           for fd in FOVS_DEG}}
                             for ph, a in phs.items()}
                         for s, phs in res[arm].items()}
                  for arm in res}, f, indent=1)
    print(f"\n[geom_fov] JSON -> {outp}", file=sys.stderr)


if __name__ == "__main__":
    main()
