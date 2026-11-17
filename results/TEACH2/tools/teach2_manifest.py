#!/usr/bin/env python3
"""results/TEACH2/tools/teach2_manifest.py — manifest wahadła lotu długiego TEACH-II (PRE_TEACH2 §4, PROMPT_TEACH2_S1 §1; 0 bootów).

Wejście: manifest NAD3 v2 (results/NAD3/s1/scenario_manifest_nad3_v2.json, READ-ONLY). Generator: funkcja `wahadlo` z
results/NAD2/tools/nad2_s4_manifest.py (import, plik nietknięty) — odcinki [0, 200] s w przód, potem ten sam tor wstecz, na przemian;
długość ustawiana w tym procesie (moduł: EP_DUR_S_L) na 1000 s ⇒ pięć nóg po 200 s. Każdy z 120 epizodów przez `wahadlo` (pola
epizodu bez zmian, w tym episode_id ⇒ niezmiennik pozycja = numer zostaje); nagłówek manifestu jak v2, ep_dur_s 1000, pole „zrodlo”.
Sprawdziany dla c10_s01 (PROMPT §1): pierwsze 200 s równe v2 odcinek w odcinek; tor ciągły przez 1000 s (position_at co 0.1 s, krok
≤ 0.1 m); promień intruza ≤ 11.0 m — progi zastąpione przez ANEKS_TEACH2-1 §3: krok ≤ v·0.1 s + 0.001 m, promień ≤ 11.001 m;
--sprawdz: sprawdziany na istniejącym pliku bez regeneracji (ANEKS_TEACH2-1 §4.3). Wyjście: results/TEACH2/scenario_manifest_teach2L.json + teach2_manifest.json (sha256, sprawdziany).
"""
import copy
import hashlib
import json
import math
import os
import sys

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
sys.path[:0] = [ROOT, os.path.join(ROOT, "results/NAD2/tools")]
from bench import scenarios as S                         # noqa: E402
import nad2_s4_manifest as W                             # noqa: E402

V2 = os.path.join(ROOT, "results/NAD3/s1/scenario_manifest_nad3_v2.json")
OUT = os.path.join(ROOT, "results/TEACH2/scenario_manifest_teach2L.json")
DLUGOSC = 1000.0
SCEN = "c10_s01"
TOL_KROK, R_MAX = 0.001, 11.001                          # ANEKS_TEACH2-1 §3 (zastępuje progi 0.1 m / 11.0 m z PROMPT_TEACH2_S1 §1)


def sprawdz_istniejacy():
    """ANEKS_TEACH2-1 §4.3: sprawdziany na istniejącym manifeście (bez regeneracji); suma pliku = zapisana."""
    info = json.load(open(os.path.join(ROOT, "results/TEACH2/teach2_manifest.json")))
    sha = hashlib.sha256(open(OUT, "rb").read()).hexdigest()
    v2e = next(e for e in json.load(open(V2))["episodes"] if e["scenario_id"] == SCEN)
    e = next(e for e in json.load(open(OUT))["episodes"] if e["scenario_id"] == SCEN)
    spr = sprawdziany(v2e, e)
    return {"sha256": sha, "sha_zgodna_z_zapisana": sha == info["sha256"], "sprawdziany_c10_s01": spr, "ok": spr["ok"] and sha == info["sha256"]}


def sprawdziany(v2_ep, ep):
    pierwsze = [sg for sg in ep["segments"] if sg["t0"] < 200.0]
    oryg = [sg for sg in v2_ep["segments"] if sg["t0"] < 200.0]
    rowne = len(pierwsze) == len(oryg) and all(
        all(a[k] == b[k] for k in ("x0", "y0", "heading_deg", "v", "t0")) and a["t1"] == min(b["t1"], 200.0) for a, b in zip(pierwsze, oryg))
    t = np.arange(0.0, DLUGOSC + 1e-9, 0.1)
    p = np.array([S.position_at(ep, x)[:2] for x in t])
    krok = float(np.max(np.hypot(*np.diff(p, axis=0).T)))
    r = float(np.max(np.hypot(p[:, 0], p[:, 1])))
    p0 = np.array([S.position_at(v2_ep, x)[:2] for x in t[t <= 200.0]])
    d200 = float(np.max(np.hypot(*(p[: len(p0)] - p0).T)))
    v = max(sg["v"] for sg in ep["segments"])
    krok_max, r_max = v * 0.1 + TOL_KROK, R_MAX                       # ANEKS_TEACH2-1 §3
    return {"pierwsze_200s_rowne_v2": bool(rowne), "n_odcinkow_200s": len(pierwsze), "max_roznica_pozycji_0_200s_m": round(d200, 9),
            "krok_max_0p1s_m": round(krok, 6), "prog_kroku_m": round(krok_max, 6), "ciagly": krok <= krok_max,
            "promien_max_m": round(r, 6), "prog_promienia_m": r_max, "promien_ok": r <= r_max,
            "koniec_ostatniego_odcinka_s": ep["segments"][-1]["t1"], "ep_dur_s": ep["ep_dur_s"],
            "litera": "ANEKS_TEACH2-1 §3: krok ≤ v·0.1 s + 0.001 m, promień ≤ 11.001 m",
            "ok": bool(rowne) and krok <= krok_max and r <= r_max and ep["segments"][-1]["t1"] >= DLUGOSC - 1e-6}


def main():
    v2 = json.load(open(V2))
    W.EP_DUR_S_L = DLUGOSC                                  # wyłącznie w tym procesie
    nowe = {k: v for k, v in v2.items() if k != "episodes"}
    nowe["episodes"] = [W.wahadlo(ep) for ep in v2["episodes"]]
    nowe["ep_dur_s"] = DLUGOSC
    nowe["zrodlo"] = {"v2": os.path.relpath(V2, ROOT), "v2_sha256": hashlib.sha256(open(V2, "rb").read()).hexdigest(),
                      "generator": "results/NAD2/tools/nad2_s4_manifest.wahadlo (import), EP_DUR_S_L = 1000 s",
                      "generator_sha256": hashlib.sha256(open(W.__file__, "rb").read()).hexdigest()}
    assert [e["episode_id"] for e in nowe["episodes"]] == [e["episode_id"] for e in v2["episodes"]] == list(range(len(v2["episodes"])))
    json.dump(nowe, open(OUT, "w"), indent=1)
    sha = hashlib.sha256(open(OUT, "rb").read()).hexdigest()
    v2e = next(e for e in v2["episodes"] if e["scenario_id"] == SCEN)
    e = next(e for e in nowe["episodes"] if e["scenario_id"] == SCEN)
    spr = sprawdziany(v2e, e)
    info = {"manifest": os.path.relpath(OUT, ROOT), "sha256": sha, "ep_dur_s": DLUGOSC, "episode_id": e["episode_id"], "scenario_id": SCEN,
            "sprawdziany_c10_s01": spr, "n_epizodow": len(nowe["episodes"])}
    json.dump(info, open(os.path.join(ROOT, "results/TEACH2/teach2_manifest.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(info, ensure_ascii=False))
    sys.exit(0 if spr["ok"] else 2)


if __name__ == "__main__":
    if "--sprawdz" in sys.argv[1:]:
        w = sprawdz_istniejacy()
        print(json.dumps(w, ensure_ascii=False))
        sys.exit(0 if w["ok"] else 2)
    main()
