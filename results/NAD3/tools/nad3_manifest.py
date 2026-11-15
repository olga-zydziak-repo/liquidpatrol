#!/usr/bin/env python3
"""results/NAD3/tools/nad3_manifest.py — manifest scenariuszy NADIR-III (PRE_NAD3 §4, PROMPT_NAD3_S1 §1.4; 0 bootów).

Generator bench/scenarios.gen_manifest z parametrami NAD3: RANGE0 = 10.0 m, DISK_R = 11.0 m, próg zawracania 8.5 m; reszta bez
zmian. Długość jak bramka NAD2 (results/NADIR/s4/scenario_manifest_s4.json, wzór results/NADIR/tools/nadir_s4_manifest.py):
trajektorie 200 s, orbit_dir przypięty z wersji 110 s tych samych parametrów (dłuższa pętla odcinków przesuwa losowanie
orbit_dir), prefiks odcinków o t1 < 110 s identyczny z wersją 110 s (asercja). Epizody: c00–c03 (nominały) oraz c05 i c10
(cięcia), ziarno s01, episode_id jak w kanonie ((seed − 1)·12 + komórka).
Testy na sucho (asercje, wynik w nad3_manifest.json): |intruz| ≤ DISK_R = 11.0 m (+ rozdzielczość generatora 1e-4 m: x0/y0
zaokrąglane do 4 cyfr, początek odcinka po wyjściu na brzeg dysku leży do ~7e-5 m za DISK_R) w całym epizodzie na torze ZADAWANYM (początki
odcinków, koniec ostatniego, próbka position_at co 0.01 s; koniec odcinka nieostatniego liczony z x0 zaokrąglonego do 1e-4 nie
jest zadawany — position_at przechodzi na x0 następnego — i jest obserwablą r_max_konce_obliczone), ciągłość toru: koniec odcinka = początek następnego z tolerancją rozdzielczości generatora (lekcja ANEKS_NAD2-4): x0/y0
i t0/t1 zaokrąglane do 4 cyfr ⇒ 2·√2·5e-5 + v_max·2·5e-5 = 2.414e-4 m (nie ostrzej niż 1e-4 m z promptu), czas: ep_dur_s = 200 i koniec ostatniego odcinka ≥ 200 s.
Wyjście: results/NAD3/s1/scenario_manifest_nad3.json + results/NAD3/s1/nad3_manifest.json (sha256, testy).

ANEKS_NAD3-1 §3.2–§3.4 — tryb domyślny „v2”: PEŁNA lista 120 epizodów (te same parametry, 200 s, orbit_dir z wersji 110 s) ⇒
pozycja na liście = episode_id (asercja dla 120/120 — niezmiennik, na którym stoi harness/intruder_motion.py:169); wpisy c00–c03,
c05, c10 identyczne (równość słowników) z plikiem S1; testy promienia, ciągłości i czasu WIĄŻĄCE dla 6 komórek używanych,
raportowane (nie blokują) dla pozostałych 114. Wyjście: results/NAD3/s1/scenario_manifest_nad3_v2.json + nad3_manifest_v2.json.
Tryb „v1” (argument) odtwarza plik S1 (6 epizodów) bez zmian. Użycie: nad3_manifest.py [v1|v2]
"""
import hashlib
import json
import math
import os
import sys

ROOT = "/home/olga/projects/liquidpatrol"
sys.path.insert(0, ROOT)
from bench import scenarios as S

PAR = {"range0": 10.0, "disk_r": 11.0, "prog_zawracania": 8.5}
EP_DUR = 200.0
KOMORKI = ("c00_s01", "c01_s01", "c02_s01", "c03_s01", "c05_s01", "c10_s01")
OUT = os.path.join(ROOT, "results/NAD3/s1/scenario_manifest_nad3.json")
OUT_V2 = os.path.join(ROOT, "results/NAD3/s1/scenario_manifest_nad3_v2.json")
TOL_R = 1e-4                                       # promień: x0/y0 zaokrąglone do 1e-4 ⇒ ≤ √2·5e-5 = 7.1e-5 m za brzegiem
V_MAX_INTR = 1.0
TOL_CIAGLOSC = 2 * math.sqrt(2) * 5e-5 + V_MAX_INTR * 2 * 5e-5   # x0/y0 obu odcinków + t0/t1 zaokrąglone do 1e-4 s ⇒ 2.414e-4 m


