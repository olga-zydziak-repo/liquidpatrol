#!/usr/bin/env python3
"""results/NADIR/tools/nadir_s4_manifest.py — manifest scenariuszy S4 NADIR (PROMPT_NADIR_S4 §0.3: ruch intruza ciągły przez cały
epizod, parametry intruder_motion nazwane i stałe dla wszystkich epizodów).

Kanon results/BENCH/scenario_manifest.json ma trajektorie EP_DUR_S = 110 s (po końcu intruder_motion przestaje prowadzić intruza).
Epizod cięcia S4 trwa t_entry (≤ 25) + 30 + ≥ 110 s kontynuacji ⇒ do ~165 s sim. Ten skrypt generuje manifest tym samym
generatorem bench/scenarios.gen_episode (import, plik nietknięty) z EP_DUR_S_S4 = 200 s; zmiana wyłącznie długości:
  - odcinki o t0 < 110 s są bajtowo identyczne z kanonem (ten sam RNG, te same losowania) — asercja per epizod; odcinek
    przecinający 110 s w kanonie jest przycięty przez pętlę `while t < EP_DUR_S` tylko długością dur (losowanie to samo) — asercja;
  - orbit_dir losowany PO pętli odcinków ⇒ dłuższa pętla zmieniłaby go; przypięty z kanonu (asercja zgodności pozostałych pól);
  - komórki v = 0 (c00–c03): intruz stoi przez cały epizod (jeden odcinek 0–200 s).
Wyjście: results/NADIR/s4/scenario_manifest_s4.json (+ sha256 w nadir_s4_manifest.json).
"""
import hashlib
import json
import os
import sys

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, ROOT)
from bench import scenarios as S

EP_DUR_S_S4 = 200.0
KANON = os.path.join(ROOT, "results/BENCH/scenario_manifest.json")
OUT = os.path.join(ROOT, "results/NADIR/s4/scenario_manifest_s4.json")


def main():
    kan = json.load(open(KANON))
    assert kan["ep_dur_s"] == S.EP_DUR_S == 110.0
    S.EP_DUR_S = EP_DUR_S_S4                       # wyłącznie w tym procesie
    nowe = S.gen_manifest()
    S.EP_DUR_S = 110.0
    assert len(nowe["episodes"]) == len(kan["episodes"])
    for a, b in zip(kan["episodes"], nowe["episodes"]):
        assert a["scenario_id"] == b["scenario_id"] and a["episode_id"] == b["episode_id"]
        for k in ("cell", "cell_index", "seed", "block", "is_test", "start_pos", "z"):
            assert a[k] == b[k], (a["scenario_id"], k)
        sa, sb = a["segments"], b["segments"]
        for i, s in enumerate(sa):
            if s["t1"] < 110.0 - 1e-9:
                assert sb[i] == s, (a["scenario_id"], i)
            else:                                  # odcinek przycięty na 110 s w kanonie: start, kurs, prędkość identyczne
                assert all(sb[i][k] == s[k] for k in ("t0", "x0", "y0", "heading_deg", "v")), (a["scenario_id"], i)
                assert sb[i]["t1"] >= s["t1"] - 1e-9
        assert sb[-1]["t1"] >= EP_DUR_S_S4 - 1e-6
        b["orbit_dir_wygenerowany_200s"] = b["orbit_dir"]
        b["orbit_dir"] = a["orbit_dir"]           # przypięty z kanonu
        b["ep_dur_s"] = EP_DUR_S_S4
    nowe["ep_dur_s"] = EP_DUR_S_S4
    nowe["zrodlo"] = {"kanon": "results/BENCH/scenario_manifest.json",
                      "kanon_sha256": hashlib.sha256(open(KANON, "rb").read()).hexdigest(),
                      "generator": "bench/scenarios.gen_manifest z EP_DUR_S=200 (PROMPT_NADIR_S4 §0.3)",
                      "orbit_dir": "z kanonu", "prefiks_110s": "identyczny z kanonem (asercja)"}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(nowe, open(OUT, "w"), indent=1)
    sha = hashlib.sha256(open(OUT, "rb").read()).hexdigest()
    json.dump({"manifest": os.path.relpath(OUT, ROOT), "sha256": sha, "ep_dur_s": EP_DUR_S_S4,
               "orbit_dir_rozne_od_wygenerowanego": sum(e["orbit_dir"] != e["orbit_dir_wygenerowany_200s"] for e in nowe["episodes"])},
              open(os.path.join(os.path.dirname(OUT), "nadir_s4_manifest.json"), "w"), indent=1)
    print("OK", sha)


if __name__ == "__main__":
    main()
