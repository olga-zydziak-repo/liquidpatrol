#!/usr/bin/env python3
"""results/TEACH/tools/teach_w3.py — W3 czas producenta mapy na jednym rdzeniu (PROMPT_TEACH_S1 §4 W3, PRE_TEACH §6 S1; 0 bootów).

Bieg teach_w2.py w wariancie z results/TEACH/s1/tor.json, jeden proces przypięty do jednego rdzenia (taskset -c RDZEŃ), cv2
jednowątkowo, łata S, 13 lotów (W2 i tak sprawdza wierność na wszystkich łatach). Części do katalogu tymczasowego; tu tylko czasy:
od klatki flagi do gotowej georeferencji (wymóg ≤ 0.5 s — największa z 13 lotów), opóźnienie pierwszej przyjętej poprawki po
fladze (czas sim), czas kadru w fazie mapy i lokalizacji p50 / p95 / max (wywołanie Producent.obserwacja bez renderu).
Wyjście: results/TEACH/s1/w3_czas.json; kod 2, gdy zamknięcie > 0.5 s (STOP bez śmierci, PROMPT §5).
"""
import json
import os
import subprocess
import sys
import tempfile

import numpy as np

ROOT = "/home/olga/projects/liquidpatrol"
S1 = os.path.join(ROOT, "results/TEACH/s1")
RDZEN = os.environ.get("TEACH_W3_RDZEN", "3")
WYMOG_MS = 500.0


def main():
    wariant = json.load(open(os.path.join(S1, "tor.json")))["tor"]["wariant_K"]
    tmp = tempfile.mkdtemp(prefix="teach_w3_")
    cmd = ["taskset", "-c", RDZEN, sys.executable, os.path.join(ROOT, "results/TEACH/tools/teach_w2.py"), "--wariant", wariant,
           "--procesy", "1", "--laty", "S", "--wyj", tmp]
    p = subprocess.run(cmd, capture_output=True, text=True)
    assert p.returncode == 0, p.stderr[-2000:]
    w = json.load(open(os.path.join(tmp, f"w2_{'K' if wariant == 'K' else 'K2'}.json")))
    lot = {r["lot"]: r["czas"] for r in w["wyniki"]}
    zam = [c["ms_od_flagi_do_georef"] for c in lot.values()]
    q = lambda key, f: {"p50_max": round(max(c[key]["p50"] for c in lot.values()), 2),
                        "p95_max": round(max(c[key]["p95"] for c in lot.values()), 2), "max": round(max(c[key]["max"] for c in lot.values()), 2)}
    op = [c["opoznienie_pierwszej_poprawki_s"] for c in lot.values()]
    out = {"wariant_K": wariant, "rdzen": RDZEN, "cv2": w["cv2"], "python": w["python"], "interpreter": w["interpreter"],
           "zgodne_z_reconem": w["zgodne_wszystkie"], "polecenie": " ".join(cmd[:3] + ["python3"] + cmd[4:6] + cmd[6:]),
           "zamkniecie_ms": {"max": round(max(zam), 2), "p50": round(float(np.median(zam)), 2), "wymog": WYMOG_MS,
                             "spelniony": max(zam) <= WYMOG_MS},
           "opoznienie_pierwszej_poprawki_s": {"max": max(op), "min": min(op)},
           "kadr_mapa_ms": q("ms_mapa", None), "kadr_lokalizacja_ms": q("ms_lok", None), "per_lot": lot,
           "uwaga": "kadr mapy: decyzja klatki kluczowej + prostowanie + cechy SIFT + dopasowania wyprzedzające (w buforze jednej klatki "
                    "koszt przypada na następną klatkę); kadr lokalizacji: prostowanie + cechy + do 3 dopasowań; zamknięcie: zbiór wiązań "
                    "z bufora dopasowań + Gauss–Newton M4 + włączenie kadru z bufora"}
    json.dump(out, open(os.path.join(S1, "w3_czas.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "per_lot"}, ensure_ascii=False, indent=1))
    sys.exit(0 if out["zamkniecie_ms"]["spelniony"] else 2)


if __name__ == "__main__":
    main()
