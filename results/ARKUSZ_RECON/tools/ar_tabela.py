#!/usr/bin/env python3
"""results/ARKUSZ_RECON/tools/ar_tabela.py — tablica R3 szczebel × k (PROMPT_ARKUSZ_S0 §5, §8; 0 bootów).

Źródła: r3.json (k = 1, wszystkie 5 095 605 par, punkt stały), r3k.json (k = 1, 10, 20 na próbie 400 komórek źródłowych),
r3f.json (kontrprzykłady), r3e.json (sufit sprzężony k = 1). Zapis r3_tabela.json.
"""
import json
import os

OUT = "/home/olga/projects/liquidpatrol/results/ARKUSZ_RECON"


def wczytaj(n):
    p = os.path.join(OUT, n)
    return json.load(open(p)) if os.path.exists(p) else {}


r3, r3k, r3f, r3e = map(wczytaj, ("r3.json", "r3k.json", "r3f.json", "r3e.json"))
tab = []
for p in ("D1", "D2", "D3"):
    o = r3.get("k1", {}).get(p)
    if o:
        h = o["historia"][-1]
        tab.append({"szczebel": p, "k": 1, "zakres": "wszystkie komórki i pary", "dowiedzione_komorki": h["dowiedzione_komorki"],
                    "dowiedzione_czas": h["dowiedzione_czas"], "iteracje": len(o["historia"]), "operacje_par": o["operacje_par"],
                    "czas_s": o["czas_s"], "polszer_obrazu_stan_p50_iter0": o["historia"][0]["polszer_obrazu_stan_p50"],
                    "polszer_Z_koncowa_stan": o["polszer_Z_koncowa_stan"],
                    "test_start": r3.get("testy", {}).get(p + "_start"), "test_koniec": r3.get("testy", {}).get(p + "_koniec")})
    for k in (1, 10, 20):
        q = r3k.get(f"{p}_k{k}")
        if q:
            tab.append({"szczebel": p, "k": k, "zakres": "próba 200 + 200 komórek źródłowych (jednostajna / ważona czasem)",
                        "zrodla_wszystkie_cele_ok": [q["jednostajna"]["zrodla_wszystkie_cele_ok"], q["czas"]["zrodla_wszystkie_cele_ok"]],
                        "pary_ok": [q["jednostajna"]["pary_ok"], q["czas"]["pary_ok"]], "pary": [q["jednostajna"]["pary"], q["czas"]["pary"]],
                        "polszer_ograniczenia_reszty_mediana": [q["jednostajna"]["polszer_ograniczenia_reszty_mediana"], q["czas"]["polszer_ograniczenia_reszty_mediana"]],
                        "czas_s": q["czas_s"], "test": q["test"]})
tab.append({"szczebel": "D4", "k": None, "uwaga": "niewykonany (prompt: jeśli starczy czasu)"})
sufit = {"kontrprzyklady": {k: {kk: v[kk] for kk in ("dopuszczalne", "kontrprzyklady_D2D3", "czas_pobytu_w_falsyfikowanych_D2D3",
                                                     "kontrprzyklady_D1", "czas_pobytu_w_falsyfikowanych_D1")} for k, v in r3f.items() if isinstance(v, dict)},
         "sprzezony_k1": {p: v["historia"][-1] for p, v in r3e.items()},
         "rozprzezony_k1": {p: v["historia"][-1] for p, v in r3.get("sufit_empiryczny_k1", {}).items()}}
json.dump({"tablica": tab, "sufit": sufit}, open(os.path.join(OUT, "r3_tabela.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps({"tablica": tab, "sufit": sufit}, ensure_ascii=False, indent=1)[:6000])