def koniec(s):
    dt = s["t1"] - s["t0"]
    hx, hy = math.cos(math.radians(s["heading_deg"])), math.sin(math.radians(s["heading_deg"]))
    return s["x0"] + s["v"] * hx * dt, s["y0"] + s["v"] * hy * dt


def testy(ep):
    seg = ep["segments"]
    rmax_zadane = max([math.hypot(s["x0"], s["y0"]) for s in seg] + [math.hypot(*koniec(seg[-1]))])
    rmax_konce = max(math.hypot(*koniec(s)) for s in seg)   # koniec liczony z x0 zaokrąglonego do 1e-4 — obserwabla
    rmax_probka = max(math.hypot(*S.position_at(ep, k * 0.01)[:2]) for k in range(int(EP_DUR * 100) + 1))
    skok = max([math.hypot(koniec(a)[0] - b["x0"], koniec(a)[1] - b["y0"]) for a, b in zip(seg, seg[1:])] or [0.0])
    czas = abs(seg[-1]["t1"] - seg[-1]["t0"]) >= 0 and seg[-1]["t1"] >= EP_DUR - 1e-6 and ep["ep_dur_s"] == EP_DUR
    ciag_t = all(abs(a["t1"] - b["t0"]) <= 1e-9 for a, b in zip(seg, seg[1:]))
    return {"r_max_zadane": round(rmax_zadane, 6), "r_max_probka": round(rmax_probka, 6), "r_max_konce_obliczone": round(rmax_konce, 6),
            "skok_max_m": round(skok, 8),
            "r_ok": rmax_zadane <= PAR["disk_r"] + TOL_R and rmax_probka <= PAR["disk_r"] + TOL_R,
            "ciaglosc_ok": skok <= TOL_CIAGLOSC and ciag_t, "czas_ok": czas, "n_odcinkow": len(seg)}


def generuj():
    """Pełna lista 200 s (orbit_dir z wersji 110 s, prefiks 110 s — asercje) — wspólna dla v1 i v2."""
    kr = S.gen_manifest(**PAR)
    assert S.EP_DUR_S == 110.0
    S.EP_DUR_S = EP_DUR
    dl = S.gen_manifest(**PAR)
    S.EP_DUR_S = 110.0
    for a, b in zip(kr["episodes"], dl["episodes"]):
        for k in ("scenario_id", "episode_id", "cell", "cell_index", "seed", "block", "is_test", "start_pos", "z"):
            assert a[k] == b[k], (a["scenario_id"], k)
        for i, s_ in enumerate(a["segments"]):
            if s_["t1"] < 110.0 - 1e-9:
                assert b["segments"][i] == s_, (a["scenario_id"], i)
            else:
                assert all(b["segments"][i][k] == s_[k] for k in ("t0", "x0", "y0", "heading_deg", "v")), (a["scenario_id"], i)
        b["orbit_dir_wygenerowany_200s"] = b["orbit_dir"]
        b["orbit_dir"] = a["orbit_dir"]
        b["ep_dur_s"] = EP_DUR
    return dl


def main_v2():
    dl = generuj()
    eps = dl["episodes"]
    assert len(eps) == 120 and all(i == e["episode_id"] for i, e in enumerate(eps)), "pozycja ≠ episode_id"
    v1 = {e["scenario_id"]: e for e in json.load(open(OUT))["episodes"]}
    ident = {sid: eps[e["episode_id"]] == e for sid, e in v1.items()}
    assert all(ident.values()), ident
    wyn, raport = {}, {}
    for e in eps:
        t = testy(e)
        if e["scenario_id"] in KOMORKI:
            assert t["r_ok"] and t["ciaglosc_ok"] and t["czas_ok"], (e["scenario_id"], t)
            wyn[e["scenario_id"]] = t
        else:
            raport[e["scenario_id"]] = t
    man = {k: dl[k] for k in ("n_cells", "seeds", "block1_seeds", "block2_seeds", "z_intr_m", "test_rule", "cells")}
    man.update(n_episodes=len(eps), disk_r_m=PAR["disk_r"], range0_m=PAR["range0"], prog_zawracania_m=PAR["prog_zawracania"],
               ep_dur_s=EP_DUR, episodes=eps,
               zrodlo={"generator": "bench/scenarios.gen_manifest(range0=10.0, disk_r=11.0, prog_zawracania=8.5)",
                       "pre": "PRE_NAD3 §4", "aneks": "ANEKS_NAD3-1 §3.2 (pełna lista: pozycja = episode_id)",
                       "orbit_dir": "z wersji 110 s tych samych parametrów", "prefiks_110s": "identyczny z wersją 110 s (asercja)",
                       "komorki_uzywane": list(KOMORKI)})
    json.dump(man, open(OUT_V2, "w"), indent=1)
    sha = hashlib.sha256(open(OUT_V2, "rb").read()).hexdigest()
    zle = {k: v for k, v in raport.items() if not (v["r_ok"] and v["ciaglosc_ok"] and v["czas_ok"])}
    json.dump({"manifest": os.path.relpath(OUT_V2, ROOT), "sha256": sha, "parametry": PAR, "ep_dur_s": EP_DUR, "n_episodes": len(eps),
               "pozycja_eq_episode_id": True, "identyczne_z_S1": ident, "testy": wyn,
               "testy_pozostale_114": {"n": len(raport), "niespelnione": zle,
                                       "r_max_probka_max": max(v["r_max_probka"] for v in raport.values()),
                                       "skok_max_m": max(v["skok_max_m"] for v in raport.values())},
               "tolerancja_ciaglosci_m": round(TOL_CIAGLOSC, 7), "tolerancja_promienia_m": TOL_R},
              open(os.path.join(os.path.dirname(OUT_V2), "nad3_manifest_v2.json"), "w"), indent=1, ensure_ascii=False)
    print(sha, {k: (v["r_max_probka"], v["n_odcinkow"]) for k, v in wyn.items()}, "pozostałe niespełnione:", len(zle))


