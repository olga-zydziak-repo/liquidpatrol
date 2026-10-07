#!/usr/bin/env python3
"""results/DET/tools/detS4_pairs.py — NARZĘDZIE PAROWANIA kampanii C (ANEKS_DET-3 §3.7/§3.9).

Czyta detS4_summary.json wszystkich bootów results/DET/camp/r*_{B,V2}[r]/ i buduje:
  * tabelę 48 par per scenariusz: wynik ramienia = PIERWSZA ważna próba (boot bazowy,
    potem powtórka 'r' — wzór kolejki LIQ); para WSPÓLNIE WAŻNA ⇔ obie strony ważne
    (V2′ ∧ żywość feedu dla V2); n_common < 40 ⇒ STOP (flaga);
  * Δ = pass(B) − pass(V2) na parach wspólnie ważnych (werdykt D6 sędziego frozen);
  * dekompozycje OPISOWE (ANEKS_DET-3 §2/§3.7): Δ na 46 parach sceno-świeżych
    (c08_s03, c11_s01 w TRAIN detektora — wyłączone), Δ per komórka z etykietą
    TRAIN/VAL/TEST (split FROZEN PRE_DET §3: TEST c06+c09, VAL c02+c04, TRAIN reszta),
    udział ogona d<6 m w porażkach V2 (err_d_lt6 epizodów V2-FAIL);
  * REFUSE per gałąź per ramię (wynik epizodu, osobny licznik fałszywych odmów pod
    szumem percepcji); sygnały STOP.
Wyjście: results/DET/camp/detS4_pairs.json + tabela na stdout.
Użycie: detS4_pairs.py [--campdir results/DET/camp]
"""
import argparse
import glob
import json
import os
import re

ROOT = "/home/olga/projects/liquidpatrol"
SCENE_IN_TRAIN = {"c08_s03", "c11_s01"}           # prerejestracja ANEKS_DET-3 §2
CELL_SPLIT = {"c02": "VAL", "c04": "VAL", "c06": "TEST", "c09": "TEST"}


def cell_of(sid):
    return sid.split("_")[0]


def split_of(sid):
    return CELL_SPLIT.get(cell_of(sid), "TRAIN")


