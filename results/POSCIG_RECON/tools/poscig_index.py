#!/usr/bin/env python3
"""results/POSCIG_RECON/tools/poscig_index.py — indeks epizodów kampanii FANTOM S2 i AKW S3.

Skanuje akw_summary.json per boot-dir (r*_V2 / r*_B / retry r*_V2r|Br), buduje mapę
scenario_id×ramię×kampania → (dir, werdykt, fail_reasons, t_first_fresh, t_entry, d_min, valid).
Przy duplikatach (retry) wygrywa wpis valid_final=True z najpóźniejszej rundy (jak parowanie kampanii).
Wynik: results/POSCIG_RECON/index_episodes.json. Zero edycji istniejących plików.
"""
import glob
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT = os.path.join(ROOT, "results", "POSCIG_RECON", "index_episodes.json")

CAMPS = {
    "FANTOM_S2": os.path.join(ROOT, "results", "FANTOM", "camp"),
    "AKW_S3": os.path.join(ROOT, "results", "AKW", "camp"),
}


def main():
    idx = {}
    for camp, base in CAMPS.items():
        for d in sorted(glob.glob(os.path.join(base, "r*_*"))):
            if not os.path.isdir(d):
                continue
            m = re.match(r"r(\d+)_(V2|B)(r?)$", os.path.basename(d))
            if not m:
                continue
            rnd, arm, retry = int(m.group(1)), m.group(2), bool(m.group(3))
            summ = os.path.join(d, "akw_summary.json")
            if not os.path.exists(summ):
                continue
            s = json.load(open(summ))
            for ep in s.get("episodes", []):
                key = f"{camp}:{arm}:{ep['scenario_id']}"
                rec = {
                    "camp": camp, "arm": arm, "round": rnd, "retry": retry,
                    "dir": os.path.relpath(d, ROOT),
                    "scenario_id": ep["scenario_id"], "episode_id": ep["episode_id"],
                    "valid_final": ep.get("valid_final"), "success_D6": ep.get("success_D6"),
                    "d_min_m": ep.get("d_min_m"),
                    "fail_reasons": (ep.get("akw") or {}).get("fail_reasons"),
                    "t_entry_s": (ep.get("akw") or {}).get("t_entry_s"),
                    "t_first_fresh_rel": (ep.get("akw") or {}).get("t_first_track_rel"),
                    "t_first_fresh": (ep.get("akw") or {}).get("t_first_fresh_rel"),
                    "frac_hold": (ep.get("akw") or {}).get("frac_hold"),
                    "controller": s.get("controller"),
                }
                old = idx.get(key)
                take = old is None
                if old is not None:
                    # preferuj valid_final; przy obu valid — późniejsza runda/retry
                    if rec["valid_final"] and not old["valid_final"]:
                        take = True
                    elif rec["valid_final"] == old["valid_final"] and (rnd, retry) >= (old["round"], old["retry"]):
                        take = True
                if take:
                    idx[key] = rec
    json.dump(idx, open(OUT, "w"), indent=1)
    # skrót na stdout: komórki v=1.0 (c08-c11) + c05 w obu kampaniach
    for key in sorted(idx):
        r = idx[key]
        cell = int(r["scenario_id"][1:3])
        if cell >= 8 or r["scenario_id"].startswith("c05") or r["scenario_id"].startswith("c10"):
            print(f"{key:28s} dir={r['dir']:34s} valid={r['valid_final']} D6={r['success_D6']} "
                  f"fail={r['fail_reasons']} t_acq={r['t_first_fresh']} t_entry={r['t_entry_s']} dmin={r['d_min_m']}")


if __name__ == "__main__":
    main()