def main():
    kr = S.gen_manifest(**PAR)                         # wersja 110 s tych samych parametrów (orbit_dir, prefiks)
    assert S.EP_DUR_S == 110.0
    S.EP_DUR_S = EP_DUR                                # wyłącznie w tym procesie
    dl = S.gen_manifest(**PAR)
    S.EP_DUR_S = 110.0
    eps, wyn = [], {}
    for a, b in zip(kr["episodes"], dl["episodes"]):
        if b["scenario_id"] not in KOMORKI:
            continue
        for k in ("scenario_id", "episode_id", "cell", "cell_index", "seed", "block", "is_test", "start_pos", "z"):
            assert a[k] == b[k], (a["scenario_id"], k)
        for i, s in enumerate(a["segments"]):
            if s["t1"] < 110.0 - 1e-9:
                assert b["segments"][i] == s, (a["scenario_id"], i)
            else:
                assert all(b["segments"][i][k] == s[k] for k in ("t0", "x0", "y0", "heading_deg", "v")), (a["scenario_id"], i)
        b["orbit_dir_wygenerowany_200s"] = b["orbit_dir"]
        b["orbit_dir"] = a["orbit_dir"]
        b["ep_dur_s"] = EP_DUR
        t = testy(b)
        assert t["r_ok"] and t["ciaglosc_ok"] and t["czas_ok"], (b["scenario_id"], t)
        wyn[b["scenario_id"]] = t
        eps.append(b)
    assert [e["scenario_id"] for e in eps] == list(KOMORKI), [e["scenario_id"] for e in eps]
    man = {k: dl[k] for k in ("n_cells", "seeds", "block1_seeds", "block2_seeds", "z_intr_m", "test_rule", "cells")}
    man.update(n_episodes=len(eps), disk_r_m=PAR["disk_r"], range0_m=PAR["range0"], prog_zawracania_m=PAR["prog_zawracania"],
               ep_dur_s=EP_DUR, episodes=eps,
               zrodlo={"generator": "bench/scenarios.gen_manifest(range0=10.0, disk_r=11.0, prog_zawracania=8.5)",
                       "pre": "PRE_NAD3 §4", "orbit_dir": "z wersji 110 s tych samych parametrów",
                       "prefiks_110s": "identyczny z wersją 110 s (asercja)", "komorki": list(KOMORKI)})
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(man, open(OUT, "w"), indent=1)
    sha = hashlib.sha256(open(OUT, "rb").read()).hexdigest()
    json.dump({"manifest": os.path.relpath(OUT, ROOT), "sha256": sha, "parametry": PAR, "ep_dur_s": EP_DUR, "testy": wyn,
               "tolerancja_ciaglosci_m": round(TOL_CIAGLOSC, 7), "tolerancja_promienia_m": TOL_R},
              open(os.path.join(os.path.dirname(OUT), "nad3_manifest.json"), "w"), indent=1, ensure_ascii=False)
    print(sha, {k: (v["r_max_probka"], v["n_odcinkow"]) for k, v in wyn.items()})


if __name__ == "__main__":
    (main if sys.argv[1:] == ["v1"] else main_v2)()
