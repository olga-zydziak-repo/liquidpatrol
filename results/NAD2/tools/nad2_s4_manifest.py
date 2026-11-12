#!/usr/bin/env python3
"""results/NAD2/tools/nad2_s4_manifest.py — manifest scenariuszy lotu długiego NAD2 (ANEKS_NAD2-3 §2 pozycje 1 i 2).

Użycie: nad2_s4_manifest.py [1|2] (dom. 2). Pozycja 1 nie przeszła T2 (nad2_s4_testy.py: krok 0.1000206 m > v·0.1 + 1e-6 przy
t = 677.1 s — zaokrąglenie x0/y0 do 1e-4 m w generatorze na granicy odcinków) ⇒ pozycja 2 (wahadło), niżej.

Pozycja 1 (wyjście *_poz1.json):

Manifest bramki (results/NADIR/s4/scenario_manifest_s4.json, nadir_s4_manifest.py) ma trajektorie 200 s; po końcu intruder_motion
przestaje prowadzić intruza. Lot długi trwa t_entry + 30 + 600.5 s ≈ 655 s sim. Ten skrypt generuje manifest tym samym generatorem
bench/scenarios.gen_manifest (import, plik nietknięty) z EP_DUR_S_L = 800 s; zmiana wyłącznie długości:
  - odcinki o t0 < 200 s są identyczne z manifestem bramki (ten sam RNG, te same losowania) — asercja per epizod;
  - orbit_dir losowany PO pętli odcinków ⇒ przypięty z manifestu bramki (jak w nadir_s4_manifest.py);
  - komórki v = 0: jeden odcinek 0–800 s.

Pozycja 2 — wahadło (wyjście results/NAD2/s4/scenario_manifest_s4L.json + nad2_s4_manifest.json): odcinki bramki przycięte do
[0, 200] s w przód, potem ten sam tor wstecz (kurs + 180°, ta sama prędkość), na przemian, do 800 s. Odcinki wsteczne startują
w końcu odcinka liczonym tym samym wzorem co position_at (bez zaokrągleń), więc tor wsteczny jest lustrem toru w przód;
nawrót przy 200/600 s i przy 400 s (start) jest ciągły w pozycji. Pola epizodu (w tym orbit_dir) z manifestu bramki.
"""
import copy
import math
import hashlib
import json
import os
import sys

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, ROOT)
from bench import scenarios as S

EP_DUR_S_L = 800.0
BRAMKA = os.path.join(ROOT, "results/NADIR/s4/scenario_manifest_s4.json")
OUT = os.path.join(ROOT, "results/NAD2/s4/scenario_manifest_s4L.json")


OUT2 = OUT
OUT1 = OUT.replace(".json", "_poz1.json")
OKRES = 200.0


def _koniec(sg, t1):
    h = math.radians(sg["heading_deg"]); dt = t1 - sg["t0"]
    return sg["x0"] + sg["v"] * math.cos(h) * dt, sg["y0"] + sg["v"] * math.sin(h) * dt


