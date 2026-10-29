#!/usr/bin/env python3
"""results/WK2/tools/wk2_kcontrol.py — kontrola oporu per boot (PRE_WK2 §2, PROMPT_WK2_S1 §1.3/§2.1).

Importuje miernik reconu `results/WK2_RECON/tools/wk2_k.py` (09e4b440, READ-ONLY): k z fazy orbity bootu
(bilans sił poziomych). Oczekiwane k = kalibracja reconu dla skali świata (z manifestu, blok `wk.world`):
s = 0.63 → 0.4939 /s (kal2_s063), s = 0.46 → 0.3219 /s (kal1_s046). Tolerancja ±20% (PRE_WK2 §2);
poza ⇒ STOP do adjudykacji CC; dwukrotnie ⇒ STOP-ANEKS (PRE §3).
Pomiar dotyczy ramienia sieci; prędkości sieci są niższe od nauczyciela — liniowość oporu w v sprawdzona
w RECON_WK2 §R1. Przy wietrze ≠ 0 bilans `wk2_k` zakłada wiatr 0 ⇒ k tam NIE jest porównywane z tolerancją
(pole `kontrola` = "n/d (wiatr)"), raportowane opisowo.

Użycie: wk2_kcontrol.py <out.json> <katalog_boota>...
"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "results", "WK2_RECON", "tools"))
from wk2_k import measure  # noqa: E402

K_KAL = {"world_wk2_s063": 0.4939, "world_wk2_k055": 0.3219}
TOL = 0.20


def main():
    out, dirs = sys.argv[1], sys.argv[2:]
    res = []
    for d in dirs:
        d = os.path.abspath(d)
        world = json.load(open(os.path.join(d, "manifest.json")))["wk"]["world"]
        base, wind = world.rsplit("_", 1)
        r = measure(d)
        k_exp = K_KAL.get(base)
        r.update({"world": world, "k_oczekiwane": k_exp})
        if wind != "s0":
            r["kontrola"] = "n/d (wiatr)"
        elif k_exp is None or "k" not in r:
            r["kontrola"] = "BRAK DANYCH"
        else:
            dev = (r["k"] - k_exp) / k_exp
            r["odchylenie"] = round(dev, 4)
            r["kontrola"] = "OK" if abs(dev) <= TOL else "POZA TOLERANCJA"
        res.append(r)
        print(r["boot"], world, "k", r.get("k"), r.get("k_ci95_bootstrap_blokowy"), "oczek.", k_exp,
              "odch.", r.get("odchylenie"), r["kontrola"])
    json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
