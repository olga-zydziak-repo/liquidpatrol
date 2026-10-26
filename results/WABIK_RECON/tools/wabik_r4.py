#!/usr/bin/env python3
"""results/WABIK_RECON/tools/wabik_r4.py — R4 PROMPT_WABIK_S0: arytmetyka czasu
rezydencji w pasie admisji dh∈[5,18] m dla rodzin manewrów (v ≤ 1.0 m/s),
vs 10.0 s prostej radialnej (sufit TRANSIT).

Twierdzenie (dolna granica, forma zamknięta): dla KAŻDEGO toru o |v| ≤ v_max
zachodzi |d dh/dt| ≤ v_max, więc czas przejścia pasa od dh=15 (start siatki)
do dh=5 wynosi ≥ (15−5)/v_max = 10.0 s — prosta radialna REALIZUJE minimum.
⇒ manewr NIE MOŻE skrócić okna poniżej 10.0 s, jeśli cel ma zejść pod 5 m;
jedyny sposób „obniżenia" = NIE wchodzić pod 5 m (wtedy d_min ≥ b i separacja
D6 nie jest zagrożona — sufit przestaje być groźny, bo nie ma czego bronić).

Rodziny (rachunek, v=1.0): styczny przelot (cięciwa o parametrze b),
łuk o promieniu skrętu R_c (najkrótsze zejście 15→5 przy ograniczonej krzywiźnie),
loiter na promieniu r0, zygzak (dolna granica = twierdzenie).
Wyjście: r4_rezydencja.json + stdout.
"""
import json
import math
import os

OUTD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = 1.0
R_IN, R_OUT, R_START = 5.0, 18.0, 15.0

rows = []
rows.append({"rodzina": "prosta radialna (baseline siatki)", "parametr": "—",
             "rezydencja_s": 10.0,
             "nota": "minimum osiągnięte; pas 15→5 @1 m/s (litera TRANSIT)"})
rows.append({"rodzina": "DOLNA GRANICA (twierdzenie)", "parametr": "dowolny tor |v|<=1",
             "rezydencja_s": 10.0,
             "nota": "|d dh/dt| <= |v| <= 1 ⇒ czas 15→5 >= 10 s; manewr NIE skraca"})
for b in (5.0, 8.0, 12.0, 15.0, 17.0):
    L = 2.0 * math.sqrt(R_OUT * R_OUT - b * b)
    rows.append({"rodzina": "styczny przelot (cięciwa)", "parametr": f"b={b:.0f} m",
                 "rezydencja_s": round(L / V, 1),
                 "nota": f"d_min={b:.0f} m — pod 5 m NIE wchodzi ⇒ D6-separacja "
                         "niezagrożona bez akwizycji" if b >= 5 else ""})
# łuk: zejście 15→5 po łuku o promieniu skrętu R_c (styczna spirala ~ ćwiartka);
# dolne oszacowanie długości: >= odległość radialna 10 m; górne dla R_c: ~ (pi/2)*R_c przy R_c>=10
for Rc in (5.0, 10.0, 20.0):
    L = max(10.0, (math.pi / 2.0) * Rc * (10.0 / max(Rc, 10.0)))
    rows.append({"rodzina": "łuk (ograniczona krzywizna)", "parametr": f"R_c={Rc:.0f} m",
                 "rezydencja_s": round(max(10.0, L) / V, 1),
                 "nota": "zejście po łuku ZAWSZE >= 10 s (twierdzenie); łuk tylko wydłuża"})
for r0 in (6.0, 10.0, 17.0):
    rows.append({"rodzina": "loiter na promieniu", "parametr": f"r0={r0:.0f} m",
                 "rezydencja_s": None,
                 "nota": "rezydencja = cały epizod (ograniczona tylko EP_DUR 110 s) — "
                         "okno admisji NIEOGRANICZONE; sufit przeglądu przestaje wiązać"})
rows.append({"rodzina": "zygzak |v|<=1", "parametr": "dowolne kąty",
             "rezydencja_s": ">=10 + wydłużenie",
             "nota": "postęp radialny <= v ⇒ każdy zygzak WYDŁUŻA rezydencję vs prosta"})

out = {"pas_m": [R_IN, R_OUT], "start_siatki_m": R_START, "v_max": V,
       "wniosek": "prosta radialna = NAJGORSZY przypadek czasowy (minimum 10.0 s); "
                  "każdy manewr v<=1 wchodzący pod 5 m WYDŁUŻA okno admisji "
                  "(sufit TRANSIT może tylko ZELŻEĆ); 'obniżenie' wyłącznie przez "
                  "nie-wchodzenie pod 5 m — wtedy d_min=b>=5 i separacja D6 trzyma "
                  "bez akwizycji (zagrożeniem przestaje być tor, zostaje ROZPOZNANIE)",
       "niezmierzone": "zmiana kursu celu POD orbitą (pościg za manewrem) — kampanie "
                       "dowiodły orbit na celach radialnych v<=1.0; interakcja "
                       "manewr-pod-orbitą wymaga lotów",
       "wiersze": rows}
json.dump(out, open(os.path.join(OUTD, "r4_rezydencja.json"), "w"), indent=1)
for r in rows:
    print(f"{r['rodzina']:38s} {r['parametr']:18s} rez={r['rezydencja_s']}  {r['nota'][:60]}")
print("zapisano r4_rezydencja.json")