def wahadlo(ep):
    przod = []
    for sg in ep["segments"]:
        if sg["t0"] >= OKRES:
            break
        przod.append(dict(sg, t1=min(sg["t1"], OKRES)))
    out = []
    for k in range(int(round(EP_DUR_S_L / OKRES))):
        base = k * OKRES
        if k % 2 == 0:                               # w przód: kopie odcinków bramki
            out += [dict(sg, t0=round(base + sg["t0"], 6), t1=round(base + sg["t1"], 6)) for sg in przod]
        else:                                        # wstecz: lustro w czasie, start w końcu odcinka w przód
            for sg in reversed(przod):
                ex, ey = _koniec(sg, sg["t1"])
                out.append({"t0": round(base + OKRES - sg["t1"], 6), "t1": round(base + OKRES - sg["t0"], 6),
                            "x0": ex, "y0": ey, "heading_deg": (sg["heading_deg"] + 180.0) % 360.0, "v": sg["v"]})
    e = copy.deepcopy(ep)
    e["segments"] = out
    e["ep_dur_s"] = EP_DUR_S_L
    e["wahadlo"] = {"okres_s": OKRES, "n_nog": len(out) // max(1, len(przod)), "zrodlo": "segmenty bramki [0, 200] s"}
    return e


def main_poz2():
    bra = json.load(open(BRAMKA))
    nowe = dict({k: v for k, v in bra.items() if k != "episodes"})
    nowe["episodes"] = [wahadlo(ep) for ep in bra["episodes"]]
    nowe["ep_dur_s"] = EP_DUR_S_L
    nowe["zrodlo"] = {"bramka": "results/NADIR/s4/scenario_manifest_s4.json",
                      "bramka_sha256": hashlib.sha256(open(BRAMKA, "rb").read()).hexdigest(),
                      "generator": "wahadło po segmentach bramki [0, 200] s, do 800 s (ANEKS_NAD2-3 §2 poz. 2)",
                      "orbit_dir": "z manifestu bramki", "prefiks_200s": "segmenty bramki (kopie)"}
    json.dump(nowe, open(OUT2, "w"), indent=1)
    sha = hashlib.sha256(open(OUT2, "rb").read()).hexdigest()
    json.dump({"manifest": os.path.relpath(OUT2, ROOT), "sha256": sha, "ep_dur_s": EP_DUR_S_L, "pozycja": 2},
              open(os.path.join(os.path.dirname(OUT2), "nad2_s4_manifest.json"), "w"), indent=1)
    print("OK poz2", sha)


def main():
    bra = json.load(open(BRAMKA))
    assert bra["ep_dur_s"] == 200.0 and S.EP_DUR_S == 110.0
    S.EP_DUR_S = EP_DUR_S_L                        # wyłącznie w tym procesie
    nowe = S.gen_manifest()
    S.EP_DUR_S = 110.0
    assert len(nowe["episodes"]) == len(bra["episodes"])
    for a, b in zip(bra["episodes"], nowe["episodes"]):
        assert a["scenario_id"] == b["scenario_id"] and a["episode_id"] == b["episode_id"]
        for k in ("cell", "cell_index", "seed", "block", "is_test", "start_pos", "z"):
            assert a[k] == b[k], (a["scenario_id"], k)
        sa, sb = a["segments"], b["segments"]
        for i, s in enumerate(sa):
            if s["v"] > 0 or len(sa) > 1:
                assert sb[i] == s, (a["scenario_id"], i)   # także odcinek przecinający 200 s (pętla nie przycina dur)
            else:                                          # v = 0: jeden odcinek 0–ep_dur
                assert all(sb[i][k] == s[k] for k in ("t0", "x0", "y0", "heading_deg", "v")), (a["scenario_id"], i)
        assert sb[-1]["t1"] >= EP_DUR_S_L - 1e-6
        b["orbit_dir_wygenerowany_800s"] = b["orbit_dir"]
        b["orbit_dir"] = a["orbit_dir"]           # przypięty z manifestu bramki
        b["ep_dur_s"] = EP_DUR_S_L
    nowe["ep_dur_s"] = EP_DUR_S_L
    nowe["zrodlo"] = {"bramka": "results/NADIR/s4/scenario_manifest_s4.json",
                      "bramka_sha256": hashlib.sha256(open(BRAMKA, "rb").read()).hexdigest(),
                      "generator": "bench/scenarios.gen_manifest z EP_DUR_S=800 (ANEKS_NAD2-3 §2 poz. 1)",
                      "orbit_dir": "z manifestu bramki", "prefiks_200s": "identyczny z bramką (asercja)"}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(nowe, open(OUT1, "w"), indent=1)
    sha = hashlib.sha256(open(OUT1, "rb").read()).hexdigest()
    json.dump({"manifest": os.path.relpath(OUT1, ROOT), "sha256": sha, "ep_dur_s": EP_DUR_S_L, "pozycja": 1,
               "orbit_dir_rozne_od_wygenerowanego": sum(e["orbit_dir"] != e["orbit_dir_wygenerowany_800s"] for e in nowe["episodes"])},
              open(os.path.join(os.path.dirname(OUT1), "nad2_s4_manifest_poz1.json"), "w"), indent=1)
    print("OK poz1", sha)


if __name__ == "__main__":
    (main if sys.argv[1:] == ["1"] else main_poz2)()