def pooled(stats_list, key):
    """Zbiera (n,p50,p95,max) per epizod — bez surowych próbek agreguje zachowawczo:
    mediana p50/p95 per epizod + max globalny (jawnie: agregat per-epizod, nie pooled próbek)."""
    xs = [s[key] for s in stats_list if s and s.get(key) and s[key].get("n")]
    if not xs:
        return None
    p50s = sorted(x["p50"] for x in xs)
    p95s = sorted(x["p95"] for x in xs)
    return {"n_eps": len(xs), "n_samples": sum(x["n"] for x in xs),
            "p50_med": p50s[len(p50s) // 2], "p95_med": p95s[len(p95s) // 2],
            "p95_max": max(x["p95"] for x in xs), "max": max(x["max"] for x in xs)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--campdir", default=os.path.join(ROOT, "results/DET/camp"))
    a = ap.parse_args()

    boots = []
    for p in sorted(glob.glob(os.path.join(a.campdir, "r*_*", "detS4_summary.json"))):
        name = os.path.basename(os.path.dirname(p))
        m = re.match(r"r(\d+)_(B|V2)(r?)$", name)
        if not m:
            continue
        s = json.load(open(p))
        boots.append({"name": name, "round": int(m.group(1)), "arm": m.group(2),
                      "attempt": 2 if m.group(3) else 1, "sum": s})
    boots.sort(key=lambda b: (b["round"], b["arm"], b["attempt"]))

    # wynik ramienia per scenariusz = pierwsza ważna próba
    res = {}                                       # sid -> {"B": ep|None, "V2": ep|None}
    refuse = {"B": {}, "V2": {}}
    stop_flags = []
    for b in boots:
        s = b["sum"]
        if s.get("stop_now"):
            stop_flags.append(b["name"])
        for br, n in s["s_bezp"]["refuse_branches"].items():
            refuse[b["arm"]][br] = refuse[b["arm"]].get(br, 0) + n
        for ep in s["episodes"]:
            sid = ep["scenario_id"]
            slot = res.setdefault(sid, {"B": None, "V2": None, "attempts": {"B": [], "V2": []}})
            slot["attempts"][b["arm"]].append({"boot": b["name"], "valid": ep["valid_final"],
                                               "D6": ep["success_D6"]})
            if ep["valid_final"] and slot[b["arm"]] is None:
                ep = dict(ep); ep["boot"] = b["name"]
                slot[b["arm"]] = ep

    sids = sorted(res)
    pairs = []
    for sid in sids:
        rB, rV = res[sid]["B"], res[sid]["V2"]
        common = rB is not None and rV is not None
        pairs.append({"scenario_id": sid, "cell": cell_of(sid), "split": split_of(sid),
                      "scene_fresh": sid not in SCENE_IN_TRAIN,
                      "common_valid": common,
                      "B_valid": rB is not None, "V2_valid": rV is not None,
                      "B_D6": (rB or {}).get("success_D6"), "V2_D6": (rV or {}).get("success_D6"),
                      "B_boot": (rB or {}).get("boot"), "V2_boot": (rV or {}).get("boot"),
                      "B_dmin": (rB or {}).get("d_min_m"), "V2_dmin": (rV or {}).get("d_min_m"),
                      "B_refuse": (rB or {}).get("refuse_count"), "V2_refuse": (rV or {}).get("refuse_count"),
                      "V2_err_fresh": ((rV or {}).get("telemetry") or {}).get("err_fresh"),
                      "V2_err_lt6": ((rV or {}).get("telemetry") or {}).get("err_d_lt6")})

    common = [p for p in pairs if p["common_valid"]]
    passB = sum(1 for p in common if p["B_D6"])
    passV = sum(1 for p in common if p["V2_D6"])
    delta = passB - passV

    def sub(pp):
        c = [p for p in pp if p["common_valid"]]
        return {"n_pairs": len(pp), "n_common": len(c),
                "pass_B": sum(1 for p in c if p["B_D6"]),
                "pass_V2": sum(1 for p in c if p["V2_D6"]),
                "delta": sum(1 for p in c if p["B_D6"]) - sum(1 for p in c if p["V2_D6"])}

    fresh46 = [p for p in pairs if p["scene_fresh"]]
    per_cell = {}
    for p in pairs:
        per_cell.setdefault(f'{p["cell"]} ({p["split"]})', []).append(p)
    v2_fail = [p for p in common if not p["V2_D6"]]
    tail = [{"scenario_id": p["scenario_id"], "err_d_lt6": p["V2_err_lt6"],
             "err_fresh": p["V2_err_fresh"], "d_min": p["V2_dmin"]} for p in v2_fail]

    # telemetria zbiorcza per ramię (z pierwszych ważnych prób)
    telem = {}
    for armk in ("B", "V2"):
        eps = [res[sid][armk] for sid in sids if res[sid][armk]]
        ts = [e["telemetry"] for e in eps]
        telem[armk] = {
            "err_fresh": pooled(ts, "err_fresh"),
            "err_consumed_demo": pooled(ts, "err_consumed_demo"),
            "err_d_lt6": pooled(ts, "err_d_lt6"),
            "z_max_alt_max": max((t["z_max_alt"] for t in ts if t["z_max_alt"] is not None), default=None),
            "r_max_max": max((t["r_max"] for t in ts if t["r_max"] is not None), default=None),
            "d_min_min": min((e["d_min_m"] for e in eps if e.get("d_min_m") is not None), default=None),
            "feed_expire_total": sum((t.get("feed_v2") or {}).get("n_feed_expire", 0) for t in ts),
            "refuse_total": sum(e.get("refuse_count", 0) for e in eps),
        }

    out = {
        "n_pairs_grid": len(pairs), "n_common": len(common),
        "stop_n_common_lt40": len(common) < 40 and len(pairs) >= 48,
        "pass_B": passB, "pass_V2": passV, "delta": delta,
        "decomp_46_scene_fresh": sub(fresh46),
        "decomp_2_scene_in_train": sub([p for p in pairs if not p["scene_fresh"]]),
        "decomp_per_cell": {k: sub(v) for k, v in sorted(per_cell.items())},
        "v2_failures_tail_lt6": tail,
        "refuse_branches": refuse,
        "stop_flags": stop_flags,
        "telemetry_per_arm": telem,
        "pairs": pairs,
        "boots_seen": [b["name"] for b in boots],
    }
    os.makedirs(a.campdir, exist_ok=True)
    op = os.path.join(a.campdir, "detS4_pairs.json")
    json.dump(out, open(op, "w"), indent=1)

    print(f"pary: {len(pairs)}/48 w siatce · wspólnie ważne n_common={len(common)}"
          f"{' (STOP n_common<40!)' if out['stop_n_common_lt40'] else ''}")
    print(f"pass(B)={passB} pass(V2)={passV} Δ={delta}")
    print(f"46 sceno-świeże: {out['decomp_46_scene_fresh']}")
    print("scenario_id   split  common  B_D6   V2_D6  d_minB  d_minV2")
    for p in pairs:
        print(f'{p["scenario_id"]:<13} {p["split"]:<6} {str(p["common_valid"]):<7} '
              f'{str(p["B_D6"]):<6} {str(p["V2_D6"]):<6} {str(p["B_dmin"]):<7} {str(p["V2_dmin"])}')
    print(f"→ {op}")


if __name__ == "__main__":
    main()
